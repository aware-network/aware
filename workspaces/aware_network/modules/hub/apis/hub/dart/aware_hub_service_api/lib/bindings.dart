// GENERATED CODE - DO NOT MODIFY BY HAND
// Compiled API bindings for generated Dart SDK wrappers.

import 'dart:convert' as convert;

const String apiPackageName = "hub-service-api";
const String apiFqnPrefix = "aware_hub_service_api";

final Map<String, Object?> apiInterfaceSpecPayload = _decodeJsonObject(r'''
{
  "apis": [
    {
      "capabilities": [
        {
          "endpoints": [
            {
              "description": "Publish a generic immutable artifact payload lock through Hub authority truth.",
              "discriminant": "hub.artifact.publish",
              "name": "publish",
              "request": {
                "class_ref": "aware_hub_service_dto.hub.PublishHubArtifactRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_hub_service_dto.hub.PublishHubArtifactResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            },
            {
              "description": "Resolve a generic immutable artifact payload lock through Hub authority truth.",
              "discriminant": "hub.artifact.resolve",
              "name": "resolve",
              "request": {
                "class_ref": "aware_hub_service_dto.hub.ResolveHubArtifactRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_hub_service_dto.hub.ResolveHubArtifactResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            }
          ],
          "name": "artifact",
          "source_path": "bindings/hub.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Describe one CodePackage descriptor through Hub package authority truth.",
              "discriminant": "hub.code_package.describe",
              "name": "describe",
              "request": {
                "class_ref": "aware_code_service_dto.code.DescribeCodePackageRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_code_service_dto.code.DescribeCodePackageResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            },
            {
              "description": "Discover public Hub CodePackage channel heads for pre-identity map surfaces.",
              "discriminant": "hub.code_package.discover_channel_heads",
              "name": "discover_channel_heads",
              "request": {
                "class_ref": "aware_code_service_dto.code.DiscoverCodePackageChannelHeadsRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_code_service_dto.code.DiscoverCodePackageChannelHeadsResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            },
            {
              "description": "Return one explicit CodePackage artifact download lock through Hub package authority truth.",
              "discriminant": "hub.code_package.download",
              "name": "download",
              "request": {
                "class_ref": "aware_code_service_dto.code.DownloadCodePackageRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_code_service_dto.code.DownloadCodePackageResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            },
            {
              "description": "Register one staged CodePackage artifact lock into Hub package authority truth.",
              "discriminant": "hub.code_package.publish",
              "name": "publish",
              "request": {
                "class_ref": "aware_code_service_dto.code.PublishCodePackageRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_code_service_dto.code.PublishCodePackageResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            },
            {
              "description": "Resolve one exact CodePackage artifact lock through Hub package authority truth.",
              "discriminant": "hub.code_package.resolve",
              "name": "resolve",
              "request": {
                "class_ref": "aware_code_service_dto.code.ResolveCodePackageRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_code_service_dto.code.ResolveCodePackageResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            },
            {
              "description": "Search CodePackage descriptors through Hub package authority truth.",
              "discriminant": "hub.code_package.search",
              "name": "search",
              "request": {
                "class_ref": "aware_code_service_dto.code.SearchCodePackageRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_code_service_dto.code.SearchCodePackageResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            }
          ],
          "name": "code_package",
          "source_path": "bindings/hub.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Resolve a deployment artifact payload lock through Hub authority truth.",
              "discriminant": "hub.deployment_artifact.resolve",
              "name": "resolve",
              "request": {
                "class_ref": "aware_hub_service_dto.hub.ResolveDeploymentArtifactRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_hub_service_dto.hub.ResolveDeploymentArtifactResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            }
          ],
          "name": "deployment_artifact",
          "source_path": "bindings/hub.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Discover the public Hub package/revision map for pre-identity Control surfaces.",
              "discriminant": "hub.public_map.discover",
              "name": "discover",
              "request": {
                "class_ref": "aware_hub_service_dto.hub.DiscoverPublicMapRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_hub_service_dto.hub.DiscoverPublicMapResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            }
          ],
          "name": "public_map",
          "source_path": "bindings/hub.apis.aware"
        }
      ],
      "name": "hub",
      "source_path": "bindings/hub.apis.aware"
    }
  ],
  "fqn_prefix": "aware_hub_service_api",
  "package_name": "hub-service-api",
  "schema_version": 1
}
''');

