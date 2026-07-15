from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ExperienceProgramOwnership:
    ref: str
    name: str
    path: str
    dependencies: tuple[str, ...]
    required_symbols: tuple[str, ...]
    optional_symbols: tuple[str, ...]
    invocation_plan_artifact: dict[str, object] | None = None
    program_config_plan_artifact: dict[str, object] | None = None
    program_apply_calls_artifact: dict[str, object] | None = None
    required_projection_ids: tuple[str, ...] = ()
    required_projection_node_ids: tuple[str, ...] = ()
    required_projection_node_identity_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExperienceEventBindingOwnership:
    projection: str
    type_ref: str
    class_fqn: str | None
    operation: str
    attribute: str | None = None


@dataclass(frozen=True, slots=True)
class ProjectionOwnedClassTruth:
    class_fqn: str
    attributes: frozenset[str]
    identity_key_attributes: frozenset[str] = frozenset()
    relationship_targets: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class ExperienceActorRoleContract:
    actor_config_class_fqn: str
    role_config_class_fqn: str


@dataclass(frozen=True, slots=True)
class ExperienceRoleOwnership:
    name: str
    source_path: str
    capabilities: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExperienceActorOwnership:
    name: str
    kind: str
    roles: tuple[str, ...]
    source_path: str


@dataclass(frozen=True, slots=True)
class ExperienceEnvironmentActorBinding:
    environment: str
    actor: str
    roles: tuple[str, ...]
    source_path: str


@dataclass(frozen=True, slots=True)
class ExperienceEventOwnership:
    symbol: str
    event_name: str
    renderer_key: str
    title: str | None
    description: str | None
    source_path: str
    bindings: tuple[ExperienceEventBindingOwnership, ...]
    package_name: str | None = None
    fqn_prefix: str | None = None
    is_dependency: bool = False


@dataclass(frozen=True, slots=True)
class ExperienceActionProgramBindingOwnership:
    program: str
    args: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExperienceActionOwnership:
    symbol: str
    action_name: str
    source_path: str
    params: tuple[str, ...]
    program_bindings: tuple[ExperienceActionProgramBindingOwnership, ...]
    package_name: str | None = None
    fqn_prefix: str | None = None
    is_dependency: bool = False


@dataclass(frozen=True, slots=True)
class ExperienceConnectorInvocationRequestFieldOwnership:
    attribute: str
    source_ref: str
    required: bool = True


@dataclass(frozen=True, slots=True)
class ExperienceConnectorInvocationActionConfigOwnership:
    action_key: str
    action_kind: str
    target_ref: str
    source_path: str
    label: str | None = None
    receipt_policy: str | None = None
    confirmation_policy: str | None = None
    optimistic_policy: str | None = None
    request_fields: tuple[ExperienceConnectorInvocationRequestFieldOwnership, ...] = ()


@dataclass(frozen=True, slots=True)
class ExperienceConnectorProviderOwnership:
    provider_key: str
    provider_kind: str
    source_path: str
    provider_ref: str | None = None
    label: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class ExperienceSensorConfigOwnership:
    sensor_key: str
    sensor_kind: str
    source_path: str
    source_ref: str | None = None
    observed_state_node_refs: tuple[str, ...] = ()
    label: str | None = None
    description: str | None = None
    invocation_action_configs: tuple[
        ExperienceConnectorInvocationActionConfigOwnership, ...
    ] = ()


@dataclass(frozen=True, slots=True)
class ExperienceActuatorConfigOwnership:
    actuator_key: str
    actuator_kind: str
    source_path: str
    target_ref: str | None = None
    affected_state_node_refs: tuple[str, ...] = ()
    label: str | None = None
    description: str | None = None
    invocation_action_configs: tuple[
        ExperienceConnectorInvocationActionConfigOwnership, ...
    ] = ()


@dataclass(frozen=True, slots=True)
class ExperienceConnectorConfigOwnership:
    connector_key: str
    connector_kind: str
    source_path: str
    label: str | None = None
    description: str | None = None
    providers: tuple[ExperienceConnectorProviderOwnership, ...] = ()
    sensor_configs: tuple[ExperienceSensorConfigOwnership, ...] = ()
    actuator_configs: tuple[ExperienceActuatorConfigOwnership, ...] = ()
    package_name: str | None = None
    fqn_prefix: str | None = None
    is_dependency: bool = False


