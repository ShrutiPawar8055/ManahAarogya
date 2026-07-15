from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database.db import get_session
from app.database.models import MoodEntry
from app.repositories.mood_repository import MoodRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.schemas.mood_schema import MoodLogRequest
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/mood", tags=["mood"])


@router.post("/log")
def log_mood(payload: MoodLogRequest, user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Log mood entry and update user profile trend."""
    mood_repository = MoodRepository(session)
    profile_repository = UserProfileRepository(session)

    mood_entry = mood_repository.create(
        MoodEntry(user_id=user.id, mood_score=payload.mood_score, notes=payload.notes)
    )

    recent_scores = [item.mood_score for item in mood_repository.list_by_user(user.id, limit=7)]
    mood_trend = "unknown"
    if recent_scores:
        avg_score = sum(recent_scores) / len(recent_scores)
        if avg_score >= 7:
            mood_trend = "improving"
        elif avg_score >= 4:
            mood_trend = "stable"
        else:
            mood_trend = "declining"

    profile_repository.upsert(user_id=user.id, mood_trend=mood_trend)

    return {
        "data": {
            "user_id": user.id,
            "id": mood_entry.id,
            "mood_score": mood_entry.mood_score,
            "notes": mood_entry.notes,
            "mood_trend": mood_trend,
            "saved": True,
        }
    }


@router.get("/latest")
def latest_mood(user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Return the latest mood entry for the user (or null)."""
    repo = MoodRepository(session)
    item = repo.latest_by_user(user.id)
    if not item:
        return {"data": None}
    return {
        "data": {
            "id": item.id,
            "user_id": item.user_id,
            "mood_score": item.mood_score,
            "notes": item.notes,
            "created_at": item.created_at.isoformat(),
        }
    }


@router.get("/history")
def mood_history(days: int = 7, user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Return recent mood entries (default: last 7 entries)."""
    repo = MoodRepository(session)
    limit = max(1, min(int(days), 30))
    items = repo.list_by_user(user.id, limit=limit)
    # Return chronological order for charting
    items_sorted = sorted(items, key=lambda x: x.created_at)
    return {
        "data": [
            {
                "id": item.id,
                "mood_score": item.mood_score,
                "notes": item.notes,
                "created_at": item.created_at.isoformat(),
            }
            for item in items_sorted
        ]
    }
