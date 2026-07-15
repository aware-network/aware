// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'network_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_NetworkRequest _$NetworkRequestFromJson(Map<String, dynamic> json) =>
    _NetworkRequest(
      id: _$JsonConverterFromJson<String, UuidValue>(
        json['id'],
        const UuidValueConverter().fromJson,
      ),
      status: NetworkRequestStatusExtension.fromJson(json['status'] as String),
      requesterId: _$JsonConverterFromJson<String, UuidValue>(
        json['requester_id'],
        const UuidValueConverter().fromJson,
      ),
      requester: json['requester'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$NetworkRequestToJson(_NetworkRequest instance) =>
    <String, dynamic>{
      'id': _$JsonConverterToJson<String, UuidValue>(
        instance.id,
        const UuidValueConverter().toJson,
      ),
      'status': NetworkRequestStatusExtension.toJson(instance.status),
      'requester_id': _$JsonConverterToJson<String, UuidValue>(
        instance.requesterId,
        const UuidValueConverter().toJson,
      ),
      'requester': instance.requester,
    };

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);

_NetworkResponse _$NetworkResponseFromJson(Map<String, dynamic> json) =>
    _NetworkResponse(
      id: _$JsonConverterFromJson<String, UuidValue>(
        json['id'],
        const UuidValueConverter().fromJson,
      ),
      status: NetworkRequestStatusExtension.fromJson(json['status'] as String),
      error: json['error'] as String?,
      networkRequestId: _$JsonConverterFromJson<String, UuidValue>(
        json['network_request_id'],
        const UuidValueConverter().fromJson,
      ),
    );

Map<String, dynamic> _$NetworkResponseToJson(_NetworkResponse instance) =>
    <String, dynamic>{
      'id': _$JsonConverterToJson<String, UuidValue>(
        instance.id,
        const UuidValueConverter().toJson,
      ),
      'status': NetworkRequestStatusExtension.toJson(instance.status),
      'error': instance.error,
      'network_request_id': _$JsonConverterToJson<String, UuidValue>(
        instance.networkRequestId,
        const UuidValueConverter().toJson,
      ),
    };

_NetworkOperationHop _$NetworkOperationHopFromJson(Map<String, dynamic> json) =>
    _NetworkOperationHop(
      sourceAppType: NetworkAppTypeExtension.fromJson(
        json['source_app_type'] as String,
      ),
      targetAppType: NetworkAppTypeExtension.fromJson(
        json['target_app_type'] as String,
      ),
      sourceNodeId: _$JsonConverterFromJson<String, UuidValue>(
        json['source_node_id'],
        const UuidValueConverter().fromJson,
      ),
      sourceInterfaceId: _$JsonConverterFromJson<String, UuidValue>(
        json['source_interface_id'],
        const UuidValueConverter().fromJson,
      ),
      sourceEnvironmentId: _$JsonConverterFromJson<String, UuidValue>(
        json['source_environment_id'],
        const UuidValueConverter().fromJson,
      ),
      targetNodeId: _$JsonConverterFromJson<String, UuidValue>(
        json['target_node_id'],
        const UuidValueConverter().fromJson,
      ),
      targetInterfaceId: _$JsonConverterFromJson<String, UuidValue>(
        json['target_interface_id'],
        const UuidValueConverter().fromJson,
      ),
      targetEnvironmentId: _$JsonConverterFromJson<String, UuidValue>(
        json['target_environment_id'],
        const UuidValueConverter().fromJson,
      ),
    );

Map<String, dynamic> _$NetworkOperationHopToJson(
  _NetworkOperationHop instance,
) => <String, dynamic>{
  'source_app_type': NetworkAppTypeExtension.toJson(instance.sourceAppType),
  'target_app_type': NetworkAppTypeExtension.toJson(instance.targetAppType),
  'source_node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.sourceNodeId,
    const UuidValueConverter().toJson,
  ),
  'source_interface_id': _$JsonConverterToJson<String, UuidValue>(
    instance.sourceInterfaceId,
    const UuidValueConverter().toJson,
  ),
  'source_environment_id': _$JsonConverterToJson<String, UuidValue>(
    instance.sourceEnvironmentId,
    const UuidValueConverter().toJson,
  ),
  'target_node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.targetNodeId,
    const UuidValueConverter().toJson,
  ),
  'target_interface_id': _$JsonConverterToJson<String, UuidValue>(
    instance.targetInterfaceId,
    const UuidValueConverter().toJson,
  ),
  'target_environment_id': _$JsonConverterToJson<String, UuidValue>(
    instance.targetEnvironmentId,
    const UuidValueConverter().toJson,
  ),
};

_NetworkOperation _$NetworkOperationFromJson(
  Map<String, dynamic> json,
) => _NetworkOperation(
  id: const UuidValueConverter().fromJson(json['id'] as String),
  messageType: NetworkOperationMessageTypeExtension.fromJson(
    json['message_type'] as String,
  ),
  type: NetworkOperationTypeExtension.fromJson(json['type'] as String),
  networkOperationHopList:
      (json['network_operation_hop_list'] as List<dynamic>?)
          ?.map((e) => NetworkOperationHop.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  networkRequest: json['network_request'] == null
      ? null
      : NetworkRequest.fromJson(
          json['network_request'] as Map<String, dynamic>,
        ),
  networkResponse: json['network_response'] == null
      ? null
      : NetworkResponse.fromJson(
          json['network_response'] as Map<String, dynamic>,
        ),
  apiOperation: json['api_operation'] == null
      ? null
      : ApiOperation.fromJson(json['api_operation'] as Map<String, dynamic>),
  serviceOperation: json['service_operation'] == null
      ? null
      : ServiceOperation.fromJson(
          json['service_operation'] as Map<String, dynamic>,
        ),
  networkNodeOperation: json['network_node_operation'] == null
      ? null
      : NetworkNodeOperation.fromJson(
          json['network_node_operation'] as Map<String, dynamic>,
        ),
);

Map<String, dynamic> _$NetworkOperationToJson(_NetworkOperation instance) =>
    <String, dynamic>{
      'id': const UuidValueConverter().toJson(instance.id),
      'message_type': NetworkOperationMessageTypeExtension.toJson(
        instance.messageType,
      ),
      'type': NetworkOperationTypeExtension.toJson(instance.type),
      'network_operation_hop_list': instance.networkOperationHopList
          .map((e) => e.toJson())
          .toList(),
      'network_request': instance.networkRequest?.toJson(),
      'network_response': instance.networkResponse?.toJson(),
      'api_operation': instance.apiOperation?.toJson(),
      'service_operation': instance.serviceOperation?.toJson(),
      'network_node_operation': instance.networkNodeOperation?.toJson(),
    };
