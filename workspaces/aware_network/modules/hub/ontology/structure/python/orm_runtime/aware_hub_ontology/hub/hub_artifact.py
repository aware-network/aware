from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Hub Ontology
from aware_hub_ontology.hub.hub_enums import HubArtifactStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_hub_ontology.hub.hub_producer_provenance import HubProducerProvenance


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

    async def publish_revision(
        self,
        revision_id: str,
        payload_url: str,
        payload_sha256: str,
        selector_key: str | None = None,
        target_ref: str | None = None,
        media_type: str | None = None,
        size_bytes: int | None = None,
        producer_provenance_id: UUID | None = None,
        published_at_utc: str | None = None,
        metadata: JsonObject = {},
    ) -> HubArtifactRevision:
        """Publish one immutable revision under this artifact."""

        payload = {
            "revision_id": revision_id,
            "payload_url": payload_url,
            "payload_sha256": payload_sha256,
            "selector_key": selector_key,
            "target_ref": target_ref,
            "media_type": media_type,
            "size_bytes": size_bytes,
            "producer_provenance_id": producer_provenance_id,
            "published_at_utc": published_at_utc,
            "metadata": metadata,
        }
        result = await invoke_instance(orm_model=self, function_name="publish_revision", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, HubArtifactRevision):
            return value
        return HubArtifactRevision.validate_invocation_value(value)

    @classmethod
    async def build_via_hub_authority(
        cls,
        hub_authority_id: UUID,
        artifact_family: str,
        artifact_key: str,
        title: str | None = None,
        description: str | None = None,
        media_type: str | None = None,
    ) -> HubArtifact:
        """
        Create one Hub-owned artifact identity.

        Contract:
        - `artifact_family` is open so Hub can carry CodePackage, deployment,
          and future artifact families without importing producer APIs.
        - Revisions carry immutable payload locks.
        """

        payload = {
            "hub_authority_id": hub_authority_id,
            "artifact_family": artifact_family,
            "artifact_key": artifact_key,
            "title": title,
            "description": description,
            "media_type": media_type,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_hub_authority", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, HubArtifact):
            return value
        return HubArtifact.validate_invocation_value(value)


class HubArtifactPublishRevisionInput(BaseModel):
    revision_id: str
    payload_url: str
    payload_sha256: str
    selector_key: str | None = Field(default=None)
    target_ref: str | None = Field(default=None)
    media_type: str | None = Field(default=None)
    size_bytes: int | None = Field(default=None)
    producer_provenance_id: UUID | None = Field(default=None)
    published_at_utc: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class HubArtifactPublishRevisionOutput(BaseModel):
    value: HubArtifactRevision


class HubArtifactBuildViaHubAuthorityInput(BaseModel):
    hub_authority_id: UUID = Field(description="Foreign key for HubAuthority.artifacts")
    artifact_family: str
    artifact_key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    media_type: str | None = Field(default=None)


class HubArtifactBuildViaHubAuthorityOutput(BaseModel):
    value: HubArtifact


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

    @classmethod
    async def build_via_hub_artifact(
        cls,
        hub_artifact_id: UUID,
        revision_id: str,
        payload_url: str,
        payload_sha256: str,
        selector_key: str | None = None,
        target_ref: str | None = None,
        media_type: str | None = None,
        size_bytes: int | None = None,
        producer_provenance_id: UUID | None = None,
        published_at_utc: str | None = None,
        metadata: JsonObject = {},
    ) -> HubArtifactRevision:
        """Create one immutable artifact payload lock."""

        payload = {
            "hub_artifact_id": hub_artifact_id,
            "revision_id": revision_id,
            "payload_url": payload_url,
            "payload_sha256": payload_sha256,
            "selector_key": selector_key,
            "target_ref": target_ref,
            "media_type": media_type,
            "size_bytes": size_bytes,
            "producer_provenance_id": producer_provenance_id,
            "published_at_utc": published_at_utc,
            "metadata": metadata,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_hub_artifact", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, HubArtifactRevision):
            return value
        return HubArtifactRevision.validate_invocation_value(value)


class HubArtifactRevisionBuildViaHubArtifactInput(BaseModel):
    hub_artifact_id: UUID = Field(description="Foreign key for HubArtifact.revisions")
    revision_id: str
    payload_url: str
    payload_sha256: str
    selector_key: str | None = Field(default=None)
    target_ref: str | None = Field(default=None)
    media_type: str | None = Field(default=None)
    size_bytes: int | None = Field(default=None)
    producer_provenance_id: UUID | None = Field(default=None)
    published_at_utc: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class HubArtifactRevisionBuildViaHubArtifactOutput(BaseModel):
    value: HubArtifactRevision


FUNCTIONS = {
    "HubArtifact": {
        "publish_revision": {
            "canonical": {
                "name": "publish_revision",
                "description": "Publish one immutable revision under this artifact.",
                "is_constructor": False,
            },
            "input": HubArtifactPublishRevisionInput,
            "output": HubArtifactPublishRevisionOutput,
        },
        "build_via_hub_authority": {
            "canonical": {
                "name": "build_via_hub_authority",
                "description": "Create one Hub-owned artifact identity.\n\nContract:\n- `artifact_family` is open so Hub can carry CodePackage, deployment,\n  and future artifact families without importing producer APIs.\n- Revisions carry immutable payload locks.",
                "is_constructor": True,
            },
            "input": HubArtifactBuildViaHubAuthorityInput,
            "output": HubArtifactBuildViaHubAuthorityOutput,
        },
    },
    "HubArtifactRevision": {
        "build_via_hub_artifact": {
            "canonical": {
                "name": "build_via_hub_artifact",
                "description": "Create one immutable artifact payload lock.",
                "is_constructor": True,
            },
            "input": HubArtifactRevisionBuildViaHubArtifactInput,
            "output": HubArtifactRevisionBuildViaHubArtifactOutput,
        },
    },
}

__all__ = [
    "HubArtifact",
    "HubArtifactPublishRevisionInput",
    "HubArtifactPublishRevisionOutput",
    "HubArtifactBuildViaHubAuthorityInput",
    "HubArtifactBuildViaHubAuthorityOutput",
    "HubArtifactRevision",
    "HubArtifactRevisionBuildViaHubArtifactInput",
    "HubArtifactRevisionBuildViaHubArtifactOutput",
    "FUNCTIONS",
]
