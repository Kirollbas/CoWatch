"""Handlers for linking Kinopoisk account and importing votes"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session

from bot.database.session import SessionLocal
from bot.services.kinopoisk_user_service import KinopoiskUserService
from bot.utils.states import set_state, get_state, clear_state
from bot.config import Config

logger = logging.getLogger(__name__)


async def link_kp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /link_kp command - ask for KP user id"""
    try:
        user_id = update.effective_user.id
        logger.info(f"User {user_id} called /link_kp")
        
        # Check if API key is configured
        if not Config.KINOPOISK_API_KEY:
            await update.message.reply_text(
                "⚠️ API ключ Kinopoisk не настроен.\n\n"
                "Для работы функции /link_kp необходимо:\n"
                "1. Получить API ключ на https://kinopoiskapiunofficial.tech/\n"
                "2. Добавить в .env файл:\n"
                "   KINOPOISK_API_KEY=ваш_ключ\n\n"
                "После настройки API ключа команда будет работать."
            )
            return
        
        await update.message.reply_text(
            "Отправьте ваш ID пользователя на Кинопоиске.\n\n"
            "Где взять ID:\n"
            "1) Откройте ваш профиль на kinopoisk.ru\n"
            "2) Скопируйте число в адресной строке (после /user/)\n\n"
            "Пример: https://www.kinopoisk.ru/user/1234567/ → ваш ID: 1234567"
        )
        set_state(user_id, "waiting_for_kp_id")
    except Exception as e:
        logger.error(f"Error in link_kp_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Произошла ошибка при выполнении команды. Попробуйте позже."
        )


async def handle_kp_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process KP user id, fetch votes and store them"""
    user_id = update.effective_user.id
    
    try:
        if get_state(user_id) != "waiting_for_kp_id":
            logger.debug(f"User {user_id} not in waiting_for_kp_id state")
            return
        
        if not update.message or not update.message.text:
            logger.warning(f"User {user_id} sent empty message")
            return
        
        kp_id_text = update.message.text.strip()
        
        # Try to extract ID from URL if user sent full URL
        if "/user/" in kp_id_text:
            import re
            match = re.search(r"/user/(\d+)", kp_id_text)
            if match:
                kp_id_text = match.group(1)
                logger.info(f"Extracted KP ID {kp_id_text} from URL")
        
        if not kp_id_text.isdigit():
            await update.message.reply_text(
                "❌ Некорректный ID. Отправьте только число или ссылку на профиль.\n\n"
                "Примеры:\n"
                "• 1234567\n"
                "• https://www.kinopoisk.ru/user/1234567/"
            )
            return
        
        # Check API key
        if not Config.KINOPOISK_API_KEY:
            await update.message.reply_text(
                "❌ API ключ Kinopoisk не настроен. Невозможно импортировать оценки."
            )
            clear_state(user_id)
            return
        
        db: Session = SessionLocal()
        try:
            # Save mapping and import votes
            logger.info(f"Linking KP ID {kp_id_text} to user {user_id}")
            KinopoiskUserService.set_user_kp_id(db, user_id, kp_id_text)
            await update.message.reply_text("🔄 Импортирую ваши оценки с Кинопоиска...")
            
            try:
                count = KinopoiskUserService.fetch_and_store_votes(db, user_id)
                if count > 0:
                    await update.message.reply_text(
                        f"✅ Импортировано/обновлено оценок: {count}\n\n"
                        f"Теперь я буду предлагать слоты с участниками с похожими предпочтениями."
                    )
                else:
                    await update.message.reply_text(
                        "⚠️ Не найдено оценок для импорта.\n\n"
                        "Убедитесь, что:\n"
                        "• ID пользователя правильный\n"
                        "• У вас есть оценки на Кинопоиске"
                    )
            except ValueError as e:
                logger.error(f"ValueError in fetch_and_store_votes: {e}")
                await update.message.reply_text(f"❌ Ошибка: {e}")
            except Exception as e:
                logger.error(f"Error fetching votes: {e}", exc_info=True)
                await update.message.reply_text(
                    f"❌ Не удалось импортировать оценки: {e}\n\n"
                    "Возможные причины:\n"
                    "• Неверный API ключ\n"
                    "• Проблемы с сетью\n"
                    "• Неверный ID пользователя"
                )
        finally:
            db.close()
            clear_state(user_id)
    except Exception as e:
        logger.error(f"Error in handle_kp_id: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке ID. Попробуйте позже."
        )
        clear_state(user_id)


