## VitaBand — Usage Guide

This document shows quick steps to run VitaBand in test mode (no hardware) and in live mode
with sensors connected. It also includes notes to troubleshoot common issues.

Setup (one-time)

1. Create and activate a virtual environment, then install requirements:

   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt

2. Ensure model artifacts exist under `model/`:

   The edge app loads joblib files (model, scaler and encoder). Standard filenames in
   this repo use the `edge_*_*.joblib` pattern (e.g. `edge_activity_dataset_model.joblib`).

Running in simulation / test mode (no sensors)

- Purpose: validate inference + recommendation pipeline using recorded sensor samples.
- Script: `test/main.py`

From the repo root:

   python3 test/main.py

Notes:
- `test/main.py` looks for `sensor_data.json` in the current working directory (the `test/` folder).
- It also expects model and scaler files under `model/`. If you see "model not found" errors, check
  the model filenames and either rename them to match or change the `model_path`/`scaler_path` values
  in the script.

Live mode (with sensors attached to a Raspberry Pi)

- Purpose: launch the full edge application; it starts the sensor subprocesses and publishes via MQTT.
- Script: `app/inferenceEngine.py`

From the repo root:

   python3 app/inferenceEngine.py

Important runtime behavior:
- `app/inferenceEngine.py` starts `SensorManager` which launches sensor scripts from `sensors/` as subprocesses.
- If a sensor script is missing, it will be skipped and the manager uses default values until real readings arrive.
- MQTT publishing defaults to `localhost`. To broadcast to another broker, edit the `mqtt_broker` parameter
  or modify the script.

Available sensor scripts (examples):

- `sensors/max30102-master/max30102_sensor.py` — reads PPG/HR/SpO2 and prints JSON lines
- `sensors/bme280_sensor.py` — prints ambient temperature, humidity and pressure
- `sensors/mpu6050_sensor.py` — prints accelerometer and gyro lines
- `sensors/temp_ds18b20_sensor.py` — prints body/skin temperature

Logging and CSV output

- The live monitor writes CSV logs into the `data/` folder (filename includes UTC timestamp).

MQTT topics

- vitaband/vitals — published health summary (JSON)
- vitaband/explanation — plain-English recommendations
- vitaband/device/status — status and heartbeat

Troubleshooting

- "Missing sensor keys" — indicates SensorManager didn't supply all expected features. Check sensor subprocess logs and ensure scripts are executable.
- "Model not found" — verify model files exist in `model/` and match names expected in the script you run.
- MQTT connection fails — ensure a broker is running (e.g., mosquitto) and reachable on the host/port configured.
