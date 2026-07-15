# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "hub-service-api"
API_FQN_PREFIX: Final[str] = "aware_hub_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Publish a generic immutable artifact "
                                "payload lock through Hub authority "
                                "truth.",
                                "discriminant": "hub.artifact.publish",
                                "name": "publish",
                                "request": {
                                    "class_ref": "aware_hub_service_dto.hub.PublishHubArtifactRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_hub_service_dto.hub.PublishHubArtifactResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            },
                            {
                                "description": "Resolve a generic immutable artifact "
                                "payload lock through Hub authority "
                                "truth.",
                                "discriminant": "hub.artifact.resolve",
                                "name": "resolve",
                                "request": {
                                    "class_ref": "aware_hub_service_dto.hub.ResolveHubArtifactRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_hub_service_dto.hub.ResolveHubArtifactResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            },
                        ],
                        "name": "artifact",
                        "source_path": "bindings/hub.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Describe one CodePackage descriptor "
                                "through Hub package authority truth.",
                                "discriminant": "hub.code_package.describe",
                                "name": "describe",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.DescribeCodePackageRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.DescribeCodePackageResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            },
                            {
                                "description": "Discover public Hub CodePackage "
                                "channel heads for pre-identity map "
                                "surfaces.",
                                "discriminant": "hub.code_package.discover_channel_heads",
                                "name": "discover_channel_heads",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.DiscoverCodePackageChannelHeadsRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.DiscoverCodePackageChannelHeadsResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            },
                            {
                                "description": "Return one explicit CodePackage "
                                "artifact download lock through Hub "
                                "package authority truth.",
                                "discriminant": "hub.code_package.download",
                                "name": "download",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.DownloadCodePackageRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.DownloadCodePackageResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            },
                            {
                                "description": "Register one staged CodePackage "
                                "artifact lock into Hub package "
                                "authority truth.",
                                "discriminant": "hub.code_package.publish",
                                "name": "publish",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.PublishCodePackageRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.PublishCodePackageResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            },
                            {
                                "description": "Resolve one exact CodePackage artifact "
                                "lock through Hub package authority "
                                "truth.",
                                "discriminant": "hub.code_package.resolve",
                                "name": "resolve",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodePackageRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodePackageResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            },
                            {
                                "description": "Search CodePackage descriptors through " "Hub package authority truth.",
                                "discriminant": "hub.code_package.search",
                                "name": "search",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.SearchCodePackageRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.SearchCodePackageResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            },
                        ],
                        "name": "code_package",
                        "source_path": "bindings/hub.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve a deployment artifact payload "
                                "lock through Hub authority truth.",
                                "discriminant": "hub.deployment_artifact.resolve",
                                "name": "resolve",
                                "request": {
                                    "class_ref": "aware_hub_service_dto.hub.ResolveDeploymentArtifactRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_hub_service_dto.hub.ResolveDeploymentArtifactResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            }
                        ],
                        "name": "deployment_artifact",
                        "source_path": "bindings/hub.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Discover the public Hub "
                                "package/revision map for pre-identity "
                                "Control surfaces.",
                                "discriminant": "hub.public_map.discover",
                                "name": "discover",
                                "request": {
                                    "class_ref": "aware_hub_service_dto.hub.DiscoverPublicMapRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_hub_service_dto.hub.DiscoverPublicMapResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            }
                        ],
                        "name": "public_map",
                        "source_path": "bindings/hub.apis.aware",
                    },
                ],
                "name": "hub",
                "source_path": "bindings/hub.apis.aware",
            }
        ],
        "fqn_prefix": "aware_hub_service_api",
        "package_name": "hub-service-api",
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
                                "description": "Publish a generic immutable artifact "
                                "payload lock through Hub authority "
                                "truth.",
                                "discriminant": "hub.artifact.publish",
                                "endpoint_ref": "hub.artifact.publish",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "publish",
                                "request": {
                                    "class_ref": "aware_hub_service_dto.hub.PublishHubArtifactRequest",
                                    "python_model_ref": "aware_hub_service_dto.hub.artifact_authority.PublishHubArtifactRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_hub_service_dto.hub.PublishHubArtifactResponse",
                                    "python_model_ref": "aware_hub_service_dto.hub.artifact_authority.PublishHubArtifactResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve a generic immutable artifact "
                                "payload lock through Hub authority "
                                "truth.",
                                "discriminant": "hub.artifact.resolve",
                                "endpoint_ref": "hub.artifact.resolve",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve",
                                "request": {
                                    "class_ref": "aware_hub_service_dto.hub.ResolveHubArtifactRequest",
                                    "python_model_ref": "aware_hub_service_dto.hub.artifact_authority.ResolveHubArtifactRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_hub_service_dto.hub.ResolveHubArtifactResponse",
                                    "python_model_ref": "aware_hub_service_dto.hub.artifact_authority.ResolveHubArtifactResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            },
                        ],
                        "name": "artifact",
                        "source_path": "bindings/hub.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Describe one CodePackage descriptor "
                                "through Hub package authority truth.",
                                "discriminant": "hub.code_package.describe",
                                "endpoint_ref": "hub.code_package.describe",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.DescribeCodePackageRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_distribution.DescribeCodePackageRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.DescribeCodePackageResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_distribution.DescribeCodePackageResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Discover public Hub CodePackage "
                                "channel heads for pre-identity map "
                                "surfaces.",
                                "discriminant": "hub.code_package.discover_channel_heads",
                                "endpoint_ref": "hub.code_package.discover_channel_heads",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "discover_channel_heads",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.DiscoverCodePackageChannelHeadsRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_distribution.DiscoverCodePackageChannelHeadsRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.DiscoverCodePackageChannelHeadsResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_distribution.DiscoverCodePackageChannelHeadsResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Return one explicit CodePackage "
                                "artifact download lock through Hub "
                                "package authority truth.",
                                "discriminant": "hub.code_package.download",
                                "endpoint_ref": "hub.code_package.download",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "download",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.DownloadCodePackageRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_distribution.DownloadCodePackageRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.DownloadCodePackageResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_distribution.DownloadCodePackageResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Register one staged CodePackage "
                                "artifact lock into Hub package "
                                "authority truth.",
                                "discriminant": "hub.code_package.publish",
                                "endpoint_ref": "hub.code_package.publish",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "publish",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.PublishCodePackageRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_distribution.PublishCodePackageRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.PublishCodePackageResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_distribution.PublishCodePackageResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve one exact CodePackage artifact "
                                "lock through Hub package authority "
                                "truth.",
                                "discriminant": "hub.code_package.resolve",
                                "endpoint_ref": "hub.code_package.resolve",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodePackageRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_distribution.ResolveCodePackageRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.ResolveCodePackageResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_distribution.ResolveCodePackageResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Search CodePackage descriptors through " "Hub package authority truth.",
                                "discriminant": "hub.code_package.search",
                                "endpoint_ref": "hub.code_package.search",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "search",
                                "request": {
                                    "class_ref": "aware_code_service_dto.code.SearchCodePackageRequest",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_distribution.SearchCodePackageRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_code_service_dto.code.SearchCodePackageResponse",
                                    "python_model_ref": "aware_code_service_dto.code.features.package_distribution.SearchCodePackageResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            },
                        ],
                        "name": "code_package",
                        "source_path": "bindings/hub.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve a deployment artifact payload "
                                "lock through Hub authority truth.",
                                "discriminant": "hub.deployment_artifact.resolve",
                                "endpoint_ref": "hub.deployment_artifact.resolve",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve",
                                "request": {
                                    "class_ref": "aware_hub_service_dto.hub.ResolveDeploymentArtifactRequest",
                                    "python_model_ref": "aware_hub_service_dto.hub.deployment_artifact_authority.ResolveDeploymentArtifactRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_hub_service_dto.hub.ResolveDeploymentArtifactResponse",
                                    "python_model_ref": "aware_hub_service_dto.hub.deployment_artifact_authority.ResolveDeploymentArtifactResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            }
                        ],
                        "name": "deployment_artifact",
                        "source_path": "bindings/hub.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Discover the public Hub "
                                "package/revision map for pre-identity "
                                "Control surfaces.",
                                "discriminant": "hub.public_map.discover",
                                "endpoint_ref": "hub.public_map.discover",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "discover",
                                "request": {
                                    "class_ref": "aware_hub_service_dto.hub.DiscoverPublicMapRequest",
                                    "python_model_ref": "aware_hub_service_dto.hub.public_map_discovery.DiscoverPublicMapRequest",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_hub_service_dto.hub.DiscoverPublicMapResponse",
                                    "python_model_ref": "aware_hub_service_dto.hub.public_map_discovery.DiscoverPublicMapResponse",
                                    "source_path": "bindings/hub.apis.aware",
                                },
                                "source_path": "bindings/hub.apis.aware",
                            }
                        ],
                        "name": "public_map",
                        "source_path": "bindings/hub.apis.aware",
                    },
                ],
                "name": "hub",
                "source_path": "bindings/hub.apis.aware",
            }
        ],
        "fqn_prefix": "aware_hub_service_api",
        "package_name": "hub-service-api",
        "schema_version": 1,
    }
)

