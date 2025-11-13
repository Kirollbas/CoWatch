import logging
import requests
from typing import Optional
from bot.config import Config
from sqlalchemy.orm import Session
from bot.database.models import Slot, Movie
from bot.database.repositories import MovieRepository

logger = logging.getLogger(__name__)

class WatchTogetherService:

    API_BASE_URL = "https://api.w2g.tv/rooms/create.json"

    @staticmethod
    def create_wt_room(db: Session, slot: Slot) -> Optional[str]:
        # Check if API key is configured
        if not Config.WATCH_TOGETHER_API_KEY:
            logger.warning(f"Watch Together API key not configured, skipping room creation for slot {slot.id}")
            return None
            
        movie = MovieRepository.get_by_id(db, slot.movie_id)
        if not movie:
            logger.error(f"Movie with movie_id={slot.movie_id} not found")
            return None
        
        if movie.type == "series":
            share_url = f"https://flcksbr.top/series/{movie.kinopoisk_id}/"
        else:
            share_url = f"https://flcksbr.top/film/{movie.kinopoisk_id}/"
            
        payload = {
            "w2g_api_key": Config.WATCH_TOGETHER_API_KEY,
            "share": share_url,
        }

        try:
            response = requests.post(WatchTogetherService.API_BASE_URL, json=payload, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Network error creating W2G room for slot {slot.id}: {e}")
            return None

        data = response.json()
        streamkey = data.get("streamkey")
        if not streamkey:
            logger.error(f"W2G API returned no streamkey for slot {slot.id}, response: {data}")
            return None

        room_url = f"https://w2g.tv/rooms/{streamkey}"
        logger.info(f"Watch2Gether room created: {room_url} for slot {slot.id}")

        return room_url