// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import '../../environment/environment_model.dart';
import '../../experience/actor_admission/models_model.dart';
import 'hosted_interface_namespace_model.dart';
import 'interface_host_state_model.dart';
import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'control_plane_model.freezed.dart';
part 'control_plane_model.g.dart';

/// Canonical local control-plane DTOs for the Interface daemon.
/// This package is local-machine scoped:
/// - not a remote API rail
/// - not graph/ORM SSOT
/// - generated from `.aware` so `services/interface`, textual clients, and
/// future CLI clients share one request/response vocabulary
@freezed
abstract class InterfaceControlPlaneOperation
    with _$InterfaceControlPlaneOperation {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneOperation.def({
    InterfaceControlPlaneRequest? request,
    InterfaceControlPlaneResponse? response,
    InterfaceControlPlaneNotification? notification,
  }) = _InterfaceControlPlaneOperation;

  factory InterfaceControlPlaneOperation({
    InterfaceControlPlaneRequest? request,
    InterfaceControlPlaneResponse? response,
    InterfaceControlPlaneNotification? notification,
  }) {
    return _InterfaceControlPlaneOperation(
      request: request,
      response: response,
      notification: notification,
    );
  }

  factory InterfaceControlPlaneOperation.fromJson(Map<String, dynamic> json) =>
      _$InterfaceControlPlaneOperationFromJson(json);
}

