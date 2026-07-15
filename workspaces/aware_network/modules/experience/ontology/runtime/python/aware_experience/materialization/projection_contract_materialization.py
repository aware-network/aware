from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Protocol, cast
from uuid import UUID

from pydantic import ValidationError

from aware_api_ontology.stable_ids import (
    stable_api_capability_endpoint_id,
    stable_api_capability_id,
    stable_api_id,
    stable_api_view_capability_endpoint_id,
)
from aware_attention_ontology.stable_ids import stable_layout_config_section_config_id
from aware_experience.compiler.models import (
    ExperienceProjectionExperienceOwnership,
    ExperienceProjectionViewInvocationActionOwnership,
)
from aware_experience.environment_profile.runtime_support import ocg_support
from aware_experience.graph.materialization.service import (
    ProjectionExperienceNodeMaterializationSpec,
    materialize_experience_graph_ontology,
)
from aware_experience.graph.ontology import decode_graph_ontology_plan_payload
from aware_experience.materialization.compile_plan_payloads import (
    _ProjectionLayoutGraphBindingPayload,
    _ProjectionMaterializationNodePayload,
    _ProjectionMaterializationStepPayload,
    _ProjectionMaterializationViewInvocationActionPayload,
    _ProjectionMaterializationViewPayload,
    _ProjectionSectionSurfaceBindingPayload,
    _ProjectionSectionSurfaceMaterializationStepPayload,
    _expect_list,
    _expect_mapping,
    _expect_nonempty_text,
    _format_step_payload_validation_error,
    _optional_payload_token,
    load_experience_compile_plan_payloads,
)
from aware_experience.materialization.environment_profile_materialization import (
    EnvironmentProfileMaterializationSpec,
    resolve_environment_profile_materialization_specs,
)
from aware_experience.materialization.projection_materialization_runner import (
    ProjectionMaterializationRunnerDependencies,
    run_projection_materialization,
)
from aware_experience.materialization.projection_resolution import (
    ProjectionRuntimeResolver,
    build_projection_runtime_resolver,
)
from aware_experience.materialization.section_surface_materialization_runner import (
    SectionSurfaceMaterializationRunnerDependencies,
    run_section_surface_materialization,
)
from aware_experience.materialization.snapshot_commit import (
    ExperienceProjectionViewInvocationActionSnapshot,
)
from aware_experience.projection.contracts import (
    decode_projection_experience_ownership_payload,
)
from aware_experience.program.registry_index import find_repo_root
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_experience_ontology.projection.projection_experience_view import (
    ProjectionExperienceView,
)
from aware_meta.materialization import (
    MaterializationLaneContext,
    MaterializationPlan,
    MaterializationRunReceipt,
    MaterializationStep,
)
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.stable_ids import stable_object_projection_graph_observable_id
from aware_orm.session.session import Session
from aware_utils.logging import logger


class _RuntimeProtocol(Protocol):
    @property
    def manifest_path(self) -> Path: ...

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
    logger.info("Experience package materialization phase started: %s", phase_name)
    try:
        yield
    finally:
        duration_s = _round_duration_s(perf_counter() - started_at)
        phase_timings_s[phase_name] = duration_s
        logger.info(
            "Experience package materialization phase finished: %s (%.6fs)",
            phase_name,
            duration_s,
        )


@dataclass(frozen=True, slots=True)
class ProjectionExperienceViewMaterializationSpec:
    observable_key: str
    view_key: str
    api_name: str
    api_view_name: str
    api_view_ref: str
    state_model_ref: str | None = None
    state_provider_ref: str | None = None
    invocation_actions: tuple[
        ExperienceProjectionViewInvocationActionOwnership, ...
    ] = ()


@dataclass(frozen=True, slots=True)
class _ApiViewCapabilityEndpointMaterializationRef:
    api_name: str
    view_name: str
    view_ref: str
    action_key: str
    endpoint_ref: str
    source_path: str
    api_capability_endpoint_id: UUID
    description: str | None = None


@dataclass(frozen=True, slots=True)
class ProjectionExperienceMaterializationSpec:
    experience_name: str
    projection_key: str
    branches: tuple[str, ...]
    views: tuple[ProjectionExperienceViewMaterializationSpec, ...]
    nodes: tuple[ProjectionExperienceNodeMaterializationSpec, ...] = ()
    runtime_opgi_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ProjectionExperienceSectionSurfaceBindingSpec:
    surface_key: str
    section_key: str
    observable_key: str
    view_key: str
    source_path: str
    layout_config_section_config_id: UUID | None = None
    source_surface_key: str | None = None
    graph_identity_ref: str | None = None
    node_identity_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ProjectionExperienceLayoutGraphBindingSpec:
    layout_config_id: UUID
    binding_key: str
    section_graph_binding_keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectionExperienceSectionSurfaceMaterializationSpec:
    experience_name: str
    projection_key: str
    surfaces: tuple[ProjectionExperienceSectionSurfaceBindingSpec, ...]
    layout_bindings: tuple[ProjectionExperienceLayoutGraphBindingSpec, ...] = ()
    runtime_opgi_id: UUID | None = None


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


def _projection_node_materialization_specs_for_ownership(
    *,
    ownership: ExperienceProjectionExperienceOwnership,
    experience_name: str,
) -> tuple[ProjectionExperienceNodeMaterializationSpec, ...]:
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
    return tuple(
        sorted(
            node_specs,
            key=lambda item: (item.name.casefold(), item.node_ref.casefold()),
        )
    )


