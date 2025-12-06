#!/usr/bin/env python3
"""
Optimized MPU6050 Interface for Raspberry Pi
Reads accelerometer and gyroscope data via I2C
"""

import smbus2
import time
import sys

class MPU6050:
    # MPU6050 Registers
    PWR_MGMT_1 = 0x6B
    SMPLRT_DIV = 0x19
    CONFIG = 0x1A
    GYRO_CONFIG = 0x1B
    ACCEL_CONFIG = 0x1C
    INT_ENABLE = 0x38
    
    ACCEL_XOUT_H = 0x3B
    ACCEL_YOUT_H = 0x3D
    ACCEL_ZOUT_H = 0x3F
    TEMP_OUT_H = 0x41
    GYRO_XOUT_H = 0x43
    GYRO_YOUT_H = 0x45
    GYRO_ZOUT_H = 0x47
    
    def __init__(self, bus=1, address=0x68):
        """
        Initialize MPU6050
        
        Args:
            bus: I2C bus number (1 for Raspberry Pi 3/4, 0 for older models)
            address: I2C address of MPU6050 (default 0x68)
        """
        self.bus = smbus2.SMBus(bus)
        self.address = address
        
        # Wake up the MPU6050
        self.bus.write_byte_data(self.address, self.PWR_MGMT_1, 0)
        time.sleep(0.1)
        
        # Configure sample rate (1kHz / (1 + SMPLRT_DIV))
        self.bus.write_byte_data(self.address, self.SMPLRT_DIV, 7)
        
        # Configure digital low pass filter
        self.bus.write_byte_data(self.address, self.CONFIG, 0)
        
        # Configure gyroscope range (±250°/s)
        self.bus.write_byte_data(self.address, self.GYRO_CONFIG, 0)
        
        # Configure accelerometer range (±2g)
        self.bus.write_byte_data(self.address, self.ACCEL_CONFIG, 0)
        
        # Sensitivity scale factors
        self.accel_scale = 16384.0  # LSB/g for ±2g
        self.gyro_scale = 131.0     # LSB/(°/s) for ±250°/s
        
    def read_raw_data(self, addr):
        """Read 16-bit signed value from two registers"""
        high = self.bus.read_byte_data(self.address, addr)
        low = self.bus.read_byte_data(self.address, addr + 1)
        
        # Combine high and low bytes
        value = (high << 8) | low
        
        # Convert to signed value
        if value > 32768:
            value -= 65536
        
        return value
    
    def read_accel(self):
        """
        Read accelerometer data
        
        Returns:
            tuple: (ax, ay, az) in g's
        """
        ax = self.read_raw_data(self.ACCEL_XOUT_H) / self.accel_scale
        ay = self.read_raw_data(self.ACCEL_YOUT_H) / self.accel_scale
        az = self.read_raw_data(self.ACCEL_ZOUT_H) / self.accel_scale
        
        return (ax, ay, az)
    
    def read_gyro(self):
        """
        Read gyroscope data
        
        Returns:
            tuple: (gx, gy, gz) in °/s
        """
        gx = self.read_raw_data(self.GYRO_XOUT_H) / self.gyro_scale
        gy = self.read_raw_data(self.GYRO_YOUT_H) / self.gyro_scale
        gz = self.read_raw_data(self.GYRO_ZOUT_H) / self.gyro_scale
        
        return (gx, gy, gz)
    
    def read_all(self):
        """
        Read all sensor data at once (optimized)
        
        Returns:
            dict: All sensor readings
        """
        # Read all 14 bytes at once for efficiency
        data = self.bus.read_i2c_block_data(self.address, self.ACCEL_XOUT_H, 14)
        
        # Parse accelerometer data
        ax = self._convert_raw(data[0], data[1]) / self.accel_scale
        ay = self._convert_raw(data[2], data[3]) / self.accel_scale
        az = self._convert_raw(data[4], data[5]) / self.accel_scale
        
        # Parse gyroscope data
        gx = self._convert_raw(data[8], data[9]) / self.gyro_scale
        gy = self._convert_raw(data[10], data[11]) / self.gyro_scale
        gz = self._convert_raw(data[12], data[13]) / self.gyro_scale
        
        return {
            'accel': (ax, ay, az),
            'gyro': (gx, gy, gz),
        }
    
    def _convert_raw(self, high, low):
        """Convert two bytes to signed 16-bit value"""
        value = (high << 8) | low
        if value > 32768:
            value -= 65536
        return value
    
    def close(self):
        """Close I2C bus connection"""
        self.bus.close()


def main():
    """Main loop - prints sensor data for sensor_manager.py to parse"""
    try:
        # Initialize sensor
        mpu = MPU6050(bus=1, address=0x68)
        
        # Brief startup message to stderr (won't be parsed)
        print("MPU6050 initialized", file=sys.stderr, flush=True)
        
        while True:
            # Read all data efficiently
            data = mpu.read_all()
            
            ax, ay, az = data['accel']
            gx, gy, gz = data['gyro']
             
            # Print in format expected by sensor_manager.py
            # Use flush=True to ensure immediate output to parent process
            print(f"Accel: X={ax:6.2f}g  Y={ay:6.2f}g  Z={az:6.2f}g", flush=True)
            print(f"Gyro:  X={gx:7.2f}°/s  Y={gy:7.2f}°/s  Z={gz:7.2f}°/s", flush=True)
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nMPU6050 stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"MPU6050 Error: {e}", file=sys.stderr)
        print("\nTroubleshooting:", file=sys.stderr)
        print("1. Check I2C is enabled: sudo raspi-config", file=sys.stderr)
        print("2. Check connections: SDA->GPIO2, SCL->GPIO3, VCC->3.3V, GND->GND", file=sys.stderr)
        print("3. Check device address: sudo i2cdetect -y 1", file=sys.stderr)
        sys.exit(1)
    finally:
        if 'mpu' in locals():
            mpu.close()


if __name__ == "__main__":
    main()