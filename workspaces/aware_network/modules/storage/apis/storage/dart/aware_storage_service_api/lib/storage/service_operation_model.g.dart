// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'service_operation_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

RegisterStorageBlobRequest _$RegisterStorageBlobRequestFromJson(
  Map<String, dynamic> json,
) => RegisterStorageBlobRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  objectId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_id'],
    const UuidValueConverter().fromJson,
  ),
  sha: json['sha'] as String,
  mimeType: json['mime_type'] as String,
  sizeBytes: (json['size_bytes'] as num).toInt(),
  bucketId: _$JsonConverterFromJson<String, UuidValue>(
    json['bucket_id'],
    const UuidValueConverter().fromJson,
  ),
  objectKey: json['object_key'] as String?,
  pathLocal: json['path_local'] as String?,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$RegisterStorageBlobRequestToJson(
  RegisterStorageBlobRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'object_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectId,
    const UuidValueConverter().toJson,
  ),
  'sha': instance.sha,
  'mime_type': instance.mimeType,
  'size_bytes': instance.sizeBytes,
  'bucket_id': _$JsonConverterToJson<String, UuidValue>(
    instance.bucketId,
    const UuidValueConverter().toJson,
  ),
  'object_key': instance.objectKey,
  'path_local': instance.pathLocal,
  'operation': instance.$type,
};

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);

DescribeStorageBlobRequest _$DescribeStorageBlobRequestFromJson(
  Map<String, dynamic> json,
) => DescribeStorageBlobRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  objectId: const UuidValueConverter().fromJson(json['object_id'] as String),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DescribeStorageBlobRequestToJson(
  DescribeStorageBlobRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'object_id': const UuidValueConverter().toJson(instance.objectId),
  'operation': instance.$type,
};

ResolveStorageMediaRequest _$ResolveStorageMediaRequestFromJson(
  Map<String, dynamic> json,
) => ResolveStorageMediaRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  mediaRef: StorageMediaRef.fromJson(json['media_ref'] as Map<String, dynamic>),
  requireOwnership: json['require_ownership'] as bool,
  includeHttpUrl: json['include_http_url'] as bool,
  preferredUriScheme: json['preferred_uri_scheme'] as String?,
  filename: json['filename'] as String?,
  disposition: StorageMediaDispositionExtension.fromJson(
    json['disposition'] as String,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$ResolveStorageMediaRequestToJson(
  ResolveStorageMediaRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'media_ref': instance.mediaRef.toJson(),
  'require_ownership': instance.requireOwnership,
  'include_http_url': instance.includeHttpUrl,
  'preferred_uri_scheme': instance.preferredUriScheme,
  'filename': instance.filename,
  'disposition': StorageMediaDispositionExtension.toJson(instance.disposition),
  'operation': instance.$type,
};

RegisterStorageBlobResponse _$RegisterStorageBlobResponseFromJson(
  Map<String, dynamic> json,
) => RegisterStorageBlobResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  error: json['error'] as String?,
  receipt: json['receipt'] == null
      ? null
      : StorageOperationReceipt.fromJson(
          json['receipt'] as Map<String, dynamic>,
        ),
  metadata: json['metadata'] == null
      ? null
      : StorageBlobMetadata.fromJson(json['metadata'] as Map<String, dynamic>),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$RegisterStorageBlobResponseToJson(
  RegisterStorageBlobResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'error': instance.error,
  'receipt': instance.receipt?.toJson(),
  'metadata': instance.metadata?.toJson(),
  'operation': instance.$type,
};

DescribeStorageBlobResponse _$DescribeStorageBlobResponseFromJson(
  Map<String, dynamic> json,
) => DescribeStorageBlobResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  error: json['error'] as String?,
  receipt: json['receipt'] == null
      ? null
      : StorageOperationReceipt.fromJson(
          json['receipt'] as Map<String, dynamic>,
        ),
  metadata: json['metadata'] == null
      ? null
      : StorageBlobMetadata.fromJson(json['metadata'] as Map<String, dynamic>),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DescribeStorageBlobResponseToJson(
  DescribeStorageBlobResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'error': instance.error,
  'receipt': instance.receipt?.toJson(),
  'metadata': instance.metadata?.toJson(),
  'operation': instance.$type,
};

ResolveStorageMediaResponse _$ResolveStorageMediaResponseFromJson(
  Map<String, dynamic> json,
) => ResolveStorageMediaResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  error: json['error'] as String?,
  receipt: json['receipt'] == null
      ? null
      : StorageOperationReceipt.fromJson(
          json['receipt'] as Map<String, dynamic>,
        ),
  metadata: json['metadata'] == null
      ? null
      : StorageBlobMetadata.fromJson(json['metadata'] as Map<String, dynamic>),
  resolution: json['resolution'] == null
      ? null
      : StorageMediaResolution.fromJson(
          json['resolution'] as Map<String, dynamic>,
        ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$ResolveStorageMediaResponseToJson(
  ResolveStorageMediaResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'error': instance.error,
  'receipt': instance.receipt?.toJson(),
  'metadata': instance.metadata?.toJson(),
  'resolution': instance.resolution?.toJson(),
  'operation': instance.$type,
};
