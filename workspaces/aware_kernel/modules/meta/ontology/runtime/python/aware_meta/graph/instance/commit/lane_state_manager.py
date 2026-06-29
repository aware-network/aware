from __future__ import annotations

from dataclasses import dataclass
from typing import cast
from uuid import UUID
import asyncio

# Kernel Graph Ontology
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.instance.object_instance_graph_branch import (
    ObjectInstanceGraphBranch,
)
from aware_meta_ontology.graph.instance.object_instance_graph_lane import (
    ObjectInstanceGraphLane,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)

from aware_history_ontology.lane.lane import Lane

# Meta Runtime
from aware_meta.graph.instance.apply import apply_object_instance_graph_changes
from aware_meta.graph.instance.commit.hash_contract import compute_oig_lane_hash_state
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.instance.commit.fs_store import FSCommitStore, FSSnapshotStore
from aware_meta.graph.instance.commit.validator import (
    OigCommitValidationError,
    validate_object_instance_graph_commit,
)

from aware_orm.session.autobind import disable_autobind

from aware_utils.logging import logger


LaneKey = tuple[UUID, str]  # (branch_id, projection_hash)


@dataclass(frozen=True)
class LaneState:
    branch: ObjectInstanceGraphBranch
    lane: ObjectInstanceGraphLane
    projection_hash: str
    oig: ObjectInstanceGraph
    head_commit_id: UUID | None
    commit_count: int


