"""Profile and rooms handlers"""
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session

from bot.database.session import SessionLocal
from bot.database.repositories import UserRepository, RoomRepository
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
        
        profile_text = format_user_profile(user)
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

