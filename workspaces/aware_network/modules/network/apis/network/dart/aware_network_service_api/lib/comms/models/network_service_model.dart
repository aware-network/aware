// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'network_service_model.freezed.dart';
part 'network_service_model.g.dart';

/// Public Network Service DTOs for topology, hosted-service discovery, and route resolution.
/// These are graph/ORM agnostic API contracts. The Network Service implementation may
/// back them with local cache during bootstrap, but durable truth belongs to committed
/// Network ontology objects (`NetworkNode`, `NetworkNodePeer`, `NetworkNodeService`).
@freezed
abstract class NetworkNodeRouteDescriptor with _$NetworkNodeRouteDescriptor {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeRouteDescriptor.def({
    @UuidValueConverter() required UuidValue nodeId,
    String? publicKey,
    required String hostname,
    required int port,
    String? baseUrl,
    required String status,
    String? lastSeenAt,
  }) = _NetworkNodeRouteDescriptor;

  factory NetworkNodeRouteDescriptor({
    required UuidValue nodeId,
    String? publicKey,
    required String hostname,
    required int port,
    String? baseUrl,
    String? status,
    String? lastSeenAt,
  }) {
    return _NetworkNodeRouteDescriptor(
      nodeId: nodeId,
      publicKey: publicKey,
      hostname: hostname,
      port: port,
      baseUrl: baseUrl,
      status: status ?? 'active',
      lastSeenAt: lastSeenAt,
    );
  }

  factory NetworkNodeRouteDescriptor.fromJson(Map<String, dynamic> json) =>
      _$NetworkNodeRouteDescriptorFromJson({
        ...json,
        if (!json.containsKey('status')) 'status': 'active',
      });
}

@freezed
abstract class NetworkPeerFanoutRuleDescriptor
    with _$NetworkPeerFanoutRuleDescriptor {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkPeerFanoutRuleDescriptor.def({
    @UuidValueConverter() UuidValue? id,
    @UuidValueConverter() required UuidValue laneBranchId,
    required String laneProjectionHash,
    required bool enabled,
    required String mode,
  }) = _NetworkPeerFanoutRuleDescriptor;

  factory NetworkPeerFanoutRuleDescriptor({
    UuidValue? id,
    required UuidValue laneBranchId,
    required String laneProjectionHash,
    bool? enabled,
    String? mode,
  }) {
    return _NetworkPeerFanoutRuleDescriptor(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      laneBranchId: laneBranchId,
      laneProjectionHash: laneProjectionHash,
      enabled: enabled ?? true,
      mode: mode ?? 'notify_pull',
    );
  }

  factory NetworkPeerFanoutRuleDescriptor.fromJson(Map<String, dynamic> json) =>
      _$NetworkPeerFanoutRuleDescriptorFromJson({
        ...json,
        if (!json.containsKey('enabled')) 'enabled': true,
        if (!json.containsKey('mode')) 'mode': 'notify_pull',
      });
}

@freezed
abstract class NetworkPeerDescriptor with _$NetworkPeerDescriptor {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkPeerDescriptor.def({
    @UuidValueConverter() UuidValue? edgeId,
    @UuidValueConverter() required UuidValue sourceNodeId,
    @UuidValueConverter() required UuidValue targetNodeId,
    @UuidValueConverter() required UuidValue peerNodeId,
    required String peerBaseUrl,
    required String direction,
    required String status,
    required double trustScore,
    @Default(const []) List<NetworkPeerFanoutRuleDescriptor> fanoutRules,
    String? connectedAt,
    String? lastPingAt,
  }) = _NetworkPeerDescriptor;

  factory NetworkPeerDescriptor({
    UuidValue? edgeId,
    required UuidValue sourceNodeId,
    required UuidValue targetNodeId,
    required UuidValue peerNodeId,
    required String peerBaseUrl,
    String? direction,
    String? status,
    double? trustScore,
    List<NetworkPeerFanoutRuleDescriptor> fanoutRules = const [],
    String? connectedAt,
    String? lastPingAt,
  }) {
    return _NetworkPeerDescriptor(
      edgeId: edgeId,
      sourceNodeId: sourceNodeId,
      targetNodeId: targetNodeId,
      peerNodeId: peerNodeId,
      peerBaseUrl: peerBaseUrl,
      direction: direction ?? 'outgoing',
      status: status ?? 'accepted',
      trustScore: trustScore ?? 0.0,
      fanoutRules: fanoutRules,
      connectedAt: connectedAt,
      lastPingAt: lastPingAt,
    );
  }

  factory NetworkPeerDescriptor.fromJson(Map<String, dynamic> json) =>
      _$NetworkPeerDescriptorFromJson({
        ...json,
        if (!json.containsKey('direction')) 'direction': 'outgoing',
        if (!json.containsKey('status')) 'status': 'accepted',
        if (!json.containsKey('trust_score')) 'trust_score': 0.0,
      });
}

