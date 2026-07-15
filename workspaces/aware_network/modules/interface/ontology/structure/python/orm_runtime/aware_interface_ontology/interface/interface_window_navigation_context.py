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
    from aware_environment_ontology.environment.environment_navigation_context import EnvironmentNavigationContext
    from aware_interface_ontology.interface.interface_environment import InterfaceEnvironment


class InterfaceWindowNavigationContext(ORMModel):
    """
    Protected per-window target over an Interface-authorized Environment
    navigation context.
    Contract:
    - `interface_environment` proves this window target is scoped by Interface
    Environment access.
    - `environment_navigation_context` is the browser-tab-like OS pointer this
    InterfaceWindow follows.
    - The selected Process/Thread target remains Environment truth on
    EnvironmentNavigationContext.
    - The selected Thread's active layout remains Environment/Attention truth:
    resolve through EnvironmentNavigationContext -> Thread.active_thread_layout.
    """

    # Relationships
    interface_environment: InterfaceEnvironment | None = Field(default=None, exclude=True)
    environment_navigation_context: EnvironmentNavigationContext | None = Field(default=None, exclude=True)

    # Foreign Keys
    interface_window_id: UUID = Field(description="Foreign key for InterfaceWindow.window_navigation_contexts")
    interface_environment_id: UUID = Field(
        description="Foreign key for InterfaceWindowNavigationContext.interface_environment"
    )
    environment_navigation_context_id: UUID = Field(
        description="Foreign key for InterfaceWindowNavigationContext.environment_navigation_context"
    )

    @classmethod
    async def create_via_interface_window(
        cls, interface_window_id: UUID, interface_environment_id: UUID, environment_navigation_context_id: UUID
    ) -> InterfaceWindowNavigationContext:
        """
        Creates a deterministic InterfaceWindow -> InterfaceEnvironment /
        EnvironmentNavigationContext target association.
        """

        payload = {
            "interface_window_id": interface_window_id,
            "interface_environment_id": interface_environment_id,
            "environment_navigation_context_id": environment_navigation_context_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_interface_window", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, InterfaceWindowNavigationContext):
            return value
        return InterfaceWindowNavigationContext.validate_invocation_value(value)


class InterfaceWindowNavigationContextCreateViaInterfaceWindowInput(BaseModel):
    interface_window_id: UUID = Field(description="Foreign key for InterfaceWindow.window_navigation_contexts")
    interface_environment_id: UUID
    environment_navigation_context_id: UUID


class InterfaceWindowNavigationContextCreateViaInterfaceWindowOutput(BaseModel):
    value: InterfaceWindowNavigationContext


FUNCTIONS = {
    "InterfaceWindowNavigationContext": {
        "create_via_interface_window": {
            "canonical": {
                "name": "create_via_interface_window",
                "description": "Creates a deterministic InterfaceWindow -> InterfaceEnvironment /\nEnvironmentNavigationContext target association.",
                "is_constructor": True,
            },
            "input": InterfaceWindowNavigationContextCreateViaInterfaceWindowInput,
            "output": InterfaceWindowNavigationContextCreateViaInterfaceWindowOutput,
        },
    },
}

__all__ = [
    "InterfaceWindowNavigationContext",
    "InterfaceWindowNavigationContextCreateViaInterfaceWindowInput",
    "InterfaceWindowNavigationContextCreateViaInterfaceWindowOutput",
    "FUNCTIONS",
]
