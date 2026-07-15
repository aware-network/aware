// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'content_service_operation_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_ContentTextPartV1 _$ContentTextPartV1FromJson(Map<String, dynamic> json) =>
    _ContentTextPartV1(
      contentPartContentId: _$JsonConverterFromJson<String, UuidValue>(
        json['content_part_content_id'],
        const UuidValueConverter().fromJson,
      ),
      contentPartId: _$JsonConverterFromJson<String, UuidValue>(
        json['content_part_id'],
        const UuidValueConverter().fromJson,
      ),
      contentPartTextId: _$JsonConverterFromJson<String, UuidValue>(
        json['content_part_text_id'],
        const UuidValueConverter().fromJson,
      ),
      position: (json['position'] as num).toInt(),
      partKey: json['part_key'] as String?,
      mediaType: json['media_type'] as String,
      text: json['text'] as String,
      digestAlgorithm: json['digest_algorithm'] as String,
      digest: json['digest'] as String?,
      sizeBytes: (json['size_bytes'] as num).toInt(),
      sourceKind: json['source_kind'] as String,
      provenance: json['provenance'] as Map<String, dynamic>,
    );

Map<String, dynamic> _$ContentTextPartV1ToJson(_ContentTextPartV1 instance) =>
    <String, dynamic>{
      'content_part_content_id': _$JsonConverterToJson<String, UuidValue>(
        instance.contentPartContentId,
        const UuidValueConverter().toJson,
      ),
      'content_part_id': _$JsonConverterToJson<String, UuidValue>(
        instance.contentPartId,
        const UuidValueConverter().toJson,
      ),
      'content_part_text_id': _$JsonConverterToJson<String, UuidValue>(
        instance.contentPartTextId,
        const UuidValueConverter().toJson,
      ),
      'position': instance.position,
      'part_key': instance.partKey,
      'media_type': instance.mediaType,
      'text': instance.text,
      'digest_algorithm': instance.digestAlgorithm,
      'digest': instance.digest,
      'size_bytes': instance.sizeBytes,
      'source_kind': instance.sourceKind,
      'provenance': instance.provenance,
    };

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);

