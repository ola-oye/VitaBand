#!/usr/bin/env python3
"""
Test script for Sensor Manager
Run this to see sensor data output and save to file
"""

import time
import json
import os 
from datetime import datetime
from sensor_manager import SensorManager 


JSON_FILENAME = "sensor_data.json"
# Save the full JSON file (by rewriting) only every N readings to improve performance
SAVE_INTERVAL = 5 

def load_existing_data(filename):
    """Load existing sensor data from a standard JSON array file."""
    if not os.path.exists(filename):
        return []
    
    try:
        with open(filename, 'r') as f:
            # Load the entire JSON array
            return json.load(f)
    except json.JSONDecodeError:
        print(f"'{filename}' exists but is not valid JSON. Starting fresh.")
        return []
    except Exception as e:
        print(f"Could not read '{filename}'. Error: {e}")
        return []

def save_all_data_json(data_list, filename=JSON_FILENAME):
    """Overwrite the file with the complete list of sensor data records."""
    # Use 'w' to overwrite the file
    with open(filename, 'w') as f:
        # Dump the entire list as a single, valid JSON array
        json.dump(data_list, f, indent=4) # Use indent=4 for human-readable output

def main():
    print("=" * 60)
    print("RUNNING SENSOR MANAGER TEST")
    print("=" * 60)
    
    # Load any data previously saved to maintain a continuous log
    # This list will hold ALL records (old and new)
    all_sensor_records = load_existing_data(JSON_FILENAME)
    reading_count = len(all_sensor_records)

    print(f"✓ Saving JSON to: {JSON_FILENAME}")
    
    manager = None # Initialize manager to None
    
    try:
        manager = SensorManager()
        
        print("\nWaiting for sensors to stabilize...")
        time.sleep(3)
        
        print("\n" + "=" * 60)
        print("READING SENSOR DATA (Press Ctrl+C to stop)")
        print("=" * 60)
        
        while True:
            data = manager.read_all_sensors()
            status = manager.get_sensor_status()

            timestamp = datetime.now().isoformat()
            new_record = {
                "timestamp": timestamp,
                "readings": data,
            }
            
            #LOG AND SAVE (In-memory update)
            all_sensor_records.append(new_record)
            reading_count += 1
            
            #CONDITIONAL FILE WRITE (The correction)
            if reading_count % SAVE_INTERVAL == 0:
                save_all_data_json(all_sensor_records, JSON_FILENAME)
                print(f"-> Full JSON file SAVED at reading #{reading_count}")

            
            print("\n" + "-" * 60)
            print(f"TIMESTAMP: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Reading #{reading_count} in memory (Last full save: #{reading_count - (reading_count % SAVE_INTERVAL)})")
            print("-" * 60)
            
            # Print sections
            print("\n TEMPERATURE & ENVIRONMENT:")
            # Use .get() in case a key is missing
            print(f"  Body Temperature:    {data.get('body_temp', 'N/A'):.1f}°C")
            print(f"  Ambient Temperature: {data.get('ambient_temp', 'N/A'):.1f}°C")
            print(f"  Pressure:            {data.get('pressure_hpa', 'N/A'):.1f} hPa")
            print(f"  Humidity:            {data.get('humidity_pct', 'N/A'):.1f}%")
            
            # Check for keys before accessing them to prevent KeyErrors
            if all(key in data for key in ['accel_x', 'accel_y', 'accel_z']):
                print("\n MOTION (Accelerometer):")
                print(f"  X-axis: {data['accel_x']:+.2f}g")
                print(f"  Y-axis: {data['accel_y']:+.2f}g")
                print(f"  Z-axis: {data['accel_z']:+.2f}g")
            
            if all(key in data for key in ['gyro_x', 'gyro_y', 'gyro_z']):
                print("\n ROTATION (Gyroscope):")
                print(f"  X-axis: {data['gyro_x']:+.1f}°/s")
                print(f"  Y-axis: {data['gyro_y']:+.1f}°/s")
                print(f"  Z-axis: {data['gyro_z']:+.1f}°/s")
            
            # Health readings
            print("\n HEALTH VITALS:")
            print(f"  Heart Rate: {data.get('heart_rate_bpm', 'N/A'):.0f} BPM")
            print(f"  SpO2 Level: {data.get('spo2_pct', 'N/A'):.1f}%")
            
            # Summary of active sensors
            active_count = sum(status.values())
            total_count = len(status)
            print(f"\n SENSORS ACTIVE: {active_count}/{total_count}")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\nStopping sensor readings...")
        # Save any unsaved data when stopping
        if reading_count % SAVE_INTERVAL != 0:
             save_all_data_json(all_sensor_records, JSON_FILENAME)
             print(f"-> Final data saved to JSON. Total records: {reading_count}")
        else:
             print(f"Total records saved: {reading_count}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if manager is not None:
            manager.close()
        print("\nTest completed.")

if __name__ == "__main__":
    main()