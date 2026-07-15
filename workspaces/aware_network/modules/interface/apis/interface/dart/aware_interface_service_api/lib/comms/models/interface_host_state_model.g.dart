// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'interface_host_state_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_InterfaceTransportState _$InterfaceTransportStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceTransportState(
  available: json['available'] as bool,
  registered: json['registered'] as bool,
  authenticated: json['authenticated'] as bool,
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  interfaceId: _$JsonConverterFromJson<String, UuidValue>(
    json['interface_id'],
    const UuidValueConverter().fromJson,
  ),
  interfaceSystemActorId: _$JsonConverterFromJson<String, UuidValue>(
    json['interface_system_actor_id'],
    const UuidValueConverter().fromJson,
  ),
  interfaceSystemIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['interface_system_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  interfaceSessionId: _$JsonConverterFromJson<String, UuidValue>(
    json['interface_session_id'],
    const UuidValueConverter().fromJson,
  ),
  sessionLabel: json['session_label'] as String?,
  capabilities:
      (json['capabilities'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  protocolVersion: (json['protocol_version'] as num?)?.toInt(),
  lastSeenAt: json['last_seen_at'] as String?,
  interfaceIdentityNetworkNodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['interface_identity_network_node_id'],
    const UuidValueConverter().fromJson,
  ),
  interfaceSessionNetworkBindingId: _$JsonConverterFromJson<String, UuidValue>(
    json['interface_session_network_binding_id'],
    const UuidValueConverter().fromJson,
  ),
);

Map<String, dynamic> _$InterfaceTransportStateToJson(
  _InterfaceTransportState instance,
) => <String, dynamic>{
  'available': instance.available,
  'registered': instance.registered,
  'authenticated': instance.authenticated,
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'interface_id': _$JsonConverterToJson<String, UuidValue>(
    instance.interfaceId,
    const UuidValueConverter().toJson,
  ),
  'interface_system_actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.interfaceSystemActorId,
    const UuidValueConverter().toJson,
  ),
  'interface_system_identity_id': _$JsonConverterToJson<String, UuidValue>(
    instance.interfaceSystemIdentityId,
    const UuidValueConverter().toJson,
  ),
  'interface_session_id': _$JsonConverterToJson<String, UuidValue>(
    instance.interfaceSessionId,
    const UuidValueConverter().toJson,
  ),
  'session_label': instance.sessionLabel,
  'capabilities': instance.capabilities,
  'protocol_version': instance.protocolVersion,
  'last_seen_at': instance.lastSeenAt,
  'interface_identity_network_node_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.interfaceIdentityNetworkNodeId,
        const UuidValueConverter().toJson,
      ),
  'interface_session_network_binding_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.interfaceSessionNetworkBindingId,
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

_InterfaceRendererPanePackageCapabilityState
_$InterfaceRendererPanePackageCapabilityStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceRendererPanePackageCapabilityState(
  panePackageId: _$JsonConverterFromJson<String, UuidValue>(
    json['pane_package_id'],
    const UuidValueConverter().fromJson,
  ),
  panePackageName: json['pane_package_name'] as String?,
  paneKind: json['pane_kind'] as String,
);

Map<String, dynamic> _$InterfaceRendererPanePackageCapabilityStateToJson(
  _InterfaceRendererPanePackageCapabilityState instance,
) => <String, dynamic>{
  'pane_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.panePackageId,
    const UuidValueConverter().toJson,
  ),
  'pane_package_name': instance.panePackageName,
  'pane_kind': instance.paneKind,
};

_InterfaceRendererViewCapabilityState
_$InterfaceRendererViewCapabilityStateFromJson(Map<String, dynamic> json) =>
    _InterfaceRendererViewCapabilityState(
      viewRef: json['view_ref'] as String?,
      projectionViewKey: json['projection_view_key'] as String?,
      paneKind: json['pane_kind'] as String?,
      hasDecoder: json['has_decoder'] as bool,
    );

Map<String, dynamic> _$InterfaceRendererViewCapabilityStateToJson(
  _InterfaceRendererViewCapabilityState instance,
) => <String, dynamic>{
  'view_ref': instance.viewRef,
  'projection_view_key': instance.projectionViewKey,
  'pane_kind': instance.paneKind,
  'has_decoder': instance.hasDecoder,
};

_InterfaceRendererCacheCapabilityState
_$InterfaceRendererCacheCapabilityStateFromJson(Map<String, dynamic> json) =>
    _InterfaceRendererCacheCapabilityState(
      storeKind: json['store_kind'] as String,
      supportsNamespaceReplace: json['supports_namespace_replace'] as bool,
      supportsPersistentStorage: json['supports_persistent_storage'] as bool,
      supportsCursorLookup: json['supports_cursor_lookup'] as bool,
    );

Map<String, dynamic> _$InterfaceRendererCacheCapabilityStateToJson(
  _InterfaceRendererCacheCapabilityState instance,
) => <String, dynamic>{
  'store_kind': instance.storeKind,
  'supports_namespace_replace': instance.supportsNamespaceReplace,
  'supports_persistent_storage': instance.supportsPersistentStorage,
  'supports_cursor_lookup': instance.supportsCursorLookup,
};

