from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Hub Ontology
from aware_hub_ontology.hub.hub_enums import HubAuthorityVisibility
from aware_hub_ontology.hub.hub_channel import (
    HubChannel,
    HubChannelHead,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_hub.handlers.impl.hub._helpers import (
    append_if_missing,
    clean_optional,
    clean_required,
    first_by_id,
    handler_session_or_none,
)
from aware_hub.handlers.impl.hub.hub_channel_head import (
    build_via_hub_channel as build_via_hub_channel,
    move as move,
)
from aware_hub.stable_ids import (
    stable_hub_channel_head_id,
    stable_hub_channel_id,
)

_HUB_CHANNEL_COMPAT_EXPORTS = (build_via_hub_channel, move)

# --- AWARE: USER_IMPORTS END


async def upsert_head(
    hub_channel: HubChannel,
    artifact_family: str,
    artifact_key: str,
    revision_id: str,
    selector_key: str | None = None,
    artifact_revision_id: UUID | None = None,
    code_package_publication_id: UUID | None = None,
    updated_at_utc: str | None = None,
) -> HubChannelHead:
    """
    Move a channel head to one artifact revision/publication.
    """

    # --- AWARE: LOGIC START upsert_head
    if hub_channel.id is None:
        raise RuntimeError("HubChannel.upsert_head requires HubChannel.id")

    family = clean_required(artifact_family, "artifact_family")
    key = clean_required(artifact_key, "artifact_key")
    head_id = stable_hub_channel_head_id(
        hub_channel_id=hub_channel.id,
        artifact_family=family,
        artifact_key=key,
    )
    session = handler_session_or_none()
    existing = session.imap_get(HubChannelHead, head_id) if session is not None else None
    if existing is None:
        existing = first_by_id(hub_channel.heads, head_id)

    if existing is not None:
        append_if_missing(hub_channel.heads, existing)
        return await existing.move(
            revision_id=revision_id,
            selector_key=selector_key,
            artifact_revision_id=artifact_revision_id,
            code_package_publication_id=code_package_publication_id,
            updated_at_utc=updated_at_utc,
        )

    head = await HubChannelHead.build_via_hub_channel(
        hub_channel_id=hub_channel.id,
        artifact_family=family,
        artifact_key=key,
        revision_id=revision_id,
        selector_key=selector_key,
        artifact_revision_id=artifact_revision_id,
        code_package_publication_id=code_package_publication_id,
        updated_at_utc=updated_at_utc,
    )
    append_if_missing(hub_channel.heads, head)
    return head
    # --- AWARE: LOGIC END upsert_head


async def build_via_hub_authority(
    hub_authority_id: UUID,
    channel_key: str,
    title: str | None = None,
    description: str | None = None,
    visibility: HubAuthorityVisibility = HubAuthorityVisibility.public,
) -> HubChannel:
    """
    Create one Hub-owned channel.
    """

    # --- AWARE: LOGIC START build_via_hub_authority
    channel_key_norm = clean_required(channel_key, "channel_key")
    channel_id = stable_hub_channel_id(
        hub_authority_id=hub_authority_id,
        channel_key=channel_key_norm,
    )
    session = handler_session_or_none()
    if session is not None:
        existing = session.imap_get(HubChannel, channel_id)
        if existing is not None:
            if existing.hub_authority_id != hub_authority_id or existing.channel_key != channel_key_norm:
                raise RuntimeError(f"HubChannel.build_via_hub_authority key mismatch: hub_channel_id={channel_id}")
            return existing

    return HubChannel(
        id=channel_id,
        hub_authority_id=hub_authority_id,
        channel_key=channel_key_norm,
        title=clean_optional(title),
        description=clean_optional(description),
        visibility=visibility,
    )
    # --- AWARE: LOGIC END build_via_hub_authority
