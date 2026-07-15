from sqlmodel import Session, select

from app.database.models import Resource


class ResourceRepository:
    """Database operations for resources."""

    def __init__(self, session: Session) -> None:
        """Store the active database session."""
        self.session = session

    def list_all(self) -> list[Resource]:
        """Return all available resources."""
        statement = select(Resource)
        return list(self.session.exec(statement))

    def list_recommended(self, limit: int = 5) -> list[Resource]:
        """Return recommended resources with a limit."""
        statement = select(Resource).where(Resource.recommended == True)  # noqa: E712
        return list(self.session.exec(statement))[:limit]

    def ensure_seed_data(self) -> None:
        """Populate starter resources if table is empty."""
        if self.list_all():
            return
        starter_resources = [
            Resource(
                title="Guided Breathing Basics",
                description="A short breathing guide for anxious moments.",
                url="https://www.sleepfoundation.org/mental-health",
                resource_type="article",
                category="anxiety",
                recommended=True,
            ),
            Resource(
                title="Sleep Hygiene Checklist",
                description="A practical nightly checklist for better sleep.",
                url="https://www.sleepfoundation.org/sleep-hygiene",
                resource_type="guide",
                category="sleep",
                recommended=True,
            ),
            Resource(
                title="Campus Counseling Starter Pack",
                description="How to prepare for your first counseling session.",
                url="https://www.nami.org",
                resource_type="guide",
                category="counseling",
                recommended=False,
            ),
        ]
        for resource in starter_resources:
            self.session.add(resource)
        self.session.commit()
