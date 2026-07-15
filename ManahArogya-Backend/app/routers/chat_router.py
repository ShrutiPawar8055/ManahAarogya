import json
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat_schema import ConversationCreateRequest, MessageCreateRequest
from app.services.ai_moderation_service import check_suicidal_language
from app.services.auth_service import get_current_user
from app.services.chat_service import ChatService, get_chat_service

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.get("/conversations")
def list_conversations(user=Depends(get_current_user), service: ChatService = Depends(get_chat_service)):
    """Return all user conversations."""
    return {"data": service.list_conversations(user.id)}


@router.post("/conversations")
def create_conversation(payload: ConversationCreateRequest, user=Depends(get_current_user), service: ChatService = Depends(get_chat_service)):
    """Create a conversation."""
    return {"data": service.create_conversation(user.id, payload.title)}


@router.get("/conversations/{conversation_id}/messages")
def list_messages(conversation_id: int, user=Depends(get_current_user), service: ChatService = Depends(get_chat_service)):
    """Return messages for one conversation."""
    return {"data": service.list_messages(user.id, conversation_id)}


@router.post("/conversations/{conversation_id}/messages")
async def send_message(conversation_id: int, payload: MessageCreateRequest, background_tasks: BackgroundTasks, user=Depends(get_current_user), service: ChatService = Depends(get_chat_service)):
    """Send user message and get assistant reply."""
    if not payload.text.strip():
        raise HTTPException(status_code=422, detail="Message text is required.")
    
    background_tasks.add_task(check_suicidal_language, user.id, payload.text.strip())
    
    return {"data": await service.send_message(user.id, conversation_id, payload.text.strip())}


@router.post("/conversations/{conversation_id}/messages/stream")
async def stream_message(
    conversation_id: int,
    payload: MessageCreateRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    """Send user message and stream assistant reply as SSE."""
    text = payload.text.strip() if payload and payload.text else ""
    if not text:
        raise HTTPException(status_code=422, detail="Message text is required.")
        
    background_tasks.add_task(check_suicidal_language, user.id, text)

    async def event_gen():
        started_at = datetime.now(timezone.utc).isoformat()
        assistant_text_parts: list[str] = []

        def sse(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

        yield sse("message_start", {"conversation_id": conversation_id, "started_at": started_at})
        try:
            async for item in service.stream_message(user.id, conversation_id, text):
                event = item.get("event")
                data = item.get("data", {})
                if event == "message_delta":
                    delta = (data or {}).get("delta") or ""
                    if delta:
                        assistant_text_parts.append(delta)
                yield sse(event or "message_delta", data if isinstance(data, dict) else {"value": data})
        except Exception as exc:
            yield sse("error", {"detail": str(exc) or "Streaming failed"})
            return

        final_text = "".join(assistant_text_parts).strip()
        if final_text:
            service.chat_repository.create_message(conversation_id, "assistant", final_text)
        yield sse("message_end", {"conversation_id": conversation_id, "text": final_text})

    return StreamingResponse(event_gen(), media_type="text/event-stream")
