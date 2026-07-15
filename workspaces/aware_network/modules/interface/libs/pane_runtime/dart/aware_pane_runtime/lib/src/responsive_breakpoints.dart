import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';

/// Canonical device size classes for the Aware Interface.
///
/// Based on Material Design 3 window size classes, adapted for Aware's
/// three-pane shell architecture.
enum DeviceSizeClass {
  /// < 600px — phones portrait.
  compact,

  /// 600–899px — phones landscape, small tablets, narrow windows.
  medium,

  /// 900–1199px — tablets, typical laptops.
  expanded,

  /// >= 1200px — desktop wide screens.
  large,
}

/// Canonical platform type (includes web as a distinct class).
enum DevicePlatformType {
  /// iOS or Android native.
  mobile,

  /// macOS, Linux, Windows native.
  desktop,

  /// Any platform via browser.
  web,
}

/// Shared responsive breakpoint utilities for the Aware Interface.
///
/// Usage:
/// ```dart
/// final sc = ResponsiveBreakpoints.sizeClassOf(context);
/// if (sc == DeviceSizeClass.compact) { ... }
/// ```
class ResponsiveBreakpoints {
  ResponsiveBreakpoints._();

  static const double compactMax = 600;
  static const double mediumMax = 900;
  static const double expandedMax = 1200;

  /// Returns the [DeviceSizeClass] for the current [BuildContext] based on
  /// viewport width.
  static DeviceSizeClass sizeClassOf(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    return sizeClassFromWidth(width);
  }

  /// Returns the [DeviceSizeClass] for a given pixel width.
  static DeviceSizeClass sizeClassFromWidth(double width) {
    if (width < compactMax) return DeviceSizeClass.compact;
    if (width < mediumMax) return DeviceSizeClass.medium;
    if (width < expandedMax) return DeviceSizeClass.expanded;
    return DeviceSizeClass.large;
  }

  /// Returns the current [DevicePlatformType] (stable across the app
  /// lifetime).
  static DevicePlatformType get platformType {
    if (kIsWeb) return DevicePlatformType.web;
    switch (defaultTargetPlatform) {
      case TargetPlatform.iOS:
      case TargetPlatform.android:
        return DevicePlatformType.mobile;
      case TargetPlatform.macOS:
      case TargetPlatform.linux:
      case TargetPlatform.windows:
      case TargetPlatform.fuchsia:
        return DevicePlatformType.desktop;
    }
  }

  /// True if the viewport is in the compact size class (< 600px).
  static bool isCompact(BuildContext context) =>
      sizeClassOf(context) == DeviceSizeClass.compact;

  /// True if the viewport is compact or medium (< 900px).
  static bool isCompactOrMedium(BuildContext context) {
    final sc = sizeClassOf(context);
    return sc == DeviceSizeClass.compact || sc == DeviceSizeClass.medium;
  }
}
