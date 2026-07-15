from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Hub Ontology
from aware_hub_ontology.hub.hub_channel import HubChannelHead

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_hub.handlers.impl.hub._helpers import (
    clean_optional,
    clean_required,
    handler_session_or_none,
)
from aware_hub.stable_ids import stable_hub_channel_head_id
from aware_hub_ontology.hub.hub_artifact import HubArtifactRevision
from aware_hub_ontology.hub.hub_code_package_publication import HubCodePackagePublication

# --- AWARE: USER_IMPORTS END


async def move(
    hub_channel_head: HubChannelHead,
    revision_id: str,
    selector_key: str | None = None,
    artifact_revision_id: UUID | None = None,
    code_package_publication_id: UUID | None = None,
    updated_at_utc: str | None = None,
) -> HubChannelHead:
    """
    Move this channel head through its own mutation boundary.
    """

    # --- AWARE: LOGIC START move
    hub_channel_head.revision_id = clean_required(revision_id, "revision_id")
    hub_channel_head.selector_key = clean_optional(selector_key)
    hub_channel_head.artifact_revision_id = artifact_revision_id
    hub_channel_head.code_package_publication_id = code_package_publication_id
    hub_channel_head.updated_at_utc = clean_optional(updated_at_utc)

    session = handler_session_or_none()
    hub_channel_head.artifact_revision = (
        session.imap_get(HubArtifactRevision, artifact_revision_id)
        if session is not None and artifact_revision_id is not None
        else None
    )
    hub_channel_head.code_package_publication = (
        session.imap_get(HubCodePackagePublication, code_package_publication_id)
        if session is not None and code_package_publication_id is not None
        else None
    )
    return hub_channel_head
    # --- AWARE: LOGIC END move


async def build_via_hub_channel(
    hub_channel_id: UUID,
    artifact_family: str,
    artifact_key: str,
    revision_id: str,
    selector_key: str | None = None,
    artifact_revision_id: UUID | None = None,
    code_package_publication_id: UUID | None = None,
    updated_at_utc: str | None = None,
) -> HubChannelHead:
    """
    Create one channel head row scoped by channel, artifact family, and artifact key.
    """

    # --- AWARE: LOGIC START build_via_hub_channel
    family = clean_required(artifact_family, "artifact_family")
    key = clean_required(artifact_key, "artifact_key")
    revision_key = clean_required(revision_id, "revision_id")
    head_id = stable_hub_channel_head_id(
        hub_channel_id=hub_channel_id,
        artifact_family=family,
        artifact_key=key,
    )

    session = handler_session_or_none()
    if session is not None:
        existing = session.imap_get(HubChannelHead, head_id)
        if existing is not None:
            if (
                existing.hub_channel_id != hub_channel_id
                or existing.artifact_family != family
                or existing.artifact_key != key
            ):
                raise RuntimeError(f"HubChannelHead.build_via_hub_channel key mismatch: hub_channel_head_id={head_id}")
            return existing

    artifact_revision = (
        session.imap_get(HubArtifactRevision, artifact_revision_id)
        if session is not None and artifact_revision_id is not None
        else None
    )
    code_package_publication = (
        session.imap_get(HubCodePackagePublication, code_package_publication_id)
        if session is not None and code_package_publication_id is not None
        else None
    )
    return HubChannelHead(
        id=head_id,
        hub_channel_id=hub_channel_id,
        artifact_family=family,
        artifact_key=key,
        revision_id=revision_key,
        selector_key=clean_optional(selector_key),
        artifact_revision=artifact_revision,
        artifact_revision_id=artifact_revision_id,
        code_package_publication=code_package_publication,
        code_package_publication_id=code_package_publication_id,
        updated_at_utc=clean_optional(updated_at_utc),
    )
    # --- AWARE: LOGIC END build_via_hub_channel
