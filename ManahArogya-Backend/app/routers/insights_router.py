from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database.db import get_session
from app.repositories.habit_repository import HabitRepository
from app.repositories.mood_repository import MoodRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.services.assessment_service import AssessmentService
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/daily")
def daily_insights(user=Depends(get_current_user), session: Session = Depends(get_session)):
    mood_repo = MoodRepository(session)
    habit_repo = HabitRepository(session)
    profile_repo = UserProfileRepository(session)
    assessment_service = AssessmentService(session)

    profile = profile_repo.get_by_user_id(user.id)
    moods = mood_repo.list_by_user(user.id, limit=7)
    habits = habit_repo.list_by_user(user.id)
    latest_session = assessment_service.latest_session(user.id)

    mood_scores = [m.mood_score for m in moods]
    mood_avg = round(sum(mood_scores) / len(mood_scores), 2) if mood_scores else None
    completed = sum(1 for h in habits if h.done)
    total = len(habits)

    risk_level = latest_session.get("feedback", {}).get("risk_level") if latest_session else None
    if not risk_level:
        risk_level = profile.risk_level if profile else "low"
    mood_trend = profile.mood_trend if profile else "unknown"
    problems = latest_session.get("user_problems", []) if latest_session else []

    explanations: list[str] = []
    feedback = latest_session.get("feedback", {}) if latest_session else {}
    if feedback.get("overall_summary"):
        explanations.append(feedback["overall_summary"])
    if feedback.get("trend_comparison"):
        explanations.append(feedback["trend_comparison"])
    if mood_avg is not None:
        explanations.append(f"Your 7-check-in mood average is {mood_avg}/10.")
    explanations.append(f"Mood trend is marked as '{mood_trend}'.")
    explanations.append(f"Risk level is currently '{risk_level}'.")
    if total:
        explanations.append(f"You completed {completed}/{total} habits recently.")

    next_actions: list[dict[str, str]] = []
    for action in feedback.get("recommended_actions", [])[:3]:
        next_actions.append(
            {
                "title": action.get("title", "Recommended next step"),
                "because": action.get("rationale", "Generated from your latest structured analysis."),
            }
        )
    if not next_actions:
        next_actions = [
            {
                "title": "Retake your assessment",
                "because": "Fresh screening results sharpen the daily explanation layer.",
            },
            {
                "title": "Pick one tiny habit for today",
                "because": "Consistency builds momentum and improves mood stability over time.",
            },
            {
                "title": "Check the recommended resources",
                "because": "Theyâ€™re selected based on your recent signals.",
            },
        ]

    summary = "Weâ€™re tracking your mood + habits to personalize support."
    if feedback.get("ui_summary"):
        summary = feedback["ui_summary"]
    elif mood_avg is not None:
        summary = f"Todayâ€™s snapshot: mood_avg_7d={mood_avg}/10, trend={mood_trend}, risk={risk_level}."

    return {
        "data": {
            "summary": summary,
            "signals": {
                "mood_avg_7d": mood_avg,
                "mood_trend": mood_trend,
                "risk_level": risk_level,
                "habit_completion": {"total": total, "completed": completed},
                "problems": problems,
            },
            "explanations": explanations,
            "next_actions": next_actions,
        }
    }