@Freezed(unionKey: 'operation')
abstract class InterfaceControlPlaneRequest
    with _$InterfaceControlPlaneRequest {
  @FreezedUnionValue('ping')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.ping({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
  }) = PingRequest;

  @FreezedUnionValue('namespace_ensure')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.namespaceEnsure({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    String? hostLabel,
    String? endpoint,
    String? authToken,
    @UuidValueConverter() UuidValue? environmentConfigId,
    @UuidValueConverter() UuidValue? interfacePackageId,
    String? interfacePackageName,
  }) = NamespaceEnsureRequest;

  @FreezedUnionValue('namespace_list')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.namespaceList({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
  }) = NamespaceListRequest;

  @FreezedUnionValue('interface_status')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceStatus({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
  }) = InterfaceStatusRequest;

  @FreezedUnionValue('interface_admit_environment_actor')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceAdmitEnvironmentActor({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() required UuidValue environmentProfileId,
    @UuidValueConverter() required UuidValue actorConfigId,
    @UuidValueConverter() required UuidValue classInstanceIdentityId,
    required String objectInstanceGraphBranchKey,
    @UuidValueConverter() UuidValue? objectInstanceGraphBranchId,
    @UuidValueListConverter()
    @Default(const [])
    List<UuidValue> requestedRoleConfigIds,
    @Default(const []) List<String> requestedRoleConfigNames,
    String? reason,
    required Map<String, dynamic> evidence,
  }) = InterfaceAdmitEnvironmentActorRequest;

  @FreezedUnionValue('interface_join_environment_session')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceJoinEnvironmentSession({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    @UuidValueConverter() required UuidValue environmentSessionId,
    @UuidValueConverter() UuidValue? environmentProfileId,
    EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt,
    String? reason,
    required Map<String, dynamic> evidence,
  }) = InterfaceJoinEnvironmentSessionRequest;

  @FreezedUnionValue('interface_select_environment_navigation_target')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceSelectEnvironmentNavigationTarget({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    @UuidValueConverter() UuidValue? environmentNavigationContextId,
    @UuidValueConverter() UuidValue? selectedProcessId,
    @UuidValueConverter() UuidValue? selectedThreadId,
    String? reason,
    required Map<String, dynamic> evidence,
  }) = InterfaceSelectEnvironmentNavigationTargetRequest;

  @FreezedUnionValue('interface_enter_environment')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceEnterEnvironment({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() UuidValue? environmentProfileId,
    @UuidValueConverter() UuidValue? actorConfigId,
    @UuidValueConverter() UuidValue? classInstanceIdentityId,
    required String objectInstanceGraphBranchKey,
    @UuidValueConverter() UuidValue? objectInstanceGraphBranchId,
    @UuidValueListConverter()
    @Default(const [])
    List<UuidValue> requestedRoleConfigIds,
    @Default(const []) List<String> requestedRoleConfigNames,
    EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt,
    @UuidValueConverter() UuidValue? environmentSessionId,
    @UuidValueConverter() UuidValue? environmentSessionConfigId,
    String? sessionKey,
    String? title,
    String? description,
    String? purpose,
    String? sourceKind,
    String? sourceRef,
    String? reason,
    required Map<String, dynamic> evidence,
  }) = InterfaceEnterEnvironmentRequest;

  @FreezedUnionValue('interface_resolve_experience_lens')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceResolveExperienceLens({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt,
    EnvironmentNavigationContextView? environmentNavigationContext,
    ExperienceActorConfigAdmissionReceipt? experienceActorAdmission,
    @UuidValueConverter() UuidValue? experienceIdentitySessionConfigId,
    String? reason,
    required Map<String, dynamic> evidence,
  }) = InterfaceResolveExperienceLensRequest;

  @FreezedUnionValue('interface_action')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceAction({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    String? paneRef,
    required String actionKey,
    String? actionKind,
    String? operationRef,
    String? sdkOperationId,
    String? paneConfigSdkOperationId,
    String? endpointRef,
    String? apiCapabilityEndpointId,
    String? paneConfigApiCapabilityEndpointId,
    required Map<String, dynamic> payload,
  }) = InterfaceActionRequest;

  @FreezedUnionValue('interface_select_step')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceSelectStep({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    String? stepId,
  }) = InterfaceSelectStepRequest;

  @FreezedUnionValue('interface_select_profile')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceSelectProfile({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    required String profileId,
  }) = InterfaceSelectProfileRequest;

  @FreezedUnionValue('interface_select_runtime_layout')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceSelectRuntimeLayout({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    @UuidValueConverter() UuidValue? layoutConfigId,
  }) = InterfaceSelectRuntimeLayoutRequest;

  @FreezedUnionValue('interface_activate_runtime_focus')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceActivateRuntimeFocus({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    @UuidValueConverter() UuidValue? representationId,
  }) = InterfaceActivateRuntimeFocusRequest;

  @FreezedUnionValue('interface_request_window_layout')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceRequestWindowLayout({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    @UuidValueConverter() UuidValue? interfacePackageId,
    String? interfacePackageName,
    String? windowKey,
    @UuidValueConverter() UuidValue? layoutConfigId,
    String? layoutKey,
    String? sectionKey,
    @UuidValueConverter() UuidValue? observableId,
    @UuidValueConverter() UuidValue? representationId,
    String? requestedByService,
    String? requestedByOperation,
    String? reason,
    String? idempotencyKey,
  }) = InterfaceRequestWindowLayoutRequest;

  @FreezedUnionValue('interface_apply_attention_layout_transition')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceApplyAttentionLayoutTransition({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    required String clientIntentId,
    @UuidValueConverter() UuidValue? expectedPreviousLayoutTransitionId,
    @UuidValueConverter() UuidValue? topologyTransitionId,
    @Default(const [])
    List<InterfaceAttentionLayoutTransitionSectionIntent> sectionStates,
  }) = InterfaceApplyAttentionLayoutTransitionRequest;

  @FreezedUnionValue('interface_apply_attention_layout_topology_transition')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceApplyAttentionLayoutTopologyTransition({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    required String clientIntentId,
    @UuidValueConverter() UuidValue? expectedPreviousTopologyTransitionId,
    @Default(const [])
    List<InterfaceAttentionLayoutTopologyTransitionSectionIntent> sectionStates,
  }) = InterfaceApplyAttentionLayoutTopologyTransitionRequest;

  @FreezedUnionValue('interface_report_renderer_capabilities')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceReportRendererCapabilities({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    required InterfaceRendererCapabilitiesState rendererCapabilities,
  }) = InterfaceReportRendererCapabilitiesRequest;

  @FreezedUnionValue('interface_sync_view_state_cursor')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceSyncViewStateCursor({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    String? rendererId,
    String? knownCursor,
    String? knownDigest,
  }) = InterfaceSyncViewStateCursorRequest;

  @FreezedUnionValue('interface_follow')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceFollow({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    required int pollIntervalMs,
  }) = InterfaceFollowRequest;

  @FreezedUnionValue('interface_invoke_api')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceInvokeApi({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    required String endpointRef,
    required String discriminant,
    required Map<String, dynamic> requestPayload,
  }) = InterfaceInvokeApiRequest;

  @FreezedUnionValue('interface_stream_api')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceStreamApi({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    required String endpointRef,
    required String discriminant,
    required Map<String, dynamic> requestPayload,
  }) = InterfaceStreamApiRequest;

  @FreezedUnionValue('interface_stop')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneRequest.interfaceStop({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
  }) = InterfaceStopRequest;

  factory InterfaceControlPlaneRequest.fromJson(Map<String, dynamic> json) =>
      _$InterfaceControlPlaneRequestFromJson(json);
}