@freezed
abstract class NetworkHostedServiceDescriptor
    with _$NetworkHostedServiceDescriptor {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkHostedServiceDescriptor.def({
    @UuidValueConverter() UuidValue? servicePackageId,
    @UuidValueConverter() required UuidValue serviceId,
    required String serviceName,
    @Default(const []) List<String> servicePackageNames,
    @Default(const []) List<String> endpointRefs,
    @Default(const []) List<String> streamEndpointRefs,
    required String hostId,
    String? hostVersion,
    required String protocolVersion,
    required bool supportsStreamEvents,
  }) = _NetworkHostedServiceDescriptor;

  factory NetworkHostedServiceDescriptor({
    UuidValue? servicePackageId,
    required UuidValue serviceId,
    required String serviceName,
    List<String> servicePackageNames = const [],
    List<String> endpointRefs = const [],
    List<String> streamEndpointRefs = const [],
    required String hostId,
    String? hostVersion,
    required String protocolVersion,
    bool? supportsStreamEvents,
  }) {
    return _NetworkHostedServiceDescriptor(
      servicePackageId: servicePackageId,
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

  factory NetworkHostedServiceDescriptor.fromJson(Map<String, dynamic> json) =>
      _$NetworkHostedServiceDescriptorFromJson({
        ...json,
        if (!json.containsKey('supports_stream_events'))
          'supports_stream_events': false,
      });
}

@freezed
abstract class NetworkEnvironmentDescriptor
    with _$NetworkEnvironmentDescriptor {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkEnvironmentDescriptor.def({
    @UuidValueConverter() UuidValue? nodeId,
    @UuidValueConverter() required UuidValue environmentId,
    String? environmentKey,
    String? environmentTitle,
    required String role,
    required bool isActive,
    required int priority,
    required String status,
    @Default(const []) List<String> experienceNames,
    @UuidValueConverter() UuidValue? environmentConfigId,
    String? environmentConfigKey,
  }) = _NetworkEnvironmentDescriptor;

  factory NetworkEnvironmentDescriptor({
    UuidValue? nodeId,
    required UuidValue environmentId,
    String? environmentKey,
    String? environmentTitle,
    String? role,
    bool? isActive,
    int? priority,
    String? status,
    List<String> experienceNames = const [],
    UuidValue? environmentConfigId,
    String? environmentConfigKey,
  }) {
    return _NetworkEnvironmentDescriptor(
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

  factory NetworkEnvironmentDescriptor.fromJson(Map<String, dynamic> json) =>
      _$NetworkEnvironmentDescriptorFromJson({
        ...json,
        if (!json.containsKey('role')) 'role': 'replica',
        if (!json.containsKey('is_active')) 'is_active': true,
        if (!json.containsKey('priority')) 'priority': 0,
        if (!json.containsKey('status')) 'status': 'active',
      });
}

@freezed
abstract class NetworkResolvedHostedServiceRoute
    with _$NetworkResolvedHostedServiceRoute {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkResolvedHostedServiceRoute.def({
    @UuidValueConverter() required UuidValue providerNodeId,
    required String providerNodeBaseUrl,
    @UuidValueConverter() UuidValue? routeConnectionId,
    required NetworkHostedServiceDescriptor hostedService,
  }) = _NetworkResolvedHostedServiceRoute;

  factory NetworkResolvedHostedServiceRoute({
    required UuidValue providerNodeId,
    required String providerNodeBaseUrl,
    UuidValue? routeConnectionId,
    required NetworkHostedServiceDescriptor hostedService,
  }) {
    return _NetworkResolvedHostedServiceRoute(
      providerNodeId: providerNodeId,
      providerNodeBaseUrl: providerNodeBaseUrl,
      routeConnectionId: routeConnectionId,
      hostedService: hostedService,
    );
  }

  factory NetworkResolvedHostedServiceRoute.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkResolvedHostedServiceRouteFromJson(json);
}

@freezed
abstract class NetworkTerritoryNodeDescriptor
    with _$NetworkTerritoryNodeDescriptor {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkTerritoryNodeDescriptor.def({
    required NetworkNodeRouteDescriptor node,
    @Default(const []) List<NetworkEnvironmentDescriptor> environments,
    @Default(const []) List<NetworkHostedServiceDescriptor> hostedServices,
    @Default(const []) List<NetworkPeerDescriptor> peers,
  }) = _NetworkTerritoryNodeDescriptor;

  factory NetworkTerritoryNodeDescriptor({
    required NetworkNodeRouteDescriptor node,
    List<NetworkEnvironmentDescriptor> environments = const [],
    List<NetworkHostedServiceDescriptor> hostedServices = const [],
    List<NetworkPeerDescriptor> peers = const [],
  }) {
    return _NetworkTerritoryNodeDescriptor(
      node: node,
      environments: environments,
      hostedServices: hostedServices,
      peers: peers,
    );
  }

  factory NetworkTerritoryNodeDescriptor.fromJson(Map<String, dynamic> json) =>
      _$NetworkTerritoryNodeDescriptorFromJson(json);
}

@freezed
abstract class NetworkExperienceServiceCandidate
    with _$NetworkExperienceServiceCandidate {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkExperienceServiceCandidate.def({
    required NetworkHostedServiceDescriptor hostedService,
    @UuidValueConverter() required UuidValue providerNodeId,
    String? providerNodeBaseUrl,
    @UuidValueConverter() UuidValue? routeConnectionId,
    required String routeStatus,
    @Default(const []) List<String> matchedServicePackageNames,
    @Default(const []) List<String> matchedEndpointRefs,
    @Default(const []) List<String> missingServicePackageNames,
    @Default(const []) List<String> missingEndpointRefs,
  }) = _NetworkExperienceServiceCandidate;

  factory NetworkExperienceServiceCandidate({
    required NetworkHostedServiceDescriptor hostedService,
    required UuidValue providerNodeId,
    String? providerNodeBaseUrl,
    UuidValue? routeConnectionId,
    String? routeStatus,
    List<String> matchedServicePackageNames = const [],
    List<String> matchedEndpointRefs = const [],
    List<String> missingServicePackageNames = const [],
    List<String> missingEndpointRefs = const [],
  }) {
    return _NetworkExperienceServiceCandidate(
      hostedService: hostedService,
      providerNodeId: providerNodeId,
      providerNodeBaseUrl: providerNodeBaseUrl,
      routeConnectionId: routeConnectionId,
      routeStatus: routeStatus ?? 'reachable',
      matchedServicePackageNames: matchedServicePackageNames,
      matchedEndpointRefs: matchedEndpointRefs,
      missingServicePackageNames: missingServicePackageNames,
      missingEndpointRefs: missingEndpointRefs,
    );
  }

  factory NetworkExperienceServiceCandidate.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkExperienceServiceCandidateFromJson({
    ...json,
    if (!json.containsKey('route_status')) 'route_status': 'reachable',
  });
}

@freezed
abstract class NetworkExperienceTerritoryEntry
    with _$NetworkExperienceTerritoryEntry {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkExperienceTerritoryEntry.def({
    required String experienceName,
    required NetworkNodeRouteDescriptor node,
    required NetworkEnvironmentDescriptor environment,
    @Default(const [])
    List<NetworkExperienceServiceCandidate> serviceCandidates,
    required String routeStatus,
    @Default(const []) List<String> missingServicePackageNames,
    @Default(const []) List<String> missingEndpointRefs,
  }) = _NetworkExperienceTerritoryEntry;

  factory NetworkExperienceTerritoryEntry({
    required String experienceName,
    required NetworkNodeRouteDescriptor node,
    required NetworkEnvironmentDescriptor environment,
    List<NetworkExperienceServiceCandidate> serviceCandidates = const [],
    String? routeStatus,
    List<String> missingServicePackageNames = const [],
    List<String> missingEndpointRefs = const [],
  }) {
    return _NetworkExperienceTerritoryEntry(
      experienceName: experienceName,
      node: node,
      environment: environment,
      serviceCandidates: serviceCandidates,
      routeStatus: routeStatus ?? 'unavailable',
      missingServicePackageNames: missingServicePackageNames,
      missingEndpointRefs: missingEndpointRefs,
    );
  }

  factory NetworkExperienceTerritoryEntry.fromJson(Map<String, dynamic> json) =>
      _$NetworkExperienceTerritoryEntryFromJson({
        ...json,
        if (!json.containsKey('route_status')) 'route_status': 'unavailable',
      });
}

/// Non-authoritative Node runtime observation submitted for Network
/// reconciliation.
@freezed
abstract class NetworkNodePublicationNode with _$NetworkNodePublicationNode {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodePublicationNode.def({
    @UuidValueConverter() required UuidValue nodeId,
    required String publicKey,
    required String hostname,
    required int port,
    String? baseUrl,
    required String status,
  }) = _NetworkNodePublicationNode;

  factory NetworkNodePublicationNode({
    required UuidValue nodeId,
    required String publicKey,
    required String hostname,
    required int port,
    String? baseUrl,
    String? status,
  }) {
    return _NetworkNodePublicationNode(
      nodeId: nodeId,
      publicKey: publicKey,
      hostname: hostname,
      port: port,
      baseUrl: baseUrl,
      status: status ?? 'active',
    );
  }

  factory NetworkNodePublicationNode.fromJson(Map<String, dynamic> json) =>
      _$NetworkNodePublicationNodeFromJson({
        ...json,
        if (!json.containsKey('status')) 'status': 'active',
      });
}

/// One Environment association requested by a Node publication intent.
@freezed
abstract class NetworkNodePublicationEnvironment
    with _$NetworkNodePublicationEnvironment {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodePublicationEnvironment.def({
    @UuidValueConverter() required UuidValue environmentId,
    String? environmentKey,
    String? environmentTitle,
    required String role,
    required bool isActive,
    required int priority,
    required String status,
    @Default(const []) List<String> experienceNames,
    @UuidValueConverter() UuidValue? environmentConfigId,
    String? environmentConfigKey,
  }) = _NetworkNodePublicationEnvironment;

  factory NetworkNodePublicationEnvironment({
    required UuidValue environmentId,
    String? environmentKey,
    String? environmentTitle,
    String? role,
    bool? isActive,
    int? priority,
    String? status,
    List<String> experienceNames = const [],
    UuidValue? environmentConfigId,
    String? environmentConfigKey,
  }) {
    return _NetworkNodePublicationEnvironment(
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

  factory NetworkNodePublicationEnvironment.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkNodePublicationEnvironmentFromJson({
    ...json,
    if (!json.containsKey('role')) 'role': 'replica',
    if (!json.containsKey('is_active')) 'is_active': true,
    if (!json.containsKey('priority')) 'priority': 0,
    if (!json.containsKey('status')) 'status': 'active',
  });
}

/// One complete hosted-Service observation in a Node publication intent.
@freezed
abstract class NetworkNodePublicationHostedService
    with _$NetworkNodePublicationHostedService {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodePublicationHostedService.def({
    @UuidValueConverter() required UuidValue servicePackageId,
    @UuidValueConverter() required UuidValue serviceId,
    required String serviceName,
    @Default(const []) List<String> servicePackageNames,
    @Default(const []) List<String> endpointRefs,
    @Default(const []) List<String> streamEndpointRefs,
    required String hostId,
    String? hostVersion,
    required String protocolVersion,
    required bool supportsStreamEvents,
  }) = _NetworkNodePublicationHostedService;

  factory NetworkNodePublicationHostedService({
    required UuidValue servicePackageId,
    required UuidValue serviceId,
    required String serviceName,
    List<String> servicePackageNames = const [],
    List<String> endpointRefs = const [],
    List<String> streamEndpointRefs = const [],
    required String hostId,
    String? hostVersion,
    required String protocolVersion,
    bool? supportsStreamEvents,
  }) {
    return _NetworkNodePublicationHostedService(
      servicePackageId: servicePackageId,
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

  factory NetworkNodePublicationHostedService.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkNodePublicationHostedServiceFromJson({
    ...json,
    if (!json.containsKey('supports_stream_events'))
      'supports_stream_events': false,
  });
}

/// Desired runtime publication submitted by a Node through Network SDK.
/// This value is evidence, not Network discovery truth. Network Service owns
/// validation, committed-state comparison, mutation, and coverage verification.
@freezed
abstract class NetworkNodePublicationIntent
    with _$NetworkNodePublicationIntent {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodePublicationIntent.def({
    required String publicationDigest,
    required NetworkNodePublicationNode node,
    required NetworkNodePublicationEnvironment environment,
    @Default(const []) List<NetworkNodePublicationHostedService> hostedServices,
    @UuidValueConverter() UuidValue? sourceWorkspaceRevisionId,
    @UuidValueConverter() UuidValue? sourceNodeConfigId,
  }) = _NetworkNodePublicationIntent;

  factory NetworkNodePublicationIntent({
    required String publicationDigest,
    required NetworkNodePublicationNode node,
    required NetworkNodePublicationEnvironment environment,
    List<NetworkNodePublicationHostedService> hostedServices = const [],
    UuidValue? sourceWorkspaceRevisionId,
    UuidValue? sourceNodeConfigId,
  }) {
    return _NetworkNodePublicationIntent(
      publicationDigest: publicationDigest,
      node: node,
      environment: environment,
      hostedServices: hostedServices,
      sourceWorkspaceRevisionId: sourceWorkspaceRevisionId,
      sourceNodeConfigId: sourceNodeConfigId,
    );
  }

  factory NetworkNodePublicationIntent.fromJson(Map<String, dynamic> json) =>
      _$NetworkNodePublicationIntentFromJson(json);
}

/// One commit produced while Network Service reconciles publication intent.
@freezed
abstract class NetworkNodePublicationCommitReceipt
    with _$NetworkNodePublicationCommitReceipt {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodePublicationCommitReceipt.def({
    required String operation,
    @UuidValueConverter() UuidValue? domainCommitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    @UuidValueConverter() UuidValue? rootObjectId,
  }) = _NetworkNodePublicationCommitReceipt;

  factory NetworkNodePublicationCommitReceipt({
    required String operation,
    UuidValue? domainCommitId,
    UuidValue? objectInstanceGraphCommitId,
    UuidValue? rootObjectId,
  }) {
    return _NetworkNodePublicationCommitReceipt(
      operation: operation,
      domainCommitId: domainCommitId,
      objectInstanceGraphCommitId: objectInstanceGraphCommitId,
      rootObjectId: rootObjectId,
    );
  }

  factory NetworkNodePublicationCommitReceipt.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkNodePublicationCommitReceiptFromJson(json);
}

/// Committed coverage observed after Network Service reconciliation.
@freezed
abstract class NetworkNodePublicationCoverage
    with _$NetworkNodePublicationCoverage {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodePublicationCoverage.def({
    required bool nodeRegistered,
    required bool environmentPublished,
    @UuidValueListConverter()
    @Default(const [])
    List<UuidValue> hostedServicePackageIds,
    @UuidValueListConverter()
    @Default(const [])
    List<UuidValue> missingHostedServicePackageIds,
    @UuidValueListConverter()
    @Default(const [])
    List<UuidValue> unexpectedHostedServicePackageIds,
  }) = _NetworkNodePublicationCoverage;

  factory NetworkNodePublicationCoverage({
    bool? nodeRegistered,
    bool? environmentPublished,
    List<UuidValue> hostedServicePackageIds = const [],
    List<UuidValue> missingHostedServicePackageIds = const [],
    List<UuidValue> unexpectedHostedServicePackageIds = const [],
  }) {
    return _NetworkNodePublicationCoverage(
      nodeRegistered: nodeRegistered ?? false,
      environmentPublished: environmentPublished ?? false,
      hostedServicePackageIds: hostedServicePackageIds,
      missingHostedServicePackageIds: missingHostedServicePackageIds,
      unexpectedHostedServicePackageIds: unexpectedHostedServicePackageIds,
    );
  }

  factory NetworkNodePublicationCoverage.fromJson(Map<String, dynamic> json) =>
      _$NetworkNodePublicationCoverageFromJson({
        ...json,
        if (!json.containsKey('node_registered')) 'node_registered': false,
        if (!json.containsKey('environment_published'))
          'environment_published': false,
      });
}

@freezed
abstract class NetworkReconcileNodePublicationRequest
    with _$NetworkReconcileNodePublicationRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkReconcileNodePublicationRequest.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? requestId,
    required NetworkNodePublicationIntent intent,
  }) = _NetworkReconcileNodePublicationRequest;

  factory NetworkReconcileNodePublicationRequest({
    UuidValue? actorId,
    UuidValue? requestId,
    required NetworkNodePublicationIntent intent,
  }) {
    return _NetworkReconcileNodePublicationRequest(
      actorId: actorId,
      requestId: requestId,
      intent: intent,
    );
  }

  factory NetworkReconcileNodePublicationRequest.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkReconcileNodePublicationRequestFromJson(json);
}

@freezed
abstract class NetworkReconcileNodePublicationResponse
    with _$NetworkReconcileNodePublicationResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkReconcileNodePublicationResponse.def({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    required String status,
    String? error,
    String? publicationDigest,
    NetworkNodeRouteDescriptor? node,
    NetworkEnvironmentDescriptor? environment,
    @Default(const []) List<NetworkHostedServiceDescriptor> hostedServices,
    NetworkNodePublicationCoverage? coverage,
    @Default(const []) List<NetworkNodePublicationCommitReceipt> commitReceipts,
  }) = _NetworkReconcileNodePublicationResponse;

  factory NetworkReconcileNodePublicationResponse({
    UuidValue? requestId,
    bool? success,
    String? status,
    String? error,
    String? publicationDigest,
    NetworkNodeRouteDescriptor? node,
    NetworkEnvironmentDescriptor? environment,
    List<NetworkHostedServiceDescriptor> hostedServices = const [],
    NetworkNodePublicationCoverage? coverage,
    List<NetworkNodePublicationCommitReceipt> commitReceipts = const [],
  }) {
    return _NetworkReconcileNodePublicationResponse(
      requestId: requestId,
      success: success ?? true,
      status: status ?? 'converged',
      error: error,
      publicationDigest: publicationDigest,
      node: node,
      environment: environment,
      hostedServices: hostedServices,
      coverage: coverage,
      commitReceipts: commitReceipts,
    );
  }

  factory NetworkReconcileNodePublicationResponse.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkReconcileNodePublicationResponseFromJson({
    ...json,
    if (!json.containsKey('success')) 'success': true,
    if (!json.containsKey('status')) 'status': 'converged',
  });
}

@freezed
abstract class NetworkRegisterNodeRequest with _$NetworkRegisterNodeRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkRegisterNodeRequest.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() UuidValue? nodeId,
    required String publicKey,
    required String hostname,
    required int port,
    String? baseUrl,
    required String status,
  }) = _NetworkRegisterNodeRequest;

  factory NetworkRegisterNodeRequest({
    UuidValue? actorId,
    UuidValue? requestId,
    UuidValue? nodeId,
    required String publicKey,
    required String hostname,
    required int port,
    String? baseUrl,
    String? status,
  }) {
    return _NetworkRegisterNodeRequest(
      actorId: actorId,
      requestId: requestId,
      nodeId: nodeId,
      publicKey: publicKey,
      hostname: hostname,
      port: port,
      baseUrl: baseUrl,
      status: status ?? 'active',
    );
  }

  factory NetworkRegisterNodeRequest.fromJson(Map<String, dynamic> json) =>
      _$NetworkRegisterNodeRequestFromJson({
        ...json,
        if (!json.containsKey('status')) 'status': 'active',
      });
}

@freezed
abstract class NetworkRegisterNodeResponse with _$NetworkRegisterNodeResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkRegisterNodeResponse.def({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? error,
    NetworkNodeRouteDescriptor? node,
  }) = _NetworkRegisterNodeResponse;

  factory NetworkRegisterNodeResponse({
    UuidValue? requestId,
    bool? success,
    String? error,
    NetworkNodeRouteDescriptor? node,
  }) {
    return _NetworkRegisterNodeResponse(
      requestId: requestId,
      success: success ?? true,
      error: error,
      node: node,
    );
  }

  factory NetworkRegisterNodeResponse.fromJson(Map<String, dynamic> json) =>
      _$NetworkRegisterNodeResponseFromJson({
        ...json,
        if (!json.containsKey('success')) 'success': true,
      });
}

