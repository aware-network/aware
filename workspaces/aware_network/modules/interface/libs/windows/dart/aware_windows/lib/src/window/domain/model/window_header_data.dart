import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Data describing how a window header should render.
class WindowHeaderData {
  const WindowHeaderData({
    required this.title,
    this.icon,
    this.subtitle,
    this.leadingActions = const [],
    this.trailingActions = const [],
    this.accentColor,
  });

  final String title;
  final IconData? icon;
  final String? subtitle;
  final List<WindowHeaderAction> leadingActions;
  final List<WindowHeaderAction> trailingActions;
  final Color? accentColor;
}

/// Callback signature for header actions.
typedef WindowHeaderActionCallback = Future<void> Function(WidgetRef ref);

/// Representation of an interactive action rendered in the window header.
class WindowHeaderAction {
  const WindowHeaderAction({
    required this.icon,
    required this.onPressed,
    this.tooltip,
    this.enabled = true,
    this.isActive = false,
    this.foregroundColor,
    this.badgeLabel,
    this.iconSize,
  });

  final IconData icon;
  final WindowHeaderActionCallback onPressed;
  final String? tooltip;
  final bool enabled;
  final bool isActive;
  final Color? foregroundColor;
  final String? badgeLabel;
  final double? iconSize;
}
