#!/bin/bash
# Docker entrypoint script for VitaBand

set -e

echo "VitaBand Health Monitoring System - Starting"

# Start D-Bus (required for Avahi)
echo "[1/4] Starting D-Bus..."
mkdir -p /var/run/dbus
dbus-daemon --system --fork || echo "D-Bus already running"

# Start Avahi daemon (mDNS)
echo "[2/4] Starting Avahi daemon..."
avahi-daemon --daemonize || echo "Avahi already running"

# Start Mosquitto MQTT broker
echo "[3/4] Starting Mosquitto MQTT broker..."
mosquitto -c /etc/mosquitto/conf.d/custom.conf -d || echo "Mosquitto already running"

# Wait for services to start
sleep 2

# Check if services are running
echo "[4/4] Checking services..."

# Check Mosquitto
if mosquitto_sub -h localhost -t '$SYS/broker/version' -C 1 -W 1 >/dev/null 2>&1; then
    echo "  ✓ Mosquitto is running"
else
    echo "  ✗ Mosquitto failed to start"
fi

# Check Avahi
if pgrep -x "avahi-daemon" > /dev/null; then
    echo "  ✓ Avahi is running"
else
    echo "  ✗ Avahi failed to start"
fi

echo ""
echo "Services started. Starting application..."
echo ""

# Execute the main command
exec "$@"