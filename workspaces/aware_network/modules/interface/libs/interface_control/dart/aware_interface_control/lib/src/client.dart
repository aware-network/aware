import 'dart:async';
import 'dart:convert';

import 'package:aware_interface_service_api/aware_interface_service_api.dart';
import 'package:uuid/uuid.dart';

import 'path_resolution.dart';
import 'transport.dart';

String? _normalizeControlPlaneErrorMessage(String? raw) {
  if (raw == null) {
    return null;
  }
  var normalized = raw.trim();
  while (normalized.length >= 2) {
    final startsWithSingleQuote = normalized.startsWith("'");
    final endsWithSingleQuote = normalized.endsWith("'");
    final startsWithDoubleQuote = normalized.startsWith('"');
    final endsWithDoubleQuote = normalized.endsWith('"');
    final wrappedInMatchingQuotes =
        (startsWithSingleQuote && endsWithSingleQuote) ||
            (startsWithDoubleQuote && endsWithDoubleQuote);
    if (!wrappedInMatchingQuotes) {
      break;
    }
    normalized = normalized.substring(1, normalized.length - 1).trim();
  }
  if (normalized.isEmpty) {
    return null;
  }
  return normalized;
}

class InterfaceControlPlaneClientError implements Exception {
  InterfaceControlPlaneClientError({
    required this.operation,
    required this.error,
  });

  final String? operation;
  final String? error;

  @override
  String toString() {
    final message = _normalizeControlPlaneErrorMessage(error);
    if (message != null) {
      return message;
    }
    final op = operation?.trim();
    if (op != null && op.isNotEmpty) {
      return 'Interface control plane request failed for `$op`.';
    }
    return 'Interface control plane request failed.';
  }
}

class InterfaceControlPlaneApiStreamHandle {
  const InterfaceControlPlaneApiStreamHandle({
    required this.events,
    required this.response,
    required this.close,
  });

  final Stream<InterfaceApiEventNotification> events;
  final Future<InterfaceApiStreamClosedNotification> response;
  final Future<void> Function() close;
}

class InterfaceActionTargetTransport {
  const InterfaceActionTargetTransport({
    required this.actionKey,
    required this.actionKind,
    this.operationRef,
    this.sdkOperationId,
    this.paneConfigSdkOperationId,
    this.endpointRef,
    this.apiCapabilityEndpointId,
    this.paneConfigApiCapabilityEndpointId,
  });

  final String actionKey;
  final String actionKind;
  final String? operationRef;
  final String? sdkOperationId;
  final String? paneConfigSdkOperationId;
  final String? endpointRef;
  final String? apiCapabilityEndpointId;
  final String? paneConfigApiCapabilityEndpointId;

  Map<String, dynamic> toJson() {
    final trimmedOperationRef = _trimmedOrNull(operationRef);
    final trimmedSdkOperationId = _trimmedOrNull(sdkOperationId);
    final trimmedPaneConfigSdkOperationId = _trimmedOrNull(
      paneConfigSdkOperationId,
    );
    final trimmedEndpointRef = _trimmedOrNull(endpointRef);
    final trimmedApiCapabilityEndpointId = _trimmedOrNull(
      apiCapabilityEndpointId,
    );
    final trimmedPaneConfigApiCapabilityEndpointId = _trimmedOrNull(
      paneConfigApiCapabilityEndpointId,
    );
    return <String, dynamic>{
      'action_key': actionKey,
      'action_kind': actionKind,
      if (trimmedOperationRef != null) 'operation_ref': trimmedOperationRef,
      if (trimmedSdkOperationId != null)
        'sdk_operation_id': trimmedSdkOperationId,
      if (trimmedPaneConfigSdkOperationId != null)
        'pane_config_sdk_operation_id': trimmedPaneConfigSdkOperationId,
      if (trimmedEndpointRef != null) 'endpoint_ref': trimmedEndpointRef,
      if (trimmedApiCapabilityEndpointId != null)
        'api_capability_endpoint_id': trimmedApiCapabilityEndpointId,
      if (trimmedPaneConfigApiCapabilityEndpointId != null)
        'pane_config_api_capability_endpoint_id':
            trimmedPaneConfigApiCapabilityEndpointId,
    };
  }
}

