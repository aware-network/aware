// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import '../../environment/environment_model.dart';
import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'interface_host_state_model.freezed.dart';
part 'interface_host_state_model.g.dart';

/// Transport-facing state snapshots exposed by the local Interface daemon.
/// These DTOs are not SSOT graph entities. They are local control-plane read
/// models that summarize the live host service state for renderer and CLI clients.
@freezed
abstract class InterfaceTransportState with _$InterfaceTransportState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceTransportState.def({
    required bool available,
    required bool registered,
    required bool authenticated,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? interfaceId,
    @UuidValueConverter() UuidValue? interfaceSystemActorId,
    @UuidValueConverter() UuidValue? interfaceSystemIdentityId,
    @UuidValueConverter() UuidValue? interfaceSessionId,
    String? sessionLabel,
    @Default(const []) List<String> capabilities,
    int? protocolVersion,
    String? lastSeenAt,
    @UuidValueConverter() UuidValue? interfaceIdentityNetworkNodeId,
    @UuidValueConverter() UuidValue? interfaceSessionNetworkBindingId,
  }) = _InterfaceTransportState;

  factory InterfaceTransportState({
    required bool available,
    required bool registered,
    required bool authenticated,
    UuidValue? actorId,
    UuidValue? interfaceId,
    UuidValue? interfaceSystemActorId,
    UuidValue? interfaceSystemIdentityId,
    UuidValue? interfaceSessionId,
    String? sessionLabel,
    List<String> capabilities = const [],
    int? protocolVersion,
    String? lastSeenAt,
    UuidValue? interfaceIdentityNetworkNodeId,
    UuidValue? interfaceSessionNetworkBindingId,
  }) {
    return _InterfaceTransportState(
      available: available,
      registered: registered,
      authenticated: authenticated,
      actorId: actorId,
      interfaceId: interfaceId,
      interfaceSystemActorId: interfaceSystemActorId,
      interfaceSystemIdentityId: interfaceSystemIdentityId,
      interfaceSessionId: interfaceSessionId,
      sessionLabel: sessionLabel,
      capabilities: capabilities,
      protocolVersion: protocolVersion,
      lastSeenAt: lastSeenAt,
      interfaceIdentityNetworkNodeId: interfaceIdentityNetworkNodeId,
      interfaceSessionNetworkBindingId: interfaceSessionNetworkBindingId,
    );
  }

  factory InterfaceTransportState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceTransportStateFromJson(json);
}

@freezed
abstract class InterfaceRendererPanePackageCapabilityState
    with _$InterfaceRendererPanePackageCapabilityState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceRendererPanePackageCapabilityState.def({
    @UuidValueConverter() UuidValue? panePackageId,
    String? panePackageName,
    required String paneKind,
  }) = _InterfaceRendererPanePackageCapabilityState;

  factory InterfaceRendererPanePackageCapabilityState({
    UuidValue? panePackageId,
    String? panePackageName,
    required String paneKind,
  }) {
    return _InterfaceRendererPanePackageCapabilityState(
      panePackageId: panePackageId,
      panePackageName: panePackageName,
      paneKind: paneKind,
    );
  }

  factory InterfaceRendererPanePackageCapabilityState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceRendererPanePackageCapabilityStateFromJson(json);
}

@freezed
abstract class InterfaceRendererViewCapabilityState
    with _$InterfaceRendererViewCapabilityState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceRendererViewCapabilityState.def({
    String? viewRef,
    String? projectionViewKey,
    String? paneKind,
    required bool hasDecoder,
  }) = _InterfaceRendererViewCapabilityState;

  factory InterfaceRendererViewCapabilityState({
    String? viewRef,
    String? projectionViewKey,
    String? paneKind,
    bool? hasDecoder,
  }) {
    return _InterfaceRendererViewCapabilityState(
      viewRef: viewRef,
      projectionViewKey: projectionViewKey,
      paneKind: paneKind,
      hasDecoder: hasDecoder ?? false,
    );
  }

  factory InterfaceRendererViewCapabilityState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceRendererViewCapabilityStateFromJson({
    ...json,
    if (!json.containsKey('has_decoder')) 'has_decoder': false,
  });
}

@freezed
abstract class InterfaceRendererCacheCapabilityState
    with _$InterfaceRendererCacheCapabilityState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceRendererCacheCapabilityState.def({
    required String storeKind,
    required bool supportsNamespaceReplace,
    required bool supportsPersistentStorage,
    required bool supportsCursorLookup,
  }) = _InterfaceRendererCacheCapabilityState;

  factory InterfaceRendererCacheCapabilityState({
    String? storeKind,
    bool? supportsNamespaceReplace,
    bool? supportsPersistentStorage,
    bool? supportsCursorLookup,
  }) {
    return _InterfaceRendererCacheCapabilityState(
      storeKind: storeKind ?? 'memory',
      supportsNamespaceReplace: supportsNamespaceReplace ?? true,
      supportsPersistentStorage: supportsPersistentStorage ?? false,
      supportsCursorLookup: supportsCursorLookup ?? false,
    );
  }

  factory InterfaceRendererCacheCapabilityState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceRendererCacheCapabilityStateFromJson({
    ...json,
    if (!json.containsKey('store_kind')) 'store_kind': 'memory',
    if (!json.containsKey('supports_namespace_replace'))
      'supports_namespace_replace': true,
    if (!json.containsKey('supports_persistent_storage'))
      'supports_persistent_storage': false,
    if (!json.containsKey('supports_cursor_lookup'))
      'supports_cursor_lookup': false,
  });
}

@freezed
abstract class InterfaceRendererCapabilitiesState
    with _$InterfaceRendererCapabilitiesState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceRendererCapabilitiesState.def({
    required String rendererId,
    required String rendererKind,
    String? rendererVersion,
    @UuidValueConverter() UuidValue? interfacePackageId,
    String? interfacePackageName,
    @Default(const []) List<String> experienceKeys,
    @Default(const [])
    List<InterfaceRendererPanePackageCapabilityState> panePackages,
    @Default(const [])
    List<InterfaceRendererViewCapabilityState> viewCapabilities,
    InterfaceRendererCacheCapabilityState? cache,
    String? reportedAt,
  }) = _InterfaceRendererCapabilitiesState;

  factory InterfaceRendererCapabilitiesState({
    required String rendererId,
    String? rendererKind,
    String? rendererVersion,
    UuidValue? interfacePackageId,
    String? interfacePackageName,
    List<String> experienceKeys = const [],
    List<InterfaceRendererPanePackageCapabilityState> panePackages = const [],
    List<InterfaceRendererViewCapabilityState> viewCapabilities = const [],
    InterfaceRendererCacheCapabilityState? cache,
    String? reportedAt,
  }) {
    return _InterfaceRendererCapabilitiesState(
      rendererId: rendererId,
      rendererKind: rendererKind ?? 'flutter',
      rendererVersion: rendererVersion,
      interfacePackageId: interfacePackageId,
      interfacePackageName: interfacePackageName,
      experienceKeys: experienceKeys,
      panePackages: panePackages,
      viewCapabilities: viewCapabilities,
      cache: cache,
      reportedAt: reportedAt,
    );
  }

  factory InterfaceRendererCapabilitiesState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceRendererCapabilitiesStateFromJson({
    ...json,
    if (!json.containsKey('renderer_kind')) 'renderer_kind': 'flutter',
  });
}

@freezed
abstract class InterfaceHostViewStateDigestEntryState
    with _$InterfaceHostViewStateDigestEntryState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceHostViewStateDigestEntryState.def({
    required String paneStateKey,
    required String digest,
    String? viewRef,
    String? projectionViewKey,
    String? projectionHash,
    String? headCommitId,
    String? graphHashPost,
  }) = _InterfaceHostViewStateDigestEntryState;

  factory InterfaceHostViewStateDigestEntryState({
    required String paneStateKey,
    required String digest,
    String? viewRef,
    String? projectionViewKey,
    String? projectionHash,
    String? headCommitId,
    String? graphHashPost,
  }) {
    return _InterfaceHostViewStateDigestEntryState(
      paneStateKey: paneStateKey,
      digest: digest,
      viewRef: viewRef,
      projectionViewKey: projectionViewKey,
      projectionHash: projectionHash,
      headCommitId: headCommitId,
      graphHashPost: graphHashPost,
    );
  }

  factory InterfaceHostViewStateDigestEntryState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceHostViewStateDigestEntryStateFromJson(json);
}

@freezed
abstract class InterfaceHostViewStateCursorState
    with _$InterfaceHostViewStateCursorState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceHostViewStateCursorState.def({
    required String cursor,
    required String digest,
    required int materializedEntryCount,
    @Default(const [])
    List<InterfaceHostViewStateDigestEntryState> entryDigests,
    String? computedAt,
  }) = _InterfaceHostViewStateCursorState;

  factory InterfaceHostViewStateCursorState({
    required String cursor,
    required String digest,
    int? materializedEntryCount,
    List<InterfaceHostViewStateDigestEntryState> entryDigests = const [],
    String? computedAt,
  }) {
    return _InterfaceHostViewStateCursorState(
      cursor: cursor,
      digest: digest,
      materializedEntryCount: materializedEntryCount ?? 0,
      entryDigests: entryDigests,
      computedAt: computedAt,
    );
  }

  factory InterfaceHostViewStateCursorState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceHostViewStateCursorStateFromJson({
    ...json,
    if (!json.containsKey('materialized_entry_count'))
      'materialized_entry_count': 0,
  });
}

@freezed
abstract class InterfaceLaneSyncState with _$InterfaceLaneSyncState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceLaneSyncState.def({
    required bool enabled,
    required bool watching,
    String? windowKey,
    @UuidValueConverter() UuidValue? laneId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() UuidValue? lastCommitId,
    String? lastGraphHashPost,
    required int updatesReceived,
    required int advancedCount,
    String? lastSyncedAt,
    String? error,
  }) = _InterfaceLaneSyncState;

  factory InterfaceLaneSyncState({
    required bool enabled,
    required bool watching,
    String? windowKey,
    UuidValue? laneId,
    UuidValue? branchId,
    String? projectionHash,
    UuidValue? lastCommitId,
    String? lastGraphHashPost,
    int? updatesReceived,
    int? advancedCount,
    String? lastSyncedAt,
    String? error,
  }) {
    return _InterfaceLaneSyncState(
      enabled: enabled,
      watching: watching,
      windowKey: windowKey,
      laneId: laneId,
      branchId: branchId,
      projectionHash: projectionHash,
      lastCommitId: lastCommitId,
      lastGraphHashPost: lastGraphHashPost,
      updatesReceived: updatesReceived ?? 0,
      advancedCount: advancedCount ?? 0,
      lastSyncedAt: lastSyncedAt,
      error: error,
    );
  }

  factory InterfaceLaneSyncState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceLaneSyncStateFromJson({
        ...json,
        if (!json.containsKey('updates_received')) 'updates_received': 0,
        if (!json.containsKey('advanced_count')) 'advanced_count': 0,
      });
}

@freezed
abstract class InterfaceEnvironmentAdmissionRoleEligibilityState
    with _$InterfaceEnvironmentAdmissionRoleEligibilityState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceEnvironmentAdmissionRoleEligibilityState.def({
    @UuidValueConverter() required UuidValue environmentProfileActorConfigId,
    @UuidValueConverter() required UuidValue actorConfigRoleConfigId,
    @UuidValueConverter() required UuidValue roleConfigId,
    String? roleConfigName,
  }) = _InterfaceEnvironmentAdmissionRoleEligibilityState;

  factory InterfaceEnvironmentAdmissionRoleEligibilityState({
    required UuidValue environmentProfileActorConfigId,
    required UuidValue actorConfigRoleConfigId,
    required UuidValue roleConfigId,
    String? roleConfigName,
  }) {
    return _InterfaceEnvironmentAdmissionRoleEligibilityState(
      environmentProfileActorConfigId: environmentProfileActorConfigId,
      actorConfigRoleConfigId: actorConfigRoleConfigId,
      roleConfigId: roleConfigId,
      roleConfigName: roleConfigName,
    );
  }

  factory InterfaceEnvironmentAdmissionRoleEligibilityState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceEnvironmentAdmissionRoleEligibilityStateFromJson(json);
}

@freezed
abstract class InterfaceEnvironmentAdmissionRoleBindingState
    with _$InterfaceEnvironmentAdmissionRoleBindingState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceEnvironmentAdmissionRoleBindingState.def({
    @UuidValueConverter() required UuidValue environmentProfileActorConfigId,
    @UuidValueConverter() required UuidValue actorConfigRoleConfigId,
    @UuidValueConverter() required UuidValue roleConfigId,
    String? roleConfigName,
    @UuidValueConverter() required UuidValue actorId,
    @UuidValueConverter() required UuidValue roleId,
    @UuidValueConverter() required UuidValue actorRoleId,
    @UuidValueConverter() required UuidValue roleClassInstanceId,
    @UuidValueConverter() required UuidValue classInstanceIdentityId,
    @UuidValueConverter() required UuidValue roleConfigClassConfigId,
    @UuidValueConverter() required UuidValue objectInstanceGraphIdentityId,
    required String objectInstanceGraphBranchKey,
    @UuidValueConverter() UuidValue? objectInstanceGraphBranchId,
  }) = _InterfaceEnvironmentAdmissionRoleBindingState;

  factory InterfaceEnvironmentAdmissionRoleBindingState({
    required UuidValue environmentProfileActorConfigId,
    required UuidValue actorConfigRoleConfigId,
    required UuidValue roleConfigId,
    String? roleConfigName,
    required UuidValue actorId,
    required UuidValue roleId,
    required UuidValue actorRoleId,
    required UuidValue roleClassInstanceId,
    required UuidValue classInstanceIdentityId,
    required UuidValue roleConfigClassConfigId,
    required UuidValue objectInstanceGraphIdentityId,
    required String objectInstanceGraphBranchKey,
    UuidValue? objectInstanceGraphBranchId,
  }) {
    return _InterfaceEnvironmentAdmissionRoleBindingState(
      environmentProfileActorConfigId: environmentProfileActorConfigId,
      actorConfigRoleConfigId: actorConfigRoleConfigId,
      roleConfigId: roleConfigId,
      roleConfigName: roleConfigName,
      actorId: actorId,
      roleId: roleId,
      actorRoleId: actorRoleId,
      roleClassInstanceId: roleClassInstanceId,
      classInstanceIdentityId: classInstanceIdentityId,
      roleConfigClassConfigId: roleConfigClassConfigId,
      objectInstanceGraphIdentityId: objectInstanceGraphIdentityId,
      objectInstanceGraphBranchKey: objectInstanceGraphBranchKey,
      objectInstanceGraphBranchId: objectInstanceGraphBranchId,
    );
  }

  factory InterfaceEnvironmentAdmissionRoleBindingState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceEnvironmentAdmissionRoleBindingStateFromJson(json);
}

