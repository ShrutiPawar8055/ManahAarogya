from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AssessmentSubmission(BaseModel):
    """Single assessment submission payload."""

    test_id: str
    answers: list[int] = Field(default_factory=list)


class AssessmentSubmitRequest(BaseModel):
    """Batch assessment request."""

    submissions: list[AssessmentSubmission]


class AssessmentSessionCreateRequest(BaseModel):
    """Create a new assessment session."""

    mode: str = Field(default="retake")


class AssessmentAnswerUpdateRequest(BaseModel):
    """Patch one answer inside a session."""

    test_id: str
    question_index: int = Field(ge=0)
    answer_value: int = Field(ge=0, le=3)


class RecommendedAction(BaseModel):
    title: str
    rationale: str
    priority: str = "medium"


class AssessmentScoreCard(BaseModel):
    test_id: str
    title: str
    score: int
    severity: str
    summary: str


class AssessmentTrendEntry(BaseModel):
    test_id: str
    score: int
    severity: str
    created_at: datetime | None = None


class ActivitySnapshot(BaseModel):
    mood_avg_7d: float | None = None
    mood_trend: str = "unknown"
    recent_mood_notes: list[str] = Field(default_factory=list)
    latest_mood_score: int | None = None
    habit_total: int = 0
    habit_completed: int = 0
    habit_completion_rate: float | None = None
    chatbot_conversations: int = 0
    chatbot_messages_last_14d: int = 0
    appointment_total: int = 0
    appointment_completed: int = 0
    appointment_pending: int = 0
    community_posts: int = 0
    community_comments: int = 0
    event_registrations: int = 0
    resource_recommendation_count: int = 0
    assessment_history: list[AssessmentTrendEntry] = Field(default_factory=list)
    emotion_summary: str | None = None


class StructuredAssessmentFeedback(BaseModel):
    overall_summary: str = ""
    ui_summary: str = ""
    risk_level: str = "low"
    risk_rationale: str = ""
    key_findings: list[str] = Field(default_factory=list)
    contributing_factors: list[str] = Field(default_factory=list)
    trend_comparison: str = ""
    recommended_actions: list[RecommendedAction] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    clinician_flags: list[str] = Field(default_factory=list)
    suggested_topics: list[str] = Field(default_factory=list)
    safety_plan: list[str] = Field(default_factory=list)
    needs_urgent_support: bool = False


class AssessmentSessionSummaryResponse(BaseModel):
    id: int
    user_id: int
    mode: str
    status: str
    question_count: int
    answered_count: int
    risk_level: str
    scores: list[AssessmentScoreCard] = Field(default_factory=list)
    feedback: StructuredAssessmentFeedback = Field(default_factory=StructuredAssessmentFeedback)
    recommended_categories: list[str] = Field(default_factory=list)
    user_problems: list[dict[str, str]] = Field(default_factory=list)
    started_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class AssessmentSessionDetailResponse(AssessmentSessionSummaryResponse):
    answers: dict[str, list[int | None]] = Field(default_factory=dict)
    activity_snapshot: ActivitySnapshot = Field(default_factory=ActivitySnapshot)


class AssessmentResultResponse(BaseModel):
    """Legacy assessment result returned by APIs."""

    id: int
    user_id: int
    test_id: str
    score: int
    severity: str
    summary: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