class InterfaceControlPlaneClient {
  InterfaceControlPlaneClient({
    String? socketPath,
    String? stateHome,
    String? controlPlaneUrl,
    Uri? controlPlaneUri,
    InterfaceControlPlaneTransport? transport,
  })  : controlPlaneUri = transport == null
            ? _resolveControlPlaneUri(
                controlPlaneUrl: controlPlaneUrl,
                controlPlaneUri: controlPlaneUri,
              )
            : controlPlaneUri,
        socketPath = transport == null
            ? _resolveSocketPath(
                socketPath: socketPath,
                stateHome: stateHome,
                controlPlaneUrl: controlPlaneUrl,
                controlPlaneUri: controlPlaneUri,
              )
            : socketPath,
        _transport = transport ??
            _buildDefaultTransport(
              socketPath: socketPath,
              stateHome: stateHome,
              controlPlaneUrl: controlPlaneUrl,
              controlPlaneUri: controlPlaneUri,
            );

  final Uri? controlPlaneUri;
  final String? socketPath;
  final InterfaceControlPlaneTransport _transport;
  final Uuid _uuid = const Uuid();

  static Uri? _resolveControlPlaneUri({
    String? controlPlaneUrl,
    Uri? controlPlaneUri,
  }) {
    return controlPlaneUri ??
        resolveControlPlaneWebSocketUri(controlPlaneUrl: controlPlaneUrl);
  }

  static String? _resolveSocketPath({
    String? socketPath,
    String? stateHome,
    String? controlPlaneUrl,
    Uri? controlPlaneUri,
  }) {
    final remoteUri = _resolveControlPlaneUri(
      controlPlaneUrl: controlPlaneUrl,
      controlPlaneUri: controlPlaneUri,
    );
    if (remoteUri != null) {
      return null;
    }
    return resolveControlSocketPath(
      socketPath: socketPath,
      stateHome: stateHome,
    );
  }

  static InterfaceControlPlaneTransport _buildDefaultTransport({
    String? socketPath,
    String? stateHome,
    String? controlPlaneUrl,
    Uri? controlPlaneUri,
  }) {
    final remoteUri = _resolveControlPlaneUri(
      controlPlaneUrl: controlPlaneUrl,
      controlPlaneUri: controlPlaneUri,
    );
    if (remoteUri != null) {
      return InterfaceControlPlaneWebSocketTransport(uri: remoteUri);
    }
    return InterfaceControlPlaneSocketTransport(
      socketPath: resolveControlSocketPath(
        socketPath: socketPath,
        stateHome: stateHome,
      ),
    );
  }

  Future<PingResponse> ping() async {
    return _request(
      fallbackOperation: 'ping',
      InterfaceControlPlaneRequest.ping(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
      ),
      expect: (response) =>
          response.maybeMap(ping: (value) => value, orElse: () => null),
    );
  }

  Future<NamespaceEnsureResponse> ensureNamespace({
    required String namespace,
    String? authToken,
    String? endpoint,
    String? hostLabel,
    UuidValue? environmentConfigId,
  }) async {
    return _request(
      fallbackOperation: 'namespace_ensure',
      InterfaceControlPlaneRequest.namespaceEnsure(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
        namespace: namespace,
        authToken: authToken,
        endpoint: endpoint,
        hostLabel: hostLabel,
        environmentConfigId: environmentConfigId,
      ),
      expect: (response) => response.maybeMap(
        namespaceEnsure: (value) => value,
        orElse: () => null,
      ),
    );
  }

  Future<NamespaceListResponse> listNamespaces() async {
    return _request(
      fallbackOperation: 'namespace_list',
      InterfaceControlPlaneRequest.namespaceList(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
      ),
      expect: (response) => response.maybeMap(
        namespaceList: (value) => value,
        orElse: () => null,
      ),
    );
  }

