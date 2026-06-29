// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'sdk_operation_api_capability_endpoint_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_SdkOperationApiCapabilityEndpoint _$SdkOperationApiCapabilityEndpointFromJson(
  Map<String, dynamic> json,
) => _SdkOperationApiCapabilityEndpoint(
  id: const UuidValueConverter().fromJson(json['id'] as String),
  apiCapabilityEndpoint: json['api_capability_endpoint'] == null
      ? null
      : ApiCapabilityEndpoint.fromJson(
          json['api_capability_endpoint'] as Map<String, dynamic>,
        ),
  name: json['name'] as String,
  endpointRef: json['endpoint_ref'] as String?,
  discriminant: json['discriminant'] as String?,
  role: json['role'] as String,
  order: (json['order'] as num).toInt(),
  required_: json['required'] as bool,
  sdkOperationId: const UuidValueConverter().fromJson(
    json['sdk_operation_id'] as String,
  ),
  apiCapabilityEndpointId: _$JsonConverterFromJson<String, UuidValue>(
    json['api_capability_endpoint_id'],
    const UuidValueConverter().fromJson,
  ),
);

Map<String, dynamic> _$SdkOperationApiCapabilityEndpointToJson(
  _SdkOperationApiCapabilityEndpoint instance,
) => <String, dynamic>{
  'id': const UuidValueConverter().toJson(instance.id),
  'api_capability_endpoint': instance.apiCapabilityEndpoint?.toJson(),
  'name': instance.name,
  'endpoint_ref': instance.endpointRef,
  'discriminant': instance.discriminant,
  'role': instance.role,
  'order': instance.order,
  'required': instance.required_,
  'sdk_operation_id': const UuidValueConverter().toJson(
    instance.sdkOperationId,
  ),
  'api_capability_endpoint_id': _$JsonConverterToJson<String, UuidValue>(
    instance.apiCapabilityEndpointId,
    const UuidValueConverter().toJson,
  ),
};

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);