@Freezed(unionKey: 'operation')
abstract class InterfaceControlPlaneResponse
    with _$InterfaceControlPlaneResponse {
  @FreezedUnionValue('ping')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.ping({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String service,
    required String status,
    String? socketPath,
    @UuidValueConverter() UuidValue? daemonInstanceId,
    String? daemonStartedAt,
    String? daemonSourceFingerprint,
    String? repositoryRoot,
    String? stateHome,
    String? defaultEndpoint,
    String? expectedSourceFingerprint,
    required bool restartRecommended,
    String? restartReason,
    @Default(const []) List<HostedInterfaceNamespace> namespaces,
  }) = PingResponse;

  @FreezedUnionValue('namespace_ensure')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.namespaceEnsure({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    required InterfaceHostState hostState,
  }) = NamespaceEnsureResponse;

  @FreezedUnionValue('namespace_list')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.namespaceList({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    @Default(const []) List<HostedInterfaceNamespace> namespaces,
  }) = NamespaceListResponse;

  @FreezedUnionValue('interface_status')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceStatus({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    required InterfaceHostState hostState,
  }) = InterfaceStatusResponse;

  @FreezedUnionValue('interface_admit_environment_actor')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceAdmitEnvironmentActor({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    InterfaceEnvironmentAdmissionState? environmentAdmission,
    EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt,
    required InterfaceHostState hostState,
  }) = InterfaceAdmitEnvironmentActorResponse;

  @FreezedUnionValue('interface_join_environment_session')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceJoinEnvironmentSession({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    EnvironmentSessionView? environmentSession,
    EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt,
    EnvironmentNavigationContextView? environmentNavigationContext,
    EnvironmentNavigationCommitReceipt? defaultNavigationReceipt,
    InterfaceEnvironmentSessionState? environmentSessionState,
    InterfaceEnvironmentNavigationState? environmentNavigationState,
    required InterfaceHostState hostState,
  }) = InterfaceJoinEnvironmentSessionResponse;

  @FreezedUnionValue('interface_select_environment_navigation_target')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceSelectEnvironmentNavigationTarget({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    EnvironmentNavigationContextView? environmentNavigationContext,
    EnvironmentNavigationCommitReceipt? environmentNavigationReceipt,
    InterfaceEnvironmentNavigationState? environmentNavigationState,
    required InterfaceHostState hostState,
  }) = InterfaceSelectEnvironmentNavigationTargetResponse;

  @FreezedUnionValue('interface_enter_environment')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceEnterEnvironment({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    InterfaceEnvironmentAdmissionState? environmentAdmission,
    EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt,
    EnvironmentSessionView? environmentSession,
    EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt,
    EnvironmentNavigationContextView? environmentNavigationContext,
    EnvironmentNavigationCommitReceipt? defaultNavigationReceipt,
    InterfaceEnvironmentSessionState? environmentSessionState,
    InterfaceEnvironmentNavigationState? environmentNavigationState,
    required InterfaceHostState hostState,
  }) = InterfaceEnterEnvironmentResponse;

  @FreezedUnionValue('interface_resolve_experience_lens')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceResolveExperienceLens({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    InterfaceEnvironmentSessionState? environmentSession,
    InterfaceEnvironmentNavigationState? environmentNavigation,
    InterfaceExperienceLensState? experienceLens,
    required InterfaceHostState hostState,
  }) = InterfaceResolveExperienceLensResponse;

  @FreezedUnionValue('interface_action')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceAction({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    String? paneRef,
    required String actionKey,
    required InterfaceHostState hostState,
  }) = InterfaceActionResponse;

  @FreezedUnionValue('interface_select_step')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceSelectStep({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    String? stepId,
    required InterfaceHostState hostState,
  }) = InterfaceSelectStepResponse;

  @FreezedUnionValue('interface_select_profile')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceSelectProfile({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    required String profileId,
    required InterfaceHostState hostState,
  }) = InterfaceSelectProfileResponse;

  @FreezedUnionValue('interface_select_runtime_layout')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceSelectRuntimeLayout({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    @UuidValueConverter() UuidValue? layoutConfigId,
    required InterfaceHostState hostState,
  }) = InterfaceSelectRuntimeLayoutResponse;

  @FreezedUnionValue('interface_activate_runtime_focus')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceActivateRuntimeFocus({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    @UuidValueConverter() UuidValue? representationId,
    @UuidValueConverter() UuidValue? layoutConfigId,
    required InterfaceHostState hostState,
  }) = InterfaceActivateRuntimeFocusResponse;

  @FreezedUnionValue('interface_request_window_layout')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceRequestWindowLayout({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    @UuidValueConverter() UuidValue? interfacePackageId,
    String? interfacePackageName,
    String? windowKey,
    @UuidValueConverter() UuidValue? layoutConfigId,
    String? layoutKey,
    String? sectionKey,
    @UuidValueConverter() UuidValue? observableId,
    @UuidValueConverter() UuidValue? representationId,
    String? requestedByService,
    String? requestedByOperation,
    String? reason,
    String? idempotencyKey,
    required InterfaceHostState hostState,
  }) = InterfaceRequestWindowLayoutResponse;

  @FreezedUnionValue('interface_apply_attention_layout_transition')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceApplyAttentionLayoutTransition({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    required String outcome,
    String? conflictReason,
    @UuidValueConverter() UuidValue? activeLayoutTransitionId,
    @UuidValueConverter() UuidValue? activeTopologyTransitionId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    String? graphHashPost,
    required InterfaceHostState hostState,
  }) = InterfaceApplyAttentionLayoutTransitionResponse;

  @FreezedUnionValue('interface_apply_attention_layout_topology_transition')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceApplyAttentionLayoutTopologyTransition({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    required String outcome,
    String? conflictReason,
    @UuidValueConverter() UuidValue? activeTopologyTransitionId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    String? graphHashPost,
    required InterfaceHostState hostState,
  }) = InterfaceApplyAttentionLayoutTopologyTransitionResponse;

  @FreezedUnionValue('interface_report_renderer_capabilities')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceReportRendererCapabilities({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    required InterfaceHostState hostState,
  }) = InterfaceReportRendererCapabilitiesResponse;

  @FreezedUnionValue('interface_sync_view_state_cursor')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceSyncViewStateCursor({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    required bool changed,
    InterfaceHostViewStateCursorState? viewStateCursor,
    required InterfaceHostState hostState,
  }) = InterfaceSyncViewStateCursorResponse;

  @FreezedUnionValue('interface_follow')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceFollow({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    required InterfaceHostState hostState,
  }) = InterfaceFollowResponse;

  @FreezedUnionValue('interface_invoke_api')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceInvokeApi({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    required String endpointRef,
    required String discriminant,
    String? serviceStatus,
    Object? responsePayload,
  }) = InterfaceInvokeApiResponse;

  @FreezedUnionValue('interface_stream_api')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceStreamApi({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    required String endpointRef,
    required String discriminant,
  }) = InterfaceStreamApiResponse;

  @FreezedUnionValue('interface_stop')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneResponse.interfaceStop({
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    required HostedInterfaceNamespace hostedNamespace,
  }) = InterfaceStopResponse;

  factory InterfaceControlPlaneResponse.fromJson(Map<String, dynamic> json) =>
      _$InterfaceControlPlaneResponseFromJson(json);
}

