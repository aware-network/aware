from __future__ import annotations

# pyright: reportMissingImports=false, reportAttributeAccessIssue=false

from pathlib import Path
from typing import Any, Protocol, cast
from uuid import UUID

from pydantic import BaseModel
from aware_types import JsonArray, JsonObject

from aware_experience_ontology.stable_ids import (
    stable_experience_session_id,
    stable_experience_session_profile_id,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionRequest,
    MetaGraphInvokeFunctionResponse,
)
from aware_meta_service_dto.graph.instance.function_call_target import (
    MetaGraphFunctionCallTarget,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex

from aware_experience.section_graph_binding.api_models import (
    ActivateExperienceLayoutGraphBindingRequest as CanonicalActivateExperienceLayoutGraphBindingRequest,
)
from aware_experience.section_graph_binding.api_models import (
    ActivateExperienceSectionGraphBindingRequest as CanonicalActivateExperienceSectionGraphBindingRequest,
)
from aware_experience.section_graph_binding.api_models import (
    ApplyExperienceViewEventTransitionRequest as CanonicalApplyExperienceViewEventTransitionRequest,
)
from aware_experience.section_graph_binding.api_models import (
    GetExperienceLayoutGraphBindingCatalogRequest as CanonicalGetExperienceLayoutGraphBindingCatalogRequest,
)
from aware_experience.section_graph_binding.api_models import (
    GetExperienceLayoutGraphBindingStateRequest as CanonicalGetExperienceLayoutGraphBindingStateRequest,
)
from aware_experience.section_graph_binding.api_models import (
    GetExperienceSectionGraphBindingCatalogRequest as CanonicalGetExperienceSectionGraphBindingCatalogRequest,
)
from aware_experience.section_graph_binding.api_models import (
    GetExperienceSectionGraphBindingStateRequest as CanonicalGetExperienceSectionGraphBindingStateRequest,
)
from aware_experience.section_graph_binding.api_models import (
    InvokeExperienceViewInvocationActionRequest as CanonicalInvokeExperienceViewInvocationActionRequest,
)
from aware_experience.section_graph_binding.api_models import (
    RecordExperienceViewInvocationActionRequest as CanonicalRecordExperienceViewInvocationActionRequest,
)
from aware_experience.section_graph_binding.api_models import (
    WatchExperienceSectionGraphBindingsRequest as CanonicalWatchExperienceSectionGraphBindingsRequest,
)
from aware_experience.thread_layout_resolution.api_models import (
    ResolveExperienceThreadLayoutIntentRequest as CanonicalResolveExperienceThreadLayoutIntentRequest,
)
from aware_experience.environment_profile.api_models import (
    ApplyExperienceEnvironmentProfileProgramsRequest as CanonicalApplyExperienceEnvironmentProfileProgramsRequest,
)
from aware_experience.environment_profile.api_models import (
    ProvisionExperienceEnvironmentProfileRequest as CanonicalProvisionExperienceEnvironmentProfileRequest,
)
from aware_experience.environment_profile.api_models import (
    UpsertExperienceEnvironmentProfileRequest as CanonicalUpsertExperienceEnvironmentProfileRequest,
)
from aware_experience.environment_profile.service import (
    ExperienceEnvironmentProfileReactivityPolicyBackend,
    ExperienceEnvironmentProfileRuntimeBackend,
    apply_experience_environment_profile_programs,
    provision_experience_environment_profile,
    upsert_experience_environment_profile,
)
from aware_experience.package_projection_ownership import (
    resolve_experience_package_projection_ownership_catalog,
)
from aware_experience.environment_profile.reactivity_policy import (
    has_profile_reactivity_events,
)
from aware_experience.section_graph_binding.service import (
    activate_layout_graph_binding,
    activate_section_graph_binding,
    apply_view_event_transition,
    get_layout_graph_binding_catalog,
    get_layout_graph_binding_state,
    get_section_graph_binding_catalog,
    get_section_graph_binding_state,
    invoke_experience_view_invocation_action,
    record_experience_view_invocation_action,
    stream_watch_section_graph_bindings,
    watch_section_graph_bindings,
)
from aware_experience.thread_layout_resolution.service import (
    resolve_thread_layout_intent,
)
from aware_experience.layout_transition.api_models import (
    RequestExperienceLayoutTransitionRequest as CanonicalRequestExperienceLayoutTransitionRequest,
)
from aware_experience.layout_transition.service import (
    request_layout_transition,
)
from aware_experience_service_dto.experience.environment_profile.service_operation import (
    ApplyExperienceEnvironmentProfileProgramsRequest,
    ApplyExperienceEnvironmentProfileProgramsResponse,
    ProvisionExperienceEnvironmentProfileRequest,
    ProvisionExperienceEnvironmentProfileResponse,
    UpsertExperienceEnvironmentProfileRequest,
    UpsertExperienceEnvironmentProfileResponse,
)
from aware_experience_service_dto.experience.package_materialization.service_operation import (
    ResolveExperiencePackageProjectionOwnershipRequest,
    ResolveExperiencePackageProjectionOwnershipResponse,
)
from aware_experience_service_dto.experience.package_materialization.models import (
    ExperiencePackageProjectionOwnershipCatalog,
)
from aware_experience_service_dto.experience.program.service_operation import (
    ApplyProgramRefRequest,
    ApplyProgramRefResponse,
    GetTurnExecutionRequest,
    GetTurnExecutionResponse,
    RunProgramRequest,
    RunProgramResponse,
    SubmitProgramTurnRequest,
    SubmitProgramTurnResponse,
)
from aware_experience_service_dto.experience.actor_admission.models import (
    ExperienceActorConfigAdmissionReceipt,
)
from aware_experience_service_dto.experience.actor_admission.service_operation import (
    AdmitExperienceActorConfigRequest,
    AdmitExperienceActorConfigResponse,
)
from aware_experience_service_dto.experience.layout_transition.service_operation import (
    RequestExperienceLayoutTransitionRequest,
    RequestExperienceLayoutTransitionResponse,
)
from aware_experience_service_dto.experience.section_graph_binding.models import (
    ExperienceInvocationActionAdmissionPreflight,
    ExperienceSectionGraphBindingStateEvent,
)
from aware_experience_service_dto.experience.section_graph_binding.service_operation import (
    ActivateExperienceLayoutGraphBindingRequest,
    ActivateExperienceLayoutGraphBindingResponse,
    ActivateExperienceSectionGraphBindingRequest,
    ActivateExperienceSectionGraphBindingResponse,
    ApplyExperienceViewEventTransitionRequest,
    ApplyExperienceViewEventTransitionResponse,
    GetExperienceLayoutGraphBindingCatalogRequest,
    GetExperienceLayoutGraphBindingCatalogResponse,
    GetExperienceLayoutGraphBindingStateRequest,
    GetExperienceLayoutGraphBindingStateResponse,
    GetExperienceSectionGraphBindingCatalogRequest,
    GetExperienceSectionGraphBindingCatalogResponse,
    GetExperienceSectionGraphBindingStateRequest,
    GetExperienceSectionGraphBindingStateResponse,
    InvokeExperienceViewInvocationActionRequest,
    InvokeExperienceViewInvocationActionResponse,
    RecordExperienceViewInvocationActionRequest,
    RecordExperienceViewInvocationActionResponse,
    ResolveExperienceInvocationActionRolePolicyRequest,
    ResolveExperienceInvocationActionRolePolicyResponse,
    WatchExperienceSectionGraphBindingsRequest,
    WatchExperienceSectionGraphBindingsResponse,
)
from aware_experience_service_dto.experience.view_state.models import (
    ExperienceViewStateEvent,
)
from aware_experience_service_dto.experience.view_state.service_operation import (
    WatchExperienceViewStateRequest,
    WatchExperienceViewStateResponse,
)
from aware_experience_service_dto.experience.thread_layout_resolution.service_operation import (
    ResolveExperienceThreadLayoutIntentRequest,
    ResolveExperienceThreadLayoutIntentResponse,
)
from aware_experience_service_dto.experience.session_handoff.models import (
    ExperienceSessionHandoffActorAdmissionReceipt,
    ExperienceSessionHandoffActorContext,
    ExperienceSessionHandoffFeatureLeaseReceipt,
    ExperienceSessionIdentityEvidence,
    ExperienceSessionHandoffReceipt,
    ExperienceSessionHandoffScope,
    ExperienceSessionHandoffStatusReceipt,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentSessionRequest,
    EnvironmentActorAdmissionReceipt,
    EnvironmentSessionAttentionResolution,
    EnvironmentSessionJoinReceipt,
)
from aware_identity_service_dto.session.session import SessionDescribeRequest
from aware_experience_service_dto.experience.session_handoff.service_operation import (
    EnsureExperienceSessionHandoffRequest,
    EnsureExperienceSessionHandoffResponse,
    GetExperienceSessionHandoffStatusRequest,
    GetExperienceSessionHandoffStatusResponse,
)
from aware_experience_service_dto.experience.session_context.models import (
    ExperienceSessionContextReceipt,
    ExperienceSessionLensContext,
)
from aware_experience_service_dto.experience.session_context.service_operation import (
    ResolveExperienceSessionContextRequest,
    ResolveExperienceSessionContextResponse,
)
from aware_experience_service_dto.experience.session_view_frame.models import (
    ExperienceSessionViewFrame,
    ExperienceSessionViewFrameLens,
)
from aware_experience_service_dto.experience.session_view_frame.service_operation import (
    ResolveExperienceSessionViewFrameRequest,
    ResolveExperienceSessionViewFrameResponse,
)
from aware_experience_service_dto.experience.session_commit.service_operation import (
    DescribeExperienceSessionRequest,
    DescribeExperienceSessionResponse,
    ExperienceSessionView,
    MountExperienceSessionProfileRequest,
    MountExperienceSessionProfileResponse,
    StartExperienceSessionRequest,
    StartExperienceSessionResponse,
)
from aware_service_runtime.api_ingress.host_context import (
    ServiceApiHostContext,
    current_service_api_host_context,
)
from aware_service_runtime.api_ingress.ontology_replica_context import (
    require_service_ontology_replica_query,
)
from aware_service_runtime.local_service_host_api_client import (
    build_service_api_client_for_api_package,
)
from aware_experience_service.reactivity_policy_backend import (
    ExperienceReactivitySdkPolicyBackend,
)
from aware_experience_service.actor_admission_service import (
    AdmitExperienceActorConfigRequestSpec,
    ExperienceActorConfigAdmissionBackend,
    IdentityRoleAssignmentApiClient,
    admit_experience_actor_config,
)
from aware_experience_service.actor_action_policy_service import (
    ExperienceInvocationActionRolePolicyBackend,
    ResolveExperienceInvocationActionRolePolicyRequestSpec,
    resolve_experience_invocation_action_role_policy,
)
from aware_experience_service.invocation_action_preflight_service import (
    ExperienceInvocationActionTargetBackend,
    InvokeExperienceViewInvocationActionPreflightRequestSpec,
    preflight_experience_view_invocation_action,
)
from aware_experience_service.session_feature_service import (
    AdmitExperienceSessionActorRequest,
    EnsureExperienceSessionFeatureRequest,
    ExperienceFeatureLeaseSnapshotSpec,
    ExperienceSessionActorAdmissionSpec,
    ExperienceSessionActorContextSpec,
    GetExperienceSessionSnapshotRequest,
    IdentityExperienceSessionApiClient,
    ExperienceSessionScopeSpec,
    admit_experience_session_actor,
    ensure_experience_session_feature,
    get_experience_session_snapshot,
)
from aware_experience_service.session_context_service import (
    EnvironmentSessionContextApiClient,
    ResolveExperienceSessionContextRequestSpec,
    resolve_experience_session_context,
)
from aware_experience_service.session_view_frame_service import (
    ResolveExperienceSessionViewFrameRequestSpec,
    resolve_experience_session_view_frame,
)
from aware_experience_service.view_state_watch import (
    ExperienceViewStateBackend,
    RouteBackedExperienceViewStateBackend,
    stream_watch_experience_view_state,
    watch_experience_view_state,
)

_REACTIVITY_SERVICE_API_PACKAGE_NAME = "reactivity-service-api"
_IDENTITY_SERVICE_API_PACKAGE_NAME = "identity-service-api"
_ENVIRONMENT_SERVICE_API_PACKAGE_NAME = "environment-service-api"


def build_aware_experience_service_protocol_handler(
    *,
    environment_profile_backend: (
        ExperienceEnvironmentProfileRuntimeBackend | None
    ) = None,
    program_runtime_backend: "ExperienceProgramRuntimeBackend | None" = None,
    actor_config_admission_backend: ExperienceActorConfigAdmissionBackend | None = None,
    action_policy_backend: ExperienceInvocationActionRolePolicyBackend | None = None,
    action_target_backend: ExperienceInvocationActionTargetBackend | None = None,
    view_state_backend: ExperienceViewStateBackend | None = None,
    identity_api_client: (
        IdentityRoleAssignmentApiClient | IdentityExperienceSessionApiClient | None
    ) = None,
    environment_api_client: EnvironmentSessionContextApiClient | None = None,
) -> object:
    return _AwareExperienceServiceProtocolHandler(
        environment_profile_backend=environment_profile_backend,
        program_runtime_backend=program_runtime_backend,
        actor_config_admission_backend=actor_config_admission_backend,
        action_policy_backend=action_policy_backend,
        action_target_backend=action_target_backend,
        view_state_backend=view_state_backend,
        identity_api_client=identity_api_client,
        environment_api_client=environment_api_client,
    )


class ExperienceProgramRuntimeBackend(Protocol):
    async def apply_program_ref(
        self,
        *,
        request: ApplyProgramRefRequest,
        host_context: ServiceApiHostContext | None = None,
    ) -> ApplyProgramRefResponse: ...

    async def submit_program_turn(
        self,
        *,
        request: SubmitProgramTurnRequest,
        host_context: ServiceApiHostContext | None = None,
    ) -> SubmitProgramTurnResponse: ...

    async def run_program(
        self,
        *,
        request: RunProgramRequest,
        host_context: ServiceApiHostContext | None = None,
    ) -> RunProgramResponse: ...

    async def get_turn_execution(
        self,
        *,
        request: GetTurnExecutionRequest,
        host_context: ServiceApiHostContext | None = None,
    ) -> GetTurnExecutionResponse: ...


class _ExperienceProtocolSupport:
    def __init__(
        self,
        *,
        environment_profile_backend: (
            ExperienceEnvironmentProfileRuntimeBackend | None
        ) = None,
        program_runtime_backend: ExperienceProgramRuntimeBackend | None = None,
        actor_config_admission_backend: (
            ExperienceActorConfigAdmissionBackend | None
        ) = None,
        action_policy_backend: (
            ExperienceInvocationActionRolePolicyBackend | None
        ) = None,
        action_target_backend: ExperienceInvocationActionTargetBackend | None = None,
        view_state_backend: ExperienceViewStateBackend | None = None,
        identity_api_client: (
            IdentityRoleAssignmentApiClient | IdentityExperienceSessionApiClient | None
        ) = None,
        environment_api_client: EnvironmentSessionContextApiClient | None = None,
    ) -> None:
        self.environment_profile_backend = environment_profile_backend
        self.program_runtime_backend = program_runtime_backend
        self.actor_config_admission_backend = actor_config_admission_backend
        self.action_policy_backend = action_policy_backend
        self.action_target_backend = action_target_backend
        self.view_state_backend = (
            view_state_backend or RouteBackedExperienceViewStateBackend()
        )
        self.identity_api_client = identity_api_client
        self.environment_api_client = environment_api_client

    def host_context(self) -> ServiceApiHostContext:
        host_context = current_service_api_host_context()
        if host_context is None:
            raise RuntimeError(
                "Experience service protocol requires an active Service API host context."
            )
        return host_context

    def reactivity_policy_backend(
        self,
        *,
        host_context: ServiceApiHostContext,
    ) -> ExperienceEnvironmentProfileReactivityPolicyBackend | None:
        invoker = build_service_api_client_for_api_package(
            host_context.service_api_dependency_routes,
            api_package_name=_REACTIVITY_SERVICE_API_PACKAGE_NAME,
            actor_id=host_context.operation_context.actor_id,
            invocation_context=cast(
                JsonObject | None,
                _host_invocation_context_payload(host_context),
            ),
        )
        if invoker is None:
            return None

        from aware_reactivity_sdk import ReactivitySdkClient
        from aware_reactivity_service_api import AwareReactivityServiceApiClient

        return ExperienceReactivitySdkPolicyBackend(
            sdk=ReactivitySdkClient(
                api_client=AwareReactivityServiceApiClient(invoker),
            )
        )

    def identity_session_api_client(self) -> Any:
        if self.identity_api_client is not None:
            return self.identity_api_client
        host_context = self.host_context()
        invoker = build_service_api_client_for_api_package(
            host_context.service_api_dependency_routes,
            api_package_name=_IDENTITY_SERVICE_API_PACKAGE_NAME,
            actor_id=host_context.operation_context.actor_id,
            invocation_context=cast(
                JsonObject | None,
                _host_invocation_context_payload(host_context),
            ),
        )
        if invoker is None:
            raise RuntimeError(
                "ExperienceSession start requires the Identity service API route."
            )
        from aware_identity_service_api import AwareIdentityServiceApiClient

        return AwareIdentityServiceApiClient(invoker)

    def environment_session_api_client(self) -> Any:
        if self.environment_api_client is not None:
            return self.environment_api_client
        host_context = self.host_context()
        invoker = build_service_api_client_for_api_package(
            host_context.service_api_dependency_routes,
            api_package_name=_ENVIRONMENT_SERVICE_API_PACKAGE_NAME,
            actor_id=host_context.operation_context.actor_id,
            invocation_context=cast(
                JsonObject | None,
                _host_invocation_context_payload(host_context),
            ),
        )
        if invoker is None:
            raise RuntimeError(
                "ExperienceSession start requires the Environment service API route."
            )
        from aware_environment_service_api import AwareEnvironmentServiceApiClient

        return AwareEnvironmentServiceApiClient(invoker)

    async def commit_projection_constructor(
        self,
        *,
        projection_name: str,
        class_name: str,
        constructor_name: str,
        root_object_id: UUID,
        kwargs: JsonObject,
    ) -> MetaGraphInvokeFunctionResponse:
        host_context = self.host_context()
        graph_gateway = host_context.graph_gateway
        if graph_gateway is None:
            raise RuntimeError(
                f"{projection_name} commit requires a Service graph gateway."
            )
        actor_id = host_context.operation_context.actor_id
        if actor_id is None:
            raise RuntimeError(
                f"{projection_name} commit requires an admitted actor id."
            )

        graph_context: object
        if host_context.materialization is not None:
            graph_context = host_context.materialization.graph_context
        elif host_context.graph_context_provider is not None:
            graph_context = (
                await host_context.graph_context_provider.resolve_graph_context()
            )
        else:
            resolve_graph_context = getattr(
                graph_gateway,
                "resolve_graph_context",
                None,
            )
            if not callable(resolve_graph_context):
                raise RuntimeError(
                    f"{projection_name} graph gateway cannot resolve graph context."
                )
            graph_context = await resolve_graph_context()
        runtime_index_value = getattr(graph_context, "index", graph_context)
        if not hasattr(runtime_index_value, "class_configs_by_id") or not hasattr(
            runtime_index_value,
            "opg_by_hash",
        ):
            raise RuntimeError(
                f"{projection_name} graph context has no Meta runtime index."
            )
        runtime_index = cast(MetaGraphRuntimeIndex, runtime_index_value)
        projection, class_config = _resolve_projection_root(
            runtime_index=runtime_index,
            projection_name=projection_name,
            class_name=class_name,
        )
        function_id = _resolve_constructor_id(
            class_config=class_config,
            constructor_name=constructor_name,
            projection_name=projection_name,
        )
        response = await graph_gateway.invoke_function(
            request=MetaGraphInvokeFunctionRequest(
                actor_id=actor_id,
                domain_branch_id=root_object_id,
                domain_projection_hash=str(projection.projection_hash),
                call_target=MetaGraphFunctionCallTarget.opg_constructor,
                object_projection_graph_id=UUID(str(projection.id)),
                function_id=function_id,
                args=cast(JsonArray, []),
                kwargs=kwargs,
                commit=True,
                publish=False,
            ),
            graph_context=runtime_index,
        )
        result = MetaGraphInvokeFunctionResponse.model_validate(response)
        if result.status.strip().lower() != "succeeded":
            raise RuntimeError(
                f"{projection_name} constructor failed: "
                f"{result.error or result.status}"
            )
        if result.root_object_id != root_object_id:
            raise RuntimeError(
                f"{projection_name} constructor returned a non-canonical root id."
            )
        if result.object_instance_graph_commit_id is None:
            raise RuntimeError(
                f"{projection_name} constructor returned no graph commit id."
            )
        if not result.graph_hash_post:
            raise RuntimeError(f"{projection_name} constructor returned no graph hash.")
        return result


def _resolve_projection_root(
    *,
    runtime_index: MetaGraphRuntimeIndex,
    projection_name: str,
    class_name: str,
) -> tuple[Any, Any]:
    class_configs_by_id = cast(Any, runtime_index.class_configs_by_id)
    matches: list[tuple[Any, Any]] = []
    for projection in cast(Any, runtime_index.opg_by_hash).values():
        if (getattr(projection, "name", "") or "").strip() != projection_name:
            continue
        for node in projection.object_projection_graph_nodes or []:
            if not node.is_root:
                continue
            class_config = class_configs_by_id.get(node.class_config_id)
            if class_config is not None and (
                (getattr(class_config, "name", "") or "").strip() == class_name
            ):
                matches.append((projection, class_config))
    if len(matches) != 1:
        raise RuntimeError(
            f"{projection_name} projection root is missing or ambiguous: "
            f"matches={len(matches)}"
        )
    return matches[0]


def _resolve_constructor_id(
    *,
    class_config: Any,
    constructor_name: str,
    projection_name: str,
) -> UUID:
    matches = [
        function_config.id
        for link in class_config.class_config_function_configs or []
        for function_config in [link.function_config]
        if function_config is not None
        and (function_config.name or "").strip() == constructor_name
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"{projection_name} {constructor_name} constructor is missing or "
            f"ambiguous: matches={len(matches)}"
        )
    return UUID(str(matches[0]))


class _DescribeExperienceSessionCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def describe_experience_session(
        self,
        request: DescribeExperienceSessionRequest,
    ) -> DescribeExperienceSessionResponse:
        host_context = self._support.host_context()
        graph_context: object
        if host_context.materialization is not None:
            graph_context = host_context.materialization.graph_context
        elif host_context.graph_context_provider is not None:
            graph_context = (
                await host_context.graph_context_provider.resolve_graph_context()
            )
        else:
            graph_gateway = host_context.graph_gateway
            resolve_graph_context = getattr(
                graph_gateway, "resolve_graph_context", None
            )
            if not callable(resolve_graph_context):
                raise RuntimeError(
                    "ExperienceSession describe requires a Meta runtime graph context."
                )
            graph_context = await resolve_graph_context()
        runtime_index_value = getattr(graph_context, "index", graph_context)
        runtime_index = cast(MetaGraphRuntimeIndex, runtime_index_value)
        projection, class_config = _resolve_projection_root(
            runtime_index=runtime_index,
            projection_name="ExperienceSession",
            class_name="ExperienceSession",
        )
        record = require_service_ontology_replica_query().get_class_instance(
            instance_id=request.experience_session_id
        )
        if record is None:
            return DescribeExperienceSessionResponse(
                request_id=request.request_id,
                status="not_found",
                session=None,
            )
        if (
            record.class_config_id != UUID(str(class_config.id))
            or record.projection_hash != str(projection.projection_hash)
            or record.root_object_id != request.experience_session_id
        ):
            raise RuntimeError(
                "ExperienceSession describe found mismatched projection evidence."
            )
        attributes = record.attributes
        return DescribeExperienceSessionResponse(
            request_id=request.request_id,
            status="found",
            session=ExperienceSessionView(
                experience_session_id=request.experience_session_id,
                environment_experience_id=UUID(
                    str(attributes["environment_experience_id"])
                ),
                identity_session_id=UUID(str(attributes["identity_session_id"])),
                environment_session_id=UUID(str(attributes["environment_session_id"])),
                state=str(attributes["state"]),
                domain_commit_id=record.updated_commit_id,
            ),
        )


class _StartExperienceSessionCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def start_experience_session(
        self,
        request: StartExperienceSessionRequest,
    ) -> StartExperienceSessionResponse:
        environment_client = self._support.environment_session_api_client()
        environment_result = (
            await environment_client.environment.session.describe_session(
                DescribeEnvironmentSessionRequest(
                    environment_id=request.environment_id,
                    environment_session_id=request.environment_session_id,
                )
            )
        )
        environment_session = environment_result.session
        if environment_session is None:
            raise RuntimeError(
                "ExperienceSession start requires a committed EnvironmentSession."
            )
        if environment_session.environment_id != request.environment_id:
            raise RuntimeError(
                "ExperienceSession EnvironmentSession authority mismatch."
            )
        parent_identity_session_id = environment_session.identity_session_id
        if parent_identity_session_id is None:
            raise RuntimeError(
                "ExperienceSession parent EnvironmentSession has no Identity Session."
            )

        identity_client = self._support.identity_session_api_client()
        identity_result = (
            await identity_client.identity.describe_session.describe_session(
                SessionDescribeRequest(session_id=request.identity_session_id)
            )
        )
        child_identity_session = identity_result.session
        if child_identity_session is None:
            raise RuntimeError(
                "ExperienceSession start requires a committed child Identity Session."
            )
        if child_identity_session.parent_session_id != parent_identity_session_id:
            raise RuntimeError(
                "ExperienceSession Identity Session parent does not match the "
                "EnvironmentSession Identity Session."
            )

        state = request.state.strip().lower()
        if state not in {"active", "suspended", "closed"}:
            raise ValueError(f"Unsupported ExperienceSession state: {request.state!r}.")
        experience_session_id = stable_experience_session_id(
            environment_experience_id=request.environment_experience_id,
            identity_session_id=request.identity_session_id,
        )
        result = await self._support.commit_projection_constructor(
            projection_name="ExperienceSession",
            class_name="ExperienceSession",
            constructor_name="build_via_environment_experience",
            root_object_id=experience_session_id,
            kwargs=cast(
                JsonObject,
                {
                    "environment_experience_id": str(request.environment_experience_id),
                    "identity_session_id": str(request.identity_session_id),
                    "environment_session_id": str(request.environment_session_id),
                    "state": state,
                },
            ),
        )
        return StartExperienceSessionResponse(
            request_id=request.request_id,
            success=True,
            experience_session_id=experience_session_id,
            environment_experience_id=request.environment_experience_id,
            environment_id=request.environment_id,
            identity_session_id=request.identity_session_id,
            environment_session_id=request.environment_session_id,
            state=state,
            domain_commit_id=result.domain_commit_id,
            object_instance_graph_commit_id=result.object_instance_graph_commit_id,
            graph_hash_post=result.graph_hash_post,
        )


class _MountExperienceSessionProfileCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def mount_experience_session_profile(
        self,
        request: MountExperienceSessionProfileRequest,
    ) -> MountExperienceSessionProfileResponse:
        status = request.status.strip().lower()
        if not status:
            raise ValueError("ExperienceSessionProfile status must not be blank.")
        metadata_json = cast(JsonObject, dict(request.metadata_json or {}))
        mount_id = stable_experience_session_profile_id(
            experience_session_id=request.experience_session_id,
            profile_id=request.profile_id,
        )
        result = await self._support.commit_projection_constructor(
            projection_name="ExperienceSessionProfile",
            class_name="ExperienceSessionProfile",
            constructor_name="build_via_experience_session",
            root_object_id=mount_id,
            kwargs=cast(
                JsonObject,
                {
                    "experience_session_id": str(request.experience_session_id),
                    "profile_id": str(request.profile_id),
                    "status": status,
                    "metadata_json": metadata_json,
                },
            ),
        )
        return MountExperienceSessionProfileResponse(
            request_id=request.request_id,
            success=True,
            experience_session_profile_id=mount_id,
            experience_session_id=request.experience_session_id,
            profile_id=request.profile_id,
            status=status,
            metadata_json=metadata_json,
            domain_commit_id=result.domain_commit_id,
            object_instance_graph_commit_id=result.object_instance_graph_commit_id,
            graph_hash_post=result.graph_hash_post,
        )


class _ExperienceActorAdmissionCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def admit_experience_actor_config(
        self,
        request: AdmitExperienceActorConfigRequest,
    ) -> AdmitExperienceActorConfigResponse:
        response = await admit_experience_actor_config(
            request=_convert_model(
                request,
                model_cls=AdmitExperienceActorConfigRequestSpec,
            ),
            host_context=self._support.host_context(),
            admission_backend=self._support.actor_config_admission_backend,
            identity_api_client=cast(
                IdentityRoleAssignmentApiClient | None,
                self._support.identity_api_client,
            ),
        )
        receipt = _convert_model(
            response.receipt,
            model_cls=ExperienceActorConfigAdmissionReceipt,
        )
        return AdmitExperienceActorConfigResponse(
            request_id=response.request_id,
            accepted=response.accepted,
            status=response.status,
            error=response.error,
            receipt=receipt,
            evidence=cast(JsonObject, dict(response.evidence)),
        )


class _RequestExperienceLayoutTransitionCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def request_experience_layout_transition(
        self,
        request: RequestExperienceLayoutTransitionRequest,
    ) -> RequestExperienceLayoutTransitionResponse:
        response = await request_layout_transition(
            request=_convert_model(
                request,
                model_cls=CanonicalRequestExperienceLayoutTransitionRequest,
            ),
            host_context=self._support.host_context(),
        )
        return _convert_model(
            response,
            model_cls=RequestExperienceLayoutTransitionResponse,
        )


class _ResolveExperienceThreadLayoutIntentCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def resolve_experience_thread_layout_intent(
        self,
        request: ResolveExperienceThreadLayoutIntentRequest,
    ) -> ResolveExperienceThreadLayoutIntentResponse:
        response = await resolve_thread_layout_intent(
            request=_convert_model(
                request,
                model_cls=CanonicalResolveExperienceThreadLayoutIntentRequest,
            ),
            host_context=self._support.host_context(),
        )
        return _convert_model(
            response,
            model_cls=ResolveExperienceThreadLayoutIntentResponse,
        )


class _ExperienceEnvironmentProfileCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def upsert_experience_environment_profile(
        self,
        request: UpsertExperienceEnvironmentProfileRequest,
    ) -> UpsertExperienceEnvironmentProfileResponse:
        host_context = self._support.host_context()
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalUpsertExperienceEnvironmentProfileRequest,
        )
        reactivity_policy_backend = None
        if not canonical_request.validate_only and has_profile_reactivity_events(
            profile=canonical_request.profile
        ):
            reactivity_policy_backend = self._support.reactivity_policy_backend(
                host_context=host_context,
            )
        response = await upsert_experience_environment_profile(
            request=canonical_request,
            host_context=host_context,
            runtime_backend=self._support.environment_profile_backend,
            reactivity_policy_backend=reactivity_policy_backend,
        )
        return _convert_model(
            response,
            model_cls=UpsertExperienceEnvironmentProfileResponse,
        )

    async def provision_experience_environment_profile(
        self,
        request: ProvisionExperienceEnvironmentProfileRequest,
    ) -> ProvisionExperienceEnvironmentProfileResponse:
        response = await provision_experience_environment_profile(
            request=_convert_model(
                request,
                model_cls=CanonicalProvisionExperienceEnvironmentProfileRequest,
            ),
            host_context=self._support.host_context(),
            runtime_backend=self._support.environment_profile_backend,
        )
        return _convert_model(
            response,
            model_cls=ProvisionExperienceEnvironmentProfileResponse,
        )

    async def apply_experience_environment_profile_programs(
        self,
        request: ApplyExperienceEnvironmentProfileProgramsRequest,
    ) -> ApplyExperienceEnvironmentProfileProgramsResponse:
        response = await apply_experience_environment_profile_programs(
            request=_convert_model(
                request,
                model_cls=CanonicalApplyExperienceEnvironmentProfileProgramsRequest,
            ),
            host_context=self._support.host_context(),
            runtime_backend=self._support.environment_profile_backend,
        )
        return _convert_model(
            response,
            model_cls=ApplyExperienceEnvironmentProfileProgramsResponse,
        )


