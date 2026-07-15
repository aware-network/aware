from __future__ import annotations

import json
from dataclasses import dataclass
from typing import cast
from uuid import UUID

from aware_interface.lane_stores import (
    InterfaceLaneStores,
    LocalCommitRecord,
    LocalSnapshotRecord,
)
from aware_meta.graph.instance.apply import apply_object_instance_graph_changes
from aware_meta.graph.instance.builder import build_rooted_object_instance_graph_base
from aware_meta.graph.instance.change import (
    CommitChangeTreeSummary,
    build_commit_semantics_payload,
    summarize_commit_change_tree,
)
from aware_meta.graph.instance.commit.hash_contract import compute_oig_lane_hash_state
from aware_meta.graph.instance.commit.validator import (
    OigCommitValidationError,
    validate_object_instance_graph_commit,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
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


JsonObject = dict[str, object]


@dataclass(frozen=True, slots=True)
class InterfaceMaterializedLane:
    branch_id: str
    projection_hash: str
    target_commit_id: str
    snapshot_commit_id: str | None
    applied_commit_ids: tuple[str, ...]
    graph: ObjectInstanceGraph
    indexes: JsonObject
    last_change_tree: CommitChangeTreeSummary | None = None
    last_semantics: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class InterfaceMaterializationPostHashMismatchDetails:
    have_hash: str
    expected_hash: str
    raw_hash: str
    volatile_source_reference_attrs_removed: int
    commit_id: str
    branch_id: str
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
            "commit_id": self.commit_id,
            "branch_id": self.branch_id,
            "projection_hash": self.projection_hash,
            "class_instances": self.class_instances,
            "relationships": self.relationships,
            "change_tree": self.change_tree.to_dict(),
            "semantics": dict(self.semantics),
        }


class InterfaceMaterializationPostHashMismatchError(ValueError):
    details: InterfaceMaterializationPostHashMismatchDetails

    def __init__(self, *, details: InterfaceMaterializationPostHashMismatchDetails) -> None:
        self.details = details
        super().__init__(
            f"Interface materialization post-hash mismatch: have={details.have_hash} "
            + f"expected={details.expected_hash} raw_have={details.raw_hash} "
            + f"commit={details.commit_id} branch_id={details.branch_id} projection_hash={details.projection_hash}"
        )


