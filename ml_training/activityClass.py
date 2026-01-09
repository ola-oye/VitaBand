import numpy as np
import pandas as pd

np.random.seed(42)
n_samples = 50000

# -----------------------------
# Activity classes (Model A)
# -----------------------------
activities = ["Sleeping", "Resting", "Walking", "Running", "Sedentary"]

def generate_sample(activity):
    # Defaults (normal resting human)
    body_temp = np.random.normal(36.8, 0.3)
    spo2 = np.random.normal(97, 1)
    humidity = np.random.uniform(30, 80)
    pressure = np.random.normal(1013, 10)

    if activity == "Sleeping":
        hr = np.random.normal(50, 5)
        accel = np.random.normal(0.05, 0.03, 3)
        gyro = np.random.normal(5, 3, 3)

    elif activity == "Resting":
        hr = np.random.normal(65, 8)
        accel = np.random.normal(0.1, 0.05, 3)
        gyro = np.random.normal(10, 5, 3)

    elif activity == "Walking":
        hr = np.random.normal(95, 10)
        accel = np.random.normal(1.2, 0.4, 3)
        gyro = np.random.normal(120, 40, 3)

    elif activity == "Running":
        hr = np.random.normal(150, 20)
        accel = np.random.normal(3.0, 0.8, 3)
        gyro = np.random.normal(400, 120, 3)

    elif activity == "Sedentary":
        hr = np.random.normal(70, 6)
        accel = np.random.normal(0.08, 0.04, 3)
        gyro = np.random.normal(8, 4, 3)

    ambient_temp = np.random.normal(28, 6)

    return [
        body_temp,
        ambient_temp,
        pressure,
        humidity,
        *accel,
        *gyro,
        hr,
        spo2,
        activity
    ]

# -----------------------------
# Generate dataset
# -----------------------------
data = [generate_sample(np.random.choice(activities)) for _ in range(n_samples)]

columns = [
    "body_temp", "ambient_temp", "pressure_hpa", "humidity_pct",
    "accel_x", "accel_y", "accel_z",
    "gyro_x", "gyro_y", "gyro_z",
    "heart_rate_bpm", "spo2_pct",
    "activity_label"
]

df = pd.DataFrame(data, columns=columns)
df = df.round(2)

# Clip to sensor-safe ranges (important for edge stability)
df["body_temp"] = df["body_temp"].clip(30, 42)
df["ambient_temp"] = df["ambient_temp"].clip(-20, 60)
df["heart_rate_bpm"] = df["heart_rate_bpm"].clip(30, 220)
df["spo2_pct"] = df["spo2_pct"].clip(70, 100)

df.to_csv("edge_activity_dataset.csv", index=False)
print("Edge classification dataset saved.")
