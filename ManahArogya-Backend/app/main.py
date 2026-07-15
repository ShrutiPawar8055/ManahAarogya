from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.database import models  # noqa: F401
from app.database.db import create_db_and_tables
from app.repositories.event_repository import EventRepository
from app.repositories.resource_repository import ResourceRepository
from app.routers.admin_router import router as admin_router
from app.routers.appointment_router import router as appointment_router
from app.routers.assessment_router import router as assessment_router
from app.routers.auth_router import router as auth_router
from app.routers.chat_router import router as chat_router
from app.routers.community_router import router as community_router
from app.routers.dashboard_router import router as dashboard_router
from app.routers.emotion_router import router as emotion_router
from app.routers.event_router import router as event_router
from app.routers.habit_router import router as habit_router
from app.routers.insights_router import router as insights_router
from app.routers.mood_router import router as mood_router
from app.routers.profile_router import router as profile_router
from app.routers.resource_router import router as resource_router
from app.routers.therapist_router import router as therapist_router
from app.routers.voice_router import router as voice_router

configure_logging()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Mental wellness platform backend",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every API request and response status."""
    logger.info("Request started: {} {}", request.method, request.url.path)
    response = await call_next(request)
    logger.info("Request finished: {} {} -> {}", request.method, request.url.path, response.status_code)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    """Return readable fallback error for unhandled exceptions."""
    logger.exception("Unhandled server error: {}", str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error. Please try again."})


@app.on_event("startup")
def startup() -> None:
    """Create tables and seed startup data."""
    create_db_and_tables()
    from sqlmodel import Session

    from app.database.db import engine

    with Session(engine) as session:
        ResourceRepository(session).ensure_seed_data()
        EventRepository(session).ensure_seed_data()


@app.get("/")
def root() -> dict[str, str]:
    """Return service status."""
    return {"status": "ok", "service": settings.app_name, "version": settings.app_version}


@app.get("/health")
def health() -> dict[str, str]:
    """Return health check status."""
    return {"status": "healthy"}


@app.post("/internal/cron/heartbeat")
def cron_heartbeat(x_cron_key: str | None = Header(default=None)) -> dict[str, str]:
    """Heartbeat endpoint for external schedulers."""
    if not settings.cron_secret:
        raise HTTPException(status_code=503, detail="CRON_SECRET is not configured.")

    if x_cron_key != settings.cron_secret:
        raise HTTPException(status_code=401, detail="Invalid cron key.")

    now = datetime.now(timezone.utc).isoformat()
    logger.info("Cron heartbeat received at {} for service {}", now, settings.app_name)
    return {"status": "ok", "service": settings.app_name, "timestamp_utc": now}


app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(habit_router, prefix=settings.api_prefix)
app.include_router(mood_router, prefix=settings.api_prefix)
app.include_router(profile_router, prefix=settings.api_prefix)
app.include_router(assessment_router, prefix=settings.api_prefix)
app.include_router(chat_router, prefix=settings.api_prefix)
app.include_router(resource_router, prefix=settings.api_prefix)
app.include_router(appointment_router, prefix=settings.api_prefix)
app.include_router(event_router, prefix=settings.api_prefix)
app.include_router(community_router, prefix=settings.api_prefix)
app.include_router(dashboard_router, prefix=settings.api_prefix)
app.include_router(emotion_router, prefix=settings.api_prefix)
app.include_router(insights_router, prefix=settings.api_prefix)
app.include_router(voice_router, prefix=settings.api_prefix)
app.include_router(admin_router, prefix=settings.api_prefix)
app.include_router(therapist_router, prefix=settings.api_prefix)