class _ExperienceProgramCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def apply_program_ref(
        self,
        request: ApplyProgramRefRequest,
    ) -> ApplyProgramRefResponse:
        backend = self._support.program_runtime_backend
        if backend is None:
            return ApplyProgramRefResponse(
                request_id=request.request_id,
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="unavailable",
                error="experience_program_runtime_backend_unavailable",
                program_ref=request.program_ref,
            )
        return await backend.apply_program_ref(
            request=request,
            host_context=self._support.host_context(),
        )

    async def submit_program_turn(
        self,
        request: SubmitProgramTurnRequest,
    ) -> SubmitProgramTurnResponse:
        backend = self._support.program_runtime_backend
        if backend is None:
            return SubmitProgramTurnResponse(
                request_id=request.request_id,
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="unavailable",
                error="experience_program_runtime_backend_unavailable",
                mailbox_key=request.mailbox_key,
            )
        return await backend.submit_program_turn(
            request=request,
            host_context=self._support.host_context(),
        )

    async def run_program(
        self,
        request: RunProgramRequest,
    ) -> RunProgramResponse:
        backend = self._support.program_runtime_backend
        if backend is None:
            return RunProgramResponse(
                request_id=request.request_id,
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="unavailable",
                error="experience_program_runtime_backend_unavailable",
                program_ref=request.program_ref,
                mailbox_key=request.mailbox_key,
            )
        return await backend.run_program(
            request=request,
            host_context=self._support.host_context(),
        )

    async def get_turn_execution(
        self,
        request: GetTurnExecutionRequest,
    ) -> GetTurnExecutionResponse:
        backend = self._support.program_runtime_backend
        if backend is None:
            return GetTurnExecutionResponse(
                request_id=request.request_id,
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="unavailable",
                error="experience_program_runtime_backend_unavailable",
                turn_id=request.turn_id,
            )
        return await backend.get_turn_execution(
            request=request,
            host_context=self._support.host_context(),
        )


class _ExperiencePackageMaterializationCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def resolve_experience_package_projection_ownership(
        self,
        request: ResolveExperiencePackageProjectionOwnershipRequest,
    ) -> ResolveExperiencePackageProjectionOwnershipResponse:
        _ = self._support
        if not request.workspace_root or not request.experience_toml_path:
            return ResolveExperiencePackageProjectionOwnershipResponse(
                request_id=request.request_id,
                success=False,
                status="missing_package_source",
                error=(
                    "workspace_root and experience_toml_path are required for "
                    "source-backed Experience package projection ownership resolution."
                ),
                package_name=request.package_name,
                experience_name=request.experience_name,
                catalog=ExperiencePackageProjectionOwnershipCatalog(
                    package_name=request.package_name,
                    experience_name=request.experience_name,
                    workspace_root=request.workspace_root,
                    experience_toml_path=request.experience_toml_path,
                    status="missing_package_source",
                    entries=[],
                    missing_required_projection_refs=[],
                    evidence=JsonObject(),
                ),
                evidence=cast(JsonObject, {"validate_only": request.validate_only}),
            )
        try:
            catalog = resolve_experience_package_projection_ownership_catalog(
                workspace_root=Path(request.workspace_root),
                experience_toml_path=Path(request.experience_toml_path),
            )
        except Exception as exc:
            return ResolveExperiencePackageProjectionOwnershipResponse(
                request_id=request.request_id,
                success=False,
                status="error",
                error=str(exc),
                package_name=request.package_name,
                experience_name=request.experience_name,
                catalog=ExperiencePackageProjectionOwnershipCatalog(
                    package_name=request.package_name,
                    experience_name=request.experience_name,
                    workspace_root=request.workspace_root,
                    experience_toml_path=request.experience_toml_path,
                    status="error",
                    entries=[],
                    missing_required_projection_refs=[],
                    evidence=cast(JsonObject, {"error_type": type(exc).__name__}),
                ),
                evidence=cast(JsonObject, {"error_type": type(exc).__name__}),
            )
        return ResolveExperiencePackageProjectionOwnershipResponse(
            request_id=request.request_id,
            success=not catalog.missing_required_projection_refs,
            status=catalog.status,
            info="Experience package projection ownership resolved.",
            package_name=catalog.package_name,
            experience_name=request.experience_name or catalog.experience_name,
            catalog=catalog,
            evidence=cast(JsonObject, {"validate_only": request.validate_only}),
        )


