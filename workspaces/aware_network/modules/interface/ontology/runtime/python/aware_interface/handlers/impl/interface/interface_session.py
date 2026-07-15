from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Interface Ontology
from aware_interface_ontology.interface.interface_enums import InterfaceSessionState
from aware_interface_ontology.interface.interface_session import InterfaceSession
from aware_interface_ontology.interface.interface_session_experience_session import InterfaceSessionExperienceSession

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_interface_ontology.stable_ids import stable_interface_session_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def mount_experience_session(
    interface_session: InterfaceSession,
    experience_session_id: UUID,
    status: str = "active",
    metadata_json: JsonObject | None = JsonObject(),
) -> InterfaceSessionExperienceSession:
    """
    Mount one committed ExperienceSession through this InterfaceSession.

    Contract:
    - Stable identity is InterfaceSession plus ExperienceSession.
    - ExperienceSession is an Experience-owned projection portal target.
    - Mounting records provenance only; it does not activate a profile,
      lens, Environment, AttentionSession, or ExperienceSession globally.
    """

    # --- AWARE: LOGIC START mount_experience_session
    if interface_session.id is None:
        raise RuntimeError("InterfaceSession.mount_experience_session requires InterfaceSession.id")
    if not isinstance(experience_session_id, UUID):
        raise TypeError("InterfaceSession.mount_experience_session requires " "experience_session_id (UUID)")

    mounted = await InterfaceSessionExperienceSession.build_via_interface_session(
        interface_session_id=interface_session.id,
        experience_session_id=experience_session_id,
        status=status,
        metadata_json=metadata_json,
    )
    for existing in interface_session.experience_sessions:
        if existing.id == mounted.id:
            return existing

    interface_session.experience_sessions.append(mounted)
    return mounted
    # --- AWARE: LOGIC END mount_experience_session


async def build_via_interface(
    interface_id: UUID,
    identity_session_id: UUID,
    name: str,
    state: InterfaceSessionState = InterfaceSessionState.active,
) -> InterfaceSession:
    """
    Construct one commit-backed client attachment under Interface and
    Interface parent scope.

    Contract:
    - Stable identity is Interface + Identity Session + normalized name.
    - Interface identifies the concrete shared door/client attachment.
    - Identity Session owns all participating actors; this durable session
      is not parented by one InterfaceIdentity.
    - This constructor does not register a transport connection or mint a
      bearer token.
    - Identity owns membership, roles, lifecycle, and provider sessions.
    """

    # --- AWARE: LOGIC START build_via_interface
    if not isinstance(interface_id, UUID):
        raise TypeError("InterfaceSession.build requires interface_id (UUID)")
    if not isinstance(identity_session_id, UUID):
        raise TypeError("InterfaceSession.build requires identity_session_id (UUID)")
    normalized_name = name.strip() if isinstance(name, str) else ""
    if not normalized_name:
        raise ValueError("InterfaceSession.build requires non-empty name")

    interface_session_id = stable_interface_session_id(
        interface_id=interface_id,
        identity_session_id=identity_session_id,
        name=normalized_name,
    )
    try:
        session = current_handler_session()
    except RuntimeError:
        session = None
    if session is not None:
        existing = session.imap_get(InterfaceSession, interface_session_id)
        if existing is not None:
            return existing

    return InterfaceSession(
        id=interface_session_id,
        interface_id=interface_id,
        identity_session=None,
        identity_session_id=identity_session_id,
        name=normalized_name,
        state=state,
    )
    # --- AWARE: LOGIC END build_via_interface
