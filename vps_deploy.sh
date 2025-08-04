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
BOT_DIR="/home/botuser/telegram-bot"
SERVICE_NAME="telegram-bot"

echo "📁 Setting up bot directory..."
cd $BOT_DIR || { echo "❌ Bot directory not found!"; exit 1; }

echo "🐍 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "⚙️ Checking .env file..."
if [ ! -f ".env" ]; then
    echo "❌ .env file not found! Creating template..."
    echo "BOT_TOKEN=YOUR_BOT_TOKEN_HERE" > .env
    echo "⚠️  Please edit .env file with your bot token!"
    echo "   nano .env"
    exit 1
fi

echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=Client Privacy Manager Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=$BOT_DIR
Environment=PATH=$BOT_DIR/venv/bin
ExecStart=$BOT_DIR/venv/bin/python $BOT_DIR/final_bot.py
Restart=always
RestartSec=10

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