class _GetExperienceSectionGraphBindingCatalogCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def get_experience_section_graph_binding_catalog(
        self,
        request: GetExperienceSectionGraphBindingCatalogRequest,
    ) -> GetExperienceSectionGraphBindingCatalogResponse:
        response = await get_section_graph_binding_catalog(
            request=_convert_model(
                request,
                model_cls=CanonicalGetExperienceSectionGraphBindingCatalogRequest,
            ),
            host_context=self._support.host_context(),
        )
        return _convert_model(
            response,
            model_cls=GetExperienceSectionGraphBindingCatalogResponse,
        )


class _GetExperienceLayoutGraphBindingCatalogCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def get_experience_layout_graph_binding_catalog(
        self,
        request: GetExperienceLayoutGraphBindingCatalogRequest,
    ) -> GetExperienceLayoutGraphBindingCatalogResponse:
        response = await get_layout_graph_binding_catalog(
            request=_convert_model(
                request,
                model_cls=CanonicalGetExperienceLayoutGraphBindingCatalogRequest,
            ),
            host_context=self._support.host_context(),
        )
        return _convert_model(
            response,
            model_cls=GetExperienceLayoutGraphBindingCatalogResponse,
        )


class _GetExperienceSectionGraphBindingStateCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def get_experience_section_graph_binding_state(
        self,
        request: GetExperienceSectionGraphBindingStateRequest,
    ) -> GetExperienceSectionGraphBindingStateResponse:
        response = await get_section_graph_binding_state(
            request=_convert_model(
                request,
                model_cls=CanonicalGetExperienceSectionGraphBindingStateRequest,
            ),
            host_context=self._support.host_context(),
        )
        return _convert_model(
            response,
            model_cls=GetExperienceSectionGraphBindingStateResponse,
        )


class _GetExperienceLayoutGraphBindingStateCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def get_experience_layout_graph_binding_state(
        self,
        request: GetExperienceLayoutGraphBindingStateRequest,
    ) -> GetExperienceLayoutGraphBindingStateResponse:
        response = await get_layout_graph_binding_state(
            request=_convert_model(
                request,
                model_cls=CanonicalGetExperienceLayoutGraphBindingStateRequest,
            ),
            host_context=self._support.host_context(),
        )
        return _convert_model(
            response,
            model_cls=GetExperienceLayoutGraphBindingStateResponse,
        )


class _ActivateExperienceSectionGraphBindingCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def activate_experience_section_graph_binding(
        self,
        request: ActivateExperienceSectionGraphBindingRequest,
    ) -> ActivateExperienceSectionGraphBindingResponse:
        response = await activate_section_graph_binding(
            request=_convert_model(
                request,
                model_cls=CanonicalActivateExperienceSectionGraphBindingRequest,
            ),
            host_context=self._support.host_context(),
        )
        return _convert_model(
            response,
            model_cls=ActivateExperienceSectionGraphBindingResponse,
        )


class _ActivateExperienceLayoutGraphBindingCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def activate_experience_layout_graph_binding(
        self,
        request: ActivateExperienceLayoutGraphBindingRequest,
    ) -> ActivateExperienceLayoutGraphBindingResponse:
        response = await activate_layout_graph_binding(
            request=_convert_model(
                request,
                model_cls=CanonicalActivateExperienceLayoutGraphBindingRequest,
            ),
            host_context=self._support.host_context(),
        )
        return _convert_model(
            response,
            model_cls=ActivateExperienceLayoutGraphBindingResponse,
        )


class _ApplyExperienceViewEventTransitionCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def apply_experience_view_event_transition(
        self,
        request: ApplyExperienceViewEventTransitionRequest,
    ) -> ApplyExperienceViewEventTransitionResponse:
        response = await apply_view_event_transition(
            request=_convert_model(
                request,
                model_cls=CanonicalApplyExperienceViewEventTransitionRequest,
            ),
            host_context=self._support.host_context(),
        )
        return _convert_model(
            response,
            model_cls=ApplyExperienceViewEventTransitionResponse,
        )


class _RecordExperienceViewInvocationActionCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def record_experience_view_invocation_action(
        self,
        request: RecordExperienceViewInvocationActionRequest,
    ) -> RecordExperienceViewInvocationActionResponse:
        response = await record_experience_view_invocation_action(
            request=_convert_model(
                request,
                model_cls=CanonicalRecordExperienceViewInvocationActionRequest,
            ),
            host_context=self._support.host_context(),
        )
        return _convert_model(
            response,
            model_cls=RecordExperienceViewInvocationActionResponse,
        )


class _InvokeExperienceViewInvocationActionCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def invoke_experience_view_invocation_action(
        self,
        request: InvokeExperienceViewInvocationActionRequest,
    ) -> InvokeExperienceViewInvocationActionResponse:
        host_context = self._support.host_context()
        preflight = await preflight_experience_view_invocation_action(
            request=_convert_model(
                request,
                model_cls=InvokeExperienceViewInvocationActionPreflightRequestSpec,
            ),
            host_context=host_context,
            target_backend=self._support.action_target_backend,
            policy_backend=self._support.action_policy_backend,
        )
        preflight_dto = _convert_model(
            preflight,
            model_cls=ExperienceInvocationActionAdmissionPreflight,
        )
        if not preflight.accepted:
            return InvokeExperienceViewInvocationActionResponse(
                request_id=request.request_id,
                success=False,
                error=preflight.status,
                experience_name=request.experience_name,
                receipt=None,
                admission_preflight=preflight_dto,
            )
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalInvokeExperienceViewInvocationActionRequest,
        )
        canonical_request = canonical_request.model_copy(
            update={
                "admission_evidence": {
                    **dict(canonical_request.admission_evidence),
                    "experience_invocation_action_admission_preflight": (
                        preflight.model_dump(mode="json")
                    ),
                }
            }
        )
        response = await invoke_experience_view_invocation_action(
            request=canonical_request,
            host_context=host_context,
        )
        service_response = _convert_model(
            response,
            model_cls=InvokeExperienceViewInvocationActionResponse,
        )
        return service_response.model_copy(
            update={"admission_preflight": preflight_dto},
        )


class _ResolveExperienceInvocationActionRolePolicyCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def resolve_experience_invocation_action_role_policy(
        self,
        request: ResolveExperienceInvocationActionRolePolicyRequest,
    ) -> ResolveExperienceInvocationActionRolePolicyResponse:
        response = await resolve_experience_invocation_action_role_policy(
            request=_convert_model(
                request,
                model_cls=ResolveExperienceInvocationActionRolePolicyRequestSpec,
            ),
            host_context=self._support.host_context(),
            policy_backend=self._support.action_policy_backend,
        )
        return _convert_model(
            response,
            model_cls=ResolveExperienceInvocationActionRolePolicyResponse,
        )


class _WatchExperienceSectionGraphBindingsCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def watch_experience_section_graph_bindings(
        self,
        request: WatchExperienceSectionGraphBindingsRequest,
    ) -> WatchExperienceSectionGraphBindingsResponse:
        response = await watch_section_graph_bindings(
            request=_convert_model(
                request,
                model_cls=CanonicalWatchExperienceSectionGraphBindingsRequest,
            ),
            host_context=self._support.host_context(),
        )
        return _convert_model(
            response,
            model_cls=WatchExperienceSectionGraphBindingsResponse,
        )

    async def stream_watch_experience_section_graph_bindings(
        self,
        request: WatchExperienceSectionGraphBindingsRequest,
    ):
        async for event in stream_watch_section_graph_bindings(
            request=_convert_model(
                request,
                model_cls=CanonicalWatchExperienceSectionGraphBindingsRequest,
            ),
            host_context=self._support.host_context(),
        ):
            yield _convert_model(
                event,
                model_cls=ExperienceSectionGraphBindingStateEvent,
            )


class _WatchExperienceViewStateCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def watch_experience_view_state(
        self,
        request: WatchExperienceViewStateRequest,
    ) -> WatchExperienceViewStateResponse:
        return await watch_experience_view_state(
            request=request,
            host_context=self._support.host_context(),
            backend=self._support.view_state_backend,
            identity_api_client=cast(
                IdentityExperienceSessionApiClient | None,
                self._support.identity_api_client,
            ),
            environment_api_client=self._support.environment_api_client,
        )

    async def stream_watch_experience_view_state(
        self,
        request: WatchExperienceViewStateRequest,
    ):
        async for event in stream_watch_experience_view_state(
            request=request,
            host_context=self._support.host_context(),
            backend=self._support.view_state_backend,
            identity_api_client=cast(
                IdentityExperienceSessionApiClient | None,
                self._support.identity_api_client,
            ),
            environment_api_client=self._support.environment_api_client,
        ):
            yield _convert_model(
                event,
                model_cls=ExperienceViewStateEvent,
            )


class _ExperienceSessionHandoffCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def ensure_experience_session_handoff(
        self,
        request: EnsureExperienceSessionHandoffRequest,
    ) -> EnsureExperienceSessionHandoffResponse:
        host_context = self._support.host_context()
        session_scope = _session_handoff_scope_spec(request.session_scope)
        if (
            session_scope.environment_session_id is None
            and request.environment_session_join is not None
        ):
            session_scope = session_scope.model_copy(
                update={
                    "environment_session_id": (
                        request.environment_session_join.environment_session_id
                    )
                }
            )
        actor_context = _session_handoff_actor_context_spec(request.actor_context)
        admission = await admit_experience_session_actor(
            request=AdmitExperienceSessionActorRequest(
                request_id=request.request_id,
                session_scope=session_scope,
                actor_context=actor_context,
                environment_admission=_session_handoff_environment_admission_spec(
                    request.environment_admission,
                ),
                environment_session_join=_session_handoff_environment_session_join_spec(
                    request.environment_session_join,
                ),
                experience_actor_admission=_session_handoff_experience_actor_admission_spec(
                    request.experience_actor_admission,
                ),
                experience_identity_session_config_id=(
                    request.experience_identity_session_config_id
                ),
                idempotency_key=request.idempotency_key,
            ),
            host_context=host_context,
            identity_api_client=cast(
                IdentityExperienceSessionApiClient | None,
                self._support.identity_api_client,
            ),
        )
        if not admission.admission.admitted:
            receipt = _session_handoff_receipt(
                request=request,
                admission=admission.admission,
                feature_lease=None,
                accepted=False,
                status="blocked",
                error=admission.admission.reason,
            )
            return EnsureExperienceSessionHandoffResponse(
                request_id=request.request_id,
                accepted=False,
                status="blocked",
                error=admission.admission.reason,
                receipt=receipt,
                evidence=cast(JsonObject, dict(receipt.evidence)),
            )

        feature = await ensure_experience_session_feature(
            request=EnsureExperienceSessionFeatureRequest(
                session_scope=session_scope,
                feature_key=request.feature.feature_key,
                config=_session_handoff_feature_config(request),
                lease_key=request.feature.lease_key or request.idempotency_key,
            ),
            host_context=host_context,
        )
        status = "active" if feature.accepted else "blocked"
        error = feature.error
        receipt = _session_handoff_receipt(
            request=request,
            admission=feature.actor_admission or admission.admission,
            feature_lease=feature.snapshot,
            accepted=feature.accepted,
            status=status,
            error=error,
        )
        return EnsureExperienceSessionHandoffResponse(
            request_id=request.request_id,
            accepted=feature.accepted,
            status=status,
            error=error,
            receipt=receipt,
            evidence=cast(JsonObject, dict(receipt.evidence)),
        )

    async def get_experience_session_handoff_status(
        self,
        request: GetExperienceSessionHandoffStatusRequest,
    ) -> GetExperienceSessionHandoffStatusResponse:
        host_context = self._support.host_context()
        session_scope = _session_handoff_scope_spec(request.session_scope)
        response = await get_experience_session_snapshot(
            request=GetExperienceSessionSnapshotRequest(
                session_scope=session_scope,
            ),
            host_context=host_context,
        )
        receipt = _session_handoff_status_receipt(
            request=request,
            accepted=response.accepted,
            snapshot=response.snapshot,
            error=response.error,
        )
        return GetExperienceSessionHandoffStatusResponse(
            request_id=request.request_id,
            accepted=response.accepted,
            status=receipt.status,
            error=response.error,
            receipt=receipt,
            evidence=cast(JsonObject, dict(receipt.evidence)),
        )


class _ExperienceSessionContextCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def resolve_experience_session_context(
        self,
        request: ResolveExperienceSessionContextRequest,
    ) -> ResolveExperienceSessionContextResponse:
        response = await resolve_experience_session_context(
            request=_convert_model(
                request,
                model_cls=ResolveExperienceSessionContextRequestSpec,
            ),
            host_context=self._support.host_context(),
            identity_api_client=cast(
                IdentityExperienceSessionApiClient | None,
                self._support.identity_api_client,
            ),
            environment_api_client=self._support.environment_api_client,
        )
        receipt = _session_context_receipt(response.receipt)
        return ResolveExperienceSessionContextResponse(
            request_id=response.request_id,
            accepted=response.accepted,
            status=response.status,
            error=response.error,
            receipt=receipt,
            evidence=cast(JsonObject, dict(response.evidence)),
        )


class _ExperienceSessionViewFrameCapabilityHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self._support = support

    async def resolve_experience_session_view_frame(
        self,
        request: ResolveExperienceSessionViewFrameRequest,
    ) -> ResolveExperienceSessionViewFrameResponse:
        response = await resolve_experience_session_view_frame(
            request=_convert_model(
                request,
                model_cls=ResolveExperienceSessionViewFrameRequestSpec,
            ),
            host_context=self._support.host_context(),
            identity_api_client=cast(
                IdentityExperienceSessionApiClient | None,
                self._support.identity_api_client,
            ),
            environment_api_client=self._support.environment_api_client,
        )
        frame = _session_view_frame(response.frame)
        return ResolveExperienceSessionViewFrameResponse(
            request_id=response.request_id,
            accepted=response.accepted,
            status=response.status,
            error=response.error,
            frame=frame,
            evidence=cast(JsonObject, dict(response.evidence)),
        )


class _ExperienceApiServiceProtocolHandler:
    def __init__(self, *, support: _ExperienceProtocolSupport) -> None:
        self.describe_experience_session = _DescribeExperienceSessionCapabilityHandler(
            support=support
        )
        self.start_experience_session = _StartExperienceSessionCapabilityHandler(
            support=support
        )
        self.mount_experience_session_profile = (
            _MountExperienceSessionProfileCapabilityHandler(support=support)
        )
        self.actor_admission = _ExperienceActorAdmissionCapabilityHandler(
            support=support
        )
        self.resolve_experience_thread_layout_intent = (
            _ResolveExperienceThreadLayoutIntentCapabilityHandler(support=support)
        )
        self.request_experience_layout_transition = (
            _RequestExperienceLayoutTransitionCapabilityHandler(support=support)
        )
        self.environment_profile = _ExperienceEnvironmentProfileCapabilityHandler(
            support=support
        )
        self.program = _ExperienceProgramCapabilityHandler(support=support)
        self.package_materialization = (
            _ExperiencePackageMaterializationCapabilityHandler(support=support)
        )
        self.get_experience_section_graph_binding_catalog = (
            _GetExperienceSectionGraphBindingCatalogCapabilityHandler(support=support)
        )
        self.get_experience_layout_graph_binding_catalog = (
            _GetExperienceLayoutGraphBindingCatalogCapabilityHandler(support=support)
        )
        self.get_experience_section_graph_binding_state = (
            _GetExperienceSectionGraphBindingStateCapabilityHandler(support=support)
        )
        self.get_experience_layout_graph_binding_state = (
            _GetExperienceLayoutGraphBindingStateCapabilityHandler(support=support)
        )
        self.activate_experience_section_graph_binding = (
            _ActivateExperienceSectionGraphBindingCapabilityHandler(support=support)
        )
        self.activate_experience_layout_graph_binding = (
            _ActivateExperienceLayoutGraphBindingCapabilityHandler(support=support)
        )
        self.apply_experience_view_event_transition = (
            _ApplyExperienceViewEventTransitionCapabilityHandler(support=support)
        )
        self.record_experience_view_invocation_action = (
            _RecordExperienceViewInvocationActionCapabilityHandler(support=support)
        )
        self.invoke_experience_view_invocation_action = (
            _InvokeExperienceViewInvocationActionCapabilityHandler(support=support)
        )
        self.resolve_experience_invocation_action_role_policy = (
            _ResolveExperienceInvocationActionRolePolicyCapabilityHandler(
                support=support
            )
        )
        self.watch_experience_section_graph_bindings = (
            _WatchExperienceSectionGraphBindingsCapabilityHandler(support=support)
        )
        self.watch_experience_view_state = _WatchExperienceViewStateCapabilityHandler(
            support=support
        )
        self.session_handoff = _ExperienceSessionHandoffCapabilityHandler(
            support=support
        )
        self.session_context = _ExperienceSessionContextCapabilityHandler(
            support=support
        )
        self.session_view_frame = _ExperienceSessionViewFrameCapabilityHandler(
            support=support
        )


class _AwareExperienceServiceProtocolHandler:
    def __init__(
        self,
        *,
        environment_profile_backend: (
            ExperienceEnvironmentProfileRuntimeBackend | None
        ) = None,
        program_runtime_backend: ExperienceProgramRuntimeBackend | None = None,
        actor_config_admission_backend: (
            ExperienceActorConfigAdmissionBackend | None
        ) = None,
        action_policy_backend: (
            ExperienceInvocationActionRolePolicyBackend | None
        ) = None,
        action_target_backend: ExperienceInvocationActionTargetBackend | None = None,
        view_state_backend: ExperienceViewStateBackend | None = None,
        identity_api_client: (
            IdentityRoleAssignmentApiClient | IdentityExperienceSessionApiClient | None
        ) = None,
        environment_api_client: EnvironmentSessionContextApiClient | None = None,
    ) -> None:
        support = _ExperienceProtocolSupport(
            environment_profile_backend=environment_profile_backend,
            program_runtime_backend=program_runtime_backend,
            actor_config_admission_backend=actor_config_admission_backend,
            action_policy_backend=action_policy_backend,
            action_target_backend=action_target_backend,
            view_state_backend=view_state_backend,
            identity_api_client=identity_api_client,
            environment_api_client=environment_api_client,
        )
        self.experience = _ExperienceApiServiceProtocolHandler(support=support)


def _convert_model(value: object, *, model_cls: type[BaseModel]) -> Any:
    payload = value
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json", exclude_none=True)
    return model_cls.model_validate(payload)


def _host_invocation_context_payload(
    host_context: ServiceApiHostContext,
) -> dict[str, object] | None:
    if host_context.invocation_context is None:
        return None
    return dict(host_context.invocation_context)


def _session_handoff_scope_spec(
    scope: ExperienceSessionHandoffScope,
) -> ExperienceSessionScopeSpec:
    return ExperienceSessionScopeSpec(
        experience_name=scope.experience_name,
        profile_key=scope.profile_key,
        environment_id=scope.environment_id,
        environment_session_id=scope.environment_session_id,
        actor_id=scope.actor_id,
        process_id=scope.process_id,
        thread_id=scope.thread_id,
        branch_id=scope.branch_id,
        projection_hash=scope.projection_hash,
        workspace_session_id=scope.workspace_session_id,
    )


