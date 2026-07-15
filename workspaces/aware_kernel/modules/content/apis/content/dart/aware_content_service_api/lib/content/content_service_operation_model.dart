// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'content_service_operation_model.freezed.dart';
part 'content_service_operation_model.g.dart';

/// Content service operation DTOs.
/// Contract:
/// - Content API is a read/render, text commit, and package materialization boundary over
/// Content ontology truth.
/// - DTOs carry Content ids and Experience-safe reference ids, not Social,
/// provider, or workspace-specific payloads.
/// - Blob-backed text fails closed unless the concrete service has an explicit
/// blob store path.
@freezed
abstract class ContentTextPartV1 with _$ContentTextPartV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ContentTextPartV1.def({
    @UuidValueConverter() UuidValue? contentPartContentId,
    @UuidValueConverter() UuidValue? contentPartId,
    @UuidValueConverter() UuidValue? contentPartTextId,
    required int position,
    String? partKey,
    required String mediaType,
    required String text,
    required String digestAlgorithm,
    String? digest,
    required int sizeBytes,
    required String sourceKind,
    required Map<String, dynamic> provenance,
  }) = _ContentTextPartV1;

  factory ContentTextPartV1({
    UuidValue? contentPartContentId,
    UuidValue? contentPartId,
    UuidValue? contentPartTextId,
    int? position,
    String? partKey,
    String? mediaType,
    String? text,
    String? digestAlgorithm,
    String? digest,
    int? sizeBytes,
    String? sourceKind,
    Map<String, dynamic>? provenance,
  }) {
    return _ContentTextPartV1(
      contentPartContentId: contentPartContentId,
      contentPartId: contentPartId,
      contentPartTextId: contentPartTextId,
      position: position ?? 0,
      partKey: partKey,
      mediaType: mediaType ?? 'text/plain',
      text: text ?? '',
      digestAlgorithm: digestAlgorithm ?? 'sha256',
      digest: digest,
      sizeBytes: sizeBytes ?? 0,
      sourceKind: sourceKind ?? 'inline_text',
      provenance: provenance ?? {},
    );
  }

  factory ContentTextPartV1.fromJson(Map<String, dynamic> json) =>
      _$ContentTextPartV1FromJson({
        ...json,
        if (!json.containsKey('position')) 'position': 0,
        if (!json.containsKey('media_type')) 'media_type': 'text/plain',
        if (!json.containsKey('text')) 'text': '',
        if (!json.containsKey('digest_algorithm')) 'digest_algorithm': 'sha256',
        if (!json.containsKey('size_bytes')) 'size_bytes': 0,
        if (!json.containsKey('source_kind')) 'source_kind': 'inline_text',
        if (!json.containsKey('provenance')) 'provenance': {},
      });
}

@freezed
abstract class ContentTextResolutionV1 with _$ContentTextResolutionV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ContentTextResolutionV1.def({
    @UuidValueConverter() required UuidValue contentId,
    String? contentKey,
    String? title,
    required String mediaType,
    required String text,
    @Default(const []) List<ContentTextPartV1> parts,
    required String digestAlgorithm,
    String? digest,
    required int sizeBytes,
    required String sourceKind,
    required Map<String, dynamic> provenance,
  }) = _ContentTextResolutionV1;

  factory ContentTextResolutionV1({
    required UuidValue contentId,
    String? contentKey,
    String? title,
    String? mediaType,
    String? text,
    List<ContentTextPartV1> parts = const [],
    String? digestAlgorithm,
    String? digest,
    int? sizeBytes,
    String? sourceKind,
    Map<String, dynamic>? provenance,
  }) {
    return _ContentTextResolutionV1(
      contentId: contentId,
      contentKey: contentKey,
      title: title,
      mediaType: mediaType ?? 'text/plain',
      text: text ?? '',
      parts: parts,
      digestAlgorithm: digestAlgorithm ?? 'sha256',
      digest: digest,
      sizeBytes: sizeBytes ?? 0,
      sourceKind: sourceKind ?? 'inline_text',
      provenance: provenance ?? {},
    );
  }

  factory ContentTextResolutionV1.fromJson(Map<String, dynamic> json) =>
      _$ContentTextResolutionV1FromJson({
        ...json,
        if (!json.containsKey('media_type')) 'media_type': 'text/plain',
        if (!json.containsKey('text')) 'text': '',
        if (!json.containsKey('digest_algorithm')) 'digest_algorithm': 'sha256',
        if (!json.containsKey('size_bytes')) 'size_bytes': 0,
        if (!json.containsKey('source_kind')) 'source_kind': 'inline_text',
        if (!json.containsKey('provenance')) 'provenance': {},
      });
}

