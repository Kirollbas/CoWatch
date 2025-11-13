#!/usr/bin/env python3
"""Clean restart script"""
import os
import time
import subprocess
import signal

def kill_all_bots():
    """Kill all bot processes"""
    try:
        # Find and kill all python processes running the bot
        result = subprocess.run(['pgrep', '-f', 'run_test_bot.py'], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    print(f"Killing process {pid}")
                    os.kill(int(pid), signal.SIGKILL)
        
        # Also try pkill
        subprocess.run(['pkill', '-f', 'run_test_bot.py'], capture_output=True)
        
    except Exception as e:
        print(f"Error killing processes: {e}")

def main():
    print("🔄 Stopping all bot processes...")
    kill_all_bots()
    
    print("⏳ Waiting for Telegram API to release connection...")
    time.sleep(10)  # Wait 10 seconds for Telegram API
    
    print("🗄️ Cleaning database...")
    if os.path.exists('cowatch.db'):
        os.remove('cowatch.db')
    
    print("🔧 Creating fresh database...")
    from bot.database.init_db import init_database
    init_database()
    
    print("🚀 Starting bot with clean state...")
    os.system('python3 run_test_bot.py')

if __name__ == "__main__":
    main()