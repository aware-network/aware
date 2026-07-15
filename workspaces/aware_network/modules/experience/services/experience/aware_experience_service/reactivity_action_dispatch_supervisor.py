from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol, cast
from uuid import UUID

from aware_api_runtime.invocation import ApiInvocationIR, ApiInvocationSourceCommit
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_capability_endpoint_request_config import (
    ApiCapabilityEndpointRequestConfig,
)
from aware_api_ontology.api.api_capability_endpoint_response_config import (
    ApiCapabilityEndpointResponseConfig,
)
from aware_api_ontology.stable_ids import (
    stable_api_capability_endpoint_id,
    stable_api_capability_endpoint_request_config_id,
    stable_api_capability_endpoint_response_config_id,
    stable_api_capability_id,
    stable_api_id,
)
from aware_code.types import JsonObject
from aware_experience.action_dispatch.bridge import (
    ActionDispatchBinding,
    ActionDispatchBridgeResult,
    ActionDispatchRoleEvidence,
    dispatch_requested_action_intent,
    resolve_action_dispatch_binding_from_environment_profile,
)
from aware_experience.action_dispatch.fulfillment import (
    ActionTerminalFulfillmentInvoker,
)
from aware_experience.program.action_continuation_activation import (
    HydratedProgramActionContinuationActivationRuntime,
    ProgramActionContinuationActivationError,
    ProgramActionContinuationActivationResult,
    ProgramActionContinuationActivationRuntime,
    ProgramActionContinuationEndpointRoute,
)
from aware_experience.program.action_continuation_graph import (
    ProgramActionContinuationActivationInput,
)
from aware_experience.program.snapshot_contract import ProgramOntologySnapshot
from aware_experience.program.snapshot_reader import ProgramOntologySnapshotReader
from aware_experience.section_graph_binding.service import (
    hydrate_experience_reference_session,
)
from aware_experience.supervisor import (
    ActionIntentDispatcher,
    ActionIntentDispatcherFactory,
    ExperienceSessionFeatureLease,
)
from aware_experience_ontology.environment.environment_experience_profile_config import (
    EnvironmentExperienceProfileConfig,
)
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_api_runtime.invocation import ApiInvocationRuntimeProtocol
from aware_reactivity_ontology.action.action_config import ActionConfig
from aware_reactivity_sdk import ReactivitySdkClient
from aware_experience.action_dispatch.fulfillment import ActionDispatchTerminalOutcome
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntent,
)
from aware_reactivity_service_dto.reactivity.bridge_event import (
    ActorReactivityBridgeEvent,
)
from aware_reactivity_service_dto.reactivity.event_meaning import (
    ReactivityEventMeaningResolutionRequest,
)
from aware_service_runtime.api_ingress.host_context import ServiceApiHostContext
from aware_service_runtime.action_dispatch_fulfillment import (
    ServiceHostActionTerminalFulfillmentInvoker,
)
from aware_service_runtime.local_service_host_api_client import (
    build_local_service_host_duplex_client_factory_for_route,
)
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
    ServiceApiDependencyRouteKind,
)


EXPERIENCE_ACTION_DISPATCH_PROJECTION_NAMES = (
    "EnvironmentExperienceProfileConfig",
    "ActionExperience",
    "ExperienceInvocationActionConfig",
    "EventConfig",
    "ActionConfig",
    "Api",
)

_SEMANTIC_EVENT_INPUT_KEY = "semantic_event"
_SEMANTIC_EVENT_CLASS_NAME = "ReactivityEventMeaningResolutionRequest"


@dataclass(frozen=True, slots=True)
class ExperienceActionDispatchServiceRuntime:
    profile_config: EnvironmentExperienceProfileConfig
    runtime: ApiInvocationRuntimeProtocol
    index: MetaGraphRuntimeIndex
    source_lane: MaterializationLaneContext
    target_lane: MaterializationLaneContext
    ir: ApiInvocationIR
    terminal_fulfillment_invoker: ActionTerminalFulfillmentInvoker
    role_evidence: tuple[ActionDispatchRoleEvidence, ...] = ()
    program_continuation_activation_runtime: (
        ProgramActionContinuationActivationRuntime | None
    ) = None


class ExperienceActionDispatchServiceRuntimeLoader(Protocol):
    async def load_action_dispatch_runtime(
        self,
        *,
        lease: ExperienceSessionFeatureLease,
        event: ActorReactivityBridgeEvent,
        intent: ReactivityActionIntent,
        host_context: ServiceApiHostContext,
    ) -> ExperienceActionDispatchServiceRuntime: ...


