import 'dart:io';

import 'package:aware_shell/aware_shell.dart';
import 'package:aware_shell/src/runtime/interface_host_view_state_sqlite_cache.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:uuid/uuid.dart';

void main() {
  late Directory tempDir;
  late String databasePath;

  setUp(() async {
    tempDir = await Directory.systemTemp.createTemp(
      'aware-shell-host-view-state-cache-',
    );
    databasePath = p.join(tempDir.path, 'host_view_state_cache.sqlite');
  });

  tearDown(() async {
    if (await tempDir.exists()) {
      await tempDir.delete(recursive: true);
    }
  });

  test('persists host view-state cache entries across store reopen', () async {
    final hostState = _hostState(
      namespace: 'control',
      viewStateCursor: _viewStateCursor(digest: 'digest-1'),
      materializedStates: <InterfaceMaterializedPaneState>[
        _materializedState(
          paneStateKey: 'pane-a',
          viewRef: 'aware_control.identity.admission.v1',
          projectionViewKey: 'identity.admission.v1',
        ),
      ],
    );
    final store = SqliteInterfaceHostViewStateCacheStore(
      databasePath: databasePath,
    );
    final cache = InterfaceHostViewStateCache(store);

    final first = await cache.replaceFromHostState(hostState);
    await store.close();

    final reopened = SqliteInterfaceHostViewStateCacheStore(
      databasePath: databasePath,
    );
    addTearDown(reopened.close);
    final persistedCursor = await reopened.viewStateCursor(
      namespace: 'control',
    );
    final persistedEntry = await reopened.readPaneState(
      namespace: 'control',
      paneStateKey: 'pane-a',
      viewRef: 'aware_control.identity.admission.v1',
      projectionViewKey: 'identity.admission.v1',
    );
    final second = await InterfaceHostViewStateCache(
      reopened,
    ).replaceFromHostState(hostState);

    expect(first.storedEntryCount, 1);
    expect(first.removedEntryCount, 0);
    expect(persistedCursor?.digest, 'digest-1');
    expect(persistedCursor?.entryDigests.single.paneStateKey, 'pane-a');
    expect(persistedEntry, isNotNull);
    expect(persistedEntry!.key.interfacePackageName, 'aware-control-interface');
    expect(persistedEntry.materializedState.state, <String, dynamic>{
      'label': 'Ready',
    });
    expect(second.skipped, isTrue);
    expect(second.changed, isFalse);
  });

  test('replaceNamespace transaction evicts stale persisted entries', () async {
    final store = SqliteInterfaceHostViewStateCacheStore(
      databasePath: databasePath,
    );
    addTearDown(store.close);
    final cache = InterfaceHostViewStateCache(store);
    await cache.replaceFromHostState(
      _hostState(
        namespace: 'control',
        viewStateCursor: _viewStateCursor(
          digest: 'digest-1',
          paneKeys: const <String>['pane-a', 'pane-b'],
        ),
        materializedStates: <InterfaceMaterializedPaneState>[
          _materializedState(paneStateKey: 'pane-a'),
          _materializedState(paneStateKey: 'pane-b'),
        ],
      ),
    );

    final result = await cache.replaceFromHostState(
      _hostState(
        namespace: 'control',
        viewStateCursor: _viewStateCursor(
          digest: 'digest-2',
          paneKeys: const <String>['pane-b'],
        ),
        materializedStates: <InterfaceMaterializedPaneState>[
          _materializedState(paneStateKey: 'pane-b'),
        ],
      ),
    );

    expect(result.storedEntryCount, 1);
    expect(result.removedEntryCount, 2);
    expect(await store.viewStateCursor(namespace: 'control'), isNotNull);
    expect(
      await store.readPaneState(namespace: 'control', paneStateKey: 'pane-a'),
      isNull,
    );
    expect(
      await store.readPaneState(namespace: 'control', paneStateKey: 'pane-b'),
      isNotNull,
    );
    expect(await store.entries(namespace: 'control'), hasLength(1));
  });

  test('clear removes one namespace or the whole persisted cache', () async {
    final store = SqliteInterfaceHostViewStateCacheStore(
      databasePath: databasePath,
    );
    addTearDown(store.close);
    final cache = InterfaceHostViewStateCache(store);
    await cache.replaceFromHostState(
      _hostState(
        namespace: 'control',
        viewStateCursor: _viewStateCursor(digest: 'digest-control'),
        materializedStates: <InterfaceMaterializedPaneState>[
          _materializedState(paneStateKey: 'pane-a'),
        ],
      ),
    );
    await cache.replaceFromHostState(
      _hostState(
        namespace: 'agent',
        viewStateCursor: _viewStateCursor(digest: 'digest-agent'),
        materializedStates: <InterfaceMaterializedPaneState>[
          _materializedState(paneStateKey: 'pane-b'),
        ],
      ),
    );

    await store.clear(namespace: 'control');

    expect(await store.entries(namespace: 'control'), isEmpty);
    expect(await store.viewStateCursor(namespace: 'control'), isNull);
    expect(await store.entries(namespace: 'agent'), hasLength(1));

    await store.clear();

    expect(await store.entries(), isEmpty);
    expect(await store.viewStateCursor(namespace: 'agent'), isNull);
  });
}

