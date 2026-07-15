// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'public_map_discovery_model.freezed.dart';
part 'public_map_discovery_model.g.dart';

/// Hub public map discovery DTOs.
/// Contract:
/// - Hub owns public package/revision map discovery before identity admission.
/// - Entries describe distribution/readiness truth only; they do not activate
/// runtime, resolve Experience semantics, price access, or mutate Interface.
/// - Initial service implementation may lower existing CodePackage authority
/// entries into this shape while later Hub producers publish richer artifact
/// families such as experience-package, workspace-revision, and kernel-revision.
@Freezed(unionKey: 'operation')
abstract class PublicMapDiscoveryRequest with _$PublicMapDiscoveryRequest {
  @FreezedUnionValue('discover_public_map')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory PublicMapDiscoveryRequest.discoverPublicMap({
    @UuidValueConverter() UuidValue? requestId,
    String? query,
    String? artifactFamily,
    String? artifactKey,
    String? packageName,
    String? experienceName,
    String? channel,
    String? authorityBaseUrl,
    String? indexUrl,
    required int limit,
  }) = DiscoverPublicMapRequest;

  factory PublicMapDiscoveryRequest.fromJson(Map<String, dynamic> json) =>
      _$PublicMapDiscoveryRequestFromJson(json);
}

@Freezed(unionKey: 'operation')
abstract class PublicMapDiscoveryResponse with _$PublicMapDiscoveryResponse {
  @FreezedUnionValue('discover_public_map')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory PublicMapDiscoveryResponse.discoverPublicMap({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? info,
    String? error,
    String? authoritySourceUrl,
    @Default(const []) List<HubPublicMapEntry> entries,
  }) = DiscoverPublicMapResponse;

  factory PublicMapDiscoveryResponse.fromJson(Map<String, dynamic> json) =>
      _$PublicMapDiscoveryResponseFromJson(json);
}

@freezed
abstract class HubPublicMapEntry with _$HubPublicMapEntry {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory HubPublicMapEntry.def({
    required String artifactFamily,
    required String artifactKey,
    required String channel,
    String? revisionId,
    String? packageName,
    String? language,
    String? surface,
    String? manifestKind,
    String? digest,
    String? artifactUrl,
    String? artifactSha256,
    int? artifactSizeBytes,
    String? mediaType,
    String? title,
    String? summary,
    String? experienceName,
    String? fqnPrefix,
    String? producerKind,
    String? producerRevisionId,
    String? sourceRevisionId,
    required String visibility,
    required Map<String, dynamic> metadata,
  }) = _HubPublicMapEntry;

  factory HubPublicMapEntry({
    required String artifactFamily,
    required String artifactKey,
    String? channel,
    String? revisionId,
    String? packageName,
    String? language,
    String? surface,
    String? manifestKind,
    String? digest,
    String? artifactUrl,
    String? artifactSha256,
    int? artifactSizeBytes,
    String? mediaType,
    String? title,
    String? summary,
    String? experienceName,
    String? fqnPrefix,
    String? producerKind,
    String? producerRevisionId,
    String? sourceRevisionId,
    String? visibility,
    Map<String, dynamic>? metadata,
  }) {
    return _HubPublicMapEntry(
      artifactFamily: artifactFamily,
      artifactKey: artifactKey,
      channel: channel ?? 'stable',
      revisionId: revisionId,
      packageName: packageName,
      language: language,
      surface: surface,
      manifestKind: manifestKind,
      digest: digest,
      artifactUrl: artifactUrl,
      artifactSha256: artifactSha256,
      artifactSizeBytes: artifactSizeBytes,
      mediaType: mediaType,
      title: title,
      summary: summary,
      experienceName: experienceName,
      fqnPrefix: fqnPrefix,
      producerKind: producerKind,
      producerRevisionId: producerRevisionId,
      sourceRevisionId: sourceRevisionId,
      visibility: visibility ?? 'public',
      metadata: metadata ?? {},
    );
  }

  factory HubPublicMapEntry.fromJson(Map<String, dynamic> json) =>
      _$HubPublicMapEntryFromJson({
        ...json,
        if (!json.containsKey('channel')) 'channel': 'stable',
        if (!json.containsKey('visibility')) 'visibility': 'public',
        if (!json.containsKey('metadata')) 'metadata': {},
      });
}
