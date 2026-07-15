import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../model/overlay_pane_session.dart';
import '../service/overlay_shortcut_handle.dart';

final overlayPaneSessionProvider = Provider<OverlayPaneSession?>((ref) {
  return null;
});

final overlayShortcutHandleProvider = Provider<OverlayShortcutHandle>((ref) {
  final session = ref.watch(overlayPaneSessionProvider);
  if (session == null) {
    throw StateError(
      'overlayShortcutHandleProvider accessed outside an overlay session scope.',
    );
  }
  return session.shortcutHandle;
}, dependencies: [overlayPaneSessionProvider]);
