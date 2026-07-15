import 'package:aware_interface_service_api/aware_interface_service_api.dart';
import 'package:flutter/foundation.dart';

@immutable
class InterfaceHostViewStateCacheKey {
  const InterfaceHostViewStateCacheKey({
    required this.namespace,
    required this.paneStateKey,
    this.environmentId,
    this.environmentConfigId,
    this.interfacePackageId,
    this.interfacePackageName,
    this.windowKey,
    this.layoutKey,
    this.sectionKey,
    this.paneKind,
    this.paneConfigId,
    this.panePackageId,
    this.focusScopeId,
    this.branchId,
    this.projectionExperienceViewId,
    this.projectionViewId,
    this.viewRef,
    this.projectionViewKey,
    this.stateModelId,
    this.projectionHash,
    this.headCommitId,
    this.graphHashPost,
  });

  factory InterfaceHostViewStateCacheKey.fromMaterializedState({
    required String namespace,
    required InterfaceMaterializedPaneState materializedState,
    String? environmentId,
    String? environmentConfigId,
    String? interfacePackageId,
    String? interfacePackageName,
  }) {
    return InterfaceHostViewStateCacheKey(
      namespace: _requiredToken(namespace, 'namespace'),
      environmentId: _trimmedOrNull(environmentId),
      environmentConfigId: _trimmedOrNull(environmentConfigId),
      interfacePackageId: _trimmedOrNull(interfacePackageId),
      interfacePackageName: _trimmedOrNull(interfacePackageName),
      paneStateKey: _requiredToken(
        materializedState.paneStateKey,
        'paneStateKey',
      ),
      windowKey: _trimmedOrNull(materializedState.windowKey),
      layoutKey: _trimmedOrNull(materializedState.layoutKey),
      sectionKey: _trimmedOrNull(materializedState.sectionKey),
      paneKind: _trimmedOrNull(materializedState.paneKind),
      paneConfigId: materializedState.paneConfigId?.uuid,
      panePackageId: materializedState.panePackageId?.uuid,
      focusScopeId: materializedState.focusScopeId?.uuid,
      branchId: materializedState.branchId?.uuid,
      projectionExperienceViewId:
          materializedState.projectionExperienceViewId?.uuid,
      projectionViewId: _trimmedOrNull(materializedState.projectionViewId),
      viewRef: _stringFromMap(materializedState.provenance, 'view_ref'),
      projectionViewKey: _stringFromMap(
        materializedState.provenance,
        'projection_view_key',
      ),
      stateModelId: materializedState.stateModelId?.uuid,
      projectionHash: _trimmedOrNull(materializedState.projectionHash),
      headCommitId: _trimmedOrNull(materializedState.headCommitId),
      graphHashPost: _trimmedOrNull(materializedState.graphHashPost),
    );
  }

  factory InterfaceHostViewStateCacheKey.fromJson(Map<String, dynamic> json) {
    return InterfaceHostViewStateCacheKey(
      namespace: json['namespace'] as String,
      paneStateKey: json['pane_state_key'] as String,
      environmentId: json['environment_id'] as String?,
      environmentConfigId: json['environment_config_id'] as String?,
      interfacePackageId: json['interface_package_id'] as String?,
      interfacePackageName: json['interface_package_name'] as String?,
      windowKey: json['window_key'] as String?,
      layoutKey: json['layout_key'] as String?,
      sectionKey: json['section_key'] as String?,
      paneKind: json['pane_kind'] as String?,
      paneConfigId: json['pane_config_id'] as String?,
      panePackageId: json['pane_package_id'] as String?,
      focusScopeId: json['focus_scope_id'] as String?,
      branchId: json['branch_id'] as String?,
      projectionExperienceViewId:
          json['projection_experience_view_id'] as String?,
      projectionViewId: json['projection_view_id'] as String?,
      viewRef: json['view_ref'] as String?,
      projectionViewKey: json['projection_view_key'] as String?,
      stateModelId: json['state_model_id'] as String?,
      projectionHash: json['projection_hash'] as String?,
      headCommitId: json['head_commit_id'] as String?,
      graphHashPost: json['graph_hash_post'] as String?,
    );
  }

  final String namespace;
  final String paneStateKey;
  final String? environmentId;
  final String? environmentConfigId;
  final String? interfacePackageId;
  final String? interfacePackageName;
  final String? windowKey;
  final String? layoutKey;
  final String? sectionKey;
  final String? paneKind;
  final String? paneConfigId;
  final String? panePackageId;
  final String? focusScopeId;
  final String? branchId;
  final String? projectionExperienceViewId;
  final String? projectionViewId;
  final String? viewRef;
  final String? projectionViewKey;
  final String? stateModelId;
  final String? projectionHash;
  final String? headCommitId;
  final String? graphHashPost;

