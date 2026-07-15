// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:freezed_annotation/freezed_annotation.dart';

part 'territory_discovery_model.freezed.dart';
part 'territory_discovery_model.g.dart';

/// View-state contract for public Network territory discovery.
/// Public API view key: network.territory_discovery
@freezed
abstract class NetworkTerritoryNodeRouteViewStateV1
    with _$NetworkTerritoryNodeRouteViewStateV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkTerritoryNodeRouteViewStateV1.def({
    String? nodeId,
    String? publicKey,
    String? hostname,
    int? port,
    String? baseUrl,
    required String status,
    String? lastSeenAt,
  }) = _NetworkTerritoryNodeRouteViewStateV1;

  factory NetworkTerritoryNodeRouteViewStateV1({
    String? nodeId,
    String? publicKey,
    String? hostname,
    int? port,
    String? baseUrl,
    String? status,
    String? lastSeenAt,
  }) {
    return _NetworkTerritoryNodeRouteViewStateV1(
      nodeId: nodeId,
      publicKey: publicKey,
      hostname: hostname,
      port: port,
      baseUrl: baseUrl,
      status: status ?? 'active',
      lastSeenAt: lastSeenAt,
    );
  }

  factory NetworkTerritoryNodeRouteViewStateV1.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkTerritoryNodeRouteViewStateV1FromJson({
    ...json,
    if (!json.containsKey('status')) 'status': 'active',
  });
}

@freezed
abstract class NetworkTerritoryEnvironmentViewStateV1
    with _$NetworkTerritoryEnvironmentViewStateV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkTerritoryEnvironmentViewStateV1.def({
    String? nodeId,
    String? environmentId,
    String? environmentKey,
    String? environmentTitle,
    required String role,
    required bool isActive,
    required int priority,
    required String status,
    @Default(const []) List<String> experienceNames,
    String? environmentConfigId,
    String? environmentConfigKey,
  }) = _NetworkTerritoryEnvironmentViewStateV1;

  factory NetworkTerritoryEnvironmentViewStateV1({
    String? nodeId,
    String? environmentId,
    String? environmentKey,
    String? environmentTitle,
    String? role,
    bool? isActive,
    int? priority,
    String? status,
    List<String> experienceNames = const [],
    String? environmentConfigId,
    String? environmentConfigKey,
  }) {
    return _NetworkTerritoryEnvironmentViewStateV1(
      nodeId: nodeId,
      environmentId: environmentId,
      environmentKey: environmentKey,
      environmentTitle: environmentTitle,
      role: role ?? 'replica',
      isActive: isActive ?? true,
      priority: priority ?? 0,
      status: status ?? 'active',
      experienceNames: experienceNames,
      environmentConfigId: environmentConfigId,
      environmentConfigKey: environmentConfigKey,
    );
  }

  factory NetworkTerritoryEnvironmentViewStateV1.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkTerritoryEnvironmentViewStateV1FromJson({
    ...json,
    if (!json.containsKey('role')) 'role': 'replica',
    if (!json.containsKey('is_active')) 'is_active': true,
    if (!json.containsKey('priority')) 'priority': 0,
    if (!json.containsKey('status')) 'status': 'active',
  });
}

@freezed
abstract class NetworkTerritoryHostedServiceViewStateV1
    with _$NetworkTerritoryHostedServiceViewStateV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkTerritoryHostedServiceViewStateV1.def({
    String? serviceId,
    String? serviceName,
    @Default(const []) List<String> servicePackageNames,
    @Default(const []) List<String> endpointRefs,
    @Default(const []) List<String> streamEndpointRefs,
    String? hostId,
    String? hostVersion,
    String? protocolVersion,
    required bool supportsStreamEvents,
  }) = _NetworkTerritoryHostedServiceViewStateV1;

  factory NetworkTerritoryHostedServiceViewStateV1({
    String? serviceId,
    String? serviceName,
    List<String> servicePackageNames = const [],
    List<String> endpointRefs = const [],
    List<String> streamEndpointRefs = const [],
    String? hostId,
    String? hostVersion,
    String? protocolVersion,
    bool? supportsStreamEvents,
  }) {
    return _NetworkTerritoryHostedServiceViewStateV1(
      serviceId: serviceId,
      serviceName: serviceName,
      servicePackageNames: servicePackageNames,
      endpointRefs: endpointRefs,
      streamEndpointRefs: streamEndpointRefs,
      hostId: hostId,
      hostVersion: hostVersion,
      protocolVersion: protocolVersion,
      supportsStreamEvents: supportsStreamEvents ?? false,
    );
  }

  factory NetworkTerritoryHostedServiceViewStateV1.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkTerritoryHostedServiceViewStateV1FromJson({
    ...json,
    if (!json.containsKey('supports_stream_events'))
      'supports_stream_events': false,
  });
}

