import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/model/window_config.dart';
import '../../domain/model/window_header_data.dart';
import '../../domain/provider/window_header_provider.dart';
import '../../domain/provider/window_overlay_provider.dart';
import '../../domain/presenter/window_pane_presenter.dart';
import '../../domain/provider/window_overlay_session_provider.dart';
import 'window_section_focus_binding.dart';

class WindowOverlayPaneHost extends ConsumerStatefulWidget {
  const WindowOverlayPaneHost({
    super.key,
    required this.windowId,
    required this.overlayId,
    required this.paneId,
    this.sectionId,
    this.paneConfig = const <String, dynamic>{},
    this.headerArgs,
    this.fallbackBuilder,
  });

  final String windowId;
  final String overlayId;
  final String paneId;
  final String? sectionId;
  final Map<String, dynamic> paneConfig;
  final HeaderControllerArgs? headerArgs;
  final WidgetBuilder? fallbackBuilder;

  @override
  ConsumerState<WindowOverlayPaneHost> createState() =>
      _WindowOverlayPaneHostState();
}

class _WindowOverlayPaneHostState extends ConsumerState<WindowOverlayPaneHost> {
  HeaderControllerArgs get _headerArgs =>
      widget.headerArgs ??
      HeaderControllerArgs(
        windowId: widget.windowId,
        initialData: const WindowHeaderData(title: ''),
      );

  WindowSectionConfig get _sectionConfig => WindowSectionConfig(
    id: widget.sectionId ?? '${widget.overlayId}::pane',
    paneId: widget.paneId,
    flex: 1.0,
    paneConfig: widget.paneConfig.isEmpty ? null : widget.paneConfig,
  );

  @override
  Widget build(BuildContext context) {
    final presenter = ref
        .watch(windowPaneRegistryProvider)
        .presenterFor(widget.paneId);

    if (presenter == null) {
      return widget.fallbackBuilder?.call(context) ??
          Center(child: Text('Pane not registered: ${widget.paneId}'));
    }

    final sectionConfig = _sectionConfig;
    final headerArgs = _headerArgs;

    final overlays = presenter.buildOverlays(ref, sectionConfig, headerArgs);
    if (overlays.isNotEmpty) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return;
        final overlayRegistry = ref.read(windowOverlayRegistryProvider);
        for (final descriptor in overlays) {
          overlayRegistry.register(descriptor);
        }
      });
    }

    final shortcuts = presenter.buildShortcuts(ref, sectionConfig, headerArgs);
    final shortcutHandle = ref.read(overlayShortcutHandleProvider);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      shortcutHandle.register(shortcuts);
    });

    final child = presenter.build(context, ref, sectionConfig, headerArgs);

    final focusConfig = presenter.focusConfig;

    return WindowSectionFocusBinding(
      windowId: widget.windowId,
      section: sectionConfig,
      focusConfig: focusConfig,
      child: child,
    );
  }
}
