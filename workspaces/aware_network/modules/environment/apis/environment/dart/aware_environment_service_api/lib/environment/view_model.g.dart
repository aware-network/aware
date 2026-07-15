// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'view_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_EnvironmentStatusBlockSummaryV1 _$EnvironmentStatusBlockSummaryV1FromJson(
  Map<String, dynamic> json,
) => _EnvironmentStatusBlockSummaryV1(
  name: json['name'] as String,
  available: json['available'] as bool,
  authorityKind: json['authority_kind'] as String?,
  unavailableReason: json['unavailable_reason'] as String?,
  payload: json['payload'] as Map<String, dynamic>,
);

Map<String, dynamic> _$EnvironmentStatusBlockSummaryV1ToJson(
  _EnvironmentStatusBlockSummaryV1 instance,
) => <String, dynamic>{
  'name': instance.name,
  'available': instance.available,
  'authority_kind': instance.authorityKind,
  'unavailable_reason': instance.unavailableReason,
  'payload': instance.payload,
};

_EnvironmentThreadNavigationItemV1 _$EnvironmentThreadNavigationItemV1FromJson(
  Map<String, dynamic> json,
) => _EnvironmentThreadNavigationItemV1(
  threadId: _$JsonConverterFromJson<String, UuidValue>(
    json['thread_id'],
    const UuidValueConverter().fromJson,
  ),
  threadKey: json['thread_key'] as String?,
  title: json['title'] as String,
  description: json['description'] as String?,
  attachmentCount: (json['attachment_count'] as num).toInt(),
  activeAttachmentCount: (json['active_attachment_count'] as num).toInt(),
  isSelected: json['is_selected'] as bool,
);

Map<String, dynamic> _$EnvironmentThreadNavigationItemV1ToJson(
  _EnvironmentThreadNavigationItemV1 instance,
) => <String, dynamic>{
  'thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadId,
    const UuidValueConverter().toJson,
  ),
  'thread_key': instance.threadKey,
  'title': instance.title,
  'description': instance.description,
  'attachment_count': instance.attachmentCount,
  'active_attachment_count': instance.activeAttachmentCount,
  'is_selected': instance.isSelected,
};

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);

_EnvironmentProcessNavigationItemV1
_$EnvironmentProcessNavigationItemV1FromJson(Map<String, dynamic> json) =>
    _EnvironmentProcessNavigationItemV1(
      processId: _$JsonConverterFromJson<String, UuidValue>(
        json['process_id'],
        const UuidValueConverter().fromJson,
      ),
      processKey: json['process_key'] as String?,
      title: json['title'] as String,
      description: json['description'] as String?,
      threadCount: (json['thread_count'] as num).toInt(),
      isSelected: json['is_selected'] as bool,
      threads:
          (json['threads'] as List<dynamic>?)
              ?.map(
                (e) => EnvironmentThreadNavigationItemV1.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
    );

Map<String, dynamic> _$EnvironmentProcessNavigationItemV1ToJson(
  _EnvironmentProcessNavigationItemV1 instance,
) => <String, dynamic>{
  'process_id': _$JsonConverterToJson<String, UuidValue>(
    instance.processId,
    const UuidValueConverter().toJson,
  ),
  'process_key': instance.processKey,
  'title': instance.title,
  'description': instance.description,
  'thread_count': instance.threadCount,
  'is_selected': instance.isSelected,
  'threads': instance.threads.map((e) => e.toJson()).toList(),
};

_EnvironmentNavigatorViewStateV1 _$EnvironmentNavigatorViewStateV1FromJson(
  Map<String, dynamic> json,
) => _EnvironmentNavigatorViewStateV1(
  environmentId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_id'],
    const UuidValueConverter().fromJson,
  ),
  title: json['title'] as String,
  status: json['status'] as String,
  ready: json['ready'] as bool,
  selectedProcessId: _$JsonConverterFromJson<String, UuidValue>(
    json['selected_process_id'],
    const UuidValueConverter().fromJson,
  ),
  selectedProcessKey: json['selected_process_key'] as String?,
  selectedThreadId: _$JsonConverterFromJson<String, UuidValue>(
    json['selected_thread_id'],
    const UuidValueConverter().fromJson,
  ),
  selectedThreadKey: json['selected_thread_key'] as String?,
  processes:
      (json['processes'] as List<dynamic>?)
          ?.map(
            (e) => EnvironmentProcessNavigationItemV1.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  statusBlocks:
      (json['status_blocks'] as List<dynamic>?)
          ?.map(
            (e) => EnvironmentStatusBlockSummaryV1.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  emptyMessage: json['empty_message'] as String,
  provenance: json['provenance'] as Map<String, dynamic>,
);

Map<String, dynamic> _$EnvironmentNavigatorViewStateV1ToJson(
  _EnvironmentNavigatorViewStateV1 instance,
) => <String, dynamic>{
  'environment_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentId,
    const UuidValueConverter().toJson,
  ),
  'title': instance.title,
  'status': instance.status,
  'ready': instance.ready,
  'selected_process_id': _$JsonConverterToJson<String, UuidValue>(
    instance.selectedProcessId,
    const UuidValueConverter().toJson,
  ),
  'selected_process_key': instance.selectedProcessKey,
  'selected_thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.selectedThreadId,
    const UuidValueConverter().toJson,
  ),
  'selected_thread_key': instance.selectedThreadKey,
  'processes': instance.processes.map((e) => e.toJson()).toList(),
  'status_blocks': instance.statusBlocks.map((e) => e.toJson()).toList(),
  'empty_message': instance.emptyMessage,
  'provenance': instance.provenance,
};

