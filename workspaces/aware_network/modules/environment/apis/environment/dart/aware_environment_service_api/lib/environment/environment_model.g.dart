// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'environment_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_EnvironmentOperationContext _$EnvironmentOperationContextFromJson(
  Map<String, dynamic> json,
) => _EnvironmentOperationContext(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
);

Map<String, dynamic> _$EnvironmentOperationContextToJson(
  _EnvironmentOperationContext instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
};

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);

_EnvironmentOperationNotificationContext
_$EnvironmentOperationNotificationContextFromJson(Map<String, dynamic> json) =>
    _EnvironmentOperationNotificationContext(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
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
      threadId: _$JsonConverterFromJson<String, UuidValue>(
        json['thread_id'],
        const UuidValueConverter().fromJson,
      ),
      branchId: const UuidValueConverter().fromJson(
        json['branch_id'] as String,
      ),
      projectionHash: json['projection_hash'] as String,
    );

Map<String, dynamic> _$EnvironmentOperationNotificationContextToJson(
  _EnvironmentOperationNotificationContext instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
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
  'thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': const UuidValueConverter().toJson(instance.branchId),
  'projection_hash': instance.projectionHash,
};

_EnvironmentOperation _$EnvironmentOperationFromJson(
  Map<String, dynamic> json,
) => _EnvironmentOperation(
  request: json['request'] == null
      ? null
      : EnvironmentOperationRequest.fromJson(
          json['request'] as Map<String, dynamic>,
        ),
  response: json['response'] == null
      ? null
      : EnvironmentOperationResponse.fromJson(
          json['response'] as Map<String, dynamic>,
        ),
  notification: json['notification'] == null
      ? null
      : EnvironmentOperationNotification.fromJson(
          json['notification'] as Map<String, dynamic>,
        ),
);

Map<String, dynamic> _$EnvironmentOperationToJson(
  _EnvironmentOperation instance,
) => <String, dynamic>{
  'request': instance.request?.toJson(),
  'response': instance.response?.toJson(),
  'notification': instance.notification?.toJson(),
};

FetchCapabilitiesRequest _$FetchCapabilitiesRequestFromJson(
  Map<String, dynamic> json,
) => FetchCapabilitiesRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$FetchCapabilitiesRequestToJson(
  FetchCapabilitiesRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'operation': instance.$type,
};

DescribeEnvironmentConfigRequest _$DescribeEnvironmentConfigRequestFromJson(
  Map<String, dynamic> json,
) => DescribeEnvironmentConfigRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DescribeEnvironmentConfigRequestToJson(
  DescribeEnvironmentConfigRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'operation': instance.$type,
};

DescribeEnvironmentRequest _$DescribeEnvironmentRequestFromJson(
  Map<String, dynamic> json,
) => DescribeEnvironmentRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DescribeEnvironmentRequestToJson(
  DescribeEnvironmentRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'operation': instance.$type,
};

DescribeEnvironmentTopologyRequest _$DescribeEnvironmentTopologyRequestFromJson(
  Map<String, dynamic> json,
) => DescribeEnvironmentTopologyRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  processKey: json['process_key'] as String?,
  threadKey: json['thread_key'] as String?,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DescribeEnvironmentTopologyRequestToJson(
  DescribeEnvironmentTopologyRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'process_key': instance.processKey,
  'thread_key': instance.threadKey,
  'operation': instance.$type,
};

DescribeEnvironmentStatusRequest _$DescribeEnvironmentStatusRequestFromJson(
  Map<String, dynamic> json,
) => DescribeEnvironmentStatusRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  includeBlocks:
      (json['include_blocks'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  strictCommitTruth: json['strict_commit_truth'] as bool,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DescribeEnvironmentStatusRequestToJson(
  DescribeEnvironmentStatusRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'include_blocks': instance.includeBlocks,
  'strict_commit_truth': instance.strictCommitTruth,
  'operation': instance.$type,
};

EnsureReadyRequest _$EnsureReadyRequestFromJson(Map<String, dynamic> json) =>
    EnsureReadyRequest(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentId: const UuidValueConverter().fromJson(
        json['environment_id'] as String,
      ),
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
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$EnsureReadyRequestToJson(
  EnsureReadyRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'operation': instance.$type,
};

GetLaneHeadRequest _$GetLaneHeadRequestFromJson(Map<String, dynamic> json) =>
    GetLaneHeadRequest(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentId: const UuidValueConverter().fromJson(
        json['environment_id'] as String,
      ),
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
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$GetLaneHeadRequestToJson(
  GetLaneHeadRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'operation': instance.$type,
};

GetObjectInstanceGraphCommitRequest
_$GetObjectInstanceGraphCommitRequestFromJson(Map<String, dynamic> json) =>
    GetObjectInstanceGraphCommitRequest(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentId: const UuidValueConverter().fromJson(
        json['environment_id'] as String,
      ),
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
      commitId: const UuidValueConverter().fromJson(
        json['commit_id'] as String,
      ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$GetObjectInstanceGraphCommitRequestToJson(
  GetObjectInstanceGraphCommitRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'commit_id': const UuidValueConverter().toJson(instance.commitId),
  'operation': instance.$type,
};

MaterializeCommittedProjectionDtoRequest
_$MaterializeCommittedProjectionDtoRequestFromJson(Map<String, dynamic> json) =>
    MaterializeCommittedProjectionDtoRequest(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentId: const UuidValueConverter().fromJson(
        json['environment_id'] as String,
      ),
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
      commitId: const UuidValueConverter().fromJson(
        json['commit_id'] as String,
      ),
      expectedGraphHashPost: json['expected_graph_hash_post'] as String?,
      objectInstanceGraphId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_instance_graph_id'],
        const UuidValueConverter().fromJson,
      ),
      rootObjectId: _$JsonConverterFromJson<String, UuidValue>(
        json['root_object_id'],
        const UuidValueConverter().fromJson,
      ),
      useCommitRoot: json['use_commit_root'] as bool,
      dtoClassRef: json['dto_class_ref'] as String?,
      classConfigId: _$JsonConverterFromJson<String, UuidValue>(
        json['class_config_id'],
        const UuidValueConverter().fromJson,
      ),
      dtoPackageName: json['dto_package_name'] as String?,
      dtoImportRoot: json['dto_import_root'] as String?,
      viewRef: json['view_ref'] as String?,
      projectionViewKey: json['projection_view_key'] as String?,
      includeRelationships: json['include_relationships'] as bool,
      maxDepth: (json['max_depth'] as num?)?.toInt(),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$MaterializeCommittedProjectionDtoRequestToJson(
  MaterializeCommittedProjectionDtoRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'commit_id': const UuidValueConverter().toJson(instance.commitId),
  'expected_graph_hash_post': instance.expectedGraphHashPost,
  'object_instance_graph_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphId,
    const UuidValueConverter().toJson,
  ),
  'root_object_id': _$JsonConverterToJson<String, UuidValue>(
    instance.rootObjectId,
    const UuidValueConverter().toJson,
  ),
  'use_commit_root': instance.useCommitRoot,
  'dto_class_ref': instance.dtoClassRef,
  'class_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.classConfigId,
    const UuidValueConverter().toJson,
  ),
  'dto_package_name': instance.dtoPackageName,
  'dto_import_root': instance.dtoImportRoot,
  'view_ref': instance.viewRef,
  'projection_view_key': instance.projectionViewKey,
  'include_relationships': instance.includeRelationships,
  'max_depth': instance.maxDepth,
  'operation': instance.$type,
};

ResolveRuntimeRefsRequest _$ResolveRuntimeRefsRequestFromJson(
  Map<String, dynamic> json,
) => ResolveRuntimeRefsRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  functionTargets:
      (json['function_targets'] as List<dynamic>?)
          ?.map(
            (e) => ResolveRuntimeFunctionTargetQuery.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  classRefs:
      (json['class_refs'] as List<dynamic>?)
          ?.map(
            (e) =>
                ResolveRuntimeClassRefQuery.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$ResolveRuntimeRefsRequestToJson(
  ResolveRuntimeRefsRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'function_targets': instance.functionTargets.map((e) => e.toJson()).toList(),
  'class_refs': instance.classRefs.map((e) => e.toJson()).toList(),
  'operation': instance.$type,
};

ConfigureServiceApiDependencyRoutesRequest
_$ConfigureServiceApiDependencyRoutesRequestFromJson(
  Map<String, dynamic> json,
) => ConfigureServiceApiDependencyRoutesRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  routes: json['routes'] as List<dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$ConfigureServiceApiDependencyRoutesRequestToJson(
  ConfigureServiceApiDependencyRoutesRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'routes': instance.routes,
  'operation': instance.$type,
};

AttachEnvironmentOntologyRequest _$AttachEnvironmentOntologyRequestFromJson(
  Map<String, dynamic> json,
) => AttachEnvironmentOntologyRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  ontologyId: const UuidValueConverter().fromJson(
    json['ontology_id'] as String,
  ),
  role: json['role'] as String,
  status: json['status'] as String,
  title: json['title'] as String?,
  description: json['description'] as String?,
  expectedGraphHashPre: json['expected_graph_hash_pre'] as String?,
  expectedHeadCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['expected_head_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  commit: json['commit'] as bool,
  publish: json['publish'] as bool,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$AttachEnvironmentOntologyRequestToJson(
  AttachEnvironmentOntologyRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'ontology_id': const UuidValueConverter().toJson(instance.ontologyId),
  'role': instance.role,
  'status': instance.status,
  'title': instance.title,
  'description': instance.description,
  'expected_graph_hash_pre': instance.expectedGraphHashPre,
  'expected_head_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.expectedHeadCommitId,
    const UuidValueConverter().toJson,
  ),
  'commit': instance.commit,
  'publish': instance.publish,
  'operation': instance.$type,
};

EnsureEnvironmentOntologyRuntimeRequest
_$EnsureEnvironmentOntologyRuntimeRequestFromJson(Map<String, dynamic> json) =>
    EnsureEnvironmentOntologyRuntimeRequest(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentId: const UuidValueConverter().fromJson(
        json['environment_id'] as String,
      ),
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
      ontologyId: _$JsonConverterFromJson<String, UuidValue>(
        json['ontology_id'],
        const UuidValueConverter().fromJson,
      ),
      packageName: json['package_name'] as String?,
      fqnPrefix: json['fqn_prefix'] as String?,
      artifactSetId: json['artifact_set_id'] as String?,
      workspaceRevisionId: json['workspace_revision_id'] as String?,
      materializationRef: json['materialization_ref'] as String?,
      includeArtifacts: json['include_artifacts'] as bool,
      sourcePayload: json['source_payload'] as Map<String, dynamic>?,
      membershipCommitId: _$JsonConverterFromJson<String, UuidValue>(
        json['membership_commit_id'],
        const UuidValueConverter().fromJson,
      ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$EnsureEnvironmentOntologyRuntimeRequestToJson(
  EnsureEnvironmentOntologyRuntimeRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'ontology_id': _$JsonConverterToJson<String, UuidValue>(
    instance.ontologyId,
    const UuidValueConverter().toJson,
  ),
  'package_name': instance.packageName,
  'fqn_prefix': instance.fqnPrefix,
  'artifact_set_id': instance.artifactSetId,
  'workspace_revision_id': instance.workspaceRevisionId,
  'materialization_ref': instance.materializationRef,
  'include_artifacts': instance.includeArtifacts,
  'source_payload': instance.sourcePayload,
  'membership_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.membershipCommitId,
    const UuidValueConverter().toJson,
  ),
  'operation': instance.$type,
};

ListEnvironmentOntologiesRequest _$ListEnvironmentOntologiesRequestFromJson(
  Map<String, dynamic> json,
) => ListEnvironmentOntologiesRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  commitId: _$JsonConverterFromJson<String, UuidValue>(
    json['commit_id'],
    const UuidValueConverter().fromJson,
  ),
  rootObjectId: _$JsonConverterFromJson<String, UuidValue>(
    json['root_object_id'],
    const UuidValueConverter().fromJson,
  ),
  expectedGraphHashPost: json['expected_graph_hash_post'] as String?,
  dtoClassRef: json['dto_class_ref'] as String?,
  dtoPackageName: json['dto_package_name'] as String?,
  dtoImportRoot: json['dto_import_root'] as String?,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$ListEnvironmentOntologiesRequestToJson(
  ListEnvironmentOntologiesRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.commitId,
    const UuidValueConverter().toJson,
  ),
  'root_object_id': _$JsonConverterToJson<String, UuidValue>(
    instance.rootObjectId,
    const UuidValueConverter().toJson,
  ),
  'expected_graph_hash_post': instance.expectedGraphHashPost,
  'dto_class_ref': instance.dtoClassRef,
  'dto_package_name': instance.dtoPackageName,
  'dto_import_root': instance.dtoImportRoot,
  'operation': instance.$type,
};

ResolveEnvironmentSessionAttentionRequest
_$ResolveEnvironmentSessionAttentionRequestFromJson(
  Map<String, dynamic> json,
) => ResolveEnvironmentSessionAttentionRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentSessionId: const UuidValueConverter().fromJson(
    json['environment_session_id'] as String,
  ),
  environmentNavigationContextId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_navigation_context_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentSessionThreadId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_session_thread_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentSessionAttentionSessionId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['environment_session_attention_session_id'],
        const UuidValueConverter().fromJson,
      ),
  expectedAttentionSessionId: _$JsonConverterFromJson<String, UuidValue>(
    json['expected_attention_session_id'],
    const UuidValueConverter().fromJson,
  ),
  attentionFocusTransitionId: _$JsonConverterFromJson<String, UuidValue>(
    json['attention_focus_transition_id'],
    const UuidValueConverter().fromJson,
  ),
  expectedAttentionSessionSectionId: _$JsonConverterFromJson<String, UuidValue>(
    json['expected_attention_session_section_id'],
    const UuidValueConverter().fromJson,
  ),
  expectedFocusScopeId: _$JsonConverterFromJson<String, UuidValue>(
    json['expected_focus_scope_id'],
    const UuidValueConverter().fromJson,
  ),
  expectedObjectInstanceGraphCommitId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['expected_object_instance_graph_commit_id'],
        const UuidValueConverter().fromJson,
      ),
  expectedProjectionHash: json['expected_projection_hash'] as String?,
  includeAttentionSession: json['include_attention_session'] as bool,
  includeTransitionList: json['include_transition_list'] as bool,
  transitionLimit: (json['transition_limit'] as num?)?.toInt(),
  metadata: json['metadata'] as Map<String, dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$ResolveEnvironmentSessionAttentionRequestToJson(
  ResolveEnvironmentSessionAttentionRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'environment_session_id': const UuidValueConverter().toJson(
    instance.environmentSessionId,
  ),
  'environment_navigation_context_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentNavigationContextId,
    const UuidValueConverter().toJson,
  ),
  'environment_session_thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentSessionThreadId,
    const UuidValueConverter().toJson,
  ),
  'environment_session_attention_session_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.environmentSessionAttentionSessionId,
        const UuidValueConverter().toJson,
      ),
  'expected_attention_session_id': _$JsonConverterToJson<String, UuidValue>(
    instance.expectedAttentionSessionId,
    const UuidValueConverter().toJson,
  ),
  'attention_focus_transition_id': _$JsonConverterToJson<String, UuidValue>(
    instance.attentionFocusTransitionId,
    const UuidValueConverter().toJson,
  ),
  'expected_attention_session_section_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.expectedAttentionSessionSectionId,
        const UuidValueConverter().toJson,
      ),
  'expected_focus_scope_id': _$JsonConverterToJson<String, UuidValue>(
    instance.expectedFocusScopeId,
    const UuidValueConverter().toJson,
  ),
  'expected_object_instance_graph_commit_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.expectedObjectInstanceGraphCommitId,
        const UuidValueConverter().toJson,
      ),
  'expected_projection_hash': instance.expectedProjectionHash,
  'include_attention_session': instance.includeAttentionSession,
  'include_transition_list': instance.includeTransitionList,
  'transition_limit': instance.transitionLimit,
  'metadata': instance.metadata,
  'operation': instance.$type,
};

