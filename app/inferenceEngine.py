#!/usr/bin/env python3
"""
Activity Monitor
Sensor Manager -> Model -> Recommendations -> (optional) MQTT / mDNS
"""
import sys
import os
import time
import csv
import joblib
from datetime import datetime
from typing import Dict, List, Any
import numpy as np


# Import sensor manager (required)
try:
    from sensor_manager import SensorManager
except ImportError:
    print("ERROR: sensor_manager.py not found! Make sure it is in the same directory.")
    sys.exit(1)

#Import Machine learn inference engine (required)
try:
    from generic_inferenceEngine import MLModel
except ImportError:
    print("ERROR: generic_inferenceEngine.py not found! Make sure it is in the same directory.")
    sys.exit(1)

# Import recommendation engine (required)
try:
    from recommendation_engine import RecommendationEngine
except ImportError:
    print("ERROR: recommendation_engine.py not found! Make sure it is in the same directory.")
    sys.exit(1)

# Import MQTT publisher
try:
    from mqtt_publisher import HealthMQTTPublisher
except ImportError:
    print("WARNING: mqtt_publisher.py not found. MQTT publishing disabled.")
    HealthMQTTPublisher = None

# Import mDNS service
try:
    from mdns_service import HealthMonitorService
except ImportError:
    print("WARNING: mdns_service.py not found. mDNS service disabled.")
    HealthMonitorService = None


