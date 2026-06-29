from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
from typing import Protocol, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as DescKind,
)
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.attribute.attribute_value_link import (
    AttributeValueLink,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)

from aware_meta.graph.config.lane.common import bool_env_default_true
from aware_meta.graph.config.lane.telemetry import (
    SeedTimings,
    maybe_metric,
    maybe_timed,
)
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.index import (
    ObjectInstanceGraphIndex,
    build_index,
)
from aware_meta.graph.instance.scoped_index import (
    OigGraphDiffIndex,
    build_oig_graph_diff_index,
    deserialize_oig_graph_diff_index_sidecar,
    serialize_oig_graph_diff_index_sidecar,
)
from aware_orm.session.autobind import disable_autobind

logger = logging.getLogger(__name__)


class _MsgpackPackFn(Protocol):
    def __call__(self, o: object, **kwargs: object) -> bytes | bytearray | memoryview: ...


class _MsgpackUnpackFn(Protocol):
    def __call__(self, packed: bytes | bytearray | memoryview, **kwargs: object) -> object: ...


def _as_str_object_dict(payload: object) -> dict[str, object] | None:
    if not isinstance(payload, dict):
        return None
    payload_dict = cast(dict[object, object], payload)
    coerced: dict[str, object] = {}
    for key, value in payload_dict.items():
        if not isinstance(key, str):
            return None
        coerced[key] = value
    return coerced


def _load_msgpack_pack_fn() -> _MsgpackPackFn | None:
    try:
        import msgpack  # pyright: ignore[reportMissingTypeStubs]
        return cast(_MsgpackPackFn, msgpack.packb)
    except Exception:
        return None


def _load_msgpack_unpack_fn() -> _MsgpackUnpackFn | None:
    try:
        import msgpack  # pyright: ignore[reportMissingTypeStubs]
        return cast(_MsgpackUnpackFn, msgpack.unpackb)
    except Exception:
        return None


