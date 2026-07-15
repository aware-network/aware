from __future__ import annotations

import os
from uuid import UUID

from fastapi import Depends, HTTPException, status

from aware_comms.http.utils import auth_scheme


def _is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _actor_id_matches_public_key(*, actor_id: UUID, public_key: str) -> bool:
    """Verify anti-claim: actor_id must be derivable from the authenticated public key.

    We don't know the identity type at transport time, so we accept any of the
    known IdentityType stable-id derivations.
    """

    from aware_identity.auth.public_key.generator import canonicalize_ed25519_public_key
    from aware_identity_ontology.stable_ids import stable_actor_id, stable_identity_id

    canonical_public_key, _ = canonicalize_ed25519_public_key(public_key)
    for identity_type_value in ("human", "agent", "organization", "system"):
        identity_id = stable_identity_id(
            public_key=canonical_public_key,
            type=identity_type_value,
        )
        if stable_actor_id(identity_id=identity_id) == actor_id:
            return True
    return False


async def resolve_actor_id_from_bearer_token(token: str) -> UUID:
    """Resolve an authenticated actor_id from an HTTP Bearer token.

    v1 (preferred):
    - token is the `interface_session_network_binding_id` (UUID) returned by
      `interface_session_register` on the active websocket.
    - token is valid only while the websocket binding is active and authenticated.

    Legacy (optional, dev-only):
    - token is an actor_id UUID.
    """

    raw = (token or "").strip()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    try:
        token_uuid = UUID(raw)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        ) from None

    from aware_network.communications.identity_session_manager import (
        IdentitySessionManager,
    )
    from aware_network.communications.interface_session_binding_manager import (
        InterfaceSessionBindingManager,
    )

    binding = (
        await InterfaceSessionBindingManager.instance().get_binding_by_session_token(
            session_token=token_uuid
        )
    )
    if binding is None:
        if _is_truthy(os.getenv("AWARE_HTTP_ALLOW_LEGACY_ACTOR_ID_BEARER")):
            return token_uuid
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated",
        )

    session = IdentitySessionManager.instance().get_session(
        connection_id=binding.connection_id
    )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated",
        )

    if not _actor_id_matches_public_key(
        actor_id=binding.identity_id,
        public_key=session.public_key,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated",
        )

    return binding.identity_id


async def get_current_actor_id(token: str = Depends(auth_scheme.get_token)) -> UUID:
    return await resolve_actor_id_from_bearer_token(token)


__all__ = ["get_current_actor_id", "resolve_actor_id_from_bearer_token"]
