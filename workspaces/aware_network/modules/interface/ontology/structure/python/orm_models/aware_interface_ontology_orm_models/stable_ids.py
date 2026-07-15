# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_INTERFACE = uuid5(NAMESPACE_URL, "aware://interface/v1")


def stable_app_config_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:app_config:{name_norm}")


def stable_app_config_screen_config_id(
    *,
    app_config_id: UUID,
    projection_experience_id: UUID,
    projection_experience_layout_graph_binding_id: UUID,
    screen_key: str,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: app_config_id, projection_experience_id, projection_experience_layout_graph_binding_id, screen_key"""

    screen_key_norm = (screen_key or "").casefold().strip()
    return uuid5(
        NS_INTERFACE,
        f"aware:app_config_screen_config:{app_config_id}:{projection_experience_id}:{projection_experience_layout_graph_binding_id}:{screen_key_norm}",
    )


def stable_app_package_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:app_package:{name_norm}")


def stable_app_package_experience_package_id(*, app_package_id: UUID, experience_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: app_package_id, experience_package_id"""

    return uuid5(NS_INTERFACE, f"aware:app_package_experience_package:{app_package_id}:{experience_package_id}")


def stable_app_package_interface_package_id(*, app_package_id: UUID, interface_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: app_package_id, interface_package_id"""

    return uuid5(NS_INTERFACE, f"aware:app_package_interface_package:{app_package_id}:{interface_package_id}")


def stable_interface_id(*, interface_config_id: UUID, os: str, version: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: interface_config_id, os, version"""

    os_norm = (os or "").casefold().strip()
    version_norm = (version or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:interface:{interface_config_id}:{os_norm}:{version_norm}")


def stable_interface_config_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:interface_config:{name_norm}")


def stable_interface_config_pane_config_id(*, interface_config_id: UUID, pane_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: interface_config_id, pane_config_id"""

    return uuid5(NS_INTERFACE, f"aware:interface_config_pane_config:{interface_config_id}:{pane_config_id}")


def stable_interface_config_pane_config_section_config_id(
    *, interface_config_pane_config_id: UUID, layout_config_section_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: interface_config_pane_config_id, layout_config_section_config_id"""

    return uuid5(
        NS_INTERFACE,
        f"aware:interface_config_pane_config_section_config:{interface_config_pane_config_id}:{layout_config_section_config_id}",
    )


def stable_interface_config_window_config_id(*, interface_config_id: UUID, window_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: interface_config_id, window_config_id"""

    return uuid5(NS_INTERFACE, f"aware:interface_config_window_config:{interface_config_id}:{window_config_id}")


def stable_interface_environment_id(*, interface_id: UUID, environment_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: interface_id, environment_id"""

    return uuid5(NS_INTERFACE, f"aware:interface_environment:{interface_id}:{environment_id}")


def stable_interface_identity_id(*, identity_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: identity_id"""

    return uuid5(NS_INTERFACE, f"aware:interface_identity:{identity_id}")


def stable_interface_identity_network_node_id(*, network_node_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: network_node_id"""

    return uuid5(NS_INTERFACE, f"aware:interface_identity_network_node:{network_node_id}")


def stable_interface_package_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:interface_package:{name_norm}")


def stable_interface_package_experience_package_id(*, interface_package_id: UUID, experience_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: interface_package_id, experience_package_id"""

    return uuid5(
        NS_INTERFACE, f"aware:interface_package_experience_package:{interface_package_id}:{experience_package_id}"
    )


def stable_interface_package_pane_package_id(*, interface_package_id: UUID, pane_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: interface_package_id, pane_package_id"""

    return uuid5(NS_INTERFACE, f"aware:interface_package_pane_package:{interface_package_id}:{pane_package_id}")


def stable_interface_package_render_component_package_id(
    *, interface_package_id: UUID, render_component_package_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: interface_package_id, render_component_package_id"""

    return uuid5(
        NS_INTERFACE,
        f"aware:interface_package_render_component_package:{interface_package_id}:{render_component_package_id}",
    )


def stable_interface_session_id(*, interface_id: UUID, identity_session_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: interface_id, identity_session_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:interface_session:{interface_id}:{identity_session_id}:{name_norm}")


def stable_interface_session_experience_session_id(*, interface_session_id: UUID, experience_session_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: interface_session_id, experience_session_id"""

    return uuid5(
        NS_INTERFACE, f"aware:interface_session_experience_session:{interface_session_id}:{experience_session_id}"
    )


def stable_interface_window_id(*, interface_id: UUID, window_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: interface_id, window_id"""

    return uuid5(NS_INTERFACE, f"aware:interface_window:{interface_id}:{window_id}")


def stable_interface_window_navigation_context_id(
    *, interface_window_id: UUID, interface_environment_id: UUID, environment_navigation_context_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: interface_window_id, interface_environment_id, environment_navigation_context_id"""

    return uuid5(
        NS_INTERFACE,
        f"aware:interface_window_navigation_context:{interface_window_id}:{interface_environment_id}:{environment_navigation_context_id}",
    )


def stable_pane_action_binding_id(*, pane_render_node_id: UUID, binding_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: pane_render_node_id, binding_key"""

    binding_key_norm = (binding_key or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:pane_action_binding:{pane_render_node_id}:{binding_key_norm}")


def stable_pane_config_id(*, projection_experience_view_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: projection_experience_view_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:pane_config:{projection_experience_view_id}:{name_norm}")


def stable_pane_input_binding_id(*, pane_action_binding_id: UUID, payload_path: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: pane_action_binding_id, payload_path"""

    payload_path_norm = (payload_path or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:pane_input_binding:{pane_action_binding_id}:{payload_path_norm}")


def stable_pane_package_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:pane_package:{name_norm}")


def stable_pane_package_experience_package_id(*, pane_package_id: UUID, experience_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: pane_package_id, experience_package_id"""

    return uuid5(NS_INTERFACE, f"aware:pane_package_experience_package:{pane_package_id}:{experience_package_id}")


def stable_pane_package_render_component_package_id(
    *, pane_package_id: UUID, render_component_package_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: pane_package_id, render_component_package_id"""

    return uuid5(
        NS_INTERFACE, f"aware:pane_package_render_component_package:{pane_package_id}:{render_component_package_id}"
    )


def stable_pane_renderer_capability_requirement_id(
    *, pane_render_spec_id: UUID, capability_kind: str, capability_key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: pane_render_spec_id, capability_kind, capability_key"""

    capability_kind_norm = (capability_kind or "").casefold().strip()
    capability_key_norm = (capability_key or "").casefold().strip()
    return uuid5(
        NS_INTERFACE,
        f"aware:pane_renderer_capability_requirement:{pane_render_spec_id}:{capability_kind_norm}:{capability_key_norm}",
    )


def stable_pane_render_node_id(*, pane_render_spec_id: UUID, node_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: pane_render_spec_id, node_key"""

    node_key_norm = (node_key or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:pane_render_node:{pane_render_spec_id}:{node_key_norm}")


def stable_pane_render_spec_id(*, pane_config_id: UUID, name: str, spec_version: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: pane_config_id, name, spec_version"""

    name_norm = (name or "").casefold().strip()
    spec_version_norm = (spec_version or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:pane_render_spec:{pane_config_id}:{name_norm}:{spec_version_norm}")


def stable_pane_state_binding_id(*, pane_render_node_id: UUID, binding_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: pane_render_node_id, binding_key"""

    binding_key_norm = (binding_key or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:pane_state_binding:{pane_render_node_id}:{binding_key_norm}")


def stable_pane_style_token_ref_id(*, pane_render_node_id: UUID, token_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: pane_render_node_id, token_key"""

    token_key_norm = (token_key or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:pane_style_token_ref:{pane_render_node_id}:{token_key_norm}")


def stable_render_component_action_port_id(*, render_component_contract_id: UUID, port_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: render_component_contract_id, port_key"""

    port_key_norm = (port_key or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:render_component_action_port:{render_component_contract_id}:{port_key_norm}")


def stable_render_component_capability_id(
    *, render_component_contract_id: UUID, capability_kind: str, capability_key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: render_component_contract_id, capability_kind, capability_key"""

    capability_kind_norm = (capability_kind or "").casefold().strip()
    capability_key_norm = (capability_key or "").casefold().strip()
    return uuid5(
        NS_INTERFACE,
        f"aware:render_component_capability:{render_component_contract_id}:{capability_kind_norm}:{capability_key_norm}",
    )


def stable_render_component_config_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:render_component_config:{name_norm}")


def stable_render_component_contract_id(*, render_component_config_id: UUID, component_ref: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: render_component_config_id, component_ref"""

    component_ref_norm = (component_ref or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:render_component_contract:{render_component_config_id}:{component_ref_norm}")


def stable_render_component_fallback_policy_id(*, render_component_contract_id: UUID, policy_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: render_component_contract_id, policy_key"""

    policy_key_norm = (policy_key or "").casefold().strip()
    return uuid5(
        NS_INTERFACE, f"aware:render_component_fallback_policy:{render_component_contract_id}:{policy_key_norm}"
    )


def stable_render_component_input_port_id(*, render_component_contract_id: UUID, port_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: render_component_contract_id, port_key"""

    port_key_norm = (port_key or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:render_component_input_port:{render_component_contract_id}:{port_key_norm}")


def stable_render_component_package_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:render_component_package:{name_norm}")


def stable_window_id(*, window_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: window_id"""

    return uuid5(NS_INTERFACE, f"aware:window:{window_id}")


def stable_window_config_id(*, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_INTERFACE, f"aware:window_config:{key_norm}")


def stable_window_config_layout_config_id(*, window_config_id: UUID, layout_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: window_config_id, layout_config_id"""

    return uuid5(NS_INTERFACE, f"aware:window_config_layout_config:{window_config_id}:{layout_config_id}")


def stable_window_layout_id(*, window_id: UUID, layout_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: window_id, layout_id"""

    return uuid5(NS_INTERFACE, f"aware:window_layout:{window_id}:{layout_id}")


def stable_window_layout_section_id(*, window_layout_id: UUID, layout_section_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: window_layout_id, layout_section_id"""

    return uuid5(NS_INTERFACE, f"aware:window_layout_section:{window_layout_id}:{layout_section_id}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "0fc639ed-8f86-538d-aec8-ee029970ab0f": (
        "stable_render_component_fallback_policy_id",
        ("render_component_contract_id", "policy_key"),
    ),
    "180f921d-3941-5d32-b0e4-f2cccaec3d16": (
        "stable_interface_package_render_component_package_id",
        ("interface_package_id", "render_component_package_id"),
    ),
    "20715012-ed7f-596a-b488-d4784ff064b1": ("stable_app_package_id", ("name",)),
    "2d1f290b-d657-5d7b-aa24-05ef5660521a": (
        "stable_render_component_contract_id",
        ("render_component_config_id", "component_ref"),
    ),
    "3417ec25-2c24-59cb-bce3-d4a274d98773": (
        "stable_window_config_layout_config_id",
        ("window_config_id", "layout_config_id"),
    ),
    "4161ddac-e0e3-5292-bd7f-18299a47fd00": (
        "stable_interface_config_pane_config_id",
        ("interface_config_id", "pane_config_id"),
    ),
    "4b640535-8b2d-53a8-b69f-4a65a1a0a00f": (
        "stable_interface_window_navigation_context_id",
        ("interface_window_id", "interface_environment_id", "environment_navigation_context_id"),
    ),
    "5337b1b9-323c-5bbe-8d67-d85e9125b704": ("stable_interface_package_id", ("name",)),
    "54afba52-5cac-54c1-b639-303f70baa672": ("stable_interface_config_id", ("name",)),
    "55f63ce9-eb32-5b62-a285-b4828fb7cf3f": ("stable_pane_render_node_id", ("pane_render_spec_id", "node_key")),
    "569e3f31-bc7a-5c5f-8869-5b33374ad092": ("stable_pane_state_binding_id", ("pane_render_node_id", "binding_key")),
    "5dad0929-125d-5238-9906-35ab07a4d110": (
        "stable_interface_config_pane_config_section_config_id",
        ("interface_config_pane_config_id", "layout_config_section_config_id"),
    ),
    "5f25f95e-6420-5a1c-b9ce-ae0db3d28777": (
        "stable_render_component_action_port_id",
        ("render_component_contract_id", "port_key"),
    ),
    "5fb488c5-ad21-5a5a-a7b4-699cc1c200de": (
        "stable_interface_package_pane_package_id",
        ("interface_package_id", "pane_package_id"),
    ),
    "61ad5916-6124-5a34-a5f6-4d30279bb8c3": (
        "stable_app_package_experience_package_id",
        ("app_package_id", "experience_package_id"),
    ),
    "645e6ffd-c455-5943-a084-9113e0ad3281": ("stable_pane_render_spec_id", ("pane_config_id", "name", "spec_version")),
    "7ae9ab4e-d4fc-5086-bf0e-b2eb1a61ba1d": ("stable_interface_environment_id", ("interface_id", "environment_id")),
    "7ce7495a-fbb9-5237-8956-b4356893807f": (
        "stable_interface_session_id",
        ("interface_id", "identity_session_id", "name"),
    ),
    "7e7a3bab-5e84-5156-9390-a6ab4e17f9d2": (
        "stable_interface_session_experience_session_id",
        ("interface_session_id", "experience_session_id"),
    ),
    "886f47ba-457d-5619-81b4-4b9c96d69551": (
        "stable_app_config_screen_config_id",
        ("app_config_id", "projection_experience_id", "projection_experience_layout_graph_binding_id", "screen_key"),
    ),
    "949e3a3a-90b4-58d9-bdb0-391df69d4e2d": ("stable_interface_id", ("interface_config_id", "os", "version")),
    "954b4ef3-b9f8-5559-9ae5-d5c1fb72b046": ("stable_pane_config_id", ("projection_experience_view_id", "name")),
    "99fba59a-366a-53c2-abf8-3455899acd8c": ("stable_render_component_config_id", ("name",)),
    "9eecc52d-4c79-5462-957d-24ef8107ddf3": (
        "stable_interface_config_window_config_id",
        ("interface_config_id", "window_config_id"),
    ),
    "a22242cf-0cec-5478-93d7-e715c3ca3dff": (
        "stable_window_layout_section_id",
        ("window_layout_id", "layout_section_id"),
    ),
    "a70c88cd-2094-5368-a372-2e8fadfa3358": ("stable_interface_window_id", ("interface_id", "window_id")),
    "aebfb798-5e4b-53a5-a54f-c5d9c68042aa": ("stable_render_component_package_id", ("name",)),
    "b6f9b318-08f2-56a3-9d33-b3985bf86a3b": (
        "stable_pane_package_experience_package_id",
        ("pane_package_id", "experience_package_id"),
    ),
    "bd434068-b848-5898-b8cf-ed309b4589c0": ("stable_app_config_id", ("name",)),
    "c2d210a7-f0af-58ed-8505-a120f92a72e1": (
        "stable_pane_input_binding_id",
        ("pane_action_binding_id", "payload_path"),
    ),
    "cbbb0090-3dc4-51a3-a324-cb817b25af51": (
        "stable_render_component_input_port_id",
        ("render_component_contract_id", "port_key"),
    ),
    "cca073a7-a010-549b-b3ba-e441c484b9f7": ("stable_window_id", ("window_id",)),
    "cec168d6-facd-5fd4-97a2-92f5fb55360a": (
        "stable_interface_package_experience_package_id",
        ("interface_package_id", "experience_package_id"),
    ),
    "d6e91aeb-8b86-56bf-8863-0a8639f2b7f5": (
        "stable_pane_package_render_component_package_id",
        ("pane_package_id", "render_component_package_id"),
    ),
    "d7308895-3a4f-52ab-accf-7232f36754db": ("stable_pane_action_binding_id", ("pane_render_node_id", "binding_key")),
    "d74fc5a3-b3c3-5852-a241-73c38c661172": (
        "stable_pane_renderer_capability_requirement_id",
        ("pane_render_spec_id", "capability_kind", "capability_key"),
    ),
    "ddcc6a6a-1cd1-5206-a37b-394f1d150020": ("stable_pane_style_token_ref_id", ("pane_render_node_id", "token_key")),
    "e6ca4a78-3e8e-5b8c-8732-ca1f36d9728e": (
        "stable_render_component_capability_id",
        ("render_component_contract_id", "capability_kind", "capability_key"),
    ),
    "e8675cef-df1a-5a18-85f0-9fb7b9ebc25f": ("stable_window_layout_id", ("window_id", "layout_id")),
    "eb6a128c-7405-5986-a142-4f1840a21b57": (
        "stable_app_package_interface_package_id",
        ("app_package_id", "interface_package_id"),
    ),
    "efeb1c58-fee3-5de5-a652-c1a4a64f6bd8": ("stable_pane_package_id", ("name",)),
    "f1b126f2-259d-50bf-84b0-480f9187f13b": ("stable_window_config_id", ("key",)),
}

__all__ = [
    "stable_app_config_id",
    "stable_app_config_screen_config_id",
    "stable_app_package_id",
    "stable_app_package_experience_package_id",
    "stable_app_package_interface_package_id",
    "stable_interface_id",
    "stable_interface_config_id",
    "stable_interface_config_pane_config_id",
    "stable_interface_config_pane_config_section_config_id",
    "stable_interface_config_window_config_id",
    "stable_interface_environment_id",
    "stable_interface_identity_id",
    "stable_interface_identity_network_node_id",
    "stable_interface_package_id",
    "stable_interface_package_experience_package_id",
    "stable_interface_package_pane_package_id",
    "stable_interface_package_render_component_package_id",
    "stable_interface_session_id",
    "stable_interface_session_experience_session_id",
    "stable_interface_window_id",
    "stable_interface_window_navigation_context_id",
    "stable_pane_action_binding_id",
    "stable_pane_config_id",
    "stable_pane_input_binding_id",
    "stable_pane_package_id",
    "stable_pane_package_experience_package_id",
    "stable_pane_package_render_component_package_id",
    "stable_pane_renderer_capability_requirement_id",
    "stable_pane_render_node_id",
    "stable_pane_render_spec_id",
    "stable_pane_state_binding_id",
    "stable_pane_style_token_ref_id",
    "stable_render_component_action_port_id",
    "stable_render_component_capability_id",
    "stable_render_component_config_id",
    "stable_render_component_contract_id",
    "stable_render_component_fallback_policy_id",
    "stable_render_component_input_port_id",
    "stable_render_component_package_id",
    "stable_window_id",
    "stable_window_config_id",
    "stable_window_config_layout_config_id",
    "stable_window_layout_id",
    "stable_window_layout_section_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
