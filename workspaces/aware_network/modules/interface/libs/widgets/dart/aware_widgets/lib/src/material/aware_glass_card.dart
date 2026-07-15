import 'dart:ui';

import 'package:flutter/material.dart';

import '../kinematics/glass_kinematics.dart';
import '../kinematics/kinematic_glass.dart';
import '../tokens/aware_colors.dart';
import '../tokens/aware_gradients.dart';
import '../tokens/aware_shadows.dart';
import 'aware_glass_material.dart';

/// State of a glass card (gate).
enum GlassCardState {
  /// Locked - not yet accessible, dimmed
  locked,

  /// Active - currently focused, glowing
  active,

  /// Crossed - completed, subtle success indicator
  crossed,
}

/// A glass card with state-based styling for gates.
///
/// Three states:
/// - **locked**: Flatter, less blur, less glow - pending
/// - **active**: Full opacity, purple/blue halo glow + inner highlight
/// - **crossed**: Settled, subtle green glow, verified
///
/// Design principle: Each gate is a "crystal lens" you cross through.
/// Material feels like glass with depth, not just an opacity layer.
class AwareGlassCard extends StatelessWidget {
  const AwareGlassCard({
    super.key,
    required this.child,
    this.state = GlassCardState.active,
    this.variant = GlassMaterialVariant.smoked,
    this.borderRadius = const BorderRadius.all(Radius.circular(20)),
    this.padding = const EdgeInsets.all(20),
    this.onTap,
    this.kinematicPreset = GlassKinematicPreset.interactive,
    this.autoSettle = true,
  });

  /// Content of the glass card
  final Widget child;

  /// Current state of the card
  final GlassCardState state;

  /// Glass material variant
  final GlassMaterialVariant variant;

  /// Border radius
  final BorderRadius borderRadius;

  /// Inner padding
  final EdgeInsets padding;

  /// Tap callback
  final VoidCallback? onTap;

  /// Kinematic behavior preset.
  /// - [GlassKinematicPreset.interactive]: breathing + settling + touch (default)
  /// - [GlassKinematicPreset.responsive]: touch response only
  /// - [GlassKinematicPreset.none]: no kinematics
  final GlassKinematicPreset kinematicPreset;

  /// Whether to auto-trigger settling animation on mount.
  /// Set to false if using with cinematic (cinematic controls reveal timing).
  final bool autoSettle;

  @override
  Widget build(BuildContext context) {
    final shadows = _getShadows();
    final showGradientBorder = state == GlassCardState.active;

    // State-based material properties
    final effectiveBlur = _getEffectiveBlur();
    final effectiveOpacity = _getEffectiveOpacity();

    Widget card = AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeOutCubic,
      decoration: BoxDecoration(
        borderRadius: borderRadius.add(
          const BorderRadius.all(Radius.circular(2)),
        ),
        boxShadow: shadows,
      ),
      child: showGradientBorder
          ? _buildGradientBorderCard(effectiveBlur, effectiveOpacity)
          : _buildSimpleCard(effectiveBlur, effectiveOpacity),
    );

    // Apply locked dim effect
    if (state == GlassCardState.locked) {
      card = AnimatedOpacity(
        duration: const Duration(milliseconds: 300),
        opacity: 0.6,
        child: card,
      );
    }

    // Always wrap with KinematicGlass for full glass experience:
    // - Settling: spring physics on entry (Pixar-style landing)
    // - Breathing: subtle life while visible
    // - Response: satisfying touch feedback
    final effectiveResponse = onTap == null
        ? GlassResponse.none
        : (state == GlassCardState.active
              ? GlassResponse.standard
              : GlassResponse.subtle);

    card = KinematicGlass(
      preset: kinematicPreset,
      response: effectiveResponse,
      onTap: onTap,
      autoSettle: autoSettle,
      child: card,
    );

