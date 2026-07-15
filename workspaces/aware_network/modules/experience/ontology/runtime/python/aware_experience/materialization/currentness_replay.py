from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path

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
        request.provider_key != "aware_experience"
        or request.workspace_manifest_kind != "experience"
        or request.semantic_package_family != "experience"
        or request.semantic_package_kind != "experience_package"
    ):
        return SemanticMaterializationCurrentnessReplayResult(
            status="not_supported",
            reason="experience_package_currentness_shape_unsupported",
        )
    if not semantic_materialization_declared_source_tree_input_is_complete(
        request=request
    ):
        return SemanticMaterializationCurrentnessReplayResult(
            status="must_execute",
            reason="experience_package_current_input_incomplete",
        )
    if not request.bundles:
        return SemanticMaterializationCurrentnessReplayResult(
            status="must_execute",
            reason="experience_package_previous_bundle_missing",
        )
    for bundle in request.bundles:
        if not await semantic_materialization_bundle_matches_live_head(
            bundle=bundle,
            read_head=request.read_head,
        ):
            return SemanticMaterializationCurrentnessReplayResult(
                status="must_execute",
                reason="experience_package_live_head_mismatch",
            )
    generated_deltas = _mapping_sequence(
        request.replay_output_details.get("generated_code_package_deltas")
    )
    if not _generated_delta_outputs_match(
        workspace_root=request.workspace_root,
        generated_deltas=generated_deltas,
    ):
        return SemanticMaterializationCurrentnessReplayResult(
            status="must_execute",
            reason="experience_generated_output_mismatch",
        )
    expected_runtime_packages = {
        _text(ref.get("package_name"))
        for bundle in request.bundles
        for raw_ref in bundle.runtime_code_package_refs
        for ref in (_mapping(raw_ref),)
        if ref is not None and _text(ref.get("package_name")) is not None
    }
    witnessed_runtime_packages = {
        _text(delta.get("package_name"))
        for delta in generated_deltas
        if _text(delta.get("package_name")) is not None
    }
    if expected_runtime_packages != witnessed_runtime_packages:
        return SemanticMaterializationCurrentnessReplayResult(
            status="must_execute",
            reason="experience_generated_output_witness_incomplete",
        )
    return SemanticMaterializationCurrentnessReplayResult(
        status="reused",
        reason="experience_package_head_and_outputs_current",
        replay_kind="previous_experience_output_bundles",
    )


def _generated_delta_outputs_match(
    *,
    workspace_root: Path,
    generated_deltas: tuple[Mapping[str, object], ...],
) -> bool:
    resolved_root = workspace_root.resolve()
    for delta in generated_deltas:
        package_root = _text(delta.get("package_root"))
        paths = _mapping_sequence(delta.get("paths"))
        if package_root is None or not paths:
            return False
        for path_payload in paths:
            relative_path = _text(path_payload.get("relative_path"))
            expected_hash = _text(path_payload.get("after_hash"))
            if relative_path is None or expected_hash is None:
                return False
            path = (resolved_root / package_root / relative_path).resolve()
            try:
                path.relative_to(resolved_root)
            except ValueError:
                return False
            if not path.is_file() or path.is_symlink():
                return False
            if sha256(path.read_bytes()).hexdigest() != expected_hash:
                return False
    return True


def _mapping(value: object) -> Mapping[str, object] | None:
    if isinstance(value, Mapping):
        return value
    to_payload = getattr(value, "to_payload", None)
    if not callable(to_payload):
        return None
    payload = to_payload()
    return payload if isinstance(payload, Mapping) else None


def _mapping_sequence(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


__all__ = ["resolve_currentness_replay"]
