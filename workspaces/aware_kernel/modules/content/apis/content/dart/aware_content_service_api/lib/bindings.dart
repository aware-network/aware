// GENERATED CODE - DO NOT MODIFY BY HAND
// Compiled API bindings for generated Dart SDK wrappers.

import 'dart:convert' as convert;

const String apiPackageName = "content-service-api";
const String apiFqnPrefix = "aware_content_service_api";

final Map<String, Object?> apiInterfaceSpecPayload = _decodeJsonObject(r'''
{
  "apis": [
    {
      "capabilities": [
        {
          "endpoints": [
            {
              "description": "Materialize a provider export document into Content-owned ContentPackage truth.",
              "discriminant": "content.package.materialize_content_package",
              "name": "materialize_content_package",
              "request": {
                "class_ref": "aware_content_service_dto.content.MaterializeContentPackageRequest",
                "source_path": "bindings/content.apis.aware"
              },
              "response": {
                "class_ref": "aware_content_service_dto.content.MaterializeContentPackageResponse",
                "source_path": "bindings/content.apis.aware"
              },
              "source_path": "bindings/content.apis.aware"
            }
          ],
          "name": "package",
          "source_path": "bindings/content.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Resolve one Content object into deterministic text parts and a flattened text payload.",
              "discriminant": "content.text.resolve_content_text",
              "name": "resolve_content_text",
              "request": {
                "class_ref": "aware_content_service_dto.content.ResolveContentTextRequest",
                "source_path": "bindings/content.apis.aware"
              },
              "response": {
                "class_ref": "aware_content_service_dto.content.ResolveContentTextResponse",
                "source_path": "bindings/content.apis.aware"
              },
              "source_path": "bindings/content.apis.aware"
            }
          ],
          "name": "text",
          "source_path": "bindings/content.apis.aware"
        }
      ],
      "name": "content",
      "source_path": "bindings/content.apis.aware"
    }
  ],
  "fqn_prefix": "aware_content_service_api",
  "package_name": "content-service-api",
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
              "description": "Materialize a provider export document into Content-owned ContentPackage truth.",
              "discriminant": "content.package.materialize_content_package",
              "endpoint_ref": "content.package.materialize_content_package",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "materialize_content_package",
              "request": {
                "class_ref": "aware_content_service_dto.content.MaterializeContentPackageRequest",
                "source_path": "bindings/content.apis.aware"
              },
              "response": {
                "class_ref": "aware_content_service_dto.content.MaterializeContentPackageResponse",
                "source_path": "bindings/content.apis.aware"
              },
              "source_path": "bindings/content.apis.aware"
            }
          ],
          "name": "package",
          "source_path": "bindings/content.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Resolve one Content object into deterministic text parts and a flattened text payload.",
              "discriminant": "content.text.resolve_content_text",
              "endpoint_ref": "content.text.resolve_content_text",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "resolve_content_text",
              "request": {
                "class_ref": "aware_content_service_dto.content.ResolveContentTextRequest",
                "source_path": "bindings/content.apis.aware"
              },
              "response": {
                "class_ref": "aware_content_service_dto.content.ResolveContentTextResponse",
                "source_path": "bindings/content.apis.aware"
              },
              "source_path": "bindings/content.apis.aware"
            }
          ],
          "name": "text",
          "source_path": "bindings/content.apis.aware"
        }
      ],
      "name": "content",
      "source_path": "bindings/content.apis.aware"
    }
  ],
  "fqn_prefix": "aware_content_service_api",
  "package_name": "content-service-api",
  "schema_version": 1
}
''');

const String contentPackageMaterializeContentPackageEndpointRef =
    "content.package.materialize_content_package";
const String contentPackageMaterializeContentPackageDiscriminant =
    "content.package.materialize_content_package";
const String contentTextResolveContentTextEndpointRef =
    "content.text.resolve_content_text";
const String contentTextResolveContentTextDiscriminant =
    "content.text.resolve_content_text";

Map<String, Object?> _decodeJsonObject(String raw) {
  final decoded = convert.jsonDecode(raw);
  if (decoded is! Map) {
    throw StateError(
      'Expected compiled API payload to decode to a JSON object.',
    );
  }
  return Map<String, Object?>.from(decoded);
}
