// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'node_deploy_operation_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_NodeDeployTarget _$NodeDeployTargetFromJson(Map<String, dynamic> json) =>
    _NodeDeployTarget(
      targetId: _$JsonConverterFromJson<String, UuidValue>(
        json['target_id'],
        const UuidValueConverter().fromJson,
      ),
      targetKey: json['target_key'] as String?,
      displayName: json['display_name'] as String?,
      nodeBaseUrl: json['node_base_url'] as String?,
      nodeWebsocketPath: json['node_websocket_path'] as String?,
    );

Map<String, dynamic> _$NodeDeployTargetToJson(_NodeDeployTarget instance) =>
    <String, dynamic>{
      'target_id': _$JsonConverterToJson<String, UuidValue>(
        instance.targetId,
        const UuidValueConverter().toJson,
      ),
      'target_key': instance.targetKey,
      'display_name': instance.displayName,
      'node_base_url': instance.nodeBaseUrl,
      'node_websocket_path': instance.nodeWebsocketPath,
    };

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);

_NodeDeployTargetStatus _$NodeDeployTargetStatusFromJson(
  Map<String, dynamic> json,
) => _NodeDeployTargetStatus(
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

Map<String, dynamic> _$NodeDeployTargetStatusToJson(
  _NodeDeployTargetStatus instance,
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

_NodeDeployRuntimeStatus _$NodeDeployRuntimeStatusFromJson(
  Map<String, dynamic> json,
) => _NodeDeployRuntimeStatus(
  target: json['target'] == null
      ? null
      : NodeDeployTarget.fromJson(json['target'] as Map<String, dynamic>),
  phase: NodeDeployRuntimePhaseExtension.fromJson(json['phase'] as String),
  activeTargetId: json['active_target_id'] as String?,
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
            (e) => NodeDeployTargetStatus.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$NodeDeployRuntimeStatusToJson(
  _NodeDeployRuntimeStatus instance,
) => <String, dynamic>{
  'target': instance.target?.toJson(),
  'phase': NodeDeployRuntimePhaseExtension.toJson(instance.phase),
  'active_target_id': instance.activeTargetId,
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

_NodeDeployOperationContext _$NodeDeployOperationContextFromJson(
  Map<String, dynamic> json,
) => _NodeDeployOperationContext(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
);

Map<String, dynamic> _$NodeDeployOperationContextToJson(
  _NodeDeployOperationContext instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
};

_NodeDeployOperation _$NodeDeployOperationFromJson(Map<String, dynamic> json) =>
    _NodeDeployOperation(
      request: json['request'] == null
          ? null
          : NodeDeployOperationRequest.fromJson(
              json['request'] as Map<String, dynamic>,
            ),
      response: json['response'] == null
          ? null
          : NodeDeployOperationResponse.fromJson(
              json['response'] as Map<String, dynamic>,
            ),
      streamItem: json['stream_item'] == null
          ? null
          : NodeDeployOperationEvent.fromJson(
              json['stream_item'] as Map<String, dynamic>,
            ),
    );

Map<String, dynamic> _$NodeDeployOperationToJson(
  _NodeDeployOperation instance,
) => <String, dynamic>{
  'request': instance.request?.toJson(),
  'response': instance.response?.toJson(),
  'stream_item': instance.streamItem?.toJson(),
};

DescribeNodeRuntimeRequest _$DescribeNodeRuntimeRequestFromJson(
  Map<String, dynamic> json,
) => DescribeNodeRuntimeRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  target: json['target'] == null
      ? null
      : NodeDeployTarget.fromJson(json['target'] as Map<String, dynamic>),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DescribeNodeRuntimeRequestToJson(
  DescribeNodeRuntimeRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'target': instance.target?.toJson(),
  'operation': instance.$type,
};

EnsureNodeRuntimeStartedRequest _$EnsureNodeRuntimeStartedRequestFromJson(
  Map<String, dynamic> json,
) => EnsureNodeRuntimeStartedRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  target: json['target'] == null
      ? null
      : NodeDeployTarget.fromJson(json['target'] as Map<String, dynamic>),
  waitForReady: json['wait_for_ready'] as bool,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$EnsureNodeRuntimeStartedRequestToJson(
  EnsureNodeRuntimeStartedRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'target': instance.target?.toJson(),
  'wait_for_ready': instance.waitForReady,
  'operation': instance.$type,
};

RestartNodeRuntimeRequest _$RestartNodeRuntimeRequestFromJson(
  Map<String, dynamic> json,
) => RestartNodeRuntimeRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  target: json['target'] == null
      ? null
      : NodeDeployTarget.fromJson(json['target'] as Map<String, dynamic>),
  waitForReady: json['wait_for_ready'] as bool,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$RestartNodeRuntimeRequestToJson(
  RestartNodeRuntimeRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'target': instance.target?.toJson(),
  'wait_for_ready': instance.waitForReady,
  'operation': instance.$type,
};

StopNodeRuntimeRequest _$StopNodeRuntimeRequestFromJson(
  Map<String, dynamic> json,
) => StopNodeRuntimeRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  target: json['target'] == null
      ? null
      : NodeDeployTarget.fromJson(json['target'] as Map<String, dynamic>),
  force: json['force'] as bool,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$StopNodeRuntimeRequestToJson(
  StopNodeRuntimeRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'target': instance.target?.toJson(),
  'force': instance.force,
  'operation': instance.$type,
};

TailNodeRuntimeLogsRequest _$TailNodeRuntimeLogsRequestFromJson(
  Map<String, dynamic> json,
) => TailNodeRuntimeLogsRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  target: json['target'] == null
      ? null
      : NodeDeployTarget.fromJson(json['target'] as Map<String, dynamic>),
  lineCount: (json['line_count'] as num).toInt(),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$TailNodeRuntimeLogsRequestToJson(
  TailNodeRuntimeLogsRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'target': instance.target?.toJson(),
  'line_count': instance.lineCount,
  'operation': instance.$type,
};

StreamNodeRuntimeEventsRequest _$StreamNodeRuntimeEventsRequestFromJson(
  Map<String, dynamic> json,
) => StreamNodeRuntimeEventsRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  target: json['target'] == null
      ? null
      : NodeDeployTarget.fromJson(json['target'] as Map<String, dynamic>),
  includeHistory: json['include_history'] as bool,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$StreamNodeRuntimeEventsRequestToJson(
  StreamNodeRuntimeEventsRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'target': instance.target?.toJson(),
  'include_history': instance.includeHistory,
  'operation': instance.$type,
};

DescribeNodeRuntimeResponse _$DescribeNodeRuntimeResponseFromJson(
  Map<String, dynamic> json,
) => DescribeNodeRuntimeResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  status: json['status'] as String,
  error: json['error'] as String?,
  runtimeStatus: json['runtime_status'] == null
      ? null
      : NodeDeployRuntimeStatus.fromJson(
          json['runtime_status'] as Map<String, dynamic>,
        ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DescribeNodeRuntimeResponseToJson(
  DescribeNodeRuntimeResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'status': instance.status,
  'error': instance.error,
  'runtime_status': instance.runtimeStatus?.toJson(),
  'operation': instance.$type,
};

EnsureNodeRuntimeStartedResponse _$EnsureNodeRuntimeStartedResponseFromJson(
  Map<String, dynamic> json,
) => EnsureNodeRuntimeStartedResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  status: json['status'] as String,
  error: json['error'] as String?,
  runtimeStatus: json['runtime_status'] == null
      ? null
      : NodeDeployRuntimeStatus.fromJson(
          json['runtime_status'] as Map<String, dynamic>,
        ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$EnsureNodeRuntimeStartedResponseToJson(
  EnsureNodeRuntimeStartedResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'status': instance.status,
  'error': instance.error,
  'runtime_status': instance.runtimeStatus?.toJson(),
  'operation': instance.$type,
};

RestartNodeRuntimeResponse _$RestartNodeRuntimeResponseFromJson(
  Map<String, dynamic> json,
) => RestartNodeRuntimeResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  status: json['status'] as String,
  error: json['error'] as String?,
  runtimeStatus: json['runtime_status'] == null
      ? null
      : NodeDeployRuntimeStatus.fromJson(
          json['runtime_status'] as Map<String, dynamic>,
        ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$RestartNodeRuntimeResponseToJson(
  RestartNodeRuntimeResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'status': instance.status,
  'error': instance.error,
  'runtime_status': instance.runtimeStatus?.toJson(),
  'operation': instance.$type,
};

StopNodeRuntimeResponse _$StopNodeRuntimeResponseFromJson(
  Map<String, dynamic> json,
) => StopNodeRuntimeResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  status: json['status'] as String,
  error: json['error'] as String?,
  runtimeStatus: json['runtime_status'] == null
      ? null
      : NodeDeployRuntimeStatus.fromJson(
          json['runtime_status'] as Map<String, dynamic>,
        ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$StopNodeRuntimeResponseToJson(
  StopNodeRuntimeResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'status': instance.status,
  'error': instance.error,
  'runtime_status': instance.runtimeStatus?.toJson(),
  'operation': instance.$type,
};

TailNodeRuntimeLogsResponse _$TailNodeRuntimeLogsResponseFromJson(
  Map<String, dynamic> json,
) => TailNodeRuntimeLogsResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  status: json['status'] as String,
  error: json['error'] as String?,
  runtimeStatus: json['runtime_status'] == null
      ? null
      : NodeDeployRuntimeStatus.fromJson(
          json['runtime_status'] as Map<String, dynamic>,
        ),
  logLines:
      (json['log_lines'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$TailNodeRuntimeLogsResponseToJson(
  TailNodeRuntimeLogsResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'status': instance.status,
  'error': instance.error,
  'runtime_status': instance.runtimeStatus?.toJson(),
  'log_lines': instance.logLines,
  'operation': instance.$type,
};

StreamNodeRuntimeEventsResponse _$StreamNodeRuntimeEventsResponseFromJson(
  Map<String, dynamic> json,
) => StreamNodeRuntimeEventsResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  status: json['status'] as String,
  error: json['error'] as String?,
  runtimeStatus: json['runtime_status'] == null
      ? null
      : NodeDeployRuntimeStatus.fromJson(
          json['runtime_status'] as Map<String, dynamic>,
        ),
  streamOpen: json['stream_open'] as bool,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$StreamNodeRuntimeEventsResponseToJson(
  StreamNodeRuntimeEventsResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'status': instance.status,
  'error': instance.error,
  'runtime_status': instance.runtimeStatus?.toJson(),
  'stream_open': instance.streamOpen,
  'operation': instance.$type,
};

NodeDeployRuntimeStatusEvent _$NodeDeployRuntimeStatusEventFromJson(
  Map<String, dynamic> json,
) => NodeDeployRuntimeStatusEvent(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  operation: json['operation'] as String?,
  runtimeStatus: json['runtime_status'] == null
      ? null
      : NodeDeployRuntimeStatus.fromJson(
          json['runtime_status'] as Map<String, dynamic>,
        ),
  message: json['message'] as String?,
  timestamp: json['timestamp'] as String?,
  $type: json['kind'] as String?,
);

Map<String, dynamic> _$NodeDeployRuntimeStatusEventToJson(
  NodeDeployRuntimeStatusEvent instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'operation': instance.operation,
  'runtime_status': instance.runtimeStatus?.toJson(),
  'message': instance.message,
  'timestamp': instance.timestamp,
  'kind': instance.$type,
};

NodeDeployRuntimeLogEvent _$NodeDeployRuntimeLogEventFromJson(
  Map<String, dynamic> json,
) => NodeDeployRuntimeLogEvent(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  operation: json['operation'] as String?,
  runtimeStatus: json['runtime_status'] == null
      ? null
      : NodeDeployRuntimeStatus.fromJson(
          json['runtime_status'] as Map<String, dynamic>,
        ),
  message: json['message'] as String?,
  timestamp: json['timestamp'] as String?,
  logLine: json['log_line'] as String?,
  $type: json['kind'] as String?,
);

Map<String, dynamic> _$NodeDeployRuntimeLogEventToJson(
  NodeDeployRuntimeLogEvent instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'operation': instance.operation,
  'runtime_status': instance.runtimeStatus?.toJson(),
  'message': instance.message,
  'timestamp': instance.timestamp,
  'log_line': instance.logLine,
  'kind': instance.$type,
};

NodeDeployRuntimeTerminalEvent _$NodeDeployRuntimeTerminalEventFromJson(
  Map<String, dynamic> json,
) => NodeDeployRuntimeTerminalEvent(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  operation: json['operation'] as String?,
  runtimeStatus: json['runtime_status'] == null
      ? null
      : NodeDeployRuntimeStatus.fromJson(
          json['runtime_status'] as Map<String, dynamic>,
        ),
  message: json['message'] as String?,
  timestamp: json['timestamp'] as String?,
  terminalStatus: json['terminal_status'] as String,
  $type: json['kind'] as String?,
);

Map<String, dynamic> _$NodeDeployRuntimeTerminalEventToJson(
  NodeDeployRuntimeTerminalEvent instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'operation': instance.operation,
  'runtime_status': instance.runtimeStatus?.toJson(),
  'message': instance.message,
  'timestamp': instance.timestamp,
  'terminal_status': instance.terminalStatus,
  'kind': instance.$type,
};