def resolve_projection_materialization_specs(
    *,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    api_compile_plan_payloads: Sequence[Mapping[str, object]] = (),
    index: MetaGraphRuntimeIndex | None = None,
    allow_unresolved_projection_experiences: bool = False,
) -> tuple[ProjectionExperienceMaterializationSpec, ...]:
    if not compile_plan_payloads:
        return ()

    specs_by_experience: dict[str, ProjectionExperienceMaterializationSpec] = {}
    try:
        projection_ownership = _decode_projection_experience_ownership(
            compile_plan_payloads=compile_plan_payloads
        )
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc
    api_view_action_refs_by_key = _api_view_capability_endpoint_refs_by_view_action(
        api_compile_plan_payloads=api_compile_plan_payloads
    )

    resolver = (
        build_projection_runtime_resolver(index=index) if index is not None else None
    )
    for ownership in projection_ownership:
        experience_name = ownership.name.strip()
        try:
            projection_key, runtime_opgi_id = (
                _projection_materialization_key_for_ownership(
                    ownership=ownership,
                    resolver=resolver,
                    context="Projection materialization",
                )
            )
        except RuntimeError:
            if allow_unresolved_projection_experiences:
                continue
            raise
        if not experience_name:
            raise RuntimeError(
                "Invalid experience compile plan: projection_experience_ownership[].name is required"
            )
        if not projection_key:
            raise RuntimeError(
                "Invalid experience compile plan: projection_experience_ownership[].projection is required"
            )

        default_branch_count = sum(
            1 for branch in ownership.branches if branch.is_default
        )
        if default_branch_count > 1:
            raise RuntimeError(
                "Invalid experience compile plan: projection experience allows at most one default branch "
                + f"(experience={experience_name!r}, defaults={default_branch_count})"
            )

        branches_seen: set[str] = set()
        branches: list[str] = []
        for branch in ownership.branches:
            branch_name = branch.name.strip()
            if not branch_name:
                raise RuntimeError(
                    "Invalid experience compile plan: projection_experience_ownership[].branches[].name is required"
                )
            branch_name_key = branch_name.casefold()
            if branch_name_key in branches_seen:
                raise RuntimeError(
                    "Invalid experience compile plan: duplicate projection branch declaration "
                    + f"(experience={experience_name!r}, branch={branch_name!r})"
                )
            branches_seen.add(branch_name_key)
            branches.append(branch_name)

        view_specs: list[ProjectionExperienceViewMaterializationSpec] = []
        view_keys_seen: set[tuple[str, str]] = set()
        for observable in ownership.observables:
            observable_key = observable.key.strip()
            if not observable_key:
                raise RuntimeError(
                    "Invalid experience compile plan: projection_experience_ownership[].observables[].key is required"
                )
            default_view_count = sum(1 for view in observable.views if view.is_default)
            if default_view_count != 1:
                raise RuntimeError(
                    "Invalid experience compile plan: observable requires exactly one default view "
                    + f"(experience={experience_name!r}, observable={observable_key!r}, defaults={default_view_count})"
                )
            for view in observable.views:
                view_key = view.key.strip()
                if not view_key:
                    raise RuntimeError(
                        "Invalid experience compile plan: projection_experience_ownership[].observables[].views[].key "
                        + "is required"
                    )
                view_spec_key = (observable_key.casefold(), view_key.casefold())
                if view_spec_key in view_keys_seen:
                    raise RuntimeError(
                        "Invalid experience compile plan: duplicate projection view declaration "
                        + (
                            f"(experience={experience_name!r}, observable={observable_key!r}, "
                            f"view={view_key!r})"
                        )
                    )
                view_keys_seen.add(view_spec_key)
                if view.api_view_ref is not None:
                    api_name, api_view_name = _split_api_view_ref(
                        view.api_view_ref,
                        context=(
                            "projection_experience_ownership[].observables[]."
                            + f"views[] api_view_ref for {experience_name!r} "
                            + f"{observable_key!r}.{view_key!r}"
                        ),
                    )
                    api_view_ref = view.api_view_ref
                    state_model_ref = view.state_model_ref
                else:
                    raise RuntimeError(
                        "Invalid experience compile plan: ProjectionExperienceView "
                        "must declare api_view_ref; Experience-generated View API "
                        "fallback is retired "
                        + (
                            f"(experience={experience_name!r}, "
                            f"observable={observable_key!r}, view={view_key!r})"
                        )
                    )
                view_specs.append(
                    ProjectionExperienceViewMaterializationSpec(
                        observable_key=observable_key,
                        view_key=view_key,
                        api_name=api_name,
                        api_view_name=api_view_name,
                        api_view_ref=api_view_ref,
                        state_model_ref=state_model_ref,
                        state_provider_ref=view.state_provider_ref,
                        invocation_actions=(
                            _resolve_projection_view_invocation_actions(
                                experience_name=experience_name,
                                observable_key=observable_key,
                                view_key=view_key,
                                api_view_ref=api_view_ref,
                                authored_actions=view.invocation_actions,
                                refs_by_view_action=api_view_action_refs_by_key,
                            )
                        ),
                    )
                )

        node_specs = _projection_node_materialization_specs_for_ownership(
            ownership=ownership,
            experience_name=experience_name,
        )
        spec = ProjectionExperienceMaterializationSpec(
            experience_name=experience_name,
            projection_key=projection_key,
            branches=tuple(sorted(branches, key=str.casefold)),
            views=tuple(
                sorted(
                    view_specs,
                    key=lambda item: (
                        item.observable_key.casefold(),
                        item.view_key.casefold(),
                        item.api_name.casefold(),
                        item.api_view_name.casefold(),
                        item.api_view_ref.casefold(),
                        (item.state_model_ref or "").casefold(),
                        (item.state_provider_ref or "").casefold(),
                    ),
                )
            ),
            nodes=node_specs,
            runtime_opgi_id=runtime_opgi_id,
        )
        experience_key = experience_name.casefold()
        existing = specs_by_experience.get(experience_key)
        if existing is not None and existing != spec:
            raise RuntimeError(
                "Invalid experience compile plan: duplicate projection experience ownership entries disagree "
                + f"for experience={experience_name!r}"
            )
        specs_by_experience[experience_key] = spec

    return tuple(
        sorted(
            specs_by_experience.values(),
            key=lambda item: item.experience_name.casefold(),
        )
    )


def build_projection_materialization_plan(
    *,
    lane: MaterializationLaneContext,
    specs: Sequence[ProjectionExperienceMaterializationSpec],
) -> MaterializationPlan:
    steps = tuple(
        MaterializationStep(
            step_id=f"projection:{spec.experience_name}",
            step_kind="experience.projection",
            payload=encode_projection_materialization_step_payload(spec=spec),
            commit_requested=True,
        )
        for spec in specs
    )
    return MaterializationPlan(
        module_id="experience",
        pipeline_id="experience.compile_plan.projection",
        lane=lane,
        steps=steps,
    )


def encode_projection_materialization_step_payload(
    *,
    spec: ProjectionExperienceMaterializationSpec,
) -> dict[str, object]:
    payload = _ProjectionMaterializationStepPayload(
        experience_name=spec.experience_name,
        projection_key=spec.projection_key,
        runtime_opgi_id=spec.runtime_opgi_id,
        branches=spec.branches,
        views=tuple(
            _ProjectionMaterializationViewPayload(
                observable_key=view.observable_key,
                view_key=view.view_key,
                api_name=view.api_name,
                api_view_name=view.api_view_name,
                api_view_ref=view.api_view_ref,
                state_model_ref=view.state_model_ref,
                state_provider_ref=view.state_provider_ref,
                invocation_actions=tuple(
                    _encode_projection_view_invocation_action(action=action)
                    for action in view.invocation_actions
                ),
            )
            for view in spec.views
        ),
        nodes=tuple(
            _ProjectionMaterializationNodePayload(
                name=node.name,
                node_ref=node.node_ref,
                identity_keys=node.identity_keys,
            )
            for node in spec.nodes
        ),
    )
    return cast(dict[str, object], payload.model_dump(mode="json"))


