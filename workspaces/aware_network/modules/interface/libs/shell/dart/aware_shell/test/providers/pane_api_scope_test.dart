import 'dart:io';

import 'package:aware_api/aware_api.dart' as aware_api;
import 'package:aware_interface_service_api/aware_interface_service_api.dart'
    as service_api;
import 'package:aware_pane/aware_pane.dart' as runtime;
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:aware_shell/aware_shell.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:uuid/uuid.dart';

void main() {
  testWidgets('decodes host materialized view state from pane context', (
    tester,
  ) async {
    final materializedState = InterfaceMaterializedPaneState(
      paneStateKey: 'main:layout:section:identity:test-pane:hash',
      windowKey: 'main',
      layoutKey: 'layout',
      sectionKey: 'section',
      paneKind: 'identity',
      status: 'materialized',
      state: const <String, dynamic>{'label': 'Ready'},
      provenance: const <String, dynamic>{},
    );
    final registry = InterfaceViewStateDecoderRegistry.fromDecoderMaps(
      <Map<String, InterfaceViewStateDecoder>>[
        <String, InterfaceViewStateDecoder>{
          'aware_test.identity.profile.v1': FakeViewState.fromJson,
        },
      ],
    );
    final paneContext = PaneContext(
      paneId: 'identity',
      kind: 'identity',
      parameters: <String, dynamic>{
        kPaneParamPaneStateKey: materializedState.paneStateKey,
        kPaneParamViewRef: 'aware_test.identity.profile.v1',
        kPaneParamViewKey: 'identity.profile.v1',
      },
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          interfacePaneMaterializedStatesProvider.overrideWithValue(
            <InterfaceMaterializedPaneState>[materializedState],
          ),
          interfacePaneViewStateDecoderRegistryProvider.overrideWithValue(
            registry,
          ),
        ],
        child: Directionality(
          textDirection: TextDirection.ltr,
          child: Consumer(
            builder: (context, ref, _) {
              final result = interfacePaneViewStateForContext<FakeViewState>(
                ref,
                paneContext,
              );
              return Text('${result.status}:${result.value?.label}');
            },
          ),
        ),
      ),
    );

    expect(
      find.text('${InterfaceViewStateDecodeStatus.decoded}:Ready'),
      findsOneWidget,
    );
  });

  testWidgets('reads cached host view state from pane context', (tester) async {
    final store = MemoryInterfaceHostViewStateCacheStore();
    final materializedState = InterfaceMaterializedPaneState(
      paneStateKey: 'main:layout:section:identity:test-pane:hash',
      windowKey: 'main',
      layoutKey: 'layout',
      sectionKey: 'section',
      paneKind: 'identity',
      status: 'materialized',
      state: const <String, dynamic>{'label': 'Cached'},
      provenance: const <String, dynamic>{
        'view_ref': 'aware_test.identity.profile.v1',
        'projection_view_key': 'identity.profile.v1',
      },
    );
    await store.replaceNamespace(
      namespace: 'control',
      entries: <InterfaceHostViewStateCacheEntry>[
        InterfaceHostViewStateCacheEntry.fromMaterializedState(
          namespace: 'control',
          interfacePackageName: 'aware-control-interface',
          materializedState: materializedState,
        ),
      ],
    );
    final paneContext = PaneContext(
      paneId: 'identity',
      kind: 'identity',
      parameters: <String, dynamic>{
        kPaneParamPaneStateKey: materializedState.paneStateKey,
        kPaneParamViewRef: 'aware_test.identity.profile.v1',
        kPaneParamViewKey: 'identity.profile.v1',
      },
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          interfacePaneApiNamespaceProvider.overrideWithValue('control'),
          interfaceHostViewStateCacheStoreProvider.overrideWithValue(store),
        ],
        child: Directionality(
          textDirection: TextDirection.ltr,
          child: Consumer(
            builder: (context, ref, _) {
              return FutureBuilder<InterfaceHostViewStateCacheEntry?>(
                future: interfaceCachedPaneViewStateForContext(
                  ref,
                  paneContext,
                ),
                builder: (context, snapshot) {
                  final label =
                      snapshot.data?.materializedState.state['label'] ??
                      'missing';
                  return Text('$label');
                },
              );
            },
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Cached'), findsOneWidget);
  });

  test('cache store provider resolves configured SQLite store', () async {
    final tempDir = await Directory.systemTemp.createTemp(
      'aware-shell-pane-api-cache-provider-',
    );
    addTearDown(() async {
      if (await tempDir.exists()) {
        await tempDir.delete(recursive: true);
      }
    });
    final config = InterfaceHostViewStateCacheStoreConfig.sqlite(
      databasePath: p.join(tempDir.path, 'host_view_state_cache.sqlite'),
    );
    final materializedState = InterfaceMaterializedPaneState(
      paneStateKey: 'pane-a',
      windowKey: 'main',
      layoutKey: 'layout',
      sectionKey: 'section',
      paneKind: 'identity',
      status: 'materialized',
      state: const <String, dynamic>{'label': 'Provider'},
      provenance: const <String, dynamic>{
        'view_ref': 'aware_test.identity.profile.v1',
        'projection_view_key': 'identity.profile.v1',
      },
    );

    final firstContainer = ProviderContainer(
      overrides: <Override>[
        interfaceHostViewStateCacheStoreConfigProvider.overrideWithValue(
          config,
        ),
      ],
    );
    final firstStore = firstContainer.read(
      interfaceHostViewStateCacheStoreProvider,
    );
    await firstStore.replaceNamespace(
      namespace: 'control',
      entries: <InterfaceHostViewStateCacheEntry>[
        InterfaceHostViewStateCacheEntry.fromMaterializedState(
          namespace: 'control',
          materializedState: materializedState,
        ),
      ],
      viewStateCursor: _viewStateCursor(),
    );
    await _closeStore(firstStore);
    firstContainer.dispose();

    final reopenedContainer = ProviderContainer(
      overrides: <Override>[
        interfaceHostViewStateCacheStoreConfigProvider.overrideWithValue(
          config,
        ),
      ],
    );
    addTearDown(reopenedContainer.dispose);
    final reopenedStore = reopenedContainer.read(
      interfaceHostViewStateCacheStoreProvider,
    );
    addTearDown(() => _closeStore(reopenedStore));

    final entry = await reopenedStore.readPaneState(
      namespace: 'control',
      paneStateKey: 'pane-a',
      viewRef: 'aware_test.identity.profile.v1',
      projectionViewKey: 'identity.profile.v1',
    );

    expect(entry?.materializedState.state, <String, dynamic>{
      'label': 'Provider',
    });
  });

  testWidgets('reports renderer capabilities through pane API scope', (
    tester,
  ) async {
    final sdkClient = _FakeInterfaceSdkClient();
    final packageRuntime = _packageRuntime();

    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(sdkClient),
        ],
        child: InterfacePaneApiScope(
          namespace: 'control',
          child: Directionality(
            textDirection: TextDirection.ltr,
            child: InterfaceRendererCapabilityHandshakeSync(
              rendererId: 'flutter-control',
              interfacePackageRuntime: packageRuntime,
              child: Consumer(
                builder: (context, ref, _) {
                  final status = ref.watch(
                    interfaceRendererCapabilityHandshakeStatusProvider,
                  );
                  return Text('handshake:${status.phase.name}');
                },
              ),
            ),
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('handshake:ready'), findsOneWidget);
    expect(sdkClient.reportedNamespaces, <String>['control']);
    expect(sdkClient.reportedCapabilities.single.rendererId, 'flutter-control');
    expect(
      sdkClient.reportedCapabilities.single.viewCapabilities.single.hasDecoder,
      isTrue,
    );
    expect(
      sdkClient.reportedCapabilities.single.cache?.supportsCursorLookup,
      isTrue,
    );
  });

  testWidgets('syncs view-state cursor through pane API scope', (tester) async {
    final sdkClient = _FakeInterfaceSdkClient();
    Future<InterfaceSyncViewStateCursorResponse>? pendingResponse;

    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          interfaceSdkClientProvider.overrideWithValue(sdkClient),
        ],
        child: InterfacePaneApiScope(
          namespace: 'control',
          child: Directionality(
            textDirection: TextDirection.ltr,
            child: Consumer(
              builder: (context, ref, _) {
                pendingResponse ??= interfaceSyncViewStateCursor(
                  ref,
                  rendererId: 'flutter-control',
                  knownCursor: 'view-state:digest-1',
                  knownDigest: 'digest-1',
                );
                return const Text('syncing');
              },
            ),
          ),
        ),
      ),
    );

    final response = await pendingResponse;

    expect(response?.changed, isFalse);
    expect(sdkClient.syncedCursorNamespaces, <String>['control']);
    expect(sdkClient.syncedKnownCursors, <String?>['view-state:digest-1']);
    expect(sdkClient.syncedKnownDigests, <String?>['digest-1']);
  });
}

