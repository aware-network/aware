// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_api_ontology/api/api_capability_endpoint.dart';
import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'sdk_operation_api_capability_endpoint_model.freezed.dart';
part 'sdk_operation_api_capability_endpoint_model.g.dart';

/// SDK operation to API endpoint bridge.
@freezed
abstract class SdkOperationApiCapabilityEndpoint
    with _$SdkOperationApiCapabilityEndpoint {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory SdkOperationApiCapabilityEndpoint.def({
    @UuidValueConverter() required UuidValue id,
    ApiCapabilityEndpoint? apiCapabilityEndpoint,
    required String name,
    String? endpointRef,
    String? discriminant,
    required String role,
    required int order,
    @JsonKey(name: 'required') required bool required_,
    @UuidValueConverter() required UuidValue sdkOperationId,
    @UuidValueConverter() UuidValue? apiCapabilityEndpointId,
  }) = _SdkOperationApiCapabilityEndpoint;

  factory SdkOperationApiCapabilityEndpoint({
    UuidValue? id,
    ApiCapabilityEndpoint? apiCapabilityEndpoint,
    required String name,
    String? endpointRef,
    String? discriminant,
    required String role,
    required int order,
    required bool required_,
    required UuidValue sdkOperationId,
    UuidValue? apiCapabilityEndpointId,
  }) {
    return _SdkOperationApiCapabilityEndpoint(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      apiCapabilityEndpoint: apiCapabilityEndpoint,
      name: name,
      endpointRef: endpointRef,
      discriminant: discriminant,
      role: role,
      order: order,
      required_: required_,
      sdkOperationId: sdkOperationId,
      apiCapabilityEndpointId: apiCapabilityEndpointId,
    );
  }

  factory SdkOperationApiCapabilityEndpoint.fromJson(
    Map<String, dynamic> json,
  ) => _$SdkOperationApiCapabilityEndpointFromJson(json);
}
