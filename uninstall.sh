#!/bin/bash

# Check for root privileges 
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root" 
    exit 1
fi

# TODO: Add confirmation.

systemctl disable --now service-status-indicator-api.service &> /dev/null
systemctl disable --now service-status-indicator-scheduler.service &> /dev/null
rm /etc/systemd/system/service-status-indicator-* &> /dev/null
rm /usr/bin/local/ssi &> /dev/null
rm -rf /etc/service-status-indicator/ &> /dev/null
echo "✅ Uninstall complete. Bye bye 👋"