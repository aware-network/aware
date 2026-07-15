// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:aware_sdk_ontology/sdk/sdk_operation_model.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'sdk_operation_dependency_model.freezed.dart';
part 'sdk_operation_dependency_model.g.dart';

/// SDK operation-to-operation dependency edge.
/// This is SDK composition truth. It does not replace API endpoint bindings;
/// it records that one SDK operation is allowed to orchestrate another SDK
/// operation from the same SDK config or from a declared SDK package
/// dependency closure.
@freezed
abstract class SdkOperationDependency with _$SdkOperationDependency {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory SdkOperationDependency.def({
    @UuidValueConverter() required UuidValue id,
    SdkOperation? targetSdkOperation,
    required String targetOperationRef,
    required String targetSdkName,
    required String targetOperationName,
    String? targetPackageName,
    required String role,
    required int order,
    @JsonKey(name: 'required') required bool required_,
    String? description,
    @UuidValueConverter() required UuidValue sdkOperationId,
    @UuidValueConverter() UuidValue? targetSdkOperationId,
  }) = _SdkOperationDependency;

  factory SdkOperationDependency({
    UuidValue? id,
    SdkOperation? targetSdkOperation,
    required String targetOperationRef,
    required String targetSdkName,
    required String targetOperationName,
    String? targetPackageName,
    required String role,
    required int order,
    required bool required_,
    String? description,
    required UuidValue sdkOperationId,
    UuidValue? targetSdkOperationId,
  }) {
    return _SdkOperationDependency(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      targetSdkOperation: targetSdkOperation,
      targetOperationRef: targetOperationRef,
      targetSdkName: targetSdkName,
      targetOperationName: targetOperationName,
      targetPackageName: targetPackageName,
      role: role,
      order: order,
      required_: required_,
      description: description,
      sdkOperationId: sdkOperationId,
      targetSdkOperationId: targetSdkOperationId,
    );
  }

  factory SdkOperationDependency.fromJson(Map<String, dynamic> json) =>
      _$SdkOperationDependencyFromJson(json);
}
