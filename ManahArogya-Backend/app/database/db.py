from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

engine_kwargs = {"echo": False}
if settings.sqlalchemy_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Supabase/Postgres over pooler can drop idle connections; pre_ping recovers transparently.
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(settings.sqlalchemy_url, **engine_kwargs)


def create_db_and_tables() -> None:
    """Create all SQLModel tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Yield a database session for request scope."""
    with Session(engine) as session:
        yield session
