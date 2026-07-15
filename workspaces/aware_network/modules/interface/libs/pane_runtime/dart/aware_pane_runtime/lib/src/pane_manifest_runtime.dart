import 'package:uuid/uuid_value.dart';

import 'pane_kind.dart';
import 'pane_branch_snapshot.dart';

class PaneThreadSnapshot {
  const PaneThreadSnapshot({
    required this.id,
    required this.title,
    required this.createdAt,
    required this.updatedAt,
  });

  final UuidValue id;
  final String? title;
  final DateTime createdAt;
  final DateTime? updatedAt;
}

abstract class PaneContextIdentifiable {
  String get paneContextKey;
}

class PaneManifestBundle<TPayload> {
  PaneManifestBundle({
    required this.branchSnapshot,
    required this.payload,
    this.manifestHash,
  });

  final PaneBranchSnapshot branchSnapshot;
  final TPayload payload;
  final String? manifestHash;

  String get contextKey {
    final value = payload;
    if (value is PaneContextIdentifiable) {
      final key = value.paneContextKey.trim();
      if (key.isNotEmpty) {
        return key;
      }
    }
    return branchSnapshot.branchId.toString();
  }
}

class SyntheticLaneBootstrap {
  const SyntheticLaneBootstrap({
    required this.threadId,
    required this.branchId,
    required this.objectInstanceGraphId,
    required this.paneKind,
    required this.opgName,
    required this.projectionHash,
  });

  final UuidValue threadId;
  final UuidValue branchId;
  final UuidValue objectInstanceGraphId;
  final PaneKey paneKind;
  final String opgName;
  final String projectionHash;
}
