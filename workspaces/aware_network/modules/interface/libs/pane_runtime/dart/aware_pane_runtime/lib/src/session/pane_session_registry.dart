import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../pane_kind.dart';
import '../pane_selection_context.dart';

/// Persisted snapshot payload for a single pane instance session.
///
/// Modules should define their own snapshot type and persist/restore it via
/// [PaneSessionClient]. Snapshots are expected to be small and serializable,
/// but serialization is host-defined (in-memory v0).
abstract class PaneSessionSnapshot {
  const PaneSessionSnapshot();
}

/// Context describing the currently mounted pane instance inside a window session.
///
/// Contract:
/// - [paneInstanceId] MUST be stable for the lifetime of the pane instance
///   (browser-tab semantics). Hosts should derive it from pane kind + content key.
/// - [windowSessionId] is the "session namespace" for all pane instances in a window.
@immutable
class PaneSessionContext {
  const PaneSessionContext({
    required this.windowId,
    required this.windowSessionId,
    required this.sectionId,
    required this.paneInstanceId,
    required this.paneKind,
    this.threadId,
    this.processId,
    this.selectionContext,
    this.descriptorSignature,
    this.contentKey,
  });

  /// Window identity (host-defined).
  final String windowId;

  /// Stable window session identity. v0: equal to [windowId].
  final String windowSessionId;

  /// Host section identity within a window (tmux split / column / row).
  final String sectionId;

  /// Stable pane instance identity (tab).
  final String paneInstanceId;

  /// Pane kind (module-owned pane key).
  final PaneKey paneKind;

  /// Optional lane/thread attachment info (best-effort).
  final String? threadId;
  final String? processId;

  /// Optional selection context (manifest/descriptor payload).
  final PaneSelectionContext? selectionContext;

  /// Optional host signature for descriptor/params used to validate restore.
  final String? descriptorSignature;

  /// Optional host-provided content discriminator (lane key, view key, etc).
  final String? contentKey;
}

@immutable
class PaneSessionSnapshotHeader {
  const PaneSessionSnapshotHeader({
    required this.paneKind,
    this.threadId,
    this.descriptorSignature,
    this.contentKey,
  });

  final PaneKey paneKind;
  final String? threadId;
  final String? descriptorSignature;
  final String? contentKey;

  bool matches(PaneSessionContext context) {
    if (paneKind != context.paneKind) return false;

    // Optional fields are "fail-closed" only when both sides are non-null.
    final headerThreadId = threadId;
    final ctxThreadId = context.threadId;
    if (headerThreadId != null &&
        ctxThreadId != null &&
        headerThreadId != ctxThreadId) {
      return false;
    }

    final headerSig = descriptorSignature;
    final ctxSig = context.descriptorSignature;
    if (headerSig != null && ctxSig != null && headerSig != ctxSig) {
      return false;
    }

    final headerContentKey = contentKey;
    final ctxContentKey = context.contentKey;
    if (headerContentKey != null &&
        ctxContentKey != null &&
        headerContentKey != ctxContentKey) {
      return false;
    }

    return true;
  }
}

class PaneSessionSnapshotEnvelope<T extends PaneSessionSnapshot>
    extends PaneSessionSnapshot {
  const PaneSessionSnapshotEnvelope({
    required this.header,
    required this.snapshot,
  });

  final PaneSessionSnapshotHeader header;
  final T snapshot;
}

@immutable
class PaneSessionInstanceMeta {
  const PaneSessionInstanceMeta({this.isDirty = false, this.isPinned = false});

  final bool isDirty;
  final bool isPinned;

  PaneSessionInstanceMeta copyWith({bool? isDirty, bool? isPinned}) {
    return PaneSessionInstanceMeta(
      isDirty: isDirty ?? this.isDirty,
      isPinned: isPinned ?? this.isPinned,
    );
  }

  static const PaneSessionInstanceMeta empty = PaneSessionInstanceMeta();
}

/// In-memory v0 session snapshot store.
///
/// Keyed by:
/// - window session id
/// - pane instance id
class PaneSessionRegistry {
  final Map<String, Map<String, PaneSessionSnapshot>> _store = {};
  final Map<String, Map<String, PaneSessionInstanceMeta>> _meta = {};

  T? read<T extends PaneSessionSnapshot>(
    String windowSessionId,
    String paneInstanceId,
  ) {
    final snapshot = _store[windowSessionId]?[paneInstanceId];
    if (snapshot is T) return snapshot;
    return null;
  }

  PaneSessionInstanceMeta metaFor(
    String windowSessionId,
    String paneInstanceId,
  ) {
    return _meta[windowSessionId]?[paneInstanceId] ??
        PaneSessionInstanceMeta.empty;
  }

  void setDirty(String windowSessionId, String paneInstanceId, bool isDirty) {
    final previous = metaFor(windowSessionId, paneInstanceId);
    if (previous.isDirty == isDirty) return;
    _writeMeta(
      windowSessionId,
      paneInstanceId,
      previous.copyWith(isDirty: isDirty),
    );
  }

