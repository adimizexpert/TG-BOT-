#!/bin/bash

# Activate virtual environment
export VIRTUAL_ENV="$(pwd)/venv"
export PATH="$VIRTUAL_ENV/bin:$PATH"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    exit 1
fi

# Check if bot.py exists
if [ ! -f "bot.py" ]; then
    echo "❌ Error: bot.py not found!"
    exit 1
fi

echo "🤖 Starting Client Privacy Manager Bot..."
echo "✅ Environment: $(python --version)"
echo "✅ Virtual Environment: $VIRTUAL_ENV"
echo "🔄 Bot is starting..."

# Run the bot with error handling
python bot.py

# If the bot exits, show status
echo "🛑 Bot stopped" 