@freezed
abstract class NetworkUpsertPeerRequest with _$NetworkUpsertPeerRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkUpsertPeerRequest.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() required UuidValue sourceNodeId,
    @UuidValueConverter() required UuidValue targetNodeId,
    required String targetBaseUrl,
    required String status,
    required double trustScore,
  }) = _NetworkUpsertPeerRequest;

  factory NetworkUpsertPeerRequest({
    UuidValue? actorId,
    UuidValue? requestId,
    required UuidValue sourceNodeId,
    required UuidValue targetNodeId,
    required String targetBaseUrl,
    String? status,
    double? trustScore,
  }) {
    return _NetworkUpsertPeerRequest(
      actorId: actorId,
      requestId: requestId,
      sourceNodeId: sourceNodeId,
      targetNodeId: targetNodeId,
      targetBaseUrl: targetBaseUrl,
      status: status ?? 'accepted',
      trustScore: trustScore ?? 0.0,
    );
  }

  factory NetworkUpsertPeerRequest.fromJson(Map<String, dynamic> json) =>
      _$NetworkUpsertPeerRequestFromJson({
        ...json,
        if (!json.containsKey('status')) 'status': 'accepted',
        if (!json.containsKey('trust_score')) 'trust_score': 0.0,
      });
}

@freezed
abstract class NetworkUpsertPeerResponse with _$NetworkUpsertPeerResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkUpsertPeerResponse.def({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? error,
    NetworkPeerDescriptor? peer,
  }) = _NetworkUpsertPeerResponse;

  factory NetworkUpsertPeerResponse({
    UuidValue? requestId,
    bool? success,
    String? error,
    NetworkPeerDescriptor? peer,
  }) {
    return _NetworkUpsertPeerResponse(
      requestId: requestId,
      success: success ?? true,
      error: error,
      peer: peer,
    );
  }

  factory NetworkUpsertPeerResponse.fromJson(Map<String, dynamic> json) =>
      _$NetworkUpsertPeerResponseFromJson({
        ...json,
        if (!json.containsKey('success')) 'success': true,
      });
}