class FakeViewState {
  const FakeViewState({required this.label});

  factory FakeViewState.fromJson(Map<String, dynamic> json) {
    return FakeViewState(label: json['label'] as String);
  }

  final String label;
}

InterfacePackageRuntime _packageRuntime() {
  final panePackageId = UuidValue.fromString(
    '99999999-9999-4999-8999-999999999999',
  );
  final registry = PanePackageRegistry()
    ..registerPanePackage(
      panePackageId: panePackageId,
      panePackageName: 'identity-admission-pane',
      paneKind: 'identity_admission',
      factory: (_) => const SizedBox.shrink(),
      capabilities: const runtime.PaneCapabilities(),
    );
  return InterfacePackageRuntime(
    interfacePackageId: '33333333-3333-4333-8333-333333333333',
    interfacePackageName: 'aware-control-interface',
    panePackageRegistry: registry,
    experienceKeys: const <String>['aware_control_identity'],
    sectionRepresentations:
        const <InterfacePackageRuntimeSectionRepresentation>[
          InterfacePackageRuntimeSectionRepresentation(
            representationId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
            windowKey: 'main',
            layoutKey: 'coordination_center',
            sectionKey: 'workspace',
            paneName: 'identity',
            paneKind: 'identity_admission',
            label: 'Identity',
            observableId: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
            viewRef: 'aware_identity.profile.home.v1',
            projectionViewKey: 'profile.home.v1',
          ),
        ],
    viewStateDecoderRegistry: InterfaceViewStateDecoderRegistry.fromDecoderMaps(
      <Map<String, InterfaceViewStateDecoder>>[
        <String, InterfaceViewStateDecoder>{
          'aware_identity.profile.home.v1': FakeViewState.fromJson,
        },
      ],
    ),
  );
}

