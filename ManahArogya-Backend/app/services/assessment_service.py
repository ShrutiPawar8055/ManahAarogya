import json
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException
from sqlmodel import Session, select

from app.agents.assessment_analysis_agent import assessment_analysis_agent
from app.agents.resource_agent import resource_agent
from app.database.db import get_session
from app.database.models import (
    Alert,
    Appointment,
    AssessmentAnswer,
    AssessmentResult,
    AssessmentSession,
    ChatConversation,
    ChatMessage,
    CommunityCommentReddit,
    CommunityPostReddit,
    EventRegistration,
)
from app.repositories.assessment_answer_repository import AssessmentAnswerRepository
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.assessment_session_repository import AssessmentSessionRepository
from app.repositories.habit_repository import HabitRepository
from app.repositories.mood_repository import MoodRepository
from app.repositories.resource_repository import ResourceRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.schemas.assessment_schema import (
    ActivitySnapshot,
    AssessmentScoreCard,
    AssessmentSessionDetailResponse,
    AssessmentSessionSummaryResponse,
    AssessmentTrendEntry,
    StructuredAssessmentFeedback,
)


ASSESSMENT_DEFINITIONS = {
    "phq9": {
        "title": "PHQ-9",
        "description": "Depression symptom screening",
        "thresholds": [
            (20, "severe"),
            (15, "moderately severe"),
            (10, "moderate"),
            (5, "mild"),
            (0, "minimal"),
        ],
        "question_count": 9,
    },
    "gad7": {
        "title": "GAD-7",
        "description": "Anxiety symptom screening",
        "thresholds": [
            (15, "severe"),
            (10, "moderate"),
            (5, "mild"),
            (0, "minimal"),
        ],
        "question_count": 7,
    },
}
DEFAULT_TEST_ORDER = ["phq9", "gad7"]
TOTAL_QUESTION_COUNT = sum(item["question_count"] for item in ASSESSMENT_DEFINITIONS.values())


