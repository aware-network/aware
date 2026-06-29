from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_sdk_ontology_dto.sdk.sdk_operation import SdkOperation
    from aware_sdk_ontology_dto.sdk.sdk_surface import SdkSurface


class SdkConfig(BaseModel):
    """
    Canonical SDK semantic root.
    SDKs are local orchestration surfaces over committed API contracts. They do
    not own API ingress truth; operation endpoint bindings point back to
    `ApiCapabilityEndpoint`.
    """

    # Relationships
    operations: list[SdkOperation] = Field(default_factory=list)
    surfaces: list[SdkSurface] = Field(default_factory=list)

    # Attributes
    name: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
