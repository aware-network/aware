from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, cast
from uuid import UUID, NAMESPACE_URL, uuid5

from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_experience import stable_ids as experience_stable_ids
from aware_experience.graph.materialization.service import (
    ProjectionExperienceNodeMaterializationSpec,
    build_projection_node_snapshots_for_materialization,
)
from aware_experience.materialization.branches import (
    derive_experience_reference_branch_id,
)
from aware_experience.materialization.compile_plan_payloads import (
    _expect_list,
    _expect_mapping,
    _optional_payload_token,
    _required_step_payload_token,
)
from aware_experience.materialization.environment_profile_materialization import (
    _projection_keys_by_experience_name_from_catalog,
)
from aware_experience.materialization.snapshot_commit import (
    _build_primitive_attribute_config,
    _commit_snapshot,
    _remember,
)
from aware_experience.environment_profile.runtime_support import ocg_support
from aware_environment.environment_config.stable_ids import stable_environment_config_id
from aware_environment_ontology import stable_ids as environment_stable_ids
from aware_experience_ontology.action.action_experience import ActionExperience
from aware_experience_ontology.action.action_experience_invocation import (
    ActionExperienceInvocation,
)
from aware_experience_ontology.action.action_experience_invocation_request_field import (
    ActionExperienceInvocationRequestField,
)
from aware_experience_ontology.environment.environment_experience_event import (
    EnvironmentExperienceEvent,
)
from aware_experience_ontology.environment.environment_experience_event_action import (
    EnvironmentExperienceEventAction,
)
from aware_experience_ontology.environment.environment_experience_event_node_scope import (
    EnvironmentExperienceEventNodeScope,
)
from aware_experience_ontology.environment.environment_experience_profile_config import (
    EnvironmentExperienceProfileConfig,
)
from aware_experience_ontology.environment.environment_experience_projection import (
    EnvironmentExperienceProjection,
)
from aware_experience_ontology.invocation.experience_invocation_action_config import (
    ExperienceInvocationActionConfig,
)
from aware_experience_ontology.invocation.experience_invocation_action_target_kind import (
    ExperienceInvocationActionTargetKind,
)
from aware_meta.graph.config.stable_ids import stable_attribute_config_id
from aware_meta_ontology.stable_ids import stable_object_instance_graph_id
from aware_meta.materialization import (
    MaterializationExecutor,
    MaterializationLaneContext,
    MaterializationPlan,
    MaterializationRunReceipt,
    MaterializationStep,
    MaterializationStepResult,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_orm.models.base_model import BaseORMModel
from aware_reactivity_ontology.stable_ids import (
    stable_action_config_id,
    stable_condition_config_id,
    stable_event_config_condition_config_id,
    stable_event_config_id,
)


_EXPERIENCE_ACTIVATION_PROFILE_CONFIG_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/activation/profile-config-snapshot/v1",
)
_EXPERIENCE_ACTIVATION_ACTION_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/activation/action-snapshot/v1",
)
_EXPERIENCE_ACTIVATION_INVOCATION_CONFIG_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/activation/invocation-config-snapshot/v1",
)


class ActionMaterializationSpec(Protocol):
    action_name: str
    program_keys: tuple[str, ...]
    is_dependency: bool


class ConnectorInvocationRequestFieldMaterializationSpec(Protocol):
    attribute: str
    source_ref: str
    required: bool


class ConnectorInvocationActionConfigMaterializationSpec(Protocol):
    materialized_action_key: str
    target_ref: str
    action_kind: str
    request_fields: Sequence[ConnectorInvocationRequestFieldMaterializationSpec]


class SensorConfigMaterializationSpec(Protocol):
    sensor_key: str
    invocation_action_configs: Sequence[
        ConnectorInvocationActionConfigMaterializationSpec
    ]


class ActuatorConfigMaterializationSpec(Protocol):
    actuator_key: str
    invocation_action_configs: Sequence[
        ConnectorInvocationActionConfigMaterializationSpec
    ]


class ConnectorConfigMaterializationSpec(Protocol):
    connector_key: str
    projection_experience_name: str
    sensor_configs: Sequence[SensorConfigMaterializationSpec]
    actuator_configs: Sequence[ActuatorConfigMaterializationSpec]


class EnvironmentProfileThreadProjectionMaterializationSpec(Protocol):
    projection_experience_name: str


class EnvironmentProfileThreadLayoutSectionMaterializationSpec(Protocol):
    projection_experience_name: str


class EnvironmentProfileThreadLayoutMaterializationSpec(Protocol):
    sections: Sequence[EnvironmentProfileThreadLayoutSectionMaterializationSpec]


class EnvironmentProfileThreadMaterializationSpec(Protocol):
    projection_experiences: Sequence[
        EnvironmentProfileThreadProjectionMaterializationSpec
    ]
    layout_configs: Sequence[EnvironmentProfileThreadLayoutMaterializationSpec]


class EnvironmentProfileProcessMaterializationSpec(Protocol):
    thread_configs: Sequence[EnvironmentProfileThreadMaterializationSpec]


class EnvironmentProfileViewEventTransitionMaterializationSpec(Protocol):
    source_projection_experience_name: str
    target_projection_experience_name: str


class EnvironmentProfileMaterializationSpec(Protocol):
    fqn_prefix: str
    experience_name: str
    key: str
    title: str | None
    description: str | None
    narrative: str | None
    process_configs: Sequence[EnvironmentProfileProcessMaterializationSpec]
    view_event_transitions: Sequence[
        EnvironmentProfileViewEventTransitionMaterializationSpec
    ]


class ProjectionExperienceMaterializationSpec(Protocol):
    experience_name: str
    projection_key: str
    runtime_opgi_id: UUID | None
    nodes: Sequence[ProjectionExperienceNodeMaterializationSpec]


class ResolveEnvironmentProfileSpecs(Protocol):
    def __call__(
        self,
        *,
        compile_plan_payloads: Sequence[Mapping[str, object]],
        external_projection_keys_by_experience_name: Mapping[str, str] | None = None,
    ) -> Sequence[EnvironmentProfileMaterializationSpec]: ...


class ProjectionExperienceCatalogLoader(Protocol):
    async def __call__(
        self,
        *,
        index: MetaGraphRuntimeIndex,
        branch_ids: Sequence[UUID],
    ) -> Mapping[str, object]: ...


