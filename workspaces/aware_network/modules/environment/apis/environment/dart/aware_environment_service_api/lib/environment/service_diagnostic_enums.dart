// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:json_annotation/json_annotation.dart';

part 'service_diagnostic_enums.g.dart';

/// SSOT: `environment-service-dto` generated from `apis/environment/dto`.
@JsonEnum(fieldRename: FieldRename.snake, alwaysCreate: true)
enum ServiceDiagnosticCategory { runtimeInvariant, internalFailure }

extension ServiceDiagnosticCategoryExtension on ServiceDiagnosticCategory {
  static String toJson(ServiceDiagnosticCategory type) =>
      _$ServiceDiagnosticCategoryEnumMap[type]!;

  static ServiceDiagnosticCategory fromJson(String json) =>
      _$ServiceDiagnosticCategoryEnumMap.map(
        (key, value) => MapEntry(value, key),
      )[json]!;

  static String? toJsonNullable(ServiceDiagnosticCategory? type) =>
      type == null ? null : toJson(type);

  static ServiceDiagnosticCategory? fromJsonNullable(String? json) =>
      json == null ? null : fromJson(json);
}

extension ListServiceDiagnosticCategoryExtension
    on List<ServiceDiagnosticCategory> {
  static List<String> toJson(List<ServiceDiagnosticCategory> values) =>
      values.map(ServiceDiagnosticCategoryExtension.toJson).toList();

  static List<ServiceDiagnosticCategory> fromJson(List<dynamic> json) => json
      .map((e) => ServiceDiagnosticCategoryExtension.fromJson(e as String))
      .toList();

  static List<String>? toJsonNullable(
    List<ServiceDiagnosticCategory>? values,
  ) => values == null ? null : toJson(values);

  static List<ServiceDiagnosticCategory>? fromJsonNullable(
    List<dynamic>? json,
  ) => json == null ? null : fromJson(json);
}

extension SetServiceDiagnosticCategoryExtension
    on Set<ServiceDiagnosticCategory> {
  static List<String> toJson(Set<ServiceDiagnosticCategory> values) =>
      values.map(ServiceDiagnosticCategoryExtension.toJson).toList();

  static Set<ServiceDiagnosticCategory> fromJson(List<dynamic> json) => json
      .map((e) => ServiceDiagnosticCategoryExtension.fromJson(e as String))
      .toSet();

  static List<String>? toJsonNullable(Set<ServiceDiagnosticCategory>? values) =>
      values == null ? null : toJson(values);

  static Set<ServiceDiagnosticCategory>? fromJsonNullable(
    List<dynamic>? json,
  ) => json == null ? null : fromJson(json);
}

@JsonEnum(fieldRename: FieldRename.snake, alwaysCreate: true)
enum ServiceDiagnosticSeverity { info, warning, error, critical }

extension ServiceDiagnosticSeverityExtension on ServiceDiagnosticSeverity {
  static String toJson(ServiceDiagnosticSeverity type) =>
      _$ServiceDiagnosticSeverityEnumMap[type]!;

  static ServiceDiagnosticSeverity fromJson(String json) =>
      _$ServiceDiagnosticSeverityEnumMap.map(
        (key, value) => MapEntry(value, key),
      )[json]!;

  static String? toJsonNullable(ServiceDiagnosticSeverity? type) =>
      type == null ? null : toJson(type);

  static ServiceDiagnosticSeverity? fromJsonNullable(String? json) =>
      json == null ? null : fromJson(json);
}

extension ListServiceDiagnosticSeverityExtension
    on List<ServiceDiagnosticSeverity> {
  static List<String> toJson(List<ServiceDiagnosticSeverity> values) =>
      values.map(ServiceDiagnosticSeverityExtension.toJson).toList();

  static List<ServiceDiagnosticSeverity> fromJson(List<dynamic> json) => json
      .map((e) => ServiceDiagnosticSeverityExtension.fromJson(e as String))
      .toList();

  static List<String>? toJsonNullable(
    List<ServiceDiagnosticSeverity>? values,
  ) => values == null ? null : toJson(values);

  static List<ServiceDiagnosticSeverity>? fromJsonNullable(
    List<dynamic>? json,
  ) => json == null ? null : fromJson(json);
}

extension SetServiceDiagnosticSeverityExtension
    on Set<ServiceDiagnosticSeverity> {
  static List<String> toJson(Set<ServiceDiagnosticSeverity> values) =>
      values.map(ServiceDiagnosticSeverityExtension.toJson).toList();

  static Set<ServiceDiagnosticSeverity> fromJson(List<dynamic> json) => json
      .map((e) => ServiceDiagnosticSeverityExtension.fromJson(e as String))
      .toSet();

  static List<String>? toJsonNullable(Set<ServiceDiagnosticSeverity>? values) =>
      values == null ? null : toJson(values);

  static Set<ServiceDiagnosticSeverity>? fromJsonNullable(
    List<dynamic>? json,
  ) => json == null ? null : fromJson(json);
}

@JsonEnum(fieldRename: FieldRename.snake, alwaysCreate: true)
enum ServiceDiagnosticResolutionStatus { unresolved, partial, resolved }

extension ServiceDiagnosticResolutionStatusExtension
    on ServiceDiagnosticResolutionStatus {
  static String toJson(ServiceDiagnosticResolutionStatus type) =>
      _$ServiceDiagnosticResolutionStatusEnumMap[type]!;

  static ServiceDiagnosticResolutionStatus fromJson(String json) =>
      _$ServiceDiagnosticResolutionStatusEnumMap.map(
        (key, value) => MapEntry(value, key),
      )[json]!;

  static String? toJsonNullable(ServiceDiagnosticResolutionStatus? type) =>
      type == null ? null : toJson(type);

  static ServiceDiagnosticResolutionStatus? fromJsonNullable(String? json) =>
      json == null ? null : fromJson(json);
}

extension ListServiceDiagnosticResolutionStatusExtension
    on List<ServiceDiagnosticResolutionStatus> {
  static List<String> toJson(List<ServiceDiagnosticResolutionStatus> values) =>
      values.map(ServiceDiagnosticResolutionStatusExtension.toJson).toList();

  static List<ServiceDiagnosticResolutionStatus> fromJson(List<dynamic> json) =>
      json
          .map(
            (e) => ServiceDiagnosticResolutionStatusExtension.fromJson(
              e as String,
            ),
          )
          .toList();

  static List<String>? toJsonNullable(
    List<ServiceDiagnosticResolutionStatus>? values,
  ) => values == null ? null : toJson(values);

  static List<ServiceDiagnosticResolutionStatus>? fromJsonNullable(
    List<dynamic>? json,
  ) => json == null ? null : fromJson(json);
}

extension SetServiceDiagnosticResolutionStatusExtension
    on Set<ServiceDiagnosticResolutionStatus> {
  static List<String> toJson(Set<ServiceDiagnosticResolutionStatus> values) =>
      values.map(ServiceDiagnosticResolutionStatusExtension.toJson).toList();

  static Set<ServiceDiagnosticResolutionStatus> fromJson(List<dynamic> json) =>
      json
          .map(
            (e) => ServiceDiagnosticResolutionStatusExtension.fromJson(
              e as String,
            ),
          )
          .toSet();

  static List<String>? toJsonNullable(
    Set<ServiceDiagnosticResolutionStatus>? values,
  ) => values == null ? null : toJson(values);

  static Set<ServiceDiagnosticResolutionStatus>? fromJsonNullable(
    List<dynamic>? json,
  ) => json == null ? null : fromJson(json);
}