MountEnvironmentSessionAttentionRequest
_$MountEnvironmentSessionAttentionRequestFromJson(Map<String, dynamic> json) =>
    MountEnvironmentSessionAttentionRequest(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentId: const UuidValueConverter().fromJson(
        json['environment_id'] as String,
      ),
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
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentSessionId: const UuidValueConverter().fromJson(
        json['environment_session_id'] as String,
      ),
      attentionSessionId: const UuidValueConverter().fromJson(
        json['attention_session_id'] as String,
      ),
      key: json['key'] as String?,
      title: json['title'] as String?,
      status: json['status'] as String,
      metadata: json['metadata'] as Map<String, dynamic>,
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$MountEnvironmentSessionAttentionRequestToJson(
  MountEnvironmentSessionAttentionRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'environment_session_id': const UuidValueConverter().toJson(
    instance.environmentSessionId,
  ),
  'attention_session_id': const UuidValueConverter().toJson(
    instance.attentionSessionId,
  ),
  'key': instance.key,
  'title': instance.title,
  'status': instance.status,
  'metadata': instance.metadata,
  'operation': instance.$type,
};

CreateEnvironmentNavigationContextRequest
_$CreateEnvironmentNavigationContextRequestFromJson(
  Map<String, dynamic> json,
) => CreateEnvironmentNavigationContextRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentSessionId: const UuidValueConverter().fromJson(
    json['environment_session_id'] as String,
  ),
  sessionJoinReceipt: EnvironmentSessionJoinReceipt.fromJson(
    json['session_join_receipt'] as Map<String, dynamic>,
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
  metadata: json['metadata'] as Map<String, dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$CreateEnvironmentNavigationContextRequestToJson(
  CreateEnvironmentNavigationContextRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'environment_session_id': const UuidValueConverter().toJson(
    instance.environmentSessionId,
  ),
  'session_join_receipt': instance.sessionJoinReceipt.toJson(),
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
  'metadata': instance.metadata,
  'operation': instance.$type,
};

SelectEnvironmentNavigationTargetRequest
_$SelectEnvironmentNavigationTargetRequestFromJson(Map<String, dynamic> json) =>
    SelectEnvironmentNavigationTargetRequest(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentId: const UuidValueConverter().fromJson(
        json['environment_id'] as String,
      ),
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
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentSessionId: const UuidValueConverter().fromJson(
        json['environment_session_id'] as String,
      ),
      environmentNavigationContextId: const UuidValueConverter().fromJson(
        json['environment_navigation_context_id'] as String,
      ),
      sessionJoinReceipt: EnvironmentSessionJoinReceipt.fromJson(
        json['session_join_receipt'] as Map<String, dynamic>,
      ),
      selectedProcessId: _$JsonConverterFromJson<String, UuidValue>(
        json['selected_process_id'],
        const UuidValueConverter().fromJson,
      ),
      selectedThreadId: _$JsonConverterFromJson<String, UuidValue>(
        json['selected_thread_id'],
        const UuidValueConverter().fromJson,
      ),
      expectedHeadCommitId: _$JsonConverterFromJson<String, UuidValue>(
        json['expected_head_commit_id'],
        const UuidValueConverter().fromJson,
      ),
      expectedGraphHashPre: json['expected_graph_hash_pre'] as String?,
      reason: json['reason'] as String?,
      metadata: json['metadata'] as Map<String, dynamic>,
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$SelectEnvironmentNavigationTargetRequestToJson(
  SelectEnvironmentNavigationTargetRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'environment_session_id': const UuidValueConverter().toJson(
    instance.environmentSessionId,
  ),
  'environment_navigation_context_id': const UuidValueConverter().toJson(
    instance.environmentNavigationContextId,
  ),
  'session_join_receipt': instance.sessionJoinReceipt.toJson(),
  'selected_process_id': _$JsonConverterToJson<String, UuidValue>(
    instance.selectedProcessId,
    const UuidValueConverter().toJson,
  ),
  'selected_thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.selectedThreadId,
    const UuidValueConverter().toJson,
  ),
  'expected_head_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.expectedHeadCommitId,
    const UuidValueConverter().toJson,
  ),
  'expected_graph_hash_pre': instance.expectedGraphHashPre,
  'reason': instance.reason,
  'metadata': instance.metadata,
  'operation': instance.$type,
};

DescribeEnvironmentNavigationContextRequest
_$DescribeEnvironmentNavigationContextRequestFromJson(
  Map<String, dynamic> json,
) => DescribeEnvironmentNavigationContextRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  environmentSessionId: const UuidValueConverter().fromJson(
    json['environment_session_id'] as String,
  ),
  environmentNavigationContextId: const UuidValueConverter().fromJson(
    json['environment_navigation_context_id'] as String,
  ),
  sessionJoinReceipt: EnvironmentSessionJoinReceipt.fromJson(
    json['session_join_receipt'] as Map<String, dynamic>,
  ),
  includeCommit: json['include_commit'] as bool,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DescribeEnvironmentNavigationContextRequestToJson(
  DescribeEnvironmentNavigationContextRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'environment_session_id': const UuidValueConverter().toJson(
    instance.environmentSessionId,
  ),
  'environment_navigation_context_id': const UuidValueConverter().toJson(
    instance.environmentNavigationContextId,
  ),
  'session_join_receipt': instance.sessionJoinReceipt.toJson(),
  'include_commit': instance.includeCommit,
  'operation': instance.$type,
};

ListEnvironmentNavigationContextsRequest
_$ListEnvironmentNavigationContextsRequestFromJson(Map<String, dynamic> json) =>
    ListEnvironmentNavigationContextsRequest(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentId: const UuidValueConverter().fromJson(
        json['environment_id'] as String,
      ),
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
      environmentSessionId: const UuidValueConverter().fromJson(
        json['environment_session_id'] as String,
      ),
      sessionJoinReceipt: EnvironmentSessionJoinReceipt.fromJson(
        json['session_join_receipt'] as Map<String, dynamic>,
      ),
      includeClosed: json['include_closed'] as bool,
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$ListEnvironmentNavigationContextsRequestToJson(
  ListEnvironmentNavigationContextsRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'environment_session_id': const UuidValueConverter().toJson(
    instance.environmentSessionId,
  ),
  'session_join_receipt': instance.sessionJoinReceipt.toJson(),
  'include_closed': instance.includeClosed,
  'operation': instance.$type,
};

InvokeFunctionRequest _$InvokeFunctionRequestFromJson(
  Map<String, dynamic> json,
) => InvokeFunctionRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  callTarget: InvokeFunctionCallTargetExtension.fromJson(
    json['call_target'] as String,
  ),
  objectId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_id'],
    const UuidValueConverter().fromJson,
  ),
  objectProjectionGraphId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_projection_graph_id'],
    const UuidValueConverter().fromJson,
  ),
  objectProjectionGraphIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_projection_graph_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  functionId: const UuidValueConverter().fromJson(
    json['function_id'] as String,
  ),
  args: json['args'] as List<dynamic>,
  kwargs: json['kwargs'] as Map<String, dynamic>,
  expectedGraphHashPre: json['expected_graph_hash_pre'] as String?,
  expectedHeadCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['expected_head_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  commit: json['commit'] as bool,
  publish: json['publish'] as bool,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InvokeFunctionRequestToJson(
  InvokeFunctionRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'call_target': InvokeFunctionCallTargetExtension.toJson(instance.callTarget),
  'object_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectId,
    const UuidValueConverter().toJson,
  ),
  'object_projection_graph_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectProjectionGraphId,
    const UuidValueConverter().toJson,
  ),
  'object_projection_graph_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.objectProjectionGraphIdentityId,
        const UuidValueConverter().toJson,
      ),
  'function_id': const UuidValueConverter().toJson(instance.functionId),
  'args': instance.args,
  'kwargs': instance.kwargs,
  'expected_graph_hash_pre': instance.expectedGraphHashPre,
  'expected_head_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.expectedHeadCommitId,
    const UuidValueConverter().toJson,
  ),
  'commit': instance.commit,
  'publish': instance.publish,
  'operation': instance.$type,
};

EnvironmentServiceOperationRequest _$EnvironmentServiceOperationRequestFromJson(
  Map<String, dynamic> json,
) => EnvironmentServiceOperationRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  serviceOperation: EnvironmentServiceOperation.fromJson(
    json['service_operation'] as Map<String, dynamic>,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$EnvironmentServiceOperationRequestToJson(
  EnvironmentServiceOperationRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'service_operation': instance.serviceOperation.toJson(),
  'operation': instance.$type,
};

FetchCapabilitiesResponse _$FetchCapabilitiesResponseFromJson(
  Map<String, dynamic> json,
) => FetchCapabilitiesResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  roles:
      (json['roles'] as List<dynamic>?)
          ?.map((e) => CapabilityRole.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  functions:
      (json['functions'] as List<dynamic>?)
          ?.map((e) => CapabilityFunction.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  objects:
      (json['objects'] as List<dynamic>?)
          ?.map((e) => CapabilityObject.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$FetchCapabilitiesResponseToJson(
  FetchCapabilitiesResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'roles': instance.roles.map((e) => e.toJson()).toList(),
  'functions': instance.functions.map((e) => e.toJson()).toList(),
  'objects': instance.objects.map((e) => e.toJson()).toList(),
  'operation': instance.$type,
};

DescribeEnvironmentConfigResponse _$DescribeEnvironmentConfigResponseFromJson(
  Map<String, dynamic> json,
) => DescribeEnvironmentConfigResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  title: json['title'] as String?,
  environmentConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_config_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentConfigTitle: json['environment_config_title'] as String?,
  canonicalLanguage: json['canonical_language'] as String?,
  bundleManifestPath: json['bundle_manifest_path'] as String?,
  bundleManifestHttpPath: json['bundle_manifest_http_path'] as String?,
  bundleArtifactHttpPathPrefix:
      json['bundle_artifact_http_path_prefix'] as String?,
  bundleDescriptorHttpPath: json['bundle_descriptor_http_path'] as String?,
  bundleHeadId: json['bundle_head_id'] as String?,
  bundleReleaseIdentity:
      json['bundle_release_identity'] as Map<String, dynamic>?,
  ocgId: _$JsonConverterFromJson<String, UuidValue>(
    json['ocg_id'],
    const UuidValueConverter().fromJson,
  ),
  opgHashes:
      (json['opg_hashes'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  opgs:
      (json['opgs'] as List<dynamic>?)
          ?.map(
            (e) => DescribeEnvironmentOPG.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DescribeEnvironmentConfigResponseToJson(
  DescribeEnvironmentConfigResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'title': instance.title,
  'environment_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentConfigId,
    const UuidValueConverter().toJson,
  ),
  'environment_config_title': instance.environmentConfigTitle,
  'canonical_language': instance.canonicalLanguage,
  'bundle_manifest_path': instance.bundleManifestPath,
  'bundle_manifest_http_path': instance.bundleManifestHttpPath,
  'bundle_artifact_http_path_prefix': instance.bundleArtifactHttpPathPrefix,
  'bundle_descriptor_http_path': instance.bundleDescriptorHttpPath,
  'bundle_head_id': instance.bundleHeadId,
  'bundle_release_identity': instance.bundleReleaseIdentity,
  'ocg_id': _$JsonConverterToJson<String, UuidValue>(
    instance.ocgId,
    const UuidValueConverter().toJson,
  ),
  'opg_hashes': instance.opgHashes,
  'opgs': instance.opgs.map((e) => e.toJson()).toList(),
  'operation': instance.$type,
};

DescribeEnvironmentResponse _$DescribeEnvironmentResponseFromJson(
  Map<String, dynamic> json,
) => DescribeEnvironmentResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  status: json['status'] as String,
  error: json['error'] as String?,
  environmentConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_config_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentConfigTitle: json['environment_config_title'] as String?,
  bundleManifestPath: json['bundle_manifest_path'] as String?,
  bundleManifestHttpPath: json['bundle_manifest_http_path'] as String?,
  bundleArtifactHttpPathPrefix:
      json['bundle_artifact_http_path_prefix'] as String?,
  bundleDescriptorHttpPath: json['bundle_descriptor_http_path'] as String?,
  bundleHeadId: json['bundle_head_id'] as String?,
  bundleReleaseIdentity:
      json['bundle_release_identity'] as Map<String, dynamic>?,
  ocgId: _$JsonConverterFromJson<String, UuidValue>(
    json['ocg_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentTitle: json['environment_title'] as String?,
  environmentDescription: json['environment_description'] as String?,
  bootProcessId: _$JsonConverterFromJson<String, UuidValue>(
    json['boot_process_id'],
    const UuidValueConverter().fromJson,
  ),
  bootThreadId: _$JsonConverterFromJson<String, UuidValue>(
    json['boot_thread_id'],
    const UuidValueConverter().fromJson,
  ),
  bootBranchId: _$JsonConverterFromJson<String, UuidValue>(
    json['boot_branch_id'],
    const UuidValueConverter().fromJson,
  ),
  headCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['head_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  headGraphHashPost: json['head_graph_hash_post'] as String?,
  headObjectInstanceGraphId: _$JsonConverterFromJson<String, UuidValue>(
    json['head_object_instance_graph_id'],
    const UuidValueConverter().fromJson,
  ),
  headRootObjectId: _$JsonConverterFromJson<String, UuidValue>(
    json['head_root_object_id'],
    const UuidValueConverter().fromJson,
  ),
  headVersion: (json['head_version'] as num?)?.toInt(),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DescribeEnvironmentResponseToJson(
  DescribeEnvironmentResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'status': instance.status,
  'error': instance.error,
  'environment_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentConfigId,
    const UuidValueConverter().toJson,
  ),
  'environment_config_title': instance.environmentConfigTitle,
  'bundle_manifest_path': instance.bundleManifestPath,
  'bundle_manifest_http_path': instance.bundleManifestHttpPath,
  'bundle_artifact_http_path_prefix': instance.bundleArtifactHttpPathPrefix,
  'bundle_descriptor_http_path': instance.bundleDescriptorHttpPath,
  'bundle_head_id': instance.bundleHeadId,
  'bundle_release_identity': instance.bundleReleaseIdentity,
  'ocg_id': _$JsonConverterToJson<String, UuidValue>(
    instance.ocgId,
    const UuidValueConverter().toJson,
  ),
  'environment_title': instance.environmentTitle,
  'environment_description': instance.environmentDescription,
  'boot_process_id': _$JsonConverterToJson<String, UuidValue>(
    instance.bootProcessId,
    const UuidValueConverter().toJson,
  ),
  'boot_thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.bootThreadId,
    const UuidValueConverter().toJson,
  ),
  'boot_branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.bootBranchId,
    const UuidValueConverter().toJson,
  ),
  'head_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.headCommitId,
    const UuidValueConverter().toJson,
  ),
  'head_graph_hash_post': instance.headGraphHashPost,
  'head_object_instance_graph_id': _$JsonConverterToJson<String, UuidValue>(
    instance.headObjectInstanceGraphId,
    const UuidValueConverter().toJson,
  ),
  'head_root_object_id': _$JsonConverterToJson<String, UuidValue>(
    instance.headRootObjectId,
    const UuidValueConverter().toJson,
  ),
  'head_version': instance.headVersion,
  'operation': instance.$type,
};

DescribeEnvironmentTopologyResponse
_$DescribeEnvironmentTopologyResponseFromJson(Map<String, dynamic> json) =>
    DescribeEnvironmentTopologyResponse(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentId: const UuidValueConverter().fromJson(
        json['environment_id'] as String,
      ),
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
      status: json['status'] as String,
      error: json['error'] as String?,
      processes:
          (json['processes'] as List<dynamic>?)
              ?.map(
                (e) => DescribeEnvironmentTopologyProcess.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$DescribeEnvironmentTopologyResponseToJson(
  DescribeEnvironmentTopologyResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'status': instance.status,
  'error': instance.error,
  'processes': instance.processes.map((e) => e.toJson()).toList(),
  'operation': instance.$type,
};

DescribeEnvironmentStatusResponse _$DescribeEnvironmentStatusResponseFromJson(
  Map<String, dynamic> json,
) => DescribeEnvironmentStatusResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  status: json['status'] as String,
  error: json['error'] as String?,
  statusVersion: json['status_version'] as String,
  blocks:
      (json['blocks'] as List<dynamic>?)
          ?.map(
            (e) => EnvironmentStatusBlock.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  refusals: json['refusals'] as List<dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DescribeEnvironmentStatusResponseToJson(
  DescribeEnvironmentStatusResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'status': instance.status,
  'error': instance.error,
  'status_version': instance.statusVersion,
  'blocks': instance.blocks.map((e) => e.toJson()).toList(),
  'refusals': instance.refusals,
  'operation': instance.$type,
};

EnsureReadyResponse _$EnsureReadyResponseFromJson(Map<String, dynamic> json) =>
    EnsureReadyResponse(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentId: const UuidValueConverter().fromJson(
        json['environment_id'] as String,
      ),
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
      status: json['status'] as String,
      error: json['error'] as String?,
      bundleManifestPath: json['bundle_manifest_path'] as String?,
      bundleManifestHttpPath: json['bundle_manifest_http_path'] as String?,
      bundleArtifactHttpPathPrefix:
          json['bundle_artifact_http_path_prefix'] as String?,
      bundleDescriptorHttpPath: json['bundle_descriptor_http_path'] as String?,
      bundleHeadId: json['bundle_head_id'] as String?,
      bundleReleaseIdentity:
          json['bundle_release_identity'] as Map<String, dynamic>?,
      ocgId: _$JsonConverterFromJson<String, UuidValue>(
        json['ocg_id'],
        const UuidValueConverter().fromJson,
      ),
      opgHashes:
          (json['opg_hashes'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      readinessReceipt: json['readiness_receipt'] == null
          ? null
          : EnvironmentReadinessReceipt.fromJson(
              json['readiness_receipt'] as Map<String, dynamic>,
            ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$EnsureReadyResponseToJson(
  EnsureReadyResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'status': instance.status,
  'error': instance.error,
  'bundle_manifest_path': instance.bundleManifestPath,
  'bundle_manifest_http_path': instance.bundleManifestHttpPath,
  'bundle_artifact_http_path_prefix': instance.bundleArtifactHttpPathPrefix,
  'bundle_descriptor_http_path': instance.bundleDescriptorHttpPath,
  'bundle_head_id': instance.bundleHeadId,
  'bundle_release_identity': instance.bundleReleaseIdentity,
  'ocg_id': _$JsonConverterToJson<String, UuidValue>(
    instance.ocgId,
    const UuidValueConverter().toJson,
  ),
  'opg_hashes': instance.opgHashes,
  'readiness_receipt': instance.readinessReceipt?.toJson(),
  'operation': instance.$type,
};

GetLaneHeadResponse _$GetLaneHeadResponseFromJson(Map<String, dynamic> json) =>
    GetLaneHeadResponse(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentId: const UuidValueConverter().fromJson(
        json['environment_id'] as String,
      ),
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
      status: json['status'] as String,
      error: json['error'] as String?,
      commitId: _$JsonConverterFromJson<String, UuidValue>(
        json['commit_id'],
        const UuidValueConverter().fromJson,
      ),
      objectInstanceGraphCommitId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_instance_graph_commit_id'],
        const UuidValueConverter().fromJson,
      ),
      graphHashPost: json['graph_hash_post'] as String?,
      objectInstanceGraphId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_instance_graph_id'],
        const UuidValueConverter().fromJson,
      ),
      objectInstanceGraphIdentityId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_instance_graph_identity_id'],
        const UuidValueConverter().fromJson,
      ),
      objectInstanceGraphBranchId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_instance_graph_branch_id'],
        const UuidValueConverter().fromJson,
      ),
      objectProjectionGraphId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_projection_graph_id'],
        const UuidValueConverter().fromJson,
      ),
      objectProjectionGraphIdentityId:
          _$JsonConverterFromJson<String, UuidValue>(
            json['object_projection_graph_identity_id'],
            const UuidValueConverter().fromJson,
          ),
      rootObjectId: _$JsonConverterFromJson<String, UuidValue>(
        json['root_object_id'],
        const UuidValueConverter().fromJson,
      ),
      headVersion: (json['head_version'] as num?)?.toInt(),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$GetLaneHeadResponseToJson(
  GetLaneHeadResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'status': instance.status,
  'error': instance.error,
  'commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.commitId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphCommitId,
    const UuidValueConverter().toJson,
  ),
  'graph_hash_post': instance.graphHashPost,
  'object_instance_graph_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_identity_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphIdentityId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphBranchId,
    const UuidValueConverter().toJson,
  ),
  'object_projection_graph_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectProjectionGraphId,
    const UuidValueConverter().toJson,
  ),
  'object_projection_graph_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.objectProjectionGraphIdentityId,
        const UuidValueConverter().toJson,
      ),
  'root_object_id': _$JsonConverterToJson<String, UuidValue>(
    instance.rootObjectId,
    const UuidValueConverter().toJson,
  ),
  'head_version': instance.headVersion,
  'operation': instance.$type,
};

GetObjectInstanceGraphCommitResponse
_$GetObjectInstanceGraphCommitResponseFromJson(Map<String, dynamic> json) =>
    GetObjectInstanceGraphCommitResponse(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentId: const UuidValueConverter().fromJson(
        json['environment_id'] as String,
      ),
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
      status: json['status'] as String,
      error: json['error'] as String?,
      commitId: _$JsonConverterFromJson<String, UuidValue>(
        json['commit_id'],
        const UuidValueConverter().fromJson,
      ),
      objectInstanceGraphCommitId: const UuidValueConverter().fromJson(
        json['object_instance_graph_commit_id'] as String,
      ),
      objectInstanceGraphId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_instance_graph_id'],
        const UuidValueConverter().fromJson,
      ),
      objectInstanceGraphIdentityId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_instance_graph_identity_id'],
        const UuidValueConverter().fromJson,
      ),
      objectInstanceGraphBranchId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_instance_graph_branch_id'],
        const UuidValueConverter().fromJson,
      ),
      objectProjectionGraphId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_projection_graph_id'],
        const UuidValueConverter().fromJson,
      ),
      objectProjectionGraphIdentityId:
          _$JsonConverterFromJson<String, UuidValue>(
            json['object_projection_graph_identity_id'],
            const UuidValueConverter().fromJson,
          ),
      rootObjectId: _$JsonConverterFromJson<String, UuidValue>(
        json['root_object_id'],
        const UuidValueConverter().fromJson,
      ),
      graphHashPre: json['graph_hash_pre'] as String?,
      graphHashPost: json['graph_hash_post'] as String?,
      commit: json['commit'] as Map<String, dynamic>?,
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$GetObjectInstanceGraphCommitResponseToJson(
  GetObjectInstanceGraphCommitResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'status': instance.status,
  'error': instance.error,
  'commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.commitId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_commit_id': const UuidValueConverter().toJson(
    instance.objectInstanceGraphCommitId,
  ),
  'object_instance_graph_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_identity_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphIdentityId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphBranchId,
    const UuidValueConverter().toJson,
  ),
  'object_projection_graph_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectProjectionGraphId,
    const UuidValueConverter().toJson,
  ),
  'object_projection_graph_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.objectProjectionGraphIdentityId,
        const UuidValueConverter().toJson,
      ),
  'root_object_id': _$JsonConverterToJson<String, UuidValue>(
    instance.rootObjectId,
    const UuidValueConverter().toJson,
  ),
  'graph_hash_pre': instance.graphHashPre,
  'graph_hash_post': instance.graphHashPost,
  'commit': instance.commit,
  'operation': instance.$type,
};

