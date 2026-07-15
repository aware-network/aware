// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'environment_service_operation_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_EnvironmentServiceOperation _$EnvironmentServiceOperationFromJson(
  Map<String, dynamic> json,
) => _EnvironmentServiceOperation(
  service: json['service'] as String,
  operation: json['operation'] as String?,
);

Map<String, dynamic> _$EnvironmentServiceOperationToJson(
  _EnvironmentServiceOperation instance,
) => <String, dynamic>{
  'service': instance.service,
  'operation': instance.operation,
};
