# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "service-service-api"
API_FQN_PREFIX: Final[str] = "aware_service_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Invoke a canonical Service operation "
                                "envelope through the Service service "
                                "boundary.",
                                "discriminant": "service.operation.invoke",
                                "name": "invoke",
                                "request": {
                                    "class_ref": "aware_service_service_dto.comms.models.ServiceOperationRequest",
                                    "source_path": "bindings/service.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_service_service_dto.comms.models.ServiceOperationResponse",
                                    "source_path": "bindings/service.apis.aware",
                                },
                                "source_path": "bindings/service.apis.aware",
                            }
                        ],
                        "name": "operation",
                        "source_path": "bindings/service.apis.aware",
                    }
                ],
                "name": "service",
                "source_path": "bindings/service.apis.aware",
            }
        ],
        "fqn_prefix": "aware_service_service_api",
        "package_name": "service-service-api",
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
                                "description": "Invoke a canonical Service operation "
                                "envelope through the Service service "
                                "boundary.",
                                "discriminant": "service.operation.invoke",
                                "endpoint_ref": "service.operation.invoke",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "invoke",
                                "request": {
                                    "class_ref": "aware_service_service_dto.comms.models.ServiceOperationRequest",
                                    "python_model_ref": "aware_service_service_dto.comms.models.service.ServiceOperationRequest",
                                    "source_path": "bindings/service.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_service_service_dto.comms.models.ServiceOperationResponse",
                                    "python_model_ref": "aware_service_service_dto.comms.models.service.ServiceOperationResponse",
                                    "source_path": "bindings/service.apis.aware",
                                },
                                "source_path": "bindings/service.apis.aware",
                            }
                        ],
                        "name": "operation",
                        "source_path": "bindings/service.apis.aware",
                    }
                ],
                "name": "service",
                "source_path": "bindings/service.apis.aware",
            }
        ],
        "fqn_prefix": "aware_service_service_api",
        "package_name": "service-service-api",
        "schema_version": 1,
    }
)

SERVICE__OPERATION__INVOKE_ENDPOINT_REF: Final[str] = "service.operation.invoke"

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "service.operation.invoke": SERVICE__OPERATION__INVOKE_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "SERVICE__OPERATION__INVOKE_ENDPOINT_REF",
]
