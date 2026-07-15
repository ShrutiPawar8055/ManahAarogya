from fastapi import APIRouter, Depends, Query

from app.services.auth_service import get_current_user
from app.services.resource_service import ResourceService, get_resource_service

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("/")
def list_resources(_user=Depends(get_current_user), service: ResourceService = Depends(get_resource_service)):
    """Return all resources."""
    return {"data": service.list_resources()}


@router.get("/categories")
def categories(_user=Depends(get_current_user), service: ResourceService = Depends(get_resource_service)):
    """Return unique resource categories."""
    return {"data": service.list_categories()}


@router.get("/library")
def library(
    query: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    type: str | None = Query(default=None),
    recommended: bool = Query(default=False),
    limit: int = Query(default=50),
    _user=Depends(get_current_user),
    service: ResourceService = Depends(get_resource_service),
):
    """Return filtered resource library."""
    return {"data": service.list_library(query, resource_type or type, recommended, limit)}


@router.get("/recommendations")
async def recommendations(user=Depends(get_current_user), service: ResourceService = Depends(get_resource_service)):
    """Return personalized recommendation payload."""
    return {"data": await service.get_recommendations(user.id)}
