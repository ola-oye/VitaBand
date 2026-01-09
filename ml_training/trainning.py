#!/usr/bin/env python3
"""
Multi-Label Activity Classification - Data Analysis & Preparation
Analyzes synthetic sensor data and prepares it for training
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.multioutput import MultiOutputClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    hamming_loss, accuracy_score, f1_score, 
    classification_report, multilabel_confusion_matrix
)
import joblib   # ← Joblib import
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)


class MultiLabelDataAnalyzer:
    """Analyze and visualize multi-label dataset"""
    
    def __init__(self, filepath):
        """Load dataset"""
        self.df = pd.read_csv(filepath)
        print(f"Dataset loaded: {self.df.shape[0]} samples, {self.df.shape[1]} columns")
        
        self.feature_cols = [
            "body_temp", "ambient_temp", "pressure_hpa", "humidity_pct",
            "accel_x", "accel_y", "accel_z",
            "gyro_x", "gyro_y", "gyro_z",
            "heart_rate_bpm", "spo2_pct"
        ]
        self.label_cols = [col for col in self.df.columns if col not in self.feature_cols]

    def basic_stats(self):
        print("\n" + "="*70)
        print("BASIC STATISTICS")
        print("="*70)
        
        print("\n--- Feature Statistics ---")
        print(self.df[self.feature_cols].describe())
        
        print("\n--- Label Distribution ---")
        label_counts = self.df[self.label_cols].sum().sort_values(ascending=False)
        print(label_counts)
        
        labels_per_sample = self.df[self.label_cols].sum(axis=1)
        print(f"\nAverage labels per sample: {labels_per_sample.mean():.2f}")
        print("Label count distribution:")
        print(labels_per_sample.value_counts().sort_index())

    def check_data_quality(self):
        print("\n" + "="*70)
        print("DATA QUALITY CHECK")
        print("="*70)

        missing = self.df.isnull().sum()
        if missing.sum() == 0:
            print("✓ No missing values found")
        else:
            print("Missing values:")
            print(missing[missing > 0])

    def visualize_distributions(self):
        print("\n" + "="*70)
        print("GENERATING VISUALIZATIONS")
        print("="*70)

        fig, axes = plt.subplots(3, 4, figsize=(16, 10))
        axes = axes.ravel()
        
        for idx, feat in enumerate(self.feature_cols):
            axes[idx].hist(self.df[feat], bins=50, edgecolor='black', alpha=0.7)
            axes[idx].set_title(feat)

        plt.tight_layout()
        plt.savefig('feature_distributions.png')
        plt.close()


class MultiLabelClassifierTrainer:

    def __init__(self, df, feature_cols, label_cols):
        self.df = df
        self.feature_cols = feature_cols
        self.label_cols = label_cols
        self.scaler = StandardScaler()
        
    def prepare_data(self, test_size=0.2, random_state=42):
        print("\n" + "="*70)
        print("DATA PREPARATION")
        print("="*70)
        
        X = self.df[self.feature_cols].values
        y = self.df[self.label_cols].values
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        return X_train_scaled, X_test_scaled, y_train, y_test
    
    def train_random_forest(self, X_train, y_train):
        print("\n--- Training Random Forest Classifier ---")
        
        rf_classifier = MultiOutputClassifier(
            RandomForestClassifier(
                n_estimators=100,
                max_depth=20,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
        )
        
        rf_classifier.fit(X_train, y_train)
        return rf_classifier
    
    def train_mlp(self, X_train, y_train):
        print("\n--- Training MLP Neural Network ---")
        
        mlp_classifier = MLPClassifier(
            hidden_layer_sizes=(128, 64, 32),
            activation='relu',
            solver='adam',
            max_iter=200,
            random_state=42,
            early_stopping=True
        )
        
        mlp_classifier.fit(X_train, y_train)
        return mlp_classifier
    
    def evaluate_model(self, model, X_test, y_test, model_name="Model"):
        print("\n" + "="*70)
        print(f"{model_name.upper()} EVALUATION")
        print("="*70)
        
        y_pred = model.predict(X_test)
        
        print(f"Hamming Loss: {hamming_loss(y_test, y_pred):.4f}")
        print(f"Micro F1 Score: {f1_score(y_test, y_pred, average='micro'):.4f}")
        print(f"Macro F1 Score: {f1_score(y_test, y_pred, average='macro'):.4f}")
        
        return y_pred
    
    def save_preprocessor(self, filename='scaler.joblib'):
        joblib.dump(self.scaler, filename)
        print(f"✓ Scaler saved to {filename}")


def main():
    print("\n" + "="*70)
    print("MULTI-LABEL ACTIVITY CLASSIFICATION - DATA ANALYSIS & TRAINING")
    print("="*70)
    
    analyzer = MultiLabelDataAnalyzer('synthetic_activity_50k_multilabel.csv')
    analyzer.basic_stats()
    analyzer.check_data_quality()
    
    trainer = MultiLabelClassifierTrainer(
        analyzer.df, analyzer.feature_cols, analyzer.label_cols
    )
    
    X_train, X_test, y_train, y_test = trainer.prepare_data()
    
    # Train RF
    rf_model = trainer.train_random_forest(X_train, y_train)
    trainer.evaluate_model(rf_model, X_test, y_test, "Random Forest")

    # Train MLP
    mlp_model = trainer.train_mlp(X_train, y_train)
    trainer.evaluate_model(mlp_model, X_test, y_test, "Neural Network")

    # Save scaler and models (Joblib)
    trainer.save_preprocessor("scaler.joblib")

    joblib.dump(rf_model, "rf_model.joblib")
    print("✓ Random Forest model saved to rf_model.joblib")

    joblib.dump(mlp_model, "mlp_model.joblib")
    print("✓ Neural Network model saved to mlp_model.joblib")
    
    print("\nTRAINING COMPLETE")


if __name__ == "__main__":
    main()

