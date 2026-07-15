import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../kinematics/glass_kinematics.dart';
import '../kinematics/kinematic_glass.dart';
import 'aware_glass_material.dart';

/// Canonical full-height glass pane surface.
///
/// This is used by Studio (desktop) panes and large mobile surfaces.
///
/// Key design constraint:
/// - **Do not translate/scale the BackdropFilter** on every pointer/tilt tick.
///   Moving the blur region forces expensive re-rasterization and can read as a
///   “refresh” (the background appears to pop/change under the glass).
///
/// Instead, the pane keeps the blur region anchored and only shifts subtle
/// specular highlights + shadow lift based on kinematic values.
class AwareGlassPane extends StatelessWidget {
  const AwareGlassPane({
    super.key,
    required this.child,
    this.kinematicPreset = GlassKinematicPreset.subtle,
    this.hover = GlassHover.subtle,
    this.floating = GlassFloating.subtle,
    this.response = GlassResponse.none,
    this.blur = 18,
    this.tintColor,
    this.tintOpacity = 0.14,
    this.borderRadius = const BorderRadius.all(Radius.circular(16)),
    this.showHighlight = true,
    this.showBorder = true,
    this.showCornerBloom = false,
    this.shadowColor = Colors.black,
    this.shadowOpacity = 0.25,
    this.shadowBlurRadius = 18,
    this.shadowOffset = const Offset(0, 8),
  });

  final Widget child;

  final GlassKinematicPreset kinematicPreset;
  final GlassHover hover;
  final GlassFloating floating;
  final GlassResponse response;

  final double blur;
  final Color? tintColor;
  final double tintOpacity;
  final BorderRadius borderRadius;
  final bool showHighlight;
  final bool showBorder;
  final bool showCornerBloom;

  final Color shadowColor;
  final double shadowOpacity;
  final double shadowBlurRadius;
  final Offset shadowOffset;

  static double _lerp(double a, double b, double t) => a + (b - a) * t;

  @override
  Widget build(BuildContext context) {
    // Keep the expensive BackdropFilter subtree stable. Kinematic ticks should
    // modulate only cheap overlays (shadow + sheen), not rebuild the blur.
    final blurBase = blur.clamp(0.0, 80.0);
    final baseGlass = RepaintBoundary(
      child: AwareGlassMaterial(
        blur: blurBase,
        tintColor: tintColor,
        tintOpacity: tintOpacity.clamp(0.0, 1.0),
        borderRadius: borderRadius,
        showHighlight: showHighlight,
        showBorder: showBorder,
        showCornerBloom: showCornerBloom,
        child: RepaintBoundary(child: child),
      ),
    );

    return KinematicGlass(
      preset: kinematicPreset,
      hover: hover,
      floating: floating,
      response: response,
      builder: (context, glassChild, values) {
        final hoverT = values.hoverT.clamp(0.0, 1.0);
        // Only treat compression as "pressure" (ignore overshoot above 1.0).
        // Note: AwareGlassPane itself is not tap-interactive (no onTap), so
        // this will usually remain 0. Keep it for future-proofing.
        final pressT =
            ((1.0 - values.responseScale).clamp(0.0, 0.08).toDouble() / 0.08);

        final lift = _lerp(0.0, 2.0, hoverT);
        final shadowY = shadowOffset.dy - lift;
        final shadowBlur = _lerp(
          shadowBlurRadius,
          shadowBlurRadius + 6.0,
          hoverT,
        );
        final shadowAlpha = _lerp(
          shadowOpacity,
          math.min(0.35, shadowOpacity + 0.06),
          hoverT,
        );

        // Convert float offset to a normalized shear for highlight placement.
        final maxOffset = math.max(0.001, floating.maxTranslation);
        final sx = (values.floatOffset.dx / maxOffset).clamp(-1.0, 1.0);
        final sy = (values.floatOffset.dy / maxOffset).clamp(-1.0, 1.0);

        final sheenOpacity = (0.03 + (0.05 * hoverT) + (0.02 * pressT)).clamp(
          0.0,
          0.10,
        );
        final sheenCenter = Alignment(-0.35 + (sx * 0.18), -0.25 + (sy * 0.16));

        return Container(
          decoration: BoxDecoration(
            borderRadius: borderRadius,
            boxShadow: [
              BoxShadow(
                color: shadowColor.withValues(alpha: shadowAlpha),
                blurRadius: shadowBlur,
                offset: Offset(shadowOffset.dx, shadowY),
              ),
            ],
          ),
          child: Stack(
            children: [
              glassChild,
              if (sheenOpacity > 0)
                Positioned.fill(
                  child: IgnorePointer(
                    child: ClipRRect(
                      borderRadius: borderRadius,
                      child: DecoratedBox(
                        decoration: BoxDecoration(
                          gradient: RadialGradient(
                            center: sheenCenter,
                            radius: 1.25,
                            colors: [
                              Colors.white.withValues(alpha: sheenOpacity),
                              Colors.transparent,
                            ],
                            stops: const [0.0, 1.0],
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
            ],
          ),
        );
      },
      child: baseGlass,
    );
  }
}