@Freezed(unionKey: 'operation')
abstract class InterfaceControlPlaneNotification
    with _$InterfaceControlPlaneNotification {
  @FreezedUnionValue('interface_state')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneNotification.interfaceState({
    @UuidValueConverter() UuidValue? notificationId,
    required int protocolVersion,
    required String namespace,
    required InterfaceHostState hostState,
  }) = InterfaceStateNotification;

  @FreezedUnionValue('interface_api_event')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneNotification.interfaceApiEvent({
    @UuidValueConverter() UuidValue? notificationId,
    required int protocolVersion,
    required String namespace,
    required String endpointRef,
    required String discriminant,
    required String eventKind,
    required int sequence,
    required String itemKey,
    Object? payload,
  }) = InterfaceApiEventNotification;

  @FreezedUnionValue('interface_api_stream_closed')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceControlPlaneNotification.interfaceApiStreamClosed({
    @UuidValueConverter() UuidValue? notificationId,
    required int protocolVersion,
    required String namespace,
    required String endpointRef,
    required String discriminant,
    String? serviceStatus,
    Object? responsePayload,
    String? error,
  }) = InterfaceApiStreamClosedNotification;

  factory InterfaceControlPlaneNotification.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceControlPlaneNotificationFromJson(json);
}

@freezed
abstract class InterfaceSessionStartRequest
    with _$InterfaceSessionStartRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceSessionStartRequest.def({
    required String operation,
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    @UuidValueConverter() required UuidValue interfaceId,
    @UuidValueConverter() required UuidValue identitySessionId,
    required String name,
    required String state,
  }) = _InterfaceSessionStartRequest;

  factory InterfaceSessionStartRequest({
    String? operation,
    UuidValue? requestId,
    int? protocolVersion,
    required UuidValue interfaceId,
    required UuidValue identitySessionId,
    required String name,
    String? state,
  }) {
    return _InterfaceSessionStartRequest(
      operation: operation ?? 'interface_session_start',
      requestId: requestId,
      protocolVersion: protocolVersion ?? 1,
      interfaceId: interfaceId,
      identitySessionId: identitySessionId,
      name: name,
      state: state ?? 'active',
    );
  }

  factory InterfaceSessionStartRequest.fromJson(Map<String, dynamic> json) =>
      _$InterfaceSessionStartRequestFromJson({
        ...json,
        if (!json.containsKey('operation'))
          'operation': 'interface_session_start',
        if (!json.containsKey('protocol_version')) 'protocol_version': 1,
        if (!json.containsKey('state')) 'state': 'active',
      });
}

