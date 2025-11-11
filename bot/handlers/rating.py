"""Rating handler"""
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session

from bot.database.session import SessionLocal
from bot.database.repositories import RoomRepository, UserRepository
from bot.services.rating_service import RatingService
from bot.utils.keyboards import get_rating_keyboard


async def rate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /rate command"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    db: Session = SessionLocal()
    try:
        # Find room for this chat (in future: by telegram_group_id)
        # For now, find active rooms where user participates
        rooms = RoomRepository.get_user_rooms(db, user_id)
        
        if not rooms:
            await update.message.reply_text(
                "У вас нет активных комнат для оценки.\n"
                "Команда /rate доступна только в комнатах после просмотра."
            )
            return
        
        # For MVP: use first active room
        # In future: determine room by chat_id
        room = rooms[0]
        
        # Get users to rate
        users_to_rate = RatingService.get_users_to_rate(db, room.id, user_id)
        
        if not users_to_rate:
            await update.message.reply_text(
                "✅ Вы уже оценили всех участников этой комнаты!"
            )
            return
        
        # Get first user to rate
        user_to_rate_id = users_to_rate[0]
        user_to_rate = UserRepository.get_by_id(db, user_to_rate_id)
        
        if not user_to_rate:
            await update.message.reply_text("❌ Пользователь не найден.")
            return
        
        # Store state for rating
        if not hasattr(context, 'user_data'):
            context.user_data = {}
        context.user_data[f'rating_room_{room.id}'] = {
            'room_id': room.id,
            'users_to_rate': users_to_rate,
            'current_index': 0
        }
        
        await update.message.reply_text(
            f"Оцените активность участника:\n\n"
            f"👤 {user_to_rate.first_name}"
            + (f" (@{user_to_rate.username})" if user_to_rate.username else ""),
            reply_markup=get_rating_keyboard(room.id, user_to_rate_id)
        )
    finally:
        db.close()


async def rate_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle rate_user callback"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split(":")
    room_id = int(parts[1])
    rated_id = int(parts[2])
    score = int(parts[3])
    
    rater_id = query.from_user.id
    
    db: Session = SessionLocal()
    try:
        # Create rating
        success = RatingService.create_rating(db, room_id, rater_id, rated_id, score)
        
        if not success:
            await query.edit_message_text("❌ Не удалось сохранить оценку.")
            return
        
        # Get next user to rate
        users_to_rate = RatingService.get_users_to_rate(db, room_id, rater_id)
        
        if not users_to_rate:
            await query.edit_message_text(
                "✅ Спасибо! Вы оценили всех участников.\n\n"
                "Ваши оценки сохранены и учтены в рейтингах."
            )
            return
        
        # Get next user
        next_user_id = users_to_rate[0]
        next_user = UserRepository.get_by_id(db, next_user_id)
        
        if not next_user:
            await query.edit_message_text("✅ Оценка сохранена!")
            return
        
        await query.edit_message_text(
            f"✅ Оценка сохранена!\n\n"
            f"Оцените следующего участника:\n\n"
            f"👤 {next_user.first_name}"
            + (f" (@{next_user.username})" if next_user.username else ""),
            reply_markup=get_rating_keyboard(room_id, next_user_id)
        )
    finally:
        db.close()

