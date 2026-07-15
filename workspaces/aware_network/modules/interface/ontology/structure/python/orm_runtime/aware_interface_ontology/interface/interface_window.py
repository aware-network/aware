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
    from aware_interface_ontology.interface.interface_window_navigation_context import InterfaceWindowNavigationContext
    from aware_interface_ontology.window.window import Window


class InterfaceWindow(ORMModel):
    # Relationships
    window: Window | None = Field(default=None, exclude=True)
    window_navigation_contexts: list[InterfaceWindowNavigationContext] = Field(default_factory=list, exclude=True)
    active_navigation_context: InterfaceWindowNavigationContext | None = Field(default=None, exclude=True)

    # Foreign Keys
    interface_id: UUID = Field(description="Foreign key for Interface.interface_windows")
    window_id: UUID = Field(description="Foreign key for InterfaceWindow.window")
    active_navigation_context_id: UUID | None = Field(
        default=None, description="Foreign key for InterfaceWindow.active_navigation_context"
    )

    async def attach_navigation_context(
        self, interface_environment_id: UUID, environment_navigation_context_id: UUID
    ) -> InterfaceWindowNavigationContext:
        """
        Creates (or ensures) a window target over an Interface-authorized
        EnvironmentNavigationContext.

        Contract:
        - InterfaceWindow follows Environment navigation context truth.
        - The selected Process/Thread target resolves from the navigation context.
        - The selected Thread's active layout remains Environment/Attention truth.
        """

        payload = {
            "interface_environment_id": interface_environment_id,
            "environment_navigation_context_id": environment_navigation_context_id,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_navigation_context", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.interface_window_navigation_context import (
            InterfaceWindowNavigationContext,
        )

        if isinstance(value, InterfaceWindowNavigationContext):
            return value
        return InterfaceWindowNavigationContext.validate_invocation_value(value)

    async def set_active_navigation_context(
        self, interface_environment_id: UUID, environment_navigation_context_id: UUID
    ) -> InterfaceWindowNavigationContext:
        """
        Selects the protected EnvironmentNavigationContext this InterfaceWindow
        follows.

        Contract:
        - Mutates only the InterfaceWindow active navigation-context pointer.
        - Does not mutate the EnvironmentNavigationContext target.
        - Thread selection changes happen through
          EnvironmentNavigationContext.select_target.
        """

        payload = {
            "interface_environment_id": interface_environment_id,
            "environment_navigation_context_id": environment_navigation_context_id,
        }
        result = await invoke_instance(orm_model=self, function_name="set_active_navigation_context", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.interface_window_navigation_context import (
            InterfaceWindowNavigationContext,
        )

        if isinstance(value, InterfaceWindowNavigationContext):
            return value
        return InterfaceWindowNavigationContext.validate_invocation_value(value)

    @classmethod
    async def create_via_interface(cls, interface_id: UUID, window_id: UUID) -> InterfaceWindow:
        """Creates a new InterfaceWindow."""

        payload = {"interface_id": interface_id, "window_id": window_id}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_interface", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, InterfaceWindow):
            return value
        return InterfaceWindow.validate_invocation_value(value)


class InterfaceWindowAttachNavigationContextInput(BaseModel):
    interface_environment_id: UUID
    environment_navigation_context_id: UUID


class InterfaceWindowAttachNavigationContextOutput(BaseModel):
    value: InterfaceWindowNavigationContext


class InterfaceWindowSetActiveNavigationContextInput(BaseModel):
    interface_environment_id: UUID
    environment_navigation_context_id: UUID


class InterfaceWindowSetActiveNavigationContextOutput(BaseModel):
    value: InterfaceWindowNavigationContext


class InterfaceWindowCreateViaInterfaceInput(BaseModel):
    interface_id: UUID = Field(description="Foreign key for Interface.interface_windows")
    window_id: UUID


class InterfaceWindowCreateViaInterfaceOutput(BaseModel):
    value: InterfaceWindow


FUNCTIONS = {
    "InterfaceWindow": {
        "attach_navigation_context": {
            "canonical": {
                "name": "attach_navigation_context",
                "description": "Creates (or ensures) a window target over an Interface-authorized\nEnvironmentNavigationContext.\n\nContract:\n- InterfaceWindow follows Environment navigation context truth.\n- The selected Process/Thread target resolves from the navigation context.\n- The selected Thread's active layout remains Environment/Attention truth.",
                "is_constructor": False,
            },
            "input": InterfaceWindowAttachNavigationContextInput,
            "output": InterfaceWindowAttachNavigationContextOutput,
        },
        "set_active_navigation_context": {
            "canonical": {
                "name": "set_active_navigation_context",
                "description": "Selects the protected EnvironmentNavigationContext this InterfaceWindow\nfollows.\n\nContract:\n- Mutates only the InterfaceWindow active navigation-context pointer.\n- Does not mutate the EnvironmentNavigationContext target.\n- Thread selection changes happen through\n  EnvironmentNavigationContext.select_target.",
                "is_constructor": False,
            },
            "input": InterfaceWindowSetActiveNavigationContextInput,
            "output": InterfaceWindowSetActiveNavigationContextOutput,
        },
        "create_via_interface": {
            "canonical": {
                "name": "create_via_interface",
                "description": "Creates a new InterfaceWindow.",
                "is_constructor": True,
            },
            "input": InterfaceWindowCreateViaInterfaceInput,
            "output": InterfaceWindowCreateViaInterfaceOutput,
        },
    },
}

__all__ = [
    "InterfaceWindow",
    "InterfaceWindowAttachNavigationContextInput",
    "InterfaceWindowAttachNavigationContextOutput",
    "InterfaceWindowSetActiveNavigationContextInput",
    "InterfaceWindowSetActiveNavigationContextOutput",
    "InterfaceWindowCreateViaInterfaceInput",
    "InterfaceWindowCreateViaInterfaceOutput",
    "FUNCTIONS",
]
