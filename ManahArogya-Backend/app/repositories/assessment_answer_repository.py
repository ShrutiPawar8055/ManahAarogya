from sqlmodel import Session, select

from app.database.models import AssessmentAnswer


class AssessmentAnswerRepository:
    """Database operations for per-question assessment responses."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_many(self, rows: list[AssessmentAnswer]) -> None:
        if not rows:
            return
        self.session.add_all(rows)
        self.session.commit()

    def list_by_user(self, user_id: int, limit: int = 200) -> list[AssessmentAnswer]:
        statement = select(AssessmentAnswer).where(AssessmentAnswer.user_id == user_id)
        rows = list(self.session.exec(statement))
        rows.sort(key=lambda item: item.created_at, reverse=True)
        return rows[:limit]
