#!/usr/bin/env bash
set -euo pipefail

echo "Updating package list..."
sudo apt-get update -y

# installing xcb, cursor, and all necessary depensencies for PySide6

echo "Installing system dependencies for Python, venv, and Qt/XCB..."
sudo apt-get install -y \
  python3 python3-venv python3-pip \
  libx11-6 libx11-xcb1 libxext6 libxrender1 libxkbcommon-x11-0 \
  libxcb1 libxcb-cursor0 libxcb-image0 libxcb-icccm4 libxcb-keysyms1 \
  libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-shm0 \
  libxcb-sync1 libxcb-xfixes0 libxcb-xinerama0 libxcb-xkb1 \
  libglib2.0-0 libsm6 libdbus-1-3 libfontconfig1 libfreetype6 \
  libglu1-mesa \
  libqt6gui6 libqt6widgets6 libqt6waylandclient6

# if there is no virtual enviroment create one
if [ ! -d "venvc" ]; then
  echo "[+] Creating virtual environment: venvc"
  python3 -m venv venvc
fi

echo "Activating virtual environment..."
# get in the virtual enviroment
source venvc/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

# prevent plugin path conflicts
unset QT_PLUGIN_PATH
export QT_QPA_PLATFORM=xcb

# enforce 1 Qt binding (PySide6)
# if user asked for PyQt5, comment PySide6 and install PyQt5 instead.
echo "Ensuring only one Qt binding is installed..."
pip uninstall -y PyQt5 PyQt5-Qt5 PyQt5-sip PySide2 || true
pip install -U PySide6

if [ -f "requirements.txt" ]; then
  # warn if both bindings appear in requirements.txt
  if grep -qiE '(^|\s)(PyQt5|PySide2)\b' requirements.txt && grep -qiE '(^|\s)PySide6\b' requirements.txt; then
    echo "[-] ERROR: requirements.txt includes both PyQt/PySide variants. Keep ONE (recommend PySide6)."
    exit 2
  fi
  # install all listed in requiremtnsts.txt
  echo "Installing requirements.txt..."
  pip install -r requirements.txt
else
  echo "requirements.txt not found. Skipping pip install."
fi

# guarntee psycopg2 is present and importable 
echo "[+] Verifying psycopg2 import..."
set +e
python - <<'PY'
try:
    import psycopg2
    print("OK: psycopg2 is importable.")
except Exception as e:
    import sys
    print("MISSING: psycopg2 not importable ->", e, file=sys.stderr)
    sys.exit(1)
PY
status=$?
set -e

if [ $status -ne 0 ]; then
    echo "[+] Installing psycopg2-binary explicitly..."
    pip install -U 'psycopg2-binary>=2.9'
    echo "[+] Re-checking psycopg2 import..."
    python - <<'PY'
import psycopg2
print("OK: psycopg2 now importable. Version:", psycopg2.__version__)
PY
fi

echo "Setup complete."
echo "To activate later: source venvc/bin/activate"