@freezed
abstract class InterfaceEnvironmentAdmissionState
    with _$InterfaceEnvironmentAdmissionState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceEnvironmentAdmissionState.def({
    required String status,
    required String sourceKind,
    required bool accepted,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() UuidValue? environmentProfileId,
    @UuidValueConverter() UuidValue? environmentProfileActorConfigId,
    @UuidValueConverter() UuidValue? actorConfigId,
    @UuidValueConverter() UuidValue? classInstanceIdentityId,
    String? objectInstanceGraphBranchKey,
    @UuidValueConverter() UuidValue? objectInstanceGraphBranchId,
    @UuidValueListConverter()
    @Default(const [])
    List<UuidValue> requestedRoleConfigIds,
    @Default(const []) List<String> requestedRoleConfigNames,
    required int eligibleRoleCount,
    required int bindingCount,
    @Default(const [])
    List<InterfaceEnvironmentAdmissionRoleEligibilityState> eligibleRoles,
    @Default(const [])
    List<InterfaceEnvironmentAdmissionRoleBindingState> bindings,
    @Default(const []) List<String> blockers,
    String? error,
    String? reason,
    String? updatedAt,
    required Map<String, dynamic> evidence,
  }) = _InterfaceEnvironmentAdmissionState;

  factory InterfaceEnvironmentAdmissionState({
    String? status,
    String? sourceKind,
    bool? accepted,
    UuidValue? actorId,
    UuidValue? environmentId,
    UuidValue? environmentProfileId,
    UuidValue? environmentProfileActorConfigId,
    UuidValue? actorConfigId,
    UuidValue? classInstanceIdentityId,
    String? objectInstanceGraphBranchKey,
    UuidValue? objectInstanceGraphBranchId,
    List<UuidValue> requestedRoleConfigIds = const [],
    List<String> requestedRoleConfigNames = const [],
    int? eligibleRoleCount,
    int? bindingCount,
    List<InterfaceEnvironmentAdmissionRoleEligibilityState> eligibleRoles =
        const [],
    List<InterfaceEnvironmentAdmissionRoleBindingState> bindings = const [],
    List<String> blockers = const [],
    String? error,
    String? reason,
    String? updatedAt,
    Map<String, dynamic>? evidence,
  }) {
    return _InterfaceEnvironmentAdmissionState(
      status: status ?? 'inactive',
      sourceKind: sourceKind ?? 'environment_sdk_actor_admission',
      accepted: accepted ?? false,
      actorId: actorId,
      environmentId: environmentId,
      environmentProfileId: environmentProfileId,
      environmentProfileActorConfigId: environmentProfileActorConfigId,
      actorConfigId: actorConfigId,
      classInstanceIdentityId: classInstanceIdentityId,
      objectInstanceGraphBranchKey: objectInstanceGraphBranchKey,
      objectInstanceGraphBranchId: objectInstanceGraphBranchId,
      requestedRoleConfigIds: requestedRoleConfigIds,
      requestedRoleConfigNames: requestedRoleConfigNames,
      eligibleRoleCount: eligibleRoleCount ?? 0,
      bindingCount: bindingCount ?? 0,
      eligibleRoles: eligibleRoles,
      bindings: bindings,
      blockers: blockers,
      error: error,
      reason: reason,
      updatedAt: updatedAt,
      evidence: evidence ?? {},
    );
  }

  factory InterfaceEnvironmentAdmissionState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceEnvironmentAdmissionStateFromJson({
    ...json,
    if (!json.containsKey('status')) 'status': 'inactive',
    if (!json.containsKey('source_kind'))
      'source_kind': 'environment_sdk_actor_admission',
    if (!json.containsKey('accepted')) 'accepted': false,
    if (!json.containsKey('eligible_role_count')) 'eligible_role_count': 0,
    if (!json.containsKey('binding_count')) 'binding_count': 0,
    if (!json.containsKey('evidence')) 'evidence': {},
  });
}

@freezed
abstract class InterfaceEnvironmentNavigationState
    with _$InterfaceEnvironmentNavigationState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceEnvironmentNavigationState.def({
    required String status,
    required String sourceKind,
    required bool accepted,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() UuidValue? environmentSessionId,
    @UuidValueConverter() UuidValue? environmentNavigationContextId,
    String? key,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() UuidValue? rootObjectId,
    @UuidValueConverter() UuidValue? commitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    @Default(const []) List<String> blockers,
    String? error,
    String? reason,
    String? updatedAt,
    required Map<String, dynamic> evidence,
  }) = _InterfaceEnvironmentNavigationState;

  factory InterfaceEnvironmentNavigationState({
    String? status,
    String? sourceKind,
    bool? accepted,
    UuidValue? actorId,
    UuidValue? environmentId,
    UuidValue? environmentSessionId,
    UuidValue? environmentNavigationContextId,
    String? key,
    UuidValue? processId,
    UuidValue? threadId,
    UuidValue? branchId,
    String? projectionHash,
    UuidValue? rootObjectId,
    UuidValue? commitId,
    UuidValue? objectInstanceGraphCommitId,
    List<String> blockers = const [],
    String? error,
    String? reason,
    String? updatedAt,
    Map<String, dynamic>? evidence,
  }) {
    return _InterfaceEnvironmentNavigationState(
      status: status ?? 'inactive',
      sourceKind: sourceKind ?? 'environment_attention_navigation',
      accepted: accepted ?? false,
      actorId: actorId,
      environmentId: environmentId,
      environmentSessionId: environmentSessionId,
      environmentNavigationContextId: environmentNavigationContextId,
      key: key,
      processId: processId,
      threadId: threadId,
      branchId: branchId,
      projectionHash: projectionHash,
      rootObjectId: rootObjectId,
      commitId: commitId,
      objectInstanceGraphCommitId: objectInstanceGraphCommitId,
      blockers: blockers,
      error: error,
      reason: reason,
      updatedAt: updatedAt,
      evidence: evidence ?? {},
    );
  }

  factory InterfaceEnvironmentNavigationState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceEnvironmentNavigationStateFromJson({
    ...json,
    if (!json.containsKey('status')) 'status': 'inactive',
    if (!json.containsKey('source_kind'))
      'source_kind': 'environment_attention_navigation',
    if (!json.containsKey('accepted')) 'accepted': false,
    if (!json.containsKey('evidence')) 'evidence': {},
  });
}

@freezed
abstract class InterfaceEnvironmentSessionState
    with _$InterfaceEnvironmentSessionState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceEnvironmentSessionState.def({
    required String status,
    required String sourceKind,
    required bool accepted,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() UuidValue? environmentProfileId,
    @UuidValueConverter() UuidValue? environmentSessionId,
    String? environmentSessionKey,
    @UuidValueConverter() UuidValue? identitySessionId,
    @UuidValueConverter() UuidValue? identityMemberId,
    required int identityActorRoleCount,
    @Default(const []) List<String> blockers,
    String? error,
    String? reason,
    String? updatedAt,
    required Map<String, dynamic> evidence,
  }) = _InterfaceEnvironmentSessionState;

  factory InterfaceEnvironmentSessionState({
    String? status,
    String? sourceKind,
    bool? accepted,
    UuidValue? actorId,
    UuidValue? environmentId,
    UuidValue? environmentProfileId,
    UuidValue? environmentSessionId,
    String? environmentSessionKey,
    UuidValue? identitySessionId,
    UuidValue? identityMemberId,
    int? identityActorRoleCount,
    List<String> blockers = const [],
    String? error,
    String? reason,
    String? updatedAt,
    Map<String, dynamic>? evidence,
  }) {
    return _InterfaceEnvironmentSessionState(
      status: status ?? 'inactive',
      sourceKind: sourceKind ?? 'environment_session_join',
      accepted: accepted ?? false,
      actorId: actorId,
      environmentId: environmentId,
      environmentProfileId: environmentProfileId,
      environmentSessionId: environmentSessionId,
      environmentSessionKey: environmentSessionKey,
      identitySessionId: identitySessionId,
      identityMemberId: identityMemberId,
      identityActorRoleCount: identityActorRoleCount ?? 0,
      blockers: blockers,
      error: error,
      reason: reason,
      updatedAt: updatedAt,
      evidence: evidence ?? {},
    );
  }

  factory InterfaceEnvironmentSessionState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceEnvironmentSessionStateFromJson({
    ...json,
    if (!json.containsKey('status')) 'status': 'inactive',
    if (!json.containsKey('source_kind'))
      'source_kind': 'environment_session_join',
    if (!json.containsKey('accepted')) 'accepted': false,
    if (!json.containsKey('identity_actor_role_count'))
      'identity_actor_role_count': 0,
    if (!json.containsKey('evidence')) 'evidence': {},
  });
}

@freezed
abstract class InterfaceExperienceLensActionState
    with _$InterfaceExperienceLensActionState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceExperienceLensActionState.def({
    required String actionKey,
    String? actionKind,
    String? targetRef,
    String? label,
    @UuidValueConverter() required UuidValue viewInvocationActionConfigId,
    @UuidValueConverter() UuidValue? experienceInvocationActionConfigId,
    @UuidValueConverter() UuidValue? apiCapabilityEndpointId,
    @UuidValueConverter() UuidValue? sdkOperationId,
  }) = _InterfaceExperienceLensActionState;

  factory InterfaceExperienceLensActionState({
    required String actionKey,
    String? actionKind,
    String? targetRef,
    String? label,
    required UuidValue viewInvocationActionConfigId,
    UuidValue? experienceInvocationActionConfigId,
    UuidValue? apiCapabilityEndpointId,
    UuidValue? sdkOperationId,
  }) {
    return _InterfaceExperienceLensActionState(
      actionKey: actionKey,
      actionKind: actionKind,
      targetRef: targetRef,
      label: label,
      viewInvocationActionConfigId: viewInvocationActionConfigId,
      experienceInvocationActionConfigId: experienceInvocationActionConfigId,
      apiCapabilityEndpointId: apiCapabilityEndpointId,
      sdkOperationId: sdkOperationId,
    );
  }

  factory InterfaceExperienceLensActionState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceExperienceLensActionStateFromJson(json);
}

@freezed
abstract class InterfaceExperienceLensState
    with _$InterfaceExperienceLensState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceExperienceLensState.def({
    required String status,
    required String sourceKind,
    required bool accepted,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() UuidValue? environmentSessionId,
    @UuidValueConverter() UuidValue? environmentNavigationContextId,
    String? experienceName,
    String? viewRef,
    String? sectionKey,
    @UuidValueConverter() UuidValue? observableId,
    String? sectionGraphBindingKey,
    @UuidValueConverter() UuidValue? projectionExperienceViewInstanceId,
    @UuidValueConverter() UuidValue? projectionExperienceGraphIdentityId,
    @UuidValueConverter() UuidValue? objectProjectionGraphIdentityId,
    @UuidValueConverter() UuidValue? focusScopeId,
    @UuidValueConverter() UuidValue? focusId,
    required int actionCount,
    @Default(const []) List<InterfaceExperienceLensActionState> actions,
    @Default(const []) List<String> blockers,
    String? error,
    String? reason,
    String? updatedAt,
    required Map<String, dynamic> evidence,
  }) = _InterfaceExperienceLensState;

  factory InterfaceExperienceLensState({
    String? status,
    String? sourceKind,
    bool? accepted,
    UuidValue? actorId,
    UuidValue? environmentId,
    UuidValue? environmentSessionId,
    UuidValue? environmentNavigationContextId,
    String? experienceName,
    String? viewRef,
    String? sectionKey,
    UuidValue? observableId,
    String? sectionGraphBindingKey,
    UuidValue? projectionExperienceViewInstanceId,
    UuidValue? projectionExperienceGraphIdentityId,
    UuidValue? objectProjectionGraphIdentityId,
    UuidValue? focusScopeId,
    UuidValue? focusId,
    int? actionCount,
    List<InterfaceExperienceLensActionState> actions = const [],
    List<String> blockers = const [],
    String? error,
    String? reason,
    String? updatedAt,
    Map<String, dynamic>? evidence,
  }) {
    return _InterfaceExperienceLensState(
      status: status ?? 'inactive',
      sourceKind: sourceKind ?? 'experience_section_graph_binding',
      accepted: accepted ?? false,
      actorId: actorId,
      environmentId: environmentId,
      environmentSessionId: environmentSessionId,
      environmentNavigationContextId: environmentNavigationContextId,
      experienceName: experienceName,
      viewRef: viewRef,
      sectionKey: sectionKey,
      observableId: observableId,
      sectionGraphBindingKey: sectionGraphBindingKey,
      projectionExperienceViewInstanceId: projectionExperienceViewInstanceId,
      projectionExperienceGraphIdentityId: projectionExperienceGraphIdentityId,
      objectProjectionGraphIdentityId: objectProjectionGraphIdentityId,
      focusScopeId: focusScopeId,
      focusId: focusId,
      actionCount: actionCount ?? 0,
      actions: actions,
      blockers: blockers,
      error: error,
      reason: reason,
      updatedAt: updatedAt,
      evidence: evidence ?? {},
    );
  }

  factory InterfaceExperienceLensState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceExperienceLensStateFromJson({
        ...json,
        if (!json.containsKey('status')) 'status': 'inactive',
        if (!json.containsKey('source_kind'))
          'source_kind': 'experience_section_graph_binding',
        if (!json.containsKey('accepted')) 'accepted': false,
        if (!json.containsKey('action_count')) 'action_count': 0,
        if (!json.containsKey('evidence')) 'evidence': {},
      });
}

