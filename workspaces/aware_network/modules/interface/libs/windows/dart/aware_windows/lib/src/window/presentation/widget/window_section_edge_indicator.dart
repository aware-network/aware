import 'package:flutter/material.dart';

import '../../domain/model/window_slot.dart';

/// Edge indicator for mobile — a thin vertical strip on the left or right
/// edge showing that an adjacent section is swipeable.
///
/// Placed as a [Positioned] overlay inside the mobile scaffold [Stack].
/// Uses [AnimatedOpacity] for smooth show/hide transitions.
class WindowSectionEdgeIndicator extends StatelessWidget {
  const WindowSectionEdgeIndicator({
    super.key,
    required this.slot,
    required this.onTap,
    this.edge = _Edge.right,
    this.visible = true,
  });

  /// The adjacent section this indicator points to.
  final WindowSlot slot;

  /// Called when the indicator is tapped.
  final VoidCallback onTap;

  /// Which edge to render on.
  final _Edge edge;

  /// Whether the indicator is visible.
  final bool visible;

  /// Right-edge indicator (default — shows "swipe right for Agent").
  const WindowSectionEdgeIndicator.right({
    super.key,
    required this.slot,
    required this.onTap,
    this.visible = true,
  }) : edge = _Edge.right;

  /// Left-edge indicator (shows "swipe left for Workspace").
  const WindowSectionEdgeIndicator.left({
    super.key,
    required this.slot,
    required this.onTap,
    this.visible = true,
  }) : edge = _Edge.left;

  @override
  Widget build(BuildContext context) {
    final accent = slot.accentColor ?? Theme.of(context).colorScheme.primary;
    final isRight = edge == _Edge.right;

    return Positioned(
      top: 0,
      bottom: 0,
      right: isRight ? 0 : null,
      left: isRight ? null : 0,
      child: AnimatedOpacity(
        duration: const Duration(milliseconds: 250),
        opacity: visible ? 1.0 : 0.0,
        child: IgnorePointer(
          ignoring: !visible,
          child: GestureDetector(
            onTap: onTap,
            behavior: HitTestBehavior.translucent,
            child: Container(
              width: 24,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: isRight ? Alignment.centerRight : Alignment.centerLeft,
                  end: isRight ? Alignment.centerLeft : Alignment.centerRight,
                  colors: [
                    accent.withValues(alpha: 0.15),
                    accent.withValues(alpha: 0.0),
                  ],
                ),
              ),
              child: Icon(
                isRight ? Icons.chevron_right : Icons.chevron_left,
                size: 16,
                color: accent.withValues(alpha: 0.6),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

enum _Edge { left, right }
