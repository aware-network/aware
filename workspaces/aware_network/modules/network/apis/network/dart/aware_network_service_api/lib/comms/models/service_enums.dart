// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:json_annotation/json_annotation.dart';

part 'service_enums.g.dart';

/// Canonical Service operation DTOs (transport-layer, graph/ORM agnostic).
/// SSOT: `service-service-dto` generated from this API-owned `.aware` contract.
/// `aware_comms` may re-export these DTOs for transport/service import
/// stability, but schema ownership remains under `apis/service/dto`.
@JsonEnum(fieldRename: FieldRename.snake, alwaysCreate: true)
enum RequestStatus { succeeded, failed, pending }

extension RequestStatusExtension on RequestStatus {
  static String toJson(RequestStatus type) => _$RequestStatusEnumMap[type]!;

  static RequestStatus fromJson(String json) =>
      _$RequestStatusEnumMap.map((key, value) => MapEntry(value, key))[json]!;

  static String? toJsonNullable(RequestStatus? type) =>
      type == null ? null : toJson(type);

  static RequestStatus? fromJsonNullable(String? json) =>
      json == null ? null : fromJson(json);
}

extension ListRequestStatusExtension on List<RequestStatus> {
  static List<String> toJson(List<RequestStatus> values) =>
      values.map(RequestStatusExtension.toJson).toList();

  static List<RequestStatus> fromJson(List<dynamic> json) =>
      json.map((e) => RequestStatusExtension.fromJson(e as String)).toList();

  static List<String>? toJsonNullable(List<RequestStatus>? values) =>
      values == null ? null : toJson(values);

  static List<RequestStatus>? fromJsonNullable(List<dynamic>? json) =>
      json == null ? null : fromJson(json);
}

extension SetRequestStatusExtension on Set<RequestStatus> {
  static List<String> toJson(Set<RequestStatus> values) =>
      values.map(RequestStatusExtension.toJson).toList();

  static Set<RequestStatus> fromJson(List<dynamic> json) =>
      json.map((e) => RequestStatusExtension.fromJson(e as String)).toSet();

  static List<String>? toJsonNullable(Set<RequestStatus>? values) =>
      values == null ? null : toJson(values);

  static Set<RequestStatus>? fromJsonNullable(List<dynamic>? json) =>
      json == null ? null : fromJson(json);
}

@JsonEnum(fieldRename: FieldRename.snake, alwaysCreate: true)
enum StreamLifecycle { autoClose, started, closed }

extension StreamLifecycleExtension on StreamLifecycle {
  static String toJson(StreamLifecycle type) => _$StreamLifecycleEnumMap[type]!;

  static StreamLifecycle fromJson(String json) =>
      _$StreamLifecycleEnumMap.map((key, value) => MapEntry(value, key))[json]!;

  static String? toJsonNullable(StreamLifecycle? type) =>
      type == null ? null : toJson(type);

  static StreamLifecycle? fromJsonNullable(String? json) =>
      json == null ? null : fromJson(json);
}

extension ListStreamLifecycleExtension on List<StreamLifecycle> {
  static List<String> toJson(List<StreamLifecycle> values) =>
      values.map(StreamLifecycleExtension.toJson).toList();

  static List<StreamLifecycle> fromJson(List<dynamic> json) =>
      json.map((e) => StreamLifecycleExtension.fromJson(e as String)).toList();

  static List<String>? toJsonNullable(List<StreamLifecycle>? values) =>
      values == null ? null : toJson(values);

  static List<StreamLifecycle>? fromJsonNullable(List<dynamic>? json) =>
      json == null ? null : fromJson(json);
}

extension SetStreamLifecycleExtension on Set<StreamLifecycle> {
  static List<String> toJson(Set<StreamLifecycle> values) =>
      values.map(StreamLifecycleExtension.toJson).toList();

  static Set<StreamLifecycle> fromJson(List<dynamic> json) =>
      json.map((e) => StreamLifecycleExtension.fromJson(e as String)).toSet();

  static List<String>? toJsonNullable(Set<StreamLifecycle>? values) =>
      values == null ? null : toJson(values);

  static Set<StreamLifecycle>? fromJsonNullable(List<dynamic>? json) =>
      json == null ? null : fromJson(json);
}
