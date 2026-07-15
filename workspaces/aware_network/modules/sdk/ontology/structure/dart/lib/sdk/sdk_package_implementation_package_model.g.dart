// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'sdk_package_implementation_package_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_SdkPackageImplementationPackage _$SdkPackageImplementationPackageFromJson(
  Map<String, dynamic> json,
) => _SdkPackageImplementationPackage(
  id: const UuidValueConverter().fromJson(json['id'] as String),
  codePackage: json['code_package'] == null
      ? null
      : CodePackage.fromJson(json['code_package'] as Map<String, dynamic>),
  entrypoint: json['entrypoint'] as String?,
  excludePaths: json['exclude_paths'] as List<dynamic>,
  importRoot: json['import_root'] as String,
  includePaths: json['include_paths'] as List<dynamic>,
  language: CodeLanguageExtension.fromJson(json['language'] as String),
  manifestRelativePath: json['manifest_relative_path'] as String,
  packageName: json['package_name'] as String,
  packageRoot: json['package_root'] as String,
  role: json['role'] as String,
  sdkPackageId: const UuidValueConverter().fromJson(
    json['sdk_package_id'] as String,
  ),
  codePackageId: _$JsonConverterFromJson<String, UuidValue>(
    json['code_package_id'],
    const UuidValueConverter().fromJson,
  ),
);

Map<String, dynamic> _$SdkPackageImplementationPackageToJson(
  _SdkPackageImplementationPackage instance,
) => <String, dynamic>{
  'id': const UuidValueConverter().toJson(instance.id),
  'code_package': instance.codePackage?.toJson(),
  'entrypoint': instance.entrypoint,
  'exclude_paths': instance.excludePaths,
  'import_root': instance.importRoot,
  'include_paths': instance.includePaths,
  'language': CodeLanguageExtension.toJson(instance.language),
  'manifest_relative_path': instance.manifestRelativePath,
  'package_name': instance.packageName,
  'package_root': instance.packageRoot,
  'role': instance.role,
  'sdk_package_id': const UuidValueConverter().toJson(instance.sdkPackageId),
  'code_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.codePackageId,
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
