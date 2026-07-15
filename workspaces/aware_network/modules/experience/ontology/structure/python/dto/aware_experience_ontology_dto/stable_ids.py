# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_EXPERIENCE = uuid5(NAMESPACE_URL, "aware://experience/v1")


def stable_action_experience_id(*, action_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: action_config_id"""

    return uuid5(NS_EXPERIENCE, f"aware:action_experience:{action_config_id}")


def stable_action_experience_invocation_id(
    *, action_experience_id: UUID, experience_invocation_action_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: action_experience_id, experience_invocation_action_config_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:action_experience_invocation:{action_experience_id}:{experience_invocation_action_config_id}",
    )


def stable_action_experience_invocation_action_id(
    *, action_experience_invocation_id: UUID, experience_invocation_action_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: action_experience_invocation_id, experience_invocation_action_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:action_experience_invocation_action:{action_experience_invocation_id}:{experience_invocation_action_id}",
    )


def stable_action_experience_invocation_request_field_id(
    *, action_experience_invocation_id: UUID, attribute_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: action_experience_invocation_id, attribute_config_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:action_experience_invocation_request_field:{action_experience_invocation_id}:{attribute_config_id}",
    )


def stable_action_experience_program_id(*, action_experience_id: UUID, program_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: action_experience_id, program_config_id"""

    return uuid5(NS_EXPERIENCE, f"aware:action_experience_program:{action_experience_id}:{program_config_id}")


def stable_actuator_id(*, actuator_config_id: UUID, actuator_instance_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: actuator_config_id, actuator_instance_key"""

    actuator_instance_key_norm = (actuator_instance_key or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:actuator:{actuator_config_id}:{actuator_instance_key_norm}")


def stable_actuator_config_id(*, connector_config_id: UUID, actuator_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: connector_config_id, actuator_key"""

    actuator_key_norm = (actuator_key or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:actuator_config:{connector_config_id}:{actuator_key_norm}")


def stable_actuator_config_state_node_id(*, actuator_config_id: UUID, object_projection_graph_node_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: actuator_config_id, object_projection_graph_node_id"""

    return uuid5(
        NS_EXPERIENCE, f"aware:actuator_config_state_node:{actuator_config_id}:{object_projection_graph_node_id}"
    )


def stable_actuator_invocation_action_id(
    *, actuator_invocation_action_config_id: UUID, experience_invocation_action_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: actuator_invocation_action_config_id, experience_invocation_action_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:actuator_invocation_action:{actuator_invocation_action_config_id}:{experience_invocation_action_id}",
    )


def stable_actuator_invocation_action_config_id(
    *, actuator_config_id: UUID, experience_invocation_action_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: actuator_config_id, experience_invocation_action_config_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:actuator_invocation_action_config:{actuator_config_id}:{experience_invocation_action_config_id}",
    )


def stable_connector_id(*, connector_config_id: UUID, connector_instance_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: connector_config_id, connector_instance_key"""

    connector_instance_key_norm = (connector_instance_key or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:connector:{connector_config_id}:{connector_instance_key_norm}")


def stable_connector_config_id(*, connector_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: connector_key"""

    connector_key_norm = (connector_key or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:connector_config:{connector_key_norm}")


def stable_connector_provider_id(*, connector_config_id: UUID, provider_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: connector_config_id, provider_key"""

    provider_key_norm = (provider_key or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:connector_provider:{connector_config_id}:{provider_key_norm}")


def stable_connector_session_id(*, connector_provider_id: UUID, connector_id: UUID, session_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: connector_provider_id, connector_id, session_key"""

    session_key_norm = (session_key or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:connector_session:{connector_provider_id}:{connector_id}:{session_key_norm}")


def stable_environment_experience_id(*, fqn_prefix: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: fqn_prefix"""

    fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:environment_experience:{fqn_prefix_norm}")


def stable_environment_experience_actor_config_id(
    *, environment_experience_profile_config_id: UUID, actor_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_experience_profile_config_id, actor_config_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:environment_experience_actor_config:{environment_experience_profile_config_id}:{actor_config_id}",
    )


def stable_environment_experience_event_id(
    *, environment_experience_profile_config_id: UUID, event_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_experience_profile_config_id, event_config_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:environment_experience_event:{environment_experience_profile_config_id}:{event_config_id}",
    )


def stable_environment_experience_event_action_id(
    *, environment_experience_event_id: UUID, action_experience_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_experience_event_id, action_experience_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:environment_experience_event_action:{environment_experience_event_id}:{action_experience_id}",
    )


def stable_environment_experience_event_node_scope_id(
    *,
    environment_experience_event_id: UUID,
    event_config_condition_config_id: UUID,
    projection_experience_node_identity_id: UUID,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_experience_event_id, event_config_condition_config_id, projection_experience_node_identity_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:environment_experience_event_node_scope:{environment_experience_event_id}:{event_config_condition_config_id}:{projection_experience_node_identity_id}",
    )


def stable_environment_experience_process_config_id(
    *, environment_experience_profile_config_id: UUID, process_config_id: UUID, key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_experience_profile_config_id, process_config_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:environment_experience_process_config:{environment_experience_profile_config_id}:{process_config_id}:{key_norm}",
    )


def stable_environment_experience_profile_id(
    *, environment_experience_id: UUID, profile_config_id: UUID, environment_profile_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_experience_id, profile_config_id, environment_profile_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:environment_experience_profile:{environment_experience_id}:{profile_config_id}:{environment_profile_id}",
    )


def stable_environment_experience_profile_config_id(
    *, environment_experience_id: UUID, environment_profile_config_id: UUID, key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_experience_id, environment_profile_config_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:environment_experience_profile_config:{environment_experience_id}:{environment_profile_config_id}:{key_norm}",
    )


def stable_environment_experience_program_id(
    *, environment_experience_thread_config_id: UUID, program_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_experience_thread_config_id, program_config_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:environment_experience_program:{environment_experience_thread_config_id}:{program_config_id}",
    )


def stable_environment_experience_program_apply_id(*, environment_experience_thread_config_id: UUID, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_experience_thread_config_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:environment_experience_program_apply:{environment_experience_thread_config_id}:{key_norm}",
    )


def stable_environment_experience_projection_id(
    *, environment_experience_profile_config_id: UUID, projection_experience_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_experience_profile_config_id, projection_experience_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:environment_experience_projection:{environment_experience_profile_config_id}:{projection_experience_id}",
    )


def stable_environment_experience_thread_config_id(
    *, environment_experience_process_config_id: UUID, thread_config_id: UUID, key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_experience_process_config_id, thread_config_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:environment_experience_thread_config:{environment_experience_process_config_id}:{thread_config_id}:{key_norm}",
    )


def stable_environment_experience_view_event_transition_id(
    *,
    environment_experience_profile_config_id: UUID,
    source_view_id: UUID,
    trigger_event_id: UUID,
    target_section_graph_binding_id: UUID,
    transition_key: str,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_experience_profile_config_id, source_view_id, trigger_event_id, target_section_graph_binding_id, transition_key"""

    transition_key_norm = (transition_key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:environment_experience_view_event_transition:{environment_experience_profile_config_id}:{source_view_id}:{trigger_event_id}:{target_section_graph_binding_id}:{transition_key_norm}",
    )


def stable_environment_topology_process_seed_id(
    *, environment_topology_seed_id: UUID, process_config_id: UUID, process_key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_topology_seed_id, process_config_id, process_key"""

    process_key_norm = (process_key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:environment_topology_process_seed:{environment_topology_seed_id}:{process_config_id}:{process_key_norm}",
    )


def stable_environment_topology_seed_id(
    *, environment_experience_id: UUID, environment_experience_profile_config_id: UUID, key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_experience_id, environment_experience_profile_config_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:environment_topology_seed:{environment_experience_id}:{environment_experience_profile_config_id}:{key_norm}",
    )


def stable_environment_topology_thread_layout_seed_id(
    *, environment_topology_thread_seed_id: UUID, layout_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_topology_thread_seed_id, layout_config_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:environment_topology_thread_layout_seed:{environment_topology_thread_seed_id}:{layout_config_id}",
    )


def stable_environment_topology_thread_seed_id(
    *, environment_topology_process_seed_id: UUID, thread_config_id: UUID, thread_key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_topology_process_seed_id, thread_config_id, thread_key"""

    thread_key_norm = (thread_key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:environment_topology_thread_seed:{environment_topology_process_seed_id}:{thread_config_id}:{thread_key_norm}",
    )


def stable_experience_contract_actor_role_grant_id(
    *, projection_experience_id: UUID, actor_config_role_config_id: UUID, role_config_id: UUID, grant_key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_id, actor_config_role_config_id, role_config_id, grant_key"""

    grant_key_norm = (grant_key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:experience_contract_actor_role_grant:{projection_experience_id}:{actor_config_role_config_id}:{role_config_id}:{grant_key_norm}",
    )


def stable_experience_invocation_action_id(
    *, experience_invocation_action_config_id: UUID, invocation_key: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: experience_invocation_action_config_id, invocation_key"""

    return uuid5(
        NS_EXPERIENCE, f"aware:experience_invocation_action:{experience_invocation_action_config_id}:{invocation_key}"
    )


def stable_experience_invocation_action_commit_id(
    *, experience_invocation_action_id: UUID, object_instance_graph_commit_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: experience_invocation_action_id, object_instance_graph_commit_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:experience_invocation_action_commit:{experience_invocation_action_id}:{object_instance_graph_commit_id}",
    )


def stable_experience_invocation_action_commit_event_id(
    *, experience_invocation_action_commit_id: UUID, event_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: experience_invocation_action_commit_id, event_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:experience_invocation_action_commit_event:{experience_invocation_action_commit_id}:{event_id}",
    )


def stable_experience_invocation_action_config_id(
    *, projection_experience_id: UUID, target_kind: str, entity_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_id, target_kind, entity_id"""

    target_kind_norm = (target_kind or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:experience_invocation_action_config:{projection_experience_id}:{target_kind_norm}:{entity_id}",
    )


def stable_experience_invocation_action_propagation_id(
    *, experience_invocation_action_id: UUID, target_invocation_action_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: experience_invocation_action_id, target_invocation_action_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:experience_invocation_action_propagation:{experience_invocation_action_id}:{target_invocation_action_id}",
    )


def stable_experience_package_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:experience_package:{name_norm}")


def stable_experience_package_api_package_id(*, experience_package_id: UUID, api_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: experience_package_id, api_package_id"""

    return uuid5(NS_EXPERIENCE, f"aware:experience_package_api_package:{experience_package_id}:{api_package_id}")


def stable_experience_package_attention_package_id(*, experience_package_id: UUID, attention_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: experience_package_id, attention_package_id"""

    return uuid5(
        NS_EXPERIENCE, f"aware:experience_package_attention_package:{experience_package_id}:{attention_package_id}"
    )


def stable_experience_package_dependency_id(*, experience_package_id: UUID, target_experience_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: experience_package_id, target_experience_package_id"""

    return uuid5(
        NS_EXPERIENCE, f"aware:experience_package_dependency:{experience_package_id}:{target_experience_package_id}"
    )


def stable_experience_package_language_package_id(*, experience_package_id: UUID, code_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: experience_package_id, code_package_id"""

    return uuid5(NS_EXPERIENCE, f"aware:experience_package_language_package:{experience_package_id}:{code_package_id}")


def stable_experience_package_sdk_package_id(*, experience_package_id: UUID, sdk_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: experience_package_id, sdk_package_id"""

    return uuid5(NS_EXPERIENCE, f"aware:experience_package_sdk_package:{experience_package_id}:{sdk_package_id}")


def stable_experience_provider_id(*, projection_experience_id: UUID, provider_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_id, provider_key"""

    provider_key_norm = (provider_key or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:experience_provider:{projection_experience_id}:{provider_key_norm}")


def stable_experience_provider_action_binding_id(
    *, experience_provider_id: UUID, experience_invocation_action_config_id: UUID, binding_key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: experience_provider_id, experience_invocation_action_config_id, binding_key"""

    binding_key_norm = (binding_key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:experience_provider_action_binding:{experience_provider_id}:{experience_invocation_action_config_id}:{binding_key_norm}",
    )


def stable_experience_session_id(*, environment_experience_id: UUID, identity_session_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_experience_id, identity_session_id"""

    return uuid5(NS_EXPERIENCE, f"aware:experience_session:{environment_experience_id}:{identity_session_id}")


def stable_experience_session_profile_id(*, experience_session_id: UUID, profile_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: experience_session_id, profile_id"""

    return uuid5(NS_EXPERIENCE, f"aware:experience_session_profile:{experience_session_id}:{profile_id}")


def stable_program_id(*, program_impl_id: UUID, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_impl_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:program:{program_impl_id}:{key_norm}")


def stable_program_actor_id(*, program_id: UUID, program_config_actor_config_id: UUID, actor_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_id, program_config_actor_config_id, actor_id"""

    return uuid5(NS_EXPERIENCE, f"aware:program_actor:{program_id}:{program_config_actor_config_id}:{actor_id}")


def stable_program_actor_role_id(
    *, program_actor_id: UUID, actor_role_id: UUID, actor_config_role_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_actor_id, actor_role_id, actor_config_role_config_id"""

    return uuid5(
        NS_EXPERIENCE, f"aware:program_actor_role:{program_actor_id}:{actor_role_id}:{actor_config_role_config_id}"
    )


def stable_program_attribute_id(*, config_id: UUID, attribute_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: config_id, attribute_id"""

    return uuid5(NS_EXPERIENCE, f"aware:program_attribute:{config_id}:{attribute_id}")


def stable_program_branch_id(*, program_id: UUID, object_instance_graph_branch_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_id, object_instance_graph_branch_id"""

    return uuid5(NS_EXPERIENCE, f"aware:program_branch:{program_id}:{object_instance_graph_branch_id}")


def stable_program_config_id(*, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:program_config:{key_norm}")


def stable_program_config_actor_config_id(*, program_config_id: UUID, alias: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_config_id, alias"""

    alias_norm = (alias or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:program_config_actor_config:{program_config_id}:{alias_norm}")


def stable_program_config_attribute_config_id(
    *, program_config_id: UUID, attribute_config_id: UUID, type: str = "input"
) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_config_id, attribute_config_id, type"""

    type_norm = (type or "").casefold().strip() or "input"
    return uuid5(
        NS_EXPERIENCE, f"aware:program_config_attribute_config:{program_config_id}:{attribute_config_id}:{type_norm}"
    )


def stable_program_config_graph_id(*, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:program_config_graph:{key_norm}")


def stable_program_config_graph_object_config_graph_id(
    *, program_config_graph_id: UUID, object_config_graph_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_config_graph_id, object_config_graph_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:program_config_graph_object_config_graph:{program_config_graph_id}:{object_config_graph_id}",
    )


def stable_program_config_graph_program_config_id(*, program_config_graph_id: UUID, program_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_config_graph_id, program_config_id"""

    return uuid5(
        NS_EXPERIENCE, f"aware:program_config_graph_program_config:{program_config_graph_id}:{program_config_id}"
    )


def stable_program_config_graph_program_config_port_projection_experience_node_class_id(
    *,
    program_config_graph_program_config_id: UUID,
    projection_experience_node_class_identity_id: UUID,
    program_config_port_projection_experience_node_id: UUID,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_config_graph_program_config_id, projection_experience_node_class_identity_id, program_config_port_projection_experience_node_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:program_config_graph_program_config_port_projection_experience_node_class:{program_config_graph_program_config_id}:{projection_experience_node_class_identity_id}:{program_config_port_projection_experience_node_id}",
    )


def stable_program_config_graph_projection_experience_oigi_id(
    *, program_config_graph_id: UUID, projection_experience_oigi_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_config_graph_id, projection_experience_oigi_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:program_config_graph_projection_experience_oigi:{program_config_graph_id}:{projection_experience_oigi_id}",
    )


def stable_program_config_input_config_id(*, program_config_id: UUID, name: str, source: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_config_id, name, source"""

    name_norm = (name or "").casefold().strip()
    source_norm = (source or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:program_config_input_config:{program_config_id}:{name_norm}:{source_norm}")


def stable_program_config_input_config_attribute_config_id(
    *, program_config_input_config_id: UUID, attribute_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_config_input_config_id, attribute_config_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:program_config_input_config_attribute_config:{program_config_input_config_id}:{attribute_config_id}",
    )


def stable_program_config_layout_id(*, program_config_id: UUID, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_config_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:program_config_layout:{program_config_id}:{key_norm}")


def stable_program_config_layout_port_section_id(
    *, program_config_layout_id: UUID, program_config_port_id: UUID, layout_section_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_config_layout_id, program_config_port_id, layout_section_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:program_config_layout_port_section:{program_config_layout_id}:{program_config_port_id}:{layout_section_id}",
    )


def stable_program_config_port_id(*, program_config_id: UUID, key: str | None = None) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_config_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:program_config_port:{program_config_id}:{key_norm}")


def stable_program_config_port_projection_experience_node_id(
    *, program_config_port_id: UUID, projection_experience_node_id: UUID, key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_config_port_id, projection_experience_node_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:program_config_port_projection_experience_node:{program_config_port_id}:{projection_experience_node_id}:{key_norm}",
    )


def stable_program_config_port_projection_experience_node_identity_id(
    *, program_config_port_projection_experience_node_id: UUID, projection_experience_node_identity_id: UUID, key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_config_port_projection_experience_node_id, projection_experience_node_identity_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:program_config_port_projection_experience_node_identity:{program_config_port_projection_experience_node_id}:{projection_experience_node_identity_id}:{key_norm}",
    )


def stable_program_impl_id(*, program_config_id: UUID, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_config_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:program_impl:{program_config_id}:{key_norm}")


def stable_program_impl_instruction_id(*, program_impl_id: UUID, sequence: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_impl_id, sequence"""

    return uuid5(NS_EXPERIENCE, f"aware:program_impl_instruction:{program_impl_id}:{sequence}")


def stable_program_impl_instruction_bind_id(*, program_impl_instruction_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_impl_instruction_id"""

    return uuid5(NS_EXPERIENCE, f"aware:program_impl_instruction_bind:{program_impl_instruction_id}")


def stable_program_impl_instruction_expect_id(*, program_impl_instruction_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_impl_instruction_id"""

    return uuid5(NS_EXPERIENCE, f"aware:program_impl_instruction_expect:{program_impl_instruction_id}")


def stable_program_impl_instruction_input_id(
    *, program_impl_instruction_id: UUID, program_config_input_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_impl_instruction_id, program_config_input_config_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:program_impl_instruction_input:{program_impl_instruction_id}:{program_config_input_config_id}",
    )


def stable_program_impl_instruction_intent_id(*, program_impl_instruction_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_impl_instruction_id"""

    return uuid5(NS_EXPERIENCE, f"aware:program_impl_instruction_intent:{program_impl_instruction_id}")


def stable_program_impl_instruction_intent_activation_field_binding_id(
    *,
    program_impl_instruction_intent_id: UUID,
    source_class_config_id: UUID,
    source_attribute_config_id: UUID,
    target_request_attribute_config_id: UUID,
    source_input_key: str,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_impl_instruction_intent_id, source_class_config_id, source_attribute_config_id, target_request_attribute_config_id, source_input_key"""

    source_input_key_norm = (source_input_key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:program_impl_instruction_intent_activation_field_binding:{program_impl_instruction_intent_id}:{source_class_config_id}:{source_attribute_config_id}:{target_request_attribute_config_id}:{source_input_key_norm}",
    )


def stable_program_impl_instruction_intent_outcome_field_binding_id(
    *,
    program_impl_instruction_intent_id: UUID,
    source_program_impl_instruction_intent_id: UUID,
    source_response_attribute_config_id: UUID,
    target_request_attribute_config_id: UUID,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_impl_instruction_intent_id, source_program_impl_instruction_intent_id, source_response_attribute_config_id, target_request_attribute_config_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:program_impl_instruction_intent_outcome_field_binding:{program_impl_instruction_intent_id}:{source_program_impl_instruction_intent_id}:{source_response_attribute_config_id}:{target_request_attribute_config_id}",
    )


def stable_program_impl_instruction_intent_receipt_field_binding_id(
    *,
    program_impl_instruction_intent_id: UUID,
    source_program_impl_instruction_intent_id: UUID,
    source_receipt_class_config_id: UUID,
    source_receipt_attribute_config_id: UUID,
    target_request_attribute_config_id: UUID,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_impl_instruction_intent_id, source_program_impl_instruction_intent_id, source_receipt_class_config_id, source_receipt_attribute_config_id, target_request_attribute_config_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:program_impl_instruction_intent_receipt_field_binding:{program_impl_instruction_intent_id}:{source_program_impl_instruction_intent_id}:{source_receipt_class_config_id}:{source_receipt_attribute_config_id}:{target_request_attribute_config_id}",
    )


def stable_program_impl_instruction_invoke_id(*, program_impl_instruction_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_impl_instruction_id"""

    return uuid5(NS_EXPERIENCE, f"aware:program_impl_instruction_invoke:{program_impl_instruction_id}")


def stable_program_impl_instruction_invoke_attribute_config_id(
    *, program_impl_instruction_invoke_id: UUID, attribute_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_impl_instruction_invoke_id, attribute_config_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:program_impl_instruction_invoke_attribute_config:{program_impl_instruction_invoke_id}:{attribute_config_id}",
    )


def stable_program_impl_instruction_let_id(*, program_impl_instruction_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_impl_instruction_id"""

    return uuid5(NS_EXPERIENCE, f"aware:program_impl_instruction_let:{program_impl_instruction_id}")


def stable_program_input_attribute_id(*, config_id: UUID, attribute_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: config_id, attribute_id"""

    return uuid5(NS_EXPERIENCE, f"aware:program_input_attribute:{config_id}:{attribute_id}")


def stable_program_layout_id(*, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:program_layout:{key_norm}")


def stable_program_layout_section_id(*, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:program_layout_section:{key_norm}")


def stable_program_turn_id(*, program_id: UUID, turn_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_id, turn_id"""

    return uuid5(NS_EXPERIENCE, f"aware:program_turn:{program_id}:{turn_id}")


def stable_program_turn_instruction_id(*, program_turn_id: UUID, program_instruction_id: UUID, sequence: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_turn_id, program_instruction_id, sequence"""

    return uuid5(NS_EXPERIENCE, f"aware:program_turn_instruction:{program_turn_id}:{program_instruction_id}:{sequence}")


def stable_program_turn_instruction_action_id(
    *,
    program_turn_instruction_id: UUID,
    program_impl_instruction_intent_id: UUID,
    action_config_id: UUID,
    event_config_id: UUID,
    intent_key: str,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_turn_instruction_id, program_impl_instruction_intent_id, action_config_id, event_config_id, intent_key"""

    intent_key_norm = (intent_key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:program_turn_instruction_action:{program_turn_instruction_id}:{program_impl_instruction_intent_id}:{action_config_id}:{event_config_id}:{intent_key_norm}",
    )


def stable_program_turn_instruction_bind_id(
    *,
    program_turn_instruction_id: UUID,
    program_impl_instruction_bind_id: UUID,
    object_instance_graph_branch_id: UUID,
    projection_experience_view_id: UUID,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_turn_instruction_id, program_impl_instruction_bind_id, object_instance_graph_branch_id, projection_experience_view_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:program_turn_instruction_bind:{program_turn_instruction_id}:{program_impl_instruction_bind_id}:{object_instance_graph_branch_id}:{projection_experience_view_id}",
    )


def stable_program_turn_instruction_bind_identity_id(
    *,
    program_turn_instruction_bind_id: UUID,
    program_config_port_projection_experience_node_id: UUID,
    projection_experience_node_class_identity_id: UUID,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_turn_instruction_bind_id, program_config_port_projection_experience_node_id, projection_experience_node_class_identity_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:program_turn_instruction_bind_identity:{program_turn_instruction_bind_id}:{program_config_port_projection_experience_node_id}:{projection_experience_node_class_identity_id}",
    )


def stable_program_turn_instruction_decision_id(*, program_turn_instruction_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_turn_instruction_id"""

    return uuid5(NS_EXPERIENCE, f"aware:program_turn_instruction_decision:{program_turn_instruction_id}")


def stable_program_turn_instruction_invoke_id(
    *,
    program_turn_instruction_id: UUID,
    program_impl_instruction_invoke_id: UUID,
    program_actor_role_id: UUID,
    projection_experience_node_class_identity_id: UUID,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_turn_instruction_id, program_impl_instruction_invoke_id, program_actor_role_id, projection_experience_node_class_identity_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:program_turn_instruction_invoke:{program_turn_instruction_id}:{program_impl_instruction_invoke_id}:{program_actor_role_id}:{projection_experience_node_class_identity_id}",
    )


def stable_program_turn_instruction_invoke_attribute_config_id(
    *, program_turn_instruction_invoke_id: UUID, program_impl_instruction_invoke_attribute_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: program_turn_instruction_invoke_id, program_impl_instruction_invoke_attribute_config_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:program_turn_instruction_invoke_attribute_config:{program_turn_instruction_invoke_id}:{program_impl_instruction_invoke_attribute_config_id}",
    )


def stable_projection_experience_id(*, object_projection_graph_identity_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_projection_graph_identity_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:projection_experience:{object_projection_graph_identity_id}:{name_norm}")


def stable_projection_experience_branch_id(*, projection_experience_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:projection_experience_branch:{projection_experience_id}:{name_norm}")


def stable_projection_experience_graph_id(*, projection_experience_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:projection_experience_graph:{projection_experience_id}:{name_norm}")


def stable_projection_experience_graph_identity_id(
    *, projection_experience_graph_id: UUID, projection_experience_node_identity_id: UUID, key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_graph_id, projection_experience_node_identity_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:projection_experience_graph_identity:{projection_experience_graph_id}:{projection_experience_node_identity_id}:{key_norm}",
    )


def stable_projection_experience_graph_identity_edge_id(
    *,
    projection_experience_graph_id: UUID,
    child_projection_experience_graph_identity_id: UUID,
    parent_projection_experience_graph_identity_id: UUID,
    projection_experience_node_identity_edge_id: UUID,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_graph_id, child_projection_experience_graph_identity_id, parent_projection_experience_graph_identity_id, projection_experience_node_identity_edge_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:projection_experience_graph_identity_edge:{projection_experience_graph_id}:{child_projection_experience_graph_identity_id}:{parent_projection_experience_graph_identity_id}:{projection_experience_node_identity_edge_id}",
    )


def stable_projection_experience_graph_identity_profile_id(*, projection_experience_graph_identity_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_graph_identity_id"""

    return uuid5(
        NS_EXPERIENCE, f"aware:projection_experience_graph_identity_profile:{projection_experience_graph_identity_id}"
    )


def stable_projection_experience_graph_identity_profile_exemplar_id(
    *, projection_experience_graph_identity_profile_id: UUID, key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_graph_identity_profile_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:projection_experience_graph_identity_profile_exemplar:{projection_experience_graph_identity_profile_id}:{key_norm}",
    )


def stable_projection_experience_layout_graph_binding_id(
    *, projection_experience_id: UUID, layout_config_id: UUID, binding_key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_id, layout_config_id, binding_key"""

    binding_key_norm = (binding_key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:projection_experience_layout_graph_binding:{projection_experience_id}:{layout_config_id}:{binding_key_norm}",
    )


def stable_projection_experience_layout_section_graph_binding_id(
    *, projection_experience_layout_graph_binding_id: UUID, section_graph_binding_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_layout_graph_binding_id, section_graph_binding_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:projection_experience_layout_section_graph_binding:{projection_experience_layout_graph_binding_id}:{section_graph_binding_id}",
    )


def stable_projection_experience_node_id(
    *, projection_experience_id: UUID, object_projection_graph_node_id: UUID, key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_id, object_projection_graph_node_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:projection_experience_node:{projection_experience_id}:{object_projection_graph_node_id}:{key_norm}",
    )


def stable_projection_experience_node_class_identity_id(
    *,
    projection_experience_oigi_id: UUID,
    projection_experience_node_identity_id: UUID,
    class_instance_identity_id: UUID,
    key: str,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_oigi_id, projection_experience_node_identity_id, class_instance_identity_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:projection_experience_node_class_identity:{projection_experience_oigi_id}:{projection_experience_node_identity_id}:{class_instance_identity_id}:{key_norm}",
    )


def stable_projection_experience_node_class_identity_edge_id(
    *,
    projection_experience_oigi_id: UUID,
    child_node_class_identity_id: UUID,
    parent_node_class_identity_id: UUID,
    class_instance_relationship_identity_id: UUID,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_oigi_id, child_node_class_identity_id, parent_node_class_identity_id, class_instance_relationship_identity_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:projection_experience_node_class_identity_edge:{projection_experience_oigi_id}:{child_node_class_identity_id}:{parent_node_class_identity_id}:{class_instance_relationship_identity_id}",
    )


def stable_projection_experience_node_class_identity_key_binding_id(
    *, projection_experience_node_class_identity_id: UUID, projection_experience_node_key_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_node_class_identity_id, projection_experience_node_key_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:projection_experience_node_class_identity_key_binding:{projection_experience_node_class_identity_id}:{projection_experience_node_key_id}",
    )


def stable_projection_experience_node_identity_id(*, projection_experience_node_id: UUID, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_node_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:projection_experience_node_identity:{projection_experience_node_id}:{key_norm}")


def stable_projection_experience_node_identity_edge_id(
    *,
    projection_experience_graph_id: UUID,
    child_projection_experience_node_identity_id: UUID,
    parent_projection_experience_node_identity_id: UUID,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_graph_id, child_projection_experience_node_identity_id, parent_projection_experience_node_identity_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:projection_experience_node_identity_edge:{projection_experience_graph_id}:{child_projection_experience_node_identity_id}:{parent_projection_experience_node_identity_id}",
    )


def stable_projection_experience_node_key_id(
    *, projection_experience_node_id: UUID, object_projection_graph_node_key_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_node_id, object_projection_graph_node_key_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:projection_experience_node_key:{projection_experience_node_id}:{object_projection_graph_node_key_id}",
    )


def stable_projection_experience_oigi_id(
    *, projection_experience_id: UUID, object_instance_graph_identity_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_id, object_instance_graph_identity_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:projection_experience_oigi:{projection_experience_id}:{object_instance_graph_identity_id}",
    )


def stable_projection_experience_section_id(*, projection_experience_id: UUID, section_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_id, section_id"""

    return uuid5(NS_EXPERIENCE, f"aware:projection_experience_section:{projection_experience_id}:{section_id}")


def stable_projection_experience_section_graph_binding_id(
    *,
    projection_experience_id: UUID,
    layout_config_section_config_id: UUID,
    projection_experience_view_id: UUID,
    projection_experience_graph_identity_id: UUID,
    binding_key: str,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_id, layout_config_section_config_id, projection_experience_view_id, projection_experience_graph_identity_id, binding_key"""

    binding_key_norm = (binding_key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:projection_experience_section_graph_binding:{projection_experience_id}:{layout_config_section_config_id}:{projection_experience_view_id}:{projection_experience_graph_identity_id}:{binding_key_norm}",
    )


def stable_projection_experience_section_view_id(
    *, projection_experience_section_id: UUID, projection_experience_view_instance_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_section_id, projection_experience_view_instance_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:projection_experience_section_view:{projection_experience_section_id}:{projection_experience_view_instance_id}",
    )


def stable_projection_experience_view_id(*, projection_experience_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:projection_experience_view:{projection_experience_id}:{name_norm}")


def stable_projection_experience_view_instance_id(
    *, projection_experience_view_id: UUID, section_graph_binding_id: UUID, view_instance_key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_view_id, section_graph_binding_id, view_instance_key"""

    view_instance_key_norm = (view_instance_key or "").casefold().strip()
    return uuid5(
        NS_EXPERIENCE,
        f"aware:projection_experience_view_instance:{projection_experience_view_id}:{section_graph_binding_id}:{view_instance_key_norm}",
    )


def stable_projection_experience_view_invocation_action_id(
    *, view_invocation_action_config_id: UUID, experience_invocation_action_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: view_invocation_action_config_id, experience_invocation_action_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:projection_experience_view_invocation_action:{view_invocation_action_config_id}:{experience_invocation_action_id}",
    )


def stable_projection_experience_view_invocation_action_config_id(
    *, projection_experience_view_id: UUID, api_view_capability_endpoint_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_view_id, api_view_capability_endpoint_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:projection_experience_view_invocation_action_config:{projection_experience_view_id}:{api_view_capability_endpoint_id}",
    )


def stable_projection_experience_view_state_provider_id(*, projection_experience_view_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_view_id"""

    return uuid5(NS_EXPERIENCE, f"aware:projection_experience_view_state_provider:{projection_experience_view_id}")


def stable_role_config_invocation_action_config_id(
    *, experience_invocation_action_config_id: UUID, role_config_id: UUID, policy_key: str = "invoke"
) -> UUID:
    """Compiler-generated from class-attribute identity keys: experience_invocation_action_config_id, role_config_id, policy_key"""

    policy_key_norm = (policy_key or "").casefold().strip() or "invoke"
    return uuid5(
        NS_EXPERIENCE,
        f"aware:role_config_invocation_action_config:{experience_invocation_action_config_id}:{role_config_id}:{policy_key_norm}",
    )


def stable_sensor_id(*, sensor_config_id: UUID, sensor_instance_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: sensor_config_id, sensor_instance_key"""

    sensor_instance_key_norm = (sensor_instance_key or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:sensor:{sensor_config_id}:{sensor_instance_key_norm}")


def stable_sensor_config_id(*, connector_config_id: UUID, sensor_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: connector_config_id, sensor_key"""

    sensor_key_norm = (sensor_key or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:sensor_config:{connector_config_id}:{sensor_key_norm}")


def stable_sensor_config_state_node_id(*, sensor_config_id: UUID, object_projection_graph_node_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: sensor_config_id, object_projection_graph_node_id"""

    return uuid5(NS_EXPERIENCE, f"aware:sensor_config_state_node:{sensor_config_id}:{object_projection_graph_node_id}")


def stable_sensor_invocation_action_id(
    *, sensor_invocation_action_config_id: UUID, experience_invocation_action_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: sensor_invocation_action_config_id, experience_invocation_action_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:sensor_invocation_action:{sensor_invocation_action_config_id}:{experience_invocation_action_id}",
    )


def stable_sensor_invocation_action_config_id(
    *, sensor_config_id: UUID, experience_invocation_action_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: sensor_config_id, experience_invocation_action_config_id"""

    return uuid5(
        NS_EXPERIENCE,
        f"aware:sensor_invocation_action_config:{sensor_config_id}:{experience_invocation_action_config_id}",
    )


def stable_thread_program_id(*, thread_id: UUID, program_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: thread_id, program_id"""

    return uuid5(NS_EXPERIENCE, f"aware:thread_program:{thread_id}:{program_id}")


def stable_turn_id(*, environment_id: UUID, key: str, target_actor_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_id, key, target_actor_id"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_EXPERIENCE, f"aware:turn:{environment_id}:{key_norm}:{target_actor_id}")


def stable_turn_feedback_id(*, turn_id: UUID, sequence: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: turn_id, sequence"""

    return uuid5(NS_EXPERIENCE, f"aware:turn_feedback:{turn_id}:{sequence}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "0956de29-ed71-5092-9b77-a8be627775c0": (
        "stable_projection_experience_id",
        ("object_projection_graph_identity_id", "name"),
    ),
    "0cb35c4f-eba1-59fb-a20c-32ee27d3cb64": ("stable_program_turn_id", ("program_id", "turn_id")),
    "1073b835-e224-5f1d-8b96-b2d278375464": (
        "stable_environment_experience_actor_config_id",
        ("environment_experience_profile_config_id", "actor_config_id"),
    ),
    "1314d177-a357-510c-b57e-078d4a76c5c3": (
        "stable_program_config_attribute_config_id",
        ("program_config_id", "attribute_config_id", "type"),
    ),
    "144c3f90-9b30-591a-9033-02f5d51e2eaa": ("stable_turn_id", ("environment_id", "key", "target_actor_id")),
    "1a43bbad-601e-5498-a9ff-6db8de277b9a": (
        "stable_environment_experience_projection_id",
        ("environment_experience_profile_config_id", "projection_experience_id"),
    ),
    "1ccf1e19-8acf-5f1f-bb83-bcc587f6c0b0": (
        "stable_actuator_invocation_action_config_id",
        ("actuator_config_id", "experience_invocation_action_config_id"),
    ),
    "1dbd1a9f-e448-515f-bc86-2a6d0c472807": (
        "stable_projection_experience_graph_identity_profile_exemplar_id",
        ("projection_experience_graph_identity_profile_id", "key"),
    ),
    "1df3f42b-b1b3-5da2-ae27-b78848e3331a": ("stable_program_config_port_id", ("program_config_id", "key")),
    "1ea2d20e-7720-5fcc-b1f5-7b65e1b9c09d": (
        "stable_environment_experience_event_action_id",
        ("environment_experience_event_id", "action_experience_id"),
    ),
    "26cbfef5-9121-5738-b34e-ade7b31b8eed": (
        "stable_program_config_graph_program_config_port_projection_experience_node_class_id",
        (
            "program_config_graph_program_config_id",
            "projection_experience_node_class_identity_id",
            "program_config_port_projection_experience_node_id",
        ),
    ),
    "27a9c9a5-e5fa-5d98-8b87-15d0765fc1a4": (
        "stable_action_experience_invocation_request_field_id",
        ("action_experience_invocation_id", "attribute_config_id"),
    ),
    "2e0f924e-7c02-5608-b74b-f9b52689fcaf": (
        "stable_projection_experience_section_graph_binding_id",
        (
            "projection_experience_id",
            "layout_config_section_config_id",
            "projection_experience_view_id",
            "projection_experience_graph_identity_id",
            "binding_key",
        ),
    ),
    "2f9d0788-485b-5ab3-99fa-f1974f03f07b": (
        "stable_projection_experience_graph_identity_id",
        ("projection_experience_graph_id", "projection_experience_node_identity_id", "key"),
    ),
    "30420de5-7d19-5d9f-b05a-a905b2a2670a": (
        "stable_projection_experience_graph_identity_edge_id",
        (
            "projection_experience_graph_id",
            "child_projection_experience_graph_identity_id",
            "parent_projection_experience_graph_identity_id",
            "projection_experience_node_identity_edge_id",
        ),
    ),
    "30e843ac-c577-575c-a382-32db29c4439c": (
        "stable_experience_invocation_action_commit_id",
        ("experience_invocation_action_id", "object_instance_graph_commit_id"),
    ),
    "32cb0462-97e3-5ca0-9c65-1e3116e50c43": ("stable_program_id", ("program_impl_id", "key")),
    "3a5ff034-9cc0-53e3-9968-6027e0944cca": (
        "stable_program_impl_instruction_intent_outcome_field_binding_id",
        (
            "program_impl_instruction_intent_id",
            "source_program_impl_instruction_intent_id",
            "source_response_attribute_config_id",
            "target_request_attribute_config_id",
        ),
    ),
    "3c8b9b1a-1d09-5c79-8b28-7030e5f874bf": (
        "stable_projection_experience_branch_id",
        ("projection_experience_id", "name"),
    ),
    "3f8bf5ca-f718-5441-9a34-1862cade3f18": (
        "stable_experience_package_sdk_package_id",
        ("experience_package_id", "sdk_package_id"),
    ),
    "3fcd133d-6e45-567d-8b5c-19ce370c160c": (
        "stable_projection_experience_node_identity_edge_id",
        (
            "projection_experience_graph_id",
            "child_projection_experience_node_identity_id",
            "parent_projection_experience_node_identity_id",
        ),
    ),
    "42f81410-f217-5374-83b9-4751422db454": (
        "stable_experience_package_attention_package_id",
        ("experience_package_id", "attention_package_id"),
    ),
    "44d064f6-7eea-5303-9426-fb9bd0acb33d": (
        "stable_projection_experience_node_id",
        ("projection_experience_id", "object_projection_graph_node_id", "key"),
    ),
    "45c3d8b0-eab2-56b8-bdff-3edd94294883": (
        "stable_environment_experience_profile_config_id",
        ("environment_experience_id", "environment_profile_config_id", "key"),
    ),
    "45d7a5e2-0fa9-5220-a2b9-484cd0f4c9f8": (
        "stable_experience_package_language_package_id",
        ("experience_package_id", "code_package_id"),
    ),
    "45eb3eb6-df4f-5b55-abab-e947d91b5dac": (
        "stable_experience_package_api_package_id",
        ("experience_package_id", "api_package_id"),
    ),
    "49393e83-333f-5b29-914d-9abe0d8b0f1a": ("stable_actuator_id", ("actuator_config_id", "actuator_instance_key")),
    "49dabb94-3902-5632-8f90-1bb9c05f6383": (
        "stable_projection_experience_oigi_id",
        ("projection_experience_id", "object_instance_graph_identity_id"),
    ),
    "4a3343f0-6c80-53b3-93e4-538af505b4cf": (
        "stable_environment_experience_event_node_scope_id",
        (
            "environment_experience_event_id",
            "event_config_condition_config_id",
            "projection_experience_node_identity_id",
        ),
    ),
    "4b34683d-c10c-5956-b97d-a972f588f07d": (
        "stable_program_turn_instruction_invoke_id",
        (
            "program_turn_instruction_id",
            "program_impl_instruction_invoke_id",
            "program_actor_role_id",
            "projection_experience_node_class_identity_id",
        ),
    ),
    "4b74bddb-922d-5532-b60c-4bd7bf87ad7b": (
        "stable_experience_session_id",
        ("environment_experience_id", "identity_session_id"),
    ),
    "4be3594a-f25e-5cef-877b-9778fbc3c8f4": (
        "stable_environment_experience_process_config_id",
        ("environment_experience_profile_config_id", "process_config_id", "key"),
    ),
    "4f2286fc-d0a5-5692-8733-3fda969fd22f": (
        "stable_projection_experience_view_id",
        ("projection_experience_id", "name"),
    ),
    "505d2867-3148-5355-891d-9dbfbd46ddf4": (
        "stable_program_actor_role_id",
        ("program_actor_id", "actor_role_id", "actor_config_role_config_id"),
    ),
    "50f598f2-2f51-535e-9831-eba1c9e0f0ee": ("stable_turn_feedback_id", ("turn_id", "sequence")),
    "511f8b7d-1454-52b0-9da7-0b853a46743a": (
        "stable_projection_experience_layout_graph_binding_id",
        ("projection_experience_id", "layout_config_id", "binding_key"),
    ),
    "554f5e78-44ee-5418-b97e-fe06ac4a6346": (
        "stable_program_impl_instruction_expect_id",
        ("program_impl_instruction_id",),
    ),
    "560e3d37-5724-5a63-b617-f411a502cfd5": (
        "stable_environment_experience_thread_config_id",
        ("environment_experience_process_config_id", "thread_config_id", "key"),
    ),
    "58f36b51-59d8-5cd2-911d-db6a8f655cb1": (
        "stable_experience_invocation_action_config_id",
        ("projection_experience_id", "target_kind", "entity_id"),
    ),
    "5d40fb03-d15a-546b-8ea7-b73396dc6d84": (
        "stable_program_config_port_projection_experience_node_id",
        ("program_config_port_id", "projection_experience_node_id", "key"),
    ),
    "5dd63812-3102-509f-93fa-3311e6e82ce2": (
        "stable_environment_topology_thread_seed_id",
        ("environment_topology_process_seed_id", "thread_config_id", "thread_key"),
    ),
    "5dffd795-29b6-5673-b2f9-c71701721172": (
        "stable_program_config_port_projection_experience_node_identity_id",
        ("program_config_port_projection_experience_node_id", "projection_experience_node_identity_id", "key"),
    ),
    "62052fc9-d3c4-5216-924c-0632d5452550": (
        "stable_projection_experience_section_view_id",
        ("projection_experience_section_id", "projection_experience_view_instance_id"),
    ),
    "6627a3d7-fc97-5287-99fc-60744d25ee5f": (
        "stable_environment_experience_view_event_transition_id",
        (
            "environment_experience_profile_config_id",
            "source_view_id",
            "trigger_event_id",
            "target_section_graph_binding_id",
            "transition_key",
        ),
    ),
    "668383f1-de52-55f3-b616-1f7599b30f37": (
        "stable_program_actor_id",
        ("program_id", "program_config_actor_config_id", "actor_id"),
    ),
    "6720f9c0-b173-520d-ace3-5cee07daa389": (
        "stable_program_impl_instruction_bind_id",
        ("program_impl_instruction_id",),
    ),
    "6c07c3db-6b44-54ed-9eb4-852bf996a423": ("stable_program_config_id", ("key",)),
    "6c9beeb2-1b7b-58b8-afaa-00d1309983bd": (
        "stable_program_branch_id",
        ("program_id", "object_instance_graph_branch_id"),
    ),
    "70a5dd96-c9ce-5928-8076-03ff9cc55f7c": (
        "stable_actuator_config_state_node_id",
        ("actuator_config_id", "object_projection_graph_node_id"),
    ),
    "70e03bdb-9dad-51e5-8d2f-1d2935ee180b": (
        "stable_sensor_config_state_node_id",
        ("sensor_config_id", "object_projection_graph_node_id"),
    ),
    "7137ed21-89e8-5445-9094-73b2047d4a67": (
        "stable_program_impl_instruction_intent_receipt_field_binding_id",
        (
            "program_impl_instruction_intent_id",
            "source_program_impl_instruction_intent_id",
            "source_receipt_class_config_id",
            "source_receipt_attribute_config_id",
            "target_request_attribute_config_id",
        ),
    ),
    "75dcdeb2-d881-5fb2-8649-d840ed3b5a38": (
        "stable_program_turn_instruction_action_id",
        (
            "program_turn_instruction_id",
            "program_impl_instruction_intent_id",
            "action_config_id",
            "event_config_id",
            "intent_key",
        ),
    ),
    "77c96bb4-285f-5425-86ff-83b3e0dbfeb3": ("stable_actuator_config_id", ("connector_config_id", "actuator_key")),
    "7ab1f768-8c62-521d-b183-8672396ebd01": (
        "stable_projection_experience_view_state_provider_id",
        ("projection_experience_view_id",),
    ),
    "7afcad14-d946-52fc-a807-05eef6ee8c29": (
        "stable_environment_experience_event_id",
        ("environment_experience_profile_config_id", "event_config_id"),
    ),
    "7fd8ad81-14db-58b6-82d0-53fe069b6ab9": ("stable_action_experience_id", ("action_config_id",)),
    "7ff945fc-a992-54df-b4c2-6e99e5625042": (
        "stable_program_impl_instruction_invoke_attribute_config_id",
        ("program_impl_instruction_invoke_id", "attribute_config_id"),
    ),
    "8021108c-8bb7-53d2-b754-1cca400e2bbb": (
        "stable_experience_contract_actor_role_grant_id",
        ("projection_experience_id", "actor_config_role_config_id", "role_config_id", "grant_key"),
    ),
    "81d94713-7292-5540-9e7b-92d49d064d3f": (
        "stable_program_impl_instruction_intent_id",
        ("program_impl_instruction_id",),
    ),
    "8464a138-03ba-5d25-b2e4-975167bd6f51": (
        "stable_program_config_graph_object_config_graph_id",
        ("program_config_graph_id", "object_config_graph_id"),
    ),
    "84cd9128-45fa-5770-af1e-959214689004": (
        "stable_program_impl_instruction_intent_activation_field_binding_id",
        (
            "program_impl_instruction_intent_id",
            "source_class_config_id",
            "source_attribute_config_id",
            "target_request_attribute_config_id",
            "source_input_key",
        ),
    ),
    "8a6bfb48-18e7-50fa-b4a9-7ff6897cbab6": ("stable_sensor_config_id", ("connector_config_id", "sensor_key")),
    "8dc45102-14c9-5c5e-b642-e63b2a740f23": ("stable_sensor_id", ("sensor_config_id", "sensor_instance_key")),
    "95fa2998-3dcd-56d2-a2ce-e1b63e651445": (
        "stable_projection_experience_view_instance_id",
        ("projection_experience_view_id", "section_graph_binding_id", "view_instance_key"),
    ),
    "979e5681-4f17-59d4-92a6-cd020fd1e9b4": ("stable_connector_id", ("connector_config_id", "connector_instance_key")),
    "98bba6b0-7c87-5b4e-b57e-fd1dc6440628": (
        "stable_environment_experience_profile_id",
        ("environment_experience_id", "profile_config_id", "environment_profile_id"),
    ),
    "9ad09d56-8e29-5a8b-95d1-7de40439575b": (
        "stable_program_turn_instruction_bind_id",
        (
            "program_turn_instruction_id",
            "program_impl_instruction_bind_id",
            "object_instance_graph_branch_id",
            "projection_experience_view_id",
        ),
    ),
    "9bac3af5-5343-5d05-9642-e1ab1756a7ff": (
        "stable_connector_session_id",
        ("connector_provider_id", "connector_id", "session_key"),
    ),
    "9be8f01b-d092-5022-becb-3a7141aac8e8": (
        "stable_environment_topology_process_seed_id",
        ("environment_topology_seed_id", "process_config_id", "process_key"),
    ),
    "9dd91452-f2f0-5fa7-ac75-1a92849cd925": ("stable_program_config_layout_id", ("program_config_id", "key")),
    "9e352b0a-8d4d-5369-b288-afdf1c6bebd1": (
        "stable_projection_experience_view_invocation_action_config_id",
        ("projection_experience_view_id", "api_view_capability_endpoint_id"),
    ),
    "9e8812e6-d746-55ab-bdfa-93433db344ca": (
        "stable_experience_session_profile_id",
        ("experience_session_id", "profile_id"),
    ),
    "9f16ad62-8316-5ad6-b8d6-7529b2f9a620": ("stable_experience_package_id", ("name",)),
    "aac904d0-be5d-5972-b931-34cb30a79fbd": ("stable_thread_program_id", ("thread_id", "program_id")),
    "abf535c9-8610-5402-83a5-50ef19ec9f70": (
        "stable_program_impl_instruction_input_id",
        ("program_impl_instruction_id", "program_config_input_config_id"),
    ),
    "b3a35f4b-0df4-50d6-9642-8c0047fe963f": (
        "stable_program_impl_instruction_invoke_id",
        ("program_impl_instruction_id",),
    ),
    "b74875f3-4cad-59c8-ba2c-b840800592bf": (
        "stable_projection_experience_node_identity_id",
        ("projection_experience_node_id", "key"),
    ),
    "bb6f9b4c-d71a-5463-bae6-b5470f66a444": ("stable_program_impl_instruction_id", ("program_impl_id", "sequence")),
    "bc4e905e-4f61-5d4b-a4a1-4c327a298f1d": (
        "stable_program_turn_instruction_bind_identity_id",
        (
            "program_turn_instruction_bind_id",
            "program_config_port_projection_experience_node_id",
            "projection_experience_node_class_identity_id",
        ),
    ),
    "c06bce47-f719-500c-b6c7-e98a4e3d01f5": (
        "stable_sensor_invocation_action_config_id",
        ("sensor_config_id", "experience_invocation_action_config_id"),
    ),
    "c668a9c0-864d-5c4e-a20f-d5d523553ea5": (
        "stable_program_turn_instruction_id",
        ("program_turn_id", "program_instruction_id", "sequence"),
    ),
    "c80fc42c-925a-5902-a311-396b24bfcb72": (
        "stable_environment_experience_program_apply_id",
        ("environment_experience_thread_config_id", "key"),
    ),
    "c82d2f6b-25d7-5992-91c7-f5fd1046b815": ("stable_connector_provider_id", ("connector_config_id", "provider_key")),
    "c99d5620-8bda-5fc4-9ee4-41fd8f613f3e": (
        "stable_experience_invocation_action_id",
        ("experience_invocation_action_config_id", "invocation_key"),
    ),
    "cb6ccf2a-ff4b-512e-a1d0-7df94d15ac80": ("stable_program_impl_id", ("program_config_id", "key")),
    "cc6d00a8-73f0-53e1-9ed2-bf0e233adb12": (
        "stable_projection_experience_layout_section_graph_binding_id",
        ("projection_experience_layout_graph_binding_id", "section_graph_binding_id"),
    ),
    "ce77e182-eeae-51cd-a64c-a4a9a00ebe05": (
        "stable_projection_experience_graph_identity_profile_id",
        ("projection_experience_graph_identity_id",),
    ),
    "d03bd277-09fa-5555-8ebb-aa7b30f1f428": (
        "stable_program_config_layout_port_section_id",
        ("program_config_layout_id", "program_config_port_id", "layout_section_id"),
    ),
    "d0ff7a15-5372-5199-a98c-52f4516400de": (
        "stable_program_turn_instruction_invoke_attribute_config_id",
        ("program_turn_instruction_invoke_id", "program_impl_instruction_invoke_attribute_config_id"),
    ),
    "d290496b-508a-584c-9ccb-60547cb08b9b": (
        "stable_experience_invocation_action_commit_event_id",
        ("experience_invocation_action_commit_id", "event_id"),
    ),
    "d351be81-dd60-5448-b086-c35edb85ccf5": (
        "stable_projection_experience_node_class_identity_edge_id",
        (
            "projection_experience_oigi_id",
            "child_node_class_identity_id",
            "parent_node_class_identity_id",
            "class_instance_relationship_identity_id",
        ),
    ),
    "d473973b-1659-5116-a213-f89cf1bf0edb": (
        "stable_experience_provider_action_binding_id",
        ("experience_provider_id", "experience_invocation_action_config_id", "binding_key"),
    ),
    "d4f12eff-42ea-5a7c-b6ee-44e76a9ca394": (
        "stable_program_impl_instruction_let_id",
        ("program_impl_instruction_id",),
    ),
    "d86c87f1-17ac-5ba0-94a7-f98ea64c5738": (
        "stable_role_config_invocation_action_config_id",
        ("experience_invocation_action_config_id", "role_config_id", "policy_key"),
    ),
    "d8d98f95-a157-5e94-9ad3-8066406c7906": (
        "stable_projection_experience_node_class_identity_id",
        (
            "projection_experience_oigi_id",
            "projection_experience_node_identity_id",
            "class_instance_identity_id",
            "key",
        ),
    ),
    "da390689-107c-5282-8664-f31f965e42a1": (
        "stable_projection_experience_node_key_id",
        ("projection_experience_node_id", "object_projection_graph_node_key_id"),
    ),
    "de8c344a-014e-5fcd-a0e4-489f5fe9808d": (
        "stable_environment_experience_program_id",
        ("environment_experience_thread_config_id", "program_config_id"),
    ),
    "e28d64f5-be4f-5082-8855-4c9b53847c36": (
        "stable_program_config_graph_program_config_id",
        ("program_config_graph_id", "program_config_id"),
    ),
    "e30d9203-8dd0-5a08-851a-0b1fbebe6cb0": ("stable_environment_experience_id", ("fqn_prefix",)),
    "e3cc6858-9bff-56ac-8cc2-5e0032bd8dc5": (
        "stable_projection_experience_graph_id",
        ("projection_experience_id", "name"),
    ),
    "e5811a3b-5c1b-54ca-aadc-94095f2a113c": (
        "stable_action_experience_invocation_action_id",
        ("action_experience_invocation_id", "experience_invocation_action_id"),
    ),
    "e6500325-bbc5-57ed-acd3-8404bd5a9d96": ("stable_program_config_actor_config_id", ("program_config_id", "alias")),
    "e9a24b0f-849d-5e62-a79f-b4c713ee7da2": (
        "stable_environment_topology_thread_layout_seed_id",
        ("environment_topology_thread_seed_id", "layout_config_id"),
    ),
    "eb1f1022-8f20-5012-8d52-56915d5a19e0": (
        "stable_program_config_input_config_id",
        ("program_config_id", "name", "source"),
    ),
    "ec1c70ae-83f8-51cd-ae77-9f92b57d84a0": (
        "stable_projection_experience_node_class_identity_key_binding_id",
        ("projection_experience_node_class_identity_id", "projection_experience_node_key_id"),
    ),
    "ec9cd507-d220-522c-b5e7-9ece37449b79": (
        "stable_program_config_input_config_attribute_config_id",
        ("program_config_input_config_id", "attribute_config_id"),
    ),
    "f1078e0e-809c-5d9d-bfde-6114a9cea1b0": (
        "stable_program_turn_instruction_decision_id",
        ("program_turn_instruction_id",),
    ),
    "f18ff342-80af-52dc-a9b3-104a18027ec8": (
        "stable_action_experience_invocation_id",
        ("action_experience_id", "experience_invocation_action_config_id"),
    ),
    "f419ee08-ec4d-5ab2-9174-ff4a53b4048c": ("stable_connector_config_id", ("connector_key",)),
    "f7699132-21f3-520e-8922-de33a6604d97": (
        "stable_experience_package_dependency_id",
        ("experience_package_id", "target_experience_package_id"),
    ),
    "f8d0b3e1-30e3-5721-b170-3af20d4cdc36": ("stable_program_config_graph_id", ("key",)),
    "f916170a-52b4-5c6b-8301-01a84c0c8eca": (
        "stable_experience_invocation_action_propagation_id",
        ("experience_invocation_action_id", "target_invocation_action_id"),
    ),
    "fa3657db-e65f-597e-8a8c-119166c6c423": (
        "stable_environment_topology_seed_id",
        ("environment_experience_id", "environment_experience_profile_config_id", "key"),
    ),
    "fbd925de-dda4-5c3e-bb7f-3e8d5bdea4c5": (
        "stable_program_config_graph_projection_experience_oigi_id",
        ("program_config_graph_id", "projection_experience_oigi_id"),
    ),
    "fd9ca2cc-f343-59d8-8740-c442044c3a12": (
        "stable_experience_provider_id",
        ("projection_experience_id", "provider_key"),
    ),
    "fe79eb06-9a92-58f8-a20d-86e78727b127": (
        "stable_action_experience_program_id",
        ("action_experience_id", "program_config_id"),
    ),
    "ff3ea221-91fc-5478-a853-5893f39c745b": (
        "stable_projection_experience_section_id",
        ("projection_experience_id", "section_id"),
    ),
}

__all__ = [
    "stable_action_experience_id",
    "stable_action_experience_invocation_id",
    "stable_action_experience_invocation_action_id",
    "stable_action_experience_invocation_request_field_id",
    "stable_action_experience_program_id",
    "stable_actuator_id",
    "stable_actuator_config_id",
    "stable_actuator_config_state_node_id",
    "stable_actuator_invocation_action_id",
    "stable_actuator_invocation_action_config_id",
    "stable_connector_id",
    "stable_connector_config_id",
    "stable_connector_provider_id",
    "stable_connector_session_id",
    "stable_environment_experience_id",
    "stable_environment_experience_actor_config_id",
    "stable_environment_experience_event_id",
    "stable_environment_experience_event_action_id",
    "stable_environment_experience_event_node_scope_id",
    "stable_environment_experience_process_config_id",
    "stable_environment_experience_profile_id",
    "stable_environment_experience_profile_config_id",
    "stable_environment_experience_program_id",
    "stable_environment_experience_program_apply_id",
    "stable_environment_experience_projection_id",
    "stable_environment_experience_thread_config_id",
    "stable_environment_experience_view_event_transition_id",
    "stable_environment_topology_process_seed_id",
    "stable_environment_topology_seed_id",
    "stable_environment_topology_thread_layout_seed_id",
    "stable_environment_topology_thread_seed_id",
    "stable_experience_contract_actor_role_grant_id",
    "stable_experience_invocation_action_id",
    "stable_experience_invocation_action_commit_id",
    "stable_experience_invocation_action_commit_event_id",
    "stable_experience_invocation_action_config_id",
    "stable_experience_invocation_action_propagation_id",
    "stable_experience_package_id",
    "stable_experience_package_api_package_id",
    "stable_experience_package_attention_package_id",
    "stable_experience_package_dependency_id",
    "stable_experience_package_language_package_id",
    "stable_experience_package_sdk_package_id",
    "stable_experience_provider_id",
    "stable_experience_provider_action_binding_id",
    "stable_experience_session_id",
    "stable_experience_session_profile_id",
    "stable_program_id",
    "stable_program_actor_id",
    "stable_program_actor_role_id",
    "stable_program_attribute_id",
    "stable_program_branch_id",
    "stable_program_config_id",
    "stable_program_config_actor_config_id",
    "stable_program_config_attribute_config_id",
    "stable_program_config_graph_id",
    "stable_program_config_graph_object_config_graph_id",
    "stable_program_config_graph_program_config_id",
    "stable_program_config_graph_program_config_port_projection_experience_node_class_id",
    "stable_program_config_graph_projection_experience_oigi_id",
    "stable_program_config_input_config_id",
    "stable_program_config_input_config_attribute_config_id",
    "stable_program_config_layout_id",
    "stable_program_config_layout_port_section_id",
    "stable_program_config_port_id",
    "stable_program_config_port_projection_experience_node_id",
    "stable_program_config_port_projection_experience_node_identity_id",
    "stable_program_impl_id",
    "stable_program_impl_instruction_id",
    "stable_program_impl_instruction_bind_id",
    "stable_program_impl_instruction_expect_id",
    "stable_program_impl_instruction_input_id",
    "stable_program_impl_instruction_intent_id",
    "stable_program_impl_instruction_intent_activation_field_binding_id",
    "stable_program_impl_instruction_intent_outcome_field_binding_id",
    "stable_program_impl_instruction_intent_receipt_field_binding_id",
    "stable_program_impl_instruction_invoke_id",
    "stable_program_impl_instruction_invoke_attribute_config_id",
    "stable_program_impl_instruction_let_id",
    "stable_program_input_attribute_id",
    "stable_program_layout_id",
    "stable_program_layout_section_id",
    "stable_program_turn_id",
    "stable_program_turn_instruction_id",
    "stable_program_turn_instruction_action_id",
    "stable_program_turn_instruction_bind_id",
    "stable_program_turn_instruction_bind_identity_id",
    "stable_program_turn_instruction_decision_id",
    "stable_program_turn_instruction_invoke_id",
    "stable_program_turn_instruction_invoke_attribute_config_id",
    "stable_projection_experience_id",
    "stable_projection_experience_branch_id",
    "stable_projection_experience_graph_id",
    "stable_projection_experience_graph_identity_id",
    "stable_projection_experience_graph_identity_edge_id",
    "stable_projection_experience_graph_identity_profile_id",
    "stable_projection_experience_graph_identity_profile_exemplar_id",
    "stable_projection_experience_layout_graph_binding_id",
    "stable_projection_experience_layout_section_graph_binding_id",
    "stable_projection_experience_node_id",
    "stable_projection_experience_node_class_identity_id",
    "stable_projection_experience_node_class_identity_edge_id",
    "stable_projection_experience_node_class_identity_key_binding_id",
    "stable_projection_experience_node_identity_id",
    "stable_projection_experience_node_identity_edge_id",
    "stable_projection_experience_node_key_id",
    "stable_projection_experience_oigi_id",
    "stable_projection_experience_section_id",
    "stable_projection_experience_section_graph_binding_id",
    "stable_projection_experience_section_view_id",
    "stable_projection_experience_view_id",
    "stable_projection_experience_view_instance_id",
    "stable_projection_experience_view_invocation_action_id",
    "stable_projection_experience_view_invocation_action_config_id",
    "stable_projection_experience_view_state_provider_id",
    "stable_role_config_invocation_action_config_id",
    "stable_sensor_id",
    "stable_sensor_config_id",
    "stable_sensor_config_state_node_id",
    "stable_sensor_invocation_action_id",
    "stable_sensor_invocation_action_config_id",
    "stable_thread_program_id",
    "stable_turn_id",
    "stable_turn_feedback_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
