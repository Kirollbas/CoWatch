"""Message formatting utilities"""
from datetime import datetime
from bot.database.models import Movie, Slot, User, Room

def format_movie_info(movie: Movie) -> str:
    """Format movie information for display"""
    text = f"🎬 <b>{movie.title}</b>"
    if movie.year:
        text += f" ({movie.year})"
    text += f"\nТип: {movie.type}"
    if movie.description:
        text += f"\n\n{movie.description[:200]}"
        if len(movie.description) > 200:
            text += "..."
    return text


def format_slot_info(slot: Slot) -> str:
    """Format slot information for display"""
    datetime_str = slot.datetime.strftime("%d.%m.%Y в %H:%M")
    participants_count = len(slot.participants)
    text = f"📅 <b>{slot.movie.title}</b>\n"
    text += f"Время: {datetime_str}\n"
    text += f"Участников: {participants_count}/{slot.min_participants}"
    if slot.max_participants:
        text += f" (макс: {slot.max_participants})"
    text += f"\nСтатус: {slot.status}"
    return text


def format_user_profile(user: User) -> str:
    """Format user profile for display"""
    text = f"👤 <b>Профиль</b>\n\n"
    text += f"Имя: {user.first_name}\n"
    if user.username:
        text += f"Username: @{user.username}\n"
    text += f"Рейтинг: {user.rating:.2f} ⭐\n"
    text += f"Всего оценок: {user.total_ratings}\n"
    text += f"Регистрация: {user.created_at.strftime('%d.%m.%Y')}"
    return text


def format_room_info(room: Room) -> str:
    """Format room information for display"""
    slot = room.slot
    datetime_str = slot.datetime.strftime("%d.%m.%Y в %H:%M")
    text = f"🏠 <b>Комната</b>\n\n"
    text += f"Фильм: {slot.movie.title}\n"
    text += f"Время просмотра: {datetime_str}\n"
    text += f"Статус: {room.status}"
    if room.telegram_group_id:
        text += f"\nГруппа: {room.telegram_group_id}"
    return text

