import 'dart:math' as math;

import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/physics.dart';
import 'package:flutter/scheduler.dart';

import 'glass_field.dart';
import 'glass_kinematics.dart';
import '../tokens/aware_motion.dart';
import '../diagnostics/glass_ticker_diagnostics.dart';

/// Wrapper that adds kinematic behavior to any glass widget.
///
/// Provides:
/// - Breathing: Subtle continuous life
/// - Settling: Spring physics on entry
/// - Response: Touch/press feedback (expansive glass feel)
///
/// Usage:
/// ```dart
/// KinematicGlass(
///   preset: GlassKinematicPreset.interactive,
///   onTap: () => print('tapped'),
///   child: AwareGlassMaterial(...),
/// )
/// ```
class KinematicGlass extends StatefulWidget {
  /// Child widget (typically AwareGlassMaterial)
  final Widget child;

  /// Preset for common kinematic behaviors.
  final GlassKinematicPreset? preset;

  /// Custom breathing configuration.
  final GlassBreathing? breathing;

  /// Custom settling configuration.
  final GlassSettling? settling;

  /// Custom response configuration.
  final GlassResponse? response;

  /// Custom hover configuration (desktop pointer).
  final GlassHover? hover;

  /// Custom floating/parallax configuration.
  final GlassFloating? floating;

  /// Whether to auto-trigger settling animation on first build.
  final bool autoSettle;

  /// Callback when tapped (enables touch response)
  final VoidCallback? onTap;

  /// Callback when long pressed
  final VoidCallback? onLongPress;

  /// Builder for custom rendering with kinematic values.
  final Widget Function(
    BuildContext context,
    Widget child,
    KinematicValues values,
  )?
  builder;

  const KinematicGlass({
    super.key,
    required this.child,
    this.preset = GlassKinematicPreset.subtle,
    this.breathing,
    this.settling,
    this.response,
    this.hover,
    this.floating,
    this.autoSettle = true,
    this.onTap,
    this.onLongPress,
    this.builder,
  });

  @override
  State<KinematicGlass> createState() => KinematicGlassState();
}

/// Kinematic values exposed for custom rendering.
class KinematicValues {
  final double breathOpacity;
  final double breathBlur;
  final double settleScale;
  final double settleOffset;
  final double settleOpacity;
  final double responseScale;
  final double hoverT;
  final double hoverScale;
  final double hoverLift;
  final Offset floatOffset;
  final bool isPressed;
  final bool isHovered;

  const KinematicValues({
    required this.breathOpacity,
    required this.breathBlur,
    required this.settleScale,
    required this.settleOffset,
    required this.settleOpacity,
    required this.responseScale,
    required this.hoverT,
    required this.hoverScale,
    required this.hoverLift,
    required this.floatOffset,
    required this.isPressed,
    required this.isHovered,
  });

  /// Combined opacity (settling only).
  ///
  /// Note: breathing should not modulate overall opacity for glass surfaces,
  /// because it mixes the blurred backdrop with the unfiltered background and
  /// can read as “background popping through”.
  double get opacity => settleOpacity;

  /// Combined scale (settling + hover + response)
  double get scale => settleScale * hoverScale * responseScale;

  /// Combined offset (floating + settling + hover lift).
  Offset get offset => floatOffset + Offset(0, settleOffset - hoverLift);

  static const KinematicValues identity = KinematicValues(
    breathOpacity: 0,
    breathBlur: 0,
    settleScale: 1.0,
    settleOffset: 0,
    settleOpacity: 1.0,
    responseScale: 1.0,
    hoverT: 0.0,
    hoverScale: 1.0,
    hoverLift: 0.0,
    floatOffset: Offset.zero,
    isPressed: false,
    isHovered: false,
  );
}

