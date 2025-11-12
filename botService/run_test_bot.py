#!/usr/bin/env python3
"""Run bot for testing with instructions"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.config import Config

def print_instructions():
    """Print testing instructions"""
    print("=" * 60)
    print("🤖 COWATCH BOT - TESTING INSTRUCTIONS")
    print("=" * 60)
    print()
    print("📋 BEFORE STARTING:")
    print("1. Get bot token from @BotFather in Telegram")
    print("2. Edit .env file and set TELEGRAM_BOT_TOKEN")
    print("3. Run: python3 setup_test_data.py")
    print()
    print("🧪 TEST SCENARIOS:")
    print()
    print("Scenario 1: Compatible slot matching")
    print("- Send /add_movie")
    print("- Send: https://www.kinopoisk.ru/film/447301/")
    print("- Expected: Should show compatible slot for Inception")
    print()
    print("Scenario 2: Auto-join and room creation")
    print("- Send /add_movie") 
    print("- Send: https://www.imdb.com/title/tt0903747/")
    print("- Expected: May auto-join Breaking Bad slot (2/3 → 3/3)")
    print("- Expected: Room should be created automatically")
    print()
    print("Scenario 3: No compatible slots")
    print("- Use test user Charlie (low rating)")
    print("- Try adding any movie")
    print("- Expected: No compatible slots shown")
    print()
    print("📱 BOT COMMANDS:")
    print("/start - Start bot")
    print("/add_movie - Add movie interest")
    print("/my_slots - View your slots")
    print("/profile - View profile")
    print("/help - Help")
    print()
    print("🔧 TEST DATA:")
    print("- Alice (4.5⭐): Has slots for Inception and Breaking Bad")
    print("- Bob (4.3⭐): Joined Breaking Bad slot")
    print("- Charlie (2.1⭐): Low rating user")
    print("- Diana (0⭐): New user")
    print()
    print("=" * 60)

def main():
    """Main function"""
    print_instructions()
    
    # Check if token is set
    try:
        Config.validate()
        print("✅ Configuration valid - starting bot...")
        print()
        
        # Import and run bot
        from bot.main import main as bot_main
        bot_main()
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print()
        print("Please:")
        print("1. Get token from @BotFather")
        print("2. Edit .env file: TELEGRAM_BOT_TOKEN=your_actual_token")
        print("3. Run: python3 setup_test_data.py")
        print("4. Run: python3 run_test_bot.py")
        sys.exit(1)

if __name__ == "__main__":
    main()