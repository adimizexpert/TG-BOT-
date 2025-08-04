# 🚀 VPS Hosting Guide - Client Privacy Manager Bot

## 📋 **Prerequisites**
- VPS with Ubuntu 20.04/22.04 LTS
- Minimum 1GB RAM, 25GB Storage
- SSH access to your VPS
- Your bot token: `8345847465:AAEKaXDbiAx_fgb77uH-pZ9k6V2xVUHwU04`

## 🔧 **Step-by-Step VPS Setup**

### **Step 1: Initial VPS Setup**

#### **Connect to VPS:**
```bash
ssh root@YOUR_VPS_IP
```

#### **Update System:**
```bash
apt update && apt upgrade -y
```

#### **Create Non-Root User:**
```bash
adduser botuser
usermod -aG sudo botuser
su - botuser
```

#### **Install Required Software:**
```bash
# Install Python, Git, and other tools
sudo apt install python3 python3-pip python3-venv git curl nano htop -y

# Verify installations
python3 --version
git --version
```

### **Step 2: Upload Bot Files**

#### **Method 1: Git Clone (Recommended)**
```bash
cd /home/botuser
git clone https://github.com/adimizexpert/TG-BOT-.git telegram-bot
cd telegram-bot
```

#### **Method 2: Manual Upload via SCP**
```bash
# From your local machine
scp -r "TG final bot" botuser@YOUR_VPS_IP:/home/botuser/telegram-bot
```

### **Step 3: Set Up Environment**

#### **Create Virtual Environment:**
```bash
cd /home/botuser/telegram-bot
python3 -m venv venv
source venv/bin/activate
```

#### **Install Dependencies:**
```bash
pip install -r requirements.txt
```

#### **Create Environment File:**
```bash
nano .env
```

**Add this content to .env:**
```
BOT_TOKEN=8345847465:AAEKaXDbiAx_fgb77uH-pZ9k6V2xVUHwU04
```

### **Step 4: Test Bot**

#### **Test Run:**
```bash
python final_bot.py
```

**Expected Output:**
```
🤖 Final Client Privacy Manager starting...
✅ Using bot token from .env file
🔄 Bot is now running...
💡 Use Ctrl+C to stop the bot
🚀 Starting bot...
```

Press `Ctrl+C` to stop the test.

### **Step 5: Create Systemd Service (Auto-Start)**

#### **Create Service File:**
```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

**Add this content:**
```ini
[Unit]
Description=Client Privacy Manager Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/home/botuser/telegram-bot
Environment=PATH=/home/botuser/telegram-bot/venv/bin
ExecStart=/home/botuser/telegram-bot/venv/bin/python /home/botuser/telegram-bot/final_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### **Enable and Start Service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

#### **Check Service Status:**
```bash
sudo systemctl status telegram-bot
```

### **Step 6: Firewall Setup (Optional but Recommended)**

```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS (if needed later)
sudo ufw allow 80
sudo ufw allow 443

# Check status
sudo ufw status
```

### **Step 7: Monitor and Manage**

#### **Useful Commands:**

**Check Bot Status:**
```bash
sudo systemctl status telegram-bot
```

**View Live Logs:**
```bash
sudo journalctl -u telegram-bot -f
```

**Restart Bot:**
```bash
sudo systemctl restart telegram-bot
```

**Stop Bot:**
```bash
sudo systemctl stop telegram-bot
```

**Update Bot Code:**
```bash
cd /home/botuser/telegram-bot
git pull origin main
sudo systemctl restart telegram-bot
```

## 🔐 **Security Best Practices**

### **1. SSH Key Authentication:**
```bash
# Generate SSH key on your local machine
ssh-keygen -t rsa -b 4096

# Copy public key to VPS
ssh-copy-id botuser@YOUR_VPS_IP

# Disable password authentication
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart ssh
```

### **2. Regular Updates:**
```bash
# Set up automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

### **3. Backup Data:**
```bash
# Backup bot data
cp /home/botuser/telegram-bot/config.json ~/config_backup.json
cp /home/botuser/telegram-bot/client_data.json ~/client_data_backup.json
```

## 📊 **Monitoring and Maintenance**

### **System Resources:**
```bash
# Check memory usage
free -h

# Check disk usage
df -h

# Check CPU usage
htop
```

### **Bot Performance:**
```bash
# Check bot process
ps aux | grep python

# Monitor bot logs
tail -f /var/log/syslog | grep telegram-bot
```

## 🚨 **Troubleshooting**

### **Common Issues:**

#### **Bot Not Starting:**
```bash
# Check service logs
sudo journalctl -u telegram-bot --no-pager

# Check Python path
which python3

# Verify .env file
cat /home/botuser/telegram-bot/.env
```

#### **Permission Issues:**
```bash
# Fix ownership
sudo chown -R botuser:botuser /home/botuser/telegram-bot

# Fix permissions
chmod +x /home/botuser/telegram-bot/final_bot.py
```

#### **Memory Issues:**
```bash
# Check memory usage
free -h

# Restart bot if needed
sudo systemctl restart telegram-bot
```

## 📱 **Post-Deployment Checklist**

- [ ] ✅ Bot starts automatically on VPS reboot
- [ ] ✅ Bot responds to `/start` command
- [ ] ✅ Admin panel works correctly
- [ ] ✅ Client approval system functions
- [ ] ✅ Message forwarding works (3-letter privacy)
- [ ] ✅ Group assignment works
- [ ] ✅ Reply routing functions properly
- [ ] ✅ All admin features accessible
- [ ] ✅ Logs are being generated
- [ ] ✅ Service auto-restarts on failure

## 🎯 **Success Indicators**

Your bot is successfully hosted when:

1. **Service Status**: `sudo systemctl status telegram-bot` shows "active (running)"
2. **Bot Responds**: Bot replies to `/start` in Telegram
3. **Admin Panel**: All 6 admin options work correctly
4. **Message Flow**: Client messages → Group, Group replies → Client
5. **Privacy**: Only 3 letters of usernames shown
6. **Auto-Start**: Bot starts automatically after VPS reboot

## 🔄 **Maintenance Schedule**

### **Weekly:**
- Check service status
- Review logs for errors
- Monitor system resources

### **Monthly:**
- Update system packages
- Backup configuration files
- Check disk space usage

### **As Needed:**
- Update bot code from GitHub
- Restart service after updates
- Monitor for new features or security patches

---

**🎉 Congratulations! Your Client Privacy Manager Bot is now running 24/7 on your VPS!** 