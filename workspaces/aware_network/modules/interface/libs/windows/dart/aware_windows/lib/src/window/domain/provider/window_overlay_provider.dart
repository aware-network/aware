import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../model/window_overlay_descriptor.dart';
import '../service/window_overlay_registry.dart';

/// Provider exposing the singleton overlay registry.
final windowOverlayRegistryProvider = Provider<WindowOverlayRegistry>((ref) {
  return WindowOverlayRegistry();
});

/// Immutable overlay state for a window.
class WindowOverlayState {
  const WindowOverlayState({
    this.activeOverlayId,
    this.arguments,
    this.isVisible = false,
  });

  final String? activeOverlayId;
  final Map<String, dynamic>? arguments;
  final bool isVisible;

  WindowOverlayState copyWith({
    String? activeOverlayId,
    Map<String, dynamic>? arguments,
    bool? isVisible,
  }) {
    return WindowOverlayState(
      activeOverlayId: activeOverlayId ?? this.activeOverlayId,
      arguments: arguments ?? this.arguments,
      isVisible: isVisible ?? this.isVisible,
    );
  }

  static const hidden = WindowOverlayState();
}

/// Controller responsible for showing or hiding overlays for a specific window.
class WindowOverlayController extends StateNotifier<WindowOverlayState> {
  WindowOverlayController(this.ref, this.windowId)
    : super(WindowOverlayState.hidden);

  final Ref ref;
  final String windowId;

  WindowOverlayRegistry get _registry =>
      ref.read(windowOverlayRegistryProvider);

  void showOverlay(String overlayId, {Map<String, dynamic>? arguments}) {
    final descriptor = _registry.descriptorFor(overlayId);
    if (descriptor == null || descriptor.windowId != windowId) {
      // Overlay not registered for this window; ignore.
      return;
    }
    state = WindowOverlayState(
      activeOverlayId: overlayId,
      arguments: arguments,
      isVisible: true,
    );
  }

  void hideOverlay() {
    state = WindowOverlayState.hidden;
  }

  void toggleOverlay(String overlayId, {Map<String, dynamic>? arguments}) {
    if (state.isVisible && state.activeOverlayId == overlayId) {
      hideOverlay();
    } else {
      showOverlay(overlayId, arguments: arguments);
    }
  }

  void dismissForPolicy() {
    if (!state.isVisible) return;
    final descriptor = state.activeOverlayId != null
        ? _registry.descriptorFor(state.activeOverlayId!)
        : null;
    if (descriptor?.dismissPolicy == OverlayDismissPolicy.autoOnSectionChange) {
      hideOverlay();
    }
  }
}

/// Family provider for overlay controllers per window id.
final windowOverlayControllerProvider =
    StateNotifierProvider.family<
      WindowOverlayController,
      WindowOverlayState,
      String
    >((ref, windowId) {
      return WindowOverlayController(ref, windowId);
    });
