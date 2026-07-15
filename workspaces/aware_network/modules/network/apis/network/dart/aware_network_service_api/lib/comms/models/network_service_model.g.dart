// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'network_service_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_NetworkNodeRouteDescriptor _$NetworkNodeRouteDescriptorFromJson(
  Map<String, dynamic> json,
) => _NetworkNodeRouteDescriptor(
  nodeId: const UuidValueConverter().fromJson(json['node_id'] as String),
  publicKey: json['public_key'] as String?,
  hostname: json['hostname'] as String,
  port: (json['port'] as num).toInt(),
  baseUrl: json['base_url'] as String?,
  status: json['status'] as String,
  lastSeenAt: json['last_seen_at'] as String?,
);

Map<String, dynamic> _$NetworkNodeRouteDescriptorToJson(
  _NetworkNodeRouteDescriptor instance,
) => <String, dynamic>{
  'node_id': const UuidValueConverter().toJson(instance.nodeId),
  'public_key': instance.publicKey,
  'hostname': instance.hostname,
  'port': instance.port,
  'base_url': instance.baseUrl,
  'status': instance.status,
  'last_seen_at': instance.lastSeenAt,
};

_NetworkPeerFanoutRuleDescriptor _$NetworkPeerFanoutRuleDescriptorFromJson(
  Map<String, dynamic> json,
) => _NetworkPeerFanoutRuleDescriptor(
  id: _$JsonConverterFromJson<String, UuidValue>(
    json['id'],
    const UuidValueConverter().fromJson,
  ),
  laneBranchId: const UuidValueConverter().fromJson(
    json['lane_branch_id'] as String,
  ),
  laneProjectionHash: json['lane_projection_hash'] as String,
  enabled: json['enabled'] as bool,
  mode: json['mode'] as String,
);

Map<String, dynamic> _$NetworkPeerFanoutRuleDescriptorToJson(
  _NetworkPeerFanoutRuleDescriptor instance,
) => <String, dynamic>{
  'id': _$JsonConverterToJson<String, UuidValue>(
    instance.id,
    const UuidValueConverter().toJson,
  ),
  'lane_branch_id': const UuidValueConverter().toJson(instance.laneBranchId),
  'lane_projection_hash': instance.laneProjectionHash,
  'enabled': instance.enabled,
  'mode': instance.mode,
};

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);

