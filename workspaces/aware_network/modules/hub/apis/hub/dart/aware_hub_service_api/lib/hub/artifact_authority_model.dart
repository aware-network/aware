// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'artifact_authority_model.freezed.dart';
part 'artifact_authority_model.g.dart';

/// Hub-owned generic artifact authority DTOs.
/// Contract:
/// - Hub owns artifact family/key/channel/revision authority.
/// - Producers may provide payload bytes, payload JSON, a staged payload URL, or
/// a pre-published payload lock.
/// - Producer provenance remains descriptive; Hub artifact revisions own the
/// immutable payload lock and channel head.
@Freezed(unionKey: 'operation')
abstract class HubArtifactAuthorityRequest with _$HubArtifactAuthorityRequest {
  @FreezedUnionValue('publish_hub_artifact')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory HubArtifactAuthorityRequest.publishHubArtifact({
    @UuidValueConverter() UuidValue? requestId,
    required String artifactFamily,
    required String artifactKey,
    required String revisionId,
    required String channel,
    String? authorityBaseUrl,
    String? indexUrl,
    String? payloadUrl,
    String? payloadSha256,
    int? payloadSizeBytes,
    String? payloadMediaType,
    String? payloadContract,
    Map<String, dynamic>? payloadJson,
    String? payloadBytesBase64,
    String? payloadSourceUrl,
    String? selectorKey,
    String? targetRef,
    HubArtifactProducerProvenance? producer,
    String? publisherExecutionId,
    String? idempotencyKey,
    String? publishedAtUtc,
    required Map<String, dynamic> metadata,
  }) = PublishHubArtifactRequest;

  @FreezedUnionValue('resolve_hub_artifact')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory HubArtifactAuthorityRequest.resolveHubArtifact({
    @UuidValueConverter() UuidValue? requestId,
    required String artifactFamily,
    required String artifactKey,
    required String channel,
    String? revisionId,
    String? authorityBaseUrl,
    String? indexUrl,
  }) = ResolveHubArtifactRequest;

  factory HubArtifactAuthorityRequest.fromJson(Map<String, dynamic> json) =>
      _$HubArtifactAuthorityRequestFromJson(json);
}

@Freezed(unionKey: 'operation')
abstract class HubArtifactAuthorityResponse
    with _$HubArtifactAuthorityResponse {
  @FreezedUnionValue('publish_hub_artifact')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory HubArtifactAuthorityResponse.publishHubArtifact({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? info,
    String? error,
    required bool accepted,
    required String authoritySourceUrl,
    required HubArtifactPayloadLock artifactLock,
    HubArtifactProducerProvenance? producer,
  }) = PublishHubArtifactResponse;

  @FreezedUnionValue('resolve_hub_artifact')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory HubArtifactAuthorityResponse.resolveHubArtifact({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? info,
    String? error,
    required String authoritySourceUrl,
    required HubArtifactPayloadLock artifactLock,
    HubArtifactProducerProvenance? producer,
  }) = ResolveHubArtifactResponse;

  factory HubArtifactAuthorityResponse.fromJson(Map<String, dynamic> json) =>
      _$HubArtifactAuthorityResponseFromJson(json);
}

@freezed
abstract class HubArtifactProducerProvenance
    with _$HubArtifactProducerProvenance {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory HubArtifactProducerProvenance.def({
    required String producerKind,
    required String producerKey,
    String? provenanceKey,
    String? producerRevisionId,
    String? sourceRevisionId,
    String? sourceRevisionKind,
    String? materializationRef,
    String? buildRef,
    required Map<String, dynamic> metadata,
  }) = _HubArtifactProducerProvenance;

  factory HubArtifactProducerProvenance({
    String? producerKind,
    String? producerKey,
    String? provenanceKey,
    String? producerRevisionId,
    String? sourceRevisionId,
    String? sourceRevisionKind,
    String? materializationRef,
    String? buildRef,
    Map<String, dynamic>? metadata,
  }) {
    return _HubArtifactProducerProvenance(
      producerKind: producerKind ?? 'unknown',
      producerKey: producerKey ?? 'default',
      provenanceKey: provenanceKey,
      producerRevisionId: producerRevisionId,
      sourceRevisionId: sourceRevisionId,
      sourceRevisionKind: sourceRevisionKind,
      materializationRef: materializationRef,
      buildRef: buildRef,
      metadata: metadata ?? {},
    );
  }

  factory HubArtifactProducerProvenance.fromJson(Map<String, dynamic> json) =>
      _$HubArtifactProducerProvenanceFromJson({
        ...json,
        if (!json.containsKey('producer_kind')) 'producer_kind': 'unknown',
        if (!json.containsKey('producer_key')) 'producer_key': 'default',
        if (!json.containsKey('metadata')) 'metadata': {},
      });
}

@freezed
abstract class HubArtifactPayloadLock with _$HubArtifactPayloadLock {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory HubArtifactPayloadLock.def({
    required String artifactFamily,
    required String artifactKey,
    required String channel,
    required String revisionId,
    required String payloadUrl,
    required String payloadSha256,
    int? payloadSizeBytes,
    String? payloadMediaType,
    String? payloadContract,
    String? authoritySourceUrl,
    String? selectorKey,
    String? targetRef,
    required Map<String, dynamic> metadata,
  }) = _HubArtifactPayloadLock;

  factory HubArtifactPayloadLock({
    required String artifactFamily,
    required String artifactKey,
    String? channel,
    required String revisionId,
    required String payloadUrl,
    required String payloadSha256,
    int? payloadSizeBytes,
    String? payloadMediaType,
    String? payloadContract,
    String? authoritySourceUrl,
    String? selectorKey,
    String? targetRef,
    Map<String, dynamic>? metadata,
  }) {
    return _HubArtifactPayloadLock(
      artifactFamily: artifactFamily,
      artifactKey: artifactKey,
      channel: channel ?? 'stable',
      revisionId: revisionId,
      payloadUrl: payloadUrl,
      payloadSha256: payloadSha256,
      payloadSizeBytes: payloadSizeBytes,
      payloadMediaType: payloadMediaType,
      payloadContract: payloadContract,
      authoritySourceUrl: authoritySourceUrl,
      selectorKey: selectorKey,
      targetRef: targetRef,
      metadata: metadata ?? {},
    );
  }

  factory HubArtifactPayloadLock.fromJson(Map<String, dynamic> json) =>
      _$HubArtifactPayloadLockFromJson({
        ...json,
        if (!json.containsKey('channel')) 'channel': 'stable',
        if (!json.containsKey('metadata')) 'metadata': {},
      });
}
