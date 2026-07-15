// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'environment_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_EnvironmentActorAdmissionRoleEligibility
_$EnvironmentActorAdmissionRoleEligibilityFromJson(Map<String, dynamic> json) =>
    _EnvironmentActorAdmissionRoleEligibility(
      environmentProfileActorConfigId: const UuidValueConverter().fromJson(
        json['environment_profile_actor_config_id'] as String,
      ),
      actorConfigRoleConfigId: const UuidValueConverter().fromJson(
        json['actor_config_role_config_id'] as String,
      ),
      roleConfigId: const UuidValueConverter().fromJson(
        json['role_config_id'] as String,
      ),
      roleConfigName: json['role_config_name'] as String?,
    );

Map<String, dynamic> _$EnvironmentActorAdmissionRoleEligibilityToJson(
  _EnvironmentActorAdmissionRoleEligibility instance,
) => <String, dynamic>{
  'environment_profile_actor_config_id': const UuidValueConverter().toJson(
    instance.environmentProfileActorConfigId,
  ),
  'actor_config_role_config_id': const UuidValueConverter().toJson(
    instance.actorConfigRoleConfigId,
  ),
  'role_config_id': const UuidValueConverter().toJson(instance.roleConfigId),
  'role_config_name': instance.roleConfigName,
};

_EnvironmentActorAdmissionRoleBinding
_$EnvironmentActorAdmissionRoleBindingFromJson(Map<String, dynamic> json) =>
    _EnvironmentActorAdmissionRoleBinding(
      environmentProfileActorConfigId: const UuidValueConverter().fromJson(
        json['environment_profile_actor_config_id'] as String,
      ),
      actorConfigRoleConfigId: const UuidValueConverter().fromJson(
        json['actor_config_role_config_id'] as String,
      ),
      roleConfigId: const UuidValueConverter().fromJson(
        json['role_config_id'] as String,
      ),
      roleConfigName: json['role_config_name'] as String?,
      actorId: const UuidValueConverter().fromJson(json['actor_id'] as String),
      roleId: const UuidValueConverter().fromJson(json['role_id'] as String),
      actorRoleId: const UuidValueConverter().fromJson(
        json['actor_role_id'] as String,
      ),
      roleClassInstanceId: const UuidValueConverter().fromJson(
        json['role_class_instance_id'] as String,
      ),
      classInstanceIdentityId: const UuidValueConverter().fromJson(
        json['class_instance_identity_id'] as String,
      ),
      roleConfigClassConfigId: const UuidValueConverter().fromJson(
        json['role_config_class_config_id'] as String,
      ),
      objectInstanceGraphIdentityId: const UuidValueConverter().fromJson(
        json['object_instance_graph_identity_id'] as String,
      ),
      objectInstanceGraphBranchKey:
          json['object_instance_graph_branch_key'] as String,
      objectInstanceGraphBranchId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_instance_graph_branch_id'],
        const UuidValueConverter().fromJson,
      ),
    );

Map<String, dynamic> _$EnvironmentActorAdmissionRoleBindingToJson(
  _EnvironmentActorAdmissionRoleBinding instance,
) => <String, dynamic>{
  'environment_profile_actor_config_id': const UuidValueConverter().toJson(
    instance.environmentProfileActorConfigId,
  ),
  'actor_config_role_config_id': const UuidValueConverter().toJson(
    instance.actorConfigRoleConfigId,
  ),
  'role_config_id': const UuidValueConverter().toJson(instance.roleConfigId),
  'role_config_name': instance.roleConfigName,
  'actor_id': const UuidValueConverter().toJson(instance.actorId),
  'role_id': const UuidValueConverter().toJson(instance.roleId),
  'actor_role_id': const UuidValueConverter().toJson(instance.actorRoleId),
  'role_class_instance_id': const UuidValueConverter().toJson(
    instance.roleClassInstanceId,
  ),
  'class_instance_identity_id': const UuidValueConverter().toJson(
    instance.classInstanceIdentityId,
  ),
  'role_config_class_config_id': const UuidValueConverter().toJson(
    instance.roleConfigClassConfigId,
  ),
  'object_instance_graph_identity_id': const UuidValueConverter().toJson(
    instance.objectInstanceGraphIdentityId,
  ),
  'object_instance_graph_branch_key': instance.objectInstanceGraphBranchKey,
  'object_instance_graph_branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphBranchId,
    const UuidValueConverter().toJson,
  ),
};

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);

