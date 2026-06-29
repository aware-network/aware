from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Orm Models
from aware_code_ontology_orm_models.package.code_package_enums import CodePackageArtifactStatus

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject


class CodePackageArtifact(ORMModel):
    """
    Package-owned materialized output evidence.
    Contract:
    - CodePackageArtifact is durable package output evidence, not a
    WorkspaceRevision artifact pointer.
    - Identity is package-scoped by `(code_package_id, output_key, artifact_key)`.
    - Digest/path/URI/provider receipts are payload, not the primary identity.
    - WorkspaceRevision hydrates these artifacts through the pinned
    WorkspaceRevisionCodePackage commit; it must not duplicate per-artifact
    revision pointers.
    """

    # Attributes
    output_key: str
    artifact_key: str
    status: CodePackageArtifactStatus = Field(default=CodePackageArtifactStatus.available)
    artifact_family: str | None = Field(default=None)
    artifact_role: str | None = Field(default=None)
    required_for: list[str] = Field(default_factory=list)
    producer_key: str | None = Field(default=None)
    producer_kind: str | None = Field(default=None)
    materialization_index: int | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    source_object_instance_graph_commit_id: UUID | None = Field(default=None)
    input_code_package_id: UUID | None = Field(default=None)
    input_object_instance_graph_commit_id: UUID | None = Field(default=None)
    digest: str | None = Field(default=None)
    relative_path: str | None = Field(default=None)
    uri: str | None = Field(default=None)
    media_type: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    provider_payload: JsonObject | None = Field(default=None)
    receipt_payload: JsonObject | None = Field(default=None)
    error: str | None = Field(default=None)

    # Foreign Keys
    code_package_id: UUID = Field(description="Foreign key for CodePackage.artifacts")


class CodePackageArtifactRef(BaseModel):
    """
    Transport shape for package-owned artifact evidence.
    This inline value is for runtime/build receipts and consumer DTOs. Durable
    package ownership remains CodePackageArtifact.
    """

    # Attributes
    code_package_id: UUID | None = Field(default=None)
    code_package_config_output_id: UUID | None = Field(default=None)
    output_key: str
    artifact_key: str
    status: CodePackageArtifactStatus = Field(default=CodePackageArtifactStatus.available)
    artifact_family: str | None = Field(default=None)
    artifact_role: str | None = Field(default=None)
    required_for: list[str] = Field(default_factory=list)
    producer_key: str | None = Field(default=None)
    producer_kind: str | None = Field(default=None)
    materialization_index: int | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    source_object_instance_graph_commit_id: UUID | None = Field(default=None)
    input_code_package_id: UUID | None = Field(default=None)
    input_object_instance_graph_commit_id: UUID | None = Field(default=None)
    digest: str | None = Field(default=None)
    relative_path: str | None = Field(default=None)
    uri: str | None = Field(default=None)
    media_type: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    provider_payload: JsonObject | None = Field(default=None)
    receipt_payload: JsonObject | None = Field(default=None)
    error: str | None = Field(default=None)
