#!/usr/bin/env python3
"""
Simple test script to verify bot token and basic functionality
"""

import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

# Load environment variables
load_dotenv()

async def test_bot():
    """Test the bot token and basic functionality"""
    bot_token = os.getenv('BOT_TOKEN')
    
    if not bot_token or bot_token == 'your_bot_token_here':
        print("❌ Error: BOT_TOKEN not set in .env file!")
        return
    
    print("🤖 Testing bot token...")
    
    try:
        bot = Bot(token=bot_token)
        me = await bot.get_me()
        print(f"✅ Bot connected successfully!")
        print(f"📱 Bot name: {me.first_name}")
        print(f"🆔 Bot username: @{me.username}")
        print(f"🆔 Bot ID: {me.id}")
        
        # Test getting updates
        updates = await bot.get_updates()
        print(f"📨 Found {len(updates)} recent updates")
        
        await bot.close()
        print("✅ Bot test completed successfully!")
        
    except Exception as e:
        print(f"❌ Bot test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_bot()) 