@freezed
abstract class ContentTextCommitPartV1 with _$ContentTextCommitPartV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ContentTextCommitPartV1.def({
    required int position,
    String? partKey,
    required String mediaType,
    required String text,
    required String digestAlgorithm,
    String? digest,
    int? sizeBytes,
    required Map<String, dynamic> provenance,
  }) = _ContentTextCommitPartV1;

  factory ContentTextCommitPartV1({
    int? position,
    String? partKey,
    String? mediaType,
    required String text,
    String? digestAlgorithm,
    String? digest,
    int? sizeBytes,
    Map<String, dynamic>? provenance,
  }) {
    return _ContentTextCommitPartV1(
      position: position ?? 0,
      partKey: partKey,
      mediaType: mediaType ?? 'text/plain',
      text: text,
      digestAlgorithm: digestAlgorithm ?? 'sha256',
      digest: digest,
      sizeBytes: sizeBytes,
      provenance: provenance ?? {},
    );
  }

  factory ContentTextCommitPartV1.fromJson(Map<String, dynamic> json) =>
      _$ContentTextCommitPartV1FromJson({
        ...json,
        if (!json.containsKey('position')) 'position': 0,
        if (!json.containsKey('media_type')) 'media_type': 'text/plain',
        if (!json.containsKey('digest_algorithm')) 'digest_algorithm': 'sha256',
        if (!json.containsKey('provenance')) 'provenance': {},
      });
}

@freezed
abstract class ContentTextCommitResultV1 with _$ContentTextCommitResultV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ContentTextCommitResultV1.def({
    @UuidValueConverter() required UuidValue contentId,
    required String contentKey,
    String? title,
    required String sourceKind,
    required String sourceRef,
    required String mediaType,
    required String digestAlgorithm,
    required String digest,
    required int sizeBytes,
    @UuidValueConverter() UuidValue? domainCommitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    String? serviceHostReceiptRef,
    required Map<String, dynamic> provenance,
  }) = _ContentTextCommitResultV1;

  factory ContentTextCommitResultV1({
    required UuidValue contentId,
    required String contentKey,
    String? title,
    required String sourceKind,
    required String sourceRef,
    String? mediaType,
    String? digestAlgorithm,
    required String digest,
    required int sizeBytes,
    UuidValue? domainCommitId,
    UuidValue? objectInstanceGraphCommitId,
    String? serviceHostReceiptRef,
    Map<String, dynamic>? provenance,
  }) {
    return _ContentTextCommitResultV1(
      contentId: contentId,
      contentKey: contentKey,
      title: title,
      sourceKind: sourceKind,
      sourceRef: sourceRef,
      mediaType: mediaType ?? 'text/plain',
      digestAlgorithm: digestAlgorithm ?? 'sha256',
      digest: digest,
      sizeBytes: sizeBytes,
      domainCommitId: domainCommitId,
      objectInstanceGraphCommitId: objectInstanceGraphCommitId,
      serviceHostReceiptRef: serviceHostReceiptRef,
      provenance: provenance ?? {},
    );
  }

  factory ContentTextCommitResultV1.fromJson(Map<String, dynamic> json) =>
      _$ContentTextCommitResultV1FromJson({
        ...json,
        if (!json.containsKey('media_type')) 'media_type': 'text/plain',
        if (!json.containsKey('digest_algorithm')) 'digest_algorithm': 'sha256',
        if (!json.containsKey('provenance')) 'provenance': {},
      });
}

