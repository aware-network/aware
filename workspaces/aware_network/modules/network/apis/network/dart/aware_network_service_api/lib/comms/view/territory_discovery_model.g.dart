// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'territory_discovery_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_NetworkTerritoryNodeRouteViewStateV1
_$NetworkTerritoryNodeRouteViewStateV1FromJson(Map<String, dynamic> json) =>
    _NetworkTerritoryNodeRouteViewStateV1(
      nodeId: json['node_id'] as String?,
      publicKey: json['public_key'] as String?,
      hostname: json['hostname'] as String?,
      port: (json['port'] as num?)?.toInt(),
      baseUrl: json['base_url'] as String?,
      status: json['status'] as String,
      lastSeenAt: json['last_seen_at'] as String?,
    );

Map<String, dynamic> _$NetworkTerritoryNodeRouteViewStateV1ToJson(
  _NetworkTerritoryNodeRouteViewStateV1 instance,
) => <String, dynamic>{
  'node_id': instance.nodeId,
  'public_key': instance.publicKey,
  'hostname': instance.hostname,
  'port': instance.port,
  'base_url': instance.baseUrl,
  'status': instance.status,
  'last_seen_at': instance.lastSeenAt,
};

_NetworkTerritoryEnvironmentViewStateV1
_$NetworkTerritoryEnvironmentViewStateV1FromJson(Map<String, dynamic> json) =>
    _NetworkTerritoryEnvironmentViewStateV1(
      nodeId: json['node_id'] as String?,
      environmentId: json['environment_id'] as String?,
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
      environmentConfigId: json['environment_config_id'] as String?,
      environmentConfigKey: json['environment_config_key'] as String?,
    );

Map<String, dynamic> _$NetworkTerritoryEnvironmentViewStateV1ToJson(
  _NetworkTerritoryEnvironmentViewStateV1 instance,
) => <String, dynamic>{
  'node_id': instance.nodeId,
  'environment_id': instance.environmentId,
  'environment_key': instance.environmentKey,
  'environment_title': instance.environmentTitle,
  'role': instance.role,
  'is_active': instance.isActive,
  'priority': instance.priority,
  'status': instance.status,
  'experience_names': instance.experienceNames,
  'environment_config_id': instance.environmentConfigId,
  'environment_config_key': instance.environmentConfigKey,
};

_NetworkTerritoryHostedServiceViewStateV1
_$NetworkTerritoryHostedServiceViewStateV1FromJson(Map<String, dynamic> json) =>
    _NetworkTerritoryHostedServiceViewStateV1(
      serviceId: json['service_id'] as String?,
      serviceName: json['service_name'] as String?,
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
      hostId: json['host_id'] as String?,
      hostVersion: json['host_version'] as String?,
      protocolVersion: json['protocol_version'] as String?,
      supportsStreamEvents: json['supports_stream_events'] as bool,
    );

Map<String, dynamic> _$NetworkTerritoryHostedServiceViewStateV1ToJson(
  _NetworkTerritoryHostedServiceViewStateV1 instance,
) => <String, dynamic>{
  'service_id': instance.serviceId,
  'service_name': instance.serviceName,
  'service_package_names': instance.servicePackageNames,
  'endpoint_refs': instance.endpointRefs,
  'stream_endpoint_refs': instance.streamEndpointRefs,
  'host_id': instance.hostId,
  'host_version': instance.hostVersion,
  'protocol_version': instance.protocolVersion,
  'supports_stream_events': instance.supportsStreamEvents,
};

_NetworkTerritoryPeerViewStateV1 _$NetworkTerritoryPeerViewStateV1FromJson(
  Map<String, dynamic> json,
) => _NetworkTerritoryPeerViewStateV1(
  edgeId: json['edge_id'] as String?,
  sourceNodeId: json['source_node_id'] as String?,
  targetNodeId: json['target_node_id'] as String?,
  peerNodeId: json['peer_node_id'] as String?,
  peerBaseUrl: json['peer_base_url'] as String?,
  direction: json['direction'] as String,
  status: json['status'] as String,
  trustScore: (json['trust_score'] as num).toDouble(),
  connectedAt: json['connected_at'] as String?,
  lastPingAt: json['last_ping_at'] as String?,
);

Map<String, dynamic> _$NetworkTerritoryPeerViewStateV1ToJson(
  _NetworkTerritoryPeerViewStateV1 instance,
) => <String, dynamic>{
  'edge_id': instance.edgeId,
  'source_node_id': instance.sourceNodeId,
  'target_node_id': instance.targetNodeId,
  'peer_node_id': instance.peerNodeId,
  'peer_base_url': instance.peerBaseUrl,
  'direction': instance.direction,
  'status': instance.status,
  'trust_score': instance.trustScore,
  'connected_at': instance.connectedAt,
  'last_ping_at': instance.lastPingAt,
};

_NetworkTerritoryNodeViewStateV1 _$NetworkTerritoryNodeViewStateV1FromJson(
  Map<String, dynamic> json,
) => _NetworkTerritoryNodeViewStateV1(
  node: json['node'] == null
      ? null
      : NetworkTerritoryNodeRouteViewStateV1.fromJson(
          json['node'] as Map<String, dynamic>,
        ),
  environments:
      (json['environments'] as List<dynamic>?)
          ?.map(
            (e) => NetworkTerritoryEnvironmentViewStateV1.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  hostedServices:
      (json['hosted_services'] as List<dynamic>?)
          ?.map(
            (e) => NetworkTerritoryHostedServiceViewStateV1.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  peers:
      (json['peers'] as List<dynamic>?)
          ?.map(
            (e) => NetworkTerritoryPeerViewStateV1.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$NetworkTerritoryNodeViewStateV1ToJson(
  _NetworkTerritoryNodeViewStateV1 instance,
) => <String, dynamic>{
  'node': instance.node?.toJson(),
  'environments': instance.environments.map((e) => e.toJson()).toList(),
  'hosted_services': instance.hostedServices.map((e) => e.toJson()).toList(),
  'peers': instance.peers.map((e) => e.toJson()).toList(),
};

_NetworkTerritoryDiscoveryViewStateV1
_$NetworkTerritoryDiscoveryViewStateV1FromJson(Map<String, dynamic> json) =>
    _NetworkTerritoryDiscoveryViewStateV1(
      status: json['status'] as String,
      authoritySourceUrl: json['authority_source_url'] as String?,
      nodes:
          (json['nodes'] as List<dynamic>?)
              ?.map(
                (e) => NetworkTerritoryNodeViewStateV1.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
      summary: json['summary'] as String?,
      emptyMessage: json['empty_message'] as String,
      error: json['error'] as String?,
      provenance: json['provenance'] as Map<String, dynamic>,
    );

Map<String, dynamic> _$NetworkTerritoryDiscoveryViewStateV1ToJson(
  _NetworkTerritoryDiscoveryViewStateV1 instance,
) => <String, dynamic>{
  'status': instance.status,
  'authority_source_url': instance.authoritySourceUrl,
  'nodes': instance.nodes.map((e) => e.toJson()).toList(),
  'summary': instance.summary,
  'empty_message': instance.emptyMessage,
  'error': instance.error,
  'provenance': instance.provenance,
};
