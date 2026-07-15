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
    from aware_environment_ontology.environment.environment import Environment


class InterfaceEnvironment(ORMModel):
    """
    Interface-owned Environment access contract.
    Contract:
    - This is the canonical commit-backed fact that an Interface can resolve against an Environment.
    - Window/thread targeting must route through this association instead of letting windows grant
    Environment access directly.
    """

    # Relationships
    environment: Environment | None = Field(default=None, exclude=True)

    # Foreign Keys
    interface_id: UUID = Field(description="Foreign key for Interface.environments")
    environment_id: UUID = Field(description="Foreign key for InterfaceEnvironment.environment")

    @classmethod
    async def create_via_interface(cls, interface_id: UUID, environment_id: UUID) -> InterfaceEnvironment:
        """Creates a deterministic Interface -> Environment access association."""

        payload = {"interface_id": interface_id, "environment_id": environment_id}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_interface", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, InterfaceEnvironment):
            return value
        return InterfaceEnvironment.validate_invocation_value(value)


class InterfaceEnvironmentCreateViaInterfaceInput(BaseModel):
    interface_id: UUID = Field(description="Foreign key for Interface.environments")
    environment_id: UUID


class InterfaceEnvironmentCreateViaInterfaceOutput(BaseModel):
    value: InterfaceEnvironment


FUNCTIONS = {
    "InterfaceEnvironment": {
        "create_via_interface": {
            "canonical": {
                "name": "create_via_interface",
                "description": "Creates a deterministic Interface -> Environment access association.",
                "is_constructor": True,
            },
            "input": InterfaceEnvironmentCreateViaInterfaceInput,
            "output": InterfaceEnvironmentCreateViaInterfaceOutput,
        },
    },
}

__all__ = [
    "InterfaceEnvironment",
    "InterfaceEnvironmentCreateViaInterfaceInput",
    "InterfaceEnvironmentCreateViaInterfaceOutput",
    "FUNCTIONS",
]