_ProcessWorkspaceThreadViewStateV1 _$ProcessWorkspaceThreadViewStateV1FromJson(
  Map<String, dynamic> json,
) => _ProcessWorkspaceThreadViewStateV1(
  threadId: _$JsonConverterFromJson<String, UuidValue>(
    json['thread_id'],
    const UuidValueConverter().fromJson,
  ),
  threadKey: json['thread_key'] as String?,
  title: json['title'] as String,
  description: json['description'] as String?,
  attachmentCount: (json['attachment_count'] as num).toInt(),
  activeAttachmentCount: (json['active_attachment_count'] as num).toInt(),
  laneCount: (json['lane_count'] as num).toInt(),
  layoutCount: (json['layout_count'] as num).toInt(),
  isSelected: json['is_selected'] as bool,
);

Map<String, dynamic> _$ProcessWorkspaceThreadViewStateV1ToJson(
  _ProcessWorkspaceThreadViewStateV1 instance,
) => <String, dynamic>{
  'thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadId,
    const UuidValueConverter().toJson,
  ),
  'thread_key': instance.threadKey,
  'title': instance.title,
  'description': instance.description,
  'attachment_count': instance.attachmentCount,
  'active_attachment_count': instance.activeAttachmentCount,
  'lane_count': instance.laneCount,
  'layout_count': instance.layoutCount,
  'is_selected': instance.isSelected,
};

_ProcessWorkspaceViewStateV1 _$ProcessWorkspaceViewStateV1FromJson(
  Map<String, dynamic> json,
) => _ProcessWorkspaceViewStateV1(
  environmentId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_id'],
    const UuidValueConverter().fromJson,
  ),
  processId: _$JsonConverterFromJson<String, UuidValue>(
    json['process_id'],
    const UuidValueConverter().fromJson,
  ),
  processKey: json['process_key'] as String?,
  title: json['title'] as String,
  description: json['description'] as String?,
  status: json['status'] as String,
  selectedThreadId: _$JsonConverterFromJson<String, UuidValue>(
    json['selected_thread_id'],
    const UuidValueConverter().fromJson,
  ),
  selectedThreadKey: json['selected_thread_key'] as String?,
  threads:
      (json['threads'] as List<dynamic>?)
          ?.map(
            (e) => ProcessWorkspaceThreadViewStateV1.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  emptyMessage: json['empty_message'] as String,
  provenance: json['provenance'] as Map<String, dynamic>,
);

