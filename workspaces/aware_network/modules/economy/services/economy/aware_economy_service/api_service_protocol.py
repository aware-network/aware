from __future__ import annotations

# pyright: reportMissingImports=false

from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from aware_economy.finance_readiness import (
    EconomyFinanceReadinessOperationContext,
    ensure_finance_entity as ensure_finance_entity_runtime,
    resolve_economy_finance_readiness_runtime_context,
    resolve_finance_entity_readiness as resolve_finance_entity_readiness_runtime,
)
from aware_economy.price_reservation_settlement import (
    build_economy_price_lane,
    finalize_price_reservation,
    reserve_price_reservation,
)
from aware_economy.smart_contract_settlement import (
    EconomySmartContractSettlementOperationContext,
    ensure_service_operation_permit as ensure_service_operation_permit_runtime,
    finalize_smart_contract_settlement as finalize_smart_contract_settlement_runtime,
    prepare_smart_contract_reservation as prepare_smart_contract_reservation_runtime,
    release_smart_contract_reservation as release_smart_contract_reservation_runtime,
    resolve_economy_smart_contract_settlement_runtime_context,
)
from aware_economy.wallet_funding import (
    EconomyWalletFundingOperationContext,
    hydrate_wallet_funding_intent_at_commit,
    resolve_economy_wallet_funding_runtime_context,
    describe_wallet_balance as describe_wallet_balance_runtime,
    prepare_wallet_funding as prepare_wallet_funding_runtime,
    record_verified_wallet_funding as record_verified_wallet_funding_runtime,
    record_wallet_funding_expiration as record_wallet_funding_expiration_runtime,
)
from aware_economy.provider_lifecycle import (
    EconomyProviderLifecycleOperationContext,
    resolve_economy_provider_lifecycle_runtime_context,
    record_provider_lifecycle_event as record_provider_lifecycle_event_runtime,
)
from aware_economy.meta_runtime import EconomyMetaRuntimeLaneBinder
from aware_code.types import JsonObject
from aware_economy_ontology.price.price_reservation_enums import PriceReservationStatus
from aware_economy_ontology.smart_contract.smart_contract_reservation_enums import (
    ReservationStatus,
)
from aware_economy_ontology.transaction.provider_lifecycle_receipt_enums import (
    ProviderLifecycleEventKind,
)
from aware_economy_service_dto.economy.service import EconomyActorStatusRequest
from aware_economy_service_dto.economy.service import EconomyActorStatusResponse
from aware_economy_service_dto.economy.service import EconomyEnsureFinanceEntityRequest
from aware_economy_service_dto.economy.service import EconomyEnsureFinanceEntityResponse
from aware_economy_service_dto.economy.service import (
    EconomyPriceReservationFinalizeRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomyPriceReservationFinalizeResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomyPriceReservationReserveRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomyPriceReservationReserveResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomyServiceOperationPermitEnsureRequest,
    EconomyServiceOperationPermitEnsureResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomySmartContractReservationPrepareRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomySmartContractReservationPrepareResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomySmartContractReservationReleaseRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomySmartContractReservationReleaseResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomySmartContractSettlementFinalizeRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomySmartContractSettlementFinalizeResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletBalanceDescribeRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletBalanceDescribeResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalFrameResolveRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalFrameResolveResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalViewStateResolveRequest,
)
from aware_economy_service_dto.economy.service import EconomyWalletFundingPrepareRequest
from aware_economy_service_dto.economy.service import (
    EconomyWalletFundingPrepareResponse,
)
from aware_economy_service_dto.economy.service import EconomyWalletFundingRecordRequest
from aware_economy_service_dto.economy.service import EconomyWalletFundingRecordResponse
from aware_economy_service_dto.economy.service import EconomyWalletFundingCancelRequest
from aware_economy_service_dto.economy.service import EconomyWalletFundingCancelResponse
from aware_economy_service_dto.economy.service import (
    EconomyWalletFundingContextResolveRequest,
    EconomyWalletFundingContextResolveResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomyProviderLifecycleRecordRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomyProviderLifecycleRecordResponse,
)
from aware_economy_service_dto.economy.view import EconomyWalletCapitalViewStateV1
from aware_service_runtime.api_ingress.host_context import (
    current_service_api_host_context,
    require_current_service_api_materialization_context,
)
from aware_service_runtime.api_ingress.ontology_replica_orm_context import (
    require_service_ontology_replica_orm_session,
)
from aware_economy_service.wallet_funding_context import (
    resolve_wallet_funding_context_models,
    resolve_wallet_funding_prepare_context,
)
from aware_economy_service.provider_lifecycle_context import (
    resolve_provider_lifecycle_context_models,
)
from aware_economy_service.replica_commits import (
    mirror_economy_materialization_commits,
)


def build_aware_economy_service_protocol_handler() -> object:
    return _AwareEconomyServiceProtocolHandler()


class _EconomyActorStatusCapabilityHandler:
    async def economy_actor_status(
        self,
        request: EconomyActorStatusRequest,
        execution: object | None = None,
    ) -> EconomyActorStatusResponse:
        _ = execution
        materialization = require_current_service_api_materialization_context()
        actor_id = _parse_optional_uuid(request.actor_id, field_name="actor_id")
        finance_role_key = _require_finance_role_key(request.finance_role_key)
        if actor_id is None:
            return EconomyActorStatusResponse(
                operation="economy_actor_status",
                finance_role_key=finance_role_key,
                finance_entity_ready=False,
                wallet_ready=False,
                next_step="ensure_finance_entity",
                finance_entity_id=None,
                wallet_id=None,
                wallet_public_id=None,
            )
        receipt = await resolve_finance_entity_readiness_runtime(
            runtime_context=_finance_readiness_runtime_context(materialization),
            actor_id=actor_id,
            finance_role_key=finance_role_key,
        )
        ready = receipt.finance_entity_ready and receipt.wallet_ready
        return EconomyActorStatusResponse(
            operation="economy_actor_status",
            finance_role_key=receipt.finance_role_key,
            finance_entity_ready=ready,
            wallet_ready=receipt.wallet_ready,
            next_step="ready" if ready else "ensure_finance_entity",
            finance_entity_id=(
                str(receipt.finance_entity_id) if receipt.finance_entity_ready else None
            ),
            wallet_id=str(receipt.wallet_id) if receipt.wallet_ready else None,
            wallet_public_id=(
                str(receipt.wallet_public_id) if receipt.wallet_ready else None
            ),
        )


