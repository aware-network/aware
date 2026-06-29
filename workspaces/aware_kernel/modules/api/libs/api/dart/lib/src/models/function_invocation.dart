import 'package:uuid/uuid.dart';

import 'function_call.dart';

enum FunctionInvocationCallTarget {
  instance,
  opgConstructor,
}

class FunctionInvocationContext {
  const FunctionInvocationContext({
    required this.threadId,
    required this.branchId,
    this.projectionHash,
    this.opgId,
  });

  final UuidValue threadId;
  final UuidValue branchId;
  final String? projectionHash;
  final UuidValue? opgId;
}

class FunctionInvocationArgument {
  const FunctionInvocationArgument({
    required this.name,
    required this.value,
    this.cliFlags = const [],
    this.expectsValue = true,
    this.multiple = false,
  });

  final String name;
  final dynamic value;
  final List<String> cliFlags;
  final bool expectsValue;
  final bool multiple;
}

class FunctionInvocationRequest {
  FunctionInvocationRequest({
    required this.objectType,
    this.objectId,
    this.objectProjectionGraphId,
    required this.functionName,
    this.processId,
    required this.threadId,
    required this.branchId,
    required this.arguments,
    this.callTarget = FunctionInvocationCallTarget.instance,
    this.projectionHash,
    this.expectList = false,
    this.commit = true,
    this.publish = false,
    this.expectedGraphHashPre,
    this.expectedHeadCommitId,
  });

  final String objectType;
  final UuidValue? objectId;
  final UuidValue? objectProjectionGraphId;
  final String functionName;
  final UuidValue? processId;
  final UuidValue threadId;
  final UuidValue branchId;
  final List<FunctionInvocationArgument> arguments;
  final FunctionInvocationCallTarget callTarget;
  final String? projectionHash;
  final bool expectList;
  final bool commit;
  final bool publish;
  final String? expectedGraphHashPre;
  final UuidValue? expectedHeadCommitId;

  FunctionCallTarget toCallTarget() {
    switch (callTarget) {
      case FunctionInvocationCallTarget.opgConstructor:
        return FunctionCallTarget.opgConstructor;
      case FunctionInvocationCallTarget.instance:
        return FunctionCallTarget.instance;
    }
  }
}