def _session_handoff_actor_context_spec(
    actor_context: ExperienceSessionHandoffActorContext | None,
) -> ExperienceSessionActorContextSpec | None:
    if actor_context is None:
        return None
    return ExperienceSessionActorContextSpec(
        status=actor_context.status,
        kind=actor_context.kind,
        source=actor_context.source,
        actor_id=actor_context.actor_id,
        identity_id=actor_context.identity_id,
        execution_id=actor_context.execution_id,
        provider_key=actor_context.provider_key,
        provider_session_id=actor_context.provider_session_id,
        agent_process_thread_id=actor_context.agent_process_thread_id,
        evidence=dict(actor_context.evidence),
    )


def _session_handoff_environment_admission_spec(
    environment_admission: EnvironmentActorAdmissionReceipt | None,
) -> EnvironmentActorAdmissionReceipt | None:
    if environment_admission is None:
        return None
    return _convert_model(
        environment_admission, model_cls=EnvironmentActorAdmissionReceipt
    )


def _session_handoff_environment_session_join_spec(
    environment_session_join: EnvironmentSessionJoinReceipt | None,
) -> EnvironmentSessionJoinReceipt | None:
    if environment_session_join is None:
        return None
    return _convert_model(
        environment_session_join,
        model_cls=EnvironmentSessionJoinReceipt,
    )


def _session_handoff_experience_actor_admission_spec(
    experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None,
) -> ExperienceActorConfigAdmissionReceipt | None:
    if experience_actor_admission is None:
        return None
    return _convert_model(
        experience_actor_admission,
        model_cls=ExperienceActorConfigAdmissionReceipt,
    )


def _session_handoff_feature_config(
    request: EnsureExperienceSessionHandoffRequest,
) -> dict[str, Any]:
    config = dict(request.feature.config)
    if request.feature.reason is not None:
        config.setdefault("handoff_reason", request.feature.reason)
    config.setdefault(
        "handoff_scope",
        request.session_scope.model_dump(mode="json", exclude_none=True),
    )
    config.setdefault("handoff_evidence", dict(request.evidence))
    if request.environment_admission is not None:
        config.setdefault(
            "environment_admission",
            request.environment_admission.model_dump(
                mode="json",
                exclude_none=True,
            ),
        )
    if request.environment_session_join is not None:
        config.setdefault(
            "environment_session_join",
            request.environment_session_join.model_dump(
                mode="json",
                exclude_none=True,
            ),
        )
    if request.experience_actor_admission is not None:
        config.setdefault(
            "experience_actor_admission",
            request.experience_actor_admission.model_dump(
                mode="json",
                exclude_none=True,
            ),
        )
    if request.experience_identity_session_config_id is not None:
        config.setdefault(
            "experience_identity_session_config_id",
            str(request.experience_identity_session_config_id),
        )
    return config


def _session_handoff_environment_admission_receipt(
    environment_admission: EnvironmentActorAdmissionReceipt | None,
) -> EnvironmentActorAdmissionReceipt | None:
    if environment_admission is None:
        return None
    return _convert_model(
        environment_admission, model_cls=EnvironmentActorAdmissionReceipt
    )


def _session_handoff_environment_session_join_receipt(
    environment_session_join: EnvironmentSessionJoinReceipt | None,
) -> EnvironmentSessionJoinReceipt | None:
    if environment_session_join is None:
        return None
    return _convert_model(
        environment_session_join,
        model_cls=EnvironmentSessionJoinReceipt,
    )


def _session_handoff_experience_actor_admission_receipt(
    experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None,
) -> ExperienceActorConfigAdmissionReceipt | None:
    if experience_actor_admission is None:
        return None
    return _convert_model(
        experience_actor_admission,
        model_cls=ExperienceActorConfigAdmissionReceipt,
    )


def _session_handoff_identity_evidence(
    identity_evidence: object | None,
) -> ExperienceSessionIdentityEvidence | None:
    if identity_evidence is None:
        return None
    return _convert_model(
        identity_evidence,
        model_cls=ExperienceSessionIdentityEvidence,
    )


def _session_handoff_admission_receipt(
    admission: ExperienceSessionActorAdmissionSpec | None,
) -> ExperienceSessionHandoffActorAdmissionReceipt | None:
    if admission is None:
        return None
    return ExperienceSessionHandoffActorAdmissionReceipt(
        status=admission.status,
        admitted=admission.admitted,
        reason=admission.reason,
        actor_id=admission.actor_id,
        actor_kind=admission.actor_kind,
        identity_id=admission.identity_id,
        execution_id=admission.execution_id,
        provider_key=admission.provider_key,
        provider_session_id=admission.provider_session_id,
        agent_process_thread_id=admission.agent_process_thread_id,
        environment_admission=_session_handoff_environment_admission_receipt(
            admission.environment_admission,
        ),
        environment_session_join=_session_handoff_environment_session_join_receipt(
            admission.environment_session_join,
        ),
        experience_actor_admission=_session_handoff_experience_actor_admission_receipt(
            admission.experience_actor_admission,
        ),
        identity_evidence=_session_handoff_identity_evidence(
            admission.identity_evidence,
        ),
        blockers=list(admission.blockers),
        next_suggested_action=admission.next_suggested_action,
        evidence=cast(JsonObject, dict(admission.evidence)),
    )


def _session_handoff_feature_lease_receipt(
    snapshot: ExperienceFeatureLeaseSnapshotSpec | None,
) -> ExperienceSessionHandoffFeatureLeaseReceipt | None:
    if snapshot is None:
        return None
    return ExperienceSessionHandoffFeatureLeaseReceipt(
        lease_key=snapshot.lease_key,
        feature_key=snapshot.feature_key,
        desired_state=snapshot.desired_state,
        worker_status=snapshot.worker_status,
        revision=snapshot.revision,
        info=snapshot.info,
        last_error=snapshot.last_error,
        health_payload=cast(JsonObject | None, snapshot.health_payload),
    )


def _session_handoff_status_feature_lease_receipt(
    *,
    snapshot: ExperienceFeatureLeaseSnapshotSpec,
    include_health: bool,
) -> ExperienceSessionHandoffFeatureLeaseReceipt:
    return ExperienceSessionHandoffFeatureLeaseReceipt(
        lease_key=snapshot.lease_key,
        feature_key=snapshot.feature_key,
        desired_state=snapshot.desired_state,
        worker_status=snapshot.worker_status,
        revision=snapshot.revision,
        info=snapshot.info,
        last_error=snapshot.last_error,
        health_payload=cast(
            JsonObject | None,
            snapshot.health_payload if include_health else None,
        ),
    )


def _session_handoff_status_receipt(
    *,
    request: GetExperienceSessionHandoffStatusRequest,
    accepted: bool,
    snapshot: object | None,
    error: str | None,
) -> ExperienceSessionHandoffStatusReceipt:
    leases = []
    actor_admission = None
    if snapshot is not None:
        raw_leases = list(getattr(snapshot, "leases", []) or [])
        leases = [
            _session_handoff_status_feature_lease_receipt(
                snapshot=lease,
                include_health=request.include_health,
            )
            for lease in raw_leases
            if _session_handoff_status_lease_matches_request(
                lease=lease,
                feature_key=request.feature_key,
                lease_key=request.lease_key,
            )
        ]
        actor_admission = getattr(snapshot, "actor_admission", None)
    status = _session_handoff_status_from_leases(
        accepted=accepted,
        leases=leases,
        error=error,
    )
    evidence: dict[str, object] = {
        "source": "aware_experience_service.session_handoff_status",
        "feature_key": request.feature_key,
        "lease_key": request.lease_key,
        "include_health": request.include_health,
        "feature_lease_count": len(leases),
    }
    if request.evidence:
        evidence["request_evidence"] = dict(request.evidence)
    return ExperienceSessionHandoffStatusReceipt(
        accepted=accepted,
        status=status,
        session_scope=request.session_scope,
        actor_admission=_session_handoff_admission_receipt(actor_admission),
        identity_evidence=_session_handoff_identity_evidence(
            getattr(actor_admission, "identity_evidence", None),
        ),
        feature_lease=leases[0] if len(leases) == 1 else None,
        feature_leases=leases,
        feature_lease_count=len(leases),
        error=error,
        evidence=cast(JsonObject, evidence),
    )


def _session_handoff_status_lease_matches_request(
    *,
    lease: ExperienceFeatureLeaseSnapshotSpec,
    feature_key: str | None,
    lease_key: str | None,
) -> bool:
    if feature_key is not None and lease.feature_key != feature_key:
        return False
    if lease_key is not None and lease.lease_key != lease_key:
        return False
    return True


def _session_handoff_status_from_leases(
    *,
    accepted: bool,
    leases: list[ExperienceSessionHandoffFeatureLeaseReceipt],
    error: str | None,
) -> str:
    if not accepted:
        return "unavailable"
    if error:
        return "blocked"
    if not leases:
        return "idle"
    worker_statuses = {lease.worker_status for lease in leases}
    if "failed" in worker_statuses:
        return "degraded"
    if "running" in worker_statuses:
        return "active"
    if worker_statuses == {"completed"}:
        return "completed"
    if worker_statuses == {"released"}:
        return "released"
    return "known"


