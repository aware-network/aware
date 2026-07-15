// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_meta_ontology/graph/config/object_config_graph_package.dart';
import 'package:aware_meta_ontology/graph/instance/object_instance_graph_commit.dart';
import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'sdk_package_object_config_graph_package_model.freezed.dart';
part 'sdk_package_object_config_graph_package_model.g.dart';

/// SDK package to owned ObjectConfigGraphPackage bridge.
/// This records OCG/state packages declared by `aware.sdk.toml` as SDK-owned
/// package surfaces. These are not package dependencies; they are part of the
/// SDK package truth and should travel with WorkspaceRevision/Hub receipts.
@freezed
abstract class SdkPackageObjectConfigGraphPackage
    with _$SdkPackageObjectConfigGraphPackage {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory SdkPackageObjectConfigGraphPackage.def({
    @UuidValueConverter() required UuidValue id,
    ObjectConfigGraphPackage? objectConfigGraphPackage,
    ObjectInstanceGraphCommit?
    objectConfigGraphPackageObjectInstanceGraphCommit,
    required String role,
    required String manifestRelativePath,
    required String packageKind,
    String? expectedHashSha256,
    String? description,
    @UuidValueConverter() required UuidValue sdkPackageId,
    @UuidValueConverter() UuidValue? objectConfigGraphPackageId,
    @UuidValueConverter()
    UuidValue? objectConfigGraphPackageObjectInstanceGraphCommitId,
  }) = _SdkPackageObjectConfigGraphPackage;

  factory SdkPackageObjectConfigGraphPackage({
    UuidValue? id,
    ObjectConfigGraphPackage? objectConfigGraphPackage,
    ObjectInstanceGraphCommit?
    objectConfigGraphPackageObjectInstanceGraphCommit,
    required String role,
    required String manifestRelativePath,
    required String packageKind,
    String? expectedHashSha256,
    String? description,
    required UuidValue sdkPackageId,
    UuidValue? objectConfigGraphPackageId,
    UuidValue? objectConfigGraphPackageObjectInstanceGraphCommitId,
  }) {
    return _SdkPackageObjectConfigGraphPackage(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      objectConfigGraphPackage: objectConfigGraphPackage,
      objectConfigGraphPackageObjectInstanceGraphCommit:
          objectConfigGraphPackageObjectInstanceGraphCommit,
      role: role,
      manifestRelativePath: manifestRelativePath,
      packageKind: packageKind,
      expectedHashSha256: expectedHashSha256,
      description: description,
      sdkPackageId: sdkPackageId,
      objectConfigGraphPackageId: objectConfigGraphPackageId,
      objectConfigGraphPackageObjectInstanceGraphCommitId:
          objectConfigGraphPackageObjectInstanceGraphCommitId,
    );
  }

  factory SdkPackageObjectConfigGraphPackage.fromJson(
    Map<String, dynamic> json,
  ) => _$SdkPackageObjectConfigGraphPackageFromJson(json);
}
