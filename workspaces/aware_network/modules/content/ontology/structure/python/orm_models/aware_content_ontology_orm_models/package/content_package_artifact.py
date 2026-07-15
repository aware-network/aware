from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Content Ontology Orm Models
from aware_content_ontology_orm_models.package.content_package_enums import ContentPackageArtifactStatus

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject


class ContentPackageArtifact(ORMModel):
    """
    Package-owned materialized content output evidence.
    Contract:
    - ContentPackageArtifact is durable package output evidence, not a
    WorkspaceRevision artifact pointer.
    - Identity is package-scoped by `(content_package_id, output_key,
    artifact_key)`.
    - Digest/path/URI/provider receipts are payload, not primary identity.
    - WorkspaceRevision should hydrate these artifacts through a pinned
    WorkspaceRevisionContentPackage commit once Workspace owns that rail.
    """

    # Attributes
    output_key: str
    artifact_key: str
    status: ContentPackageArtifactStatus = Field(default=ContentPackageArtifactStatus.available)
    artifact_family: str | None = Field(default=None)
    artifact_role: str | None = Field(default=None)
    required_for: list[str] = Field(default_factory=list)
    producer_provider_key: str | None = Field(default=None)
    producer_key: str | None = Field(default=None)
    producer_kind: str | None = Field(default=None)
    materialization_index: int | None = Field(default=None)
    source_content_package_id: UUID | None = Field(default=None)
    source_object_instance_graph_commit_id: UUID | None = Field(default=None)
    input_content_package_id: UUID | None = Field(default=None)
    input_object_instance_graph_commit_id: UUID | None = Field(default=None)
    digest: str | None = Field(default=None)
    digest_algorithm: str | None = Field(default="sha256")
    relative_path: str | None = Field(default=None)
    uri: str | None = Field(default=None)
    media_type: str | None = Field(default=None)
    size_bytes: int | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    provider_payload: JsonObject | None = Field(default=None)
    receipt_payload: JsonObject | None = Field(default=None)
    error: str | None = Field(default=None)

    # Foreign Keys
    content_package_id: UUID = Field(description="Foreign key for ContentPackage.artifacts")


class ContentPackageArtifactRef(BaseModel):
    """
    Transport shape for package-owned content artifact evidence.
    This inline value is for runtime/build receipts and consumer DTOs. Durable
    package ownership remains ContentPackageArtifact.
    """

    # Attributes
    content_package_id: UUID | None = Field(default=None)
    output_key: str
    artifact_key: str
    status: ContentPackageArtifactStatus = Field(default=ContentPackageArtifactStatus.available)
    artifact_family: str | None = Field(default=None)
    artifact_role: str | None = Field(default=None)
    required_for: list[str] = Field(default_factory=list)
    producer_provider_key: str | None = Field(default=None)
    producer_key: str | None = Field(default=None)
    producer_kind: str | None = Field(default=None)
    materialization_index: int | None = Field(default=None)
    source_content_package_id: UUID | None = Field(default=None)
    source_object_instance_graph_commit_id: UUID | None = Field(default=None)
    input_content_package_id: UUID | None = Field(default=None)
    input_object_instance_graph_commit_id: UUID | None = Field(default=None)
    digest: str | None = Field(default=None)
    digest_algorithm: str | None = Field(default="sha256")
    relative_path: str | None = Field(default=None)
    uri: str | None = Field(default=None)
    media_type: str | None = Field(default=None)
    size_bytes: int | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    provider_payload: JsonObject | None = Field(default=None)
    receipt_payload: JsonObject | None = Field(default=None)
    error: str | None = Field(default=None)
