#!/bin/bash

# wget -qO- https://service-status-indicator.remiservices.uk/install.sh | sudo sh - 

# Check for root privileges 
if [[ $EUID -ne 0 ]]; then
    echo "❕ Installation script must run with root privileges." 
    exit 1
fi



# Create temporarily structure folder  
rm -rf .ssi_temp &> /dev/null
mkdir .ssi_temp
mkdir .ssi_temp/src
mkdir .ssi_temp/src/scripts



# Keep existing user stuff from previous installation 
cp /etc/service-status-indicator/services/users.json .ssi_temp/services/users.json &> /dev/null
cp -r /etc/service-status-indicator/services/scripts/users .ssi_temp/services/scripts/ &> /dev/null
ssi &> /dev/null 2>&1 && enabled=$(ssi get-enabled-services-ids)



# Clean previous installation
systemctl disable --now service-status-indicator-api &> /dev/null
systemctl disable --now service-status-indicator-scheduler &> /dev/null
rm -rf /etc/service-status-indicator &> /dev/null
rm /etc/systemd/system/service-status-indicator-* &> /dev/null



# Check if systemd process is running
if ! ps -p 1 | grep -q systemd; then
    echo "❌ Only systemd is supported"
    exit 1
fi

# Check for Python
if ! command -v python &> /dev/null; then
    echo "❌ Python is unavailable."
    exit 1
fi



# Download necessary stuff
echo -ne " ⬇️ Downloading source files..."
repo="https://github.com/RemiZlatinis/service_status_indicator"
tar_file=".ssr_temp.tar.gz"
curl -L -o "$tar_file" "$repo/archive/master.tar.gz" &> /dev/null
tar -xzvf "$tar_file" &> /dev/null
rm "$tar_file" &> /dev/null
cd service_status_indicator-main

cp api.py ../.ssi_temp/src
cp cli.py ../.ssi_temp/src
cp helpers.py ../.ssi_temp/src
cp config.py ../.ssi_temp/src
cp database.py ../.ssi_temp/src
cp logger.py ../.ssi_temp/src
cp models.py ../.ssi_temp/src
cp scheduler.py ../.ssi_temp/src
cp service_registry.py ../.ssi_temp/src
cp wsgi.py ../.ssi_temp/src

cp -r scripts ../.ssi_temp/src
cp -r services ../.ssi_temp/
cp -r units ../.ssi_temp/
cd ..
rm -rf service_status_indicator-main
echo -e "\r✅ Download complete.            "


# Configure port
read -p "⚙️  Enter a PORT for the API [default: 8000]: " port
if [[ -z "$port" ]]; then
  port="8000"
fi
# Replace the port on server's staring script
sed -i "s/0\.0\.0\.0:{PORT}/0.0.0.0:$port/g" .ssi_temp/src/scripts/start-server.sh
echo -e "\033[1A\033[K✅ PORT successfully set to $port.            "


# Copy source files
rm -rf /etc/service-status-indicator
mv .ssi_temp /etc/service-status-indicator



# Create a Python virtual environment & install dependencies
cd /etc/service-status-indicator/src
echo -ne " ⬇️ Installing dependencies..."
python -m venv .env
source .env/bin/activate
pip install flask gunicorn qrcode &> /dev/null
deactivate
cd /etc/service-status-indicator/



# Move systemd services
echo -ne "\r🔧 Configure system services..."
mv units/* /etc/systemd/system/
rm -r units
systemctl daemon-reload
systemctl enable --now service-status-indicator-api &> /dev/null
systemctl enable --now service-status-indicator-scheduler &> /dev/null
echo -e "\r✅ Installation complete.         "



# Re-enable services
/etc/service-status-indicator/src/scripts/ssi bulk-enable $enabled



echo # New line & Create a symbolic link for the CLI
ln -sf /etc/service-status-indicator/src/scripts/ssi /usr/local/bin
echo "🛠️  Service Status Indicator CLI is now available."
echo '🦯 Use "sudo ssi" to find more.'
