#!/usr/bin/env python3
"""Reset test data and run bot"""

import os
import sys
import subprocess

def reset_and_run():
    """Reset database and restart bot"""
    print("🔄 Resetting test data and restarting bot...")
    
    # Kill existing bot processes
    subprocess.run(["pkill", "-f", "run_test_bot.py"], capture_output=True)
    
    # Remove database
    if os.path.exists("cowatch.db"):
        os.remove("cowatch.db")
        print("🗑️ Removed old database")
    
    # Initialize database
    from bot.database.init_db import init_database
    init_database()
    print("🔧 Initialized database")
    
    # Setup test data
    from setup_test_data import setup_test_data
    setup_test_data()
    print("📊 Setup test data")
    
    # Start bot
    print("🤖 Starting bot...")
    subprocess.run([sys.executable, "run_test_bot.py"])

if __name__ == "__main__":
    reset_and_run()