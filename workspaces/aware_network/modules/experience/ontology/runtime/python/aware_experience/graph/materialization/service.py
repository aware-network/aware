from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
import shutil
from time import perf_counter
from typing import Any, ClassVar, Protocol, cast
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    StrictBool,
    StrictStr,
    ValidationError,
    field_validator,
)

from aware_experience import stable_ids as experience_stable_ids
from aware_experience.compiler.models import ExperienceProjectionExperienceOwnership
from aware_experience.graph.ontology import (
    ExperienceGraphOntologyPlan,
    decode_graph_ontology_plan_payload,
)
from aware_experience.materialization.snapshot_commit import (
    ExperienceGraphIdentityEdgeSnapshot,
    ExperienceGraphIdentitySnapshot,
    ExperienceNodeIdentityEdgeSnapshot,
    ExperienceProjectionNodeSnapshot,
    commit_projection_experience_graph_snapshot,
    commit_projection_experience_snapshot,
)
from aware_experience.materialization.projection_snapshot_preservation import (
    merge_projection_node_snapshots,
    preserve_projection_branch_snapshots_from_session,
    preserve_projection_node_snapshots_from_session,
    preserve_projection_oigi_snapshots_from_session,
    preserve_projection_view_snapshots_from_session,
)
from aware_experience.materialization.branches import (
    derive_experience_reference_branch_id,
)
from aware_experience.materialization.projection_resolution import (
    ProjectionRuntimeResolver,
    build_projection_runtime_resolver,
)
from aware_experience.projection.contracts import (
    decode_projection_experience_ownership_payload,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)

from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    get_shared_materialization_cache,
)
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.instance.validator_opg import (
    validate_object_instance_graph_against_opg,
)
from aware_meta.materialization import (
    MaterializationExecutor,
    MaterializationLaneContext,
    MaterializationPlan,
    MaterializationRunReceipt,
    MaterializationStep,
    MaterializationStepResult,
)
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_meta.runtime.projection_support import build_meta_graph_opgi_index
from aware_orm.session.session import Session
from aware_utils.logging import logger


class _RuntimeProtocol(Protocol):
    @property
    def invoker(self) -> object: ...


def _round_duration_s(duration_s: float) -> float:
    return round(max(duration_s, 0.0), 6)


@contextmanager
def _record_optional_phase(
    phase_timings_s: dict[str, float] | None,
    phase_name: str,
) -> Iterator[None]:
    if phase_timings_s is None:
        yield
        return
    started_at = perf_counter()
    logger.info("Experience graph materialization phase started: %s", phase_name)
    try:
        yield
    finally:
        duration_s = _round_duration_s(perf_counter() - started_at)
        phase_timings_s[phase_name] = duration_s
        logger.info(
            "Experience graph materialization phase finished: %s (%.6fs)",
            phase_name,
            duration_s,
        )


@dataclass(frozen=True, slots=True)
class ProjectionExperienceNodeMaterializationSpec:
    name: str
    node_ref: str
    identity_keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectionExperienceGraphIdentityMaterializationSpec:
    ref: str
    key: str
    is_root: bool


@dataclass(frozen=True, slots=True)
class ProjectionExperienceNodeIdentityEdgeMaterializationSpec:
    parent_ref: str
    child_ref: str
    key: str | None


@dataclass(frozen=True, slots=True)
class ProjectionExperienceGraphIdentityEdgeMaterializationSpec:
    parent_ref: str
    child_ref: str
    key: str | None


@dataclass(frozen=True, slots=True)
class ProjectionExperienceGraphMaterializationSpec:
    experience_name: str
    projection_key: str
    graph_name: str
    nodes: tuple[ProjectionExperienceNodeMaterializationSpec, ...]
    identities: tuple[ProjectionExperienceGraphIdentityMaterializationSpec, ...]
    node_identity_edges: tuple[
        ProjectionExperienceNodeIdentityEdgeMaterializationSpec, ...
    ]
    graph_identity_edges: tuple[
        ProjectionExperienceGraphIdentityEdgeMaterializationSpec, ...
    ]
    runtime_opgi_id: UUID | None = None


class _GraphMaterializationNodePayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    name: StrictStr
    node_ref: StrictStr
    identity_keys: tuple[StrictStr, ...]

    @field_validator("name", "node_ref", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)

    @field_validator("identity_keys", mode="before")
    @classmethod
    def _validate_identity_keys(cls, value: object) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            raise ValueError("identity_keys must be a list")
        value_items = cast(Sequence[object], value)
        normalized_keys = tuple(
            _required_step_payload_token(item) for item in value_items
        )
        if not normalized_keys:
            raise ValueError("identity_keys requires at least one entry")
        return normalized_keys


class _GraphMaterializationIdentityPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    ref: StrictStr
    key: StrictStr
    is_root: StrictBool = False

    @field_validator("ref", "key", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)


class _GraphMaterializationEdgePayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    parent_ref: StrictStr
    child_ref: StrictStr
    key: StrictStr | None = None

    @field_validator("parent_ref", "child_ref", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)

    @field_validator("key", mode="before")
    @classmethod
    def _validate_optional_token(cls, value: object) -> str | None:
        return _optional_step_payload_token(value)


class _GraphMaterializationStepPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    experience_name: StrictStr
    projection_key: StrictStr
    runtime_opgi_id: UUID | None = None
    graph_name: StrictStr
    nodes: tuple[_GraphMaterializationNodePayload, ...] = ()
    identities: tuple[_GraphMaterializationIdentityPayload, ...] = ()
    node_identity_edges: tuple[_GraphMaterializationEdgePayload, ...] = ()
    graph_identity_edges: tuple[_GraphMaterializationEdgePayload, ...] = ()

    @field_validator("experience_name", "projection_key", "graph_name", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)


