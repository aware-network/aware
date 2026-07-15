from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar
from uuid import UUID

from aware_experience.materialization.branches import (
    derive_experience_reference_branch_id,
)
from aware_experience.materialization.lane_state import hydrate_lane_session
from aware_experience.materialization.snapshot_commit import (
    ExperienceLayoutGraphBindingSnapshot,
    ExperienceSectionGraphBindingSnapshot,
    commit_projection_experience_snapshot,
)
from aware_experience.materialization.projection_snapshot_preservation import (
    preserve_projection_branch_snapshots_from_session,
    preserve_projection_node_snapshots_from_session,
    preserve_projection_oigi_snapshots_from_session,
    preserve_projection_view_snapshots_from_session,
)
from aware_experience_ontology.projection.projection_experience_graph import (
    ProjectionExperienceGraph,
)
from aware_experience_ontology.projection.projection_experience_graph_identity import (
    ProjectionExperienceGraphIdentity,
)
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
from aware_experience.environment_profile.runtime_support import ocg_support


class SectionSurfaceBindingSpec(Protocol):
    @property
    def surface_key(self) -> str: ...

    @property
    def section_key(self) -> str: ...

    @property
    def observable_key(self) -> str: ...

    @property
    def view_key(self) -> str: ...

    @property
    def layout_config_section_config_id(self) -> UUID | None: ...

    @property
    def graph_identity_ref(self) -> str | None: ...


class LayoutGraphBindingSpec(Protocol):
    @property
    def layout_config_id(self) -> UUID: ...

    @property
    def binding_key(self) -> str: ...

    @property
    def section_graph_binding_keys(self) -> Sequence[str]: ...


class SectionSurfaceStepSpec(Protocol):
    @property
    def experience_name(self) -> str: ...

    @property
    def projection_key(self) -> str: ...

    @property
    def surfaces(self) -> Sequence[SectionSurfaceBindingSpec]: ...

    @property
    def layout_bindings(self) -> Sequence[LayoutGraphBindingSpec]: ...

    @property
    def runtime_opgi_id(self) -> UUID | None: ...


SectionSurfaceStepSpecT = TypeVar(
    "SectionSurfaceStepSpecT", bound=SectionSurfaceStepSpec
)


class ResolveSectionSurfaceSpecs(Protocol, Generic[SectionSurfaceStepSpecT]):
    def __call__(
        self,
        *,
        compile_plan_payloads: Sequence[Mapping[str, object]],
        index: MetaGraphRuntimeIndex,
        external_projection_keys_by_experience_name: Mapping[str, str] | None,
        allow_unresolved_projection_experiences: bool,
    ) -> Sequence[SectionSurfaceStepSpecT]: ...


class BuildSectionSurfacePlan(Protocol, Generic[SectionSurfaceStepSpecT]):
    def __call__(
        self,
        *,
        lane: MaterializationLaneContext,
        specs: Sequence[SectionSurfaceStepSpecT],
    ) -> MaterializationPlan: ...


class DecodeSectionSurfaceStepPayload(Protocol, Generic[SectionSurfaceStepSpecT]):
    def __call__(self, payload: Mapping[str, object]) -> SectionSurfaceStepSpecT: ...


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


class ProjectionExperienceIdsByNameAndOpgi(Protocol):
    def __call__(
        self,
        *,
        projection_session: Session,
    ) -> dict[tuple[str, UUID], UUID]: ...


class ProjectionViewIdsByProjectionKey(Protocol):
    def __call__(
        self,
        *,
        projection_session: Session,
    ) -> dict[tuple[UUID, str], UUID]: ...


