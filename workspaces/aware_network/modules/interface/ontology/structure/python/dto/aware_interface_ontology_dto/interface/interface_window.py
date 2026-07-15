from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_interface_ontology_dto.interface.interface_window_navigation_context import (
        InterfaceWindowNavigationContext,
    )
    from aware_interface_ontology_dto.window.window import Window


class InterfaceWindow(BaseModel):
    # Relationships
    window: Window | None = Field(default=None)
    window_navigation_contexts: list[InterfaceWindowNavigationContext] = Field(default_factory=list)
    active_navigation_context: InterfaceWindowNavigationContext | None = Field(default=None)
