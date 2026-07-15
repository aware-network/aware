import 'package:flutter/widgets.dart';

/// Optional pane-provided hints for the window “world” (background/lighting).
///
/// Contract: panes may suggest a mood/scrim/focus, but must not replace
/// backgrounds. The window host remains the owner of the world.
@immutable
class PaneWorldHint {
  const PaneWorldHint({
    this.mood = PaneWorldMood.focused,
    this.scrimStrength,
    this.focusPoint,
    this.graphDensity,
    this.accent,
    this.energy,
  });

  final PaneWorldMood mood;

  /// Preferred readability scrim for the world (0..1).
  ///
  /// The host may clamp/override based on accessibility and context.
  final double? scrimStrength;

  /// Optional normalized focus point (0..1) in window space.
  final Offset? focusPoint;

  /// Preferred graph density/contrast behind glass (0..1).
  ///
  /// Lower values indicate “text safe zone” softening.
  final double? graphDensity;

  /// Optional accent channel for the world.
  final PaneWorldAccent? accent;

  /// Preferred energy level for the world’s ambient motion (0..1).
  final double? energy;
}

enum PaneWorldMood { calm, focused, charged, welcome }

enum PaneWorldAccent { neutral, networkGreen, identityPurple }
