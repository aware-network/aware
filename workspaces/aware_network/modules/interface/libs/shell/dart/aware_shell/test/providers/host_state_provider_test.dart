import 'dart:async';

import 'package:aware_api/aware_api.dart' as aware_api;
import 'package:aware_shell/aware_shell.dart';
import 'package:aware_interface_service_api/aware_interface_service_api.dart'
    as service_api;
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uuid/uuid.dart';

final UuidValue _workspaceControlLayoutId = UuidValue.fromString(
  '11111111-1111-1111-1111-111111111111',
);
final UuidValue _graphViewLayoutId = UuidValue.fromString(
  '22222222-2222-2222-2222-222222222222',
);

StreamController<InterfaceHostState> _newFollowController() {
  return StreamController<InterfaceHostState>.broadcast();
}

Future<void> _waitFor(
  bool Function() predicate, {
  Duration timeout = const Duration(seconds: 1),
}) async {
  final deadline = DateTime.now().add(timeout);
  while (!predicate()) {
    if (DateTime.now().isAfter(deadline)) {
      throw TimeoutException('Condition was not met within $timeout.');
    }
    await Future<void>.delayed(const Duration(milliseconds: 10));
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test(
    'interface control client provider switches to remote websocket transport when configured',
    () async {
      final controlPlaneUri = Uri.parse('wss://interface.example/control');
      final container = ProviderContainer(
        overrides: <Override>[
          interfaceHostTargetProvider.overrideWith(
            (ref) => InterfaceHostTarget.remote(
              controlPlaneUrl: controlPlaneUri.toString(),
              controlPlaneUri: controlPlaneUri,
              source: InterfaceHostBootstrapSource.explicit,
            ),
          ),
        ],
      );

      addTearDown(() {
        container.dispose();
      });

      final client = container.read(interfaceHostClientProvider);
      final target = container.read(interfaceHostTargetProvider);

      expect(container.read(interfaceHostRemoteEntryEnabledProvider), isTrue);
      expect(client, isA<InterfaceSdkClient>());
      expect(target.controlPlaneUri, controlPlaneUri);
      expect(target.socketPath, isNull);
    },
  );

  test(
    'interface host providers resolve inside scoped control target override',
    () async {
      final parent = ProviderContainer();
      final followController = _newFollowController();
      final initial = _hostState(
        namespace: 'scoped-test',
        screenKey: 'runtime_ready',
        title: 'Runtime Ready',
        message: 'Scoped runtime is ready.',
      );
      final fakeClient = _FakeInterfaceSdkClient(
        initial: initial,
        followController: followController,
      );
      final child = ProviderContainer(
        parent: parent,
        overrides: <Override>[
          interfaceHostTargetProvider.overrideWith(
            (ref) => InterfaceHostTarget.remote(
              controlPlaneUrl: 'wss://scoped.example/interface/control',
              controlPlaneUri: Uri.parse(
                'wss://scoped.example/interface/control',
              ),
              source: InterfaceHostBootstrapSource.explicit,
            ),
          ),
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
          interfaceControlNamespaceProvider.overrideWith(
            (ref) async => 'scoped-test',
          ),
        ],
      );

      addTearDown(() async {
        child.dispose();
        parent.dispose();
        await followController.close();
      });

      final connection = await child.read(
        interfaceHostConnectionProvider.future,
      );
      final hostState = await child.read(interfaceHostStateProvider.future);

      expect(connection.namespace, 'scoped-test');
      expect(connection.remoteTarget, isTrue);
      expect(hostState.namespace, 'scoped-test');
      expect(fakeClient.ensureNamespaceCalls, <String>['scoped-test']);
    },
  );

  test(
    'default namespace resolves inside scoped control target override',
    () async {
      final parent = ProviderContainer();
      final followController = _newFollowController();
      final fakeClient = _FakeInterfaceSdkClient(
        initial: _hostState(
          namespace: 'fallback-host-state',
          screenKey: 'runtime_ready',
          title: 'Runtime Ready',
          message: 'Scoped runtime is ready.',
        ),
        followController: followController,
      );
      final child = ProviderContainer(
        parent: parent,
        overrides: <Override>[
          interfaceHostTargetProvider.overrideWith(
            (ref) => InterfaceHostTarget.remote(
              controlPlaneUrl: 'wss://source-local.example/interface/control',
              controlPlaneUri: Uri.parse(
                'wss://source-local.example/interface/control',
              ),
              source: InterfaceHostBootstrapSource.explicit,
            ),
          ),
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
        ],
      );

      addTearDown(() async {
        child.dispose();
        parent.dispose();
        await followController.close();
      });

      final connection = await child.read(
        interfaceHostConnectionProvider.future,
      );
      await child.read(interfaceHostStateProvider.future);

      expect(connection.namespace, isNotEmpty);
      expect(fakeClient.ensureNamespaceCalls, <String>[connection.namespace]);
    },
  );

  test(
    'interface host state provider does not enter environment without target',
    () async {
      final followController = _newFollowController();
      final fakeClient = _FakeInterfaceSdkClient(
        initial: _hostState(
          namespace: 'flutter-test',
          screenKey: 'runtime_ready',
          title: 'Runtime Ready',
          message: 'Namespace is ready.',
        ),
        followController: followController,
      );
      final container = ProviderContainer(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
          interfaceControlNamespaceProvider.overrideWith(
            (ref) async => 'flutter-test',
          ),
        ],
      );

      addTearDown(() async {
        container.dispose();
        await followController.close();
      });

      await container.read(interfaceHostStateProvider.future);

      expect(fakeClient.ensureNamespaceCalls, <String>['flutter-test']);
      expect(fakeClient.enterEnvironmentCalls, isEmpty);
    },
  );

  test(
    'interface host state provider enters configured environment target',
    () async {
      final environmentId = UuidValue.fromString(
        'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
      );
      final environmentProfileId = UuidValue.fromString(
        'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
      );
      final environmentSessionId = UuidValue.fromString(
        'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
      );
      final environmentNavigationContextId = UuidValue.fromString(
        'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
      );
      final entered = _hostState(
        namespace: 'flutter-test',
        screenKey: 'runtime_ready',
        title: 'Runtime Ready',
        message: 'Environment entered.',
      ).copyWith(
        environmentId: environmentId,
        environmentSession: InterfaceEnvironmentSessionState(
          status: 'joined',
          sourceKind: 'interface_enter_environment',
          accepted: true,
          environmentId: environmentId,
          environmentProfileId: environmentProfileId,
          environmentSessionId: environmentSessionId,
          environmentSessionKey: 'dogfood-coordination',
          identityActorRoleCount: 1,
          evidence: const <String, dynamic>{'test': 'entered'},
        ),
        environmentNavigation: InterfaceEnvironmentNavigationState(
          status: 'active',
          sourceKind: 'environment_default_navigation_context',
          accepted: true,
          environmentId: environmentId,
          environmentSessionId: environmentSessionId,
          environmentNavigationContextId: environmentNavigationContextId,
          key: 'default',
          evidence: const <String, dynamic>{'test': 'navigation'},
        ),
      );
      final followController = _newFollowController();
      final fakeClient = _FakeInterfaceSdkClient(
        initial: _hostState(
          namespace: 'flutter-test',
          screenKey: 'runtime_ready',
          title: 'Runtime Ready',
          message: 'Namespace is ready.',
        ),
        enteredEnvironmentHostState: entered,
        followController: followController,
      );
      final container = ProviderContainer(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
          interfaceControlNamespaceProvider.overrideWith(
            (ref) async => 'flutter-test',
          ),
          interfaceEnvironmentEntryTargetProvider.overrideWith(
            (ref) => InterfaceEnvironmentEntryTarget(
              environmentId: environmentId,
              environmentProfileId: environmentProfileId,
              environmentSessionId: environmentSessionId,
              sessionKey: 'dogfood-coordination',
              sourceKind: 'test_shell_boot',
              sourceRef: 'test://shell',
              evidence: const <String, dynamic>{'source': 'test'},
            ),
          ),
        ],
      );

      addTearDown(() async {
        container.dispose();
        await followController.close();
      });

      await container.read(interfaceHostStateProvider.future);
      await _waitFor(() => fakeClient.enterEnvironmentCalls.length == 1);
      await _waitFor(
        () =>
            container
                .read(interfaceHostStateProvider)
                .valueOrNull
                ?.environmentSession
                ?.accepted ==
            true,
      );
      final hostState = container.read(interfaceHostStateProvider).valueOrNull;

      expect(hostState?.environmentSession?.accepted, isTrue);
      expect(hostState?.environmentNavigation?.accepted, isTrue);
      expect(fakeClient.ensureNamespaceCalls, <String>['flutter-test']);
      expect(fakeClient.enterEnvironmentCalls, hasLength(1));
      final call = fakeClient.enterEnvironmentCalls.single;
      expect(call.namespace, 'flutter-test');
      expect(call.environmentId, environmentId);
      expect(call.environmentProfileId, environmentProfileId);
      expect(call.environmentSessionId, environmentSessionId);
      expect(call.environmentSessionConfigId, isNull);
      expect(call.sessionKey, 'dogfood-coordination');
      expect(call.sourceKind, 'test_shell_boot');
      expect(call.sourceRef, 'test://shell');
    },
  );

  test('interface host state provider enters committed App screen', () async {
    final appPackageId = UuidValue.fromString(
      '11111111-1111-4111-8111-111111111111',
    );
    final appPackageBranchId = UuidValue.fromString(
      '22222222-2222-4222-8222-222222222222',
    );
    final appPackageCommitId = UuidValue.fromString(
      '33333333-3333-4333-8333-333333333333',
    );
    final screenId = UuidValue.fromString(
      '44444444-4444-4444-8444-444444444444',
    );
    final initial = _hostState(
      namespace: 'flutter-test',
      screenKey: 'control',
      title: 'Control',
      message: 'Control is ready.',
    );
    final entered = initial.copyWith(
      appScreen: InterfaceAppScreenState(
        status: 'accepted',
        accepted: true,
        appPackageId: appPackageId,
        appPackageBranchId: appPackageBranchId,
        appPackageObjectInstanceGraphCommitId: appPackageCommitId,
        appConfigScreenConfigId: screenId,
        screenKey: 'home',
        evidence: const <String, dynamic>{'source': 'test'},
      ),
    );
    final followController = _newFollowController();
    final fakeClient = _FakeInterfaceSdkClient(
      initial: initial,
      enteredAppScreenHostState: entered,
      followController: followController,
    );
    final container = ProviderContainer(
      overrides: <Override>[
        interfaceSdkClientProvider.overrideWithValue(fakeClient),
        interfaceControlNamespaceProvider.overrideWith(
          (ref) async => 'flutter-test',
        ),
      ],
    );

    addTearDown(() async {
      container.dispose();
      await followController.close();
    });

    await container.read(interfaceHostStateProvider.future);
    final next = await container
        .read(interfaceHostStateProvider.notifier)
        .enterAppScreen(
      appPackageId: appPackageId,
      appPackageBranchId: appPackageBranchId,
      appPackageObjectInstanceGraphCommitId: appPackageCommitId,
      appConfigScreenConfigId: screenId,
      reason: 'control_action:admit_identity',
      evidence: const <String, dynamic>{'source': 'test'},
    );

    expect(next.appScreen?.accepted, isTrue);
    expect(fakeClient.enterAppScreenCalls, hasLength(1));
    final call = fakeClient.enterAppScreenCalls.single;
    expect(call.namespace, 'flutter-test');
    expect(call.appPackageId, appPackageId);
    expect(call.appPackageBranchId, appPackageBranchId);
    expect(call.appPackageObjectInstanceGraphCommitId, appPackageCommitId);
    expect(call.appConfigScreenConfigId, screenId);
    expect(call.reason, 'control_action:admit_identity');
    expect(call.evidence, const <String, dynamic>{'source': 'test'});
  });

  test(
    'interface host state provider selects environment navigation target',
    () async {
      final environmentNavigationContextId = UuidValue.fromString(
        'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
      );
      final processId = UuidValue.fromString(
        'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
      );
      final threadId = UuidValue.fromString(
        'ffffffff-ffff-4fff-8fff-ffffffffffff',
      );
      final selectedHostState = _hostState(
        namespace: 'flutter-test',
        screenKey: 'runtime_ready',
        title: 'Runtime Ready',
        message: 'Environment navigation selected.',
      ).copyWith(
        environmentNavigation: InterfaceEnvironmentNavigationState(
          status: 'active',
          sourceKind: 'test',
          accepted: true,
          environmentNavigationContextId: environmentNavigationContextId,
          processId: processId,
          threadId: threadId,
          evidence: const <String, dynamic>{},
        ),
      );
      final followController = _newFollowController();
      final fakeClient = _FakeInterfaceSdkClient(
        initial: _hostState(
          namespace: 'flutter-test',
          screenKey: 'runtime_ready',
          title: 'Runtime Ready',
          message: 'Namespace is ready.',
        ),
        selectedEnvironmentNavigationHostState: selectedHostState,
        followController: followController,
      );
      final container = ProviderContainer(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
          interfaceControlNamespaceProvider.overrideWith(
            (ref) async => 'flutter-test',
          ),
        ],
      );

      addTearDown(() async {
        container.dispose();
        await followController.close();
      });

      await container.read(interfaceHostStateProvider.future);
      final next = await container
          .read(interfaceHostStateProvider.notifier)
          .selectEnvironmentNavigationTarget(
        environmentNavigationContextId: environmentNavigationContextId,
        selectedProcessId: processId,
        selectedThreadId: threadId,
        reason: 'test_select',
        evidence: const <String, dynamic>{'source': 'test'},
      );

      expect(next.environmentNavigation?.threadId, threadId);
      expect(fakeClient.selectEnvironmentNavigationTargetCalls, hasLength(1));
      final call = fakeClient.selectEnvironmentNavigationTargetCalls.single;
      expect(call.namespace, 'flutter-test');
      expect(
        call.environmentNavigationContextId,
        environmentNavigationContextId,
      );
      expect(call.selectedProcessId, processId);
      expect(call.selectedThreadId, threadId);
      expect(call.reason, 'test_select');
      expect(call.evidence, const <String, dynamic>{'source': 'test'});
    },
  );

  test('interface host state provider follows live daemon updates', () async {
    final initial = _hostState(
      namespace: 'flutter-test',
      screenKey: 'local_service_host_gate',
      title: 'Local Service Host Required',
      message: 'Start the local service host to continue.',
    );
    final next = _hostState(
      namespace: 'flutter-test',
      screenKey: 'local_node_runtime_gate',
      title: 'Local Node Required',
      message: 'Start the local node runtime to continue.',
    );
    final followController = _newFollowController();
    final fakeClient = _FakeInterfaceSdkClient(
      initial: initial,
      followController: followController,
    );

    final container = ProviderContainer(
      overrides: <Override>[
        interfaceSdkClientProvider.overrideWithValue(fakeClient),
        interfaceControlNamespaceProvider.overrideWith(
          (ref) async => 'flutter-test',
        ),
        interfaceHostStateFollowReconnectDelayMsProvider.overrideWith(
          (ref) => 10,
        ),
      ],
    );
    final followedState = Completer<void>();
    final subscription = container.listen<AsyncValue<InterfaceHostState>>(
      interfaceHostStateProvider,
      (_, nextValue) {
        if (nextValue.valueOrNull?.currentScreen?.screenKey ==
                'local_node_runtime_gate' &&
            !followedState.isCompleted) {
          followedState.complete();
        }
      },
      fireImmediately: true,
    );

    addTearDown(() async {
      subscription.close();
      container.dispose();
      await followController.close();
    });

    final first = await container.read(interfaceHostStateProvider.future);
    expect(first.currentScreen?.screenKey, 'local_service_host_gate');
    await _waitFor(() => fakeClient.followCalls == 1);

    followController.add(next);
    await followedState.future.timeout(const Duration(seconds: 1));

    final followed = container.read(interfaceHostStateProvider).valueOrNull;
    expect(followed, isNotNull);
    expect(followed?.currentScreen?.screenKey, 'local_node_runtime_gate');
  });

  test(
    'interface pane action dispatcher invokes scoped render action target',
    () async {
      final initial = _hostState(
        namespace: 'flutter-test',
        screenKey: 'identity_auth_gate',
        title: 'Identity Admission',
        message: 'Admit identity.',
      );
      final fakeClient = _FakeInterfaceSdkClient(
        initial: initial,
        followController: _newFollowController(),
      );

      final container = ProviderContainer(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
          interfaceControlNamespaceProvider.overrideWith(
            (ref) async => 'flutter-test',
          ),
        ],
      );

      addTearDown(() async {
        container.dispose();
        await fakeClient.followController.close();
      });

      await container.read(interfaceHostStateProvider.future);
      await container
          .read(interfacePaneActionDispatcherProvider)
          .invokeActionTarget(
        paneContext: PaneContext(
          paneId: 'identity-pane',
          kind: 'identity_admission',
          parameters: const <String, dynamic>{
            kPaneParamWindowKey: 'main',
            kPaneParamLayoutKey: 'coordination_center',
            kPaneParamSectionKey: 'orchestration',
          },
        ),
        actionTarget: const PaneRenderActionTarget(
          actionKey: 'admit_identity',
          actionKind: kPaneRenderActionKindViewAction,
        ),
        payload: const <String, dynamic>{'public_key': 'ed25519:test'},
      );

      expect(fakeClient.actionCalls, hasLength(1));
      final action = fakeClient.actionCalls.single;
      expect(action.namespace, 'flutter-test');
      expect(action.paneRef, 'main/coordination_center/orchestration');
      expect(action.actionKey, 'admit_identity');
      expect(action.actionTarget, isNotNull);
      expect(action.actionTarget?.actionKey, 'admit_identity');
      expect(action.actionTarget?.actionKind, kPaneRenderActionKindViewAction);
      expect(action.actionTarget?.operationRef, isNull);
      expect(action.actionTarget?.sdkOperationId, isNull);
      expect(action.actionTarget?.paneConfigSdkOperationId, isNull);
      expect(action.payload, <String, dynamic>{'public_key': 'ed25519:test'});
    },
  );

  test(
    'interface pane action dispatcher surfaces failed host operation',
    () async {
      final initial = _hostState(
        namespace: 'flutter-test',
        screenKey: 'identity_auth_gate',
        title: 'Identity Admission',
        message: 'Admit identity.',
      );
      final failedActionState = _hostState(
        namespace: 'flutter-test',
        screenKey: 'identity_auth_gate',
        title: 'Identity Admission',
        message: 'Admit identity.',
        currentOperation: InterfaceOperationState(
          operationKey: 'mounted_pane_view_action',
          title: 'Mounted view action: admit_identity',
          status: 'failed',
          phase: 'failed',
          currentTargetId: 'admit_identity',
          currentTargetTitle: 'admit_identity',
          summary: 'Mounted pane view action failed.',
          error: 'Interface host view action failed.',
          running: false,
          retryable: true,
          recentActivity: const <String>[
            'main/coordination_center/orchestration -> admit_identity',
          ],
        ),
      );
      final fakeClient = _FakeInterfaceSdkClient(
        initial: initial,
        actionHostState: failedActionState,
        followController: _newFollowController(),
      );

      final container = ProviderContainer(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
          interfaceControlNamespaceProvider.overrideWith(
            (ref) async => 'flutter-test',
          ),
        ],
      );

      addTearDown(() async {
        container.dispose();
        await fakeClient.followController.close();
      });

      await container.read(interfaceHostStateProvider.future);
      await expectLater(
        container
            .read(interfacePaneActionDispatcherProvider)
            .invokeActionTarget(
          paneContext: PaneContext(
            paneId: 'identity-pane',
            kind: 'identity_admission',
            parameters: const <String, dynamic>{
              kPaneParamWindowKey: 'main',
              kPaneParamLayoutKey: 'coordination_center',
              kPaneParamSectionKey: 'orchestration',
            },
          ),
          actionTarget: const PaneRenderActionTarget(
            actionKey: 'admit_identity',
            actionKind: kPaneRenderActionKindViewAction,
          ),
          payload: const <String, dynamic>{'public_key': 'ed25519:test'},
        ),
        throwsA(
          isA<InterfacePaneActionFailure>()
              .having(
                (error) => error.operationKey,
                'operationKey',
                'mounted_pane_view_action',
              )
              .having(
                (error) => error.message,
                'message',
                contains('Interface host view action failed'),
              ),
        ),
      );

      expect(fakeClient.actionCalls, hasLength(1));
      expect(
        container
            .read(interfaceHostStateProvider)
            .valueOrNull
            ?.currentOperation
            ?.status,
        'failed',
      );
    },
  );

  test('interface pane action dispatcher stays in scoped namespace', () async {
    final parentFollowController = _newFollowController();
    final parentFakeClient = _FakeInterfaceSdkClient(
      initial: _hostState(
        namespace: 'root-namespace',
        screenKey: 'root',
        title: 'Root',
        message: 'Root state.',
      ),
      followController: parentFollowController,
    );
    final parent = ProviderContainer(
      overrides: <Override>[
        interfaceSdkClientProvider.overrideWithValue(parentFakeClient),
        interfaceControlNamespaceProvider.overrideWith(
          (ref) async => 'root-namespace',
        ),
      ],
    );
    parent.read(interfacePaneActionDispatcherProvider);

    final childFollowController = _newFollowController();
    final childFakeClient = _FakeInterfaceSdkClient(
      initial: _hostState(
        namespace: 'scoped-action',
        screenKey: 'identity_auth_gate',
        title: 'Identity Admission',
        message: 'Admit identity.',
      ),
      followController: childFollowController,
    );
    final child = ProviderContainer(
      parent: parent,
      overrides: <Override>[
        interfaceSdkClientProvider.overrideWithValue(childFakeClient),
        interfaceControlNamespaceProvider.overrideWith(
          (ref) async => 'scoped-action',
        ),
      ],
    );

    addTearDown(() async {
      child.dispose();
      parent.dispose();
      await childFollowController.close();
      await parentFollowController.close();
    });

    await child.read(interfaceHostStateProvider.future);
    await child.read(interfacePaneActionDispatcherProvider).invokeAction(
      paneContext: PaneContext(
        paneId: 'identity-pane',
        kind: 'identity_admission',
        parameters: const <String, dynamic>{
          kPaneParamWindowKey: 'main',
          kPaneParamLayoutKey: 'coordination_center',
          kPaneParamSectionKey: 'orchestration',
        },
      ),
      actionKey: 'admit_identity',
      payload: const <String, dynamic>{'profile': 'scoped'},
    );

    expect(parentFakeClient.actionCalls, isEmpty);
    expect(childFakeClient.actionCalls, hasLength(1));
    expect(childFakeClient.actionCalls.single.namespace, 'scoped-action');
  });

  test(
    'interface host connection provider flags legacy daemon metadata as restart recommended',
    () async {
      final fakeClient = _FakeInterfaceSdkClient(
        initial: _hostState(
          namespace: 'flutter-test',
          screenKey: 'local_service_host_gate',
          title: 'Local Service Host Required',
          message: 'Start the local service host to continue.',
        ),
        followController: _newFollowController(),
        pingResponse: PingResponse(
          protocolVersion: 1,
          success: true,
          service: 'aware_interface_service',
          status: 'ok',
          restartRecommended: true,
          socketPath: '/tmp/interface-control.sock',
          daemonStartedAt: null,
          daemonSourceFingerprint: null,
          repositoryRoot: null,
          stateHome: null,
          defaultEndpoint: null,
          namespaces: const [],
        ),
      );

      final container = ProviderContainer(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
        ],
      );

      addTearDown(() async {
        container.dispose();
        await fakeClient.followController.close();
      });

      final connection = await container.read(
        interfaceHostConnectionProvider.future,
      );

      expect(connection.statusLabel, 'Restart Recommended');
      expect(connection.restartRecommended, isTrue);
      expect(connection.blocksRuntimeEntry, isTrue);
    },
  );

  test(
    'interface host connection provider respects daemon freshness restart signal',
    () async {
      final fakeClient = _FakeInterfaceSdkClient(
        initial: _hostState(
          namespace: 'flutter-test',
          screenKey: 'local_service_host_gate',
          title: 'Local Service Host Required',
          message: 'Start the local service host to continue.',
        ),
        followController: _newFollowController(),
        pingResponse: PingResponse(
          protocolVersion: 1,
          success: true,
          service: 'aware_interface_service',
          status: 'ok',
          socketPath: '/tmp/interface-control.sock',
          daemonStartedAt: '2026-04-12T09:42:18Z',
          daemonSourceFingerprint: 'stale-fingerprint',
          expectedSourceFingerprint: 'current-fingerprint',
          restartRecommended: true,
          restartReason:
              'daemon source fingerprint differs from the current workspace',
          repositoryRoot: '/home/luis/aware',
          stateHome: '/tmp/interface-state',
          defaultEndpoint: 'ws://localhost:8000',
          namespaces: const [],
        ),
      );

      final container = ProviderContainer(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
        ],
      );

      addTearDown(() async {
        container.dispose();
        await fakeClient.followController.close();
      });

      final connection = await container.read(
        interfaceHostConnectionProvider.future,
      );

      expect(connection.statusLabel, 'Restart Recommended');
      expect(connection.restartRecommended, isTrue);
      expect(connection.blocksRuntimeEntry, isTrue);
      expect(
        connection.restartReason,
        'daemon source fingerprint differs from the current workspace',
      );
      expect(connection.expectedSourceFingerprint, 'current-fingerprint');
    },
  );

  test(
    'interface host connection provider treats missing expected freshness metadata as legacy daemon',
    () async {
      final fakeClient = _FakeInterfaceSdkClient(
        initial: _hostState(
          namespace: 'flutter-test',
          screenKey: 'local_service_host_gate',
          title: 'Local Service Host Required',
          message: 'Start the local service host to continue.',
        ),
        followController: _newFollowController(),
        pingResponse: PingResponse(
          protocolVersion: 1,
          success: true,
          service: 'aware_interface_service',
          status: 'ok',
          socketPath: '/tmp/interface-control.sock',
          daemonStartedAt: '2026-04-12T09:42:18Z',
          daemonSourceFingerprint: 'stale-fingerprint',
          expectedSourceFingerprint: null,
          restartRecommended: false,
          restartReason: null,
          repositoryRoot: '/home/luis/aware',
          stateHome: '/tmp/interface-state',
          defaultEndpoint: 'ws://localhost:8000',
          namespaces: const [],
        ),
      );

      final container = ProviderContainer(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
        ],
      );

      addTearDown(() async {
        container.dispose();
        await fakeClient.followController.close();
      });

      final connection = await container.read(
        interfaceHostConnectionProvider.future,
      );

      expect(connection.statusLabel, 'Restart Recommended');
      expect(connection.restartRecommended, isTrue);
      expect(connection.blocksRuntimeEntry, isTrue);
      expect(
        connection.restartReason,
        'daemon is missing freshness-comparison metadata',
      );
    },
  );

  test(
    'interface host connection provider does not synthesize legacy restart advice for remote targets',
    () async {
      final fakeClient = _FakeInterfaceSdkClient(
        initial: _hostState(
          namespace: 'flutter-test',
          screenKey: 'workspace_start_gate',
          title: 'Start Workspace',
          message: 'Remote host is available.',
        ),
        followController: _newFollowController(),
        pingResponse: PingResponse(
          protocolVersion: 1,
          success: true,
          service: 'aware_interface_service',
          status: 'ok',
          socketPath: null,
          daemonStartedAt: '2026-04-20T11:00:00Z',
          daemonSourceFingerprint: null,
          expectedSourceFingerprint: null,
          restartRecommended: false,
          restartReason: null,
          repositoryRoot: null,
          stateHome: null,
          defaultEndpoint: 'wss://interface.aware.run/control',
          namespaces: const [],
        ),
      );

      final container = ProviderContainer(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
          interfaceHostTargetProvider.overrideWith(
            (ref) => InterfaceHostTarget.remote(
              controlPlaneUrl: 'https://interface.aware.run/control',
              controlPlaneUri: Uri.parse('wss://interface.aware.run/control'),
              source: InterfaceHostBootstrapSource.explicit,
            ),
          ),
          interfaceControlNamespaceProvider.overrideWith(
            (ref) async => 'flutter-test',
          ),
        ],
      );

      addTearDown(() async {
        container.dispose();
        await fakeClient.followController.close();
      });

      final connection = await container.read(
        interfaceHostConnectionProvider.future,
      );

      expect(connection.remoteTarget, isTrue);
      expect(connection.restartRecommended, isFalse);
      expect(connection.blocksRuntimeEntry, isFalse);
      expect(connection.protocolVersion, 1);
      expect(connection.namespace, 'flutter-test');
      expect(connection.namespaceBound, isFalse);
      expect(connection.bootstrapSourceLabel, 'explicit');
      expect(connection.targetTransport, 'remote_websocket');
    },
  );

  test(
    'interface host connection provider blocks incompatible control-plane contracts',
    () async {
      final fakeClient = _FakeInterfaceSdkClient(
        initial: _hostState(
          namespace: 'flutter-test',
          screenKey: 'workspace_start_gate',
          title: 'Start Workspace',
          message: 'Remote host is available.',
        ),
        followController: _newFollowController(),
        pingResponse: PingResponse(
          protocolVersion: 2,
          success: true,
          service: 'unexpected_interface_service',
          status: 'ok',
          restartRecommended: false,
          namespaces: const [],
        ),
      );

      final container = ProviderContainer(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
          interfaceHostTargetProvider.overrideWith(
            (ref) => InterfaceHostTarget.remote(
              controlPlaneUrl: 'https://interface.aware.run/control',
              controlPlaneUri: Uri.parse('wss://interface.aware.run/control'),
              source: InterfaceHostBootstrapSource.explicit,
            ),
          ),
          interfaceControlNamespaceProvider.overrideWith(
            (ref) async => 'flutter-test',
          ),
        ],
      );

      addTearDown(() async {
        container.dispose();
        await fakeClient.followController.close();
      });

      final connection = await container.read(
        interfaceHostConnectionProvider.future,
      );

      expect(connection.statusLabel, 'Incompatible');
      expect(connection.blocksRuntimeEntry, isTrue);
      expect(
        connection.compatibilityIssues,
        contains('unexpected_service:unexpected_interface_service'),
      );
      expect(
        connection.compatibilityIssues,
        contains('unsupported_protocol_version:2'),
      );
      expect(connection.restartRecommended, isFalse);
    },
  );

  test(
    'interface host binding provider exposes the matching hosted namespace',
    () async {
      final fakeClient = _FakeInterfaceSdkClient(
        initial: _hostState(
          namespace: 'flutter-test',
          screenKey: 'workspace_start_gate',
          title: 'Start Workspace',
          message: 'Remote host is available.',
        ),
        followController: _newFollowController(),
        pingResponse: PingResponse(
          protocolVersion: 1,
          success: true,
          service: 'aware_interface_service',
          status: 'ok',
          restartRecommended: false,
          namespaces: <HostedInterfaceNamespace>[
            HostedInterfaceNamespace(
              namespace: 'flutter-test',
              hostLabel: 'interface-flutter',
              started: true,
              actorId: UuidValue.fromString(
                'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
              ),
              interfaceId: UuidValue.fromString(
                'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
              ),
              interfaceSessionId: UuidValue.fromString(
                'cccccccc-cccc-cccc-cccc-cccccccccccc',
              ),
              environmentId: UuidValue.fromString(
                'dddddddd-dddd-dddd-dddd-dddddddddddd',
              ),
              environmentConfigId: UuidValue.fromString(
                'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
              ),
              warnings: const <String>['runtime_unbound'],
            ),
          ],
        ),
      );

      final container = ProviderContainer(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
          interfaceControlNamespaceProvider.overrideWith(
            (ref) async => 'flutter-test',
          ),
        ],
      );

      addTearDown(() async {
        container.dispose();
        await fakeClient.followController.close();
      });

      final binding = await container.read(interfaceHostBindingProvider.future);

      expect(binding.compatible, isTrue);
      expect(binding.namespace, 'flutter-test');
      expect(binding.namespaceBinding.bound, isTrue);
      expect(binding.namespaceBinding.hostLabel, 'interface-flutter');
      expect(
        binding.namespaceBinding.interfaceId,
        UuidValue.fromString('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'),
      );
      expect(binding.connection.namespaceBound, isTrue);
      expect(binding.connection.namespaceCount, 1);
    },
  );

  test(
    'remote host binding and state providers align on deploy-shaped workspace truth',
    () async {
      final harness = _RemoteWorkspaceHostHarness();
      final fakeClient = _FakeInterfaceSdkClient(
        initial: harness.mountableHostState(),
        followController: _newFollowController(),
        pingResponse: harness.pingResponse(),
      );

      final container = ProviderContainer(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
          interfaceHostTargetProvider.overrideWith((ref) => harness.target),
          interfaceControlNamespaceProvider.overrideWith(
            (ref) async => harness.namespace,
          ),
          interfaceHostStateFollowReconnectDelayMsProvider.overrideWith(
            (ref) => 10,
          ),
        ],
      );

      addTearDown(() async {
        container.dispose();
        await fakeClient.followController.close();
      });

      final binding = await container.read(interfaceHostBindingProvider.future);
      final hostState = await container.read(interfaceHostStateProvider.future);
      await _waitFor(() => fakeClient.followCalls == 1);

      expect(binding.compatible, isTrue);
      expect(binding.target.isRemote, isTrue);
      expect(binding.namespace, harness.namespace);
      expect(binding.connection.connected, isTrue);
      expect(binding.connection.remoteTarget, isTrue);
      expect(binding.connection.targetTransport, 'remote_websocket');
      expect(binding.connection.bootstrapSourceLabel, 'explicit');
      expect(binding.connection.namespaceBound, isTrue);
      expect(binding.connection.defaultEndpoint, harness.defaultEndpoint);
      expect(binding.namespaceBinding.bound, isTrue);
      expect(binding.namespaceBinding.hostLabel, harness.hostLabel);
      expect(binding.namespaceBinding.interfaceId, harness.interfaceId);
      expect(
        binding.namespaceBinding.environmentConfigId,
        harness.environmentConfigId,
      );
      expect(binding.namespaceBinding.warnings, <String>['runtime_unbound']);

      expect(hostState.hostLabel, harness.hostLabel);
      expect(hostState.namespace, harness.namespace);
      expect(hostState.selectedWorkspace?.workspaceRoot, harness.workspaceRoot);
      expect(hostState.selectedWorkspace?.lifecycle?.joined, isTrue);
      expect(
        hostState.selectedWorkspace?.semanticSource?.sourceMode,
        'bundle_backed',
      );
      expect(
        hostState.selectedSemanticPackage?.package.selectorKey,
        'interface_package:aware_workspace',
      );
      expect(
        hostState.runtime?.resolvedView?.projectionViewId,
        'aware_workspace.control.main',
      );
      expect(interfaceHostRuntimeShellAvailable(hostState), isTrue);
      expect(interfaceHostRuntimeLayoutKey(hostState), 'workspace_control');
      expect(
        interfaceHostRuntimeLayoutConfigId(hostState),
        _workspaceControlLayoutId,
      );
      expect(
        interfaceHostRuntimeLayoutStates(
          hostState,
        ).map((layout) => layout.layoutKey).toList(growable: false),
        const <String>['workspace_control', 'graph_view'],
      );
      expect(
        canEnterInterfaceHostRuntimeShell(
          connection: binding.connection,
          hostState: hostState,
        ),
        isTrue,
      );
      expect(fakeClient.ensureNamespaceCalls, <String>[harness.namespace]);
    },
  );

  test(
    'interface host runtime shell helpers keep package-less bootstrap layouts in entry control plane',
    () {
      const connection = InterfaceHostConnectionState(
        service: 'aware_interface_service',
        statusLabel: 'Connected',
        title: 'Interface Host Connected',
        message: 'Connected.',
        connected: true,
        blocksRuntimeEntry: false,
        restartRecommended: false,
        restartReason: null,
        socketPath: '/tmp/interface-control.sock',
        daemonStartedAt: '2026-04-13T00:00:00Z',
        daemonSourceFingerprint: 'current',
        expectedSourceFingerprint: 'current',
        repositoryRoot: '/home/luis/aware',
        stateHome: '/tmp/interface-state',
        defaultEndpoint: 'ws://localhost:8000',
        namespaceCount: 1,
      );
      final hostState = InterfaceHostState(
        hostLabel: 'interface-flutter-test',
        namespace: 'flutter-test',
        started: true,
        transport: _testTransportState(),
        runtime: InterfaceRuntimeState(
          backend: _testBackendState(),
          resolvedView: InterfaceResolvedView(
            experienceKey: 'aware.interface.bootstrap',
            projectionViewId: 'entry.control-plane',
            hostPayload: const <String, dynamic>{
              'window_layout': <String, dynamic>{
                'window_key': 'bootstrap',
                'layout_key': 'bootstrap.control-plane',
                'sections': <Map<String, dynamic>>[
                  <String, dynamic>{'section_key': 'workspace', 'order': 0},
                ],
              },
            },
          ),
        ),
      );

      expect(interfaceHostRuntimeWindowLayoutPayload(hostState), isNotNull);
      expect(interfaceHostRuntimeShellAvailable(hostState), isFalse);
      expect(
        canEnterInterfaceHostRuntimeShell(
          connection: connection,
          hostState: hostState,
        ),
        isFalse,
      );
    },
  );

  test(
    'interface host runtime shell helpers require current connection and host layout payload',
    () {
      const connection = InterfaceHostConnectionState(
        service: 'aware_interface_service',
        statusLabel: 'Connected',
        title: 'Interface Host Connected',
        message: 'Connected.',
        connected: true,
        blocksRuntimeEntry: false,
        restartRecommended: false,
        restartReason: null,
        socketPath: '/tmp/interface-control.sock',
        daemonStartedAt: '2026-04-13T00:00:00Z',
        daemonSourceFingerprint: 'current',
        expectedSourceFingerprint: 'current',
        repositoryRoot: '/home/luis/aware',
        stateHome: '/tmp/interface-state',
        defaultEndpoint: 'ws://localhost:8000',
        namespaceCount: 1,
      );
      final hostState = InterfaceHostState(
        hostLabel: 'interface-flutter-test',
        namespace: 'flutter-test',
        started: true,
        transport: _testTransportState(),
        runtime: InterfaceRuntimeState(
          backend: _testBackendState(),
          activeLayoutConfigId: _workspaceControlLayoutId,
          layoutStates: <InterfaceRuntimeLayoutState>[
            InterfaceRuntimeLayoutState(
              layoutConfigId: _workspaceControlLayoutId,
              layoutKey: 'workspace_control',
              label: 'Workspace',
              isDefault: true,
              isActive: true,
            ),
            InterfaceRuntimeLayoutState(
              layoutConfigId: _graphViewLayoutId,
              layoutKey: 'graph_view',
              label: 'Graph',
              isDefault: false,
              isActive: false,
            ),
          ],
          resolvedView: InterfaceResolvedView(
            experienceKey: 'aware_workspace',
            interfacePackageId: UuidValue.fromString(
              '292f93ef-a026-5776-825c-5dfc6d9195fc',
            ),
            interfacePackageName: 'aware-workspace-interface',
            projectionViewId: 'aware_workspace.control.main',
            hostPayload: <String, dynamic>{
              'window_layout': <String, dynamic>{
                'window_key': 'main',
                'layout_config_id': _workspaceControlLayoutId.uuid,
                'layout_key': 'workspace_control',
                'sections': <Map<String, dynamic>>[
                  <String, dynamic>{'section_key': 'center', 'order': 0},
                ],
              },
            },
          ),
        ),
      );

      expect(interfaceHostRuntimeShellAvailable(hostState), isTrue);
      expect(
        interfaceHostRuntimeLayoutConfigId(hostState),
        _workspaceControlLayoutId,
      );
      expect(interfaceHostRuntimeLayoutKey(hostState), 'workspace_control');
      expect(
        interfaceHostRuntimeLayoutStates(
          hostState,
        ).map((layout) => layout.layoutKey).toList(growable: false),
        const <String>['workspace_control', 'graph_view'],
      );
      expect(
        canEnterInterfaceHostRuntimeShell(
          connection: connection,
          hostState: hostState,
        ),
        isTrue,
      );
      expect(
        canEnterInterfaceHostRuntimeShell(
          connection: const InterfaceHostConnectionState(
            service: 'aware_interface_service',
            statusLabel: 'Connected',
            title: 'Interface Host Connected',
            message: 'Connected.',
            connected: true,
            blocksRuntimeEntry: true,
            restartRecommended: false,
            restartReason: null,
            socketPath: '/tmp/interface-control.sock',
            daemonStartedAt: '2026-04-13T00:00:00Z',
            daemonSourceFingerprint: 'current',
            expectedSourceFingerprint: 'current',
            repositoryRoot: '/home/luis/aware',
            stateHome: '/tmp/interface-state',
            defaultEndpoint: 'ws://localhost:8000',
            namespaceCount: 1,
          ),
          hostState: hostState,
        ),
        isFalse,
      );
      expect(
        interfaceHostRuntimeWindowLayoutPayload(
          InterfaceHostState(
            hostLabel: 'interface-flutter-test',
            namespace: 'flutter-test',
            started: true,
            transport: _testTransportState(),
          ),
        ),
        isNull,
      );
    },
  );

  test(
    'interface host runtime shell helpers prefer typed window layout state',
    () {
      final hostState = InterfaceHostState(
        hostLabel: 'interface-flutter-test',
        namespace: 'flutter-test',
        started: true,
        transport: _testTransportState(),
        runtime: InterfaceRuntimeState(
          backend: _testBackendState(),
          activeLayoutConfigId: _workspaceControlLayoutId,
          windowLayout: InterfaceWindowLayoutState(
            sourceKind: 'committed_oig',
            windowKey: 'execution',
            layoutConfigId: _workspaceControlLayoutId,
            layoutKey: 'workspace_control',
            frameMode: 'grid',
            stale: false,
            sections: <InterfaceWindowLayoutSectionState>[
              InterfaceWindowLayoutSectionState(
                sectionKey: 'center',
                order: 0,
                flex: 1,
                isVisible: true,
              ),
            ],
          ),
          resolvedView: InterfaceResolvedView(
            experienceKey: 'aware_workspace',
            interfacePackageName: 'aware-workspace-interface',
            projectionViewId: 'aware_workspace.control.main',
            hostPayload: const <String, dynamic>{},
          ),
        ),
      );

      expect(interfaceHostRuntimeWindowLayoutPayload(hostState), isNull);
      expect(interfaceHostRuntimeWindowLayoutState(hostState), isNotNull);
      expect(interfaceHostRuntimeShellAvailable(hostState), isTrue);
      expect(
        interfaceHostRuntimeLayoutConfigId(hostState),
        _workspaceControlLayoutId,
      );
      expect(interfaceHostRuntimeLayoutKey(hostState), 'workspace_control');
    },
  );

  // The resolveInterfaceHostEntryMode test stayed with modules/interface/representation:
  // it covers the entry-routing helper (src/entry/interface_entry_targeting.dart),
  // not the shell host-state provider.

  test(
    'interface host state provider suppresses follow while host restart is recommended',
    () async {
      final fakeClient = _FakeInterfaceSdkClient(
        initial: _hostState(
          namespace: 'flutter-test',
          screenKey: 'local_service_host_gate',
          title: 'Local Service Host Required',
          message: 'Start the local service host to continue.',
        ),
        followController: _newFollowController(),
        pingResponse: PingResponse(
          protocolVersion: 1,
          success: true,
          service: 'aware_interface_service',
          status: 'ok',
          restartRecommended: true,
          socketPath: '/tmp/interface-control.sock',
          daemonStartedAt: null,
          daemonSourceFingerprint: null,
          repositoryRoot: null,
          stateHome: null,
          defaultEndpoint: null,
          namespaces: const [],
        ),
      );

      final container = ProviderContainer(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
          interfaceControlNamespaceProvider.overrideWith(
            (ref) async => 'flutter-test',
          ),
        ],
      );

      addTearDown(() async {
        container.dispose();
        await fakeClient.followController.close();
      });

      await container.read(interfaceHostStateProvider.future);

      expect(fakeClient.followCalls, 0);
      expect(fakeClient.ensureNamespaceCalls, <String>['flutter-test']);
    },
  );

  test(
    'interface host state provider forwards selected step mutation',
    () async {
      final initial = _hostState(
        namespace: 'flutter-test',
        screenKey: 'local_node_runtime_gate',
        title: 'Local Node Required',
        message: 'Start the local node runtime to continue.',
      );
      final selected = initial.copyWith(
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
      final fakeClient = _FakeInterfaceSdkClient(
        initial: initial,
        followController: _newFollowController(),
        selected: selected,
      );

      final container = ProviderContainer(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
          interfaceControlNamespaceProvider.overrideWith(
            (ref) async => 'flutter-test',
          ),
        ],
      );

      addTearDown(() async {
        container.dispose();
        await fakeClient.followController.close();
      });

      await container.read(interfaceHostStateProvider.future);
      final updated = await container
          .read(interfaceHostStateProvider.notifier)
          .selectStep(stepId: 'environment');

      expect(fakeClient.selectStepCalls, <String?>['environment']);
      expect(updated.controlPlaneWorkspace?.selectedStepId, 'environment');
    },
  );

  test(
    'interface host state provider activates compiled runtime layouts through the control plane',
    () async {
      final initial = _hostState(
        namespace: 'flutter-test',
        screenKey: 'workspace_runtime_layout',
        title: 'Workspace Layout',
        message: 'Workspace control is active.',
      ).copyWith(
        runtime: InterfaceRuntimeState(
          backend: _testBackendState(),
          activeLayoutConfigId: _workspaceControlLayoutId,
          resolvedView: InterfaceResolvedView(
            experienceKey: 'aware_workspace',
            projectionViewId: 'aware_workspace.control.main',
            hostPayload: <String, dynamic>{
              'window_layout': <String, dynamic>{
                'window_key': 'main',
                'layout_config_id': _workspaceControlLayoutId.uuid,
                'layout_key': 'workspace_control',
                'sections': <Map<String, dynamic>>[
                  <String, dynamic>{'section_key': 'center', 'order': 0},
                ],
              },
            },
          ),
        ),
      );
      final selected = initial.copyWith(
        runtime: InterfaceRuntimeState(
          backend: _testBackendState(),
          activeLayoutConfigId: _graphViewLayoutId,
          resolvedView: InterfaceResolvedView(
            experienceKey: 'aware_workspace',
            projectionViewId: 'aware_workspace.graph.center',
            hostPayload: <String, dynamic>{
              'window_layout': <String, dynamic>{
                'window_key': 'main',
                'layout_config_id': _graphViewLayoutId.uuid,
                'layout_key': 'graph_view',
                'sections': <Map<String, dynamic>>[
                  <String, dynamic>{'section_key': 'center', 'order': 0},
                ],
              },
            },
          ),
        ),
      );
      final fakeClient = _FakeInterfaceSdkClient(
        initial: initial,
        followController: _newFollowController(),
        activatedRuntimeFocusState: selected,
      );

      final container = ProviderContainer(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
          interfaceControlNamespaceProvider.overrideWith(
            (ref) async => 'flutter-test',
          ),
        ],
      );

      addTearDown(() async {
        container.dispose();
        await fakeClient.followController.close();
      });

      await container.read(interfaceHostStateProvider.future);
      final updated = await container
          .read(interfaceHostStateProvider.notifier)
          .activateRuntimeLayout(layoutConfigId: _graphViewLayoutId.uuid);

      expect(
        fakeClient.selectRuntimeLayoutCalls,
        <({UuidValue? layoutConfigId})>[(layoutConfigId: _graphViewLayoutId)],
      );
      expect(
        fakeClient.activateRuntimeFocusCalls,
        <({
          UuidValue? representationId,
          UuidValue? layoutConfigId,
          String? layoutKey,
          String? sectionKey,
          UuidValue? observableId,
        })>[],
      );
      expect(interfaceHostRuntimeLayoutConfigId(updated), _graphViewLayoutId);
      expect(interfaceHostRuntimeLayoutKey(updated), 'graph_view');
    },
  );

  test(
    'interface host state provider activates compiled runtime representation ids',
    () async {
      final selected = _hostState(
        namespace: 'flutter-test',
        screenKey: 'workspace_join_gate',
        title: 'Workspace Ready',
        message: 'Representation activated.',
      );
      final fakeClient = _FakeInterfaceSdkClient(
        initial: _hostState(
          namespace: 'flutter-test',
          screenKey: 'workspace_join_gate',
          title: 'Workspace Ready',
          message: 'Workspace runtime available.',
        ),
        followController: _newFollowController(),
        activatedRuntimeFocusState: selected,
      );

      final container = ProviderContainer(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
          interfaceControlNamespaceProvider.overrideWith(
            (ref) async => 'flutter-test',
          ),
        ],
      );

      addTearDown(() async {
        container.dispose();
        await fakeClient.followController.close();
      });

      await container.read(interfaceHostStateProvider.future);
      final updated = await container
          .read(interfaceHostStateProvider.notifier)
          .activateRuntimeRepresentation(
            representationId: '77777777-7777-7777-7777-777777777777',
          );

      expect(
        fakeClient.activateRuntimeFocusCalls,
        <({UuidValue? representationId})>[
          (
            representationId: UuidValue.fromString(
              '77777777-7777-7777-7777-777777777777',
            ),
          ),
        ],
      );
      expect(updated.namespace, 'flutter-test');
    },
  );

  test(
    'interface host state provider re-ensures namespace on refresh drift',
    () async {
      final initial = _hostState(
        namespace: 'flutter-test',
        screenKey: 'local_service_host_gate',
        title: 'Local Service Host Required',
        message: 'Start the local service host to continue.',
      );
      final refreshed = _hostState(
        namespace: 'flutter-test',
        screenKey: 'local_node_runtime_gate',
        title: 'Local Node Required',
        message: 'Recovered after daemon restart.',
      );
      final fakeClient = _FakeInterfaceSdkClient(
        initial: initial,
        followController: _newFollowController(),
        refreshed: refreshed,
        failStatusOnce: true,
      );

      final container = ProviderContainer(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
          interfaceControlNamespaceProvider.overrideWith(
            (ref) async => 'flutter-test',
          ),
        ],
      );

      addTearDown(() async {
        container.dispose();
        await fakeClient.followController.close();
      });

      await container.read(interfaceHostStateProvider.future);
      final updated =
          await container.read(interfaceHostStateProvider.notifier).refresh();

      expect(fakeClient.ensureNamespaceCalls, <String>[
        'flutter-test',
        'flutter-test',
      ]);
      expect(fakeClient.statusCalls, <String>['flutter-test']);
      expect(updated.currentScreen?.screenKey, 'local_node_runtime_gate');
    },
  );

  test(
    'interface host state provider re-ensures namespace after follow drift',
    () async {
      final initial = _hostState(
        namespace: 'flutter-test',
        screenKey: 'local_service_host_gate',
        title: 'Local Service Host Required',
        message: 'Start the local service host to continue.',
      );
      final recovered = _hostState(
        namespace: 'flutter-test',
        screenKey: 'local_node_runtime_gate',
        title: 'Local Node Required',
        message: 'Recovered follow stream after daemon restart.',
      );
      final followController = _newFollowController();
      final fakeClient = _FakeInterfaceSdkClient(
        initial: initial,
        followController: followController,
        failFollowOnce: true,
      );

      final container = ProviderContainer(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(fakeClient),
          interfaceControlNamespaceProvider.overrideWith(
            (ref) async => 'flutter-test',
          ),
          interfaceHostStateFollowReconnectDelayMsProvider.overrideWith(
            (ref) => 10,
          ),
        ],
      );

      addTearDown(() async {
        container.dispose();
        await followController.close();
      });

      await container.read(interfaceHostStateProvider.future);
      await Future<void>.delayed(const Duration(milliseconds: 50));

      followController.add(recovered);
      await Future<void>.delayed(const Duration(milliseconds: 50));

      expect(fakeClient.ensureNamespaceCalls, <String>[
        'flutter-test',
        'flutter-test',
      ]);
      expect(fakeClient.followCalls, 2);
      final latest = container.read(interfaceHostStateProvider).valueOrNull;
      expect(latest?.currentScreen?.screenKey, 'local_node_runtime_gate');
    },
  );

  test('interface host state provider restarts the interface host', () async {
    final initial = _hostState(
      namespace: 'flutter-test',
      screenKey: 'local_node_runtime_gate',
      title: 'Local Node Required',
      message: 'Start the local node runtime to continue.',
    );
    final refreshed = _hostState(
      namespace: 'flutter-test',
      screenKey: 'workspace_start_gate',
      title: 'Start Workspace',
      message: 'Recovered after Interface Host restart.',
    );
    final fakeClient = _FakeInterfaceSdkClient(
      initial: initial,
      followController: _newFollowController(),
      refreshed: refreshed,
    );
    final fakeDaemonController = _FakeInterfaceHostDaemonController();

    final container = ProviderContainer(
      overrides: <Override>[
        interfaceSdkClientProvider.overrideWithValue(fakeClient),
        interfaceHostDaemonControllerProvider.overrideWith(
          (ref) => fakeDaemonController,
        ),
        interfaceControlNamespaceProvider.overrideWith(
          (ref) async => 'flutter-test',
        ),
      ],
    );

    addTearDown(() async {
      container.dispose();
      await fakeClient.followController.close();
    });

    await container.read(interfaceHostStateProvider.future);
    final updated = await container
        .read(interfaceHostStateProvider.notifier)
        .restartInterfaceHost();

    expect(fakeDaemonController.restartCalls, 1);
    expect(
      fakeDaemonController.lastSocketPath,
      '/tmp/aware-interface-provider-test.sock',
    );
    expect(fakeClient.ensureNamespaceCalls, <String>[
      'flutter-test',
      'flutter-test',
    ]);
    expect(updated.currentScreen?.screenKey, 'workspace_start_gate');
  });

  test('interface host state provider commits one full layout vector',
      () async {
    final initial = _hostState(
      namespace: 'flutter-test',
      screenKey: 'runtime_ready',
      title: 'Runtime Ready',
      message: 'Ready for shared layout.',
    );
    final fakeClient = _FakeInterfaceSdkClient(
      initial: initial,
      followController: _newFollowController(),
    );
    final container = ProviderContainer(
      overrides: <Override>[
        interfaceSdkClientProvider.overrideWithValue(fakeClient),
        interfaceControlNamespaceProvider.overrideWith(
          (ref) async => 'flutter-test',
        ),
      ],
    );
    addTearDown(() async {
      container.dispose();
      await fakeClient.followController.close();
    });
    await container.read(interfaceHostStateProvider.future);
    final sectionId = UuidValue.fromString(
      '11111111-1111-4111-8111-111111111111',
    );

    final updated = await container
        .read(interfaceHostStateProvider.notifier)
        .applyAttentionLayoutTransition(
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

    expect(updated.namespace, 'flutter-test');
    expect(fakeClient.layoutTransitionCalls, hasLength(1));
    expect(fakeClient.layoutTransitionCalls.single.clientIntentId, 'drag-1');
    expect(
      fakeClient.layoutTransitionCalls.single.topologyTransitionId?.uuid,
      '88888888-8888-4888-8888-888888888888',
    );
    expect(
      fakeClient.layoutTransitionCalls.single.sectionStates.single
          .layoutConfigSectionConfigId,
      sectionId,
    );
  });

  test('interface host state provider commits one full topology vector',
      () async {
    final initial = _hostState(
      namespace: 'flutter-test',
      screenKey: 'runtime_ready',
      title: 'Runtime Ready',
      message: 'Ready for shared topology.',
    );
    final fakeClient = _FakeInterfaceSdkClient(
      initial: initial,
      followController: _newFollowController(),
    );
    final container = ProviderContainer(
      overrides: <Override>[
        interfaceSdkClientProvider.overrideWithValue(fakeClient),
        interfaceControlNamespaceProvider.overrideWith(
          (ref) async => 'flutter-test',
        ),
      ],
    );
    addTearDown(() async {
      container.dispose();
      await fakeClient.followController.close();
    });
    await container.read(interfaceHostStateProvider.future);
    final sectionIds = <UuidValue>[
      UuidValue.fromString('11111111-1111-4111-8111-111111111111'),
      UuidValue.fromString('22222222-2222-4222-8222-222222222222'),
    ];

    final updated = await container
        .read(interfaceHostStateProvider.notifier)
        .applyAttentionLayoutTopologyTransition(
      clientIntentId: 'topology-1',
      expectedPreviousTopologyTransitionId: UuidValue.fromString(
        '99999999-9999-4999-8999-999999999999',
      ),
      sectionStates: <InterfaceAttentionLayoutTopologyTransitionSectionIntent>[
        for (final (order, sectionId) in sectionIds.indexed)
          InterfaceAttentionLayoutTopologyTransitionSectionIntent(
            layoutConfigSectionConfigId: sectionId,
            order: order,
          ),
      ],
    );

    expect(updated.namespace, 'flutter-test');
    expect(fakeClient.layoutTopologyTransitionCalls, hasLength(1));
    expect(
      fakeClient.layoutTopologyTransitionCalls.single.sectionStates
          .map((section) => section.layoutConfigSectionConfigId),
      sectionIds,
    );
  });
}