class ResolveActionSpecs(Protocol):
    def __call__(
        self,
        *,
        compile_plan_payloads: Sequence[Mapping[str, object]],
    ) -> Sequence[ActionMaterializationSpec]: ...


class ResolveConnectorSpecs(Protocol):
    def __call__(
        self,
        *,
        compile_plan_payloads: Sequence[Mapping[str, object]],
    ) -> Sequence[ConnectorConfigMaterializationSpec]: ...


class ResolveActivationTargetSpecs(Protocol):
    def __call__(
        self,
        *,
        compile_plan_payloads: Sequence[Mapping[str, object]],
    ) -> Sequence[ConnectorConfigMaterializationSpec]: ...


class ResolveProjectionSpecs(Protocol):
    def __call__(
        self,
        *,
        compile_plan_payloads: Sequence[Mapping[str, object]],
        api_compile_plan_payloads: Sequence[Mapping[str, object]],
        index: MetaGraphRuntimeIndex,
        allow_unresolved_projection_experiences: bool,
    ) -> Sequence[ProjectionExperienceMaterializationSpec]: ...


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


class ConnectorInvocationActionTargetIds(Protocol):
    def __call__(
        self,
        *,
        action: ConnectorInvocationActionConfigMaterializationSpec,
        connector_key: str,
        surface_kind: str,
        surface_key: str,
    ) -> tuple[ExperienceInvocationActionTargetKind, UUID | None, UUID | None]: ...


class NormalizeSymbol(Protocol):
    def __call__(self, raw: str) -> str: ...


@dataclass(frozen=True, slots=True)
class ActivationTopologyMaterializationDependencies:
    load_projection_experience_catalog: ProjectionExperienceCatalogLoader
    resolve_environment_profile_materialization_specs: ResolveEnvironmentProfileSpecs
    resolve_action_materialization_specs: ResolveActionSpecs
    resolve_connector_config_materialization_specs: ResolveConnectorSpecs
    resolve_activation_target_materialization_specs: ResolveActivationTargetSpecs
    resolve_projection_materialization_specs: ResolveProjectionSpecs
    resolve_projection_opgi_id_for_projection_key: ResolveProjectionOpgiId
    find_projection_graph_by_opgi_id: FindProjectionGraphByOpgiId
    connector_invocation_action_target_ids: ConnectorInvocationActionTargetIds
    normalize_symbol: NormalizeSymbol


@dataclass(frozen=True, slots=True)
class _EndpointRequestAttributeRef:
    endpoint_ref: str
    class_config_id: UUID
    class_ref: str
    attributes_by_name: Mapping[str, UUID]


@dataclass(frozen=True, slots=True)
class _ActivationInvocationTargetSpec:
    materialized_action_key: str
    target_ref: str
    target_kind: ExperienceInvocationActionTargetKind
    api_capability_endpoint_id: UUID | None
    sdk_operation_id: UUID | None
    experience_invocation_action_config_id: UUID
    request_fields: tuple[ConnectorInvocationRequestFieldMaterializationSpec, ...]


@dataclass(frozen=True, slots=True)
class _ActivationTopologyStepContext:
    environment_handle: str
    profile_spec: EnvironmentProfileMaterializationSpec
    action_specs: tuple[ActionMaterializationSpec, ...]
    connector_specs: tuple[ConnectorConfigMaterializationSpec, ...]
    activation_target_specs: tuple[ConnectorConfigMaterializationSpec, ...]
    projection_specs: tuple[ProjectionExperienceMaterializationSpec, ...]
    environment_events: Mapping[str, tuple[Mapping[str, object], ...]]
    endpoint_request_attributes: Mapping[str, _EndpointRequestAttributeRef]


