import 'dart:ui';

import 'package:flutter/material.dart';

import '../tokens/aware_colors.dart';
import '../tokens/aware_gradients.dart';

/// Glass material effect with blur, tint, and specular highlights.
///
/// Creates a crystal lens appearance that:
/// - Blurs what's behind (BackdropFilter)
/// - Adds a tint for readability stability (but stays clear enough to "read the graph")
/// - Adds specular edge highlights for glass thickness
/// - Feels like "a lens sitting above reality"
///
/// Design principle: Glass lens, not frosted plastic.
/// Apple-style glass uses blur + tint + specular edges.
class AwareGlassMaterial extends StatelessWidget {
  const AwareGlassMaterial({
    super.key,
    required this.child,
    this.blur = 24.0,
    this.tintColor,
    this.tintOpacity = 0.55, // Reduced from 0.65 for more clarity
    this.borderRadius = const BorderRadius.all(Radius.circular(20)),
    this.showHighlight = true,
    this.showBorder = true,
    this.showCornerBloom = false,
  });

  /// Child widget to display on the glass
  final Widget child;

  /// Blur intensity (sigma). Higher = more frosted. Default: 24
  final double blur;

  /// Tint color for the glass. Defaults to dark smoked glass.
  final Color? tintColor;

  /// Opacity of the tint layer. Default: 0.55 (reduced for clarity)
  final double tintOpacity;

  /// Border radius of the glass material
  final BorderRadius borderRadius;

  /// Whether to show the specular highlights (top edge, inner gradient)
  final bool showHighlight;

  /// Whether to show the subtle outer stroke
  final bool showBorder;

  /// Whether to show corner bloom (for active state)
  final bool showCornerBloom;