def load_pre_oig_from_snapshot_fast_path(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    timings: SeedTimings | None = None,
) -> tuple[ObjectInstanceGraph, dict[str, object]] | None:
    """Best-effort exact-commit snapshot load (pickle -> msgpack -> json)."""

    def _disable_wrapping_context():
        try:
            from aware_orm.session.change_collector import disable_change_tracking_hooks

            return disable_change_tracking_hooks()
        except Exception:
            return nullcontext()

    lane_dir = Path(store.aware_root) / ".aware" / "oig" / str(branch_id) / str(projection_hash).strip()
    snapshots_dir = lane_dir / "snapshots"
    indexes_dir = lane_dir / "indexes"
    json_path = snapshots_dir / f"{commit_id}.json"
    msgpack_path = snapshots_dir / f"{commit_id}.msgpack"
    pickle_path = snapshots_dir / f"{commit_id}.pickle"
    index_path = indexes_dir / f"{commit_id}.json"
    pickle_enabled = bool_env_default_true("AWARE_OCG_DELTA_SNAPSHOT_PICKLE_SIDECAR_ENABLED")
    maybe_metric(
        timings,
        "ocg_delta_materialize_pre_snapshot_pickle_enabled",
        pickle_enabled,
    )

    canonical_snapshot_exists = json_path.exists() or msgpack_path.exists()
    if not canonical_snapshot_exists:
        maybe_metric(timings, "ocg_delta_materialize_pre_snapshot_loader", "miss")
        return None

    indexes: dict[str, object] = {}
    if index_path.exists():
        try:
            with maybe_timed(timings, "ocg_delta.materialize_oig_pre_snapshot_read_index"):
                raw_indexes_object = cast(
                    object,
                    json.loads(index_path.read_text(encoding="utf-8")),
                )
            coerced_indexes = _as_str_object_dict(raw_indexes_object)
            if coerced_indexes is not None:
                indexes = coerced_indexes
        except Exception:
            indexes = {}

    def _maybe_write_pickle_sidecar(*, oig: ObjectInstanceGraph) -> bool:
        if not pickle_enabled or pickle_path.exists():
            return False
        try:
            import pickle

            with maybe_timed(timings, "ocg_delta.materialize_oig_pre_snapshot_write_pickle"):
                _ = pickle_path.write_bytes(pickle.dumps(oig, protocol=pickle.HIGHEST_PROTOCOL))
            return True
        except Exception:
            return False

    if pickle_enabled and pickle_path.exists():
        try:
            import pickle

            with maybe_timed(
                timings,
                "ocg_delta.materialize_oig_pre_snapshot_read_pickle",
            ):
                payload_bytes = pickle_path.read_bytes()
            with maybe_timed(
                timings,
                "ocg_delta.materialize_oig_pre_snapshot_load_pickle",
            ):
                with disable_autobind(), _disable_wrapping_context():
                    oig_object = cast(object, pickle.loads(payload_bytes))
            if not isinstance(oig_object, ObjectInstanceGraph):
                raise TypeError(
                    "Snapshot pickle sidecar payload is not an ObjectInstanceGraph instance"
                )
            maybe_metric(timings, "ocg_delta_materialize_pre_snapshot_loader", "pickle")
            return oig_object, indexes
        except Exception:
            maybe_metric(
                timings,
                "ocg_delta_materialize_pre_snapshot_loader_fallback",
                "pickle_error",
            )

    unpackb = _load_msgpack_unpack_fn()
    if msgpack_path.exists() and unpackb is not None:
        try:
            with maybe_timed(
                timings,
                "ocg_delta.materialize_oig_pre_snapshot_read_msgpack",
            ):
                payload_bytes = msgpack_path.read_bytes()
            with maybe_timed(
                timings,
                "ocg_delta.materialize_oig_pre_snapshot_decode_msgpack",
            ):
                payload = unpackb(payload_bytes, raw=False)
            with maybe_timed(
                timings,
                "ocg_delta.materialize_oig_pre_snapshot_validate_msgpack",
            ):
                with disable_autobind(), _disable_wrapping_context():
                    oig = ObjectInstanceGraph.model_validate(payload)
            maybe_metric(timings, "ocg_delta_materialize_pre_snapshot_loader", "msgpack")
            maybe_metric(
                timings,
                "ocg_delta_materialize_pre_snapshot_pickle_written",
                _maybe_write_pickle_sidecar(oig=oig),
            )
            return oig, indexes
        except Exception:
            maybe_metric(
                timings,
                "ocg_delta_materialize_pre_snapshot_loader",
                "msgpack_error_fallback_json",
            )

    if not json_path.exists():
        maybe_metric(timings, "ocg_delta_materialize_pre_snapshot_loader", "miss")
        return None

    try:
        with maybe_timed(timings, "ocg_delta.materialize_oig_pre_snapshot_read_json"):
            payload_json = json_path.read_text(encoding="utf-8")
        with maybe_timed(timings, "ocg_delta.materialize_oig_pre_snapshot_validate_json"):
            with disable_autobind(), _disable_wrapping_context():
                oig = ObjectInstanceGraph.model_validate_json(payload_json)
        maybe_metric(timings, "ocg_delta_materialize_pre_snapshot_loader", "json")
    except Exception:
        maybe_metric(
            timings,
            "ocg_delta_materialize_pre_snapshot_loader",
            "json_error",
        )
        return None

    wrote_msgpack_sidecar = False
    if not msgpack_path.exists():
        packb = _load_msgpack_pack_fn()
        if packb is not None:
            try:
                with maybe_timed(
                    timings,
                    "ocg_delta.materialize_oig_pre_snapshot_write_msgpack",
                ):
                    packed_payload = packb(
                        oig.model_dump(mode="json", exclude_none=True),
                        use_bin_type=True,
                    )
                    if isinstance(packed_payload, memoryview):
                        _ = msgpack_path.write_bytes(packed_payload.tobytes())
                    else:
                        _ = msgpack_path.write_bytes(bytes(packed_payload))
                wrote_msgpack_sidecar = True
            except Exception:
                wrote_msgpack_sidecar = False
    maybe_metric(
        timings,
        "ocg_delta_materialize_pre_snapshot_msgpack_written",
        wrote_msgpack_sidecar,
    )
    maybe_metric(
        timings,
        "ocg_delta_materialize_pre_snapshot_pickle_written",
        _maybe_write_pickle_sidecar(oig=oig),
    )
    return oig, indexes


def oig_diff_index_sidecar_path(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
) -> Path:
    return (
        Path(store.aware_root)
        / ".aware"
        / "oig"
        / str(branch_id)
        / str(projection_hash).strip()
        / "indexes"
        / f"{commit_id}.oig-diff-index.pickle"
    )


def _oig_diff_index_sidecar_graph_hash_key(*, graph_hash: str) -> str:
    normalized = str(graph_hash or "").strip()
    if not normalized:
        return ""
    return uuid5(
        NAMESPACE_URL,
        f"aware:oig-diff-index-graph-hash:{normalized}",
    ).hex


