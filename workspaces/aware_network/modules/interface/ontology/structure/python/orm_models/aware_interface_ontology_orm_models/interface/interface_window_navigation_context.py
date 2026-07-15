from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.environment.environment_navigation_context import (
        EnvironmentNavigationContext,
    )
    from aware_interface_ontology_orm_models.interface.interface_environment import InterfaceEnvironment


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
