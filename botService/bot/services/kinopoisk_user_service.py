"""Service to fetch and store Kinopoisk user votes"""
import logging
from typing import Optional
import requests

from bot.config import Config
from sqlalchemy.orm import Session
from bot.database.repositories import UserKinopoiskRepository, UserVoteRepository

logger = logging.getLogger(__name__)

class KinopoiskUserService:
    BASE_URL = "https://kinopoiskapiunofficial.tech/api/v1/kp_users"
    
    @staticmethod
    def set_user_kp_id(db: Session, user_id: int, kp_user_id: str) -> None:
        UserKinopoiskRepository.set_kp_user_id(db, user_id, kp_user_id)
    
    @staticmethod
    def fetch_and_store_votes(db: Session, user_id: int) -> int:
        """
        Fetch all votes for the user from Kinopoisk API and store them.
        Returns number of votes stored/updated.
        """
        record = UserKinopoiskRepository.get_by_user_id(db, user_id)
        if not record:
            raise ValueError("Kinopoisk user id is not linked. Use /link_kp first.")
        
        kp_user_id = record.kp_user_id
        headers = {"X-API-KEY": Config.KINOPOISK_API_KEY}
        
        page = 1
        total_pages = 1
        stored = 0
        
        while page <= total_pages:
            url = f"{KinopoiskUserService.BASE_URL}/{kp_user_id}/votes?page={page}"
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                logger.error(f"Failed to fetch KP votes for {kp_user_id}, status={resp.status_code}, body={resp.text[:200]}")
                break
            
            data = resp.json()
            total_pages = data.get("totalPages", 1) or 1
            items = data.get("items", []) or []
            
            for item in items:
                try:
                    kinopoisk_id = str(item.get("kinopoiskId"))
                    title = item.get("nameRu") or item.get("nameEn") or item.get("nameOriginal")
                    year_raw = item.get("year")
                    year = None
                    try:
                        year = int(year_raw) if year_raw is not None else None
                    except Exception:
                        year = None
                    movie_type = item.get("type")
                    poster_url = item.get("posterUrlPreview") or item.get("posterUrl")
                    user_rating = int(item.get("userRating")) if item.get("userRating") is not None else None
                    if not kinopoisk_id or user_rating is None:
                        continue
                    
                    UserVoteRepository.upsert_vote(
                        db=db,
                        user_id=user_id,
                        kinopoisk_id=kinopoisk_id,
                        title=title,
                        year=year,
                        movie_type=movie_type,
                        user_rating=user_rating,
                        poster_url=poster_url
                    )
                    stored += 1
                except Exception as e:
                    logger.warning(f"Failed to process vote item: {e}")
            
            page += 1
        
        return stored


