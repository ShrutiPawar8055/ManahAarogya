from datetime import datetime

from sqlmodel import Session, select

from app.database.models import CommunityCommentReddit, CommunityPostReddit, CommunityPostVote


class CommunityRepository:
    """Database operations for community posts and comments."""

    def __init__(self, session: Session) -> None:
        """Store the active database session."""
        self.session = session

    def list_posts(self, sort: str = "new", topic: str | None = None, q: str | None = None) -> list[CommunityPostReddit]:
        """Return posts sorted (new/top) with simple filtering."""
        statement = select(CommunityPostReddit)
        if topic:
            statement = statement.where(CommunityPostReddit.topic == topic)
        rows = list(self.session.exec(statement))
        if q:
            ql = q.lower()
            rows = [r for r in rows if ql in r.title.lower() or ql in r.content.lower()]
        if sort == "top":
            return sorted(rows, key=lambda item: (item.upvotes - item.downvotes, item.created_at), reverse=True)
        return sorted(rows, key=lambda item: item.created_at, reverse=True)

    def get_post(self, post_id: int) -> CommunityPostReddit | None:
        """Return a post by ID."""
        statement = select(CommunityPostReddit).where(CommunityPostReddit.id == post_id)
        return self.session.exec(statement).first()

    def create_post(self, post: CommunityPostReddit) -> CommunityPostReddit:
        """Insert a new post."""
        self.session.add(post)
        self.session.commit()
        self.session.refresh(post)
        return post

    def save_post(self, post: CommunityPostReddit) -> CommunityPostReddit:
        """Persist updates to a post."""
        post.updated_at = datetime.utcnow()
        self.session.add(post)
        self.session.commit()
        self.session.refresh(post)
        return post

    def create_comment(self, comment: CommunityCommentReddit) -> CommunityCommentReddit:
        """Insert a new comment."""
        self.session.add(comment)
        self.session.commit()
        self.session.refresh(comment)
        return comment

    def list_comments(self, post_id: int) -> list[CommunityCommentReddit]:
        """Return comments for one post."""
        statement = select(CommunityCommentReddit).where(CommunityCommentReddit.post_id == post_id)
        rows = list(self.session.exec(statement))
        return sorted(rows, key=lambda item: item.created_at)

    def get_vote(self, user_id: int, post_id: int) -> CommunityPostVote | None:
        statement = select(CommunityPostVote).where(
            CommunityPostVote.user_id == user_id, CommunityPostVote.post_id == post_id
        )
        return self.session.exec(statement).first()

    def upsert_vote(self, user_id: int, post_id: int, value: int) -> CommunityPostVote:
        vote = self.get_vote(user_id, post_id)
        if vote:
            vote.value = value
            self.session.add(vote)
            self.session.commit()
            self.session.refresh(vote)
            return vote
        vote = CommunityPostVote(user_id=user_id, post_id=post_id, value=value)
        self.session.add(vote)
        self.session.commit()
        self.session.refresh(vote)
        return vote
