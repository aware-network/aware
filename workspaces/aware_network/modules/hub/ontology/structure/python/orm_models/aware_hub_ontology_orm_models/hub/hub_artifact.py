from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Hub Ontology Orm Models
from aware_hub_ontology_orm_models.hub.hub_enums import HubArtifactStatus

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_hub_ontology_orm_models.hub.hub_producer_provenance import HubProducerProvenance


class HubArtifact(ORMModel):
    # Relationships
    revisions: list[HubArtifactRevision] = Field(default_factory=list)

    # Attributes
    artifact_family: str
    artifact_key: str
    description: str | None = Field(default=None)
    media_type: str | None = Field(default=None)
    title: str | None = Field(default=None)

    # Foreign Keys
    hub_authority_id: UUID = Field(description="Foreign key for HubAuthority.artifacts")


class HubArtifactRevision(ORMModel):
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

    # Foreign Keys
    hub_artifact_id: UUID = Field(description="Foreign key for HubArtifact.revisions")
    producer_provenance_id: UUID | None = Field(
        default=None, description="Foreign key for HubArtifactRevision.producer_provenance"
    )