async def materialize_experience_graph_ontology(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    phase_timings_s: dict[str, float] | None = None,
    allow_unresolved_projection_experiences: bool = False,
) -> MaterializationRunReceipt | None:
    with _record_optional_phase(
        phase_timings_s,
        "experience_graph.resolve_graph_materialization_specs",
    ):
        specs = resolve_graph_materialization_specs(
            compile_plan_payloads=compile_plan_payloads,
            index=index,
            allow_unresolved_projection_experiences=(
                allow_unresolved_projection_experiences
            ),
        )
    if not specs:
        return None

    with _record_optional_phase(
        phase_timings_s,
        "experience_graph.resolve_projection_hashes_and_plan",
    ):
        projection_experience_projection_hash = _find_projection_hash_by_name(
            index=index,
            projection_name="ProjectionExperience",
        )
        projection_experience_oigi_projection_hash = _find_projection_hash_by_name(
            index=index,
            projection_name="ProjectionExperienceOIGI",
        )
        projection_experience_graph_projection_hash = _find_projection_hash_by_name(
            index=index,
            projection_name="ProjectionExperienceGraph",
        )
        projection_lane = MaterializationLaneContext(
            branch_id=lane.branch_id,
            projection_hash=projection_experience_projection_hash,
        )
        graph_lane = MaterializationLaneContext(
            branch_id=lane.branch_id,
            projection_hash=projection_experience_graph_projection_hash,
        )
        plan = build_graph_materialization_plan(lane=graph_lane, specs=specs)
    with _record_optional_phase(phase_timings_s, "experience_graph.build_opgi_index"):
        opgi_by_key = build_meta_graph_opgi_index(index=index)
        opgi_by_key_casefolded = {
            (key or "").strip().casefold(): opgi_entry
            for key, opgi_entry in opgi_by_key.items()
            if (key or "").strip()
        }

    with _record_optional_phase(
        phase_timings_s, "experience_graph.build_class_catalog"
    ):
        class_catalog = _build_class_catalog(index=index)
    with _record_optional_phase(
        phase_timings_s, "experience_graph.build_relationship_targets_by_source_class"
    ):
        relationship_targets_by_source_class = (
            _build_relationship_targets_by_source_class(class_catalog=class_catalog)
        )
    opg_by_opgi_id: dict[UUID, ObjectProjectionGraph] = {}
    node_id_cache: dict[tuple[UUID, str], UUID] = {}

    async def _runner(
        *, plan: MaterializationPlan, step: MaterializationStep
    ) -> MaterializationStepResult:
        with _record_optional_phase(
            phase_timings_s,
            f"experience_graph.runner:{step.step_id}.decode_step_payload",
        ):
            spec = decode_graph_materialization_step_payload(step.payload)
            experience_branch_id = derive_experience_reference_branch_id(
                base_branch_id=plan.lane.branch_id,
                experience_name=spec.experience_name,
            )
            projection_step_lane = MaterializationLaneContext(
                branch_id=experience_branch_id,
                projection_hash=projection_lane.projection_hash,
            )
            graph_step_lane = MaterializationLaneContext(
                branch_id=experience_branch_id,
                projection_hash=graph_lane.projection_hash,
            )

        with _record_optional_phase(
            phase_timings_s,
            f"experience_graph.runner:{step.step_id}.reset_stale_generated_lanes_if_needed",
        ):
            stale_projection_lane_reset = False
            stale_graph_lane_reset = (
                await _reset_stale_generated_projection_lane_if_needed(
                    index=index,
                    branch_id=graph_step_lane.branch_id,
                    projection_hash=graph_step_lane.projection_hash,
                    error_context="Experience graph materialization graph lane",
                )
            )

        with _record_optional_phase(
            phase_timings_s,
            f"experience_graph.runner:{step.step_id}.resolve_projection_opgi",
        ):
            opgi_entry = _resolve_projection_opgi_entry(
                opgi_by_key_casefolded=opgi_by_key_casefolded,
                projection_key=spec.projection_key,
                experience_name=spec.experience_name,
                graph_name=spec.graph_name,
                runtime_opgi_id=spec.runtime_opgi_id,
            )
            projection_opgi_id = opgi_entry[0]

        with _record_optional_phase(
            phase_timings_s,
            f"experience_graph.runner:{step.step_id}.find_projection_graph",
        ):
            opg = opg_by_opgi_id.get(projection_opgi_id)
            if opg is None:
                opg = _find_projection_graph_by_opgi_id(
                    index=index,
                    object_projection_graph_identity_id=projection_opgi_id,
                )
                opg_by_opgi_id[projection_opgi_id] = opg

        node_identity_id_by_ref: dict[str, UUID] = {}
        graph_identity_id_by_ref: dict[str, UUID] = {}
        node_identity_edge_id_by_ref: dict[tuple[str, str], UUID] = {}
        projection_experience_id = (
            experience_stable_ids.stable_projection_experience_id(
                object_projection_graph_identity_id=projection_opgi_id,
                name=spec.experience_name,
            )
        )

        with _record_optional_phase(
            phase_timings_s,
            f"experience_graph.runner:{step.step_id}.load_projection_lane_head",
        ):
            projection_lane_head = await FSCommitStore().head(
                branch_id=projection_step_lane.branch_id,
                projection_hash=projection_step_lane.projection_hash,
            )
        projection_lane_reused = (
            projection_lane_head is not None
            and projection_lane_head.get("commit_id") is not None
        )
        preserved_projection_branches = ()
        preserved_projection_views = ()
        preserved_projection_nodes = ()
        preserved_projection_oigis = ()
        if projection_lane_reused:
            with _record_optional_phase(
                phase_timings_s,
                f"experience_graph.runner:{step.step_id}.preserve_projection_snapshot_catalog",
            ):
                projection_session = await _hydrate_lane_session(
                    index=index,
                    branch_id=projection_step_lane.branch_id,
                    projection_hash=projection_step_lane.projection_hash,
                    error_context=("Experience graph materialization projection lane"),
                )
                preserved_projection_branches = (
                    preserve_projection_branch_snapshots_from_session(
                        projection_session=projection_session,
                        projection_experience_id=projection_experience_id,
                    )
                )
                preserved_projection_views = (
                    preserve_projection_view_snapshots_from_session(
                        projection_session=projection_session,
                        projection_experience_id=projection_experience_id,
                    )
                )
                preserved_projection_nodes = (
                    preserve_projection_node_snapshots_from_session(
                        projection_session=projection_session,
                        projection_experience_id=projection_experience_id,
                    )
                )
                preserved_projection_oigis = (
                    preserve_projection_oigi_snapshots_from_session(
                        projection_session=projection_session,
                        projection_experience_id=projection_experience_id,
                    )
                )
        with _record_optional_phase(
            phase_timings_s,
            f"experience_graph.runner:{step.step_id}.build_projection_node_snapshots",
        ):
            projection_node_snapshots: list[ExperienceProjectionNodeSnapshot] = []
            for node_spec in spec.nodes:
                cache_key = (projection_opgi_id, node_spec.node_ref.casefold())
                object_projection_graph_node_id = node_id_cache.get(cache_key)
                if object_projection_graph_node_id is None:
                    object_projection_graph_node_id = (
                        resolve_projection_node_id_for_node_ref(
                            opg=opg,
                            class_catalog=class_catalog,
                            relationship_targets_by_source_class=(
                                relationship_targets_by_source_class
                            ),
                            node_ref=node_spec.node_ref,
                            experience_name=spec.experience_name,
                        )
                    )
                    node_id_cache[cache_key] = object_projection_graph_node_id

                projection_node_snapshots.append(
                    ExperienceProjectionNodeSnapshot(
                        object_projection_graph_node_id=(
                            object_projection_graph_node_id
                        ),
                        key=node_spec.name,
                        identity_keys=node_spec.identity_keys,
                    )
                )
                projection_experience_node_id = (
                    experience_stable_ids.stable_projection_experience_node_id(
                        projection_experience_id=projection_experience_id,
                        object_projection_graph_node_id=(
                            object_projection_graph_node_id
                        ),
                        key=node_spec.name,
                    )
                )
                for identity_key in node_spec.identity_keys:
                    if identity_key in node_identity_id_by_ref:
                        raise RuntimeError(
                            "Graph materialization requires projection node identities "
                            + "to be unique by bare identity ref within one experience "
                            + f"(identity={identity_key!r})"
                        )
                    node_identity_id_by_ref[identity_key] = (
                        experience_stable_ids.stable_projection_experience_node_identity_id(
                            projection_experience_node_id=projection_experience_node_id,
                            key=identity_key,
                        )
                    )
        with _record_optional_phase(
            phase_timings_s,
            f"experience_graph.runner:{step.step_id}.commit_projection_node_snapshot",
        ):
            projection_snapshot = await commit_projection_experience_snapshot(
                index=index,
                actor_id=actor_id,
                branch_id=projection_step_lane.branch_id,
                projection_hash=projection_step_lane.projection_hash,
                projection_oigi_hash=projection_experience_oigi_projection_hash,
                object_projection_graph_identity_id=projection_opgi_id,
                name=spec.experience_name,
                branches=preserved_projection_branches,
                views=preserved_projection_views,
                nodes=merge_projection_node_snapshots(
                    preserved_projection_nodes,
                    tuple(projection_node_snapshots),
                ),
                oigis=preserved_projection_oigis,
            )

        with _record_optional_phase(
            phase_timings_s,
            f"experience_graph.runner:{step.step_id}.load_graph_lane_head",
        ):
            graph_lane_head = await FSCommitStore().head(
                branch_id=graph_step_lane.branch_id,
                projection_hash=graph_step_lane.projection_hash,
            )
        graph_lane_reused = (
            graph_lane_head is not None and graph_lane_head.get("commit_id") is not None
        )
        projection_experience_graph_id = (
            experience_stable_ids.stable_projection_experience_graph_id(
                projection_experience_id=projection_experience_id,
                name=spec.graph_name,
            )
        )
        with _record_optional_phase(
            phase_timings_s,
            f"experience_graph.runner:{step.step_id}.build_graph_snapshots",
        ):
            graph_identity_snapshots: list[ExperienceGraphIdentitySnapshot] = []
            for identity_spec in spec.identities:
                projection_experience_node_identity_id = node_identity_id_by_ref.get(
                    identity_spec.ref
                )
                if projection_experience_node_identity_id is None:
                    raise RuntimeError(
                        "Graph materialization requires known projection node identity ref "
                        + f"{identity_spec.ref!r} in experience={spec.experience_name!r} "
                        + f"graph={spec.graph_name!r}"
                    )
                graph_identity_snapshots.append(
                    ExperienceGraphIdentitySnapshot(
                        projection_experience_node_identity_id=(
                            projection_experience_node_identity_id
                        ),
                        key=identity_spec.key,
                        is_root=identity_spec.is_root,
                    )
                )
                graph_identity_id_by_ref[identity_spec.ref] = (
                    experience_stable_ids.stable_projection_experience_graph_identity_id(
                        projection_experience_graph_id=(projection_experience_graph_id),
                        projection_experience_node_identity_id=(
                            projection_experience_node_identity_id
                        ),
                        key=identity_spec.key,
                    )
                )

            node_identity_edge_snapshots: list[ExperienceNodeIdentityEdgeSnapshot] = []
            for node_edge_spec in spec.node_identity_edges:
                parent_node_identity_id = node_identity_id_by_ref.get(
                    node_edge_spec.parent_ref
                )
                if parent_node_identity_id is None:
                    raise RuntimeError(
                        "Graph materialization requires known parent node identity ref "
                        + f"{node_edge_spec.parent_ref!r} in graph={spec.graph_name!r}"
                    )
                child_node_identity_id = node_identity_id_by_ref.get(
                    node_edge_spec.child_ref
                )
                if child_node_identity_id is None:
                    raise RuntimeError(
                        "Graph materialization requires known child node identity ref "
                        + f"{node_edge_spec.child_ref!r} in graph={spec.graph_name!r}"
                    )
                node_identity_edge_snapshots.append(
                    ExperienceNodeIdentityEdgeSnapshot(
                        parent_projection_experience_node_identity_id=(
                            parent_node_identity_id
                        ),
                        child_projection_experience_node_identity_id=(
                            child_node_identity_id
                        ),
                        key=node_edge_spec.key,
                    )
                )
                node_identity_edge_id_by_ref[
                    (node_edge_spec.parent_ref, node_edge_spec.child_ref)
                ] = experience_stable_ids.stable_projection_experience_node_identity_edge_id(
                    projection_experience_graph_id=(projection_experience_graph_id),
                    child_projection_experience_node_identity_id=(
                        child_node_identity_id
                    ),
                    parent_projection_experience_node_identity_id=(
                        parent_node_identity_id
                    ),
                )

            graph_identity_edge_snapshots: list[ExperienceGraphIdentityEdgeSnapshot] = (
                []
            )
            for graph_edge_spec in spec.graph_identity_edges:
                parent_graph_identity_id = graph_identity_id_by_ref.get(
                    graph_edge_spec.parent_ref
                )
                if parent_graph_identity_id is None:
                    raise RuntimeError(
                        "Graph materialization requires known parent graph identity ref "
                        + f"{graph_edge_spec.parent_ref!r} in graph={spec.graph_name!r}"
                    )
                child_graph_identity_id = graph_identity_id_by_ref.get(
                    graph_edge_spec.child_ref
                )
                if child_graph_identity_id is None:
                    raise RuntimeError(
                        "Graph materialization requires known child graph identity ref "
                        + f"{graph_edge_spec.child_ref!r} in graph={spec.graph_name!r}"
                    )
                node_identity_edge_id = node_identity_edge_id_by_ref.get(
                    (graph_edge_spec.parent_ref, graph_edge_spec.child_ref)
                )
                if node_identity_edge_id is None:
                    raise RuntimeError(
                        "Graph materialization requires matching node identity edge for graph edge "
                        + f"{graph_edge_spec.parent_ref!r}->{graph_edge_spec.child_ref!r}"
                    )
                graph_identity_edge_snapshots.append(
                    ExperienceGraphIdentityEdgeSnapshot(
                        parent_projection_experience_graph_identity_id=(
                            parent_graph_identity_id
                        ),
                        child_projection_experience_graph_identity_id=(
                            child_graph_identity_id
                        ),
                        projection_experience_node_identity_edge_id=(
                            node_identity_edge_id
                        ),
                        key=graph_edge_spec.key,
                    )
                )
        with _record_optional_phase(
            phase_timings_s,
            f"experience_graph.runner:{step.step_id}.commit_graph_snapshot",
        ):
            graph_snapshot = await commit_projection_experience_graph_snapshot(
                index=index,
                actor_id=actor_id,
                branch_id=graph_step_lane.branch_id,
                projection_hash=graph_step_lane.projection_hash,
                projection_experience_id=projection_experience_id,
                name=spec.graph_name,
                identities=tuple(graph_identity_snapshots),
                node_identity_edges=tuple(node_identity_edge_snapshots),
                graph_identity_edges=tuple(graph_identity_edge_snapshots),
            )

        return MaterializationStepResult(
            details={
                "experience_name": spec.experience_name,
                "projection_key": spec.projection_key,
                "graph_name": spec.graph_name,
                "node_count": len(spec.nodes),
                "identity_count": len(spec.identities),
                "node_edge_count": len(spec.node_identity_edges),
                "graph_edge_count": len(spec.graph_identity_edges),
                "branch_id": str(experience_branch_id),
                "stale_projection_lane_reset": stale_projection_lane_reset,
                "stale_graph_lane_reset": stale_graph_lane_reset,
                "projection_lane_reused": projection_lane_reused,
                "graph_lane_reused": graph_lane_reused,
            },
            commit_id=graph_snapshot.commit_id or projection_snapshot.commit_id,
            head_commit_id=graph_snapshot.head_commit_id,
        )

    with _record_optional_phase(phase_timings_s, "experience_graph.executor.run"):
        return await MaterializationExecutor().run(plan=plan, runner=_runner)