@freezed
abstract class ContentPackageExportPartV1 with _$ContentPackageExportPartV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ContentPackageExportPartV1.def({
    required String partKey,
    required int position,
    required String modalityType,
    required String contentPartType,
    required String mediaType,
    String? text,
    String? rawPath,
    String? uri,
    String? providerId,
    required String digestAlgorithm,
    String? digest,
    int? sizeBytes,
    required Map<String, dynamic> awareContentMapping,
    required Map<String, dynamic> provenance,
  }) = _ContentPackageExportPartV1;

  factory ContentPackageExportPartV1({
    required String partKey,
    int? position,
    String? modalityType,
    String? contentPartType,
    String? mediaType,
    String? text,
    String? rawPath,
    String? uri,
    String? providerId,
    String? digestAlgorithm,
    String? digest,
    int? sizeBytes,
    Map<String, dynamic>? awareContentMapping,
    Map<String, dynamic>? provenance,
  }) {
    return _ContentPackageExportPartV1(
      partKey: partKey,
      position: position ?? 0,
      modalityType: modalityType ?? 'text',
      contentPartType: contentPartType ?? 'text',
      mediaType: mediaType ?? 'text/plain',
      text: text,
      rawPath: rawPath,
      uri: uri,
      providerId: providerId,
      digestAlgorithm: digestAlgorithm ?? 'sha256',
      digest: digest,
      sizeBytes: sizeBytes,
      awareContentMapping: awareContentMapping ?? {},
      provenance: provenance ?? {},
    );
  }

  factory ContentPackageExportPartV1.fromJson(Map<String, dynamic> json) =>
      _$ContentPackageExportPartV1FromJson({
        ...json,
        if (!json.containsKey('position')) 'position': 0,
        if (!json.containsKey('modality_type')) 'modality_type': 'text',
        if (!json.containsKey('content_part_type')) 'content_part_type': 'text',
        if (!json.containsKey('media_type')) 'media_type': 'text/plain',
        if (!json.containsKey('digest_algorithm')) 'digest_algorithm': 'sha256',
        if (!json.containsKey('aware_content_mapping'))
          'aware_content_mapping': {},
        if (!json.containsKey('provenance')) 'provenance': {},
      });
}

@freezed
abstract class ContentPackageArtifactProjectionV1
    with _$ContentPackageArtifactProjectionV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ContentPackageArtifactProjectionV1.def({
    required String outputKey,
    required String artifactKey,
    required String artifactFamily,
    required String artifactRole,
    @Default(const []) List<String> requiredFor,
    required String producerProviderKey,
    required String producerKey,
    required String producerKind,
    int? materializationIndex,
    required String relativePath,
    String? uri,
    required String mediaType,
    required String digestAlgorithm,
    String? digest,
    int? sizeBytes,
    required String runtimeContractVersion,
    required Map<String, dynamic> providerPayload,
    required Map<String, dynamic> receiptPayload,
  }) = _ContentPackageArtifactProjectionV1;

  factory ContentPackageArtifactProjectionV1({
    String? outputKey,
    required String artifactKey,
    String? artifactFamily,
    String? artifactRole,
    List<String> requiredFor = const [],
    required String producerProviderKey,
    required String producerKey,
    String? producerKind,
    int? materializationIndex,
    required String relativePath,
    String? uri,
    String? mediaType,
    String? digestAlgorithm,
    String? digest,
    int? sizeBytes,
    String? runtimeContractVersion,
    Map<String, dynamic>? providerPayload,
    Map<String, dynamic>? receiptPayload,
  }) {
    return _ContentPackageArtifactProjectionV1(
      outputKey: outputKey ?? 'content',
      artifactKey: artifactKey,
      artifactFamily: artifactFamily ?? 'workspace_content',
      artifactRole: artifactRole ?? 'coordination_content',
      requiredFor: requiredFor,
      producerProviderKey: producerProviderKey,
      producerKey: producerKey,
      producerKind: producerKind ?? 'service_export',
      materializationIndex: materializationIndex,
      relativePath: relativePath,
      uri: uri,
      mediaType: mediaType ?? 'text/plain',
      digestAlgorithm: digestAlgorithm ?? 'sha256',
      digest: digest,
      sizeBytes: sizeBytes,
      runtimeContractVersion:
          runtimeContractVersion ?? 'aware.content.package_export.v1',
      providerPayload: providerPayload ?? {},
      receiptPayload: receiptPayload ?? {},
    );
  }

  factory ContentPackageArtifactProjectionV1.fromJson(
    Map<String, dynamic> json,
  ) => _$ContentPackageArtifactProjectionV1FromJson({
    ...json,
    if (!json.containsKey('output_key')) 'output_key': 'content',
    if (!json.containsKey('artifact_family'))
      'artifact_family': 'workspace_content',
    if (!json.containsKey('artifact_role'))
      'artifact_role': 'coordination_content',
    if (!json.containsKey('producer_kind')) 'producer_kind': 'service_export',
    if (!json.containsKey('media_type')) 'media_type': 'text/plain',
    if (!json.containsKey('digest_algorithm')) 'digest_algorithm': 'sha256',
    if (!json.containsKey('runtime_contract_version'))
      'runtime_contract_version': 'aware.content.package_export.v1',
    if (!json.containsKey('provider_payload')) 'provider_payload': {},
    if (!json.containsKey('receipt_payload')) 'receipt_payload': {},
  });
}

