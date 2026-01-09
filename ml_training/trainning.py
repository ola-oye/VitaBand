#!/usr/bin/env python3
"""
Unified Training Script for Edge Inference Models

Models:
- Model A: Activity Classification
- Model B: Physiological State Classification
- Model C: Risk / Severity Classification

All models:
- Single-label, multi-class
- Share same sensor feature space
- Edge-deployment friendly
"""

import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report


# CONFIGURATION
RANDOM_STATE = 42
TEST_SIZE = 0.2

FEATURE_COLS = [
    "body_temp", "ambient_temp", "pressure_hpa", "humidity_pct",
    "accel_x", "accel_y", "accel_z",
    "gyro_x", "gyro_y", "gyro_z",
    "heart_rate_bpm", "spo2_pct"
]

MODELS = {
    "edge_physiological_state_dataset": {
        "csv": "edge_physio_state_dataset.csv",
        "label": "physio_state"
    }
}

# DATA PREPARATION
def load_prepare_data(csv_file, label_col):
    df = pd.read_csv(csv_file)

    # Ensure sensor realism
    X = df[FEATURE_COLS].round(2).values
    y = df[label_col].values

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y_encoded,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y_encoded
    )

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    return X_train, X_test, y_train, y_test, scaler, label_encoder

# TRAINING
def train_and_evaluate(model_name, csv_file, label_col):
    print(f"\n{'='*70}")
    print(f"TRAINING {model_name.upper()}")
    print(f"{'='*70}")

    X_train, X_test, y_train, y_test, scaler, encoder = load_prepare_data(
        csv_file, label_col
    )

    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=16,
        min_samples_split=5,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print("Accuracy:", accuracy_score(y_test, y_pred))
    print(classification_report(
        y_test,
        y_pred,
        target_names=encoder.classes_
    ))

    # Save artifacts for edge inference
    joblib.dump(model, f"{model_name}_model.joblib")
    joblib.dump(scaler, f"{model_name}_scaler.joblib")
    joblib.dump(encoder, f"{model_name}_label_encoder.joblib")

    print(f"✓ Saved {model_name}_model.joblib")
    print(f"✓ Saved {model_name}_scaler.joblib")
    print(f"✓ Saved {model_name}_label_encoder.joblib")

# MAIN
def main():
    print("\nEDGE AI TRAINING PIPELINE STARTED")

    for model_name, cfg in MODELS.items():
        train_and_evaluate(
            model_name,
            cfg["csv"],
            cfg["label"]
        )

    print("\n✓ ALL MODELS TRAINED AND SAVED SUCCESSFULLY")

if __name__ == "__main__":
    main()