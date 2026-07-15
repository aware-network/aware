import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/physics.dart';

import '../tokens/aware_motion.dart';
import '../diagnostics/glass_ticker_diagnostics.dart';

/// Preset kinematics for glass widgets.
///
/// Each preset defines a combination of behaviors:
/// - [none]: No kinematics (static glass)
/// - [subtle]: Settling only (no idle breathing)
/// - [alive]: Full breathing + settling on entry
/// - [responsive]: Touch/hover feedback
/// - [interactive]: Settling + response + hover/parallax (no idle breathing)
enum GlassKinematicPreset {
  /// No kinematics — static glass
  none,

  /// Settling only (no idle breathing)
  /// Good for: background panels, large surfaces
  subtle,

  /// Full breathing + settling on entry
  /// Good for: hero sections, feature cards
  alive,

  /// Touch/hover feedback only (no breathing)
  /// Good for: buttons, interactive chips
  responsive,

  /// Settling + response + hover/parallax (no idle breathing)
  /// Good for: primary cards, gate cards
  interactive,
}

/// Configuration for glass breathing behavior.
///
/// Creates subtle, continuous life in glass surfaces.
/// Should be imperceptible unless you look for it.
class GlassBreathing {
  /// How much opacity varies (e.g., 0.02 = ±2%)
  final double opacityRange;

  /// How much blur varies (e.g., 0.5 = ±0.5px)
  final double blurRange;

  /// Duration of one breath cycle
  final Duration period;

  /// Curve for the breath (usually sinusoidal)
  final Curve curve;

  const GlassBreathing({
    this.opacityRange = 0.015,
    this.blurRange = 0.3,
    this.period = const Duration(milliseconds: 5000),
    this.curve = Curves.easeInOut,
  });

  /// No breathing
  static const GlassBreathing none = GlassBreathing(
    opacityRange: 0,
    blurRange: 0,
  );

  /// Barely perceptible breathing
  static const GlassBreathing subtle = GlassBreathing(
    opacityRange: 0.01,
    blurRange: 0.2,
    period: Duration(milliseconds: 6000),
  );

  /// More noticeable breathing
  static const GlassBreathing alive = GlassBreathing(
    opacityRange: 0.02,
    blurRange: 0.5,
    period: Duration(milliseconds: 4500),
  );
}

/// Configuration for glass settling behavior.
///
/// Spring physics when glass appears or state changes.
/// Creates physical "landing" feel.
class GlassSettling {
  /// Spring damping ratio ζ (0.5 = underdamped, 1.0 = critical, >1 = overdamped)
  final double damping;

  /// Spring stiffness (higher = faster settle)
  final double stiffness;

  /// Perceived mass (higher = heavier feel)
  final double mass;

  /// Initial scale offset (1.0 = no scale, 0.95 = start smaller)
  final double initialScale;

  /// Initial vertical offset in logical pixels
  final double initialOffset;

  /// Duration of the settle animation
  final Duration duration;

  const GlassSettling({
    this.damping = 0.7,
    this.stiffness = 180,
    this.mass = 1.0,
    this.initialScale = 0.97,
    this.initialOffset = 8.0,
    this.duration = const Duration(milliseconds: 600),
  });

  /// No settling — instant appear
  static const GlassSettling none = GlassSettling(
    initialScale: 1.0,
    initialOffset: 0,
    duration: Duration.zero,
  );

  /// Subtle settle — barely noticeable
  static const GlassSettling subtle = GlassSettling(
    damping: 0.85,
    stiffness: 160,
    initialScale: 0.98,
    initialOffset: 4.0,
    duration: Duration(milliseconds: 400),
  );

  /// Confident settle — clear landing
  static const GlassSettling confident = GlassSettling(
    damping: 0.82,
    stiffness: 170,
    initialScale: 0.96,
    initialOffset: 10.0,
    duration: Duration(milliseconds: 550),
  );
}

/// Configuration for glass touch response.
///
/// Creates satisfying press/release feedback.
/// Press is FAST (immediate), release is SLOW with overshoot (satisfying).
class GlassResponse {
  /// Scale when pressed (e.g., 0.97 = 3% smaller)
  final double pressScale;

  /// Scale overshoot on release (e.g., 1.03 = 3% larger before settling)
  final double releaseOvershoot;

  /// Duration of press animation (should be fast)
  final Duration pressDuration;

  /// Duration of release animation (slower, with spring)
  final Duration releaseDuration;

  /// Curve for press (fast, immediate)
  final Curve pressCurve;

  /// Curve for release (spring-like overshoot)
  final Curve releaseCurve;

  const GlassResponse({
    this.pressScale = 0.97,
    this.releaseOvershoot = 1.02,
    this.pressDuration = const Duration(milliseconds: 80),
    this.releaseDuration = const Duration(milliseconds: 280),
    this.pressCurve = Curves.easeOut,
    this.releaseCurve = Curves.elasticOut,
  });