def _encode_projection_view_invocation_action(
    *,
    action: ExperienceProjectionViewInvocationActionOwnership,
) -> _ProjectionMaterializationViewInvocationActionPayload:
    if action.endpoint_ref is None or action.api_capability_endpoint_id is None:
        raise RuntimeError(
            "Projection invocation action requires resolved endpoint identity before "
            f"materialization encoding: action={action.key!r} source={action.source_path!r}"
        )
    return _ProjectionMaterializationViewInvocationActionPayload(
        key=action.key,
        api_view_capability_endpoint_id=action.api_view_capability_endpoint_id,
        endpoint_ref=action.endpoint_ref,
        api_capability_endpoint_id=action.api_capability_endpoint_id,
        sdk_operation_api_view_capability_endpoint_id=(
            action.sdk_operation_api_view_capability_endpoint_id
        ),
        sdk_operation_id=action.sdk_operation_id,
        source_path=action.source_path,
        label=action.label,
        receipt_policy=action.receipt_policy,
        confirmation_policy=action.confirmation_policy,
        optimistic_policy=action.optimistic_policy,
    )


def decode_projection_materialization_step_payload(
    payload: Mapping[str, object],
) -> ProjectionExperienceMaterializationSpec:
    try:
        step_payload = _ProjectionMaterializationStepPayload.model_validate(payload)
    except ValidationError as exc:
        raise RuntimeError(_format_step_payload_validation_error(exc=exc)) from exc

    branch_keys_seen: set[str] = set()
    normalized_branches: list[str] = []
    for branch in step_payload.branches:
        branch_key = branch.casefold()
        if branch_key in branch_keys_seen:
            raise RuntimeError(
                "Invalid experience compile plan: duplicate projection branch declaration "
                + f"(branch={branch!r})"
            )
        branch_keys_seen.add(branch_key)
        normalized_branches.append(branch)

    view_specs: list[ProjectionExperienceViewMaterializationSpec] = []
    view_keys_seen: set[tuple[str, str]] = set()
    for view in step_payload.views:
        view_spec_key = (view.observable_key.casefold(), view.view_key.casefold())
        if view_spec_key in view_keys_seen:
            raise RuntimeError(
                "Invalid experience compile plan: duplicate projection view declaration "
                + f"(observable={view.observable_key!r}, view={view.view_key!r})"
            )
        view_keys_seen.add(view_spec_key)
        view_specs.append(
            ProjectionExperienceViewMaterializationSpec(
                observable_key=view.observable_key,
                view_key=view.view_key,
                api_name=view.api_name,
                api_view_name=view.api_view_name,
                api_view_ref=view.api_view_ref,
                state_model_ref=view.state_model_ref,
                state_provider_ref=view.state_provider_ref,
                invocation_actions=tuple(
                    ExperienceProjectionViewInvocationActionOwnership(
                        key=action.key,
                        api_view_capability_endpoint_id=(
                            action.api_view_capability_endpoint_id
                        ),
                        endpoint_ref=action.endpoint_ref,
                        api_capability_endpoint_id=action.api_capability_endpoint_id,
                        sdk_operation_api_view_capability_endpoint_id=(
                            action.sdk_operation_api_view_capability_endpoint_id
                        ),
                        sdk_operation_id=action.sdk_operation_id,
                        source_path=action.source_path,
                        label=action.label,
                        receipt_policy=action.receipt_policy,
                        confirmation_policy=action.confirmation_policy,
                        optimistic_policy=action.optimistic_policy,
                    )
                    for action in view.invocation_actions
                ),
            )
        )

    node_specs: list[ProjectionExperienceNodeMaterializationSpec] = []
    for node_payload in step_payload.nodes:
        node_specs.append(
            ProjectionExperienceNodeMaterializationSpec(
                name=node_payload.name,
                node_ref=node_payload.node_ref,
                identity_keys=node_payload.identity_keys,
            )
        )

    return ProjectionExperienceMaterializationSpec(
        experience_name=step_payload.experience_name,
        projection_key=step_payload.projection_key,
        branches=tuple(normalized_branches),
        views=tuple(view_specs),
        nodes=tuple(node_specs),
        runtime_opgi_id=step_payload.runtime_opgi_id,
    )


async def materialize_experience_projection_ontology(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    api_compile_plan_payloads: Sequence[Mapping[str, object]] = (),
    phase_timings_s: dict[str, float] | None = None,
    allow_unresolved_projection_experiences: bool = False,
    semantic_materialization_context: Mapping[str, object] | None = None,
    source_experience_toml_path: Path | None = None,
) -> MaterializationRunReceipt | None:
    return await run_projection_materialization(
        index=index,
        actor_id=actor_id,
        lane=lane,
        compile_plan_payloads=compile_plan_payloads,
        api_compile_plan_payloads=api_compile_plan_payloads,
        phase_timings_s=phase_timings_s,
        allow_unresolved_projection_experiences=(
            allow_unresolved_projection_experiences
        ),
        semantic_materialization_context=semantic_materialization_context,
        source_experience_toml_path=source_experience_toml_path,
        dependencies=ProjectionMaterializationRunnerDependencies(
            phase_recorder=_record_optional_phase,
            resolve_projection_materialization_specs=(
                resolve_projection_materialization_specs
            ),
            build_projection_materialization_plan=(
                build_projection_materialization_plan
            ),
            decode_projection_materialization_step_payload=(
                decode_projection_materialization_step_payload
            ),
            resolve_projection_opgi_id_for_projection_key=(
                _resolve_projection_opgi_id_for_projection_key
            ),
            find_projection_graph_by_opgi_id=_find_projection_graph_by_opgi_id,
            build_observable_id_index=_build_observable_id_index,
            resolve_observable_id_for_projection_view=(
                _resolve_observable_id_for_projection_view
            ),
            projection_view_key=_projection_view_key,
            projection_view_invocation_action_snapshot=(
                _projection_view_invocation_action_snapshot
            ),
            projection_view_ids_by_projection_key_from_session=(
                _projection_experience_view_ids_by_projection_key_from_session
            ),
        ),
    )


async def materialize_experience_compile_plan_projections(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    planned_processes: Sequence[Mapping[str, object]],
) -> MaterializationRunReceipt | None:
    if not _has_planned_threads(planned_processes=planned_processes):
        return None

    repo_root = find_repo_root(start=runtime.manifest_path.parent)
    compile_plan_payloads = load_experience_compile_plan_payloads(repo_root=repo_root)
    return await materialize_experience_projection_ontology(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        compile_plan_payloads=compile_plan_payloads,
    )