@freezed
abstract class NetworkListPeersRequest with _$NetworkListPeersRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkListPeersRequest.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() required UuidValue nodeId,
    required bool includeIncoming,
    required bool includeOutgoing,
    required bool acceptedOnly,
    int? limitResults,
  }) = _NetworkListPeersRequest;

  factory NetworkListPeersRequest({
    UuidValue? actorId,
    UuidValue? requestId,
    required UuidValue nodeId,
    bool? includeIncoming,
    bool? includeOutgoing,
    bool? acceptedOnly,
    int? limitResults,
  }) {
    return _NetworkListPeersRequest(
      actorId: actorId,
      requestId: requestId,
      nodeId: nodeId,
      includeIncoming: includeIncoming ?? true,
      includeOutgoing: includeOutgoing ?? true,
      acceptedOnly: acceptedOnly ?? true,
      limitResults: limitResults ?? 200,
    );
  }

  factory NetworkListPeersRequest.fromJson(Map<String, dynamic> json) =>
      _$NetworkListPeersRequestFromJson({
        ...json,
        if (!json.containsKey('include_incoming')) 'include_incoming': true,
        if (!json.containsKey('include_outgoing')) 'include_outgoing': true,
        if (!json.containsKey('accepted_only')) 'accepted_only': true,
        if (!json.containsKey('limit_results')) 'limit_results': 200,
      });
}

