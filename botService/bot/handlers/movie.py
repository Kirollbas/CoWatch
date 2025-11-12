"""Movie handler - add movie and create slots"""
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session

from bot.database.session import SessionLocal
from bot.database.repositories import (
    MovieRepository, SlotRepository, SlotParticipantRepository,
    UserRepository, RoomRepository
)
from bot.database.models import SlotParticipant
from bot.services.movie_parser import MovieParser
from bot.services.matching import MatchingService
from bot.services.room_manager import RoomManager
from bot.utils.validators import validate_movie_url
from bot.utils.keyboards import get_movie_actions_keyboard, get_slots_list_keyboard, get_compatible_slots_keyboard
from bot.utils.formatters import format_movie_info, format_slot_info
from bot.constants import MovieType
from bot.utils.states import set_state, clear_state, get_state


async def add_movie_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add_movie command"""
    await update.message.reply_text(
        "Отправьте ссылку на фильм или сериал с Kinopoisk или IMDb:\n\n"
        "Примеры:\n"
        "• https://www.kinopoisk.ru/film/12345/\n"
        "• https://www.imdb.com/title/tt1234567/"
    )
    set_state(update.effective_user.id, "waiting_for_movie_url")


async def handle_movie_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle movie URL input"""
    user_id = update.effective_user.id
    url = update.message.text.strip()
    
    if get_state(user_id) != "waiting_for_movie_url":
        return
    
    # Validate URL
    if not validate_movie_url(url):
        await update.message.reply_text(
            "❌ Неверный формат ссылки. Пожалуйста, отправьте ссылку на Kinopoisk или IMDb."
        )
        return
    
    db: Session = SessionLocal()
    try:
        # Parse movie data (stub)
        parser = MovieParser()
        movie_data = parser.parse_url(url)
        
        if not movie_data:
            await update.message.reply_text("❌ Не удалось обработать ссылку. Попробуйте другую.")
            clear_state(user_id)
            return
        
        # Check if movie already exists
        movie = None
        if movie_data.get("kinopoisk_id"):
            movie = MovieRepository.find_by_kinopoisk_id(db, movie_data["kinopoisk_id"])
        elif movie_data.get("imdb_id"):
            movie = MovieRepository.find_by_imdb_id(db, movie_data["imdb_id"])
        
        # Create movie if not exists
        if not movie:
            movie = MovieRepository.create(
                db=db,
                title=movie_data["title"],
                year=movie_data.get("year"),
                movie_type=movie_data.get("type", MovieType.MOVIE),
                kinopoisk_id=movie_data.get("kinopoisk_id"),
                imdb_id=movie_data.get("imdb_id"),
                description=movie_data.get("description"),
                poster_url=movie_data.get("poster_url")
            )
        
        # Ensure user exists in database
        user = UserRepository.get_or_create(
            db,
            user_id,
            update.effective_user.username,
            update.effective_user.first_name
        )
        
        # Check for compatible slots and potentially auto-join
        await handle_movie_interest(update, context, db, movie, user)
        
        clear_state(user_id)
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}")
        clear_state(user_id)
    finally:
        db.close()


async def create_slot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle create_slot callback"""
    query = update.callback_query
    await query.answer()
    
    movie_id = int(query.data.split(":")[1])
    user_id = query.from_user.id
    
    db: Session = SessionLocal()
    try:
        movie = MovieRepository.get_by_id(db, movie_id)
        if not movie:
            await query.edit_message_text("❌ Фильм не найден.")
            return
        
        # Store state for conversation
        set_state(user_id, f"waiting_for_slot_datetime:{movie_id}")
        
        await query.edit_message_text(
            f"Создание слота для: <b>{movie.title}</b>\n\n"
            "Укажите дату и время в формате: <b>ДД.ММ.ГГГГ ЧЧ:ММ</b>\n\n"
            "Пример: 25.12.2024 20:00",
            parse_mode="HTML"
        )
    finally:
        db.close()


async def handle_slot_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle slot datetime input"""
    user_id = update.effective_user.id
    
    state = get_state(user_id)
    if not state or not state.startswith("waiting_for_slot_datetime:"):
        return
    
    movie_id = int(state.split(":")[1])
    datetime_str = update.message.text.strip()
    
    from bot.utils.validators import parse_datetime
    from datetime import datetime
    
    datetime_obj = parse_datetime(datetime_str)
    if not datetime_obj:
        await update.message.reply_text(
            "❌ Неверный формат даты. Используйте: <b>ДД.ММ.ГГГГ ЧЧ:ММ</b>\n"
            "Пример: 25.12.2024 20:00",
            parse_mode="HTML"
        )
        return
    
    # Check if datetime is in the future
    if datetime_obj <= datetime.now():
        await update.message.reply_text("❌ Время должно быть в будущем.")
        return
    
    db: Session = SessionLocal()
    try:
        from bot.config import Config
        
        # Ask for min participants
        set_state(user_id, f"waiting_for_min_participants:{movie_id}:{datetime_obj.isoformat()}")
        
        await update.message.reply_text(
            f"Время установлено: {datetime_obj.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Минимум участников? (по умолчанию: {Config.MIN_PARTICIPANTS_DEFAULT})\n"
            "Отправьте число или нажмите /skip для значения по умолчанию."
        )
    finally:
        db.close()


