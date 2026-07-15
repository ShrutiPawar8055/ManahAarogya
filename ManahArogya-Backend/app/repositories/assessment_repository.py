from sqlmodel import Session, select

from app.database.models import AssessmentResult


class AssessmentRepository:
    """Database operations for assessments."""

    def __init__(self, session: Session) -> None:
        """Store the active database session."""
        self.session = session

    def list_by_user(self, user_id: int) -> list[AssessmentResult]:
        """Return user assessments sorted newest first."""
        statement = select(AssessmentResult).where(AssessmentResult.user_id == user_id)
        rows = list(self.session.exec(statement))
        return sorted(rows, key=lambda item: item.created_at, reverse=True)

    def latest_by_user(self, user_id: int) -> AssessmentResult | None:
        """Return the most recent legacy assessment result for a user."""
        rows = self.list_by_user(user_id)
        return rows[0] if rows else None

    def create(self, assessment_result: AssessmentResult) -> AssessmentResult:
        """Insert a new assessment result."""
        self.session.add(assessment_result)
        self.session.commit()
        self.session.refresh(assessment_result)
        return assessment_result
