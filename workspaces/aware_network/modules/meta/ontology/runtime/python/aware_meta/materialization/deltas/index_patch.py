from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.materialization.deltas.baseline import (
    _baseline_ref_payload,
    _mapping_value,
    _model_payload,
    _optional_text,
    _request_value,
    _tuple_text,
    _uuid_value,
)
from aware_meta.runtime.package_index import (
    MetaRuntimePackageIndexPatch,
    MetaRuntimePackageProjectionIndex,
    MetaRuntimeSemanticObjectIndexEntry,
    record_meta_runtime_package_index_patch,
)
from aware_meta_ontology.stable_ids import (
    stable_object_config_graph_id,
    stable_object_config_graph_package_id,
)


_RUNTIME_PACKAGE_INDEX_PATCH_CONTRACT_VERSION = (
    "aware.meta.ocg.provider-delta-runtime-package-index-patch.v1"
)


@dataclass(frozen=True, slots=True)
class _RuntimePackageIndexPatchContext:
    aware_root: Path
    package_name: str
    fqn_prefix: str
    manifest_path: Path


@dataclass(frozen=True, slots=True)
class _RuntimePackageIndexPatchBuild:
    patch: MetaRuntimePackageIndexPatch
    semantic_object_upsert_keys: tuple[str, ...]
    semantic_object_delete_keys: tuple[str, ...]
    blockers: tuple[str, ...] = ()


def _provider_delta_runtime_package_index_patch_receipt(
    *,
    request: object,
    provider_delta_typed_operation_plan: Mapping[str, object],
    provider_delta_head_move_applied_receipt: Mapping[str, object],
    provider_delta_oig_commit_receipt: Mapping[str, object],
    current_delta_fingerprint: str,
) -> dict[str, object]:
    commit_status = _optional_text(provider_delta_oig_commit_receipt.get("status"))
    head_receipt_status = _optional_text(
        provider_delta_head_move_applied_receipt.get("status")
    )
    head_refs = _mapping_value(
        provider_delta_head_move_applied_receipt.get("head_refs")
    )
    typed_plan_status = _optional_text(
        provider_delta_typed_operation_plan.get("status")
    )
    operations = _typed_operation_payloads(
        provider_delta_typed_operation_plan.get("typed_operations")
    )
    blockers = _runtime_package_index_patch_readiness_blockers(
        commit_status=commit_status,
        head_receipt_status=head_receipt_status,
        head_refs=head_refs,
        typed_plan_status=typed_plan_status,
    )
    if blockers:
        return _runtime_package_index_patch_receipt_payload(
            status="runtime_package_index_patch_blocked",
            reason="meta_ocg_provider_delta_runtime_package_index_patch_blocked",
            provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
            provider_delta_head_move_applied_receipt=(
                provider_delta_head_move_applied_receipt
            ),
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            current_delta_fingerprint=current_delta_fingerprint,
            blockers=blockers,
            head_refs=head_refs,
        )

    if not operations:
        return _runtime_package_index_patch_receipt_payload(
            status="runtime_package_index_patch_empty",
            reason="meta_ocg_provider_delta_runtime_package_index_patch_empty",
            provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
            provider_delta_head_move_applied_receipt=(
                provider_delta_head_move_applied_receipt
            ),
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            current_delta_fingerprint=current_delta_fingerprint,
            blockers=(),
            head_refs=head_refs,
            semantic_object_upsert_keys=(),
            semantic_object_delete_keys=(),
            applied_index=None,
        )
    context, context_blockers = _runtime_package_index_patch_context(
        request=request,
        operations=operations,
    )
    if context is None:
        return _runtime_package_index_patch_receipt_payload(
            status="runtime_package_index_patch_blocked",
            reason=("meta_ocg_provider_delta_runtime_package_index_context_incomplete"),
            provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
            provider_delta_head_move_applied_receipt=(
                provider_delta_head_move_applied_receipt
            ),
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            current_delta_fingerprint=current_delta_fingerprint,
            blockers=context_blockers,
            head_refs=head_refs,
        )

    build = _runtime_package_index_patch_from_operations(
        context=context,
        operations=operations,
        head_refs=head_refs,
        current_delta_fingerprint=current_delta_fingerprint,
    )
    if build.blockers:
        return _runtime_package_index_patch_receipt_payload(
            status="runtime_package_index_patch_blocked",
            reason=("meta_ocg_provider_delta_runtime_package_index_patch_incomplete"),
            provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
            provider_delta_head_move_applied_receipt=(
                provider_delta_head_move_applied_receipt
            ),
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            current_delta_fingerprint=current_delta_fingerprint,
            blockers=build.blockers,
            head_refs=head_refs,
            context=context,
            semantic_object_upsert_keys=build.semantic_object_upsert_keys,
            semantic_object_delete_keys=build.semantic_object_delete_keys,
        )
    if not build.semantic_object_upsert_keys and not build.semantic_object_delete_keys:
        return _runtime_package_index_patch_receipt_payload(
            status="runtime_package_index_patch_empty",
            reason="meta_ocg_provider_delta_runtime_package_index_patch_empty",
            provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
            provider_delta_head_move_applied_receipt=(
                provider_delta_head_move_applied_receipt
            ),
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            current_delta_fingerprint=current_delta_fingerprint,
            blockers=(),
            head_refs=head_refs,
            context=context,
            semantic_object_upsert_keys=(),
            semantic_object_delete_keys=(),
            applied_index=None,
        )

    applied_index = record_meta_runtime_package_index_patch(
        aware_root=context.aware_root,
        patch=build.patch,
    )
    if applied_index is None:
        return _runtime_package_index_patch_receipt_payload(
            status="runtime_package_index_patch_blocked",
            reason="meta_ocg_runtime_package_index_unavailable",
            provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
            provider_delta_head_move_applied_receipt=(
                provider_delta_head_move_applied_receipt
            ),
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            current_delta_fingerprint=current_delta_fingerprint,
            blockers=("runtime_package_index_unavailable",),
            head_refs=head_refs,
            context=context,
            semantic_object_upsert_keys=build.semantic_object_upsert_keys,
            semantic_object_delete_keys=build.semantic_object_delete_keys,
        )
    return _runtime_package_index_patch_receipt_payload(
        status="runtime_package_index_patch_applied",
        reason="meta_ocg_provider_delta_runtime_package_index_patch_applied",
        provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
        provider_delta_head_move_applied_receipt=(
            provider_delta_head_move_applied_receipt
        ),
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
        current_delta_fingerprint=current_delta_fingerprint,
        blockers=(),
        head_refs=head_refs,
        context=context,
        semantic_object_upsert_keys=build.semantic_object_upsert_keys,
        semantic_object_delete_keys=build.semantic_object_delete_keys,
        applied_index=applied_index,
    )


