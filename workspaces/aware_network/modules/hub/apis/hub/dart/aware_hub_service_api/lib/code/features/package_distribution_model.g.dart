// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'package_distribution_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DiscoverCodePackageChannelHeadsRequest
_$DiscoverCodePackageChannelHeadsRequestFromJson(Map<String, dynamic> json) =>
    DiscoverCodePackageChannelHeadsRequest(
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      query: json['query'] as String?,
      packageName: json['package_name'] as String?,
      language: CodeLanguageExtension.fromJsonNullable(
        json['language'] as String?,
      ),
      surface: json['surface'] as String?,
      channel: json['channel'] as String?,
      authorityBaseUrl: json['authority_base_url'] as String?,
      indexUrl: json['index_url'] as String?,
      limit: (json['limit'] as num).toInt(),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$DiscoverCodePackageChannelHeadsRequestToJson(
  DiscoverCodePackageChannelHeadsRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'query': instance.query,
  'package_name': instance.packageName,
  'language': CodeLanguageExtension.toJsonNullable(instance.language),
  'surface': instance.surface,
  'channel': instance.channel,
  'authority_base_url': instance.authorityBaseUrl,
  'index_url': instance.indexUrl,
  'limit': instance.limit,
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

SearchCodePackageRequest _$SearchCodePackageRequestFromJson(
  Map<String, dynamic> json,
) => SearchCodePackageRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  query: json['query'] as String?,
  packageName: json['package_name'] as String?,
  language: CodeLanguageExtension.fromJsonNullable(json['language'] as String?),
  surface: json['surface'] as String?,
  channel: json['channel'] as String,
  authorityBaseUrl: json['authority_base_url'] as String?,
  indexUrl: json['index_url'] as String?,
  limit: (json['limit'] as num).toInt(),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$SearchCodePackageRequestToJson(
  SearchCodePackageRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'query': instance.query,
  'package_name': instance.packageName,
  'language': CodeLanguageExtension.toJsonNullable(instance.language),
  'surface': instance.surface,
  'channel': instance.channel,
  'authority_base_url': instance.authorityBaseUrl,
  'index_url': instance.indexUrl,
  'limit': instance.limit,
  'operation': instance.$type,
};

DescribeCodePackageRequest _$DescribeCodePackageRequestFromJson(
  Map<String, dynamic> json,
) => DescribeCodePackageRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  selector: CodePackageRef.fromJson(json['selector'] as Map<String, dynamic>),
  authorityBaseUrl: json['authority_base_url'] as String?,
  indexUrl: json['index_url'] as String?,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DescribeCodePackageRequestToJson(
  DescribeCodePackageRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'selector': instance.selector.toJson(),
  'authority_base_url': instance.authorityBaseUrl,
  'index_url': instance.indexUrl,
  'operation': instance.$type,
};

ResolveCodePackageRequest _$ResolveCodePackageRequestFromJson(
  Map<String, dynamic> json,
) => ResolveCodePackageRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  selector: CodePackageRef.fromJson(json['selector'] as Map<String, dynamic>),
  authorityBaseUrl: json['authority_base_url'] as String?,
  indexUrl: json['index_url'] as String?,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$ResolveCodePackageRequestToJson(
  ResolveCodePackageRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'selector': instance.selector.toJson(),
  'authority_base_url': instance.authorityBaseUrl,
  'index_url': instance.indexUrl,
  'operation': instance.$type,
};

DownloadCodePackageRequest _$DownloadCodePackageRequestFromJson(
  Map<String, dynamic> json,
) => DownloadCodePackageRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  selector: CodePackageRef.fromJson(json['selector'] as Map<String, dynamic>),
  authorityBaseUrl: json['authority_base_url'] as String?,
  indexUrl: json['index_url'] as String?,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DownloadCodePackageRequestToJson(
  DownloadCodePackageRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'selector': instance.selector.toJson(),
  'authority_base_url': instance.authorityBaseUrl,
  'index_url': instance.indexUrl,
  'operation': instance.$type,
};

PublishCodePackageRequest _$PublishCodePackageRequestFromJson(
  Map<String, dynamic> json,
) => PublishCodePackageRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  descriptor: CodePackageDescriptor.fromJson(
    json['descriptor'] as Map<String, dynamic>,
  ),
  artifactLock: CodePackageArtifactLock.fromJson(
    json['artifact_lock'] as Map<String, dynamic>,
  ),
  channel: json['channel'] as String,
  authorityBaseUrl: json['authority_base_url'] as String?,
  indexUrl: json['index_url'] as String?,
  publisherExecutionId: json['publisher_execution_id'] as String?,
  idempotencyKey: json['idempotency_key'] as String?,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$PublishCodePackageRequestToJson(
  PublishCodePackageRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'descriptor': instance.descriptor.toJson(),
  'artifact_lock': instance.artifactLock.toJson(),
  'channel': instance.channel,
  'authority_base_url': instance.authorityBaseUrl,
  'index_url': instance.indexUrl,
  'publisher_execution_id': instance.publisherExecutionId,
  'idempotency_key': instance.idempotencyKey,
  'operation': instance.$type,
};

DiscoverCodePackageChannelHeadsResponse
_$DiscoverCodePackageChannelHeadsResponseFromJson(Map<String, dynamic> json) =>
    DiscoverCodePackageChannelHeadsResponse(
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
              ?.map(
                (e) => CodePackageDiscoveryEntry.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$DiscoverCodePackageChannelHeadsResponseToJson(
  DiscoverCodePackageChannelHeadsResponse instance,
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
  'operation': instance.$type,
};

SearchCodePackageResponse _$SearchCodePackageResponseFromJson(
  Map<String, dynamic> json,
) => SearchCodePackageResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  info: json['info'] as String?,
  error: json['error'] as String?,
  authoritySourceUrl: json['authority_source_url'] as String?,
  descriptors:
      (json['descriptors'] as List<dynamic>?)
          ?.map(
            (e) => CodePackageDescriptor.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$SearchCodePackageResponseToJson(
  SearchCodePackageResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'info': instance.info,
  'error': instance.error,
  'authority_source_url': instance.authoritySourceUrl,
  'descriptors': instance.descriptors.map((e) => e.toJson()).toList(),
  'operation': instance.$type,
};

DescribeCodePackageResponse _$DescribeCodePackageResponseFromJson(
  Map<String, dynamic> json,
) => DescribeCodePackageResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  info: json['info'] as String?,
  error: json['error'] as String?,
  authoritySourceUrl: json['authority_source_url'] as String?,
  descriptor: json['descriptor'] == null
      ? null
      : CodePackageDescriptor.fromJson(
          json['descriptor'] as Map<String, dynamic>,
        ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DescribeCodePackageResponseToJson(
  DescribeCodePackageResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'info': instance.info,
  'error': instance.error,
  'authority_source_url': instance.authoritySourceUrl,
  'descriptor': instance.descriptor?.toJson(),
  'operation': instance.$type,
};

ResolveCodePackageResponse _$ResolveCodePackageResponseFromJson(
  Map<String, dynamic> json,
) => ResolveCodePackageResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  info: json['info'] as String?,
  error: json['error'] as String?,
  authoritySourceUrl: json['authority_source_url'] as String?,
  selector: CodePackageRef.fromJson(json['selector'] as Map<String, dynamic>),
  descriptor: CodePackageDescriptor.fromJson(
    json['descriptor'] as Map<String, dynamic>,
  ),
  artifactLock: CodePackageArtifactLock.fromJson(
    json['artifact_lock'] as Map<String, dynamic>,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$ResolveCodePackageResponseToJson(
  ResolveCodePackageResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'info': instance.info,
  'error': instance.error,
  'authority_source_url': instance.authoritySourceUrl,
  'selector': instance.selector.toJson(),
  'descriptor': instance.descriptor.toJson(),
  'artifact_lock': instance.artifactLock.toJson(),
  'operation': instance.$type,
};

DownloadCodePackageResponse _$DownloadCodePackageResponseFromJson(
  Map<String, dynamic> json,
) => DownloadCodePackageResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  info: json['info'] as String?,
  error: json['error'] as String?,
  authoritySourceUrl: json['authority_source_url'] as String?,
  selector: CodePackageRef.fromJson(json['selector'] as Map<String, dynamic>),
  artifactLock: CodePackageArtifactLock.fromJson(
    json['artifact_lock'] as Map<String, dynamic>,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DownloadCodePackageResponseToJson(
  DownloadCodePackageResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'info': instance.info,
  'error': instance.error,
  'authority_source_url': instance.authoritySourceUrl,
  'selector': instance.selector.toJson(),
  'artifact_lock': instance.artifactLock.toJson(),
  'operation': instance.$type,
};

PublishCodePackageResponse _$PublishCodePackageResponseFromJson(
  Map<String, dynamic> json,
) => PublishCodePackageResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  info: json['info'] as String?,
  error: json['error'] as String?,
  authoritySourceUrl: json['authority_source_url'] as String?,
  selector: json['selector'] == null
      ? null
      : CodePackageRef.fromJson(json['selector'] as Map<String, dynamic>),
  descriptor: json['descriptor'] == null
      ? null
      : CodePackageDescriptor.fromJson(
          json['descriptor'] as Map<String, dynamic>,
        ),
  artifactLock: json['artifact_lock'] == null
      ? null
      : CodePackageArtifactLock.fromJson(
          json['artifact_lock'] as Map<String, dynamic>,
        ),
  accepted: json['accepted'] as bool,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$PublishCodePackageResponseToJson(
  PublishCodePackageResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'info': instance.info,
  'error': instance.error,
  'authority_source_url': instance.authoritySourceUrl,
  'selector': instance.selector?.toJson(),
  'descriptor': instance.descriptor?.toJson(),
  'artifact_lock': instance.artifactLock?.toJson(),
  'accepted': instance.accepted,
  'operation': instance.$type,
};

_CodePackageRef _$CodePackageRefFromJson(Map<String, dynamic> json) =>
    _CodePackageRef(
      packageName: json['package_name'] as String,
      language: CodeLanguageExtension.fromJsonNullable(
        json['language'] as String?,
      ),
      surface: json['surface'] as String?,
      channel: json['channel'] as String,
      version: json['version'] as String?,
      revisionId: json['revision_id'] as String?,
      digest: json['digest'] as String?,
    );

Map<String, dynamic> _$CodePackageRefToJson(_CodePackageRef instance) =>
    <String, dynamic>{
      'package_name': instance.packageName,
      'language': CodeLanguageExtension.toJsonNullable(instance.language),
      'surface': instance.surface,
      'channel': instance.channel,
      'version': instance.version,
      'revision_id': instance.revisionId,
      'digest': instance.digest,
    };

_CodePackageArtifactLock _$CodePackageArtifactLockFromJson(
  Map<String, dynamic> json,
) => _CodePackageArtifactLock(
  artifactUrl: json['artifact_url'] as String,
  sha256: json['sha256'] as String,
  sizeBytes: (json['size_bytes'] as num?)?.toInt(),
  mediaType: json['media_type'] as String?,
  archiveFormat: json['archive_format'] as String?,
  revisionId: json['revision_id'] as String?,
  publishedAt: json['published_at'] as String?,
);

Map<String, dynamic> _$CodePackageArtifactLockToJson(
  _CodePackageArtifactLock instance,
) => <String, dynamic>{
  'artifact_url': instance.artifactUrl,
  'sha256': instance.sha256,
  'size_bytes': instance.sizeBytes,
  'media_type': instance.mediaType,
  'archive_format': instance.archiveFormat,
  'revision_id': instance.revisionId,
  'published_at': instance.publishedAt,
};

_CodePackageDescriptor _$CodePackageDescriptorFromJson(
  Map<String, dynamic> json,
) => _CodePackageDescriptor(
  packageName: json['package_name'] as String,
  language: CodeLanguageExtension.fromJson(json['language'] as String),
  surface: json['surface'] as String,
  manifestKind: json['manifest_kind'] as String,
  manifestRelativePath: json['manifest_relative_path'] as String,
  packageRoot: json['package_root'] as String,
  sourcesRoot: json['sources_root'] as String?,
  fqnPrefix: json['fqn_prefix'] as String?,
  version: json['version'] as String?,
  revisionId: json['revision_id'] as String?,
  digest: json['digest'] as String?,
  artifactMediaType: json['artifact_media_type'] as String?,
  artifactSizeBytes: (json['artifact_size_bytes'] as num?)?.toInt(),
  downloadHandle: json['download_handle'] as String?,
  metadata: json['metadata'] as Map<String, dynamic>,
);

Map<String, dynamic> _$CodePackageDescriptorToJson(
  _CodePackageDescriptor instance,
) => <String, dynamic>{
  'package_name': instance.packageName,
  'language': CodeLanguageExtension.toJson(instance.language),
  'surface': instance.surface,
  'manifest_kind': instance.manifestKind,
  'manifest_relative_path': instance.manifestRelativePath,
  'package_root': instance.packageRoot,
  'sources_root': instance.sourcesRoot,
  'fqn_prefix': instance.fqnPrefix,
  'version': instance.version,
  'revision_id': instance.revisionId,
  'digest': instance.digest,
  'artifact_media_type': instance.artifactMediaType,
  'artifact_size_bytes': instance.artifactSizeBytes,
  'download_handle': instance.downloadHandle,
  'metadata': instance.metadata,
};

_CodePackageChannelHead _$CodePackageChannelHeadFromJson(
  Map<String, dynamic> json,
) => _CodePackageChannelHead(
  packageName: json['package_name'] as String,
  language: CodeLanguageExtension.fromJsonNullable(json['language'] as String?),
  surface: json['surface'] as String?,
  channel: json['channel'] as String,
  revisionId: json['revision_id'] as String,
  updatedAt: json['updated_at'] as String?,
  publisherExecutionId: json['publisher_execution_id'] as String?,
  idempotencyKey: json['idempotency_key'] as String?,
  metadata: json['metadata'] as Map<String, dynamic>,
);

Map<String, dynamic> _$CodePackageChannelHeadToJson(
  _CodePackageChannelHead instance,
) => <String, dynamic>{
  'package_name': instance.packageName,
  'language': CodeLanguageExtension.toJsonNullable(instance.language),
  'surface': instance.surface,
  'channel': instance.channel,
  'revision_id': instance.revisionId,
  'updated_at': instance.updatedAt,
  'publisher_execution_id': instance.publisherExecutionId,
  'idempotency_key': instance.idempotencyKey,
  'metadata': instance.metadata,
};

_CodePackageDiscoveryEntry _$CodePackageDiscoveryEntryFromJson(
  Map<String, dynamic> json,
) => _CodePackageDiscoveryEntry(
  channelHead: CodePackageChannelHead.fromJson(
    json['channel_head'] as Map<String, dynamic>,
  ),
  descriptor: json['descriptor'] == null
      ? null
      : CodePackageDescriptor.fromJson(
          json['descriptor'] as Map<String, dynamic>,
        ),
  artifactLock: json['artifact_lock'] == null
      ? null
      : CodePackageArtifactLock.fromJson(
          json['artifact_lock'] as Map<String, dynamic>,
        ),
);

Map<String, dynamic> _$CodePackageDiscoveryEntryToJson(
  _CodePackageDiscoveryEntry instance,
) => <String, dynamic>{
  'channel_head': instance.channelHead.toJson(),
  'descriptor': instance.descriptor?.toJson(),
  'artifact_lock': instance.artifactLock?.toJson(),
};
