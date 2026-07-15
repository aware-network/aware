// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'api_model.freezed.dart';
part 'api_model.g.dart';

@freezed
abstract class ApiOperationContext with _$ApiOperationContext {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ApiOperationContext.def({@UuidValueConverter() UuidValue? actorId}) =
      _ApiOperationContext;

  factory ApiOperationContext({UuidValue? actorId}) {
    return _ApiOperationContext(actorId: actorId);
  }

  factory ApiOperationContext.fromJson(Map<String, dynamic> json) =>
      _$ApiOperationContextFromJson(json);
}

@freezed
abstract class ApiOperation with _$ApiOperation {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ApiOperation.def({
    ApiOperationRequest? request,
    ApiOperationResponse? response,
  }) = _ApiOperation;

  factory ApiOperation({
    ApiOperationRequest? request,
    ApiOperationResponse? response,
  }) {
    return _ApiOperation(request: request, response: response);
  }

  factory ApiOperation.fromJson(Map<String, dynamic> json) =>
      _$ApiOperationFromJson(json);
}

@freezed
abstract class ApiOperationRequest with _$ApiOperationRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ApiOperationRequest.def({
    @UuidValueConverter() UuidValue? actorId,
    required String operation,
  }) = _ApiOperationRequest;

  factory ApiOperationRequest({UuidValue? actorId, required String operation}) {
    return _ApiOperationRequest(actorId: actorId, operation: operation);
  }

  factory ApiOperationRequest.fromJson(Map<String, dynamic> json) =>
      _$ApiOperationRequestFromJson(json);
}

@freezed
abstract class ApiOperationResponse with _$ApiOperationResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ApiOperationResponse.def({
    @UuidValueConverter() UuidValue? actorId,
    required String operation,
  }) = _ApiOperationResponse;

  factory ApiOperationResponse({
    UuidValue? actorId,
    required String operation,
  }) {
    return _ApiOperationResponse(actorId: actorId, operation: operation);
  }

  factory ApiOperationResponse.fromJson(Map<String, dynamic> json) =>
      _$ApiOperationResponseFromJson(json);
}