def oig_diff_index_post_sidecar_path(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    graph_hash: str,
) -> Path:
    key = _oig_diff_index_sidecar_graph_hash_key(graph_hash=graph_hash)
    if not key:
        raise ValueError("post diff-index sidecar requires non-empty graph_hash")
    return (
        Path(store.aware_root)
        / ".aware"
        / "oig"
        / str(branch_id)
        / str(projection_hash).strip()
        / "indexes"
        / f"post-{key}.oig-diff-index.pickle"
    )


def load_pre_oig_diff_index_sidecar(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    graph: ObjectInstanceGraph,
    timings: SeedTimings | None = None,
) -> OigGraphDiffIndex | None:
    enabled = bool_env_default_true("AWARE_OCG_DELTA_PRE_DIFF_INDEX_SIDECAR_ENABLED")
    maybe_metric(timings, "ocg_delta_oig_diff_index_pre_sidecar_enabled", enabled)
    if not enabled:
        maybe_metric(timings, "ocg_delta_oig_diff_index_pre_sidecar_loader", "disabled")
        return None

    sidecar_path = oig_diff_index_sidecar_path(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
    )
    if not sidecar_path.exists():
        maybe_metric(timings, "ocg_delta_oig_diff_index_pre_sidecar_loader", "miss")
        return None

    try:
        import pickle

        with maybe_timed(timings, "ocg_delta.read_oig_diff_index_pre_sidecar"):
            payload_bytes = sidecar_path.read_bytes()
        with maybe_timed(timings, "ocg_delta.load_oig_diff_index_pre_sidecar"):
            payload = cast(object, pickle.loads(payload_bytes))
        with maybe_timed(timings, "ocg_delta.validate_oig_diff_index_pre_sidecar"):
            index = deserialize_oig_graph_diff_index_sidecar(
                payload=payload,
                graph=graph,
                expected_graph_hash=str(graph.hash or "").strip(),
            )
        maybe_metric(timings, "ocg_delta_oig_diff_index_pre_sidecar_loader", "hit")
        return index
    except Exception as exc:
        maybe_metric(timings, "ocg_delta_oig_diff_index_pre_sidecar_loader", "error")
        maybe_metric(
            timings,
            "ocg_delta_oig_diff_index_pre_sidecar_fallback",
            str(exc),
        )
        return None


def load_post_oig_diff_index_sidecar(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    graph_hash: str,
    graph: ObjectInstanceGraph,
    timings: SeedTimings | None = None,
) -> OigGraphDiffIndex | None:
    enabled = bool_env_default_true("AWARE_OCG_DELTA_POST_DIFF_INDEX_SIDECAR_ENABLED")
    maybe_metric(timings, "ocg_delta_oig_diff_index_post_sidecar_enabled", enabled)
    if not enabled:
        maybe_metric(timings, "ocg_delta_oig_diff_index_post_sidecar_loader", "disabled")
        return None
    if not str(graph_hash or "").strip():
        maybe_metric(timings, "ocg_delta_oig_diff_index_post_sidecar_loader", "miss")
        return None

    try:
        sidecar_path = oig_diff_index_post_sidecar_path(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            graph_hash=graph_hash,
        )
    except Exception:
        maybe_metric(timings, "ocg_delta_oig_diff_index_post_sidecar_loader", "miss")
        return None
    if not sidecar_path.exists():
        maybe_metric(timings, "ocg_delta_oig_diff_index_post_sidecar_loader", "miss")
        return None

    try:
        import pickle

        with maybe_timed(timings, "ocg_delta.read_oig_diff_index_post_sidecar"):
            payload_bytes = sidecar_path.read_bytes()
        with maybe_timed(timings, "ocg_delta.load_oig_diff_index_post_sidecar"):
            payload = cast(object, pickle.loads(payload_bytes))
        with maybe_timed(timings, "ocg_delta.validate_oig_diff_index_post_sidecar"):
            index = deserialize_oig_graph_diff_index_sidecar(
                payload=payload,
                graph=graph,
                expected_graph_hash=str(graph_hash or "").strip(),
            )
        maybe_metric(timings, "ocg_delta_oig_diff_index_post_sidecar_loader", "hit")
        return index
    except Exception as exc:
        maybe_metric(timings, "ocg_delta_oig_diff_index_post_sidecar_loader", "error")
        maybe_metric(
            timings,
            "ocg_delta_oig_diff_index_post_sidecar_fallback",
            str(exc),
        )
        return None