final _environmentId = UuidValue.fromString(
  '11111111-1111-4111-8111-111111111111',
);
final _environmentConfigId = UuidValue.fromString(
  '22222222-2222-4222-8222-222222222222',
);
final _interfacePackageId = UuidValue.fromString(
  '33333333-3333-4333-8333-333333333333',
);
final _stateModelId = UuidValue.fromString(
  '44444444-4444-4444-8444-444444444444',
);
final _focusScopeId = UuidValue.fromString(
  '55555555-5555-4555-8555-555555555555',
);
final _branchId = UuidValue.fromString('66666666-6666-4666-8666-666666666666');

InterfaceHostState _hostState({
  required String namespace,
  required List<InterfaceMaterializedPaneState> materializedStates,
  InterfaceHostViewStateCursorState? viewStateCursor,
}) {
  return InterfaceHostState(
    hostLabel: 'test-host',
    namespace: namespace,
    environmentId: _environmentId,
    environmentConfigId: _environmentConfigId,
    started: true,
    transport: _testTransportState(),
    runtime: InterfaceRuntimeState(
      backend: _testBackendState(),
      resolvedView: InterfaceResolvedView(
        experienceKey: 'aware_control',
        interfacePackageId: _interfacePackageId,
        interfacePackageName: 'aware-control-interface',
        hostPayload: const <String, dynamic>{},
      ),
      viewStateCursor: viewStateCursor,
      materializedPaneStates: materializedStates,
    ),
  );
}

InterfaceHostViewStateCursorState _viewStateCursor({
  required String digest,
  List<String> paneKeys = const <String>['pane-a'],
}) {
  return InterfaceHostViewStateCursorState(
    cursor: 'view-state:$digest',
    digest: digest,
    materializedEntryCount: paneKeys.length,
    entryDigests: <InterfaceHostViewStateDigestEntryState>[
      for (final paneKey in paneKeys)
        InterfaceHostViewStateDigestEntryState(
          paneStateKey: paneKey,
          digest: '$paneKey-entry-digest',
          viewRef: 'aware_control.identity.admission.v1',
          projectionViewKey: 'identity.admission.v1',
          projectionHash: 'projection-hash',
          headCommitId: 'head-1',
          graphHashPost: 'graph-1',
        ),
    ],
    computedAt: '2026-05-07T10:00:00Z',
  );
}

InterfaceMaterializedPaneState _materializedState({
  required String paneStateKey,
  String viewRef = 'aware_control.identity.admission.v1',
  String projectionViewKey = 'identity.admission.v1',
  String headCommitId = 'head-1',
  String graphHashPost = 'graph-1',
}) {
  return InterfaceMaterializedPaneState(
    paneStateKey: paneStateKey,
    windowKey: 'main',
    layoutKey: 'coordination_center',
    sectionKey: 'primary',
    paneKind: 'identity_admission',
    focusScopeId: _focusScopeId,
    branchId: _branchId,
    projectionViewId: 'identity.admission.v1',
    stateModelId: _stateModelId,
    projectionHash: 'projection-hash',
    status: 'materialized',
    headCommitId: headCommitId,
    graphHashPost: graphHashPost,
    state: const <String, dynamic>{'label': 'Ready'},
    provenance: <String, dynamic>{
      'view_ref': viewRef,
      'projection_view_key': projectionViewKey,
    },
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
