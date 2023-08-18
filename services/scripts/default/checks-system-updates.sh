#!/bin/bash

# Determine the package manager
if [ -x "$(command -v pacman -h)" ]; then
    # Arch-based distribution
    PM="pacman"
elif [ -x "$(command -v apt-get)" ]; then
    # Debian-based distribution
    PM="apt-get"
else
    echo "Unsupported distribution."
    exit 1
fi



# Get the number of available updates
if [ $PM = "pacman" ]; then
    sudo pacman -Syy # Update the local database
    NUM_UPDATES=$(sudo pacman -Qu | wc -l)
else
    sudo $PM update 2>&1 # Refresh the package list
    NUM_UPDATES=$(sudo apt-get -s upgrade | grep -c ^Inst)
fi

# If there are no updates available, exit the script
if [ $NUM_UPDATES -eq 0 ]; then
    echo "ok message=Your system is up-to-date."
    exit 0
fi
echo "update message=There are $NUM_UPDATES available system updates."