  Future<InterfaceStatusResponse> status({required String namespace}) async {
    return _request(
      fallbackOperation: 'interface_status',
      InterfaceControlPlaneRequest.interfaceStatus(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
        namespace: namespace,
      ),
      expect: (response) => response.maybeMap(
        interfaceStatus: (value) => value,
        orElse: () => null,
      ),
    );
  }

  Future<InterfaceJoinEnvironmentSessionResponse> joinEnvironmentSession({
    required String namespace,
    required UuidValue environmentSessionId,
    UuidValue? environmentProfileId,
    EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt,
    String? reason,
    Map<String, dynamic> evidence = const <String, dynamic>{},
  }) async {
    return _request(
      fallbackOperation: 'interface_join_environment_session',
      InterfaceControlPlaneRequest.interfaceJoinEnvironmentSession(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
        namespace: namespace,
        environmentSessionId: environmentSessionId,
        environmentProfileId: environmentProfileId,
        environmentAdmissionReceipt: environmentAdmissionReceipt,
        reason: reason,
        evidence: evidence,
      ),
      expect: (response) => response.maybeMap(
        interfaceJoinEnvironmentSession: (value) => value,
        orElse: () => null,
      ),
    );
  }

  Future<InterfaceEnterEnvironmentResponse> enterEnvironment({
    required String namespace,
    UuidValue? environmentId,
    UuidValue? environmentProfileId,
    UuidValue? actorConfigId,
    UuidValue? classInstanceIdentityId,
    String objectInstanceGraphBranchKey = 'all',
    UuidValue? objectInstanceGraphBranchId,
    List<UuidValue> requestedRoleConfigIds = const <UuidValue>[],
    List<String> requestedRoleConfigNames = const <String>[],
    EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt,
    UuidValue? environmentSessionId,
    UuidValue? environmentSessionConfigId,
    String? sessionKey,
    String? title,
    String? description,
    String? purpose,
    String? sourceKind,
    String? sourceRef,
    String? reason,
    Map<String, dynamic> evidence = const <String, dynamic>{},
  }) async {
    return _request(
      fallbackOperation: 'interface_enter_environment',
      InterfaceControlPlaneRequest.interfaceEnterEnvironment(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
        namespace: namespace,
        environmentId: environmentId,
        environmentProfileId: environmentProfileId,
        actorConfigId: actorConfigId,
        classInstanceIdentityId: classInstanceIdentityId,
        objectInstanceGraphBranchKey: objectInstanceGraphBranchKey,
        objectInstanceGraphBranchId: objectInstanceGraphBranchId,
        requestedRoleConfigIds: requestedRoleConfigIds,
        requestedRoleConfigNames: requestedRoleConfigNames,
        environmentAdmissionReceipt: environmentAdmissionReceipt,
        environmentSessionId: environmentSessionId,
        environmentSessionConfigId: environmentSessionConfigId,
        sessionKey: sessionKey,
        title: title,
        description: description,
        purpose: purpose,
        sourceKind: sourceKind,
        sourceRef: sourceRef,
        reason: reason,
        evidence: evidence,
      ),
      expect: (response) => response.maybeMap(
        interfaceEnterEnvironment: (value) => value,
        orElse: () => null,
      ),
    );
  }

  Future<InterfaceSelectEnvironmentNavigationTargetResponse>
      selectEnvironmentNavigationTarget({
    required String namespace,
    UuidValue? environmentNavigationContextId,
    UuidValue? selectedProcessId,
    UuidValue? selectedThreadId,
    String? reason,
    Map<String, dynamic> evidence = const <String, dynamic>{},
  }) async {
    return _request(
      fallbackOperation: 'interface_select_environment_navigation_target',
      InterfaceControlPlaneRequest.interfaceSelectEnvironmentNavigationTarget(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
        namespace: namespace,
        environmentNavigationContextId: environmentNavigationContextId,
        selectedProcessId: selectedProcessId,
        selectedThreadId: selectedThreadId,
        reason: reason,
        evidence: evidence,
      ),
      expect: (response) => response.maybeMap(
        interfaceSelectEnvironmentNavigationTarget: (value) => value,
        orElse: () => null,
      ),
    );
  }

