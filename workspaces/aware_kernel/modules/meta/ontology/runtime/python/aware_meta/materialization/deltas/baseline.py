from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence, Sized
from dataclasses import dataclass
from inspect import isawaitable
from typing import Any, cast
from uuid import UUID

from aware_code.semantic_materialization import (
    SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY,
)
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.runtime.graph_context import find_meta_graph_projection_hash_by_name
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)


_BASELINE_DIRTY_PREFLIGHT_CONTRACT_VERSION = (
    "aware.meta.ocg.baseline-dirty-preflight.v1"
)
_BASELINE_HYDRATION_PREFLIGHT_CONTRACT_VERSION = (
    "aware.meta.ocg.baseline-hydration-preflight.v1"
)
_BASELINE_SEMANTIC_OBJECT_INDEX_CONTRACT_VERSION = (
    "aware.meta.ocg.baseline-semantic-object-index.v1"
)
_BASELINE_COMMIT_REF_FIELDS = (
    "baseline_source_object_instance_graph_commit_id",
    "baseline_semantic_object_instance_graph_commit_id",
    "baseline_semantic_root_object_instance_graph_commit_id",
)
_BASELINE_REF_HYDRATOR_REQUIRED_FIELDS = (
    "source_object_instance_graph_commit_id",
    "semantic_branch_id",
    "semantic_projection_name",
    "semantic_package_id",
    "semantic_object_instance_graph_commit_id",
    "semantic_root_kind",
    "semantic_root_id",
    "semantic_root_object_instance_graph_commit_id",
)
_BASELINE_OIG_DIRECT_SEMANTIC_KEY_FIELDS = (
    "semantic_key",
    "semantic_object_key",
    "source_semantic_key",
)
_BASELINE_OIG_GRAPH_SEMANTIC_KEY_FIELDS = (
    "graph_semantic_key",
    "object_config_graph_semantic_key",
    "ocg_semantic_key",
)
_BASELINE_OIG_ATTRIBUTE_OWNER_SEMANTIC_KEY_FIELDS = (
    "parent_semantic_key",
    "owner_semantic_key",
    "node_semantic_key",
    "class_semantic_key",
    "function_semantic_key",
)
_BASELINE_OIG_FUNCTION_IMPL_KEY_DEFAULT = "default"
_BASELINE_OIG_FUNCTION_IMPL_KIND_DEFAULT = "instruction_body"
_BASELINE_OIG_FUNCTION_CONFIG_RELATIONSHIP_KEYS = frozenset(
    (
        "function_config",
        "function",
    )
)
_BASELINE_OIG_FUNCTION_IMPL_RELATIONSHIP_KEYS = frozenset(
    (
        "function_impl",
        "impl",
    )
)
_BASELINE_OIG_ATTRIBUTE_IDENTITY_FIELD_NAMES = frozenset(
    (
        *_BASELINE_OIG_DIRECT_SEMANTIC_KEY_FIELDS,
        *_BASELINE_OIG_GRAPH_SEMANTIC_KEY_FIELDS,
        "node_key",
        "node_type",
    )
)
_BASELINE_OIG_NODE_KINDS = frozenset(
    ("class", "enum", "relationship", "function", "object_config_graph_node")
)
_BASELINE_OIG_LAYOUT_KIND = "object_config_graph_node_layout"
_BASELINE_OIG_SOURCE_REF_ATTRIBUTE_FIELDS = (
    "source_refs",
    "source_paths",
    "source_path",
    "relative_path",
)


@dataclass(frozen=True, slots=True)
class _BaselineOigSourceRefContext:
    source_refs_by_class_instance_id: Mapping[str, tuple[str, ...]]
    source_refs_by_semantic_key: Mapping[str, tuple[str, ...]]
    semantic_key_by_class_instance_id: Mapping[str, str]
    all_source_refs: tuple[str, ...]


class _BaselineHydrationTimings:
    def __init__(self) -> None:
        self.metrics: dict[str, object] = {}

    def metric(self, key: str, value: object) -> object:
        if not key:
            return None
        json_value = _json_safe_metric_value(value)
        if json_value is None:
            return None
        self.metrics[str(key)] = json_value
        return None


async def _baseline_dirty_preflight(*, request: object) -> dict[str, object]:
    baseline_refs = _baseline_commit_refs(request=request)
    baseline_ref = _baseline_ref_payload(request=request)
    missing_fields = tuple(
        field_name
        for field_name in _BASELINE_COMMIT_REF_FIELDS
        if not baseline_refs.get(field_name)
    )
    missing_baseline_ref_fields = _baseline_ref_missing_required_fields(
        baseline_ref=baseline_ref,
    )
    commit_backed_baseline_available = not missing_fields
    baseline_ref_hydrator_ready = (
        baseline_ref is not None and not missing_baseline_ref_fields
    )
    hydration_preflight = await _baseline_hydration_preflight(
        request=request,
        baseline_ref=baseline_ref,
        commit_backed_baseline_available=commit_backed_baseline_available,
        missing_baseline_ref_fields=missing_baseline_ref_fields,
    )
    previous_evidence = getattr(request, "previous_materialization_evidence", None)
    previous_evidence_source = None
    if isinstance(previous_evidence, Mapping):
        previous_evidence_source = _optional_text(
            previous_evidence.get("evidence_source")
        )
    semantic_dirty_diff_status = _baseline_dirty_diff_status(
        commit_backed_baseline_available=commit_backed_baseline_available,
        baseline_ref_hydrator_ready=baseline_ref_hydrator_ready,
        hydration_preflight=hydration_preflight,
    )
    did_hydrate_baseline = hydration_preflight["status"] == "baseline_hydrated"
    return {
        "preflight_kind": "meta_ocg_baseline_dirty_preflight",
        "contract_version": _BASELINE_DIRTY_PREFLIGHT_CONTRACT_VERSION,
        "status": (
            "baseline_commit_refs_available"
            if commit_backed_baseline_available
            else "baseline_context_missing"
        ),
        "reason": (
            "meta_ocg_dirty_preflight_has_commit_backed_baseline"
            if commit_backed_baseline_available
            else "meta_ocg_dirty_preflight_requires_committed_baseline_refs"
        ),
        "source": "workspace.provider_delta_request",
        "commit_backed_baseline_available": commit_backed_baseline_available,
        "baseline_ref_available": baseline_ref is not None,
        "baseline_ref_hydrator_ready": baseline_ref_hydrator_ready,
        "semantic_dirty_diff_available": False,
        "semantic_dirty_diff_status": semantic_dirty_diff_status,
        "semantic_dirty_diff_reason": (
            _baseline_dirty_diff_unavailable_reason(
                commit_backed_baseline_available=commit_backed_baseline_available,
                baseline_ref_hydrator_ready=baseline_ref_hydrator_ready,
                hydration_preflight=hydration_preflight,
            )
        ),
        "did_hydrate_baseline": did_hydrate_baseline,
        "did_compare_against_current_delta": False,
        "baseline_hydration_preflight": hydration_preflight,
        "required_fields": _BASELINE_COMMIT_REF_FIELDS,
        "missing_required_fields": missing_fields,
        "baseline_commit_refs": baseline_refs,
        "baseline_ref_required_fields": _BASELINE_REF_HYDRATOR_REQUIRED_FIELDS,
        "baseline_ref_missing_required_fields": missing_baseline_ref_fields,
        "baseline_ref": baseline_ref,
        "previous_materialization_evidence_source": previous_evidence_source,
    }


async def _baseline_hydration_preflight(
    *,
    request: object,
    baseline_ref: Mapping[str, object] | None,
    commit_backed_baseline_available: bool,
    missing_baseline_ref_fields: tuple[str, ...],
) -> dict[str, object]:
    if not commit_backed_baseline_available:
        return _baseline_hydration_payload(
            status="baseline_context_missing",
            reason="meta_ocg_baseline_hydration_requires_commit_backed_baseline",
            source="workspace.provider_delta_request",
            baseline_ref=baseline_ref,
            hydrator_available=False,
        )
    if baseline_ref is None:
        return _baseline_hydration_payload(
            status="baseline_ref_missing",
            reason="meta_ocg_baseline_hydration_requires_workspace_baseline_ref",
            source="workspace.provider_delta_request",
            baseline_ref=None,
            hydrator_available=False,
        )
    if missing_baseline_ref_fields:
        return _baseline_hydration_payload(
            status="baseline_ref_incomplete",
            reason="meta_ocg_baseline_ref_missing_required_hydration_fields",
            source="workspace.provider_delta_request",
            baseline_ref=baseline_ref,
            hydrator_available=False,
            details={"missing_required_fields": missing_baseline_ref_fields},
        )

    request_hydrator = _request_baseline_oig_hydrator(request=request)
    if request_hydrator is not None:
        return await _hydrate_baseline_from_request_hydrator(
            hydrator=request_hydrator,
            request=request,
            baseline_ref=baseline_ref,
        )

    index = await _request_runtime_index(request=request)
    if index is None:
        return _baseline_hydration_payload(
            status="baseline_hydrator_unavailable",
            reason="meta_ocg_baseline_hydration_requires_runtime_index_or_adapter",
            source="workspace.provider_delta_request",
            baseline_ref=baseline_ref,
            hydrator_available=False,
        )
    return await _hydrate_baseline_from_runtime_index(
        request=request,
        index=index,
        baseline_ref=baseline_ref,
    )


async def _hydrate_baseline_from_request_hydrator(
    *,
    hydrator: Callable[..., object],
    request: object,
    baseline_ref: Mapping[str, object],
) -> dict[str, object]:
    try:
        hydrated = hydrator(request=request, baseline_ref=baseline_ref)
        if isawaitable(hydrated):
            hydrated = await hydrated
    except Exception as exc:
        return _baseline_hydration_failed_payload(
            baseline_ref=baseline_ref,
            source="request.baseline_oig_hydrator",
            exc=exc,
        )
    return _baseline_hydration_result_payload(
        hydrated=hydrated,
        baseline_ref=baseline_ref,
        source="request.baseline_oig_hydrator",
    )


async def _hydrate_baseline_from_runtime_index(
    *,
    request: object,
    index: object,
    baseline_ref: Mapping[str, object],
) -> dict[str, object]:
    projection_name = _optional_text(baseline_ref.get("semantic_projection_name"))
    if projection_name is None:
        return _baseline_hydration_payload(
            status="baseline_ref_incomplete",
            reason="meta_ocg_baseline_ref_missing_required_hydration_fields",
            source="workspace.provider_delta_request",
            baseline_ref=baseline_ref,
            hydrator_available=True,
            details={"missing_required_fields": ("semantic_projection_name",)},
        )
    try:
        projection_hash = _projection_hash_by_name(
            index=index,
            projection_name=projection_name,
        )
        opg = _opg_by_projection_hash(index=index, projection_hash=projection_hash)
    except Exception as exc:
        return _baseline_hydration_payload(
            status="baseline_projection_unresolved",
            reason="meta_ocg_baseline_projection_unresolved",
            source="meta_runtime_index",
            baseline_ref=baseline_ref,
            semantic_projection_hash=None,
            hydrator_available=True,
            details={"error": f"{type(exc).__name__}: {exc}"},
        )
    branch_id = _uuid_value(baseline_ref.get("semantic_branch_id"))
    commit_id = _uuid_value(
        baseline_ref.get("semantic_object_instance_graph_commit_id")
    )
    invalid_fields: list[str] = []
    if branch_id is None:
        invalid_fields.append("semantic_branch_id")
    if commit_id is None:
        invalid_fields.append("semantic_object_instance_graph_commit_id")
    if invalid_fields:
        return _baseline_hydration_payload(
            status="baseline_ref_invalid",
            reason="meta_ocg_baseline_ref_contains_non_uuid_commit_identity",
            source="workspace.provider_delta_request",
            baseline_ref=baseline_ref,
            semantic_projection_hash=projection_hash,
            hydrator_available=True,
            details={"invalid_fields": tuple(invalid_fields)},
        )
    if branch_id is None or commit_id is None:
        raise AssertionError("validated baseline commit identity unexpectedly missing")
    try:
        materializer = CachedLaneMaterializer()
        timings = _BaselineHydrationTimings()
        oig, materializer_metadata = await materializer.get(
            branch_id=branch_id,
            ocg=cast(Any, getattr(index, "ocg")),
            opg=cast(Any, opg),
            commit_id=commit_id,
            attribute_configs_by_id=cast(
                Any,
                getattr(index, "attribute_configs_by_id", None),
            ),
            class_configs_by_id=cast(
                Any,
                getattr(index, "class_configs_by_id", None),
            ),
            timings=timings,
        )
    except Exception as exc:
        return _baseline_hydration_failed_payload(
            baseline_ref=baseline_ref,
            source="aware_meta.CachedLaneMaterializer",
            exc=exc,
            semantic_projection_hash=projection_hash,
        )
    request_baseline_index = _request_baseline_semantic_object_index(
        request=request,
        baseline_ref=baseline_ref,
    )
    baseline_semantic_object_index_source = (
        "request.baseline_semantic_object_index"
        if request_baseline_index
        else "object_instance_graph"
    )
    materializer_metadata_payload = _mapping_value(materializer_metadata)
    materializer_metadata_payload.setdefault(
        "baseline_semantic_object_index_source",
        baseline_semantic_object_index_source,
    )
    materializer_metadata_payload.setdefault(
        "materialization_cache_metrics",
        materializer.snapshot_cache_metrics(),
    )
    materializer_metadata_payload.setdefault(
        "oig_materializer_phase_metrics",
        dict(timings.metrics),
    )
    materializer_metadata_payload.setdefault(
        "oig_materializer_phase_metric_count",
        len(timings.metrics),
    )
    return _baseline_hydrated_payload(
        baseline_ref=baseline_ref,
        source="aware_meta.CachedLaneMaterializer",
        semantic_projection_hash=projection_hash,
        object_counts=_object_counts_from_oig(oig),
        baseline_semantic_object_index=(
            request_baseline_index
            or _baseline_semantic_object_index_from_oig(
                oig=oig,
                baseline_ref=baseline_ref,
            )
        ),
        materializer_metadata=materializer_metadata_payload,
    )


