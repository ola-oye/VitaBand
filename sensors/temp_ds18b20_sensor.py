#!/usr/bin/env python3
"""
DS18B20 Temperature Sensor Interface for Raspberry Pi
Reads body temperature via 1-Wire protocol
"""

import os
import glob
import time
import sys

# Load kernel modules for 1-Wire communication
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'

def find_sensor():
    """
    Find DS18B20 sensor on 1-Wire bus
    
    Returns:
        str: Path to sensor device file, or None if not found
    """
    try:
        device_list = glob.glob(base_dir + '28*')
        if not device_list:
            return None
        # Use first sensor found (28-xxx is DS18B20 family code)
        device_folder = device_list[0]
        device_file = device_folder + '/w1_slave'
        return device_file
    except Exception as e:
        print(f"Error finding DS18B20 sensor: {e}", file=sys.stderr, flush=True)
        return None

def read_temp_raw(device_file):
    """
    Read raw data from sensor file
    
    Args:
        device_file: Path to w1_slave file
        
    Returns:
        list: Lines from sensor file, or None on error
    """
    try:
        with open(device_file, 'r') as f:
            lines = f.readlines()
        return lines
    except Exception as e:
        print(f"Error reading sensor file: {e}", file=sys.stderr, flush=True)
        return None

def read_temp(device_file):
    """
    Read temperature from DS18B20 sensor
    
    Args:
        device_file: Path to w1_slave file
        
    Returns:
        float: Temperature in Celsius, or None on error
    """
    try:
        lines = read_temp_raw(device_file)
        if not lines:
            return None
        
        # Wait for valid CRC (YES indicates good read)
        retry_count = 0
        while lines[0].strip()[-3:] != 'YES':
            if retry_count > 10:
                print("DS18B20 CRC check failed after 10 retries", file=sys.stderr, flush=True)
                return None
            time.sleep(0.2)
            lines = read_temp_raw(device_file)
            if not lines:
                return None
            retry_count += 1
        
        # Parse temperature from second line
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos + 2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c
        else:
            print("DS18B20 temperature value not found in data", file=sys.stderr, flush=True)
            return None
            
    except Exception as e:
        print(f"Error reading temperature: {e}", file=sys.stderr, flush=True)
        return None

def main():
    """Main loop - prints temperature readings for sensor_manager.py to parse"""
    # Find sensor at startup
    device_file = find_sensor()
    
    if not device_file:
        print("DS18B20 sensor not found!", file=sys.stderr, flush=True)
        print("Check connections and ensure 1-Wire is enabled", file=sys.stderr, flush=True)
        print("Run: sudo raspi-config -> Interface Options -> 1-Wire", file=sys.stderr, flush=True)
        sys.exit(1)
    
    print(f"DS18B20 sensor found at: {device_file}", file=sys.stderr, flush=True)
    print("Reading temperature... (Press Ctrl+C to stop)", file=sys.stderr, flush=True)
    
    consecutive_errors = 0
    max_consecutive_errors = 10
    
    try:
        while True:
            temp = read_temp(device_file)
            
            if temp is not None:
                # Print temperature value only (sensor_manager expects single number)
                # Format: just the number with 1 decimal place
                print(f"{temp:.1f}", flush=True)
                consecutive_errors = 0
            else:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    print(f"DS18B20 failed {max_consecutive_errors} consecutive reads - sensor may be disconnected", 
                          file=sys.stderr, flush=True)
                    # Try to re-find sensor
                    device_file = find_sensor()
                    if not device_file:
                        print("DS18B20 sensor no longer detected, exiting", file=sys.stderr, flush=True)
                        sys.exit(1)
                    consecutive_errors = 0
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nDS18B20 stopped by user", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"DS18B20 unexpected error: {e}", file=sys.stderr, flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()