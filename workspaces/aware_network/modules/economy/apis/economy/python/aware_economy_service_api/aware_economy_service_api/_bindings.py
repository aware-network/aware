# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "economy-service-api"
API_FQN_PREFIX: Final[str] = "aware_economy_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Read the actor's finance and " "product-readiness state.",
                                "discriminant": "economy.economy_actor_status.economy_actor_status",
                                "name": "economy_actor_status",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyActorStatusRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyActorStatusResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "economy_actor_status",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Ensure the actor has a canonical " "FinanceEntity and wallet.",
                                "discriminant": "economy.ensure_finance_entity.ensure_finance_entity",
                                "name": "ensure_finance_entity",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyEnsureFinanceEntityRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyEnsureFinanceEntityResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "ensure_finance_entity",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Finalize one canonical Economy price "
                                "reservation. Economy derives settled "
                                "value from the committed schedule and "
                                "actual provider-neutral metering "
                                "evidence.",
                                "discriminant": "economy.price_reservation_finalize.price_reservation_finalize",
                                "name": "price_reservation_finalize",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyPriceReservationFinalizeRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyPriceReservationFinalizeResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "price_reservation_finalize",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Reserve one canonical Economy price "
                                "receipt. Dynamic prices require a "
                                "provider-neutral upper-bound cost "
                                "basis and evidence reference.",
                                "discriminant": "economy.price_reservation_reserve.price_reservation_reserve",
                                "name": "price_reservation_reserve",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyPriceReservationReserveRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyPriceReservationReserveResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "price_reservation_reserve",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Record verified external provider "
                                "lifecycle evidence as Aware wallet "
                                "receipt truth.",
                                "discriminant": "economy.provider_lifecycle_record.record_provider_lifecycle_event",
                                "name": "record_provider_lifecycle_event",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyProviderLifecycleRecordRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyProviderLifecycleRecordResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "provider_lifecycle_record",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Ensure or refresh the admitted actor's "
                                "Economy permit for one priced Service "
                                "operation contract.",
                                "discriminant": "economy.service_operation_permit_ensure.ensure_service_operation_permit",
                                "name": "ensure_service_operation_permit",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyServiceOperationPermitEnsureRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyServiceOperationPermitEnsureResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "service_operation_permit_ensure",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Reserve service capital from a "
                                "committed Aware Wallet through a "
                                "smart-contract escrow receipt.",
                                "discriminant": "economy.smart_contract_reservation_prepare.prepare_smart_contract_reservation",
                                "name": "prepare_smart_contract_reservation",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomySmartContractReservationPrepareRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomySmartContractReservationPrepareResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "smart_contract_reservation_prepare",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Cancel or expire a pending "
                                "smart-contract reservation and release "
                                "its held wallet capital.",
                                "discriminant": "economy.smart_contract_reservation_release.release_smart_contract_reservation",
                                "name": "release_smart_contract_reservation",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomySmartContractReservationReleaseRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomySmartContractReservationReleaseResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "smart_contract_reservation_release",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Finalize a smart-contract settlement "
                                "and reconcile payer/receiver Aware "
                                "Wallet balances.",
                                "discriminant": "economy.smart_contract_settlement_finalize.finalize_smart_contract_settlement",
                                "name": "finalize_smart_contract_settlement",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomySmartContractSettlementFinalizeRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomySmartContractSettlementFinalizeResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "smart_contract_settlement_finalize",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read the current Economy wallet " "balance for a wallet and coin.",
                                "discriminant": "economy.wallet_balance_describe.describe_wallet_balance",
                                "name": "describe_wallet_balance",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletBalanceDescribeRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletBalanceDescribeResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "wallet_balance_describe",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve an operator-safe wallet "
                                "capital read frame from Economy "
                                "replica truth.",
                                "discriminant": "economy.wallet_capital_frame_resolve.resolve_wallet_capital_frame",
                                "name": "resolve_wallet_capital_frame",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletCapitalFrameResolveRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletCapitalFrameResolveResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "wallet_capital_frame_resolve",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve the wallet-capital API view "
                                "state from Economy replica truth.",
                                "discriminant": "economy.wallet_capital_view_state_resolve.resolve_wallet_capital_view_state",
                                "name": "resolve_wallet_capital_view_state",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletCapitalViewStateResolveRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletCapitalViewStateV1",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "wallet_capital_view_state_resolve",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Record verified terminal no-credit "
                                "evidence and cancel the funding "
                                "intent.",
                                "discriminant": "economy.wallet_funding_cancel.record_wallet_funding_expiration",
                                "name": "record_wallet_funding_expiration",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletFundingCancelRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletFundingCancelResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "wallet_funding_cancel",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve provider-neutral committed "
                                "wallet-funding context by intent and "
                                "commit identity.",
                                "discriminant": "economy.wallet_funding_context_resolve.resolve_wallet_funding_context",
                                "name": "resolve_wallet_funding_context",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletFundingContextResolveRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletFundingContextResolveResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "wallet_funding_context_resolve",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Prepare an Aware-owned wallet funding "
                                "intent before external provider "
                                "confirmation.",
                                "discriminant": "economy.wallet_funding_prepare.prepare_wallet_funding",
                                "name": "prepare_wallet_funding",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletFundingPrepareRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletFundingPrepareResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "wallet_funding_prepare",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Record verified external funding "
                                "evidence as Economy transaction and "
                                "wallet balance truth.",
                                "discriminant": "economy.wallet_funding_record.record_verified_wallet_funding",
                                "name": "record_verified_wallet_funding",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletFundingRecordRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletFundingRecordResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "wallet_funding_record",
                        "source_path": "bindings/economy.apis.aware",
                    },
                ],
                "name": "economy",
                "source_path": "bindings/economy.apis.aware",
            }
        ],
        "fqn_prefix": "aware_economy_service_api",
        "package_name": "economy-service-api",
        "schema_version": 1,
    }
)

