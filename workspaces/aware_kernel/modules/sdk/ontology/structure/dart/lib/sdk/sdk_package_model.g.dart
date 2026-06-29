// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'sdk_package_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_SdkPackage _$SdkPackageFromJson(Map<String, dynamic> json) => _SdkPackage(
  id: const UuidValueConverter().fromJson(json['id'] as String),
  sourceCodePackage: json['source_code_package'] == null
      ? null
      : CodePackage.fromJson(
          json['source_code_package'] as Map<String, dynamic>,
        ),
  apiPackages:
      (json['api_packages'] as List<dynamic>?)
          ?.map((e) => SdkPackageApiPackage.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  implementationPackages:
      (json['implementation_packages'] as List<dynamic>?)
          ?.map(
            (e) => SdkPackageImplementationPackage.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  objectConfigGraphPackages:
      (json['object_config_graph_packages'] as List<dynamic>?)
          ?.map(
            (e) => SdkPackageObjectConfigGraphPackage.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  sdkPackageDependencies:
      (json['sdk_package_dependencies'] as List<dynamic>?)
          ?.map((e) => SdkPackageDependency.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  sdkConfig: json['sdk_config'] == null
      ? null
      : SdkConfig.fromJson(json['sdk_config'] as Map<String, dynamic>),
  sdkConfigObjectInstanceGraphCommit:
      json['sdk_config_object_instance_graph_commit'] == null
      ? null
      : ObjectInstanceGraphCommit.fromJson(
          json['sdk_config_object_instance_graph_commit']
              as Map<String, dynamic>,
        ),
  awareSdkVersion: (json['aware_sdk_version'] as num).toInt(),
  compilationMode: json['compilation_mode'] as String,
  dependencies: json['dependencies'] as List<dynamic>,
  description: json['description'] as String?,
  excludePaths: json['exclude_paths'] as List<dynamic>,
  forceFreshScan: json['force_fresh_scan'] as bool,
  fqnPrefix: json['fqn_prefix'] as String?,
  includePaths: json['include_paths'] as List<dynamic>,
  manifestRelativePath: json['manifest_relative_path'] as String?,
  name: json['name'] as String,
  packageRoot: json['package_root'] as String,
  sourcesRoot: json['sources_root'] as String,
  targets: json['targets'] as Map<String, dynamic>,
  title: json['title'] as String?,
  versionNumber: (json['version_number'] as num).toInt(),
  sourceCodePackageId: _$JsonConverterFromJson<String, UuidValue>(
    json['source_code_package_id'],
    const UuidValueConverter().fromJson,
  ),
  sdkConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['sdk_config_id'],
    const UuidValueConverter().fromJson,
  ),
  sdkConfigObjectInstanceGraphCommitId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['sdk_config_object_instance_graph_commit_id'],
        const UuidValueConverter().fromJson,
      ),
);

Map<String, dynamic> _$SdkPackageToJson(_SdkPackage instance) =>
    <String, dynamic>{
      'id': const UuidValueConverter().toJson(instance.id),
      'source_code_package': instance.sourceCodePackage?.toJson(),
      'api_packages': instance.apiPackages.map((e) => e.toJson()).toList(),
      'implementation_packages': instance.implementationPackages
          .map((e) => e.toJson())
          .toList(),
      'object_config_graph_packages': instance.objectConfigGraphPackages
          .map((e) => e.toJson())
          .toList(),
      'sdk_package_dependencies': instance.sdkPackageDependencies
          .map((e) => e.toJson())
          .toList(),
      'sdk_config': instance.sdkConfig?.toJson(),
      'sdk_config_object_instance_graph_commit': instance
          .sdkConfigObjectInstanceGraphCommit
          ?.toJson(),
      'aware_sdk_version': instance.awareSdkVersion,
      'compilation_mode': instance.compilationMode,
      'dependencies': instance.dependencies,
      'description': instance.description,
      'exclude_paths': instance.excludePaths,
      'force_fresh_scan': instance.forceFreshScan,
      'fqn_prefix': instance.fqnPrefix,
      'include_paths': instance.includePaths,
      'manifest_relative_path': instance.manifestRelativePath,
      'name': instance.name,
      'package_root': instance.packageRoot,
      'sources_root': instance.sourcesRoot,
      'targets': instance.targets,
      'title': instance.title,
      'version_number': instance.versionNumber,
      'source_code_package_id': _$JsonConverterToJson<String, UuidValue>(
        instance.sourceCodePackageId,
        const UuidValueConverter().toJson,
      ),
      'sdk_config_id': _$JsonConverterToJson<String, UuidValue>(
        instance.sdkConfigId,
        const UuidValueConverter().toJson,
      ),
      'sdk_config_object_instance_graph_commit_id':
          _$JsonConverterToJson<String, UuidValue>(
            instance.sdkConfigObjectInstanceGraphCommitId,
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