@freezed
abstract class InterfaceAppScreenState with _$InterfaceAppScreenState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceAppScreenState.def({
    required String status,
    required bool accepted,
    @UuidValueConverter() UuidValue? appPackageId,
    @UuidValueConverter() UuidValue? appPackageBranchId,
    @UuidValueConverter() UuidValue? appPackageObjectInstanceGraphCommitId,
    @UuidValueConverter() UuidValue? appConfigId,
    @UuidValueConverter() UuidValue? appConfigObjectInstanceGraphCommitId,
    @UuidValueConverter() UuidValue? appConfigScreenConfigId,
    String? screenKey,
    @UuidValueConverter() UuidValue? projectionExperienceId,
    @UuidValueConverter() UuidValue? projectionExperienceBranchId,
    @UuidValueConverter() UuidValue? projectionExperienceHeadCommitId,
    @UuidValueConverter() UuidValue? projectionExperienceLayoutGraphBindingId,
    String? experienceName,
    String? layoutBindingKey,
    @Default(const []) List<String> blockers,
    String? error,
    String? reason,
    String? updatedAt,
    required Map<String, dynamic> evidence,
  }) = _InterfaceAppScreenState;

  factory InterfaceAppScreenState({
    String? status,
    bool? accepted,
    UuidValue? appPackageId,
    UuidValue? appPackageBranchId,
    UuidValue? appPackageObjectInstanceGraphCommitId,
    UuidValue? appConfigId,
    UuidValue? appConfigObjectInstanceGraphCommitId,
    UuidValue? appConfigScreenConfigId,
    String? screenKey,
    UuidValue? projectionExperienceId,
    UuidValue? projectionExperienceBranchId,
    UuidValue? projectionExperienceHeadCommitId,
    UuidValue? projectionExperienceLayoutGraphBindingId,
    String? experienceName,
    String? layoutBindingKey,
    List<String> blockers = const [],
    String? error,
    String? reason,
    String? updatedAt,
    Map<String, dynamic>? evidence,
  }) {
    return _InterfaceAppScreenState(
      status: status ?? 'inactive',
      accepted: accepted ?? false,
      appPackageId: appPackageId,
      appPackageBranchId: appPackageBranchId,
      appPackageObjectInstanceGraphCommitId:
          appPackageObjectInstanceGraphCommitId,
      appConfigId: appConfigId,
      appConfigObjectInstanceGraphCommitId:
          appConfigObjectInstanceGraphCommitId,
      appConfigScreenConfigId: appConfigScreenConfigId,
      screenKey: screenKey,
      projectionExperienceId: projectionExperienceId,
      projectionExperienceBranchId: projectionExperienceBranchId,
      projectionExperienceHeadCommitId: projectionExperienceHeadCommitId,
      projectionExperienceLayoutGraphBindingId:
          projectionExperienceLayoutGraphBindingId,
      experienceName: experienceName,
      layoutBindingKey: layoutBindingKey,
      blockers: blockers,
      error: error,
      reason: reason,
      updatedAt: updatedAt,
      evidence: evidence ?? {},
    );
  }

  factory InterfaceAppScreenState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceAppScreenStateFromJson({
        ...json,
        if (!json.containsKey('status')) 'status': 'inactive',
        if (!json.containsKey('accepted')) 'accepted': false,
        if (!json.containsKey('evidence')) 'evidence': {},
      });
}

@freezed
abstract class InterfaceExperienceSessionNarrationEventState
    with _$InterfaceExperienceSessionNarrationEventState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceExperienceSessionNarrationEventState.def({
    @UuidValueConverter() UuidValue? commitId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @Default(const []) List<String> narrationLines,
    String? operationLabel,
    String? graphHashPost,
    @UuidValueConverter() UuidValue? objectInstanceGraphIdentityId,
    @UuidValueConverter() UuidValue? objectInstanceGraphBranchId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    @UuidValueConverter() UuidValue? projectionExperienceGraphIdentityId,
    @UuidValueConverter() UuidValue? objectProjectionGraphIdentityId,
    required Map<String, dynamic> semantics,
    required Map<String, dynamic> evidence,
  }) = _InterfaceExperienceSessionNarrationEventState;

  factory InterfaceExperienceSessionNarrationEventState({
    UuidValue? commitId,
    UuidValue? branchId,
    String? projectionHash,
    List<String> narrationLines = const [],
    String? operationLabel,
    String? graphHashPost,
    UuidValue? objectInstanceGraphIdentityId,
    UuidValue? objectInstanceGraphBranchId,
    UuidValue? objectInstanceGraphCommitId,
    UuidValue? projectionExperienceGraphIdentityId,
    UuidValue? objectProjectionGraphIdentityId,
    Map<String, dynamic>? semantics,
    Map<String, dynamic>? evidence,
  }) {
    return _InterfaceExperienceSessionNarrationEventState(
      commitId: commitId,
      branchId: branchId,
      projectionHash: projectionHash,
      narrationLines: narrationLines,
      operationLabel: operationLabel,
      graphHashPost: graphHashPost,
      objectInstanceGraphIdentityId: objectInstanceGraphIdentityId,
      objectInstanceGraphBranchId: objectInstanceGraphBranchId,
      objectInstanceGraphCommitId: objectInstanceGraphCommitId,
      projectionExperienceGraphIdentityId: projectionExperienceGraphIdentityId,
      objectProjectionGraphIdentityId: objectProjectionGraphIdentityId,
      semantics: semantics ?? {},
      evidence: evidence ?? {},
    );
  }

  factory InterfaceExperienceSessionNarrationEventState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceExperienceSessionNarrationEventStateFromJson({
    ...json,
    if (!json.containsKey('semantics')) 'semantics': {},
    if (!json.containsKey('evidence')) 'evidence': {},
  });
}

@freezed
abstract class InterfaceExperienceSessionNarrationState
    with _$InterfaceExperienceSessionNarrationState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceExperienceSessionNarrationState.def({
    required String status,
    String? featureKey,
    String? experienceName,
    String? viewRef,
    @UuidValueConverter() UuidValue? actorId,
    String? featureLeaseId,
    required int eventCount,
    @UuidValueConverter() UuidValue? lastCommitId,
    @Default(const [])
    List<InterfaceExperienceSessionNarrationEventState> events,
    String? error,
    required Map<String, dynamic> evidence,
  }) = _InterfaceExperienceSessionNarrationState;

  factory InterfaceExperienceSessionNarrationState({
    String? status,
    String? featureKey,
    String? experienceName,
    String? viewRef,
    UuidValue? actorId,
    String? featureLeaseId,
    int? eventCount,
    UuidValue? lastCommitId,
    List<InterfaceExperienceSessionNarrationEventState> events = const [],
    String? error,
    Map<String, dynamic>? evidence,
  }) {
    return _InterfaceExperienceSessionNarrationState(
      status: status ?? 'inactive',
      featureKey: featureKey,
      experienceName: experienceName,
      viewRef: viewRef,
      actorId: actorId,
      featureLeaseId: featureLeaseId,
      eventCount: eventCount ?? 0,
      lastCommitId: lastCommitId,
      events: events,
      error: error,
      evidence: evidence ?? {},
    );
  }

  factory InterfaceExperienceSessionNarrationState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceExperienceSessionNarrationStateFromJson({
    ...json,
    if (!json.containsKey('status')) 'status': 'inactive',
    if (!json.containsKey('event_count')) 'event_count': 0,
    if (!json.containsKey('evidence')) 'evidence': {},
  });
}

@freezed
abstract class InterfaceBackendState with _$InterfaceBackendState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceBackendState.def({
    required bool available,
    String? manifestPath,
    String? registryPath,
    String? databasePath,
    required bool databaseExists,
    @UuidValueConverter() UuidValue? environmentId,
    required int opgCount,
    required bool projectionBundleAvailable,
    required int projectionPlanCount,
    required int tableCount,
    String? reason,
  }) = _InterfaceBackendState;

  factory InterfaceBackendState({
    required bool available,
    String? manifestPath,
    String? registryPath,
    String? databasePath,
    required bool databaseExists,
    UuidValue? environmentId,
    required int opgCount,
    required bool projectionBundleAvailable,
    required int projectionPlanCount,
    required int tableCount,
    String? reason,
  }) {
    return _InterfaceBackendState(
      available: available,
      manifestPath: manifestPath,
      registryPath: registryPath,
      databasePath: databasePath,
      databaseExists: databaseExists,
      environmentId: environmentId,
      opgCount: opgCount,
      projectionBundleAvailable: projectionBundleAvailable,
      projectionPlanCount: projectionPlanCount,
      tableCount: tableCount,
      reason: reason,
    );
  }

  factory InterfaceBackendState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceBackendStateFromJson(json);
}

@freezed
abstract class InterfaceLocalServiceHostState
    with _$InterfaceLocalServiceHostState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceLocalServiceHostState.def({
    required bool managed,
    required bool supported,
    String? socketPath,
    required bool available,
    required bool ready,
    required String status,
    String? hostId,
    String? hostVersion,
    String? protocolVersion,
    @Default(const []) List<String> capabilities,
    String? error,
    int? probeDurationMs,
    String? lastCheckedAt,
  }) = _InterfaceLocalServiceHostState;

  factory InterfaceLocalServiceHostState({
    bool? managed,
    bool? supported,
    String? socketPath,
    bool? available,
    bool? ready,
    String? status,
    String? hostId,
    String? hostVersion,
    String? protocolVersion,
    List<String> capabilities = const [],
    String? error,
    int? probeDurationMs,
    String? lastCheckedAt,
  }) {
    return _InterfaceLocalServiceHostState(
      managed: managed ?? false,
      supported: supported ?? false,
      socketPath: socketPath,
      available: available ?? false,
      ready: ready ?? false,
      status: status ?? 'absent',
      hostId: hostId,
      hostVersion: hostVersion,
      protocolVersion: protocolVersion,
      capabilities: capabilities,
      error: error,
      probeDurationMs: probeDurationMs,
      lastCheckedAt: lastCheckedAt,
    );
  }

  factory InterfaceLocalServiceHostState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceLocalServiceHostStateFromJson({
        ...json,
        if (!json.containsKey('managed')) 'managed': false,
        if (!json.containsKey('supported')) 'supported': false,
        if (!json.containsKey('available')) 'available': false,
        if (!json.containsKey('ready')) 'ready': false,
        if (!json.containsKey('status')) 'status': 'absent',
      });
}

@freezed
abstract class InterfaceLocalNodeRuntimeState
    with _$InterfaceLocalNodeRuntimeState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceLocalNodeRuntimeState.def({
    required bool managed,
    required bool available,
    required bool ready,
    required String phase,
    String? activeTargetId,
    String? targetKey,
    String? displayName,
    String? backendKind,
    required bool isActive,
    required bool isHealthy,
    String? nodeBaseUrl,
    String? nodeWebsocketPath,
    String? summary,
    String? error,
    String? updatedAt,
    @Default(const []) List<String> recentLogLines,
    @Default(const []) List<InterfaceOperationTargetState> targetStatuses,
  }) = _InterfaceLocalNodeRuntimeState;

  factory InterfaceLocalNodeRuntimeState({
    bool? managed,
    bool? available,
    bool? ready,
    String? phase,
    String? activeTargetId,
    String? targetKey,
    String? displayName,
    String? backendKind,
    bool? isActive,
    bool? isHealthy,
    String? nodeBaseUrl,
    String? nodeWebsocketPath,
    String? summary,
    String? error,
    String? updatedAt,
    List<String> recentLogLines = const [],
    List<InterfaceOperationTargetState> targetStatuses = const [],
  }) {
    return _InterfaceLocalNodeRuntimeState(
      managed: managed ?? false,
      available: available ?? false,
      ready: ready ?? false,
      phase: phase ?? 'idle',
      activeTargetId: activeTargetId,
      targetKey: targetKey,
      displayName: displayName,
      backendKind: backendKind,
      isActive: isActive ?? false,
      isHealthy: isHealthy ?? false,
      nodeBaseUrl: nodeBaseUrl,
      nodeWebsocketPath: nodeWebsocketPath,
      summary: summary,
      error: error,
      updatedAt: updatedAt,
      recentLogLines: recentLogLines,
      targetStatuses: targetStatuses,
    );
  }

  factory InterfaceLocalNodeRuntimeState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceLocalNodeRuntimeStateFromJson({
        ...json,
        if (!json.containsKey('managed')) 'managed': false,
        if (!json.containsKey('available')) 'available': false,
        if (!json.containsKey('ready')) 'ready': false,
        if (!json.containsKey('phase')) 'phase': 'idle',
        if (!json.containsKey('is_active')) 'is_active': false,
        if (!json.containsKey('is_healthy')) 'is_healthy': false,
      });
}

@freezed
abstract class InterfaceHostedRuntimeServiceState
    with _$InterfaceHostedRuntimeServiceState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceHostedRuntimeServiceState.def({
    required String serviceName,
    @Default(const []) List<String> endpointRefs,
    @Default(const []) List<String> streamEndpointRefs,
  }) = _InterfaceHostedRuntimeServiceState;

  factory InterfaceHostedRuntimeServiceState({
    required String serviceName,
    List<String> endpointRefs = const [],
    List<String> streamEndpointRefs = const [],
  }) {
    return _InterfaceHostedRuntimeServiceState(
      serviceName: serviceName,
      endpointRefs: endpointRefs,
      streamEndpointRefs: streamEndpointRefs,
    );
  }

  factory InterfaceHostedRuntimeServiceState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceHostedRuntimeServiceStateFromJson(json);
}

@freezed
abstract class InterfaceHostedServiceRequirementState
    with _$InterfaceHostedServiceRequirementState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceHostedServiceRequirementState.def({
    required String serviceName,
    String? serviceLabel,
    required bool isRequired,
    required String status,
    required String sourceKind,
    String? summary,
    String? error,
    String? matchedRuntimeHostId,
    @Default(const []) List<String> endpointRefs,
    @Default(const []) List<String> streamEndpointRefs,
  }) = _InterfaceHostedServiceRequirementState;

  factory InterfaceHostedServiceRequirementState({
    required String serviceName,
    String? serviceLabel,
    bool? isRequired,
    String? status,
    String? sourceKind,
    String? summary,
    String? error,
    String? matchedRuntimeHostId,
    List<String> endpointRefs = const [],
    List<String> streamEndpointRefs = const [],
  }) {
    return _InterfaceHostedServiceRequirementState(
      serviceName: serviceName,
      serviceLabel: serviceLabel,
      isRequired: isRequired ?? true,
      status: status ?? 'missing',
      sourceKind: sourceKind ?? 'host_requirement',
      summary: summary,
      error: error,
      matchedRuntimeHostId: matchedRuntimeHostId,
      endpointRefs: endpointRefs,
      streamEndpointRefs: streamEndpointRefs,
    );
  }

  factory InterfaceHostedServiceRequirementState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceHostedServiceRequirementStateFromJson({
    ...json,
    if (!json.containsKey('is_required')) 'is_required': true,
    if (!json.containsKey('status')) 'status': 'missing',
    if (!json.containsKey('source_kind')) 'source_kind': 'host_requirement',
  });
}

