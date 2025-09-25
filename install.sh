#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"

# --- sanity checks ---
[[ -f server.py ]] || { echo "ERROR: server.py not found in $(pwd)"; exit 1; }
if [[ ! -f requirements.txt && ! -f requirements.base.txt ]]; then
  echo "ERROR: Provide requirements.txt OR requirements.base.txt (with optional requirements.gui.txt)."
  exit 1
fi

echo "[+] Checking system Python & pip ..."
if command -v tdnf >/dev/null 2>&1; then
  sudo tdnf install -y python3 python3-pip || true
elif command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y python3 python3-venv python3-pip
elif command -v dnf >/dev/null 2>&1; then
  sudo dnf install -y python3 python3-pip
else
  echo "[WARN] Unknown distro. Ensure python3 & pip are installed."
fi

# --- venv ---
if [[ ! -d .venv ]]; then
  echo "[+] Creating venv ..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel

# --- deps install (two modes) ---
if [[ -f requirements.base.txt ]]; then
  echo "[+] Installing base deps..."
  pip install -r requirements.base.txt

  if [[ "${WITH_GUI:-0}" == "1" && -f requirements.gui.txt ]]; then
    echo "[+] Installing GUI deps (wheels only)..."
    PIP_ONLY_BINARY=":all:" pip install -r requirements.gui.txt -v \
      || echo "[WARN] GUI deps not installed (no compatible wheels). Continuing without GUI."
  fi
else
  echo "[+] Installing deps from requirements.txt..."
  pip install -r requirements.txt
fi

echo "[+] Starting server.py ..."
exec python server.py