def write_pre_oig_diff_index_sidecar(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    graph_hash: str,
    index: OigGraphDiffIndex,
    timings: SeedTimings | None = None,
) -> bool:
    enabled = bool_env_default_true("AWARE_OCG_DELTA_PRE_DIFF_INDEX_SIDECAR_ENABLED")
    if not enabled:
        return False

    sidecar_path = oig_diff_index_sidecar_path(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
    )
    if sidecar_path.exists():
        return False

    try:
        import pickle

        payload = serialize_oig_graph_diff_index_sidecar(
            index=index,
            graph_hash=graph_hash,
        )
        with maybe_timed(timings, "ocg_delta.write_oig_diff_index_pre_sidecar"):
            sidecar_path.parent.mkdir(parents=True, exist_ok=True)
            _ = sidecar_path.write_bytes(pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL))
        return True
    except Exception:
        return False


def write_post_oig_diff_index_sidecar(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    graph_hash: str,
    index: OigGraphDiffIndex,
    timings: SeedTimings | None = None,
) -> bool:
    enabled = bool_env_default_true("AWARE_OCG_DELTA_POST_DIFF_INDEX_SIDECAR_ENABLED")
    if not enabled or not str(graph_hash or "").strip():
        return False

    try:
        sidecar_path = oig_diff_index_post_sidecar_path(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            graph_hash=graph_hash,
        )
    except Exception:
        return False
    if sidecar_path.exists():
        return False

    try:
        import pickle

        payload = serialize_oig_graph_diff_index_sidecar(
            index=index,
            graph_hash=graph_hash,
        )
        with maybe_timed(timings, "ocg_delta.write_oig_diff_index_post_sidecar"):
            sidecar_path.parent.mkdir(parents=True, exist_ok=True)
            _ = sidecar_path.write_bytes(pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL))
        return True
    except Exception:
        return False


def _bool_env_default_false(name: str) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _ocg_delta_progress_enabled() -> bool:
    return _bool_env_default_false("AWARE_OCG_DELTA_LOG_PROGRESS") or _bool_env_default_false(
        "AWARE_ENV_COMPOSED_RAIL_LOG_SUBSTEPS"
    )


def log_ocg_delta_progress(event: str, **fields: object) -> None:
    if not _ocg_delta_progress_enabled():
        return
    parts = [f"{key}={value}" for key, value in fields.items() if value is not None]
    suffix = (" " + " ".join(parts)) if parts else ""
    logger.info("[commit_ocg_delta_to_lane] %s%s", event, suffix)


def is_volatile_source_reference_attribute_name(name: str | None) -> bool:
    """Return True for non-structural source-reference FK attrs."""
    normalized = (name or "").strip().lower()
    return normalized.startswith("code_section_") and normalized.endswith("_id")


def strip_volatile_source_reference_attrs_from_oig(
    *,
    graph: ObjectInstanceGraph,
    schema_attribute_configs_by_id: dict[UUID, AttributeConfig],
    timings: SeedTimings | None = None,
    metric_prefix: str = "ocg_delta",
) -> int:
    """Strip non-structural source-reference attrs from an OIG snapshot."""
    prefix = (metric_prefix or "").strip() or "ocg_delta"
    volatile_attr_config_ids = {
        attr_id
        for attr_id, attr_cfg in (schema_attribute_configs_by_id or {}).items()
        if is_volatile_source_reference_attribute_name(attr_cfg.name)
    }
    maybe_metric(
        timings,
        f"{prefix}_volatile_source_ref_attr_config_ids",
        len(volatile_attr_config_ids),
    )
    if not volatile_attr_config_ids:
        return 0

    removed = 0
    touched_instances = 0
    for class_instance in graph.class_instances:
        edges = list(class_instance.class_instance_attributes)
        if not edges:
            continue
        kept_edges = []
        removed_here = 0
        for edge in edges:
            attr = edge.attribute
            if attr is None:
                kept_edges.append(edge)
                continue
            if attr.attribute_config_id in volatile_attr_config_ids:
                removed += 1
                removed_here += 1
                continue
            kept_edges.append(edge)
        if removed_here:
            class_instance.class_instance_attributes = kept_edges
            touched_instances += 1

    maybe_metric(
        timings,
        f"{prefix}_volatile_source_ref_attrs_removed",
        removed,
    )
    maybe_metric(
        timings,
        f"{prefix}_volatile_source_ref_instances_touched",
        touched_instances,
    )
    return removed


