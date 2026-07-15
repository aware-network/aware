from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Code Ontology
from aware_code_ontology.package.code_package_enums import CodePackageArtifactStatus
from aware_code_ontology.package.code_package_artifact import CodePackageArtifact

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.stable_ids import stable_code_package_artifact_id
from aware_code_ontology.package.code_package import CodePackage
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_code_package(
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

    # --- AWARE: LOGIC START build_via_code_package
    normalized_output_key = (output_key or "").strip()
    normalized_artifact_key = (artifact_key or "").strip()
    if not normalized_output_key:
        raise RuntimeError("CodePackageArtifact.build_via_code_package requires non-empty output_key")
    if not normalized_artifact_key:
        raise RuntimeError("CodePackageArtifact.build_via_code_package requires non-empty artifact_key")

    resolved_status = status
    if not isinstance(resolved_status, CodePackageArtifactStatus):
        resolved_status = CodePackageArtifactStatus(str(status))

    session = current_handler_session()
    code_package = session.imap_get(CodePackage, code_package_id)
    if code_package is None:
        raise RuntimeError(
            "CodePackageArtifact.build_via_code_package requires existing CodePackage: "
            + f"code_package_id={code_package_id}"
        )

    artifact_id = stable_code_package_artifact_id(
        code_package_id=code_package_id,
        output_key=normalized_output_key,
        artifact_key=normalized_artifact_key,
    )
    payload = {
        "code_package_id": code_package_id,
        "output_key": normalized_output_key,
        "artifact_key": normalized_artifact_key,
        "status": resolved_status,
        "artifact_family": (artifact_family or "").strip() or None,
        "artifact_role": (artifact_role or "").strip() or None,
        "required_for": list(required_for or []),
        "producer_key": (producer_key or "").strip() or None,
        "producer_kind": (producer_kind or "").strip() or None,
        "materialization_index": materialization_index,
        "source_code_package_id": source_code_package_id,
        "source_object_instance_graph_commit_id": source_object_instance_graph_commit_id,
        "input_code_package_id": input_code_package_id,
        "input_object_instance_graph_commit_id": input_object_instance_graph_commit_id,
        "digest": (digest or "").strip() or None,
        "relative_path": (relative_path or "").strip() or None,
        "uri": (uri or "").strip() or None,
        "media_type": (media_type or "").strip() or None,
        "runtime_contract_version": (runtime_contract_version or "").strip() or None,
        "provider_payload": provider_payload,
        "receipt_payload": receipt_payload,
        "error": (error or "").strip() or None,
    }

    existing = session.imap_get(CodePackageArtifact, artifact_id)
    if existing is not None:
        if (
            existing.code_package_id != code_package_id
            or (existing.output_key or "").strip() != normalized_output_key
            or (existing.artifact_key or "").strip() != normalized_artifact_key
        ):
            raise RuntimeError(
                "CodePackageArtifact.build_via_code_package payload mismatch for existing artifact: "
                + f"code_package_artifact_id={artifact_id}"
            )
        for attr, value in payload.items():
            setattr(existing, attr, value)
        return existing

    return CodePackageArtifact(id=artifact_id, **payload)
    # --- AWARE: LOGIC END build_via_code_package