_ContentTextResolutionV1 _$ContentTextResolutionV1FromJson(
  Map<String, dynamic> json,
) => _ContentTextResolutionV1(
  contentId: const UuidValueConverter().fromJson(json['content_id'] as String),
  contentKey: json['content_key'] as String?,
  title: json['title'] as String?,
  mediaType: json['media_type'] as String,
  text: json['text'] as String,
  parts:
      (json['parts'] as List<dynamic>?)
          ?.map((e) => ContentTextPartV1.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  digestAlgorithm: json['digest_algorithm'] as String,
  digest: json['digest'] as String?,
  sizeBytes: (json['size_bytes'] as num).toInt(),
  sourceKind: json['source_kind'] as String,
  provenance: json['provenance'] as Map<String, dynamic>,
);

Map<String, dynamic> _$ContentTextResolutionV1ToJson(
  _ContentTextResolutionV1 instance,
) => <String, dynamic>{
  'content_id': const UuidValueConverter().toJson(instance.contentId),
  'content_key': instance.contentKey,
  'title': instance.title,
  'media_type': instance.mediaType,
  'text': instance.text,
  'parts': instance.parts.map((e) => e.toJson()).toList(),
  'digest_algorithm': instance.digestAlgorithm,
  'digest': instance.digest,
  'size_bytes': instance.sizeBytes,
  'source_kind': instance.sourceKind,
  'provenance': instance.provenance,
};

_ContentTextCommitPartV1 _$ContentTextCommitPartV1FromJson(
  Map<String, dynamic> json,
) => _ContentTextCommitPartV1(
  position: (json['position'] as num).toInt(),
  partKey: json['part_key'] as String?,
  mediaType: json['media_type'] as String,
  text: json['text'] as String,
  digestAlgorithm: json['digest_algorithm'] as String,
  digest: json['digest'] as String?,
  sizeBytes: (json['size_bytes'] as num?)?.toInt(),
  provenance: json['provenance'] as Map<String, dynamic>,
);

Map<String, dynamic> _$ContentTextCommitPartV1ToJson(
  _ContentTextCommitPartV1 instance,
) => <String, dynamic>{
  'position': instance.position,
  'part_key': instance.partKey,
  'media_type': instance.mediaType,
  'text': instance.text,
  'digest_algorithm': instance.digestAlgorithm,
  'digest': instance.digest,
  'size_bytes': instance.sizeBytes,
  'provenance': instance.provenance,
};

_ContentTextCommitResultV1 _$ContentTextCommitResultV1FromJson(
  Map<String, dynamic> json,
) => _ContentTextCommitResultV1(
  contentId: const UuidValueConverter().fromJson(json['content_id'] as String),
  contentKey: json['content_key'] as String,
  title: json['title'] as String?,
  sourceKind: json['source_kind'] as String,
  sourceRef: json['source_ref'] as String,
  mediaType: json['media_type'] as String,
  digestAlgorithm: json['digest_algorithm'] as String,
  digest: json['digest'] as String,
  sizeBytes: (json['size_bytes'] as num).toInt(),
  domainCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['domain_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  serviceHostReceiptRef: json['service_host_receipt_ref'] as String?,
  provenance: json['provenance'] as Map<String, dynamic>,
);

Map<String, dynamic> _$ContentTextCommitResultV1ToJson(
  _ContentTextCommitResultV1 instance,
) => <String, dynamic>{
  'content_id': const UuidValueConverter().toJson(instance.contentId),
  'content_key': instance.contentKey,
  'title': instance.title,
  'source_kind': instance.sourceKind,
  'source_ref': instance.sourceRef,
  'media_type': instance.mediaType,
  'digest_algorithm': instance.digestAlgorithm,
  'digest': instance.digest,
  'size_bytes': instance.sizeBytes,
  'domain_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.domainCommitId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphCommitId,
    const UuidValueConverter().toJson,
  ),
  'service_host_receipt_ref': instance.serviceHostReceiptRef,
  'provenance': instance.provenance,
};

_ContentPackageExportPartV1 _$ContentPackageExportPartV1FromJson(
  Map<String, dynamic> json,
) => _ContentPackageExportPartV1(
  partKey: json['part_key'] as String,
  position: (json['position'] as num).toInt(),
  modalityType: json['modality_type'] as String,
  contentPartType: json['content_part_type'] as String,
  mediaType: json['media_type'] as String,
  text: json['text'] as String?,
  rawPath: json['raw_path'] as String?,
  uri: json['uri'] as String?,
  providerId: json['provider_id'] as String?,
  digestAlgorithm: json['digest_algorithm'] as String,
  digest: json['digest'] as String?,
  sizeBytes: (json['size_bytes'] as num?)?.toInt(),
  awareContentMapping: json['aware_content_mapping'] as Map<String, dynamic>,
  provenance: json['provenance'] as Map<String, dynamic>,
);

Map<String, dynamic> _$ContentPackageExportPartV1ToJson(
  _ContentPackageExportPartV1 instance,
) => <String, dynamic>{
  'part_key': instance.partKey,
  'position': instance.position,
  'modality_type': instance.modalityType,
  'content_part_type': instance.contentPartType,
  'media_type': instance.mediaType,
  'text': instance.text,
  'raw_path': instance.rawPath,
  'uri': instance.uri,
  'provider_id': instance.providerId,
  'digest_algorithm': instance.digestAlgorithm,
  'digest': instance.digest,
  'size_bytes': instance.sizeBytes,
  'aware_content_mapping': instance.awareContentMapping,
  'provenance': instance.provenance,
};

_ContentPackageArtifactProjectionV1
_$ContentPackageArtifactProjectionV1FromJson(Map<String, dynamic> json) =>
    _ContentPackageArtifactProjectionV1(
      outputKey: json['output_key'] as String,
      artifactKey: json['artifact_key'] as String,
      artifactFamily: json['artifact_family'] as String,
      artifactRole: json['artifact_role'] as String,
      requiredFor:
          (json['required_for'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      producerProviderKey: json['producer_provider_key'] as String,
      producerKey: json['producer_key'] as String,
      producerKind: json['producer_kind'] as String,
      materializationIndex: (json['materialization_index'] as num?)?.toInt(),
      relativePath: json['relative_path'] as String,
      uri: json['uri'] as String?,
      mediaType: json['media_type'] as String,
      digestAlgorithm: json['digest_algorithm'] as String,
      digest: json['digest'] as String?,
      sizeBytes: (json['size_bytes'] as num?)?.toInt(),
      runtimeContractVersion: json['runtime_contract_version'] as String,
      providerPayload: json['provider_payload'] as Map<String, dynamic>,
      receiptPayload: json['receipt_payload'] as Map<String, dynamic>,
    );

Map<String, dynamic> _$ContentPackageArtifactProjectionV1ToJson(
  _ContentPackageArtifactProjectionV1 instance,
) => <String, dynamic>{
  'output_key': instance.outputKey,
  'artifact_key': instance.artifactKey,
  'artifact_family': instance.artifactFamily,
  'artifact_role': instance.artifactRole,
  'required_for': instance.requiredFor,
  'producer_provider_key': instance.producerProviderKey,
  'producer_key': instance.producerKey,
  'producer_kind': instance.producerKind,
  'materialization_index': instance.materializationIndex,
  'relative_path': instance.relativePath,
  'uri': instance.uri,
  'media_type': instance.mediaType,
  'digest_algorithm': instance.digestAlgorithm,
  'digest': instance.digest,
  'size_bytes': instance.sizeBytes,
  'runtime_contract_version': instance.runtimeContractVersion,
  'provider_payload': instance.providerPayload,
  'receipt_payload': instance.receiptPayload,
};

_ContentPackageExportDocumentV1 _$ContentPackageExportDocumentV1FromJson(
  Map<String, dynamic> json,
) => _ContentPackageExportDocumentV1(
  exportKind: json['export_kind'] as String,
  contractVersion: json['contract_version'] as String,
  packageName: json['package_name'] as String,
  packageRoot: json['package_root'] as String?,
  manifestRelativePath: json['manifest_relative_path'] as String?,
  title: json['title'] as String?,
  packageKind: json['package_kind'] as String,
  sourceProviderKey: json['source_provider_key'] as String,
  sourceRef: json['source_ref'] as String,
  runtimeContractVersion: json['runtime_contract_version'] as String,
  contentKey: json['content_key'] as String?,
  contentTitle: json['content_title'] as String?,
  targetPath: json['target_path'] as String,
  mediaType: json['media_type'] as String,
  digestAlgorithm: json['digest_algorithm'] as String,
  digest: json['digest'] as String?,
  sizeBytes: (json['size_bytes'] as num?)?.toInt(),
  contentText: json['content_text'] as String?,
  parts:
      (json['parts'] as List<dynamic>?)
          ?.map(
            (e) =>
                ContentPackageExportPartV1.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  artifact: json['artifact'] == null
      ? null
      : ContentPackageArtifactProjectionV1.fromJson(
          json['artifact'] as Map<String, dynamic>,
        ),
  awareContentMapping: json['aware_content_mapping'] as Map<String, dynamic>,
  providerPayload: json['provider_payload'] as Map<String, dynamic>,
  provenance: json['provenance'] as Map<String, dynamic>,
);

Map<String, dynamic> _$ContentPackageExportDocumentV1ToJson(
  _ContentPackageExportDocumentV1 instance,
) => <String, dynamic>{
  'export_kind': instance.exportKind,
  'contract_version': instance.contractVersion,
  'package_name': instance.packageName,
  'package_root': instance.packageRoot,
  'manifest_relative_path': instance.manifestRelativePath,
  'title': instance.title,
  'package_kind': instance.packageKind,
  'source_provider_key': instance.sourceProviderKey,
  'source_ref': instance.sourceRef,
  'runtime_contract_version': instance.runtimeContractVersion,
  'content_key': instance.contentKey,
  'content_title': instance.contentTitle,
  'target_path': instance.targetPath,
  'media_type': instance.mediaType,
  'digest_algorithm': instance.digestAlgorithm,
  'digest': instance.digest,
  'size_bytes': instance.sizeBytes,
  'content_text': instance.contentText,
  'parts': instance.parts.map((e) => e.toJson()).toList(),
  'artifact': instance.artifact?.toJson(),
  'aware_content_mapping': instance.awareContentMapping,
  'provider_payload': instance.providerPayload,
  'provenance': instance.provenance,
};

_ContentPackageMaterializedArtifactRefV1
_$ContentPackageMaterializedArtifactRefV1FromJson(Map<String, dynamic> json) =>
    _ContentPackageMaterializedArtifactRefV1(
      contentPackageId: _$JsonConverterFromJson<String, UuidValue>(
        json['content_package_id'],
        const UuidValueConverter().fromJson,
      ),
      contentId: _$JsonConverterFromJson<String, UuidValue>(
        json['content_id'],
        const UuidValueConverter().fromJson,
      ),
      domainCommitId: _$JsonConverterFromJson<String, UuidValue>(
        json['domain_commit_id'],
        const UuidValueConverter().fromJson,
      ),
      objectInstanceGraphCommitId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_instance_graph_commit_id'],
        const UuidValueConverter().fromJson,
      ),
      serviceHostReceiptRef: json['service_host_receipt_ref'] as String?,
      outputKey: json['output_key'] as String,
      artifactKey: json['artifact_key'] as String,
      status: json['status'] as String,
      artifactFamily: json['artifact_family'] as String?,
      artifactRole: json['artifact_role'] as String?,
      requiredFor:
          (json['required_for'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      producerProviderKey: json['producer_provider_key'] as String?,
      producerKey: json['producer_key'] as String?,
      producerKind: json['producer_kind'] as String?,
      materializationIndex: (json['materialization_index'] as num?)?.toInt(),
      digestAlgorithm: json['digest_algorithm'] as String?,
      digest: json['digest'] as String?,
      relativePath: json['relative_path'] as String?,
      uri: json['uri'] as String?,
      mediaType: json['media_type'] as String?,
      sizeBytes: (json['size_bytes'] as num?)?.toInt(),
      runtimeContractVersion: json['runtime_contract_version'] as String?,
      providerPayload: json['provider_payload'] as Map<String, dynamic>,
      receiptPayload: json['receipt_payload'] as Map<String, dynamic>,
    );

Map<String, dynamic> _$ContentPackageMaterializedArtifactRefV1ToJson(
  _ContentPackageMaterializedArtifactRefV1 instance,
) => <String, dynamic>{
  'content_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.contentPackageId,
    const UuidValueConverter().toJson,
  ),
  'content_id': _$JsonConverterToJson<String, UuidValue>(
    instance.contentId,
    const UuidValueConverter().toJson,
  ),
  'domain_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.domainCommitId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphCommitId,
    const UuidValueConverter().toJson,
  ),
  'service_host_receipt_ref': instance.serviceHostReceiptRef,
  'output_key': instance.outputKey,
  'artifact_key': instance.artifactKey,
  'status': instance.status,
  'artifact_family': instance.artifactFamily,
  'artifact_role': instance.artifactRole,
  'required_for': instance.requiredFor,
  'producer_provider_key': instance.producerProviderKey,
  'producer_key': instance.producerKey,
  'producer_kind': instance.producerKind,
  'materialization_index': instance.materializationIndex,
  'digest_algorithm': instance.digestAlgorithm,
  'digest': instance.digest,
  'relative_path': instance.relativePath,
  'uri': instance.uri,
  'media_type': instance.mediaType,
  'size_bytes': instance.sizeBytes,
  'runtime_contract_version': instance.runtimeContractVersion,
  'provider_payload': instance.providerPayload,
  'receipt_payload': instance.receiptPayload,
};

_ContentPackageMaterializationResultV1
_$ContentPackageMaterializationResultV1FromJson(Map<String, dynamic> json) =>
    _ContentPackageMaterializationResultV1(
      contentPackageId: _$JsonConverterFromJson<String, UuidValue>(
        json['content_package_id'],
        const UuidValueConverter().fromJson,
      ),
      contentId: _$JsonConverterFromJson<String, UuidValue>(
        json['content_id'],
        const UuidValueConverter().fromJson,
      ),
      domainCommitId: _$JsonConverterFromJson<String, UuidValue>(
        json['domain_commit_id'],
        const UuidValueConverter().fromJson,
      ),
      objectInstanceGraphCommitId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_instance_graph_commit_id'],
        const UuidValueConverter().fromJson,
      ),
      serviceHostReceiptRef: json['service_host_receipt_ref'] as String?,
      packageName: json['package_name'] as String,
      contentKey: json['content_key'] as String?,
      sourceProviderKey: json['source_provider_key'] as String,
      sourceRef: json['source_ref'] as String,
      targetPath: json['target_path'] as String,
      mediaType: json['media_type'] as String,
      digestAlgorithm: json['digest_algorithm'] as String,
      digest: json['digest'] as String?,
      sizeBytes: (json['size_bytes'] as num?)?.toInt(),
      artifactRefs:
          (json['artifact_refs'] as List<dynamic>?)
              ?.map(
                (e) => ContentPackageMaterializedArtifactRefV1.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
      awareContentMapping:
          json['aware_content_mapping'] as Map<String, dynamic>,
      provenance: json['provenance'] as Map<String, dynamic>,
    );

Map<String, dynamic> _$ContentPackageMaterializationResultV1ToJson(
  _ContentPackageMaterializationResultV1 instance,
) => <String, dynamic>{
  'content_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.contentPackageId,
    const UuidValueConverter().toJson,
  ),
  'content_id': _$JsonConverterToJson<String, UuidValue>(
    instance.contentId,
    const UuidValueConverter().toJson,
  ),
  'domain_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.domainCommitId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphCommitId,
    const UuidValueConverter().toJson,
  ),
  'service_host_receipt_ref': instance.serviceHostReceiptRef,
  'package_name': instance.packageName,
  'content_key': instance.contentKey,
  'source_provider_key': instance.sourceProviderKey,
  'source_ref': instance.sourceRef,
  'target_path': instance.targetPath,
  'media_type': instance.mediaType,
  'digest_algorithm': instance.digestAlgorithm,
  'digest': instance.digest,
  'size_bytes': instance.sizeBytes,
  'artifact_refs': instance.artifactRefs.map((e) => e.toJson()).toList(),
  'aware_content_mapping': instance.awareContentMapping,
  'provenance': instance.provenance,
};

_ContentOperationReceipt _$ContentOperationReceiptFromJson(
  Map<String, dynamic> json,
) => _ContentOperationReceipt(
  operation: json['operation'] as String,
  status: json['status'] as String,
  contentId: _$JsonConverterFromJson<String, UuidValue>(
    json['content_id'],
    const UuidValueConverter().fromJson,
  ),
  contentPackageId: _$JsonConverterFromJson<String, UuidValue>(
    json['content_package_id'],
    const UuidValueConverter().fromJson,
  ),
  domainCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['domain_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  serviceHostReceiptRef: json['service_host_receipt_ref'] as String?,
  packageName: json['package_name'] as String?,
  digestAlgorithm: json['digest_algorithm'] as String,
  digest: json['digest'] as String?,
  sizeBytes: (json['size_bytes'] as num?)?.toInt(),
  backendKind: json['backend_kind'] as String,
  metadata: json['metadata'] as Map<String, dynamic>,
);

Map<String, dynamic> _$ContentOperationReceiptToJson(
  _ContentOperationReceipt instance,
) => <String, dynamic>{
  'operation': instance.operation,
  'status': instance.status,
  'content_id': _$JsonConverterToJson<String, UuidValue>(
    instance.contentId,
    const UuidValueConverter().toJson,
  ),
  'content_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.contentPackageId,
    const UuidValueConverter().toJson,
  ),
  'domain_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.domainCommitId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphCommitId,
    const UuidValueConverter().toJson,
  ),
  'service_host_receipt_ref': instance.serviceHostReceiptRef,
  'package_name': instance.packageName,
  'digest_algorithm': instance.digestAlgorithm,
  'digest': instance.digest,
  'size_bytes': instance.sizeBytes,
  'backend_kind': instance.backendKind,
  'metadata': instance.metadata,
};

