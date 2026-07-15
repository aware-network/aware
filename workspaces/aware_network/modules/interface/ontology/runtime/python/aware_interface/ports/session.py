from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from aware_interface.lane_sync import InterfaceLaneSyncSource


class InterfaceSessionPort(Protocol):
    """Host-neutral session dependency consumed by the interface runtime."""

    async def ensure_boot_interface_graph(self) -> UUID:
        """Ensure the canonical interface substrate exists for the active session context."""
        ...

    async def resolve_projection_hash(self, *, opg_name: str) -> str:
        """Resolve a projection hash by canonical OPG name for the active environment."""
        ...

    async def resolve_focus_scope_lane(
        self,
        *,
        window_key: str,
    ) -> Any:
        """Resolve the canonical focus-scope lane for a window key."""
        ...

    async def resolve_section_focus_scope_lane(
        self,
        *,
        window_key: str,
        layout_key: str,
        section_key: str,
    ) -> Any:
        """Resolve the canonical section-owned focus-scope lane."""
        ...

    def lane_sync_source(
        self,
        *,
        include_commit_payload: bool = True,
    ) -> InterfaceLaneSyncSource:
        """Build a canonical remote lane-sync source for the interface runtime."""
        ...

    def context_ids(self) -> tuple[UUID | None, UUID | None]:
        """Return canonical `(process_id, thread_id)` selection from the active session context."""
        ...


__all__ = ["InterfaceSessionPort"]
