#!/usr/bin/env bash
# install.sh — Laser Tag project installer for Debian/Ubuntu
# Usage:
#   chmod +x install.sh
#   ./install.sh [--no-systemd] [--dev] [--ports "7500 7501"] [--repo <git_url>] [--dir </path/to/install>]

set -euo pipefail

# ---- Config (change if you want) ----
DEFAULT_DIR="$HOME/soft-engr-laser-tag"
DEFAULT_PORTS="7500 7501"         # SEND/RECV UDP ports you mentioned
PY_FALLBACK_REQS=("pygame" "PyQt5" "pillow")  # used if no requirements.txt
CREATE_SYSTEMD=true
DEV_MODE=false
REPO_URL=""
INSTALL_DIR="$DEFAULT_DIR"
PORTS="$DEFAULT_PORTS"

# ---- Args ----
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-systemd) CREATE_SYSTEMD=false; shift ;;
    --dev) DEV_MODE=true; shift ;;
    --ports) PORTS="$2"; shift 2 ;;
    --repo) REPO_URL="$2"; shift 2 ;;
    --dir) INSTALL_DIR="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

echo "[1/7] Checking apt…"
if ! command -v apt >/dev/null 2>&1; then
  echo "This script expects Debian/Ubuntu (apt)."; exit 1
fi

echo "[2/7] Updating & installing system packages… (sudo required)"
sudo apt update -y
sudo apt upgrade -y

# Core build & Python
sudo apt install -y \
  git curl wget unzip ca-certificates \
  build-essential pkg-config \
  python3 python3-pip python3-venv python3-dev

# GUI/toolkits frequently used in your project threads
# - tkinter: for simple GUIs
# - PyQt5 (system libs) to make sure Qt is present (pip wheels often fine, this is a safety net)
# - libsdl for pygame audio/video if needed
sudo apt install -y \
  python3-tk \
  python3-pyqt5 \
  libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev

# Optional firewall & systemd already exist on Debian, but make sure ufw is there if you want port opening:
sudo apt install -y ufw || true

# ---- Acquire code ----
echo "[3/7] Getting project files…"
if [[ -n "$REPO_URL" ]]; then
  mkdir -p "$INSTALL_DIR"
  if [[ -d "$INSTALL_DIR/.git" ]]; then
    echo "Repo already exists at $INSTALL_DIR — pulling latest…"
    git -C "$INSTALL_DIR" pull --rebase
  else
    echo "Cloning $REPO_URL into $INSTALL_DIR…"
    git clone "$REPO_URL" "$INSTALL_DIR"
  fi
else
  # If you run the script inside your repo, we just install in-place
  # Otherwise we copy the current folder into INSTALL_DIR
  if [[ -d .git ]]; then
    INSTALL_DIR="$(pwd)"
    echo "Using current directory as project root: $INSTALL_DIR"
  else
    echo "No --repo provided and current directory is not a git repo."
    echo "Creating $INSTALL_DIR and copying files there…"
    mkdir -p "$INSTALL_DIR"
    cp -a . "$INSTALL_DIR"/
  fi
fi

# ---- Python venv & deps ----
echo "[4/7] Creating virtual environment & installing Python deps…"
cd "$INSTALL_DIR"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip wheel

if [[ -f "requirements.txt" ]]; then
  echo "Installing from requirements.txt…"
  pip install -r requirements.txt
else
  echo "No requirements.txt found. Installing common deps: ${PY_FALLBACK_REQS[*]}"
  pip install "${PY_FALLBACK_REQS[@]}"
fi

# ---- .env config (used by your server/client) ----
echo "[5/7] Writing .env (non-secret runtime config)…"
ENV_FILE="$INSTALL_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  cat > "$ENV_FILE" <<EOF
# Laser Tag runtime configuration
DEFAULT_IP=127.0.0.1
SEND_PORT=7500
RECEIVE_PORT=7501
GAME_TIME_SECONDS=30
# Example: override IP/ports with environment or CLI if your app supports it
EOF
  echo "Created $ENV_FILE"
else
  echo ".env already exists, leaving it untouched."
fi

# ---- Optional: open ports via ufw ----
echo "[6/7] Opening UDP ports (if ufw is active)…"
if command -v ufw >/dev/null 2>&1; then
  if sudo ufw status | grep -q "Status: active"; then
    for P in $PORTS; do
      sudo ufw allow "${P}/udp" || true
    done
    echo "Allowed UDP ports: $PORTS"
  else
    echo "ufw is installed but not active; skipping port rules."
  fi
fi

# ---- Optional: systemd service for server.py ----
echo "[7/7] (Optional) systemd service setup…"
if $CREATE_SYSTEMD; then
  # Pick a plausible entry point; change if your server filename differs
  SERVER_ENTRY="server.py"
  if [[ -f "$SERVER_ENTRY" ]]; then
    SERVICE_NAME="laser-tag-server"
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    echo "Creating systemd service: $SERVICE_NAME"

    PY_PATH="$INSTALL_DIR/.venv/bin/python"
    cat <<SERVICE | sudo tee "$SERVICE_FILE" >/dev/null
[Unit]
Description=Laser Tag UDP Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$PY_PATH $INSTALL_DIR/$SERVER_ENTRY
Restart=on-failure
RestartSec=2
User=$USER
# If your server writes logs:
# StandardOutput=append:$INSTALL_DIR/logs/server.out
# StandardError=append:$INSTALL_DIR/logs/server.err

[Install]
WantedBy=multi-user.target
SERVICE

    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
    sudo systemctl restart "$SERVICE_NAME" || sudo systemctl start "$SERVICE_NAME"

    echo "Service '${SERVICE_NAME}' installed. Status:"
    systemctl --no-pager --full status "$SERVICE_NAME" || true
  else
    echo "No $SERVER_ENTRY found — skipping systemd service creation."
  fi
else
  echo "Systemd step skipped (--no-systemd)."
fi

echo
echo "✅ Install finished."
echo "Project dir: $INSTALL_DIR"
echo "To use the venv now: source $INSTALL_DIR/.venv/bin/activate"
echo "If you created the service: journalctl -u laser-tag-server -f  (to tail logs)"
$DEV_MODE && echo "Dev mode: you can run 'python client.py' or 'python server.py' manually inside the venv."
