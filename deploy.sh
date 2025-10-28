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
# Target VPS user and app dir (explicit for idempotent deploys)
BOT_USER="botuser"
APP_DIR="/home/${BOT_USER}/TGBOTS/Adimibot/TG-BOT-"
VENV_DIR="${APP_DIR}/venv"
PYTHON_BIN="/usr/bin/python3.13"

# Pyenv/python version to install if system python3.13 isn't available
PYTHON_VERSION="3.13.3"

echo "---- Adimi bot deploy script ----"
echo "App dir: ${APP_DIR}"

echo "1) Ensure system packages (basic) are installed"
sudo apt update -y
sudo apt install -y git curl build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget llvm libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev \
    python3-venv || true

# If python3.13 is not available from apt, we'll use pyenv later to build it.

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

# Determine python binary: prefer system python3.13, else try pyenv or system python3
if command -v python3.13 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3.13)"
    echo "Using system python: $PYTHON_BIN"
else
    echo "python3.13 not found system-wide; will attempt pyenv install of ${PYTHON_VERSION}"
    # Install pyenv if missing
    if [ ! -d "$HOME/.pyenv" ]; then
        echo "Installing pyenv (user-level)"
        curl https://pyenv.run | bash
        # Load pyenv into current shell
        export PYENV_ROOT="$HOME/.pyenv"
        export PATH="$PYENV_ROOT/bin:$PATH"
        eval "$(pyenv init -)" || true
    else
        export PYENV_ROOT="$HOME/.pyenv"
        export PATH="$PYENV_ROOT/bin:$PATH"
        eval "$(pyenv init -)" || true
    fi

    # Install desired Python version if not present
    if ! pyenv versions --bare | grep -q "^${PYTHON_VERSION}$"; then
        echo "Installing Python ${PYTHON_VERSION} via pyenv (this may take a few minutes)"
        pyenv install -s "${PYTHON_VERSION}"
    fi

    # Set local python for app dir
    mkdir -p "$APP_DIR"
    pushd "$APP_DIR" >/dev/null || true
    pyenv local "${PYTHON_VERSION}"
    popd >/dev/null || true

    # Use pyenv's python
    PYTHON_BIN="$HOME/.pyenv/versions/${PYTHON_VERSION}/bin/python3"
    echo "Using pyenv python: $PYTHON_BIN"
fi

cd "$APP_DIR"
if [ -d "$VENV_DIR" ]; then
    echo "Updating existing venv..."
else
    echo "Creating venv at ${VENV_DIR} using $PYTHON_BIN"
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
PIDS=$(pgrep -f "${APP_DIR}/bot.py" || true)
if [ -n "$PIDS" ]; then
    echo "Killing stray bot processes: $PIDS"
    echo "$PIDS" | xargs -r kill || true
fi

echo "Starting bot with nohup"
nohup "$VENV_DIR/bin/python3" bot.py >> "$APP_DIR/bot.log" 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > bot.pid
echo "Bot started (pid $NEW_PID). Logs: ${APP_DIR}/bot.log"

echo "Deployment complete. Follow logs with: tail -f ${APP_DIR}/bot.log"
