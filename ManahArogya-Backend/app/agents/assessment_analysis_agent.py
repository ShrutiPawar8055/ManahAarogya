from __future__ import annotations

import json
from typing import TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from app.core.config import settings
from app.core.logging import logger
from app.schemas.assessment_schema import (
    ActivitySnapshot,
    AssessmentScoreCard,
    AssessmentTrendEntry,
    RecommendedAction,
    StructuredAssessmentFeedback,
)


class AssessmentAnalysisState(TypedDict):
    score_cards: list[AssessmentScoreCard]
    activity_snapshot: ActivitySnapshot
    previous_assessments: list[AssessmentTrendEntry]
    risk_flags: dict[str, object]
    trend_comparison: str
    feedback: StructuredAssessmentFeedback


class AssessmentAnalysisAgent:
    """Generate structured post-assessment feedback using LangGraph."""

    def __init__(self) -> None:
        self.model = self._build_model()
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a careful mental health triage assistant for a wellness app.\n"
                    "Use only the supplied structured data.\n"
                    "Do not diagnose. Do not invent facts. Keep recommendations specific and safe.\n"
                    "If the risk flags indicate urgent support, set needs_urgent_support=true, keep risk_level='high', "
                    "and include a concrete safety_plan.\n"
                    "Make recommended_actions practical and short.",
                ),
                (
                    "human",
                    "Score cards:\n{score_cards}\n\n"
                    "Activity snapshot:\n{activity_snapshot}\n\n"
                    "Previous assessments:\n{previous_assessments}\n\n"
                    "Risk flags:\n{risk_flags}\n\n"
                    "Trend comparison:\n{trend_comparison}",
                ),
            ]
        )
        self.workflow = self._build_graph()

    def _build_model(self) -> ChatOpenAI | None:
        if not settings.cerebras_api_key:
            logger.warning("CEREBRAS_API_KEY is missing. Assessment analysis will use deterministic fallback.")
            return None

        return ChatOpenAI(
            api_key=settings.cerebras_api_key,
            base_url=settings.cerebras_base_url,
            model=settings.cerebras_model,
            temperature=0.2,
        )

    def _build_graph(self):
        graph = StateGraph(AssessmentAnalysisState)
        graph.add_node("analyze_trend", self._analyze_trend)
        graph.add_node("generate_feedback", self._generate_feedback)
        graph.add_edge(START, "analyze_trend")
        graph.add_edge("analyze_trend", "generate_feedback")
        graph.add_edge("generate_feedback", END)
        return graph.compile()

    def _analyze_trend(self, state: AssessmentAnalysisState) -> dict[str, object]:
        scores = state["score_cards"]
        previous = state["previous_assessments"]
        if not previous:
            return {"trend_comparison": "This is the first completed assessment session, so there is no prior trend baseline yet."}

        latest_by_test = {entry.test_id: entry for entry in previous}
        comparisons: list[str] = []
        for score in scores:
            prior = latest_by_test.get(score.test_id)
            if not prior:
                continue
            delta = score.score - prior.score
            if delta == 0:
                direction = "unchanged"
            elif delta > 0:
                direction = f"up by {delta} points"
            else:
                direction = f"down by {abs(delta)} points"
            comparisons.append(f"{score.title} is {direction} versus the previous completed check-in.")

        if not comparisons:
            return {"trend_comparison": "Previous assessment history exists, but a direct test-by-test comparison was not available."}
        return {"trend_comparison": " ".join(comparisons)}

    def _generate_feedback(self, state: AssessmentAnalysisState) -> dict[str, object]:
        if not self.model:
            return {"feedback": self._build_fallback_feedback(state)}

        structured_model = self.model.with_structured_output(StructuredAssessmentFeedback)
        chain = self.prompt | structured_model
        try:
            feedback = chain.invoke(
                {
                    "score_cards": json.dumps([item.model_dump(mode="json") for item in state["score_cards"]], ensure_ascii=True),
                    "activity_snapshot": state["activity_snapshot"].model_dump_json(),
                    "previous_assessments": json.dumps(
                        [item.model_dump(mode="json") for item in state["previous_assessments"]],
                        ensure_ascii=True,
                    ),
                    "risk_flags": json.dumps(state["risk_flags"], ensure_ascii=True),
                    "trend_comparison": state["trend_comparison"],
                }
            )
            return {"feedback": feedback}
        except Exception as exc:
            logger.warning("Structured assessment generation failed, using fallback: {}", str(exc))
            return {"feedback": self._build_fallback_feedback(state)}

    def _build_fallback_feedback(self, state: AssessmentAnalysisState) -> StructuredAssessmentFeedback:
        scores = state["score_cards"]
        snapshot = state["activity_snapshot"]
        risk_flags = state["risk_flags"]
        risk_level = str(risk_flags.get("risk_level") or "low")
        urgent = bool(risk_flags.get("needs_urgent_support"))

        score_summary = ", ".join(
            f"{item.title} {item.score} ({item.severity.replace('_', ' ')})"
            for item in scores
        ) or "No score data was available."

        key_findings = [
            f"Latest scores: {score_summary}.",
        ]
        if snapshot.mood_avg_7d is not None:
            key_findings.append(
                f"Recent mood average is {snapshot.mood_avg_7d}/10 with a '{snapshot.mood_trend}' trend."
            )
        if snapshot.habit_total:
            key_findings.append(
                f"Habit completion is {snapshot.habit_completed}/{snapshot.habit_total} in the current tracker snapshot."
            )

        contributing_factors: list[str] = []
        if snapshot.mood_trend == "declining":
            contributing_factors.append("Mood check-ins are trending downward, which can amplify anxiety and low-energy patterns.")
        if snapshot.habit_completion_rate is not None and snapshot.habit_completion_rate < 40:
            contributing_factors.append("Low habit completion suggests routines may not be stabilizing symptoms consistently.")
        if snapshot.chatbot_messages_last_14d >= 12:
            contributing_factors.append("High recent assistant usage may indicate elevated need for support or reassurance.")
        if snapshot.appointment_pending > 0:
            contributing_factors.append("Pending appointments suggest support planning may still be in progress.")
        if not contributing_factors:
            contributing_factors.append("Recent platform activity does not show a single dominant stressor, so the picture is mixed rather than driven by one signal.")

        recommended_actions = [
            RecommendedAction(
                title="Retain one daily stabilizer",
                rationale="Choose one repeatable habit or exercise so the next assessment reflects a consistent routine.",
                priority="high" if risk_level != "low" else "medium",
            ),
            RecommendedAction(
                title="Add one short written check-in",
                rationale="A brief mood note improves context for the next structured analysis.",
                priority="medium",
            ),
            RecommendedAction(
                title="Review one recommended resource",
                rationale="The resource list is already aligned to current severity and recent behavior.",
                priority="medium",
            ),
        ]

        follow_up_questions = [
            "Which situations have felt most difficult since the previous assessment?",
            "What time of day or activity pattern seems to worsen symptoms most?",
        ]

        clinician_flags: list[str] = []
        if urgent:
            clinician_flags.append("High-risk screening indicators were detected and should be reviewed promptly.")
        if risk_flags.get("repeated_elevated_scores"):
            clinician_flags.append("Moderate or higher symptoms have persisted across multiple check-ins.")
        if risk_flags.get("phq9_item9_flag"):
            clinician_flags.append("The PHQ-9 self-harm item was elevated in this session.")

        safety_plan: list[str] = []
        if urgent:
            safety_plan = [
                "Contact a trusted person or a local emergency resource right away if you feel at risk of harming yourself.",
                "Do not stay isolated while the risk feels active.",
                "Seek immediate in-person professional support if thoughts of self-harm are intensifying.",
            ]
            recommended_actions.insert(
                0,
                RecommendedAction(
                    title="Use urgent human support now",
                    rationale="The current screening result crosses the threshold where immediate human support matters more than self-guided steps.",
                    priority="critical",
                ),
            )

        suggested_topics = [
            "symptom triggers",
            "sleep and recovery",
            "routine consistency",
        ]
        if snapshot.mood_trend == "declining":
            suggested_topics[0] = "recent decline in mood"
        if risk_level == "high":
            suggested_topics.append("safety planning")

        overall_summary = (
            f"The latest assessment shows {risk_level} current concern based on {score_summary}. "
            f"{state['trend_comparison']}"
        )

        ui_summary = "Structured feedback updated from your latest assessment and recent platform activity."
        if urgent:
            ui_summary = "High-risk signals detected. Prioritize human support and safety planning now."

        risk_rationale = str(risk_flags.get("risk_rationale") or "Risk was determined from score severity and recent support signals.")

        return StructuredAssessmentFeedback(
            overall_summary=overall_summary,
            ui_summary=ui_summary,
            risk_level=risk_level,
            risk_rationale=risk_rationale,
            key_findings=key_findings,
            contributing_factors=contributing_factors,
            trend_comparison=state["trend_comparison"],
            recommended_actions=recommended_actions,
            follow_up_questions=follow_up_questions,
            clinician_flags=clinician_flags,
            suggested_topics=suggested_topics,
            safety_plan=safety_plan,
            needs_urgent_support=urgent,
        )

    def run(
        self,
        *,
        score_cards: list[AssessmentScoreCard],
        activity_snapshot: ActivitySnapshot,
        previous_assessments: list[AssessmentTrendEntry],
        risk_flags: dict[str, object],
    ) -> StructuredAssessmentFeedback:
        initial_state: AssessmentAnalysisState = {
            "score_cards": score_cards,
            "activity_snapshot": activity_snapshot,
            "previous_assessments": previous_assessments,
            "risk_flags": risk_flags,
            "trend_comparison": "",
            "feedback": StructuredAssessmentFeedback(),
        }
        result = self.workflow.invoke(initial_state)
        feedback = result.get("feedback")
        if isinstance(feedback, StructuredAssessmentFeedback):
            return feedback
        return self._build_fallback_feedback(initial_state)


assessment_analysis_agent = AssessmentAnalysisAgent()
