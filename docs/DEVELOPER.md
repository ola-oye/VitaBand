## VitaBand — Developer Notes & Architecture

This document helps developers understand the internal structure, key classes and
how the pieces fit together. It also lists a few suggested improvements.

Core components

- SensorManager (`app/sensor_manager.py`)
  - Starts sensor scripts (subprocesses) located in `sensors/`.
  - Reads each subprocess stdout, parses lines, and updates an in-memory buffer.
  - Exposes `read_all_sensors()` returning a dictionary of features expected by ML models.
  - Feature list:
    - body_temp, ambient_temp, pressure_hpa, humidity_pct,
    - accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z,
    - heart_rate_bpm, spo2_pct

- ML model wrapper (`app/generic_inferenceEngine.py`)
  - Loads a trained model, a scaler and a label encoder from joblib files.
  - Provides a `predict()` method that accepts the sensor_data dictionary and returns active labels.

- Recommendation engine (`app/recommendation_engine.py`)
  - Converts a set of labels and feature values into a natural-language recommendation
    (summary, priority and a human-readable full_message).

- MQTT publisher (`app/mqtt_publisher.py`)
  - Publishes JSON summaries and recommendations to configurable topics.

Entry points

- `app/inferenceEngine.py` — main runtime for live deployments (starts sensors, loads models, publishes via MQTT)
- `test/main.py` — a simplified harness that reads `test/sensor_data.json` and runs predictions for demo/testing

Model artifacts

- Trained models, scalers and label encoders are stored in `model/` as joblib files.
- Filenames used by the live app are `edge_*_*.joblib` for model, scaler and label encoder.

Feature ordering and compatibility

- The inference code expects features in an exact order (see `feature_names` in `inferenceEngine.py` and test harnesses). When training, ensure your feature CSV matches this ordering.

Developer checklist when changing models or features

1. Update `FEATURE_COLS` in training script to match the features used by the edge app.
2. Retrain models and save scaler & label encoder alongside model artifact.
3. Place the artifacts in `model/` and ensure filenames match the loader in the edge script you plan to run.


Security & deployment notes

- For deployment beyond a trusted network, enable authenticated and encrypted MQTT (TLS + username/password).
- Consider trimming logs and limiting retained historical data to avoid leaking user health information.

