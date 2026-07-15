from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, Protocol, TypeVar, cast
from uuid import UUID

from aware_api_ontology.stable_ids import stable_api_id, stable_api_view_id
from aware_experience.graph.materialization.service import (
    ProjectionExperienceNodeMaterializationSpec,
    build_projection_node_snapshots_for_materialization,
)
from aware_experience.compiler.models import (
    ExperienceProjectionViewInvocationActionOwnership,
)
from aware_experience.materialization.branches import (
    derive_experience_reference_branch_id,
)
from aware_experience.materialization.lane_state import (
    reset_projection_lane_with_duplicate_view_keys_if_needed,
    reset_stale_generated_projection_lane_if_needed,
)
from aware_experience.materialization.snapshot_commit import (
    ExperienceProjectionBranchSnapshot,
    ExperienceProjectionViewInvocationActionSnapshot,
    ExperienceProjectionViewSnapshot,
    commit_projection_experience_snapshot,
)
from aware_experience.materialization.source_module_ontology import (
    source_module_ontology_dto_stable_ids_import_targets,
    temporary_python_import_paths,
)
from aware_experience.materialization.static_projection_targets import (
    projection_oigi_snapshots_for_materialization,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.materialization import (
    MaterializationExecutor,
    MaterializationLaneContext,
    MaterializationPlan,
    MaterializationRunReceipt,
    MaterializationStep,
    MaterializationStepResult,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_orm.session.session import Session
from aware_utils.logging import logger
from aware_experience.environment_profile.runtime_support import ocg_support


class PhaseRecorder(Protocol):
    def __call__(
        self,
        phase_timings_s: dict[str, float] | None,
        phase_name: str,
    ) -> AbstractContextManager[None]: ...


class ProjectionNodeSpec(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def node_ref(self) -> str: ...

    @property
    def identity_keys(self) -> Sequence[str]: ...


class ProjectionViewSpec(Protocol):
    @property
    def api_name(self) -> str: ...

    @property
    def api_view_name(self) -> str: ...

    @property
    def observable_key(self) -> str: ...

    @property
    def view_key(self) -> str: ...

    @property
    def state_provider_ref(self) -> str | None: ...

    @property
    def invocation_actions(
        self,
    ) -> Sequence[ExperienceProjectionViewInvocationActionOwnership]: ...


class ProjectionStepSpec(Protocol):
    @property
    def experience_name(self) -> str: ...

    @property
    def projection_key(self) -> str: ...

    @property
    def branches(self) -> Sequence[str]: ...

    @property
    def views(self) -> Sequence[ProjectionViewSpec]: ...

    @property
    def nodes(self) -> Sequence[ProjectionNodeSpec]: ...

    @property
    def runtime_opgi_id(self) -> UUID | None: ...


ProjectionStepSpecT = TypeVar("ProjectionStepSpecT", bound=ProjectionStepSpec)


class ResolveProjectionSpecs(Protocol, Generic[ProjectionStepSpecT]):
    def __call__(
        self,
        *,
        compile_plan_payloads: Sequence[Mapping[str, object]],
        api_compile_plan_payloads: Sequence[Mapping[str, object]],
        index: MetaGraphRuntimeIndex,
        allow_unresolved_projection_experiences: bool,
    ) -> Sequence[ProjectionStepSpecT]: ...


class BuildProjectionPlan(Protocol, Generic[ProjectionStepSpecT]):
    def __call__(
        self,
        *,
        lane: MaterializationLaneContext,
        specs: Sequence[ProjectionStepSpecT],
    ) -> MaterializationPlan: ...


class DecodeProjectionStepPayload(Protocol, Generic[ProjectionStepSpecT]):
    def __call__(self, payload: Mapping[str, object]) -> ProjectionStepSpecT: ...


class ResolveProjectionOpgiId(Protocol):
    def __call__(
        self,
        *,
        opgi_by_key_casefolded: Mapping[str, tuple[UUID, set[str] | frozenset[str]]],
        projection_key: str,
        experience_name: str,
        runtime_opgi_id: UUID | None = None,
    ) -> UUID: ...


class FindProjectionGraphByOpgiId(Protocol):
    def __call__(
        self,
        *,
        index: MetaGraphRuntimeIndex,
        object_projection_graph_identity_id: UUID,
    ) -> ObjectProjectionGraph: ...


class BuildObservableIdIndex(Protocol):
    def __call__(
        self,
        *,
        index: MetaGraphRuntimeIndex,
        opg: ObjectProjectionGraph,
    ) -> dict[str, UUID]: ...


class ResolveObservableIdForProjectionView(Protocol):
    def __call__(
        self,
        *,
        observable_id_by_key: Mapping[str, UUID],
        object_projection_graph_identity_id: UUID,
        observable_key: str,
        experience_name: str,
        projection_key: str,
    ) -> UUID: ...


class ProjectionViewKey(Protocol):
    def __call__(self, *, observable_key: str, view_key: str) -> str: ...


class ProjectionViewInvocationActionSnapshotFactory(Protocol):
    def __call__(
        self,
        *,
        action: ExperienceProjectionViewInvocationActionOwnership,
        api_view_id: UUID,
        experience_name: str,
        observable_key: str,
        view_key: str,
    ) -> ExperienceProjectionViewInvocationActionSnapshot: ...


class ProjectionViewIdsByProjectionKeyResolver(Protocol):
    def __call__(self, *, projection_session: Session) -> object: ...


@dataclass(frozen=True, slots=True)
class ProjectionMaterializationRunnerDependencies(Generic[ProjectionStepSpecT]):
    phase_recorder: PhaseRecorder
    resolve_projection_materialization_specs: ResolveProjectionSpecs[
        ProjectionStepSpecT
    ]
    build_projection_materialization_plan: BuildProjectionPlan[ProjectionStepSpecT]
    decode_projection_materialization_step_payload: DecodeProjectionStepPayload[
        ProjectionStepSpecT
    ]
    resolve_projection_opgi_id_for_projection_key: ResolveProjectionOpgiId
    find_projection_graph_by_opgi_id: FindProjectionGraphByOpgiId
    build_observable_id_index: BuildObservableIdIndex
    resolve_observable_id_for_projection_view: ResolveObservableIdForProjectionView
    projection_view_key: ProjectionViewKey
    projection_view_invocation_action_snapshot: (
        ProjectionViewInvocationActionSnapshotFactory
    )
    projection_view_ids_by_projection_key_from_session: (
        ProjectionViewIdsByProjectionKeyResolver
    )


async def run_projection_materialization(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    api_compile_plan_payloads: Sequence[Mapping[str, object]] = (),
    phase_timings_s: dict[str, float] | None = None,
    allow_unresolved_projection_experiences: bool = False,
    semantic_materialization_context: Mapping[str, object] | None = None,
    source_experience_toml_path: Path | None = None,
    dependencies: ProjectionMaterializationRunnerDependencies[ProjectionStepSpecT],
) -> MaterializationRunReceipt | None:
    with dependencies.phase_recorder(
        phase_timings_s,
        "experience_projection.resolve_projection_materialization_specs",
    ):
        specs = dependencies.resolve_projection_materialization_specs(
            compile_plan_payloads=compile_plan_payloads,
            api_compile_plan_payloads=api_compile_plan_payloads,
            index=index,
            allow_unresolved_projection_experiences=(
                allow_unresolved_projection_experiences
            ),
        )
    if not specs:
        return None

    with dependencies.phase_recorder(
        phase_timings_s,
        "experience_projection.resolve_projection_hash_and_plan",
    ):
        projection_experience_projection_hash = (
            ocg_support.find_projection_hash_by_name(
                index=index,
                projection_name="ProjectionExperience",
            )
        )
        projection_experience_oigi_projection_hash = (
            ocg_support.find_projection_hash_by_name(
                index=index,
                projection_name="ProjectionExperienceOIGI",
            )
        )
        projection_lane = MaterializationLaneContext(
            branch_id=lane.branch_id,
            projection_hash=projection_experience_projection_hash,
        )
        plan = dependencies.build_projection_materialization_plan(
            lane=projection_lane,
            specs=specs,
        )
    with dependencies.phase_recorder(
        phase_timings_s,
        "experience_projection.build_opgi_index",
    ):
        opgi_by_key = ocg_support.build_opgi_index(index=index)
        opgi_by_key_casefolded = {
            (key or "").strip().casefold(): opgi_entry
            for key, opgi_entry in opgi_by_key.items()
            if (key or "").strip()
        }
    opg_by_opgi_id: dict[UUID, ObjectProjectionGraph] = {}
    dto_stable_ids_import_targets = (
        source_module_ontology_dto_stable_ids_import_targets(
            context=semantic_materialization_context,
            source_experience_toml_path=source_experience_toml_path,
        )
    )

    async def _runner(
        *, plan: MaterializationPlan, step: MaterializationStep
    ) -> MaterializationStepResult:
        logger.debug(
            "Running Experience projection materialization step %s", step.step_id
        )
        with dependencies.phase_recorder(
            phase_timings_s,
            f"experience_projection.runner:{step.step_id}.decode_step_payload",
        ):
            spec = dependencies.decode_projection_materialization_step_payload(
                step.payload
            )
            experience_branch_id = derive_experience_reference_branch_id(
                base_branch_id=projection_lane.branch_id,
                experience_name=spec.experience_name,
            )
            projection_step_lane = MaterializationLaneContext(
                branch_id=experience_branch_id,
                projection_hash=projection_lane.projection_hash,
            )

        with dependencies.phase_recorder(
            phase_timings_s,
            f"experience_projection.runner:{step.step_id}.reset_stale_generated_lane_if_needed",
        ):
            invalid_opg_projection_lane_reset = (
                await reset_stale_generated_projection_lane_if_needed(
                    index=index,
                    branch_id=projection_step_lane.branch_id,
                    projection_hash=projection_step_lane.projection_hash,
                    error_context="Experience projection materialization",
                )
            )
            duplicate_view_key_projection_lane_reset = False
            if not invalid_opg_projection_lane_reset:
                duplicate_view_key_projection_lane_reset = await reset_projection_lane_with_duplicate_view_keys_if_needed(
                    index=index,
                    branch_id=projection_step_lane.branch_id,
                    projection_hash=projection_step_lane.projection_hash,
                    error_context="Experience projection materialization",
                    view_ids_by_projection_key_resolver=(
                        dependencies.projection_view_ids_by_projection_key_from_session
                    ),
                )
            stale_projection_lane_reset = (
                invalid_opg_projection_lane_reset
                or duplicate_view_key_projection_lane_reset
            )

        with dependencies.phase_recorder(
            phase_timings_s,
            f"experience_projection.runner:{step.step_id}.resolve_projection_opgi",
        ):
            projection_opgi_id = (
                dependencies.resolve_projection_opgi_id_for_projection_key(
                    opgi_by_key_casefolded=opgi_by_key_casefolded,
                    projection_key=spec.projection_key,
                    experience_name=spec.experience_name,
                    runtime_opgi_id=spec.runtime_opgi_id,
                )
            )

        with dependencies.phase_recorder(
            phase_timings_s,
            f"experience_projection.runner:{step.step_id}.find_projection_graph",
        ):
            opg = opg_by_opgi_id.get(projection_opgi_id)
            if opg is None:
                opg = dependencies.find_projection_graph_by_opgi_id(
                    index=index,
                    object_projection_graph_identity_id=projection_opgi_id,
                )
                opg_by_opgi_id[projection_opgi_id] = opg

        with dependencies.phase_recorder(
            phase_timings_s,
            f"experience_projection.runner:{step.step_id}.build_observable_id_index",
        ):
            observable_id_by_key = dependencies.build_observable_id_index(
                index=index,
                opg=opg,
            )
        with dependencies.phase_recorder(
            phase_timings_s,
            f"experience_projection.runner:{step.step_id}.build_projection_node_snapshots",
        ):
            projection_node_snapshots = (
                build_projection_node_snapshots_for_materialization(
                    index=index,
                    opg=opg,
                    nodes=cast(
                        Sequence[ProjectionExperienceNodeMaterializationSpec],
                        spec.nodes,
                    ),
                    experience_name=spec.experience_name,
                )
            )
            with temporary_python_import_paths(
                dto_stable_ids_import_targets.import_paths
            ):
                projection_oigi_snapshots = (
                    projection_oigi_snapshots_for_materialization(
                        index=index,
                        opg=opg,
                        object_projection_graph_identity_id=projection_opgi_id,
                        experience_name=spec.experience_name,
                        projection_node_snapshots=projection_node_snapshots,
                        compile_plan_payloads=compile_plan_payloads,
                        dto_stable_ids_import_roots_by_module_id=(
                            dto_stable_ids_import_targets.roots_by_module_id
                        ),
                    )
                )

        with dependencies.phase_recorder(
            phase_timings_s,
            f"experience_projection.runner:{step.step_id}.load_projection_lane_head",
        ):
            projection_lane_head = await FSCommitStore().head(
                branch_id=projection_step_lane.branch_id,
                projection_hash=projection_step_lane.projection_hash,
            )

        projection_lane_reused = (
            projection_lane_head is not None
            and projection_lane_head.get("commit_id") is not None
        )
        with dependencies.phase_recorder(
            phase_timings_s,
            f"experience_projection.runner:{step.step_id}.commit_projection_snapshot",
        ):
            view_snapshots: list[ExperienceProjectionViewSnapshot] = []
            for view_spec in spec.views:
                observable_id = dependencies.resolve_observable_id_for_projection_view(
                    observable_id_by_key=observable_id_by_key,
                    object_projection_graph_identity_id=projection_opgi_id,
                    observable_key=view_spec.observable_key,
                    experience_name=spec.experience_name,
                    projection_key=spec.projection_key,
                )
                api_view_id = stable_api_view_id(
                    api_id=stable_api_id(name=view_spec.api_name),
                    object_projection_graph_observable_id=observable_id,
                    name=view_spec.api_view_name,
                )
                view_snapshots.append(
                    ExperienceProjectionViewSnapshot(
                        api_view_id=api_view_id,
                        name=dependencies.projection_view_key(
                            observable_key=view_spec.observable_key,
                            view_key=view_spec.view_key,
                        ),
                        state_provider_ref=view_spec.state_provider_ref,
                        invocation_actions=tuple(
                            dependencies.projection_view_invocation_action_snapshot(
                                action=action,
                                api_view_id=api_view_id,
                                experience_name=spec.experience_name,
                                observable_key=view_spec.observable_key,
                                view_key=view_spec.view_key,
                            )
                            for action in view_spec.invocation_actions
                        ),
                    )
                )
            projection_snapshot = await commit_projection_experience_snapshot(
                index=index,
                actor_id=actor_id,
                branch_id=projection_step_lane.branch_id,
                projection_hash=projection_step_lane.projection_hash,
                projection_oigi_hash=projection_experience_oigi_projection_hash,
                object_projection_graph_identity_id=projection_opgi_id,
                name=spec.experience_name,
                branches=tuple(
                    ExperienceProjectionBranchSnapshot(name=branch_name)
                    for branch_name in spec.branches
                ),
                views=tuple(view_snapshots),
                nodes=projection_node_snapshots,
                oigis=projection_oigi_snapshots,
            )

        return MaterializationStepResult(
            details={
                "experience_name": spec.experience_name,
                "projection_key": spec.projection_key,
                "branch_count": len(spec.branches),
                "view_count": len(spec.views),
                "node_count": len(spec.nodes),
                "oigi_count": len(projection_oigi_snapshots),
                "branch_id": str(projection_step_lane.branch_id),
                "stale_projection_lane_reset": stale_projection_lane_reset,
                "duplicate_view_key_projection_lane_reset": (
                    duplicate_view_key_projection_lane_reset
                ),
                "projection_lane_reused": projection_lane_reused,
            },
            commit_id=projection_snapshot.commit_id,
            head_commit_id=projection_snapshot.head_commit_id,
        )

    with dependencies.phase_recorder(
        phase_timings_s, "experience_projection.executor.run"
    ):
        return await MaterializationExecutor().run(plan=plan, runner=_runner)


__all__ = [
    "ProjectionMaterializationRunnerDependencies",
    "run_projection_materialization",
]
