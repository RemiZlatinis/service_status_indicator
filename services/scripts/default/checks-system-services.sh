#!/bin/bash

source /etc/service-status-indicator/services/scripts/functions
if check_systemctl_service_all; then
    echo "ok message=All system services are running fine."
else
    echo "failure message=There is an issue with one or more system services."
fi