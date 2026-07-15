import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../service/overlay_shortcut_handle.dart';

import '../provider/window_overlay_session_provider.dart';

/// Holds overlay-specific session state, including the provider container
/// reused across the overlay subtree while it remains mounted.
class OverlayPaneSession {
  OverlayPaneSession({
    required this.windowId,
    required this.overlayId,
    required ProviderContainer providerContainer,
    required this.shortcutHandle,
  }) : _providerContainer = providerContainer,
       _disposeCallbacks = <VoidCallback>[];

  final String windowId;
  final String overlayId;
  final OverlayShortcutHandle shortcutHandle;

  final ProviderContainer _providerContainer;
  final List<VoidCallback> _disposeCallbacks;
  bool _disposed = false;

  ProviderContainer get providerContainer => _providerContainer;

  /// Registers a callback invoked when the session is disposed.
  void whenDisposed(VoidCallback callback) {
    if (_disposed) {
      callback();
      return;
    }
    _disposeCallbacks.add(callback);
  }

  void dispose() {
    if (_disposed) {
      return;
    }
    _disposed = true;
    for (final callback in _disposeCallbacks) {
      callback();
    }
    _disposeCallbacks.clear();
    _providerContainer.dispose();
    shortcutHandle.dispose();
  }
}