MaterializeCommittedProjectionDtoResponse
_$MaterializeCommittedProjectionDtoResponseFromJson(
  Map<String, dynamic> json,
) => MaterializeCommittedProjectionDtoResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  status: json['status'] as String,
  error: json['error'] as String?,
  refusalCode: json['refusal_code'] as String?,
  dtoPayload: json['dto_payload'] as Map<String, dynamic>?,
  dtoClassRef: json['dto_class_ref'] as String?,
  classConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['class_config_id'],
    const UuidValueConverter().fromJson,
  ),
  dtoPackageName: json['dto_package_name'] as String?,
  dtoImportRoot: json['dto_import_root'] as String?,
  dtoArtifactDigest: json['dto_artifact_digest'] as String?,
  commitId: _$JsonConverterFromJson<String, UuidValue>(
    json['commit_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_id'],
    const UuidValueConverter().fromJson,
  ),
  rootObjectId: _$JsonConverterFromJson<String, UuidValue>(
    json['root_object_id'],
    const UuidValueConverter().fromJson,
  ),
  graphHashPost: json['graph_hash_post'] as String?,
  materializerVersion: json['materializer_version'] as String?,
  evidence: json['evidence'] as Map<String, dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$MaterializeCommittedProjectionDtoResponseToJson(
  MaterializeCommittedProjectionDtoResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'status': instance.status,
  'error': instance.error,
  'refusal_code': instance.refusalCode,
  'dto_payload': instance.dtoPayload,
  'dto_class_ref': instance.dtoClassRef,
  'class_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.classConfigId,
    const UuidValueConverter().toJson,
  ),
  'dto_package_name': instance.dtoPackageName,
  'dto_import_root': instance.dtoImportRoot,
  'dto_artifact_digest': instance.dtoArtifactDigest,
  'commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.commitId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphCommitId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphId,
    const UuidValueConverter().toJson,
  ),
  'root_object_id': _$JsonConverterToJson<String, UuidValue>(
    instance.rootObjectId,
    const UuidValueConverter().toJson,
  ),
  'graph_hash_post': instance.graphHashPost,
  'materializer_version': instance.materializerVersion,
  'evidence': instance.evidence,
  'operation': instance.$type,
};

