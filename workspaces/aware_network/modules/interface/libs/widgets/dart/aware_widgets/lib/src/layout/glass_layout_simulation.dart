import 'dart:math' as math;

import 'package:flutter/physics.dart';

/// A minimal 1D spring simulation for [GlassLayout].
///
/// Notes:
/// - Pure math/state: no widgets, no render objects.
/// - Targets may change every frame (e.g. AnimatedSize); the simulation tracks
///   the moving equilibrium without restarting animations.
/// - A simple non-overlap constraint keeps children ordered on the main axis.
class GlassLayoutSimulation {
  GlassLayoutSimulation({
    required SpringDescription spring,
    this.restDisplacementThreshold = 0.25,
    this.restVelocityThreshold = 2.0,
    this.maxTimeStep = 1 / 90,
  }) : _spring = spring;

  SpringDescription get spring => _spring;
  SpringDescription _spring;

  final double restDisplacementThreshold;
  final double restVelocityThreshold;

  /// Maximum integration step (seconds). Large frame gaps are sub-stepped.
  final double maxTimeStep;

  final List<double> _positions = <double>[];
  final List<double> _velocities = <double>[];
  final List<double> _targets = <double>[];
  final List<double> _pressures = <double>[];

  int get count => _positions.length;

  double positionFor(int index) => _positions[index];
  double targetFor(int index) => _targets[index];
  double pressureFor(int index) => _pressures[index];

  void _normalizeLengths() {
    final minLen = math.min(
      _positions.length,
      math.min(
        _velocities.length,
        math.min(_targets.length, _pressures.length),
      ),
    );

    if (_positions.length != minLen) _positions.length = minLen;
    if (_velocities.length != minLen) _velocities.length = minLen;
    if (_targets.length != minLen) _targets.length = minLen;
    if (_pressures.length != minLen) _pressures.length = minLen;
  }

  /// Updates targets and keeps existing positions to preserve visual continuity.
  ///
  /// New indices initialize to `target` with zero velocity.
  void syncTargets(List<double> newTargets) {
    _normalizeLengths();
    final newCount = newTargets.length;

    if (_positions.length > newCount) {
      // Avoid `removeRange` to reduce the chance of transient list invariant
      // mismatches causing hard-to-debug exceptions in layout.
      _positions.length = newCount;
      _velocities.length = newCount;
      _targets.length = newCount;
      _pressures.length = newCount;
    } else {
      while (_positions.length < newCount) {
        final index = _positions.length;
        final target = newTargets[index];
        _positions.add(target);
        _velocities.add(0.0);
        _targets.add(target);
        _pressures.add(0.0);
      }
    }

    for (int i = 0; i < newCount; i++) {
      _targets[i] = newTargets[i];
    }

    // If a target jump would create overlap (e.g. expanding item above),
    // resolve immediately so the next paint never shows a collision.
    resolveConstraints();
  }

  void updateSpring(SpringDescription spring) {
    _spring = spring;
  }

  /// Advances the simulation by [dtSeconds].
  ///
  /// Applies a unilateral constraint so children can't cross/overlap:
  /// `position[i] >= position[i-1] + (target[i] - target[i-1])`
  void step(double dtSeconds) {
    _normalizeLengths();
    if (_positions.isEmpty) return;
    if (dtSeconds <= 0) return;

    final maxStep = maxTimeStep <= 0 ? dtSeconds : maxTimeStep;
    var remaining = dtSeconds;

    while (remaining > 0) {
      final dt = math.min(remaining, maxStep);
      _stepOnce(dt);
      remaining -= dt;
    }
  }

  void _stepOnce(double dt) {
    final m = _spring.mass;
    final k = _spring.stiffness;
    final c = _spring.damping;

    for (int i = 0; i < _positions.length; i++) {
      final x = _positions[i] - _targets[i];
      final v = _velocities[i];

      // Damped spring: a = (-k*x - c*v) / m
      final a = (-k * x - c * v) / m;

      final nextV = v + a * dt;
      final nextX = _positions[i] + nextV * dt;

      _velocities[i] = nextV;
      _positions[i] = nextX;
    }

    // Enforce order / non-overlap on the main axis.
    resolveConstraints();
  }

  /// Enforces the non-overlap/order constraint without advancing time.
  ///
  /// This is used both after integration and immediately after target updates
  /// so layout changes never render interpenetrating children.
  void resolveConstraints() {
    _normalizeLengths();
    for (int i = 0; i < _pressures.length; i++) {
      _pressures[i] = 0.0;
    }

    for (int i = 1; i < _positions.length; i++) {
      final desiredDelta = _targets[i] - _targets[i - 1];
      final limit = _positions[i - 1] + desiredDelta;

      if (desiredDelta >= 0) {
        if (_positions[i] < limit) {
          final penetration = (limit - _positions[i]).abs();
          final relativeSpeed = (_velocities[i] - _velocities[i - 1]).abs();
          final pressure =
              ((penetration / 12.0) + (relativeSpeed / 1200.0) * 0.25).clamp(
                0.0,
                1.0,
              );
          _pressures[i] = math.max(_pressures[i], pressure);
          _pressures[i - 1] = math.max(_pressures[i - 1], pressure);

          _positions[i] = limit;
          if (_velocities[i] < 0) _velocities[i] = 0;
        }
      } else {
        if (_positions[i] > limit) {
          final penetration = (_positions[i] - limit).abs();
          final relativeSpeed = (_velocities[i] - _velocities[i - 1]).abs();
          final pressure =
              ((penetration / 12.0) + (relativeSpeed / 1200.0) * 0.25).clamp(
                0.0,
                1.0,
              );
          _pressures[i] = math.max(_pressures[i], pressure);
          _pressures[i - 1] = math.max(_pressures[i - 1], pressure);

          _positions[i] = limit;
          if (_velocities[i] > 0) _velocities[i] = 0;
        }
      }
    }
  }

  bool get isAtRest {
    _normalizeLengths();
    for (int i = 0; i < _positions.length; i++) {
      final dx = (_positions[i] - _targets[i]).abs();
      final dv = _velocities[i].abs();
      if (dx > restDisplacementThreshold || dv > restVelocityThreshold) {
        return false;
      }
    }
    return true;
  }

  void snapToTargets() {
    _normalizeLengths();
    for (int i = 0; i < _positions.length; i++) {
      _positions[i] = _targets[i];
      _velocities[i] = 0.0;
      _pressures[i] = 0.0;
    }
  }
}