  Future<InterfaceInvokeApiResponse> invokeApi({
    required String namespace,
    required String endpointRef,
    required String discriminant,
    Map<String, dynamic> requestPayload = const <String, dynamic>{},
  }) async {
    return _request(
      fallbackOperation: 'interface_invoke_api',
      InterfaceControlPlaneRequest.interfaceInvokeApi(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
        namespace: namespace,
        endpointRef: endpointRef,
        discriminant: discriminant,
        requestPayload: requestPayload,
      ),
      expect: (response) => response.maybeMap(
        interfaceInvokeApi: (value) => value,
        orElse: () => null,
      ),
    );
  }

  Future<InterfaceActionResponse> action({
    required String namespace,
    required String actionKey,
    String? paneRef,
    InterfaceActionTargetTransport? actionTarget,
    Map<String, dynamic> payload = const <String, dynamic>{},
  }) async {
    final actionTargetPayload = actionTarget?.toJson();
    return _request(
      fallbackOperation: 'interface_action',
      InterfaceControlPlaneRequest.interfaceAction(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
        namespace: namespace,
        paneRef: paneRef,
        actionKey: actionKey,
        actionKind: actionTargetPayload?['action_kind'] as String?,
        operationRef: actionTargetPayload?['operation_ref'] as String?,
        sdkOperationId: actionTargetPayload?['sdk_operation_id'] as String?,
        paneConfigSdkOperationId:
            actionTargetPayload?['pane_config_sdk_operation_id'] as String?,
        endpointRef: actionTargetPayload?['endpoint_ref'] as String?,
        apiCapabilityEndpointId:
            actionTargetPayload?['api_capability_endpoint_id'] as String?,
        paneConfigApiCapabilityEndpointId:
            actionTargetPayload?['pane_config_api_capability_endpoint_id']
                as String?,
        payload: payload,
      ),
      expect: (response) => response.maybeMap(
        interfaceAction: (value) => value,
        orElse: () => null,
      ),
    );
  }

  Future<InterfaceSelectStepResponse> selectStep({
    required String namespace,
    String? stepId,
  }) async {
    return _request(
      fallbackOperation: 'interface_select_step',
      InterfaceControlPlaneRequest.interfaceSelectStep(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
        namespace: namespace,
        stepId: stepId,
      ),
      expect: (response) => response.maybeMap(
        interfaceSelectStep: (value) => value,
        orElse: () => null,
      ),
    );
  }

  Future<InterfaceSelectProfileResponse> selectProfile({
    required String namespace,
    required String profileId,
  }) async {
    return _request(
      fallbackOperation: 'interface_select_profile',
      InterfaceControlPlaneRequest.interfaceSelectProfile(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
        namespace: namespace,
        profileId: profileId,
      ),
      expect: (response) => response.maybeMap(
        interfaceSelectProfile: (value) => value,
        orElse: () => null,
      ),
    );
  }

  Future<InterfaceSelectRuntimeLayoutResponse> selectRuntimeLayout({
    required String namespace,
    UuidValue? layoutConfigId,
  }) async {
    return _request(
      fallbackOperation: 'interface_select_runtime_layout',
      InterfaceControlPlaneRequest.interfaceSelectRuntimeLayout(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
        namespace: namespace,
        layoutConfigId: layoutConfigId,
      ),
      expect: (response) => response.maybeMap(
        interfaceSelectRuntimeLayout: (value) => value,
        orElse: () => null,
      ),
    );
  }

  Future<InterfaceActivateRuntimeFocusResponse> activateRuntimeFocus({
    required String namespace,
    UuidValue? representationId,
  }) async {
    return _request(
      fallbackOperation: 'interface_activate_runtime_focus',
      InterfaceControlPlaneRequest.interfaceActivateRuntimeFocus(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
        namespace: namespace,
        representationId: representationId,
      ),
      expect: (response) => response.maybeMap(
        interfaceActivateRuntimeFocus: (value) => value,
        orElse: () => null,
      ),
    );
  }

