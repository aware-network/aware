from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Hub Ontology
from aware_hub_ontology.hub.hub_artifact import (
    HubArtifact,
    HubArtifactRevision,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_hub.handlers.impl.hub._helpers import (
    append_if_missing,
    clean_optional,
    clean_required,
    handler_session_or_none,
)
from aware_hub.handlers.impl.hub.hub_artifact_revision import (
    build_via_hub_artifact as build_via_hub_artifact,
)
from aware_hub.stable_ids import stable_hub_artifact_id

_HUB_ARTIFACT_COMPAT_EXPORTS = (build_via_hub_artifact,)

# --- AWARE: USER_IMPORTS END


async def publish_revision(
    hub_artifact: HubArtifact,
    revision_id: str,
    payload_url: str,
    payload_sha256: str,
    selector_key: str | None = None,
    target_ref: str | None = None,
    media_type: str | None = None,
    size_bytes: int | None = None,
    producer_provenance_id: UUID | None = None,
    published_at_utc: str | None = None,
    metadata: JsonObject = JsonObject(),
) -> HubArtifactRevision:
    """
    Publish one immutable revision under this artifact.
    """

    # --- AWARE: LOGIC START publish_revision
    if hub_artifact.id is None:
        raise RuntimeError("HubArtifact.publish_revision requires HubArtifact.id")

    revision = await HubArtifactRevision.build_via_hub_artifact(
        hub_artifact_id=hub_artifact.id,
        revision_id=revision_id,
        payload_url=payload_url,
        payload_sha256=payload_sha256,
        selector_key=selector_key,
        target_ref=target_ref,
        media_type=media_type,
        size_bytes=size_bytes,
        producer_provenance_id=producer_provenance_id,
        published_at_utc=published_at_utc,
        metadata=metadata,
    )
    append_if_missing(hub_artifact.revisions, revision)
    return revision
    # --- AWARE: LOGIC END publish_revision


async def build_via_hub_authority(
    hub_authority_id: UUID,
    artifact_family: str,
    artifact_key: str,
    title: str | None = None,
    description: str | None = None,
    media_type: str | None = None,
) -> HubArtifact:
    """
    Create one Hub-owned artifact identity.

    Contract:
    - `artifact_family` is open so Hub can carry CodePackage, deployment,
      and future artifact families without importing producer APIs.
    - Revisions carry immutable payload locks.
    """

    # --- AWARE: LOGIC START build_via_hub_authority
    family = clean_required(artifact_family, "artifact_family")
    key = clean_required(artifact_key, "artifact_key")
    artifact_id = stable_hub_artifact_id(
        hub_authority_id=hub_authority_id,
        artifact_family=family,
        artifact_key=key,
    )

    session = handler_session_or_none()
    if session is not None:
        existing = session.imap_get(HubArtifact, artifact_id)
        if existing is not None:
            if (
                existing.hub_authority_id != hub_authority_id
                or existing.artifact_family != family
                or existing.artifact_key != key
            ):
                raise RuntimeError(f"HubArtifact.build key mismatch: hub_artifact_id={artifact_id}")
            return existing

    return HubArtifact(
        id=artifact_id,
        hub_authority_id=hub_authority_id,
        artifact_family=family,
        artifact_key=key,
        title=clean_optional(title),
        description=clean_optional(description),
        media_type=clean_optional(media_type),
    )
    # --- AWARE: LOGIC END build_via_hub_authority
