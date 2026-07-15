import 'dart:convert';
import 'dart:io';

import 'package:aware_interface_service_api/aware_interface_service_api.dart';
import 'package:aware_interface_control/aware_interface_control.dart';
import 'package:path/path.dart' as p;
import 'package:test/test.dart';
import 'package:uuid/uuid.dart';

void main() {
  test('resolveControlSocketPath prefers explicit socket path', () {
    final socketPath = resolveControlSocketPath(
      socketPath: '/tmp/interface.sock',
      stateHome: '/tmp/ignored',
    );
    expect(socketPath, '/tmp/interface.sock');
  });

  test('resolveDefaultStateHome falls back to the repo local state dir', () {
    final stateHome = resolveDefaultStateHome(
      currentDirectory: Directory.current.path,
    );
    expect(stateHome, endsWith('.aware/interface_service'));
  });

  test('resolveControlPlaneWebSocketUri normalizes https bootstrap URLs', () {
    final uri = resolveControlPlaneWebSocketUri(
      controlPlaneUrl: 'https://aware.run/interface/control',
    );
    expect(uri, isNotNull);
    expect(uri?.scheme, 'wss');
    expect(uri?.host, 'aware.run');
    expect(uri?.path, '/interface/control');
  });

  test(
    'resolveInterfaceControlPlaneTarget returns remote websocket target',
    () {
      final target = resolveInterfaceControlPlaneTarget(
        controlPlaneUrl: 'https://aware.run/interface/control',
      );

      expect(target.isRemote, isTrue);
      expect(target.controlPlaneUrl, 'https://aware.run/interface/control');
      expect(target.controlPlaneUri?.scheme, 'wss');
      expect(target.controlPlaneUri?.host, 'aware.run');
      expect(target.source, InterfaceControlPlaneBootstrapSource.explicit);
      expect(target.transportLabel, 'remote_websocket');
    },
  );

  test(
    'resolveInterfaceControlPlaneTarget falls back to local socket target',
    () {
      final target = resolveInterfaceControlPlaneTarget(
        socketPath: '/tmp/interface.sock',
      );

      expect(target.isRemote, isFalse);
      expect(target.socketPath, '/tmp/interface.sock');
      expect(target.source, InterfaceControlPlaneBootstrapSource.explicit);
      expect(target.transportLabel, 'local_socket');
    },
  );

  test('client tolerates legacy ping freshness fields being null', () async {
    if (Platform.isWindows) {
      return;
    }

    final tempDir = await Directory.systemTemp.createTemp(
      'aware-interface-control-dart-ping-legacy-',
    );
    final socketPath = p.join(tempDir.path, 'interface-control.sock');
    final server = await ServerSocket.bind(
      InternetAddress(socketPath, type: InternetAddressType.unix),
      0,
    );

    addTearDown(() async {
      await server.close();
      if (File(socketPath).existsSync()) {
        await File(socketPath).delete();
      }
      await tempDir.delete(recursive: true);
    });

    server.listen((Socket socket) {
      socket
          .cast<List<int>>()
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((String line) async {
        final operation = InterfaceControlPlaneOperation.fromJson(
          Map<String, dynamic>.from(jsonDecode(line) as Map),
        );
        final request = operation.request;
        expect(request, isA<PingRequest>());
        socket.write(
          jsonEncode(<String, dynamic>{
            'response': <String, dynamic>{
              'operation': 'ping',
              'request_id': null,
              'protocol_version': 1,
              'success': true,
              'error': null,
              'service': 'aware_interface_service',
              'status': 'ok',
              'socket_path': socketPath,
              'daemon_instance_id': null,
              'daemon_started_at': null,
              'daemon_source_fingerprint': null,
              'repository_root': null,
              'state_home': null,
              'default_endpoint': null,
              'expected_source_fingerprint': null,
              'restart_recommended': null,
              'restart_reason': null,
              'namespaces': <dynamic>[],
            },
          }),
        );
        socket.write('\n');
        await socket.flush();
        await socket.close();
      });
    });

    final client = InterfaceControlPlaneClient(socketPath: socketPath);
    final response = await client.ping();
    expect(response.restartRecommended, isFalse);
    expect(response.restartReason, isNull);
    expect(response.expectedSourceFingerprint, isNull);
  });

  test('client can use an injected control-plane transport', () async {
    final transport = _FakeInterfaceControlPlaneTransport(
      lines: <String>[
        jsonEncode(
          InterfaceControlPlaneOperation(
            response: InterfaceControlPlaneResponse.ping(
              requestId: UuidValue.fromString(const Uuid().v4()),
              protocolVersion: 1,
              success: true,
              service: 'aware_interface_service',
              status: 'ok',
              restartRecommended: false,
            ),
          ).toJson(),
        ),
      ],
    );

    final client = InterfaceControlPlaneClient(transport: transport);
    final response = await client.ping();

    expect(response.service, 'aware_interface_service');
    expect(response.status, 'ok');
    expect(transport.writtenLines, hasLength(1));
    expect(
      InterfaceControlPlaneOperation.fromJson(
        Map<String, dynamic>.from(
          jsonDecode(transport.writtenLines.single) as Map,
        ),
      ).request,
      isA<PingRequest>(),
    );
  });

  test(
    'client sends interface_action with canonical action target fields',
    () async {
      final hostState = _hostState(
        namespace: 'flutter-test',
        screenKey: 'identity_auth_gate',
        title: 'Identity Admission',
        message: 'Ready',
      );
      final transport = _FakeInterfaceControlPlaneTransport(
        lines: <String>[
          jsonEncode(
            InterfaceControlPlaneOperation(
              response: InterfaceControlPlaneResponse.interfaceAction(
                requestId: UuidValue.fromString(const Uuid().v4()),
                protocolVersion: 1,
                success: true,
                namespace: 'flutter-test',
                paneRef: 'main/coordination_center/orchestration',
                actionKey: 'sdk:example_sdk.run_action',
                hostState: hostState,
              ),
            ).toJson(),
          ),
        ],
      );

      final client = InterfaceControlPlaneClient(transport: transport);
      final response = await client.action(
        namespace: 'flutter-test',
        paneRef: 'main/coordination_center/orchestration',
        actionKey: 'sdk:example_sdk.run_action',
        actionTarget: const InterfaceActionTargetTransport(
          actionKey: 'sdk:example_sdk.run_action',
          actionKind: 'sdk_operation',
          operationRef: 'example_sdk.run_action',
          sdkOperationId: 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
          paneConfigSdkOperationId: 'ffffffff-ffff-4fff-8fff-ffffffffffff',
        ),
        payload: const <String, dynamic>{'public_key': 'ed25519:test'},
      );

      expect(response.actionKey, 'sdk:example_sdk.run_action');
      expect(transport.writtenLines, hasLength(1));
      final envelope = Map<String, dynamic>.from(
        jsonDecode(transport.writtenLines.single) as Map,
      );
      final rawRequest = Map<String, dynamic>.from(envelope['request'] as Map);
      expect(rawRequest['operation'], 'interface_action');
      expect(rawRequest['namespace'], 'flutter-test');
      expect(rawRequest['pane_ref'], 'main/coordination_center/orchestration');
      expect(rawRequest['action_key'], 'sdk:example_sdk.run_action');
      expect(rawRequest['action_kind'], 'sdk_operation');
      expect(rawRequest['operation_ref'], 'example_sdk.run_action');
      expect(
        rawRequest['sdk_operation_id'],
        'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
      );
      expect(
        rawRequest['pane_config_sdk_operation_id'],
        'ffffffff-ffff-4fff-8fff-ffffffffffff',
      );
      expect(rawRequest['payload'], <String, dynamic>{
        'public_key': 'ed25519:test',
      });
      final typedRequest = InterfaceControlPlaneOperation.fromJson(
        envelope,
      ).request;
      expect(typedRequest, isA<InterfaceActionRequest>());
      final actionRequest = typedRequest! as InterfaceActionRequest;
      expect(actionRequest.actionKind, 'sdk_operation');
      expect(actionRequest.operationRef, 'example_sdk.run_action');
      expect(
        actionRequest.sdkOperationId,
        'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
      );
      expect(
        actionRequest.paneConfigSdkOperationId,
        'ffffffff-ffff-4fff-8fff-ffffffffffff',
      );
    },
  );

  test(
    'client joins environment session through typed control plane',
    () async {
      final hostState = _hostState(
        namespace: 'flutter-test',
        screenKey: 'coordination',
        title: 'Coordination',
        message: 'Joined',
      );
      final environmentSessionId = UuidValue.fromString(
        '77777777-7777-4777-8777-777777777777',
      );
      final transport = _FakeInterfaceControlPlaneTransport(
        lines: <String>[
          jsonEncode(
            InterfaceControlPlaneOperation(
              response:
                  InterfaceControlPlaneResponse.interfaceJoinEnvironmentSession(
                protocolVersion: 1,
                success: true,
                namespace: 'flutter-test',
                hostState: hostState,
              ),
            ).toJson(),
          ),
        ],
      );

      final client = InterfaceControlPlaneClient(transport: transport);
      final response = await client.joinEnvironmentSession(
        namespace: 'flutter-test',
        environmentSessionId: environmentSessionId,
        reason: 'join coordination session',
        evidence: const <String, dynamic>{'source': 'dart-test'},
      );

      expect(response.hostState?.namespace, 'flutter-test');
      expect(transport.writtenLines, hasLength(1));
      final operation = InterfaceControlPlaneOperation.fromJson(
        Map<String, dynamic>.from(
          jsonDecode(transport.writtenLines.single) as Map,
        ),
      );
      final request = operation.request;
      expect(request, isA<InterfaceJoinEnvironmentSessionRequest>());
      final joinRequest = request! as InterfaceJoinEnvironmentSessionRequest;
      expect(joinRequest.namespace, 'flutter-test');
      expect(joinRequest.environmentSessionId, environmentSessionId);
      expect(joinRequest.reason, 'join coordination session');
      expect(joinRequest.evidence['source'], 'dart-test');
    },
  );

  test('client enters environment through typed control plane', () async {
    final hostState = _hostState(
      namespace: 'flutter-test',
      screenKey: 'coordination',
      title: 'Coordination',
      message: 'Entered',
    );
    final environmentProfileId = UuidValue.fromString(
      '11111111-1111-4111-8111-111111111111',
    );
    final actorConfigId = UuidValue.fromString(
      '22222222-2222-4222-8222-222222222222',
    );
    final classInstanceIdentityId = UuidValue.fromString(
      '33333333-3333-4333-8333-333333333333',
    );
    final environmentSessionConfigId = UuidValue.fromString(
      '44444444-4444-4444-8444-444444444444',
    );
    final transport = _FakeInterfaceControlPlaneTransport(
      lines: <String>[
        jsonEncode(
          InterfaceControlPlaneOperation(
            response: InterfaceControlPlaneResponse.interfaceEnterEnvironment(
              protocolVersion: 1,
              success: true,
              namespace: 'flutter-test',
              hostState: hostState,
            ),
          ).toJson(),
        ),
      ],
    );

    final client = InterfaceControlPlaneClient(transport: transport);
    final response = await client.enterEnvironment(
      namespace: 'flutter-test',
      environmentProfileId: environmentProfileId,
      actorConfigId: actorConfigId,
      classInstanceIdentityId: classInstanceIdentityId,
      objectInstanceGraphBranchKey: 'all',
      environmentSessionConfigId: environmentSessionConfigId,
      sessionKey: 'coordination-default',
      reason: 'enter environment',
      evidence: const <String, dynamic>{'source': 'dart-test'},
    );

    expect(response.hostState?.namespace, 'flutter-test');
    expect(transport.writtenLines, hasLength(1));
    final envelope = Map<String, dynamic>.from(
      jsonDecode(transport.writtenLines.single) as Map,
    );
    final rawRequest = Map<String, dynamic>.from(envelope['request'] as Map);
    expect(rawRequest['operation'], 'interface_enter_environment');
    expect(rawRequest.containsKey('selected_process_id'), isFalse);
    expect(rawRequest.containsKey('selected_thread_id'), isFalse);
    final request = InterfaceControlPlaneOperation.fromJson(envelope).request;
    expect(request, isA<InterfaceEnterEnvironmentRequest>());
    final enterRequest = request! as InterfaceEnterEnvironmentRequest;
    expect(enterRequest.namespace, 'flutter-test');
    expect(enterRequest.environmentProfileId, environmentProfileId);
    expect(enterRequest.actorConfigId, actorConfigId);
    expect(enterRequest.classInstanceIdentityId, classInstanceIdentityId);
    expect(enterRequest.environmentSessionConfigId, environmentSessionConfigId);
    expect(enterRequest.sessionKey, 'coordination-default');
    expect(enterRequest.reason, 'enter environment');
    expect(enterRequest.evidence['source'], 'dart-test');
  });

  test(
    'client reports renderer capabilities through typed control plane',
    () async {
      final capabilities = _rendererCapabilities();
      final hostState = _hostState(
        namespace: 'flutter-test',
        screenKey: 'workspace_runtime',
        title: 'Runtime',
        message: 'Ready',
      ).copyWith(rendererCapabilities: capabilities);
      final transport = _FakeInterfaceControlPlaneTransport(
        lines: <String>[
          jsonEncode(
            InterfaceControlPlaneOperation(
              response: InterfaceControlPlaneResponse
                  .interfaceReportRendererCapabilities(
                protocolVersion: 1,
                success: true,
                namespace: 'flutter-test',
                hostState: hostState,
              ),
            ).toJson(),
          ),
        ],
      );

      final client = InterfaceControlPlaneClient(transport: transport);
      final response = await client.reportRendererCapabilities(
        namespace: 'flutter-test',
        rendererCapabilities: capabilities,
      );

      expect(
        response.hostState?.rendererCapabilities?.rendererId,
        'flutter-test-renderer',
      );
      final operation = InterfaceControlPlaneOperation.fromJson(
        Map<String, dynamic>.from(
          jsonDecode(transport.writtenLines.single) as Map,
        ),
      );
      final request = operation.request;
      expect(request, isA<InterfaceReportRendererCapabilitiesRequest>());
      final reportRequest =
          request! as InterfaceReportRendererCapabilitiesRequest;
      expect(reportRequest.namespace, 'flutter-test');
      expect(
        reportRequest.rendererCapabilities?.viewCapabilities.single.hasDecoder,
        isTrue,
      );
    },
  );

  test('client sends one complete Attention layout transition vector',
      () async {
    final hostState = _hostState(
      namespace: 'flutter-test',
      screenKey: 'workspace_runtime',
      title: 'Runtime',
      message: 'Ready',
    );
    final transport = _FakeInterfaceControlPlaneTransport(
      lines: <String>[
        jsonEncode(
          InterfaceControlPlaneOperation(
            response: InterfaceControlPlaneResponse
                .interfaceApplyAttentionLayoutTransition(
              protocolVersion: 1,
              success: true,
              namespace: 'flutter-test',
              outcome: 'committed',
              activeLayoutTransitionId: UuidValue.fromString(
                'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
              ),
              graphHashPost: 'sha256:layout',
              hostState: hostState,
            ),
          ).toJson(),
        ),
      ],
    );
    final sectionId = UuidValue.fromString(
      '11111111-1111-4111-8111-111111111111',
    );
    final client = InterfaceControlPlaneClient(transport: transport);

    final response = await client.applyAttentionLayoutTransition(
      namespace: 'flutter-test',
      clientIntentId: 'drag-1',
      expectedPreviousLayoutTransitionId: UuidValue.fromString(
        '99999999-9999-4999-8999-999999999999',
      ),
      topologyTransitionId: UuidValue.fromString(
        '88888888-8888-4888-8888-888888888888',
      ),
      sectionStates: <InterfaceAttentionLayoutTransitionSectionIntent>[
        InterfaceAttentionLayoutTransitionSectionIntent(
          layoutConfigSectionConfigId: sectionId,
          order: 0,
          weightMicros: 1000000,
        ),
      ],
    );

    expect(response.outcome, 'committed');
    expect(response.graphHashPost, 'sha256:layout');
    expect(transport.writtenLines, hasLength(1));
    final operation = InterfaceControlPlaneOperation.fromJson(
      Map<String, dynamic>.from(
        jsonDecode(transport.writtenLines.single) as Map,
      ),
    );
    final request = operation.request;
    expect(request, isA<InterfaceApplyAttentionLayoutTransitionRequest>());
    final transitionRequest =
        request! as InterfaceApplyAttentionLayoutTransitionRequest;
    expect(transitionRequest.clientIntentId, 'drag-1');
    expect(
      transitionRequest.topologyTransitionId?.uuid,
      '88888888-8888-4888-8888-888888888888',
    );
    expect(transitionRequest.sectionStates, hasLength(1));
    expect(
      transitionRequest.sectionStates.single.layoutConfigSectionConfigId,
      sectionId,
    );
  });

  test('client sends one complete Attention topology transition vector',
      () async {
    final hostState = _hostState(
      namespace: 'flutter-test',
      screenKey: 'workspace_runtime',
      title: 'Runtime',
      message: 'Ready',
    );
    final transport = _FakeInterfaceControlPlaneTransport(
      lines: <String>[
        jsonEncode(
          InterfaceControlPlaneOperation(
            response: InterfaceControlPlaneResponse
                .interfaceApplyAttentionLayoutTopologyTransition(
              protocolVersion: 1,
              success: true,
              namespace: 'flutter-test',
              outcome: 'committed',
              activeTopologyTransitionId: UuidValue.fromString(
                'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
              ),
              graphHashPost: 'sha256:topology',
              hostState: hostState,
            ),
          ).toJson(),
        ),
      ],
    );
    final sectionId = UuidValue.fromString(
      '11111111-1111-4111-8111-111111111111',
    );
    final client = InterfaceControlPlaneClient(transport: transport);

    final response = await client.applyAttentionLayoutTopologyTransition(
      namespace: 'flutter-test',
      clientIntentId: 'topology-1',
      expectedPreviousTopologyTransitionId: UuidValue.fromString(
        '99999999-9999-4999-8999-999999999999',
      ),
      sectionStates: <InterfaceAttentionLayoutTopologyTransitionSectionIntent>[
        InterfaceAttentionLayoutTopologyTransitionSectionIntent(
          layoutConfigSectionConfigId: sectionId,
          order: 0,
        ),
      ],
    );

    expect(response.outcome, 'committed');
    expect(response.graphHashPost, 'sha256:topology');
    expect(transport.writtenLines, hasLength(1));
    final operation = InterfaceControlPlaneOperation.fromJson(
      Map<String, dynamic>.from(
        jsonDecode(transport.writtenLines.single) as Map,
      ),
    );
    final request = operation.request;
    expect(
      request,
      isA<InterfaceApplyAttentionLayoutTopologyTransitionRequest>(),
    );
    final transitionRequest =
        request! as InterfaceApplyAttentionLayoutTopologyTransitionRequest;
    expect(transitionRequest.clientIntentId, 'topology-1');
    expect(
      transitionRequest.expectedPreviousTopologyTransitionId?.uuid,
      '99999999-9999-4999-8999-999999999999',
    );
    expect(transitionRequest.sectionStates, hasLength(1));
    expect(
      transitionRequest.sectionStates.single.layoutConfigSectionConfigId,
      sectionId,
    );
  });

  test(
    'client labels failed environment admission response branches',
    () async {
      final admissionTransport = _FakeInterfaceControlPlaneTransport(
        lines: <String>[
          jsonEncode(
            InterfaceControlPlaneOperation(
              response:
                  InterfaceControlPlaneResponse.interfaceAdmitEnvironmentActor(
                protocolVersion: 1,
                success: false,
                namespace: 'flutter-test',
                hostState: _hostState(
                  namespace: 'flutter-test',
                  screenKey: 'identity_auth_gate',
                  title: 'Identity Admission',
                  message: 'Actor context missing',
                ),
                error: 'actor context missing',
              ),
            ).toJson(),
          ),
        ],
      );
      final admissionClient = InterfaceControlPlaneClient(
        transport: admissionTransport,
      );

      await expectLater(
        () => admissionClient.status(namespace: 'flutter-test'),
        throwsA(
          isA<InterfaceControlPlaneClientError>()
              .having(
                (error) => error.operation,
                'operation',
                'interface_admit_environment_actor',
              )
              .having((error) => error.error, 'error', 'actor context missing'),
        ),
      );

      final lensTransport = _FakeInterfaceControlPlaneTransport(
        lines: <String>[
          jsonEncode(
            InterfaceControlPlaneOperation(
              response:
                  InterfaceControlPlaneResponse.interfaceResolveExperienceLens(
                protocolVersion: 1,
                success: false,
                namespace: 'flutter-test',
                hostState: _hostState(
                  namespace: 'flutter-test',
                  screenKey: 'experience_lens',
                  title: 'Experience Lens',
                  message: 'Environment session missing',
                ),
                error: 'environment session missing',
              ),
            ).toJson(),
          ),
        ],
      );
      final lensClient = InterfaceControlPlaneClient(transport: lensTransport);

      await expectLater(
        () => lensClient.status(namespace: 'flutter-test'),
        throwsA(
          isA<InterfaceControlPlaneClientError>()
              .having(
                (error) => error.operation,
                'operation',
                'interface_resolve_experience_lens',
              )
              .having(
                (error) => error.error,
                'error',
                'environment session missing',
              ),
        ),
      );
    },
  );

  test(
    'client syncs host view-state cursor through typed control plane',
    () async {
      final cursor = _viewStateCursor();
      final hostState = _hostState(
        namespace: 'flutter-test',
        screenKey: 'workspace_runtime',
        title: 'Runtime',
        message: 'Ready',
      ).copyWith(
        runtime: InterfaceRuntimeState(
          backend: _testBackendState(),
          viewStateCursor: cursor,
        ),
      );
      final transport = _FakeInterfaceControlPlaneTransport(
        lines: <String>[
          jsonEncode(
            InterfaceControlPlaneOperation(
              response:
                  InterfaceControlPlaneResponse.interfaceSyncViewStateCursor(
                protocolVersion: 1,
                success: true,
                namespace: 'flutter-test',
                changed: false,
                viewStateCursor: cursor,
                hostState: hostState,
              ),
            ).toJson(),
          ),
        ],
      );

      final client = InterfaceControlPlaneClient(transport: transport);
      final response = await client.syncViewStateCursor(
        namespace: 'flutter-test',
        rendererId: 'flutter-test-renderer',
        knownCursor: 'view-state:digest-1',
        knownDigest: 'digest-1',
      );

      expect(response.changed, isFalse);
      expect(response.viewStateCursor?.cursor, 'view-state:digest-1');
      final operation = InterfaceControlPlaneOperation.fromJson(
        Map<String, dynamic>.from(
          jsonDecode(transport.writtenLines.single) as Map,
        ),
      );
      final request = operation.request;
      expect(request, isA<InterfaceSyncViewStateCursorRequest>());
      final syncRequest = request! as InterfaceSyncViewStateCursorRequest;
      expect(syncRequest.namespace, 'flutter-test');
      expect(syncRequest.rendererId, 'flutter-test-renderer');
      expect(syncRequest.knownCursor, 'view-state:digest-1');
      expect(syncRequest.knownDigest, 'digest-1');
    },
  );

  test('client can use a websocket control-plane transport', () async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);

    addTearDown(() async {
      await server.close(force: true);
    });

    server.listen((HttpRequest request) async {
      final socket = await WebSocketTransformer.upgrade(request);
      socket.listen((dynamic message) async {
        final operation = InterfaceControlPlaneOperation.fromJson(
          Map<String, dynamic>.from(jsonDecode(message as String) as Map),
        );
        final request = operation.request;
        expect(request, isA<PingRequest>());
        socket.add(
          jsonEncode(
            InterfaceControlPlaneOperation(
              response: InterfaceControlPlaneResponse.ping(
                requestId: request?.requestId,
                protocolVersion: 1,
                success: true,
                service: 'aware_interface_service',
                status: 'ok',
                restartRecommended: false,
              ),
            ).toJson(),
          ),
        );
        await socket.close();
      });
    });

    final client = InterfaceControlPlaneClient(
      controlPlaneUri: Uri(
        scheme: 'ws',
        host: server.address.address,
        port: server.port,
        path: '/control',
      ),
    );
    final response = await client.ping();

    expect(response.service, 'aware_interface_service');
    expect(response.status, 'ok');
    expect(client.controlPlaneUri?.scheme, 'ws');
    expect(client.socketPath, isNull);
  });

  test('client handles status and follow over the local socket', () async {
    if (Platform.isWindows) {
      return;
    }

    final tempDir = await Directory.systemTemp.createTemp(
      'aware-interface-control-dart-',
    );
    final socketPath = p.join(tempDir.path, 'interface-control.sock');
    final server = await ServerSocket.bind(
      InternetAddress(socketPath, type: InternetAddressType.unix),
      0,
    );

    addTearDown(() async {
      await server.close();
      if (File(socketPath).existsSync()) {
        await File(socketPath).delete();
      }
      await tempDir.delete(recursive: true);
    });

    final firstHostState = _hostState(
      namespace: 'flutter-test',
      screenKey: 'local_service_host_gate',
      title: 'Local Service Host Required',
      message: 'Start the local service host to continue.',
    );
    final secondHostState = _hostState(
      namespace: 'flutter-test',
      screenKey: 'local_node_runtime_gate',
      title: 'Local Node Required',
      message: 'Start the local node runtime to continue.',
    );

    server.listen((Socket socket) {
      socket
          .cast<List<int>>()
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((String line) async {
        final operation = InterfaceControlPlaneOperation.fromJson(
          Map<String, dynamic>.from(jsonDecode(line) as Map),
        );

        final request = operation.request;
        expect(request, isNotNull);

        if (request is InterfaceStatusRequest) {
          socket.write(
            jsonEncode(
              InterfaceControlPlaneOperation(
                response: InterfaceControlPlaneResponse.interfaceStatus(
                  requestId: request.requestId,
                  protocolVersion: 1,
                  success: true,
                  namespace: request.namespace,
                  hostState: firstHostState,
                ),
              ).toJson(),
            ),
          );
          socket.write('\n');
          await socket.flush();
          await socket.close();
          return;
        }

        if (request is InterfaceFollowRequest) {
          socket.write(
            jsonEncode(
              InterfaceControlPlaneOperation(
                response: InterfaceControlPlaneResponse.interfaceFollow(
                  requestId: request.requestId,
                  protocolVersion: 1,
                  success: true,
                  namespace: request.namespace,
                  hostState: firstHostState,
                ),
              ).toJson(),
            ),
          );
          socket.write('\n');
          socket.write(
            jsonEncode(
              InterfaceControlPlaneOperation(
                notification: InterfaceControlPlaneNotification.interfaceState(
                  notificationId: request.requestId,
                  protocolVersion: 1,
                  namespace: request.namespace,
                  hostState: secondHostState,
                ),
              ).toJson(),
            ),
          );
          socket.write('\n');
          await socket.flush();
          await socket.close();
          return;
        }

        fail('Unexpected request: $request');
      });
    });

    final client = InterfaceControlPlaneClient(socketPath: socketPath);

    final status = await client.status(namespace: 'flutter-test');
    expect(
      status.hostState?.currentScreen?.screenKey,
      'local_service_host_gate',
    );

    final followFrames = await client
        .follow(namespace: 'flutter-test', pollIntervalMs: 25)
        .take(2)
        .toList();
    expect(followFrames, hasLength(2));
    expect(
      followFrames.first.currentScreen?.screenKey,
      'local_service_host_gate',
    );
    expect(
      followFrames.last.currentScreen?.screenKey,
      'local_node_runtime_gate',
    );
  });

  test(
    'client sends interface_invoke_api and returns the typed response',
    () async {
      if (Platform.isWindows) {
        return;
      }

      final tempDir = await Directory.systemTemp.createTemp(
        'aware-interface-control-dart-invoke-api-',
      );
      final socketPath = p.join(tempDir.path, 'interface-control.sock');
      final server = await ServerSocket.bind(
        InternetAddress(socketPath, type: InternetAddressType.unix),
        0,
      );

      addTearDown(() async {
        await server.close();
        if (File(socketPath).existsSync()) {
          await File(socketPath).delete();
        }
        await tempDir.delete(recursive: true);
      });

      server.listen((Socket socket) {
        socket
            .cast<List<int>>()
            .transform(utf8.decoder)
            .transform(const LineSplitter())
            .listen((String line) async {
          final operation = InterfaceControlPlaneOperation.fromJson(
            Map<String, dynamic>.from(jsonDecode(line) as Map),
          );
          final request = operation.request;
          expect(request, isA<InterfaceInvokeApiRequest>());
          final invokeRequest = request! as InterfaceInvokeApiRequest;
          expect(invokeRequest.namespace, 'flutter-test');
          expect(invokeRequest.endpointRef, 'agent/session/start_session');
          expect(invokeRequest.discriminant, 'start_session');
          expect(invokeRequest.requestPayload, {'prompt': 'hello'});
          socket.write(
            jsonEncode(
              InterfaceControlPlaneOperation(
                response: InterfaceControlPlaneResponse.interfaceInvokeApi(
                  requestId: invokeRequest.requestId,
                  protocolVersion: 1,
                  success: true,
                  namespace: invokeRequest.namespace,
                  endpointRef: invokeRequest.endpointRef,
                  discriminant: invokeRequest.discriminant,
                  serviceStatus: 'succeeded',
                  responsePayload: <String, dynamic>{
                    'agent_session_id': 'session-1',
                  },
                ),
              ).toJson(),
            ),
          );
          socket.write('\n');
          await socket.flush();
          await socket.close();
        });
      });

      final client = InterfaceControlPlaneClient(socketPath: socketPath);
      final response = await client.invokeApi(
        namespace: 'flutter-test',
        endpointRef: 'agent/session/start_session',
        discriminant: 'start_session',
        requestPayload: <String, dynamic>{'prompt': 'hello'},
      );
      expect(response.serviceStatus, 'succeeded');
      expect(response.responsePayload, <String, dynamic>{
        'agent_session_id': 'session-1',
      });
    },
  );

  test(
    'client opens interface_stream_api and yields typed event notifications',
    () async {
      if (Platform.isWindows) {
        return;
      }

      final tempDir = await Directory.systemTemp.createTemp(
        'aware-interface-control-dart-stream-api-',
      );
      final socketPath = p.join(tempDir.path, 'interface-control.sock');
      final server = await ServerSocket.bind(
        InternetAddress(socketPath, type: InternetAddressType.unix),
        0,
      );

      addTearDown(() async {
        await server.close();
        if (File(socketPath).existsSync()) {
          await File(socketPath).delete();
        }
        await tempDir.delete(recursive: true);
      });

      server.listen((Socket socket) {
        socket
            .cast<List<int>>()
            .transform(utf8.decoder)
            .transform(const LineSplitter())
            .listen((String line) async {
          final operation = InterfaceControlPlaneOperation.fromJson(
            Map<String, dynamic>.from(jsonDecode(line) as Map),
          );
          final request = operation.request;
          expect(request, isA<InterfaceStreamApiRequest>());
          final streamRequest = request! as InterfaceStreamApiRequest;
          expect(streamRequest.namespace, 'flutter-test');
          expect(
            streamRequest.endpointRef,
            'agent/session/subscribe_session',
          );
          expect(streamRequest.discriminant, 'subscribe_session');
          expect(streamRequest.requestPayload, <String, dynamic>{
            'agent_session_id': 'session-1',
          });

          socket.write(
            jsonEncode(
              InterfaceControlPlaneOperation(
                response: InterfaceControlPlaneResponse.interfaceStreamApi(
                  requestId: streamRequest.requestId,
                  protocolVersion: 1,
                  success: true,
                  namespace: streamRequest.namespace,
                  endpointRef: streamRequest.endpointRef,
                  discriminant: streamRequest.discriminant,
                ),
              ).toJson(),
            ),
          );
          socket.write('\n');
          socket.write(
            jsonEncode(
              InterfaceControlPlaneOperation(
                notification:
                    InterfaceControlPlaneNotification.interfaceApiEvent(
                  notificationId: streamRequest.requestId,
                  protocolVersion: 1,
                  namespace: streamRequest.namespace,
                  endpointRef: streamRequest.endpointRef,
                  discriminant: streamRequest.discriminant,
                  eventKind: 'delta',
                  sequence: 1,
                  itemKey: 'turn-1',
                  payload: <String, dynamic>{'delta': 'hello'},
                ),
              ).toJson(),
            ),
          );
          socket.write('\n');
          socket.write(
            jsonEncode(
              InterfaceControlPlaneOperation(
                notification:
                    InterfaceControlPlaneNotification.interfaceApiStreamClosed(
                  notificationId: streamRequest.requestId,
                  protocolVersion: 1,
                  namespace: streamRequest.namespace,
                  endpointRef: streamRequest.endpointRef,
                  discriminant: streamRequest.discriminant,
                  serviceStatus: 'succeeded',
                  responsePayload: <String, dynamic>{'closed': true},
                  error: null,
                ),
              ).toJson(),
            ),
          );
          socket.write('\n');
          await socket.flush();
          await socket.close();
        });
      });

      final client = InterfaceControlPlaneClient(socketPath: socketPath);
      final handle = await client.openApiStream(
        namespace: 'flutter-test',
        endpointRef: 'agent/session/subscribe_session',
        discriminant: 'subscribe_session',
        requestPayload: <String, dynamic>{'agent_session_id': 'session-1'},
      );

      final events = await handle.events.toList();
      final terminal = await handle.response;
      expect(events, hasLength(1));
      expect(events.first.eventKind, 'delta');
      expect(events.first.sequence, 1);
      expect(events.first.itemKey, 'turn-1');
      expect(events.first.payload, <String, dynamic>{'delta': 'hello'});
      expect(terminal.serviceStatus, 'succeeded');
      expect(terminal.responsePayload, <String, dynamic>{'closed': true});
      await handle.close();
    },
  );

  test('client sends interface_select_step and returns host state', () async {
    if (Platform.isWindows) {
      return;
    }

    final tempDir = await Directory.systemTemp.createTemp(
      'aware-interface-control-dart-select-step-',
    );
    final socketPath = p.join(tempDir.path, 'interface-control.sock');
    final server = await ServerSocket.bind(
      InternetAddress(socketPath, type: InternetAddressType.unix),
      0,
    );

    addTearDown(() async {
      await server.close();
      if (File(socketPath).existsSync()) {
        await File(socketPath).delete();
      }
      await tempDir.delete(recursive: true);
    });

    final selectedHostState = _hostState(
      namespace: 'flutter-test',
      screenKey: 'local_node_runtime_gate',
      title: 'Local Node Required',
      message: 'Selected step moved to environment.',
    ).copyWith(
      controlPlaneWorkspace: InterfaceControlPlaneWorkspaceState(
        selectedStepId: 'environment',
        currentStepId: 'bundle',
        orchestrationSteps: <InterfaceControlPlaneOrchestrationStep>[
          InterfaceControlPlaneOrchestrationStep(
            stepId: 'bundle',
            title: 'Environment Bundle',
            kind: 'bundle',
            status: 'running',
            phase: 'starting_bundle',
            summary: 'Bundle is still preparing.',
            current: true,
            selected: false,
          ),
          InterfaceControlPlaneOrchestrationStep(
            stepId: 'environment',
            title: 'Aware Environment',
            kind: 'service',
            status: 'waiting',
            phase: 'waiting_targets',
            summary: 'Environment is still warming up.',
            current: false,
            selected: true,
          ),
        ],
      ),
    );

    server.listen((Socket socket) {
      socket
          .cast<List<int>>()
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((String line) async {
        final operation = InterfaceControlPlaneOperation.fromJson(
          Map<String, dynamic>.from(jsonDecode(line) as Map),
        );
        final request = operation.request;
        expect(request, isA<InterfaceSelectStepRequest>());
        final selectRequest = request! as InterfaceSelectStepRequest;
        expect(selectRequest.namespace, 'flutter-test');
        expect(selectRequest.stepId, 'environment');
        socket.write(
          jsonEncode(
            InterfaceControlPlaneOperation(
              response: InterfaceControlPlaneResponse.interfaceSelectStep(
                requestId: selectRequest.requestId,
                protocolVersion: 1,
                success: true,
                namespace: selectRequest.namespace,
                stepId: selectRequest.stepId,
                hostState: selectedHostState,
              ),
            ).toJson(),
          ),
        );
        socket.write('\n');
        await socket.flush();
        await socket.close();
      });
    });

    final client = InterfaceControlPlaneClient(socketPath: socketPath);
    final response = await client.selectStep(
      namespace: 'flutter-test',
      stepId: 'environment',
    );
    expect(response.stepId, 'environment');
    expect(
      response.hostState?.controlPlaneWorkspace?.selectedStepId,
      'environment',
    );
  });

  test(
    'client sends interface_select_profile and returns host state',
    () async {
      if (Platform.isWindows) {
        return;
      }

      final tempDir = await Directory.systemTemp.createTemp(
        'aware-interface-control-dart-select-profile-',
      );
      final socketPath = p.join(tempDir.path, 'interface-control.sock');
      final server = await ServerSocket.bind(
        InternetAddress(socketPath, type: InternetAddressType.unix),
        0,
      );

      addTearDown(() async {
        await server.close();
        if (File(socketPath).existsSync()) {
          await File(socketPath).delete();
        }
        await tempDir.delete(recursive: true);
      });

      final selectedHostState = _hostState(
        namespace: 'flutter-test',
        screenKey: 'identity_auth_gate',
        title: 'Identity/Auth Required',
        message: 'Consumer admission selected.',
      ).copyWith(
        controlPlaneProfiles: InterfaceControlPlaneProfilesState(
          activeProfileId: 'consumer.remote_admission',
          profiles: <InterfaceControlPlaneProfileState>[
            InterfaceControlPlaneProfileState(
              profileId: 'operator.local_bootstrap',
              title: 'Operator Bootstrap',
              kind: 'operator',
              selected: false,
            ),
            InterfaceControlPlaneProfileState(
              profileId: 'consumer.remote_admission',
              title: 'Consumer Admission',
              kind: 'consumer',
              selected: true,
            ),
          ],
        ),
      );

      server.listen((Socket socket) {
        socket
            .cast<List<int>>()
            .transform(utf8.decoder)
            .transform(const LineSplitter())
            .listen((String line) async {
          final operation = InterfaceControlPlaneOperation.fromJson(
            Map<String, dynamic>.from(jsonDecode(line) as Map),
          );
          final request = operation.request;
          expect(request, isA<InterfaceSelectProfileRequest>());
          final selectRequest = request! as InterfaceSelectProfileRequest;
          expect(selectRequest.namespace, 'flutter-test');
          expect(selectRequest.profileId, 'consumer.remote_admission');
          socket.write(
            jsonEncode(
              InterfaceControlPlaneOperation(
                response: InterfaceControlPlaneResponse.interfaceSelectProfile(
                  requestId: selectRequest.requestId,
                  protocolVersion: 1,
                  success: true,
                  namespace: selectRequest.namespace,
                  profileId: selectRequest.profileId,
                  hostState: selectedHostState,
                ),
              ).toJson(),
            ),
          );
          socket.write('\n');
          await socket.flush();
          await socket.close();
        });
      });

      final client = InterfaceControlPlaneClient(socketPath: socketPath);
      final response = await client.selectProfile(
        namespace: 'flutter-test',
        profileId: 'consumer.remote_admission',
      );
      expect(response.profileId, 'consumer.remote_admission');
      expect(
        response.hostState?.controlPlaneProfiles?.activeProfileId,
        'consumer.remote_admission',
      );
    },
  );

  test(
    'client sends interface_select_runtime_layout and returns host state',
    () async {
      if (Platform.isWindows) {
        return;
      }

      final tempDir = await Directory.systemTemp.createTemp(
        'aware-interface-control-dart-select-runtime-layout-',
      );
      final socketPath = p.join(tempDir.path, 'interface-control.sock');
      final server = await ServerSocket.bind(
        InternetAddress(socketPath, type: InternetAddressType.unix),
        0,
      );
      final layoutConfigId = UuidValue.fromString(
        '22222222-2222-2222-2222-222222222222',
      );

      addTearDown(() async {
        await server.close();
        if (File(socketPath).existsSync()) {
          await File(socketPath).delete();
        }
        await tempDir.delete(recursive: true);
      });

      final selectedHostState = _hostState(
        namespace: 'flutter-test',
        screenKey: 'workspace_runtime_layout',
        title: 'Workspace Layout',
        message: 'Graph view selected.',
      ).copyWith(
        runtime: InterfaceRuntimeState(
          backend: _testBackendState(),
          activeLayoutConfigId: layoutConfigId,
          resolvedView: InterfaceResolvedView(
            experienceKey: 'aware_workspace',
            projectionViewId: 'aware_workspace.graph.center',
            hostPayload: <String, dynamic>{
              'window_layout': <String, dynamic>{
                'window_key': 'main',
                'layout_config_id': layoutConfigId.uuid,
                'layout_key': 'graph_view',
                'sections': <Map<String, dynamic>>[
                  <String, dynamic>{'section_key': 'center', 'order': 0},
                ],
              },
            },
          ),
        ),
      );

      server.listen((Socket socket) {
        socket
            .cast<List<int>>()
            .transform(utf8.decoder)
            .transform(const LineSplitter())
            .listen((String line) async {
          final operation = InterfaceControlPlaneOperation.fromJson(
            Map<String, dynamic>.from(jsonDecode(line) as Map),
          );
          final request = operation.request;
          expect(request, isA<InterfaceSelectRuntimeLayoutRequest>());
          final selectRequest = request! as InterfaceSelectRuntimeLayoutRequest;
          expect(selectRequest.namespace, 'flutter-test');
          expect(selectRequest.layoutConfigId, layoutConfigId);
          socket.write(
            jsonEncode(
              InterfaceControlPlaneOperation(
                response:
                    InterfaceControlPlaneResponse.interfaceSelectRuntimeLayout(
                  requestId: selectRequest.requestId,
                  protocolVersion: 1,
                  success: true,
                  namespace: selectRequest.namespace,
                  layoutConfigId: selectRequest.layoutConfigId,
                  hostState: selectedHostState,
                ),
              ).toJson(),
            ),
          );
          socket.write('\n');
          await socket.flush();
          await socket.close();
        });
      });

      final client = InterfaceControlPlaneClient(socketPath: socketPath);
      final response = await client.selectRuntimeLayout(
        namespace: 'flutter-test',
        layoutConfigId: layoutConfigId,
      );
      expect(response.layoutConfigId, layoutConfigId);
      expect(
        response.hostState?.runtime?.resolvedView?.hostPayload['window_layout']
            as Map<String, dynamic>,
        containsPair('layout_key', 'graph_view'),
      );
      expect(
        response.hostState?.runtime?.resolvedView?.hostPayload['window_layout']
            ?['layout_config_id'],
        layoutConfigId.uuid,
      );
      expect(
        response.hostState?.runtime?.resolvedView?.hostPayload['window_layout']
            ?['layout_key'],
        'graph_view',
      );
    },
  );

  test(
    'client sends interface_activate_runtime_focus and returns host state',
    () async {
      if (Platform.isWindows) {
        return;
      }

      final tempDir = await Directory.systemTemp.createTemp(
        'aware-interface-control-dart-activate-runtime-focus-',
      );
      final socketPath = p.join(tempDir.path, 'interface-control.sock');
      final server = await ServerSocket.bind(
        InternetAddress(socketPath, type: InternetAddressType.unix),
        0,
      );
      final representationId = UuidValue.fromString(
        '77777777-7777-7777-7777-777777777777',
      );
      final layoutConfigId = UuidValue.fromString(
        '33333333-3333-3333-3333-333333333333',
      );
      const layoutKey = 'graph_view';
      const sectionKey = 'center';
      final selectedHostState = _hostState(
        namespace: 'flutter-test',
        screenKey: 'workspace_runtime_layout',
        title: 'Workspace Layout',
        message: 'graph_view',
      ).copyWith(
        runtime: InterfaceRuntimeState(
          backend: InterfaceBackendState(
            available: false,
            databaseExists: false,
            opgCount: 0,
            projectionBundleAvailable: false,
            projectionPlanCount: 0,
            tableCount: 0,
          ),
          activeLayoutConfigId: layoutConfigId,
          activeFocus: InterfaceRuntimeFocusState(
            layoutConfigId: layoutConfigId,
            layoutKey: layoutKey,
            sectionKey: sectionKey,
          ),
          resolvedView: InterfaceResolvedView(
            experienceKey: 'aware_workspace',
            projectionViewId: 'aware_workspace.graph.center',
            hostPayload: <String, dynamic>{
              'window_layout': <String, dynamic>{
                'window_key': 'main',
                'layout_config_id': layoutConfigId.uuid,
                'layout_key': layoutKey,
                'sections': <Map<String, dynamic>>[
                  <String, dynamic>{'section_key': sectionKey, 'order': 0},
                ],
              },
            },
          ),
        ),
      );

      server.listen((Socket socket) {
        socket
            .cast<List<int>>()
            .transform(utf8.decoder)
            .transform(const LineSplitter())
            .listen((String line) async {
          final operation = InterfaceControlPlaneOperation.fromJson(
            Map<String, dynamic>.from(jsonDecode(line) as Map),
          );
          final request = operation.request;
          expect(request, isA<InterfaceActivateRuntimeFocusRequest>());
          final activateRequest =
              request! as InterfaceActivateRuntimeFocusRequest;
          expect(activateRequest.namespace, 'flutter-test');
          expect(activateRequest.representationId, representationId);
          socket.write(
            jsonEncode(
              InterfaceControlPlaneOperation(
                response:
                    InterfaceControlPlaneResponse.interfaceActivateRuntimeFocus(
                  requestId: activateRequest.requestId,
                  protocolVersion: 1,
                  success: true,
                  namespace: activateRequest.namespace,
                  representationId: activateRequest.representationId,
                  layoutConfigId: layoutConfigId,
                  hostState: selectedHostState,
                ),
              ).toJson(),
            ),
          );
          socket.write('\n');
          await socket.flush();
          await socket.close();
        });
      });

      final client = InterfaceControlPlaneClient(socketPath: socketPath);
      final response = await client.activateRuntimeFocus(
        namespace: 'flutter-test',
        representationId: representationId,
      );
      expect(response.representationId, representationId);
      expect(response.layoutConfigId, layoutConfigId);
      expect(response.hostState?.runtime?.activeFocus?.sectionKey, sectionKey);
    },
  );

  test(
    'client sends interface_request_window_layout and returns host state',
    () async {
      if (Platform.isWindows) {
        return;
      }

      final tempDir = await Directory.systemTemp.createTemp(
        'aware-interface-control-dart-request-window-layout-',
      );
      final socketPath = p.join(tempDir.path, 'interface-control.sock');
      final server = await ServerSocket.bind(
        InternetAddress(socketPath, type: InternetAddressType.unix),
        0,
      );
      final interfacePackageId = UuidValue.fromString(
        '292f93ef-a026-5776-825c-5dfc6d9195fc',
      );
      final layoutConfigId = UuidValue.fromString(
        '33333333-3333-4333-8333-333333333333',
      );
      final observableId = UuidValue.fromString(
        '44444444-4444-4444-8444-444444444444',
      );
      final representationId = UuidValue.fromString(
        '77777777-7777-4777-8777-777777777777',
      );
      const interfacePackageName = 'aware-workspace-interface';
      const windowKey = 'main';
      const layoutKey = 'coordination_center';
      const sectionKey = 'primary';
      const requestedByService = 'identity';
      const requestedByOperation = 'admission';
      const reason = 'identity-admitted';
      const idempotencyKey = 'identity-admission:test';

      addTearDown(() async {
        await server.close();
        if (File(socketPath).existsSync()) {
          await File(socketPath).delete();
        }
        await tempDir.delete(recursive: true);
      });

      final selectedHostState = _hostState(
        namespace: 'flutter-test',
        screenKey: 'workspace_runtime_layout',
        title: 'Workspace Layout',
        message: 'coordination_center',
      ).copyWith(
        runtime: InterfaceRuntimeState(
          backend: _testBackendState(),
          activeLayoutConfigId: layoutConfigId,
          activeFocus: InterfaceRuntimeFocusState(
            layoutConfigId: layoutConfigId,
            layoutKey: layoutKey,
            sectionKey: sectionKey,
            observableId: observableId,
          ),
          resolvedView: InterfaceResolvedView(
            experienceKey: 'aware_workspace',
            projectionViewId: 'aware_workspace.coordination.primary',
            hostPayload: <String, dynamic>{
              'window_layout': <String, dynamic>{
                'window_key': windowKey,
                'interface_package_name': interfacePackageName,
                'layout_config_id': layoutConfigId.uuid,
                'layout_key': layoutKey,
                'active_section_key': sectionKey,
              },
            },
          ),
        ),
      );

      server.listen((Socket socket) {
        socket
            .cast<List<int>>()
            .transform(utf8.decoder)
            .transform(const LineSplitter())
            .listen((String line) async {
          final operation = InterfaceControlPlaneOperation.fromJson(
            Map<String, dynamic>.from(jsonDecode(line) as Map),
          );
          final request = operation.request;
          expect(request, isA<InterfaceRequestWindowLayoutRequest>());
          final layoutRequest = request! as InterfaceRequestWindowLayoutRequest;
          expect(layoutRequest.namespace, 'flutter-test');
          expect(layoutRequest.interfacePackageId, interfacePackageId);
          expect(layoutRequest.interfacePackageName, interfacePackageName);
          expect(layoutRequest.windowKey, windowKey);
          expect(layoutRequest.layoutKey, layoutKey);
          expect(layoutRequest.sectionKey, sectionKey);
          expect(layoutRequest.observableId, observableId);
          expect(layoutRequest.requestedByService, requestedByService);
          expect(layoutRequest.requestedByOperation, requestedByOperation);
          expect(layoutRequest.reason, reason);
          expect(layoutRequest.idempotencyKey, idempotencyKey);
          socket.write(
            jsonEncode(
              InterfaceControlPlaneOperation(
                response:
                    InterfaceControlPlaneResponse.interfaceRequestWindowLayout(
                  requestId: layoutRequest.requestId,
                  protocolVersion: 1,
                  success: true,
                  namespace: layoutRequest.namespace,
                  interfacePackageId: layoutRequest.interfacePackageId,
                  interfacePackageName: layoutRequest.interfacePackageName,
                  windowKey: layoutRequest.windowKey,
                  layoutConfigId: layoutConfigId,
                  layoutKey: layoutRequest.layoutKey,
                  sectionKey: layoutRequest.sectionKey,
                  observableId: layoutRequest.observableId,
                  representationId: representationId,
                  requestedByService: layoutRequest.requestedByService,
                  requestedByOperation: layoutRequest.requestedByOperation,
                  reason: layoutRequest.reason,
                  idempotencyKey: layoutRequest.idempotencyKey,
                  hostState: selectedHostState,
                ),
              ).toJson(),
            ),
          );
          socket.write('\n');
          await socket.flush();
          await socket.close();
        });
      });

      final client = InterfaceControlPlaneClient(socketPath: socketPath);
      final response = await client.requestWindowLayout(
        namespace: 'flutter-test',
        interfacePackageId: interfacePackageId,
        interfacePackageName: interfacePackageName,
        windowKey: windowKey,
        layoutKey: layoutKey,
        sectionKey: sectionKey,
        observableId: observableId,
        requestedByService: requestedByService,
        requestedByOperation: requestedByOperation,
        reason: reason,
        idempotencyKey: idempotencyKey,
      );
      expect(response.interfacePackageId, interfacePackageId);
      expect(response.interfacePackageName, interfacePackageName);
      expect(response.windowKey, windowKey);
      expect(response.layoutConfigId, layoutConfigId);
      expect(response.layoutKey, layoutKey);
      expect(response.sectionKey, sectionKey);
      expect(response.observableId, observableId);
      expect(response.representationId, representationId);
      expect(response.requestedByService, requestedByService);
      expect(response.requestedByOperation, requestedByOperation);
      expect(response.reason, reason);
      expect(response.idempotencyKey, idempotencyKey);
      expect(response.hostState?.runtime?.activeFocus?.sectionKey, sectionKey);
      expect(
        response.hostState?.runtime?.resolvedView?.hostPayload['window_layout']
            ?['interface_package_name'],
        interfacePackageName,
      );
    },
  );

  test(
    'client surfaces failed interface_status envelopes before typed decode',
    () async {
      if (Platform.isWindows) {
        return;
      }

      final tempDir = await Directory.systemTemp.createTemp(
        'aware-interface-control-dart-status-failure-',
      );
      final socketPath = p.join(tempDir.path, 'interface-control.sock');
      final server = await ServerSocket.bind(
        InternetAddress(socketPath, type: InternetAddressType.unix),
        0,
      );

      addTearDown(() async {
        await server.close();
        if (File(socketPath).existsSync()) {
          await File(socketPath).delete();
        }
        await tempDir.delete(recursive: true);
      });

      server.listen((Socket socket) {
        socket
            .cast<List<int>>()
            .transform(utf8.decoder)
            .transform(const LineSplitter())
            .listen((String line) async {
          final operation = InterfaceControlPlaneOperation.fromJson(
            Map<String, dynamic>.from(jsonDecode(line) as Map),
          );
          final request = operation.request;
          expect(request, isA<InterfaceStatusRequest>());
          socket.write(
            jsonEncode(<String, dynamic>{
              'response': <String, dynamic>{
                'operation': 'interface_status',
                'request_id': request!.requestId?.uuid,
                'protocol_version': 1,
                'success': false,
                'error': 'Unknown namespace: flutter-test',
              },
            }),
          );
          socket.write('\n');
          await socket.flush();
          await socket.close();
        });
      });

      final client = InterfaceControlPlaneClient(socketPath: socketPath);
      await expectLater(
        () => client.status(namespace: 'flutter-test'),
        throwsA(
          isA<InterfaceControlPlaneClientError>().having(
            (error) => error.error,
            'error',
            'Unknown namespace: flutter-test',
          ),
        ),
      );
    },
  );

  test('client normalizes quoted interface_status failure envelopes', () async {
    if (Platform.isWindows) {
      return;
    }

    final tempDir = await Directory.systemTemp.createTemp(
      'aware-interface-control-dart-status-quoted-failure-',
    );
    final socketPath = p.join(tempDir.path, 'interface-control.sock');
    final server = await ServerSocket.bind(
      InternetAddress(socketPath, type: InternetAddressType.unix),
      0,
    );

    addTearDown(() async {
      await server.close();
      if (File(socketPath).existsSync()) {
        await File(socketPath).delete();
      }
      await tempDir.delete(recursive: true);
    });

    server.listen((Socket socket) {
      socket
          .cast<List<int>>()
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((String line) async {
        final operation = InterfaceControlPlaneOperation.fromJson(
          Map<String, dynamic>.from(jsonDecode(line) as Map),
        );
        final request = operation.request;
        expect(request, isA<InterfaceStatusRequest>());
        socket.write(
          jsonEncode(<String, dynamic>{
            'response': <String, dynamic>{
              'operation': 'interface_status',
              'request_id': request!.requestId?.uuid,
              'protocol_version': 1,
              'success': false,
              'error': "'Unknown namespace: flutter-test'",
            },
          }),
        );
        socket.write('\n');
        await socket.flush();
        await socket.close();
      });
    });

    final client = InterfaceControlPlaneClient(socketPath: socketPath);
    await expectLater(
      () => client.status(namespace: 'flutter-test'),
      throwsA(
        isA<InterfaceControlPlaneClientError>().having(
          (error) => error.error,
          'error',
          'Unknown namespace: flutter-test',
        ),
      ),
    );
  });

  test(
    'client surfaces failed interface_follow envelopes before typed decode',
    () async {
      if (Platform.isWindows) {
        return;
      }

      final tempDir = await Directory.systemTemp.createTemp(
        'aware-interface-control-dart-follow-failure-',
      );
      final socketPath = p.join(tempDir.path, 'interface-control.sock');
      final server = await ServerSocket.bind(
        InternetAddress(socketPath, type: InternetAddressType.unix),
        0,
      );

      addTearDown(() async {
        await server.close();
        if (File(socketPath).existsSync()) {
          await File(socketPath).delete();
        }
        await tempDir.delete(recursive: true);
      });

      server.listen((Socket socket) {
        socket
            .cast<List<int>>()
            .transform(utf8.decoder)
            .transform(const LineSplitter())
            .listen((String line) async {
          final operation = InterfaceControlPlaneOperation.fromJson(
            Map<String, dynamic>.from(jsonDecode(line) as Map),
          );
          final request = operation.request;
          expect(request, isA<InterfaceFollowRequest>());
          socket.write(
            jsonEncode(<String, dynamic>{
              'response': <String, dynamic>{
                'operation': 'interface_follow',
                'request_id': request!.requestId?.uuid,
                'protocol_version': 1,
                'success': false,
                'error': 'Unknown namespace: flutter-test',
              },
            }),
          );
          socket.write('\n');
          await socket.flush();
          await socket.close();
        });
      });

      final client = InterfaceControlPlaneClient(socketPath: socketPath);
      await expectLater(
        () => client.follow(namespace: 'flutter-test').drain<void>(),
        throwsA(
          isA<InterfaceControlPlaneClientError>().having(
            (error) => error.error,
            'error',
            'Unknown namespace: flutter-test',
          ),
        ),
      );
    },
  );

  test('client normalizes quoted interface_follow failure envelopes', () async {
    if (Platform.isWindows) {
      return;
    }

    final tempDir = await Directory.systemTemp.createTemp(
      'aware-interface-control-dart-follow-quoted-failure-',
    );
    final socketPath = p.join(tempDir.path, 'interface-control.sock');
    final server = await ServerSocket.bind(
      InternetAddress(socketPath, type: InternetAddressType.unix),
      0,
    );

    addTearDown(() async {
      await server.close();
      if (File(socketPath).existsSync()) {
        await File(socketPath).delete();
      }
      await tempDir.delete(recursive: true);
    });

    server.listen((Socket socket) {
      socket
          .cast<List<int>>()
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((String line) async {
        final operation = InterfaceControlPlaneOperation.fromJson(
          Map<String, dynamic>.from(jsonDecode(line) as Map),
        );
        final request = operation.request;
        expect(request, isA<InterfaceFollowRequest>());
        socket.write(
          jsonEncode(<String, dynamic>{
            'response': <String, dynamic>{
              'operation': 'interface_follow',
              'request_id': request!.requestId?.uuid,
              'protocol_version': 1,
              'success': false,
              'error': "'Unknown namespace: flutter-test'",
            },
          }),
        );
        socket.write('\n');
        await socket.flush();
        await socket.close();
      });
    });

    final client = InterfaceControlPlaneClient(socketPath: socketPath);
    await expectLater(
      () => client.follow(namespace: 'flutter-test').drain<void>(),
      throwsA(
        isA<InterfaceControlPlaneClientError>().having(
          (error) => error.error,
          'error',
          'Unknown namespace: flutter-test',
        ),
      ),
    );
  });
}

