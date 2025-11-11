"""Movie parser service (stub implementation)"""
from typing import Optional, Dict
from bot.database.models import Movie

class MovieParser:
    """Parser for movie links (stub - returns test data)"""
    
    @staticmethod
    def parse_url(url: str) -> Optional[Dict]:
        """
        Parse movie URL and return movie data
        Currently returns stub data - real implementation will parse Kinopoisk/IMDb
        """
        # Stub implementation - returns test data
        # In future: parse Kinopoisk/IMDb URLs and extract metadata
        
        # Simple detection based on URL
        if "kinopoisk" in url.lower():
            return {
                "title": "Тестовый фильм (Kinopoisk)",
                "year": 2024,
                "type": "movie",
                "kinopoisk_id": url.split("/")[-1] if "/" in url else None,
                "description": "Это тестовое описание фильма. В будущем здесь будет реальное описание с Kinopoisk.",
                "poster_url": None
            }
        elif "imdb" in url.lower():
            return {
                "title": "Test Movie (IMDb)",
                "year": 2024,
                "type": "movie",
                "imdb_id": url.split("/")[-1] if "/" in url else None,
                "description": "This is a test movie description. In future, real description from IMDb will be here.",
                "poster_url": None
            }
        else:
            # Default stub
            return {
                "title": "Тестовый фильм",
                "year": 2024,
                "type": "movie",
                "description": "Тестовое описание фильма",
                "poster_url": None
            }
    
    @staticmethod
    def extract_id_from_url(url: str, source: str) -> Optional[str]:
        """Extract movie ID from URL"""
        # Stub implementation
        if "/" in url:
            return url.split("/")[-1].split("?")[0]
        return None