async def materialize_experience_activation_topology_ontology(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    api_compile_plan_payloads: Sequence[Mapping[str, object]] = (),
    projection_reference_branch_ids_by_name: Mapping[str, UUID] | None = None,
    allow_unresolved_projection_experiences: bool = False,
    dependencies: ActivationTopologyMaterializationDependencies,
) -> MaterializationRunReceipt | None:
    external_projection_keys_by_experience_name: dict[str, str] = {}
    if projection_reference_branch_ids_by_name:
        reference_catalog = await dependencies.load_projection_experience_catalog(
            index=index,
            branch_ids=tuple(
                dict.fromkeys(projection_reference_branch_ids_by_name.values())
            ),
        )
        external_projection_keys_by_experience_name = (
            _projection_keys_by_experience_name_from_catalog(
                index=index,
                catalog=reference_catalog,
            )
        )
        if not external_projection_keys_by_experience_name:
            raise RuntimeError(
                "Experience activation topology dependency reference catalog contained no resolvable projection ownership; "
                + "reference names="
                + repr(
                    tuple(sorted(projection_reference_branch_ids_by_name)[:12])
                )
            )
    contexts = _resolve_activation_topology_step_contexts(
        index=index,
        compile_plan_payloads=compile_plan_payloads,
        api_compile_plan_payloads=api_compile_plan_payloads,
        external_projection_keys_by_experience_name=(
            external_projection_keys_by_experience_name
        ),
        allow_unresolved_projection_experiences=allow_unresolved_projection_experiences,
        dependencies=dependencies,
    )
    if not contexts:
        return None

    profile_config_projection_hash = ocg_support.find_projection_hash_by_name(
        index=index,
        projection_name="EnvironmentExperienceProfileConfig",
    )
    action_experience_projection_hash = ocg_support.find_projection_hash_by_name(
        index=index,
        projection_name="ActionExperience",
    )
    invocation_config_projection_hash = ocg_support.find_projection_hash_by_name(
        index=index,
        projection_name="ExperienceInvocationActionConfig",
    )
    plan = MaterializationPlan(
        module_id="experience",
        pipeline_id="experience.package.activation_topology",
        lane=MaterializationLaneContext(
            branch_id=lane.branch_id,
            projection_hash=profile_config_projection_hash,
        ),
        steps=tuple(
            MaterializationStep(
                step_id=(
                    "activation_topology:"
                    f"{context.profile_spec.experience_name}:"
                    f"{context.profile_spec.key}"
                ),
                step_kind="experience.activation_topology",
                payload={
                    "experience_name": context.profile_spec.experience_name,
                    "profile_key": context.profile_spec.key,
                },
                commit_requested=True,
            )
            for context in contexts
        ),
    )
    context_by_step_id = {
        step.step_id: context for step, context in zip(plan.steps, contexts)
    }
    opgi_by_key = ocg_support.build_opgi_index(index=index)
    opgi_by_key_casefolded = {
        (key or "").strip().casefold(): opgi_entry
        for key, opgi_entry in opgi_by_key.items()
        if (key or "").strip()
    }

    async def _runner(
        *, plan: MaterializationPlan, step: MaterializationStep
    ) -> MaterializationStepResult:
        context = context_by_step_id[step.step_id]
        reference_branch_id = derive_experience_reference_branch_id(
            base_branch_id=lane.branch_id,
            experience_name=context.profile_spec.experience_name,
        )
        projection_spec = _activation_projection_spec_for_profile(context=context)
        projection_experience_id = _activation_projection_experience_id(
            index=index,
            opgi_by_key_casefolded=opgi_by_key_casefolded,
            projection_spec=projection_spec,
            dependencies=dependencies,
        )
        invocation_targets = _activation_invocation_targets_for_projection(
            connector_specs=context.connector_specs,
            projection_spec=projection_spec,
            projection_experience_id=projection_experience_id,
            dependencies=dependencies,
        )
        invocation_targets = tuple(
            sorted(
                (
                    *invocation_targets,
                    *_activation_invocation_targets_for_imported_action_targets(
                        connector_specs=context.activation_target_specs,
                        projection_experience_id=projection_experience_id,
                        dependencies=dependencies,
                    ),
                ),
                key=lambda item: (
                    item.materialized_action_key.casefold(),
                    item.target_ref.casefold(),
                ),
            )
        )

        profile_commit = await _commit_activation_profile_config_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=reference_branch_id,
            projection_hash=profile_config_projection_hash,
            context=context,
            projection_spec=projection_spec,
            projection_experience_id=projection_experience_id,
            opgi_by_key_casefolded=opgi_by_key_casefolded,
            dependencies=dependencies,
        )
        invocation_commit = await _commit_activation_invocation_config_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=reference_branch_id,
            projection_hash=invocation_config_projection_hash,
            projection_experience_id=projection_experience_id,
            targets=invocation_targets,
        )
        action_commit = await _commit_activation_action_experience_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=reference_branch_id,
            projection_hash=action_experience_projection_hash,
            context=context,
            targets=invocation_targets,
            dependencies=dependencies,
        )

        return MaterializationStepResult(
            details={
                "environment_handle": context.environment_handle,
                "experience_name": context.profile_spec.experience_name,
                "profile_key": context.profile_spec.key,
                "reference_branch_id": str(reference_branch_id),
                "projection_experience_id": str(projection_experience_id),
                "environment_experience_profile_config_id": str(
                    profile_commit["environment_experience_profile_config_id"]
                ),
                "environment_profile_config_id": str(
                    profile_commit["environment_profile_config_id"]
                ),
                "profile_config_commit_id": str(profile_commit["commit_id"]),
                "profile_config_head_commit_id": str(profile_commit["head_commit_id"]),
                "profile_config_branch_id": str(profile_commit["branch_id"]),
                "profile_config_projection_hash": str(
                    profile_commit["projection_hash"]
                ),
                "profile_config_domain_object_instance_graph_id": str(
                    profile_commit["domain_object_instance_graph_id"]
                ),
                "profile_config_object_instance_graph_commit_id": str(
                    profile_commit["object_instance_graph_commit_id"]
                ),
                "profile_config_event_count": profile_commit["event_count"],
                "profile_config_node_scope_count": profile_commit["node_scope_count"],
                "profile_config_event_action_count": profile_commit[
                    "event_action_count"
                ],
                "invocation_config_commit_id": (
                    str(invocation_commit["commit_id"])
                    if invocation_commit is not None
                    else None
                ),
                "invocation_config_head_commit_id": (
                    str(invocation_commit["head_commit_id"])
                    if invocation_commit is not None
                    else None
                ),
                "invocation_config_count": (
                    invocation_commit["invocation_config_count"]
                    if invocation_commit is not None
                    else 0
                ),
                "action_experience_commit_id": (
                    str(action_commit["commit_id"])
                    if action_commit is not None
                    else None
                ),
                "action_experience_head_commit_id": (
                    str(action_commit["head_commit_id"])
                    if action_commit is not None
                    else None
                ),
                "action_experience_count": (
                    action_commit["action_experience_count"]
                    if action_commit is not None
                    else 0
                ),
                "action_experience_invocation_count": (
                    action_commit["action_experience_invocation_count"]
                    if action_commit is not None
                    else 0
                ),
                "request_field_count": (
                    action_commit["request_field_count"]
                    if action_commit is not None
                    else 0
                ),
            },
            commit_id=(
                cast(UUID, action_commit["commit_id"])
                if action_commit is not None
                else cast(UUID, profile_commit["commit_id"])
            ),
            head_commit_id=(
                cast(UUID, action_commit["head_commit_id"])
                if action_commit is not None
                else cast(UUID, profile_commit["head_commit_id"])
            ),
        )

    return await MaterializationExecutor().run(plan=plan, runner=_runner)


def _resolve_activation_topology_step_contexts(
    *,
    index: MetaGraphRuntimeIndex,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    api_compile_plan_payloads: Sequence[Mapping[str, object]],
    external_projection_keys_by_experience_name: Mapping[str, str] | None = None,
    allow_unresolved_projection_experiences: bool,
    dependencies: ActivationTopologyMaterializationDependencies,
) -> tuple[_ActivationTopologyStepContext, ...]:
    profile_specs = dependencies.resolve_environment_profile_materialization_specs(
        compile_plan_payloads=compile_plan_payloads,
        external_projection_keys_by_experience_name=(
            external_projection_keys_by_experience_name
        ),
    )
    if not profile_specs:
        return ()
    environment_handle = _activation_environment_handle(
        compile_plan_payloads=compile_plan_payloads,
    )
    if not environment_handle:
        raise RuntimeError(
            "Experience activation topology materialization requires build.environment_handle"
        )
    action_specs = dependencies.resolve_action_materialization_specs(
        compile_plan_payloads=compile_plan_payloads,
    )
    connector_specs = dependencies.resolve_connector_config_materialization_specs(
        compile_plan_payloads=compile_plan_payloads,
    )
    activation_target_specs = (
        dependencies.resolve_activation_target_materialization_specs(
            compile_plan_payloads=compile_plan_payloads,
        )
    )
    projection_specs = dependencies.resolve_projection_materialization_specs(
        compile_plan_payloads=compile_plan_payloads,
        api_compile_plan_payloads=api_compile_plan_payloads,
        index=index,
        allow_unresolved_projection_experiences=allow_unresolved_projection_experiences,
    )
    if not projection_specs:
        raise RuntimeError(
            "Experience activation topology materialization requires projection experience ownership"
        )
    environment_events = _activation_environment_events_by_experience(
        compile_plan_payloads=compile_plan_payloads,
    )
    endpoint_request_attributes = _endpoint_request_attributes_by_endpoint_ref(
        index=index,
        api_compile_plan_payloads=api_compile_plan_payloads,
    )
    return tuple(
        _ActivationTopologyStepContext(
            environment_handle=environment_handle,
            profile_spec=profile_spec,
            action_specs=tuple(action_specs),
            connector_specs=tuple(connector_specs),
            activation_target_specs=tuple(activation_target_specs),
            projection_specs=tuple(projection_specs),
            environment_events=environment_events,
            endpoint_request_attributes=endpoint_request_attributes,
        )
        for profile_spec in profile_specs
    )


