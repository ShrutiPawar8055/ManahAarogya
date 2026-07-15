from fastapi import APIRouter, Depends

from app.schemas.user_schema import LoginRequest, LoginResponse, UserResponse
from app.services.auth_service import AuthService, get_auth_service, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, service: AuthService = Depends(get_auth_service)):
    """Login or create a user."""
    return service.login(payload)


@router.get("/me", response_model=UserResponse)
def me(user=Depends(get_current_user)):
    """Return current user profile."""
    return user
