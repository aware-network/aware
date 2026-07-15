from __future__ import annotations

# Standard
from enum import Enum
from functools import lru_cache
from typing import (
    ClassVar,
    Literal,
)
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
    SerializeAsAny,
    field_validator,
    model_validator,
)

# Attention Service Dto
from aware_attention_service_dto.attention.session.models import (
    AttentionFocusTransitionPin,
    AttentionSessionPin,
    AttentionTransitionValidationResult,
)

# Identity Service Dto
from aware_identity_service_dto.session.session import (
    SessionMemberActorRoleSummary,
    SessionMemberSummary,
    SessionSummary,
)

# Types
from aware_types import (
    JsonArray,
    JsonObject,
    JsonValue,
)


class EnvironmentOperationContext(BaseModel):
    """
    Canonical environment operation DTOs (transport-layer, graph/ORM agnostic).
    SSOT: `environment-service-dto` generated from `apis/environment/dto`.
    `aware_comms` re-exports these DTOs for transport/service import stability,
    but schema ownership remains here so all language targets compile from one rail.
    """

    # Attributes
    actor_id: UUID | None = Field(default=None)
    environment_id: UUID
    process_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)


class EnvironmentOperationNotificationContext(BaseModel):
    """
    Context for environment notifications (fan-out).
    Notifications may be emitted by commit stores and transport layers that do not
    have a full EnvironmentOperationContext. The lane key is still canonical.
    """

    # Attributes
    actor_id: UUID | None = Field(default=None)
    environment_id: UUID | None = Field(default=None)
    process_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    branch_id: UUID
    projection_hash: str


class EnvironmentOperation(BaseModel):
    """EnvironmentOperation is either a request or a response."""

    # Attributes
    request: SerializeAsAny[EnvironmentOperationRequest] | None = Field(default=None)
    response: SerializeAsAny[EnvironmentOperationResponse] | None = Field(default=None)
    notification: SerializeAsAny[EnvironmentOperationNotification] | None = Field(default=None)

    @field_validator("request", mode="before")
    @classmethod
    def _parse_request(cls, v):
        if v is None:
            return None
        return EnvironmentOperationRequest.parse(v)

    @field_validator("response", mode="before")
    @classmethod
    def _parse_response(cls, v):
        if v is None:
            return None
        return EnvironmentOperationResponse.parse(v)

    @field_validator("notification", mode="before")
    @classmethod
    def _parse_notification(cls, v):
        if v is None:
            return None
        return EnvironmentOperationNotification.parse(v)

    @model_validator(mode="after")
    def _validate_oneof_0(self):
        if (
            sum(
                v is not None
                for v in (
                    self.request,
                    self.response,
                    self.notification,
                )
            )
            != 1
        ):
            raise ValueError("Exactly one of request, response, notification must be set")
        return self


