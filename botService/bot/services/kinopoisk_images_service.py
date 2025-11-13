"""Service for fetching movie images from Kinopoisk API"""
import logging
import requests
from typing import Optional, List, Dict
from bot.config import Config

logger = logging.getLogger(__name__)


class KinopoiskImagesService:
    """Service for fetching movie images from Kinopoisk API"""
    
    BASE_URL = "https://kinopoiskapiunofficial.tech/api/v2.2"
    
    @staticmethod
    def get_movie_images(kinopoisk_id: str, image_type: str = "POSTER", page: int = 1) -> Optional[List[Dict]]:
        """
        Get movie images by Kinopoisk ID
        
        Args:
            kinopoisk_id: Kinopoisk movie ID
            image_type: Type of images (POSTER, STILL, SHOOTING, FAN_ART, etc.)
            page: Page number (default: 1)
            
        Returns:
            List of image dictionaries or None if error
        """
        if not Config.KINOPOISK_API_KEY:
            logger.error("KINOPOISK_API_KEY is not configured")
            return None
            
        try:
            headers = {"X-API-KEY": Config.KINOPOISK_API_KEY}
            url = f"{KinopoiskImagesService.BASE_URL}/films/{kinopoisk_id}/images"
            
            params = {
                "type": image_type,
                "page": page
            }
            
            logger.info(f"Fetching {image_type} images for movie {kinopoisk_id}")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                images = data.get("items", [])
                logger.info(f"Found {len(images)} {image_type} images for movie {kinopoisk_id}")
                return images
            else:
                logger.error(f"Failed to fetch images: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching movie images: {e}")
            return None
    
    @staticmethod
    def get_best_poster(kinopoisk_id: str) -> Optional[str]:
        """
        Get the best poster URL for a movie
        
        Args:
            kinopoisk_id: Kinopoisk movie ID
            
        Returns:
            Best poster URL or None if not found
        """
        posters = KinopoiskImagesService.get_movie_images(kinopoisk_id, "POSTER")
        
        if not posters:
            logger.warning(f"No posters found for movie {kinopoisk_id}")
            return None
        
        # Sort by preview URL availability and take the first one
        for poster in posters:
            preview_url = poster.get("previewUrl")
            image_url = poster.get("imageUrl")
            
            # Prefer preview URL (smaller size, better for avatars)
            if preview_url:
                logger.info(f"Selected preview poster: {preview_url}")
                return preview_url
            elif image_url:
                logger.info(f"Selected full poster: {image_url}")
                return image_url
        
        logger.warning(f"No valid poster URLs found for movie {kinopoisk_id}")
        return None
    
    @staticmethod
    def download_image(image_url: str) -> Optional[bytes]:
        """
        Download image from URL
        
        Args:
            image_url: URL of the image to download
            
        Returns:
            Image bytes or None if error
        """
        try:
            logger.info(f"Downloading image from: {image_url}")
            response = requests.get(image_url, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Successfully downloaded image ({len(response.content)} bytes)")
                return response.content
            else:
                logger.error(f"Failed to download image: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return None