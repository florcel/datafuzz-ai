# training/sdv/__init__.py

"""
This module contains the implementation of training methods using the Synthetic Data Vault (SDV).
"""

# Import necessary libraries and modules for SDV training
from sdv import SDV
from sdv.metadata import Metadata

# Define the main SDV training class
class SDVTrainer:
    def __init__(self, metadata: Metadata):
        self.metadata = metadata
        self.sdv_model = SDV(metadata)

    def fit(self, data):
        """Fit the SDV model to the provided data."""
        self.sdv_model.fit(data)

    def sample(self, num_samples: int):
        """Generate synthetic samples using the fitted SDV model."""
        return self.sdv_model.sample(num_samples)

    def save(self, filepath: str):
        """Save the trained SDV model to a file."""
        self.sdv_model.save(filepath)

    def load(self, filepath: str):
        """Load a trained SDV model from a file."""
        self.sdv_model = SDV.load(filepath)