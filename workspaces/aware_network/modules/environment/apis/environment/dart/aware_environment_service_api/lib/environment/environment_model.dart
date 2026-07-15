// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import '../attention/session/models_model.dart';
import '../session/session_model.dart';
import 'environment_enums.dart';
import 'environment_service_operation_model.dart';
import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'environment_model.freezed.dart';
part 'environment_model.g.dart';

/// Canonical environment operation DTOs (transport-layer, graph/ORM agnostic).
/// SSOT: `environment-service-dto` generated from `apis/environment/dto`.
/// `aware_comms` re-exports these DTOs for transport/service import stability,
/// but schema ownership remains here so all language targets compile from one rail.
@freezed
abstract class EnvironmentOperationContext with _$EnvironmentOperationContext {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationContext.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
  }) = _EnvironmentOperationContext;

  factory EnvironmentOperationContext({
    UuidValue? actorId,
    required UuidValue environmentId,
    UuidValue? processId,
    UuidValue? threadId,
    UuidValue? branchId,
    String? projectionHash,
  }) {
    return _EnvironmentOperationContext(
      actorId: actorId,
      environmentId: environmentId,
      processId: processId,
      threadId: threadId,
      branchId: branchId,
      projectionHash: projectionHash,
    );
  }

  factory EnvironmentOperationContext.fromJson(Map<String, dynamic> json) =>
      _$EnvironmentOperationContextFromJson(json);
}

/// Context for environment notifications (fan-out).
/// Notifications may be emitted by commit stores and transport layers that do not
/// have a full EnvironmentOperationContext. The lane key is still canonical.
@freezed
abstract class EnvironmentOperationNotificationContext
    with _$EnvironmentOperationNotificationContext {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationNotificationContext.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() required UuidValue branchId,
    required String projectionHash,
  }) = _EnvironmentOperationNotificationContext;

  factory EnvironmentOperationNotificationContext({
    UuidValue? actorId,
    UuidValue? environmentId,
    UuidValue? processId,
    UuidValue? threadId,
    required UuidValue branchId,
    required String projectionHash,
  }) {
    return _EnvironmentOperationNotificationContext(
      actorId: actorId,
      environmentId: environmentId,
      processId: processId,
      threadId: threadId,
      branchId: branchId,
      projectionHash: projectionHash,
    );
  }

  factory EnvironmentOperationNotificationContext.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentOperationNotificationContextFromJson(json);
}

/// EnvironmentOperation is either a request or a response.
@freezed
abstract class EnvironmentOperation with _$EnvironmentOperation {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperation.def({
    EnvironmentOperationRequest? request,
    EnvironmentOperationResponse? response,
    EnvironmentOperationNotification? notification,
  }) = _EnvironmentOperation;

  factory EnvironmentOperation({
    EnvironmentOperationRequest? request,
    EnvironmentOperationResponse? response,
    EnvironmentOperationNotification? notification,
  }) {
    return _EnvironmentOperation(
      request: request,
      response: response,
      notification: notification,
    );
  }

  factory EnvironmentOperation.fromJson(Map<String, dynamic> json) =>
      _$EnvironmentOperationFromJson(json);
}

/// Request union base (operation + context).
@Freezed(unionKey: 'operation')
abstract class EnvironmentOperationRequest with _$EnvironmentOperationRequest {
  @FreezedUnionValue('fetch_capabilities')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.fetchCapabilities({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
  }) = FetchCapabilitiesRequest;

  @FreezedUnionValue('describe_environment_config')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.describeEnvironmentConfig({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
  }) = DescribeEnvironmentConfigRequest;

  @FreezedUnionValue('describe_environment')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.describeEnvironment({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
  }) = DescribeEnvironmentRequest;

  @FreezedUnionValue('describe_environment_topology')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.describeEnvironmentTopology({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    String? processKey,
    String? threadKey,
  }) = DescribeEnvironmentTopologyRequest;

  @FreezedUnionValue('describe_environment_status')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.describeEnvironmentStatus({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @Default(const []) List<String> includeBlocks,
    required bool strictCommitTruth,
  }) = DescribeEnvironmentStatusRequest;

  @FreezedUnionValue('ensure_ready')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.ensureReady({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
  }) = EnsureReadyRequest;

  @FreezedUnionValue('get_lane_head')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.getLaneHead({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
  }) = GetLaneHeadRequest;

  @FreezedUnionValue('get_object_instance_graph_commit')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.getObjectInstanceGraphCommit({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() required UuidValue commitId,
  }) = GetObjectInstanceGraphCommitRequest;

  @FreezedUnionValue('materialize_committed_projection_dto')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.materializeCommittedProjectionDto({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() required UuidValue commitId,
    String? expectedGraphHashPost,
    @UuidValueConverter() UuidValue? objectInstanceGraphId,
    @UuidValueConverter() UuidValue? rootObjectId,
    required bool useCommitRoot,
    String? dtoClassRef,
    @UuidValueConverter() UuidValue? classConfigId,
    String? dtoPackageName,
    String? dtoImportRoot,
    String? viewRef,
    String? projectionViewKey,
    required bool includeRelationships,
    int? maxDepth,
  }) = MaterializeCommittedProjectionDtoRequest;

  @FreezedUnionValue('resolve_runtime_refs')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.resolveRuntimeRefs({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @Default(const []) List<ResolveRuntimeFunctionTargetQuery> functionTargets,
    @Default(const []) List<ResolveRuntimeClassRefQuery> classRefs,
  }) = ResolveRuntimeRefsRequest;

  @FreezedUnionValue('configure_service_api_dependency_routes')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.configureServiceApiDependencyRoutes({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required List<dynamic> routes,
  }) = ConfigureServiceApiDependencyRoutesRequest;

  @FreezedUnionValue('attach_environment_ontology')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.attachEnvironmentOntology({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() required UuidValue ontologyId,
    required String role,
    required String status,
    String? title,
    String? description,
    String? expectedGraphHashPre,
    @UuidValueConverter() UuidValue? expectedHeadCommitId,
    required bool commit,
    required bool publish,
  }) = AttachEnvironmentOntologyRequest;

  @FreezedUnionValue('ensure_environment_ontology_runtime')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.ensureEnvironmentOntologyRuntime({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() UuidValue? ontologyId,
    String? packageName,
    String? fqnPrefix,
    String? artifactSetId,
    String? workspaceRevisionId,
    String? materializationRef,
    required bool includeArtifacts,
    Map<String, dynamic>? sourcePayload,
    @UuidValueConverter() UuidValue? membershipCommitId,
  }) = EnsureEnvironmentOntologyRuntimeRequest;

  @FreezedUnionValue('list_environment_ontologies')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.listEnvironmentOntologies({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() UuidValue? commitId,
    @UuidValueConverter() UuidValue? rootObjectId,
    String? expectedGraphHashPost,
    String? dtoClassRef,
    String? dtoPackageName,
    String? dtoImportRoot,
  }) = ListEnvironmentOntologiesRequest;

  @FreezedUnionValue('resolve_environment_session_attention')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.resolveEnvironmentSessionAttention({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() required UuidValue environmentSessionId,
    @UuidValueConverter() UuidValue? environmentNavigationContextId,
    @UuidValueConverter() UuidValue? environmentSessionThreadId,
    @UuidValueConverter() UuidValue? environmentSessionAttentionSessionId,
    @UuidValueConverter() UuidValue? expectedAttentionSessionId,
    @UuidValueConverter() UuidValue? attentionFocusTransitionId,
    @UuidValueConverter() UuidValue? expectedAttentionSessionSectionId,
    @UuidValueConverter() UuidValue? expectedFocusScopeId,
    @UuidValueConverter() UuidValue? expectedObjectInstanceGraphCommitId,
    String? expectedProjectionHash,
    required bool includeAttentionSession,
    required bool includeTransitionList,
    int? transitionLimit,
    required Map<String, dynamic> metadata,
  }) = ResolveEnvironmentSessionAttentionRequest;

  @FreezedUnionValue('mount_environment_session_attention')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.mountEnvironmentSessionAttention({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() required UuidValue environmentSessionId,
    @UuidValueConverter() required UuidValue attentionSessionId,
    String? key,
    String? title,
    required String status,
    required Map<String, dynamic> metadata,
  }) = MountEnvironmentSessionAttentionRequest;

  @FreezedUnionValue('create_environment_navigation_context')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.createEnvironmentNavigationContext({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() required UuidValue environmentSessionId,
    required EnvironmentSessionJoinReceipt sessionJoinReceipt,
    required String key,
    String? title,
    required String status,
    required bool isDefault,
    @UuidValueConverter() UuidValue? selectedProcessId,
    @UuidValueConverter() UuidValue? selectedThreadId,
    required Map<String, dynamic> metadata,
  }) = CreateEnvironmentNavigationContextRequest;

  @FreezedUnionValue('select_environment_navigation_target')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.selectEnvironmentNavigationTarget({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() required UuidValue environmentSessionId,
    @UuidValueConverter() required UuidValue environmentNavigationContextId,
    required EnvironmentSessionJoinReceipt sessionJoinReceipt,
    @UuidValueConverter() UuidValue? selectedProcessId,
    @UuidValueConverter() UuidValue? selectedThreadId,
    @UuidValueConverter() UuidValue? expectedHeadCommitId,
    String? expectedGraphHashPre,
    String? reason,
    required Map<String, dynamic> metadata,
  }) = SelectEnvironmentNavigationTargetRequest;

  @FreezedUnionValue('describe_environment_navigation_context')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.describeEnvironmentNavigationContext({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() required UuidValue environmentSessionId,
    @UuidValueConverter() required UuidValue environmentNavigationContextId,
    required EnvironmentSessionJoinReceipt sessionJoinReceipt,
    required bool includeCommit,
  }) = DescribeEnvironmentNavigationContextRequest;

  @FreezedUnionValue('list_environment_navigation_contexts')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.listEnvironmentNavigationContexts({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() required UuidValue environmentSessionId,
    required EnvironmentSessionJoinReceipt sessionJoinReceipt,
    required bool includeClosed,
  }) = ListEnvironmentNavigationContextsRequest;

  @FreezedUnionValue('invoke_function')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.invokeFunction({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @JsonKey(
      fromJson: InvokeFunctionCallTargetExtension.fromJson,
      toJson: InvokeFunctionCallTargetExtension.toJson,
    )
    required InvokeFunctionCallTarget callTarget,
    @UuidValueConverter() UuidValue? objectId,
    @UuidValueConverter() UuidValue? objectProjectionGraphId,
    @UuidValueConverter() UuidValue? objectProjectionGraphIdentityId,
    @UuidValueConverter() required UuidValue functionId,
    required List<dynamic> args,
    required Map<String, dynamic> kwargs,
    String? expectedGraphHashPre,
    @UuidValueConverter() UuidValue? expectedHeadCommitId,
    required bool commit,
    required bool publish,
  }) = InvokeFunctionRequest;

  @FreezedUnionValue('service_operation')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationRequest.serviceOperation({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required EnvironmentServiceOperation serviceOperation,
  }) = EnvironmentServiceOperationRequest;

  factory EnvironmentOperationRequest.fromJson(Map<String, dynamic> json) =>
      _$EnvironmentOperationRequestFromJson(json);
}