@freezed
abstract class NetworkListPeersResponse with _$NetworkListPeersResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkListPeersResponse.def({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? error,
    @Default(const []) List<NetworkPeerDescriptor> peers,
  }) = _NetworkListPeersResponse;

  factory NetworkListPeersResponse({
    UuidValue? requestId,
    bool? success,
    String? error,
    List<NetworkPeerDescriptor> peers = const [],
  }) {
    return _NetworkListPeersResponse(
      requestId: requestId,
      success: success ?? true,
      error: error,
      peers: peers,
    );
  }

  factory NetworkListPeersResponse.fromJson(Map<String, dynamic> json) =>
      _$NetworkListPeersResponseFromJson({
        ...json,
        if (!json.containsKey('success')) 'success': true,
      });
}

@freezed
abstract class NetworkPublishHostedServiceRequest
    with _$NetworkPublishHostedServiceRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkPublishHostedServiceRequest.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() required UuidValue nodeId,
    @UuidValueConverter() UuidValue? servicePackageId,
    @UuidValueConverter() required UuidValue serviceId,
    required String serviceName,
    @Default(const []) List<String> servicePackageNames,
    @Default(const []) List<String> endpointRefs,
    @Default(const []) List<String> streamEndpointRefs,
    required String hostId,
    String? hostVersion,
    required String protocolVersion,
    required bool supportsStreamEvents,
  }) = _NetworkPublishHostedServiceRequest;

  factory NetworkPublishHostedServiceRequest({
    UuidValue? actorId,
    UuidValue? requestId,
    required UuidValue nodeId,
    UuidValue? servicePackageId,
    required UuidValue serviceId,
    required String serviceName,
    List<String> servicePackageNames = const [],
    List<String> endpointRefs = const [],
    List<String> streamEndpointRefs = const [],
    required String hostId,
    String? hostVersion,
    required String protocolVersion,
    bool? supportsStreamEvents,
  }) {
    return _NetworkPublishHostedServiceRequest(
      actorId: actorId,
      requestId: requestId,
      nodeId: nodeId,
      servicePackageId: servicePackageId,
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

  factory NetworkPublishHostedServiceRequest.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkPublishHostedServiceRequestFromJson({
    ...json,
    if (!json.containsKey('supports_stream_events'))
      'supports_stream_events': false,
  });
}

@freezed
abstract class NetworkPublishHostedServiceResponse
    with _$NetworkPublishHostedServiceResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkPublishHostedServiceResponse.def({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? error,
    NetworkHostedServiceDescriptor? hostedService,
  }) = _NetworkPublishHostedServiceResponse;

  factory NetworkPublishHostedServiceResponse({
    UuidValue? requestId,
    bool? success,
    String? error,
    NetworkHostedServiceDescriptor? hostedService,
  }) {
    return _NetworkPublishHostedServiceResponse(
      requestId: requestId,
      success: success ?? true,
      error: error,
      hostedService: hostedService,
    );
  }

  factory NetworkPublishHostedServiceResponse.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkPublishHostedServiceResponseFromJson({
    ...json,
    if (!json.containsKey('success')) 'success': true,
  });
}