_EnvironmentActorAdmissionReceipt _$EnvironmentActorAdmissionReceiptFromJson(
  Map<String, dynamic> json,
) => _EnvironmentActorAdmissionReceipt(
  accepted: json['accepted'] as bool,
  status: json['status'] as String,
  error: json['error'] as String?,
  reason: json['reason'] as String?,
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
  environmentProfileId: const UuidValueConverter().fromJson(
    json['environment_profile_id'] as String,
  ),
  environmentProfileActorConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_profile_actor_config_id'],
    const UuidValueConverter().fromJson,
  ),
  actorConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_config_id'],
    const UuidValueConverter().fromJson,
  ),
  classInstanceIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['class_instance_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphBranchKey:
      json['object_instance_graph_branch_key'] as String,
  objectInstanceGraphBranchId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_branch_id'],
    const UuidValueConverter().fromJson,
  ),
  requestedRoleConfigIds: json['requested_role_config_ids'] == null
      ? const []
      : const UuidValueListConverter().fromJson(
          json['requested_role_config_ids'] as List,
        ),
  requestedRoleConfigNames:
      (json['requested_role_config_names'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  eligibleRoles:
      (json['eligible_roles'] as List<dynamic>?)
          ?.map(
            (e) => EnvironmentActorAdmissionRoleEligibility.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  bindings:
      (json['bindings'] as List<dynamic>?)
          ?.map(
            (e) => EnvironmentActorAdmissionRoleBinding.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  blockers:
      (json['blockers'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$EnvironmentActorAdmissionReceiptToJson(
  _EnvironmentActorAdmissionReceipt instance,
) => <String, dynamic>{
  'accepted': instance.accepted,
  'status': instance.status,
  'error': instance.error,
  'reason': instance.reason,
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
  'environment_profile_id': const UuidValueConverter().toJson(
    instance.environmentProfileId,
  ),
  'environment_profile_actor_config_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.environmentProfileActorConfigId,
        const UuidValueConverter().toJson,
      ),
  'actor_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorConfigId,
    const UuidValueConverter().toJson,
  ),
  'class_instance_identity_id': _$JsonConverterToJson<String, UuidValue>(
    instance.classInstanceIdentityId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_branch_key': instance.objectInstanceGraphBranchKey,
  'object_instance_graph_branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphBranchId,
    const UuidValueConverter().toJson,
  ),
  'requested_role_config_ids': const UuidValueListConverter().toJson(
    instance.requestedRoleConfigIds,
  ),
  'requested_role_config_names': instance.requestedRoleConfigNames,
  'eligible_roles': instance.eligibleRoles.map((e) => e.toJson()).toList(),
  'bindings': instance.bindings.map((e) => e.toJson()).toList(),
  'blockers': instance.blockers,
  'evidence': instance.evidence,
};

_EnvironmentSessionIdentityEvidence
_$EnvironmentSessionIdentityEvidenceFromJson(Map<String, dynamic> json) =>
    _EnvironmentSessionIdentityEvidence(
      identitySession: json['identity_session'] == null
          ? null
          : SessionSummary.fromJson(
              json['identity_session'] as Map<String, dynamic>,
            ),
      identityMember: json['identity_member'] == null
          ? null
          : SessionMemberSummary.fromJson(
              json['identity_member'] as Map<String, dynamic>,
            ),
      identityActorRoles:
          (json['identity_actor_roles'] as List<dynamic>?)
              ?.map(
                (e) => SessionMemberActorRoleSummary.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
      evidence: json['evidence'] as Map<String, dynamic>,
    );

Map<String, dynamic> _$EnvironmentSessionIdentityEvidenceToJson(
  _EnvironmentSessionIdentityEvidence instance,
) => <String, dynamic>{
  'identity_session': instance.identitySession?.toJson(),
  'identity_member': instance.identityMember?.toJson(),
  'identity_actor_roles': instance.identityActorRoles
      .map((e) => e.toJson())
      .toList(),
  'evidence': instance.evidence,
};

_EnvironmentSessionView _$EnvironmentSessionViewFromJson(
  Map<String, dynamic> json,
) => _EnvironmentSessionView(
  environmentSessionId: const UuidValueConverter().fromJson(
    json['environment_session_id'] as String,
  ),
  environmentSessionConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_session_config_id'],
    const UuidValueConverter().fromJson,
  ),
  identitySessionId: _$JsonConverterFromJson<String, UuidValue>(
    json['identity_session_id'],
    const UuidValueConverter().fromJson,
  ),
  identitySession: json['identity_session'] == null
      ? null
      : SessionSummary.fromJson(
          json['identity_session'] as Map<String, dynamic>,
        ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
  environmentProfileId: const UuidValueConverter().fromJson(
    json['environment_profile_id'] as String,
  ),
  sessionKey: json['session_key'] as String,
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
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$EnvironmentSessionViewToJson(
  _EnvironmentSessionView instance,
) => <String, dynamic>{
  'environment_session_id': const UuidValueConverter().toJson(
    instance.environmentSessionId,
  ),
  'environment_session_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentSessionConfigId,
    const UuidValueConverter().toJson,
  ),
  'identity_session_id': _$JsonConverterToJson<String, UuidValue>(
    instance.identitySessionId,
    const UuidValueConverter().toJson,
  ),
  'identity_session': instance.identitySession?.toJson(),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
  'environment_profile_id': const UuidValueConverter().toJson(
    instance.environmentProfileId,
  ),
  'session_key': instance.sessionKey,
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
  'evidence': instance.evidence,
};

_EnvironmentSessionJoinReceipt _$EnvironmentSessionJoinReceiptFromJson(
  Map<String, dynamic> json,
) => _EnvironmentSessionJoinReceipt(
  accepted: json['accepted'] as bool,
  status: json['status'] as String,
  error: json['error'] as String?,
  reason: json['reason'] as String?,
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
  environmentProfileId: const UuidValueConverter().fromJson(
    json['environment_profile_id'] as String,
  ),
  environmentSessionId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_session_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentSessionKey: json['environment_session_key'] as String?,
  identityEvidence: json['identity_evidence'] == null
      ? null
      : EnvironmentSessionIdentityEvidence.fromJson(
          json['identity_evidence'] as Map<String, dynamic>,
        ),
  blockers:
      (json['blockers'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$EnvironmentSessionJoinReceiptToJson(
  _EnvironmentSessionJoinReceipt instance,
) => <String, dynamic>{
  'accepted': instance.accepted,
  'status': instance.status,
  'error': instance.error,
  'reason': instance.reason,
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
  'environment_profile_id': const UuidValueConverter().toJson(
    instance.environmentProfileId,
  ),
  'environment_session_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentSessionId,
    const UuidValueConverter().toJson,
  ),
  'environment_session_key': instance.environmentSessionKey,
  'identity_evidence': instance.identityEvidence?.toJson(),
  'blockers': instance.blockers,
  'evidence': instance.evidence,
};

_EnvironmentNavigationContextView _$EnvironmentNavigationContextViewFromJson(
  Map<String, dynamic> json,
) => _EnvironmentNavigationContextView(
  environmentNavigationContextId: const UuidValueConverter().fromJson(
    json['environment_navigation_context_id'] as String,
  ),
  environmentSessionId: const UuidValueConverter().fromJson(
    json['environment_session_id'] as String,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
  key: json['key'] as String,
  title: json['title'] as String?,
  status: json['status'] as String,
  isDefault: json['is_default'] as bool,
  selectedProcessId: _$JsonConverterFromJson<String, UuidValue>(
    json['selected_process_id'],
    const UuidValueConverter().fromJson,
  ),
  selectedThreadId: _$JsonConverterFromJson<String, UuidValue>(
    json['selected_thread_id'],
    const UuidValueConverter().fromJson,
  ),
  branchId: _$JsonConverterFromJson<String, UuidValue>(
    json['branch_id'],
    const UuidValueConverter().fromJson,
  ),
  projectionHash: json['projection_hash'] as String?,
  rootObjectId: _$JsonConverterFromJson<String, UuidValue>(
    json['root_object_id'],
    const UuidValueConverter().fromJson,
  ),
  commitId: _$JsonConverterFromJson<String, UuidValue>(
    json['commit_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  graphHashPost: json['graph_hash_post'] as String?,
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$EnvironmentNavigationContextViewToJson(
  _EnvironmentNavigationContextView instance,
) => <String, dynamic>{
  'environment_navigation_context_id': const UuidValueConverter().toJson(
    instance.environmentNavigationContextId,
  ),
  'environment_session_id': const UuidValueConverter().toJson(
    instance.environmentSessionId,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
  'key': instance.key,
  'title': instance.title,
  'status': instance.status,
  'is_default': instance.isDefault,
  'selected_process_id': _$JsonConverterToJson<String, UuidValue>(
    instance.selectedProcessId,
    const UuidValueConverter().toJson,
  ),
  'selected_thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.selectedThreadId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.branchId,
    const UuidValueConverter().toJson,
  ),
  'projection_hash': instance.projectionHash,
  'root_object_id': _$JsonConverterToJson<String, UuidValue>(
    instance.rootObjectId,
    const UuidValueConverter().toJson,
  ),
  'commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.commitId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphCommitId,
    const UuidValueConverter().toJson,
  ),
  'graph_hash_post': instance.graphHashPost,
  'evidence': instance.evidence,
};

_EnvironmentNavigationCommitReceipt
_$EnvironmentNavigationCommitReceiptFromJson(
  Map<String, dynamic> json,
) => _EnvironmentNavigationCommitReceipt(
  accepted: json['accepted'] as bool,
  status: json['status'] as String,
  error: json['error'] as String?,
  reason: json['reason'] as String?,
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
  environmentSessionId: const UuidValueConverter().fromJson(
    json['environment_session_id'] as String,
  ),
  environmentNavigationContextId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_navigation_context_id'],
    const UuidValueConverter().fromJson,
  ),
  key: json['key'] as String?,
  isDefault: json['is_default'] as bool,
  branchId: _$JsonConverterFromJson<String, UuidValue>(
    json['branch_id'],
    const UuidValueConverter().fromJson,
  ),
  projectionHash: json['projection_hash'] as String?,
  rootObjectId: _$JsonConverterFromJson<String, UuidValue>(
    json['root_object_id'],
    const UuidValueConverter().fromJson,
  ),
  commitId: _$JsonConverterFromJson<String, UuidValue>(
    json['commit_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  graphHashPre: json['graph_hash_pre'] as String?,
  graphHashPost: json['graph_hash_post'] as String?,
  functionCallId: _$JsonConverterFromJson<String, UuidValue>(
    json['function_call_id'],
    const UuidValueConverter().fromJson,
  ),
  functionCallResponseId: _$JsonConverterFromJson<String, UuidValue>(
    json['function_call_response_id'],
    const UuidValueConverter().fromJson,
  ),
  selectedProcessId: _$JsonConverterFromJson<String, UuidValue>(
    json['selected_process_id'],
    const UuidValueConverter().fromJson,
  ),
  selectedThreadId: _$JsonConverterFromJson<String, UuidValue>(
    json['selected_thread_id'],
    const UuidValueConverter().fromJson,
  ),
  blockers:
      (json['blockers'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$EnvironmentNavigationCommitReceiptToJson(
  _EnvironmentNavigationCommitReceipt instance,
) => <String, dynamic>{
  'accepted': instance.accepted,
  'status': instance.status,
  'error': instance.error,
  'reason': instance.reason,
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
  'environment_session_id': const UuidValueConverter().toJson(
    instance.environmentSessionId,
  ),
  'environment_navigation_context_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentNavigationContextId,
    const UuidValueConverter().toJson,
  ),
  'key': instance.key,
  'is_default': instance.isDefault,
  'branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.branchId,
    const UuidValueConverter().toJson,
  ),
  'projection_hash': instance.projectionHash,
  'root_object_id': _$JsonConverterToJson<String, UuidValue>(
    instance.rootObjectId,
    const UuidValueConverter().toJson,
  ),
  'commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.commitId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphCommitId,
    const UuidValueConverter().toJson,
  ),
  'graph_hash_pre': instance.graphHashPre,
  'graph_hash_post': instance.graphHashPost,
  'function_call_id': _$JsonConverterToJson<String, UuidValue>(
    instance.functionCallId,
    const UuidValueConverter().toJson,
  ),
  'function_call_response_id': _$JsonConverterToJson<String, UuidValue>(
    instance.functionCallResponseId,
    const UuidValueConverter().toJson,
  ),
  'selected_process_id': _$JsonConverterToJson<String, UuidValue>(
    instance.selectedProcessId,
    const UuidValueConverter().toJson,
  ),
  'selected_thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.selectedThreadId,
    const UuidValueConverter().toJson,
  ),
  'blockers': instance.blockers,
  'evidence': instance.evidence,
};
