from pydantic import BaseModel, ConfigDict


class ResourceResponse(BaseModel):
    """Resource response schema."""

    id: int
    title: str
    description: str
    url: str
    resource_type: str
    category: str
    recommended: bool

    model_config = ConfigDict(from_attributes=True)