@freezed
abstract class ContentPackageExportDocumentV1
    with _$ContentPackageExportDocumentV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ContentPackageExportDocumentV1.def({
    required String exportKind,
    required String contractVersion,
    required String packageName,
    String? packageRoot,
    String? manifestRelativePath,
    String? title,
    required String packageKind,
    required String sourceProviderKey,
    required String sourceRef,
    required String runtimeContractVersion,
    String? contentKey,
    String? contentTitle,
    required String targetPath,
    required String mediaType,
    required String digestAlgorithm,
    String? digest,
    int? sizeBytes,
    String? contentText,
    @Default(const []) List<ContentPackageExportPartV1> parts,
    ContentPackageArtifactProjectionV1? artifact,
    required Map<String, dynamic> awareContentMapping,
    required Map<String, dynamic> providerPayload,
    required Map<String, dynamic> provenance,
  }) = _ContentPackageExportDocumentV1;

  factory ContentPackageExportDocumentV1({
    String? exportKind,
    String? contractVersion,
    required String packageName,
    String? packageRoot,
    String? manifestRelativePath,
    String? title,
    String? packageKind,
    required String sourceProviderKey,
    required String sourceRef,
    String? runtimeContractVersion,
    String? contentKey,
    String? contentTitle,
    required String targetPath,
    String? mediaType,
    String? digestAlgorithm,
    String? digest,
    int? sizeBytes,
    String? contentText,
    List<ContentPackageExportPartV1> parts = const [],
    ContentPackageArtifactProjectionV1? artifact,
    Map<String, dynamic>? awareContentMapping,
    Map<String, dynamic>? providerPayload,
    Map<String, dynamic>? provenance,
  }) {
    return _ContentPackageExportDocumentV1(
      exportKind: exportKind ?? 'content_package_export',
      contractVersion: contractVersion ?? 'aware.content.package_export.v1',
      packageName: packageName,
      packageRoot: packageRoot,
      manifestRelativePath: manifestRelativePath,
      title: title,
      packageKind: packageKind ?? 'content',
      sourceProviderKey: sourceProviderKey,
      sourceRef: sourceRef,
      runtimeContractVersion:
          runtimeContractVersion ?? 'aware.content.package_export.v1',
      contentKey: contentKey,
      contentTitle: contentTitle,
      targetPath: targetPath,
      mediaType: mediaType ?? 'text/plain',
      digestAlgorithm: digestAlgorithm ?? 'sha256',
      digest: digest,
      sizeBytes: sizeBytes,
      contentText: contentText,
      parts: parts,
      artifact: artifact,
      awareContentMapping: awareContentMapping ?? {},
      providerPayload: providerPayload ?? {},
      provenance: provenance ?? {},
    );
  }

  factory ContentPackageExportDocumentV1.fromJson(Map<String, dynamic> json) =>
      _$ContentPackageExportDocumentV1FromJson({
        ...json,
        if (!json.containsKey('export_kind'))
          'export_kind': 'content_package_export',
        if (!json.containsKey('contract_version'))
          'contract_version': 'aware.content.package_export.v1',
        if (!json.containsKey('package_kind')) 'package_kind': 'content',
        if (!json.containsKey('runtime_contract_version'))
          'runtime_contract_version': 'aware.content.package_export.v1',
        if (!json.containsKey('media_type')) 'media_type': 'text/plain',
        if (!json.containsKey('digest_algorithm')) 'digest_algorithm': 'sha256',
        if (!json.containsKey('aware_content_mapping'))
          'aware_content_mapping': {},
        if (!json.containsKey('provider_payload')) 'provider_payload': {},
        if (!json.containsKey('provenance')) 'provenance': {},
      });
}