def _runtime_package_index_patch_readiness_blockers(
    *,
    commit_status: str | None,
    head_receipt_status: str | None,
    head_refs: Mapping[str, object],
    typed_plan_status: str | None,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if commit_status not in {
        "execute_flag_commit_applied",
        "execute_flag_commit_noop",
    }:
        blockers.append(f"oig_commit_not_applied:{commit_status or 'unknown'}")
    if head_receipt_status != "head_move_applied_receipt_ready":
        blockers.append(
            "head_move_applied_receipt_not_ready:" f"{head_receipt_status or 'unknown'}"
        )
    if head_refs.get("head_ref_status") != "head_refs_available":
        blockers.append(
            "head_refs_not_available:"
            f"{_optional_text(head_refs.get('head_ref_status')) or 'unknown'}"
        )
    if typed_plan_status != "typed_operation_plan_ready":
        blockers.append(
            f"typed_operation_plan_not_ready:{typed_plan_status or 'unknown'}"
        )
    return tuple(dict.fromkeys(blockers))


def _runtime_package_index_patch_context(
    *,
    request: object,
    operations: tuple[Mapping[str, object], ...],
) -> tuple[_RuntimePackageIndexPatchContext | None, tuple[str, ...]]:
    package_payload = _model_payload(_request_value(request=request, key="package"))
    baseline_ref = _baseline_ref_payload(request=request) or {}
    manifest_path = _path_from_text(
        package_payload.get("manifest_path")
        or baseline_ref.get("manifest_toml_path")
        or baseline_ref.get("manifest_path")
    )
    package_name = (
        _optional_text(package_payload.get("package_name"))
        or _optional_text(baseline_ref.get("semantic_package_name"))
        or _package_name_from_operations(operations=operations)
    )
    fqn_prefix = _optional_text(
        package_payload.get("fqn_prefix")
    ) or _fqn_prefix_from_operations(operations=operations)
    aware_root = _aware_root_from_request(
        request=request,
        manifest_path=manifest_path,
    )
    blockers: list[str] = []
    if aware_root is None:
        blockers.append("runtime_package_index_aware_root_unavailable")
    if manifest_path is None:
        blockers.append("runtime_package_index_manifest_path_unavailable")
    if package_name is None:
        blockers.append("runtime_package_index_package_name_unavailable")
    if fqn_prefix is None:
        blockers.append("runtime_package_index_fqn_prefix_unavailable")
    if blockers or aware_root is None or manifest_path is None:
        return None, tuple(blockers)
    if package_name is None or fqn_prefix is None:
        raise AssertionError("validated package index context unexpectedly missing")
    return (
        _RuntimePackageIndexPatchContext(
            aware_root=aware_root,
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            manifest_path=manifest_path,
        ),
        (),
    )


def _runtime_package_index_patch_from_operations(
    *,
    context: _RuntimePackageIndexPatchContext,
    operations: tuple[Mapping[str, object], ...],
    head_refs: Mapping[str, object],
    current_delta_fingerprint: str,
) -> _RuntimePackageIndexPatchBuild:
    blockers: list[str] = []
    upserts: list[MetaRuntimeSemanticObjectIndexEntry] = []
    deletes: list[str] = []
    for operation in operations:
        operation_family = _optional_text(operation.get("operation_family"))
        semantic_key = _optional_text(operation.get("semantic_key"))
        if semantic_key is None:
            blockers.append("typed_operation_semantic_key_unavailable")
            continue
        if operation_family == "delete":
            deletes.append(semantic_key)
            continue
        if operation_family not in {"create", "update"}:
            continue
        entry, entry_blockers = _semantic_object_upsert_entry(
            context=context,
            operation=operation,
            head_refs=head_refs,
            current_delta_fingerprint=current_delta_fingerprint,
        )
        if entry is None:
            blockers.extend(f"{semantic_key}:{blocker}" for blocker in entry_blockers)
            continue
        upserts.append(entry)

    return _RuntimePackageIndexPatchBuild(
        patch=MetaRuntimePackageIndexPatch(
            semantic_object_upserts=tuple(
                sorted(upserts, key=lambda item: item.semantic_key)
            ),
            semantic_object_deletes=tuple(sorted(dict.fromkeys(deletes))),
            runtime_delta_fingerprint=current_delta_fingerprint,
        ),
        semantic_object_upsert_keys=tuple(
            sorted(entry.semantic_key for entry in upserts)
        ),
        semantic_object_delete_keys=tuple(sorted(dict.fromkeys(deletes))),
        blockers=tuple(dict.fromkeys(blockers)),
    )


def _semantic_object_upsert_entry(
    *,
    context: _RuntimePackageIndexPatchContext,
    operation: Mapping[str, object],
    head_refs: Mapping[str, object],
    current_delta_fingerprint: str,
) -> tuple[MetaRuntimeSemanticObjectIndexEntry | None, tuple[str, ...]]:
    semantic_key = _optional_text(operation.get("semantic_key"))
    current = _mapping_value(operation.get("current"))
    current_payload = _mapping_value(current.get("payload"))
    baseline = _mapping_value(operation.get("baseline"))
    object_kind = (
        _optional_text(operation.get("ontology_subject_kind"))
        or _optional_text(current.get("object_kind"))
        or _optional_text(baseline.get("object_kind"))
    )
    if semantic_key is None or object_kind is None:
        blockers: list[str] = []
        if semantic_key is None:
            blockers.append("semantic_key_unavailable")
        if object_kind is None:
            blockers.append("object_kind_unavailable")
        return None, tuple(blockers)

    object_id = _semantic_object_id(
        operation_family=_optional_text(operation.get("operation_family")),
        object_kind=object_kind,
        semantic_key=semantic_key,
        package_name=context.package_name,
        fqn_prefix=context.fqn_prefix,
        current=current,
        current_payload=current_payload,
        baseline=baseline,
    )
    graph_semantic_key = _graph_semantic_key(
        semantic_key=semantic_key,
        current=current,
        current_payload=current_payload,
    )
    payload = _semantic_object_payload(
        operation=operation,
        current=current,
        current_payload=current_payload,
        baseline=baseline,
    )
    return (
        MetaRuntimeSemanticObjectIndexEntry(
            semantic_key=semantic_key,
            object_kind=object_kind,
            package_name=context.package_name,
            fqn_prefix=context.fqn_prefix,
            manifest_path=context.manifest_path,
            object_id=object_id,
            entity_id=_optional_text(
                current.get("entity_id")
                or current_payload.get("entity_id")
                or current_payload.get("attribute_config_id")
                or current_payload.get("node_id")
            ),
            graph_semantic_key=graph_semantic_key,
            parent_semantic_key=(
                _optional_text(current.get("parent_semantic_key"))
                or _optional_text(current_payload.get("parent_semantic_key"))
                or _optional_text(current.get("owner_semantic_key"))
                or _optional_text(current_payload.get("owner_semantic_key"))
            ),
            owner_semantic_key=(
                _optional_text(current.get("owner_semantic_key"))
                or _optional_text(current_payload.get("owner_semantic_key"))
                or _optional_text(current.get("parent_semantic_key"))
                or _optional_text(current_payload.get("parent_semantic_key"))
            ),
            node_key=(
                _optional_text(current.get("node_key"))
                or _optional_text(current_payload.get("node_key"))
            ),
            attribute_name=(
                _optional_text(current.get("attribute_name"))
                or _optional_text(current_payload.get("attribute_name"))
            ),
            source_refs=_source_refs(
                operation=operation, current_payload=current_payload
            ),
            object_config_graph_id=_object_config_graph_id(
                fqn_prefix=context.fqn_prefix,
                current=current,
                current_payload=current_payload,
            ),
            object_config_graph_hash=(
                _optional_text(current_payload.get("object_config_graph_hash"))
                or _optional_text(current_payload.get("hash"))
            ),
            semantic_root_object_instance_graph_commit_id=_uuid_value(
                head_refs.get("semantic_root_object_instance_graph_commit_id")
            ),
            semantic_package_object_instance_graph_commit_id=_uuid_value(
                head_refs.get("semantic_package_commit_id")
                or head_refs.get("semantic_object_instance_graph_commit_id")
            ),
            source_object_instance_graph_commit_id=_uuid_value(
                head_refs.get("source_object_instance_graph_commit_id")
            ),
            runtime_delta_fingerprint=current_delta_fingerprint,
            evidence_source="provider_delta_index_patch",
            payload=payload,
        ),
        (),
    )


def _semantic_object_id(
    *,
    operation_family: str | None,
    object_kind: str,
    semantic_key: str,
    package_name: str,
    fqn_prefix: str,
    current: Mapping[str, object],
    current_payload: Mapping[str, object],
    baseline: Mapping[str, object],
) -> UUID | None:
    if object_kind == "object_config_graph_package":
        return stable_object_config_graph_package_id(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        )
    if object_kind == "object_config_graph":
        return _object_config_graph_id(
            fqn_prefix=fqn_prefix,
            current=current,
            current_payload=current_payload,
        )
    if operation_family == "update":
        baseline_object_id = _uuid_value(baseline.get("object_id"))
        if baseline_object_id is not None:
            return baseline_object_id
    for value in (
        current.get("object_id"),
        current_payload.get("object_id"),
        current_payload.get("node_id"),
        current_payload.get("attribute_config_id"),
        current.get("entity_id"),
        current_payload.get("entity_id"),
        current_payload.get("id"),
        baseline.get("object_id"),
    ):
        object_id = _uuid_value(value)
        if object_id is not None:
            return object_id
    _ = semantic_key
    return None


def _object_config_graph_id(
    *,
    fqn_prefix: str,
    current: Mapping[str, object],
    current_payload: Mapping[str, object],
) -> UUID | None:
    for value in (
        current.get("object_config_graph_id"),
        current_payload.get("object_config_graph_id"),
        current_payload.get("id"),
    ):
        object_config_graph_id = _uuid_value(value)
        if object_config_graph_id is not None:
            return object_config_graph_id
    language = (
        _optional_text(current_payload.get("language"))
        or _optional_text(current.get("language"))
        or CodeLanguage.aware.value
    )
    return stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=language,
    )


