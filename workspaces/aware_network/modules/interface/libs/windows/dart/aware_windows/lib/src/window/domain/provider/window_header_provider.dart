import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../model/window_header_data.dart';

class WindowHeaderState {
  const WindowHeaderState({required this.base, this.overlay});

  final WindowHeaderData base;
  final WindowHeaderData? overlay;

  WindowHeaderState copyWith({
    WindowHeaderData? base,
    WindowHeaderData? overlay,
  }) {
    return WindowHeaderState(base: base ?? this.base, overlay: overlay);
  }

  WindowHeaderData get active => overlay ?? base;
}

class WindowHeaderController extends StateNotifier<WindowHeaderState> {
  WindowHeaderController({required WindowHeaderData initialBase})
    : super(WindowHeaderState(base: initialBase));

  void setBase(WindowHeaderData data) {
    state = state.copyWith(base: data);
  }

  void setOverlay(WindowHeaderData data) {
    state = state.copyWith(overlay: data);
  }

  void clearOverlay() {
    if (state.overlay != null) {
      state = state.copyWith(overlay: null);
    }
  }
}

final windowHeaderControllerProvider =
    StateNotifierProvider.family<
      WindowHeaderController,
      WindowHeaderState,
      HeaderControllerArgs
    >((ref, args) {
      return WindowHeaderController(initialBase: args.initialData);
    });

/// Unique args for building a header controller.
class HeaderControllerArgs {
  const HeaderControllerArgs({
    required this.windowId,
    required this.initialData,
  });

  final String windowId;
  final WindowHeaderData initialData;

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is HeaderControllerArgs && other.windowId == windowId;
  }

  @override
  int get hashCode => windowId.hashCode;
}
