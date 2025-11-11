"""Validation utilities"""
import re
from datetime import datetime
from typing import Optional, Tuple

def validate_kinopoisk_url(url: str) -> bool:
    """Validate Kinopoisk URL"""
    pattern = r'https?://(www\.)?(kinopoisk\.ru|kinozal\.tv)/.*'
    return bool(re.match(pattern, url, re.IGNORECASE))


def validate_imdb_url(url: str) -> bool:
    """Validate IMDb URL"""
    pattern = r'https?://(www\.)?imdb\.com/.*'
    return bool(re.match(pattern, url, re.IGNORECASE))


def validate_movie_url(url: str) -> bool:
    """Validate movie URL (Kinopoisk or IMDb)"""
    return validate_kinopoisk_url(url) or validate_imdb_url(url)


def parse_datetime(date_str: str) -> Optional[datetime]:
    """Parse datetime from string format DD.MM.YYYY HH:MM"""
    try:
        return datetime.strptime(date_str, "%d.%m.%Y %H:%M")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
        except ValueError:
            return None


def validate_rating(score: int) -> bool:
    """Validate rating score (1-5)"""
    return 1 <= score <= 5