def _slot_label_for_value_link(link: AttributeValueLink) -> str:
    role = str(link.role.value)
    identity_key = link.identity_key
    if identity_key is not None:
        return f"{role}:{identity_key}"
    position = link.position
    if position is not None:
        return f"{role}:{position}"
    return role


def _expected_child_descriptor_for_value_link(
    *,
    parent_desc: AttributeTypeDescriptor,
    link: AttributeValueLink,
) -> AttributeTypeDescriptor | None:
    if parent_desc.kind in (DescKind.collection, DescKind.mapping):
        for child_link in parent_desc.child_links:
            if child_link.role == link.role:
                return child_link.child
        return None

    if parent_desc.kind in (DescKind.tuple, DescKind.union):
        for child_link in parent_desc.child_links:
            if child_link.role != link.role:
                continue
            if child_link.position == link.position:
                return child_link.child
        return None

    return None


def collect_stale_schema_owned_type_descriptor_mismatches(
    *,
    graph: ObjectInstanceGraph,
    schema_attribute_configs_by_id: dict[UUID, AttributeConfig],
    limit: int = 10,
) -> list[str]:
    out: list[str] = []

    def _walk_value_tree(
        *,
        node: AttributeValue,
        expected_desc: AttributeTypeDescriptor,
        path: str,
        class_instance_id: UUID,
        attribute_config_id: UUID,
    ) -> None:
        if len(out) >= limit:
            return
        actual_desc_id = node.type_descriptor.id
        expected_desc_id = expected_desc.id
        if actual_desc_id != expected_desc_id:
            out.append(
                "class_instance_id="
                + f"{class_instance_id} attribute_config_id={attribute_config_id} path={path} "
                + f"actual_descriptor_id={actual_desc_id} expected_descriptor_id={expected_desc_id}"
            )
            return
        for link in node.child_links:
            expected_child = _expected_child_descriptor_for_value_link(
                parent_desc=expected_desc,
                link=link,
            )
            if expected_child is None:
                continue
            _walk_value_tree(
                node=link.child,
                expected_desc=expected_child,
                path=f"{path}/{_slot_label_for_value_link(link)}",
                class_instance_id=class_instance_id,
                attribute_config_id=attribute_config_id,
            )

    for class_instance in graph.class_instances:
        for attr in class_instance.attributes:
            attr_cfg = schema_attribute_configs_by_id.get(attr.attribute_config_id)
            if attr_cfg is None:
                continue
            _walk_value_tree(
                node=attr.value_root,
                expected_desc=attr_cfg.type_descriptor,
                path="root",
                class_instance_id=class_instance.id,
                attribute_config_id=attr.attribute_config_id,
            )
            if len(out) >= limit:
                return out
    return out


def expand_delta_scoped_candidate_ids(
    *,
    candidate_ids: set[UUID],
    before_oig: ObjectInstanceGraph,
    after_oig: ObjectInstanceGraph,
    metric_prefix: str = "ocg_delta_delta_scoped",
    timings: SeedTimings | None,
) -> set[UUID]:
    """Expand delta-scoped candidate ids using the OIG relationship graph."""
    raw_depth = (os.getenv("AWARE_OCG_DELTA_CANDIDATE_EXPANSION_DEPTH") or "").strip()
    try:
        max_depth = max(int(raw_depth), 0) if raw_depth else 2
    except Exception:
        max_depth = 2

    raw_max = (os.getenv("AWARE_OCG_DELTA_CANDIDATE_MAX_IDS") or "").strip()
    try:
        max_ids = max(int(raw_max), 0) if raw_max else 20_000
    except Exception:
        max_ids = 20_000

    prefix = (metric_prefix or "").strip() or "ocg_delta_delta_scoped"
    base = set(candidate_ids)
    maybe_metric(timings, f"{prefix}_candidate_ids_base", len(base))
    if not base or max_depth <= 0 or max_ids <= 0:
        maybe_metric(timings, f"{prefix}_candidate_ids_expanded", len(base))
        maybe_metric(timings, f"{prefix}_candidate_expansion_depth", 0)
        maybe_metric(timings, f"{prefix}_candidate_expansion_truncated", False)
        return base

    expanded = set(base)
    added_pre = 0
    added_post = 0
    depth_used = 0
    truncated = False

    def _scan_relationships(graph: ObjectInstanceGraph, *, current: set[UUID]) -> set[UUID]:
        to_add: set[UUID] = set()
        for rel in graph.class_instance_relationships:
            src = rel.source_class_instance_id
            tgt = rel.target_class_instance_id
            if src in current and tgt not in current:
                to_add.add(tgt)
            if tgt in current and src not in current:
                to_add.add(src)
        return to_add

    for depth in range(max_depth):
        to_add_pre = _scan_relationships(before_oig, current=expanded)
        to_add_post = _scan_relationships(after_oig, current=expanded)
        to_add = to_add_pre | to_add_post
        if not to_add:
            break

        if len(expanded) + len(to_add) > max_ids:
            truncated = True
            remaining = max_ids - len(expanded)
            if remaining <= 0:
                break
            chosen = sorted(to_add, key=str)[:remaining]
            expanded.update(chosen)
            added_pre += sum(1 for candidate_id in chosen if candidate_id in to_add_pre)
            added_post += sum(1 for candidate_id in chosen if candidate_id in to_add_post)
            depth_used = depth + 1
            break

        expanded.update(to_add)
        added_pre += len(to_add_pre)
        added_post += len(to_add_post)
        depth_used = depth + 1

    maybe_metric(timings, f"{prefix}_candidate_ids_added_pre", added_pre)
    maybe_metric(timings, f"{prefix}_candidate_ids_added_post", added_post)
    maybe_metric(timings, f"{prefix}_candidate_expansion_depth", depth_used)
    maybe_metric(timings, f"{prefix}_candidate_expansion_truncated", truncated)
    maybe_metric(timings, f"{prefix}_candidate_ids_expanded", len(expanded))
    return expanded


