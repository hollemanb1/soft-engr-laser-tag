#!/usr/bin/env bash
set -Eeuo pipefail

# ---- Settings ----
VENV_DIR="venvc"
REQS_FILE="requirements.txt"
LOG_FILE="pip_install.log"

echo "[+] Updating apt and installing Python + build prerequisites..."
sudo apt-get update -y

# Core Python & venv
sudo apt-get install -y python3 python3-venv python3-pip

# Common build deps that fix 'metadata-generation-failed' for many packages
# - build-essential, python3-dev: compile C/C++ extensions
# - pkg-config, libffi-dev, libssl-dev: cryptography/ffi deps
# - rustc, cargo: many modern wheels (e.g., cryptography>=41, orjson) need Rust
# - Optional but helpful: libjpeg-dev, zlib1g-dev, libxml2-dev, libxslt1-dev
sudo apt-get install -y \
  build-essential python3-dev pkg-config \
  libffi-dev libssl-dev \
  rustc cargo \
  libjpeg-dev zlib1g-dev libxml2-dev libxslt1-dev

# Create venv if missing
if [ ! -d "$VENV_DIR" ]; then
  echo "[+] Creating virtual environment: $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

echo "[+] Activating virtual environment..."
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# Ensure latest pip tooling to reduce build issues
echo "[+] Upgrading pip, setuptools, wheel..."
python -m pip install --upgrade pip setuptools wheel

# Optional helper for PEP 517 projects that use setuptools_scm, hatchling, etc.
python -m pip install --upgrade setuptools-scm hatchling tomli || true

if [ -f "$REQS_FILE" ]; then
  echo "[+] Installing dependencies from $REQS_FILE (logging to $LOG_FILE)..."
  # Capture detailed logs to help diagnose any build-backend failures
  # --use-pep517 ensures modern builds; --no-cache-dir avoids stale wheels
  # If something fails, we show the tail of the log.
  set +e
  python -m pip install --use-pep517 --no-cache-dir -r "$REQS_FILE" 2>&1 | tee "$LOG_FILE"
  status=${PIPESTATUS[0]}
  set -e
  if [ $status -ne 0 ]; then
    echo ""
    echo "[!] pip reported an error (likely from a package build subprocess)."
    echo "    Showing last 50 lines of $LOG_FILE for the failing package:"
    tail -n 50 "$LOG_FILE" || true
    echo ""
    echo "Tips:"
    echo "  • Ensure the failing package lists prebuilt wheels for your Python/Debian combo."
    echo "  • If it's 'cryptography' or anything Rust-based, Rust is already installed here."
    echo "  • If it's a DB driver (e.g., psycopg2), you may need libpq-dev."
    echo "  • For MySQL drivers, you may need default-libmysqlclient-dev."
    echo "  • Re-run after adding the needed -dev package."
  fi
else
  echo "[!] $REQS_FILE not found. Skipping pip install."
fi

echo ""
echo "[+] Done. Dropping you into the virtualenv shell now."
echo "    To leave: 'exit' (you'll return to your previous shell)."
# Replace the current process with an interactive shell that keeps the venv active
exec bash -i






# #!/usr/bin/env bash
# set -euo pipefail

# echo "[+] Updating package list..."
# sudo apt-get update -y

# echo "[+] Installing Python3 and venv..."
# sudo apt-get install -y python3 python3-venv python3-pip

# # create venv if it doesn’t exist
# if [ ! -d "venvc" ]; then
#     echo "[+] Creating virtual environment: venvc"
#     python3 -m venv venvc
# fi

# echo "[+] Activating virtual environment..."
# # shellcheck source=/dev/null
# source venvc/bin/activate

# if [ -f "requirements.txt" ]; then
#     echo "[+] Installing dependencies from requirements.txt..."
#     pip install --upgrade pip
#     pip install -r requirements.txt
# else
#     echo "[!] requirements.txt not found. Skipping pip install."
# fi

# echo "[+] Setup complete. Virtual environment is ready."
# echo "To activate later, run: source venvc/bin/activate"






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
