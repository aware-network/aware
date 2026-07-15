from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_environment_ontology_dto.environment.environment_navigation_context import EnvironmentNavigationContext
    from aware_interface_ontology_dto.interface.interface_environment import InterfaceEnvironment


class InterfaceWindowNavigationContext(BaseModel):
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
    interface_environment: InterfaceEnvironment | None = Field(default=None)
    environment_navigation_context: EnvironmentNavigationContext | None = Field(default=None)