@dataclass(frozen=True, slots=True)
class ExperienceEnvironmentProgramOwnership:
    program_config: str
    program_impl: str


@dataclass(frozen=True, slots=True)
class ExperienceEnvironmentEventActionOwnership:
    action: str


@dataclass(frozen=True, slots=True)
class ExperienceEnvironmentEventNodeScopeOwnership:
    node_ref: str


@dataclass(frozen=True, slots=True)
class ExperienceEnvironmentEventOwnership:
    event: str
    actions: tuple[ExperienceEnvironmentEventActionOwnership, ...]
    node_scopes: tuple[ExperienceEnvironmentEventNodeScopeOwnership, ...] = ()


@dataclass(frozen=True, slots=True)
class ExperienceEnvironmentOwnership:
    name: str
    source_path: str
    experiences: tuple[str, ...]
    programs: tuple[ExperienceEnvironmentProgramOwnership, ...]
    events: tuple[ExperienceEnvironmentEventOwnership, ...]


@dataclass(frozen=True, slots=True)
class ExperienceProjectionBranchOwnership:
    name: str
    is_default: bool
    source_path: str


@dataclass(frozen=True, slots=True)
class ExperienceProjectionViewOwnership:
    key: str
    is_default: bool
    source_path: str
    state_model_ref: str | None = None
    api_view_ref: str | None = None
    state_provider_ref: str | None = None
    invocation_actions: tuple[
        "ExperienceProjectionViewInvocationActionOwnership", ...
    ] = ()


@dataclass(frozen=True, slots=True)
class ExperienceProjectionViewInvocationActionOwnership:
    key: str
    source_path: str
    api_view_capability_endpoint_id: UUID | None = None
    endpoint_ref: str | None = None
    api_capability_endpoint_id: UUID | None = None
    sdk_operation_api_view_capability_endpoint_id: UUID | None = None
    sdk_operation_id: UUID | None = None
    label: str | None = None
    receipt_policy: str | None = None
    confirmation_policy: str | None = None
    optimistic_policy: str | None = None


@dataclass(frozen=True, slots=True)
class ExperienceViewApiViewOwnership:
    api_name: str
    view_name: str
    experience_name: str
    observable_key: str
    view_key: str
    observable_ref: str
    view_ref: str
    projection_view_key: str
    state_model_ref: str
    state_model_id: UUID | None
    is_default: bool
    source_path: str
    invocation_actions: tuple[
        ExperienceProjectionViewInvocationActionOwnership, ...
    ] = ()


@dataclass(frozen=True, slots=True)
class ExperienceViewApiOwnership:
    package_name: str
    fqn_prefix: str
    api_name: str
    source_path: str
    views: tuple[ExperienceViewApiViewOwnership, ...]


@dataclass(frozen=True, slots=True)
class ExperienceProjectionObservableOwnership:
    key: str
    source_path: str
    views: tuple[ExperienceProjectionViewOwnership, ...]


@dataclass(frozen=True, slots=True)
class ExperienceProjectionNodeKeyParamOwnership:
    name: str
    type_ref: str


@dataclass(frozen=True, slots=True)
class ExperienceProjectionNodeIdentityOwnership:
    key: str
    source_path: str


@dataclass(frozen=True, slots=True)
class ExperienceProjectionNodeOwnership:
    name: str
    node_ref: str
    source_path: str
    params: tuple[ExperienceProjectionNodeKeyParamOwnership, ...]
    identities: tuple[ExperienceProjectionNodeIdentityOwnership, ...]


@dataclass(frozen=True, slots=True)
class ExperienceProjectionSectionSurfaceOwnership:
    surface_key: str
    section_key: str
    observable_key: str
    view_key: str
    source_path: str
    source_surface_key: str | None = None
    graph_identity_ref: str | None = None
    node_identity_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ExperienceProjectionExperienceOwnership:
    name: str
    projection: str
    source_path: str
    branches: tuple[ExperienceProjectionBranchOwnership, ...]
    observables: tuple[ExperienceProjectionObservableOwnership, ...]
    nodes: tuple[ExperienceProjectionNodeOwnership, ...] = ()
    section_surfaces: tuple[ExperienceProjectionSectionSurfaceOwnership, ...] = ()