@dataclass(frozen=True)
class OigFingerprintDiffScope:
    """OIG fingerprint-derived scoped diff inputs."""

    candidate_ids: set[UUID]
    changed_relationship_tuples: set[tuple[UUID, UUID, UUID]]
    before_graph_index: OigGraphDiffIndex | None = None
    after_graph_index: OigGraphDiffIndex | None = None


def oig_fingerprint_diff_scope(
    *,
    before_oig: ObjectInstanceGraph,
    after_oig: ObjectInstanceGraph,
    timings: SeedTimings | None,
    before_graph_index_hint: OigGraphDiffIndex | None = None,
    after_graph_index_hint: OigGraphDiffIndex | None = None,
) -> OigFingerprintDiffScope:
    """Derive a minimal candidate id set directly from OIG(pre/post) content."""
    try:
        before_graph_index = before_graph_index_hint
        if before_graph_index is None:
            with maybe_timed(timings, "ocg_delta.build_oig_diff_index_pre"):
                before_graph_index = build_oig_graph_diff_index(graph=before_oig)
        after_graph_index = after_graph_index_hint
        if after_graph_index is None:
            with maybe_timed(timings, "ocg_delta.build_oig_diff_index_post"):
                after_graph_index = build_oig_graph_diff_index(graph=after_oig)
    except Exception:
        return OigFingerprintDiffScope(candidate_ids=set(), changed_relationship_tuples=set())

    before_by_id = before_graph_index.class_instances_by_id
    after_by_id = after_graph_index.class_instances_by_id
    before_ids = set(before_by_id.keys())
    after_ids = set(after_by_id.keys())
    maybe_metric(timings, "ocg_delta_oig_diff_index_instance_count_pre", len(before_by_id))
    maybe_metric(timings, "ocg_delta_oig_diff_index_instance_count_post", len(after_by_id))

    candidate_ids: set[UUID] = set()
    candidate_ids.update(before_ids - after_ids)
    candidate_ids.update(after_ids - before_ids)

    before_fingerprints = before_graph_index.class_instance_fingerprints
    after_fingerprints = after_graph_index.class_instance_fingerprints
    changed_instances = 0
    for candidate_id in sorted(before_ids & after_ids, key=str):
        if before_fingerprints.get(candidate_id) != after_fingerprints.get(candidate_id):
            candidate_ids.add(candidate_id)
            changed_instances += 1

    rel_delta = (
        before_graph_index.relationship_membership_tuples
        ^ after_graph_index.relationship_membership_tuples
    )
    for relationship_id, source_id, target_id in rel_delta:
        candidate_ids.add(relationship_id)
        candidate_ids.add(source_id)
        candidate_ids.add(target_id)

    maybe_metric(
        timings,
        "ocg_delta_oig_diff_index_rel_memberships_pre",
        len(before_graph_index.relationship_membership_tuples),
    )
    maybe_metric(
        timings,
        "ocg_delta_oig_diff_index_rel_memberships_post",
        len(after_graph_index.relationship_membership_tuples),
    )
    maybe_metric(timings, "ocg_delta_oig_scoped_instance_ids_pre", len(before_ids))
    maybe_metric(timings, "ocg_delta_oig_scoped_instance_ids_post", len(after_ids))
    maybe_metric(timings, "ocg_delta_oig_scoped_instance_ids_changed", changed_instances)
    maybe_metric(timings, "ocg_delta_oig_scoped_rel_rows_changed", len(rel_delta))
    maybe_metric(timings, "ocg_delta_oig_scoped_candidate_ids_base", len(candidate_ids))
    return OigFingerprintDiffScope(
        candidate_ids=candidate_ids,
        changed_relationship_tuples=rel_delta,
        before_graph_index=before_graph_index,
        after_graph_index=after_graph_index,
    )