def resolve_graph_materialization_specs(
    *,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    index: MetaGraphRuntimeIndex | None = None,
    allow_unresolved_projection_experiences: bool = False,
) -> tuple[ProjectionExperienceGraphMaterializationSpec, ...]:
    if not compile_plan_payloads:
        return ()

    projection_specs_by_experience = _build_projection_specs_by_experience(
        compile_plan_payloads=compile_plan_payloads,
        index=index,
        allow_unresolved_projection_experiences=(
            allow_unresolved_projection_experiences
        ),
    )
    specs_by_key: dict[
        tuple[str, str], ProjectionExperienceGraphMaterializationSpec
    ] = {}

    for graph_plan in _decode_graph_ontology_plans(
        compile_plan_payloads=compile_plan_payloads
    ):
        graph_name = graph_plan.graph.graph_name
        experience_name = graph_plan.graph.experience
        root_ref = graph_plan.graph.root_ref

        projection_spec = projection_specs_by_experience.get(experience_name.casefold())
        if projection_spec is None:
            if allow_unresolved_projection_experiences:
                continue
            raise RuntimeError(
                "Invalid experience compile plan: graph ontology experience has no projection experience ownership "
                + f"entry: experience={experience_name!r}"
            )

        nodes_by_name = {
            node_spec.name: node_spec for node_spec in projection_spec.nodes
        }
        identities = _resolve_graph_identity_specs_from_plan(
            graph_plan=graph_plan,
            nodes_by_name=nodes_by_name,
        )
        identities_by_ref = {identity.ref: identity for identity in identities}
        if root_ref not in identities_by_ref:
            raise RuntimeError(
                "Invalid experience compile plan: graph root ref is missing from graph identities "
                + f"(graph={graph_name!r}, root_ref={root_ref!r})"
            )

        roots = tuple(identity for identity in identities if identity.is_root)
        if len(roots) != 1:
            raise RuntimeError(
                "Invalid experience compile plan: graph identities require exactly one root entry "
                + f"(graph={graph_name!r}, roots={len(roots)})"
            )
        if roots[0].ref != root_ref:
            raise RuntimeError(
                "Invalid experience compile plan: graph root ref must match root identity entry "
                + f"(graph={graph_name!r}, root_ref={root_ref!r}, root_identity_ref={roots[0].ref!r})"
            )

        node_identity_edges = _resolve_node_identity_edge_specs_from_plan(
            graph_plan=graph_plan,
            identity_refs=frozenset(identities_by_ref),
        )
        graph_identity_edges = _resolve_graph_identity_edge_specs_from_plan(
            graph_plan=graph_plan,
            identity_refs=frozenset(identities_by_ref),
        )

        spec = ProjectionExperienceGraphMaterializationSpec(
            experience_name=projection_spec.experience_name,
            projection_key=projection_spec.projection_key,
            runtime_opgi_id=projection_spec.runtime_opgi_id,
            graph_name=graph_name,
            nodes=projection_spec.nodes,
            identities=identities,
            node_identity_edges=node_identity_edges,
            graph_identity_edges=graph_identity_edges,
        )
        spec_key = (spec.experience_name.casefold(), spec.graph_name.casefold())
        existing = specs_by_key.get(spec_key)
        if existing is not None and existing != spec:
            raise RuntimeError(
                "Invalid experience compile plan: duplicate graph ontology entries disagree "
                + f"for experience={spec.experience_name!r} graph={spec.graph_name!r}"
            )
        specs_by_key[spec_key] = spec

    return tuple(
        sorted(
            specs_by_key.values(),
            key=lambda item: (
                item.experience_name.casefold(),
                item.graph_name.casefold(),
            ),
        )
    )


