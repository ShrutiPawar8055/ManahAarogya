import httpx
from fastapi import Depends
from sqlmodel import Session

from app.database.db import get_session
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.resource_repository import ResourceRepository


class ResourceService:
    """Business logic for resource library and recommendations."""

    def __init__(self, session: Session) -> None:
        """Create service with repository dependencies."""
        self.assessment_repository = AssessmentRepository(session)
        self.resource_repository = ResourceRepository(session)

    def list_resources(self) -> list:
        """Return all resources."""
        return self.resource_repository.list_all()

    def list_categories(self) -> list[str]:
        """Return sorted resource categories."""
        resources = self.resource_repository.list_all()
        return sorted({resource.category for resource in resources})

    def list_library(self, query: str | None, resource_type: str | None, recommended: bool, limit: int) -> list:
        """Filter resource library by simple search options."""
        resources = self.resource_repository.list_all()
        if query:
            resources = [item for item in resources if query.lower() in item.title.lower()]
        if resource_type:
            resources = [item for item in resources if item.resource_type == resource_type]
        if recommended:
            resources = [item for item in resources if item.recommended]
        return resources[:limit]

    async def get_recommendations(self, user_id: int) -> dict[str, object]:
        """Build recommendations using assessments and one external tip."""
        assessments = self.assessment_repository.list_by_user(user_id)
        recommended = self.resource_repository.list_recommended(limit=5)
        severity_labels = [item.severity for item in assessments[:3]]
        external_tip = await self._fetch_daily_tip()
        return {
            "resources": recommended,
            "severity_labels": severity_labels,
            "daily_tip": external_tip,
        }

    async def _fetch_daily_tip(self) -> str:
        """Fetch one short wellness tip with graceful fallback."""
        fallback_tip = "Take a short walk and hydrate before starting your next task."
        # Keep dashboard/resource calls fast in local/dev by default.
        return fallback_tip

        # Optional remote tip source (disabled for now):
        url = "https://zenquotes.io/api/random"
        try:
            async with httpx.AsyncClient(timeout=0.8) as client:
                response = await client.get(url)
            if response.status_code != 200:
                return fallback_tip
            payload = response.json()
            if isinstance(payload, list) and payload:
                quote = payload[0].get("q")
                return quote or fallback_tip
        except Exception:
            return fallback_tip
        return fallback_tip


def get_resource_service(session: Session = Depends(get_session)) -> ResourceService:
    """FastAPI dependency for ResourceService."""
    return ResourceService(session)
