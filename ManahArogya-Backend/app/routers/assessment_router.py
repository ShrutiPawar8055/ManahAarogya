from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.assessment_schema import (
    AssessmentAnswerUpdateRequest,
    AssessmentSessionCreateRequest,
    AssessmentSubmitRequest,
)
from app.services.assessment_service import AssessmentService, get_assessment_service
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("/catalog")
def catalog(_user=Depends(get_current_user), service: AssessmentService = Depends(get_assessment_service)):
    return {"data": service.get_catalog()}


@router.post("/sessions")
def create_session(
    payload: AssessmentSessionCreateRequest,
    user=Depends(get_current_user),
    service: AssessmentService = Depends(get_assessment_service),
):
    return {"data": service.create_session(user.id, mode=payload.mode)}


@router.get("/sessions/{session_id}")
def get_session(
    session_id: int,
    user=Depends(get_current_user),
    service: AssessmentService = Depends(get_assessment_service),
):
    return {"data": service.get_session(user.id, session_id)}


@router.patch("/sessions/{session_id}/answers")
def update_answer(
    session_id: int,
    payload: AssessmentAnswerUpdateRequest,
    user=Depends(get_current_user),
    service: AssessmentService = Depends(get_assessment_service),
):
    return {
        "data": service.update_session_answer(
            user.id,
            session_id,
            test_id=payload.test_id,
            question_index=payload.question_index,
            answer_value=payload.answer_value,
        )
    }


@router.post("/sessions/{session_id}/complete")
def complete_session(
    session_id: int,
    user=Depends(get_current_user),
    service: AssessmentService = Depends(get_assessment_service),
):
    return {"data": service.complete_session(user.id, session_id)}


@router.get("/history")
def history(
    limit: int = Query(default=10, ge=1, le=50),
    user=Depends(get_current_user),
    service: AssessmentService = Depends(get_assessment_service),
):
    return {"data": service.list_history(user.id, limit=limit)}


@router.get("/latest")
def latest_session(
    user=Depends(get_current_user),
    service: AssessmentService = Depends(get_assessment_service),
):
    return {"data": service.latest_session(user.id)}


@router.post("/submit")
def submit(payload: AssessmentSubmitRequest, user=Depends(get_current_user), service: AssessmentService = Depends(get_assessment_service)):
    if not payload.submissions:
        raise HTTPException(status_code=422, detail="At least one submission is required.")
    submissions = [submission.model_dump() for submission in payload.submissions]
    return {"data": service.submit_batch(user.id, submissions)}


@router.get("/")
def list_assessments(user=Depends(get_current_user), service: AssessmentService = Depends(get_assessment_service)):
    return {"data": service.list_assessments(user.id)}
