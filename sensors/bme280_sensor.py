#!/usr/bin/env python3
"""
BME280 Environmental Sensor Interface for Raspberry Pi
Reads ambient temperature, pressure, and humidity via I2C
"""

import time
import sys
import smbus2
import bme280

# BME280 sensor address (default is 0x76, some modules use 0x77)
ADDRESS = 0x76

def init_sensor(bus_num=1):
    """
    Initialize BME280 sensor
    
    Args:
        bus_num: I2C bus number (1 for Raspberry Pi 3/4)
        
    Returns:
        tuple: (bus, calibration_params) or (None, None) on error
    """
    try:
        bus = smbus2.SMBus(bus_num)
        calibration_params = bme280.load_calibration_params(bus, ADDRESS)
        
        # Test read to verify sensor is working
        test_data = bme280.sample(bus, ADDRESS, calibration_params)
        
        print(f"BME280 initialized at address 0x{ADDRESS:02X}", file=sys.stderr, flush=True)
        return bus, calibration_params
        
    except FileNotFoundError:
        print("I2C device not found - is I2C enabled?", file=sys.stderr, flush=True)
        print("Enable I2C: sudo raspi-config -> Interface Options -> I2C", file=sys.stderr, flush=True)
        return None, None
    except OSError as e:
        print(f"BME280 not found at address 0x{ADDRESS:02X}", file=sys.stderr, flush=True)
        print("Check connections: SDA->GPIO2, SCL->GPIO3, VCC->3.3V, GND->GND", file=sys.stderr, flush=True)
        print("Try alternate address: Some BME280 modules use 0x77", file=sys.stderr, flush=True)
        print(f"Run 'sudo i2cdetect -y 1' to find the sensor address", file=sys.stderr, flush=True)
        return None, None
    except Exception as e:
        print(f"Error initializing BME280: {e}", file=sys.stderr, flush=True)
        return None, None

def read_sensor(bus, calibration_params):
    """
    Read data from BME280 sensor
    
    Args:
        bus: I2C bus object
        calibration_params: Sensor calibration parameters
        
    Returns:
        tuple: (temperature_c, pressure_hpa, humidity_pct) or (None, None, None) on error
    """
    try:
        data = bme280.sample(bus, ADDRESS, calibration_params)
        return data.temperature, data.pressure, data.humidity
    except Exception as e:
        print(f"Error reading BME280: {e}", file=sys.stderr, flush=True)
        return None, None, None

def main():
    """Main loop - prints environmental data for sensor_manager.py to parse"""
    
    # Initialize sensor
    bus, calibration_params = init_sensor()
    
    if bus is None:
        print("BME280 initialization failed", file=sys.stderr, flush=True)
        sys.exit(1)
    
    print("Reading environmental data... (Press Ctrl+C to stop)", file=sys.stderr, flush=True)
    
    consecutive_errors = 0
    max_consecutive_errors = 10
    
    try:
        while True:
            # Read sensor data
            temperature, pressure, humidity = read_sensor(bus, calibration_params)
            
            if temperature is not None:
                # Print readings in format expected by sensor_manager.py
                # Use flush=True to ensure immediate output to parent process
                print(f"Temperature: {temperature:.2f} °C", flush=True)
                print(f"Pressure: {pressure:.2f} hPa", flush=True)
                print(f"Humidity: {humidity:.2f} %", flush=True)
                
                consecutive_errors = 0
            else:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    print(f"BME280 failed {max_consecutive_errors} consecutive reads", 
                          file=sys.stderr, flush=True)
                    print("Sensor may be disconnected, attempting to reinitialize...", 
                          file=sys.stderr, flush=True)
                    
                    # Try to reinitialize
                    bus, calibration_params = init_sensor()
                    if bus is None:
                        print("BME280 reinitialization failed, exiting", file=sys.stderr, flush=True)
                        sys.exit(1)
                    consecutive_errors = 0
            
            # Wait before next reading
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nBME280 stopped by user", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"BME280 unexpected error: {e}", file=sys.stderr, flush=True)
        sys.exit(1)
    finally:
        try:
            bus.close()
        except:
            pass

if __name__ == "__main__":
    main()