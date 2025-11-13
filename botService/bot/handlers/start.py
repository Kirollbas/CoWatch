"""Start and help command handlers"""
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session

from bot.database.session import SessionLocal
from bot.database.repositories import UserRepository
from bot.utils.keyboards import get_main_menu_keyboard


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with deep link support"""
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
        
        # Check for deep link parameters
        if context.args:
            param = context.args[0]
            
            # Handle group creation deep link
            if param.startswith("movie_"):
                await handle_group_creation(update, context, param, db)
                return
        
        # Default welcome message
        welcome_text = (
            f"Привет, {user.first_name}! 👋\n\n"
            "Добро пожаловать в <b>CoWatch</b> - бот для совместного просмотра фильмов и сериалов!\n\n"
            "🎬 Находите людей для просмотра\n"
            "💬 Обсуждайте увиденное\n"
            "⭐ Получайте рейтинги за активность\n\n"
            "🔗 Чтобы улучшить рекомендации, свяжите аккаунт Кинопоиска: /link_kp\n"
            "🎯 Посмотреть все рекомендованные слоты: /recommend\n\n"
            "Используйте /help для списка команд."
        )
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
    finally:
        db.close()


async def handle_group_creation(update: Update, context: ContextTypes.DEFAULT_TYPE, param: str, db: Session):
    """Handle group creation from deep link"""
    import logging
    from bot.database.repositories import SlotRepository
    
    logger = logging.getLogger(__name__)
    
    try:
        # Extract slot ID from parameter (movie_123 -> 123)
        slot_id = int(param.split("_")[1])
        logger.info(f"Group creation requested for slot {slot_id}")
        
        # Store slot_id in user context for later use in group setup
        context.user_data['pending_slot_id'] = slot_id
        
        # Get slot information
        slot = SlotRepository.get_by_id(db, slot_id)
        if not slot:
            await update.message.reply_text("❌ Слот не найден.")
            return
        
        # Check if slot is still active and user is participant
        user_id = update.effective_user.id
        is_participant = any(p.user_id == user_id for p in slot.participants)
        
        if not is_participant:
            await update.message.reply_text("❌ Вы не являетесь участником этого слота.")
            return
        
        # Check if slot is already processed (room created)
        if slot.status == "full":
            await update.message.reply_text(
                f"✅ Группа для этого слота уже создана!\n\n"
                f"🎬 Фильм: {slot.movie.title}\n"
                f"📅 Время: {slot.datetime.strftime('%d.%m.%Y в %H:%M')}\n\n"
                f"Группа уже настроена и готова к использованию."
            )
            return
        
        # Check if slot is not open (can't create group)
        if slot.status != "open":
            await update.message.reply_text(
                f"❌ Этот слот больше не доступен для создания группы.\n\n"
                f"🎬 Фильм: {slot.movie.title}\n"
                f"📊 Статус: {slot.status}"
            )
            return
        
        # Create group creation instructions
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        # Create a button that opens group creation dialog
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "👥 Создать группу с участниками",
                url=f"tg://resolve?domain=telegram&startgroup=cowatch_{slot_id}"
            )]
        ])
        
        group_msg = f"""🎬 **Создание группы для просмотра**

**Фильм:** {slot.movie.title}
**Время:** {slot.datetime.strftime('%d.%m.%Y в %H:%M')}
**Участники:** {len(slot.participants)}

🤖 **Автоматическое создание:**
1. Нажмите кнопку ниже
2. Telegram откроет диалог создания группы
3. Добавьте участников из слота
4. Бот автоматически отправит ссылку остальным

💡 **Это займет 30 секунд!**"""
        
        await update.message.reply_text(
            group_msg,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        # Also send a fallback message with manual instructions
        participants_info = []
        for participant in slot.participants:
            try:
                user_info = await context.bot.get_chat(participant.user_id)
                if user_info.username:
                    participants_info.append(f"• @{user_info.username} ({user_info.first_name})")
                else:
                    participants_info.append(f"• {user_info.first_name}")
            except:
                if participant.user_id == 999888777:
                    participants_info.append(f"• @petontyapa")
                else:
                    participants_info.append(f"• User {participant.user_id}")
        
        manual_msg = f"""📱 **Участники для добавления в группу:**

{chr(10).join(participants_info)}

**Название группы:** 🎬 {slot.movie.title} - {slot.datetime.strftime('%d.%m')}

💡 Если автоматическое создание не работает, создайте группу вручную и добавьте всех участников."""
        
        await update.message.reply_text(manual_msg, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error handling group creation: {e}")
        await update.message.reply_text("❌ Ошибка при создании группы. Попробуйте позже.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "📖 <b>Справка по командам:</b>\n\n"
        "/start - Начать работу с ботом\n"
        "/recommend - Рекомендованные слоты по вашим предпочтениям\n"
        "/link_kp - Привязать ваш ID на Кинопоиске (для рекомендаций)\n"
        "/add_movie - Добавить фильм/сериал для просмотра\n"
        "/my_slots - Мои созданные слоты\n"
        "/my_rooms - Мои активные комнаты\n"
        "/profile - Мой профиль и рейтинг\n"
        "/rate - Оценить участников после обсуждения\n"
        "/cancel - Отменить участие в слоте\n"
        "/help - Показать эту справку\n\n"
        "<b>Как это работает:</b>\n"
        "1. Свяжите Кинопоиск через /link_kp (по желанию, для лучших рекомендаций)\n"
        "2. Откройте рекомендации через /recommend и присоединяйтесь к слотам\n"
        "3. Или добавьте фильм через /add_movie и создайте свой слот\n"
        "4. Когда наберется минимум участников — создастся комната\n"
        "5. После просмотра оцените участников через /rate"
    )
    
    await update.message.reply_text(help_text, parse_mode="HTML")

