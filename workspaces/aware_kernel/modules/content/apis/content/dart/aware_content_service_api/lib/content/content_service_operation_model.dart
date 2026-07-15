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
/// - Content API is a read/render and package materialization boundary over
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
    required int position,
    String? partKey,
    required String mediaType,
    required String text,
    required String digestAlgorithm,
    String? digest,
    required int sizeBytes,
    required String sourceKind,
    required Map<String, dynamic> provenance,
  }) {
    return _ContentTextPartV1(
      contentPartContentId: contentPartContentId,
      contentPartId: contentPartId,
      contentPartTextId: contentPartTextId,
      position: position,
      partKey: partKey,
      mediaType: mediaType,
      text: text,
      digestAlgorithm: digestAlgorithm,
      digest: digest,
      sizeBytes: sizeBytes,
      sourceKind: sourceKind,
      provenance: provenance,
    );
  }

  factory ContentTextPartV1.fromJson(Map<String, dynamic> json) =>
      _$ContentTextPartV1FromJson(json);
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
    required String mediaType,
    required String text,
    List<ContentTextPartV1> parts = const [],
    required String digestAlgorithm,
    String? digest,
    required int sizeBytes,
    required String sourceKind,
    required Map<String, dynamic> provenance,
  }) {
    return _ContentTextResolutionV1(
      contentId: contentId,
      contentKey: contentKey,
      title: title,
      mediaType: mediaType,
      text: text,
      parts: parts,
      digestAlgorithm: digestAlgorithm,
      digest: digest,
      sizeBytes: sizeBytes,
      sourceKind: sourceKind,
      provenance: provenance,
    );
  }

  factory ContentTextResolutionV1.fromJson(Map<String, dynamic> json) =>
      _$ContentTextResolutionV1FromJson(json);
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
  }) {
    return _ContentPackageExportPartV1(
      partKey: partKey,
      position: position,
      modalityType: modalityType,
      contentPartType: contentPartType,
      mediaType: mediaType,
      text: text,
      rawPath: rawPath,
      uri: uri,
      providerId: providerId,
      digestAlgorithm: digestAlgorithm,
      digest: digest,
      sizeBytes: sizeBytes,
      awareContentMapping: awareContentMapping,
      provenance: provenance,
    );
  }

  factory ContentPackageExportPartV1.fromJson(Map<String, dynamic> json) =>
      _$ContentPackageExportPartV1FromJson(json);
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
    required String outputKey,
    required String artifactKey,
    required String artifactFamily,
    required String artifactRole,
    List<String> requiredFor = const [],
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
  }) {
    return _ContentPackageArtifactProjectionV1(
      outputKey: outputKey,
      artifactKey: artifactKey,
      artifactFamily: artifactFamily,
      artifactRole: artifactRole,
      requiredFor: requiredFor,
      producerProviderKey: producerProviderKey,
      producerKey: producerKey,
      producerKind: producerKind,
      materializationIndex: materializationIndex,
      relativePath: relativePath,
      uri: uri,
      mediaType: mediaType,
      digestAlgorithm: digestAlgorithm,
      digest: digest,
      sizeBytes: sizeBytes,
      runtimeContractVersion: runtimeContractVersion,
      providerPayload: providerPayload,
      receiptPayload: receiptPayload,
    );
  }

  factory ContentPackageArtifactProjectionV1.fromJson(
    Map<String, dynamic> json,
  ) => _$ContentPackageArtifactProjectionV1FromJson(json);
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
    List<ContentPackageExportPartV1> parts = const [],
    ContentPackageArtifactProjectionV1? artifact,
    required Map<String, dynamic> awareContentMapping,
    required Map<String, dynamic> providerPayload,
    required Map<String, dynamic> provenance,
  }) {
    return _ContentPackageExportDocumentV1(
      exportKind: exportKind,
      contractVersion: contractVersion,
      packageName: packageName,
      packageRoot: packageRoot,
      manifestRelativePath: manifestRelativePath,
      title: title,
      packageKind: packageKind,
      sourceProviderKey: sourceProviderKey,
      sourceRef: sourceRef,
      runtimeContractVersion: runtimeContractVersion,
      contentKey: contentKey,
      contentTitle: contentTitle,
      targetPath: targetPath,
      mediaType: mediaType,
      digestAlgorithm: digestAlgorithm,
      digest: digest,
      sizeBytes: sizeBytes,
      contentText: contentText,
      parts: parts,
      artifact: artifact,
      awareContentMapping: awareContentMapping,
      providerPayload: providerPayload,
      provenance: provenance,
    );
  }

  factory ContentPackageExportDocumentV1.fromJson(Map<String, dynamic> json) =>
      _$ContentPackageExportDocumentV1FromJson(json);
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
    required String status,
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
    required Map<String, dynamic> providerPayload,
    required Map<String, dynamic> receiptPayload,
  }) {
    return _ContentPackageMaterializedArtifactRefV1(
      contentPackageId: contentPackageId,
      contentId: contentId,
      domainCommitId: domainCommitId,
      objectInstanceGraphCommitId: objectInstanceGraphCommitId,
      serviceHostReceiptRef: serviceHostReceiptRef,
      outputKey: outputKey,
      artifactKey: artifactKey,
      status: status,
      artifactFamily: artifactFamily,
      artifactRole: artifactRole,
      requiredFor: requiredFor,
      producerProviderKey: producerProviderKey,
      producerKey: producerKey,
      producerKind: producerKind,
      materializationIndex: materializationIndex,
      digestAlgorithm: digestAlgorithm,
      digest: digest,
      relativePath: relativePath,
      uri: uri,
      mediaType: mediaType,
      sizeBytes: sizeBytes,
      runtimeContractVersion: runtimeContractVersion,
      providerPayload: providerPayload,
      receiptPayload: receiptPayload,
    );
  }

  factory ContentPackageMaterializedArtifactRefV1.fromJson(
    Map<String, dynamic> json,
  ) => _$ContentPackageMaterializedArtifactRefV1FromJson(json);
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
    required String mediaType,
    required String digestAlgorithm,
    String? digest,
    int? sizeBytes,
    List<ContentPackageMaterializedArtifactRefV1> artifactRefs = const [],
    required Map<String, dynamic> awareContentMapping,
    required Map<String, dynamic> provenance,
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
      mediaType: mediaType,
      digestAlgorithm: digestAlgorithm,
      digest: digest,
      sizeBytes: sizeBytes,
      artifactRefs: artifactRefs,
      awareContentMapping: awareContentMapping,
      provenance: provenance,
    );
  }

  factory ContentPackageMaterializationResultV1.fromJson(
    Map<String, dynamic> json,
  ) => _$ContentPackageMaterializationResultV1FromJson(json);
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
    required String status,
    UuidValue? contentId,
    UuidValue? contentPackageId,
    UuidValue? domainCommitId,
    UuidValue? objectInstanceGraphCommitId,
    String? serviceHostReceiptRef,
    String? packageName,
    required String digestAlgorithm,
    String? digest,
    int? sizeBytes,
    required String backendKind,
    required Map<String, dynamic> metadata,
  }) {
    return _ContentOperationReceipt(
      operation: operation,
      status: status,
      contentId: contentId,
      contentPackageId: contentPackageId,
      domainCommitId: domainCommitId,
      objectInstanceGraphCommitId: objectInstanceGraphCommitId,
      serviceHostReceiptRef: serviceHostReceiptRef,
      packageName: packageName,
      digestAlgorithm: digestAlgorithm,
      digest: digest,
      sizeBytes: sizeBytes,
      backendKind: backendKind,
      metadata: metadata,
    );
  }

  factory ContentOperationReceipt.fromJson(Map<String, dynamic> json) =>
      _$ContentOperationReceiptFromJson(json);
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
