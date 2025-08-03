#!/usr/bin/env python3
"""
Working Telegram Bot for Company Communication
"""

import json
import logging
import os
from datetime import datetime
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

class WorkingBot:
    def __init__(self):
        self.config = self.load_config()
        self.client_data = self.load_client_data()
        self.pending_replies = {}
        # Initialize client-group assignments if not exists
        if "CLIENT_GROUP_ASSIGNMENTS" not in self.config:
            self.config["CLIENT_GROUP_ASSIGNMENTS"] = {}
            self.save_config()
        
        # Initialize pending clients if not exists
        if "PENDING_CLIENTS" not in self.config:
            self.config["PENDING_CLIENTS"] = {}
            self.save_config()
        
        # Initialize group names if not exists
        if "GROUP_NAMES" not in self.config:
            self.config["GROUP_NAMES"] = {}
            self.save_config()
        
        # Initialize admin-only groups if not exists
        if "ADMIN_ONLY_GROUPS" not in self.config:
            self.config["ADMIN_ONLY_GROUPS"] = []
            self.save_config()
    
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
    
    def is_client_approved(self, client_id: str) -> bool:
        """Check if client is approved"""
        return client_id in self.client_data and self.client_data[client_id].get("status", "pending") == "approved"
    
    def is_client_pending(self, telegram_id: int) -> bool:
        """Check if client is pending approval"""
        return str(telegram_id) in self.config.get("PENDING_CLIENTS", {})
    
    async def get_group_name(self, group_id: str, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Get group name from Telegram or stored names"""
        # First try to get from Telegram
        try:
            group_chat = await context.bot.get_chat(int(group_id))
            group_name = group_chat.title or f"Group {group_id}"
            # Store the name for future use
            self.config["GROUP_NAMES"][group_id] = group_name
            self.save_config()
            return group_name
        except Exception as e:
            # Fall back to stored name or default
            stored_name = self.config.get("GROUP_NAMES", {}).get(group_id)
            if stored_name:
                return stored_name
            return f"Group {group_id}"
    
    def add_pending_client(self, telegram_id: int, username: str, first_name: str):
        """Add client to pending list"""
        self.config["PENDING_CLIENTS"][str(telegram_id)] = {
            "username": username,
            "first_name": first_name,
            "timestamp": datetime.now().isoformat()
        }
        self.save_config()
    
    def approve_client(self, client_id: str):
        """Approve a client"""
        if client_id in self.client_data:
            self.client_data[client_id]["status"] = "approved"
            self.save_client_data()
            
            # Remove from pending if exists
            telegram_id = self.client_data[client_id].get("telegram_id")
            if telegram_id and str(telegram_id) in self.config.get("PENDING_CLIENTS", {}):
                del self.config["PENDING_CLIENTS"][str(telegram_id)]
                self.save_config()
    
    def reject_client(self, telegram_id: int):
        """Reject a client"""
        if str(telegram_id) in self.config.get("PENDING_CLIENTS", {}):
            del self.config["PENDING_CLIENTS"][str(telegram_id)]
            self.save_config()
    
    async def handle_private_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages from clients"""
        message = update.message
        user = message.from_user
        
        # Check if admin is waiting for custom group name input
        if self.is_admin(user.id):
            temp_data = self.config.get("TEMP_GROUP_ADD", {})
            if temp_data.get("waiting_for_name") and temp_data.get("pending_chat_id"):
                chat_id = temp_data["pending_chat_id"]
                custom_name = message.text.strip()
                
                if len(custom_name) > 50:
                    await message.reply_text("❌ Group name too long! Please use a shorter name (max 50 characters).")
                    return
                
                # Add to GROUP_IDS
                if "GROUP_IDS" not in self.config:
                    self.config["GROUP_IDS"] = []
                
                if chat_id not in self.config["GROUP_IDS"]:
                    self.config["GROUP_IDS"].append(chat_id)
                
                # Store the custom name
                if "GROUP_NAMES" not in self.config:
                    self.config["GROUP_NAMES"] = {}
                self.config["GROUP_NAMES"][str(chat_id)] = custom_name
                
                # Clean up temp data
                del self.config["TEMP_GROUP_ADD"]
                self.save_config()
                
                # Add back button
                keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await message.reply_text(
                    f"✅ Group added successfully!\n\n"
                    f"Group: {custom_name}\n"
                    f"ID: {chat_id}",
                    reply_markup=reply_markup
                )
                return
        
        if self.is_admin(user.id):
            return
        
        # Check if client is pending approval
        if self.is_client_pending(user.id):
            await message.reply_text("⏳ Your account is pending approval. Please wait for admin approval.")
            return
        
        # Get or create client ID
        client_id = self.get_client_id_by_telegram_id(user.id)
        if not client_id:
            # New client - add to pending
            self.add_pending_client(user.id, user.username or "", user.first_name or "")
            await message.reply_text("⏳ Your account is pending approval. Please wait for admin approval.")
            
            # Notify all admins about new pending client
            for admin_id in self.config.get("ADMIN_IDS", []):
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"🆕 New client pending approval:\n"
                             f"ID: {user.id}\n"
                             f"Username: @{user.username or 'None'}\n"
                             f"Name: {user.first_name or 'None'}\n"
                             f"Use /approve {user.id} or /reject {user.id}"
                    )
                except Exception as e:
                    print(f"❌ Error notifying admin {admin_id}: {e}")
            return
        
        # Check if client is approved
        if not self.is_client_approved(client_id):
            await message.reply_text("⏳ Your account is pending approval. Please wait for admin approval.")
            return
        
        # Get actual username from Telegram
        telegram_id = self.client_data[client_id].get("telegram_id", "")
        try:
            user = await context.bot.get_chat(telegram_id)
            username = user.username or user.first_name or f"User{telegram_id}"
        except:
            username = f"User{telegram_id}"
        
        # For group chats, show only first 3 characters of username
        # For admin private chat, show full username
        username_preview = username[:3] if len(username) >= 3 else username
        client_display = f"@{username_preview}"
        
        # Get assigned groups for this client
        assigned_groups = self.config.get("CLIENT_GROUP_ASSIGNMENTS", {}).get(client_id, [])
        
        # Only forward to admin IDs (private chats) - no group forwarding
        admin_ids = self.config.get("ADMIN_IDS", [])
        
        print(f"🔍 Debug: Client {client_id} assigned to groups: {assigned_groups}")
        print(f"🔍 Debug: Forwarding to {len(admin_ids)} admin IDs: {admin_ids}")
        
        # Forward to admin IDs only (private chats)
        for admin_id in admin_ids:
            try:
                print(f"🔍 Debug: Attempting to forward to admin {admin_id}")
                caption = f"📩 Message from: {client_display}"
                
                if message.text:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"{caption}\n\n{message.text}"
                    )
                    print(f"✅ Debug: Successfully forwarded text message to admin {admin_id}")
                elif message.photo:
                    await context.bot.send_photo(
                        chat_id=admin_id,
                        photo=message.photo[-1].file_id,
                        caption=caption
                    )
                    print(f"✅ Debug: Successfully forwarded photo to admin {admin_id}")
                elif message.video:
                    await context.bot.send_video(
                        chat_id=admin_id,
                        video=message.video.file_id,
                        caption=caption
                    )
                    print(f"✅ Debug: Successfully forwarded video to admin {admin_id}")
                elif message.audio:
                    await context.bot.send_audio(
                        chat_id=admin_id,
                        audio=message.audio.file_id,
                        caption=caption
                    )
                    print(f"✅ Debug: Successfully forwarded audio to admin {admin_id}")
                elif message.document:
                    await context.bot.send_document(
                        chat_id=admin_id,
                        document=message.document.file_id,
                        caption=caption
                    )
                    print(f"✅ Debug: Successfully forwarded document to admin {admin_id}")
                elif message.voice:
                    await context.bot.send_voice(
                        chat_id=admin_id,
                        voice=message.voice.file_id,
                        caption=caption
                    )
                    print(f"✅ Debug: Successfully forwarded voice to admin {admin_id}")
            except Exception as e:
                print(f"❌ Debug: Error forwarding to admin {admin_id}: {e}")
                logger.error(f"Error forwarding to admin {admin_id}: {e}")
        
        await message.reply_text("✅ Message received!")
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        # Check if this is an admin callback and restrict to private chat
        if query.data.startswith(("admin_", "select_", "toggle_", "delete_group_")) and not query.data.startswith("add_group_"):
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            # Only allow admin callbacks in private chat (except for group addition)
            if query.message.chat.type != "private":
                await query.edit_message_text("❌ Admin features can only be used in private chat with the bot!")
                return
        
        # Reply functionality removed - all group messages are automatically forwarded to clients
        
        if query.data == "admin_list_clients":
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            if not self.client_data:
                await query.edit_message_text("📋 No clients registered yet.")
                return
            
            clients_text = "📋 Registered Clients:\n\n"
            for client_id, data in self.client_data.items():
                telegram_id = data.get("telegram_id", "Unknown")
                # Try to get actual username from Telegram
                try:
                    user = await context.bot.get_chat(telegram_id)
                    username = user.username or user.first_name or f"User{telegram_id}"
                except:
                    username = f"User{telegram_id}"
                clients_text += f"• {client_id}: @{username}\n"
            
            # Add back button
            keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(clients_text, reply_markup=reply_markup)
        
        elif query.data == "admin_add_group":
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            chat_id = query.message.chat.id
            
            if chat_id in self.config.get("GROUP_IDS", []):
                await query.edit_message_text("✅ Group already authorized!")
                return
            
            if "GROUP_IDS" not in self.config:
                self.config["GROUP_IDS"] = []
            
            self.config["GROUP_IDS"].append(chat_id)
            self.save_config()
            
            # Add back button
            keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text("✅ Group added as authorized broadcast group!", reply_markup=reply_markup)
        
        elif query.data == "admin_panel":
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            keyboard = [
                [InlineKeyboardButton("📋 List Clients", callback_data="admin_list_clients")],
                [InlineKeyboardButton("➕ Add Group", callback_data="admin_add_group")],
                [InlineKeyboardButton("🏢 Assign Group from Chat", callback_data="admin_assign_group_chat")],
                [InlineKeyboardButton("📋 View Clients", callback_data="admin_set_alias")],
                [InlineKeyboardButton("ℹ️ Get Client Info", callback_data="admin_get_info")],
                [InlineKeyboardButton("🔗 Assign Client to Groups", callback_data="admin_assign_client_groups")],
                [InlineKeyboardButton("🗑️ Delete Clients", callback_data="admin_delete_clients")],
                [InlineKeyboardButton("⏳ Pending Clients", callback_data="admin_pending_clients")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text("🔧 Admin Panel\n\nSelect an option:", reply_markup=reply_markup)
        
        elif query.data == "admin_set_alias":
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            if not self.client_data:
                await query.edit_message_text("📋 No clients registered yet.")
                return
            
            # Create client selection buttons with usernames
            keyboard = []
            for client_id, data in self.client_data.items():
                telegram_id = data.get("telegram_id", "")
                # Try to get actual username from Telegram
                try:
                    user = await context.bot.get_chat(telegram_id)
                    username = user.username or user.first_name or f"User{telegram_id}"
                except:
                    username = f"User{telegram_id}"
                keyboard.append([InlineKeyboardButton(f"👤 @{username} ({client_id})", callback_data=f"select_alias_{client_id}")])
            
            keyboard.append([InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text("📋 Client List:\n\nShowing clients with their Telegram ID preview:", reply_markup=reply_markup)
        
        elif query.data.startswith("select_alias_"):
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            client_id = query.data.split("_", 2)[2]
            client_data = self.client_data.get(client_id)
            
            if not client_data:
                await query.edit_message_text("❌ Client not found!")
                return
            
            telegram_id = client_data.get("telegram_id", "Unknown")
            # Try to get actual username from Telegram
            try:
                user = await context.bot.get_chat(telegram_id)
                username = user.username or user.first_name or f"User{telegram_id}"
            except:
                username = f"User{telegram_id}"
            
            info_text = f"📋 Client Information:\n"
            info_text += f"ID: {client_id}\n"
            info_text += f"Telegram ID: {telegram_id}\n"
            info_text += f"Username: @{username}"
            
            # Add back button
            keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(info_text, reply_markup=reply_markup)
        
        elif query.data == "admin_assign_client_groups":
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            if not self.client_data:
                await query.edit_message_text("📋 No clients registered yet.")
                return
            
            if not self.config.get("GROUP_IDS", []):
                await query.edit_message_text("❌ No groups configured yet. Please add groups first.")
                return
            
            # Create client selection buttons
            keyboard = []
            for client_id, data in self.client_data.items():
                telegram_id = data.get("telegram_id", "")
                try:
                    user = await context.bot.get_chat(telegram_id)
                    username = user.username or user.first_name or f"User{telegram_id}"
                except:
                    username = f"User{telegram_id}"
                keyboard.append([InlineKeyboardButton(f"👤 @{username} ({client_id})", callback_data=f"select_client_groups_{client_id}")])
            
            keyboard.append([InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text("🔗 Select a client to assign groups:", reply_markup=reply_markup)
        
        elif query.data.startswith("select_client_groups_"):
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            client_id = query.data.split("_", 3)[3]
            client_data = self.client_data.get(client_id)
            
            if not client_data:
                await query.edit_message_text("❌ Client not found!")
                return
            
            # Get current assignments for this client
            current_assignments = self.config.get("CLIENT_GROUP_ASSIGNMENTS", {}).get(client_id, [])
            
            # Only show groups that actually exist in GROUP_IDS
            available_groups = self.config.get("GROUP_IDS", [])
            
            if not available_groups:
                await query.edit_message_text("❌ No groups configured yet. Please add groups first.")
                return
            
            # Create group selection buttons
            keyboard = []
            for group_id in available_groups:
                is_assigned = str(group_id) in current_assignments
                status = "✅" if is_assigned else "❌"
                
                # Get group name using our method
                group_name = await self.get_group_name(str(group_id), context)
                
                keyboard.append([InlineKeyboardButton(f"{status} {group_name}", callback_data=f"toggle_group_{client_id}_{group_id}")])
            
            keyboard.append([InlineKeyboardButton("🔙 Back to Client Selection", callback_data="admin_assign_client_groups")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(f"🔗 Select groups for client {client_id}:\n\n✅ = Assigned\n❌ = Not Assigned\n\nAvailable groups:", reply_markup=reply_markup)
        
        elif query.data.startswith("toggle_group_"):
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            parts = query.data.split("_")
            client_id = parts[2]
            group_id = parts[3]
            
            # Initialize if not exists
            if "CLIENT_GROUP_ASSIGNMENTS" not in self.config:
                self.config["CLIENT_GROUP_ASSIGNMENTS"] = {}
            
            if client_id not in self.config["CLIENT_GROUP_ASSIGNMENTS"]:
                self.config["CLIENT_GROUP_ASSIGNMENTS"][client_id] = []
            
            # Toggle assignment
            if str(group_id) in self.config["CLIENT_GROUP_ASSIGNMENTS"][client_id]:
                self.config["CLIENT_GROUP_ASSIGNMENTS"][client_id].remove(str(group_id))
                action = "removed from"
            else:
                self.config["CLIENT_GROUP_ASSIGNMENTS"][client_id].append(str(group_id))
                action = "assigned to"
            
            self.save_config()
            
            # Refresh the group selection view
            current_assignments = self.config["CLIENT_GROUP_ASSIGNMENTS"][client_id]
            keyboard = []
            for gid in self.config.get("GROUP_IDS", []):
                is_assigned = str(gid) in current_assignments
                status = "✅" if is_assigned else "❌"
                
                # Get group name using our method
                group_name = await self.get_group_name(str(gid), context)
                
                keyboard.append([InlineKeyboardButton(f"{status} {group_name}", callback_data=f"toggle_group_{client_id}_{gid}")])
            
            keyboard.append([InlineKeyboardButton("🔙 Back to Client Selection", callback_data="admin_assign_client_groups")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Get group name for confirmation message
            group_name = await self.get_group_name(str(group_id), context)
            
            await query.edit_message_text(f"✅ Client {client_id} {action} {group_name}!\n\n🔗 Select groups for client {client_id}:\n\n✅ = Assigned\n❌ = Not Assigned", reply_markup=reply_markup)
        
        elif query.data == "admin_get_info":
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            if not self.client_data:
                await query.edit_message_text("📋 No clients registered yet.")
                return
            
            # Create client selection buttons with usernames
            keyboard = []
            for client_id, data in self.client_data.items():
                telegram_id = data.get("telegram_id", "")
                # Try to get actual username from Telegram
                try:
                    user = await context.bot.get_chat(telegram_id)
                    username = user.username or user.first_name or f"User{telegram_id}"
                except:
                    username = f"User{telegram_id}"
                keyboard.append([InlineKeyboardButton(f"👤 @{username} ({client_id})", callback_data=f"select_info_{client_id}")])
            
            keyboard.append([InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text("ℹ️ Select client to get info:\n\nClick on a client to see their details:", reply_markup=reply_markup)
        
        elif query.data.startswith("select_info_"):
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            client_id = query.data.split("_", 2)[2]
            client_data = self.client_data.get(client_id)
            
            if not client_data:
                await query.edit_message_text("❌ Client not found!")
                return
            
            info_text = f"📋 Client Information:\n"
            info_text += f"ID: {client_id}\n"
            info_text += f"Telegram ID: {client_data['telegram_id']}\n"
            info_text += f"Alias: {client_data.get('alias', 'Not set')}"
            
            # Add back button
            keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(info_text, reply_markup=reply_markup)
        
        elif query.data == "admin_assign_group_chat":
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            # Show current groups and options
            current_groups = self.config.get("GROUP_IDS", [])
            
            if not current_groups:
                text = "🏢 Group Management\n\nNo groups assigned yet.\n\nTo add this chat as a group:\n1. Make sure the bot is added to the group\n2. Click '➕ Add This Chat' below"
                keyboard = [
                    [InlineKeyboardButton("➕ Add This Chat", callback_data="admin_add_current_chat")],
                    [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]
                ]
            else:
                text = "🏢 Group Management\n\nCurrently assigned groups:\n"
                for i, group_id in enumerate(current_groups, 1):
                    # Get group name using our method
                    group_name = await self.get_group_name(str(group_id), context)
                    text += f"{i}. {group_name} (ID: {group_id})\n"
                text += "\nTo add this chat as a group:\n1. Make sure the bot is added to the group\n2. Click '➕ Add This Chat' below"
                
                keyboard = [
                    [InlineKeyboardButton("➕ Add This Chat", callback_data="admin_add_current_chat")],
                    [InlineKeyboardButton("🗑️ Delete Groups", callback_data="admin_delete_groups")],
                    [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]
                ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup)
        
        elif query.data == "admin_add_current_chat":
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            chat_id = query.message.chat.id
            
            if chat_id in self.config.get("GROUP_IDS", []):
                await query.edit_message_text("✅ This chat is already authorized!")
                return
            
            # Store the chat_id temporarily for name input
            if "TEMP_GROUP_ADD" not in self.config:
                self.config["TEMP_GROUP_ADD"] = {}
            
            self.config["TEMP_GROUP_ADD"]["pending_chat_id"] = chat_id
            self.save_config()
            
            # Show options for adding the group
            keyboard = [
                [InlineKeyboardButton("✅ Add with Auto Name", callback_data=f"add_group_auto_{chat_id}")],
                [InlineKeyboardButton("✏️ Add with Custom Name", callback_data=f"add_group_custom_{chat_id}")],
                [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Try to get current group name
            try:
                group_chat = await context.bot.get_chat(chat_id)
                current_name = group_chat.title or f"Group {chat_id}"
            except:
                current_name = f"Group {chat_id}"
            
            await query.edit_message_text(
                f"🏢 Add Group\n\n"
                f"Current Group: {current_name}\n"
                f"Group ID: {chat_id}\n\n"
                f"Choose how to add this group:\n"
                f"✅ Auto Name - Use Telegram group name\n"
                f"✏️ Custom Name - Set your own name",
                reply_markup=reply_markup
            )
        
        elif query.data.startswith("add_group_auto_"):
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            chat_id = int(query.data.split("_")[3])
            
            # Add to GROUP_IDS
            if "GROUP_IDS" not in self.config:
                self.config["GROUP_IDS"] = []
            
            if chat_id not in self.config["GROUP_IDS"]:
                self.config["GROUP_IDS"].append(chat_id)
            
            # Try to get and store the group name
            try:
                group_chat = await context.bot.get_chat(chat_id)
                group_name = group_chat.title or f"Group {chat_id}"
                
                # Store the name
                if "GROUP_NAMES" not in self.config:
                    self.config["GROUP_NAMES"] = {}
                self.config["GROUP_NAMES"][str(chat_id)] = group_name
            except:
                group_name = f"Group {chat_id}"
            
            self.save_config()
            
            # Clean up temp data
            if "TEMP_GROUP_ADD" in self.config:
                del self.config["TEMP_GROUP_ADD"]
                self.save_config()
            
            # Add back button
            keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ Group added successfully!\n\n"
                f"Group: {group_name}\n"
                f"ID: {chat_id}",
                reply_markup=reply_markup
            )
        
        elif query.data.startswith("add_group_custom_"):
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            chat_id = int(query.data.split("_")[3])
            
            # Store chat_id for name input
            if "TEMP_GROUP_ADD" not in self.config:
                self.config["TEMP_GROUP_ADD"] = {}
            
            self.config["TEMP_GROUP_ADD"]["pending_chat_id"] = chat_id
            self.config["TEMP_GROUP_ADD"]["waiting_for_name"] = True
            self.save_config()
            
            # Add back button
            keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="admin_panel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✏️ Set Custom Group Name\n\n"
                f"Group ID: {chat_id}\n\n"
                f"Please send the custom name for this group:",
                reply_markup=reply_markup
            )
        
        elif query.data == "admin_delete_groups":
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            current_groups = self.config.get("GROUP_IDS", [])
            
            if not current_groups:
                await query.edit_message_text("📋 No groups to delete!")
                return
            
            # Create delete buttons for each group
            keyboard = []
            for i, group_id in enumerate(current_groups, 1):
                # Get group name using our method
                group_name = await self.get_group_name(str(group_id), context)
                keyboard.append([InlineKeyboardButton(f"🗑️ Delete {group_name}", callback_data=f"delete_group_{group_id}")])
            
            keyboard.append([InlineKeyboardButton("🔙 Back to Group Management", callback_data="admin_assign_group_chat")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text("🗑️ Select a group to delete:", reply_markup=reply_markup)
        
        elif query.data.startswith("delete_group_"):
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            group_id = int(query.data.split("_", 2)[2])
            current_groups = self.config.get("GROUP_IDS", [])
            
            if group_id in current_groups:
                current_groups.remove(group_id)
                self.config["GROUP_IDS"] = current_groups
                self.save_config()
                
                # Add back button
                keyboard = [[InlineKeyboardButton("🔙 Back to Group Management", callback_data="admin_assign_group_chat")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Get group name for confirmation message
                group_name = await self.get_group_name(str(group_id), context)
                
                await query.edit_message_text(f"✅ {group_name} deleted successfully!", reply_markup=reply_markup)
        else:
            await query.edit_message_text("❌ Group not found!")
            return
        
        elif query.data == "admin_panel":
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            # Only allow in private chat
            if query.message.chat.type != "private":
                await query.edit_message_text("❌ Admin panel can only be used in private chat with the bot!")
                return
            
            keyboard = [
                [InlineKeyboardButton("📋 List Clients", callback_data="admin_list_clients")],
                [InlineKeyboardButton("➕ Add Group", callback_data="admin_add_group")],
                [InlineKeyboardButton("🔗 Assign Client to Groups", callback_data="admin_assign_client_groups")],
                [InlineKeyboardButton("🗑️ Delete Groups", callback_data="admin_delete_groups")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            admin_text = """🔧 Admin Panel

📱 **Button Commands (Click to use):**
📋 List Clients - View all registered clients
➕ Add Group - Add current group as authorized
🔗 Assign Client to Groups - Assign specific groups to clients
🗑️ Delete Groups - Remove unwanted groups

📝 **Text Commands (Type to use):**
• /listclients - List all registered clients
• /getinfo <client_id> - Get client details
• /setalias <client_id> <alias> - Set client alias
• /assigngroup - Add current group as authorized

🔐 **Security Commands:**
• /pending - List pending clients for approval
• /approve <telegram_id> - Approve a client
• /reject <telegram_id> - Reject a client

Select an option below or use text commands directly!"""
            
            await query.edit_message_text(admin_text, reply_markup=reply_markup)
        
        elif query.data.startswith("approve_"):
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            telegram_id = int(query.data.split("_", 1)[1])
            pending_clients = self.config.get("PENDING_CLIENTS", {})
            
            if str(telegram_id) not in pending_clients:
                await query.edit_message_text("❌ Client not found in pending list!")
                return
            
            # Generate client ID and approve
            client_id = self.generate_client_id()
            self.client_data[client_id] = {
                "telegram_id": telegram_id,
                "status": "approved"
            }
            self.save_client_data()
            
            # Remove from pending
            del pending_clients[str(telegram_id)]
            self.config["PENDING_CLIENTS"] = pending_clients
            self.save_config()
            
            # Get client info for display
            client_info = pending_clients.get(str(telegram_id), {})
            username = client_info.get("username", "Unknown")
            
            # Add back button
            keyboard = [[InlineKeyboardButton("🔙 Back to Pending Clients", callback_data="admin_pending_clients")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(f"✅ Client @{username} approved successfully!\n\nClient ID: {client_id}", reply_markup=reply_markup)
        
        elif query.data.startswith("reject_"):
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            telegram_id = int(query.data.split("_", 1)[1])
            pending_clients = self.config.get("PENDING_CLIENTS", {})
            
            if str(telegram_id) not in pending_clients:
                await query.edit_message_text("❌ Client not found in pending list!")
                return
            
            # Get client info for display
            client_info = pending_clients.get(str(telegram_id), {})
            username = client_info.get("username", "Unknown")
            
            # Remove from pending
            del pending_clients[str(telegram_id)]
            self.config["PENDING_CLIENTS"] = pending_clients
            self.save_config()
            
            # Add back button
            keyboard = [[InlineKeyboardButton("🔙 Back to Pending Clients", callback_data="admin_pending_clients")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(f"❌ Client @{username} rejected successfully!", reply_markup=reply_markup)
        
        elif query.data == "admin_pending_clients":
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            pending_clients = self.config.get("PENDING_CLIENTS", {})
            
            if not pending_clients:
                await query.edit_message_text("📋 No pending clients")
                return
            
            clients_text = "📋 Pending Clients:\n\n"
            keyboard = []
            
            for telegram_id, data in pending_clients.items():
                username = data.get("username", "None")
                first_name = data.get("first_name", "None")
                timestamp = data.get("timestamp", "Unknown")
                clients_text += f"• ID: {telegram_id}\n"
                clients_text += f"  Username: @{username}\n"
                clients_text += f"  Name: {first_name}\n"
                clients_text += f"  Time: {timestamp}\n\n"
                
                # Add approve/reject buttons for each client
                keyboard.append([
                    InlineKeyboardButton(f"✅ Approve {username}", callback_data=f"approve_{telegram_id}"),
                    InlineKeyboardButton(f"❌ Reject {username}", callback_data=f"reject_{telegram_id}")
                ])
            
            # Add back button
            keyboard.append([InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(clients_text, reply_markup=reply_markup)
        
        elif query.data == "admin_delete_clients":
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            if not self.client_data:
                await query.edit_message_text("📋 No clients registered yet.")
                return
            
            # Create client selection buttons with usernames
            keyboard = []
            for client_id, data in self.client_data.items():
                telegram_id = data.get("telegram_id", "")
                # Try to get actual username from Telegram
                try:
                    user = await context.bot.get_chat(telegram_id)
                    username = user.username or user.first_name or f"User{telegram_id}"
                except:
                    username = f"User{telegram_id}"
                keyboard.append([InlineKeyboardButton(f"🗑️ @{username} ({client_id})", callback_data=f"delete_client_{client_id}")])
            
            keyboard.append([InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text("🗑️ Delete Clients:\n\nSelect a client to delete:", reply_markup=reply_markup)
        
        elif query.data.startswith("delete_client_"):
            if not self.is_admin(query.from_user.id):
                await query.edit_message_text("❌ Admin access required!")
                return
            
            client_id = query.data.split("_", 2)[2]
            client_data = self.client_data.get(client_id)
            
            if not client_data:
                await query.edit_message_text("❌ Client not found!")
                return
            
            telegram_id = client_data.get("telegram_id", "Unknown")
            # Try to get actual username from Telegram
            try:
                user = await context.bot.get_chat(telegram_id)
                username = user.username or user.first_name or f"User{telegram_id}"
            except:
                username = f"User{telegram_id}"
            
            # Remove client from client_data
            del self.client_data[client_id]
            self.save_client_data()
            
            # Remove from group assignments if exists
            if "CLIENT_GROUP_ASSIGNMENTS" in self.config:
                if client_id in self.config["CLIENT_GROUP_ASSIGNMENTS"]:
                    del self.config["CLIENT_GROUP_ASSIGNMENTS"][client_id]
                    self.save_config()
            
            # Remove from pending clients if exists
            if "PENDING_CLIENTS" in self.config:
                if str(telegram_id) in self.config["PENDING_CLIENTS"]:
                    del self.config["PENDING_CLIENTS"][str(telegram_id)]
                    self.save_config()
            
            success_text = f"✅ Client deleted successfully!\n\n"
            success_text += f"Deleted Client:\n"
            success_text += f"• ID: {client_id}\n"
            success_text += f"• Telegram ID: {telegram_id}\n"
            success_text += f"• Username: @{username}"
            
            # Add back button
            keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(success_text, reply_markup=reply_markup)
    
    async def handle_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages from groups and forward to all clients"""
        message = update.message
        chat_id = message.chat.id
        
        # Only process messages from authorized groups
        if chat_id not in self.config.get("GROUP_IDS", []):
            return
        
        # Skip bot messages
        if message.from_user.is_bot:
            return
        
        print(f"🔍 Debug: Received message from group {chat_id}")
        print(f"🔍 Debug: Message from user: {message.from_user.id}")
        print(f"🔍 Debug: Message text: {message.text}")
        
        # Forward to all clients
        for client_id, client_data in self.client_data.items():
            client_telegram_id = client_data.get("telegram_id")
            if not client_telegram_id:
                continue
            
            try:
                # Get sender info
                sender_name = message.from_user.first_name or message.from_user.username or f"User{message.from_user.id}"
                
                if message.text:
                    await context.bot.send_message(
                        chat_id=client_telegram_id,
                        text=message.text
                    )
                    print(f"✅ Debug: Forwarded text to client {client_telegram_id}")
                elif message.photo:
                    await context.bot.send_photo(
                        chat_id=client_telegram_id,
                        photo=message.photo[-1].file_id
                    )
                    print(f"✅ Debug: Forwarded photo to client {client_telegram_id}")
                elif message.video:
                    await context.bot.send_video(
                        chat_id=client_telegram_id,
                        video=message.video.file_id
                    )
                    print(f"✅ Debug: Forwarded video to client {client_telegram_id}")
                elif message.audio:
                    await context.bot.send_audio(
                        chat_id=client_telegram_id,
                        audio=message.audio.file_id
                    )
                    print(f"✅ Debug: Forwarded audio to client {client_telegram_id}")
                elif message.document:
                    await context.bot.send_document(
                        chat_id=client_telegram_id,
                        document=message.document.file_id
                    )
                    print(f"✅ Debug: Forwarded document to client {client_telegram_id}")
                elif message.voice:
                    await context.bot.send_voice(
                        chat_id=client_telegram_id,
                        voice=message.voice.file_id
                    )
                    print(f"✅ Debug: Forwarded voice to client {client_telegram_id}")
                
            except Exception as e:
                print(f"❌ Debug: Error forwarding to client {client_telegram_id}: {e}")
                logger.error(f"Error forwarding to client {client_telegram_id}: {e}")
    
    async def handle_employee_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle employee replies (kept for backward compatibility but not used)"""
        # This function is kept for backward compatibility but the reply functionality is removed
        pass
    
    async def approve_client_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to approve a client"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin access required!")
            return
        
        # Only allow in private chat
        if update.effective_chat.type != "private":
            await update.message.reply_text("❌ This command can only be used in private chat with the bot!")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Usage: /approve <telegram_id>")
            return
        
        try:
            telegram_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid Telegram ID!")
            return
        
        # Check if client exists in pending
        if not self.is_client_pending(telegram_id):
            await update.message.reply_text("❌ Client not found in pending list!")
            return
        
        # Create client ID and approve
        client_id = self.generate_client_id()
        self.client_data[client_id] = {
            "telegram_id": telegram_id,
            "status": "approved"
        }
        self.save_client_data()
        
        # Remove from pending
        self.reject_client(telegram_id)
        
        await update.message.reply_text(f"✅ Client {telegram_id} approved with ID: {client_id}")
    
    async def reject_client_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to reject a client"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin access required!")
            return
        
        # Only allow in private chat
        if update.effective_chat.type != "private":
            await update.message.reply_text("❌ This command can only be used in private chat with the bot!")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Usage: /reject <telegram_id>")
            return
        
        try:
            telegram_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid Telegram ID!")
            return
        
        # Check if client exists in pending
        if not self.is_client_pending(telegram_id):
            await update.message.reply_text("❌ Client not found in pending list!")
            return
        
        # Remove from pending
        self.reject_client(telegram_id)
        
        await update.message.reply_text(f"❌ Client {telegram_id} rejected")
    
    async def pending_clients_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to list pending clients"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin access required!")
            return
        
        # Only allow in private chat
        if update.effective_chat.type != "private":
            await update.message.reply_text("❌ This command can only be used in private chat with the bot!")
            return
        
        pending_clients = self.config.get("PENDING_CLIENTS", {})
        
        if not pending_clients:
            await update.message.reply_text("📋 No pending clients")
            return
        
        clients_text = "📋 Pending Clients:\n\n"
        keyboard = []
        
        for telegram_id, data in pending_clients.items():
            username = data.get("username", "None")
            first_name = data.get("first_name", "None")
            timestamp = data.get("timestamp", "Unknown")
            clients_text += f"• ID: {telegram_id}\n"
            clients_text += f"  Username: @{username}\n"
            clients_text += f"  Name: {first_name}\n"
            clients_text += f"  Time: {timestamp}\n\n"
            
            # Add approve/reject buttons for each client
            keyboard.append([
                InlineKeyboardButton(f"✅ Approve {username}", callback_data=f"approve_{telegram_id}"),
                InlineKeyboardButton(f"❌ Reject {username}", callback_data=f"reject_{telegram_id}")
            ])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(clients_text, reply_markup=reply_markup)
    
    async def assign_group_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to assign group"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin access required!")
            return
        
        chat_id = update.effective_chat.id
        
        if chat_id in self.config.get("GROUP_IDS", []):
            await update.message.reply_text("✅ Group already authorized!")
            return
        
        # Store the chat_id temporarily for name input
        if "TEMP_GROUP_ADD" not in self.config:
            self.config["TEMP_GROUP_ADD"] = {}
        
        self.config["TEMP_GROUP_ADD"]["pending_chat_id"] = chat_id
        self.save_config()
        
        # Show options for adding the group
        keyboard = [
            [InlineKeyboardButton("✅ Add with Auto Name", callback_data=f"add_group_auto_{chat_id}")],
            [InlineKeyboardButton("✏️ Add with Custom Name", callback_data=f"add_group_custom_{chat_id}")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="admin_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Try to get current group name
        try:
            group_chat = await context.bot.get_chat(chat_id)
            current_name = group_chat.title or f"Group {chat_id}"
        except:
            current_name = f"Group {chat_id}"
        
        await update.message.reply_text(
            f"🏢 Add Group\n\n"
            f"Current Group: {current_name}\n"
            f"Group ID: {chat_id}\n\n"
            f"Choose how to add this group:\n"
            f"✅ Auto Name - Use Telegram group name\n"
            f"✏️ Custom Name - Set your own name",
            reply_markup=reply_markup
        )
    
    async def set_alias_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set alias for a client"""
        if not self.is_admin(update.message.from_user.id):
            await update.message.reply_text("❌ Admin access required!")
            return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("❌ Usage: /setalias <client_id> <alias>")
            return
        
        client_id = context.args[0].upper()
        alias = " ".join(context.args[1:])
        
        if client_id not in self.client_data:
            await update.message.reply_text("❌ Client not found!")
            return
        
        # Update client data with alias
        if "aliases" not in self.client_data[client_id]:
            self.client_data[client_id]["aliases"] = {}
        
        self.client_data[client_id]["aliases"]["custom"] = alias
        self.save_client_data()
        
        await update.message.reply_text(f"✅ Alias set for {client_id}: {alias}")
    
    async def set_group_name_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set custom name for a group"""
        if not self.is_admin(update.message.from_user.id):
            await update.message.reply_text("❌ Admin access required!")
            return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("❌ Usage: /setgroupname <group_id> <name>")
            return
        
        group_id = context.args[0]
        group_name = " ".join(context.args[1:])
        
        if group_id not in self.config.get("GROUP_IDS", []):
            await update.message.reply_text("❌ Group not found in authorized groups!")
            return
        
        # Store the custom group name
        if "GROUP_NAMES" not in self.config:
            self.config["GROUP_NAMES"] = {}
        
        self.config["GROUP_NAMES"][group_id] = group_name
        self.save_config()
        
        await update.message.reply_text(f"✅ Group name set for {group_id}: {group_name}")
    
    async def get_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to get client information"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin access required!")
            return
        
        # Only allow in private chat
        if update.effective_chat.type != "private":
            await update.message.reply_text("❌ This command can only be used in private chat with the bot!")
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
        
        # Only allow in private chat
        if update.effective_chat.type != "private":
            await update.message.reply_text("❌ This command can only be used in private chat with the bot!")
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
        """Show help"""
        user_id = update.effective_user.id
        
        if self.is_admin(user_id):
            # Only show admin panel in private chat
            if update.effective_chat.type == "private":
                # Create admin buttons
                keyboard = [
                    [InlineKeyboardButton("📋 List Clients", callback_data="admin_list_clients")],
                    [InlineKeyboardButton("➕ Add Group", callback_data="admin_add_group")],
                    [InlineKeyboardButton("🔧 Admin Panel", callback_data="admin_panel")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                help_text = """
🔧 Admin Panel

📱 **Button Commands (Click to use):**
📋 List Clients - View all registered clients
➕ Add Group - Add current group as authorized
🔧 Admin Panel - Open full admin panel
🔗 Assign Client to Groups - Assign specific groups to clients
🗑️ Delete Clients - Remove unwanted clients
⏳ Pending Clients - Approve/reject new clients

📝 **Text Commands (Type to use):**
• /listclients - List all registered clients
• /getinfo <client_id> - Get client details
• /setalias <client_id> <alias> - Set client alias
• /assigngroup - Add current group as authorized

🔐 **Security Commands:**
• /pending - List pending clients for approval
• /approve <telegram_id> - Approve a client
• /reject <telegram_id> - Reject a client

🏢 **Group Management:**
• View all assigned groups
• Add new groups from any chat
• Delete unwanted groups
• Assign clients to specific groups

💡 **Quick Tips:**
• Use buttons for easy navigation
• Use text commands for quick access
• All commands work in private chat only
                """
                
                await update.message.reply_text(help_text, reply_markup=reply_markup)
            else:
                # In groups, show group-specific help
                help_text = """
🔧 Admin Commands in Groups

Available commands in this group:
• /assigngroup - Add this group as authorized (with name options)
• /help - Show this help message

📝 **How to add this group:**
1. Use /assigngroup command
2. Choose "Auto Name" or "Custom Name"
3. If custom name, type the name in private chat

For full admin features, use /help in private chat with the bot.
                """
                await update.message.reply_text(help_text)
        else:
            help_text = """
💬 Welcome! Send me any message and I'll forward it to the team.

✅ You'll receive a confirmation when your message is sent.
            """
            
            await update.message.reply_text(help_text)
    
    async def admin_panel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin panel with buttons"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin access required!")
            return
        
        # Only allow in private chat
        if update.effective_chat.type != "private":
            await update.message.reply_text("❌ This command can only be used in private chat with the bot!")
            return
        
        keyboard = [
            [InlineKeyboardButton("📋 List Clients", callback_data="admin_list_clients")],
            [InlineKeyboardButton("➕ Add Group", callback_data="admin_add_group")],
            [InlineKeyboardButton("🔗 Assign Client to Groups", callback_data="admin_assign_client_groups")],
            [InlineKeyboardButton("🗑️ Delete Groups", callback_data="admin_delete_groups")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        admin_text = """🔧 Admin Panel

📱 **Button Commands (Click to use):**
📋 List Clients - View all registered clients
➕ Add Group - Add current group as authorized
🔗 Assign Client to Groups - Assign specific groups to clients
🗑️ Delete Groups - Remove unwanted groups

📝 **Text Commands (Type to use):**
• /listclients - List all registered clients
• /getinfo <client_id> - Get client details
• /setalias <client_id> <alias> - Set client alias
• /setgroupname <group_id> <name> - Set custom group name
• /assigngroup - Add current group as authorized

🔐 **Security Commands:**
• /pending - List pending clients for approval
• /approve <telegram_id> - Approve a client
• /reject <telegram_id> - Reject a client

Select an option below or use text commands directly!"""
        
        await update.message.reply_text(admin_text, reply_markup=reply_markup)

def main():
    """Main function"""
    bot = WorkingBot()
    
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token or bot_token == 'your_bot_token_here':
        print("❌ Error: BOT_TOKEN not set in .env file!")
        return
    
    print("🤖 Bot starting...")
    print("✅ Using bot token from .env file")
    print("🔄 Bot is now running and listening for messages...")
    print("💡 Use Ctrl+C to stop the bot")
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("assigngroup", bot.assign_group_command))
    application.add_handler(CommandHandler("approve", bot.approve_client_command))
    application.add_handler(CommandHandler("reject", bot.reject_client_command))
    application.add_handler(CommandHandler("pending", bot.pending_clients_command))
    application.add_handler(CommandHandler("setalias", bot.set_alias_command))
    application.add_handler(CommandHandler("setgroupname", bot.set_group_name_command))
    application.add_handler(CommandHandler("getinfo", bot.get_info_command))
    application.add_handler(CommandHandler("listclients", bot.list_clients_command))
    application.add_handler(CommandHandler("admin", bot.admin_panel_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("start", bot.help_command))
    
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & ~filters.COMMAND,
        bot.handle_private_message
    ))
    
    application.add_handler(MessageHandler(
        filters.ChatType.GROUPS & ~filters.COMMAND,
        bot.handle_group_message
    ))
    
    application.add_handler(CallbackQueryHandler(bot.handle_callback_query))
    
    # Run the bot
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}") 