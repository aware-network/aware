from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from uuid import UUID

from aware_code.semantic_materialization import (
    SemanticPackageMaterializationExecutionContextRequest,
)
from aware_api_ontology.stable_ids import stable_api_package_id
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.materialization import stable_semantic_package_branch_id
from aware_meta.runtime.graph_context import find_meta_graph_projection_hash_by_name
from aware_service_runtime.manifest.loader import load_aware_service_toml_spec


async def resolve_service_api_reference_branch_ids_by_api_name(
    request: SemanticPackageMaterializationExecutionContextRequest,
) -> Mapping[str, UUID]:
    """Resolve committed API branch refs required by Service materialization."""

    dependency_package_names = _service_dependency_package_names(
        service_toml_path=request.manifest_path,
    )
    if not dependency_package_names:
        return {}

    dependency_workspace_manifest_kind = (
        _provider_payload_text(
            request.provider_payload,
            "dependency_workspace_manifest_kind",
        )
        or "api"
    )
    api_projection_name = (
        _provider_payload_text(
            request.provider_payload,
            "dependency_projection_name",
        )
        or "ApiPackage"
    )
    try:
        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=request.index,
            projection_name=api_projection_name,
        )
    except ValueError:
        return {}

    entries_by_package_name = {
        entry["code_package_name"]: entry
        for entry in _workspace_semantic_package_entries(request.context)
        if entry.get("workspace_manifest_kind") == dependency_workspace_manifest_kind
    }
    dependency_entries_by_package_name = {
        entry["code_package_name"]: entry
        for entry in _workspace_dependency_semantic_package_entries(request.context)
        if entry.get("workspace_manifest_kind") == dependency_workspace_manifest_kind
    }
    local_commit_store = FSCommitStore()
    seeded: dict[str, UUID] = {}
    for package_name in dependency_package_names:
        dependency_entry = dependency_entries_by_package_name.get(package_name)
        if dependency_entry is not None:
            branch_id = await _validated_dependency_api_package_branch_id(
                entry=dependency_entry,
                package_name=package_name,
                api_projection_name=api_projection_name,
                api_projection_hash=api_projection_hash,
                commit_store=_dependency_entry_commit_store(
                    entry=dependency_entry,
                    package_name=package_name,
                ),
            )
            if branch_id is not None:
                seeded[package_name] = branch_id
                continue
        entry = entries_by_package_name.get(package_name)
        if entry is None:
            continue
        branch_id = _semantic_branch_id_for_entry(
            lane_branch_id=request.branch_id,
            entry=entry,
        )
        committed_head = await local_commit_store.head(
            branch_id=branch_id,
            projection_hash=api_projection_hash,
        )
        if committed_head is None:
            continue
        reference_tokens = (
            package_name,
            *_api_names_from_runtime_compile_plan(
                workspace_root=request.workspace_root,
                package_name=package_name,
            ),
        )
        for api_name in reference_tokens:
            existing = seeded.get(api_name)
            if existing is not None and existing != branch_id:
                raise RuntimeError(
                    "Service semantic context found duplicate committed API "
                    f"name {api_name!r}: first_branch_id={existing} "
                    f"second_branch_id={branch_id}"
                )
            seeded[api_name] = branch_id
    return seeded


async def _validated_dependency_api_package_branch_id(
    *,
    entry: Mapping[str, object],
    package_name: str,
    api_projection_name: str,
    api_projection_hash: str,
    commit_store: FSCommitStore,
) -> UUID | None:
    raw_lane_ref = entry.get("semantic_lane_ref")
    if not isinstance(raw_lane_ref, Mapping):
        return None
    projection_name = str(raw_lane_ref.get("semantic_projection_name") or "").strip()
    projection_hash = str(raw_lane_ref.get("projection_hash") or "").strip()
    if projection_name != api_projection_name or projection_hash != api_projection_hash:
        raise RuntimeError(
            "Service dependency API package witness projection mismatch: "
            f"package_name={package_name!r} projection_name={projection_name!r}"
        )
    expected_package_id = stable_api_package_id(name=package_name)
    witnessed_package_id = _uuid_or_none(raw_lane_ref.get("semantic_package_id"))
    if witnessed_package_id != expected_package_id:
        raise RuntimeError(
            "Service dependency API package witness identity mismatch: "
            f"package_name={package_name!r} expected={expected_package_id} "
            f"actual={witnessed_package_id}"
        )
    branch_id = _uuid_or_none(raw_lane_ref.get("branch_id"))
    head_commit_id = _uuid_or_none(raw_lane_ref.get("head_commit_id"))
    object_instance_graph_commit_id = _uuid_or_none(
        raw_lane_ref.get("object_instance_graph_commit_id")
    )
    if (
        branch_id is None
        or head_commit_id is None
        or object_instance_graph_commit_id is None
    ):
        raise RuntimeError(
            "Service dependency API package witness is incomplete: "
            f"package_name={package_name!r}"
        )
    committed_head = await commit_store.head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    committed_head_id = (
        _uuid_or_none(committed_head.get("commit_id"))
        if isinstance(committed_head, Mapping)
        else None
    )
    if committed_head_id != head_commit_id:
        raise RuntimeError(
            "Service dependency API package witness HEAD mismatch: "
            f"package_name={package_name!r} expected={head_commit_id} "
            f"actual={committed_head_id}"
        )
    return branch_id