class EnvironmentOperationRequest(EnvironmentOperationContext):
    """Request union base (operation + context)."""

    # Discriminator Key
    operation: str

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "fetch_capabilities": "aware_environment_service_dto.environment.environment.FetchCapabilitiesRequest",
        "describe_environment_config": "aware_environment_service_dto.environment.environment.DescribeEnvironmentConfigRequest",
        "describe_environment": "aware_environment_service_dto.environment.environment.DescribeEnvironmentRequest",
        "describe_environment_topology": "aware_environment_service_dto.environment.environment.DescribeEnvironmentTopologyRequest",
        "describe_environment_status": "aware_environment_service_dto.environment.environment.DescribeEnvironmentStatusRequest",
        "ensure_ready": "aware_environment_service_dto.environment.environment.EnsureReadyRequest",
        "get_lane_head": "aware_environment_service_dto.environment.environment.GetLaneHeadRequest",
        "get_object_instance_graph_commit": "aware_environment_service_dto.environment.environment.GetObjectInstanceGraphCommitRequest",
        "materialize_committed_projection_dto": "aware_environment_service_dto.environment.environment.MaterializeCommittedProjectionDtoRequest",
        "resolve_runtime_refs": "aware_environment_service_dto.environment.environment.ResolveRuntimeRefsRequest",
        "configure_service_api_dependency_routes": "aware_environment_service_dto.environment.environment.ConfigureServiceApiDependencyRoutesRequest",
        "attach_environment_ontology": "aware_environment_service_dto.environment.environment.AttachEnvironmentOntologyRequest",
        "ensure_environment_ontology_runtime": "aware_environment_service_dto.environment.environment.EnsureEnvironmentOntologyRuntimeRequest",
        "list_environment_ontologies": "aware_environment_service_dto.environment.environment.ListEnvironmentOntologiesRequest",
        "resolve_environment_session_attention": "aware_environment_service_dto.environment.environment.ResolveEnvironmentSessionAttentionRequest",
        "mount_environment_session_attention": "aware_environment_service_dto.environment.environment.MountEnvironmentSessionAttentionRequest",
        "create_environment_navigation_context": "aware_environment_service_dto.environment.environment.CreateEnvironmentNavigationContextRequest",
        "select_environment_navigation_target": "aware_environment_service_dto.environment.environment.SelectEnvironmentNavigationTargetRequest",
        "describe_environment_navigation_context": "aware_environment_service_dto.environment.environment.DescribeEnvironmentNavigationContextRequest",
        "list_environment_navigation_contexts": "aware_environment_service_dto.environment.environment.ListEnvironmentNavigationContextsRequest",
        "invoke_function": "aware_environment_service_dto.environment.environment.InvokeFunctionRequest",
        "service_operation": "aware_environment_service_dto.environment.environment_service_operation.EnvironmentServiceOperationRequest",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownEnvironmentOperationRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownEnvironmentOperationRequest(EnvironmentOperationRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class EnvironmentOperationResponse(EnvironmentOperationContext):
    """Response union base (operation + context)."""

    # Discriminator Key
    operation: str

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "fetch_capabilities": "aware_environment_service_dto.environment.environment.FetchCapabilitiesResponse",
        "describe_environment_config": "aware_environment_service_dto.environment.environment.DescribeEnvironmentConfigResponse",
        "describe_environment": "aware_environment_service_dto.environment.environment.DescribeEnvironmentResponse",
        "describe_environment_topology": "aware_environment_service_dto.environment.environment.DescribeEnvironmentTopologyResponse",
        "describe_environment_status": "aware_environment_service_dto.environment.environment.DescribeEnvironmentStatusResponse",
        "ensure_ready": "aware_environment_service_dto.environment.environment.EnsureReadyResponse",
        "get_lane_head": "aware_environment_service_dto.environment.environment.GetLaneHeadResponse",
        "get_object_instance_graph_commit": "aware_environment_service_dto.environment.environment.GetObjectInstanceGraphCommitResponse",
        "materialize_committed_projection_dto": "aware_environment_service_dto.environment.environment.MaterializeCommittedProjectionDtoResponse",
        "resolve_runtime_refs": "aware_environment_service_dto.environment.environment.ResolveRuntimeRefsResponse",
        "configure_service_api_dependency_routes": "aware_environment_service_dto.environment.environment.ConfigureServiceApiDependencyRoutesResponse",
        "attach_environment_ontology": "aware_environment_service_dto.environment.environment.AttachEnvironmentOntologyResponse",
        "ensure_environment_ontology_runtime": "aware_environment_service_dto.environment.environment.EnsureEnvironmentOntologyRuntimeResponse",
        "list_environment_ontologies": "aware_environment_service_dto.environment.environment.ListEnvironmentOntologiesResponse",
        "resolve_environment_session_attention": "aware_environment_service_dto.environment.environment.ResolveEnvironmentSessionAttentionResponse",
        "mount_environment_session_attention": "aware_environment_service_dto.environment.environment.MountEnvironmentSessionAttentionResponse",
        "create_environment_navigation_context": "aware_environment_service_dto.environment.environment.CreateEnvironmentNavigationContextResponse",
        "select_environment_navigation_target": "aware_environment_service_dto.environment.environment.SelectEnvironmentNavigationTargetResponse",
        "describe_environment_navigation_context": "aware_environment_service_dto.environment.environment.DescribeEnvironmentNavigationContextResponse",
        "list_environment_navigation_contexts": "aware_environment_service_dto.environment.environment.ListEnvironmentNavigationContextsResponse",
        "invoke_function": "aware_environment_service_dto.environment.environment.InvokeFunctionResponse",
        "service_operation": "aware_environment_service_dto.environment.environment_service_operation.EnvironmentServiceOperationResponse",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownEnvironmentOperationResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownEnvironmentOperationResponse(EnvironmentOperationResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class EnvironmentOperationNotification(EnvironmentOperationNotificationContext):
    """
    Notification union base (operation + context).
    Used for commit receipts / lane head moves so clients can sync lanes without
    inferring from unrelated transports (e.g., inference streams).
    """

    # Discriminator Key
    operation: str

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "lane_commit_receipt": "aware_environment_service_dto.environment.environment.LaneCommitReceiptNotification",
        "lane_event_receipt": "aware_environment_service_dto.environment.environment.LaneEventReceiptNotification",
        "lane_action_execution_receipt": "aware_environment_service_dto.environment.environment.LaneActionExecutionReceiptNotification",
        "lane_action_feedback_receipt": "aware_environment_service_dto.environment.environment.LaneActionFeedbackReceiptNotification",
        "lane_action_terminal_receipt": "aware_environment_service_dto.environment.environment.LaneActionTerminalReceiptNotification",
        "lane_turn_stream_receipt": "aware_environment_service_dto.environment.environment.LaneTurnStreamReceiptNotification",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownEnvironmentOperationNotification.model_validate(v)
        return cls.model_validate(v)


class UnknownEnvironmentOperationNotification(EnvironmentOperationNotification):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class InvokeFunctionCallTarget(Enum):
    instance = "instance"
    opg_constructor = "opg_constructor"


class FetchCapabilitiesRequest(EnvironmentOperationRequest):
    # Discriminator Tag
    operation: Literal["fetch_capabilities"] = "fetch_capabilities"


class DescribeEnvironmentConfigRequest(EnvironmentOperationRequest):
    """
    Describe the hosted EnvironmentConfig (template/map) for this ENVIRONMENT service.
    This does NOT describe a provisioned environment instance (territory). Use
    `DescribeEnvironmentRequest` for the territory instance.
    """

    # Discriminator Tag
    operation: Literal["describe_environment_config"] = "describe_environment_config"


class DescribeEnvironmentRequest(EnvironmentOperationRequest):
    """Describe a provisioned Environment instance (territory) and its boot/lane pointers."""

    # Discriminator Tag
    operation: Literal["describe_environment"] = "describe_environment"


class DescribeEnvironmentTopologyRequest(EnvironmentOperationRequest):
    """
    Describe the provisioned environment OS topology (Process/Thread) and the
    attached domain lanes per thread (ThreadObjectInstanceGraphBranch).
    Purpose:
    - Deterministic lane discovery for agents/CLIs (no guessing from UI titles).
    - Interface-parity bootstrap for (process_key, thread_key) -> lane list.
    """

    # Discriminator Tag
    operation: Literal["describe_environment_topology"] = "describe_environment_topology"

    # Attributes
    process_key: str | None = Field(
        default=None, description="Optional filter by canonical Process key (stable-id input)."
    )
    thread_key: str | None = Field(
        default=None, description="Optional filter by canonical Thread key (stable-id input)."
    )


class DescribeEnvironmentStatusRequest(EnvironmentOperationRequest):
    """
    Describe canonical environment status envelope for local/remote parity.
    Contract:
    - One payload shape for both local and remote providers.
    - Blocks must declare authority kind explicitly.
    - `strict_commit_truth=true` refuses when commit truth cannot be resolved.
    """

    # Discriminator Tag
    operation: Literal["describe_environment_status"] = "describe_environment_status"

    # Attributes
    include_blocks: list[str] = Field(
        default_factory=list,
        description="Optional block filter (`environment_interface`, `local_workspace`, `issue`, `runtime`, `commit_truth`).",
    )
    strict_commit_truth: bool = Field(
        default=False, description="When true, missing commit-truth authority is a refusal."
    )


class EnsureReadyRequest(EnvironmentOperationRequest):
    # Discriminator Tag
    operation: Literal["ensure_ready"] = "ensure_ready"


class GetLaneHeadRequest(EnvironmentOperationRequest):
    # Discriminator Tag
    operation: Literal["get_lane_head"] = "get_lane_head"


class GetObjectInstanceGraphCommitRequest(EnvironmentOperationRequest):
    # Discriminator Tag
    operation: Literal["get_object_instance_graph_commit"] = "get_object_instance_graph_commit"

    # Attributes
    commit_id: UUID


class MaterializeCommittedProjectionDtoRequest(EnvironmentOperationRequest):
    """
    Materialize one committed projection root as an ontology DTO snapshot.
    V0 verifier contract:
    - Caller must provide an explicit `(branch_id, projection_hash, commit_id)`.
    - Runtime must not resolve DTO classes from caller paths or repo-local imports.
    - Runtime may return `dto_runtime_artifact_unavailable` until the deploy
    contract declares a pinned DTO artifact/package closure for the requested
    DTO target.
    """

    # Discriminator Tag
    operation: Literal["materialize_committed_projection_dto"] = "materialize_committed_projection_dto"

    # Attributes
    commit_id: UUID
    expected_graph_hash_post: str | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    use_commit_root: bool = Field(default=True)
    dto_class_ref: str | None = Field(default=None)
    class_config_id: UUID | None = Field(default=None)
    dto_package_name: str | None = Field(default=None)
    dto_import_root: str | None = Field(default=None)
    view_ref: str | None = Field(default=None)
    projection_view_key: str | None = Field(default=None)
    include_relationships: bool = Field(default=True)
    max_depth: int | None = Field(default=None)


class ResolveRuntimeFunctionTargetQuery(BaseModel):
    # Attributes
    query_key: str | None = Field(default=None)
    function_ref: str
    call_target: InvokeFunctionCallTarget = Field(default=InvokeFunctionCallTarget.instance)
    projection_hash_hint: str | None = Field(default=None)


class ResolveRuntimeClassRefQuery(BaseModel):
    # Attributes
    query_key: str | None = Field(default=None)
    class_ref: str


class ResolveRuntimeRefsRequest(EnvironmentOperationRequest):
    # Discriminator Tag
    operation: Literal["resolve_runtime_refs"] = "resolve_runtime_refs"

    # Attributes
    function_targets: list[ResolveRuntimeFunctionTargetQuery] = Field(default_factory=list)
    class_refs: list[ResolveRuntimeClassRefQuery] = Field(default_factory=list)


class ConfigureServiceApiDependencyRoutesRequest(EnvironmentOperationRequest):
    """
    Install live service-to-service API dependency routes into this Environment.
    Node sends this after it binds selected ServicePackage required/provided
    ApiPackage truth to concrete provider ServiceHost endpoints. The payload
    uses the shared route descriptor JSON contract; Environment must not infer
    providers from source manifests.
    """

    # Discriminator Tag
    operation: Literal["configure_service_api_dependency_routes"] = "configure_service_api_dependency_routes"

    # Attributes
    routes: JsonArray = Field(default_factory=JsonArray)


class AdmitEnvironmentActorRequest(EnvironmentOperationRequest):
    """
    Admit an actor to a concrete EnvironmentProfile using Identity-owned ActorConfig
    eligibility.
    Contract:
    - Environment owns the admission scope and EnvironmentProfile -> ActorConfig
    eligibility check.
    - Identity owns concrete RoleAssignment/ActorRole truth.
    - This operation grants no Experience access and does not infer Experience
    participation.
    """

    # Attributes
    operation: str = Field(default="admit_actor")
    request_id: UUID | None = Field(default=None)
    environment_profile_id: UUID
    actor_config_id: UUID
    class_instance_identity_id: UUID
    object_instance_graph_branch_key: str = Field(default="all")
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    requested_role_config_ids: list[UUID] = Field(default_factory=list)
    requested_role_config_names: list[str] = Field(default_factory=list)
    reason: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class InvokeFunctionRequest(EnvironmentOperationRequest):
    # Discriminator Tag
    operation: Literal["invoke_function"] = "invoke_function"

    # Attributes
    call_target: InvokeFunctionCallTarget = Field(
        default=InvokeFunctionCallTarget.instance,
        description="Lane addressing (canonical):\n- `branch_id` (in EnvironmentOperationContext) is REQUIRED for `call_target=instance`.\n- `branch_id` MAY be omitted for `call_target=opg_constructor` (runtime allocates and returns it).\nThe lane key is `(branch_id, projection_hash)`; runtime must not guess `branch_id` from env/thread.",
    )
    object_id: UUID | None = Field(default=None)
    object_projection_graph_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID | None = Field(
        default=None,
        description="Resolved ObjectProjectionGraphIdentity for this call target when known.\nEnvironment does not need this to invoke Meta, but consumers such as\nAttention need it to bind committed focus to the same projection identity\nwithout subscribing to Meta directly.",
    )
    function_id: UUID
    args: JsonArray = Field(default_factory=JsonArray)
    kwargs: JsonObject = Field(default_factory=JsonObject)
    expected_graph_hash_pre: str | None = Field(default=None)
    expected_head_commit_id: UUID | None = Field(default=None)
    commit: bool = Field(default=True)
    publish: bool = Field(default=False)


class CapabilityArgument(BaseModel):
    # Attributes
    id: UUID
    name: str
    direction: str | None = Field(default=None)
    type: str | None = Field(default=None)
    required: bool = Field(default=True)
    default: JsonValue | None = Field(default=None)
    enum: JsonArray | None = Field(default=None)
    description: str | None = Field(default=None)


class CapabilityFunction(BaseModel):
    # Attributes
    id: UUID
    name: str
    summary: str | None = Field(default=None)
    role_id: UUID | None = Field(default=None)
    is_constructor: bool = Field(default=False)
    inputs: list[CapabilityArgument] = Field(default_factory=list)
    outputs: list[CapabilityArgument] = Field(default_factory=list)
    arguments: list[CapabilityArgument] = Field(default_factory=list)


class CapabilityRole(BaseModel):
    # Attributes
    id: UUID
    name: str
    description: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)
    functions: list[CapabilityFunction] = Field(default_factory=list)


class CapabilityObject(BaseModel):
    # Attributes
    id: UUID
    name: str
    description: str | None = Field(default=None)
    functions: list[CapabilityFunction] = Field(default_factory=list)


class FetchCapabilitiesResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["fetch_capabilities"] = "fetch_capabilities"

    # Attributes
    roles: list[CapabilityRole] = Field(default_factory=list)
    functions: list[CapabilityFunction] = Field(default_factory=list)
    objects: list[CapabilityObject] = Field(default_factory=list)


class ResolvedRuntimeFunctionTarget(BaseModel):
    # Attributes
    query_key: str | None = Field(default=None)
    status: str
    error: str | None = Field(default=None)
    function_ref: str
    call_target: InvokeFunctionCallTarget = Field(default=InvokeFunctionCallTarget.instance)
    class_config_id: UUID | None = Field(default=None)
    class_name: str | None = Field(default=None)
    class_fqn: str | None = Field(default=None)
    class_config_function_config_id: UUID | None = Field(default=None)
    function_id: UUID | None = Field(default=None)
    function_name: str | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    object_projection_graph_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID | None = Field(default=None)
    candidate_projection_hashes: list[str] = Field(default_factory=list)
    evidence: JsonObject = Field(default_factory=JsonObject)


class ResolvedRuntimeClassRef(BaseModel):
    # Attributes
    query_key: str | None = Field(default=None)
    status: str
    error: str | None = Field(default=None)
    class_ref: str
    class_config_id: UUID | None = Field(default=None)
    class_name: str | None = Field(default=None)
    class_fqn: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class ResolveRuntimeRefsResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["resolve_runtime_refs"] = "resolve_runtime_refs"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    function_targets: list[ResolvedRuntimeFunctionTarget] = Field(default_factory=list)
    class_refs: list[ResolvedRuntimeClassRef] = Field(default_factory=list)
    evidence: JsonObject = Field(default_factory=JsonObject)


class ConfigureServiceApiDependencyRoutesResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["configure_service_api_dependency_routes"] = "configure_service_api_dependency_routes"

    # Attributes
    status: str = Field(default="succeeded")
    error: str | None = Field(default=None)
    route_count: int = Field(default=0)
    route_consumers_started: bool = Field(default=False)


class EnvironmentOntologyMembership(BaseModel):
    """
    Environment-owned membership pointer to one Ontology authority.
    Contract:
    - This is not an OIG/OIGI inventory view.
    - OIGI discovery remains behind the linked Ontology authority.
    - Commit fields are mutation/read receipts for the Environment lane only.
    """

    # Attributes
    environment_ontology_id: UUID | None = Field(default=None)
    ontology_id: UUID
    role: str = Field(default="runtime")
    status: str = Field(default="active")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    commit_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class AttachEnvironmentOntologyRequest(EnvironmentOperationRequest):
    """
    Attach one Ontology authority to an existing stable Environment.
    Contract:
    - Mutates `Environment.ontologies` through the Environment projection lane.
    - Service implementation must route the mutation through Ontology graph
    authority; no service-local registry is allowed.
    - Does not accept or persist OIG/OIGI membership or OIG commit pins.
    """

    # Discriminator Tag
    operation: Literal["attach_environment_ontology"] = "attach_environment_ontology"

    # Attributes
    ontology_id: UUID
    role: str = Field(default="runtime")
    status: str = Field(default="active")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    expected_graph_hash_pre: str | None = Field(default=None)
    expected_head_commit_id: UUID | None = Field(default=None)
    commit: bool = Field(default=True)
    publish: bool = Field(default=False)


class AttachEnvironmentOntologyResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["attach_environment_ontology"] = "attach_environment_ontology"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    membership: EnvironmentOntologyMembership | None = Field(default=None)
    commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    graph_hash_pre: str | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class EnsureEnvironmentOntologyRuntimeRequest(EnvironmentOperationRequest):
    """
    Resolve and register an Ontology-owned runtime artifact set for this running
    Environment.
    Contract:
    - This does not create Environment/Ontology membership. Use
    `attach_environment_ontology` for commit truth first.
    - Runtime artifacts are resolved through Ontology service authority.
    - Environment owns only an activation/availability registry over returned
    artifact-set descriptors; Ontology remains artifact provenance authority.
    """

    # Discriminator Tag
    operation: Literal["ensure_environment_ontology_runtime"] = "ensure_environment_ontology_runtime"

    # Attributes
    ontology_id: UUID | None = Field(default=None)
    package_name: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    artifact_set_id: str | None = Field(default=None)
    workspace_revision_id: str | None = Field(default=None)
    materialization_ref: str | None = Field(default=None)
    include_artifacts: bool = Field(default=True)
    source_payload: JsonObject | None = Field(default=None)
    membership_commit_id: UUID | None = Field(default=None)


class EnsureEnvironmentOntologyRuntimeResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["ensure_environment_ontology_runtime"] = "ensure_environment_ontology_runtime"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    ontology_id: UUID | None = Field(default=None)
    package_name: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    artifact_set_id: str | None = Field(default=None)
    runtime_projection_descriptor_count: int = Field(default=0)
    capability_object_count: int = Field(default=0)
    capability_function_count: int = Field(default=0)
    registered_artifact_ref_count: int = Field(default=0)
    registry_artifact_ref_count: int = Field(default=0)
    membership_commit_id: UUID | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class ListEnvironmentOntologiesRequest(EnvironmentOperationRequest):
    """
    List Environment-owned Ontology memberships from a committed Environment DTO.
    Contract:
    - Returns only `EnvironmentOntology` membership pointers.
    - Does not expand Ontology-owned OIGI inventory.
    """

    # Discriminator Tag
    operation: Literal["list_environment_ontologies"] = "list_environment_ontologies"

    # Attributes
    commit_id: UUID | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    expected_graph_hash_post: str | None = Field(default=None)
    dto_class_ref: str | None = Field(default="aware_environment_ontology_dto.environment.environment.Environment")
    dto_package_name: str | None = Field(default="environment-ontology-dto")
    dto_import_root: str | None = Field(default="aware_environment_ontology_dto")


class ListEnvironmentOntologiesResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["list_environment_ontologies"] = "list_environment_ontologies"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    memberships: list[EnvironmentOntologyMembership] = Field(default_factory=list)
    commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class EnvironmentProfileProjectionSpec(BaseModel):
    # Attributes
    object_projection_graph_ref: str = Field(
        description="Canonical OPG identity key (`{ocg_fqn_prefix}:{projection_name}`)."
    )
    view_key: str | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_default: bool = Field(default=False)


class EnvironmentProfileLayoutSectionSpec(BaseModel):
    # Attributes
    section_key: str = Field(description="Stable section key under the selected Attention LayoutConfig.")
    layout_config_section_config_id: UUID | None = Field(
        default=None, description="Optional direct Attention LayoutConfigSectionConfig id."
    )
    object_projection_graph_ref: str | None = Field(
        default=None, description="Optional OPG ref hosted in this section."
    )
    view_key: str | None = Field(default=None)
    key: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_default: bool = Field(default=False)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class EnvironmentProfileLayoutConfigSpec(BaseModel):
    # Attributes
    layout_key: str | None = Field(default=None, description="Canonical Attention LayoutConfig key.")
    layout_config_id: UUID | None = Field(default=None, description="Optional direct Attention LayoutConfig id.")
    key: str | None = Field(default=None, description="Optional stable association key under the ThreadConfig.")
    position: int | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    sections: list[EnvironmentProfileLayoutSectionSpec] = Field(default_factory=list)


class EnvironmentProfileThreadConfigSpec(BaseModel):
    # Attributes
    key: str = Field(description="Reusable ThreadConfig key under the target ProcessConfig.")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    workspace_view_key: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_default: bool = Field(default=False)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    state_prompt_template: str | None = Field(default=None)
    projection_refs: list[EnvironmentProfileProjectionSpec] = Field(default_factory=list)
    layout_configs: list[EnvironmentProfileLayoutConfigSpec] = Field(default_factory=list)


class EnvironmentProfileProcessConfigSpec(BaseModel):
    # Attributes
    key: str = Field(description="Reusable ProcessConfig key under the profile.")
    type: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    shape: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_default: bool = Field(default=False)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    thread_configs: list[EnvironmentProfileThreadConfigSpec] = Field(default_factory=list)


class EnvironmentProfileTopologyLayoutSeedSpec(BaseModel):
    # Attributes
    layout_key: str = Field(description="Must reference a layout candidate declared in the selected ThreadConfig.")
    key: str | None = Field(default=None)
    position: int | None = Field(default=None)
    activate_on_seed: bool = Field(default=False)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class EnvironmentProfileTopologyThreadSeedSpec(BaseModel):
    # Attributes
    thread_config_key: str = Field(description="Must reference a ThreadConfig key under the selected ProcessConfig.")
    thread_key: str = Field(description="Runtime Thread.key for this concrete seed instance.")
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_main: bool = Field(default=False)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    layout_seeds: list[EnvironmentProfileTopologyLayoutSeedSpec] = Field(default_factory=list)


class EnvironmentProfileTopologyProcessSeedSpec(BaseModel):
    # Attributes
    process_config_key: str = Field(description="Must reference a ProcessConfig key under the selected profile.")
    process_key: str = Field(description="Runtime Process.key for this concrete seed instance.")
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    thread_seeds: list[EnvironmentProfileTopologyThreadSeedSpec] = Field(default_factory=list)


class EnvironmentProfileTopologySeedSpec(BaseModel):
    # Attributes
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    narrative: str | None = Field(default=None)
    process_seeds: list[EnvironmentProfileTopologyProcessSeedSpec] = Field(default_factory=list)


class EnvironmentProfileRuntimeMountReceipt(BaseModel):
    # Attributes
    environment_id: UUID
    environment_profile_id: UUID
    topology_seed_key: str
    process_config_id: UUID | None = Field(default=None)
    process_key: str
    process_id: UUID
    thread_config_id: UUID | None = Field(default=None)
    thread_key: str
    thread_id: UUID
    thread_layout_config_id: UUID | None = Field(default=None)
    layout_key: str | None = Field(default=None)
    layout_config_id: UUID | None = Field(default=None)
    layout_id: UUID | None = Field(default=None)
    thread_layout_id: UUID | None = Field(default=None)
    activate_on_seed: bool = Field(default=False)
    status: str = Field(default="succeeded")


class EnvironmentProfileInstallSpec(BaseModel):
    # Attributes
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    narrative: str | None = Field(default=None)
    process_configs: list[EnvironmentProfileProcessConfigSpec] = Field(default_factory=list)


class UpsertEnvironmentProfileRequest(EnvironmentOperationRequest):
    # Attributes
    operation: str = Field(default="upsert_environment_profile")
    environment_config_id: UUID | None = Field(
        default=None,
        description="Optional hosted EnvironmentConfig override.\nContract:\n- Normal hosted service calls omit this and Environment service resolves\nthe EnvironmentConfig from its own runtime artifact set.\n- Test/tool callers may provide it to validate deterministic profile\nconfig IDs without making Interface own EnvironmentConfig truth.",
    )
    profile: EnvironmentProfileInstallSpec
    topology_seeds: list[EnvironmentProfileTopologySeedSpec] = Field(default_factory=list)
    validate_only: bool = Field(default=False)


class UpsertEnvironmentProfileResponse(EnvironmentOperationResponse):
    # Attributes
    operation: str = Field(default="upsert_environment_profile")
    status: str
    error: str | None = Field(default=None)
    environment_config_id: UUID | None = Field(default=None)
    environment_profile_config_id: UUID | None = Field(default=None)
    environment_profile_id: UUID | None = Field(default=None)
    process_config_ids: list[UUID] = Field(default_factory=list)
    thread_config_ids: list[UUID] = Field(default_factory=list)
    thread_projection_association_ids: list[UUID] = Field(default_factory=list)
    thread_layout_config_ids: list[UUID] = Field(default_factory=list)
    topology_seed_ids: list[UUID] = Field(default_factory=list)
    topology_process_seed_ids: list[UUID] = Field(default_factory=list)
    topology_thread_seed_ids: list[UUID] = Field(default_factory=list)
    topology_thread_layout_seed_ids: list[UUID] = Field(default_factory=list)


class ProvisionEnvironmentProfileRequest(EnvironmentOperationRequest):
    # Attributes
    operation: str = Field(default="provision_environment_profile")
    environment_profile_id: UUID | None = Field(default=None)
    topology_seed_key: str
    validate_only: bool = Field(default=False)


class ProvisionEnvironmentProfileResponse(EnvironmentOperationResponse):
    # Attributes
    operation: str = Field(default="provision_environment_profile")
    status: str
    error: str | None = Field(default=None)
    environment_profile_id: UUID | None = Field(default=None)
    process_ids: list[UUID] = Field(default_factory=list)
    thread_ids: list[UUID] = Field(default_factory=list)
    thread_layout_ids: list[UUID] = Field(default_factory=list)
    runtime_mounts: list[EnvironmentProfileRuntimeMountReceipt] = Field(default_factory=list)


class EnvironmentActorAdmissionRoleEligibility(BaseModel):
    # Attributes
    environment_profile_actor_config_id: UUID
    actor_config_role_config_id: UUID
    role_config_id: UUID
    role_config_name: str | None = Field(default=None)


class EnvironmentActorAdmissionRoleBinding(BaseModel):
    # Attributes
    environment_profile_actor_config_id: UUID
    actor_config_role_config_id: UUID
    role_config_id: UUID
    role_config_name: str | None = Field(default=None)
    actor_id: UUID
    role_id: UUID
    actor_role_id: UUID
    role_class_instance_id: UUID
    class_instance_identity_id: UUID
    role_config_class_config_id: UUID
    object_instance_graph_identity_id: UUID
    object_instance_graph_branch_key: str = Field(default="all")
    object_instance_graph_branch_id: UUID | None = Field(default=None)


class EnvironmentActorAdmissionReceipt(BaseModel):
    # Attributes
    accepted: bool = Field(default=False)
    status: str
    error: str | None = Field(default=None)
    reason: str | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    environment_id: UUID
    environment_profile_id: UUID
    environment_profile_actor_config_id: UUID | None = Field(default=None)
    actor_config_id: UUID | None = Field(default=None)
    class_instance_identity_id: UUID | None = Field(default=None)
    object_instance_graph_branch_key: str = Field(default="all")
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    requested_role_config_ids: list[UUID] = Field(default_factory=list)
    requested_role_config_names: list[str] = Field(default_factory=list)
    eligible_roles: list[EnvironmentActorAdmissionRoleEligibility] = Field(default_factory=list)
    bindings: list[EnvironmentActorAdmissionRoleBinding] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    evidence: JsonObject = Field(default_factory=JsonObject)


class AdmitEnvironmentActorResponse(EnvironmentOperationResponse):
    # Attributes
    operation: str = Field(default="admit_actor")
    request_id: UUID | None = Field(default=None)
    accepted: bool = Field(default=False)
    status: str
    error: str | None = Field(default=None)
    receipt: EnvironmentActorAdmissionReceipt
    evidence: JsonObject = Field(default_factory=JsonObject)


class StartEnvironmentSessionRequest(EnvironmentOperationRequest):
    """
    Start a shared EnvironmentSession after accepted Environment admission.
    Contract:
    - Admission receipt is required and must match actor/environment/profile.
    - Creates or resolves a session under the EnvironmentProfile and joins the
    admitted actor as a member.
    - Resolves the Environment-owned default navigation context only when
    `resolve_default_navigation_context` is true.
    - Callers never supply Process/Thread defaults through this operation.
    """

    # Attributes
    operation: str = Field(default="start_environment_session")
    request_id: UUID | None = Field(default=None)
    environment_profile_id: UUID
    environment_session_config_id: UUID
    admission_receipt: EnvironmentActorAdmissionReceipt
    session_key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    resolve_default_navigation_context: bool = Field(default=False)
    metadata: JsonObject = Field(default_factory=JsonObject)


class JoinEnvironmentSessionRequest(EnvironmentOperationRequest):
    """
    Join an existing shared EnvironmentSession after accepted Environment admission.
    Contract:
    - Admission receipt is required and must match actor/environment/profile.
    - Resolves the Environment-owned default navigation context only when
    `resolve_default_navigation_context` is true.
    - Callers never supply Process/Thread defaults through this operation.
    """

    # Attributes
    operation: str = Field(default="join_environment_session")
    request_id: UUID | None = Field(default=None)
    environment_profile_id: UUID
    environment_session_id: UUID
    admission_receipt: EnvironmentActorAdmissionReceipt
    reason: str | None = Field(default=None)
    resolve_default_navigation_context: bool = Field(default=False)
    metadata: JsonObject = Field(default_factory=JsonObject)


class DescribeEnvironmentSessionRequest(EnvironmentOperationRequest):
    """
    Describe a shared EnvironmentSession.
    Contract:
    - Read model only; does not grant admission or navigation.
    """

    # Attributes
    operation: str = Field(default="describe_environment_session")
    environment_session_id: UUID


class EnvironmentSessionIdentityEvidence(BaseModel):
    # Attributes
    identity_session: SessionSummary | None = Field(default=None)
    identity_member: SessionMemberSummary | None = Field(default=None)
    identity_actor_roles: list[SessionMemberActorRoleSummary] = Field(default_factory=list)
    evidence: JsonObject = Field(default_factory=JsonObject)


class EnvironmentSessionView(BaseModel):
    # Attributes
    environment_session_id: UUID
    environment_session_config_id: UUID | None = Field(default=None)
    identity_session_id: UUID | None = Field(default=None)
    identity_session: SessionSummary | None = Field(default=None)
    environment_id: UUID
    environment_profile_id: UUID
    session_key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    created_by_actor_id: UUID | None = Field(default=None)
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class EnvironmentSessionJoinReceipt(BaseModel):
    # Attributes
    accepted: bool = Field(default=False)
    status: str
    error: str | None = Field(default=None)
    reason: str | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    environment_id: UUID
    environment_profile_id: UUID
    environment_session_id: UUID | None = Field(default=None)
    environment_session_key: str | None = Field(default=None)
    identity_evidence: EnvironmentSessionIdentityEvidence | None = Field(default=None)
    blockers: list[str] = Field(default_factory=list)
    evidence: JsonObject = Field(default_factory=JsonObject)


class StartEnvironmentSessionResponse(EnvironmentOperationResponse):
    # Attributes
    operation: str = Field(default="start_environment_session")
    request_id: UUID | None = Field(default=None)
    accepted: bool = Field(default=False)
    status: str
    error: str | None = Field(default=None)
    session: EnvironmentSessionView | None = Field(default=None)
    join_receipt: EnvironmentSessionJoinReceipt
    default_navigation_context: EnvironmentNavigationContextView | None = Field(default=None)
    default_navigation_receipt: EnvironmentNavigationCommitReceipt | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class JoinEnvironmentSessionResponse(EnvironmentOperationResponse):
    # Attributes
    operation: str = Field(default="join_environment_session")
    request_id: UUID | None = Field(default=None)
    accepted: bool = Field(default=False)
    status: str
    error: str | None = Field(default=None)
    session: EnvironmentSessionView | None = Field(default=None)
    receipt: EnvironmentSessionJoinReceipt
    default_navigation_context: EnvironmentNavigationContextView | None = Field(default=None)
    default_navigation_receipt: EnvironmentNavigationCommitReceipt | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class DescribeEnvironmentSessionResponse(EnvironmentOperationResponse):
    # Attributes
    operation: str = Field(default="describe_environment_session")
    status: str
    error: str | None = Field(default=None)
    session: EnvironmentSessionView | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class ResolveEnvironmentSessionAttentionRequest(EnvironmentOperationRequest):
    """
    Environment-owned resolution over session Thread/Layout pins into Attention.
    Contract:
    - Environment validates the EnvironmentSession/NavigationContext/SessionThread
    scope through Environment-owned state.
    - AttentionSession and AttentionFocusTransition structure is validated by
    the Attention service surface, not by reading Attention ontology internals.
    - This is a read/validation receipt, not a persisted frame model.
    """

    # Discriminator Tag
    operation: Literal["resolve_environment_session_attention"] = "resolve_environment_session_attention"

    # Attributes
    request_id: UUID | None = Field(default=None)
    environment_session_id: UUID
    environment_navigation_context_id: UUID | None = Field(default=None)
    environment_session_thread_id: UUID | None = Field(default=None)
    environment_session_attention_session_id: UUID | None = Field(default=None)
    expected_attention_session_id: UUID | None = Field(default=None)
    attention_focus_transition_id: UUID | None = Field(default=None)
    expected_attention_session_section_id: UUID | None = Field(default=None)
    expected_focus_scope_id: UUID | None = Field(default=None)
    expected_object_instance_graph_commit_id: UUID | None = Field(default=None)
    expected_projection_hash: str | None = Field(default=None)
    include_attention_session: bool = Field(default=True)
    include_transition_list: bool = Field(default=False)
    transition_limit: int | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class EnvironmentSessionAttentionResolution(BaseModel):
    # Attributes
    environment_session_id: UUID
    environment_navigation_context_id: UUID | None = Field(default=None)
    environment_session_thread_id: UUID | None = Field(default=None)
    environment_session_attention_session_id: UUID | None = Field(default=None)
    environment_id: UUID
    environment_profile_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    thread_layout_id: UUID | None = Field(default=None)
    attention_session_id: UUID | None = Field(default=None)
    identity_session_id: UUID | None = Field(default=None)
    attention_session: AttentionSessionPin | None = Field(default=None)
    active_transition: AttentionFocusTransitionPin | None = Field(default=None)
    validation: AttentionTransitionValidationResult | None = Field(default=None)
    transitions: list[AttentionFocusTransitionPin] = Field(default_factory=list)
    status: str = Field(default="resolved")
    blockers: list[str] = Field(default_factory=list)
    evidence: JsonObject = Field(default_factory=JsonObject)


class ResolveEnvironmentSessionAttentionResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["resolve_environment_session_attention"] = "resolve_environment_session_attention"

    # Attributes
    request_id: UUID | None = Field(default=None)
    status: str
    error: str | None = Field(default=None)
    resolution: EnvironmentSessionAttentionResolution | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class MountEnvironmentSessionAttentionRequest(EnvironmentOperationRequest):
    """Commit one EnvironmentSession-owned portal to an existing AttentionSession."""

    # Discriminator Tag
    operation: Literal["mount_environment_session_attention"] = "mount_environment_session_attention"

    # Attributes
    request_id: UUID | None = Field(default=None)
    environment_session_id: UUID
    attention_session_id: UUID
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    metadata: JsonObject = Field(default_factory=JsonObject)


class MountEnvironmentSessionAttentionResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["mount_environment_session_attention"] = "mount_environment_session_attention"

    # Attributes
    request_id: UUID | None = Field(default=None)
    environment_session_attention_session_id: UUID
    environment_session_id: UUID
    attention_session_id: UUID
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    status: str
    metadata: JsonObject = Field(default_factory=JsonObject)
    domain_commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)