ResolveRuntimeRefsResponse _$ResolveRuntimeRefsResponseFromJson(
  Map<String, dynamic> json,
) => ResolveRuntimeRefsResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  status: json['status'] as String,
  error: json['error'] as String?,
  functionTargets:
      (json['function_targets'] as List<dynamic>?)
          ?.map(
            (e) => ResolvedRuntimeFunctionTarget.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  classRefs:
      (json['class_refs'] as List<dynamic>?)
          ?.map(
            (e) => ResolvedRuntimeClassRef.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  evidence: json['evidence'] as Map<String, dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$ResolveRuntimeRefsResponseToJson(
  ResolveRuntimeRefsResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'status': instance.status,
  'error': instance.error,
  'function_targets': instance.functionTargets.map((e) => e.toJson()).toList(),
  'class_refs': instance.classRefs.map((e) => e.toJson()).toList(),
  'evidence': instance.evidence,
  'operation': instance.$type,
};

ConfigureServiceApiDependencyRoutesResponse
_$ConfigureServiceApiDependencyRoutesResponseFromJson(
  Map<String, dynamic> json,
) => ConfigureServiceApiDependencyRoutesResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  status: json['status'] as String,
  error: json['error'] as String?,
  routeCount: (json['route_count'] as num).toInt(),
  routeConsumersStarted: json['route_consumers_started'] as bool,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$ConfigureServiceApiDependencyRoutesResponseToJson(
  ConfigureServiceApiDependencyRoutesResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'status': instance.status,
  'error': instance.error,
  'route_count': instance.routeCount,
  'route_consumers_started': instance.routeConsumersStarted,
  'operation': instance.$type,
};

AttachEnvironmentOntologyResponse _$AttachEnvironmentOntologyResponseFromJson(
  Map<String, dynamic> json,
) => AttachEnvironmentOntologyResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  status: json['status'] as String,
  error: json['error'] as String?,
  membership: json['membership'] == null
      ? null
      : EnvironmentOntologyMembership.fromJson(
          json['membership'] as Map<String, dynamic>,
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
  evidence: json['evidence'] as Map<String, dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$AttachEnvironmentOntologyResponseToJson(
  AttachEnvironmentOntologyResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'status': instance.status,
  'error': instance.error,
  'membership': instance.membership?.toJson(),
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
  'evidence': instance.evidence,
  'operation': instance.$type,
};

EnsureEnvironmentOntologyRuntimeResponse
_$EnsureEnvironmentOntologyRuntimeResponseFromJson(Map<String, dynamic> json) =>
    EnsureEnvironmentOntologyRuntimeResponse(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentId: const UuidValueConverter().fromJson(
        json['environment_id'] as String,
      ),
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
      status: json['status'] as String,
      error: json['error'] as String?,
      ontologyId: _$JsonConverterFromJson<String, UuidValue>(
        json['ontology_id'],
        const UuidValueConverter().fromJson,
      ),
      packageName: json['package_name'] as String?,
      fqnPrefix: json['fqn_prefix'] as String?,
      artifactSetId: json['artifact_set_id'] as String?,
      runtimeProjectionDescriptorCount:
          (json['runtime_projection_descriptor_count'] as num).toInt(),
      capabilityObjectCount: (json['capability_object_count'] as num).toInt(),
      capabilityFunctionCount: (json['capability_function_count'] as num)
          .toInt(),
      registeredArtifactRefCount: (json['registered_artifact_ref_count'] as num)
          .toInt(),
      registryArtifactRefCount: (json['registry_artifact_ref_count'] as num)
          .toInt(),
      membershipCommitId: _$JsonConverterFromJson<String, UuidValue>(
        json['membership_commit_id'],
        const UuidValueConverter().fromJson,
      ),
      evidence: json['evidence'] as Map<String, dynamic>,
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$EnsureEnvironmentOntologyRuntimeResponseToJson(
  EnsureEnvironmentOntologyRuntimeResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'status': instance.status,
  'error': instance.error,
  'ontology_id': _$JsonConverterToJson<String, UuidValue>(
    instance.ontologyId,
    const UuidValueConverter().toJson,
  ),
  'package_name': instance.packageName,
  'fqn_prefix': instance.fqnPrefix,
  'artifact_set_id': instance.artifactSetId,
  'runtime_projection_descriptor_count':
      instance.runtimeProjectionDescriptorCount,
  'capability_object_count': instance.capabilityObjectCount,
  'capability_function_count': instance.capabilityFunctionCount,
  'registered_artifact_ref_count': instance.registeredArtifactRefCount,
  'registry_artifact_ref_count': instance.registryArtifactRefCount,
  'membership_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.membershipCommitId,
    const UuidValueConverter().toJson,
  ),
  'evidence': instance.evidence,
  'operation': instance.$type,
};

ListEnvironmentOntologiesResponse _$ListEnvironmentOntologiesResponseFromJson(
  Map<String, dynamic> json,
) => ListEnvironmentOntologiesResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  status: json['status'] as String,
  error: json['error'] as String?,
  memberships:
      (json['memberships'] as List<dynamic>?)
          ?.map(
            (e) => EnvironmentOntologyMembership.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
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
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$ListEnvironmentOntologiesResponseToJson(
  ListEnvironmentOntologiesResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'status': instance.status,
  'error': instance.error,
  'memberships': instance.memberships.map((e) => e.toJson()).toList(),
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
  'operation': instance.$type,
};

ResolveEnvironmentSessionAttentionResponse
_$ResolveEnvironmentSessionAttentionResponseFromJson(
  Map<String, dynamic> json,
) => ResolveEnvironmentSessionAttentionResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  status: json['status'] as String,
  error: json['error'] as String?,
  resolution: json['resolution'] == null
      ? null
      : EnvironmentSessionAttentionResolution.fromJson(
          json['resolution'] as Map<String, dynamic>,
        ),
  evidence: json['evidence'] as Map<String, dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$ResolveEnvironmentSessionAttentionResponseToJson(
  ResolveEnvironmentSessionAttentionResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'status': instance.status,
  'error': instance.error,
  'resolution': instance.resolution?.toJson(),
  'evidence': instance.evidence,
  'operation': instance.$type,
};

MountEnvironmentSessionAttentionResponse
_$MountEnvironmentSessionAttentionResponseFromJson(Map<String, dynamic> json) =>
    MountEnvironmentSessionAttentionResponse(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentId: const UuidValueConverter().fromJson(
        json['environment_id'] as String,
      ),
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
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentSessionAttentionSessionId: const UuidValueConverter().fromJson(
        json['environment_session_attention_session_id'] as String,
      ),
      environmentSessionId: const UuidValueConverter().fromJson(
        json['environment_session_id'] as String,
      ),
      attentionSessionId: const UuidValueConverter().fromJson(
        json['attention_session_id'] as String,
      ),
      key: json['key'] as String?,
      title: json['title'] as String?,
      status: json['status'] as String,
      metadata: json['metadata'] as Map<String, dynamic>,
      domainCommitId: _$JsonConverterFromJson<String, UuidValue>(
        json['domain_commit_id'],
        const UuidValueConverter().fromJson,
      ),
      objectInstanceGraphCommitId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_instance_graph_commit_id'],
        const UuidValueConverter().fromJson,
      ),
      graphHashPost: json['graph_hash_post'] as String?,
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$MountEnvironmentSessionAttentionResponseToJson(
  MountEnvironmentSessionAttentionResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'environment_session_attention_session_id': const UuidValueConverter().toJson(
    instance.environmentSessionAttentionSessionId,
  ),
  'environment_session_id': const UuidValueConverter().toJson(
    instance.environmentSessionId,
  ),
  'attention_session_id': const UuidValueConverter().toJson(
    instance.attentionSessionId,
  ),
  'key': instance.key,
  'title': instance.title,
  'status': instance.status,
  'metadata': instance.metadata,
  'domain_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.domainCommitId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphCommitId,
    const UuidValueConverter().toJson,
  ),
  'graph_hash_post': instance.graphHashPost,
  'operation': instance.$type,
};

CreateEnvironmentNavigationContextResponse
_$CreateEnvironmentNavigationContextResponseFromJson(
  Map<String, dynamic> json,
) => CreateEnvironmentNavigationContextResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  accepted: json['accepted'] as bool,
  status: json['status'] as String,
  error: json['error'] as String?,
  context: json['context'] == null
      ? null
      : EnvironmentNavigationContextView.fromJson(
          json['context'] as Map<String, dynamic>,
        ),
  receipt: EnvironmentNavigationCommitReceipt.fromJson(
    json['receipt'] as Map<String, dynamic>,
  ),
  evidence: json['evidence'] as Map<String, dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$CreateEnvironmentNavigationContextResponseToJson(
  CreateEnvironmentNavigationContextResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'accepted': instance.accepted,
  'status': instance.status,
  'error': instance.error,
  'context': instance.context?.toJson(),
  'receipt': instance.receipt.toJson(),
  'evidence': instance.evidence,
  'operation': instance.$type,
};

SelectEnvironmentNavigationTargetResponse
_$SelectEnvironmentNavigationTargetResponseFromJson(
  Map<String, dynamic> json,
) => SelectEnvironmentNavigationTargetResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  accepted: json['accepted'] as bool,
  status: json['status'] as String,
  error: json['error'] as String?,
  context: json['context'] == null
      ? null
      : EnvironmentNavigationContextView.fromJson(
          json['context'] as Map<String, dynamic>,
        ),
  receipt: EnvironmentNavigationCommitReceipt.fromJson(
    json['receipt'] as Map<String, dynamic>,
  ),
  evidence: json['evidence'] as Map<String, dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$SelectEnvironmentNavigationTargetResponseToJson(
  SelectEnvironmentNavigationTargetResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'accepted': instance.accepted,
  'status': instance.status,
  'error': instance.error,
  'context': instance.context?.toJson(),
  'receipt': instance.receipt.toJson(),
  'evidence': instance.evidence,
  'operation': instance.$type,
};

DescribeEnvironmentNavigationContextResponse
_$DescribeEnvironmentNavigationContextResponseFromJson(
  Map<String, dynamic> json,
) => DescribeEnvironmentNavigationContextResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  status: json['status'] as String,
  error: json['error'] as String?,
  context: json['context'] == null
      ? null
      : EnvironmentNavigationContextView.fromJson(
          json['context'] as Map<String, dynamic>,
        ),
  blockers:
      (json['blockers'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  evidence: json['evidence'] as Map<String, dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DescribeEnvironmentNavigationContextResponseToJson(
  DescribeEnvironmentNavigationContextResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'status': instance.status,
  'error': instance.error,
  'context': instance.context?.toJson(),
  'blockers': instance.blockers,
  'evidence': instance.evidence,
  'operation': instance.$type,
};

ListEnvironmentNavigationContextsResponse
_$ListEnvironmentNavigationContextsResponseFromJson(
  Map<String, dynamic> json,
) => ListEnvironmentNavigationContextsResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  status: json['status'] as String,
  error: json['error'] as String?,
  contexts:
      (json['contexts'] as List<dynamic>?)
          ?.map(
            (e) => EnvironmentNavigationContextView.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  blockers:
      (json['blockers'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  evidence: json['evidence'] as Map<String, dynamic>,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$ListEnvironmentNavigationContextsResponseToJson(
  ListEnvironmentNavigationContextsResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'status': instance.status,
  'error': instance.error,
  'contexts': instance.contexts.map((e) => e.toJson()).toList(),
  'blockers': instance.blockers,
  'evidence': instance.evidence,
  'operation': instance.$type,
};

InvokeFunctionResponse _$InvokeFunctionResponseFromJson(
  Map<String, dynamic> json,
) => InvokeFunctionResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  status: json['status'] as String,
  payload: json['payload'],
  error: json['error'] as String?,
  logs:
      (json['logs'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  executionTimeMs: (json['execution_time_ms'] as num?)?.toInt(),
  rootObjectId: _$JsonConverterFromJson<String, UuidValue>(
    json['root_object_id'],
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
  changes: json['changes'] as List<dynamic>,
  commitId: _$JsonConverterFromJson<String, UuidValue>(
    json['commit_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  objectProjectionGraphId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_projection_graph_id'],
    const UuidValueConverter().fromJson,
  ),
  objectProjectionGraphIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_projection_graph_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphBranchId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_branch_id'],
    const UuidValueConverter().fromJson,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InvokeFunctionResponseToJson(
  InvokeFunctionResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'status': instance.status,
  'payload': instance.payload,
  'error': instance.error,
  'logs': instance.logs,
  'execution_time_ms': instance.executionTimeMs,
  'root_object_id': _$JsonConverterToJson<String, UuidValue>(
    instance.rootObjectId,
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
  'changes': instance.changes,
  'commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.commitId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphCommitId,
    const UuidValueConverter().toJson,
  ),
  'object_projection_graph_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectProjectionGraphId,
    const UuidValueConverter().toJson,
  ),
  'object_projection_graph_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.objectProjectionGraphIdentityId,
        const UuidValueConverter().toJson,
      ),
  'object_instance_graph_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_identity_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphIdentityId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphBranchId,
    const UuidValueConverter().toJson,
  ),
  'operation': instance.$type,
};

EnvironmentServiceOperationResponse
_$EnvironmentServiceOperationResponseFromJson(Map<String, dynamic> json) =>
    EnvironmentServiceOperationResponse(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentId: const UuidValueConverter().fromJson(
        json['environment_id'] as String,
      ),
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
      serviceOperation: EnvironmentServiceOperation.fromJson(
        json['service_operation'] as Map<String, dynamic>,
      ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$EnvironmentServiceOperationResponseToJson(
  EnvironmentServiceOperationResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'service_operation': instance.serviceOperation.toJson(),
  'operation': instance.$type,
};

LaneCommitReceiptNotification _$LaneCommitReceiptNotificationFromJson(
  Map<String, dynamic> json,
) => LaneCommitReceiptNotification(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
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
  threadId: _$JsonConverterFromJson<String, UuidValue>(
    json['thread_id'],
    const UuidValueConverter().fromJson,
  ),
  branchId: const UuidValueConverter().fromJson(json['branch_id'] as String),
  projectionHash: json['projection_hash'] as String,
  commitId: const UuidValueConverter().fromJson(json['commit_id'] as String),
  objectInstanceGraphCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  objectProjectionGraphId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_projection_graph_id'],
    const UuidValueConverter().fromJson,
  ),
  objectProjectionGraphIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_projection_graph_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphBranchId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_branch_id'],
    const UuidValueConverter().fromJson,
  ),
  createdAtUnixMs: (json['created_at_unix_ms'] as num?)?.toInt(),
  operationLabel: json['operation_label'] as String?,
  callTarget: InvokeFunctionCallTargetExtension.fromJsonNullable(
    json['call_target'] as String?,
  ),
  functionId: _$JsonConverterFromJson<String, UuidValue>(
    json['function_id'],
    const UuidValueConverter().fromJson,
  ),
  objectId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_id'],
    const UuidValueConverter().fromJson,
  ),
  classInstanceIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['class_instance_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  graphHashPost: json['graph_hash_post'] as String?,
  rootObjectId: _$JsonConverterFromJson<String, UuidValue>(
    json['root_object_id'],
    const UuidValueConverter().fromJson,
  ),
  headVersion: (json['head_version'] as num?)?.toInt(),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$LaneCommitReceiptNotificationToJson(
  LaneCommitReceiptNotification instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
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
  'thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': const UuidValueConverter().toJson(instance.branchId),
  'projection_hash': instance.projectionHash,
  'commit_id': const UuidValueConverter().toJson(instance.commitId),
  'object_instance_graph_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphCommitId,
    const UuidValueConverter().toJson,
  ),
  'object_projection_graph_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectProjectionGraphId,
    const UuidValueConverter().toJson,
  ),
  'object_projection_graph_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.objectProjectionGraphIdentityId,
        const UuidValueConverter().toJson,
      ),
  'object_instance_graph_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_identity_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphIdentityId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphBranchId,
    const UuidValueConverter().toJson,
  ),
  'created_at_unix_ms': instance.createdAtUnixMs,
  'operation_label': instance.operationLabel,
  'call_target': InvokeFunctionCallTargetExtension.toJsonNullable(
    instance.callTarget,
  ),
  'function_id': _$JsonConverterToJson<String, UuidValue>(
    instance.functionId,
    const UuidValueConverter().toJson,
  ),
  'object_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectId,
    const UuidValueConverter().toJson,
  ),
  'class_instance_identity_id': _$JsonConverterToJson<String, UuidValue>(
    instance.classInstanceIdentityId,
    const UuidValueConverter().toJson,
  ),
  'graph_hash_post': instance.graphHashPost,
  'root_object_id': _$JsonConverterToJson<String, UuidValue>(
    instance.rootObjectId,
    const UuidValueConverter().toJson,
  ),
  'head_version': instance.headVersion,
  'operation': instance.$type,
};

LaneEventReceiptNotification _$LaneEventReceiptNotificationFromJson(
  Map<String, dynamic> json,
) => LaneEventReceiptNotification(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
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
  threadId: _$JsonConverterFromJson<String, UuidValue>(
    json['thread_id'],
    const UuidValueConverter().fromJson,
  ),
  branchId: const UuidValueConverter().fromJson(json['branch_id'] as String),
  projectionHash: json['projection_hash'] as String,
  eventId: const UuidValueConverter().fromJson(json['event_id'] as String),
  eventType: json['event_type'] as String,
  source: json['source'] as String,
  createdAtUnixMs: (json['created_at_unix_ms'] as num).toInt(),
  commitId: const UuidValueConverter().fromJson(json['commit_id'] as String),
  targetActorId: _$JsonConverterFromJson<String, UuidValue>(
    json['target_actor_id'],
    const UuidValueConverter().fromJson,
  ),
  actorSubscriptionId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_subscription_id'],
    const UuidValueConverter().fromJson,
  ),
  eventConfigConditionConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['event_config_condition_config_id'],
    const UuidValueConverter().fromJson,
  ),
  graphHashPost: json['graph_hash_post'] as String?,
  objectInstanceGraphId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_id'],
    const UuidValueConverter().fromJson,
  ),
  rootObjectId: _$JsonConverterFromJson<String, UuidValue>(
    json['root_object_id'],
    const UuidValueConverter().fromJson,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$LaneEventReceiptNotificationToJson(
  LaneEventReceiptNotification instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
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
  'thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': const UuidValueConverter().toJson(instance.branchId),
  'projection_hash': instance.projectionHash,
  'event_id': const UuidValueConverter().toJson(instance.eventId),
  'event_type': instance.eventType,
  'source': instance.source,
  'created_at_unix_ms': instance.createdAtUnixMs,
  'commit_id': const UuidValueConverter().toJson(instance.commitId),
  'target_actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.targetActorId,
    const UuidValueConverter().toJson,
  ),
  'actor_subscription_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorSubscriptionId,
    const UuidValueConverter().toJson,
  ),
  'event_config_condition_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.eventConfigConditionConfigId,
    const UuidValueConverter().toJson,
  ),
  'graph_hash_post': instance.graphHashPost,
  'object_instance_graph_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphId,
    const UuidValueConverter().toJson,
  ),
  'root_object_id': _$JsonConverterToJson<String, UuidValue>(
    instance.rootObjectId,
    const UuidValueConverter().toJson,
  ),
  'operation': instance.$type,
};

LaneActionExecutionReceiptNotification
_$LaneActionExecutionReceiptNotificationFromJson(
  Map<String, dynamic> json,
) => LaneActionExecutionReceiptNotification(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
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
  threadId: _$JsonConverterFromJson<String, UuidValue>(
    json['thread_id'],
    const UuidValueConverter().fromJson,
  ),
  branchId: const UuidValueConverter().fromJson(json['branch_id'] as String),
  projectionHash: json['projection_hash'] as String,
  actionExecutionId: const UuidValueConverter().fromJson(
    json['action_execution_id'] as String,
  ),
  eventId: const UuidValueConverter().fromJson(json['event_id'] as String),
  eventType: json['event_type'] as String,
  source: json['source'] as String,
  createdAtUnixMs: (json['created_at_unix_ms'] as num).toInt(),
  commitId: const UuidValueConverter().fromJson(json['commit_id'] as String),
  targetActorId: _$JsonConverterFromJson<String, UuidValue>(
    json['target_actor_id'],
    const UuidValueConverter().fromJson,
  ),
  actorSubscriptionId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_subscription_id'],
    const UuidValueConverter().fromJson,
  ),
  eventConfigConditionConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['event_config_condition_config_id'],
    const UuidValueConverter().fromJson,
  ),
  actionBindingId: _$JsonConverterFromJson<String, UuidValue>(
    json['action_binding_id'],
    const UuidValueConverter().fromJson,
  ),
  actionConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['action_config_id'],
    const UuidValueConverter().fromJson,
  ),
  actionType: json['action_type'] as String?,
  graphHashPost: json['graph_hash_post'] as String?,
  objectInstanceGraphId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_id'],
    const UuidValueConverter().fromJson,
  ),
  rootObjectId: _$JsonConverterFromJson<String, UuidValue>(
    json['root_object_id'],
    const UuidValueConverter().fromJson,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$LaneActionExecutionReceiptNotificationToJson(
  LaneActionExecutionReceiptNotification instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
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
  'thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': const UuidValueConverter().toJson(instance.branchId),
  'projection_hash': instance.projectionHash,
  'action_execution_id': const UuidValueConverter().toJson(
    instance.actionExecutionId,
  ),
  'event_id': const UuidValueConverter().toJson(instance.eventId),
  'event_type': instance.eventType,
  'source': instance.source,
  'created_at_unix_ms': instance.createdAtUnixMs,
  'commit_id': const UuidValueConverter().toJson(instance.commitId),
  'target_actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.targetActorId,
    const UuidValueConverter().toJson,
  ),
  'actor_subscription_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorSubscriptionId,
    const UuidValueConverter().toJson,
  ),
  'event_config_condition_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.eventConfigConditionConfigId,
    const UuidValueConverter().toJson,
  ),
  'action_binding_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actionBindingId,
    const UuidValueConverter().toJson,
  ),
  'action_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actionConfigId,
    const UuidValueConverter().toJson,
  ),
  'action_type': instance.actionType,
  'graph_hash_post': instance.graphHashPost,
  'object_instance_graph_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphId,
    const UuidValueConverter().toJson,
  ),
  'root_object_id': _$JsonConverterToJson<String, UuidValue>(
    instance.rootObjectId,
    const UuidValueConverter().toJson,
  ),
  'operation': instance.$type,
};

LaneActionFeedbackReceiptNotification
_$LaneActionFeedbackReceiptNotificationFromJson(Map<String, dynamic> json) =>
    LaneActionFeedbackReceiptNotification(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
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
      threadId: _$JsonConverterFromJson<String, UuidValue>(
        json['thread_id'],
        const UuidValueConverter().fromJson,
      ),
      branchId: const UuidValueConverter().fromJson(
        json['branch_id'] as String,
      ),
      projectionHash: json['projection_hash'] as String,
      actionExecutionId: const UuidValueConverter().fromJson(
        json['action_execution_id'] as String,
      ),
      eventId: const UuidValueConverter().fromJson(json['event_id'] as String),
      sequence: (json['sequence'] as num).toInt(),
      createdAtUnixMs: (json['created_at_unix_ms'] as num).toInt(),
      stage: json['stage'] as String,
      status: json['status'] as String,
      actionBindingId: _$JsonConverterFromJson<String, UuidValue>(
        json['action_binding_id'],
        const UuidValueConverter().fromJson,
      ),
      actionConfigId: _$JsonConverterFromJson<String, UuidValue>(
        json['action_config_id'],
        const UuidValueConverter().fromJson,
      ),
      actionType: json['action_type'] as String?,
      message: json['message'] as String?,
      actorIdentityId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_identity_id'],
        const UuidValueConverter().fromJson,
      ),
      actorProcessThreadId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_process_thread_id'],
        const UuidValueConverter().fromJson,
      ),
      executionRequestId: _$JsonConverterFromJson<String, UuidValue>(
        json['execution_request_id'],
        const UuidValueConverter().fromJson,
      ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$LaneActionFeedbackReceiptNotificationToJson(
  LaneActionFeedbackReceiptNotification instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
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
  'thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': const UuidValueConverter().toJson(instance.branchId),
  'projection_hash': instance.projectionHash,
  'action_execution_id': const UuidValueConverter().toJson(
    instance.actionExecutionId,
  ),
  'event_id': const UuidValueConverter().toJson(instance.eventId),
  'sequence': instance.sequence,
  'created_at_unix_ms': instance.createdAtUnixMs,
  'stage': instance.stage,
  'status': instance.status,
  'action_binding_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actionBindingId,
    const UuidValueConverter().toJson,
  ),
  'action_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actionConfigId,
    const UuidValueConverter().toJson,
  ),
  'action_type': instance.actionType,
  'message': instance.message,
  'actor_identity_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorIdentityId,
    const UuidValueConverter().toJson,
  ),
  'actor_process_thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorProcessThreadId,
    const UuidValueConverter().toJson,
  ),
  'execution_request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.executionRequestId,
    const UuidValueConverter().toJson,
  ),
  'operation': instance.$type,
};

