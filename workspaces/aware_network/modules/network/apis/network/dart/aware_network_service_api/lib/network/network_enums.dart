// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:json_annotation/json_annotation.dart';

part 'network_enums.g.dart';

/// Network protocol enums.
/// These live in the ontology (SSOT) because they are referenced by network
/// domain models and must be available when composing the runtime OCG without
/// any DTO/API packages.
@JsonEnum(fieldRename: FieldRename.snake, alwaysCreate: true)
enum NetworkAppType {
  environment,
  @JsonValue('interface')
  interface_,
  networkNode,
}

extension NetworkAppTypeExtension on NetworkAppType {
  static String toJson(NetworkAppType type) => _$NetworkAppTypeEnumMap[type]!;

  static NetworkAppType fromJson(String json) =>
      _$NetworkAppTypeEnumMap.map((key, value) => MapEntry(value, key))[json]!;

  static String? toJsonNullable(NetworkAppType? type) =>
      type == null ? null : toJson(type);

  static NetworkAppType? fromJsonNullable(String? json) =>
      json == null ? null : fromJson(json);
}

extension ListNetworkAppTypeExtension on List<NetworkAppType> {
  static List<String> toJson(List<NetworkAppType> values) =>
      values.map(NetworkAppTypeExtension.toJson).toList();

  static List<NetworkAppType> fromJson(List<dynamic> json) =>
      json.map((e) => NetworkAppTypeExtension.fromJson(e as String)).toList();

  static List<String>? toJsonNullable(List<NetworkAppType>? values) =>
      values == null ? null : toJson(values);

  static List<NetworkAppType>? fromJsonNullable(List<dynamic>? json) =>
      json == null ? null : fromJson(json);
}

extension SetNetworkAppTypeExtension on Set<NetworkAppType> {
  static List<String> toJson(Set<NetworkAppType> values) =>
      values.map(NetworkAppTypeExtension.toJson).toList();

  static Set<NetworkAppType> fromJson(List<dynamic> json) =>
      json.map((e) => NetworkAppTypeExtension.fromJson(e as String)).toSet();

  static List<String>? toJsonNullable(Set<NetworkAppType>? values) =>
      values == null ? null : toJson(values);

  static Set<NetworkAppType>? fromJsonNullable(List<dynamic>? json) =>
      json == null ? null : fromJson(json);
}

@JsonEnum(fieldRename: FieldRename.snake, alwaysCreate: true)
enum NetworkOperationMessageType { request, response, stream, notification }

extension NetworkOperationMessageTypeExtension on NetworkOperationMessageType {
  static String toJson(NetworkOperationMessageType type) =>
      _$NetworkOperationMessageTypeEnumMap[type]!;

  static NetworkOperationMessageType fromJson(String json) =>
      _$NetworkOperationMessageTypeEnumMap.map(
        (key, value) => MapEntry(value, key),
      )[json]!;

  static String? toJsonNullable(NetworkOperationMessageType? type) =>
      type == null ? null : toJson(type);

  static NetworkOperationMessageType? fromJsonNullable(String? json) =>
      json == null ? null : fromJson(json);
}

extension ListNetworkOperationMessageTypeExtension
    on List<NetworkOperationMessageType> {
  static List<String> toJson(List<NetworkOperationMessageType> values) =>
      values.map(NetworkOperationMessageTypeExtension.toJson).toList();

  static List<NetworkOperationMessageType> fromJson(List<dynamic> json) => json
      .map((e) => NetworkOperationMessageTypeExtension.fromJson(e as String))
      .toList();

  static List<String>? toJsonNullable(
    List<NetworkOperationMessageType>? values,
  ) => values == null ? null : toJson(values);

  static List<NetworkOperationMessageType>? fromJsonNullable(
    List<dynamic>? json,
  ) => json == null ? null : fromJson(json);
}

extension SetNetworkOperationMessageTypeExtension
    on Set<NetworkOperationMessageType> {
  static List<String> toJson(Set<NetworkOperationMessageType> values) =>
      values.map(NetworkOperationMessageTypeExtension.toJson).toList();

  static Set<NetworkOperationMessageType> fromJson(List<dynamic> json) => json
      .map((e) => NetworkOperationMessageTypeExtension.fromJson(e as String))
      .toSet();

  static List<String>? toJsonNullable(
    Set<NetworkOperationMessageType>? values,
  ) => values == null ? null : toJson(values);

  static Set<NetworkOperationMessageType>? fromJsonNullable(
    List<dynamic>? json,
  ) => json == null ? null : fromJson(json);
}

