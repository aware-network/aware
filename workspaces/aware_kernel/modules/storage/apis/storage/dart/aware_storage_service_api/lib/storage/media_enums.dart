// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:json_annotation/json_annotation.dart';

part 'media_enums.g.dart';

/// Storage media DTOs.
/// Contract:
/// - Blob bytes are data-plane payloads and are not embedded in generated API
/// JSON requests or responses.
/// - StorageBlob metadata remains the commit-backed reference truth.
/// - Renderers resolve media through Storage API descriptors and then fetch
/// bytes through a Storage-owned data-plane transport.
@JsonEnum(fieldRename: FieldRename.snake, alwaysCreate: true)
enum StorageMediaDisposition { inline, attachment }

extension StorageMediaDispositionExtension on StorageMediaDisposition {
  static String toJson(StorageMediaDisposition type) =>
      _$StorageMediaDispositionEnumMap[type]!;

  static StorageMediaDisposition fromJson(String json) =>
      _$StorageMediaDispositionEnumMap.map(
        (key, value) => MapEntry(value, key),
      )[json]!;

  static String? toJsonNullable(StorageMediaDisposition? type) =>
      type == null ? null : toJson(type);

  static StorageMediaDisposition? fromJsonNullable(String? json) =>
      json == null ? null : fromJson(json);
}

extension ListStorageMediaDispositionExtension
    on List<StorageMediaDisposition> {
  static List<String> toJson(List<StorageMediaDisposition> values) =>
      values.map(StorageMediaDispositionExtension.toJson).toList();

  static List<StorageMediaDisposition> fromJson(List<dynamic> json) => json
      .map((e) => StorageMediaDispositionExtension.fromJson(e as String))
      .toList();

  static List<String>? toJsonNullable(List<StorageMediaDisposition>? values) =>
      values == null ? null : toJson(values);

  static List<StorageMediaDisposition>? fromJsonNullable(List<dynamic>? json) =>
      json == null ? null : fromJson(json);
}

extension SetStorageMediaDispositionExtension on Set<StorageMediaDisposition> {
  static List<String> toJson(Set<StorageMediaDisposition> values) =>
      values.map(StorageMediaDispositionExtension.toJson).toList();

  static Set<StorageMediaDisposition> fromJson(List<dynamic> json) => json
      .map((e) => StorageMediaDispositionExtension.fromJson(e as String))
      .toSet();

  static List<String>? toJsonNullable(Set<StorageMediaDisposition>? values) =>
      values == null ? null : toJson(values);

  static Set<StorageMediaDisposition>? fromJsonNullable(List<dynamic>? json) =>
      json == null ? null : fromJson(json);
}