def build_graph_materialization_plan(
    *,
    lane: MaterializationLaneContext,
    specs: Sequence[ProjectionExperienceGraphMaterializationSpec],
) -> MaterializationPlan:
    steps = tuple(
        MaterializationStep(
            step_id=f"graph:{spec.experience_name}:{spec.graph_name}",
            step_kind="experience.graph",
            payload=encode_graph_materialization_step_payload(spec=spec),
            commit_requested=True,
        )
        for spec in specs
    )
    return MaterializationPlan(
        module_id="experience",
        pipeline_id="experience.compile_plan.graph",
        lane=lane,
        steps=steps,
    )


@dataclass(frozen=True, slots=True)
class _ProjectionExperienceSpec:
    experience_name: str
    projection_key: str
    runtime_opgi_id: UUID | None
    nodes: tuple[ProjectionExperienceNodeMaterializationSpec, ...]


def _projection_materialization_key_for_ownership(
    *,
    ownership: ExperienceProjectionExperienceOwnership,
    resolver: ProjectionRuntimeResolver | None,
    context: str,
) -> tuple[str, UUID | None]:
    projection_key = ownership.projection.strip()
    if resolver is None:
        return (projection_key.casefold(), None)
    resolution = resolver.resolve(
        projection_key=projection_key,
        node_refs=(node.node_ref for node in ownership.nodes),
        experience_name=ownership.name,
        context=context,
    )
    return (projection_key.casefold(), resolution.opgi_id)


