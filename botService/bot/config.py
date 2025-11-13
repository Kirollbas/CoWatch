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
        project_root = Path(__file__).parent.parent.resolve()  # Используем resolve() сразу
        db_path_env = os.getenv("DATABASE_PATH")
        if db_path_env:
            db_path = Path(db_path_env).resolve()
        else:
            db_path = project_root / "cowatch.db"
        
        # Проверяем DATABASE_URL_SQLITE из .env, но преобразуем относительный путь в абсолютный
        db_url_sqlite = os.getenv("DATABASE_URL_SQLITE")
        if db_url_sqlite and db_url_sqlite.startswith("sqlite:///"):
            # Извлекаем путь из URL
            db_path_from_env = db_url_sqlite.replace("sqlite:///", "")
            # Преобразуем относительный путь в абсолютный
            if not Path(db_path_from_env).is_absolute():
                # Если путь относительный, разрешаем его относительно project_root
                db_path = (project_root / db_path_from_env).resolve()
            else:
                db_path = Path(db_path_from_env)
            # SQLite требует формат sqlite:///path (три слэша для абсолютного пути)
            db_path_str = str(db_path)
            DATABASE_URL = f"sqlite:///{db_path_str}"
        else:
            # Если DATABASE_URL_SQLITE не указан, используем вычисленный путь
            db_path_str = str(db_path)
            DATABASE_URL = f"sqlite:///{db_path_str}"
    
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
        
        # Optional but recommended API keys
        if not cls.KINOPOISK_API_KEY:
            print("⚠️  Warning: KINOPOISK_API_KEY is not set. Movie parsing from URLs will be limited.")
        # Watch Together API key is optional for testing
        if not cls.WATCH_TOGETHER_API_KEY:
            print("⚠️ WATCH_TOGETHER_API_KEY is not set - Watch Together functionality will be disabled")
        elif cls.WATCH_TOGETHER_API_KEY == "test_key_placeholder":
            print("ℹ️ Using test Watch Together API key - rooms will be created with test key")