  String get cacheKey => <String>[
    namespace,
    environmentId ?? '',
    environmentConfigId ?? '',
    interfacePackageId ?? '',
    interfacePackageName ?? '',
    paneStateKey,
    windowKey ?? '',
    layoutKey ?? '',
    sectionKey ?? '',
    paneKind ?? '',
    paneConfigId ?? '',
    panePackageId ?? '',
    focusScopeId ?? '',
    branchId ?? '',
    projectionExperienceViewId ?? '',
    projectionViewId ?? '',
    viewRef ?? '',
    projectionViewKey ?? '',
    stateModelId ?? '',
    projectionHash ?? '',
    headCommitId ?? '',
    graphHashPost ?? '',
  ].join('\n');

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'namespace': namespace,
      'pane_state_key': paneStateKey,
      'environment_id': environmentId,
      'environment_config_id': environmentConfigId,
      'interface_package_id': interfacePackageId,
      'interface_package_name': interfacePackageName,
      'window_key': windowKey,
      'layout_key': layoutKey,
      'section_key': sectionKey,
      'pane_kind': paneKind,
      'pane_config_id': paneConfigId,
      'pane_package_id': panePackageId,
      'focus_scope_id': focusScopeId,
      'branch_id': branchId,
      'projection_experience_view_id': projectionExperienceViewId,
      'projection_view_id': projectionViewId,
      'view_ref': viewRef,
      'projection_view_key': projectionViewKey,
      'state_model_id': stateModelId,
      'projection_hash': projectionHash,
      'head_commit_id': headCommitId,
      'graph_hash_post': graphHashPost,
    };
  }

  bool matchesPaneLookup({
    required String namespace,
    required String paneStateKey,
    String? viewRef,
    String? projectionViewKey,
  }) {
    if (this.namespace != _requiredToken(namespace, 'namespace')) {
      return false;
    }
    if (this.paneStateKey != _requiredToken(paneStateKey, 'paneStateKey')) {
      return false;
    }
    final normalizedViewRef = _trimmedOrNull(viewRef);
    if (normalizedViewRef != null && this.viewRef != normalizedViewRef) {
      return false;
    }
    final normalizedViewKey = _trimmedOrNull(projectionViewKey);
    if (normalizedViewKey != null &&
        this.projectionViewKey != normalizedViewKey) {
      return false;
    }
    return true;
  }

  @override
  bool operator ==(Object other) {
    return other is InterfaceHostViewStateCacheKey &&
        other.cacheKey == cacheKey;
  }

  @override
  int get hashCode => cacheKey.hashCode;

  @override
  String toString() => 'InterfaceHostViewStateCacheKey($cacheKey)';
}

@immutable
class InterfaceHostViewStateCacheEntry {
  const InterfaceHostViewStateCacheEntry({
    required this.key,
    required this.materializedState,
  });

  factory InterfaceHostViewStateCacheEntry.fromMaterializedState({
    required String namespace,
    required InterfaceMaterializedPaneState materializedState,
    String? environmentId,
    String? environmentConfigId,
    String? interfacePackageId,
    String? interfacePackageName,
  }) {
    return InterfaceHostViewStateCacheEntry(
      key: InterfaceHostViewStateCacheKey.fromMaterializedState(
        namespace: namespace,
        materializedState: materializedState,
        environmentId: environmentId,
        environmentConfigId: environmentConfigId,
        interfacePackageId: interfacePackageId,
        interfacePackageName: interfacePackageName,
      ),
      materializedState: materializedState,
    );
  }

  factory InterfaceHostViewStateCacheEntry.fromJson(Map<String, dynamic> json) {
    return InterfaceHostViewStateCacheEntry(
      key: InterfaceHostViewStateCacheKey.fromJson(
        Map<String, dynamic>.from(json['key'] as Map),
      ),
      materializedState: InterfaceMaterializedPaneState.fromJson(
        Map<String, dynamic>.from(json['materialized_state'] as Map),
      ),
    );
  }

  final InterfaceHostViewStateCacheKey key;
  final InterfaceMaterializedPaneState materializedState;

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'key': key.toJson(),
      'materialized_state': materializedState.toJson(),
    };
  }
}

@immutable
class InterfaceHostViewStateCacheSyncResult {
  const InterfaceHostViewStateCacheSyncResult({
    required this.namespace,
    required this.storedEntryCount,
    required this.removedEntryCount,
    this.cursor,
    this.digest,
    this.skipped = false,
  });

  final String namespace;
  final int storedEntryCount;
  final int removedEntryCount;
  final String? cursor;
  final String? digest;
  final bool skipped;

  bool get changed =>
      !skipped && (storedEntryCount > 0 || removedEntryCount > 0);
}