def _build_projection_specs_by_experience(
    *,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    index: MetaGraphRuntimeIndex | None = None,
    allow_unresolved_projection_experiences: bool = False,
) -> dict[str, _ProjectionExperienceSpec]:
    specs_by_experience: dict[str, _ProjectionExperienceSpec] = {}
    resolver = (
        build_projection_runtime_resolver(index=index) if index is not None else None
    )
    for ownership in _decode_projection_experience_ownership(
        compile_plan_payloads=compile_plan_payloads
    ):
        experience_name = ownership.name.strip()
        try:
            projection_key, runtime_opgi_id = (
                _projection_materialization_key_for_ownership(
                    ownership=ownership,
                    resolver=resolver,
                    context="Graph materialization",
                )
            )
        except RuntimeError:
            if allow_unresolved_projection_experiences:
                continue
            raise

        node_specs: list[ProjectionExperienceNodeMaterializationSpec] = []
        for node_row in ownership.nodes:
            node_name = node_row.name.strip()
            node_ref = node_row.node_ref.strip()
            if not node_name:
                raise RuntimeError(
                    "Invalid experience compile plan: projection_experience_ownership[].nodes[].name is required"
                )
            if not node_ref:
                raise RuntimeError(
                    "Invalid experience compile plan: projection_experience_ownership[].nodes[].node_ref is required"
                )

            identity_keys = tuple(
                sorted(
                    {
                        identity_row.key.strip()
                        for identity_row in node_row.identities
                        if identity_row.key.strip()
                    }
                )
            )
            if not identity_keys:
                raise RuntimeError(
                    "Invalid experience compile plan: projection_experience_ownership node requires identities "
                    + f"(experience={experience_name!r}, node={node_name!r})"
                )

            node_specs.append(
                ProjectionExperienceNodeMaterializationSpec(
                    name=node_name,
                    node_ref=node_ref,
                    identity_keys=identity_keys,
                )
            )

        spec = _ProjectionExperienceSpec(
            experience_name=experience_name,
            projection_key=projection_key,
            runtime_opgi_id=runtime_opgi_id,
            nodes=tuple(
                sorted(
                    node_specs,
                    key=lambda item: (item.name.casefold(), item.node_ref.casefold()),
                )
            ),
        )
        experience_key = experience_name.casefold()
        existing = specs_by_experience.get(experience_key)
        if existing is not None and existing != spec:
            raise RuntimeError(
                "Invalid experience compile plan: duplicate projection experience ownership entries disagree "
                + f"for experience={experience_name!r}"
            )
        specs_by_experience[experience_key] = spec
    return specs_by_experience


def _decode_projection_experience_ownership(
    *,
    compile_plan_payloads: Sequence[Mapping[str, object]],
) -> tuple[ExperienceProjectionExperienceOwnership, ...]:
    ownership_rows: list[object] = []
    for payload in compile_plan_payloads:
        ownership_rows.extend(
            _expect_list(
                payload.get("projection_experience_ownership", []),
                field_name="projection_experience_ownership",
            )
        )
    return decode_projection_experience_ownership_payload(payload=ownership_rows)


def _decode_graph_ontology_plans(
    *,
    compile_plan_payloads: Sequence[Mapping[str, object]],
) -> tuple[ExperienceGraphOntologyPlan, ...]:
    plans: list[ExperienceGraphOntologyPlan] = []
    for payload in compile_plan_payloads:
        graph_rows = _expect_list(
            payload.get("graph_ontology", []), field_name="graph_ontology"
        )
        plans.extend(decode_graph_ontology_plan_payload(payload=graph_rows))
    return tuple(plans)


def _resolve_graph_identity_specs_from_plan(
    *,
    graph_plan: ExperienceGraphOntologyPlan,
    nodes_by_name: Mapping[str, ProjectionExperienceNodeMaterializationSpec],
) -> tuple[ProjectionExperienceGraphIdentityMaterializationSpec, ...]:
    identities: list[ProjectionExperienceGraphIdentityMaterializationSpec] = []
    seen_refs: set[str] = set()
    for identity_row in graph_plan.identities:
        ref = identity_row.ref
        key = identity_row.key
        if ref in seen_refs:
            raise RuntimeError(
                "Invalid experience compile plan: duplicate graph identity ref "
                + f"{ref!r}"
            )
        seen_refs.add(ref)

        identity_key = identity_row.identity_key
        node_name = identity_row.node_name
        if ref != identity_key:
            raise RuntimeError(
                "Invalid experience compile plan: graph identity ref tuple mismatch "
                + f"(ref={ref!r}, node_name={identity_row.node_name!r}, identity_key={identity_row.identity_key!r})"
            )
        node_spec = nodes_by_name.get(node_name)
        if node_spec is None:
            raise RuntimeError(
                "Invalid experience compile plan: graph identity ref node is not declared in projection experience "
                + f"(ref={ref!r})"
            )
        if identity_key not in node_spec.identity_keys:
            raise RuntimeError(
                "Invalid experience compile plan: graph identity ref identity key is not declared on node "
                + f"(ref={ref!r}, node={node_name!r}, identity_key={identity_key!r})"
            )

        identities.append(
            ProjectionExperienceGraphIdentityMaterializationSpec(
                ref=ref,
                key=key,
                is_root=identity_row.is_root,
            )
        )

    if not identities:
        raise RuntimeError(
            "Invalid experience compile plan: graph_ontology requires at least one identity"
        )
    return tuple(identities)


def _resolve_node_identity_edge_specs_from_plan(
    *,
    graph_plan: ExperienceGraphOntologyPlan,
    identity_refs: frozenset[str],
) -> tuple[ProjectionExperienceNodeIdentityEdgeMaterializationSpec, ...]:
    edges: list[ProjectionExperienceNodeIdentityEdgeMaterializationSpec] = []
    for edge_row in graph_plan.node_identity_edges:
        parent_ref = edge_row.parent_ref
        child_ref = edge_row.child_ref
        if parent_ref not in identity_refs or child_ref not in identity_refs:
            raise RuntimeError(
                "Invalid experience compile plan: node identity edge refs must exist in graph identities "
                + f"(parent_ref={parent_ref!r}, child_ref={child_ref!r})"
            )
        key_token = _optional_key_token(edge_row.key)
        edges.append(
            ProjectionExperienceNodeIdentityEdgeMaterializationSpec(
                parent_ref=parent_ref,
                child_ref=child_ref,
                key=key_token,
            )
        )
    return tuple(edges)


def _resolve_graph_identity_edge_specs_from_plan(
    *,
    graph_plan: ExperienceGraphOntologyPlan,
    identity_refs: frozenset[str],
) -> tuple[ProjectionExperienceGraphIdentityEdgeMaterializationSpec, ...]:
    edges: list[ProjectionExperienceGraphIdentityEdgeMaterializationSpec] = []
    for edge_row in graph_plan.graph_identity_edges:
        parent_ref = edge_row.parent_ref
        child_ref = edge_row.child_ref
        if parent_ref not in identity_refs or child_ref not in identity_refs:
            raise RuntimeError(
                "Invalid experience compile plan: graph identity edge refs must exist in graph identities "
                + f"(parent_ref={parent_ref!r}, child_ref={child_ref!r})"
            )
        key_token = _optional_key_token(edge_row.key)
        edges.append(
            ProjectionExperienceGraphIdentityEdgeMaterializationSpec(
                parent_ref=parent_ref,
                child_ref=child_ref,
                key=key_token,
            )
        )
    return tuple(edges)


