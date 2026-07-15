// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';
import 'package_distribution_enums.dart';

part 'package_distribution_model.freezed.dart';
part 'package_distribution_model.g.dart';

@Freezed(unionKey: 'operation')
abstract class CodePackageServiceRequest with _$CodePackageServiceRequest {
  @FreezedUnionValue('discover_code_package_channel_heads')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CodePackageServiceRequest.discoverCodePackageChannelHeads({
    @UuidValueConverter() UuidValue? requestId,
    String? query,
    String? packageName,
    @JsonKey(
      fromJson: CodeLanguageExtension.fromJsonNullable,
      toJson: CodeLanguageExtension.toJsonNullable,
    )
    CodeLanguage? language,
    String? surface,
    String? channel,
    String? authorityBaseUrl,
    String? indexUrl,
    required int limit,
  }) = DiscoverCodePackageChannelHeadsRequest;

  @FreezedUnionValue('search_code_package')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CodePackageServiceRequest.searchCodePackage({
    @UuidValueConverter() UuidValue? requestId,
    String? query,
    String? packageName,
    @JsonKey(
      fromJson: CodeLanguageExtension.fromJsonNullable,
      toJson: CodeLanguageExtension.toJsonNullable,
    )
    CodeLanguage? language,
    String? surface,
    required String channel,
    String? authorityBaseUrl,
    String? indexUrl,
    required int limit,
  }) = SearchCodePackageRequest;

  @FreezedUnionValue('describe_code_package')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CodePackageServiceRequest.describeCodePackage({
    @UuidValueConverter() UuidValue? requestId,
    required CodePackageRef selector,
    String? authorityBaseUrl,
    String? indexUrl,
  }) = DescribeCodePackageRequest;

  @FreezedUnionValue('resolve_code_package')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CodePackageServiceRequest.resolveCodePackage({
    @UuidValueConverter() UuidValue? requestId,
    required CodePackageRef selector,
    String? authorityBaseUrl,
    String? indexUrl,
  }) = ResolveCodePackageRequest;

  @FreezedUnionValue('download_code_package')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CodePackageServiceRequest.downloadCodePackage({
    @UuidValueConverter() UuidValue? requestId,
    required CodePackageRef selector,
    String? authorityBaseUrl,
    String? indexUrl,
  }) = DownloadCodePackageRequest;

  @FreezedUnionValue('publish_code_package')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CodePackageServiceRequest.publishCodePackage({
    @UuidValueConverter() UuidValue? requestId,
    required CodePackageDescriptor descriptor,
    required CodePackageArtifactLock artifactLock,
    required String channel,
    String? authorityBaseUrl,
    String? indexUrl,
    String? publisherExecutionId,
    String? idempotencyKey,
  }) = PublishCodePackageRequest;

  factory CodePackageServiceRequest.fromJson(Map<String, dynamic> json) =>
      _$CodePackageServiceRequestFromJson(json);
}

@Freezed(unionKey: 'operation')
abstract class CodePackageServiceResponse with _$CodePackageServiceResponse {
  @FreezedUnionValue('discover_code_package_channel_heads')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CodePackageServiceResponse.discoverCodePackageChannelHeads({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? info,
    String? error,
    String? authoritySourceUrl,
    @Default(const []) List<CodePackageDiscoveryEntry> entries,
  }) = DiscoverCodePackageChannelHeadsResponse;

  @FreezedUnionValue('search_code_package')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CodePackageServiceResponse.searchCodePackage({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? info,
    String? error,
    String? authoritySourceUrl,
    @Default(const []) List<CodePackageDescriptor> descriptors,
  }) = SearchCodePackageResponse;

  @FreezedUnionValue('describe_code_package')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CodePackageServiceResponse.describeCodePackage({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? info,
    String? error,
    String? authoritySourceUrl,
    CodePackageDescriptor? descriptor,
  }) = DescribeCodePackageResponse;

  @FreezedUnionValue('resolve_code_package')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CodePackageServiceResponse.resolveCodePackage({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? info,
    String? error,
    String? authoritySourceUrl,
    required CodePackageRef selector,
    required CodePackageDescriptor descriptor,
    required CodePackageArtifactLock artifactLock,
  }) = ResolveCodePackageResponse;

  @FreezedUnionValue('download_code_package')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CodePackageServiceResponse.downloadCodePackage({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? info,
    String? error,
    String? authoritySourceUrl,
    required CodePackageRef selector,
    required CodePackageArtifactLock artifactLock,
  }) = DownloadCodePackageResponse;

  @FreezedUnionValue('publish_code_package')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CodePackageServiceResponse.publishCodePackage({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? info,
    String? error,
    String? authoritySourceUrl,
    CodePackageRef? selector,
    CodePackageDescriptor? descriptor,
    CodePackageArtifactLock? artifactLock,
    required bool accepted,
  }) = PublishCodePackageResponse;

  factory CodePackageServiceResponse.fromJson(Map<String, dynamic> json) =>
      _$CodePackageServiceResponseFromJson(json);
}

@freezed
abstract class CodePackageRef with _$CodePackageRef {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CodePackageRef.def({
    required String packageName,
    @JsonKey(
      fromJson: CodeLanguageExtension.fromJsonNullable,
      toJson: CodeLanguageExtension.toJsonNullable,
    )
    CodeLanguage? language,
    String? surface,
    required String channel,
    String? version,
    String? revisionId,
    String? digest,
  }) = _CodePackageRef;

  factory CodePackageRef({
    required String packageName,
    CodeLanguage? language,
    String? surface,
    String? channel,
    String? version,
    String? revisionId,
    String? digest,
  }) {
    return _CodePackageRef(
      packageName: packageName,
      language: language,
      surface: surface,
      channel: channel ?? 'stable',
      version: version,
      revisionId: revisionId,
      digest: digest,
    );
  }