ResolveContentTextRequest _$ResolveContentTextRequestFromJson(
  Map<String, dynamic> json,
) => ResolveContentTextRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  branchId: _$JsonConverterFromJson<String, UuidValue>(
    json['branch_id'],
    const UuidValueConverter().fromJson,
  ),
  contentId: _$JsonConverterFromJson<String, UuidValue>(
    json['content_id'],
    const UuidValueConverter().fromJson,
  ),
  contentClassInstanceIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['content_class_instance_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  contentClassConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['content_class_config_id'],
    const UuidValueConverter().fromJson,
  ),
  mediaType: json['media_type'] as String,
  includeParts: json['include_parts'] as bool,
  maxChars: (json['max_chars'] as num?)?.toInt(),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$ResolveContentTextRequestToJson(
  ResolveContentTextRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.branchId,
    const UuidValueConverter().toJson,
  ),
  'content_id': _$JsonConverterToJson<String, UuidValue>(
    instance.contentId,
    const UuidValueConverter().toJson,
  ),
  'content_class_instance_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.contentClassInstanceIdentityId,
        const UuidValueConverter().toJson,
      ),
  'content_class_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.contentClassConfigId,
    const UuidValueConverter().toJson,
  ),
  'media_type': instance.mediaType,
  'include_parts': instance.includeParts,
  'max_chars': instance.maxChars,
  'operation': instance.$type,
};

