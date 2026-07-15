from sqlmodel import Session, select

from app.database.models import AssessmentSession


class AssessmentSessionRepository:
    """Database operations for assessment sessions."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, assessment_session: AssessmentSession) -> AssessmentSession:
        self.session.add(assessment_session)
        self.session.commit()
        self.session.refresh(assessment_session)
        return assessment_session

    def save(self, assessment_session: AssessmentSession) -> AssessmentSession:
        self.session.add(assessment_session)
        self.session.commit()
        self.session.refresh(assessment_session)
        return assessment_session

    def get_by_id_for_user(self, user_id: int, session_id: int) -> AssessmentSession | None:
        statement = select(AssessmentSession).where(
            AssessmentSession.user_id == user_id,
            AssessmentSession.id == session_id,
        )
        return self.session.exec(statement).first()

    def list_by_user(
        self,
        user_id: int,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> list[AssessmentSession]:
        statement = select(AssessmentSession).where(AssessmentSession.user_id == user_id)
        if status:
            statement = statement.where(AssessmentSession.status == status)
        rows = list(self.session.exec(statement))
        rows = sorted(rows, key=lambda item: item.completed_at or item.updated_at or item.started_at, reverse=True)
        if limit is not None:
            return rows[:limit]
        return rows

    def latest_by_user(
        self,
        user_id: int,
        *,
        status: str | None = "completed",
    ) -> AssessmentSession | None:
        rows = self.list_by_user(user_id, status=status, limit=1)
        return rows[0] if rows else None
