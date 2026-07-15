import 'dart:io';

import 'package:aware_shell/aware_shell.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:uuid/uuid.dart';

void main() {
  test('builds a memory cache store by default', () async {
    final store = buildInterfaceHostViewStateCacheStore(
      const InterfaceHostViewStateCacheStoreConfig.memory(),
    );
    addTearDown(() => _closeStore(store));

    expect(store, isA<MemoryInterfaceHostViewStateCacheStore>());
  });

  test('rejects empty SQLite cache paths', () {
    expect(
      () => InterfaceHostViewStateCacheStoreConfig.sqlite(databasePath: ' '),
      throwsArgumentError,
    );
  });

  test('uses configured SQLite persistence on IO runtimes', () async {
    final tempDir = await Directory.systemTemp.createTemp(
      'aware-shell-host-view-state-cache-factory-',
    );
    addTearDown(() async {
      if (await tempDir.exists()) {
        await tempDir.delete(recursive: true);
      }
    });
    final config = InterfaceHostViewStateCacheStoreConfig.sqlite(
      databasePath: p.join(tempDir.path, 'host_view_state_cache.sqlite'),
    );
    final entry = _cacheEntry();
    final cursor = _viewStateCursor();

    final first = buildInterfaceHostViewStateCacheStore(config);
    await first.replaceNamespace(
      namespace: 'control',
      entries: <InterfaceHostViewStateCacheEntry>[entry],
      viewStateCursor: cursor,
    );
    await _closeStore(first);

    final reopened = buildInterfaceHostViewStateCacheStore(config);
    addTearDown(() => _closeStore(reopened));

    final persistedCursor = await reopened.viewStateCursor(
      namespace: 'control',
    );
    final persistedEntry = await reopened.readPaneState(
      namespace: 'control',
      paneStateKey: 'pane-a',
      viewRef: 'aware_control.identity.admission.v1',
      projectionViewKey: 'identity.admission.v1',
    );
    final skipped = await reopened.replaceNamespace(
      namespace: 'control',
      entries: <InterfaceHostViewStateCacheEntry>[entry],
      viewStateCursor: cursor,
    );

    expect(persistedCursor?.digest, 'digest-1');
    expect(persistedEntry?.materializedState.state, <String, dynamic>{
      'label': 'Factory',
    });
    expect(skipped.skipped, isTrue);
  });
}

Future<void> _closeStore(InterfaceHostViewStateCacheStore store) async {
  if (store is InterfaceHostViewStateCacheStoreLifecycle) {
    await (store as InterfaceHostViewStateCacheStoreLifecycle).close();
  }
}

final _stateModelId = UuidValue.fromString(
  '44444444-4444-4444-8444-444444444444',
);
final _focusScopeId = UuidValue.fromString(
  '55555555-5555-4555-8555-555555555555',
);
final _branchId = UuidValue.fromString('66666666-6666-4666-8666-666666666666');

InterfaceHostViewStateCacheEntry _cacheEntry() {
  return InterfaceHostViewStateCacheEntry.fromMaterializedState(
    namespace: 'control',
    interfacePackageName: 'aware-control-interface',
    materializedState: InterfaceMaterializedPaneState(
      paneStateKey: 'pane-a',
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
      headCommitId: 'head-1',
      graphHashPost: 'graph-1',
      state: const <String, dynamic>{'label': 'Factory'},
      provenance: const <String, dynamic>{
        'view_ref': 'aware_control.identity.admission.v1',
        'projection_view_key': 'identity.admission.v1',
      },
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
        digest: 'pane-a-entry-digest',
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