/// Response union base (operation + context).
@Freezed(unionKey: 'operation')
abstract class EnvironmentOperationResponse
    with _$EnvironmentOperationResponse {
  @FreezedUnionValue('fetch_capabilities')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.fetchCapabilities({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @Default(const []) List<CapabilityRole> roles,
    @Default(const []) List<CapabilityFunction> functions,
    @Default(const []) List<CapabilityObject> objects,
  }) = FetchCapabilitiesResponse;

  @FreezedUnionValue('describe_environment_config')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.describeEnvironmentConfig({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    String? title,
    @UuidValueConverter() UuidValue? environmentConfigId,
    String? environmentConfigTitle,
    String? canonicalLanguage,
    String? bundleManifestPath,
    String? bundleManifestHttpPath,
    String? bundleArtifactHttpPathPrefix,
    String? bundleDescriptorHttpPath,
    String? bundleHeadId,
    Map<String, dynamic>? bundleReleaseIdentity,
    @UuidValueConverter() UuidValue? ocgId,
    @Default(const []) List<String> opgHashes,
    @Default(const []) List<DescribeEnvironmentOPG> opgs,
  }) = DescribeEnvironmentConfigResponse;

  @FreezedUnionValue('describe_environment')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.describeEnvironment({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String status,
    String? error,
    @UuidValueConverter() UuidValue? environmentConfigId,
    String? environmentConfigTitle,
    String? bundleManifestPath,
    String? bundleManifestHttpPath,
    String? bundleArtifactHttpPathPrefix,
    String? bundleDescriptorHttpPath,
    String? bundleHeadId,
    Map<String, dynamic>? bundleReleaseIdentity,
    @UuidValueConverter() UuidValue? ocgId,
    String? environmentTitle,
    String? environmentDescription,
    @UuidValueConverter() UuidValue? bootProcessId,
    @UuidValueConverter() UuidValue? bootThreadId,
    @UuidValueConverter() UuidValue? bootBranchId,
    @UuidValueConverter() UuidValue? headCommitId,
    String? headGraphHashPost,
    @UuidValueConverter() UuidValue? headObjectInstanceGraphId,
    @UuidValueConverter() UuidValue? headRootObjectId,
    int? headVersion,
  }) = DescribeEnvironmentResponse;

  @FreezedUnionValue('describe_environment_topology')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.describeEnvironmentTopology({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String status,
    String? error,
    @Default(const []) List<DescribeEnvironmentTopologyProcess> processes,
  }) = DescribeEnvironmentTopologyResponse;

  @FreezedUnionValue('describe_environment_status')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.describeEnvironmentStatus({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String status,
    String? error,
    required String statusVersion,
    @Default(const []) List<EnvironmentStatusBlock> blocks,
    required List<dynamic> refusals,
  }) = DescribeEnvironmentStatusResponse;

  @FreezedUnionValue('ensure_ready')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.ensureReady({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String status,
    String? error,
    String? bundleManifestPath,
    String? bundleManifestHttpPath,
    String? bundleArtifactHttpPathPrefix,
    String? bundleDescriptorHttpPath,
    String? bundleHeadId,
    Map<String, dynamic>? bundleReleaseIdentity,
    @UuidValueConverter() UuidValue? ocgId,
    @Default(const []) List<String> opgHashes,
    EnvironmentReadinessReceipt? readinessReceipt,
  }) = EnsureReadyResponse;

  @FreezedUnionValue('get_lane_head')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.getLaneHead({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String status,
    String? error,
    @UuidValueConverter() UuidValue? commitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    String? graphHashPost,
    @UuidValueConverter() UuidValue? objectInstanceGraphId,
    @UuidValueConverter() UuidValue? objectInstanceGraphIdentityId,
    @UuidValueConverter() UuidValue? objectInstanceGraphBranchId,
    @UuidValueConverter() UuidValue? objectProjectionGraphId,
    @UuidValueConverter() UuidValue? objectProjectionGraphIdentityId,
    @UuidValueConverter() UuidValue? rootObjectId,
    int? headVersion,
  }) = GetLaneHeadResponse;

  @FreezedUnionValue('get_object_instance_graph_commit')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.getObjectInstanceGraphCommit({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String status,
    String? error,
    @UuidValueConverter() UuidValue? commitId,
    @UuidValueConverter() required UuidValue objectInstanceGraphCommitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphId,
    @UuidValueConverter() UuidValue? objectInstanceGraphIdentityId,
    @UuidValueConverter() UuidValue? objectInstanceGraphBranchId,
    @UuidValueConverter() UuidValue? objectProjectionGraphId,
    @UuidValueConverter() UuidValue? objectProjectionGraphIdentityId,
    @UuidValueConverter() UuidValue? rootObjectId,
    String? graphHashPre,
    String? graphHashPost,
    Map<String, dynamic>? commit,
  }) = GetObjectInstanceGraphCommitResponse;

  @FreezedUnionValue('materialize_committed_projection_dto')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.materializeCommittedProjectionDto({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String status,
    String? error,
    String? refusalCode,
    Map<String, dynamic>? dtoPayload,
    String? dtoClassRef,
    @UuidValueConverter() UuidValue? classConfigId,
    String? dtoPackageName,
    String? dtoImportRoot,
    String? dtoArtifactDigest,
    @UuidValueConverter() UuidValue? commitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphId,
    @UuidValueConverter() UuidValue? rootObjectId,
    String? graphHashPost,
    String? materializerVersion,
    required Map<String, dynamic> evidence,
  }) = MaterializeCommittedProjectionDtoResponse;

  @FreezedUnionValue('resolve_runtime_refs')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.resolveRuntimeRefs({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String status,
    String? error,
    @Default(const []) List<ResolvedRuntimeFunctionTarget> functionTargets,
    @Default(const []) List<ResolvedRuntimeClassRef> classRefs,
    required Map<String, dynamic> evidence,
  }) = ResolveRuntimeRefsResponse;

  @FreezedUnionValue('configure_service_api_dependency_routes')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.configureServiceApiDependencyRoutes({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String status,
    String? error,
    required int routeCount,
    required bool routeConsumersStarted,
  }) = ConfigureServiceApiDependencyRoutesResponse;

  @FreezedUnionValue('attach_environment_ontology')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.attachEnvironmentOntology({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String status,
    String? error,
    EnvironmentOntologyMembership? membership,
    @UuidValueConverter() UuidValue? commitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    String? graphHashPre,
    String? graphHashPost,
    required Map<String, dynamic> evidence,
  }) = AttachEnvironmentOntologyResponse;

  @FreezedUnionValue('ensure_environment_ontology_runtime')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.ensureEnvironmentOntologyRuntime({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String status,
    String? error,
    @UuidValueConverter() UuidValue? ontologyId,
    String? packageName,
    String? fqnPrefix,
    String? artifactSetId,
    required int runtimeProjectionDescriptorCount,
    required int capabilityObjectCount,
    required int capabilityFunctionCount,
    required int registeredArtifactRefCount,
    required int registryArtifactRefCount,
    @UuidValueConverter() UuidValue? membershipCommitId,
    required Map<String, dynamic> evidence,
  }) = EnsureEnvironmentOntologyRuntimeResponse;

  @FreezedUnionValue('list_environment_ontologies')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.listEnvironmentOntologies({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String status,
    String? error,
    @Default(const []) List<EnvironmentOntologyMembership> memberships,
    @UuidValueConverter() UuidValue? commitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    String? graphHashPost,
    required Map<String, dynamic> evidence,
  }) = ListEnvironmentOntologiesResponse;

  @FreezedUnionValue('resolve_environment_session_attention')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.resolveEnvironmentSessionAttention({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() UuidValue? requestId,
    required String status,
    String? error,
    EnvironmentSessionAttentionResolution? resolution,
    required Map<String, dynamic> evidence,
  }) = ResolveEnvironmentSessionAttentionResponse;

  @FreezedUnionValue('mount_environment_session_attention')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.mountEnvironmentSessionAttention({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter()
    required UuidValue environmentSessionAttentionSessionId,
    @UuidValueConverter() required UuidValue environmentSessionId,
    @UuidValueConverter() required UuidValue attentionSessionId,
    String? key,
    String? title,
    required String status,
    required Map<String, dynamic> metadata,
    @UuidValueConverter() UuidValue? domainCommitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    String? graphHashPost,
  }) = MountEnvironmentSessionAttentionResponse;

  @FreezedUnionValue('create_environment_navigation_context')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.createEnvironmentNavigationContext({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() UuidValue? requestId,
    required bool accepted,
    required String status,
    String? error,
    EnvironmentNavigationContextView? context,
    required EnvironmentNavigationCommitReceipt receipt,
    required Map<String, dynamic> evidence,
  }) = CreateEnvironmentNavigationContextResponse;

  @FreezedUnionValue('select_environment_navigation_target')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.selectEnvironmentNavigationTarget({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() UuidValue? requestId,
    required bool accepted,
    required String status,
    String? error,
    EnvironmentNavigationContextView? context,
    required EnvironmentNavigationCommitReceipt receipt,
    required Map<String, dynamic> evidence,
  }) = SelectEnvironmentNavigationTargetResponse;

  @FreezedUnionValue('describe_environment_navigation_context')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.describeEnvironmentNavigationContext({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String status,
    String? error,
    EnvironmentNavigationContextView? context,
    @Default(const []) List<String> blockers,
    required Map<String, dynamic> evidence,
  }) = DescribeEnvironmentNavigationContextResponse;

  @FreezedUnionValue('list_environment_navigation_contexts')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.listEnvironmentNavigationContexts({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String status,
    String? error,
    @Default(const []) List<EnvironmentNavigationContextView> contexts,
    @Default(const []) List<String> blockers,
    required Map<String, dynamic> evidence,
  }) = ListEnvironmentNavigationContextsResponse;

  @FreezedUnionValue('invoke_function')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.invokeFunction({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String status,
    Object? payload,
    String? error,
    @Default(const []) List<String> logs,
    int? executionTimeMs,
    @UuidValueConverter() UuidValue? rootObjectId,
    String? graphHashPre,
    String? graphHashPost,
    @UuidValueConverter() UuidValue? functionCallId,
    @UuidValueConverter() UuidValue? functionCallResponseId,
    required List<dynamic> changes,
    @UuidValueConverter() UuidValue? commitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    @UuidValueConverter() UuidValue? objectProjectionGraphId,
    @UuidValueConverter() UuidValue? objectProjectionGraphIdentityId,
    @UuidValueConverter() UuidValue? objectInstanceGraphId,
    @UuidValueConverter() UuidValue? objectInstanceGraphIdentityId,
    @UuidValueConverter() UuidValue? objectInstanceGraphBranchId,
  }) = InvokeFunctionResponse;

  @FreezedUnionValue('service_operation')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationResponse.serviceOperation({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required EnvironmentServiceOperation serviceOperation,
  }) = EnvironmentServiceOperationResponse;

  factory EnvironmentOperationResponse.fromJson(Map<String, dynamic> json) =>
      _$EnvironmentOperationResponseFromJson(json);
}

/// Notification union base (operation + context).
/// Used for commit receipts / lane head moves so clients can sync lanes without
/// inferring from unrelated transports (e.g., inference streams).
@Freezed(unionKey: 'operation')
abstract class EnvironmentOperationNotification
    with _$EnvironmentOperationNotification {
  @FreezedUnionValue('lane_commit_receipt')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationNotification.laneCommitReceipt({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() required UuidValue branchId,
    required String projectionHash,
    @UuidValueConverter() required UuidValue commitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    @UuidValueConverter() UuidValue? objectProjectionGraphId,
    @UuidValueConverter() UuidValue? objectProjectionGraphIdentityId,
    @UuidValueConverter() UuidValue? objectInstanceGraphId,
    @UuidValueConverter() UuidValue? objectInstanceGraphIdentityId,
    @UuidValueConverter() UuidValue? objectInstanceGraphBranchId,
    int? createdAtUnixMs,
    String? operationLabel,
    @JsonKey(
      fromJson: InvokeFunctionCallTargetExtension.fromJsonNullable,
      toJson: InvokeFunctionCallTargetExtension.toJsonNullable,
    )
    InvokeFunctionCallTarget? callTarget,
    @UuidValueConverter() UuidValue? functionId,
    @UuidValueConverter() UuidValue? objectId,
    @UuidValueConverter() UuidValue? classInstanceIdentityId,
    String? graphHashPost,
    @UuidValueConverter() UuidValue? rootObjectId,
    int? headVersion,
  }) = LaneCommitReceiptNotification;

  @FreezedUnionValue('lane_event_receipt')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationNotification.laneEventReceipt({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() required UuidValue branchId,
    required String projectionHash,
    @UuidValueConverter() required UuidValue eventId,
    required String eventType,
    required String source,
    required int createdAtUnixMs,
    @UuidValueConverter() required UuidValue commitId,
    @UuidValueConverter() UuidValue? targetActorId,
    @UuidValueConverter() UuidValue? actorSubscriptionId,
    @UuidValueConverter() UuidValue? eventConfigConditionConfigId,
    String? graphHashPost,
    @UuidValueConverter() UuidValue? objectInstanceGraphId,
    @UuidValueConverter() UuidValue? rootObjectId,
  }) = LaneEventReceiptNotification;

  @FreezedUnionValue('lane_action_execution_receipt')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationNotification.laneActionExecutionReceipt({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() required UuidValue branchId,
    required String projectionHash,
    @UuidValueConverter() required UuidValue actionExecutionId,
    @UuidValueConverter() required UuidValue eventId,
    required String eventType,
    required String source,
    required int createdAtUnixMs,
    @UuidValueConverter() required UuidValue commitId,
    @UuidValueConverter() UuidValue? targetActorId,
    @UuidValueConverter() UuidValue? actorSubscriptionId,
    @UuidValueConverter() UuidValue? eventConfigConditionConfigId,
    @UuidValueConverter() UuidValue? actionBindingId,
    @UuidValueConverter() UuidValue? actionConfigId,
    String? actionType,
    String? graphHashPost,
    @UuidValueConverter() UuidValue? objectInstanceGraphId,
    @UuidValueConverter() UuidValue? rootObjectId,
  }) = LaneActionExecutionReceiptNotification;

  @FreezedUnionValue('lane_action_feedback_receipt')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationNotification.laneActionFeedbackReceipt({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() required UuidValue branchId,
    required String projectionHash,
    @UuidValueConverter() required UuidValue actionExecutionId,
    @UuidValueConverter() required UuidValue eventId,
    required int sequence,
    required int createdAtUnixMs,
    required String stage,
    required String status,
    @UuidValueConverter() UuidValue? actionBindingId,
    @UuidValueConverter() UuidValue? actionConfigId,
    String? actionType,
    String? message,
    @UuidValueConverter() UuidValue? actorIdentityId,
    @UuidValueConverter() UuidValue? actorProcessThreadId,
    @UuidValueConverter() UuidValue? executionRequestId,
  }) = LaneActionFeedbackReceiptNotification;

  @FreezedUnionValue('lane_action_terminal_receipt')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationNotification.laneActionTerminalReceipt({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() required UuidValue branchId,
    required String projectionHash,
    @UuidValueConverter() required UuidValue actionExecutionId,
    @UuidValueConverter() required UuidValue eventId,
    required String terminalStatus,
    required bool handled,
    required int createdAtUnixMs,
    @UuidValueConverter() UuidValue? actionBindingId,
    @UuidValueConverter() UuidValue? actionConfigId,
    String? actionType,
    String? info,
    String? error,
    @UuidValueConverter() UuidValue? actorIdentityId,
    @UuidValueConverter() UuidValue? actorProcessThreadId,
    @UuidValueConverter() UuidValue? executionRequestId,
  }) = LaneActionTerminalReceiptNotification;

  @FreezedUnionValue('lane_turn_stream_receipt')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOperationNotification.laneTurnStreamReceipt({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() required UuidValue branchId,
    required String projectionHash,
    required String service,
    @UuidValueConverter() required UuidValue inferenceRequestId,
    required int createdAtUnixMs,
    required String streamKind,
    int? sequence,
    @UuidValueConverter() UuidValue? agentIdentityId,
    @UuidValueConverter() UuidValue? agentProcessThreadId,
    String? textDelta,
    String? message,
    Object? payload,
  }) = LaneTurnStreamReceiptNotification;

  factory EnvironmentOperationNotification.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentOperationNotificationFromJson(json);
}

@freezed
abstract class ResolveRuntimeFunctionTargetQuery
    with _$ResolveRuntimeFunctionTargetQuery {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ResolveRuntimeFunctionTargetQuery.def({
    String? queryKey,
    required String functionRef,
    @JsonKey(
      fromJson: InvokeFunctionCallTargetExtension.fromJson,
      toJson: InvokeFunctionCallTargetExtension.toJson,
    )
    required InvokeFunctionCallTarget callTarget,
    String? projectionHashHint,
  }) = _ResolveRuntimeFunctionTargetQuery;

  factory ResolveRuntimeFunctionTargetQuery({
    String? queryKey,
    required String functionRef,
    InvokeFunctionCallTarget? callTarget,
    String? projectionHashHint,
  }) {
    return _ResolveRuntimeFunctionTargetQuery(
      queryKey: queryKey,
      functionRef: functionRef,
      callTarget: callTarget ?? InvokeFunctionCallTarget.instance,
      projectionHashHint: projectionHashHint,
    );
  }

  factory ResolveRuntimeFunctionTargetQuery.fromJson(
    Map<String, dynamic> json,
  ) => _$ResolveRuntimeFunctionTargetQueryFromJson({
    ...json,
    if (!json.containsKey('call_target')) 'call_target': 'instance',
  });
}

