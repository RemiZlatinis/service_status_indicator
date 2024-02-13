#!/bin/bash

# wget -qO- https://service-status-indicator.remiservices.uk/install.sh | sudo sh - 
indicator_folder="/etc/service-status-indicator"
if [ -d "$indicator_folder" ]; then
  echo -ne "🔽 Updating..."
else
  echo -ne "🔄 Loading..."
fi


# Check for root privileges 
if [[ $EUID -ne 0 ]]; then
    echo "❕ Installation script must run with root privileges." 
    exit 1
fi

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



# Create a temporary structured folder  
rm -rf .ssi_temp &> /dev/null
mkdir .ssi_temp
cd .ssi_temp
mkdir services
mkdir services/scripts
mkdir src
mkdir src/scripts



# Keep existing user stuff from the previous installation 
cp /etc/service-status-indicator/.config.json . &> /dev/null
cp /etc/service-status-indicator/services/users.json services/users.json &> /dev/null
cp -r /etc/service-status-indicator/services/scripts/users services/scripts/ &> /dev/null
ssi &> /dev/null 2>&1 && enabled=$(ssi get-enabled-services-ids)
if [ -e /etc/service-status-indicator/src/scripts/start-server.sh ]; then
  previous_port=$(grep -oP '0\.0\.0\.0:\K\d+' /etc/service-status-indicator/src/scripts/start-server.sh)
fi


# Clean previous installation
systemctl disable --now service-status-indicator-api &> /dev/null
systemctl disable --now service-status-indicator-scheduler &> /dev/null
rm -rf /etc/service-status-indicator &> /dev/null
rm /etc/systemd/system/service-status-indicator-api &> /dev/null
rm /etc/systemd/system/service-status-indicator-scheduler &> /dev/null



# Download source code
echo -ne "\r🔽 Downloading source files..."
repo="https://github.com/RemiZlatinis/service_status_indicator"
tar_file=".ssr_temp.tar.gz"
curl -L -o "$tar_file" "$repo/archive/master.tar.gz" &> /dev/null
tar -xzvf "$tar_file" &> /dev/null
rm "$tar_file" &> /dev/null
cd service_status_indicator-main

# Copy necessary folders (into the temporarily structured folder)
cp -r scripts ../src
cp -r units ../

# Copy necessary modules
cp api.py ../src
cp cli.py ../src
cp config.py ../src
cp database.py ../src
cp helpers.py ../src
cp logger.py ../src
cp models.py ../src
cp scheduler.py ../src
cp service_registry.py ../src
cp wsgi.py ../src


# Copy services and scripts
if [ ! -e ../services/users.json ] && [ ! -e ../services/scripts/users ]; then
    # If there isn't user stuff override anything
    cp -r services ../
else
    # Copy only built-in services and scripts
    cp services/default.json ../services/
    cp services/scripts/functions ../services/scripts/
    cp -r services/scripts/default ../services/scripts/
fi


cd .. # .ssi_temp directory is one level up
rm -rf service_status_indicator-main
echo -e "\r✅ Download complete.            "




# Configure port
default_port="8000"
port="${previous_port:-$default_port}"

read -p "⚙️  Enter a PORT for the API [default: $port]: " new_port

if [[ -n "$new_port" ]]; then
  port="$new_port"
fi

# Replace the port in the server's starting script
sed -i "s/0\.0\.0\.0:{PORT}/0.0.0.0:$port/g" src/scripts/start-server.sh
echo -e "\033[1A\033[K✅ PORT successfully set to $port.            "



# Copy source files
rm -rf /etc/service-status-indicator
cd ..
mv .ssi_temp /etc/service-status-indicator




# Install Debian dependencies
apt-get install python3-venv -y &> /dev/null


# Create a Python virtual environment & install dependencies
cd /etc/service-status-indicator/src
echo -ne "🔽 Installing dependencies..."
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