class OIGLaneStateManager:
    """Lane-isolated OIG state cache.

    Keyed by (branch_id, projection_hash) to keep multiple projection lanes independent on the same branch.
    """

    def __init__(
        self,
        *,
        commits: FSCommitStore | None = None,
        snaps: FSSnapshotStore | None = None,
        materializer: OIGMaterializer | None = None,
        snapshot_every: int = 20,
    ) -> None:
        self._commits = commits or FSCommitStore()
        self._snaps = snaps or FSSnapshotStore()
        self._mat = materializer or OIGMaterializer(self._commits, self._snaps)
        self._snapshot_every = snapshot_every

        self._lanes: dict[LaneKey, LaneState] = {}
        self._instance_index: dict[LaneKey, dict[UUID, UUID]] = {}
        self._classcfg_index: dict[LaneKey, dict[UUID, UUID]] = {}
        self._locks: dict[LaneKey, asyncio.Lock] = {}

    def _lock_for(self, key: LaneKey) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    def _lane_branch_id(self, branch: ObjectInstanceGraphBranch) -> UUID:
        if branch.branch_id is not None:
            return branch.branch_id
        if getattr(branch, "branch", None) is not None and getattr(branch.branch, "id", None) is not None:
            return branch.branch.id
        raise ValueError("ObjectInstanceGraphBranch missing branch_id and branch.id")

    def _resolve_or_create_lane(
        self, *, branch: ObjectInstanceGraphBranch, projection_hash: str
    ) -> ObjectInstanceGraphLane:
        """Resolve (or create) the canonical ObjectInstanceGraphLane for this branch+hash.

        SSOT for lane identity is the ORM graph object `ObjectInstanceGraphLane` and its
        `Lane(lane_hash=projection_hash)` relationship.

        This method is intentionally DB-free (pure in-memory). Persistence is a runtime concern.
        """
        for lane_binding in branch.object_instance_graph_lanes:
            if lane_binding.lane.lane_hash == projection_hash:
                return lane_binding

        branch_id = self._lane_branch_id(branch)
        with disable_autobind():
            lane = Lane(branch_id=branch_id, lane_hash=projection_hash)
            oig_lane = ObjectInstanceGraphLane(
                object_instance_graph_branch_id=branch.id,
                lane=lane,
                lane_id=lane.id,
            )
        branch.object_instance_graph_lanes.append(oig_lane)
        return oig_lane

    def _indexes_from_graph(self, graph: ObjectInstanceGraph) -> dict[str, dict[str, str]]:
        # Keep legacy index keys, but for canonical ClassInstance ids the mapping is identity.
        inst_map: dict[str, str] = {}
        classcfg_map: dict[str, str] = {}
        for ci in graph.class_instances:
            if ci.id is None or ci.class_config_id is None:
                continue
            inst_map[str(ci.id)] = str(ci.id)
            classcfg_map[str(ci.id)] = str(ci.class_config_id)
        return {"instance_map": inst_map, "classcfg_map": classcfg_map}

    async def ensure_loaded(
        self,
        *,
        branch: ObjectInstanceGraphBranch,
        ocg: ObjectConfigGraph,
        opg: ObjectProjectionGraph,
        commit_id: UUID | None = None,
    ) -> LaneState:
        """Ensure lane cache is materialized up to commit_id (or HEAD if None)."""
        projection_hash = opg.projection_hash
        lane_branch_id = self._lane_branch_id(branch)
        key = (lane_branch_id, projection_hash)
        async with self._lock_for(key):
            oig_lane = self._resolve_or_create_lane(branch=branch, projection_hash=projection_hash)

            head_meta = await self._commits.head(branch_id=lane_branch_id, projection_hash=projection_hash)
            head_id = UUID(str(head_meta["commit_id"])) if head_meta and head_meta.get("commit_id") else None
            head_oig_id = head_meta.get("object_instance_graph_id") if head_meta else None

            # Keep the canonical history Lane head pointer aligned with the lane store.
            # This is a view today (FS is durability boundary), but becomes SSOT once DB persistence lands.
            oig_lane.lane.head_commit_id = head_id
            oig_lane.lane.head_commit = None
            if head_id is not None:
                try:
                    head_commit = await self._commits.get_commit(
                        branch_id=lane_branch_id,
                        projection_hash=projection_hash,
                        commit_id=head_id,
                    )
                    if head_commit is not None:
                        oig_lane.lane.head_commit = head_commit.commit
                except Exception:
                    pass

            st = self._lanes.get(key)
            target_id = commit_id or head_id
            if st and st.head_commit_id == target_id:
                return st

            oig, idx = await self._mat.get(
                branch_id=lane_branch_id,
                ocg=ocg,
                opg=opg,
                commit_id=commit_id,
                oig_id=UUID(str(head_oig_id)) if head_oig_id else None,
            )
            inst_map = {UUID(k): UUID(v) for k, v in (idx.get("instance_map") or {}).items()}
            cc_map = {UUID(k): UUID(v) for k, v in (idx.get("classcfg_map") or {}).items()}
            self._instance_index[key] = inst_map
            self._classcfg_index[key] = cc_map

            try:
                commit_count = len(list((self._commits._commits_dir(lane_branch_id, projection_hash)).glob("*.json")))
            except Exception:
                commit_count = 0

            st = LaneState(
                branch=branch,
                lane=oig_lane,
                projection_hash=projection_hash,
                oig=oig,
                head_commit_id=target_id,
                commit_count=commit_count,
            )
            self._lanes[key] = st
            return st

    def get_oig(self, *, branch_id: UUID, projection_hash: str) -> ObjectInstanceGraph:
        return self._lanes[(branch_id, projection_hash)].oig

    def resolve_object_instance_id(self, *, branch_id: UUID, projection_hash: str, instance_id: UUID) -> UUID:
        idx = self._instance_index.get((branch_id, projection_hash), {})
        if instance_id not in idx:
            raise KeyError(f"instance_id {instance_id} not present in lane {(branch_id, projection_hash)}")
        return idx[instance_id]

    def resolve_class_config_id(self, *, branch_id: UUID, projection_hash: str, instance_id: UUID) -> UUID:
        idx = self._classcfg_index.get((branch_id, projection_hash), {})
        if instance_id not in idx:
            raise KeyError(f"class_config_id for {instance_id} not present in lane {(branch_id, projection_hash)}")
        return idx[instance_id]

    async def on_commit_appended(
        self,
        *,
        branch: ObjectInstanceGraphBranch,
        ocg: ObjectConfigGraph,
        opg: ObjectProjectionGraph,
        commit: ObjectInstanceGraphCommit,
    ) -> LaneState:
        """Refresh lane to the appended commit.

        Fast path: apply the appended commit changes directly to the cached OIG when the
        lane is currently at the commit's parent and the pre-hash matches.
        """
        projection_hash = opg.projection_hash
        lane_branch_id = self._lane_branch_id(branch)
        key = (lane_branch_id, projection_hash)
        async with self._lock_for(key):
            oig_lane = self._resolve_or_create_lane(branch=branch, projection_hash=projection_hash)

            head_meta = await self._commits.head(branch_id=lane_branch_id, projection_hash=projection_hash)
            if not head_meta or head_meta.get("commit_id") != str(commit.commit.id):
                raise ValueError("on_commit_appended: HEAD not updated to appended commit")
            head_oig_id = head_meta.get("object_instance_graph_id")
            if head_oig_id and str(head_oig_id) != str(commit.object_instance_graph_id):
                raise ValueError(
                    "on_commit_appended: lane OIG id mismatch: "
                    f"branch_id={lane_branch_id} projection_hash={projection_hash} "
                    + f"head_object_instance_graph_id={head_oig_id} "
                    + f"expected_object_instance_graph_id={commit.object_instance_graph_id}"
                )

            oig_lane.lane.head_commit_id = commit.commit.id
            oig_lane.lane.head_commit = commit.commit

            prev = self._lanes.get(key)
            parent_commit_id: UUID | None = None
            if commit.commit.commit_parents:
                if len(commit.commit.commit_parents) > 1:
                    raise ValueError("on_commit_appended: non-linear commit has >1 parent")
                parent_commit_id = commit.commit.commit_parents[0].parent_commit_id

            def _attribute_configs_by_id() -> dict[UUID, AttributeConfig]:
                out: dict[UUID, AttributeConfig] = {}
                for node in ocg.object_config_graph_nodes:
                    if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
                        continue
                    for link in node.class_config.class_config_attribute_configs:
                        if link.attribute_config is None:
                            continue
                        out[link.attribute_config.id] = link.attribute_config
                return out

            # Fast-path: apply changes directly to the cached lane state.
            if prev is not None:
                if prev.oig.id != commit.object_instance_graph_id:
                    raise ValueError(
                        "on_commit_appended: cached OIG id mismatch: "
                        f"lane_oig_id={prev.oig.id} commit_object_instance_graph_id={commit.object_instance_graph_id}"
                    )
                pre_hash_state = compute_oig_lane_hash_state(
                    graph=prev.oig,
                    schema_attribute_configs_by_id=_attribute_configs_by_id(),
                    expected_hash=commit.graph_hash_pre or "",
                )
                if prev.head_commit_id == parent_commit_id and pre_hash_state.matches(
                    commit.graph_hash_pre or ""
                ):
                    try:
                        validate_object_instance_graph_commit(
                            commit=commit,
                            expected_object_instance_graph_identity_id=branch.object_instance_graph_identity_id,
                            expected_object_instance_graph_id=prev.oig.id,
                            expected_projection_hash=projection_hash,
                            require_linear_history=True,
                        )
                    except OigCommitValidationError as e:
                        raise ValueError(f"on_commit_appended: invalid commit payload: {e}") from e

                    apply_object_instance_graph_changes(
                        graph=prev.oig,
                        changes=commit.object_instance_graph_changes,
                        attribute_configs_by_id=_attribute_configs_by_id(),
                    )
                    post_hash_state = compute_oig_lane_hash_state(
                        graph=prev.oig,
                        schema_attribute_configs_by_id=_attribute_configs_by_id(),
                        expected_hash=commit.graph_hash_post or "",
                    )
                    prev.oig.hash = post_hash_state.matched_hash_or_default(commit.graph_hash_post or "")
                    if not post_hash_state.matches(commit.graph_hash_post or ""):
                        raise ValueError(
                            "on_commit_appended: post-hash mismatch after apply: "
                            + f"have={post_hash_state.lane_hash} raw_have={post_hash_state.raw_hash} "
                            + f"expected={commit.graph_hash_post} commit_id={commit.commit.id}"
                        )

                    idx = self._indexes_from_graph(prev.oig)
                    self._instance_index[key] = {UUID(k): UUID(v) for k, v in (idx.get("instance_map") or {}).items()}
                    self._classcfg_index[key] = {UUID(k): UUID(v) for k, v in (idx.get("classcfg_map") or {}).items()}

                    commit_count = prev.commit_count + 1
                    st = LaneState(
                        branch=branch,
                        lane=oig_lane,
                        projection_hash=projection_hash,
                        oig=prev.oig,
                        head_commit_id=commit.commit.id,
                        commit_count=commit_count,
                    )
                    self._lanes[key] = st

                    if self._snapshot_every and (commit_count % self._snapshot_every == 0):
                        try:
                            await self._snaps.put(
                                branch_id=lane_branch_id,
                                projection_hash=projection_hash,
                                commit_id=commit.commit.id,
                                oig=prev.oig,
                                indexes=cast(dict[str, object], idx),
                            )
                        except Exception as e:
                            logger.debug(f"snapshot skipped: {e}")

                    return st

            # Fallback: full rematerialization to the new head commit.
            oig, idx = await self._mat.get(
                branch_id=lane_branch_id,
                ocg=ocg,
                opg=opg,
                commit_id=commit.commit.id,
                oig_id=UUID(str(head_oig_id)) if head_oig_id else None,
            )
            self._instance_index[key] = {UUID(k): UUID(v) for k, v in (idx.get("instance_map") or {}).items()}
            self._classcfg_index[key] = {UUID(k): UUID(v) for k, v in (idx.get("classcfg_map") or {}).items()}

            if prev is not None:
                commit_count = prev.commit_count + 1
            else:
                try:
                    commit_count = len(
                        list((self._commits._commits_dir(lane_branch_id, projection_hash)).glob("*.json"))
                    )
                except Exception:
                    commit_count = 1
            st = LaneState(
                branch=branch,
                lane=oig_lane,
                projection_hash=projection_hash,
                oig=oig,
                head_commit_id=commit.commit.id,
                commit_count=commit_count,
            )
            self._lanes[key] = st

            if self._snapshot_every and (commit_count % self._snapshot_every == 0):
                try:
                    await self._snaps.put(
                        branch_id=lane_branch_id,
                        projection_hash=projection_hash,
                        commit_id=commit.commit.id,
                        oig=oig,
                        indexes=idx,
                    )
                except Exception as e:
                    logger.debug(f"snapshot skipped: {e}")

            return st

    async def invalidate_lane(self, *, branch_id: UUID, projection_hash: str) -> None:
        key = (branch_id, projection_hash)
        async with self._lock_for(key):
            self._lanes.pop(key, None)
            self._instance_index.pop(key, None)
            self._classcfg_index.pop(key, None)


oig_lane_state_manager = OIGLaneStateManager()
