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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_experience_ontology.actuator.actuator import Actuator
    from aware_experience_ontology.actuator.actuator_config_state_node import ActuatorConfigStateNode
    from aware_experience_ontology.actuator.actuator_invocation_action_config import ActuatorInvocationActionConfig


class ActuatorConfig(ORMModel):
    """
    Actuator configuration.
    Contract:
    - An Actuator config describes outbound action capability a Connector can perform.
    - Actuator instances are runtime fulfillments declared under this config.
    - Affected state-node footprint declares which Projection nodes this
    actuator can affect; payload DTOs are resolved only through invocation
    bindings.
    - Invocation action config bindings expose the shared Experience invocation
    target surface without duplicating API/SDK/service fields.
    """

    # Relationships
    invocation_action_configs: list[ActuatorInvocationActionConfig] = Field(default_factory=list)
    affected_state_nodes: list[ActuatorConfigStateNode] = Field(default_factory=list)
    actuators: list[Actuator] = Field(default_factory=list)

    # Attributes
    actuator_key: str
    actuator_kind: str
    target_ref: str | None = Field(default=None)
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    connector_config_id: UUID = Field(description="Foreign key for ConnectorConfig.actuator_configs")

    async def add_affected_state_node(self, object_projection_graph_node_id: UUID) -> ActuatorConfigStateNode:
        """
        Add one affected Projection node footprint to this Actuator config.

        Contract:
        - The state node is a Meta ObjectProjectionGraphNode portal.
        - This is not a payload schema. Payload DTO contracts resolve through
          the bound ExperienceInvocationActionConfig endpoint only.
        """

        payload = {"object_projection_graph_node_id": object_projection_graph_node_id}
        result = await invoke_instance(orm_model=self, function_name="add_affected_state_node", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.actuator.actuator_config_state_node import ActuatorConfigStateNode

        if isinstance(value, ActuatorConfigStateNode):
            return value
        return ActuatorConfigStateNode.validate_invocation_value(value)

    async def create_actuator(
        self, actuator_instance_key: str, external_ref: str | None = None, status: str = "active"
    ) -> Actuator:
        """
        Create one deterministic Actuator instance under this Actuator config.

        Contract:
        - Config -> Instance is the canonical ownership rail.
        - Parent `ActuatorConfig` scope is propagated by constructor lowering.
        - `actuator_instance_key` identifies this runtime fulfillment.
        """

        payload = {"actuator_instance_key": actuator_instance_key, "external_ref": external_ref, "status": status}
        result = await invoke_instance(orm_model=self, function_name="create_actuator", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.actuator.actuator import Actuator

        if isinstance(value, Actuator):
            return value
        return Actuator.validate_invocation_value(value)

    async def bind_invocation_action_config(
        self, experience_invocation_action_config_id: UUID
    ) -> ActuatorInvocationActionConfig:
        """
        Bind one reusable Experience invocation action config to this Actuator config.

        Contract:
        - `ActuatorConfig` remains the raw actuator capability surface.
        - `ExperienceInvocationActionConfig` remains the shared target metadata.
        - Actuator instances use the matching action config binding when recording
          concrete invocation provenance.
        """

        payload = {"experience_invocation_action_config_id": experience_invocation_action_config_id}
        result = await invoke_instance(orm_model=self, function_name="bind_invocation_action_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.actuator.actuator_invocation_action_config import ActuatorInvocationActionConfig

        if isinstance(value, ActuatorInvocationActionConfig):
            return value
        return ActuatorInvocationActionConfig.validate_invocation_value(value)

    @classmethod
    async def build_via_connector_config(
        cls,
        connector_config_id: UUID,
        actuator_key: str,
        actuator_kind: str,
        target_ref: str | None = None,
        label: str | None = None,
        description: str | None = None,
    ) -> ActuatorConfig:
        """
        Create one deterministic Actuator config under a ConnectorConfig.

        Contract:
        - Parent `ConnectorConfig` scope is propagated by constructor lowering.
        - `actuator_key` is stable within the Connector config.
        - `actuator_kind` identifies the outbound target/action family.
        """

        payload = {
            "connector_config_id": connector_config_id,
            "actuator_key": actuator_key,
            "actuator_kind": actuator_kind,
            "target_ref": target_ref,
            "label": label,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_connector_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActuatorConfig):
            return value
        return ActuatorConfig.validate_invocation_value(value)


class ActuatorConfigAddAffectedStateNodeInput(BaseModel):
    object_projection_graph_node_id: UUID


class ActuatorConfigAddAffectedStateNodeOutput(BaseModel):
    value: ActuatorConfigStateNode


class ActuatorConfigCreateActuatorInput(BaseModel):
    actuator_instance_key: str
    external_ref: str | None = Field(default=None)
    status: str = Field(default="active")


class ActuatorConfigCreateActuatorOutput(BaseModel):
    value: Actuator


class ActuatorConfigBindInvocationActionConfigInput(BaseModel):
    experience_invocation_action_config_id: UUID


class ActuatorConfigBindInvocationActionConfigOutput(BaseModel):
    value: ActuatorInvocationActionConfig


class ActuatorConfigBuildViaConnectorConfigInput(BaseModel):
    connector_config_id: UUID = Field(description="Foreign key for ConnectorConfig.actuator_configs")
    actuator_key: str
    actuator_kind: str
    target_ref: str | None = Field(default=None)
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)


class ActuatorConfigBuildViaConnectorConfigOutput(BaseModel):
    value: ActuatorConfig


FUNCTIONS = {
    "ActuatorConfig": {
        "add_affected_state_node": {
            "canonical": {
                "name": "add_affected_state_node",
                "description": "Add one affected Projection node footprint to this Actuator config.\n\nContract:\n- The state node is a Meta ObjectProjectionGraphNode portal.\n- This is not a payload schema. Payload DTO contracts resolve through\n  the bound ExperienceInvocationActionConfig endpoint only.",
                "is_constructor": False,
            },
            "input": ActuatorConfigAddAffectedStateNodeInput,
            "output": ActuatorConfigAddAffectedStateNodeOutput,
        },
        "create_actuator": {
            "canonical": {
                "name": "create_actuator",
                "description": "Create one deterministic Actuator instance under this Actuator config.\n\nContract:\n- Config -> Instance is the canonical ownership rail.\n- Parent `ActuatorConfig` scope is propagated by constructor lowering.\n- `actuator_instance_key` identifies this runtime fulfillment.",
                "is_constructor": False,
            },
            "input": ActuatorConfigCreateActuatorInput,
            "output": ActuatorConfigCreateActuatorOutput,
        },
        "bind_invocation_action_config": {
            "canonical": {
                "name": "bind_invocation_action_config",
                "description": "Bind one reusable Experience invocation action config to this Actuator config.\n\nContract:\n- `ActuatorConfig` remains the raw actuator capability surface.\n- `ExperienceInvocationActionConfig` remains the shared target metadata.\n- Actuator instances use the matching action config binding when recording\n  concrete invocation provenance.",
                "is_constructor": False,
            },
            "input": ActuatorConfigBindInvocationActionConfigInput,
            "output": ActuatorConfigBindInvocationActionConfigOutput,
        },
        "build_via_connector_config": {
            "canonical": {
                "name": "build_via_connector_config",
                "description": "Create one deterministic Actuator config under a ConnectorConfig.\n\nContract:\n- Parent `ConnectorConfig` scope is propagated by constructor lowering.\n- `actuator_key` is stable within the Connector config.\n- `actuator_kind` identifies the outbound target/action family.",
                "is_constructor": True,
            },
            "input": ActuatorConfigBuildViaConnectorConfigInput,
            "output": ActuatorConfigBuildViaConnectorConfigOutput,
        },
    },
}

__all__ = [
    "ActuatorConfig",
    "ActuatorConfigAddAffectedStateNodeInput",
    "ActuatorConfigAddAffectedStateNodeOutput",
    "ActuatorConfigCreateActuatorInput",
    "ActuatorConfigCreateActuatorOutput",
    "ActuatorConfigBindInvocationActionConfigInput",
    "ActuatorConfigBindInvocationActionConfigOutput",
    "ActuatorConfigBuildViaConnectorConfigInput",
    "ActuatorConfigBuildViaConnectorConfigOutput",
    "FUNCTIONS",
]
