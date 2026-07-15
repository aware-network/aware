// GENERATED CODE - DO NOT MODIFY BY HAND
// Thin typed API wrapper over package:aware_api/aware_api.dart.

import 'dart:async';

import 'package:aware_api/aware_api.dart';

import 'bindings.dart';
import 'environment/environment.dart' as environmentEnvironment_54;

class EnvironmentActorAdmissionCapabilityClient {
  EnvironmentActorAdmissionCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Admit an actor to an EnvironmentProfile through committed ActorConfig eligibility and Identity role assignment.
  Future<environmentEnvironment_54.AdmitEnvironmentActorResponse> admitActor(
    environmentEnvironment_54.AdmitEnvironmentActorRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.AdmitEnvironmentActorResponse
    >(
      endpointRef: environmentActorAdmissionAdmitActorEndpointRef,
      discriminant: environmentActorAdmissionAdmitActorDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54.AdmitEnvironmentActorResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: environmentActorAdmissionAdmitActorEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class EnvironmentCapabilitiesCapabilityClient {
  EnvironmentCapabilitiesCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Read Environment runtime capability advertisement through the canonical Environment API boundary.
  Future<environmentEnvironment_54.FetchCapabilitiesResponse> fetchCapabilities(
    environmentEnvironment_54.FetchCapabilitiesRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client
        .invokeApiEndpoint<environmentEnvironment_54.FetchCapabilitiesResponse>(
          endpointRef: environmentCapabilitiesFetchCapabilitiesEndpointRef,
          discriminant: environmentCapabilitiesFetchCapabilitiesDiscriminant,
          requestPayload: request.toJson(),
          decodeResponse: (payload) =>
              environmentEnvironment_54.FetchCapabilitiesResponse.fromJson(
                _requireJsonMap(
                  payload,
                  endpointRef:
                      environmentCapabilitiesFetchCapabilitiesEndpointRef,
                ),
              ),
          timeout: timeout,
        );
  }
}

class EnvironmentCommittedProjectionDtoCapabilityClient {
  EnvironmentCommittedProjectionDtoCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Materialize a committed projection root as a typed ontology DTO snapshot through an explicit commit locator.
  Future<environmentEnvironment_54.MaterializeCommittedProjectionDtoResponse>
  materializeCommittedProjectionDto(
    environmentEnvironment_54.MaterializeCommittedProjectionDtoRequest
    request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.MaterializeCommittedProjectionDtoResponse
    >(
      endpointRef:
          environmentCommittedProjectionDtoMaterializeCommittedProjectionDtoEndpointRef,
      discriminant:
          environmentCommittedProjectionDtoMaterializeCommittedProjectionDtoDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54
              .MaterializeCommittedProjectionDtoResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  environmentCommittedProjectionDtoMaterializeCommittedProjectionDtoEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class EnvironmentDescribeCapabilityClient {
  EnvironmentDescribeCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// Describe one provisioned Environment instance and its current boot/lane pointers.
  Future<environmentEnvironment_54.DescribeEnvironmentResponse>
  describeEnvironment(
    environmentEnvironment_54.DescribeEnvironmentRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.DescribeEnvironmentResponse
    >(
      endpointRef: environmentDescribeDescribeEnvironmentEndpointRef,
      discriminant: environmentDescribeDescribeEnvironmentDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54.DescribeEnvironmentResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: environmentDescribeDescribeEnvironmentEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class EnvironmentDescribeConfigCapabilityClient {
  EnvironmentDescribeConfigCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Describe the hosted EnvironmentConfig through the canonical Environment API boundary.
  Future<environmentEnvironment_54.DescribeEnvironmentConfigResponse>
  describeEnvironmentConfig(
    environmentEnvironment_54.DescribeEnvironmentConfigRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.DescribeEnvironmentConfigResponse
    >(
      endpointRef:
          environmentDescribeConfigDescribeEnvironmentConfigEndpointRef,
      discriminant:
          environmentDescribeConfigDescribeEnvironmentConfigDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54.DescribeEnvironmentConfigResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  environmentDescribeConfigDescribeEnvironmentConfigEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class EnvironmentFunctionCallCapabilityClient {
  EnvironmentFunctionCallCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Invoke one graph function through the canonical commit-backed Environment runtime boundary.
  Future<environmentEnvironment_54.InvokeFunctionResponse> invokeFunction(
    environmentEnvironment_54.InvokeFunctionRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client
        .invokeApiEndpoint<environmentEnvironment_54.InvokeFunctionResponse>(
          endpointRef: environmentFunctionCallInvokeFunctionEndpointRef,
          discriminant: environmentFunctionCallInvokeFunctionDiscriminant,
          requestPayload: request.toJson(),
          decodeResponse: (payload) =>
              environmentEnvironment_54.InvokeFunctionResponse.fromJson(
                _requireJsonMap(
                  payload,
                  endpointRef: environmentFunctionCallInvokeFunctionEndpointRef,
                ),
              ),
          timeout: timeout,
        );
  }
}

class EnvironmentLaneHeadCapabilityClient {
  EnvironmentLaneHeadCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// Read the current head commit for one explicit Environment lane key.
  Future<environmentEnvironment_54.GetLaneHeadResponse> getLaneHead(
    environmentEnvironment_54.GetLaneHeadRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client
        .invokeApiEndpoint<environmentEnvironment_54.GetLaneHeadResponse>(
          endpointRef: environmentLaneHeadGetLaneHeadEndpointRef,
          discriminant: environmentLaneHeadGetLaneHeadDiscriminant,
          requestPayload: request.toJson(),
          decodeResponse: (payload) =>
              environmentEnvironment_54.GetLaneHeadResponse.fromJson(
                _requireJsonMap(
                  payload,
                  endpointRef: environmentLaneHeadGetLaneHeadEndpointRef,
                ),
              ),
          timeout: timeout,
        );
  }
}

class EnvironmentNavigationCapabilityClient {
  EnvironmentNavigationCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Create an EnvironmentSession-owned navigation context after accepted session join.
  Future<environmentEnvironment_54.CreateEnvironmentNavigationContextResponse>
  createNavigationContext(
    environmentEnvironment_54.CreateEnvironmentNavigationContextRequest
    request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.CreateEnvironmentNavigationContextResponse
    >(
      endpointRef: environmentNavigationCreateNavigationContextEndpointRef,
      discriminant: environmentNavigationCreateNavigationContextDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54
              .CreateEnvironmentNavigationContextResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  environmentNavigationCreateNavigationContextEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// Describe one Environment navigation context without mutating Attention or Experience state.
  Future<environmentEnvironment_54.DescribeEnvironmentNavigationContextResponse>
  describeNavigationContext(
    environmentEnvironment_54.DescribeEnvironmentNavigationContextRequest
    request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.DescribeEnvironmentNavigationContextResponse
    >(
      endpointRef: environmentNavigationDescribeNavigationContextEndpointRef,
      discriminant: environmentNavigationDescribeNavigationContextDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54
              .DescribeEnvironmentNavigationContextResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  environmentNavigationDescribeNavigationContextEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// List Environment navigation contexts owned by one EnvironmentSession.
  Future<environmentEnvironment_54.ListEnvironmentNavigationContextsResponse>
  listNavigationContexts(
    environmentEnvironment_54.ListEnvironmentNavigationContextsRequest
    request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.ListEnvironmentNavigationContextsResponse
    >(
      endpointRef: environmentNavigationListNavigationContextsEndpointRef,
      discriminant: environmentNavigationListNavigationContextsDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54
              .ListEnvironmentNavigationContextsResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  environmentNavigationListNavigationContextsEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// Select the Process/Thread target for one Environment navigation context.
  Future<environmentEnvironment_54.SelectEnvironmentNavigationTargetResponse>
  selectNavigationTarget(
    environmentEnvironment_54.SelectEnvironmentNavigationTargetRequest
    request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.SelectEnvironmentNavigationTargetResponse
    >(
      endpointRef: environmentNavigationSelectNavigationTargetEndpointRef,
      discriminant: environmentNavigationSelectNavigationTargetDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54
              .SelectEnvironmentNavigationTargetResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  environmentNavigationSelectNavigationTargetEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class EnvironmentObjectInstanceGraphCommitCapabilityClient {
  EnvironmentObjectInstanceGraphCommitCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Read one ObjectInstanceGraphCommit by id through the Environment service boundary.
  Future<environmentEnvironment_54.GetObjectInstanceGraphCommitResponse>
  getObjectInstanceGraphCommit(
    environmentEnvironment_54.GetObjectInstanceGraphCommitRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.GetObjectInstanceGraphCommitResponse
    >(
      endpointRef:
          environmentObjectInstanceGraphCommitGetObjectInstanceGraphCommitEndpointRef,
      discriminant:
          environmentObjectInstanceGraphCommitGetObjectInstanceGraphCommitDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54
              .GetObjectInstanceGraphCommitResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  environmentObjectInstanceGraphCommitGetObjectInstanceGraphCommitEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class EnvironmentOntologyCapabilityClient {
  EnvironmentOntologyCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// Attach one Ontology authority to a stable Environment through the canonical Environment API boundary.
  Future<environmentEnvironment_54.AttachEnvironmentOntologyResponse>
  attachEnvironmentOntology(
    environmentEnvironment_54.AttachEnvironmentOntologyRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.AttachEnvironmentOntologyResponse
    >(
      endpointRef: environmentOntologyAttachEnvironmentOntologyEndpointRef,
      discriminant: environmentOntologyAttachEnvironmentOntologyDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54.AttachEnvironmentOntologyResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  environmentOntologyAttachEnvironmentOntologyEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// Resolve and register one Ontology-owned runtime artifact set for a running Environment.
  Future<environmentEnvironment_54.EnsureEnvironmentOntologyRuntimeResponse>
  ensureEnvironmentOntologyRuntime(
    environmentEnvironment_54.EnsureEnvironmentOntologyRuntimeRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.EnsureEnvironmentOntologyRuntimeResponse
    >(
      endpointRef:
          environmentOntologyEnsureEnvironmentOntologyRuntimeEndpointRef,
      discriminant:
          environmentOntologyEnsureEnvironmentOntologyRuntimeDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54
              .EnsureEnvironmentOntologyRuntimeResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  environmentOntologyEnsureEnvironmentOntologyRuntimeEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// List Environment-owned Ontology membership pointers without expanding Ontology-owned OIGI inventory.
  Future<environmentEnvironment_54.ListEnvironmentOntologiesResponse>
  listEnvironmentOntologies(
    environmentEnvironment_54.ListEnvironmentOntologiesRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.ListEnvironmentOntologiesResponse
    >(
      endpointRef: environmentOntologyListEnvironmentOntologiesEndpointRef,
      discriminant: environmentOntologyListEnvironmentOntologiesDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54.ListEnvironmentOntologiesResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  environmentOntologyListEnvironmentOntologiesEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class EnvironmentProfileCapabilityClient {
  EnvironmentProfileCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// Provision concrete Environment Process/Thread topology from an installed EnvironmentProfile seed.
  Future<environmentEnvironment_54.ProvisionEnvironmentProfileResponse>
  provisionEnvironmentProfile(
    environmentEnvironment_54.ProvisionEnvironmentProfileRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.ProvisionEnvironmentProfileResponse
    >(
      endpointRef: environmentProfileProvisionEnvironmentProfileEndpointRef,
      discriminant: environmentProfileProvisionEnvironmentProfileDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54
              .ProvisionEnvironmentProfileResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  environmentProfileProvisionEnvironmentProfileEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// Install or update Environment-owned profile topology through the Environment API boundary.
  Future<environmentEnvironment_54.UpsertEnvironmentProfileResponse>
  upsertEnvironmentProfile(
    environmentEnvironment_54.UpsertEnvironmentProfileRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.UpsertEnvironmentProfileResponse
    >(
      endpointRef: environmentProfileUpsertEnvironmentProfileEndpointRef,
      discriminant: environmentProfileUpsertEnvironmentProfileDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54.UpsertEnvironmentProfileResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  environmentProfileUpsertEnvironmentProfileEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class EnvironmentReadyCapabilityClient {
  EnvironmentReadyCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// Ensure the Environment runtime is ready to execute commit-backed graph operations.
  Future<environmentEnvironment_54.EnsureReadyResponse> ensureReady(
    environmentEnvironment_54.EnsureReadyRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client
        .invokeApiEndpoint<environmentEnvironment_54.EnsureReadyResponse>(
          endpointRef: environmentReadyEnsureReadyEndpointRef,
          discriminant: environmentReadyEnsureReadyDiscriminant,
          requestPayload: request.toJson(),
          decodeResponse: (payload) =>
              environmentEnvironment_54.EnsureReadyResponse.fromJson(
                _requireJsonMap(
                  payload,
                  endpointRef: environmentReadyEnsureReadyEndpointRef,
                ),
              ),
          timeout: timeout,
        );
  }
}

class EnvironmentRuntimeRefCapabilityClient {
  EnvironmentRuntimeRefCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Resolve hosted runtime OCG/function/class references for remote graph invocation.
  Future<environmentEnvironment_54.ResolveRuntimeRefsResponse>
  resolveRuntimeRefs(
    environmentEnvironment_54.ResolveRuntimeRefsRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.ResolveRuntimeRefsResponse
    >(
      endpointRef: environmentRuntimeRefResolveRuntimeRefsEndpointRef,
      discriminant: environmentRuntimeRefResolveRuntimeRefsDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54.ResolveRuntimeRefsResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: environmentRuntimeRefResolveRuntimeRefsEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class EnvironmentServiceRoutesCapabilityClient {
  EnvironmentServiceRoutesCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Configure Environment-hosted service API dependency routes through the canonical Environment API boundary.
  Future<environmentEnvironment_54.ConfigureServiceApiDependencyRoutesResponse>
  configureServiceApiDependencyRoutes(
    environmentEnvironment_54.ConfigureServiceApiDependencyRoutesRequest
    request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.ConfigureServiceApiDependencyRoutesResponse
    >(
      endpointRef:
          environmentServiceRoutesConfigureServiceApiDependencyRoutesEndpointRef,
      discriminant:
          environmentServiceRoutesConfigureServiceApiDependencyRoutesDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54
              .ConfigureServiceApiDependencyRoutesResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  environmentServiceRoutesConfigureServiceApiDependencyRoutesEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class EnvironmentSessionCapabilityClient {
  EnvironmentSessionCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// Describe a shared EnvironmentSession without resolving navigation or Attention.
  Future<environmentEnvironment_54.DescribeEnvironmentSessionResponse>
  describeSession(
    environmentEnvironment_54.DescribeEnvironmentSessionRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.DescribeEnvironmentSessionResponse
    >(
      endpointRef: environmentSessionDescribeSessionEndpointRef,
      discriminant: environmentSessionDescribeSessionDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54.DescribeEnvironmentSessionResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: environmentSessionDescribeSessionEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// Join a shared EnvironmentSession after accepted Environment admission.
  Future<environmentEnvironment_54.JoinEnvironmentSessionResponse> joinSession(
    environmentEnvironment_54.JoinEnvironmentSessionRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.JoinEnvironmentSessionResponse
    >(
      endpointRef: environmentSessionJoinSessionEndpointRef,
      discriminant: environmentSessionJoinSessionDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54.JoinEnvironmentSessionResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: environmentSessionJoinSessionEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// Commit one EnvironmentSession-owned portal to an existing AttentionSession authority.
  Future<environmentEnvironment_54.MountEnvironmentSessionAttentionResponse>
  mountAttentionSession(
    environmentEnvironment_54.MountEnvironmentSessionAttentionRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.MountEnvironmentSessionAttentionResponse
    >(
      endpointRef: environmentSessionMountAttentionSessionEndpointRef,
      discriminant: environmentSessionMountAttentionSessionDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54
              .MountEnvironmentSessionAttentionResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: environmentSessionMountAttentionSessionEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// Resolve Environment session Thread/Layout pins against Attention session and transition validation.
  Future<environmentEnvironment_54.ResolveEnvironmentSessionAttentionResponse>
  resolveAttention(
    environmentEnvironment_54.ResolveEnvironmentSessionAttentionRequest
    request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.ResolveEnvironmentSessionAttentionResponse
    >(
      endpointRef: environmentSessionResolveAttentionEndpointRef,
      discriminant: environmentSessionResolveAttentionDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54
              .ResolveEnvironmentSessionAttentionResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: environmentSessionResolveAttentionEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// Start a shared EnvironmentSession after accepted Environment admission.
  Future<environmentEnvironment_54.StartEnvironmentSessionResponse>
  startSession(
    environmentEnvironment_54.StartEnvironmentSessionRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.StartEnvironmentSessionResponse
    >(
      endpointRef: environmentSessionStartSessionEndpointRef,
      discriminant: environmentSessionStartSessionDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54.StartEnvironmentSessionResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: environmentSessionStartSessionEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class EnvironmentStatusCapabilityClient {
  EnvironmentStatusCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// Read the canonical Environment status envelope with explicit authority blocks.
  Future<environmentEnvironment_54.DescribeEnvironmentStatusResponse>
  describeEnvironmentStatus(
    environmentEnvironment_54.DescribeEnvironmentStatusRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.DescribeEnvironmentStatusResponse
    >(
      endpointRef: environmentStatusDescribeEnvironmentStatusEndpointRef,
      discriminant: environmentStatusDescribeEnvironmentStatusDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54.DescribeEnvironmentStatusResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  environmentStatusDescribeEnvironmentStatusEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class EnvironmentTopologyCapabilityClient {
  EnvironmentTopologyCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// Describe the process/thread topology and attached OIG lanes for an Environment.
  Future<environmentEnvironment_54.DescribeEnvironmentTopologyResponse>
  describeEnvironmentTopology(
    environmentEnvironment_54.DescribeEnvironmentTopologyRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      environmentEnvironment_54.DescribeEnvironmentTopologyResponse
    >(
      endpointRef: environmentTopologyDescribeEnvironmentTopologyEndpointRef,
      discriminant: environmentTopologyDescribeEnvironmentTopologyDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          environmentEnvironment_54
              .DescribeEnvironmentTopologyResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  environmentTopologyDescribeEnvironmentTopologyEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class EnvironmentApiClient {
  EnvironmentApiClient(AwareApiClient client)
    : actorAdmission = EnvironmentActorAdmissionCapabilityClient(client),
      capabilities = EnvironmentCapabilitiesCapabilityClient(client),
      committedProjectionDto =
          EnvironmentCommittedProjectionDtoCapabilityClient(client),
      describe = EnvironmentDescribeCapabilityClient(client),
      describeConfig = EnvironmentDescribeConfigCapabilityClient(client),
      functionCall = EnvironmentFunctionCallCapabilityClient(client),
      laneHead = EnvironmentLaneHeadCapabilityClient(client),
      navigation = EnvironmentNavigationCapabilityClient(client),
      objectInstanceGraphCommit =
          EnvironmentObjectInstanceGraphCommitCapabilityClient(client),
      ontology = EnvironmentOntologyCapabilityClient(client),
      profile = EnvironmentProfileCapabilityClient(client),
      ready = EnvironmentReadyCapabilityClient(client),
      runtimeRef = EnvironmentRuntimeRefCapabilityClient(client),
      serviceRoutes = EnvironmentServiceRoutesCapabilityClient(client),
      session = EnvironmentSessionCapabilityClient(client),
      status = EnvironmentStatusCapabilityClient(client),
      topology = EnvironmentTopologyCapabilityClient(client);

  final EnvironmentActorAdmissionCapabilityClient actorAdmission;
  final EnvironmentCapabilitiesCapabilityClient capabilities;
  final EnvironmentCommittedProjectionDtoCapabilityClient
  committedProjectionDto;
  final EnvironmentDescribeCapabilityClient describe;
  final EnvironmentDescribeConfigCapabilityClient describeConfig;
  final EnvironmentFunctionCallCapabilityClient functionCall;
  final EnvironmentLaneHeadCapabilityClient laneHead;
  final EnvironmentNavigationCapabilityClient navigation;
  final EnvironmentObjectInstanceGraphCommitCapabilityClient
  objectInstanceGraphCommit;
  final EnvironmentOntologyCapabilityClient ontology;
  final EnvironmentProfileCapabilityClient profile;
  final EnvironmentReadyCapabilityClient ready;
  final EnvironmentRuntimeRefCapabilityClient runtimeRef;
  final EnvironmentServiceRoutesCapabilityClient serviceRoutes;
  final EnvironmentSessionCapabilityClient session;
  final EnvironmentStatusCapabilityClient status;
  final EnvironmentTopologyCapabilityClient topology;
}

class AwareEnvironmentServiceApiClient {
  AwareEnvironmentServiceApiClient(AwareApiClient client)
    : environment = EnvironmentApiClient(client);

  final Map<String, Object?> interfaceSpecPayload = apiInterfaceSpecPayload;
  final Map<String, Object?> invocationManifestPayload =
      apiInvocationManifestPayload;
  final EnvironmentApiClient environment;
}

Map<String, dynamic> _requireJsonMap(
  Object? payload, {
  required String endpointRef,
}) {
  if (payload is Map<String, dynamic>) {
    return payload;
  }
  if (payload is Map) {
    return Map<String, dynamic>.from(payload);
  }
  throw StateError(
    'Expected API payload for $endpointRef to decode to a JSON object.',
  );
}
