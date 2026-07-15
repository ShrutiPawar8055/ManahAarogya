from sqlmodel import Session

from app.agents.chat_agent import chat_agent
from app.core.logging import logger
from app.database.db import engine
from app.database.models import Alert, CommunityPostReddit


def check_suicidal_language(user_id: int, text: str):
    """Evaluate text for suicidal language and create an alert if detected."""
    prompt = f"Does the following text strongly indicate suicidal intent, self-harm, or a severe crisis? Answer with strictly 'YES' or 'NO'. Text: '{text}'"
    try:
        response = chat_agent.run(user_message=prompt, history=[])
        if "YES" in response.upper():
            logger.warning(f"Suicidal language detected for user {user_id}")
            with Session(engine) as session:
                alert = Alert(
                    user_id=user_id,
                    type="suicidal_language",
                    details=text[:255]
                )
                session.add(alert)
                session.commit()
    except Exception as e:
        logger.error(f"Failed to check suicidal language: {e}")


def check_harmful_post(post_id: int):
    """Evaluate community post for harmful or abusive content."""
    try:
        with Session(engine) as session:
            post = session.get(CommunityPostReddit, post_id)
            if not post:
                return
            prompt = f"Does the following community post contain harmful, severely abusive, or highly inappropriate content that violates safety guidelines? Answer with strictly 'YES' or 'NO'. Title: '{post.title}' Content: '{post.content}'"
            response = chat_agent.run(user_message=prompt, history=[])
            if "YES" in response.upper():
                logger.warning(f"Harmful content detected in post {post_id}")
                post.is_flagged = True
                post.is_approved = False
                session.add(post)
                session.commit()
    except Exception as e:
        logger.error(f"Failed to check harmful post: {e}")
