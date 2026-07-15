from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from aware_interface.lifecycle.models import (
        InterfaceActionReceipt,
        InterfaceActionRequest,
    )


class InterfaceActionPort(Protocol):
    """Host-neutral action dependency for interface runtime coordination."""

    async def perform_action(
        self,
        request: "InterfaceActionRequest",
    ) -> "InterfaceActionReceipt":
        ...


__all__ = [
    "InterfaceActionPort",
]
