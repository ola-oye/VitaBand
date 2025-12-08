#!/usr/bin/env python3
"""
Test script for Sensor Manager
Run this to see sensor data output
"""

import time
from sensor_manager import SensorManager

def main():
    print("=" * 60)
    print("SENSOR MANAGER TEST")
    print("=" * 60)
    
    try:
        # Create sensor manager (starts all sensors)
        manager = SensorManager()
        
        print("\nWaiting for sensors to stabilize...")
        time.sleep(3)
        
        print("\n" + "=" * 60)
        print("READING SENSOR DATA (Press Ctrl+C to stop)")
        print("=" * 60)
        
        # Read sensor data every 2 seconds
        while True:
            # Get all sensor readings
            data = manager.read_all_sensors()
            
            # Get sensor status
            status = manager.get_sensor_status()
            
            print("\n" + "-" * 60)
            print(f"TIMESTAMP: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 60)
            
            # Temperature readings
            print("\n📊 TEMPERATURE & ENVIRONMENT:")
            print(f"  Body Temperature:    {data['body_temp']:.1f}°C {'✓' if status['body_temp'] else '✗ (using default)'}")
            print(f"  Ambient Temperature: {data['ambient_temp']:.1f}°C {'✓' if status['ambient_temp'] else '✗ (using default)'}")
            print(f"  Pressure:            {data['pressure_hpa']:.1f} hPa {'✓' if status['pressure_hpa'] else '✗ (using default)'}")
            print(f"  Humidity:            {data['humidity_pct']:.1f}% {'✓' if status['humidity_pct'] else '✗ (using default)'}")
            
            # Motion readings
            print("\n🎯 MOTION (Accelerometer):")
            print(f"  X-axis: {data['accel_x']:+.2f}g {'✓' if status['accel_x'] else '✗'}")
            print(f"  Y-axis: {data['accel_y']:+.2f}g {'✓' if status['accel_y'] else '✗'}")
            print(f"  Z-axis: {data['accel_z']:+.2f}g {'✓' if status['accel_z'] else '✗'}")
            
            print("\n🔄 ROTATION (Gyroscope):")
            print(f"  X-axis: {data['gyro_x']:+.1f}°/s {'✓' if status['gyro_x'] else '✗'}")
            print(f"  Y-axis: {data['gyro_y']:+.1f}°/s {'✓' if status['gyro_y'] else '✗'}")
            print(f"  Z-axis: {data['gyro_z']:+.1f}°/s {'✓' if status['gyro_z'] else '✗'}")
            
            # Health readings
            print("\n❤️  HEALTH VITALS:")
            print(f"  Heart Rate: {data['heart_rate_bpm']:.0f} BPM {'✓' if status['heart_rate_bpm'] else '✗ (using default)'}")
            print(f"  SpO2 Level: {data['spo2_pct']:.1f}% {'✓' if status['spo2_pct'] else '✗ (using default)'}")
            
            # Summary of active sensors
            active_count = sum(status.values())
            total_count = len(status)
            print(f"\n📡 SENSORS ACTIVE: {active_count}/{total_count}")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\nStopping sensor readings...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'manager' in locals():
            manager.close()
        print("\nTest completed.")

if __name__ == "__main__":
    main()