  void setPinned(String windowSessionId, String paneInstanceId, bool isPinned) {
    final previous = metaFor(windowSessionId, paneInstanceId);
    if (previous.isPinned == isPinned) return;
    _writeMeta(
      windowSessionId,
      paneInstanceId,
      previous.copyWith(isPinned: isPinned),
    );
  }

  void _writeMeta(
    String windowSessionId,
    String paneInstanceId,
    PaneSessionInstanceMeta meta,
  ) {
    if (!meta.isDirty && !meta.isPinned) {
      final sessionMeta = _meta[windowSessionId];
      if (sessionMeta == null) return;
      sessionMeta.remove(paneInstanceId);
      if (sessionMeta.isEmpty) {
        _meta.remove(windowSessionId);
      }
      return;
    }

    final sessionMeta = _meta.putIfAbsent(windowSessionId, () => {});
    sessionMeta[paneInstanceId] = meta;
  }

  void write(
    String windowSessionId,
    String paneInstanceId,
    PaneSessionSnapshot snapshot,
  ) {
    final sessionMap = _store.putIfAbsent(windowSessionId, () => {});
    sessionMap[paneInstanceId] = snapshot;
  }

  void clearWindowSession(String windowSessionId) {
    _store.remove(windowSessionId);
    _meta.remove(windowSessionId);
  }

  void clearPaneInstance(String windowSessionId, String paneInstanceId) {
    final sessionMap = _store[windowSessionId];
    if (sessionMap == null) return;
    sessionMap.remove(paneInstanceId);
    if (sessionMap.isEmpty) {
      _store.remove(windowSessionId);
    }

    final sessionMeta = _meta[windowSessionId];
    if (sessionMeta != null) {
      sessionMeta.remove(paneInstanceId);
      if (sessionMeta.isEmpty) {
        _meta.remove(windowSessionId);
      }
    }
  }
}

final paneSessionRegistryProvider = Provider<PaneSessionRegistry>(
  (_) => PaneSessionRegistry(),
);

class PaneSessionHandle {
  const PaneSessionHandle({required this.context, required this.registry});

  final PaneSessionContext context;
  final PaneSessionRegistry registry;

  String get windowSessionId => context.windowSessionId;
  String get paneInstanceId => context.paneInstanceId;

  T? restore<T extends PaneSessionSnapshot>() =>
      registry.read<T>(windowSessionId, paneInstanceId);

  void persist(PaneSessionSnapshot snapshot) {
    registry.write(windowSessionId, paneInstanceId, snapshot);
  }

  void persistWithMetadata(
    PaneSessionSnapshot snapshot, {
    PaneSessionSnapshotHeader? header,
  }) {
    final record = PaneSessionSnapshotEnvelope(
      header:
          header ??
          PaneSessionSnapshotHeader(
            paneKind: context.paneKind,
            threadId: context.threadId,
            descriptorSignature: context.descriptorSignature,
            contentKey: context.contentKey,
          ),
      snapshot: snapshot,
    );
    persist(record);
  }

  void clear() {
    registry.clearPaneInstance(windowSessionId, paneInstanceId);
  }

  PaneSessionInstanceMeta get meta =>
      registry.metaFor(windowSessionId, paneInstanceId);

  void setDirty(bool isDirty) =>
      registry.setDirty(windowSessionId, paneInstanceId, isDirty);

  void setPinned(bool isPinned) =>
      registry.setPinned(windowSessionId, paneInstanceId, isPinned);
}

/// Host-mounted session scope for a single pane instance.
class PaneSessionScope extends InheritedWidget {
  const PaneSessionScope({
    super.key,
    required this.handle,
    required this.context,
    required super.child,
  });

  final PaneSessionHandle handle;
  final PaneSessionContext context;

  static PaneSessionHandle? maybeOf(BuildContext context) {
    return context
        .dependOnInheritedWidgetOfExactType<PaneSessionScope>()
        ?.handle;
  }

  static PaneSessionContext? maybeContext(BuildContext context) {
    return context
        .dependOnInheritedWidgetOfExactType<PaneSessionScope>()
        ?.context;
  }

  @override
  bool updateShouldNotify(PaneSessionScope oldWidget) {
    // Avoid rebuilding dependents when the session identity is unchanged.
    if (!identical(oldWidget.handle.registry, handle.registry)) {
      return true;
    }

    final a = oldWidget.context;
    final b = context;
    if (a.windowId != b.windowId) return true;
    if (a.windowSessionId != b.windowSessionId) return true;
    if (a.sectionId != b.sectionId) return true;
    if (a.paneInstanceId != b.paneInstanceId) return true;
    if (a.paneKind != b.paneKind) return true;
    if (a.threadId != b.threadId) return true;
    if (a.processId != b.processId) return true;
    if (a.descriptorSignature != b.descriptorSignature) return true;
    if (a.contentKey != b.contentKey) return true;
    if (a.selectionContext != b.selectionContext) return true;

    return false;
  }
}
