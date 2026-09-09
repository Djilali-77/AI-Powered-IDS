import os
import glob
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
import joblib
import json
import wandb  # <-- Import de W&B ajouté

# ===========================
# 0. Kaggle Download & Setup
# ===========================
print("📥 Downloading Data from Kaggle...")
os.system("mkdir -p dataset")
os.system("kaggle datasets download -d chethuhn/network-intrusion-dataset -p ./dataset")
os.system("unzip -q -o ./dataset/network-intrusion-dataset.zip -d ./dataset/")

# ===========================
# 1. Data Loading & Cleaning
# ===========================
print("⚙️ Preparing Data...")
all_files = glob.glob("./dataset/*.csv")

if len(all_files) == 0:
    print("❌ Error: No CSV files found. Please check your Kaggle API setup.")
    exit()

df_list = [pd.read_csv(filename) for filename in all_files]
combined_df = pd.concat(df_list, ignore_index=True)

# Clean Columns
combined_df.columns = combined_df.columns.str.strip().str.lower().str.replace(' ', '_')
combined_df.replace([np.inf, -np.inf], np.nan, inplace=True)
combined_df.dropna(inplace=True)

# Encode Labels (0 for BENIGN, 1 for Attack)
combined_df["label"] = np.where(combined_df["label"] == "BENIGN", 0, 1)

print("⚖️ Normalizing and Splitting Data...")
min_max_scaler = MinMaxScaler()

# 78 Features (Drop label)
X = combined_df.drop(columns=['label']) 
X = min_max_scaler.fit_transform(X)
y = combined_df['label'].values

# Save the scaler for FastAPI
joblib.dump(min_max_scaler, "scaler.pkl")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
# Train ONLY on Normal traffic (Unsupervised learning)
X_train_normal = X_train[y_train == 0]

# Convert to PyTorch Tensors
train_tensor = torch.tensor(X_train_normal, dtype=torch.float32)
test_tensor = torch.tensor(X_test, dtype=torch.float32)
train_loader = DataLoader(TensorDataset(train_tensor, train_tensor), batch_size=256, shuffle=True)

# ===========================
# 2. PyTorch Autoencoder Model
# ===========================
class Autoencoder(nn.Module):
    def __init__(self, latent_dim=16, input_dim=78):
        super(Autoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, latent_dim),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim),
            nn.Sigmoid()
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

# ===========================
# 3. Training Loop with W&B
# ===========================
print("🧠 Training PyTorch Autoencoder...")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = Autoencoder(latent_dim=16).to(device)
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# INITIALISATION W&B
wandb.init(project="ids-autoencoder-pytorch", name="entrainement-modele")

epochs = 10
for epoch in range(epochs):
    model.train()
    train_loss = 0
    for batch_x, _ in train_loader:
        batch_x = batch_x.to(device)
        optimizer.zero_grad()
        outputs = model(batch_x)
        loss = criterion(outputs, batch_x)
        loss.backward()
        optimizer.step()
        train_loss += loss.item()
    
    avg_loss = train_loss / len(train_loader)
    print(f"Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.6f}")
    
    # ENVOYER LA LOSS À W&B
    wandb.log({"epoch": epoch + 1, "train_loss": avg_loss})

# Save the PyTorch Model
torch.save(model.state_dict(), "autoencoder.pth")
print("✅ Model weights saved to autoencoder.pth")

# ===========================
# 4. Evaluation & Threshold
# ===========================
print("📊 Evaluating Model & Calculating Threshold...")
model.eval()
with torch.no_grad():
    train_preds = model(train_tensor.to(device)).cpu().numpy()
    train_error = np.mean(np.square(X_train_normal - train_preds), axis=1)
    
    # Calculate and save Threshold
    threshold = np.mean(train_error) + np.std(train_error)
    with open("model_config.json", "w") as f:
        json.dump({"threshold": float(threshold)}, f)
        
    print(f"🎯 Calculated Threshold (Seuil d'alerte) : {threshold}")
    
    test_preds = model(test_tensor.to(device)).cpu().numpy()
    reconstruction_error = np.mean(np.square(X_test - test_preds), axis=1)

# Calcul des prédictions (1 = Attack, 0 = Normal)
predictions = (reconstruction_error > threshold).astype(int)

# Calcul du ROC AUC (pour correspondre au rapport !)
auc_score = roc_auc_score(y_test, reconstruction_error)

# Envoyer les metrics finales à W&B
wandb.log({
    "threshold": threshold,
    "roc_auc_score": auc_score
})

print("\n📈 ROC AUC Score:", round(auc_score, 4))
print("\n📝 Classification Report:\n", classification_report(y_test, predictions))

# Fin de la session W&B
wandb.finish()