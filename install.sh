#!/bin/bash

echo "Updating package lists..."
sudo apt update

# Install a specific package (e.g., htop)
echo "Installing python packages"
sudo apt install python python3 python3-pyqt5 python3-pyqt5.qtquick python3-pyqt5.qtsvg python3-psycopg2

echo "Packages installed. Opening application..."
python3 main.py
