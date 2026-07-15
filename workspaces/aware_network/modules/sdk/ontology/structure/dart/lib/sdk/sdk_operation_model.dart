// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:aware_sdk_ontology/sdk/sdk_operation_api_capability_endpoint_model.dart';
import 'package:aware_sdk_ontology/sdk/sdk_operation_dependency_model.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'sdk_operation_model.freezed.dart';
part 'sdk_operation_model.g.dart';

/// SDK-local operation truth.
/// One operation may coordinate one or more API capability endpoints. The API
/// endpoint remains the canonical ingress contract for request/response/stream
/// payloads.
@freezed
abstract class SdkOperation with _$SdkOperation {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory SdkOperation.def({
    @UuidValueConverter() required UuidValue id,
    @Default(const [])
    List<SdkOperationApiCapabilityEndpoint> apiCapabilityEndpoints,
    @Default(const []) List<SdkOperationDependency> sdkOperationDependencies,
    required String name,
    String? title,
    String? description,
    String? implementationRef,
    @UuidValueConverter() required UuidValue sdkConfigId,
  }) = _SdkOperation;

  factory SdkOperation({
    UuidValue? id,
    List<SdkOperationApiCapabilityEndpoint> apiCapabilityEndpoints = const [],
    List<SdkOperationDependency> sdkOperationDependencies = const [],
    required String name,
    String? title,
    String? description,
    String? implementationRef,
    required UuidValue sdkConfigId,
  }) {
    return _SdkOperation(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      apiCapabilityEndpoints: apiCapabilityEndpoints,
      sdkOperationDependencies: sdkOperationDependencies,
      name: name,
      title: title,
      description: description,
      implementationRef: implementationRef,
      sdkConfigId: sdkConfigId,
    );
  }

  factory SdkOperation.fromJson(Map<String, dynamic> json) =>
      _$SdkOperationFromJson(json);
}
