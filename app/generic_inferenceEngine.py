#!/usr/bin/env python3
"""
ML Model Class - Create abstraction layer around trained ML artifacts

Provides a MLModel class that:
1. Load Model artifacts
2. Accept sensor data 
3. Provides predict() method that returns list of native label

"""

import joblib
import numpy as np

class MLModel:
    def __init__(self, model_path, scaler_path, label_encoder_path, name="model"):
        self.name = name

        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        self.label_encoder = joblib.load(label_encoder_path)

        print(f"   ✓ {name} model loaded")

    def predict(self, features, feature_order):
        """
        Prediction:
        features: dict of sensor data
        feature_order: list defining feature order
        """
        # Extract features in the exact order expected by the model
        X = np.array([features[f] for f in feature_order], dtype=float).reshape(1, -1)
        #Scale
        X_scaled = self.scaler.transform(X)

        #Predict
        raw_pred = self.model.predict(X_scaled)

        # Handle probabilistic / encoded outputs
        try:
            decoded = self.label_encoder.inverse_transform(raw_pred)
            return decoded.tolist()
        except Exception:
            return raw_pred.tolist()
