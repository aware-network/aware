from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_interface_ontology_orm_models.interface.interface_window_navigation_context import (
        InterfaceWindowNavigationContext,
    )
    from aware_interface_ontology_orm_models.window.window import Window


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
