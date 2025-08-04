#!/usr/bin/env python3
"""
Simple startup script for the Client Privacy Manager Bot
"""

import os
import sys
import subprocess
import time

def main():
    print("🤖 Client Privacy Manager Bot - Startup Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("bot.py"):
        print("❌ Error: bot.py not found in current directory")
        return
    
    # Check if .env exists
    if not os.path.exists(".env"):
        print("❌ Error: .env file not found")
        return
    
    # Check if virtual environment exists
    if not os.path.exists("venv"):
        print("❌ Error: Virtual environment not found")
        return
    
    print("✅ All files found")
    print("✅ Virtual environment ready")
    print("✅ Environment file ready")
    
    # Set up environment
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = os.path.abspath('venv')
    env['PATH'] = os.path.abspath('venv/bin') + ':' + env.get('PATH', '')
    
    print("🚀 Starting bot...")
    print("💡 Press Ctrl+C to stop the bot")
    print("-" * 50)
    
    try:
        # Run the bot
        process = subprocess.Popen(
            [sys.executable, 'bot.py'],
            env=env,
            cwd=os.getcwd()
        )
        
        print(f"✅ Bot started with PID: {process.pid}")
        print("🔄 Bot is running...")
        
        # Wait for the process
        process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping bot...")
        if 'process' in locals():
            process.terminate()
            process.wait()
        print("✅ Bot stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 