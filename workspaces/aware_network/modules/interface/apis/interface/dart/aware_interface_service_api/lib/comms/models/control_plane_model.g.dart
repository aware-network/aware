// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'control_plane_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_InterfaceControlPlaneOperation _$InterfaceControlPlaneOperationFromJson(
  Map<String, dynamic> json,
) => _InterfaceControlPlaneOperation(
  request: json['request'] == null
      ? null
      : InterfaceControlPlaneRequest.fromJson(
          json['request'] as Map<String, dynamic>,
        ),
  response: json['response'] == null
      ? null
      : InterfaceControlPlaneResponse.fromJson(
          json['response'] as Map<String, dynamic>,
        ),
  notification: json['notification'] == null
      ? null
      : InterfaceControlPlaneNotification.fromJson(
          json['notification'] as Map<String, dynamic>,
        ),
);

Map<String, dynamic> _$InterfaceControlPlaneOperationToJson(
  _InterfaceControlPlaneOperation instance,
) => <String, dynamic>{
  'request': instance.request?.toJson(),
  'response': instance.response?.toJson(),
  'notification': instance.notification?.toJson(),
};

PingRequest _$PingRequestFromJson(Map<String, dynamic> json) => PingRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$PingRequestToJson(PingRequest instance) =>
    <String, dynamic>{
      'request_id': _$JsonConverterToJson<String, UuidValue>(
        instance.requestId,
        const UuidValueConverter().toJson,
      ),
      'protocol_version': instance.protocolVersion,
      'operation': instance.$type,
    };

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);

NamespaceEnsureRequest _$NamespaceEnsureRequestFromJson(
  Map<String, dynamic> json,
) => NamespaceEnsureRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  namespace: json['namespace'] as String,
  hostLabel: json['host_label'] as String?,
  endpoint: json['endpoint'] as String?,
  authToken: json['auth_token'] as String?,
  environmentConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_config_id'],
    const UuidValueConverter().fromJson,
  ),
  interfacePackageId: _$JsonConverterFromJson<String, UuidValue>(
    json['interface_package_id'],
    const UuidValueConverter().fromJson,
  ),
  interfacePackageName: json['interface_package_name'] as String?,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$NamespaceEnsureRequestToJson(
  NamespaceEnsureRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'host_label': instance.hostLabel,
  'endpoint': instance.endpoint,
  'auth_token': instance.authToken,
  'environment_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentConfigId,
    const UuidValueConverter().toJson,
  ),
  'interface_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.interfacePackageId,
    const UuidValueConverter().toJson,
  ),
  'interface_package_name': instance.interfacePackageName,
  'operation': instance.$type,
};

NamespaceListRequest _$NamespaceListRequestFromJson(
  Map<String, dynamic> json,
) => NamespaceListRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$NamespaceListRequestToJson(
  NamespaceListRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'operation': instance.$type,
};

InterfaceStatusRequest _$InterfaceStatusRequestFromJson(
  Map<String, dynamic> json,
) => InterfaceStatusRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  namespace: json['namespace'] as String,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceStatusRequestToJson(
  InterfaceStatusRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'operation': instance.$type,
};

InterfaceAdmitEnvironmentActorRequest
_$InterfaceAdmitEnvironmentActorRequestFromJson(Map<String, dynamic> json) =>
    InterfaceAdmitEnvironmentActorRequest(
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      protocolVersion: (json['protocol_version'] as num).toInt(),
      namespace: json['namespace'] as String,
      environmentId: _$JsonConverterFromJson<String, UuidValue>(
        json['environment_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentProfileId: const UuidValueConverter().fromJson(
        json['environment_profile_id'] as String,
      ),
      actorConfigId: const UuidValueConverter().fromJson(
        json['actor_config_id'] as String,
      ),
      classInstanceIdentityId: const UuidValueConverter().fromJson(
        json['class_instance_identity_id'] as String,
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
      reason: json['reason'] as String?,
      evidence: json['evidence'] as Map<String, dynamic>,
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$InterfaceAdmitEnvironmentActorRequestToJson(
  InterfaceAdmitEnvironmentActorRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'environment_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentId,
    const UuidValueConverter().toJson,
  ),
  'environment_profile_id': const UuidValueConverter().toJson(
    instance.environmentProfileId,
  ),
  'actor_config_id': const UuidValueConverter().toJson(instance.actorConfigId),
  'class_instance_identity_id': const UuidValueConverter().toJson(
    instance.classInstanceIdentityId,
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
  'reason': instance.reason,
  'evidence': instance.evidence,
  'operation': instance.$type,
};

InterfaceJoinEnvironmentSessionRequest
_$InterfaceJoinEnvironmentSessionRequestFromJson(Map<String, dynamic> json) =>
    InterfaceJoinEnvironmentSessionRequest(
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      protocolVersion: (json['protocol_version'] as num).toInt(),
      namespace: json['namespace'] as String,
      environmentSessionId: const UuidValueConverter().fromJson(
        json['environment_session_id'] as String,
      ),
      environmentProfileId: _$JsonConverterFromJson<String, UuidValue>(
        json['environment_profile_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentAdmissionReceipt: json['environment_admission_receipt'] == null
          ? null
          : EnvironmentActorAdmissionReceipt.fromJson(
              json['environment_admission_receipt'] as Map<String, dynamic>,
            ),
      reason: json['reason'] as String?,
      evidence: json['evidence'] as Map<String, dynamic>,
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$InterfaceJoinEnvironmentSessionRequestToJson(
  InterfaceJoinEnvironmentSessionRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'environment_session_id': const UuidValueConverter().toJson(
    instance.environmentSessionId,
  ),
  'environment_profile_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentProfileId,
    const UuidValueConverter().toJson,
  ),
  'environment_admission_receipt': instance.environmentAdmissionReceipt
      ?.toJson(),
  'reason': instance.reason,
  'evidence': instance.evidence,
  'operation': instance.$type,
};

InterfaceSelectEnvironmentNavigationTargetRequest
_$InterfaceSelectEnvironmentNavigationTargetRequestFromJson(
  Map<String, dynamic> json,
) => InterfaceSelectEnvironmentNavigationTargetRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  namespace: json['namespace'] as String,
  environmentNavigationContextId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_navigation_context_id'],
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
  reason: json['reason'] as String?,
  evidence: json['evidence'] as Map<String, dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceSelectEnvironmentNavigationTargetRequestToJson(
  InterfaceSelectEnvironmentNavigationTargetRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'environment_navigation_context_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentNavigationContextId,
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
  'reason': instance.reason,
  'evidence': instance.evidence,
  'operation': instance.$type,
};

InterfaceEnterEnvironmentRequest _$InterfaceEnterEnvironmentRequestFromJson(
  Map<String, dynamic> json,
) => InterfaceEnterEnvironmentRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  namespace: json['namespace'] as String,
  environmentId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentProfileId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_profile_id'],
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
  environmentAdmissionReceipt: json['environment_admission_receipt'] == null
      ? null
      : EnvironmentActorAdmissionReceipt.fromJson(
          json['environment_admission_receipt'] as Map<String, dynamic>,
        ),
  environmentSessionId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_session_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentSessionConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_session_config_id'],
    const UuidValueConverter().fromJson,
  ),
  sessionKey: json['session_key'] as String?,
  title: json['title'] as String?,
  description: json['description'] as String?,
  purpose: json['purpose'] as String?,
  sourceKind: json['source_kind'] as String?,
  sourceRef: json['source_ref'] as String?,
  reason: json['reason'] as String?,
  evidence: json['evidence'] as Map<String, dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceEnterEnvironmentRequestToJson(
  InterfaceEnterEnvironmentRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'environment_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentId,
    const UuidValueConverter().toJson,
  ),
  'environment_profile_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentProfileId,
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
  'environment_admission_receipt': instance.environmentAdmissionReceipt
      ?.toJson(),
  'environment_session_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentSessionId,
    const UuidValueConverter().toJson,
  ),
  'environment_session_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentSessionConfigId,
    const UuidValueConverter().toJson,
  ),
  'session_key': instance.sessionKey,
  'title': instance.title,
  'description': instance.description,
  'purpose': instance.purpose,
  'source_kind': instance.sourceKind,
  'source_ref': instance.sourceRef,
  'reason': instance.reason,
  'evidence': instance.evidence,
  'operation': instance.$type,
};

InterfaceResolveExperienceLensRequest
_$InterfaceResolveExperienceLensRequestFromJson(
  Map<String, dynamic> json,
) => InterfaceResolveExperienceLensRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  namespace: json['namespace'] as String,
  environmentSessionJoinReceipt:
      json['environment_session_join_receipt'] == null
      ? null
      : EnvironmentSessionJoinReceipt.fromJson(
          json['environment_session_join_receipt'] as Map<String, dynamic>,
        ),
  environmentNavigationContext: json['environment_navigation_context'] == null
      ? null
      : EnvironmentNavigationContextView.fromJson(
          json['environment_navigation_context'] as Map<String, dynamic>,
        ),
  experienceActorAdmission: json['experience_actor_admission'] == null
      ? null
      : ExperienceActorConfigAdmissionReceipt.fromJson(
          json['experience_actor_admission'] as Map<String, dynamic>,
        ),
  experienceIdentitySessionConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['experience_identity_session_config_id'],
    const UuidValueConverter().fromJson,
  ),
  reason: json['reason'] as String?,
  evidence: json['evidence'] as Map<String, dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceResolveExperienceLensRequestToJson(
  InterfaceResolveExperienceLensRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'environment_session_join_receipt': instance.environmentSessionJoinReceipt
      ?.toJson(),
  'environment_navigation_context': instance.environmentNavigationContext
      ?.toJson(),
  'experience_actor_admission': instance.experienceActorAdmission?.toJson(),
  'experience_identity_session_config_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.experienceIdentitySessionConfigId,
        const UuidValueConverter().toJson,
      ),
  'reason': instance.reason,
  'evidence': instance.evidence,
  'operation': instance.$type,
};

