// GENERATED CODE - DO NOT MODIFY BY HAND
// Thin typed API wrapper over package:aware_api/aware_api.dart.

import 'dart:async';

import 'package:aware_api/aware_api.dart';

import 'bindings.dart';
import 'comms/models/control_plane.dart' as commsModelsControlPlane_56;

typedef InterfaceStreamInterfaceApiStreamInterfaceApiStreamEvent =
    commsModelsControlPlane_56.InterfaceControlPlaneNotification;
typedef InterfaceWatchInterfaceStateWatchInterfaceStateStreamEvent =
    commsModelsControlPlane_56.InterfaceStateNotification;

class InterfaceActivateInterfaceRuntimeFocusCapabilityClient {
  InterfaceActivateInterfaceRuntimeFocusCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Activate an Interface runtime section representation or focus target.
  Future<commsModelsControlPlane_56.InterfaceActivateRuntimeFocusResponse>
  activateInterfaceRuntimeFocus(
    commsModelsControlPlane_56.InterfaceActivateRuntimeFocusRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceActivateRuntimeFocusResponse
    >(
      endpointRef:
          interfaceActivateInterfaceRuntimeFocusActivateInterfaceRuntimeFocusEndpointRef,
      discriminant:
          interfaceActivateInterfaceRuntimeFocusActivateInterfaceRuntimeFocusDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56
              .InterfaceActivateRuntimeFocusResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceActivateInterfaceRuntimeFocusActivateInterfaceRuntimeFocusEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceAdmitEnvironmentActorCapabilityClient {
  InterfaceAdmitEnvironmentActorCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Admit the current Interface actor to an Environment/Profile before Experience lens resolution.
  Future<commsModelsControlPlane_56.InterfaceAdmitEnvironmentActorResponse>
  admitEnvironmentActor(
    commsModelsControlPlane_56.InterfaceAdmitEnvironmentActorRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceAdmitEnvironmentActorResponse
    >(
      endpointRef:
          interfaceAdmitEnvironmentActorAdmitEnvironmentActorEndpointRef,
      discriminant:
          interfaceAdmitEnvironmentActorAdmitEnvironmentActorDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56
              .InterfaceAdmitEnvironmentActorResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceAdmitEnvironmentActorAdmitEnvironmentActorEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceAdmitInterfaceCapabilityClient {
  InterfaceAdmitInterfaceCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Admit or resume one renderer/agent namespace into the Interface service runtime.
  Future<commsModelsControlPlane_56.NamespaceEnsureResponse> admitInterface(
    commsModelsControlPlane_56.NamespaceEnsureRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client
        .invokeApiEndpoint<commsModelsControlPlane_56.NamespaceEnsureResponse>(
          endpointRef: interfaceAdmitInterfaceAdmitInterfaceEndpointRef,
          discriminant: interfaceAdmitInterfaceAdmitInterfaceDiscriminant,
          requestPayload: request.toJson(),
          decodeResponse: (payload) =>
              commsModelsControlPlane_56.NamespaceEnsureResponse.fromJson(
                _requireJsonMap(
                  payload,
                  endpointRef: interfaceAdmitInterfaceAdmitInterfaceEndpointRef,
                ),
              ),
          timeout: timeout,
        );
  }
}

class InterfaceApplyAttentionLayoutTopologyTransitionCapabilityClient {
  InterfaceApplyAttentionLayoutTopologyTransitionCapabilityClient(
    AwareApiClient client,
  ) : _client = client;

  final AwareApiClient _client;

  /// Commit one complete active-membership/order vector through Interface Host and Attention authority.
  Future<
    commsModelsControlPlane_56.InterfaceApplyAttentionLayoutTopologyTransitionResponse
  >
  applyAttentionLayoutTopologyTransition(
    commsModelsControlPlane_56.InterfaceApplyAttentionLayoutTopologyTransitionRequest
    request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceApplyAttentionLayoutTopologyTransitionResponse
    >(
      endpointRef:
          interfaceApplyAttentionLayoutTopologyTransitionApplyAttentionLayoutTopologyTransitionEndpointRef,
      discriminant:
          interfaceApplyAttentionLayoutTopologyTransitionApplyAttentionLayoutTopologyTransitionDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56
              .InterfaceApplyAttentionLayoutTopologyTransitionResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceApplyAttentionLayoutTopologyTransitionApplyAttentionLayoutTopologyTransitionEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceApplyAttentionLayoutTransitionCapabilityClient {
  InterfaceApplyAttentionLayoutTransitionCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Commit one complete shared-layout vector through Interface Host and Attention authority.
  Future<
    commsModelsControlPlane_56.InterfaceApplyAttentionLayoutTransitionResponse
  >
  applyAttentionLayoutTransition(
    commsModelsControlPlane_56.InterfaceApplyAttentionLayoutTransitionRequest
    request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceApplyAttentionLayoutTransitionResponse
    >(
      endpointRef:
          interfaceApplyAttentionLayoutTransitionApplyAttentionLayoutTransitionEndpointRef,
      discriminant:
          interfaceApplyAttentionLayoutTransitionApplyAttentionLayoutTransitionDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56
              .InterfaceApplyAttentionLayoutTransitionResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceApplyAttentionLayoutTransitionApplyAttentionLayoutTransitionEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceDescribeInterfaceSessionCapabilityClient {
  InterfaceDescribeInterfaceSessionCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Read one committed InterfaceSession and its Interface-owned ExperienceSession portal rows.
  Future<commsModelsControlPlane_56.InterfaceSessionDescribeResponse>
  describeInterfaceSession(
    commsModelsControlPlane_56.InterfaceSessionDescribeRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceSessionDescribeResponse
    >(
      endpointRef:
          interfaceDescribeInterfaceSessionDescribeInterfaceSessionEndpointRef,
      discriminant:
          interfaceDescribeInterfaceSessionDescribeInterfaceSessionDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56.InterfaceSessionDescribeResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceDescribeInterfaceSessionDescribeInterfaceSessionEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceEnterAppScreenCapabilityClient {
  InterfaceEnterAppScreenCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Enter one committed AppPackage screen through Interface Host and Experience layout activation.
  Future<commsModelsControlPlane_56.InterfaceEnterAppScreenResponse>
  enterAppScreen(
    commsModelsControlPlane_56.InterfaceEnterAppScreenRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceEnterAppScreenResponse
    >(
      endpointRef: interfaceEnterAppScreenEnterAppScreenEndpointRef,
      discriminant: interfaceEnterAppScreenEnterAppScreenDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56.InterfaceEnterAppScreenResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: interfaceEnterAppScreenEnterAppScreenEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceEnterEnvironmentCapabilityClient {
  InterfaceEnterEnvironmentCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Enter or resume an Environment shell context without Interface-owned Process/Thread defaults.
  Future<commsModelsControlPlane_56.InterfaceEnterEnvironmentResponse>
  enterEnvironment(
    commsModelsControlPlane_56.InterfaceEnterEnvironmentRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceEnterEnvironmentResponse
    >(
      endpointRef: interfaceEnterEnvironmentEnterEnvironmentEndpointRef,
      discriminant: interfaceEnterEnvironmentEnterEnvironmentDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56.InterfaceEnterEnvironmentResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: interfaceEnterEnvironmentEnterEnvironmentEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceGetInterfaceStateCapabilityClient {
  InterfaceGetInterfaceStateCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Read the current Interface host state for an admitted namespace.
  Future<commsModelsControlPlane_56.InterfaceStatusResponse> getInterfaceState(
    commsModelsControlPlane_56.InterfaceStatusRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client
        .invokeApiEndpoint<commsModelsControlPlane_56.InterfaceStatusResponse>(
          endpointRef: interfaceGetInterfaceStateGetInterfaceStateEndpointRef,
          discriminant: interfaceGetInterfaceStateGetInterfaceStateDiscriminant,
          requestPayload: request.toJson(),
          decodeResponse: (payload) =>
              commsModelsControlPlane_56.InterfaceStatusResponse.fromJson(
                _requireJsonMap(
                  payload,
                  endpointRef:
                      interfaceGetInterfaceStateGetInterfaceStateEndpointRef,
                ),
              ),
          timeout: timeout,
        );
  }
}

class InterfaceInvokeInterfaceApiCapabilityClient {
  InterfaceInvokeInterfaceApiCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Invoke a mounted API endpoint from Interface action context.
  Future<commsModelsControlPlane_56.InterfaceInvokeApiResponse>
  invokeInterfaceApi(
    commsModelsControlPlane_56.InterfaceInvokeApiRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceInvokeApiResponse
    >(
      endpointRef: interfaceInvokeInterfaceApiInvokeInterfaceApiEndpointRef,
      discriminant: interfaceInvokeInterfaceApiInvokeInterfaceApiDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56.InterfaceInvokeApiResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceInvokeInterfaceApiInvokeInterfaceApiEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceJoinEnvironmentSessionCapabilityClient {
  InterfaceJoinEnvironmentSessionCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Join an Environment session and consume the Environment-owned default navigation context.
  Future<commsModelsControlPlane_56.InterfaceJoinEnvironmentSessionResponse>
  joinEnvironmentSession(
    commsModelsControlPlane_56.InterfaceJoinEnvironmentSessionRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceJoinEnvironmentSessionResponse
    >(
      endpointRef:
          interfaceJoinEnvironmentSessionJoinEnvironmentSessionEndpointRef,
      discriminant:
          interfaceJoinEnvironmentSessionJoinEnvironmentSessionDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56
              .InterfaceJoinEnvironmentSessionResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceJoinEnvironmentSessionJoinEnvironmentSessionEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceListInterfaceNamespacesCapabilityClient {
  InterfaceListInterfaceNamespacesCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// List locally admitted Interface namespaces for operator/debug surfaces.
  Future<commsModelsControlPlane_56.NamespaceListResponse>
  listInterfaceNamespaces(
    commsModelsControlPlane_56.NamespaceListRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.NamespaceListResponse
    >(
      endpointRef:
          interfaceListInterfaceNamespacesListInterfaceNamespacesEndpointRef,
      discriminant:
          interfaceListInterfaceNamespacesListInterfaceNamespacesDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56.NamespaceListResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceListInterfaceNamespacesListInterfaceNamespacesEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceMountInterfaceExperienceSessionCapabilityClient {
  InterfaceMountInterfaceExperienceSessionCapabilityClient(
    AwareApiClient client,
  ) : _client = client;

  final AwareApiClient _client;

  /// Commit one InterfaceSession-owned portal to an existing ExperienceSession authority.
  Future<commsModelsControlPlane_56.InterfaceExperienceSessionMountResponse>
  mountInterfaceExperienceSession(
    commsModelsControlPlane_56.InterfaceExperienceSessionMountRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceExperienceSessionMountResponse
    >(
      endpointRef:
          interfaceMountInterfaceExperienceSessionMountInterfaceExperienceSessionEndpointRef,
      discriminant:
          interfaceMountInterfaceExperienceSessionMountInterfaceExperienceSessionDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56
              .InterfaceExperienceSessionMountResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceMountInterfaceExperienceSessionMountInterfaceExperienceSessionEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfacePerformInterfaceActionCapabilityClient {
  InterfacePerformInterfaceActionCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Dispatch a mounted Interface action through the canonical service boundary.
  Future<commsModelsControlPlane_56.InterfaceActionResponse>
  performInterfaceAction(
    commsModelsControlPlane_56.InterfaceActionRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceActionResponse
    >(
      endpointRef:
          interfacePerformInterfaceActionPerformInterfaceActionEndpointRef,
      discriminant:
          interfacePerformInterfaceActionPerformInterfaceActionDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56.InterfaceActionResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfacePerformInterfaceActionPerformInterfaceActionEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfacePingInterfaceHostCapabilityClient {
  InterfacePingInterfaceHostCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Read local Interface host readiness for service transport adapters.
  Future<commsModelsControlPlane_56.PingResponse> pingInterfaceHost(
    commsModelsControlPlane_56.PingRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<commsModelsControlPlane_56.PingResponse>(
      endpointRef: interfacePingInterfaceHostPingInterfaceHostEndpointRef,
      discriminant: interfacePingInterfaceHostPingInterfaceHostDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56.PingResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfacePingInterfaceHostPingInterfaceHostEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceReportRendererCapabilitiesCapabilityClient {
  InterfaceReportRendererCapabilitiesCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Report renderer capabilities for the admitted Interface namespace.
  Future<commsModelsControlPlane_56.InterfaceReportRendererCapabilitiesResponse>
  reportRendererCapabilities(
    commsModelsControlPlane_56.InterfaceReportRendererCapabilitiesRequest
    request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceReportRendererCapabilitiesResponse
    >(
      endpointRef:
          interfaceReportRendererCapabilitiesReportRendererCapabilitiesEndpointRef,
      discriminant:
          interfaceReportRendererCapabilitiesReportRendererCapabilitiesDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56
              .InterfaceReportRendererCapabilitiesResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceReportRendererCapabilitiesReportRendererCapabilitiesEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceRequestInterfaceWindowLayoutCapabilityClient {
  InterfaceRequestInterfaceWindowLayoutCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Request a canonical Interface window/layout/section binding for a consumer action.
  Future<commsModelsControlPlane_56.InterfaceRequestWindowLayoutResponse>
  requestInterfaceWindowLayout(
    commsModelsControlPlane_56.InterfaceRequestWindowLayoutRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceRequestWindowLayoutResponse
    >(
      endpointRef:
          interfaceRequestInterfaceWindowLayoutRequestInterfaceWindowLayoutEndpointRef,
      discriminant:
          interfaceRequestInterfaceWindowLayoutRequestInterfaceWindowLayoutDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56
              .InterfaceRequestWindowLayoutResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceRequestInterfaceWindowLayoutRequestInterfaceWindowLayoutEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceResolveExperienceLensCapabilityClient {
  InterfaceResolveExperienceLensCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Resolve the current Interface focus into an actor-specific Experience lens over an admitted Environment session.
  Future<commsModelsControlPlane_56.InterfaceResolveExperienceLensResponse>
  resolveExperienceLens(
    commsModelsControlPlane_56.InterfaceResolveExperienceLensRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceResolveExperienceLensResponse
    >(
      endpointRef:
          interfaceResolveExperienceLensResolveExperienceLensEndpointRef,
      discriminant:
          interfaceResolveExperienceLensResolveExperienceLensDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56
              .InterfaceResolveExperienceLensResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceResolveExperienceLensResolveExperienceLensEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceSelectEnvironmentNavigationTargetCapabilityClient {
  InterfaceSelectEnvironmentNavigationTargetCapabilityClient(
    AwareApiClient client,
  ) : _client = client;

  final AwareApiClient _client;

  /// Select the active Environment Process/Thread target through Interface-owned shell navigation.
  Future<
    commsModelsControlPlane_56.InterfaceSelectEnvironmentNavigationTargetResponse
  >
  selectEnvironmentNavigationTarget(
    commsModelsControlPlane_56.InterfaceSelectEnvironmentNavigationTargetRequest
    request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceSelectEnvironmentNavigationTargetResponse
    >(
      endpointRef:
          interfaceSelectEnvironmentNavigationTargetSelectEnvironmentNavigationTargetEndpointRef,
      discriminant:
          interfaceSelectEnvironmentNavigationTargetSelectEnvironmentNavigationTargetDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56
              .InterfaceSelectEnvironmentNavigationTargetResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceSelectEnvironmentNavigationTargetSelectEnvironmentNavigationTargetEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceSelectInterfaceProfileCapabilityClient {
  InterfaceSelectInterfaceProfileCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Select the active Interface control profile for an admitted namespace.
  Future<commsModelsControlPlane_56.InterfaceSelectProfileResponse>
  selectInterfaceProfile(
    commsModelsControlPlane_56.InterfaceSelectProfileRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceSelectProfileResponse
    >(
      endpointRef:
          interfaceSelectInterfaceProfileSelectInterfaceProfileEndpointRef,
      discriminant:
          interfaceSelectInterfaceProfileSelectInterfaceProfileDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56.InterfaceSelectProfileResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceSelectInterfaceProfileSelectInterfaceProfileEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceSelectInterfaceRuntimeLayoutCapabilityClient {
  InterfaceSelectInterfaceRuntimeLayoutCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Select the active Interface runtime layout configuration.
  Future<commsModelsControlPlane_56.InterfaceSelectRuntimeLayoutResponse>
  selectInterfaceRuntimeLayout(
    commsModelsControlPlane_56.InterfaceSelectRuntimeLayoutRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceSelectRuntimeLayoutResponse
    >(
      endpointRef:
          interfaceSelectInterfaceRuntimeLayoutSelectInterfaceRuntimeLayoutEndpointRef,
      discriminant:
          interfaceSelectInterfaceRuntimeLayoutSelectInterfaceRuntimeLayoutDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56
              .InterfaceSelectRuntimeLayoutResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceSelectInterfaceRuntimeLayoutSelectInterfaceRuntimeLayoutEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceSelectInterfaceStepCapabilityClient {
  InterfaceSelectInterfaceStepCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Select the active Interface orchestration step for an admitted namespace.
  Future<commsModelsControlPlane_56.InterfaceSelectStepResponse>
  selectInterfaceStep(
    commsModelsControlPlane_56.InterfaceSelectStepRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceSelectStepResponse
    >(
      endpointRef: interfaceSelectInterfaceStepSelectInterfaceStepEndpointRef,
      discriminant: interfaceSelectInterfaceStepSelectInterfaceStepDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56.InterfaceSelectStepResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceSelectInterfaceStepSelectInterfaceStepEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceStartInterfaceSessionCapabilityClient {
  InterfaceStartInterfaceSessionCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Commit one Interface-owned shared door rooted on a canonical Identity Session.
  Future<commsModelsControlPlane_56.InterfaceSessionStartResponse>
  startInterfaceSession(
    commsModelsControlPlane_56.InterfaceSessionStartRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceSessionStartResponse
    >(
      endpointRef:
          interfaceStartInterfaceSessionStartInterfaceSessionEndpointRef,
      discriminant:
          interfaceStartInterfaceSessionStartInterfaceSessionDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56.InterfaceSessionStartResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceStartInterfaceSessionStartInterfaceSessionEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceStopInterfaceNamespaceCapabilityClient {
  InterfaceStopInterfaceNamespaceCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Stop one local Interface namespace.
  Future<commsModelsControlPlane_56.InterfaceStopResponse>
  stopInterfaceNamespace(
    commsModelsControlPlane_56.InterfaceStopRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceStopResponse
    >(
      endpointRef:
          interfaceStopInterfaceNamespaceStopInterfaceNamespaceEndpointRef,
      discriminant:
          interfaceStopInterfaceNamespaceStopInterfaceNamespaceDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56.InterfaceStopResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceStopInterfaceNamespaceStopInterfaceNamespaceEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceStreamInterfaceApiCapabilityClient {
  InterfaceStreamInterfaceApiCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Invoke a mounted streaming API endpoint from Interface action context.
  Future<commsModelsControlPlane_56.InterfaceStreamApiResponse>
  streamInterfaceApi(
    commsModelsControlPlane_56.InterfaceStreamApiRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceStreamApiResponse
    >(
      endpointRef: interfaceStreamInterfaceApiStreamInterfaceApiEndpointRef,
      discriminant: interfaceStreamInterfaceApiStreamInterfaceApiDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56.InterfaceStreamApiResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceStreamInterfaceApiStreamInterfaceApiEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// Invoke a mounted streaming API endpoint from Interface action context.
  Stream<InterfaceStreamInterfaceApiStreamInterfaceApiStreamEvent>
  streamStreamInterfaceApi(
    commsModelsControlPlane_56.InterfaceStreamApiRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) {
    return _client.streamApiEndpoint<
      InterfaceStreamInterfaceApiStreamInterfaceApiStreamEvent
    >(
      endpointRef: interfaceStreamInterfaceApiStreamInterfaceApiEndpointRef,
      discriminant: interfaceStreamInterfaceApiStreamInterfaceApiDiscriminant,
      requestPayload: request.toJson(),
      decodeEvent: (payload) =>
          commsModelsControlPlane_56.InterfaceControlPlaneNotification.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceStreamInterfaceApiStreamInterfaceApiEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceSyncViewStateCursorCapabilityClient {
  InterfaceSyncViewStateCursorCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Acknowledge consumed view-state cursors for Interface renderer backpressure.
  Future<commsModelsControlPlane_56.InterfaceSyncViewStateCursorResponse>
  syncViewStateCursor(
    commsModelsControlPlane_56.InterfaceSyncViewStateCursorRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceSyncViewStateCursorResponse
    >(
      endpointRef: interfaceSyncViewStateCursorSyncViewStateCursorEndpointRef,
      discriminant: interfaceSyncViewStateCursorSyncViewStateCursorDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56
              .InterfaceSyncViewStateCursorResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceSyncViewStateCursorSyncViewStateCursorEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceWatchInterfaceStateCapabilityClient {
  InterfaceWatchInterfaceStateCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Read and stream Interface host state snapshots for an admitted namespace.
  Future<commsModelsControlPlane_56.InterfaceFollowResponse>
  watchInterfaceState(
    commsModelsControlPlane_56.InterfaceFollowRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsControlPlane_56.InterfaceFollowResponse
    >(
      endpointRef: interfaceWatchInterfaceStateWatchInterfaceStateEndpointRef,
      discriminant: interfaceWatchInterfaceStateWatchInterfaceStateDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsControlPlane_56.InterfaceFollowResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceWatchInterfaceStateWatchInterfaceStateEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// Read and stream Interface host state snapshots for an admitted namespace.
  Stream<InterfaceWatchInterfaceStateWatchInterfaceStateStreamEvent>
  streamWatchInterfaceState(
    commsModelsControlPlane_56.InterfaceFollowRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) {
    return _client.streamApiEndpoint<
      InterfaceWatchInterfaceStateWatchInterfaceStateStreamEvent
    >(
      endpointRef: interfaceWatchInterfaceStateWatchInterfaceStateEndpointRef,
      discriminant: interfaceWatchInterfaceStateWatchInterfaceStateDiscriminant,
      requestPayload: request.toJson(),
      decodeEvent: (payload) =>
          commsModelsControlPlane_56.InterfaceStateNotification.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  interfaceWatchInterfaceStateWatchInterfaceStateEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class InterfaceApiClient {
  InterfaceApiClient(AwareApiClient client)
    : activateInterfaceRuntimeFocus =
          InterfaceActivateInterfaceRuntimeFocusCapabilityClient(client),
      admitEnvironmentActor = InterfaceAdmitEnvironmentActorCapabilityClient(
        client,
      ),
      admitInterface = InterfaceAdmitInterfaceCapabilityClient(client),
      applyAttentionLayoutTopologyTransition =
          InterfaceApplyAttentionLayoutTopologyTransitionCapabilityClient(
            client,
          ),
      applyAttentionLayoutTransition =
          InterfaceApplyAttentionLayoutTransitionCapabilityClient(client),
      describeInterfaceSession =
          InterfaceDescribeInterfaceSessionCapabilityClient(client),
      enterAppScreen = InterfaceEnterAppScreenCapabilityClient(client),
      enterEnvironment = InterfaceEnterEnvironmentCapabilityClient(client),
      getInterfaceState = InterfaceGetInterfaceStateCapabilityClient(client),
      invokeInterfaceApi = InterfaceInvokeInterfaceApiCapabilityClient(client),
      joinEnvironmentSession = InterfaceJoinEnvironmentSessionCapabilityClient(
        client,
      ),
      listInterfaceNamespaces =
          InterfaceListInterfaceNamespacesCapabilityClient(client),
      mountInterfaceExperienceSession =
          InterfaceMountInterfaceExperienceSessionCapabilityClient(client),
      performInterfaceAction = InterfacePerformInterfaceActionCapabilityClient(
        client,
      ),
      pingInterfaceHost = InterfacePingInterfaceHostCapabilityClient(client),
      reportRendererCapabilities =
          InterfaceReportRendererCapabilitiesCapabilityClient(client),
      requestInterfaceWindowLayout =
          InterfaceRequestInterfaceWindowLayoutCapabilityClient(client),
      resolveExperienceLens = InterfaceResolveExperienceLensCapabilityClient(
        client,
      ),
      selectEnvironmentNavigationTarget =
          InterfaceSelectEnvironmentNavigationTargetCapabilityClient(client),
      selectInterfaceProfile = InterfaceSelectInterfaceProfileCapabilityClient(
        client,
      ),
      selectInterfaceRuntimeLayout =
          InterfaceSelectInterfaceRuntimeLayoutCapabilityClient(client),
      selectInterfaceStep = InterfaceSelectInterfaceStepCapabilityClient(
        client,
      ),
      startInterfaceSession = InterfaceStartInterfaceSessionCapabilityClient(
        client,
      ),
      stopInterfaceNamespace = InterfaceStopInterfaceNamespaceCapabilityClient(
        client,
      ),
      streamInterfaceApi = InterfaceStreamInterfaceApiCapabilityClient(client),
      syncViewStateCursor = InterfaceSyncViewStateCursorCapabilityClient(
        client,
      ),
      watchInterfaceState = InterfaceWatchInterfaceStateCapabilityClient(
        client,
      );

  final InterfaceActivateInterfaceRuntimeFocusCapabilityClient
  activateInterfaceRuntimeFocus;
  final InterfaceAdmitEnvironmentActorCapabilityClient admitEnvironmentActor;
  final InterfaceAdmitInterfaceCapabilityClient admitInterface;
  final InterfaceApplyAttentionLayoutTopologyTransitionCapabilityClient
  applyAttentionLayoutTopologyTransition;
  final InterfaceApplyAttentionLayoutTransitionCapabilityClient
  applyAttentionLayoutTransition;
  final InterfaceDescribeInterfaceSessionCapabilityClient
  describeInterfaceSession;
  final InterfaceEnterAppScreenCapabilityClient enterAppScreen;
  final InterfaceEnterEnvironmentCapabilityClient enterEnvironment;
  final InterfaceGetInterfaceStateCapabilityClient getInterfaceState;
  final InterfaceInvokeInterfaceApiCapabilityClient invokeInterfaceApi;
  final InterfaceJoinEnvironmentSessionCapabilityClient joinEnvironmentSession;
  final InterfaceListInterfaceNamespacesCapabilityClient
  listInterfaceNamespaces;
  final InterfaceMountInterfaceExperienceSessionCapabilityClient
  mountInterfaceExperienceSession;
  final InterfacePerformInterfaceActionCapabilityClient performInterfaceAction;
  final InterfacePingInterfaceHostCapabilityClient pingInterfaceHost;
  final InterfaceReportRendererCapabilitiesCapabilityClient
  reportRendererCapabilities;
  final InterfaceRequestInterfaceWindowLayoutCapabilityClient
  requestInterfaceWindowLayout;
  final InterfaceResolveExperienceLensCapabilityClient resolveExperienceLens;
  final InterfaceSelectEnvironmentNavigationTargetCapabilityClient
  selectEnvironmentNavigationTarget;
  final InterfaceSelectInterfaceProfileCapabilityClient selectInterfaceProfile;
  final InterfaceSelectInterfaceRuntimeLayoutCapabilityClient
  selectInterfaceRuntimeLayout;
  final InterfaceSelectInterfaceStepCapabilityClient selectInterfaceStep;
  final InterfaceStartInterfaceSessionCapabilityClient startInterfaceSession;
  final InterfaceStopInterfaceNamespaceCapabilityClient stopInterfaceNamespace;
  final InterfaceStreamInterfaceApiCapabilityClient streamInterfaceApi;
  final InterfaceSyncViewStateCursorCapabilityClient syncViewStateCursor;
  final InterfaceWatchInterfaceStateCapabilityClient watchInterfaceState;
}

class AwareInterfaceServiceApiClient {
  AwareInterfaceServiceApiClient(AwareApiClient client)
    : interface = InterfaceApiClient(client);

  final Map<String, Object?> interfaceSpecPayload = apiInterfaceSpecPayload;
  final Map<String, Object?> invocationManifestPayload =
      apiInvocationManifestPayload;
  final InterfaceApiClient interface;
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