def _semantic_object_payload(
    *,
    operation: Mapping[str, object],
    current: Mapping[str, object],
    current_payload: Mapping[str, object],
    baseline: Mapping[str, object],
) -> dict[str, object]:
    return {
        "source": "provider_delta_typed_operation",
        "operation_key": _optional_text(operation.get("operation_key")),
        "operation_family": _optional_text(operation.get("operation_family")),
        "provider_operation_type": _optional_text(
            operation.get("provider_operation_type")
        ),
        "semantic_subject_type": _optional_text(operation.get("semantic_subject_type")),
        "ontology_subject_kind": _optional_text(operation.get("ontology_subject_kind")),
        "baseline_object_id": _optional_text(baseline.get("object_id")),
        "baseline_object_kind": _optional_text(baseline.get("object_kind")),
        "semantic_fingerprint": _optional_text(
            current_payload.get("semantic_fingerprint")
        ),
        "attribute_signature": _mapping_value(current.get("attribute_signature")),
        "function_signature": _mapping_value(current.get("function_signature")),
        "function_impl_signature": _mapping_value(
            current.get("function_impl_signature")
        ),
        "relationship_signature": _mapping_value(current.get("relationship_signature")),
        "current": dict(current),
        "current_payload": dict(current_payload),
    }


def _runtime_package_index_patch_receipt_payload(
    *,
    status: str,
    reason: str,
    provider_delta_oig_commit_receipt: Mapping[str, object],
    provider_delta_head_move_applied_receipt: Mapping[str, object],
    provider_delta_typed_operation_plan: Mapping[str, object],
    current_delta_fingerprint: str,
    blockers: tuple[str, ...],
    head_refs: Mapping[str, object],
    context: _RuntimePackageIndexPatchContext | None = None,
    semantic_object_upsert_keys: tuple[str, ...] = (),
    semantic_object_delete_keys: tuple[str, ...] = (),
    applied_index: MetaRuntimePackageProjectionIndex | None = None,
) -> dict[str, object]:
    applied = status == "runtime_package_index_patch_applied"
    return {
        "receipt_kind": "meta_ocg_provider_delta_runtime_package_index_patch",
        "contract_version": _RUNTIME_PACKAGE_INDEX_PATCH_CONTRACT_VERSION,
        "status": status,
        "reason": reason,
        "available": status
        in {
            "runtime_package_index_patch_applied",
            "runtime_package_index_patch_empty",
        },
        "blocked": bool(blockers),
        "blockers": blockers,
        "blocker_count": len(blockers),
        "current_delta_fingerprint": current_delta_fingerprint,
        "provider_delta_oig_commit_receipt_status": _optional_text(
            provider_delta_oig_commit_receipt.get("status")
        ),
        "provider_delta_oig_commit_receipt_reason": _optional_text(
            provider_delta_oig_commit_receipt.get("reason")
        ),
        "provider_delta_head_move_applied_receipt_status": _optional_text(
            provider_delta_head_move_applied_receipt.get("status")
        ),
        "provider_delta_head_move_applied_receipt_reason": _optional_text(
            provider_delta_head_move_applied_receipt.get("reason")
        ),
        "provider_delta_typed_operation_plan_status": _optional_text(
            provider_delta_typed_operation_plan.get("status")
        ),
        "provider_delta_typed_operation_plan_reason": _optional_text(
            provider_delta_typed_operation_plan.get("reason")
        ),
        "typed_operation_count": _int_value(
            provider_delta_typed_operation_plan.get("typed_operation_count")
        ),
        "head_refs": dict(head_refs),
        "aware_root": context.aware_root.as_posix() if context is not None else None,
        "package_name": context.package_name if context is not None else None,
        "fqn_prefix": context.fqn_prefix if context is not None else None,
        "manifest_path": (
            context.manifest_path.as_posix() if context is not None else None
        ),
        "semantic_object_upsert_count": len(semantic_object_upsert_keys),
        "semantic_object_delete_count": len(semantic_object_delete_keys),
        "semantic_object_upsert_keys": semantic_object_upsert_keys,
        "semantic_object_delete_keys": semantic_object_delete_keys,
        "package_index_semantic_object_count": (
            len(applied_index.semantic_objects_by_key)
            if applied_index is not None
            else 0
        ),
        "would_execute": (
            _optional_text(provider_delta_oig_commit_receipt.get("status"))
            == "execute_flag_commit_applied"
        ),
        "would_persist": (
            _optional_text(provider_delta_head_move_applied_receipt.get("status"))
            == "head_move_applied_receipt_ready"
        ),
        "did_execute": applied,
        "did_persist": applied,
        "execution_wired": applied,
        "production_execution_wired": applied,
    }


