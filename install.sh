#!/usr/bin/env bash
set -euo pipefail

echo "[+] Updating package list..."
sudo apt-get update -y

echo "[+] Installing Python3 and venv..."
sudo apt-get install -y python3 python3-venv python3-pip

# create venv if it doesn’t exist
if [ ! -d "venvc" ]; then
    echo "[+] Creating virtual environment: venvc"
    python3 -m venv venvc
fi

echo "[+] Activating virtual environment..."
# shellcheck source=/dev/null
source venvc/bin/activate

if [ -f "requirements.txt" ]; then
    echo "[+] Installing dependencies from requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "[!] requirements.txt not found. Skipping pip install."
fi

echo "[+] Setup complete. Virtual environment is ready."
echo "To activate later, run: source venvc/bin/activate"






# #!/usr/bin/env bash

# # Use bash; env helps find it on different systems.

# set -Eeuo pipefail

# # E: preserve ERR, traps in functions and subshells
# # e: exit on first error
# # u: error on unset variables
# # o: fail if any command in a pipeline fails

# cd "$(dirname "$0")"

# # always run relative to the script file; the parent dir of install.sh
# # now for sanity checking:
# [[ -f server.py ]] || { echo "ERROR: server.py not found in $(pwd)"; exit 1; }
# # requires a requirements.txt or both that and requirements.base.txt
# if [[ ! -f requirements.txt && ! -f requirements.base.txt ]]; then
#   echo "ERROR: Provide requirements.txt OR requirements.base.txt (with optional requirements.gui.txt)."
#   exit 1
# fi

# echo "[+] Checking system Python & pip ..."
# # install python and pip for various distros
# if command -v tdnf >/dev/null 2>&1; then
# # Photon os 
#   sudo tdnf install -y python3 python3-pip || true
# elif command -v apt-get >/dev/null 2>&1; then
# # Debian or Ubuntu
#   sudo apt-get update -y
#   sudo apt-get install -y python3 python3-venv python3-pip
# elif command -v dnf >/dev/null 2>&1; then
# # Fedora
#   sudo dnf install -y python3 python3-pip
# else
#   echo "[WARN] Unknown distro. Ensure python3 & pip are installed."
# fi

# # set up the virtual environment
# if [[ ! -d .venv ]]; then
#   echo "[+] Creating venv ..."
#   python3 -m venv .venv
# fi
# # activate the virutual environment for the rest of the pip and python calls
# # shellcheck disable=SC1091
# source .venv/bin/activate
# # make sure modern packaging tools are present
# python -m pip install --upgrade pip setuptools wheel

# # dependencies install logic
# if [[ -f requirements.base.txt ]]; then
#   echo "[+] Installing base deps..."
#   pip install -r requirements.base.txt
# # optional GUI dependendicies from the requirements.gui.txt
#   if [[ "${WITH_GUI:-0}" == "1" && -f requirements.gui.txt ]]; then
#     echo "[+] Installing GUI deps (wheels only)..."
#     # try to install GUI deps, but don't fail if it doesn't work (no compatible wheels)
#     PIP_ONLY_BINARY=":all:" pip install -r requirements.gui.txt -v \
#       || echo "[WARN] GUI deps not installed (no compatible wheels). Continuing without GUI."
#   fi
# else
#   echo "[+] Installing deps from requirements.txt..."
#   pip install -r requirements.txt
# fi

# echo "[+] Starting server.py ..."
# # replace shell with the python process
# echo "[+] Virtual environment ready. Dropping you into shell..."
# exec $SHELL --rcfile <(echo "source .venv/bin/activate; exec $SHELL -i")
