import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text("🤖 Bot is working! Hello!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text("💡 This is a test bot. Use /start to begin.")

def main():
    """Main function"""
    # Get bot token
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        print("❌ Error: BOT_TOKEN not set in .env file!")
        return
    
    print("🤖 Test Bot starting...")
    print("✅ Using bot token from .env file")
    print("🔄 Bot is now running...")
    print("💡 Use Ctrl+C to stop the bot")
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Run the bot
    print("🚀 Starting bot...")
    application.run_polling()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}") 