class _FakeInterfaceHostDaemonController extends InterfaceHostDaemonController {
  int restartCalls = 0;
  String? lastEndpoint;
  String? lastSocketPath;

  @override
  Future<void> restart({String? endpoint, String? socketPath}) async {
    restartCalls += 1;
    lastEndpoint = endpoint;
    lastSocketPath = socketPath;
  }
}

class _RemoteWorkspaceHostHarness {
  final String namespace = 'flutter-test';
  final String hostLabel = 'workspace-home-story-host';
  final String workspaceRoot = '/home/luis/aware';
  final String defaultEndpoint = 'https://dev.aware.run';
  final String controlPlaneUrl = 'https://dev.aware.run/interface/control';
  final UuidValue actorId = UuidValue.fromString(
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  );
  final UuidValue interfaceId = UuidValue.fromString(
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
  );
  final UuidValue interfaceSessionId = UuidValue.fromString(
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
  );
  final UuidValue environmentId = UuidValue.fromString(
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
  );
  final UuidValue environmentConfigId = UuidValue.fromString(
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
  );

  InterfaceHostTarget get target => InterfaceHostTarget.remote(
        controlPlaneUrl: controlPlaneUrl,
        controlPlaneUri: Uri.parse('wss://dev.aware.run/interface/control'),
        source: InterfaceHostBootstrapSource.explicit,
      );

