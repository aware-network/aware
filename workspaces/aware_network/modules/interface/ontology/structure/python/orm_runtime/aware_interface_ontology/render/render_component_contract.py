from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Interface Ontology
from aware_interface_ontology.render.pane_render_enums import (
    PaneActionEvent,
    PaneRenderNodeKind,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_interface_ontology.render.render_component_action_port import RenderComponentActionPort
    from aware_interface_ontology.render.render_component_capability import RenderComponentCapability
    from aware_interface_ontology.render.render_component_fallback_policy import RenderComponentFallbackPolicy
    from aware_interface_ontology.render.render_component_input_port import RenderComponentInputPort


class RenderComponentContract(ORMModel):
    # Relationships
    input_ports: list[RenderComponentInputPort] = Field(default_factory=list)
    action_ports: list[RenderComponentActionPort] = Field(default_factory=list)
    capabilities: list[RenderComponentCapability] = Field(default_factory=list)
    fallback_policies: list[RenderComponentFallbackPolicy] = Field(default_factory=list)

    # Attributes
    component_ref: str
    contract_version: int = Field(default=1)
    display_name: str | None = Field(default=None)
    description: str | None = Field(default=None)
    surface_kind: str | None = Field(default=None)

    # Foreign Keys
    render_component_config_id: UUID = Field(description="Foreign key for RenderComponentConfig.contracts")

    async def add_input_port(
        self, port_key: str, value_kind: str, is_required: bool = True, description: str | None = None
    ) -> RenderComponentInputPort:
        """Add one explicit state/data input port."""

        payload = {
            "port_key": port_key,
            "value_kind": value_kind,
            "is_required": is_required,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="add_input_port", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.render.render_component_input_port import RenderComponentInputPort

        if isinstance(value, RenderComponentInputPort):
            return value
        return RenderComponentInputPort.validate_invocation_value(value)

    async def add_action_port(
        self,
        port_key: str,
        event: PaneActionEvent = PaneActionEvent.activate,
        is_required: bool = True,
        description: str | None = None,
    ) -> RenderComponentActionPort:
        """Add one explicit action output port."""

        payload = {"port_key": port_key, "event": event, "is_required": is_required, "description": description}
        result = await invoke_instance(orm_model=self, function_name="add_action_port", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.render.render_component_action_port import RenderComponentActionPort

        if isinstance(value, RenderComponentActionPort):
            return value
        return RenderComponentActionPort.validate_invocation_value(value)

    async def require_capability(
        self, capability_kind: str, capability_key: str, is_required: bool = True, description: str | None = None
    ) -> RenderComponentCapability:
        """Declare one renderer capability required or preferred by this component."""

        payload = {
            "capability_kind": capability_kind,
            "capability_key": capability_key,
            "is_required": is_required,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="require_capability", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.render.render_component_capability import RenderComponentCapability

        if isinstance(value, RenderComponentCapability):
            return value
        return RenderComponentCapability.validate_invocation_value(value)

    async def add_fallback_policy(
        self,
        policy_key: str,
        fallback_kind: str,
        fallback_component_ref: str | None = None,
        fallback_node_kind: PaneRenderNodeKind | None = None,
        description: str | None = None,
    ) -> RenderComponentFallbackPolicy:
        """Declare how renderers should degrade when this component cannot be mounted."""

        payload = {
            "policy_key": policy_key,
            "fallback_kind": fallback_kind,
            "fallback_component_ref": fallback_component_ref,
            "fallback_node_kind": fallback_node_kind,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="add_fallback_policy", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.render.render_component_fallback_policy import RenderComponentFallbackPolicy

        if isinstance(value, RenderComponentFallbackPolicy):
            return value
        return RenderComponentFallbackPolicy.validate_invocation_value(value)

    @classmethod
    async def build_via_render_component_config(
        cls,
        render_component_config_id: UUID,
        component_ref: str,
        contract_version: int = 1,
        display_name: str | None = None,
        description: str | None = None,
        surface_kind: str | None = None,
    ) -> RenderComponentContract:
        """
        Create one renderer-neutral component contract.

        Contract:
        - `component_ref` is the stable reference PaneRenderSpec will use when selecting a
          reusable render component.
        - Input ports receive explicitly bound pane/view state.
        - Action ports emit canonical pane/API actions through ActionBinding.
        - Capabilities and fallback policies let renderers degrade without guessing pane state.
        """

        payload = {
            "render_component_config_id": render_component_config_id,
            "component_ref": component_ref,
            "contract_version": contract_version,
            "display_name": display_name,
            "description": description,
            "surface_kind": surface_kind,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_render_component_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, RenderComponentContract):
            return value
        return RenderComponentContract.validate_invocation_value(value)


class RenderComponentContractAddInputPortInput(BaseModel):
    port_key: str
    value_kind: str
    is_required: bool = Field(default=True)
    description: str | None = Field(default=None)


class RenderComponentContractAddInputPortOutput(BaseModel):
    value: RenderComponentInputPort


class RenderComponentContractAddActionPortInput(BaseModel):
    port_key: str
    event: PaneActionEvent = Field(default=PaneActionEvent.activate)
    is_required: bool = Field(default=True)
    description: str | None = Field(default=None)


class RenderComponentContractAddActionPortOutput(BaseModel):
    value: RenderComponentActionPort


class RenderComponentContractRequireCapabilityInput(BaseModel):
    capability_kind: str
    capability_key: str
    is_required: bool = Field(default=True)
    description: str | None = Field(default=None)


class RenderComponentContractRequireCapabilityOutput(BaseModel):
    value: RenderComponentCapability


class RenderComponentContractAddFallbackPolicyInput(BaseModel):
    policy_key: str
    fallback_kind: str
    fallback_component_ref: str | None = Field(default=None)
    fallback_node_kind: PaneRenderNodeKind | None = Field(default=None)
    description: str | None = Field(default=None)


class RenderComponentContractAddFallbackPolicyOutput(BaseModel):
    value: RenderComponentFallbackPolicy


class RenderComponentContractBuildViaRenderComponentConfigInput(BaseModel):
    render_component_config_id: UUID = Field(description="Foreign key for RenderComponentConfig.contracts")
    component_ref: str
    contract_version: int = Field(default=1)
    display_name: str | None = Field(default=None)
    description: str | None = Field(default=None)
    surface_kind: str | None = Field(default=None)


class RenderComponentContractBuildViaRenderComponentConfigOutput(BaseModel):
    value: RenderComponentContract


FUNCTIONS = {
    "RenderComponentContract": {
        "add_input_port": {
            "canonical": {
                "name": "add_input_port",
                "description": "Add one explicit state/data input port.",
                "is_constructor": False,
            },
            "input": RenderComponentContractAddInputPortInput,
            "output": RenderComponentContractAddInputPortOutput,
        },
        "add_action_port": {
            "canonical": {
                "name": "add_action_port",
                "description": "Add one explicit action output port.",
                "is_constructor": False,
            },
            "input": RenderComponentContractAddActionPortInput,
            "output": RenderComponentContractAddActionPortOutput,
        },
        "require_capability": {
            "canonical": {
                "name": "require_capability",
                "description": "Declare one renderer capability required or preferred by this component.",
                "is_constructor": False,
            },
            "input": RenderComponentContractRequireCapabilityInput,
            "output": RenderComponentContractRequireCapabilityOutput,
        },
        "add_fallback_policy": {
            "canonical": {
                "name": "add_fallback_policy",
                "description": "Declare how renderers should degrade when this component cannot be mounted.",
                "is_constructor": False,
            },
            "input": RenderComponentContractAddFallbackPolicyInput,
            "output": RenderComponentContractAddFallbackPolicyOutput,
        },
        "build_via_render_component_config": {
            "canonical": {
                "name": "build_via_render_component_config",
                "description": "Create one renderer-neutral component contract.\n\nContract:\n- `component_ref` is the stable reference PaneRenderSpec will use when selecting a\n  reusable render component.\n- Input ports receive explicitly bound pane/view state.\n- Action ports emit canonical pane/API actions through ActionBinding.\n- Capabilities and fallback policies let renderers degrade without guessing pane state.",
                "is_constructor": True,
            },
            "input": RenderComponentContractBuildViaRenderComponentConfigInput,
            "output": RenderComponentContractBuildViaRenderComponentConfigOutput,
        },
    },
}

__all__ = [
    "RenderComponentContract",
    "RenderComponentContractAddInputPortInput",
    "RenderComponentContractAddInputPortOutput",
    "RenderComponentContractAddActionPortInput",
    "RenderComponentContractAddActionPortOutput",
    "RenderComponentContractRequireCapabilityInput",
    "RenderComponentContractRequireCapabilityOutput",
    "RenderComponentContractAddFallbackPolicyInput",
    "RenderComponentContractAddFallbackPolicyOutput",
    "RenderComponentContractBuildViaRenderComponentConfigInput",
    "RenderComponentContractBuildViaRenderComponentConfigOutput",
    "FUNCTIONS",
]