  /// No response
  static const GlassResponse none = GlassResponse(
    pressScale: 1.0,
    releaseOvershoot: 1.0,
    pressDuration: Duration.zero,
    releaseDuration: Duration.zero,
  );

  /// Subtle response — barely noticeable
  static const GlassResponse subtle = GlassResponse(
    pressScale: 0.99,
    releaseOvershoot: 1.002,
    pressDuration: Duration(milliseconds: 60),
    releaseDuration: Duration(milliseconds: 220),
  );

  /// Standard response — clear feedback
  static const GlassResponse standard = GlassResponse(
    pressScale: 0.985,
    releaseOvershoot: 1.004,
    pressDuration: Duration(milliseconds: 70),
    releaseDuration: Duration(milliseconds: 260),
  );

  /// Bouncy response — playful, more overshoot
  static const GlassResponse bouncy = GlassResponse(
    pressScale: 0.975,
    releaseOvershoot: 1.01,
    pressDuration: Duration(milliseconds: 90),
    releaseDuration: Duration(milliseconds: 320),
  );
}

/// Configuration for glass hover behavior (desktop pointer).
///
/// Hover is subtle: a small lift + slight scale to make glass feel responsive
/// without becoming “buttony”.
class GlassHover {
  /// Scale multiplier when hovered (e.g., 1.01 = 1% larger).
  final double hoverScale;

  /// Lift in logical pixels when hovered (positive = lift upward).
  final double hoverLift;

  const GlassHover({this.hoverScale = 1.006, this.hoverLift = 2.0});

  static const GlassHover none = GlassHover(hoverScale: 1.0, hoverLift: 0.0);

  static const GlassHover subtle = GlassHover(
    hoverScale: 1.003,
    hoverLift: 1.0,
  );

  static const GlassHover interactive = GlassHover(
    hoverScale: 1.006,
    hoverLift: 1.5,
  );
}

/// Configuration for glass floating/parallax behavior.
///
/// Current v0 implementation: pointer-follow parallax (desktop/web).
class GlassFloating {
  /// Parallax translation factor relative to the smaller side of the widget.
  ///
  /// Example: 0.02 on a 240px-tall card → ~5px max offset.
  final double parallaxFactor;

  /// Whether to respond to pointer position (desktop/web).
  final bool followPointer;

  /// Whether to respond to touch drag (mobile).
  ///
  /// Disabled by default because translating full glass surfaces while
  /// scrolling can feel like the UI is “sliding away” and can be expensive
  /// when the surface contains a blur.
  final bool followTouch;

  /// Clamp maximum translation (in px) to prevent exaggerated motion on large panes.
  final double maxTranslation;

  /// Whether to translate on the X axis.
  ///
  /// Default is enabled.
  final bool translateX;

  /// Whether to translate on the Y axis.
  ///
  /// Default is disabled to avoid “floating” up/down in vertical stacks.
  final bool translateY;

  const GlassFloating({
    this.parallaxFactor = 0.012,
    this.followPointer = true,
    this.followTouch = false,
    this.maxTranslation = 6.0,
    this.translateX = true,
    this.translateY = false,
  });

  static const GlassFloating none = GlassFloating(
    parallaxFactor: 0.0,
    followPointer: false,
    followTouch: false,
    maxTranslation: 0.0,
    translateX: false,
    translateY: false,
  );

  static const GlassFloating subtle = GlassFloating(
    parallaxFactor: 0.008,
    followPointer: true,
    maxTranslation: 3.0,
  );

  static const GlassFloating interactive = GlassFloating(
    parallaxFactor: 0.008,
    followPointer: true,
    maxTranslation: 3.5,
  );
}

/// Controller for glass kinematic animations.
///
/// Manages the animation controllers for breathing and settling.
/// Used internally by [KinematicGlass].
class GlassKinematicController {
  final TickerProvider vsync;
  final GlassBreathing breathing;
  final GlassSettling settling;

  AnimationController? _breathController;
  AnimationController? _settleController;

  // Breathing outputs
  double _breathOpacity = 0;
  double _breathBlur = 0;

  // Settling outputs
  double _settleScale = 1.0;
  double _settleOffset = 0;
  double _settleOpacity = 1.0;

  GlassKinematicController({
    required this.vsync,
    required this.breathing,
    required this.settling,
  }) {
    _initBreathing();
    _initSettling();
  }

  void _initBreathing() {
    if (breathing.opacityRange == 0 && breathing.blurRange == 0) return;

    _breathController = AnimationController(
      vsync: vsync,
      duration: breathing.period,
    );

    _breathController!.addListener(_updateBreathing);
    _breathController!.repeat();
    GlassTickerDiagnostics.onKinematicBreathingTickerStarted();
  }

  void _initSettling() {
    if (settling.duration == Duration.zero) {
      _settleScale = 1.0;
      _settleOffset = 0;
      _settleOpacity = 1.0;
      return;
    }

    _settleController = AnimationController.unbounded(vsync: vsync);
    _settleController!.addListener(_updateSettling);

    // Start un-settled (caller triggers settle on visibility change).
    _settleController!.value = 0.0;
    _settleScale = settling.initialScale;
    _settleOffset = settling.initialOffset;
    _settleOpacity = 0.0;
  }

