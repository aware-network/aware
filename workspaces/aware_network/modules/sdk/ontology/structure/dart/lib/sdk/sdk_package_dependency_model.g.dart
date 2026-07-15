// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'sdk_package_dependency_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_SdkPackageDependency _$SdkPackageDependencyFromJson(
  Map<String, dynamic> json,
) => _SdkPackageDependency(
  id: const UuidValueConverter().fromJson(json['id'] as String),
  targetSdkPackage: json['target_sdk_package'] == null
      ? null
      : SdkPackage.fromJson(json['target_sdk_package'] as Map<String, dynamic>),
  targetSdkPackageObjectInstanceGraphCommit:
      json['target_sdk_package_object_instance_graph_commit'] == null
      ? null
      : ObjectInstanceGraphCommit.fromJson(
          json['target_sdk_package_object_instance_graph_commit']
              as Map<String, dynamic>,
        ),
  targetPackageName: json['target_package_name'] as String,
  targetVersionNumber: (json['target_version_number'] as num?)?.toInt(),
  expectedHashSha256: json['expected_hash_sha256'] as String?,
  description: json['description'] as String?,
  sdkPackageId: const UuidValueConverter().fromJson(
    json['sdk_package_id'] as String,
  ),
  targetSdkPackageId: _$JsonConverterFromJson<String, UuidValue>(
    json['target_sdk_package_id'],
    const UuidValueConverter().fromJson,
  ),
  targetSdkPackageObjectInstanceGraphCommitId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['target_sdk_package_object_instance_graph_commit_id'],
        const UuidValueConverter().fromJson,
      ),
);

Map<String, dynamic> _$SdkPackageDependencyToJson(
  _SdkPackageDependency instance,
) => <String, dynamic>{
  'id': const UuidValueConverter().toJson(instance.id),
  'target_sdk_package': instance.targetSdkPackage?.toJson(),
  'target_sdk_package_object_instance_graph_commit': instance
      .targetSdkPackageObjectInstanceGraphCommit
      ?.toJson(),
  'target_package_name': instance.targetPackageName,
  'target_version_number': instance.targetVersionNumber,
  'expected_hash_sha256': instance.expectedHashSha256,
  'description': instance.description,
  'sdk_package_id': const UuidValueConverter().toJson(instance.sdkPackageId),
  'target_sdk_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.targetSdkPackageId,
    const UuidValueConverter().toJson,
  ),
  'target_sdk_package_object_instance_graph_commit_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.targetSdkPackageObjectInstanceGraphCommitId,
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