def _dependency_entry_commit_store(
    *,
    entry: Mapping[str, object],
    package_name: str,
) -> FSCommitStore:
    raw_owner_root = entry.get("owner_workspace_root")
    if not isinstance(raw_owner_root, str) or not raw_owner_root.strip():
        raise RuntimeError(
            "Service dependency API package witness owner root is missing: "
            f"package_name={package_name!r}"
        )
    owner_root = Path(raw_owner_root).expanduser()
    if not owner_root.is_absolute():
        raise RuntimeError(
            "Service dependency API package witness owner root must be absolute: "
            f"package_name={package_name!r}"
        )
    return FSCommitStore(root_dir=owner_root.resolve())


def _service_dependency_package_names(*, service_toml_path: Path) -> tuple[str, ...]:
    try:
        spec = load_aware_service_toml_spec(toml_path=service_toml_path)
    except Exception:
        return ()
    package_names: list[str] = []
    seen: set[str] = set()
    for dependency in spec.dependencies:
        package_name = dependency.package_name.strip()
        if not package_name or package_name in seen:
            continue
        seen.add(package_name)
        package_names.append(package_name)
    return tuple(package_names)


def _workspace_semantic_package_entries(
    context: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    raw_entries = context.get("workspace_semantic_package_entries")
    if not isinstance(raw_entries, (list, tuple)):
        return ()
    entries: list[dict[str, object]] = []
    for raw_entry in raw_entries:
        if isinstance(raw_entry, Mapping):
            entries.append(dict(raw_entry))
    return tuple(entries)


def _workspace_dependency_semantic_package_entries(
    context: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    raw_entries = context.get("workspace_dependency_semantic_package_entries")
    if not isinstance(raw_entries, (list, tuple)):
        return ()
    return tuple(
        dict(raw_entry) for raw_entry in raw_entries if isinstance(raw_entry, Mapping)
    )


def _uuid_or_none(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return UUID(value)
    except ValueError:
        return None


def _semantic_branch_id_for_entry(
    *,
    lane_branch_id: UUID,
    entry: Mapping[str, object],
) -> UUID:
    metadata = entry.get("semantic_package_metadata")
    branch_mode = ""
    if isinstance(metadata, Mapping):
        branch_mode = str(metadata.get("workspace_materialization_branch") or "")
    if branch_mode.strip().casefold() in {"lane", "none"}:
        return lane_branch_id
    return stable_semantic_package_branch_id(
        parent_branch_id=lane_branch_id,
        package_name=str(entry.get("workspace_manifest_kind") or ""),
        fqn_prefix=str(entry.get("manifest_path") or ""),
    )


def _api_names_from_runtime_compile_plan(
    *,
    workspace_root: Path,
    package_name: str,
) -> tuple[str, ...]:
    compile_plan_path = (
        workspace_root
        / ".aware"
        / "api"
        / "runtime"
        / package_name
        / "api.compile_plan.json"
    )
    if not compile_plan_path.is_file():
        return ()
    try:
        payload = json.loads(compile_plan_path.read_text(encoding="utf-8") or "{}")
    except Exception:
        return ()
    if not isinstance(payload, dict):
        return ()
    api_names: list[str] = []
    for api_plan in payload.get("api_ontology") or ():
        if not isinstance(api_plan, dict):
            continue
        api_payload = api_plan.get("api")
        if not isinstance(api_payload, dict):
            continue
        api_name = str(api_payload.get("name") or "").strip()
        if api_name:
            api_names.append(api_name)
    return tuple(dict.fromkeys(api_names))


def _provider_payload_text(
    provider_payload: Mapping[str, object],
    key: str,
) -> str | None:
    value = provider_payload.get(key)
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


__all__ = ["resolve_service_api_reference_branch_ids_by_api_name"]
