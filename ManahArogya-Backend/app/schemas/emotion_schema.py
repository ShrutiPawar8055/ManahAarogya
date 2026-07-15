from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EmotionAnalyzeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    image_base64: str = Field(..., alias="imageBase64", min_length=100)

    @field_validator("image_base64")
    @classmethod
    def strip_and_validate(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("imageBase64 cannot be empty.")
        return cleaned


class EmotionFaceResponse(BaseModel):
    x: int
    y: int
    w: int
    h: int
    left_percent: float = Field(..., alias="leftPercent")
    top_percent: float = Field(..., alias="topPercent")
    width_percent: float = Field(..., alias="widthPercent")
    height_percent: float = Field(..., alias="heightPercent")
    emotion: str = ""


class EmotionAnalyzeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    frame_width: int = Field(default=0, alias="frameWidth")
    frame_height: int = Field(default=0, alias="frameHeight")
    dominant_emotion: str = Field(default="", alias="dominantEmotion")
    confidence: float | None = None
    faces: list[EmotionFaceResponse] = Field(default_factory=list)
