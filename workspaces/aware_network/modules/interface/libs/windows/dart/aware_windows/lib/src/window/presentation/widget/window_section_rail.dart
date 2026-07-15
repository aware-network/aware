import 'package:flutter/material.dart';

import '../../domain/model/window_slot.dart';

/// Callback to wrap the rail in a host-provided surface (e.g. glass material).
typedef SectionRailSurfaceBuilder = Widget Function(Widget child);

/// Vertical section rail for desktop — renders [WindowSlot] items as a thin
/// navigation column on the far left edge of the window host.
///
/// This widget lives in `aware_windows` and has NO dependency on
/// `aware_pane_runtime` or pane implementations. Glass treatment and
/// branding are injected via [surfaceBuilder] by the host (Studio).
class WindowSectionRail extends StatelessWidget {
  const WindowSectionRail({
    super.key,
    required this.slots,
    required this.onSlotTapped,
    this.surfaceBuilder,
    this.width = 48,
  });

  /// Available window slots to render as rail items.
  final List<WindowSlot> slots;

  /// Called when a slot item is tapped.
  final ValueChanged<WindowSlot> onSlotTapped;

  /// Optional surface wrapper (e.g. glass material).
  final SectionRailSurfaceBuilder? surfaceBuilder;

  /// Rail width in logical pixels.
  final double width;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    Widget rail = SizedBox(
      width: width,
      child: Column(
        children: [
          const SizedBox(height: 12),
          for (final slot in slots) ...[
            _SlotItem(
              slot: slot,
              onTap: () => onSlotTapped(slot),
              theme: theme,
            ),
          ],
          const Spacer(),
        ],
      ),
    );

    if (surfaceBuilder != null) {
      rail = surfaceBuilder!(rail);
    }

    return rail;
  }
}

class _SlotItem extends StatelessWidget {
  const _SlotItem({
    required this.slot,
    required this.onTap,
    required this.theme,
  });

  final WindowSlot slot;
  final VoidCallback onTap;
  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    final isActive = slot.isActive;
    final accent = slot.accentColor ?? theme.colorScheme.primary;
    final iconColor = isActive
        ? accent
        : theme.colorScheme.onSurface.withValues(alpha: 0.5);

    return Tooltip(
      message: slot.label,
      preferBelow: false,
      waitDuration: const Duration(milliseconds: 400),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(10),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          width: 40,
          height: 40,
          margin: const EdgeInsets.symmetric(vertical: 4),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(10),
            color: isActive
                ? accent.withValues(alpha: 0.12)
                : Colors.transparent,
          ),
          child: Center(child: Icon(slot.icon, size: 20, color: iconColor)),
        ),
      ),
    );
  }
}
