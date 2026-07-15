import 'package:flutter/material.dart';

import 'aware_colors.dart';

/// AWARE shadow tokens for depth and elevation.
///
/// Design principle: Depth comes from stacking, not gradients.
/// Shadows create the sense of glass layers lifting from reality.
abstract final class AwareShadows {
  // ============================================
  // Container Shadows (Glass Cards)
  // ============================================

  /// Primary glass card shadow - soft, wide, low contrast
  static List<BoxShadow> get glassCard => [
    BoxShadow(
      color: Colors.black.withValues(alpha: 0.25),
      blurRadius: 32,
      spreadRadius: 0,
      offset: const Offset(0, 8),
    ),
    BoxShadow(
      color: Colors.black.withValues(alpha: 0.1),
      blurRadius: 64,
      spreadRadius: -8,
      offset: const Offset(0, 16),
    ),
  ];

  /// Elevated glass card - more pronounced lift
  static List<BoxShadow> get glassCardElevated => [
    BoxShadow(
      color: Colors.black.withValues(alpha: 0.3),
      blurRadius: 40,
      spreadRadius: 0,
      offset: const Offset(0, 12),
    ),
    BoxShadow(
      color: Colors.black.withValues(alpha: 0.15),
      blurRadius: 80,
      spreadRadius: -8,
      offset: const Offset(0, 24),
    ),
  ];

  /// Inset element shadow - for rows/items inside cards
  static List<BoxShadow> get glassInset => [
    BoxShadow(
      color: Colors.black.withValues(alpha: 0.15),
      blurRadius: 8,
      spreadRadius: 0,
      offset: const Offset(0, 2),
    ),
  ];

  // ============================================
  // Glow Effects (Halos)
  // ============================================

  /// Active gate glow - purple/blue halo
  static List<BoxShadow> get activeGlow => [
    BoxShadow(
      color: AwareColors.brandPurple.withValues(alpha: 0.35),
      blurRadius: 24,
      spreadRadius: 4,
    ),
    BoxShadow(
      color: AwareColors.brandBlue.withValues(alpha: 0.2),
      blurRadius: 48,
      spreadRadius: 8,
    ),
  ];

  /// Crossed/success gate glow - subtle green halo
  static List<BoxShadow> get crossedGlow => [
    BoxShadow(
      color: AwareColors.success.withValues(alpha: 0.15),
      blurRadius: 16,
      spreadRadius: 2,
    ),
  ];

  /// Error gate glow - red warning halo
  static List<BoxShadow> get errorGlow => [
    BoxShadow(
      color: AwareColors.error.withValues(alpha: 0.25),
      blurRadius: 20,
      spreadRadius: 2,
    ),
  ];

  /// Focus ring glow - for interactive elements
  static List<BoxShadow> get focusGlow => [
    BoxShadow(
      color: AwareColors.brandPurple.withValues(alpha: 0.5),
      blurRadius: 8,
      spreadRadius: 1,
    ),
  ];

  // ============================================
  // Utility
  // ============================================

  /// Combine shadows with glow
  static List<BoxShadow> withGlow(List<BoxShadow> base, List<BoxShadow> glow) {
    return [...glow, ...base];
  }
}
