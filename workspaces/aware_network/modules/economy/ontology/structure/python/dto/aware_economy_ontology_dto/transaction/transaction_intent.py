from __future__ import annotations

# Standard
from datetime import datetime
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology Dto
from aware_economy_ontology_dto.transaction.transaction_intent_enums import TransactionIntentStatus

# Types
from aware_types import (
    DecimalWire,
    JsonObject,
)

if TYPE_CHECKING:
    from aware_economy_ontology_dto.coin.coin import Coin
    from aware_economy_ontology_dto.external_capital.external_capital_provider_config import (
        ExternalCapitalProviderConfig,
    )
    from aware_economy_ontology_dto.finance.finance_entity import FinanceEntity
    from aware_economy_ontology_dto.transaction.capital_conversion_quote import CapitalConversionQuote
    from aware_economy_ontology_dto.transaction.transaction_intent_external_expiration import (
        TransactionIntentExternalExpiration,
    )
    from aware_economy_ontology_dto.wallet.wallet import Wallet
    from aware_economy_ontology_dto.wallet.wallet_public import WalletPublic


class TransactionIntent(BaseModel):
    # Relationships
    capital_conversion_quote: CapitalConversionQuote | None = Field(default=None)
    coin: Coin | None = Field(default=None)
    external_expirations: list[TransactionIntentExternalExpiration] = Field(default_factory=list)
    provider_config: ExternalCapitalProviderConfig | None = Field(default=None)
    recipient_finance_entity: FinanceEntity | None = Field(default=None)
    recipient_wallet: Wallet | None = Field(default=None)
    recipient_wallet_public: WalletPublic | None = Field(default=None)

    # Attributes
    amount: Annotated[Decimal, DecimalWire()]
    created_at: datetime
    funding_intent_key: str
    idempotency_key: str
    metadata_json: JsonObject | None = Field(default=None)
    provider_key: str
    status: TransactionIntentStatus = Field(default=TransactionIntentStatus.created)
    updated_at: datetime | None = Field(default=None)
