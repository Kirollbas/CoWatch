#!/usr/bin/env python3
"""Test script for database functionality"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from bot.database import (
    SessionLocal,
    UserRepository,
    MovieRepository,
    SlotRepository,
    SlotParticipantRepository,
    RoomRepository,
    RatingRepository,
    EpisodeRepository,
    CommentRepository,
    LikeRepository,
    WatchHistoryRepository,
    get_db_session,
)
from bot.constants import SlotStatus, RoomStatus, MovieType


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_basic_repositories(db):
    """Test basic repositories (User, Movie, Slot, etc.)"""
    print_section("Testing Basic Repositories")
    
    # 1. Create user
    print("1. Creating user...")
    user = UserRepository.get_or_create(
        db, 
        user_id=123456789,
        username="test_user",
        first_name="Test User"
    )
    print(f"   ✓ User created: ID={user.id}, Name={user.first_name}, Rating={user.rating}")
    
    # 2. Create movie
    print("2. Creating movie...")
    movie = MovieRepository.create(
        db,
        title="Test Movie",
        year=2024,
        movie_type=MovieType.MOVIE,
        description="A test movie for database testing"
    )
    print(f"   ✓ Movie created: ID={movie.id}, Title={movie.title}, Type={movie.type}")
    
    # 3. Create slot
    print("3. Creating slot...")
    slot_datetime = datetime.now(timezone.utc) + timedelta(days=1)
    slot = SlotRepository.create(
        db,
        movie_id=movie.id,
        creator_id=user.id,
        datetime_obj=slot_datetime,
        min_participants=2,
        max_participants=5
    )
    print(f"   ✓ Slot created: ID={slot.id}, Movie={slot.movie.title}, "
          f"DateTime={slot.datetime}, Status={slot.status}")
    
    # 4. Add participant
    print("4. Adding participant to slot...")
    participant = SlotParticipantRepository.add_participant(
        db,
        slot_id=slot.id,
        user_id=user.id
    )
    print(f"   ✓ Participant added: Slot={participant.slot_id}, User={participant.user_id}")
    
    # 5. Create room
    print("5. Creating room...")
    room = RoomRepository.create(db, slot_id=slot.id)
    print(f"   ✓ Room created: ID={room.id}, Slot={room.slot_id}, Status={room.status}")
    
    # 6. Create rating
    print("6. Creating rating...")
    # Need another user to rate
    user2 = UserRepository.get_or_create(
        db,
        user_id=987654321,
        username="test_user2",
        first_name="Test User 2"
    )
    SlotParticipantRepository.add_participant(db, slot_id=slot.id, user_id=user2.id)
    
    rating = RatingRepository.create(
        db,
        room_id=room.id,
        rater_id=user.id,
        rated_id=user2.id,
        score=5
    )
    print(f"   ✓ Rating created: Rater={rating.rater_id}, Rated={rating.rated_id}, Score={rating.score}")
    
    # 7. Update user rating
    print("7. Updating user rating...")
    UserRepository.update_rating(db, user2.id)
    user2_updated = UserRepository.get_by_id(db, user2.id)
    print(f"   ✓ User rating updated: Rating={user2_updated.rating}, Total={user2_updated.total_ratings}")
    
    return {
        'user_id': user.id,
        'movie_id': movie.id,
        'slot_id': slot.id,
        'room_id': room.id,
        'user2_id': user2.id
    }


def test_new_repositories(db, test_data):
    """Test new repositories (Episode, Comment, Like, WatchHistory)"""
    print_section("Testing New Repositories")
    
    user_id = test_data['user_id']
    room_id = test_data['room_id']
    
    # 1. Create series
    print("1. Creating series...")
    series = MovieRepository.create(
        db,
        title="Test Series",
        year=2024,
        movie_type=MovieType.SERIES,
        description="A test series for database testing"
    )
    print(f"   ✓ Series created: ID={series.id}, Title={series.title}, Type={series.type}")
    
    # 2. Create episode
    print("2. Creating episode...")
    episode = EpisodeRepository.create(
        db,
        series_id=series.id,
        season_number=1,
        episode_number=1,
        title="Pilot",
        description="First episode of the series",
        runtime_minutes=45
    )
    print(f"   ✓ Episode created: ID={episode.id}, S{episode.season_number}E{episode.episode_number}, "
          f"Title={episode.title}")
    
    # 3. Get episodes by series
    print("3. Getting episodes by series...")
    episodes = EpisodeRepository.get_by_series(db, series_id=series.id)
    print(f"   ✓ Found {len(episodes)} episode(s) for series")
    
    # 4. Create comment
    print("4. Creating comment...")
    comment = CommentRepository.create(
        db,
        room_id=room_id,
        user_id=user_id,
        episode_id=episode.id,
        content="Great episode! Really enjoyed it."
    )
    print(f"   ✓ Comment created: ID={comment.id}, Content='{comment.content[:30]}...'")
    
    # 5. Create reply comment
    print("5. Creating reply comment...")
    reply = CommentRepository.create(
        db,
        room_id=room_id,
        user_id=test_data['user2_id'],
        episode_id=episode.id,
        content="I agree!",
        reply_to_id=comment.id
    )
    print(f"   ✓ Reply created: ID={reply.id}, ReplyTo={reply.reply_to_id}")
    
    # 6. Get comments by room
    print("6. Getting comments by room...")
    comments = CommentRepository.get_by_room(db, room_id=room_id)
    print(f"   ✓ Found {len(comments)} comment(s) in room")
    
    # 7. Toggle like
    print("7. Toggling like on comment...")
    was_created, is_liked = LikeRepository.toggle_like(
        db,
        comment_id=comment.id,
        user_id=user_id
    )
    print(f"   ✓ Like toggled: Created={was_created}, IsLiked={is_liked}")
    
    # 8. Get likes count
    likes_count = LikeRepository.get_likes_count(db, comment_id=comment.id)
    print(f"   ✓ Likes count: {likes_count}")
    
    # 9. Toggle like again (unlike)
    print("8. Toggling like again (unlike)...")
    was_created2, is_liked2 = LikeRepository.toggle_like(
        db,
        comment_id=comment.id,
        user_id=user_id
    )
    print(f"   ✓ Like toggled: Created={was_created2}, IsLiked={is_liked2}")
    likes_count2 = LikeRepository.get_likes_count(db, comment_id=comment.id)
    print(f"   ✓ Likes count after unlike: {likes_count2}")
    
    # 10. Create watch history
    print("9. Creating watch history...")
    watch = WatchHistoryRepository.create_or_update(
        db,
        user_id=user_id,
        movie_id=series.id,
        episode_id=episode.id,
        room_id=room_id,
        progress_seconds=1800,  # 30 minutes
        completed=0
    )
    print(f"   ✓ Watch history created: ID={watch.id}, Progress={watch.progress_seconds}s, "
          f"Completed={watch.completed}")
    
    # 11. Update watch history
    print("10. Updating watch history...")
    watch_updated = WatchHistoryRepository.create_or_update(
        db,
        user_id=user_id,
        movie_id=series.id,
        episode_id=episode.id,
        room_id=room_id,
        progress_seconds=2700,  # 45 minutes
        completed=1  # Completed
    )
    print(f"   ✓ Watch history updated: Progress={watch_updated.progress_seconds}s, "
          f"Completed={watch_updated.completed}")
    
    # 12. Get user watch history
    print("11. Getting user watch history...")
    history = WatchHistoryRepository.get_user_history(db, user_id=user_id, limit=10)
    print(f"   ✓ Found {len(history)} watch history entry/entries")
    
    # 13. Get completed count
    completed_count = WatchHistoryRepository.get_completed_count(db, user_id=user_id)
    print(f"   ✓ Completed watches: {completed_count}")


def test_relationships(db):
    """Test relationships between models"""
    print_section("Testing Model Relationships")
    
    # Get a user with relationships
    user = UserRepository.get_by_id(db, user_id=123456789)
    if user:
        print(f"User: {user.first_name} (ID: {user.id})")
        print(f"  - Created slots: {len(user.created_slots)}")
        print(f"  - Slot participations: {len(user.slot_participations)}")
        print(f"  - Ratings given: {len(user.ratings_given)}")
        print(f"  - Ratings received: {len(user.ratings_received)}")
        print(f"  - Comments: {len(user.comments)}")
        print(f"  - Likes: {len(user.likes)}")
        print(f"  - Watch history: {len(user.watch_history)}")
    
    # Get a movie/series with episodes
    from bot.database.models import Movie
    series = db.query(Movie).filter(Movie.type == MovieType.SERIES).first()
    
    if series:
        print(f"\nSeries: {series.title} (ID: {series.id})")
        print(f"  - Episodes: {len(series.episodes)}")
        if series.episodes:
            for ep in series.episodes[:3]:  # Show first 3
                print(f"    * S{ep.season_number}E{ep.episode_number}: {ep.title or 'Untitled'}")


def test_queries(db):
    """Test various query methods"""
    print_section("Testing Query Methods")
    
    # Test slot queries
    print("1. Testing slot queries...")
    user = UserRepository.get_by_id(db, user_id=123456789)
    if user:
        created_slots = SlotRepository.get_by_creator(db, creator_id=user.id)
        print(f"   ✓ User created {len(created_slots)} slot(s)")
        
        participations = SlotRepository.get_user_participations(db, user_id=user.id)
        print(f"   ✓ User participates in {len(participations)} slot(s)")
    
    # Test episode queries
    print("2. Testing episode queries...")
    from bot.database.models import Movie
    series_list = db.query(Movie).filter(Movie.type == MovieType.SERIES).all()
    if series_list:
        series = series_list[0]
        episodes = EpisodeRepository.get_by_series_season(db, series_id=series.id, season_number=1)
        print(f"   ✓ Found {len(episodes)} episode(s) in season 1")
        
        episode = EpisodeRepository.find_by_series_season_episode(
            db, series_id=series.id, season_number=1, episode_number=1
        )
        if episode:
            print(f"   ✓ Found episode: {episode.title}")
    
    # Test comment queries
    print("3. Testing comment queries...")
    from bot.database.models import Room
    room_list = db.query(Room).limit(1).all()
    if room_list:
        room = room_list[0]
        comments = CommentRepository.get_by_room(db, room_id=room.id, limit=5)
        print(f"   ✓ Found {len(comments)} comment(s) in room")
        
        if comments:
            replies = CommentRepository.get_replies(db, comment_id=comments[0].id)
            print(f"   ✓ Found {len(replies)} reply/replies to first comment")


def main():
    """Main test function"""
    print("\n" + "="*60)
    print("  DATABASE FUNCTIONALITY TEST")
    print("="*60)
    
    try:
        # Use single session for all tests
        with get_db_session() as db:
            # Test basic repositories
            test_data = test_basic_repositories(db)
            
            # Test new repositories
            test_new_repositories(db, test_data)
            
            # Test relationships
            test_relationships(db)
            
            # Test queries
            test_queries(db)
        
        print_section("TEST SUMMARY")
        print("✅ All tests completed successfully!")
        print("\nDatabase is working correctly with:")
        print("  ✓ User management")
        print("  ✓ Movie/Series management")
        print("  ✓ Slot management")
        print("  ✓ Room management")
        print("  ✓ Rating system")
        print("  ✓ Episode management")
        print("  ✓ Comment system")
        print("  ✓ Like system")
        print("  ✓ Watch history tracking")
        
    except Exception as e:
        print_section("ERROR")
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

