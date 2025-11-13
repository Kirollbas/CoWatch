"""Message formatting utilities"""
from datetime import datetime
from bot.database.models import Movie, Slot, User, Room

def format_movie_info(movie: Movie) -> str:
    """Format movie information for display"""
    text = f"🎬 <b>{movie.title}</b>"
    if movie.name_original and movie.name_original != movie.title:
        text += f" ({movie.name_original})"
    if movie.year:
        text += f" ({movie.year})"
    text += f"\nТип: {movie.type}"
    
    # Ratings
    ratings_parts = []
    if movie.rating_kinopoisk:
        ratings_parts.append(f"Кинопоиск: {movie.rating_kinopoisk:.1f} ⭐")
    if movie.rating_imdb:
        ratings_parts.append(f"IMDb: {movie.rating_imdb:.1f} ⭐")
    if movie.rating:
        ratings_parts.append(f"Общий: {movie.rating:.1f} ⭐")
    
    if ratings_parts:
        text += "\n" + " | ".join(ratings_parts)
    
    # Additional metadata
    metadata_parts = []
    if movie.film_length:
        hours = movie.film_length // 60
        minutes = movie.film_length % 60
        if hours > 0:
            metadata_parts.append(f"⏱ {hours}ч {minutes}м")
        else:
            metadata_parts.append(f"⏱ {minutes}м")
    if movie.age_rating:
        metadata_parts.append(f"🔞 {movie.age_rating}")
    
    if metadata_parts:
        text += "\n" + " | ".join(metadata_parts)
    
    # Genres and countries
    if movie.genres:
        import json
        try:
            genres_list = json.loads(movie.genres)
            if genres_list:
                text += f"\n🎭 {', '.join(genres_list[:3])}"  # Показываем первые 3 жанра
        except:
            pass
    
    if movie.slogan:
        text += f"\n💬 <i>{movie.slogan}</i>"
    
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

