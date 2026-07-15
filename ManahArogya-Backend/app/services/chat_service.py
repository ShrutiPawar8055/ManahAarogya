import json

from fastapi import Depends, HTTPException
from sqlmodel import Session

from app.agents.chat_agent import chat_agent
from app.agents.tools import TOOL_REGISTRY, ToolContext
from app.database.db import get_session
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.habit_repository import HabitRepository
from app.repositories.mood_repository import MoodRepository
from app.repositories.user_profile_repository import UserProfileRepository


class ChatService:
    """Business logic for AI chatbot conversations."""

    def __init__(self, session: Session) -> None:
        """Create service with repository dependencies."""
        self.session = session
        self.chat_repository = ChatRepository(session)
        self.assessment_repository = AssessmentRepository(session)
        self.habit_repository = HabitRepository(session)
        self.user_profile_repository = UserProfileRepository(session)
        self.mood_repository = MoodRepository(session)

    def list_conversations(self, user_id: int):
        """Return all user conversations."""
        return self.chat_repository.list_conversations(user_id)

    def create_conversation(self, user_id: int, title: str | None):
        """Create one conversation for a user."""
        conversation_title = title or "New Conversation"
        return self.chat_repository.create_conversation(user_id, conversation_title)

    def list_messages(self, user_id: int, conversation_id: int):
        """Return messages for one conversation."""
        conversation = self.chat_repository.get_conversation(user_id, conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        return self.chat_repository.list_messages(conversation_id)

    async def send_message(self, user_id: int, conversation_id: int, text: str) -> dict[str, object]:
        """Save user message, generate AI reply, optionally execute tools, and save response."""
        conversation = self.chat_repository.get_conversation(user_id, conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found.")

        self.chat_repository.create_message(conversation_id, "user", text)
        history = self.chat_repository.list_messages(conversation_id)
        history_rows = [{"sender": item.sender, "text": item.text} for item in history]

        tool_context = self._build_behavior_context(user_id)
        if tool_context:
            history_rows.insert(0, {"sender": "tool_context", "text": tool_context})

        assistant_text = chat_agent.run(user_message=text, history=history_rows)

        tool_ctx = ToolContext(user_id, self.session)
        # Follow up on a single tool call and add result to the context
        for _ in range(3):
            tool_call = self._extract_tool_call(assistant_text)
            if not tool_call:
                break

            call_name = str(tool_call.get("name") or "").strip()
            args = tool_call.get("args") or {}
            tool_fn = TOOL_REGISTRY.get(call_name)
            
            history_rows.append(
                {
                    "sender": "assistant",
                    "text": assistant_text,
                }
            )

            if not tool_fn:
                assistant_text += f"\n[ERROR] Unknown tool: {call_name}"
                history_rows.append(
                    {
                        "sender": "tool",
                        "text": f"TOOL_RESULT {call_name}: {{\"error\": \"Unknown tool\"}}",
                    }
                )
                assistant_text = chat_agent.run(user_message=text, history=history_rows)
                continue

            try:
                result = tool_fn(tool_ctx, args)
            except Exception as exc:
                assistant_text += f"\n[ERROR] Tool {call_name} failed: {str(exc)}"
                history_rows.append(
                    {
                        "sender": "tool",
                        "text": f"TOOL_RESULT {call_name}: {{\"error\": {json.dumps(str(exc))}}}",
                    }
                )
                assistant_text = chat_agent.run(user_message=text, history=history_rows)
                continue

            history_rows.append(
                {
                    "sender": "tool",
                    "text": f"TOOL_RESULT {call_name}: {json.dumps(result, ensure_ascii=True)}",
                }
            )
            assistant_text = chat_agent.run(user_message=text, history=history_rows)

        assistant_message = self.chat_repository.create_message(conversation_id, "assistant", assistant_text)
        return {"conversation_id": conversation_id, "response": assistant_message}

    async def stream_message(self, user_id: int, conversation_id: int, text: str):
        """Yield structured chat events for SSE streaming with tool calls."""
        conversation = self.chat_repository.get_conversation(user_id, conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found.")

        self.chat_repository.create_message(conversation_id, "user", text)

        history = self.chat_repository.list_messages(conversation_id)
        history_rows = [{"sender": item.sender, "text": item.text} for item in history]

        tool_ctx = ToolContext(user_id, self.session)

        for _ in range(3):
            pending = ""
            tool_detected = False
            tool_call = None
            
            async for chunk in chat_agent.astream(user_message=text, history=history_rows):
                pending += str(chunk)

                while "\n" in pending:
                    line, pending = pending.split("\n", 1)
                    stripped = line.strip()

                    if not stripped:
                        # preserve full newline boundary as a small delta
                        yield {"event": "message_delta", "data": {"delta": "\n"}}
                        continue

                    try:
                        obj = json.loads(stripped)
                        if isinstance(obj, dict) and isinstance(obj.get("tool_call"), dict):
                            tool_call = obj.get("tool_call")
                    except Exception:
                        pass

                    if tool_call:
                        tool_detected = True
                        break

                    # Not a tool call: stream as assistant text.
                    yield {"event": "message_delta", "data": {"delta": line + "\n"}}
                
                if tool_detected:
                    break

            if not tool_detected and pending:
                stripped = pending.strip()
                if stripped:
                    try:
                        obj = json.loads(stripped)
                        if isinstance(obj, dict) and isinstance(obj.get("tool_call"), dict):
                            tool_call = obj.get("tool_call")
                            tool_detected = True
                    except Exception:
                        pass
                
                if not tool_detected:
                    yield {"event": "message_delta", "data": {"delta": pending}}

            if not tool_detected:
                # Flow naturally ended without calling a tool
                break

            name = str(tool_call.get("name") or "").strip()
            args = tool_call.get("args") or {}
            tool_fn = TOOL_REGISTRY.get(name)
            
            history_rows.append({"sender": "assistant", "text": json.dumps({"tool_call": tool_call})})

            if not tool_fn:
                # Unknown tool name
                yield {
                    "event": "tool_call",
                    "data": {"tool_name": name, "args": args, "call_id": "", "ok": False, "result": {"error": "Unknown tool"}},
                }
                history_rows.append({"sender": "tool", "text": f"TOOL_RESULT {name}: {{\"error\": \"Unknown tool\"}}"})
                continue

            call_id = f"{name}-{user_id}-{conversation_id}"
            yield {
                "event": "tool_call",
                "data": {"tool_name": name, "args": args, "call_id": call_id},
            }
            try:
                result = tool_fn(tool_ctx, args)
                ok = True
            except Exception as exc:
                ok = False
                result = {"error": str(exc)}

            yield {
                "event": "tool_result",
                "data": {"call_id": call_id, "ok": ok, "result": result},
            }

            history_rows.append(
                {
                    "sender": "tool",
                    "text": f"TOOL_RESULT {name}: {json.dumps(result, ensure_ascii=True)}",
                }
            )

    def _build_behavior_context(self, user_id: int) -> str:
        """Aggregate user behavior snapshot similar to internal tool output."""
        profile = self.user_profile_repository.get_by_user_id(user_id)
        assessments = self.assessment_repository.list_by_user(user_id)[:3]
        habits = self.habit_repository.list_by_user(user_id)[:8]
        moods = self.mood_repository.list_by_user(user_id, limit=7)

        problems = []
        if profile and profile.current_problems_json:
            try:
                parsed = json.loads(profile.current_problems_json)
                if isinstance(parsed, list):
                    problems = parsed[:5]
            except Exception:
                problems = []
        if not problems:
            problems = [{"name": item.test_id.upper(), "severity": item.severity} for item in assessments]

        mood_scores = [item.mood_score for item in moods]
        mood_avg = round(sum(mood_scores) / len(mood_scores), 2) if mood_scores else None
        completed = sum(1 for item in habits if item.done)

        payload = {
            "risk_level": profile.risk_level if profile else "low",
            "mood_trend": profile.mood_trend if profile else "unknown",
            "mood_avg_7d": mood_avg,
            "problems": problems,
            "habit_summary": {
                "total": len(habits),
                "completed": completed,
                "items": [
                    {
                        "title": item.title,
                        "category": item.category,
                        "done": item.done,
                    }
                    for item in habits
                ],
            },
        }
        return f"USER_BEHAVIOR_CONTEXT: {json.dumps(payload, ensure_ascii=True)}"

    def _build_tool_snapshot(self, user_id: int) -> dict[str, object]:
        """Return a safe, UI-friendly snapshot for tool events."""
        profile = self.user_profile_repository.get_by_user_id(user_id)
        assessments = self.assessment_repository.list_by_user(user_id)[:3]
        habits = self.habit_repository.list_by_user(user_id)[:8]
        moods = self.mood_repository.list_by_user(user_id, limit=7)

        mood_scores = [item.mood_score for item in moods]
        mood_avg = round(sum(mood_scores) / len(mood_scores), 2) if mood_scores else None
        completed = sum(1 for item in habits if item.done)

        problems = []
        if profile and profile.current_problems_json:
            try:
                parsed = json.loads(profile.current_problems_json)
                if isinstance(parsed, list):
                    problems = parsed[:5]
            except Exception:
                problems = []
        if not problems:
            problems = [{"name": item.test_id.upper(), "severity": item.severity} for item in assessments]

        return {
            "risk_level": profile.risk_level if profile else "low",
            "mood_trend": profile.mood_trend if profile else "unknown",
            "mood_avg_7d": mood_avg,
            "problems": problems,
            "habits": [{"title": item.title, "category": item.category, "done": item.done} for item in habits],
            "habit_completion": {"total": len(habits), "completed": completed},
        }

    def _extract_tool_call(self, text: str) -> dict[str, object] | None:
        """Detect a single tool_call JSON object in agent response text."""
        if not text:
            return None

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and isinstance(obj.get("tool_call"), dict):
                return obj["tool_call"]

        return None


def get_chat_service(session: Session = Depends(get_session)) -> ChatService:
    """FastAPI dependency for ChatService."""
    return ChatService(session)