    return card;
  }

  /// Locked state = flatter (less blur). Active = more refractive.
  double _getEffectiveBlur() {
    return switch (state) {
      GlassCardState.locked => variant.blur * 0.5, // Flatter
      GlassCardState.active => variant.blur * 1.2, // More refractive
      GlassCardState.crossed => variant.blur, // Normal
    };
  }

  /// Locked state = more opaque. Active = slightly more transparent (glass-like).
  double _getEffectiveOpacity() {
    return switch (state) {
      GlassCardState.locked => variant.tintOpacity + 0.1, // More solid
      GlassCardState.active => variant.tintOpacity - 0.05, // More glass-like
      GlassCardState.crossed => variant.tintOpacity, // Normal
    };
  }

  List<BoxShadow> _getShadows() {
    return switch (state) {
      // Locked: minimal shadow, no glow
      GlassCardState.locked => [
        BoxShadow(
          color: Colors.black.withValues(alpha: 0.15),
          blurRadius: 16,
          offset: const Offset(0, 4),
        ),
      ],
      // Active: elevated + halo glow
      GlassCardState.active => AwareShadows.withGlow(
        AwareShadows.glassCardElevated,
        AwareShadows.activeGlow,
      ),
      // Crossed: normal shadow + subtle green glow
      GlassCardState.crossed => AwareShadows.withGlow(
        AwareShadows.glassCard,
        AwareShadows.crossedGlow,
      ),
    };
  }

  Widget _buildGradientBorderCard(double blur, double opacity) {
    return Container(
      decoration: BoxDecoration(
        gradient: AwareGradients.activeBorder,
        borderRadius: borderRadius.add(
          const BorderRadius.all(Radius.circular(2)),
        ),
      ),
      padding: const EdgeInsets.all(2), // Gradient border thickness
      child: _buildGlassContent(blur, opacity, showHighlight: true),
    );
  }

  Widget _buildSimpleCard(double blur, double opacity) {
    final borderColor = switch (state) {
      GlassCardState.locked => AwareColors.neutral.withValues(alpha: 0.15),
      GlassCardState.crossed => AwareColors.success.withValues(alpha: 0.25),
      GlassCardState.active => Colors.transparent,
    };

    return Container(
      decoration: BoxDecoration(
        borderRadius: borderRadius,
        border: Border.all(color: borderColor, width: 1),
      ),
      child: _buildGlassContent(
        blur,
        opacity,
        showHighlight: state != GlassCardState.locked,
      ),
    );
  }

  Widget _buildGlassContent(
    double blur,
    double opacity, {
    bool showHighlight = true,
  }) {
    return AwareGlassMaterial(
      blur: blur,
      tintColor: variant.tintColor,
      tintOpacity: opacity,
      borderRadius: borderRadius,
      showBorder: state != GlassCardState.active,
      showHighlight: showHighlight,
      child: Padding(padding: padding, child: child),
    );
  }
}

/// Header for a glass card with icon and title.
///
/// Supports an optional inline status indicator (statusLabel + statusColor)
/// shown to the right of the title area, before the state indicator.
class GlassCardHeader extends StatelessWidget {
  const GlassCardHeader({
    super.key,
    required this.title,
    this.subtitle,
    this.icon,
    this.iconColor,
    this.trailing,
    this.state = GlassCardState.active,
    this.statusLabel,
    this.statusColor,
  });

  final String title;
  final String? subtitle;
  final IconData? icon;

  /// Optional icon color override. If null, derives from state.
  final Color? iconColor;

  final Widget? trailing;
  final GlassCardState state;

  /// Inline status label (e.g., "Signup required", "Checking membership...")
  final String? statusLabel;

  /// Status indicator color (defaults to warning orange if not provided)
  final Color? statusColor;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    final effectiveIconColor =
        iconColor ??
        switch (state) {
          GlassCardState.locked => AwareColors.neutral,
          GlassCardState.active => AwareColors.brandPurple,
          GlassCardState.crossed => AwareColors.success,
        };

