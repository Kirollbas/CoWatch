"""Recommended slots listing based on user KP preferences"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session

from bot.database.session import SessionLocal
from bot.database.repositories import SlotRepository
from bot.services.matching import MatchingService
from bot.database.models import SlotParticipant


async def recommend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recommended slots ranked by movie interest; exclude watched movies"""
    user_id = update.effective_user.id
    db: Session = SessionLocal()
    try:
        # All open slots
        slots = SlotRepository.get_all_open(db)
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
        
        # Exclude watched movies using user votes (by kp id)
        from bot.database.models import UserVote as UserVoteModel
        user_votes = db.query(UserVoteModel).filter(UserVoteModel.user_id == user_id).all()
        exclude_kp_ids = {v.kinopoisk_id for v in user_votes if v.kinopoisk_id}
        
        scored = MatchingService.annotate_slots_by_interest(db, user_id, slots, exclude_kp_ids)
        if not scored:
            await update.message.reply_text("Подходящих рекомендаций нет. Добавьте интересные фильмы через /add_movie.")
            return
        
        text_lines = ["🎯 <b>Рекомендованные слоты:</b>\n"]
        buttons = []
        for i, (slot, score) in enumerate(scored[:20], 1):
            participants_count = len(slot.participants)
            needed = max(0, slot.min_participants - participants_count)
            stars = max(0, min(3, int(round(score * 3))))
            stars_text = f" {'⭐'*stars}" if stars > 0 else ""
            text_lines.append(
                f"{i}. {slot.movie.title} — {slot.datetime.strftime('%d.%m.%Y %H:%M')}{stars_text} "
                f"({participants_count}/{slot.min_participants}, нужно еще {needed})"
            )
            btn_text = f"{slot.movie.title[:18]} {slot.datetime.strftime('%d.%m %H:%M')}{stars_text}"
            buttons.append([InlineKeyboardButton(btn_text, callback_data=f"join_slot:{slot.id}")])
        
        await update.message.reply_text(
            "\n".join(text_lines),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="HTML"
        )
    finally:
        db.close()


