from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Content Ontology
from aware_content_ontology.package.content_package import ContentPackage
from aware_content_ontology.package.content_package_enums import ContentPackageArtifactStatus

# Types
from aware_types import JsonObject

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_content_ontology.package.content_package_artifact import (
    ContentPackageArtifact,
)
from aware_content_ontology.package.content_package_content import (
    ContentPackageContent,
)

# --- AWARE: USER_IMPORTS END


async def attach_content(
    content_package: ContentPackage,
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

    # --- AWARE: LOGIC START attach_content
    if content_package.id is None:
        raise ValueError("ContentPackage.attach_content requires package id.")
    created = await ContentPackageContent.build_via_content_package(
        content_package_id=content_package.id,
        content_id=content_id,
        relative_path=relative_path,
        content_role=content_role,
        position=position,
        media_type=media_type,
        title=title,
        source_ref=source_ref,
        provider_payload=provider_payload,
        receipt_payload=receipt_payload,
    )
    if all(
        getattr(item, "id", None) != getattr(created, "id", None)
        for item in content_package.content_package_contents
    ):
        content_package.content_package_contents.append(created)
    return created
    # --- AWARE: LOGIC END attach_content


async def attach_artifact(
    content_package: ContentPackage,
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

    # --- AWARE: LOGIC START attach_artifact
    if content_package.id is None:
        raise ValueError("ContentPackage.attach_artifact requires package id.")
    created = await ContentPackageArtifact.build_via_content_package(
        content_package_id=content_package.id,
        output_key=output_key,
        artifact_key=artifact_key,
        status=status,
        artifact_family=artifact_family,
        artifact_role=artifact_role,
        required_for=required_for,
        producer_provider_key=producer_provider_key,
        producer_key=producer_key,
        producer_kind=producer_kind,
        materialization_index=materialization_index,
        source_content_package_id=source_content_package_id,
        source_object_instance_graph_commit_id=source_object_instance_graph_commit_id,
        input_content_package_id=input_content_package_id,
        input_object_instance_graph_commit_id=input_object_instance_graph_commit_id,
        digest=digest,
        digest_algorithm=digest_algorithm,
        relative_path=relative_path,
        uri=uri,
        media_type=media_type,
        size_bytes=size_bytes,
        runtime_contract_version=runtime_contract_version,
        provider_payload=provider_payload,
        receipt_payload=receipt_payload,
        error=error,
    )
    if all(
        getattr(item, "id", None) != getattr(created, "id", None)
        for item in content_package.artifacts
    ):
        content_package.artifacts.append(created)
    return created
    # --- AWARE: LOGIC END attach_artifact
