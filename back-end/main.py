from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import torch
import torch.nn as nn
import joblib
import json

app = FastAPI(title="AI-Powered IDS API (PyTorch)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PyTorch Model Definition (Must be exactly the same as in train_model.py)
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
        return self.decoder(self.encoder(x))

# Load Model, Scaler, and Config
try:
    model = Autoencoder(latent_dim=16)
    model.load_state_dict(torch.load("autoencoder.pth", map_location=torch.device('cpu')))
    model.eval() # Important: set to evaluation mode
    
    scaler = joblib.load("scaler.pkl")
    
    with open("model_config.json", "r") as f:
        config = json.load(f)
        THRESHOLD = config["threshold"]
        
    print("[INFO] Model, Scaler, and Threshold loaded successfully!")
except Exception as e:
    print(f"[ERROR] Loading files failed: {e}")
    THRESHOLD = 0.08 # Fallback just in case

class TrafficData(BaseModel):
    features: list[float]

@app.post("/predict")
def predict_traffic(data: TrafficData):
    features_array = np.array([data.features])
    
    if features_array.shape[1] != 78:
        return {"error": f"Expected 78 features, got {features_array.shape[1]}"}
    
    # 1. Scale the input data ! (Very Important)
    scaled_features = scaler.transform(features_array)
    
    # 2. Convert to PyTorch Tensor
    tensor_data = torch.tensor(scaled_features, dtype=torch.float32)
    
    # 3. Predict & Calculate Error
    with torch.no_grad():
        reconstructed = model(tensor_data)
        
    # Calculate MSE
    error = torch.mean((tensor_data - reconstructed) ** 2).item()
    
    is_attack = error > THRESHOLD
    
    return {
        "reconstruction_error": error,
        "threshold": THRESHOLD,
        "status": "Attack Detected 🚨" if is_attack else "Normal Traffic ✅",
        "danger": is_attack
    }

@app.get("/")
def home():
    return {"message": "PyTorch IDS Backend is running smoothly!"}