@dataclass(frozen=True, slots=True)
class SectionSurfaceMaterializationRunnerDependencies(Generic[SectionSurfaceStepSpecT]):
    resolve_section_surface_materialization_specs: ResolveSectionSurfaceSpecs[
        SectionSurfaceStepSpecT
    ]
    build_section_surface_materialization_plan: BuildSectionSurfacePlan[
        SectionSurfaceStepSpecT
    ]
    decode_section_surface_materialization_step_payload: (
        DecodeSectionSurfaceStepPayload[SectionSurfaceStepSpecT]
    )
    resolve_projection_opgi_id_for_projection_key: ResolveProjectionOpgiId
    find_projection_graph_by_opgi_id: FindProjectionGraphByOpgiId
    build_observable_id_index: BuildObservableIdIndex
    resolve_observable_id_for_projection_view: ResolveObservableIdForProjectionView
    projection_view_key: ProjectionViewKey
    projection_experience_ids_by_name_and_opgi_from_session: (
        ProjectionExperienceIdsByNameAndOpgi
    )
    projection_experience_view_ids_by_projection_key_from_session: (
        ProjectionViewIdsByProjectionKey
    )


async def run_section_surface_materialization(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    external_projection_keys_by_experience_name: Mapping[str, str] | None = None,
    allow_unresolved_projection_experiences: bool = False,
    dependencies: SectionSurfaceMaterializationRunnerDependencies[
        SectionSurfaceStepSpecT
    ],
) -> MaterializationRunReceipt | None:
    specs = dependencies.resolve_section_surface_materialization_specs(
        compile_plan_payloads=compile_plan_payloads,
        index=index,
        external_projection_keys_by_experience_name=(
            external_projection_keys_by_experience_name
        ),
        allow_unresolved_projection_experiences=(
            allow_unresolved_projection_experiences
        ),
    )
    if not specs:
        return None

    projection_experience_projection_hash = ocg_support.find_projection_hash_by_name(
        index=index,
        projection_name="ProjectionExperience",
    )
    projection_experience_graph_projection_hash = (
        ocg_support.find_projection_hash_by_name(
            index=index,
            projection_name="ProjectionExperienceGraph",
        )
    )
    projection_experience_oigi_projection_hash = (
        ocg_support.find_projection_hash_by_name(
            index=index,
            projection_name="ProjectionExperienceOIGI",
        )
    )
    section_graph_binding_projection_hash = ocg_support.find_projection_hash_by_name(
        index=index,
        projection_name="ProjectionExperienceSectionGraphBinding",
    )
    layout_graph_binding_projection_hash = ocg_support.find_projection_hash_by_name(
        index=index,
        projection_name="ProjectionExperienceLayoutGraphBinding",
    )
    attention_layout_config_projection_hash = ocg_support.find_projection_hash_by_name(
        index=index,
        projection_name="LayoutConfig",
    )
    projection_lane = MaterializationLaneContext(
        branch_id=lane.branch_id,
        projection_hash=projection_experience_projection_hash,
    )
    graph_lane = MaterializationLaneContext(
        branch_id=lane.branch_id,
        projection_hash=projection_experience_graph_projection_hash,
    )
    plan = dependencies.build_section_surface_materialization_plan(
        lane=projection_lane,
        specs=specs,
    )

    opgi_by_key = ocg_support.build_opgi_index(index=index)
    opgi_by_key_casefolded = {
        (key or "").strip().casefold(): opgi_entry
        for key, opgi_entry in opgi_by_key.items()
        if (key or "").strip()
    }
    opg_by_opgi_id: dict[UUID, ObjectProjectionGraph] = {}

    async def _runner(
        *, plan: MaterializationPlan, step: MaterializationStep
    ) -> MaterializationStepResult:
        spec = dependencies.decode_section_surface_materialization_step_payload(
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
        graph_step_lane = MaterializationLaneContext(
            branch_id=experience_branch_id,
            projection_hash=graph_lane.projection_hash,
        )
        projection_opgi_id = dependencies.resolve_projection_opgi_id_for_projection_key(
            opgi_by_key_casefolded=opgi_by_key_casefolded,
            projection_key=spec.projection_key,
            experience_name=spec.experience_name,
            runtime_opgi_id=spec.runtime_opgi_id,
        )
        opg = opg_by_opgi_id.get(projection_opgi_id)
        if opg is None:
            opg = dependencies.find_projection_graph_by_opgi_id(
                index=index,
                object_projection_graph_identity_id=projection_opgi_id,
            )
            opg_by_opgi_id[projection_opgi_id] = opg
        observable_id_by_key = dependencies.build_observable_id_index(
            index=index,
            opg=opg,
        )

        projection_session = await hydrate_lane_session(
            index=index,
            branch_id=projection_step_lane.branch_id,
            projection_hash=projection_step_lane.projection_hash,
            error_context="ProjectionExperience section-surface materialization",
        )
        graph_session = await hydrate_lane_session(
            index=index,
            branch_id=graph_step_lane.branch_id,
            projection_hash=graph_step_lane.projection_hash,
            error_context="ProjectionExperienceGraph section-surface materialization",
        )

        experience_ids_by_name_and_opgi = (
            dependencies.projection_experience_ids_by_name_and_opgi_from_session(
                projection_session=projection_session,
            )
        )
        view_ids_by_projection_key = (
            dependencies.projection_experience_view_ids_by_projection_key_from_session(
                projection_session=projection_session
            )
        )
        projection_experience_ids_by_graph_id: dict[UUID, UUID] = {}
        graph_identity_ids_by_key: dict[tuple[UUID, str], UUID] = {}
        projection_graph_identities: list[ProjectionExperienceGraphIdentity] = []

        for obj in graph_session.imap_all_objects():
            if isinstance(obj, ProjectionExperienceGraph) and obj.id is not None:
                projection_experience_id = getattr(
                    obj, "projection_experience_id", None
                )
                if projection_experience_id is not None:
                    projection_experience_ids_by_graph_id[obj.id] = (
                        projection_experience_id
                    )
            elif (
                isinstance(obj, ProjectionExperienceGraphIdentity)
                and obj.id is not None
            ):
                projection_graph_identities.append(obj)

        for obj in projection_graph_identities:
            projection_experience_graph_id = getattr(
                obj, "projection_experience_graph_id", None
            )
            if projection_experience_graph_id is None:
                continue
            projection_experience_id = projection_experience_ids_by_graph_id.get(
                projection_experience_graph_id
            )
            key = (obj.key or "").strip()
            if projection_experience_id is not None and key:
                graph_identity_ids_by_key[
                    (projection_experience_id, key.casefold())
                ] = obj.id

        experience_id = experience_ids_by_name_and_opgi.get(
            (spec.experience_name.casefold(), projection_opgi_id)
        )
        if experience_id is None:
            raise RuntimeError(
                "Section-surface materialization requires committed ProjectionExperience "
                + f"for experience={spec.experience_name!r} "
                + f"and runtime_opgi_id={projection_opgi_id}"
            )

        binding_snapshots: list[ExperienceSectionGraphBindingSnapshot] = []
        for surface in spec.surfaces:
            dependencies.resolve_observable_id_for_projection_view(
                observable_id_by_key=observable_id_by_key,
                object_projection_graph_identity_id=projection_opgi_id,
                observable_key=surface.observable_key,
                experience_name=spec.experience_name,
                projection_key=spec.projection_key,
            )
            view_id = view_ids_by_projection_key.get(
                (
                    experience_id,
                    dependencies.projection_view_key(
                        observable_key=surface.observable_key,
                        view_key=surface.view_key,
                    ).casefold(),
                )
            )
            if view_id is None:
                raise RuntimeError(
                    "Section-surface materialization could not resolve committed ProjectionExperienceView "
                    + f"(experience={spec.experience_name!r}, surface={surface.surface_key!r}, "
                    + f"view={surface.observable_key}.{surface.view_key})"
                )
            if surface.graph_identity_ref is None:
                raise RuntimeError(
                    "Section-surface materialization requires graph_identity_ref "
                    + f"(experience={spec.experience_name!r}, surface={surface.surface_key!r})"
                )
            graph_identity_id = graph_identity_ids_by_key.get(
                (experience_id, surface.graph_identity_ref.casefold())
            )
            if graph_identity_id is None:
                raise RuntimeError(
                    "Section-surface materialization could not resolve committed "
                    + "ProjectionExperienceGraphIdentity "
                    + f"(experience={spec.experience_name!r}, surface={surface.surface_key!r}, "
                    + f"graph_identity={surface.graph_identity_ref!r})"
                )
            if surface.layout_config_section_config_id is None:
                raise RuntimeError(
                    "Section-surface materialization requires explicit "
                    + "layout_config_section_config_id for "
                    + f"experience={spec.experience_name!r}, surface={surface.surface_key!r}. "
                    + "ProjectionExperienceSectionGraphBinding must target Attention "
                    + "LayoutConfigSectionConfig directly."
                )
            binding_snapshots.append(
                ExperienceSectionGraphBindingSnapshot(
                    layout_config_section_config_id=(
                        surface.layout_config_section_config_id
                    ),
                    projection_experience_view_id=view_id,
                    projection_experience_graph_identity_id=graph_identity_id,
                    binding_key=surface.surface_key,
                    section_key=surface.section_key,
                )
            )
        layout_binding_snapshots = tuple(
            ExperienceLayoutGraphBindingSnapshot(
                layout_config_id=layout_binding.layout_config_id,
                binding_key=layout_binding.binding_key,
                section_graph_binding_keys=tuple(
                    layout_binding.section_graph_binding_keys
                ),
            )
            for layout_binding in spec.layout_bindings
        )
        projection_snapshot = await commit_projection_experience_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=projection_step_lane.branch_id,
            projection_hash=projection_step_lane.projection_hash,
            projection_oigi_hash=projection_experience_oigi_projection_hash,
            projection_graph_hash=projection_experience_graph_projection_hash,
            section_graph_binding_hash=section_graph_binding_projection_hash,
            layout_graph_binding_hash=layout_graph_binding_projection_hash,
            attention_layout_config_hash=attention_layout_config_projection_hash,
            object_projection_graph_identity_id=projection_opgi_id,
            name=spec.experience_name,
            branches=preserve_projection_branch_snapshots_from_session(
                projection_session=projection_session,
                projection_experience_id=experience_id,
            ),
            views=preserve_projection_view_snapshots_from_session(
                projection_session=projection_session,
                projection_experience_id=experience_id,
            ),
            nodes=preserve_projection_node_snapshots_from_session(
                projection_session=projection_session,
                projection_experience_id=experience_id,
            ),
            oigis=preserve_projection_oigi_snapshots_from_session(
                projection_session=projection_session,
                projection_experience_id=experience_id,
            ),
            section_graph_bindings=tuple(binding_snapshots),
            layout_graph_bindings=layout_binding_snapshots,
        )
        return MaterializationStepResult(
            details={
                "experience_name": spec.experience_name,
                "projection_key": spec.projection_key,
                "surface_count": len(spec.surfaces),
                "section_graph_binding_commit_ids": tuple(
                    str(commit_id)
                    for commit_id in projection_snapshot.section_graph_binding_commit_ids
                ),
                "layout_graph_binding_commit_ids": tuple(
                    str(commit_id)
                    for commit_id in projection_snapshot.layout_graph_binding_commit_ids
                ),
                "branch_id": str(projection_step_lane.branch_id),
            },
            commit_id=projection_snapshot.commit_id,
            head_commit_id=projection_snapshot.head_commit_id,
        )

    return await MaterializationExecutor().run(plan=plan, runner=_runner)


__all__ = [
    "run_section_surface_materialization",
    "SectionSurfaceMaterializationRunnerDependencies",
]
