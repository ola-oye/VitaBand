#!/bin/bash
# Setup Mosquitto Authentication
# Creates users and ACL for secure MQTT access

set -e

echo "=========================================="
echo "Mosquitto Authentication Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Configuration paths
PASSWD_FILE="/etc/mosquitto/passwd"
ACL_FILE="/etc/mosquitto/acl"

# ==============================================================================
# STEP 1: Create Password File
# ==============================================================================

echo "Step 1: Creating users..."
echo ""

# Create admin user
echo "Creating admin user..."
mosquitto_passwd -c "$PASSWD_FILE" admin

# Create raspberry_pi user
echo ""
echo "Creating raspberry_pi user (for publisher)..."
mosquitto_passwd "$PASSWD_FILE" raspberry_pi

# Create mobile_app user
echo ""
echo "Creating mobile_app user (for mobile clients)..."
mosquitto_passwd "$PASSWD_FILE" mobile_app

echo ""
echo "✓ Users created in $PASSWD_FILE"
echo ""

# ==============================================================================
# STEP 2: Create ACL File
# ==============================================================================

echo "Step 2: Creating Access Control List (ACL)..."

cat > "$ACL_FILE" << 'EOF'
# Mosquitto Access Control List (ACL)
# Format: topic [read|write|readwrite] <topic pattern>

# ============================================================
# Admin - Full access to everything
# ============================================================
user admin
topic readwrite #

# ============================================================
# Raspberry Pi Publisher - Write access to health topics
# ============================================================
user raspberry_pi
topic write health/#
topic write $SYS/#

# ============================================================
# Mobile App - Read access to health topics
# ============================================================
user mobile_app
topic read health/#

# ============================================================
# Anonymous Users (if enabled)
# ============================================================
# pattern read health/recommendation
# pattern read health/sensors
# pattern read health/status
EOF

echo "✓ ACL created in $ACL_FILE"
echo ""

# ==============================================================================
# STEP 3: Set Permissions
# ==============================================================================

echo "Step 3: Setting file permissions..."

chown mosquitto:mosquitto "$PASSWD_FILE"
chmod 600 "$PASSWD_FILE"

chown mosquitto:mosquitto "$ACL_FILE"
chmod 644 "$ACL_FILE"

echo "✓ Permissions set"
echo ""

# ==============================================================================
# STEP 4: Update Configuration
# ==============================================================================

echo "Step 4: Updating mosquitto.conf..."

CONF_FILE="/etc/mosquitto/mosquitto.conf"
BACKUP_FILE="/etc/mosquitto/mosquitto.conf.backup"

# Backup existing config
if [ -f "$CONF_FILE" ]; then
    cp "$CONF_FILE" "$BACKUP_FILE"
    echo "  Backup created: $BACKUP_FILE"
fi

# Add authentication settings if not present
if ! grep -q "password_file" "$CONF_FILE"; then
    echo "" >> "$CONF_FILE"
    echo "# Authentication" >> "$CONF_FILE"
    echo "allow_anonymous false" >> "$CONF_FILE"
    echo "password_file $PASSWD_FILE" >> "$CONF_FILE"
    echo "acl_file $ACL_FILE" >> "$CONF_FILE"
    echo "  ✓ Authentication settings added"
else
    echo "  Authentication already configured"
fi

echo ""

# ==============================================================================
# STEP 5: Restart Mosquitto
# ==============================================================================

echo "Step 5: Restarting Mosquitto..."

systemctl restart mosquitto

if systemctl is-active --quiet mosquitto; then
    echo "✓ Mosquitto restarted successfully"
else
    echo "✗ Mosquitto failed to start"
    echo "  Check logs: journalctl -u mosquitto -n 50"
    exit 1
fi

echo ""
echo "Mosquitto Authentication Setup Completed Successfully!"