// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_meta_ontology/graph/instance/object_instance_graph_commit.dart';
import 'package:aware_model_helpers/converters.dart';
import 'package:aware_sdk_ontology/sdk/sdk_package_model.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'sdk_package_dependency_model.freezed.dart';
part 'sdk_package_dependency_model.g.dart';

/// SDK package to SDK package dependency bridge.
/// The authored `aware.sdk.toml` dependency row is selector truth. The resolved
/// OIG commit pin, when present, is exact reproducibility authority for Hub and
/// WorkspaceRevision consumers.
@freezed
abstract class SdkPackageDependency with _$SdkPackageDependency {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory SdkPackageDependency.def({
    @UuidValueConverter() required UuidValue id,
    SdkPackage? targetSdkPackage,
    ObjectInstanceGraphCommit? targetSdkPackageObjectInstanceGraphCommit,
    required String targetPackageName,
    int? targetVersionNumber,
    String? expectedHashSha256,
    String? description,
    @UuidValueConverter() required UuidValue sdkPackageId,
    @UuidValueConverter() UuidValue? targetSdkPackageId,
    @UuidValueConverter()
    UuidValue? targetSdkPackageObjectInstanceGraphCommitId,
  }) = _SdkPackageDependency;

  factory SdkPackageDependency({
    UuidValue? id,
    SdkPackage? targetSdkPackage,
    ObjectInstanceGraphCommit? targetSdkPackageObjectInstanceGraphCommit,
    required String targetPackageName,
    int? targetVersionNumber,
    String? expectedHashSha256,
    String? description,
    required UuidValue sdkPackageId,
    UuidValue? targetSdkPackageId,
    UuidValue? targetSdkPackageObjectInstanceGraphCommitId,
  }) {
    return _SdkPackageDependency(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      targetSdkPackage: targetSdkPackage,
      targetSdkPackageObjectInstanceGraphCommit:
          targetSdkPackageObjectInstanceGraphCommit,
      targetPackageName: targetPackageName,
      targetVersionNumber: targetVersionNumber,
      expectedHashSha256: expectedHashSha256,
      description: description,
      sdkPackageId: sdkPackageId,
      targetSdkPackageId: targetSdkPackageId,
      targetSdkPackageObjectInstanceGraphCommitId:
          targetSdkPackageObjectInstanceGraphCommitId,
    );
  }

  factory SdkPackageDependency.fromJson(Map<String, dynamic> json) =>
      _$SdkPackageDependencyFromJson(json);
}