def resolve_section_surface_materialization_specs(
    *,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    index: MetaGraphRuntimeIndex | None = None,
    external_projection_keys_by_experience_name: Mapping[str, str] | None = None,
    allow_unresolved_projection_experiences: bool = False,
) -> tuple[ProjectionExperienceSectionSurfaceMaterializationSpec, ...]:
    if not compile_plan_payloads:
        return ()

    try:
        projection_ownership = _decode_projection_experience_ownership(
            compile_plan_payloads=compile_plan_payloads
        )
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc

    graph_identity_keys_by_experience: dict[str, set[str]] = {}
    for payload in compile_plan_payloads:
        try:
            graph_plans = decode_graph_ontology_plan_payload(
                payload=_expect_list(
                    payload.get("graph_ontology", []), field_name="graph_ontology"
                )
            )
        except ValueError as exc:
            raise RuntimeError(str(exc)) from exc
        for plan in graph_plans:
            experience_key = plan.graph.experience.casefold()
            bucket = graph_identity_keys_by_experience.setdefault(experience_key, set())
            bucket.update(
                identity.key.casefold()
                for identity in plan.identities
                if identity.key.strip()
            )

    specs_by_experience: dict[
        str, ProjectionExperienceSectionSurfaceMaterializationSpec
    ] = {}
    profile_specs = resolve_environment_profile_materialization_specs(
        compile_plan_payloads=compile_plan_payloads,
        external_projection_keys_by_experience_name=(
            external_projection_keys_by_experience_name
        ),
    )
    layout_section_id_by_surface = _layout_config_section_config_ids_by_section_surface(
        profile_specs=profile_specs
    )
    layout_bindings_by_experience = _layout_graph_binding_specs_by_experience(
        profile_specs=profile_specs
    )
    resolver = (
        build_projection_runtime_resolver(index=index) if index is not None else None
    )
    for ownership in projection_ownership:
        if not ownership.section_surfaces:
            continue
        experience_name = ownership.name.strip()
        try:
            projection_key, runtime_opgi_id = (
                _projection_materialization_key_for_ownership(
                    ownership=ownership,
                    resolver=resolver,
                    context="ProjectionExperience section-surface materialization",
                )
            )
        except RuntimeError:
            if allow_unresolved_projection_experiences:
                continue
            raise
        if not experience_name:
            raise RuntimeError(
                "Invalid experience compile plan: projection_experience_ownership[].name is required"
            )
        if not projection_key:
            raise RuntimeError(
                "Invalid experience compile plan: projection_experience_ownership[].projection is required"
            )

        graph_identity_keys = graph_identity_keys_by_experience.get(
            experience_name.casefold(), set()
        )
        surfaces: list[ProjectionExperienceSectionSurfaceBindingSpec] = []
        surface_keys_seen: set[str] = set()
        for surface in ownership.section_surfaces:
            surface_key = surface.surface_key.strip()
            if not surface_key:
                raise RuntimeError(
                    "Invalid experience compile plan: projection_experience_ownership[].section_surfaces[].surface_key "
                    + "is required"
                )
            surface_key_casefolded = surface_key.casefold()
            if surface_key_casefolded in surface_keys_seen:
                raise RuntimeError(
                    "Invalid experience compile plan: duplicate section surface declaration "
                    + f"(experience={experience_name!r}, surface={surface_key!r})"
                )
            surface_keys_seen.add(surface_key_casefolded)
            if not surface.graph_identity_ref:
                raise RuntimeError(
                    "Invalid experience compile plan: section surface must resolve graph identity "
                    + f"(experience={experience_name!r}, surface={surface_key!r})"
                )
            if surface.graph_identity_ref.casefold() not in graph_identity_keys:
                raise RuntimeError(
                    "Invalid experience compile plan: section surface references unknown graph identity "
                    + f"(experience={experience_name!r}, surface={surface_key!r}, "
                    + f"graph_identity={surface.graph_identity_ref!r})"
                )
            if surface.node_identity_ref is not None:
                raise RuntimeError(
                    "Invalid experience compile plan: section surface must not declare node identity anchor "
                    + f"(experience={experience_name!r}, surface={surface_key!r}, "
                    + f"node_identity={surface.node_identity_ref!r})"
                )
            if surface.source_surface_key is not None:
                raise RuntimeError(
                    "Invalid experience compile plan: section surface must not declare source surface linkage "
                    + f"(experience={experience_name!r}, surface={surface_key!r}, "
                    + f"source_surface={surface.source_surface_key!r})"
                )
            surfaces.append(
                ProjectionExperienceSectionSurfaceBindingSpec(
                    surface_key=surface_key,
                    section_key=surface.section_key.strip(),
                    observable_key=surface.observable_key.strip(),
                    view_key=surface.view_key.strip(),
                    source_path=surface.source_path,
                    layout_config_section_config_id=layout_section_id_by_surface.get(
                        (experience_name.casefold(), surface_key.casefold())
                    ),
                    source_surface_key=None,
                    graph_identity_ref=(surface.graph_identity_ref or "").strip()
                    or None,
                    node_identity_ref=None,
                )
            )

        spec = ProjectionExperienceSectionSurfaceMaterializationSpec(
            experience_name=experience_name,
            projection_key=projection_key,
            surfaces=tuple(
                _sort_section_surface_binding_specs(
                    surfaces=surfaces, experience_name=experience_name
                )
            ),
            layout_bindings=layout_bindings_by_experience.get(
                experience_name.casefold(),
                (),
            ),
            runtime_opgi_id=runtime_opgi_id,
        )
        experience_key = experience_name.casefold()
        existing = specs_by_experience.get(experience_key)
        if existing is not None and existing != spec:
            raise RuntimeError(
                "Invalid experience compile plan: duplicate section-surface ownership entries disagree "
                + f"for experience={experience_name!r}"
            )
        specs_by_experience[experience_key] = spec

    return tuple(
        sorted(
            specs_by_experience.values(),
            key=lambda item: item.experience_name.casefold(),
        )
    )


def _layout_config_section_config_ids_by_section_surface(
    *,
    profile_specs: Sequence[EnvironmentProfileMaterializationSpec],
) -> dict[tuple[str, str], UUID]:
    ids_by_surface: dict[tuple[str, str], UUID] = {}
    for profile in profile_specs:
        for process in profile.process_configs:
            for thread in process.thread_configs:
                for layout in thread.layout_configs:
                    for section in layout.sections:
                        binding_key = (section.section_graph_binding_key or "").strip()
                        if not binding_key:
                            continue
                        key = (
                            section.projection_experience_name.casefold(),
                            binding_key.casefold(),
                        )
                        layout_section_id = stable_layout_config_section_config_id(
                            layout_config_id=layout.layout_config_id,
                            section_key=section.section_key,
                        )
                        existing = ids_by_surface.get(key)
                        if existing is not None and existing != layout_section_id:
                            raise RuntimeError(
                                "Invalid experience compile plan: section surface "
                                + "binding resolves to multiple layout sections "
                                + (
                                    f"(experience={section.projection_experience_name!r}, "
                                    f"binding={binding_key!r})"
                                )
                            )
                        ids_by_surface[key] = layout_section_id
    return ids_by_surface


