#!/usr/bin/env python3
"""Test movie parser directly"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.services.movie_parser import MovieParser
from bot.config import Config

def test_parser():
    """Test the movie parser with real URL"""
    print("🧪 Testing movie parser...")
    print(f"API Key configured: {bool(Config.KINOPOISK_API_KEY)}")
    print(f"API Key: {Config.KINOPOISK_API_KEY[:10]}..." if Config.KINOPOISK_API_KEY else "No API key")
    
    url = "https://www.kinopoisk.ru/film/590286/"
    print(f"\nTesting URL: {url}")
    
    try:
        result = MovieParser.parse_url(url)
        print(f"\nResult: {result}")
        
        if result:
            print(f"✅ Title: {result.get('title')}")
            print(f"✅ Year: {result.get('year')}")
            print(f"✅ Description: {result.get('description', 'No description')[:100]}...")
        else:
            print("❌ No result returned")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parser()