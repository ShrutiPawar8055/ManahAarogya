from __future__ import annotations

from typing import AsyncIterator, TypedDict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from app.core.config import settings
from app.core.logging import logger


class ChatState(TypedDict):
    """State object passed through the LangGraph pipeline."""

    user_message: str
    history: list[dict[str, str]]
    response_text: str


class ChatAgent:
    """Chat assistant backed by LangChain and LangGraph."""

    def __init__(self) -> None:
        """Initialize prompt and model client."""
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are Zenith, a flagship, highly intelligent, action-oriented mental wellness assistant.\n"
                    "Keep your responses practical, warm, and highly engaging. Actively assist the user instead of just talking.\n"
                    "You have access to the following tools:\n"
                    "- `get_current_time`: Returns the exact current date, time, and timezone.\n"
                    "- `get_latest_mood`: Returns the user's most recent mood score and notes.\n"
                    "- `get_mood_history`: Returns a list of the user's recent moods (accepts optional 'limit').\n"
                    "- `get_habits_overview`: Returns a statistical breakdown of the user's habits.\n"
                    "- `get_recent_assessments`: Returns the user's recent mental health checkups.\n"
                    "- `get_community_stats`: Returns community engagement statistics.\n"
                    "- `get_profile_snapshot`: Returns high-level user behavioral insights.\n"
                    "- `create_new_habit`: Creates a new habit for the user. Requires 'title' and 'category'.\n"
                    "- `mark_habit_complete`: Marks an existing habit as done. Requires 'habit_id'.\n"
                    "- `trigger_breathing_exercise`: Triggers an interactive breathing UI widget for the user in panic or high stress.\n"
                    "- `get_grounding_technique`: Triggers a 5-4-3-2-1 visual grounding UI widget for the user in panic or high stress.\n\n"
                    "You can request these tools by emitting ONLY a single JSON object on its own line, for example:\n"
                    '{{"tool_call": {{"name": "create_new_habit", "args": {{"title": "Drink water", "category": "wellbeing"}}}}}}\n\n'
                    "When using a tool, you may say something brief like 'Let me set that up for you...' inline, but make sure to emit the JSON right after.\n"
                    "When tool_results are added to history, use them to personalize the answer.\n"
                    "Do not keep calling tools forever; stop once you have enough context.",
                ),
                ("human", "Conversation history:\n{history}\n\nUser message:\n{user_message}"),
            ]
        )
        self.parser = StrOutputParser()
        self.model = self._build_model()
        self.workflow = self._build_graph()

    def _build_model(self) -> ChatOpenAI | None:
        """Create Cerebras chat model client when credentials are present."""
        if not settings.cerebras_api_key:
            logger.warning("CEREBRAS_API_KEY is missing. Chat agent will use fallback responses.")
            return None
        return ChatOpenAI(
            api_key=settings.cerebras_api_key,
            base_url=settings.cerebras_base_url,
            model=settings.cerebras_model,
            temperature=0.3,
        )

    def _build_graph(self):
        """Create a simple retrieve-generate-save LangGraph."""
        graph_builder = StateGraph(ChatState)
        graph_builder.add_node("retrieve_history", self._retrieve_history)
        graph_builder.add_node("generate_response", self._generate_response)
        graph_builder.add_edge(START, "retrieve_history")
        graph_builder.add_edge("retrieve_history", "generate_response")
        graph_builder.add_edge("generate_response", END)
        return graph_builder.compile()

    def _retrieve_history(self, state: ChatState) -> dict:
        """Prepare history window before response generation."""
        # FIX 2: Return only the dictionary keys you want to update in the state
        return {"history": state["history"][-10:]}

    def _history_as_text(self, history: list[dict[str, str]]) -> str:
        """Render history into plain text for the prompt."""
        if not history:
            return "No previous messages."
        lines: list[str] = []
        for message_record in history[-10:]:
            lines.append(f"{message_record['sender']}: {message_record['text']}")
        return "\n".join(lines)

    def _generate_response(self, state: ChatState) -> dict:
        """Generate assistant response from current state."""
        if not self.model:
            return {"response_text": "I am here with you. Try one small grounding exercise: inhale for 4 seconds, exhale for 6 seconds, for one minute."}

        history_text = self._history_as_text(state["history"])
        chain = self.prompt | self.model | self.parser
        response_text = chain.invoke({"history": history_text, "user_message": state["user_message"]})
        
        # FIX 2: Return only the dictionary keys you want to update in the state
        return {"response_text": response_text.strip()}

    def run(self, user_message: str, history: list[dict[str, str]]) -> str:
        """Run the graph and return the response text."""
        initial_state: ChatState = {
            "user_message": user_message,
            "history": history,
            "response_text": "",
        }
        result_state = self.workflow.invoke(initial_state)
        response_text = result_state["response_text"]
        logger.info("AI response generated: {}", response_text)
        return response_text

    async def astream(self, user_message: str, history: list[dict[str, str]]) -> AsyncIterator[str]:
        """Stream the response text incrementally as deltas."""
        if not self.model:
            fallback = (
                "I am here with you. Try one small grounding exercise: inhale for 4 seconds, "
                "exhale for 6 seconds, for one minute."
            )
            for i in range(0, len(fallback), 24):
                yield fallback[i : i + 24]
            return

        history_text = self._history_as_text(history)
        messages = self.prompt.format_messages(history=history_text, user_message=user_message)
        try:
            async for chunk in self.model.astream(messages):
                delta = getattr(chunk, "content", None)
                if not delta:
                    continue
                yield str(delta)
        except Exception as exc:
            logger.exception("Streaming generation failed: {}", str(exc))
            raise


chat_agent = ChatAgent()