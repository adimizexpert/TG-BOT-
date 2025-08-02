#!/bin/bash

# Telegram Bot Deployment Script
# This script sets up the bot on a VPS

echo "🚀 Starting Telegram Bot Deployment..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please don't run this script as root"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "🔧 Installing Python and dependencies..."
sudo apt install -y python3 python3-pip python3-venv git curl

# Create bot directory
BOT_DIR="$HOME/telegram-bot"
echo "📁 Creating bot directory: $BOT_DIR"
mkdir -p "$BOT_DIR"
cd "$BOT_DIR"

# Copy bot files (assuming script is run from bot directory)
echo "📋 Copying bot files..."
cp -r . "$BOT_DIR/"

# Setup virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create systemd service
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/telegram-bot.service > /dev/null <<EOF
[Unit]
Description=Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BOT_DIR
Environment=BOT_TOKEN=$(grep BOT_TOKEN .env | cut -d '=' -f2)
ExecStart=$BOT_DIR/venv/bin/python working_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
echo "🔄 Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# Check status
echo "📊 Checking service status..."
sudo systemctl status telegram-bot --no-pager

echo "✅ Deployment complete!"
echo "📝 Useful commands:"
echo "  - View logs: sudo journalctl -u telegram-bot -f"
echo "  - Restart bot: sudo systemctl restart telegram-bot"
echo "  - Stop bot: sudo systemctl stop telegram-bot"
echo "  - Check status: sudo systemctl status telegram-bot" 