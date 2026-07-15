import 'package:flutter/widgets.dart';

import 'pane_controller_registry.dart';
import 'pane_session_registry.dart';

/// Provides restore/persist helpers for panes hosted inside [PaneSessionScope].
mixin PaneSessionClient<
  TWidget extends StatefulWidget,
  TSnapshot extends PaneSessionSnapshot
>
    on State<TWidget> {
  PaneSessionHandle? _paneSessionHandle;
  PaneSessionContext? _paneSessionContext;
  bool _paneSessionRestored = false;

  @protected
  PaneSessionHandle? get paneSessionHandle => _paneSessionHandle;

  @protected
  PaneSessionContext? get paneSessionContext => _paneSessionContext;

  @protected
  String? get paneThreadId => _paneSessionContext?.threadId;

  @protected
  String? get paneWindowId => _paneSessionContext?.windowId;

  @protected
  bool get hasPaneSession => _paneSessionHandle != null;

  /// Mark this pane instance as "dirty" (unsaved state).
  ///
  /// Hosts may use this flag to avoid evicting controller state under memory
  /// pressure.
  @protected
  void setPaneSessionDirty(bool isDirty) {
    _paneSessionHandle?.setDirty(isDirty);
  }

  /// Pin this pane instance to avoid host eviction.
  @protected
  void setPaneSessionPinned(bool isPinned) {
    _paneSessionHandle?.setPinned(isPinned);
  }

  /// Call from [didChangeDependencies] to hydrate session state.
  @protected
  void handlePaneSessionLifecycle() {
    final handle = PaneSessionScope.maybeOf(context);
    final contextMeta = PaneSessionScope.maybeContext(context);
    if (_paneSessionHandle != handle) {
      _paneSessionHandle = handle;
      _paneSessionRestored = false;
    }
    _paneSessionContext = contextMeta;
    if (!_paneSessionRestored && handle != null) {
      final restored = handle.restore<PaneSessionSnapshot>();
      if (restored != null) {
        final snapshot = _maybeExtractSnapshot(restored);
        if (snapshot != null) {
          onRestorePaneSession(snapshot);
        }
      }
      _paneSessionRestored = true;
    }
  }

  TSnapshot? _maybeExtractSnapshot(PaneSessionSnapshot restored) {
    final contextMeta = _paneSessionContext;
    if (restored is PaneSessionSnapshotEnvelope) {
      final payload = restored.snapshot;
      if (payload is! TSnapshot) {
        return null;
      }
      if (contextMeta != null && !restored.header.matches(contextMeta)) {
        return null;
      }
      return payload;
    }
    if (restored is TSnapshot) {
      // Legacy snapshot without metadata.
      return restored;
    }
    return null;
  }

  /// Persist a snapshot when state changes or during [dispose].
  @protected
  void persistPaneSessionSnapshot(TSnapshot snapshot) {
    final handle = _paneSessionHandle;
    if (handle == null) return;

    final ctx = _paneSessionContext;
    handle.persistWithMetadata(
      snapshot,
      header: ctx == null
          ? null
          : PaneSessionSnapshotHeader(
              paneKind: ctx.paneKind,
              threadId: ctx.threadId,
              descriptorSignature: ctx.descriptorSignature,
              contentKey: ctx.contentKey,
            ),
    );
  }

  /// Clears the snapshot for the current pane instance.
  @protected
  void clearPaneSessionSnapshot() {
    _paneSessionHandle?.clear();
  }

  /// Override to hydrate state from the restored snapshot.
  void onRestorePaneSession(TSnapshot snapshot);
}

class _OwnedPaneController {
  _OwnedPaneController(this.entry, this.controller);

  final PaneControllerEntry<dynamic> entry;
  final Object controller;

  void dispose() {
    entry.dispose(controller);
  }
}

/// Handles controller acquisition via [PaneControllerScope] with local fallback.
mixin PaneControllerClient<
  TWidget extends StatefulWidget,
  TSnapshot extends PaneSessionSnapshot
>
    on PaneSessionClient<TWidget, TSnapshot> {
  final Map<String, _OwnedPaneController> _ownedPaneControllers = {};

  static const String _windowScopedInstanceId = '__window__';

  /// Obtain a controller from the registry or create a local instance when no
  /// session exists.
  @protected
  T usePaneController<T>(
    String controllerKey,
    PaneControllerEntry<T> entry, {
    bool scopeToPaneInstance = true,
  }) {
    final registry = PaneControllerScope.maybeOf(context);
    final session = paneSessionHandle;
    final ctx = paneSessionContext;

    if (registry != null && session != null && ctx != null) {
      final paneInstanceId = scopeToPaneInstance
          ? ctx.paneInstanceId
          : _windowScopedInstanceId;
      return registry.obtain(
        ctx.windowSessionId,
        paneInstanceId,
        controllerKey,
        entry,
      );
    }

    final owned = _ownedPaneControllers.putIfAbsent(controllerKey, () {
      final controller = entry.create();
      return _OwnedPaneController(
        entry as PaneControllerEntry<dynamic>,
        controller as Object,
      );
    });
    return owned.controller as T;
  }

  /// Dispose controllers that were created locally (outside a registry scope).
  @protected
  void disposeOwnedPaneControllers() {
    for (final owned in _ownedPaneControllers.values) {
      owned.dispose();
    }
    _ownedPaneControllers.clear();
  }
}
