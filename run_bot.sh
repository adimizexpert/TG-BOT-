#!/usr/bin/env bash
set -euo pipefail

# run_bot.sh — start the bot using the project's venv python3
# Ensures .env is sourced, logs written to bot.log in project root,
# and prevents duplicate processes by recording PID in bot.pid

BOT_USER="botuser"
APP_DIR="/home/${BOT_USER}/TGBOTS/Adimibot/TG-BOT-"
VENV_DIR="$APP_DIR/venv"
PYTHON="$VENV_DIR/bin/python3"
PID_FILE="$APP_DIR/bot.pid"
LOG_FILE="$APP_DIR/bot.log"

echo "🔁 run_bot.sh — starting in ${APP_DIR}"

if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Virtualenv not found at $VENV_DIR"
    echo "Create one with: python3 -m venv venv"
    exit 1
fi

if [ ! -f "bot.py" ]; then
    echo "❌ bot.py not found in ${APP_DIR}"
    exit 1
fi

if [ -f "$APP_DIR/.env" ]; then
    echo "📥 Loading .env"
    # shellcheck disable=SC1090
    set -a
    # shellcheck disable=SC1091
    . "$APP_DIR/.env"
    set +a
else
    echo "⚠️  .env not found — ensure BOT_TOKEN is in environment"
fi

# Kill any existing process started from this directory running bot.py
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE" || true)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" >/dev/null 2>&1; then
        echo "Stopping previous bot process (pid $OLD_PID)"
        kill "$OLD_PID" || true
        sleep 1
    fi
fi

PIDS=$(pgrep -f "${APP_DIR}/bot.py" || true)
if [ -n "$PIDS" ]; then
    echo "Killing stray bot processes: $PIDS"
    echo "$PIDS" | xargs -r kill || true
fi

echo "▶ Starting bot with $PYTHON — logs: $LOG_FILE"
nohup "$PYTHON" bot.py >> "$LOG_FILE" 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > "$PID_FILE"
echo "Started (pid $NEW_PID)"