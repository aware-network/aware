import 'package:flutter/widgets.dart';

/// Canonical "glass field" signals shared across widgets.
///
/// v0: ambient shear (tilt) only.
/// vNext: pressure/energy channels for optics + haptics.
class GlassFieldController extends ChangeNotifier {
  Offset _shear = Offset.zero;

  /// Ambient shear in normalized space (-1..1) for X/Y.
  Offset get shear => _shear;

  set shear(Offset value) {
    final clamped = Offset(
      value.dx.clamp(-1.0, 1.0),
      value.dy.clamp(-1.0, 1.0),
    );

    // Avoid notifying for tiny sensor jitter.
    final dx = clamped.dx - _shear.dx;
    final dy = clamped.dy - _shear.dy;
    if ((dx * dx + dy * dy) < 0.000004) return; // ~0.002 delta

    _shear = clamped;
    notifyListeners();
  }
}

/// Provides [GlassFieldController] to descendants.
///
/// Intended usage:
/// - App creates a controller at the root.
/// - Platform drivers (tilt, haptics, etc.) update controller.
/// - Widgets (KinematicGlass, GlassMaterial) read the field.
class GlassFieldScope extends InheritedNotifier<GlassFieldController> {
  const GlassFieldScope({
    super.key,
    required GlassFieldController controller,
    required super.child,
  }) : super(notifier: controller);

  static GlassFieldController? maybeOf(BuildContext context) {
    return context
        .dependOnInheritedWidgetOfExactType<GlassFieldScope>()
        ?.notifier;
  }

  static GlassFieldController of(BuildContext context) {
    final controller = maybeOf(context);
    assert(controller != null, 'GlassFieldScope not found in context');
    return controller!;
  }
}
