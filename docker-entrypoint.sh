#!/bin/bash
# Docker entrypoint script for VitaBand

set -e

echo "VitaBand Health Monitoring System - Starting"

# Function to check if a process is running
check_process() {
    local process_name=$1
    if pgrep -x "$process_name" > /dev/null; then
        echo "  ✓ $process_name is running"
        return 0
    else
        echo "  ✗ $process_name is not running"
        return 1
    fi
}

# Function to wait for a service
wait_for_service() {
    local service_name=$1
    local check_command=$2
    local max_wait=10
    local count=0
    
    echo "  Waiting for $service_name..."
    while ! eval "$check_command" > /dev/null 2>&1; do
        sleep 1
        count=$((count + 1))
        if [ $count -ge $max_wait ]; then
            echo "  ✗ $service_name failed to start (timeout)"
            return 1
        fi
    done
    echo "  ✓ $service_name is ready"
    return 0
}

# STEP 1: Start D-Bus (required for Avahi)
echo "[1/5] Starting D-Bus..."
mkdir -p /var/run/dbus

# Clean up stale D-Bus files
rm -f /var/run/dbus/pid
rm -f /run/dbus/pid

# Start D-Bus daemon
dbus-daemon --system --fork 2>/dev/null || {
    echo "  Note: D-Bus may already be running"
}

sleep 1
check_process "dbus-daemon" || echo "  Warning: D-Bus status uncertain"

# STEP 2: Start Avahi daemon (mDNS)

echo "[2/5] Starting Avahi daemon..."
mkdir -p /var/run/avahi-daemon

# Clean up stale files
rm -f /var/run/avahi-daemon/pid
rm -f /var/run/avahi-daemon/socket

# Start Avahi - show errors
echo "  Attempting to start Avahi..."
avahi-daemon --daemonize --no-chroot 2>&1 || {
    echo "  Warning: Avahi start command returned error"
}

sleep 2

# Check if actually running
if pgrep -x "avahi-daemon" > /dev/null; then
    echo "  ✓ avahi-daemon is running (PID: $(pgrep -x avahi-daemon))"
else
    echo "  ✗ avahi-daemon is NOT running"
    echo "  Checking logs..."
    # Try to see what went wrong
    avahi-daemon --debug --no-chroot 2>&1 | head -20 || echo "  Could not get debug output"
fi

# STEP 3: Start Mosquitto MQTT broker

echo "[3/5] Starting Mosquitto MQTT broker..."

# Ensure directories exist
mkdir -p /var/lib/mosquitto
mkdir -p /var/log/mosquitto
chown -R mosquitto:mosquitto /var/lib/mosquitto /var/log/mosquitto

# Clean up stale PID file
rm -f /var/run/mosquitto.pid

# Start Mosquitto with custom config
mosquitto -c /etc/mosquitto/conf.d/custom.conf -d || {
    echo "  ✗ Mosquitto failed to start"
    exit 1
}

# Wait for Mosquitto to be ready
wait_for_service "Mosquitto" "mosquitto_sub -h localhost -t '\$SYS/broker/version' -C 1 -W 1"

# STEP 4: Verify Services

echo "[4/5] Verifying services..."

# Check D-Bus
if check_process "dbus-daemon"; then
    echo "  ✓ D-Bus verified"
else
    echo "  ⚠ D-Bus not running (mDNS may not work)"
fi

# Check Avahi
if check_process "avahi-daemon"; then
    echo "  ✓ Avahi verified"
    
    # Display hostname
    HOSTNAME=$(hostname)
    echo "  → mDNS Name: ${HOSTNAME}.local"
else
    echo "  ⚠ Avahi not running (device discovery may not work)"
fi

# Check Mosquitto
if mosquitto_sub -h localhost -t '$SYS/broker/version' -C 1 -W 2 >/dev/null 2>&1; then
    VERSION=$(mosquitto_sub -h localhost -t '$SYS/broker/version' -C 1 -W 2 2>/dev/null)
    echo "  ✓ Mosquitto verified"
    echo "  → Version: ${VERSION}"
else
    echo "  ✗ Mosquitto connection failed"
    exit 1
fi

# Display published services (if avahi is running)
if check_process "avahi-daemon"; then
    echo ""
    echo "  Published mDNS services:"
    timeout 3 avahi-browse -a -t 2>/dev/null | grep "Health Monitor" || echo "  → Service registration pending..."
fi

# STEP 5: Display Configuration

echo ""
echo "[5/5] Configuration Summary..."

# Get IP address
IP_ADDR=$(hostname -I | awk '{print $1}' || echo "unknown")
HOSTNAME=$(hostname)

echo "  Hostname: ${HOSTNAME}"
echo "  IP Address: ${IP_ADDR}"
echo "  mDNS Name: ${HOSTNAME}.local"
echo ""
echo "  MQTT Broker:"
echo "    • Internal: localhost:1883"
echo "    • External: ${IP_ADDR}:1883"
echo "    • mDNS: ${HOSTNAME}.local:1883"
echo ""
echo "  MQTT Topics:"
echo "    • health/recommendation (QoS 1)"
echo "    • health/sensors (QoS 0)"
echo "    • health/status (QoS 1)"
echo "    • health/alerts (QoS 2)"
echo "    • health/heartbeat (retained)"

# STEP 6: Environment Variables

echo ""
echo "Environment:"
echo "  MQTT_BROKER: ${MQTT_BROKER:-localhost}"
echo "  MQTT_PORT: ${MQTT_PORT:-1883}"
echo "  MQTT_USE_AUTH: ${MQTT_USE_AUTH:-false}"
echo "  LOG_LEVEL: ${LOG_LEVEL:-INFO}"

# Set Python path
export PYTHONPATH="${PYTHONPATH}:/app/app"

echo ""
echo "=========================================="
echo "Services started. Starting application..."
echo "=========================================="
echo ""

# STEP 7: Execute Main Application

# Trap signals for graceful shutdown
trap 'echo "Shutting down..."; pkill -TERM -P $; wait; exit 0' SIGTERM SIGINT

# Execute the main command
exec "$@"