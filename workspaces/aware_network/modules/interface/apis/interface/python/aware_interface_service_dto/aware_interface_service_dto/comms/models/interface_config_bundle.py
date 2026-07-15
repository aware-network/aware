from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class InterfaceConfigApiBundle(BaseModel):
    """
    Canonical bundle-facing Interface config DTOs.
    These types are transport-neutral read/write contracts for authored or
    compiled Interface configuration payloads before they are materialized into
    canonical Interface ontology truth. They are intentionally scoped to
    configuration semantics, not live renderer state.
    """

    # Attributes
    interface_config_api_id: UUID
    api_id: UUID
    api_ref: str


class InterfaceWindowLayoutSectionBundle(BaseModel):
    # Attributes
    layout_config_section_config_id: UUID
    key: str


class InterfaceWindowConfigLayoutBundle(BaseModel):
    # Attributes
    window_config_layout_config_id: UUID
    layout_config_id: UUID
    key: str
    is_default: bool = Field(default=False)
    sections: list[InterfaceWindowLayoutSectionBundle] = Field(default_factory=list)


class InterfaceWindowConfigBundle(BaseModel):
    # Attributes
    interface_config_window_config_id: UUID
    window_config_id: UUID
    key: str
    description: str | None = Field(default=None)
    layout_configs: list[InterfaceWindowConfigLayoutBundle] = Field(default_factory=list)


class InterfacePaneSectionMountBundle(BaseModel):
    # Attributes
    mount_id: UUID
    layout_config_section_config_id: UUID


class InterfacePaneViewInvocationActionBundle(BaseModel):
    # Attributes
    projection_experience_view_invocation_action_id: UUID
    action_key: str
    action_kind: str
    target_ref: str
    api_capability_endpoint_id: UUID | None = Field(default=None)
    sdk_operation_id: UUID | None = Field(default=None)
    label: str | None = Field(default=None)
    receipt_policy: str | None = Field(default=None)
    confirmation_policy: str | None = Field(default=None)
    optimistic_policy: str | None = Field(default=None)


class InterfacePaneProjectionExperienceViewBundle(BaseModel):
    # Attributes
    binding_id: UUID
    projection_experience_view_id: UUID
    object_projection_graph_observable_id: UUID | None = Field(default=None)
    projection_experience_graph_identity_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID | None = Field(default=None)
    section_graph_binding_key: str | None = Field(default=None)
    state_model_id: UUID | None = Field(default=None)
    view_ref: str
    projection_view_key: str | None = Field(default=None)
    is_default: bool = Field(default=False)
    invocation_actions: list[InterfacePaneViewInvocationActionBundle] = Field(default_factory=list)
    section_mounts: list[InterfacePaneSectionMountBundle] = Field(default_factory=list)


class InterfacePaneApiCapabilityEndpointBundle(BaseModel):
    # Attributes
    binding_id: UUID
    api_capability_endpoint_id: UUID
    endpoint_ref: str | None = Field(default=None)
    discriminant: str | None = Field(default=None)


class InterfacePaneSdkOperationBundle(BaseModel):
    # Attributes
    binding_id: UUID
    sdk_operation_id: UUID
    operation_ref: str | None = Field(default=None)
    discriminant: str | None = Field(default=None)


class InterfacePaneConfigBundle(BaseModel):
    # Attributes
    pane_config_id: UUID
    pane_package_id: UUID | None = Field(default=None)
    pane_package_name: str | None = Field(default=None)
    name: str
    pane_kind: str
    description: str | None = Field(default=None)
    narrative_key: str | None = Field(default=None)
    projection_experience_views: list[InterfacePaneProjectionExperienceViewBundle] = Field(default_factory=list)
    api_capability_endpoints: list[InterfacePaneApiCapabilityEndpointBundle] = Field(default_factory=list)
    sdk_operations: list[InterfacePaneSdkOperationBundle] = Field(default_factory=list)


class InterfaceConfigBundle(BaseModel):
    # Attributes
    interface_package_id: UUID
    interface_package_name: str
    interface_config_id: UUID
    name: str
    description: str | None = Field(default=None)
    apis: list[InterfaceConfigApiBundle] = Field(default_factory=list)
    window_configs: list[InterfaceWindowConfigBundle] = Field(default_factory=list)
    pane_configs: list[InterfacePaneConfigBundle] = Field(default_factory=list)
