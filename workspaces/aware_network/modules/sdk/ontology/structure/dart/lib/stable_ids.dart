// GENERATED CODE - DO NOT MODIFY BY HAND
// Canonical stable-id derivations (UUIDv5).

import 'package:uuid/uuid.dart';

final Uuid _uuid = Uuid();

final String nsSDK = _uuid.v5(Namespace.url.value, 'aware://sdk/v1');

UuidValue stableSdkConfigId({required String name}) {
  final nameNorm = name.toLowerCase().trim();
  final seed = 'aware:sdk_config:${nameNorm}';
  return UuidValue.fromString(_uuid.v5(nsSDK, seed));
}

UuidValue stableSdkOperationId({
  required UuidValue sdkConfigId,
  required String name,
}) {
  final nameNorm = name.toLowerCase().trim();
  final seed = 'aware:sdk_operation:${sdkConfigId.uuid}:${nameNorm}';
  return UuidValue.fromString(_uuid.v5(nsSDK, seed));
}

UuidValue stableSdkOperationApiCapabilityEndpointId({
  required UuidValue sdkOperationId,
  required String name,
  required UuidValue apiCapabilityEndpointId,
}) {
  final nameNorm = name.toLowerCase().trim();
  final seed =
      'aware:sdk_operation_api_capability_endpoint:${sdkOperationId.uuid}:${nameNorm}:${apiCapabilityEndpointId.uuid}';
  return UuidValue.fromString(_uuid.v5(nsSDK, seed));
}

UuidValue stableSdkOperationDependencyId({
  required UuidValue sdkOperationId,
  required UuidValue targetSdkOperationId,
}) {
  final seed =
      'aware:sdk_operation_dependency:${sdkOperationId.uuid}:${targetSdkOperationId.uuid}';
  return UuidValue.fromString(_uuid.v5(nsSDK, seed));
}

UuidValue stableSdkPackageId({required String name}) {
  final nameNorm = name.toLowerCase().trim();
  final seed = 'aware:sdk_package:${nameNorm}';
  return UuidValue.fromString(_uuid.v5(nsSDK, seed));
}

UuidValue stableSdkPackageApiPackageId({
  required UuidValue sdkPackageId,
  required UuidValue apiPackageId,
}) {
  final seed =
      'aware:sdk_package_api_package:${sdkPackageId.uuid}:${apiPackageId.uuid}';
  return UuidValue.fromString(_uuid.v5(nsSDK, seed));
}

UuidValue stableSdkPackageDependencyId({
  required UuidValue sdkPackageId,
  required UuidValue targetSdkPackageId,
}) {
  final seed =
      'aware:sdk_package_dependency:${sdkPackageId.uuid}:${targetSdkPackageId.uuid}';
  return UuidValue.fromString(_uuid.v5(nsSDK, seed));
}

UuidValue stableSdkPackageImplementationPackageId({
  required UuidValue sdkPackageId,
  required UuidValue codePackageId,
}) {
  final seed =
      'aware:sdk_package_implementation_package:${sdkPackageId.uuid}:${codePackageId.uuid}';
  return UuidValue.fromString(_uuid.v5(nsSDK, seed));
}

UuidValue stableSdkPackageObjectConfigGraphPackageId({
  required UuidValue sdkPackageId,
  required UuidValue objectConfigGraphPackageId,
}) {
  final seed =
      'aware:sdk_package_object_config_graph_package:${sdkPackageId.uuid}:${objectConfigGraphPackageId.uuid}';
  return UuidValue.fromString(_uuid.v5(nsSDK, seed));
}

UuidValue stableSdkSurfaceId({
  required UuidValue sdkConfigId,
  required String name,
}) {
  final nameNorm = name.toLowerCase().trim();
  final seed = 'aware:sdk_surface:${sdkConfigId.uuid}:${nameNorm}';
  return UuidValue.fromString(_uuid.v5(nsSDK, seed));
}

UuidValue stableSdkSurfaceMethodId({
  required UuidValue sdkSurfaceId,
  required String name,
  required UuidValue targetSdkOperationId,
}) {
  final nameNorm = name.toLowerCase().trim();
  final seed =
      'aware:sdk_surface_method:${sdkSurfaceId.uuid}:${nameNorm}:${targetSdkOperationId.uuid}';
  return UuidValue.fromString(_uuid.v5(nsSDK, seed));
}
