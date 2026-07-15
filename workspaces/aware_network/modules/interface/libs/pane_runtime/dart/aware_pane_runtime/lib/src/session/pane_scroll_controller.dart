import 'package:flutter/widgets.dart';

import 'pane_controller_registry.dart';

/// A [ScrollController] that retains its last known offset even after being
/// detached from all scroll positions.
///
/// This is useful for pane instances that are frequently mounted/unmounted
/// (switching between panes/tabs) but should preserve scroll position.
class PaneRetainedScrollController extends ScrollController {
  PaneRetainedScrollController({
    double initialOffset = 0.0,
    super.keepScrollOffset = true,
    super.debugLabel,
  }) : _retainedOffset = initialOffset,
       super(initialScrollOffset: initialOffset);

  double _retainedOffset;

  double get retainedOffset => _retainedOffset;

  @override
  void detach(ScrollPosition position) {
    // Best-effort: capture the last pixels before the position is disposed.
    try {
      _retainedOffset = position.pixels;
    } catch (_) {
      // Ignore; position may not be attached or fully initialized.
    }
    super.detach(position);
  }

  @override
  ScrollPosition createScrollPosition(
    ScrollPhysics physics,
    ScrollContext context,
    ScrollPosition? oldPosition,
  ) {
    final initialPixels = (() {
      try {
        return oldPosition?.pixels ?? _retainedOffset;
      } catch (_) {
        return _retainedOffset;
      }
    })();

    return ScrollPositionWithSingleContext(
      physics: physics,
      context: context,
      oldPosition: oldPosition,
      initialPixels: initialPixels,
      keepScrollOffset: keepScrollOffset,
      debugLabel: debugLabel,
    );
  }
}

class PaneRetainedScrollControllerEntry
    extends PaneControllerEntry<PaneRetainedScrollController> {
  const PaneRetainedScrollControllerEntry({this.debugLabel});

  final String? debugLabel;

  @override
  PaneRetainedScrollController create() =>
      PaneRetainedScrollController(debugLabel: debugLabel);

  @override
  void dispose(PaneRetainedScrollController controller) => controller.dispose();
}