  Future<InterfaceRequestWindowLayoutResponse> requestWindowLayout({
    required String namespace,
    UuidValue? interfacePackageId,
    String? interfacePackageName,
    String? windowKey,
    UuidValue? layoutConfigId,
    String? layoutKey,
    String? sectionKey,
    UuidValue? observableId,
    UuidValue? representationId,
    String? requestedByService,
    String? requestedByOperation,
    String? reason,
    String? idempotencyKey,
  }) async {
    return _request(
      fallbackOperation: 'interface_request_window_layout',
      InterfaceControlPlaneRequest.interfaceRequestWindowLayout(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
        namespace: namespace,
        interfacePackageId: interfacePackageId,
        interfacePackageName: interfacePackageName,
        windowKey: windowKey,
        layoutConfigId: layoutConfigId,
        layoutKey: layoutKey,
        sectionKey: sectionKey,
        observableId: observableId,
        representationId: representationId,
        requestedByService: requestedByService,
        requestedByOperation: requestedByOperation,
        reason: reason,
        idempotencyKey: idempotencyKey,
      ),
      expect: (response) => response.maybeMap(
        interfaceRequestWindowLayout: (value) => value,
        orElse: () => null,
      ),
    );
  }

  Future<InterfaceApplyAttentionLayoutTransitionResponse>
      applyAttentionLayoutTransition({
    required String namespace,
    required String clientIntentId,
    UuidValue? expectedPreviousLayoutTransitionId,
    UuidValue? topologyTransitionId,
    required List<InterfaceAttentionLayoutTransitionSectionIntent>
        sectionStates,
  }) async {
    return _request(
      fallbackOperation: 'interface_apply_attention_layout_transition',
      InterfaceControlPlaneRequest.interfaceApplyAttentionLayoutTransition(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
        namespace: namespace,
        clientIntentId: clientIntentId,
        expectedPreviousLayoutTransitionId: expectedPreviousLayoutTransitionId,
        topologyTransitionId: topologyTransitionId,
        sectionStates: sectionStates,
      ),
      expect: (response) => response.maybeMap(
        interfaceApplyAttentionLayoutTransition: (value) => value,
        orElse: () => null,
      ),
    );
  }

  Future<InterfaceApplyAttentionLayoutTopologyTransitionResponse>
      applyAttentionLayoutTopologyTransition({
    required String namespace,
    required String clientIntentId,
    UuidValue? expectedPreviousTopologyTransitionId,
    required List<InterfaceAttentionLayoutTopologyTransitionSectionIntent>
        sectionStates,
  }) async {
    return _request(
      fallbackOperation: 'interface_apply_attention_layout_topology_transition',
      InterfaceControlPlaneRequest
          .interfaceApplyAttentionLayoutTopologyTransition(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
        namespace: namespace,
        clientIntentId: clientIntentId,
        expectedPreviousTopologyTransitionId:
            expectedPreviousTopologyTransitionId,
        sectionStates: sectionStates,
      ),
      expect: (response) => response.maybeMap(
        interfaceApplyAttentionLayoutTopologyTransition: (value) => value,
        orElse: () => null,
      ),
    );
  }

  Future<InterfaceReportRendererCapabilitiesResponse>
      reportRendererCapabilities({
    required String namespace,
    required InterfaceRendererCapabilitiesState rendererCapabilities,
  }) async {
    return _request(
      fallbackOperation: 'interface_report_renderer_capabilities',
      InterfaceControlPlaneRequest.interfaceReportRendererCapabilities(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
        namespace: namespace,
        rendererCapabilities: rendererCapabilities,
      ),
      expect: (response) => response.maybeMap(
        interfaceReportRendererCapabilities: (value) => value,
        orElse: () => null,
      ),
    );
  }