@JsonEnum(fieldRename: FieldRename.snake, alwaysCreate: true)
enum NetworkOperationType {
  api,
  environment,
  environmentConfig,
  service,
  networkNode,
}

extension NetworkOperationTypeExtension on NetworkOperationType {
  static String toJson(NetworkOperationType type) =>
      _$NetworkOperationTypeEnumMap[type]!;

  static NetworkOperationType fromJson(String json) =>
      _$NetworkOperationTypeEnumMap.map(
        (key, value) => MapEntry(value, key),
      )[json]!;

  static String? toJsonNullable(NetworkOperationType? type) =>
      type == null ? null : toJson(type);

  static NetworkOperationType? fromJsonNullable(String? json) =>
      json == null ? null : fromJson(json);
}

extension ListNetworkOperationTypeExtension on List<NetworkOperationType> {
  static List<String> toJson(List<NetworkOperationType> values) =>
      values.map(NetworkOperationTypeExtension.toJson).toList();

  static List<NetworkOperationType> fromJson(List<dynamic> json) => json
      .map((e) => NetworkOperationTypeExtension.fromJson(e as String))
      .toList();

  static List<String>? toJsonNullable(List<NetworkOperationType>? values) =>
      values == null ? null : toJson(values);

  static List<NetworkOperationType>? fromJsonNullable(List<dynamic>? json) =>
      json == null ? null : fromJson(json);
}

extension SetNetworkOperationTypeExtension on Set<NetworkOperationType> {
  static List<String> toJson(Set<NetworkOperationType> values) =>
      values.map(NetworkOperationTypeExtension.toJson).toList();

  static Set<NetworkOperationType> fromJson(List<dynamic> json) => json
      .map((e) => NetworkOperationTypeExtension.fromJson(e as String))
      .toSet();

  static List<String>? toJsonNullable(Set<NetworkOperationType>? values) =>
      values == null ? null : toJson(values);

  static Set<NetworkOperationType>? fromJsonNullable(List<dynamic>? json) =>
      json == null ? null : fromJson(json);
}

@JsonEnum(fieldRename: FieldRename.snake, alwaysCreate: true)
enum NetworkRequestStatus { accepted, pending, rejected, succeeded, failed }

extension NetworkRequestStatusExtension on NetworkRequestStatus {
  static String toJson(NetworkRequestStatus type) =>
      _$NetworkRequestStatusEnumMap[type]!;

  static NetworkRequestStatus fromJson(String json) =>
      _$NetworkRequestStatusEnumMap.map(
        (key, value) => MapEntry(value, key),
      )[json]!;

  static String? toJsonNullable(NetworkRequestStatus? type) =>
      type == null ? null : toJson(type);

  static NetworkRequestStatus? fromJsonNullable(String? json) =>
      json == null ? null : fromJson(json);
}

extension ListNetworkRequestStatusExtension on List<NetworkRequestStatus> {
  static List<String> toJson(List<NetworkRequestStatus> values) =>
      values.map(NetworkRequestStatusExtension.toJson).toList();

  static List<NetworkRequestStatus> fromJson(List<dynamic> json) => json
      .map((e) => NetworkRequestStatusExtension.fromJson(e as String))
      .toList();

  static List<String>? toJsonNullable(List<NetworkRequestStatus>? values) =>
      values == null ? null : toJson(values);

  static List<NetworkRequestStatus>? fromJsonNullable(List<dynamic>? json) =>
      json == null ? null : fromJson(json);
}

extension SetNetworkRequestStatusExtension on Set<NetworkRequestStatus> {
  static List<String> toJson(Set<NetworkRequestStatus> values) =>
      values.map(NetworkRequestStatusExtension.toJson).toList();

  static Set<NetworkRequestStatus> fromJson(List<dynamic> json) => json
      .map((e) => NetworkRequestStatusExtension.fromJson(e as String))
      .toSet();

  static List<String>? toJsonNullable(Set<NetworkRequestStatus>? values) =>
      values == null ? null : toJson(values);

  static Set<NetworkRequestStatus>? fromJsonNullable(List<dynamic>? json) =>
      json == null ? null : fromJson(json);
}