class EnvironmentNavigationContextView(BaseModel):
    # Attributes
    environment_navigation_context_id: UUID
    environment_session_id: UUID
    environment_id: UUID
    key: str
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    is_default: bool = Field(default=False)
    selected_process_id: UUID | None = Field(default=None)
    selected_thread_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class EnvironmentNavigationCommitReceipt(BaseModel):
    # Attributes
    accepted: bool = Field(default=False)
    status: str
    error: str | None = Field(default=None)
    reason: str | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    environment_id: UUID
    environment_session_id: UUID
    environment_navigation_context_id: UUID | None = Field(default=None)
    key: str | None = Field(default=None)
    is_default: bool = Field(default=False)
    branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    graph_hash_pre: str | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    function_call_id: UUID | None = Field(default=None)
    function_call_response_id: UUID | None = Field(default=None)
    selected_process_id: UUID | None = Field(default=None)
    selected_thread_id: UUID | None = Field(default=None)
    blockers: list[str] = Field(default_factory=list)
    evidence: JsonObject = Field(default_factory=JsonObject)


class CreateEnvironmentNavigationContextRequest(EnvironmentOperationRequest):
    """
    Create one EnvironmentSession-owned navigation context.
    Contract:
    - Requires accepted EnvironmentSession join evidence.
    - Does not accept Environment admission receipts.
    - Does not resolve Attention focus or Experience lens/action state.
    """

    # Discriminator Tag
    operation: Literal["create_environment_navigation_context"] = "create_environment_navigation_context"

    # Attributes
    request_id: UUID | None = Field(default=None)
    environment_session_id: UUID
    session_join_receipt: EnvironmentSessionJoinReceipt
    key: str
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    is_default: bool = Field(default=False)
    selected_process_id: UUID | None = Field(default=None)
    selected_thread_id: UUID | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class CreateEnvironmentNavigationContextResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["create_environment_navigation_context"] = "create_environment_navigation_context"

    # Attributes
    request_id: UUID | None = Field(default=None)
    accepted: bool = Field(default=False)
    status: str
    error: str | None = Field(default=None)
    context: EnvironmentNavigationContextView | None = Field(default=None)
    receipt: EnvironmentNavigationCommitReceipt
    evidence: JsonObject = Field(default_factory=JsonObject)


