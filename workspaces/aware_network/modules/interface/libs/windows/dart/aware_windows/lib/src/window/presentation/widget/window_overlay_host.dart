import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/model/window_overlay_descriptor.dart';
import '../../domain/model/window_header_data.dart';
import '../../domain/provider/window_overlay_provider.dart';
import '../../domain/provider/window_header_provider.dart';
import '../../domain/provider/window_focus_provider.dart';
import 'window_overlay_session_scope.dart';

/// Hosts overlays above a window's primary content.
typedef WindowOverlayScrimBuilder =
    Widget Function(
      BuildContext context,
      WidgetRef ref,
      WindowOverlayDescriptor descriptor,
      VoidCallback dismiss,
    );

class WindowOverlayHost extends ConsumerStatefulWidget {
  const WindowOverlayHost({
    super.key,
    required this.headerArgs,
    this.scrimBuilder,
  });

  final HeaderControllerArgs headerArgs;
  final WindowOverlayScrimBuilder? scrimBuilder;

  @override
  ConsumerState<WindowOverlayHost> createState() => _WindowOverlayHostState();
}

class _WindowOverlayHostState extends ConsumerState<WindowOverlayHost> {
  String? _capturingOverlayId;

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(
      windowOverlayControllerProvider(widget.headerArgs.windowId),
    );
    final focusController = ref.read(
      windowFocusControllerProvider(widget.headerArgs.windowId).notifier,
    );

    if (!state.isVisible || state.activeOverlayId == null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        ref
            .read(windowHeaderControllerProvider(widget.headerArgs).notifier)
            .clearOverlay();
        _releaseFocusIfNeeded(focusController);
      });
      return const SizedBox.shrink();
    }

    final registry = ref.watch(windowOverlayRegistryProvider);
    final descriptor = registry.descriptorFor(state.activeOverlayId!);
    if (descriptor == null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        ref
            .read(windowHeaderControllerProvider(widget.headerArgs).notifier)
            .clearOverlay();
        _releaseFocusIfNeeded(focusController);
      });
      return const SizedBox.shrink();
    }

    final controller = ref.read(
      windowOverlayControllerProvider(widget.headerArgs.windowId).notifier,
    );

    final headerController = ref.read(
      windowHeaderControllerProvider(widget.headerArgs).notifier,
    );

    final headerData = descriptor.headerBuilder?.call(ref);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (headerData != null) {
        headerController.setOverlay(headerData);
      } else {
        headerController.clearOverlay();
      }
    });

    if (descriptor.capturesFocus) {
      if (_capturingOverlayId != descriptor.overlayId) {
        final overlayId = descriptor.overlayId;
        WidgetsBinding.instance.addPostFrameCallback((_) {
          focusController.suspendForOverlay(overlayId);
        });
        _capturingOverlayId = descriptor.overlayId;
      }
    } else {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _releaseFocusIfNeeded(focusController);
      });
    }

    final overlayContent = descriptor.builder(context, ref, state.arguments);
    final overlayWithSession = OverlayPaneSessionScope(
      windowId: descriptor.windowId,
      overlayId: descriptor.overlayId,
      child: overlayContent,
    );

    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 180),
      child: Stack(
        key: ValueKey(descriptor.overlayId),
        children: [
          if (descriptor.scrimStyle != OverlayScrimStyle.none)
            Positioned.fill(
              child: widget.scrimBuilder != null
                  ? widget.scrimBuilder!(
                      context,
                      ref,
                      descriptor,
                      controller.hideOverlay,
                    )
                  : _buildScrim(context, ref, descriptor, controller),
            ),
          Positioned.fill(child: overlayWithSession),
        ],
      ),
    );
  }

  Widget _buildScrim(
    BuildContext context,
    WidgetRef ref,
    WindowOverlayDescriptor descriptor,
    WindowOverlayController controller,
  ) {
    final color = switch (descriptor.scrimStyle) {
      OverlayScrimStyle.opaque => Colors.black.withValues(alpha: 0.6),
      OverlayScrimStyle.translucent => Colors.black.withValues(alpha: 0.35),
      OverlayScrimStyle.none => Colors.transparent,
    };

    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: () {
        // Allow manual overlays to close via scrim tap.
        if (descriptor.dismissPolicy == OverlayDismissPolicy.manual) {
          controller.hideOverlay();
        }
      },
      child: Container(color: color),
    );
  }

  void _releaseFocusIfNeeded(WindowFocusController controller) {
    if (_capturingOverlayId != null) {
      controller.resumeFromOverlay(_capturingOverlayId);
      _capturingOverlayId = null;
    } else {
      controller.resumeFromOverlay();
    }
  }
}
