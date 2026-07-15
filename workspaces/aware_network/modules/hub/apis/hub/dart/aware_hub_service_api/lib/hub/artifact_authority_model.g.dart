// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'artifact_authority_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PublishHubArtifactRequest _$PublishHubArtifactRequestFromJson(
  Map<String, dynamic> json,
) => PublishHubArtifactRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  artifactFamily: json['artifact_family'] as String,
  artifactKey: json['artifact_key'] as String,
  revisionId: json['revision_id'] as String,
  channel: json['channel'] as String,
  authorityBaseUrl: json['authority_base_url'] as String?,
  indexUrl: json['index_url'] as String?,
  payloadUrl: json['payload_url'] as String?,
  payloadSha256: json['payload_sha256'] as String?,
  payloadSizeBytes: (json['payload_size_bytes'] as num?)?.toInt(),
  payloadMediaType: json['payload_media_type'] as String?,
  payloadContract: json['payload_contract'] as String?,
  payloadJson: json['payload_json'] as Map<String, dynamic>?,
  payloadBytesBase64: json['payload_bytes_base64'] as String?,
  payloadSourceUrl: json['payload_source_url'] as String?,
  selectorKey: json['selector_key'] as String?,
  targetRef: json['target_ref'] as String?,
  producer: json['producer'] == null
      ? null
      : HubArtifactProducerProvenance.fromJson(
          json['producer'] as Map<String, dynamic>,
        ),
  publisherExecutionId: json['publisher_execution_id'] as String?,
  idempotencyKey: json['idempotency_key'] as String?,
  publishedAtUtc: json['published_at_utc'] as String?,
  metadata: json['metadata'] as Map<String, dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$PublishHubArtifactRequestToJson(
  PublishHubArtifactRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'artifact_family': instance.artifactFamily,
  'artifact_key': instance.artifactKey,
  'revision_id': instance.revisionId,
  'channel': instance.channel,
  'authority_base_url': instance.authorityBaseUrl,
  'index_url': instance.indexUrl,
  'payload_url': instance.payloadUrl,
  'payload_sha256': instance.payloadSha256,
  'payload_size_bytes': instance.payloadSizeBytes,
  'payload_media_type': instance.payloadMediaType,
  'payload_contract': instance.payloadContract,
  'payload_json': instance.payloadJson,
  'payload_bytes_base64': instance.payloadBytesBase64,
  'payload_source_url': instance.payloadSourceUrl,
  'selector_key': instance.selectorKey,
  'target_ref': instance.targetRef,
  'producer': instance.producer?.toJson(),
  'publisher_execution_id': instance.publisherExecutionId,
  'idempotency_key': instance.idempotencyKey,
  'published_at_utc': instance.publishedAtUtc,
  'metadata': instance.metadata,
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

ResolveHubArtifactRequest _$ResolveHubArtifactRequestFromJson(
  Map<String, dynamic> json,
) => ResolveHubArtifactRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  artifactFamily: json['artifact_family'] as String,
  artifactKey: json['artifact_key'] as String,
  channel: json['channel'] as String,
  revisionId: json['revision_id'] as String?,
  authorityBaseUrl: json['authority_base_url'] as String?,
  indexUrl: json['index_url'] as String?,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$ResolveHubArtifactRequestToJson(
  ResolveHubArtifactRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'artifact_family': instance.artifactFamily,
  'artifact_key': instance.artifactKey,
  'channel': instance.channel,
  'revision_id': instance.revisionId,
  'authority_base_url': instance.authorityBaseUrl,
  'index_url': instance.indexUrl,
  'operation': instance.$type,
};

PublishHubArtifactResponse _$PublishHubArtifactResponseFromJson(
  Map<String, dynamic> json,
) => PublishHubArtifactResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  info: json['info'] as String?,
  error: json['error'] as String?,
  accepted: json['accepted'] as bool,
  authoritySourceUrl: json['authority_source_url'] as String,
  artifactLock: HubArtifactPayloadLock.fromJson(
    json['artifact_lock'] as Map<String, dynamic>,
  ),
  producer: json['producer'] == null
      ? null
      : HubArtifactProducerProvenance.fromJson(
          json['producer'] as Map<String, dynamic>,
        ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$PublishHubArtifactResponseToJson(
  PublishHubArtifactResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'info': instance.info,
  'error': instance.error,
  'accepted': instance.accepted,
  'authority_source_url': instance.authoritySourceUrl,
  'artifact_lock': instance.artifactLock.toJson(),
  'producer': instance.producer?.toJson(),
  'operation': instance.$type,
};

ResolveHubArtifactResponse _$ResolveHubArtifactResponseFromJson(
  Map<String, dynamic> json,
) => ResolveHubArtifactResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  info: json['info'] as String?,
  error: json['error'] as String?,
  authoritySourceUrl: json['authority_source_url'] as String,
  artifactLock: HubArtifactPayloadLock.fromJson(
    json['artifact_lock'] as Map<String, dynamic>,
  ),
  producer: json['producer'] == null
      ? null
      : HubArtifactProducerProvenance.fromJson(
          json['producer'] as Map<String, dynamic>,
        ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$ResolveHubArtifactResponseToJson(
  ResolveHubArtifactResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'info': instance.info,
  'error': instance.error,
  'authority_source_url': instance.authoritySourceUrl,
  'artifact_lock': instance.artifactLock.toJson(),
  'producer': instance.producer?.toJson(),
  'operation': instance.$type,
};

_HubArtifactProducerProvenance _$HubArtifactProducerProvenanceFromJson(
  Map<String, dynamic> json,
) => _HubArtifactProducerProvenance(
  producerKind: json['producer_kind'] as String,
  producerKey: json['producer_key'] as String,
  provenanceKey: json['provenance_key'] as String?,
  producerRevisionId: json['producer_revision_id'] as String?,
  sourceRevisionId: json['source_revision_id'] as String?,
  sourceRevisionKind: json['source_revision_kind'] as String?,
  materializationRef: json['materialization_ref'] as String?,
  buildRef: json['build_ref'] as String?,
  metadata: json['metadata'] as Map<String, dynamic>,
);

Map<String, dynamic> _$HubArtifactProducerProvenanceToJson(
  _HubArtifactProducerProvenance instance,
) => <String, dynamic>{
  'producer_kind': instance.producerKind,
  'producer_key': instance.producerKey,
  'provenance_key': instance.provenanceKey,
  'producer_revision_id': instance.producerRevisionId,
  'source_revision_id': instance.sourceRevisionId,
  'source_revision_kind': instance.sourceRevisionKind,
  'materialization_ref': instance.materializationRef,
  'build_ref': instance.buildRef,
  'metadata': instance.metadata,
};

_HubArtifactPayloadLock _$HubArtifactPayloadLockFromJson(
  Map<String, dynamic> json,
) => _HubArtifactPayloadLock(
  artifactFamily: json['artifact_family'] as String,
  artifactKey: json['artifact_key'] as String,
  channel: json['channel'] as String,
  revisionId: json['revision_id'] as String,
  payloadUrl: json['payload_url'] as String,
  payloadSha256: json['payload_sha256'] as String,
  payloadSizeBytes: (json['payload_size_bytes'] as num?)?.toInt(),
  payloadMediaType: json['payload_media_type'] as String?,
  payloadContract: json['payload_contract'] as String?,
  authoritySourceUrl: json['authority_source_url'] as String?,
  selectorKey: json['selector_key'] as String?,
  targetRef: json['target_ref'] as String?,
  metadata: json['metadata'] as Map<String, dynamic>,
);

Map<String, dynamic> _$HubArtifactPayloadLockToJson(
  _HubArtifactPayloadLock instance,
) => <String, dynamic>{
  'artifact_family': instance.artifactFamily,
  'artifact_key': instance.artifactKey,
  'channel': instance.channel,
  'revision_id': instance.revisionId,
  'payload_url': instance.payloadUrl,
  'payload_sha256': instance.payloadSha256,
  'payload_size_bytes': instance.payloadSizeBytes,
  'payload_media_type': instance.payloadMediaType,
  'payload_contract': instance.payloadContract,
  'authority_source_url': instance.authoritySourceUrl,
  'selector_key': instance.selectorKey,
  'target_ref': instance.targetRef,
  'metadata': instance.metadata,
};
