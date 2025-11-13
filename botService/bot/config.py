"""Configuration module for the bot"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Bot configuration"""
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Database URL - можно использовать SQLite для локального тестирования
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL or DATABASE_URL == "postgresql://cowatch_user:cowatch_password@localhost:5432/cowatch":
        # Используем SQLite если PostgreSQL не настроен
        # Определяем путь к БД относительно корня проекта (botService/)
        project_root = Path(__file__).parent.parent
        db_path = os.getenv("DATABASE_PATH", str(project_root / "cowatch.db"))
        DATABASE_URL = os.getenv("DATABASE_URL_SQLITE", f"sqlite:///{db_path}")
        if not DATABASE_URL.startswith("sqlite"):
            DATABASE_URL = f"sqlite:///{db_path}"
    
    MIN_PARTICIPANTS_DEFAULT = int(os.getenv("MIN_PARTICIPANTS_DEFAULT", "2"))
    
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
        
        # Optional but recommended API keys
        if not cls.KINOPOISK_API_KEY:
            print("⚠️  Warning: KINOPOISK_API_KEY is not set. Movie parsing from URLs will be limited.")
        if not cls.WATCH_TOGETHER_API_KEY:
            print("⚠️  Warning: WATCH_TOGETHER_API_KEY is not set. Watch2Gether integration will be unavailable.")