_InterfaceRendererCapabilitiesState
_$InterfaceRendererCapabilitiesStateFromJson(Map<String, dynamic> json) =>
    _InterfaceRendererCapabilitiesState(
      rendererId: json['renderer_id'] as String,
      rendererKind: json['renderer_kind'] as String,
      rendererVersion: json['renderer_version'] as String?,
      interfacePackageId: _$JsonConverterFromJson<String, UuidValue>(
        json['interface_package_id'],
        const UuidValueConverter().fromJson,
      ),
      interfacePackageName: json['interface_package_name'] as String?,
      experienceKeys:
          (json['experience_keys'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      panePackages:
          (json['pane_packages'] as List<dynamic>?)
              ?.map(
                (e) => InterfaceRendererPanePackageCapabilityState.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
      viewCapabilities:
          (json['view_capabilities'] as List<dynamic>?)
              ?.map(
                (e) => InterfaceRendererViewCapabilityState.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
      cache: json['cache'] == null
          ? null
          : InterfaceRendererCacheCapabilityState.fromJson(
              json['cache'] as Map<String, dynamic>,
            ),
      reportedAt: json['reported_at'] as String?,
    );

Map<String, dynamic> _$InterfaceRendererCapabilitiesStateToJson(
  _InterfaceRendererCapabilitiesState instance,
) => <String, dynamic>{
  'renderer_id': instance.rendererId,
  'renderer_kind': instance.rendererKind,
  'renderer_version': instance.rendererVersion,
  'interface_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.interfacePackageId,
    const UuidValueConverter().toJson,
  ),
  'interface_package_name': instance.interfacePackageName,
  'experience_keys': instance.experienceKeys,
  'pane_packages': instance.panePackages.map((e) => e.toJson()).toList(),
  'view_capabilities': instance.viewCapabilities
      .map((e) => e.toJson())
      .toList(),
  'cache': instance.cache?.toJson(),
  'reported_at': instance.reportedAt,
};

_InterfaceHostViewStateDigestEntryState
_$InterfaceHostViewStateDigestEntryStateFromJson(Map<String, dynamic> json) =>
    _InterfaceHostViewStateDigestEntryState(
      paneStateKey: json['pane_state_key'] as String,
      digest: json['digest'] as String,
      viewRef: json['view_ref'] as String?,
      projectionViewKey: json['projection_view_key'] as String?,
      projectionHash: json['projection_hash'] as String?,
      headCommitId: json['head_commit_id'] as String?,
      graphHashPost: json['graph_hash_post'] as String?,
    );

Map<String, dynamic> _$InterfaceHostViewStateDigestEntryStateToJson(
  _InterfaceHostViewStateDigestEntryState instance,
) => <String, dynamic>{
  'pane_state_key': instance.paneStateKey,
  'digest': instance.digest,
  'view_ref': instance.viewRef,
  'projection_view_key': instance.projectionViewKey,
  'projection_hash': instance.projectionHash,
  'head_commit_id': instance.headCommitId,
  'graph_hash_post': instance.graphHashPost,
};

_InterfaceHostViewStateCursorState _$InterfaceHostViewStateCursorStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceHostViewStateCursorState(
  cursor: json['cursor'] as String,
  digest: json['digest'] as String,
  materializedEntryCount: (json['materialized_entry_count'] as num).toInt(),
  entryDigests:
      (json['entry_digests'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceHostViewStateDigestEntryState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  computedAt: json['computed_at'] as String?,
);

Map<String, dynamic> _$InterfaceHostViewStateCursorStateToJson(
  _InterfaceHostViewStateCursorState instance,
) => <String, dynamic>{
  'cursor': instance.cursor,
  'digest': instance.digest,
  'materialized_entry_count': instance.materializedEntryCount,
  'entry_digests': instance.entryDigests.map((e) => e.toJson()).toList(),
  'computed_at': instance.computedAt,
};

_InterfaceLaneSyncState _$InterfaceLaneSyncStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceLaneSyncState(
  enabled: json['enabled'] as bool,
  watching: json['watching'] as bool,
  windowKey: json['window_key'] as String?,
  laneId: _$JsonConverterFromJson<String, UuidValue>(
    json['lane_id'],
    const UuidValueConverter().fromJson,
  ),
  branchId: _$JsonConverterFromJson<String, UuidValue>(
    json['branch_id'],
    const UuidValueConverter().fromJson,
  ),
  projectionHash: json['projection_hash'] as String?,
  lastCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['last_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  lastGraphHashPost: json['last_graph_hash_post'] as String?,
  updatesReceived: (json['updates_received'] as num).toInt(),
  advancedCount: (json['advanced_count'] as num).toInt(),
  lastSyncedAt: json['last_synced_at'] as String?,
  error: json['error'] as String?,
);

Map<String, dynamic> _$InterfaceLaneSyncStateToJson(
  _InterfaceLaneSyncState instance,
) => <String, dynamic>{
  'enabled': instance.enabled,
  'watching': instance.watching,
  'window_key': instance.windowKey,
  'lane_id': _$JsonConverterToJson<String, UuidValue>(
    instance.laneId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.branchId,
    const UuidValueConverter().toJson,
  ),
  'projection_hash': instance.projectionHash,
  'last_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.lastCommitId,
    const UuidValueConverter().toJson,
  ),
  'last_graph_hash_post': instance.lastGraphHashPost,
  'updates_received': instance.updatesReceived,
  'advanced_count': instance.advancedCount,
  'last_synced_at': instance.lastSyncedAt,
  'error': instance.error,
};

_InterfaceEnvironmentAdmissionRoleEligibilityState
_$InterfaceEnvironmentAdmissionRoleEligibilityStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceEnvironmentAdmissionRoleEligibilityState(
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

Map<String, dynamic> _$InterfaceEnvironmentAdmissionRoleEligibilityStateToJson(
  _InterfaceEnvironmentAdmissionRoleEligibilityState instance,
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

_InterfaceEnvironmentAdmissionRoleBindingState
_$InterfaceEnvironmentAdmissionRoleBindingStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceEnvironmentAdmissionRoleBindingState(
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

Map<String, dynamic> _$InterfaceEnvironmentAdmissionRoleBindingStateToJson(
  _InterfaceEnvironmentAdmissionRoleBindingState instance,
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

_InterfaceEnvironmentAdmissionState
_$InterfaceEnvironmentAdmissionStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceEnvironmentAdmissionState(
  status: json['status'] as String,
  sourceKind: json['source_kind'] as String,
  accepted: json['accepted'] as bool,
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentProfileId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_profile_id'],
    const UuidValueConverter().fromJson,
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
      json['object_instance_graph_branch_key'] as String?,
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
  eligibleRoleCount: (json['eligible_role_count'] as num).toInt(),
  bindingCount: (json['binding_count'] as num).toInt(),
  eligibleRoles:
      (json['eligible_roles'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceEnvironmentAdmissionRoleEligibilityState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  bindings:
      (json['bindings'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceEnvironmentAdmissionRoleBindingState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  blockers:
      (json['blockers'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  error: json['error'] as String?,
  reason: json['reason'] as String?,
  updatedAt: json['updated_at'] as String?,
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$InterfaceEnvironmentAdmissionStateToJson(
  _InterfaceEnvironmentAdmissionState instance,
) => <String, dynamic>{
  'status': instance.status,
  'source_kind': instance.sourceKind,
  'accepted': instance.accepted,
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentId,
    const UuidValueConverter().toJson,
  ),
  'environment_profile_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentProfileId,
    const UuidValueConverter().toJson,
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
  'eligible_role_count': instance.eligibleRoleCount,
  'binding_count': instance.bindingCount,
  'eligible_roles': instance.eligibleRoles.map((e) => e.toJson()).toList(),
  'bindings': instance.bindings.map((e) => e.toJson()).toList(),
  'blockers': instance.blockers,
  'error': instance.error,
  'reason': instance.reason,
  'updated_at': instance.updatedAt,
  'evidence': instance.evidence,
};

_InterfaceEnvironmentNavigationState
_$InterfaceEnvironmentNavigationStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceEnvironmentNavigationState(
  status: json['status'] as String,
  sourceKind: json['source_kind'] as String,
  accepted: json['accepted'] as bool,
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentSessionId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_session_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentNavigationContextId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_navigation_context_id'],
    const UuidValueConverter().fromJson,
  ),
  key: json['key'] as String?,
  processId: _$JsonConverterFromJson<String, UuidValue>(
    json['process_id'],
    const UuidValueConverter().fromJson,
  ),
  threadId: _$JsonConverterFromJson<String, UuidValue>(
    json['thread_id'],
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
  blockers:
      (json['blockers'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  error: json['error'] as String?,
  reason: json['reason'] as String?,
  updatedAt: json['updated_at'] as String?,
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$InterfaceEnvironmentNavigationStateToJson(
  _InterfaceEnvironmentNavigationState instance,
) => <String, dynamic>{
  'status': instance.status,
  'source_kind': instance.sourceKind,
  'accepted': instance.accepted,
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentId,
    const UuidValueConverter().toJson,
  ),
  'environment_session_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentSessionId,
    const UuidValueConverter().toJson,
  ),
  'environment_navigation_context_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentNavigationContextId,
    const UuidValueConverter().toJson,
  ),
  'key': instance.key,
  'process_id': _$JsonConverterToJson<String, UuidValue>(
    instance.processId,
    const UuidValueConverter().toJson,
  ),
  'thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadId,
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
  'blockers': instance.blockers,
  'error': instance.error,
  'reason': instance.reason,
  'updated_at': instance.updatedAt,
  'evidence': instance.evidence,
};

_InterfaceEnvironmentSessionState _$InterfaceEnvironmentSessionStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceEnvironmentSessionState(
  status: json['status'] as String,
  sourceKind: json['source_kind'] as String,
  accepted: json['accepted'] as bool,
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentProfileId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_profile_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentSessionId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_session_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentSessionKey: json['environment_session_key'] as String?,
  identitySessionId: _$JsonConverterFromJson<String, UuidValue>(
    json['identity_session_id'],
    const UuidValueConverter().fromJson,
  ),
  identityMemberId: _$JsonConverterFromJson<String, UuidValue>(
    json['identity_member_id'],
    const UuidValueConverter().fromJson,
  ),
  identityActorRoleCount: (json['identity_actor_role_count'] as num).toInt(),
  blockers:
      (json['blockers'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  error: json['error'] as String?,
  reason: json['reason'] as String?,
  updatedAt: json['updated_at'] as String?,
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$InterfaceEnvironmentSessionStateToJson(
  _InterfaceEnvironmentSessionState instance,
) => <String, dynamic>{
  'status': instance.status,
  'source_kind': instance.sourceKind,
  'accepted': instance.accepted,
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentId,
    const UuidValueConverter().toJson,
  ),
  'environment_profile_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentProfileId,
    const UuidValueConverter().toJson,
  ),
  'environment_session_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentSessionId,
    const UuidValueConverter().toJson,
  ),
  'environment_session_key': instance.environmentSessionKey,
  'identity_session_id': _$JsonConverterToJson<String, UuidValue>(
    instance.identitySessionId,
    const UuidValueConverter().toJson,
  ),
  'identity_member_id': _$JsonConverterToJson<String, UuidValue>(
    instance.identityMemberId,
    const UuidValueConverter().toJson,
  ),
  'identity_actor_role_count': instance.identityActorRoleCount,
  'blockers': instance.blockers,
  'error': instance.error,
  'reason': instance.reason,
  'updated_at': instance.updatedAt,
  'evidence': instance.evidence,
};

_InterfaceExperienceLensActionState
_$InterfaceExperienceLensActionStateFromJson(Map<String, dynamic> json) =>
    _InterfaceExperienceLensActionState(
      actionKey: json['action_key'] as String,
      actionKind: json['action_kind'] as String?,
      targetRef: json['target_ref'] as String?,
      label: json['label'] as String?,
      viewInvocationActionConfigId: const UuidValueConverter().fromJson(
        json['view_invocation_action_config_id'] as String,
      ),
      experienceInvocationActionConfigId:
          _$JsonConverterFromJson<String, UuidValue>(
            json['experience_invocation_action_config_id'],
            const UuidValueConverter().fromJson,
          ),
      apiCapabilityEndpointId: _$JsonConverterFromJson<String, UuidValue>(
        json['api_capability_endpoint_id'],
        const UuidValueConverter().fromJson,
      ),
      sdkOperationId: _$JsonConverterFromJson<String, UuidValue>(
        json['sdk_operation_id'],
        const UuidValueConverter().fromJson,
      ),
    );

Map<String, dynamic> _$InterfaceExperienceLensActionStateToJson(
  _InterfaceExperienceLensActionState instance,
) => <String, dynamic>{
  'action_key': instance.actionKey,
  'action_kind': instance.actionKind,
  'target_ref': instance.targetRef,
  'label': instance.label,
  'view_invocation_action_config_id': const UuidValueConverter().toJson(
    instance.viewInvocationActionConfigId,
  ),
  'experience_invocation_action_config_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.experienceInvocationActionConfigId,
        const UuidValueConverter().toJson,
      ),
  'api_capability_endpoint_id': _$JsonConverterToJson<String, UuidValue>(
    instance.apiCapabilityEndpointId,
    const UuidValueConverter().toJson,
  ),
  'sdk_operation_id': _$JsonConverterToJson<String, UuidValue>(
    instance.sdkOperationId,
    const UuidValueConverter().toJson,
  ),
};

_InterfaceExperienceLensState _$InterfaceExperienceLensStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceExperienceLensState(
  status: json['status'] as String,
  sourceKind: json['source_kind'] as String,
  accepted: json['accepted'] as bool,
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentSessionId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_session_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentNavigationContextId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_navigation_context_id'],
    const UuidValueConverter().fromJson,
  ),
  experienceName: json['experience_name'] as String?,
  viewRef: json['view_ref'] as String?,
  sectionKey: json['section_key'] as String?,
  observableId: _$JsonConverterFromJson<String, UuidValue>(
    json['observable_id'],
    const UuidValueConverter().fromJson,
  ),
  sectionGraphBindingKey: json['section_graph_binding_key'] as String?,
  projectionExperienceViewInstanceId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['projection_experience_view_instance_id'],
        const UuidValueConverter().fromJson,
      ),
  projectionExperienceGraphIdentityId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['projection_experience_graph_identity_id'],
        const UuidValueConverter().fromJson,
      ),
  objectProjectionGraphIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_projection_graph_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  focusScopeId: _$JsonConverterFromJson<String, UuidValue>(
    json['focus_scope_id'],
    const UuidValueConverter().fromJson,
  ),
  focusId: _$JsonConverterFromJson<String, UuidValue>(
    json['focus_id'],
    const UuidValueConverter().fromJson,
  ),
  actionCount: (json['action_count'] as num).toInt(),
  actions:
      (json['actions'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceExperienceLensActionState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  blockers:
      (json['blockers'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  error: json['error'] as String?,
  reason: json['reason'] as String?,
  updatedAt: json['updated_at'] as String?,
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$InterfaceExperienceLensStateToJson(
  _InterfaceExperienceLensState instance,
) => <String, dynamic>{
  'status': instance.status,
  'source_kind': instance.sourceKind,
  'accepted': instance.accepted,
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentId,
    const UuidValueConverter().toJson,
  ),
  'environment_session_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentSessionId,
    const UuidValueConverter().toJson,
  ),
  'environment_navigation_context_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentNavigationContextId,
    const UuidValueConverter().toJson,
  ),
  'experience_name': instance.experienceName,
  'view_ref': instance.viewRef,
  'section_key': instance.sectionKey,
  'observable_id': _$JsonConverterToJson<String, UuidValue>(
    instance.observableId,
    const UuidValueConverter().toJson,
  ),
  'section_graph_binding_key': instance.sectionGraphBindingKey,
  'projection_experience_view_instance_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.projectionExperienceViewInstanceId,
        const UuidValueConverter().toJson,
      ),
  'projection_experience_graph_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.projectionExperienceGraphIdentityId,
        const UuidValueConverter().toJson,
      ),
  'object_projection_graph_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.objectProjectionGraphIdentityId,
        const UuidValueConverter().toJson,
      ),
  'focus_scope_id': _$JsonConverterToJson<String, UuidValue>(
    instance.focusScopeId,
    const UuidValueConverter().toJson,
  ),
  'focus_id': _$JsonConverterToJson<String, UuidValue>(
    instance.focusId,
    const UuidValueConverter().toJson,
  ),
  'action_count': instance.actionCount,
  'actions': instance.actions.map((e) => e.toJson()).toList(),
  'blockers': instance.blockers,
  'error': instance.error,
  'reason': instance.reason,
  'updated_at': instance.updatedAt,
  'evidence': instance.evidence,
};

_InterfaceAppScreenState _$InterfaceAppScreenStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceAppScreenState(
  status: json['status'] as String,
  accepted: json['accepted'] as bool,
  appPackageId: _$JsonConverterFromJson<String, UuidValue>(
    json['app_package_id'],
    const UuidValueConverter().fromJson,
  ),
  appPackageBranchId: _$JsonConverterFromJson<String, UuidValue>(
    json['app_package_branch_id'],
    const UuidValueConverter().fromJson,
  ),
  appPackageObjectInstanceGraphCommitId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['app_package_object_instance_graph_commit_id'],
        const UuidValueConverter().fromJson,
      ),
  appConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['app_config_id'],
    const UuidValueConverter().fromJson,
  ),
  appConfigObjectInstanceGraphCommitId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['app_config_object_instance_graph_commit_id'],
        const UuidValueConverter().fromJson,
      ),
  appConfigScreenConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['app_config_screen_config_id'],
    const UuidValueConverter().fromJson,
  ),
  screenKey: json['screen_key'] as String?,
  projectionExperienceId: _$JsonConverterFromJson<String, UuidValue>(
    json['projection_experience_id'],
    const UuidValueConverter().fromJson,
  ),
  projectionExperienceBranchId: _$JsonConverterFromJson<String, UuidValue>(
    json['projection_experience_branch_id'],
    const UuidValueConverter().fromJson,
  ),
  projectionExperienceHeadCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['projection_experience_head_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  projectionExperienceLayoutGraphBindingId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['projection_experience_layout_graph_binding_id'],
        const UuidValueConverter().fromJson,
      ),
  experienceName: json['experience_name'] as String?,
  layoutBindingKey: json['layout_binding_key'] as String?,
  blockers:
      (json['blockers'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  error: json['error'] as String?,
  reason: json['reason'] as String?,
  updatedAt: json['updated_at'] as String?,
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$InterfaceAppScreenStateToJson(
  _InterfaceAppScreenState instance,
) => <String, dynamic>{
  'status': instance.status,
  'accepted': instance.accepted,
  'app_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.appPackageId,
    const UuidValueConverter().toJson,
  ),
  'app_package_branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.appPackageBranchId,
    const UuidValueConverter().toJson,
  ),
  'app_package_object_instance_graph_commit_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.appPackageObjectInstanceGraphCommitId,
        const UuidValueConverter().toJson,
      ),
  'app_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.appConfigId,
    const UuidValueConverter().toJson,
  ),
  'app_config_object_instance_graph_commit_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.appConfigObjectInstanceGraphCommitId,
        const UuidValueConverter().toJson,
      ),
  'app_config_screen_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.appConfigScreenConfigId,
    const UuidValueConverter().toJson,
  ),
  'screen_key': instance.screenKey,
  'projection_experience_id': _$JsonConverterToJson<String, UuidValue>(
    instance.projectionExperienceId,
    const UuidValueConverter().toJson,
  ),
  'projection_experience_branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.projectionExperienceBranchId,
    const UuidValueConverter().toJson,
  ),
  'projection_experience_head_commit_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.projectionExperienceHeadCommitId,
        const UuidValueConverter().toJson,
      ),
  'projection_experience_layout_graph_binding_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.projectionExperienceLayoutGraphBindingId,
        const UuidValueConverter().toJson,
      ),
  'experience_name': instance.experienceName,
  'layout_binding_key': instance.layoutBindingKey,
  'blockers': instance.blockers,
  'error': instance.error,
  'reason': instance.reason,
  'updated_at': instance.updatedAt,
  'evidence': instance.evidence,
};

_InterfaceExperienceSessionNarrationEventState
_$InterfaceExperienceSessionNarrationEventStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceExperienceSessionNarrationEventState(
  commitId: _$JsonConverterFromJson<String, UuidValue>(
    json['commit_id'],
    const UuidValueConverter().fromJson,
  ),
  branchId: _$JsonConverterFromJson<String, UuidValue>(
    json['branch_id'],
    const UuidValueConverter().fromJson,
  ),
  projectionHash: json['projection_hash'] as String?,
  narrationLines:
      (json['narration_lines'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  operationLabel: json['operation_label'] as String?,
  graphHashPost: json['graph_hash_post'] as String?,
  objectInstanceGraphIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_identity_id'],
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
  projectionExperienceGraphIdentityId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['projection_experience_graph_identity_id'],
        const UuidValueConverter().fromJson,
      ),
  objectProjectionGraphIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_projection_graph_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  semantics: json['semantics'] as Map<String, dynamic>,
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$InterfaceExperienceSessionNarrationEventStateToJson(
  _InterfaceExperienceSessionNarrationEventState instance,
) => <String, dynamic>{
  'commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.commitId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.branchId,
    const UuidValueConverter().toJson,
  ),
  'projection_hash': instance.projectionHash,
  'narration_lines': instance.narrationLines,
  'operation_label': instance.operationLabel,
  'graph_hash_post': instance.graphHashPost,
  'object_instance_graph_identity_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphIdentityId,
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
  'projection_experience_graph_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.projectionExperienceGraphIdentityId,
        const UuidValueConverter().toJson,
      ),
  'object_projection_graph_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.objectProjectionGraphIdentityId,
        const UuidValueConverter().toJson,
      ),
  'semantics': instance.semantics,
  'evidence': instance.evidence,
};