  PingResponse pingResponse() {
    return PingResponse(
      protocolVersion: 1,
      success: true,
      service: 'aware_interface_service',
      status: 'ok',
      restartRecommended: false,
      socketPath: null,
      daemonStartedAt: '2026-04-23T00:00:00Z',
      daemonSourceFingerprint: 'remote-current',
      expectedSourceFingerprint: 'remote-current',
      repositoryRoot: workspaceRoot,
      stateHome: '/tmp/interface-state',
      defaultEndpoint: defaultEndpoint,
      namespaces: <HostedInterfaceNamespace>[
        HostedInterfaceNamespace(
          namespace: namespace,
          hostLabel: hostLabel,
          started: true,
          actorId: actorId,
          interfaceId: interfaceId,
          interfaceSessionId: interfaceSessionId,
          environmentId: environmentId,
          environmentConfigId: environmentConfigId,
          warnings: const <String>['runtime_unbound'],
        ),
      ],
    );
  }

  InterfaceHostState mountableHostState() {
    final selectedPackage = _selectedSemanticPackage();
    final semanticSource = _semanticSource(selectedPackage);
    return InterfaceHostState(
      hostLabel: hostLabel,
      namespace: namespace,
      started: true,
      transport: _testTransportState(),
      selectedWorkspace: InterfaceSelectedWorkspaceState(
        selectorKey: workspaceRoot,
        label: 'Aware Workspace',
        workspaceRoot: workspaceRoot,
        registrySource: 'workspace_toml',
        compatibilityMode: false,
        workspaceTomlPath: '$workspaceRoot/aware.workspace.toml',
        summary:
            'Workspace semantic/runtime truth was resolved by the deployed Interface Host.',
        environmentCount: 1,
        apiCount: 1,
        serviceCount: 2,
        experienceCount: 1,
        interfaceCount: 1,
        lifecycle: InterfaceWorkspaceLifecycleState(
          status: 'joined',
          summary:
              'Aware Workspace is already mounted on the paired Interface Host.',
          joined: true,
          attachedNamespaceCount: 1,
          joinable: false,
          startable: false,
          recoverable: false,
          leaveable: true,
          stoppable: true,
        ),
        semanticSource: semanticSource,
      ),
      selectedSemanticPackage: InterfaceSelectedSemanticPackageState(
        package: selectedPackage,
        previewStatus: 'preview_available',
        summary:
            'The root interface package is already selected for remote shell bootstrap.',
        previewGraph: InterfaceWorkspaceSemanticObjectConfigGraphPreviewState(
          packageKind: selectedPackage.packageKind,
          packageName: selectedPackage.packageName,
          manifestPath: selectedPackage.manifestRelativePath,
          objectConfigGraphId: selectedPackage.objectConfigGraphId,
          materializeInvocationId: 'workspace-materialize-001',
          materializeReceiptPath:
              '$workspaceRoot/.aware/reports/workspace/materialize-receipt.json',
          laneBranchId: 'workspace-branch-main',
          objectConfigGraph: <String, dynamic>{
            'id': selectedPackage.objectConfigGraphId,
            'name': selectedPackage.packageName,
            'hash': 'preview-hash-${selectedPackage.objectConfigGraphId}',
            'fqn_prefix': selectedPackage.fqnPrefix,
            'language': 'aware',
            'domains': <dynamic>[],
            'domain_relationships': <dynamic>[],
            'object_config_graph_nodes': <dynamic>[],
            'object_config_graph_relationships': <dynamic>[],
          },
        ),
      ),
      runtime: InterfaceRuntimeState(
        backend: _testBackendState(),
        activeLayoutConfigId: _workspaceControlLayoutId,
        layoutStates: <InterfaceRuntimeLayoutState>[
          InterfaceRuntimeLayoutState(
            layoutConfigId: _workspaceControlLayoutId,
            layoutKey: 'workspace_control',
            label: 'Workspace',
            isDefault: true,
            isActive: true,
          ),
          InterfaceRuntimeLayoutState(
            layoutConfigId: _graphViewLayoutId,
            layoutKey: 'graph_view',
            label: 'Graph',
            isDefault: false,
            isActive: false,
          ),
        ],
        resolvedView: InterfaceResolvedView(
          experienceKey: 'aware_workspace',
          interfacePackageId: UuidValue.fromString(
            '292f93ef-a026-5776-825c-5dfc6d9195fc',
          ),
          interfacePackageName: 'aware-workspace-interface',
          projectionViewId: 'aware_workspace.control.main',
          hostPayload: <String, dynamic>{
            'window_layout': <String, dynamic>{
              'window_key': 'main',
              'layout_config_id': _workspaceControlLayoutId.uuid,
              'layout_key': 'workspace_control',
              'frame_mode': 'grid',
              'source_kind': 'remote_host_runtime',
              'sections': const <Map<String, dynamic>>[
                <String, dynamic>{'section_key': 'orchestration', 'order': 0},
                <String, dynamic>{'section_key': 'center', 'order': 1},
                <String, dynamic>{'section_key': 'inspector', 'order': 2},
                <String, dynamic>{'section_key': 'console', 'order': 3},
              ],
            },
          },
        ),
        resolvedPanes: <InterfaceResolvedPaneDescriptor>[
          InterfaceResolvedPaneDescriptor(
            windowKey: 'main',
            layoutKey: 'workspace_control',
            sectionKey: 'center',
            paneKind: 'workspace',
            panePackageId: UuidValue.fromString(
              'fdff6abd-599b-5069-a6fb-66bbb6654e6d',
            ),
            panePackageName: 'aware-workspace-control-pane',
            paneConfigId: UuidValue.fromString(
              '17cde6d7-0d52-54d7-b86d-a3812368dff4',
            ),
            title: 'Workspace Control',
            stateSourceKind: 'section_focus_scope_lane',
          ),
        ],
      ),
    );
  }