def encode_graph_materialization_step_payload(
    *,
    spec: ProjectionExperienceGraphMaterializationSpec,
) -> dict[str, object]:
    payload = _GraphMaterializationStepPayload(
        experience_name=spec.experience_name,
        projection_key=spec.projection_key,
        runtime_opgi_id=spec.runtime_opgi_id,
        graph_name=spec.graph_name,
        nodes=tuple(
            _GraphMaterializationNodePayload(
                name=node.name,
                node_ref=node.node_ref,
                identity_keys=node.identity_keys,
            )
            for node in spec.nodes
        ),
        identities=tuple(
            _GraphMaterializationIdentityPayload(
                ref=identity.ref,
                key=identity.key,
                is_root=identity.is_root,
            )
            for identity in spec.identities
        ),
        node_identity_edges=tuple(
            _GraphMaterializationEdgePayload(
                parent_ref=edge.parent_ref,
                child_ref=edge.child_ref,
                key=edge.key,
            )
            for edge in spec.node_identity_edges
        ),
        graph_identity_edges=tuple(
            _GraphMaterializationEdgePayload(
                parent_ref=edge.parent_ref,
                child_ref=edge.child_ref,
                key=edge.key,
            )
            for edge in spec.graph_identity_edges
        ),
    )
    return cast(dict[str, object], payload.model_dump(mode="json"))


def decode_graph_materialization_step_payload(
    payload: Mapping[str, object],
) -> ProjectionExperienceGraphMaterializationSpec:
    try:
        step_payload = _GraphMaterializationStepPayload.model_validate(payload)
    except ValidationError as exc:
        raise RuntimeError(_format_step_payload_validation_error(exc=exc)) from exc

    return ProjectionExperienceGraphMaterializationSpec(
        experience_name=step_payload.experience_name,
        projection_key=step_payload.projection_key,
        runtime_opgi_id=step_payload.runtime_opgi_id,
        graph_name=step_payload.graph_name,
        nodes=tuple(
            ProjectionExperienceNodeMaterializationSpec(
                name=node_row.name,
                node_ref=node_row.node_ref,
                identity_keys=node_row.identity_keys,
            )
            for node_row in step_payload.nodes
        ),
        identities=tuple(
            ProjectionExperienceGraphIdentityMaterializationSpec(
                ref=identity_row.ref,
                key=identity_row.key,
                is_root=identity_row.is_root,
            )
            for identity_row in step_payload.identities
        ),
        node_identity_edges=tuple(
            ProjectionExperienceNodeIdentityEdgeMaterializationSpec(
                parent_ref=edge_row.parent_ref,
                child_ref=edge_row.child_ref,
                key=edge_row.key,
            )
            for edge_row in step_payload.node_identity_edges
        ),
        graph_identity_edges=tuple(
            ProjectionExperienceGraphIdentityEdgeMaterializationSpec(
                parent_ref=edge_row.parent_ref,
                child_ref=edge_row.child_ref,
                key=edge_row.key,
            )
            for edge_row in step_payload.graph_identity_edges
        ),
    )


def resolve_projection_node_id_for_node_ref(
    *,
    opg: ObjectProjectionGraph,
    class_catalog: Mapping[UUID, ClassConfig],
    relationship_targets_by_source_class: Mapping[UUID, Mapping[str, frozenset[UUID]]],
    node_ref: str,
    experience_name: str,
) -> UUID:
    class_token, relationship_tokens = _split_node_ref(node_ref=node_ref)
    opg_nodes = tuple(opg.object_projection_graph_nodes or ())

    class_ids_in_opg = {node.class_config_id for node in opg_nodes}
    if not class_ids_in_opg:
        raise RuntimeError(
            "Graph materialization requires projection graph nodes with class_config_id"
        )

    class_leaf_casefolded = class_token.split(".")[-1].casefold()
    candidate_start_class_ids = {
        class_id
        for class_id in class_ids_in_opg
        if _class_name_leaf(class_config=class_catalog.get(class_id)).casefold()
        == class_leaf_casefolded
    }
    if not candidate_start_class_ids:
        raise RuntimeError(
            "Graph materialization node_ref class token did not resolve in projection graph "
            + f"(experience={experience_name!r}, node_ref={node_ref!r}, class_token={class_token!r})"
        )
    if len(candidate_start_class_ids) != 1:
        raise RuntimeError(
            "Graph materialization node_ref class token resolved ambiguously in projection graph "
            + f"(experience={experience_name!r}, node_ref={node_ref!r}, class_token={class_token!r})"
        )

    current_class_id = next(iter(candidate_start_class_ids))
    for relationship_token in relationship_tokens:
        target_class_ids = _resolve_relationship_target_class_ids(
            source_class_id=current_class_id,
            relationship_token=relationship_token,
            class_catalog=class_catalog,
            relationship_targets_by_source_class=relationship_targets_by_source_class,
            node_ref=node_ref,
            experience_name=experience_name,
        )
        if not target_class_ids:
            raise RuntimeError(
                "Graph materialization node_ref relationship token did not resolve "
                + f"(experience={experience_name!r}, node_ref={node_ref!r}, relationship={relationship_token!r})"
            )
        if len(target_class_ids) != 1:
            raise RuntimeError(
                "Graph materialization node_ref relationship token resolved ambiguously "
                + f"(experience={experience_name!r}, node_ref={node_ref!r}, relationship={relationship_token!r})"
            )
        current_class_id = next(iter(target_class_ids))

    candidate_node_ids = [
        node.id for node in opg_nodes if node.class_config_id == current_class_id
    ]
    if not candidate_node_ids:
        raise RuntimeError(
            "Graph materialization node_ref final class has no projection node instance "
            + f"(experience={experience_name!r}, node_ref={node_ref!r})"
        )
    if len(candidate_node_ids) != 1:
        raise RuntimeError(
            "Graph materialization node_ref final class resolved to multiple projection nodes "
            + f"(experience={experience_name!r}, node_ref={node_ref!r})"
        )
    return candidate_node_ids[0]


