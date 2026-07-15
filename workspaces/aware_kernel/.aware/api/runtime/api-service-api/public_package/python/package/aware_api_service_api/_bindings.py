# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "api-service-api"
API_FQN_PREFIX: Final[str] = "aware_api_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Invoke a canonical API operation "
                                "envelope through the API service "
                                "boundary.",
                                "discriminant": "api.operation.invoke",
                                "name": "invoke",
                                "request": {
                                    "class_ref": "aware_api_service_dto.comms.models.ApiOperationRequest",
                                    "source_path": "bindings/api.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_api_service_dto.comms.models.ApiOperationResponse",
                                    "source_path": "bindings/api.apis.aware",
                                },
                                "source_path": "bindings/api.apis.aware",
                            }
                        ],
                        "name": "operation",
                        "source_path": "bindings/api.apis.aware",
                    }
                ],
                "name": "api",
                "source_path": "bindings/api.apis.aware",
            }
        ],
        "fqn_prefix": "aware_api_service_api",
        "package_name": "api-service-api",
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
                                "description": "Invoke a canonical API operation "
                                "envelope through the API service "
                                "boundary.",
                                "discriminant": "api.operation.invoke",
                                "endpoint_ref": "api.operation.invoke",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "invoke",
                                "request": {
                                    "class_ref": "aware_api_service_dto.comms.models.ApiOperationRequest",
                                    "python_model_ref": "aware_api_service_dto.comms.models.api.ApiOperationRequest",
                                    "source_path": "bindings/api.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_api_service_dto.comms.models.ApiOperationResponse",
                                    "python_model_ref": "aware_api_service_dto.comms.models.api.ApiOperationResponse",
                                    "source_path": "bindings/api.apis.aware",
                                },
                                "source_path": "bindings/api.apis.aware",
                            }
                        ],
                        "name": "operation",
                        "source_path": "bindings/api.apis.aware",
                    }
                ],
                "name": "api",
                "source_path": "bindings/api.apis.aware",
            }
        ],
        "fqn_prefix": "aware_api_service_api",
        "package_name": "api-service-api",
        "schema_version": 1,
    }
)

API__OPERATION__INVOKE_ENDPOINT_REF: Final[str] = "api.operation.invoke"

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "api.operation.invoke": API__OPERATION__INVOKE_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "API__OPERATION__INVOKE_ENDPOINT_REF",
]
