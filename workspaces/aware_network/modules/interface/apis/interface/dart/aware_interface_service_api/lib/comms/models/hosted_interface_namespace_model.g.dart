// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'hosted_interface_namespace_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_HostedInterfaceNamespace _$HostedInterfaceNamespaceFromJson(
  Map<String, dynamic> json,
) => _HostedInterfaceNamespace(
  namespace: json['namespace'] as String,
  hostLabel: json['host_label'] as String,
  started: json['started'] as bool,
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  interfaceId: _$JsonConverterFromJson<String, UuidValue>(
    json['interface_id'],
    const UuidValueConverter().fromJson,
  ),
  interfaceSessionId: _$JsonConverterFromJson<String, UuidValue>(
    json['interface_session_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_config_id'],
    const UuidValueConverter().fromJson,
  ),
  warnings:
      (json['warnings'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
);

Map<String, dynamic> _$HostedInterfaceNamespaceToJson(
  _HostedInterfaceNamespace instance,
) => <String, dynamic>{
  'namespace': instance.namespace,
  'host_label': instance.hostLabel,
  'started': instance.started,
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'interface_id': _$JsonConverterToJson<String, UuidValue>(
    instance.interfaceId,
    const UuidValueConverter().toJson,
  ),
  'interface_session_id': _$JsonConverterToJson<String, UuidValue>(
    instance.interfaceSessionId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentId,
    const UuidValueConverter().toJson,
  ),
  'environment_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentConfigId,
    const UuidValueConverter().toJson,
  ),
  'warnings': instance.warnings,
};

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);