@dataclass(frozen=True, slots=True)
class CommittedExperienceActionDispatchServiceRuntimeLoader:
    """Hydrate action dispatch only from committed Experience and Service truth."""

    async def load_action_dispatch_runtime(
        self,
        *,
        lease: ExperienceSessionFeatureLease,
        event: ActorReactivityBridgeEvent,
        intent: ReactivityActionIntent,
        host_context: ServiceApiHostContext,
    ) -> ExperienceActionDispatchServiceRuntime:
        materialization = host_context.materialization
        if materialization is None:
            raise RuntimeError(
                "Experience action dispatch requires Service materialization context."
            )
        index = cast(
            MetaGraphRuntimeIndex,
            getattr(
                materialization.graph_context, "index", materialization.graph_context
            ),
        )
        session = await hydrate_experience_reference_session(
            host_context=host_context,
            experience_name=lease.session_scope.experience_name,
            projection_names=EXPERIENCE_ACTION_DISPATCH_PROJECTION_NAMES,
        )
        profile, binding = _resolve_profile_and_binding(
            objects=session.imap_all_objects(),
            profile_key=lease.session_scope.profile_key,
            intent=intent,
            index=index,
        )
        endpoint_ref, route = _resolve_endpoint_route(
            routes=host_context.service_api_dependency_routes,
            endpoint_id=binding.api_capability_endpoint_id,
        )
        ir = _build_action_invocation_ir(
            endpoint_ref=endpoint_ref,
            binding=binding,
            class_configs_by_id=index.class_configs_by_id,
        )
        terminal_invoker = ServiceHostActionTerminalFulfillmentInvoker(
            actor_id=host_context.operation_context.actor_id,
            client_factory=build_local_service_host_duplex_client_factory_for_route(
                route
            ),
            request_timeout_s=route.request_timeout_s,
            invocation_context=JsonObject(
                {
                    "source": "experience.reactivity_action_dispatch",
                    "experience_name": lease.session_scope.experience_name,
                }
            ),
        )
        environment_id = _require_environment_id(
            lease=lease,
            host_context=host_context,
        )
        branch_id = (
            host_context.experience_reference_branch_ids_by_experience_name.get(
                lease.session_scope.experience_name
            )
            or lease.session_scope.branch_id
            or host_context.operation_context.branch_id
        )
        if branch_id is None:
            raise RuntimeError(
                "Experience action dispatch requires an Experience reference branch."
            )
        continuation_runtime = _CommittedProgramContinuationRuntime(
            snapshot_reader=ProgramOntologySnapshotReader(
                branch_id=branch_id,
                environment_id=environment_id,
                index=index,
            ),
            class_configs_by_id=index.class_configs_by_id,
            routes=host_context.service_api_dependency_routes,
            terminal_fulfillment_invoker=terminal_invoker,
            event=event,
        )
        lane = materialization.target_lane
        return ExperienceActionDispatchServiceRuntime(
            profile_config=profile,
            runtime=cast(ApiInvocationRuntimeProtocol, materialization.runtime),
            index=index,
            source_lane=lane,
            target_lane=lane,
            ir=ir,
            terminal_fulfillment_invoker=terminal_invoker,
            program_continuation_activation_runtime=continuation_runtime,
        )


@dataclass(frozen=True, slots=True)
class _ResolvedProgramSnapshotResolver:
    snapshots: tuple[ProgramOntologySnapshot, ...]

    async def resolve_action_continuation_candidates(
        self,
        *,
        action_config_id: UUID,
        event_config_id: UUID,
    ) -> tuple[ProgramOntologySnapshot, ...]:
        _ = (action_config_id, event_config_id)
        return self.snapshots


