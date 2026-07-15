import 'package:meta/meta.dart';

enum PaneMaterializationMode { fileSystem, commits }

@immutable
class PaneMaterializationModeParseResult {
  const PaneMaterializationModeParseResult({
    required this.mode,
    this.source,
    this.error,
  });

  final PaneMaterializationMode? mode;
  final String? source;
  final String? error;

  bool get isValid => mode != null && error == null;
}

extension PaneMaterializationModeUtils on PaneMaterializationMode {
  static PaneMaterializationModeParseResult fromString(String? raw) {
    if (raw == null || raw.trim().isEmpty) {
      return const PaneMaterializationModeParseResult(mode: null);
    }

    final normalized = raw.trim().toLowerCase();
    switch (normalized) {
      case 'filesystem':
      case 'file_system':
      case 'fs':
        return PaneMaterializationModeParseResult(
          mode: PaneMaterializationMode.fileSystem,
          source: raw,
        );
      case 'commits':
      case 'commit':
      case 'network':
        return PaneMaterializationModeParseResult(
          mode: PaneMaterializationMode.commits,
          source: raw,
        );
      default:
        return PaneMaterializationModeParseResult(
          mode: null,
          source: raw,
          error: 'Unsupported pane materialization mode "${raw}".',
        );
    }
  }

  String get label {
    switch (this) {
      case PaneMaterializationMode.fileSystem:
        return 'filesystem';
      case PaneMaterializationMode.commits:
        return 'commits';
    }
  }
}
