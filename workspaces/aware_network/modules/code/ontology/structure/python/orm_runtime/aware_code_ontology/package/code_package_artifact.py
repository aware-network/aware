from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.package.code_package_enums import CodePackageArtifactStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

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

    @classmethod
    async def build_via_code_package(
        cls,
        code_package_id: UUID,
        output_key: str,
        artifact_key: str,
        status: CodePackageArtifactStatus = CodePackageArtifactStatus.available,
        artifact_family: str | None = None,
        artifact_role: str | None = None,
        required_for: list[str] = [],
        producer_key: str | None = None,
        producer_kind: str | None = None,
        materialization_index: int | None = None,
        source_code_package_id: UUID | None = None,
        source_object_instance_graph_commit_id: UUID | None = None,
        input_code_package_id: UUID | None = None,
        input_object_instance_graph_commit_id: UUID | None = None,
        digest: str | None = None,
        relative_path: str | None = None,
        uri: str | None = None,
        media_type: str | None = None,
        runtime_contract_version: str | None = None,
        provider_payload: JsonObject | None = None,
        receipt_payload: JsonObject | None = None,
        error: str | None = None,
    ) -> CodePackageArtifact:
        """
        Create one package-owned artifact evidence row under CodePackage.

        Contract:
        - Parent CodePackage context is propagated by constructor lowering.
        - `output_key` identifies the declared CodePackageConfigOutput.
        - `artifact_key` identifies one deterministic output member.
        - WorkspaceRevision id is never an identity input here.
        """

        payload = {
            "code_package_id": code_package_id,
            "output_key": output_key,
            "artifact_key": artifact_key,
            "status": status,
            "artifact_family": artifact_family,
            "artifact_role": artifact_role,
            "required_for": required_for,
            "producer_key": producer_key,
            "producer_kind": producer_kind,
            "materialization_index": materialization_index,
            "source_code_package_id": source_code_package_id,
            "source_object_instance_graph_commit_id": source_object_instance_graph_commit_id,
            "input_code_package_id": input_code_package_id,
            "input_object_instance_graph_commit_id": input_object_instance_graph_commit_id,
            "digest": digest,
            "relative_path": relative_path,
            "uri": uri,
            "media_type": media_type,
            "runtime_contract_version": runtime_contract_version,
            "provider_payload": provider_payload,
            "receipt_payload": receipt_payload,
            "error": error,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodePackageArtifact):
            return value
        return CodePackageArtifact.validate_invocation_value(value)


class CodePackageArtifactBuildViaCodePackageInput(BaseModel):
    code_package_id: UUID = Field(description="Foreign key for CodePackage.artifacts")
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


class CodePackageArtifactBuildViaCodePackageOutput(BaseModel):
    value: CodePackageArtifact


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


FUNCTIONS = {
    "CodePackageArtifact": {
        "build_via_code_package": {
            "canonical": {
                "name": "build_via_code_package",
                "description": "Create one package-owned artifact evidence row under CodePackage.\n\nContract:\n- Parent CodePackage context is propagated by constructor lowering.\n- `output_key` identifies the declared CodePackageConfigOutput.\n- `artifact_key` identifies one deterministic output member.\n- WorkspaceRevision id is never an identity input here.",
                "is_constructor": True,
            },
            "input": CodePackageArtifactBuildViaCodePackageInput,
            "output": CodePackageArtifactBuildViaCodePackageOutput,
        },
    },
}

__all__ = [
    "CodePackageArtifact",
    "CodePackageArtifactBuildViaCodePackageInput",
    "CodePackageArtifactBuildViaCodePackageOutput",
    "FUNCTIONS",
]
