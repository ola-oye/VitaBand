#!/usr/bin/env python3
"""
Sensor Manager CSV Logger

- Reads sensor data via SensorManager
- Prints formatted readings to terminal
- Appends readings to CSV file (ML-ready)

Recommended for:
- Dataset collection
- Edge inference validation
- Model training
"""

import time
import os
import csv
from datetime import datetime
from app.sensor_manager import SensorManager


# FILE CONFIGURATION

CSV_FILENAME = "sensor_data.csv"

FEATURE_COLS = [
    "body_temp",
    "ambient_temp",
    "pressure_hpa",
    "humidity_pct",
    "accel_x",
    "accel_y",
    "accel_z",
    "gyro_x",
    "gyro_y",
    "gyro_z",
    "heart_rate_bpm",
    "spo2_pct",
]


# CSV LOGICS
def init_csv_file(filename):
    """Create CSV file with headers if it does not exist."""
    if not os.path.exists(filename):
        with open(filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["timestamp"] + FEATURE_COLS)


def append_csv_row(filename, timestamp, readings):
    """Append one row of sensor readings to CSV."""
    row = [timestamp] + [readings.get(col, None) for col in FEATURE_COLS]

    with open(filename, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(row)


def main():
    print("_" * 60)
    print("RUNNING SENSOR MANAGER (CSV LOGGER)")
    print("_" * 60)

    print(f"Logging to CSV: {CSV_FILENAME}")

    # Ensure CSV exists
    init_csv_file(CSV_FILENAME)

    manager = None
    reading_count = 0

    try:
        manager = SensorManager()

        print("\nWaiting for sensors to stabilize...")
        time.sleep(5)

        print("\n" + "_" * 60)
        print("READING SENSOR DATA (Ctrl+C to stop)")
        print("_" * 60)

        while True:
            readings = manager.read_all_sensors()
            status = manager.get_sensor_status()

            timestamp = datetime.now().isoformat()
            reading_count += 1

            # Save CSV row
            append_csv_row(CSV_FILENAME, timestamp, readings)

            # PRINT OUTPUT
            print("\n" + "_" * 60)
            print(f"TIMESTAMP: {timestamp}")
            print(f"READING #: {reading_count}")
            print("_" * 60)

            print("\n TEMPERATURE & ENVIRONMENT:")
            print(f"  Body Temp:      {readings.get('body_temp', 0):.1f} °C")
            print(f"  Ambient Temp:   {readings.get('ambient_temp', 0):.1f} °C")
            print(f"  Pressure:       {readings.get('pressure_hpa', 0):.1f} hPa")
            print(f"  Humidity:       {readings.get('humidity_pct', 0):.1f} %")

            if all(k in readings for k in ["accel_x", "accel_y", "accel_z"]):
                print("\n MOTION (Accelerometer):")
                print(f"  X: {readings['accel_x']:+.2f} g")
                print(f"  Y: {readings['accel_y']:+.2f} g")
                print(f"  Z: {readings['accel_z']:+.2f} g")

            if all(k in readings for k in ["gyro_x", "gyro_y", "gyro_z"]):
                print("\n POSITION (Gyroscope):")
                print(f"  X: {readings['gyro_x']:+.1f} °/s")
                print(f"  Y: {readings['gyro_y']:+.1f} °/s")
                print(f"  Z: {readings['gyro_z']:+.1f} °/s")

            print("\n HEALTH VITALS:")
            print(f"  Heart Rate: {readings.get('heart_rate_bpm', 0):.0f} BPM")
            print(f"  SpO2:       {readings.get('spo2_pct', 0):.1f} %")

            active = sum(status.values())
            total = len(status)
            print(f"\n SENSORS ACTIVE: {active}/{total}")

            time.sleep(3)

    except KeyboardInterrupt:
        print("\nStopping sensor readings...")
        print(f"Total CSV records written: {reading_count}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if manager:
            manager.close()
        print("\nLogger stopped cleanly.")


if __name__ == "__main__":
    main()