_InterfaceExperienceSessionNarrationState
_$InterfaceExperienceSessionNarrationStateFromJson(Map<String, dynamic> json) =>
    _InterfaceExperienceSessionNarrationState(
      status: json['status'] as String,
      featureKey: json['feature_key'] as String?,
      experienceName: json['experience_name'] as String?,
      viewRef: json['view_ref'] as String?,
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      featureLeaseId: json['feature_lease_id'] as String?,
      eventCount: (json['event_count'] as num).toInt(),
      lastCommitId: _$JsonConverterFromJson<String, UuidValue>(
        json['last_commit_id'],
        const UuidValueConverter().fromJson,
      ),
      events:
          (json['events'] as List<dynamic>?)
              ?.map(
                (e) => InterfaceExperienceSessionNarrationEventState.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
      error: json['error'] as String?,
      evidence: json['evidence'] as Map<String, dynamic>,
    );

Map<String, dynamic> _$InterfaceExperienceSessionNarrationStateToJson(
  _InterfaceExperienceSessionNarrationState instance,
) => <String, dynamic>{
  'status': instance.status,
  'feature_key': instance.featureKey,
  'experience_name': instance.experienceName,
  'view_ref': instance.viewRef,
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'feature_lease_id': instance.featureLeaseId,
  'event_count': instance.eventCount,
  'last_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.lastCommitId,
    const UuidValueConverter().toJson,
  ),
  'events': instance.events.map((e) => e.toJson()).toList(),
  'error': instance.error,
  'evidence': instance.evidence,
};

_InterfaceBackendState _$InterfaceBackendStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceBackendState(
  available: json['available'] as bool,
  manifestPath: json['manifest_path'] as String?,
  registryPath: json['registry_path'] as String?,
  databasePath: json['database_path'] as String?,
  databaseExists: json['database_exists'] as bool,
  environmentId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_id'],
    const UuidValueConverter().fromJson,
  ),
  opgCount: (json['opg_count'] as num).toInt(),
  projectionBundleAvailable: json['projection_bundle_available'] as bool,
  projectionPlanCount: (json['projection_plan_count'] as num).toInt(),
  tableCount: (json['table_count'] as num).toInt(),
  reason: json['reason'] as String?,
);

Map<String, dynamic> _$InterfaceBackendStateToJson(
  _InterfaceBackendState instance,
) => <String, dynamic>{
  'available': instance.available,
  'manifest_path': instance.manifestPath,
  'registry_path': instance.registryPath,
  'database_path': instance.databasePath,
  'database_exists': instance.databaseExists,
  'environment_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentId,
    const UuidValueConverter().toJson,
  ),
  'opg_count': instance.opgCount,
  'projection_bundle_available': instance.projectionBundleAvailable,
  'projection_plan_count': instance.projectionPlanCount,
  'table_count': instance.tableCount,
  'reason': instance.reason,
};

