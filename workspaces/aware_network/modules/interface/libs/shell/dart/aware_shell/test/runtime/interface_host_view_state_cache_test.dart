import 'package:aware_shell/aware_shell.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uuid/uuid.dart';

void main() {
  test(
    'replaceFromHostState caches host materialized states by namespace',
    () async {
      final store = MemoryInterfaceHostViewStateCacheStore();
      final cache = InterfaceHostViewStateCache(store);
      final hostState = _hostState(
        namespace: 'control',
        materializedStates: <InterfaceMaterializedPaneState>[
          _materializedState(
            paneStateKey: 'pane-a',
            viewRef: 'aware_control.identity.admission.v1',
            projectionViewKey: 'identity.admission.v1',
          ),
        ],
      );

      final result = await cache.replaceFromHostState(hostState);

      expect(result.namespace, 'control');
      expect(result.storedEntryCount, 1);
      expect(result.removedEntryCount, 0);
      final entry = await store.readPaneState(
        namespace: 'control',
        paneStateKey: 'pane-a',
        viewRef: 'aware_control.identity.admission.v1',
      );
      expect(entry, isNotNull);
      expect(entry!.key.environmentId, _environmentId.uuid);
      expect(entry.key.interfacePackageName, 'aware-control-interface');
      expect(entry.materializedState.state, <String, dynamic>{
        'label': 'Ready',
      });
    },
  );

  test(
    'replaceFromHostState evicts stale pane states for the namespace',
    () async {
      final store = MemoryInterfaceHostViewStateCacheStore();
      final cache = InterfaceHostViewStateCache(store);
      await cache.replaceFromHostState(
        _hostState(
          namespace: 'control',
          materializedStates: <InterfaceMaterializedPaneState>[
            _materializedState(paneStateKey: 'pane-a'),
            _materializedState(paneStateKey: 'pane-b'),
          ],
        ),
      );

      final result = await cache.replaceFromHostState(
        _hostState(
          namespace: 'control',
          materializedStates: <InterfaceMaterializedPaneState>[
            _materializedState(paneStateKey: 'pane-b'),
          ],
        ),
      );

      expect(result.storedEntryCount, 1);
      expect(result.removedEntryCount, 2);
      expect(
        await store.readPaneState(namespace: 'control', paneStateKey: 'pane-a'),
        isNull,
      );
      expect(
        await store.readPaneState(namespace: 'control', paneStateKey: 'pane-b'),
        isNotNull,
      );
    },
  );

  test('replaceFromHostState skips unchanged namespace cursor', () async {
    final store = MemoryInterfaceHostViewStateCacheStore();
    final cache = InterfaceHostViewStateCache(store);
    final cursor = _viewStateCursor();
    final hostState = _hostState(
      namespace: 'control',
      viewStateCursor: cursor,
      materializedStates: <InterfaceMaterializedPaneState>[
        _materializedState(paneStateKey: 'pane-a'),
      ],
    );

    final first = await cache.replaceFromHostState(hostState);
    final second = await cache.replaceFromHostState(hostState);

    expect(first.skipped, isFalse);
    expect(first.cursor, 'view-state:digest-1');
    expect(first.digest, 'digest-1');
    expect(second.skipped, isTrue);
    expect(second.changed, isFalse);
    expect(second.storedEntryCount, 0);
    expect(second.removedEntryCount, 0);
    expect((await store.entries(namespace: 'control')), hasLength(1));
    expect(
      (await store.viewStateCursor(namespace: 'control'))?.digest,
      'digest-1',
    );
  });

  test('provenance changes produce distinct cache keys', () {
    final first = InterfaceHostViewStateCacheKey.fromMaterializedState(
      namespace: 'control',
      materializedState: _materializedState(
        paneStateKey: 'pane-a',
        headCommitId: 'head-1',
        graphHashPost: 'graph-1',
      ),
    );
    final second = InterfaceHostViewStateCacheKey.fromMaterializedState(
      namespace: 'control',
      materializedState: _materializedState(
        paneStateKey: 'pane-a',
        headCommitId: 'head-2',
        graphHashPost: 'graph-2',
      ),
    );

    expect(first, isNot(second));
    expect(first.cacheKey, isNot(second.cacheKey));
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

InterfaceHostViewStateCursorState _viewStateCursor() {
  return InterfaceHostViewStateCursorState(
    cursor: 'view-state:digest-1',
    digest: 'digest-1',
    materializedEntryCount: 1,
    entryDigests: <InterfaceHostViewStateDigestEntryState>[
      InterfaceHostViewStateDigestEntryState(
        paneStateKey: 'pane-a',
        digest: 'entry-digest-1',
        viewRef: 'aware_control.identity.admission.v1',
        projectionViewKey: 'identity.admission.v1',
        projectionHash: 'projection-hash',
        headCommitId: 'head-1',
        graphHashPost: 'graph-1',
      ),
    ],
    computedAt: '2026-05-07T09:00:00Z',
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
