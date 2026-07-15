import 'package:flutter/material.dart';

class WindowPalette {
  final Color background;
  final Color card;
  final Color divider;
  final Color border;
  final Color primary;
  final Color text;
  final Color mutedText;

  const WindowPalette({
    required this.background,
    required this.card,
    required this.divider,
    required this.border,
    required this.primary,
    required this.text,
    required this.mutedText,
  });

  factory WindowPalette.fromTheme(ThemeData theme) {
    final colorScheme = theme.colorScheme;
    final baseText =
        theme.textTheme.bodyMedium?.color ?? colorScheme.onBackground;
    return WindowPalette(
      background: theme.scaffoldBackgroundColor,
      card: theme.cardColor,
      divider: theme.dividerColor,
      border: theme.dividerColor,
      primary: colorScheme.primary,
      text: baseText,
      mutedText: baseText.withValues(alpha: 0.6),
    );
  }
}