@freezed
abstract class InterfaceHostedRuntimeState with _$InterfaceHostedRuntimeState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceHostedRuntimeState.def({
    required String hostId,
    String? hostVersion,
    String? protocolVersion,
    required String readinessStatus,
    required bool isReady,
    required bool isAlive,
    required bool supportsStreamEvents,
    String? summary,
    String? error,
    String? updatedAt,
    int? probeDurationMs,
    @Default(const []) List<InterfaceHostedRuntimeServiceState> services,
  }) = _InterfaceHostedRuntimeState;

  factory InterfaceHostedRuntimeState({
    required String hostId,
    String? hostVersion,
    String? protocolVersion,
    String? readinessStatus,
    bool? isReady,
    bool? isAlive,
    bool? supportsStreamEvents,
    String? summary,
    String? error,
    String? updatedAt,
    int? probeDurationMs,
    List<InterfaceHostedRuntimeServiceState> services = const [],
  }) {
    return _InterfaceHostedRuntimeState(
      hostId: hostId,
      hostVersion: hostVersion,
      protocolVersion: protocolVersion,
      readinessStatus: readinessStatus ?? 'unknown',
      isReady: isReady ?? false,
      isAlive: isAlive ?? false,
      supportsStreamEvents: supportsStreamEvents ?? false,
      summary: summary,
      error: error,
      updatedAt: updatedAt,
      probeDurationMs: probeDurationMs,
      services: services,
    );
  }

  factory InterfaceHostedRuntimeState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceHostedRuntimeStateFromJson({
        ...json,
        if (!json.containsKey('readiness_status'))
          'readiness_status': 'unknown',
        if (!json.containsKey('is_ready')) 'is_ready': false,
        if (!json.containsKey('is_alive')) 'is_alive': false,
        if (!json.containsKey('supports_stream_events'))
          'supports_stream_events': false,
      });
}

@freezed
abstract class InterfaceHostedServicesState
    with _$InterfaceHostedServicesState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceHostedServicesState.def({
    required bool available,
    required String sourceKind,
    String? updatedAt,
    String? error,
    int? refreshDurationMs,
    required int runtimeCount,
    required int serviceCount,
    int? requiredServiceCount,
    int? satisfiedServiceCount,
    @Default(const [])
    List<InterfaceHostedServiceRequirementState> serviceRequirements,
    @Default(const []) List<InterfaceHostedRuntimeState> runtimes,
  }) = _InterfaceHostedServicesState;

  factory InterfaceHostedServicesState({
    bool? available,
    String? sourceKind,
    String? updatedAt,
    String? error,
    int? refreshDurationMs,
    int? runtimeCount,
    int? serviceCount,
    int? requiredServiceCount,
    int? satisfiedServiceCount,
    List<InterfaceHostedServiceRequirementState> serviceRequirements = const [],
    List<InterfaceHostedRuntimeState> runtimes = const [],
  }) {
    return _InterfaceHostedServicesState(
      available: available ?? false,
      sourceKind: sourceKind ?? 'node_control_plane',
      updatedAt: updatedAt,
      error: error,
      refreshDurationMs: refreshDurationMs,
      runtimeCount: runtimeCount ?? 0,
      serviceCount: serviceCount ?? 0,
      requiredServiceCount: requiredServiceCount,
      satisfiedServiceCount: satisfiedServiceCount,
      serviceRequirements: serviceRequirements,
      runtimes: runtimes,
    );
  }

  factory InterfaceHostedServicesState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceHostedServicesStateFromJson({
        ...json,
        if (!json.containsKey('available')) 'available': false,
        if (!json.containsKey('source_kind'))
          'source_kind': 'node_control_plane',
        if (!json.containsKey('runtime_count')) 'runtime_count': 0,
        if (!json.containsKey('service_count')) 'service_count': 0,
      });
}

@freezed
abstract class InterfaceCurrentScreen with _$InterfaceCurrentScreen {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceCurrentScreen.def({
    required String screenKind,
    required String screenKey,
    required String sourceKind,
    String? title,
    String? message,
    @UuidValueConverter() UuidValue? windowId,
    @UuidValueConverter() UuidValue? sectionId,
    @UuidValueConverter() UuidValue? focusScopeId,
    @UuidValueConverter() UuidValue? focusId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionViewId,
    String? paneKey,
  }) = _InterfaceCurrentScreen;

  factory InterfaceCurrentScreen({
    required String screenKind,
    required String screenKey,
    required String sourceKind,
    String? title,
    String? message,
    UuidValue? windowId,
    UuidValue? sectionId,
    UuidValue? focusScopeId,
    UuidValue? focusId,
    UuidValue? branchId,
    String? projectionViewId,
    String? paneKey,
  }) {
    return _InterfaceCurrentScreen(
      screenKind: screenKind,
      screenKey: screenKey,
      sourceKind: sourceKind,
      title: title,
      message: message,
      windowId: windowId,
      sectionId: sectionId,
      focusScopeId: focusScopeId,
      focusId: focusId,
      branchId: branchId,
      projectionViewId: projectionViewId,
      paneKey: paneKey,
    );
  }

  factory InterfaceCurrentScreen.fromJson(Map<String, dynamic> json) =>
      _$InterfaceCurrentScreenFromJson(json);
}

@freezed
abstract class InterfaceAllowedAction with _$InterfaceAllowedAction {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceAllowedAction.def({
    required String actionKey,
    required String label,
    required bool enabled,
    String? reason,
    String? payloadSchemaHint,
  }) = _InterfaceAllowedAction;

  factory InterfaceAllowedAction({
    required String actionKey,
    required String label,
    bool? enabled,
    String? reason,
    String? payloadSchemaHint,
  }) {
    return _InterfaceAllowedAction(
      actionKey: actionKey,
      label: label,
      enabled: enabled ?? true,
      reason: reason,
      payloadSchemaHint: payloadSchemaHint,
    );
  }

  factory InterfaceAllowedAction.fromJson(Map<String, dynamic> json) =>
      _$InterfaceAllowedActionFromJson({
        ...json,
        if (!json.containsKey('enabled')) 'enabled': true,
      });
}

@freezed
abstract class InterfaceHostRecoveryCapabilityState
    with _$InterfaceHostRecoveryCapabilityState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceHostRecoveryCapabilityState.def({
    required String key,
    required String label,
    required bool enabled,
    String? reason,
    String? actionKey,
  }) = _InterfaceHostRecoveryCapabilityState;

  factory InterfaceHostRecoveryCapabilityState({
    required String key,
    required String label,
    bool? enabled,
    String? reason,
    String? actionKey,
  }) {
    return _InterfaceHostRecoveryCapabilityState(
      key: key,
      label: label,
      enabled: enabled ?? false,
      reason: reason,
      actionKey: actionKey,
    );
  }

  factory InterfaceHostRecoveryCapabilityState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceHostRecoveryCapabilityStateFromJson({
    ...json,
    if (!json.containsKey('enabled')) 'enabled': false,
  });
}

@freezed
abstract class InterfaceWorkspaceCandidate with _$InterfaceWorkspaceCandidate {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceWorkspaceCandidate.def({
    required String selectorKey,
    required String label,
    required String workspaceRoot,
    required String registrySource,
    required bool compatibilityMode,
    String? workspaceTomlPath,
    String? summary,
    required int environmentCount,
    required int apiCount,
    required int serviceCount,
    required int experienceCount,
    required int interfaceCount,
    InterfaceWorkspaceLifecycleState? lifecycle,
  }) = _InterfaceWorkspaceCandidate;

  factory InterfaceWorkspaceCandidate({
    required String selectorKey,
    required String label,
    required String workspaceRoot,
    required String registrySource,
    bool? compatibilityMode,
    String? workspaceTomlPath,
    String? summary,
    int? environmentCount,
    int? apiCount,
    int? serviceCount,
    int? experienceCount,
    int? interfaceCount,
    InterfaceWorkspaceLifecycleState? lifecycle,
  }) {
    return _InterfaceWorkspaceCandidate(
      selectorKey: selectorKey,
      label: label,
      workspaceRoot: workspaceRoot,
      registrySource: registrySource,
      compatibilityMode: compatibilityMode ?? false,
      workspaceTomlPath: workspaceTomlPath,
      summary: summary,
      environmentCount: environmentCount ?? 0,
      apiCount: apiCount ?? 0,
      serviceCount: serviceCount ?? 0,
      experienceCount: experienceCount ?? 0,
      interfaceCount: interfaceCount ?? 0,
      lifecycle: lifecycle,
    );
  }

  factory InterfaceWorkspaceCandidate.fromJson(Map<String, dynamic> json) =>
      _$InterfaceWorkspaceCandidateFromJson({
        ...json,
        if (!json.containsKey('compatibility_mode'))
          'compatibility_mode': false,
        if (!json.containsKey('environment_count')) 'environment_count': 0,
        if (!json.containsKey('api_count')) 'api_count': 0,
        if (!json.containsKey('service_count')) 'service_count': 0,
        if (!json.containsKey('experience_count')) 'experience_count': 0,
        if (!json.containsKey('interface_count')) 'interface_count': 0,
      });
}

@freezed
abstract class InterfaceWorkspaceDiscoveryState
    with _$InterfaceWorkspaceDiscoveryState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceWorkspaceDiscoveryState.def({
    required bool selectionRequired,
    String? selectedSelectorKey,
    @Default(const []) List<InterfaceWorkspaceCandidate> candidates,
    String? error,
  }) = _InterfaceWorkspaceDiscoveryState;

  factory InterfaceWorkspaceDiscoveryState({
    bool? selectionRequired,
    String? selectedSelectorKey,
    List<InterfaceWorkspaceCandidate> candidates = const [],
    String? error,
  }) {
    return _InterfaceWorkspaceDiscoveryState(
      selectionRequired: selectionRequired ?? false,
      selectedSelectorKey: selectedSelectorKey,
      candidates: candidates,
      error: error,
    );
  }

  factory InterfaceWorkspaceDiscoveryState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceWorkspaceDiscoveryStateFromJson({
    ...json,
    if (!json.containsKey('selection_required')) 'selection_required': false,
  });
}

@freezed
abstract class InterfaceSelectedWorkspaceState
    with _$InterfaceSelectedWorkspaceState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceSelectedWorkspaceState.def({
    required String selectorKey,
    required String label,
    required String workspaceRoot,
    required String registrySource,
    required bool compatibilityMode,
    String? workspaceTomlPath,
    String? summary,
    required int environmentCount,
    required int apiCount,
    required int serviceCount,
    required int experienceCount,
    required int interfaceCount,
    InterfaceWorkspaceLifecycleState? lifecycle,
    InterfaceWorkspaceSemanticSourceState? semanticSource,
  }) = _InterfaceSelectedWorkspaceState;

  factory InterfaceSelectedWorkspaceState({
    required String selectorKey,
    required String label,
    required String workspaceRoot,
    required String registrySource,
    bool? compatibilityMode,
    String? workspaceTomlPath,
    String? summary,
    int? environmentCount,
    int? apiCount,
    int? serviceCount,
    int? experienceCount,
    int? interfaceCount,
    InterfaceWorkspaceLifecycleState? lifecycle,
    InterfaceWorkspaceSemanticSourceState? semanticSource,
  }) {
    return _InterfaceSelectedWorkspaceState(
      selectorKey: selectorKey,
      label: label,
      workspaceRoot: workspaceRoot,
      registrySource: registrySource,
      compatibilityMode: compatibilityMode ?? false,
      workspaceTomlPath: workspaceTomlPath,
      summary: summary,
      environmentCount: environmentCount ?? 0,
      apiCount: apiCount ?? 0,
      serviceCount: serviceCount ?? 0,
      experienceCount: experienceCount ?? 0,
      interfaceCount: interfaceCount ?? 0,
      lifecycle: lifecycle,
      semanticSource: semanticSource,
    );
  }

  factory InterfaceSelectedWorkspaceState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceSelectedWorkspaceStateFromJson({
        ...json,
        if (!json.containsKey('compatibility_mode'))
          'compatibility_mode': false,
        if (!json.containsKey('environment_count')) 'environment_count': 0,
        if (!json.containsKey('api_count')) 'api_count': 0,
        if (!json.containsKey('service_count')) 'service_count': 0,
        if (!json.containsKey('experience_count')) 'experience_count': 0,
        if (!json.containsKey('interface_count')) 'interface_count': 0,
      });
}

@freezed
abstract class InterfaceWorkspaceLifecycleState
    with _$InterfaceWorkspaceLifecycleState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceWorkspaceLifecycleState.def({
    required String status,
    String? summary,
    String? error,
    required bool joined,
    required int attachedNamespaceCount,
    required bool joinable,
    required bool startable,
    required bool recoverable,
    required bool leaveable,
    required bool stoppable,
    String? safetyReason,
  }) = _InterfaceWorkspaceLifecycleState;

  factory InterfaceWorkspaceLifecycleState({
    String? status,
    String? summary,
    String? error,
    bool? joined,
    int? attachedNamespaceCount,
    bool? joinable,
    bool? startable,
    bool? recoverable,
    bool? leaveable,
    bool? stoppable,
    String? safetyReason,
  }) {
    return _InterfaceWorkspaceLifecycleState(
      status: status ?? 'unknown',
      summary: summary,
      error: error,
      joined: joined ?? false,
      attachedNamespaceCount: attachedNamespaceCount ?? 0,
      joinable: joinable ?? false,
      startable: startable ?? false,
      recoverable: recoverable ?? false,
      leaveable: leaveable ?? false,
      stoppable: stoppable ?? false,
      safetyReason: safetyReason,
    );
  }

  factory InterfaceWorkspaceLifecycleState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceWorkspaceLifecycleStateFromJson({
    ...json,
    if (!json.containsKey('status')) 'status': 'unknown',
    if (!json.containsKey('joined')) 'joined': false,
    if (!json.containsKey('attached_namespace_count'))
      'attached_namespace_count': 0,
    if (!json.containsKey('joinable')) 'joinable': false,
    if (!json.containsKey('startable')) 'startable': false,
    if (!json.containsKey('recoverable')) 'recoverable': false,
    if (!json.containsKey('leaveable')) 'leaveable': false,
    if (!json.containsKey('stoppable')) 'stoppable': false,
  });
}