def _resolve_oig_scoped_relationship_coverage_limit() -> float:
    raw = (os.getenv("AWARE_OCG_DELTA_OIG_SCOPED_RELATIONSHIP_COVERAGE_MAX") or "").strip()
    try:
        limit = float(raw) if raw else 0.85
    except Exception:
        limit = 0.85
    if limit < 0.0:
        return 0.0
    if limit > 1.0:
        return 1.0
    return limit


def should_skip_oig_scoped_diff_by_relationship_scope(
    *,
    total_relationships_pre: int,
    total_relationships_post: int,
    scoped_relationships_pre: int,
    scoped_relationships_post: int,
) -> tuple[bool, float, float, float]:
    limit = _resolve_oig_scoped_relationship_coverage_limit()
    pre_coverage = (
        float(scoped_relationships_pre) / float(total_relationships_pre)
        if total_relationships_pre > 0
        else 0.0
    )
    post_coverage = (
        float(scoped_relationships_post) / float(total_relationships_post)
        if total_relationships_post > 0
        else 0.0
    )
    should_skip = (total_relationships_pre > 0 and pre_coverage >= limit) or (
        total_relationships_post > 0 and post_coverage >= limit
    )
    return should_skip, pre_coverage, post_coverage, limit


def _summarize_attribute_value(value: AttributeValue | None, *, max_len: int = 160) -> str:
    if value is None:
        return "null"

    primitive = value.primitive_value
    if primitive is not None:
        rendered = repr(primitive)
        if len(rendered) > max_len:
            return rendered[: max_len - 3] + "..."
        return rendered
    if value.enum_option_id is not None:
        return f"enum:{value.enum_option_id}"
    if value.class_instance_id is not None:
        return f"ref:{value.class_instance_id}"
    if value.child_links:
        return f"children:{len(value.child_links)}"
    try:
        rendered = repr(value)
        if len(rendered) > max_len:
            return rendered[: max_len - 3] + "..."
        return rendered
    except Exception:
        return "<unrepr>"


def _index_class_instance_by_id(
    index: ObjectInstanceGraphIndex,
    class_instance_id: UUID,
) -> ClassInstance | None:
    entity = index.get_entity_by_id(class_instance_id)
    if isinstance(entity, ClassInstance):
        return entity
    return None


def _index_attribute_by_id(
    index: ObjectInstanceGraphIndex,
    attribute_id: UUID,
) -> Attribute | None:
    entity = index.get_entity_by_id(attribute_id)
    if isinstance(entity, Attribute):
        return entity
    return None


