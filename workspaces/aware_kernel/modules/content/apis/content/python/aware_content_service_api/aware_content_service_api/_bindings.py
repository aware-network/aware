# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "content-service-api"
API_FQN_PREFIX: Final[str] = "aware_content_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Materialize a provider export document "
                                "into Content-owned ContentPackage "
                                "truth.",
                                "discriminant": "content.package.materialize_content_package",
                                "name": "materialize_content_package",
                                "request": {
                                    "class_ref": "aware_content_service_dto.content.MaterializeContentPackageRequest",
                                    "source_path": "bindings/content.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_content_service_dto.content.MaterializeContentPackageResponse",
                                    "source_path": "bindings/content.apis.aware",
                                },
                                "source_path": "bindings/content.apis.aware",
                            }
                        ],
                        "name": "package",
                        "source_path": "bindings/content.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve one Content object into "
                                "deterministic text parts and a "
                                "flattened text payload.",
                                "discriminant": "content.text.resolve_content_text",
                                "name": "resolve_content_text",
                                "request": {
                                    "class_ref": "aware_content_service_dto.content.ResolveContentTextRequest",
                                    "source_path": "bindings/content.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_content_service_dto.content.ResolveContentTextResponse",
                                    "source_path": "bindings/content.apis.aware",
                                },
                                "source_path": "bindings/content.apis.aware",
                            }
                        ],
                        "name": "text",
                        "source_path": "bindings/content.apis.aware",
                    },
                ],
                "name": "content",
                "source_path": "bindings/content.apis.aware",
            }
        ],
        "fqn_prefix": "aware_content_service_api",
        "package_name": "content-service-api",
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
                                "description": "Materialize a provider export document "
                                "into Content-owned ContentPackage "
                                "truth.",
                                "discriminant": "content.package.materialize_content_package",
                                "endpoint_ref": "content.package.materialize_content_package",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "materialize_content_package",
                                "request": {
                                    "class_ref": "aware_content_service_dto.content.MaterializeContentPackageRequest",
                                    "python_model_ref": "aware_content_service_dto.content.content_service_operation.MaterializeContentPackageRequest",
                                    "source_path": "bindings/content.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_content_service_dto.content.MaterializeContentPackageResponse",
                                    "python_model_ref": "aware_content_service_dto.content.content_service_operation.MaterializeContentPackageResponse",
                                    "source_path": "bindings/content.apis.aware",
                                },
                                "source_path": "bindings/content.apis.aware",
                            }
                        ],
                        "name": "package",
                        "source_path": "bindings/content.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve one Content object into "
                                "deterministic text parts and a "
                                "flattened text payload.",
                                "discriminant": "content.text.resolve_content_text",
                                "endpoint_ref": "content.text.resolve_content_text",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_content_text",
                                "request": {
                                    "class_ref": "aware_content_service_dto.content.ResolveContentTextRequest",
                                    "python_model_ref": "aware_content_service_dto.content.content_service_operation.ResolveContentTextRequest",
                                    "source_path": "bindings/content.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_content_service_dto.content.ResolveContentTextResponse",
                                    "python_model_ref": "aware_content_service_dto.content.content_service_operation.ResolveContentTextResponse",
                                    "source_path": "bindings/content.apis.aware",
                                },
                                "source_path": "bindings/content.apis.aware",
                            }
                        ],
                        "name": "text",
                        "source_path": "bindings/content.apis.aware",
                    },
                ],
                "name": "content",
                "source_path": "bindings/content.apis.aware",
            }
        ],
        "fqn_prefix": "aware_content_service_api",
        "package_name": "content-service-api",
        "schema_version": 1,
    }
)

CONTENT__PACKAGE__MATERIALIZE_CONTENT_PACKAGE_ENDPOINT_REF: Final[str] = "content.package.materialize_content_package"
CONTENT__TEXT__RESOLVE_CONTENT_TEXT_ENDPOINT_REF: Final[str] = "content.text.resolve_content_text"

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "content.package.materialize_content_package": CONTENT__PACKAGE__MATERIALIZE_CONTENT_PACKAGE_ENDPOINT_REF,
    "content.text.resolve_content_text": CONTENT__TEXT__RESOLVE_CONTENT_TEXT_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "CONTENT__PACKAGE__MATERIALIZE_CONTENT_PACKAGE_ENDPOINT_REF",
    "CONTENT__TEXT__RESOLVE_CONTENT_TEXT_ENDPOINT_REF",
]