Map<String, dynamic> _$ProcessWorkspaceViewStateV1ToJson(
  _ProcessWorkspaceViewStateV1 instance,
) => <String, dynamic>{
  'environment_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentId,
    const UuidValueConverter().toJson,
  ),
  'process_id': _$JsonConverterToJson<String, UuidValue>(
    instance.processId,
    const UuidValueConverter().toJson,
  ),
  'process_key': instance.processKey,
  'title': instance.title,
  'description': instance.description,
  'status': instance.status,
  'selected_thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.selectedThreadId,
    const UuidValueConverter().toJson,
  ),
  'selected_thread_key': instance.selectedThreadKey,
  'threads': instance.threads.map((e) => e.toJson()).toList(),
  'empty_message': instance.emptyMessage,
  'provenance': instance.provenance,
};

_ThreadLayoutLaneViewStateV1 _$ThreadLayoutLaneViewStateV1FromJson(
  Map<String, dynamic> json,
) => _ThreadLayoutLaneViewStateV1(
  laneHash: json['lane_hash'] as String,
  opgId: _$JsonConverterFromJson<String, UuidValue>(
    json['opg_id'],
    const UuidValueConverter().fromJson,
  ),
  opgName: json['opg_name'] as String?,
);

Map<String, dynamic> _$ThreadLayoutLaneViewStateV1ToJson(
  _ThreadLayoutLaneViewStateV1 instance,
) => <String, dynamic>{
  'lane_hash': instance.laneHash,
  'opg_id': _$JsonConverterToJson<String, UuidValue>(
    instance.opgId,
    const UuidValueConverter().toJson,
  ),
  'opg_name': instance.opgName,
};

_ThreadLayoutAttachmentViewStateV1 _$ThreadLayoutAttachmentViewStateV1FromJson(
  Map<String, dynamic> json,
) => _ThreadLayoutAttachmentViewStateV1(
  attachmentId: _$JsonConverterFromJson<String, UuidValue>(
    json['attachment_id'],
    const UuidValueConverter().fromJson,
  ),
  title: json['title'] as String?,
  isActive: json['is_active'] as bool,
  objectInstanceGraphBranchId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_branch_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  domainBranchId: _$JsonConverterFromJson<String, UuidValue>(
    json['domain_branch_id'],
    const UuidValueConverter().fromJson,
  ),
  lanes:
      (json['lanes'] as List<dynamic>?)
          ?.map(
            (e) =>
                ThreadLayoutLaneViewStateV1.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$ThreadLayoutAttachmentViewStateV1ToJson(
  _ThreadLayoutAttachmentViewStateV1 instance,
) => <String, dynamic>{
  'attachment_id': _$JsonConverterToJson<String, UuidValue>(
    instance.attachmentId,
    const UuidValueConverter().toJson,
  ),
  'title': instance.title,
  'is_active': instance.isActive,
  'object_instance_graph_branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphBranchId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_identity_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphIdentityId,
    const UuidValueConverter().toJson,
  ),
  'domain_branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.domainBranchId,
    const UuidValueConverter().toJson,
  ),
  'lanes': instance.lanes.map((e) => e.toJson()).toList(),
};

_ThreadLayoutSectionViewStateV1 _$ThreadLayoutSectionViewStateV1FromJson(
  Map<String, dynamic> json,
) => _ThreadLayoutSectionViewStateV1(
  sectionKey: json['section_key'] as String,
  title: json['title'] as String,
  description: json['description'] as String?,
  order: (json['order'] as num).toInt(),
  flex: (json['flex'] as num).toDouble(),
  isVisible: json['is_visible'] as bool,
  focusScopeId: _$JsonConverterFromJson<String, UuidValue>(
    json['focus_scope_id'],
    const UuidValueConverter().fromJson,
  ),
  viewRef: json['view_ref'] as String?,
  viewKey: json['view_key'] as String?,
  packageName: json['package_name'] as String?,
  paneKey: json['pane_key'] as String?,
);

