from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.code.code_enums import CodeLanguage

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.package.code_package import CodePackage
    from aware_hub_ontology_orm_models.hub.hub_artifact import HubArtifactRevision
    from aware_hub_ontology_orm_models.hub.hub_producer_provenance import HubProducerProvenance


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
