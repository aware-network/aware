import 'package:uuid/uuid_value.dart';

import 'pane_branch_snapshot.dart';
import 'pane_kind.dart';

class BranchManifestRecord {
  BranchManifestRecord({
    required this.branchId,
    required this.paneKind,
    required this.name,
    required this.isMain,
    required this.createdAt,
    required this.updatedAt,
    this.headCommitId,
    this.objectInstanceGraphId,
    this.threadBranchId,
    this.threadId,
    Map<String, Object?>? metadata,
  }) : metadata = Map.unmodifiable(
         metadata == null ? const {} : Map<String, Object?>.from(metadata),
       );

  final UuidValue branchId;
  final PaneKey paneKind;
  final String name;
  final bool isMain;
  final DateTime createdAt;
  final DateTime updatedAt;
  final UuidValue? headCommitId;
  final UuidValue? objectInstanceGraphId;
  final UuidValue? threadBranchId;
  final UuidValue? threadId;
  final Map<String, Object?> metadata;

  Map<String, dynamic> toJson() {
    final result = <String, dynamic>{
      'branch_id': branchId.toString(),
      'pane_kind': paneKind.name,
      'name': name,
      'is_main': isMain,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
      if (headCommitId != null) 'head_commit_id': headCommitId.toString(),
      if (objectInstanceGraphId != null)
        'object_instance_graph_id': objectInstanceGraphId.toString(),
      if (threadBranchId != null) 'thread_branch_id': threadBranchId.toString(),
      if (threadId != null) 'thread_id': threadId.toString(),
    };
    if (metadata.isNotEmpty) {
      result['metadata'] = metadata;
    }
    return result;
  }

  factory BranchManifestRecord.fromJson(Map<String, dynamic> json) {
    final metadata = (json['metadata'] as Map?)?.cast<String, Object?>();
    final rawPaneKey =
        json['pane_key'] ?? json['pane_kind'] ?? json['paneKind'];
    final paneKey = rawPaneKey is String && rawPaneKey.trim().isNotEmpty
        ? rawPaneKey
        : kPaneKeyGeneric;
    return BranchManifestRecord(
      branchId: UuidValue.fromString(json['branch_id'] as String),
      paneKind: paneKey,
      name: json['name'] as String? ?? 'Branch',
      isMain: json['is_main'] as bool? ?? true,
      createdAt: DateTime.parse(json['created_at'] as String).toUtc(),
      updatedAt: DateTime.parse(json['updated_at'] as String).toUtc(),
      headCommitId: (json['head_commit_id'] as String?) != null
          ? UuidValue.fromString(json['head_commit_id'] as String)
          : null,
      objectInstanceGraphId:
          (json['object_instance_graph_id'] as String?) != null
          ? UuidValue.fromString(json['object_instance_graph_id'] as String)
          : null,
      threadBranchId: (json['thread_branch_id'] as String?) != null
          ? UuidValue.fromString(json['thread_branch_id'] as String)
          : null,
      threadId: (json['thread_id'] as String?) != null
          ? UuidValue.fromString(json['thread_id'] as String)
          : null,
      metadata: metadata,
    );
  }

  PaneBranchSnapshot toSnapshot({
    Map<String, Object?> additionalMetadata = const {},
  }) {
    return PaneBranchSnapshot(
      branchId: branchId,
      paneKind: paneKind,
      name: name,
      isMain: isMain,
      createdAt: createdAt,
      updatedAt: updatedAt,
      metadata: {...metadata, ...additionalMetadata},
    );
  }

  factory BranchManifestRecord.fromSnapshot(PaneBranchSnapshot snapshot) {
    return BranchManifestRecord(
      branchId: snapshot.branchId,
      paneKind: snapshot.paneKind,
      name: snapshot.name,
      isMain: snapshot.isMain,
      createdAt: snapshot.createdAt,
      updatedAt: snapshot.updatedAt,
      metadata: snapshot.metadata,
    );
  }

  BranchManifestRecord copyWith({
    UuidValue? branchId,
    PaneKey? paneKind,
    String? name,
    bool? isMain,
    DateTime? createdAt,
    DateTime? updatedAt,
    UuidValue? headCommitId,
    UuidValue? objectInstanceGraphId,
    UuidValue? threadBranchId,
    UuidValue? threadId,
    Map<String, Object?>? metadata,
  }) {
    return BranchManifestRecord(
      branchId: branchId ?? this.branchId,
      paneKind: paneKind ?? this.paneKind,
      name: name ?? this.name,
      isMain: isMain ?? this.isMain,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      headCommitId: headCommitId ?? this.headCommitId,
      objectInstanceGraphId:
          objectInstanceGraphId ?? this.objectInstanceGraphId,
      threadBranchId: threadBranchId ?? this.threadBranchId,
      threadId: threadId ?? this.threadId,
      metadata: metadata ?? this.metadata,
    );
  }
}