  InterfaceWorkspaceCommittedSemanticPackageState _selectedSemanticPackage() {
    return InterfaceWorkspaceCommittedSemanticPackageState(
      selectorKey: 'interface_package:aware_workspace',
      familyKey: 'interface_package',
      familyTitle: 'Interface Packages',
      packageKind: 'interface_package',
      label: 'aware_workspace',
      moduleName: 'aware_workspace',
      packageName: 'aware_workspace',
      awareTomlPath:
          '$workspaceRoot/workspaces/aware_workspace/interfaces/aware_workspace/aware.interface.toml',
      manifestRelativePath:
          'workspaces/aware_workspace/interfaces/aware_workspace/aware.interface.toml',
      packageRoot: 'workspaces/aware_workspace/interfaces/aware_workspace',
      sourcesRoot: 'workspaces/aware_workspace/interfaces/aware_workspace',
      fqnPrefix: 'aware.workspace',
      objectConfigGraphId: 'workspace-interface-ocg',
      objectConfigGraphPackageId: 'workspace-interface-ocg-package',
    );
  }

  InterfaceWorkspaceSemanticSourceState _semanticSource(
    InterfaceWorkspaceCommittedSemanticPackageState selectedPackage,
  ) {
    return InterfaceWorkspaceSemanticSourceState(
      sourceMode: 'bundle_backed',
      summary:
          'The remote Interface Host resolved semantic truth from bundled workspace deployment inputs before mounting runtime state.',
      materializeInvocationId: 'workspace-materialize-001',
      materializeReceiptPath:
          '$workspaceRoot/.aware/reports/workspace/materialize-receipt.json',
      semanticPackages: <InterfaceWorkspaceSemanticPackageState>[
        InterfaceWorkspaceSemanticPackageState(
          packageKind: selectedPackage.packageKind,
          packageName: selectedPackage.packageName,
          manifestPath:
              '$workspaceRoot/${selectedPackage.manifestRelativePath}',
          objectConfigGraphId: selectedPackage.objectConfigGraphId,
        ),
      ],
      committedSemanticPackages: <InterfaceWorkspaceCommittedSemanticPackageState>[
        selectedPackage
      ],
      committedSemanticPackageFamilies: <InterfaceWorkspaceCommittedSemanticPackageFamilyState>[
        InterfaceWorkspaceCommittedSemanticPackageFamilyState(
          familyKey: selectedPackage.familyKey,
          title: selectedPackage.familyTitle,
          members: <InterfaceWorkspaceCommittedSemanticPackageState>[
            selectedPackage,
          ],
        ),
      ],
    );
  }
}

