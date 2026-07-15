import 'dart:async';

import '../model/window_shortcut_binding.dart';
import '../service/window_shortcut_registry.dart';
import '../provider/window_shortcut_provider.dart';

class OverlayShortcutHandle {
  OverlayShortcutHandle({
    required this.windowId,
    required this.overlayId,
    required WindowShortcutRegistry registry,
  }) : _registry = registry;

  final String windowId;
  final String overlayId;
  final WindowShortcutRegistry _registry;

  bool _disposed = false;
  bool _hasBindings = false;

  void register(Iterable<ShortcutBinding> bindings) {
    if (_disposed) {
      return;
    }
    if (bindings.isEmpty) {
      Future.microtask(() {
        if (_disposed) return;
        _registry.unregisterOverlayBindings(overlayId);
      });
      _hasBindings = false;
      return;
    }
    Future.microtask(() {
      if (_disposed) return;
      _registry.registerOverlayBindings(overlayId, bindings);
    });
    _hasBindings = true;
  }

  void unregister() {
    if (_disposed || !_hasBindings) {
      return;
    }
    Future.microtask(() {
      _registry.unregisterOverlayBindings(overlayId);
    });
    _hasBindings = false;
  }

  void dispose() {
    if (_disposed) {
      return;
    }
    unregister();
    _disposed = true;
  }
}
