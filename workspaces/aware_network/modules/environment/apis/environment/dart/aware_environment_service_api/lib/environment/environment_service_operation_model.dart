// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:freezed_annotation/freezed_annotation.dart';

part 'environment_service_operation_model.freezed.dart';
part 'environment_service_operation_model.g.dart';

/// Environment service operation base (DTO-only).
/// SSOT: `environment-service-dto` generated from `apis/environment/dto`.
/// This is the Environment plugin rail payload root. Service-specific variants
/// (Inference now; LSP/Terminal later) should `augment` this type.
/// NOTE:
/// This is defined in its own module to avoid import cycles between the
/// environment DTO module and service-specific DTO modules.
@freezed
abstract class EnvironmentServiceOperation with _$EnvironmentServiceOperation {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentServiceOperation.def({
    required String service,
    String? operation,
  }) = _EnvironmentServiceOperation;

  factory EnvironmentServiceOperation({
    required String service,
    String? operation,
  }) {
    return _EnvironmentServiceOperation(service: service, operation: operation);
  }

  factory EnvironmentServiceOperation.fromJson(Map<String, dynamic> json) =>
      _$EnvironmentServiceOperationFromJson(json);
}
