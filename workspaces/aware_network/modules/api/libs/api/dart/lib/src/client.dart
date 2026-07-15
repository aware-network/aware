import 'dart:async';

import 'package:uuid/uuid.dart';

import 'capability_resolver.dart';
import 'config.dart';
import 'context.dart';
import 'invoker.dart';
import 'models/function_call.dart';
import 'models/function_invocation.dart';
import 'transport.dart';

class AwareApiClient {
  AwareApiClient(
      {required ApiEndpointTransport transport, AwareApiConfig? config})
      : _endpointInvoker = AwareApiEndpointInvoker(transport: transport),
        _context = config?.context;

  final AwareApiEndpointInvoker _endpointInvoker;

  AwareApiContext? _context;
  Object? _capabilities;
  CapabilityResolver? _resolver;

  void setContext(AwareApiContext context) {
    _context = context;
  }

  AwareApiContext get context {
    final ctx = _context;
    if (ctx == null) {
      throw StateError('AwareApiClient context has not been set.');
    }
    return ctx;
  }

  void setCapabilities(Object? capabilities) {
    _capabilities = capabilities;
    _resolver = CapabilityResolver(capabilities: capabilities);
  }

  Object? get capabilities => _capabilities;

  CapabilityResolver? get capabilityResolver => _resolver;

  Future<Map<String, dynamic>?> fetchCapabilities({
    Duration timeout = const Duration(seconds: 30),
  }) async {
    final payload = await _invokeEnvironmentOperation(
      operation: 'fetch_capabilities',
      requestPayload: _environmentOperationPayload(
        operation: 'fetch_capabilities',
        context: context,
      ),
      actorId: _context?.actorId,
      timeout: timeout,
    );
    final capabilities = _asJsonMapOrNull(payload);
    if (capabilities != null) {
      setCapabilities(capabilities);
    }
    return capabilities;
  }