CommitContentTextRequest _$CommitContentTextRequestFromJson(
  Map<String, dynamic> json,
) => CommitContentTextRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  branchId: _$JsonConverterFromJson<String, UuidValue>(
    json['branch_id'],
    const UuidValueConverter().fromJson,
  ),
  contentKey: json['content_key'] as String,
  title: json['title'] as String?,
  sourceKind: json['source_kind'] as String,
  sourceRef: json['source_ref'] as String,
  mediaType: json['media_type'] as String,
  text: json['text'] as String?,
  parts:
      (json['parts'] as List<dynamic>?)
          ?.map(
            (e) => ContentTextCommitPartV1.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  digestAlgorithm: json['digest_algorithm'] as String,
  digest: json['digest'] as String?,
  sizeBytes: (json['size_bytes'] as num?)?.toInt(),
  provenance: json['provenance'] as Map<String, dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$CommitContentTextRequestToJson(
  CommitContentTextRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.branchId,
    const UuidValueConverter().toJson,
  ),
  'content_key': instance.contentKey,
  'title': instance.title,
  'source_kind': instance.sourceKind,
  'source_ref': instance.sourceRef,
  'media_type': instance.mediaType,
  'text': instance.text,
  'parts': instance.parts.map((e) => e.toJson()).toList(),
  'digest_algorithm': instance.digestAlgorithm,
  'digest': instance.digest,
  'size_bytes': instance.sizeBytes,
  'provenance': instance.provenance,
  'operation': instance.$type,
};