  factory CodePackageRef.fromJson(Map<String, dynamic> json) =>
      _$CodePackageRefFromJson({
        ...json,
        if (!json.containsKey('channel')) 'channel': 'stable',
      });
}

@freezed
abstract class CodePackageArtifactLock with _$CodePackageArtifactLock {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CodePackageArtifactLock.def({
    required String artifactUrl,
    required String sha256,
    int? sizeBytes,
    String? mediaType,
    String? archiveFormat,
    String? revisionId,
    String? publishedAt,
  }) = _CodePackageArtifactLock;

  factory CodePackageArtifactLock({
    required String artifactUrl,
    required String sha256,
    int? sizeBytes,
    String? mediaType,
    String? archiveFormat,
    String? revisionId,
    String? publishedAt,
  }) {
    return _CodePackageArtifactLock(
      artifactUrl: artifactUrl,
      sha256: sha256,
      sizeBytes: sizeBytes,
      mediaType: mediaType,
      archiveFormat: archiveFormat,
      revisionId: revisionId,
      publishedAt: publishedAt,
    );
  }

  factory CodePackageArtifactLock.fromJson(Map<String, dynamic> json) =>
      _$CodePackageArtifactLockFromJson(json);
}

@freezed
abstract class CodePackageDescriptor with _$CodePackageDescriptor {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CodePackageDescriptor.def({
    required String packageName,
    @JsonKey(
      fromJson: CodeLanguageExtension.fromJson,
      toJson: CodeLanguageExtension.toJson,
    )
    required CodeLanguage language,
    required String surface,
    required String manifestKind,
    required String manifestRelativePath,
    required String packageRoot,
    String? sourcesRoot,
    String? fqnPrefix,
    String? version,
    String? revisionId,
    String? digest,
    String? artifactMediaType,
    int? artifactSizeBytes,
    String? downloadHandle,
    required Map<String, dynamic> metadata,
  }) = _CodePackageDescriptor;

  factory CodePackageDescriptor({
    required String packageName,
    required CodeLanguage language,
    required String surface,
    required String manifestKind,
    required String manifestRelativePath,
    required String packageRoot,
    String? sourcesRoot,
    String? fqnPrefix,
    String? version,
    String? revisionId,
    String? digest,
    String? artifactMediaType,
    int? artifactSizeBytes,
    String? downloadHandle,
    Map<String, dynamic>? metadata,
  }) {
    return _CodePackageDescriptor(
      packageName: packageName,
      language: language,
      surface: surface,
      manifestKind: manifestKind,
      manifestRelativePath: manifestRelativePath,
      packageRoot: packageRoot,
      sourcesRoot: sourcesRoot,
      fqnPrefix: fqnPrefix,
      version: version,
      revisionId: revisionId,
      digest: digest,
      artifactMediaType: artifactMediaType,
      artifactSizeBytes: artifactSizeBytes,
      downloadHandle: downloadHandle,
      metadata: metadata ?? {},
    );
  }

  factory CodePackageDescriptor.fromJson(Map<String, dynamic> json) =>
      _$CodePackageDescriptorFromJson({
        ...json,
        if (!json.containsKey('metadata')) 'metadata': {},
      });
}

@freezed
abstract class CodePackageChannelHead with _$CodePackageChannelHead {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CodePackageChannelHead.def({
    required String packageName,
    @JsonKey(
      fromJson: CodeLanguageExtension.fromJsonNullable,
      toJson: CodeLanguageExtension.toJsonNullable,
    )
    CodeLanguage? language,
    String? surface,
    required String channel,
    required String revisionId,
    String? updatedAt,
    String? publisherExecutionId,
    String? idempotencyKey,
    required Map<String, dynamic> metadata,
  }) = _CodePackageChannelHead;

  factory CodePackageChannelHead({
    required String packageName,
    CodeLanguage? language,
    String? surface,
    String? channel,
    required String revisionId,
    String? updatedAt,
    String? publisherExecutionId,
    String? idempotencyKey,
    Map<String, dynamic>? metadata,
  }) {
    return _CodePackageChannelHead(
      packageName: packageName,
      language: language,
      surface: surface,
      channel: channel ?? 'stable',
      revisionId: revisionId,
      updatedAt: updatedAt,
      publisherExecutionId: publisherExecutionId,
      idempotencyKey: idempotencyKey,
      metadata: metadata ?? {},
    );
  }

  factory CodePackageChannelHead.fromJson(Map<String, dynamic> json) =>
      _$CodePackageChannelHeadFromJson({
        ...json,
        if (!json.containsKey('channel')) 'channel': 'stable',
        if (!json.containsKey('metadata')) 'metadata': {},
      });
}

@freezed
abstract class CodePackageDiscoveryEntry with _$CodePackageDiscoveryEntry {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CodePackageDiscoveryEntry.def({
    required CodePackageChannelHead channelHead,
    CodePackageDescriptor? descriptor,
    CodePackageArtifactLock? artifactLock,
  }) = _CodePackageDiscoveryEntry;

  factory CodePackageDiscoveryEntry({
    required CodePackageChannelHead channelHead,
    CodePackageDescriptor? descriptor,
    CodePackageArtifactLock? artifactLock,
  }) {
    return _CodePackageDiscoveryEntry(
      channelHead: channelHead,
      descriptor: descriptor,
      artifactLock: artifactLock,
    );
  }

  factory CodePackageDiscoveryEntry.fromJson(Map<String, dynamic> json) =>
      _$CodePackageDiscoveryEntryFromJson(json);
}