class _FakeInterfaceControlPlaneTransport
    implements InterfaceControlPlaneTransport {
  _FakeInterfaceControlPlaneTransport({required List<String> lines})
      : _lines = lines;

  final List<String> _lines;
  final List<String> writtenLines = <String>[];

  @override
  Future<InterfaceControlPlaneConnection> connect() async {
    return _FakeInterfaceControlPlaneConnection(
      lines: _lines,
      writtenLines: writtenLines,
    );
  }
}

class _FakeInterfaceControlPlaneConnection
    implements InterfaceControlPlaneConnection {
  _FakeInterfaceControlPlaneConnection({
    required List<String> lines,
    required this.writtenLines,
  }) : _lines = lines;

  final List<String> _lines;
  final List<String> writtenLines;

  @override
  Stream<String> get lines => Stream<String>.fromIterable(_lines);

  @override
  Future<void> writeLine(String line) async {
    writtenLines.add(line);
  }

  @override
  Future<void> close() async {}
}

InterfaceHostState _hostState({
  required String namespace,
  required String screenKey,
  required String title,
  required String message,
}) {
  return InterfaceHostState(
    hostLabel: 'interface-flutter-test',
    namespace: namespace,
    started: true,
    transport: _testTransportState(),
    currentScreen: InterfaceCurrentScreen(
      screenKind: 'gate',
      screenKey: screenKey,
      sourceKind: 'gate',
      title: title,
      message: message,
      paneKey: screenKey,
    ),
    warnings: const <String>[],
  );
}

