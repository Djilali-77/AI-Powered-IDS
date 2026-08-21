import os
import glob
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras import layers, losses
from tensorflow.keras.models import Model
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import wandb
from wandb.keras import WandbMetricsLogger

#===========================
# 0. Kaggle Download & Setup
#===========================
print("Data from Kaggle : ")
os.system("mkdir -p dataset")
os.system("kaggle datasets download -d chethuhn/network-intrusion-dataset -p ./dataset")
os.system("unzip -q -o ./dataset/network-intrusion-dataset.zip -d ./dataset/")

#===========================
# 1. Weights & Biases Init
#===========================
wandb.init(
    project="ai-powered-ids",
    name="autoencoder-run-1",
    config={
        "latent_dim": 16,
        "epochs": 10,
        "batch_size": 256
    }
)
config = wandb.config

#===========================
# 2. Data Loading & Cleaning
#===========================
print("Prepare data : ")
all_files = glob.glob("./dataset/*.csv")
df_list = [pd.read_csv(filename) for filename in all_files]
combined_df = pd.concat(df_list, ignore_index=True)

combined_df.columns = combined_df.columns.str.strip().str.lower().str.replace(' ', '_')
combined_df.replace([np.inf, -np.inf], np.nan, inplace=True)
combined_df.dropna(inplace=True)
combined_df["label"] = np.where(combined_df["label"] == "BENIGN", 0, 1)

print("Normalisation et Split : ")
min_max_scaler = MinMaxScaler()
X = combined_df.drop(columns=['label']) 
X = min_max_scaler.fit_transform(X)
y = combined_df['label']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
X_train_normal = X_train[y_train == 0]

#===========================
# 3. Autoencoder Model
#===========================
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

print("Train model : ")
autoencoder = Autoencoder(latent_dim=config.latent_dim)
autoencoder.compile(optimizer='adam', loss=losses.MeanSquaredError())

autoencoder.fit(X_train_normal, X_train_normal,
                epochs=config.epochs,
                batch_size=config.batch_size,
                shuffle=True,
                validation_data=(X_test, X_test),
                callbacks=[WandbMetricsLogger()])

#===========================
# 4. Evaluation & Threshold
#===========================
print("Calculate error and accurancy : ")
X_reconstructed = autoencoder.predict(X_test)
reconstruction_error = np.mean(np.square(X_test - X_reconstructed), axis=1)

X_train_reconstructed = autoencoder.predict(X_train_normal)
train_error = np.mean(np.square(X_train_normal - X_train_reconstructed), axis=1)

threshold = np.mean(train_error) + np.std(train_error)
print(f"Threshold (Seuil d'alerte) : {threshold}")

predictions = reconstruction_error > threshold

print("\nAccuracy Score:", accuracy_score(y_test, predictions))
print("\nConfusion Matrix:\n", confusion_matrix(y_test, predictions))
print("\nClassification Report:\n", classification_report(y_test, predictions))

wandb.finish()