// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:freezed_annotation/freezed_annotation.dart';

part 'session_status_model.freezed.dart';
part 'session_status_model.g.dart';

/// API-owned view-state contract for NetworkNode session readiness.
/// Public API view key: network.session_status
@freezed
abstract class NetworkNodeSessionStatusViewStateV1
    with _$NetworkNodeSessionStatusViewStateV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeSessionStatusViewStateV1.def({
    required bool managed,
    required bool available,
    required bool ready,
    required String phase,
    String? activeTargetId,
    String? targetKey,
    String? displayName,
    String? backendKind,
    String? summary,
    String? error,
    @Default(const []) List<String> recentLogLines,
    @Default(const []) List<Map<String, dynamic>> targetStatuses,
  }) = _NetworkNodeSessionStatusViewStateV1;

  factory NetworkNodeSessionStatusViewStateV1({
    bool? managed,
    bool? available,
    bool? ready,
    String? phase,
    String? activeTargetId,
    String? targetKey,
    String? displayName,
    String? backendKind,
    String? summary,
    String? error,
    List<String> recentLogLines = const [],
    List<Map<String, dynamic>> targetStatuses = const [],
  }) {
    return _NetworkNodeSessionStatusViewStateV1(
      managed: managed ?? false,
      available: available ?? false,
      ready: ready ?? false,
      phase: phase ?? 'idle',
      activeTargetId: activeTargetId,
      targetKey: targetKey,
      displayName: displayName,
      backendKind: backendKind,
      summary: summary,
      error: error,
      recentLogLines: recentLogLines,
      targetStatuses: targetStatuses,
    );
  }

  factory NetworkNodeSessionStatusViewStateV1.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkNodeSessionStatusViewStateV1FromJson({
    ...json,
    if (!json.containsKey('managed')) 'managed': false,
    if (!json.containsKey('available')) 'available': false,
    if (!json.containsKey('ready')) 'ready': false,
    if (!json.containsKey('phase')) 'phase': 'idle',
  });
}
