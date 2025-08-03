# 🤖 Telegram Bot - Company Communication System

A secure, feature-rich Telegram bot for company communication with role-based access control (Admin, Employee, Client).

## 🚀 Features

### ✅ Core Functionality
- **Client Message Forwarding**: All media types (text, photo, video, audio, document, voice)
- **Admin Panel**: Full control with buttons and text commands
- **Client Approval System**: Secure client verification
- **Group Management**: Assign clients to specific groups
- **Multi-Admin Support**: Multiple administrators
- **Auto-Restart**: Built-in reliability features

### 🎯 User Roles
- **Admin**: Full control panel, client management, group assignment
- **Employee**: Can send messages from groups to clients
- **Client**: Send messages to assigned groups

## 📋 Requirements

- Python 3.10+
- `python-telegram-bot==21.0.1`
- `python-dotenv==1.0.0`
- Telegram Bot Token

## 🛠️ Quick Setup

### 1. Local Development
```bash
# Clone repository
git clone <your-repo-url>
cd telegram-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your BOT_TOKEN (keep this secret!)

# Run bot
python working_bot.py
```

### 2. Docker Deployment
```bash
# Build and run with Docker
docker-compose up -d

# Or build manually
docker build -t telegram-bot .
docker run -d --name telegram-bot \
  -e BOT_TOKEN=your_token \
  -v $(pwd)/config.json:/app/config.json \
  -v $(pwd)/client_data.json:/app/client_data.json \
  telegram-bot
```

### 3. VPS Deployment
```bash
# Run deployment script
./deploy.sh

# Or manual setup
sudo apt update && sudo apt install python3 python3-pip python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Setup systemd service (see hosting_guide.md)
```

## 🌐 Online Hosting

### Recommended Platforms:

#### 1. **Railway** (Easiest)
- Free tier available
- Automatic deployment from GitHub
- Easy environment variable setup

#### 2. **Render** (Popular)
- Free tier available
- Good for production apps
- Built-in monitoring

#### 3. **VPS** (Full Control)
- DigitalOcean, Linode, Vultr
- Complete control over setup
- Cost: $3-10/month

### Quick Deployment Steps:

1. **Upload to GitHub**
2. **Choose hosting platform**
3. **Set environment variable**: `BOT_TOKEN=your_token`
4. **Deploy** - Done!

📖 **Detailed hosting guide**: See `hosting_guide.md`

## 🔧 Configuration

### Environment Variables
```bash
# Required
BOT_TOKEN=your_telegram_bot_token

# Optional
LOG_LEVEL=INFO
ADMIN_ID=123456789
```

### Admin Setup
1. Add admin IDs to `config.json`
2. Use `/admin` command in private chat
3. Access full admin panel

## 📱 Bot Commands

### Admin Commands (Private Chat Only)
- `/admin` - Open admin panel
- `/help` - Show help information
- `/pending` - List pending clients
- `/approve <id>` - Approve client
- `/reject <id>` - Reject client

### Group Commands
- `/assigngroup` - Add current group as authorized

## 🗂️ File Structure

```
telegram-bot/
├── working_bot.py          # Main bot file
├── config.json             # Configuration data
├── client_data.json        # Client information
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables
├── hosting_guide.md       # Detailed hosting guide
├── deploy.sh              # VPS deployment script
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose setup
├── Procfile               # Heroku/Railway config
└── runtime.txt            # Python version
```

## 🔍 Monitoring

### Local Development
```bash
# View logs
tail -f bot.log

# Check status
ps aux | grep working_bot.py
```

### VPS Deployment
```bash
# View logs
sudo journalctl -u telegram-bot -f

# Check status
sudo systemctl status telegram-bot

# Restart service
sudo systemctl restart telegram-bot
```

## 🛠️ Troubleshooting

### Common Issues:

1. **Bot not responding**
   - Check if service is running
   - Verify BOT_TOKEN is correct
   - Check logs for errors

2. **Permission errors**
   - Ensure files are readable
   - Check file ownership

3. **Event loop errors**
   - Use `working_bot.py` (not `main.py`)
   - Check Python version compatibility

## 📞 Support

- **Documentation**: See `hosting_guide.md`
- **Issues**: Check logs and error messages
- **Updates**: Pull latest code and restart service

## 🚀 Production Checklist

- [ ] Bot token configured
- [ ] Admin IDs set in config.json
- [ ] Environment variables set
- [ ] Service running (VPS) or deployed (cloud)
- [ ] Logs monitored
- [ ] Backups configured
- [ ] Security measures in place

---

**🎉 Your bot is ready for production!**

For detailed hosting instructions, see `hosting_guide.md` 