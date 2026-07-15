// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'sdk_package_api_package_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_SdkPackageApiPackage _$SdkPackageApiPackageFromJson(
  Map<String, dynamic> json,
) => _SdkPackageApiPackage(
  id: const UuidValueConverter().fromJson(json['id'] as String),
  apiPackage: json['api_package'] == null
      ? null
      : ApiPackage.fromJson(json['api_package'] as Map<String, dynamic>),
  description: json['description'] as String?,
  sdkPackageId: const UuidValueConverter().fromJson(
    json['sdk_package_id'] as String,
  ),
  apiPackageId: _$JsonConverterFromJson<String, UuidValue>(
    json['api_package_id'],
    const UuidValueConverter().fromJson,
  ),
);

Map<String, dynamic> _$SdkPackageApiPackageToJson(
  _SdkPackageApiPackage instance,
) => <String, dynamic>{
  'id': const UuidValueConverter().toJson(instance.id),
  'api_package': instance.apiPackage?.toJson(),
  'description': instance.description,
  'sdk_package_id': const UuidValueConverter().toJson(instance.sdkPackageId),
  'api_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.apiPackageId,
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
