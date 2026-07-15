from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_content_ontology.content.content import Content
    from aware_content_ontology.package.content_package_artifact import ContentPackageArtifact
    from aware_content_ontology.package.content_package_content import ContentPackageContent


class ContentPackage(ORMModel):
    # Relationships
    artifacts: list[ContentPackageArtifact] = Field(default_factory=list, exclude=True)

    # Attributes
    package_name: str
    package_root: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    title: str | None = Field(default=None)
    package_kind: str | None = Field(default="content")
    source_provider_key: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    provider_payload: JsonObject | None = Field(default=None)

    # Edges
    content_package_contents: list[ContentPackageContent] = Field(
        default_factory=list, exclude=True, description="Edge association helper for contents"
    )

    @property
    def contents(self) -> list[Content]:
        return [edge.content for edge in self.content_package_contents if edge.content is not None]

    @classmethod
    async def build(
        cls,
        package_name: str,
        package_root: str | None = None,
        manifest_relative_path: str | None = None,
        title: str | None = None,
        package_kind: str | None = "content",
        source_provider_key: str | None = None,
        source_ref: str | None = None,
        runtime_contract_version: str | None = None,
        provider_payload: JsonObject | None = None,
    ) -> ContentPackage:
        """
        Create a deterministic ContentPackage.

        Contract:
        - ContentPackage is the Content-owned package authority, parallel to
          CodePackage but not owned by Code.
        - Identity is package-scoped by `package_name`.
        - Content membership is over Content objects; checkout paths and
          filesystem artifacts are materialization coordinates.
        - WorkspaceRevisionContentPackage will later pin package commits under
          WorkspaceRevision. WorkspaceRevisionArtifactRef remains an output
          receipt, not package authority.
        """

        payload = {
            "package_name": package_name,
            "package_root": package_root,
            "manifest_relative_path": manifest_relative_path,
            "title": title,
            "package_kind": package_kind,
            "source_provider_key": source_provider_key,
            "source_ref": source_ref,
            "runtime_contract_version": runtime_contract_version,
            "provider_payload": provider_payload,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentPackage):
            return value
        return ContentPackage.validate_invocation_value(value)

    async def attach_content(
        self,
        content_id: UUID,
        relative_path: str,
        content_role: str = "content",
        position: int | None = None,
        media_type: str | None = None,
        title: str | None = None,
        source_ref: str | None = None,
        provider_payload: JsonObject | None = None,
        receipt_payload: JsonObject | None = None,
    ) -> ContentPackageContent:
        """
        Attach existing Content to this package through package-owned
        membership metadata.
        """

        payload = {
            "content_id": content_id,
            "relative_path": relative_path,
            "content_role": content_role,
            "position": position,
            "media_type": media_type,
            "title": title,
            "source_ref": source_ref,
            "provider_payload": provider_payload,
            "receipt_payload": receipt_payload,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_content", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_content_ontology.package.content_package_content import ContentPackageContent

        if isinstance(value, ContentPackageContent):
            return value
        return ContentPackageContent.validate_invocation_value(value)

    async def attach_artifact(
        self,
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
        Attach one package-owned artifact evidence row.

        Contract:
        - This is package output evidence.
        - WorkspaceRevision should hydrate artifacts through the pinned
          WorkspaceRevisionContentPackage commit once that rail exists.
        """

        payload = {
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
        result = await invoke_instance(orm_model=self, function_name="attach_artifact", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_content_ontology.package.content_package_artifact import ContentPackageArtifact

        if isinstance(value, ContentPackageArtifact):
            return value
        return ContentPackageArtifact.validate_invocation_value(value)


class ContentPackageBuildInput(BaseModel):
    package_name: str
    package_root: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    title: str | None = Field(default=None)
    package_kind: str | None = Field(default="content")
    source_provider_key: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    provider_payload: JsonObject | None = Field(default=None)


class ContentPackageBuildOutput(BaseModel):
    value: ContentPackage


class ContentPackageAttachContentInput(BaseModel):
    content_id: UUID
    relative_path: str
    content_role: str = Field(default="content")
    position: int | None = Field(default=None)
    media_type: str | None = Field(default=None)
    title: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    provider_payload: JsonObject | None = Field(default=None)
    receipt_payload: JsonObject | None = Field(default=None)


class ContentPackageAttachContentOutput(BaseModel):
    value: ContentPackageContent


class ContentPackageAttachArtifactInput(BaseModel):
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


class ContentPackageAttachArtifactOutput(BaseModel):
    value: ContentPackageArtifact


FUNCTIONS = {
    "ContentPackage": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create a deterministic ContentPackage.\n\nContract:\n- ContentPackage is the Content-owned package authority, parallel to\n  CodePackage but not owned by Code.\n- Identity is package-scoped by `package_name`.\n- Content membership is over Content objects; checkout paths and\n  filesystem artifacts are materialization coordinates.\n- WorkspaceRevisionContentPackage will later pin package commits under\n  WorkspaceRevision. WorkspaceRevisionArtifactRef remains an output\n  receipt, not package authority.",
                "is_constructor": True,
            },
            "input": ContentPackageBuildInput,
            "output": ContentPackageBuildOutput,
        },
        "attach_content": {
            "canonical": {
                "name": "attach_content",
                "description": "Attach existing Content to this package through package-owned\nmembership metadata.",
                "is_constructor": False,
            },
            "input": ContentPackageAttachContentInput,
            "output": ContentPackageAttachContentOutput,
        },
        "attach_artifact": {
            "canonical": {
                "name": "attach_artifact",
                "description": "Attach one package-owned artifact evidence row.\n\nContract:\n- This is package output evidence.\n- WorkspaceRevision should hydrate artifacts through the pinned\n  WorkspaceRevisionContentPackage commit once that rail exists.",
                "is_constructor": False,
            },
            "input": ContentPackageAttachArtifactInput,
            "output": ContentPackageAttachArtifactOutput,
        },
    },
}

__all__ = [
    "ContentPackage",
    "ContentPackageBuildInput",
    "ContentPackageBuildOutput",
    "ContentPackageAttachContentInput",
    "ContentPackageAttachContentOutput",
    "ContentPackageAttachArtifactInput",
    "ContentPackageAttachArtifactOutput",
    "FUNCTIONS",
]