@freezed
abstract class ResolveRuntimeClassRefQuery with _$ResolveRuntimeClassRefQuery {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ResolveRuntimeClassRefQuery.def({
    String? queryKey,
    required String classRef,
  }) = _ResolveRuntimeClassRefQuery;

  factory ResolveRuntimeClassRefQuery({
    String? queryKey,
    required String classRef,
  }) {
    return _ResolveRuntimeClassRefQuery(queryKey: queryKey, classRef: classRef);
  }

  factory ResolveRuntimeClassRefQuery.fromJson(Map<String, dynamic> json) =>
      _$ResolveRuntimeClassRefQueryFromJson(json);
}

/// Admit an actor to a concrete EnvironmentProfile using Identity-owned ActorConfig
/// eligibility.
/// Contract:
/// - Environment owns the admission scope and EnvironmentProfile -> ActorConfig
/// eligibility check.
/// - Identity owns concrete RoleAssignment/ActorRole truth.
/// - This operation grants no Experience access and does not infer Experience
/// participation.
@freezed
abstract class AdmitEnvironmentActorRequest
    with _$AdmitEnvironmentActorRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory AdmitEnvironmentActorRequest.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String operation,
    @UuidValueConverter() UuidValue? requestId,
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
  }) = _AdmitEnvironmentActorRequest;

  factory AdmitEnvironmentActorRequest({
    UuidValue? actorId,
    required UuidValue environmentId,
    UuidValue? processId,
    UuidValue? threadId,
    UuidValue? branchId,
    String? projectionHash,
    String? operation,
    UuidValue? requestId,
    required UuidValue environmentProfileId,
    required UuidValue actorConfigId,
    required UuidValue classInstanceIdentityId,
    String? objectInstanceGraphBranchKey,
    UuidValue? objectInstanceGraphBranchId,
    List<UuidValue> requestedRoleConfigIds = const [],
    List<String> requestedRoleConfigNames = const [],
    String? reason,
    Map<String, dynamic>? evidence,
  }) {
    return _AdmitEnvironmentActorRequest(
      actorId: actorId,
      environmentId: environmentId,
      processId: processId,
      threadId: threadId,
      branchId: branchId,
      projectionHash: projectionHash,
      operation: operation ?? 'admit_actor',
      requestId: requestId,
      environmentProfileId: environmentProfileId,
      actorConfigId: actorConfigId,
      classInstanceIdentityId: classInstanceIdentityId,
      objectInstanceGraphBranchKey: objectInstanceGraphBranchKey ?? 'all',
      objectInstanceGraphBranchId: objectInstanceGraphBranchId,
      requestedRoleConfigIds: requestedRoleConfigIds,
      requestedRoleConfigNames: requestedRoleConfigNames,
      reason: reason,
      evidence: evidence ?? {},
    );
  }

  factory AdmitEnvironmentActorRequest.fromJson(Map<String, dynamic> json) =>
      _$AdmitEnvironmentActorRequestFromJson({
        ...json,
        if (!json.containsKey('operation')) 'operation': 'admit_actor',
        if (!json.containsKey('object_instance_graph_branch_key'))
          'object_instance_graph_branch_key': 'all',
        if (!json.containsKey('evidence')) 'evidence': {},
      });
}

@freezed
abstract class CapabilityArgument with _$CapabilityArgument {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CapabilityArgument.def({
    @UuidValueConverter() required UuidValue id,
    required String name,
    String? direction,
    String? type,
    @JsonKey(name: 'required') required bool required_,
    @JsonKey(name: 'default') Object? default_,
    @JsonKey(name: 'enum') List<dynamic>? enum_,
    String? description,
  }) = _CapabilityArgument;

  factory CapabilityArgument({
    UuidValue? id,
    required String name,
    String? direction,
    String? type,
    bool? required_,
    Object? default_,
    List<dynamic>? enum_,
    String? description,
  }) {
    return _CapabilityArgument(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      name: name,
      direction: direction,
      type: type,
      required_: required_ ?? true,
      default_: default_,
      enum_: enum_,
      description: description,
    );
  }

  factory CapabilityArgument.fromJson(Map<String, dynamic> json) =>
      _$CapabilityArgumentFromJson({
        ...json,
        if (!json.containsKey('required')) 'required': true,
      });
}

@freezed
abstract class CapabilityFunction with _$CapabilityFunction {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CapabilityFunction.def({
    @UuidValueConverter() required UuidValue id,
    required String name,
    String? summary,
    @UuidValueConverter() UuidValue? roleId,
    required bool isConstructor,
    @Default(const []) List<CapabilityArgument> inputs,
    @Default(const []) List<CapabilityArgument> outputs,
    @Default(const []) List<CapabilityArgument> arguments,
  }) = _CapabilityFunction;

  factory CapabilityFunction({
    UuidValue? id,
    required String name,
    String? summary,
    UuidValue? roleId,
    bool? isConstructor,
    List<CapabilityArgument> inputs = const [],
    List<CapabilityArgument> outputs = const [],
    List<CapabilityArgument> arguments = const [],
  }) {
    return _CapabilityFunction(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      name: name,
      summary: summary,
      roleId: roleId,
      isConstructor: isConstructor ?? false,
      inputs: inputs,
      outputs: outputs,
      arguments: arguments,
    );
  }

  factory CapabilityFunction.fromJson(Map<String, dynamic> json) =>
      _$CapabilityFunctionFromJson({
        ...json,
        if (!json.containsKey('is_constructor')) 'is_constructor': false,
      });
}

@freezed
abstract class CapabilityRole with _$CapabilityRole {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CapabilityRole.def({
    @UuidValueConverter() required UuidValue id,
    required String name,
    String? description,
    required Map<String, dynamic> metadata,
    @Default(const []) List<CapabilityFunction> functions,
  }) = _CapabilityRole;

  factory CapabilityRole({
    UuidValue? id,
    required String name,
    String? description,
    Map<String, dynamic>? metadata,
    List<CapabilityFunction> functions = const [],
  }) {
    return _CapabilityRole(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      name: name,
      description: description,
      metadata: metadata ?? {},
      functions: functions,
    );
  }

  factory CapabilityRole.fromJson(Map<String, dynamic> json) =>
      _$CapabilityRoleFromJson({
        ...json,
        if (!json.containsKey('metadata')) 'metadata': {},
      });
}

@freezed
abstract class CapabilityObject with _$CapabilityObject {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory CapabilityObject.def({
    @UuidValueConverter() required UuidValue id,
    required String name,
    String? description,
    @Default(const []) List<CapabilityFunction> functions,
  }) = _CapabilityObject;

  factory CapabilityObject({
    UuidValue? id,
    required String name,
    String? description,
    List<CapabilityFunction> functions = const [],
  }) {
    return _CapabilityObject(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      name: name,
      description: description,
      functions: functions,
    );
  }

  factory CapabilityObject.fromJson(Map<String, dynamic> json) =>
      _$CapabilityObjectFromJson(json);
}

@freezed
abstract class ResolvedRuntimeFunctionTarget
    with _$ResolvedRuntimeFunctionTarget {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ResolvedRuntimeFunctionTarget.def({
    String? queryKey,
    required String status,
    String? error,
    required String functionRef,
    @JsonKey(
      fromJson: InvokeFunctionCallTargetExtension.fromJson,
      toJson: InvokeFunctionCallTargetExtension.toJson,
    )
    required InvokeFunctionCallTarget callTarget,
    @UuidValueConverter() UuidValue? classConfigId,
    String? className,
    String? classFqn,
    @UuidValueConverter() UuidValue? classConfigFunctionConfigId,
    @UuidValueConverter() UuidValue? functionId,
    String? functionName,
    String? projectionHash,
    @UuidValueConverter() UuidValue? objectProjectionGraphId,
    @UuidValueConverter() UuidValue? objectProjectionGraphIdentityId,
    @Default(const []) List<String> candidateProjectionHashes,
    required Map<String, dynamic> evidence,
  }) = _ResolvedRuntimeFunctionTarget;

  factory ResolvedRuntimeFunctionTarget({
    String? queryKey,
    required String status,
    String? error,
    required String functionRef,
    InvokeFunctionCallTarget? callTarget,
    UuidValue? classConfigId,
    String? className,
    String? classFqn,
    UuidValue? classConfigFunctionConfigId,
    UuidValue? functionId,
    String? functionName,
    String? projectionHash,
    UuidValue? objectProjectionGraphId,
    UuidValue? objectProjectionGraphIdentityId,
    List<String> candidateProjectionHashes = const [],
    Map<String, dynamic>? evidence,
  }) {
    return _ResolvedRuntimeFunctionTarget(
      queryKey: queryKey,
      status: status,
      error: error,
      functionRef: functionRef,
      callTarget: callTarget ?? InvokeFunctionCallTarget.instance,
      classConfigId: classConfigId,
      className: className,
      classFqn: classFqn,
      classConfigFunctionConfigId: classConfigFunctionConfigId,
      functionId: functionId,
      functionName: functionName,
      projectionHash: projectionHash,
      objectProjectionGraphId: objectProjectionGraphId,
      objectProjectionGraphIdentityId: objectProjectionGraphIdentityId,
      candidateProjectionHashes: candidateProjectionHashes,
      evidence: evidence ?? {},
    );
  }

  factory ResolvedRuntimeFunctionTarget.fromJson(Map<String, dynamic> json) =>
      _$ResolvedRuntimeFunctionTargetFromJson({
        ...json,
        if (!json.containsKey('call_target')) 'call_target': 'instance',
        if (!json.containsKey('evidence')) 'evidence': {},
      });
}

@freezed
abstract class ResolvedRuntimeClassRef with _$ResolvedRuntimeClassRef {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ResolvedRuntimeClassRef.def({
    String? queryKey,
    required String status,
    String? error,
    required String classRef,
    @UuidValueConverter() UuidValue? classConfigId,
    String? className,
    String? classFqn,
    required Map<String, dynamic> evidence,
  }) = _ResolvedRuntimeClassRef;

  factory ResolvedRuntimeClassRef({
    String? queryKey,
    required String status,
    String? error,
    required String classRef,
    UuidValue? classConfigId,
    String? className,
    String? classFqn,
    Map<String, dynamic>? evidence,
  }) {
    return _ResolvedRuntimeClassRef(
      queryKey: queryKey,
      status: status,
      error: error,
      classRef: classRef,
      classConfigId: classConfigId,
      className: className,
      classFqn: classFqn,
      evidence: evidence ?? {},
    );
  }

  factory ResolvedRuntimeClassRef.fromJson(Map<String, dynamic> json) =>
      _$ResolvedRuntimeClassRefFromJson({
        ...json,
        if (!json.containsKey('evidence')) 'evidence': {},
      });
}

/// Environment-owned membership pointer to one Ontology authority.
/// Contract:
/// - This is not an OIG/OIGI inventory view.
/// - OIGI discovery remains behind the linked Ontology authority.
/// - Commit fields are mutation/read receipts for the Environment lane only.
@freezed
abstract class EnvironmentOntologyMembership
    with _$EnvironmentOntologyMembership {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentOntologyMembership.def({
    @UuidValueConverter() UuidValue? environmentOntologyId,
    @UuidValueConverter() required UuidValue ontologyId,
    required String role,
    required String status,
    String? title,
    String? description,
    @UuidValueConverter() UuidValue? commitId,
    String? graphHashPost,
    required Map<String, dynamic> evidence,
  }) = _EnvironmentOntologyMembership;

  factory EnvironmentOntologyMembership({
    UuidValue? environmentOntologyId,
    required UuidValue ontologyId,
    String? role,
    String? status,
    String? title,
    String? description,
    UuidValue? commitId,
    String? graphHashPost,
    Map<String, dynamic>? evidence,
  }) {
    return _EnvironmentOntologyMembership(
      environmentOntologyId: environmentOntologyId,
      ontologyId: ontologyId,
      role: role ?? 'runtime',
      status: status ?? 'active',
      title: title,
      description: description,
      commitId: commitId,
      graphHashPost: graphHashPost,
      evidence: evidence ?? {},
    );
  }

  factory EnvironmentOntologyMembership.fromJson(Map<String, dynamic> json) =>
      _$EnvironmentOntologyMembershipFromJson({
        ...json,
        if (!json.containsKey('role')) 'role': 'runtime',
        if (!json.containsKey('status')) 'status': 'active',
        if (!json.containsKey('evidence')) 'evidence': {},
      });
}

@freezed
abstract class EnvironmentProfileProjectionSpec
    with _$EnvironmentProfileProjectionSpec {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentProfileProjectionSpec.def({
    required String objectProjectionGraphRef,
    String? viewKey,
    String? narrative,
    String? intent,
    int? position,
    required bool isDefault,
  }) = _EnvironmentProfileProjectionSpec;

  factory EnvironmentProfileProjectionSpec({
    required String objectProjectionGraphRef,
    String? viewKey,
    String? narrative,
    String? intent,
    int? position,
    bool? isDefault,
  }) {
    return _EnvironmentProfileProjectionSpec(
      objectProjectionGraphRef: objectProjectionGraphRef,
      viewKey: viewKey,
      narrative: narrative,
      intent: intent,
      position: position,
      isDefault: isDefault ?? false,
    );
  }

  factory EnvironmentProfileProjectionSpec.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentProfileProjectionSpecFromJson({
    ...json,
    if (!json.containsKey('is_default')) 'is_default': false,
  });
}

@freezed
abstract class EnvironmentProfileLayoutSectionSpec
    with _$EnvironmentProfileLayoutSectionSpec {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentProfileLayoutSectionSpec.def({
    required String sectionKey,
    @UuidValueConverter() UuidValue? layoutConfigSectionConfigId,
    String? objectProjectionGraphRef,
    String? viewKey,
    String? key,
    int? position,
    required bool isDefault,
    String? narrative,
    String? intent,
  }) = _EnvironmentProfileLayoutSectionSpec;

  factory EnvironmentProfileLayoutSectionSpec({
    required String sectionKey,
    UuidValue? layoutConfigSectionConfigId,
    String? objectProjectionGraphRef,
    String? viewKey,
    String? key,
    int? position,
    bool? isDefault,
    String? narrative,
    String? intent,
  }) {
    return _EnvironmentProfileLayoutSectionSpec(
      sectionKey: sectionKey,
      layoutConfigSectionConfigId: layoutConfigSectionConfigId,
      objectProjectionGraphRef: objectProjectionGraphRef,
      viewKey: viewKey,
      key: key,
      position: position,
      isDefault: isDefault ?? false,
      narrative: narrative,
      intent: intent,
    );
  }

  factory EnvironmentProfileLayoutSectionSpec.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentProfileLayoutSectionSpecFromJson({
    ...json,
    if (!json.containsKey('is_default')) 'is_default': false,
  });
}

