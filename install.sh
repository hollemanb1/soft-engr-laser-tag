#!/usr/bin/env bash
set -euo pipefail
#e: exit on first error
#u: error on unset variables
#o: fail if any command in a pipeline fails
#pipefall: fail if any command in a pipeline fails

echo "Updating package list..."
sudo apt-get update -y

#use sudo apt-get install -y to avoid prompts, then install python3, venv, pip, and libxcb-cursor0
# libxcb-cursor0 is needed for PyQt5
echo "Install dependencies..."
sudo apt-get install -y python3 python3-venv python3-pip libxcb-cursor0
sudo apt install python python3-pyqt5 python3-pyqt5.qtquick python3-pyqt5.qtsvg python3-psycopg2

# create venv if it doesn’t exist
if [ ! -d "venvc" ]; then
    echo "[+] Creating virtual environment: venvc"
    python3 -m venv venvc
fi

# ensure QT_DEBUG_PLUGINS is set whenever this venv is activated
# if ! grep -q 'QT_DEBUG_PLUGINS' venvc/bin/activate; then
#     echo "[+] Adding QT_DEBUG_PLUGINS=1 to venv activation"
#     {
#         echo ""
#         echo "# Enable Qt plugin debug output for PySide6/PyQt"
#         echo "export QT_DEBUG_PLUGINS=1"
#     } >> venvc/bin/activate
# fi

echo "Activating virtual environment..."
# shellcheck source=/dev/null
source venvc/bin/activate

if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "requirements.txt not found. Skipping pip install."
fi

echo "Setup complete, and virtual environment is ready."
echo "To activate, run: source venvc/bin/activate"