class _EconomyEnsureFinanceEntityCapabilityHandler:
    async def ensure_finance_entity(
        self,
        request: EconomyEnsureFinanceEntityRequest,
        execution: object | None = None,
    ) -> EconomyEnsureFinanceEntityResponse:
        _ = execution
        materialization = require_current_service_api_materialization_context()
        actor_id = _parse_required_uuid(request.actor_id, field_name="actor_id")
        async with mirror_economy_materialization_commits(
            materialization=materialization
        ) as mirrored_materialization:
            receipt = await ensure_finance_entity_runtime(
                runtime_context=_finance_readiness_runtime_context(
                    mirrored_materialization
                ),
                operation_context=EconomyFinanceReadinessOperationContext(
                    actor_id=actor_id,
                ),
                actor_id=actor_id,
                finance_role_key=_require_finance_role_key(request.finance_role_key),
                commit=True,
                publish=False,
            )
        return EconomyEnsureFinanceEntityResponse(
            operation="ensure_finance_entity",
            finance_role_key=receipt.finance_role_key,
            finance_entity_id=str(receipt.finance_entity_id),
            wallet_id=str(receipt.wallet_id),
            wallet_public_id=str(receipt.wallet_public_id),
        )


class _EconomyWalletFundingPrepareCapabilityHandler:
    async def prepare_wallet_funding(
        self,
        request: EconomyWalletFundingPrepareRequest,
        execution: object | None = None,
    ) -> EconomyWalletFundingPrepareResponse:
        _ = execution
        materialization = require_current_service_api_materialization_context()
        _ = require_service_ontology_replica_orm_session()
        actor_id = _require_admitted_actor_id()
        target_wallet_id = _parse_required_uuid(
            request.target_wallet_id,
            field_name="target_wallet_id",
        )
        coin_id = _parse_required_uuid(request.coin_id, field_name="coin_id")
        provider_key = _require_non_empty(
            request.provider_key,
            field_name="provider_key",
        ).casefold()
        resolved = await resolve_wallet_funding_prepare_context(
            admitted_actor_id=actor_id,
            target_wallet_id=target_wallet_id,
            coin_id=coin_id,
            provider_key=provider_key,
            amount=request.amount,
        )
        async with mirror_economy_materialization_commits(
            materialization=materialization
        ) as mirrored_materialization:
            receipt = await prepare_wallet_funding_runtime(
                runtime_context=_wallet_funding_runtime_context(
                    mirrored_materialization
                ),
                operation_context=EconomyWalletFundingOperationContext(
                    actor_id=actor_id,
                ),
                provider_config_id=resolved.provider_config.id,
                provider_route_id=resolved.provider_route.id,
                provider_finance_entity_id=resolved.provider_finance_entity.id,
                recipient_finance_entity_id=resolved.recipient_finance_entity.id,
                recipient_wallet_id=resolved.recipient_wallet.id,
                recipient_wallet_public_id=resolved.recipient_wallet_public_id,
                coin_id=resolved.coin.id,
                amount=resolved.amount,
                funding_intent_key=_require_non_empty(
                    request.funding_intent_key,
                    field_name="funding_intent_key",
                ),
                idempotency_key=_require_non_empty(
                    request.idempotency_key,
                    field_name="idempotency_key",
                ),
                provider_key=provider_key,
                external_currency=resolved.provider_route.external_currency,
                external_minor_unit_exponent=(
                    resolved.provider_route.external_minor_unit_exponent
                ),
                conversion_mode=resolved.provider_route.conversion_mode,
                created_at=datetime.now(UTC),
                commit=True,
                publish=True,
            )
        return EconomyWalletFundingPrepareResponse(
            operation="prepare_wallet_funding",
            transaction_intent_id=str(receipt.transaction_intent_id),
            transaction_intent_commit_id=str(receipt.transaction_intent_commit_id),
            funding_intent_key=receipt.funding_intent_key,
            idempotency_key=receipt.idempotency_key,
            provider_key=receipt.provider_key,
            provider_config_id=str(receipt.provider_config_id),
            provider_route_id=str(receipt.provider_route_id),
            provider_finance_entity_id=str(receipt.provider_finance_entity_id),
            recipient_finance_entity_id=str(receipt.recipient_finance_entity_id),
            recipient_wallet_id=str(receipt.recipient_wallet_id),
            recipient_wallet_public_id=str(receipt.recipient_wallet_public_id),
            coin_id=str(receipt.coin_id),
            amount=receipt.amount,
            capital_conversion_quote_id=str(receipt.capital_conversion_quote_id),
            quote_hash=receipt.quote_hash,
            external_amount_minor=receipt.external_amount_minor,
            external_currency=receipt.external_currency,
            conversion_mode=receipt.conversion_mode,
            quote_captured_at=receipt.quote_captured_at.isoformat(),
            quote_expires_at=(
                receipt.quote_expires_at.isoformat()
                if receipt.quote_expires_at is not None
                else None
            ),
            status=receipt.status,
            idempotent_replay=receipt.idempotent_replay,
        )


class _EconomyWalletFundingContextResolveCapabilityHandler:
    async def resolve_wallet_funding_context(
        self,
        request: EconomyWalletFundingContextResolveRequest,
        execution: object | None = None,
    ) -> EconomyWalletFundingContextResolveResponse:
        _ = execution
        actor_id = _require_admitted_actor_id()
        materialization = require_current_service_api_materialization_context()
        _ = require_service_ontology_replica_orm_session()
        transaction_intent_id = _parse_required_uuid(
            request.transaction_intent_id,
            field_name="transaction_intent_id",
        )
        transaction_intent_commit_id = _parse_required_uuid(
            request.transaction_intent_commit_id,
            field_name="transaction_intent_commit_id",
        )
        intent = await hydrate_wallet_funding_intent_at_commit(
            runtime_context=_wallet_funding_runtime_context(materialization),
            transaction_intent_id=transaction_intent_id,
            transaction_intent_commit_id=transaction_intent_commit_id,
        )
        resolved = await resolve_wallet_funding_context_models(
            intent=intent,
            admitted_provider_actor_id=actor_id,
        )
        quote = resolved.quote
        return EconomyWalletFundingContextResolveResponse(
            operation="resolve_wallet_funding_context",
            transaction_intent_id=str(intent.id),
            transaction_intent_commit_id=str(transaction_intent_commit_id),
            funding_intent_key=intent.funding_intent_key,
            idempotency_key=intent.idempotency_key,
            provider_key=intent.provider_key,
            provider_config_id=str(resolved.provider_config.id),
            provider_route_id=str(resolved.provider_route.id),
            provider_finance_entity_id=str(resolved.provider_finance_entity.id),
            recipient_finance_entity_id=str(resolved.recipient_finance_entity.id),
            recipient_wallet_id=str(resolved.recipient_wallet.id),
            recipient_wallet_public_id=str(intent.recipient_wallet_public_id),
            coin_id=str(resolved.coin.id),
            amount=intent.amount,
            status=intent.status.value,
            capital_conversion_quote_id=str(quote.id),
            quote_hash=quote.quote_hash,
            external_amount_minor=quote.external_amount_minor,
            external_currency=quote.external_currency,
            target_amount=quote.target_amount,
            conversion_mode=quote.conversion_mode.value,
            quote_source=quote.source,
            quote_captured_at=quote.captured_at.isoformat(),
            quote_expires_at=(
                quote.expires_at.isoformat() if quote.expires_at is not None else None
            ),
        )


