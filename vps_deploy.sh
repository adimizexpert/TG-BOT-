#!/bin/bash

# VPS Deployment Script for Client Privacy Manager Bot
# Run this script on your VPS after uploading the bot files

echo "🚀 Client Privacy Manager Bot - VPS Deployment"
echo "=============================================="

# Check if running as botuser
if [ "$USER" != "botuser" ]; then
    echo "❌ Please run this script as 'botuser'"
    echo "   Switch user: su - botuser"
    exit 1
fi

# Set variables
BOT_DIR="/home/botuser/TGBOTS/Adimibot/TG-BOT-"
SERVICE_NAME="telegram-bot"


echo "📁 Setting up bot directory..."
mkdir -p "$BOT_DIR"
cd "$BOT_DIR" || { echo "❌ Bot directory not found!"; exit 1; }

echo "🐍 Creating virtual environment (if missing)..."
python3 -m venv venv || true
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install --upgrade pip setuptools wheel
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt not found — make sure it's in the repo"
fi

echo "⚙️ Checking .env file..."
if [ ! -f ".env" ]; then
    echo "❌ .env file not found! Creating template..."
    echo "BOT_TOKEN=YOUR_BOT_TOKEN_HERE" > .env
    echo "⚠️  Please edit .env file with your bot token!"
    echo "   nano .env"
    exit 1
fi

echo "🔧 Creating systemd service (uses venv/bin/python3 and loads .env)"
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=Client Privacy Manager Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=$BOT_DIR
# Load environment variables from the project's .env
EnvironmentFile=$BOT_DIR/.env
Environment=PYTHONUNBUFFERED=1
ExecStart=$BOT_DIR/venv/bin/python3 $BOT_DIR/bot.py
Restart=on-failure
RestartSec=10
StandardOutput=append:$BOT_DIR/bot.log
StandardError=append:$BOT_DIR/bot.log

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo "📊 Service status:"
sudo systemctl status $SERVICE_NAME --no-pager

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📋 Useful commands:"
echo "   Check status: sudo systemctl status $SERVICE_NAME"
echo "   View logs:    sudo journalctl -u $SERVICE_NAME -f"
echo "   Restart:      sudo systemctl restart $SERVICE_NAME"
echo "   Stop:         sudo systemctl stop $SERVICE_NAME"
echo ""
echo "🔥 Your bot should now be running on the VPS!" 