LaneActionTerminalReceiptNotification
_$LaneActionTerminalReceiptNotificationFromJson(Map<String, dynamic> json) =>
    LaneActionTerminalReceiptNotification(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
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
      threadId: _$JsonConverterFromJson<String, UuidValue>(
        json['thread_id'],
        const UuidValueConverter().fromJson,
      ),
      branchId: const UuidValueConverter().fromJson(
        json['branch_id'] as String,
      ),
      projectionHash: json['projection_hash'] as String,
      actionExecutionId: const UuidValueConverter().fromJson(
        json['action_execution_id'] as String,
      ),
      eventId: const UuidValueConverter().fromJson(json['event_id'] as String),
      terminalStatus: json['terminal_status'] as String,
      handled: json['handled'] as bool,
      createdAtUnixMs: (json['created_at_unix_ms'] as num).toInt(),
      actionBindingId: _$JsonConverterFromJson<String, UuidValue>(
        json['action_binding_id'],
        const UuidValueConverter().fromJson,
      ),
      actionConfigId: _$JsonConverterFromJson<String, UuidValue>(
        json['action_config_id'],
        const UuidValueConverter().fromJson,
      ),
      actionType: json['action_type'] as String?,
      info: json['info'] as String?,
      error: json['error'] as String?,
      actorIdentityId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_identity_id'],
        const UuidValueConverter().fromJson,
      ),
      actorProcessThreadId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_process_thread_id'],
        const UuidValueConverter().fromJson,
      ),
      executionRequestId: _$JsonConverterFromJson<String, UuidValue>(
        json['execution_request_id'],
        const UuidValueConverter().fromJson,
      ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$LaneActionTerminalReceiptNotificationToJson(
  LaneActionTerminalReceiptNotification instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
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
  'thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': const UuidValueConverter().toJson(instance.branchId),
  'projection_hash': instance.projectionHash,
  'action_execution_id': const UuidValueConverter().toJson(
    instance.actionExecutionId,
  ),
  'event_id': const UuidValueConverter().toJson(instance.eventId),
  'terminal_status': instance.terminalStatus,
  'handled': instance.handled,
  'created_at_unix_ms': instance.createdAtUnixMs,
  'action_binding_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actionBindingId,
    const UuidValueConverter().toJson,
  ),
  'action_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actionConfigId,
    const UuidValueConverter().toJson,
  ),
  'action_type': instance.actionType,
  'info': instance.info,
  'error': instance.error,
  'actor_identity_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorIdentityId,
    const UuidValueConverter().toJson,
  ),
  'actor_process_thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorProcessThreadId,
    const UuidValueConverter().toJson,
  ),
  'execution_request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.executionRequestId,
    const UuidValueConverter().toJson,
  ),
  'operation': instance.$type,
};

LaneTurnStreamReceiptNotification _$LaneTurnStreamReceiptNotificationFromJson(
  Map<String, dynamic> json,
) => LaneTurnStreamReceiptNotification(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
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
  threadId: _$JsonConverterFromJson<String, UuidValue>(
    json['thread_id'],
    const UuidValueConverter().fromJson,
  ),
  branchId: const UuidValueConverter().fromJson(json['branch_id'] as String),
  projectionHash: json['projection_hash'] as String,
  service: json['service'] as String,
  inferenceRequestId: const UuidValueConverter().fromJson(
    json['inference_request_id'] as String,
  ),
  createdAtUnixMs: (json['created_at_unix_ms'] as num).toInt(),
  streamKind: json['stream_kind'] as String,
  sequence: (json['sequence'] as num?)?.toInt(),
  agentIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['agent_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  agentProcessThreadId: _$JsonConverterFromJson<String, UuidValue>(
    json['agent_process_thread_id'],
    const UuidValueConverter().fromJson,
  ),
  textDelta: json['text_delta'] as String?,
  message: json['message'] as String?,
  payload: json['payload'],
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$LaneTurnStreamReceiptNotificationToJson(
  LaneTurnStreamReceiptNotification instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
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
  'thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': const UuidValueConverter().toJson(instance.branchId),
  'projection_hash': instance.projectionHash,
  'service': instance.service,
  'inference_request_id': const UuidValueConverter().toJson(
    instance.inferenceRequestId,
  ),
  'created_at_unix_ms': instance.createdAtUnixMs,
  'stream_kind': instance.streamKind,
  'sequence': instance.sequence,
  'agent_identity_id': _$JsonConverterToJson<String, UuidValue>(
    instance.agentIdentityId,
    const UuidValueConverter().toJson,
  ),
  'agent_process_thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.agentProcessThreadId,
    const UuidValueConverter().toJson,
  ),
  'text_delta': instance.textDelta,
  'message': instance.message,
  'payload': instance.payload,
  'operation': instance.$type,
};

_ResolveRuntimeFunctionTargetQuery _$ResolveRuntimeFunctionTargetQueryFromJson(
  Map<String, dynamic> json,
) => _ResolveRuntimeFunctionTargetQuery(
  queryKey: json['query_key'] as String?,
  functionRef: json['function_ref'] as String,
  callTarget: InvokeFunctionCallTargetExtension.fromJson(
    json['call_target'] as String,
  ),
  projectionHashHint: json['projection_hash_hint'] as String?,
);

Map<String, dynamic> _$ResolveRuntimeFunctionTargetQueryToJson(
  _ResolveRuntimeFunctionTargetQuery instance,
) => <String, dynamic>{
  'query_key': instance.queryKey,
  'function_ref': instance.functionRef,
  'call_target': InvokeFunctionCallTargetExtension.toJson(instance.callTarget),
  'projection_hash_hint': instance.projectionHashHint,
};

_ResolveRuntimeClassRefQuery _$ResolveRuntimeClassRefQueryFromJson(
  Map<String, dynamic> json,
) => _ResolveRuntimeClassRefQuery(
  queryKey: json['query_key'] as String?,
  classRef: json['class_ref'] as String,
);

Map<String, dynamic> _$ResolveRuntimeClassRefQueryToJson(
  _ResolveRuntimeClassRefQuery instance,
) => <String, dynamic>{
  'query_key': instance.queryKey,
  'class_ref': instance.classRef,
};

_AdmitEnvironmentActorRequest _$AdmitEnvironmentActorRequestFromJson(
  Map<String, dynamic> json,
) => _AdmitEnvironmentActorRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  operation: json['operation'] as String,
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
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
);

Map<String, dynamic> _$AdmitEnvironmentActorRequestToJson(
  _AdmitEnvironmentActorRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'operation': instance.operation,
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
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
};

_CapabilityArgument _$CapabilityArgumentFromJson(Map<String, dynamic> json) =>
    _CapabilityArgument(
      id: const UuidValueConverter().fromJson(json['id'] as String),
      name: json['name'] as String,
      direction: json['direction'] as String?,
      type: json['type'] as String?,
      required_: json['required'] as bool,
      default_: json['default'],
      enum_: json['enum'] as List<dynamic>?,
      description: json['description'] as String?,
    );

Map<String, dynamic> _$CapabilityArgumentToJson(_CapabilityArgument instance) =>
    <String, dynamic>{
      'id': const UuidValueConverter().toJson(instance.id),
      'name': instance.name,
      'direction': instance.direction,
      'type': instance.type,
      'required': instance.required_,
      'default': instance.default_,
      'enum': instance.enum_,
      'description': instance.description,
    };

_CapabilityFunction _$CapabilityFunctionFromJson(
  Map<String, dynamic> json,
) => _CapabilityFunction(
  id: const UuidValueConverter().fromJson(json['id'] as String),
  name: json['name'] as String,
  summary: json['summary'] as String?,
  roleId: _$JsonConverterFromJson<String, UuidValue>(
    json['role_id'],
    const UuidValueConverter().fromJson,
  ),
  isConstructor: json['is_constructor'] as bool,
  inputs:
      (json['inputs'] as List<dynamic>?)
          ?.map((e) => CapabilityArgument.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  outputs:
      (json['outputs'] as List<dynamic>?)
          ?.map((e) => CapabilityArgument.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  arguments:
      (json['arguments'] as List<dynamic>?)
          ?.map((e) => CapabilityArgument.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
);

Map<String, dynamic> _$CapabilityFunctionToJson(_CapabilityFunction instance) =>
    <String, dynamic>{
      'id': const UuidValueConverter().toJson(instance.id),
      'name': instance.name,
      'summary': instance.summary,
      'role_id': _$JsonConverterToJson<String, UuidValue>(
        instance.roleId,
        const UuidValueConverter().toJson,
      ),
      'is_constructor': instance.isConstructor,
      'inputs': instance.inputs.map((e) => e.toJson()).toList(),
      'outputs': instance.outputs.map((e) => e.toJson()).toList(),
      'arguments': instance.arguments.map((e) => e.toJson()).toList(),
    };

_CapabilityRole _$CapabilityRoleFromJson(Map<String, dynamic> json) =>
    _CapabilityRole(
      id: const UuidValueConverter().fromJson(json['id'] as String),
      name: json['name'] as String,
      description: json['description'] as String?,
      metadata: json['metadata'] as Map<String, dynamic>,
      functions:
          (json['functions'] as List<dynamic>?)
              ?.map(
                (e) => CapabilityFunction.fromJson(e as Map<String, dynamic>),
              )
              .toList() ??
          const [],
    );

Map<String, dynamic> _$CapabilityRoleToJson(_CapabilityRole instance) =>
    <String, dynamic>{
      'id': const UuidValueConverter().toJson(instance.id),
      'name': instance.name,
      'description': instance.description,
      'metadata': instance.metadata,
      'functions': instance.functions.map((e) => e.toJson()).toList(),
    };

_CapabilityObject _$CapabilityObjectFromJson(Map<String, dynamic> json) =>
    _CapabilityObject(
      id: const UuidValueConverter().fromJson(json['id'] as String),
      name: json['name'] as String,
      description: json['description'] as String?,
      functions:
          (json['functions'] as List<dynamic>?)
              ?.map(
                (e) => CapabilityFunction.fromJson(e as Map<String, dynamic>),
              )
              .toList() ??
          const [],
    );

Map<String, dynamic> _$CapabilityObjectToJson(_CapabilityObject instance) =>
    <String, dynamic>{
      'id': const UuidValueConverter().toJson(instance.id),
      'name': instance.name,
      'description': instance.description,
      'functions': instance.functions.map((e) => e.toJson()).toList(),
    };

_ResolvedRuntimeFunctionTarget _$ResolvedRuntimeFunctionTargetFromJson(
  Map<String, dynamic> json,
) => _ResolvedRuntimeFunctionTarget(
  queryKey: json['query_key'] as String?,
  status: json['status'] as String,
  error: json['error'] as String?,
  functionRef: json['function_ref'] as String,
  callTarget: InvokeFunctionCallTargetExtension.fromJson(
    json['call_target'] as String,
  ),
  classConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['class_config_id'],
    const UuidValueConverter().fromJson,
  ),
  className: json['class_name'] as String?,
  classFqn: json['class_fqn'] as String?,
  classConfigFunctionConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['class_config_function_config_id'],
    const UuidValueConverter().fromJson,
  ),
  functionId: _$JsonConverterFromJson<String, UuidValue>(
    json['function_id'],
    const UuidValueConverter().fromJson,
  ),
  functionName: json['function_name'] as String?,
  projectionHash: json['projection_hash'] as String?,
  objectProjectionGraphId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_projection_graph_id'],
    const UuidValueConverter().fromJson,
  ),
  objectProjectionGraphIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_projection_graph_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  candidateProjectionHashes:
      (json['candidate_projection_hashes'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$ResolvedRuntimeFunctionTargetToJson(
  _ResolvedRuntimeFunctionTarget instance,
) => <String, dynamic>{
  'query_key': instance.queryKey,
  'status': instance.status,
  'error': instance.error,
  'function_ref': instance.functionRef,
  'call_target': InvokeFunctionCallTargetExtension.toJson(instance.callTarget),
  'class_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.classConfigId,
    const UuidValueConverter().toJson,
  ),
  'class_name': instance.className,
  'class_fqn': instance.classFqn,
  'class_config_function_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.classConfigFunctionConfigId,
    const UuidValueConverter().toJson,
  ),
  'function_id': _$JsonConverterToJson<String, UuidValue>(
    instance.functionId,
    const UuidValueConverter().toJson,
  ),
  'function_name': instance.functionName,
  'projection_hash': instance.projectionHash,
  'object_projection_graph_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectProjectionGraphId,
    const UuidValueConverter().toJson,
  ),
  'object_projection_graph_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.objectProjectionGraphIdentityId,
        const UuidValueConverter().toJson,
      ),
  'candidate_projection_hashes': instance.candidateProjectionHashes,
  'evidence': instance.evidence,
};

_ResolvedRuntimeClassRef _$ResolvedRuntimeClassRefFromJson(
  Map<String, dynamic> json,
) => _ResolvedRuntimeClassRef(
  queryKey: json['query_key'] as String?,
  status: json['status'] as String,
  error: json['error'] as String?,
  classRef: json['class_ref'] as String,
  classConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['class_config_id'],
    const UuidValueConverter().fromJson,
  ),
  className: json['class_name'] as String?,
  classFqn: json['class_fqn'] as String?,
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$ResolvedRuntimeClassRefToJson(
  _ResolvedRuntimeClassRef instance,
) => <String, dynamic>{
  'query_key': instance.queryKey,
  'status': instance.status,
  'error': instance.error,
  'class_ref': instance.classRef,
  'class_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.classConfigId,
    const UuidValueConverter().toJson,
  ),
  'class_name': instance.className,
  'class_fqn': instance.classFqn,
  'evidence': instance.evidence,
};

_EnvironmentOntologyMembership _$EnvironmentOntologyMembershipFromJson(
  Map<String, dynamic> json,
) => _EnvironmentOntologyMembership(
  environmentOntologyId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_ontology_id'],
    const UuidValueConverter().fromJson,
  ),
  ontologyId: const UuidValueConverter().fromJson(
    json['ontology_id'] as String,
  ),
  role: json['role'] as String,
  status: json['status'] as String,
  title: json['title'] as String?,
  description: json['description'] as String?,
  commitId: _$JsonConverterFromJson<String, UuidValue>(
    json['commit_id'],
    const UuidValueConverter().fromJson,
  ),
  graphHashPost: json['graph_hash_post'] as String?,
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$EnvironmentOntologyMembershipToJson(
  _EnvironmentOntologyMembership instance,
) => <String, dynamic>{
  'environment_ontology_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentOntologyId,
    const UuidValueConverter().toJson,
  ),
  'ontology_id': const UuidValueConverter().toJson(instance.ontologyId),
  'role': instance.role,
  'status': instance.status,
  'title': instance.title,
  'description': instance.description,
  'commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.commitId,
    const UuidValueConverter().toJson,
  ),
  'graph_hash_post': instance.graphHashPost,
  'evidence': instance.evidence,
};

_EnvironmentProfileProjectionSpec _$EnvironmentProfileProjectionSpecFromJson(
  Map<String, dynamic> json,
) => _EnvironmentProfileProjectionSpec(
  objectProjectionGraphRef: json['object_projection_graph_ref'] as String,
  viewKey: json['view_key'] as String?,
  narrative: json['narrative'] as String?,
  intent: json['intent'] as String?,
  position: (json['position'] as num?)?.toInt(),
  isDefault: json['is_default'] as bool,
);

Map<String, dynamic> _$EnvironmentProfileProjectionSpecToJson(
  _EnvironmentProfileProjectionSpec instance,
) => <String, dynamic>{
  'object_projection_graph_ref': instance.objectProjectionGraphRef,
  'view_key': instance.viewKey,
  'narrative': instance.narrative,
  'intent': instance.intent,
  'position': instance.position,
  'is_default': instance.isDefault,
};

