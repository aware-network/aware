import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../service/window_shortcut_registry.dart';

final windowShortcutRegistryProvider =
    StateNotifierProvider.family<
      WindowShortcutRegistry,
      WindowShortcutState,
      String
    >((ref, windowId) {
      return WindowShortcutRegistry(windowId);
    });
