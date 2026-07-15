from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Economy Ontology
from aware_economy_ontology.transaction.provider_lifecycle_receipt_enums import (
    ProviderLifecycleEventKind,
    ProviderLifecycleStatus,
)
from aware_economy_ontology.transaction.provider_lifecycle_receipt import ProviderLifecycleReceipt

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Economy Ontology
from aware_economy_ontology.stable_ids import stable_provider_lifecycle_receipt_id

# Economy Runtime
from aware_economy.capital_amount import (
    non_negative_amount,
    positive_amount,
)

# --- AWARE: USER_IMPORTS END


async def record(
    provider_finance_entity_id: UUID,
    provider_key: str,
    provider_lifecycle_object_id: str,
    provider_lifecycle_effect_key: str,
    provider_event_id: str,
    wallet_finance_entity_id: UUID,
    wallet_id: UUID,
    wallet_public_id: UUID,
    coin_id: UUID,
    amount: Annotated[Decimal, DecimalWire()],
    event_kind: ProviderLifecycleEventKind,
    status: ProviderLifecycleStatus,
    idempotency_key: str,
    previous_balance: Annotated[Decimal, DecimalWire()],
    new_balance: Annotated[Decimal, DecimalWire()],
    previous_held_balance: Annotated[Decimal, DecimalWire()],
    new_held_balance: Annotated[Decimal, DecimalWire()],
    previous_available_balance: Annotated[Decimal, DecimalWire()],
    new_available_balance: Annotated[Decimal, DecimalWire()],
    provider_payment_reference: str,
    provider_payload_hash: str,
    external_created_at: datetime,
    transaction_id: UUID,
    transaction_external_id: UUID,
    metadata_json: JsonObject | None = None,
) -> ProviderLifecycleReceipt:
    """
    Records a provider lifecycle event as Aware Economy receipt truth.

    Receipt: one provider lifecycle object/effect stage correlated to the
    original external-ingress transaction. Provider evidence never selects
    Aware wallet coordinates; Economy derives them from committed funding
    truth and remains the only WalletBalance mutation authority.
    """

    # --- AWARE: LOGIC START record
    provider_key_norm = provider_key.strip().casefold()
    provider_lifecycle_object_id_norm = provider_lifecycle_object_id.strip()
    provider_lifecycle_effect_key_norm = provider_lifecycle_effect_key.strip().casefold()
    provider_event_id_norm = provider_event_id.strip()
    idempotency_key_norm = idempotency_key.strip()
    provider_payment_reference_norm = provider_payment_reference.strip()
    provider_payload_hash_norm = provider_payload_hash.strip().casefold()
    if not provider_key_norm:
        raise ValueError("provider_lifecycle_receipt.record requires provider_key")
    if not provider_lifecycle_object_id_norm:
        raise ValueError("provider_lifecycle_receipt.record requires provider_lifecycle_object_id")
    if not provider_lifecycle_effect_key_norm:
        raise ValueError("provider_lifecycle_receipt.record requires provider_lifecycle_effect_key")
    if not provider_event_id_norm:
        raise ValueError("provider_lifecycle_receipt.record requires provider_event_id")
    if not idempotency_key_norm:
        raise ValueError("provider_lifecycle_receipt.record requires idempotency_key")
    if not provider_payment_reference_norm:
        raise ValueError("provider_lifecycle_receipt.record requires provider_payment_reference")
    if not provider_payload_hash_norm:
        raise ValueError("provider_lifecycle_receipt.record requires provider_payload_hash")

    amount_value = positive_amount(
        amount,
        field_name="provider lifecycle amount",
    )
    if provider_lifecycle_effect_key_norm != event_kind.value:
        raise ValueError("provider lifecycle effect key must match the event kind")

    receipt_id = stable_provider_lifecycle_receipt_id(
        provider_finance_entity_id=provider_finance_entity_id,
        provider_key=provider_key_norm,
        provider_lifecycle_object_id=provider_lifecycle_object_id_norm,
        provider_lifecycle_effect_key=provider_lifecycle_effect_key_norm,
    )

    return ProviderLifecycleReceipt(
        id=receipt_id,
        provider_finance_entity_id=provider_finance_entity_id,
        provider_key=provider_key_norm,
        provider_lifecycle_object_id=provider_lifecycle_object_id_norm,
        provider_lifecycle_effect_key=provider_lifecycle_effect_key_norm,
        provider_event_id=provider_event_id_norm,
        wallet_finance_entity_id=wallet_finance_entity_id,
        wallet_id=wallet_id,
        wallet_public_id=wallet_public_id,
        coin_id=coin_id,
        amount=amount_value,
        event_kind=event_kind,
        status=status,
        idempotency_key=idempotency_key_norm,
        previous_balance=non_negative_amount(
            previous_balance,
            field_name="provider lifecycle previous_balance",
        ),
        new_balance=non_negative_amount(
            new_balance,
            field_name="provider lifecycle new_balance",
        ),
        previous_held_balance=non_negative_amount(
            previous_held_balance,
            field_name="provider lifecycle previous_held_balance",
        ),
        new_held_balance=non_negative_amount(
            new_held_balance,
            field_name="provider lifecycle new_held_balance",
        ),
        previous_available_balance=non_negative_amount(
            previous_available_balance,
            field_name="provider lifecycle previous_available_balance",
        ),
        new_available_balance=non_negative_amount(
            new_available_balance,
            field_name="provider lifecycle new_available_balance",
        ),
        provider_payment_reference=provider_payment_reference_norm,
        provider_payload_hash=provider_payload_hash_norm,
        external_created_at=external_created_at,
        metadata_json=metadata_json,
        transaction_id=transaction_id,
        transaction_external_id=transaction_external_id,
    )
    # --- AWARE: LOGIC END record