_EnvironmentProfileLayoutSectionSpec
_$EnvironmentProfileLayoutSectionSpecFromJson(Map<String, dynamic> json) =>
    _EnvironmentProfileLayoutSectionSpec(
      sectionKey: json['section_key'] as String,
      layoutConfigSectionConfigId: _$JsonConverterFromJson<String, UuidValue>(
        json['layout_config_section_config_id'],
        const UuidValueConverter().fromJson,
      ),
      objectProjectionGraphRef: json['object_projection_graph_ref'] as String?,
      viewKey: json['view_key'] as String?,
      key: json['key'] as String?,
      position: (json['position'] as num?)?.toInt(),
      isDefault: json['is_default'] as bool,
      narrative: json['narrative'] as String?,
      intent: json['intent'] as String?,
    );

Map<String, dynamic> _$EnvironmentProfileLayoutSectionSpecToJson(
  _EnvironmentProfileLayoutSectionSpec instance,
) => <String, dynamic>{
  'section_key': instance.sectionKey,
  'layout_config_section_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutConfigSectionConfigId,
    const UuidValueConverter().toJson,
  ),
  'object_projection_graph_ref': instance.objectProjectionGraphRef,
  'view_key': instance.viewKey,
  'key': instance.key,
  'position': instance.position,
  'is_default': instance.isDefault,
  'narrative': instance.narrative,
  'intent': instance.intent,
};

_EnvironmentProfileLayoutConfigSpec
_$EnvironmentProfileLayoutConfigSpecFromJson(Map<String, dynamic> json) =>
    _EnvironmentProfileLayoutConfigSpec(
      layoutKey: json['layout_key'] as String?,
      layoutConfigId: _$JsonConverterFromJson<String, UuidValue>(
        json['layout_config_id'],
        const UuidValueConverter().fromJson,
      ),
      key: json['key'] as String?,
      position: (json['position'] as num?)?.toInt(),
      narrative: json['narrative'] as String?,
      intent: json['intent'] as String?,
      sections:
          (json['sections'] as List<dynamic>?)
              ?.map(
                (e) => EnvironmentProfileLayoutSectionSpec.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
    );

Map<String, dynamic> _$EnvironmentProfileLayoutConfigSpecToJson(
  _EnvironmentProfileLayoutConfigSpec instance,
) => <String, dynamic>{
  'layout_key': instance.layoutKey,
  'layout_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutConfigId,
    const UuidValueConverter().toJson,
  ),
  'key': instance.key,
  'position': instance.position,
  'narrative': instance.narrative,
  'intent': instance.intent,
  'sections': instance.sections.map((e) => e.toJson()).toList(),
};

_EnvironmentProfileThreadConfigSpec
_$EnvironmentProfileThreadConfigSpecFromJson(Map<String, dynamic> json) =>
    _EnvironmentProfileThreadConfigSpec(
      key: json['key'] as String,
      title: json['title'] as String?,
      description: json['description'] as String?,
      workspaceViewKey: json['workspace_view_key'] as String?,
      position: (json['position'] as num?)?.toInt(),
      isDefault: json['is_default'] as bool,
      narrative: json['narrative'] as String?,
      intent: json['intent'] as String?,
      statePromptTemplate: json['state_prompt_template'] as String?,
      projectionRefs:
          (json['projection_refs'] as List<dynamic>?)
              ?.map(
                (e) => EnvironmentProfileProjectionSpec.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
      layoutConfigs:
          (json['layout_configs'] as List<dynamic>?)
              ?.map(
                (e) => EnvironmentProfileLayoutConfigSpec.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
    );

Map<String, dynamic> _$EnvironmentProfileThreadConfigSpecToJson(
  _EnvironmentProfileThreadConfigSpec instance,
) => <String, dynamic>{
  'key': instance.key,
  'title': instance.title,
  'description': instance.description,
  'workspace_view_key': instance.workspaceViewKey,
  'position': instance.position,
  'is_default': instance.isDefault,
  'narrative': instance.narrative,
  'intent': instance.intent,
  'state_prompt_template': instance.statePromptTemplate,
  'projection_refs': instance.projectionRefs.map((e) => e.toJson()).toList(),
  'layout_configs': instance.layoutConfigs.map((e) => e.toJson()).toList(),
};

_EnvironmentProfileProcessConfigSpec
_$EnvironmentProfileProcessConfigSpecFromJson(Map<String, dynamic> json) =>
    _EnvironmentProfileProcessConfigSpec(
      key: json['key'] as String,
      type: json['type'] as String,
      title: json['title'] as String?,
      description: json['description'] as String?,
      shape: json['shape'] as String?,
      position: (json['position'] as num?)?.toInt(),
      isDefault: json['is_default'] as bool,
      narrative: json['narrative'] as String?,
      intent: json['intent'] as String?,
      threadConfigs:
          (json['thread_configs'] as List<dynamic>?)
              ?.map(
                (e) => EnvironmentProfileThreadConfigSpec.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
    );

Map<String, dynamic> _$EnvironmentProfileProcessConfigSpecToJson(
  _EnvironmentProfileProcessConfigSpec instance,
) => <String, dynamic>{
  'key': instance.key,
  'type': instance.type,
  'title': instance.title,
  'description': instance.description,
  'shape': instance.shape,
  'position': instance.position,
  'is_default': instance.isDefault,
  'narrative': instance.narrative,
  'intent': instance.intent,
  'thread_configs': instance.threadConfigs.map((e) => e.toJson()).toList(),
};

_EnvironmentProfileTopologyLayoutSeedSpec
_$EnvironmentProfileTopologyLayoutSeedSpecFromJson(Map<String, dynamic> json) =>
    _EnvironmentProfileTopologyLayoutSeedSpec(
      layoutKey: json['layout_key'] as String,
      key: json['key'] as String?,
      position: (json['position'] as num?)?.toInt(),
      activateOnSeed: json['activate_on_seed'] as bool,
      narrative: json['narrative'] as String?,
      intent: json['intent'] as String?,
    );

Map<String, dynamic> _$EnvironmentProfileTopologyLayoutSeedSpecToJson(
  _EnvironmentProfileTopologyLayoutSeedSpec instance,
) => <String, dynamic>{
  'layout_key': instance.layoutKey,
  'key': instance.key,
  'position': instance.position,
  'activate_on_seed': instance.activateOnSeed,
  'narrative': instance.narrative,
  'intent': instance.intent,
};

_EnvironmentProfileTopologyThreadSeedSpec
_$EnvironmentProfileTopologyThreadSeedSpecFromJson(Map<String, dynamic> json) =>
    _EnvironmentProfileTopologyThreadSeedSpec(
      threadConfigKey: json['thread_config_key'] as String,
      threadKey: json['thread_key'] as String,
      key: json['key'] as String?,
      title: json['title'] as String?,
      description: json['description'] as String?,
      position: (json['position'] as num?)?.toInt(),
      isMain: json['is_main'] as bool,
      narrative: json['narrative'] as String?,
      intent: json['intent'] as String?,
      layoutSeeds:
          (json['layout_seeds'] as List<dynamic>?)
              ?.map(
                (e) => EnvironmentProfileTopologyLayoutSeedSpec.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
    );

Map<String, dynamic> _$EnvironmentProfileTopologyThreadSeedSpecToJson(
  _EnvironmentProfileTopologyThreadSeedSpec instance,
) => <String, dynamic>{
  'thread_config_key': instance.threadConfigKey,
  'thread_key': instance.threadKey,
  'key': instance.key,
  'title': instance.title,
  'description': instance.description,
  'position': instance.position,
  'is_main': instance.isMain,
  'narrative': instance.narrative,
  'intent': instance.intent,
  'layout_seeds': instance.layoutSeeds.map((e) => e.toJson()).toList(),
};

_EnvironmentProfileTopologyProcessSeedSpec
_$EnvironmentProfileTopologyProcessSeedSpecFromJson(
  Map<String, dynamic> json,
) => _EnvironmentProfileTopologyProcessSeedSpec(
  processConfigKey: json['process_config_key'] as String,
  processKey: json['process_key'] as String,
  key: json['key'] as String?,
  title: json['title'] as String?,
  description: json['description'] as String?,
  position: (json['position'] as num?)?.toInt(),
  narrative: json['narrative'] as String?,
  intent: json['intent'] as String?,
  threadSeeds:
      (json['thread_seeds'] as List<dynamic>?)
          ?.map(
            (e) => EnvironmentProfileTopologyThreadSeedSpec.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$EnvironmentProfileTopologyProcessSeedSpecToJson(
  _EnvironmentProfileTopologyProcessSeedSpec instance,
) => <String, dynamic>{
  'process_config_key': instance.processConfigKey,
  'process_key': instance.processKey,
  'key': instance.key,
  'title': instance.title,
  'description': instance.description,
  'position': instance.position,
  'narrative': instance.narrative,
  'intent': instance.intent,
  'thread_seeds': instance.threadSeeds.map((e) => e.toJson()).toList(),
};

_EnvironmentProfileTopologySeedSpec
_$EnvironmentProfileTopologySeedSpecFromJson(Map<String, dynamic> json) =>
    _EnvironmentProfileTopologySeedSpec(
      key: json['key'] as String,
      title: json['title'] as String?,
      description: json['description'] as String?,
      narrative: json['narrative'] as String?,
      processSeeds:
          (json['process_seeds'] as List<dynamic>?)
              ?.map(
                (e) => EnvironmentProfileTopologyProcessSeedSpec.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
    );

Map<String, dynamic> _$EnvironmentProfileTopologySeedSpecToJson(
  _EnvironmentProfileTopologySeedSpec instance,
) => <String, dynamic>{
  'key': instance.key,
  'title': instance.title,
  'description': instance.description,
  'narrative': instance.narrative,
  'process_seeds': instance.processSeeds.map((e) => e.toJson()).toList(),
};

_EnvironmentProfileRuntimeMountReceipt
_$EnvironmentProfileRuntimeMountReceiptFromJson(
  Map<String, dynamic> json,
) => _EnvironmentProfileRuntimeMountReceipt(
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
  environmentProfileId: const UuidValueConverter().fromJson(
    json['environment_profile_id'] as String,
  ),
  topologySeedKey: json['topology_seed_key'] as String,
  processConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['process_config_id'],
    const UuidValueConverter().fromJson,
  ),
  processKey: json['process_key'] as String,
  processId: const UuidValueConverter().fromJson(json['process_id'] as String),
  threadConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['thread_config_id'],
    const UuidValueConverter().fromJson,
  ),
  threadKey: json['thread_key'] as String,
  threadId: const UuidValueConverter().fromJson(json['thread_id'] as String),
  threadLayoutConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['thread_layout_config_id'],
    const UuidValueConverter().fromJson,
  ),
  layoutKey: json['layout_key'] as String?,
  layoutConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['layout_config_id'],
    const UuidValueConverter().fromJson,
  ),
  layoutId: _$JsonConverterFromJson<String, UuidValue>(
    json['layout_id'],
    const UuidValueConverter().fromJson,
  ),
  threadLayoutId: _$JsonConverterFromJson<String, UuidValue>(
    json['thread_layout_id'],
    const UuidValueConverter().fromJson,
  ),
  activateOnSeed: json['activate_on_seed'] as bool,
  status: json['status'] as String,
);

Map<String, dynamic> _$EnvironmentProfileRuntimeMountReceiptToJson(
  _EnvironmentProfileRuntimeMountReceipt instance,
) => <String, dynamic>{
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
  'environment_profile_id': const UuidValueConverter().toJson(
    instance.environmentProfileId,
  ),
  'topology_seed_key': instance.topologySeedKey,
  'process_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.processConfigId,
    const UuidValueConverter().toJson,
  ),
  'process_key': instance.processKey,
  'process_id': const UuidValueConverter().toJson(instance.processId),
  'thread_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadConfigId,
    const UuidValueConverter().toJson,
  ),
  'thread_key': instance.threadKey,
  'thread_id': const UuidValueConverter().toJson(instance.threadId),
  'thread_layout_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadLayoutConfigId,
    const UuidValueConverter().toJson,
  ),
  'layout_key': instance.layoutKey,
  'layout_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutConfigId,
    const UuidValueConverter().toJson,
  ),
  'layout_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutId,
    const UuidValueConverter().toJson,
  ),
  'thread_layout_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadLayoutId,
    const UuidValueConverter().toJson,
  ),
  'activate_on_seed': instance.activateOnSeed,
  'status': instance.status,
};

_EnvironmentProfileInstallSpec _$EnvironmentProfileInstallSpecFromJson(
  Map<String, dynamic> json,
) => _EnvironmentProfileInstallSpec(
  key: json['key'] as String?,
  title: json['title'] as String?,
  description: json['description'] as String?,
  narrative: json['narrative'] as String?,
  processConfigs:
      (json['process_configs'] as List<dynamic>?)
          ?.map(
            (e) => EnvironmentProfileProcessConfigSpec.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$EnvironmentProfileInstallSpecToJson(
  _EnvironmentProfileInstallSpec instance,
) => <String, dynamic>{
  'key': instance.key,
  'title': instance.title,
  'description': instance.description,
  'narrative': instance.narrative,
  'process_configs': instance.processConfigs.map((e) => e.toJson()).toList(),
};

_UpsertEnvironmentProfileRequest _$UpsertEnvironmentProfileRequestFromJson(
  Map<String, dynamic> json,
) => _UpsertEnvironmentProfileRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  operation: json['operation'] as String,
  environmentConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_config_id'],
    const UuidValueConverter().fromJson,
  ),
  profile: EnvironmentProfileInstallSpec.fromJson(
    json['profile'] as Map<String, dynamic>,
  ),
  topologySeeds:
      (json['topology_seeds'] as List<dynamic>?)
          ?.map(
            (e) => EnvironmentProfileTopologySeedSpec.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  validateOnly: json['validate_only'] as bool,
);

Map<String, dynamic> _$UpsertEnvironmentProfileRequestToJson(
  _UpsertEnvironmentProfileRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'operation': instance.operation,
  'environment_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentConfigId,
    const UuidValueConverter().toJson,
  ),
  'profile': instance.profile.toJson(),
  'topology_seeds': instance.topologySeeds.map((e) => e.toJson()).toList(),
  'validate_only': instance.validateOnly,
};

_UpsertEnvironmentProfileResponse _$UpsertEnvironmentProfileResponseFromJson(
  Map<String, dynamic> json,
) => _UpsertEnvironmentProfileResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  operation: json['operation'] as String,
  status: json['status'] as String,
  error: json['error'] as String?,
  environmentConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_config_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentProfileConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_profile_config_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentProfileId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_profile_id'],
    const UuidValueConverter().fromJson,
  ),
  processConfigIds: json['process_config_ids'] == null
      ? const []
      : const UuidValueListConverter().fromJson(
          json['process_config_ids'] as List,
        ),
  threadConfigIds: json['thread_config_ids'] == null
      ? const []
      : const UuidValueListConverter().fromJson(
          json['thread_config_ids'] as List,
        ),
  threadProjectionAssociationIds:
      json['thread_projection_association_ids'] == null
      ? const []
      : const UuidValueListConverter().fromJson(
          json['thread_projection_association_ids'] as List,
        ),
  threadLayoutConfigIds: json['thread_layout_config_ids'] == null
      ? const []
      : const UuidValueListConverter().fromJson(
          json['thread_layout_config_ids'] as List,
        ),
  topologySeedIds: json['topology_seed_ids'] == null
      ? const []
      : const UuidValueListConverter().fromJson(
          json['topology_seed_ids'] as List,
        ),
  topologyProcessSeedIds: json['topology_process_seed_ids'] == null
      ? const []
      : const UuidValueListConverter().fromJson(
          json['topology_process_seed_ids'] as List,
        ),
  topologyThreadSeedIds: json['topology_thread_seed_ids'] == null
      ? const []
      : const UuidValueListConverter().fromJson(
          json['topology_thread_seed_ids'] as List,
        ),
  topologyThreadLayoutSeedIds: json['topology_thread_layout_seed_ids'] == null
      ? const []
      : const UuidValueListConverter().fromJson(
          json['topology_thread_layout_seed_ids'] as List,
        ),
);