class _FakeInterfaceSdkClient extends InterfaceSdkClient {
  _FakeInterfaceSdkClient({
    required this.initial,
    required this.followController,
    this.selected,
    this.activatedRuntimeFocusState,
    this.actionHostState,
    this.enteredEnvironmentHostState,
    this.enteredAppScreenHostState,
    this.selectedEnvironmentNavigationHostState,
    this.refreshed,
    this.pingResponse,
    this.failStatusOnce = false,
    this.failFollowOnce = false,
  }) : super(serviceClient: _noopServiceApiClient());

  final InterfaceHostState initial;
  final StreamController<InterfaceHostState> followController;
  final InterfaceHostState? selected;
  final InterfaceHostState? activatedRuntimeFocusState;
  final InterfaceHostState? actionHostState;
  final InterfaceHostState? enteredEnvironmentHostState;
  final InterfaceHostState? enteredAppScreenHostState;
  final InterfaceHostState? selectedEnvironmentNavigationHostState;
  final InterfaceHostState? refreshed;
  final PingResponse? pingResponse;
  bool failStatusOnce;
  bool failFollowOnce;
  final List<String?> selectStepCalls = <String?>[];
  final List<
      ({
        String namespace,
        String? paneRef,
        String actionKey,
        InterfaceActionTarget? actionTarget,
        Map<String, dynamic> payload,
      })> actionCalls = <({
    String namespace,
    String? paneRef,
    String actionKey,
    InterfaceActionTarget? actionTarget,
    Map<String, dynamic> payload,
  })>[];
  final List<({UuidValue? layoutConfigId})> selectRuntimeLayoutCalls =
      <({UuidValue? layoutConfigId})>[];
  final List<({UuidValue? representationId})> activateRuntimeFocusCalls =
      <({UuidValue? representationId})>[];
  final List<
      ({
        String clientIntentId,
        UuidValue? expectedPreviousLayoutTransitionId,
        UuidValue? topologyTransitionId,
        List<InterfaceAttentionLayoutTransitionSectionIntent> sectionStates,
      })> layoutTransitionCalls = <({
    String clientIntentId,
    UuidValue? expectedPreviousLayoutTransitionId,
    UuidValue? topologyTransitionId,
    List<InterfaceAttentionLayoutTransitionSectionIntent> sectionStates,
  })>[];
  final List<
      ({
        String clientIntentId,
        UuidValue? expectedPreviousTopologyTransitionId,
        List<
            InterfaceAttentionLayoutTopologyTransitionSectionIntent> sectionStates,
      })> layoutTopologyTransitionCalls = <({
    String clientIntentId,
    UuidValue? expectedPreviousTopologyTransitionId,
    List<InterfaceAttentionLayoutTopologyTransitionSectionIntent> sectionStates,
  })>[];
  final List<
      ({
        String namespace,
        UuidValue? environmentId,
        UuidValue? environmentProfileId,
        UuidValue? actorConfigId,
        UuidValue? classInstanceIdentityId,
        UuidValue? environmentSessionId,
        UuidValue? environmentSessionConfigId,
        String? sessionKey,
        String? sourceKind,
        String? sourceRef,
        Map<String, dynamic> evidence,
      })> enterEnvironmentCalls = <({
    String namespace,
    UuidValue? environmentId,
    UuidValue? environmentProfileId,
    UuidValue? actorConfigId,
    UuidValue? classInstanceIdentityId,
    UuidValue? environmentSessionId,
    UuidValue? environmentSessionConfigId,
    String? sessionKey,
    String? sourceKind,
    String? sourceRef,
    Map<String, dynamic> evidence,
  })>[];
  final List<
      ({
        String namespace,
        UuidValue appPackageId,
        UuidValue appPackageBranchId,
        UuidValue appPackageObjectInstanceGraphCommitId,
        UuidValue appConfigScreenConfigId,
        String? reason,
        Map<String, dynamic> evidence,
      })> enterAppScreenCalls = <({
    String namespace,
    UuidValue appPackageId,
    UuidValue appPackageBranchId,
    UuidValue appPackageObjectInstanceGraphCommitId,
    UuidValue appConfigScreenConfigId,
    String? reason,
    Map<String, dynamic> evidence,
  })>[];
  final List<
      ({
        String namespace,
        UuidValue? environmentNavigationContextId,
        UuidValue? selectedProcessId,
        UuidValue? selectedThreadId,
        String? reason,
        Map<String, dynamic> evidence,
      })> selectEnvironmentNavigationTargetCalls = <({
    String namespace,
    UuidValue? environmentNavigationContextId,
    UuidValue? selectedProcessId,
    UuidValue? selectedThreadId,
    String? reason,
    Map<String, dynamic> evidence,
  })>[];
  final List<String> ensureNamespaceCalls = <String>[];
  final List<String> statusCalls = <String>[];
  int followCalls = 0;

