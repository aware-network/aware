import 'pane_manifest_contract.dart';
import 'pane_selection_handler.dart';

/// Standard metadata keys used when dispatching pane selection events.
class PaneSelectionMetadataKeys {
  PaneSelectionMetadataKeys._();

  static const threadId = 'threadId';
  static const processId = 'processId';
  static const branchId = 'branchId';
  static const paneInstanceId = 'paneInstanceId';
  static const origin = 'origin';
}

/// Helper for composing metadata maps for [PaneSelectionHandler] payloads.
class PaneSelectionMetadataBuilder {
  PaneSelectionMetadataBuilder._();

  static Map<String, Object?> compose({
    String? threadId,
    String? processId,
    String? branchId,
    String? paneInstanceId,
    String? origin,
    Map<String, Object?>? extras,
  }) {
    final metadata = <String, Object?>{};
    if (threadId != null) {
      metadata[PaneSelectionMetadataKeys.threadId] = threadId;
    }
    if (processId != null) {
      metadata[PaneSelectionMetadataKeys.processId] = processId;
    }
    if (branchId != null) {
      metadata[PaneSelectionMetadataKeys.branchId] = branchId;
    }
    if (paneInstanceId != null) {
      metadata[PaneSelectionMetadataKeys.paneInstanceId] = paneInstanceId;
    }
    if (origin != null) {
      metadata[PaneSelectionMetadataKeys.origin] = origin;
    }
    if (extras != null && extras.isNotEmpty) {
      metadata.addAll(extras);
    }
    return metadata;
  }
}

/// Metadata keys for [PaneBranchContext] entries passed to manifest adapters.
class PaneManifestMetadataKeys {
  PaneManifestMetadataKeys._();

  static const threadDirectory = 'threadDirectory';
  static const threadSnapshot = 'threadSnapshot';
  static const branch = 'branch';
}

/// Helper for composing metadata maps for [PaneBranchContext].
class PaneManifestMetadataBuilder {
  PaneManifestMetadataBuilder._();

  static Map<String, Object?> compose({
    String? threadDirectory,
    Object? threadSnapshot,
    Object? branch,
    Map<String, Object?>? extras,
  }) {
    final metadata = <String, Object?>{};
    if (threadDirectory != null) {
      metadata[PaneManifestMetadataKeys.threadDirectory] = threadDirectory;
    }
    if (threadSnapshot != null) {
      metadata[PaneManifestMetadataKeys.threadSnapshot] = threadSnapshot;
    }
    if (branch != null) {
      metadata[PaneManifestMetadataKeys.branch] = branch;
    }
    if (extras != null && extras.isNotEmpty) {
      metadata.addAll(extras);
    }
    return metadata;
  }
}
