from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Api Ontology Dto
from aware_api_ontology_dto.api.api_view_stream_enums import ApiViewStreamMode


class ApiViewStreamPolicy(BaseModel):
    """Optional stream policy for one readable API view contract."""

    # Attributes
    stream_mode: ApiViewStreamMode
    description: str | None = Field(default=None)
