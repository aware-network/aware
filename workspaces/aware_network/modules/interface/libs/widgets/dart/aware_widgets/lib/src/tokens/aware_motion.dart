import 'dart:math' as math;

import 'package:flutter/physics.dart';

/// AWARE motion tokens (springs + helpers).
///
/// Goal: a single canonical motion vocabulary across:
/// - layout physics (GlassLayout)
/// - surface kinematics (KinematicGlass)
/// - future desktop orchestration transitions
abstract final class AwareMotion {
  /// Converts a damping ratio (ζ) into a SpringDescription damping coefficient.
  static double dampingCoefficient({
    required double mass,
    required double stiffness,
    required double dampingRatio,
  }) {
    final clampedRatio = dampingRatio.isFinite ? dampingRatio : 1.0;
    return 2 * clampedRatio * math.sqrt(stiffness * mass);
  }

  /// Converts a SpringDescription damping coefficient into a damping ratio (ζ).
  static double dampingRatio({
    required double mass,
    required double stiffness,
    required double damping,
  }) {
    final denom = 2 * math.sqrt(stiffness * mass);
    if (denom == 0) return 1.0;
    return damping / denom;
  }

  /// Builds a [SpringDescription] from damping-ratio semantics.
  static SpringDescription spring({
    double mass = 1.0,
    double stiffness = 300.0,
    double dampingRatio = 0.7,
  }) {
    return SpringDescription(
      mass: mass,
      stiffness: stiffness,
      damping: dampingCoefficient(
        mass: mass,
        stiffness: stiffness,
        dampingRatio: dampingRatio,
      ),
    );
  }

  /// Computes damping ratio ζ from percent overshoot (0..1).
  ///
  /// For a standard 2nd-order underdamped system, PO = exp(-ζπ / √(1-ζ²)).
  /// Solving yields: ζ = -ln(PO) / √(π² + ln(PO)²).
  static double dampingRatioForOvershoot(double percentOvershoot) {
    if (!percentOvershoot.isFinite) return 1.0;
    if (percentOvershoot <= 0) return 1.0; // no overshoot
    if (percentOvershoot >= 1) return 0.0; // extreme overshoot

    final ln = math.log(percentOvershoot);
    return (-ln) / math.sqrt(math.pi * math.pi + ln * ln);
  }
}

/// Canonical spring presets for glass UI.
///
/// These are tuned to feel good on desktop (mouse + trackpad) while staying
/// stable under rapid target changes (AnimatedSize, window resizes).
abstract final class GlassSprings {
  // Layout (position) springs

  /// Quick, minimal overshoot. Good for responsive UI.
  static final SpringDescription layoutSnappy = AwareMotion.spring(
    mass: 1.0,
    stiffness: 400.0,
    dampingRatio: 0.625,
  );

  /// Gentle, no overshoot. Good for subtle transitions.
  static final SpringDescription layoutSmooth = AwareMotion.spring(
    mass: 1.0,
    stiffness: 200.0,
    dampingRatio: 0.92,
  );

  /// Calm, liquid motion. Overdamped and stable under rapid target changes.
  static final SpringDescription layoutLiquid = AwareMotion.spring(
    mass: 1.0,
    stiffness: 170.0,
    dampingRatio: 1.08,
  );

  /// Playful, more overshoot. Good for interactive elements.
  static final SpringDescription layoutBouncy = AwareMotion.spring(
    mass: 1.0,
    stiffness: 300.0,
    dampingRatio: 0.52,
  );

  /// Weighty, deliberate motion. Good for large panels.
  static final SpringDescription layoutHeavy = AwareMotion.spring(
    mass: 2.0,
    stiffness: 250.0,
    dampingRatio: 0.67,
  );

  // Kinematic (surface) springs

  /// Settling spring for glass entering/appearing.
  static final SpringDescription settleConfident = AwareMotion.spring(
    mass: 1.0,
    stiffness: 180.0,
    dampingRatio: 0.8,
  );

  /// Press down is fast and critically damped (no bounce).
  static final SpringDescription press = AwareMotion.spring(
    mass: 1.0,
    stiffness: 900.0,
    dampingRatio: 1.05,
  );

  /// Release spring is derived from desired overshoot, then uses a stable
  /// stiffness suitable for interactive glass.
  static SpringDescription release({
    required double pressScale,
    required double releaseOvershoot,
    double stiffness = 420.0,
    double mass = 1.0,
  }) {
    final step = (1.0 - pressScale).abs();
    if (step <= 0.0001) {
      return AwareMotion.spring(
        mass: mass,
        stiffness: stiffness,
        dampingRatio: 1.0,
      );
    }

    // Spring semantics: percent overshoot is relative to the step amplitude.
    // For UI calmness, clamp to avoid underdamped “shake” on small steps.
    final percentOvershoot = ((releaseOvershoot - 1.0) / step).clamp(0.0, 0.35);
    final computed = AwareMotion.dampingRatioForOvershoot(percentOvershoot);
    final dampingRatio = computed.clamp(0.72, 1.25);

    return AwareMotion.spring(
      mass: mass,
      stiffness: stiffness,
      dampingRatio: dampingRatio,
    );
  }

  /// Hover enter/exit spring (fast, stable).
  static final SpringDescription hover = AwareMotion.spring(
    mass: 1.0,
    stiffness: 420.0,
    dampingRatio: 1.05,
  );

  /// Pointer parallax spring (tracks moving targets without wobble).
  static final SpringDescription parallax = AwareMotion.spring(
    mass: 1.0,
    stiffness: 160.0,
    dampingRatio: 1.18,
  );
}
