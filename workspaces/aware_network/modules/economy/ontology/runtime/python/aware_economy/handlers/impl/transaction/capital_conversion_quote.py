from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

# Economy Ontology
from aware_economy_ontology.external_capital.external_capital_enums import ExternalCapitalConversionMode
from aware_economy_ontology.transaction.capital_conversion_quote import CapitalConversionQuote

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Economy Ontology
from aware_economy_ontology.stable_ids import (
    stable_capital_conversion_quote_id,
    stable_coin_id,
)

# Economy Runtime
from aware_economy.capital_amount import positive_amount

# --- AWARE: USER_IMPORTS END


async def build(
    provider_route_id: UUID,
    target_coin_id: UUID,
    quote_key: str,
    quote_hash: str,
    external_amount_minor: int,
    external_currency: str,
    target_amount: Annotated[Decimal, DecimalWire()],
    conversion_mode: ExternalCapitalConversionMode,
    source: str,
    captured_at: datetime,
    expires_at: datetime | None = None,
) -> CapitalConversionQuote:
    """
    Captures the immutable external-to-Aware capital conversion accepted by one TransactionIntent.

    V0 accepts direct denomination only. The quote is contained by its
    TransactionIntent and has no independent lifecycle.
    """

    # --- AWARE: LOGIC START build
    quote_key = quote_key.strip().casefold()
    if not quote_key:
        raise ValueError("capital_conversion_quote.build requires quote_key")

    quote_hash = quote_hash.strip().casefold()
    if len(quote_hash) != 64 or any(character not in "0123456789abcdef" for character in quote_hash):
        raise ValueError("capital_conversion_quote.build requires a SHA-256 quote_hash")

    external_currency = external_currency.strip().upper()
    if len(external_currency) != 3 or not external_currency.isascii() or not external_currency.isalpha():
        raise ValueError("capital_conversion_quote.build requires a three-letter ASCII external_currency")
    if external_amount_minor <= 0:
        raise ValueError("capital_conversion_quote.build requires external_amount_minor > 0")
    if conversion_mode != ExternalCapitalConversionMode.direct_denomination:
        raise ValueError("capital_conversion_quote.build supports direct_denomination only")
    if target_coin_id != stable_coin_id(symbol=external_currency):
        raise ValueError(
            "capital_conversion_quote.build direct denomination requires target Coin to match external_currency"
        )

    source = source.strip().casefold()
    if source != "external_capital_provider_route":
        raise ValueError("capital_conversion_quote.build requires external_capital_provider_route source")
    if captured_at.tzinfo is None or captured_at.utcoffset() is None:
        raise ValueError("capital_conversion_quote.build requires timezone-aware captured_at")
    if expires_at is not None:
        if expires_at.tzinfo is None or expires_at.utcoffset() is None:
            raise ValueError("capital_conversion_quote.build requires timezone-aware expires_at")
        if expires_at <= captured_at:
            raise ValueError("capital_conversion_quote.build requires expires_at after captured_at")

    target_amount = positive_amount(
        target_amount,
        field_name="capital conversion target_amount",
    )
    return CapitalConversionQuote(
        id=stable_capital_conversion_quote_id(quote_key=quote_key),
        provider_route_id=provider_route_id,
        target_coin_id=target_coin_id,
        quote_key=quote_key,
        quote_hash=quote_hash,
        external_amount_minor=external_amount_minor,
        external_currency=external_currency,
        target_amount=target_amount,
        conversion_mode=conversion_mode,
        source=source,
        captured_at=captured_at,
        expires_at=expires_at,
    )
    # --- AWARE: LOGIC END build
