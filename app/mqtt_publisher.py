#!/usr/bin/env python3
"""
MQTT Publisher for Health Monitoring System
"""

import json
import time
import signal
from datetime import datetime

import paho.mqtt.client as mqtt


class HealthMQTTPublisher:
    """
    MQTT Publisher for health monitoring data.
    Includes:
    - Auto reconnect
    - validation
    - Safe publish handling
    - TLS + Authentication support
    """

    def __init__(
        self,
        broker_host="localhost",
        broker_port=1883,
        client_id=None,
        username=None,
        password=None,
        use_tls=False,
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.connected = False

        # Generate unique client ID
        if client_id is None:
            client_id = f"health_monitor_{int(time.time())}"

        # Create MQTT client with explicit protocol
        self.client = mqtt.Client(
            client_id=client_id, protocol=mqtt.MQTTv311
        )

        # Authentication (if set)
        if username and password:
            self.client.username_pw_set(username, password)

        # TLS security (optional)
        if use_tls:
            self.client.tls_set()

        # Set callback handlers
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish

        # Topics
        self.topics = {
            "health_status": "health/status",
            "recommendation": "health/recommendation",
            "sensor_data": "health/sensors",
            "alerts": "health/alerts",
            # "heartbeat": "health/heartbeat",
        }

        print(f"[INIT] MQTT Publisher initialized (Client ID: {client_id})")

    # -----------------------------------------------------
    # CONNECTION HANDLING
    # -----------------------------------------------------

    def connect(self):
        """Connect to MQTT broker with safety and timeout"""

        print(f"[CONNECT] Connecting to {self.broker_host}:{self.broker_port}...")

        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
        except Exception as e:
            print(f"[ERROR] Connection attempt failed: {e}")
            return False

        # Start background loop safely
        try:
            self.client.loop_start()
        except Exception as e:
            print(f"[ERROR] Failed to start MQTT network loop: {e}")
            return False

        # Wait max 5 seconds for connection
        timeout = 5
        start = time.time()

        while not self.connected and time.time() - start < timeout:
            time.sleep(0.1)

        if self.connected:
            print("[CONNECT] ✓ Connected successfully")
            return True

        print("[CONNECT] ✗ Connection timeout")
        return False

    def disconnect(self):
        """close connection"""
        if self.connected:
            print("[DISCONNECT] Disconnecting...")
            try:
                self.client.loop_stop()
                self.client.disconnect()
                print("[DISCONNECT] Disconnected cleanly.")
            except Exception as e:
                print(f"[ERROR] During disconnect: {e}")

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    def _validate_result(self, result):
        """Ensure result contains all required fields"""

        required = ["timestamp", "sensor_data", "active_labels", "num_active", "recommendation"]

        for key in required:
            if key not in result:
                raise ValueError(f"Missing required key: '{key}'")

    # -----------------------------------------------------
    # MAIN PUBLISHING METHOD
    # -----------------------------------------------------

    def _publish(self, topic, message, qos=0, retain=False):
        """Safe publish with JSON conversion + publish confirmation"""

        try:
            payload = json.dumps(message)
        except Exception as e:
            print(f"[ERROR] Failed to encode JSON: {e}")
            return False

        try:
            publish_result = self.client.publish(topic, payload, qos=qos, retain=retain)
            publish_result.wait_for_publish(timeout=3)
        except Exception as e:
            print(f"[ERROR] Publish to {topic} failed: {e}")
            return False

        if publish_result.is_published():
            print(f"[PUBLISH] Sent → {topic} ({len(payload)} bytes)")
            return True

        print(f"[WARN] Publish to {topic} may not have completed")
        return False

    # -----------------------------------------------------
    # HEALTH UPDATE PUBLISHING
    # -----------------------------------------------------

    def publish_health_update(self, result):
        """Publish all health updates in structured format"""
 
        if not self.connected:
            print("[WARN] Cannot publish – not connected to MQTT broker.")
            return False

        try:
            self._validate_result(result)
        except Exception as e:
            print(f"[ERROR] Invalid result data: {e}")
            return False

        # To use ISO 8601 timestamp for all messages
        timestamp = datetime.utcnow().isoformat() + "Z"

        # 1. Recommendation
        rec = result.get("recommendation")
        if rec:
            rec_msg = {
                "timestamp": timestamp,
                "message": rec.get("full_message"),
                "summary": rec.get("summary"),
                "advice": rec.get("recommendation"),
                "priority": rec.get("priority") if rec else "normal",

            }
            self._publish(self.topics["recommendation"], rec_msg, qos=1)

        # 2. Sensor data
        sensor_msg = {
            "timestamp": timestamp,
            "sensors": result["sensor_data"],
        }
        self._publish(self.topics["sensor_data"], sensor_msg)

        # 3. Health status
        status_msg = {
            "timestamp": timestamp,
            "priority": rec.get("priority") if rec else "normal",
        }
        self._publish(self.topics["health_status"], status_msg, qos=1)

        # 4. Critical alerts (if needed)
        if rec and rec.get("priority") in ["critical", "warning"]:
            alert_msg = {
                "timestamp": timestamp,
                "level": rec["priority"],
                "message": rec["full_message"],
                "labels": result["active_labels"],
            }
            self._publish(self.topics["alerts"], alert_msg, qos=2)

        return True

    # -----------------------------------------------------
    # HEARTBEAT
    # -----------------------------------------------------

    # def publish_heartbeat(self):
    #     """Publish retained heartbeat for monitoring dashboards"""

    #     if not self.connected:
    #         return

    #     heartbeat_msg = {
    #         "timestamp": datetime.utcnow().isoformat() + "Z",
    #         "status": "alive",
    #     }

    #     self._publish(self.topics["heartbeat"], heartbeat_msg, retain=True)

    # -----------------------------------------------------
    # CALLBACKS
    # -----------------------------------------------------

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print("[MQTT] Connected (rc=0)")
        else:
            print(f"[MQTT] Connection failed (rc={rc})")

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        print(f"[MQTT] Disconnected (rc={rc})")

        if rc != 0:
            print("[MQTT] Unexpected disconnect, retrying...")
            try:
                client.reconnect()
            except Exception as e:
                print(f"[ERROR] Reconnect failed: {e}")

    def _on_publish(self, client, userdata, mid):
        pass  # Optional logging


# -----------------------------------------------------
# SHUTDOWN (Ctrl+C)
# -----------------------------------------------------

def enable_shutdown(publisher):
    def shutdown_handler(sig, frame):
        print("\n[EXIT] Caught shutdown signal.")
        publisher.disconnect()
        exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
