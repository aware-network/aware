// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'node_deploy_operation_enums.dart';
import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'node_deploy_operation_model.freezed.dart';
part 'node_deploy_operation_model.g.dart';

@freezed
abstract class NodeDeployTarget with _$NodeDeployTarget {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployTarget.def({
    @UuidValueConverter() UuidValue? targetId,
    String? targetKey,
    String? displayName,
    String? nodeBaseUrl,
    String? nodeWebsocketPath,
  }) = _NodeDeployTarget;

  factory NodeDeployTarget({
    UuidValue? targetId,
    String? targetKey,
    String? displayName,
    String? nodeBaseUrl,
    String? nodeWebsocketPath,
  }) {
    return _NodeDeployTarget(
      targetId: targetId,
      targetKey: targetKey,
      displayName: displayName,
      nodeBaseUrl: nodeBaseUrl,
      nodeWebsocketPath: nodeWebsocketPath,
    );
  }

  factory NodeDeployTarget.fromJson(Map<String, dynamic> json) =>
      _$NodeDeployTargetFromJson(json);
}

@freezed
abstract class NodeDeployTargetStatus with _$NodeDeployTargetStatus {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployTargetStatus.def({
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
  }) = _NodeDeployTargetStatus;

  factory NodeDeployTargetStatus({
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
    return _NodeDeployTargetStatus(
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

  factory NodeDeployTargetStatus.fromJson(Map<String, dynamic> json) =>
      _$NodeDeployTargetStatusFromJson({
        ...json,
        if (!json.containsKey('phase')) 'phase': 'idle',
        if (!json.containsKey('is_active')) 'is_active': false,
        if (!json.containsKey('is_healthy')) 'is_healthy': false,
      });
}

@freezed
abstract class NodeDeployRuntimeStatus with _$NodeDeployRuntimeStatus {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployRuntimeStatus.def({
    NodeDeployTarget? target,
    @JsonKey(
      fromJson: NodeDeployRuntimePhaseExtension.fromJson,
      toJson: NodeDeployRuntimePhaseExtension.toJson,
    )
    required NodeDeployRuntimePhase phase,
    String? activeTargetId,
    String? backendKind,
    required bool isActive,
    required bool isHealthy,
    String? nodeBaseUrl,
    String? nodeWebsocketPath,
    String? summary,
    String? error,
    String? updatedAt,
    @Default(const []) List<String> recentLogLines,
    @Default(const []) List<NodeDeployTargetStatus> targetStatuses,
  }) = _NodeDeployRuntimeStatus;

  factory NodeDeployRuntimeStatus({
    NodeDeployTarget? target,
    NodeDeployRuntimePhase? phase,
    String? activeTargetId,
    String? backendKind,
    bool? isActive,
    bool? isHealthy,
    String? nodeBaseUrl,
    String? nodeWebsocketPath,
    String? summary,
    String? error,
    String? updatedAt,
    List<String> recentLogLines = const [],
    List<NodeDeployTargetStatus> targetStatuses = const [],
  }) {
    return _NodeDeployRuntimeStatus(
      target: target,
      phase: phase ?? NodeDeployRuntimePhase.idle,
      activeTargetId: activeTargetId,
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

  factory NodeDeployRuntimeStatus.fromJson(Map<String, dynamic> json) =>
      _$NodeDeployRuntimeStatusFromJson({
        ...json,
        if (!json.containsKey('phase')) 'phase': 'idle',
        if (!json.containsKey('is_active')) 'is_active': false,
        if (!json.containsKey('is_healthy')) 'is_healthy': false,
      });
}

@freezed
abstract class NodeDeployOperationContext with _$NodeDeployOperationContext {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployOperationContext.def({
    @UuidValueConverter() UuidValue? actorId,
  }) = _NodeDeployOperationContext;

  factory NodeDeployOperationContext({UuidValue? actorId}) {
    return _NodeDeployOperationContext(actorId: actorId);
  }

  factory NodeDeployOperationContext.fromJson(Map<String, dynamic> json) =>
      _$NodeDeployOperationContextFromJson(json);
}

@freezed
abstract class NodeDeployOperation with _$NodeDeployOperation {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployOperation.def({
    NodeDeployOperationRequest? request,
    NodeDeployOperationResponse? response,
    NodeDeployOperationEvent? streamItem,
  }) = _NodeDeployOperation;

  factory NodeDeployOperation({
    NodeDeployOperationRequest? request,
    NodeDeployOperationResponse? response,
    NodeDeployOperationEvent? streamItem,
  }) {
    return _NodeDeployOperation(
      request: request,
      response: response,
      streamItem: streamItem,
    );
  }

  factory NodeDeployOperation.fromJson(Map<String, dynamic> json) =>
      _$NodeDeployOperationFromJson(json);
}

@Freezed(unionKey: 'operation')
abstract class NodeDeployOperationRequest with _$NodeDeployOperationRequest {
  @FreezedUnionValue('describe_node_runtime')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployOperationRequest.describeNodeRuntime({
    @UuidValueConverter() UuidValue? actorId,
    NodeDeployTarget? target,
  }) = DescribeNodeRuntimeRequest;

  @FreezedUnionValue('ensure_node_runtime_started')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployOperationRequest.ensureNodeRuntimeStarted({
    @UuidValueConverter() UuidValue? actorId,
    NodeDeployTarget? target,
    required bool waitForReady,
  }) = EnsureNodeRuntimeStartedRequest;

  @FreezedUnionValue('restart_node_runtime')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployOperationRequest.restartNodeRuntime({
    @UuidValueConverter() UuidValue? actorId,
    NodeDeployTarget? target,
    required bool waitForReady,
  }) = RestartNodeRuntimeRequest;

  @FreezedUnionValue('stop_node_runtime')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployOperationRequest.stopNodeRuntime({
    @UuidValueConverter() UuidValue? actorId,
    NodeDeployTarget? target,
    required bool force,
  }) = StopNodeRuntimeRequest;

  @FreezedUnionValue('tail_node_runtime_logs')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployOperationRequest.tailNodeRuntimeLogs({
    @UuidValueConverter() UuidValue? actorId,
    NodeDeployTarget? target,
    required int lineCount,
  }) = TailNodeRuntimeLogsRequest;

  @FreezedUnionValue('stream_node_runtime_events')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployOperationRequest.streamNodeRuntimeEvents({
    @UuidValueConverter() UuidValue? actorId,
    NodeDeployTarget? target,
    required bool includeHistory,
  }) = StreamNodeRuntimeEventsRequest;

  factory NodeDeployOperationRequest.fromJson(Map<String, dynamic> json) =>
      _$NodeDeployOperationRequestFromJson(json);
}

@Freezed(unionKey: 'operation')
abstract class NodeDeployOperationResponse with _$NodeDeployOperationResponse {
  @FreezedUnionValue('describe_node_runtime')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployOperationResponse.describeNodeRuntime({
    @UuidValueConverter() UuidValue? actorId,
    required String status,
    String? error,
    NodeDeployRuntimeStatus? runtimeStatus,
  }) = DescribeNodeRuntimeResponse;

  @FreezedUnionValue('ensure_node_runtime_started')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployOperationResponse.ensureNodeRuntimeStarted({
    @UuidValueConverter() UuidValue? actorId,
    required String status,
    String? error,
    NodeDeployRuntimeStatus? runtimeStatus,
  }) = EnsureNodeRuntimeStartedResponse;

  @FreezedUnionValue('restart_node_runtime')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployOperationResponse.restartNodeRuntime({
    @UuidValueConverter() UuidValue? actorId,
    required String status,
    String? error,
    NodeDeployRuntimeStatus? runtimeStatus,
  }) = RestartNodeRuntimeResponse;

  @FreezedUnionValue('stop_node_runtime')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployOperationResponse.stopNodeRuntime({
    @UuidValueConverter() UuidValue? actorId,
    required String status,
    String? error,
    NodeDeployRuntimeStatus? runtimeStatus,
  }) = StopNodeRuntimeResponse;

  @FreezedUnionValue('tail_node_runtime_logs')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployOperationResponse.tailNodeRuntimeLogs({
    @UuidValueConverter() UuidValue? actorId,
    required String status,
    String? error,
    NodeDeployRuntimeStatus? runtimeStatus,
    @Default(const []) List<String> logLines,
  }) = TailNodeRuntimeLogsResponse;

  @FreezedUnionValue('stream_node_runtime_events')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployOperationResponse.streamNodeRuntimeEvents({
    @UuidValueConverter() UuidValue? actorId,
    required String status,
    String? error,
    NodeDeployRuntimeStatus? runtimeStatus,
    required bool streamOpen,
  }) = StreamNodeRuntimeEventsResponse;

  factory NodeDeployOperationResponse.fromJson(Map<String, dynamic> json) =>
      _$NodeDeployOperationResponseFromJson(json);
}

@Freezed(unionKey: 'kind')
abstract class NodeDeployOperationEvent with _$NodeDeployOperationEvent {
  @FreezedUnionValue('runtime_status')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployOperationEvent.runtimeStatus({
    @UuidValueConverter() UuidValue? actorId,
    String? operation,
    NodeDeployRuntimeStatus? runtimeStatus,
    String? message,
    String? timestamp,
  }) = NodeDeployRuntimeStatusEvent;

  @FreezedUnionValue('runtime_log')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployOperationEvent.runtimeLog({
    @UuidValueConverter() UuidValue? actorId,
    String? operation,
    NodeDeployRuntimeStatus? runtimeStatus,
    String? message,
    String? timestamp,
    String? logLine,
  }) = NodeDeployRuntimeLogEvent;

  @FreezedUnionValue('runtime_terminal')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeDeployOperationEvent.runtimeTerminal({
    @UuidValueConverter() UuidValue? actorId,
    String? operation,
    NodeDeployRuntimeStatus? runtimeStatus,
    String? message,
    String? timestamp,
    required String terminalStatus,
  }) = NodeDeployRuntimeTerminalEvent;

  factory NodeDeployOperationEvent.fromJson(Map<String, dynamic> json) =>
      _$NodeDeployOperationEventFromJson(json);
}
