"""Recommended slots listing based on user KP preferences"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session, joinedload

from bot.database.session import SessionLocal
from bot.services.matching import MatchingService
from bot.database.models import Slot
from bot.constants import SlotStatus

logger = logging.getLogger(__name__)


async def recommend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recommended slots ranked by movie interest; exclude watched movies"""
    user_id = update.effective_user.id
    db: Session = SessionLocal()
    try:
        # All open slots with eager loading of participants and movie
        slots = db.query(Slot).options(
            joinedload(Slot.participants),
            joinedload(Slot.movie)
        ).filter(Slot.status == SlotStatus.OPEN).all()
        
        if not slots:
            await update.message.reply_text("Сейчас нет доступных слотов. Создайте свой через /add_movie.")
            return
        
        # Exclude slots where user already participates
        filtered = []
        for s in slots:
            if any(p.user_id == user_id for p in s.participants):
                continue
            filtered.append(s)
        slots = filtered
        
        # Filter out slots without movies
        slots = [s for s in slots if s.movie is not None]
        
        if not slots:
            await update.message.reply_text("Сейчас нет доступных слотов. Создайте свой через /add_movie.")
            return
        
        # Exclude watched movies using user votes (by kp id)
        from bot.database.models import UserVote as UserVoteModel
        try:
            user_votes = db.query(UserVoteModel).filter(UserVoteModel.user_id == user_id).all()
            exclude_kp_ids = {v.kinopoisk_id for v in user_votes if v.kinopoisk_id}
        except Exception as e:
            logger.warning(f"Error fetching user votes for user {user_id}: {e}")
            exclude_kp_ids = set()
        
        try:
            scored = MatchingService.annotate_slots_by_interest(db, user_id, slots, exclude_kp_ids)
        except Exception as e:
            logger.error(f"Error in annotate_slots_by_interest for user {user_id}: {e}", exc_info=True)
            # Fallback: show all slots without scoring
            scored = [(slot, 0.0) for slot in slots]
        
        if not scored:
            await update.message.reply_text("Подходящих рекомендаций нет. Добавьте интересные фильмы через /add_movie.")
            return
        
        text_lines = ["🎯 <b>Рекомендованные слоты:</b>\n"]
        buttons = []
        for i, (slot, score) in enumerate(scored[:20], 1):
            if not slot.movie:
                continue
            participants_count = len(slot.participants) if slot.participants else 0
            needed = max(0, slot.min_participants - participants_count)
            stars = max(0, min(3, int(round(score * 3))))
            stars_text = f" {'⭐'*stars}" if stars > 0 else ""
            try:
                datetime_str = slot.datetime.strftime('%d.%m.%Y %H:%M') if slot.datetime else "Дата не указана"
                text_lines.append(
                    f"{i}. {slot.movie.title} — {datetime_str}{stars_text} "
                    f"({participants_count}/{slot.min_participants}, нужно еще {needed})"
                )
                btn_text = f"{slot.movie.title[:18]} {slot.datetime.strftime('%d.%m %H:%M') if slot.datetime else 'N/A'}{stars_text}"
                buttons.append([InlineKeyboardButton(btn_text, callback_data=f"join_slot:{slot.id}")])
            except Exception as e:
                logger.warning(f"Error formatting slot {slot.id}: {e}")
                continue
        
        if not buttons:
            await update.message.reply_text("Подходящих рекомендаций нет. Добавьте интересные фильмы через /add_movie.")
            return
        
        await update.message.reply_text(
            "\n".join(text_lines),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in recommend_command for user {user_id}: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Произошла ошибка при получении рекомендаций. Попробуйте позже."
        )
    finally:
        db.close()


