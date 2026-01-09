import numpy as np
import pandas as pd

np.random.seed(42)
n_samples = 50000

risk_levels = [
    "Healthy",
    "Slight abnormality",
    "Warning",
    "Critical"
]

def generate_risk_sample(risk):
    # Baseline normal human
    body_temp = np.random.normal(36.8, 0.3)
    heart_rate = np.random.normal(70, 8)
    spo2 = np.random.normal(97, 1)
    accel = np.random.normal(0.1, 0.05, 3)
    gyro = np.random.normal(10, 5, 3)
    ambient_temp = np.random.normal(28, 5)
    pressure = np.random.normal(1013, 10)
    humidity = np.random.uniform(30, 80)

    if risk == "Healthy":
        pass

    elif risk == "Slight abnormality":
        body_temp = np.random.normal(37.5, 0.3)
        heart_rate = np.random.normal(90, 10)

    elif risk == "Warning":
        body_temp = np.random.normal(38.5, 0.4)
        heart_rate = np.random.normal(110, 15)
        spo2 = np.random.normal(92, 2)

    elif risk == "Critical":
        body_temp = np.random.normal(40.0, 0.6)
        heart_rate = np.random.normal(150, 20)
        spo2 = np.random.normal(85, 4)

    return [
        body_temp,
        ambient_temp,
        pressure,
        humidity,
        *accel,
        *gyro,
        heart_rate,
        spo2,
        risk
    ]

# Generate dataset
data = [generate_risk_sample(np.random.choice(risk_levels)) for _ in range(n_samples)]

columns = [
    "body_temp", "ambient_temp", "pressure_hpa", "humidity_pct",
    "accel_x", "accel_y", "accel_z",
    "gyro_x", "gyro_y", "gyro_z",
    "heart_rate_bpm", "spo2_pct",
    "risk_level"
]

df = pd.DataFrame(data, columns=columns)
df = df.round(2)

# Sensor-safe clipping
df["body_temp"] = df["body_temp"].clip(30, 42)
df["heart_rate_bpm"] = df["heart_rate_bpm"].clip(30, 220)
df["spo2_pct"] = df["spo2_pct"].clip(70, 100)
df["ambient_temp"] = df["ambient_temp"].clip(-20, 60)

df.to_csv("edge_risk_severity_dataset.csv", index=False)
print("Risk / severity dataset saved.")
