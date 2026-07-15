import 'package:flutter/widgets.dart';

import 'responsive_breakpoints.dart';

/// Exposes canonical device context to all descendant panes.
///
/// Placed at the Studio shell level so that any pane widget can access the
/// current size class, orientation, and platform type without calling
/// [MediaQuery] directly.
///
/// Usage in a pane:
/// ```dart
/// final layout = DeviceLayoutScope.of(context);
/// if (layout.isCompact) { /* phone layout */ }
/// ```
class DeviceLayoutScope extends InheritedWidget {
  const DeviceLayoutScope({
    super.key,
    required this.sizeClass,
    required this.orientation,
    required this.platformType,
    required super.child,
  });

  /// The current canonical size class based on viewport width.
  final DeviceSizeClass sizeClass;

  /// Portrait or landscape orientation.
  final Orientation orientation;

  /// Native mobile, native desktop, or web.
  final DevicePlatformType platformType;

  /// True when the viewport is in the compact size class (< 600px).
  bool get isCompact => sizeClass == DeviceSizeClass.compact;

  /// True when the viewport is in the medium size class (600–899px).
  bool get isMedium => sizeClass == DeviceSizeClass.medium;

  /// True when the viewport is in the expanded size class (900–1199px).
  bool get isExpanded => sizeClass == DeviceSizeClass.expanded;

  /// True when the viewport is in the large size class (>= 1200px).
  bool get isLarge => sizeClass == DeviceSizeClass.large;

  /// True when running on a native mobile platform (iOS / Android).
  bool get isMobile => platformType == DevicePlatformType.mobile;

  /// Returns the nearest [DeviceLayoutScope], or null if none exists.
  static DeviceLayoutScope? maybeOf(BuildContext context) {
    return context.dependOnInheritedWidgetOfExactType<DeviceLayoutScope>();
  }

  /// Returns the nearest [DeviceLayoutScope].
  ///
  /// Asserts that a scope exists; call from within the Studio shell subtree.
  static DeviceLayoutScope of(BuildContext context) {
    final scope = maybeOf(context);
    assert(scope != null, 'DeviceLayoutScope is missing above this widget.');
    return scope!;
  }

  @override
  bool updateShouldNotify(DeviceLayoutScope oldWidget) {
    return sizeClass != oldWidget.sizeClass ||
        orientation != oldWidget.orientation ||
        platformType != oldWidget.platformType;
  }
}