enum InterfaceHostViewStateCacheStoreKind { memory, sqlite }

@immutable
class InterfaceHostViewStateCacheStoreConfig {
  const InterfaceHostViewStateCacheStoreConfig.memory()
    : storeKind = InterfaceHostViewStateCacheStoreKind.memory,
      databasePath = null;

  InterfaceHostViewStateCacheStoreConfig.sqlite({required String databasePath})
    : storeKind = InterfaceHostViewStateCacheStoreKind.sqlite,
      databasePath = _requiredToken(databasePath, 'databasePath');

  final InterfaceHostViewStateCacheStoreKind storeKind;
  final String? databasePath;

  @override
  bool operator ==(Object other) {
    return other is InterfaceHostViewStateCacheStoreConfig &&
        other.storeKind == storeKind &&
        other.databasePath == databasePath;
  }

  @override
  int get hashCode => Object.hash(storeKind, databasePath);
}

abstract interface class InterfaceHostViewStateCacheStore {
  Future<InterfaceHostViewStateCacheEntry?> read(
    InterfaceHostViewStateCacheKey key,
  );

  Future<InterfaceHostViewStateCacheEntry?> readPaneState({
    required String namespace,
    required String paneStateKey,
    String? viewRef,
    String? projectionViewKey,
  });

  Future<List<InterfaceHostViewStateCacheEntry>> entries({String? namespace});

  Future<InterfaceHostViewStateCursorState?> viewStateCursor({
    required String namespace,
  });

  Future<InterfaceHostViewStateCacheSyncResult> replaceNamespace({
    required String namespace,
    required Iterable<InterfaceHostViewStateCacheEntry> entries,
    InterfaceHostViewStateCursorState? viewStateCursor,
  });

  Future<void> clear({String? namespace});
}

abstract interface class InterfaceHostViewStateCacheStoreLifecycle {
  Future<void> close();
}

class MemoryInterfaceHostViewStateCacheStore
    implements InterfaceHostViewStateCacheStore {
  final Map<String, InterfaceHostViewStateCacheEntry> _entries =
      <String, InterfaceHostViewStateCacheEntry>{};
  final Map<String, InterfaceHostViewStateCursorState> _cursors =
      <String, InterfaceHostViewStateCursorState>{};

  @override
  Future<InterfaceHostViewStateCacheEntry?> read(
    InterfaceHostViewStateCacheKey key,
  ) async {
    return _entries[key.cacheKey];
  }

  @override
  Future<InterfaceHostViewStateCacheEntry?> readPaneState({
    required String namespace,
    required String paneStateKey,
    String? viewRef,
    String? projectionViewKey,
  }) async {
    final matches = _entries.values.where(
      (entry) => entry.key.matchesPaneLookup(
        namespace: namespace,
        paneStateKey: paneStateKey,
        viewRef: viewRef,
        projectionViewKey: projectionViewKey,
      ),
    );
    if (matches.isEmpty) {
      return null;
    }
    final ordered = matches.toList(growable: false)
      ..sort((left, right) => left.key.cacheKey.compareTo(right.key.cacheKey));
    return ordered.last;
  }

  @override
  Future<List<InterfaceHostViewStateCacheEntry>> entries({
    String? namespace,
  }) async {
    final normalizedNamespace = _trimmedOrNull(namespace);
    final out =
        _entries.values
            .where((entry) {
              return normalizedNamespace == null ||
                  entry.key.namespace == normalizedNamespace;
            })
            .toList(growable: false)
          ..sort(
            (left, right) => left.key.cacheKey.compareTo(right.key.cacheKey),
          );
    return List<InterfaceHostViewStateCacheEntry>.unmodifiable(out);
  }

  @override
  Future<InterfaceHostViewStateCursorState?> viewStateCursor({
    required String namespace,
  }) async {
    return _cursors[_requiredToken(namespace, 'namespace')];
  }

  @override
  Future<InterfaceHostViewStateCacheSyncResult> replaceNamespace({
    required String namespace,
    required Iterable<InterfaceHostViewStateCacheEntry> entries,
    InterfaceHostViewStateCursorState? viewStateCursor,
  }) async {
    final normalizedNamespace = _requiredToken(namespace, 'namespace');
    final incoming = entries.toList(growable: false);
    final cursor = _trimmedOrNull(viewStateCursor?.cursor);
    final digest = _trimmedOrNull(viewStateCursor?.digest);
    final previousCursor = _cursors[normalizedNamespace];
    if (_sameViewStateCursor(previousCursor, viewStateCursor)) {
      return InterfaceHostViewStateCacheSyncResult(
        namespace: normalizedNamespace,
        storedEntryCount: 0,
        removedEntryCount: 0,
        cursor: cursor,
        digest: digest,
        skipped: true,
      );
    }
    for (final entry in incoming) {
      if (entry.key.namespace != normalizedNamespace) {
        throw ArgumentError.value(
          entry.key.namespace,
          'entry.key.namespace',
          'must match replace namespace $normalizedNamespace',
        );
      }
    }
    final previousKeys = _entries.entries
        .where((entry) => entry.value.key.namespace == normalizedNamespace)
        .map((entry) => entry.key)
        .toList(growable: false);
    for (final key in previousKeys) {
      _entries.remove(key);
    }
    for (final entry in incoming) {
      _entries[entry.key.cacheKey] = entry;
    }
    if (viewStateCursor == null || cursor == null || digest == null) {
      _cursors.remove(normalizedNamespace);
    } else {
      _cursors[normalizedNamespace] = viewStateCursor;
    }
    return InterfaceHostViewStateCacheSyncResult(
      namespace: normalizedNamespace,
      storedEntryCount: incoming.length,
      removedEntryCount: previousKeys.length,
      cursor: cursor,
      digest: digest,
    );
  }

  @override
  Future<void> clear({String? namespace}) async {
    final normalizedNamespace = _trimmedOrNull(namespace);
    if (normalizedNamespace == null) {
      _entries.clear();
      _cursors.clear();
      return;
    }
    _cursors.remove(normalizedNamespace);
    final keys = _entries.entries
        .where((entry) => entry.value.key.namespace == normalizedNamespace)
        .map((entry) => entry.key)
        .toList(growable: false);
    for (final key in keys) {
      _entries.remove(key);
    }
  }
}