def _activation_environment_handle(
    *,
    compile_plan_payloads: Sequence[Mapping[str, object]],
) -> str:
    handles = {
        str(payload.get("environment_handle") or "").strip()
        for payload in compile_plan_payloads
        if str(payload.get("environment_handle") or "").strip()
    }
    if len(handles) > 1:
        raise RuntimeError(
            "Experience activation topology materialization found multiple environment handles: "
            + ", ".join(sorted(handles))
        )
    return next(iter(handles), "")


def _activation_environment_events_by_experience(
    *,
    compile_plan_payloads: Sequence[Mapping[str, object]],
) -> Mapping[str, tuple[Mapping[str, object], ...]]:
    events_by_experience: dict[str, list[Mapping[str, object]]] = {}
    for payload in compile_plan_payloads:
        environment_rows = _expect_list(
            payload.get("environment_ownership", []),
            field_name="environment_ownership",
        )
        for environment_obj in environment_rows:
            environment_row = _expect_mapping(
                environment_obj, field_name="environment_ownership[]"
            )
            experiences = tuple(
                str(item).strip()
                for item in _expect_list(
                    environment_row.get("experiences", []),
                    field_name="environment_ownership[].experiences",
                )
                if str(item).strip()
            )
            if not experiences:
                continue
            events = tuple(
                _expect_mapping(
                    event_obj,
                    field_name="environment_ownership[].events[]",
                )
                for event_obj in _expect_list(
                    environment_row.get("events", []),
                    field_name="environment_ownership[].events",
                )
            )
            for experience_name in experiences:
                events_by_experience.setdefault(
                    experience_name.casefold(),
                    [],
                ).extend(events)
    return {
        experience_name: tuple(events)
        for experience_name, events in events_by_experience.items()
    }


def _endpoint_request_attributes_by_endpoint_ref(
    *,
    index: MetaGraphRuntimeIndex,
    api_compile_plan_payloads: Sequence[Mapping[str, object]],
) -> Mapping[str, _EndpointRequestAttributeRef]:
    refs_by_endpoint: dict[str, _EndpointRequestAttributeRef] = {}
    for payload_index, payload in enumerate(api_compile_plan_payloads):
        api_ontology_rows = _expect_list(
            payload.get("api_ontology", []),
            field_name=f"api_compile_plan[{payload_index}].api_ontology",
        )
        for api_index, api_obj in enumerate(api_ontology_rows):
            api_row = _expect_mapping(
                api_obj,
                field_name=f"api_compile_plan[{payload_index}].api_ontology[{api_index}]",
            )
            for request_index, request_obj in enumerate(
                _expect_list(
                    api_row.get("capability_endpoint_request_configs", []),
                    field_name=(
                        f"api_compile_plan[{payload_index}].api_ontology[{api_index}]"
                        ".capability_endpoint_request_configs"
                    ),
                )
            ):
                request_row = _expect_mapping(
                    request_obj,
                    field_name=(
                        f"api_compile_plan[{payload_index}].api_ontology[{api_index}]"
                        f".capability_endpoint_request_configs[{request_index}]"
                    ),
                )
                api_name = _optional_payload_token(request_row.get("api_name"))
                capability_name = _optional_payload_token(
                    request_row.get("capability_name")
                )
                endpoint_name = _optional_payload_token(
                    request_row.get("endpoint_name")
                )
                raw_class_config_id = _optional_payload_token(
                    request_row.get("class_config_id")
                )
                class_ref = _optional_payload_token(request_row.get("class_ref"))
                if not (
                    api_name
                    and capability_name
                    and endpoint_name
                    and raw_class_config_id
                    and class_ref
                ):
                    continue
                endpoint_ref = f"{api_name}.{capability_name}.{endpoint_name}"
                class_config_id = UUID(raw_class_config_id)
                refs_by_endpoint[endpoint_ref.casefold()] = (
                    _EndpointRequestAttributeRef(
                        endpoint_ref=endpoint_ref,
                        class_config_id=class_config_id,
                        class_ref=class_ref,
                        attributes_by_name=_class_attribute_ids_by_name(
                            index=index,
                            class_config_id=class_config_id,
                        ),
                    )
                )
    return refs_by_endpoint


def _class_attribute_ids_by_name(
    *,
    index: MetaGraphRuntimeIndex,
    class_config_id: UUID,
) -> Mapping[str, UUID]:
    class_config = index.class_configs_by_id.get(class_config_id)
    if class_config is None:
        return {}
    attribute_ids: dict[str, UUID] = {}
    for edge in getattr(class_config, "class_config_attribute_configs", ()):
        attribute = getattr(edge, "attribute_config", None)
        name = str(getattr(attribute, "name", "") or "").strip()
        attribute_config_id = getattr(edge, "attribute_config_id", None) or getattr(
            attribute,
            "id",
            None,
        )
        if name and attribute_config_id is not None:
            attribute_ids[name.casefold()] = UUID(str(attribute_config_id))
    return attribute_ids


