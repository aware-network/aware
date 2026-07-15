from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_capability_endpoint import ApiCapabilityEndpoint


class ActionConfig(BaseModel):
    # Relationships
    api_capability_endpoint: ApiCapabilityEndpoint | None = Field(default=None)

    # Attributes
    action_schema: JsonObject = Field(
        default_factory=JsonObject,
        description="Deprecated compatibility schema mirror.\nSchema authority belongs to Meta ClassConfig and API endpoint\nrequest/response/stream contracts. New action rail code must resolve\ntyped contracts through Experience bindings and `InlineValueInstance`\npayload evidence, not this JSON attribute.",
    )
    action_type: str
    allowed_roles: list[str] = Field(default_factory=list)
    description: str
    is_enabled: bool = Field(default=True)
    is_system: bool = Field(default=False)
    name: str
    require_authentication: bool = Field(default=True)