def _layout_graph_binding_specs_by_experience(
    *,
    profile_specs: Sequence[EnvironmentProfileMaterializationSpec],
) -> dict[str, tuple[ProjectionExperienceLayoutGraphBindingSpec, ...]]:
    section_keys_by_layout: dict[tuple[str, UUID, str], set[str]] = {}
    layout_tokens_by_key: dict[tuple[str, UUID, str], tuple[str, UUID, str]] = {}
    for profile in profile_specs:
        for process in profile.process_configs:
            for thread in process.thread_configs:
                for layout in thread.layout_configs:
                    layout_binding_key = layout.layout_key.strip()
                    if not layout_binding_key:
                        continue
                    for section in layout.sections:
                        section_binding_key = (
                            section.section_graph_binding_key or ""
                        ).strip()
                        if not section_binding_key:
                            continue
                        experience_key = section.projection_experience_name.casefold()
                        layout_key = (
                            experience_key,
                            layout.layout_config_id,
                            layout_binding_key.casefold(),
                        )
                        layout_tokens_by_key[layout_key] = (
                            experience_key,
                            layout.layout_config_id,
                            layout_binding_key,
                        )
                        section_keys_by_layout.setdefault(layout_key, set()).add(
                            section_binding_key
                        )

    specs_by_experience: dict[str, list[ProjectionExperienceLayoutGraphBindingSpec]] = (
        {}
    )
    for layout_key in sorted(
        section_keys_by_layout,
        key=lambda item: (item[0], str(item[1]), item[2]),
    ):
        experience_key, layout_config_id, layout_binding_key = layout_tokens_by_key[
            layout_key
        ]
        specs_by_experience.setdefault(experience_key, []).append(
            ProjectionExperienceLayoutGraphBindingSpec(
                layout_config_id=layout_config_id,
                binding_key=layout_binding_key,
                section_graph_binding_keys=tuple(
                    sorted(
                        section_keys_by_layout[layout_key],
                        key=str.casefold,
                    )
                ),
            )
        )
    return {
        key: tuple(values)
        for key, values in sorted(specs_by_experience.items(), key=lambda item: item[0])
    }


def build_section_surface_materialization_plan(
    *,
    lane: MaterializationLaneContext,
    specs: Sequence[ProjectionExperienceSectionSurfaceMaterializationSpec],
) -> MaterializationPlan:
    steps = tuple(
        MaterializationStep(
            step_id=f"section_surface:{spec.experience_name}",
            step_kind="experience.section_surface",
            payload=encode_section_surface_materialization_step_payload(spec=spec),
            commit_requested=True,
        )
        for spec in specs
    )
    return MaterializationPlan(
        module_id="experience",
        pipeline_id="experience.compile_plan.section_surface",
        lane=lane,
        steps=steps,
    )


def encode_section_surface_materialization_step_payload(
    *,
    spec: ProjectionExperienceSectionSurfaceMaterializationSpec,
) -> dict[str, object]:
    payload = _ProjectionSectionSurfaceMaterializationStepPayload(
        experience_name=spec.experience_name,
        projection_key=spec.projection_key,
        runtime_opgi_id=spec.runtime_opgi_id,
        layout_bindings=tuple(
            _ProjectionLayoutGraphBindingPayload(
                layout_config_id=layout_binding.layout_config_id,
                binding_key=layout_binding.binding_key,
                section_graph_binding_keys=(layout_binding.section_graph_binding_keys),
            )
            for layout_binding in spec.layout_bindings
        ),
        surfaces=tuple(
            _ProjectionSectionSurfaceBindingPayload(
                surface_key=surface.surface_key,
                section_key=surface.section_key,
                observable_key=surface.observable_key,
                view_key=surface.view_key,
                source_path=surface.source_path,
                layout_config_section_config_id=surface.layout_config_section_config_id,
                source_surface_key=surface.source_surface_key,
                graph_identity_ref=surface.graph_identity_ref,
                node_identity_ref=surface.node_identity_ref,
            )
            for surface in spec.surfaces
        ),
    )
    return cast(dict[str, object], payload.model_dump(mode="json"))


def decode_section_surface_materialization_step_payload(
    payload: Mapping[str, object],
) -> ProjectionExperienceSectionSurfaceMaterializationSpec:
    try:
        step_payload = (
            _ProjectionSectionSurfaceMaterializationStepPayload.model_validate(payload)
        )
    except ValidationError as exc:
        raise RuntimeError(
            _format_step_payload_validation_error(exc=exc, prefix="section_surface")
        ) from exc

    surfaces = [
        ProjectionExperienceSectionSurfaceBindingSpec(
            surface_key=surface.surface_key,
            section_key=surface.section_key,
            observable_key=surface.observable_key,
            view_key=surface.view_key,
            source_path=surface.source_path,
            layout_config_section_config_id=surface.layout_config_section_config_id,
            source_surface_key=surface.source_surface_key,
            graph_identity_ref=surface.graph_identity_ref,
            node_identity_ref=surface.node_identity_ref,
        )
        for surface in step_payload.surfaces
    ]
    layout_bindings = [
        ProjectionExperienceLayoutGraphBindingSpec(
            layout_config_id=layout_binding.layout_config_id,
            binding_key=layout_binding.binding_key,
            section_graph_binding_keys=tuple(layout_binding.section_graph_binding_keys),
        )
        for layout_binding in step_payload.layout_bindings
    ]
    return ProjectionExperienceSectionSurfaceMaterializationSpec(
        experience_name=step_payload.experience_name,
        projection_key=step_payload.projection_key,
        surfaces=tuple(
            _sort_section_surface_binding_specs(
                surfaces=surfaces,
                experience_name=step_payload.experience_name,
            )
        ),
        layout_bindings=tuple(layout_bindings),
        runtime_opgi_id=step_payload.runtime_opgi_id,
    )


async def materialize_experience_section_surface_ontology(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    external_projection_keys_by_experience_name: Mapping[str, str] | None = None,
    allow_unresolved_projection_experiences: bool = False,
) -> MaterializationRunReceipt | None:
    return await run_section_surface_materialization(
        index=index,
        actor_id=actor_id,
        lane=lane,
        compile_plan_payloads=compile_plan_payloads,
        external_projection_keys_by_experience_name=(
            external_projection_keys_by_experience_name
        ),
        allow_unresolved_projection_experiences=(
            allow_unresolved_projection_experiences
        ),
        dependencies=SectionSurfaceMaterializationRunnerDependencies(
            resolve_section_surface_materialization_specs=(
                resolve_section_surface_materialization_specs
            ),
            build_section_surface_materialization_plan=(
                build_section_surface_materialization_plan
            ),
            decode_section_surface_materialization_step_payload=(
                decode_section_surface_materialization_step_payload
            ),
            resolve_projection_opgi_id_for_projection_key=(
                _resolve_projection_opgi_id_for_projection_key
            ),
            find_projection_graph_by_opgi_id=_find_projection_graph_by_opgi_id,
            build_observable_id_index=_build_observable_id_index,
            resolve_observable_id_for_projection_view=(
                _resolve_observable_id_for_projection_view
            ),
            projection_view_key=_projection_view_key,
            projection_experience_ids_by_name_and_opgi_from_session=(
                _projection_experience_ids_by_name_and_opgi_from_session
            ),
            projection_experience_view_ids_by_projection_key_from_session=(
                _projection_experience_view_ids_by_projection_key_from_session
            ),
        ),
    )


