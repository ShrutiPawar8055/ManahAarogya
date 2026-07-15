from sqlmodel import Session, select

from app.database.models import User


class UserRepository:
    """Database operations for users."""

    def __init__(self, session: Session) -> None:
        """Store the active database session."""
        self.session = session

    def get_by_external_uid(self, external_uid: str) -> User | None:
        """Find a user by external UID."""
        statement = select(User).where(User.external_uid == external_uid)
        return self.session.exec(statement).first()

    def get_by_email(self, email: str) -> User | None:
        """Find a user by email."""
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()

    def create(self, external_uid: str, email: str | None, name: str | None) -> User:
        """Create and persist a user record."""
        user_record = User(external_uid=external_uid, email=email, name=name)
        self.session.add(user_record)
        self.session.commit()
        self.session.refresh(user_record)
        return user_record

    def save(self, user_record: User) -> User:
        """Persist updates to an existing user record."""
        self.session.add(user_record)
        self.session.commit()
        self.session.refresh(user_record)
        return user_record

    def get_or_create(self, external_uid: str, email: str | None, name: str | None) -> User:
        """Return an existing user or create one."""
        user_record = self.get_by_external_uid(external_uid)
        if user_record:
            needs_update = False
            if email and user_record.email != email:
                user_record.email = email
                needs_update = True
            if name and user_record.name != name:
                user_record.name = name
                needs_update = True
            if needs_update:
                self.session.add(user_record)
                self.session.commit()
                self.session.refresh(user_record)
            return user_record
        return self.create(external_uid=external_uid, email=email, name=name)