Map<String, dynamic> _$UpsertEnvironmentProfileResponseToJson(
  _UpsertEnvironmentProfileResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'operation': instance.operation,
  'status': instance.status,
  'error': instance.error,
  'environment_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentConfigId,
    const UuidValueConverter().toJson,
  ),
  'environment_profile_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentProfileConfigId,
    const UuidValueConverter().toJson,
  ),
  'environment_profile_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentProfileId,
    const UuidValueConverter().toJson,
  ),
  'process_config_ids': const UuidValueListConverter().toJson(
    instance.processConfigIds,
  ),
  'thread_config_ids': const UuidValueListConverter().toJson(
    instance.threadConfigIds,
  ),
  'thread_projection_association_ids': const UuidValueListConverter().toJson(
    instance.threadProjectionAssociationIds,
  ),
  'thread_layout_config_ids': const UuidValueListConverter().toJson(
    instance.threadLayoutConfigIds,
  ),
  'topology_seed_ids': const UuidValueListConverter().toJson(
    instance.topologySeedIds,
  ),
  'topology_process_seed_ids': const UuidValueListConverter().toJson(
    instance.topologyProcessSeedIds,
  ),
  'topology_thread_seed_ids': const UuidValueListConverter().toJson(
    instance.topologyThreadSeedIds,
  ),
  'topology_thread_layout_seed_ids': const UuidValueListConverter().toJson(
    instance.topologyThreadLayoutSeedIds,
  ),
};

_ProvisionEnvironmentProfileRequest
_$ProvisionEnvironmentProfileRequestFromJson(Map<String, dynamic> json) =>
    _ProvisionEnvironmentProfileRequest(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentId: const UuidValueConverter().fromJson(
        json['environment_id'] as String,
      ),
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
      operation: json['operation'] as String,
      environmentProfileId: _$JsonConverterFromJson<String, UuidValue>(
        json['environment_profile_id'],
        const UuidValueConverter().fromJson,
      ),
      topologySeedKey: json['topology_seed_key'] as String,
      validateOnly: json['validate_only'] as bool,
    );

Map<String, dynamic> _$ProvisionEnvironmentProfileRequestToJson(
  _ProvisionEnvironmentProfileRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'operation': instance.operation,
  'environment_profile_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentProfileId,
    const UuidValueConverter().toJson,
  ),
  'topology_seed_key': instance.topologySeedKey,
  'validate_only': instance.validateOnly,
};

_ProvisionEnvironmentProfileResponse
_$ProvisionEnvironmentProfileResponseFromJson(Map<String, dynamic> json) =>
    _ProvisionEnvironmentProfileResponse(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentId: const UuidValueConverter().fromJson(
        json['environment_id'] as String,
      ),
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
      operation: json['operation'] as String,
      status: json['status'] as String,
      error: json['error'] as String?,
      environmentProfileId: _$JsonConverterFromJson<String, UuidValue>(
        json['environment_profile_id'],
        const UuidValueConverter().fromJson,
      ),
      processIds: json['process_ids'] == null
          ? const []
          : const UuidValueListConverter().fromJson(
              json['process_ids'] as List,
            ),
      threadIds: json['thread_ids'] == null
          ? const []
          : const UuidValueListConverter().fromJson(json['thread_ids'] as List),
      threadLayoutIds: json['thread_layout_ids'] == null
          ? const []
          : const UuidValueListConverter().fromJson(
              json['thread_layout_ids'] as List,
            ),
      runtimeMounts:
          (json['runtime_mounts'] as List<dynamic>?)
              ?.map(
                (e) => EnvironmentProfileRuntimeMountReceipt.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
    );

Map<String, dynamic> _$ProvisionEnvironmentProfileResponseToJson(
  _ProvisionEnvironmentProfileResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'operation': instance.operation,
  'status': instance.status,
  'error': instance.error,
  'environment_profile_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentProfileId,
    const UuidValueConverter().toJson,
  ),
  'process_ids': const UuidValueListConverter().toJson(instance.processIds),
  'thread_ids': const UuidValueListConverter().toJson(instance.threadIds),
  'thread_layout_ids': const UuidValueListConverter().toJson(
    instance.threadLayoutIds,
  ),
  'runtime_mounts': instance.runtimeMounts.map((e) => e.toJson()).toList(),
};

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

_AdmitEnvironmentActorResponse _$AdmitEnvironmentActorResponseFromJson(
  Map<String, dynamic> json,
) => _AdmitEnvironmentActorResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  operation: json['operation'] as String,
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  accepted: json['accepted'] as bool,
  status: json['status'] as String,
  error: json['error'] as String?,
  receipt: EnvironmentActorAdmissionReceipt.fromJson(
    json['receipt'] as Map<String, dynamic>,
  ),
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$AdmitEnvironmentActorResponseToJson(
  _AdmitEnvironmentActorResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'operation': instance.operation,
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'accepted': instance.accepted,
  'status': instance.status,
  'error': instance.error,
  'receipt': instance.receipt.toJson(),
  'evidence': instance.evidence,
};

_StartEnvironmentSessionRequest _$StartEnvironmentSessionRequestFromJson(
  Map<String, dynamic> json,
) => _StartEnvironmentSessionRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  operation: json['operation'] as String,
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentProfileId: const UuidValueConverter().fromJson(
    json['environment_profile_id'] as String,
  ),
  environmentSessionConfigId: const UuidValueConverter().fromJson(
    json['environment_session_config_id'] as String,
  ),
  admissionReceipt: EnvironmentActorAdmissionReceipt.fromJson(
    json['admission_receipt'] as Map<String, dynamic>,
  ),
  sessionKey: json['session_key'] as String,
  title: json['title'] as String?,
  description: json['description'] as String?,
  purpose: json['purpose'] as String?,
  sourceKind: json['source_kind'] as String?,
  sourceRef: json['source_ref'] as String?,
  resolveDefaultNavigationContext:
      json['resolve_default_navigation_context'] as bool,
  metadata: json['metadata'] as Map<String, dynamic>,
);

Map<String, dynamic> _$StartEnvironmentSessionRequestToJson(
  _StartEnvironmentSessionRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'operation': instance.operation,
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'environment_profile_id': const UuidValueConverter().toJson(
    instance.environmentProfileId,
  ),
  'environment_session_config_id': const UuidValueConverter().toJson(
    instance.environmentSessionConfigId,
  ),
  'admission_receipt': instance.admissionReceipt.toJson(),
  'session_key': instance.sessionKey,
  'title': instance.title,
  'description': instance.description,
  'purpose': instance.purpose,
  'source_kind': instance.sourceKind,
  'source_ref': instance.sourceRef,
  'resolve_default_navigation_context':
      instance.resolveDefaultNavigationContext,
  'metadata': instance.metadata,
};

_JoinEnvironmentSessionRequest _$JoinEnvironmentSessionRequestFromJson(
  Map<String, dynamic> json,
) => _JoinEnvironmentSessionRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  operation: json['operation'] as String,
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentProfileId: const UuidValueConverter().fromJson(
    json['environment_profile_id'] as String,
  ),
  environmentSessionId: const UuidValueConverter().fromJson(
    json['environment_session_id'] as String,
  ),
  admissionReceipt: EnvironmentActorAdmissionReceipt.fromJson(
    json['admission_receipt'] as Map<String, dynamic>,
  ),
  reason: json['reason'] as String?,
  resolveDefaultNavigationContext:
      json['resolve_default_navigation_context'] as bool,
  metadata: json['metadata'] as Map<String, dynamic>,
);

Map<String, dynamic> _$JoinEnvironmentSessionRequestToJson(
  _JoinEnvironmentSessionRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'operation': instance.operation,
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'environment_profile_id': const UuidValueConverter().toJson(
    instance.environmentProfileId,
  ),
  'environment_session_id': const UuidValueConverter().toJson(
    instance.environmentSessionId,
  ),
  'admission_receipt': instance.admissionReceipt.toJson(),
  'reason': instance.reason,
  'resolve_default_navigation_context':
      instance.resolveDefaultNavigationContext,
  'metadata': instance.metadata,
};

_DescribeEnvironmentSessionRequest _$DescribeEnvironmentSessionRequestFromJson(
  Map<String, dynamic> json,
) => _DescribeEnvironmentSessionRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  operation: json['operation'] as String,
  environmentSessionId: const UuidValueConverter().fromJson(
    json['environment_session_id'] as String,
  ),
);

Map<String, dynamic> _$DescribeEnvironmentSessionRequestToJson(
  _DescribeEnvironmentSessionRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'operation': instance.operation,
  'environment_session_id': const UuidValueConverter().toJson(
    instance.environmentSessionId,
  ),
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

_StartEnvironmentSessionResponse _$StartEnvironmentSessionResponseFromJson(
  Map<String, dynamic> json,
) => _StartEnvironmentSessionResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  operation: json['operation'] as String,
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  accepted: json['accepted'] as bool,
  status: json['status'] as String,
  error: json['error'] as String?,
  session: json['session'] == null
      ? null
      : EnvironmentSessionView.fromJson(
          json['session'] as Map<String, dynamic>,
        ),
  joinReceipt: EnvironmentSessionJoinReceipt.fromJson(
    json['join_receipt'] as Map<String, dynamic>,
  ),
  defaultNavigationContext: json['default_navigation_context'] == null
      ? null
      : EnvironmentNavigationContextView.fromJson(
          json['default_navigation_context'] as Map<String, dynamic>,
        ),
  defaultNavigationReceipt: json['default_navigation_receipt'] == null
      ? null
      : EnvironmentNavigationCommitReceipt.fromJson(
          json['default_navigation_receipt'] as Map<String, dynamic>,
        ),
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$StartEnvironmentSessionResponseToJson(
  _StartEnvironmentSessionResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'operation': instance.operation,
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'accepted': instance.accepted,
  'status': instance.status,
  'error': instance.error,
  'session': instance.session?.toJson(),
  'join_receipt': instance.joinReceipt.toJson(),
  'default_navigation_context': instance.defaultNavigationContext?.toJson(),
  'default_navigation_receipt': instance.defaultNavigationReceipt?.toJson(),
  'evidence': instance.evidence,
};

_JoinEnvironmentSessionResponse _$JoinEnvironmentSessionResponseFromJson(
  Map<String, dynamic> json,
) => _JoinEnvironmentSessionResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
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
  operation: json['operation'] as String,
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  accepted: json['accepted'] as bool,
  status: json['status'] as String,
  error: json['error'] as String?,
  session: json['session'] == null
      ? null
      : EnvironmentSessionView.fromJson(
          json['session'] as Map<String, dynamic>,
        ),
  receipt: EnvironmentSessionJoinReceipt.fromJson(
    json['receipt'] as Map<String, dynamic>,
  ),
  defaultNavigationContext: json['default_navigation_context'] == null
      ? null
      : EnvironmentNavigationContextView.fromJson(
          json['default_navigation_context'] as Map<String, dynamic>,
        ),
  defaultNavigationReceipt: json['default_navigation_receipt'] == null
      ? null
      : EnvironmentNavigationCommitReceipt.fromJson(
          json['default_navigation_receipt'] as Map<String, dynamic>,
        ),
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$JoinEnvironmentSessionResponseToJson(
  _JoinEnvironmentSessionResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'operation': instance.operation,
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'accepted': instance.accepted,
  'status': instance.status,
  'error': instance.error,
  'session': instance.session?.toJson(),
  'receipt': instance.receipt.toJson(),
  'default_navigation_context': instance.defaultNavigationContext?.toJson(),
  'default_navigation_receipt': instance.defaultNavigationReceipt?.toJson(),
  'evidence': instance.evidence,
};

_DescribeEnvironmentSessionResponse
_$DescribeEnvironmentSessionResponseFromJson(Map<String, dynamic> json) =>
    _DescribeEnvironmentSessionResponse(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      environmentId: const UuidValueConverter().fromJson(
        json['environment_id'] as String,
      ),
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
      operation: json['operation'] as String,
      status: json['status'] as String,
      error: json['error'] as String?,
      session: json['session'] == null
          ? null
          : EnvironmentSessionView.fromJson(
              json['session'] as Map<String, dynamic>,
            ),
      evidence: json['evidence'] as Map<String, dynamic>,
    );

Map<String, dynamic> _$DescribeEnvironmentSessionResponseToJson(
  _DescribeEnvironmentSessionResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
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
  'operation': instance.operation,
  'status': instance.status,
  'error': instance.error,
  'session': instance.session?.toJson(),
  'evidence': instance.evidence,
};

_EnvironmentSessionAttentionResolution
_$EnvironmentSessionAttentionResolutionFromJson(
  Map<String, dynamic> json,
) => _EnvironmentSessionAttentionResolution(
  environmentSessionId: const UuidValueConverter().fromJson(
    json['environment_session_id'] as String,
  ),
  environmentNavigationContextId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_navigation_context_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentSessionThreadId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_session_thread_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentSessionAttentionSessionId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['environment_session_attention_session_id'],
        const UuidValueConverter().fromJson,
      ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
  environmentProfileId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_profile_id'],
    const UuidValueConverter().fromJson,
  ),
  threadId: _$JsonConverterFromJson<String, UuidValue>(
    json['thread_id'],
    const UuidValueConverter().fromJson,
  ),
  threadLayoutId: _$JsonConverterFromJson<String, UuidValue>(
    json['thread_layout_id'],
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
  attentionSession: json['attention_session'] == null
      ? null
      : AttentionSessionPin.fromJson(
          json['attention_session'] as Map<String, dynamic>,
        ),
  activeTransition: json['active_transition'] == null
      ? null
      : AttentionFocusTransitionPin.fromJson(
          json['active_transition'] as Map<String, dynamic>,
        ),
  validation: json['validation'] == null
      ? null
      : AttentionTransitionValidationResult.fromJson(
          json['validation'] as Map<String, dynamic>,
        ),
  transitions:
      (json['transitions'] as List<dynamic>?)
          ?.map(
            (e) =>
                AttentionFocusTransitionPin.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  status: json['status'] as String,
  blockers:
      (json['blockers'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$EnvironmentSessionAttentionResolutionToJson(
  _EnvironmentSessionAttentionResolution instance,
) => <String, dynamic>{
  'environment_session_id': const UuidValueConverter().toJson(
    instance.environmentSessionId,
  ),
  'environment_navigation_context_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentNavigationContextId,
    const UuidValueConverter().toJson,
  ),
  'environment_session_thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentSessionThreadId,
    const UuidValueConverter().toJson,
  ),
  'environment_session_attention_session_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.environmentSessionAttentionSessionId,
        const UuidValueConverter().toJson,
      ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
  'environment_profile_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentProfileId,
    const UuidValueConverter().toJson,
  ),
  'thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadId,
    const UuidValueConverter().toJson,
  ),
  'thread_layout_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadLayoutId,
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
  'attention_session': instance.attentionSession?.toJson(),
  'active_transition': instance.activeTransition?.toJson(),
  'validation': instance.validation?.toJson(),
  'transitions': instance.transitions.map((e) => e.toJson()).toList(),
  'status': instance.status,
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

_DescribeEnvironmentOPGConstructor _$DescribeEnvironmentOPGConstructorFromJson(
  Map<String, dynamic> json,
) => _DescribeEnvironmentOPGConstructor(
  functionId: const UuidValueConverter().fromJson(
    json['function_id'] as String,
  ),
  rootClassConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['root_class_config_id'],
    const UuidValueConverter().fromJson,
  ),
);

Map<String, dynamic> _$DescribeEnvironmentOPGConstructorToJson(
  _DescribeEnvironmentOPGConstructor instance,
) => <String, dynamic>{
  'function_id': const UuidValueConverter().toJson(instance.functionId),
  'root_class_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.rootClassConfigId,
    const UuidValueConverter().toJson,
  ),
};