@dataclass(frozen=True, slots=True)
class _CommittedProgramContinuationRuntime:
    snapshot_reader: ProgramOntologySnapshotReader
    class_configs_by_id: Mapping[UUID, ClassConfig]
    routes: tuple[ServiceApiDependencyRouteDescriptor, ...]
    terminal_fulfillment_invoker: ActionTerminalFulfillmentInvoker
    event: ActorReactivityBridgeEvent

    async def activate(
        self,
        *,
        initial_action_config_id: UUID,
        initial_event_config_id: UUID,
        initial_api_capability_endpoint_id: UUID,
        initial_outcome: ActionDispatchTerminalOutcome,
    ) -> ProgramActionContinuationActivationResult | None:
        snapshots = await self.snapshot_reader.resolve_action_continuation_candidates(
            action_config_id=initial_action_config_id,
            event_config_id=initial_event_config_id,
        )
        if not snapshots:
            return None
        if len(snapshots) != 1:
            raise ProgramActionContinuationActivationError(
                "program_action_continuation_activation_ambiguous"
            )
        snapshot = snapshots[0]
        actions, endpoints, endpoint_routes = _hydrate_program_contract_pins(
            snapshot=snapshot,
            routes=self.routes,
            class_configs_by_id=self.class_configs_by_id,
        )
        runtime = HydratedProgramActionContinuationActivationRuntime(
            snapshot_resolver=_ResolvedProgramSnapshotResolver(snapshots),
            action_configs_by_id=actions,
            api_capability_endpoints_by_id=endpoints,
            class_configs_by_id=self.class_configs_by_id,
            endpoint_routes_by_id=endpoint_routes,
            activation_inputs_by_key=_build_program_activation_inputs(
                snapshot=snapshot,
                event=self.event,
                class_configs_by_id=self.class_configs_by_id,
            ),
            terminal_fulfillment_invoker=self.terminal_fulfillment_invoker,
        )
        return await runtime.activate(
            initial_action_config_id=initial_action_config_id,
            initial_event_config_id=initial_event_config_id,
            initial_api_capability_endpoint_id=initial_api_capability_endpoint_id,
            initial_outcome=initial_outcome,
        )


def _build_program_activation_inputs(
    *,
    snapshot: ProgramOntologySnapshot,
    event: ActorReactivityBridgeEvent,
    class_configs_by_id: Mapping[UUID, ClassConfig],
) -> Mapping[str, ProgramActionContinuationActivationInput]:
    class_ids_by_key: dict[str, set[UUID]] = {}
    for rows in snapshot.activation_field_bindings_by_intent_id.values():
        for row in rows:
            key = (row.source_input_key or "").strip()
            if not key:
                raise ProgramActionContinuationActivationError(
                    "program_action_continuation_activation_input_key_missing"
                )
            class_ids_by_key.setdefault(key, set()).add(row.source_class_config_id)
    if not class_ids_by_key:
        return {}
    unsupported = sorted(set(class_ids_by_key) - {_SEMANTIC_EVENT_INPUT_KEY})
    if unsupported:
        raise ProgramActionContinuationActivationError(
            "program_action_continuation_activation_input_unsupported:"
            + ",".join(unsupported)
        )
    class_ids = class_ids_by_key[_SEMANTIC_EVENT_INPUT_KEY]
    if len(class_ids) != 1:
        raise ProgramActionContinuationActivationError(
            "program_action_continuation_activation_class_ambiguous:"
            + _SEMANTIC_EVENT_INPUT_KEY
        )
    class_config_id = next(iter(class_ids))
    class_config = class_configs_by_id.get(class_config_id)
    if class_config is None:
        raise ProgramActionContinuationActivationError(
            "program_action_continuation_activation_class_missing:"
            + str(class_config_id)
        )
    if (class_config.name or "").strip() != _SEMANTIC_EVENT_CLASS_NAME:
        raise ProgramActionContinuationActivationError(
            "program_action_continuation_semantic_event_class_mismatch:"
            + str(class_config_id)
        )
    request = ReactivityEventMeaningResolutionRequest(event=event)
    return {
        _SEMANTIC_EVENT_INPUT_KEY: ProgramActionContinuationActivationInput(
            input_key=_SEMANTIC_EVENT_INPUT_KEY,
            model_id=event.event_id,
            class_config=class_config,
            payload=request.model_dump(mode="python"),
        )
    }


def _require_event_matches_intent(
    *,
    event: ActorReactivityBridgeEvent,
    intent: ReactivityActionIntent,
) -> None:
    shared_values = (
        ("event_id", event.event_id, intent.event_id),
        ("event_config_id", event.event_config_id, intent.event_config_id),
        ("activation_id", event.activation_id, intent.activation_id),
        ("event_type", event.event_type, intent.event_type),
        ("source", event.source, intent.source),
        ("branch_id", event.branch_id, intent.branch_id),
        ("projection_hash", event.projection_hash, intent.projection_hash),
        ("commit_id", event.commit_id, intent.commit_id),
        ("root_object_id", event.root_object_id, intent.root_object_id),
        (
            "object_instance_graph_id",
            event.object_instance_graph_id,
            intent.object_instance_graph_id,
        ),
        (
            "object_instance_graph_commit_id",
            event.object_instance_graph_commit_id,
            intent.object_instance_graph_commit_id,
        ),
        ("graph_hash_post", event.graph_hash_post, intent.graph_hash_post),
    )
    mismatches = [
        name
        for name, event_value, intent_value in shared_values
        if event_value != intent_value
    ]
    if mismatches:
        raise RuntimeError(
            "Experience action dispatch event/intent provenance mismatch: "
            + ",".join(mismatches)
        )


