// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:freezed_annotation/freezed_annotation.dart';

part 'mount_status_model.freezed.dart';
part 'mount_status_model.g.dart';

/// API-owned view-state contract for Interface package mount readiness.
/// Public API view key: interface.package_mount_status
@freezed
abstract class InterfaceMountStatusViewStateV1
    with _$InterfaceMountStatusViewStateV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceMountStatusViewStateV1.def({
    required bool mounted,
    required bool ready,
    required String status,
    String? summary,
    String? error,
    String? activeLayoutKey,
    String? activeSectionKey,
  }) = _InterfaceMountStatusViewStateV1;

  factory InterfaceMountStatusViewStateV1({
    bool? mounted,
    bool? ready,
    String? status,
    String? summary,
    String? error,
    String? activeLayoutKey,
    String? activeSectionKey,
  }) {
    return _InterfaceMountStatusViewStateV1(
      mounted: mounted ?? false,
      ready: ready ?? false,
      status: status ?? 'unknown',
      summary: summary,
      error: error,
      activeLayoutKey: activeLayoutKey,
      activeSectionKey: activeSectionKey,
    );
  }

  factory InterfaceMountStatusViewStateV1.fromJson(Map<String, dynamic> json) =>
      _$InterfaceMountStatusViewStateV1FromJson({
        ...json,
        if (!json.containsKey('mounted')) 'mounted': false,
        if (!json.containsKey('ready')) 'ready': false,
        if (!json.containsKey('status')) 'status': 'unknown',
      });
}
