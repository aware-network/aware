import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'window_header_data.dart';

/// Builder signature for window overlays.
typedef WindowOverlayBuilder =
    Widget Function(
      BuildContext context,
      WidgetRef ref,
      Map<String, dynamic>? arguments,
    );

typedef WindowOverlayHeaderBuilder = WindowHeaderData Function(WidgetRef ref);

/// Describes a logical overlay that can be mounted above a window.
class WindowOverlayDescriptor {
  const WindowOverlayDescriptor({
    required this.overlayId,
    required this.windowId,
    required this.builder,
    this.priority = OverlayPriority.modal,
    this.dismissPolicy = OverlayDismissPolicy.manual,
    this.scrimStyle = OverlayScrimStyle.translucent,
    this.headerBuilder,
    this.capturesFocus = true,
  });

  final String overlayId;
  final String windowId;
  final OverlayPriority priority;
  final OverlayDismissPolicy dismissPolicy;
  final OverlayScrimStyle scrimStyle;
  final WindowOverlayBuilder builder;
  final WindowOverlayHeaderBuilder? headerBuilder;
  final bool capturesFocus;
}

/// Ordering hints when multiple overlays compete for the same window.
enum OverlayPriority { modal, floating }

/// Describes how an overlay should be dismissed automatically.
enum OverlayDismissPolicy { manual, autoOnSectionChange }

/// Basic scrim styles supported by the overlay host.
enum OverlayScrimStyle { none, translucent, opaque }