final Map<String, Object?> apiInvocationManifestPayload = _decodeJsonObject(r'''
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
              "description": "Publish a generic immutable artifact payload lock through Hub authority truth.",
              "discriminant": "hub.artifact.publish",
              "endpoint_ref": "hub.artifact.publish",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "publish",
              "request": {
                "class_ref": "aware_hub_service_dto.hub.PublishHubArtifactRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_hub_service_dto.hub.PublishHubArtifactResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            },
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Resolve a generic immutable artifact payload lock through Hub authority truth.",
              "discriminant": "hub.artifact.resolve",
              "endpoint_ref": "hub.artifact.resolve",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "resolve",
              "request": {
                "class_ref": "aware_hub_service_dto.hub.ResolveHubArtifactRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_hub_service_dto.hub.ResolveHubArtifactResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            }
          ],
          "name": "artifact",
          "source_path": "bindings/hub.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Describe one CodePackage descriptor through Hub package authority truth.",
              "discriminant": "hub.code_package.describe",
              "endpoint_ref": "hub.code_package.describe",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "describe",
              "request": {
                "class_ref": "aware_code_service_dto.code.DescribeCodePackageRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_code_service_dto.code.DescribeCodePackageResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            },
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Discover public Hub CodePackage channel heads for pre-identity map surfaces.",
              "discriminant": "hub.code_package.discover_channel_heads",
              "endpoint_ref": "hub.code_package.discover_channel_heads",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "discover_channel_heads",
              "request": {
                "class_ref": "aware_code_service_dto.code.DiscoverCodePackageChannelHeadsRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_code_service_dto.code.DiscoverCodePackageChannelHeadsResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            },
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Return one explicit CodePackage artifact download lock through Hub package authority truth.",
              "discriminant": "hub.code_package.download",
              "endpoint_ref": "hub.code_package.download",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "download",
              "request": {
                "class_ref": "aware_code_service_dto.code.DownloadCodePackageRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_code_service_dto.code.DownloadCodePackageResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            },
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Register one staged CodePackage artifact lock into Hub package authority truth.",
              "discriminant": "hub.code_package.publish",
              "endpoint_ref": "hub.code_package.publish",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "publish",
              "request": {
                "class_ref": "aware_code_service_dto.code.PublishCodePackageRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_code_service_dto.code.PublishCodePackageResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            },
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Resolve one exact CodePackage artifact lock through Hub package authority truth.",
              "discriminant": "hub.code_package.resolve",
              "endpoint_ref": "hub.code_package.resolve",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "resolve",
              "request": {
                "class_ref": "aware_code_service_dto.code.ResolveCodePackageRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_code_service_dto.code.ResolveCodePackageResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            },
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Search CodePackage descriptors through Hub package authority truth.",
              "discriminant": "hub.code_package.search",
              "endpoint_ref": "hub.code_package.search",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "search",
              "request": {
                "class_ref": "aware_code_service_dto.code.SearchCodePackageRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_code_service_dto.code.SearchCodePackageResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            }
          ],
          "name": "code_package",
          "source_path": "bindings/hub.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Resolve a deployment artifact payload lock through Hub authority truth.",
              "discriminant": "hub.deployment_artifact.resolve",
              "endpoint_ref": "hub.deployment_artifact.resolve",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "resolve",
              "request": {
                "class_ref": "aware_hub_service_dto.hub.ResolveDeploymentArtifactRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_hub_service_dto.hub.ResolveDeploymentArtifactResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            }
          ],
          "name": "deployment_artifact",
          "source_path": "bindings/hub.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Discover the public Hub package/revision map for pre-identity Control surfaces.",
              "discriminant": "hub.public_map.discover",
              "endpoint_ref": "hub.public_map.discover",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "discover",
              "request": {
                "class_ref": "aware_hub_service_dto.hub.DiscoverPublicMapRequest",
                "source_path": "bindings/hub.apis.aware"
              },
              "response": {
                "class_ref": "aware_hub_service_dto.hub.DiscoverPublicMapResponse",
                "source_path": "bindings/hub.apis.aware"
              },
              "source_path": "bindings/hub.apis.aware"
            }
          ],
          "name": "public_map",
          "source_path": "bindings/hub.apis.aware"
        }
      ],
      "name": "hub",
      "source_path": "bindings/hub.apis.aware"
    }
  ],
  "fqn_prefix": "aware_hub_service_api",
  "package_name": "hub-service-api",
  "schema_version": 1
}
''');

const String hubArtifactPublishEndpointRef = "hub.artifact.publish";
const String hubArtifactPublishDiscriminant = "hub.artifact.publish";
const String hubArtifactResolveEndpointRef = "hub.artifact.resolve";
const String hubArtifactResolveDiscriminant = "hub.artifact.resolve";
const String hubCodePackageDescribeEndpointRef = "hub.code_package.describe";
const String hubCodePackageDescribeDiscriminant = "hub.code_package.describe";
const String hubCodePackageDiscoverChannelHeadsEndpointRef =
    "hub.code_package.discover_channel_heads";
const String hubCodePackageDiscoverChannelHeadsDiscriminant =
    "hub.code_package.discover_channel_heads";
const String hubCodePackageDownloadEndpointRef = "hub.code_package.download";
const String hubCodePackageDownloadDiscriminant = "hub.code_package.download";
const String hubCodePackagePublishEndpointRef = "hub.code_package.publish";
const String hubCodePackagePublishDiscriminant = "hub.code_package.publish";
const String hubCodePackageResolveEndpointRef = "hub.code_package.resolve";
const String hubCodePackageResolveDiscriminant = "hub.code_package.resolve";
const String hubCodePackageSearchEndpointRef = "hub.code_package.search";
const String hubCodePackageSearchDiscriminant = "hub.code_package.search";
const String hubDeploymentArtifactResolveEndpointRef =
    "hub.deployment_artifact.resolve";
const String hubDeploymentArtifactResolveDiscriminant =
    "hub.deployment_artifact.resolve";
const String hubPublicMapDiscoverEndpointRef = "hub.public_map.discover";
const String hubPublicMapDiscoverDiscriminant = "hub.public_map.discover";

Map<String, Object?> _decodeJsonObject(String raw) {
  final decoded = convert.jsonDecode(raw);
  if (decoded is! Map) {
    throw StateError(
      'Expected compiled API payload to decode to a JSON object.',
    );
  }
  return Map<String, Object?>.from(decoded);
}