@freezed
abstract class InterfaceWorkspaceSemanticPackageState
    with _$InterfaceWorkspaceSemanticPackageState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceWorkspaceSemanticPackageState.def({
    required String packageKind,
    required String packageName,
    required String manifestPath,
    String? workspaceRelativePath,
    String? title,
    String? fqnPrefix,
    String? objectConfigGraphId,
    String? objectConfigGraphPackageId,
    String? semanticBranchId,
  }) = _InterfaceWorkspaceSemanticPackageState;

  factory InterfaceWorkspaceSemanticPackageState({
    required String packageKind,
    required String packageName,
    required String manifestPath,
    String? workspaceRelativePath,
    String? title,
    String? fqnPrefix,
    String? objectConfigGraphId,
    String? objectConfigGraphPackageId,
    String? semanticBranchId,
  }) {
    return _InterfaceWorkspaceSemanticPackageState(
      packageKind: packageKind,
      packageName: packageName,
      manifestPath: manifestPath,
      workspaceRelativePath: workspaceRelativePath,
      title: title,
      fqnPrefix: fqnPrefix,
      objectConfigGraphId: objectConfigGraphId,
      objectConfigGraphPackageId: objectConfigGraphPackageId,
      semanticBranchId: semanticBranchId,
    );
  }

  factory InterfaceWorkspaceSemanticPackageState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceWorkspaceSemanticPackageStateFromJson(json);
}

@freezed
abstract class InterfaceWorkspaceCommittedSemanticPackageState
    with _$InterfaceWorkspaceCommittedSemanticPackageState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceWorkspaceCommittedSemanticPackageState.def({
    required String selectorKey,
    required String familyKey,
    required String familyTitle,
    required String packageKind,
    required String label,
    required String moduleName,
    required String packageName,
    required String awareTomlPath,
    required String manifestRelativePath,
    required String packageRoot,
    String? sourcesRoot,
    required String fqnPrefix,
    required String objectConfigGraphId,
    required String objectConfigGraphPackageId,
  }) = _InterfaceWorkspaceCommittedSemanticPackageState;

  factory InterfaceWorkspaceCommittedSemanticPackageState({
    required String selectorKey,
    required String familyKey,
    required String familyTitle,
    required String packageKind,
    required String label,
    required String moduleName,
    required String packageName,
    required String awareTomlPath,
    required String manifestRelativePath,
    required String packageRoot,
    String? sourcesRoot,
    required String fqnPrefix,
    required String objectConfigGraphId,
    required String objectConfigGraphPackageId,
  }) {
    return _InterfaceWorkspaceCommittedSemanticPackageState(
      selectorKey: selectorKey,
      familyKey: familyKey,
      familyTitle: familyTitle,
      packageKind: packageKind,
      label: label,
      moduleName: moduleName,
      packageName: packageName,
      awareTomlPath: awareTomlPath,
      manifestRelativePath: manifestRelativePath,
      packageRoot: packageRoot,
      sourcesRoot: sourcesRoot,
      fqnPrefix: fqnPrefix,
      objectConfigGraphId: objectConfigGraphId,
      objectConfigGraphPackageId: objectConfigGraphPackageId,
    );
  }

  factory InterfaceWorkspaceCommittedSemanticPackageState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceWorkspaceCommittedSemanticPackageStateFromJson(json);
}

@freezed
abstract class InterfaceWorkspaceCommittedSemanticPackageFamilyState
    with _$InterfaceWorkspaceCommittedSemanticPackageFamilyState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceWorkspaceCommittedSemanticPackageFamilyState.def({
    required String familyKey,
    required String title,
    @Default(const [])
    List<InterfaceWorkspaceCommittedSemanticPackageState> members,
  }) = _InterfaceWorkspaceCommittedSemanticPackageFamilyState;

  factory InterfaceWorkspaceCommittedSemanticPackageFamilyState({
    required String familyKey,
    required String title,
    List<InterfaceWorkspaceCommittedSemanticPackageState> members = const [],
  }) {
    return _InterfaceWorkspaceCommittedSemanticPackageFamilyState(
      familyKey: familyKey,
      title: title,
      members: members,
    );
  }

  factory InterfaceWorkspaceCommittedSemanticPackageFamilyState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceWorkspaceCommittedSemanticPackageFamilyStateFromJson(json);
}

@freezed
abstract class InterfaceWorkspaceMaterializationStateRef
    with _$InterfaceWorkspaceMaterializationStateRef {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceWorkspaceMaterializationStateRef.def({
    required String sourceKind,
    String? status,
    String? invocationId,
    String? receiptPath,
    String? latestPath,
    String? workspaceMaterializationId,
    String? workspaceMaterializationCommitId,
    String? workspaceMaterializationHeadCommitId,
  }) = _InterfaceWorkspaceMaterializationStateRef;

  factory InterfaceWorkspaceMaterializationStateRef({
    required String sourceKind,
    String? status,
    String? invocationId,
    String? receiptPath,
    String? latestPath,
    String? workspaceMaterializationId,
    String? workspaceMaterializationCommitId,
    String? workspaceMaterializationHeadCommitId,
  }) {
    return _InterfaceWorkspaceMaterializationStateRef(
      sourceKind: sourceKind,
      status: status,
      invocationId: invocationId,
      receiptPath: receiptPath,
      latestPath: latestPath,
      workspaceMaterializationId: workspaceMaterializationId,
      workspaceMaterializationCommitId: workspaceMaterializationCommitId,
      workspaceMaterializationHeadCommitId:
          workspaceMaterializationHeadCommitId,
    );
  }

  factory InterfaceWorkspaceMaterializationStateRef.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceWorkspaceMaterializationStateRefFromJson(json);
}

@freezed
abstract class InterfaceWorkspaceSemanticObjectConfigGraphPreviewState
    with _$InterfaceWorkspaceSemanticObjectConfigGraphPreviewState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceWorkspaceSemanticObjectConfigGraphPreviewState.def({
    required String packageKind,
    required String packageName,
    required String manifestPath,
    required String objectConfigGraphId,
    InterfaceWorkspaceMaterializationStateRef? materialization,
    required String materializeInvocationId,
    required String materializeReceiptPath,
    required String laneBranchId,
    required Map<String, dynamic> objectConfigGraph,
  }) = _InterfaceWorkspaceSemanticObjectConfigGraphPreviewState;

  factory InterfaceWorkspaceSemanticObjectConfigGraphPreviewState({
    required String packageKind,
    required String packageName,
    required String manifestPath,
    required String objectConfigGraphId,
    InterfaceWorkspaceMaterializationStateRef? materialization,
    required String materializeInvocationId,
    required String materializeReceiptPath,
    required String laneBranchId,
    required Map<String, dynamic> objectConfigGraph,
  }) {
    return _InterfaceWorkspaceSemanticObjectConfigGraphPreviewState(
      packageKind: packageKind,
      packageName: packageName,
      manifestPath: manifestPath,
      objectConfigGraphId: objectConfigGraphId,
      materialization: materialization,
      materializeInvocationId: materializeInvocationId,
      materializeReceiptPath: materializeReceiptPath,
      laneBranchId: laneBranchId,
      objectConfigGraph: objectConfigGraph,
    );
  }

  factory InterfaceWorkspaceSemanticObjectConfigGraphPreviewState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceWorkspaceSemanticObjectConfigGraphPreviewStateFromJson(json);
}

@freezed
abstract class InterfaceWorkspaceSemanticSourceState
    with _$InterfaceWorkspaceSemanticSourceState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceWorkspaceSemanticSourceState.def({
    required String sourceMode,
    String? summary,
    String? error,
    InterfaceWorkspaceMaterializationStateRef? materialization,
    String? materializeInvocationId,
    String? materializeReceiptPath,
    @Default(const [])
    List<InterfaceWorkspaceSemanticPackageState> semanticPackages,
    @Default(const [])
    List<InterfaceWorkspaceCommittedSemanticPackageState>
    committedSemanticPackages,
    @Default(const [])
    List<InterfaceWorkspaceCommittedSemanticPackageFamilyState>
    committedSemanticPackageFamilies,
    InterfaceWorkspaceSemanticObjectConfigGraphPreviewState? previewGraph,
  }) = _InterfaceWorkspaceSemanticSourceState;

  factory InterfaceWorkspaceSemanticSourceState({
    String? sourceMode,
    String? summary,
    String? error,
    InterfaceWorkspaceMaterializationStateRef? materialization,
    String? materializeInvocationId,
    String? materializeReceiptPath,
    List<InterfaceWorkspaceSemanticPackageState> semanticPackages = const [],
    List<InterfaceWorkspaceCommittedSemanticPackageState>
        committedSemanticPackages =
        const [],
    List<InterfaceWorkspaceCommittedSemanticPackageFamilyState>
        committedSemanticPackageFamilies =
        const [],
    InterfaceWorkspaceSemanticObjectConfigGraphPreviewState? previewGraph,
  }) {
    return _InterfaceWorkspaceSemanticSourceState(
      sourceMode: sourceMode ?? 'bundle_backed',
      summary: summary,
      error: error,
      materialization: materialization,
      materializeInvocationId: materializeInvocationId,
      materializeReceiptPath: materializeReceiptPath,
      semanticPackages: semanticPackages,
      committedSemanticPackages: committedSemanticPackages,
      committedSemanticPackageFamilies: committedSemanticPackageFamilies,
      previewGraph: previewGraph,
    );
  }

  factory InterfaceWorkspaceSemanticSourceState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceWorkspaceSemanticSourceStateFromJson({
    ...json,
    if (!json.containsKey('source_mode')) 'source_mode': 'bundle_backed',
  });
}

@freezed
abstract class InterfaceSelectedSemanticPackageState
    with _$InterfaceSelectedSemanticPackageState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceSelectedSemanticPackageState.def({
    required InterfaceWorkspaceCommittedSemanticPackageState package,
    required String previewStatus,
    String? summary,
    String? error,
    InterfaceWorkspaceSemanticObjectConfigGraphPreviewState? previewGraph,
  }) = _InterfaceSelectedSemanticPackageState;

  factory InterfaceSelectedSemanticPackageState({
    required InterfaceWorkspaceCommittedSemanticPackageState package,
    String? previewStatus,
    String? summary,
    String? error,
    InterfaceWorkspaceSemanticObjectConfigGraphPreviewState? previewGraph,
  }) {
    return _InterfaceSelectedSemanticPackageState(
      package: package,
      previewStatus: previewStatus ?? 'none',
      summary: summary,
      error: error,
      previewGraph: previewGraph,
    );
  }

  factory InterfaceSelectedSemanticPackageState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceSelectedSemanticPackageStateFromJson({
    ...json,
    if (!json.containsKey('preview_status')) 'preview_status': 'none',
  });
}

@freezed
abstract class InterfaceOperationTargetState
    with _$InterfaceOperationTargetState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceOperationTargetState.def({
    required String targetId,
    required String displayName,
    String? kind,
    String? endpoint,
    required String phase,
    required bool isActive,
    required bool isHealthy,
    String? summary,
    String? error,
    @Default(const []) List<String> detailLines,
  }) = _InterfaceOperationTargetState;

  factory InterfaceOperationTargetState({
    required String targetId,
    required String displayName,
    String? kind,
    String? endpoint,
    String? phase,
    bool? isActive,
    bool? isHealthy,
    String? summary,
    String? error,
    List<String> detailLines = const [],
  }) {
    return _InterfaceOperationTargetState(
      targetId: targetId,
      displayName: displayName,
      kind: kind,
      endpoint: endpoint,
      phase: phase ?? 'idle',
      isActive: isActive ?? false,
      isHealthy: isHealthy ?? false,
      summary: summary,
      error: error,
      detailLines: detailLines,
    );
  }

  factory InterfaceOperationTargetState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceOperationTargetStateFromJson({
        ...json,
        if (!json.containsKey('phase')) 'phase': 'idle',
        if (!json.containsKey('is_active')) 'is_active': false,
        if (!json.containsKey('is_healthy')) 'is_healthy': false,
      });
}

@freezed
abstract class InterfaceOperationState with _$InterfaceOperationState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceOperationState.def({
    required String operationKey,
    String? title,
    required String status,
    String? phase,
    String? currentTargetId,
    String? currentTargetTitle,
    String? summary,
    String? error,
    required bool running,
    required bool retryable,
    String? updatedAt,
    @Default(const []) List<String> recentActivity,
    @Default(const []) List<InterfaceOperationTargetState> targetStatuses,
  }) = _InterfaceOperationState;

  factory InterfaceOperationState({
    required String operationKey,
    String? title,
    required String status,
    String? phase,
    String? currentTargetId,
    String? currentTargetTitle,
    String? summary,
    String? error,
    bool? running,
    bool? retryable,
    String? updatedAt,
    List<String> recentActivity = const [],
    List<InterfaceOperationTargetState> targetStatuses = const [],
  }) {
    return _InterfaceOperationState(
      operationKey: operationKey,
      title: title,
      status: status,
      phase: phase,
      currentTargetId: currentTargetId,
      currentTargetTitle: currentTargetTitle,
      summary: summary,
      error: error,
      running: running ?? false,
      retryable: retryable ?? false,
      updatedAt: updatedAt,
      recentActivity: recentActivity,
      targetStatuses: targetStatuses,
    );
  }

  factory InterfaceOperationState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceOperationStateFromJson({
        ...json,
        if (!json.containsKey('running')) 'running': false,
        if (!json.containsKey('retryable')) 'retryable': false,
      });
}

@freezed
abstract class InterfaceControlPlaneTraceEntry
    with _$InterfaceControlPlaneTraceEntry {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneTraceEntry.def({
    String? stepId,
    required String sourceKey,
    required String sourceLabel,
    required String message,
    String? stepLabel,
  }) = _InterfaceControlPlaneTraceEntry;

  factory InterfaceControlPlaneTraceEntry({
    String? stepId,
    required String sourceKey,
    required String sourceLabel,
    required String message,
    String? stepLabel,
  }) {
    return _InterfaceControlPlaneTraceEntry(
      stepId: stepId,
      sourceKey: sourceKey,
      sourceLabel: sourceLabel,
      message: message,
      stepLabel: stepLabel,
    );
  }

  factory InterfaceControlPlaneTraceEntry.fromJson(Map<String, dynamic> json) =>
      _$InterfaceControlPlaneTraceEntryFromJson(json);
}

@freezed
abstract class InterfaceControlPlaneTraceGroup
    with _$InterfaceControlPlaneTraceGroup {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneTraceGroup.def({
    required String stepId,
    required String stepTitle,
    required String status,
    required bool current,
    required bool selected,
    @Default(const []) List<InterfaceControlPlaneTraceEntry> entries,
  }) = _InterfaceControlPlaneTraceGroup;

  factory InterfaceControlPlaneTraceGroup({
    required String stepId,
    required String stepTitle,
    required String status,
    bool? current,
    bool? selected,
    List<InterfaceControlPlaneTraceEntry> entries = const [],
  }) {
    return _InterfaceControlPlaneTraceGroup(
      stepId: stepId,
      stepTitle: stepTitle,
      status: status,
      current: current ?? false,
      selected: selected ?? false,
      entries: entries,
    );
  }

  factory InterfaceControlPlaneTraceGroup.fromJson(Map<String, dynamic> json) =>
      _$InterfaceControlPlaneTraceGroupFromJson({
        ...json,
        if (!json.containsKey('current')) 'current': false,
        if (!json.containsKey('selected')) 'selected': false,
      });
}

