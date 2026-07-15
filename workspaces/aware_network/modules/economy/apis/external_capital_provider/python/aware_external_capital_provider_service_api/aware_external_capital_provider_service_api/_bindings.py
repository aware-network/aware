# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "external-capital-provider-service-api"
API_FQN_PREFIX: Final[str] = "aware_external_capital_provider_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Create an external-provider "
                                "continuation for a committed Aware "
                                "wallet-funding intent.",
                                "discriminant": "external_capital.wallet_funding_session.create_wallet_funding_session",
                                "name": "create_wallet_funding_session",
                                "request": {
                                    "class_ref": "aware_external_capital_provider_service_dto.external_capital.ExternalCapitalWalletFundingSessionRequest",
                                    "source_path": "bindings/external_capital_provider.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_external_capital_provider_service_dto.external_capital.ExternalCapitalWalletFundingSessionResponse",
                                    "source_path": "bindings/external_capital_provider.apis.aware",
                                },
                                "source_path": "bindings/external_capital_provider.apis.aware",
                            }
                        ],
                        "name": "wallet_funding_session",
                        "source_path": "bindings/external_capital_provider.apis.aware",
                    }
                ],
                "name": "external_capital",
                "source_path": "bindings/external_capital_provider.apis.aware",
            }
        ],
        "fqn_prefix": "aware_external_capital_provider_service_api",
        "package_name": "external-capital-provider-service-api",
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
                                "description": "Create an external-provider "
                                "continuation for a committed Aware "
                                "wallet-funding intent.",
                                "discriminant": "external_capital.wallet_funding_session.create_wallet_funding_session",
                                "endpoint_ref": "external_capital.wallet_funding_session.create_wallet_funding_session",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "create_wallet_funding_session",
                                "request": {
                                    "class_ref": "aware_external_capital_provider_service_dto.external_capital.ExternalCapitalWalletFundingSessionRequest",
                                    "python_model_ref": "aware_external_capital_provider_service_dto.external_capital.wallet_funding.ExternalCapitalWalletFundingSessionRequest",
                                    "source_path": "bindings/external_capital_provider.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_external_capital_provider_service_dto.external_capital.ExternalCapitalWalletFundingSessionResponse",
                                    "python_model_ref": "aware_external_capital_provider_service_dto.external_capital.wallet_funding.ExternalCapitalWalletFundingSessionResponse",
                                    "source_path": "bindings/external_capital_provider.apis.aware",
                                },
                                "source_path": "bindings/external_capital_provider.apis.aware",
                            }
                        ],
                        "name": "wallet_funding_session",
                        "source_path": "bindings/external_capital_provider.apis.aware",
                    }
                ],
                "name": "external_capital",
                "source_path": "bindings/external_capital_provider.apis.aware",
            }
        ],
        "fqn_prefix": "aware_external_capital_provider_service_api",
        "package_name": "external-capital-provider-service-api",
        "schema_version": 1,
    }
)

EXTERNAL_CAPITAL__WALLET_FUNDING_SESSION__CREATE_WALLET_FUNDING_SESSION_ENDPOINT_REF: Final[str] = (
    "external_capital.wallet_funding_session.create_wallet_funding_session"
)

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "external_capital.wallet_funding_session.create_wallet_funding_session": EXTERNAL_CAPITAL__WALLET_FUNDING_SESSION__CREATE_WALLET_FUNDING_SESSION_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "EXTERNAL_CAPITAL__WALLET_FUNDING_SESSION__CREATE_WALLET_FUNDING_SESSION_ENDPOINT_REF",
]
