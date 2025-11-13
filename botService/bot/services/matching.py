"""Matching service - preferences and peer rating similarity"""
import logging
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from bot.database.repositories import UserVoteRepository, UserRepository
from bot.database.models import Slot, Movie

logger = logging.getLogger(__name__)

class MatchingService:
    """Service for matching users by preferences and peer ratings"""
    
    @staticmethod
    def compute_user_similarity(db: Session, user_a_id: int, user_b_id: int) -> float:
        """
        Compute similarity between two users:
        - Preferences similarity based on KP votes overlap (1 - normalized MAE)
        - Peer rating closeness based on in-bot rating (User.rating)
        Returns score in [0,1].
        """
        votes_a = UserVoteRepository.get_user_votes_map(db, user_a_id)
        votes_b = UserVoteRepository.get_user_votes_map(db, user_b_id)
        
        # Preference similarity
        common = set(votes_a.keys()) & set(votes_b.keys())
        if common:
            diffs = [abs(votes_a[k] - votes_b[k]) for k in common]
            # KP is typically 1..10; normalize by 9 (max diff)
            pref_sim = 1.0 - (sum(diffs) / (len(diffs) * 9.0))
            if pref_sim < 0.0:
                pref_sim = 0.0
        else:
            pref_sim = 0.0
        
        # Peer rating closeness
        ua = UserRepository.get_by_id(db, user_a_id)
        ub = UserRepository.get_by_id(db, user_b_id)
        if ua and ub:
            diff = abs((ua.rating or 0.0) - (ub.rating or 0.0))
            rating_close = 1.0 - min(1.0, diff / 5.0)  # ratings 0..5
        else:
            rating_close = 0.0
        
        # Combine (weighted)
        return 0.7 * pref_sim + 0.3 * rating_close
    
    @staticmethod
    def compute_slot_compatibility(db: Session, user_id: int, slot: Slot) -> float:
        """Average similarity to current participants"""
        if not slot.participants:
            return 0.0
        sims = [MatchingService.compute_user_similarity(db, user_id, p.user_id) for p in slot.participants]
        return sum(sims) / len(sims)
    
    @staticmethod
    def annotate_slots_by_compatibility(db: Session, user_id: int, slots: List[Slot]) -> List[Tuple[Slot, float]]:
        """Return list of (slot, score) sorted by score desc"""
        scored = [(slot, MatchingService.compute_slot_compatibility(db, user_id, slot)) for slot in slots]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    # ---- Interest-based ranking for movies (not user similarity) ----
    @staticmethod
    def _compute_user_vote_stats(db: Session, user_id: int) -> Tuple[float | None, Dict[str, int], int]:
        """Return (avg_year, type_counts, total_votes) from user votes"""
        votes = db.query(UserVoteRepository).first()  # placeholder to satisfy linter types
        user_votes = UserVoteRepository.get_user_votes_map(db, user_id)
        # We need extended info, so re-query full rows
        from bot.database.models import UserVote as UserVoteModel
        rows = db.query(UserVoteModel).filter(UserVoteModel.user_id == user_id).all()
        years = [r.year for r in rows if r.year is not None]
        avg_year = sum(years) / len(years) if years else None
        type_counts: Dict[str, int] = {}
        for r in rows:
            if r.type:
                type_counts[r.type] = type_counts.get(r.type, 0) + 1
        total = len(rows)
        return avg_year, type_counts, total
    
    @staticmethod
    def compute_movie_interest(db: Session, user_id: int, movie: Movie) -> float:
        """
        Heuristic interest score in [0,1] based on:
        - type preference (user's distribution over FILM/TV_SERIES)
        - year proximity to user's average year
        - light popularity proxy (not here; handled at slot level if needed)
        """
        avg_year, type_counts, total = MatchingService._compute_user_vote_stats(db, user_id)
        
        # Type score
        type_score = 0.0
        if total > 0 and movie.type:
            type_score = type_counts.get(movie.type, 0) / total
        
        # Year score
        year_score = 0.0
        if avg_year is not None and movie.year:
            diff = abs(movie.year - avg_year)
            year_score = 1.0 - min(1.0, diff / 30.0)  # decay over ~30 years
        
        # Combine
        return 0.7 * type_score + 0.3 * year_score
    
    @staticmethod
    def annotate_slots_by_interest(db: Session, user_id: int, slots: List[Slot], exclude_kinopoisk_ids: set[str]) -> List[Tuple[Slot, float]]:
        """Score slots by movie interest, exclude watched (by kp id)"""
        scored: List[Tuple[Slot, float]] = []
        for slot in slots:
            kp_id = slot.movie.kinopoisk_id
            if kp_id and kp_id in exclude_kinopoisk_ids:
                continue
            score = MatchingService.compute_movie_interest(db, user_id, slot.movie)
            scored.append((slot, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

