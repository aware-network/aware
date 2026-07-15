import 'package:flutter/material.dart';

/// A slot in a window — represents one available pane position.
///
/// Window uses slots to declare which panes CAN be shown. The rail
/// renders these slots as navigation items. Window never imports
/// pane implementations — slots carry presentational metadata only.
class WindowSlot {
  const WindowSlot({
    required this.slotId,
    required this.paneId,
    required this.label,
    required this.icon,
    this.accentColor,
    this.isActive = false,
  });

  /// Unique identifier for this slot within the window.
  final String slotId;

  /// The presenter paneId this slot maps to (matches [WindowSectionConfig.paneId]).
  final String paneId;

  /// Human-readable label (e.g. "Environment", "Workspace", "Agent").
  final String label;

  /// Icon shown in the rail for this slot.
  final IconData icon;

  /// Optional accent color for active/hover state. Falls back to theme primary.
  final Color? accentColor;

  /// Whether this slot is currently active/focused.
  final bool isActive;

  WindowSlot copyWith({
    String? slotId,
    String? paneId,
    String? label,
    IconData? icon,
    Color? accentColor,
    bool? isActive,
  }) {
    return WindowSlot(
      slotId: slotId ?? this.slotId,
      paneId: paneId ?? this.paneId,
      label: label ?? this.label,
      icon: icon ?? this.icon,
      accentColor: accentColor ?? this.accentColor,
      isActive: isActive ?? this.isActive,
    );
  }
}
