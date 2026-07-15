// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:aware_sdk_ontology/sdk/sdk_operation_model.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'sdk_surface_method_model.freezed.dart';
part 'sdk_surface_method_model.g.dart';

/// SDK surface method truth.
/// Surface methods are the stable SDK-facing method contract that renderers can
/// project into CLI commands, Skill targets, or other invocation affordances.
@freezed
abstract class SdkSurfaceMethod with _$SdkSurfaceMethod {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory SdkSurfaceMethod.def({
    @UuidValueConverter() required UuidValue id,
    SdkOperation? targetSdkOperation,
    required String name,
    required String operationRef,
    required String operationName,
    required String methodFamily,
    required String effect,
    required String mutationScope,
    required String confirmationPolicy,
    required String executionMode,
    required String runtimeBindingKind,
    String? description,
    @UuidValueConverter() required UuidValue sdkSurfaceId,
    @UuidValueConverter() UuidValue? targetSdkOperationId,
  }) = _SdkSurfaceMethod;

  factory SdkSurfaceMethod({
    UuidValue? id,
    SdkOperation? targetSdkOperation,
    required String name,
    required String operationRef,
    required String operationName,
    required String methodFamily,
    required String effect,
    required String mutationScope,
    required String confirmationPolicy,
    required String executionMode,
    required String runtimeBindingKind,
    String? description,
    required UuidValue sdkSurfaceId,
    UuidValue? targetSdkOperationId,
  }) {
    return _SdkSurfaceMethod(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      targetSdkOperation: targetSdkOperation,
      name: name,
      operationRef: operationRef,
      operationName: operationName,
      methodFamily: methodFamily,
      effect: effect,
      mutationScope: mutationScope,
      confirmationPolicy: confirmationPolicy,
      executionMode: executionMode,
      runtimeBindingKind: runtimeBindingKind,
      description: description,
      sdkSurfaceId: sdkSurfaceId,
      targetSdkOperationId: targetSdkOperationId,
    );
  }

  factory SdkSurfaceMethod.fromJson(Map<String, dynamic> json) =>
      _$SdkSurfaceMethodFromJson(json);
}
