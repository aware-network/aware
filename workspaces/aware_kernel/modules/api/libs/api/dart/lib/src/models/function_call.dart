import 'package:uuid/uuid.dart';

enum FunctionCallStatus {
  succeeded,
  failed,
}

enum FunctionCallTarget {
  instance,
  opgConstructor,
}

extension FunctionCallTargetWire on FunctionCallTarget {
  String get wireValue {
    switch (this) {
      case FunctionCallTarget.opgConstructor:
        return 'opg_constructor';
      case FunctionCallTarget.instance:
        return 'instance';
    }
  }
}

class FunctionCallRequest {
  FunctionCallRequest({
    this.callTarget = FunctionCallTarget.instance,
    this.objectId,
    this.objectProjectionGraphId,
    required this.functionId,
    this.args = const [],
    this.kwargs = const {},
    required this.actorId,
    this.commit = true,
    this.publish = false,
    this.expectedGraphHashPre,
    this.expectedHeadCommitId,
  }) {
    _validateRouting();
  }

  final FunctionCallTarget callTarget;
  final UuidValue? objectId;
  final UuidValue? objectProjectionGraphId;
  final UuidValue functionId;
  final List<dynamic> args;
  final Map<String, dynamic> kwargs;
  final UuidValue actorId;
  final bool commit;
  final bool publish;
  final String? expectedGraphHashPre;
  final UuidValue? expectedHeadCommitId;

  void _validateRouting() {
    if (callTarget == FunctionCallTarget.instance) {
      if (objectId == null) {
        throw ArgumentError('objectId is required when callTarget=instance');
      }
      if (objectProjectionGraphId != null) {
        throw ArgumentError(
          'objectProjectionGraphId is not allowed when callTarget=instance',
        );
      }
      return;
    }

    if (callTarget == FunctionCallTarget.opgConstructor) {
      if (objectProjectionGraphId == null) {
        throw ArgumentError(
          'objectProjectionGraphId is required when callTarget=opgConstructor',
        );
      }
      if (objectId != null) {
        throw ArgumentError(
          'objectId must be null when callTarget=opgConstructor',
        );
      }
      return;
    }

    throw ArgumentError('Unsupported callTarget=$callTarget');
  }
}

class FunctionCallResult {
  const FunctionCallResult({
    required this.status,
    this.payload,
    this.error,
    this.logs = const [],
    this.executionTimeMs,
    this.branchId,
    this.rootObjectId,
    this.projectionHash,
    this.graphHashPre,
    this.graphHashPost,
    this.changes = const [],
    this.commitId,
    this.objectInstanceGraphCommitId,
  });

  final FunctionCallStatus status;
  final Object? payload;
  final String? error;
  final List<String> logs;
  final int? executionTimeMs;
  final UuidValue? branchId;
  final UuidValue? rootObjectId;
  final String? projectionHash;
  final String? graphHashPre;
  final String? graphHashPost;
  final List<dynamic> changes;
  final UuidValue? commitId;
  final UuidValue? objectInstanceGraphCommitId;

  bool get isSuccess => status == FunctionCallStatus.succeeded;

  factory FunctionCallResult.fromEnvironmentPayload(Object? payload) {
    final map = _asJsonMap(payload);
    return FunctionCallResult(
      status: _parseStatus(map['status']?.toString() ?? ''),
      payload: map['payload'],
      error: map['error']?.toString(),
      logs: _stringList(map['logs']),
      executionTimeMs: _intOrNull(
        map['execution_time_ms'] ?? map['executionTimeMs'],
      ),
      branchId: _uuidOrNull(map['branch_id'] ?? map['branchId']),
      rootObjectId: _uuidOrNull(map['root_object_id'] ?? map['rootObjectId']),
      projectionHash:
          (map['projection_hash'] ?? map['projectionHash'])?.toString(),
      graphHashPre: (map['graph_hash_pre'] ?? map['graphHashPre'])?.toString(),
      graphHashPost:
          (map['graph_hash_post'] ?? map['graphHashPost'])?.toString(),
      changes: _dynamicList(map['changes']),
      commitId: _uuidOrNull(map['commit_id'] ?? map['commitId']),
      objectInstanceGraphCommitId: _uuidOrNull(
        map['object_instance_graph_commit_id'] ??
            map['objectInstanceGraphCommitId'],
      ),
    );
  }

  static FunctionCallStatus _parseStatus(String status) {
    final normalized = status.trim().toLowerCase();
    if (normalized == 'succeeded' ||
        normalized == 'success' ||
        normalized == 'ok') {
      return FunctionCallStatus.succeeded;
    }
    return FunctionCallStatus.failed;
  }
}

Map<String, dynamic> _asJsonMap(Object? payload) {
  if (payload is Map<String, dynamic>) return payload;
  if (payload is Map) return Map<String, dynamic>.from(payload);
  throw StateError(
    'Function call response payload must be a JSON object; got ${payload.runtimeType}.',
  );
}

List<String> _stringList(Object? value) {
  if (value is Iterable) {
    return value.map((entry) => entry.toString()).toList();
  }
  return const <String>[];
}

List<dynamic> _dynamicList(Object? value) {
  if (value is Iterable) return value.toList();
  return const <dynamic>[];
}

int? _intOrNull(Object? value) {
  if (value == null) return null;
  if (value is int) return value;
  if (value is num) return value.toInt();
  return int.tryParse(value.toString());
}

UuidValue? _uuidOrNull(Object? value) {
  if (value == null) return null;
  final text = value.toString();
  if (text.trim().isEmpty) return null;
  return UuidValue.fromString(text);
}
