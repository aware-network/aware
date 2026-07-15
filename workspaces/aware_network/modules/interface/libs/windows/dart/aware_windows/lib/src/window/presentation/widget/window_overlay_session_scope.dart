import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/model/overlay_pane_session.dart';
import '../../domain/provider/window_overlay_session_provider.dart';
import '../../domain/service/overlay_shortcut_handle.dart';
import '../../domain/provider/window_shortcut_provider.dart';

class OverlayPaneSessionScope extends StatefulWidget {
  const OverlayPaneSessionScope({
    super.key,
    required this.windowId,
    required this.overlayId,
    required this.child,
  });

  final String windowId;
  final String overlayId;
  final Widget child;

  @override
  State<OverlayPaneSessionScope> createState() =>
      _OverlayPaneSessionScopeState();
}

class _OverlayPaneSessionScopeState extends State<OverlayPaneSessionScope> {
  ProviderContainer? _container;
  OverlayPaneSession? _session;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_container != null) {
      return;
    }
    final parentContainer = ProviderScope.containerOf(context);
    final container = ProviderContainer(parent: parentContainer);
    _container = container;
    _session = OverlayPaneSession(
      windowId: widget.windowId,
      overlayId: widget.overlayId,
      providerContainer: container,
      shortcutHandle: OverlayShortcutHandle(
        windowId: widget.windowId,
        overlayId: widget.overlayId,
        registry: container.read(
          windowShortcutRegistryProvider(widget.windowId).notifier,
        ),
      ),
    );
  }

  @override
  void dispose() {
    _session?.dispose();
    _container?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final container = _container;
    final session = _session;
    assert(container != null && session != null);
    final sessionValue = session!;
    return ProviderScope(
      parent: container,
      overrides: [
        overlayPaneSessionProvider.overrideWithValue(sessionValue),
        overlayShortcutHandleProvider.overrideWithValue(
          sessionValue.shortcutHandle,
        ),
      ],
      child: widget.child,
    );
  }
}
