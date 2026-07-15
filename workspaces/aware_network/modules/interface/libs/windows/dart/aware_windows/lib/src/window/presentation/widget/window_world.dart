import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/provider/window_world_provider.dart';

typedef WindowWorldBackgroundBuilder =
    Widget Function(
      BuildContext context,
      WidgetRef ref,
      String windowId,
      WindowWorldHint hint,
    );

/// Persistent “world” host for a window.
///
/// Contract: the background stays mounted; panes recompose on top.
class WindowWorld extends ConsumerWidget {
  const WindowWorld({
    super.key,
    required this.windowId,
    required this.child,
    required this.backgroundBuilder,
    this.scrimBuilder,
  });

  final String windowId;
  final Widget child;
  final WindowWorldBackgroundBuilder backgroundBuilder;

  /// Optional foreground scrim layer. Defaults to `hint.scrimStrength` if null.
  final Widget Function(BuildContext context, WindowWorldHint hint)?
  scrimBuilder;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final hint = ref.watch(windowWorldControllerProvider(windowId));
    final background = backgroundBuilder(context, ref, windowId, hint);

    final scrim =
        scrimBuilder?.call(context, hint) ??
        (hint.scrimStrength <= 0
            ? null
            : Container(
                color: Colors.black.withValues(alpha: hint.scrimStrength),
              ));

    return Stack(
      children: [
        Positioned.fill(
          child: RepaintBoundary(
            child: Opacity(opacity: hint.backgroundOpacity, child: background),
          ),
        ),
        if (scrim != null) Positioned.fill(child: scrim),
        Positioned.fill(child: child),
      ],
    );
  }
}