  @override
  Future<PingResponse> ping() async {
    return pingResponse ??
        PingResponse(
          protocolVersion: 1,
          success: true,
          service: 'aware_interface_service',
          status: 'ok',
          restartRecommended: false,
          socketPath: '/tmp/aware-interface-provider-test.sock',
          daemonStartedAt: '2026-04-09T12:30:00Z',
          daemonSourceFingerprint: 'fingerprint-current',
          expectedSourceFingerprint: 'fingerprint-current',
          repositoryRoot: '/home/luis/aware',
          stateHome: '/tmp/aware-interface-provider-test',
          defaultEndpoint: 'ws://localhost:8000',
          namespaces: const [],
        );
  }

  @override
  Future<NamespaceEnsureResponse> ensureNamespace({
    required String namespace,
    String? authToken,
    String? endpoint,
    String? hostLabel,
    UuidValue? environmentConfigId,
  }) async {
    ensureNamespaceCalls.add(namespace);
    final snapshot =
        ensureNamespaceCalls.length > 1 ? (refreshed ?? initial) : initial;
    return NamespaceEnsureResponse(
      protocolVersion: 1,
      success: true,
      namespace: namespace,
      hostState: snapshot,
    );
  }

  @override
  Future<InterfaceStatusResponse> status({required String namespace}) async {
    statusCalls.add(namespace);
    if (failStatusOnce) {
      failStatusOnce = false;
      throw InterfaceSdkClientError(
        operation: 'interface_status',
        error: "'Unknown namespace: $namespace'",
      );
    }
    return InterfaceStatusResponse(
      protocolVersion: 1,
      success: true,
      namespace: namespace,
      hostState: refreshed ?? initial,
    );
  }

