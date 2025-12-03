#!/usr/bin/env python3
"""
MQTT Configuration
Settings for connecting to MQTT broker with authentication
"""

import os

# MQTT BROKER SETTINGS
''''''
# Broker connection
MQTT_BROKER_HOST = os.getenv('MQTT_BROKER_HOST', 'localhost')
MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', 1883))

# AUTHENTICATION

# Development (no authentication)
MQTT_USE_AUTH = os.getenv('MQTT_USE_AUTH', 'false').lower() == 'true'
MQTT_USERNAME = os.getenv('MQTT_USERNAME', 'raspberry_pi')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', None)

# Production (with authentication)
# Set these environment variables:
# export MQTT_USE_AUTH=true
# export MQTT_USERNAME=raspberry_pi
# export MQTT_PASSWORD=your_secure_password

# TLS/SSL SECURITY

MQTT_USE_TLS = os.getenv('MQTT_USE_TLS', 'false').lower() == 'true'
MQTT_TLS_PORT = int(os.getenv('MQTT_TLS_PORT', 8883))

# TLS certificate paths
MQTT_CA_CERT = os.getenv('MQTT_CA_CERT', '/etc/mosquitto/ca_certificates/ca.crt')
MQTT_CLIENT_CERT = os.getenv('MQTT_CLIENT_CERT', None)
MQTT_CLIENT_KEY = os.getenv('MQTT_CLIENT_KEY', None)

# CONNECTION SETTINGS

MQTT_KEEPALIVE = 60
MQTT_CONNECT_TIMEOUT = 5
MQTT_RECONNECT_DELAY = 5
MQTT_MAX_RECONNECT_DELAY = 120

# QoS SETTINGS

QOS_RECOMMENDATION = 1  # Important messages
QOS_SENSOR_DATA = 0     # High frequency, can lose some
QOS_STATUS = 1          # Important status updates
QOS_ALERTS = 2          # Critical alerts, must deliver

# TOPICS

TOPICS = {
    'health_status': 'health/status',
    'recommendation': 'health/recommendation',
    'sensor_data': 'health/sensors',
    'alerts': 'health/alerts',
    'heartbeat': 'health/heartbeat'
}

# HELPER FUNCTIONS

def get_mqtt_config():
    """Get MQTT configuration as dictionary"""
    config = {
        'broker_host': MQTT_BROKER_HOST,
        'broker_port': MQTT_BROKER_PORT,
        'keepalive': MQTT_KEEPALIVE,
    }
    
    # Add authentication if enabled
    if MQTT_USE_AUTH and MQTT_PASSWORD:
        config['username'] = MQTT_USERNAME
        config['password'] = MQTT_PASSWORD
    
    # Add TLS if enabled
    if MQTT_USE_TLS:
        config['use_tls'] = True
        config['broker_port'] = MQTT_TLS_PORT
        config['ca_cert'] = MQTT_CA_CERT
        if MQTT_CLIENT_CERT:
            config['client_cert'] = MQTT_CLIENT_CERT
        if MQTT_CLIENT_KEY:
            config['client_key'] = MQTT_CLIENT_KEY
    
    return config


def print_config():
    """Print current MQTT configuration (without passwords)"""
    print("MQTT Configuration:")
    print(f"  Broker: {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
    print(f"  Authentication: {'Enabled' if MQTT_USE_AUTH else 'Disabled'}")
    if MQTT_USE_AUTH:
        print(f"  Username: {MQTT_USERNAME}")
        print(f"  Password: {'*' * len(MQTT_PASSWORD) if MQTT_PASSWORD else 'Not Set'}")
    print(f"  TLS: {'Enabled' if MQTT_USE_TLS else 'Disabled'}")
    if MQTT_USE_TLS:
        print(f"  TLS Port: {MQTT_TLS_PORT}")


# EXAMPLE USAGE

if __name__ == "__main__":
    print_config()
    print("\nTo enable authentication:")
    print("  export MQTT_USE_AUTH=true")
    print("  export MQTT_USERNAME=raspberry_pi")
    print("  export MQTT_PASSWORD=your_password")
    print("\nTo enable TLS:")
    print("  export MQTT_USE_TLS=true")