  Future<InterfaceSyncViewStateCursorResponse> syncViewStateCursor({
    required String namespace,
    String? rendererId,
    String? knownCursor,
    String? knownDigest,
  }) async {
    return _request(
      fallbackOperation: 'interface_sync_view_state_cursor',
      InterfaceControlPlaneRequest.interfaceSyncViewStateCursor(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
        namespace: namespace,
        rendererId: rendererId,
        knownCursor: knownCursor,
        knownDigest: knownDigest,
      ),
      expect: (response) => response.maybeMap(
        interfaceSyncViewStateCursor: (value) => value,
        orElse: () => null,
      ),
    );
  }

  Stream<InterfaceHostState> follow({
    required String namespace,
    int pollIntervalMs = 1000,
  }) async* {
    final connection = await _connect();
    final lines = connection.lines;

    final request = InterfaceControlPlaneOperation(
      request: InterfaceControlPlaneRequest.interfaceFollow(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
        namespace: namespace,
        pollIntervalMs: pollIntervalMs,
      ),
    );

    try {
      await _writeOperation(connection, request);
      final iterator = StreamIterator<String>(lines);
      try {
        final hasFirst = await iterator.moveNext();
        if (!hasFirst) {
          throw StateError(
            'Interface control plane closed without a follow response.',
          );
        }

        final first = _parseOperation(
          iterator.current,
          fallbackOperation: 'interface_follow',
        );
        final response = first.response;
        if (response is! InterfaceFollowResponse) {
          throw StateError(
            'Interface control plane returned an invalid follow response envelope.',
          );
        }
        _throwIfFailed(response);
        yield response.hostState;

        while (await iterator.moveNext()) {
          final operation = _parseOperation(iterator.current);
          final notification = operation.notification;
          if (notification == null) {
            continue;
          }
          final hostState = notification.maybeMap<InterfaceHostState?>(
            interfaceState: (value) => value.hostState,
            orElse: () => null,
          );
          if (hostState != null) {
            yield hostState;
          }
        }
      } finally {
        await iterator.cancel();
      }
    } finally {
      await connection.close();
    }
  }

  Future<InterfaceControlPlaneApiStreamHandle> openApiStream({
    required String namespace,
    required String endpointRef,
    required String discriminant,
    Map<String, dynamic> requestPayload = const <String, dynamic>{},
  }) async {
    final connection = await _connect();
    final lines = connection.lines;

    final request = InterfaceControlPlaneOperation(
      request: InterfaceControlPlaneRequest.interfaceStreamApi(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
        namespace: namespace,
        endpointRef: endpointRef,
        discriminant: discriminant,
        requestPayload: requestPayload,
      ),
    );

    await _writeOperation(connection, request);
    final iterator = StreamIterator<String>(lines);
    final hasFirst = await iterator.moveNext();
    if (!hasFirst) {
      await iterator.cancel();
      await connection.close();
      throw StateError(
        'Interface control plane closed without an API stream response.',
      );
    }

    final first = _parseOperation(
      iterator.current,
      fallbackOperation: 'interface_stream_api',
    );
    final response = first.response;
    if (response is! InterfaceStreamApiResponse) {
      await iterator.cancel();
      await connection.close();
      throw StateError(
        'Interface control plane returned an invalid API stream response envelope.',
      );
    }
    _throwIfFailed(response);

    final events = StreamController<InterfaceApiEventNotification>();
    final responseCompleter = Completer<InterfaceApiStreamClosedNotification>();
    var closed = false;

    Future<void> close() async {
      if (closed) {
        return;
      }
      closed = true;
      await iterator.cancel();
      await connection.close();
      if (!responseCompleter.isCompleted) {
        responseCompleter.completeError(
          StateError(
            'Interface control plane API stream closed before a terminal notification.',
          ),
        );
      }
      await events.close();
    }

    unawaited(() async {
      try {
        while (await iterator.moveNext()) {
          final operation = _parseOperation(iterator.current);
          final notification = operation.notification;
          if (notification == null) {
            continue;
          }
          final event = notification.maybeMap<InterfaceApiEventNotification?>(
            interfaceApiEvent: (value) => value,
            orElse: () => null,
          );
          if (event != null) {
            if (!events.isClosed) {
              events.add(event);
            }
            continue;
          }
          final terminal =
              notification.maybeMap<InterfaceApiStreamClosedNotification?>(
            interfaceApiStreamClosed: (value) => value,
            orElse: () => null,
          );
          if (terminal != null) {
            if (!responseCompleter.isCompleted) {
              responseCompleter.complete(terminal);
            }
            break;
          }
        }
        if (!responseCompleter.isCompleted) {
          responseCompleter.completeError(
            StateError(
              'Interface control plane API stream ended without a terminal notification.',
            ),
          );
        }
      } catch (error, stackTrace) {
        if (!events.isClosed) {
          events.addError(error, stackTrace);
        }
        if (!responseCompleter.isCompleted) {
          responseCompleter.completeError(error, stackTrace);
        }
      } finally {
        closed = true;
        await iterator.cancel();
        await connection.close();
        if (!events.isClosed) {
          await events.close();
        }
      }
    }());

    return InterfaceControlPlaneApiStreamHandle(
      events: events.stream,
      response: responseCompleter.future,
      close: close,
    );
  }