async def handle_min_participants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle min participants input"""
    user_id = update.effective_user.id
    
    state = get_state(user_id)
    if not state or not state.startswith("waiting_for_min_participants:"):
        return
    
    parts = state.split(":")
    movie_id = int(parts[1])
    datetime_str = parts[2]
    datetime_obj = datetime.fromisoformat(datetime_str)
    
    from bot.config import Config
    
    min_participants = Config.MIN_PARTICIPANTS_DEFAULT
    if update.message.text and update.message.text.strip() != "/skip":
        try:
            min_participants = int(update.message.text.strip())
            if min_participants < 2:
                await update.message.reply_text("❌ Минимум участников должен быть не менее 2.")
                return
        except ValueError:
            await update.message.reply_text("❌ Введите число.")
            return
    
    db: Session = SessionLocal()
    try:
        # Create slot
        slot = SlotRepository.create(
            db=db,
            movie_id=movie_id,
            creator_id=user_id,
            datetime_obj=datetime_obj,
            min_participants=min_participants
        )
        
        # Add creator as participant
        SlotParticipantRepository.add_participant(db, slot.id, user_id)
        
        clear_state(user_id)
        
        await update.message.reply_text(
            f"✅ Слот создан!\n\n"
            f"Фильм: {slot.movie.title}\n"
            f"Время: {datetime_obj.strftime('%d.%m.%Y %H:%M')}\n"
            f"Минимум участников: {min_participants}\n\n"
            "Ожидаем участников..."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при создании слота: {str(e)}")
        clear_state(user_id)
    finally:
        db.close()


async def find_slots_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle find_slots callback"""
    query = update.callback_query
    await query.answer()
    
    movie_id = int(query.data.split(":")[1])
    
    db: Session = SessionLocal()
    try:
        movie = MovieRepository.get_by_id(db, movie_id)
        if not movie:
            await query.edit_message_text("❌ Фильм не найден.")
            return
        
        slots = SlotRepository.get_by_movie(db, movie_id)
        
        if not slots:
            await query.edit_message_text(
                f"Для <b>{movie.title}</b> пока нет доступных слотов.\n\n"
                "Создайте новый слот!",
                parse_mode="HTML"
            )
            return
        
        slots_text = f"Доступные слоты для <b>{movie.title}</b>:\n\n"
        await query.edit_message_text(
            slots_text,
            reply_markup=get_slots_list_keyboard(slots),
            parse_mode="HTML"
        )
    finally:
        db.close()




async def handle_movie_interest(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                               db: Session, movie, user):
    """
    Handle when user expresses interest in a movie
    This is the core logic that checks for existing slots and creates rooms
    """
    user_id = user.id
    movie_id = movie.id
    
    # Find compatible slots for this movie
    compatible_slots = MatchingService.find_compatible_slots(db, movie_id, user_id)
    
    # Check if there's a slot ready for auto-join
    best_slot = MatchingService.find_best_slot_for_auto_join(db, movie_id, user_id)
    
    if best_slot:
        # Auto-join the user to the best compatible slot
        SlotParticipantRepository.add_participant(db, best_slot.id, user_id)
        
        # Check if room should be created after adding this participant
        db.refresh(best_slot)  # Refresh to get updated participants
        
        if RoomManager.should_create_room(best_slot):
            # Create room and notify all participants
            room = RoomManager.create_room_for_slot(db, best_slot)
            if room:
                # Notify all participants about room creation
                message = RoomManager.get_room_creation_message(room)
                RoomManager.notify_participants(context, room, message)
                
                # Schedule reminders (stub)
                RoomManager.schedule_movie_reminder(context, room)
                
                await update.message.reply_text(
                    f"🎉 <b>Отлично!</b>\n\n"
                    f"Вы автоматически присоединены к слоту для <b>{movie.title}</b>!\n\n"
                    f"Набралось достаточно участников, комната создана!\n\n"
                    f"{format_slot_info(best_slot)}",
                    parse_mode="HTML"
                )
                return
        
        # Slot joined but room not created yet
        await update.message.reply_text(
            f"✅ <b>Вы присоединились к слоту!</b>\n\n"
            f"{format_slot_info(best_slot)}\n\n"
            f"Ожидаем еще участников для создания комнаты...",
            parse_mode="HTML"
        )
        return
    
    # No auto-join, show movie info and available options
    movie_text = format_movie_info(movie)
    
    if compatible_slots:
        # Show compatible slots
        movie_text += f"\n\n🔍 <b>Найдены совместимые слоты:</b>"
        await update.message.reply_text(
            movie_text,
            parse_mode="HTML"
        )
        
        # Show compatible slots with enhanced keyboard
        slots_text = f"Совместимые слоты для <b>{movie.title}</b>:\n\n"
        slots_text += f"⭐ - слоты с совместимым рейтингом участников"
        await update.message.reply_text(
            slots_text,
            reply_markup=get_compatible_slots_keyboard(compatible_slots, movie.id),
            parse_mode="HTML"
        )
    else:
        # No compatible slots, show standard options
        movie_text += f"\n\n💡 <i>Совместимых слотов не найдено. Создайте новый слот или найдите существующие.</i>"
        await update.message.reply_text(
            movie_text,
            reply_markup=get_movie_actions_keyboard(movie.id),
            parse_mode="HTML"
        )


async def separator_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle separator callback (do nothing)"""
    query = update.callback_query
    await query.answer()