class InterfaceHostViewStateCache {
  const InterfaceHostViewStateCache(this.store);

  final InterfaceHostViewStateCacheStore store;

  Future<InterfaceHostViewStateCacheSyncResult> replaceFromHostState(
    InterfaceHostState hostState, {
    String? interfacePackageId,
    String? interfacePackageName,
  }) {
    final namespace = _requiredToken(
      hostState.namespace,
      'hostState.namespace',
    );
    return store.replaceNamespace(
      namespace: namespace,
      viewStateCursor: hostState.runtime?.viewStateCursor,
      entries: entriesFromHostState(
        hostState,
        interfacePackageId: interfacePackageId,
        interfacePackageName: interfacePackageName,
      ),
    );
  }

  Iterable<InterfaceHostViewStateCacheEntry> entriesFromHostState(
    InterfaceHostState hostState, {
    String? interfacePackageId,
    String? interfacePackageName,
  }) sync* {
    final namespace = _requiredToken(
      hostState.namespace,
      'hostState.namespace',
    );
    final runtime = hostState.runtime;
    final resolvedView = runtime?.resolvedView;
    final resolvedInterfacePackageId =
        _trimmedOrNull(interfacePackageId) ??
        resolvedView?.interfacePackageId?.uuid;
    final resolvedInterfacePackageName =
        _trimmedOrNull(interfacePackageName) ??
        resolvedView?.interfacePackageName;
    if (runtime == null) {
      return;
    }
    for (final materializedState in runtime.materializedPaneStates) {
      yield InterfaceHostViewStateCacheEntry.fromMaterializedState(
        namespace: namespace,
        environmentId: hostState.environmentId?.uuid,
        environmentConfigId: hostState.environmentConfigId?.uuid,
        interfacePackageId: resolvedInterfacePackageId,
        interfacePackageName: resolvedInterfacePackageName,
        materializedState: materializedState,
      );
    }
  }
}

String? _stringFromMap(Map<String, dynamic> payload, String key) {
  final value = payload[key];
  if (value is! String) {
    return null;
  }
  return _trimmedOrNull(value);
}

bool _sameViewStateCursor(
  InterfaceHostViewStateCursorState? left,
  InterfaceHostViewStateCursorState? right,
) {
  if (left == null || right == null) {
    return false;
  }
  final leftCursor = _trimmedOrNull(left.cursor);
  final rightCursor = _trimmedOrNull(right.cursor);
  if (leftCursor != null && leftCursor == rightCursor) {
    return true;
  }
  final leftDigest = _trimmedOrNull(left.digest);
  final rightDigest = _trimmedOrNull(right.digest);
  return leftDigest != null && leftDigest == rightDigest;
}

String _requiredToken(String value, String label) {
  final normalized = _trimmedOrNull(value);
  if (normalized == null) {
    throw ArgumentError.value(value, label, 'must be non-empty');
  }
  return normalized;
}

String? _trimmedOrNull(String? value) {
  final trimmed = value?.trim();
  if (trimmed == null || trimmed.isEmpty) {
    return null;
  }
  return trimmed;
}