@freezed
abstract class ContentPackageMaterializedArtifactRefV1
    with _$ContentPackageMaterializedArtifactRefV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ContentPackageMaterializedArtifactRefV1.def({
    @UuidValueConverter() UuidValue? contentPackageId,
    @UuidValueConverter() UuidValue? contentId,
    @UuidValueConverter() UuidValue? domainCommitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    String? serviceHostReceiptRef,
    required String outputKey,
    required String artifactKey,
    required String status,
    String? artifactFamily,
    String? artifactRole,
    @Default(const []) List<String> requiredFor,
    String? producerProviderKey,
    String? producerKey,
    String? producerKind,
    int? materializationIndex,
    String? digestAlgorithm,
    String? digest,
    String? relativePath,
    String? uri,
    String? mediaType,
    int? sizeBytes,
    String? runtimeContractVersion,
    required Map<String, dynamic> providerPayload,
    required Map<String, dynamic> receiptPayload,
  }) = _ContentPackageMaterializedArtifactRefV1;

  factory ContentPackageMaterializedArtifactRefV1({
    UuidValue? contentPackageId,
    UuidValue? contentId,
    UuidValue? domainCommitId,
    UuidValue? objectInstanceGraphCommitId,
    String? serviceHostReceiptRef,
    required String outputKey,
    required String artifactKey,
    String? status,
    String? artifactFamily,
    String? artifactRole,
    List<String> requiredFor = const [],
    String? producerProviderKey,
    String? producerKey,
    String? producerKind,
    int? materializationIndex,
    String? digestAlgorithm,
    String? digest,
    String? relativePath,
    String? uri,
    String? mediaType,
    int? sizeBytes,
    String? runtimeContractVersion,
    Map<String, dynamic>? providerPayload,
    Map<String, dynamic>? receiptPayload,
  }) {
    return _ContentPackageMaterializedArtifactRefV1(
      contentPackageId: contentPackageId,
      contentId: contentId,
      domainCommitId: domainCommitId,
      objectInstanceGraphCommitId: objectInstanceGraphCommitId,
      serviceHostReceiptRef: serviceHostReceiptRef,
      outputKey: outputKey,
      artifactKey: artifactKey,
      status: status ?? 'available',
      artifactFamily: artifactFamily,
      artifactRole: artifactRole,
      requiredFor: requiredFor,
      producerProviderKey: producerProviderKey,
      producerKey: producerKey,
      producerKind: producerKind,
      materializationIndex: materializationIndex,
      digestAlgorithm: digestAlgorithm ?? 'sha256',
      digest: digest,
      relativePath: relativePath,
      uri: uri,
      mediaType: mediaType,
      sizeBytes: sizeBytes,
      runtimeContractVersion: runtimeContractVersion,
      providerPayload: providerPayload ?? {},
      receiptPayload: receiptPayload ?? {},
    );
  }

  factory ContentPackageMaterializedArtifactRefV1.fromJson(
    Map<String, dynamic> json,
  ) => _$ContentPackageMaterializedArtifactRefV1FromJson({
    ...json,
    if (!json.containsKey('status')) 'status': 'available',
    if (!json.containsKey('digest_algorithm')) 'digest_algorithm': 'sha256',
    if (!json.containsKey('provider_payload')) 'provider_payload': {},
    if (!json.containsKey('receipt_payload')) 'receipt_payload': {},
  });
}