def build_projection_node_snapshots_for_materialization(
    *,
    index: MetaGraphRuntimeIndex,
    opg: ObjectProjectionGraph,
    nodes: Sequence[ProjectionExperienceNodeMaterializationSpec],
    experience_name: str,
) -> tuple[ExperienceProjectionNodeSnapshot, ...]:
    if not nodes:
        return ()
    class_catalog = _build_class_catalog(index=index)
    relationship_targets_by_source_class = _build_relationship_targets_by_source_class(
        class_catalog=class_catalog,
    )
    snapshots: list[ExperienceProjectionNodeSnapshot] = []
    node_id_cache: dict[str, UUID] = {}
    for node_spec in nodes:
        cache_key = node_spec.node_ref.casefold()
        object_projection_graph_node_id = node_id_cache.get(cache_key)
        if object_projection_graph_node_id is None:
            object_projection_graph_node_id = resolve_projection_node_id_for_node_ref(
                opg=opg,
                class_catalog=class_catalog,
                relationship_targets_by_source_class=(
                    relationship_targets_by_source_class
                ),
                node_ref=node_spec.node_ref,
                experience_name=experience_name,
            )
            node_id_cache[cache_key] = object_projection_graph_node_id
        snapshots.append(
            ExperienceProjectionNodeSnapshot(
                object_projection_graph_node_id=object_projection_graph_node_id,
                key=node_spec.name,
                identity_keys=node_spec.identity_keys,
            )
        )
    return tuple(snapshots)


def _build_class_catalog(*, index: MetaGraphRuntimeIndex) -> dict[UUID, ClassConfig]:
    class_catalog: dict[UUID, ClassConfig] = {}
    ocg_nodes = tuple(index.ocg.object_config_graph_nodes or ())
    for node in ocg_nodes:
        if node.type != ObjectConfigGraphNodeType.class_:
            continue
        class_config = node.class_config
        if class_config is None:
            continue
        class_catalog[class_config.id] = class_config
    return class_catalog


def _build_relationship_targets_by_source_class(
    *,
    class_catalog: Mapping[UUID, ClassConfig],
) -> dict[UUID, dict[str, frozenset[UUID]]]:
    targets_by_source: dict[UUID, dict[str, frozenset[UUID]]] = {}
    mutable_targets: dict[UUID, dict[str, set[UUID]]] = {}

    for source_class_id, class_config in class_catalog.items():
        relationships = tuple(class_config.class_config_relationships or ())
        source_targets = mutable_targets.setdefault(source_class_id, {})

        for relationship in relationships:
            target_class_id = relationship.target_class_config_id
            names = _relationship_reference_names(relationship=relationship)
            for name in names:
                source_targets.setdefault(name.casefold(), set()).add(target_class_id)

    for source_class_id, source_targets in mutable_targets.items():
        targets_by_source[source_class_id] = {
            relationship_name: frozenset(target_ids)
            for relationship_name, target_ids in source_targets.items()
        }
    return targets_by_source


def _resolve_relationship_target_class_ids(
    *,
    source_class_id: UUID,
    relationship_token: str,
    class_catalog: Mapping[UUID, ClassConfig],
    relationship_targets_by_source_class: Mapping[UUID, Mapping[str, frozenset[UUID]]],
    node_ref: str,
    experience_name: str,
) -> frozenset[UUID]:
    relationship_targets = relationship_targets_by_source_class.get(source_class_id, {})
    relationship_token_casefolded = relationship_token.casefold()
    named_targets = relationship_targets.get(relationship_token_casefolded)
    if named_targets:
        return named_targets
    normalized_named_targets = relationship_targets.get(
        _relationship_match_key(relationship_token_casefolded)
    )
    if normalized_named_targets:
        return normalized_named_targets

    source_class = class_catalog.get(source_class_id)
    if source_class is None:
        return frozenset()
    relationships = tuple(source_class.class_config_relationships or ())
    fallback_matches: set[UUID] = set()
    for relationship in relationships:
        target_class_id = relationship.target_class_config_id
        target_leaf = _class_name_leaf(
            class_config=class_catalog.get(target_class_id)
        ).casefold()
        if _relationship_token_matches_target_leaf(
            relationship_token_casefolded=relationship_token_casefolded,
            target_leaf_casefolded=target_leaf,
        ):
            fallback_matches.add(target_class_id)

    if len(fallback_matches) > 1:
        raise RuntimeError(
            "Graph materialization node_ref relationship token resolved ambiguously by target class leaf "
            + f"(experience={experience_name!r}, node_ref={node_ref!r}, relationship={relationship_token!r})"
        )
    return frozenset(fallback_matches)


def _relationship_token_matches_target_leaf(
    *,
    relationship_token_casefolded: str,
    target_leaf_casefolded: str,
) -> bool:
    token = (relationship_token_casefolded or "").strip()
    target_leaf = (target_leaf_casefolded or "").strip()
    if not token or not target_leaf:
        return False
    if token == target_leaf:
        return True

    token_key = _relationship_match_key(token)
    target_leaf_key = _relationship_match_key(target_leaf)
    if not token_key or not target_leaf_key:
        return False
    if token_key == target_leaf_key:
        return True

    singular_token = token_key[:-1] if token_key.endswith("s") else token_key
    if singular_token and singular_token == target_leaf_key:
        return True
    if singular_token and target_leaf_key.endswith(singular_token):
        return True
    return target_leaf_key.endswith(token_key)