@freezed
abstract class EnvironmentProfileLayoutConfigSpec
    with _$EnvironmentProfileLayoutConfigSpec {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentProfileLayoutConfigSpec.def({
    String? layoutKey,
    @UuidValueConverter() UuidValue? layoutConfigId,
    String? key,
    int? position,
    String? narrative,
    String? intent,
    @Default(const []) List<EnvironmentProfileLayoutSectionSpec> sections,
  }) = _EnvironmentProfileLayoutConfigSpec;

  factory EnvironmentProfileLayoutConfigSpec({
    String? layoutKey,
    UuidValue? layoutConfigId,
    String? key,
    int? position,
    String? narrative,
    String? intent,
    List<EnvironmentProfileLayoutSectionSpec> sections = const [],
  }) {
    return _EnvironmentProfileLayoutConfigSpec(
      layoutKey: layoutKey,
      layoutConfigId: layoutConfigId,
      key: key,
      position: position,
      narrative: narrative,
      intent: intent,
      sections: sections,
    );
  }

  factory EnvironmentProfileLayoutConfigSpec.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentProfileLayoutConfigSpecFromJson(json);
}

@freezed
abstract class EnvironmentProfileThreadConfigSpec
    with _$EnvironmentProfileThreadConfigSpec {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentProfileThreadConfigSpec.def({
    required String key,
    String? title,
    String? description,
    String? workspaceViewKey,
    int? position,
    required bool isDefault,
    String? narrative,
    String? intent,
    String? statePromptTemplate,
    @Default(const []) List<EnvironmentProfileProjectionSpec> projectionRefs,
    @Default(const []) List<EnvironmentProfileLayoutConfigSpec> layoutConfigs,
  }) = _EnvironmentProfileThreadConfigSpec;

  factory EnvironmentProfileThreadConfigSpec({
    required String key,
    String? title,
    String? description,
    String? workspaceViewKey,
    int? position,
    bool? isDefault,
    String? narrative,
    String? intent,
    String? statePromptTemplate,
    List<EnvironmentProfileProjectionSpec> projectionRefs = const [],
    List<EnvironmentProfileLayoutConfigSpec> layoutConfigs = const [],
  }) {
    return _EnvironmentProfileThreadConfigSpec(
      key: key,
      title: title,
      description: description,
      workspaceViewKey: workspaceViewKey,
      position: position,
      isDefault: isDefault ?? false,
      narrative: narrative,
      intent: intent,
      statePromptTemplate: statePromptTemplate,
      projectionRefs: projectionRefs,
      layoutConfigs: layoutConfigs,
    );
  }

  factory EnvironmentProfileThreadConfigSpec.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentProfileThreadConfigSpecFromJson({
    ...json,
    if (!json.containsKey('is_default')) 'is_default': false,
  });
}

@freezed
abstract class EnvironmentProfileProcessConfigSpec
    with _$EnvironmentProfileProcessConfigSpec {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentProfileProcessConfigSpec.def({
    required String key,
    required String type,
    String? title,
    String? description,
    String? shape,
    int? position,
    required bool isDefault,
    String? narrative,
    String? intent,
    @Default(const []) List<EnvironmentProfileThreadConfigSpec> threadConfigs,
  }) = _EnvironmentProfileProcessConfigSpec;

  factory EnvironmentProfileProcessConfigSpec({
    required String key,
    required String type,
    String? title,
    String? description,
    String? shape,
    int? position,
    bool? isDefault,
    String? narrative,
    String? intent,
    List<EnvironmentProfileThreadConfigSpec> threadConfigs = const [],
  }) {
    return _EnvironmentProfileProcessConfigSpec(
      key: key,
      type: type,
      title: title,
      description: description,
      shape: shape,
      position: position,
      isDefault: isDefault ?? false,
      narrative: narrative,
      intent: intent,
      threadConfigs: threadConfigs,
    );
  }

  factory EnvironmentProfileProcessConfigSpec.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentProfileProcessConfigSpecFromJson({
    ...json,
    if (!json.containsKey('is_default')) 'is_default': false,
  });
}

@freezed
abstract class EnvironmentProfileTopologyLayoutSeedSpec
    with _$EnvironmentProfileTopologyLayoutSeedSpec {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentProfileTopologyLayoutSeedSpec.def({
    required String layoutKey,
    String? key,
    int? position,
    required bool activateOnSeed,
    String? narrative,
    String? intent,
  }) = _EnvironmentProfileTopologyLayoutSeedSpec;

  factory EnvironmentProfileTopologyLayoutSeedSpec({
    required String layoutKey,
    String? key,
    int? position,
    bool? activateOnSeed,
    String? narrative,
    String? intent,
  }) {
    return _EnvironmentProfileTopologyLayoutSeedSpec(
      layoutKey: layoutKey,
      key: key,
      position: position,
      activateOnSeed: activateOnSeed ?? false,
      narrative: narrative,
      intent: intent,
    );
  }

  factory EnvironmentProfileTopologyLayoutSeedSpec.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentProfileTopologyLayoutSeedSpecFromJson({
    ...json,
    if (!json.containsKey('activate_on_seed')) 'activate_on_seed': false,
  });
}

@freezed
abstract class EnvironmentProfileTopologyThreadSeedSpec
    with _$EnvironmentProfileTopologyThreadSeedSpec {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentProfileTopologyThreadSeedSpec.def({
    required String threadConfigKey,
    required String threadKey,
    String? key,
    String? title,
    String? description,
    int? position,
    required bool isMain,
    String? narrative,
    String? intent,
    @Default(const [])
    List<EnvironmentProfileTopologyLayoutSeedSpec> layoutSeeds,
  }) = _EnvironmentProfileTopologyThreadSeedSpec;

  factory EnvironmentProfileTopologyThreadSeedSpec({
    required String threadConfigKey,
    required String threadKey,
    String? key,
    String? title,
    String? description,
    int? position,
    bool? isMain,
    String? narrative,
    String? intent,
    List<EnvironmentProfileTopologyLayoutSeedSpec> layoutSeeds = const [],
  }) {
    return _EnvironmentProfileTopologyThreadSeedSpec(
      threadConfigKey: threadConfigKey,
      threadKey: threadKey,
      key: key,
      title: title,
      description: description,
      position: position,
      isMain: isMain ?? false,
      narrative: narrative,
      intent: intent,
      layoutSeeds: layoutSeeds,
    );
  }

  factory EnvironmentProfileTopologyThreadSeedSpec.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentProfileTopologyThreadSeedSpecFromJson({
    ...json,
    if (!json.containsKey('is_main')) 'is_main': false,
  });
}

@freezed
abstract class EnvironmentProfileTopologyProcessSeedSpec
    with _$EnvironmentProfileTopologyProcessSeedSpec {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentProfileTopologyProcessSeedSpec.def({
    required String processConfigKey,
    required String processKey,
    String? key,
    String? title,
    String? description,
    int? position,
    String? narrative,
    String? intent,
    @Default(const [])
    List<EnvironmentProfileTopologyThreadSeedSpec> threadSeeds,
  }) = _EnvironmentProfileTopologyProcessSeedSpec;

  factory EnvironmentProfileTopologyProcessSeedSpec({
    required String processConfigKey,
    required String processKey,
    String? key,
    String? title,
    String? description,
    int? position,
    String? narrative,
    String? intent,
    List<EnvironmentProfileTopologyThreadSeedSpec> threadSeeds = const [],
  }) {
    return _EnvironmentProfileTopologyProcessSeedSpec(
      processConfigKey: processConfigKey,
      processKey: processKey,
      key: key,
      title: title,
      description: description,
      position: position,
      narrative: narrative,
      intent: intent,
      threadSeeds: threadSeeds,
    );
  }

  factory EnvironmentProfileTopologyProcessSeedSpec.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentProfileTopologyProcessSeedSpecFromJson(json);
}

@freezed
abstract class EnvironmentProfileTopologySeedSpec
    with _$EnvironmentProfileTopologySeedSpec {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentProfileTopologySeedSpec.def({
    required String key,
    String? title,
    String? description,
    String? narrative,
    @Default(const [])
    List<EnvironmentProfileTopologyProcessSeedSpec> processSeeds,
  }) = _EnvironmentProfileTopologySeedSpec;

  factory EnvironmentProfileTopologySeedSpec({
    required String key,
    String? title,
    String? description,
    String? narrative,
    List<EnvironmentProfileTopologyProcessSeedSpec> processSeeds = const [],
  }) {
    return _EnvironmentProfileTopologySeedSpec(
      key: key,
      title: title,
      description: description,
      narrative: narrative,
      processSeeds: processSeeds,
    );
  }

  factory EnvironmentProfileTopologySeedSpec.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentProfileTopologySeedSpecFromJson(json);
}

@freezed
abstract class EnvironmentProfileRuntimeMountReceipt
    with _$EnvironmentProfileRuntimeMountReceipt {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentProfileRuntimeMountReceipt.def({
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() required UuidValue environmentProfileId,
    required String topologySeedKey,
    @UuidValueConverter() UuidValue? processConfigId,
    required String processKey,
    @UuidValueConverter() required UuidValue processId,
    @UuidValueConverter() UuidValue? threadConfigId,
    required String threadKey,
    @UuidValueConverter() required UuidValue threadId,
    @UuidValueConverter() UuidValue? threadLayoutConfigId,
    String? layoutKey,
    @UuidValueConverter() UuidValue? layoutConfigId,
    @UuidValueConverter() UuidValue? layoutId,
    @UuidValueConverter() UuidValue? threadLayoutId,
    required bool activateOnSeed,
    required String status,
  }) = _EnvironmentProfileRuntimeMountReceipt;

  factory EnvironmentProfileRuntimeMountReceipt({
    required UuidValue environmentId,
    required UuidValue environmentProfileId,
    required String topologySeedKey,
    UuidValue? processConfigId,
    required String processKey,
    required UuidValue processId,
    UuidValue? threadConfigId,
    required String threadKey,
    required UuidValue threadId,
    UuidValue? threadLayoutConfigId,
    String? layoutKey,
    UuidValue? layoutConfigId,
    UuidValue? layoutId,
    UuidValue? threadLayoutId,
    bool? activateOnSeed,
    String? status,
  }) {
    return _EnvironmentProfileRuntimeMountReceipt(
      environmentId: environmentId,
      environmentProfileId: environmentProfileId,
      topologySeedKey: topologySeedKey,
      processConfigId: processConfigId,
      processKey: processKey,
      processId: processId,
      threadConfigId: threadConfigId,
      threadKey: threadKey,
      threadId: threadId,
      threadLayoutConfigId: threadLayoutConfigId,
      layoutKey: layoutKey,
      layoutConfigId: layoutConfigId,
      layoutId: layoutId,
      threadLayoutId: threadLayoutId,
      activateOnSeed: activateOnSeed ?? false,
      status: status ?? 'succeeded',
    );
  }

  factory EnvironmentProfileRuntimeMountReceipt.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentProfileRuntimeMountReceiptFromJson({
    ...json,
    if (!json.containsKey('activate_on_seed')) 'activate_on_seed': false,
    if (!json.containsKey('status')) 'status': 'succeeded',
  });
}

@freezed
abstract class EnvironmentProfileInstallSpec
    with _$EnvironmentProfileInstallSpec {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentProfileInstallSpec.def({
    String? key,
    String? title,
    String? description,
    String? narrative,
    @Default(const []) List<EnvironmentProfileProcessConfigSpec> processConfigs,
  }) = _EnvironmentProfileInstallSpec;

  factory EnvironmentProfileInstallSpec({
    String? key,
    String? title,
    String? description,
    String? narrative,
    List<EnvironmentProfileProcessConfigSpec> processConfigs = const [],
  }) {
    return _EnvironmentProfileInstallSpec(
      key: key,
      title: title,
      description: description,
      narrative: narrative,
      processConfigs: processConfigs,
    );
  }

  factory EnvironmentProfileInstallSpec.fromJson(Map<String, dynamic> json) =>
      _$EnvironmentProfileInstallSpecFromJson(json);
}

@freezed
abstract class UpsertEnvironmentProfileRequest
    with _$UpsertEnvironmentProfileRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory UpsertEnvironmentProfileRequest.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String operation,
    @UuidValueConverter() UuidValue? environmentConfigId,
    required EnvironmentProfileInstallSpec profile,
    @Default(const []) List<EnvironmentProfileTopologySeedSpec> topologySeeds,
    required bool validateOnly,
  }) = _UpsertEnvironmentProfileRequest;

  factory UpsertEnvironmentProfileRequest({
    UuidValue? actorId,
    required UuidValue environmentId,
    UuidValue? processId,
    UuidValue? threadId,
    UuidValue? branchId,
    String? projectionHash,
    String? operation,
    UuidValue? environmentConfigId,
    required EnvironmentProfileInstallSpec profile,
    List<EnvironmentProfileTopologySeedSpec> topologySeeds = const [],
    bool? validateOnly,
  }) {
    return _UpsertEnvironmentProfileRequest(
      actorId: actorId,
      environmentId: environmentId,
      processId: processId,
      threadId: threadId,
      branchId: branchId,
      projectionHash: projectionHash,
      operation: operation ?? 'upsert_environment_profile',
      environmentConfigId: environmentConfigId,
      profile: profile,
      topologySeeds: topologySeeds,
      validateOnly: validateOnly ?? false,
    );
  }

  factory UpsertEnvironmentProfileRequest.fromJson(Map<String, dynamic> json) =>
      _$UpsertEnvironmentProfileRequestFromJson({
        ...json,
        if (!json.containsKey('operation'))
          'operation': 'upsert_environment_profile',
        if (!json.containsKey('validate_only')) 'validate_only': false,
      });
}

