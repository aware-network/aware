// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'media_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_StorageBlobRef _$StorageBlobRefFromJson(Map<String, dynamic> json) =>
    _StorageBlobRef(
      objectId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_id'],
        const UuidValueConverter().fromJson,
      ),
      sha: json['sha'] as String?,
    );

Map<String, dynamic> _$StorageBlobRefToJson(_StorageBlobRef instance) =>
    <String, dynamic>{
      'object_id': _$JsonConverterToJson<String, UuidValue>(
        instance.objectId,
        const UuidValueConverter().toJson,
      ),
      'sha': instance.sha,
    };

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);

_StorageMediaRef _$StorageMediaRefFromJson(Map<String, dynamic> json) =>
    _StorageMediaRef(
      objectId: const UuidValueConverter().fromJson(
        json['object_id'] as String,
      ),
      uri: json['uri'] as String?,
      uriScheme: json['uri_scheme'] as String,
      mediaKind: json['media_kind'] as String?,
      mimeType: json['mime_type'] as String?,
      sha: json['sha'] as String?,
      variantKey: json['variant_key'] as String?,
      renditionKey: json['rendition_key'] as String?,
      filename: json['filename'] as String?,
      metadata: json['metadata'] as Map<String, dynamic>,
    );

Map<String, dynamic> _$StorageMediaRefToJson(_StorageMediaRef instance) =>
    <String, dynamic>{
      'object_id': const UuidValueConverter().toJson(instance.objectId),
      'uri': instance.uri,
      'uri_scheme': instance.uriScheme,
      'media_kind': instance.mediaKind,
      'mime_type': instance.mimeType,
      'sha': instance.sha,
      'variant_key': instance.variantKey,
      'rendition_key': instance.renditionKey,
      'filename': instance.filename,
      'metadata': instance.metadata,
    };

_StorageBlobMetadata _$StorageBlobMetadataFromJson(Map<String, dynamic> json) =>
    _StorageBlobMetadata(
      objectId: const UuidValueConverter().fromJson(
        json['object_id'] as String,
      ),
      sha: json['sha'] as String,
      mimeType: json['mime_type'] as String,
      sizeBytes: (json['size_bytes'] as num).toInt(),
      objectKey: json['object_key'] as String?,
      pathLocal: json['path_local'] as String?,
      bucketId: _$JsonConverterFromJson<String, UuidValue>(
        json['bucket_id'],
        const UuidValueConverter().fromJson,
      ),
    );

Map<String, dynamic> _$StorageBlobMetadataToJson(
  _StorageBlobMetadata instance,
) => <String, dynamic>{
  'object_id': const UuidValueConverter().toJson(instance.objectId),
  'sha': instance.sha,
  'mime_type': instance.mimeType,
  'size_bytes': instance.sizeBytes,
  'object_key': instance.objectKey,
  'path_local': instance.pathLocal,
  'bucket_id': _$JsonConverterToJson<String, UuidValue>(
    instance.bucketId,
    const UuidValueConverter().toJson,
  ),
};

_StorageMediaResolution _$StorageMediaResolutionFromJson(
  Map<String, dynamic> json,
) => _StorageMediaResolution(
  mediaRef: StorageMediaRef.fromJson(json['media_ref'] as Map<String, dynamic>),
  objectId: const UuidValueConverter().fromJson(json['object_id'] as String),
  sha: json['sha'] as String,
  mimeType: json['mime_type'] as String,
  sizeBytes: (json['size_bytes'] as num).toInt(),
  uri: json['uri'] as String,
  uriScheme: json['uri_scheme'] as String,
  httpUrl: json['http_url'] as String?,
  cacheControl: json['cache_control'] as String?,
  etag: json['etag'] as String?,
  contentDisposition: json['content_disposition'] as String?,
  filename: json['filename'] as String?,
  expiresAt: json['expires_at'] as String?,
  metadata: json['metadata'] as Map<String, dynamic>,
);

Map<String, dynamic> _$StorageMediaResolutionToJson(
  _StorageMediaResolution instance,
) => <String, dynamic>{
  'media_ref': instance.mediaRef.toJson(),
  'object_id': const UuidValueConverter().toJson(instance.objectId),
  'sha': instance.sha,
  'mime_type': instance.mimeType,
  'size_bytes': instance.sizeBytes,
  'uri': instance.uri,
  'uri_scheme': instance.uriScheme,
  'http_url': instance.httpUrl,
  'cache_control': instance.cacheControl,
  'etag': instance.etag,
  'content_disposition': instance.contentDisposition,
  'filename': instance.filename,
  'expires_at': instance.expiresAt,
  'metadata': instance.metadata,
};

_StorageOperationReceipt _$StorageOperationReceiptFromJson(
  Map<String, dynamic> json,
) => _StorageOperationReceipt(
  operation: json['operation'] as String,
  status: json['status'] as String,
  objectId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_id'],
    const UuidValueConverter().fromJson,
  ),
  sha: json['sha'] as String?,
  sizeBytes: (json['size_bytes'] as num?)?.toInt(),
  mimeType: json['mime_type'] as String?,
  backendKind: json['backend_kind'] as String,
  dataPlane: json['data_plane'] as String,
  metadata: json['metadata'] as Map<String, dynamic>,
);

Map<String, dynamic> _$StorageOperationReceiptToJson(
  _StorageOperationReceipt instance,
) => <String, dynamic>{
  'operation': instance.operation,
  'status': instance.status,
  'object_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectId,
    const UuidValueConverter().toJson,
  ),
  'sha': instance.sha,
  'size_bytes': instance.sizeBytes,
  'mime_type': instance.mimeType,
  'backend_kind': instance.backendKind,
  'data_plane': instance.dataPlane,
  'metadata': instance.metadata,
};