@freezed
abstract class NetworkListHostedServicesRequest
    with _$NetworkListHostedServicesRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkListHostedServicesRequest.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() required UuidValue nodeId,
  }) = _NetworkListHostedServicesRequest;

  factory NetworkListHostedServicesRequest({
    UuidValue? actorId,
    UuidValue? requestId,
    required UuidValue nodeId,
  }) {
    return _NetworkListHostedServicesRequest(
      actorId: actorId,
      requestId: requestId,
      nodeId: nodeId,
    );
  }

  factory NetworkListHostedServicesRequest.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkListHostedServicesRequestFromJson(json);
}

@freezed
abstract class NetworkListHostedServicesResponse
    with _$NetworkListHostedServicesResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkListHostedServicesResponse.def({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? error,
    @Default(const []) List<NetworkHostedServiceDescriptor> hostedServices,
  }) = _NetworkListHostedServicesResponse;

  factory NetworkListHostedServicesResponse({
    UuidValue? requestId,
    bool? success,
    String? error,
    List<NetworkHostedServiceDescriptor> hostedServices = const [],
  }) {
    return _NetworkListHostedServicesResponse(
      requestId: requestId,
      success: success ?? true,
      error: error,
      hostedServices: hostedServices,
    );
  }

  factory NetworkListHostedServicesResponse.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkListHostedServicesResponseFromJson({
    ...json,
    if (!json.containsKey('success')) 'success': true,
  });
}