def _resolve_profile_and_binding(
    *,
    objects: Iterable[object],
    profile_key: str | None,
    intent: ReactivityActionIntent,
    index: MetaGraphRuntimeIndex,
) -> tuple[EnvironmentExperienceProfileConfig, ActionDispatchBinding]:
    normalized_profile_key = (profile_key or "").strip().casefold()
    profiles = tuple(
        item
        for item in objects
        if isinstance(item, EnvironmentExperienceProfileConfig)
        and (
            not normalized_profile_key
            or (item.key or "").strip().casefold() == normalized_profile_key
        )
    )
    if not profiles:
        raise RuntimeError(
            "Experience action dispatch profile is unavailable: "
            f"profile_key={profile_key!r}."
        )
    matches: list[tuple[EnvironmentExperienceProfileConfig, ActionDispatchBinding]] = []
    failures: list[str] = []
    for profile in profiles:
        resolution = resolve_action_dispatch_binding_from_environment_profile(
            profile_config=profile,
            intent=intent,
            index=index,
        )
        if resolution.binding is not None:
            matches.append((profile, resolution.binding))
        elif resolution.reason:
            failures.append(resolution.reason)
    if not matches:
        raise RuntimeError(
            "Experience action dispatch binding is unavailable in the committed "
            f"profile: reasons={sorted(set(failures))!r}."
        )
    if len(matches) != 1:
        raise RuntimeError(
            "Experience action dispatch binding is ambiguous across committed "
            f"profiles: matches={len(matches)}."
        )
    return matches[0]


def _resolve_endpoint_route(
    *,
    routes: Iterable[ServiceApiDependencyRouteDescriptor],
    endpoint_id: UUID,
) -> tuple[str, ServiceApiDependencyRouteDescriptor]:
    matches: list[tuple[str, ServiceApiDependencyRouteDescriptor]] = []
    for route in routes:
        for endpoint_refs in route.endpoint_refs_by_service.values():
            for endpoint_ref in endpoint_refs:
                try:
                    candidate_id = _endpoint_id_from_ref(endpoint_ref)
                except ValueError:
                    continue
                if candidate_id == endpoint_id:
                    matches.append((endpoint_ref, route))
    if not matches:
        raise RuntimeError(
            "Experience action dispatch ServiceHost route is unavailable for "
            f"api_capability_endpoint_id={endpoint_id}."
        )
    unique = {
        (endpoint_ref, route.host_id, route.provider_service_package_id): (
            endpoint_ref,
            route,
        )
        for endpoint_ref, route in matches
    }
    if len(unique) != 1:
        raise RuntimeError(
            "Experience action dispatch ServiceHost route is ambiguous for "
            f"api_capability_endpoint_id={endpoint_id}: matches={len(unique)}."
        )
    endpoint_ref, route = next(iter(unique.values()))
    if route.route_kind is not ServiceApiDependencyRouteKind.LOCAL_SERVICE_HOST_IPC:
        raise RuntimeError(
            "Experience action dispatch requires a local ServiceHost route: "
            f"endpoint_ref={endpoint_ref!r} route_kind={route.route_kind.value!r}."
        )
    return endpoint_ref, route


def _endpoint_id_from_ref(endpoint_ref: str) -> UUID:
    parts = tuple(part.strip() for part in endpoint_ref.split("."))
    if len(parts) != 3 or not all(parts):
        raise ValueError(
            "Service API endpoint ref must be api.capability.endpoint: "
            f"{endpoint_ref!r}."
        )
    api_name, capability_name, endpoint_name = parts
    api_id = stable_api_id(name=api_name)
    capability_id = stable_api_capability_id(
        api_id=api_id,
        name=capability_name,
    )
    return stable_api_capability_endpoint_id(
        api_capability_id=capability_id,
        name=endpoint_name,
    )


