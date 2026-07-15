import '../model/window_overlay_descriptor.dart';

/// Registry for window overlays keyed by window id.
class WindowOverlayRegistry {
  final Map<String, List<WindowOverlayDescriptor>> _overlaysByWindow = {};
  final Map<String, WindowOverlayDescriptor> _overlaysById = {};

  /// Register (or replace) an overlay descriptor.
  void register(WindowOverlayDescriptor descriptor) {
    _overlaysByWindow
        .putIfAbsent(descriptor.windowId, () => <WindowOverlayDescriptor>[])
        .removeWhere((existing) => existing.overlayId == descriptor.overlayId);
    _overlaysByWindow[descriptor.windowId]!.add(descriptor);
    _overlaysById[descriptor.overlayId] = descriptor;
  }

  /// Unregister an overlay by id.
  void unregister(String overlayId) {
    final descriptor = _overlaysById.remove(overlayId);
    if (descriptor == null) return;
    final list = _overlaysByWindow[descriptor.windowId];
    list?.removeWhere((item) => item.overlayId == overlayId);
  }

  /// List overlays registered for a given window.
  List<WindowOverlayDescriptor> overlaysForWindow(String windowId) {
    return List.unmodifiable(_overlaysByWindow[windowId] ?? const []);
  }

  /// Retrieve a descriptor by overlay id.
  WindowOverlayDescriptor? descriptorFor(String overlayId) {
    return _overlaysById[overlayId];
  }
}
