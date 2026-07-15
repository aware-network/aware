// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'session_status_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_NetworkNodeSessionStatusViewStateV1
_$NetworkNodeSessionStatusViewStateV1FromJson(Map<String, dynamic> json) =>
    _NetworkNodeSessionStatusViewStateV1(
      managed: json['managed'] as bool,
      available: json['available'] as bool,
      ready: json['ready'] as bool,
      phase: json['phase'] as String,
      activeTargetId: json['active_target_id'] as String?,
      targetKey: json['target_key'] as String?,
      displayName: json['display_name'] as String?,
      backendKind: json['backend_kind'] as String?,
      summary: json['summary'] as String?,
      error: json['error'] as String?,
      recentLogLines:
          (json['recent_log_lines'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      targetStatuses:
          (json['target_statuses'] as List<dynamic>?)
              ?.map((e) => e as Map<String, dynamic>)
              .toList() ??
          const [],
    );

Map<String, dynamic> _$NetworkNodeSessionStatusViewStateV1ToJson(
  _NetworkNodeSessionStatusViewStateV1 instance,
) => <String, dynamic>{
  'managed': instance.managed,
  'available': instance.available,
  'ready': instance.ready,
  'phase': instance.phase,
  'active_target_id': instance.activeTargetId,
  'target_key': instance.targetKey,
  'display_name': instance.displayName,
  'backend_kind': instance.backendKind,
  'summary': instance.summary,
  'error': instance.error,
  'recent_log_lines': instance.recentLogLines,
  'target_statuses': instance.targetStatuses,
};
