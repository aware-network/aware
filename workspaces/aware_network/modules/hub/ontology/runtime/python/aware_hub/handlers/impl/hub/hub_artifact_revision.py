from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Hub Ontology
from aware_hub_ontology.hub.hub_artifact import HubArtifactRevision

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_hub.handlers.impl.hub._helpers import (
    clean_optional,
    clean_required,
    handler_session_or_none,
    json_object,
)
from aware_hub.stable_ids import stable_hub_artifact_revision_id
from aware_hub_ontology.hub.hub_producer_provenance import HubProducerProvenance

# --- AWARE: USER_IMPORTS END


async def build_via_hub_artifact(
    hub_artifact_id: UUID,
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
    Create one immutable artifact payload lock.
    """

    # --- AWARE: LOGIC START build_via_hub_artifact
    revision_key = clean_required(revision_id, "revision_id")
    payload_url_norm = clean_required(payload_url, "payload_url")
    payload_sha256_norm = clean_required(payload_sha256, "payload_sha256")
    artifact_revision_id = stable_hub_artifact_revision_id(
        hub_artifact_id=hub_artifact_id,
        revision_id=revision_key,
    )

    session = handler_session_or_none()
    if session is not None:
        existing = session.imap_get(HubArtifactRevision, artifact_revision_id)
        if existing is not None:
            if (
                existing.hub_artifact_id != hub_artifact_id
                or existing.revision_id != revision_key
                or existing.payload_url != payload_url_norm
                or existing.payload_sha256 != payload_sha256_norm
            ):
                raise RuntimeError(
                    "HubArtifactRevision.build_via_hub_artifact immutable payload mismatch: "
                    f"hub_artifact_revision_id={artifact_revision_id}"
                )
            return existing

    producer_provenance = (
        session.imap_get(HubProducerProvenance, producer_provenance_id)
        if session is not None and producer_provenance_id is not None
        else None
    )
    return HubArtifactRevision(
        id=artifact_revision_id,
        hub_artifact_id=hub_artifact_id,
        revision_id=revision_key,
        payload_url=payload_url_norm,
        payload_sha256=payload_sha256_norm,
        selector_key=clean_optional(selector_key),
        target_ref=clean_optional(target_ref),
        media_type=clean_optional(media_type),
        size_bytes=size_bytes,
        producer_provenance=producer_provenance,
        producer_provenance_id=producer_provenance_id,
        published_at_utc=clean_optional(published_at_utc),
        metadata=json_object(metadata),
    )
    # --- AWARE: LOGIC END build_via_hub_artifact