@freezed
abstract class NetworkPublishEnvironmentRequest
    with _$NetworkPublishEnvironmentRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkPublishEnvironmentRequest.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() required UuidValue nodeId,
    @UuidValueConverter() required UuidValue environmentId,
    String? environmentKey,
    String? environmentTitle,
    required String role,
    required bool isActive,
    required int priority,
    required String status,
    @Default(const []) List<String> experienceNames,
    @UuidValueConverter() UuidValue? environmentConfigId,
    String? environmentConfigKey,
  }) = _NetworkPublishEnvironmentRequest;

  factory NetworkPublishEnvironmentRequest({
    UuidValue? actorId,
    UuidValue? requestId,
    required UuidValue nodeId,
    required UuidValue environmentId,
    String? environmentKey,
    String? environmentTitle,
    String? role,
    bool? isActive,
    int? priority,
    String? status,
    List<String> experienceNames = const [],
    UuidValue? environmentConfigId,
    String? environmentConfigKey,
  }) {
    return _NetworkPublishEnvironmentRequest(
      actorId: actorId,
      requestId: requestId,
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

  factory NetworkPublishEnvironmentRequest.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkPublishEnvironmentRequestFromJson({
    ...json,
    if (!json.containsKey('role')) 'role': 'replica',
    if (!json.containsKey('is_active')) 'is_active': true,
    if (!json.containsKey('priority')) 'priority': 0,
    if (!json.containsKey('status')) 'status': 'active',
  });
}

@freezed
abstract class NetworkPublishEnvironmentResponse
    with _$NetworkPublishEnvironmentResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkPublishEnvironmentResponse.def({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? error,
    NetworkEnvironmentDescriptor? environment,
  }) = _NetworkPublishEnvironmentResponse;

  factory NetworkPublishEnvironmentResponse({
    UuidValue? requestId,
    bool? success,
    String? error,
    NetworkEnvironmentDescriptor? environment,
  }) {
    return _NetworkPublishEnvironmentResponse(
      requestId: requestId,
      success: success ?? true,
      error: error,
      environment: environment,
    );
  }

  factory NetworkPublishEnvironmentResponse.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkPublishEnvironmentResponseFromJson({
    ...json,
    if (!json.containsKey('success')) 'success': true,
  });
}

@freezed
abstract class NetworkListEnvironmentsRequest
    with _$NetworkListEnvironmentsRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkListEnvironmentsRequest.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() UuidValue? nodeId,
    required bool activeOnly,
  }) = _NetworkListEnvironmentsRequest;

  factory NetworkListEnvironmentsRequest({
    UuidValue? actorId,
    UuidValue? requestId,
    UuidValue? nodeId,
    bool? activeOnly,
  }) {
    return _NetworkListEnvironmentsRequest(
      actorId: actorId,
      requestId: requestId,
      nodeId: nodeId,
      activeOnly: activeOnly ?? true,
    );
  }

  factory NetworkListEnvironmentsRequest.fromJson(Map<String, dynamic> json) =>
      _$NetworkListEnvironmentsRequestFromJson({
        ...json,
        if (!json.containsKey('active_only')) 'active_only': true,
      });
}

@freezed
abstract class NetworkListEnvironmentsResponse
    with _$NetworkListEnvironmentsResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkListEnvironmentsResponse.def({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? error,
    @Default(const []) List<NetworkEnvironmentDescriptor> environments,
  }) = _NetworkListEnvironmentsResponse;

  factory NetworkListEnvironmentsResponse({
    UuidValue? requestId,
    bool? success,
    String? error,
    List<NetworkEnvironmentDescriptor> environments = const [],
  }) {
    return _NetworkListEnvironmentsResponse(
      requestId: requestId,
      success: success ?? true,
      error: error,
      environments: environments,
    );
  }

  factory NetworkListEnvironmentsResponse.fromJson(Map<String, dynamic> json) =>
      _$NetworkListEnvironmentsResponseFromJson({
        ...json,
        if (!json.containsKey('success')) 'success': true,
      });
}

@freezed
abstract class NetworkResolveHostedServiceRoutesRequest
    with _$NetworkResolveHostedServiceRoutesRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkResolveHostedServiceRoutesRequest.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() required UuidValue consumerNodeId,
    String? serviceName,
    String? endpointRef,
    required bool acceptedPeersOnly,
  }) = _NetworkResolveHostedServiceRoutesRequest;

  factory NetworkResolveHostedServiceRoutesRequest({
    UuidValue? actorId,
    UuidValue? requestId,
    required UuidValue consumerNodeId,
    String? serviceName,
    String? endpointRef,
    bool? acceptedPeersOnly,
  }) {
    return _NetworkResolveHostedServiceRoutesRequest(
      actorId: actorId,
      requestId: requestId,
      consumerNodeId: consumerNodeId,
      serviceName: serviceName,
      endpointRef: endpointRef,
      acceptedPeersOnly: acceptedPeersOnly ?? true,
    );
  }

  factory NetworkResolveHostedServiceRoutesRequest.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkResolveHostedServiceRoutesRequestFromJson({
    ...json,
    if (!json.containsKey('accepted_peers_only')) 'accepted_peers_only': true,
  });
}

@freezed
abstract class NetworkResolveHostedServiceRoutesResponse
    with _$NetworkResolveHostedServiceRoutesResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkResolveHostedServiceRoutesResponse.def({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? error,
    @Default(const []) List<NetworkResolvedHostedServiceRoute> routes,
  }) = _NetworkResolveHostedServiceRoutesResponse;

  factory NetworkResolveHostedServiceRoutesResponse({
    UuidValue? requestId,
    bool? success,
    String? error,
    List<NetworkResolvedHostedServiceRoute> routes = const [],
  }) {
    return _NetworkResolveHostedServiceRoutesResponse(
      requestId: requestId,
      success: success ?? true,
      error: error,
      routes: routes,
    );
  }

  factory NetworkResolveHostedServiceRoutesResponse.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkResolveHostedServiceRoutesResponseFromJson({
    ...json,
    if (!json.containsKey('success')) 'success': true,
  });
}

