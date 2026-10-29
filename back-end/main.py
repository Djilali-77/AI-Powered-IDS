"""FastAPI backend for the AI-powered Intrusion Detection System (IDS)."""

import json
import logging
import os
import random
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal

import joblib
import numpy as np
import torch
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from model import Autoencoder, log_transform

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ids-api")

BASE_DIR = Path(__file__).resolve().parent
MAX_BATCH_SIZE = 1000


class IDSEngine:
    """Loads every artifact once and scores network-flow features."""

    def __init__(self, base_dir: Path) -> None:
        with open(base_dir / "model_config.json") as f:
            self.config = json.load(f)

        self.threshold = float(self.config["threshold"])
        self.input_dim = int(self.config["input_dim"])

        self.model = Autoencoder(
            input_dim=self.input_dim,
            hidden_dim=int(self.config["hidden_dim"]),
            latent_dim=int(self.config["latent_dim"]),
        )
        state = torch.load(base_dir / "autoencoder.pth", map_location="cpu")
        self.model.load_state_dict(state)
        self.model.eval()  # Disable training-only behaviour

        self.scaler = joblib.load(base_dir / "scaler.pkl")

        samples_path = base_dir / "samples.json"
        self.samples = json.loads(samples_path.read_text()) if samples_path.exists() else []

    @torch.no_grad()
    def score(self, features: np.ndarray) -> np.ndarray:
        """Return one reconstruction error per row of `features` (shape: n x input_dim)."""
        x = features.astype(np.float32)
        if self.config.get("log_transform", True):
            x = log_transform(x)  # Must match the preprocessing used in training
        x = self.scaler.transform(x).astype(np.float32)

        tensor = torch.from_numpy(x)
        reconstructed = self.model(tensor)
        return ((tensor - reconstructed) ** 2).mean(dim=1).numpy()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast: if an artifact is missing the server refuses to start
    app.state.engine = IDSEngine(BASE_DIR)
    logger.info("Model, scaler and threshold loaded (threshold=%.6f)", app.state.engine.threshold)
    yield


app = FastAPI(
    title="AI-Powered IDS API",
    description="Unsupervised network intrusion detection with a PyTorch autoencoder.",
    version="2.0.0",
    lifespan=lifespan,
)

# Comma-separated list, e.g. ALLOWED_ORIGINS="https://my-frontend.vercel.app"
allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,  # No cookies are used, and "*" + credentials is invalid
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def get_engine(request: Request) -> IDSEngine:
    return request.app.state.engine


EngineDep = Annotated[IDSEngine, Depends(get_engine)]


# ----------------------------------------------------------------- schemas
class TrafficData(BaseModel):
    features: list[float] = Field(..., description="Raw (unscaled) flow features, in training order.")


class BatchTrafficData(BaseModel):
    samples: list[list[float]] = Field(..., min_length=1, max_length=MAX_BATCH_SIZE)


class Prediction(BaseModel):
    reconstruction_error: float
    threshold: float
    score_ratio: float = Field(..., description="reconstruction_error / threshold (>= 1 means attack)")
    is_attack: bool
    label: Literal["normal", "attack"]


class SimulationResult(Prediction):
    kind: Literal["benign", "attack"]
    true_label: str
    correct: bool


# ----------------------------------------------------------------- helpers
def to_matrix(rows: list[list[float]], expected_dim: int) -> np.ndarray:
    try:
        matrix = np.asarray(rows, dtype=np.float64)
    except ValueError:
        raise HTTPException(status_code=422, detail="All samples must have the same length.") from None
    if matrix.ndim != 2 or matrix.shape[1] != expected_dim:
        raise HTTPException(status_code=422, detail=f"Expected {expected_dim} features per sample.")
    if not np.isfinite(matrix).all():
        raise HTTPException(status_code=422, detail="Features must be finite numbers (no NaN / Infinity).")
    return matrix


def to_prediction(error: float, threshold: float) -> Prediction:
    is_attack = error >= threshold
    return Prediction(
        reconstruction_error=error,
        threshold=threshold,
        score_ratio=error / threshold,
        is_attack=bool(is_attack),
        label="attack" if is_attack else "normal",
    )


# --------------------------------------------------------------- endpoints
@app.get("/")
def home():
    return {"message": "AI-Powered IDS backend is running.", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/wakeup")
def wakeup(engine: EngineDep):
    """Run one dummy inference so a cold server is fully warmed up."""
    engine.score(np.zeros((1, engine.input_dim)))
    return {"status": "ok", "message": "Server is ready!"}


@app.get("/model-info")
def model_info(engine: EngineDep):
    cfg = engine.config
    return {
        "input_dim": engine.input_dim,
        "threshold": engine.threshold,
        "latent_dim": cfg["latent_dim"],
        "metrics": cfg.get("metrics"),
        "baseline_isolation_forest": cfg.get("baseline_isolation_forest"),
        "trained_at": cfg.get("trained_at"),
        "demo_samples": len(engine.samples),
    }


@app.post("/predict", response_model=Prediction)
def predict(data: TrafficData, engine: EngineDep):
    matrix = to_matrix([data.features], engine.input_dim)
    error = float(engine.score(matrix)[0])
    return to_prediction(error, engine.threshold)


@app.post("/predict/batch", response_model=list[Prediction])
def predict_batch(data: BatchTrafficData, engine: EngineDep):
    matrix = to_matrix(data.samples, engine.input_dim)
    errors = engine.score(matrix)
    return [to_prediction(float(e), engine.threshold) for e in errors]


@app.get("/simulate/{kind}", response_model=SimulationResult)
def simulate(kind: Literal["benign", "attack"], engine: EngineDep):
    """Score a random REAL flow from the held-out test set and reveal its ground truth."""
    wants_attack = kind == "attack"
    pool = [s for s in engine.samples if s["is_attack"] == wants_attack]
    if not pool:
        raise HTTPException(status_code=503, detail="No demo samples available. Re-run train_model.py.")

    sample = random.choice(pool)
    matrix = to_matrix([sample["features"]], engine.input_dim)
    prediction = to_prediction(float(engine.score(matrix)[0]), engine.threshold)

    return SimulationResult(
        **prediction.model_dump(),
        kind=kind,
        true_label=sample["label"].replace("\ufffd", "-"),
        correct=prediction.is_attack == wants_attack,
    )