class AssessmentService:
    """Business logic for assessment sessions, scoring, and structured feedback."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.assessment_repository = AssessmentRepository(session)
        self.assessment_answer_repository = AssessmentAnswerRepository(session)
        self.assessment_session_repository = AssessmentSessionRepository(session)
        self.user_profile_repository = UserProfileRepository(session)
        self.mood_repository = MoodRepository(session)
        self.habit_repository = HabitRepository(session)
        self.resource_repository = ResourceRepository(session)

    def get_catalog(self) -> list[dict[str, object]]:
        """Return the supported assessment catalog."""
        return [
            {
                "test_id": test_id,
                "name": item["title"],
                "description": item["description"],
                "question_count": item["question_count"],
            }
            for test_id, item in ASSESSMENT_DEFINITIONS.items()
        ]

    def list_assessments(self, user_id: int) -> list[AssessmentResult]:
        """Return legacy per-test assessment rows."""
        return self.assessment_repository.list_by_user(user_id)

    def create_session(self, user_id: int, mode: str = "retake") -> dict[str, object]:
        """Create a new assessment session."""
        normalized_mode = mode if mode in {"initial", "retake"} else "retake"
        session_record = AssessmentSession(
            user_id=user_id,
            mode=normalized_mode,
            status="draft",
            question_count=TOTAL_QUESTION_COUNT,
            answered_count=0,
            answers_json=self._dump_json(self._empty_answers()),
        )
        saved = self.assessment_session_repository.create(session_record)
        return self._serialize_session(saved, include_answers=True, include_activity=True)

    def get_session(self, user_id: int, session_id: int) -> dict[str, object]:
        """Return one session for the current user."""
        session_record = self._require_session(user_id, session_id)
        return self._serialize_session(session_record, include_answers=True, include_activity=True)

    def update_session_answer(
        self,
        user_id: int,
        session_id: int,
        *,
        test_id: str,
        question_index: int,
        answer_value: int,
    ) -> dict[str, object]:
        """Persist one answer into an assessment session."""
        session_record = self._require_session(user_id, session_id)
        if session_record.status == "completed":
            raise HTTPException(status_code=409, detail="This assessment session is already completed.")

        normalized_test_id = self._validate_answer_patch(
            test_id=test_id,
            question_index=question_index,
            answer_value=answer_value,
        )

        answers = self._load_answers(session_record)
        answers[normalized_test_id][question_index] = int(answer_value)
        session_record.answers_json = self._dump_json(answers)
        session_record.answered_count = self._count_answered(answers)
        session_record.updated_at = datetime.utcnow()
        saved = self.assessment_session_repository.save(session_record)
        return self._serialize_session(saved, include_answers=True, include_activity=False)

    def complete_session(self, user_id: int, session_id: int) -> dict[str, object]:
        """Score the assessment, generate structured feedback, and persist the result."""
        session_record = self._require_session(user_id, session_id)
        if session_record.status == "completed":
            return self._serialize_session(session_record, include_answers=True, include_activity=True)

        answers = self._load_answers(session_record)
        if not self._is_complete(answers):
            raise HTTPException(status_code=422, detail="All assessment questions must be answered before completion.")

        previous_legacy_results = self.assessment_repository.list_by_user(user_id)
        previous_assessments = self._build_previous_assessment_entries(previous_legacy_results)
        activity_snapshot = self._build_activity_snapshot(user_id=user_id, previous_assessments=previous_assessments)
        score_cards = [self._score_test(test_id, answers[test_id]) for test_id in DEFAULT_TEST_ORDER]
        risk_flags = self._evaluate_risk(score_cards=score_cards, answers=answers, activity_snapshot=activity_snapshot, previous_assessments=previous_assessments)
        feedback = assessment_analysis_agent.run(
            score_cards=score_cards,
            activity_snapshot=activity_snapshot,
            previous_assessments=previous_assessments,
            risk_flags=risk_flags,
        )

        user_problems = [
            {"name": score.title, "severity": score.severity}
            for score in score_cards
        ]
        severity_labels = [self._normalize_resource_severity(score.severity) for score in score_cards]
        recommended_categories = resource_agent.recommend_categories(severity_labels)

        session_record.status = "completed"
        session_record.answered_count = self._count_answered(answers)
        session_record.scores_json = self._dump_json([item.model_dump(mode="json") for item in score_cards])
        session_record.feedback_json = feedback.model_dump_json()
        session_record.activity_snapshot_json = activity_snapshot.model_dump_json()
        session_record.recommended_categories_json = self._dump_json(recommended_categories)
        session_record.user_problems_json = self._dump_json(user_problems)
        session_record.risk_level = feedback.risk_level
        session_record.updated_at = datetime.utcnow()
        session_record.completed_at = datetime.utcnow()
        saved = self.assessment_session_repository.save(session_record)

        self._persist_legacy_results(user_id=user_id, answers=answers, score_cards=score_cards)
        self.user_profile_repository.upsert(
            user_id=user_id,
            has_completed_assessment=True,
            risk_level=feedback.risk_level,
            current_problems_json=self._dump_json(user_problems),
        )
        self._maybe_create_alert(user_id=user_id, feedback=feedback, risk_flags=risk_flags)

        return self._serialize_session(saved, include_answers=True, include_activity=True)

    def list_history(self, user_id: int, limit: int = 10) -> list[dict[str, object]]:
        """Return completed assessment sessions newest first."""
        rows = self.assessment_session_repository.list_by_user(user_id, status="completed", limit=limit)
        return [self._serialize_session(item, include_answers=False, include_activity=False) for item in rows]

    def latest_session(self, user_id: int) -> dict[str, object] | None:
        """Return the latest completed assessment session for a user."""
        row = self.assessment_session_repository.latest_by_user(user_id, status="completed")
        if not row:
            return None
        return self._serialize_session(row, include_answers=False, include_activity=False)

    def submit_batch(self, user_id: int, submissions: list[dict]) -> dict[str, object]:
        """Compatibility path for the legacy batch submit endpoint."""
        mode = "initial" if not self.latest_session(user_id) else "retake"
        session_payload = self.create_session(user_id, mode=mode)
        session_id = int(session_payload["id"])
        answers = self._empty_answers()

        for submission in submissions:
            test_id = str(submission.get("test_id") or "").strip().lower()
            if test_id not in ASSESSMENT_DEFINITIONS:
                raise HTTPException(status_code=422, detail=f"Unsupported assessment '{test_id}'.")
            raw_answers = submission.get("answers", [])
            if len(raw_answers) != ASSESSMENT_DEFINITIONS[test_id]["question_count"]:
                raise HTTPException(status_code=422, detail=f"{test_id.upper()} expects {ASSESSMENT_DEFINITIONS[test_id]['question_count']} answers.")
            answers[test_id] = [int(value) for value in raw_answers]

        session_record = self._require_session(user_id, session_id)
        session_record.answers_json = self._dump_json(answers)
        session_record.answered_count = self._count_answered(answers)
        session_record.updated_at = datetime.utcnow()
        self.assessment_session_repository.save(session_record)
        completed = self.complete_session(user_id, session_id)
        return {
            "session": completed,
            "results": completed.get("scores", []),
            "recommended_categories": completed.get("recommended_categories", []),
            "user_problems": completed.get("user_problems", []),
            "risk_level": completed.get("risk_level", "low"),
            "feedback": completed.get("feedback", {}),
        }

    def _serialize_session(
        self,
        session_record: AssessmentSession,
        *,
        include_answers: bool,
        include_activity: bool,
    ) -> dict[str, object]:
        scores = self._load_score_cards(session_record)
        feedback = self._load_feedback(session_record)
        payload = AssessmentSessionSummaryResponse(
            id=session_record.id or 0,
            user_id=session_record.user_id,
            mode=session_record.mode,
            status=session_record.status,
            question_count=session_record.question_count,
            answered_count=session_record.answered_count,
            risk_level=session_record.risk_level,
            scores=scores,
            feedback=feedback,
            recommended_categories=self._load_json_list(session_record.recommended_categories_json),
            user_problems=self._load_problem_list(session_record.user_problems_json),
            started_at=session_record.started_at,
            updated_at=session_record.updated_at,
            completed_at=session_record.completed_at,
        )

        if not include_answers and not include_activity:
            return payload.model_dump(mode="json")

        detail = AssessmentSessionDetailResponse(
            **payload.model_dump(),
            answers=self._load_answers(session_record) if include_answers else {},
            activity_snapshot=self._load_activity_snapshot(session_record) if include_activity else ActivitySnapshot(),
        )
        return detail.model_dump(mode="json")

    def _build_activity_snapshot(
        self,
        *,
        user_id: int,
        previous_assessments: list[AssessmentTrendEntry],
    ) -> ActivitySnapshot:
        moods = self.mood_repository.list_by_user(user_id, limit=7)
        habits = self.habit_repository.list_by_user(user_id)
        mood_scores = [item.mood_score for item in moods]
        mood_avg = round(sum(mood_scores) / len(mood_scores), 2) if mood_scores else None
        recent_mood_notes = [item.notes for item in moods if item.notes][:3]
        habit_completed = sum(1 for habit in habits if habit.done)
        habit_total = len(habits)
        completion_rate = round((habit_completed / habit_total) * 100, 2) if habit_total else None

        conversation_statement = select(ChatConversation).where(ChatConversation.user_id == user_id)
        conversation_rows = list(self.session.exec(conversation_statement))
        conversation_ids = [item.id for item in conversation_rows if item.id is not None]
        message_count = 0
        if conversation_ids:
            since = datetime.utcnow() - timedelta(days=14)
            message_statement = select(ChatMessage).where(
                ChatMessage.conversation_id.in_(conversation_ids),
                ChatMessage.created_at >= since,
            )
            message_count = len(list(self.session.exec(message_statement)))

        appointment_rows = list(self.session.exec(select(Appointment).where(Appointment.user_id == user_id)))
        appointment_completed = sum(1 for item in appointment_rows if item.status == "completed")
        appointment_pending = sum(1 for item in appointment_rows if item.status == "pending")

        post_rows = list(self.session.exec(select(CommunityPostReddit).where(CommunityPostReddit.user_id == user_id)))
        comment_rows = list(self.session.exec(select(CommunityCommentReddit).where(CommunityCommentReddit.user_id == user_id)))
        event_rows = list(self.session.exec(select(EventRegistration).where(EventRegistration.user_id == user_id)))
        recommended_resources = self.resource_repository.list_recommended(limit=5)
        profile = self.user_profile_repository.get_by_user_id(user_id)

        return ActivitySnapshot(
            mood_avg_7d=mood_avg,
            mood_trend=profile.mood_trend if profile else "unknown",
            recent_mood_notes=recent_mood_notes,
            latest_mood_score=moods[0].mood_score if moods else None,
            habit_total=habit_total,
            habit_completed=habit_completed,
            habit_completion_rate=completion_rate,
            chatbot_conversations=len(conversation_rows),
            chatbot_messages_last_14d=message_count,
            appointment_total=len(appointment_rows),
            appointment_completed=appointment_completed,
            appointment_pending=appointment_pending,
            community_posts=len(post_rows),
            community_comments=len(comment_rows),
            event_registrations=len(event_rows),
            resource_recommendation_count=len(recommended_resources),
            assessment_history=previous_assessments,
            emotion_summary=None,
        )

    def _score_test(self, test_id: str, answers: list[int | None]) -> AssessmentScoreCard:
        definition = ASSESSMENT_DEFINITIONS[test_id]
        total_score = sum(int(value or 0) for value in answers)
        severity = next(
            label
            for minimum, label in definition["thresholds"]
            if total_score >= minimum
        )
        summary = f"{definition['title']} indicates {severity} symptoms with a score of {total_score}."
        return AssessmentScoreCard(
            test_id=test_id,
            title=definition["title"],
            score=total_score,
            severity=severity,
            summary=summary,
        )

    def _evaluate_risk(
        self,
        *,
        score_cards: list[AssessmentScoreCard],
        answers: dict[str, list[int | None]],
        activity_snapshot: ActivitySnapshot,
        previous_assessments: list[AssessmentTrendEntry],
    ) -> dict[str, object]:
        severe_labels = {"severe", "moderately severe"}
        phq9_item9_flag = bool(answers.get("phq9", [None] * 9)[8] is not None and int(answers["phq9"][8]) >= 2)
        has_severe_score = any(item.severity in severe_labels for item in score_cards)
        has_moderate_score = any(item.severity == "moderate" for item in score_cards)
        has_mild_score = any(item.severity == "mild" for item in score_cards)
        repeated_elevated_scores = any(item.severity in {"moderate", "severe", "moderately severe"} for item in previous_assessments[:2])
        low_recent_mood = activity_snapshot.mood_avg_7d is not None and activity_snapshot.mood_avg_7d <= 3.5

        risk_level = "low"
        needs_urgent_support = False
        risk_rationale = "Scores are currently in the low range with no urgent flags."

        if phq9_item9_flag or has_severe_score:
            risk_level = "high"
            needs_urgent_support = True
            risk_rationale = "High-risk screening criteria were met because of either a severe score band or an elevated PHQ-9 safety item."
        elif has_moderate_score and low_recent_mood:
            risk_level = "high"
            risk_rationale = "Moderate symptoms combined with a low recent mood average increase current risk."
        elif has_moderate_score or repeated_elevated_scores or low_recent_mood or has_mild_score:
            risk_level = "medium"
            risk_rationale = "Symptoms or recent behavior suggest the user needs closer follow-up rather than a low-risk classification."

        return {
            "risk_level": risk_level,
            "risk_rationale": risk_rationale,
            "needs_urgent_support": needs_urgent_support,
            "phq9_item9_flag": phq9_item9_flag,
            "has_severe_score": has_severe_score,
            "repeated_elevated_scores": repeated_elevated_scores,
            "low_recent_mood": low_recent_mood,
        }

    def _persist_legacy_results(
        self,
        *,
        user_id: int,
        answers: dict[str, list[int | None]],
        score_cards: list[AssessmentScoreCard],
    ) -> None:
        answer_rows: list[AssessmentAnswer] = []
        for score in score_cards:
            legacy_row = AssessmentResult(
                user_id=user_id,
                test_id=score.test_id,
                score=score.score,
                severity=score.severity,
                summary=score.summary,
            )
            self.assessment_repository.create(legacy_row)
            for index, value in enumerate(answers.get(score.test_id, [])):
                answer_rows.append(
                    AssessmentAnswer(
                        user_id=user_id,
                        test_id=score.test_id,
                        question_index=index,
                        answer_value=int(value or 0),
                    )
                )
        self.assessment_answer_repository.create_many(answer_rows)

    def _maybe_create_alert(
        self,
        *,
        user_id: int,
        feedback: StructuredAssessmentFeedback,
        risk_flags: dict[str, object],
    ) -> None:
        if not feedback.needs_urgent_support and not risk_flags.get("phq9_item9_flag"):
            return

        details = feedback.risk_rationale or str(risk_flags.get("risk_rationale") or "High-risk assessment result.")
        alert = Alert(
            user_id=user_id,
            type="high_risk_assessment",
            details=details,
            is_resolved=False,
        )
        self.session.add(alert)
        self.session.commit()

    def _build_previous_assessment_entries(
        self,
        previous_results: list[AssessmentResult],
    ) -> list[AssessmentTrendEntry]:
        latest_by_test: dict[str, AssessmentTrendEntry] = {}
        for result in previous_results:
            if result.test_id in latest_by_test:
                continue
            latest_by_test[result.test_id] = AssessmentTrendEntry(
                test_id=result.test_id,
                score=result.score,
                severity=result.severity,
                created_at=result.created_at,
            )
        return list(latest_by_test.values())

    def _load_answers(self, session_record: AssessmentSession) -> dict[str, list[int | None]]:
        raw_answers = self._load_json_object(session_record.answers_json, default=self._empty_answers())
        normalized = self._empty_answers()
        for test_id, definition in ASSESSMENT_DEFINITIONS.items():
            incoming = raw_answers.get(test_id, [])
            normalized[test_id] = [
                int(value) if isinstance(value, int) else None
                for value in list(incoming)[: definition["question_count"]]
            ]
            if len(normalized[test_id]) < definition["question_count"]:
                normalized[test_id].extend([None] * (definition["question_count"] - len(normalized[test_id])))
        return normalized

    def _load_score_cards(self, session_record: AssessmentSession) -> list[AssessmentScoreCard]:
        raw_scores = self._load_json_list(session_record.scores_json)
        cards: list[AssessmentScoreCard] = []
        for item in raw_scores:
            if not isinstance(item, dict):
                continue
            try:
                cards.append(AssessmentScoreCard.model_validate(item))
            except Exception:
                continue
        return cards

    def _load_feedback(self, session_record: AssessmentSession) -> StructuredAssessmentFeedback:
        raw_feedback = self._load_json_object(session_record.feedback_json, default={})
        try:
            return StructuredAssessmentFeedback.model_validate(raw_feedback)
        except Exception:
            return StructuredAssessmentFeedback(risk_level=session_record.risk_level)

    def _load_activity_snapshot(self, session_record: AssessmentSession) -> ActivitySnapshot:
        raw_snapshot = self._load_json_object(session_record.activity_snapshot_json, default={})
        try:
            return ActivitySnapshot.model_validate(raw_snapshot)
        except Exception:
            return ActivitySnapshot()

    def _load_problem_list(self, raw_value: str) -> list[dict[str, str]]:
        raw_list = self._load_json_list(raw_value)
        return [item for item in raw_list if isinstance(item, dict)]

    def _load_json_object(self, raw_value: str, *, default: dict) -> dict:
        try:
            parsed = json.loads(raw_value) if raw_value else default
        except Exception:
            return default
        return parsed if isinstance(parsed, dict) else default

    def _load_json_list(self, raw_value: str) -> list:
        try:
            parsed = json.loads(raw_value) if raw_value else []
        except Exception:
            return []
        return parsed if isinstance(parsed, list) else []

    def _empty_answers(self) -> dict[str, list[int | None]]:
        return {
            test_id: [None] * definition["question_count"]
            for test_id, definition in ASSESSMENT_DEFINITIONS.items()
        }

    def _count_answered(self, answers: dict[str, list[int | None]]) -> int:
        return sum(
            1
            for test_id in DEFAULT_TEST_ORDER
            for value in answers.get(test_id, [])
            if isinstance(value, int)
        )

    def _is_complete(self, answers: dict[str, list[int | None]]) -> bool:
        return self._count_answered(answers) == TOTAL_QUESTION_COUNT

    def _dump_json(self, payload: object) -> str:
        return json.dumps(payload, ensure_ascii=True)

    def _require_session(self, user_id: int, session_id: int) -> AssessmentSession:
        session_record = self.assessment_session_repository.get_by_id_for_user(user_id, session_id)
        if not session_record:
            raise HTTPException(status_code=404, detail="Assessment session not found.")
        return session_record

    def _validate_answer_patch(self, *, test_id: str, question_index: int, answer_value: int) -> str:
        normalized_test_id = test_id.lower()
        if normalized_test_id not in ASSESSMENT_DEFINITIONS:
            raise HTTPException(status_code=422, detail=f"Unsupported assessment '{test_id}'.")

        definition = ASSESSMENT_DEFINITIONS[normalized_test_id]
        if question_index >= definition["question_count"]:
            raise HTTPException(status_code=422, detail=f"Question index out of range for {normalized_test_id.upper()}.")
        if answer_value not in {0, 1, 2, 3}:
            raise HTTPException(status_code=422, detail="Answer value must be between 0 and 3.")
        return normalized_test_id

    def _normalize_resource_severity(self, severity: str) -> str:
        if severity == "moderately severe":
            return "severe"
        return severity


def get_assessment_service(session: Session = Depends(get_session)) -> AssessmentService:
    return AssessmentService(session)
