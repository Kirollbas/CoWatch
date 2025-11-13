"""Configuration module for the bot"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Bot configuration"""
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Database URL - можно использовать SQLite для локального тестирования
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL or DATABASE_URL == "postgresql://cowatch_user:cowatch_password@localhost:5432/cowatch":
        # Используем SQLite если PostgreSQL не настроен
        DATABASE_URL = os.getenv("DATABASE_URL_SQLITE", "sqlite:///./cowatch.db")
        if not DATABASE_URL.startswith("sqlite"):
            DATABASE_URL = "sqlite:///./cowatch.db"
    
    MIN_PARTICIPANTS_DEFAULT = int(os.getenv("MIN_PARTICIPANTS_DEFAULT", "1"))
    
    # Kinopoisk API configuration
    KINOPOISK_API_KEY = os.getenv("KINOPOISK_API_KEY")
    
    # Watch2Gether API configuration
    WATCH_TOGETHER_API_KEY = os.getenv("WATCH_TOGETHER_API_KEY")
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        if not cls.TELEGRAM_BOT_TOKEN or cls.TELEGRAM_BOT_TOKEN == "your_bot_token_here":
            raise ValueError(
                "TELEGRAM_BOT_TOKEN is not set in .env file.\n"
                "Пожалуйста, получите токен у @BotFather в Telegram и укажите его в .env файле."
            )
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL is not set in environment variables")
        if not cls.KINOPOISK_API_KEY:
            raise ValueError("KINOPOISK_API_KEY is not set in environment variables")
        # Watch Together API key is optional for testing
        if not cls.WATCH_TOGETHER_API_KEY:
            print("⚠️ WATCH_TOGETHER_API_KEY is not set - Watch Together functionality will be disabled")
        elif cls.WATCH_TOGETHER_API_KEY == "test_key_placeholder":
            print("ℹ️ Using test Watch Together API key - rooms will be created with test key")