  @override
  Widget build(BuildContext context) {
    final effectiveTint = tintColor ?? AwareColors.glassDark;

    return ClipRRect(
      borderRadius: borderRadius,
      child: BackdropFilter.grouped(
        filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
        child: Container(
          decoration: BoxDecoration(
            // Tinted glass background - slightly more transparent for clarity
            color: effectiveTint.withValues(alpha: tintOpacity),
            borderRadius: borderRadius,
            // Faint outer stroke for edge definition
            border: showBorder
                ? Border.all(
                    color: AwareColors.glassBorder.withValues(alpha: 0.2),
                    width: 0.5,
                  )
                : null,
          ),
          child: Stack(
            children: [
              // Inner specular gradient (full panel)
              if (showHighlight)
                Positioned.fill(
                  child: IgnorePointer(
                    child: Container(
                      decoration: BoxDecoration(
                        borderRadius: borderRadius,
                        gradient: AwareGradients.glassHighlight,
                      ),
                    ),
                  ),
                ),
              // Top edge specular highlight (1px "light catch")
              // Crystal Era: stronger highlight for glass edge definition
              if (showHighlight)
                Positioned(
                  top: 0,
                  left: 0,
                  right: 0,
                  height: 1,
                  child: IgnorePointer(
                    child: Container(
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.only(
                          topLeft: borderRadius.topLeft,
                          topRight: borderRadius.topRight,
                        ),
                        gradient: LinearGradient(
                          colors: [
                            AwareColors.glassHighlight.withValues(alpha: 0.22),
                            AwareColors.glassHighlight.withValues(alpha: 0.08),
                            AwareColors.glassHighlight.withValues(alpha: 0.22),
                          ],
                          stops: const [0.0, 0.5, 1.0],
                        ),
                      ),
                    ),
                  ),
                ),
              // Inner top highlight gradient (subtle thickness)
              // Crystal Era: slightly deeper highlight for glass depth
              if (showHighlight)
                Positioned(
                  top: 1,
                  left: 1,
                  right: 1,
                  height: 40,
                  child: IgnorePointer(
                    child: Container(
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.only(
                          topLeft:
                              borderRadius.topLeft - const Radius.circular(1),
                          topRight:
                              borderRadius.topRight - const Radius.circular(1),
                        ),
                        gradient: LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: [
                            AwareColors.glassHighlight.withValues(alpha: 0.10),
                            AwareColors.glassHighlight.withValues(alpha: 0.0),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              // Corner bloom (for active state)
              if (showCornerBloom) ...[
                // Top-left bloom
                Positioned(
                  top: 0,
                  left: 0,
                  width: 60,
                  height: 60,
                  child: IgnorePointer(
                    child: Container(
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.only(
                          topLeft: borderRadius.topLeft,
                        ),
                        gradient: RadialGradient(
                          center: Alignment.topLeft,
                          radius: 1.5,
                          colors: [
                            AwareColors.brandPurple.withValues(alpha: 0.15),
                            AwareColors.brandPurple.withValues(alpha: 0.0),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
                // Top-right bloom
                Positioned(
                  top: 0,
                  right: 0,
                  width: 60,
                  height: 60,
                  child: IgnorePointer(
                    child: Container(
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.only(
                          topRight: borderRadius.topRight,
                        ),
                        gradient: RadialGradient(
                          center: Alignment.topRight,
                          radius: 1.5,
                          colors: [
                            AwareColors.brandBlue.withValues(alpha: 0.12),
                            AwareColors.brandBlue.withValues(alpha: 0.0),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ],
              // Content
              child,
            ],
          ),
        ),
      ),
    );
  }
}

/// Preset glass material variants for common use cases.
enum GlassMaterialVariant {
  /// Default smoked glass - dark, high blur
  smoked,

  /// Frost glass - lighter, medium blur
  frost,

  /// Deep space - very dark, subtle blur
  deepSpace,

  /// Inset glass - for elements inside a glass container
  inset,
}

/// Extension to create glass materials from variants.
extension GlassMaterialVariantExtension on GlassMaterialVariant {
  /// Get blur value for this variant
  double get blur => switch (this) {
    GlassMaterialVariant.smoked => 24.0,
    GlassMaterialVariant.frost => 18.0,
    GlassMaterialVariant.deepSpace => 12.0,
    GlassMaterialVariant.inset => 10.0,
  };

  /// Get tint opacity for this variant
  /// Crystal Era: reduced for lens clarity (see mesh through glass)
  double get tintOpacity => switch (this) {
    GlassMaterialVariant.smoked => 0.52, // Reduced from 0.65 - more clarity
    GlassMaterialVariant.frost => 0.48, // Reduced from 0.55
    GlassMaterialVariant.deepSpace => 0.72, // Reduced from 0.80
    GlassMaterialVariant.inset => 0.62, // Reduced from 0.70
  };

  /// Get tint color for this variant
  Color get tintColor => switch (this) {
    GlassMaterialVariant.smoked => AwareColors.glassDark,
    GlassMaterialVariant.frost => const Color(0xFF252525),
    GlassMaterialVariant.deepSpace => const Color(0xFF0A0A0A),
    GlassMaterialVariant.inset => const Color(0xFF1F1F1F),
  };
}

/// Glass surface role in the hierarchy.
/// Defines how glass behaves within the material layering.
enum GlassSurface {
  /// Gate card shell - thicker, more refractive
  panel,

  /// Content row inside a panel - pressed into glass
  inset,

  /// Small interactive element - button, badge
  chip,

  /// Ultra-transparent, nearly invisible glass
  /// Good for: overlays that integrate with background
  soft,
}

/// Extension for glass surface properties.
extension GlassSurfaceExtension on GlassSurface {
  /// Blur intensity for this surface role
  double get blur => switch (this) {
    GlassSurface.panel => 28.0, // Higher = more refractive
    GlassSurface.inset => 8.0, // Lower = pressed in
    GlassSurface.chip => 12.0, // Medium for buttons
    GlassSurface.soft => 6.0, // Very light blur
  };

  /// Tint opacity for this surface role
  double get tintOpacity => switch (this) {
    GlassSurface.panel => 0.60, // Lower = more see-through
    GlassSurface.inset => 0.75, // Higher = more solid
    GlassSurface.chip => 0.50, // Lighter for interaction
    GlassSurface.soft => 0.03, // Nearly invisible
  };

  /// Whether to show inner highlight
  bool get showHighlight => switch (this) {
    GlassSurface.panel => true,
    GlassSurface.inset => false,
    GlassSurface.chip => false,
    GlassSurface.soft => true, // Keep specular for depth
  };
}
