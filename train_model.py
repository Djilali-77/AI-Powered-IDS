"""Train the autoencoder-based IDS on CICIDS2017 and export every artifact the API needs.

Pipeline:
    1. Load + clean the data (inf/NaN removal, duplicate removal)
    2. Stateless log transform
    3. Stratified split: train / validation / test
    4. Fit the scaler on benign *training* rows only (no data leakage)
    5. Train the autoencoder on benign traffic only, with early stopping
    6. Calibrate the alert threshold on the validation set (best F1)
    7. Evaluate once on the untouched test set + compare with an Isolation Forest baseline
    8. Report the detection rate per attack type
    9. Export model, scaler, config, metrics, plots and real demo samples
"""

import argparse
import glob
import json
import os
import random
import subprocess
import sys
from datetime import datetime, timezone

import joblib
import matplotlib

matplotlib.use("Agg")  # Headless backend: no display needed
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402
import torch.nn as nn  # noqa: E402
from sklearn.ensemble import IsolationForest  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    average_precision_score,
    classification_report,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split  # noqa: E402
from sklearn.preprocessing import MinMaxScaler  # noqa: E402
from torch.utils.data import DataLoader, TensorDataset  # noqa: E402

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "back-end")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")

# Reuse the exact same model + preprocessing as the API
sys.path.insert(0, BACKEND_DIR)
from model import Autoencoder, log_transform  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the autoencoder IDS.")
    parser.add_argument("--data-dir", default=os.path.join(ROOT_DIR, "dataset"))
    parser.add_argument("--download", action="store_true", help="Download the dataset with the Kaggle CLI")
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--patience", type=int, default=5, help="Early stopping patience (epochs)")
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--latent-dim", type=int, default=16)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--wandb", action="store_true", help="Log the run to Weights & Biases")
    parser.add_argument("--skip-baseline", action="store_true", help="Skip the Isolation Forest baseline")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def download_dataset(data_dir: str) -> None:
    os.makedirs(data_dir, exist_ok=True)
    subprocess.run(
        ["kaggle", "datasets", "download", "-d", "chethuhn/network-intrusion-dataset", "-p", data_dir, "--unzip"],
        check=True,
    )


