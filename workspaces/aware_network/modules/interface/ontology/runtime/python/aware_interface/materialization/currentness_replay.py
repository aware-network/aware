from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from uuid import UUID

from aware_code.semantic_currentness import (
    SemanticMaterializationCurrentnessReplayRequest,
    SemanticMaterializationCurrentnessReplayResult,
    semantic_materialization_bundle_matches_live_head,
    semantic_materialization_declared_source_tree_input_is_complete,
)


async def resolve_currentness_replay(
    request: SemanticMaterializationCurrentnessReplayRequest,
) -> SemanticMaterializationCurrentnessReplayResult:
    if (
        request.provider_key != "aware_interface"
        or request.semantic_package_family != "interface"
        or request.semantic_package_kind != "interface_package"
        or request.workspace_manifest_kind != "interface"
    ):
        return SemanticMaterializationCurrentnessReplayResult(
            status="not_supported",
            reason="interface_package_currentness_shape_unsupported",
        )
    if not semantic_materialization_declared_source_tree_input_is_complete(request=request):
        return SemanticMaterializationCurrentnessReplayResult(
            status="must_execute",
            reason="interface_package_current_input_incomplete",
        )
    if not request.bundles:
        return SemanticMaterializationCurrentnessReplayResult(
            status="must_execute",
            reason="interface_package_previous_bundle_missing",
        )
    for bundle in request.bundles:
        if not await semantic_materialization_bundle_matches_live_head(
            bundle=bundle,
            read_head=request.read_head,
        ):
            return SemanticMaterializationCurrentnessReplayResult(
                status="must_execute",
                reason="interface_package_live_head_mismatch",
            )
        evidence = _mapping_evidence(bundle.provider_replay_evidence.get("semantic_outputs"))
        evidence_roles = {str(item.get("role") or "").strip() for item in evidence}
        for role in ("source_code_package", "interface_config"):
            if role not in evidence_roles:
                return SemanticMaterializationCurrentnessReplayResult(
                    status="must_execute",
                    reason=f"{role}_witness_missing",
                )
        for item in evidence:
            role = str(item.get("role") or "").strip()
            if role not in {
                "source_code_package",
                "interface_config",
                "pane_render_spec",
            }:
                return SemanticMaterializationCurrentnessReplayResult(
                    status="must_execute",
                    reason="interface_output_witness_role_unsupported",
                )
            if not await _semantic_output_matches_live_head(
                request=request,
                evidence=item,
            ):
                return SemanticMaterializationCurrentnessReplayResult(
                    status="must_execute",
                    reason=f"{role}_live_head_mismatch",
                )
        artifact_refs = tuple(
            artifact_ref for item in evidence for artifact_ref in _mapping_evidence(item.get("artifact_refs"))
        )
        if not artifact_refs:
            return SemanticMaterializationCurrentnessReplayResult(
                status="must_execute",
                reason="interface_artifact_witness_missing",
            )
        if not all(
            _artifact_ref_matches(
                workspace_root=request.workspace_root,
                artifact_ref=artifact_ref,
            )
            for artifact_ref in artifact_refs
        ):
            return SemanticMaterializationCurrentnessReplayResult(
                status="must_execute",
                reason="interface_artifact_witness_mismatch",
            )
    return SemanticMaterializationCurrentnessReplayResult(
        status="reused",
        reason="interface_output_heads_and_artifacts_current",
        replay_kind="previous_interface_output_bundles",
    )


async def _semantic_output_matches_live_head(
    *,
    request: SemanticMaterializationCurrentnessReplayRequest,
    evidence: Mapping[str, object],
) -> bool:
    branch_id = _uuid_or_none(evidence.get("branch_id"))
    projection_hash = _string_or_none(evidence.get("projection_hash"))
    expected_commit_id = _uuid_or_none(evidence.get("object_instance_graph_commit_id"))
    if branch_id is None or projection_hash is None or expected_commit_id is None:
        return False
    head = await request.read_head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    return (
        isinstance(head, Mapping) and _uuid_or_none(head.get("object_instance_graph_commit_id")) == expected_commit_id
    )


def _artifact_ref_matches(
    *,
    workspace_root: Path,
    artifact_ref: Mapping[str, object],
) -> bool:
    relative_path = _string_or_none(artifact_ref.get("path"))
    expected_digest = _string_or_none(artifact_ref.get("digest"))
    if relative_path is None or expected_digest is None or artifact_ref.get("digest_algorithm") != "sha256":
        return False
    resolved_workspace_root = workspace_root.resolve()
    path = (resolved_workspace_root / relative_path).resolve()
    try:
        path.relative_to(resolved_workspace_root)
    except ValueError:
        return False
    return path.is_file() and (f"sha256:{sha256(path.read_bytes()).hexdigest()}" == expected_digest)


def _mapping_evidence(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _string_or_none(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _uuid_or_none(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    text = _string_or_none(value)
    if text is None:
        return None
    try:
        return UUID(text)
    except ValueError:
        return None


__all__ = ["resolve_currentness_replay"]