class SelectEnvironmentNavigationTargetRequest(EnvironmentOperationRequest):
    """
    Select the Process/Thread target for one Environment navigation context.
    Contract:
    - Requires accepted EnvironmentSession join evidence.
    - Mutates only the EnvironmentNavigationContext target pointer.
    - History is derived from graph commits; no custom navigation event rail.
    """

    # Discriminator Tag
    operation: Literal["select_environment_navigation_target"] = "select_environment_navigation_target"

    # Attributes
    request_id: UUID | None = Field(default=None)
    environment_session_id: UUID
    environment_navigation_context_id: UUID
    session_join_receipt: EnvironmentSessionJoinReceipt
    selected_process_id: UUID | None = Field(default=None)
    selected_thread_id: UUID | None = Field(default=None)
    expected_head_commit_id: UUID | None = Field(default=None)
    expected_graph_hash_pre: str | None = Field(default=None)
    reason: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class SelectEnvironmentNavigationTargetResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["select_environment_navigation_target"] = "select_environment_navigation_target"

    # Attributes
    request_id: UUID | None = Field(default=None)
    accepted: bool = Field(default=False)
    status: str
    error: str | None = Field(default=None)
    context: EnvironmentNavigationContextView | None = Field(default=None)
    receipt: EnvironmentNavigationCommitReceipt
    evidence: JsonObject = Field(default_factory=JsonObject)


