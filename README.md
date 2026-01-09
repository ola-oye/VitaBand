# VitaBand

VitaBand is a prototype wearable IoT health system that collects physiological and
environmental signals from multiple sensors, performs local preprocessing and
lightweight ML inference on an edge device (e.g., Raspberry Pi), and publishes
human-friendly summaries and recommendations over MQTT.

This repository contains:

- app/: Edge application code (sensor manager, inference, MQTT, recommendation engine)
- sensors/: Sensor-specific drivers and helper scripts (MAX30102, BME280, MPU6050, DS18B20)
- ml_training/: Training utilities and datasets used to train lightweight models
- model/: Trained model/scaler/encoder artifacts (joblib files)
- test/: Example/test scripts and sample sensor data

Quick links:

- Usage & examples: docs/USAGE.md
- Developer notes & architecture: docs/DEVELOPER.md
- Requirements: requirements.txt

## Quick start (development)

1. Create a virtual environment and install dependencies:

	 python3 -m venv .venv
	 source .venv/bin/activate
	 pip install --upgrade pip
	 pip install -r requirements.txt

2. Run in simulation/test mode (no hardware required):

	 - The test harness is in `test/main.py`. It expects a model/scaler file under
		 `model/` and `test/sensor_data.json` to exist. Adjust model filenames if needed.

	 Example (from repo root):
	 python3 test/main.py

3. Run on a Raspberry Pi with sensors connected:

	 - Start the main monitor (this will spawn the per-sensor subprocesses from
		 the `sensors/` folder):

		 python3 app/inferenceEngine.py

	 - The app will attempt to connect to an MQTT broker at localhost by default and
		 will optionally advertise via mDNS. See `app/inferenceEngine.py` for CLI hooks.

## Model training

Training utilities live in `ml_training/`. A simple training script `trainning.py`
creates RandomForest models, scalers and label encoders and saves them as
joblib artifacts. Example usage (from repo root):

	 python3 ml_training/trainning.py

This script expects CSV datasets from the `ml_training/` folder. After training,
copy or move the produced `*_model.joblib`, `*_scaler.joblib`, and
`*_label_encoder.joblib` files into the `model/` directory so the edge app can load
them.

Note: Some test/code paths expect different artifact names (e.g., `rf_model.joblib`).
If you get "model not found" errors, either rename the trained files or update
the path inside the corresponding script.

## Project structure (high level)

- app/
	- inferenceEngine.py      # Live monitoring: uses SensorManager and ML models
	- generic_inferenceEngine.py # Generic ML model wrapper used by inferenceEngine
	- sensor_manager.py       # Starts sensor subprocesses and provides read_all_sensors()
	- recommendation_engine.py# Rule-based interpreter for ML outputs
	- mqtt_publisher.py       # MQTT publishing helper
	- mdns_service.py         # Optional service discovery
- sensors/                  # Sensor-specific scripts and drivers
- ml_training/              # Training data and scripts
- model/                    # Trained model artifacts (joblib)
- test/                     # Test harness and sample sensor data

## MQTT topics (used by app)

- vitaband/vitals — periodic JSON summary of vitals
- vitaband/explanation — plain-English recommendations
- vitaband/device/status — device heartbeat/status messages

## Known notes & next steps

- The codebase mixes a few test/demo entry points that expect different model
	filenames. If you plan to run tests, confirm the model artifact names match what
	the test script expects or update the script.
- Add simple unit tests for feature extraction and the recommendation engine.
- Consider documenting the expected JSON payload shapes for each MQTT topic.

## Where to find more information

See the docs directory for step-by-step usage and developer notes:

- docs/USAGE.md
- docs/DEVELOPER.md