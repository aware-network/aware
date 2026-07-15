from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_interface_ontology.interface.interface_config import InterfaceConfig


class NodeConfigInterfaceTarget(ORMModel):
    # Relationships
    interface_config: InterfaceConfig | None = Field(default=None)

    # Attributes
    interface_name: str

    # Foreign Keys
    node_config_id: UUID = Field(description="Foreign key for NodeConfig.interface_targets")
    interface_config_id: UUID | None = Field(
        default=None, description="Foreign key for NodeConfigInterfaceTarget.interface_config"
    )

    @classmethod
    async def build_via_node_config(cls, node_config_id: UUID, interface_name: str) -> NodeConfigInterfaceTarget:
        """
        Create one Node-owned interface target by canonical interface name.

        Contract:
        - Parent `NodeConfig` scope is injected by propagation.
        - Identity is keyed by `(node_config_id, interface_name)`.
        - The target `InterfaceConfig` portal is resolved from `interface_name` without storing a
          raw relationship-id attribute as semantic source.
        """

        payload = {"node_config_id": node_config_id, "interface_name": interface_name}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_node_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NodeConfigInterfaceTarget):
            return value
        return NodeConfigInterfaceTarget.validate_invocation_value(value)


class NodeConfigInterfaceTargetBuildViaNodeConfigInput(BaseModel):
    node_config_id: UUID = Field(description="Foreign key for NodeConfig.interface_targets")
    interface_name: str


class NodeConfigInterfaceTargetBuildViaNodeConfigOutput(BaseModel):
    value: NodeConfigInterfaceTarget


FUNCTIONS = {
    "NodeConfigInterfaceTarget": {
        "build_via_node_config": {
            "canonical": {
                "name": "build_via_node_config",
                "description": "Create one Node-owned interface target by canonical interface name.\n\nContract:\n- Parent `NodeConfig` scope is injected by propagation.\n- Identity is keyed by `(node_config_id, interface_name)`.\n- The target `InterfaceConfig` portal is resolved from `interface_name` without storing a\n  raw relationship-id attribute as semantic source.",
                "is_constructor": True,
            },
            "input": NodeConfigInterfaceTargetBuildViaNodeConfigInput,
            "output": NodeConfigInterfaceTargetBuildViaNodeConfigOutput,
        },
    },
}

__all__ = [
    "NodeConfigInterfaceTarget",
    "NodeConfigInterfaceTargetBuildViaNodeConfigInput",
    "NodeConfigInterfaceTargetBuildViaNodeConfigOutput",
    "FUNCTIONS",
]
