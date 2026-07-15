// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:json_annotation/json_annotation.dart';

part 'environment_enums.g.dart';

@JsonEnum(fieldRename: FieldRename.snake, alwaysCreate: true)
enum InvokeFunctionCallTarget { instance, opgConstructor }

extension InvokeFunctionCallTargetExtension on InvokeFunctionCallTarget {
  static String toJson(InvokeFunctionCallTarget type) =>
      _$InvokeFunctionCallTargetEnumMap[type]!;

  static InvokeFunctionCallTarget fromJson(String json) =>
      _$InvokeFunctionCallTargetEnumMap.map(
        (key, value) => MapEntry(value, key),
      )[json]!;

  static String? toJsonNullable(InvokeFunctionCallTarget? type) =>
      type == null ? null : toJson(type);

  static InvokeFunctionCallTarget? fromJsonNullable(String? json) =>
      json == null ? null : fromJson(json);
}

extension ListInvokeFunctionCallTargetExtension
    on List<InvokeFunctionCallTarget> {
  static List<String> toJson(List<InvokeFunctionCallTarget> values) =>
      values.map(InvokeFunctionCallTargetExtension.toJson).toList();

  static List<InvokeFunctionCallTarget> fromJson(List<dynamic> json) => json
      .map((e) => InvokeFunctionCallTargetExtension.fromJson(e as String))
      .toList();

  static List<String>? toJsonNullable(List<InvokeFunctionCallTarget>? values) =>
      values == null ? null : toJson(values);

  static List<InvokeFunctionCallTarget>? fromJsonNullable(
    List<dynamic>? json,
  ) => json == null ? null : fromJson(json);
}

extension SetInvokeFunctionCallTargetExtension
    on Set<InvokeFunctionCallTarget> {
  static List<String> toJson(Set<InvokeFunctionCallTarget> values) =>
      values.map(InvokeFunctionCallTargetExtension.toJson).toList();

  static Set<InvokeFunctionCallTarget> fromJson(List<dynamic> json) => json
      .map((e) => InvokeFunctionCallTargetExtension.fromJson(e as String))
      .toSet();

  static List<String>? toJsonNullable(Set<InvokeFunctionCallTarget>? values) =>
      values == null ? null : toJson(values);

  static Set<InvokeFunctionCallTarget>? fromJsonNullable(List<dynamic>? json) =>
      json == null ? null : fromJson(json);
}

@JsonEnum(fieldRename: FieldRename.snake, alwaysCreate: true)
enum EnvironmentStatusAuthorityKind {
  environmentInterfaceView,
  localFsView,
  commitTruth,
  mixed,
}

extension EnvironmentStatusAuthorityKindExtension
    on EnvironmentStatusAuthorityKind {
  static String toJson(EnvironmentStatusAuthorityKind type) =>
      _$EnvironmentStatusAuthorityKindEnumMap[type]!;

  static EnvironmentStatusAuthorityKind fromJson(String json) =>
      _$EnvironmentStatusAuthorityKindEnumMap.map(
        (key, value) => MapEntry(value, key),
      )[json]!;

  static String? toJsonNullable(EnvironmentStatusAuthorityKind? type) =>
      type == null ? null : toJson(type);

  static EnvironmentStatusAuthorityKind? fromJsonNullable(String? json) =>
      json == null ? null : fromJson(json);
}

extension ListEnvironmentStatusAuthorityKindExtension
    on List<EnvironmentStatusAuthorityKind> {
  static List<String> toJson(List<EnvironmentStatusAuthorityKind> values) =>
      values.map(EnvironmentStatusAuthorityKindExtension.toJson).toList();

  static List<EnvironmentStatusAuthorityKind> fromJson(List<dynamic> json) =>
      json
          .map(
            (e) =>
                EnvironmentStatusAuthorityKindExtension.fromJson(e as String),
          )
          .toList();

  static List<String>? toJsonNullable(
    List<EnvironmentStatusAuthorityKind>? values,
  ) => values == null ? null : toJson(values);

  static List<EnvironmentStatusAuthorityKind>? fromJsonNullable(
    List<dynamic>? json,
  ) => json == null ? null : fromJson(json);
}

extension SetEnvironmentStatusAuthorityKindExtension
    on Set<EnvironmentStatusAuthorityKind> {
  static List<String> toJson(Set<EnvironmentStatusAuthorityKind> values) =>
      values.map(EnvironmentStatusAuthorityKindExtension.toJson).toList();

  static Set<EnvironmentStatusAuthorityKind> fromJson(List<dynamic> json) =>
      json
          .map(
            (e) =>
                EnvironmentStatusAuthorityKindExtension.fromJson(e as String),
          )
          .toSet();

  static List<String>? toJsonNullable(
    Set<EnvironmentStatusAuthorityKind>? values,
  ) => values == null ? null : toJson(values);

  static Set<EnvironmentStatusAuthorityKind>? fromJsonNullable(
    List<dynamic>? json,
  ) => json == null ? null : fromJson(json);
}
