"""Handlers for linking Kinopoisk account and importing votes"""
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session

from bot.database.session import SessionLocal
from bot.services.kinopoisk_user_service import KinopoiskUserService
from bot.utils.states import set_state, get_state, clear_state


async def link_kp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /link_kp command - ask for KP user id"""
    await update.message.reply_text(
        "Отправьте ваш ID пользователя на Кинопоиске.\n\n"
        "Где взять ID:\n"
        "1) Откройте ваш профиль на kinopoisk.ru\n"
        "2) Скопируйте число в адресной строке (после /user/)\n\n"
        "Пример: https://www.kinopoisk.ru/user/1234567/ → ваш ID: 1234567"
    )
    set_state(update.effective_user.id, "waiting_for_kp_id")


async def handle_kp_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process KP user id, fetch votes and store them"""
    user_id = update.effective_user.id
    if get_state(user_id) != "waiting_for_kp_id":
        return
    
    kp_id_text = update.message.text.strip()
    if not kp_id_text.isdigit():
        await update.message.reply_text("❌ Некорректный ID. Отправьте только число, например: 1234567")
        return
    
    db: Session = SessionLocal()
    try:
        # Save mapping and import votes
        KinopoiskUserService.set_user_kp_id(db, user_id, kp_id_text)
        await update.message.reply_text("🔄 Импортирую ваши оценки с Кинопоиска...")
        
        try:
            count = KinopoiskUserService.fetch_and_store_votes(db, user_id)
            await update.message.reply_text(f"✅ Импортировано/обновлено оценок: {count}\n\n"
                                            f"Теперь я буду предлагать слоты с участниками с похожими предпочтениями.")
        except Exception as e:
            await update.message.reply_text(f"❌ Не удалось импортировать оценки: {e}")
    finally:
        db.close()
        clear_state(user_id)