def _activation_projection_spec_for_profile(
    *,
    context: _ActivationTopologyStepContext,
) -> ProjectionExperienceMaterializationSpec:
    profile_projection_names = _activation_profile_projection_names(
        profile_spec=context.profile_spec,
    )
    profile_owner_name = context.profile_spec.experience_name.casefold()
    candidates = [
        spec
        for spec in context.projection_specs
        if spec.experience_name.casefold() in profile_projection_names
    ]
    if len(candidates) == 1:
        return candidates[0]
    owner_candidates = [
        spec
        for spec in context.projection_specs
        if spec.experience_name.casefold() == profile_owner_name
    ]
    if len(owner_candidates) == 1:
        return owner_candidates[0]
    if len(candidates) != 1:
        raise RuntimeError(
            "Experience activation topology requires exactly one projection experience for profile "
            + (
                f"(experience={context.profile_spec.experience_name!r}, "
                f"profile={context.profile_spec.key!r}, "
                f"candidates={[item.experience_name for item in candidates]!r})"
            )
        )
    return candidates[0]


def _activation_profile_projection_names(
    *,
    profile_spec: EnvironmentProfileMaterializationSpec,
) -> frozenset[str]:
    names: set[str] = set()
    for process in profile_spec.process_configs:
        for thread in process.thread_configs:
            for projection in thread.projection_experiences:
                names.add(projection.projection_experience_name.casefold())
            for layout in thread.layout_configs:
                for section in layout.sections:
                    names.add(section.projection_experience_name.casefold())
    for transition in profile_spec.view_event_transitions:
        names.add(transition.source_projection_experience_name.casefold())
        names.add(transition.target_projection_experience_name.casefold())
    if not names:
        names.add(profile_spec.experience_name.casefold())
    return frozenset(names)


def _activation_projection_experience_id(
    *,
    index: MetaGraphRuntimeIndex,
    opgi_by_key_casefolded: Mapping[str, tuple[UUID, set[str] | frozenset[str]]],
    projection_spec: ProjectionExperienceMaterializationSpec,
    dependencies: ActivationTopologyMaterializationDependencies,
) -> UUID:
    projection_opgi_id = dependencies.resolve_projection_opgi_id_for_projection_key(
        opgi_by_key_casefolded=opgi_by_key_casefolded,
        projection_key=projection_spec.projection_key,
        experience_name=projection_spec.experience_name,
        runtime_opgi_id=projection_spec.runtime_opgi_id,
    )
    _ = index
    return experience_stable_ids.stable_projection_experience_id(
        object_projection_graph_identity_id=projection_opgi_id,
        name=projection_spec.experience_name,
    )


def _activation_invocation_targets_for_projection(
    *,
    connector_specs: Sequence[ConnectorConfigMaterializationSpec],
    projection_spec: ProjectionExperienceMaterializationSpec,
    projection_experience_id: UUID,
    dependencies: ActivationTopologyMaterializationDependencies,
) -> tuple[_ActivationInvocationTargetSpec, ...]:
    targets: list[_ActivationInvocationTargetSpec] = []
    for connector in connector_specs:
        if (
            connector.projection_experience_name.casefold()
            != projection_spec.experience_name.casefold()
        ):
            continue
        for sensor in connector.sensor_configs:
            for invocation in sensor.invocation_action_configs:
                targets.append(
                    _activation_invocation_target_spec(
                        invocation=invocation,
                        connector_key=connector.connector_key,
                        surface_kind="sensor",
                        surface_key=sensor.sensor_key,
                        projection_experience_id=projection_experience_id,
                        dependencies=dependencies,
                    )
                )
        for actuator in connector.actuator_configs:
            for invocation in actuator.invocation_action_configs:
                targets.append(
                    _activation_invocation_target_spec(
                        invocation=invocation,
                        connector_key=connector.connector_key,
                        surface_kind="actuator",
                        surface_key=actuator.actuator_key,
                        projection_experience_id=projection_experience_id,
                        dependencies=dependencies,
                    )
                )
    return tuple(
        sorted(
            targets,
            key=lambda item: (
                item.materialized_action_key.casefold(),
                item.target_ref.casefold(),
            ),
        )
    )


def _activation_invocation_targets_for_imported_action_targets(
    *,
    connector_specs: Sequence[ConnectorConfigMaterializationSpec],
    projection_experience_id: UUID,
    dependencies: ActivationTopologyMaterializationDependencies,
) -> tuple[_ActivationInvocationTargetSpec, ...]:
    targets: list[_ActivationInvocationTargetSpec] = []
    for connector in connector_specs:
        for sensor in connector.sensor_configs:
            for invocation in sensor.invocation_action_configs:
                targets.append(
                    _activation_invocation_target_spec(
                        invocation=invocation,
                        connector_key=connector.connector_key,
                        surface_kind="sensor",
                        surface_key=sensor.sensor_key,
                        projection_experience_id=projection_experience_id,
                        dependencies=dependencies,
                    )
                )
        for actuator in connector.actuator_configs:
            for invocation in actuator.invocation_action_configs:
                targets.append(
                    _activation_invocation_target_spec(
                        invocation=invocation,
                        connector_key=connector.connector_key,
                        surface_kind="actuator",
                        surface_key=actuator.actuator_key,
                        projection_experience_id=projection_experience_id,
                        dependencies=dependencies,
                    )
                )
    return tuple(
        sorted(
            targets,
            key=lambda item: (
                item.materialized_action_key.casefold(),
                item.target_ref.casefold(),
            ),
        )
    )


def _activation_invocation_target_spec(
    *,
    invocation: ConnectorInvocationActionConfigMaterializationSpec,
    connector_key: str,
    surface_kind: str,
    surface_key: str,
    projection_experience_id: UUID,
    dependencies: ActivationTopologyMaterializationDependencies,
) -> _ActivationInvocationTargetSpec:
    target_kind, api_capability_endpoint_id, sdk_operation_id = (
        dependencies.connector_invocation_action_target_ids(
            action=invocation,
            connector_key=connector_key,
            surface_kind=surface_kind,
            surface_key=surface_key,
        )
    )
    entity_id = api_capability_endpoint_id or sdk_operation_id
    if entity_id is None:
        raise RuntimeError(
            "Experience activation topology invocation target requires API endpoint or SDK operation id"
        )
    return _ActivationInvocationTargetSpec(
        materialized_action_key=invocation.materialized_action_key,
        target_ref=invocation.target_ref,
        target_kind=target_kind,
        api_capability_endpoint_id=api_capability_endpoint_id,
        sdk_operation_id=sdk_operation_id,
        experience_invocation_action_config_id=(
            experience_stable_ids.stable_experience_invocation_action_config_id(
                projection_experience_id=projection_experience_id,
                target_kind=target_kind.value,
                entity_id=entity_id,
            )
        ),
        request_fields=tuple(invocation.request_fields),
    )