def _build_action_invocation_ir(
    *,
    endpoint_ref: str,
    binding: ActionDispatchBinding,
    class_configs_by_id: Mapping[UUID, ClassConfig],
) -> ApiInvocationIR:
    parts = endpoint_ref.split(".")
    request_class_id = binding.request_class_config_id
    request_class = binding.request_class_config or (
        class_configs_by_id.get(request_class_id)
        if request_class_id is not None
        else None
    )
    if request_class is None or request_class_id is None:
        raise RuntimeError(
            "Experience action dispatch binding lacks a hydrated request ClassConfig."
        )
    request_ref = _class_config_ref(request_class)
    response_class = (
        None
        if binding.response_class_config_id is None
        else class_configs_by_id.get(binding.response_class_config_id)
    )
    if binding.response_class_config_id is not None and response_class is None:
        raise RuntimeError(
            "Experience action dispatch binding response ClassConfig is unavailable "
            f"from the committed catalog: {binding.response_class_config_id}."
        )
    return ApiInvocationIR(
        api_name=parts[0],
        capability_name=parts[1],
        endpoint_name=parts[2],
        endpoint_ref=endpoint_ref,
        discriminant=endpoint_ref,
        source_path="experience-reference-branch",
        request_payload={},
        request_class_ref=request_ref,
        request_class_config_id=request_class_id,
        request_source_path="experience-reference-branch",
        response_class_ref=(
            _class_config_ref(response_class) if response_class is not None else None
        ),
        response_source_path=(
            "experience-reference-branch"
            if binding.response_class_config_id is not None
            else None
        ),
        stream=None,
        fulfillment_bindings=(),
        description="Experience action dispatch through committed ServiceHost route.",
        api_capability_endpoint_id=binding.api_capability_endpoint_id,
    )


def _class_config_ref(class_config: ClassConfig) -> str:
    ref = str(
        getattr(class_config, "fqn", None)
        or getattr(class_config, "class_fqn", None)
        or getattr(class_config, "name", "")
    ).strip()
    if not ref:
        raise RuntimeError(
            f"ClassConfig {class_config.id} lacks a generated class reference."
        )
    return ref


def _require_environment_id(
    *,
    lease: ExperienceSessionFeatureLease,
    host_context: ServiceApiHostContext,
) -> UUID:
    candidates = (
        lease.session_scope.environment_id,
        getattr(host_context.environment_context, "environment_id", None),
        getattr(host_context.operation_context, "environment_id", None),
    )
    for candidate in candidates:
        if isinstance(candidate, UUID):
            return candidate
    raise RuntimeError(
        "Experience action dispatch requires environment_id for Program continuation."
    )


def _hydrate_program_contract_pins(
    *,
    snapshot: ProgramOntologySnapshot,
    routes: Iterable[ServiceApiDependencyRouteDescriptor],
    class_configs_by_id: Mapping[UUID, ClassConfig],
) -> tuple[
    dict[UUID, ActionConfig],
    dict[UUID, ApiCapabilityEndpoint],
    dict[UUID, ProgramActionContinuationEndpointRoute],
]:
    actions: dict[UUID, ActionConfig] = {}
    endpoints: dict[UUID, ApiCapabilityEndpoint] = {}
    endpoint_routes: dict[UUID, ProgramActionContinuationEndpointRoute] = {}
    for intent in snapshot.instruction_intents_by_id.values():
        endpoint_id = intent.api_capability_endpoint_id
        request_class_id = intent.request_class_config_id
        response_class_id = intent.response_class_config_id
        if endpoint_id is None or request_class_id is None or response_class_id is None:
            raise ProgramActionContinuationActivationError(
                "program_action_continuation_intent_contract_pin_missing"
            )
        if (
            request_class_id not in class_configs_by_id
            or response_class_id not in class_configs_by_id
        ):
            raise ProgramActionContinuationActivationError(
                "program_action_continuation_class_config_catalog_missing"
            )
        try:
            endpoint_ref, _route = _resolve_endpoint_route(
                routes=routes,
                endpoint_id=endpoint_id,
            )
        except RuntimeError as exc:
            raise ProgramActionContinuationActivationError(str(exc)) from exc
        api_name, capability_name, endpoint_name = endpoint_ref.split(".")
        api_id = stable_api_id(name=api_name)
        capability_id = stable_api_capability_id(
            api_id=api_id,
            name=capability_name,
        )
        request_config_id = stable_api_capability_endpoint_request_config_id(
            api_capability_endpoint_id=endpoint_id,
            class_config_id=request_class_id,
        )
        response_config_id = stable_api_capability_endpoint_response_config_id(
            api_capability_endpoint_request_config_id=request_config_id,
            class_config_id=response_class_id,
        )
        response_config = ApiCapabilityEndpointResponseConfig(
            id=response_config_id,
            api_capability_endpoint_request_config_id=request_config_id,
            class_config_id=response_class_id,
            class_config=class_configs_by_id[response_class_id],
        )
        request_config = ApiCapabilityEndpointRequestConfig(
            id=request_config_id,
            api_capability_endpoint_id=endpoint_id,
            class_config_id=request_class_id,
            class_config=class_configs_by_id[request_class_id],
            response_config=response_config,
        )
        endpoint = ApiCapabilityEndpoint(
            id=endpoint_id,
            api_capability_id=capability_id,
            name=endpoint_name,
            request_config=request_config,
        )
        prior_endpoint = endpoints.setdefault(endpoint_id, endpoint)
        if (
            prior_endpoint.request_config is None
            or prior_endpoint.request_config.class_config_id != request_class_id
            or prior_endpoint.request_config.response_config is None
            or prior_endpoint.request_config.response_config.class_config_id
            != response_class_id
        ):
            raise ProgramActionContinuationActivationError(
                "program_action_continuation_endpoint_contract_ambiguous"
            )
        action = ActionConfig(
            id=intent.action_config_id,
            name=str(intent.action_config_id),
            description="Program-pinned action continuation contract.",
            action_type=str(intent.action_config_id),
            api_capability_endpoint_id=endpoint_id,
            api_capability_endpoint=prior_endpoint,
        )
        prior_action = actions.setdefault(intent.action_config_id, action)
        if prior_action.api_capability_endpoint_id != endpoint_id:
            raise ProgramActionContinuationActivationError(
                "program_action_continuation_action_endpoint_ambiguous"
            )
        endpoint_routes[endpoint_id] = ProgramActionContinuationEndpointRoute(
            api_capability_endpoint_id=endpoint_id,
            endpoint_ref=endpoint_ref,
            discriminant=endpoint_ref,
        )
    return actions, endpoints, endpoint_routes