@freezed
abstract class InterfaceControlPlaneOrchestrationStep
    with _$InterfaceControlPlaneOrchestrationStep {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneOrchestrationStep.def({
    required String stepId,
    required String title,
    String? kind,
    required String status,
    String? phase,
    String? summary,
    required bool current,
    required bool selected,
    @Default(const []) List<InterfaceControlPlaneTraceEntry> tracePreview,
  }) = _InterfaceControlPlaneOrchestrationStep;

  factory InterfaceControlPlaneOrchestrationStep({
    required String stepId,
    required String title,
    String? kind,
    required String status,
    String? phase,
    String? summary,
    bool? current,
    bool? selected,
    List<InterfaceControlPlaneTraceEntry> tracePreview = const [],
  }) {
    return _InterfaceControlPlaneOrchestrationStep(
      stepId: stepId,
      title: title,
      kind: kind,
      status: status,
      phase: phase,
      summary: summary,
      current: current ?? false,
      selected: selected ?? false,
      tracePreview: tracePreview,
    );
  }

  factory InterfaceControlPlaneOrchestrationStep.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceControlPlaneOrchestrationStepFromJson({
    ...json,
    if (!json.containsKey('current')) 'current': false,
    if (!json.containsKey('selected')) 'selected': false,
  });
}

@freezed
abstract class InterfaceControlPlaneWorkspaceState
    with _$InterfaceControlPlaneWorkspaceState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneWorkspaceState.def({
    String? selectedStepId,
    String? currentStepId,
    @Default(const [])
    List<InterfaceControlPlaneOrchestrationStep> orchestrationSteps,
    @Default(const [])
    List<InterfaceControlPlaneTraceGroup> groupedTracePreview,
  }) = _InterfaceControlPlaneWorkspaceState;

  factory InterfaceControlPlaneWorkspaceState({
    String? selectedStepId,
    String? currentStepId,
    List<InterfaceControlPlaneOrchestrationStep> orchestrationSteps = const [],
    List<InterfaceControlPlaneTraceGroup> groupedTracePreview = const [],
  }) {
    return _InterfaceControlPlaneWorkspaceState(
      selectedStepId: selectedStepId,
      currentStepId: currentStepId,
      orchestrationSteps: orchestrationSteps,
      groupedTracePreview: groupedTracePreview,
    );
  }

  factory InterfaceControlPlaneWorkspaceState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceControlPlaneWorkspaceStateFromJson(json);
}

@freezed
abstract class InterfaceControlPlaneProfileState
    with _$InterfaceControlPlaneProfileState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneProfileState.def({
    required String profileId,
    required String title,
    required String kind,
    String? summary,
    required bool selected,
    @Default(const []) List<String> gateKeys,
    String? currentGateKey,
  }) = _InterfaceControlPlaneProfileState;

  factory InterfaceControlPlaneProfileState({
    required String profileId,
    required String title,
    required String kind,
    String? summary,
    bool? selected,
    List<String> gateKeys = const [],
    String? currentGateKey,
  }) {
    return _InterfaceControlPlaneProfileState(
      profileId: profileId,
      title: title,
      kind: kind,
      summary: summary,
      selected: selected ?? false,
      gateKeys: gateKeys,
      currentGateKey: currentGateKey,
    );
  }

  factory InterfaceControlPlaneProfileState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceControlPlaneProfileStateFromJson({
    ...json,
    if (!json.containsKey('selected')) 'selected': false,
  });
}

@freezed
abstract class InterfaceControlPlaneProfilesState
    with _$InterfaceControlPlaneProfilesState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneProfilesState.def({
    required String activeProfileId,
    @Default(const []) List<InterfaceControlPlaneProfileState> profiles,
  }) = _InterfaceControlPlaneProfilesState;

  factory InterfaceControlPlaneProfilesState({
    required String activeProfileId,
    List<InterfaceControlPlaneProfileState> profiles = const [],
  }) {
    return _InterfaceControlPlaneProfilesState(
      activeProfileId: activeProfileId,
      profiles: profiles,
    );
  }

  factory InterfaceControlPlaneProfilesState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceControlPlaneProfilesStateFromJson(json);
}

@freezed
abstract class InterfaceGateStep with _$InterfaceGateStep {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceGateStep.def({
    required String key,
    required String status,
    String? title,
    String? description,
  }) = _InterfaceGateStep;

  factory InterfaceGateStep({
    required String key,
    required String status,
    String? title,
    String? description,
  }) {
    return _InterfaceGateStep(
      key: key,
      status: status,
      title: title,
      description: description,
    );
  }

  factory InterfaceGateStep.fromJson(Map<String, dynamic> json) =>
      _$InterfaceGateStepFromJson(json);
}

@freezed
abstract class InterfaceGateState with _$InterfaceGateState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceGateState.def({
    String? destinationKey,
    String? activeStepKey,
    required bool blocked,
    @Default(const []) List<InterfaceGateStep> steps,
    String? reason,
  }) = _InterfaceGateState;

  factory InterfaceGateState({
    String? destinationKey,
    String? activeStepKey,
    bool? blocked,
    List<InterfaceGateStep> steps = const [],
    String? reason,
  }) {
    return _InterfaceGateState(
      destinationKey: destinationKey,
      activeStepKey: activeStepKey,
      blocked: blocked ?? false,
      steps: steps,
      reason: reason,
    );
  }

  factory InterfaceGateState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceGateStateFromJson({
        ...json,
        if (!json.containsKey('blocked')) 'blocked': false,
      });
}

@freezed
abstract class InterfaceResolvedView with _$InterfaceResolvedView {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceResolvedView.def({
    required String experienceKey,
    @UuidValueConverter() UuidValue? interfacePackageId,
    String? interfacePackageName,
    String? projectionViewId,
    required Map<String, dynamic> hostPayload,
  }) = _InterfaceResolvedView;

  factory InterfaceResolvedView({
    required String experienceKey,
    UuidValue? interfacePackageId,
    String? interfacePackageName,
    String? projectionViewId,
    Map<String, dynamic>? hostPayload,
  }) {
    return _InterfaceResolvedView(
      experienceKey: experienceKey,
      interfacePackageId: interfacePackageId,
      interfacePackageName: interfacePackageName,
      projectionViewId: projectionViewId,
      hostPayload: hostPayload ?? {},
    );
  }

  factory InterfaceResolvedView.fromJson(Map<String, dynamic> json) =>
      _$InterfaceResolvedViewFromJson({
        ...json,
        if (!json.containsKey('host_payload')) 'host_payload': {},
      });
}

@freezed
abstract class InterfaceRuntimeLayoutState with _$InterfaceRuntimeLayoutState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceRuntimeLayoutState.def({
    @UuidValueConverter() UuidValue? layoutConfigId,
    required String layoutKey,
    required String label,
    required bool isActive,
  }) = _InterfaceRuntimeLayoutState;

  factory InterfaceRuntimeLayoutState({
    UuidValue? layoutConfigId,
    required String layoutKey,
    required String label,
    bool? isActive,
  }) {
    return _InterfaceRuntimeLayoutState(
      layoutConfigId: layoutConfigId,
      layoutKey: layoutKey,
      label: label,
      isActive: isActive ?? false,
    );
  }

  factory InterfaceRuntimeLayoutState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceRuntimeLayoutStateFromJson({
        ...json,
        if (!json.containsKey('is_active')) 'is_active': false,
      });
}

@freezed
abstract class InterfaceAttentionFocusTargetState
    with _$InterfaceAttentionFocusTargetState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceAttentionFocusTargetState.def({
    required String kind,
    @UuidValueConverter() UuidValue? focusId,
    @UuidValueConverter() UuidValue? focusScopeId,
    @UuidValueConverter() UuidValue? projectionExperienceGraphIdentityId,
    @UuidValueConverter() required UuidValue objectProjectionGraphIdentityId,
    @UuidValueConverter() UuidValue? objectInstanceGraphBranchId,
    String? projectionHash,
    String? targetType,
    @UuidValueConverter() UuidValue? targetId,
    String? description,
  }) = _InterfaceAttentionFocusTargetState;

  factory InterfaceAttentionFocusTargetState({
    String? kind,
    UuidValue? focusId,
    UuidValue? focusScopeId,
    UuidValue? projectionExperienceGraphIdentityId,
    required UuidValue objectProjectionGraphIdentityId,
    UuidValue? objectInstanceGraphBranchId,
    String? projectionHash,
    String? targetType,
    UuidValue? targetId,
    String? description,
  }) {
    return _InterfaceAttentionFocusTargetState(
      kind: kind ?? 'constructor',
      focusId: focusId,
      focusScopeId: focusScopeId,
      projectionExperienceGraphIdentityId: projectionExperienceGraphIdentityId,
      objectProjectionGraphIdentityId: objectProjectionGraphIdentityId,
      objectInstanceGraphBranchId: objectInstanceGraphBranchId,
      projectionHash: projectionHash,
      targetType: targetType,
      targetId: targetId,
      description: description,
    );
  }

  factory InterfaceAttentionFocusTargetState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceAttentionFocusTargetStateFromJson({
    ...json,
    if (!json.containsKey('kind')) 'kind': 'constructor',
  });
}

@freezed
abstract class InterfaceRuntimeFocusState with _$InterfaceRuntimeFocusState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceRuntimeFocusState.def({
    @UuidValueConverter() UuidValue? layoutConfigId,
    String? layoutKey,
    String? sectionKey,
    @UuidValueConverter() UuidValue? layoutConfigSectionConfigId,
    @UuidValueConverter() UuidValue? layoutSectionId,
    @UuidValueConverter() UuidValue? sectionFocusScopeId,
    @UuidValueConverter() UuidValue? focusScopeId,
    @UuidValueConverter() UuidValue? focusId,
    @UuidValueConverter() UuidValue? observableId,
    InterfaceAttentionFocusTargetState? focusTarget,
  }) = _InterfaceRuntimeFocusState;

  factory InterfaceRuntimeFocusState({
    UuidValue? layoutConfigId,
    String? layoutKey,
    String? sectionKey,
    UuidValue? layoutConfigSectionConfigId,
    UuidValue? layoutSectionId,
    UuidValue? sectionFocusScopeId,
    UuidValue? focusScopeId,
    UuidValue? focusId,
    UuidValue? observableId,
    InterfaceAttentionFocusTargetState? focusTarget,
  }) {
    return _InterfaceRuntimeFocusState(
      layoutConfigId: layoutConfigId,
      layoutKey: layoutKey,
      sectionKey: sectionKey,
      layoutConfigSectionConfigId: layoutConfigSectionConfigId,
      layoutSectionId: layoutSectionId,
      sectionFocusScopeId: sectionFocusScopeId,
      focusScopeId: focusScopeId,
      focusId: focusId,
      observableId: observableId,
      focusTarget: focusTarget,
    );
  }

  factory InterfaceRuntimeFocusState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceRuntimeFocusStateFromJson(json);
}

@freezed
abstract class InterfaceRuntimeSectionRepresentationState
    with _$InterfaceRuntimeSectionRepresentationState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceRuntimeSectionRepresentationState.def({
    @UuidValueConverter() required UuidValue representationId,
    required String windowKey,
    @UuidValueConverter() UuidValue? layoutConfigId,
    required String layoutKey,
    required String sectionKey,
    @UuidValueConverter() UuidValue? layoutConfigSectionConfigId,
    required String paneName,
    required String paneKind,
    required String label,
    @UuidValueConverter() required UuidValue observableId,
    @UuidValueConverter() UuidValue? projectionExperienceGraphIdentityId,
    @UuidValueConverter() UuidValue? objectProjectionGraphIdentityId,
    String? sectionGraphBindingKey,
    required String viewRef,
    String? projectionViewKey,
    required bool isActive,
  }) = _InterfaceRuntimeSectionRepresentationState;

  factory InterfaceRuntimeSectionRepresentationState({
    required UuidValue representationId,
    required String windowKey,
    UuidValue? layoutConfigId,
    required String layoutKey,
    required String sectionKey,
    UuidValue? layoutConfigSectionConfigId,
    required String paneName,
    required String paneKind,
    required String label,
    required UuidValue observableId,
    UuidValue? projectionExperienceGraphIdentityId,
    UuidValue? objectProjectionGraphIdentityId,
    String? sectionGraphBindingKey,
    required String viewRef,
    String? projectionViewKey,
    bool? isActive,
  }) {
    return _InterfaceRuntimeSectionRepresentationState(
      representationId: representationId,
      windowKey: windowKey,
      layoutConfigId: layoutConfigId,
      layoutKey: layoutKey,
      sectionKey: sectionKey,
      layoutConfigSectionConfigId: layoutConfigSectionConfigId,
      paneName: paneName,
      paneKind: paneKind,
      label: label,
      observableId: observableId,
      projectionExperienceGraphIdentityId: projectionExperienceGraphIdentityId,
      objectProjectionGraphIdentityId: objectProjectionGraphIdentityId,
      sectionGraphBindingKey: sectionGraphBindingKey,
      viewRef: viewRef,
      projectionViewKey: projectionViewKey,
      isActive: isActive ?? false,
    );
  }

  factory InterfaceRuntimeSectionRepresentationState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceRuntimeSectionRepresentationStateFromJson({
    ...json,
    if (!json.containsKey('is_active')) 'is_active': false,
  });
}

