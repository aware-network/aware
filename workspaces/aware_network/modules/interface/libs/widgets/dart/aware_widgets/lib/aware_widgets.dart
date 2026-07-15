/// AWARE Widgets - Shared UI components and design tokens.
///
/// This package provides the foundational visual language for AWARE:
/// - Glass materials (blur, tint, highlights)
/// - Design tokens (colors, shadows, gradients)
/// - Common widgets used across modules
///
/// Module-agnostic: can be imported by any module representation.
library aware_widgets;

// Design tokens
export 'src/tokens/aware_colors.dart';
export 'src/tokens/aware_shadows.dart';
export 'src/tokens/aware_gradients.dart';
export 'src/tokens/aware_motion.dart';

// Materials
export 'src/material/aware_glass_material.dart';
export 'src/material/aware_glass_card.dart';
export 'src/material/aware_glass_pane.dart';

// Kinematics
export 'src/kinematics/glass_kinematics.dart';
export 'src/kinematics/glass_field.dart';
export 'src/kinematics/kinematic_glass.dart';

// Layout (AWARE standard)
export 'src/layout/glass_layout.dart';
export 'src/layout/glass_layout_physics.dart';

// Diagnostics
export 'src/diagnostics/glass_ticker_diagnostics.dart';
