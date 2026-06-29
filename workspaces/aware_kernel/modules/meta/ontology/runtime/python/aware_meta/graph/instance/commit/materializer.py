"""Deterministic OIG materializer over a commit lane.

Lane key (today): `(branch_id, projection_hash)`.

SSOT for evolution: `ObjectInstanceGraphCommit` (history Commit + Change graph payload).

This materializer is pure in-memory:
- applies commit Change graphs to OIG snapshots using `apply_object_instance_graph_changes`
- validates pre/post hashes per commit
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any
from uuid import UUID

from collections.abc import Mapping

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_history_ontology.lane.lane import Lane
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.class_.class_config import ClassConfig

from aware_meta.graph.instance.apply import apply_object_instance_graph_changes
from aware_meta.graph.instance.builder import build_rooted_object_instance_graph_base
from aware_meta.graph.instance.commit.hash_contract import compute_oig_lane_hash_state
from aware_meta.graph.instance.commit.fs_store import FSCommitStore, FSSnapshotStore
from aware_meta.graph.instance.commit.validator import (
    OigCommitValidationError,
    validate_object_instance_graph_commit,
)
from aware_meta.graph.instance.root import (
    resolve_root_source_object_id,
)
from aware_meta.graph.instance.change import (
    CommitChangeTreeSummary,
    build_commit_semantics_payload,
    summarize_commit_change_tree,
)


@dataclass(frozen=True, slots=True)
class MaterializerPostHashMismatchDetails:
    have_hash: str
    expected_hash: str
    raw_hash: str
    volatile_source_reference_attrs_removed: int
    commit_id: UUID
    branch_id: UUID
    projection_hash: str
    class_instances: int
    relationships: int
    change_tree: CommitChangeTreeSummary
    semantics: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "have_hash": self.have_hash,
            "expected_hash": self.expected_hash,
            "raw_hash": self.raw_hash,
            "volatile_source_reference_attrs_removed": self.volatile_source_reference_attrs_removed,
            "commit_id": str(self.commit_id),
            "branch_id": str(self.branch_id),
            "projection_hash": self.projection_hash,
            "class_instances": self.class_instances,
            "relationships": self.relationships,
            "change_tree": self.change_tree.to_dict(),
            "semantics": dict(self.semantics),
        }


class MaterializerPostHashMismatchError(ValueError):
    """Typed post-hash mismatch error carrying canonical commit semantics."""

    details: MaterializerPostHashMismatchDetails

    def __init__(self, *, details: MaterializerPostHashMismatchDetails) -> None:
        self.details = details
        super().__init__(self._build_message(details))

    @staticmethod
    def _build_message(details: MaterializerPostHashMismatchDetails) -> str:
        descriptor_count = details.semantics.get("descriptor_count")
        descriptor_kind_counts = details.semantics.get("descriptor_kind_counts")
        return (
            "Materializer post-hash mismatch: "
            f"have={details.have_hash} expected={details.expected_hash} raw_have={details.raw_hash} "
            f"volatile_source_ref_attrs_removed={details.volatile_source_reference_attrs_removed} "
            f"commit={details.commit_id} "
            f"branch_id={details.branch_id} projection_hash={details.projection_hash} "
            f"class_instances={details.class_instances} "
            f"relationships={details.relationships} "
            f"oig_changes={details.change_tree.oig_changes} "
            f"class_instance_changes={details.change_tree.class_instance_changes} "
            f"attribute_changes={details.change_tree.attribute_changes} "
            f"value_root_changes={details.change_tree.value_root_changes} "
            f"value_link_changes={details.change_tree.value_link_changes} "
            f"relationship_changes={details.change_tree.relationship_changes} "
            f"change_deltas={details.change_tree.change_deltas} "
            f"descriptor_count={descriptor_count} "
            f"descriptor_kind_counts={descriptor_kind_counts} "
            "hint=lane_commit_not_replayable_under_current_materializer_contract"
        )


class OIGMaterializer:
    """Deterministic OIG materializer over (branch_id, projection_hash) commit streams."""

    def __init__(
        self,
        commits: FSCommitStore | None = None,
        snaps: FSSnapshotStore | None = None,
    ) -> None:
        self.commits = commits or FSCommitStore()
        self.snaps = snaps or FSSnapshotStore()

    async def get(
        self,
        *,
        branch_id: UUID,
        ocg: ObjectConfigGraph,
        opg: ObjectProjectionGraph,
        commit_id: UUID | None,
        oig_id: UUID | None = None,
        attribute_configs_by_id: Mapping[UUID, AttributeConfig] | None = None,
        class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
        timings: Any | None = None,
    ) -> tuple[ObjectInstanceGraph, dict[str, Any]]:
        """
        Materialize the lane up to `commit_id` (or HEAD if None).

        Args:
            branch_id: Lane identifier (branch head pointer lives outside the commit DAG).
            ocg: ObjectConfigGraph for descriptor and relationship resolution.
            opg: ObjectProjectionGraph (membership + traversal contract).
            commit_id: Target history Commit id to materialize to; defaults to HEAD.
            oig_id: Optional stable ObjectInstanceGraph id to use when bootstrapping an empty lane.
            attribute_configs_by_id: Optional pre-indexed AttributeConfig mapping (supports cross-module OPGs).
            class_configs_by_id: Optional pre-indexed ClassConfig mapping (supports cross-module OPGs).
        """
        total_started = time.perf_counter()
        def _maybe_metric(key: str, value: Any) -> None:
            metric = getattr(timings, "metric", None) if timings is not None else None
            if not callable(metric) or not key:
                return
            try:
                metric(key, value)
            except Exception:
                pass

        def _elapsed_ms(*, started: float) -> int:
            return max(int((time.perf_counter() - started) * 1000), 0)

        try:
            index_started = time.perf_counter()
            attr_cfgs = (
                dict(attribute_configs_by_id)
                if attribute_configs_by_id is not None
                else _attribute_configs_by_id(ocg)
            )
            class_cfgs = (
                dict(class_configs_by_id)
                if class_configs_by_id is not None
                else _class_configs_by_id(ocg)
            )
            _maybe_metric("oig_materializer_index_build_ms", _elapsed_ms(started=index_started))
            _maybe_metric("oig_materializer_attribute_config_count", len(attr_cfgs))
            _maybe_metric("oig_materializer_class_config_count", len(class_cfgs))

            # SSOT for OIG identity is the lane HEAD metadata (when present).
            head_started = time.perf_counter()
            head = await self.commits.head(branch_id=branch_id, projection_hash=opg.projection_hash)
            _maybe_metric("oig_materializer_head_read_ms", _elapsed_ms(started=head_started))
            head_cid: UUID | None = UUID(str(head["commit_id"])) if head and head.get("commit_id") else None
            head_root: UUID | None = None
            if head and head.get("root_object_id"):
                try:
                    head_root = UUID(str(head["root_object_id"]))
                except Exception:
                    head_root = None
            head_oig_id: UUID | None = None
            if head and head.get("object_instance_graph_id"):
                try:
                    head_oig_id = UUID(str(head["object_instance_graph_id"]))
                except Exception:
                    head_oig_id = None

            _maybe_metric("oig_materializer_head_present", bool(head))
            _maybe_metric("oig_materializer_head_commit_id", str(head_cid) if head_cid else None)

            target_commit_id = commit_id
            if target_commit_id is not None:
                resolved_target_commit_id = (
                    await self.commits.domain_commit_id_for_object_instance_graph_commit_id(
                        branch_id=branch_id,
                        projection_hash=opg.projection_hash,
                        object_instance_graph_commit_id=target_commit_id,
                    )
                )
                if resolved_target_commit_id is not None:
                    target_commit_id = resolved_target_commit_id

            snapshot_lookup_started = time.perf_counter()
            base = await self.snaps.nearest_at_or_before(
                branch_id=branch_id,
                projection_hash=opg.projection_hash,
                commit_id=target_commit_id,
            )
            _maybe_metric(
                "oig_materializer_snapshot_lookup_ms",
                _elapsed_ms(started=snapshot_lookup_started),
            )

            preloaded_replay_commits: tuple[ObjectInstanceGraphCommit, ...] | None = None
            if base:
                base_cid, graph, indexes = base
            else:
                if head_cid is None:
                    raise RuntimeError(
                        "ObjectInstanceGraph materializer cannot synthesize a rooted snapshot for an empty lane. "
                        + f"branch_id={branch_id} projection_hash={opg.projection_hash}"
                    )
                if oig_id is None:
                    oig_id = head_oig_id
                target = target_commit_id or head_cid
                bootstrap_lineage_started = time.perf_counter()
                preloaded_replay_commits = await self._load_lineage_forward(
                    branch_id=branch_id,
                    projection_hash=opg.projection_hash,
                    head_commit_id=target,
                    stop_at_commit_id=None,
                )
                _maybe_metric(
                    "oig_materializer_bootstrap_lineage_load_ms",
                    _elapsed_ms(started=bootstrap_lineage_started),
                )
                _maybe_metric(
                    "oig_materializer_bootstrap_lineage_loaded_commit_count",
                    len(preloaded_replay_commits),
                )
                bootstrap_commit = (
                    preloaded_replay_commits[0]
                    if preloaded_replay_commits
                    else None
                )
                if bootstrap_commit is None:
                    raise RuntimeError(
                        "ObjectInstanceGraph materializer could not resolve a bootstrap commit for rooted replay. "
                        + f"branch_id={branch_id} projection_hash={opg.projection_hash} target_commit_id={target}"
                    )
                if oig_id is None:
                    oig_id = bootstrap_commit.object_instance_graph_id
                if oig_id != bootstrap_commit.object_instance_graph_id:
                    raise RuntimeError(
                        "ObjectInstanceGraph materializer bootstrap commit targets unexpected OIG id: "
                        + f"expected={oig_id} bootstrap={bootstrap_commit.object_instance_graph_id}"
                    )
                graph = build_rooted_object_instance_graph_base(
                    key=bootstrap_commit.object_instance_graph_key,
                    name=bootstrap_commit.object_instance_graph_name,
                    description=bootstrap_commit.object_instance_graph_description or "",
                    object_config_graph=ocg,
                    object_projection_graph=opg,
                    root_source_object_id=bootstrap_commit.root_source_object_id,
                    root_class_config_id=bootstrap_commit.root_class_config_id,
                    oig_id=oig_id,
                )
                bootstrap_hash_started = time.perf_counter()
                bootstrap_hash_state = compute_oig_lane_hash_state(
                    graph=graph,
                    schema_attribute_configs_by_id=attr_cfgs,
                    expected_hash=bootstrap_commit.graph_hash_pre or "",
                )
                _maybe_metric(
                    "oig_materializer_bootstrap_hash_ms",
                    _elapsed_ms(started=bootstrap_hash_started),
                )
                expected_bootstrap_hash = bootstrap_commit.graph_hash_pre or ""
                if expected_bootstrap_hash and not bootstrap_hash_state.matches(expected_bootstrap_hash):
                    raise RuntimeError(
                        "ObjectInstanceGraph materializer bootstrap base-hash mismatch: "
                        + f"have={bootstrap_hash_state.lane_hash} raw_have={bootstrap_hash_state.raw_hash} "
                        + f"expected={expected_bootstrap_hash} "
                        + f"object_instance_graph_id={oig_id} commit_id={bootstrap_commit.commit.id}"
                    )
                graph.hash = bootstrap_hash_state.matched_hash_or_default(expected_bootstrap_hash)
                indexes = {}
                base_cid = None

            _maybe_metric("oig_materializer_base_snapshot_hit", bool(base is not None))
            _maybe_metric(
                "oig_materializer_base_snapshot_commit_id",
                str(base_cid) if base_cid else None,
            )
            if base_cid is not None:
                try:
                    lane_dir = self.snaps._lane_dir(branch_id, opg.projection_hash)
                    snap_path = lane_dir / "snapshots" / f"{base_cid}.json"
                    _maybe_metric(
                        "oig_materializer_base_snapshot_bytes",
                        int(snap_path.stat().st_size) if snap_path.exists() else 0,
                    )
                except Exception:
                    pass

            if head_cid is None:
                raise RuntimeError(
                    "ObjectInstanceGraph materializer reached an empty lane without a rooted snapshot. "
                    + f"branch_id={branch_id} projection_hash={opg.projection_hash}"
                )
            if head_root is not None:
                graph_root_source_object_id = resolve_root_source_object_id(graph)
                if graph_root_source_object_id != head_root:
                    raise RuntimeError(
                        "ObjectInstanceGraph materializer head root mismatch: "
                        + f"head_root_object_id={head_root} graph_root_source_object_id={graph_root_source_object_id}"
                    )

            # Walk lineage forward from (base_cid) to target (commit_id or HEAD)
            target = target_commit_id or head_cid
            _maybe_metric("oig_materializer_target_commit_id", str(target) if target else None)
            if base_cid is not None and base_cid == target:
                cached_indexes = dict(indexes)
                cached_indexes.pop("v", None)
                if (
                    not isinstance(cached_indexes.get("instance_map"), dict)
                    or not isinstance(cached_indexes.get("classcfg_map"), dict)
                ):
                    index_rebuild_started = time.perf_counter()
                    cached_indexes = self._indexes_from_graph(graph)
                    _maybe_metric(
                        "oig_materializer_snapshot_index_rebuild_ms",
                        _elapsed_ms(started=index_rebuild_started),
                    )
                _maybe_metric("oig_materializer_applied_commit_count", 0)
                _maybe_metric("oig_materializer_replay_loaded_commit_count", 0)
                _maybe_metric("oig_materializer_snapshot_written", False)
                return graph, cached_indexes

            if preloaded_replay_commits is None:
                replay_lineage_started = time.perf_counter()
                replay_commits = await self._load_lineage_forward(
                    branch_id=branch_id,
                    projection_hash=opg.projection_hash,
                    head_commit_id=target,
                    stop_at_commit_id=base_cid,
                )
                _maybe_metric(
                    "oig_materializer_replay_lineage_load_ms",
                    _elapsed_ms(started=replay_lineage_started),
                )
                _maybe_metric("oig_materializer_replay_reused_bootstrap_lineage", False)
            else:
                replay_commits = preloaded_replay_commits
                _maybe_metric("oig_materializer_replay_lineage_load_ms", 0)
                _maybe_metric("oig_materializer_replay_reused_bootstrap_lineage", True)
            _maybe_metric("oig_materializer_replay_loaded_commit_count", len(replay_commits))

            applied_count = 0
            validation_ms = 0
            pre_hash_ms = 0
            apply_ms = 0
            post_hash_ms = 0

            for c in replay_commits:
                applied_count += 1
                if c.projection_hash and c.projection_hash != opg.projection_hash:
                    raise ValueError(f"Commit {c.commit.id} projection_hash mismatch")

                try:
                    validation_started = time.perf_counter()
                    validate_object_instance_graph_commit(
                        commit=c,
                        expected_object_instance_graph_identity_id=c.object_instance_graph_identity_id,
                        expected_object_instance_graph_id=graph.id,
                        expected_projection_hash=opg.projection_hash,
                        require_linear_history=True,
                    )
                    validation_ms += _elapsed_ms(started=validation_started)
                except OigCommitValidationError as e:
                    raise ValueError(f"Invalid OIG commit payload (commit_id={c.commit.id}): {e}") from e

                pre_hash_started = time.perf_counter()
                pre_hash_state = compute_oig_lane_hash_state(
                    graph=graph,
                    schema_attribute_configs_by_id=attr_cfgs,
                    expected_hash=c.graph_hash_pre or "",
                )
                pre_hash_ms += _elapsed_ms(started=pre_hash_started)
                expected_pre = c.graph_hash_pre or ""
                if expected_pre and not pre_hash_state.matches(expected_pre):
                    raise ValueError(
                        "Materializer pre-hash mismatch: "
                        + f"have={pre_hash_state.lane_hash} raw_have={pre_hash_state.raw_hash} "
                        + f"expected={expected_pre} commit={c.commit.id}"
                    )
                graph.hash = pre_hash_state.matched_hash_or_default(expected_pre)

                if c.object_instance_graph_changes:
                    apply_started = time.perf_counter()
                    apply_object_instance_graph_changes(
                        graph=graph,
                        changes=c.object_instance_graph_changes,
                        attribute_configs_by_id=attr_cfgs,
                        class_configs_by_id=class_cfgs,
                    )
                    apply_ms += _elapsed_ms(started=apply_started)

                post_hash_started = time.perf_counter()
                post_hash_state = compute_oig_lane_hash_state(
                    graph=graph,
                    schema_attribute_configs_by_id=attr_cfgs,
                    expected_hash=c.graph_hash_post or "",
                )
                post_hash_ms += _elapsed_ms(started=post_hash_started)
                graph.hash = post_hash_state.matched_hash_or_default(c.graph_hash_post or "")
                expected_post = c.graph_hash_post
                if not post_hash_state.matches(expected_post):
                    change_tree = summarize_commit_change_tree(commit=c)
                    semantics = build_commit_semantics_payload(
                        commit=c,
                        include_descriptors=False,
                    )
                    raise MaterializerPostHashMismatchError(
                        details=MaterializerPostHashMismatchDetails(
                            have_hash=str(post_hash_state.lane_hash or ""),
                            expected_hash=str(expected_post or ""),
                            raw_hash=str(post_hash_state.raw_hash or ""),
                            volatile_source_reference_attrs_removed=(
                                post_hash_state.volatile_source_reference_attrs_removed
                            ),
                            commit_id=c.commit.id,
                            branch_id=branch_id,
                            projection_hash=opg.projection_hash,
                            class_instances=len(graph.class_instances),
                            relationships=len(graph.class_instance_relationships),
                            change_tree=change_tree,
                            semantics=semantics,
                        )
                    )

            _maybe_metric("oig_materializer_applied_commit_count", applied_count)
            _maybe_metric("oig_materializer_replay_validation_ms", validation_ms)
            _maybe_metric("oig_materializer_replay_pre_hash_ms", pre_hash_ms)
            _maybe_metric("oig_materializer_replay_apply_ms", apply_ms)
            _maybe_metric("oig_materializer_replay_post_hash_ms", post_hash_ms)

            # Opportunistic snapshot at target
            wrote_snapshot = False
            index_build_started = time.perf_counter()
            indexes = self._indexes_from_graph(graph)
            _maybe_metric(
                "oig_materializer_snapshot_index_build_ms",
                _elapsed_ms(started=index_build_started),
            )
            snapshot_write_started = time.perf_counter()
            try:
                await self.snaps.put(
                    branch_id=branch_id,
                    projection_hash=opg.projection_hash,
                    commit_id=target,
                    oig=graph,
                    indexes=indexes,
                )
                wrote_snapshot = True
            except Exception:
                pass
            _maybe_metric(
                "oig_materializer_snapshot_write_ms",
                _elapsed_ms(started=snapshot_write_started),
            )
            _maybe_metric("oig_materializer_snapshot_written", wrote_snapshot)

            return graph, indexes
        finally:
            _maybe_metric("oig_materializer_total_ms", _elapsed_ms(started=total_started))

    async def _load_lineage_forward(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        head_commit_id: UUID,
        stop_at_commit_id: UUID | None,
    ) -> tuple[ObjectInstanceGraphCommit, ...]:
        chain: list[ObjectInstanceGraphCommit] = []
        current_commit_id: UUID | None = head_commit_id
        seen_commit_ids: set[UUID] = set()

        while current_commit_id is not None and current_commit_id not in seen_commit_ids:
            seen_commit_ids.add(current_commit_id)
            lookup_commit_id = current_commit_id
            commit = await self.commits.get_commit(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=lookup_commit_id,
            )
            if commit is None:
                domain_commit_id = (
                    await self.commits.domain_commit_id_for_object_instance_graph_commit_id(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        object_instance_graph_commit_id=current_commit_id,
                    )
                )
                if domain_commit_id is not None:
                    lookup_commit_id = domain_commit_id
                    commit = await self.commits.get_commit(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=lookup_commit_id,
                    )
            if commit is None:
                raise ValueError(
                    f"Missing commit file for {current_commit_id} in lane ({branch_id}, {projection_hash})"
                )

            chain.append(commit)
            if stop_at_commit_id is not None and stop_at_commit_id in {
                current_commit_id,
                lookup_commit_id,
            }:
                break

            parents = commit.commit.commit_parents
            if len(parents) > 1:
                raise ValueError(f"Non-linear commit {commit.commit.id} has {len(parents)} parents")
            current_commit_id = parents[0].parent_commit_id if parents else None

        out: list[ObjectInstanceGraphCommit] = []
        for commit in reversed(chain):
            if stop_at_commit_id is not None and commit.commit.id == stop_at_commit_id:
                continue
            out.append(commit)
        return tuple(out)

    async def get_for_lane(
        self,
        *,
        lane: Lane,
        ocg: ObjectConfigGraph,
        opg: ObjectProjectionGraph,
        commit_id: UUID | None,
        oig_id: UUID | None = None,
        attribute_configs_by_id: Mapping[UUID, AttributeConfig] | None = None,
        class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
    ) -> tuple[ObjectInstanceGraph, dict[str, Any]]:
        """Materialize using a canonical `Lane` identity object (Lane.branch_id + Lane.lane_hash)."""
        if lane.lane_hash != opg.projection_hash:
            raise ValueError(
                "Lane hash mismatch with provided OPG: "
                f"lane_hash={lane.lane_hash} opg.projection_hash={opg.projection_hash}"
            )
        return await self.get(
            branch_id=lane.branch_id,
            ocg=ocg,
            opg=opg,
            commit_id=commit_id,
            oig_id=oig_id,
            attribute_configs_by_id=attribute_configs_by_id,
            class_configs_by_id=class_configs_by_id,
        )

    def _indexes_from_graph(self, graph: ObjectInstanceGraph) -> dict[str, Any]:
        # Keep legacy index keys, but for canonical ClassInstance ids the mapping is identity.
        inst_map: dict[str, str] = {}
        classcfg_map: dict[str, str] = {}
        for ci in graph.class_instances:
            if ci.id is None or ci.class_config_id is None:
                continue
            inst_map[str(ci.id)] = str(ci.id)
            classcfg_map[str(ci.id)] = str(ci.class_config_id)
        return {"instance_map": inst_map, "classcfg_map": classcfg_map}


def _attribute_configs_by_id(ocg: ObjectConfigGraph) -> dict[UUID, AttributeConfig]:
    out: dict[UUID, AttributeConfig] = {}
    for node in ocg.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
            continue
        for link in node.class_config.class_config_attribute_configs:
            if link.attribute_config is None:
                continue
            out[link.attribute_config.id] = link.attribute_config
    return out


def _class_configs_by_id(ocg: ObjectConfigGraph) -> dict[UUID, ClassConfig]:
    out: dict[UUID, ClassConfig] = {}
    for node in ocg.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
            continue
        out[node.class_config.id] = node.class_config
    return out


__all__ = [
    "MaterializerPostHashMismatchDetails",
    "MaterializerPostHashMismatchError",
    "OIGMaterializer",
]