_InterfaceLocalServiceHostState _$InterfaceLocalServiceHostStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceLocalServiceHostState(
  managed: json['managed'] as bool,
  supported: json['supported'] as bool,
  socketPath: json['socket_path'] as String?,
  available: json['available'] as bool,
  ready: json['ready'] as bool,
  status: json['status'] as String,
  hostId: json['host_id'] as String?,
  hostVersion: json['host_version'] as String?,
  protocolVersion: json['protocol_version'] as String?,
  capabilities:
      (json['capabilities'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  error: json['error'] as String?,
  probeDurationMs: (json['probe_duration_ms'] as num?)?.toInt(),
  lastCheckedAt: json['last_checked_at'] as String?,
);

Map<String, dynamic> _$InterfaceLocalServiceHostStateToJson(
  _InterfaceLocalServiceHostState instance,
) => <String, dynamic>{
  'managed': instance.managed,
  'supported': instance.supported,
  'socket_path': instance.socketPath,
  'available': instance.available,
  'ready': instance.ready,
  'status': instance.status,
  'host_id': instance.hostId,
  'host_version': instance.hostVersion,
  'protocol_version': instance.protocolVersion,
  'capabilities': instance.capabilities,
  'error': instance.error,
  'probe_duration_ms': instance.probeDurationMs,
  'last_checked_at': instance.lastCheckedAt,
};

_InterfaceLocalNodeRuntimeState _$InterfaceLocalNodeRuntimeStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceLocalNodeRuntimeState(
  managed: json['managed'] as bool,
  available: json['available'] as bool,
  ready: json['ready'] as bool,
  phase: json['phase'] as String,
  activeTargetId: json['active_target_id'] as String?,
  targetKey: json['target_key'] as String?,
  displayName: json['display_name'] as String?,
  backendKind: json['backend_kind'] as String?,
  isActive: json['is_active'] as bool,
  isHealthy: json['is_healthy'] as bool,
  nodeBaseUrl: json['node_base_url'] as String?,
  nodeWebsocketPath: json['node_websocket_path'] as String?,
  summary: json['summary'] as String?,
  error: json['error'] as String?,
  updatedAt: json['updated_at'] as String?,
  recentLogLines:
      (json['recent_log_lines'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  targetStatuses:
      (json['target_statuses'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceOperationTargetState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$InterfaceLocalNodeRuntimeStateToJson(
  _InterfaceLocalNodeRuntimeState instance,
) => <String, dynamic>{
  'managed': instance.managed,
  'available': instance.available,
  'ready': instance.ready,
  'phase': instance.phase,
  'active_target_id': instance.activeTargetId,
  'target_key': instance.targetKey,
  'display_name': instance.displayName,
  'backend_kind': instance.backendKind,
  'is_active': instance.isActive,
  'is_healthy': instance.isHealthy,
  'node_base_url': instance.nodeBaseUrl,
  'node_websocket_path': instance.nodeWebsocketPath,
  'summary': instance.summary,
  'error': instance.error,
  'updated_at': instance.updatedAt,
  'recent_log_lines': instance.recentLogLines,
  'target_statuses': instance.targetStatuses.map((e) => e.toJson()).toList(),
};

_InterfaceHostedRuntimeServiceState
_$InterfaceHostedRuntimeServiceStateFromJson(Map<String, dynamic> json) =>
    _InterfaceHostedRuntimeServiceState(
      serviceName: json['service_name'] as String,
      endpointRefs:
          (json['endpoint_refs'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      streamEndpointRefs:
          (json['stream_endpoint_refs'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
    );

Map<String, dynamic> _$InterfaceHostedRuntimeServiceStateToJson(
  _InterfaceHostedRuntimeServiceState instance,
) => <String, dynamic>{
  'service_name': instance.serviceName,
  'endpoint_refs': instance.endpointRefs,
  'stream_endpoint_refs': instance.streamEndpointRefs,
};

_InterfaceHostedServiceRequirementState
_$InterfaceHostedServiceRequirementStateFromJson(Map<String, dynamic> json) =>
    _InterfaceHostedServiceRequirementState(
      serviceName: json['service_name'] as String,
      serviceLabel: json['service_label'] as String?,
      isRequired: json['is_required'] as bool,
      status: json['status'] as String,
      sourceKind: json['source_kind'] as String,
      summary: json['summary'] as String?,
      error: json['error'] as String?,
      matchedRuntimeHostId: json['matched_runtime_host_id'] as String?,
      endpointRefs:
          (json['endpoint_refs'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      streamEndpointRefs:
          (json['stream_endpoint_refs'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
    );

Map<String, dynamic> _$InterfaceHostedServiceRequirementStateToJson(
  _InterfaceHostedServiceRequirementState instance,
) => <String, dynamic>{
  'service_name': instance.serviceName,
  'service_label': instance.serviceLabel,
  'is_required': instance.isRequired,
  'status': instance.status,
  'source_kind': instance.sourceKind,
  'summary': instance.summary,
  'error': instance.error,
  'matched_runtime_host_id': instance.matchedRuntimeHostId,
  'endpoint_refs': instance.endpointRefs,
  'stream_endpoint_refs': instance.streamEndpointRefs,
};

_InterfaceHostedRuntimeState _$InterfaceHostedRuntimeStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceHostedRuntimeState(
  hostId: json['host_id'] as String,
  hostVersion: json['host_version'] as String?,
  protocolVersion: json['protocol_version'] as String?,
  readinessStatus: json['readiness_status'] as String,
  isReady: json['is_ready'] as bool,
  isAlive: json['is_alive'] as bool,
  supportsStreamEvents: json['supports_stream_events'] as bool,
  summary: json['summary'] as String?,
  error: json['error'] as String?,
  updatedAt: json['updated_at'] as String?,
  probeDurationMs: (json['probe_duration_ms'] as num?)?.toInt(),
  services:
      (json['services'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceHostedRuntimeServiceState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$InterfaceHostedRuntimeStateToJson(
  _InterfaceHostedRuntimeState instance,
) => <String, dynamic>{
  'host_id': instance.hostId,
  'host_version': instance.hostVersion,
  'protocol_version': instance.protocolVersion,
  'readiness_status': instance.readinessStatus,
  'is_ready': instance.isReady,
  'is_alive': instance.isAlive,
  'supports_stream_events': instance.supportsStreamEvents,
  'summary': instance.summary,
  'error': instance.error,
  'updated_at': instance.updatedAt,
  'probe_duration_ms': instance.probeDurationMs,
  'services': instance.services.map((e) => e.toJson()).toList(),
};

_InterfaceHostedServicesState _$InterfaceHostedServicesStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceHostedServicesState(
  available: json['available'] as bool,
  sourceKind: json['source_kind'] as String,
  updatedAt: json['updated_at'] as String?,
  error: json['error'] as String?,
  refreshDurationMs: (json['refresh_duration_ms'] as num?)?.toInt(),
  runtimeCount: (json['runtime_count'] as num).toInt(),
  serviceCount: (json['service_count'] as num).toInt(),
  requiredServiceCount: (json['required_service_count'] as num?)?.toInt(),
  satisfiedServiceCount: (json['satisfied_service_count'] as num?)?.toInt(),
  serviceRequirements:
      (json['service_requirements'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceHostedServiceRequirementState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  runtimes:
      (json['runtimes'] as List<dynamic>?)
          ?.map(
            (e) =>
                InterfaceHostedRuntimeState.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$InterfaceHostedServicesStateToJson(
  _InterfaceHostedServicesState instance,
) => <String, dynamic>{
  'available': instance.available,
  'source_kind': instance.sourceKind,
  'updated_at': instance.updatedAt,
  'error': instance.error,
  'refresh_duration_ms': instance.refreshDurationMs,
  'runtime_count': instance.runtimeCount,
  'service_count': instance.serviceCount,
  'required_service_count': instance.requiredServiceCount,
  'satisfied_service_count': instance.satisfiedServiceCount,
  'service_requirements': instance.serviceRequirements
      .map((e) => e.toJson())
      .toList(),
  'runtimes': instance.runtimes.map((e) => e.toJson()).toList(),
};

_InterfaceCurrentScreen _$InterfaceCurrentScreenFromJson(
  Map<String, dynamic> json,
) => _InterfaceCurrentScreen(
  screenKind: json['screen_kind'] as String,
  screenKey: json['screen_key'] as String,
  sourceKind: json['source_kind'] as String,
  title: json['title'] as String?,
  message: json['message'] as String?,
  windowId: _$JsonConverterFromJson<String, UuidValue>(
    json['window_id'],
    const UuidValueConverter().fromJson,
  ),
  sectionId: _$JsonConverterFromJson<String, UuidValue>(
    json['section_id'],
    const UuidValueConverter().fromJson,
  ),
  focusScopeId: _$JsonConverterFromJson<String, UuidValue>(
    json['focus_scope_id'],
    const UuidValueConverter().fromJson,
  ),
  focusId: _$JsonConverterFromJson<String, UuidValue>(
    json['focus_id'],
    const UuidValueConverter().fromJson,
  ),
  branchId: _$JsonConverterFromJson<String, UuidValue>(
    json['branch_id'],
    const UuidValueConverter().fromJson,
  ),
  projectionViewId: json['projection_view_id'] as String?,
  paneKey: json['pane_key'] as String?,
);

Map<String, dynamic> _$InterfaceCurrentScreenToJson(
  _InterfaceCurrentScreen instance,
) => <String, dynamic>{
  'screen_kind': instance.screenKind,
  'screen_key': instance.screenKey,
  'source_kind': instance.sourceKind,
  'title': instance.title,
  'message': instance.message,
  'window_id': _$JsonConverterToJson<String, UuidValue>(
    instance.windowId,
    const UuidValueConverter().toJson,
  ),
  'section_id': _$JsonConverterToJson<String, UuidValue>(
    instance.sectionId,
    const UuidValueConverter().toJson,
  ),
  'focus_scope_id': _$JsonConverterToJson<String, UuidValue>(
    instance.focusScopeId,
    const UuidValueConverter().toJson,
  ),
  'focus_id': _$JsonConverterToJson<String, UuidValue>(
    instance.focusId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.branchId,
    const UuidValueConverter().toJson,
  ),
  'projection_view_id': instance.projectionViewId,
  'pane_key': instance.paneKey,
};

_InterfaceAllowedAction _$InterfaceAllowedActionFromJson(
  Map<String, dynamic> json,
) => _InterfaceAllowedAction(
  actionKey: json['action_key'] as String,
  label: json['label'] as String,
  enabled: json['enabled'] as bool,
  reason: json['reason'] as String?,
  payloadSchemaHint: json['payload_schema_hint'] as String?,
);

Map<String, dynamic> _$InterfaceAllowedActionToJson(
  _InterfaceAllowedAction instance,
) => <String, dynamic>{
  'action_key': instance.actionKey,
  'label': instance.label,
  'enabled': instance.enabled,
  'reason': instance.reason,
  'payload_schema_hint': instance.payloadSchemaHint,
};

_InterfaceHostRecoveryCapabilityState
_$InterfaceHostRecoveryCapabilityStateFromJson(Map<String, dynamic> json) =>
    _InterfaceHostRecoveryCapabilityState(
      key: json['key'] as String,
      label: json['label'] as String,
      enabled: json['enabled'] as bool,
      reason: json['reason'] as String?,
      actionKey: json['action_key'] as String?,
    );

Map<String, dynamic> _$InterfaceHostRecoveryCapabilityStateToJson(
  _InterfaceHostRecoveryCapabilityState instance,
) => <String, dynamic>{
  'key': instance.key,
  'label': instance.label,
  'enabled': instance.enabled,
  'reason': instance.reason,
  'action_key': instance.actionKey,
};

_InterfaceWorkspaceCandidate _$InterfaceWorkspaceCandidateFromJson(
  Map<String, dynamic> json,
) => _InterfaceWorkspaceCandidate(
  selectorKey: json['selector_key'] as String,
  label: json['label'] as String,
  workspaceRoot: json['workspace_root'] as String,
  registrySource: json['registry_source'] as String,
  compatibilityMode: json['compatibility_mode'] as bool,
  workspaceTomlPath: json['workspace_toml_path'] as String?,
  summary: json['summary'] as String?,
  environmentCount: (json['environment_count'] as num).toInt(),
  apiCount: (json['api_count'] as num).toInt(),
  serviceCount: (json['service_count'] as num).toInt(),
  experienceCount: (json['experience_count'] as num).toInt(),
  interfaceCount: (json['interface_count'] as num).toInt(),
  lifecycle: json['lifecycle'] == null
      ? null
      : InterfaceWorkspaceLifecycleState.fromJson(
          json['lifecycle'] as Map<String, dynamic>,
        ),
);

Map<String, dynamic> _$InterfaceWorkspaceCandidateToJson(
  _InterfaceWorkspaceCandidate instance,
) => <String, dynamic>{
  'selector_key': instance.selectorKey,
  'label': instance.label,
  'workspace_root': instance.workspaceRoot,
  'registry_source': instance.registrySource,
  'compatibility_mode': instance.compatibilityMode,
  'workspace_toml_path': instance.workspaceTomlPath,
  'summary': instance.summary,
  'environment_count': instance.environmentCount,
  'api_count': instance.apiCount,
  'service_count': instance.serviceCount,
  'experience_count': instance.experienceCount,
  'interface_count': instance.interfaceCount,
  'lifecycle': instance.lifecycle?.toJson(),
};

_InterfaceWorkspaceDiscoveryState _$InterfaceWorkspaceDiscoveryStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceWorkspaceDiscoveryState(
  selectionRequired: json['selection_required'] as bool,
  selectedSelectorKey: json['selected_selector_key'] as String?,
  candidates:
      (json['candidates'] as List<dynamic>?)
          ?.map(
            (e) =>
                InterfaceWorkspaceCandidate.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  error: json['error'] as String?,
);

Map<String, dynamic> _$InterfaceWorkspaceDiscoveryStateToJson(
  _InterfaceWorkspaceDiscoveryState instance,
) => <String, dynamic>{
  'selection_required': instance.selectionRequired,
  'selected_selector_key': instance.selectedSelectorKey,
  'candidates': instance.candidates.map((e) => e.toJson()).toList(),
  'error': instance.error,
};

_InterfaceSelectedWorkspaceState _$InterfaceSelectedWorkspaceStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceSelectedWorkspaceState(
  selectorKey: json['selector_key'] as String,
  label: json['label'] as String,
  workspaceRoot: json['workspace_root'] as String,
  registrySource: json['registry_source'] as String,
  compatibilityMode: json['compatibility_mode'] as bool,
  workspaceTomlPath: json['workspace_toml_path'] as String?,
  summary: json['summary'] as String?,
  environmentCount: (json['environment_count'] as num).toInt(),
  apiCount: (json['api_count'] as num).toInt(),
  serviceCount: (json['service_count'] as num).toInt(),
  experienceCount: (json['experience_count'] as num).toInt(),
  interfaceCount: (json['interface_count'] as num).toInt(),
  lifecycle: json['lifecycle'] == null
      ? null
      : InterfaceWorkspaceLifecycleState.fromJson(
          json['lifecycle'] as Map<String, dynamic>,
        ),
  semanticSource: json['semantic_source'] == null
      ? null
      : InterfaceWorkspaceSemanticSourceState.fromJson(
          json['semantic_source'] as Map<String, dynamic>,
        ),
);

Map<String, dynamic> _$InterfaceSelectedWorkspaceStateToJson(
  _InterfaceSelectedWorkspaceState instance,
) => <String, dynamic>{
  'selector_key': instance.selectorKey,
  'label': instance.label,
  'workspace_root': instance.workspaceRoot,
  'registry_source': instance.registrySource,
  'compatibility_mode': instance.compatibilityMode,
  'workspace_toml_path': instance.workspaceTomlPath,
  'summary': instance.summary,
  'environment_count': instance.environmentCount,
  'api_count': instance.apiCount,
  'service_count': instance.serviceCount,
  'experience_count': instance.experienceCount,
  'interface_count': instance.interfaceCount,
  'lifecycle': instance.lifecycle?.toJson(),
  'semantic_source': instance.semanticSource?.toJson(),
};

_InterfaceWorkspaceLifecycleState _$InterfaceWorkspaceLifecycleStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceWorkspaceLifecycleState(
  status: json['status'] as String,
  summary: json['summary'] as String?,
  error: json['error'] as String?,
  joined: json['joined'] as bool,
  attachedNamespaceCount: (json['attached_namespace_count'] as num).toInt(),
  joinable: json['joinable'] as bool,
  startable: json['startable'] as bool,
  recoverable: json['recoverable'] as bool,
  leaveable: json['leaveable'] as bool,
  stoppable: json['stoppable'] as bool,
  safetyReason: json['safety_reason'] as String?,
);

Map<String, dynamic> _$InterfaceWorkspaceLifecycleStateToJson(
  _InterfaceWorkspaceLifecycleState instance,
) => <String, dynamic>{
  'status': instance.status,
  'summary': instance.summary,
  'error': instance.error,
  'joined': instance.joined,
  'attached_namespace_count': instance.attachedNamespaceCount,
  'joinable': instance.joinable,
  'startable': instance.startable,
  'recoverable': instance.recoverable,
  'leaveable': instance.leaveable,
  'stoppable': instance.stoppable,
  'safety_reason': instance.safetyReason,
};

_InterfaceWorkspaceSemanticPackageState
_$InterfaceWorkspaceSemanticPackageStateFromJson(Map<String, dynamic> json) =>
    _InterfaceWorkspaceSemanticPackageState(
      packageKind: json['package_kind'] as String,
      packageName: json['package_name'] as String,
      manifestPath: json['manifest_path'] as String,
      workspaceRelativePath: json['workspace_relative_path'] as String?,
      title: json['title'] as String?,
      fqnPrefix: json['fqn_prefix'] as String?,
      objectConfigGraphId: json['object_config_graph_id'] as String?,
      objectConfigGraphPackageId:
          json['object_config_graph_package_id'] as String?,
      semanticBranchId: json['semantic_branch_id'] as String?,
    );

Map<String, dynamic> _$InterfaceWorkspaceSemanticPackageStateToJson(
  _InterfaceWorkspaceSemanticPackageState instance,
) => <String, dynamic>{
  'package_kind': instance.packageKind,
  'package_name': instance.packageName,
  'manifest_path': instance.manifestPath,
  'workspace_relative_path': instance.workspaceRelativePath,
  'title': instance.title,
  'fqn_prefix': instance.fqnPrefix,
  'object_config_graph_id': instance.objectConfigGraphId,
  'object_config_graph_package_id': instance.objectConfigGraphPackageId,
  'semantic_branch_id': instance.semanticBranchId,
};

_InterfaceWorkspaceCommittedSemanticPackageState
_$InterfaceWorkspaceCommittedSemanticPackageStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceWorkspaceCommittedSemanticPackageState(
  selectorKey: json['selector_key'] as String,
  familyKey: json['family_key'] as String,
  familyTitle: json['family_title'] as String,
  packageKind: json['package_kind'] as String,
  label: json['label'] as String,
  moduleName: json['module_name'] as String,
  packageName: json['package_name'] as String,
  awareTomlPath: json['aware_toml_path'] as String,
  manifestRelativePath: json['manifest_relative_path'] as String,
  packageRoot: json['package_root'] as String,
  sourcesRoot: json['sources_root'] as String?,
  fqnPrefix: json['fqn_prefix'] as String,
  objectConfigGraphId: json['object_config_graph_id'] as String,
  objectConfigGraphPackageId: json['object_config_graph_package_id'] as String,
);

Map<String, dynamic> _$InterfaceWorkspaceCommittedSemanticPackageStateToJson(
  _InterfaceWorkspaceCommittedSemanticPackageState instance,
) => <String, dynamic>{
  'selector_key': instance.selectorKey,
  'family_key': instance.familyKey,
  'family_title': instance.familyTitle,
  'package_kind': instance.packageKind,
  'label': instance.label,
  'module_name': instance.moduleName,
  'package_name': instance.packageName,
  'aware_toml_path': instance.awareTomlPath,
  'manifest_relative_path': instance.manifestRelativePath,
  'package_root': instance.packageRoot,
  'sources_root': instance.sourcesRoot,
  'fqn_prefix': instance.fqnPrefix,
  'object_config_graph_id': instance.objectConfigGraphId,
  'object_config_graph_package_id': instance.objectConfigGraphPackageId,
};

_InterfaceWorkspaceCommittedSemanticPackageFamilyState
_$InterfaceWorkspaceCommittedSemanticPackageFamilyStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceWorkspaceCommittedSemanticPackageFamilyState(
  familyKey: json['family_key'] as String,
  title: json['title'] as String,
  members:
      (json['members'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceWorkspaceCommittedSemanticPackageState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic>
_$InterfaceWorkspaceCommittedSemanticPackageFamilyStateToJson(
  _InterfaceWorkspaceCommittedSemanticPackageFamilyState instance,
) => <String, dynamic>{
  'family_key': instance.familyKey,
  'title': instance.title,
  'members': instance.members.map((e) => e.toJson()).toList(),
};

_InterfaceWorkspaceMaterializationStateRef
_$InterfaceWorkspaceMaterializationStateRefFromJson(
  Map<String, dynamic> json,
) => _InterfaceWorkspaceMaterializationStateRef(
  sourceKind: json['source_kind'] as String,
  status: json['status'] as String?,
  invocationId: json['invocation_id'] as String?,
  receiptPath: json['receipt_path'] as String?,
  latestPath: json['latest_path'] as String?,
  workspaceMaterializationId: json['workspace_materialization_id'] as String?,
  workspaceMaterializationCommitId:
      json['workspace_materialization_commit_id'] as String?,
  workspaceMaterializationHeadCommitId:
      json['workspace_materialization_head_commit_id'] as String?,
);

Map<String, dynamic> _$InterfaceWorkspaceMaterializationStateRefToJson(
  _InterfaceWorkspaceMaterializationStateRef instance,
) => <String, dynamic>{
  'source_kind': instance.sourceKind,
  'status': instance.status,
  'invocation_id': instance.invocationId,
  'receipt_path': instance.receiptPath,
  'latest_path': instance.latestPath,
  'workspace_materialization_id': instance.workspaceMaterializationId,
  'workspace_materialization_commit_id':
      instance.workspaceMaterializationCommitId,
  'workspace_materialization_head_commit_id':
      instance.workspaceMaterializationHeadCommitId,
};

_InterfaceWorkspaceSemanticObjectConfigGraphPreviewState
_$InterfaceWorkspaceSemanticObjectConfigGraphPreviewStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceWorkspaceSemanticObjectConfigGraphPreviewState(
  packageKind: json['package_kind'] as String,
  packageName: json['package_name'] as String,
  manifestPath: json['manifest_path'] as String,
  objectConfigGraphId: json['object_config_graph_id'] as String,
  materialization: json['materialization'] == null
      ? null
      : InterfaceWorkspaceMaterializationStateRef.fromJson(
          json['materialization'] as Map<String, dynamic>,
        ),
  materializeInvocationId: json['materialize_invocation_id'] as String,
  materializeReceiptPath: json['materialize_receipt_path'] as String,
  laneBranchId: json['lane_branch_id'] as String,
  objectConfigGraph: json['object_config_graph'] as Map<String, dynamic>,
);

Map<String, dynamic>
_$InterfaceWorkspaceSemanticObjectConfigGraphPreviewStateToJson(
  _InterfaceWorkspaceSemanticObjectConfigGraphPreviewState instance,
) => <String, dynamic>{
  'package_kind': instance.packageKind,
  'package_name': instance.packageName,
  'manifest_path': instance.manifestPath,
  'object_config_graph_id': instance.objectConfigGraphId,
  'materialization': instance.materialization?.toJson(),
  'materialize_invocation_id': instance.materializeInvocationId,
  'materialize_receipt_path': instance.materializeReceiptPath,
  'lane_branch_id': instance.laneBranchId,
  'object_config_graph': instance.objectConfigGraph,
};

_InterfaceWorkspaceSemanticSourceState
_$InterfaceWorkspaceSemanticSourceStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceWorkspaceSemanticSourceState(
  sourceMode: json['source_mode'] as String,
  summary: json['summary'] as String?,
  error: json['error'] as String?,
  materialization: json['materialization'] == null
      ? null
      : InterfaceWorkspaceMaterializationStateRef.fromJson(
          json['materialization'] as Map<String, dynamic>,
        ),
  materializeInvocationId: json['materialize_invocation_id'] as String?,
  materializeReceiptPath: json['materialize_receipt_path'] as String?,
  semanticPackages:
      (json['semantic_packages'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceWorkspaceSemanticPackageState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  committedSemanticPackages:
      (json['committed_semantic_packages'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceWorkspaceCommittedSemanticPackageState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  committedSemanticPackageFamilies:
      (json['committed_semantic_package_families'] as List<dynamic>?)
          ?.map(
            (e) =>
                InterfaceWorkspaceCommittedSemanticPackageFamilyState.fromJson(
                  e as Map<String, dynamic>,
                ),
          )
          .toList() ??
      const [],
  previewGraph: json['preview_graph'] == null
      ? null
      : InterfaceWorkspaceSemanticObjectConfigGraphPreviewState.fromJson(
          json['preview_graph'] as Map<String, dynamic>,
        ),
);

Map<String, dynamic> _$InterfaceWorkspaceSemanticSourceStateToJson(
  _InterfaceWorkspaceSemanticSourceState instance,
) => <String, dynamic>{
  'source_mode': instance.sourceMode,
  'summary': instance.summary,
  'error': instance.error,
  'materialization': instance.materialization?.toJson(),
  'materialize_invocation_id': instance.materializeInvocationId,
  'materialize_receipt_path': instance.materializeReceiptPath,
  'semantic_packages': instance.semanticPackages
      .map((e) => e.toJson())
      .toList(),
  'committed_semantic_packages': instance.committedSemanticPackages
      .map((e) => e.toJson())
      .toList(),
  'committed_semantic_package_families': instance
      .committedSemanticPackageFamilies
      .map((e) => e.toJson())
      .toList(),
  'preview_graph': instance.previewGraph?.toJson(),
};

_InterfaceSelectedSemanticPackageState
_$InterfaceSelectedSemanticPackageStateFromJson(Map<String, dynamic> json) =>
    _InterfaceSelectedSemanticPackageState(
      package: InterfaceWorkspaceCommittedSemanticPackageState.fromJson(
        json['package'] as Map<String, dynamic>,
      ),
      previewStatus: json['preview_status'] as String,
      summary: json['summary'] as String?,
      error: json['error'] as String?,
      previewGraph: json['preview_graph'] == null
          ? null
          : InterfaceWorkspaceSemanticObjectConfigGraphPreviewState.fromJson(
              json['preview_graph'] as Map<String, dynamic>,
            ),
    );

Map<String, dynamic> _$InterfaceSelectedSemanticPackageStateToJson(
  _InterfaceSelectedSemanticPackageState instance,
) => <String, dynamic>{
  'package': instance.package.toJson(),
  'preview_status': instance.previewStatus,
  'summary': instance.summary,
  'error': instance.error,
  'preview_graph': instance.previewGraph?.toJson(),
};

_InterfaceOperationTargetState _$InterfaceOperationTargetStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceOperationTargetState(
  targetId: json['target_id'] as String,
  displayName: json['display_name'] as String,
  kind: json['kind'] as String?,
  endpoint: json['endpoint'] as String?,
  phase: json['phase'] as String,
  isActive: json['is_active'] as bool,
  isHealthy: json['is_healthy'] as bool,
  summary: json['summary'] as String?,
  error: json['error'] as String?,
  detailLines:
      (json['detail_lines'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
);

Map<String, dynamic> _$InterfaceOperationTargetStateToJson(
  _InterfaceOperationTargetState instance,
) => <String, dynamic>{
  'target_id': instance.targetId,
  'display_name': instance.displayName,
  'kind': instance.kind,
  'endpoint': instance.endpoint,
  'phase': instance.phase,
  'is_active': instance.isActive,
  'is_healthy': instance.isHealthy,
  'summary': instance.summary,
  'error': instance.error,
  'detail_lines': instance.detailLines,
};

_InterfaceOperationState _$InterfaceOperationStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceOperationState(
  operationKey: json['operation_key'] as String,
  title: json['title'] as String?,
  status: json['status'] as String,
  phase: json['phase'] as String?,
  currentTargetId: json['current_target_id'] as String?,
  currentTargetTitle: json['current_target_title'] as String?,
  summary: json['summary'] as String?,
  error: json['error'] as String?,
  running: json['running'] as bool,
  retryable: json['retryable'] as bool,
  updatedAt: json['updated_at'] as String?,
  recentActivity:
      (json['recent_activity'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  targetStatuses:
      (json['target_statuses'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceOperationTargetState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$InterfaceOperationStateToJson(
  _InterfaceOperationState instance,
) => <String, dynamic>{
  'operation_key': instance.operationKey,
  'title': instance.title,
  'status': instance.status,
  'phase': instance.phase,
  'current_target_id': instance.currentTargetId,
  'current_target_title': instance.currentTargetTitle,
  'summary': instance.summary,
  'error': instance.error,
  'running': instance.running,
  'retryable': instance.retryable,
  'updated_at': instance.updatedAt,
  'recent_activity': instance.recentActivity,
  'target_statuses': instance.targetStatuses.map((e) => e.toJson()).toList(),
};

_InterfaceControlPlaneTraceEntry _$InterfaceControlPlaneTraceEntryFromJson(
  Map<String, dynamic> json,
) => _InterfaceControlPlaneTraceEntry(
  stepId: json['step_id'] as String?,
  sourceKey: json['source_key'] as String,
  sourceLabel: json['source_label'] as String,
  message: json['message'] as String,
  stepLabel: json['step_label'] as String?,
);

Map<String, dynamic> _$InterfaceControlPlaneTraceEntryToJson(
  _InterfaceControlPlaneTraceEntry instance,
) => <String, dynamic>{
  'step_id': instance.stepId,
  'source_key': instance.sourceKey,
  'source_label': instance.sourceLabel,
  'message': instance.message,
  'step_label': instance.stepLabel,
};

_InterfaceControlPlaneTraceGroup _$InterfaceControlPlaneTraceGroupFromJson(
  Map<String, dynamic> json,
) => _InterfaceControlPlaneTraceGroup(
  stepId: json['step_id'] as String,
  stepTitle: json['step_title'] as String,
  status: json['status'] as String,
  current: json['current'] as bool,
  selected: json['selected'] as bool,
  entries:
      (json['entries'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceControlPlaneTraceEntry.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$InterfaceControlPlaneTraceGroupToJson(
  _InterfaceControlPlaneTraceGroup instance,
) => <String, dynamic>{
  'step_id': instance.stepId,
  'step_title': instance.stepTitle,
  'status': instance.status,
  'current': instance.current,
  'selected': instance.selected,
  'entries': instance.entries.map((e) => e.toJson()).toList(),
};

_InterfaceControlPlaneOrchestrationStep
_$InterfaceControlPlaneOrchestrationStepFromJson(Map<String, dynamic> json) =>
    _InterfaceControlPlaneOrchestrationStep(
      stepId: json['step_id'] as String,
      title: json['title'] as String,
      kind: json['kind'] as String?,
      status: json['status'] as String,
      phase: json['phase'] as String?,
      summary: json['summary'] as String?,
      current: json['current'] as bool,
      selected: json['selected'] as bool,
      tracePreview:
          (json['trace_preview'] as List<dynamic>?)
              ?.map(
                (e) => InterfaceControlPlaneTraceEntry.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
    );

Map<String, dynamic> _$InterfaceControlPlaneOrchestrationStepToJson(
  _InterfaceControlPlaneOrchestrationStep instance,
) => <String, dynamic>{
  'step_id': instance.stepId,
  'title': instance.title,
  'kind': instance.kind,
  'status': instance.status,
  'phase': instance.phase,
  'summary': instance.summary,
  'current': instance.current,
  'selected': instance.selected,
  'trace_preview': instance.tracePreview.map((e) => e.toJson()).toList(),
};

_InterfaceControlPlaneWorkspaceState
_$InterfaceControlPlaneWorkspaceStateFromJson(Map<String, dynamic> json) =>
    _InterfaceControlPlaneWorkspaceState(
      selectedStepId: json['selected_step_id'] as String?,
      currentStepId: json['current_step_id'] as String?,
      orchestrationSteps:
          (json['orchestration_steps'] as List<dynamic>?)
              ?.map(
                (e) => InterfaceControlPlaneOrchestrationStep.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
      groupedTracePreview:
          (json['grouped_trace_preview'] as List<dynamic>?)
              ?.map(
                (e) => InterfaceControlPlaneTraceGroup.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
    );

Map<String, dynamic> _$InterfaceControlPlaneWorkspaceStateToJson(
  _InterfaceControlPlaneWorkspaceState instance,
) => <String, dynamic>{
  'selected_step_id': instance.selectedStepId,
  'current_step_id': instance.currentStepId,
  'orchestration_steps': instance.orchestrationSteps
      .map((e) => e.toJson())
      .toList(),
  'grouped_trace_preview': instance.groupedTracePreview
      .map((e) => e.toJson())
      .toList(),
};

_InterfaceControlPlaneProfileState _$InterfaceControlPlaneProfileStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceControlPlaneProfileState(
  profileId: json['profile_id'] as String,
  title: json['title'] as String,
  kind: json['kind'] as String,
  summary: json['summary'] as String?,
  selected: json['selected'] as bool,
  gateKeys:
      (json['gate_keys'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  currentGateKey: json['current_gate_key'] as String?,
);

Map<String, dynamic> _$InterfaceControlPlaneProfileStateToJson(
  _InterfaceControlPlaneProfileState instance,
) => <String, dynamic>{
  'profile_id': instance.profileId,
  'title': instance.title,
  'kind': instance.kind,
  'summary': instance.summary,
  'selected': instance.selected,
  'gate_keys': instance.gateKeys,
  'current_gate_key': instance.currentGateKey,
};

_InterfaceControlPlaneProfilesState
_$InterfaceControlPlaneProfilesStateFromJson(Map<String, dynamic> json) =>
    _InterfaceControlPlaneProfilesState(
      activeProfileId: json['active_profile_id'] as String,
      profiles:
          (json['profiles'] as List<dynamic>?)
              ?.map(
                (e) => InterfaceControlPlaneProfileState.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
    );

Map<String, dynamic> _$InterfaceControlPlaneProfilesStateToJson(
  _InterfaceControlPlaneProfilesState instance,
) => <String, dynamic>{
  'active_profile_id': instance.activeProfileId,
  'profiles': instance.profiles.map((e) => e.toJson()).toList(),
};

_InterfaceGateStep _$InterfaceGateStepFromJson(Map<String, dynamic> json) =>
    _InterfaceGateStep(
      key: json['key'] as String,
      status: json['status'] as String,
      title: json['title'] as String?,
      description: json['description'] as String?,
    );

Map<String, dynamic> _$InterfaceGateStepToJson(_InterfaceGateStep instance) =>
    <String, dynamic>{
      'key': instance.key,
      'status': instance.status,
      'title': instance.title,
      'description': instance.description,
    };

_InterfaceGateState _$InterfaceGateStateFromJson(Map<String, dynamic> json) =>
    _InterfaceGateState(
      destinationKey: json['destination_key'] as String?,
      activeStepKey: json['active_step_key'] as String?,
      blocked: json['blocked'] as bool,
      steps:
          (json['steps'] as List<dynamic>?)
              ?.map(
                (e) => InterfaceGateStep.fromJson(e as Map<String, dynamic>),
              )
              .toList() ??
          const [],
      reason: json['reason'] as String?,
    );

Map<String, dynamic> _$InterfaceGateStateToJson(_InterfaceGateState instance) =>
    <String, dynamic>{
      'destination_key': instance.destinationKey,
      'active_step_key': instance.activeStepKey,
      'blocked': instance.blocked,
      'steps': instance.steps.map((e) => e.toJson()).toList(),
      'reason': instance.reason,
    };

_InterfaceResolvedView _$InterfaceResolvedViewFromJson(
  Map<String, dynamic> json,
) => _InterfaceResolvedView(
  experienceKey: json['experience_key'] as String,
  interfacePackageId: _$JsonConverterFromJson<String, UuidValue>(
    json['interface_package_id'],
    const UuidValueConverter().fromJson,
  ),
  interfacePackageName: json['interface_package_name'] as String?,
  projectionViewId: json['projection_view_id'] as String?,
  hostPayload: json['host_payload'] as Map<String, dynamic>,
);

Map<String, dynamic> _$InterfaceResolvedViewToJson(
  _InterfaceResolvedView instance,
) => <String, dynamic>{
  'experience_key': instance.experienceKey,
  'interface_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.interfacePackageId,
    const UuidValueConverter().toJson,
  ),
  'interface_package_name': instance.interfacePackageName,
  'projection_view_id': instance.projectionViewId,
  'host_payload': instance.hostPayload,
};

_InterfaceRuntimeLayoutState _$InterfaceRuntimeLayoutStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceRuntimeLayoutState(
  layoutConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['layout_config_id'],
    const UuidValueConverter().fromJson,
  ),
  layoutKey: json['layout_key'] as String,
  label: json['label'] as String,
  isDefault: json['is_default'] as bool,
  isActive: json['is_active'] as bool,
);

Map<String, dynamic> _$InterfaceRuntimeLayoutStateToJson(
  _InterfaceRuntimeLayoutState instance,
) => <String, dynamic>{
  'layout_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutConfigId,
    const UuidValueConverter().toJson,
  ),
  'layout_key': instance.layoutKey,
  'label': instance.label,
  'is_default': instance.isDefault,
  'is_active': instance.isActive,
};

_InterfaceAttentionFocusTargetState
_$InterfaceAttentionFocusTargetStateFromJson(Map<String, dynamic> json) =>
    _InterfaceAttentionFocusTargetState(
      kind: json['kind'] as String,
      focusId: _$JsonConverterFromJson<String, UuidValue>(
        json['focus_id'],
        const UuidValueConverter().fromJson,
      ),
      focusScopeId: _$JsonConverterFromJson<String, UuidValue>(
        json['focus_scope_id'],
        const UuidValueConverter().fromJson,
      ),
      projectionExperienceGraphIdentityId:
          _$JsonConverterFromJson<String, UuidValue>(
            json['projection_experience_graph_identity_id'],
            const UuidValueConverter().fromJson,
          ),
      objectProjectionGraphIdentityId: const UuidValueConverter().fromJson(
        json['object_projection_graph_identity_id'] as String,
      ),
      objectInstanceGraphBranchId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_instance_graph_branch_id'],
        const UuidValueConverter().fromJson,
      ),
      projectionHash: json['projection_hash'] as String?,
      targetType: json['target_type'] as String?,
      targetId: _$JsonConverterFromJson<String, UuidValue>(
        json['target_id'],
        const UuidValueConverter().fromJson,
      ),
      description: json['description'] as String?,
    );

Map<String, dynamic> _$InterfaceAttentionFocusTargetStateToJson(
  _InterfaceAttentionFocusTargetState instance,
) => <String, dynamic>{
  'kind': instance.kind,
  'focus_id': _$JsonConverterToJson<String, UuidValue>(
    instance.focusId,
    const UuidValueConverter().toJson,
  ),
  'focus_scope_id': _$JsonConverterToJson<String, UuidValue>(
    instance.focusScopeId,
    const UuidValueConverter().toJson,
  ),
  'projection_experience_graph_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.projectionExperienceGraphIdentityId,
        const UuidValueConverter().toJson,
      ),
  'object_projection_graph_identity_id': const UuidValueConverter().toJson(
    instance.objectProjectionGraphIdentityId,
  ),
  'object_instance_graph_branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphBranchId,
    const UuidValueConverter().toJson,
  ),
  'projection_hash': instance.projectionHash,
  'target_type': instance.targetType,
  'target_id': _$JsonConverterToJson<String, UuidValue>(
    instance.targetId,
    const UuidValueConverter().toJson,
  ),
  'description': instance.description,
};

_InterfaceRuntimeFocusState _$InterfaceRuntimeFocusStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceRuntimeFocusState(
  layoutConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['layout_config_id'],
    const UuidValueConverter().fromJson,
  ),
  layoutKey: json['layout_key'] as String?,
  sectionKey: json['section_key'] as String?,
  layoutConfigSectionConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['layout_config_section_config_id'],
    const UuidValueConverter().fromJson,
  ),
  layoutSectionId: _$JsonConverterFromJson<String, UuidValue>(
    json['layout_section_id'],
    const UuidValueConverter().fromJson,
  ),
  sectionFocusScopeId: _$JsonConverterFromJson<String, UuidValue>(
    json['section_focus_scope_id'],
    const UuidValueConverter().fromJson,
  ),
  focusScopeId: _$JsonConverterFromJson<String, UuidValue>(
    json['focus_scope_id'],
    const UuidValueConverter().fromJson,
  ),
  focusId: _$JsonConverterFromJson<String, UuidValue>(
    json['focus_id'],
    const UuidValueConverter().fromJson,
  ),
  observableId: _$JsonConverterFromJson<String, UuidValue>(
    json['observable_id'],
    const UuidValueConverter().fromJson,
  ),
  focusTarget: json['focus_target'] == null
      ? null
      : InterfaceAttentionFocusTargetState.fromJson(
          json['focus_target'] as Map<String, dynamic>,
        ),
);

Map<String, dynamic> _$InterfaceRuntimeFocusStateToJson(
  _InterfaceRuntimeFocusState instance,
) => <String, dynamic>{
  'layout_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutConfigId,
    const UuidValueConverter().toJson,
  ),
  'layout_key': instance.layoutKey,
  'section_key': instance.sectionKey,
  'layout_config_section_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutConfigSectionConfigId,
    const UuidValueConverter().toJson,
  ),
  'layout_section_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutSectionId,
    const UuidValueConverter().toJson,
  ),
  'section_focus_scope_id': _$JsonConverterToJson<String, UuidValue>(
    instance.sectionFocusScopeId,
    const UuidValueConverter().toJson,
  ),
  'focus_scope_id': _$JsonConverterToJson<String, UuidValue>(
    instance.focusScopeId,
    const UuidValueConverter().toJson,
  ),
  'focus_id': _$JsonConverterToJson<String, UuidValue>(
    instance.focusId,
    const UuidValueConverter().toJson,
  ),
  'observable_id': _$JsonConverterToJson<String, UuidValue>(
    instance.observableId,
    const UuidValueConverter().toJson,
  ),
  'focus_target': instance.focusTarget?.toJson(),
};

_InterfaceRuntimeSectionRepresentationState
_$InterfaceRuntimeSectionRepresentationStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceRuntimeSectionRepresentationState(
  representationId: const UuidValueConverter().fromJson(
    json['representation_id'] as String,
  ),
  windowKey: json['window_key'] as String,
  layoutConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['layout_config_id'],
    const UuidValueConverter().fromJson,
  ),
  layoutKey: json['layout_key'] as String,
  sectionKey: json['section_key'] as String,
  layoutConfigSectionConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['layout_config_section_config_id'],
    const UuidValueConverter().fromJson,
  ),
  paneName: json['pane_name'] as String,
  paneKind: json['pane_kind'] as String,
  label: json['label'] as String,
  observableId: const UuidValueConverter().fromJson(
    json['observable_id'] as String,
  ),
  projectionExperienceGraphIdentityId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['projection_experience_graph_identity_id'],
        const UuidValueConverter().fromJson,
      ),
  objectProjectionGraphIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_projection_graph_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  sectionGraphBindingKey: json['section_graph_binding_key'] as String?,
  viewRef: json['view_ref'] as String,
  projectionViewKey: json['projection_view_key'] as String?,
  isActive: json['is_active'] as bool,
);

Map<String, dynamic> _$InterfaceRuntimeSectionRepresentationStateToJson(
  _InterfaceRuntimeSectionRepresentationState instance,
) => <String, dynamic>{
  'representation_id': const UuidValueConverter().toJson(
    instance.representationId,
  ),
  'window_key': instance.windowKey,
  'layout_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutConfigId,
    const UuidValueConverter().toJson,
  ),
  'layout_key': instance.layoutKey,
  'section_key': instance.sectionKey,
  'layout_config_section_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutConfigSectionConfigId,
    const UuidValueConverter().toJson,
  ),
  'pane_name': instance.paneName,
  'pane_kind': instance.paneKind,
  'label': instance.label,
  'observable_id': const UuidValueConverter().toJson(instance.observableId),
  'projection_experience_graph_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.projectionExperienceGraphIdentityId,
        const UuidValueConverter().toJson,
      ),
  'object_projection_graph_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.objectProjectionGraphIdentityId,
        const UuidValueConverter().toJson,
      ),
  'section_graph_binding_key': instance.sectionGraphBindingKey,
  'view_ref': instance.viewRef,
  'projection_view_key': instance.projectionViewKey,
  'is_active': instance.isActive,
};

_InterfaceResolvedPaneDescriptor _$InterfaceResolvedPaneDescriptorFromJson(
  Map<String, dynamic> json,
) => _InterfaceResolvedPaneDescriptor(
  windowKey: json['window_key'] as String,
  layoutKey: json['layout_key'] as String,
  sectionKey: json['section_key'] as String,
  layoutConfigSectionConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['layout_config_section_config_id'],
    const UuidValueConverter().fromJson,
  ),
  layoutSectionId: _$JsonConverterFromJson<String, UuidValue>(
    json['layout_section_id'],
    const UuidValueConverter().fromJson,
  ),
  sectionFocusScopeId: _$JsonConverterFromJson<String, UuidValue>(
    json['section_focus_scope_id'],
    const UuidValueConverter().fromJson,
  ),
  focusScopeId: _$JsonConverterFromJson<String, UuidValue>(
    json['focus_scope_id'],
    const UuidValueConverter().fromJson,
  ),
  focusId: _$JsonConverterFromJson<String, UuidValue>(
    json['focus_id'],
    const UuidValueConverter().fromJson,
  ),
  branchId: _$JsonConverterFromJson<String, UuidValue>(
    json['branch_id'],
    const UuidValueConverter().fromJson,
  ),
  focusTarget: json['focus_target'] == null
      ? null
      : InterfaceAttentionFocusTargetState.fromJson(
          json['focus_target'] as Map<String, dynamic>,
        ),
  paneKind: json['pane_kind'] as String,
  paneConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['pane_config_id'],
    const UuidValueConverter().fromJson,
  ),
  panePackageId: _$JsonConverterFromJson<String, UuidValue>(
    json['pane_package_id'],
    const UuidValueConverter().fromJson,
  ),
  panePackageName: json['pane_package_name'] as String?,
  objectProjectionGraphObservableId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_projection_graph_observable_id'],
    const UuidValueConverter().fromJson,
  ),
  projectionExperienceGraphIdentityId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['projection_experience_graph_identity_id'],
        const UuidValueConverter().fromJson,
      ),
  objectProjectionGraphIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_projection_graph_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  sectionGraphBindingKey: json['section_graph_binding_key'] as String?,
  projectionExperienceViewId: _$JsonConverterFromJson<String, UuidValue>(
    json['projection_experience_view_id'],
    const UuidValueConverter().fromJson,
  ),
  projectionViewId: json['projection_view_id'] as String?,
  viewRef: json['view_ref'] as String?,
  projectionViewKey: json['projection_view_key'] as String?,
  stateModelId: _$JsonConverterFromJson<String, UuidValue>(
    json['state_model_id'],
    const UuidValueConverter().fromJson,
  ),
  title: json['title'] as String?,
  summary: json['summary'] as String?,
  narrativeKey: json['narrative_key'] as String?,
  stateSourceKind: json['state_source_kind'] as String,
  stateProjectionHash: json['state_projection_hash'] as String?,
  actionKeys:
      (json['action_keys'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
);

Map<String, dynamic> _$InterfaceResolvedPaneDescriptorToJson(
  _InterfaceResolvedPaneDescriptor instance,
) => <String, dynamic>{
  'window_key': instance.windowKey,
  'layout_key': instance.layoutKey,
  'section_key': instance.sectionKey,
  'layout_config_section_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutConfigSectionConfigId,
    const UuidValueConverter().toJson,
  ),
  'layout_section_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutSectionId,
    const UuidValueConverter().toJson,
  ),
  'section_focus_scope_id': _$JsonConverterToJson<String, UuidValue>(
    instance.sectionFocusScopeId,
    const UuidValueConverter().toJson,
  ),
  'focus_scope_id': _$JsonConverterToJson<String, UuidValue>(
    instance.focusScopeId,
    const UuidValueConverter().toJson,
  ),
  'focus_id': _$JsonConverterToJson<String, UuidValue>(
    instance.focusId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.branchId,
    const UuidValueConverter().toJson,
  ),
  'focus_target': instance.focusTarget?.toJson(),
  'pane_kind': instance.paneKind,
  'pane_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.paneConfigId,
    const UuidValueConverter().toJson,
  ),
  'pane_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.panePackageId,
    const UuidValueConverter().toJson,
  ),
  'pane_package_name': instance.panePackageName,
  'object_projection_graph_observable_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.objectProjectionGraphObservableId,
        const UuidValueConverter().toJson,
      ),
  'projection_experience_graph_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.projectionExperienceGraphIdentityId,
        const UuidValueConverter().toJson,
      ),
  'object_projection_graph_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.objectProjectionGraphIdentityId,
        const UuidValueConverter().toJson,
      ),
  'section_graph_binding_key': instance.sectionGraphBindingKey,
  'projection_experience_view_id': _$JsonConverterToJson<String, UuidValue>(
    instance.projectionExperienceViewId,
    const UuidValueConverter().toJson,
  ),
  'projection_view_id': instance.projectionViewId,
  'view_ref': instance.viewRef,
  'projection_view_key': instance.projectionViewKey,
  'state_model_id': _$JsonConverterToJson<String, UuidValue>(
    instance.stateModelId,
    const UuidValueConverter().toJson,
  ),
  'title': instance.title,
  'summary': instance.summary,
  'narrative_key': instance.narrativeKey,
  'state_source_kind': instance.stateSourceKind,
  'state_projection_hash': instance.stateProjectionHash,
  'action_keys': instance.actionKeys,
};

_InterfaceMaterializedPaneState _$InterfaceMaterializedPaneStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceMaterializedPaneState(
  paneStateKey: json['pane_state_key'] as String,
  windowKey: json['window_key'] as String,
  layoutKey: json['layout_key'] as String,
  sectionKey: json['section_key'] as String,
  paneKind: json['pane_kind'] as String,
  paneConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['pane_config_id'],
    const UuidValueConverter().fromJson,
  ),
  panePackageId: _$JsonConverterFromJson<String, UuidValue>(
    json['pane_package_id'],
    const UuidValueConverter().fromJson,
  ),
  focusScopeId: _$JsonConverterFromJson<String, UuidValue>(
    json['focus_scope_id'],
    const UuidValueConverter().fromJson,
  ),
  branchId: _$JsonConverterFromJson<String, UuidValue>(
    json['branch_id'],
    const UuidValueConverter().fromJson,
  ),
  projectionExperienceViewId: _$JsonConverterFromJson<String, UuidValue>(
    json['projection_experience_view_id'],
    const UuidValueConverter().fromJson,
  ),
  projectionViewId: json['projection_view_id'] as String?,
  stateModelId: _$JsonConverterFromJson<String, UuidValue>(
    json['state_model_id'],
    const UuidValueConverter().fromJson,
  ),
  projectionHash: json['projection_hash'] as String?,
  status: json['status'] as String,
  headCommitId: json['head_commit_id'] as String?,
  graphHashPost: json['graph_hash_post'] as String?,
  materializedAt: json['materialized_at'] as String?,
  state: json['state'] as Map<String, dynamic>,
  provenance: json['provenance'] as Map<String, dynamic>,
  error: json['error'] as String?,
);

Map<String, dynamic> _$InterfaceMaterializedPaneStateToJson(
  _InterfaceMaterializedPaneState instance,
) => <String, dynamic>{
  'pane_state_key': instance.paneStateKey,
  'window_key': instance.windowKey,
  'layout_key': instance.layoutKey,
  'section_key': instance.sectionKey,
  'pane_kind': instance.paneKind,
  'pane_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.paneConfigId,
    const UuidValueConverter().toJson,
  ),
  'pane_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.panePackageId,
    const UuidValueConverter().toJson,
  ),
  'focus_scope_id': _$JsonConverterToJson<String, UuidValue>(
    instance.focusScopeId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.branchId,
    const UuidValueConverter().toJson,
  ),
  'projection_experience_view_id': _$JsonConverterToJson<String, UuidValue>(
    instance.projectionExperienceViewId,
    const UuidValueConverter().toJson,
  ),
  'projection_view_id': instance.projectionViewId,
  'state_model_id': _$JsonConverterToJson<String, UuidValue>(
    instance.stateModelId,
    const UuidValueConverter().toJson,
  ),
  'projection_hash': instance.projectionHash,
  'status': instance.status,
  'head_commit_id': instance.headCommitId,
  'graph_hash_post': instance.graphHashPost,
  'materialized_at': instance.materializedAt,
  'state': instance.state,
  'provenance': instance.provenance,
  'error': instance.error,
};

_InterfaceRuntimePaneRenderSpecState
_$InterfaceRuntimePaneRenderSpecStateFromJson(Map<String, dynamic> json) =>
    _InterfaceRuntimePaneRenderSpecState(
      sourceKind: json['source_kind'] as String,
      branchId: _$JsonConverterFromJson<String, UuidValue>(
        json['branch_id'],
        const UuidValueConverter().fromJson,
      ),
      projectionHash: json['projection_hash'] as String?,
      lastCommitId: _$JsonConverterFromJson<String, UuidValue>(
        json['last_commit_id'],
        const UuidValueConverter().fromJson,
      ),
      objectInstanceGraphCommitId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_instance_graph_commit_id'],
        const UuidValueConverter().fromJson,
      ),
      paneRenderSpecId: const UuidValueConverter().fromJson(
        json['pane_render_spec_id'] as String,
      ),
      paneConfigId: const UuidValueConverter().fromJson(
        json['pane_config_id'] as String,
      ),
      renderSpecContentHashSha256:
          json['render_spec_content_hash_sha256'] as String?,
      payload: json['payload'] as Map<String, dynamic>,
    );

Map<String, dynamic> _$InterfaceRuntimePaneRenderSpecStateToJson(
  _InterfaceRuntimePaneRenderSpecState instance,
) => <String, dynamic>{
  'source_kind': instance.sourceKind,
  'branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.branchId,
    const UuidValueConverter().toJson,
  ),
  'projection_hash': instance.projectionHash,
  'last_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.lastCommitId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphCommitId,
    const UuidValueConverter().toJson,
  ),
  'pane_render_spec_id': const UuidValueConverter().toJson(
    instance.paneRenderSpecId,
  ),
  'pane_config_id': const UuidValueConverter().toJson(instance.paneConfigId),
  'render_spec_content_hash_sha256': instance.renderSpecContentHashSha256,
  'payload': instance.payload,
};

_InterfaceRuntimePackageApiPackageState
_$InterfaceRuntimePackageApiPackageStateFromJson(Map<String, dynamic> json) =>
    _InterfaceRuntimePackageApiPackageState(
      apiPackageId: _$JsonConverterFromJson<String, UuidValue>(
        json['api_package_id'],
        const UuidValueConverter().fromJson,
      ),
      apiPackageName: json['api_package_name'] as String,
    );

Map<String, dynamic> _$InterfaceRuntimePackageApiPackageStateToJson(
  _InterfaceRuntimePackageApiPackageState instance,
) => <String, dynamic>{
  'api_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.apiPackageId,
    const UuidValueConverter().toJson,
  ),
  'api_package_name': instance.apiPackageName,
};

_InterfaceRuntimePackageApiState _$InterfaceRuntimePackageApiStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceRuntimePackageApiState(
  interfaceName: json['interface_name'] as String?,
  interfaceConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['interface_config_id'],
    const UuidValueConverter().fromJson,
  ),
  interfaceConfigApiId: _$JsonConverterFromJson<String, UuidValue>(
    json['interface_config_api_id'],
    const UuidValueConverter().fromJson,
  ),
  apiId: _$JsonConverterFromJson<String, UuidValue>(
    json['api_id'],
    const UuidValueConverter().fromJson,
  ),
  apiRef: json['api_ref'] as String,
);

Map<String, dynamic> _$InterfaceRuntimePackageApiStateToJson(
  _InterfaceRuntimePackageApiState instance,
) => <String, dynamic>{
  'interface_name': instance.interfaceName,
  'interface_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.interfaceConfigId,
    const UuidValueConverter().toJson,
  ),
  'interface_config_api_id': _$JsonConverterToJson<String, UuidValue>(
    instance.interfaceConfigApiId,
    const UuidValueConverter().toJson,
  ),
  'api_id': _$JsonConverterToJson<String, UuidValue>(
    instance.apiId,
    const UuidValueConverter().toJson,
  ),
  'api_ref': instance.apiRef,
};

_InterfaceRuntimePackageRenderComponentState
_$InterfaceRuntimePackageRenderComponentStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceRuntimePackageRenderComponentState(
  componentRef: json['component_ref'] as String,
  displayName: json['display_name'] as String?,
);

Map<String, dynamic> _$InterfaceRuntimePackageRenderComponentStateToJson(
  _InterfaceRuntimePackageRenderComponentState instance,
) => <String, dynamic>{
  'component_ref': instance.componentRef,
  'display_name': instance.displayName,
};

_InterfaceRuntimePackageState _$InterfaceRuntimePackageStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceRuntimePackageState(
  sourceKind: json['source_kind'] as String,
  interfacePackageId: _$JsonConverterFromJson<String, UuidValue>(
    json['interface_package_id'],
    const UuidValueConverter().fromJson,
  ),
  interfacePackageName: json['interface_package_name'] as String,
  experienceKeys:
      (json['experience_keys'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  layouts:
      (json['layouts'] as List<dynamic>?)
          ?.map(
            (e) =>
                InterfaceRuntimeLayoutState.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  sectionRepresentations:
      (json['section_representations'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceRuntimeSectionRepresentationState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  apiPackages:
      (json['api_packages'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceRuntimePackageApiPackageState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  apis:
      (json['apis'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceRuntimePackageApiState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  dynamicPaneRenderSpecs:
      (json['dynamic_pane_render_specs'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceRuntimePaneRenderSpecState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  renderComponents:
      (json['render_components'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceRuntimePackageRenderComponentState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  warnings:
      (json['warnings'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
);

Map<String, dynamic> _$InterfaceRuntimePackageStateToJson(
  _InterfaceRuntimePackageState instance,
) => <String, dynamic>{
  'source_kind': instance.sourceKind,
  'interface_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.interfacePackageId,
    const UuidValueConverter().toJson,
  ),
  'interface_package_name': instance.interfacePackageName,
  'experience_keys': instance.experienceKeys,
  'layouts': instance.layouts.map((e) => e.toJson()).toList(),
  'section_representations': instance.sectionRepresentations
      .map((e) => e.toJson())
      .toList(),
  'api_packages': instance.apiPackages.map((e) => e.toJson()).toList(),
  'apis': instance.apis.map((e) => e.toJson()).toList(),
  'dynamic_pane_render_specs': instance.dynamicPaneRenderSpecs
      .map((e) => e.toJson())
      .toList(),
  'render_components': instance.renderComponents
      .map((e) => e.toJson())
      .toList(),
  'warnings': instance.warnings,
};

_InterfaceWindowLayoutSectionState _$InterfaceWindowLayoutSectionStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceWindowLayoutSectionState(
  sectionKey: json['section_key'] as String,
  layoutConfigSectionConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['layout_config_section_config_id'],
    const UuidValueConverter().fromJson,
  ),
  layoutSectionId: _$JsonConverterFromJson<String, UuidValue>(
    json['layout_section_id'],
    const UuidValueConverter().fromJson,
  ),
  attentionSessionSectionId: _$JsonConverterFromJson<String, UuidValue>(
    json['attention_session_section_id'],
    const UuidValueConverter().fromJson,
  ),
  title: json['title'] as String?,
  description: json['description'] as String?,
  order: (json['order'] as num).toInt(),
  flex: (json['flex'] as num).toDouble(),
  weightMicros: (json['weight_micros'] as num?)?.toInt(),
  isVisible: json['is_visible'] as bool,
  isCollapsed: json['is_collapsed'] as bool,
  projectionViewId: json['projection_view_id'] as String?,
  paneKey: json['pane_key'] as String?,
);

Map<String, dynamic> _$InterfaceWindowLayoutSectionStateToJson(
  _InterfaceWindowLayoutSectionState instance,
) => <String, dynamic>{
  'section_key': instance.sectionKey,
  'layout_config_section_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutConfigSectionConfigId,
    const UuidValueConverter().toJson,
  ),
  'layout_section_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutSectionId,
    const UuidValueConverter().toJson,
  ),
  'attention_session_section_id': _$JsonConverterToJson<String, UuidValue>(
    instance.attentionSessionSectionId,
    const UuidValueConverter().toJson,
  ),
  'title': instance.title,
  'description': instance.description,
  'order': instance.order,
  'flex': instance.flex,
  'weight_micros': instance.weightMicros,
  'is_visible': instance.isVisible,
  'is_collapsed': instance.isCollapsed,
  'projection_view_id': instance.projectionViewId,
  'pane_key': instance.paneKey,
};

_InterfaceWindowLayoutState _$InterfaceWindowLayoutStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceWindowLayoutState(
  sourceKind: json['source_kind'] as String,
  windowKey: json['window_key'] as String,
  layoutKey: json['layout_key'] as String,
  layoutConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['layout_config_id'],
    const UuidValueConverter().fromJson,
  ),
  attentionSessionId: _$JsonConverterFromJson<String, UuidValue>(
    json['attention_session_id'],
    const UuidValueConverter().fromJson,
  ),
  attentionSessionLayoutId: _$JsonConverterFromJson<String, UuidValue>(
    json['attention_session_layout_id'],
    const UuidValueConverter().fromJson,
  ),
  activeLayoutTransitionId: _$JsonConverterFromJson<String, UuidValue>(
    json['active_layout_transition_id'],
    const UuidValueConverter().fromJson,
  ),
  activeTopologyTransitionId: _$JsonConverterFromJson<String, UuidValue>(
    json['active_topology_transition_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  graphHashPost: json['graph_hash_post'] as String?,
  title: json['title'] as String?,
  description: json['description'] as String?,
  frameMode: json['frame_mode'] as String,
  versionHash: json['version_hash'] as String?,
  resolvedAt: json['resolved_at'] as String?,
  stale: json['stale'] as bool,
  admittedSections:
      (json['admitted_sections'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceWindowLayoutSectionState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  sections:
      (json['sections'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceWindowLayoutSectionState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$InterfaceWindowLayoutStateToJson(
  _InterfaceWindowLayoutState instance,
) => <String, dynamic>{
  'source_kind': instance.sourceKind,
  'window_key': instance.windowKey,
  'layout_key': instance.layoutKey,
  'layout_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutConfigId,
    const UuidValueConverter().toJson,
  ),
  'attention_session_id': _$JsonConverterToJson<String, UuidValue>(
    instance.attentionSessionId,
    const UuidValueConverter().toJson,
  ),
  'attention_session_layout_id': _$JsonConverterToJson<String, UuidValue>(
    instance.attentionSessionLayoutId,
    const UuidValueConverter().toJson,
  ),
  'active_layout_transition_id': _$JsonConverterToJson<String, UuidValue>(
    instance.activeLayoutTransitionId,
    const UuidValueConverter().toJson,
  ),
  'active_topology_transition_id': _$JsonConverterToJson<String, UuidValue>(
    instance.activeTopologyTransitionId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphCommitId,
    const UuidValueConverter().toJson,
  ),
  'graph_hash_post': instance.graphHashPost,
  'title': instance.title,
  'description': instance.description,
  'frame_mode': instance.frameMode,
  'version_hash': instance.versionHash,
  'resolved_at': instance.resolvedAt,
  'stale': instance.stale,
  'admitted_sections': instance.admittedSections
      .map((e) => e.toJson())
      .toList(),
  'sections': instance.sections.map((e) => e.toJson()).toList(),
};

_InterfaceRuntimeWindowNavigationContextState
_$InterfaceRuntimeWindowNavigationContextStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceRuntimeWindowNavigationContextState(
  sourceKind: json['source_kind'] as String,
  environmentNavigationContextId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_navigation_context_id'],
    const UuidValueConverter().fromJson,
  ),
  threadId: _$JsonConverterFromJson<String, UuidValue>(
    json['thread_id'],
    const UuidValueConverter().fromJson,
  ),
  interfaceWindowNavigationContextId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['interface_window_navigation_context_id'],
        const UuidValueConverter().fromJson,
      ),
  interfaceEnvironmentId: _$JsonConverterFromJson<String, UuidValue>(
    json['interface_environment_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_id'],
    const UuidValueConverter().fromJson,
  ),
  processId: _$JsonConverterFromJson<String, UuidValue>(
    json['process_id'],
    const UuidValueConverter().fromJson,
  ),
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$InterfaceRuntimeWindowNavigationContextStateToJson(
  _InterfaceRuntimeWindowNavigationContextState instance,
) => <String, dynamic>{
  'source_kind': instance.sourceKind,
  'environment_navigation_context_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentNavigationContextId,
    const UuidValueConverter().toJson,
  ),
  'thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadId,
    const UuidValueConverter().toJson,
  ),
  'interface_window_navigation_context_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.interfaceWindowNavigationContextId,
        const UuidValueConverter().toJson,
      ),
  'interface_environment_id': _$JsonConverterToJson<String, UuidValue>(
    instance.interfaceEnvironmentId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentId,
    const UuidValueConverter().toJson,
  ),
  'process_id': _$JsonConverterToJson<String, UuidValue>(
    instance.processId,
    const UuidValueConverter().toJson,
  ),
  'evidence': instance.evidence,
};

_InterfaceRuntimeWindowState _$InterfaceRuntimeWindowStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceRuntimeWindowState(
  sourceKind: json['source_kind'] as String,
  windowKey: json['window_key'] as String,
  active: json['active'] as bool,
  interfaceId: _$JsonConverterFromJson<String, UuidValue>(
    json['interface_id'],
    const UuidValueConverter().fromJson,
  ),
  interfaceWindowId: _$JsonConverterFromJson<String, UuidValue>(
    json['interface_window_id'],
    const UuidValueConverter().fromJson,
  ),
  windowId: _$JsonConverterFromJson<String, UuidValue>(
    json['window_id'],
    const UuidValueConverter().fromJson,
  ),
  title: json['title'] as String?,
  activeNavigationContext: json['active_navigation_context'] == null
      ? null
      : InterfaceRuntimeWindowNavigationContextState.fromJson(
          json['active_navigation_context'] as Map<String, dynamic>,
        ),
  activeLayoutId: _$JsonConverterFromJson<String, UuidValue>(
    json['active_layout_id'],
    const UuidValueConverter().fromJson,
  ),
  activeLayoutConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['active_layout_config_id'],
    const UuidValueConverter().fromJson,
  ),
  activeLayoutKey: json['active_layout_key'] as String?,
  activeLayoutSourceKind: json['active_layout_source_kind'] as String?,
  interfaceProjectionHash: json['interface_projection_hash'] as String?,
  windowProjectionHash: json['window_projection_hash'] as String?,
  interfaceHeadCommitId: json['interface_head_commit_id'] as String?,
  windowHeadCommitId: json['window_head_commit_id'] as String?,
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$InterfaceRuntimeWindowStateToJson(
  _InterfaceRuntimeWindowState instance,
) => <String, dynamic>{
  'source_kind': instance.sourceKind,
  'window_key': instance.windowKey,
  'active': instance.active,
  'interface_id': _$JsonConverterToJson<String, UuidValue>(
    instance.interfaceId,
    const UuidValueConverter().toJson,
  ),
  'interface_window_id': _$JsonConverterToJson<String, UuidValue>(
    instance.interfaceWindowId,
    const UuidValueConverter().toJson,
  ),
  'window_id': _$JsonConverterToJson<String, UuidValue>(
    instance.windowId,
    const UuidValueConverter().toJson,
  ),
  'title': instance.title,
  'active_navigation_context': instance.activeNavigationContext?.toJson(),
  'active_layout_id': _$JsonConverterToJson<String, UuidValue>(
    instance.activeLayoutId,
    const UuidValueConverter().toJson,
  ),
  'active_layout_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.activeLayoutConfigId,
    const UuidValueConverter().toJson,
  ),
  'active_layout_key': instance.activeLayoutKey,
  'active_layout_source_kind': instance.activeLayoutSourceKind,
  'interface_projection_hash': instance.interfaceProjectionHash,
  'window_projection_hash': instance.windowProjectionHash,
  'interface_head_commit_id': instance.interfaceHeadCommitId,
  'window_head_commit_id': instance.windowHeadCommitId,
  'evidence': instance.evidence,
};

_InterfaceRuntimeState _$InterfaceRuntimeStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceRuntimeState(
  backend: InterfaceBackendState.fromJson(
    json['backend'] as Map<String, dynamic>,
  ),
  gateState: json['gate_state'] == null
      ? null
      : InterfaceGateState.fromJson(json['gate_state'] as Map<String, dynamic>),
  resolvedView: json['resolved_view'] == null
      ? null
      : InterfaceResolvedView.fromJson(
          json['resolved_view'] as Map<String, dynamic>,
        ),
  windowLayout: json['window_layout'] == null
      ? null
      : InterfaceWindowLayoutState.fromJson(
          json['window_layout'] as Map<String, dynamic>,
        ),
  activeWindow: json['active_window'] == null
      ? null
      : InterfaceRuntimeWindowState.fromJson(
          json['active_window'] as Map<String, dynamic>,
        ),
  windows:
      (json['windows'] as List<dynamic>?)
          ?.map(
            (e) =>
                InterfaceRuntimeWindowState.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  activeLayoutConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['active_layout_config_id'],
    const UuidValueConverter().fromJson,
  ),
  layoutStates:
      (json['layout_states'] as List<dynamic>?)
          ?.map(
            (e) =>
                InterfaceRuntimeLayoutState.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  activeFocus: json['active_focus'] == null
      ? null
      : InterfaceRuntimeFocusState.fromJson(
          json['active_focus'] as Map<String, dynamic>,
        ),
  interfacePackageRuntime: json['interface_package_runtime'] == null
      ? null
      : InterfaceRuntimePackageState.fromJson(
          json['interface_package_runtime'] as Map<String, dynamic>,
        ),
  sectionRepresentations:
      (json['section_representations'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceRuntimeSectionRepresentationState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  resolvedPanes:
      (json['resolved_panes'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceResolvedPaneDescriptor.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  viewStateCursor: json['view_state_cursor'] == null
      ? null
      : InterfaceHostViewStateCursorState.fromJson(
          json['view_state_cursor'] as Map<String, dynamic>,
        ),
  materializedPaneStates:
      (json['materialized_pane_states'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceMaterializedPaneState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  dynamicPaneRenderSpecs:
      (json['dynamic_pane_render_specs'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceRuntimePaneRenderSpecState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  warnings:
      (json['warnings'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
);

Map<String, dynamic> _$InterfaceRuntimeStateToJson(
  _InterfaceRuntimeState instance,
) => <String, dynamic>{
  'backend': instance.backend.toJson(),
  'gate_state': instance.gateState?.toJson(),
  'resolved_view': instance.resolvedView?.toJson(),
  'window_layout': instance.windowLayout?.toJson(),
  'active_window': instance.activeWindow?.toJson(),
  'windows': instance.windows.map((e) => e.toJson()).toList(),
  'active_layout_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.activeLayoutConfigId,
    const UuidValueConverter().toJson,
  ),
  'layout_states': instance.layoutStates.map((e) => e.toJson()).toList(),
  'active_focus': instance.activeFocus?.toJson(),
  'interface_package_runtime': instance.interfacePackageRuntime?.toJson(),
  'section_representations': instance.sectionRepresentations
      .map((e) => e.toJson())
      .toList(),
  'resolved_panes': instance.resolvedPanes.map((e) => e.toJson()).toList(),
  'view_state_cursor': instance.viewStateCursor?.toJson(),
  'materialized_pane_states': instance.materializedPaneStates
      .map((e) => e.toJson())
      .toList(),
  'dynamic_pane_render_specs': instance.dynamicPaneRenderSpecs
      .map((e) => e.toJson())
      .toList(),
  'warnings': instance.warnings,
};

_InterfaceHostState _$InterfaceHostStateFromJson(
  Map<String, dynamic> json,
) => _InterfaceHostState(
  hostLabel: json['host_label'] as String,
  namespace: json['namespace'] as String,
  endpoint: json['endpoint'] as String?,
  environmentId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_config_id'],
    const UuidValueConverter().fromJson,
  ),
  started: json['started'] as bool,
  transport: InterfaceTransportState.fromJson(
    json['transport'] as Map<String, dynamic>,
  ),
  rendererCapabilities: json['renderer_capabilities'] == null
      ? null
      : InterfaceRendererCapabilitiesState.fromJson(
          json['renderer_capabilities'] as Map<String, dynamic>,
        ),
  localServiceHost: json['local_service_host'] == null
      ? null
      : InterfaceLocalServiceHostState.fromJson(
          json['local_service_host'] as Map<String, dynamic>,
        ),
  localNodeRuntime: json['local_node_runtime'] == null
      ? null
      : InterfaceLocalNodeRuntimeState.fromJson(
          json['local_node_runtime'] as Map<String, dynamic>,
        ),
  hostedServices: json['hosted_services'] == null
      ? null
      : InterfaceHostedServicesState.fromJson(
          json['hosted_services'] as Map<String, dynamic>,
        ),
  laneSync: json['lane_sync'] == null
      ? null
      : InterfaceLaneSyncState.fromJson(
          json['lane_sync'] as Map<String, dynamic>,
        ),
  environmentAdmission: json['environment_admission'] == null
      ? null
      : InterfaceEnvironmentAdmissionState.fromJson(
          json['environment_admission'] as Map<String, dynamic>,
        ),
  environmentSession: json['environment_session'] == null
      ? null
      : InterfaceEnvironmentSessionState.fromJson(
          json['environment_session'] as Map<String, dynamic>,
        ),
  environmentNavigation: json['environment_navigation'] == null
      ? null
      : InterfaceEnvironmentNavigationState.fromJson(
          json['environment_navigation'] as Map<String, dynamic>,
        ),
  environmentAdmissionReceipt: json['environment_admission_receipt'] == null
      ? null
      : EnvironmentActorAdmissionReceipt.fromJson(
          json['environment_admission_receipt'] as Map<String, dynamic>,
        ),
  environmentSessionJoinReceipt:
      json['environment_session_join_receipt'] == null
      ? null
      : EnvironmentSessionJoinReceipt.fromJson(
          json['environment_session_join_receipt'] as Map<String, dynamic>,
        ),
  experienceLens: json['experience_lens'] == null
      ? null
      : InterfaceExperienceLensState.fromJson(
          json['experience_lens'] as Map<String, dynamic>,
        ),
  appScreen: json['app_screen'] == null
      ? null
      : InterfaceAppScreenState.fromJson(
          json['app_screen'] as Map<String, dynamic>,
        ),
  experienceSessionNarration: json['experience_session_narration'] == null
      ? null
      : InterfaceExperienceSessionNarrationState.fromJson(
          json['experience_session_narration'] as Map<String, dynamic>,
        ),
  runtime: json['runtime'] == null
      ? null
      : InterfaceRuntimeState.fromJson(json['runtime'] as Map<String, dynamic>),
  controlPlaneProfiles: json['control_plane_profiles'] == null
      ? null
      : InterfaceControlPlaneProfilesState.fromJson(
          json['control_plane_profiles'] as Map<String, dynamic>,
        ),
  controlPlaneWorkspace: json['control_plane_workspace'] == null
      ? null
      : InterfaceControlPlaneWorkspaceState.fromJson(
          json['control_plane_workspace'] as Map<String, dynamic>,
        ),
  workspaceDiscovery: json['workspace_discovery'] == null
      ? null
      : InterfaceWorkspaceDiscoveryState.fromJson(
          json['workspace_discovery'] as Map<String, dynamic>,
        ),
  selectedWorkspace: json['selected_workspace'] == null
      ? null
      : InterfaceSelectedWorkspaceState.fromJson(
          json['selected_workspace'] as Map<String, dynamic>,
        ),
  selectedSemanticPackage: json['selected_semantic_package'] == null
      ? null
      : InterfaceSelectedSemanticPackageState.fromJson(
          json['selected_semantic_package'] as Map<String, dynamic>,
        ),
  currentScreen: json['current_screen'] == null
      ? null
      : InterfaceCurrentScreen.fromJson(
          json['current_screen'] as Map<String, dynamic>,
        ),
  currentOperation: json['current_operation'] == null
      ? null
      : InterfaceOperationState.fromJson(
          json['current_operation'] as Map<String, dynamic>,
        ),
  allowedActions:
      (json['allowed_actions'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceAllowedAction.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  recoveryCapabilities:
      (json['recovery_capabilities'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceHostRecoveryCapabilityState.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  warnings:
      (json['warnings'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
);

Map<String, dynamic> _$InterfaceHostStateToJson(
  _InterfaceHostState instance,
) => <String, dynamic>{
  'host_label': instance.hostLabel,
  'namespace': instance.namespace,
  'endpoint': instance.endpoint,
  'environment_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentId,
    const UuidValueConverter().toJson,
  ),
  'environment_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentConfigId,
    const UuidValueConverter().toJson,
  ),
  'started': instance.started,
  'transport': instance.transport.toJson(),
  'renderer_capabilities': instance.rendererCapabilities?.toJson(),
  'local_service_host': instance.localServiceHost?.toJson(),
  'local_node_runtime': instance.localNodeRuntime?.toJson(),
  'hosted_services': instance.hostedServices?.toJson(),
  'lane_sync': instance.laneSync?.toJson(),
  'environment_admission': instance.environmentAdmission?.toJson(),
  'environment_session': instance.environmentSession?.toJson(),
  'environment_navigation': instance.environmentNavigation?.toJson(),
  'environment_admission_receipt': instance.environmentAdmissionReceipt
      ?.toJson(),
  'environment_session_join_receipt': instance.environmentSessionJoinReceipt
      ?.toJson(),
  'experience_lens': instance.experienceLens?.toJson(),
  'app_screen': instance.appScreen?.toJson(),
  'experience_session_narration': instance.experienceSessionNarration?.toJson(),
  'runtime': instance.runtime?.toJson(),
  'control_plane_profiles': instance.controlPlaneProfiles?.toJson(),
  'control_plane_workspace': instance.controlPlaneWorkspace?.toJson(),
  'workspace_discovery': instance.workspaceDiscovery?.toJson(),
  'selected_workspace': instance.selectedWorkspace?.toJson(),
  'selected_semantic_package': instance.selectedSemanticPackage?.toJson(),
  'current_screen': instance.currentScreen?.toJson(),
  'current_operation': instance.currentOperation?.toJson(),
  'allowed_actions': instance.allowedActions.map((e) => e.toJson()).toList(),
  'recovery_capabilities': instance.recoveryCapabilities
      .map((e) => e.toJson())
      .toList(),
  'warnings': instance.warnings,
};
