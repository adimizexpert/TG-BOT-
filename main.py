#!/usr/bin/env python3
"""
Secure Telegram Bot for Company Communication
Supports Admin, Employee, and Client roles with JSON-based storage
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Union
from dotenv import load_dotenv

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    Message,
    User,
    Chat,
    Bot
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# File paths
CONFIG_FILE = 'config.json'
CLIENT_DATA_FILE = 'client_data.json'

class TelegramBot:
    def __init__(self):
        self.config = self.load_config()
        self.client_data = self.load_client_data()
        self.pending_replies = {}  # Store pending employee replies
        
    def load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create default config
            default_config = {
                "ADMIN_IDS": [5638736363],
                "GROUP_IDS": []
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            return default_config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {"ADMIN_IDS": [5638736363], "GROUP_IDS": []}
    
    def save_config(self):
        """Save configuration to JSON file"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def load_client_data(self) -> Dict:
        """Load client data from JSON file"""
        try:
            with open(CLIENT_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create empty client data
            with open(CLIENT_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=2)
            return {}
        except Exception as e:
            logger.error(f"Error loading client data: {e}")
            return {}
    
    def save_client_data(self):
        """Save client data to JSON file"""
        try:
            with open(CLIENT_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.client_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving client data: {e}")
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.config.get("ADMIN_IDS", [])
    
    def is_authorized_group(self, chat_id: int) -> bool:
        """Check if chat is an authorized group"""
        return chat_id in self.config.get("GROUP_IDS", [])
    
    def generate_client_id(self) -> str:
        """Generate unique client ID"""
        import random
        while True:
            client_id = f"CLNT_{random.randint(1000, 9999)}"
            if client_id not in self.client_data:
                return client_id
    
    def get_client_alias(self, telegram_id: int) -> Optional[str]:
        """Get client alias by telegram ID"""
        for client_id, data in self.client_data.items():
            if data.get("telegram_id") == telegram_id:
                return data.get("alias")
        return None
    
    def get_client_id_by_telegram_id(self, telegram_id: int) -> Optional[str]:
        """Get client ID by telegram ID"""
        for client_id, data in self.client_data.items():
            if data.get("telegram_id") == telegram_id:
                return client_id
        return None
    
    async def handle_private_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages from clients in private chat"""
        message = update.message
        user = message.from_user
        
        # Skip if message is from admin
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
        
        # Get client alias
        client_alias = self.client_data[client_id].get("alias", "Unknown Client")
        
        # Forward to all authorized groups
        for group_id in self.config.get("GROUP_IDS", []):
            try:
                # Create reply button
                keyboard = [
                    [InlineKeyboardButton("🔁 Reply to Client", callback_data=f"reply_{client_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Forward the message with caption
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
                elif message.video:
                    await context.bot.send_video(
                        chat_id=group_id,
                        video=message.video.file_id,
                        caption=caption,
                        reply_markup=reply_markup
                    )
                elif message.audio:
                    await context.bot.send_audio(
                        chat_id=group_id,
                        audio=message.audio.file_id,
                        caption=caption,
                        reply_markup=reply_markup
                    )
                elif message.document:
                    await context.bot.send_document(
                        chat_id=group_id,
                        document=message.document.file_id,
                        caption=caption,
                        reply_markup=reply_markup
                    )
                elif message.voice:
                    await context.bot.send_voice(
                        chat_id=group_id,
                        voice=message.voice.file_id,
                        caption=caption,
                        reply_markup=reply_markup
                    )
                
            except Exception as e:
                logger.error(f"Error forwarding message to group {group_id}: {e}")
        
        # Send confirmation to client
        await message.reply_text("✅ Message received!")
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("reply_"):
            client_id = query.data.split("_", 1)[1]
            user_id = query.from_user.id
            
            # Store pending reply
            self.pending_replies[user_id] = client_id
            
            # Send message to employee
            client_alias = self.client_data[client_id].get("alias", "Unknown Client")
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📝 Send your reply for {client_alias}:"
            )
    
    async def handle_employee_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle employee replies to clients"""
        message = update.message
        user_id = message.from_user.id
        
        # Check if user has pending reply
        if user_id not in self.pending_replies:
            return
        
        client_id = self.pending_replies[user_id]
        client_data = self.client_data.get(client_id)
        
        if not client_data:
            await message.reply_text("❌ Client not found!")
            del self.pending_replies[user_id]
            return
        
        client_telegram_id = client_data["telegram_id"]
        client_alias = client_data.get("alias", "Unknown Client")
        
        try:
            # Forward reply to client
            if message.text:
                await context.bot.send_message(
                    chat_id=client_telegram_id,
                    text=f"💬 Team: {message.text}"
                )
            elif message.photo:
                await context.bot.send_photo(
                    chat_id=client_telegram_id,
                    photo=message.photo[-1].file_id,
                    caption=f"💬 Team: {message.caption or ''}"
                )
            elif message.video:
                await context.bot.send_video(
                    chat_id=client_telegram_id,
                    video=message.video.file_id,
                    caption=f"💬 Team: {message.caption or ''}"
                )
            elif message.audio:
                await context.bot.send_audio(
                    chat_id=client_telegram_id,
                    audio=message.audio.file_id,
                    caption=f"💬 Team: {message.caption or ''}"
                )
            elif message.document:
                await context.bot.send_document(
                    chat_id=client_telegram_id,
                    document=message.document.file_id,
                    caption=f"💬 Team: {message.caption or ''}"
                )
            elif message.voice:
                await context.bot.send_voice(
                    chat_id=client_telegram_id,
                    voice=message.voice.file_id,
                    caption=f"💬 Team: {message.caption or ''}"
                )
            
            # Confirm to employee
            await message.reply_text("✅ Sent to client.")
            
            # Clear pending reply
            del self.pending_replies[user_id]
            
        except Exception as e:
            logger.error(f"Error sending reply to client: {e}")
            await message.reply_text("❌ Error sending message to client!")
            del self.pending_replies[user_id]
    
    async def assign_group_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to assign current group as authorized"""
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
    
    async def set_alias_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to set client alias"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin access required!")
            return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("❌ Usage: /setalias CLNT_xxxx Alias Name")
            return
        
        client_id = context.args[0]
        alias = " ".join(context.args[1:])
        
        if client_id not in self.client_data:
            await update.message.reply_text("❌ Client ID not found!")
            return
        
        self.client_data[client_id]["alias"] = alias
        self.save_client_data()
        
        await update.message.reply_text(f"✅ Alias set: {client_id} → {alias}")
    
    async def get_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to get client information"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin access required!")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Usage: /getinfo CLNT_xxxx")
            return
        
        client_id = context.args[0]
        
        if client_id not in self.client_data:
            await update.message.reply_text("❌ Client ID not found!")
            return
        
        client_data = self.client_data[client_id]
        info_text = f"📋 Client Information:\n"
        info_text += f"ID: {client_id}\n"
        info_text += f"Telegram ID: {client_data['telegram_id']}\n"
        info_text += f"Alias: {client_data.get('alias', 'Not set')}"
        
        await update.message.reply_text(info_text)
    
    async def list_clients_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to list all clients"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin access required!")
            return
        
        if not self.client_data:
            await update.message.reply_text("📋 No clients registered yet.")
            return
        
        clients_text = "📋 Registered Clients:\n\n"
        for client_id, data in self.client_data.items():
            alias = data.get("alias", "Not set")
            clients_text += f"• {client_id}: {alias}\n"
        
        await update.message.reply_text(clients_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help information"""
        user_id = update.effective_user.id
        
        if self.is_admin(user_id):
            help_text = """
🔧 Admin Commands:
/assigngroup - Add current group as authorized
/setalias CLNT_xxxx Name - Set client alias
/getinfo CLNT_xxxx - Get client information
/listclients - List all registered clients
/help - Show this help

📋 Client Features:
• Send any media type to bot
• Messages forwarded to authorized groups
• Receive team replies

👥 Employee Features:
• View forwarded messages in groups
• Reply to clients via buttons
            """
        else:
            help_text = """
💬 Welcome! Send me any message and I'll forward it to the team.

📱 Supported media types:
• Text messages
• Photos
• Videos
• Audio files
• Documents
• Voice messages

✅ You'll receive a confirmation when your message is sent.
            """
        
        await update.message.reply_text(help_text)

async def main():
    """Main function to run the bot"""
    # Initialize bot
    bot = TelegramBot()
    
    # Get bot token from environment variable
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token or bot_token == 'your_bot_token_here':
        print("❌ Error: BOT_TOKEN not set in .env file!")
        print("Please edit .env file and set your bot token:")
        print("BOT_TOKEN=your_actual_bot_token_here")
        return
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("assigngroup", bot.assign_group_command))
    application.add_handler(CommandHandler("setalias", bot.set_alias_command))
    application.add_handler(CommandHandler("getinfo", bot.get_info_command))
    application.add_handler(CommandHandler("listclients", bot.list_clients_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("start", bot.help_command))
    
    # Message handlers
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & ~filters.COMMAND,
        bot.handle_private_message
    ))
    
    # Handle employee replies (private messages from non-clients)
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
        bot.handle_employee_reply
    ))
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.PHOTO & ~filters.COMMAND,
        bot.handle_employee_reply
    ))
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.VIDEO & ~filters.COMMAND,
        bot.handle_employee_reply
    ))
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.AUDIO & ~filters.COMMAND,
        bot.handle_employee_reply
    ))
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.Document.ALL & ~filters.COMMAND,
        bot.handle_employee_reply
    ))
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.VOICE & ~filters.COMMAND,
        bot.handle_employee_reply
    ))
    
    # Callback query handler
    application.add_handler(CallbackQueryHandler(bot.handle_callback_query))
    
    # Start the bot
    print("🤖 Bot starting...")
    print("✅ Using bot token from .env file")
    print("🔄 Bot is now running and listening for messages...")
    print("💡 Use Ctrl+C to stop the bot")
    
    try:
        await application.run_polling(drop_pending_updates=True, close_loop=False)
    except Exception as e:
        print(f"❌ Bot error: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}") 