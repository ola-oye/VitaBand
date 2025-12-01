#!/usr/bin/env python3
"""
Sensor Manager Class - Integrated with ML Inference

Provides a SensorManager class that:
1. Starts sensor subprocesses
2. Continuously reads and buffers sensor data
3. Provides read_all_sensors() method that returns latest readings

Compatible with the ActivityMonitor inference system.
"""

import sys
import os
import subprocess
import threading
import queue
import re
import time
from datetime import datetime
from collections import defaultdict


class SensorManager:
    """
    Manages multiple sensor subprocesses and provides real-time sensor readings
    """
    
    # Sensor script paths
    SCRIPTS = [
        ("max30102", os.path.join(os.path.dirname(os.path.dirname(__file__)), "sensors", "max30102-master", "max30102_sensor.py")),
        ("ds18b20", os.path.join(os.path.dirname(os.path.dirname(__file__)), "sensors", "temp_ds18b20_sensor.py")),
        ("bme280", os.path.join(os.path.dirname(os.path.dirname(__file__)), "sensors", "bme280_sensor.py")),
        ("mpu6050", os.path.join(os.path.dirname(os.path.dirname(__file__)), "sensors", "mpu6050_sensor.py")),
    ]
    
    def __init__(self, sensors=None, buffer_time=2.0):
        """
        Initialize sensor manager
        
        Args:
            sensors: List of sensor names to use (e.g., ['bme280', 'mpu6050'])
                    If None, uses all available sensors
            buffer_time: How long to buffer data before updating (seconds)
        """
        print("Initializing Sensor Manager...")
        
        self.buffer_time = buffer_time
        self.stop_event = threading.Event()
        self.data_queue = queue.Queue()
        
        # Buffer to store latest sensor readings
        self.sensor_buffer = defaultdict(lambda: None)
        self.buffer_lock = threading.Lock()
        
        # Feature columns expected by ML model
        self.feature_cols = [
            "body_temp", "ambient_temp", "pressure_hpa", "humidity_pct",
            "accel_x", "accel_y", "accel_z",
            "gyro_x", "gyro_y", "gyro_z",
            "heart_rate_bpm", "spo2_pct"
        ]
        
        # Initialize buffer with None values
        for col in self.feature_cols:
            self.sensor_buffer[col] = None
        
        # Select which sensors to start
        if sensors:
            wanted = set(sensors)
            scripts = [s for s in self.SCRIPTS if s[0] in wanted]
        else:
            scripts = self.SCRIPTS
        
        # Start sensor subprocesses
        self.processes = self._start_subprocesses(scripts)
        
        if not self.processes:
            raise RuntimeError("No sensor subprocesses started")
        
        # Start background threads
        self.threads = []
        
        # Start reader threads for each sensor
        for name, proc in self.processes:
            t = threading.Thread(
                target=self._reader_thread,
                args=(proc, name),
                daemon=True
            )
            t.start()
            self.threads.append(t)
        
        # Start buffer updater thread
        updater = threading.Thread(
            target=self._buffer_updater_thread,
            daemon=True
        )
        updater.start()
        self.threads.append(updater)
        
        print(f"✓ Sensor Manager initialized with {len(self.processes)} sensors")
        
        # Give sensors time to start producing data
        time.sleep(5.0)
    
    def _start_subprocesses(self, scripts):
        """Start sensor scripts as subprocesses"""
        procs = []
        for name, path in scripts:
            if not os.path.exists(path):
                print(f"Warning: script for {name} not found at {path}, skipping")
                continue
            
            cmd = [sys.executable, path]
            try:
                p = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                procs.append((name, p))
                print(f"  Started {name} sensor")
            except Exception as e:
                print(f"  Failed to start {name}: {e}")
        
        return procs
    
    def _parse_line(self, sensor, line):
        """Parse sensor output line and extract metric data"""
        line = line.strip()
        results = []
        
        # DS18B20: body temperature (single number)
        if sensor == "ds18b20":
            m = re.match(r"^\s*([+-]?\d+\.?\d*)\s*$", line)
            if m:
                return [("body_temp", m.group(1))]
        
        # BME280: ambient temperature
        if "Temperature:" in line and "°C" in line:
            nums = re.findall(r"([+-]?\d+\.?\d*)", line)
            if len(nums) >= 1:
                results.append(("ambient_temp", nums[0]))
                return results
        
        # BME280: pressure
        if line.startswith("Pressure:"):
            m = re.search(r"([+-]?\d+\.?\d*)", line)
            if m:
                results.append(("pressure_hpa", m.group(1)))
                return results
        
        # BME280: humidity
        if "Humidity:" in line:
            m = re.search(r"([+-]?\d+\.?\d*)", line)
            if m:
                results.append(("humidity_pct", m.group(1)))
                return results
        
        # MPU6050: accelerometer
        if line.startswith("Accel:"):
            for axis in ("X", "Y", "Z"):
                m = re.search(rf"{axis}=\s*([+-]?\d+\.?\d*)g", line)
                if m:
                    results.append((f"accel_{axis.lower()}", m.group(1)))
            return results
        
        # MPU6050: gyroscope
        if line.startswith("Gyro:"):
            for axis in ("X", "Y", "Z"):
                m = re.search(rf"{axis}=\s*([+-]?\d+\.?\d*)°/s", line)
                if m:
                    results.append((f"gyro_{axis.lower()}", m.group(1)))
            return results
        
        # MAX30102: heart rate
        if "Heart Rate" in line:
            m = re.search(r"([0-9]+\.?[0-9]*)", line)
            if m:
                results.append(("heart_rate_bpm", m.group(1)))
                return results
        
        # MAX30102: SpO2
        if "SpO2" in line or "SpO2 Level" in line:
            m = re.search(r"([0-9]+\.?[0-9]*)", line)
            if m:
                results.append(("spo2_pct", m.group(1)))
                return results
        
        return results
    
    def _reader_thread(self, proc, sensor_name):
        """Read lines from sensor subprocess and queue parsed data"""
        try:
            for raw_line in proc.stdout:
                if self.stop_event.is_set():
                    break
                
                line = raw_line.rstrip("\n")
                parsed = self._parse_line(sensor_name, line)
                
                for metric, value in parsed:
                    self.data_queue.put({
                        "timestamp": datetime.now().isoformat(),
                        "sensor": sensor_name,
                        "metric": metric,
                        "value": value
                    })
        except Exception as e:
            print(f"Reader thread error for {sensor_name}: {e}")
    
    def _buffer_updater_thread(self):
        """Update sensor buffer from queue data"""
        while not self.stop_event.is_set():
            try:
                # Get data from queue with timeout
                data = self.data_queue.get(timeout=0.5)
                
                metric = data.get("metric")
                value = data.get("value")
                
                # Update buffer if it's a valid feature
                if metric in self.feature_cols:
                    with self.buffer_lock:
                        try:
                            self.sensor_buffer[metric] = float(value)
                        except (ValueError, TypeError):
                            pass
                
            except queue.Empty:
                continue
    
    def read_all_sensors(self):
        """
        Get current sensor readings
        
        Returns:
            dict: Dictionary with standardized keys for ML model:
                {
                    'body_temp': 37.2,
                    'ambient_temp': 25.0,
                    'pressure_hpa': 1013.0,
                    'humidity_pct': 60.0,
                    'accel_x': 0.5,
                    'accel_y': 0.3,
                    'accel_z': 1.0,
                    'gyro_x': 15.0,
                    'gyro_y': 10.0,
                    'gyro_z': 5.0,
                    'heart_rate_bpm': 80.0,
                    'spo2_pct': 98.0
                }
        """
        with self.buffer_lock:
            # Create a copy of the buffer
            sensor_data = {}
            
            for feature in self.feature_cols:
                value = self.sensor_buffer.get(feature)
                
                # Use default values if sensor data not available yet
                if value is None:
                    # Provide reasonable defaults
                    defaults = { 
                        'body_temp': 38.18543053481313,
                        'ambient_temp': 40.65328021937469,
                        'pressure_hpa': 1118.0779043417701,
                        'humidity_pct': 2.2290509612701151,
                        'accel_x': -2.9304472197953389,
                        'accel_y': 1.52609944889852,
                        'accel_z': -3.45767613961922,
                        'gyro_x': -192.49125756855392,
                        'gyro_y': 228.95306166720195,
                        'gyro_z': 104.31422945069176,
                        'heart_rate_bpm': 100.85761985373327,
                        'spo2_pct': 50.4721417330743
                    }
                    value = defaults.get(feature, 0.0)
                
                sensor_data[feature] = value
            
            return sensor_data
    
    def get_sensor_status(self):
        """
        Get status of which sensors have provided data
        
        Returns:
            dict: Status of each feature (True if data received, False otherwise)
        """
        with self.buffer_lock:
            status = {}
            for feature in self.feature_cols:
                status[feature] = self.sensor_buffer.get(feature) is not None
            return status
    
    def close(self):
        """Shutdown all sensors and threads"""
        print("\nShutting down Sensor Manager...")
        
        # Signal threads to stop
        self.stop_event.set()
        
        # Terminate subprocesses
        for name, proc in self.processes:
            try:
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=2.0)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        
        # Wait for threads
        for t in self.threads:
            t.join(timeout=1.0)
        
        print("✓ Sensor Manager shut down")


if __name__ == "__main__":
    print("SensorManager class is ready to use.")