class KinematicGlassState extends State<KinematicGlass>
    with TickerProviderStateMixin {
  GlassKinematicController? _controller;
  bool _hasSettled = false;
  bool _reduceMotion = false;

  final GlobalKey _pointerRegionKey = GlobalKey();

  // Response animation
  AnimationController? _responseController;
  late GlassResponse _responseConfig;
  double _responseScale = 1.0;
  bool _isPressed = false;

  // Hover + floating
  late GlassHover _hoverConfig;
  late GlassFloating _floatingConfig;
  bool _isHovered = false;

  late _SpringValue _hoverT;
  late _SpringValue _floatX;
  late _SpringValue _floatY;
  Ticker? _pointerTicker;
  Duration _lastPointerTick = Duration.zero;
  int? _activeTouchPointer;
  bool _pointerTickerCounted = false;

  @override
  void initState() {
    super.initState();
    _initController();
    _initResponse();
    _initPointerKinematics();

    if (widget.autoSettle) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) settle();
      });
    }
  }

  void _initController() {
    final breathing = _reduceMotion
        ? GlassBreathing.none
        : (widget.breathing ??
              widget.preset?.breathing ??
              GlassBreathing.subtle);
    final settling = _reduceMotion
        ? GlassSettling.none
        : (widget.settling ?? widget.preset?.settling ?? GlassSettling.subtle);

    _controller = GlassKinematicController(
      vsync: this,
      breathing: breathing,
      settling: settling,
    );
  }

  void _initResponse() {
    _responseController?.dispose();
    _responseController = null;

    _responseConfig = _reduceMotion
        ? GlassResponse.none
        : (widget.response ?? widget.preset?.response ?? GlassResponse.none);

    // Only create controller if response is enabled AND the surface is actually
    // interactive. This prevents non-clickable panes from "jumping" when
    // interacting with inner controls.
    final isInteractive = widget.onTap != null || widget.onLongPress != null;
    if (_responseConfig.pressDuration != Duration.zero && isInteractive) {
      _responseController = AnimationController.unbounded(
        vsync: this,
        value: _responseScale,
      )..addListener(_updateResponse);
    } else {
      _responseScale = 1.0;
    }
  }

  void _initPointerKinematics() {
    _hoverConfig = _reduceMotion
        ? GlassHover.none
        : (widget.hover ?? widget.preset?.hover ?? GlassHover.none);
    _floatingConfig = _reduceMotion
        ? GlassFloating.none
        : (widget.floating ?? widget.preset?.floating ?? GlassFloating.none);

    _hoverT = _SpringValue(
      spring: GlassSprings.hover,
      value: _isHovered ? 1.0 : 0.0,
    );
    _floatX = _SpringValue(spring: GlassSprings.parallax, value: 0.0);
    _floatY = _SpringValue(spring: GlassSprings.parallax, value: 0.0);
  }

  void _updateResponse() {
    if (_responseController == null) return;
    setState(() {
      _responseScale = _responseController!.value;
    });
  }

  void _onPressDown(TapDownDetails details) {
    if (_responseConfig.pressDuration == Duration.zero) return;
    if (_responseController == null) return;

    _isPressed = true;
    _responseController?.stop();

    // Keep pressed interactions visually anchored for mouse/trackpad clicks.
    // On touch, the “alive” signal is finger-shear, so keep parallax active.
    final kind = details.kind;
    final isTouch =
        kind == null ||
        kind == PointerDeviceKind.touch ||
        kind == PointerDeviceKind.stylus ||
        kind == PointerDeviceKind.invertedStylus;

    if (!isTouch &&
        _floatingConfig.followPointer &&
        (_floatingConfig.translateX || _floatingConfig.translateY)) {
      _floatX.target = 0.0;
      _floatY.target = 0.0;
      _ensurePointerTicker();
    }

    _responseController!.animateWith(
      SpringSimulation(
        GlassSprings.press,
        _responseController!.value,
        _responseConfig.pressScale,
        0.0,
      ),
    );
  }

  void _onPressUp() {
    if (_responseConfig.pressDuration == Duration.zero) return;
    if (_responseController == null) return;

    _isPressed = false;

    _responseController!.animateWith(
      SpringSimulation(
        GlassSprings.release(
          pressScale: _responseConfig.pressScale,
          releaseOvershoot: _responseConfig.releaseOvershoot,
        ),
        _responseController!.value,
        1.0,
        0.0,
      ),
    );
  }

  void _onPressCancel() {
    if (_responseConfig.pressDuration == Duration.zero) return;
    if (_responseController == null) return;

    _isPressed = false;

    _responseController!.animateWith(
      SpringSimulation(
        GlassSprings.press,
        _responseController!.value,
        1.0,
        0.0,
      ),
    );
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();

    final media = MediaQuery.maybeOf(context);
    final nextReduceMotion = media?.disableAnimations ?? false;
    if (nextReduceMotion == _reduceMotion) return;

    _reduceMotion = nextReduceMotion;

    _controller?.dispose();
    _initController();
    _initResponse();
    _initPointerKinematics();
  }

  @override
  void didUpdateWidget(KinematicGlass oldWidget) {
    super.didUpdateWidget(oldWidget);

    final newPreset = widget.preset;
    final oldPreset = oldWidget.preset;

    if (newPreset != oldPreset ||
        widget.breathing != oldWidget.breathing ||
        widget.settling != oldWidget.settling) {
      _controller?.dispose();
      _initController();
    }

    if (newPreset != oldPreset ||
        widget.response != oldWidget.response ||
        widget.onTap != oldWidget.onTap ||
        widget.onLongPress != oldWidget.onLongPress) {
      _initResponse();
    }

    if (newPreset != oldPreset ||
        widget.hover != oldWidget.hover ||
        widget.floating != oldWidget.floating) {
      _initPointerKinematics();
    }
  }

  void settle() {
    if (_hasSettled) return;
    _hasSettled = true;
    _controller?.settle();
  }

  void resetSettle() {
    _hasSettled = false;
  }

  @override
  void dispose() {
    _controller?.dispose();
    _responseController?.dispose();
    if (_pointerTickerCounted) {
      GlassTickerDiagnostics.onKinematicPointerTickerStopped();
      _pointerTickerCounted = false;
    }
    _pointerTicker?.dispose();
    super.dispose();
  }

  void _ensurePointerTicker() {
    _pointerTicker ??= createTicker(_handlePointerTick);
    if (_pointerTicker!.isActive) return;
    _lastPointerTick = Duration.zero;
    _pointerTicker!.start();
    if (!_pointerTickerCounted) {
      GlassTickerDiagnostics.onKinematicPointerTickerStarted();
      _pointerTickerCounted = true;
    }
  }

  void _handlePointerTick(Duration elapsed) {
    if (_lastPointerTick == Duration.zero) {
      _lastPointerTick = elapsed;
      return;
    }

    final dt = (elapsed - _lastPointerTick).inMicroseconds / 1e6;
    _lastPointerTick = elapsed;

    _hoverT.step(dt);
    _floatX.step(dt);
    _floatY.step(dt);

    if (_hoverT.isAtRest && _floatX.isAtRest && _floatY.isAtRest) {
      _hoverT.snapIfResting();
      _floatX.snapIfResting();
      _floatY.snapIfResting();
      _pointerTicker?.stop();
      _lastPointerTick = Duration.zero;
      if (_pointerTickerCounted) {
        GlassTickerDiagnostics.onKinematicPointerTickerStopped();
        _pointerTickerCounted = false;
      }
    }

    setState(() {});
  }

  bool get _needsPointerRegion {
    final hoverEnabled =
        _hoverConfig.hoverLift != 0 || _hoverConfig.hoverScale != 1.0;
    return hoverEnabled || _floatEnabled;
  }

  bool get _floatEnabled =>
      (_floatingConfig.followPointer || _floatingConfig.followTouch) &&
      _floatingConfig.parallaxFactor > 0 &&
      (_floatingConfig.translateX || _floatingConfig.translateY);

  void _onHoverEnter(PointerEnterEvent event) {
    _isHovered = true;
    _hoverT.target = 1.0;
    _ensurePointerTicker();
  }

  void _onHoverExit(PointerExitEvent event) {
    _isHovered = false;
    _hoverT.target = 0.0;
    _returnFloatToAmbient();
  }

  void _onPointerDown(PointerDownEvent event) {
    if (!_floatEnabled) return;
    if (!_floatingConfig.followTouch) return;
    if (event.kind != PointerDeviceKind.touch &&
        event.kind != PointerDeviceKind.stylus &&
        event.kind != PointerDeviceKind.invertedStylus) {
      return;
    }

    _activeTouchPointer ??= event.pointer;
    if (_activeTouchPointer != event.pointer) return;

    _updateFloatFromLocal(event.localPosition);
  }

  void _onPointerMove(PointerMoveEvent event) {
    if (_activeTouchPointer != event.pointer) return;
    if (!_floatEnabled) return;

    _updateFloatFromLocal(event.localPosition);
  }

  void _onPointerUp(PointerUpEvent event) {
    if (_activeTouchPointer != event.pointer) return;
    _activeTouchPointer = null;

    _returnFloatToAmbient();
  }

  void _onPointerCancel(PointerCancelEvent event) {
    if (_activeTouchPointer != event.pointer) return;
    _activeTouchPointer = null;

    _returnFloatToAmbient();
  }

  void _returnFloatToAmbient() {
    if (!_floatEnabled) return;

    final ambientShear = GlassFieldScope.maybeOf(context)?.shear ?? Offset.zero;
    if (ambientShear == Offset.zero) {
      if (_floatX.target == 0.0 && _floatY.target == 0.0) return;
      _floatX.target = 0.0;
      _floatY.target = 0.0;
      _ensurePointerTicker();
      return;
    }

    _updateFloatFromShear(ambientShear, deadZone: _ambientDeadZone);
  }

  void _updateFloatFromLocal(Offset local) {
    // Important: compute pointer coordinates relative to the *untransformed*
    // pointer region (Listener/MouseRegion), not the inner transformed glass
    // content. Using a transformed RenderBox can create a feedback loop:
    // content moves → local coordinates change → targets change → shaking.
    final renderObject = _pointerRegionKey.currentContext?.findRenderObject();
    if (renderObject is! RenderBox || !renderObject.hasSize) return;

    final size = renderObject.size;
    if (size.width <= 0 || size.height <= 0) return;

    final nx = ((local.dx / size.width) - 0.5) * 2; // -1..1
    final ny = ((local.dy / size.height) - 0.5) * 2; // -1..1

    _updateFloatFromShear(Offset(nx, ny), deadZone: _pointerDeadZone);
  }

  static const double _pointerDeadZone = 0.12;
  static const double _ambientDeadZone = 0.05;

  void _updateFloatFromShear(Offset shear, {required double deadZone}) {
    if (!_floatEnabled) return;

    final renderObject = _pointerRegionKey.currentContext?.findRenderObject();
    if (renderObject is! RenderBox || !renderObject.hasSize) return;

    final size = renderObject.size;
    if (size.width <= 0 || size.height <= 0) return;

    final clampX = shear.dx.clamp(-1.0, 1.0);
    final clampY = shear.dy.clamp(-1.0, 1.0);

    // Avoid “tremble” from tiny deltas around center.
    final dx = clampX.abs() < deadZone ? 0.0 : clampX;
    final dy = clampY.abs() < deadZone ? 0.0 : clampY;

    final base = math.min(size.width, size.height);
    final maxOffset = (_floatingConfig.parallaxFactor * base).clamp(
      0.0,
      _floatingConfig.maxTranslation,
    );

    final nextX = _floatingConfig.translateX ? dx * maxOffset : 0.0;
    final nextY = _floatingConfig.translateY ? dy * maxOffset : 0.0;

    final minDelta = math.max(0.01, maxOffset * 0.01);
    if ((nextX - _floatX.target).abs() < minDelta &&
        (nextY - _floatY.target).abs() < minDelta) {
      return;
    }

    _floatX.target = nextX;
    _floatY.target = nextY;
    _ensurePointerTicker();
  }

  void _onHoverMove(PointerHoverEvent event) {
    if (!_floatEnabled) return;
    if (_isPressed) return;
    _updateFloatFromLocal(event.localPosition);
  }

  @override
  Widget build(BuildContext context) {
    final controller = _controller;

    if (controller == null) {
      return widget.child;
    }

    // Ambient shear (e.g. device tilt) keeps glass alive on mobile.
    // Only apply when not actively interacting (hover/touch/press).
    if (_floatEnabled &&
        !_isHovered &&
        _activeTouchPointer == null &&
        !_isPressed) {
      final ambientShear =
          GlassFieldScope.maybeOf(context)?.shear ?? Offset.zero;
      if (ambientShear != Offset.zero) {
        _updateFloatFromShear(ambientShear, deadZone: _ambientDeadZone);
      }
    }

    // Determine if we need gesture handling.
    // Enable gestures if: callback provided OR response config is non-zero.
    final hasResponse = _responseController != null;
    final hasGestures =
        widget.onTap != null || widget.onLongPress != null || hasResponse;

    final hoverT = _hoverT.value.clamp(0.0, 1.0);
    final hoverScale = 1.0 + ((_hoverConfig.hoverScale - 1.0) * hoverT);
    final hoverLift = _hoverConfig.hoverLift * hoverT;
    final floatOffset = Offset(
      _floatingConfig.translateX ? _floatX.value : 0.0,
      _floatingConfig.translateY ? _floatY.value : 0.0,
    );

    Widget content;
    if (widget.builder != null) {
      content = AnimatedBuilder(
        animation: controller.listenable,
        child: widget.child,
        builder: (context, child) {
          final values = KinematicValues(
            breathOpacity: controller.breathOpacity,
            breathBlur: controller.breathBlur,
            settleScale: controller.settleScale,
            settleOffset: controller.settleOffset,
            settleOpacity: controller.settleOpacity,
            responseScale: _responseScale,
            hoverT: hoverT,
            hoverScale: hoverScale,
            hoverLift: hoverLift,
            floatOffset: floatOffset,
            isPressed: _isPressed,
            isHovered: _isHovered,
          );
          return widget.builder!(context, child!, values);
        },
      );
    } else {
      // Default rendering with transforms
      content = AnimatedBuilder(
        animation: controller.listenable,
        builder: (context, child) {
          // Recalculate values inside builder for breathing/settling
          final breathValues = KinematicValues(
            breathOpacity: controller.breathOpacity,
            breathBlur: controller.breathBlur,
            settleScale: controller.settleScale,
            settleOffset: controller.settleOffset,
            settleOpacity: controller.settleOpacity,
            responseScale: _responseScale,
            hoverT: hoverT,
            hoverScale: hoverScale,
            hoverLift: hoverLift,
            floatOffset: floatOffset,
            isPressed: _isPressed,
            isHovered: _isHovered,
          );

          final brightness = (1.0 + (breathValues.breathOpacity * 0.35)).clamp(
            0.97,
            1.03,
          );

          Widget result = Transform.translate(
            offset: breathValues.offset,
            child: Transform.scale(
              scale: breathValues.scale,
              child: widget.child,
            ),
          );

          // “Breathing” should feel like light shifting through glass, not
          // transparency changing. Apply a tiny brightness modulation that
          // doesn't reveal the unblurred background.
          if (controller.breathing.opacityRange != 0) {
            result = ColorFiltered(
              colorFilter: ColorFilter.matrix(<double>[
                brightness,
                0,
                0,
                0,
                0,
                0,
                brightness,
                0,
                0,
                0,
                0,
                0,
                brightness,
                0,
                0,
                0,
                0,
                0,
                1,
                0,
              ]),
              child: result,
            );
          }

          if (breathValues.settleOpacity >= 1.0) return result;
          return Opacity(
            opacity: breathValues.settleOpacity.clamp(0.0, 1.0),
            child: result,
          );
        },
      );
    }

    if (hasGestures) {
      content = GestureDetector(
        onTapDown: _onPressDown,
        onTapUp: (_) {
          _onPressUp();
          widget.onTap?.call();
        },
        onTapCancel: _onPressCancel,
        onLongPress: widget.onLongPress,
        behavior: HitTestBehavior.opaque,
        child: content,
      );
    }

    if (_needsPointerRegion) {
      final cursor = (widget.onTap != null || widget.onLongPress != null)
          ? SystemMouseCursors.click
          : MouseCursor.defer;

      content = Listener(
        key: _pointerRegionKey,
        behavior: HitTestBehavior.translucent,
        onPointerDown: _onPointerDown,
        onPointerMove: _onPointerMove,
        onPointerUp: _onPointerUp,
        onPointerCancel: _onPointerCancel,
        child: MouseRegion(
          cursor: cursor,
          onEnter: _onHoverEnter,
          onExit: _onHoverExit,
          onHover: _onHoverMove,
          child: content,
        ),
      );
    }

    return content;
  }
}

class _SpringValue {
  _SpringValue({required this.spring, required this.value, double? target})
    : target = target ?? value;

  SpringDescription spring;
  double value;
  double velocity = 0.0;
  double target;

  static const double _restDisplacementThreshold = 0.001;
  static const double _restVelocityThreshold = 0.02;

  void step(double dt) {
    if (dt <= 0) return;

    // Sub-step integration to avoid oscillation from occasional large `dt`
    // (e.g. GC, resize) which can look like “hover shake”.
    const maxTimeStep = 1 / 90;
    var remaining = dt;

    while (remaining > 0) {
      final stepDt = math.min(remaining, maxTimeStep);
      _stepOnce(stepDt);
      remaining -= stepDt;
    }
  }

  void _stepOnce(double dt) {
    final x = value - target;
    final a = (-spring.stiffness * x - spring.damping * velocity) / spring.mass;
    velocity += a * dt;
    value += velocity * dt;
  }

  bool get isAtRest =>
      (value - target).abs() <= _restDisplacementThreshold &&
      velocity.abs() <= _restVelocityThreshold;

  void snapIfResting() {
    if (!isAtRest) return;
    value = target;
    velocity = 0.0;
  }
}