@freezed
abstract class ContentPackageMaterializationResultV1
    with _$ContentPackageMaterializationResultV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ContentPackageMaterializationResultV1.def({
    @UuidValueConverter() UuidValue? contentPackageId,
    @UuidValueConverter() UuidValue? contentId,
    @UuidValueConverter() UuidValue? domainCommitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    String? serviceHostReceiptRef,
    required String packageName,
    String? contentKey,
    required String sourceProviderKey,
    required String sourceRef,
    required String targetPath,
    required String mediaType,
    required String digestAlgorithm,
    String? digest,
    int? sizeBytes,
    @Default(const [])
    List<ContentPackageMaterializedArtifactRefV1> artifactRefs,
    required Map<String, dynamic> awareContentMapping,
    required Map<String, dynamic> provenance,
  }) = _ContentPackageMaterializationResultV1;

  factory ContentPackageMaterializationResultV1({
    UuidValue? contentPackageId,
    UuidValue? contentId,
    UuidValue? domainCommitId,
    UuidValue? objectInstanceGraphCommitId,
    String? serviceHostReceiptRef,
    required String packageName,
    String? contentKey,
    required String sourceProviderKey,
    required String sourceRef,
    required String targetPath,
    String? mediaType,
    String? digestAlgorithm,
    String? digest,
    int? sizeBytes,
    List<ContentPackageMaterializedArtifactRefV1> artifactRefs = const [],
    Map<String, dynamic>? awareContentMapping,
    Map<String, dynamic>? provenance,
  }) {
    return _ContentPackageMaterializationResultV1(
      contentPackageId: contentPackageId,
      contentId: contentId,
      domainCommitId: domainCommitId,
      objectInstanceGraphCommitId: objectInstanceGraphCommitId,
      serviceHostReceiptRef: serviceHostReceiptRef,
      packageName: packageName,
      contentKey: contentKey,
      sourceProviderKey: sourceProviderKey,
      sourceRef: sourceRef,
      targetPath: targetPath,
      mediaType: mediaType ?? 'text/plain',
      digestAlgorithm: digestAlgorithm ?? 'sha256',
      digest: digest,
      sizeBytes: sizeBytes,
      artifactRefs: artifactRefs,
      awareContentMapping: awareContentMapping ?? {},
      provenance: provenance ?? {},
    );
  }

  factory ContentPackageMaterializationResultV1.fromJson(
    Map<String, dynamic> json,
  ) => _$ContentPackageMaterializationResultV1FromJson({
    ...json,
    if (!json.containsKey('media_type')) 'media_type': 'text/plain',
    if (!json.containsKey('digest_algorithm')) 'digest_algorithm': 'sha256',
    if (!json.containsKey('aware_content_mapping')) 'aware_content_mapping': {},
    if (!json.containsKey('provenance')) 'provenance': {},
  });
}

@freezed
abstract class ContentOperationReceipt with _$ContentOperationReceipt {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ContentOperationReceipt.def({
    required String operation,
    required String status,
    @UuidValueConverter() UuidValue? contentId,
    @UuidValueConverter() UuidValue? contentPackageId,
    @UuidValueConverter() UuidValue? domainCommitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    String? serviceHostReceiptRef,
    String? packageName,
    required String digestAlgorithm,
    String? digest,
    int? sizeBytes,
    required String backendKind,
    required Map<String, dynamic> metadata,
  }) = _ContentOperationReceipt;

