from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Code
from aware_code.types import JsonObject

# Hub Ontology
from aware_hub_ontology.hub.hub_producer_provenance import HubProducerProvenance

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_hub.handlers.impl.hub._helpers import (
    clean_optional,
    clean_required,
    handler_session_or_none,
    json_object,
)
from aware_hub.stable_ids import stable_hub_producer_provenance_id

# --- AWARE: USER_IMPORTS END


async def build(
    producer_kind: str,
    producer_key: str = "default",
    provenance_key: str = "default",
    producer_revision_id: str | None = None,
    source_revision_id: str | None = None,
    source_revision_kind: str | None = None,
    materialization_ref: str | None = None,
    build_ref: str | None = None,
    metadata: JsonObject = JsonObject(),
) -> HubProducerProvenance:
    """
    Create one generic producer provenance record.

    Contract:
    - Producer-specific revision fields remain opaque to Hub.
    - WorkspaceRevision can appear here without making Workspace API part of Hub.
    """

    # --- AWARE: LOGIC START build
    kind = clean_required(producer_kind, "producer_kind")
    key = clean_required(producer_key, "producer_key")
    provenance_key_norm = clean_required(provenance_key, "provenance_key")
    provenance_id = stable_hub_producer_provenance_id(
        producer_kind=kind,
        producer_key=key,
        provenance_key=provenance_key_norm,
    )

    session = handler_session_or_none()
    if session is not None:
        existing = session.imap_get(HubProducerProvenance, provenance_id)
        if existing is not None:
            if (
                existing.producer_kind != kind
                or existing.producer_key != key
                or existing.provenance_key != provenance_key_norm
            ):
                raise RuntimeError(
                    f"HubProducerProvenance.build key mismatch: hub_producer_provenance_id={provenance_id}"
                )
            return existing

    return HubProducerProvenance(
        id=provenance_id,
        producer_kind=kind,
        producer_key=key,
        provenance_key=provenance_key_norm,
        producer_revision_id=clean_optional(producer_revision_id),
        source_revision_id=clean_optional(source_revision_id),
        source_revision_kind=clean_optional(source_revision_kind),
        materialization_ref=clean_optional(materialization_ref),
        build_ref=clean_optional(build_ref),
        metadata=json_object(metadata),
    )
    # --- AWARE: LOGIC END build
