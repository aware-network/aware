import 'package:flutter/material.dart';

/// Context payload contributed by panes/hosts so a shared window chrome row can
/// render consistent breadcrumbs/badges/actions.
///
/// Canonical notes:
/// - `sectionId` targets a host-owned mount section (e.g. `workspace`), not a pane kind.
/// - Multiple contributors may publish contexts for the same section; the host
///   aggregates them by priority.
class WindowChromeContext {
  const WindowChromeContext({
    required this.sectionId,
    this.title,
    this.subtitle,
    this.breadcrumbs = const [],
    this.badges = const [],
    this.actions = const [],
    this.theme,
    this.secondary,
    this.metadata,
    this.notification,
    this.priority = 0,
  });

  /// Section identifier matching a host mount section id (e.g. `workspace`).
  final String sectionId;

  final String? title;
  final String? subtitle;
  final List<ChromeBreadcrumb> breadcrumbs;
  final List<ChromeBadge> badges;
  final List<ChromeAction> actions;
  final WindowChromeTheme? theme;
  final WindowChromeSecondaryContent? secondary;
  final ChromeMetadataModel? metadata;
  final ChromeNotification? notification;

  /// Higher priority contexts win when multiple panes contribute.
  final int priority;
}

class ChromeBreadcrumb {
  const ChromeBreadcrumb({
    required this.label,
    this.path,
    this.onTap,
    this.icon,
    this.tooltip,
  });

  final String label;
  final String? path;
  final VoidCallback? onTap;
  final IconData? icon;
  final String? tooltip;
}

class ChromeBadge {
  const ChromeBadge({
    required this.label,
    this.color,
    this.tooltip,
    this.style,
  });

  final String label;
  final Color? color;
  final String? tooltip;
  final ChromeBadgeStyle? style;
}

class ChromeAction {
  const ChromeAction({
    required this.icon,
    this.tooltip,
    required this.onPressed,
  });

  final IconData icon;
  final String? tooltip;
  final Future<void> Function()? onPressed;
}

/// Aggregated chrome context after merging every active contribution (per section).
class WindowChromeAggregateContext {
  const WindowChromeAggregateContext({
    this.title,
    this.subtitle,
    this.breadcrumbs = const [],
    this.badges = const [],
    this.actions = const [],
    this.theme,
    this.secondaryBadges = const [],
    this.secondaryBreadcrumbs = const [],
    this.metadata = const ChromeMetadataModel(),
    this.notification,
  });

  final String? title;
  final String? subtitle;
  final List<ChromeBreadcrumb> breadcrumbs;
  final List<ChromeBadge> badges;
  final List<ChromeAction> actions;
  final WindowChromeTheme? theme;
  final List<ChromeBadge> secondaryBadges;
  final List<ChromeBreadcrumb> secondaryBreadcrumbs;
  final ChromeMetadataModel metadata;
  final ChromeNotification? notification;
}

class WindowChromeTheme {
  const WindowChromeTheme({
    this.backgroundColor,
    this.backgroundGradient,
    this.textColor,
    this.titleStyle,
    this.subtitleStyle,
    this.emphasize = false,
    this.centerTitle = true,
  });

  final Color? backgroundColor;
  final Gradient? backgroundGradient;
  final Color? textColor;
  final TextStyle? titleStyle;
  final TextStyle? subtitleStyle;
  final bool emphasize;
  final bool centerTitle;
}

class WindowChromeSecondaryContent {
  const WindowChromeSecondaryContent({
    this.badges = const [],
    this.breadcrumbs = const [],
  });

  final List<ChromeBadge> badges;
  final List<ChromeBreadcrumb> breadcrumbs;
}

class ChromeBadgeStyle {
  const ChromeBadgeStyle({
    this.backgroundGradient,
    this.icon,
    this.pill = true,
    this.glow = false,
    this.iconPosition = BadgeIconPosition.left,
  });

  final Gradient? backgroundGradient;
  final IconData? icon;
  final bool pill;
  final bool glow;
  final BadgeIconPosition iconPosition;
}

enum BadgeIconPosition { left, right }

class ChromeMetadataEntry {
  const ChromeMetadataEntry({
    required this.label,
    this.icon,
    this.tooltip,
    this.color,
    this.onTap,
  });

  final String label;
  final IconData? icon;
  final String? tooltip;
  final Color? color;
  final VoidCallback? onTap;
}

class ChromeMetadataModel {
  const ChromeMetadataModel({
    this.manifest,
    this.mode,
    this.branch,
    this.receipts,
    this.scope,
    this.custom = const [],
  });

  final ChromeMetadataEntry? manifest;
  final ChromeMetadataEntry? mode;
  final ChromeMetadataEntry? branch;
  final ChromeMetadataEntry? receipts;
  final ChromeMetadataEntry? scope;
  final List<ChromeMetadataEntry> custom;

  bool get isEmpty =>
      manifest == null &&
      mode == null &&
      branch == null &&
      receipts == null &&
      scope == null &&
      custom.isEmpty;

  List<ChromeMetadataEntry> orderedEntries() {
    final entries = <ChromeMetadataEntry>[];
    if (manifest != null) entries.add(manifest!);
    if (mode != null) entries.add(mode!);
    if (branch != null) entries.add(branch!);
    if (receipts != null) entries.add(receipts!);
    if (scope != null) entries.add(scope!);
    entries.addAll(custom);
    return entries;
  }

  ChromeMetadataModel mergeMissing(ChromeMetadataModel? other) {
    if (other == null) return this;
    return ChromeMetadataModel(
      manifest: manifest ?? other.manifest,
      mode: mode ?? other.mode,
      branch: branch ?? other.branch,
      receipts: receipts ?? other.receipts,
      scope: scope ?? other.scope,
      custom: [...custom, ...other.custom],
    );
  }
}

enum ChromeNotificationSeverity { info, success, warning, danger }

class ChromeNotification {
  const ChromeNotification({
    required this.message,
    this.severity = ChromeNotificationSeverity.info,
    this.icon,
    this.onTap,
    this.ctaLabel,
  });

  final String message;
  final ChromeNotificationSeverity severity;
  final IconData? icon;
  final VoidCallback? onTap;
  final String? ctaLabel;
}
