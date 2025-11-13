#!/usr/bin/env python3
"""Test script for Kinopoisk images service"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.services.kinopoisk_images_service import KinopoiskImagesService

def test_get_poster():
    """Test getting movie poster"""
    # Test with Batman 2022 (Kinopoisk ID: 590286)
    kinopoisk_id = "590286"
    
    print(f"🎬 Testing poster retrieval for movie ID: {kinopoisk_id}")
    
    # Get all poster images
    print("\n📸 Getting all poster images...")
    posters = KinopoiskImagesService.get_movie_images(kinopoisk_id, "POSTER")
    
    if posters:
        print(f"✅ Found {len(posters)} posters")
        for i, poster in enumerate(posters[:3]):  # Show first 3
            print(f"  {i+1}. Preview: {poster.get('previewUrl', 'N/A')}")
            print(f"     Full: {poster.get('imageUrl', 'N/A')}")
    else:
        print("❌ No posters found")
        return
    
    # Get best poster URL
    print("\n🏆 Getting best poster...")
    best_poster_url = KinopoiskImagesService.get_best_poster(kinopoisk_id)
    
    if best_poster_url:
        print(f"✅ Best poster URL: {best_poster_url}")
        
        # Try to download the image
        print("\n⬇️ Downloading poster...")
        image_data = KinopoiskImagesService.download_image(best_poster_url)
        
        if image_data:
            print(f"✅ Downloaded {len(image_data)} bytes")
            
            # Save to file for testing
            with open("test_poster.jpg", "wb") as f:
                f.write(image_data)
            print("💾 Saved as test_poster.jpg")
        else:
            print("❌ Failed to download image")
    else:
        print("❌ No best poster URL found")

def test_different_image_types():
    """Test getting different types of images"""
    kinopoisk_id = "590286"
    
    image_types = ["POSTER", "STILL", "SHOOTING", "FAN_ART", "WALLPAPER"]
    
    print(f"\n🎭 Testing different image types for movie ID: {kinopoisk_id}")
    
    for image_type in image_types:
        print(f"\n📷 Getting {image_type} images...")
        images = KinopoiskImagesService.get_movie_images(kinopoisk_id, image_type)
        
        if images:
            print(f"✅ Found {len(images)} {image_type} images")
            if images:
                first_image = images[0]
                print(f"   First image: {first_image.get('previewUrl', 'N/A')}")
        else:
            print(f"❌ No {image_type} images found")

if __name__ == "__main__":
    print("🧪 Testing Kinopoisk Images Service")
    print("=" * 50)
    
    test_get_poster()
    test_different_image_types()
    
    print("\n✅ Test completed!")