InterfaceActionRequest _$InterfaceActionRequestFromJson(
  Map<String, dynamic> json,
) => InterfaceActionRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  namespace: json['namespace'] as String,
  paneRef: json['pane_ref'] as String?,
  actionKey: json['action_key'] as String,
  actionKind: json['action_kind'] as String?,
  operationRef: json['operation_ref'] as String?,
  sdkOperationId: json['sdk_operation_id'] as String?,
  paneConfigSdkOperationId: json['pane_config_sdk_operation_id'] as String?,
  endpointRef: json['endpoint_ref'] as String?,
  apiCapabilityEndpointId: json['api_capability_endpoint_id'] as String?,
  paneConfigApiCapabilityEndpointId:
      json['pane_config_api_capability_endpoint_id'] as String?,
  payload: json['payload'] as Map<String, dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceActionRequestToJson(
  InterfaceActionRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'pane_ref': instance.paneRef,
  'action_key': instance.actionKey,
  'action_kind': instance.actionKind,
  'operation_ref': instance.operationRef,
  'sdk_operation_id': instance.sdkOperationId,
  'pane_config_sdk_operation_id': instance.paneConfigSdkOperationId,
  'endpoint_ref': instance.endpointRef,
  'api_capability_endpoint_id': instance.apiCapabilityEndpointId,
  'pane_config_api_capability_endpoint_id':
      instance.paneConfigApiCapabilityEndpointId,
  'payload': instance.payload,
  'operation': instance.$type,
};

InterfaceSelectStepRequest _$InterfaceSelectStepRequestFromJson(
  Map<String, dynamic> json,
) => InterfaceSelectStepRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  namespace: json['namespace'] as String,
  stepId: json['step_id'] as String?,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceSelectStepRequestToJson(
  InterfaceSelectStepRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'step_id': instance.stepId,
  'operation': instance.$type,
};

InterfaceSelectProfileRequest _$InterfaceSelectProfileRequestFromJson(
  Map<String, dynamic> json,
) => InterfaceSelectProfileRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  namespace: json['namespace'] as String,
  profileId: json['profile_id'] as String,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceSelectProfileRequestToJson(
  InterfaceSelectProfileRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'profile_id': instance.profileId,
  'operation': instance.$type,
};

InterfaceSelectRuntimeLayoutRequest
_$InterfaceSelectRuntimeLayoutRequestFromJson(Map<String, dynamic> json) =>
    InterfaceSelectRuntimeLayoutRequest(
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      protocolVersion: (json['protocol_version'] as num).toInt(),
      namespace: json['namespace'] as String,
      layoutConfigId: _$JsonConverterFromJson<String, UuidValue>(
        json['layout_config_id'],
        const UuidValueConverter().fromJson,
      ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$InterfaceSelectRuntimeLayoutRequestToJson(
  InterfaceSelectRuntimeLayoutRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'layout_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutConfigId,
    const UuidValueConverter().toJson,
  ),
  'operation': instance.$type,
};

InterfaceActivateRuntimeFocusRequest
_$InterfaceActivateRuntimeFocusRequestFromJson(Map<String, dynamic> json) =>
    InterfaceActivateRuntimeFocusRequest(
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      protocolVersion: (json['protocol_version'] as num).toInt(),
      namespace: json['namespace'] as String,
      representationId: _$JsonConverterFromJson<String, UuidValue>(
        json['representation_id'],
        const UuidValueConverter().fromJson,
      ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$InterfaceActivateRuntimeFocusRequestToJson(
  InterfaceActivateRuntimeFocusRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'representation_id': _$JsonConverterToJson<String, UuidValue>(
    instance.representationId,
    const UuidValueConverter().toJson,
  ),
  'operation': instance.$type,
};

InterfaceRequestWindowLayoutRequest
_$InterfaceRequestWindowLayoutRequestFromJson(Map<String, dynamic> json) =>
    InterfaceRequestWindowLayoutRequest(
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      protocolVersion: (json['protocol_version'] as num).toInt(),
      namespace: json['namespace'] as String,
      interfacePackageId: _$JsonConverterFromJson<String, UuidValue>(
        json['interface_package_id'],
        const UuidValueConverter().fromJson,
      ),
      interfacePackageName: json['interface_package_name'] as String?,
      windowKey: json['window_key'] as String?,
      layoutConfigId: _$JsonConverterFromJson<String, UuidValue>(
        json['layout_config_id'],
        const UuidValueConverter().fromJson,
      ),
      layoutKey: json['layout_key'] as String?,
      sectionKey: json['section_key'] as String?,
      observableId: _$JsonConverterFromJson<String, UuidValue>(
        json['observable_id'],
        const UuidValueConverter().fromJson,
      ),
      representationId: _$JsonConverterFromJson<String, UuidValue>(
        json['representation_id'],
        const UuidValueConverter().fromJson,
      ),
      requestedByService: json['requested_by_service'] as String?,
      requestedByOperation: json['requested_by_operation'] as String?,
      reason: json['reason'] as String?,
      idempotencyKey: json['idempotency_key'] as String?,
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$InterfaceRequestWindowLayoutRequestToJson(
  InterfaceRequestWindowLayoutRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'interface_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.interfacePackageId,
    const UuidValueConverter().toJson,
  ),
  'interface_package_name': instance.interfacePackageName,
  'window_key': instance.windowKey,
  'layout_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutConfigId,
    const UuidValueConverter().toJson,
  ),
  'layout_key': instance.layoutKey,
  'section_key': instance.sectionKey,
  'observable_id': _$JsonConverterToJson<String, UuidValue>(
    instance.observableId,
    const UuidValueConverter().toJson,
  ),
  'representation_id': _$JsonConverterToJson<String, UuidValue>(
    instance.representationId,
    const UuidValueConverter().toJson,
  ),
  'requested_by_service': instance.requestedByService,
  'requested_by_operation': instance.requestedByOperation,
  'reason': instance.reason,
  'idempotency_key': instance.idempotencyKey,
  'operation': instance.$type,
};

InterfaceApplyAttentionLayoutTransitionRequest
_$InterfaceApplyAttentionLayoutTransitionRequestFromJson(
  Map<String, dynamic> json,
) => InterfaceApplyAttentionLayoutTransitionRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  namespace: json['namespace'] as String,
  clientIntentId: json['client_intent_id'] as String,
  expectedPreviousLayoutTransitionId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['expected_previous_layout_transition_id'],
        const UuidValueConverter().fromJson,
      ),
  topologyTransitionId: _$JsonConverterFromJson<String, UuidValue>(
    json['topology_transition_id'],
    const UuidValueConverter().fromJson,
  ),
  sectionStates:
      (json['section_states'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceAttentionLayoutTransitionSectionIntent.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceApplyAttentionLayoutTransitionRequestToJson(
  InterfaceApplyAttentionLayoutTransitionRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'client_intent_id': instance.clientIntentId,
  'expected_previous_layout_transition_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.expectedPreviousLayoutTransitionId,
        const UuidValueConverter().toJson,
      ),
  'topology_transition_id': _$JsonConverterToJson<String, UuidValue>(
    instance.topologyTransitionId,
    const UuidValueConverter().toJson,
  ),
  'section_states': instance.sectionStates.map((e) => e.toJson()).toList(),
  'operation': instance.$type,
};

InterfaceApplyAttentionLayoutTopologyTransitionRequest
_$InterfaceApplyAttentionLayoutTopologyTransitionRequestFromJson(
  Map<String, dynamic> json,
) => InterfaceApplyAttentionLayoutTopologyTransitionRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  namespace: json['namespace'] as String,
  clientIntentId: json['client_intent_id'] as String,
  expectedPreviousTopologyTransitionId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['expected_previous_topology_transition_id'],
        const UuidValueConverter().fromJson,
      ),
  sectionStates:
      (json['section_states'] as List<dynamic>?)
          ?.map(
            (e) =>
                InterfaceAttentionLayoutTopologyTransitionSectionIntent.fromJson(
                  e as Map<String, dynamic>,
                ),
          )
          .toList() ??
      const [],
  $type: json['operation'] as String?,
);

