from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from aware_interface.lifecycle.models import (
        InterfaceRuntimeState,
        InterfaceNavigationContextLayoutTargetState,
    )


class InterfaceNavigationContextLayoutPort(Protocol):
    """Host-neutral resolver for EnvironmentNavigationContext layout evidence."""

    async def resolve_navigation_context_layout_target(
        self,
        *,
        state: "InterfaceRuntimeState",
    ) -> "InterfaceNavigationContextLayoutTargetState | None": ...


__all__ = [
    "InterfaceNavigationContextLayoutPort",
]