  Future<Map<String, dynamic>?> ensureReady({
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _asJsonMapOrNull(
      await _invokeEnvironmentOperation(
        operation: 'ensure_ready',
        requestPayload: _environmentOperationPayload(
          operation: 'ensure_ready',
          context: context,
        ),
        actorId: _context?.actorId,
        timeout: timeout,
      ),
    );
  }

  Future<FunctionCallResult> invokeFunction(
    FunctionCallRequest request, {
    Duration timeout = const Duration(seconds: 30),
    AwareApiContext? overrideContext,
  }) async {
    final ctx = _requireContext(overrideContext);

    final threadId = ctx.threadId;
    final branchId = ctx.branchId;
    if (threadId == null || branchId == null) {
      throw StateError(
        'invokeFunction requires threadId and branchId in AwareApiContext.',
      );
    }

    final requestPayload = _environmentOperationPayload(
      operation: 'invoke_function',
      context: ctx,
      actorId: request.actorId,
    )..addAll(<String, dynamic>{
        'call_target': request.callTarget.wireValue,
        'object_id': request.objectId?.toString(),
        'object_projection_graph_id':
            request.objectProjectionGraphId?.toString(),
        'function_id': request.functionId.toString(),
        'args': coerceApiEndpointJson(request.args),
        'kwargs': coerceApiEndpointJson(request.kwargs),
        'expected_graph_hash_pre': request.expectedGraphHashPre,
        'expected_head_commit_id': request.expectedHeadCommitId?.toString(),
        'commit': request.commit,
        'publish': request.publish,
      });
    requestPayload.removeWhere((_, value) => value == null);

    final responsePayload = await _invokeEnvironmentOperation(
      operation: 'invoke_function',
      requestPayload: requestPayload,
      actorId: request.actorId,
      timeout: timeout,
    );

    return FunctionCallResult.fromEnvironmentPayload(responsePayload);
  }

  Future<FunctionCallResult> invokeFunctionByName(
    FunctionInvocationRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    final baseContext = context;
    final callContext = baseContext.copyWith(
      processId: request.processId ?? baseContext.processId,
      threadId: request.threadId,
      branchId: request.branchId,
      projectionHash: request.projectionHash ?? baseContext.projectionHash,
    );

    final actorId = callContext.actorId;
    if (actorId == null) {
      throw StateError('AwareApiContext.actorId is required for invocation.');
    }

    final resolver = await _ensureResolver();
    final functionId = resolver.resolveFunctionId(
      objectName: request.objectType,
      functionName: request.functionName,
    );
    if (functionId == null) {
      throw StateError(
        'Unable to resolve functionId for ${request.objectType}.${request.functionName}',
      );
    }

    final kwargs = _buildKwargs(request.arguments);

    final callRequest = FunctionCallRequest(
      callTarget: request.toCallTarget(),
      objectId: request.objectId,
      objectProjectionGraphId: request.objectProjectionGraphId,
      functionId: functionId,
      args: const <dynamic>[],
      kwargs: kwargs,
      actorId: actorId,
      commit: request.commit,
      publish: request.publish,
      expectedGraphHashPre: request.expectedGraphHashPre,
      expectedHeadCommitId: request.expectedHeadCommitId,
    );

    return invokeFunction(
      callRequest,
      timeout: timeout,
      overrideContext: callContext,
    );
  }

  Future<Object?> invokeApiEndpointRaw({
    required String endpointRef,
    required String discriminant,
    Object? requestPayload = const <String, dynamic>{},
    Duration timeout = const Duration(seconds: 30),
    UuidValue? actorId,
  }) async {
    return _endpointInvoker.invokeApiEndpointRaw(
      actorId: _resolveActorId(actorId),
      endpointRef: endpointRef,
      discriminant: discriminant,
      requestPayload: requestPayload,
      timeout: timeout,
    );
  }

  Future<T> invokeApiEndpoint<T>({
    required String endpointRef,
    required String discriminant,
    Object? requestPayload = const <String, dynamic>{},
    required T Function(Object? payload) decodeResponse,
    Duration timeout = const Duration(seconds: 30),
    UuidValue? actorId,
  }) async {
    return _endpointInvoker.invokeApiEndpoint<T>(
      actorId: _resolveActorId(actorId),
      endpointRef: endpointRef,
      discriminant: discriminant,
      requestPayload: requestPayload,
      decodeResponse: decodeResponse,
      timeout: timeout,
    );
  }

  Stream<Object?> streamApiEndpointRaw({
    required String endpointRef,
    required String discriminant,
    Object? requestPayload = const <String, dynamic>{},
    Duration timeout = const Duration(seconds: 30),
    UuidValue? actorId,
  }) async* {
    yield* _endpointInvoker.streamApiEndpointRaw(
      actorId: _resolveActorId(actorId),
      endpointRef: endpointRef,
      discriminant: discriminant,
      requestPayload: requestPayload,
      timeout: timeout,
    );
  }

  Stream<T> streamApiEndpoint<T>({
    required String endpointRef,
    required String discriminant,
    Object? requestPayload = const <String, dynamic>{},
    required T Function(Object? payload) decodeEvent,
    Duration timeout = const Duration(seconds: 30),
    UuidValue? actorId,
  }) async* {
    yield* _endpointInvoker.streamApiEndpoint<T>(
      actorId: _resolveActorId(actorId),
      endpointRef: endpointRef,
      discriminant: discriminant,
      requestPayload: requestPayload,
      decodeEvent: decodeEvent,
      timeout: timeout,
    );
  }

  AwareApiContext _requireContext(AwareApiContext? overrideContext) {
    final ctx = overrideContext ?? _context;
    if (ctx == null) {
      throw StateError('AwareApiClient context has not been set.');
    }
    return ctx;
  }

  Future<CapabilityResolver> _ensureResolver() async {
    final resolver = _resolver;
    if (resolver != null) {
      return resolver;
    }

    final capabilities = await fetchCapabilities();
    final updatedResolver = _resolver;
    if (capabilities == null || updatedResolver == null) {
      throw StateError('Capabilities are not available for invocation.');
    }
    return updatedResolver;
  }

  UuidValue? _resolveActorId(UuidValue? actorId) {
    return actorId ?? _context?.actorId;
  }

  Future<Object?> _invokeEnvironmentOperation({
    required String operation,
    required Map<String, dynamic> requestPayload,
    required UuidValue? actorId,
    required Duration timeout,
  }) {
    final endpointRef = _environmentEndpointRefs[operation];
    if (endpointRef == null) {
      throw StateError(
        'Environment operation $operation is not exposed on the API endpoint rail.',
      );
    }

    return invokeApiEndpointRaw(
      actorId: actorId,
      endpointRef: endpointRef,
      discriminant: endpointRef,
      requestPayload: requestPayload,
      timeout: timeout,
    );
  }

  Map<String, dynamic> _environmentOperationPayload({
    required String operation,
    required AwareApiContext context,
    UuidValue? actorId,
  }) {
    final payload = <String, dynamic>{
      'operation': operation,
      'actor_id': (actorId ?? context.actorId)?.toString(),
      'environment_id': context.environmentId.toString(),
      'process_id': context.processId?.toString(),
      'thread_id': context.threadId?.toString(),
      'branch_id': context.branchId?.toString(),
      'projection_hash': context.projectionHash,
    };
    payload.removeWhere((_, value) => value == null);
    return payload;
  }

  Map<String, dynamic> _buildKwargs(
    List<FunctionInvocationArgument> arguments,
  ) {
    final kwargs = <String, dynamic>{};
    for (final arg in arguments) {
      final value = arg.value;
      if (value == null) continue;

      if (arg.multiple && value is Iterable) {
        kwargs[arg.name] = value.map(coerceApiEndpointJson).toList();
        continue;
      }

      kwargs[arg.name] = coerceApiEndpointJson(value);
    }
    return kwargs;
  }

  Map<String, dynamic>? _asJsonMapOrNull(Object? payload) {
    if (payload == null) return null;
    if (payload is Map<String, dynamic>) return payload;
    if (payload is Map) return Map<String, dynamic>.from(payload);
    throw StateError(
      'Environment API response payload must be a JSON object; got ${payload.runtimeType}.',
    );
  }
}

const Map<String, String> _environmentEndpointRefs = {
  'fetch_capabilities': 'environment.capabilities.fetch_capabilities',
  'ensure_ready': 'environment.ready.ensure_ready',
  'invoke_function': 'environment.function_call.invoke_function',
};