class ActivityMonitor:
    """Main monitoring system that connects sensors to predictions."""

    def __init__(
        self,
        mqtt_enabled: bool = True,
        mqtt_broker: str = "localhost",
        mdns_enabled: bool = True,
    ):
        # ------ Initialization log ------
        print("=" * 70)
        print("INITIALIZING ACTIVITY MONITORING SYSTEM")
        print("=" * 70)

        # Sensor manager
        print("\n1) Initializing sensors...")
        try:
            self.sensor_manager = SensorManager()
            print("  Sensor manager initialized")
        except Exception as e:
            print(f"   Error initializing SensorManager: {e}")
            raise

        # Load scaler & model
        print("\n2) Loading ML artifacts...")
        base = os.path.join(os.path.dirname(__file__), "..", "model")
        try:
            self.activity_model = MLModel(
                model_path=os.path.join(base, "edge_activity_dataset_model.joblib"),
                scaler_path=os.path.join(base, "edge_activity_dataset_scaler.joblib"),
                label_encoder_path=os.path.join(base, "edge_activity_dataset_label_encoder.joblib"),
                name="Activity",
            )

            self.physiological_model = MLModel(
                model_path=os.path.join(base, "edge_physiological_state_dataset_model.joblib"),
                scaler_path=os.path.join(base, "edge_physiological_state_dataset_scaler.joblib"),
                label_encoder_path=os.path.join(base, "edge_physiological_state_dataset_label_encoder.joblib"),
                name="Physiological",
            )

            self.risk_model = MLModel(
                model_path=os.path.join(base, "edge_risk_severity_dataset_model.joblib"),
                scaler_path=os.path.join(base, "edge_risk_severity_dataset_scaler.joblib"),
                label_encoder_path=os.path.join(base, "edge_risk_severity_dataset_label_encoder.joblib"),
                name="Risk",
            )
        except Exception as e:
            print(f" Error loading model/scaler: {e}")
            raise


        # Recommendation engine
        print("\n3) Initializing recommendation engine...")
        try:
            self.recommendation_engine = RecommendationEngine()
            print("  Recommendation engine ready")
        except Exception as e:
            print(f"   Error initializing RecommendationEngine: {e}")
            raise

        # MQTT publisher
        self.mqtt_publisher = None
        if mqtt_enabled and HealthMQTTPublisher is not None:
            print("\n4) Initializing MQTT publisher...")
            try:
                self.mqtt_publisher = HealthMQTTPublisher(broker_host=mqtt_broker)
                if self.mqtt_publisher.connect():
                    print("  MQTT publisher connected")
                else:
                    print("   MQTT connect failed (continuing without MQTT)")
                    self.mqtt_publisher = None
            except Exception as e:
                print(f"   MQTT init error: {e}")
                self.mqtt_publisher = None
        else:
            print("\n4) MQTT publishing disabled")

        # mDNS service
        self.mdns_service = None
        if mdns_enabled and HealthMonitorService is not None:
            print("\n5) Initializing mDNS service...")
            try:
                self.mdns_service = HealthMonitorService(service_name="VitaBand", port=1883)
                started = False
                try:
                    started = self.mdns_service.start()
                except Exception:
                    # some mDNS implementations return None/True etc.
                    started = True
                if started:
                    print("  mDNS advertised")
                else:
                    print("   mDNS advertisement failed (continuing without mDNS)")
                    self.mdns_service = None
            except Exception as e:
                print(f"   mDNS init error: {e}")
                self.mdns_service = None
        else:
            print("\n5) mDNS service disabled")

        # Expected features in the correct order
        self.feature_names: List[str] = [
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

        # Label names (must match model training order)
        self.label_names: List[str] = [
            "Resting",
            "Light activity",
            "Moderate activity",
            "High activity",
            "Sleeping",
            "Walking",
            "Running",
            "Sedentary",
            "Normal",
            "Stressed",
            "Fatigued",
            "Dehydrated",
            "Possible fever",
            "Low oxygen state",
            "Overexertion",
            "Early illness indication",
            "Hot environment",
            "Cold environment",
            "Humid environment",
            "Low-pressure environment",
            "Healthy",
            "Slight abnormality",
            "Warning",
            "Critical",
        ]

        print("\n6) System ready!")
        print(f"   - Features: {len(self.feature_names)}")
        print(f"   - Labels: {len(self.label_names)}")
        print(f"   - MQTT: {'Enabled' if self.mqtt_publisher else 'Disabled'}")
        print(f"   - mDNS: {'Enabled' if self.mdns_service else 'Disabled'}")
        print("=" * 70 + "\n")


    # Sensor / validation / prediction / recommendation Logic
    def read_sensors(self) -> Dict[str, Any]:
        """Read all sensors and return a dictionary of sensor values."""
        return self.sensor_manager.read_all_sensors()

    def _validate_sensor_data(self, sensor_data: Dict[str, Any]) -> None:
        """Ensure all required feature keys exist in sensor_data."""
        missing = [k for k in self.feature_names if k not in sensor_data]
        if missing:
            raise KeyError(f"Missing sensor keys: {missing}")

    def predict(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Using the model to predict labels from sensor_data.
        """
        # Validate incoming data
        self._validate_sensor_data(sensor_data)

        activity = self.activity_model.predict(sensor_data, self.feature_names)
        physiological = self.physiological_model.predict(sensor_data, self.feature_names)
        risk = self.risk_model.predict(sensor_data, self.feature_names)
        
        # Get active labels
        active_labels = activity + physiological + risk

        # Prepare result dictionary
        timestamp = datetime.utcnow().isoformat() + "Z"
        result = {
            "timestamp": timestamp,
            "sensor_data": sensor_data,
            "labels": active_labels,
        }

        # Generate natural language recommendation
        try:
            recommendation = self.recommendation_engine.interpret(active_labels, sensor_data)
            result["recommendation"] = recommendation
        except Exception as e:
            # Prevent Recommendation engine breaking the main loop
            result["recommendation"] = {
                "summary": "",
                "recommendation": "",
                "priority": "normal",
                "full_message": f"Recommendation generation failed: {e}",
            }

        return result

    
    # Display / Logging / Publish
    def display_result(self, result: Dict[str, Any]) -> None:
        """Printing a human-friendly summary to the console."""
        print("\n" + "_" * 70)
        print(f"MONITORING UPDATE - {result['timestamp']}")
        print("_" * 70)

        s = result["sensor_data"]
        print("\nSENSOR READINGS:")
        print(f"  Body Temp:    {s['body_temp']:.1f} °C")
        print(f"  Ambient Temp: {s['ambient_temp']:.1f} °C")
        print(f"  Pressure:     {s['pressure_hpa']:.1f} hPa")
        print(f"  Humidity:     {s['humidity_pct']:.1f} %")
        print(f"  Accel:        X:{s['accel_x']:.2f}g Y:{s['accel_y']:.2f}g Z:{s['accel_z']:.2f}g")
        print(f"  Gyro:         X:{s['gyro_x']:.1f}°/s Y:{s['gyro_y']:.1f}°/s Z:{s['gyro_z']:.1f}°/s")
        print(f"  Heart Rate:   {s['heart_rate_bpm']:.0f} BPM")
        print(f"  SpO2:         {s['spo2_pct']:.1f} %")

        print(f"\nDETECTED STATES ({len(result['labels'])}):")
        if result["labels"]:
            for label in result["labels"]:
               print(f"  🔵 {label}")
        else:
            print("  (No states detected)")

        if "recommendation" in result:
            rec = result["recommendation"]
            priority = rec.get("priority", "normal").lower()
            icons = {"critical": "🚨", "warning": "⚠️", "caution": "⚡", "normal": "✅"}
            icon = icons.get(priority, "ℹ️")
            print(f"\n{icon} RECOMMENDATION [{priority.upper()}]:")
            print(f"  {rec.get('full_message', '')}")

        print("=" * 70 + "\n")

    def monitor_continuous(self, log_file: str, poll_interval: float = 5.0) -> None:
        """
        Continuously monitor sensors, predict, display, publish, and log.

        Args:
            log_file: CSV path to write logs to.
            poll_interval: seconds between each measurement.
        """
        print(f"Starting continuous monitoring (interval = {poll_interval} seconds)")
        print("Press Ctrl+C to stop\n")

        # CSV header: timestamp, features..., active_labels, recommendation, priority
        header = ["timestamp"] + self.feature_names + ["active_labels", "recommendation", "priority"]
        try:
            f = open(log_file, "w", newline="", encoding="utf-8")
        except Exception as e:
            print(f"ERROR: Cannot open log file {log_file}: {e}")
            raise

        writer = csv.writer(f)
        writer.writerow(header)
        f.flush()
        print(f"Logging to: {log_file}\n")

        try:
            while True:
                try:
                    # Read and validate sensors
                    sensor_data = self.read_sensors()
                    self._validate_sensor_data(sensor_data)
                except KeyError as e:
                    print(f"[WARN] Sensor data missing keys: {e}. Skipping this cycle.")
                    time.sleep(poll_interval)
                    continue
                except Exception as e:
                    print(f"[ERROR] Failed to read sensors: {e}. Skipping this cycle.")
                    time.sleep(poll_interval)
                    continue

                # Prediction
                try:
                    result = self.predict(sensor_data)
                except Exception as e:
                    print(f"[ERROR] Prediction failed: {e}. Skipping this cycle.")
                    time.sleep(poll_interval)
                    continue

                # Console output
                try:
                    self.display_result(result)
                except Exception as e:
                    print(f"[WARN] Display failed: {e}")

                # MQTT publish (best-effort)
                if self.mqtt_publisher:
                    try:
                        self.mqtt_publisher.publish_health_update(result)
                    except Exception as e:
                        print(f"[WARN] MQTT publish exception: {e}")

                # Prepare CSV row (match header)
                rec = result.get("recommendation", {})
                active_labels_str = ", ".join(result.get("labels", []))
                rec_msg = rec.get("summary", "")
                priority = rec.get("priority", "normal")

                row = (
                    [result["timestamp"]]
                    + [sensor_data[feat] for feat in self.feature_names]
                    + [active_labels_str, rec_msg, priority]
                )

                try:
                    writer.writerow(row)
                    f.flush()
                except Exception as e:
                    print(f"[WARN] Failed to write log row: {e}")

                # Sleep
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("\n\n✓ Monitoring stopped by user")
        finally:
            try:
                f.close()
                print(f"✓ Log saved to {log_file}")
            except Exception:
                pass

    def close(self) -> None:
        """Clean up resources (sensor manager, mqtt, mdns)"""
        try:
            if hasattr(self.sensor_manager, "close"):
                self.sensor_manager.close()
        except Exception as e:
            print(f"[WARN] sensor_manager.close() failed: {e}")

        try:
            if self.mqtt_publisher:
                self.mqtt_publisher.disconnect()
        except Exception as e:
            print(f"[WARN] mqtt_publisher.disconnect() failed: {e}")

        try:
            if self.mdns_service and hasattr(self.mdns_service, "stop"):
                self.mdns_service.stop()
        except Exception as e:
            print(f"[WARN] mdns_service.stop() failed: {e}")

# Main entrypoin
def main():
    try:
        monitor = ActivityMonitor(
            mqtt_enabled=True,
            mqtt_broker="localhost",
            mdns_enabled=True,
        )
    except Exception as e:
        print(f"\nFailed to initialize ActivityMonitor: {e}")
        sys.exit(1)

    # create log filename with timestamp
    log_file = f"data/activity_log_{datetime.utcnow().strftime('%Y%m%d_%H%M%SZ')}.csv"

    try:
        # default poll interval 5 seconds (you can change this)
        monitor.monitor_continuous(log_file=log_file, poll_interval=5.0)
    finally:
        monitor.close()


if __name__ == "__main__":
    main()
