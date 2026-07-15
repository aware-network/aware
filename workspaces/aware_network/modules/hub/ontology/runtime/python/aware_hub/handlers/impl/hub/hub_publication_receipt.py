from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Hub Ontology
from aware_hub_ontology.hub.hub_enums import HubPublicationReceiptStatus
from aware_hub_ontology.hub.hub_publication_receipt import HubPublicationReceipt

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_hub.handlers.impl.hub._helpers import (
    clean_optional,
    clean_required,
    handler_session_or_none,
    json_object,
)
from aware_hub.stable_ids import stable_hub_publication_receipt_id
from aware_hub_ontology.hub.hub_artifact import HubArtifactRevision
from aware_hub_ontology.hub.hub_code_package_publication import HubCodePackagePublication

# --- AWARE: USER_IMPORTS END


async def build_via_hub_authority(
    hub_authority_id: UUID,
    receipt_key: str,
    operation: str,
    status: HubPublicationReceiptStatus = HubPublicationReceiptStatus.accepted,
    publisher_execution_id: str | None = None,
    idempotency_key: str | None = None,
    artifact_revision_id: UUID | None = None,
    code_package_publication_id: UUID | None = None,
    authority_source_url: str | None = None,
    message: str | None = None,
    recorded_at_utc: str | None = None,
    detail: JsonObject = JsonObject(),
) -> HubPublicationReceipt:
    """
    Create one Hub authority receipt.
    """

    # --- AWARE: LOGIC START build_via_hub_authority
    receipt_key_norm = clean_required(receipt_key, "receipt_key")
    operation_norm = clean_required(operation, "operation")
    receipt_id = stable_hub_publication_receipt_id(
        hub_authority_id=hub_authority_id,
        receipt_key=receipt_key_norm,
    )
    session = handler_session_or_none()
    if session is not None:
        existing = session.imap_get(HubPublicationReceipt, receipt_id)
        if existing is not None:
            if existing.hub_authority_id != hub_authority_id or existing.receipt_key != receipt_key_norm:
                raise RuntimeError(
                    "HubPublicationReceipt.build_via_hub_authority key mismatch: "
                    f"hub_publication_receipt_id={receipt_id}"
                )
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
    return HubPublicationReceipt(
        id=receipt_id,
        hub_authority_id=hub_authority_id,
        receipt_key=receipt_key_norm,
        operation=operation_norm,
        status=status,
        publisher_execution_id=clean_optional(publisher_execution_id),
        idempotency_key=clean_optional(idempotency_key),
        artifact_revision=artifact_revision,
        artifact_revision_id=artifact_revision_id,
        code_package_publication=code_package_publication,
        code_package_publication_id=code_package_publication_id,
        authority_source_url=clean_optional(authority_source_url),
        message=clean_optional(message),
        recorded_at_utc=clean_optional(recorded_at_utc),
        detail=json_object(detail),
    )
    # --- AWARE: LOGIC END build_via_hub_authority
