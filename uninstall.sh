#!/bin/bash

# Check if is installed
if [ ! -d "/etc/service-status-indicator-api/" ]; then
    echo "Service Status Indicator API is not installed."
    exit 0 
fi


# Check for root privileges 
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root" 
    exit 1
fi


# Disable systemd service
systemctl disable --now service-status-indicator-api.service


# Remove files
rm -rf /etc/service-status-indicator-api/