# Client Privacy Manager Bot

A Telegram bot designed to maintain client privacy while enabling admins to assign specific client messages to specific groups.

## 🔐 Features

### Client Privacy
- Each client is assigned to exactly one group
- Messages are forwarded only to the assigned group
- Group replies go back only to the original client
- No cross-forwarding between groups

### Admin Features
- **Client Approval System**: Approve/reject new clients with buttons
- **Group Registration**: Add groups with button interface
- **Client-Group Assignment**: Assign clients to specific groups
- **Delete Options**: Remove clients and groups

### Message Support
- 🗣️ Voice Messages
- 🎥 Videos  
- 🖼️ Images
- 💬 Text

## 🚀 Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   - Copy `.env.example` to `.env`
   - Add your bot token to `.env`

3. **Add First Admin**:
   - Edit `config.json` and add your Telegram ID to `ADMIN_IDS`
   - Or use `/addadmin <user_id>` command

4. **Run the Bot**:
   ```bash
   python bot.py
   ```

## 📱 Usage

### For Clients
1. Send `/start` to the bot
2. Wait for admin approval
3. Once approved, send messages to be forwarded to your assigned group

### For Admins
1. Use `/start` to access admin panel
2. Approve/reject clients with buttons
3. Add groups by adding bot to group and clicking "Add Group"
4. Assign clients to groups through admin panel

## 🔧 Configuration

The bot uses two JSON files:
- `config.json`: Bot configuration and admin data
- `client_data.json`: Client information

## 🛡️ Security

- Bot token is stored in `.env` file (not in code)
- Admin-only access to management features
- Client approval system prevents unauthorized access 