import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

enum FocusTransitionPhase { suspended, resumed }

@immutable
class WindowFocusTransition {
  const WindowFocusTransition({
    required this.windowId,
    required this.overlayId,
    required this.phase,
    required this.occurredAt,
  });

  final String windowId;
  final String overlayId;
  final FocusTransitionPhase phase;
  final DateTime occurredAt;
}

/// Immutable snapshot of the current focus state for a window.
@immutable
class WindowFocusState {
  const WindowFocusState({
    required this.windowId,
    this.activeSectionId,
    this.activePaneId,
    this.overlayCapture,
    this.isSuspended = false,
    this.lastChangedAt,
  });

  final String windowId;
  final String? activeSectionId;
  final String? activePaneId;
  final String? overlayCapture;
  final bool isSuspended;
  final DateTime? lastChangedAt;

  bool get hasFocus => activeSectionId != null && !isSuspended;

  static const Object _unset = Object();

  WindowFocusState copyWith({
    Object? activeSectionId = _unset,
    Object? activePaneId = _unset,
    Object? overlayCapture = _unset,
    bool? isSuspended,
    DateTime? lastChangedAt,
  }) {
    return WindowFocusState(
      windowId: windowId,
      activeSectionId: identical(activeSectionId, _unset)
          ? this.activeSectionId
          : activeSectionId as String?,
      activePaneId: identical(activePaneId, _unset)
          ? this.activePaneId
          : activePaneId as String?,
      overlayCapture: identical(overlayCapture, _unset)
          ? this.overlayCapture
          : overlayCapture as String?,
      isSuspended: isSuspended ?? this.isSuspended,
      lastChangedAt: lastChangedAt ?? this.lastChangedAt,
    );
  }
}

/// Controller that tracks which section/pane currently owns focus.
class WindowFocusController extends StateNotifier<WindowFocusState> {
  WindowFocusController({required this.ref, required String windowId})
    : super(WindowFocusState(windowId: windowId));

  final Ref ref;

  final List<String> _diagnostics = [];
  WindowFocusTransition? _lastTransition;

  DateTime _timestamp() => DateTime.now().toUtc();

  void _emitTransition(String overlayId, FocusTransitionPhase phase) {
    final transition = WindowFocusTransition(
      windowId: state.windowId,
      overlayId: overlayId,
      phase: phase,
      occurredAt: _timestamp(),
    );
    final previous = _lastTransition;
    if (previous != null &&
        previous.overlayId == transition.overlayId &&
        previous.phase == transition.phase) {
      return;
    }
    _lastTransition = transition;
    ref
        .read(_windowFocusTransitionLogProvider(state.windowId).notifier)
        .add(transition);
  }

  void setSectionFocus({required String sectionId, required String paneId}) {
    final current = state;
    if (current.activeSectionId != null &&
        current.activeSectionId != sectionId &&
        !current.isSuspended) {
      _recordDiagnostic(
        'Focus changed from "${current.activeSectionId}" to "$sectionId" without an explicit blur.',
      );
    }

    final next = current.copyWith(
      activeSectionId: sectionId,
      activePaneId: paneId,
      isSuspended: current.overlayCapture != null,
      lastChangedAt: _timestamp(),
    );

    if (next != current) {
      state = next;
    }
  }

  void clearSectionFocus(String sectionId) {
    final current = state;
    if (current.activeSectionId != sectionId) {
      return;
    }

    if (current.isSuspended && current.overlayCapture != null) {
      // Preserve the last active pane while an overlay is capturing focus.
      return;
    }

    state = current.copyWith(
      activeSectionId: null,
      activePaneId: null,
      isSuspended: false,
      lastChangedAt: _timestamp(),
    );
  }

  void suspendForOverlay(String overlayId) {
    final current = state;
    if (current.overlayCapture == overlayId && current.isSuspended) {
      return;
    }

    state = current.copyWith(
      overlayCapture: overlayId,
      isSuspended: true,
      lastChangedAt: _timestamp(),
    );
    _emitTransition(overlayId, FocusTransitionPhase.suspended);
  }

  void resumeFromOverlay([String? overlayId]) {
    final current = state;

    if (current.overlayCapture == null) {
      if (current.isSuspended) {
        state = current.copyWith(
          isSuspended: false,
          lastChangedAt: _timestamp(),
        );
      }
      return;
    }

    if (overlayId != null && current.overlayCapture != overlayId) {
      return;
    }

    final targetOverlay = overlayId ?? current.overlayCapture!;
    state = current.copyWith(
      overlayCapture: null,
      isSuspended: false,
      lastChangedAt: _timestamp(),
    );
    _emitTransition(targetOverlay, FocusTransitionPhase.resumed);
  }

  List<String> takeDiagnostics() {
    final snapshot = List<String>.from(_diagnostics);
    _diagnostics.clear();
    return snapshot;
  }

  void _recordDiagnostic(String message) {
    _diagnostics.add(message);
    assert(() {
      debugPrint('aware_windows focus: $message');
      return true;
    }());
  }
}

/// Provider for focus controllers scoped by window id.
final windowFocusControllerProvider =
    StateNotifierProvider.family<
      WindowFocusController,
      WindowFocusState,
      String
    >((ref, windowId) {
      return WindowFocusController(ref: ref, windowId: windowId);
    });

final _windowFocusTransitionLogProvider =
    StateNotifierProvider.family<
      _WindowFocusTransitionLog,
      List<WindowFocusTransition>,
      String
    >((ref, windowId) {
      return _WindowFocusTransitionLog();
    });

final windowFocusTransitionsProvider =
    Provider.family<List<WindowFocusTransition>, String>((ref, windowId) {
      return ref.watch(_windowFocusTransitionLogProvider(windowId));
    });

class _WindowFocusTransitionLog
    extends StateNotifier<List<WindowFocusTransition>> {
  _WindowFocusTransitionLog() : super(const []);

  void add(WindowFocusTransition transition) {
    state = <WindowFocusTransition>[...state, transition];
  }

  void clear() {
    state = const [];
  }
}