@freezed
abstract class UpsertEnvironmentProfileResponse
    with _$UpsertEnvironmentProfileResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory UpsertEnvironmentProfileResponse.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String operation,
    required String status,
    String? error,
    @UuidValueConverter() UuidValue? environmentConfigId,
    @UuidValueConverter() UuidValue? environmentProfileConfigId,
    @UuidValueConverter() UuidValue? environmentProfileId,
    @UuidValueListConverter()
    @Default(const [])
    List<UuidValue> processConfigIds,
    @UuidValueListConverter()
    @Default(const [])
    List<UuidValue> threadConfigIds,
    @UuidValueListConverter()
    @Default(const [])
    List<UuidValue> threadProjectionAssociationIds,
    @UuidValueListConverter()
    @Default(const [])
    List<UuidValue> threadLayoutConfigIds,
    @UuidValueListConverter()
    @Default(const [])
    List<UuidValue> topologySeedIds,
    @UuidValueListConverter()
    @Default(const [])
    List<UuidValue> topologyProcessSeedIds,
    @UuidValueListConverter()
    @Default(const [])
    List<UuidValue> topologyThreadSeedIds,
    @UuidValueListConverter()
    @Default(const [])
    List<UuidValue> topologyThreadLayoutSeedIds,
  }) = _UpsertEnvironmentProfileResponse;

  factory UpsertEnvironmentProfileResponse({
    UuidValue? actorId,
    required UuidValue environmentId,
    UuidValue? processId,
    UuidValue? threadId,
    UuidValue? branchId,
    String? projectionHash,
    String? operation,
    required String status,
    String? error,
    UuidValue? environmentConfigId,
    UuidValue? environmentProfileConfigId,
    UuidValue? environmentProfileId,
    List<UuidValue> processConfigIds = const [],
    List<UuidValue> threadConfigIds = const [],
    List<UuidValue> threadProjectionAssociationIds = const [],
    List<UuidValue> threadLayoutConfigIds = const [],
    List<UuidValue> topologySeedIds = const [],
    List<UuidValue> topologyProcessSeedIds = const [],
    List<UuidValue> topologyThreadSeedIds = const [],
    List<UuidValue> topologyThreadLayoutSeedIds = const [],
  }) {
    return _UpsertEnvironmentProfileResponse(
      actorId: actorId,
      environmentId: environmentId,
      processId: processId,
      threadId: threadId,
      branchId: branchId,
      projectionHash: projectionHash,
      operation: operation ?? 'upsert_environment_profile',
      status: status,
      error: error,
      environmentConfigId: environmentConfigId,
      environmentProfileConfigId: environmentProfileConfigId,
      environmentProfileId: environmentProfileId,
      processConfigIds: processConfigIds,
      threadConfigIds: threadConfigIds,
      threadProjectionAssociationIds: threadProjectionAssociationIds,
      threadLayoutConfigIds: threadLayoutConfigIds,
      topologySeedIds: topologySeedIds,
      topologyProcessSeedIds: topologyProcessSeedIds,
      topologyThreadSeedIds: topologyThreadSeedIds,
      topologyThreadLayoutSeedIds: topologyThreadLayoutSeedIds,
    );
  }

  factory UpsertEnvironmentProfileResponse.fromJson(
    Map<String, dynamic> json,
  ) => _$UpsertEnvironmentProfileResponseFromJson({
    ...json,
    if (!json.containsKey('operation'))
      'operation': 'upsert_environment_profile',
  });
}

@freezed
abstract class ProvisionEnvironmentProfileRequest
    with _$ProvisionEnvironmentProfileRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ProvisionEnvironmentProfileRequest.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String operation,
    @UuidValueConverter() UuidValue? environmentProfileId,
    required String topologySeedKey,
    required bool validateOnly,
  }) = _ProvisionEnvironmentProfileRequest;

  factory ProvisionEnvironmentProfileRequest({
    UuidValue? actorId,
    required UuidValue environmentId,
    UuidValue? processId,
    UuidValue? threadId,
    UuidValue? branchId,
    String? projectionHash,
    String? operation,
    UuidValue? environmentProfileId,
    required String topologySeedKey,
    bool? validateOnly,
  }) {
    return _ProvisionEnvironmentProfileRequest(
      actorId: actorId,
      environmentId: environmentId,
      processId: processId,
      threadId: threadId,
      branchId: branchId,
      projectionHash: projectionHash,
      operation: operation ?? 'provision_environment_profile',
      environmentProfileId: environmentProfileId,
      topologySeedKey: topologySeedKey,
      validateOnly: validateOnly ?? false,
    );
  }

  factory ProvisionEnvironmentProfileRequest.fromJson(
    Map<String, dynamic> json,
  ) => _$ProvisionEnvironmentProfileRequestFromJson({
    ...json,
    if (!json.containsKey('operation'))
      'operation': 'provision_environment_profile',
    if (!json.containsKey('validate_only')) 'validate_only': false,
  });
}

@freezed
abstract class ProvisionEnvironmentProfileResponse
    with _$ProvisionEnvironmentProfileResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ProvisionEnvironmentProfileResponse.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String operation,
    required String status,
    String? error,
    @UuidValueConverter() UuidValue? environmentProfileId,
    @UuidValueListConverter() @Default(const []) List<UuidValue> processIds,
    @UuidValueListConverter() @Default(const []) List<UuidValue> threadIds,
    @UuidValueListConverter()
    @Default(const [])
    List<UuidValue> threadLayoutIds,
    @Default(const [])
    List<EnvironmentProfileRuntimeMountReceipt> runtimeMounts,
  }) = _ProvisionEnvironmentProfileResponse;

  factory ProvisionEnvironmentProfileResponse({
    UuidValue? actorId,
    required UuidValue environmentId,
    UuidValue? processId,
    UuidValue? threadId,
    UuidValue? branchId,
    String? projectionHash,
    String? operation,
    required String status,
    String? error,
    UuidValue? environmentProfileId,
    List<UuidValue> processIds = const [],
    List<UuidValue> threadIds = const [],
    List<UuidValue> threadLayoutIds = const [],
    List<EnvironmentProfileRuntimeMountReceipt> runtimeMounts = const [],
  }) {
    return _ProvisionEnvironmentProfileResponse(
      actorId: actorId,
      environmentId: environmentId,
      processId: processId,
      threadId: threadId,
      branchId: branchId,
      projectionHash: projectionHash,
      operation: operation ?? 'provision_environment_profile',
      status: status,
      error: error,
      environmentProfileId: environmentProfileId,
      processIds: processIds,
      threadIds: threadIds,
      threadLayoutIds: threadLayoutIds,
      runtimeMounts: runtimeMounts,
    );
  }

  factory ProvisionEnvironmentProfileResponse.fromJson(
    Map<String, dynamic> json,
  ) => _$ProvisionEnvironmentProfileResponseFromJson({
    ...json,
    if (!json.containsKey('operation'))
      'operation': 'provision_environment_profile',
  });
}

@freezed
abstract class EnvironmentActorAdmissionRoleEligibility
    with _$EnvironmentActorAdmissionRoleEligibility {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentActorAdmissionRoleEligibility.def({
    @UuidValueConverter() required UuidValue environmentProfileActorConfigId,
    @UuidValueConverter() required UuidValue actorConfigRoleConfigId,
    @UuidValueConverter() required UuidValue roleConfigId,
    String? roleConfigName,
  }) = _EnvironmentActorAdmissionRoleEligibility;

  factory EnvironmentActorAdmissionRoleEligibility({
    required UuidValue environmentProfileActorConfigId,
    required UuidValue actorConfigRoleConfigId,
    required UuidValue roleConfigId,
    String? roleConfigName,
  }) {
    return _EnvironmentActorAdmissionRoleEligibility(
      environmentProfileActorConfigId: environmentProfileActorConfigId,
      actorConfigRoleConfigId: actorConfigRoleConfigId,
      roleConfigId: roleConfigId,
      roleConfigName: roleConfigName,
    );
  }

  factory EnvironmentActorAdmissionRoleEligibility.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentActorAdmissionRoleEligibilityFromJson(json);
}

@freezed
abstract class EnvironmentActorAdmissionRoleBinding
    with _$EnvironmentActorAdmissionRoleBinding {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentActorAdmissionRoleBinding.def({
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
  }) = _EnvironmentActorAdmissionRoleBinding;

  factory EnvironmentActorAdmissionRoleBinding({
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
    String? objectInstanceGraphBranchKey,
    UuidValue? objectInstanceGraphBranchId,
  }) {
    return _EnvironmentActorAdmissionRoleBinding(
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
      objectInstanceGraphBranchKey: objectInstanceGraphBranchKey ?? 'all',
      objectInstanceGraphBranchId: objectInstanceGraphBranchId,
    );
  }

  factory EnvironmentActorAdmissionRoleBinding.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentActorAdmissionRoleBindingFromJson({
    ...json,
    if (!json.containsKey('object_instance_graph_branch_key'))
      'object_instance_graph_branch_key': 'all',
  });
}

@freezed
abstract class EnvironmentActorAdmissionReceipt
    with _$EnvironmentActorAdmissionReceipt {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentActorAdmissionReceipt.def({
    required bool accepted,
    required String status,
    String? error,
    String? reason,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() required UuidValue environmentProfileId,
    @UuidValueConverter() UuidValue? environmentProfileActorConfigId,
    @UuidValueConverter() UuidValue? actorConfigId,
    @UuidValueConverter() UuidValue? classInstanceIdentityId,
    required String objectInstanceGraphBranchKey,
    @UuidValueConverter() UuidValue? objectInstanceGraphBranchId,
    @UuidValueListConverter()
    @Default(const [])
    List<UuidValue> requestedRoleConfigIds,
    @Default(const []) List<String> requestedRoleConfigNames,
    @Default(const [])
    List<EnvironmentActorAdmissionRoleEligibility> eligibleRoles,
    @Default(const []) List<EnvironmentActorAdmissionRoleBinding> bindings,
    @Default(const []) List<String> blockers,
    required Map<String, dynamic> evidence,
  }) = _EnvironmentActorAdmissionReceipt;

  factory EnvironmentActorAdmissionReceipt({
    bool? accepted,
    required String status,
    String? error,
    String? reason,
    UuidValue? actorId,
    required UuidValue environmentId,
    required UuidValue environmentProfileId,
    UuidValue? environmentProfileActorConfigId,
    UuidValue? actorConfigId,
    UuidValue? classInstanceIdentityId,
    String? objectInstanceGraphBranchKey,
    UuidValue? objectInstanceGraphBranchId,
    List<UuidValue> requestedRoleConfigIds = const [],
    List<String> requestedRoleConfigNames = const [],
    List<EnvironmentActorAdmissionRoleEligibility> eligibleRoles = const [],
    List<EnvironmentActorAdmissionRoleBinding> bindings = const [],
    List<String> blockers = const [],
    Map<String, dynamic>? evidence,
  }) {
    return _EnvironmentActorAdmissionReceipt(
      accepted: accepted ?? false,
      status: status,
      error: error,
      reason: reason,
      actorId: actorId,
      environmentId: environmentId,
      environmentProfileId: environmentProfileId,
      environmentProfileActorConfigId: environmentProfileActorConfigId,
      actorConfigId: actorConfigId,
      classInstanceIdentityId: classInstanceIdentityId,
      objectInstanceGraphBranchKey: objectInstanceGraphBranchKey ?? 'all',
      objectInstanceGraphBranchId: objectInstanceGraphBranchId,
      requestedRoleConfigIds: requestedRoleConfigIds,
      requestedRoleConfigNames: requestedRoleConfigNames,
      eligibleRoles: eligibleRoles,
      bindings: bindings,
      blockers: blockers,
      evidence: evidence ?? {},
    );
  }

  factory EnvironmentActorAdmissionReceipt.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentActorAdmissionReceiptFromJson({
    ...json,
    if (!json.containsKey('accepted')) 'accepted': false,
    if (!json.containsKey('object_instance_graph_branch_key'))
      'object_instance_graph_branch_key': 'all',
    if (!json.containsKey('evidence')) 'evidence': {},
  });
}

@freezed
abstract class AdmitEnvironmentActorResponse
    with _$AdmitEnvironmentActorResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory AdmitEnvironmentActorResponse.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String operation,
    @UuidValueConverter() UuidValue? requestId,
    required bool accepted,
    required String status,
    String? error,
    required EnvironmentActorAdmissionReceipt receipt,
    required Map<String, dynamic> evidence,
  }) = _AdmitEnvironmentActorResponse;

  factory AdmitEnvironmentActorResponse({
    UuidValue? actorId,
    required UuidValue environmentId,
    UuidValue? processId,
    UuidValue? threadId,
    UuidValue? branchId,
    String? projectionHash,
    String? operation,
    UuidValue? requestId,
    bool? accepted,
    required String status,
    String? error,
    required EnvironmentActorAdmissionReceipt receipt,
    Map<String, dynamic>? evidence,
  }) {
    return _AdmitEnvironmentActorResponse(
      actorId: actorId,
      environmentId: environmentId,
      processId: processId,
      threadId: threadId,
      branchId: branchId,
      projectionHash: projectionHash,
      operation: operation ?? 'admit_actor',
      requestId: requestId,
      accepted: accepted ?? false,
      status: status,
      error: error,
      receipt: receipt,
      evidence: evidence ?? {},
    );
  }

  factory AdmitEnvironmentActorResponse.fromJson(Map<String, dynamic> json) =>
      _$AdmitEnvironmentActorResponseFromJson({
        ...json,
        if (!json.containsKey('operation')) 'operation': 'admit_actor',
        if (!json.containsKey('accepted')) 'accepted': false,
        if (!json.containsKey('evidence')) 'evidence': {},
      });
}

