#!/bin/bash

# AI CRM Service Installation Script

set -e

echo "=== AI CRM SystemD Service Installation ==="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" >&2
   exit 1
fi

SERVICE_FILE="aicrm.service"
SERVICE_PATH="/etc/systemd/system/${SERVICE_FILE}"

echo "1. Copying service file to systemd directory..."
cp "${SERVICE_FILE}" "${SERVICE_PATH}"

echo "2. Setting correct permissions..."
chmod 644 "${SERVICE_PATH}"

echo "3. Reloading systemd daemon..."
systemctl daemon-reload

echo "4. Enabling service to start on boot..."
systemctl enable aicrm

echo "5. Starting service..."
systemctl start aicrm

echo "6. Checking service status..."
sleep 2
systemctl status aicrm --no-pager

echo ""
echo "=== Installation Complete ==="
echo "Service: aicrm"
echo "Status: $(systemctl is-active aicrm)"
echo "Enabled: $(systemctl is-enabled aicrm)"
echo ""
echo "To view logs: sudo journalctl -u aicrm -f"
echo "To restart: sudo systemctl restart aicrm"
echo "To stop: sudo systemctl stop aicrm"
