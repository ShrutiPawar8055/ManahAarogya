from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.emotion_schema import EmotionAnalyzeRequest, EmotionAnalyzeResponse
from app.services.auth_service import get_current_user
from app.services.emotion_service import EmotionService, get_emotion_service

router = APIRouter(prefix="/emotion", tags=["emotion"])


@router.post("/analyze", response_model=EmotionAnalyzeResponse)
def analyze_emotion(
    payload: EmotionAnalyzeRequest,
    _user=Depends(get_current_user),
    service: EmotionService = Depends(get_emotion_service),
) -> EmotionAnalyzeResponse:
    try:
        return EmotionAnalyzeResponse.model_validate(
            service.analyze_image(payload.image_base64)
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Emotion analysis failed on the API server.",
        ) from exc
