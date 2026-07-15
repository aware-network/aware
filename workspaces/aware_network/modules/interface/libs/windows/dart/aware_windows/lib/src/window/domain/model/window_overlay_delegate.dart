import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../provider/window_overlay_provider.dart';

typedef OverlayCommand =
    void Function(String overlayId, {Map<String, dynamic>? arguments});

typedef OverlayQuery<T> = T Function();

/// Delegate exposing overlay controls to panes that opt in.
class WindowOverlayDelegate {
  WindowOverlayDelegate._({
    required this.show,
    required this.hide,
    required this.toggle,
    required this.isVisible,
    required this.activeOverlayId,
  });

  factory WindowOverlayDelegate.fromRef(WidgetRef ref, String windowId) {
    final notifier = ref.read(
      windowOverlayControllerProvider(windowId).notifier,
    );

    WindowOverlayState readState() =>
        ref.read(windowOverlayControllerProvider(windowId));

    return WindowOverlayDelegate._(
      show: (overlayId, {Map<String, dynamic>? arguments}) {
        notifier.showOverlay(overlayId, arguments: arguments);
      },
      hide: () {
        notifier.hideOverlay();
      },
      toggle: (overlayId, {Map<String, dynamic>? arguments}) {
        notifier.toggleOverlay(overlayId, arguments: arguments);
      },
      isVisible: () => readState().isVisible,
      activeOverlayId: () => readState().activeOverlayId,
    );
  }

  final OverlayCommand show;
  final void Function() hide;
  final OverlayCommand toggle;
  final OverlayQuery<bool> isVisible;
  final OverlayQuery<String?> activeOverlayId;
}
