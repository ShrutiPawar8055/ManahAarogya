from fastapi import Depends, HTTPException
from sqlmodel import Session

from app.database.db import get_session
from app.database.models import CommunityCommentReddit, CommunityPostReddit
from app.repositories.community_repository import CommunityRepository


class CommunityService:
    """Business logic for community posts and replies."""

    def __init__(self, session: Session) -> None:
        """Create service with repository dependencies."""
        self.community_repository = CommunityRepository(session)

    def list_posts(self, sort: str = "new", topic: str | None = None, q: str | None = None):
        """Return all community posts."""
        return [self._serialize_post(item) for item in self.community_repository.list_posts(sort=sort, topic=topic, q=q)]

    def get_post(self, post_id: int):
        record = self.community_repository.get_post(post_id)
        if not record:
            raise HTTPException(status_code=404, detail="Post not found.")
        return {"post": self._serialize_post(record), "comments": self.list_comments(post_id)}

    def create_post(self, user_id: int, title: str, topic: str, author: str, role: str, content: str):
        """Create one community post."""
        post_record = CommunityPostReddit(
            user_id=user_id,
            title=title.strip() or "Untitled",
            topic=(topic.strip() or "general").lower(),
            author=author,
            role=role,
            content=content,
        )
        created = self.community_repository.create_post(post_record)
        return self._serialize_post(created)

    def vote_post(self, post_id: int, user_id: int, value: int):
        """Apply per-user vote and update aggregate counts."""
        post_record = self.community_repository.get_post(post_id)
        if not post_record:
            raise HTTPException(status_code=404, detail="Post not found.")
        value = int(value)
        if value not in (-1, 0, 1):
            raise HTTPException(status_code=422, detail="Vote value must be -1, 0, or 1.")

        existing = self.community_repository.get_vote(user_id, post_id)
        prev = int(existing.value) if existing else 0
        if prev == value:
            return self._serialize_post(post_record)

        # Remove previous vote
        if prev == 1:
            post_record.upvotes = max(0, post_record.upvotes - 1)
        elif prev == -1:
            post_record.downvotes = max(0, post_record.downvotes - 1)

        # Apply new vote
        if value == 1:
            post_record.upvotes += 1
        elif value == -1:
            post_record.downvotes += 1

        self.community_repository.upsert_vote(user_id, post_id, value)
        saved = self.community_repository.save_post(post_record)
        return self._serialize_post(saved)

    def add_comment(self, post_id: int, user_id: int, content: str, parent_id: int | None = None, author: str | None = None):
        """Add comment to a post."""
        post_record = self.community_repository.get_post(post_id)
        if not post_record:
            raise HTTPException(status_code=404, detail="Post not found.")
        comment = CommunityCommentReddit(
            post_id=post_id,
            user_id=user_id,
            parent_id=parent_id,
            author=author,
            content=content,
        )
        self.community_repository.create_comment(comment)
        return self._serialize_post(post_record)

    def list_comments(self, post_id: int) -> list[dict[str, object]]:
        rows = self.community_repository.list_comments(post_id)
        return [
            {
                "id": item.id,
                "post_id": item.post_id,
                "user_id": item.user_id,
                "parent_id": item.parent_id,
                "author": item.author,
                "content": item.content,
                "created_at": item.created_at.isoformat(),
            }
            for item in rows
        ]

    def stats(self) -> dict[str, int]:
        """Return aggregate community numbers."""
        posts = self.community_repository.list_posts()
        comment_count = sum(len(self.community_repository.list_comments(post.id)) for post in posts if post.id)
        return {"posts": len(posts), "comments": comment_count}

    def groups(self) -> list[dict[str, str]]:
        """Return available peer groups."""
        return [
            {"id": 1, "name": "Exam Stress Circle", "members": 24, "next": "Saturday 6:00 PM"},
            {"id": 2, "name": "Sleep Recovery Group", "members": 18, "next": "Sunday 8:00 PM"},
        ]

    def mentors(self) -> list[dict[str, str]]:
        """Return available student mentors."""
        return [
            {"id": 1, "name": "Arjun", "specialty": "Burnout"},
            {"id": 2, "name": "Mira", "specialty": "Routine Building"},
        ]

    def _serialize_post(self, post: CommunityPostReddit) -> dict[str, object]:
        comments = self.community_repository.list_comments(post.id)
        return {
            "id": post.id,
            "user_id": post.user_id,
            "title": post.title,
            "topic": post.topic,
            "author": post.author,
            "role": post.role,
            "content": post.content,
            "upvotes": post.upvotes,
            "downvotes": post.downvotes,
            "score": int(post.upvotes) - int(post.downvotes),
            "comments": len(comments),
            "time": post.created_at.strftime("%b %d, %I:%M %p"),
            "created_at": post.created_at.isoformat(),
            "updated_at": post.updated_at.isoformat() if getattr(post, "updated_at", None) else post.created_at.isoformat(),
        }


def get_community_service(session: Session = Depends(get_session)) -> CommunityService:
    """FastAPI dependency for CommunityService."""
    return CommunityService(session)
