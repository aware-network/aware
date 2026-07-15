from __future__ import annotations

from collections.abc import Awaitable, Callable
from inspect import isawaitable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from uuid import NAMESPACE_URL, uuid5


class BearerAuth(HTTPBearer):
    async def get_token(self, request: Request) -> str:
        credentials: HTTPAuthorizationCredentials | None = await super().__call__(
            request
        )
        if not credentials or credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated"
            )
        return credentials.credentials


auth_scheme = BearerAuth()


TokenResolver = Callable[[str], UUID | Awaitable[UUID]]

_token_resolver: TokenResolver | None = None


def set_token_resolver(resolver: TokenResolver | None) -> None:
    """Install a process-local token->user-id resolver.

    `aware_comms` is transport-only and cannot own a canonical auth story.
    Services (e.g. the Network Node) may install a resolver that validates
    bearer tokens against their live session state or durable auth tables.
    """

    global _token_resolver
    _token_resolver = resolver


async def get_current_user_id(
    token: Annotated[str, Depends(auth_scheme.get_token)]
) -> UUID:
    """Extract a user identifier from the auth token.

    The canonical auth story is still evolving (actor/thread bindings, etc.).
    For now:
    - If the token is a UUID string, use it directly.
    - Otherwise, derive a deterministic UUID from the raw token.
    """

    if _token_resolver is not None:
        resolved = _token_resolver(token)
        if isawaitable(resolved):
            return await resolved
        return resolved

    try:
        return UUID(token)
    except Exception:
        raw = token.strip()
        if not raw:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            ) from None
        return uuid5(NAMESPACE_URL, f"aware:http_auth_token:{raw}")


__all__ = ["get_current_user_id", "set_token_resolver"]
