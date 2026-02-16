"""
Unsupervised baseline learner - learns network's normality WITHOUT labels
Uses denoising autoencoder to model normal traffic distribution
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from sklearn.preprocessing import StandardScaler
from typing import Tuple
import logging

logger = logging.getLogger("BaselineLearner")

class AdaptiveAutoencoder(nn.Module):
    """Denoising autoencoder for anomaly detection"""
    def __init__(self, input_dim: int = 85):
        super().__init__()
        # Encoder: 85 → 64 → 32 → 16 (latent space)
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 16)
        )
        # Decoder: 16 → 32 → 64 → 85
        self.decoder = nn.Sequential(
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Linear(64, input_dim)
        )
    
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded, encoded

class BaselineLearner:
    def __init__(self, input_dim: int = 85, learning_rate: float = 1e-3):
        self.input_dim = input_dim
        self.model = AdaptiveAutoencoder(input_dim)
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
        self.scaler = StandardScaler()
        self.threshold = 0.5  # Will be learned from baseline data
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        logger.info(f"Intialized baseline learner on {self.device}")
    
    def prepare_data(self, flows: np.ndarray) -> Tuple[torch.Tensor, StandardScaler]:
        """Scale features and convert to tensors"""
        # Fit scaler on baseline traffic (represents "normal")
        self.scaler.fit(flows)
        scaled = self.scaler.transform(flows)
        tensor = torch.tensor(scaled, dtype=torch.float32).to(self.device)
        return tensor, self.scaler
    
    def train(self, flows: np.ndarray, epochs: int = 50, batch_size: int = 256):
        """
        UNSUPERVISED training - NO labels required
        Learns reconstruction of normal traffic patterns
        """
        logger.info(f"Starting UNSUPERVISED baseline learning on {len(flows)} flows...")
        
        # Prepare data
        train_tensor, _ = self.prepare_data(flows)
        dataset = TensorDataset(train_tensor)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        # Training loop
        self.model.train()
        for epoch in range(epochs):
            epoch_loss = 0
            for batch, in loader:
                # Add noise for denoising (improves robustness to minor variations)
                noise = torch.randn_like(batch) * 0.1
                noisy_batch = batch + noise
                
                self.optimizer.zero_grad()
                reconstructed, _ = self.model(noisy_batch)
                loss = self.criterion(reconstructed, batch)
                loss.backward()
                self.optimizer.step()
                epoch_loss += loss.item()
            
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}/{epochs} | Loss: {epoch_loss/len(loader):.6f}")
        
        # Calculate adaptive threshold from reconstruction errors
        self.threshold = self._calculate_threshold(train_tensor)
        logger.info(f"✓ Baseline learning complete! Adaptive threshold: {self.threshold:.4f}")
        return self.model, self.scaler, self.threshold
    
    def _calculate_threshold(self, tensor: torch.Tensor) -> float:
        """Calculate threshold as 95th percentile of reconstruction errors"""
        self.model.eval()
        with torch.no_grad():
            reconstructed, _ = self.model(tensor)
            errors = torch.mean((reconstructed - tensor) ** 2, dim=1)
        threshold = np.percentile(errors.cpu().numpy(), 95)
        return float(threshold)
    
    def predict(self, features: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Return reconstruction errors and anomaly scores"""
        self.model.eval()
        scaled = self.scaler.transform(features)
        tensor = torch.tensor(scaled, dtype=torch.float32).to(self.device)
        
        with torch.no_grad():
            reconstructed, _ = self.model(tensor)
            errors = torch.mean((reconstructed - tensor) ** 2, dim=1)
        
        errors_np = errors.cpu().numpy()
        scores = errors_np / self.threshold  # Normalized anomaly score
        return errors_np, scores