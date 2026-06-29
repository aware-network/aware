import 'package:uuid/uuid.dart';

class AwareApiContext {
  const AwareApiContext({
    required this.environmentId,
    this.processId,
    this.threadId,
    this.branchId,
    this.projectionHash,
    this.actorId,
  });

  final UuidValue environmentId;
  final UuidValue? processId;
  final UuidValue? threadId;
  final UuidValue? branchId;
  final String? projectionHash;
  final UuidValue? actorId;

  AwareApiContext copyWith({
    UuidValue? environmentId,
    UuidValue? processId,
    UuidValue? threadId,
    UuidValue? branchId,
    String? projectionHash,
    UuidValue? actorId,
  }) {
    return AwareApiContext(
      environmentId: environmentId ?? this.environmentId,
      processId: processId ?? this.processId,
      threadId: threadId ?? this.threadId,
      branchId: branchId ?? this.branchId,
      projectionHash: projectionHash ?? this.projectionHash,
      actorId: actorId ?? this.actorId,
    );
  }
}
