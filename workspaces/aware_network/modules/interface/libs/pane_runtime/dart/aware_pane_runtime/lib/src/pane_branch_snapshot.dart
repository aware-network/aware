import 'package:uuid/uuid_value.dart';

import 'pane_kind.dart';

/// Lightweight representation of a pane branch that avoids depending on host
/// persistence models. Hosts can attach additional data in [metadata] and
/// provide codecs to convert to their native structures.
class PaneBranchSnapshot {
  const PaneBranchSnapshot({
    required this.branchId,
    required this.paneKind,
    required this.name,
    required this.isMain,
    required this.createdAt,
    required this.updatedAt,
    this.metadata = const <String, Object?>{},
  });

  final UuidValue branchId;
  final PaneKey paneKind;
  final String name;
  final bool isMain;
  final DateTime createdAt;
  final DateTime updatedAt;
  final Map<String, Object?> metadata;

  PaneBranchSnapshot copyWith({
    UuidValue? branchId,
    PaneKey? paneKind,
    String? name,
    bool? isMain,
    DateTime? createdAt,
    DateTime? updatedAt,
    Map<String, Object?>? metadata,
  }) {
    return PaneBranchSnapshot(
      branchId: branchId ?? this.branchId,
      paneKind: paneKind ?? this.paneKind,
      name: name ?? this.name,
      isMain: isMain ?? this.isMain,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      metadata: metadata ?? this.metadata,
    );
  }
}
