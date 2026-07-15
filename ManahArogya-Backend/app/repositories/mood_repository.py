from sqlmodel import Session, select

from app.database.models import MoodEntry


class MoodRepository:
    """Database operations for mood logs."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, mood_entry: MoodEntry) -> MoodEntry:
        self.session.add(mood_entry)
        self.session.commit()
        self.session.refresh(mood_entry)
        return mood_entry

    def list_by_user(self, user_id: int, limit: int = 30) -> list[MoodEntry]:
        statement = select(MoodEntry).where(MoodEntry.user_id == user_id)
        rows = list(self.session.exec(statement))
        rows.sort(key=lambda item: item.created_at, reverse=True)
        return rows[:limit]

    def latest_by_user(self, user_id: int) -> MoodEntry | None:
        """Return the most recent mood entry for a user."""
        items = self.list_by_user(user_id, limit=1)
        return items[0] if items else None
