from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings


class HabitCoachAgent:
    """Small coaching agent that gives practical habit guidance."""

    def __init__(self) -> None:
        """Prepare prompt and model."""
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a habit coach for students. Offer one clear next step."),
                ("human", "Habit summary:\n{habit_summary}\n\nUser message:\n{user_message}"),
            ]
        )
        self.parser = StrOutputParser()
        self.model = self._build_model()

    def _build_model(self) -> ChatOpenAI | None:
        """Build Cerebras model client when possible."""
        if not settings.cerebras_api_key:
            return None
        return ChatOpenAI(
            api_key=settings.cerebras_api_key,
            base_url=settings.cerebras_base_url,
            model=settings.cerebras_model,
            temperature=0.2,
        )

    def run(self, user_message: str, habit_summary: str) -> str:
        """Return coaching text for current habits."""
        if not self.model:
            return "Start with one 2-minute habit today and repeat it at the same time tomorrow."
        chain = self.prompt | self.model | self.parser
        response_text = chain.invoke({"habit_summary": habit_summary, "user_message": user_message})
        return response_text.strip()


habit_coach_agent = HabitCoachAgent()
