#!/bin/bash

# Bot Manager Script - Prevents Multiple Instances
# Usage: ./bot_manager.sh [local|vps|stop|status]

BOT_TOKEN="8345847465:AAEKaXDbiAx_fgb77uH-pZ9k6V2xVUHwU04"

echo "🤖 Client Privacy Manager - Bot Manager"
echo "======================================"

case "$1" in
    "local")
        echo "🏠 Starting LOCAL bot..."
        echo "⚠️  Make sure VPS bot is stopped first!"
        read -p "Press Enter to continue or Ctrl+C to cancel..."
        
        # Stop any existing local instances
        pkill -f "python.*bot.py" 2>/dev/null || true
        pkill -f "python.*final_bot.py" 2>/dev/null || true
        
        # Start local bot
        export VIRTUAL_ENV="$(pwd)/venv"
        export PATH="$VIRTUAL_ENV/bin:$PATH"
        python final_bot.py
        ;;
        
    "vps")
        echo "☁️  Instructions for VPS bot..."
        echo ""
        echo "Run these commands on your VPS:"
        echo "--------------------------------"
        echo "# Stop any local instances first"
        echo "sudo pkill -f 'python.*bot.py'"
        echo ""
        echo "# Start VPS service"
        echo "sudo systemctl start telegram-bot"
        echo "sudo systemctl status telegram-bot"
        echo ""
        echo "# View logs"
        echo "sudo journalctl -u telegram-bot -f"
        ;;
        
    "stop")
        echo "🛑 Stopping ALL bot instances..."
        
        # Stop local instances
        echo "Stopping local instances..."
        pkill -f "python.*bot.py" 2>/dev/null || true
        pkill -f "python.*final_bot.py" 2>/dev/null || true
        
        echo ""
        echo "To stop VPS bot, run on your server:"
        echo "sudo systemctl stop telegram-bot"
        ;;
        
    "status")
        echo "📊 Bot Status Check"
        echo "==================="
        
        # Check local processes
        LOCAL_PROCS=$(ps aux | grep -E "python.*(final_)?bot\.py" | grep -v grep | wc -l)
        echo "🏠 Local instances: $LOCAL_PROCS"
        
        if [ $LOCAL_PROCS -gt 0 ]; then
            echo "   Active local processes:"
            ps aux | grep -E "python.*(final_)?bot\.py" | grep -v grep
        fi
        
        echo ""
        echo "☁️  To check VPS status, run on your server:"
        echo "   sudo systemctl status telegram-bot"
        echo "   ps aux | grep python | grep bot"
        ;;
        
    *)
        echo "Usage: $0 [local|vps|stop|status]"
        echo ""
        echo "Commands:"
        echo "  local  - Start bot locally (for development)"
        echo "  vps    - Show instructions for VPS bot"
        echo "  stop   - Stop all local bot instances"
        echo "  status - Check bot status"
        echo ""
        echo "⚠️  IMPORTANT: Only run ONE bot instance at a time!"
        echo "   Either local OR VPS, never both simultaneously."
        ;;
esac 