@freezed
abstract class InterfaceResolvedPaneDescriptor
    with _$InterfaceResolvedPaneDescriptor {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceResolvedPaneDescriptor.def({
    required String windowKey,
    required String layoutKey,
    required String sectionKey,
    @UuidValueConverter() UuidValue? layoutConfigSectionConfigId,
    @UuidValueConverter() UuidValue? layoutSectionId,
    @UuidValueConverter() UuidValue? sectionFocusScopeId,
    @UuidValueConverter() UuidValue? focusScopeId,
    @UuidValueConverter() UuidValue? focusId,
    @UuidValueConverter() UuidValue? branchId,
    InterfaceAttentionFocusTargetState? focusTarget,
    required String paneKind,
    @UuidValueConverter() UuidValue? paneConfigId,
    @UuidValueConverter() UuidValue? panePackageId,
    String? panePackageName,
    @UuidValueConverter() UuidValue? objectProjectionGraphObservableId,
    @UuidValueConverter() UuidValue? projectionExperienceGraphIdentityId,
    @UuidValueConverter() UuidValue? objectProjectionGraphIdentityId,
    String? sectionGraphBindingKey,
    @UuidValueConverter() UuidValue? projectionExperienceViewId,
    String? projectionViewId,
    String? viewRef,
    String? projectionViewKey,
    @UuidValueConverter() UuidValue? stateModelId,
    String? title,
    String? summary,
    String? narrativeKey,
    required String stateSourceKind,
    String? stateProjectionHash,
    @Default(const []) List<String> actionKeys,
  }) = _InterfaceResolvedPaneDescriptor;

  factory InterfaceResolvedPaneDescriptor({
    required String windowKey,
    required String layoutKey,
    required String sectionKey,
    UuidValue? layoutConfigSectionConfigId,
    UuidValue? layoutSectionId,
    UuidValue? sectionFocusScopeId,
    UuidValue? focusScopeId,
    UuidValue? focusId,
    UuidValue? branchId,
    InterfaceAttentionFocusTargetState? focusTarget,
    required String paneKind,
    UuidValue? paneConfigId,
    UuidValue? panePackageId,
    String? panePackageName,
    UuidValue? objectProjectionGraphObservableId,
    UuidValue? projectionExperienceGraphIdentityId,
    UuidValue? objectProjectionGraphIdentityId,
    String? sectionGraphBindingKey,
    UuidValue? projectionExperienceViewId,
    String? projectionViewId,
    String? viewRef,
    String? projectionViewKey,
    UuidValue? stateModelId,
    String? title,
    String? summary,
    String? narrativeKey,
    required String stateSourceKind,
    String? stateProjectionHash,
    List<String> actionKeys = const [],
  }) {
    return _InterfaceResolvedPaneDescriptor(
      windowKey: windowKey,
      layoutKey: layoutKey,
      sectionKey: sectionKey,
      layoutConfigSectionConfigId: layoutConfigSectionConfigId,
      layoutSectionId: layoutSectionId,
      sectionFocusScopeId: sectionFocusScopeId,
      focusScopeId: focusScopeId,
      focusId: focusId,
      branchId: branchId,
      focusTarget: focusTarget,
      paneKind: paneKind,
      paneConfigId: paneConfigId,
      panePackageId: panePackageId,
      panePackageName: panePackageName,
      objectProjectionGraphObservableId: objectProjectionGraphObservableId,
      projectionExperienceGraphIdentityId: projectionExperienceGraphIdentityId,
      objectProjectionGraphIdentityId: objectProjectionGraphIdentityId,
      sectionGraphBindingKey: sectionGraphBindingKey,
      projectionExperienceViewId: projectionExperienceViewId,
      projectionViewId: projectionViewId,
      viewRef: viewRef,
      projectionViewKey: projectionViewKey,
      stateModelId: stateModelId,
      title: title,
      summary: summary,
      narrativeKey: narrativeKey,
      stateSourceKind: stateSourceKind,
      stateProjectionHash: stateProjectionHash,
      actionKeys: actionKeys,
    );
  }

  factory InterfaceResolvedPaneDescriptor.fromJson(Map<String, dynamic> json) =>
      _$InterfaceResolvedPaneDescriptorFromJson(json);
}

@freezed
abstract class InterfaceMaterializedPaneState
    with _$InterfaceMaterializedPaneState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceMaterializedPaneState.def({
    required String paneStateKey,
    required String windowKey,
    required String layoutKey,
    required String sectionKey,
    required String paneKind,
    @UuidValueConverter() UuidValue? paneConfigId,
    @UuidValueConverter() UuidValue? panePackageId,
    @UuidValueConverter() UuidValue? focusScopeId,
    @UuidValueConverter() UuidValue? branchId,
    @UuidValueConverter() UuidValue? projectionExperienceViewId,
    String? projectionViewId,
    @UuidValueConverter() UuidValue? stateModelId,
    String? projectionHash,
    required String status,
    String? headCommitId,
    String? graphHashPost,
    String? materializedAt,
    required Map<String, dynamic> state,
    required Map<String, dynamic> provenance,
    String? error,
  }) = _InterfaceMaterializedPaneState;

  factory InterfaceMaterializedPaneState({
    required String paneStateKey,
    required String windowKey,
    required String layoutKey,
    required String sectionKey,
    required String paneKind,
    UuidValue? paneConfigId,
    UuidValue? panePackageId,
    UuidValue? focusScopeId,
    UuidValue? branchId,
    UuidValue? projectionExperienceViewId,
    String? projectionViewId,
    UuidValue? stateModelId,
    String? projectionHash,
    String? status,
    String? headCommitId,
    String? graphHashPost,
    String? materializedAt,
    Map<String, dynamic>? state,
    Map<String, dynamic>? provenance,
    String? error,
  }) {
    return _InterfaceMaterializedPaneState(
      paneStateKey: paneStateKey,
      windowKey: windowKey,
      layoutKey: layoutKey,
      sectionKey: sectionKey,
      paneKind: paneKind,
      paneConfigId: paneConfigId,
      panePackageId: panePackageId,
      focusScopeId: focusScopeId,
      branchId: branchId,
      projectionExperienceViewId: projectionExperienceViewId,
      projectionViewId: projectionViewId,
      stateModelId: stateModelId,
      projectionHash: projectionHash,
      status: status ?? 'unknown',
      headCommitId: headCommitId,
      graphHashPost: graphHashPost,
      materializedAt: materializedAt,
      state: state ?? {},
      provenance: provenance ?? {},
      error: error,
    );
  }

  factory InterfaceMaterializedPaneState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceMaterializedPaneStateFromJson({
        ...json,
        if (!json.containsKey('status')) 'status': 'unknown',
        if (!json.containsKey('state')) 'state': {},
        if (!json.containsKey('provenance')) 'provenance': {},
      });
}

@freezed
abstract class InterfaceRuntimePaneRenderSpecState
    with _$InterfaceRuntimePaneRenderSpecState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceRuntimePaneRenderSpecState.def({
    required String sourceKind,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() UuidValue? lastCommitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    @UuidValueConverter() required UuidValue paneRenderSpecId,
    @UuidValueConverter() required UuidValue paneConfigId,
    String? renderSpecContentHashSha256,
    required Map<String, dynamic> payload,
  }) = _InterfaceRuntimePaneRenderSpecState;

  factory InterfaceRuntimePaneRenderSpecState({
    String? sourceKind,
    UuidValue? branchId,
    String? projectionHash,
    UuidValue? lastCommitId,
    UuidValue? objectInstanceGraphCommitId,
    required UuidValue paneRenderSpecId,
    required UuidValue paneConfigId,
    String? renderSpecContentHashSha256,
    Map<String, dynamic>? payload,
  }) {
    return _InterfaceRuntimePaneRenderSpecState(
      sourceKind: sourceKind ?? 'committed_oig',
      branchId: branchId,
      projectionHash: projectionHash,
      lastCommitId: lastCommitId,
      objectInstanceGraphCommitId: objectInstanceGraphCommitId,
      paneRenderSpecId: paneRenderSpecId,
      paneConfigId: paneConfigId,
      renderSpecContentHashSha256: renderSpecContentHashSha256,
      payload: payload ?? {},
    );
  }

  factory InterfaceRuntimePaneRenderSpecState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceRuntimePaneRenderSpecStateFromJson({
    ...json,
    if (!json.containsKey('source_kind')) 'source_kind': 'committed_oig',
    if (!json.containsKey('payload')) 'payload': {},
  });
}

@freezed
abstract class InterfaceRuntimePackageApiPackageState
    with _$InterfaceRuntimePackageApiPackageState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceRuntimePackageApiPackageState.def({
    @UuidValueConverter() UuidValue? apiPackageId,
    required String apiPackageName,
  }) = _InterfaceRuntimePackageApiPackageState;

  factory InterfaceRuntimePackageApiPackageState({
    UuidValue? apiPackageId,
    required String apiPackageName,
  }) {
    return _InterfaceRuntimePackageApiPackageState(
      apiPackageId: apiPackageId,
      apiPackageName: apiPackageName,
    );
  }

  factory InterfaceRuntimePackageApiPackageState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceRuntimePackageApiPackageStateFromJson(json);
}

@freezed
abstract class InterfaceRuntimePackageApiState
    with _$InterfaceRuntimePackageApiState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceRuntimePackageApiState.def({
    String? interfaceName,
    @UuidValueConverter() UuidValue? interfaceConfigId,
    @UuidValueConverter() UuidValue? interfaceConfigApiId,
    @UuidValueConverter() UuidValue? apiId,
    required String apiRef,
  }) = _InterfaceRuntimePackageApiState;

  factory InterfaceRuntimePackageApiState({
    String? interfaceName,
    UuidValue? interfaceConfigId,
    UuidValue? interfaceConfigApiId,
    UuidValue? apiId,
    required String apiRef,
  }) {
    return _InterfaceRuntimePackageApiState(
      interfaceName: interfaceName,
      interfaceConfigId: interfaceConfigId,
      interfaceConfigApiId: interfaceConfigApiId,
      apiId: apiId,
      apiRef: apiRef,
    );
  }

  factory InterfaceRuntimePackageApiState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceRuntimePackageApiStateFromJson(json);
}

@freezed
abstract class InterfaceRuntimePackageRenderComponentState
    with _$InterfaceRuntimePackageRenderComponentState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceRuntimePackageRenderComponentState.def({
    required String componentRef,
    String? displayName,
  }) = _InterfaceRuntimePackageRenderComponentState;

  factory InterfaceRuntimePackageRenderComponentState({
    required String componentRef,
    String? displayName,
  }) {
    return _InterfaceRuntimePackageRenderComponentState(
      componentRef: componentRef,
      displayName: displayName,
    );
  }

  factory InterfaceRuntimePackageRenderComponentState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceRuntimePackageRenderComponentStateFromJson(json);
}

@freezed
abstract class InterfaceRuntimePackageState
    with _$InterfaceRuntimePackageState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceRuntimePackageState.def({
    required String sourceKind,
    @UuidValueConverter() UuidValue? interfacePackageId,
    required String interfacePackageName,
    @Default(const []) List<String> experienceKeys,
    @Default(const []) List<InterfaceRuntimeLayoutState> layouts,
    @Default(const [])
    List<InterfaceRuntimeSectionRepresentationState> sectionRepresentations,
    @Default(const []) List<InterfaceRuntimePackageApiPackageState> apiPackages,
    @Default(const []) List<InterfaceRuntimePackageApiState> apis,
    @Default(const [])
    List<InterfaceRuntimePaneRenderSpecState> dynamicPaneRenderSpecs,
    @Default(const [])
    List<InterfaceRuntimePackageRenderComponentState> renderComponents,
    @Default(const []) List<String> warnings,
  }) = _InterfaceRuntimePackageState;

  factory InterfaceRuntimePackageState({
    String? sourceKind,
    UuidValue? interfacePackageId,
    required String interfacePackageName,
    List<String> experienceKeys = const [],
    List<InterfaceRuntimeLayoutState> layouts = const [],
    List<InterfaceRuntimeSectionRepresentationState> sectionRepresentations =
        const [],
    List<InterfaceRuntimePackageApiPackageState> apiPackages = const [],
    List<InterfaceRuntimePackageApiState> apis = const [],
    List<InterfaceRuntimePaneRenderSpecState> dynamicPaneRenderSpecs = const [],
    List<InterfaceRuntimePackageRenderComponentState> renderComponents =
        const [],
    List<String> warnings = const [],
  }) {
    return _InterfaceRuntimePackageState(
      sourceKind: sourceKind ?? 'interface_api',
      interfacePackageId: interfacePackageId,
      interfacePackageName: interfacePackageName,
      experienceKeys: experienceKeys,
      layouts: layouts,
      sectionRepresentations: sectionRepresentations,
      apiPackages: apiPackages,
      apis: apis,
      dynamicPaneRenderSpecs: dynamicPaneRenderSpecs,
      renderComponents: renderComponents,
      warnings: warnings,
    );
  }

  factory InterfaceRuntimePackageState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceRuntimePackageStateFromJson({
        ...json,
        if (!json.containsKey('source_kind')) 'source_kind': 'interface_api',
      });
}

@freezed
abstract class InterfaceWindowLayoutSectionState
    with _$InterfaceWindowLayoutSectionState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceWindowLayoutSectionState.def({
    required String sectionKey,
    @UuidValueConverter() UuidValue? layoutConfigSectionConfigId,
    @UuidValueConverter() UuidValue? layoutSectionId,
    @UuidValueConverter() UuidValue? attentionSessionSectionId,
    String? title,
    String? description,
    required int order,
    required double flex,
    int? weightMicros,
    required bool isVisible,
    required bool isCollapsed,
    String? projectionViewId,
    String? paneKey,
  }) = _InterfaceWindowLayoutSectionState;

  factory InterfaceWindowLayoutSectionState({
    required String sectionKey,
    UuidValue? layoutConfigSectionConfigId,
    UuidValue? layoutSectionId,
    UuidValue? attentionSessionSectionId,
    String? title,
    String? description,
    int? order,
    double? flex,
    int? weightMicros,
    bool? isVisible,
    bool? isCollapsed,
    String? projectionViewId,
    String? paneKey,
  }) {
    return _InterfaceWindowLayoutSectionState(
      sectionKey: sectionKey,
      layoutConfigSectionConfigId: layoutConfigSectionConfigId,
      layoutSectionId: layoutSectionId,
      attentionSessionSectionId: attentionSessionSectionId,
      title: title,
      description: description,
      order: order ?? 0,
      flex: flex ?? 1.0,
      weightMicros: weightMicros,
      isVisible: isVisible ?? true,
      isCollapsed: isCollapsed ?? false,
      projectionViewId: projectionViewId,
      paneKey: paneKey,
    );
  }

  factory InterfaceWindowLayoutSectionState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceWindowLayoutSectionStateFromJson({
    ...json,
    if (!json.containsKey('order')) 'order': 0,
    if (!json.containsKey('flex')) 'flex': 1.0,
    if (!json.containsKey('is_visible')) 'is_visible': true,
    if (!json.containsKey('is_collapsed')) 'is_collapsed': false,
  });
}