  void _updateBreathing() {
    if (_breathController == null) return;

    // Sine wave for smooth breathing
    final t = _breathController!.value;
    final breathValue = math.sin(t * 2 * math.pi);

    _breathOpacity = breathValue * breathing.opacityRange;
    _breathBlur = breathValue * breathing.blurRange;
  }

  void _updateSettling() {
    if (_settleController == null) return;

    final t = _settleController!.value.clamp(-0.2, 1.4);

    // Interpolate from initial to final
    _settleScale = settling.initialScale + (1.0 - settling.initialScale) * t;
    _settleOffset = settling.initialOffset * (1 - t);
    _settleOpacity = t.clamp(0.0, 1.0);
  }

  /// Trigger the settling animation (call when glass becomes visible).
  void settle() {
    if (_settleController == null) return;

    final spring = AwareMotion.spring(
      mass: settling.mass,
      stiffness: settling.stiffness,
      dampingRatio: settling.damping,
    );

    GlassTickerDiagnostics.onKinematicSettlingStarted();
    _settleController!
        .animateWith(
          SpringSimulation(spring, _settleController!.value, 1.0, 0.0),
        )
        .whenCompleteOrCancel(
          GlassTickerDiagnostics.onKinematicSettlingStopped,
        );
  }

  /// Current breathing opacity modifier.
  double get breathOpacity => _breathOpacity;

  /// Current breathing blur modifier.
  double get breathBlur => _breathBlur;

  /// Current settling scale.
  double get settleScale => _settleScale;

  /// Current settling vertical offset.
  double get settleOffset => _settleOffset;

  /// Current settling opacity.
  double get settleOpacity => _settleOpacity;

  /// Whether settling animation is complete.
  bool get hasSettled {
    if (_settleController == null) return true;
    if (_settleController!.isAnimating) return false;
    return (_settleController!.value - 1.0).abs() < 0.01;
  }

  /// Combined listenable for both animations.
  Listenable get listenable {
    final listenables = <Listenable>[];
    if (_breathController != null) listenables.add(_breathController!);
    if (_settleController != null) listenables.add(_settleController!);
    if (listenables.isEmpty) return const _EmptyListenable();
    return Listenable.merge(listenables);
  }

  void dispose() {
    if (_breathController != null) {
      GlassTickerDiagnostics.onKinematicBreathingTickerStopped();
    }
    _breathController?.dispose();
    _settleController?.dispose();
  }
}

/// Empty listenable for when no controllers are active.
class _EmptyListenable implements Listenable {
  const _EmptyListenable();

  @override
  void addListener(VoidCallback listener) {}

  @override
  void removeListener(VoidCallback listener) {}
}

/// Extension to get kinematic configs from presets.
extension GlassKinematicPresetExtension on GlassKinematicPreset {
  /// Get breathing config for this preset.
  GlassBreathing get breathing => switch (this) {
    GlassKinematicPreset.none => GlassBreathing.none,
    GlassKinematicPreset.subtle => GlassBreathing.none,
    GlassKinematicPreset.alive => GlassBreathing.alive,
    GlassKinematicPreset.responsive => GlassBreathing.none,
    GlassKinematicPreset.interactive => GlassBreathing.none,
  };

  /// Get settling config for this preset.
  GlassSettling get settling => switch (this) {
    GlassKinematicPreset.none => GlassSettling.none,
    GlassKinematicPreset.subtle => GlassSettling.subtle,
    GlassKinematicPreset.alive => GlassSettling.confident,
    GlassKinematicPreset.responsive => GlassSettling.subtle,
    GlassKinematicPreset.interactive => GlassSettling.confident,
  };

  /// Get response config for this preset.
  GlassResponse get response => switch (this) {
    GlassKinematicPreset.none => GlassResponse.none,
    GlassKinematicPreset.subtle => GlassResponse.none,
    GlassKinematicPreset.alive => GlassResponse.subtle,
    GlassKinematicPreset.responsive => GlassResponse.standard,
    GlassKinematicPreset.interactive => GlassResponse.standard,
  };

  /// Get hover config for this preset.
  GlassHover get hover => switch (this) {
    GlassKinematicPreset.none => GlassHover.none,
    GlassKinematicPreset.subtle => GlassHover.none,
    GlassKinematicPreset.alive => GlassHover.subtle,
    GlassKinematicPreset.responsive => GlassHover.subtle,
    GlassKinematicPreset.interactive => GlassHover.interactive,
  };

  /// Get floating config for this preset.
  GlassFloating get floating => switch (this) {
    GlassKinematicPreset.none => GlassFloating.none,
    GlassKinematicPreset.subtle => GlassFloating.none,
    GlassKinematicPreset.alive => GlassFloating.subtle,
    GlassKinematicPreset.responsive => GlassFloating.none,
    GlassKinematicPreset.interactive => GlassFloating.interactive,
  };
}
