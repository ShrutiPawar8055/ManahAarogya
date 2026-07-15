from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.schemas.community_schema import (
    CommunityCommentCreateRequest,
    CommunityPostCreateRequest,
    CommunityVoteRequest,
)
from app.services.auth_service import get_current_user
from app.services.ai_moderation_service import check_harmful_post
from app.services.community_service import CommunityService, get_community_service

router = APIRouter(prefix="/community", tags=["community"])


@router.get("/stats")
def stats(_user=Depends(get_current_user), service: CommunityService = Depends(get_community_service)):
    """Return community statistics."""
    return {"data": service.stats()}


@router.get("/posts")
def posts(
    sort: str = "new",
    topic: str | None = None,
    q: str | None = None,
    _user=Depends(get_current_user),
    service: CommunityService = Depends(get_community_service),
):
    """Return community posts (reddit-style)."""
    if sort not in ("new", "top"):
        sort = "new"
    return {"data": service.list_posts(sort=sort, topic=topic, q=q)}


@router.get("/posts/{post_id}")
def post_detail(post_id: int, _user=Depends(get_current_user), service: CommunityService = Depends(get_community_service)):
    """Return post with comments."""
    return {"data": service.get_post(post_id)}


@router.get("/groups")
def groups(_user=Depends(get_current_user), service: CommunityService = Depends(get_community_service)):
    """Return support groups."""
    return {"data": service.groups()}


@router.get("/mentors")
def mentors(_user=Depends(get_current_user), service: CommunityService = Depends(get_community_service)):
    """Return mentors."""
    return {"data": service.mentors()}


@router.post("/posts")
def create_post(payload: CommunityPostCreateRequest, background_tasks: BackgroundTasks, user=Depends(get_current_user), service: CommunityService = Depends(get_community_service)):
    """Create a new community post."""
    if not payload.content.strip():
        raise HTTPException(status_code=422, detail="Content cannot be empty.")
    if not payload.title.strip():
        raise HTTPException(status_code=422, detail="Title cannot be empty.")
    post = service.create_post(
        user.id,
        payload.title.strip(),
        (payload.topic or "general"),
        payload.author,
        payload.role,
        payload.content.strip(),
    )
    
    background_tasks.add_task(check_harmful_post, post.id)
    
    return {"data": post}


@router.post("/posts/{post_id}/vote")
def vote_post(
    post_id: int,
    payload: CommunityVoteRequest,
    user=Depends(get_current_user),
    service: CommunityService = Depends(get_community_service),
):
    """Upvote/downvote/clear vote on a post."""
    return {"data": service.vote_post(post_id, user.id, payload.value)}


@router.post("/posts/{post_id}/comments")
def add_comment(post_id: int, payload: CommunityCommentCreateRequest, user=Depends(get_current_user), service: CommunityService = Depends(get_community_service)):
    """Add comment to post (supports threading via parent_id)."""
    if not payload.content.strip():
        raise HTTPException(status_code=422, detail="Reply cannot be empty.")
    post = service.add_comment(post_id, user.id, payload.content.strip(), parent_id=payload.parent_id, author=payload.author)
    return {"data": post}
