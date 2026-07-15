// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:freezed_annotation/freezed_annotation.dart';

part 'channel_heads_model.freezed.dart';
part 'channel_heads_model.g.dart';

/// View-state contract for public Hub package channel-head discovery.
/// Public API view key: hub.channel_heads
@freezed
abstract class HubPublicDiscoveryDescriptorV1
    with _$HubPublicDiscoveryDescriptorV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory HubPublicDiscoveryDescriptorV1.def({
    String? packageName,
    String? language,
    String? surface,
    String? manifestKind,
    String? version,
    String? revisionId,
    String? digest,
    String? packageRoot,
    String? sourcesRoot,
    String? fqnPrefix,
    String? manifestRelativePath,
    String? artifactMediaType,
    int? artifactSizeBytes,
    String? downloadHandle,
    required Map<String, dynamic> metadata,
  }) = _HubPublicDiscoveryDescriptorV1;

  factory HubPublicDiscoveryDescriptorV1({
    String? packageName,
    String? language,
    String? surface,
    String? manifestKind,
    String? version,
    String? revisionId,
    String? digest,
    String? packageRoot,
    String? sourcesRoot,
    String? fqnPrefix,
    String? manifestRelativePath,
    String? artifactMediaType,
    int? artifactSizeBytes,
    String? downloadHandle,
    Map<String, dynamic>? metadata,
  }) {
    return _HubPublicDiscoveryDescriptorV1(
      packageName: packageName,
      language: language,
      surface: surface,
      manifestKind: manifestKind,
      version: version,
      revisionId: revisionId,
      digest: digest,
      packageRoot: packageRoot,
      sourcesRoot: sourcesRoot,
      fqnPrefix: fqnPrefix,
      manifestRelativePath: manifestRelativePath,
      artifactMediaType: artifactMediaType,
      artifactSizeBytes: artifactSizeBytes,
      downloadHandle: downloadHandle,
      metadata: metadata ?? {},
    );
  }

  factory HubPublicDiscoveryDescriptorV1.fromJson(Map<String, dynamic> json) =>
      _$HubPublicDiscoveryDescriptorV1FromJson({
        ...json,
        if (!json.containsKey('metadata')) 'metadata': {},
      });
}

@freezed
abstract class HubPublicDiscoveryArtifactLockV1
    with _$HubPublicDiscoveryArtifactLockV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory HubPublicDiscoveryArtifactLockV1.def({
    String? artifactUrl,
    String? sha256,
    int? sizeBytes,
    String? mediaType,
    String? archiveFormat,
    String? revisionId,
    String? publishedAt,
  }) = _HubPublicDiscoveryArtifactLockV1;

  factory HubPublicDiscoveryArtifactLockV1({
    String? artifactUrl,
    String? sha256,
    int? sizeBytes,
    String? mediaType,
    String? archiveFormat,
    String? revisionId,
    String? publishedAt,
  }) {
    return _HubPublicDiscoveryArtifactLockV1(
      artifactUrl: artifactUrl,
      sha256: sha256,
      sizeBytes: sizeBytes,
      mediaType: mediaType,
      archiveFormat: archiveFormat,
      revisionId: revisionId,
      publishedAt: publishedAt,
    );
  }

  factory HubPublicDiscoveryArtifactLockV1.fromJson(
    Map<String, dynamic> json,
  ) => _$HubPublicDiscoveryArtifactLockV1FromJson(json);
}

@freezed
abstract class HubPublicDiscoveryEntryV1 with _$HubPublicDiscoveryEntryV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory HubPublicDiscoveryEntryV1.def({
    String? packageName,
    String? language,
    String? surface,
    required String channel,
    String? revisionId,
    String? updatedAt,
    String? publisherExecutionId,
    String? idempotencyKey,
    required Map<String, dynamic> metadata,
    HubPublicDiscoveryDescriptorV1? descriptor,
    HubPublicDiscoveryArtifactLockV1? artifactLock,
    required Map<String, dynamic> refs,
  }) = _HubPublicDiscoveryEntryV1;

  factory HubPublicDiscoveryEntryV1({
    String? packageName,
    String? language,
    String? surface,
    String? channel,
    String? revisionId,
    String? updatedAt,
    String? publisherExecutionId,
    String? idempotencyKey,
    Map<String, dynamic>? metadata,
    HubPublicDiscoveryDescriptorV1? descriptor,
    HubPublicDiscoveryArtifactLockV1? artifactLock,
    Map<String, dynamic>? refs,
  }) {
    return _HubPublicDiscoveryEntryV1(
      packageName: packageName,
      language: language,
      surface: surface,
      channel: channel ?? 'stable',
      revisionId: revisionId,
      updatedAt: updatedAt,
      publisherExecutionId: publisherExecutionId,
      idempotencyKey: idempotencyKey,
      metadata: metadata ?? {},
      descriptor: descriptor,
      artifactLock: artifactLock,
      refs: refs ?? {},
    );
  }

  factory HubPublicDiscoveryEntryV1.fromJson(Map<String, dynamic> json) =>
      _$HubPublicDiscoveryEntryV1FromJson({
        ...json,
        if (!json.containsKey('channel')) 'channel': 'stable',
        if (!json.containsKey('metadata')) 'metadata': {},
        if (!json.containsKey('refs')) 'refs': {},
      });
}

@freezed
abstract class HubPublicDiscoveryViewStateV1
    with _$HubPublicDiscoveryViewStateV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory HubPublicDiscoveryViewStateV1.def({
    required String status,
    String? authoritySourceUrl,
    String? query,
    String? packageName,
    String? language,
    String? surface,
    String? channel,
    required int limit,
    @Default(const []) List<HubPublicDiscoveryEntryV1> entries,
    String? summary,
    required String emptyMessage,
    String? error,
    required Map<String, dynamic> provenance,
  }) = _HubPublicDiscoveryViewStateV1;

  factory HubPublicDiscoveryViewStateV1({
    String? status,
    String? authoritySourceUrl,
    String? query,
    String? packageName,
    String? language,
    String? surface,
    String? channel,
    int? limit,
    List<HubPublicDiscoveryEntryV1> entries = const [],
    String? summary,
    String? emptyMessage,
    String? error,
    Map<String, dynamic>? provenance,
  }) {
    return _HubPublicDiscoveryViewStateV1(
      status: status ?? 'waiting',
      authoritySourceUrl: authoritySourceUrl,
      query: query,
      packageName: packageName,
      language: language,
      surface: surface,
      channel: channel,
      limit: limit ?? 50,
      entries: entries,
      summary: summary,
      emptyMessage: emptyMessage ?? 'No public Hub packages published yet',
      error: error,
      provenance: provenance ?? {},
    );
  }

  factory HubPublicDiscoveryViewStateV1.fromJson(Map<String, dynamic> json) =>
      _$HubPublicDiscoveryViewStateV1FromJson({
        ...json,
        if (!json.containsKey('status')) 'status': 'waiting',
        if (!json.containsKey('limit')) 'limit': 50,
        if (!json.containsKey('empty_message'))
          'empty_message': 'No public Hub packages published yet',
        if (!json.containsKey('provenance')) 'provenance': {},
      });
}