@freezed
abstract class InterfaceSessionStartResponse
    with _$InterfaceSessionStartResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceSessionStartResponse.def({
    required String operation,
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    @UuidValueConverter() UuidValue? interfaceSessionId,
    @UuidValueConverter() required UuidValue interfaceId,
    @UuidValueConverter() required UuidValue identitySessionId,
    required String name,
    required String state,
    @UuidValueConverter() UuidValue? domainCommitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    String? graphHashPost,
  }) = _InterfaceSessionStartResponse;

  factory InterfaceSessionStartResponse({
    String? operation,
    UuidValue? requestId,
    int? protocolVersion,
    bool? success,
    String? error,
    UuidValue? interfaceSessionId,
    required UuidValue interfaceId,
    required UuidValue identitySessionId,
    required String name,
    required String state,
    UuidValue? domainCommitId,
    UuidValue? objectInstanceGraphCommitId,
    String? graphHashPost,
  }) {
    return _InterfaceSessionStartResponse(
      operation: operation ?? 'interface_session_start',
      requestId: requestId,
      protocolVersion: protocolVersion ?? 1,
      success: success ?? true,
      error: error,
      interfaceSessionId: interfaceSessionId,
      interfaceId: interfaceId,
      identitySessionId: identitySessionId,
      name: name,
      state: state,
      domainCommitId: domainCommitId,
      objectInstanceGraphCommitId: objectInstanceGraphCommitId,
      graphHashPost: graphHashPost,
    );
  }

  factory InterfaceSessionStartResponse.fromJson(Map<String, dynamic> json) =>
      _$InterfaceSessionStartResponseFromJson({
        ...json,
        if (!json.containsKey('operation'))
          'operation': 'interface_session_start',
        if (!json.containsKey('protocol_version')) 'protocol_version': 1,
        if (!json.containsKey('success')) 'success': true,
      });
}

@freezed
abstract class InterfaceSessionDescribeRequest
    with _$InterfaceSessionDescribeRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceSessionDescribeRequest.def({
    required String operation,
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    @UuidValueConverter() required UuidValue interfaceSessionId,
  }) = _InterfaceSessionDescribeRequest;

  factory InterfaceSessionDescribeRequest({
    String? operation,
    UuidValue? requestId,
    int? protocolVersion,
    required UuidValue interfaceSessionId,
  }) {
    return _InterfaceSessionDescribeRequest(
      operation: operation ?? 'interface_session_describe',
      requestId: requestId,
      protocolVersion: protocolVersion ?? 1,
      interfaceSessionId: interfaceSessionId,
    );
  }

  factory InterfaceSessionDescribeRequest.fromJson(Map<String, dynamic> json) =>
      _$InterfaceSessionDescribeRequestFromJson({
        ...json,
        if (!json.containsKey('operation'))
          'operation': 'interface_session_describe',
        if (!json.containsKey('protocol_version')) 'protocol_version': 1,
      });
}

