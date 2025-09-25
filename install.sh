#!/usr/bin/env bash
set -Eeuo pipefail

# Always run from the script’s folder
cd "$(dirname "$0")"

# 0) Sanity checks
[[ -f server.py ]] || { echo "ERROR: server.py not found in $(pwd)"; exit 1; }
[[ -f requirements.txt ]] || { echo "ERROR: requirements.txt not found"; exit 1; }

echo "[+] Checking system Python & pip ..."
if command -v tdnf >/dev/null 2>&1; then
  # Photon OS
  sudo tdnf install -y python3 python3-pip || true
elif command -v apt-get >/dev/null 2>&1; then
  # Debian/Ubuntu
  sudo apt-get update -y
  sudo apt-get install -y python3 python3-venv python3-pip
elif command -v dnf >/dev/null 2>&1; then
  sudo dnf install -y python3 python3-pip
else
  echo "WARN: Unknown distro. Make sure python3 & pip are installed."
fi

# 1) Create virtual environment (local to project)
if [[ ! -d .venv ]]; then
  echo "[+] Creating venv ..."
  python3 -m venv .venv
fi

# 2) Activate and install deps
echo "[+] Installing dependencies ..."
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip wheel
pip install -r requirements.txt

# 3) Run the server (foreground)
echo "[+] Starting server.py ..."
exec python server.py
