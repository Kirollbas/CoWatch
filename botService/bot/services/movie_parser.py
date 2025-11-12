"""Movie parser service (stub implementation)"""
import re
import requests
from typing import Optional, Dict
from bot.constants import MovieType
from bot.config import Config
from bot.database.models import Movie

class MovieParser:
    """Parser for movie links (stub - returns test data)"""
    
    @staticmethod
    def parse_url(url: str) -> Optional[Dict]:
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
        if source == "kinopoisk":
            match = re.search(r"film/(\d+)", url)
            return match.group(1) if match else None
        elif source == "imdb":
            match = re.search(r"(tt\d+)", url)
            return match.group(1) if match else None
        return None
    
    @staticmethod
    def _parse_imdb(imdb_id: str) -> Optional[Dict]:
        if not imdb_id:
            return None

        headers = {"X-API-KEY": Config.KINOPOISK_API_KEY}
        url = f"https://kinopoiskapiunofficial.tech/api/v2.2/films?imdbId={imdb_id}"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None

        data = resp.json()

        if "items" in data and len(data["items"]) > 0:
            return MovieParser._map_kinopoisk_data(data["items"][0])

        return None

    
    @staticmethod
    def _parse_kinopoisk(kinopoisk_id: str) -> Optional[Dict]:
        if not kinopoisk_id:
            return None

        headers = {"X-API-KEY": Config.KINOPOISK_API_KEY}
        url = f"https://kinopoiskapiunofficial.tech/api/v2.2/films/{kinopoisk_id}"

        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None

        data = resp.json()
        return MovieParser._map_kinopoisk_data(data)
    
    @staticmethod
    def _map_kinopoisk_data(data: Dict) -> Dict:
        
        kp_type = data.get("type", "").upper()
        if kp_type == "FILM":
            movie_type = MovieType.MOVIE
        elif kp_type == "TV_SERIES":
            movie_type = MovieType.SERIES
        else:
            movie_type = MovieType.MOVIE
        
        return {
            "title": data.get("nameRu") or data.get("nameEn") or data.get("nameOriginal"),
            "year": data.get("year"),
            "type": movie_type,
            "kinopoisk_id": str(data.get("kinopoiskId")),
            "imdb_id": str(data.get("imdbId")),
            "description": data.get("description"),
            "poster_url": data.get("posterUrlPreview") or data.get("posterUrl")
        }
