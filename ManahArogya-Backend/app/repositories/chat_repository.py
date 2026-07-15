from sqlmodel import Session, select

from app.database.models import ChatConversation, ChatMessage


class ChatRepository:
    """Database operations for chat conversations and messages."""

    def __init__(self, session: Session) -> None:
        """Store the active database session."""
        self.session = session

    def list_conversations(self, user_id: int) -> list[ChatConversation]:
        """Return all conversations for a user."""
        statement = select(ChatConversation).where(ChatConversation.user_id == user_id)
        rows = list(self.session.exec(statement))
        return sorted(rows, key=lambda item: item.created_at, reverse=True)

    def get_conversation(self, user_id: int, conversation_id: int) -> ChatConversation | None:
        """Return one conversation scoped to user."""
        statement = select(ChatConversation).where(
            ChatConversation.user_id == user_id,
            ChatConversation.id == conversation_id,
        )
        return self.session.exec(statement).first()

    def create_conversation(self, user_id: int, title: str) -> ChatConversation:
        """Create a new conversation."""
        conversation = ChatConversation(user_id=user_id, title=title)
        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)
        return conversation

    def list_messages(self, conversation_id: int) -> list[ChatMessage]:
        """Return conversation messages in chronological order."""
        statement = select(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
        rows = list(self.session.exec(statement))
        return sorted(rows, key=lambda item: item.created_at)

    def create_message(self, conversation_id: int, sender: str, text: str) -> ChatMessage:
        """Insert a chat message."""
        message_record = ChatMessage(conversation_id=conversation_id, sender=sender, text=text)
        self.session.add(message_record)
        self.session.commit()
        self.session.refresh(message_record)
        return message_record
