// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'api_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_ApiOperationContext _$ApiOperationContextFromJson(Map<String, dynamic> json) =>
    _ApiOperationContext(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
    );

Map<String, dynamic> _$ApiOperationContextToJson(
  _ApiOperationContext instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
};

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);

_ApiOperation _$ApiOperationFromJson(
  Map<String, dynamic> json,
) => _ApiOperation(
  request: json['request'] == null
      ? null
      : ApiOperationRequest.fromJson(json['request'] as Map<String, dynamic>),
  response: json['response'] == null
      ? null
      : ApiOperationResponse.fromJson(json['response'] as Map<String, dynamic>),
);

Map<String, dynamic> _$ApiOperationToJson(_ApiOperation instance) =>
    <String, dynamic>{
      'request': instance.request?.toJson(),
      'response': instance.response?.toJson(),
    };

_ApiOperationRequest _$ApiOperationRequestFromJson(Map<String, dynamic> json) =>
    _ApiOperationRequest(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      operation: json['operation'] as String,
    );

Map<String, dynamic> _$ApiOperationRequestToJson(
  _ApiOperationRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'operation': instance.operation,
};

_ApiOperationResponse _$ApiOperationResponseFromJson(
  Map<String, dynamic> json,
) => _ApiOperationResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  operation: json['operation'] as String,
);

Map<String, dynamic> _$ApiOperationResponseToJson(
  _ApiOperationResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'operation': instance.operation,
};