@freezed
abstract class InterfaceSessionExperienceSessionView
    with _$InterfaceSessionExperienceSessionView {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceSessionExperienceSessionView.def({
    @UuidValueConverter()
    required UuidValue interfaceSessionExperienceSessionId,
    @UuidValueConverter() required UuidValue experienceSessionId,
    required String status,
    Map<String, dynamic>? metadataJson,
    @UuidValueConverter() required UuidValue domainCommitId,
  }) = _InterfaceSessionExperienceSessionView;

  factory InterfaceSessionExperienceSessionView({
    required UuidValue interfaceSessionExperienceSessionId,
    required UuidValue experienceSessionId,
    required String status,
    Map<String, dynamic>? metadataJson,
    required UuidValue domainCommitId,
  }) {
    return _InterfaceSessionExperienceSessionView(
      interfaceSessionExperienceSessionId: interfaceSessionExperienceSessionId,
      experienceSessionId: experienceSessionId,
      status: status,
      metadataJson: metadataJson ?? {},
      domainCommitId: domainCommitId,
    );
  }

  factory InterfaceSessionExperienceSessionView.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceSessionExperienceSessionViewFromJson({
    ...json,
    if (!json.containsKey('metadata_json')) 'metadata_json': {},
  });
}

@freezed
abstract class InterfaceSessionView with _$InterfaceSessionView {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceSessionView.def({
    @UuidValueConverter() required UuidValue interfaceSessionId,
    @UuidValueConverter() required UuidValue interfaceId,
    @UuidValueConverter() required UuidValue identitySessionId,
    required String name,
    required String state,
    @UuidValueConverter() required UuidValue domainCommitId,
    @Default(const [])
    List<InterfaceSessionExperienceSessionView> experienceSessions,
  }) = _InterfaceSessionView;

  factory InterfaceSessionView({
    required UuidValue interfaceSessionId,
    required UuidValue interfaceId,
    required UuidValue identitySessionId,
    required String name,
    required String state,
    required UuidValue domainCommitId,
    List<InterfaceSessionExperienceSessionView> experienceSessions = const [],
  }) {
    return _InterfaceSessionView(
      interfaceSessionId: interfaceSessionId,
      interfaceId: interfaceId,
      identitySessionId: identitySessionId,
      name: name,
      state: state,
      domainCommitId: domainCommitId,
      experienceSessions: experienceSessions,
    );
  }

  factory InterfaceSessionView.fromJson(Map<String, dynamic> json) =>
      _$InterfaceSessionViewFromJson(json);
}

@freezed
abstract class InterfaceSessionDescribeResponse
    with _$InterfaceSessionDescribeResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceSessionDescribeResponse.def({
    required String operation,
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String status,
    InterfaceSessionView? session,
  }) = _InterfaceSessionDescribeResponse;

  factory InterfaceSessionDescribeResponse({
    String? operation,
    UuidValue? requestId,
    int? protocolVersion,
    bool? success,
    String? error,
    required String status,
    InterfaceSessionView? session,
  }) {
    return _InterfaceSessionDescribeResponse(
      operation: operation ?? 'interface_session_describe',
      requestId: requestId,
      protocolVersion: protocolVersion ?? 1,
      success: success ?? true,
      error: error,
      status: status,
      session: session,
    );
  }

  factory InterfaceSessionDescribeResponse.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceSessionDescribeResponseFromJson({
    ...json,
    if (!json.containsKey('operation'))
      'operation': 'interface_session_describe',
    if (!json.containsKey('protocol_version')) 'protocol_version': 1,
    if (!json.containsKey('success')) 'success': true,
  });
}