    return Row(
      children: [
        if (icon != null) ...[
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: effectiveIconColor.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: effectiveIconColor, size: 24),
          ),
          const SizedBox(width: 14),
        ],
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w700,
                  // Crossed needs to stay legible vs active "You" card
                  color: switch (state) {
                    GlassCardState.locked =>
                      theme.colorScheme.onSurface.withValues(alpha: 0.5),
                    GlassCardState.crossed => Colors.white.withValues(
                      alpha: 0.88,
                    ), // Brighter
                    GlassCardState.active => Colors.white, // Full brightness
                  },
                ),
              ),
              if (subtitle != null) ...[
                const SizedBox(height: 2),
                Text(
                  subtitle!,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                  ),
                ),
              ],
            ],
          ),
        ),
        // Inline status indicator (before trailing/state)
        if (statusLabel != null) ...[
          const SizedBox(width: 8),
          Flexible(
            child: _InlineStatusIndicator(
              label: statusLabel!,
              color: statusColor ?? AwareColors.warning,
            ),
          ),
          const SizedBox(width: 8),
        ],
        if (trailing != null) trailing!,
        // State indicator
        if (state == GlassCardState.crossed) ...[
          const SizedBox(width: 8),
          Container(
            width: 24,
            height: 24,
            decoration: const BoxDecoration(
              color: AwareColors.success,
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.check, color: Colors.white, size: 16),
          ),
        ],
        if (state == GlassCardState.locked) ...[
          const SizedBox(width: 8),
          Icon(
            Icons.lock_outline,
            color: AwareColors.neutral.withValues(alpha: 0.5),
            size: 20,
          ),
        ],
      ],
    );
  }
}

