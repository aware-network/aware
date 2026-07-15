// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:json_annotation/json_annotation.dart';

part 'node_deploy_operation_enums.g.dart';

/// Transport-agnostic DTOs for pre-node deploy supervisor operations.
/// IMPORTANT:
/// - This contract is a peer rail to live-node `NetworkNodeOperation`.
/// - It exists before a node websocket is available.
/// - `local` vs `remote` remains a transport/backend concern, not an API fork.
@JsonEnum(fieldRename: FieldRename.snake, alwaysCreate: true)
enum NodeDeployRuntimePhase {
  idle,
  startingBundle,
  startDb,
  startingEnvironment,
  waitingEnvironment,
  startingNode,
  waitingNode,
  ready,
  failed,
}

extension NodeDeployRuntimePhaseExtension on NodeDeployRuntimePhase {
  static String toJson(NodeDeployRuntimePhase type) =>
      _$NodeDeployRuntimePhaseEnumMap[type]!;

  static NodeDeployRuntimePhase fromJson(String json) =>
      _$NodeDeployRuntimePhaseEnumMap.map(
        (key, value) => MapEntry(value, key),
      )[json]!;

  static String? toJsonNullable(NodeDeployRuntimePhase? type) =>
      type == null ? null : toJson(type);

  static NodeDeployRuntimePhase? fromJsonNullable(String? json) =>
      json == null ? null : fromJson(json);
}

extension ListNodeDeployRuntimePhaseExtension on List<NodeDeployRuntimePhase> {
  static List<String> toJson(List<NodeDeployRuntimePhase> values) =>
      values.map(NodeDeployRuntimePhaseExtension.toJson).toList();

  static List<NodeDeployRuntimePhase> fromJson(List<dynamic> json) => json
      .map((e) => NodeDeployRuntimePhaseExtension.fromJson(e as String))
      .toList();

  static List<String>? toJsonNullable(List<NodeDeployRuntimePhase>? values) =>
      values == null ? null : toJson(values);

  static List<NodeDeployRuntimePhase>? fromJsonNullable(List<dynamic>? json) =>
      json == null ? null : fromJson(json);
}

extension SetNodeDeployRuntimePhaseExtension on Set<NodeDeployRuntimePhase> {
  static List<String> toJson(Set<NodeDeployRuntimePhase> values) =>
      values.map(NodeDeployRuntimePhaseExtension.toJson).toList();

  static Set<NodeDeployRuntimePhase> fromJson(List<dynamic> json) => json
      .map((e) => NodeDeployRuntimePhaseExtension.fromJson(e as String))
      .toSet();

  static List<String>? toJsonNullable(Set<NodeDeployRuntimePhase>? values) =>
      values == null ? null : toJson(values);

  static Set<NodeDeployRuntimePhase>? fromJsonNullable(List<dynamic>? json) =>
      json == null ? null : fromJson(json);
}
