"""Start and help command handlers"""
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session

from bot.database.session import SessionLocal
from bot.database.repositories import UserRepository
from bot.utils.keyboards import get_main_menu_keyboard


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    db: Session = SessionLocal()
    
    try:
        # Register or update user
        db_user = UserRepository.get_or_create(
            db=db,
            user_id=user.id,
            username=user.username,
            first_name=user.first_name or "Unknown"
        )
        
        welcome_text = (
            f"Привет, {user.first_name}! 👋\n\n"
            "Добро пожаловать в <b>CoWatch</b> - бот для совместного просмотра фильмов и сериалов!\n\n"
            "🎬 Находите людей для просмотра\n"
            "💬 Обсуждайте увиденное\n"
            "⭐ Получайте рейтинги за активность\n\n"
            "Используйте /help для списка команд."
        )
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
    finally:
        db.close()


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "📖 <b>Справка по командам:</b>\n\n"
        "/start - Начать работу с ботом\n"
        "/add_movie - Добавить фильм/сериал для просмотра\n"
        "/my_slots - Мои созданные слоты\n"
        "/my_rooms - Мои активные комнаты\n"
        "/profile - Мой профиль и рейтинг\n"
        "/rate - Оценить участников после обсуждения\n"
        "/cancel - Отменить участие в слоте\n"
        "/help - Показать эту справку\n\n"
        "<b>Как это работает:</b>\n"
        "1. Добавьте фильм через /add_movie\n"
        "2. Создайте слот с удобным временем\n"
        "3. Когда наберется достаточно участников, создастся комната\n"
        "4. После просмотра оцените активность участников"
    )
    
    await update.message.reply_text(help_text, parse_mode="HTML")

