from __future__ import annotations

import base64
import os
from pathlib import Path

from app.core.logging import logger

BACKEND_ROOT = Path(__file__).resolve().parents[2]
EMOTION_WEIGHT_FILE = "facial_expression_model_weights.h5"


def _build_weight_path(deepface_home: Path) -> Path:
    return deepface_home / ".deepface" / "weights" / EMOTION_WEIGHT_FILE


def _resolve_deepface_home() -> Path:
    env_home = os.environ.get("DEEPFACE_HOME")
    candidate_roots = [
        Path(env_home).resolve() if env_home else None,
        BACKEND_ROOT.resolve(),
        (BACKEND_ROOT / ".deepface").resolve(),
        (BACKEND_ROOT.parent / "Emotion-Recognition" / "hi" / ".deepface").resolve(),
        Path.home().resolve(),
        (Path.home() / ".deepface").resolve(),
    ]

    seen: set[str] = set()
    normalized_candidates: list[Path] = []
    for candidate in candidate_roots:
        if candidate is None:
            continue

        candidate_key = str(candidate)
        if candidate_key in seen:
            continue

        seen.add(candidate_key)
        normalized_candidates.append(candidate)

    for candidate in normalized_candidates:
        if _build_weight_path(candidate).is_file():
            return candidate

    return BACKEND_ROOT.resolve()


DEEPFACE_HOME = _resolve_deepface_home()
os.environ.setdefault("DEEPFACE_HOME", str(DEEPFACE_HOME))
os.environ.setdefault("KERAS_HOME", str(BACKEND_ROOT / ".keras"))
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")

import cv2
import numpy as np
from deepface import DeepFace


FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def _clamp_int(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(int(value), maximum))


def _percent(value: int, total: int) -> float:
    if total <= 0:
        return 0

    return round((float(value) / float(total)) * 100, 2)


def _expand_box(
    x: int,
    y: int,
    w: int,
    h: int,
    source_width: int,
    source_height: int,
    expand_ratio: float = 0.18,
) -> tuple[int, int, int, int]:
    pad_x = int(w * expand_ratio)
    pad_y = int(h * expand_ratio)
    x1 = _clamp_int(x - pad_x, 0, source_width)
    y1 = _clamp_int(y - pad_y, 0, source_height)
    x2 = _clamp_int(x + w + pad_x, 0, source_width)
    y2 = _clamp_int(y + h + pad_y, 0, source_height)
    return x1, y1, x2, y2


def _build_face_payload(
    x: int,
    y: int,
    w: int,
    h: int,
    source_width: int,
    source_height: int,
    emotion: str,
) -> dict:
    return {
        "x": int(x),
        "y": int(y),
        "w": int(w),
        "h": int(h),
        "leftPercent": _percent(x, source_width),
        "topPercent": _percent(y, source_height),
        "widthPercent": _percent(w, source_width),
        "heightPercent": _percent(h, source_height),
        "emotion": emotion,
    }


def _build_analysis_payload(
    source_width: int,
    source_height: int,
    dominant_emotion: str = "",
    confidence: float | None = None,
    faces: list[dict] | None = None,
) -> dict:
    return {
        "frameWidth": int(source_width),
        "frameHeight": int(source_height),
        "dominantEmotion": dominant_emotion,
        "confidence": confidence,
        "faces": faces or [],
    }


def _normalize_result(analysis_result):
    if isinstance(analysis_result, list):
        if not analysis_result:
            return {}
        return analysis_result[0]

    if isinstance(analysis_result, dict):
        return analysis_result

    return {}


