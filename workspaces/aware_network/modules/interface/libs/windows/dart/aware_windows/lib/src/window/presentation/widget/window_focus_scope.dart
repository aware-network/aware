import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/provider/window_focus_provider.dart';

typedef WindowFocusStateListener =
    void Function(WindowFocusState? previous, WindowFocusState next);

class WindowFocusScope extends ConsumerStatefulWidget {
  const WindowFocusScope({
    super.key,
    required this.windowId,
    required this.child,
    this.onStateChanged,
  });

  final String windowId;
  final Widget child;
  final WindowFocusStateListener? onStateChanged;

  @override
  ConsumerState<WindowFocusScope> createState() => _WindowFocusScopeState();

  static String? maybeWindowId(BuildContext context) {
    return context
        .dependOnInheritedWidgetOfExactType<_WindowFocusInherited>()
        ?.windowId;
  }
}

class _WindowFocusScopeState extends ConsumerState<WindowFocusScope> {
  ProviderSubscription<WindowFocusState>? _subscription;

  @override
  void initState() {
    super.initState();
    _subscription = ref.listenManual<WindowFocusState>(
      windowFocusControllerProvider(widget.windowId),
      (previous, next) {
        widget.onStateChanged?.call(previous, next);
      },
    );
    _subscription?.read();
  }

  @override
  void dispose() {
    _subscription?.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    ref.watch(windowFocusControllerProvider(widget.windowId));
    return _WindowFocusInherited(
      windowId: widget.windowId,
      child: widget.child,
    );
  }
}

class _WindowFocusInherited extends InheritedWidget {
  const _WindowFocusInherited({required this.windowId, required super.child});

  final String windowId;

  @override
  bool updateShouldNotify(covariant _WindowFocusInherited oldWidget) {
    return oldWidget.windowId != windowId;
  }
}