  factory ContentOperationReceipt({
    required String operation,
    String? status,
    UuidValue? contentId,
    UuidValue? contentPackageId,
    UuidValue? domainCommitId,
    UuidValue? objectInstanceGraphCommitId,
    String? serviceHostReceiptRef,
    String? packageName,
    String? digestAlgorithm,
    String? digest,
    int? sizeBytes,
    String? backendKind,
    Map<String, dynamic>? metadata,
  }) {
    return _ContentOperationReceipt(
      operation: operation,
      status: status ?? 'succeeded',
      contentId: contentId,
      contentPackageId: contentPackageId,
      domainCommitId: domainCommitId,
      objectInstanceGraphCommitId: objectInstanceGraphCommitId,
      serviceHostReceiptRef: serviceHostReceiptRef,
      packageName: packageName,
      digestAlgorithm: digestAlgorithm ?? 'sha256',
      digest: digest,
      sizeBytes: sizeBytes,
      backendKind: backendKind ?? 'content-service',
      metadata: metadata ?? {},
    );
  }

  factory ContentOperationReceipt.fromJson(Map<String, dynamic> json) =>
      _$ContentOperationReceiptFromJson({
        ...json,
        if (!json.containsKey('status')) 'status': 'succeeded',
        if (!json.containsKey('digest_algorithm')) 'digest_algorithm': 'sha256',
        if (!json.containsKey('backend_kind'))
          'backend_kind': 'content-service',
        if (!json.containsKey('metadata')) 'metadata': {},
      });
}

@Freezed(unionKey: 'operation')
abstract class ContentServiceRequest with _$ContentServiceRequest {
  @FreezedUnionValue('resolve_content_text')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ContentServiceRequest.resolveContentText({
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? branchId,
    @UuidValueConverter() UuidValue? contentId,
    @UuidValueConverter() UuidValue? contentClassInstanceIdentityId,
    @UuidValueConverter() UuidValue? contentClassConfigId,
    required String mediaType,
    required bool includeParts,
    int? maxChars,
  }) = ResolveContentTextRequest;

  @FreezedUnionValue('commit_content_text')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ContentServiceRequest.commitContentText({
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? branchId,
    required String contentKey,
    String? title,
    required String sourceKind,
    required String sourceRef,
    required String mediaType,
    String? text,
    @Default(const []) List<ContentTextCommitPartV1> parts,
    required String digestAlgorithm,
    String? digest,
    int? sizeBytes,
    required Map<String, dynamic> provenance,
  }) = CommitContentTextRequest;

  @FreezedUnionValue('materialize_content_package')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ContentServiceRequest.materializeContentPackage({
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? branchId,
    required ContentPackageExportDocumentV1 packageExport,
  }) = MaterializeContentPackageRequest;

  factory ContentServiceRequest.fromJson(Map<String, dynamic> json) =>
      _$ContentServiceRequestFromJson(json);
}

@Freezed(unionKey: 'operation')
abstract class ContentServiceResponse with _$ContentServiceResponse {
  @FreezedUnionValue('resolve_content_text')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ContentServiceResponse.resolveContentText({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? error,
    ContentOperationReceipt? receipt,
    ContentTextResolutionV1? resolution,
  }) = ResolveContentTextResponse;

  @FreezedUnionValue('commit_content_text')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ContentServiceResponse.commitContentText({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? error,
    ContentOperationReceipt? receipt,
    ContentTextCommitResultV1? commitResult,
  }) = CommitContentTextResponse;

  @FreezedUnionValue('materialize_content_package')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ContentServiceResponse.materializeContentPackage({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? error,
    ContentOperationReceipt? receipt,
    ContentPackageMaterializationResultV1? materialization,
  }) = MaterializeContentPackageResponse;

  factory ContentServiceResponse.fromJson(Map<String, dynamic> json) =>
      _$ContentServiceResponseFromJson(json);
}
