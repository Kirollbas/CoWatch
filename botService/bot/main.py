"""Main bot file"""
import logging
import sys
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes
)
from datetime import datetime

from bot.config import Config
from bot.handlers.start import start_command, help_command
from bot.handlers.movie import (
    add_movie_command, handle_movie_url, create_slot_callback,
    handle_slot_datetime, handle_min_participants, find_slots_callback
)
from bot.handlers.slots import (
    my_slots_command, join_slot_callback, cancel_command, leave_slot_callback,
    create_group_callback
)
from bot.handlers.profile import profile_command, my_rooms_command
from bot.handlers.rating import rate_command, rate_user_callback
from bot.handlers.group import handle_bot_added_to_group
from bot.utils.states import check_state

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages based on user state"""
    user_id = update.effective_user.id
    
    # Check if user is waiting for movie URL
    if check_state(user_id, "waiting_for_movie_url"):
        await handle_movie_url(update, context)
        return
    
    # Check if user is waiting for slot datetime
    if check_state(user_id, "waiting_for_slot_datetime:"):
        await handle_slot_datetime(update, context)
        return
    
    # Check if user is waiting for min participants
    if check_state(user_id, "waiting_for_min_participants|"):
        await handle_min_participants(update, context)
        return
    
    # Default: echo message
    await update.message.reply_text(
        "Используйте команды для работы с ботом. /help - справка."
    )


def main():
    """Main function to start the bot"""
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Create application
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add_movie", add_movie_command))
    application.add_handler(CommandHandler("my_slots", my_slots_command))
    application.add_handler(CommandHandler("my_rooms", my_rooms_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("rate", rate_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Register callback query handlers
    application.add_handler(CallbackQueryHandler(create_slot_callback, pattern=r"^create_slot:"))
    application.add_handler(CallbackQueryHandler(find_slots_callback, pattern=r"^find_slots:"))
    application.add_handler(CallbackQueryHandler(join_slot_callback, pattern=r"^join_slot:"))
    application.add_handler(CallbackQueryHandler(leave_slot_callback, pattern=r"^leave_slot:"))
    application.add_handler(CallbackQueryHandler(create_group_callback, pattern=r"^create_group:"))
    application.add_handler(CallbackQueryHandler(rate_user_callback, pattern=r"^rate_user:"))
    
    # Register chat member handler for group management
    from telegram.ext import ChatMemberHandler
    application.add_handler(ChatMemberHandler(handle_bot_added_to_group, ChatMemberHandler.MY_CHAT_MEMBER))
    
    # Register message handler (must be last)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Initialize database
    logger.info("Initializing database...")
    try:
        from bot.database.init_db import init_database
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        sys.exit(1)
    
    # Start bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

