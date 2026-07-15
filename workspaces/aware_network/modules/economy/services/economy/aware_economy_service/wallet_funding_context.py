from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from aware_economy.capital_amount import positive_amount
from aware_economy_ontology_orm_models.coin.coin import Coin
from aware_economy_ontology_orm_models.coin.coin_enums import CoinType
from aware_economy_ontology_orm_models.external_capital.external_capital_enums import (
    ExternalCapitalConversionMode,
    ExternalCapitalProviderStatus,
    ExternalCapitalRouteStatus,
)
from aware_economy_ontology_orm_models.external_capital.external_capital_provider_config import (
    ExternalCapitalProviderConfig,
)
from aware_economy_ontology_orm_models.external_capital.external_capital_provider_route import (
    ExternalCapitalProviderRoute,
)
from aware_economy_ontology_orm_models.finance.finance_entity import FinanceEntity
from aware_economy_ontology_orm_models.transaction.capital_conversion_quote import (
    CapitalConversionQuote,
)
from aware_economy_ontology_orm_models.transaction.transaction_intent import (
    TransactionIntent,
)
from aware_economy_ontology_orm_models.wallet.wallet import Wallet
from aware_economy_ontology_orm_models.stable_ids import stable_wallet_public_id


@dataclass(frozen=True, slots=True)
class ResolvedWalletFundingPrepareContext:
    provider_config: ExternalCapitalProviderConfig
    provider_route: ExternalCapitalProviderRoute
    provider_finance_entity: FinanceEntity
    recipient_finance_entity: FinanceEntity
    recipient_wallet: Wallet
    recipient_wallet_public_id: UUID
    coin: Coin
    amount: Decimal


@dataclass(frozen=True, slots=True)
class ResolvedWalletFundingContext:
    intent: TransactionIntent
    quote: CapitalConversionQuote
    provider_config: ExternalCapitalProviderConfig
    provider_route: ExternalCapitalProviderRoute
    provider_finance_entity: FinanceEntity
    recipient_finance_entity: FinanceEntity
    recipient_wallet: Wallet
    recipient_wallet_public_id: UUID
    coin: Coin


async def resolve_wallet_funding_prepare_context(
    *,
    admitted_actor_id: UUID,
    target_wallet_id: UUID,
    coin_id: UUID,
    provider_key: str,
    amount: Decimal,
) -> ResolvedWalletFundingPrepareContext:
    provider_key = _required_key(provider_key, field_name="provider_key").casefold()
    amount = positive_amount(amount, field_name="wallet funding amount")

    recipient_matches = await FinanceEntity.many(identity_id=admitted_actor_id)
    if len(recipient_matches) != 1:
        raise ValueError(
            "wallet funding requires exactly one FinanceEntity for the admitted actor"
        )
    recipient_finance_entity = recipient_matches[0]
    if recipient_finance_entity.wallet_id != target_wallet_id:
        raise ValueError(
            "wallet funding target Wallet is not owned by the admitted actor FinanceEntity"
        )

    recipient_wallet = await Wallet.by_id(target_wallet_id)
    if recipient_wallet is None:
        raise ValueError("wallet funding target Wallet is not ready")
    recipient_wallet_public_id = stable_wallet_public_id(
        public_key=recipient_wallet.public_key
    )

    coin = await Coin.by_id(coin_id)
    if coin is None:
        raise ValueError("wallet funding target Coin does not exist")
    if coin.type != CoinType.fiat:
        raise ValueError(
            "wallet funding direct denomination requires a fiat target Coin"
        )

    provider_matches = await ExternalCapitalProviderConfig.many(
        provider_key=provider_key,
        status=ExternalCapitalProviderStatus.active,
    )
    if len(provider_matches) != 1:
        raise ValueError(
            "wallet funding requires exactly one active provider configuration"
        )
    provider_config = provider_matches[0]

    provider_finance_entity = await FinanceEntity.by_id(
        provider_config.provider_finance_entity_id
    )
    if provider_finance_entity is None:
        raise ValueError(
            "wallet funding provider configuration references a missing FinanceEntity"
        )

    route_matches = await ExternalCapitalProviderRoute.many(
        external_capital_provider_config_id=provider_config.id,
        target_coin_id=coin_id,
        status=ExternalCapitalRouteStatus.active,
    )
    if len(route_matches) != 1:
        raise ValueError(
            "wallet funding requires exactly one active provider route for the target Coin"
        )
    provider_route = route_matches[0]
    external_amount_minor = _validate_direct_denomination(
        provider_route=provider_route,
        coin=coin,
        amount=amount,
    )
    if (
        provider_route.min_external_amount_minor is not None
        and external_amount_minor < provider_route.min_external_amount_minor
    ):
        raise ValueError("wallet funding amount is below the provider route minimum")
    if (
        provider_route.max_external_amount_minor is not None
        and external_amount_minor > provider_route.max_external_amount_minor
    ):
        raise ValueError("wallet funding amount is above the provider route maximum")

    return ResolvedWalletFundingPrepareContext(
        provider_config=provider_config,
        provider_route=provider_route,
        provider_finance_entity=provider_finance_entity,
        recipient_finance_entity=recipient_finance_entity,
        recipient_wallet=recipient_wallet,
        recipient_wallet_public_id=recipient_wallet_public_id,
        coin=coin,
        amount=amount,
    )