/// Start a shared EnvironmentSession after accepted Environment admission.
/// Contract:
/// - Admission receipt is required and must match actor/environment/profile.
/// - Creates or resolves a session under the EnvironmentProfile and joins the
/// admitted actor as a member.
/// - Resolves the Environment-owned default navigation context only when
/// `resolve_default_navigation_context` is true.
/// - Callers never supply Process/Thread defaults through this operation.
@freezed
abstract class StartEnvironmentSessionRequest
    with _$StartEnvironmentSessionRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory StartEnvironmentSessionRequest.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String operation,
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() required UuidValue environmentProfileId,
    @UuidValueConverter() required UuidValue environmentSessionConfigId,
    required EnvironmentActorAdmissionReceipt admissionReceipt,
    required String sessionKey,
    String? title,
    String? description,
    String? purpose,
    String? sourceKind,
    String? sourceRef,
    required bool resolveDefaultNavigationContext,
    required Map<String, dynamic> metadata,
  }) = _StartEnvironmentSessionRequest;

  factory StartEnvironmentSessionRequest({
    UuidValue? actorId,
    required UuidValue environmentId,
    UuidValue? processId,
    UuidValue? threadId,
    UuidValue? branchId,
    String? projectionHash,
    String? operation,
    UuidValue? requestId,
    required UuidValue environmentProfileId,
    required UuidValue environmentSessionConfigId,
    required EnvironmentActorAdmissionReceipt admissionReceipt,
    required String sessionKey,
    String? title,
    String? description,
    String? purpose,
    String? sourceKind,
    String? sourceRef,
    bool? resolveDefaultNavigationContext,
    Map<String, dynamic>? metadata,
  }) {
    return _StartEnvironmentSessionRequest(
      actorId: actorId,
      environmentId: environmentId,
      processId: processId,
      threadId: threadId,
      branchId: branchId,
      projectionHash: projectionHash,
      operation: operation ?? 'start_environment_session',
      requestId: requestId,
      environmentProfileId: environmentProfileId,
      environmentSessionConfigId: environmentSessionConfigId,
      admissionReceipt: admissionReceipt,
      sessionKey: sessionKey,
      title: title,
      description: description,
      purpose: purpose,
      sourceKind: sourceKind,
      sourceRef: sourceRef,
      resolveDefaultNavigationContext: resolveDefaultNavigationContext ?? false,
      metadata: metadata ?? {},
    );
  }

  factory StartEnvironmentSessionRequest.fromJson(Map<String, dynamic> json) =>
      _$StartEnvironmentSessionRequestFromJson({
        ...json,
        if (!json.containsKey('operation'))
          'operation': 'start_environment_session',
        if (!json.containsKey('resolve_default_navigation_context'))
          'resolve_default_navigation_context': false,
        if (!json.containsKey('metadata')) 'metadata': {},
      });
}

/// Join an existing shared EnvironmentSession after accepted Environment admission.
/// Contract:
/// - Admission receipt is required and must match actor/environment/profile.
/// - Resolves the Environment-owned default navigation context only when
/// `resolve_default_navigation_context` is true.
/// - Callers never supply Process/Thread defaults through this operation.
@freezed
abstract class JoinEnvironmentSessionRequest
    with _$JoinEnvironmentSessionRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory JoinEnvironmentSessionRequest.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String operation,
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() required UuidValue environmentProfileId,
    @UuidValueConverter() required UuidValue environmentSessionId,
    required EnvironmentActorAdmissionReceipt admissionReceipt,
    String? reason,
    required bool resolveDefaultNavigationContext,
    required Map<String, dynamic> metadata,
  }) = _JoinEnvironmentSessionRequest;

  factory JoinEnvironmentSessionRequest({
    UuidValue? actorId,
    required UuidValue environmentId,
    UuidValue? processId,
    UuidValue? threadId,
    UuidValue? branchId,
    String? projectionHash,
    String? operation,
    UuidValue? requestId,
    required UuidValue environmentProfileId,
    required UuidValue environmentSessionId,
    required EnvironmentActorAdmissionReceipt admissionReceipt,
    String? reason,
    bool? resolveDefaultNavigationContext,
    Map<String, dynamic>? metadata,
  }) {
    return _JoinEnvironmentSessionRequest(
      actorId: actorId,
      environmentId: environmentId,
      processId: processId,
      threadId: threadId,
      branchId: branchId,
      projectionHash: projectionHash,
      operation: operation ?? 'join_environment_session',
      requestId: requestId,
      environmentProfileId: environmentProfileId,
      environmentSessionId: environmentSessionId,
      admissionReceipt: admissionReceipt,
      reason: reason,
      resolveDefaultNavigationContext: resolveDefaultNavigationContext ?? false,
      metadata: metadata ?? {},
    );
  }

  factory JoinEnvironmentSessionRequest.fromJson(Map<String, dynamic> json) =>
      _$JoinEnvironmentSessionRequestFromJson({
        ...json,
        if (!json.containsKey('operation'))
          'operation': 'join_environment_session',
        if (!json.containsKey('resolve_default_navigation_context'))
          'resolve_default_navigation_context': false,
        if (!json.containsKey('metadata')) 'metadata': {},
      });
}

/// Describe a shared EnvironmentSession.
/// Contract:
/// - Read model only; does not grant admission or navigation.
@freezed
abstract class DescribeEnvironmentSessionRequest
    with _$DescribeEnvironmentSessionRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory DescribeEnvironmentSessionRequest.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String operation,
    @UuidValueConverter() required UuidValue environmentSessionId,
  }) = _DescribeEnvironmentSessionRequest;

  factory DescribeEnvironmentSessionRequest({
    UuidValue? actorId,
    required UuidValue environmentId,
    UuidValue? processId,
    UuidValue? threadId,
    UuidValue? branchId,
    String? projectionHash,
    String? operation,
    required UuidValue environmentSessionId,
  }) {
    return _DescribeEnvironmentSessionRequest(
      actorId: actorId,
      environmentId: environmentId,
      processId: processId,
      threadId: threadId,
      branchId: branchId,
      projectionHash: projectionHash,
      operation: operation ?? 'describe_environment_session',
      environmentSessionId: environmentSessionId,
    );
  }

  factory DescribeEnvironmentSessionRequest.fromJson(
    Map<String, dynamic> json,
  ) => _$DescribeEnvironmentSessionRequestFromJson({
    ...json,
    if (!json.containsKey('operation'))
      'operation': 'describe_environment_session',
  });
}

@freezed
abstract class EnvironmentSessionIdentityEvidence
    with _$EnvironmentSessionIdentityEvidence {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentSessionIdentityEvidence.def({
    SessionSummary? identitySession,
    SessionMemberSummary? identityMember,
    @Default(const []) List<SessionMemberActorRoleSummary> identityActorRoles,
    required Map<String, dynamic> evidence,
  }) = _EnvironmentSessionIdentityEvidence;

  factory EnvironmentSessionIdentityEvidence({
    SessionSummary? identitySession,
    SessionMemberSummary? identityMember,
    List<SessionMemberActorRoleSummary> identityActorRoles = const [],
    Map<String, dynamic>? evidence,
  }) {
    return _EnvironmentSessionIdentityEvidence(
      identitySession: identitySession,
      identityMember: identityMember,
      identityActorRoles: identityActorRoles,
      evidence: evidence ?? {},
    );
  }

  factory EnvironmentSessionIdentityEvidence.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentSessionIdentityEvidenceFromJson({
    ...json,
    if (!json.containsKey('evidence')) 'evidence': {},
  });
}

@freezed
abstract class EnvironmentSessionView with _$EnvironmentSessionView {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentSessionView.def({
    @UuidValueConverter() required UuidValue environmentSessionId,
    @UuidValueConverter() UuidValue? environmentSessionConfigId,
    @UuidValueConverter() UuidValue? identitySessionId,
    SessionSummary? identitySession,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() required UuidValue environmentProfileId,
    required String sessionKey,
    String? title,
    String? description,
    String? purpose,
    required String status,
    @UuidValueConverter() UuidValue? createdByActorId,
    String? sourceKind,
    String? sourceRef,
    required Map<String, dynamic> evidence,
  }) = _EnvironmentSessionView;

  factory EnvironmentSessionView({
    required UuidValue environmentSessionId,
    UuidValue? environmentSessionConfigId,
    UuidValue? identitySessionId,
    SessionSummary? identitySession,
    required UuidValue environmentId,
    required UuidValue environmentProfileId,
    required String sessionKey,
    String? title,
    String? description,
    String? purpose,
    String? status,
    UuidValue? createdByActorId,
    String? sourceKind,
    String? sourceRef,
    Map<String, dynamic>? evidence,
  }) {
    return _EnvironmentSessionView(
      environmentSessionId: environmentSessionId,
      environmentSessionConfigId: environmentSessionConfigId,
      identitySessionId: identitySessionId,
      identitySession: identitySession,
      environmentId: environmentId,
      environmentProfileId: environmentProfileId,
      sessionKey: sessionKey,
      title: title,
      description: description,
      purpose: purpose,
      status: status ?? 'active',
      createdByActorId: createdByActorId,
      sourceKind: sourceKind,
      sourceRef: sourceRef,
      evidence: evidence ?? {},
    );
  }

  factory EnvironmentSessionView.fromJson(Map<String, dynamic> json) =>
      _$EnvironmentSessionViewFromJson({
        ...json,
        if (!json.containsKey('status')) 'status': 'active',
        if (!json.containsKey('evidence')) 'evidence': {},
      });
}

@freezed
abstract class EnvironmentSessionJoinReceipt
    with _$EnvironmentSessionJoinReceipt {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentSessionJoinReceipt.def({
    required bool accepted,
    required String status,
    String? error,
    String? reason,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() required UuidValue environmentProfileId,
    @UuidValueConverter() UuidValue? environmentSessionId,
    String? environmentSessionKey,
    EnvironmentSessionIdentityEvidence? identityEvidence,
    @Default(const []) List<String> blockers,
    required Map<String, dynamic> evidence,
  }) = _EnvironmentSessionJoinReceipt;

  factory EnvironmentSessionJoinReceipt({
    bool? accepted,
    required String status,
    String? error,
    String? reason,
    UuidValue? actorId,
    required UuidValue environmentId,
    required UuidValue environmentProfileId,
    UuidValue? environmentSessionId,
    String? environmentSessionKey,
    EnvironmentSessionIdentityEvidence? identityEvidence,
    List<String> blockers = const [],
    Map<String, dynamic>? evidence,
  }) {
    return _EnvironmentSessionJoinReceipt(
      accepted: accepted ?? false,
      status: status,
      error: error,
      reason: reason,
      actorId: actorId,
      environmentId: environmentId,
      environmentProfileId: environmentProfileId,
      environmentSessionId: environmentSessionId,
      environmentSessionKey: environmentSessionKey,
      identityEvidence: identityEvidence,
      blockers: blockers,
      evidence: evidence ?? {},
    );
  }

  factory EnvironmentSessionJoinReceipt.fromJson(Map<String, dynamic> json) =>
      _$EnvironmentSessionJoinReceiptFromJson({
        ...json,
        if (!json.containsKey('accepted')) 'accepted': false,
        if (!json.containsKey('evidence')) 'evidence': {},
      });
}

@freezed
abstract class StartEnvironmentSessionResponse
    with _$StartEnvironmentSessionResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory StartEnvironmentSessionResponse.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String operation,
    @UuidValueConverter() UuidValue? requestId,
    required bool accepted,
    required String status,
    String? error,
    EnvironmentSessionView? session,
    required EnvironmentSessionJoinReceipt joinReceipt,
    EnvironmentNavigationContextView? defaultNavigationContext,
    EnvironmentNavigationCommitReceipt? defaultNavigationReceipt,
    required Map<String, dynamic> evidence,
  }) = _StartEnvironmentSessionResponse;

  factory StartEnvironmentSessionResponse({
    UuidValue? actorId,
    required UuidValue environmentId,
    UuidValue? processId,
    UuidValue? threadId,
    UuidValue? branchId,
    String? projectionHash,
    String? operation,
    UuidValue? requestId,
    bool? accepted,
    required String status,
    String? error,
    EnvironmentSessionView? session,
    required EnvironmentSessionJoinReceipt joinReceipt,
    EnvironmentNavigationContextView? defaultNavigationContext,
    EnvironmentNavigationCommitReceipt? defaultNavigationReceipt,
    Map<String, dynamic>? evidence,
  }) {
    return _StartEnvironmentSessionResponse(
      actorId: actorId,
      environmentId: environmentId,
      processId: processId,
      threadId: threadId,
      branchId: branchId,
      projectionHash: projectionHash,
      operation: operation ?? 'start_environment_session',
      requestId: requestId,
      accepted: accepted ?? false,
      status: status,
      error: error,
      session: session,
      joinReceipt: joinReceipt,
      defaultNavigationContext: defaultNavigationContext,
      defaultNavigationReceipt: defaultNavigationReceipt,
      evidence: evidence ?? {},
    );
  }

  factory StartEnvironmentSessionResponse.fromJson(Map<String, dynamic> json) =>
      _$StartEnvironmentSessionResponseFromJson({
        ...json,
        if (!json.containsKey('operation'))
          'operation': 'start_environment_session',
        if (!json.containsKey('accepted')) 'accepted': false,
        if (!json.containsKey('evidence')) 'evidence': {},
      });
}

@freezed
abstract class JoinEnvironmentSessionResponse
    with _$JoinEnvironmentSessionResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory JoinEnvironmentSessionResponse.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String operation,
    @UuidValueConverter() UuidValue? requestId,
    required bool accepted,
    required String status,
    String? error,
    EnvironmentSessionView? session,
    required EnvironmentSessionJoinReceipt receipt,
    EnvironmentNavigationContextView? defaultNavigationContext,
    EnvironmentNavigationCommitReceipt? defaultNavigationReceipt,
    required Map<String, dynamic> evidence,
  }) = _JoinEnvironmentSessionResponse;

  factory JoinEnvironmentSessionResponse({
    UuidValue? actorId,
    required UuidValue environmentId,
    UuidValue? processId,
    UuidValue? threadId,
    UuidValue? branchId,
    String? projectionHash,
    String? operation,
    UuidValue? requestId,
    bool? accepted,
    required String status,
    String? error,
    EnvironmentSessionView? session,
    required EnvironmentSessionJoinReceipt receipt,
    EnvironmentNavigationContextView? defaultNavigationContext,
    EnvironmentNavigationCommitReceipt? defaultNavigationReceipt,
    Map<String, dynamic>? evidence,
  }) {
    return _JoinEnvironmentSessionResponse(
      actorId: actorId,
      environmentId: environmentId,
      processId: processId,
      threadId: threadId,
      branchId: branchId,
      projectionHash: projectionHash,
      operation: operation ?? 'join_environment_session',
      requestId: requestId,
      accepted: accepted ?? false,
      status: status,
      error: error,
      session: session,
      receipt: receipt,
      defaultNavigationContext: defaultNavigationContext,
      defaultNavigationReceipt: defaultNavigationReceipt,
      evidence: evidence ?? {},
    );
  }

  factory JoinEnvironmentSessionResponse.fromJson(Map<String, dynamic> json) =>
      _$JoinEnvironmentSessionResponseFromJson({
        ...json,
        if (!json.containsKey('operation'))
          'operation': 'join_environment_session',
        if (!json.containsKey('accepted')) 'accepted': false,
        if (!json.containsKey('evidence')) 'evidence': {},
      });
}

