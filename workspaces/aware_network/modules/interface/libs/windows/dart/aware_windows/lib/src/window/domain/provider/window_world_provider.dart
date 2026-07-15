import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

enum WindowWorldMood { calm, focused, charged, welcome }

enum WindowWorldAccent { neutral, networkGreen, identityPurple }

@immutable
class WindowWorldHint {
  const WindowWorldHint({
    this.mood = WindowWorldMood.welcome,
    this.focusPoint,
    this.scrimStrength = 0.0,
    this.graphDensity = 1.0,
    this.accent = WindowWorldAccent.neutral,
    this.energy = 0.0,
    this.backgroundOpacity = 1.0,
  });

  final WindowWorldMood mood;

  /// Optional normalized focus point (0..1) in window space.
  final Offset? focusPoint;

  /// Host-controlled readability scrim for the world (0..1).
  final double scrimStrength;

  /// Host-controlled graph density/contrast behind glass (0..1).
  final double graphDensity;

  /// Host-controlled accent channel for the world.
  final WindowWorldAccent accent;

  /// Host-controlled energy level for ambient motion (0..1).
  final double energy;

  /// Global world opacity (0..1). Useful for entrance/exit cinematics.
  final double backgroundOpacity;

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is WindowWorldHint &&
        other.mood == mood &&
        other.focusPoint == focusPoint &&
        other.scrimStrength == scrimStrength &&
        other.graphDensity == graphDensity &&
        other.accent == accent &&
        other.energy == energy &&
        other.backgroundOpacity == backgroundOpacity;
  }

  @override
  int get hashCode => Object.hash(
    mood,
    focusPoint,
    scrimStrength,
    graphDensity,
    accent,
    energy,
    backgroundOpacity,
  );

  WindowWorldHint copyWith({
    WindowWorldMood? mood,
    Offset? focusPoint,
    bool clearFocusPoint = false,
    double? scrimStrength,
    double? graphDensity,
    WindowWorldAccent? accent,
    double? energy,
    double? backgroundOpacity,
  }) {
    return WindowWorldHint(
      mood: mood ?? this.mood,
      focusPoint: clearFocusPoint ? null : (focusPoint ?? this.focusPoint),
      scrimStrength: scrimStrength ?? this.scrimStrength,
      graphDensity: graphDensity ?? this.graphDensity,
      accent: accent ?? this.accent,
      energy: energy ?? this.energy,
      backgroundOpacity: backgroundOpacity ?? this.backgroundOpacity,
    );
  }
}

class WindowWorldController extends StateNotifier<WindowWorldHint> {
  WindowWorldController() : super(const WindowWorldHint());

  void reset() => state = const WindowWorldHint();

  void setHint(WindowWorldHint hint) {
    if (state == hint) return;
    state = hint;
  }

  void update(WindowWorldHint Function(WindowWorldHint current) updater) {
    state = updater(state);
  }

  void setMood(WindowWorldMood mood) => state = state.copyWith(mood: mood);

  void setFocusPoint(Offset? focusPoint) => state = state.copyWith(
    focusPoint: focusPoint,
    clearFocusPoint: focusPoint == null,
  );

  void setScrimStrength(double value) =>
      state = state.copyWith(scrimStrength: value.clamp(0.0, 1.0));

  void setGraphDensity(double value) =>
      state = state.copyWith(graphDensity: value.clamp(0.0, 1.0));

  void setAccent(WindowWorldAccent accent) =>
      state = state.copyWith(accent: accent);

  void setEnergy(double value) =>
      state = state.copyWith(energy: value.clamp(0.0, 1.0));

  void setBackgroundOpacity(double value) =>
      state = state.copyWith(backgroundOpacity: value.clamp(0.0, 1.0));
}

final windowWorldControllerProvider =
    StateNotifierProvider.family<
      WindowWorldController,
      WindowWorldHint,
      String
    >((ref, windowId) => WindowWorldController());