def _baseline_hydration_result_payload(
    *,
    hydrated: object,
    baseline_ref: Mapping[str, object],
    source: str,
) -> dict[str, object]:
    oig, payload = _coerce_hydrated_oig_payload(hydrated=hydrated)
    blocked_payload = _structured_hydrator_blocked_payload(
        payload=payload,
        baseline_ref=baseline_ref,
        source=source,
    )
    if blocked_payload is not None:
        return blocked_payload
    object_counts = (
        _object_counts_from_oig(oig)
        if oig is not None
        else _object_counts_from_payload(payload=payload)
    )
    baseline_semantic_object_index = _baseline_semantic_object_index_from_payload(
        payload=payload,
        baseline_ref=baseline_ref,
    )
    if not baseline_semantic_object_index and oig is not None:
        baseline_semantic_object_index = _baseline_semantic_object_index_from_oig(
            oig=oig,
            baseline_ref=baseline_ref,
        )
    if object_counts is None:
        return _baseline_hydration_payload(
            status="baseline_hydration_failed",
            reason="meta_ocg_baseline_hydrator_returned_no_oig_counts",
            source=source,
            baseline_ref=baseline_ref,
            semantic_projection_hash=_semantic_projection_hash_from_payload(
                payload=payload,
            ),
            hydrator_available=True,
            details={"hydrator_result_keys": tuple(sorted(payload))},
        )
    materializer_metadata = _mapping_value(
        payload.get("materializer_metadata") or payload.get("metadata")
    )
    return _baseline_hydrated_payload(
        baseline_ref=baseline_ref,
        source=source,
        semantic_projection_hash=_semantic_projection_hash_from_payload(
            payload=payload,
        ),
        object_counts=object_counts,
        baseline_semantic_object_index=baseline_semantic_object_index,
        materializer_metadata=materializer_metadata,
        object_instance_graph_identity_id=(
            _optional_text(payload.get("object_instance_graph_identity_id"))
            or _optional_text(
                materializer_metadata.get("object_instance_graph_identity_id")
            )
        ),
        object_instance_graph_id=(
            _optional_text(payload.get("object_instance_graph_id"))
            or _optional_text(materializer_metadata.get("object_instance_graph_id"))
        ),
        root_object_id=(
            _optional_text(payload.get("root_object_id"))
            or _optional_text(materializer_metadata.get("root_object_id"))
        ),
    )


def _structured_hydrator_blocked_payload(
    *,
    payload: Mapping[str, object],
    baseline_ref: Mapping[str, object],
    source: str,
) -> dict[str, object] | None:
    status = _optional_text(payload.get("status"))
    if status is None or status == "baseline_hydrated":
        return None
    if not status.startswith("baseline_"):
        return None
    details = _mapping_value(payload.get("details"))
    details.update(
        {
            "hydrator_payload_status": status,
            "hydrator_payload_reason": _optional_text(payload.get("reason")),
            "hydrator_payload_source": _optional_text(payload.get("source")),
            "hydrator_payload_contract_version": _optional_text(
                payload.get("contract_version")
            ),
        }
    )
    return _baseline_hydration_payload(
        status=status,
        reason=(
            _optional_text(payload.get("reason"))
            or "meta_ocg_baseline_hydrator_returned_structured_block"
        ),
        source=_optional_text(payload.get("source")) or source,
        baseline_ref=baseline_ref,
        semantic_projection_hash=_semantic_projection_hash_from_payload(
            payload=payload,
        ),
        hydrator_available=True,
        details=details,
    )


def _baseline_hydrated_payload(
    *,
    baseline_ref: Mapping[str, object],
    source: str,
    semantic_projection_hash: str | None,
    object_counts: Mapping[str, int],
    baseline_semantic_object_index: Mapping[str, Mapping[str, object]] | None = None,
    materializer_metadata: Mapping[str, object] | None = None,
    object_instance_graph_identity_id: str | None = None,
    object_instance_graph_id: str | None = None,
    root_object_id: str | None = None,
) -> dict[str, object]:
    payload = _baseline_hydration_payload(
        status="baseline_hydrated",
        reason="meta_ocg_baseline_oig_hydrated_from_workspace_ref",
        source=source,
        baseline_ref=baseline_ref,
        semantic_projection_hash=semantic_projection_hash,
        hydrator_available=True,
        details={
            "materializer_metadata": dict(materializer_metadata or {}),
        },
    )
    counts = dict(object_counts)
    baseline_index = dict(baseline_semantic_object_index or {})
    baseline_index_available = bool(baseline_index)
    payload.update(
        {
            "object_counts": counts,
            "class_instance_count": counts.get("class_instances", 0),
            "class_instance_relationship_count": counts.get(
                "class_instance_relationships",
                0,
            ),
            "baseline_semantic_object_index_contract_version": (
                _BASELINE_SEMANTIC_OBJECT_INDEX_CONTRACT_VERSION
            ),
            "baseline_semantic_object_index_status": (
                "baseline_semantic_object_index_ready"
                if baseline_index_available
                else "baseline_semantic_object_index_unavailable"
            ),
            "baseline_semantic_object_index_available": baseline_index_available,
            "baseline_semantic_object_index_count": len(baseline_index),
            "baseline_semantic_object_index": baseline_index,
            "object_instance_graph_identity_id": object_instance_graph_identity_id,
            "object_instance_graph_id": object_instance_graph_id,
            "root_object_id": root_object_id,
        }
    )
    return payload


def _baseline_hydration_failed_payload(
    *,
    baseline_ref: Mapping[str, object],
    source: str,
    exc: Exception,
    semantic_projection_hash: str | None = None,
) -> dict[str, object]:
    return _baseline_hydration_payload(
        status="baseline_hydration_failed",
        reason="meta_ocg_baseline_hydration_failed",
        source=source,
        baseline_ref=baseline_ref,
        semantic_projection_hash=semantic_projection_hash,
        hydrator_available=True,
        details={"error": f"{type(exc).__name__}: {exc}"},
    )