class InterfaceCommitMaterializer:
    """Interface-owned OIG materializer over canonical lane stores."""

    _stores: InterfaceLaneStores

    def __init__(self, *, stores: InterfaceLaneStores) -> None:
        self._stores = stores

    async def materialize_lane_head(
        self,
        *,
        branch_id: str,
        projection_hash: str,
        lane_id: str,
        ocg: ObjectConfigGraph,
        opg: ObjectProjectionGraph,
    ) -> InterfaceMaterializedLane:
        lane_head = await self._stores.load_lane_head(
            branch_id=branch_id,
            lane_id=lane_id,
            projection_hash=projection_hash,
        )
        if lane_head is None:
            raise ValueError(
                f"Interface materializer lane head missing: branch_id={branch_id} "
                + f"projection_hash={projection_hash} lane_id={lane_id}"
            )
        if lane_head.head_commit_id is None or not lane_head.head_commit_id.strip():
            raise ValueError(
                f"Interface materializer cannot replay an empty lane head: branch_id={branch_id} "
                + f"projection_hash={projection_hash} lane_id={lane_id}"
            )
        return await self.materialize_commit(
            branch_id=branch_id,
            projection_hash=projection_hash,
            target_commit_id=lane_head.head_commit_id,
            ocg=ocg,
            opg=opg,
        )

    async def materialize_commit(
        self,
        *,
        branch_id: str,
        projection_hash: str,
        target_commit_id: str,
        ocg: ObjectConfigGraph,
        opg: ObjectProjectionGraph,
    ) -> InterfaceMaterializedLane:
        if projection_hash != opg.projection_hash:
            raise ValueError(
                f"Interface materializer projection hash mismatch: projection_hash={projection_hash} "
                + f"opg.projection_hash={opg.projection_hash}"
            )

        attr_cfgs = _attribute_configs_by_id(ocg)
        class_cfgs = _class_configs_by_id(ocg)

        snapshot_record = await self._nearest_snapshot_at_or_before(
            branch_id=branch_id,
            projection_hash=projection_hash,
            target_commit_id=target_commit_id,
        )
        snapshot_commit_id: str | None = None
        if snapshot_record is not None:
            graph, indexes = _snapshot_from_record(snapshot_record)
            snapshot_commit_id = snapshot_record.commit_id
        else:
            graph = None
            indexes = {}

        commit_records = await self._collect_lineage_records(
            branch_id=branch_id,
            projection_hash=projection_hash,
            target_commit_id=target_commit_id,
            stop_at_commit_id=snapshot_commit_id,
        )

        if graph is None:
            if not commit_records:
                raise ValueError(
                    "Interface materializer cannot bootstrap an empty lane without stored commits: "
                    + f"branch_id={branch_id} projection_hash={projection_hash} "
                    + f"target_commit_id={target_commit_id}"
                )
            bootstrap_commit = _commit_from_record(commit_records[0])
            graph = _build_rooted_base_from_commit(
                commit=bootstrap_commit,
                ocg=ocg,
                opg=opg,
            )
            bootstrap_hash_state = compute_oig_lane_hash_state(
                graph=graph,
                schema_attribute_configs_by_id=attr_cfgs,
                expected_hash=bootstrap_commit.graph_hash_pre or "",
            )
            expected_bootstrap_hash = bootstrap_commit.graph_hash_pre or ""
            if expected_bootstrap_hash and not bootstrap_hash_state.matches(expected_bootstrap_hash):
                raise ValueError(
                    f"Interface materializer bootstrap base-hash mismatch: have={bootstrap_hash_state.lane_hash} "
                    + f"raw_have={bootstrap_hash_state.raw_hash} expected={expected_bootstrap_hash} "
                    + f"commit={bootstrap_commit.commit.id}"
                )
            graph.hash = bootstrap_hash_state.matched_hash_or_default(expected_bootstrap_hash)

        applied_commit_ids: list[str] = []
        last_change_tree: CommitChangeTreeSummary | None = None
        last_semantics: dict[str, object] | None = None

        for commit_record in commit_records:
            commit = _commit_from_record(commit_record)

            try:
                validate_object_instance_graph_commit(
                    commit=commit,
                    expected_object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
                    expected_object_instance_graph_id=graph.id,
                    expected_projection_hash=projection_hash,
                    require_linear_history=True,
                )
            except OigCommitValidationError as exc:
                raise ValueError(f"Invalid stored OIG commit payload (commit_id={commit.commit.id}): {exc}") from exc

            pre_hash_state = compute_oig_lane_hash_state(
                graph=graph,
                schema_attribute_configs_by_id=attr_cfgs,
                expected_hash=commit.graph_hash_pre or "",
            )
            expected_pre = commit.graph_hash_pre or ""
            if expected_pre and not pre_hash_state.matches(expected_pre):
                raise ValueError(
                    f"Interface materializer pre-hash mismatch: have={pre_hash_state.lane_hash} "
                    + f"raw_have={pre_hash_state.raw_hash} expected={expected_pre} commit={commit.commit.id}"
                )
            graph.hash = pre_hash_state.matched_hash_or_default(expected_pre)

            if commit.object_instance_graph_changes:
                _ = apply_object_instance_graph_changes(
                    graph=graph,
                    changes=commit.object_instance_graph_changes,
                    attribute_configs_by_id=attr_cfgs,
                    class_configs_by_id=class_cfgs,
                )

            post_hash_state = compute_oig_lane_hash_state(
                graph=graph,
                schema_attribute_configs_by_id=attr_cfgs,
                expected_hash=commit.graph_hash_post or "",
            )
            graph.hash = post_hash_state.matched_hash_or_default(commit.graph_hash_post or "")
            if not post_hash_state.matches(commit.graph_hash_post or ""):
                change_tree = summarize_commit_change_tree(commit=commit)
                semantics = build_commit_semantics_payload(commit=commit, include_descriptors=False)
                raise InterfaceMaterializationPostHashMismatchError(
                    details=InterfaceMaterializationPostHashMismatchDetails(
                        have_hash=str(post_hash_state.lane_hash or ""),
                        expected_hash=str(commit.graph_hash_post or ""),
                        raw_hash=str(post_hash_state.raw_hash or ""),
                        volatile_source_reference_attrs_removed=(
                            post_hash_state.volatile_source_reference_attrs_removed
                        ),
                        commit_id=str(commit.commit.id),
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        class_instances=len(graph.class_instances),
                        relationships=len(graph.class_instance_relationships),
                        change_tree=change_tree,
                        semantics=semantics,
                    )
                )

            applied_commit_ids.append(str(commit.commit.id))
            last_change_tree = summarize_commit_change_tree(commit=commit)
            last_semantics = build_commit_semantics_payload(
                commit=commit,
                include_descriptors=False,
            )

        _normalize_graph_root_class_instance(graph)
        indexes = _indexes_from_graph(graph)
        await self._stores.save_snapshot(
            LocalSnapshotRecord(
                id=target_commit_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=target_commit_id,
                oig_json=graph.model_dump_json(exclude_none=True),
                indexes_json=json.dumps(indexes, sort_keys=True, separators=(",", ":")),
                v=1,
            )
        )

        return InterfaceMaterializedLane(
            branch_id=branch_id,
            projection_hash=projection_hash,
            target_commit_id=target_commit_id,
            snapshot_commit_id=snapshot_commit_id,
            applied_commit_ids=tuple(applied_commit_ids),
            graph=graph,
            indexes=indexes,
            last_change_tree=last_change_tree,
            last_semantics=last_semantics,
        )

    async def _nearest_snapshot_at_or_before(
        self,
        *,
        branch_id: str,
        projection_hash: str,
        target_commit_id: str,
    ) -> LocalSnapshotRecord | None:
        snapshots = await self._stores.list_snapshots(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        snapshots_by_commit_id = {snapshot.commit_id: snapshot for snapshot in snapshots}

        current_commit_id: str | None = target_commit_id
        visited_commit_ids: set[str] = set()
        while current_commit_id is not None and current_commit_id not in visited_commit_ids:
            visited_commit_ids.add(current_commit_id)
            snapshot = snapshots_by_commit_id.get(current_commit_id)
            if snapshot is not None:
                return snapshot

            commit_record = await self._stores.load_commit(
                branch_id=branch_id,
                commit_id=current_commit_id,
                projection_hash=projection_hash,
            )
            if commit_record is None:
                return None
            current_commit_id = _record_parent_commit_id(commit_record)

        return None

    async def _collect_lineage_records(
        self,
        *,
        branch_id: str,
        projection_hash: str,
        target_commit_id: str,
        stop_at_commit_id: str | None,
    ) -> tuple[LocalCommitRecord, ...]:
        records: list[LocalCommitRecord] = []
        current_commit_id: str | None = target_commit_id
        visited_commit_ids: set[str] = set()

        while current_commit_id is not None and current_commit_id != stop_at_commit_id:
            if current_commit_id in visited_commit_ids:
                raise ValueError(
                    "Interface materializer encountered a cycle in stored commit lineage: "
                    + f"branch_id={branch_id} projection_hash={projection_hash} commit_id={current_commit_id}"
                )
            visited_commit_ids.add(current_commit_id)

            commit_record = await self._stores.load_commit(
                branch_id=branch_id,
                commit_id=current_commit_id,
                projection_hash=projection_hash,
            )
            if commit_record is None:
                raise ValueError(
                    f"Interface materializer missing stored commit payload: branch_id={branch_id} "
                    + f"projection_hash={projection_hash} commit_id={current_commit_id}"
                )
            records.append(commit_record)
            current_commit_id = _record_parent_commit_id(commit_record)

        records.reverse()
        return tuple(records)


def _commit_from_record(record: LocalCommitRecord) -> ObjectInstanceGraphCommit:
    payload_json = record.payload_json
    if not payload_json.strip():
        raise ValueError("Stored local commit payload_json is missing or invalid")
    return ObjectInstanceGraphCommit.model_validate_json(payload_json)


def _record_parent_commit_id(record: LocalCommitRecord) -> str | None:
    indexed_parent_commit_id = record.parent_commit_id
    if indexed_parent_commit_id is not None and not indexed_parent_commit_id.strip():
        indexed_parent_commit_id = None

    commit = _commit_from_record(record)
    parent_links = commit.commit.commit_parents
    if len(parent_links) > 1:
        raise ValueError(
            "Interface materializer only supports linear history in local lane stores: "
            + f"commit_id={commit.commit.id} parents={len(parent_links)}"
        )

    payload_parent_commit_id = None
    if parent_links:
        payload_parent_commit_id = str(parent_links[0].parent_commit_id)

    if (
        indexed_parent_commit_id is not None
        and payload_parent_commit_id is not None
        and indexed_parent_commit_id != payload_parent_commit_id
    ):
        raise ValueError(
            "Interface materializer detected parent commit mismatch between local index and payload: "
            + f"commit_id={commit.commit.id} indexed_parent_commit_id={indexed_parent_commit_id} "
            + f"payload_parent_commit_id={payload_parent_commit_id}"
        )

    return indexed_parent_commit_id or payload_parent_commit_id


def _snapshot_from_record(record: LocalSnapshotRecord) -> tuple[ObjectInstanceGraph, JsonObject]:
    graph = ObjectInstanceGraph.model_validate_json(record.oig_json)
    indexes = _json_object(record.indexes_json, label="snapshot indexes_json")
    return graph, indexes


def _json_object(raw: str, *, label: str) -> JsonObject:
    data = cast(object, json.loads(raw))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid {label}: expected JSON object")
    return cast(JsonObject, data)


def _build_rooted_base_from_commit(
    *,
    commit: ObjectInstanceGraphCommit,
    ocg: ObjectConfigGraph,
    opg: ObjectProjectionGraph,
) -> ObjectInstanceGraph:
    return build_rooted_object_instance_graph_base(
        key=commit.object_instance_graph_key,
        name=commit.object_instance_graph_name,
        description=commit.object_instance_graph_description or "",
        object_config_graph=ocg,
        object_projection_graph=opg,
        root_source_object_id=commit.root_source_object_id,
        root_class_config_id=commit.root_class_config_id,
        oig_id=commit.object_instance_graph_id,
    )


def _indexes_from_graph(graph: ObjectInstanceGraph) -> JsonObject:
    instance_map: dict[str, str] = {}
    classcfg_map: dict[str, str] = {}
    for class_instance in graph.class_instances:
        instance_map[str(class_instance.id)] = str(class_instance.id)
        classcfg_map[str(class_instance.id)] = str(class_instance.class_config_id)
    return {
        "instance_map": instance_map,
        "classcfg_map": classcfg_map,
    }


def _normalize_graph_root_class_instance(graph: ObjectInstanceGraph) -> None:
    root_class_instance_id = graph.root_class_instance_id
    if root_class_instance_id is None:
        return
    for class_instance in graph.class_instances:
        if class_instance.id == root_class_instance_id:
            graph.root_class_instance = class_instance
            return
    raise ValueError(
        "Interface materializer graph root_class_instance_id does not resolve to a class instance: "
        + f"root_class_instance_id={root_class_instance_id}"
    )


def _attribute_configs_by_id(ocg: ObjectConfigGraph) -> dict[UUID, AttributeConfig]:
    out: dict[UUID, AttributeConfig] = {}
    for node in ocg.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
            continue
        for link in node.class_config.class_config_attribute_configs:
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
    "InterfaceCommitMaterializer",
    "InterfaceMaterializationPostHashMismatchDetails",
    "InterfaceMaterializationPostHashMismatchError",
    "InterfaceMaterializedLane",
]
