from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Hub Ontology Dto
from aware_hub_ontology_dto.hub.hub_enums import HubArtifactStatus

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_hub_ontology_dto.hub.hub_producer_provenance import HubProducerProvenance


class HubArtifact(BaseModel):
    # Relationships
    revisions: list[HubArtifactRevision] = Field(default_factory=list)

    # Attributes
    artifact_family: str
    artifact_key: str
    description: str | None = Field(default=None)
    media_type: str | None = Field(default=None)
    title: str | None = Field(default=None)


class HubArtifactRevision(BaseModel):
    # Relationships
    producer_provenance: HubProducerProvenance | None = Field(default=None)

    # Attributes
    metadata: JsonObject = Field(default_factory=JsonObject)
    media_type: str | None = Field(default=None)
    payload_sha256: str
    payload_url: str
    published_at_utc: str | None = Field(default=None)
    revision_id: str
    selector_key: str | None = Field(default=None)
    size_bytes: int | None = Field(default=None)
    status: HubArtifactStatus = Field(default=HubArtifactStatus.published)
    target_ref: str | None = Field(default=None)
