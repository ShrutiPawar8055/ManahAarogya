from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CommunityPostCreateRequest(BaseModel):
    """Payload to create a community post."""

    title: str
    topic: str | None = None
    author: str
    role: str
    content: str


class CommunityCommentCreateRequest(BaseModel):
    """Payload to add a post comment."""

    content: str
    parent_id: int | None = None
    author: str | None = None


class CommunityVoteRequest(BaseModel):
    """Payload to vote on a post."""

    value: int


class CommunityPostResponse(BaseModel):
    """Community post response schema."""

    id: int
    user_id: int
    title: str
    topic: str
    author: str
    role: str
    content: str
    upvotes: int
    downvotes: int
    score: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommunityCommentResponse(BaseModel):
    """Community comment response schema."""

    id: int
    post_id: int
    user_id: int
    parent_id: int | None = None
    author: str | None = None
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
