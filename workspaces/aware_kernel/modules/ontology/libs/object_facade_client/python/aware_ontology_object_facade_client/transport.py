"""Data delivery interface only; peer admission belongs to the hosting owners."""

from typing import Protocol


class FacadeTransport(Protocol):
    async def exchange(self, request: bytes, /) -> bytes:
        """Deliver one framed request; bytes returned do not authenticate a peer."""
        ...