def _projection_experience_ids_by_name_and_opgi_from_session(
    *,
    projection_session: Session,
) -> dict[tuple[str, UUID], UUID]:
    experience_ids_by_name_and_opgi: dict[tuple[str, UUID], UUID] = {}
    for obj in projection_session.imap_all_objects():
        if not isinstance(obj, ProjectionExperience) or obj.id is None:
            continue
        name = (obj.name or "").strip()
        object_projection_graph_identity_id = getattr(
            obj, "object_projection_graph_identity_id", None
        )
        if not name or object_projection_graph_identity_id is None:
            continue
        experience_ids_by_name_and_opgi[
            (name.casefold(), object_projection_graph_identity_id)
        ] = obj.id
    return experience_ids_by_name_and_opgi


def _projection_experience_view_ids_by_projection_key_from_session(
    *,
    projection_session: Session,
) -> dict[tuple[UUID, str], UUID]:
    view_ids_by_projection_key: dict[tuple[UUID, str], UUID] = {}
    for obj in projection_session.imap_all_objects():
        if not isinstance(obj, ProjectionExperienceView) or obj.id is None:
            continue
        projection_experience_id = getattr(obj, "projection_experience_id", None)
        name = (obj.name or "").strip()
        if projection_experience_id is None or not name:
            continue
        key = (projection_experience_id, name.casefold())
        existing_view_id = view_ids_by_projection_key.get(key)
        if existing_view_id is not None and existing_view_id != obj.id:
            raise RuntimeError(
                "Section-surface materialization found duplicate committed "
                + "ProjectionExperienceView keys "
                + f"(projection_experience_id={projection_experience_id}, "
                + f"view={name!r})"
            )
        view_ids_by_projection_key[key] = obj.id
    return view_ids_by_projection_key


async def materialize_experience_compile_plan_section_surfaces(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    planned_processes: Sequence[Mapping[str, object]],
) -> MaterializationRunReceipt | None:
    if not _has_planned_threads(planned_processes=planned_processes):
        return None

    repo_root = find_repo_root(start=runtime.manifest_path.parent)
    compile_plan_payloads = load_experience_compile_plan_payloads(repo_root=repo_root)
    return await materialize_experience_section_surface_ontology(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        compile_plan_payloads=compile_plan_payloads,
    )


async def materialize_experience_compile_plan_graphs(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    planned_processes: Sequence[Mapping[str, object]],
) -> MaterializationRunReceipt | None:
    if not _has_planned_threads(planned_processes=planned_processes):
        return None

    repo_root = find_repo_root(start=runtime.manifest_path.parent)
    compile_plan_payloads = load_experience_compile_plan_payloads(repo_root=repo_root)
    return await materialize_experience_graph_ontology(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        compile_plan_payloads=compile_plan_payloads,
    )


