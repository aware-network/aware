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
from aware_interface_ontology.interface.interface_enums import (
    InterfaceOs,
    InterfaceSessionState,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_identity_ontology.actor.actor import Actor
    from aware_interface_ontology.interface.interface_environment import InterfaceEnvironment
    from aware_interface_ontology.interface.interface_identity import InterfaceIdentity
    from aware_interface_ontology.interface.interface_session import InterfaceSession
    from aware_interface_ontology.interface.interface_window import InterfaceWindow
    from aware_interface_ontology.interface.interface_window_navigation_context import InterfaceWindowNavigationContext
    from aware_network_ontology.network.network_operation_hop import NetworkOperationHop


class Interface(ORMModel):
    # Relationships
    system_actor: Actor | None = Field(
        default=None,
        exclude=True,
        description="Interface-owned system Actor used for pre-operator provenance.\nContract:\n- Interface bootstrap/admission actions are never actorless.\n- The human/operator Actor is bound later by Identity admission.\n- This portal points at Identity's canonical system Actor for this Interface.",
    )
    interface_sessions: list[InterfaceSession] = Field(default_factory=list, exclude=True)
    interface_identities: list[InterfaceIdentity] = Field(default_factory=list, exclude=True)
    environments: list[InterfaceEnvironment] = Field(default_factory=list, exclude=True)
    interface_windows: list[InterfaceWindow] = Field(default_factory=list, exclude=True)
    source_network_operation_hops: list[NetworkOperationHop] = Field(default_factory=list, exclude=True)
    target_network_operation_hops: list[NetworkOperationHop] = Field(default_factory=list, exclude=True)

    # Attributes
    os: InterfaceOs
    version: str

    # Foreign Keys
    interface_config_id: UUID = Field(description="Foreign key for InterfaceConfig.interfaces")
    system_actor_id: UUID | None = Field(default=None, description="Foreign key for Interface.system_actor")

    async def attach_window(self, window_id: UUID) -> InterfaceWindow:
        """
        Creates (or ensures) an InterfaceWindow link for an existing Window.

        Canonical v0:
        - Window instances live in the `window` projection lane (separate receipt).
        - This function commits only the link object (`InterfaceWindow`) in the `interface` lane.
        - InterfaceWindow id is derived deterministically from (interface_id, window_id).
        - Idempotent: safe to call multiple times for the same `window_id`.

        Projection boundary:
        - `InterfaceWindow::window` is a portal to the `window` projection.
        - The caller must create/ensure the target `window.Window` separately (e.g. via
        `window.Window.build(window_id)`).
        """

        payload = {"window_id": window_id}
        result = await invoke_instance(orm_model=self, function_name="attach_window", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.interface_window import InterfaceWindow

        if isinstance(value, InterfaceWindow):
            return value
        return InterfaceWindow.validate_invocation_value(value)

    async def attach_environment(self, environment_id: UUID) -> InterfaceEnvironment:
        """
        Creates (or ensures) an InterfaceEnvironment access association.

        Contract:
        - Interface owns the Environment access contract.
        - Window thread targets must reference this association instead of granting Environment access
          from raw Window state.
        - Idempotent: safe to call multiple times for the same `environment_id`.
        """

        payload = {"environment_id": environment_id}
        result = await invoke_instance(orm_model=self, function_name="attach_environment", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.interface_environment import InterfaceEnvironment

        if isinstance(value, InterfaceEnvironment):
            return value
        return InterfaceEnvironment.validate_invocation_value(value)

    async def start_session(
        self, identity_session_id: UUID, name: str, state: InterfaceSessionState = InterfaceSessionState.active
    ) -> InterfaceSession:
        """
        Start or attach one commit-backed InterfaceSession.

        Contract:
        - `identity_session_id` is canonical Identity participation evidence.
        - Identity Session membership admits every participant; the shared
          InterfaceSession is not owned by one InterfaceIdentity.
        - The commit records durable client/session provenance before any
          transport binding is registered.
        - Network connection and bearer-token lifecycle remain ephemeral
          transport concerns.
        """

        payload = {"identity_session_id": identity_session_id, "name": name, "state": state}
        result = await invoke_instance(orm_model=self, function_name="start_session", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.interface_session import InterfaceSession

        if isinstance(value, InterfaceSession):
            return value
        return InterfaceSession.validate_invocation_value(value)

    async def set_active_window_navigation_context(
        self, window_id: UUID, environment_id: UUID, environment_navigation_context_id: UUID
    ) -> InterfaceWindowNavigationContext:
        """
        Ensures Interface Environment access, ensures the InterfaceWindow link,
        and selects the protected EnvironmentNavigationContext target for that
        window inside the Interface commit.

        Contract:
        - Interface follows navigation-context truth, not raw Thread truth.
        - Process/Thread selection is mutated through the Environment
          NavigationContext API/service rail.
        """

        payload = {
            "window_id": window_id,
            "environment_id": environment_id,
            "environment_navigation_context_id": environment_navigation_context_id,
        }
        result = await invoke_instance(
            orm_model=self, function_name="set_active_window_navigation_context", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.interface_window_navigation_context import (
            InterfaceWindowNavigationContext,
        )

        if isinstance(value, InterfaceWindowNavigationContext):
            return value
        return InterfaceWindowNavigationContext.validate_invocation_value(value)

    @classmethod
    async def build_via_interface_config(cls, interface_config_id: UUID, os: InterfaceOs, version: str) -> Interface:
        """Create one Interface runtime instance under InterfaceConfig."""

        payload = {"interface_config_id": interface_config_id, "os": os, "version": version}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_interface_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Interface):
            return value
        return Interface.validate_invocation_value(value)


class InterfaceAttachWindowInput(BaseModel):
    window_id: UUID


class InterfaceAttachWindowOutput(BaseModel):
    value: InterfaceWindow


class InterfaceAttachEnvironmentInput(BaseModel):
    environment_id: UUID


class InterfaceAttachEnvironmentOutput(BaseModel):
    value: InterfaceEnvironment


class InterfaceStartSessionInput(BaseModel):
    identity_session_id: UUID
    name: str
    state: InterfaceSessionState = Field(default=InterfaceSessionState.active)


class InterfaceStartSessionOutput(BaseModel):
    value: InterfaceSession


class InterfaceSetActiveWindowNavigationContextInput(BaseModel):
    window_id: UUID
    environment_id: UUID
    environment_navigation_context_id: UUID


class InterfaceSetActiveWindowNavigationContextOutput(BaseModel):
    value: InterfaceWindowNavigationContext


class InterfaceBuildViaInterfaceConfigInput(BaseModel):
    interface_config_id: UUID = Field(description="Foreign key for InterfaceConfig.interfaces")
    os: InterfaceOs
    version: str


class InterfaceBuildViaInterfaceConfigOutput(BaseModel):
    value: Interface


FUNCTIONS = {
    "Interface": {
        "attach_window": {
            "canonical": {
                "name": "attach_window",
                "description": "Creates (or ensures) an InterfaceWindow link for an existing Window.\n\nCanonical v0:\n- Window instances live in the `window` projection lane (separate receipt).\n- This function commits only the link object (`InterfaceWindow`) in the `interface` lane.\n- InterfaceWindow id is derived deterministically from (interface_id, window_id).\n- Idempotent: safe to call multiple times for the same `window_id`.\n\nProjection boundary:\n- `InterfaceWindow::window` is a portal to the `window` projection.\n- The caller must create/ensure the target `window.Window` separately (e.g. via `window.Window.build(window_id)`).",
                "is_constructor": False,
            },
            "input": InterfaceAttachWindowInput,
            "output": InterfaceAttachWindowOutput,
        },
        "attach_environment": {
            "canonical": {
                "name": "attach_environment",
                "description": "Creates (or ensures) an InterfaceEnvironment access association.\n\nContract:\n- Interface owns the Environment access contract.\n- Window thread targets must reference this association instead of granting Environment access\n  from raw Window state.\n- Idempotent: safe to call multiple times for the same `environment_id`.",
                "is_constructor": False,
            },
            "input": InterfaceAttachEnvironmentInput,
            "output": InterfaceAttachEnvironmentOutput,
        },
        "start_session": {
            "canonical": {
                "name": "start_session",
                "description": "Start or attach one commit-backed InterfaceSession.\n\nContract:\n- `identity_session_id` is canonical Identity participation evidence.\n- Identity Session membership admits every participant; the shared\n  InterfaceSession is not owned by one InterfaceIdentity.\n- The commit records durable client/session provenance before any\n  transport binding is registered.\n- Network connection and bearer-token lifecycle remain ephemeral\n  transport concerns.",
                "is_constructor": False,
            },
            "input": InterfaceStartSessionInput,
            "output": InterfaceStartSessionOutput,
        },
        "set_active_window_navigation_context": {
            "canonical": {
                "name": "set_active_window_navigation_context",
                "description": "Ensures Interface Environment access, ensures the InterfaceWindow link,\nand selects the protected EnvironmentNavigationContext target for that\nwindow inside the Interface commit.\n\nContract:\n- Interface follows navigation-context truth, not raw Thread truth.\n- Process/Thread selection is mutated through the Environment\n  NavigationContext API/service rail.",
                "is_constructor": False,
            },
            "input": InterfaceSetActiveWindowNavigationContextInput,
            "output": InterfaceSetActiveWindowNavigationContextOutput,
        },
        "build_via_interface_config": {
            "canonical": {
                "name": "build_via_interface_config",
                "description": "Create one Interface runtime instance under InterfaceConfig.",
                "is_constructor": True,
            },
            "input": InterfaceBuildViaInterfaceConfigInput,
            "output": InterfaceBuildViaInterfaceConfigOutput,
        },
    },
}

__all__ = [
    "Interface",
    "InterfaceAttachWindowInput",
    "InterfaceAttachWindowOutput",
    "InterfaceAttachEnvironmentInput",
    "InterfaceAttachEnvironmentOutput",
    "InterfaceStartSessionInput",
    "InterfaceStartSessionOutput",
    "InterfaceSetActiveWindowNavigationContextInput",
    "InterfaceSetActiveWindowNavigationContextOutput",
    "InterfaceBuildViaInterfaceConfigInput",
    "InterfaceBuildViaInterfaceConfigOutput",
    "FUNCTIONS",
]
