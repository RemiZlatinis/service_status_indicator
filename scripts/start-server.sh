#!/bin/bash
if systemctl is-active service-status-indicator-scheduler >/dev/null 2>&1; then
  source .env/bin/activate
  gunicorn -b 0.0.0.0:{PORT} wsgi:app --log-level=info --log-file=/var/log/gunicorn.log
else
  exit 1
fi