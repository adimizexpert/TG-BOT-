#!/usr/bin/env bash
set -euo pipefail

# deploy.sh - Idempotent deploy script for Adimi bot
# Works on Ubuntu 22.04 / 24.04
# Features:
# - installs system deps (python3.13, venv, git)
# - clones or updates repo
# - creates a venv with python3.13
# - installs requirements
# - loads .env into environment
# - starts the bot with nohup and writes pid to bot.pid

REPO_URL="https://github.com/adimizexpert/TG-BOT-.git"
APP_DIR="${HOME}/TGBOTS/Adimibot/TG-BOT-"
VENV_DIR="${APP_DIR}/venv"
PYTHON_BIN="/usr/bin/python3.13"

echo "---- Adimi bot deploy script ----"
echo "App dir: ${APP_DIR}"

echo "1) Ensure system packages are installed"
sudo apt update -y
sudo apt install -y python3.13 python3.13-venv git || {
    echo "Failed to install python3.13; ensure your Ubuntu release has python3.13 in apt or install manually."
    exit 1
}

echo "2) Clone or update repository"
mkdir -p "$(dirname "$APP_DIR")"
if [ -d "$APP_DIR/.git" ]; then
    echo "Repository exists, pulling latest..."
    git -C "$APP_DIR" fetch --all --prune
    git -C "$APP_DIR" reset --hard origin/main || git -C "$APP_DIR" pull --ff-only
else
    echo "Cloning repository into ${APP_DIR}"
    git clone "$REPO_URL" "$APP_DIR"
fi

echo "3) Create / update Python venv (using python3.13)"
if [ ! -x "$PYTHON_BIN" ]; then
    echo "Python 3.13 not found at ${PYTHON_BIN}, trying to use system python3"
    PYTHON_BIN="$(command -v python3 || true)"
    if [ -z "$PYTHON_BIN" ]; then
        echo "No python3 available. Aborting."
        exit 1
    fi
fi

cd "$APP_DIR"
if [ -d "$VENV_DIR" ]; then
    echo "Updating existing venv..."
else
    echo "Creating venv at ${VENV_DIR}"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

echo "Activating venv and installing requirements"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "requirements.txt not found in repo; aborting"
    deactivate || true
    exit 1
fi

echo "4) Load environment variables from .env (if present)"
if [ -f .env ]; then
    # Export variables from .env for the current shell session
    set -a
    # shellcheck disable=SC1091
    . .env
    set +a
    echo "Loaded .env"
else
    echo ".env not found. Ensure BOT_TOKEN is available in environment or .env file."
fi

echo "5) Ensure idempotent bot startup"
# Stop existing bot process(es) started from this repo path
if [ -f bot.pid ]; then
    OLD_PID=$(cat bot.pid || true)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" >/dev/null 2>&1; then
        echo "Stopping previous bot process PID $OLD_PID"
        kill "$OLD_PID" || true
        sleep 1
    fi
fi

# Also kill any stray python processes running bot.py from this dir
PIDS=$(pgrep -f "python.*$(basename "$APP_DIR")/bot.py" || true)
if [ -n "$PIDS" ]; then
    echo "Killing stray bot processes: $PIDS"
    echo "$PIDS" | xargs -r kill || true
fi

echo "Starting bot with nohup"
nohup "$VENV_DIR/bin/python" bot.py > bot.log 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > bot.pid
echo "Bot started (pid $NEW_PID). Logs: ${APP_DIR}/bot.log"

echo "Deployment complete. Follow logs with: tail -f ${APP_DIR}/bot.log"