@freezed
abstract class InterfaceExperienceSessionMountRequest
    with _$InterfaceExperienceSessionMountRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceExperienceSessionMountRequest.def({
    required String operation,
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    @UuidValueConverter() required UuidValue interfaceSessionId,
    @UuidValueConverter() required UuidValue experienceSessionId,
    required String status,
    Map<String, dynamic>? metadataJson,
  }) = _InterfaceExperienceSessionMountRequest;

  factory InterfaceExperienceSessionMountRequest({
    String? operation,
    UuidValue? requestId,
    int? protocolVersion,
    required UuidValue interfaceSessionId,
    required UuidValue experienceSessionId,
    String? status,
    Map<String, dynamic>? metadataJson,
  }) {
    return _InterfaceExperienceSessionMountRequest(
      operation: operation ?? 'interface_experience_session_mount',
      requestId: requestId,
      protocolVersion: protocolVersion ?? 1,
      interfaceSessionId: interfaceSessionId,
      experienceSessionId: experienceSessionId,
      status: status ?? 'active',
      metadataJson: metadataJson ?? {},
    );
  }

  factory InterfaceExperienceSessionMountRequest.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceExperienceSessionMountRequestFromJson({
    ...json,
    if (!json.containsKey('operation'))
      'operation': 'interface_experience_session_mount',
    if (!json.containsKey('protocol_version')) 'protocol_version': 1,
    if (!json.containsKey('status')) 'status': 'active',
    if (!json.containsKey('metadata_json')) 'metadata_json': {},
  });
}

@freezed
abstract class InterfaceExperienceSessionMountResponse
    with _$InterfaceExperienceSessionMountResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceExperienceSessionMountResponse.def({
    required String operation,
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    @UuidValueConverter()
    required UuidValue interfaceSessionExperienceSessionId,
    @UuidValueConverter() required UuidValue interfaceSessionId,
    @UuidValueConverter() required UuidValue experienceSessionId,
    required String status,
    Map<String, dynamic>? metadataJson,
    @UuidValueConverter() UuidValue? domainCommitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    String? graphHashPost,
  }) = _InterfaceExperienceSessionMountResponse;

  factory InterfaceExperienceSessionMountResponse({
    String? operation,
    UuidValue? requestId,
    int? protocolVersion,
    bool? success,
    String? error,
    required UuidValue interfaceSessionExperienceSessionId,
    required UuidValue interfaceSessionId,
    required UuidValue experienceSessionId,
    required String status,
    Map<String, dynamic>? metadataJson,
    UuidValue? domainCommitId,
    UuidValue? objectInstanceGraphCommitId,
    String? graphHashPost,
  }) {
    return _InterfaceExperienceSessionMountResponse(
      operation: operation ?? 'interface_experience_session_mount',
      requestId: requestId,
      protocolVersion: protocolVersion ?? 1,
      success: success ?? true,
      error: error,
      interfaceSessionExperienceSessionId: interfaceSessionExperienceSessionId,
      interfaceSessionId: interfaceSessionId,
      experienceSessionId: experienceSessionId,
      status: status,
      metadataJson: metadataJson ?? {},
      domainCommitId: domainCommitId,
      objectInstanceGraphCommitId: objectInstanceGraphCommitId,
      graphHashPost: graphHashPost,
    );
  }

  factory InterfaceExperienceSessionMountResponse.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceExperienceSessionMountResponseFromJson({
    ...json,
    if (!json.containsKey('operation'))
      'operation': 'interface_experience_session_mount',
    if (!json.containsKey('protocol_version')) 'protocol_version': 1,
    if (!json.containsKey('success')) 'success': true,
    if (!json.containsKey('metadata_json')) 'metadata_json': {},
  });
}

@freezed
abstract class InterfaceEnterAppScreenRequest
    with _$InterfaceEnterAppScreenRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceEnterAppScreenRequest.def({
    required String operation,
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required String namespace,
    @UuidValueConverter() required UuidValue appPackageId,
    @UuidValueConverter() required UuidValue appPackageBranchId,
    @UuidValueConverter()
    required UuidValue appPackageObjectInstanceGraphCommitId,
    @UuidValueConverter() required UuidValue appConfigScreenConfigId,
    String? reason,
    required Map<String, dynamic> evidence,
  }) = _InterfaceEnterAppScreenRequest;

  factory InterfaceEnterAppScreenRequest({
    String? operation,
    UuidValue? requestId,
    int? protocolVersion,
    required String namespace,
    required UuidValue appPackageId,
    required UuidValue appPackageBranchId,
    required UuidValue appPackageObjectInstanceGraphCommitId,
    required UuidValue appConfigScreenConfigId,
    String? reason,
    Map<String, dynamic>? evidence,
  }) {
    return _InterfaceEnterAppScreenRequest(
      operation: operation ?? 'interface_enter_app_screen',
      requestId: requestId,
      protocolVersion: protocolVersion ?? 1,
      namespace: namespace,
      appPackageId: appPackageId,
      appPackageBranchId: appPackageBranchId,
      appPackageObjectInstanceGraphCommitId:
          appPackageObjectInstanceGraphCommitId,
      appConfigScreenConfigId: appConfigScreenConfigId,
      reason: reason,
      evidence: evidence ?? {},
    );
  }

  factory InterfaceEnterAppScreenRequest.fromJson(Map<String, dynamic> json) =>
      _$InterfaceEnterAppScreenRequestFromJson({
        ...json,
        if (!json.containsKey('operation'))
          'operation': 'interface_enter_app_screen',
        if (!json.containsKey('protocol_version')) 'protocol_version': 1,
        if (!json.containsKey('evidence')) 'evidence': {},
      });
}

