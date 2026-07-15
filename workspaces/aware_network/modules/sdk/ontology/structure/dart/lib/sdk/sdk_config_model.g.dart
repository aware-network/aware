// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'sdk_config_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_SdkConfig _$SdkConfigFromJson(Map<String, dynamic> json) => _SdkConfig(
  id: const UuidValueConverter().fromJson(json['id'] as String),
  operations:
      (json['operations'] as List<dynamic>?)
          ?.map((e) => SdkOperation.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  surfaces:
      (json['surfaces'] as List<dynamic>?)
          ?.map((e) => SdkSurface.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  name: json['name'] as String,
  title: json['title'] as String?,
  description: json['description'] as String?,
);

Map<String, dynamic> _$SdkConfigToJson(_SdkConfig instance) =>
    <String, dynamic>{
      'id': const UuidValueConverter().toJson(instance.id),
      'operations': instance.operations.map((e) => e.toJson()).toList(),
      'surfaces': instance.surfaces.map((e) => e.toJson()).toList(),
      'name': instance.name,
      'title': instance.title,
      'description': instance.description,
    };
