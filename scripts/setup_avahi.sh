#!/bin/bash
# Setup Avahi (mDNS/Zeroconf) for VitaBand Health Monitoring System
# Enables automatic device discovery by mobile apps

set -e

echo "=========================================="
echo "Avahi mDNS Service Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# STEP 1: Install Avahi (if not installed)

echo "Step 1: Checking Avahi installation..."

if ! command -v avahi-daemon &> /dev/null; then
    echo "  Avahi not found. Installing..."
    apt update
    apt install -y avahi-daemon avahi-utils
    echo "  ✓ Avahi installed"
else
    echo "  ✓ Avahi already installed"
fi

echo ""

# STEP 2: Set Hostname

echo "Step 2: Setting hostname..."

CURRENT_HOSTNAME=$(hostname)
DEFAULT_HOSTNAME="vitaband"

echo "  Current hostname: $CURRENT_HOSTNAME"
echo ""
read -p "  Set hostname to '$DEFAULT_HOSTNAME'? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    hostnamectl set-hostname "$DEFAULT_HOSTNAME"
    echo "  ✓ Hostname set to: $DEFAULT_HOSTNAME"
    echo "  Accessible at: $DEFAULT_HOSTNAME.local"
else
    echo "  Keeping current hostname: $CURRENT_HOSTNAME"
    echo "  Accessible at: $CURRENT_HOSTNAME.local"
fi

echo ""

# STEP 3: Configure Avahi

echo "Step 3: Configuring Avahi daemon..."

AVAHI_CONF="/etc/avahi/avahi-daemon.conf"
BACKUP_CONF="/etc/avahi/avahi-daemon.conf.backup"

# Backup existing config
if [ -f "$AVAHI_CONF" ]; then
    cp "$AVAHI_CONF" "$BACKUP_CONF"
    echo "  Backup created: $BACKUP_CONF"
fi

# Copy new configuration
if [ -f "avahi-daemon.conf" ]; then
    cp avahi-daemon.conf "$AVAHI_CONF"
    echo "  ✓ Configuration updated"
else
    echo "  ⚠ avahi-daemon.conf not found in current directory"
    echo "  Using default configuration"
fi

echo ""

# STEP 4: Create Service File for MQTT

echo "Step 4: Creating MQTT service advertisement..."

SERVICE_DIR="/etc/avahi/services"
SERVICE_FILE="$SERVICE_DIR/mqtt.service"

# Create services directory if it doesn't exist
mkdir -p "$SERVICE_DIR"

# Create MQTT service file
cat > "$SERVICE_FILE" << 'EOF'
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name replace-wildcards="yes">Health Monitor on %h</name>
  <service>
    <type>_mqtt._tcp</type>
    <port>1883</port>
    <txt-record>version=1.0</txt-record>
    <txt-record>service=vitaband</txt-record>
    <txt-record>description=Real-time health and activity monitoring</txt-record>
  </service>
</service-group>
EOF

echo "  ✓ MQTT service file created: $SERVICE_FILE"
echo ""

# STEP 5: Set Permissions

echo "Step 5: Setting permissions..."

chown root:root "$AVAHI_CONF"
chmod 644 "$AVAHI_CONF"

chown root:root "$SERVICE_FILE"
chmod 644 "$SERVICE_FILE"

echo "  ✓ Permissions set"
echo ""

# STEP 6: Configure Firewall

echo "Step 6: Configuring firewall..."

# Check if ufw is installed and active
if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
    echo "  UFW firewall detected"
    ufw allow 5353/udp comment 'mDNS/Avahi'
    echo "  ✓ mDNS port (5353/udp) opened in UFW"
else
    echo "  UFW not active, skipping firewall configuration"
fi

echo ""

# STEP 7: Enable and Start Avahi

echo "Step 7: Starting Avahi daemon..."

# Enable service
systemctl enable avahi-daemon

# Restart to apply changes
systemctl restart avahi-daemon

# Wait a moment for startup
sleep 2

# Check status
if systemctl is-active --quiet avahi-daemon; then
    echo "  ✓ Avahi daemon started successfully"
else
    echo "  ✗ Avahi daemon failed to start"
    echo "  Check logs: journalctl -u avahi-daemon -n 50"
    exit 1
fi

echo ""

# STEP 8: Verification

echo "Step 8: Verifying configuration..."
echo ""

HOSTNAME=$(hostname)

# Test 1: Check if service is running
if pgrep -x "avahi-daemon" > /dev/null; then
    echo "  ✓ Avahi daemon is running"
else
    echo "  ✗ Avahi daemon is not running"
fi

# Test 2: Try to resolve hostname
echo "  Testing hostname resolution..."
if avahi-resolve -n "$HOSTNAME.local" &> /dev/null; then
    IP=$(avahi-resolve -n "$HOSTNAME.local" | awk '{print $2}')
    echo "  ✓ $HOSTNAME.local resolves to $IP"
else
    echo "  ⚠ Cannot resolve $HOSTNAME.local (may not work on same device)"
fi

# Test 3: List published services
echo ""
echo "  Published services:"
avahi-browse -a -t -r | grep -A 3 "Health Monitor" || echo "  ⚠ Service not yet visible (may take a few seconds)"

echo "=========================================="