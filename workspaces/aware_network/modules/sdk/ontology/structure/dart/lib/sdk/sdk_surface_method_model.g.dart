// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'sdk_surface_method_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_SdkSurfaceMethod _$SdkSurfaceMethodFromJson(Map<String, dynamic> json) =>
    _SdkSurfaceMethod(
      id: const UuidValueConverter().fromJson(json['id'] as String),
      targetSdkOperation: json['target_sdk_operation'] == null
          ? null
          : SdkOperation.fromJson(
              json['target_sdk_operation'] as Map<String, dynamic>,
            ),
      name: json['name'] as String,
      operationRef: json['operation_ref'] as String,
      operationName: json['operation_name'] as String,
      methodFamily: json['method_family'] as String,
      effect: json['effect'] as String,
      mutationScope: json['mutation_scope'] as String,
      confirmationPolicy: json['confirmation_policy'] as String,
      executionMode: json['execution_mode'] as String,
      runtimeBindingKind: json['runtime_binding_kind'] as String,
      description: json['description'] as String?,
      sdkSurfaceId: const UuidValueConverter().fromJson(
        json['sdk_surface_id'] as String,
      ),
      targetSdkOperationId: _$JsonConverterFromJson<String, UuidValue>(
        json['target_sdk_operation_id'],
        const UuidValueConverter().fromJson,
      ),
    );

Map<String, dynamic> _$SdkSurfaceMethodToJson(
  _SdkSurfaceMethod instance,
) => <String, dynamic>{
  'id': const UuidValueConverter().toJson(instance.id),
  'target_sdk_operation': instance.targetSdkOperation?.toJson(),
  'name': instance.name,
  'operation_ref': instance.operationRef,
  'operation_name': instance.operationName,
  'method_family': instance.methodFamily,
  'effect': instance.effect,
  'mutation_scope': instance.mutationScope,
  'confirmation_policy': instance.confirmationPolicy,
  'execution_mode': instance.executionMode,
  'runtime_binding_kind': instance.runtimeBindingKind,
  'description': instance.description,
  'sdk_surface_id': const UuidValueConverter().toJson(instance.sdkSurfaceId),
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