class _EconomyWalletFundingRecordCapabilityHandler:
    async def record_verified_wallet_funding(
        self,
        request: EconomyWalletFundingRecordRequest,
        execution: object | None = None,
    ) -> EconomyWalletFundingRecordResponse:
        _ = execution
        materialization = require_current_service_api_materialization_context()
        _ = require_service_ontology_replica_orm_session()
        actor_id = _require_admitted_actor_id()
        transaction_intent_id = _parse_required_uuid(
            request.transaction_intent_id,
            field_name="transaction_intent_id",
        )
        transaction_intent_commit_id = _parse_required_uuid(
            request.transaction_intent_commit_id,
            field_name="transaction_intent_commit_id",
        )
        runtime_context = _wallet_funding_runtime_context(materialization)
        intent = await hydrate_wallet_funding_intent_at_commit(
            runtime_context=runtime_context,
            transaction_intent_id=transaction_intent_id,
            transaction_intent_commit_id=transaction_intent_commit_id,
        )
        resolved = await resolve_wallet_funding_context_models(
            intent=intent,
            admitted_provider_actor_id=actor_id,
            require_active_provider_route=False,
        )
        async with mirror_economy_materialization_commits(
            materialization=materialization
        ) as mirrored_materialization:
            receipt = await record_verified_wallet_funding_runtime(
                runtime_context=_wallet_funding_runtime_context(
                    mirrored_materialization
                ),
                operation_context=EconomyWalletFundingOperationContext(
                    actor_id=actor_id,
                ),
                transaction_intent_id=transaction_intent_id,
                transaction_intent_commit_id=transaction_intent_commit_id,
                provider_config_id=resolved.provider_config.id,
                provider_finance_entity_id=resolved.provider_finance_entity.id,
                provider_key=_require_non_empty(
                    request.provider_key,
                    field_name="provider_key",
                ),
                provider_event_id=_require_non_empty(
                    request.provider_event_id,
                    field_name="provider_event_id",
                ),
                idempotency_key=_require_non_empty(
                    request.idempotency_key,
                    field_name="idempotency_key",
                ),
                capital_conversion_quote_id=_parse_required_uuid(
                    request.capital_conversion_quote_id,
                    field_name="capital_conversion_quote_id",
                ),
                quote_hash=_require_non_empty(
                    request.quote_hash,
                    field_name="quote_hash",
                ),
                external_amount_minor=request.external_amount_minor,
                external_currency=_require_non_empty(
                    request.external_currency,
                    field_name="external_currency",
                ),
                provider_public_reference=_require_non_empty(
                    request.provider_public_reference,
                    field_name="provider_public_reference",
                ),
                provider_payload_hash=_require_non_empty(
                    request.provider_payload_hash,
                    field_name="provider_payload_hash",
                ),
                external_created_at=_parse_required_datetime(
                    request.external_created_at,
                    field_name="external_created_at",
                ),
                commit=True,
                publish=True,
            )
        return EconomyWalletFundingRecordResponse(
            operation="record_verified_wallet_funding",
            transaction_intent_id=str(receipt.transaction_intent_id),
            transaction_intent_commit_id=str(receipt.transaction_intent_commit_id),
            capital_conversion_quote_id=str(receipt.capital_conversion_quote_id),
            quote_hash=receipt.quote_hash,
            transaction_external_id=str(receipt.transaction_external_id),
            transaction_id=str(receipt.transaction_id),
            transaction_nonce=receipt.transaction_nonce,
            wallet_external_ingress_application_id=str(
                receipt.wallet_external_ingress_application_id
            ),
            wallet_balance_id=str(receipt.wallet_balance_id),
            provider_finance_entity_id=str(receipt.provider_finance_entity_id),
            recipient_finance_entity_id=str(receipt.recipient_finance_entity_id),
            recipient_wallet_id=str(receipt.recipient_wallet_id),
            recipient_wallet_public_id=str(receipt.recipient_wallet_public_id),
            coin_id=str(receipt.coin_id),
            amount=receipt.amount,
            previous_balance=receipt.previous_balance,
            new_balance=receipt.new_balance,
            status=receipt.status,
            idempotent_replay=receipt.idempotent_replay,
        )


