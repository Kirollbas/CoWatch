"""Profile and rooms handlers"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session

from bot.database.session import SessionLocal
from bot.database.repositories import (
    UserRepository, RoomRepository, 
    UserKinopoiskRepository, UserVoteRepository
)
from bot.utils.formatters import format_user_profile, format_room_info

logger = logging.getLogger(__name__)


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
        buttons = []
        
        for room in rooms:
            slot = room.slot
            text += f"• <b>{slot.movie.title}</b>\n"
            text += f"  Время: {slot.datetime.strftime('%d.%m.%Y %H:%M')}\n"
            text += f"  Статус: {room.status}\n"
            
            # Try to get or create invite link for the group
            invite_link = None
            if room.telegram_group_id:
                try:
                    # Try to get existing invite link from chat info
                    chat = await context.bot.get_chat(room.telegram_group_id)
                    if hasattr(chat, 'invite_link') and chat.invite_link:
                        invite_link = chat.invite_link
                    else:
                        # Try to export invite link
                        try:
                            invite_link = await context.bot.export_chat_invite_link(room.telegram_group_id)
                        except Exception as e:
                            logger.warning(f"Could not export invite link for group {room.telegram_group_id}: {e}")
                            # Try to create a new invite link
                            try:
                                invite_link_obj = await context.bot.create_chat_invite_link(
                                    chat_id=room.telegram_group_id,
                                    name=f"Ссылка для {slot.movie.title}"
                                )
                                invite_link = invite_link_obj.invite_link
                            except Exception as e2:
                                logger.error(f"Could not create invite link for group {room.telegram_group_id}: {e2}")
                except Exception as e:
                    logger.error(f"Error getting chat info for group {room.telegram_group_id}: {e}")
            
            if invite_link:
                text += f"  🔗 <a href=\"{invite_link}\">Перейти в группу</a>\n"
                # Add button for the room
                button_text = f"🎬 {slot.movie.title[:30]}"
                buttons.append([InlineKeyboardButton(button_text, url=invite_link)])
            else:
                text += f"  ⚠️ Группа не настроена\n"
            
            text += "\n"
        
        reply_markup = InlineKeyboardMarkup(buttons) if buttons else None
        
        await update.message.reply_text(
            text, 
            parse_mode="HTML",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Error in my_rooms_command for user {user_id}: {e}", exc_info=True)
        await update.message.reply_text("❌ Произошла ошибка при получении списка комнат.")
    finally:
        db.close()

