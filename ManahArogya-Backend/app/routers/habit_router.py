from datetime import datetime

from fastapi import APIRouter, Depends

from app.schemas.habit_schema import HabitCoachRequest, HabitCreateRequest, HabitOnboardingSubmitRequest, HabitUpdateRequest
from app.services.auth_service import get_current_user
from app.services.habit_service import HabitService, get_habit_service

router = APIRouter(prefix="/habits", tags=["habits"])


@router.get("/")
def list_habits(user=Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    """Return all habits for current user."""
    return {"data": service.list_habits(user.id)}


@router.get("/today")
def today_habits(user=Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    """Return today's habits (current implementation returns all user habits)."""
    return {"data": service.list_habits(user.id)}


@router.post("/")
def create_habit(payload: HabitCreateRequest, user=Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    """Create a new habit."""
    habit = service.create_habit(user.id, payload.title, payload.description, payload.schedule, payload.category)
    return {"data": habit}


@router.patch("/{habit_id}")
def update_habit(habit_id: int, payload: HabitUpdateRequest, user=Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    """Update one habit."""
    updates = payload.model_dump(exclude_none=True)
    return {"data": service.update_habit(user.id, habit_id, updates)}


@router.delete("/{habit_id}")
def delete_habit(habit_id: int, user=Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    """Delete one habit."""
    return {"data": service.delete_habit(user.id, habit_id)}


@router.post("/{habit_id}/complete")
def complete_habit(habit_id: int, user=Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    """Mark one habit as complete."""
    return {"data": service.update_habit(user.id, habit_id, {"done": True})}


@router.get("/stats")
def habit_stats(user=Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    """Return habit stats."""
    return {"data": service.stats(user.id)}


@router.get("/weekly-progress")
def weekly_progress(user=Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    """Return weekly habit progress."""
    return {"data": service.weekly_progress(user.id)}


@router.get("/category-progress")
def category_progress(user=Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    """Return category-wise habit progress."""
    return {"data": service.category_progress(user.id)}


@router.get("/calendar")
def habit_calendar(year: int | None = None, month: int | None = None, user=Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    """Return monthly habit calendar."""
    today = datetime.utcnow()
    return {"data": service.calendar(user.id, year or today.year, month or today.month)}


@router.post("/coach")
def habit_coach(payload: HabitCoachRequest, user=Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    """Return AI coaching for habit routines."""
    return {"data": service.coach(user.id, payload.message)}


@router.get("/onboarding/status")
def onboarding_status(user=Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    """Return whether habit onboarding is complete."""
    return {"data": service.onboarding_status(user.id)}


@router.get("/onboarding/questions")
def onboarding_questions(_user=Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    """Return first-login habit onboarding questions."""
    return {"data": service.onboarding_questions()}


@router.post("/onboarding/submit")
def onboarding_submit(
    payload: HabitOnboardingSubmitRequest,
    user=Depends(get_current_user),
    service: HabitService = Depends(get_habit_service),
):
    """Submit onboarding answers and create starter habits."""
    return {"data": service.complete_onboarding(user.id, payload.answers)}