class _EconomyWalletFundingCancelCapabilityHandler:
    async def record_wallet_funding_expiration(
        self,
        request: EconomyWalletFundingCancelRequest,
        execution: object | None = None,
    ) -> EconomyWalletFundingCancelResponse:
        _ = execution
        materialization = require_current_service_api_materialization_context()
        _ = require_service_ontology_replica_orm_session()
        actor_id = _require_admitted_actor_id()
        transaction_intent_id = _parse_required_uuid(
            request.transaction_intent_id,
            field_name="transaction_intent_id",
        )
        transaction_intent_commit_id = _parse_required_uuid(
            request.transaction_intent_commit_id,
            field_name="transaction_intent_commit_id",
        )
        runtime_context = _wallet_funding_runtime_context(materialization)
        intent = await hydrate_wallet_funding_intent_at_commit(
            runtime_context=runtime_context,
            transaction_intent_id=transaction_intent_id,
            transaction_intent_commit_id=transaction_intent_commit_id,
        )
        resolved = await resolve_wallet_funding_context_models(
            intent=intent,
            admitted_provider_actor_id=actor_id,
            require_active_provider_route=False,
        )
        async with mirror_economy_materialization_commits(
            materialization=materialization
        ) as mirrored_materialization:
            receipt = await record_wallet_funding_expiration_runtime(
                runtime_context=_wallet_funding_runtime_context(
                    mirrored_materialization
                ),
                operation_context=EconomyWalletFundingOperationContext(
                    actor_id=actor_id,
                ),
                transaction_intent_id=transaction_intent_id,
                transaction_intent_commit_id=transaction_intent_commit_id,
                provider_config_id=resolved.provider_config.id,
                provider_key=_require_non_empty(
                    request.provider_key,
                    field_name="provider_key",
                ),
                provider_event_id=_require_non_empty(
                    request.provider_event_id,
                    field_name="provider_event_id",
                ),
                idempotency_key=_require_non_empty(
                    request.idempotency_key,
                    field_name="idempotency_key",
                ),
                capital_conversion_quote_id=_parse_required_uuid(
                    request.capital_conversion_quote_id,
                    field_name="capital_conversion_quote_id",
                ),
                quote_hash=_require_non_empty(
                    request.quote_hash,
                    field_name="quote_hash",
                ),
                provider_public_reference=_require_non_empty(
                    request.provider_public_reference,
                    field_name="provider_public_reference",
                ),
                provider_payload_hash=_require_non_empty(
                    request.provider_payload_hash,
                    field_name="provider_payload_hash",
                ),
                external_created_at=_parse_required_datetime(
                    request.external_created_at,
                    field_name="external_created_at",
                ),
                commit=True,
                publish=True,
            )
        return EconomyWalletFundingCancelResponse(
            operation="record_wallet_funding_expiration",
            transaction_intent_id=str(receipt.transaction_intent_id),
            transaction_intent_commit_id=str(receipt.transaction_intent_commit_id),
            transaction_intent_external_expiration_id=str(
                receipt.transaction_intent_external_expiration_id
            ),
            provider_config_id=str(receipt.provider_config_id),
            capital_conversion_quote_id=str(receipt.capital_conversion_quote_id),
            quote_hash=receipt.quote_hash,
            provider_key=receipt.provider_key,
            provider_event_id=receipt.provider_event_id,
            provider_public_reference=receipt.provider_public_reference,
            status=receipt.status,
            idempotent_replay=receipt.idempotent_replay,
        )


class _EconomyProviderLifecycleRecordCapabilityHandler:
    async def record_provider_lifecycle_event(
        self,
        request: EconomyProviderLifecycleRecordRequest,
        execution: object | None = None,
    ) -> EconomyProviderLifecycleRecordResponse:
        _ = execution
        materialization = require_current_service_api_materialization_context()
        _ = require_service_ontology_replica_orm_session()
        actor_id = _require_admitted_actor_id()
        provider_key = _require_non_empty(
            request.provider_key,
            field_name="provider_key",
        )
        provider_lifecycle_object_id = _require_non_empty(
            request.provider_lifecycle_object_id,
            field_name="provider_lifecycle_object_id",
        )
        provider_lifecycle_effect_key = _require_non_empty(
            request.provider_lifecycle_effect_key,
            field_name="provider_lifecycle_effect_key",
        ).casefold()
        provider_payment_reference = _require_non_empty(
            request.provider_payment_reference,
            field_name="provider_payment_reference",
        )
        event_kind = _parse_provider_lifecycle_event_kind(request.event_kind)
        if provider_lifecycle_effect_key != event_kind.value:
            raise ValueError("provider_lifecycle_effect_key must match event_kind")
        resolved = await resolve_provider_lifecycle_context_models(
            admitted_provider_actor_id=actor_id,
            provider_key=provider_key,
            provider_lifecycle_object_id=provider_lifecycle_object_id,
            provider_payment_reference=provider_payment_reference,
            external_amount_minor=request.external_amount_minor,
            external_currency=_require_non_empty(
                request.external_currency,
                field_name="external_currency",
            ),
            event_kind=event_kind,
        )
        async with mirror_economy_materialization_commits(
            materialization=materialization
        ) as mirrored_materialization:
            receipt = await record_provider_lifecycle_event_runtime(
                runtime_context=_provider_lifecycle_runtime_context(
                    mirrored_materialization
                ),
                operation_context=EconomyProviderLifecycleOperationContext(
                    actor_id=actor_id,
                ),
                provider_finance_entity_id=resolved.funding.provider_finance_entity.id,
                provider_key=provider_key,
                provider_event_id=_require_non_empty(
                    request.provider_event_id,
                    field_name="provider_event_id",
                ),
                provider_lifecycle_object_id=provider_lifecycle_object_id,
                provider_lifecycle_effect_key=provider_lifecycle_effect_key,
                wallet_finance_entity_id=resolved.funding.recipient_finance_entity.id,
                wallet_id=resolved.funding.recipient_wallet.id,
                wallet_public_id=resolved.funding.intent.recipient_wallet_public_id,
                coin_id=resolved.funding.coin.id,
                amount=resolved.amount,
                event_kind=event_kind,
                provider_payment_reference=provider_payment_reference,
                provider_payload_hash=_require_non_empty(
                    request.provider_payload_hash,
                    field_name="provider_payload_hash",
                ),
                external_created_at=_parse_required_datetime(
                    request.external_created_at,
                    field_name="external_created_at",
                ),
                metadata_json=cast(JsonObject | None, request.metadata_json),
                transaction_id=resolved.transaction_external.transaction_id,
                transaction_external_id=resolved.transaction_external.id,
                commit=True,
                publish=True,
            )
        return EconomyProviderLifecycleRecordResponse(
            operation="record_provider_lifecycle_event",
            provider_lifecycle_receipt_id=str(receipt.provider_lifecycle_receipt_id),
            wallet_balance_id=str(receipt.wallet_balance_id),
            provider_finance_entity_id=str(receipt.provider_finance_entity_id),
            provider_key=receipt.provider_key,
            provider_event_id=receipt.provider_event_id,
            provider_lifecycle_object_id=receipt.provider_lifecycle_object_id,
            provider_lifecycle_effect_key=receipt.provider_lifecycle_effect_key,
            idempotency_key=receipt.idempotency_key,
            wallet_finance_entity_id=str(receipt.wallet_finance_entity_id),
            wallet_id=str(receipt.wallet_id),
            wallet_public_id=str(receipt.wallet_public_id),
            coin_id=str(receipt.coin_id),
            amount=receipt.amount,
            event_kind=receipt.event_kind,
            status=receipt.status,
            previous_balance=receipt.previous_balance,
            new_balance=receipt.new_balance,
            previous_held_balance=receipt.previous_held_balance,
            new_held_balance=receipt.new_held_balance,
            previous_available_balance=receipt.previous_available_balance,
            new_available_balance=receipt.new_available_balance,
            provider_payment_reference=receipt.provider_payment_reference,
            provider_payload_hash=receipt.provider_payload_hash,
            transaction_id=str(receipt.transaction_id),
            transaction_external_id=str(receipt.transaction_external_id),
            idempotent_replay=receipt.idempotent_replay,
        )


