from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserAdminResponse(BaseModel):
    id: int
    external_uid: str
    email: Optional[str]
    name: Optional[str]
    role: str
    organization: Optional[str]
    is_banned: bool
    created_at: datetime


class BanRequest(BaseModel):
    is_banned: bool


class RoleUpdateRequest(BaseModel):
    role: str
    organization: Optional[str]


class TherapistCreateRequest(BaseModel):
    name: str
    specialty: str
    is_verified: bool = False
    availability_json: str = "{}"
    region: Optional[str] = None
    institution: Optional[str] = None


class TherapistResponse(TherapistCreateRequest):
    id: int
    created_at: datetime


class AlertResponse(BaseModel):
    id: int
    user_id: Optional[int]
    type: str
    details: str
    is_resolved: bool
    created_at: datetime


class ResolveAlertRequest(BaseModel):
    is_resolved: bool


class ResourceAdminCreateRequest(BaseModel):
    title: str
    description: str
    url: str
    resource_type: str
    category: str
    content_format: str = "text"
    media_url: Optional[str] = None
    recommended: bool = False


class ResourceResponse(ResourceAdminCreateRequest):
    id: int


class EventAdminCreateRequest(BaseModel):
    title: str
    description: str
    category: str
    date: str
    time: str
    mode: str
    location: Optional[str] = None
    registration_link: Optional[str] = None
    host: str
    capacity: int = 50


class EventResponse(EventAdminCreateRequest):
    id: int
    attendees: int

