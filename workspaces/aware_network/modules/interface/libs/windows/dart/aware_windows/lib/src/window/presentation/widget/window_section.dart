import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/model/window_config.dart';
import '../../domain/model/window_pane_header.dart';
import '../../domain/provider/window_header_provider.dart';
import '../window_palette.dart';
import 'window.dart';
import 'window_section_focus_binding.dart';
import '../../domain/presenter/window_pane_presenter.dart';

class WindowSection extends ConsumerWidget {
  const WindowSection({
    super.key,
    required this.config,
    required this.headerArgs,
    required this.palette,
    required this.sectionBuilder,
    required this.headerBuilder,
    this.onCollapse,
    this.showSectionHeader = true,
    this.panePolicyResolver,
  });

  final WindowSectionConfig config;
  final HeaderControllerArgs headerArgs;
  final WindowPalette palette;
  final WindowSectionBuilder sectionBuilder;
  final WindowPaneHeaderBuilder headerBuilder;
  final void Function(String sectionId)? onCollapse;
  final bool showSectionHeader;
  final WindowPanePolicyResolver? panePolicyResolver;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final presenter = ref
        .watch(windowPaneRegistryProvider)
        .presenterFor(config.paneId);
    final focusConfig = presenter?.focusConfig;
    return Container(
      decoration: BoxDecoration(
        color: palette.background,
        border: Border.all(
          color: palette.border.withValues(alpha: 0.2),
          width: 0.5,
        ),
      ),
      child: Column(
        children: [
          if (showSectionHeader) _buildHeader(),
          Expanded(
            child: WindowSectionFocusBinding(
              windowId: headerArgs.windowId,
              section: config,
              focusConfig: focusConfig,
              child: sectionBuilder(context, ref, config, headerArgs),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    final presentation = headerBuilder(config);
    final overridePolicy = panePolicyResolver?.call(config);
    final policy = overridePolicy ?? presentation.policy;

    if (policy == WindowHeaderPolicy.none) {
      return const SizedBox.shrink();
    }

    if (policy == WindowHeaderPolicy.inner) {
      return const SizedBox.shrink();
    }

    return Container(
      height: 32,
      padding: const EdgeInsets.symmetric(horizontal: 8),
      decoration: BoxDecoration(
        color: palette.card.withValues(alpha: 0.5),
        border: Border(
          bottom: BorderSide(color: palette.border.withValues(alpha: 0.3)),
        ),
      ),
      child: Row(
        children: [
          if (presentation.icon != null)
            Icon(presentation.icon, size: 14, color: palette.mutedText),
          if (presentation.icon != null) const SizedBox(width: 6),
          Text(
            presentation.title,
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.5,
              color: palette.mutedText,
            ),
          ),
          const Spacer(),
          if (onCollapse != null)
            InkWell(
              onTap: () => onCollapse!(config.id),
              child: Icon(Icons.minimize, size: 14, color: palette.mutedText),
            ),
        ],
      ),
    );
  }
}
