from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConversationCreateRequest(BaseModel):
    """Payload to create a chat conversation."""

    title: str | None = None


class MessageCreateRequest(BaseModel):
    """Payload for user chat message."""

    text: str


class ConversationResponse(BaseModel):
    """Chat conversation response model."""

    id: int
    user_id: int
    title: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Chat message response model."""

    id: int
    conversation_id: int
    sender: str
    text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
