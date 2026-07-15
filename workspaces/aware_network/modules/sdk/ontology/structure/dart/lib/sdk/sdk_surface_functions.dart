// GENERATED CODE - DO NOT MODIFY BY HAND
// Function extensions for Dart OCG objects.

import 'sdk_surface_model.dart';
import 'sdk_surface_method_model.dart';
import 'package:uuid/uuid.dart';
import 'package:aware_model_helpers/payload_decoders.dart' as payload_decoders;
import 'package:aware_api/aware_api.dart';

extension SdkSurfaceFunctions on SdkSurface {
  /// Add one stable method under this SDK surface.
  Future<SdkSurfaceMethod> addMethod({
    required FunctionInvocationContext context,
    required String name,
    required UuidValue targetSdkOperationId,
    required String operationRef,
    required String operationName,
    required String methodFamily,
    required String effect,
    required String mutationScope,
    required String confirmationPolicy,
    required String executionMode,
    required String runtimeBindingKind,
    String? description,
  }) async {
    final args = <FunctionInvocationArgument>[];
    args.add(FunctionInvocationArgument(name: 'name', value: name));
    args.add(
      FunctionInvocationArgument(
        name: 'target_sdk_operation_id',
        value: targetSdkOperationId,
      ),
    );
    args.add(
      FunctionInvocationArgument(name: 'operation_ref', value: operationRef),
    );
    args.add(
      FunctionInvocationArgument(name: 'operation_name', value: operationName),
    );
    args.add(
      FunctionInvocationArgument(name: 'method_family', value: methodFamily),
    );
    args.add(FunctionInvocationArgument(name: 'effect', value: effect));
    args.add(
      FunctionInvocationArgument(name: 'mutation_scope', value: mutationScope),
    );
    args.add(
      FunctionInvocationArgument(
        name: 'confirmation_policy',
        value: confirmationPolicy,
      ),
    );
    args.add(
      FunctionInvocationArgument(name: 'execution_mode', value: executionMode),
    );
    args.add(
      FunctionInvocationArgument(
        name: 'runtime_binding_kind',
        value: runtimeBindingKind,
      ),
    );
    if (description != null) {
      args.add(
        FunctionInvocationArgument(name: 'description', value: description),
      );
    }
    final client = AwareApiLocator.of();
    final request = FunctionInvocationRequest(
      objectType: 'sdk-surface',
      objectId: id,
      functionName: 'add-method',
      threadId: context.threadId,
      branchId: context.branchId,
      projectionHash: context.projectionHash,
      arguments: args,
    );
    final response = await client.invokeFunctionByName(request);
    if (!response.isSuccess) {
      throw StateError(
        'Function SdkSurface.add_method failed: ' +
            (response.error ?? response.status.name),
      );
    }
    final responsePayload = response.payload;
    dynamic responseValue = responsePayload;
    if (responsePayload is Map && responsePayload.containsKey('value')) {
      responseValue = responsePayload['value'];
    }
    return SdkSurfaceMethod.fromJson(payload_decoders.decodeMap(responseValue));
  }
}
