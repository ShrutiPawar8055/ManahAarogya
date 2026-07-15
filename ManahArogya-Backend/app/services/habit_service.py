import json
from calendar import monthrange

from fastapi import Depends, HTTPException
from sqlmodel import Session

from app.agents.habit_coach_agent import habit_coach_agent
from app.database.db import get_session
from app.database.models import Habit
from app.repositories.habit_onboarding_repository import HabitOnboardingRepository
from app.repositories.habit_repository import HabitRepository


class HabitService:
    """Business logic for habit tracking."""

    def __init__(self, session: Session) -> None:
        """Create service with repository dependencies."""
        self.habit_repository = HabitRepository(session)
        self.habit_onboarding_repository = HabitOnboardingRepository(session)

    def list_habits(self, user_id: int) -> list[Habit]:
        """Return habits for the current user."""
        return self.habit_repository.list_by_user(user_id)

    def create_habit(
        self,
        user_id: int,
        title: str,
        description: str | None,
        schedule: str,
        category: str,
    ) -> Habit:
        """Create and persist one habit."""
        habit = Habit(user_id=user_id, title=title, description=description, schedule=schedule, category=category)
        return self.habit_repository.create(habit)

    def update_habit(self, user_id: int, habit_id: int, updates: dict) -> Habit:
        """Update a habit and return the updated record."""
        habit_record = self.habit_repository.get_by_id(user_id, habit_id)
        if not habit_record:
            raise HTTPException(status_code=404, detail="Habit not found.")
        for field_name, field_value in updates.items():
            setattr(habit_record, field_name, field_value)
        return self.habit_repository.save(habit_record)

    def delete_habit(self, user_id: int, habit_id: int) -> dict[str, bool]:
        """Delete a habit if it exists."""
        habit_record = self.habit_repository.get_by_id(user_id, habit_id)
        if not habit_record:
            raise HTTPException(status_code=404, detail="Habit not found.")
        self.habit_repository.delete(habit_record)
        return {"deleted": True}

    def stats(self, user_id: int) -> dict[str, int]:
        """Compute simple completion stats."""
        habit_list = self.habit_repository.list_by_user(user_id)
        completed_count = sum(1 for item in habit_list if item.done)
        return {"total": len(habit_list), "completed": completed_count, "pending": len(habit_list) - completed_count}

    def weekly_progress(self, user_id: int) -> list[dict[str, int]]:
        """Return a lightweight weekly progress series."""
        habit_list = self.habit_repository.list_by_user(user_id)
        completed_count = sum(1 for item in habit_list if item.done)
        return [{"day": day, "completed": completed_count} for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]]

    def category_progress(self, user_id: int) -> list[dict[str, int]]:
        """Group habits by category."""
        category_counts: dict[str, int] = {}
        for habit_record in self.habit_repository.list_by_user(user_id):
            category_counts[habit_record.category] = category_counts.get(habit_record.category, 0) + 1
        return [{"category": key, "count": value} for key, value in category_counts.items()]

    def calendar(self, user_id: int, year: int, month: int) -> dict[str, list[dict[str, int | bool]]]:
        """Build a simple monthly habit completion calendar."""
        habit_list = self.habit_repository.list_by_user(user_id)
        days_in_month = monthrange(year, month)[1]
        completed_count = sum(1 for item in habit_list if item.done)
        calendar_days = []
        for day in range(1, days_in_month + 1):
            calendar_days.append({"day": day, "completed": completed_count, "has_activity": completed_count > 0})
        return {"year": year, "month": month, "days": calendar_days}

    def coach(self, user_id: int, user_message: str | None) -> dict[str, object]:
        """Generate coaching response and include current habit list."""
        habit_list = self.habit_repository.list_by_user(user_id)
        habit_summary = ", ".join(f"{item.title} ({'done' if item.done else 'pending'})" for item in habit_list[:10])
        message_text = user_message or "Help me improve my routine."
        coaching_text = habit_coach_agent.run(message_text, habit_summary or "No habits yet")
        return {
            "response": coaching_text,
            "habits": [
                {
                    "id": item.id,
                    "title": item.title,
                    "description": item.description,
                    "schedule": item.schedule,
                    "category": item.category,
                    "done": item.done,
                }
                for item in habit_list
            ],
        }

    def onboarding_questions(self) -> list[dict[str, object]]:
        """Return first-login onboarding questionnaire."""
        return [
            {
                "id": "focus_area",
                "question": "What area do you want to improve first?",
                "options": ["stress", "sleep", "productivity", "mood"],
            },
            {
                "id": "daily_minutes",
                "question": "How much time can you commit daily?",
                "options": ["5", "10", "20"],
            },
            {
                "id": "biggest_challenge",
                "question": "What blocks your consistency most?",
                "options": ["distraction", "low_energy", "anxiety", "time_management"],
            },
            {
                "id": "preferred_slot",
                "question": "When are you most likely to follow through?",
                "options": ["morning", "afternoon", "evening"],
            },
        ]

    def onboarding_status(self, user_id: int) -> dict[str, object]:
        """Return onboarding completion and habit count for current user."""
        record = self.habit_onboarding_repository.get_by_user(user_id)
        habits = self.habit_repository.list_by_user(user_id)
        return {"completed": bool(record.completed) if record else False, "habit_count": len(habits)}

    def complete_onboarding(self, user_id: int, answers: dict[str, str]) -> dict[str, object]:
        """Persist answers and auto-create starter habits."""
        focus = answers.get("focus_area", "mood")
        minutes = answers.get("daily_minutes", "10")
        challenge = answers.get("biggest_challenge", "distraction")
        slot = answers.get("preferred_slot", "evening")

        template_habits: list[tuple[str, str, str, str]] = []
        if focus == "sleep":
            template_habits.extend(
                [
                    ("Digital sunset", "No screens 30 minutes before sleep", slot, "sleep"),
                    ("Wind-down breathing", f"{minutes} minute breathing before bed", "evening", "sleep"),
                ]
            )
        elif focus == "stress":
            template_habits.extend(
                [
                    ("4-6 breathing", f"{minutes} minute breathwork", slot, "stress"),
                    ("Stress journal", "Write one stress trigger and one response", "evening", "stress"),
                ]
            )
        elif focus == "productivity":
            template_habits.extend(
                [
                    ("Deep work block", f"{minutes} minute focused study", slot, "productivity"),
                    ("Task triage", "Pick top 3 tasks for today", "morning", "productivity"),
                ]
            )
        else:
            template_habits.extend(
                [
                    ("Mood check-in", "Rate your mood and write one line", slot, "mood"),
                    ("Gratitude note", "Write 1 thing that went well today", "evening", "mood"),
                ]
            )

        if challenge == "distraction":
            template_habits.append(("Focus mode", "Silence notifications during one work block", slot, "productivity"))
        elif challenge == "low_energy":
            template_habits.append(("Hydration + walk", "Drink water and do a short walk", "afternoon", "wellbeing"))
        elif challenge == "anxiety":
            template_habits.append(("Grounding 5-4-3-2-1", "Use sensory grounding once daily", slot, "stress"))
        else:
            template_habits.append(("Plan tomorrow", "Plan next day in 3 bullet points", "evening", "productivity"))

        existing_titles = {item.title.strip().lower() for item in self.habit_repository.list_by_user(user_id)}
        created: list[Habit] = []
        for title, description, schedule, category in template_habits:
            if title.strip().lower() in existing_titles:
                continue
            created.append(self.create_habit(user_id, title, description, schedule, category))

        self.habit_onboarding_repository.upsert(user_id=user_id, responses_json=json.dumps(answers), completed=True)
        return {"created_habits": created, "created_count": len(created), "completed": True}


def get_habit_service(session: Session = Depends(get_session)) -> HabitService:
    """FastAPI dependency for HabitService."""
    return HabitService(session)
