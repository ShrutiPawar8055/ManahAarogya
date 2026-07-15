from __future__ import annotations

import datetime
from typing import Any, Dict

from sqlmodel import Session

from app.database.models import Habit, MoodEntry
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.community_repository import CommunityRepository
from app.repositories.habit_repository import HabitRepository
from app.repositories.mood_repository import MoodRepository
from app.repositories.user_profile_repository import UserProfileRepository


ToolResult = Dict[str, Any]


class ToolContext:
    """Read-only snapshot tools for ManahNavigator."""

    def __init__(self, user_id: int, session: Session) -> None:
        self.user_id = user_id
        self.session = session

    # --- System ---
    def get_current_time(self) -> ToolResult:
        now = datetime.datetime.now()
        return {
            "kind": "system.time",
            "current_time": now.isoformat(),
            "timezone": str(now.astimezone().tzinfo)
        }

    # --- Mood ---
    def get_latest_mood(self) -> ToolResult:
        repo = MoodRepository(self.session)
        item: MoodEntry | None = repo.latest_by_user(self.user_id)
        if not item:
            return {"kind": "mood.latest", "has_data": False}
        return {
            "kind": "mood.latest",
            "has_data": True,
            "score": item.mood_score,
            "notes": item.notes,
            "created_at": item.created_at.isoformat(),
        }

    def get_mood_history(self, limit: int = 7) -> ToolResult:
        repo = MoodRepository(self.session)
        items = repo.list_by_user(self.user_id, limit=limit)
        items_sorted = sorted(items, key=lambda x: x.created_at)
        return {
            "kind": "mood.history",
            "items": [
                {
                    "score": item.mood_score,
                    "notes": item.notes,
                    "created_at": item.created_at.isoformat(),
                }
                for item in items_sorted
            ],
        }

    # --- Habits ---
    def get_habits_overview(self) -> ToolResult:
        repo = HabitRepository(self.session)
        habits = repo.list_by_user(self.user_id)
        total = len(habits)
        completed = sum(1 for h in habits if h.done)
        return {
            "kind": "habits.overview",
            "stats": {"total": total, "completed": completed, "pending": total - completed},
            "items": [
                {
                    "id": h.id,
                    "title": h.title,
                    "category": h.category,
                    "schedule": h.schedule,
                    "done": h.done,
                }
                for h in habits[:20]
            ],
        }

    def create_new_habit(self, title: str, category: str = "wellbeing") -> ToolResult:
        repo = HabitRepository(self.session)
        habit = repo.create(Habit(user_id=self.user_id, title=title, category=category))
        return {
            "kind": "habit.created",
            "id": habit.id,
            "title": habit.title,
            "category": habit.category,
            "message": f"Successfully created habit '{title}'."
        }

    def mark_habit_complete(self, habit_id: int) -> ToolResult:
        repo = HabitRepository(self.session)
        habit = repo.get_by_id(self.user_id, habit_id)
        if not habit:
            return {"kind": "error", "message": f"Habit {habit_id} not found."}
        
        habit.done = True
        self.session.add(habit)
        self.session.commit()
        return {
            "kind": "habit.completed",
            "id": habit.id,
            "title": habit.title,
            "message": f"Awesome! Marked '{habit.title}' as complete today."
        }

    # --- Interventions (Active UI states) ---
    def trigger_breathing_exercise(self) -> ToolResult:
        # A purely frontend-activating tool
        return {
            "kind": "intervention.breathing",
            "message": "Initiated a 4-7-8 breathing exercise. Please guide the user through it using the UI widget."
        }

    def get_grounding_technique(self) -> ToolResult:
        return {
            "kind": "intervention.grounding",
            "technique": "5-4-3-2-1",
            "steps": [
                "5 things you can see",
                "4 things you can physically feel",
                "3 things you can hear",
                "2 things you can smell",
                "1 thing you can taste"
            ],
            "message": "Initiated 5-4-3-2-1 grounding widget."
        }

    # --- Assessments ---
    def get_recent_assessments(self) -> ToolResult:
        repo = AssessmentRepository(self.session)
        items = repo.list_by_user(self.user_id)[:5]
        return {
            "kind": "assessments.recent",
            "items": [
                {
                    "test_id": a.test_id,
                    "score": a.score,
                    "severity": a.severity,
                    "created_at": a.created_at.isoformat(),
                }
                for a in items
            ],
        }

    # --- Resources ---
    def get_recommended_resources(self) -> ToolResult:
        repo = ResourceRepository(self.session)
        resources = repo.list_recommended(limit=5)
        return {
            "kind": "resources.recommended",
            "items": [
                {
                    "id": r.id,
                    "title": r.title,
                    "category": r.category,
                    "resource_type": r.resource_type,
                    "url": r.url,
                }
                for r in resources
            ],
        }

    # --- Community ---
    def get_community_stats(self) -> ToolResult:
        repo = CommunityRepository(self.session)
        posts = repo.list_posts()
        comment_count = sum(len(repo.list_comments(p.id)) for p in posts if p.id)
        return {
            "kind": "community.stats",
            "posts": len(posts),
            "comments": comment_count,
        }

    # --- Profile snapshot ---
    def get_profile_snapshot(self) -> ToolResult:
        profile_repo = UserProfileRepository(self.session)
        mood_repo = MoodRepository(self.session)
        assess_repo = AssessmentRepository(self.session)

        profile = profile_repo.get_by_user_id(self.user_id)
        moods = mood_repo.list_by_user(self.user_id, limit=7)
        assessments = assess_repo.list_by_user(self.user_id)[:3]

        mood_scores = [m.mood_score for m in moods]
        mood_avg = round(sum(mood_scores) / len(mood_scores), 2) if mood_scores else None
        return {
            "kind": "profile.snapshot",
            "risk_level": profile.risk_level if profile else "low",
            "mood_trend": profile.mood_trend if profile else "unknown",
            "mood_avg_7d": mood_avg,
            "assessments": [
                {
                    "test_id": a.test_id,
                    "severity": a.severity,
                    "created_at": a.created_at.isoformat(),
                }
                for a in assessments
            ],
        }


TOOL_REGISTRY: dict[str, callable] = {
    "get_current_time": lambda ctx, args: ctx.get_current_time(),
    "get_latest_mood": lambda ctx, args: ctx.get_latest_mood(),
    "get_mood_history": lambda ctx, args: ctx.get_mood_history(limit=int(args.get("limit", 7))),
    "get_habits_overview": lambda ctx, args: ctx.get_habits_overview(),
    "create_new_habit": lambda ctx, args: ctx.create_new_habit(title=args.get("title", "New Habit"), category=args.get("category", "wellbeing")),
    "mark_habit_complete": lambda ctx, args: ctx.mark_habit_complete(habit_id=int(args.get("habit_id", 0))),
    "trigger_breathing_exercise": lambda ctx, args: ctx.trigger_breathing_exercise(),
    "get_grounding_technique": lambda ctx, args: ctx.get_grounding_technique(),
    "get_recent_assessments": lambda ctx, args: ctx.get_recent_assessments(),
    "get_community_stats": lambda ctx, args: ctx.get_community_stats(),
    "get_profile_snapshot": lambda ctx, args: ctx.get_profile_snapshot(),
}

