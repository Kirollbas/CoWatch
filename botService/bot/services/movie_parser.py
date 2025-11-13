"""Movie parser service with Kinopoisk API"""
import re
import json
import logging
import requests
from typing import Optional, Dict
from bot.constants import MovieType
from bot.config import Config

logger = logging.getLogger(__name__)

class MovieParser:
    """Parser for movie links using Kinopoisk API"""
    
    API_BASE_URL = "https://kinopoiskapiunofficial.tech/api/v2.2/films"
    
    @staticmethod
    def parse_url(url: str) -> Optional[Dict]:
        """Parse movie URL and return movie data"""
        url = url.strip().lower()

        if "kinopoisk" in url:
            movie_id = MovieParser.extract_id_from_url(url, "kinopoisk")
            return MovieParser._parse_kinopoisk(movie_id)

        elif "imdb" in url:
            movie_id = MovieParser.extract_id_from_url(url, "imdb")
            return MovieParser._parse_imdb(movie_id)

        return None

    @staticmethod
    def extract_id_from_url(url: str, source: str) -> Optional[str]:
        """Extract movie ID from URL"""
        if source == "kinopoisk":
            match = re.search(r"film/(\d+)", url)
            return match.group(1) if match else None
        elif source == "imdb":
            match = re.search(r"(tt\d+)", url)
            return match.group(1) if match else None
        return None
    
    @staticmethod
    def _parse_imdb(imdb_id: str) -> Optional[Dict]:
        """Parse IMDb ID by fetching from Kinopoisk API"""
        if not imdb_id:
            return None

        if not Config.KINOPOISK_API_KEY:
            logger.warning("Kinopoisk API key not configured")
            return None

        headers = {"X-API-KEY": Config.KINOPOISK_API_KEY}
        url = f"{MovieParser.API_BASE_URL}?imdbId={imdb_id}"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"Failed to fetch IMDb {imdb_id}: {resp.status_code}")
            return None

        data = resp.json()

        if "items" in data and len(data["items"]) > 0:
            return MovieParser._map_kinopoisk_data(data["items"][0])

        return None

    
    @staticmethod
    def _parse_kinopoisk(kinopoisk_id: str) -> Optional[Dict]:
        """Parse Kinopoisk ID by fetching from API"""
        if not kinopoisk_id:
            return None

        if not Config.KINOPOISK_API_KEY:
            logger.warning("Kinopoisk API key not configured")
            return None

        headers = {"X-API-KEY": Config.KINOPOISK_API_KEY}
        url = f"{MovieParser.API_BASE_URL}/{kinopoisk_id}"

        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"Failed to fetch Kinopoisk {kinopoisk_id}: {resp.status_code}")
            return None

        data = resp.json()
        return MovieParser._map_kinopoisk_data(data)
    
    @staticmethod
    def _map_kinopoisk_data(data: Dict) -> Dict:
        """Map Kinopoisk API response to our data format with full ratings and metadata"""
        kp_type = data.get("type", "").upper()
        if kp_type == "FILM":
            movie_type = MovieType.MOVIE
        elif kp_type == "TV_SERIES":
            movie_type = MovieType.SERIES
        else:
            movie_type = MovieType.MOVIE
        
        # Extract genres as comma-separated string (compatible with main)
        genres_list = []
        try:
            genres_list = [g.get("genre") for g in (data.get("genres") or []) if g.get("genre")]
        except Exception:
            genres_list = []
        genres = ", ".join(genres_list) if genres_list else None
        
        # Extract ratings
        rating_data = data.get('rating', {})
        rating = None
        rating_kinopoisk = None
        rating_imdb = None
        rating_film_critics = None
        rating_await = None
        rating_rf_critics = None
        
        if isinstance(rating_data, dict):
            rating = rating_data.get('kp') or rating_data.get('rating')
            rating_kinopoisk = rating_data.get('kp')
            rating_imdb = rating_data.get('imdb')
            rating_film_critics = rating_data.get('filmCritics')
            rating_await = rating_data.get('await')
            rating_rf_critics = rating_data.get('russianFilmCritics')
        
        # Extract additional metadata
        film_length = data.get('filmLength')
        age_rating = data.get('ageRating')
        slogan = data.get('slogan')
        
        # Extract countries as JSON string
        countries = None
        if data.get('countries'):
            countries = json.dumps([c.get('country', '') for c in data['countries']], ensure_ascii=False)
        
        title = data.get("nameRu") or data.get("nameEn") or data.get("nameOriginal")
        name_original = data.get("nameOriginal")
        
        result = {
            "title": title,
            "name_original": name_original,
            "year": data.get("year"),
            "type": movie_type,
            "kinopoisk_id": str(data.get("kinopoiskId") or ""),
            "imdb_id": str(data.get("imdbId") or ""),
            "description": data.get("description") or data.get("shortDescription"),
            "poster_url": data.get("posterUrlPreview") or data.get("posterUrl"),
            "genres": genres,
            # Full ratings support
            "rating": rating,
            "rating_kinopoisk": rating_kinopoisk,
            "rating_imdb": rating_imdb,
            "rating_film_critics": rating_film_critics,
            "rating_await": rating_await,
            "rating_rf_critics": rating_rf_critics,
            # Additional metadata
            "film_length": film_length,
            "age_rating": age_rating,
            "slogan": slogan,
            "countries": countries,
            # Full API data for update_from_api
            "api_data": data
        }
        
        logger.info(f"Successfully parsed: {title} ({data.get('year')})")
        return result