async def resolve_wallet_funding_context_models(
    *,
    intent: TransactionIntent,
    admitted_provider_actor_id: UUID,
    require_active_provider_route: bool = True,
) -> ResolvedWalletFundingContext:
    quote_id = intent.capital_conversion_quote_id
    if quote_id is None:
        raise ValueError(
            "wallet funding context requires the contained capital conversion quote"
        )
    quote = await CapitalConversionQuote.by_id(quote_id)
    if quote is None:
        raise ValueError(
            "wallet funding context capital conversion quote is missing from the "
            "Economy replica"
        )

    provider_config = await ExternalCapitalProviderConfig.by_id(
        intent.provider_config_id
    )
    if provider_config is None:
        raise ValueError("wallet funding context provider configuration is missing")
    if (
        require_active_provider_route
        and provider_config.status != ExternalCapitalProviderStatus.active
    ):
        raise ValueError("wallet funding context provider configuration is inactive")
    if provider_config.provider_key != intent.provider_key:
        raise ValueError("wallet funding context provider key mismatch")

    provider_route = await ExternalCapitalProviderRoute.by_id(quote.provider_route_id)
    if provider_route is None:
        raise ValueError("wallet funding context provider route is missing")
    if (
        require_active_provider_route
        and provider_route.status != ExternalCapitalRouteStatus.active
    ):
        raise ValueError("wallet funding context provider route is inactive")
    if provider_route.external_capital_provider_config_id != provider_config.id:
        raise ValueError("wallet funding context provider route/config mismatch")

    provider_finance_entity = await FinanceEntity.by_id(
        provider_config.provider_finance_entity_id
    )
    recipient_finance_entity = await FinanceEntity.by_id(
        intent.recipient_finance_entity_id
    )
    recipient_wallet = await Wallet.by_id(intent.recipient_wallet_id)
    coin = await Coin.by_id(intent.coin_id)
    if provider_finance_entity is None:
        raise ValueError("wallet funding context provider FinanceEntity is missing")
    if provider_finance_entity.identity_id != admitted_provider_actor_id:
        raise ValueError(
            "wallet funding context is not authorized for the admitted provider actor"
        )
    if recipient_finance_entity is None:
        raise ValueError("wallet funding context recipient FinanceEntity is missing")
    if recipient_wallet is None:
        raise ValueError("wallet funding context recipient Wallet is missing")
    if coin is None:
        raise ValueError("wallet funding context target Coin is missing")
    if recipient_finance_entity.wallet_id != recipient_wallet.id:
        raise ValueError("wallet funding context FinanceEntity/Wallet mismatch")
    recipient_wallet_public_id = stable_wallet_public_id(
        public_key=recipient_wallet.public_key
    )
    if recipient_wallet_public_id != intent.recipient_wallet_public_id:
        raise ValueError("wallet funding context WalletPublic mismatch")

    external_amount_minor = _validate_direct_denomination(
        provider_route=provider_route,
        coin=coin,
        amount=positive_amount(intent.amount, field_name="wallet funding amount"),
    )
    if quote.target_coin_id != intent.coin_id:
        raise ValueError("wallet funding context quote target Coin mismatch")
    if quote.target_amount != intent.amount:
        raise ValueError("wallet funding context quote target amount mismatch")
    if quote.external_amount_minor != external_amount_minor:
        raise ValueError("wallet funding context quote external amount mismatch")
    if quote.external_currency != provider_route.external_currency:
        raise ValueError("wallet funding context quote external currency mismatch")
    if quote.conversion_mode != provider_route.conversion_mode:
        raise ValueError("wallet funding context quote conversion mode mismatch")
    if quote.source != "external_capital_provider_route":
        raise ValueError("wallet funding context quote source mismatch")

    return ResolvedWalletFundingContext(
        intent=intent,
        quote=quote,
        provider_config=provider_config,
        provider_route=provider_route,
        provider_finance_entity=provider_finance_entity,
        recipient_finance_entity=recipient_finance_entity,
        recipient_wallet=recipient_wallet,
        recipient_wallet_public_id=recipient_wallet_public_id,
        coin=coin,
    )


def _validate_direct_denomination(
    *,
    provider_route: ExternalCapitalProviderRoute,
    coin: Coin,
    amount: Decimal,
) -> int:
    if (
        provider_route.conversion_mode
        != ExternalCapitalConversionMode.direct_denomination
    ):
        raise ValueError("wallet funding supports direct denomination only")
    if provider_route.external_currency != coin.symbol.upper():
        raise ValueError("wallet funding provider route currency/Coin mismatch")
    exponent = provider_route.external_minor_unit_exponent
    if exponent < 0 or exponent > 18:
        raise ValueError("wallet funding provider route minor-unit exponent is invalid")
    if exponent != coin.decimals:
        raise ValueError(
            "wallet funding direct-denomination route exponent must match Coin decimals"
        )
    external_amount = amount * (Decimal(10) ** exponent)
    if external_amount != external_amount.to_integral_value():
        raise ValueError("wallet funding amount exceeds provider minor-unit precision")
    return int(external_amount)


def _required_key(value: str, *, field_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


__all__ = [
    "ResolvedWalletFundingContext",
    "ResolvedWalletFundingPrepareContext",
    "resolve_wallet_funding_context_models",
    "resolve_wallet_funding_prepare_context",
]
