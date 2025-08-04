#!/usr/bin/env python3
"""
Local bot runner script
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
    print("🤖 Client Privacy Manager - Local Runner")
    print("=" * 50)
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check environment
    if not os.path.exists(".env"):
        print("❌ Error: .env file not found!")
        return
    
    if not os.path.exists("working_bot.py"):
        print("❌ Error: working_bot.py not found!")
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
            [sys.executable, 'working_bot.py'],
            env=env,
            cwd=os.getcwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"✅ Bot started with PID: {process.pid}")
        
        # Monitor the process
        while True:
            if process.poll() is not None:
                # Process has ended
                stdout, stderr = process.communicate()
                if stdout:
                    print("📤 Output:", stdout)
                if stderr:
                    print("❌ Error:", stderr)
                print("🛑 Bot process ended")
                break
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping bot...")
        if 'process' in locals():
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        print("✅ Bot stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 