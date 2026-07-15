import 'package:flutter/material.dart';

import 'pane_key.dart';

/// Presentation metadata that hosts can use for menus/tooltips.
class PaneDisplayInfo {
  const PaneDisplayInfo({
    required this.paneKey,
    required this.title,
    this.description = 'Pane',
    this.icon = Icons.tab,
    this.closeable = true,
    this.resizable = true,
    this.badgeText,
  });

  final PaneKey paneKey;
  final String title;
  final String description;
  final IconData icon;
  final bool closeable;
  final bool resizable;
  final String? badgeText;

  PaneDisplayInfo copyWith({
    PaneKey? paneKey,
    String? title,
    String? description,
    IconData? icon,
    bool? closeable,
    bool? resizable,
    String? badgeText,
  }) {
    return PaneDisplayInfo(
      paneKey: paneKey ?? this.paneKey,
      title: title ?? this.title,
      description: description ?? this.description,
      icon: icon ?? this.icon,
      closeable: closeable ?? this.closeable,
      resizable: resizable ?? this.resizable,
      badgeText: badgeText ?? this.badgeText,
    );
  }
}