  @override
  Stream<InterfaceHostState> follow({
    required String namespace,
    int pollIntervalMs = 1000,
  }) {
    followCalls += 1;
    if (failFollowOnce) {
      failFollowOnce = false;
      return Stream<InterfaceHostState>.error(
        InterfaceSdkClientError(
          operation: 'interface_follow',
          error: "'Unknown namespace: $namespace'",
        ),
      );
    }
    return followController.stream;
  }

  @override
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
    enterEnvironmentCalls.add((
      namespace: namespace,
      environmentId: environmentId,
      environmentProfileId: environmentProfileId,
      actorConfigId: actorConfigId,
      classInstanceIdentityId: classInstanceIdentityId,
      environmentSessionId: environmentSessionId,
      environmentSessionConfigId: environmentSessionConfigId,
      sessionKey: sessionKey,
      sourceKind: sourceKind,
      sourceRef: sourceRef,
      evidence: evidence,
    ));
    return InterfaceEnterEnvironmentResponse(
      protocolVersion: 1,
      success: true,
      namespace: namespace,
      hostState: enteredEnvironmentHostState ?? initial,
    );
  }

  @override
  Future<InterfaceEnterAppScreenResponse> enterAppScreen({
    required String namespace,
    required UuidValue appPackageId,
    required UuidValue appPackageBranchId,
    required UuidValue appPackageObjectInstanceGraphCommitId,
    required UuidValue appConfigScreenConfigId,
    String? reason,
    Map<String, dynamic> evidence = const <String, dynamic>{},
  }) async {
    enterAppScreenCalls.add((
      namespace: namespace,
      appPackageId: appPackageId,
      appPackageBranchId: appPackageBranchId,
      appPackageObjectInstanceGraphCommitId:
          appPackageObjectInstanceGraphCommitId,
      appConfigScreenConfigId: appConfigScreenConfigId,
      reason: reason,
      evidence: evidence,
    ));
    final hostState = enteredAppScreenHostState ?? initial;
    return InterfaceEnterAppScreenResponse(
      operation: 'interface_enter_app_screen',
      protocolVersion: 1,
      success: true,
      namespace: namespace,
      appScreen: hostState.appScreen!,
      hostState: hostState,
    );
  }

  @override
  Future<InterfaceSelectEnvironmentNavigationTargetResponse>
      selectEnvironmentNavigationTarget({
    required String namespace,
    UuidValue? environmentNavigationContextId,
    UuidValue? selectedProcessId,
    UuidValue? selectedThreadId,
    String? reason,
    Map<String, dynamic> evidence = const <String, dynamic>{},
  }) async {
    selectEnvironmentNavigationTargetCalls.add((
      namespace: namespace,
      environmentNavigationContextId: environmentNavigationContextId,
      selectedProcessId: selectedProcessId,
      selectedThreadId: selectedThreadId,
      reason: reason,
      evidence: evidence,
    ));
    return InterfaceSelectEnvironmentNavigationTargetResponse(
      protocolVersion: 1,
      success: true,
      namespace: namespace,
      hostState: selectedEnvironmentNavigationHostState ?? initial,
    );
  }

  @override
  Future<InterfaceSelectStepResponse> selectStep({
    required String namespace,
    String? stepId,
  }) async {
    selectStepCalls.add(stepId);
    return InterfaceSelectStepResponse(
      protocolVersion: 1,
      success: true,
      namespace: namespace,
      stepId: stepId,
      hostState: selected ?? initial,
    );
  }

  @override
  Future<InterfaceActionResponse> action({
    required String namespace,
    required String actionKey,
    String? paneRef,
    InterfaceActionTarget? actionTarget,
    Map<String, dynamic> payload = const <String, dynamic>{},
  }) async {
    actionCalls.add((
      namespace: namespace,
      paneRef: paneRef,
      actionKey: actionKey,
      actionTarget: actionTarget,
      payload: payload,
    ));
    return InterfaceActionResponse(
      protocolVersion: 1,
      success: true,
      namespace: namespace,
      paneRef: paneRef,
      actionKey: actionKey,
      hostState: actionHostState ?? initial,
    );
  }

  @override
  Future<InterfaceSelectRuntimeLayoutResponse> selectRuntimeLayout({
    required String namespace,
    UuidValue? layoutConfigId,
  }) async {
    selectRuntimeLayoutCalls.add((layoutConfigId: layoutConfigId));
    return InterfaceSelectRuntimeLayoutResponse(
      protocolVersion: 1,
      success: true,
      namespace: namespace,
      layoutConfigId: layoutConfigId,
      hostState: activatedRuntimeFocusState ?? initial,
    );
  }

  @override
  Future<InterfaceActivateRuntimeFocusResponse> activateRuntimeFocus({
    required String namespace,
    UuidValue? representationId,
  }) async {
    activateRuntimeFocusCalls.add((representationId: representationId));
    return InterfaceActivateRuntimeFocusResponse(
      protocolVersion: 1,
      success: true,
      namespace: namespace,
      representationId: representationId,
      hostState: activatedRuntimeFocusState ?? initial,
    );
  }

  @override
  Future<InterfaceApplyAttentionLayoutTransitionResponse>
      applyAttentionLayoutTransition({
    required String namespace,
    required String clientIntentId,
    UuidValue? expectedPreviousLayoutTransitionId,
    UuidValue? topologyTransitionId,
    required List<InterfaceAttentionLayoutTransitionSectionIntent>
        sectionStates,
  }) async {
    layoutTransitionCalls.add((
      clientIntentId: clientIntentId,
      expectedPreviousLayoutTransitionId: expectedPreviousLayoutTransitionId,
      topologyTransitionId: topologyTransitionId,
      sectionStates: List<InterfaceAttentionLayoutTransitionSectionIntent>.of(
        sectionStates,
      ),
    ));
    return InterfaceApplyAttentionLayoutTransitionResponse(
      protocolVersion: 1,
      success: true,
      namespace: namespace,
      outcome: 'committed',
      activeLayoutTransitionId: UuidValue.fromString(
        'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
      ),
      hostState: initial,
    );
  }

  @override
  Future<InterfaceApplyAttentionLayoutTopologyTransitionResponse>
      applyAttentionLayoutTopologyTransition({
    required String namespace,
    required String clientIntentId,
    UuidValue? expectedPreviousTopologyTransitionId,
    required List<InterfaceAttentionLayoutTopologyTransitionSectionIntent>
        sectionStates,
  }) async {
    layoutTopologyTransitionCalls.add((
      clientIntentId: clientIntentId,
      expectedPreviousTopologyTransitionId:
          expectedPreviousTopologyTransitionId,
      sectionStates:
          List<InterfaceAttentionLayoutTopologyTransitionSectionIntent>.of(
        sectionStates,
      ),
    ));
    return InterfaceApplyAttentionLayoutTopologyTransitionResponse(
      protocolVersion: 1,
      success: true,
      namespace: namespace,
      outcome: 'committed',
      activeTopologyTransitionId: UuidValue.fromString(
        'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
      ),
      hostState: initial,
    );
  }
}

service_api.AwareInterfaceServiceApiClient _noopServiceApiClient() {
  return service_api.AwareInterfaceServiceApiClient(
    aware_api.AwareApiClient(transport: _NoopAwareApiTransport()),
  );
}

class _NoopAwareApiTransport implements aware_api.AwareApiTransport {
  @override
  Future<aware_api.ApiEndpointResponse> invoke(
    aware_api.ApiEndpointInvocation invocation, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    throw UnimplementedError('No-op Interface test SDK transport.');
  }

  @override
  aware_api.ApiEndpointStream openStream(
    aware_api.ApiEndpointInvocation invocation, {
    Duration timeout = const Duration(seconds: 30),
  }) {
    throw UnimplementedError('No-op Interface test SDK stream transport.');
  }
}

InterfaceHostState _hostState({
  required String namespace,
  required String screenKey,
  required String title,
  required String message,
  InterfaceOperationState? currentOperation,
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
    currentOperation: currentOperation,
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
    available: true,
    databaseExists: false,
    opgCount: 0,
    projectionBundleAvailable: true,
    projectionPlanCount: 0,
    tableCount: 0,
    reason: 'test',
  );
}