@freezed
abstract class NetworkDiscoverTerritoryRequest
    with _$NetworkDiscoverTerritoryRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkDiscoverTerritoryRequest.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? requestId,
    @UuidValueConverter() UuidValue? nodeId,
    required bool includePeers,
    required bool includeHostedServices,
    required bool includeEnvironments,
    required bool activeEnvironmentsOnly,
    required bool acceptedPeersOnly,
    int? limitNodes,
  }) = _NetworkDiscoverTerritoryRequest;

  factory NetworkDiscoverTerritoryRequest({
    UuidValue? actorId,
    UuidValue? requestId,
    UuidValue? nodeId,
    bool? includePeers,
    bool? includeHostedServices,
    bool? includeEnvironments,
    bool? activeEnvironmentsOnly,
    bool? acceptedPeersOnly,
    int? limitNodes,
  }) {
    return _NetworkDiscoverTerritoryRequest(
      actorId: actorId,
      requestId: requestId,
      nodeId: nodeId,
      includePeers: includePeers ?? true,
      includeHostedServices: includeHostedServices ?? true,
      includeEnvironments: includeEnvironments ?? true,
      activeEnvironmentsOnly: activeEnvironmentsOnly ?? true,
      acceptedPeersOnly: acceptedPeersOnly ?? true,
      limitNodes: limitNodes ?? 200,
    );
  }

  factory NetworkDiscoverTerritoryRequest.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkDiscoverTerritoryRequestFromJson({
    ...json,
    if (!json.containsKey('include_peers')) 'include_peers': true,
    if (!json.containsKey('include_hosted_services'))
      'include_hosted_services': true,
    if (!json.containsKey('include_environments')) 'include_environments': true,
    if (!json.containsKey('active_environments_only'))
      'active_environments_only': true,
    if (!json.containsKey('accepted_peers_only')) 'accepted_peers_only': true,
    if (!json.containsKey('limit_nodes')) 'limit_nodes': 200,
  });
}

@freezed
abstract class NetworkDiscoverTerritoryResponse
    with _$NetworkDiscoverTerritoryResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkDiscoverTerritoryResponse.def({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? error,
    @Default(const []) List<NetworkTerritoryNodeDescriptor> nodes,
    String? summary,
  }) = _NetworkDiscoverTerritoryResponse;

  factory NetworkDiscoverTerritoryResponse({
    UuidValue? requestId,
    bool? success,
    String? error,
    List<NetworkTerritoryNodeDescriptor> nodes = const [],
    String? summary,
  }) {
    return _NetworkDiscoverTerritoryResponse(
      requestId: requestId,
      success: success ?? true,
      error: error,
      nodes: nodes,
      summary: summary,
    );
  }

  factory NetworkDiscoverTerritoryResponse.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkDiscoverTerritoryResponseFromJson({
    ...json,
    if (!json.containsKey('success')) 'success': true,
  });
}

@freezed
abstract class NetworkDiscoverExperienceTerritoryRequest
    with _$NetworkDiscoverExperienceTerritoryRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkDiscoverExperienceTerritoryRequest.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? requestId,
    required String experienceName,
    @Default(const []) List<String> requiredServicePackageNames,
    @Default(const []) List<String> requiredEndpointRefs,
    @UuidValueConverter() UuidValue? consumerNodeId,
    required bool activeEnvironmentsOnly,
    required bool acceptedPeersOnly,
    required bool includeRouteHints,
    required bool requireAccessEvidence,
    @Default(const []) List<String> accessEvidenceRefs,
    int? limitEntries,
  }) = _NetworkDiscoverExperienceTerritoryRequest;

  factory NetworkDiscoverExperienceTerritoryRequest({
    UuidValue? actorId,
    UuidValue? requestId,
    required String experienceName,
    List<String> requiredServicePackageNames = const [],
    List<String> requiredEndpointRefs = const [],
    UuidValue? consumerNodeId,
    bool? activeEnvironmentsOnly,
    bool? acceptedPeersOnly,
    bool? includeRouteHints,
    bool? requireAccessEvidence,
    List<String> accessEvidenceRefs = const [],
    int? limitEntries,
  }) {
    return _NetworkDiscoverExperienceTerritoryRequest(
      actorId: actorId,
      requestId: requestId,
      experienceName: experienceName,
      requiredServicePackageNames: requiredServicePackageNames,
      requiredEndpointRefs: requiredEndpointRefs,
      consumerNodeId: consumerNodeId,
      activeEnvironmentsOnly: activeEnvironmentsOnly ?? true,
      acceptedPeersOnly: acceptedPeersOnly ?? true,
      includeRouteHints: includeRouteHints ?? true,
      requireAccessEvidence: requireAccessEvidence ?? false,
      accessEvidenceRefs: accessEvidenceRefs,
      limitEntries: limitEntries ?? 200,
    );
  }

  factory NetworkDiscoverExperienceTerritoryRequest.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkDiscoverExperienceTerritoryRequestFromJson({
    ...json,
    if (!json.containsKey('active_environments_only'))
      'active_environments_only': true,
    if (!json.containsKey('accepted_peers_only')) 'accepted_peers_only': true,
    if (!json.containsKey('include_route_hints')) 'include_route_hints': true,
    if (!json.containsKey('require_access_evidence'))
      'require_access_evidence': false,
    if (!json.containsKey('limit_entries')) 'limit_entries': 200,
  });
}

@freezed
abstract class NetworkDiscoverExperienceTerritoryResponse
    with _$NetworkDiscoverExperienceTerritoryResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkDiscoverExperienceTerritoryResponse.def({
    @UuidValueConverter() UuidValue? requestId,
    required bool success,
    String? error,
    String? experienceName,
    @Default(const []) List<NetworkExperienceTerritoryEntry> entries,
    String? summary,
  }) = _NetworkDiscoverExperienceTerritoryResponse;

  factory NetworkDiscoverExperienceTerritoryResponse({
    UuidValue? requestId,
    bool? success,
    String? error,
    String? experienceName,
    List<NetworkExperienceTerritoryEntry> entries = const [],
    String? summary,
  }) {
    return _NetworkDiscoverExperienceTerritoryResponse(
      requestId: requestId,
      success: success ?? true,
      error: error,
      experienceName: experienceName,
      entries: entries,
      summary: summary,
    );
  }

  factory NetworkDiscoverExperienceTerritoryResponse.fromJson(
    Map<String, dynamic> json,
  ) => _$NetworkDiscoverExperienceTerritoryResponseFromJson({
    ...json,
    if (!json.containsKey('success')) 'success': true,
  });
}