class _EconomyWalletBalanceDescribeCapabilityHandler:
    async def describe_wallet_balance(
        self,
        request: EconomyWalletBalanceDescribeRequest,
        execution: object | None = None,
    ) -> EconomyWalletBalanceDescribeResponse:
        _ = execution
        materialization = require_current_service_api_materialization_context()
        receipt = await describe_wallet_balance_runtime(
            runtime_context=_wallet_funding_runtime_context(materialization),
            wallet_id=_parse_required_uuid(request.wallet_id, field_name="wallet_id"),
            coin_id=_parse_required_uuid(request.coin_id, field_name="coin_id"),
        )
        return EconomyWalletBalanceDescribeResponse(
            operation="describe_wallet_balance",
            wallet_balance_id=str(receipt.wallet_balance_id),
            wallet_id=str(receipt.wallet_id),
            coin_id=str(receipt.coin_id),
            balance=receipt.balance,
            held_balance=receipt.held_balance,
            available_balance=receipt.available_balance,
            ready=receipt.ready,
            last_transaction_id=(
                str(receipt.last_transaction_id)
                if receipt.last_transaction_id is not None
                else None
            ),
        )


class _EconomyWalletCapitalFrameResolveCapabilityHandler:
    async def resolve_wallet_capital_frame(
        self,
        request: EconomyWalletCapitalFrameResolveRequest,
        execution: object | None = None,
    ) -> EconomyWalletCapitalFrameResolveResponse:
        _ = execution
        _ = require_service_ontology_replica_orm_session()
        from aware_economy.operator_read import (  # noqa: PLC0415
            resolve_wallet_capital_frame_from_economy_replica,
        )

        return await resolve_wallet_capital_frame_from_economy_replica(
            request=request,
        )


class _EconomyWalletCapitalViewStateResolveCapabilityHandler:
    async def resolve_wallet_capital_view_state(
        self,
        request: EconomyWalletCapitalViewStateResolveRequest,
        execution: object | None = None,
    ) -> EconomyWalletCapitalViewStateV1:
        _ = execution
        _ = require_service_ontology_replica_orm_session()
        from aware_economy.operator_read import (  # noqa: PLC0415
            resolve_wallet_capital_view_state_from_economy_replica,
        )

        frame_request = EconomyWalletCapitalFrameResolveRequest(
            actor_id=request.actor_id,
            wallet_id=request.wallet_id,
            coin_id=request.coin_id,
            limit=request.limit,
            include_transaction_intents=request.include_transaction_intents,
            include_transaction_externals=request.include_transaction_externals,
            include_transactions=request.include_transactions,
            include_reservations=request.include_reservations,
            include_escrows=request.include_escrows,
            include_settlements=request.include_settlements,
            include_provider_lifecycle=request.include_provider_lifecycle,
        )
        return await resolve_wallet_capital_view_state_from_economy_replica(
            request=frame_request,
        )


class _EconomyPriceReservationReserveCapabilityHandler:
    async def price_reservation_reserve(
        self,
        request: EconomyPriceReservationReserveRequest,
        execution: object | None = None,
    ) -> EconomyPriceReservationReserveResponse:
        _ = execution
        materialization = require_current_service_api_materialization_context()
        async with mirror_economy_materialization_commits(
            materialization=materialization
        ) as mirrored_materialization:
            receipt = await reserve_price_reservation(
                runtime=cast(Any, mirrored_materialization.runtime),
                index=_materialization_runtime_index(mirrored_materialization),
                actor_id=_parse_optional_uuid(request.actor_id, field_name="actor_id"),
                economy_price_lane=build_economy_price_lane(
                    index=_materialization_runtime_index(materialization),
                    branch_id=materialization.target_lane.branch_id,
                ),
                price_id=_parse_required_uuid(request.price_id, field_name="price_id"),
                request_hash=_require_non_empty(
                    request.request_hash, field_name="request_hash"
                ),
                operation_key=_require_non_empty(
                    request.operation_key, field_name="operation_key"
                ),
                pricing_policy_id=_parse_optional_uuid(
                    request.pricing_policy_id,
                    field_name="pricing_policy_id",
                ),
                upper_bound_cost_basis_amount=(
                    request.upper_bound_cost_basis_amount
                ),
                cost_basis_coin_id=_parse_optional_uuid(
                    request.cost_basis_coin_id,
                    field_name="cost_basis_coin_id",
                ),
                meter_evidence_ref=request.meter_evidence_ref,
                commit=True,
                publish=False,
            )
        return EconomyPriceReservationReserveResponse(
            operation="price_reservation_reserve",
            price_id=str(receipt.price_id),
            price_schedule_id=str(receipt.price_schedule_id),
            rate_snapshot_id=str(receipt.rate_snapshot_id),
            price_reservation_id=str(receipt.price_reservation_id),
            quoted_amount=receipt.quoted_amount,
            cost_basis_amount=receipt.cost_basis_amount,
            markup_percentage=receipt.markup_percentage,
            markup_amount=receipt.markup_amount,
            meter_evidence_ref=receipt.meter_evidence_ref,
            status=receipt.status.value,
        )


class _EconomyPriceReservationFinalizeCapabilityHandler:
    async def price_reservation_finalize(
        self,
        request: EconomyPriceReservationFinalizeRequest,
        execution: object | None = None,
    ) -> EconomyPriceReservationFinalizeResponse:
        _ = execution
        materialization = require_current_service_api_materialization_context()
        async with mirror_economy_materialization_commits(
            materialization=materialization
        ) as mirrored_materialization:
            receipt = await finalize_price_reservation(
                runtime=cast(Any, mirrored_materialization.runtime),
                index=_materialization_runtime_index(mirrored_materialization),
                actor_id=_parse_optional_uuid(request.actor_id, field_name="actor_id"),
                economy_price_lane=build_economy_price_lane(
                    index=_materialization_runtime_index(materialization),
                    branch_id=materialization.target_lane.branch_id,
                ),
                price_reservation_id=_parse_required_uuid(
                    request.price_reservation_id,
                    field_name="price_reservation_id",
                ),
                status=_parse_price_reservation_status(request.status),
                actual_cost_basis_amount=request.actual_cost_basis_amount,
                cost_basis_coin_id=_parse_optional_uuid(
                    request.cost_basis_coin_id,
                    field_name="cost_basis_coin_id",
                ),
                meter_evidence_ref=request.meter_evidence_ref,
                commit=True,
                publish=False,
            )
        return EconomyPriceReservationFinalizeResponse(
            operation="price_reservation_finalize",
            price_reservation_id=str(receipt.price_reservation_id),
            status=receipt.status.value,
            final_amount=receipt.final_amount,
            actual_cost_basis_amount=receipt.actual_cost_basis_amount,
            actual_markup_amount=receipt.actual_markup_amount,
            meter_evidence_ref=receipt.meter_evidence_ref,
        )


