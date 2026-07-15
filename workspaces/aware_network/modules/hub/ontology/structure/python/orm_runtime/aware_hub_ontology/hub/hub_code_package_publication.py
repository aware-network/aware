from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_ontology.package.code_package import CodePackage
    from aware_hub_ontology.hub.hub_artifact import HubArtifactRevision
    from aware_hub_ontology.hub.hub_producer_provenance import HubProducerProvenance


class HubCodePackagePublication(ORMModel):
    # Relationships
    artifact_revision: HubArtifactRevision | None = Field(default=None)
    code_package: CodePackage | None = Field(default=None)
    producer_provenance: HubProducerProvenance | None = Field(default=None)

    # Attributes
    artifact_sha256: str
    artifact_size_bytes: int | None = Field(default=None)
    artifact_url: str
    channel_key: str
    descriptor_digest: str | None = Field(default=None)
    download_handle: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    language: CodeLanguage
    manifest_kind: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    media_type: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)
    package_name: str
    package_root: str | None = Field(default=None)
    published_at_utc: str | None = Field(default=None)
    revision_id: str
    sources_root: str | None = Field(default=None)
    surface: str
    version: str | None = Field(default=None)

    # Foreign Keys
    hub_authority_id: UUID = Field(description="Foreign key for HubAuthority.code_package_publications")
    artifact_revision_id: UUID | None = Field(
        default=None, description="Foreign key for HubCodePackagePublication.artifact_revision"
    )
    code_package_id: UUID | None = Field(
        default=None, description="Foreign key for HubCodePackagePublication.code_package"
    )
    producer_provenance_id: UUID | None = Field(
        default=None, description="Foreign key for HubCodePackagePublication.producer_provenance"
    )

    @classmethod
    async def publish_via_hub_authority(
        cls,
        hub_authority_id: UUID,
        package_name: str,
        language: CodeLanguage,
        surface: str,
        channel_key: str,
        revision_id: str,
        artifact_url: str,
        artifact_sha256: str,
        code_package_id: UUID | None = None,
        artifact_revision_id: UUID | None = None,
        producer_provenance_id: UUID | None = None,
        descriptor_digest: str | None = None,
        artifact_size_bytes: int | None = None,
        media_type: str | None = None,
        download_handle: str | None = None,
        manifest_kind: str | None = None,
        manifest_relative_path: str | None = None,
        package_root: str | None = None,
        sources_root: str | None = None,
        fqn_prefix: str | None = None,
        version: str | None = None,
        published_at_utc: str | None = None,
        metadata: JsonObject = {},
    ) -> HubCodePackagePublication:
        """
        Create one Hub CodePackage publication.

        Contract:
        - CodePackage semantic truth remains Code-owned.
        - Hub publication records artifact lock, channel, provenance, and receipt truth.
        """

        payload = {
            "hub_authority_id": hub_authority_id,
            "package_name": package_name,
            "language": language,
            "surface": surface,
            "channel_key": channel_key,
            "revision_id": revision_id,
            "artifact_url": artifact_url,
            "artifact_sha256": artifact_sha256,
            "code_package_id": code_package_id,
            "artifact_revision_id": artifact_revision_id,
            "producer_provenance_id": producer_provenance_id,
            "descriptor_digest": descriptor_digest,
            "artifact_size_bytes": artifact_size_bytes,
            "media_type": media_type,
            "download_handle": download_handle,
            "manifest_kind": manifest_kind,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "sources_root": sources_root,
            "fqn_prefix": fqn_prefix,
            "version": version,
            "published_at_utc": published_at_utc,
            "metadata": metadata,
        }
        result = await invoke_constructor(orm_class=cls, function_name="publish_via_hub_authority", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, HubCodePackagePublication):
            return value
        return HubCodePackagePublication.validate_invocation_value(value)


class HubCodePackagePublicationPublishViaHubAuthorityInput(BaseModel):
    hub_authority_id: UUID = Field(description="Foreign key for HubAuthority.code_package_publications")
    package_name: str
    language: CodeLanguage
    surface: str
    channel_key: str
    revision_id: str
    artifact_url: str
    artifact_sha256: str
    code_package_id: UUID | None = Field(default=None)
    artifact_revision_id: UUID | None = Field(default=None)
    producer_provenance_id: UUID | None = Field(default=None)
    descriptor_digest: str | None = Field(default=None)
    artifact_size_bytes: int | None = Field(default=None)
    media_type: str | None = Field(default=None)
    download_handle: str | None = Field(default=None)
    manifest_kind: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str | None = Field(default=None)
    sources_root: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    version: str | None = Field(default=None)
    published_at_utc: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class HubCodePackagePublicationPublishViaHubAuthorityOutput(BaseModel):
    value: HubCodePackagePublication


FUNCTIONS = {
    "HubCodePackagePublication": {
        "publish_via_hub_authority": {
            "canonical": {
                "name": "publish_via_hub_authority",
                "description": "Create one Hub CodePackage publication.\n\nContract:\n- CodePackage semantic truth remains Code-owned.\n- Hub publication records artifact lock, channel, provenance, and receipt truth.",
                "is_constructor": True,
            },
            "input": HubCodePackagePublicationPublishViaHubAuthorityInput,
            "output": HubCodePackagePublicationPublishViaHubAuthorityOutput,
        },
    },
}

__all__ = [
    "HubCodePackagePublication",
    "HubCodePackagePublicationPublishViaHubAuthorityInput",
    "HubCodePackagePublicationPublishViaHubAuthorityOutput",
    "FUNCTIONS",
]