@dataclass(frozen=True, slots=True)
class ExperienceGraphEdgeOwnership:
    parent: str
    child: str
    source_path: str


@dataclass(frozen=True, slots=True)
class ExperienceGraphOwnership:
    name: str
    experience: str
    source_path: str
    root: str
    edges: tuple[ExperienceGraphEdgeOwnership, ...]


@dataclass(frozen=True, slots=True)
class ExperienceProjectionAPIContractParamOwnership:
    name: str
    type_ref: str


@dataclass(frozen=True, slots=True)
class ExperienceProjectionAPIContractOwnership:
    name: str
    source_path: str
    parent_class: str
    relationship_attribute: str
    key_attribute: str
    params: tuple[ExperienceProjectionAPIContractParamOwnership, ...]


@dataclass(frozen=True, slots=True)
class ExperienceProjectionAPIOwnership:
    name: str
    projection: str
    source_path: str
    contracts: tuple[ExperienceProjectionAPIContractOwnership, ...]


@dataclass(frozen=True, slots=True)
class ExperienceEnvironmentProfileThreadProjectionOwnership:
    projection_experience_name: str
    source_path: str
    view_key: str | None = None
    is_default: bool = False


@dataclass(frozen=True, slots=True)
class ExperienceEnvironmentProfileThreadLayoutSectionOwnership:
    section_key: str
    projection_experience_name: str
    view_key: str
    source_path: str
    key: str | None = None
    section_graph_binding_key: str | None = None
    position: int | None = None
    is_default: bool = False
    narrative: str | None = None
    intent: str | None = None


@dataclass(frozen=True, slots=True)
class ExperienceEnvironmentProfileThreadLayoutOwnership:
    layout_key: str
    source_path: str
    key: str | None = None
    position: int | None = None
    is_default: bool = False
    narrative: str | None = None
    intent: str | None = None
    sections: tuple[ExperienceEnvironmentProfileThreadLayoutSectionOwnership, ...] = ()


@dataclass(frozen=True, slots=True)
class ExperienceEnvironmentProfileThreadOwnership:
    key: str
    thread_key: str
    source_path: str
    title: str | None = None
    description: str | None = None
    workspace_view_key: str | None = None
    position: int | None = None
    is_default: bool = False
    narrative: str | None = None
    intent: str | None = None
    state_prompt_template: str | None = None
    projection_experiences: tuple[
        ExperienceEnvironmentProfileThreadProjectionOwnership, ...
    ] = ()
    layout_configs: tuple[ExperienceEnvironmentProfileThreadLayoutOwnership, ...] = ()


@dataclass(frozen=True, slots=True)
class ExperienceEnvironmentProfileProcessOwnership:
    type: str
    key: str
    process_key: str
    source_path: str
    title: str | None = None
    description: str | None = None
    shape: str | None = None
    position: int | None = None
    is_bootstrap_default: bool = False
    narrative: str | None = None
    intent: str | None = None
    thread_configs: tuple[ExperienceEnvironmentProfileThreadOwnership, ...] = ()


@dataclass(frozen=True, slots=True)
class ExperienceEnvironmentProfileRoleSpec:
    name: str
    description: str | None = None
    capabilities: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExperienceEnvironmentProfileActorSpec:
    key: str
    title: str | None = None
    description: str | None = None
    actor_type: str | None = None
    role_names: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExperienceEnvironmentProfileViewEventTransitionOwnership:
    key: str
    source_projection_experience_name: str
    source_view_key: str
    trigger_event_ref: str
    target_projection_experience_name: str
    target_section_graph_binding_key: str
    source_path: str
    trigger_event_config_ref: str | None = None
    name: str | None = None
    rationale: str | None = None
    idempotency_policy: str | None = None


@dataclass(frozen=True, slots=True)
class ExperienceEnvironmentProfileOwnership:
    experience_name: str
    key: str
    source_path: str
    title: str | None = None
    description: str | None = None
    narrative: str | None = None
    roles: tuple[ExperienceEnvironmentProfileRoleSpec, ...] = ()
    actors: tuple[ExperienceEnvironmentProfileActorSpec, ...] = ()
    process_configs: tuple[ExperienceEnvironmentProfileProcessOwnership, ...] = ()
    view_event_transitions: tuple[
        ExperienceEnvironmentProfileViewEventTransitionOwnership, ...
    ] = ()


