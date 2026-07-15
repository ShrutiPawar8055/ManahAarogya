from sqlmodel import Session, select

from app.database.models import Habit


class HabitRepository:
    """Database operations for habits."""

    def __init__(self, session: Session) -> None:
        """Store the active database session."""
        self.session = session

    def list_by_user(self, user_id: int) -> list[Habit]:
        """Return all habits for a user."""
        statement = select(Habit).where(Habit.user_id == user_id)
        return list(self.session.exec(statement))

    def get_by_id(self, user_id: int, habit_id: int) -> Habit | None:
        """Return one habit scoped to user."""
        statement = select(Habit).where(Habit.user_id == user_id, Habit.id == habit_id)
        return self.session.exec(statement).first()

    def create(self, habit: Habit) -> Habit:
        """Insert a new habit."""
        self.session.add(habit)
        self.session.commit()
        self.session.refresh(habit)
        return habit

    def save(self, habit: Habit) -> Habit:
        """Persist updates to an existing habit."""
        self.session.add(habit)
        self.session.commit()
        self.session.refresh(habit)
        return habit

    def delete(self, habit: Habit) -> None:
        """Delete one habit."""
        self.session.delete(habit)
        self.session.commit()