async def _commit_activation_profile_config_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    context: _ActivationTopologyStepContext,
    projection_spec: ProjectionExperienceMaterializationSpec,
    projection_experience_id: UUID,
    opgi_by_key_casefolded: Mapping[str, tuple[UUID, set[str] | frozenset[str]]],
    dependencies: ActivationTopologyMaterializationDependencies,
) -> Mapping[str, object]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    environment_config_id = stable_environment_config_id(
        handle=context.environment_handle,
    )
    environment_profile_config_id = (
        environment_stable_ids.stable_environment_profile_config_id(
            environment_config_id=environment_config_id,
            key=context.profile_spec.key,
        )
    )
    environment_experience_id = experience_stable_ids.stable_environment_experience_id(
        fqn_prefix=context.profile_spec.fqn_prefix,
    )
    profile_config_id = (
        experience_stable_ids.stable_environment_experience_profile_config_id(
            environment_experience_id=environment_experience_id,
            environment_profile_config_id=environment_profile_config_id,
            key=context.profile_spec.key,
        )
    )
    profile_config = _remember(
        objects_by_id,
        EnvironmentExperienceProfileConfig(
            id=profile_config_id,
            environment_experience_id=environment_experience_id,
            environment_profile_config_id=environment_profile_config_id,
            key=context.profile_spec.key,
            title=context.profile_spec.title,
            description=context.profile_spec.description,
            narrative=context.profile_spec.narrative,
            experiences=[],
            events=[],
        ),
    )
    projection_edge = _remember(
        objects_by_id,
        EnvironmentExperienceProjection(
            id=experience_stable_ids.stable_environment_experience_projection_id(
                environment_experience_profile_config_id=profile_config_id,
                projection_experience_id=projection_experience_id,
            ),
            environment_experience_profile_config_id=profile_config_id,
            projection_experience_id=projection_experience_id,
        ),
    )
    profile_config.experiences.append(projection_edge)

    action_names_by_ref = _activation_action_names_by_environment_ref(
        contexts=(context,),
        dependencies=dependencies,
    )
    action_specs_by_name = {
        spec.action_name.casefold(): spec for spec in context.action_specs
    }
    event_count = 0
    node_scope_count = 0
    event_action_count = 0
    events = context.environment_events.get(
        context.profile_spec.experience_name.casefold(),
        (),
    )
    for event_row in events:
        event_name = _required_step_payload_token(event_row.get("event"))
        event_config_id = stable_event_config_id(name=event_name)
        environment_event_id = (
            experience_stable_ids.stable_environment_experience_event_id(
                environment_experience_profile_config_id=profile_config_id,
                event_config_id=event_config_id,
            )
        )
        event = _remember(
            objects_by_id,
            EnvironmentExperienceEvent(
                id=environment_event_id,
                environment_experience_profile_config_id=profile_config_id,
                event_config_id=event_config_id,
                actions=[],
                node_scopes=[],
            ),
        )
        event_count += 1
        for node_scope_obj in _expect_list(
            event_row.get("node_scopes", []),
            field_name="environment_ownership[].events[].node_scopes",
        ):
            node_scope_row = _expect_mapping(
                node_scope_obj,
                field_name="environment_ownership[].events[].node_scopes[]",
            )
            node_alias = _required_step_payload_token(node_scope_row.get("node_ref"))
            condition_config_id = stable_condition_config_id(
                name=f"{event_name}.{node_alias}",
            )
            event_config_condition_config_id = stable_event_config_condition_config_id(
                event_config_id=event_config_id,
                condition_config_id=condition_config_id,
            )
            projection_node_identity_id = _activation_projection_node_identity_id(
                index=index,
                opgi_by_key_casefolded=opgi_by_key_casefolded,
                projection_spec=projection_spec,
                projection_experience_id=projection_experience_id,
                node_alias=node_alias,
                dependencies=dependencies,
            )
            node_scope = _remember(
                objects_by_id,
                EnvironmentExperienceEventNodeScope(
                    id=(
                        experience_stable_ids.stable_environment_experience_event_node_scope_id(
                            environment_experience_event_id=environment_event_id,
                            event_config_condition_config_id=(
                                event_config_condition_config_id
                            ),
                            projection_experience_node_identity_id=(
                                projection_node_identity_id
                            ),
                        )
                    ),
                    environment_experience_event_id=environment_event_id,
                    event_config_condition_config_id=event_config_condition_config_id,
                    projection_experience_node_identity_id=(
                        projection_node_identity_id
                    ),
                ),
            )
            event.node_scopes.append(node_scope)
            node_scope_count += 1
        for action_obj in _expect_list(
            event_row.get("actions", []),
            field_name="environment_ownership[].events[].actions",
        ):
            action_row = _expect_mapping(
                action_obj,
                field_name="environment_ownership[].events[].actions[]",
            )
            action_ref = dependencies.normalize_symbol(
                str(action_row.get("action") or "")
            )
            action_name = action_names_by_ref.get(action_ref, action_ref)
            if action_name.casefold() not in action_specs_by_name:
                raise RuntimeError(
                    "Experience activation topology could not resolve event action "
                    + f"{action_ref!r} to an authored action"
                )
            action_config_id = stable_action_config_id(name=action_name)
            action_experience_id = experience_stable_ids.stable_action_experience_id(
                action_config_id=action_config_id,
            )
            event_action = _remember(
                objects_by_id,
                EnvironmentExperienceEventAction(
                    id=(
                        experience_stable_ids.stable_environment_experience_event_action_id(
                            environment_experience_event_id=environment_event_id,
                            action_experience_id=action_experience_id,
                        )
                    ),
                    environment_experience_event_id=environment_event_id,
                    action_experience_id=action_experience_id,
                ),
            )
            event.actions.append(event_action)
            event_action_count += 1
        profile_config.events.append(event)

    commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=profile_config_id,
        root_object=profile_config,
        objects_by_id=objects_by_id,
        operation_label="experience.activation_topology.profile_config",
        commit_id_namespace=(
            _EXPERIENCE_ACTIVATION_PROFILE_CONFIG_SNAPSHOT_COMMIT_NAMESPACE
        ),
    )
    opg = index.opg_by_hash[projection_hash]
    return {
        "environment_experience_profile_config_id": profile_config_id,
        "environment_profile_config_id": environment_profile_config_id,
        "commit_id": commit.commit_id,
        "head_commit_id": commit.head_commit_id,
        "branch_id": branch_id,
        "projection_hash": projection_hash,
        "domain_object_instance_graph_id": stable_object_instance_graph_id(
            object_projection_graph_id=opg.id,
            key=str(branch_id),
        ),
        "object_instance_graph_commit_id": commit.object_instance_graph_commit_id,
        "event_count": event_count,
        "node_scope_count": node_scope_count,
        "event_action_count": event_action_count,
    }