class DescribeEnvironmentNavigationContextRequest(EnvironmentOperationRequest):
    """
    Describe one Environment navigation context.
    Contract:
    - Requires accepted EnvironmentSession join evidence.
    - Read model only; does not grant admission or Attention access.
    """

    # Discriminator Tag
    operation: Literal["describe_environment_navigation_context"] = "describe_environment_navigation_context"

    # Attributes
    environment_session_id: UUID
    environment_navigation_context_id: UUID
    session_join_receipt: EnvironmentSessionJoinReceipt
    include_commit: bool = Field(default=True)


class DescribeEnvironmentNavigationContextResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["describe_environment_navigation_context"] = "describe_environment_navigation_context"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    context: EnvironmentNavigationContextView | None = Field(default=None)
    blockers: list[str] = Field(default_factory=list)
    evidence: JsonObject = Field(default_factory=JsonObject)


class ListEnvironmentNavigationContextsRequest(EnvironmentOperationRequest):
    """
    List Environment navigation contexts owned by one EnvironmentSession.
    Contract:
    - Requires accepted EnvironmentSession join evidence.
    - Returns context views only; navigation history remains commit-derived.
    """

    # Discriminator Tag
    operation: Literal["list_environment_navigation_contexts"] = "list_environment_navigation_contexts"

    # Attributes
    environment_session_id: UUID
    session_join_receipt: EnvironmentSessionJoinReceipt
    include_closed: bool = Field(default=False)


class ListEnvironmentNavigationContextsResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["list_environment_navigation_contexts"] = "list_environment_navigation_contexts"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    contexts: list[EnvironmentNavigationContextView] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    evidence: JsonObject = Field(default_factory=JsonObject)


class DescribeEnvironmentOPGConstructor(BaseModel):
    # Attributes
    function_id: UUID
    root_class_config_id: UUID | None = Field(default=None)


class DescribeEnvironmentOPG(BaseModel):
    # Attributes
    id: UUID
    projection_hash: str
    name: str | None = Field(default=None)
    description: str | None = Field(default=None)
    supports_virtual_build: bool = Field(default=True)
    constructors: list[DescribeEnvironmentOPGConstructor] = Field(default_factory=list)


class DescribeEnvironmentConfigResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["describe_environment_config"] = "describe_environment_config"

    # Attributes
    title: str | None = Field(default=None)
    environment_config_id: UUID | None = Field(default=None)
    environment_config_title: str | None = Field(default=None)
    canonical_language: str | None = Field(default=None)
    bundle_manifest_path: str | None = Field(default=None)
    bundle_manifest_http_path: str | None = Field(default=None)
    bundle_artifact_http_path_prefix: str | None = Field(default=None)
    bundle_descriptor_http_path: str | None = Field(default=None)
    bundle_head_id: str | None = Field(default=None)
    bundle_release_identity: JsonObject | None = Field(default=None)
    ocg_id: UUID | None = Field(default=None)
    opg_hashes: list[str] = Field(default_factory=list)
    opgs: list[DescribeEnvironmentOPG] = Field(default_factory=list)


class DescribeEnvironmentResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["describe_environment"] = "describe_environment"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    environment_config_id: UUID | None = Field(default=None)
    environment_config_title: str | None = Field(default=None)
    bundle_manifest_path: str | None = Field(default=None)
    bundle_manifest_http_path: str | None = Field(default=None)
    bundle_artifact_http_path_prefix: str | None = Field(default=None)
    bundle_descriptor_http_path: str | None = Field(default=None)
    bundle_head_id: str | None = Field(default=None)
    bundle_release_identity: JsonObject | None = Field(default=None)
    ocg_id: UUID | None = Field(default=None)
    environment_title: str | None = Field(default=None)
    environment_description: str | None = Field(default=None)
    boot_process_id: UUID | None = Field(default=None)
    boot_thread_id: UUID | None = Field(default=None)
    boot_branch_id: UUID | None = Field(default=None)
    head_commit_id: UUID | None = Field(default=None)
    head_graph_hash_post: str | None = Field(default=None)
    head_object_instance_graph_id: UUID | None = Field(default=None)
    head_root_object_id: UUID | None = Field(default=None)
    head_version: int | None = Field(default=None)


class DescribeEnvironmentTopologyLane(BaseModel):
    # Attributes
    lane_hash: str
    opg_id: UUID | None = Field(
        default=None,
        description="Best-effort OPG descriptor from hosted OCG (when lane_hash matches a hosted projection_hash).",
    )
    opg_name: str | None = Field(default=None)


class DescribeEnvironmentTopologyAttachment(BaseModel):
    # Attributes
    assoc_id: UUID = Field(description="ThreadObjectInstanceGraphBranch association id.")
    title: str | None = Field(default=None)
    is_active: bool = Field(default=True)
    object_instance_graph_branch_id: UUID
    object_instance_graph_identity_id: UUID | None = Field(
        default=None,
        description="OIGI anchor (invertible branch id for the object_instance_graph_identity projection).",
    )
    domain_branch_id: UUID | None = Field(
        default=None,
        description="Resolved domain Branch.id for this attachment (when identity anchor is present + materialized).",
    )
    lanes: list[DescribeEnvironmentTopologyLane] = Field(default_factory=list)


class DescribeEnvironmentTopologySection(BaseModel):
    # Attributes
    section_key: str = Field(description="Stable section key inside the active Thread layout.")
    title: str = Field(default="Section")
    description: str | None = Field(default=None)
    order: int = Field(default=0)
    flex: float = Field(default=1.0)
    is_visible: bool = Field(default=True)
    focus_scope_id: UUID | None = Field(
        default=None, description="Active Attention FocusScope for this section, when already materialized."
    )
    view_ref: str | None = Field(
        default=None, description="Canonical compiled view ref (`<experience>.<observable>.<view>`)."
    )
    view_key: str | None = Field(default=None, description="Projection-local view key (`<observable>.<view>`).")
    package_name: str | None = Field(
        default=None, description="Owning canonical experience package, derived from `view_ref` when available."
    )
    pane_key: str | None = Field(
        default=None, description="Optional pane key resolved by the Interface Host package registry."
    )


class DescribeEnvironmentTopologyLayout(BaseModel):
    # Attributes
    layout_id: UUID | None = Field(default=None)
    layout_key: str | None = Field(default=None)
    title: str = Field(default="Layout")
    description: str | None = Field(default=None)
    is_active: bool = Field(default=False)
    sections: list[DescribeEnvironmentTopologySection] = Field(default_factory=list)


class DescribeEnvironmentTopologyThread(BaseModel):
    # Attributes
    thread_id: UUID
    thread_key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    active_layout_id: UUID | None = Field(default=None)
    active_layout_key: str | None = Field(default=None)
    layouts: list[DescribeEnvironmentTopologyLayout] = Field(default_factory=list)
    attachments: list[DescribeEnvironmentTopologyAttachment] = Field(default_factory=list)


class DescribeEnvironmentTopologyProcess(BaseModel):
    # Attributes
    process_id: UUID
    process_key: str | None = Field(default=None)
    title: str
    description: str | None = Field(default=None)
    threads: list[DescribeEnvironmentTopologyThread] = Field(default_factory=list)


class DescribeEnvironmentTopologyResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["describe_environment_topology"] = "describe_environment_topology"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    processes: list[DescribeEnvironmentTopologyProcess] = Field(default_factory=list)


class EnvironmentStatusAuthorityKind(Enum):
    environment_interface_view = "environment_interface_view"
    local_fs_view = "local_fs_view"
    commit_truth = "commit_truth"
    mixed = "mixed"


class EnvironmentStatusAuthority(BaseModel):
    # Attributes
    kind: EnvironmentStatusAuthorityKind
    source_artifact: str | None = Field(default=None)


class EnvironmentStatusBlock(BaseModel):
    # Attributes
    name: str
    authority: EnvironmentStatusAuthority
    payload: JsonObject = Field(default_factory=JsonObject)
    available: bool = Field(default=True)
    unavailable_reason: str | None = Field(default=None)


class DescribeEnvironmentStatusResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["describe_environment_status"] = "describe_environment_status"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    status_version: str
    blocks: list[EnvironmentStatusBlock] = Field(default_factory=list)
    refusals: JsonArray = Field(default_factory=JsonArray)


class EnvironmentReadinessPersistenceReceipt(BaseModel):
    # Attributes
    status: str
    backend: str
    database_url_ref: str | None = Field(default=None)
    environment_config_id: UUID | None = Field(default=None)
    ocg_id: UUID | None = Field(default=None)
    ocg_hash: str | None = Field(default=None)
    db_schema_hash: str | None = Field(default=None)
    db_schema_registry_hash: str | None = Field(default=None)
    marker_ocg_hash: str | None = Field(default=None)
    marker_head_commit_id: UUID | None = Field(default=None)
    installed: bool = Field(default=False)
    migrated: bool = Field(default=False)
    sql_root_count: int = Field(default=0)
    step_count: int = Field(default=0)


class EnvironmentReadinessGraphReceipt(BaseModel):
    # Attributes
    status: str
    lane_head_status: str | None = Field(default=None)
    genesis_status: str | None = Field(default=None)
    branch_id: UUID
    projection_hash: str | None = Field(default=None)
    object_projection_graph_id: UUID | None = Field(default=None)
    constructor_function_id: UUID | None = Field(default=None)
    lane_head_commit_id: UUID | None = Field(default=None)
    domain_commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    function_call_id: UUID | None = Field(default=None)
    function_call_response_id: UUID | None = Field(default=None)


class EnvironmentReadinessRouteReceipt(BaseModel):
    # Attributes
    api_package_name: str | None = Field(default=None)
    provider_service_package_name: str | None = Field(default=None)
    route_kind: str | None = Field(default=None)
    host_id: str | None = Field(default=None)
    host_version: str | None = Field(default=None)
    protocol_version: str | None = Field(default=None)
    endpoint_refs: list[str] = Field(default_factory=list)
    stream_endpoint_refs: list[str] = Field(default_factory=list)


class EnvironmentReadinessReceipt(BaseModel):
    # Attributes
    status: str
    actor_id: UUID | None = Field(default=None)
    environment_id: UUID
    environment_title: str | None = Field(default=None)
    environment_manifest_path: str | None = Field(default=None)
    environment_package_ref: JsonObject | None = Field(default=None)
    process_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    ocg_id: UUID | None = Field(default=None)
    opg_hashes: list[str] = Field(default_factory=list)
    graph: EnvironmentReadinessGraphReceipt | None = Field(default=None)
    persistence: EnvironmentReadinessPersistenceReceipt | None = Field(default=None)
    meta_route: EnvironmentReadinessRouteReceipt | None = Field(default=None)


class EnsureReadyResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["ensure_ready"] = "ensure_ready"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    bundle_manifest_path: str | None = Field(default=None)
    bundle_manifest_http_path: str | None = Field(default=None)
    bundle_artifact_http_path_prefix: str | None = Field(default=None)
    bundle_descriptor_http_path: str | None = Field(default=None)
    bundle_head_id: str | None = Field(default=None)
    bundle_release_identity: JsonObject | None = Field(default=None)
    ocg_id: UUID | None = Field(default=None)
    opg_hashes: list[str] = Field(default_factory=list)
    readiness_receipt: EnvironmentReadinessReceipt | None = Field(default=None)


class GetLaneHeadResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["get_lane_head"] = "get_lane_head"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    object_instance_graph_identity_id: UUID | None = Field(default=None)
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    object_projection_graph_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    head_version: int | None = Field(default=None)


class GetObjectInstanceGraphCommitResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["get_object_instance_graph_commit"] = "get_object_instance_graph_commit"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID
    object_instance_graph_id: UUID | None = Field(default=None)
    object_instance_graph_identity_id: UUID | None = Field(default=None)
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    object_projection_graph_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    graph_hash_pre: str | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    commit: JsonObject | None = Field(default=None)


class MaterializeCommittedProjectionDtoResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["materialize_committed_projection_dto"] = "materialize_committed_projection_dto"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    refusal_code: str | None = Field(default=None)
    dto_payload: JsonObject | None = Field(default=None)
    dto_class_ref: str | None = Field(default=None)
    class_config_id: UUID | None = Field(default=None)
    dto_package_name: str | None = Field(default=None)
    dto_import_root: str | None = Field(default=None)
    dto_artifact_digest: str | None = Field(default=None)
    commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    materializer_version: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class InvokeFunctionResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["invoke_function"] = "invoke_function"

    # Attributes
    status: str
    payload: JsonValue | None = Field(default=None)
    error: str | None = Field(default=None)
    logs: list[str] = Field(default_factory=list)
    execution_time_ms: int | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    graph_hash_pre: str | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    function_call_id: UUID | None = Field(default=None)
    function_call_response_id: UUID | None = Field(default=None)
    changes: JsonArray = Field(default_factory=JsonArray)
    commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    object_projection_graph_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    object_instance_graph_identity_id: UUID | None = Field(default=None)
    object_instance_graph_branch_id: UUID | None = Field(default=None)


class LaneCommitReceiptNotification(EnvironmentOperationNotification):
    """
    Canonical lane head receipt notification.
    The lane key is `(branch_id, projection_hash)`; receivers must not guess
    `branch_id` from env/thread.
    """

    # Discriminator Tag
    operation: Literal["lane_commit_receipt"] = "lane_commit_receipt"

    # Attributes
    commit_id: UUID
    object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Canonical Meta ObjectInstanceGraphCommit id for this domain commit.\nThis is the direct provenance ref consumers use when they need the\ndurable OIG commit identity instead of only the domain commit id.",
    )
    object_projection_graph_id: UUID | None = Field(
        default=None,
        description="ObjectProjectionGraph that owns the committed ObjectInstanceGraph when\nEnvironment/Meta topology resolution has enriched the receipt.",
    )
    object_projection_graph_identity_id: UUID | None = Field(
        default=None,
        description="ObjectProjectionGraphIdentity anchor for Attention focus targets.\nOptional at the raw commit-store edge; Environment topology/fanout should\npopulate it when resolving OIGI/OPG identity for focus attachment.",
    )
    object_instance_graph_id: UUID | None = Field(
        default=None, description="ObjectInstanceGraph snapshot identity for the committed lane head."
    )
    object_instance_graph_identity_id: UUID | None = Field(
        default=None, description="ObjectInstanceGraphIdentity worldline anchor for the committed lane head."
    )
    object_instance_graph_branch_id: UUID | None = Field(
        default=None,
        description="ObjectInstanceGraphBranch anchor for `(object_instance_graph_identity_id, branch_id)`.\nThis is the concrete materialized focus target id that Attention can use\nwithout subscribing to Meta directly.",
    )
    created_at_unix_ms: int | None = Field(
        default=None,
        description="Canonical commit creation timestamp (unix ms) when emitted by commit store.\nOptional for backward-compatible transports; receivers should fall back to\nobserved-at timestamps when absent.",
    )
    operation_label: str | None = Field(
        default=None,
        description="Canonical label for the operation that produced this commit (when known).\nThis must be emitted by runtime/commit-store writers; UI must not guess.",
    )
    call_target: InvokeFunctionCallTarget | None = Field(
        default=None, description="Optional function-call origin (when this commit was produced by invoke_function)."
    )
    function_id: UUID | None = Field(default=None)
    object_id: UUID | None = Field(default=None)
    class_instance_identity_id: UUID | None = Field(
        default=None,
        description="Canonical class-instance identity attribution for this commit when known.\nRuntime owns this value and must emit deterministic identity truth.",
    )
    graph_hash_post: str | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    head_version: int | None = Field(default=None)


class LaneEventReceiptNotification(EnvironmentOperationNotification):
    """
    Canonical reactivity event receipt notification derived from lane commits.
    Contract:
    - Emitted by runtime receipt environments after condition evaluation.
    - Deterministic per `(event_id, commit_id)` and safe for at-least-once transport.
    """

    # Discriminator Tag
    operation: Literal["lane_event_receipt"] = "lane_event_receipt"

    # Attributes
    event_id: UUID
    event_type: str
    source: str
    created_at_unix_ms: int
    commit_id: UUID
    target_actor_id: UUID | None = Field(default=None)
    actor_subscription_id: UUID | None = Field(default=None)
    event_config_condition_config_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)


class LaneActionExecutionReceiptNotification(EnvironmentOperationNotification):
    """
    Canonical action execution receipt notification derived from a reactivity event.
    Contract:
    - Emitted when one concrete action execution request is materialized.
    - Carries stable `action_execution_id` correlation for feedback/terminal receipts.
    """

    # Discriminator Tag
    operation: Literal["lane_action_execution_receipt"] = "lane_action_execution_receipt"

    # Attributes
    action_execution_id: UUID
    event_id: UUID
    event_type: str
    source: str
    created_at_unix_ms: int
    commit_id: UUID
    target_actor_id: UUID | None = Field(default=None)
    actor_subscription_id: UUID | None = Field(default=None)
    event_config_condition_config_id: UUID | None = Field(default=None)
    action_binding_id: UUID | None = Field(default=None)
    action_config_id: UUID | None = Field(default=None)
    action_type: str | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)


class LaneActionFeedbackReceiptNotification(EnvironmentOperationNotification):
    """
    Canonical progressive action feedback receipt.
    Canonical token sources:
    - `stage`: reactivity.ActionFeedbackStage
    - `status`: reactivity.ActionFeedbackStatus
    """

    # Discriminator Tag
    operation: Literal["lane_action_feedback_receipt"] = "lane_action_feedback_receipt"

    # Attributes
    action_execution_id: UUID
    event_id: UUID
    sequence: int
    created_at_unix_ms: int
    stage: str
    status: str
    action_binding_id: UUID | None = Field(default=None)
    action_config_id: UUID | None = Field(default=None)
    action_type: str | None = Field(default=None)
    message: str | None = Field(default=None)
    actor_identity_id: UUID | None = Field(default=None)
    actor_process_thread_id: UUID | None = Field(default=None)
    execution_request_id: UUID | None = Field(default=None)


class LaneActionTerminalReceiptNotification(EnvironmentOperationNotification):
    """
    Canonical action terminal receipt.
    Canonical token source:
    - `terminal_status`: reactivity.ActionTerminalStatus
    """

    # Discriminator Tag
    operation: Literal["lane_action_terminal_receipt"] = "lane_action_terminal_receipt"

    # Attributes
    action_execution_id: UUID
    event_id: UUID
    terminal_status: str
    handled: bool
    created_at_unix_ms: int
    action_binding_id: UUID | None = Field(default=None)
    action_config_id: UUID | None = Field(default=None)
    action_type: str | None = Field(default=None)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)
    actor_identity_id: UUID | None = Field(default=None)
    actor_process_thread_id: UUID | None = Field(default=None)
    execution_request_id: UUID | None = Field(default=None)


class LaneTurnStreamReceiptNotification(EnvironmentOperationNotification):
    """
    Canonical turn stream receipt emitted from service stream events.
    Contract:
    - Mirrors transport-level `stream_event` frames with canonical lane context.
    - Payload is non-SSOT telemetry for UX; authoritative state remains commit/event rails.
    """

    # Discriminator Tag
    operation: Literal["lane_turn_stream_receipt"] = "lane_turn_stream_receipt"

    # Attributes
    service: str
    inference_request_id: UUID
    created_at_unix_ms: int
    stream_kind: str
    sequence: int | None = Field(default=None)
    agent_identity_id: UUID | None = Field(default=None)
    agent_process_thread_id: UUID | None = Field(default=None)
    text_delta: str | None = Field(default=None)
    message: str | None = Field(default=None)
    payload: JsonValue | None = Field(default=None)