HUB__ARTIFACT__PUBLISH_ENDPOINT_REF: Final[str] = "hub.artifact.publish"
HUB__ARTIFACT__RESOLVE_ENDPOINT_REF: Final[str] = "hub.artifact.resolve"
HUB__CODE_PACKAGE__DESCRIBE_ENDPOINT_REF: Final[str] = "hub.code_package.describe"
HUB__CODE_PACKAGE__DISCOVER_CHANNEL_HEADS_ENDPOINT_REF: Final[str] = "hub.code_package.discover_channel_heads"
HUB__CODE_PACKAGE__DOWNLOAD_ENDPOINT_REF: Final[str] = "hub.code_package.download"
HUB__CODE_PACKAGE__PUBLISH_ENDPOINT_REF: Final[str] = "hub.code_package.publish"
HUB__CODE_PACKAGE__RESOLVE_ENDPOINT_REF: Final[str] = "hub.code_package.resolve"
HUB__CODE_PACKAGE__SEARCH_ENDPOINT_REF: Final[str] = "hub.code_package.search"
HUB__DEPLOYMENT_ARTIFACT__RESOLVE_ENDPOINT_REF: Final[str] = "hub.deployment_artifact.resolve"
HUB__PUBLIC_MAP__DISCOVER_ENDPOINT_REF: Final[str] = "hub.public_map.discover"

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "hub.artifact.publish": HUB__ARTIFACT__PUBLISH_ENDPOINT_REF,
    "hub.artifact.resolve": HUB__ARTIFACT__RESOLVE_ENDPOINT_REF,
    "hub.code_package.describe": HUB__CODE_PACKAGE__DESCRIBE_ENDPOINT_REF,
    "hub.code_package.discover_channel_heads": HUB__CODE_PACKAGE__DISCOVER_CHANNEL_HEADS_ENDPOINT_REF,
    "hub.code_package.download": HUB__CODE_PACKAGE__DOWNLOAD_ENDPOINT_REF,
    "hub.code_package.publish": HUB__CODE_PACKAGE__PUBLISH_ENDPOINT_REF,
    "hub.code_package.resolve": HUB__CODE_PACKAGE__RESOLVE_ENDPOINT_REF,
    "hub.code_package.search": HUB__CODE_PACKAGE__SEARCH_ENDPOINT_REF,
    "hub.deployment_artifact.resolve": HUB__DEPLOYMENT_ARTIFACT__RESOLVE_ENDPOINT_REF,
    "hub.public_map.discover": HUB__PUBLIC_MAP__DISCOVER_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "HUB__ARTIFACT__PUBLISH_ENDPOINT_REF",
    "HUB__ARTIFACT__RESOLVE_ENDPOINT_REF",
    "HUB__CODE_PACKAGE__DESCRIBE_ENDPOINT_REF",
    "HUB__CODE_PACKAGE__DISCOVER_CHANNEL_HEADS_ENDPOINT_REF",
    "HUB__CODE_PACKAGE__DOWNLOAD_ENDPOINT_REF",
    "HUB__CODE_PACKAGE__PUBLISH_ENDPOINT_REF",
    "HUB__CODE_PACKAGE__RESOLVE_ENDPOINT_REF",
    "HUB__CODE_PACKAGE__SEARCH_ENDPOINT_REF",
    "HUB__DEPLOYMENT_ARTIFACT__RESOLVE_ENDPOINT_REF",
    "HUB__PUBLIC_MAP__DISCOVER_ENDPOINT_REF",
]
