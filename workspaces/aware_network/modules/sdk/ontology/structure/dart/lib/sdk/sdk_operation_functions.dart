// GENERATED CODE - DO NOT MODIFY BY HAND
// Function extensions for Dart OCG objects.

import 'sdk_operation_model.dart';
import 'sdk_operation_api_capability_endpoint_model.dart';
import 'sdk_operation_dependency_model.dart';
import 'package:uuid/uuid.dart';
import 'package:aware_model_helpers/payload_decoders.dart' as payload_decoders;
import 'package:aware_api/aware_api.dart';

extension SdkOperationFunctions on SdkOperation {
  /// Bind this SDK operation to one API capability endpoint.
  ///
  /// Contract:
  /// - `api_capability_endpoint_id` points at API-owned invocation truth.
  /// - `endpoint_ref` preserves authored `api.capability.endpoint` syntax when available.
  /// - `role`, `order`, and `required` are SDK orchestration metadata only.
  Future<SdkOperationApiCapabilityEndpoint> bindApiCapabilityEndpoint({
    required FunctionInvocationContext context,
    required String name,
    required UuidValue apiCapabilityEndpointId,
    String? endpointRef,
    String? discriminant,
    required String role,
    required int order,
    required bool required_,
  }) async {
    final args = <FunctionInvocationArgument>[];
    args.add(FunctionInvocationArgument(name: 'name', value: name));
    args.add(
      FunctionInvocationArgument(
        name: 'api_capability_endpoint_id',
        value: apiCapabilityEndpointId,
      ),
    );
    if (endpointRef != null) {
      args.add(
        FunctionInvocationArgument(name: 'endpoint_ref', value: endpointRef),
      );
    }
    if (discriminant != null) {
      args.add(
        FunctionInvocationArgument(name: 'discriminant', value: discriminant),
      );
    }
    args.add(FunctionInvocationArgument(name: 'role', value: role));
    args.add(FunctionInvocationArgument(name: 'order', value: order));
    args.add(FunctionInvocationArgument(name: 'required', value: required_));
    final client = AwareApiLocator.of();
    final request = FunctionInvocationRequest(
      objectType: 'sdk-operation',
      objectId: id,
      functionName: 'bind-api-capability-endpoint',
      threadId: context.threadId,
      branchId: context.branchId,
      projectionHash: context.projectionHash,
      arguments: args,
    );
    final response = await client.invokeFunctionByName(request);
    if (!response.isSuccess) {
      throw StateError(
        'Function SdkOperation.bind_api_capability_endpoint failed: ' +
            (response.error ?? response.status.name),
      );
    }
    final responsePayload = response.payload;
    dynamic responseValue = responsePayload;
    if (responsePayload is Map && responsePayload.containsKey('value')) {
      responseValue = responsePayload['value'];
    }
    return SdkOperationApiCapabilityEndpoint.fromJson(
      payload_decoders.decodeMap(responseValue),
    );
  }

  /// Bind this SDK operation to another SDK operation.
  ///
  /// Contract:
  /// - This is SDK operation composition truth, not API endpoint ingress truth.
  /// - Local operation refs target the same `SdkConfig`; external refs must come from
  /// the package dependency closure declared by `SdkPackageDependency`.
  /// - `target_operation_ref` preserves authored `sdk_name.operation_name` syntax.
  Future<SdkOperationDependency> bindSdkOperationDependency({
    required FunctionInvocationContext context,
    required UuidValue targetSdkOperationId,
    required String targetOperationRef,
    required String targetSdkName,
    required String targetOperationName,
    String? targetPackageName,
    required String role,
    required int order,
    required bool required_,
    String? description,
  }) async {
    final args = <FunctionInvocationArgument>[];
    args.add(
      FunctionInvocationArgument(
        name: 'target_sdk_operation_id',
        value: targetSdkOperationId,
      ),
    );
    args.add(
      FunctionInvocationArgument(
        name: 'target_operation_ref',
        value: targetOperationRef,
      ),
    );
    args.add(
      FunctionInvocationArgument(name: 'target_sdk_name', value: targetSdkName),
    );
    args.add(
      FunctionInvocationArgument(
        name: 'target_operation_name',
        value: targetOperationName,
      ),
    );
    if (targetPackageName != null) {
      args.add(
        FunctionInvocationArgument(
          name: 'target_package_name',
          value: targetPackageName,
        ),
      );
    }
    args.add(FunctionInvocationArgument(name: 'role', value: role));
    args.add(FunctionInvocationArgument(name: 'order', value: order));
    args.add(FunctionInvocationArgument(name: 'required', value: required_));
    if (description != null) {
      args.add(
        FunctionInvocationArgument(name: 'description', value: description),
      );
    }
    final client = AwareApiLocator.of();
    final request = FunctionInvocationRequest(
      objectType: 'sdk-operation',
      objectId: id,
      functionName: 'bind-sdk-operation-dependency',
      threadId: context.threadId,
      branchId: context.branchId,
      projectionHash: context.projectionHash,
      arguments: args,
    );
    final response = await client.invokeFunctionByName(request);
    if (!response.isSuccess) {
      throw StateError(
        'Function SdkOperation.bind_sdk_operation_dependency failed: ' +
            (response.error ?? response.status.name),
      );
    }
    final responsePayload = response.payload;
    dynamic responseValue = responsePayload;
    if (responsePayload is Map && responsePayload.containsKey('value')) {
      responseValue = responsePayload['value'];
    }
    return SdkOperationDependency.fromJson(
      payload_decoders.decodeMap(responseValue),
    );
  }
}
