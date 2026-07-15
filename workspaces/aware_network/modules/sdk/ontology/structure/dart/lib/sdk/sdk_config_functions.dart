// GENERATED CODE - DO NOT MODIFY BY HAND
// Function extensions for Dart OCG objects.

import 'sdk_config_model.dart';
import 'sdk_operation_model.dart';
import 'sdk_surface_model.dart';
import 'package:aware_model_helpers/payload_decoders.dart' as payload_decoders;
import 'package:aware_api/aware_api.dart';

extension SdkConfigFunctions on SdkConfig {
  /// Add one SDK-owned operation under this SDK config.
  Future<SdkOperation> addOperation({
    required FunctionInvocationContext context,
    required String name,
    String? title,
    String? description,
    String? implementationRef,
  }) async {
    final args = <FunctionInvocationArgument>[];
    args.add(FunctionInvocationArgument(name: 'name', value: name));
    if (title != null) {
      args.add(FunctionInvocationArgument(name: 'title', value: title));
    }
    if (description != null) {
      args.add(
        FunctionInvocationArgument(name: 'description', value: description),
      );
    }
    if (implementationRef != null) {
      args.add(
        FunctionInvocationArgument(
          name: 'implementation_ref',
          value: implementationRef,
        ),
      );
    }
    final client = AwareApiLocator.of();
    final request = FunctionInvocationRequest(
      objectType: 'sdk-config',
      objectId: id,
      functionName: 'add-operation',
      threadId: context.threadId,
      branchId: context.branchId,
      projectionHash: context.projectionHash,
      arguments: args,
    );
    final response = await client.invokeFunctionByName(request);
    if (!response.isSuccess) {
      throw StateError(
        'Function SdkConfig.add_operation failed: ' +
            (response.error ?? response.status.name),
      );
    }
    final responsePayload = response.payload;
    dynamic responseValue = responsePayload;
    if (responsePayload is Map && responsePayload.containsKey('value')) {
      responseValue = responsePayload['value'];
    }
    return SdkOperation.fromJson(payload_decoders.decodeMap(responseValue));
  }

  /// Add one SDK-owned conceptual surface under this SDK config.
  Future<SdkSurface> addSurface({
    required FunctionInvocationContext context,
    required String name,
    String? title,
    String? description,
  }) async {
    final args = <FunctionInvocationArgument>[];
    args.add(FunctionInvocationArgument(name: 'name', value: name));
    if (title != null) {
      args.add(FunctionInvocationArgument(name: 'title', value: title));
    }
    if (description != null) {
      args.add(
        FunctionInvocationArgument(name: 'description', value: description),
      );
    }
    final client = AwareApiLocator.of();
    final request = FunctionInvocationRequest(
      objectType: 'sdk-config',
      objectId: id,
      functionName: 'add-surface',
      threadId: context.threadId,
      branchId: context.branchId,
      projectionHash: context.projectionHash,
      arguments: args,
    );
    final response = await client.invokeFunctionByName(request);
    if (!response.isSuccess) {
      throw StateError(
        'Function SdkConfig.add_surface failed: ' +
            (response.error ?? response.status.name),
      );
    }
    final responsePayload = response.payload;
    dynamic responseValue = responsePayload;
    if (responsePayload is Map && responsePayload.containsKey('value')) {
      responseValue = responsePayload['value'];
    }
    return SdkSurface.fromJson(payload_decoders.decodeMap(responseValue));
  }
}

class SdkConfigConstructors {
  /// Create one canonical reusable SDK definition.
  ///
  /// Contract:
  /// - `SdkConfig` is the semantic orchestration root for generated/handwritten SDK surfaces.
  /// - `SdkOperation` is SDK-owned local operation truth.
  /// - `SdkOperationApiCapabilityEndpoint` binds each SDK operation to API-owned endpoint truth.
  /// - Runtime language adapters consume this config; they do not invent SDK/API contracts.
  static Future<FunctionCallResult> build({
    required FunctionInvocationContext context,
    required String name,
    String? title,
    String? description,
  }) async {
    final args = <FunctionInvocationArgument>[];
    args.add(FunctionInvocationArgument(name: 'name', value: name));
    if (title != null) {
      args.add(FunctionInvocationArgument(name: 'title', value: title));
    }
    if (description != null) {
      args.add(
        FunctionInvocationArgument(name: 'description', value: description),
      );
    }
    final client = AwareApiLocator.of();
    final request = FunctionInvocationRequest(
      objectType: 'sdk-config',
      functionName: 'build',
      threadId: context.threadId,
      branchId: context.branchId,
      projectionHash: context.projectionHash,
      callTarget: FunctionInvocationCallTarget.opgConstructor,
      objectProjectionGraphId: context.opgId,
      arguments: args,
    );
    final response = await client.invokeFunctionByName(request);
    if (!response.isSuccess) {
      throw StateError(
        'Function SdkConfig.build failed: ' +
            (response.error ?? response.status.name),
      );
    }
    return response;
  }
}