def _activation_action_names_by_environment_ref(
    *,
    contexts: Sequence[_ActivationTopologyStepContext],
    dependencies: ActivationTopologyMaterializationDependencies,
) -> Mapping[str, str]:
    action_names: dict[str, str] = {}
    for context in contexts:
        for spec in context.action_specs:
            action_names[dependencies.normalize_symbol(spec.action_name)] = (
                spec.action_name
            )
    return action_names


def _activation_projection_node_identity_id(
    *,
    index: MetaGraphRuntimeIndex,
    opgi_by_key_casefolded: Mapping[str, tuple[UUID, set[str] | frozenset[str]]],
    projection_spec: ProjectionExperienceMaterializationSpec,
    projection_experience_id: UUID,
    node_alias: str,
    dependencies: ActivationTopologyMaterializationDependencies,
) -> UUID:
    node_spec = _activation_projection_node_spec_for_alias(
        projection_spec=projection_spec,
        node_alias=node_alias,
    )
    projection_opgi_id = dependencies.resolve_projection_opgi_id_for_projection_key(
        opgi_by_key_casefolded=opgi_by_key_casefolded,
        projection_key=projection_spec.projection_key,
        experience_name=projection_spec.experience_name,
        runtime_opgi_id=projection_spec.runtime_opgi_id,
    )
    opg = dependencies.find_projection_graph_by_opgi_id(
        index=index,
        object_projection_graph_identity_id=projection_opgi_id,
    )
    node_snapshots = build_projection_node_snapshots_for_materialization(
        index=index,
        opg=opg,
        nodes=(node_spec,),
        experience_name=projection_spec.experience_name,
    )
    if len(node_snapshots) != 1:
        raise RuntimeError(
            "Experience activation topology expected one projection node snapshot "
            + f"for alias {node_alias!r}"
        )
    projection_node_id = experience_stable_ids.stable_projection_experience_node_id(
        projection_experience_id=projection_experience_id,
        object_projection_graph_node_id=(
            node_snapshots[0].object_projection_graph_node_id
        ),
        key=node_spec.name,
    )
    return experience_stable_ids.stable_projection_experience_node_identity_id(
        projection_experience_node_id=projection_node_id,
        key=node_alias,
    )


def _activation_projection_node_spec_for_alias(
    *,
    projection_spec: ProjectionExperienceMaterializationSpec,
    node_alias: str,
) -> ProjectionExperienceNodeMaterializationSpec:
    alias_key = node_alias.casefold()
    matches = [
        node
        for node in projection_spec.nodes
        if alias_key in {identity.casefold() for identity in node.identity_keys}
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "Experience activation topology could not resolve node_scope alias "
            + (
                f"{node_alias!r} in projection experience "
                f"{projection_spec.experience_name!r}"
            )
        )
    return matches[0]


async def _commit_activation_invocation_config_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    projection_experience_id: UUID,
    targets: Sequence[_ActivationInvocationTargetSpec],
) -> Mapping[str, object] | None:
    if not targets:
        return None
    last_commit_id: UUID | None = None
    last_head_commit_id: UUID | None = None
    for target in targets:
        invocation_config = ExperienceInvocationActionConfig(
            id=target.experience_invocation_action_config_id,
            projection_experience_id=projection_experience_id,
            target_kind=target.target_kind,
            api_capability_endpoint_id=target.api_capability_endpoint_id,
            sdk_operation_id=target.sdk_operation_id,
        )
        commit = await _commit_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            root_object_id=invocation_config.id,
            root_object=invocation_config,
            objects_by_id={invocation_config.id: invocation_config},
            operation_label="experience.activation_topology.invocation_config",
            commit_id_namespace=(
                _EXPERIENCE_ACTIVATION_INVOCATION_CONFIG_SNAPSHOT_COMMIT_NAMESPACE
            ),
        )
        last_commit_id = commit.commit_id
        last_head_commit_id = commit.head_commit_id
    return {
        "commit_id": last_commit_id,
        "head_commit_id": last_head_commit_id,
        "invocation_config_count": len(targets),
    }


