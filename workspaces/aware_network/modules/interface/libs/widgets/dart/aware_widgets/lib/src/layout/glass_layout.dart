import 'dart:math' as math;

import 'package:flutter/rendering.dart';
import 'package:flutter/scheduler.dart';
import 'package:flutter/widgets.dart';

import 'glass_layout_physics.dart';
import 'glass_layout_simulation.dart';
import '../diagnostics/glass_ticker_diagnostics.dart';

/// A physics-aware layout that animates child positions when layout changes.
///
/// When one child changes size (e.g., expands via [AnimatedSize]), other
/// children spring to their new positions instead of teleporting. This creates
/// the "glass pushes glass" effect.
///
/// Drop-in replacement for Column/Row:
/// ```dart
/// // Before
/// Column(children: [CardA(), CardB(), CardC()])
///
/// // After
/// GlassLayout(children: [CardA(), CardB(), CardC()])
/// ```
///
/// This is the AWARE layout standard. All panes should use [GlassLayout].
class GlassLayout extends StatefulWidget {
  /// Child widgets to layout.
  final List<Widget> children;

  /// Layout direction.
  final Axis direction;

  /// Spacing between children.
  final double spacing;

  /// Physics configuration for spring animations.
  /// Defaults to [GlassLayoutPhysics.standard] if not specified.
  final GlassLayoutPhysics? physics;

  /// Main axis alignment (like Column/Row).
  final MainAxisAlignment mainAxisAlignment;

  /// Cross axis alignment (like Column/Row).
  final CrossAxisAlignment crossAxisAlignment;

  /// Main axis size (like Column/Row).
  final MainAxisSize mainAxisSize;

  /// Whether to clip children while animating.
  ///
  /// Keep as [Clip.none] to allow slight overshoot.
  final Clip clipBehavior;

  const GlassLayout({
    super.key,
    required this.children,
    this.direction = Axis.vertical,
    this.spacing = 0.0,
    this.physics,
    this.mainAxisAlignment = MainAxisAlignment.start,
    this.crossAxisAlignment = CrossAxisAlignment.center,
    this.mainAxisSize = MainAxisSize.min,
    this.clipBehavior = Clip.none,
  });

  @override
  State<GlassLayout> createState() => _GlassLayoutState();
}

class _GlassLayoutState extends State<GlassLayout>
    with TickerProviderStateMixin {
  @override
  Widget build(BuildContext context) {
    final effectivePhysics = widget.physics ?? GlassLayoutPhysics.standard;

    return _GlassLayoutRenderWidget(
      vsync: this,
      direction: widget.direction,
      spacing: widget.spacing,
      physics: effectivePhysics,
      mainAxisAlignment: widget.mainAxisAlignment,
      crossAxisAlignment: widget.crossAxisAlignment,
      mainAxisSize: widget.mainAxisSize,
      textDirection: Directionality.of(context),
      verticalDirection: VerticalDirection.down,
      clipBehavior: widget.clipBehavior,
      children: widget.children,
    );
  }
}

class _GlassLayoutRenderWidget extends MultiChildRenderObjectWidget {
  const _GlassLayoutRenderWidget({
    required this.vsync,
    required this.direction,
    required this.spacing,
    required this.physics,
    required this.mainAxisAlignment,
    required this.crossAxisAlignment,
    required this.mainAxisSize,
    required this.textDirection,
    required this.verticalDirection,
    required this.clipBehavior,
    required super.children,
  });

  final TickerProvider vsync;
  final Axis direction;
  final double spacing;
  final GlassLayoutPhysics physics;
  final MainAxisAlignment mainAxisAlignment;
  final CrossAxisAlignment crossAxisAlignment;
  final MainAxisSize mainAxisSize;
  final TextDirection textDirection;
  final VerticalDirection verticalDirection;
  final Clip clipBehavior;

  @override
  RenderGlassLayout createRenderObject(BuildContext context) {
    return RenderGlassLayout(
      vsync: vsync,
      direction: direction,
      spacing: spacing,
      physics: physics,
      mainAxisAlignment: mainAxisAlignment,
      crossAxisAlignment: crossAxisAlignment,
      mainAxisSize: mainAxisSize,
      textDirection: textDirection,
      verticalDirection: verticalDirection,
      clipBehavior: clipBehavior,
    );
  }

