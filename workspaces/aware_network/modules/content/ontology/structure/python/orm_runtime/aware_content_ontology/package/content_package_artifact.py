from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Content Ontology
from aware_content_ontology.package.content_package_enums import ContentPackageArtifactStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

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

    @classmethod
    async def build_via_content_package(
        cls,
        content_package_id: UUID,
        output_key: str,
        artifact_key: str,
        status: ContentPackageArtifactStatus = ContentPackageArtifactStatus.available,
        artifact_family: str | None = None,
        artifact_role: str | None = None,
        required_for: list[str] = [],
        producer_provider_key: str | None = None,
        producer_key: str | None = None,
        producer_kind: str | None = None,
        materialization_index: int | None = None,
        source_content_package_id: UUID | None = None,
        source_object_instance_graph_commit_id: UUID | None = None,
        input_content_package_id: UUID | None = None,
        input_object_instance_graph_commit_id: UUID | None = None,
        digest: str | None = None,
        digest_algorithm: str | None = "sha256",
        relative_path: str | None = None,
        uri: str | None = None,
        media_type: str | None = None,
        size_bytes: int | None = None,
        runtime_contract_version: str | None = None,
        provider_payload: JsonObject | None = None,
        receipt_payload: JsonObject | None = None,
        error: str | None = None,
    ) -> ContentPackageArtifact:
        """
        Create one package-owned artifact evidence row under ContentPackage.

        Contract:
        - Parent ContentPackage context is propagated by constructor lowering.
        - `output_key` identifies the declared package output surface.
        - `artifact_key` identifies one deterministic output member.
        - WorkspaceRevision id is never an identity input here.
        """

        payload = {
            "content_package_id": content_package_id,
            "output_key": output_key,
            "artifact_key": artifact_key,
            "status": status,
            "artifact_family": artifact_family,
            "artifact_role": artifact_role,
            "required_for": required_for,
            "producer_provider_key": producer_provider_key,
            "producer_key": producer_key,
            "producer_kind": producer_kind,
            "materialization_index": materialization_index,
            "source_content_package_id": source_content_package_id,
            "source_object_instance_graph_commit_id": source_object_instance_graph_commit_id,
            "input_content_package_id": input_content_package_id,
            "input_object_instance_graph_commit_id": input_object_instance_graph_commit_id,
            "digest": digest,
            "digest_algorithm": digest_algorithm,
            "relative_path": relative_path,
            "uri": uri,
            "media_type": media_type,
            "size_bytes": size_bytes,
            "runtime_contract_version": runtime_contract_version,
            "provider_payload": provider_payload,
            "receipt_payload": receipt_payload,
            "error": error,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_content_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentPackageArtifact):
            return value
        return ContentPackageArtifact.validate_invocation_value(value)


class ContentPackageArtifactBuildViaContentPackageInput(BaseModel):
    content_package_id: UUID = Field(description="Foreign key for ContentPackage.artifacts")
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


class ContentPackageArtifactBuildViaContentPackageOutput(BaseModel):
    value: ContentPackageArtifact


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


FUNCTIONS = {
    "ContentPackageArtifact": {
        "build_via_content_package": {
            "canonical": {
                "name": "build_via_content_package",
                "description": "Create one package-owned artifact evidence row under ContentPackage.\n\nContract:\n- Parent ContentPackage context is propagated by constructor lowering.\n- `output_key` identifies the declared package output surface.\n- `artifact_key` identifies one deterministic output member.\n- WorkspaceRevision id is never an identity input here.",
                "is_constructor": True,
            },
            "input": ContentPackageArtifactBuildViaContentPackageInput,
            "output": ContentPackageArtifactBuildViaContentPackageOutput,
        },
    },
}

__all__ = [
    "ContentPackageArtifact",
    "ContentPackageArtifactBuildViaContentPackageInput",
    "ContentPackageArtifactBuildViaContentPackageOutput",
    "FUNCTIONS",
]
