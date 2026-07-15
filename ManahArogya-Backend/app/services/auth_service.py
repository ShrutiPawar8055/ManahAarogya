import base64
import json

from fastapi import Depends, Header, HTTPException
from sqlmodel import Session

from app.core.logging import logger
from app.database.db import get_session
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import LoginRequest


class AuthService:
    """Business logic for login and user identity."""

    def __init__(self, session: Session) -> None:
        """Create service with repository dependencies."""
        self.user_repository = UserRepository(session)
        self.assessment_repository = AssessmentRepository(session)
        self.user_profile_repository = UserProfileRepository(session)

    def login(self, payload: LoginRequest):
        """Create user on first login and return profile."""
        external_uid = payload.uid or self._uid_from_jwt(payload.token) or payload.email
        if not external_uid:
            raise HTTPException(status_code=422, detail="Either uid or token is required.")

        # Migration safety: if older records were created with transient token IDs,
        # reconcile by email to the stable Firebase UID when possible.
        existing_by_uid = self.user_repository.get_by_external_uid(external_uid)
        if not existing_by_uid and payload.email:
            existing_by_email = self.user_repository.get_by_email(payload.email)
            if existing_by_email and payload.uid and existing_by_email.external_uid != payload.uid:
                existing_by_email.external_uid = payload.uid
                self.user_repository.save(existing_by_email)

        user_record = self.user_repository.get_or_create(external_uid, payload.email, payload.name)
        profile = self.user_profile_repository.get_by_user_id(user_record.id)
        has_completed_assessment = bool(profile.has_completed_assessment) if profile else False
        if not has_completed_assessment:
            has_completed_assessment = len(self.assessment_repository.list_by_user(user_record.id)) > 0
        risk_level = profile.risk_level if profile else "low"
        logger.info("User logged in: {}", user_record.external_uid)
        return {
            "user": user_record,
            "has_completed_assessment": has_completed_assessment,
            "risk_level": risk_level,
        }

    def _uid_from_jwt(self, token: str | None) -> str | None:
        """Extract uid-ish subject from a JWT without signature verification."""
        if not token or "." not in token:
            return None
        parts = token.split(".")
        if len(parts) < 2:
            return None
        payload_part = parts[1]
        padding = "=" * ((4 - len(payload_part) % 4) % 4)
        try:
            decoded = base64.urlsafe_b64decode((payload_part + padding).encode("utf-8"))
            data = json.loads(decoded.decode("utf-8"))
            subject = data.get("sub")
            return str(subject) if subject else None
        except Exception:
            return None


def get_auth_service(session: Session = Depends(get_session)) -> AuthService:
    """FastAPI dependency for AuthService."""
    return AuthService(session)


def get_current_user(
    x_user_id: str | None = Header(default=None),
    x_user_email: str | None = Header(default=None),
    x_user_name: str | None = Header(default=None),
    service: AuthService = Depends(get_auth_service),
):
    """Resolve the current user from request headers."""
    external_uid = x_user_id or x_user_email
    if not external_uid:
        raise HTTPException(status_code=401, detail="Missing user identity headers.")
    user = service.user_repository.get_or_create(external_uid, x_user_email, x_user_name)
    if user.is_banned:
        raise HTTPException(status_code=403, detail="Your account has been banned.")
    return user


def get_admin_user(user=Depends(get_current_user)):
    """Ensure the user is an admin."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required.")
    return user
