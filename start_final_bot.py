#!/usr/bin/env python3
"""
Startup script for the Final Client Privacy Manager Bot
"""

import os
import sys
import subprocess
import signal
import time

def signal_handler(sig, frame):
    print('\n🛑 Stopping bot...')
    sys.exit(0)

def main():
    print("🤖 Final Client Privacy Manager Bot")
    print("=" * 50)
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check environment
    if not os.path.exists(".env"):
        print("❌ Error: .env file not found!")
        return
    
    if not os.path.exists("final_bot.py"):
        print("❌ Error: final_bot.py not found!")
        return
    
    if not os.path.exists("venv"):
        print("❌ Error: Virtual environment not found!")
        return
    
    print("✅ Environment check passed")
    
    # Set up environment variables
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = os.path.abspath('venv')
    env['PATH'] = os.path.abspath('venv/bin') + ':' + env.get('PATH', '')
    
    print("🚀 Starting bot...")
    print("💡 Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        # Run the bot
        process = subprocess.Popen(
            [sys.executable, 'final_bot.py'],
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