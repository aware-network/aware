// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'public_map_discovery_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DiscoverPublicMapRequest _$DiscoverPublicMapRequestFromJson(
  Map<String, dynamic> json,
) => DiscoverPublicMapRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  query: json['query'] as String?,
  artifactFamily: json['artifact_family'] as String?,
  artifactKey: json['artifact_key'] as String?,
  packageName: json['package_name'] as String?,
  experienceName: json['experience_name'] as String?,
  channel: json['channel'] as String?,
  authorityBaseUrl: json['authority_base_url'] as String?,
  indexUrl: json['index_url'] as String?,
  limit: (json['limit'] as num).toInt(),
);

Map<String, dynamic> _$DiscoverPublicMapRequestToJson(
  DiscoverPublicMapRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'query': instance.query,
  'artifact_family': instance.artifactFamily,
  'artifact_key': instance.artifactKey,
  'package_name': instance.packageName,
  'experience_name': instance.experienceName,
  'channel': instance.channel,
  'authority_base_url': instance.authorityBaseUrl,
  'index_url': instance.indexUrl,
  'limit': instance.limit,
};

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);

DiscoverPublicMapResponse _$DiscoverPublicMapResponseFromJson(
  Map<String, dynamic> json,
) => DiscoverPublicMapResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  info: json['info'] as String?,
  error: json['error'] as String?,
  authoritySourceUrl: json['authority_source_url'] as String?,
  entries:
      (json['entries'] as List<dynamic>?)
          ?.map((e) => HubPublicMapEntry.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
);

Map<String, dynamic> _$DiscoverPublicMapResponseToJson(
  DiscoverPublicMapResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'info': instance.info,
  'error': instance.error,
  'authority_source_url': instance.authoritySourceUrl,
  'entries': instance.entries.map((e) => e.toJson()).toList(),
};

_HubPublicMapEntry _$HubPublicMapEntryFromJson(Map<String, dynamic> json) =>
    _HubPublicMapEntry(
      artifactFamily: json['artifact_family'] as String,
      artifactKey: json['artifact_key'] as String,
      channel: json['channel'] as String,
      revisionId: json['revision_id'] as String?,
      packageName: json['package_name'] as String?,
      language: json['language'] as String?,
      surface: json['surface'] as String?,
      manifestKind: json['manifest_kind'] as String?,
      digest: json['digest'] as String?,
      artifactUrl: json['artifact_url'] as String?,
      artifactSha256: json['artifact_sha256'] as String?,
      artifactSizeBytes: (json['artifact_size_bytes'] as num?)?.toInt(),
      mediaType: json['media_type'] as String?,
      title: json['title'] as String?,
      summary: json['summary'] as String?,
      experienceName: json['experience_name'] as String?,
      fqnPrefix: json['fqn_prefix'] as String?,
      producerKind: json['producer_kind'] as String?,
      producerRevisionId: json['producer_revision_id'] as String?,
      sourceRevisionId: json['source_revision_id'] as String?,
      visibility: json['visibility'] as String,
      metadata: json['metadata'] as Map<String, dynamic>,
    );

Map<String, dynamic> _$HubPublicMapEntryToJson(_HubPublicMapEntry instance) =>
    <String, dynamic>{
      'artifact_family': instance.artifactFamily,
      'artifact_key': instance.artifactKey,
      'channel': instance.channel,
      'revision_id': instance.revisionId,
      'package_name': instance.packageName,
      'language': instance.language,
      'surface': instance.surface,
      'manifest_kind': instance.manifestKind,
      'digest': instance.digest,
      'artifact_url': instance.artifactUrl,
      'artifact_sha256': instance.artifactSha256,
      'artifact_size_bytes': instance.artifactSizeBytes,
      'media_type': instance.mediaType,
      'title': instance.title,
      'summary': instance.summary,
      'experience_name': instance.experienceName,
      'fqn_prefix': instance.fqnPrefix,
      'producer_kind': instance.producerKind,
      'producer_revision_id': instance.producerRevisionId,
      'source_revision_id': instance.sourceRevisionId,
      'visibility': instance.visibility,
      'metadata': instance.metadata,
    };
