#!/usr/bin/env bash
set -euo pipefail

# --- config ---
PY=python3
VENV_DIR=".venv"

log() { printf "\033[1;32m[+]\033[0m %s\n" "$*"; }
err() { printf "\033[1;31m[!]\033[0m %s\n" "$*" >&2; }

# --- detect package manager & install system deps ---
install_sys() {
  if command -v tdnf >/dev/null 2>&1; then
    log "Using tdnf (Photon)"
    sudo tdnf install -y python3 python3-pip git
    # optional build tools if you compile wheels
    sudo tdnf install -y gcc make || true
  elif command -v apt-get >/dev/null 2>&1; then
    log "Using apt (Debian/Ubuntu)"
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-venv python3-pip git build-essential
  elif command -v dnf >/dev/null 2>&1; then
    log "Using dnf (Fedora/RHEL)"
    sudo dnf install -y python3 python3-pip git @development-tools
  else
    err "No supported package manager found. Install python3 & pip manually."
  fi
}

# --- create venv & install Python deps ---
setup_venv() {
  if [ ! -d "$VENV_DIR" ]; then
    log "Creating virtualenv in $VENV_DIR"
    $PY -m venv "$VENV_DIR"
  fi
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  log "Upgrading pip"
  python -m pip install --upgrade pip wheel
  if [ -f requirements.txt ]; then
    log "Installing requirements.txt"
    pip install -r requirements.txt
  else
    log "No requirements.txt found (skipping)"
  fi
}

# --- basic smoke tests (edit to your app) ---
smoke_test() {
  log "Running smoke test"
  python - <<'PY'
print("Python OK")
import sys, os
print("cwd:", os.getcwd())
print("venv site:", sys.prefix)
PY
  # quick import checks if you have known modules:
  # python -c "import pygame; print('pygame OK')"
}

# --- convenience runners ---
create_launchers() {
  # server launcher
  cat > run_server.sh <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
exec python server.py "$@"
EOS
  chmod +x run_server.sh

  # client launcher
  cat > run_client.sh <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
exec python client.py "$@"
EOS
  chmod +x run_client.sh

  # splash launcher (if you want)
  if [ -f splash.py ]; then
    cat > run_splash.sh <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
exec python splash.py "$@"
EOS
    chmod +x run_splash.sh
  fi
}

main() {
  install_sys
  setup_venv
  smoke_test
  create_launchers
  log "Install complete."
  log "Use: source .venv/bin/activate && python server.py"
  log "Or:  ./run_server.sh  (and ./run_client.sh, ./run_splash.sh)"
}

main "$@"
