import 'package:flutter/physics.dart';

import '../tokens/aware_motion.dart';

/// Physics configuration for GlassLayout.
///
/// Controls how child elements spring to new positions when
/// the layout changes (e.g., when one element expands).
class GlassLayoutPhysics {
  /// Spring description for position animations.
  final SpringDescription spring;

  /// Whether to apply pressure effect (slight scale reduction)
  /// to elements while they're being pushed.
  final bool pressureEffect;

  /// Amount of scale reduction during pressure (0.02 = 2%).
  final double pressureAmount;

  GlassLayoutPhysics({
    required this.spring,
    this.pressureEffect = false,
    this.pressureAmount = 0.02,
  });

  /// Create physics from individual spring parameters.
  GlassLayoutPhysics.custom({
    double mass = 1.0,
    double stiffness = 300.0,
    double damping = 20.0,
    this.pressureEffect = false,
    this.pressureAmount = 0.02,
  }) : spring = SpringDescription(
         mass: mass,
         stiffness: stiffness,
         damping: damping,
       );

  // ═══════════════════════════════════════════════════════════════
  // PRESETS
  // ═══════════════════════════════════════════════════════════════

  /// Quick, minimal overshoot. Good for responsive UI.
  static final GlassLayoutPhysics snappy = GlassLayoutPhysics(
    spring: GlassSprings.layoutSnappy,
  );

  /// Gentle, no overshoot. Good for subtle transitions.
  static final GlassLayoutPhysics smooth = GlassLayoutPhysics(
    spring: GlassSprings.layoutSmooth,
  );

  /// Calm, liquid motion. Overdamped and stable; recommended for desktop panes.
  static final GlassLayoutPhysics liquid = GlassLayoutPhysics(
    spring: GlassSprings.layoutLiquid,
    pressureEffect: true,
    pressureAmount: 0.015,
  );

  /// Playful, slight bounce. Good for interactive elements.
  static final GlassLayoutPhysics bouncy = GlassLayoutPhysics(
    spring: GlassSprings.layoutBouncy,
  );

  /// Weighty, deliberate motion. Good for large panels.
  static final GlassLayoutPhysics heavy = GlassLayoutPhysics(
    spring: GlassSprings.layoutHeavy,
  );

  /// Default preset: snappy and responsive.
  static GlassLayoutPhysics get standard => snappy;

  /// Copy with modifications.
  GlassLayoutPhysics copyWith({
    SpringDescription? spring,
    bool? pressureEffect,
    double? pressureAmount,
  }) {
    return GlassLayoutPhysics(
      spring: spring ?? this.spring,
      pressureEffect: pressureEffect ?? this.pressureEffect,
      pressureAmount: pressureAmount ?? this.pressureAmount,
    );
  }
}