_DescribeEnvironmentOPG _$DescribeEnvironmentOPGFromJson(
  Map<String, dynamic> json,
) => _DescribeEnvironmentOPG(
  id: const UuidValueConverter().fromJson(json['id'] as String),
  projectionHash: json['projection_hash'] as String,
  name: json['name'] as String?,
  description: json['description'] as String?,
  supportsVirtualBuild: json['supports_virtual_build'] as bool,
  constructors:
      (json['constructors'] as List<dynamic>?)
          ?.map(
            (e) => DescribeEnvironmentOPGConstructor.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$DescribeEnvironmentOPGToJson(
  _DescribeEnvironmentOPG instance,
) => <String, dynamic>{
  'id': const UuidValueConverter().toJson(instance.id),
  'projection_hash': instance.projectionHash,
  'name': instance.name,
  'description': instance.description,
  'supports_virtual_build': instance.supportsVirtualBuild,
  'constructors': instance.constructors.map((e) => e.toJson()).toList(),
};

_DescribeEnvironmentTopologyLane _$DescribeEnvironmentTopologyLaneFromJson(
  Map<String, dynamic> json,
) => _DescribeEnvironmentTopologyLane(
  laneHash: json['lane_hash'] as String,
  opgId: _$JsonConverterFromJson<String, UuidValue>(
    json['opg_id'],
    const UuidValueConverter().fromJson,
  ),
  opgName: json['opg_name'] as String?,
);

Map<String, dynamic> _$DescribeEnvironmentTopologyLaneToJson(
  _DescribeEnvironmentTopologyLane instance,
) => <String, dynamic>{
  'lane_hash': instance.laneHash,
  'opg_id': _$JsonConverterToJson<String, UuidValue>(
    instance.opgId,
    const UuidValueConverter().toJson,
  ),
  'opg_name': instance.opgName,
};

_DescribeEnvironmentTopologyAttachment
_$DescribeEnvironmentTopologyAttachmentFromJson(Map<String, dynamic> json) =>
    _DescribeEnvironmentTopologyAttachment(
      assocId: const UuidValueConverter().fromJson(json['assoc_id'] as String),
      title: json['title'] as String?,
      isActive: json['is_active'] as bool,
      objectInstanceGraphBranchId: const UuidValueConverter().fromJson(
        json['object_instance_graph_branch_id'] as String,
      ),
      objectInstanceGraphIdentityId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_instance_graph_identity_id'],
        const UuidValueConverter().fromJson,
      ),
      domainBranchId: _$JsonConverterFromJson<String, UuidValue>(
        json['domain_branch_id'],
        const UuidValueConverter().fromJson,
      ),
      lanes:
          (json['lanes'] as List<dynamic>?)
              ?.map(
                (e) => DescribeEnvironmentTopologyLane.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
    );

Map<String, dynamic> _$DescribeEnvironmentTopologyAttachmentToJson(
  _DescribeEnvironmentTopologyAttachment instance,
) => <String, dynamic>{
  'assoc_id': const UuidValueConverter().toJson(instance.assocId),
  'title': instance.title,
  'is_active': instance.isActive,
  'object_instance_graph_branch_id': const UuidValueConverter().toJson(
    instance.objectInstanceGraphBranchId,
  ),
  'object_instance_graph_identity_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphIdentityId,
    const UuidValueConverter().toJson,
  ),
  'domain_branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.domainBranchId,
    const UuidValueConverter().toJson,
  ),
  'lanes': instance.lanes.map((e) => e.toJson()).toList(),
};

_DescribeEnvironmentTopologySection
_$DescribeEnvironmentTopologySectionFromJson(Map<String, dynamic> json) =>
    _DescribeEnvironmentTopologySection(
      sectionKey: json['section_key'] as String,
      title: json['title'] as String,
      description: json['description'] as String?,
      order: (json['order'] as num).toInt(),
      flex: (json['flex'] as num).toDouble(),
      isVisible: json['is_visible'] as bool,
      focusScopeId: _$JsonConverterFromJson<String, UuidValue>(
        json['focus_scope_id'],
        const UuidValueConverter().fromJson,
      ),
      viewRef: json['view_ref'] as String?,
      viewKey: json['view_key'] as String?,
      packageName: json['package_name'] as String?,
      paneKey: json['pane_key'] as String?,
    );

Map<String, dynamic> _$DescribeEnvironmentTopologySectionToJson(
  _DescribeEnvironmentTopologySection instance,
) => <String, dynamic>{
  'section_key': instance.sectionKey,
  'title': instance.title,
  'description': instance.description,
  'order': instance.order,
  'flex': instance.flex,
  'is_visible': instance.isVisible,
  'focus_scope_id': _$JsonConverterToJson<String, UuidValue>(
    instance.focusScopeId,
    const UuidValueConverter().toJson,
  ),
  'view_ref': instance.viewRef,
  'view_key': instance.viewKey,
  'package_name': instance.packageName,
  'pane_key': instance.paneKey,
};

_DescribeEnvironmentTopologyLayout _$DescribeEnvironmentTopologyLayoutFromJson(
  Map<String, dynamic> json,
) => _DescribeEnvironmentTopologyLayout(
  layoutId: _$JsonConverterFromJson<String, UuidValue>(
    json['layout_id'],
    const UuidValueConverter().fromJson,
  ),
  layoutKey: json['layout_key'] as String?,
  title: json['title'] as String,
  description: json['description'] as String?,
  isActive: json['is_active'] as bool,
  sections:
      (json['sections'] as List<dynamic>?)
          ?.map(
            (e) => DescribeEnvironmentTopologySection.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$DescribeEnvironmentTopologyLayoutToJson(
  _DescribeEnvironmentTopologyLayout instance,
) => <String, dynamic>{
  'layout_id': _$JsonConverterToJson<String, UuidValue>(
    instance.layoutId,
    const UuidValueConverter().toJson,
  ),
  'layout_key': instance.layoutKey,
  'title': instance.title,
  'description': instance.description,
  'is_active': instance.isActive,
  'sections': instance.sections.map((e) => e.toJson()).toList(),
};

_DescribeEnvironmentTopologyThread _$DescribeEnvironmentTopologyThreadFromJson(
  Map<String, dynamic> json,
) => _DescribeEnvironmentTopologyThread(
  threadId: const UuidValueConverter().fromJson(json['thread_id'] as String),
  threadKey: json['thread_key'] as String?,
  title: json['title'] as String?,
  description: json['description'] as String?,
  activeLayoutId: _$JsonConverterFromJson<String, UuidValue>(
    json['active_layout_id'],
    const UuidValueConverter().fromJson,
  ),
  activeLayoutKey: json['active_layout_key'] as String?,
  layouts:
      (json['layouts'] as List<dynamic>?)
          ?.map(
            (e) => DescribeEnvironmentTopologyLayout.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  attachments:
      (json['attachments'] as List<dynamic>?)
          ?.map(
            (e) => DescribeEnvironmentTopologyAttachment.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$DescribeEnvironmentTopologyThreadToJson(
  _DescribeEnvironmentTopologyThread instance,
) => <String, dynamic>{
  'thread_id': const UuidValueConverter().toJson(instance.threadId),
  'thread_key': instance.threadKey,
  'title': instance.title,
  'description': instance.description,
  'active_layout_id': _$JsonConverterToJson<String, UuidValue>(
    instance.activeLayoutId,
    const UuidValueConverter().toJson,
  ),
  'active_layout_key': instance.activeLayoutKey,
  'layouts': instance.layouts.map((e) => e.toJson()).toList(),
  'attachments': instance.attachments.map((e) => e.toJson()).toList(),
};

_DescribeEnvironmentTopologyProcess
_$DescribeEnvironmentTopologyProcessFromJson(
  Map<String, dynamic> json,
) => _DescribeEnvironmentTopologyProcess(
  processId: const UuidValueConverter().fromJson(json['process_id'] as String),
  processKey: json['process_key'] as String?,
  title: json['title'] as String,
  description: json['description'] as String?,
  threads:
      (json['threads'] as List<dynamic>?)
          ?.map(
            (e) => DescribeEnvironmentTopologyThread.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$DescribeEnvironmentTopologyProcessToJson(
  _DescribeEnvironmentTopologyProcess instance,
) => <String, dynamic>{
  'process_id': const UuidValueConverter().toJson(instance.processId),
  'process_key': instance.processKey,
  'title': instance.title,
  'description': instance.description,
  'threads': instance.threads.map((e) => e.toJson()).toList(),
};

_EnvironmentStatusAuthority _$EnvironmentStatusAuthorityFromJson(
  Map<String, dynamic> json,
) => _EnvironmentStatusAuthority(
  kind: EnvironmentStatusAuthorityKindExtension.fromJson(
    json['kind'] as String,
  ),
  sourceArtifact: json['source_artifact'] as String?,
);

Map<String, dynamic> _$EnvironmentStatusAuthorityToJson(
  _EnvironmentStatusAuthority instance,
) => <String, dynamic>{
  'kind': EnvironmentStatusAuthorityKindExtension.toJson(instance.kind),
  'source_artifact': instance.sourceArtifact,
};

_EnvironmentStatusBlock _$EnvironmentStatusBlockFromJson(
  Map<String, dynamic> json,
) => _EnvironmentStatusBlock(
  name: json['name'] as String,
  authority: EnvironmentStatusAuthority.fromJson(
    json['authority'] as Map<String, dynamic>,
  ),
  payload: json['payload'] as Map<String, dynamic>,
  available: json['available'] as bool,
  unavailableReason: json['unavailable_reason'] as String?,
);

Map<String, dynamic> _$EnvironmentStatusBlockToJson(
  _EnvironmentStatusBlock instance,
) => <String, dynamic>{
  'name': instance.name,
  'authority': instance.authority.toJson(),
  'payload': instance.payload,
  'available': instance.available,
  'unavailable_reason': instance.unavailableReason,
};

_EnvironmentReadinessPersistenceReceipt
_$EnvironmentReadinessPersistenceReceiptFromJson(Map<String, dynamic> json) =>
    _EnvironmentReadinessPersistenceReceipt(
      status: json['status'] as String,
      backend: json['backend'] as String,
      databaseUrlRef: json['database_url_ref'] as String?,
      environmentConfigId: _$JsonConverterFromJson<String, UuidValue>(
        json['environment_config_id'],
        const UuidValueConverter().fromJson,
      ),
      ocgId: _$JsonConverterFromJson<String, UuidValue>(
        json['ocg_id'],
        const UuidValueConverter().fromJson,
      ),
      ocgHash: json['ocg_hash'] as String?,
      dbSchemaHash: json['db_schema_hash'] as String?,
      dbSchemaRegistryHash: json['db_schema_registry_hash'] as String?,
      markerOcgHash: json['marker_ocg_hash'] as String?,
      markerHeadCommitId: _$JsonConverterFromJson<String, UuidValue>(
        json['marker_head_commit_id'],
        const UuidValueConverter().fromJson,
      ),
      installed: json['installed'] as bool,
      migrated: json['migrated'] as bool,
      sqlRootCount: (json['sql_root_count'] as num).toInt(),
      stepCount: (json['step_count'] as num).toInt(),
    );

Map<String, dynamic> _$EnvironmentReadinessPersistenceReceiptToJson(
  _EnvironmentReadinessPersistenceReceipt instance,
) => <String, dynamic>{
  'status': instance.status,
  'backend': instance.backend,
  'database_url_ref': instance.databaseUrlRef,
  'environment_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentConfigId,
    const UuidValueConverter().toJson,
  ),
  'ocg_id': _$JsonConverterToJson<String, UuidValue>(
    instance.ocgId,
    const UuidValueConverter().toJson,
  ),
  'ocg_hash': instance.ocgHash,
  'db_schema_hash': instance.dbSchemaHash,
  'db_schema_registry_hash': instance.dbSchemaRegistryHash,
  'marker_ocg_hash': instance.markerOcgHash,
  'marker_head_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.markerHeadCommitId,
    const UuidValueConverter().toJson,
  ),
  'installed': instance.installed,
  'migrated': instance.migrated,
  'sql_root_count': instance.sqlRootCount,
  'step_count': instance.stepCount,
};

_EnvironmentReadinessGraphReceipt _$EnvironmentReadinessGraphReceiptFromJson(
  Map<String, dynamic> json,
) => _EnvironmentReadinessGraphReceipt(
  status: json['status'] as String,
  laneHeadStatus: json['lane_head_status'] as String?,
  genesisStatus: json['genesis_status'] as String?,
  branchId: const UuidValueConverter().fromJson(json['branch_id'] as String),
  projectionHash: json['projection_hash'] as String?,
  objectProjectionGraphId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_projection_graph_id'],
    const UuidValueConverter().fromJson,
  ),
  constructorFunctionId: _$JsonConverterFromJson<String, UuidValue>(
    json['constructor_function_id'],
    const UuidValueConverter().fromJson,
  ),
  laneHeadCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['lane_head_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  domainCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['domain_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_id'],
    const UuidValueConverter().fromJson,
  ),
  rootObjectId: _$JsonConverterFromJson<String, UuidValue>(
    json['root_object_id'],
    const UuidValueConverter().fromJson,
  ),
  graphHashPost: json['graph_hash_post'] as String?,
  functionCallId: _$JsonConverterFromJson<String, UuidValue>(
    json['function_call_id'],
    const UuidValueConverter().fromJson,
  ),
  functionCallResponseId: _$JsonConverterFromJson<String, UuidValue>(
    json['function_call_response_id'],
    const UuidValueConverter().fromJson,
  ),
);

Map<String, dynamic> _$EnvironmentReadinessGraphReceiptToJson(
  _EnvironmentReadinessGraphReceipt instance,
) => <String, dynamic>{
  'status': instance.status,
  'lane_head_status': instance.laneHeadStatus,
  'genesis_status': instance.genesisStatus,
  'branch_id': const UuidValueConverter().toJson(instance.branchId),
  'projection_hash': instance.projectionHash,
  'object_projection_graph_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectProjectionGraphId,
    const UuidValueConverter().toJson,
  ),
  'constructor_function_id': _$JsonConverterToJson<String, UuidValue>(
    instance.constructorFunctionId,
    const UuidValueConverter().toJson,
  ),
  'lane_head_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.laneHeadCommitId,
    const UuidValueConverter().toJson,
  ),
  'domain_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.domainCommitId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphCommitId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphId,
    const UuidValueConverter().toJson,
  ),
  'root_object_id': _$JsonConverterToJson<String, UuidValue>(
    instance.rootObjectId,
    const UuidValueConverter().toJson,
  ),
  'graph_hash_post': instance.graphHashPost,
  'function_call_id': _$JsonConverterToJson<String, UuidValue>(
    instance.functionCallId,
    const UuidValueConverter().toJson,
  ),
  'function_call_response_id': _$JsonConverterToJson<String, UuidValue>(
    instance.functionCallResponseId,
    const UuidValueConverter().toJson,
  ),
};

_EnvironmentReadinessRouteReceipt _$EnvironmentReadinessRouteReceiptFromJson(
  Map<String, dynamic> json,
) => _EnvironmentReadinessRouteReceipt(
  apiPackageName: json['api_package_name'] as String?,
  providerServicePackageName: json['provider_service_package_name'] as String?,
  routeKind: json['route_kind'] as String?,
  hostId: json['host_id'] as String?,
  hostVersion: json['host_version'] as String?,
  protocolVersion: json['protocol_version'] as String?,
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

Map<String, dynamic> _$EnvironmentReadinessRouteReceiptToJson(
  _EnvironmentReadinessRouteReceipt instance,
) => <String, dynamic>{
  'api_package_name': instance.apiPackageName,
  'provider_service_package_name': instance.providerServicePackageName,
  'route_kind': instance.routeKind,
  'host_id': instance.hostId,
  'host_version': instance.hostVersion,
  'protocol_version': instance.protocolVersion,
  'endpoint_refs': instance.endpointRefs,
  'stream_endpoint_refs': instance.streamEndpointRefs,
};

_EnvironmentReadinessReceipt _$EnvironmentReadinessReceiptFromJson(
  Map<String, dynamic> json,
) => _EnvironmentReadinessReceipt(
  status: json['status'] as String,
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
  environmentTitle: json['environment_title'] as String?,
  environmentManifestPath: json['environment_manifest_path'] as String?,
  environmentPackageRef:
      json['environment_package_ref'] as Map<String, dynamic>?,
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
  ocgId: _$JsonConverterFromJson<String, UuidValue>(
    json['ocg_id'],
    const UuidValueConverter().fromJson,
  ),
  opgHashes:
      (json['opg_hashes'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  graph: json['graph'] == null
      ? null
      : EnvironmentReadinessGraphReceipt.fromJson(
          json['graph'] as Map<String, dynamic>,
        ),
  persistence: json['persistence'] == null
      ? null
      : EnvironmentReadinessPersistenceReceipt.fromJson(
          json['persistence'] as Map<String, dynamic>,
        ),
  metaRoute: json['meta_route'] == null
      ? null
      : EnvironmentReadinessRouteReceipt.fromJson(
          json['meta_route'] as Map<String, dynamic>,
        ),
);

Map<String, dynamic> _$EnvironmentReadinessReceiptToJson(
  _EnvironmentReadinessReceipt instance,
) => <String, dynamic>{
  'status': instance.status,
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
  'environment_title': instance.environmentTitle,
  'environment_manifest_path': instance.environmentManifestPath,
  'environment_package_ref': instance.environmentPackageRef,
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
  'ocg_id': _$JsonConverterToJson<String, UuidValue>(
    instance.ocgId,
    const UuidValueConverter().toJson,
  ),
  'opg_hashes': instance.opgHashes,
  'graph': instance.graph?.toJson(),
  'persistence': instance.persistence?.toJson(),
  'meta_route': instance.metaRoute?.toJson(),
};
