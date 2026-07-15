// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'mount_status_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_InterfaceMountStatusViewStateV1 _$InterfaceMountStatusViewStateV1FromJson(
  Map<String, dynamic> json,
) => _InterfaceMountStatusViewStateV1(
  mounted: json['mounted'] as bool,
  ready: json['ready'] as bool,
  status: json['status'] as String,
  summary: json['summary'] as String?,
  error: json['error'] as String?,
  activeLayoutKey: json['active_layout_key'] as String?,
  activeSectionKey: json['active_section_key'] as String?,
);

Map<String, dynamic> _$InterfaceMountStatusViewStateV1ToJson(
  _InterfaceMountStatusViewStateV1 instance,
) => <String, dynamic>{
  'mounted': instance.mounted,
  'ready': instance.ready,
  'status': instance.status,
  'summary': instance.summary,
  'error': instance.error,
  'active_layout_key': instance.activeLayoutKey,
  'active_section_key': instance.activeSectionKey,
};
