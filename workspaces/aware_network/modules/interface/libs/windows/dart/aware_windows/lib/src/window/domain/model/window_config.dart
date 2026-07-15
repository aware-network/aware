import 'package:freezed_annotation/freezed_annotation.dart';

part 'window_config.freezed.dart';
part 'window_config.g.dart';

/// Window layout modes
enum WindowLayoutMode { horizontal, vertical, grid, floating }

/// Window configuration for serializable layouts
@freezed
abstract class WindowConfig with _$WindowConfig {
  const WindowConfig._(); // Add private constructor for custom methods

  const factory WindowConfig({
    required String id,
    required String name,
    required WindowLayoutMode mode,
    required List<WindowSectionConfig> sections,
    required int version, // For future migrations
    DateTime? createdAt,
    DateTime? updatedAt,
    Map<String, dynamic>? metadata,
  }) = _WindowConfig;

  factory WindowConfig.fromJson(Map<String, dynamic> json) =>
      _$WindowConfigFromJson(json);
}

/// Window section configuration
@freezed
abstract class WindowSectionConfig with _$WindowSectionConfig {
  const WindowSectionConfig._(); // Add private constructor for custom methods

  const factory WindowSectionConfig({
    required String id,
    required String paneId,
    required double flex,
    @Default(false) bool collapsed,
    @Default(0.2) double minSize,
    @Default(0.8) double maxSize,
    Map<String, dynamic>? paneConfig, // Pane-specific config
  }) = _WindowSectionConfig;

  factory WindowSectionConfig.fromJson(Map<String, dynamic> json) =>
      _$WindowSectionConfigFromJson(json);
}
