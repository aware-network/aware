// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import '../../network/network_enums.dart';
import 'api_model.dart';
import 'network_node_model.dart';
import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';
import 'service_model.dart';

part 'network_model.freezed.dart';
part 'network_model.g.dart';

/// Wire DTOs for NetworkOperation envelopes (graph/ORM agnostic).
@freezed
abstract class NetworkRequest with _$NetworkRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkRequest.def({
    @UuidValueConverter() UuidValue? id,
    @JsonKey(
      fromJson: NetworkRequestStatusExtension.fromJson,
      toJson: NetworkRequestStatusExtension.toJson,
    )
    required NetworkRequestStatus status,
    @UuidValueConverter() UuidValue? requesterId,
    Map<String, dynamic>? requester,
  }) = _NetworkRequest;

  factory NetworkRequest({
    UuidValue? id,
    NetworkRequestStatus? status,
    UuidValue? requesterId,
    Map<String, dynamic>? requester,
  }) {
    return _NetworkRequest(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      status: status ?? NetworkRequestStatus.pending,
      requesterId: requesterId,
      requester: requester,
    );
  }

  factory NetworkRequest.fromJson(Map<String, dynamic> json) =>
      _$NetworkRequestFromJson({
        ...json,
        if (!json.containsKey('status')) 'status': 'pending',
      });
}

@freezed
abstract class NetworkResponse with _$NetworkResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkResponse.def({
    @UuidValueConverter() UuidValue? id,
    @JsonKey(
      fromJson: NetworkRequestStatusExtension.fromJson,
      toJson: NetworkRequestStatusExtension.toJson,
    )
    required NetworkRequestStatus status,
    String? error,
    @UuidValueConverter() UuidValue? networkRequestId,
  }) = _NetworkResponse;

  factory NetworkResponse({
    UuidValue? id,
    NetworkRequestStatus? status,
    String? error,
    UuidValue? networkRequestId,
  }) {
    return _NetworkResponse(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      status: status ?? NetworkRequestStatus.pending,
      error: error,
      networkRequestId: networkRequestId,
    );
  }

  factory NetworkResponse.fromJson(Map<String, dynamic> json) =>
      _$NetworkResponseFromJson({
        ...json,
        if (!json.containsKey('status')) 'status': 'pending',
      });
}

@freezed
abstract class NetworkOperationHop with _$NetworkOperationHop {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkOperationHop.def({
    @JsonKey(
      fromJson: NetworkAppTypeExtension.fromJson,
      toJson: NetworkAppTypeExtension.toJson,
    )
    required NetworkAppType sourceAppType,
    @JsonKey(
      fromJson: NetworkAppTypeExtension.fromJson,
      toJson: NetworkAppTypeExtension.toJson,
    )
    required NetworkAppType targetAppType,
    @UuidValueConverter() UuidValue? sourceNodeId,
    @UuidValueConverter() UuidValue? sourceInterfaceId,
    @UuidValueConverter() UuidValue? sourceEnvironmentId,
    @UuidValueConverter() UuidValue? targetNodeId,
    @UuidValueConverter() UuidValue? targetInterfaceId,
    @UuidValueConverter() UuidValue? targetEnvironmentId,
  }) = _NetworkOperationHop;

  factory NetworkOperationHop({
    required NetworkAppType sourceAppType,
    required NetworkAppType targetAppType,
    UuidValue? sourceNodeId,
    UuidValue? sourceInterfaceId,
    UuidValue? sourceEnvironmentId,
    UuidValue? targetNodeId,
    UuidValue? targetInterfaceId,
    UuidValue? targetEnvironmentId,
  }) {
    return _NetworkOperationHop(
      sourceAppType: sourceAppType,
      targetAppType: targetAppType,
      sourceNodeId: sourceNodeId,
      sourceInterfaceId: sourceInterfaceId,
      sourceEnvironmentId: sourceEnvironmentId,
      targetNodeId: targetNodeId,
      targetInterfaceId: targetInterfaceId,
      targetEnvironmentId: targetEnvironmentId,
    );
  }

  factory NetworkOperationHop.fromJson(Map<String, dynamic> json) =>
      _$NetworkOperationHopFromJson(json);
}

@freezed
abstract class NetworkOperation with _$NetworkOperation {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkOperation.def({
    @UuidValueConverter() required UuidValue id,
    @JsonKey(
      fromJson: NetworkOperationMessageTypeExtension.fromJson,
      toJson: NetworkOperationMessageTypeExtension.toJson,
    )
    required NetworkOperationMessageType messageType,
    @JsonKey(
      fromJson: NetworkOperationTypeExtension.fromJson,
      toJson: NetworkOperationTypeExtension.toJson,
    )
    required NetworkOperationType type,
    @Default(const []) List<NetworkOperationHop> networkOperationHopList,
    NetworkRequest? networkRequest,
    NetworkResponse? networkResponse,
    ApiOperation? apiOperation,
    ServiceOperation? serviceOperation,
    NetworkNodeOperation? networkNodeOperation,
  }) = _NetworkOperation;

  factory NetworkOperation({
    UuidValue? id,
    NetworkOperationMessageType? messageType,
    NetworkOperationType? type,
    List<NetworkOperationHop> networkOperationHopList = const [],
    NetworkRequest? networkRequest,
    NetworkResponse? networkResponse,
    ApiOperation? apiOperation,
    ServiceOperation? serviceOperation,
    NetworkNodeOperation? networkNodeOperation,
  }) {
    return _NetworkOperation(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      messageType: messageType ?? NetworkOperationMessageType.notification,
      type: type ?? NetworkOperationType.api,
      networkOperationHopList: networkOperationHopList,
      networkRequest: networkRequest,
      networkResponse: networkResponse,
      apiOperation: apiOperation,
      serviceOperation: serviceOperation,
      networkNodeOperation: networkNodeOperation,
    );
  }

  factory NetworkOperation.fromJson(Map<String, dynamic> json) =>
      _$NetworkOperationFromJson({
        ...json,
        if (!json.containsKey('message_type')) 'message_type': 'notification',
        if (!json.containsKey('type')) 'type': 'api',
      });
}
