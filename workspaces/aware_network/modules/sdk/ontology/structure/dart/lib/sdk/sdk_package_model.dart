// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_code_ontology/package/code_package.dart';
import 'package:aware_meta_ontology/graph/instance/object_instance_graph_commit.dart';
import 'package:aware_model_helpers/converters.dart';
import 'package:aware_sdk_ontology/sdk/sdk_config_model.dart';
import 'package:aware_sdk_ontology/sdk/sdk_package_api_package_model.dart';
import 'package:aware_sdk_ontology/sdk/sdk_package_dependency_model.dart';
import 'package:aware_sdk_ontology/sdk/sdk_package_implementation_package_model.dart';
import 'package:aware_sdk_ontology/sdk/sdk_package_object_config_graph_package_model.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'sdk_package_model.freezed.dart';
part 'sdk_package_model.g.dart';

@freezed
abstract class SdkPackage with _$SdkPackage {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory SdkPackage.def({
    @UuidValueConverter() required UuidValue id,
    CodePackage? sourceCodePackage,
    @Default(const []) List<SdkPackageApiPackage> apiPackages,
    @Default(const [])
    List<SdkPackageImplementationPackage> implementationPackages,
    @Default(const [])
    List<SdkPackageObjectConfigGraphPackage> objectConfigGraphPackages,
    @Default(const []) List<SdkPackageDependency> sdkPackageDependencies,
    SdkConfig? sdkConfig,
    ObjectInstanceGraphCommit? sdkConfigObjectInstanceGraphCommit,
    required int awareSdkVersion,
    required String compilationMode,
    required List<dynamic> dependencies,
    String? description,
    required List<dynamic> excludePaths,
    required bool forceFreshScan,
    String? fqnPrefix,
    required List<dynamic> includePaths,
    String? manifestRelativePath,
    required String name,
    required String packageRoot,
    required String sourcesRoot,
    required Map<String, dynamic> targets,
    String? title,
    required int versionNumber,
    @UuidValueConverter() UuidValue? sourceCodePackageId,
    @UuidValueConverter() UuidValue? sdkConfigId,
    @UuidValueConverter() UuidValue? sdkConfigObjectInstanceGraphCommitId,
  }) = _SdkPackage;

  factory SdkPackage({
    UuidValue? id,
    CodePackage? sourceCodePackage,
    List<SdkPackageApiPackage> apiPackages = const [],
    List<SdkPackageImplementationPackage> implementationPackages = const [],
    List<SdkPackageObjectConfigGraphPackage> objectConfigGraphPackages =
        const [],
    List<SdkPackageDependency> sdkPackageDependencies = const [],
    SdkConfig? sdkConfig,
    ObjectInstanceGraphCommit? sdkConfigObjectInstanceGraphCommit,
    required int awareSdkVersion,
    required String compilationMode,
    required List<dynamic> dependencies,
    String? description,
    required List<dynamic> excludePaths,
    required bool forceFreshScan,
    String? fqnPrefix,
    required List<dynamic> includePaths,
    String? manifestRelativePath,
    required String name,
    required String packageRoot,
    required String sourcesRoot,
    required Map<String, dynamic> targets,
    String? title,
    required int versionNumber,
    UuidValue? sourceCodePackageId,
    UuidValue? sdkConfigId,
    UuidValue? sdkConfigObjectInstanceGraphCommitId,
  }) {
    return _SdkPackage(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      sourceCodePackage: sourceCodePackage,
      apiPackages: apiPackages,
      implementationPackages: implementationPackages,
      objectConfigGraphPackages: objectConfigGraphPackages,
      sdkPackageDependencies: sdkPackageDependencies,
      sdkConfig: sdkConfig,
      sdkConfigObjectInstanceGraphCommit: sdkConfigObjectInstanceGraphCommit,
      awareSdkVersion: awareSdkVersion,
      compilationMode: compilationMode,
      dependencies: dependencies,
      description: description,
      excludePaths: excludePaths,
      forceFreshScan: forceFreshScan,
      fqnPrefix: fqnPrefix,
      includePaths: includePaths,
      manifestRelativePath: manifestRelativePath,
      name: name,
      packageRoot: packageRoot,
      sourcesRoot: sourcesRoot,
      targets: targets,
      title: title,
      versionNumber: versionNumber,
      sourceCodePackageId: sourceCodePackageId,
      sdkConfigId: sdkConfigId,
      sdkConfigObjectInstanceGraphCommitId:
          sdkConfigObjectInstanceGraphCommitId,
    );
  }

  factory SdkPackage.fromJson(Map<String, dynamic> json) =>
      _$SdkPackageFromJson(json);
}