_NetworkPeerDescriptor _$NetworkPeerDescriptorFromJson(
  Map<String, dynamic> json,
) => _NetworkPeerDescriptor(
  edgeId: _$JsonConverterFromJson<String, UuidValue>(
    json['edge_id'],
    const UuidValueConverter().fromJson,
  ),
  sourceNodeId: const UuidValueConverter().fromJson(
    json['source_node_id'] as String,
  ),
  targetNodeId: const UuidValueConverter().fromJson(
    json['target_node_id'] as String,
  ),
  peerNodeId: const UuidValueConverter().fromJson(
    json['peer_node_id'] as String,
  ),
  peerBaseUrl: json['peer_base_url'] as String,
  direction: json['direction'] as String,
  status: json['status'] as String,
  trustScore: (json['trust_score'] as num).toDouble(),
  fanoutRules:
      (json['fanout_rules'] as List<dynamic>?)
          ?.map(
            (e) => NetworkPeerFanoutRuleDescriptor.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  connectedAt: json['connected_at'] as String?,
  lastPingAt: json['last_ping_at'] as String?,
);

Map<String, dynamic> _$NetworkPeerDescriptorToJson(
  _NetworkPeerDescriptor instance,
) => <String, dynamic>{
  'edge_id': _$JsonConverterToJson<String, UuidValue>(
    instance.edgeId,
    const UuidValueConverter().toJson,
  ),
  'source_node_id': const UuidValueConverter().toJson(instance.sourceNodeId),
  'target_node_id': const UuidValueConverter().toJson(instance.targetNodeId),
  'peer_node_id': const UuidValueConverter().toJson(instance.peerNodeId),
  'peer_base_url': instance.peerBaseUrl,
  'direction': instance.direction,
  'status': instance.status,
  'trust_score': instance.trustScore,
  'fanout_rules': instance.fanoutRules.map((e) => e.toJson()).toList(),
  'connected_at': instance.connectedAt,
  'last_ping_at': instance.lastPingAt,
};

_NetworkHostedServiceDescriptor _$NetworkHostedServiceDescriptorFromJson(
  Map<String, dynamic> json,
) => _NetworkHostedServiceDescriptor(
  servicePackageId: _$JsonConverterFromJson<String, UuidValue>(
    json['service_package_id'],
    const UuidValueConverter().fromJson,
  ),
  serviceId: const UuidValueConverter().fromJson(json['service_id'] as String),
  serviceName: json['service_name'] as String,
  servicePackageNames:
      (json['service_package_names'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
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
  hostId: json['host_id'] as String,
  hostVersion: json['host_version'] as String?,
  protocolVersion: json['protocol_version'] as String,
  supportsStreamEvents: json['supports_stream_events'] as bool,
);

Map<String, dynamic> _$NetworkHostedServiceDescriptorToJson(
  _NetworkHostedServiceDescriptor instance,
) => <String, dynamic>{
  'service_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.servicePackageId,
    const UuidValueConverter().toJson,
  ),
  'service_id': const UuidValueConverter().toJson(instance.serviceId),
  'service_name': instance.serviceName,
  'service_package_names': instance.servicePackageNames,
  'endpoint_refs': instance.endpointRefs,
  'stream_endpoint_refs': instance.streamEndpointRefs,
  'host_id': instance.hostId,
  'host_version': instance.hostVersion,
  'protocol_version': instance.protocolVersion,
  'supports_stream_events': instance.supportsStreamEvents,
};

_NetworkEnvironmentDescriptor _$NetworkEnvironmentDescriptorFromJson(
  Map<String, dynamic> json,
) => _NetworkEnvironmentDescriptor(
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
  environmentKey: json['environment_key'] as String?,
  environmentTitle: json['environment_title'] as String?,
  role: json['role'] as String,
  isActive: json['is_active'] as bool,
  priority: (json['priority'] as num).toInt(),
  status: json['status'] as String,
  experienceNames:
      (json['experience_names'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  environmentConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_config_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentConfigKey: json['environment_config_key'] as String?,
);

Map<String, dynamic> _$NetworkEnvironmentDescriptorToJson(
  _NetworkEnvironmentDescriptor instance,
) => <String, dynamic>{
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
  'environment_key': instance.environmentKey,
  'environment_title': instance.environmentTitle,
  'role': instance.role,
  'is_active': instance.isActive,
  'priority': instance.priority,
  'status': instance.status,
  'experience_names': instance.experienceNames,
  'environment_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentConfigId,
    const UuidValueConverter().toJson,
  ),
  'environment_config_key': instance.environmentConfigKey,
};

_NetworkResolvedHostedServiceRoute _$NetworkResolvedHostedServiceRouteFromJson(
  Map<String, dynamic> json,
) => _NetworkResolvedHostedServiceRoute(
  providerNodeId: const UuidValueConverter().fromJson(
    json['provider_node_id'] as String,
  ),
  providerNodeBaseUrl: json['provider_node_base_url'] as String,
  routeConnectionId: _$JsonConverterFromJson<String, UuidValue>(
    json['route_connection_id'],
    const UuidValueConverter().fromJson,
  ),
  hostedService: NetworkHostedServiceDescriptor.fromJson(
    json['hosted_service'] as Map<String, dynamic>,
  ),
);

Map<String, dynamic> _$NetworkResolvedHostedServiceRouteToJson(
  _NetworkResolvedHostedServiceRoute instance,
) => <String, dynamic>{
  'provider_node_id': const UuidValueConverter().toJson(
    instance.providerNodeId,
  ),
  'provider_node_base_url': instance.providerNodeBaseUrl,
  'route_connection_id': _$JsonConverterToJson<String, UuidValue>(
    instance.routeConnectionId,
    const UuidValueConverter().toJson,
  ),
  'hosted_service': instance.hostedService.toJson(),
};

_NetworkTerritoryNodeDescriptor _$NetworkTerritoryNodeDescriptorFromJson(
  Map<String, dynamic> json,
) => _NetworkTerritoryNodeDescriptor(
  node: NetworkNodeRouteDescriptor.fromJson(
    json['node'] as Map<String, dynamic>,
  ),
  environments:
      (json['environments'] as List<dynamic>?)
          ?.map(
            (e) => NetworkEnvironmentDescriptor.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  hostedServices:
      (json['hosted_services'] as List<dynamic>?)
          ?.map(
            (e) => NetworkHostedServiceDescriptor.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  peers:
      (json['peers'] as List<dynamic>?)
          ?.map(
            (e) => NetworkPeerDescriptor.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$NetworkTerritoryNodeDescriptorToJson(
  _NetworkTerritoryNodeDescriptor instance,
) => <String, dynamic>{
  'node': instance.node.toJson(),
  'environments': instance.environments.map((e) => e.toJson()).toList(),
  'hosted_services': instance.hostedServices.map((e) => e.toJson()).toList(),
  'peers': instance.peers.map((e) => e.toJson()).toList(),
};

_NetworkExperienceServiceCandidate _$NetworkExperienceServiceCandidateFromJson(
  Map<String, dynamic> json,
) => _NetworkExperienceServiceCandidate(
  hostedService: NetworkHostedServiceDescriptor.fromJson(
    json['hosted_service'] as Map<String, dynamic>,
  ),
  providerNodeId: const UuidValueConverter().fromJson(
    json['provider_node_id'] as String,
  ),
  providerNodeBaseUrl: json['provider_node_base_url'] as String?,
  routeConnectionId: _$JsonConverterFromJson<String, UuidValue>(
    json['route_connection_id'],
    const UuidValueConverter().fromJson,
  ),
  routeStatus: json['route_status'] as String,
  matchedServicePackageNames:
      (json['matched_service_package_names'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  matchedEndpointRefs:
      (json['matched_endpoint_refs'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  missingServicePackageNames:
      (json['missing_service_package_names'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  missingEndpointRefs:
      (json['missing_endpoint_refs'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
);

Map<String, dynamic> _$NetworkExperienceServiceCandidateToJson(
  _NetworkExperienceServiceCandidate instance,
) => <String, dynamic>{
  'hosted_service': instance.hostedService.toJson(),
  'provider_node_id': const UuidValueConverter().toJson(
    instance.providerNodeId,
  ),
  'provider_node_base_url': instance.providerNodeBaseUrl,
  'route_connection_id': _$JsonConverterToJson<String, UuidValue>(
    instance.routeConnectionId,
    const UuidValueConverter().toJson,
  ),
  'route_status': instance.routeStatus,
  'matched_service_package_names': instance.matchedServicePackageNames,
  'matched_endpoint_refs': instance.matchedEndpointRefs,
  'missing_service_package_names': instance.missingServicePackageNames,
  'missing_endpoint_refs': instance.missingEndpointRefs,
};

_NetworkExperienceTerritoryEntry _$NetworkExperienceTerritoryEntryFromJson(
  Map<String, dynamic> json,
) => _NetworkExperienceTerritoryEntry(
  experienceName: json['experience_name'] as String,
  node: NetworkNodeRouteDescriptor.fromJson(
    json['node'] as Map<String, dynamic>,
  ),
  environment: NetworkEnvironmentDescriptor.fromJson(
    json['environment'] as Map<String, dynamic>,
  ),
  serviceCandidates:
      (json['service_candidates'] as List<dynamic>?)
          ?.map(
            (e) => NetworkExperienceServiceCandidate.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  routeStatus: json['route_status'] as String,
  missingServicePackageNames:
      (json['missing_service_package_names'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  missingEndpointRefs:
      (json['missing_endpoint_refs'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
);

Map<String, dynamic> _$NetworkExperienceTerritoryEntryToJson(
  _NetworkExperienceTerritoryEntry instance,
) => <String, dynamic>{
  'experience_name': instance.experienceName,
  'node': instance.node.toJson(),
  'environment': instance.environment.toJson(),
  'service_candidates': instance.serviceCandidates
      .map((e) => e.toJson())
      .toList(),
  'route_status': instance.routeStatus,
  'missing_service_package_names': instance.missingServicePackageNames,
  'missing_endpoint_refs': instance.missingEndpointRefs,
};

_NetworkNodePublicationNode _$NetworkNodePublicationNodeFromJson(
  Map<String, dynamic> json,
) => _NetworkNodePublicationNode(
  nodeId: const UuidValueConverter().fromJson(json['node_id'] as String),
  publicKey: json['public_key'] as String,
  hostname: json['hostname'] as String,
  port: (json['port'] as num).toInt(),
  baseUrl: json['base_url'] as String?,
  status: json['status'] as String,
);

Map<String, dynamic> _$NetworkNodePublicationNodeToJson(
  _NetworkNodePublicationNode instance,
) => <String, dynamic>{
  'node_id': const UuidValueConverter().toJson(instance.nodeId),
  'public_key': instance.publicKey,
  'hostname': instance.hostname,
  'port': instance.port,
  'base_url': instance.baseUrl,
  'status': instance.status,
};

_NetworkNodePublicationEnvironment _$NetworkNodePublicationEnvironmentFromJson(
  Map<String, dynamic> json,
) => _NetworkNodePublicationEnvironment(
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
  environmentKey: json['environment_key'] as String?,
  environmentTitle: json['environment_title'] as String?,
  role: json['role'] as String,
  isActive: json['is_active'] as bool,
  priority: (json['priority'] as num).toInt(),
  status: json['status'] as String,
  experienceNames:
      (json['experience_names'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  environmentConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_config_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentConfigKey: json['environment_config_key'] as String?,
);

Map<String, dynamic> _$NetworkNodePublicationEnvironmentToJson(
  _NetworkNodePublicationEnvironment instance,
) => <String, dynamic>{
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
  'environment_key': instance.environmentKey,
  'environment_title': instance.environmentTitle,
  'role': instance.role,
  'is_active': instance.isActive,
  'priority': instance.priority,
  'status': instance.status,
  'experience_names': instance.experienceNames,
  'environment_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentConfigId,
    const UuidValueConverter().toJson,
  ),
  'environment_config_key': instance.environmentConfigKey,
};

_NetworkNodePublicationHostedService
_$NetworkNodePublicationHostedServiceFromJson(Map<String, dynamic> json) =>
    _NetworkNodePublicationHostedService(
      servicePackageId: const UuidValueConverter().fromJson(
        json['service_package_id'] as String,
      ),
      serviceId: const UuidValueConverter().fromJson(
        json['service_id'] as String,
      ),
      serviceName: json['service_name'] as String,
      servicePackageNames:
          (json['service_package_names'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
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
      hostId: json['host_id'] as String,
      hostVersion: json['host_version'] as String?,
      protocolVersion: json['protocol_version'] as String,
      supportsStreamEvents: json['supports_stream_events'] as bool,
    );

Map<String, dynamic> _$NetworkNodePublicationHostedServiceToJson(
  _NetworkNodePublicationHostedService instance,
) => <String, dynamic>{
  'service_package_id': const UuidValueConverter().toJson(
    instance.servicePackageId,
  ),
  'service_id': const UuidValueConverter().toJson(instance.serviceId),
  'service_name': instance.serviceName,
  'service_package_names': instance.servicePackageNames,
  'endpoint_refs': instance.endpointRefs,
  'stream_endpoint_refs': instance.streamEndpointRefs,
  'host_id': instance.hostId,
  'host_version': instance.hostVersion,
  'protocol_version': instance.protocolVersion,
  'supports_stream_events': instance.supportsStreamEvents,
};

_NetworkNodePublicationIntent _$NetworkNodePublicationIntentFromJson(
  Map<String, dynamic> json,
) => _NetworkNodePublicationIntent(
  publicationDigest: json['publication_digest'] as String,
  node: NetworkNodePublicationNode.fromJson(
    json['node'] as Map<String, dynamic>,
  ),
  environment: NetworkNodePublicationEnvironment.fromJson(
    json['environment'] as Map<String, dynamic>,
  ),
  hostedServices:
      (json['hosted_services'] as List<dynamic>?)
          ?.map(
            (e) => NetworkNodePublicationHostedService.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  sourceWorkspaceRevisionId: _$JsonConverterFromJson<String, UuidValue>(
    json['source_workspace_revision_id'],
    const UuidValueConverter().fromJson,
  ),
  sourceNodeConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['source_node_config_id'],
    const UuidValueConverter().fromJson,
  ),
);

Map<String, dynamic> _$NetworkNodePublicationIntentToJson(
  _NetworkNodePublicationIntent instance,
) => <String, dynamic>{
  'publication_digest': instance.publicationDigest,
  'node': instance.node.toJson(),
  'environment': instance.environment.toJson(),
  'hosted_services': instance.hostedServices.map((e) => e.toJson()).toList(),
  'source_workspace_revision_id': _$JsonConverterToJson<String, UuidValue>(
    instance.sourceWorkspaceRevisionId,
    const UuidValueConverter().toJson,
  ),
  'source_node_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.sourceNodeConfigId,
    const UuidValueConverter().toJson,
  ),
};

_NetworkNodePublicationCommitReceipt
_$NetworkNodePublicationCommitReceiptFromJson(Map<String, dynamic> json) =>
    _NetworkNodePublicationCommitReceipt(
      operation: json['operation'] as String,
      domainCommitId: _$JsonConverterFromJson<String, UuidValue>(
        json['domain_commit_id'],
        const UuidValueConverter().fromJson,
      ),
      objectInstanceGraphCommitId: _$JsonConverterFromJson<String, UuidValue>(
        json['object_instance_graph_commit_id'],
        const UuidValueConverter().fromJson,
      ),
      rootObjectId: _$JsonConverterFromJson<String, UuidValue>(
        json['root_object_id'],
        const UuidValueConverter().fromJson,
      ),
    );

Map<String, dynamic> _$NetworkNodePublicationCommitReceiptToJson(
  _NetworkNodePublicationCommitReceipt instance,
) => <String, dynamic>{
  'operation': instance.operation,
  'domain_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.domainCommitId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphCommitId,
    const UuidValueConverter().toJson,
  ),
  'root_object_id': _$JsonConverterToJson<String, UuidValue>(
    instance.rootObjectId,
    const UuidValueConverter().toJson,
  ),
};

_NetworkNodePublicationCoverage _$NetworkNodePublicationCoverageFromJson(
  Map<String, dynamic> json,
) => _NetworkNodePublicationCoverage(
  nodeRegistered: json['node_registered'] as bool,
  environmentPublished: json['environment_published'] as bool,
  hostedServicePackageIds: json['hosted_service_package_ids'] == null
      ? const []
      : const UuidValueListConverter().fromJson(
          json['hosted_service_package_ids'] as List,
        ),
  missingHostedServicePackageIds:
      json['missing_hosted_service_package_ids'] == null
      ? const []
      : const UuidValueListConverter().fromJson(
          json['missing_hosted_service_package_ids'] as List,
        ),
  unexpectedHostedServicePackageIds:
      json['unexpected_hosted_service_package_ids'] == null
      ? const []
      : const UuidValueListConverter().fromJson(
          json['unexpected_hosted_service_package_ids'] as List,
        ),
);

Map<String, dynamic> _$NetworkNodePublicationCoverageToJson(
  _NetworkNodePublicationCoverage instance,
) => <String, dynamic>{
  'node_registered': instance.nodeRegistered,
  'environment_published': instance.environmentPublished,
  'hosted_service_package_ids': const UuidValueListConverter().toJson(
    instance.hostedServicePackageIds,
  ),
  'missing_hosted_service_package_ids': const UuidValueListConverter().toJson(
    instance.missingHostedServicePackageIds,
  ),
  'unexpected_hosted_service_package_ids': const UuidValueListConverter()
      .toJson(instance.unexpectedHostedServicePackageIds),
};

_NetworkReconcileNodePublicationRequest
_$NetworkReconcileNodePublicationRequestFromJson(Map<String, dynamic> json) =>
    _NetworkReconcileNodePublicationRequest(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      intent: NetworkNodePublicationIntent.fromJson(
        json['intent'] as Map<String, dynamic>,
      ),
    );

Map<String, dynamic> _$NetworkReconcileNodePublicationRequestToJson(
  _NetworkReconcileNodePublicationRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'intent': instance.intent.toJson(),
};

_NetworkReconcileNodePublicationResponse
_$NetworkReconcileNodePublicationResponseFromJson(Map<String, dynamic> json) =>
    _NetworkReconcileNodePublicationResponse(
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      success: json['success'] as bool,
      status: json['status'] as String,
      error: json['error'] as String?,
      publicationDigest: json['publication_digest'] as String?,
      node: json['node'] == null
          ? null
          : NetworkNodeRouteDescriptor.fromJson(
              json['node'] as Map<String, dynamic>,
            ),
      environment: json['environment'] == null
          ? null
          : NetworkEnvironmentDescriptor.fromJson(
              json['environment'] as Map<String, dynamic>,
            ),
      hostedServices:
          (json['hosted_services'] as List<dynamic>?)
              ?.map(
                (e) => NetworkHostedServiceDescriptor.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
      coverage: json['coverage'] == null
          ? null
          : NetworkNodePublicationCoverage.fromJson(
              json['coverage'] as Map<String, dynamic>,
            ),
      commitReceipts:
          (json['commit_receipts'] as List<dynamic>?)
              ?.map(
                (e) => NetworkNodePublicationCommitReceipt.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
    );

Map<String, dynamic> _$NetworkReconcileNodePublicationResponseToJson(
  _NetworkReconcileNodePublicationResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'status': instance.status,
  'error': instance.error,
  'publication_digest': instance.publicationDigest,
  'node': instance.node?.toJson(),
  'environment': instance.environment?.toJson(),
  'hosted_services': instance.hostedServices.map((e) => e.toJson()).toList(),
  'coverage': instance.coverage?.toJson(),
  'commit_receipts': instance.commitReceipts.map((e) => e.toJson()).toList(),
};

_NetworkRegisterNodeRequest _$NetworkRegisterNodeRequestFromJson(
  Map<String, dynamic> json,
) => _NetworkRegisterNodeRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  publicKey: json['public_key'] as String,
  hostname: json['hostname'] as String,
  port: (json['port'] as num).toInt(),
  baseUrl: json['base_url'] as String?,
  status: json['status'] as String,
);

Map<String, dynamic> _$NetworkRegisterNodeRequestToJson(
  _NetworkRegisterNodeRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'public_key': instance.publicKey,
  'hostname': instance.hostname,
  'port': instance.port,
  'base_url': instance.baseUrl,
  'status': instance.status,
};

_NetworkRegisterNodeResponse _$NetworkRegisterNodeResponseFromJson(
  Map<String, dynamic> json,
) => _NetworkRegisterNodeResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  error: json['error'] as String?,
  node: json['node'] == null
      ? null
      : NetworkNodeRouteDescriptor.fromJson(
          json['node'] as Map<String, dynamic>,
        ),
);

Map<String, dynamic> _$NetworkRegisterNodeResponseToJson(
  _NetworkRegisterNodeResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'error': instance.error,
  'node': instance.node?.toJson(),
};

_NetworkUpsertPeerRequest _$NetworkUpsertPeerRequestFromJson(
  Map<String, dynamic> json,
) => _NetworkUpsertPeerRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  sourceNodeId: const UuidValueConverter().fromJson(
    json['source_node_id'] as String,
  ),
  targetNodeId: const UuidValueConverter().fromJson(
    json['target_node_id'] as String,
  ),
  targetBaseUrl: json['target_base_url'] as String,
  status: json['status'] as String,
  trustScore: (json['trust_score'] as num).toDouble(),
);

Map<String, dynamic> _$NetworkUpsertPeerRequestToJson(
  _NetworkUpsertPeerRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'source_node_id': const UuidValueConverter().toJson(instance.sourceNodeId),
  'target_node_id': const UuidValueConverter().toJson(instance.targetNodeId),
  'target_base_url': instance.targetBaseUrl,
  'status': instance.status,
  'trust_score': instance.trustScore,
};

_NetworkUpsertPeerResponse _$NetworkUpsertPeerResponseFromJson(
  Map<String, dynamic> json,
) => _NetworkUpsertPeerResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  error: json['error'] as String?,
  peer: json['peer'] == null
      ? null
      : NetworkPeerDescriptor.fromJson(json['peer'] as Map<String, dynamic>),
);

Map<String, dynamic> _$NetworkUpsertPeerResponseToJson(
  _NetworkUpsertPeerResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'error': instance.error,
  'peer': instance.peer?.toJson(),
};

_NetworkListPeersRequest _$NetworkListPeersRequestFromJson(
  Map<String, dynamic> json,
) => _NetworkListPeersRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: const UuidValueConverter().fromJson(json['node_id'] as String),
  includeIncoming: json['include_incoming'] as bool,
  includeOutgoing: json['include_outgoing'] as bool,
  acceptedOnly: json['accepted_only'] as bool,
  limitResults: (json['limit_results'] as num?)?.toInt(),
);

Map<String, dynamic> _$NetworkListPeersRequestToJson(
  _NetworkListPeersRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'node_id': const UuidValueConverter().toJson(instance.nodeId),
  'include_incoming': instance.includeIncoming,
  'include_outgoing': instance.includeOutgoing,
  'accepted_only': instance.acceptedOnly,
  'limit_results': instance.limitResults,
};

_NetworkListPeersResponse _$NetworkListPeersResponseFromJson(
  Map<String, dynamic> json,
) => _NetworkListPeersResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  error: json['error'] as String?,
  peers:
      (json['peers'] as List<dynamic>?)
          ?.map(
            (e) => NetworkPeerDescriptor.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$NetworkListPeersResponseToJson(
  _NetworkListPeersResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'error': instance.error,
  'peers': instance.peers.map((e) => e.toJson()).toList(),
};

_NetworkPublishHostedServiceRequest
_$NetworkPublishHostedServiceRequestFromJson(Map<String, dynamic> json) =>
    _NetworkPublishHostedServiceRequest(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      nodeId: const UuidValueConverter().fromJson(json['node_id'] as String),
      servicePackageId: _$JsonConverterFromJson<String, UuidValue>(
        json['service_package_id'],
        const UuidValueConverter().fromJson,
      ),
      serviceId: const UuidValueConverter().fromJson(
        json['service_id'] as String,
      ),
      serviceName: json['service_name'] as String,
      servicePackageNames:
          (json['service_package_names'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
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
      hostId: json['host_id'] as String,
      hostVersion: json['host_version'] as String?,
      protocolVersion: json['protocol_version'] as String,
      supportsStreamEvents: json['supports_stream_events'] as bool,
    );

Map<String, dynamic> _$NetworkPublishHostedServiceRequestToJson(
  _NetworkPublishHostedServiceRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'node_id': const UuidValueConverter().toJson(instance.nodeId),
  'service_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.servicePackageId,
    const UuidValueConverter().toJson,
  ),
  'service_id': const UuidValueConverter().toJson(instance.serviceId),
  'service_name': instance.serviceName,
  'service_package_names': instance.servicePackageNames,
  'endpoint_refs': instance.endpointRefs,
  'stream_endpoint_refs': instance.streamEndpointRefs,
  'host_id': instance.hostId,
  'host_version': instance.hostVersion,
  'protocol_version': instance.protocolVersion,
  'supports_stream_events': instance.supportsStreamEvents,
};

_NetworkPublishHostedServiceResponse
_$NetworkPublishHostedServiceResponseFromJson(Map<String, dynamic> json) =>
    _NetworkPublishHostedServiceResponse(
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      success: json['success'] as bool,
      error: json['error'] as String?,
      hostedService: json['hosted_service'] == null
          ? null
          : NetworkHostedServiceDescriptor.fromJson(
              json['hosted_service'] as Map<String, dynamic>,
            ),
    );

Map<String, dynamic> _$NetworkPublishHostedServiceResponseToJson(
  _NetworkPublishHostedServiceResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'error': instance.error,
  'hosted_service': instance.hostedService?.toJson(),
};

_NetworkListHostedServicesRequest _$NetworkListHostedServicesRequestFromJson(
  Map<String, dynamic> json,
) => _NetworkListHostedServicesRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: const UuidValueConverter().fromJson(json['node_id'] as String),
);

Map<String, dynamic> _$NetworkListHostedServicesRequestToJson(
  _NetworkListHostedServicesRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'node_id': const UuidValueConverter().toJson(instance.nodeId),
};

_NetworkListHostedServicesResponse _$NetworkListHostedServicesResponseFromJson(
  Map<String, dynamic> json,
) => _NetworkListHostedServicesResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  error: json['error'] as String?,
  hostedServices:
      (json['hosted_services'] as List<dynamic>?)
          ?.map(
            (e) => NetworkHostedServiceDescriptor.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$NetworkListHostedServicesResponseToJson(
  _NetworkListHostedServicesResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'error': instance.error,
  'hosted_services': instance.hostedServices.map((e) => e.toJson()).toList(),
};

_NetworkPublishEnvironmentRequest _$NetworkPublishEnvironmentRequestFromJson(
  Map<String, dynamic> json,
) => _NetworkPublishEnvironmentRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: const UuidValueConverter().fromJson(json['node_id'] as String),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
  environmentKey: json['environment_key'] as String?,
  environmentTitle: json['environment_title'] as String?,
  role: json['role'] as String,
  isActive: json['is_active'] as bool,
  priority: (json['priority'] as num).toInt(),
  status: json['status'] as String,
  experienceNames:
      (json['experience_names'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  environmentConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_config_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentConfigKey: json['environment_config_key'] as String?,
);

Map<String, dynamic> _$NetworkPublishEnvironmentRequestToJson(
  _NetworkPublishEnvironmentRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'node_id': const UuidValueConverter().toJson(instance.nodeId),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
  'environment_key': instance.environmentKey,
  'environment_title': instance.environmentTitle,
  'role': instance.role,
  'is_active': instance.isActive,
  'priority': instance.priority,
  'status': instance.status,
  'experience_names': instance.experienceNames,
  'environment_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentConfigId,
    const UuidValueConverter().toJson,
  ),
  'environment_config_key': instance.environmentConfigKey,
};

_NetworkPublishEnvironmentResponse _$NetworkPublishEnvironmentResponseFromJson(
  Map<String, dynamic> json,
) => _NetworkPublishEnvironmentResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  error: json['error'] as String?,
  environment: json['environment'] == null
      ? null
      : NetworkEnvironmentDescriptor.fromJson(
          json['environment'] as Map<String, dynamic>,
        ),
);

Map<String, dynamic> _$NetworkPublishEnvironmentResponseToJson(
  _NetworkPublishEnvironmentResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'error': instance.error,
  'environment': instance.environment?.toJson(),
};

_NetworkListEnvironmentsRequest _$NetworkListEnvironmentsRequestFromJson(
  Map<String, dynamic> json,
) => _NetworkListEnvironmentsRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  activeOnly: json['active_only'] as bool,
);

Map<String, dynamic> _$NetworkListEnvironmentsRequestToJson(
  _NetworkListEnvironmentsRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'active_only': instance.activeOnly,
};

_NetworkListEnvironmentsResponse _$NetworkListEnvironmentsResponseFromJson(
  Map<String, dynamic> json,
) => _NetworkListEnvironmentsResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  error: json['error'] as String?,
  environments:
      (json['environments'] as List<dynamic>?)
          ?.map(
            (e) => NetworkEnvironmentDescriptor.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$NetworkListEnvironmentsResponseToJson(
  _NetworkListEnvironmentsResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'error': instance.error,
  'environments': instance.environments.map((e) => e.toJson()).toList(),
};

_NetworkResolveHostedServiceRoutesRequest
_$NetworkResolveHostedServiceRoutesRequestFromJson(Map<String, dynamic> json) =>
    _NetworkResolveHostedServiceRoutesRequest(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      requestId: _$JsonConverterFromJson<String, UuidValue>(
        json['request_id'],
        const UuidValueConverter().fromJson,
      ),
      consumerNodeId: const UuidValueConverter().fromJson(
        json['consumer_node_id'] as String,
      ),
      serviceName: json['service_name'] as String?,
      endpointRef: json['endpoint_ref'] as String?,
      acceptedPeersOnly: json['accepted_peers_only'] as bool,
    );

Map<String, dynamic> _$NetworkResolveHostedServiceRoutesRequestToJson(
  _NetworkResolveHostedServiceRoutesRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'consumer_node_id': const UuidValueConverter().toJson(
    instance.consumerNodeId,
  ),
  'service_name': instance.serviceName,
  'endpoint_ref': instance.endpointRef,
  'accepted_peers_only': instance.acceptedPeersOnly,
};

_NetworkResolveHostedServiceRoutesResponse
_$NetworkResolveHostedServiceRoutesResponseFromJson(
  Map<String, dynamic> json,
) => _NetworkResolveHostedServiceRoutesResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  error: json['error'] as String?,
  routes:
      (json['routes'] as List<dynamic>?)
          ?.map(
            (e) => NetworkResolvedHostedServiceRoute.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$NetworkResolveHostedServiceRoutesResponseToJson(
  _NetworkResolveHostedServiceRoutesResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'error': instance.error,
  'routes': instance.routes.map((e) => e.toJson()).toList(),
};

_NetworkDiscoverTerritoryRequest _$NetworkDiscoverTerritoryRequestFromJson(
  Map<String, dynamic> json,
) => _NetworkDiscoverTerritoryRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  includePeers: json['include_peers'] as bool,
  includeHostedServices: json['include_hosted_services'] as bool,
  includeEnvironments: json['include_environments'] as bool,
  activeEnvironmentsOnly: json['active_environments_only'] as bool,
  acceptedPeersOnly: json['accepted_peers_only'] as bool,
  limitNodes: (json['limit_nodes'] as num?)?.toInt(),
);

Map<String, dynamic> _$NetworkDiscoverTerritoryRequestToJson(
  _NetworkDiscoverTerritoryRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'include_peers': instance.includePeers,
  'include_hosted_services': instance.includeHostedServices,
  'include_environments': instance.includeEnvironments,
  'active_environments_only': instance.activeEnvironmentsOnly,
  'accepted_peers_only': instance.acceptedPeersOnly,
  'limit_nodes': instance.limitNodes,
};

_NetworkDiscoverTerritoryResponse _$NetworkDiscoverTerritoryResponseFromJson(
  Map<String, dynamic> json,
) => _NetworkDiscoverTerritoryResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  error: json['error'] as String?,
  nodes:
      (json['nodes'] as List<dynamic>?)
          ?.map(
            (e) => NetworkTerritoryNodeDescriptor.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  summary: json['summary'] as String?,
);

Map<String, dynamic> _$NetworkDiscoverTerritoryResponseToJson(
  _NetworkDiscoverTerritoryResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'error': instance.error,
  'nodes': instance.nodes.map((e) => e.toJson()).toList(),
  'summary': instance.summary,
};

_NetworkDiscoverExperienceTerritoryRequest
_$NetworkDiscoverExperienceTerritoryRequestFromJson(
  Map<String, dynamic> json,
) => _NetworkDiscoverExperienceTerritoryRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  experienceName: json['experience_name'] as String,
  requiredServicePackageNames:
      (json['required_service_package_names'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  requiredEndpointRefs:
      (json['required_endpoint_refs'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  consumerNodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['consumer_node_id'],
    const UuidValueConverter().fromJson,
  ),
  activeEnvironmentsOnly: json['active_environments_only'] as bool,
  acceptedPeersOnly: json['accepted_peers_only'] as bool,
  includeRouteHints: json['include_route_hints'] as bool,
  requireAccessEvidence: json['require_access_evidence'] as bool,
  accessEvidenceRefs:
      (json['access_evidence_refs'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  limitEntries: (json['limit_entries'] as num?)?.toInt(),
);

Map<String, dynamic> _$NetworkDiscoverExperienceTerritoryRequestToJson(
  _NetworkDiscoverExperienceTerritoryRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'experience_name': instance.experienceName,
  'required_service_package_names': instance.requiredServicePackageNames,
  'required_endpoint_refs': instance.requiredEndpointRefs,
  'consumer_node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.consumerNodeId,
    const UuidValueConverter().toJson,
  ),
  'active_environments_only': instance.activeEnvironmentsOnly,
  'accepted_peers_only': instance.acceptedPeersOnly,
  'include_route_hints': instance.includeRouteHints,
  'require_access_evidence': instance.requireAccessEvidence,
  'access_evidence_refs': instance.accessEvidenceRefs,
  'limit_entries': instance.limitEntries,
};

_NetworkDiscoverExperienceTerritoryResponse
_$NetworkDiscoverExperienceTerritoryResponseFromJson(
  Map<String, dynamic> json,
) => _NetworkDiscoverExperienceTerritoryResponse(
  requestId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_id'],
    const UuidValueConverter().fromJson,
  ),
  success: json['success'] as bool,
  error: json['error'] as String?,
  experienceName: json['experience_name'] as String?,
  entries:
      (json['entries'] as List<dynamic>?)
          ?.map(
            (e) => NetworkExperienceTerritoryEntry.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  summary: json['summary'] as String?,
);

Map<String, dynamic> _$NetworkDiscoverExperienceTerritoryResponseToJson(
  _NetworkDiscoverExperienceTerritoryResponse instance,
) => <String, dynamic>{
  'request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestId,
    const UuidValueConverter().toJson,
  ),
  'success': instance.success,
  'error': instance.error,
  'experience_name': instance.experienceName,
  'entries': instance.entries.map((e) => e.toJson()).toList(),
  'summary': instance.summary,
};
