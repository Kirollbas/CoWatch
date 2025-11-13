"""Profile and rooms handlers"""
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session

from bot.database.session import SessionLocal
from bot.database.repositories import (
    UserRepository, RoomRepository, 
    UserKinopoiskRepository, UserVoteRepository
)
from bot.utils.formatters import format_user_profile, format_room_info


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /profile command"""
    user_id = update.effective_user.id
    
    db: Session = SessionLocal()
    try:
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            await update.message.reply_text("Пользователь не найден. Используйте /start.")
            return
        
        # Get Kinopoisk link info
        kp_link = UserKinopoiskRepository.get_by_user_id(db, user_id)
        kp_user_id = kp_link.kp_user_id if kp_link else None
        
        # Get imported votes count from Kinopoisk
        imported_votes_count = 0
        if kp_link:
            imported_votes = UserVoteRepository.get_user_votes_map(db, user_id)
            imported_votes_count = len(imported_votes)
        
        # Get bot ratings given by user (ratings this user gave to others)
        from bot.database.models import Rating
        bot_ratings_given = db.query(Rating).filter(Rating.rater_id == user_id).count()
        
        profile_text = format_user_profile(
            user, 
            kp_user_id=kp_user_id,
            imported_votes_count=imported_votes_count,
            bot_ratings_given=bot_ratings_given
        )
        await update.message.reply_text(profile_text, parse_mode="HTML")
    finally:
        db.close()


async def my_rooms_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /my_rooms command"""
    user_id = update.effective_user.id
    
    db: Session = SessionLocal()
    try:
        rooms = RoomRepository.get_user_rooms(db, user_id)
        
        if not rooms:
            await update.message.reply_text("У вас пока нет активных комнат.")
            return
        
        text = "🏠 <b>Ваши активные комнаты:</b>\n\n"
        for room in rooms:
            slot = room.slot
            text += f"• <b>{slot.movie.title}</b>\n"
            text += f"  Время: {slot.datetime.strftime('%d.%m.%Y %H:%M')}\n"
            text += f"  Статус: {room.status}\n\n"
        
        await update.message.reply_text(text, parse_mode="HTML")
    finally:
        db.close()