def _normalize_symbol(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.strip()


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


def _resolve_projection_view_invocation_actions(
    *,
    experience_name: str,
    observable_key: str,
    view_key: str,
    api_view_ref: str,
    authored_actions: Sequence[ExperienceProjectionViewInvocationActionOwnership],
    refs_by_view_action: Mapping[
        tuple[str, str], _ApiViewCapabilityEndpointMaterializationRef
    ],
) -> tuple[ExperienceProjectionViewInvocationActionOwnership, ...]:
    refs_for_view = tuple(
        sorted(
            (
                ref
                for key, ref in refs_by_view_action.items()
                if key[0] == api_view_ref.casefold()
            ),
            key=lambda item: (item.action_key.casefold(), item.endpoint_ref.casefold()),
        )
    )
    authored_by_key = {action.key.casefold(): action for action in authored_actions}
    if len(authored_by_key) != len(tuple(authored_actions)):
        raise RuntimeError(
            "Invalid experience compile plan: duplicate projection view action metadata "
            + (
                f"(experience={experience_name!r}, observable={observable_key!r}, "
                f"view={view_key!r})"
            )
        )

    selected_refs: tuple[_ApiViewCapabilityEndpointMaterializationRef, ...]
    if authored_actions:
        selected: list[_ApiViewCapabilityEndpointMaterializationRef] = []
        for authored in authored_actions:
            ref = refs_by_view_action.get(
                (api_view_ref.casefold(), authored.key.casefold())
            )
            if ref is None:
                raise RuntimeError(
                    "Invalid experience compile plan: projection view action metadata "
                    + "does not match an API-owned ApiViewCapabilityEndpoint "
                    + (
                        f"(experience={experience_name!r}, observable={observable_key!r}, "
                        f"view={view_key!r}, api_view_ref={api_view_ref!r}, "
                        f"action={authored.key!r})"
                    )
                )
            selected.append(ref)
        selected_refs = tuple(selected)
    else:
        selected_refs = refs_for_view

    resolved: list[ExperienceProjectionViewInvocationActionOwnership] = []
    for ref in selected_refs:
        authored = authored_by_key.get(ref.action_key.casefold())
        resolved.append(
            ExperienceProjectionViewInvocationActionOwnership(
                key=ref.action_key,
                endpoint_ref=ref.endpoint_ref,
                api_capability_endpoint_id=ref.api_capability_endpoint_id,
                source_path=(authored.source_path if authored else ref.source_path),
                label=(
                    authored.label
                    if authored is not None and authored.label is not None
                    else ref.description
                ),
                receipt_policy=authored.receipt_policy if authored else None,
                confirmation_policy=authored.confirmation_policy if authored else None,
                optimistic_policy=authored.optimistic_policy if authored else None,
            )
        )
    return tuple(resolved)


def _api_view_capability_endpoint_refs_by_view_action(
    *,
    api_compile_plan_payloads: Sequence[Mapping[str, object]],
) -> Mapping[tuple[str, str], _ApiViewCapabilityEndpointMaterializationRef]:
    refs_by_key: dict[tuple[str, str], _ApiViewCapabilityEndpointMaterializationRef] = (
        {}
    )
    for payload_index, payload in enumerate(api_compile_plan_payloads):
        for api_index, api_raw in enumerate(
            _expect_list(
                payload.get("api_ownership", []),
                field_name=f"api_compile_plan[{payload_index}].api_ownership",
            )
        ):
            api_field = f"api_compile_plan[{payload_index}].api_ownership[{api_index}]"
            api_row = _expect_mapping(api_raw, field_name=api_field)
            api_name = _expect_nonempty_text(
                api_row.get("name"), field_name=f"{api_field}.name"
            )
            for view_index, view_raw in enumerate(
                _expect_list(
                    api_row.get("views", []),
                    field_name=f"{api_field}.views",
                )
            ):
                view_field = f"{api_field}.views[{view_index}]"
                view_row = _expect_mapping(view_raw, field_name=view_field)
                view_name = _expect_nonempty_text(
                    view_row.get("name"), field_name=f"{view_field}.name"
                )
                view_ref = _expect_nonempty_text(
                    view_row.get("view_ref"), field_name=f"{view_field}.view_ref"
                )
                for action_index, action_raw in enumerate(
                    _expect_list(
                        view_row.get("capability_endpoints", []),
                        field_name=f"{view_field}.capability_endpoints",
                    )
                ):
                    action_field = f"{view_field}.capability_endpoints[{action_index}]"
                    action_row = _expect_mapping(action_raw, field_name=action_field)
                    action_key = _expect_nonempty_text(
                        action_row.get("action_key"),
                        field_name=f"{action_field}.action_key",
                    )
                    endpoint_ref = _expect_nonempty_text(
                        action_row.get("endpoint_ref"),
                        field_name=f"{action_field}.endpoint_ref",
                    )
                    api_capability_endpoint_id = (
                        _stable_api_capability_endpoint_id_for_endpoint_ref(
                            endpoint_ref=endpoint_ref,
                            expected_api_name=api_name,
                            context=action_field,
                        )
                    )
                    ref = _ApiViewCapabilityEndpointMaterializationRef(
                        api_name=api_name,
                        view_name=view_name,
                        view_ref=view_ref,
                        action_key=action_key,
                        endpoint_ref=endpoint_ref,
                        source_path=_expect_nonempty_text(
                            action_row.get("source_path"),
                            field_name=f"{action_field}.source_path",
                        ),
                        api_capability_endpoint_id=api_capability_endpoint_id,
                        description=_optional_payload_token(
                            action_row.get("description")
                        ),
                    )
                    key = (view_ref.casefold(), action_key.casefold())
                    existing = refs_by_key.get(key)
                    if existing is not None and existing != ref:
                        raise RuntimeError(
                            "Invalid API compile plan: duplicate ApiViewCapabilityEndpoint "
                            + "entries disagree "
                            + f"(view_ref={view_ref!r}, action_key={action_key!r})"
                        )
                    refs_by_key[key] = ref
    return refs_by_key


def _stable_api_capability_endpoint_id_for_endpoint_ref(
    *,
    endpoint_ref: str,
    expected_api_name: str,
    context: str,
) -> UUID:
    parts = [part.strip() for part in endpoint_ref.split(".") if part.strip()]
    if len(parts) != 3:
        raise RuntimeError(
            "Invalid API compile plan: ApiViewCapabilityEndpoint.endpoint_ref must use "
            + f"`api.capability.endpoint` ({context}, endpoint_ref={endpoint_ref!r})"
        )
    api_name, capability_name, endpoint_name = parts
    if api_name.casefold() != expected_api_name.casefold():
        raise RuntimeError(
            "Invalid API compile plan: ApiViewCapabilityEndpoint.endpoint_ref api name "
            + "does not match owning API "
            + f"({context}, api_name={expected_api_name!r}, endpoint_ref={endpoint_ref!r})"
        )
    api_id = stable_api_id(name=api_name)
    api_capability_id = stable_api_capability_id(
        api_id=api_id,
        name=capability_name,
    )
    return stable_api_capability_endpoint_id(
        api_capability_id=api_capability_id,
        name=endpoint_name,
    )


def _split_api_view_ref(value: str, *, context: str) -> tuple[str, str]:
    token = (value or "").strip()
    api_name, separator, view_name = token.rpartition(".")
    if not separator or not api_name.strip() or not view_name.strip():
        raise RuntimeError(
            "Invalid experience compile plan: api_view_ref must use "
            f"'<api>.<view>' form ({context}, api_view_ref={value!r})"
        )
    return api_name.strip(), view_name.strip()


def _sort_section_surface_binding_specs(
    *,
    surfaces: Sequence[ProjectionExperienceSectionSurfaceBindingSpec],
    experience_name: str,
) -> list[ProjectionExperienceSectionSurfaceBindingSpec]:
    surface_by_key = {
        surface.surface_key.casefold(): surface
        for surface in surfaces
        if surface.surface_key.strip()
    }
    pending = list(surfaces)
    ordered: list[ProjectionExperienceSectionSurfaceBindingSpec] = []
    resolved_surface_keys: set[str] = set()

    while pending:
        progressed = False
        still_pending: list[ProjectionExperienceSectionSurfaceBindingSpec] = []
        for surface in pending:
            source_surface_key = (surface.source_surface_key or "").strip().casefold()
            if source_surface_key and source_surface_key not in surface_by_key:
                raise RuntimeError(
                    "Invalid experience compile plan: section surface references unknown source surface "
                    + f"(experience={experience_name!r}, surface={surface.surface_key!r}, "
                    + f"source_surface={surface.source_surface_key!r})"
                )
            if source_surface_key and source_surface_key not in resolved_surface_keys:
                still_pending.append(surface)
                continue
            ordered.append(surface)
            resolved_surface_keys.add(surface.surface_key.casefold())
            progressed = True
        if progressed:
            pending = still_pending
            continue
        unresolved = [surface.surface_key for surface in pending]
        raise RuntimeError(
            "Invalid experience compile plan: section surface source dependency cycle "
            + f"(experience={experience_name!r}, surfaces={unresolved!r})"
        )

    return ordered


def _resolve_projection_opgi_id_for_projection_key(
    *,
    opgi_by_key_casefolded: Mapping[str, tuple[UUID, set[str] | frozenset[str]]],
    projection_key: str,
    experience_name: str,
    runtime_opgi_id: UUID | None = None,
) -> UUID:
    if runtime_opgi_id is not None:
        for opgi_id, _view_keys in opgi_by_key_casefolded.values():
            if opgi_id == runtime_opgi_id:
                return runtime_opgi_id
        raise RuntimeError(
            "Projection materialization resolved runtime OPGI was not found in OPGI catalog "
            + f"(experience={experience_name!r}, projection={projection_key!r}, "
            + f"runtime_opgi_id={runtime_opgi_id})"
        )

    normalized_projection_key = projection_key.strip().casefold()
    if not normalized_projection_key:
        raise RuntimeError(
            "Projection materialization requires projection key "
            + f"(experience={experience_name!r})"
        )

    exact = opgi_by_key_casefolded.get(normalized_projection_key)
    if exact is not None:
        return exact[0]

    suffix_matches = [
        entry[0]
        for key, entry in opgi_by_key_casefolded.items()
        if key.rsplit(":", 1)[-1] == normalized_projection_key
    ]
    if len(suffix_matches) == 1:
        return suffix_matches[0]
    if len(suffix_matches) > 1:
        raise RuntimeError(
            "Projection materialization projection key resolved ambiguously across OPGI keys "
            + f"(experience={experience_name!r}, projection={projection_key!r})"
        )
    raise RuntimeError(
        "Projection materialization projection key was not found in OPGI catalog "
        + f"(experience={experience_name!r}, projection={projection_key!r})"
    )


def _projection_view_key(*, observable_key: str, view_key: str) -> str:
    normalized_observable_key = (observable_key or "").strip()
    normalized_view_key = (view_key or "").strip()
    if not normalized_observable_key or not normalized_view_key:
        raise RuntimeError(
            "ProjectionExperienceView materialization requires non-empty observable and view keys"
        )
    return f"{normalized_observable_key}.{normalized_view_key}"


def _projection_view_invocation_action_snapshot(
    *,
    action: ExperienceProjectionViewInvocationActionOwnership,
    api_view_id: UUID,
    experience_name: str,
    observable_key: str,
    view_key: str,
) -> ExperienceProjectionViewInvocationActionSnapshot:
    if action.api_capability_endpoint_id is None:
        raise RuntimeError(
            "ProjectionExperienceView invocation action requires resolved "
            + "api_capability_endpoint_id "
            + (
                f"(experience={experience_name!r}, observable={observable_key!r}, "
                f"view={view_key!r}, action={action.key!r})"
            )
        )
    api_view_capability_endpoint_id = stable_api_view_capability_endpoint_id(
        api_view_id=api_view_id,
        api_capability_endpoint_id=action.api_capability_endpoint_id,
    )
    if (
        action.api_view_capability_endpoint_id is not None
        and action.api_view_capability_endpoint_id != api_view_capability_endpoint_id
    ):
        raise RuntimeError(
            "ProjectionExperienceView invocation action resolved mismatched "
            + "api_view_capability_endpoint_id "
            + (
                f"(experience={experience_name!r}, observable={observable_key!r}, "
                f"view={view_key!r}, action={action.key!r})"
            )
        )
    endpoint_ref = (action.endpoint_ref or "").strip()
    if not endpoint_ref:
        raise RuntimeError(
            "ProjectionExperienceView invocation action requires resolved endpoint_ref "
            + (
                f"(experience={experience_name!r}, observable={observable_key!r}, "
                f"view={view_key!r}, action={action.key!r})"
            )
        )

    return ExperienceProjectionViewInvocationActionSnapshot(
        api_view_capability_endpoint_id=api_view_capability_endpoint_id,
        action_key=action.key,
        sdk_operation_api_view_capability_endpoint_id=(
            action.sdk_operation_api_view_capability_endpoint_id
        ),
        api_capability_endpoint_id=action.api_capability_endpoint_id,
        sdk_operation_id=action.sdk_operation_id,
        label=action.label,
        receipt_policy=action.receipt_policy,
        confirmation_policy=action.confirmation_policy,
        optimistic_policy=action.optimistic_policy,
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
        "Projection materialization could not resolve projection graph for OPGI "
        + f"{object_projection_graph_identity_id}"
    )


def _build_observable_id_index(
    *, index: MetaGraphRuntimeIndex, opg: ObjectProjectionGraph
) -> dict[str, UUID]:
    observable_id_by_key: dict[str, UUID] = {}
    opgi = cast(Any, getattr(opg, "ObjectProjectionGraphIdentity", None))
    if opgi is None:
        _ocgi, resolved_opgi = resolve_meta_graph_ocgi_opgi(
            index=index, projection_hash=opg.projection_hash
        )
        opgi = resolved_opgi
    observables_raw = (
        getattr(opgi, "object_projection_graph_observables", ())
        if opgi is not None
        else ()
    )
    observables = (
        tuple(observables_raw) if isinstance(observables_raw, (list, tuple)) else ()
    )
    for observable in observables:
        observable_key = (observable.key or "").strip()
        if not observable_key:
            continue
        observable_id_by_key[observable_key.casefold()] = observable.id
    return observable_id_by_key


def _resolve_observable_id_for_projection_view(
    *,
    observable_id_by_key: Mapping[str, UUID],
    object_projection_graph_identity_id: UUID,
    observable_key: str,
    experience_name: str,
    projection_key: str,
) -> UUID:
    normalized_observable_key = observable_key.strip().casefold()
    if not normalized_observable_key:
        raise RuntimeError(
            "Projection materialization requires observable key "
            + f"(experience={experience_name!r}, projection={projection_key!r})"
        )

    exact = observable_id_by_key.get(normalized_observable_key)
    if exact is not None:
        return exact

    suffix_matches = [
        observable_id
        for candidate_key, observable_id in observable_id_by_key.items()
        if candidate_key.rsplit(":", 1)[-1] == normalized_observable_key
    ]
    if len(suffix_matches) == 1:
        return suffix_matches[0]
    if len(suffix_matches) > 1:
        raise RuntimeError(
            "Projection materialization observable key resolved ambiguously "
            + (
                f"(experience={experience_name!r}, projection={projection_key!r}, "
                f"observable={observable_key!r})"
            )
        )
    return stable_object_projection_graph_observable_id(
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        observable_key=normalized_observable_key,
    )


def _resolve_projection_hash_for_class_suffix(
    *,
    index: MetaGraphRuntimeIndex,
    class_name_suffix: str,
    preferred_projection_name: str | None = None,
) -> str:
    class_config_id = ocg_support.resolve_class_config_id(
        index=index, class_name_suffix=class_name_suffix
    )
    candidate_hashes: list[str] = []
    for opg in index.ocg.object_projection_graphs:
        nodes = getattr(opg, "object_projection_graph_nodes", []) or []
        if any(
            getattr(node, "class_config_id", None) == class_config_id for node in nodes
        ):
            candidate_hashes.append(opg.projection_hash)

    if not candidate_hashes:
        raise RuntimeError(
            "Could not resolve projection hash for class suffix "
            + f"{class_name_suffix!r} (class_config_id={class_config_id})"
        )

    normalized_preferred_name = (preferred_projection_name or "").strip().casefold()
    if normalized_preferred_name:
        preferred_hashes: list[str] = []
        for projection_hash in candidate_hashes:
            projection_graph = index.opg_by_hash.get(projection_hash)
            projection_name = (
                (projection_graph.name or "").strip().casefold()
                if projection_graph is not None
                else ""
            )
            if projection_name == normalized_preferred_name:
                preferred_hashes.append(projection_hash)
        if len(preferred_hashes) == 1:
            return preferred_hashes[0]
        if len(preferred_hashes) > 1:
            raise RuntimeError(
                "Projection hash resolved ambiguously for class suffix and preferred projection name "
                + f"(class_name_suffix={class_name_suffix!r}, preferred_projection_name={preferred_projection_name!r})"
            )

    if len(candidate_hashes) > 1:
        raise RuntimeError(
            "Projection hash resolved ambiguously for class suffix "
            + f"{class_name_suffix!r} (candidates={candidate_hashes!r})"
        )
    return candidate_hashes[0]


def _has_planned_threads(*, planned_processes: Sequence[Mapping[str, object]]) -> bool:
    for process_plan in planned_processes:
        threads = process_plan.get("threads")
        if isinstance(threads, list) and threads:
            return True
    return False