@freezed
abstract class InterfaceEnterAppScreenResponse
    with _$InterfaceEnterAppScreenResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceEnterAppScreenResponse.def({
    required String operation,
    @UuidValueConverter() UuidValue? requestId,
    required int protocolVersion,
    required bool success,
    String? error,
    required String namespace,
    InterfaceAppScreenState? appScreen,
    required InterfaceHostState hostState,
  }) = _InterfaceEnterAppScreenResponse;

  factory InterfaceEnterAppScreenResponse({
    String? operation,
    UuidValue? requestId,
    int? protocolVersion,
    bool? success,
    String? error,
    required String namespace,
    InterfaceAppScreenState? appScreen,
    required InterfaceHostState hostState,
  }) {
    return _InterfaceEnterAppScreenResponse(
      operation: operation ?? 'interface_enter_app_screen',
      requestId: requestId,
      protocolVersion: protocolVersion ?? 1,
      success: success ?? true,
      error: error,
      namespace: namespace,
      appScreen: appScreen,
      hostState: hostState,
    );
  }

  factory InterfaceEnterAppScreenResponse.fromJson(Map<String, dynamic> json) =>
      _$InterfaceEnterAppScreenResponseFromJson({
        ...json,
        if (!json.containsKey('operation'))
          'operation': 'interface_enter_app_screen',
        if (!json.containsKey('protocol_version')) 'protocol_version': 1,
        if (!json.containsKey('success')) 'success': true,
      });
}

/// One stable-id row in a complete shared-layout transition intent.
@freezed
abstract class InterfaceAttentionLayoutTransitionSectionIntent
    with _$InterfaceAttentionLayoutTransitionSectionIntent {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceAttentionLayoutTransitionSectionIntent.def({
    @UuidValueConverter() required UuidValue layoutConfigSectionConfigId,
    required int order,
    required int weightMicros,
    required bool isVisible,
    required bool isCollapsed,
  }) = _InterfaceAttentionLayoutTransitionSectionIntent;

  factory InterfaceAttentionLayoutTransitionSectionIntent({
    required UuidValue layoutConfigSectionConfigId,
    required int order,
    required int weightMicros,
    bool? isVisible,
    bool? isCollapsed,
  }) {
    return _InterfaceAttentionLayoutTransitionSectionIntent(
      layoutConfigSectionConfigId: layoutConfigSectionConfigId,
      order: order,
      weightMicros: weightMicros,
      isVisible: isVisible ?? true,
      isCollapsed: isCollapsed ?? false,
    );
  }

  factory InterfaceAttentionLayoutTransitionSectionIntent.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceAttentionLayoutTransitionSectionIntentFromJson({
    ...json,
    if (!json.containsKey('is_visible')) 'is_visible': true,
    if (!json.containsKey('is_collapsed')) 'is_collapsed': false,
  });
}

/// One stable admitted config-section anchor in a complete topology intent.
@freezed
abstract class InterfaceAttentionLayoutTopologyTransitionSectionIntent
    with _$InterfaceAttentionLayoutTopologyTransitionSectionIntent {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceAttentionLayoutTopologyTransitionSectionIntent.def({
    @UuidValueConverter() required UuidValue layoutConfigSectionConfigId,
    required int order,
  }) = _InterfaceAttentionLayoutTopologyTransitionSectionIntent;

  factory InterfaceAttentionLayoutTopologyTransitionSectionIntent({
    required UuidValue layoutConfigSectionConfigId,
    required int order,
  }) {
    return _InterfaceAttentionLayoutTopologyTransitionSectionIntent(
      layoutConfigSectionConfigId: layoutConfigSectionConfigId,
      order: order,
    );
  }

  factory InterfaceAttentionLayoutTopologyTransitionSectionIntent.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceAttentionLayoutTopologyTransitionSectionIntentFromJson(json);
}
