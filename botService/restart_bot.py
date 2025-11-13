#!/usr/bin/env python3
"""Script to restart the bot with updated code"""
import os
import signal
import subprocess
import sys
import time

def kill_existing_bots():
    """Kill any existing bot processes"""
    try:
        # Kill processes by name
        subprocess.run(['pkill', '-f', 'run_test_bot.py'], check=False)
        subprocess.run(['pkill', '-f', 'python3.*bot'], check=False)
        time.sleep(2)
        print("✅ Existing bot processes stopped")
    except Exception as e:
        print(f"⚠️ Error stopping processes: {e}")

def start_bot():
    """Start the bot"""
    try:
        print("🚀 Starting bot...")
        os.chdir('/Users/attachsir/Desktop/CoWatch/botService')
        
        # Activate virtual environment and run bot
        cmd = ['bash', '-c', 'source venv/bin/activate && python3 run_test_bot.py']
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")

if __name__ == "__main__":
    print("🔄 Restarting bot...")
    kill_existing_bots()
    start_bot()