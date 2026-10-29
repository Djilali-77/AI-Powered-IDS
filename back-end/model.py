"""Shared model definition and preprocessing used by both training and the API."""

import numpy as np
import torch.nn as nn


class Autoencoder(nn.Module):
    """Symmetric fully-connected autoencoder for tabular network-flow features."""

    def __init__(self, input_dim: int = 78, hidden_dim: int = 64, latent_dim: int = 16) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, latent_dim),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
            nn.Sigmoid(),
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))


def log_transform(x: np.ndarray) -> np.ndarray:
    """Signed log1p transform.

    Network-flow features (durations, byte counts, ...) are extremely heavy-tailed.
    Min-max scaling alone squeezes most values close to 0, so we compress the
    range first. The sign is preserved because some features contain -1 / negatives.
    """
    return np.sign(x) * np.log1p(np.abs(x))