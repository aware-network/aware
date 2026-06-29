// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'media_model.freezed.dart';
part 'media_model.g.dart';

@freezed
abstract class StorageBlobRef with _$StorageBlobRef {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory StorageBlobRef.def({
    @UuidValueConverter() UuidValue? objectId,
    String? sha,
  }) = _StorageBlobRef;

  factory StorageBlobRef({UuidValue? objectId, String? sha}) {
    return _StorageBlobRef(objectId: objectId, sha: sha);
  }

  factory StorageBlobRef.fromJson(Map<String, dynamic> json) =>
      _$StorageBlobRefFromJson(json);
}

@freezed
abstract class StorageMediaRef with _$StorageMediaRef {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory StorageMediaRef.def({
    @UuidValueConverter() required UuidValue objectId,
    String? uri,
    required String uriScheme,
    String? mediaKind,
    String? mimeType,
    String? sha,
    String? variantKey,
    String? renditionKey,
    String? filename,
    required Map<String, dynamic> metadata,
  }) = _StorageMediaRef;

  factory StorageMediaRef({
    required UuidValue objectId,
    String? uri,
    required String uriScheme,
    String? mediaKind,
    String? mimeType,
    String? sha,
    String? variantKey,
    String? renditionKey,
    String? filename,
    required Map<String, dynamic> metadata,
  }) {
    return _StorageMediaRef(
      objectId: objectId,
      uri: uri,
      uriScheme: uriScheme,
      mediaKind: mediaKind,
      mimeType: mimeType,
      sha: sha,
      variantKey: variantKey,
      renditionKey: renditionKey,
      filename: filename,
      metadata: metadata,
    );
  }

  factory StorageMediaRef.fromJson(Map<String, dynamic> json) =>
      _$StorageMediaRefFromJson(json);
}

@freezed
abstract class StorageBlobMetadata with _$StorageBlobMetadata {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory StorageBlobMetadata.def({
    @UuidValueConverter() required UuidValue objectId,
    required String sha,
    required String mimeType,
    required int sizeBytes,
    String? objectKey,
    String? pathLocal,
    @UuidValueConverter() UuidValue? bucketId,
  }) = _StorageBlobMetadata;

  factory StorageBlobMetadata({
    required UuidValue objectId,
    required String sha,
    required String mimeType,
    required int sizeBytes,
    String? objectKey,
    String? pathLocal,
    UuidValue? bucketId,
  }) {
    return _StorageBlobMetadata(
      objectId: objectId,
      sha: sha,
      mimeType: mimeType,
      sizeBytes: sizeBytes,
      objectKey: objectKey,
      pathLocal: pathLocal,
      bucketId: bucketId,
    );
  }

  factory StorageBlobMetadata.fromJson(Map<String, dynamic> json) =>
      _$StorageBlobMetadataFromJson(json);
}

@freezed
abstract class StorageMediaResolution with _$StorageMediaResolution {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory StorageMediaResolution.def({
    required StorageMediaRef mediaRef,
    @UuidValueConverter() required UuidValue objectId,
    required String sha,
    required String mimeType,
    required int sizeBytes,
    required String uri,
    required String uriScheme,
    String? httpUrl,
    String? cacheControl,
    String? etag,
    String? contentDisposition,
    String? filename,
    String? expiresAt,
    required Map<String, dynamic> metadata,
  }) = _StorageMediaResolution;

  factory StorageMediaResolution({
    required StorageMediaRef mediaRef,
    required UuidValue objectId,
    required String sha,
    required String mimeType,
    required int sizeBytes,
    required String uri,
    required String uriScheme,
    String? httpUrl,
    String? cacheControl,
    String? etag,
    String? contentDisposition,
    String? filename,
    String? expiresAt,
    required Map<String, dynamic> metadata,
  }) {
    return _StorageMediaResolution(
      mediaRef: mediaRef,
      objectId: objectId,
      sha: sha,
      mimeType: mimeType,
      sizeBytes: sizeBytes,
      uri: uri,
      uriScheme: uriScheme,
      httpUrl: httpUrl,
      cacheControl: cacheControl,
      etag: etag,
      contentDisposition: contentDisposition,
      filename: filename,
      expiresAt: expiresAt,
      metadata: metadata,
    );
  }

  factory StorageMediaResolution.fromJson(Map<String, dynamic> json) =>
      _$StorageMediaResolutionFromJson(json);
}

@freezed
abstract class StorageOperationReceipt with _$StorageOperationReceipt {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory StorageOperationReceipt.def({
    required String operation,
    required String status,
    @UuidValueConverter() UuidValue? objectId,
    String? sha,
    int? sizeBytes,
    String? mimeType,
    required String backendKind,
    required String dataPlane,
    required Map<String, dynamic> metadata,
  }) = _StorageOperationReceipt;

  factory StorageOperationReceipt({
    required String operation,
    required String status,
    UuidValue? objectId,
    String? sha,
    int? sizeBytes,
    String? mimeType,
    required String backendKind,
    required String dataPlane,
    required Map<String, dynamic> metadata,
  }) {
    return _StorageOperationReceipt(
      operation: operation,
      status: status,
      objectId: objectId,
      sha: sha,
      sizeBytes: sizeBytes,
      mimeType: mimeType,
      backendKind: backendKind,
      dataPlane: dataPlane,
      metadata: metadata,
    );
  }

  factory StorageOperationReceipt.fromJson(Map<String, dynamic> json) =>
      _$StorageOperationReceiptFromJson(json);
}