@freezed
abstract class DescribeEnvironmentSessionResponse
    with _$DescribeEnvironmentSessionResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory DescribeEnvironmentSessionResponse.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    required String operation,
    required String status,
    String? error,
    EnvironmentSessionView? session,
    required Map<String, dynamic> evidence,
  }) = _DescribeEnvironmentSessionResponse;

  factory DescribeEnvironmentSessionResponse({
    UuidValue? actorId,
    required UuidValue environmentId,
    UuidValue? processId,
    UuidValue? threadId,
    UuidValue? branchId,
    String? projectionHash,
    String? operation,
    required String status,
    String? error,
    EnvironmentSessionView? session,
    Map<String, dynamic>? evidence,
  }) {
    return _DescribeEnvironmentSessionResponse(
      actorId: actorId,
      environmentId: environmentId,
      processId: processId,
      threadId: threadId,
      branchId: branchId,
      projectionHash: projectionHash,
      operation: operation ?? 'describe_environment_session',
      status: status,
      error: error,
      session: session,
      evidence: evidence ?? {},
    );
  }

  factory DescribeEnvironmentSessionResponse.fromJson(
    Map<String, dynamic> json,
  ) => _$DescribeEnvironmentSessionResponseFromJson({
    ...json,
    if (!json.containsKey('operation'))
      'operation': 'describe_environment_session',
    if (!json.containsKey('evidence')) 'evidence': {},
  });
}

@freezed
abstract class EnvironmentSessionAttentionResolution
    with _$EnvironmentSessionAttentionResolution {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentSessionAttentionResolution.def({
    @UuidValueConverter() required UuidValue environmentSessionId,
    @UuidValueConverter() UuidValue? environmentNavigationContextId,
    @UuidValueConverter() UuidValue? environmentSessionThreadId,
    @UuidValueConverter() UuidValue? environmentSessionAttentionSessionId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? environmentProfileId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? threadLayoutId,
    @UuidValueConverter() UuidValue? attentionSessionId,
    @UuidValueConverter() UuidValue? identitySessionId,
    AttentionSessionPin? attentionSession,
    AttentionFocusTransitionPin? activeTransition,
    AttentionTransitionValidationResult? validation,
    @Default(const []) List<AttentionFocusTransitionPin> transitions,
    required String status,
    @Default(const []) List<String> blockers,
    required Map<String, dynamic> evidence,
  }) = _EnvironmentSessionAttentionResolution;

  factory EnvironmentSessionAttentionResolution({
    required UuidValue environmentSessionId,
    UuidValue? environmentNavigationContextId,
    UuidValue? environmentSessionThreadId,
    UuidValue? environmentSessionAttentionSessionId,
    required UuidValue environmentId,
    UuidValue? environmentProfileId,
    UuidValue? threadId,
    UuidValue? threadLayoutId,
    UuidValue? attentionSessionId,
    UuidValue? identitySessionId,
    AttentionSessionPin? attentionSession,
    AttentionFocusTransitionPin? activeTransition,
    AttentionTransitionValidationResult? validation,
    List<AttentionFocusTransitionPin> transitions = const [],
    String? status,
    List<String> blockers = const [],
    Map<String, dynamic>? evidence,
  }) {
    return _EnvironmentSessionAttentionResolution(
      environmentSessionId: environmentSessionId,
      environmentNavigationContextId: environmentNavigationContextId,
      environmentSessionThreadId: environmentSessionThreadId,
      environmentSessionAttentionSessionId:
          environmentSessionAttentionSessionId,
      environmentId: environmentId,
      environmentProfileId: environmentProfileId,
      threadId: threadId,
      threadLayoutId: threadLayoutId,
      attentionSessionId: attentionSessionId,
      identitySessionId: identitySessionId,
      attentionSession: attentionSession,
      activeTransition: activeTransition,
      validation: validation,
      transitions: transitions,
      status: status ?? 'resolved',
      blockers: blockers,
      evidence: evidence ?? {},
    );
  }

  factory EnvironmentSessionAttentionResolution.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentSessionAttentionResolutionFromJson({
    ...json,
    if (!json.containsKey('status')) 'status': 'resolved',
    if (!json.containsKey('evidence')) 'evidence': {},
  });
}

@freezed
abstract class EnvironmentNavigationContextView
    with _$EnvironmentNavigationContextView {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentNavigationContextView.def({
    @UuidValueConverter() required UuidValue environmentNavigationContextId,
    @UuidValueConverter() required UuidValue environmentSessionId,
    @UuidValueConverter() required UuidValue environmentId,
    required String key,
    String? title,
    required String status,
    required bool isDefault,
    @UuidValueConverter() UuidValue? selectedProcessId,
    @UuidValueConverter() UuidValue? selectedThreadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() UuidValue? rootObjectId,
    @UuidValueConverter() UuidValue? commitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    String? graphHashPost,
    required Map<String, dynamic> evidence,
  }) = _EnvironmentNavigationContextView;

  factory EnvironmentNavigationContextView({
    required UuidValue environmentNavigationContextId,
    required UuidValue environmentSessionId,
    required UuidValue environmentId,
    required String key,
    String? title,
    String? status,
    bool? isDefault,
    UuidValue? selectedProcessId,
    UuidValue? selectedThreadId,
    UuidValue? branchId,
    String? projectionHash,
    UuidValue? rootObjectId,
    UuidValue? commitId,
    UuidValue? objectInstanceGraphCommitId,
    String? graphHashPost,
    Map<String, dynamic>? evidence,
  }) {
    return _EnvironmentNavigationContextView(
      environmentNavigationContextId: environmentNavigationContextId,
      environmentSessionId: environmentSessionId,
      environmentId: environmentId,
      key: key,
      title: title,
      status: status ?? 'active',
      isDefault: isDefault ?? false,
      selectedProcessId: selectedProcessId,
      selectedThreadId: selectedThreadId,
      branchId: branchId,
      projectionHash: projectionHash,
      rootObjectId: rootObjectId,
      commitId: commitId,
      objectInstanceGraphCommitId: objectInstanceGraphCommitId,
      graphHashPost: graphHashPost,
      evidence: evidence ?? {},
    );
  }

  factory EnvironmentNavigationContextView.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentNavigationContextViewFromJson({
    ...json,
    if (!json.containsKey('status')) 'status': 'active',
    if (!json.containsKey('is_default')) 'is_default': false,
    if (!json.containsKey('evidence')) 'evidence': {},
  });
}

@freezed
abstract class EnvironmentNavigationCommitReceipt
    with _$EnvironmentNavigationCommitReceipt {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentNavigationCommitReceipt.def({
    required bool accepted,
    required String status,
    String? error,
    String? reason,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() required UuidValue environmentSessionId,
    @UuidValueConverter() UuidValue? environmentNavigationContextId,
    String? key,
    required bool isDefault,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() UuidValue? rootObjectId,
    @UuidValueConverter() UuidValue? commitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    String? graphHashPre,
    String? graphHashPost,
    @UuidValueConverter() UuidValue? functionCallId,
    @UuidValueConverter() UuidValue? functionCallResponseId,
    @UuidValueConverter() UuidValue? selectedProcessId,
    @UuidValueConverter() UuidValue? selectedThreadId,
    @Default(const []) List<String> blockers,
    required Map<String, dynamic> evidence,
  }) = _EnvironmentNavigationCommitReceipt;

  factory EnvironmentNavigationCommitReceipt({
    bool? accepted,
    required String status,
    String? error,
    String? reason,
    UuidValue? actorId,
    required UuidValue environmentId,
    required UuidValue environmentSessionId,
    UuidValue? environmentNavigationContextId,
    String? key,
    bool? isDefault,
    UuidValue? branchId,
    String? projectionHash,
    UuidValue? rootObjectId,
    UuidValue? commitId,
    UuidValue? objectInstanceGraphCommitId,
    String? graphHashPre,
    String? graphHashPost,
    UuidValue? functionCallId,
    UuidValue? functionCallResponseId,
    UuidValue? selectedProcessId,
    UuidValue? selectedThreadId,
    List<String> blockers = const [],
    Map<String, dynamic>? evidence,
  }) {
    return _EnvironmentNavigationCommitReceipt(
      accepted: accepted ?? false,
      status: status,
      error: error,
      reason: reason,
      actorId: actorId,
      environmentId: environmentId,
      environmentSessionId: environmentSessionId,
      environmentNavigationContextId: environmentNavigationContextId,
      key: key,
      isDefault: isDefault ?? false,
      branchId: branchId,
      projectionHash: projectionHash,
      rootObjectId: rootObjectId,
      commitId: commitId,
      objectInstanceGraphCommitId: objectInstanceGraphCommitId,
      graphHashPre: graphHashPre,
      graphHashPost: graphHashPost,
      functionCallId: functionCallId,
      functionCallResponseId: functionCallResponseId,
      selectedProcessId: selectedProcessId,
      selectedThreadId: selectedThreadId,
      blockers: blockers,
      evidence: evidence ?? {},
    );
  }

  factory EnvironmentNavigationCommitReceipt.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentNavigationCommitReceiptFromJson({
    ...json,
    if (!json.containsKey('accepted')) 'accepted': false,
    if (!json.containsKey('is_default')) 'is_default': false,
    if (!json.containsKey('evidence')) 'evidence': {},
  });
}

@freezed
abstract class DescribeEnvironmentOPGConstructor
    with _$DescribeEnvironmentOPGConstructor {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory DescribeEnvironmentOPGConstructor.def({
    @UuidValueConverter() required UuidValue functionId,
    @UuidValueConverter() UuidValue? rootClassConfigId,
  }) = _DescribeEnvironmentOPGConstructor;

  factory DescribeEnvironmentOPGConstructor({
    required UuidValue functionId,
    UuidValue? rootClassConfigId,
  }) {
    return _DescribeEnvironmentOPGConstructor(
      functionId: functionId,
      rootClassConfigId: rootClassConfigId,
    );
  }

  factory DescribeEnvironmentOPGConstructor.fromJson(
    Map<String, dynamic> json,
  ) => _$DescribeEnvironmentOPGConstructorFromJson(json);
}

@freezed
abstract class DescribeEnvironmentOPG with _$DescribeEnvironmentOPG {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory DescribeEnvironmentOPG.def({
    @UuidValueConverter() required UuidValue id,
    required String projectionHash,
    String? name,
    String? description,
    required bool supportsVirtualBuild,
    @Default(const []) List<DescribeEnvironmentOPGConstructor> constructors,
  }) = _DescribeEnvironmentOPG;

  factory DescribeEnvironmentOPG({
    UuidValue? id,
    required String projectionHash,
    String? name,
    String? description,
    bool? supportsVirtualBuild,
    List<DescribeEnvironmentOPGConstructor> constructors = const [],
  }) {
    return _DescribeEnvironmentOPG(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      projectionHash: projectionHash,
      name: name,
      description: description,
      supportsVirtualBuild: supportsVirtualBuild ?? true,
      constructors: constructors,
    );
  }

  factory DescribeEnvironmentOPG.fromJson(Map<String, dynamic> json) =>
      _$DescribeEnvironmentOPGFromJson({
        ...json,
        if (!json.containsKey('supports_virtual_build'))
          'supports_virtual_build': true,
      });
}

@freezed
abstract class DescribeEnvironmentTopologyLane
    with _$DescribeEnvironmentTopologyLane {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory DescribeEnvironmentTopologyLane.def({
    required String laneHash,
    @UuidValueConverter() UuidValue? opgId,
    String? opgName,
  }) = _DescribeEnvironmentTopologyLane;

  factory DescribeEnvironmentTopologyLane({
    required String laneHash,
    UuidValue? opgId,
    String? opgName,
  }) {
    return _DescribeEnvironmentTopologyLane(
      laneHash: laneHash,
      opgId: opgId,
      opgName: opgName,
    );
  }

  factory DescribeEnvironmentTopologyLane.fromJson(Map<String, dynamic> json) =>
      _$DescribeEnvironmentTopologyLaneFromJson(json);
}

@freezed
abstract class DescribeEnvironmentTopologyAttachment
    with _$DescribeEnvironmentTopologyAttachment {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory DescribeEnvironmentTopologyAttachment.def({
    @UuidValueConverter() required UuidValue assocId,
    String? title,
    required bool isActive,
    @UuidValueConverter() required UuidValue objectInstanceGraphBranchId,
    @UuidValueConverter() UuidValue? objectInstanceGraphIdentityId,
    @UuidValueConverter() UuidValue? domainBranchId,
    @Default(const []) List<DescribeEnvironmentTopologyLane> lanes,
  }) = _DescribeEnvironmentTopologyAttachment;

  factory DescribeEnvironmentTopologyAttachment({
    required UuidValue assocId,
    String? title,
    bool? isActive,
    required UuidValue objectInstanceGraphBranchId,
    UuidValue? objectInstanceGraphIdentityId,
    UuidValue? domainBranchId,
    List<DescribeEnvironmentTopologyLane> lanes = const [],
  }) {
    return _DescribeEnvironmentTopologyAttachment(
      assocId: assocId,
      title: title,
      isActive: isActive ?? true,
      objectInstanceGraphBranchId: objectInstanceGraphBranchId,
      objectInstanceGraphIdentityId: objectInstanceGraphIdentityId,
      domainBranchId: domainBranchId,
      lanes: lanes,
    );
  }

  factory DescribeEnvironmentTopologyAttachment.fromJson(
    Map<String, dynamic> json,
  ) => _$DescribeEnvironmentTopologyAttachmentFromJson({
    ...json,
    if (!json.containsKey('is_active')) 'is_active': true,
  });
}