InterfaceTransportState _testTransportState() {
  return InterfaceTransportState(
    available: true,
    registered: true,
    authenticated: true,
  );
}

InterfaceBackendState _testBackendState() {
  return InterfaceBackendState(
    available: false,
    databaseExists: false,
    opgCount: 0,
    projectionBundleAvailable: false,
    projectionPlanCount: 0,
    tableCount: 0,
  );
}

InterfaceRendererCapabilitiesState _rendererCapabilities() {
  return InterfaceRendererCapabilitiesState(
    rendererId: 'flutter-test-renderer',
    rendererKind: 'flutter',
    rendererVersion: '0.1.0',
    interfacePackageId: UuidValue.fromString(
      '33333333-3333-4333-8333-333333333333',
    ),
    interfacePackageName: 'aware-control-interface',
    experienceKeys: const <String>['aware_control_identity'],
    panePackages: <InterfaceRendererPanePackageCapabilityState>[
      InterfaceRendererPanePackageCapabilityState(
        panePackageId: UuidValue.fromString(
          '99999999-9999-4999-8999-999999999999',
        ),
        panePackageName: 'identity-admission-pane',
        paneKind: 'identity_admission',
      ),
    ],
    viewCapabilities: <InterfaceRendererViewCapabilityState>[
      InterfaceRendererViewCapabilityState(
        viewRef: 'aware_identity.profile.home.v1',
        projectionViewKey: 'profile.home.v1',
        paneKind: 'identity_admission',
        hasDecoder: true,
      ),
    ],
    cache: InterfaceRendererCacheCapabilityState(
      storeKind: 'memory',
      supportsNamespaceReplace: true,
      supportsPersistentStorage: false,
      supportsCursorLookup: false,
    ),
    reportedAt: '2026-05-07T00:00:00Z',
  );
}

InterfaceHostViewStateCursorState _viewStateCursor() {
  return InterfaceHostViewStateCursorState(
    cursor: 'view-state:digest-1',
    digest: 'digest-1',
    materializedEntryCount: 1,
    entryDigests: <InterfaceHostViewStateDigestEntryState>[
      InterfaceHostViewStateDigestEntryState(
        paneStateKey: 'pane-a',
        digest: 'entry-digest-1',
        viewRef: 'aware_test.identity.profile.v1',
        projectionViewKey: 'identity.profile.v1',
        projectionHash: 'projection-hash',
        headCommitId: 'head-1',
        graphHashPost: 'graph-1',
      ),
    ],
    computedAt: '2026-05-07T09:00:00Z',
  );
}
