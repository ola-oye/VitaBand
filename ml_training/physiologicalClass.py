import numpy as np
import pandas as pd

np.random.seed(42)
n_samples = 50000

states = [
    "Normal",
    "Stressed",
    "Fatigued",
    "Dehydrated",
    "Low oxygen state",
    "Possible fever",
    "Overexertion",
]

def generate_physiological_sample(state):
    # Baseline healthy human
    body_temp = np.random.normal(36.8, 0.3)
    heart_rate = np.random.normal(70, 8)
    spo2 = np.random.normal(97, 1)
    accel = np.random.normal(0.1, 0.05, 3)
    gyro = np.random.normal(10, 5, 3)
    ambient_temp = np.random.normal(28, 5)
    pressure = np.random.normal(1013, 10)
    humidity = np.random.uniform(30, 80)

    # State-specific adjustments
    if state == "Normal":
        pass

    elif state == "Stressed":
        heart_rate = np.random.normal(95, 12)
        accel = np.random.normal(0.15, 0.07, 3)

    elif state == "Fatigued":
        heart_rate = np.random.normal(60, 6)
        spo2 = np.random.normal(94, 1.5)
        accel = np.random.normal(0.05, 0.03, 3)

    elif state == "Dehydrated":
        heart_rate = np.random.normal(100, 10)
        body_temp = np.random.normal(37.6, 0.4)

    elif state == "Low oxygen state":
        spo2 = np.random.normal(88, 4)
        heart_rate = np.random.normal(105, 12)

    elif state == "Possible fever":
        body_temp = np.random.normal(38.5, 0.5)
        heart_rate = np.random.normal(95, 10)

    elif state == "Overexertion":
        heart_rate = np.random.normal(160, 20)
        body_temp = np.random.normal(38.2, 0.4)
        accel = np.random.normal(2.5, 0.7, 3)
        spo2 = np.random.normal(93, 2)

    return [
        body_temp,
        ambient_temp,
        pressure,
        humidity,
        *accel,
        *gyro,
        heart_rate,
        spo2,
        state
    ]
# Generate datase
data = [generate_physiological_sample(np.random.choice(states)) for _ in range(n_samples)]

columns = [
    "body_temp", "ambient_temp", "pressure_hpa", "humidity_pct",
    "accel_x", "accel_y", "accel_z",
    "gyro_x", "gyro_y", "gyro_z",
    "heart_rate_bpm", "spo2_pct",
    "physio_state"
]

df = pd.DataFrame(data, columns=columns)
df = df.round(2)
# Sensor-safe clippin
df["body_temp"] = df["body_temp"].clip(30, 42)
df["ambient_temp"] = df["ambient_temp"].clip(-20, 60)
df["heart_rate_bpm"] = df["heart_rate_bpm"].clip(30, 220)
df["spo2_pct"] = df["spo2_pct"].clip(70, 100)

df.to_csv("edge_physio_state_dataset.csv", index=False)

print("Physiological state dataset saved.")
