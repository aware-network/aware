// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'models_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_AttentionSessionPin _$AttentionSessionPinFromJson(Map<String, dynamic> json) =>
    _AttentionSessionPin(
      attentionSessionId: const UuidValueConverter().fromJson(
        json['attention_session_id'] as String,
      ),
      identitySessionId: const UuidValueConverter().fromJson(
        json['identity_session_id'] as String,
      ),
      activeLayoutId: _$JsonConverterFromJson<String, UuidValue>(
        json['active_layout_id'],
        const UuidValueConverter().fromJson,
      ),
      key: json['key'] as String?,
      title: json['title'] as String?,
      description: json['description'] as String?,
      purpose: json['purpose'] as String?,
      status: json['status'] as String,
      sourceKind: json['source_kind'] as String?,
      sourceRef: json['source_ref'] as String?,
      metadataJson: json['metadata_json'] as Map<String, dynamic>,
    );

Map<String, dynamic> _$AttentionSessionPinToJson(
  _AttentionSessionPin instance,
) => <String, dynamic>{
  'attention_session_id': const UuidValueConverter().toJson(
    instance.attentionSessionId,
  ),
  'identity_session_id': const UuidValueConverter().toJson(
    instance.identitySessionId,
  ),
  'active_layout_id': _$JsonConverterToJson<String, UuidValue>(
    instance.activeLayoutId,
    const UuidValueConverter().toJson,
  ),
  'key': instance.key,
  'title': instance.title,
  'description': instance.description,
  'purpose': instance.purpose,
  'status': instance.status,
  'source_kind': instance.sourceKind,
  'source_ref': instance.sourceRef,
  'metadata_json': instance.metadataJson,
};

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);

_AttentionFocusTransitionPin _$AttentionFocusTransitionPinFromJson(
  Map<String, dynamic> json,
) => _AttentionFocusTransitionPin(
  attentionFocusTransitionId: const UuidValueConverter().fromJson(
    json['attention_focus_transition_id'] as String,
  ),
  attentionSessionSectionId: const UuidValueConverter().fromJson(
    json['attention_session_section_id'] as String,
  ),
  attentionSessionLayoutId: _$JsonConverterFromJson<String, UuidValue>(
    json['attention_session_layout_id'],
    const UuidValueConverter().fromJson,
  ),
  attentionSessionId: _$JsonConverterFromJson<String, UuidValue>(
    json['attention_session_id'],
    const UuidValueConverter().fromJson,
  ),
  identitySessionId: _$JsonConverterFromJson<String, UuidValue>(
    json['identity_session_id'],
    const UuidValueConverter().fromJson,
  ),
  layoutSectionId: _$JsonConverterFromJson<String, UuidValue>(
    json['layout_section_id'],
    const UuidValueConverter().fromJson,
  ),
  sectionId: _$JsonConverterFromJson<String, UuidValue>(
    json['section_id'],
    const UuidValueConverter().fromJson,
  ),
  sectionKey: json['section_key'] as String?,
  layoutId: _$JsonConverterFromJson<String, UuidValue>(
    json['layout_id'],
    const UuidValueConverter().fromJson,
  ),
  layoutConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['layout_config_id'],
    const UuidValueConverter().fromJson,
  ),
  previousTransitionId: _$JsonConverterFromJson<String, UuidValue>(
    json['previous_transition_id'],
    const UuidValueConverter().fromJson,
  ),
  focusScopeId: const UuidValueConverter().fromJson(
    json['focus_scope_id'] as String,
  ),
  focusId: _$JsonConverterFromJson<String, UuidValue>(
    json['focus_id'],
    const UuidValueConverter().fromJson,
  ),
  observableId: _$JsonConverterFromJson<String, UuidValue>(
    json['observable_id'],
    const UuidValueConverter().fromJson,
  ),
  objectProjectionGraphIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_projection_graph_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphBranchId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_branch_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  transitionKey: json['transition_key'] as String,
  sequence: (json['sequence'] as num).toInt(),
  projectionHash: json['projection_hash'] as String?,
  transitionKind: json['transition_kind'] as String,
  rationale: json['rationale'] as String?,
  sourceKind: json['source_kind'] as String?,
  sourceRef: json['source_ref'] as String?,
  metadataJson: json['metadata_json'] as Map<String, dynamic>,
);

Map<String, dynamic> _$AttentionFocusTransitionPinToJson(
  _AttentionFocusTransitionPin instance,
) => <String, dynamic>{
  'attention_focus_transition_id': const UuidValueConverter().toJson(
    instance.attentionFocusTransitionId,
  ),
  'attention_session_section_id': const UuidValueConverter().toJson(
    instance.attentionSessionSectionId,
  ),
  'attention_session_layout_id': _$JsonConverterToJson<String, UuidValue>(
    instance.attentionSessionLayoutId,
    const UuidValueConverter().toJson,
  ),
  'attention_session_id': _$JsonConverterToJson<String, UuidValue>(
    instance.attentionSessionId,
    const UuidValueConverter().toJson,
  ),
  'identity_session_id': _$JsonConverterToJson<String, UuidValue>(
    instance.identitySessionId,
    const UuidValueConverter().toJson,
  ),
  'layout_section_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutSectionId,
    const UuidValueConverter().toJson,
  ),
  'section_id': _$JsonConverterToJson<String, UuidValue>(
    instance.sectionId,
    const UuidValueConverter().toJson,
  ),
  'section_key': instance.sectionKey,
  'layout_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutId,
    const UuidValueConverter().toJson,
  ),
  'layout_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutConfigId,
    const UuidValueConverter().toJson,
  ),
  'previous_transition_id': _$JsonConverterToJson<String, UuidValue>(
    instance.previousTransitionId,
    const UuidValueConverter().toJson,
  ),
  'focus_scope_id': const UuidValueConverter().toJson(instance.focusScopeId),
  'focus_id': _$JsonConverterToJson<String, UuidValue>(
    instance.focusId,
    const UuidValueConverter().toJson,
  ),
  'observable_id': _$JsonConverterToJson<String, UuidValue>(
    instance.observableId,
    const UuidValueConverter().toJson,
  ),
  'object_projection_graph_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.objectProjectionGraphIdentityId,
        const UuidValueConverter().toJson,
      ),
  'object_instance_graph_branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphBranchId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphCommitId,
    const UuidValueConverter().toJson,
  ),
  'transition_key': instance.transitionKey,
  'sequence': instance.sequence,
  'projection_hash': instance.projectionHash,
  'transition_kind': instance.transitionKind,
  'rationale': instance.rationale,
  'source_kind': instance.sourceKind,
  'source_ref': instance.sourceRef,
  'metadata_json': instance.metadataJson,
};

_AttentionTransitionValidationResult
_$AttentionTransitionValidationResultFromJson(Map<String, dynamic> json) =>
    _AttentionTransitionValidationResult(
      exists: json['exists'] as bool,
      valid: json['valid'] as bool,
      failureReasons:
          (json['failure_reasons'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      transition: json['transition'] == null
          ? null
          : AttentionFocusTransitionPin.fromJson(
              json['transition'] as Map<String, dynamic>,
            ),
    );

Map<String, dynamic> _$AttentionTransitionValidationResultToJson(
  _AttentionTransitionValidationResult instance,
) => <String, dynamic>{
  'exists': instance.exists,
  'valid': instance.valid,
  'failure_reasons': instance.failureReasons,
  'transition': instance.transition?.toJson(),
};
