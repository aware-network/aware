// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'deployment_artifact_authority_model.freezed.dart';
part 'deployment_artifact_authority_model.g.dart';

/// Hub-owned deployment artifact authority DTOs.
/// Contract:
/// - Hub owns the public deployment authority request/response model.
/// - Producers such as Workspace map their revision truth into generic
/// producer provenance.
/// - Hub resolves deployment artifact payload locks; it does not resolve
/// WorkspaceRevision semantics.
@Freezed(unionKey: 'operation')
abstract class DeploymentArtifactAuthorityRequest
    with _$DeploymentArtifactAuthorityRequest {
  @FreezedUnionValue('resolve_deployment_artifact')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory DeploymentArtifactAuthorityRequest.resolveDeploymentArtifact({
    @UuidValueConverter() UuidValue? requestId,
    required String artifactFamily,
    String? artifactKey,
    required String channel,
    String? revisionId,
    String? authorityBaseUrl,
    String? indexUrl,
  }) = ResolveDeploymentArtifactRequest;

  factory DeploymentArtifactAuthorityRequest.fromJson(
    Map<String, dynamic> json,
  ) => _$DeploymentArtifactAuthorityRequestFromJson(json);
}

@Freezed(unionKey: 'operation')
abstract class DeploymentArtifactAuthorityResponse
    with _$DeploymentArtifactAuthorityResponse {
  @FreezedUnionValue('resolve_deployment_artifact')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory DeploymentArtifactAuthorityResponse.resolveDeploymentArtifact({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? info,
    String? error,
    required String authoritySourceUrl,
    required String artifactFamily,
    required String artifactKey,
    required String channel,
    required String revisionId,
    required String payloadUrl,
    required String payloadSha256,
    required String selectorKey,
    required String targetRef,
    required DeploymentArtifactProducerProvenance producer,
    required String nodePackageName,
    required DeploymentArtifactLock artifactLock,
    required DeploymentArtifactTarget target,
  }) = ResolveDeploymentArtifactResponse;

  factory DeploymentArtifactAuthorityResponse.fromJson(
    Map<String, dynamic> json,
  ) => _$DeploymentArtifactAuthorityResponseFromJson(json);
}

@freezed
abstract class DeploymentArtifactProducerProvenance
    with _$DeploymentArtifactProducerProvenance {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory DeploymentArtifactProducerProvenance.def({
    required String producerKind,
    String? producerRevisionId,
    String? sourceRevisionId,
    String? sourceRevisionKind,
    String? materializationRef,
    String? buildRef,
  }) = _DeploymentArtifactProducerProvenance;

  factory DeploymentArtifactProducerProvenance({
    required String producerKind,
    String? producerRevisionId,
    String? sourceRevisionId,
    String? sourceRevisionKind,
    String? materializationRef,
    String? buildRef,
  }) {
    return _DeploymentArtifactProducerProvenance(
      producerKind: producerKind,
      producerRevisionId: producerRevisionId,
      sourceRevisionId: sourceRevisionId,
      sourceRevisionKind: sourceRevisionKind,
      materializationRef: materializationRef,
      buildRef: buildRef,
    );
  }

  factory DeploymentArtifactProducerProvenance.fromJson(
    Map<String, dynamic> json,
  ) => _$DeploymentArtifactProducerProvenanceFromJson(json);
}

@freezed
abstract class DeploymentArtifactLock with _$DeploymentArtifactLock {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory DeploymentArtifactLock.def({
    required String artifactFamily,
    required String artifactKey,
    required String channel,
    required String revisionId,
    required String payloadUrl,
    required String payloadSha256,
    required String payloadContractVersion,
  }) = _DeploymentArtifactLock;

  factory DeploymentArtifactLock({
    String? artifactFamily,
    required String artifactKey,
    String? channel,
    required String revisionId,
    required String payloadUrl,
    required String payloadSha256,
    String? payloadContractVersion,
  }) {
    return _DeploymentArtifactLock(
      artifactFamily: artifactFamily ?? 'workspace-deployment',
      artifactKey: artifactKey,
      channel: channel ?? 'stable',
      revisionId: revisionId,
      payloadUrl: payloadUrl,
      payloadSha256: payloadSha256,
      payloadContractVersion:
          payloadContractVersion ?? 'aware.workspace_deployment.payload.v1',
    );
  }

  factory DeploymentArtifactLock.fromJson(Map<String, dynamic> json) =>
      _$DeploymentArtifactLockFromJson({
        ...json,
        if (!json.containsKey('artifact_family'))
          'artifact_family': 'workspace-deployment',
        if (!json.containsKey('channel')) 'channel': 'stable',
        if (!json.containsKey('payload_contract_version'))
          'payload_contract_version': 'aware.workspace_deployment.payload.v1',
      });
}

@freezed
abstract class DeploymentArtifactTarget with _$DeploymentArtifactTarget {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory DeploymentArtifactTarget.def({
    required String selectorKey,
    required String targetRef,
    required String nodePackageName,
  }) = _DeploymentArtifactTarget;

  factory DeploymentArtifactTarget({
    required String selectorKey,
    required String targetRef,
    required String nodePackageName,
  }) {
    return _DeploymentArtifactTarget(
      selectorKey: selectorKey,
      targetRef: targetRef,
      nodePackageName: nodePackageName,
    );
  }

  factory DeploymentArtifactTarget.fromJson(Map<String, dynamic> json) =>
      _$DeploymentArtifactTargetFromJson(json);
}