@freezed
abstract class InterfaceWindowLayoutState with _$InterfaceWindowLayoutState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceWindowLayoutState.def({
    required String sourceKind,
    required String windowKey,
    required String layoutKey,
    @UuidValueConverter() UuidValue? layoutConfigId,
    @UuidValueConverter() UuidValue? attentionSessionId,
    @UuidValueConverter() UuidValue? attentionSessionLayoutId,
    @UuidValueConverter() UuidValue? activeLayoutTransitionId,
    @UuidValueConverter() UuidValue? activeTopologyTransitionId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    String? graphHashPost,
    String? title,
    String? description,
    required String frameMode,
    String? versionHash,
    String? resolvedAt,
    required bool stale,
    @Default(const []) List<InterfaceWindowLayoutSectionState> admittedSections,
    @Default(const []) List<InterfaceWindowLayoutSectionState> sections,
  }) = _InterfaceWindowLayoutState;

  factory InterfaceWindowLayoutState({
    required String sourceKind,
    required String windowKey,
    required String layoutKey,
    UuidValue? layoutConfigId,
    UuidValue? attentionSessionId,
    UuidValue? attentionSessionLayoutId,
    UuidValue? activeLayoutTransitionId,
    UuidValue? activeTopologyTransitionId,
    UuidValue? objectInstanceGraphCommitId,
    String? graphHashPost,
    String? title,
    String? description,
    String? frameMode,
    String? versionHash,
    String? resolvedAt,
    bool? stale,
    List<InterfaceWindowLayoutSectionState> admittedSections = const [],
    List<InterfaceWindowLayoutSectionState> sections = const [],
  }) {
    return _InterfaceWindowLayoutState(
      sourceKind: sourceKind,
      windowKey: windowKey,
      layoutKey: layoutKey,
      layoutConfigId: layoutConfigId,
      attentionSessionId: attentionSessionId,
      attentionSessionLayoutId: attentionSessionLayoutId,
      activeLayoutTransitionId: activeLayoutTransitionId,
      activeTopologyTransitionId: activeTopologyTransitionId,
      objectInstanceGraphCommitId: objectInstanceGraphCommitId,
      graphHashPost: graphHashPost,
      title: title,
      description: description,
      frameMode: frameMode ?? 'vertical',
      versionHash: versionHash,
      resolvedAt: resolvedAt,
      stale: stale ?? false,
      admittedSections: admittedSections,
      sections: sections,
    );
  }

  factory InterfaceWindowLayoutState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceWindowLayoutStateFromJson({
        ...json,
        if (!json.containsKey('frame_mode')) 'frame_mode': 'vertical',
        if (!json.containsKey('stale')) 'stale': false,
      });
}

@freezed
abstract class InterfaceRuntimeWindowNavigationContextState
    with _$InterfaceRuntimeWindowNavigationContextState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceRuntimeWindowNavigationContextState.def({
    required String sourceKind,
    @UuidValueConverter() UuidValue? environmentNavigationContextId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? interfaceWindowNavigationContextId,
    @UuidValueConverter() UuidValue? interfaceEnvironmentId,
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() UuidValue? processId,
    required Map<String, dynamic> evidence,
  }) = _InterfaceRuntimeWindowNavigationContextState;

  factory InterfaceRuntimeWindowNavigationContextState({
    required String sourceKind,
    UuidValue? environmentNavigationContextId,
    UuidValue? threadId,
    UuidValue? interfaceWindowNavigationContextId,
    UuidValue? interfaceEnvironmentId,
    UuidValue? environmentId,
    UuidValue? processId,
    Map<String, dynamic>? evidence,
  }) {
    return _InterfaceRuntimeWindowNavigationContextState(
      sourceKind: sourceKind,
      environmentNavigationContextId: environmentNavigationContextId,
      threadId: threadId,
      interfaceWindowNavigationContextId: interfaceWindowNavigationContextId,
      interfaceEnvironmentId: interfaceEnvironmentId,
      environmentId: environmentId,
      processId: processId,
      evidence: evidence ?? {},
    );
  }

  factory InterfaceRuntimeWindowNavigationContextState.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceRuntimeWindowNavigationContextStateFromJson({
    ...json,
    if (!json.containsKey('evidence')) 'evidence': {},
  });
}

@freezed
abstract class InterfaceRuntimeWindowState with _$InterfaceRuntimeWindowState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceRuntimeWindowState.def({
    required String sourceKind,
    required String windowKey,
    required bool active,
    @UuidValueConverter() UuidValue? interfaceId,
    @UuidValueConverter() UuidValue? interfaceWindowId,
    @UuidValueConverter() UuidValue? windowId,
    String? title,
    InterfaceRuntimeWindowNavigationContextState? activeNavigationContext,
    @UuidValueConverter() UuidValue? activeLayoutId,
    @UuidValueConverter() UuidValue? activeLayoutConfigId,
    String? activeLayoutKey,
    String? activeLayoutSourceKind,
    String? interfaceProjectionHash,
    String? windowProjectionHash,
    String? interfaceHeadCommitId,
    String? windowHeadCommitId,
    required Map<String, dynamic> evidence,
  }) = _InterfaceRuntimeWindowState;

  factory InterfaceRuntimeWindowState({
    required String sourceKind,
    required String windowKey,
    bool? active,
    UuidValue? interfaceId,
    UuidValue? interfaceWindowId,
    UuidValue? windowId,
    String? title,
    InterfaceRuntimeWindowNavigationContextState? activeNavigationContext,
    UuidValue? activeLayoutId,
    UuidValue? activeLayoutConfigId,
    String? activeLayoutKey,
    String? activeLayoutSourceKind,
    String? interfaceProjectionHash,
    String? windowProjectionHash,
    String? interfaceHeadCommitId,
    String? windowHeadCommitId,
    Map<String, dynamic>? evidence,
  }) {
    return _InterfaceRuntimeWindowState(
      sourceKind: sourceKind,
      windowKey: windowKey,
      active: active ?? false,
      interfaceId: interfaceId,
      interfaceWindowId: interfaceWindowId,
      windowId: windowId,
      title: title,
      activeNavigationContext: activeNavigationContext,
      activeLayoutId: activeLayoutId,
      activeLayoutConfigId: activeLayoutConfigId,
      activeLayoutKey: activeLayoutKey,
      activeLayoutSourceKind: activeLayoutSourceKind,
      interfaceProjectionHash: interfaceProjectionHash,
      windowProjectionHash: windowProjectionHash,
      interfaceHeadCommitId: interfaceHeadCommitId,
      windowHeadCommitId: windowHeadCommitId,
      evidence: evidence ?? {},
    );
  }

  factory InterfaceRuntimeWindowState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceRuntimeWindowStateFromJson({
        ...json,
        if (!json.containsKey('active')) 'active': false,
        if (!json.containsKey('evidence')) 'evidence': {},
      });
}

@freezed
abstract class InterfaceRuntimeState with _$InterfaceRuntimeState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceRuntimeState.def({
    required InterfaceBackendState backend,
    InterfaceGateState? gateState,
    InterfaceResolvedView? resolvedView,
    InterfaceWindowLayoutState? windowLayout,
    InterfaceRuntimeWindowState? activeWindow,
    @Default(const []) List<InterfaceRuntimeWindowState> windows,
    @UuidValueConverter() UuidValue? activeLayoutConfigId,
    @Default(const []) List<InterfaceRuntimeLayoutState> layoutStates,
    InterfaceRuntimeFocusState? activeFocus,
    InterfaceRuntimePackageState? interfacePackageRuntime,
    @Default(const [])
    List<InterfaceRuntimeSectionRepresentationState> sectionRepresentations,
    @Default(const []) List<InterfaceResolvedPaneDescriptor> resolvedPanes,
    InterfaceHostViewStateCursorState? viewStateCursor,
    @Default(const [])
    List<InterfaceMaterializedPaneState> materializedPaneStates,
    @Default(const [])
    List<InterfaceRuntimePaneRenderSpecState> dynamicPaneRenderSpecs,
    @Default(const []) List<String> warnings,
  }) = _InterfaceRuntimeState;

  factory InterfaceRuntimeState({
    required InterfaceBackendState backend,
    InterfaceGateState? gateState,
    InterfaceResolvedView? resolvedView,
    InterfaceWindowLayoutState? windowLayout,
    InterfaceRuntimeWindowState? activeWindow,
    List<InterfaceRuntimeWindowState> windows = const [],
    UuidValue? activeLayoutConfigId,
    List<InterfaceRuntimeLayoutState> layoutStates = const [],
    InterfaceRuntimeFocusState? activeFocus,
    InterfaceRuntimePackageState? interfacePackageRuntime,
    List<InterfaceRuntimeSectionRepresentationState> sectionRepresentations =
        const [],
    List<InterfaceResolvedPaneDescriptor> resolvedPanes = const [],
    InterfaceHostViewStateCursorState? viewStateCursor,
    List<InterfaceMaterializedPaneState> materializedPaneStates = const [],
    List<InterfaceRuntimePaneRenderSpecState> dynamicPaneRenderSpecs = const [],
    List<String> warnings = const [],
  }) {
    return _InterfaceRuntimeState(
      backend: backend,
      gateState: gateState,
      resolvedView: resolvedView,
      windowLayout: windowLayout,
      activeWindow: activeWindow,
      windows: windows,
      activeLayoutConfigId: activeLayoutConfigId,
      layoutStates: layoutStates,
      activeFocus: activeFocus,
      interfacePackageRuntime: interfacePackageRuntime,
      sectionRepresentations: sectionRepresentations,
      resolvedPanes: resolvedPanes,
      viewStateCursor: viewStateCursor,
      materializedPaneStates: materializedPaneStates,
      dynamicPaneRenderSpecs: dynamicPaneRenderSpecs,
      warnings: warnings,
    );
  }

  factory InterfaceRuntimeState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceRuntimeStateFromJson(json);
}

@freezed
abstract class InterfaceHostState with _$InterfaceHostState {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceHostState.def({
    required String hostLabel,
    required String namespace,
    String? endpoint,
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() UuidValue? environmentConfigId,
    required bool started,
    required InterfaceTransportState transport,
    InterfaceRendererCapabilitiesState? rendererCapabilities,
    InterfaceLocalServiceHostState? localServiceHost,
    InterfaceLocalNodeRuntimeState? localNodeRuntime,
    InterfaceHostedServicesState? hostedServices,
    InterfaceLaneSyncState? laneSync,
    InterfaceEnvironmentAdmissionState? environmentAdmission,
    InterfaceEnvironmentSessionState? environmentSession,
    InterfaceEnvironmentNavigationState? environmentNavigation,
    EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt,
    EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt,
    InterfaceExperienceLensState? experienceLens,
    InterfaceAppScreenState? appScreen,
    InterfaceExperienceSessionNarrationState? experienceSessionNarration,
    InterfaceRuntimeState? runtime,
    InterfaceControlPlaneProfilesState? controlPlaneProfiles,
    InterfaceControlPlaneWorkspaceState? controlPlaneWorkspace,
    InterfaceWorkspaceDiscoveryState? workspaceDiscovery,
    InterfaceSelectedWorkspaceState? selectedWorkspace,
    InterfaceSelectedSemanticPackageState? selectedSemanticPackage,
    InterfaceCurrentScreen? currentScreen,
    InterfaceOperationState? currentOperation,
    @Default(const []) List<InterfaceAllowedAction> allowedActions,
    @Default(const [])
    List<InterfaceHostRecoveryCapabilityState> recoveryCapabilities,
    @Default(const []) List<String> warnings,
  }) = _InterfaceHostState;

  factory InterfaceHostState({
    required String hostLabel,
    required String namespace,
    String? endpoint,
    UuidValue? environmentId,
    UuidValue? environmentConfigId,
    required bool started,
    required InterfaceTransportState transport,
    InterfaceRendererCapabilitiesState? rendererCapabilities,
    InterfaceLocalServiceHostState? localServiceHost,
    InterfaceLocalNodeRuntimeState? localNodeRuntime,
    InterfaceHostedServicesState? hostedServices,
    InterfaceLaneSyncState? laneSync,
    InterfaceEnvironmentAdmissionState? environmentAdmission,
    InterfaceEnvironmentSessionState? environmentSession,
    InterfaceEnvironmentNavigationState? environmentNavigation,
    EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt,
    EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt,
    InterfaceExperienceLensState? experienceLens,
    InterfaceAppScreenState? appScreen,
    InterfaceExperienceSessionNarrationState? experienceSessionNarration,
    InterfaceRuntimeState? runtime,
    InterfaceControlPlaneProfilesState? controlPlaneProfiles,
    InterfaceControlPlaneWorkspaceState? controlPlaneWorkspace,
    InterfaceWorkspaceDiscoveryState? workspaceDiscovery,
    InterfaceSelectedWorkspaceState? selectedWorkspace,
    InterfaceSelectedSemanticPackageState? selectedSemanticPackage,
    InterfaceCurrentScreen? currentScreen,
    InterfaceOperationState? currentOperation,
    List<InterfaceAllowedAction> allowedActions = const [],
    List<InterfaceHostRecoveryCapabilityState> recoveryCapabilities = const [],
    List<String> warnings = const [],
  }) {
    return _InterfaceHostState(
      hostLabel: hostLabel,
      namespace: namespace,
      endpoint: endpoint,
      environmentId: environmentId,
      environmentConfigId: environmentConfigId,
      started: started,
      transport: transport,
      rendererCapabilities: rendererCapabilities,
      localServiceHost: localServiceHost,
      localNodeRuntime: localNodeRuntime,
      hostedServices: hostedServices,
      laneSync: laneSync,
      environmentAdmission: environmentAdmission,
      environmentSession: environmentSession,
      environmentNavigation: environmentNavigation,
      environmentAdmissionReceipt: environmentAdmissionReceipt,
      environmentSessionJoinReceipt: environmentSessionJoinReceipt,
      experienceLens: experienceLens,
      appScreen: appScreen,
      experienceSessionNarration: experienceSessionNarration,
      runtime: runtime,
      controlPlaneProfiles: controlPlaneProfiles,
      controlPlaneWorkspace: controlPlaneWorkspace,
      workspaceDiscovery: workspaceDiscovery,
      selectedWorkspace: selectedWorkspace,
      selectedSemanticPackage: selectedSemanticPackage,
      currentScreen: currentScreen,
      currentOperation: currentOperation,
      allowedActions: allowedActions,
      recoveryCapabilities: recoveryCapabilities,
      warnings: warnings,
    );
  }

  factory InterfaceHostState.fromJson(Map<String, dynamic> json) =>
      _$InterfaceHostStateFromJson(json);
}