  Future<InterfaceStopResponse> stop({required String namespace}) async {
    return _request(
      fallbackOperation: 'interface_stop',
      InterfaceControlPlaneRequest.interfaceStop(
        requestId: UuidValue.fromString(_uuid.v4()),
        protocolVersion: 1,
        namespace: namespace,
      ),
      expect: (response) => response.maybeMap(
        interfaceStop: (value) => value,
        orElse: () => null,
      ),
    );
  }

  Future<T> _request<T>(
    InterfaceControlPlaneRequest request, {
    required String fallbackOperation,
    required T? Function(InterfaceControlPlaneResponse response) expect,
  }) async {
    final connection = await _connect();
    final lines = connection.lines;
    try {
      await _writeOperation(
        connection,
        InterfaceControlPlaneOperation(request: request),
      );
      final line = await lines.first;
      final operation = _parseOperation(
        line,
        fallbackOperation: fallbackOperation,
      );
      final response = operation.response;
      if (response == null) {
        throw StateError(
          'Interface control plane returned a non-response envelope.',
        );
      }
      _throwIfFailed(response);
      final typed = expect(response);
      if (typed == null) {
        throw StateError(
          'Interface control plane returned ${response.runtimeType} for ${request.runtimeType}.',
        );
      }
      return typed;
    } finally {
      await connection.close();
    }
  }

  Future<InterfaceControlPlaneConnection> _connect() async {
    return _transport.connect();
  }

  Future<void> _writeOperation(
    InterfaceControlPlaneConnection connection,
    InterfaceControlPlaneOperation operation,
  ) async {
    final payload = operation.toJson();
    await connection.writeLine(jsonEncode(payload));
  }

  InterfaceControlPlaneOperation _parseOperation(
    String line, {
    String? fallbackOperation,
  }) {
    final payload = jsonDecode(line);
    if (payload is! Map) {
      throw StateError(
        'Interface control plane yielded a non-object JSON envelope.',
      );
    }
    final envelope = Map<String, dynamic>.from(payload);
    _normalizeEnvelopeForCompatibility(envelope);
    _throwIfFailedEnvelope(envelope, fallbackOperation: fallbackOperation);
    return InterfaceControlPlaneOperation.fromJson(envelope);
  }

  void _normalizeEnvelopeForCompatibility(Map<String, dynamic> envelope) {
    final responsePayload = envelope['response'];
    if (responsePayload is! Map) {
      return;
    }
    final response = Map<String, dynamic>.from(responsePayload);
    if (response['operation'] == 'ping') {
      if (response['restart_recommended'] == null) {
        response['restart_recommended'] = false;
      }
    }
    envelope['response'] = response;
  }