class EmotionService:
    def __init__(self) -> None:
        weight_path = _build_weight_path(DEEPFACE_HOME)
        if weight_path.is_file():
            logger.info("Emotion model weights resolved at {}", weight_path)
        else:
            logger.warning(
                "Emotion model weights not found at {}. DeepFace may attempt a download.",
                weight_path,
            )

    def analyze_image(self, image_base64: str) -> dict:
        frame = self._decode_frame(image_base64)
        return self._analyze_frame(frame)

    def _decode_frame(self, image_base64: str):
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as exc:
            raise ValueError("Unable to decode imageBase64.") from exc

        frame_buffer = np.frombuffer(image_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame_buffer, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Unable to decode the captured frame.")

        return frame

    def _detect_faces_with_haar(self, gray_frame):
        detections = []
        detection_profiles = [
            {"scaleFactor": 1.08, "minNeighbors": 5, "minSize": (36, 36)},
            {"scaleFactor": 1.05, "minNeighbors": 4, "minSize": (28, 28)},
            {"scaleFactor": 1.03, "minNeighbors": 3, "minSize": (24, 24)},
        ]

        equalized = cv2.equalizeHist(gray_frame)

        for profile in detection_profiles:
            faces = FACE_CASCADE.detectMultiScale(
                equalized,
                scaleFactor=profile["scaleFactor"],
                minNeighbors=profile["minNeighbors"],
                minSize=profile["minSize"],
            )
            if len(faces) > 0:
                detections.extend(faces)
                break

        return detections

    def _detect_faces_with_deepface(self, frame, source_width: int, source_height: int):
        try:
            extracted_faces = DeepFace.extract_faces(
                frame,
                detector_backend="opencv",
                enforce_detection=False,
                align=True,
                expand_percentage=12,
                grayscale=False,
                color_face="bgr",
                normalize_face=False,
            )
        except Exception as exc:
            logger.warning("DeepFace face extraction failed: {}", str(exc))
            return []

        candidates = []
        for extracted in extracted_faces:
            facial_area = extracted.get("facial_area") or {}
            x = int(facial_area.get("x", 0))
            y = int(facial_area.get("y", 0))
            w = int(facial_area.get("w", 0))
            h = int(facial_area.get("h", 0))
            confidence = float(extracted.get("confidence") or 0.0)

            if w <= 0 or h <= 0:
                continue

            area_ratio = (w * h) / float(max(source_width * source_height, 1))
            is_full_frame_fallback = confidence <= 0.01 and area_ratio >= 0.9
            if is_full_frame_fallback:
                continue

            candidates.append((x, y, w, h, confidence))

        return candidates

    def _analyze_face_roi(self, frame, x: int, y: int, w: int, h: int) -> dict:
        source_height, source_width = frame.shape[:2]
        x1, y1, x2, y2 = _expand_box(x, y, w, h, source_width, source_height)
        face_roi = frame[y1:y2, x1:x2]

        analysis_result = DeepFace.analyze(
            face_roi,
            actions=["emotion"],
            enforce_detection=False,
            detector_backend="skip",
            align=False,
            silent=True,
        )
        normalized = _normalize_result(analysis_result)
        dominant_emotion = normalized.get("dominant_emotion", "")
        emotion_scores = normalized.get("emotion") or {}
        confidence = emotion_scores.get(dominant_emotion)

        return _build_analysis_payload(
            source_width=source_width,
            source_height=source_height,
            dominant_emotion=dominant_emotion,
            confidence=round(float(confidence), 2) if confidence is not None else None,
            faces=[
                _build_face_payload(x, y, w, h, source_width, source_height, dominant_emotion)
            ],
        )

    def _analyze_frame(self, frame) -> dict:
        source_height, source_width = frame.shape[:2]
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        haar_faces = self._detect_faces_with_haar(gray_frame)
        if len(haar_faces) > 0:
            x, y, w, h = max(haar_faces, key=lambda face: face[2] * face[3])
            return self._analyze_face_roi(frame, x, y, w, h)

        deepface_faces = self._detect_faces_with_deepface(frame, source_width, source_height)
        if len(deepface_faces) > 0:
            x, y, w, h, _ = max(deepface_faces, key=lambda face: face[2] * face[3])
            return self._analyze_face_roi(frame, x, y, w, h)

        return _build_analysis_payload(
            source_width=source_width,
            source_height=source_height,
        )


_emotion_service = EmotionService()


def get_emotion_service() -> EmotionService:
    return _emotion_service
