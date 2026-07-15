// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'channel_heads_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_HubPublicDiscoveryDescriptorV1 _$HubPublicDiscoveryDescriptorV1FromJson(
  Map<String, dynamic> json,
) => _HubPublicDiscoveryDescriptorV1(
  packageName: json['package_name'] as String?,
  language: json['language'] as String?,
  surface: json['surface'] as String?,
  manifestKind: json['manifest_kind'] as String?,
  version: json['version'] as String?,
  revisionId: json['revision_id'] as String?,
  digest: json['digest'] as String?,
  packageRoot: json['package_root'] as String?,
  sourcesRoot: json['sources_root'] as String?,
  fqnPrefix: json['fqn_prefix'] as String?,
  manifestRelativePath: json['manifest_relative_path'] as String?,
  artifactMediaType: json['artifact_media_type'] as String?,
  artifactSizeBytes: (json['artifact_size_bytes'] as num?)?.toInt(),
  downloadHandle: json['download_handle'] as String?,
  metadata: json['metadata'] as Map<String, dynamic>,
);

Map<String, dynamic> _$HubPublicDiscoveryDescriptorV1ToJson(
  _HubPublicDiscoveryDescriptorV1 instance,
) => <String, dynamic>{
  'package_name': instance.packageName,
  'language': instance.language,
  'surface': instance.surface,
  'manifest_kind': instance.manifestKind,
  'version': instance.version,
  'revision_id': instance.revisionId,
  'digest': instance.digest,
  'package_root': instance.packageRoot,
  'sources_root': instance.sourcesRoot,
  'fqn_prefix': instance.fqnPrefix,
  'manifest_relative_path': instance.manifestRelativePath,
  'artifact_media_type': instance.artifactMediaType,
  'artifact_size_bytes': instance.artifactSizeBytes,
  'download_handle': instance.downloadHandle,
  'metadata': instance.metadata,
};

_HubPublicDiscoveryArtifactLockV1 _$HubPublicDiscoveryArtifactLockV1FromJson(
  Map<String, dynamic> json,
) => _HubPublicDiscoveryArtifactLockV1(
  artifactUrl: json['artifact_url'] as String?,
  sha256: json['sha256'] as String?,
  sizeBytes: (json['size_bytes'] as num?)?.toInt(),
  mediaType: json['media_type'] as String?,
  archiveFormat: json['archive_format'] as String?,
  revisionId: json['revision_id'] as String?,
  publishedAt: json['published_at'] as String?,
);

Map<String, dynamic> _$HubPublicDiscoveryArtifactLockV1ToJson(
  _HubPublicDiscoveryArtifactLockV1 instance,
) => <String, dynamic>{
  'artifact_url': instance.artifactUrl,
  'sha256': instance.sha256,
  'size_bytes': instance.sizeBytes,
  'media_type': instance.mediaType,
  'archive_format': instance.archiveFormat,
  'revision_id': instance.revisionId,
  'published_at': instance.publishedAt,
};

_HubPublicDiscoveryEntryV1 _$HubPublicDiscoveryEntryV1FromJson(
  Map<String, dynamic> json,
) => _HubPublicDiscoveryEntryV1(
  packageName: json['package_name'] as String?,
  language: json['language'] as String?,
  surface: json['surface'] as String?,
  channel: json['channel'] as String,
  revisionId: json['revision_id'] as String?,
  updatedAt: json['updated_at'] as String?,
  publisherExecutionId: json['publisher_execution_id'] as String?,
  idempotencyKey: json['idempotency_key'] as String?,
  metadata: json['metadata'] as Map<String, dynamic>,
  descriptor: json['descriptor'] == null
      ? null
      : HubPublicDiscoveryDescriptorV1.fromJson(
          json['descriptor'] as Map<String, dynamic>,
        ),
  artifactLock: json['artifact_lock'] == null
      ? null
      : HubPublicDiscoveryArtifactLockV1.fromJson(
          json['artifact_lock'] as Map<String, dynamic>,
        ),
  refs: json['refs'] as Map<String, dynamic>,
);

Map<String, dynamic> _$HubPublicDiscoveryEntryV1ToJson(
  _HubPublicDiscoveryEntryV1 instance,
) => <String, dynamic>{
  'package_name': instance.packageName,
  'language': instance.language,
  'surface': instance.surface,
  'channel': instance.channel,
  'revision_id': instance.revisionId,
  'updated_at': instance.updatedAt,
  'publisher_execution_id': instance.publisherExecutionId,
  'idempotency_key': instance.idempotencyKey,
  'metadata': instance.metadata,
  'descriptor': instance.descriptor?.toJson(),
  'artifact_lock': instance.artifactLock?.toJson(),
  'refs': instance.refs,
};

_HubPublicDiscoveryViewStateV1 _$HubPublicDiscoveryViewStateV1FromJson(
  Map<String, dynamic> json,
) => _HubPublicDiscoveryViewStateV1(
  status: json['status'] as String,
  authoritySourceUrl: json['authority_source_url'] as String?,
  query: json['query'] as String?,
  packageName: json['package_name'] as String?,
  language: json['language'] as String?,
  surface: json['surface'] as String?,
  channel: json['channel'] as String?,
  limit: (json['limit'] as num).toInt(),
  entries:
      (json['entries'] as List<dynamic>?)
          ?.map(
            (e) =>
                HubPublicDiscoveryEntryV1.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  summary: json['summary'] as String?,
  emptyMessage: json['empty_message'] as String,
  error: json['error'] as String?,
  provenance: json['provenance'] as Map<String, dynamic>,
);

Map<String, dynamic> _$HubPublicDiscoveryViewStateV1ToJson(
  _HubPublicDiscoveryViewStateV1 instance,
) => <String, dynamic>{
  'status': instance.status,
  'authority_source_url': instance.authoritySourceUrl,
  'query': instance.query,
  'package_name': instance.packageName,
  'language': instance.language,
  'surface': instance.surface,
  'channel': instance.channel,
  'limit': instance.limit,
  'entries': instance.entries.map((e) => e.toJson()).toList(),
  'summary': instance.summary,
  'empty_message': instance.emptyMessage,
  'error': instance.error,
  'provenance': instance.provenance,
};