/// Status indicator chip - prominent, crystal-styled action prompt.
/// Must be clearly visible to communicate next required action.
class _InlineStatusIndicator extends StatelessWidget {
  const _InlineStatusIndicator({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        // Glass chip background
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.4), width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Glowing dot
          Container(
            width: 6,
            height: 6,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: color,
              boxShadow: [
                BoxShadow(
                  color: color.withValues(alpha: 0.6),
                  blurRadius: 4,
                  spreadRadius: 1,
                ),
              ],
            ),
          ),
          const SizedBox(width: 6),
          // Label - compact but readable
          Flexible(
            child: Text(
              label,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: Colors.white.withValues(alpha: 0.95),
                fontWeight: FontWeight.w600,
                letterSpacing: 0.2,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}

/// Inset glass container for content inside a glass card.
/// Feels "pressed into" the parent glass - less blur, more solid.
class GlassInset extends StatelessWidget {
  const GlassInset({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
    this.borderRadius = const BorderRadius.all(Radius.circular(12)),
    this.minHeight = 44.0, // Minimum touch target
  });

  final Widget child;
  final EdgeInsets padding;
  final BorderRadius borderRadius;
  final double minHeight;

  @override
  Widget build(BuildContext context) {
    return AwareGlassMaterial(
      blur: GlassSurface.inset.blur,
      tintColor: GlassMaterialVariant.inset.tintColor,
      tintOpacity: GlassSurface.inset.tintOpacity,
      borderRadius: borderRadius,
      showHighlight: false,
      showBorder: false,
      child: ConstrainedBox(
        constraints: BoxConstraints(minHeight: minHeight),
        child: Padding(padding: padding, child: child),
      ),
    );
  }
}

/// Toggle control for expandable sections (Show Details).
/// 44px minimum tap target, proper semantics, subtle glass effect.
class GlassToggleControl extends StatelessWidget {
  const GlassToggleControl({
    super.key,
    required this.expanded,
    required this.onToggle,
    this.expandedLabel = 'Hide Details',
    this.collapsedLabel = 'Show Details',
  });

  final bool expanded;
  final VoidCallback onToggle;
  final String expandedLabel;
  final String collapsedLabel;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      toggled: expanded,
      label: expanded ? expandedLabel : collapsedLabel,
      child: Material(
        type: MaterialType.transparency,
        child: InkWell(
          onTap: onToggle,
          borderRadius: BorderRadius.circular(8),
          splashColor: Colors.white.withValues(alpha: 0.1),
          highlightColor: Colors.white.withValues(alpha: 0.05),
          child: ConstrainedBox(
            constraints: const BoxConstraints(minHeight: 44),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                mainAxisSize: MainAxisSize.min,
                children: [
                  AnimatedRotation(
                    turns: expanded ? 0.5 : 0,
                    duration: const Duration(milliseconds: 200),
                    child: Icon(
                      Icons.keyboard_arrow_down,
                      size: 18,
                      color: Colors.white.withValues(alpha: 0.5),
                    ),
                  ),
                  const SizedBox(width: 4),
                  Text(
                    expanded ? expandedLabel : collapsedLabel,
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: Colors.white.withValues(alpha: 0.5),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Expandable section with smooth AnimatedSize + Opacity animation.
/// Replaces AnimatedCrossFade for smoother "glass" feel.
class GlassExpandable extends StatelessWidget {
  const GlassExpandable({
    super.key,
    required this.expanded,
    required this.child,
    this.duration = const Duration(milliseconds: 250),
    this.curve = Curves.easeOutCubic,
  });

  final bool expanded;
  final Widget child;
  final Duration duration;
  final Curve curve;

  @override
  Widget build(BuildContext context) {
    return AnimatedSize(
      duration: duration,
      curve: curve,
      alignment: Alignment.topCenter,
      child: AnimatedOpacity(
        duration: duration,
        opacity: expanded ? 1.0 : 0.0,
        child: expanded
            ? Padding(padding: const EdgeInsets.only(top: 8), child: child)
            : const SizedBox.shrink(),
      ),
    );
  }
}

/// Hero primary action button for glass cards.
///
/// Large, centered, unmissable CTA for gates.
/// Use this when the user MUST take action (signup, subscribe, enter).
///
/// NOTE: Consider using [GlassActionButton] for glass-over-glass design.
class GlassPrimaryAction extends StatelessWidget {
  const GlassPrimaryAction({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.loading = false,
  });

  /// Button label (e.g., "Sign Up", "Subscribe", "Enter Territory")
  final String label;

  /// Called when button is pressed
  final VoidCallback onPressed;

  /// Optional leading icon
  final IconData? icon;

  /// Show loading spinner instead of content
  final bool loading;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(minWidth: 200, minHeight: 52),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: loading ? null : onPressed,
            borderRadius: BorderRadius.circular(14),
            splashColor: Colors.white.withValues(alpha: 0.2),
            highlightColor: Colors.white.withValues(alpha: 0.1),
            child: Ink(
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AwareColors.brandPurple, AwareColors.brandBlue],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(14),
                boxShadow: [
                  BoxShadow(
                    color: AwareColors.brandPurple.withValues(alpha: 0.4),
                    blurRadius: 16,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 32,
                  vertical: 14,
                ),
                child: loading
                    ? const SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(
                            Colors.white,
                          ),
                        ),
                      )
                    : Row(
                        mainAxisSize: MainAxisSize.min,
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          if (icon != null) ...[
                            Icon(icon, color: Colors.white, size: 20),
                            const SizedBox(width: 10),
                          ],
                          Text(
                            label,
                            style: Theme.of(context).textTheme.titleMedium
                                ?.copyWith(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w600,
                                  letterSpacing: 0.5,
                                ),
                          ),
                        ],
                      ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Glass-styled action button for glass-over-glass design.
///
/// Uses glass material with gradient border (not solid fill).
/// Feels like pressing INTO glass, not clicking a solid button.
///
/// Design: Glass chip surface + gradient border + subtle glow.
/// Liquid treatment: specular sweep on appear + swell on press.
class GlassActionButton extends StatefulWidget {
  const GlassActionButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.loading = false,
    this.animateLoading = true,
    this.accentColor,
  });

  /// Button label
  final String label;

  /// Called when button is pressed
  final VoidCallback onPressed;

  /// Optional leading icon
  final IconData? icon;

  /// Show loading spinner instead of content
  final bool loading;

  /// Whether the loading indicator should animate.
  ///
  /// When `false`, a static activity indicator is rendered to avoid continuous
  /// frame scheduling (useful for long-running states like network retries).
  ///
  /// Note: Reduced-motion (`MediaQuery.disableAnimations`) will disable loading
  /// animation regardless of this setting.
  final bool animateLoading;

  /// Optional accent color (defaults to brand purple/blue gradient)
  final Color? accentColor;

  @override
  State<GlassActionButton> createState() => _GlassActionButtonState();
}

class _GlassActionButtonState extends State<GlassActionButton>
    with TickerProviderStateMixin {
  late AnimationController _sweepController;
  late AnimationController _pressController;
  late Animation<double> _sweepAnimation;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    // Specular sweep on appear (once, 500ms)
    _sweepController = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );
    _sweepAnimation = CurvedAnimation(
      parent: _sweepController,
      curve: Curves.easeOut,
    );

    // Swell on press (spring physics)
    _pressController = AnimationController(
      duration: const Duration(milliseconds: 150),
      vsync: this,
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.04).animate(
      CurvedAnimation(parent: _pressController, curve: Curves.easeOutCubic),
    );

    // Trigger sweep after short delay
    Future.delayed(const Duration(milliseconds: 300), () {
      if (mounted) _sweepController.forward();
    });
  }

  @override
  void dispose() {
    _sweepController.dispose();
    _pressController.dispose();
    super.dispose();
  }

  void _onTapDown(TapDownDetails details) {
    _pressController.forward();
  }

  void _onTapUp(TapUpDetails details) {
    _pressController.reverse();
    if (!widget.loading) widget.onPressed();
  }

  void _onTapCancel() {
    _pressController.reverse();
  }

  @override
  Widget build(BuildContext context) {
    final disableAnimations =
        MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    final animateLoading = widget.animateLoading && !disableAnimations;

    final content = widget.loading
        ? (animateLoading
              ? const SizedBox(
                  width: 24,
                  height: 24,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  ),
                )
              : const SizedBox(
                  width: 24,
                  height: 24,
                  child: CircularProgressIndicator(
                    value: 0.75,
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  ),
                ))
        : Row(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (widget.icon != null) ...[
                Icon(widget.icon, color: Colors.white, size: 22),
                const SizedBox(width: 12),
              ],
              Text(
                widget.label,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 0.5,
                ),
              ),
            ],
          );

    return AnimatedBuilder(
      animation: Listenable.merge([_scaleAnimation, _sweepAnimation]),
      builder: (context, _) {
        return Transform.scale(
          scale: _scaleAnimation.value,
          child: GestureDetector(
            onTapDown: _onTapDown,
            onTapUp: _onTapUp,
            onTapCancel: _onTapCancel,
            child: Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(16),
                // Outer glow for presence
                boxShadow: [
                  BoxShadow(
                    color: AwareColors.brandPurple.withValues(alpha: 0.4),
                    blurRadius: 20,
                  ),
                  BoxShadow(
                    color: AwareColors.brandBlue.withValues(alpha: 0.25),
                    blurRadius: 28,
                    spreadRadius: 2,
                  ),
                ],
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: BackdropFilter.grouped(
                  filter: ImageFilter.blur(sigmaX: 4, sigmaY: 4),
                  child: Stack(
                    children: [
                      // Gradient core
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 32,
                          vertical: 16,
                        ),
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [
                              AwareColors.brandPurple,
                              AwareColors.brandBlue,
                            ],
                            begin: Alignment.centerLeft,
                            end: Alignment.centerRight,
                          ),
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: content,
                      ),
                      // Specular sweep
                      if (_sweepController.value < 1.0)
                        Positioned.fill(
                          child: IgnorePointer(
                            child: CustomPaint(
                              painter: _ButtonSpecularSweepPainter(
                                progress: _sweepAnimation.value,
                              ),
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}

/// Paints the specular sweep across the button.
class _ButtonSpecularSweepPainter extends CustomPainter {
  final double progress;

  _ButtonSpecularSweepPainter({required this.progress});

  @override
  void paint(Canvas canvas, Size size) {
    if (progress >= 1.0 || progress <= 0.0) return;

    final sweepWidth = size.width * 0.4;
    final position = progress * (size.width + sweepWidth) - sweepWidth / 2;

    final paint = Paint()
      ..shader =
          LinearGradient(
            colors: [
              Colors.transparent,
              Colors.white.withValues(alpha: 0.35 * (1 - progress)),
              Colors.white.withValues(alpha: 0.5 * (1 - progress)),
              Colors.white.withValues(alpha: 0.35 * (1 - progress)),
              Colors.transparent,
            ],
            stops: const [0.0, 0.25, 0.5, 0.75, 1.0],
          ).createShader(
            Rect.fromLTWH(
              position - sweepWidth / 2,
              0,
              sweepWidth,
              size.height,
            ),
          );

    final rect = RRect.fromRectAndRadius(
      Rect.fromLTWH(0, 0, size.width, size.height),
      const Radius.circular(12.5),
    );

    canvas.save();
    canvas.clipRRect(rect);
    canvas.drawRect(
      Rect.fromLTWH(position - sweepWidth / 2, 0, sweepWidth, size.height),
      paint,
    );
    canvas.restore();
  }

  @override
  bool shouldRepaint(_ButtonSpecularSweepPainter oldDelegate) =>
      oldDelegate.progress != progress;
}