Map<String, dynamic>
_$InterfaceApplyAttentionLayoutTopologyTransitionRequestToJson(
  InterfaceApplyAttentionLayoutTopologyTransitionRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'client_intent_id': instance.clientIntentId,
  'expected_previous_topology_transition_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.expectedPreviousTopologyTransitionId,
        const UuidValueConverter().toJson,
      ),
  'section_states': instance.sectionStates.map((e) => e.toJson()).toList(),
  'operation': instance.$type,
};

InterfaceReportRendererCapabilitiesRequest
_$InterfaceReportRendererCapabilitiesRequestFromJson(
  Map<String, dynamic> json,
) => InterfaceReportRendererCapabilitiesRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  namespace: json['namespace'] as String,
  rendererCapabilities: InterfaceRendererCapabilitiesState.fromJson(
    json['renderer_capabilities'] as Map<String, dynamic>,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceReportRendererCapabilitiesRequestToJson(
  InterfaceReportRendererCapabilitiesRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'renderer_capabilities': instance.rendererCapabilities.toJson(),
  'operation': instance.$type,
};

InterfaceSyncViewStateCursorRequest
_$InterfaceSyncViewStateCursorRequestFromJson(Map<String, dynamic> json) =>
    InterfaceSyncViewStateCursorRequest(
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      protocolVersion: (json['protocol_version'] as num).toInt(),
      namespace: json['namespace'] as String,
      rendererId: json['renderer_id'] as String?,
      knownCursor: json['known_cursor'] as String?,
      knownDigest: json['known_digest'] as String?,
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$InterfaceSyncViewStateCursorRequestToJson(
  InterfaceSyncViewStateCursorRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'renderer_id': instance.rendererId,
  'known_cursor': instance.knownCursor,
  'known_digest': instance.knownDigest,
  'operation': instance.$type,
};

InterfaceFollowRequest _$InterfaceFollowRequestFromJson(
  Map<String, dynamic> json,
) => InterfaceFollowRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  namespace: json['namespace'] as String,
  pollIntervalMs: (json['poll_interval_ms'] as num).toInt(),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceFollowRequestToJson(
  InterfaceFollowRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'poll_interval_ms': instance.pollIntervalMs,
  'operation': instance.$type,
};

InterfaceInvokeApiRequest _$InterfaceInvokeApiRequestFromJson(
  Map<String, dynamic> json,
) => InterfaceInvokeApiRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  namespace: json['namespace'] as String,
  endpointRef: json['endpoint_ref'] as String,
  discriminant: json['discriminant'] as String,
  requestPayload: json['request_payload'] as Map<String, dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceInvokeApiRequestToJson(
  InterfaceInvokeApiRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'endpoint_ref': instance.endpointRef,
  'discriminant': instance.discriminant,
  'request_payload': instance.requestPayload,
  'operation': instance.$type,
};

InterfaceStreamApiRequest _$InterfaceStreamApiRequestFromJson(
  Map<String, dynamic> json,
) => InterfaceStreamApiRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  namespace: json['namespace'] as String,
  endpointRef: json['endpoint_ref'] as String,
  discriminant: json['discriminant'] as String,
  requestPayload: json['request_payload'] as Map<String, dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceStreamApiRequestToJson(
  InterfaceStreamApiRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'endpoint_ref': instance.endpointRef,
  'discriminant': instance.discriminant,
  'request_payload': instance.requestPayload,
  'operation': instance.$type,
};

InterfaceStopRequest _$InterfaceStopRequestFromJson(
  Map<String, dynamic> json,
) => InterfaceStopRequest(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  namespace: json['namespace'] as String,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceStopRequestToJson(
  InterfaceStopRequest instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'operation': instance.$type,
};

PingResponse _$PingResponseFromJson(Map<String, dynamic> json) => PingResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  success: json['success'] as bool,
  error: json['error'] as String?,
  service: json['service'] as String,
  status: json['status'] as String,
  socketPath: json['socket_path'] as String?,
  daemonInstanceId: _$JsonConverterFromJson<String, UuidValue>(
    json['daemon_instance_id'],
    const UuidValueConverter().fromJson,
  ),
  daemonStartedAt: json['daemon_started_at'] as String?,
  daemonSourceFingerprint: json['daemon_source_fingerprint'] as String?,
  repositoryRoot: json['repository_root'] as String?,
  stateHome: json['state_home'] as String?,
  defaultEndpoint: json['default_endpoint'] as String?,
  expectedSourceFingerprint: json['expected_source_fingerprint'] as String?,
  restartRecommended: json['restart_recommended'] as bool,
  restartReason: json['restart_reason'] as String?,
  namespaces:
      (json['namespaces'] as List<dynamic>?)
          ?.map(
            (e) => HostedInterfaceNamespace.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$PingResponseToJson(PingResponse instance) =>
    <String, dynamic>{
      'request_id': _$JsonConverterToJson<String, UuidValue>(
        instance.requestId,
        const UuidValueConverter().toJson,
      ),
      'protocol_version': instance.protocolVersion,
      'success': instance.success,
      'error': instance.error,
      'service': instance.service,
      'status': instance.status,
      'socket_path': instance.socketPath,
      'daemon_instance_id': _$JsonConverterToJson<String, UuidValue>(
        instance.daemonInstanceId,
        const UuidValueConverter().toJson,
      ),
      'daemon_started_at': instance.daemonStartedAt,
      'daemon_source_fingerprint': instance.daemonSourceFingerprint,
      'repository_root': instance.repositoryRoot,
      'state_home': instance.stateHome,
      'default_endpoint': instance.defaultEndpoint,
      'expected_source_fingerprint': instance.expectedSourceFingerprint,
      'restart_recommended': instance.restartRecommended,
      'restart_reason': instance.restartReason,
      'namespaces': instance.namespaces.map((e) => e.toJson()).toList(),
      'operation': instance.$type,
    };

NamespaceEnsureResponse _$NamespaceEnsureResponseFromJson(
  Map<String, dynamic> json,
) => NamespaceEnsureResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  success: json['success'] as bool,
  error: json['error'] as String?,
  namespace: json['namespace'] as String,
  hostState: InterfaceHostState.fromJson(
    json['host_state'] as Map<String, dynamic>,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$NamespaceEnsureResponseToJson(
  NamespaceEnsureResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'host_state': instance.hostState.toJson(),
  'operation': instance.$type,
};

NamespaceListResponse _$NamespaceListResponseFromJson(
  Map<String, dynamic> json,
) => NamespaceListResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  success: json['success'] as bool,
  error: json['error'] as String?,
  namespaces:
      (json['namespaces'] as List<dynamic>?)
          ?.map(
            (e) => HostedInterfaceNamespace.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$NamespaceListResponseToJson(
  NamespaceListResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespaces': instance.namespaces.map((e) => e.toJson()).toList(),
  'operation': instance.$type,
};

InterfaceStatusResponse _$InterfaceStatusResponseFromJson(
  Map<String, dynamic> json,
) => InterfaceStatusResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  success: json['success'] as bool,
  error: json['error'] as String?,
  namespace: json['namespace'] as String,
  hostState: InterfaceHostState.fromJson(
    json['host_state'] as Map<String, dynamic>,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceStatusResponseToJson(
  InterfaceStatusResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'host_state': instance.hostState.toJson(),
  'operation': instance.$type,
};

InterfaceAdmitEnvironmentActorResponse
_$InterfaceAdmitEnvironmentActorResponseFromJson(Map<String, dynamic> json) =>
    InterfaceAdmitEnvironmentActorResponse(
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      protocolVersion: (json['protocol_version'] as num).toInt(),
      success: json['success'] as bool,
      error: json['error'] as String?,
      namespace: json['namespace'] as String,
      environmentAdmission: json['environment_admission'] == null
          ? null
          : InterfaceEnvironmentAdmissionState.fromJson(
              json['environment_admission'] as Map<String, dynamic>,
            ),
      environmentAdmissionReceipt: json['environment_admission_receipt'] == null
          ? null
          : EnvironmentActorAdmissionReceipt.fromJson(
              json['environment_admission_receipt'] as Map<String, dynamic>,
            ),
      hostState: InterfaceHostState.fromJson(
        json['host_state'] as Map<String, dynamic>,
      ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$InterfaceAdmitEnvironmentActorResponseToJson(
  InterfaceAdmitEnvironmentActorResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'environment_admission': instance.environmentAdmission?.toJson(),
  'environment_admission_receipt': instance.environmentAdmissionReceipt
      ?.toJson(),
  'host_state': instance.hostState.toJson(),
  'operation': instance.$type,
};

InterfaceJoinEnvironmentSessionResponse
_$InterfaceJoinEnvironmentSessionResponseFromJson(Map<String, dynamic> json) =>
    InterfaceJoinEnvironmentSessionResponse(
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      protocolVersion: (json['protocol_version'] as num).toInt(),
      success: json['success'] as bool,
      error: json['error'] as String?,
      namespace: json['namespace'] as String,
      environmentSession: json['environment_session'] == null
          ? null
          : EnvironmentSessionView.fromJson(
              json['environment_session'] as Map<String, dynamic>,
            ),
      environmentSessionJoinReceipt:
          json['environment_session_join_receipt'] == null
          ? null
          : EnvironmentSessionJoinReceipt.fromJson(
              json['environment_session_join_receipt'] as Map<String, dynamic>,
            ),
      environmentNavigationContext:
          json['environment_navigation_context'] == null
          ? null
          : EnvironmentNavigationContextView.fromJson(
              json['environment_navigation_context'] as Map<String, dynamic>,
            ),
      defaultNavigationReceipt: json['default_navigation_receipt'] == null
          ? null
          : EnvironmentNavigationCommitReceipt.fromJson(
              json['default_navigation_receipt'] as Map<String, dynamic>,
            ),
      environmentSessionState: json['environment_session_state'] == null
          ? null
          : InterfaceEnvironmentSessionState.fromJson(
              json['environment_session_state'] as Map<String, dynamic>,
            ),
      environmentNavigationState: json['environment_navigation_state'] == null
          ? null
          : InterfaceEnvironmentNavigationState.fromJson(
              json['environment_navigation_state'] as Map<String, dynamic>,
            ),
      hostState: InterfaceHostState.fromJson(
        json['host_state'] as Map<String, dynamic>,
      ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$InterfaceJoinEnvironmentSessionResponseToJson(
  InterfaceJoinEnvironmentSessionResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'environment_session': instance.environmentSession?.toJson(),
  'environment_session_join_receipt': instance.environmentSessionJoinReceipt
      ?.toJson(),
  'environment_navigation_context': instance.environmentNavigationContext
      ?.toJson(),
  'default_navigation_receipt': instance.defaultNavigationReceipt?.toJson(),
  'environment_session_state': instance.environmentSessionState?.toJson(),
  'environment_navigation_state': instance.environmentNavigationState?.toJson(),
  'host_state': instance.hostState.toJson(),
  'operation': instance.$type,
};

InterfaceSelectEnvironmentNavigationTargetResponse
_$InterfaceSelectEnvironmentNavigationTargetResponseFromJson(
  Map<String, dynamic> json,
) => InterfaceSelectEnvironmentNavigationTargetResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  success: json['success'] as bool,
  error: json['error'] as String?,
  namespace: json['namespace'] as String,
  environmentNavigationContext: json['environment_navigation_context'] == null
      ? null
      : EnvironmentNavigationContextView.fromJson(
          json['environment_navigation_context'] as Map<String, dynamic>,
        ),
  environmentNavigationReceipt: json['environment_navigation_receipt'] == null
      ? null
      : EnvironmentNavigationCommitReceipt.fromJson(
          json['environment_navigation_receipt'] as Map<String, dynamic>,
        ),
  environmentNavigationState: json['environment_navigation_state'] == null
      ? null
      : InterfaceEnvironmentNavigationState.fromJson(
          json['environment_navigation_state'] as Map<String, dynamic>,
        ),
  hostState: InterfaceHostState.fromJson(
    json['host_state'] as Map<String, dynamic>,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceSelectEnvironmentNavigationTargetResponseToJson(
  InterfaceSelectEnvironmentNavigationTargetResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'environment_navigation_context': instance.environmentNavigationContext
      ?.toJson(),
  'environment_navigation_receipt': instance.environmentNavigationReceipt
      ?.toJson(),
  'environment_navigation_state': instance.environmentNavigationState?.toJson(),
  'host_state': instance.hostState.toJson(),
  'operation': instance.$type,
};

InterfaceEnterEnvironmentResponse _$InterfaceEnterEnvironmentResponseFromJson(
  Map<String, dynamic> json,
) => InterfaceEnterEnvironmentResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  success: json['success'] as bool,
  error: json['error'] as String?,
  namespace: json['namespace'] as String,
  environmentAdmission: json['environment_admission'] == null
      ? null
      : InterfaceEnvironmentAdmissionState.fromJson(
          json['environment_admission'] as Map<String, dynamic>,
        ),
  environmentAdmissionReceipt: json['environment_admission_receipt'] == null
      ? null
      : EnvironmentActorAdmissionReceipt.fromJson(
          json['environment_admission_receipt'] as Map<String, dynamic>,
        ),
  environmentSession: json['environment_session'] == null
      ? null
      : EnvironmentSessionView.fromJson(
          json['environment_session'] as Map<String, dynamic>,
        ),
  environmentSessionJoinReceipt:
      json['environment_session_join_receipt'] == null
      ? null
      : EnvironmentSessionJoinReceipt.fromJson(
          json['environment_session_join_receipt'] as Map<String, dynamic>,
        ),
  environmentNavigationContext: json['environment_navigation_context'] == null
      ? null
      : EnvironmentNavigationContextView.fromJson(
          json['environment_navigation_context'] as Map<String, dynamic>,
        ),
  defaultNavigationReceipt: json['default_navigation_receipt'] == null
      ? null
      : EnvironmentNavigationCommitReceipt.fromJson(
          json['default_navigation_receipt'] as Map<String, dynamic>,
        ),
  environmentSessionState: json['environment_session_state'] == null
      ? null
      : InterfaceEnvironmentSessionState.fromJson(
          json['environment_session_state'] as Map<String, dynamic>,
        ),
  environmentNavigationState: json['environment_navigation_state'] == null
      ? null
      : InterfaceEnvironmentNavigationState.fromJson(
          json['environment_navigation_state'] as Map<String, dynamic>,
        ),
  hostState: InterfaceHostState.fromJson(
    json['host_state'] as Map<String, dynamic>,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceEnterEnvironmentResponseToJson(
  InterfaceEnterEnvironmentResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'environment_admission': instance.environmentAdmission?.toJson(),
  'environment_admission_receipt': instance.environmentAdmissionReceipt
      ?.toJson(),
  'environment_session': instance.environmentSession?.toJson(),
  'environment_session_join_receipt': instance.environmentSessionJoinReceipt
      ?.toJson(),
  'environment_navigation_context': instance.environmentNavigationContext
      ?.toJson(),
  'default_navigation_receipt': instance.defaultNavigationReceipt?.toJson(),
  'environment_session_state': instance.environmentSessionState?.toJson(),
  'environment_navigation_state': instance.environmentNavigationState?.toJson(),
  'host_state': instance.hostState.toJson(),
  'operation': instance.$type,
};

InterfaceResolveExperienceLensResponse
_$InterfaceResolveExperienceLensResponseFromJson(Map<String, dynamic> json) =>
    InterfaceResolveExperienceLensResponse(
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      protocolVersion: (json['protocol_version'] as num).toInt(),
      success: json['success'] as bool,
      error: json['error'] as String?,
      namespace: json['namespace'] as String,
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
      experienceLens: json['experience_lens'] == null
          ? null
          : InterfaceExperienceLensState.fromJson(
              json['experience_lens'] as Map<String, dynamic>,
            ),
      hostState: InterfaceHostState.fromJson(
        json['host_state'] as Map<String, dynamic>,
      ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$InterfaceResolveExperienceLensResponseToJson(
  InterfaceResolveExperienceLensResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'environment_session': instance.environmentSession?.toJson(),
  'environment_navigation': instance.environmentNavigation?.toJson(),
  'experience_lens': instance.experienceLens?.toJson(),
  'host_state': instance.hostState.toJson(),
  'operation': instance.$type,
};

InterfaceActionResponse _$InterfaceActionResponseFromJson(
  Map<String, dynamic> json,
) => InterfaceActionResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  success: json['success'] as bool,
  error: json['error'] as String?,
  namespace: json['namespace'] as String,
  paneRef: json['pane_ref'] as String?,
  actionKey: json['action_key'] as String,
  hostState: InterfaceHostState.fromJson(
    json['host_state'] as Map<String, dynamic>,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceActionResponseToJson(
  InterfaceActionResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'pane_ref': instance.paneRef,
  'action_key': instance.actionKey,
  'host_state': instance.hostState.toJson(),
  'operation': instance.$type,
};

InterfaceSelectStepResponse _$InterfaceSelectStepResponseFromJson(
  Map<String, dynamic> json,
) => InterfaceSelectStepResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  success: json['success'] as bool,
  error: json['error'] as String?,
  namespace: json['namespace'] as String,
  stepId: json['step_id'] as String?,
  hostState: InterfaceHostState.fromJson(
    json['host_state'] as Map<String, dynamic>,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceSelectStepResponseToJson(
  InterfaceSelectStepResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'step_id': instance.stepId,
  'host_state': instance.hostState.toJson(),
  'operation': instance.$type,
};

InterfaceSelectProfileResponse _$InterfaceSelectProfileResponseFromJson(
  Map<String, dynamic> json,
) => InterfaceSelectProfileResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  success: json['success'] as bool,
  error: json['error'] as String?,
  namespace: json['namespace'] as String,
  profileId: json['profile_id'] as String,
  hostState: InterfaceHostState.fromJson(
    json['host_state'] as Map<String, dynamic>,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceSelectProfileResponseToJson(
  InterfaceSelectProfileResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'profile_id': instance.profileId,
  'host_state': instance.hostState.toJson(),
  'operation': instance.$type,
};

InterfaceSelectRuntimeLayoutResponse
_$InterfaceSelectRuntimeLayoutResponseFromJson(Map<String, dynamic> json) =>
    InterfaceSelectRuntimeLayoutResponse(
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      protocolVersion: (json['protocol_version'] as num).toInt(),
      success: json['success'] as bool,
      error: json['error'] as String?,
      namespace: json['namespace'] as String,
      layoutConfigId: _$JsonConverterFromJson<String, UuidValue>(
        json['layout_config_id'],
        const UuidValueConverter().fromJson,
      ),
      hostState: InterfaceHostState.fromJson(
        json['host_state'] as Map<String, dynamic>,
      ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$InterfaceSelectRuntimeLayoutResponseToJson(
  InterfaceSelectRuntimeLayoutResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'layout_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutConfigId,
    const UuidValueConverter().toJson,
  ),
  'host_state': instance.hostState.toJson(),
  'operation': instance.$type,
};

InterfaceActivateRuntimeFocusResponse
_$InterfaceActivateRuntimeFocusResponseFromJson(Map<String, dynamic> json) =>
    InterfaceActivateRuntimeFocusResponse(
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      protocolVersion: (json['protocol_version'] as num).toInt(),
      success: json['success'] as bool,
      error: json['error'] as String?,
      namespace: json['namespace'] as String,
      representationId: _$JsonConverterFromJson<String, UuidValue>(
        json['representation_id'],
        const UuidValueConverter().fromJson,
      ),
      layoutConfigId: _$JsonConverterFromJson<String, UuidValue>(
        json['layout_config_id'],
        const UuidValueConverter().fromJson,
      ),
      hostState: InterfaceHostState.fromJson(
        json['host_state'] as Map<String, dynamic>,
      ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$InterfaceActivateRuntimeFocusResponseToJson(
  InterfaceActivateRuntimeFocusResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'representation_id': _$JsonConverterToJson<String, UuidValue>(
    instance.representationId,
    const UuidValueConverter().toJson,
  ),
  'layout_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutConfigId,
    const UuidValueConverter().toJson,
  ),
  'host_state': instance.hostState.toJson(),
  'operation': instance.$type,
};

InterfaceRequestWindowLayoutResponse
_$InterfaceRequestWindowLayoutResponseFromJson(Map<String, dynamic> json) =>
    InterfaceRequestWindowLayoutResponse(
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      protocolVersion: (json['protocol_version'] as num).toInt(),
      success: json['success'] as bool,
      error: json['error'] as String?,
      namespace: json['namespace'] as String,
      interfacePackageId: _$JsonConverterFromJson<String, UuidValue>(
        json['interface_package_id'],
        const UuidValueConverter().fromJson,
      ),
      interfacePackageName: json['interface_package_name'] as String?,
      windowKey: json['window_key'] as String?,
      layoutConfigId: _$JsonConverterFromJson<String, UuidValue>(
        json['layout_config_id'],
        const UuidValueConverter().fromJson,
      ),
      layoutKey: json['layout_key'] as String?,
      sectionKey: json['section_key'] as String?,
      observableId: _$JsonConverterFromJson<String, UuidValue>(
        json['observable_id'],
        const UuidValueConverter().fromJson,
      ),
      representationId: _$JsonConverterFromJson<String, UuidValue>(
        json['representation_id'],
        const UuidValueConverter().fromJson,
      ),
      requestedByService: json['requested_by_service'] as String?,
      requestedByOperation: json['requested_by_operation'] as String?,
      reason: json['reason'] as String?,
      idempotencyKey: json['idempotency_key'] as String?,
      hostState: InterfaceHostState.fromJson(
        json['host_state'] as Map<String, dynamic>,
      ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$InterfaceRequestWindowLayoutResponseToJson(
  InterfaceRequestWindowLayoutResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'interface_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.interfacePackageId,
    const UuidValueConverter().toJson,
  ),
  'interface_package_name': instance.interfacePackageName,
  'window_key': instance.windowKey,
  'layout_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutConfigId,
    const UuidValueConverter().toJson,
  ),
  'layout_key': instance.layoutKey,
  'section_key': instance.sectionKey,
  'observable_id': _$JsonConverterToJson<String, UuidValue>(
    instance.observableId,
    const UuidValueConverter().toJson,
  ),
  'representation_id': _$JsonConverterToJson<String, UuidValue>(
    instance.representationId,
    const UuidValueConverter().toJson,
  ),
  'requested_by_service': instance.requestedByService,
  'requested_by_operation': instance.requestedByOperation,
  'reason': instance.reason,
  'idempotency_key': instance.idempotencyKey,
  'host_state': instance.hostState.toJson(),
  'operation': instance.$type,
};

InterfaceApplyAttentionLayoutTransitionResponse
_$InterfaceApplyAttentionLayoutTransitionResponseFromJson(
  Map<String, dynamic> json,
) => InterfaceApplyAttentionLayoutTransitionResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  success: json['success'] as bool,
  error: json['error'] as String?,
  namespace: json['namespace'] as String,
  outcome: json['outcome'] as String,
  conflictReason: json['conflict_reason'] as String?,
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
  hostState: InterfaceHostState.fromJson(
    json['host_state'] as Map<String, dynamic>,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceApplyAttentionLayoutTransitionResponseToJson(
  InterfaceApplyAttentionLayoutTransitionResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'outcome': instance.outcome,
  'conflict_reason': instance.conflictReason,
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
  'host_state': instance.hostState.toJson(),
  'operation': instance.$type,
};

InterfaceApplyAttentionLayoutTopologyTransitionResponse
_$InterfaceApplyAttentionLayoutTopologyTransitionResponseFromJson(
  Map<String, dynamic> json,
) => InterfaceApplyAttentionLayoutTopologyTransitionResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  success: json['success'] as bool,
  error: json['error'] as String?,
  namespace: json['namespace'] as String,
  outcome: json['outcome'] as String,
  conflictReason: json['conflict_reason'] as String?,
  activeTopologyTransitionId: _$JsonConverterFromJson<String, UuidValue>(
    json['active_topology_transition_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  graphHashPost: json['graph_hash_post'] as String?,
  hostState: InterfaceHostState.fromJson(
    json['host_state'] as Map<String, dynamic>,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic>
_$InterfaceApplyAttentionLayoutTopologyTransitionResponseToJson(
  InterfaceApplyAttentionLayoutTopologyTransitionResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'outcome': instance.outcome,
  'conflict_reason': instance.conflictReason,
  'active_topology_transition_id': _$JsonConverterToJson<String, UuidValue>(
    instance.activeTopologyTransitionId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphCommitId,
    const UuidValueConverter().toJson,
  ),
  'graph_hash_post': instance.graphHashPost,
  'host_state': instance.hostState.toJson(),
  'operation': instance.$type,
};

InterfaceReportRendererCapabilitiesResponse
_$InterfaceReportRendererCapabilitiesResponseFromJson(
  Map<String, dynamic> json,
) => InterfaceReportRendererCapabilitiesResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  success: json['success'] as bool,
  error: json['error'] as String?,
  namespace: json['namespace'] as String,
  hostState: InterfaceHostState.fromJson(
    json['host_state'] as Map<String, dynamic>,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceReportRendererCapabilitiesResponseToJson(
  InterfaceReportRendererCapabilitiesResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'host_state': instance.hostState.toJson(),
  'operation': instance.$type,
};

InterfaceSyncViewStateCursorResponse
_$InterfaceSyncViewStateCursorResponseFromJson(Map<String, dynamic> json) =>
    InterfaceSyncViewStateCursorResponse(
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      protocolVersion: (json['protocol_version'] as num).toInt(),
      success: json['success'] as bool,
      error: json['error'] as String?,
      namespace: json['namespace'] as String,
      changed: json['changed'] as bool,
      viewStateCursor: json['view_state_cursor'] == null
          ? null
          : InterfaceHostViewStateCursorState.fromJson(
              json['view_state_cursor'] as Map<String, dynamic>,
            ),
      hostState: InterfaceHostState.fromJson(
        json['host_state'] as Map<String, dynamic>,
      ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$InterfaceSyncViewStateCursorResponseToJson(
  InterfaceSyncViewStateCursorResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'changed': instance.changed,
  'view_state_cursor': instance.viewStateCursor?.toJson(),
  'host_state': instance.hostState.toJson(),
  'operation': instance.$type,
};

InterfaceFollowResponse _$InterfaceFollowResponseFromJson(
  Map<String, dynamic> json,
) => InterfaceFollowResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  success: json['success'] as bool,
  error: json['error'] as String?,
  namespace: json['namespace'] as String,
  hostState: InterfaceHostState.fromJson(
    json['host_state'] as Map<String, dynamic>,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceFollowResponseToJson(
  InterfaceFollowResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'host_state': instance.hostState.toJson(),
  'operation': instance.$type,
};

InterfaceInvokeApiResponse _$InterfaceInvokeApiResponseFromJson(
  Map<String, dynamic> json,
) => InterfaceInvokeApiResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  success: json['success'] as bool,
  error: json['error'] as String?,
  namespace: json['namespace'] as String,
  endpointRef: json['endpoint_ref'] as String,
  discriminant: json['discriminant'] as String,
  serviceStatus: json['service_status'] as String?,
  responsePayload: json['response_payload'],
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceInvokeApiResponseToJson(
  InterfaceInvokeApiResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'endpoint_ref': instance.endpointRef,
  'discriminant': instance.discriminant,
  'service_status': instance.serviceStatus,
  'response_payload': instance.responsePayload,
  'operation': instance.$type,
};

InterfaceStreamApiResponse _$InterfaceStreamApiResponseFromJson(
  Map<String, dynamic> json,
) => InterfaceStreamApiResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  success: json['success'] as bool,
  error: json['error'] as String?,
  namespace: json['namespace'] as String,
  endpointRef: json['endpoint_ref'] as String,
  discriminant: json['discriminant'] as String,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceStreamApiResponseToJson(
  InterfaceStreamApiResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'endpoint_ref': instance.endpointRef,
  'discriminant': instance.discriminant,
  'operation': instance.$type,
};

InterfaceStopResponse _$InterfaceStopResponseFromJson(
  Map<String, dynamic> json,
) => InterfaceStopResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  success: json['success'] as bool,
  error: json['error'] as String?,
  namespace: json['namespace'] as String,
  hostedNamespace: HostedInterfaceNamespace.fromJson(
    json['hosted_namespace'] as Map<String, dynamic>,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceStopResponseToJson(
  InterfaceStopResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'hosted_namespace': instance.hostedNamespace.toJson(),
  'operation': instance.$type,
};

InterfaceStateNotification _$InterfaceStateNotificationFromJson(
  Map<String, dynamic> json,
) => InterfaceStateNotification(
  notificationId: _$JsonConverterFromJson<String, UuidValue>(
    json['notification_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  namespace: json['namespace'] as String,
  hostState: InterfaceHostState.fromJson(
    json['host_state'] as Map<String, dynamic>,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceStateNotificationToJson(
  InterfaceStateNotification instance,
) => <String, dynamic>{
  'notification_id': _$JsonConverterToJson<String, UuidValue>(
    instance.notificationId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'host_state': instance.hostState.toJson(),
  'operation': instance.$type,
};

InterfaceApiEventNotification _$InterfaceApiEventNotificationFromJson(
  Map<String, dynamic> json,
) => InterfaceApiEventNotification(
  notificationId: _$JsonConverterFromJson<String, UuidValue>(
    json['notification_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  namespace: json['namespace'] as String,
  endpointRef: json['endpoint_ref'] as String,
  discriminant: json['discriminant'] as String,
  eventKind: json['event_kind'] as String,
  sequence: (json['sequence'] as num).toInt(),
  itemKey: json['item_key'] as String,
  payload: json['payload'],
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceApiEventNotificationToJson(
  InterfaceApiEventNotification instance,
) => <String, dynamic>{
  'notification_id': _$JsonConverterToJson<String, UuidValue>(
    instance.notificationId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'endpoint_ref': instance.endpointRef,
  'discriminant': instance.discriminant,
  'event_kind': instance.eventKind,
  'sequence': instance.sequence,
  'item_key': instance.itemKey,
  'payload': instance.payload,
  'operation': instance.$type,
};

InterfaceApiStreamClosedNotification
_$InterfaceApiStreamClosedNotificationFromJson(Map<String, dynamic> json) =>
    InterfaceApiStreamClosedNotification(
      notificationId: _$JsonConverterFromJson<String, UuidValue>(
        json['notification_id'],
        const UuidValueConverter().fromJson,
      ),
      protocolVersion: (json['protocol_version'] as num).toInt(),
      namespace: json['namespace'] as String,
      endpointRef: json['endpoint_ref'] as String,
      discriminant: json['discriminant'] as String,
      serviceStatus: json['service_status'] as String?,
      responsePayload: json['response_payload'],
      error: json['error'] as String?,
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$InterfaceApiStreamClosedNotificationToJson(
  InterfaceApiStreamClosedNotification instance,
) => <String, dynamic>{
  'notification_id': _$JsonConverterToJson<String, UuidValue>(
    instance.notificationId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'endpoint_ref': instance.endpointRef,
  'discriminant': instance.discriminant,
  'service_status': instance.serviceStatus,
  'response_payload': instance.responsePayload,
  'error': instance.error,
  'operation': instance.$type,
};

_InterfaceSessionStartRequest _$InterfaceSessionStartRequestFromJson(
  Map<String, dynamic> json,
) => _InterfaceSessionStartRequest(
  operation: json['operation'] as String,
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  interfaceId: const UuidValueConverter().fromJson(
    json['interface_id'] as String,
  ),
  identitySessionId: const UuidValueConverter().fromJson(
    json['identity_session_id'] as String,
  ),
  name: json['name'] as String,
  state: json['state'] as String,
);

Map<String, dynamic> _$InterfaceSessionStartRequestToJson(
  _InterfaceSessionStartRequest instance,
) => <String, dynamic>{
  'operation': instance.operation,
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'interface_id': const UuidValueConverter().toJson(instance.interfaceId),
  'identity_session_id': const UuidValueConverter().toJson(
    instance.identitySessionId,
  ),
  'name': instance.name,
  'state': instance.state,
};

_InterfaceSessionStartResponse _$InterfaceSessionStartResponseFromJson(
  Map<String, dynamic> json,
) => _InterfaceSessionStartResponse(
  operation: json['operation'] as String,
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  success: json['success'] as bool,
  error: json['error'] as String?,
  interfaceSessionId: _$JsonConverterFromJson<String, UuidValue>(
    json['interface_session_id'],
    const UuidValueConverter().fromJson,
  ),
  interfaceId: const UuidValueConverter().fromJson(
    json['interface_id'] as String,
  ),
  identitySessionId: const UuidValueConverter().fromJson(
    json['identity_session_id'] as String,
  ),
  name: json['name'] as String,
  state: json['state'] as String,
  domainCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['domain_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  graphHashPost: json['graph_hash_post'] as String?,
);

Map<String, dynamic> _$InterfaceSessionStartResponseToJson(
  _InterfaceSessionStartResponse instance,
) => <String, dynamic>{
  'operation': instance.operation,
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'interface_session_id': _$JsonConverterToJson<String, UuidValue>(
    instance.interfaceSessionId,
    const UuidValueConverter().toJson,
  ),
  'interface_id': const UuidValueConverter().toJson(instance.interfaceId),
  'identity_session_id': const UuidValueConverter().toJson(
    instance.identitySessionId,
  ),
  'name': instance.name,
  'state': instance.state,
  'domain_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.domainCommitId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphCommitId,
    const UuidValueConverter().toJson,
  ),
  'graph_hash_post': instance.graphHashPost,
};

_InterfaceSessionDescribeRequest _$InterfaceSessionDescribeRequestFromJson(
  Map<String, dynamic> json,
) => _InterfaceSessionDescribeRequest(
  operation: json['operation'] as String,
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  interfaceSessionId: const UuidValueConverter().fromJson(
    json['interface_session_id'] as String,
  ),
);

Map<String, dynamic> _$InterfaceSessionDescribeRequestToJson(
  _InterfaceSessionDescribeRequest instance,
) => <String, dynamic>{
  'operation': instance.operation,
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'interface_session_id': const UuidValueConverter().toJson(
    instance.interfaceSessionId,
  ),
};

_InterfaceSessionExperienceSessionView
_$InterfaceSessionExperienceSessionViewFromJson(Map<String, dynamic> json) =>
    _InterfaceSessionExperienceSessionView(
      interfaceSessionExperienceSessionId: const UuidValueConverter().fromJson(
        json['interface_session_experience_session_id'] as String,
      ),
      experienceSessionId: const UuidValueConverter().fromJson(
        json['experience_session_id'] as String,
      ),
      status: json['status'] as String,
      metadataJson: json['metadata_json'] as Map<String, dynamic>?,
      domainCommitId: const UuidValueConverter().fromJson(
        json['domain_commit_id'] as String,
      ),
    );

Map<String, dynamic> _$InterfaceSessionExperienceSessionViewToJson(
  _InterfaceSessionExperienceSessionView instance,
) => <String, dynamic>{
  'interface_session_experience_session_id': const UuidValueConverter().toJson(
    instance.interfaceSessionExperienceSessionId,
  ),
  'experience_session_id': const UuidValueConverter().toJson(
    instance.experienceSessionId,
  ),
  'status': instance.status,
  'metadata_json': instance.metadataJson,
  'domain_commit_id': const UuidValueConverter().toJson(
    instance.domainCommitId,
  ),
};

_InterfaceSessionView _$InterfaceSessionViewFromJson(
  Map<String, dynamic> json,
) => _InterfaceSessionView(
  interfaceSessionId: const UuidValueConverter().fromJson(
    json['interface_session_id'] as String,
  ),
  interfaceId: const UuidValueConverter().fromJson(
    json['interface_id'] as String,
  ),
  identitySessionId: const UuidValueConverter().fromJson(
    json['identity_session_id'] as String,
  ),
  name: json['name'] as String,
  state: json['state'] as String,
  domainCommitId: const UuidValueConverter().fromJson(
    json['domain_commit_id'] as String,
  ),
  experienceSessions:
      (json['experience_sessions'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceSessionExperienceSessionView.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$InterfaceSessionViewToJson(
  _InterfaceSessionView instance,
) => <String, dynamic>{
  'interface_session_id': const UuidValueConverter().toJson(
    instance.interfaceSessionId,
  ),
  'interface_id': const UuidValueConverter().toJson(instance.interfaceId),
  'identity_session_id': const UuidValueConverter().toJson(
    instance.identitySessionId,
  ),
  'name': instance.name,
  'state': instance.state,
  'domain_commit_id': const UuidValueConverter().toJson(
    instance.domainCommitId,
  ),
  'experience_sessions': instance.experienceSessions
      .map((e) => e.toJson())
      .toList(),
};

_InterfaceSessionDescribeResponse _$InterfaceSessionDescribeResponseFromJson(
  Map<String, dynamic> json,
) => _InterfaceSessionDescribeResponse(
  operation: json['operation'] as String,
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  success: json['success'] as bool,
  error: json['error'] as String?,
  status: json['status'] as String,
  session: json['session'] == null
      ? null
      : InterfaceSessionView.fromJson(json['session'] as Map<String, dynamic>),
);

Map<String, dynamic> _$InterfaceSessionDescribeResponseToJson(
  _InterfaceSessionDescribeResponse instance,
) => <String, dynamic>{
  'operation': instance.operation,
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'status': instance.status,
  'session': instance.session?.toJson(),
};

_InterfaceExperienceSessionMountRequest
_$InterfaceExperienceSessionMountRequestFromJson(Map<String, dynamic> json) =>
    _InterfaceExperienceSessionMountRequest(
      operation: json['operation'] as String,
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      protocolVersion: (json['protocol_version'] as num).toInt(),
      interfaceSessionId: const UuidValueConverter().fromJson(
        json['interface_session_id'] as String,
      ),
      experienceSessionId: const UuidValueConverter().fromJson(
        json['experience_session_id'] as String,
      ),
      status: json['status'] as String,
      metadataJson: json['metadata_json'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$InterfaceExperienceSessionMountRequestToJson(
  _InterfaceExperienceSessionMountRequest instance,
) => <String, dynamic>{
  'operation': instance.operation,
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'interface_session_id': const UuidValueConverter().toJson(
    instance.interfaceSessionId,
  ),
  'experience_session_id': const UuidValueConverter().toJson(
    instance.experienceSessionId,
  ),
  'status': instance.status,
  'metadata_json': instance.metadataJson,
};

_InterfaceExperienceSessionMountResponse
_$InterfaceExperienceSessionMountResponseFromJson(Map<String, dynamic> json) =>
    _InterfaceExperienceSessionMountResponse(
      operation: json['operation'] as String,
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      protocolVersion: (json['protocol_version'] as num).toInt(),
      success: json['success'] as bool,
      error: json['error'] as String?,
      interfaceSessionExperienceSessionId: const UuidValueConverter().fromJson(
        json['interface_session_experience_session_id'] as String,
      ),
      interfaceSessionId: const UuidValueConverter().fromJson(
        json['interface_session_id'] as String,
      ),
      experienceSessionId: const UuidValueConverter().fromJson(
        json['experience_session_id'] as String,
      ),
      status: json['status'] as String,
      metadataJson: json['metadata_json'] as Map<String, dynamic>?,
      domainCommitId: _$JsonConverterFromJson<String, UuidValue>(
        json['domain_commit_id'],
        const UuidValueConverter().fromJson,
      ),
      objectInstanceGraphCommitId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_instance_graph_commit_id'],
        const UuidValueConverter().fromJson,
      ),
      graphHashPost: json['graph_hash_post'] as String?,
    );

Map<String, dynamic> _$InterfaceExperienceSessionMountResponseToJson(
  _InterfaceExperienceSessionMountResponse instance,
) => <String, dynamic>{
  'operation': instance.operation,
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'interface_session_experience_session_id': const UuidValueConverter().toJson(
    instance.interfaceSessionExperienceSessionId,
  ),
  'interface_session_id': const UuidValueConverter().toJson(
    instance.interfaceSessionId,
  ),
  'experience_session_id': const UuidValueConverter().toJson(
    instance.experienceSessionId,
  ),
  'status': instance.status,
  'metadata_json': instance.metadataJson,
  'domain_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.domainCommitId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphCommitId,
    const UuidValueConverter().toJson,
  ),
  'graph_hash_post': instance.graphHashPost,
};

_InterfaceEnterAppScreenRequest _$InterfaceEnterAppScreenRequestFromJson(
  Map<String, dynamic> json,
) => _InterfaceEnterAppScreenRequest(
  operation: json['operation'] as String,
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  namespace: json['namespace'] as String,
  appPackageId: const UuidValueConverter().fromJson(
    json['app_package_id'] as String,
  ),
  appPackageBranchId: const UuidValueConverter().fromJson(
    json['app_package_branch_id'] as String,
  ),
  appPackageObjectInstanceGraphCommitId: const UuidValueConverter().fromJson(
    json['app_package_object_instance_graph_commit_id'] as String,
  ),
  appConfigScreenConfigId: const UuidValueConverter().fromJson(
    json['app_config_screen_config_id'] as String,
  ),
  reason: json['reason'] as String?,
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$InterfaceEnterAppScreenRequestToJson(
  _InterfaceEnterAppScreenRequest instance,
) => <String, dynamic>{
  'operation': instance.operation,
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'namespace': instance.namespace,
  'app_package_id': const UuidValueConverter().toJson(instance.appPackageId),
  'app_package_branch_id': const UuidValueConverter().toJson(
    instance.appPackageBranchId,
  ),
  'app_package_object_instance_graph_commit_id': const UuidValueConverter()
      .toJson(instance.appPackageObjectInstanceGraphCommitId),
  'app_config_screen_config_id': const UuidValueConverter().toJson(
    instance.appConfigScreenConfigId,
  ),
  'reason': instance.reason,
  'evidence': instance.evidence,
};

_InterfaceEnterAppScreenResponse _$InterfaceEnterAppScreenResponseFromJson(
  Map<String, dynamic> json,
) => _InterfaceEnterAppScreenResponse(
  operation: json['operation'] as String,
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  protocolVersion: (json['protocol_version'] as num).toInt(),
  success: json['success'] as bool,
  error: json['error'] as String?,
  namespace: json['namespace'] as String,
  appScreen: json['app_screen'] == null
      ? null
      : InterfaceAppScreenState.fromJson(
          json['app_screen'] as Map<String, dynamic>,
        ),
  hostState: InterfaceHostState.fromJson(
    json['host_state'] as Map<String, dynamic>,
  ),
);

Map<String, dynamic> _$InterfaceEnterAppScreenResponseToJson(
  _InterfaceEnterAppScreenResponse instance,
) => <String, dynamic>{
  'operation': instance.operation,
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'protocol_version': instance.protocolVersion,
  'success': instance.success,
  'error': instance.error,
  'namespace': instance.namespace,
  'app_screen': instance.appScreen?.toJson(),
  'host_state': instance.hostState.toJson(),
};

_InterfaceAttentionLayoutTransitionSectionIntent
_$InterfaceAttentionLayoutTransitionSectionIntentFromJson(
  Map<String, dynamic> json,
) => _InterfaceAttentionLayoutTransitionSectionIntent(
  layoutConfigSectionConfigId: const UuidValueConverter().fromJson(
    json['layout_config_section_config_id'] as String,
  ),
  order: (json['order'] as num).toInt(),
  weightMicros: (json['weight_micros'] as num).toInt(),
  isVisible: json['is_visible'] as bool,
  isCollapsed: json['is_collapsed'] as bool,
);

Map<String, dynamic> _$InterfaceAttentionLayoutTransitionSectionIntentToJson(
  _InterfaceAttentionLayoutTransitionSectionIntent instance,
) => <String, dynamic>{
  'layout_config_section_config_id': const UuidValueConverter().toJson(
    instance.layoutConfigSectionConfigId,
  ),
  'order': instance.order,
  'weight_micros': instance.weightMicros,
  'is_visible': instance.isVisible,
  'is_collapsed': instance.isCollapsed,
};

_InterfaceAttentionLayoutTopologyTransitionSectionIntent
_$InterfaceAttentionLayoutTopologyTransitionSectionIntentFromJson(
  Map<String, dynamic> json,
) => _InterfaceAttentionLayoutTopologyTransitionSectionIntent(
  layoutConfigSectionConfigId: const UuidValueConverter().fromJson(
    json['layout_config_section_config_id'] as String,
  ),
  order: (json['order'] as num).toInt(),
);

Map<String, dynamic>
_$InterfaceAttentionLayoutTopologyTransitionSectionIntentToJson(
  _InterfaceAttentionLayoutTopologyTransitionSectionIntent instance,
) => <String, dynamic>{
  'layout_config_section_config_id': const UuidValueConverter().toJson(
    instance.layoutConfigSectionConfigId,
  ),
  'order': instance.order,
};