class _EconomySmartContractReservationPrepareCapabilityHandler:
    async def prepare_smart_contract_reservation(
        self,
        request: EconomySmartContractReservationPrepareRequest,
        execution: object | None = None,
    ) -> EconomySmartContractReservationPrepareResponse:
        _ = execution
        materialization = require_current_service_api_materialization_context()
        actor_id = _parse_optional_uuid(request.actor_id, field_name="actor_id")
        async with mirror_economy_materialization_commits(
            materialization=materialization
        ) as mirrored_materialization:
            receipt = await prepare_smart_contract_reservation_runtime(
                runtime_context=_smart_contract_settlement_runtime_context(
                    mirrored_materialization
                ),
                operation_context=EconomySmartContractSettlementOperationContext(
                    actor_id=actor_id,
                ),
                smart_contract_id=_parse_required_uuid(
                    request.smart_contract_id,
                    field_name="smart_contract_id",
                ),
                permit_id=_parse_required_uuid(
                    request.permit_id, field_name="permit_id"
                ),
                permit_nonce=request.permit_nonce,
                payer_finance_entity_id=_parse_required_uuid(
                    request.payer_finance_entity_id,
                    field_name="payer_finance_entity_id",
                ),
                payer_wallet_id=_parse_required_uuid(
                    request.payer_wallet_id,
                    field_name="payer_wallet_id",
                ),
                payer_wallet_public_id=_parse_required_uuid(
                    request.payer_wallet_public_id,
                    field_name="payer_wallet_public_id",
                ),
                args_hash=_require_non_empty(request.args_hash, field_name="args_hash"),
                max_cost=request.max_cost,
                rate_snapshot_id=_parse_required_uuid(
                    request.rate_snapshot_id,
                    field_name="rate_snapshot_id",
                ),
                deadline=_parse_required_datetime(
                    request.deadline,
                    field_name="deadline",
                ),
                coin_id=_parse_required_uuid(request.coin_id, field_name="coin_id"),
                commit=True,
                publish=False,
            )
        return EconomySmartContractReservationPrepareResponse(
            operation="prepare_smart_contract_reservation",
            smart_contract_id=str(receipt.smart_contract_id),
            permit_id=str(receipt.permit_id),
            reservation_id=str(receipt.reservation_id),
            escrow_id=str(receipt.escrow_id),
            payer_finance_entity_id=str(receipt.payer_finance_entity_id),
            payer_wallet_id=str(receipt.payer_wallet_id),
            payer_wallet_public_id=str(receipt.payer_wallet_public_id),
            op_nonce=receipt.op_nonce,
            coin_id=str(receipt.coin_id),
            max_cost=receipt.max_cost,
            payer_balance=receipt.payer_balance,
            payer_held_balance=receipt.payer_held_balance,
            payer_available_balance=receipt.payer_available_balance,
            status=receipt.status,
            idempotent_replay=receipt.idempotent_replay,
        )


class _EconomyServiceOperationPermitEnsureCapabilityHandler:
    async def ensure_service_operation_permit(
        self,
        request: EconomyServiceOperationPermitEnsureRequest,
        execution: object | None = None,
    ) -> EconomyServiceOperationPermitEnsureResponse:
        _ = execution
        admitted_actor_id = _require_admitted_actor_id()
        requested_actor_id = _parse_optional_uuid(
            request.actor_id,
            field_name="actor_id",
        )
        if requested_actor_id is not None and requested_actor_id != admitted_actor_id:
            raise ValueError(
                "ensure_service_operation_permit actor_id must match the admitted Service actor"
            )
        materialization = require_current_service_api_materialization_context()
        async with mirror_economy_materialization_commits(
            materialization=materialization
        ) as mirrored_materialization:
            receipt = await ensure_service_operation_permit_runtime(
                runtime_context=_smart_contract_settlement_runtime_context(
                    mirrored_materialization
                ),
                operation_context=EconomySmartContractSettlementOperationContext(
                    actor_id=admitted_actor_id,
                ),
                actor_id=admitted_actor_id,
                finance_role_key=_require_finance_role_key(request.finance_role_key),
                smart_contract_id=_parse_required_uuid(
                    request.smart_contract_id,
                    field_name="smart_contract_id",
                ),
                price_schedule_id=_parse_required_uuid(
                    request.price_schedule_id,
                    field_name="price_schedule_id",
                ),
                coin_id=_parse_required_uuid(request.coin_id, field_name="coin_id"),
                cap_amount=request.cap_amount,
                expires_at=_parse_required_datetime(
                    request.expires_at,
                    field_name="expires_at",
                ),
                commit=True,
                publish=False,
            )
        return EconomyServiceOperationPermitEnsureResponse(
            operation="ensure_service_operation_permit",
            actor_id=str(receipt.actor_id),
            finance_role_key=receipt.finance_role_key,
            smart_contract_id=str(receipt.smart_contract_id),
            permit_id=str(receipt.permit_id),
            parent_permit_id=(
                str(receipt.parent_permit_id)
                if receipt.parent_permit_id is not None
                else None
            ),
            permit_nonce=receipt.permit_nonce,
            finance_entity_id=str(receipt.finance_entity_id),
            wallet_id=str(receipt.wallet_id),
            wallet_public_id=str(receipt.wallet_public_id),
            price_schedule_id=str(receipt.price_schedule_id),
            coin_id=str(receipt.coin_id),
            cap_amount=receipt.cap_amount,
            expires_at=receipt.expires_at.isoformat(),
            status=receipt.status,
            refreshed=receipt.refreshed,
            idempotent_replay=receipt.idempotent_replay,
        )


