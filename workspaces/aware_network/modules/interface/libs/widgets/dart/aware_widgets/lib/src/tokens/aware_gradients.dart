import 'package:flutter/material.dart';

import 'aware_colors.dart';

/// AWARE gradient tokens for brand identity and visual effects.
///
/// Design principle: Gradients are used sparingly for emphasis.
/// They appear on: primary actions, active states, brand elements.
abstract final class AwareGradients {
  // ============================================
  // Canonical Aware Network Brand Gradient
  // ============================================

  /// Canonical Aware Network brand gradient — cyan → violet → pink.
  ///
  /// Used on the live entrance (`aware.run/`) title shader, protocol
  /// hairline, and atrium chrome. Reflects the Aware logo gradient.
  static const LinearGradient awareNetwork = LinearGradient(
    colors: [AwareColors.cyan, AwareColors.violet, AwareColors.pink],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  /// Horizontal Aware Network brand gradient.
  static const LinearGradient awareNetworkHorizontal = LinearGradient(
    colors: [AwareColors.cyan, AwareColors.violet, AwareColors.pink],
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
  );

  // ============================================
  // Brand Gradients (legacy aliases)
  // ============================================

  /// Primary brand gradient - blue to purple
  static const LinearGradient brand = LinearGradient(
    colors: [AwareColors.brandBlue, AwareColors.brandPurple],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  /// Accent gradient - purple to gold
  static const LinearGradient accent = LinearGradient(
    colors: [AwareColors.brandPurple, AwareColors.brandGold],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  /// Horizontal brand gradient
  static const LinearGradient brandHorizontal = LinearGradient(
    colors: [AwareColors.brandBlue, AwareColors.brandPurple],
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
  );

  // ============================================
  // Glass Highlights
  // ============================================

  /// Top highlight for glass - subtle white gradient
  static LinearGradient get glassHighlight => LinearGradient(
    colors: [
      AwareColors.glassHighlight.withValues(alpha: 0.12),
      AwareColors.glassHighlight.withValues(alpha: 0.0),
    ],
    begin: Alignment.topCenter,
    end: Alignment.center,
  );

  /// Edge highlight for glass - specular reflection
  static LinearGradient get glassEdge => LinearGradient(
    colors: [
      AwareColors.glassHighlight.withValues(alpha: 0.15),
      AwareColors.glassHighlight.withValues(alpha: 0.05),
      AwareColors.glassHighlight.withValues(alpha: 0.0),
    ],
    stops: const [0.0, 0.3, 1.0],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // ============================================
  // State Gradients
  // ============================================

  /// Active state border gradient
  static const LinearGradient activeBorder = LinearGradient(
    colors: [AwareColors.brandBlue, AwareColors.brandPurple],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  /// Success/crossed state subtle gradient
  static LinearGradient get crossedBorder => LinearGradient(
    colors: [
      AwareColors.success.withValues(alpha: 0.6),
      AwareColors.success.withValues(alpha: 0.3),
    ],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // ============================================
  // Refraction Effect
  // ============================================

  /// Refraction sweep for selection highlight
  static LinearGradient get refractionSweep => LinearGradient(
    colors: [
      Colors.transparent,
      AwareColors.glassHighlight.withValues(alpha: 0.2),
      Colors.transparent,
    ],
    stops: const [0.0, 0.5, 1.0],
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
  );
}
