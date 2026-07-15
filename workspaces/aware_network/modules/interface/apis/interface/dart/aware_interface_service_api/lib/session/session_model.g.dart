// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'session_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_SessionSummary _$SessionSummaryFromJson(Map<String, dynamic> json) =>
    _SessionSummary(
      sessionId: const UuidValueConverter().fromJson(
        json['session_id'] as String,
      ),
      sessionConfigId: const UuidValueConverter().fromJson(
        json['session_config_id'] as String,
      ),
      parentSessionId: _$JsonConverterFromJson<String, UuidValue>(
        json['parent_session_id'],
        const UuidValueConverter().fromJson,
      ),
      key: json['key'] as String,
      title: json['title'] as String?,
      description: json['description'] as String?,
      purpose: json['purpose'] as String?,
      status: json['status'] as String,
      createdByActorId: _$JsonConverterFromJson<String, UuidValue>(
        json['created_by_actor_id'],
        const UuidValueConverter().fromJson,
      ),
      sourceKind: json['source_kind'] as String?,
      sourceRef: json['source_ref'] as String?,
      metadataJson: json['metadata_json'] as Map<String, dynamic>,
      providerSessions:
          (json['provider_sessions'] as List<dynamic>?)
              ?.map(
                (e) => SessionProviderSessionSummary.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
      memberCount: (json['member_count'] as num).toInt(),
    );

Map<String, dynamic> _$SessionSummaryToJson(_SessionSummary instance) =>
    <String, dynamic>{
      'session_id': const UuidValueConverter().toJson(instance.sessionId),
      'session_config_id': const UuidValueConverter().toJson(
        instance.sessionConfigId,
      ),
      'parent_session_id': _$JsonConverterToJson<String, UuidValue>(
        instance.parentSessionId,
        const UuidValueConverter().toJson,
      ),
      'key': instance.key,
      'title': instance.title,
      'description': instance.description,
      'purpose': instance.purpose,
      'status': instance.status,
      'created_by_actor_id': _$JsonConverterToJson<String, UuidValue>(
        instance.createdByActorId,
        const UuidValueConverter().toJson,
      ),
      'source_kind': instance.sourceKind,
      'source_ref': instance.sourceRef,
      'metadata_json': instance.metadataJson,
      'provider_sessions': instance.providerSessions
          .map((e) => e.toJson())
          .toList(),
      'member_count': instance.memberCount,
    };

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);

_SessionMemberSummary _$SessionMemberSummaryFromJson(
  Map<String, dynamic> json,
) => _SessionMemberSummary(
  sessionMemberId: const UuidValueConverter().fromJson(
    json['session_member_id'] as String,
  ),
  sessionId: const UuidValueConverter().fromJson(json['session_id'] as String),
  actorId: const UuidValueConverter().fromJson(json['actor_id'] as String),
  sessionActorConfigId: const UuidValueConverter().fromJson(
    json['session_actor_config_id'] as String,
  ),
  status: json['status'] as String,
  joinedAtUnixMs: (json['joined_at_unix_ms'] as num?)?.toInt(),
  leftAtUnixMs: (json['left_at_unix_ms'] as num?)?.toInt(),
  metadataJson: json['metadata_json'] as Map<String, dynamic>,
  actorRoles:
      (json['actor_roles'] as List<dynamic>?)
          ?.map(
            (e) => SessionMemberActorRoleSummary.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$SessionMemberSummaryToJson(
  _SessionMemberSummary instance,
) => <String, dynamic>{
  'session_member_id': const UuidValueConverter().toJson(
    instance.sessionMemberId,
  ),
  'session_id': const UuidValueConverter().toJson(instance.sessionId),
  'actor_id': const UuidValueConverter().toJson(instance.actorId),
  'session_actor_config_id': const UuidValueConverter().toJson(
    instance.sessionActorConfigId,
  ),
  'status': instance.status,
  'joined_at_unix_ms': instance.joinedAtUnixMs,
  'left_at_unix_ms': instance.leftAtUnixMs,
  'metadata_json': instance.metadataJson,
  'actor_roles': instance.actorRoles.map((e) => e.toJson()).toList(),
};

_SessionMemberActorRoleSummary _$SessionMemberActorRoleSummaryFromJson(
  Map<String, dynamic> json,
) => _SessionMemberActorRoleSummary(
  sessionMemberActorRoleId: const UuidValueConverter().fromJson(
    json['session_member_actor_role_id'] as String,
  ),
  sessionMemberId: const UuidValueConverter().fromJson(
    json['session_member_id'] as String,
  ),
  actorRoleId: const UuidValueConverter().fromJson(
    json['actor_role_id'] as String,
  ),
  sourceKind: json['source_kind'] as String,
  status: json['status'] as String,
  evidenceJson: json['evidence_json'] as Map<String, dynamic>,
);

Map<String, dynamic> _$SessionMemberActorRoleSummaryToJson(
  _SessionMemberActorRoleSummary instance,
) => <String, dynamic>{
  'session_member_actor_role_id': const UuidValueConverter().toJson(
    instance.sessionMemberActorRoleId,
  ),
  'session_member_id': const UuidValueConverter().toJson(
    instance.sessionMemberId,
  ),
  'actor_role_id': const UuidValueConverter().toJson(instance.actorRoleId),
  'source_kind': instance.sourceKind,
  'status': instance.status,
  'evidence_json': instance.evidenceJson,
};

_SessionProviderSessionSummary _$SessionProviderSessionSummaryFromJson(
  Map<String, dynamic> json,
) => _SessionProviderSessionSummary(
  sessionProviderSessionId: const UuidValueConverter().fromJson(
    json['session_provider_session_id'] as String,
  ),
  sessionId: const UuidValueConverter().fromJson(json['session_id'] as String),
  providerSessionConfigId: const UuidValueConverter().fromJson(
    json['provider_session_config_id'] as String,
  ),
  providerSessionKey: json['provider_session_key'] as String,
  providerSessionRef: json['provider_session_ref'] as String?,
  providerObjectInstanceGraphIdentityId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['provider_object_instance_graph_identity_id'],
        const UuidValueConverter().fromJson,
      ),
  providerClassInstanceIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['provider_class_instance_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  providerObjectInstanceGraphBranchId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['provider_object_instance_graph_branch_id'],
        const UuidValueConverter().fromJson,
      ),
  status: json['status'] as String,
  metadataJson: json['metadata_json'] as Map<String, dynamic>,
);

Map<String, dynamic> _$SessionProviderSessionSummaryToJson(
  _SessionProviderSessionSummary instance,
) => <String, dynamic>{
  'session_provider_session_id': const UuidValueConverter().toJson(
    instance.sessionProviderSessionId,
  ),
  'session_id': const UuidValueConverter().toJson(instance.sessionId),
  'provider_session_config_id': const UuidValueConverter().toJson(
    instance.providerSessionConfigId,
  ),
  'provider_session_key': instance.providerSessionKey,
  'provider_session_ref': instance.providerSessionRef,
  'provider_object_instance_graph_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.providerObjectInstanceGraphIdentityId,
        const UuidValueConverter().toJson,
      ),
  'provider_class_instance_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.providerClassInstanceIdentityId,
        const UuidValueConverter().toJson,
      ),
  'provider_object_instance_graph_branch_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.providerObjectInstanceGraphBranchId,
        const UuidValueConverter().toJson,
      ),
  'status': instance.status,
  'metadata_json': instance.metadataJson,
};
