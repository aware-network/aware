// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'sdk_surface_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_SdkSurface _$SdkSurfaceFromJson(Map<String, dynamic> json) => _SdkSurface(
  id: const UuidValueConverter().fromJson(json['id'] as String),
  methods:
      (json['methods'] as List<dynamic>?)
          ?.map((e) => SdkSurfaceMethod.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  name: json['name'] as String,
  title: json['title'] as String?,
  description: json['description'] as String?,
  sdkConfigId: const UuidValueConverter().fromJson(
    json['sdk_config_id'] as String,
  ),
);

Map<String, dynamic> _$SdkSurfaceToJson(_SdkSurface instance) =>
    <String, dynamic>{
      'id': const UuidValueConverter().toJson(instance.id),
      'methods': instance.methods.map((e) => e.toJson()).toList(),
      'name': instance.name,
      'title': instance.title,
      'description': instance.description,
      'sdk_config_id': const UuidValueConverter().toJson(instance.sdkConfigId),
    };