def _session_handoff_receipt(
    *,
    request: EnsureExperienceSessionHandoffRequest,
    admission: ExperienceSessionActorAdmissionSpec | None,
    feature_lease: ExperienceFeatureLeaseSnapshotSpec | None,
    accepted: bool,
    status: str,
    error: str | None,
) -> ExperienceSessionHandoffReceipt:
    admitted = admission.admitted if admission is not None else False
    feature_enabled = accepted and feature_lease is not None
    session_scope = request.session_scope
    if (
        admission is not None
        and admission.session_scope.environment_session_id is not None
        and session_scope.environment_session_id is None
    ):
        session_scope = session_scope.model_copy(
            update={
                "environment_session_id": admission.session_scope.environment_session_id
            }
        )
    evidence: dict[str, object] = {
        "source": "aware_experience_service.session_handoff",
        "actor_admission_status": admission.status if admission is not None else None,
        "feature_key": request.feature.feature_key,
    }
    if request.evidence:
        evidence["request_evidence"] = dict(request.evidence)
    return ExperienceSessionHandoffReceipt(
        accepted=accepted,
        status=status,
        admitted=admitted,
        feature_enabled=feature_enabled,
        session_scope=session_scope,
        actor_admission=_session_handoff_admission_receipt(admission),
        identity_evidence=_session_handoff_identity_evidence(
            admission.identity_evidence if admission is not None else None,
        ),
        feature_lease=_session_handoff_feature_lease_receipt(feature_lease),
        idempotency_key=request.idempotency_key,
        error=error,
        evidence=cast(JsonObject, evidence),
    )


def _session_context_receipt(
    receipt: object,
) -> ExperienceSessionContextReceipt:
    raw_scope = getattr(receipt, "session_scope")
    session_scope = ExperienceSessionHandoffScope(
        experience_name=raw_scope.experience_name,
        profile_key=raw_scope.profile_key,
        environment_id=raw_scope.environment_id,
        environment_session_id=raw_scope.environment_session_id,
        actor_id=raw_scope.actor_id,
        process_id=raw_scope.process_id,
        thread_id=raw_scope.thread_id,
        branch_id=raw_scope.branch_id,
        projection_hash=raw_scope.projection_hash,
        workspace_session_id=raw_scope.workspace_session_id,
    )
    lens = getattr(receipt, "lens", None)
    return ExperienceSessionContextReceipt(
        accepted=bool(getattr(receipt, "accepted")),
        status=str(getattr(receipt, "status")),
        error=cast(str | None, getattr(receipt, "error", None)),
        session_scope=session_scope,
        actor_admission=_session_handoff_admission_receipt(
            getattr(receipt, "actor_admission", None),
        ),
        identity_evidence=_session_handoff_identity_evidence(
            getattr(receipt, "identity_evidence", None),
        ),
        environment_attention_resolution=_session_context_environment_attention_resolution(
            getattr(receipt, "environment_attention_resolution", None),
        ),
        lens=(
            ExperienceSessionLensContext(
                status=lens.status,
                view_ref=lens.view_ref,
                projection_view_key=lens.projection_view_key,
                section_graph_binding_key=lens.section_graph_binding_key,
                blockers=list(lens.blockers),
                evidence=cast(JsonObject, dict(lens.evidence)),
            )
            if lens is not None
            else None
        ),
        blockers=list(getattr(receipt, "blockers", [])),
        evidence=cast(JsonObject, dict(getattr(receipt, "evidence", {}) or {})),
    )


def _session_context_environment_attention_resolution(
    resolution: object | None,
) -> EnvironmentSessionAttentionResolution | None:
    if resolution is None:
        return None
    return _convert_model(
        resolution,
        model_cls=EnvironmentSessionAttentionResolution,
    )


def _session_view_frame(frame: object) -> ExperienceSessionViewFrame:
    return ExperienceSessionViewFrame(
        accepted=bool(getattr(frame, "accepted")),
        status=str(getattr(frame, "status")),
        error=cast(str | None, getattr(frame, "error", None)),
        session_scope=_session_view_frame_scope(getattr(frame, "session_scope")),
        actor_admission=_session_handoff_admission_receipt(
            getattr(frame, "actor_admission", None),
        ),
        identity_evidence=_session_handoff_identity_evidence(
            getattr(frame, "identity_evidence", None),
        ),
        environment_attention_resolution=_session_context_environment_attention_resolution(
            getattr(frame, "environment_attention_resolution", None),
        ),
        context_receipt=(
            _session_context_receipt(getattr(frame, "context_receipt"))
            if getattr(frame, "context_receipt", None) is not None
            else None
        ),
        lens=_session_view_frame_lens(getattr(frame, "lens", None)),
        environment_id=getattr(frame, "environment_id", None),
        environment_profile_id=getattr(frame, "environment_profile_id", None),
        environment_session_id=getattr(frame, "environment_session_id", None),
        environment_navigation_context_id=getattr(
            frame,
            "environment_navigation_context_id",
            None,
        ),
        environment_session_thread_id=getattr(
            frame,
            "environment_session_thread_id",
            None,
        ),
        environment_session_attention_session_id=getattr(
            frame,
            "environment_session_attention_session_id",
            None,
        ),
        process_id=getattr(frame, "process_id", None),
        thread_id=getattr(frame, "thread_id", None),
        thread_layout_id=getattr(frame, "thread_layout_id", None),
        branch_id=getattr(frame, "branch_id", None),
        projection_hash=getattr(frame, "projection_hash", None),
        attention_session_id=getattr(frame, "attention_session_id", None),
        active_attention_focus_transition_id=getattr(
            frame,
            "active_attention_focus_transition_id",
            None,
        ),
        transition_count=int(getattr(frame, "transition_count", 0) or 0),
        blockers=list(getattr(frame, "blockers", [])),
        evidence=cast(JsonObject, dict(getattr(frame, "evidence", {}) or {})),
    )


def _session_view_frame_scope(raw_scope: object) -> ExperienceSessionHandoffScope:
    return ExperienceSessionHandoffScope(
        namespace=getattr(raw_scope, "namespace", None),
        experience_name=str(getattr(raw_scope, "experience_name")),
        profile_key=getattr(raw_scope, "profile_key", None),
        environment_id=getattr(raw_scope, "environment_id", None),
        environment_session_id=getattr(raw_scope, "environment_session_id", None),
        actor_id=getattr(raw_scope, "actor_id", None),
        process_id=getattr(raw_scope, "process_id", None),
        thread_id=getattr(raw_scope, "thread_id", None),
        branch_id=getattr(raw_scope, "branch_id", None),
        projection_hash=getattr(raw_scope, "projection_hash", None),
        workspace_session_id=getattr(raw_scope, "workspace_session_id", None),
        view_ref=getattr(raw_scope, "view_ref", None),
        window_key=getattr(raw_scope, "window_key", None),
        layout_key=getattr(raw_scope, "layout_key", None),
        layout_config_id=getattr(raw_scope, "layout_config_id", None),
        section_key=getattr(raw_scope, "section_key", None),
        layout_config_section_config_id=getattr(
            raw_scope,
            "layout_config_section_config_id",
            None,
        ),
        layout_section_id=getattr(raw_scope, "layout_section_id", None),
        section_focus_scope_id=getattr(raw_scope, "section_focus_scope_id", None),
        focus_scope_id=getattr(raw_scope, "focus_scope_id", None),
        focus_id=getattr(raw_scope, "focus_id", None),
        observable_id=getattr(raw_scope, "observable_id", None),
        projection_view_key=getattr(raw_scope, "projection_view_key", None),
        section_graph_binding_key=getattr(
            raw_scope,
            "section_graph_binding_key",
            None,
        ),
        projection_experience_graph_identity_id=getattr(
            raw_scope,
            "projection_experience_graph_identity_id",
            None,
        ),
        object_projection_graph_identity_id=getattr(
            raw_scope,
            "object_projection_graph_identity_id",
            None,
        ),
        object_instance_graph_branch_id=getattr(
            raw_scope,
            "object_instance_graph_branch_id",
            None,
        ),
        topology_seed_key=getattr(raw_scope, "topology_seed_key", None),
        source_kind=getattr(raw_scope, "source_kind", "interface_runtime_focus"),
        evidence=cast(JsonObject, dict(getattr(raw_scope, "evidence", {}) or {})),
    )


def _session_view_frame_lens(
    lens: object | None,
) -> ExperienceSessionViewFrameLens | None:
    if lens is None:
        return None
    return ExperienceSessionViewFrameLens(
        status=str(getattr(lens, "status")),
        view_ref=getattr(lens, "view_ref", None),
        projection_view_key=getattr(lens, "projection_view_key", None),
        section_graph_binding_key=getattr(lens, "section_graph_binding_key", None),
        section_key=getattr(lens, "section_key", None),
        window_key=getattr(lens, "window_key", None),
        layout_key=getattr(lens, "layout_key", None),
        layout_config_id=getattr(lens, "layout_config_id", None),
        layout_config_section_config_id=getattr(
            lens,
            "layout_config_section_config_id",
            None,
        ),
        layout_section_id=getattr(lens, "layout_section_id", None),
        section_focus_scope_id=getattr(lens, "section_focus_scope_id", None),
        focus_scope_id=getattr(lens, "focus_scope_id", None),
        focus_id=getattr(lens, "focus_id", None),
        observable_id=getattr(lens, "observable_id", None),
        blockers=list(getattr(lens, "blockers", [])),
        evidence=cast(JsonObject, dict(getattr(lens, "evidence", {}) or {})),
    )


__all__ = [
    "build_aware_experience_service_protocol_handler",
]