class _EconomySmartContractReservationReleaseCapabilityHandler:
    async def release_smart_contract_reservation(
        self,
        request: EconomySmartContractReservationReleaseRequest,
        execution: object | None = None,
    ) -> EconomySmartContractReservationReleaseResponse:
        _ = execution
        materialization = require_current_service_api_materialization_context()
        actor_id = _parse_optional_uuid(request.actor_id, field_name="actor_id")
        async with mirror_economy_materialization_commits(
            materialization=materialization
        ) as mirrored_materialization:
            receipt = await release_smart_contract_reservation_runtime(
                runtime_context=_smart_contract_settlement_runtime_context(
                    mirrored_materialization
                ),
                operation_context=EconomySmartContractSettlementOperationContext(
                    actor_id=actor_id,
                ),
                smart_contract_id=_parse_required_uuid(
                    request.smart_contract_id,
                    field_name="smart_contract_id",
                ),
                permit_id=_parse_required_uuid(
                    request.permit_id, field_name="permit_id"
                ),
                reservation_id=_parse_required_uuid(
                    request.reservation_id,
                    field_name="reservation_id",
                ),
                payer_finance_entity_id=_parse_required_uuid(
                    request.payer_finance_entity_id,
                    field_name="payer_finance_entity_id",
                ),
                payer_wallet_id=_parse_required_uuid(
                    request.payer_wallet_id,
                    field_name="payer_wallet_id",
                ),
                payer_wallet_public_id=_parse_required_uuid(
                    request.payer_wallet_public_id,
                    field_name="payer_wallet_public_id",
                ),
                coin_id=_parse_required_uuid(request.coin_id, field_name="coin_id"),
                status=_parse_reservation_release_status(request.status),
                commit=True,
                publish=False,
            )
        return EconomySmartContractReservationReleaseResponse(
            operation="release_smart_contract_reservation",
            smart_contract_id=str(receipt.smart_contract_id),
            permit_id=str(receipt.permit_id),
            reservation_id=str(receipt.reservation_id),
            escrow_id=str(receipt.escrow_id),
            payer_finance_entity_id=str(receipt.payer_finance_entity_id),
            payer_wallet_id=str(receipt.payer_wallet_id),
            payer_wallet_public_id=str(receipt.payer_wallet_public_id),
            payer_wallet_balance_id=str(receipt.payer_wallet_balance_id),
            coin_id=str(receipt.coin_id),
            released_amount=receipt.released_amount,
            payer_balance=receipt.payer_balance,
            payer_previous_held_balance=receipt.payer_previous_held_balance,
            payer_new_held_balance=receipt.payer_new_held_balance,
            payer_previous_available_balance=receipt.payer_previous_available_balance,
            payer_new_available_balance=receipt.payer_new_available_balance,
            status=receipt.status,
            idempotent_replay=receipt.idempotent_replay,
        )


class _EconomySmartContractSettlementFinalizeCapabilityHandler:
    async def finalize_smart_contract_settlement(
        self,
        request: EconomySmartContractSettlementFinalizeRequest,
        execution: object | None = None,
    ) -> EconomySmartContractSettlementFinalizeResponse:
        _ = execution
        materialization = require_current_service_api_materialization_context()
        actor_id = _parse_optional_uuid(request.actor_id, field_name="actor_id")
        async with mirror_economy_materialization_commits(
            materialization=materialization
        ) as mirrored_materialization:
            receipt = await finalize_smart_contract_settlement_runtime(
                runtime_context=_smart_contract_settlement_runtime_context(
                    mirrored_materialization
                ),
                operation_context=EconomySmartContractSettlementOperationContext(
                    actor_id=actor_id,
                ),
                smart_contract_id=_parse_required_uuid(
                    request.smart_contract_id,
                    field_name="smart_contract_id",
                ),
                permit_id=_parse_required_uuid(
                    request.permit_id, field_name="permit_id"
                ),
                reservation_id=_parse_required_uuid(
                    request.reservation_id,
                    field_name="reservation_id",
                ),
                payer_finance_entity_id=_parse_required_uuid(
                    request.payer_finance_entity_id,
                    field_name="payer_finance_entity_id",
                ),
                payer_wallet_id=_parse_required_uuid(
                    request.payer_wallet_id,
                    field_name="payer_wallet_id",
                ),
                payer_wallet_public_id=_parse_required_uuid(
                    request.payer_wallet_public_id,
                    field_name="payer_wallet_public_id",
                ),
                receiver_finance_entity_id=_parse_required_uuid(
                    request.receiver_finance_entity_id,
                    field_name="receiver_finance_entity_id",
                ),
                receiver_wallet_id=_parse_required_uuid(
                    request.receiver_wallet_id,
                    field_name="receiver_wallet_id",
                ),
                receiver_wallet_public_id=_parse_required_uuid(
                    request.receiver_wallet_public_id,
                    field_name="receiver_wallet_public_id",
                ),
                coin_id=_parse_required_uuid(request.coin_id, field_name="coin_id"),
                final_cost=request.final_cost,
                commit=True,
                publish=False,
            )
        return EconomySmartContractSettlementFinalizeResponse(
            operation="finalize_smart_contract_settlement",
            smart_contract_id=str(receipt.smart_contract_id),
            permit_id=str(receipt.permit_id),
            reservation_id=str(receipt.reservation_id),
            settlement_id=str(receipt.settlement_id),
            transaction_id=(
                str(receipt.transaction_id)
                if receipt.transaction_id is not None
                else None
            ),
            payer_finance_entity_id=str(receipt.payer_finance_entity_id),
            payer_wallet_id=str(receipt.payer_wallet_id),
            payer_wallet_public_id=str(receipt.payer_wallet_public_id),
            payer_wallet_balance_id=str(receipt.payer_wallet_balance_id),
            payer_previous_balance=receipt.payer_previous_balance,
            payer_new_balance=receipt.payer_new_balance,
            payer_previous_held_balance=receipt.payer_previous_held_balance,
            payer_new_held_balance=receipt.payer_new_held_balance,
            payer_previous_available_balance=receipt.payer_previous_available_balance,
            payer_new_available_balance=receipt.payer_new_available_balance,
            receiver_finance_entity_id=str(receipt.receiver_finance_entity_id),
            receiver_wallet_id=str(receipt.receiver_wallet_id),
            receiver_wallet_public_id=str(receipt.receiver_wallet_public_id),
            receiver_wallet_balance_id=str(receipt.receiver_wallet_balance_id),
            receiver_previous_balance=receipt.receiver_previous_balance,
            receiver_new_balance=receipt.receiver_new_balance,
            coin_id=str(receipt.coin_id),
            final_cost=receipt.final_cost,
            status=receipt.status,
            idempotent_replay=receipt.idempotent_replay,
        )