class _FakeInterfaceSdkClient extends InterfaceSdkClient {
  _FakeInterfaceSdkClient() : super(serviceClient: _noopServiceApiClient());

  final List<String> reportedNamespaces = <String>[];
  final List<InterfaceRendererCapabilitiesState> reportedCapabilities =
      <InterfaceRendererCapabilitiesState>[];
  final List<String> syncedCursorNamespaces = <String>[];
  final List<String?> syncedKnownCursors = <String?>[];
  final List<String?> syncedKnownDigests = <String?>[];

  @override
  Future<InterfaceReportRendererCapabilitiesResponse>
  reportRendererCapabilities({
    required String namespace,
    required InterfaceRendererCapabilitiesState rendererCapabilities,
  }) async {
    reportedNamespaces.add(namespace);
    reportedCapabilities.add(rendererCapabilities);
    return InterfaceReportRendererCapabilitiesResponse(
      protocolVersion: 1,
      success: true,
      namespace: namespace,
      hostState: InterfaceHostState(
        hostLabel: 'interface-shell-test',
        namespace: namespace,
        started: true,
        transport: _testTransportState(),
        rendererCapabilities: rendererCapabilities,
      ),
    );
  }

  @override
  Future<InterfaceSyncViewStateCursorResponse> syncViewStateCursor({
    required String namespace,
    String? rendererId,
    String? knownCursor,
    String? knownDigest,
  }) async {
    syncedCursorNamespaces.add(namespace);
    syncedKnownCursors.add(knownCursor);
    syncedKnownDigests.add(knownDigest);
    return InterfaceSyncViewStateCursorResponse(
      protocolVersion: 1,
      success: true,
      namespace: namespace,
      changed: false,
      viewStateCursor: _viewStateCursor(),
      hostState: InterfaceHostState(
        hostLabel: 'interface-shell-test',
        namespace: namespace,
        started: true,
        transport: _testTransportState(),
        runtime: InterfaceRuntimeState(
          backend: _testBackendState(),
          viewStateCursor: _viewStateCursor(),
        ),
      ),
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
    throw UnimplementedError('No-op Interface pane API test transport.');
  }

  @override
  aware_api.ApiEndpointStream openStream(
    aware_api.ApiEndpointInvocation invocation, {
    Duration timeout = const Duration(seconds: 30),
  }) {
    throw UnimplementedError('No-op Interface pane API test stream transport.');
  }
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
      ),
    ],
    computedAt: '2026-05-07T09:00:00Z',
  );
}

Future<void> _closeStore(InterfaceHostViewStateCacheStore store) async {
  if (store is InterfaceHostViewStateCacheStoreLifecycle) {
    await (store as InterfaceHostViewStateCacheStoreLifecycle).close();
  }
}
