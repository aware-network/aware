// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:json_annotation/json_annotation.dart';

part 'package_distribution_enums.g.dart';

/// CodePackage distribution DTOs for Product A consumers.
/// Contract:
/// - Hub can expose search/describe/resolve/download/publish over these DTOs.
/// - The DTOs describe package artifact truth and replay locks, not executable
/// plugin activation.
/// - Publish registers an already-staged artifact lock with Hub authority truth;
/// binary upload/storage transport is intentionally separate.
/// - CodeModule/module aggregate layout is intentionally out of scope here.
@JsonEnum(fieldRename: FieldRename.snake, alwaysCreate: true)
enum CodeLanguage { aware, dart, python, sql }

extension CodeLanguageExtension on CodeLanguage {
  static String toJson(CodeLanguage type) => _$CodeLanguageEnumMap[type]!;

  static CodeLanguage fromJson(String json) =>
      _$CodeLanguageEnumMap.map((key, value) => MapEntry(value, key))[json]!;

  static String? toJsonNullable(CodeLanguage? type) =>
      type == null ? null : toJson(type);

  static CodeLanguage? fromJsonNullable(String? json) =>
      json == null ? null : fromJson(json);
}

extension ListCodeLanguageExtension on List<CodeLanguage> {
  static List<String> toJson(List<CodeLanguage> values) =>
      values.map(CodeLanguageExtension.toJson).toList();

  static List<CodeLanguage> fromJson(List<dynamic> json) =>
      json.map((e) => CodeLanguageExtension.fromJson(e as String)).toList();

  static List<String>? toJsonNullable(List<CodeLanguage>? values) =>
      values == null ? null : toJson(values);

  static List<CodeLanguage>? fromJsonNullable(List<dynamic>? json) =>
      json == null ? null : fromJson(json);
}

extension SetCodeLanguageExtension on Set<CodeLanguage> {
  static List<String> toJson(Set<CodeLanguage> values) =>
      values.map(CodeLanguageExtension.toJson).toList();

  static Set<CodeLanguage> fromJson(List<dynamic> json) =>
      json.map((e) => CodeLanguageExtension.fromJson(e as String)).toSet();

  static List<String>? toJsonNullable(Set<CodeLanguage>? values) =>
      values == null ? null : toJson(values);

  static Set<CodeLanguage>? fromJsonNullable(List<dynamic>? json) =>
      json == null ? null : fromJson(json);
}