  @override
  void updateRenderObject(
    BuildContext context,
    RenderGlassLayout renderObject,
  ) {
    renderObject
      ..vsync = vsync
      ..direction = direction
      ..spacing = spacing
      ..physics = physics
      ..mainAxisAlignment = mainAxisAlignment
      ..crossAxisAlignment = crossAxisAlignment
      ..mainAxisSize = mainAxisSize
      ..textDirection = textDirection
      ..verticalDirection = verticalDirection
      ..clipBehavior = clipBehavior;
  }
}

class GlassLayoutParentData extends ContainerBoxParentData<RenderBox> {}

class RenderGlassLayout extends RenderBox
    with
        ContainerRenderObjectMixin<RenderBox, GlassLayoutParentData>,
        RenderBoxContainerDefaultsMixin<RenderBox, GlassLayoutParentData> {
  RenderGlassLayout({
    required TickerProvider vsync,
    required Axis direction,
    required double spacing,
    required GlassLayoutPhysics physics,
    required MainAxisAlignment mainAxisAlignment,
    required CrossAxisAlignment crossAxisAlignment,
    required MainAxisSize mainAxisSize,
    required TextDirection textDirection,
    required VerticalDirection verticalDirection,
    required Clip clipBehavior,
  }) : _vsync = vsync,
       _direction = direction,
       _spacing = spacing,
       _physics = physics,
       _mainAxisAlignment = mainAxisAlignment,
       _crossAxisAlignment = crossAxisAlignment,
       _mainAxisSize = mainAxisSize,
       _textDirection = textDirection,
       _verticalDirection = verticalDirection,
       _clipBehavior = clipBehavior,
       _simulation = GlassLayoutSimulation(spring: physics.spring);

  GlassLayoutSimulation _simulation;

  TickerProvider _vsync;
  Ticker? _ticker;
  Duration _lastTick = Duration.zero;
  bool _tickerCounted = false;

  Axis get direction => _direction;
  Axis _direction;
  set direction(Axis value) {
    if (_direction == value) return;
    _direction = value;
    markNeedsLayout();
  }

  double get spacing => _spacing;
  double _spacing;
  set spacing(double value) {
    if (_spacing == value) return;
    _spacing = value;
    markNeedsLayout();
  }

  GlassLayoutPhysics get physics => _physics;
  GlassLayoutPhysics _physics;
  set physics(GlassLayoutPhysics value) {
    if (identical(_physics, value)) return;
    _physics = value;
    _simulation.updateSpring(value.spring);
    _ensureTicking();
    markNeedsPaint();
  }

  MainAxisAlignment get mainAxisAlignment => _mainAxisAlignment;
  MainAxisAlignment _mainAxisAlignment;
  set mainAxisAlignment(MainAxisAlignment value) {
    if (_mainAxisAlignment == value) return;
    _mainAxisAlignment = value;
    markNeedsLayout();
  }

  CrossAxisAlignment get crossAxisAlignment => _crossAxisAlignment;
  CrossAxisAlignment _crossAxisAlignment;
  set crossAxisAlignment(CrossAxisAlignment value) {
    if (_crossAxisAlignment == value) return;
    _crossAxisAlignment = value;
    markNeedsLayout();
  }

  MainAxisSize get mainAxisSize => _mainAxisSize;
  MainAxisSize _mainAxisSize;
  set mainAxisSize(MainAxisSize value) {
    if (_mainAxisSize == value) return;
    _mainAxisSize = value;
    markNeedsLayout();
  }

  TextDirection get textDirection => _textDirection;
  TextDirection _textDirection;
  set textDirection(TextDirection value) {
    if (_textDirection == value) return;
    _textDirection = value;
    markNeedsLayout();
  }

  VerticalDirection get verticalDirection => _verticalDirection;
  VerticalDirection _verticalDirection;
  set verticalDirection(VerticalDirection value) {
    if (_verticalDirection == value) return;
    _verticalDirection = value;
    markNeedsLayout();
  }

  Clip get clipBehavior => _clipBehavior;
  Clip _clipBehavior;
  set clipBehavior(Clip value) {
    if (_clipBehavior == value) return;
    _clipBehavior = value;
    markNeedsPaint();
  }

  TickerProvider get vsync => _vsync;
  set vsync(TickerProvider value) {
    if (identical(_vsync, value)) return;
    _vsync = value;
    if (!attached) return;

    final wasActive = _ticker?.isActive ?? false;
    if (_tickerCounted) {
      GlassTickerDiagnostics.onGlassLayoutTickerStopped();
      _tickerCounted = false;
    }
    _ticker?.dispose();
    _ticker = _vsync.createTicker(_handleTick);
    if (wasActive) {
      _startTicker();
    }
  }

  bool get _mainAxisReversed => switch (_direction) {
    Axis.vertical => _verticalDirection == VerticalDirection.up,
    Axis.horizontal => _textDirection == TextDirection.rtl,
  };

  bool get _crossAxisReversed => switch (_direction) {
    Axis.vertical => _textDirection == TextDirection.rtl,
    Axis.horizontal => _verticalDirection == VerticalDirection.up,
  };

  @override
  void attach(PipelineOwner owner) {
    super.attach(owner);
    _ticker ??= _vsync.createTicker(_handleTick);
  }

  @override
  void detach() {
    if (_tickerCounted) {
      GlassTickerDiagnostics.onGlassLayoutTickerStopped();
      _tickerCounted = false;
    }
    _ticker?.dispose();
    _ticker = null;
    super.detach();
  }

  void _handleTick(Duration elapsed) {
    if (_lastTick == Duration.zero) {
      _lastTick = elapsed;
      return;
    }

    final dt = (elapsed - _lastTick).inMicroseconds / 1e6;
    _lastTick = elapsed;

    _simulation.step(dt);
    markNeedsPaint();

    if (_simulation.isAtRest) {
      _simulation.snapToTargets();
      _ticker?.stop();
      _lastTick = Duration.zero;
      if (_tickerCounted) {
        GlassTickerDiagnostics.onGlassLayoutTickerStopped();
        _tickerCounted = false;
      }
    }
  }

  void _startTicker() {
    if (!attached) return;
    if (_ticker == null) return;
    if (_ticker!.isActive) return;

    _lastTick = Duration.zero;
    _ticker!.start();
    if (!_tickerCounted) {
      GlassTickerDiagnostics.onGlassLayoutTickerStarted();
      _tickerCounted = true;
    }
  }

  void _ensureTicking() {
    _startTicker();
  }

  double _mainSizeOf(Size size) =>
      _direction == Axis.vertical ? size.height : size.width;
  double _crossSizeOf(Size size) =>
      _direction == Axis.vertical ? size.width : size.height;

  BoxConstraints _constraintsForChild(BoxConstraints constraints) {
    final shouldStretch = _crossAxisAlignment == CrossAxisAlignment.stretch;

    return switch (_direction) {
      Axis.vertical => BoxConstraints(
        minWidth: shouldStretch && constraints.hasBoundedWidth
            ? constraints.maxWidth
            : 0.0,
        maxWidth: constraints.maxWidth,
        minHeight: 0.0,
        maxHeight: constraints.maxHeight,
      ),
      Axis.horizontal => BoxConstraints(
        minWidth: 0.0,
        maxWidth: constraints.maxWidth,
        minHeight: shouldStretch && constraints.hasBoundedHeight
            ? constraints.maxHeight
            : 0.0,
        maxHeight: constraints.maxHeight,
      ),
    };
  }

  double _crossOffsetForChild(double crossExtent, double childCross) {
    final remaining = crossExtent - childCross;

    return switch (_crossAxisAlignment) {
      CrossAxisAlignment.start => _crossAxisReversed ? remaining : 0.0,
      CrossAxisAlignment.end => _crossAxisReversed ? 0.0 : remaining,
      CrossAxisAlignment.center => remaining / 2.0,
      CrossAxisAlignment.stretch => 0.0,
      CrossAxisAlignment.baseline => 0.0,
    };
  }

  bool _targetsDiffer(List<double> newTargets) {
    final oldCount = _simulation.count;
    if (oldCount == 0) {
      // First layout: `syncTargets` will initialize new indices at target with
      // zero velocity, so there is no reason to start a ticker.
      return false;
    }

    // Treat sub-pixel target jitter as noise. If we tick for ~0.001px diffs, the
    // layout can end up scheduling frames continuously on some platforms.
    final threshold = _simulation.restDisplacementThreshold;

    final compareCount = math.min(oldCount, newTargets.length);
    for (int i = 0; i < compareCount; i++) {
      if ((newTargets[i] - _simulation.targetFor(i)).abs() > threshold) {
        return true;
      }
    }

    return false;
  }

  @override
  void setupParentData(RenderBox child) {
    if (child.parentData is! GlassLayoutParentData) {
      child.parentData = GlassLayoutParentData();
    }
  }

  @override
  void performLayout() {
    assert(
      _crossAxisAlignment != CrossAxisAlignment.baseline ||
          _direction == Axis.horizontal,
    );

    var totalChildrenMain = 0.0;
    var maxChildCross = 0.0;

    // Layout children and compute intrinsic extents.
    var childCount = 0;
    RenderBox? child = firstChild;
    while (child != null) {
      final childParentData = child.parentData as GlassLayoutParentData;
      child.layout(_constraintsForChild(constraints), parentUsesSize: true);

      totalChildrenMain += _mainSizeOf(child.size);
      maxChildCross = math.max(maxChildCross, _crossSizeOf(child.size));

      childCount++;
      child = childParentData.nextSibling;
    }

    final baseSpacingTotal = _spacing * math.max(0, childCount - 1);
    final totalMain = totalChildrenMain + baseSpacingTotal;

    final maxMainConstraint = _direction == Axis.vertical
        ? constraints.maxHeight
        : constraints.maxWidth;
    final hasBoundedMain = maxMainConstraint.isFinite;

    final desiredMain = (_mainAxisSize == MainAxisSize.max && hasBoundedMain)
        ? maxMainConstraint
        : totalMain;

    final desiredCross = switch (_direction) {
      Axis.vertical =>
        constraints.hasBoundedWidth ? constraints.maxWidth : maxChildCross,
      Axis.horizontal =>
        constraints.hasBoundedHeight ? constraints.maxHeight : maxChildCross,
    };

    size = constraints.constrain(
      _direction == Axis.vertical
          ? Size(desiredCross, desiredMain)
          : Size(desiredMain, desiredCross),
    );

    final mainExtent = _direction == Axis.vertical ? size.height : size.width;
    final crossExtent = _direction == Axis.vertical ? size.width : size.height;

    final freeSpace = math.max(0.0, mainExtent - totalMain);
    var leadingSpace = 0.0;
    var betweenSpace = _spacing;

    if (childCount > 0 && freeSpace > 0) {
      switch (_mainAxisAlignment) {
        case MainAxisAlignment.start:
          leadingSpace = 0.0;
          betweenSpace = _spacing;
        case MainAxisAlignment.end:
          leadingSpace = freeSpace;
          betweenSpace = _spacing;
        case MainAxisAlignment.center:
          leadingSpace = freeSpace / 2.0;
          betweenSpace = _spacing;
        case MainAxisAlignment.spaceBetween:
          leadingSpace = 0.0;
          betweenSpace = childCount > 1
              ? _spacing + (freeSpace / (childCount - 1))
              : 0.0;
        case MainAxisAlignment.spaceAround:
          betweenSpace = _spacing + (freeSpace / childCount);
          leadingSpace = betweenSpace / 2.0;
        case MainAxisAlignment.spaceEvenly:
          betweenSpace = _spacing + (freeSpace / (childCount + 1));
          leadingSpace = betweenSpace;
      }
    }

    final newTargets = List<double>.filled(childCount, 0.0, growable: false);

    // Assign target offsets to children.
    var index = 0;
    child = firstChild;

    if (_mainAxisReversed) {
      var mainPos = mainExtent - leadingSpace;

      while (child != null) {
        final childParentData = child.parentData as GlassLayoutParentData;
        final childMain = _mainSizeOf(child.size);

        mainPos -= childMain;
        final crossPos = _crossOffsetForChild(
          crossExtent,
          _crossSizeOf(child.size),
        );

        childParentData.offset = _direction == Axis.vertical
            ? Offset(crossPos, mainPos)
            : Offset(mainPos, crossPos);

        newTargets[index] = mainPos;

        mainPos -= betweenSpace;
        index++;
        child = childParentData.nextSibling;
      }
    } else {
      var mainPos = leadingSpace;

      while (child != null) {
        final childParentData = child.parentData as GlassLayoutParentData;
        final childMain = _mainSizeOf(child.size);
        final crossPos = _crossOffsetForChild(
          crossExtent,
          _crossSizeOf(child.size),
        );

        childParentData.offset = _direction == Axis.vertical
            ? Offset(crossPos, mainPos)
            : Offset(mainPos, crossPos);

        newTargets[index] = mainPos;

        mainPos += childMain + betweenSpace;
        index++;
        child = childParentData.nextSibling;
      }
    }

    final targetsChanged = _targetsDiffer(newTargets);
    _simulation.syncTargets(newTargets);
    if (targetsChanged || !_simulation.isAtRest) {
      _ensureTicking();
    }
  }

  double _scaleForPressure(double pressure) {
    if (!_physics.pressureEffect) return 1.0;
    final normalized = pressure.clamp(0.0, 1.0);
    if (normalized <= 0.0) return 1.0;
    return 1.0 - (normalized * _physics.pressureAmount);
  }

  void _paintChildren(PaintingContext context, Offset offset) {
    var index = 0;
    RenderBox? child = firstChild;

    while (child != null) {
      final renderChild = child;
      final childParentData = renderChild.parentData as GlassLayoutParentData;
      final translation =
          _simulation.positionFor(index) - _simulation.targetFor(index);
      final scale = _scaleForPressure(_simulation.pressureFor(index));

      final childOffset =
          childParentData.offset +
          (_direction == Axis.vertical
              ? Offset(0.0, translation)
              : Offset(translation, 0.0));

      if (scale == 1.0) {
        context.paintChild(renderChild, offset + childOffset);
      } else {
        final cx = renderChild.size.width / 2;
        final cy = renderChild.size.height / 2;

        final transform =
            Matrix4.translationValues(cx, cy, 0) *
            Matrix4.diagonal3Values(scale, scale, 1) *
            Matrix4.translationValues(-cx, -cy, 0);

        context.pushTransform(
          needsCompositing,
          offset + childOffset,
          transform,
          (context, offset) => context.paintChild(renderChild, offset),
        );
      }

      index++;
      child = childParentData.nextSibling;
    }
  }

  @override
  void paint(PaintingContext context, Offset offset) {
    if (_clipBehavior == Clip.none) {
      _paintChildren(context, offset);
      return;
    }

    context.pushClipRect(
      needsCompositing,
      offset,
      Offset.zero & size,
      _paintChildren,
      clipBehavior: _clipBehavior,
    );
  }

  @override
  bool hitTestChildren(BoxHitTestResult result, {required Offset position}) {
    var index = _simulation.count - 1;
    RenderBox? child = lastChild;

    while (child != null && index >= 0) {
      final renderChild = child;
      final childParentData = renderChild.parentData as GlassLayoutParentData;
      final translation =
          _simulation.positionFor(index) - _simulation.targetFor(index);
      final scale = _scaleForPressure(_simulation.pressureFor(index));

      final childOffset =
          childParentData.offset +
          (_direction == Axis.vertical
              ? Offset(0.0, translation)
              : Offset(translation, 0.0));

      final isHit = scale == 1.0
          ? result.addWithPaintOffset(
              offset: childOffset,
              position: position,
              hitTest: (result, transformed) =>
                  renderChild.hitTest(result, position: transformed),
            )
          : result.addWithPaintTransform(
              transform: (() {
                final cx = renderChild.size.width / 2;
                final cy = renderChild.size.height / 2;

                return Matrix4.translationValues(
                      childOffset.dx,
                      childOffset.dy,
                      0,
                    ) *
                    Matrix4.translationValues(cx, cy, 0) *
                    Matrix4.diagonal3Values(scale, scale, 1) *
                    Matrix4.translationValues(-cx, -cy, 0);
              })(),
              position: position,
              hitTest: (result, transformed) =>
                  renderChild.hitTest(result, position: transformed),
            );

      if (isHit) return true;

      index--;
      child = childParentData.previousSibling;
    }

    return false;
  }
}