def _baseline_hydration_payload(
    *,
    status: str,
    reason: str,
    source: str,
    baseline_ref: Mapping[str, object] | None,
    hydrator_available: bool,
    semantic_projection_hash: str | None = None,
    details: Mapping[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "preflight_kind": "meta_ocg_baseline_hydration_preflight",
        "contract_version": _BASELINE_HYDRATION_PREFLIGHT_CONTRACT_VERSION,
        "status": status,
        "reason": reason,
        "source": source,
        "baseline_identity_source": "workspace.baseline_ref",
        "hydrator_available": hydrator_available,
        "would_persist": False,
        "did_persist": False,
        "did_hydrate": status == "baseline_hydrated",
        "source_object_instance_graph_commit_id": None,
        "semantic_branch_id": None,
        "semantic_package_id": None,
        "semantic_package_commit_id": None,
        "semantic_projection_name": None,
        "semantic_projection_hash": semantic_projection_hash,
        "semantic_object_instance_graph_commit_id": None,
        "semantic_root_kind": None,
        "semantic_root_id": None,
        "semantic_root_object_instance_graph_commit_id": None,
        "object_instance_graph_identity_id": None,
        "object_instance_graph_id": None,
        "root_object_id": None,
        "object_counts": {
            "class_instances": 0,
            "class_instance_relationships": 0,
        },
        "class_instance_count": 0,
        "class_instance_relationship_count": 0,
        "baseline_semantic_object_index_contract_version": (
            _BASELINE_SEMANTIC_OBJECT_INDEX_CONTRACT_VERSION
        ),
        "baseline_semantic_object_index_status": "baseline_not_hydrated",
        "baseline_semantic_object_index_available": False,
        "baseline_semantic_object_index_count": 0,
        "baseline_semantic_object_index": {},
        "details": dict(details or {}),
    }
    if baseline_ref is not None:
        payload.update(
            {
                "source_object_instance_graph_commit_id": _optional_text(
                    baseline_ref.get("source_object_instance_graph_commit_id")
                ),
                "semantic_branch_id": _optional_text(
                    baseline_ref.get("semantic_branch_id")
                ),
                "semantic_package_id": _optional_text(
                    baseline_ref.get("semantic_package_id")
                ),
                "semantic_package_commit_id": _optional_text(
                    baseline_ref.get("semantic_package_commit_id")
                ),
                "semantic_projection_name": _optional_text(
                    baseline_ref.get("semantic_projection_name")
                ),
                "semantic_object_instance_graph_commit_id": _optional_text(
                    baseline_ref.get("semantic_object_instance_graph_commit_id")
                ),
                "semantic_root_kind": _optional_text(
                    baseline_ref.get("semantic_root_kind")
                ),
                "semantic_root_id": _optional_text(
                    baseline_ref.get("semantic_root_id")
                ),
                "semantic_root_object_instance_graph_commit_id": _optional_text(
                    baseline_ref.get(
                        "semantic_root_object_instance_graph_commit_id"
                    )
                ),
            }
        )
    return payload


def _request_baseline_oig_hydrator(
    *,
    request: object,
) -> Callable[..., object] | None:
    candidate = _request_or_durable_execution_input_value(
        request=request,
        keys=(
            "baseline_oig_hydrator",
            "baseline_hydrator",
            "meta_baseline_hydrator",
        ),
    )
    return candidate if callable(candidate) else None


async def _request_runtime_index(*, request: object) -> object | None:
    for key in ("index", "runtime_index"):
        candidate = _request_value(request=request, key=key)
        if _looks_like_runtime_index(candidate):
            return candidate
    for key in ("runtime", "harness"):
        candidate = _request_value(request=request, key=key)
        index_method = getattr(candidate, "index", None)
        if callable(index_method):
            try:
                value = index_method()
                if isawaitable(value):
                    value = await value
            except Exception:
                continue
            if _looks_like_runtime_index(value):
                return value
    return None


def _request_value(*, request: object, key: str) -> object | None:
    if isinstance(request, Mapping):
        value = request.get(key)
        if value is not None:
            return value
    value = getattr(request, key, None)
    if value is not None:
        return value
    context = getattr(request, "context", None)
    if isinstance(context, Mapping):
        return context.get(key)
    return getattr(context, key, None) if context is not None else None


def _looks_like_runtime_index(value: object) -> bool:
    return (
        value is not None
        and getattr(value, "ocg", None) is not None
        and isinstance(getattr(value, "opg_by_hash", None), Mapping)
    )


def _projection_hash_by_name(*, index: object, projection_name: str) -> str:
    try:
        return find_meta_graph_projection_hash_by_name(
            index=cast(Any, index),
            projection_name=projection_name,
        )
    except Exception:
        matches = sorted(
            {
                str(projection_hash)
                for projection_hash, opg in _mapping_items(
                    getattr(index, "opg_by_hash", None)
                )
                if (str(getattr(opg, "name", "") or "").strip())
                == projection_name.strip()
            }
        )
        if len(matches) == 1:
            return matches[0]
        if not matches:
            raise ValueError(
                f"Projection {projection_name!r} was not found in runtime index"
            )
        raise ValueError(
            f"Projection {projection_name!r} matched multiple hashes: {matches}"
        )


def _opg_by_projection_hash(*, index: object, projection_hash: str) -> object:
    opg_by_hash = getattr(index, "opg_by_hash", None)
    if isinstance(opg_by_hash, Mapping):
        opg = opg_by_hash.get(projection_hash)
        if opg is not None:
            return opg
    ocg = getattr(index, "ocg", None)
    for opg in getattr(ocg, "object_projection_graphs", ()) or ():
        if _optional_text(getattr(opg, "projection_hash", None)) == projection_hash:
            return opg
    raise ValueError(f"Projection hash {projection_hash!r} was not found")


def _mapping_items(value: object) -> tuple[tuple[object, object], ...]:
    if not isinstance(value, Mapping):
        return ()
    return tuple(value.items())


def _uuid_value(value: object) -> UUID | None:
    text = _optional_text(value)
    if text is None:
        return None
    try:
        return UUID(text)
    except ValueError:
        return None


def _coerce_hydrated_oig_payload(
    *,
    hydrated: object,
) -> tuple[object | None, dict[str, object]]:
    if isinstance(hydrated, tuple) and hydrated:
        oig = hydrated[0]
        payload = _model_payload(hydrated[1]) if len(hydrated) > 1 else {}
        return oig, payload
    payload = _model_payload(hydrated)
    oig = payload.get("object_instance_graph") or payload.get("oig")
    if oig is None and _looks_like_oig(hydrated):
        oig = hydrated
    return oig, payload


def _looks_like_oig(value: object) -> bool:
    return (
        value is not None
        and getattr(value, "class_instances", None) is not None
        and getattr(value, "class_instance_relationships", None) is not None
    )


def _baseline_semantic_object_index_from_payload(
    *,
    payload: Mapping[str, object],
    baseline_ref: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    for key in (
        "baseline_semantic_object_index",
        "semantic_object_index",
        "baseline_semantic_objects_by_key",
        "semantic_objects_by_key",
        "current_semantic_object_ids",
    ):
        index = _normalize_baseline_semantic_object_index(
            value=payload.get(key),
            baseline_ref=baseline_ref,
            source=f"hydrator_payload.{key}",
        )
        if index:
            return index
    return {}


def _request_baseline_semantic_object_index(
    *,
    request: object,
    baseline_ref: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    for key in (
        "baseline_semantic_object_index",
        "semantic_object_index",
        "baseline_semantic_objects_by_key",
        "semantic_objects_by_key",
        "current_semantic_object_ids",
    ):
        normalized = _normalize_baseline_semantic_object_index(
            value=_request_value(request=request, key=key),
            baseline_ref=baseline_ref,
            source=f"request.{key}",
        )
        if normalized:
            return normalized

    previous_evidence = _request_value(
        request=request,
        key="previous_materialization_evidence",
    )
    evidence_payload = _mapping_value(previous_evidence)
    normalized = _baseline_semantic_object_index_from_payload(
        payload=evidence_payload,
        baseline_ref=baseline_ref,
    )
    if normalized:
        return normalized

    context_payload = _mapping_value(_request_value(request=request, key="context"))
    return _baseline_semantic_object_index_from_payload(
        payload=context_payload,
        baseline_ref=baseline_ref,
    )


def _baseline_semantic_object_index_from_oig(
    *,
    oig: object,
    baseline_ref: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    if isinstance(oig, ObjectInstanceGraph):
        return _baseline_semantic_object_index_from_typed_oig(
            oig=oig,
            baseline_ref=baseline_ref,
        )
    entries: dict[str, dict[str, object]] = {}
    source_ref_context = _baseline_oig_source_ref_context(
        oig=oig,
        baseline_ref=baseline_ref,
    )
    for class_instance in tuple(getattr(oig, "class_instances", ()) or ()):
        semantic_key = _baseline_oig_object_semantic_key(value=class_instance)
        if semantic_key is None:
            continue
        attr_values = _class_instance_attribute_text_values(value=class_instance)
        object_kind = _baseline_oig_object_kind(value=class_instance)
        source_refs = _baseline_oig_object_source_refs(
            class_instance=class_instance,
            semantic_key=semantic_key,
            object_kind=object_kind,
            source_ref_context=source_ref_context,
            baseline_ref=baseline_ref,
        )
        entries[semantic_key] = _baseline_semantic_object_index_entry(
            semantic_key=semantic_key,
            value={
                "object_id": _optional_text(getattr(class_instance, "id", None)),
                "object_kind": object_kind,
                "class_config_id": _optional_text(
                    getattr(class_instance, "class_config_id", None)
                ),
                "source_object_id": _optional_text(
                    getattr(class_instance, "source_object_id", None)
                ),
                "source_refs": source_refs,
                "class_fqn": attr_values.get("class_fqn"),
                "name": attr_values.get("name"),
                "description": attr_values.get("description"),
                "is_base": attr_values.get("is_base"),
                "is_edge": attr_values.get("is_edge"),
                "value_mode": attr_values.get("value_mode"),
                "identity_mode": attr_values.get("identity_mode"),
                "class_signature": _class_signature_payload(attr_values),
            },
            baseline_ref=baseline_ref,
            source="object_instance_graph.class_instances",
        )
        entries.update(
            _baseline_oig_attribute_entries_for_class_instance(
                class_instance=class_instance,
                owner_semantic_key=semantic_key,
                owner_kind=object_kind,
                owner_source_refs=source_refs,
                baseline_ref=baseline_ref,
            )
        )
    entries.update(
        _baseline_oig_function_impl_entries(
            oig=oig,
            source_ref_context=source_ref_context,
            baseline_ref=baseline_ref,
        )
    )
    for relationship in tuple(
        getattr(oig, "class_instance_relationships", ()) or ()
    ):
        semantic_key = _baseline_oig_object_semantic_key(value=relationship)
        if semantic_key is None:
            continue
        entries[semantic_key] = _baseline_semantic_object_index_entry(
            semantic_key=semantic_key,
            value={
                "object_id": _optional_text(getattr(relationship, "id", None)),
                "object_kind": "relationship",
                "class_config_relationship_id": _optional_text(
                    getattr(relationship, "class_config_relationship_id", None)
                ),
                "source_class_instance_id": _optional_text(
                    getattr(relationship, "source_class_instance_id", None)
                ),
                "target_class_instance_id": _optional_text(
                    getattr(relationship, "target_class_instance_id", None)
                ),
            },
            baseline_ref=baseline_ref,
            source="object_instance_graph.class_instance_relationships",
        )
    return dict(sorted(entries.items()))


def _baseline_semantic_object_index_from_typed_oig(
    *,
    oig: ObjectInstanceGraph,
    baseline_ref: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    entries: dict[str, dict[str, object]] = {}
    source_ref_context = _typed_baseline_oig_source_ref_context(
        oig=oig,
        baseline_ref=baseline_ref,
    )
    for class_instance in oig.class_instances:
        semantic_key = _typed_baseline_oig_object_semantic_key(
            value=class_instance,
        )
        if semantic_key is None:
            continue
        attr_values = _typed_class_instance_attribute_text_values(
            value=class_instance,
        )
        object_kind = _typed_baseline_oig_object_kind(value=class_instance)
        source_refs = _typed_baseline_oig_object_source_refs(
            class_instance=class_instance,
            semantic_key=semantic_key,
            object_kind=object_kind,
            source_ref_context=source_ref_context,
            baseline_ref=baseline_ref,
        )
        entries[semantic_key] = _baseline_semantic_object_index_entry(
            semantic_key=semantic_key,
            value={
                "object_id": str(class_instance.id),
                "object_kind": object_kind,
                "class_config_id": str(class_instance.class_config_id),
                "source_object_id": str(class_instance.source_object_id),
                "source_refs": source_refs,
                "semantic_fingerprint": attr_values.get("semantic_fingerprint"),
                "runtime_delta_fingerprint": attr_values.get(
                    "runtime_delta_fingerprint"
                )
                or attr_values.get("semantic_fingerprint"),
                "graph_semantic_key": attr_values.get("graph_semantic_key"),
                "node_key": attr_values.get("node_key"),
                "node_type": attr_values.get("node_type"),
                "class_fqn": attr_values.get("class_fqn"),
                "name": attr_values.get("name"),
                "description": attr_values.get("description"),
                "is_base": attr_values.get("is_base"),
                "is_edge": attr_values.get("is_edge"),
                "value_mode": attr_values.get("value_mode"),
                "identity_mode": attr_values.get("identity_mode"),
                "class_signature": _class_signature_payload(attr_values),
                "attribute_name": attr_values.get("attribute_name")
                or attr_values.get("name"),
                "owner_semantic_key": attr_values.get("owner_semantic_key"),
                "parent_semantic_key": attr_values.get("parent_semantic_key"),
                "function_name": attr_values.get("function_name"),
                "function_semantic_key": attr_values.get("function_semantic_key"),
                "function_impl_key": attr_values.get("function_impl_key"),
                "function_impl_kind": attr_values.get("kind"),
                "relationship_key": attr_values.get("relationship_key"),
            },
            baseline_ref=baseline_ref,
            source="object_instance_graph.class_instances",
        )
        entries.update(
            _typed_baseline_oig_attribute_entries_for_class_instance(
                class_instance=class_instance,
                owner_semantic_key=semantic_key,
                owner_kind=object_kind,
                owner_source_refs=source_refs,
                baseline_ref=baseline_ref,
            )
        )
    entries.update(
        _typed_baseline_oig_function_impl_entries(
            oig=oig,
            source_ref_context=source_ref_context,
            baseline_ref=baseline_ref,
        )
    )
    for relationship in oig.class_instance_relationships:
        semantic_key = _typed_baseline_oig_relationship_semantic_key(
            relationship=relationship,
            source_ref_context=source_ref_context,
        )
        if semantic_key is None:
            continue
        entries[semantic_key] = _baseline_semantic_object_index_entry(
            semantic_key=semantic_key,
            value={
                "object_id": str(relationship.id),
                "object_kind": "relationship",
                "class_config_relationship_id": str(
                    relationship.class_config_relationship_id
                ),
                "source_class_instance_id": str(
                    relationship.source_class_instance_id
                ),
                "target_class_instance_id": str(
                    relationship.target_class_instance_id
                ),
            },
            baseline_ref=baseline_ref,
            source="object_instance_graph.class_instance_relationships",
        )
    return dict(sorted(entries.items()))


def _normalize_baseline_semantic_object_index(
    *,
    value: object,
    baseline_ref: Mapping[str, object],
    source: str,
) -> dict[str, dict[str, object]]:
    if isinstance(value, Mapping):
        semantic_key = _optional_text(value.get("semantic_key"))
        if semantic_key is not None:
            return {
                semantic_key: _baseline_semantic_object_index_entry(
                    semantic_key=semantic_key,
                    value=value,
                    baseline_ref=baseline_ref,
                    source=source,
                )
            }
        entries: dict[str, dict[str, object]] = {}
        for raw_key, raw_value in value.items():
            entry_key = _optional_text(raw_key)
            if entry_key is None:
                continue
            entries[entry_key] = _baseline_semantic_object_index_entry(
                semantic_key=entry_key,
                value=raw_value,
                baseline_ref=baseline_ref,
                source=source,
            )
        return dict(sorted(entries.items()))
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        entries = {}
        for item in value:
            item_payload = _mapping_value(item)
            semantic_key = _optional_text(item_payload.get("semantic_key"))
            if semantic_key is None:
                continue
            entries[semantic_key] = _baseline_semantic_object_index_entry(
                semantic_key=semantic_key,
                value=item_payload,
                baseline_ref=baseline_ref,
                source=source,
            )
        return dict(sorted(entries.items()))
    return {}


def _baseline_semantic_object_index_entry(
    *,
    semantic_key: str,
    value: object,
    baseline_ref: Mapping[str, object],
    source: str,
) -> dict[str, object]:
    payload = _mapping_value(value)
    object_id = _optional_text(
        payload.get("object_id")
        or payload.get("semantic_object_id")
        or payload.get("class_instance_id")
        or payload.get("id")
    )
    if object_id is None:
        object_id = _optional_text(value)
    object_kind = _optional_text(
        payload.get("object_kind")
        or payload.get("semantic_object_kind")
        or payload.get("ontology_subject_kind")
        or payload.get("kind")
    )
    commit_id = _optional_text(
        payload.get("object_instance_graph_commit_id")
        or payload.get("semantic_object_instance_graph_commit_id")
        or baseline_ref.get("semantic_object_instance_graph_commit_id")
    )
    class_signature = _class_signature_payload(payload)
    return {
        "semantic_key": semantic_key,
        "object_id": object_id,
        "object_kind": object_kind,
        "object_instance_graph_commit_id": commit_id,
        "class_config_id": _optional_text(payload.get("class_config_id")),
        "source_object_id": _optional_text(payload.get("source_object_id")),
        "attribute_config_id": _optional_text(payload.get("attribute_config_id")),
        "attribute_name": _optional_text(payload.get("attribute_name")),
        "class_config_attribute_config_id": _optional_text(
            payload.get("class_config_attribute_config_id")
        ),
        "function_config_attribute_config_id": _optional_text(
            payload.get("function_config_attribute_config_id")
        ),
        "attribute_membership_semantic_key": _optional_text(
            payload.get("attribute_membership_semantic_key")
        ),
        "attribute_membership_owner_kind": _optional_text(
            payload.get("attribute_membership_owner_kind")
        ),
        "attribute_membership_signature": _mapping_value(
            payload.get("attribute_membership_signature")
        ),
        "function_attribute_type": _optional_text(
            payload.get("function_attribute_type")
        ),
        "parent_semantic_key": _optional_text(payload.get("parent_semantic_key")),
        "owner_semantic_key": _optional_text(payload.get("owner_semantic_key")),
        "owner_object_id": _optional_text(payload.get("owner_object_id")),
        "source_refs": _tuple_text(
            payload.get("source_refs")
            or payload.get("source_paths")
            or payload.get("source_path")
        ),
        "semantic_fingerprint": _optional_text(
            payload.get("semantic_fingerprint")
            or payload.get("runtime_delta_fingerprint")
        ),
        "runtime_delta_fingerprint": _optional_text(
            payload.get("runtime_delta_fingerprint")
            or payload.get("semantic_fingerprint")
        ),
        "graph_semantic_key": _optional_text(payload.get("graph_semantic_key")),
        "node_key": _optional_text(payload.get("node_key")),
        "node_type": _optional_text(payload.get("node_type")),
        "class_fqn": _optional_text(payload.get("class_fqn")),
        "name": _optional_text(payload.get("name") or payload.get("entity_name")),
        "description": _optional_text(payload.get("description")),
        "is_base": _class_signature_bool_value(
            payload.get("is_base"),
            fallback=class_signature.get("is_base"),
        ),
        "is_edge": _class_signature_bool_value(
            payload.get("is_edge"),
            fallback=class_signature.get("is_edge"),
        ),
        "value_mode": _optional_text(
            payload.get("value_mode") or class_signature.get("value_mode")
        ),
        "identity_mode": _optional_text(
            payload.get("identity_mode") or class_signature.get("identity_mode")
        ),
        "class_signature": class_signature,
        "attribute_signature": _mapping_value(payload.get("attribute_signature")),
        "function_name": _optional_text(payload.get("function_name")),
        "class_config_function_config_id": _optional_text(
            payload.get("class_config_function_config_id")
        ),
        "function_config_id": _optional_text(payload.get("function_config_id")),
        "function_membership_semantic_key": _optional_text(
            payload.get("function_membership_semantic_key")
        ),
        "function_membership_signature": _mapping_value(
            payload.get("function_membership_signature")
        ),
        "function_semantic_key": _optional_text(
            payload.get("function_semantic_key")
        ),
        "function_impl_key": _optional_text(payload.get("function_impl_key")),
        "function_impl_kind": _optional_text(payload.get("function_impl_kind")),
        "function_signature": _mapping_value(payload.get("function_signature")),
        "function_impl_signature": _mapping_value(
            payload.get("function_impl_signature")
        ),
        "relationship_key": _optional_text(payload.get("relationship_key")),
        "relationship_type": _optional_text(payload.get("relationship_type")),
        "relationship_signature": _mapping_value(
            payload.get("relationship_signature")
        ),
        "class_config_relationship_id": _optional_text(
            payload.get("class_config_relationship_id")
        ),
        "source_class_instance_id": _optional_text(
            payload.get("source_class_instance_id")
        ),
        "target_class_instance_id": _optional_text(
            payload.get("target_class_instance_id")
        ),
        "source": source,
        "payload": payload,
    }


def _typed_baseline_oig_source_ref_context(
    *,
    oig: ObjectInstanceGraph,
    baseline_ref: Mapping[str, object],
) -> _BaselineOigSourceRefContext:
    direct_source_refs_by_id: dict[str, tuple[str, ...]] = {}
    layout_source_refs_by_id: dict[str, tuple[str, ...]] = {}
    semantic_key_by_class_instance_id: dict[str, str] = {}
    class_instance_ids = {str(class_instance.id) for class_instance in oig.class_instances}
    for class_instance in oig.class_instances:
        class_instance_id = str(class_instance.id)
        direct_source_refs = _typed_baseline_oig_direct_source_refs(
            value=class_instance,
            baseline_ref=baseline_ref,
        )
        if direct_source_refs:
            direct_source_refs_by_id[class_instance_id] = direct_source_refs
        if (
            _typed_baseline_oig_object_kind(value=class_instance)
            == _BASELINE_OIG_LAYOUT_KIND
        ):
            layout_source_refs_by_id[class_instance_id] = direct_source_refs
        semantic_key = _typed_baseline_oig_object_semantic_key(value=class_instance)
        if semantic_key is not None:
            semantic_key_by_class_instance_id[class_instance_id] = semantic_key

    source_refs_by_id: dict[str, tuple[str, ...]] = dict(direct_source_refs_by_id)
    for relationship in oig.class_instance_relationships:
        source_id = str(relationship.source_class_instance_id)
        target_id = str(relationship.target_class_instance_id)
        source_layout_refs = layout_source_refs_by_id.get(source_id)
        target_layout_refs = layout_source_refs_by_id.get(target_id)
        if source_layout_refs and target_id in class_instance_ids:
            source_refs_by_id[target_id] = _merge_source_refs(
                source_refs_by_id.get(target_id, ()),
                source_layout_refs,
            )
        if target_layout_refs and source_id in class_instance_ids:
            source_refs_by_id[source_id] = _merge_source_refs(
                source_refs_by_id.get(source_id, ()),
                target_layout_refs,
            )

    source_refs_by_semantic_key: dict[str, tuple[str, ...]] = {}
    for class_instance_id, semantic_key in semantic_key_by_class_instance_id.items():
        source_refs = source_refs_by_id.get(class_instance_id, ())
        if not source_refs:
            continue
        source_refs_by_semantic_key[semantic_key] = _merge_source_refs(
            source_refs_by_semantic_key.get(semantic_key, ()),
            source_refs,
        )

    all_source_refs: tuple[str, ...] = ()
    for source_refs in source_refs_by_semantic_key.values():
        all_source_refs = _merge_source_refs(all_source_refs, source_refs)

    return _BaselineOigSourceRefContext(
        source_refs_by_class_instance_id=dict(sorted(source_refs_by_id.items())),
        source_refs_by_semantic_key=dict(sorted(source_refs_by_semantic_key.items())),
        semantic_key_by_class_instance_id=dict(
            sorted(semantic_key_by_class_instance_id.items())
        ),
        all_source_refs=all_source_refs,
    )


def _typed_baseline_oig_function_impl_entries(
    *,
    oig: ObjectInstanceGraph,
    source_ref_context: _BaselineOigSourceRefContext,
    baseline_ref: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    class_instance_by_id = {
        str(class_instance.id): class_instance for class_instance in oig.class_instances
    }
    function_semantic_key_by_instance_id = (
        _typed_baseline_oig_function_semantic_keys_by_instance_id(
            oig=oig,
            class_instance_by_id=class_instance_by_id,
            source_ref_context=source_ref_context,
        )
    )
    function_semantic_key_by_source_object_id = {
        str(class_instance.source_object_id): function_semantic_key
        for instance_id, function_semantic_key in (
            function_semantic_key_by_instance_id.items()
        )
        if (class_instance := class_instance_by_id.get(instance_id)) is not None
    }
    entries: dict[str, dict[str, object]] = {}
    for class_instance in oig.class_instances:
        if _typed_baseline_oig_object_kind(value=class_instance) != "function_impl":
            continue
        attr_values = _typed_class_instance_attribute_text_values(value=class_instance)
        function_semantic_key = _typed_baseline_oig_function_semantic_key_for_impl(
            function_impl=class_instance,
            attr_values=attr_values,
            oig=oig,
            function_semantic_key_by_instance_id=(
                function_semantic_key_by_instance_id
            ),
            function_semantic_key_by_source_object_id=(
                function_semantic_key_by_source_object_id
            ),
        )
        if function_semantic_key is None:
            continue
        function_impl_key = _baseline_oig_function_impl_key(
            attr_values=attr_values,
        )
        semantic_key = f"{function_semantic_key}/function_impl:{function_impl_key}"
        function_source_refs = source_ref_context.source_refs_by_semantic_key.get(
            function_semantic_key,
            (),
        )
        source_refs = _merge_source_refs(
            _typed_baseline_oig_direct_source_refs(
                value=class_instance,
                baseline_ref=baseline_ref,
            ),
            function_source_refs,
        )
        entries[semantic_key] = _baseline_semantic_object_index_entry(
            semantic_key=semantic_key,
            value={
                "object_id": str(class_instance.id),
                "object_kind": "function_impl",
                "class_config_id": str(class_instance.class_config_id),
                "source_object_id": str(class_instance.source_object_id),
                "parent_semantic_key": function_semantic_key,
                "owner_semantic_key": _baseline_oig_function_owner_semantic_key(
                    function_semantic_key=function_semantic_key,
                ),
                "function_semantic_key": function_semantic_key,
                "function_name": _baseline_oig_function_name_from_semantic_key(
                    function_semantic_key=function_semantic_key,
                ),
                "function_impl_key": function_impl_key,
                "function_impl_kind": (
                    attr_values.get("kind")
                    or _BASELINE_OIG_FUNCTION_IMPL_KIND_DEFAULT
                ),
                "function_impl_signature": (
                    _baseline_oig_function_impl_signature(
                        attr_values=attr_values,
                        function_semantic_key=function_semantic_key,
                        function_impl_key=function_impl_key,
                    )
                ),
                "source_refs": source_refs,
                "semantic_fingerprint": attr_values.get("semantic_fingerprint"),
                "runtime_delta_fingerprint": attr_values.get(
                    "runtime_delta_fingerprint"
                ),
            },
            baseline_ref=baseline_ref,
            source="object_instance_graph.function_impl",
        )
    return dict(sorted(entries.items()))


def _typed_baseline_oig_function_semantic_keys_by_instance_id(
    *,
    oig: ObjectInstanceGraph,
    class_instance_by_id: Mapping[str, ClassInstance],
    source_ref_context: _BaselineOigSourceRefContext,
) -> dict[str, str]:
    semantic_keys = {
        class_instance_id: semantic_key
        for class_instance_id, semantic_key in (
            source_ref_context.semantic_key_by_class_instance_id.items()
        )
        if (
            class_instance := class_instance_by_id.get(class_instance_id)
        ) is not None
        and _typed_baseline_oig_object_kind(value=class_instance) == "function"
    }
    changed = True
    while changed:
        changed = False
        for relationship in oig.class_instance_relationships:
            source_id = str(relationship.source_class_instance_id)
            target_id = str(relationship.target_class_instance_id)
            source_key = semantic_keys.get(source_id)
            target_key = semantic_keys.get(target_id)
            source_instance = class_instance_by_id.get(source_id)
            target_instance = class_instance_by_id.get(target_id)
            if source_instance is None or target_instance is None:
                continue
            source_kind = _typed_baseline_oig_object_kind(value=source_instance)
            target_kind = _typed_baseline_oig_object_kind(value=target_instance)
            relationship_key = _typed_relationship_key(relationship=relationship)
            if (
                source_key is not None
                and target_key is None
                and target_kind == "function"
                and _baseline_oig_function_config_relationship_candidate(
                    relationship_key=relationship_key,
                )
            ):
                semantic_keys[target_id] = source_key
                changed = True
            if (
                target_key is not None
                and source_key is None
                and source_kind == "function"
                and _baseline_oig_function_config_relationship_candidate(
                    relationship_key=relationship_key,
                )
            ):
                semantic_keys[source_id] = target_key
                changed = True
    return dict(sorted(semantic_keys.items()))


def _typed_baseline_oig_function_semantic_key_for_impl(
    *,
    function_impl: ClassInstance,
    attr_values: Mapping[str, str],
    oig: ObjectInstanceGraph,
    function_semantic_key_by_instance_id: Mapping[str, str],
    function_semantic_key_by_source_object_id: Mapping[str, str],
) -> str | None:
    direct = _baseline_oig_function_semantic_key(attr_values=attr_values)
    if direct is not None:
        return direct
    function_config_id = _optional_text(attr_values.get("function_config_id"))
    if function_config_id is not None:
        by_fk = function_semantic_key_by_source_object_id.get(function_config_id)
        if by_fk is not None:
            return by_fk
    impl_instance_id = str(function_impl.id)
    for relationship in oig.class_instance_relationships:
        source_id = str(relationship.source_class_instance_id)
        target_id = str(relationship.target_class_instance_id)
        if source_id == impl_instance_id:
            candidate = function_semantic_key_by_instance_id.get(target_id)
        elif target_id == impl_instance_id:
            candidate = function_semantic_key_by_instance_id.get(source_id)
        else:
            continue
        if candidate is None:
            continue
        relationship_key = _typed_relationship_key(relationship=relationship)
        if _baseline_oig_function_impl_relationship_candidate(
            relationship_key=relationship_key,
        ):
            return candidate
    return None


def _typed_baseline_oig_object_source_refs(
    *,
    class_instance: ClassInstance,
    semantic_key: str,
    object_kind: str | None,
    source_ref_context: _BaselineOigSourceRefContext,
    baseline_ref: Mapping[str, object],
) -> tuple[str, ...]:
    class_instance_id = str(class_instance.id)
    source_refs = source_ref_context.source_refs_by_class_instance_id.get(
        class_instance_id,
        (),
    )
    if source_refs:
        return source_refs
    source_refs = source_ref_context.source_refs_by_semantic_key.get(
        semantic_key,
        (),
    )
    if source_refs:
        return source_refs
    if object_kind == "object_config_graph":
        return source_ref_context.all_source_refs
    if object_kind == "object_config_graph_package":
        return _baseline_oig_manifest_source_refs(baseline_ref=baseline_ref)
    if object_kind == "attribute":
        attr_values = _typed_class_instance_attribute_text_values(value=class_instance)
        owner_semantic_key = _baseline_oig_attribute_owner_semantic_key(
            attr_values=attr_values,
        )
        if owner_semantic_key is not None:
            return source_ref_context.source_refs_by_semantic_key.get(
                owner_semantic_key,
                (),
            )
    return ()


def _typed_baseline_oig_direct_source_refs(
    *,
    value: ClassInstance,
    baseline_ref: Mapping[str, object],
) -> tuple[str, ...]:
    source_refs: tuple[str, ...] = ()
    attr_values = _typed_class_instance_attribute_text_values(value=value)
    for field_name in _BASELINE_OIG_SOURCE_REF_ATTRIBUTE_FIELDS:
        source_refs = _merge_source_refs(
            source_refs,
            _tuple_source_refs(attr_values.get(field_name)),
        )
    if _typed_baseline_oig_object_kind(value=value) == "object_config_graph_package":
        source_refs = _merge_source_refs(
            source_refs,
            _baseline_oig_manifest_source_refs(baseline_ref=baseline_ref),
        )
    return source_refs


def _typed_baseline_oig_attribute_entries_for_class_instance(
    *,
    class_instance: ClassInstance,
    owner_semantic_key: str,
    owner_kind: str | None,
    owner_source_refs: tuple[str, ...],
    baseline_ref: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    if owner_kind not in _BASELINE_OIG_NODE_KINDS:
        return {}
    entries: dict[str, dict[str, object]] = {}
    for attribute in _typed_class_instance_attributes(value=class_instance):
        attribute_config = attribute.attribute_config
        if attribute_config is None:
            continue
        attribute_name = _optional_text(attribute_config.name)
        if (
            attribute_name is None
            or attribute_name in _BASELINE_OIG_ATTRIBUTE_IDENTITY_FIELD_NAMES
        ):
            continue
        semantic_key = f"{owner_semantic_key}/attribute:{attribute_name}"
        entries[semantic_key] = _baseline_semantic_object_index_entry(
            semantic_key=semantic_key,
            value={
                "object_id": str(attribute.id),
                "object_kind": "attribute",
                "attribute_config_id": str(attribute_config.id),
                "attribute_name": attribute_name,
                "owner_semantic_key": owner_semantic_key,
                "owner_object_id": str(class_instance.id),
                "source_object_id": str(class_instance.source_object_id),
                "source_refs": owner_source_refs,
                "value_preview": _typed_attribute_primitive_text(value=attribute),
            },
            baseline_ref=baseline_ref,
            source="object_instance_graph.class_instance_attributes",
        )
    return dict(sorted(entries.items()))


def _typed_baseline_oig_object_semantic_key(
    *,
    value: ClassInstance,
) -> str | None:
    attr_values = _typed_class_instance_attribute_text_values(value=value)
    for attr_name in _BASELINE_OIG_DIRECT_SEMANTIC_KEY_FIELDS:
        attr_value = attr_values.get(attr_name)
        if attr_value is not None:
            return attr_value
    class_kind = _typed_baseline_oig_object_kind(value=value)
    if class_kind == "attribute":
        return _baseline_oig_attribute_semantic_key(attr_values=attr_values)
    if class_kind == "function_impl":
        function_semantic_key = _baseline_oig_function_semantic_key(
            attr_values=attr_values,
        )
        impl_key = _baseline_oig_function_impl_key(attr_values=attr_values)
        if function_semantic_key is not None:
            return f"{function_semantic_key}/function_impl:{impl_key}"
    graph_key = _baseline_oig_graph_semantic_key(attr_values=attr_values)
    node_key = _baseline_oig_node_key(
        attr_values=attr_values,
        class_kind=class_kind,
    )
    if graph_key is not None and node_key is not None:
        return f"{graph_key}/node:{node_key}"
    package_key = (
        attr_values.get("package_name")
        or attr_values.get("package_key")
        or attr_values.get("name")
    )
    if class_kind == "object_config_graph_package" and package_key is not None:
        return f"ocg_package:{package_key}"
    graph_fqn = (
        attr_values.get("fqn_prefix")
        or attr_values.get("object_config_graph_fqn_prefix")
        or attr_values.get("graph_fqn_prefix")
        or attr_values.get("key")
    )
    if class_kind == "object_config_graph" and graph_fqn is not None:
        return _baseline_oig_normalized_graph_semantic_key(value=graph_fqn)
    return None


def _typed_baseline_oig_object_kind(*, value: ClassInstance) -> str | None:
    class_config = value.class_config
    if class_config is None:
        return None
    raw_name = _optional_text(
        class_config.name or class_config.class_fqn
    )
    if raw_name is None:
        return None
    normalized = raw_name.rsplit(".", 1)[-1]
    if normalized == "ObjectConfigGraphNode":
        node_type = _baseline_oig_node_type(
            attr_values=_typed_class_instance_attribute_text_values(value=value)
        )
        if node_type in _BASELINE_OIG_NODE_KINDS:
            return node_type
    return {
        "ObjectConfigGraphPackage": "object_config_graph_package",
        "ObjectConfigGraph": "object_config_graph",
        "ObjectConfigGraphNode": "object_config_graph_node",
        "ClassConfig": "class",
        "EnumConfig": "enum",
        "ClassConfigRelationship": "relationship",
        "FunctionConfig": "function",
        "FunctionImpl": "function_impl",
        "AttributeConfig": "attribute",
        "ObjectConfigGraphNodeLayout": _BASELINE_OIG_LAYOUT_KIND,
    }.get(normalized, normalized)


def _typed_baseline_oig_relationship_semantic_key(
    *,
    relationship: ClassInstanceRelationship,
    source_ref_context: _BaselineOigSourceRefContext,
) -> str | None:
    relationship_config = relationship.class_config_relationship
    if relationship_config is None:
        return None
    relationship_key = _optional_text(relationship_config.relationship_key)
    if relationship_key is None:
        return None
    source_semantic_key = source_ref_context.semantic_key_by_class_instance_id.get(
        str(relationship.source_class_instance_id)
    )
    target_semantic_key = source_ref_context.semantic_key_by_class_instance_id.get(
        str(relationship.target_class_instance_id)
    )
    graph_semantic_key = _semantic_key_graph_prefix(
        source_semantic_key,
        target_semantic_key,
    )
    if graph_semantic_key is None:
        return None
    return f"{graph_semantic_key}/node:{relationship_key}"


def _semantic_key_graph_prefix(*values: str | None) -> str | None:
    for value in values:
        if value is None:
            continue
        if "/node:" in value:
            return value.split("/node:", 1)[0]
        if value.startswith("ocg:"):
            return value
    return None


def _typed_class_instance_attribute_text_values(
    *,
    value: ClassInstance,
) -> dict[str, str]:
    values: dict[str, str] = {}
    for attribute in _typed_class_instance_attributes(value=value):
        attribute_config = attribute.attribute_config
        if attribute_config is None:
            continue
        attribute_name = _optional_text(attribute_config.name)
        if attribute_name is None:
            continue
        attribute_value = _typed_attribute_primitive_text(value=attribute)
        if attribute_value is not None:
            values[attribute_name] = attribute_value
    return values


def _typed_class_instance_attributes(*, value: ClassInstance) -> tuple[Attribute, ...]:
    attributes: list[Attribute] = []
    attributes.extend(value.attributes)
    for edge in value.class_instance_attributes:
        attribute = edge.attribute
        if attribute is not None:
            attributes.append(attribute)
    deduped: list[Attribute] = []
    seen_keys: set[str] = set()
    for attribute in attributes:
        attribute_key = str(attribute.id)
        if attribute_key in seen_keys:
            continue
        seen_keys.add(attribute_key)
        deduped.append(attribute)
    return tuple(deduped)


def _typed_attribute_primitive_text(*, value: Attribute) -> str | None:
    primitive_value = value.value_root.primitive_value
    if isinstance(primitive_value, Mapping):
        for key in ("value", "text", "string_value"):
            candidate = primitive_value.get(key)
            if candidate is not None:
                return _optional_text(candidate)
        return None
    if isinstance(primitive_value, (list, tuple)):
        return None
    return _optional_text(primitive_value)


def _baseline_oig_source_ref_context(
    *,
    oig: object,
    baseline_ref: Mapping[str, object],
) -> _BaselineOigSourceRefContext:
    class_instances = tuple(getattr(oig, "class_instances", ()) or ())
    instance_ids = {
        _optional_text(getattr(class_instance, "id", None)): class_instance
        for class_instance in class_instances
        if _optional_text(getattr(class_instance, "id", None)) is not None
    }
    direct_source_refs_by_id: dict[str, tuple[str, ...]] = {}
    layout_source_refs_by_id: dict[str, tuple[str, ...]] = {}
    for instance_id, class_instance in instance_ids.items():
        if instance_id is None:
            continue
        direct_source_refs = _baseline_oig_direct_source_refs(
            value=class_instance,
            baseline_ref=baseline_ref,
        )
        if direct_source_refs:
            direct_source_refs_by_id[instance_id] = direct_source_refs
        if _baseline_oig_object_kind(value=class_instance) == _BASELINE_OIG_LAYOUT_KIND:
            layout_source_refs_by_id[instance_id] = direct_source_refs

    source_refs_by_id: dict[str, tuple[str, ...]] = dict(direct_source_refs_by_id)
    for relationship in tuple(
        getattr(oig, "class_instance_relationships", ()) or ()
    ):
        source_id = _optional_text(
            getattr(relationship, "source_class_instance_id", None)
        )
        target_id = _optional_text(
            getattr(relationship, "target_class_instance_id", None)
        )
        if source_id is None or target_id is None:
            continue
        source_layout_refs = layout_source_refs_by_id.get(source_id)
        target_layout_refs = layout_source_refs_by_id.get(target_id)
        if source_layout_refs and target_id in instance_ids:
            source_refs_by_id[target_id] = _merge_source_refs(
                source_refs_by_id.get(target_id, ()),
                source_layout_refs,
            )
        if target_layout_refs and source_id in instance_ids:
            source_refs_by_id[source_id] = _merge_source_refs(
                source_refs_by_id.get(source_id, ()),
                target_layout_refs,
            )

    source_refs_by_semantic_key: dict[str, tuple[str, ...]] = {}
    semantic_key_by_class_instance_id: dict[str, str] = {}
    for instance_id, class_instance in instance_ids.items():
        if instance_id is None:
            continue
        semantic_key = _baseline_oig_object_semantic_key(value=class_instance)
        if semantic_key is None:
            continue
        semantic_key_by_class_instance_id[instance_id] = semantic_key
        source_refs = source_refs_by_id.get(instance_id, ())
        if not source_refs:
            continue
        source_refs_by_semantic_key[semantic_key] = _merge_source_refs(
            source_refs_by_semantic_key.get(semantic_key, ()),
            source_refs,
        )

    all_source_refs: tuple[str, ...] = ()
    for source_refs in source_refs_by_semantic_key.values():
        all_source_refs = _merge_source_refs(all_source_refs, source_refs)

    return _BaselineOigSourceRefContext(
        source_refs_by_class_instance_id=dict(sorted(source_refs_by_id.items())),
        source_refs_by_semantic_key=dict(sorted(source_refs_by_semantic_key.items())),
        semantic_key_by_class_instance_id=dict(
            sorted(semantic_key_by_class_instance_id.items())
        ),
        all_source_refs=all_source_refs,
    )


def _baseline_oig_function_impl_entries(
    *,
    oig: object,
    source_ref_context: _BaselineOigSourceRefContext,
    baseline_ref: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    class_instances = tuple(getattr(oig, "class_instances", ()) or ())
    class_instance_by_id = {
        instance_id: class_instance
        for class_instance in class_instances
        if (instance_id := _optional_text(getattr(class_instance, "id", None)))
        is not None
    }
    function_semantic_key_by_instance_id = (
        _baseline_oig_function_semantic_keys_by_instance_id(
            oig=oig,
            class_instance_by_id=class_instance_by_id,
            source_ref_context=source_ref_context,
        )
    )
    function_semantic_key_by_source_object_id = {
        str(source_object_id): function_semantic_key
        for instance_id, function_semantic_key in (
            function_semantic_key_by_instance_id.items()
        )
        if (class_instance := class_instance_by_id.get(instance_id)) is not None
        and (
            source_object_id := _optional_text(
                getattr(class_instance, "source_object_id", None)
            )
        )
        is not None
    }
    entries: dict[str, dict[str, object]] = {}
    for class_instance in class_instances:
        if _baseline_oig_object_kind(value=class_instance) != "function_impl":
            continue
        attr_values = _class_instance_attribute_text_values(value=class_instance)
        function_semantic_key = _baseline_oig_function_semantic_key_for_impl(
            function_impl=class_instance,
            attr_values=attr_values,
            oig=oig,
            function_semantic_key_by_instance_id=(
                function_semantic_key_by_instance_id
            ),
            function_semantic_key_by_source_object_id=(
                function_semantic_key_by_source_object_id
            ),
        )
        if function_semantic_key is None:
            continue
        function_impl_key = _baseline_oig_function_impl_key(
            attr_values=attr_values,
        )
        semantic_key = f"{function_semantic_key}/function_impl:{function_impl_key}"
        source_refs = _merge_source_refs(
            _baseline_oig_direct_source_refs(
                value=class_instance,
                baseline_ref=baseline_ref,
            ),
            source_ref_context.source_refs_by_semantic_key.get(
                function_semantic_key,
                (),
            ),
        )
        entries[semantic_key] = _baseline_semantic_object_index_entry(
            semantic_key=semantic_key,
            value={
                "object_id": _optional_text(getattr(class_instance, "id", None)),
                "object_kind": "function_impl",
                "class_config_id": _optional_text(
                    getattr(class_instance, "class_config_id", None)
                ),
                "source_object_id": _optional_text(
                    getattr(class_instance, "source_object_id", None)
                ),
                "parent_semantic_key": function_semantic_key,
                "owner_semantic_key": _baseline_oig_function_owner_semantic_key(
                    function_semantic_key=function_semantic_key,
                ),
                "function_semantic_key": function_semantic_key,
                "function_name": _baseline_oig_function_name_from_semantic_key(
                    function_semantic_key=function_semantic_key,
                ),
                "function_impl_key": function_impl_key,
                "function_impl_kind": (
                    attr_values.get("kind")
                    or _BASELINE_OIG_FUNCTION_IMPL_KIND_DEFAULT
                ),
                "function_impl_signature": (
                    _baseline_oig_function_impl_signature(
                        attr_values=attr_values,
                        function_semantic_key=function_semantic_key,
                        function_impl_key=function_impl_key,
                    )
                ),
                "source_refs": source_refs,
                "semantic_fingerprint": attr_values.get("semantic_fingerprint"),
                "runtime_delta_fingerprint": attr_values.get(
                    "runtime_delta_fingerprint"
                ),
            },
            baseline_ref=baseline_ref,
            source="object_instance_graph.function_impl",
        )
    return dict(sorted(entries.items()))


def _baseline_oig_function_semantic_keys_by_instance_id(
    *,
    oig: object,
    class_instance_by_id: Mapping[str, object],
    source_ref_context: _BaselineOigSourceRefContext,
) -> dict[str, str]:
    semantic_keys = {
        class_instance_id: semantic_key
        for class_instance_id, semantic_key in (
            source_ref_context.semantic_key_by_class_instance_id.items()
        )
        if (
            class_instance := class_instance_by_id.get(class_instance_id)
        ) is not None
        and _baseline_oig_object_kind(value=class_instance) == "function"
    }
    changed = True
    while changed:
        changed = False
        for relationship in tuple(
            getattr(oig, "class_instance_relationships", ()) or ()
        ):
            source_id = _optional_text(
                getattr(relationship, "source_class_instance_id", None)
            )
            target_id = _optional_text(
                getattr(relationship, "target_class_instance_id", None)
            )
            if source_id is None or target_id is None:
                continue
            source_key = semantic_keys.get(source_id)
            target_key = semantic_keys.get(target_id)
            source_instance = class_instance_by_id.get(source_id)
            target_instance = class_instance_by_id.get(target_id)
            if source_instance is None or target_instance is None:
                continue
            source_kind = _baseline_oig_object_kind(value=source_instance)
            target_kind = _baseline_oig_object_kind(value=target_instance)
            relationship_key = _relationship_key(relationship=relationship)
            if (
                source_key is not None
                and target_key is None
                and target_kind == "function"
                and _baseline_oig_function_config_relationship_candidate(
                    relationship_key=relationship_key,
                )
            ):
                semantic_keys[target_id] = source_key
                changed = True
            if (
                target_key is not None
                and source_key is None
                and source_kind == "function"
                and _baseline_oig_function_config_relationship_candidate(
                    relationship_key=relationship_key,
                )
            ):
                semantic_keys[source_id] = target_key
                changed = True
    return dict(sorted(semantic_keys.items()))


def _baseline_oig_function_semantic_key_for_impl(
    *,
    function_impl: object,
    attr_values: Mapping[str, str],
    oig: object,
    function_semantic_key_by_instance_id: Mapping[str, str],
    function_semantic_key_by_source_object_id: Mapping[str, str],
) -> str | None:
    direct = _baseline_oig_function_semantic_key(attr_values=attr_values)
    if direct is not None:
        return direct
    function_config_id = _optional_text(attr_values.get("function_config_id"))
    if function_config_id is not None:
        by_fk = function_semantic_key_by_source_object_id.get(function_config_id)
        if by_fk is not None:
            return by_fk
    impl_instance_id = _optional_text(getattr(function_impl, "id", None))
    if impl_instance_id is None:
        return None
    for relationship in tuple(getattr(oig, "class_instance_relationships", ()) or ()):
        source_id = _optional_text(
            getattr(relationship, "source_class_instance_id", None)
        )
        target_id = _optional_text(
            getattr(relationship, "target_class_instance_id", None)
        )
        if source_id == impl_instance_id and target_id is not None:
            candidate = function_semantic_key_by_instance_id.get(target_id)
        elif target_id == impl_instance_id and source_id is not None:
            candidate = function_semantic_key_by_instance_id.get(source_id)
        else:
            continue
        if candidate is None:
            continue
        relationship_key = _relationship_key(relationship=relationship)
        if _baseline_oig_function_impl_relationship_candidate(
            relationship_key=relationship_key,
        ):
            return candidate
    return None


def _baseline_oig_object_source_refs(
    *,
    class_instance: object,
    semantic_key: str,
    object_kind: str | None,
    source_ref_context: _BaselineOigSourceRefContext,
    baseline_ref: Mapping[str, object],
) -> tuple[str, ...]:
    class_instance_id = _optional_text(getattr(class_instance, "id", None))
    if class_instance_id is not None:
        source_refs = source_ref_context.source_refs_by_class_instance_id.get(
            class_instance_id,
            (),
        )
        if source_refs:
            return source_refs
    source_refs = source_ref_context.source_refs_by_semantic_key.get(
        semantic_key,
        (),
    )
    if source_refs:
        return source_refs
    if object_kind == "object_config_graph":
        return source_ref_context.all_source_refs
    if object_kind == "object_config_graph_package":
        return _baseline_oig_manifest_source_refs(baseline_ref=baseline_ref)
    if object_kind == "attribute":
        attr_values = _class_instance_attribute_text_values(value=class_instance)
        owner_semantic_key = _baseline_oig_attribute_owner_semantic_key(
            attr_values=attr_values,
        )
        if owner_semantic_key is not None:
            return source_ref_context.source_refs_by_semantic_key.get(
                owner_semantic_key,
                (),
            )
    return ()


def _baseline_oig_direct_source_refs(
    *,
    value: object,
    baseline_ref: Mapping[str, object],
) -> tuple[str, ...]:
    payload = _mapping_value(value)
    source_refs: tuple[str, ...] = ()
    for field_name in _BASELINE_OIG_SOURCE_REF_ATTRIBUTE_FIELDS:
        source_refs = _merge_source_refs(
            source_refs,
            _tuple_source_refs(payload.get(field_name)),
        )
    attr_values = _class_instance_attribute_text_values(value=value)
    for field_name in _BASELINE_OIG_SOURCE_REF_ATTRIBUTE_FIELDS:
        source_refs = _merge_source_refs(
            source_refs,
            _tuple_source_refs(attr_values.get(field_name)),
        )
    if _baseline_oig_object_kind(value=value) == "object_config_graph_package":
        source_refs = _merge_source_refs(
            source_refs,
            _baseline_oig_manifest_source_refs(baseline_ref=baseline_ref),
        )
    return source_refs


def _baseline_oig_manifest_source_refs(
    *,
    baseline_ref: Mapping[str, object],
) -> tuple[str, ...]:
    raw_path = _optional_text(
        baseline_ref.get("manifest_toml_path")
        or baseline_ref.get("manifest_path")
        or baseline_ref.get("aware_toml_path")
    )
    if raw_path is None:
        return ("aware.toml",)
    normalized = raw_path.replace("\\", "/").strip().strip("/")
    if normalized.endswith("/aware.toml") or normalized == "aware.toml":
        return ("aware.toml",)
    return _tuple_source_refs(normalized)


def _baseline_oig_function_semantic_key(
    *,
    attr_values: Mapping[str, str],
) -> str | None:
    for field_name in (
        "function_semantic_key",
        "parent_semantic_key",
        "owner_function_semantic_key",
    ):
        value = _optional_text(attr_values.get(field_name))
        if value is not None:
            return value
    return None


def _baseline_oig_function_impl_key(
    *,
    attr_values: Mapping[str, str],
) -> str:
    return (
        _optional_text(attr_values.get("function_impl_key"))
        or _optional_text(attr_values.get("key"))
        or _BASELINE_OIG_FUNCTION_IMPL_KEY_DEFAULT
    )


def _baseline_oig_function_impl_signature(
    *,
    attr_values: Mapping[str, str],
    function_semantic_key: str,
    function_impl_key: str,
) -> dict[str, object]:
    instruction_summaries = _tuple_text(attr_values.get("instruction_summaries"))
    instruction_count = _int_object_value(attr_values.get("instruction_count"))
    if instruction_count == 0 and instruction_summaries:
        instruction_count = len(instruction_summaries)
    return {
        "key": function_impl_key,
        "kind": (
            _optional_text(attr_values.get("kind"))
            or _BASELINE_OIG_FUNCTION_IMPL_KIND_DEFAULT
        ),
        "function_name": _baseline_oig_function_name_from_semantic_key(
            function_semantic_key=function_semantic_key,
        ),
        "function_owner_key": _baseline_oig_function_owner_key_from_semantic_key(
            function_semantic_key=function_semantic_key,
        ),
        "instruction_count": instruction_count,
        "instruction_summaries": instruction_summaries,
        "instructions": (),
    }


def _baseline_oig_function_name_from_semantic_key(
    *,
    function_semantic_key: str,
) -> str | None:
    node_key = _baseline_oig_function_node_key_from_semantic_key(
        function_semantic_key=function_semantic_key,
    )
    if node_key is None or "." not in node_key:
        return None
    return node_key.rsplit(".", 1)[1] or None


def _baseline_oig_function_owner_key_from_semantic_key(
    *,
    function_semantic_key: str,
) -> str | None:
    node_key = _baseline_oig_function_node_key_from_semantic_key(
        function_semantic_key=function_semantic_key,
    )
    if node_key is None or "." not in node_key:
        return None
    return node_key.rsplit(".", 1)[0] or None


def _baseline_oig_function_owner_semantic_key(
    *,
    function_semantic_key: str,
) -> str | None:
    owner_key = _baseline_oig_function_owner_key_from_semantic_key(
        function_semantic_key=function_semantic_key,
    )
    if owner_key is None:
        return None
    graph_semantic_key = _semantic_key_graph_prefix(function_semantic_key)
    if graph_semantic_key is None:
        return None
    return f"{graph_semantic_key}/node:{owner_key}"


def _baseline_oig_function_node_key_from_semantic_key(
    *,
    function_semantic_key: str,
) -> str | None:
    marker = "/node:"
    if marker not in function_semantic_key:
        return None
    return function_semantic_key.split(marker, 1)[1].split("/", 1)[0] or None


def _baseline_oig_function_config_relationship_candidate(
    *,
    relationship_key: str | None,
) -> bool:
    if relationship_key is None:
        return True
    normalized = relationship_key.rsplit("::", 1)[-1].rsplit(".", 1)[-1]
    return normalized in _BASELINE_OIG_FUNCTION_CONFIG_RELATIONSHIP_KEYS


def _baseline_oig_function_impl_relationship_candidate(
    *,
    relationship_key: str | None,
) -> bool:
    if relationship_key is None:
        return True
    normalized = relationship_key.rsplit("::", 1)[-1].rsplit(".", 1)[-1]
    return normalized in _BASELINE_OIG_FUNCTION_IMPL_RELATIONSHIP_KEYS


def _typed_relationship_key(
    *,
    relationship: ClassInstanceRelationship,
) -> str | None:
    relationship_config = relationship.class_config_relationship
    if relationship_config is None:
        return None
    return _optional_text(relationship_config.relationship_key)


def _relationship_key(*, relationship: object) -> str | None:
    relationship_config = getattr(relationship, "class_config_relationship", None)
    return _optional_text(getattr(relationship_config, "relationship_key", None))


def _tuple_source_refs(value: object) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            source_ref
            for item in _tuple_text(value)
            if (source_ref := _normalize_source_ref(value=item)) is not None
        )
    )


def _normalize_source_ref(*, value: str) -> str | None:
    text = value.replace("\\", "/").strip().strip("/")
    if not text:
        return None
    if text.startswith("./"):
        text = text[2:]
    if text.startswith("aware/") and text.endswith(".aware"):
        text = text.removeprefix("aware/")
    return text or None


def _merge_source_refs(
    left: tuple[str, ...],
    right: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys((*left, *right))))


def _baseline_oig_attribute_entries_for_class_instance(
    *,
    class_instance: object,
    owner_semantic_key: str,
    owner_kind: str | None,
    owner_source_refs: tuple[str, ...],
    baseline_ref: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    if owner_kind not in _BASELINE_OIG_NODE_KINDS:
        return {}
    entries: dict[str, dict[str, object]] = {}
    for attribute in _class_instance_attributes(value=class_instance):
        attribute_config = getattr(attribute, "attribute_config", None)
        attribute_name = _optional_text(getattr(attribute_config, "name", None))
        if (
            attribute_name is None
            or attribute_name in _BASELINE_OIG_ATTRIBUTE_IDENTITY_FIELD_NAMES
        ):
            continue
        semantic_key = f"{owner_semantic_key}/attribute:{attribute_name}"
        entries[semantic_key] = _baseline_semantic_object_index_entry(
            semantic_key=semantic_key,
            value={
                "object_id": _optional_text(getattr(attribute, "id", None)),
                "object_kind": "attribute",
                "attribute_config_id": _optional_text(
                    getattr(attribute_config, "id", None)
                )
                or _optional_text(getattr(attribute, "attribute_config_id", None)),
                "attribute_name": attribute_name,
                "owner_semantic_key": owner_semantic_key,
                "owner_object_id": _optional_text(
                    getattr(class_instance, "id", None)
                ),
                "source_object_id": _optional_text(
                    getattr(class_instance, "source_object_id", None)
                ),
                "source_refs": owner_source_refs,
                "value_preview": _attribute_primitive_text(value=attribute),
            },
            baseline_ref=baseline_ref,
            source="object_instance_graph.class_instance_attributes",
        )
    return dict(sorted(entries.items()))


def _baseline_oig_object_semantic_key(*, value: object) -> str | None:
    for attr_name in _BASELINE_OIG_DIRECT_SEMANTIC_KEY_FIELDS:
        direct_value = _optional_text(getattr(value, attr_name, None))
        if direct_value is not None:
            return direct_value
    attr_values = _class_instance_attribute_text_values(value=value)
    for attr_name in _BASELINE_OIG_DIRECT_SEMANTIC_KEY_FIELDS:
        attr_value = attr_values.get(attr_name)
        if attr_value is not None:
            return attr_value
    class_kind = _baseline_oig_object_kind(value=value)
    if class_kind == "attribute":
        return _baseline_oig_attribute_semantic_key(attr_values=attr_values)
    if class_kind == "function_impl":
        function_semantic_key = _baseline_oig_function_semantic_key(
            attr_values=attr_values,
        )
        impl_key = _baseline_oig_function_impl_key(attr_values=attr_values)
        if function_semantic_key is not None:
            return f"{function_semantic_key}/function_impl:{impl_key}"
    graph_key = _baseline_oig_graph_semantic_key(attr_values=attr_values)
    node_key = _baseline_oig_node_key(
        attr_values=attr_values,
        class_kind=class_kind,
    )
    if graph_key is not None and node_key is not None:
        return f"{graph_key}/node:{node_key}"
    package_key = (
        attr_values.get("package_name")
        or attr_values.get("package_key")
        or attr_values.get("name")
    )
    if class_kind == "object_config_graph_package" and package_key is not None:
        return f"ocg_package:{package_key}"
    graph_fqn = (
        attr_values.get("fqn_prefix")
        or attr_values.get("object_config_graph_fqn_prefix")
        or attr_values.get("graph_fqn_prefix")
        or attr_values.get("key")
    )
    if class_kind == "object_config_graph" and graph_fqn is not None:
        return _baseline_oig_normalized_graph_semantic_key(value=graph_fqn)
    return None


def _baseline_oig_object_kind(*, value: object) -> str | None:
    class_config = getattr(value, "class_config", None)
    raw_name = _optional_text(
        getattr(class_config, "name", None)
        or getattr(class_config, "key", None)
        or getattr(class_config, "fqn", None)
    )
    if raw_name is None:
        return None
    normalized = raw_name.rsplit(".", 1)[-1]
    if normalized == "ObjectConfigGraphNode":
        node_type = _baseline_oig_node_type(
            attr_values=_class_instance_attribute_text_values(value=value)
        )
        if node_type in _BASELINE_OIG_NODE_KINDS:
            return node_type
    return {
        "ObjectConfigGraphPackage": "object_config_graph_package",
        "ObjectConfigGraph": "object_config_graph",
        "ObjectConfigGraphNode": "object_config_graph_node",
        "ClassConfig": "class",
        "EnumConfig": "enum",
        "ClassConfigRelationship": "relationship",
        "FunctionConfig": "function",
        "FunctionImpl": "function_impl",
        "AttributeConfig": "attribute",
        "ObjectConfigGraphNodeLayout": _BASELINE_OIG_LAYOUT_KIND,
    }.get(normalized, normalized)


def _class_instance_attribute_text_values(*, value: object) -> dict[str, str]:
    values: dict[str, str] = {}
    for attribute in _class_instance_attributes(value=value):
        attribute_config = getattr(attribute, "attribute_config", None)
        attribute_name = _optional_text(getattr(attribute_config, "name", None))
        if attribute_name is None:
            continue
        attribute_value = _attribute_primitive_text(value=attribute)
        if attribute_value is not None:
            values[attribute_name] = attribute_value
    return values


def _class_instance_attributes(*, value: object) -> tuple[object, ...]:
    attributes: list[object] = []
    attributes.extend(tuple(getattr(value, "attributes", ()) or ()))
    for edge in tuple(getattr(value, "class_instance_attributes", ()) or ()):
        attribute = getattr(edge, "attribute", None)
        if attribute is not None:
            attributes.append(attribute)
    deduped: list[object] = []
    seen_keys: set[str] = set()
    for attribute in attributes:
        attribute_key = _optional_text(getattr(attribute, "id", None))
        if attribute_key is not None:
            if attribute_key in seen_keys:
                continue
            seen_keys.add(attribute_key)
        deduped.append(attribute)
    return tuple(deduped)


def _attribute_primitive_text(*, value: object) -> str | None:
    value_root = getattr(value, "value_root", None)
    primitive_value = None
    for attr_name in ("primitive_value", "value", "text", "string_value"):
        primitive_value = getattr(value_root, attr_name, None)
        if primitive_value is not None:
            break
    if isinstance(primitive_value, Mapping):
        for key in ("value", "text", "string_value"):
            candidate = primitive_value.get(key)
            if candidate is not None:
                return _optional_text(candidate)
        return None
    if isinstance(primitive_value, (list, tuple)):
        return None
    return _optional_text(primitive_value)


def _baseline_oig_graph_semantic_key(
    *,
    attr_values: Mapping[str, str],
) -> str | None:
    for attr_name in _BASELINE_OIG_GRAPH_SEMANTIC_KEY_FIELDS:
        graph_key = attr_values.get(attr_name)
        if graph_key is not None:
            return _baseline_oig_normalized_graph_semantic_key(value=graph_key)
    graph_fqn = (
        attr_values.get("fqn_prefix")
        or attr_values.get("object_config_graph_fqn_prefix")
        or attr_values.get("graph_fqn_prefix")
        or attr_values.get("graph_key")
    )
    if graph_fqn is None:
        return None
    return _baseline_oig_normalized_graph_semantic_key(value=graph_fqn)


def _baseline_oig_normalized_graph_semantic_key(*, value: str) -> str:
    return value if value.startswith("ocg:") else f"ocg:{value}"


def _baseline_oig_node_key(
    *,
    attr_values: Mapping[str, str],
    class_kind: str | None,
) -> str | None:
    node_key = (
        attr_values.get("node_key")
        or attr_values.get("object_config_graph_node_key")
    )
    if node_key is not None:
        return node_key
    if class_kind == "class":
        return attr_values.get("class_fqn") or attr_values.get("fqn")
    if class_kind == "enum":
        return attr_values.get("enum_fqn") or attr_values.get("fqn")
    if class_kind == "function":
        return (
            attr_values.get("function_fqn")
            or attr_values.get("qualified_name")
            or _baseline_oig_function_node_key(attr_values=attr_values)
        )
    if class_kind == "relationship":
        return _baseline_oig_relationship_node_key(attr_values=attr_values)
    return None


def _baseline_oig_function_node_key(
    *,
    attr_values: Mapping[str, str],
) -> str | None:
    owner_key = attr_values.get("owner_key") or attr_values.get("parent_node_key")
    name = attr_values.get("name") or attr_values.get("function_name")
    if owner_key is None or name is None:
        return None
    return f"{owner_key}.{name}"


def _baseline_oig_relationship_node_key(
    *,
    attr_values: Mapping[str, str],
) -> str | None:
    explicit_key = (
        attr_values.get("relationship_node_key")
        or attr_values.get("relationship_semantic_key")
        or attr_values.get("relationship_key")
    )
    if explicit_key is not None and ":" in explicit_key:
        return explicit_key
    source_key = (
        attr_values.get("source_node_key")
        or attr_values.get("source_class_key")
        or attr_values.get("source_class_fqn")
    )
    relationship_name = (
        attr_values.get("relationship_name")
        or attr_values.get("relationship_key")
        or attr_values.get("name")
    )
    target_key = (
        attr_values.get("target_node_key")
        or attr_values.get("target_class_key")
        or attr_values.get("target_class_fqn")
    )
    if source_key is None or relationship_name is None or target_key is None:
        return None
    cardinality = (
        attr_values.get("cardinality")
        or attr_values.get("relationship_type")
        or attr_values.get("collection_kind")
        or "unknown"
    )
    return f"{source_key}:{relationship_name}:{cardinality}:{target_key}"


def _baseline_oig_node_type(*, attr_values: Mapping[str, str]) -> str | None:
    value = attr_values.get("node_type") or attr_values.get("type")
    if value is None:
        return None
    normalized = value.rsplit(".", 1)[-1].lower()
    return {
        "class": "class",
        "enum": "enum",
        "relationship": "relationship",
        "function": "function",
    }.get(normalized)


def _baseline_oig_attribute_semantic_key(
    *,
    attr_values: Mapping[str, str],
) -> str | None:
    attribute_name = (
        attr_values.get("attribute_name")
        or attr_values.get("name")
        or attr_values.get("key")
    )
    owner_semantic_key = _baseline_oig_attribute_owner_semantic_key(
        attr_values=attr_values,
    )
    if attribute_name is None or owner_semantic_key is None:
        return None
    return f"{owner_semantic_key}/attribute:{attribute_name}"


def _baseline_oig_attribute_owner_semantic_key(
    *,
    attr_values: Mapping[str, str],
) -> str | None:
    for attr_name in _BASELINE_OIG_ATTRIBUTE_OWNER_SEMANTIC_KEY_FIELDS:
        owner_semantic_key = attr_values.get(attr_name)
        if owner_semantic_key is not None:
            return owner_semantic_key
    owner_key = (
        attr_values.get("owner_key")
        or attr_values.get("owner_node_key")
        or attr_values.get("parent_node_key")
    )
    if owner_key is None:
        return None
    if owner_key.startswith("ocg:"):
        return owner_key
    if not _baseline_oig_text_can_be_node_key(value=owner_key):
        return None
    graph_key = _baseline_oig_graph_semantic_key(attr_values=attr_values)
    if graph_key is None:
        return None
    return f"{graph_key}/node:{owner_key}"


def _baseline_oig_text_can_be_node_key(*, value: str) -> bool:
    if _uuid_value(value) is not None:
        return False
    return "." in value or "/" in value


def _object_counts_from_oig(oig: object) -> dict[str, int]:
    return {
        "class_instances": _sequence_count(getattr(oig, "class_instances", ())),
        "class_instance_relationships": _sequence_count(
            getattr(oig, "class_instance_relationships", ())
        ),
    }


def _object_counts_from_payload(
    *,
    payload: Mapping[str, object],
) -> dict[str, int] | None:
    raw_counts = payload.get("object_counts")
    if isinstance(raw_counts, Mapping):
        return {
            "class_instances": _int_payload_value(
                raw_counts,
                "class_instances",
            ),
            "class_instance_relationships": _int_payload_value(
                raw_counts,
                "class_instance_relationships",
            ),
        }
    if "class_instance_count" not in payload:
        return None
    return {
        "class_instances": _int_payload_value(payload, "class_instance_count"),
        "class_instance_relationships": _int_payload_value(
            payload,
            "class_instance_relationship_count",
        ),
    }


def _int_payload_value(payload: Mapping[str, object], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except Exception:
        return 0


def _int_object_value(value: object) -> int:
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except Exception:
        return 0


def _sequence_count(value: object) -> int:
    if isinstance(value, Sequence) and not isinstance(value, str):
        return len(value)
    if isinstance(value, Sized):
        return len(value)
    return 0


def _semantic_projection_hash_from_payload(
    *,
    payload: Mapping[str, object],
) -> str | None:
    return _optional_text(
        payload.get("semantic_projection_hash") or payload.get("projection_hash")
    )


def _baseline_commit_refs(*, request: object) -> dict[str, str | None]:
    return {
        field_name: _optional_text(getattr(request, field_name, None))
        for field_name in _BASELINE_COMMIT_REF_FIELDS
    }


def _baseline_ref_payload(*, request: object) -> dict[str, object] | None:
    baseline_ref = getattr(request, "baseline_ref", None)
    if baseline_ref is None:
        return None
    payload = _model_payload(baseline_ref)
    return payload if payload else None


def _baseline_ref_missing_required_fields(
    *,
    baseline_ref: Mapping[str, object] | None,
) -> tuple[str, ...]:
    if baseline_ref is None:
        return _BASELINE_REF_HYDRATOR_REQUIRED_FIELDS
    return tuple(
        field_name
        for field_name in _BASELINE_REF_HYDRATOR_REQUIRED_FIELDS
        if not _optional_text(baseline_ref.get(field_name))
    )


def _baseline_dirty_diff_status(
    *,
    commit_backed_baseline_available: bool,
    baseline_ref_hydrator_ready: bool,
    hydration_preflight: Mapping[str, object],
) -> str:
    if not commit_backed_baseline_available:
        return "baseline_context_missing"
    if not baseline_ref_hydrator_ready:
        return str(hydration_preflight.get("status") or "baseline_ref_incomplete")
    if hydration_preflight.get("status") == "baseline_hydrated":
        return "baseline_hydrated_dirty_diff_not_wired"
    return str(hydration_preflight.get("status") or "baseline_hydration_unavailable")


def _baseline_dirty_diff_unavailable_reason(
    *,
    commit_backed_baseline_available: bool,
    baseline_ref_hydrator_ready: bool,
    hydration_preflight: Mapping[str, object],
) -> str:
    if not commit_backed_baseline_available:
        return "meta_ocg_dirty_diff_requires_commit_backed_baseline"
    if not baseline_ref_hydrator_ready:
        return "meta_ocg_dirty_diff_requires_workspace_baseline_ref"
    hydration_status = str(hydration_preflight.get("status") or "")
    if hydration_status == "baseline_hydrated":
        return "meta_ocg_dirty_diff_compare_not_wired"
    if hydration_status == "baseline_projection_unresolved":
        return "meta_ocg_dirty_diff_requires_resolvable_baseline_projection"
    if hydration_status == "baseline_hydrator_unavailable":
        return "meta_ocg_dirty_diff_requires_baseline_hydrator_context"
    if hydration_status == "baseline_hydration_failed":
        return "meta_ocg_dirty_diff_baseline_hydration_failed"
    if hydration_status == "baseline_ref_invalid":
        return "meta_ocg_dirty_diff_requires_valid_workspace_baseline_ref"
    if hydration_status == "baseline_runtime_index_missing":
        return "meta_ocg_dirty_diff_requires_baseline_hydrator_runtime_index"
    if hydration_status == "baseline_oig_payload_ref_missing":
        return "meta_ocg_dirty_diff_requires_workspace_oig_payload_ref_or_local_commit"
    if hydration_status == "baseline_oig_payload_import_failed":
        return "meta_ocg_dirty_diff_baseline_oig_payload_import_failed"
    if hydration_status == "baseline_oig_commit_missing":
        return "meta_ocg_dirty_diff_requires_local_baseline_oig_commit"
    if hydration_status == "baseline_oig_lane_head_missing":
        return "meta_ocg_dirty_diff_requires_local_baseline_oig_lane_head"
    return "meta_ocg_dirty_diff_requires_baseline_hydration"


def _provider_delta_durable_execution_inputs_payload(
    *,
    request: object,
) -> dict[str, object]:
    value = _request_value(
        request=request,
        key=SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY,
    )
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        payload = model_dump(mode="python")
        if isinstance(payload, Mapping):
            return {str(key): item for key, item in payload.items()}
    return {}


def _provider_delta_durable_execution_input_value(
    *,
    request: object,
    keys: tuple[str, ...],
) -> object | None:
    payload = _provider_delta_durable_execution_inputs_payload(request=request)
    for key in keys:
        value = payload.get(key)
        if value is not None:
            return value
    provider_inputs = payload.get("provider_inputs")
    if isinstance(provider_inputs, Mapping):
        for key in keys:
            value = provider_inputs.get(key)
            if value is not None:
                return value
    return None


def _request_or_durable_execution_input_value(
    *,
    request: object,
    keys: tuple[str, ...],
) -> object | None:
    value = _provider_delta_durable_execution_input_value(
        request=request,
        keys=keys,
    )
    if value is not None:
        return value
    for key in keys:
        value = _request_value(request=request, key=key)
        if value is not None:
            return value
    return None


def _model_payload(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="json")
        if isinstance(dumped, Mapping):
            return {str(key): item for key, item in dumped.items()}
    try:
        raw_vars = vars(value)
    except TypeError:
        return {}
    if isinstance(raw_vars, Mapping):
        return {str(key): item for key, item in raw_vars.items()}
    return {}


def _mapping_value(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _json_safe_metric_value(value: object) -> object | None:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, UUID):
        return str(value)
    return None


def _class_signature_payload(
    payload: Mapping[str, object],
) -> dict[str, object]:
    existing = _mapping_value(payload.get("class_signature"))
    if existing:
        return existing
    return {
        "class_fqn": _optional_text(payload.get("class_fqn")),
        "name": _optional_text(payload.get("name") or payload.get("entity_name")),
        "description": _optional_text(payload.get("description")),
        "is_base": _class_signature_bool_value(payload.get("is_base")),
        "is_edge": _class_signature_bool_value(payload.get("is_edge")),
        "value_mode": _optional_text(payload.get("value_mode")),
        "identity_mode": _optional_text(payload.get("identity_mode")),
    }


def _class_signature_bool_value(
    value: object,
    *,
    fallback: object | None = None,
) -> bool | str | None:
    raw_value = value if value is not None else fallback
    if isinstance(raw_value, bool):
        return raw_value
    text = _optional_text(raw_value)
    if text is None:
        return None
    folded = text.casefold()
    if folded in {"1", "true", "yes", "y", "on"}:
        return True
    if folded in {"0", "false", "no", "n", "off"}:
        return False
    return text


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _tuple_text(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        values: list[str] = []
        for item in value:
            text = _optional_text(item)
            if text is not None:
                values.append(text)
        return tuple(values)
    text = _optional_text(value)
    return (text,) if text is not None else ()


__all__ = [
    "_BASELINE_COMMIT_REF_FIELDS",
    "_baseline_commit_refs",
    "_baseline_dirty_preflight",
    "_baseline_ref_missing_required_fields",
    "_baseline_ref_payload",
    "_baseline_semantic_object_index_from_oig",
    "_coerce_hydrated_oig_payload",
    "_int_object_value",
    "_int_payload_value",
    "_looks_like_oig",
    "_request_baseline_oig_hydrator",
    "_request_or_durable_execution_input_value",
    "_request_value",
    "_uuid_value",
]