@freezed
abstract class NetworkTerritoryPeerViewStateV1
    with _$NetworkTerritoryPeerViewStateV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkTerritoryPeerViewStateV1.def({
    String? edgeId,
    String? sourceNodeId,
    String? targetNodeId,
    String? peerNodeId,
    String? peerBaseUrl,
    required String direction,
    required String status,
    required double trustScore,
    String? connectedAt,
    String? lastPingAt,
  }) = _NetworkTerritoryPeerViewStateV1;

  factory NetworkTerritoryPeerViewStateV1({
    String? edgeId,
    String? sourceNodeId,
    String? targetNodeId,
    String? peerNodeId,
    String? peerBaseUrl,
    String? direction,
    String? status,
    double? trustScore,
    String? connectedAt,
    String? lastPingAt,
  }) {
    return _NetworkTerritoryPeerViewStateV1(
      edgeId: edgeId,
      sourceNodeId: sourceNodeId,
      targetNodeId: targetNodeId,
      peerNodeId: peerNodeId,
      peerBaseUrl: peerBaseUrl,
      direction: direction ?? 'outgoing',
      status: status ?? 'accepted',
      trustScore: trustScore ?? 0.0,
      connectedAt: connectedAt,
      lastPingAt: lastPingAt,
    );
  }

  factory NetworkTerritoryPeerViewStateV1.fromJson(Map<String, dynamic> json) =>
      _$NetworkTerritoryPeerViewStateV1FromJson({
        ...json,
        if (!json.containsKey('direction')) 'direction': 'outgoing',
        if (!json.containsKey('status')) 'status': 'accepted',
        if (!json.containsKey('trust_score')) 'trust_score': 0.0,
      });
}

@freezed
abstract class NetworkTerritoryNodeViewStateV1
    with _$NetworkTerritoryNodeViewStateV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkTerritoryNodeViewStateV1.def({
    NetworkTerritoryNodeRouteViewStateV1? node,
    @Default(const [])
    List<NetworkTerritoryEnvironmentViewStateV1> environments,
    @Default(const [])
    List<NetworkTerritoryHostedServiceViewStateV1> hostedServices,
    @Default(const []) List<NetworkTerritoryPeerViewStateV1> peers,
  }) = _NetworkTerritoryNodeViewStateV1;

  factory NetworkTerritoryNodeViewStateV1({
    NetworkTerritoryNodeRouteViewStateV1? node,
    List<NetworkTerritoryEnvironmentViewStateV1> environments = const [],
    List<NetworkTerritoryHostedServiceViewStateV1> hostedServices = const [],
    List<NetworkTerritoryPeerViewStateV1> peers = const [],
  }) {
    return _NetworkTerritoryNodeViewStateV1(
      node: node,
      environments: environments,
      hostedServices: hostedServices,
      peers: peers,
    );
  }

  factory NetworkTerritoryNodeViewStateV1.fromJson(Map<String, dynamic> json) =>
      _$NetworkTerritoryNodeViewStateV1FromJson(json);
}

@freezed
abstract class NetworkTerritoryDiscoveryViewStateV1
    with _$NetworkTerritoryDiscoveryViewStateV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkTerritoryDiscoveryViewStateV1.def({
    required String status,
    String? authoritySourceUrl,
    @Default(const []) List<NetworkTerritoryNodeViewStateV1> nodes,
    String? summary,
    required String emptyMessage,
    String? error,
    required Map<String, dynamic> provenance,
  }) = _NetworkTerritoryDiscoveryViewStateV1;

  factory NetworkTerritoryDiscoveryViewStateV1({
    String? status,
    String? authoritySourceUrl,
    List<NetworkTerritoryNodeViewStateV1> nodes = const [],
    String? summary,
    String? emptyMessage,
    String? error,
    Map<String, dynamic>? provenance,
  }) {
    return _NetworkTerritoryDiscoveryViewStateV1(
      status: status ?? 'waiting',
      authoritySourceUrl: authoritySourceUrl,
      nodes: nodes,
      summary: summary,
      emptyMessage:
          emptyMessage ?? 'No Network territory has been published yet',
      error: error,
      provenance: provenance ?? {},
    );
  }

  factory NetworkTerritoryDiscoveryViewStateV1.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkTerritoryDiscoveryViewStateV1FromJson({
    ...json,
    if (!json.containsKey('status')) 'status': 'waiting',
    if (!json.containsKey('empty_message'))
      'empty_message': 'No Network territory has been published yet',
    if (!json.containsKey('provenance')) 'provenance': {},
  });
}
