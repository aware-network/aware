# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import (
    ENVIRONMENT__ACTOR_ADMISSION__ADMIT_ACTOR_ENDPOINT_REF,
    ENVIRONMENT__CAPABILITIES__FETCH_CAPABILITIES_ENDPOINT_REF,
    ENVIRONMENT__COMMITTED_PROJECTION_DTO__MATERIALIZE_COMMITTED_PROJECTION_DTO_ENDPOINT_REF,
    ENVIRONMENT__DESCRIBE_CONFIG__DESCRIBE_ENVIRONMENT_CONFIG_ENDPOINT_REF,
    ENVIRONMENT__DESCRIBE__DESCRIBE_ENVIRONMENT_ENDPOINT_REF,
    ENVIRONMENT__FUNCTION_CALL__INVOKE_FUNCTION_ENDPOINT_REF,
    ENVIRONMENT__LANE_HEAD__GET_LANE_HEAD_ENDPOINT_REF,
    ENVIRONMENT__NAVIGATION__CREATE_NAVIGATION_CONTEXT_ENDPOINT_REF,
    ENVIRONMENT__NAVIGATION__DESCRIBE_NAVIGATION_CONTEXT_ENDPOINT_REF,
    ENVIRONMENT__NAVIGATION__LIST_NAVIGATION_CONTEXTS_ENDPOINT_REF,
    ENVIRONMENT__NAVIGATION__SELECT_NAVIGATION_TARGET_ENDPOINT_REF,
    ENVIRONMENT__OBJECT_INSTANCE_GRAPH_COMMIT__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF,
    ENVIRONMENT__ONTOLOGY__ATTACH_ENVIRONMENT_ONTOLOGY_ENDPOINT_REF,
    ENVIRONMENT__ONTOLOGY__ENSURE_ENVIRONMENT_ONTOLOGY_RUNTIME_ENDPOINT_REF,
    ENVIRONMENT__ONTOLOGY__LIST_ENVIRONMENT_ONTOLOGIES_ENDPOINT_REF,
    ENVIRONMENT__PROFILE__PROVISION_ENVIRONMENT_PROFILE_ENDPOINT_REF,
    ENVIRONMENT__PROFILE__UPSERT_ENVIRONMENT_PROFILE_ENDPOINT_REF,
    ENVIRONMENT__READY__ENSURE_READY_ENDPOINT_REF,
    ENVIRONMENT__RUNTIME_REF__RESOLVE_RUNTIME_REFS_ENDPOINT_REF,
    ENVIRONMENT__SERVICE_ROUTES__CONFIGURE_SERVICE_API_DEPENDENCY_ROUTES_ENDPOINT_REF,
    ENVIRONMENT__SESSION__DESCRIBE_SESSION_ENDPOINT_REF,
    ENVIRONMENT__SESSION__JOIN_SESSION_ENDPOINT_REF,
    ENVIRONMENT__SESSION__MOUNT_ATTENTION_SESSION_ENDPOINT_REF,
    ENVIRONMENT__SESSION__RESOLVE_ATTENTION_ENDPOINT_REF,
    ENVIRONMENT__SESSION__START_SESSION_ENDPOINT_REF,
    ENVIRONMENT__STATUS__DESCRIBE_ENVIRONMENT_STATUS_ENDPOINT_REF,
    ENVIRONMENT__TOPOLOGY__DESCRIBE_ENVIRONMENT_TOPOLOGY_ENDPOINT_REF,
)
from aware_environment_service_dto.environment.environment import (
    AdmitEnvironmentActorRequest,
    AdmitEnvironmentActorResponse,
    AttachEnvironmentOntologyRequest,
    AttachEnvironmentOntologyResponse,
    ConfigureServiceApiDependencyRoutesRequest,
    ConfigureServiceApiDependencyRoutesResponse,
    CreateEnvironmentNavigationContextRequest,
    CreateEnvironmentNavigationContextResponse,
    DescribeEnvironmentConfigRequest,
    DescribeEnvironmentConfigResponse,
    DescribeEnvironmentNavigationContextRequest,
    DescribeEnvironmentNavigationContextResponse,
    DescribeEnvironmentRequest,
    DescribeEnvironmentResponse,
    DescribeEnvironmentSessionRequest,
    DescribeEnvironmentSessionResponse,
    DescribeEnvironmentStatusRequest,
    DescribeEnvironmentStatusResponse,
    DescribeEnvironmentTopologyRequest,
    DescribeEnvironmentTopologyResponse,
    EnsureEnvironmentOntologyRuntimeRequest,
    EnsureEnvironmentOntologyRuntimeResponse,
    EnsureReadyRequest,
    EnsureReadyResponse,
    FetchCapabilitiesRequest,
    FetchCapabilitiesResponse,
    GetLaneHeadRequest,
    GetLaneHeadResponse,
    GetObjectInstanceGraphCommitRequest,
    GetObjectInstanceGraphCommitResponse,
    InvokeFunctionRequest,
    InvokeFunctionResponse,
    JoinEnvironmentSessionRequest,
    JoinEnvironmentSessionResponse,
    ListEnvironmentNavigationContextsRequest,
    ListEnvironmentNavigationContextsResponse,
    ListEnvironmentOntologiesRequest,
    ListEnvironmentOntologiesResponse,
    MaterializeCommittedProjectionDtoRequest,
    MaterializeCommittedProjectionDtoResponse,
    MountEnvironmentSessionAttentionRequest,
    MountEnvironmentSessionAttentionResponse,
    ProvisionEnvironmentProfileRequest,
    ProvisionEnvironmentProfileResponse,
    ResolveEnvironmentSessionAttentionRequest,
    ResolveEnvironmentSessionAttentionResponse,
    ResolveRuntimeRefsRequest,
    ResolveRuntimeRefsResponse,
    SelectEnvironmentNavigationTargetRequest,
    SelectEnvironmentNavigationTargetResponse,
    StartEnvironmentSessionRequest,
    StartEnvironmentSessionResponse,
    UpsertEnvironmentProfileRequest,
    UpsertEnvironmentProfileResponse,
)


class EnvironmentActorAdmissionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def admit_actor(self, request: AdmitEnvironmentActorRequest) -> AdmitEnvironmentActorResponse:
        """Admit an actor to an EnvironmentProfile through committed ActorConfig eligibility and Identity role assignment."""
        return cast(
            AdmitEnvironmentActorResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__ACTOR_ADMISSION__ADMIT_ACTOR_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EnvironmentCapabilitiesCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def fetch_capabilities(self, request: FetchCapabilitiesRequest) -> FetchCapabilitiesResponse:
        """Read Environment runtime capability advertisement through the canonical Environment API boundary."""
        return cast(
            FetchCapabilitiesResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__CAPABILITIES__FETCH_CAPABILITIES_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EnvironmentCommittedProjectionDtoCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def materialize_committed_projection_dto(
        self, request: MaterializeCommittedProjectionDtoRequest
    ) -> MaterializeCommittedProjectionDtoResponse:
        """Materialize a committed projection root as a typed ontology DTO snapshot through an explicit commit locator."""
        return cast(
            MaterializeCommittedProjectionDtoResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__COMMITTED_PROJECTION_DTO__MATERIALIZE_COMMITTED_PROJECTION_DTO_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EnvironmentDescribeCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def describe_environment(self, request: DescribeEnvironmentRequest) -> DescribeEnvironmentResponse:
        """Describe one provisioned Environment instance and its current boot/lane pointers."""
        return cast(
            DescribeEnvironmentResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__DESCRIBE__DESCRIBE_ENVIRONMENT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EnvironmentDescribeConfigCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def describe_environment_config(
        self, request: DescribeEnvironmentConfigRequest
    ) -> DescribeEnvironmentConfigResponse:
        """Describe the hosted EnvironmentConfig through the canonical Environment API boundary."""
        return cast(
            DescribeEnvironmentConfigResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__DESCRIBE_CONFIG__DESCRIBE_ENVIRONMENT_CONFIG_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EnvironmentFunctionCallCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def invoke_function(self, request: InvokeFunctionRequest) -> InvokeFunctionResponse:
        """Invoke one graph function through the canonical commit-backed Environment runtime boundary."""
        return cast(
            InvokeFunctionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__FUNCTION_CALL__INVOKE_FUNCTION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EnvironmentLaneHeadCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def get_lane_head(self, request: GetLaneHeadRequest) -> GetLaneHeadResponse:
        """Read the current head commit for one explicit Environment lane key."""
        return cast(
            GetLaneHeadResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__LANE_HEAD__GET_LANE_HEAD_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EnvironmentNavigationCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def create_navigation_context(
        self, request: CreateEnvironmentNavigationContextRequest
    ) -> CreateEnvironmentNavigationContextResponse:
        """Create an EnvironmentSession-owned navigation context after accepted session join."""
        return cast(
            CreateEnvironmentNavigationContextResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__NAVIGATION__CREATE_NAVIGATION_CONTEXT_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def describe_navigation_context(
        self, request: DescribeEnvironmentNavigationContextRequest
    ) -> DescribeEnvironmentNavigationContextResponse:
        """Describe one Environment navigation context without mutating Attention or Experience state."""
        return cast(
            DescribeEnvironmentNavigationContextResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__NAVIGATION__DESCRIBE_NAVIGATION_CONTEXT_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def list_navigation_contexts(
        self, request: ListEnvironmentNavigationContextsRequest
    ) -> ListEnvironmentNavigationContextsResponse:
        """List Environment navigation contexts owned by one EnvironmentSession."""
        return cast(
            ListEnvironmentNavigationContextsResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__NAVIGATION__LIST_NAVIGATION_CONTEXTS_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def select_navigation_target(
        self, request: SelectEnvironmentNavigationTargetRequest
    ) -> SelectEnvironmentNavigationTargetResponse:
        """Select the Process/Thread target for one Environment navigation context."""
        return cast(
            SelectEnvironmentNavigationTargetResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__NAVIGATION__SELECT_NAVIGATION_TARGET_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EnvironmentObjectInstanceGraphCommitCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def get_object_instance_graph_commit(
        self, request: GetObjectInstanceGraphCommitRequest
    ) -> GetObjectInstanceGraphCommitResponse:
        """Read one ObjectInstanceGraphCommit by id through the Environment service boundary."""
        return cast(
            GetObjectInstanceGraphCommitResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__OBJECT_INSTANCE_GRAPH_COMMIT__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EnvironmentOntologyCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def attach_environment_ontology(
        self, request: AttachEnvironmentOntologyRequest
    ) -> AttachEnvironmentOntologyResponse:
        """Attach one Ontology authority to a stable Environment through the canonical Environment API boundary."""
        return cast(
            AttachEnvironmentOntologyResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__ONTOLOGY__ATTACH_ENVIRONMENT_ONTOLOGY_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def ensure_environment_ontology_runtime(
        self, request: EnsureEnvironmentOntologyRuntimeRequest
    ) -> EnsureEnvironmentOntologyRuntimeResponse:
        """Resolve and register one Ontology-owned runtime artifact set for a running Environment."""
        return cast(
            EnsureEnvironmentOntologyRuntimeResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__ONTOLOGY__ENSURE_ENVIRONMENT_ONTOLOGY_RUNTIME_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def list_environment_ontologies(
        self, request: ListEnvironmentOntologiesRequest
    ) -> ListEnvironmentOntologiesResponse:
        """List Environment-owned Ontology membership pointers without expanding Ontology-owned OIGI inventory."""
        return cast(
            ListEnvironmentOntologiesResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__ONTOLOGY__LIST_ENVIRONMENT_ONTOLOGIES_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EnvironmentProfileCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def provision_environment_profile(
        self, request: ProvisionEnvironmentProfileRequest
    ) -> ProvisionEnvironmentProfileResponse:
        """Provision concrete Environment Process/Thread topology from an installed EnvironmentProfile seed."""
        return cast(
            ProvisionEnvironmentProfileResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__PROFILE__PROVISION_ENVIRONMENT_PROFILE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def upsert_environment_profile(
        self, request: UpsertEnvironmentProfileRequest
    ) -> UpsertEnvironmentProfileResponse:
        """Install or update Environment-owned profile topology through the Environment API boundary."""
        return cast(
            UpsertEnvironmentProfileResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__PROFILE__UPSERT_ENVIRONMENT_PROFILE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EnvironmentReadyCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def ensure_ready(self, request: EnsureReadyRequest) -> EnsureReadyResponse:
        """Ensure the Environment runtime is ready to execute commit-backed graph operations."""
        return cast(
            EnsureReadyResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__READY__ENSURE_READY_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EnvironmentRuntimeRefCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_runtime_refs(self, request: ResolveRuntimeRefsRequest) -> ResolveRuntimeRefsResponse:
        """Resolve hosted runtime OCG/function/class references for remote graph invocation."""
        return cast(
            ResolveRuntimeRefsResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__RUNTIME_REF__RESOLVE_RUNTIME_REFS_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EnvironmentServiceRoutesCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def configure_service_api_dependency_routes(
        self, request: ConfigureServiceApiDependencyRoutesRequest
    ) -> ConfigureServiceApiDependencyRoutesResponse:
        """Configure Environment-hosted service API dependency routes through the canonical Environment API boundary."""
        return cast(
            ConfigureServiceApiDependencyRoutesResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__SERVICE_ROUTES__CONFIGURE_SERVICE_API_DEPENDENCY_ROUTES_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EnvironmentSessionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def describe_session(self, request: DescribeEnvironmentSessionRequest) -> DescribeEnvironmentSessionResponse:
        """Describe a shared EnvironmentSession without resolving navigation or Attention."""
        return cast(
            DescribeEnvironmentSessionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__SESSION__DESCRIBE_SESSION_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def join_session(self, request: JoinEnvironmentSessionRequest) -> JoinEnvironmentSessionResponse:
        """Join a shared EnvironmentSession after accepted Environment admission."""
        return cast(
            JoinEnvironmentSessionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__SESSION__JOIN_SESSION_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def mount_attention_session(
        self, request: MountEnvironmentSessionAttentionRequest
    ) -> MountEnvironmentSessionAttentionResponse:
        """Commit one EnvironmentSession-owned portal to an existing AttentionSession authority."""
        return cast(
            MountEnvironmentSessionAttentionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__SESSION__MOUNT_ATTENTION_SESSION_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def resolve_attention(
        self, request: ResolveEnvironmentSessionAttentionRequest
    ) -> ResolveEnvironmentSessionAttentionResponse:
        """Resolve Environment session Thread/Layout pins against Attention session and transition validation."""
        return cast(
            ResolveEnvironmentSessionAttentionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__SESSION__RESOLVE_ATTENTION_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def start_session(self, request: StartEnvironmentSessionRequest) -> StartEnvironmentSessionResponse:
        """Start a shared EnvironmentSession after accepted Environment admission."""
        return cast(
            StartEnvironmentSessionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__SESSION__START_SESSION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EnvironmentStatusCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def describe_environment_status(
        self, request: DescribeEnvironmentStatusRequest
    ) -> DescribeEnvironmentStatusResponse:
        """Read the canonical Environment status envelope with explicit authority blocks."""
        return cast(
            DescribeEnvironmentStatusResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__STATUS__DESCRIBE_ENVIRONMENT_STATUS_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EnvironmentTopologyCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def describe_environment_topology(
        self, request: DescribeEnvironmentTopologyRequest
    ) -> DescribeEnvironmentTopologyResponse:
        """Describe the process/thread topology and attached OIG lanes for an Environment."""
        return cast(
            DescribeEnvironmentTopologyResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ENVIRONMENT__TOPOLOGY__DESCRIBE_ENVIRONMENT_TOPOLOGY_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EnvironmentApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.actor_admission = EnvironmentActorAdmissionCapabilityClient(client)
        self.capabilities = EnvironmentCapabilitiesCapabilityClient(client)
        self.committed_projection_dto = EnvironmentCommittedProjectionDtoCapabilityClient(client)
        self.describe = EnvironmentDescribeCapabilityClient(client)
        self.describe_config = EnvironmentDescribeConfigCapabilityClient(client)
        self.function_call = EnvironmentFunctionCallCapabilityClient(client)
        self.lane_head = EnvironmentLaneHeadCapabilityClient(client)
        self.navigation = EnvironmentNavigationCapabilityClient(client)
        self.object_instance_graph_commit = EnvironmentObjectInstanceGraphCommitCapabilityClient(client)
        self.ontology = EnvironmentOntologyCapabilityClient(client)
        self.profile = EnvironmentProfileCapabilityClient(client)
        self.ready = EnvironmentReadyCapabilityClient(client)
        self.runtime_ref = EnvironmentRuntimeRefCapabilityClient(client)
        self.service_routes = EnvironmentServiceRoutesCapabilityClient(client)
        self.session = EnvironmentSessionCapabilityClient(client)
        self.status = EnvironmentStatusCapabilityClient(client)
        self.topology = EnvironmentTopologyCapabilityClient(client)


class AwareEnvironmentServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.environment = EnvironmentApiClient(client)


__all__ = [
    "AwareEnvironmentServiceApiClient",
    "EnvironmentApiClient",
    "EnvironmentActorAdmissionCapabilityClient",
    "EnvironmentCapabilitiesCapabilityClient",
    "EnvironmentCommittedProjectionDtoCapabilityClient",
    "EnvironmentDescribeCapabilityClient",
    "EnvironmentDescribeConfigCapabilityClient",
    "EnvironmentFunctionCallCapabilityClient",
    "EnvironmentLaneHeadCapabilityClient",
    "EnvironmentNavigationCapabilityClient",
    "EnvironmentObjectInstanceGraphCommitCapabilityClient",
    "EnvironmentOntologyCapabilityClient",
    "EnvironmentProfileCapabilityClient",
    "EnvironmentReadyCapabilityClient",
    "EnvironmentRuntimeRefCapabilityClient",
    "EnvironmentServiceRoutesCapabilityClient",
    "EnvironmentSessionCapabilityClient",
    "EnvironmentStatusCapabilityClient",
    "EnvironmentTopologyCapabilityClient",
]
