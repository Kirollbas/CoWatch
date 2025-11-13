"""Movie handler - add movie and create slots"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from datetime import datetime

from bot.database.session import SessionLocal
from bot.database.repositories import MovieRepository, SlotRepository, SlotParticipantRepository
from bot.database.models import SlotParticipant
from bot.services.movie_parser import MovieParser
from bot.services.matching import MatchingService
from bot.utils.validators import validate_movie_url
from bot.utils.keyboards import get_movie_actions_keyboard, get_slots_list_keyboard
from bot.utils.formatters import format_movie_info, format_slot_info
from bot.constants import MovieType
from bot.utils.states import set_state, clear_state, get_state

logger = logging.getLogger(__name__)


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
        # Parse movie data using Kinopoisk API
        movie_data = MovieParser.parse_url(url)
        
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
        
        # Show movie info and available slots
        from bot.database.repositories import UserRepository
        from bot.constants import SlotStatus
        
        # Get user's rating for compatibility check
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            # Create user if doesn't exist
            user = UserRepository.get_or_create(db, user_id, update.effective_user.first_name or "User")
        
        # Find existing slots for this movie (including all movies with same Kinopoisk ID)
        existing_slots = []
        if movie.kinopoisk_id:
            # Find all movies with same Kinopoisk ID
            from bot.database.models import Movie
            all_movies = db.query(Movie).filter(Movie.kinopoisk_id == movie.kinopoisk_id).all()
            for m in all_movies:
                existing_slots.extend(SlotRepository.get_by_movie(db, m.id))
        else:
            existing_slots = SlotRepository.get_by_movie(db, movie.id)
        available_slots = []
        user_full_slots = []  # Slots where user is participant and slot is full
        
        logger.info(f"DEBUG: Found {len(existing_slots)} existing slots for movie {movie.id}")
        
        for slot in existing_slots:
            logger.info(f"DEBUG: Slot {slot.id} - status: {slot.status}, participants: {len(slot.participants)}, min_participants: {slot.min_participants}")
            
            # Check if user is already participating
            is_participating = any(p.user_id == user_id for p in slot.participants)
            
            if slot.status == SlotStatus.FULL and is_participating:
                # User is in a full slot - show it with "Create group" option
                logger.info(f"DEBUG: Adding full slot {slot.id} where user is participating")
                user_full_slots.append(slot)
                continue
            
            if slot.status != SlotStatus.OPEN:
                logger.info(f"DEBUG: Skipping slot {slot.id} - status is {slot.status}, not OPEN")
                continue
                
            if is_participating:
                logger.info(f"DEBUG: Skipping slot {slot.id} - user {user_id} already participating")
                continue
                
            # Check if slot is full
            if slot.max_participants and len(slot.participants) >= slot.max_participants:
                logger.info(f"DEBUG: Skipping slot {slot.id} - slot is full ({len(slot.participants)}/{slot.max_participants})")
                continue
                
            logger.info(f"DEBUG: Adding slot {slot.id} to available slots")
            available_slots.append(slot)
        
        logger.info(f"DEBUG: Total available slots: {len(available_slots)}")
        
        # Show movie info and available slots
        movie_text = format_movie_info(movie)
        
        # Create combined keyboard with slots and create button
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        buttons = []
        
        # Show user's full slots first (ready for group creation)
        if user_full_slots:
            slots_text = "\n\n🎉 <b>Готовые слоты (можно создать группу):</b>\n"
            for i, slot in enumerate(user_full_slots, 1):
                participants_count = len(slot.participants)
                slots_text += f"{i}. {slot.datetime.strftime('%d.%m.%Y %H:%M')} "
                slots_text += f"({participants_count}/{slot.min_participants} участников) ✅\n"
                
                # Add "Create group" button for full slots
                button_text = f"🎬 Создать группу - {slot.datetime.strftime('%d.%m %H:%M')}"
                buttons.append([
                    InlineKeyboardButton(button_text, callback_data=f"create_group:{slot.id}")
                ])
        else:
            slots_text = ""
        
        # Show available slots to join (sorted by compatibility)
        if available_slots:
            if slots_text:
                slots_text += "\n📅 <b>Доступные слоты:</b>\n"
            else:
                slots_text = "\n\n📅 <b>Доступные слоты:</b>\n"
            
            # Score and sort by compatibility
            scored = MatchingService.annotate_slots_by_compatibility(db, user_id, available_slots)
            
            for i, (slot, score) in enumerate(scored, 1):
                participants_count = len(slot.participants)
                needed = slot.min_participants - participants_count
                stars = max(0, min(3, int(round(score * 3))))
                stars_text = f" {'⭐'*stars}" if stars > 0 else ""
                slots_text += f"{i}. {slot.datetime.strftime('%d.%m.%Y %H:%M')}{stars_text} "
                slots_text += f"({participants_count}/{slot.min_participants}, нужно еще {needed})\n"
            
            slots_text += "\n💡 Нажмите на слот чтобы присоединиться:"
            
            # Add slot buttons
            for (slot, score) in scored:
                participants_count = len(slot.participants)
                needed = slot.min_participants - participants_count
                stars = max(0, min(3, int(round(score * 3))))
                star_emoji = "⭐"*stars
                suffix = f" {star_emoji}" if stars > 0 else ""
                button_text = f"{slot.datetime.strftime('%d.%m %H:%M')} (нужно еще {needed}){suffix}"
                buttons.append([
                    InlineKeyboardButton(button_text, callback_data=f"join_slot:{slot.id}")
                ])
        
        # Always add create new slot button
        buttons.append([
            InlineKeyboardButton("➕ Создать новый слот", callback_data=f"create_slot:{movie.id}")
        ])
        
        keyboard = InlineKeyboardMarkup(buttons)
        
        if slots_text:
            await update.message.reply_text(
                movie_text + slots_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                movie_text + "\n\n💡 Нет доступных слотов. Создайте новый!",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        
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
        set_state(user_id, f"waiting_for_slot_datetime|{movie_id}")
        
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
    if not state or not state.startswith("waiting_for_slot_datetime|"):
        return
    
    movie_id = int(state.split("|")[1])
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
        set_state(user_id, f"waiting_for_min_participants|{movie_id}|{datetime_obj.isoformat()}")
        
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
    if not state or not state.startswith("waiting_for_min_participants|"):
        return
    
    parts = state.split("|")
    movie_id = int(parts[1])
    datetime_str = parts[2]
    datetime_obj = datetime.fromisoformat(datetime_str)
    
    from bot.config import Config
    
    min_participants = Config.MIN_PARTICIPANTS_DEFAULT
    if update.message.text and update.message.text.strip() != "/skip":
        try:
            min_participants = int(update.message.text.strip())
            if min_participants < 1:
                await update.message.reply_text("❌ Минимум участников должен быть не менее 1.")
                return
        except ValueError:
            await update.message.reply_text("❌ Введите число.")
            return
    
    db: Session = SessionLocal()
    try:
        # Check if similar slot already exists (same movie, same time, same min_participants)
        from bot.database.repositories import UserRepository
        from bot.services.room_manager import RoomManager
        from bot.database.repositories import RoomRepository
        from bot.constants import SlotStatus
        
        existing_slots = SlotRepository.get_by_movie(db, movie_id)
        matching_slot = None
        
        for slot in existing_slots:
            if (slot.datetime == datetime_obj and
                slot.min_participants == min_participants and
                slot.status == SlotStatus.OPEN):
                # Check if user is already participating
                is_participating = any(p.user_id == user_id for p in slot.participants)
                if is_participating:
                    # User is already in this exact slot
                    await update.message.reply_text(
                        f"✅ Вы уже участвуете в таком слоте!\n\n{format_slot_info(slot)}",
                        parse_mode="HTML"
                    )
                    clear_state(user_id)
                    return
                else:
                    # Check if slot is not full
                    if not slot.max_participants or len(slot.participants) < slot.max_participants:
                        matching_slot = slot
                        break
        
        if matching_slot:
            # Join existing slot instead of creating new one
            SlotParticipantRepository.add_participant(db, matching_slot.id, user_id)
            
            # Check if should create room
            updated_slot = SlotRepository.get_by_id(db, matching_slot.id)
            if RoomManager.should_create_room(updated_slot):
                # Create room
                room = RoomRepository.create(db, matching_slot.id)
                updated_slot.status = SlotStatus.FULL
                db.commit()
                
                # Create Telegram group
                await RoomManager.create_room_for_slot(updated_slot, context.bot)
                
                # Notify all participants (only real users, skip test users)
                real_user_ids = [890859555, 999888777]  # Add real user IDs here (you + @petontyapa)
                for participant in updated_slot.participants:
                    if participant.user_id != user_id and participant.user_id in real_user_ids:
                        try:
                            await context.bot.send_message(
                                chat_id=participant.user_id,
                                text=f"🎉 Комната создана!\n\n{format_slot_info(updated_slot)}",
                                parse_mode="HTML"
                            )
                        except Exception as e:
                            logger.error(f"Failed to notify user {participant.user_id}: {e}")
                
                await update.message.reply_text(
                    f"🎉 Найден идентичный слот! Вы присоединились и комната создана!\n\n{format_slot_info(updated_slot)}",
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text(
                    f"✅ Найден идентичный слот! Вы присоединились к нему!\n\n{format_slot_info(updated_slot)}",
                    parse_mode="HTML"
                )
        else:
            # Create new slot
            slot = SlotRepository.create(
                db=db,
                movie_id=movie_id,
                creator_id=user_id,
                datetime_obj=datetime_obj,
                min_participants=min_participants
            )
            
            # Add creator as participant
            SlotParticipantRepository.add_participant(db, slot.id, user_id)
            
            # Check if should create room immediately (for min_participants=1)
            updated_slot = SlotRepository.get_by_id(db, slot.id)
            if RoomManager.should_create_room(updated_slot):
                # Create room
                room = RoomRepository.create(db, slot.id)
                updated_slot.status = SlotStatus.FULL
                db.commit()
                
                # Create Telegram group
                await RoomManager.create_room_for_slot(updated_slot, context.bot)
                
                await update.message.reply_text(
                    f"🎉 Слот заполнен! Создаем группу...\n\n"
                    f"🎬 Фильм: {updated_slot.movie.title}\n"
                    f"📅 Время: {datetime_obj.strftime('%d.%m.%Y %H:%M')}\n"
                    f"👥 Участники: {len(updated_slot.participants)}"
                )
            else:
                await update.message.reply_text(
                    f"✅ Слот создан!\n\n"
                    f"Фильм: {slot.movie.title}\n"
                    f"Время: {datetime_obj.strftime('%d.%m.%Y %H:%M')}\n"
                    f"Минимум участников: {min_participants}\n\n"
                    "Ожидаем участников..."
                )
        
        clear_state(user_id)
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

