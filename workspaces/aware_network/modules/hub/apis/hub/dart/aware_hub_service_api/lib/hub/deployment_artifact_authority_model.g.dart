// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'deployment_artifact_authority_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ResolveDeploymentArtifactRequest _$ResolveDeploymentArtifactRequestFromJson(
  Map<String, dynamic> json,
) => ResolveDeploymentArtifactRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  artifactFamily: json['artifact_family'] as String,
  artifactKey: json['artifact_key'] as String?,
  channel: json['channel'] as String,
  revisionId: json['revision_id'] as String?,
  authorityBaseUrl: json['authority_base_url'] as String?,
  indexUrl: json['index_url'] as String?,
);

Map<String, dynamic> _$ResolveDeploymentArtifactRequestToJson(
  ResolveDeploymentArtifactRequest instance,
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
};

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);

ResolveDeploymentArtifactResponse _$ResolveDeploymentArtifactResponseFromJson(
  Map<String, dynamic> json,
) => ResolveDeploymentArtifactResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  info: json['info'] as String?,
  error: json['error'] as String?,
  authoritySourceUrl: json['authority_source_url'] as String,
  artifactFamily: json['artifact_family'] as String,
  artifactKey: json['artifact_key'] as String,
  channel: json['channel'] as String,
  revisionId: json['revision_id'] as String,
  payloadUrl: json['payload_url'] as String,
  payloadSha256: json['payload_sha256'] as String,
  selectorKey: json['selector_key'] as String,
  targetRef: json['target_ref'] as String,
  producer: DeploymentArtifactProducerProvenance.fromJson(
    json['producer'] as Map<String, dynamic>,
  ),
  nodePackageName: json['node_package_name'] as String,
  artifactLock: DeploymentArtifactLock.fromJson(
    json['artifact_lock'] as Map<String, dynamic>,
  ),
  target: DeploymentArtifactTarget.fromJson(
    json['target'] as Map<String, dynamic>,
  ),
);

Map<String, dynamic> _$ResolveDeploymentArtifactResponseToJson(
  ResolveDeploymentArtifactResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'info': instance.info,
  'error': instance.error,
  'authority_source_url': instance.authoritySourceUrl,
  'artifact_family': instance.artifactFamily,
  'artifact_key': instance.artifactKey,
  'channel': instance.channel,
  'revision_id': instance.revisionId,
  'payload_url': instance.payloadUrl,
  'payload_sha256': instance.payloadSha256,
  'selector_key': instance.selectorKey,
  'target_ref': instance.targetRef,
  'producer': instance.producer.toJson(),
  'node_package_name': instance.nodePackageName,
  'artifact_lock': instance.artifactLock.toJson(),
  'target': instance.target.toJson(),
};

_DeploymentArtifactProducerProvenance
_$DeploymentArtifactProducerProvenanceFromJson(Map<String, dynamic> json) =>
    _DeploymentArtifactProducerProvenance(
      producerKind: json['producer_kind'] as String,
      producerRevisionId: json['producer_revision_id'] as String?,
      sourceRevisionId: json['source_revision_id'] as String?,
      sourceRevisionKind: json['source_revision_kind'] as String?,
      materializationRef: json['materialization_ref'] as String?,
      buildRef: json['build_ref'] as String?,
    );

Map<String, dynamic> _$DeploymentArtifactProducerProvenanceToJson(
  _DeploymentArtifactProducerProvenance instance,
) => <String, dynamic>{
  'producer_kind': instance.producerKind,
  'producer_revision_id': instance.producerRevisionId,
  'source_revision_id': instance.sourceRevisionId,
  'source_revision_kind': instance.sourceRevisionKind,
  'materialization_ref': instance.materializationRef,
  'build_ref': instance.buildRef,
};

_DeploymentArtifactLock _$DeploymentArtifactLockFromJson(
  Map<String, dynamic> json,
) => _DeploymentArtifactLock(
  artifactFamily: json['artifact_family'] as String,
  artifactKey: json['artifact_key'] as String,
  channel: json['channel'] as String,
  revisionId: json['revision_id'] as String,
  payloadUrl: json['payload_url'] as String,
  payloadSha256: json['payload_sha256'] as String,
  payloadContractVersion: json['payload_contract_version'] as String,
);

Map<String, dynamic> _$DeploymentArtifactLockToJson(
  _DeploymentArtifactLock instance,
) => <String, dynamic>{
  'artifact_family': instance.artifactFamily,
  'artifact_key': instance.artifactKey,
  'channel': instance.channel,
  'revision_id': instance.revisionId,
  'payload_url': instance.payloadUrl,
  'payload_sha256': instance.payloadSha256,
  'payload_contract_version': instance.payloadContractVersion,
};

_DeploymentArtifactTarget _$DeploymentArtifactTargetFromJson(
  Map<String, dynamic> json,
) => _DeploymentArtifactTarget(
  selectorKey: json['selector_key'] as String,
  targetRef: json['target_ref'] as String,
  nodePackageName: json['node_package_name'] as String,
);

Map<String, dynamic> _$DeploymentArtifactTargetToJson(
  _DeploymentArtifactTarget instance,
) => <String, dynamic>{
  'selector_key': instance.selectorKey,
  'target_ref': instance.targetRef,
  'node_package_name': instance.nodePackageName,
};