@dataclass(frozen=True, slots=True)
class ExperienceViewStateModelContract:
    state_model_ref: str
    class_config_id: UUID
    source_path: str


@dataclass(frozen=True, slots=True)
class ExperienceCompilePlan:
    schema_version: int
    package_name: str
    fqn_prefix: str
    environment_handle: str
    source_files: tuple[str, ...]
    view_state_model_contracts: tuple[ExperienceViewStateModelContract, ...]
    view_api_ownership: ExperienceViewApiOwnership | None
    actor_role_contract: ExperienceActorRoleContract | None
    role_ownership: tuple[ExperienceRoleOwnership, ...]
    actor_ownership: tuple[ExperienceActorOwnership, ...]
    environment_actor_bindings: tuple[ExperienceEnvironmentActorBinding, ...]
    action_ownership: tuple[ExperienceActionOwnership, ...]
    connector_ownership: tuple[ExperienceConnectorConfigOwnership, ...]
    action_target_ownership: tuple[ExperienceConnectorConfigOwnership, ...]
    environment_ownership: tuple[ExperienceEnvironmentOwnership, ...]
    projection_experience_ownership: tuple[ExperienceProjectionExperienceOwnership, ...]
    environment_profile_ownership: tuple[ExperienceEnvironmentProfileOwnership, ...]
    projection_api_ownership: tuple[ExperienceProjectionAPIOwnership, ...]
    graph_ownership: tuple[ExperienceGraphOwnership, ...]
    program_ownership: tuple[ExperienceProgramOwnership, ...]
    event_ownership: tuple[ExperienceEventOwnership, ...]


@dataclass(frozen=True, slots=True)
class ExperienceCompilePlanArtifact:
    path: Path
    relpath: str
    hash_sha256: str


__all__ = [
    "ExperienceCompilePlan",
    "ExperienceCompilePlanArtifact",
    "ExperienceActionOwnership",
    "ExperienceActionProgramBindingOwnership",
    "ExperienceActuatorConfigOwnership",
    "ExperienceActorOwnership",
    "ExperienceActorRoleContract",
    "ExperienceConnectorConfigOwnership",
    "ExperienceConnectorInvocationActionConfigOwnership",
    "ExperienceConnectorProviderOwnership",
    "ExperienceEnvironmentProfileOwnership",
    "ExperienceEnvironmentProfileProcessOwnership",
    "ExperienceEnvironmentProfileActorSpec",
    "ExperienceEnvironmentProfileRoleSpec",
    "ExperienceEnvironmentProfileViewEventTransitionOwnership",
    "ExperienceViewStateModelContract",
    "ExperienceEnvironmentProfileThreadOwnership",
    "ExperienceEnvironmentProfileThreadProjectionOwnership",
    "ExperienceEnvironmentEventActionOwnership",
    "ExperienceEnvironmentEventOwnership",
    "ExperienceEnvironmentOwnership",
    "ExperienceEnvironmentProgramOwnership",
    "ExperienceEnvironmentActorBinding",
    "ExperienceEventBindingOwnership",
    "ExperienceEventOwnership",
    "ExperienceGraphEdgeOwnership",
    "ExperienceGraphOwnership",
    "ExperienceProgramOwnership",
    "ExperienceProjectionBranchOwnership",
    "ExperienceProjectionExperienceOwnership",
    "ExperienceProjectionAPIOwnership",
    "ExperienceProjectionAPIContractOwnership",
    "ExperienceProjectionAPIContractParamOwnership",
    "ExperienceProjectionNodeKeyParamOwnership",
    "ExperienceProjectionNodeIdentityOwnership",
    "ExperienceViewApiViewOwnership",
    "ExperienceViewApiOwnership",
    "ExperienceProjectionNodeOwnership",
    "ExperienceProjectionObservableOwnership",
    "ExperienceProjectionSectionSurfaceOwnership",
    "ExperienceProjectionViewInvocationActionOwnership",
    "ExperienceProjectionViewOwnership",
    "ExperienceRoleOwnership",
    "ExperienceSensorConfigOwnership",
    "ProjectionOwnedClassTruth",
]