@freezed
abstract class DescribeEnvironmentTopologySection
    with _$DescribeEnvironmentTopologySection {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory DescribeEnvironmentTopologySection.def({
    required String sectionKey,
    required String title,
    String? description,
    required int order,
    required double flex,
    required bool isVisible,
    @UuidValueConverter() UuidValue? focusScopeId,
    String? viewRef,
    String? viewKey,
    String? packageName,
    String? paneKey,
  }) = _DescribeEnvironmentTopologySection;

  factory DescribeEnvironmentTopologySection({
    required String sectionKey,
    String? title,
    String? description,
    int? order,
    double? flex,
    bool? isVisible,
    UuidValue? focusScopeId,
    String? viewRef,
    String? viewKey,
    String? packageName,
    String? paneKey,
  }) {
    return _DescribeEnvironmentTopologySection(
      sectionKey: sectionKey,
      title: title ?? 'Section',
      description: description,
      order: order ?? 0,
      flex: flex ?? 1.0,
      isVisible: isVisible ?? true,
      focusScopeId: focusScopeId,
      viewRef: viewRef,
      viewKey: viewKey,
      packageName: packageName,
      paneKey: paneKey,
    );
  }

  factory DescribeEnvironmentTopologySection.fromJson(
    Map<String, dynamic> json,
  ) => _$DescribeEnvironmentTopologySectionFromJson({
    ...json,
    if (!json.containsKey('title')) 'title': 'Section',
    if (!json.containsKey('order')) 'order': 0,
    if (!json.containsKey('flex')) 'flex': 1.0,
    if (!json.containsKey('is_visible')) 'is_visible': true,
  });
}

@freezed
abstract class DescribeEnvironmentTopologyLayout
    with _$DescribeEnvironmentTopologyLayout {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory DescribeEnvironmentTopologyLayout.def({
    @UuidValueConverter() UuidValue? layoutId,
    String? layoutKey,
    required String title,
    String? description,
    required bool isActive,
    @Default(const []) List<DescribeEnvironmentTopologySection> sections,
  }) = _DescribeEnvironmentTopologyLayout;

  factory DescribeEnvironmentTopologyLayout({
    UuidValue? layoutId,
    String? layoutKey,
    String? title,
    String? description,
    bool? isActive,
    List<DescribeEnvironmentTopologySection> sections = const [],
  }) {
    return _DescribeEnvironmentTopologyLayout(
      layoutId: layoutId,
      layoutKey: layoutKey,
      title: title ?? 'Layout',
      description: description,
      isActive: isActive ?? false,
      sections: sections,
    );
  }

  factory DescribeEnvironmentTopologyLayout.fromJson(
    Map<String, dynamic> json,
  ) => _$DescribeEnvironmentTopologyLayoutFromJson({
    ...json,
    if (!json.containsKey('title')) 'title': 'Layout',
    if (!json.containsKey('is_active')) 'is_active': false,
  });
}

@freezed
abstract class DescribeEnvironmentTopologyThread
    with _$DescribeEnvironmentTopologyThread {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory DescribeEnvironmentTopologyThread.def({
    @UuidValueConverter() required UuidValue threadId,
    String? threadKey,
    String? title,
    String? description,
    @UuidValueConverter() UuidValue? activeLayoutId,
    String? activeLayoutKey,
    @Default(const []) List<DescribeEnvironmentTopologyLayout> layouts,
    @Default(const []) List<DescribeEnvironmentTopologyAttachment> attachments,
  }) = _DescribeEnvironmentTopologyThread;

  factory DescribeEnvironmentTopologyThread({
    required UuidValue threadId,
    String? threadKey,
    String? title,
    String? description,
    UuidValue? activeLayoutId,
    String? activeLayoutKey,
    List<DescribeEnvironmentTopologyLayout> layouts = const [],
    List<DescribeEnvironmentTopologyAttachment> attachments = const [],
  }) {
    return _DescribeEnvironmentTopologyThread(
      threadId: threadId,
      threadKey: threadKey,
      title: title,
      description: description,
      activeLayoutId: activeLayoutId,
      activeLayoutKey: activeLayoutKey,
      layouts: layouts,
      attachments: attachments,
    );
  }

  factory DescribeEnvironmentTopologyThread.fromJson(
    Map<String, dynamic> json,
  ) => _$DescribeEnvironmentTopologyThreadFromJson(json);
}

@freezed
abstract class DescribeEnvironmentTopologyProcess
    with _$DescribeEnvironmentTopologyProcess {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory DescribeEnvironmentTopologyProcess.def({
    @UuidValueConverter() required UuidValue processId,
    String? processKey,
    required String title,
    String? description,
    @Default(const []) List<DescribeEnvironmentTopologyThread> threads,
  }) = _DescribeEnvironmentTopologyProcess;

  factory DescribeEnvironmentTopologyProcess({
    required UuidValue processId,
    String? processKey,
    required String title,
    String? description,
    List<DescribeEnvironmentTopologyThread> threads = const [],
  }) {
    return _DescribeEnvironmentTopologyProcess(
      processId: processId,
      processKey: processKey,
      title: title,
      description: description,
      threads: threads,
    );
  }

  factory DescribeEnvironmentTopologyProcess.fromJson(
    Map<String, dynamic> json,
  ) => _$DescribeEnvironmentTopologyProcessFromJson(json);
}

@freezed
abstract class EnvironmentStatusAuthority with _$EnvironmentStatusAuthority {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentStatusAuthority.def({
    @JsonKey(
      fromJson: EnvironmentStatusAuthorityKindExtension.fromJson,
      toJson: EnvironmentStatusAuthorityKindExtension.toJson,
    )
    required EnvironmentStatusAuthorityKind kind,
    String? sourceArtifact,
  }) = _EnvironmentStatusAuthority;

  factory EnvironmentStatusAuthority({
    required EnvironmentStatusAuthorityKind kind,
    String? sourceArtifact,
  }) {
    return _EnvironmentStatusAuthority(
      kind: kind,
      sourceArtifact: sourceArtifact,
    );
  }

  factory EnvironmentStatusAuthority.fromJson(Map<String, dynamic> json) =>
      _$EnvironmentStatusAuthorityFromJson(json);
}

@freezed
abstract class EnvironmentStatusBlock with _$EnvironmentStatusBlock {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentStatusBlock.def({
    required String name,
    required EnvironmentStatusAuthority authority,
    required Map<String, dynamic> payload,
    required bool available,
    String? unavailableReason,
  }) = _EnvironmentStatusBlock;

  factory EnvironmentStatusBlock({
    required String name,
    required EnvironmentStatusAuthority authority,
    Map<String, dynamic>? payload,
    bool? available,
    String? unavailableReason,
  }) {
    return _EnvironmentStatusBlock(
      name: name,
      authority: authority,
      payload: payload ?? {},
      available: available ?? true,
      unavailableReason: unavailableReason,
    );
  }

  factory EnvironmentStatusBlock.fromJson(Map<String, dynamic> json) =>
      _$EnvironmentStatusBlockFromJson({
        ...json,
        if (!json.containsKey('payload')) 'payload': {},
        if (!json.containsKey('available')) 'available': true,
      });
}

@freezed
abstract class EnvironmentReadinessPersistenceReceipt
    with _$EnvironmentReadinessPersistenceReceipt {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentReadinessPersistenceReceipt.def({
    required String status,
    required String backend,
    String? databaseUrlRef,
    @UuidValueConverter() UuidValue? environmentConfigId,
    @UuidValueConverter() UuidValue? ocgId,
    String? ocgHash,
    String? dbSchemaHash,
    String? dbSchemaRegistryHash,
    String? markerOcgHash,
    @UuidValueConverter() UuidValue? markerHeadCommitId,
    required bool installed,
    required bool migrated,
    required int sqlRootCount,
    required int stepCount,
  }) = _EnvironmentReadinessPersistenceReceipt;

  factory EnvironmentReadinessPersistenceReceipt({
    required String status,
    required String backend,
    String? databaseUrlRef,
    UuidValue? environmentConfigId,
    UuidValue? ocgId,
    String? ocgHash,
    String? dbSchemaHash,
    String? dbSchemaRegistryHash,
    String? markerOcgHash,
    UuidValue? markerHeadCommitId,
    bool? installed,
    bool? migrated,
    int? sqlRootCount,
    int? stepCount,
  }) {
    return _EnvironmentReadinessPersistenceReceipt(
      status: status,
      backend: backend,
      databaseUrlRef: databaseUrlRef,
      environmentConfigId: environmentConfigId,
      ocgId: ocgId,
      ocgHash: ocgHash,
      dbSchemaHash: dbSchemaHash,
      dbSchemaRegistryHash: dbSchemaRegistryHash,
      markerOcgHash: markerOcgHash,
      markerHeadCommitId: markerHeadCommitId,
      installed: installed ?? false,
      migrated: migrated ?? false,
      sqlRootCount: sqlRootCount ?? 0,
      stepCount: stepCount ?? 0,
    );
  }

  factory EnvironmentReadinessPersistenceReceipt.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentReadinessPersistenceReceiptFromJson({
    ...json,
    if (!json.containsKey('installed')) 'installed': false,
    if (!json.containsKey('migrated')) 'migrated': false,
    if (!json.containsKey('sql_root_count')) 'sql_root_count': 0,
    if (!json.containsKey('step_count')) 'step_count': 0,
  });
}

@freezed
abstract class EnvironmentReadinessGraphReceipt
    with _$EnvironmentReadinessGraphReceipt {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentReadinessGraphReceipt.def({
    required String status,
    String? laneHeadStatus,
    String? genesisStatus,
    @UuidValueConverter() required UuidValue branchId,
    String? projectionHash,
    @UuidValueConverter() UuidValue? objectProjectionGraphId,
    @UuidValueConverter() UuidValue? constructorFunctionId,
    @UuidValueConverter() UuidValue? laneHeadCommitId,
    @UuidValueConverter() UuidValue? domainCommitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphId,
    @UuidValueConverter() UuidValue? rootObjectId,
    String? graphHashPost,
    @UuidValueConverter() UuidValue? functionCallId,
    @UuidValueConverter() UuidValue? functionCallResponseId,
  }) = _EnvironmentReadinessGraphReceipt;

  factory EnvironmentReadinessGraphReceipt({
    required String status,
    String? laneHeadStatus,
    String? genesisStatus,
    required UuidValue branchId,
    String? projectionHash,
    UuidValue? objectProjectionGraphId,
    UuidValue? constructorFunctionId,
    UuidValue? laneHeadCommitId,
    UuidValue? domainCommitId,
    UuidValue? objectInstanceGraphCommitId,
    UuidValue? objectInstanceGraphId,
    UuidValue? rootObjectId,
    String? graphHashPost,
    UuidValue? functionCallId,
    UuidValue? functionCallResponseId,
  }) {
    return _EnvironmentReadinessGraphReceipt(
      status: status,
      laneHeadStatus: laneHeadStatus,
      genesisStatus: genesisStatus,
      branchId: branchId,
      projectionHash: projectionHash,
      objectProjectionGraphId: objectProjectionGraphId,
      constructorFunctionId: constructorFunctionId,
      laneHeadCommitId: laneHeadCommitId,
      domainCommitId: domainCommitId,
      objectInstanceGraphCommitId: objectInstanceGraphCommitId,
      objectInstanceGraphId: objectInstanceGraphId,
      rootObjectId: rootObjectId,
      graphHashPost: graphHashPost,
      functionCallId: functionCallId,
      functionCallResponseId: functionCallResponseId,
    );
  }

  factory EnvironmentReadinessGraphReceipt.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentReadinessGraphReceiptFromJson(json);
}

@freezed
abstract class EnvironmentReadinessRouteReceipt
    with _$EnvironmentReadinessRouteReceipt {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentReadinessRouteReceipt.def({
    String? apiPackageName,
    String? providerServicePackageName,
    String? routeKind,
    String? hostId,
    String? hostVersion,
    String? protocolVersion,
    @Default(const []) List<String> endpointRefs,
    @Default(const []) List<String> streamEndpointRefs,
  }) = _EnvironmentReadinessRouteReceipt;

  factory EnvironmentReadinessRouteReceipt({
    String? apiPackageName,
    String? providerServicePackageName,
    String? routeKind,
    String? hostId,
    String? hostVersion,
    String? protocolVersion,
    List<String> endpointRefs = const [],
    List<String> streamEndpointRefs = const [],
  }) {
    return _EnvironmentReadinessRouteReceipt(
      apiPackageName: apiPackageName,
      providerServicePackageName: providerServicePackageName,
      routeKind: routeKind,
      hostId: hostId,
      hostVersion: hostVersion,
      protocolVersion: protocolVersion,
      endpointRefs: endpointRefs,
      streamEndpointRefs: streamEndpointRefs,
    );
  }

  factory EnvironmentReadinessRouteReceipt.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentReadinessRouteReceiptFromJson(json);
}

@freezed
abstract class EnvironmentReadinessReceipt with _$EnvironmentReadinessReceipt {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentReadinessReceipt.def({
    required String status,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    String? environmentTitle,
    String? environmentManifestPath,
    Map<String, dynamic>? environmentPackageRef,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() UuidValue? ocgId,
    @Default(const []) List<String> opgHashes,
    EnvironmentReadinessGraphReceipt? graph,
    EnvironmentReadinessPersistenceReceipt? persistence,
    EnvironmentReadinessRouteReceipt? metaRoute,
  }) = _EnvironmentReadinessReceipt;

  factory EnvironmentReadinessReceipt({
    required String status,
    UuidValue? actorId,
    required UuidValue environmentId,
    String? environmentTitle,
    String? environmentManifestPath,
    Map<String, dynamic>? environmentPackageRef,
    UuidValue? processId,
    UuidValue? threadId,
    UuidValue? branchId,
    String? projectionHash,
    UuidValue? ocgId,
    List<String> opgHashes = const [],
    EnvironmentReadinessGraphReceipt? graph,
    EnvironmentReadinessPersistenceReceipt? persistence,
    EnvironmentReadinessRouteReceipt? metaRoute,
  }) {
    return _EnvironmentReadinessReceipt(
      status: status,
      actorId: actorId,
      environmentId: environmentId,
      environmentTitle: environmentTitle,
      environmentManifestPath: environmentManifestPath,
      environmentPackageRef: environmentPackageRef,
      processId: processId,
      threadId: threadId,
      branchId: branchId,
      projectionHash: projectionHash,
      ocgId: ocgId,
      opgHashes: opgHashes,
      graph: graph,
      persistence: persistence,
      metaRoute: metaRoute,
    );
  }

  factory EnvironmentReadinessReceipt.fromJson(Map<String, dynamic> json) =>
      _$EnvironmentReadinessReceiptFromJson(json);
}
