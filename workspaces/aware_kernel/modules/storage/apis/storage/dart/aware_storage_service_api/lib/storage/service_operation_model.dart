// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'media_enums.dart';
import 'media_model.dart';
import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'service_operation_model.freezed.dart';
part 'service_operation_model.g.dart';

/// Storage service operation DTOs.
/// The generated Product A API is the control-plane boundary. It registers and
/// resolves commit-backed StorageBlob metadata, then returns media descriptors
/// for Storage-owned byte transport. Raw media bytes are intentionally absent
/// from these payloads.
@Freezed(unionKey: 'operation')
abstract class StorageServiceRequest with _$StorageServiceRequest {
  @FreezedUnionValue('register_blob')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory StorageServiceRequest.registerBlob({
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? objectId,
    required String sha,
    required String mimeType,
    required int sizeBytes,
    @UuidValueConverter() UuidValue? bucketId,
    String? objectKey,
    String? pathLocal,
  }) = RegisterStorageBlobRequest;

  @FreezedUnionValue('describe_blob')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory StorageServiceRequest.describeBlob({
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue objectId,
  }) = DescribeStorageBlobRequest;

  @FreezedUnionValue('resolve_media')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory StorageServiceRequest.resolveMedia({
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() UuidValue? actorId,
    required StorageMediaRef mediaRef,
    required bool requireOwnership,
    required bool includeHttpUrl,
    String? preferredUriScheme,
    String? filename,
    @JsonKey(
      fromJson: StorageMediaDispositionExtension.fromJson,
      toJson: StorageMediaDispositionExtension.toJson,
    )
    required StorageMediaDisposition disposition,
  }) = ResolveStorageMediaRequest;

  factory StorageServiceRequest.fromJson(Map<String, dynamic> json) =>
      _$StorageServiceRequestFromJson(json);
}

@Freezed(unionKey: 'operation')
abstract class StorageServiceResponse with _$StorageServiceResponse {
  @FreezedUnionValue('register_blob')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory StorageServiceResponse.registerBlob({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? error,
    StorageOperationReceipt? receipt,
    StorageBlobMetadata? metadata,
  }) = RegisterStorageBlobResponse;

  @FreezedUnionValue('describe_blob')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory StorageServiceResponse.describeBlob({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? error,
    StorageOperationReceipt? receipt,
    StorageBlobMetadata? metadata,
  }) = DescribeStorageBlobResponse;

  @FreezedUnionValue('resolve_media')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory StorageServiceResponse.resolveMedia({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? error,
    StorageOperationReceipt? receipt,
    StorageBlobMetadata? metadata,
    StorageMediaResolution? resolution,
  }) = ResolveStorageMediaResponse;

  factory StorageServiceResponse.fromJson(Map<String, dynamic> json) =>
      _$StorageServiceResponseFromJson(json);
}
