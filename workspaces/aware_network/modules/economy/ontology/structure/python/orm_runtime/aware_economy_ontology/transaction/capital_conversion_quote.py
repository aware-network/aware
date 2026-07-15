from __future__ import annotations

# Standard
from datetime import datetime
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology
from aware_economy_ontology.external_capital.external_capital_enums import ExternalCapitalConversionMode

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology.coin.coin import Coin
    from aware_economy_ontology.external_capital.external_capital_provider_route import ExternalCapitalProviderRoute


class CapitalConversionQuote(ORMModel):
    # Relationships
    provider_route: ExternalCapitalProviderRoute | None = Field(default=None, exclude=True)
    target_coin: Coin | None = Field(default=None, exclude=True)

    # Attributes
    captured_at: datetime
    conversion_mode: ExternalCapitalConversionMode
    expires_at: datetime | None = Field(default=None)
    external_amount_minor: int
    external_currency: str
    quote_hash: str
    quote_key: str
    source: str
    target_amount: Annotated[Decimal, DecimalWire()]

    # Foreign Keys
    provider_route_id: UUID = Field(description="Foreign key for CapitalConversionQuote.provider_route")
    target_coin_id: UUID = Field(description="Foreign key for CapitalConversionQuote.target_coin")

    @classmethod
    async def build(
        cls,
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

        payload = {
            "provider_route_id": provider_route_id,
            "target_coin_id": target_coin_id,
            "quote_key": quote_key,
            "quote_hash": quote_hash,
            "external_amount_minor": external_amount_minor,
            "external_currency": external_currency,
            "target_amount": target_amount,
            "conversion_mode": conversion_mode,
            "source": source,
            "captured_at": captured_at,
            "expires_at": expires_at,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CapitalConversionQuote):
            return value
        return CapitalConversionQuote.validate_invocation_value(value)


class CapitalConversionQuoteBuildInput(BaseModel):
    provider_route_id: UUID
    target_coin_id: UUID
    quote_key: str
    quote_hash: str
    external_amount_minor: int
    external_currency: str
    target_amount: Annotated[Decimal, DecimalWire()]
    conversion_mode: ExternalCapitalConversionMode
    source: str
    captured_at: datetime
    expires_at: datetime | None = Field(default=None)


class CapitalConversionQuoteBuildOutput(BaseModel):
    value: CapitalConversionQuote


FUNCTIONS = {
    "CapitalConversionQuote": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Captures the immutable external-to-Aware capital conversion accepted by one TransactionIntent.\n\nV0 accepts direct denomination only. The quote is contained by its\nTransactionIntent and has no independent lifecycle.",
                "is_constructor": True,
            },
            "input": CapitalConversionQuoteBuildInput,
            "output": CapitalConversionQuoteBuildOutput,
        },
    },
}

__all__ = [
    "CapitalConversionQuote",
    "CapitalConversionQuoteBuildInput",
    "CapitalConversionQuoteBuildOutput",
    "FUNCTIONS",
]
