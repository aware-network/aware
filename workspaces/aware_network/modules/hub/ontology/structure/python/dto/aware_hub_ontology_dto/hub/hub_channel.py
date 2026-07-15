from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Hub Ontology Dto
from aware_hub_ontology_dto.hub.hub_enums import HubAuthorityVisibility

if TYPE_CHECKING:
    from aware_hub_ontology_dto.hub.hub_artifact import HubArtifactRevision
    from aware_hub_ontology_dto.hub.hub_code_package_publication import HubCodePackagePublication


class HubChannel(BaseModel):
    # Relationships
    heads: list[HubChannelHead] = Field(default_factory=list)

    # Attributes
    channel_key: str
    description: str | None = Field(default=None)
    title: str | None = Field(default=None)
    visibility: HubAuthorityVisibility = Field(default=HubAuthorityVisibility.public)


class HubChannelHead(BaseModel):
    # Relationships
    artifact_revision: HubArtifactRevision | None = Field(default=None)
    code_package_publication: HubCodePackagePublication | None = Field(default=None)

    # Attributes
    artifact_family: str
    artifact_key: str
    revision_id: str
    selector_key: str | None = Field(default=None)
    updated_at_utc: str | None = Field(default=None)