async def _commit_activation_action_experience_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    context: _ActivationTopologyStepContext,
    targets: Sequence[_ActivationInvocationTargetSpec],
    dependencies: ActivationTopologyMaterializationDependencies,
) -> Mapping[str, object] | None:
    action_bindings = _activation_action_request_bindings(
        action_specs=context.action_specs,
        targets=targets,
        dependencies=dependencies,
    )
    if not action_bindings:
        return None
    last_commit_id: UUID | None = None
    last_head_commit_id: UUID | None = None
    action_experience_count = 0
    invocation_count = 0
    request_field_count = 0
    for action_spec, bound_targets in action_bindings:
        objects_by_id: dict[UUID, BaseORMModel] = {}
        action_config_id = stable_action_config_id(name=action_spec.action_name)
        action_experience_id = experience_stable_ids.stable_action_experience_id(
            action_config_id=action_config_id,
        )
        action_experience = _remember(
            objects_by_id,
            ActionExperience(
                id=action_experience_id,
                action_config_id=action_config_id,
                action_experience_invocations=[],
            ),
        )
        action_experience_count += 1
        for target in bound_targets:
            if target.request_fields and target.target_kind is not (
                ExperienceInvocationActionTargetKind.api
            ):
                raise RuntimeError(
                    "Experience activation topology request fields require an API invocation target "
                    + f"(target_ref={target.target_ref!r})"
                )
            action_invocation_id = (
                experience_stable_ids.stable_action_experience_invocation_id(
                    action_experience_id=action_experience_id,
                    experience_invocation_action_config_id=(
                        target.experience_invocation_action_config_id
                    ),
                )
            )
            invocation = _remember(
                objects_by_id,
                ActionExperienceInvocation(
                    id=action_invocation_id,
                    action_experience_id=action_experience_id,
                    experience_invocation_action_config_id=(
                        target.experience_invocation_action_config_id
                    ),
                    request_fields=[],
                ),
            )
            invocation_count += 1
            endpoint_ref = context.endpoint_request_attributes.get(
                target.target_ref.casefold()
            )
            for position, field in enumerate(target.request_fields):
                if endpoint_ref is None:
                    raise RuntimeError(
                        "Experience activation topology could not resolve API endpoint request class "
                        + f"for target_ref={target.target_ref!r}"
                    )
                attribute = _activation_request_attribute_config(
                    objects_by_id=objects_by_id,
                    endpoint_ref=endpoint_ref,
                    field=field,
                )
                request_field = _remember(
                    objects_by_id,
                    ActionExperienceInvocationRequestField(
                        id=(
                            experience_stable_ids.stable_action_experience_invocation_request_field_id(
                                action_experience_invocation_id=(action_invocation_id),
                                attribute_config_id=attribute.id,
                            )
                        ),
                        action_experience_invocation_id=action_invocation_id,
                        attribute_config_id=attribute.id,
                        attribute_config=attribute,
                        source_ref=field.source_ref,
                        required=field.required,
                        position=position,
                    ),
                )
                invocation.request_fields.append(request_field)
                request_field_count += 1
            action_experience.action_experience_invocations.append(invocation)

        commit = await _commit_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            root_object_id=action_experience_id,
            root_object=action_experience,
            objects_by_id=objects_by_id,
            operation_label="experience.activation_topology.action_experience",
            commit_id_namespace=(
                _EXPERIENCE_ACTIVATION_ACTION_SNAPSHOT_COMMIT_NAMESPACE
            ),
        )
        last_commit_id = commit.commit_id
        last_head_commit_id = commit.head_commit_id
    return {
        "commit_id": last_commit_id,
        "head_commit_id": last_head_commit_id,
        "action_experience_count": action_experience_count,
        "action_experience_invocation_count": invocation_count,
        "request_field_count": request_field_count,
    }


def _activation_action_request_bindings(
    *,
    action_specs: Sequence[ActionMaterializationSpec],
    targets: Sequence[_ActivationInvocationTargetSpec],
    dependencies: ActivationTopologyMaterializationDependencies,
) -> tuple[
    tuple[ActionMaterializationSpec, tuple[_ActivationInvocationTargetSpec, ...]], ...
]:
    request_targets = tuple(target for target in targets if target.request_fields)
    if not action_specs:
        return ()
    if not request_targets:
        dependency_actions = tuple(
            action.action_name for action in action_specs if action.is_dependency
        )
        if dependency_actions:
            raise RuntimeError(
                "Experience activation topology dependency actions require a "
                + "request-bearing invocation target: "
                + ", ".join(sorted(dependency_actions, key=str.casefold))
            )
        return ()
    bindings: list[
        tuple[ActionMaterializationSpec, tuple[_ActivationInvocationTargetSpec, ...]]
    ] = []
    for action_spec in action_specs:
        matches = tuple(
            target
            for target in request_targets
            if _activation_target_matches_action(
                action_name=action_spec.action_name,
                target=target,
                dependencies=dependencies,
            )
        )
        if (
            not matches
            and not action_spec.is_dependency
            and len(action_specs) == 1
            and len(request_targets) == 1
        ):
            matches = request_targets
        if not matches:
            continue
        if len(matches) > 1:
            raise RuntimeError(
                "Experience activation topology cannot infer a unique request-bearing invocation "
                + f"for action {action_spec.action_name!r}"
            )
        bindings.append((action_spec, matches))
    if not bindings and request_targets:
        raise RuntimeError(
            "Experience activation topology found request-field declarations but no authored action binding"
        )
    return tuple(bindings)


def _activation_target_matches_action(
    *,
    action_name: str,
    target: _ActivationInvocationTargetSpec,
    dependencies: ActivationTopologyMaterializationDependencies,
) -> bool:
    normalized_action = dependencies.normalize_symbol(action_name).casefold()
    if not normalized_action:
        return False
    tokens = {
        token
        for token in target.materialized_action_key.casefold()
        .replace(".", "_")
        .split("_")
        if token
    }
    action_tokens = {
        token for token in normalized_action.replace(".", "_").split("_") if token
    }
    return bool(action_tokens and action_tokens.issubset(tokens))


def _activation_request_attribute_config(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    endpoint_ref: _EndpointRequestAttributeRef,
    field: ConnectorInvocationRequestFieldMaterializationSpec,
) -> AttributeConfig:
    attribute_name = field.attribute.strip()
    if not attribute_name:
        raise RuntimeError("Request-field attribute name is required")
    expected_attribute_id = stable_attribute_config_id(
        owner_key=endpoint_ref.class_ref,
        name=attribute_name,
    )
    indexed_attribute_id = endpoint_ref.attributes_by_name.get(
        attribute_name.casefold()
    )
    if endpoint_ref.attributes_by_name and indexed_attribute_id is None:
        raise RuntimeError(
            "Experience activation topology request field does not belong to endpoint request ClassConfig "
            + (
                f"(endpoint_ref={endpoint_ref.endpoint_ref!r}, "
                f"class_ref={endpoint_ref.class_ref!r}, attribute={attribute_name!r})"
            )
        )
    if (
        indexed_attribute_id is not None
        and indexed_attribute_id != expected_attribute_id
    ):
        raise RuntimeError(
            "Experience activation topology request field stable id drifted "
            + (
                f"(endpoint_ref={endpoint_ref.endpoint_ref!r}, "
                f"attribute={attribute_name!r}, "
                f"expected={expected_attribute_id}, actual={indexed_attribute_id})"
            )
        )
    return _build_primitive_attribute_config(
        objects_by_id=objects_by_id,
        owner_key=endpoint_ref.class_ref,
        name=attribute_name,
        primitive_base_type=CodePrimitiveBaseType.any,
        is_required=field.required,
    )


__all__ = [
    "ActivationTopologyMaterializationDependencies",
    "materialize_experience_activation_topology_ontology",
    "_ActivationInvocationTargetSpec",
    "_ActivationTopologyStepContext",
    "_EndpointRequestAttributeRef",
    "_activation_action_request_bindings",
    "_activation_projection_spec_for_profile",
    "_endpoint_request_attributes_by_endpoint_ref",
]