def build_experience_action_intent_dispatcher_factory(
    *,
    host_context_provider: Callable[[], ServiceApiHostContext],
    reactivity_sdk_provider: Callable[[], ReactivitySdkClient],
    runtime_loader: ExperienceActionDispatchServiceRuntimeLoader,
) -> ActionIntentDispatcherFactory:
    def _for_lease(lease: ExperienceSessionFeatureLease) -> ActionIntentDispatcher:
        async def _dispatch(
            event: ActorReactivityBridgeEvent,
            intent: ReactivityActionIntent,
        ) -> ActionDispatchBridgeResult:
            _require_event_matches_intent(event=event, intent=intent)
            host_context = host_context_provider()
            sdk: ReactivitySdkClient = reactivity_sdk_provider()
            runtime = await runtime_loader.load_action_dispatch_runtime(
                lease=lease,
                event=event,
                intent=intent,
                host_context=host_context,
            )
            environment_id = _require_environment_id(
                lease=lease,
                host_context=host_context,
            )
            return await dispatch_requested_action_intent(
                profile_config=runtime.profile_config,
                intent=intent,
                reactivity=sdk,
                execution_claimer=sdk,
                runtime=runtime.runtime,
                index=runtime.index,
                actor_id=host_context.operation_context.actor_id,
                environment_id=environment_id,
                source_lane=runtime.source_lane,
                target_lane=runtime.target_lane,
                ir=runtime.ir,
                source_commit=ApiInvocationSourceCommit(
                    branch_id=intent.branch_id,
                    projection_hash=intent.projection_hash,
                    commit_id=intent.commit_id,
                    object_instance_graph_id=intent.object_instance_graph_id,
                    object_instance_graph_commit_id=(
                        intent.object_instance_graph_commit_id
                    ),
                ),
                role_evidence=runtime.role_evidence,
                subscription_id=intent.actor_subscription_id,
                terminal_fulfillment_invoker=(runtime.terminal_fulfillment_invoker),
                program_continuation_activation_runtime=(
                    runtime.program_continuation_activation_runtime
                ),
            )

        return _dispatch

    return _for_lease


__all__ = [
    "CommittedExperienceActionDispatchServiceRuntimeLoader",
    "EXPERIENCE_ACTION_DISPATCH_PROJECTION_NAMES",
    "ExperienceActionDispatchServiceRuntime",
    "ExperienceActionDispatchServiceRuntimeLoader",
    "build_experience_action_intent_dispatcher_factory",
]