API_INVOCATION_MANIFEST: Final[LoadedApiInvocationManifest] = load_api_invocation_manifest_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read the actor's finance and " "product-readiness state.",
                                "discriminant": "economy.economy_actor_status.economy_actor_status",
                                "endpoint_ref": "economy.economy_actor_status.economy_actor_status",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "economy_actor_status",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyActorStatusRequest",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyActorStatusRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyActorStatusResponse",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyActorStatusResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "economy_actor_status",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Ensure the actor has a canonical " "FinanceEntity and wallet.",
                                "discriminant": "economy.ensure_finance_entity.ensure_finance_entity",
                                "endpoint_ref": "economy.ensure_finance_entity.ensure_finance_entity",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "ensure_finance_entity",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyEnsureFinanceEntityRequest",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyEnsureFinanceEntityRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyEnsureFinanceEntityResponse",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyEnsureFinanceEntityResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "ensure_finance_entity",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Finalize one canonical Economy price "
                                "reservation. Economy derives settled "
                                "value from the committed schedule and "
                                "actual provider-neutral metering "
                                "evidence.",
                                "discriminant": "economy.price_reservation_finalize.price_reservation_finalize",
                                "endpoint_ref": "economy.price_reservation_finalize.price_reservation_finalize",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "price_reservation_finalize",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyPriceReservationFinalizeRequest",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyPriceReservationFinalizeRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyPriceReservationFinalizeResponse",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyPriceReservationFinalizeResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "price_reservation_finalize",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Reserve one canonical Economy price "
                                "receipt. Dynamic prices require a "
                                "provider-neutral upper-bound cost "
                                "basis and evidence reference.",
                                "discriminant": "economy.price_reservation_reserve.price_reservation_reserve",
                                "endpoint_ref": "economy.price_reservation_reserve.price_reservation_reserve",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "price_reservation_reserve",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyPriceReservationReserveRequest",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyPriceReservationReserveRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyPriceReservationReserveResponse",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyPriceReservationReserveResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "price_reservation_reserve",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Record verified external provider "
                                "lifecycle evidence as Aware wallet "
                                "receipt truth.",
                                "discriminant": "economy.provider_lifecycle_record.record_provider_lifecycle_event",
                                "endpoint_ref": "economy.provider_lifecycle_record.record_provider_lifecycle_event",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "record_provider_lifecycle_event",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyProviderLifecycleRecordRequest",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyProviderLifecycleRecordRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyProviderLifecycleRecordResponse",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyProviderLifecycleRecordResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "provider_lifecycle_record",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Ensure or refresh the admitted actor's "
                                "Economy permit for one priced Service "
                                "operation contract.",
                                "discriminant": "economy.service_operation_permit_ensure.ensure_service_operation_permit",
                                "endpoint_ref": "economy.service_operation_permit_ensure.ensure_service_operation_permit",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "ensure_service_operation_permit",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyServiceOperationPermitEnsureRequest",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyServiceOperationPermitEnsureRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyServiceOperationPermitEnsureResponse",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyServiceOperationPermitEnsureResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "service_operation_permit_ensure",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Reserve service capital from a "
                                "committed Aware Wallet through a "
                                "smart-contract escrow receipt.",
                                "discriminant": "economy.smart_contract_reservation_prepare.prepare_smart_contract_reservation",
                                "endpoint_ref": "economy.smart_contract_reservation_prepare.prepare_smart_contract_reservation",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "prepare_smart_contract_reservation",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomySmartContractReservationPrepareRequest",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomySmartContractReservationPrepareRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomySmartContractReservationPrepareResponse",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomySmartContractReservationPrepareResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "smart_contract_reservation_prepare",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Cancel or expire a pending "
                                "smart-contract reservation and release "
                                "its held wallet capital.",
                                "discriminant": "economy.smart_contract_reservation_release.release_smart_contract_reservation",
                                "endpoint_ref": "economy.smart_contract_reservation_release.release_smart_contract_reservation",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "release_smart_contract_reservation",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomySmartContractReservationReleaseRequest",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomySmartContractReservationReleaseRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomySmartContractReservationReleaseResponse",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomySmartContractReservationReleaseResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "smart_contract_reservation_release",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Finalize a smart-contract settlement "
                                "and reconcile payer/receiver Aware "
                                "Wallet balances.",
                                "discriminant": "economy.smart_contract_settlement_finalize.finalize_smart_contract_settlement",
                                "endpoint_ref": "economy.smart_contract_settlement_finalize.finalize_smart_contract_settlement",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "finalize_smart_contract_settlement",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomySmartContractSettlementFinalizeRequest",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomySmartContractSettlementFinalizeRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomySmartContractSettlementFinalizeResponse",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomySmartContractSettlementFinalizeResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "smart_contract_settlement_finalize",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read the current Economy wallet " "balance for a wallet and coin.",
                                "discriminant": "economy.wallet_balance_describe.describe_wallet_balance",
                                "endpoint_ref": "economy.wallet_balance_describe.describe_wallet_balance",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe_wallet_balance",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletBalanceDescribeRequest",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyWalletBalanceDescribeRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletBalanceDescribeResponse",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyWalletBalanceDescribeResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "wallet_balance_describe",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve an operator-safe wallet "
                                "capital read frame from Economy "
                                "replica truth.",
                                "discriminant": "economy.wallet_capital_frame_resolve.resolve_wallet_capital_frame",
                                "endpoint_ref": "economy.wallet_capital_frame_resolve.resolve_wallet_capital_frame",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_wallet_capital_frame",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletCapitalFrameResolveRequest",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyWalletCapitalFrameResolveRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletCapitalFrameResolveResponse",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyWalletCapitalFrameResolveResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "wallet_capital_frame_resolve",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve the wallet-capital API view "
                                "state from Economy replica truth.",
                                "discriminant": "economy.wallet_capital_view_state_resolve.resolve_wallet_capital_view_state",
                                "endpoint_ref": "economy.wallet_capital_view_state_resolve.resolve_wallet_capital_view_state",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_wallet_capital_view_state",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletCapitalViewStateResolveRequest",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyWalletCapitalViewStateResolveRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletCapitalViewStateV1",
                                    "python_model_ref": "aware_economy_service_dto.economy.view.EconomyWalletCapitalViewStateV1",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "wallet_capital_view_state_resolve",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Record verified terminal no-credit "
                                "evidence and cancel the funding "
                                "intent.",
                                "discriminant": "economy.wallet_funding_cancel.record_wallet_funding_expiration",
                                "endpoint_ref": "economy.wallet_funding_cancel.record_wallet_funding_expiration",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "record_wallet_funding_expiration",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletFundingCancelRequest",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyWalletFundingCancelRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletFundingCancelResponse",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyWalletFundingCancelResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "wallet_funding_cancel",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve provider-neutral committed "
                                "wallet-funding context by intent and "
                                "commit identity.",
                                "discriminant": "economy.wallet_funding_context_resolve.resolve_wallet_funding_context",
                                "endpoint_ref": "economy.wallet_funding_context_resolve.resolve_wallet_funding_context",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_wallet_funding_context",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletFundingContextResolveRequest",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyWalletFundingContextResolveRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletFundingContextResolveResponse",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyWalletFundingContextResolveResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "wallet_funding_context_resolve",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Prepare an Aware-owned wallet funding "
                                "intent before external provider "
                                "confirmation.",
                                "discriminant": "economy.wallet_funding_prepare.prepare_wallet_funding",
                                "endpoint_ref": "economy.wallet_funding_prepare.prepare_wallet_funding",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "prepare_wallet_funding",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletFundingPrepareRequest",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyWalletFundingPrepareRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletFundingPrepareResponse",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyWalletFundingPrepareResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "wallet_funding_prepare",
                        "source_path": "bindings/economy.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Record verified external funding "
                                "evidence as Economy transaction and "
                                "wallet balance truth.",
                                "discriminant": "economy.wallet_funding_record.record_verified_wallet_funding",
                                "endpoint_ref": "economy.wallet_funding_record.record_verified_wallet_funding",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "record_verified_wallet_funding",
                                "request": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletFundingRecordRequest",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyWalletFundingRecordRequest",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_economy_service_dto.economy.EconomyWalletFundingRecordResponse",
                                    "python_model_ref": "aware_economy_service_dto.economy.service.EconomyWalletFundingRecordResponse",
                                    "source_path": "bindings/economy.apis.aware",
                                },
                                "source_path": "bindings/economy.apis.aware",
                            }
                        ],
                        "name": "wallet_funding_record",
                        "source_path": "bindings/economy.apis.aware",
                    },
                ],
                "name": "economy",
                "source_path": "bindings/economy.apis.aware",
            }
        ],
        "fqn_prefix": "aware_economy_service_api",
        "package_name": "economy-service-api",
        "schema_version": 1,
    }
)

