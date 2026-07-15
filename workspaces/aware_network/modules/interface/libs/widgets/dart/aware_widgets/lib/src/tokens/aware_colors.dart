import 'package:flutter/material.dart';

/// AWARE brand colors and semantic color tokens.
///
/// Design principle: Color is reserved for intent.
/// Most UI is neutral glass. Color appears only where meaning exists:
/// - Primary action
/// - Current/active step
/// - Success/verified
/// - Authority/selection
abstract final class AwareColors {
  // ============================================
  // Canonical Aware Network Brand Palette
  // ============================================
  //
  // These are the public-facing brand colors used by the live Aware Network
  // entrance (`aware.run/`) and the post-admission atrium (Control's
  // coordination_center). They flow from the Aware logo gradient.
  //
  // Surfaces inside the atrium use these as role tokens:
  //   Identity (admission, presence)        → cyan
  //   Hub Map (the network's public packages) → violet
  //   Connection (your link to the network) → pink
  //
  // Agents (later TBD) reserve a red/pink hue distinct from `pink`.

  /// Aware cyan — entrance, Identity role, "you are entering".
  static const Color cyan = Color(0xFF38C6FF);

  /// Aware violet — brand center, Hub Map role.
  static const Color violet = Color(0xFF8B6FFF);

  /// Aware pink — Connection / link edge role.
  static const Color pink = Color(0xFFFF6FA8);

  // ============================================
  // Semantic Role Tokens
  // ============================================

  /// Identity / admission / "you are here" role.
  static const Color identityRole = cyan;

  /// Hub / Map / "what is here" role.
  static const Color hubRole = violet;

  /// Connection / Link / "your link to the network" role.
  static const Color connectionRole = pink;

  // ============================================
  // Brand Colors (legacy aliases)
  // ============================================
  //
  // Existing internal surfaces (glass cards, IDE workbench, etc.) still
  // reference these names. New public-facing code should prefer
  // `cyan/violet/pink` or the role tokens above.

  /// Primary blue - trust, connection
  static const Color brandBlue = Color(0xFF2563EB);

  /// Primary purple - intelligence, protocol
  static const Color brandPurple = Color(0xFF7C3AED);

  /// Accent gold - value, achievement
  static const Color brandGold = Color(0xFFF59E0B);

  // ============================================
  // Semantic Colors
  // ============================================

  /// Success/verified - crossed gates, completed actions
  static const Color success = Color(0xFF10B981);

  /// Error/failed - blocked gates, errors
  static const Color error = Color(0xFFDC2626);

  /// Warning/pending - attention needed
  static const Color warning = Color(0xFFF59E0B);

  /// Neutral/inactive - pending, locked
  static const Color neutral = Color(0xFF6B7280);

  // ============================================
  // Glass Material Colors
  // ============================================

  /// Dark glass tint - for dark theme panels
  static const Color glassDark = Color(0xFF1A1A1A);

  /// Light glass tint - for light theme panels
  static const Color glassLight = Color(0xFFF5F5F5);

  /// Inner highlight color - top edge of glass
  static const Color glassHighlight = Color(0xFFFFFFFF);

  /// Glass border color - subtle edge definition
  static const Color glassBorder = Color(0xFF3F3F46);

  /// Surface dark - background for dark mode panes
  static const Color surfaceDark = Color(0xFF0F0F0F);

  // ============================================
  // State Colors
  // ============================================

  /// Active state - glowing, focused
  static Color get activeGlow => brandPurple.withValues(alpha: 0.4);

  /// Crossed/completed state - subtle success
  static Color get crossedGlow => success.withValues(alpha: 0.2);

  /// Locked state - dimmed
  static Color get lockedOverlay => Colors.black.withValues(alpha: 0.3);
}