Map<String, dynamic> _$ThreadLayoutSectionViewStateV1ToJson(
  _ThreadLayoutSectionViewStateV1 instance,
) => <String, dynamic>{
  'section_key': instance.sectionKey,
  'title': instance.title,
  'description': instance.description,
  'order': instance.order,
  'flex': instance.flex,
  'is_visible': instance.isVisible,
  'focus_scope_id': _$JsonConverterToJson<String, UuidValue>(
    instance.focusScopeId,
    const UuidValueConverter().toJson,
  ),
  'view_ref': instance.viewRef,
  'view_key': instance.viewKey,
  'package_name': instance.packageName,
  'pane_key': instance.paneKey,
};

_ThreadLayoutCandidateViewStateV1 _$ThreadLayoutCandidateViewStateV1FromJson(
  Map<String, dynamic> json,
) => _ThreadLayoutCandidateViewStateV1(
  layoutId: _$JsonConverterFromJson<String, UuidValue>(
    json['layout_id'],
    const UuidValueConverter().fromJson,
  ),
  layoutKey: json['layout_key'] as String?,
  title: json['title'] as String,
  description: json['description'] as String?,
  isActive: json['is_active'] as bool,
  sections:
      (json['sections'] as List<dynamic>?)
          ?.map(
            (e) => ThreadLayoutSectionViewStateV1.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$ThreadLayoutCandidateViewStateV1ToJson(
  _ThreadLayoutCandidateViewStateV1 instance,
) => <String, dynamic>{
  'layout_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutId,
    const UuidValueConverter().toJson,
  ),
  'layout_key': instance.layoutKey,
  'title': instance.title,
  'description': instance.description,
  'is_active': instance.isActive,
  'sections': instance.sections.map((e) => e.toJson()).toList(),
};

_ThreadLayoutViewStateV1 _$ThreadLayoutViewStateV1FromJson(
  Map<String, dynamic> json,
) => _ThreadLayoutViewStateV1(
  environmentId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_id'],
    const UuidValueConverter().fromJson,
  ),
  processId: _$JsonConverterFromJson<String, UuidValue>(
    json['process_id'],
    const UuidValueConverter().fromJson,
  ),
  processKey: json['process_key'] as String?,
  threadId: _$JsonConverterFromJson<String, UuidValue>(
    json['thread_id'],
    const UuidValueConverter().fromJson,
  ),
  threadKey: json['thread_key'] as String?,
  title: json['title'] as String,
  description: json['description'] as String?,
  status: json['status'] as String,
  activeLayoutId: _$JsonConverterFromJson<String, UuidValue>(
    json['active_layout_id'],
    const UuidValueConverter().fromJson,
  ),
  activeLayoutKey: json['active_layout_key'] as String?,
  layouts:
      (json['layouts'] as List<dynamic>?)
          ?.map(
            (e) => ThreadLayoutCandidateViewStateV1.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  sections:
      (json['sections'] as List<dynamic>?)
          ?.map(
            (e) => ThreadLayoutSectionViewStateV1.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  attachments:
      (json['attachments'] as List<dynamic>?)
          ?.map(
            (e) => ThreadLayoutAttachmentViewStateV1.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  emptyMessage: json['empty_message'] as String,
  provenance: json['provenance'] as Map<String, dynamic>,
);

Map<String, dynamic> _$ThreadLayoutViewStateV1ToJson(
  _ThreadLayoutViewStateV1 instance,
) => <String, dynamic>{
  'environment_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentId,
    const UuidValueConverter().toJson,
  ),
  'process_id': _$JsonConverterToJson<String, UuidValue>(
    instance.processId,
    const UuidValueConverter().toJson,
  ),
  'process_key': instance.processKey,
  'thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadId,
    const UuidValueConverter().toJson,
  ),
  'thread_key': instance.threadKey,
  'title': instance.title,
  'description': instance.description,
  'status': instance.status,
  'active_layout_id': _$JsonConverterToJson<String, UuidValue>(
    instance.activeLayoutId,
    const UuidValueConverter().toJson,
  ),
  'active_layout_key': instance.activeLayoutKey,
  'layouts': instance.layouts.map((e) => e.toJson()).toList(),
  'sections': instance.sections.map((e) => e.toJson()).toList(),
  'attachments': instance.attachments.map((e) => e.toJson()).toList(),
  'empty_message': instance.emptyMessage,
  'provenance': instance.provenance,
};
