// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'sdk_operation_dependency_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_SdkOperationDependency _$SdkOperationDependencyFromJson(
  Map<String, dynamic> json,
) => _SdkOperationDependency(
  id: const UuidValueConverter().fromJson(json['id'] as String),
  targetSdkOperation: json['target_sdk_operation'] == null
      ? null
      : SdkOperation.fromJson(
          json['target_sdk_operation'] as Map<String, dynamic>,
        ),
  targetOperationRef: json['target_operation_ref'] as String,
  targetSdkName: json['target_sdk_name'] as String,
  targetOperationName: json['target_operation_name'] as String,
  targetPackageName: json['target_package_name'] as String?,
  role: json['role'] as String,
  order: (json['order'] as num).toInt(),
  required_: json['required'] as bool,
  description: json['description'] as String?,
  sdkOperationId: const UuidValueConverter().fromJson(
    json['sdk_operation_id'] as String,
  ),
  targetSdkOperationId: _$JsonConverterFromJson<String, UuidValue>(
    json['target_sdk_operation_id'],
    const UuidValueConverter().fromJson,
  ),
);

Map<String, dynamic> _$SdkOperationDependencyToJson(
  _SdkOperationDependency instance,
) => <String, dynamic>{
  'id': const UuidValueConverter().toJson(instance.id),
  'target_sdk_operation': instance.targetSdkOperation?.toJson(),
  'target_operation_ref': instance.targetOperationRef,
  'target_sdk_name': instance.targetSdkName,
  'target_operation_name': instance.targetOperationName,
  'target_package_name': instance.targetPackageName,
  'role': instance.role,
  'order': instance.order,
  'required': instance.required_,
  'description': instance.description,
  'sdk_operation_id': const UuidValueConverter().toJson(
    instance.sdkOperationId,
  ),
  'target_sdk_operation_id': _$JsonConverterToJson<String, UuidValue>(
    instance.targetSdkOperationId,
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