def _relationship_match_key(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _relationship_reference_names(
    *, relationship: ClassConfigRelationship
) -> tuple[str, ...]:
    attribute_rows = tuple(relationship.class_config_relationship_attributes or ())
    preferred_names: list[str] = []
    fallback_names: list[str] = []

    for attribute_row in attribute_rows:
        direction_token = _enum_token(attribute_row.direction)
        if direction_token != ClassConfigRelationshipDirection.forward.value:
            continue

        attribute_cfg = attribute_row.attribute_config
        attribute_name = (
            (attribute_cfg.name or "").strip() if attribute_cfg is not None else ""
        )
        if not attribute_name:
            continue

        role_token = _enum_token(attribute_row.role)
        if role_token == ClassConfigRelationshipAttributeRole.reference.value:
            preferred_names.append(attribute_name)
        else:
            fallback_names.append(attribute_name)

    names = preferred_names or fallback_names
    deduped_names: list[str] = []
    seen: set[str] = set()
    for name in names:
        key = name.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped_names.append(name)
        normalized_key = _relationship_match_key(name)
        if normalized_key and normalized_key not in seen:
            seen.add(normalized_key)
            deduped_names.append(normalized_key)
    return tuple(deduped_names)


def _class_name_leaf(*, class_config: ClassConfig | None) -> str:
    class_name = (class_config.name or "").strip() if class_config is not None else ""
    if not class_name:
        return ""
    if "." in class_name:
        return class_name.split(".")[-1]
    return class_name


def _enum_token(value: object) -> str:
    if value is None:
        return ""
    enum_value = getattr(value, "value", None)
    if isinstance(enum_value, str):
        return enum_value.strip().casefold()
    if isinstance(value, str):
        return value.strip().casefold()
    return str(value).strip().casefold()


def _find_projection_hash_by_name(
    *,
    index: MetaGraphRuntimeIndex,
    projection_name: str,
) -> str:
    target = (projection_name or "").strip()
    for opg in index.ocg.object_projection_graphs:
        name = (opg.name or "").strip()
        if name == target:
            return opg.projection_hash
    raise ValueError(
        f"Projection {projection_name!r} was not found in hosted environment OCG"
    )


def _find_projection_graph_by_opgi_id(
    *,
    index: MetaGraphRuntimeIndex,
    object_projection_graph_identity_id: UUID,
) -> ObjectProjectionGraph:
    for opg in index.ocg.object_projection_graphs:
        opgi = cast(Any, getattr(opg, "ObjectProjectionGraphIdentity", None))
        if opgi is not None and opgi.id == object_projection_graph_identity_id:
            return opg
        _ocgi, resolved_opgi = resolve_meta_graph_ocgi_opgi(
            index=index, projection_hash=opg.projection_hash
        )
        if (
            resolved_opgi is not None
            and resolved_opgi.id == object_projection_graph_identity_id
        ):
            return opg
    raise RuntimeError(
        "Graph materialization requires projection graph for object_projection_graph_identity_id="
        + str(object_projection_graph_identity_id)
    )


def _reset_generated_projection_lane(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
) -> None:
    branch_dir = store.aware_root / ".aware" / "oig" / str(branch_id)
    lane_dir = branch_dir / projection_hash
    if lane_dir.exists():
        shutil.rmtree(lane_dir)
    get_shared_materialization_cache().invalidate_lane(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if branch_dir.exists() and not any(branch_dir.iterdir()):
        shutil.rmtree(branch_dir)


async def _reset_stale_generated_projection_lane_if_needed(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    error_context: str,
) -> bool:
    store = FSCommitStore()
    head = await store.head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return False

    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"{error_context} missing projection hash: {projection_hash}"
        )

    try:
        oig, _ = await OIGMaterializer(commits=store).get(
            branch_id=branch_id,
            ocg=index.ocg,
            opg=opg,
            commit_id=None,
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
        )
        validate_object_instance_graph_against_opg(
            graph=oig,
            object_config_graph=index.ocg,
            object_projection_graph=opg,
        )
    except Exception as exc:
        _reset_generated_projection_lane(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        logger.warning(
            "%s reset stale generated projection lane: branch_id=%s projection_hash=%s error=%s",
            error_context,
            branch_id,
            projection_hash,
            exc,
        )
        return True
    return False


async def _hydrate_lane_session(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    error_context: str,
) -> Session:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        raise RuntimeError(f"{error_context} requires a committed lane head")

    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"{error_context} missing projection hash: {projection_hash}"
        )

    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=None,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    session = reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
    )
    return session


async def _lane_head_commit_id(
    *,
    branch_id: UUID,
    projection_hash: str,
) -> UUID | None:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None:
        return None
    raw_commit_id = head.get("commit_id")
    if raw_commit_id is None:
        return None
    if isinstance(raw_commit_id, UUID):
        return raw_commit_id
    return UUID(str(raw_commit_id))


def _split_node_ref(*, node_ref: str) -> tuple[str, tuple[str, ...]]:
    token = (node_ref or "").strip()
    if not token:
        raise RuntimeError("Graph materialization node_ref must be non-empty")
    parts = [part.strip() for part in token.split("::")]
    if not parts or not parts[0]:
        raise RuntimeError(f"Graph materialization node_ref is invalid: {node_ref!r}")
    class_token = parts[0]
    relationship_tokens = tuple(part for part in parts[1:] if part)
    return class_token, relationship_tokens


def _expect_list(value: object, *, field_name: str) -> list[object]:
    if isinstance(value, list):
        return cast(list[object], value)
    raise RuntimeError(f"Invalid experience compile plan: {field_name} must be a list")


def _optional_key_token(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        token = value.strip()
        return token or None
    raise RuntimeError(
        "Invalid experience compile plan: edge key must be string or null"
    )


def _required_step_payload_token(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("must be a string")
    token = value.strip()
    if not token:
        raise ValueError("must be non-empty")
    return token


def _optional_step_payload_token(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("must be a string or null")
    token = value.strip()
    return token or None


def _format_step_payload_validation_error(*, exc: ValidationError) -> str:
    details: list[str] = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", ()))
        message = str(error.get("msg", "invalid payload"))
        details.append(f"{location}: {message}" if location else message)
    detail_token = "; ".join(details) if details else str(exc)
    return f"Invalid graph materialization payload: {detail_token}"


def _resolve_projection_opgi_entry(
    *,
    opgi_by_key_casefolded: Mapping[str, tuple[UUID, set[str]]],
    projection_key: str,
    experience_name: str,
    graph_name: str,
    runtime_opgi_id: UUID | None = None,
) -> tuple[UUID, set[str]]:
    if runtime_opgi_id is not None:
        for opgi_entry in opgi_by_key_casefolded.values():
            if opgi_entry[0] == runtime_opgi_id:
                return opgi_entry
        raise RuntimeError(
            "Graph materialization resolved runtime OPGI was not found in OPGI catalog "
            + f"(experience={experience_name!r}, graph={graph_name!r}, "
            + f"projection={projection_key!r}, runtime_opgi_id={runtime_opgi_id})"
        )

    projection_key_casefolded = projection_key.casefold()
    exact_match = opgi_by_key_casefolded.get(projection_key_casefolded)
    if exact_match is not None:
        return exact_match

    suffix_matches = [
        (candidate_key, opgi_entry)
        for candidate_key, opgi_entry in opgi_by_key_casefolded.items()
        if candidate_key.rsplit(":", 1)[-1] == projection_key_casefolded
    ]
    if len(suffix_matches) == 1:
        return suffix_matches[0][1]

    candidate_projection_keys = sorted(opgi_by_key_casefolded)
    if len(suffix_matches) > 1:
        ambiguous = sorted(candidate_key for candidate_key, _ in suffix_matches)
        raise RuntimeError(
            "Graph materialization projection resolution failed: ambiguous projection key "
            + f"{projection_key!r} for experience={experience_name!r} graph={graph_name!r}; "
            + f"matches={ambiguous}; candidates={candidate_projection_keys}"
        )

    raise RuntimeError(
        "Graph materialization projection resolution failed: unknown projection key "
        + f"{projection_key!r} for experience={experience_name!r} graph={graph_name!r}; "
        + f"candidates={candidate_projection_keys}"
    )


__all__ = [
    "ProjectionExperienceGraphMaterializationSpec",
    "ProjectionExperienceGraphIdentityEdgeMaterializationSpec",
    "ProjectionExperienceGraphIdentityMaterializationSpec",
    "ProjectionExperienceNodeIdentityEdgeMaterializationSpec",
    "ProjectionExperienceNodeMaterializationSpec",
    "build_graph_materialization_plan",
    "build_projection_node_snapshots_for_materialization",
    "decode_graph_materialization_step_payload",
    "encode_graph_materialization_step_payload",
    "materialize_experience_graph_ontology",
    "resolve_graph_materialization_specs",
    "resolve_projection_node_id_for_node_ref",
]
