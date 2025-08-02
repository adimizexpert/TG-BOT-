#!/usr/bin/env python3
"""
Simplified Telegram Bot for Company Communication
"""

import json
import logging
import os
from typing import Dict, Optional

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# File paths
CONFIG_FILE = 'config.json'
CLIENT_DATA_FILE = 'client_data.json'

class SimpleBot:
    def __init__(self):
        self.config = self.load_config()
        self.client_data = self.load_client_data()
        self.pending_replies = {}
        
    def load_config(self) -> Dict:
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            default_config = {"ADMIN_IDS": [5638736363], "GROUP_IDS": []}
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def save_config(self):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)
    
    def load_client_data(self) -> Dict:
        try:
            with open(CLIENT_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            with open(CLIENT_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=2)
            return {}
    
    def save_client_data(self):
        with open(CLIENT_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.client_data, f, indent=2)
    
    def is_admin(self, user_id: int) -> bool:
        return user_id in self.config.get("ADMIN_IDS", [])
    
    def generate_client_id(self) -> str:
        import random
        while True:
            client_id = f"CLNT_{random.randint(1000, 9999)}"
            if client_id not in self.client_data:
                return client_id
    
    def get_client_id_by_telegram_id(self, telegram_id: int) -> Optional[str]:
        for client_id, data in self.client_data.items():
            if data.get("telegram_id") == telegram_id:
                return client_id
        return None
    
    async def handle_private_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages from clients"""
        message = update.message
        user = message.from_user
        
        if self.is_admin(user.id):
            return
        
        # Get or create client ID
        client_id = self.get_client_id_by_telegram_id(user.id)
        if not client_id:
            client_id = self.generate_client_id()
            self.client_data[client_id] = {
                "telegram_id": user.id,
                "alias": None
            }
            self.save_client_data()
        
        client_alias = self.client_data[client_id].get("alias", "Unknown Client")
        
        # Forward to groups
        for group_id in self.config.get("GROUP_IDS", []):
            try:
                keyboard = [[InlineKeyboardButton("🔁 Reply to Client", callback_data=f"reply_{client_id}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                caption = f"📩 Message from: {client_alias}"
                
                if message.text:
                    await context.bot.send_message(
                        chat_id=group_id,
                        text=f"{caption}\n\n{message.text}",
                        reply_markup=reply_markup
                    )
                elif message.photo:
                    await context.bot.send_photo(
                        chat_id=group_id,
                        photo=message.photo[-1].file_id,
                        caption=caption,
                        reply_markup=reply_markup
                    )
            except Exception as e:
                logger.error(f"Error forwarding to group {group_id}: {e}")
        
        await message.reply_text("✅ Message received!")
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("reply_"):
            client_id = query.data.split("_", 1)[1]
            user_id = query.from_user.id
            
            self.pending_replies[user_id] = client_id
            client_alias = self.client_data[client_id].get("alias", "Unknown Client")
            
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📝 Send your reply for {client_alias}:"
            )
    
    async def handle_employee_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle employee replies"""
        message = update.message
        user_id = message.from_user.id
        
        if user_id not in self.pending_replies:
            return
        
        client_id = self.pending_replies[user_id]
        client_data = self.client_data.get(client_id)
        
        if not client_data:
            await message.reply_text("❌ Client not found!")
            del self.pending_replies[user_id]
            return
        
        client_telegram_id = client_data["telegram_id"]
        
        try:
            if message.text:
                await context.bot.send_message(
                    chat_id=client_telegram_id,
                    text=f"💬 Team: {message.text}"
                )
            
            await message.reply_text("✅ Sent to client.")
            del self.pending_replies[user_id]
            
        except Exception as e:
            logger.error(f"Error sending reply: {e}")
            await message.reply_text("❌ Error sending message!")
            del self.pending_replies[user_id]
    
    async def assign_group_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to assign group"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin access required!")
            return
        
        chat_id = update.effective_chat.id
        
        if chat_id in self.config.get("GROUP_IDS", []):
            await update.message.reply_text("✅ Group already authorized!")
            return
        
        if "GROUP_IDS" not in self.config:
            self.config["GROUP_IDS"] = []
        
        self.config["GROUP_IDS"].append(chat_id)
        self.save_config()
        
        await update.message.reply_text("✅ Group added as authorized broadcast group!")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help"""
        user_id = update.effective_user.id
        
        if self.is_admin(user_id):
            help_text = """
🔧 Admin Commands:
/assigngroup - Add current group as authorized
/help - Show this help

📋 Client Features:
• Send any media type to bot
• Messages forwarded to authorized groups
• Receive team replies
            """
        else:
            help_text = """
💬 Welcome! Send me any message and I'll forward it to the team.

✅ You'll receive a confirmation when your message is sent.
            """
        
        await update.message.reply_text(help_text)

async def main():
    """Main function"""
    bot = SimpleBot()
    
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token or bot_token == 'your_bot_token_here':
        print("❌ Error: BOT_TOKEN not set in .env file!")
        return
    
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("assigngroup", bot.assign_group_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("start", bot.help_command))
    
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & ~filters.COMMAND,
        bot.handle_private_message
    ))
    
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
        bot.handle_employee_reply
    ))
    
    application.add_handler(CallbackQueryHandler(bot.handle_callback_query))
    
    print("🤖 Bot starting...")
    print("✅ Using bot token from .env file")
    print("🔄 Bot is now running and listening for messages...")
    print("💡 Use Ctrl+C to stop the bot")
    
    await application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}") 