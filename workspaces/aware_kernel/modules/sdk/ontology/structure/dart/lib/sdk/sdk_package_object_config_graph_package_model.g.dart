// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'sdk_package_object_config_graph_package_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_SdkPackageObjectConfigGraphPackage
_$SdkPackageObjectConfigGraphPackageFromJson(Map<String, dynamic> json) =>
    _SdkPackageObjectConfigGraphPackage(
      id: const UuidValueConverter().fromJson(json['id'] as String),
      objectConfigGraphPackage: json['object_config_graph_package'] == null
          ? null
          : ObjectConfigGraphPackage.fromJson(
              json['object_config_graph_package'] as Map<String, dynamic>,
            ),
      objectConfigGraphPackageObjectInstanceGraphCommit:
          json['object_config_graph_package_object_instance_graph_commit'] ==
              null
          ? null
          : ObjectInstanceGraphCommit.fromJson(
              json['object_config_graph_package_object_instance_graph_commit']
                  as Map<String, dynamic>,
            ),
      role: json['role'] as String,
      manifestRelativePath: json['manifest_relative_path'] as String,
      packageKind: json['package_kind'] as String,
      expectedHashSha256: json['expected_hash_sha256'] as String?,
      description: json['description'] as String?,
      sdkPackageId: const UuidValueConverter().fromJson(
        json['sdk_package_id'] as String,
      ),
      objectConfigGraphPackageId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_config_graph_package_id'],
        const UuidValueConverter().fromJson,
      ),
      objectConfigGraphPackageObjectInstanceGraphCommitId:
          _$JsonConverterFromJson<String, UuidValue>(
            json['object_config_graph_package_object_instance_graph_commit_id'],
            const UuidValueConverter().fromJson,
          ),
    );

Map<String, dynamic> _$SdkPackageObjectConfigGraphPackageToJson(
  _SdkPackageObjectConfigGraphPackage instance,
) => <String, dynamic>{
  'id': const UuidValueConverter().toJson(instance.id),
  'object_config_graph_package': instance.objectConfigGraphPackage?.toJson(),
  'object_config_graph_package_object_instance_graph_commit': instance
      .objectConfigGraphPackageObjectInstanceGraphCommit
      ?.toJson(),
  'role': instance.role,
  'manifest_relative_path': instance.manifestRelativePath,
  'package_kind': instance.packageKind,
  'expected_hash_sha256': instance.expectedHashSha256,
  'description': instance.description,
  'sdk_package_id': const UuidValueConverter().toJson(instance.sdkPackageId),
  'object_config_graph_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectConfigGraphPackageId,
    const UuidValueConverter().toJson,
  ),
  'object_config_graph_package_object_instance_graph_commit_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.objectConfigGraphPackageObjectInstanceGraphCommitId,
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