class _EconomyCapabilityNamespace:
    def __init__(self) -> None:
        self.economy_actor_status = _EconomyActorStatusCapabilityHandler()
        self.ensure_finance_entity = _EconomyEnsureFinanceEntityCapabilityHandler()
        self.wallet_funding_prepare = _EconomyWalletFundingPrepareCapabilityHandler()
        self.wallet_funding_context_resolve = (
            _EconomyWalletFundingContextResolveCapabilityHandler()
        )
        self.wallet_funding_record = _EconomyWalletFundingRecordCapabilityHandler()
        self.wallet_funding_cancel = _EconomyWalletFundingCancelCapabilityHandler()
        self.provider_lifecycle_record = (
            _EconomyProviderLifecycleRecordCapabilityHandler()
        )
        self.wallet_balance_describe = _EconomyWalletBalanceDescribeCapabilityHandler()
        self.wallet_capital_frame_resolve = (
            _EconomyWalletCapitalFrameResolveCapabilityHandler()
        )
        self.wallet_capital_view_state_resolve = (
            _EconomyWalletCapitalViewStateResolveCapabilityHandler()
        )
        self.price_reservation_reserve = (
            _EconomyPriceReservationReserveCapabilityHandler()
        )
        self.price_reservation_finalize = (
            _EconomyPriceReservationFinalizeCapabilityHandler()
        )
        self.service_operation_permit_ensure = (
            _EconomyServiceOperationPermitEnsureCapabilityHandler()
        )
        self.smart_contract_reservation_prepare = (
            _EconomySmartContractReservationPrepareCapabilityHandler()
        )
        self.smart_contract_reservation_release = (
            _EconomySmartContractReservationReleaseCapabilityHandler()
        )
        self.smart_contract_settlement_finalize = (
            _EconomySmartContractSettlementFinalizeCapabilityHandler()
        )


class _AwareEconomyServiceProtocolHandler:
    def __init__(self) -> None:
        self.economy = _EconomyCapabilityNamespace()


def _wallet_funding_runtime_context(
    materialization: object,
    *,
    lane_binder: EconomyMetaRuntimeLaneBinder | None = None,
):
    return resolve_economy_wallet_funding_runtime_context(
        lane_binder=lane_binder or _materialization_lane_binder(materialization),
        index=_materialization_runtime_index(materialization),
    )


def _provider_lifecycle_runtime_context(
    materialization: object,
    *,
    lane_binder: EconomyMetaRuntimeLaneBinder | None = None,
):
    return resolve_economy_provider_lifecycle_runtime_context(
        lane_binder=lane_binder or _materialization_lane_binder(materialization),
        index=_materialization_runtime_index(materialization),
    )


def _smart_contract_settlement_runtime_context(
    materialization: object,
    *,
    lane_binder: EconomyMetaRuntimeLaneBinder | None = None,
):
    return resolve_economy_smart_contract_settlement_runtime_context(
        lane_binder=lane_binder or _materialization_lane_binder(materialization),
        index=_materialization_runtime_index(materialization),
    )


def _finance_readiness_runtime_context(
    materialization: object,
    *,
    lane_binder: EconomyMetaRuntimeLaneBinder | None = None,
):
    return resolve_economy_finance_readiness_runtime_context(
        lane_binder=lane_binder or _materialization_lane_binder(materialization),
        index=_materialization_runtime_index(materialization),
    )


def _materialization_lane_binder(
    materialization: object,
) -> EconomyMetaRuntimeLaneBinder:
    runtime = getattr(materialization, "runtime", None)
    if not callable(getattr(runtime, "bind", None)):
        raise RuntimeError(
            "Economy service protocol requires an active Meta runtime lane binder."
        )
    return cast(EconomyMetaRuntimeLaneBinder, runtime)


def _materialization_runtime_index(materialization: object) -> object:
    runtime_index = getattr(materialization, "runtime_index", None)
    if runtime_index is not None:
        return runtime_index
    graph_context = getattr(materialization, "graph_context", None)
    if graph_context is not None:
        return graph_context
    runtime = getattr(materialization, "runtime", None)
    runtime_context = getattr(runtime, "context", None)
    runtime_index = getattr(runtime_context, "index", None)
    if runtime_index is not None:
        return runtime_index
    runtime_index = getattr(runtime, "index", None)
    if runtime_index is not None:
        return runtime_index
    raise RuntimeError(
        "Economy service protocol requires an active Meta runtime index."
    )


def _require_admitted_actor_id() -> UUID:
    host_context = current_service_api_host_context()
    if host_context is None or host_context.operation_context.actor_id is None:
        raise ValueError(
            "Economy wallet funding requires an admitted Service operation actor"
        )
    return host_context.operation_context.actor_id


def _parse_optional_uuid(value: str | None, *, field_name: str) -> UUID | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return UUID(raw)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid UUID string") from exc


def _parse_required_uuid(value: str, *, field_name: str) -> UUID:
    parsed = _parse_optional_uuid(value, field_name=field_name)
    if parsed is None:
        raise ValueError(f"{field_name} is required")
    return parsed


def _require_finance_role_key(value: str | None) -> str:
    raw = str(value or "primary").strip().casefold()
    if not raw:
        raise ValueError("finance_role_key is required")
    return raw


def _parse_price_reservation_status(value: str) -> PriceReservationStatus:
    raw = _require_non_empty(value, field_name="status")
    try:
        return PriceReservationStatus(raw)
    except ValueError as exc:
        raise ValueError(
            f"status must be one of {[item.value for item in PriceReservationStatus]}"
        ) from exc


def _parse_reservation_release_status(value: str) -> ReservationStatus:
    raw = _require_non_empty(value, field_name="status")
    try:
        status = ReservationStatus(raw)
    except ValueError as exc:
        raise ValueError("status must be cancelled or expired") from exc
    if status not in {ReservationStatus.cancelled, ReservationStatus.expired}:
        raise ValueError("status must be cancelled or expired")
    return status


def _parse_provider_lifecycle_event_kind(value: str) -> ProviderLifecycleEventKind:
    raw = _require_non_empty(value, field_name="event_kind")
    try:
        return ProviderLifecycleEventKind(raw)
    except ValueError as exc:
        raise ValueError(
            "event_kind must be one of "
            f"{[item.value for item in ProviderLifecycleEventKind]}"
        ) from exc


def _require_non_empty(value: str, *, field_name: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError(f"{field_name} is required")
    return raw


def _optional_non_empty(value: str | None) -> str | None:
    raw = str(value or "").strip()
    return raw or None


def _parse_optional_datetime(value: str | None, *, field_name: str) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 datetime string") from exc


def _parse_required_datetime(value: str, *, field_name: str) -> datetime:
    parsed = _parse_optional_datetime(value, field_name=field_name)
    if parsed is None:
        raise ValueError(f"{field_name} is required")
    return parsed


__all__ = [
    "build_aware_economy_service_protocol_handler",
]
