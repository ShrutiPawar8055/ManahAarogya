from datetime import datetime

from sqlmodel import Session, select

from app.database.models import UserProfile


class UserProfileRepository:
    """Database operations for derived user profile state."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_user_id(self, user_id: int) -> UserProfile | None:
        statement = select(UserProfile).where(UserProfile.user_id == user_id)
        return self.session.exec(statement).first()

    def upsert(
        self,
        user_id: int,
        has_completed_assessment: bool | None = None,
        risk_level: str | None = None,
        mood_trend: str | None = None,
        current_problems_json: str | None = None,
    ) -> UserProfile:
        profile = self.get_by_user_id(user_id)
        if not profile:
            profile = UserProfile(user_id=user_id)

        if has_completed_assessment is not None:
            profile.has_completed_assessment = has_completed_assessment
        if risk_level is not None:
            profile.risk_level = risk_level
        if mood_trend is not None:
            profile.mood_trend = mood_trend
        if current_problems_json is not None:
            profile.current_problems_json = current_problems_json
        profile.updated_at = datetime.utcnow()

        self.session.add(profile)
        self.session.commit()
        self.session.refresh(profile)
        return profile