def _typed_operation_payloads(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(_mapping_value(item) for item in value if isinstance(item, Mapping))


def _source_refs(
    *,
    operation: Mapping[str, object],
    current_payload: Mapping[str, object],
) -> tuple[str, ...]:
    source_refs = _tuple_text(operation.get("source_refs"))
    if source_refs:
        return source_refs
    return _tuple_text(current_payload.get("source_refs"))


def _graph_semantic_key(
    *,
    semantic_key: str,
    current: Mapping[str, object],
    current_payload: Mapping[str, object],
) -> str | None:
    graph_semantic_key = _optional_text(
        current.get("graph_semantic_key")
    ) or _optional_text(current_payload.get("graph_semantic_key"))
    if graph_semantic_key is not None:
        return graph_semantic_key
    if semantic_key.startswith("ocg:"):
        return semantic_key.split("/node:", 1)[0]
    return None


def _package_name_from_operations(
    *,
    operations: tuple[Mapping[str, object], ...],
) -> str | None:
    for operation in operations:
        current = _mapping_value(operation.get("current"))
        current_payload = _mapping_value(current.get("payload"))
        package_name = _optional_text(
            current_payload.get("package_name")
        ) or _optional_text(current.get("package_name"))
        if package_name is not None:
            return package_name
        semantic_key = _optional_text(operation.get("semantic_key"))
        if semantic_key is not None and semantic_key.startswith("ocg_package:"):
            return semantic_key.removeprefix("ocg_package:")
    return None


def _fqn_prefix_from_operations(
    *,
    operations: tuple[Mapping[str, object], ...],
) -> str | None:
    for operation in operations:
        current = _mapping_value(operation.get("current"))
        current_payload = _mapping_value(current.get("payload"))
        fqn_prefix = _optional_text(
            current_payload.get("fqn_prefix")
        ) or _optional_text(current.get("fqn_prefix"))
        if fqn_prefix is not None:
            return fqn_prefix
        for value in (
            current.get("graph_semantic_key"),
            current_payload.get("graph_semantic_key"),
            operation.get("semantic_key"),
        ):
            graph_key = _optional_text(value)
            if graph_key is not None and graph_key.startswith("ocg:"):
                return graph_key.removeprefix("ocg:").split("/node:", 1)[0]
    return None


def _aware_root_from_request(
    *,
    request: object,
    manifest_path: Path | None,
) -> Path | None:
    for key in ("aware_root", "workspace_root", "repo_root", "root_path"):
        value = _request_value(request=request, key=key)
        path = _path_from_text(value)
        if path is not None:
            return path.expanduser().resolve()
    if manifest_path is None:
        return None
    manifest = manifest_path.expanduser().resolve()
    for parent in (manifest.parent, *manifest.parents):
        if parent.name == "modules":
            return parent.parent
    return manifest.parent


def _path_from_text(value: object) -> Path | None:
    text = _optional_text(value)
    return Path(text).expanduser().resolve() if text is not None else None


def _int_value(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = _optional_text(value)
    if text is None:
        return 0
    try:
        return int(text)
    except ValueError:
        return 0


__all__ = [
    "_provider_delta_runtime_package_index_patch_receipt",
]