MaterializeContentPackageRequest _$MaterializeContentPackageRequestFromJson(
  Map<String, dynamic> json,
) => MaterializeContentPackageRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  branchId: _$JsonConverterFromJson<String, UuidValue>(
    json['branch_id'],
    const UuidValueConverter().fromJson,
  ),
  packageExport: ContentPackageExportDocumentV1.fromJson(
    json['package_export'] as Map<String, dynamic>,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$MaterializeContentPackageRequestToJson(
  MaterializeContentPackageRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.branchId,
    const UuidValueConverter().toJson,
  ),
  'package_export': instance.packageExport.toJson(),
  'operation': instance.$type,
};

ResolveContentTextResponse _$ResolveContentTextResponseFromJson(
  Map<String, dynamic> json,
) => ResolveContentTextResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  error: json['error'] as String?,
  receipt: json['receipt'] == null
      ? null
      : ContentOperationReceipt.fromJson(
          json['receipt'] as Map<String, dynamic>,
        ),
  resolution: json['resolution'] == null
      ? null
      : ContentTextResolutionV1.fromJson(
          json['resolution'] as Map<String, dynamic>,
        ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$ResolveContentTextResponseToJson(
  ResolveContentTextResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'error': instance.error,
  'receipt': instance.receipt?.toJson(),
  'resolution': instance.resolution?.toJson(),
  'operation': instance.$type,
};

CommitContentTextResponse _$CommitContentTextResponseFromJson(
  Map<String, dynamic> json,
) => CommitContentTextResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  error: json['error'] as String?,
  receipt: json['receipt'] == null
      ? null
      : ContentOperationReceipt.fromJson(
          json['receipt'] as Map<String, dynamic>,
        ),
  commitResult: json['commit_result'] == null
      ? null
      : ContentTextCommitResultV1.fromJson(
          json['commit_result'] as Map<String, dynamic>,
        ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$CommitContentTextResponseToJson(
  CommitContentTextResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'error': instance.error,
  'receipt': instance.receipt?.toJson(),
  'commit_result': instance.commitResult?.toJson(),
  'operation': instance.$type,
};

MaterializeContentPackageResponse _$MaterializeContentPackageResponseFromJson(
  Map<String, dynamic> json,
) => MaterializeContentPackageResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  error: json['error'] as String?,
  receipt: json['receipt'] == null
      ? null
      : ContentOperationReceipt.fromJson(
          json['receipt'] as Map<String, dynamic>,
        ),
  materialization: json['materialization'] == null
      ? null
      : ContentPackageMaterializationResultV1.fromJson(
          json['materialization'] as Map<String, dynamic>,
        ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$MaterializeContentPackageResponseToJson(
  MaterializeContentPackageResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'error': instance.error,
  'receipt': instance.receipt?.toJson(),
  'materialization': instance.materialization?.toJson(),
  'operation': instance.$type,
};