ECONOMY__ECONOMY_ACTOR_STATUS__ECONOMY_ACTOR_STATUS_ENDPOINT_REF: Final[str] = (
    "economy.economy_actor_status.economy_actor_status"
)
ECONOMY__ENSURE_FINANCE_ENTITY__ENSURE_FINANCE_ENTITY_ENDPOINT_REF: Final[str] = (
    "economy.ensure_finance_entity.ensure_finance_entity"
)
ECONOMY__PRICE_RESERVATION_FINALIZE__PRICE_RESERVATION_FINALIZE_ENDPOINT_REF: Final[str] = (
    "economy.price_reservation_finalize.price_reservation_finalize"
)
ECONOMY__PRICE_RESERVATION_RESERVE__PRICE_RESERVATION_RESERVE_ENDPOINT_REF: Final[str] = (
    "economy.price_reservation_reserve.price_reservation_reserve"
)
ECONOMY__PROVIDER_LIFECYCLE_RECORD__RECORD_PROVIDER_LIFECYCLE_EVENT_ENDPOINT_REF: Final[str] = (
    "economy.provider_lifecycle_record.record_provider_lifecycle_event"
)
ECONOMY__SERVICE_OPERATION_PERMIT_ENSURE__ENSURE_SERVICE_OPERATION_PERMIT_ENDPOINT_REF: Final[str] = (
    "economy.service_operation_permit_ensure.ensure_service_operation_permit"
)
ECONOMY__SMART_CONTRACT_RESERVATION_PREPARE__PREPARE_SMART_CONTRACT_RESERVATION_ENDPOINT_REF: Final[str] = (
    "economy.smart_contract_reservation_prepare.prepare_smart_contract_reservation"
)
ECONOMY__SMART_CONTRACT_RESERVATION_RELEASE__RELEASE_SMART_CONTRACT_RESERVATION_ENDPOINT_REF: Final[str] = (
    "economy.smart_contract_reservation_release.release_smart_contract_reservation"
)
ECONOMY__SMART_CONTRACT_SETTLEMENT_FINALIZE__FINALIZE_SMART_CONTRACT_SETTLEMENT_ENDPOINT_REF: Final[str] = (
    "economy.smart_contract_settlement_finalize.finalize_smart_contract_settlement"
)
ECONOMY__WALLET_BALANCE_DESCRIBE__DESCRIBE_WALLET_BALANCE_ENDPOINT_REF: Final[str] = (
    "economy.wallet_balance_describe.describe_wallet_balance"
)
ECONOMY__WALLET_CAPITAL_FRAME_RESOLVE__RESOLVE_WALLET_CAPITAL_FRAME_ENDPOINT_REF: Final[str] = (
    "economy.wallet_capital_frame_resolve.resolve_wallet_capital_frame"
)
ECONOMY__WALLET_CAPITAL_VIEW_STATE_RESOLVE__RESOLVE_WALLET_CAPITAL_VIEW_STATE_ENDPOINT_REF: Final[str] = (
    "economy.wallet_capital_view_state_resolve.resolve_wallet_capital_view_state"
)
ECONOMY__WALLET_FUNDING_CANCEL__RECORD_WALLET_FUNDING_EXPIRATION_ENDPOINT_REF: Final[str] = (
    "economy.wallet_funding_cancel.record_wallet_funding_expiration"
)
ECONOMY__WALLET_FUNDING_CONTEXT_RESOLVE__RESOLVE_WALLET_FUNDING_CONTEXT_ENDPOINT_REF: Final[str] = (
    "economy.wallet_funding_context_resolve.resolve_wallet_funding_context"
)
ECONOMY__WALLET_FUNDING_PREPARE__PREPARE_WALLET_FUNDING_ENDPOINT_REF: Final[str] = (
    "economy.wallet_funding_prepare.prepare_wallet_funding"
)
ECONOMY__WALLET_FUNDING_RECORD__RECORD_VERIFIED_WALLET_FUNDING_ENDPOINT_REF: Final[str] = (
    "economy.wallet_funding_record.record_verified_wallet_funding"
)

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "economy.economy_actor_status.economy_actor_status": ECONOMY__ECONOMY_ACTOR_STATUS__ECONOMY_ACTOR_STATUS_ENDPOINT_REF,
    "economy.ensure_finance_entity.ensure_finance_entity": ECONOMY__ENSURE_FINANCE_ENTITY__ENSURE_FINANCE_ENTITY_ENDPOINT_REF,
    "economy.price_reservation_finalize.price_reservation_finalize": ECONOMY__PRICE_RESERVATION_FINALIZE__PRICE_RESERVATION_FINALIZE_ENDPOINT_REF,
    "economy.price_reservation_reserve.price_reservation_reserve": ECONOMY__PRICE_RESERVATION_RESERVE__PRICE_RESERVATION_RESERVE_ENDPOINT_REF,
    "economy.provider_lifecycle_record.record_provider_lifecycle_event": ECONOMY__PROVIDER_LIFECYCLE_RECORD__RECORD_PROVIDER_LIFECYCLE_EVENT_ENDPOINT_REF,
    "economy.service_operation_permit_ensure.ensure_service_operation_permit": ECONOMY__SERVICE_OPERATION_PERMIT_ENSURE__ENSURE_SERVICE_OPERATION_PERMIT_ENDPOINT_REF,
    "economy.smart_contract_reservation_prepare.prepare_smart_contract_reservation": ECONOMY__SMART_CONTRACT_RESERVATION_PREPARE__PREPARE_SMART_CONTRACT_RESERVATION_ENDPOINT_REF,
    "economy.smart_contract_reservation_release.release_smart_contract_reservation": ECONOMY__SMART_CONTRACT_RESERVATION_RELEASE__RELEASE_SMART_CONTRACT_RESERVATION_ENDPOINT_REF,
    "economy.smart_contract_settlement_finalize.finalize_smart_contract_settlement": ECONOMY__SMART_CONTRACT_SETTLEMENT_FINALIZE__FINALIZE_SMART_CONTRACT_SETTLEMENT_ENDPOINT_REF,
    "economy.wallet_balance_describe.describe_wallet_balance": ECONOMY__WALLET_BALANCE_DESCRIBE__DESCRIBE_WALLET_BALANCE_ENDPOINT_REF,
    "economy.wallet_capital_frame_resolve.resolve_wallet_capital_frame": ECONOMY__WALLET_CAPITAL_FRAME_RESOLVE__RESOLVE_WALLET_CAPITAL_FRAME_ENDPOINT_REF,
    "economy.wallet_capital_view_state_resolve.resolve_wallet_capital_view_state": ECONOMY__WALLET_CAPITAL_VIEW_STATE_RESOLVE__RESOLVE_WALLET_CAPITAL_VIEW_STATE_ENDPOINT_REF,
    "economy.wallet_funding_cancel.record_wallet_funding_expiration": ECONOMY__WALLET_FUNDING_CANCEL__RECORD_WALLET_FUNDING_EXPIRATION_ENDPOINT_REF,
    "economy.wallet_funding_context_resolve.resolve_wallet_funding_context": ECONOMY__WALLET_FUNDING_CONTEXT_RESOLVE__RESOLVE_WALLET_FUNDING_CONTEXT_ENDPOINT_REF,
    "economy.wallet_funding_prepare.prepare_wallet_funding": ECONOMY__WALLET_FUNDING_PREPARE__PREPARE_WALLET_FUNDING_ENDPOINT_REF,
    "economy.wallet_funding_record.record_verified_wallet_funding": ECONOMY__WALLET_FUNDING_RECORD__RECORD_VERIFIED_WALLET_FUNDING_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "ECONOMY__ECONOMY_ACTOR_STATUS__ECONOMY_ACTOR_STATUS_ENDPOINT_REF",
    "ECONOMY__ENSURE_FINANCE_ENTITY__ENSURE_FINANCE_ENTITY_ENDPOINT_REF",
    "ECONOMY__PRICE_RESERVATION_FINALIZE__PRICE_RESERVATION_FINALIZE_ENDPOINT_REF",
    "ECONOMY__PRICE_RESERVATION_RESERVE__PRICE_RESERVATION_RESERVE_ENDPOINT_REF",
    "ECONOMY__PROVIDER_LIFECYCLE_RECORD__RECORD_PROVIDER_LIFECYCLE_EVENT_ENDPOINT_REF",
    "ECONOMY__SERVICE_OPERATION_PERMIT_ENSURE__ENSURE_SERVICE_OPERATION_PERMIT_ENDPOINT_REF",
    "ECONOMY__SMART_CONTRACT_RESERVATION_PREPARE__PREPARE_SMART_CONTRACT_RESERVATION_ENDPOINT_REF",
    "ECONOMY__SMART_CONTRACT_RESERVATION_RELEASE__RELEASE_SMART_CONTRACT_RESERVATION_ENDPOINT_REF",
    "ECONOMY__SMART_CONTRACT_SETTLEMENT_FINALIZE__FINALIZE_SMART_CONTRACT_SETTLEMENT_ENDPOINT_REF",
    "ECONOMY__WALLET_BALANCE_DESCRIBE__DESCRIBE_WALLET_BALANCE_ENDPOINT_REF",
    "ECONOMY__WALLET_CAPITAL_FRAME_RESOLVE__RESOLVE_WALLET_CAPITAL_FRAME_ENDPOINT_REF",
    "ECONOMY__WALLET_CAPITAL_VIEW_STATE_RESOLVE__RESOLVE_WALLET_CAPITAL_VIEW_STATE_ENDPOINT_REF",
    "ECONOMY__WALLET_FUNDING_CANCEL__RECORD_WALLET_FUNDING_EXPIRATION_ENDPOINT_REF",
    "ECONOMY__WALLET_FUNDING_CONTEXT_RESOLVE__RESOLVE_WALLET_FUNDING_CONTEXT_ENDPOINT_REF",
    "ECONOMY__WALLET_FUNDING_PREPARE__PREPARE_WALLET_FUNDING_ENDPOINT_REF",
    "ECONOMY__WALLET_FUNDING_RECORD__RECORD_VERIFIED_WALLET_FUNDING_ENDPOINT_REF",
]
