from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from aware_interface.lifecycle.models import (
        InterfaceResolvedView,
        InterfaceRuntimeState,
    )


class InterfaceExperiencePort(Protocol):
    """Host-neutral view-resolution dependency for interface runtime coordination."""

    async def resolve_view(
        self,
        *,
        state: "InterfaceRuntimeState",
    ) -> "InterfaceResolvedView | None":
        ...


__all__ = [
    "InterfaceExperiencePort",
]
