import os
import json
import logging
from typing import Dict, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ClientPrivacyManager:
    def __init__(self):
        """Initialize the bot with data storage"""
        self.config_file = "config.json"
        self.client_data_file = "client_data.json"
        
        # Load existing data or create new
        self.config = self.load_config()
        self.client_data = self.load_client_data()
        
        # Initialize default values if not present
        if "ADMIN_IDS" not in self.config:
            self.config["ADMIN_IDS"] = []
        if "PENDING_CLIENTS" not in self.config:
            self.config["PENDING_CLIENTS"] = {}
        if "APPROVED_CLIENTS" not in self.config:
            self.config["APPROVED_CLIENTS"] = {}
        if "GROUPS" not in self.config:
            self.config["GROUPS"] = {}
        if "CLIENT_GROUP_ASSIGNMENTS" not in self.config:
            self.config["CLIENT_GROUP_ASSIGNMENTS"] = {}
        if "MESSAGE_LINK_MAP" not in self.config:
            self.config["MESSAGE_LINK_MAP"] = {}
        
        self.save_config()
    
    def load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_config(self):
        """Save configuration to JSON file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def load_client_data(self) -> Dict:
        """Load client data from JSON file"""
        try:
            with open(self.client_data_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_client_data(self):
        """Save client data to JSON file"""
        with open(self.client_data_file, 'w') as f:
            json.dump(self.client_data, f, indent=2)
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.config.get("ADMIN_IDS", [])
    
    def generate_client_id(self) -> str:
        """Generate unique client ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def get_client_id_by_telegram_id(self, telegram_id: int) -> Optional[str]:
        """Get client ID by Telegram ID"""
        for client_id, data in self.client_data.items():
            if data.get("telegram_id") == telegram_id:
                return client_id
        return None
    
    def is_client_approved(self, client_id: str) -> bool:
        """Check if client is approved"""
        return client_id in self.config.get("APPROVED_CLIENTS", {})
    
    def is_client_pending(self, telegram_id: int) -> bool:
        """Check if client is pending approval"""
        return str(telegram_id) in self.config.get("PENDING_CLIENTS", {})
    
    def add_pending_client(self, telegram_id: int, username: str, first_name: str):
        """Add client to pending list"""
        self.config["PENDING_CLIENTS"][str(telegram_id)] = {
            "username": username,
            "first_name": first_name
        }
        self.save_config()
    
    def approve_client(self, client_id: str):
        """Approve a client"""
        if client_id in self.client_data:
            telegram_id = self.client_data[client_id]["telegram_id"]
            # Remove from pending
            if str(telegram_id) in self.config["PENDING_CLIENTS"]:
                del self.config["PENDING_CLIENTS"][str(telegram_id)]
            # Add to approved
            self.config["APPROVED_CLIENTS"][client_id] = self.client_data[client_id]
            self.save_config()
    
    def reject_client(self, telegram_id: int):
        """Reject a client"""
        if str(telegram_id) in self.config["PENDING_CLIENTS"]:
            del self.config["PENDING_CLIENTS"][str(telegram_id)]
            self.save_config()
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        if self.is_admin(user.id):
            # Admin start - show admin panel
            await self.show_admin_panel(update, context)
        else:
            # Client start - check if approved
            client_id = self.get_client_id_by_telegram_id(user.id)
            
            if not client_id:
                # New client - add to pending
                client_id = self.generate_client_id()
                self.client_data[client_id] = {
                    "telegram_id": user.id,
                    "username": user.username or "",
                    "first_name": user.first_name or "",
                    "status": "pending"
                }
                self.save_client_data()
                self.add_pending_client(user.id, user.username or "", user.first_name or "")
                
                # Notify admins
                await self.notify_admins_new_client(user, context)
                
                await update.message.reply_text(
                    "⏳ Your request is pending approval.\n\nYou'll be notified when approved."
                )
            elif self.is_client_approved(client_id):
                # Approved client
                await update.message.reply_text(
                    "✅ You are approved!\n\nSend any message and it will be forwarded to your assigned group."
                )
            else:
                # Pending client
                await update.message.reply_text(
                    "⏳ Your request is still pending approval.\n\nYou'll be notified when approved."
                )
    
    async def notify_admins_new_client(self, user, context: ContextTypes.DEFAULT_TYPE):
        """Notify all admins about new pending client"""
        for admin_id in self.config.get("ADMIN_IDS", []):
            try:
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Accept", callback_data=f"approve_{user.id}"),
                        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"🆕 New client request:\n\n"
                         f"ID: {user.id}\n"
                         f"Username: @{user.username or 'None'}\n"
                         f"Name: {user.first_name or 'None'}",
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Error notifying admin {admin_id}: {e}")
    
    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin panel"""
        keyboard = [
            [InlineKeyboardButton("👥 Manage Clients", callback_data="admin_clients")],
            [InlineKeyboardButton("📋 Manage Groups", callback_data="admin_groups")],
            [InlineKeyboardButton("🔗 Assign Clients", callback_data="admin_assign")],
            [InlineKeyboardButton("➕ Add Admin", callback_data="admin_add_admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔧 Admin Panel\n\nSelect an option:",
            reply_markup=reply_markup
        )
    
    async def handle_private_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle private messages from clients"""
        user = update.effective_user
        
        if self.is_admin(user.id):
            return
        
        # Check if client is approved
        client_id = self.get_client_id_by_telegram_id(user.id)
        if not client_id or not self.is_client_approved(client_id):
            await update.message.reply_text("⏳ Your account is pending approval.")
            return
        
        # Get assigned group
        assigned_group = self.config.get("CLIENT_GROUP_ASSIGNMENTS", {}).get(client_id)
        if not assigned_group:
            await update.message.reply_text("❌ You are not assigned to any group yet.")
            return
        
        # Forward message to assigned group
        try:
            caption = f"📩 From: @{user.username or user.first_name}"
            
            if update.message.text:
                forwarded_msg = await context.bot.send_message(
                    chat_id=int(assigned_group),
                    text=f"{caption}\n\n{update.message.text}"
                )
            elif update.message.photo:
                forwarded_msg = await context.bot.send_photo(
                    chat_id=int(assigned_group),
                    photo=update.message.photo[-1].file_id,
                    caption=caption
                )
            elif update.message.video:
                forwarded_msg = await context.bot.send_video(
                    chat_id=int(assigned_group),
                    video=update.message.video.file_id,
                    caption=caption
                )
            elif update.message.voice:
                forwarded_msg = await context.bot.send_voice(
                    chat_id=int(assigned_group),
                    voice=update.message.voice.file_id,
                    caption=caption
                )
            else:
                await update.message.reply_text("❌ Unsupported message type.")
                return
            
            # Track message for replies
            self.config["MESSAGE_LINK_MAP"][f"{assigned_group}_{forwarded_msg.message_id}"] = client_id
            self.save_config()
            
            await update.message.reply_text("✅ Message sent!")
            
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")
            await update.message.reply_text("❌ Error sending message.")
    
    async def handle_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle group messages (replies)"""
        message = update.message
        chat_id = str(message.chat.id)
        
        # Check if this is a reply to a forwarded message
        if message.reply_to_message:
            message_key = f"{chat_id}_{message.reply_to_message.message_id}"
            original_client_id = self.config.get("MESSAGE_LINK_MAP", {}).get(message_key)
            
            if original_client_id and original_client_id in self.client_data:
                client_telegram_id = self.client_data[original_client_id]["telegram_id"]
                
                try:
                    # Forward reply to original client
                    if message.text:
                        await context.bot.send_message(
                            chat_id=client_telegram_id,
                            text=f"💬 Reply from group:\n\n{message.text}"
                        )
                    elif message.photo:
                        await context.bot.send_photo(
                            chat_id=client_telegram_id,
                            photo=message.photo[-1].file_id,
                            caption="💬 Reply from group:"
                        )
                    elif message.video:
                        await context.bot.send_video(
                            chat_id=client_telegram_id,
                            video=message.video.file_id,
                            caption="💬 Reply from group:"
                        )
                    elif message.voice:
                        await context.bot.send_voice(
                            chat_id=client_telegram_id,
                            voice=message.voice.file_id,
                            caption="💬 Reply from group:"
                        )
                except Exception as e:
                    logger.error(f"Error forwarding reply: {e}")
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        if not self.is_admin(query.from_user.id):
            try:
                await query.edit_message_text("❌ Admin access required!")
            except:
                await context.bot.send_message(chat_id=query.from_user.id, text="❌ Admin access required!")
            return
        
        data = query.data
        
        try:
            if data == "admin_panel":
                await self.show_admin_panel_callback(query, context)
            elif data == "admin_clients":
                await self.show_clients_panel(query, context)
            elif data == "admin_groups":
                await self.show_groups_panel(query, context)
            elif data == "admin_assign":
                await self.show_assign_panel(query, context)
            elif data == "admin_add_admin":
                await self.show_add_admin_panel(query, context)
            elif data.startswith("approve_"):
                await self.approve_client_callback(query, context)
            elif data.startswith("reject_"):
                await self.reject_client_callback(query, context)
            elif data.startswith("delete_client_"):
                await self.delete_client_callback(query, context)
            elif data.startswith("delete_group_"):
                await self.delete_group_callback(query, context)
            elif data.startswith("assign_"):
                await self.assign_client_callback(query, context)
            elif data.startswith("assign_to_"):
                await self.assign_to_callback(query, context)
            elif data == "add_group":
                await self.add_group_callback(query, context)
            else:
                await query.edit_message_text("❌ Unknown action!")
        except Exception as e:
            logger.error(f"Error in callback query: {e}")
            try:
                await query.edit_message_text("❌ An error occurred!")
            except:
                await context.bot.send_message(chat_id=query.from_user.id, text="❌ An error occurred!")
    
    async def show_admin_panel_callback(self, query, context):
        """Show admin panel via callback"""
        keyboard = [
            [InlineKeyboardButton("👥 Manage Clients", callback_data="admin_clients")],
            [InlineKeyboardButton("📋 Manage Groups", callback_data="admin_groups")],
            [InlineKeyboardButton("🔗 Assign Clients", callback_data="admin_assign")],
            [InlineKeyboardButton("➕ Add Admin", callback_data="admin_add_admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔧 Admin Panel\n\nSelect an option:",
            reply_markup=reply_markup
        )
    
    async def show_clients_panel(self, query, context):
        """Show clients management panel"""
        approved_clients = self.config.get("APPROVED_CLIENTS", {})
        pending_clients = self.config.get("PENDING_CLIENTS", {})
        
        keyboard = []
        
        # Add approved clients
        for client_id, data in approved_clients.items():
            username = data.get("username", "None")
            keyboard.append([InlineKeyboardButton(
                f"✅ {username}", 
                callback_data=f"delete_client_{client_id}"
            )])
        
        # Add pending clients
        for telegram_id, data in pending_clients.items():
            username = data.get("username", "None")
            keyboard.append([InlineKeyboardButton(
                f"⏳ {username}", 
                callback_data=f"approve_{telegram_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"👥 Clients\n\n"
            f"✅ Approved: {len(approved_clients)}\n"
            f"⏳ Pending: {len(pending_clients)}",
            reply_markup=reply_markup
        )
    
    async def show_groups_panel(self, query, context):
        """Show groups management panel"""
        groups = self.config.get("GROUPS", {})
        
        keyboard = []
        for group_id, group_name in groups.items():
            keyboard.append([InlineKeyboardButton(
                f"📋 {group_name}", 
                callback_data=f"delete_group_{group_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📋 Groups\n\n"
            f"Total: {len(groups)}",
            reply_markup=reply_markup
        )
    
    async def show_assign_panel(self, query, context):
        """Show client assignment panel"""
        approved_clients = self.config.get("APPROVED_CLIENTS", {})
        groups = self.config.get("GROUPS", {})
        assignments = self.config.get("CLIENT_GROUP_ASSIGNMENTS", {})
        
        keyboard = []
        
        for client_id, client_data in approved_clients.items():
            username = client_data.get("username", "None")
            assigned_group = assignments.get(client_id)
            group_name = groups.get(assigned_group, "None") if assigned_group else "None"
            
            keyboard.append([InlineKeyboardButton(
                f"👤 {username} → {group_name}", 
                callback_data=f"assign_{client_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🔗 Assignments\n\n"
            f"Clients: {len(approved_clients)}\n"
            f"Groups: {len(groups)}",
            reply_markup=reply_markup
        )
    
    async def approve_client_callback(self, query, context):
        """Approve client via callback"""
        telegram_id = int(query.data.split("_")[1])
        client_id = self.get_client_id_by_telegram_id(telegram_id)
        
        if client_id:
            self.approve_client(client_id)
            await query.edit_message_text("✅ Client approved!")
        else:
            await query.edit_message_text("❌ Client not found!")
    
    async def reject_client_callback(self, query, context):
        """Reject client via callback"""
        telegram_id = int(query.data.split("_")[1])
        self.reject_client(telegram_id)
        await query.edit_message_text("❌ Client rejected!")
    
    async def delete_client_callback(self, query, context):
        """Delete client via callback"""
        client_id = query.data.split("_")[2]
        
        # Remove from approved clients
        if client_id in self.config["APPROVED_CLIENTS"]:
            del self.config["APPROVED_CLIENTS"][client_id]
        
        # Remove from client data
        if client_id in self.client_data:
            del self.client_data[client_id]
        
        # Remove from assignments
        if client_id in self.config["CLIENT_GROUP_ASSIGNMENTS"]:
            del self.config["CLIENT_GROUP_ASSIGNMENTS"][client_id]
        
        self.save_config()
        self.save_client_data()
        
        await query.edit_message_text("🗑️ Client deleted!")
    
    async def delete_group_callback(self, query, context):
        """Delete group via callback"""
        group_id = query.data.split("_")[2]
        
        # Remove from groups
        if group_id in self.config["GROUPS"]:
            del self.config["GROUPS"][group_id]
        
        # Remove from assignments
        for client_id, assigned_group in list(self.config["CLIENT_GROUP_ASSIGNMENTS"].items()):
            if assigned_group == group_id:
                del self.config["CLIENT_GROUP_ASSIGNMENTS"][client_id]
        
        self.save_config()
        
        await query.edit_message_text("🗑️ Group deleted!")
    
    async def assign_client_callback(self, query, context):
        """Assign client to group via callback"""
        client_id = query.data.split("_")[1]
        groups = self.config.get("GROUPS", {})
        
        keyboard = []
        for group_id, group_name in groups.items():
            keyboard.append([InlineKeyboardButton(
                group_name, 
                callback_data=f"assign_to_{client_id}_{group_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_assign")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        client_data = self.config["APPROVED_CLIENTS"].get(client_id, {})
        username = client_data.get("username", "Unknown")
        
        await query.edit_message_text(
            f"🔗 Assign {username} to:",
            reply_markup=reply_markup
        )
    
    async def add_group_callback(self, query, context):
        """Add current group via callback"""
        chat_id = str(query.message.chat.id)
        chat_title = query.message.chat.title or "Unknown Group"
        
        self.config["GROUPS"][chat_id] = chat_title
        self.save_config()
        
        await query.edit_message_text(f"✅ Group '{chat_title}' added!")
    
    async def show_add_admin_panel(self, query, context):
        """Show add admin panel"""
        await query.edit_message_text(
            "➕ Add Admin\n\n"
            "To add an admin, have them send /start to the bot, "
            "then use this command:\n\n"
            "/addadmin <user_id>"
        )
    
    async def assign_to_callback(self, query, context):
        """Handle assign_to callback"""
        parts = query.data.split("_")
        if len(parts) >= 4:
            client_id = parts[2]
            group_id = parts[3]
            
            # Assign client to group
            self.config["CLIENT_GROUP_ASSIGNMENTS"][client_id] = group_id
            self.save_config()
            
            await query.edit_message_text("✅ Client assigned to group!")
        else:
            await query.edit_message_text("❌ Invalid assignment data!")
    
    async def add_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add admin command"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin access required!")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Usage: /addadmin <user_id>")
            return
        
        try:
            new_admin_id = int(context.args[0])
            if new_admin_id not in self.config["ADMIN_IDS"]:
                self.config["ADMIN_IDS"].append(new_admin_id)
                self.save_config()
                await update.message.reply_text(f"✅ Admin {new_admin_id} added!")
            else:
                await update.message.reply_text("❌ Admin already exists!")
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")

def main():
    """Main function"""
    bot = ClientPrivacyManager()
    
    # Get bot token
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        print("❌ Error: BOT_TOKEN not set in .env file!")
        return
    
    print("🤖 Client Privacy Manager starting...")
    print("✅ Using bot token from .env file")
    print("🔄 Bot is now running...")
    print("💡 Use Ctrl+C to stop the bot")
    
    # Create application (ApplicationBuilder is the modern async entrypoint)
    application = ApplicationBuilder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.handle_start))
    application.add_handler(CommandHandler("addadmin", bot.add_admin_command))
    
    # Message handlers
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & ~filters.COMMAND,
        bot.handle_private_message
    ))
    
    application.add_handler(MessageHandler(
        filters.ChatType.GROUPS & ~filters.COMMAND,
        bot.handle_group_message
    ))
    
    # Callback query handler
    application.add_handler(CallbackQueryHandler(bot.handle_callback_query))
    
    # Run the bot
    try:
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        # Fallback method
        application.run_polling()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}") 