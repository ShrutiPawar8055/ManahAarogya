from datetime import datetime

from sqlmodel import Session, select

from app.database.models import HabitOnboarding


class HabitOnboardingRepository:
    """Database operations for first-time habit onboarding."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_user(self, user_id: int) -> HabitOnboarding | None:
        statement = select(HabitOnboarding).where(HabitOnboarding.user_id == user_id)
        return self.session.exec(statement).first()

    def upsert(self, user_id: int, responses_json: str, completed: bool) -> HabitOnboarding:
        record = self.get_by_user(user_id)
        if not record:
            record = HabitOnboarding(user_id=user_id)
        record.responses_json = responses_json
        record.completed = completed
        record.updated_at = datetime.utcnow()
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record
