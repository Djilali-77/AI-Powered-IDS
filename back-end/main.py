from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, losses
from tensorflow.keras.models import Model

app = FastAPI(title="AI-Powered IDS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Autoencoder(Model):
    def __init__(self, latent_dim):
        super(Autoencoder, self).__init__()
        self.latent_dim = latent_dim   
        self.encoder = tf.keras.Sequential([
            layers.Dense(32, activation='relu'),
            layers.Dense(latent_dim, activation='relu'),
        ])
        self.decoder = tf.keras.Sequential([
            layers.Dense(32, activation='relu'),
            layers.Dense(78, activation='sigmoid')
        ])

    def call(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

latent_dimension = 16
autoencoder = Autoencoder(latent_dim=latent_dimension)
autoencoder(tf.random.normal([1, 78]))

try:
    autoencoder.load_weights("autoencoder.weights.h5")
    print("[INFO] Model weights loaded successfully!")
except Exception as e:
    print(f"[WARNING] Could not load weights: {e}")

THRESHOLD = 0.08 

class TrafficData(BaseModel):
    features: list[float]

@app.post("/predict")
def predict_traffic(data: TrafficData):
    features_array = np.array([data.features])
    
    if features_array.shape[1] != 78:
        return {"error": f"Expected 78 features, got {features_array.shape[1]}"}
    
    reconstructed = autoencoder.predict(features_array)
    error = float(np.mean(np.square(features_array - reconstructed)))
    
    is_attack = error > THRESHOLD
    
    return {
        "reconstruction_error": error,
        "threshold": THRESHOLD,
        "status": "Attack Detected!" if is_attack else "Normal Traffic",
        "danger": is_attack
    }

@app.get("/")
def home():
    return {"message": "AI-Powered IDS Backend is running smoothly!"}