def summarize_delta_drift(
    *,
    changes: list[ObjectInstanceGraphChange],
    before_oig: ObjectInstanceGraph,
    after_oig: ObjectInstanceGraph,
    schema_class_configs_by_id: dict[UUID, ClassConfig],
    schema_attribute_configs_by_id: dict[UUID, AttributeConfig],
    max_items: int = 6,
    max_attrs: int = 4,
) -> list[dict[str, object]]:
    pre_index = build_index(before_oig)
    post_index = build_index(after_oig)

    out: list[dict[str, object]] = []
    seen_instance_ids: set[UUID] = set()
    seen_rel_ids: set[tuple[str, str, str]] = set()

    def _class_name(class_config_id: UUID | None) -> str | None:
        if class_config_id is None:
            return None
        class_config = schema_class_configs_by_id.get(class_config_id)
        return class_config.name if class_config is not None else str(class_config_id)

    def _attr_name(attribute_config_id: UUID) -> str:
        attribute_config = schema_attribute_configs_by_id.get(attribute_config_id)
        return attribute_config.name if attribute_config is not None else str(attribute_config_id)

    for change in changes:
        if len(out) >= max_items:
            break

        for ci_change in change.class_instance_changes or []:
            if len(out) >= max_items:
                break
            class_instance_id = ci_change.class_instance_id
            if class_instance_id in seen_instance_ids:
                continue
            seen_instance_ids.add(class_instance_id)

            pre_ci = _index_class_instance_by_id(pre_index, class_instance_id)
            post_ci = _index_class_instance_by_id(post_index, class_instance_id)
            class_config_id = (
                post_ci.class_config_id
                if post_ci is not None
                else (pre_ci.class_config_id if pre_ci is not None else None)
            )
            item: dict[str, object] = {
                "kind": "object_instance",
                "op": str(ci_change.change.type),
                "class_instance_id": str(class_instance_id),
                "class_config_id": (str(class_config_id) if class_config_id is not None else None),
                "class_name": _class_name(class_config_id),
            }

            attr_samples: list[dict[str, object]] = []
            for attr_change in (ci_change.attribute_changes or [])[:max_attrs]:
                attribute_id = attr_change.attribute_id
                pre_attr = _index_attribute_by_id(pre_index, attribute_id)
                post_attr = _index_attribute_by_id(post_index, attribute_id)
                attribute_config_id = (
                    post_attr.attribute_config_id
                    if post_attr is not None
                    else (pre_attr.attribute_config_id if pre_attr is not None else None)
                )
                pre_val = pre_attr.value_root if pre_attr is not None else None
                post_val = post_attr.value_root if post_attr is not None else None
                attr_samples.append(
                    {
                        "attribute_id": str(attribute_id),
                        "attribute_config_id": (
                            str(attribute_config_id) if attribute_config_id is not None else None
                        ),
                        "attribute_name": (
                            _attr_name(attribute_config_id)
                            if attribute_config_id is not None
                            else None
                        ),
                        "op": str(attr_change.change.type),
                        "pre": _summarize_attribute_value(pre_val),
                        "post": _summarize_attribute_value(post_val),
                    }
                )
            if attr_samples:
                item["attribute_samples"] = attr_samples
            out.append(item)

        for rel_change in change.class_instance_relationship_changes or []:
            if len(out) >= max_items:
                break
            relationship_id = rel_change.class_config_relationship_id
            source_id = rel_change.source_class_instance_id
            target_id = rel_change.target_class_instance_id
            key = (str(relationship_id), str(source_id), str(target_id))
            if key in seen_rel_ids:
                continue
            seen_rel_ids.add(key)

            source_ci = _index_class_instance_by_id(pre_index, source_id) or _index_class_instance_by_id(
                post_index,
                source_id,
            )
            target_ci = _index_class_instance_by_id(pre_index, target_id) or _index_class_instance_by_id(
                post_index,
                target_id,
            )
            source_class_config_id = source_ci.class_config_id if source_ci is not None else None
            target_class_config_id = target_ci.class_config_id if target_ci is not None else None
            out.append(
                {
                    "kind": "relationship",
                    "op": str(rel_change.change.type),
                    "class_config_relationship_id": str(relationship_id),
                    "source_class_instance_id": str(source_id),
                    "source_class_name": _class_name(source_class_config_id),
                    "target_class_instance_id": str(target_id),
                    "target_class_name": _class_name(target_class_config_id),
                }
            )

    return out


def lane_commit_id(
    *,
    branch_id: UUID,
    projection_hash: str,
    parent_commit_id: UUID,
    ocg_hash_post: str,
) -> UUID:
    return uuid5(
        NAMESPACE_URL,
        f"aware:ocg-commit:{branch_id}:{projection_hash}:{parent_commit_id}:{ocg_hash_post}",
    )


__all__ = [
    "OigFingerprintDiffScope",
    "collect_stale_schema_owned_type_descriptor_mismatches",
    "expand_delta_scoped_candidate_ids",
    "is_volatile_source_reference_attribute_name",
    "load_post_oig_diff_index_sidecar",
    "load_pre_oig_from_snapshot_fast_path",
    "oig_diff_index_post_sidecar_path",
    "oig_diff_index_sidecar_path",
    "oig_fingerprint_diff_scope",
    "should_skip_oig_scoped_diff_by_relationship_scope",
    "strip_volatile_source_reference_attrs_from_oig",
    "write_post_oig_diff_index_sidecar",
    "write_pre_oig_diff_index_sidecar",
]
