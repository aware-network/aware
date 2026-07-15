from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Sdk Ontology
from aware_sdk_ontology.sdk.sdk_operation_call import SdkOperationCall

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_sdk_ontology.stable_ids import stable_sdk_operation_call_id

# --- AWARE: USER_IMPORTS END


async def create_via_sdk_operation(
    sdk_operation_id: UUID,
    call_key: UUID,
    request_hash: str,
    description: str | None = None,
    context_hash: str | None = None,
    status: str = "pending",
    api_call_id: UUID | None = None,
) -> SdkOperationCall:
    """
    Create one SDK operation call receipt under SdkOperation.

    Contract:
    - Parent `SdkOperation` scope is propagated by constructor lowering.
    - `request_hash` is the durable payload fingerprint until typed SDK request
      value instances are introduced.
    - `api_call_id` links to API ingress provenance without making API own SDK
      dispatch truth.
    """

    # --- AWARE: LOGIC START create_via_sdk_operation
    normalized_request_hash = (request_hash or "").strip()
    if not normalized_request_hash:
        raise RuntimeError("SdkOperationCall.create_via_sdk_operation requires non-empty request_hash")

    return SdkOperationCall(
        id=stable_sdk_operation_call_id(
            sdk_operation_id=sdk_operation_id,
            call_key=call_key,
        ),
        sdk_operation_id=sdk_operation_id,
        call_key=call_key,
        request_hash=normalized_request_hash,
        description=(description or "").strip() or None,
        context_hash=(context_hash or "").strip() or None,
        status=(status or "").strip() or "pending",
        api_call_id=api_call_id,
    )
    # --- AWARE: LOGIC END create_via_sdk_operation
