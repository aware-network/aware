import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/model/window_config.dart';
import '../../domain/provider/window_focus_provider.dart';
import '../../domain/provider/window_overlay_provider.dart';
import '../../domain/provider/window_shortcut_provider.dart';
import '../../domain/provider/window_header_provider.dart';
import '../../domain/presenter/window_pane_presenter.dart';
import 'window_section_focus_binding.dart';

class WindowPaneHost extends ConsumerWidget {
  const WindowPaneHost({
    super.key,
    required this.windowId,
    required this.sectionConfig,
    required this.headerArgs,
    required this.paneId,
    this.paneConfig = const <String, dynamic>{},
    this.fallbackBuilder,
  });

  final String windowId;
  final WindowSectionConfig sectionConfig;
  final HeaderControllerArgs headerArgs;
  final String paneId;
  final Map<String, dynamic> paneConfig;
  final WidgetBuilder? fallbackBuilder;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final presenter = ref
        .watch(windowPaneRegistryProvider)
        .presenterFor(paneId);

    if (presenter == null) {
      return fallbackBuilder?.call(context) ??
          Center(child: Text('Pane not registered: $paneId'));
    }

    final targetConfig = sectionConfig.copyWith(
      paneId: paneId,
      paneConfig: paneConfig.isNotEmpty ? paneConfig : sectionConfig.paneConfig,
    );

    final overlays = presenter.buildOverlays(ref, targetConfig, headerArgs);
    if (overlays.isNotEmpty) {
      Future.microtask(() {
        if (!context.mounted) return;
        final overlayRegistry = ref.read(windowOverlayRegistryProvider);
        for (final descriptor in overlays) {
          overlayRegistry.register(descriptor);
        }
      });
    }

    final shortcuts = presenter.buildShortcuts(ref, targetConfig, headerArgs);
    if (shortcuts.isNotEmpty) {
      Future.microtask(() {
        if (!context.mounted) return;
        ref
            .read(windowShortcutRegistryProvider(windowId).notifier)
            .registerPaneBindings(paneId, shortcuts);
      });
    }

    final child = presenter.build(context, ref, targetConfig, headerArgs);

    return WindowSectionFocusBinding(
      windowId: windowId,
      section: targetConfig,
      focusConfig: presenter.focusConfig,
      child: child,
    );
  }
}