def load_data(data_dir: str) -> pd.DataFrame:
    files = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
    if not files:
        raise SystemExit(f"No CSV files found in {data_dir}. Use --download or copy the dataset there.")

    df = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(inplace=True)
    # CICIDS2017 contains many exact duplicates that would leak between splits
    df.drop_duplicates(inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


@torch.no_grad()
def reconstruction_errors(model: nn.Module, data: np.ndarray, device: torch.device, batch_size: int = 8192) -> np.ndarray:
    """Per-sample mean squared reconstruction error."""
    model.eval()
    errors = []
    for start in range(0, len(data), batch_size):
        batch = torch.from_numpy(data[start:start + batch_size]).to(device)
        reconstructed = model(batch)
        errors.append(((batch - reconstructed) ** 2).mean(dim=1).cpu().numpy())
    return np.concatenate(errors)


def train_autoencoder(model, train_data, val_data, args, device, run):
    """Train on benign data only; keep the weights with the best validation loss."""
    loader = DataLoader(TensorDataset(torch.from_numpy(train_data)), batch_size=args.batch_size, shuffle=True)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    best_val, best_state, wait = float("inf"), None, 0
    for epoch in range(1, args.epochs + 1):
        model.train()
        total = 0.0
        for (batch,) in loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            loss = criterion(model(batch), batch)
            loss.backward()
            optimizer.step()
            total += loss.item()

        train_loss = total / len(loader)
        val_loss = float(reconstruction_errors(model, val_data, device).mean())
        print(f"Epoch [{epoch}/{args.epochs}] train_loss={train_loss:.6f} val_loss={val_loss:.6f}")
        if run:
            run.log({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})

        if val_loss < best_val - 1e-8:
            best_val = val_loss
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            wait = 0
        else:
            wait += 1
            if wait >= args.patience:
                print(f"Early stopping at epoch {epoch}")
                break

    model.load_state_dict(best_state)
    return model


def compute_metrics(y_true: np.ndarray, errors: np.ndarray, threshold: float) -> dict:
    y_pred = (errors >= threshold).astype(int)
    report = classification_report(y_true, y_pred, target_names=["benign", "attack"], output_dict=True, zero_division=0)
    benign_count = max(int((y_true == 0).sum()), 1)
    return {
        "roc_auc": float(roc_auc_score(y_true, errors)),
        "average_precision": float(average_precision_score(y_true, errors)),
        "precision": float(report["attack"]["precision"]),
        "recall": float(report["attack"]["recall"]),
        "f1": float(report["attack"]["f1-score"]),
        "false_positive_rate": float(((y_pred == 1) & (y_true == 0)).sum() / benign_count),
    }


def per_attack_recall(names: np.ndarray, errors: np.ndarray, threshold: float) -> dict:
    """Detection rate for each attack type (names and errors must be aligned)."""
    results = {}
    for name in sorted(set(names)):
        if name == "BENIGN":
            continue
        mask = names == name
        results[name] = {
            "count": int(mask.sum()),
            "detection_rate": float((errors[mask] >= threshold).mean()),
        }
    return results


def save_plots(y_test, scores_by_model, errors_test, threshold) -> None:
    os.makedirs(ASSETS_DIR, exist_ok=True)

    # ROC curves (autoencoder vs baseline)
    plt.figure(figsize=(6, 5))
    for name, scores in scores_by_model.items():
        fpr, tpr, _ = roc_curve(y_test, scores)
        plt.plot(fpr, tpr, label=f"{name} (AUC={roc_auc_score(y_test, scores):.3f})")
    plt.plot([0, 1], [0, 1], "k--", alpha=0.4)
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title("ROC curve (test set)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "roc_curve.png"), dpi=150)
    plt.close()

    # Reconstruction error distribution
    errors = np.clip(errors_test, 1e-10, None)
    bins = np.logspace(np.log10(errors.min()), np.log10(errors.max()), 80)
    plt.figure(figsize=(7, 4.5))
    plt.hist(errors[y_test == 0], bins=bins, alpha=0.6, density=True, label="benign")
    plt.hist(errors[y_test == 1], bins=bins, alpha=0.6, density=True, label="attack")
    plt.axvline(threshold, color="k", linestyle="--", label=f"threshold = {threshold:.2e}")
    plt.xscale("log")
    plt.xlabel("Reconstruction error (log scale)")
    plt.ylabel("Density")
    plt.title("Reconstruction error distribution (test set)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "error_distribution.png"), dpi=150)
    plt.close()


def export_samples(rng, x_raw, y, names, test_idx, per_class: int = 25) -> list:
    """Export RAW (unscaled) real test rows so the demo uses genuine traffic."""
    samples = []
    for is_attack in (0, 1):
        pool = test_idx[y[test_idx] == is_attack]
        chosen = rng.choice(pool, size=min(per_class, len(pool)), replace=False)
        for i in chosen:
            samples.append({
                "label": str(names[i]),
                "is_attack": bool(is_attack),
                "features": [float(v) for v in x_raw[i]],
            })
    return samples


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    run = None
    if args.wandb:
        import wandb

        run = wandb.init(project="ids-autoencoder-pytorch", config=vars(args))

    # ---------------------------------------------------------------- data
    if args.download:
        download_dataset(args.data_dir)
    df = load_data(args.data_dir)

    attack_names = df["label"].astype(str).str.strip().to_numpy()
    y = (attack_names != "BENIGN").astype(int)
    feature_names = [c for c in df.columns if c != "label"]
    x_raw = df[feature_names].to_numpy(dtype=np.float32)
    del df  # Free memory
    print(f"Samples: {len(y):,} | Features: {len(feature_names)} | Attack ratio: {y.mean():.2%}")

    x_log = log_transform(x_raw)

    # -------------------------------------------------------------- splits
    # test (20%) is never touched until the final evaluation
    idx = np.arange(len(y))
    idx_trainval, idx_test = train_test_split(idx, test_size=0.2, stratify=y, random_state=args.seed)
    idx_fit, idx_val = train_test_split(
        idx_trainval, test_size=0.25, stratify=y[idx_trainval], random_state=args.seed
    )
    benign_fit = idx_fit[y[idx_fit] == 0]
    benign_val = idx_val[y[idx_val] == 0]

    # Scaler is fitted on benign training rows only -> no leakage from val/test
    scaler = MinMaxScaler().fit(x_log[benign_fit])

    def prep(indices: np.ndarray) -> np.ndarray:
        return scaler.transform(x_log[indices]).astype(np.float32)

    train_data = prep(benign_fit)
    val_benign_data = prep(benign_val)
    val_data, y_val = prep(idx_val), y[idx_val]
    test_data, y_test = prep(idx_test), y[idx_test]

    # ------------------------------------------------------------ training
    model = Autoencoder(len(feature_names), args.hidden_dim, args.latent_dim).to(device)
    model = train_autoencoder(model, train_data, val_benign_data, args, device, run)

    # ----------------------------------------------------------- threshold
    val_errors = reconstruction_errors(model, val_data, device)
    precision, recall, thresholds = precision_recall_curve(y_val, val_errors)
    f1_scores = 2 * precision[:-1] * recall[:-1] / (precision[:-1] + recall[:-1] + 1e-12)
    threshold = float(thresholds[int(np.argmax(f1_scores))])
    threshold_p99 = float(np.percentile(val_errors[y_val == 0], 99))
    print(f"Threshold (best validation F1): {threshold:.6f} | 99th percentile of benign: {threshold_p99:.6f}")

    # ---------------------------------------------------------- evaluation
    test_errors = reconstruction_errors(model, test_data, device)
    metrics = compute_metrics(y_test, test_errors, threshold)
    print("\nTest metrics:", json.dumps(metrics, indent=2))
    print(classification_report(y_test, (test_errors >= threshold).astype(int), target_names=["benign", "attack"], zero_division=0))

    # Detection rate per attack type (shows which attacks the model misses)
    per_attack = per_attack_recall(attack_names[idx_test], test_errors, threshold)
    print("\nDetection rate per attack type:")
    for name, stats in sorted(per_attack.items(), key=lambda item: item[1]["detection_rate"]):
        print(f"  {name:<30} n={stats['count']:>7,}  detected={stats['detection_rate']:.1%}")

    scores_by_model = {"Autoencoder": test_errors}
    baseline_metrics = None
    if not args.skip_baseline:
        print("\nTraining Isolation Forest baseline...")
        rng_base = np.random.default_rng(args.seed)
        subset = rng_base.choice(len(train_data), size=min(200_000, len(train_data)), replace=False)
        forest = IsolationForest(n_estimators=100, random_state=args.seed, n_jobs=-1).fit(train_data[subset])
        forest_scores = -forest.score_samples(test_data)  # Higher = more anomalous
        scores_by_model["Isolation Forest"] = forest_scores
        baseline_metrics = {"roc_auc": float(roc_auc_score(y_test, forest_scores))}
        print(f"Isolation Forest ROC AUC: {baseline_metrics['roc_auc']:.4f}")

    save_plots(y_test, scores_by_model, test_errors, threshold)

    # ------------------------------------------------------------- exports
    os.makedirs(ASSETS_DIR, exist_ok=True)
    torch.save(model.cpu().state_dict(), os.path.join(BACKEND_DIR, "autoencoder.pth"))
    joblib.dump(scaler, os.path.join(BACKEND_DIR, "scaler.pkl"))

    config = {
        "threshold": threshold,
        "threshold_p99_benign": threshold_p99,
        "input_dim": len(feature_names),
        "hidden_dim": args.hidden_dim,
        "latent_dim": args.latent_dim,
        "log_transform": True,
        "feature_names": feature_names,
        "metrics": metrics,
        "baseline_isolation_forest": baseline_metrics,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    with open(os.path.join(BACKEND_DIR, "model_config.json"), "w") as f:
        json.dump(config, f, indent=2)

    rng = np.random.default_rng(args.seed)
    with open(os.path.join(BACKEND_DIR, "samples.json"), "w") as f:
        json.dump(export_samples(rng, x_raw, y, attack_names, idx_test), f)

    with open(os.path.join(ASSETS_DIR, "metrics.json"), "w") as f:
        json.dump(
            {"autoencoder": metrics, "isolation_forest": baseline_metrics, "per_attack_type": per_attack},
            f,
            indent=2,
        )

    if run:
        run.log({"threshold": threshold, **{f"test_{k}": v for k, v in metrics.items()}})
        run.finish()
    print("\nDone. Artifacts saved in back-end/ and assets/.")


if __name__ == "__main__":
    main()