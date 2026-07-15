from datetime import datetime

from sqlmodel import Field, SQLModel

from sqlalchemy import UniqueConstraint


class User(SQLModel, table=True):
    """User account used across the platform."""

    id: int | None = Field(default=None, primary_key=True)
    external_uid: str = Field(index=True, unique=True)
    email: str | None = None
    name: str | None = None
    role: str = "user"
    organization: str | None = None
    is_banned: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserProfile(SQLModel, table=True):
    """Derived user profile used for personalization and onboarding status."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, unique=True)
    has_completed_assessment: bool = False
    risk_level: str = "low"
    mood_trend: str = "unknown"
    current_problems_json: str = "[]"
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Habit(SQLModel, table=True):
    """Habit configured by a user."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    title: str
    description: str | None = None
    schedule: str = "Anytime"
    category: str = "wellbeing"
    done: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AssessmentResult(SQLModel, table=True):
    """Stored result for a mental health assessment."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    test_id: str = Field(index=True)
    score: int
    severity: str
    summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AssessmentAnswer(SQLModel, table=True):
    """Stores per-question responses for each assessment submission."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    test_id: str = Field(index=True)
    question_index: int
    answer_value: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AssessmentSession(SQLModel, table=True):
    """Session-oriented assessment record used for retakes and structured feedback."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    mode: str = Field(default="retake", index=True)
    status: str = Field(default="draft", index=True)
    question_count: int = 16
    answered_count: int = 0
    answers_json: str = "{}"
    scores_json: str = "[]"
    feedback_json: str = "{}"
    activity_snapshot_json: str = "{}"
    recommended_categories_json: str = "[]"
    user_problems_json: str = "[]"
    risk_level: str = "low"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


class MoodEntry(SQLModel, table=True):
    """Simple mood history for trend analysis."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    mood_score: int
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HabitOnboarding(SQLModel, table=True):
    """Stores first-time habit onboarding responses and completion state."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, unique=True)
    responses_json: str = "{}"
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Resource(SQLModel, table=True):
    """Mental health resource entry."""

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str
    url: str
    resource_type: str
    category: str
    content_format: str = "text"
    media_url: str | None = None
    recommended: bool = False


class Appointment(SQLModel, table=True):
    """User appointment with counselor/therapist."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    therapist_id: int | None = Field(default=None, index=True)
    counselor_name: str | None = None
    preferred_slot: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    mode: str
    location: str | None = None
    notes: str | None = None
    therapist_notes: str | None = None
    status: str = "pending"
    google_event_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Event(SQLModel, table=True):
    """Community or wellness event."""

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str
    category: str
    date: str
    time: str
    mode: str
    location: str | None = None
    registration_link: str | None = None
    host: str
    capacity: int = 50
    attendees: int = 0


class EventRegistration(SQLModel, table=True):
    """Reservation state for event attendance."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    event_id: int = Field(index=True)
    mode: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CommunityPost(SQLModel, table=True):
    """Community post created by a user."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    author: str
    role: str
    content: str
    likes: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CommunityComment(SQLModel, table=True):
    """Comment on a community post."""

    id: int | None = Field(default=None, primary_key=True)
    post_id: int = Field(index=True)
    user_id: int = Field(index=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatConversation(SQLModel, table=True):
    """A chat thread between user and assistant."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    title: str = "New Conversation"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatMessage(SQLModel, table=True):
    """Single message in a conversation."""

    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(index=True)
    sender: str
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CommunityPostReddit(SQLModel, table=True):
    """Reddit-style community post (v2 table)."""

    __table_args__ = ()

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    title: str
    topic: str = Field(default="general", index=True)
    author: str
    role: str
    content: str
    upvotes: int = 0
    downvotes: int = 0
    is_approved: bool = True
    is_flagged: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CommunityCommentReddit(SQLModel, table=True):
    """Threaded comment for reddit-style posts (v2 table)."""

    id: int | None = Field(default=None, primary_key=True)
    post_id: int = Field(index=True)
    user_id: int = Field(index=True)
    parent_id: int | None = Field(default=None, index=True)
    author: str | None = None
    content: str
    is_approved: bool = True
    is_flagged: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CommunityPostVote(SQLModel, table=True):
    """Per-user vote (+1/-1) to prevent infinite re-voting."""

    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_user_post_vote"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    post_id: int = Field(index=True)
    value: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Therapist(SQLModel, table=True):
    """Mental health professional representation."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, index=True)
    name: str
    specialty: str
    is_verified: bool = False
    availability_json: str = "{}"
    session_duration: int = 60
    region: str | None = None
    institution: str | None = None
    google_calendar_token_json: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Alert(SQLModel, table=True):
    """Safety and moderation alerts for admins."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(index=True, default=None)
    type: str  # e.g., 'suicidal_language'
    details: str
    is_resolved: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TherapistMessage(SQLModel, table=True):
    """Messages between therapist and patient."""

    id: int | None = Field(default=None, primary_key=True)
    therapist_id: int = Field(index=True)
    user_id: int = Field(index=True)
    sender: str  # 'therapist' or 'patient'
    content: str
    message_type: str = "text" # 'text' or 'resource'
    resource_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