  void _throwIfFailedEnvelope(
    Map<String, dynamic> envelope, {
    String? fallbackOperation,
  }) {
    final responsePayload = envelope['response'];
    if (responsePayload is! Map) {
      return;
    }
    final response = Map<String, dynamic>.from(responsePayload);
    if (response['success'] == true) {
      return;
    }
    throw InterfaceControlPlaneClientError(
      operation: (response['operation'] as String?) ?? fallbackOperation,
      error: _normalizeControlPlaneErrorMessage(response['error'] as String?),
    );
  }

  void _throwIfFailed(InterfaceControlPlaneResponse response) {
    if (response.success) {
      return;
    }
    throw InterfaceControlPlaneClientError(
      operation: response.map(
        ping: (_) => 'ping',
        namespaceEnsure: (_) => 'namespace_ensure',
        namespaceList: (_) => 'namespace_list',
        interfaceAction: (_) => 'interface_action',
        interfaceAdmitEnvironmentActor: (_) =>
            'interface_admit_environment_actor',
        interfaceJoinEnvironmentSession: (_) =>
            'interface_join_environment_session',
        interfaceSelectEnvironmentNavigationTarget: (_) =>
            'interface_select_environment_navigation_target',
        interfaceEnterEnvironment: (_) => 'interface_enter_environment',
        interfaceResolveExperienceLens: (_) =>
            'interface_resolve_experience_lens',
        interfaceInvokeApi: (_) => 'interface_invoke_api',
        interfaceStreamApi: (_) => 'interface_stream_api',
        interfaceFollow: (_) => 'interface_follow',
        interfaceSelectProfile: (_) => 'interface_select_profile',
        interfaceSelectRuntimeLayout: (_) => 'interface_select_runtime_layout',
        interfaceActivateRuntimeFocus: (_) =>
            'interface_activate_runtime_focus',
        interfaceRequestWindowLayout: (_) => 'interface_request_window_layout',
        interfaceApplyAttentionLayoutTransition: (_) =>
            'interface_apply_attention_layout_transition',
        interfaceApplyAttentionLayoutTopologyTransition: (_) =>
            'interface_apply_attention_layout_topology_transition',
        interfaceReportRendererCapabilities: (_) =>
            'interface_report_renderer_capabilities',
        interfaceSyncViewStateCursor: (_) => 'interface_sync_view_state_cursor',
        interfaceSelectStep: (_) => 'interface_select_step',
        interfaceStatus: (_) => 'interface_status',
        interfaceStop: (_) => 'interface_stop',
      ),
      error: _normalizeControlPlaneErrorMessage(response.error),
    );
  }
}

class InterfaceControlPlaneOperation {
  const InterfaceControlPlaneOperation({
    this.request,
    this.response,
    this.notification,
  }) : assert(
          (request == null ? 0 : 1) +
                  (response == null ? 0 : 1) +
                  (notification == null ? 0 : 1) ==
              1,
          'Interface control-plane operation must contain exactly one payload.',
        );

  factory InterfaceControlPlaneOperation.fromJson(Map<String, dynamic> json) {
    final requestPayload = json['request'];
    final responsePayload = json['response'];
    final notificationPayload = json['notification'];
    return InterfaceControlPlaneOperation(
      request: requestPayload is Map
          ? InterfaceControlPlaneRequest.fromJson(
              Map<String, dynamic>.from(requestPayload),
            )
          : null,
      response: responsePayload is Map
          ? InterfaceControlPlaneResponse.fromJson(
              Map<String, dynamic>.from(responsePayload),
            )
          : null,
      notification: notificationPayload is Map
          ? InterfaceControlPlaneNotification.fromJson(
              Map<String, dynamic>.from(notificationPayload),
            )
          : null,
    );
  }

  final InterfaceControlPlaneRequest? request;
  final InterfaceControlPlaneResponse? response;
  final InterfaceControlPlaneNotification? notification;

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      if (request != null) 'request': request!.toJson(),
      if (response != null) 'response': response!.toJson(),
      if (notification != null) 'notification': notification!.toJson(),
    };
  }
}

String? _trimmedOrNull(String? value) {
  final trimmed = value?.trim();
  if (trimmed == null || trimmed.isEmpty) {
    return null;
  }
  return trimmed;
}
