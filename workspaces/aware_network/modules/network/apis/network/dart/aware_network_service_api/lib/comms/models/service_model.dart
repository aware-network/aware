// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';
import 'service_enums.dart';

part 'service_model.freezed.dart';
part 'service_model.g.dart';

@freezed
abstract class ServiceOperationContext with _$ServiceOperationContext {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ServiceOperationContext.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue branchId,
    required String projectionHash,
  }) = _ServiceOperationContext;

  factory ServiceOperationContext({
    UuidValue? actorId,
    required UuidValue branchId,
    required String projectionHash,
  }) {
    return _ServiceOperationContext(
      actorId: actorId,
      branchId: branchId,
      projectionHash: projectionHash,
    );
  }

  factory ServiceOperationContext.fromJson(Map<String, dynamic> json) =>
      _$ServiceOperationContextFromJson(json);
}

/// Reference-only projection of the shared commercial execution receipt.
/// Amounts, balances, and ledger authority remain queryable from Economy.
@freezed
abstract class ServiceOperationEconomicReceiptRefsV1
    with _$ServiceOperationEconomicReceiptRefsV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ServiceOperationEconomicReceiptRefsV1.def({
    required String contractVersion,
    @UuidValueConverter() required UuidValue serviceOperationId,
    @UuidValueConverter() required UuidValue serviceContractId,
    @UuidValueConverter() required UuidValue permitId,
    @UuidValueConverter() required UuidValue priceId,
    @UuidValueConverter() required UuidValue priceScheduleId,
    @UuidValueConverter() required UuidValue rateSnapshotId,
    @UuidValueConverter() required UuidValue priceReservationId,
    @UuidValueConverter() required UuidValue smartContractReservationId,
    @UuidValueConverter() required UuidValue settlementId,
    @UuidValueConverter() UuidValue? transactionId,
    @UuidValueConverter() required UuidValue payerWalletBalanceId,
    @UuidValueConverter() required UuidValue receiverWalletBalanceId,
    required String status,
    required bool idempotentReplay,
  }) = _ServiceOperationEconomicReceiptRefsV1;

  factory ServiceOperationEconomicReceiptRefsV1({
    String? contractVersion,
    required UuidValue serviceOperationId,
    required UuidValue serviceContractId,
    required UuidValue permitId,
    required UuidValue priceId,
    required UuidValue priceScheduleId,
    required UuidValue rateSnapshotId,
    required UuidValue priceReservationId,
    required UuidValue smartContractReservationId,
    required UuidValue settlementId,
    UuidValue? transactionId,
    required UuidValue payerWalletBalanceId,
    required UuidValue receiverWalletBalanceId,
    required String status,
    bool? idempotentReplay,
  }) {
    return _ServiceOperationEconomicReceiptRefsV1(
      contractVersion:
          contractVersion ?? 'aware.service.operation_economic_receipt_refs.v1',
      serviceOperationId: serviceOperationId,
      serviceContractId: serviceContractId,
      permitId: permitId,
      priceId: priceId,
      priceScheduleId: priceScheduleId,
      rateSnapshotId: rateSnapshotId,
      priceReservationId: priceReservationId,
      smartContractReservationId: smartContractReservationId,
      settlementId: settlementId,
      transactionId: transactionId,
      payerWalletBalanceId: payerWalletBalanceId,
      receiverWalletBalanceId: receiverWalletBalanceId,
      status: status,
      idempotentReplay: idempotentReplay ?? false,
    );
  }

  factory ServiceOperationEconomicReceiptRefsV1.fromJson(
    Map<String, dynamic> json,
  ) => _$ServiceOperationEconomicReceiptRefsV1FromJson({
    ...json,
    if (!json.containsKey('contract_version'))
      'contract_version': 'aware.service.operation_economic_receipt_refs.v1',
    if (!json.containsKey('idempotent_replay')) 'idempotent_replay': false,
  });
}

@freezed
abstract class ServiceOperation with _$ServiceOperation {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ServiceOperation.def({
    ServiceOperationRequest? request,
    ServiceOperationResponse? response,
  }) = _ServiceOperation;

  factory ServiceOperation({
    ServiceOperationRequest? request,
    ServiceOperationResponse? response,
  }) {
    return _ServiceOperation(request: request, response: response);
  }

  factory ServiceOperation.fromJson(Map<String, dynamic> json) =>
      _$ServiceOperationFromJson(json);
}

@freezed
abstract class ServiceApiDispatchEnvelope with _$ServiceApiDispatchEnvelope {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ServiceApiDispatchEnvelope.def({
    @UuidValueConverter() required UuidValue apiCallId,
    @UuidValueConverter() required UuidValue apiCapabilityEndpointId,
    @UuidValueConverter() required UuidValue callKey,
    required String requestHash,
    @UuidValueConverter() required UuidValue commitId,
    @UuidValueConverter() required UuidValue headCommitId,
    @UuidValueConverter() required UuidValue branchId,
    required String projectionHash,
    required String apiName,
    required String capabilityName,
    required String endpointName,
    required String endpointRef,
    required String discriminant,
    required String sourcePath,
    @UuidValueConverter() required UuidValue requestModelId,
    @UuidValueConverter() required UuidValue requestClassConfigId,
    required String requestClassRef,
    required String requestSourcePath,
    String? responseClassRef,
    String? responseSourcePath,
  }) = _ServiceApiDispatchEnvelope;

  factory ServiceApiDispatchEnvelope({
    required UuidValue apiCallId,
    required UuidValue apiCapabilityEndpointId,
    required UuidValue callKey,
    required String requestHash,
    required UuidValue commitId,
    required UuidValue headCommitId,
    required UuidValue branchId,
    required String projectionHash,
    required String apiName,
    required String capabilityName,
    required String endpointName,
    required String endpointRef,
    required String discriminant,
    required String sourcePath,
    required UuidValue requestModelId,
    required UuidValue requestClassConfigId,
    required String requestClassRef,
    required String requestSourcePath,
    String? responseClassRef,
    String? responseSourcePath,
  }) {
    return _ServiceApiDispatchEnvelope(
      apiCallId: apiCallId,
      apiCapabilityEndpointId: apiCapabilityEndpointId,
      callKey: callKey,
      requestHash: requestHash,
      commitId: commitId,
      headCommitId: headCommitId,
      branchId: branchId,
      projectionHash: projectionHash,
      apiName: apiName,
      capabilityName: capabilityName,
      endpointName: endpointName,
      endpointRef: endpointRef,
      discriminant: discriminant,
      sourcePath: sourcePath,
      requestModelId: requestModelId,
      requestClassConfigId: requestClassConfigId,
      requestClassRef: requestClassRef,
      requestSourcePath: requestSourcePath,
      responseClassRef: responseClassRef,
      responseSourcePath: responseSourcePath,
    );
  }

  factory ServiceApiDispatchEnvelope.fromJson(Map<String, dynamic> json) =>
      _$ServiceApiDispatchEnvelopeFromJson(json);
}

@freezed
abstract class ServiceApiDispatchFulfillmentBinding
    with _$ServiceApiDispatchFulfillmentBinding {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ServiceApiDispatchFulfillmentBinding.def({
    required String name,
    required String graphTarget,
    required String graphCapabilityFunctionName,
    required String graphFunctionPythonRef,
    required String graphFunctionRuntimeTarget,
    required String methodName,
    required String requestTypeRef,
    required String responseTypeRef,
    required String sourcePath,
    @UuidValueConverter() UuidValue? apiCapabilityEndpointFunctionId,
  }) = _ServiceApiDispatchFulfillmentBinding;

  factory ServiceApiDispatchFulfillmentBinding({
    required String name,
    required String graphTarget,
    required String graphCapabilityFunctionName,
    required String graphFunctionPythonRef,
    required String graphFunctionRuntimeTarget,
    required String methodName,
    required String requestTypeRef,
    required String responseTypeRef,
    required String sourcePath,
    UuidValue? apiCapabilityEndpointFunctionId,
  }) {
    return _ServiceApiDispatchFulfillmentBinding(
      name: name,
      graphTarget: graphTarget,
      graphCapabilityFunctionName: graphCapabilityFunctionName,
      graphFunctionPythonRef: graphFunctionPythonRef,
      graphFunctionRuntimeTarget: graphFunctionRuntimeTarget,
      methodName: methodName,
      requestTypeRef: requestTypeRef,
      responseTypeRef: responseTypeRef,
      sourcePath: sourcePath,
      apiCapabilityEndpointFunctionId: apiCapabilityEndpointFunctionId,
    );
  }

  factory ServiceApiDispatchFulfillmentBinding.fromJson(
    Map<String, dynamic> json,
  ) => _$ServiceApiDispatchFulfillmentBindingFromJson(json);
}

@freezed
abstract class ServiceApiDispatchRequest with _$ServiceApiDispatchRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ServiceApiDispatchRequest.def({
    required String operationKey,
    required ServiceApiDispatchEnvelope envelope,
    required Map<String, dynamic> requestPayload,
    @Default(const [])
    List<ServiceApiDispatchFulfillmentBinding> fulfillmentBindings,
  }) = _ServiceApiDispatchRequest;

  factory ServiceApiDispatchRequest({
    required String operationKey,
    required ServiceApiDispatchEnvelope envelope,
    required Map<String, dynamic> requestPayload,
    List<ServiceApiDispatchFulfillmentBinding> fulfillmentBindings = const [],
  }) {
    return _ServiceApiDispatchRequest(
      operationKey: operationKey,
      envelope: envelope,
      requestPayload: requestPayload,
      fulfillmentBindings: fulfillmentBindings,
    );
  }

  factory ServiceApiDispatchRequest.fromJson(Map<String, dynamic> json) =>
      _$ServiceApiDispatchRequestFromJson(json);
}

@freezed
abstract class ServiceApiDispatchReceipt with _$ServiceApiDispatchReceipt {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ServiceApiDispatchReceipt.def({
    required String endpointRef,
    required String discriminant,
    @JsonKey(
      fromJson: RequestStatusExtension.fromJson,
      toJson: RequestStatusExtension.toJson,
    )
    required RequestStatus status,
    @UuidValueConverter() UuidValue? networkRequestId,
    @UuidValueConverter() UuidValue? apiCallId,
    @UuidValueConverter() UuidValue? apiCapabilityEndpointId,
    @UuidValueConverter() UuidValue? callKey,
    String? requestHash,
    @UuidValueConverter() UuidValue? requestModelId,
    @UuidValueConverter() UuidValue? apiCallOutcomeId,
    @UuidValueConverter() UuidValue? responseModelId,
    @UuidValueConverter() UuidValue? serviceOperationId,
    @UuidValueConverter() UuidValue? serviceOperationConfigId,
    @UuidValueConverter() UuidValue? serviceOperationConfigApiEndpointId,
    @UuidValueConverter() UuidValue? serviceOperationCommitId,
    @UuidValueConverter() UuidValue? serviceOperationHeadCommitId,
    @UuidValueConverter() UuidValue? serviceOperationBranchId,
    String? serviceOperationProjectionHash,
    @UuidValueConverter() UuidValue? apiCallOutcomeCommitId,
    @UuidValueConverter() UuidValue? apiCallOutcomeHeadCommitId,
    @UuidValueConverter() UuidValue? apiCallOutcomeBranchId,
    String? apiCallOutcomeProjectionHash,
    ServiceOperationEconomicReceiptRefsV1? economicReceipt,
  }) = _ServiceApiDispatchReceipt;

  factory ServiceApiDispatchReceipt({
    required String endpointRef,
    required String discriminant,
    RequestStatus? status,
    UuidValue? networkRequestId,
    UuidValue? apiCallId,
    UuidValue? apiCapabilityEndpointId,
    UuidValue? callKey,
    String? requestHash,
    UuidValue? requestModelId,
    UuidValue? apiCallOutcomeId,
    UuidValue? responseModelId,
    UuidValue? serviceOperationId,
    UuidValue? serviceOperationConfigId,
    UuidValue? serviceOperationConfigApiEndpointId,
    UuidValue? serviceOperationCommitId,
    UuidValue? serviceOperationHeadCommitId,
    UuidValue? serviceOperationBranchId,
    String? serviceOperationProjectionHash,
    UuidValue? apiCallOutcomeCommitId,
    UuidValue? apiCallOutcomeHeadCommitId,
    UuidValue? apiCallOutcomeBranchId,
    String? apiCallOutcomeProjectionHash,
    ServiceOperationEconomicReceiptRefsV1? economicReceipt,
  }) {
    return _ServiceApiDispatchReceipt(
      endpointRef: endpointRef,
      discriminant: discriminant,
      status: status ?? RequestStatus.succeeded,
      networkRequestId: networkRequestId,
      apiCallId: apiCallId,
      apiCapabilityEndpointId: apiCapabilityEndpointId,
      callKey: callKey,
      requestHash: requestHash,
      requestModelId: requestModelId,
      apiCallOutcomeId: apiCallOutcomeId,
      responseModelId: responseModelId,
      serviceOperationId: serviceOperationId,
      serviceOperationConfigId: serviceOperationConfigId,
      serviceOperationConfigApiEndpointId: serviceOperationConfigApiEndpointId,
      serviceOperationCommitId: serviceOperationCommitId,
      serviceOperationHeadCommitId: serviceOperationHeadCommitId,
      serviceOperationBranchId: serviceOperationBranchId,
      serviceOperationProjectionHash: serviceOperationProjectionHash,
      apiCallOutcomeCommitId: apiCallOutcomeCommitId,
      apiCallOutcomeHeadCommitId: apiCallOutcomeHeadCommitId,
      apiCallOutcomeBranchId: apiCallOutcomeBranchId,
      apiCallOutcomeProjectionHash: apiCallOutcomeProjectionHash,
      economicReceipt: economicReceipt,
    );
  }

  factory ServiceApiDispatchReceipt.fromJson(Map<String, dynamic> json) =>
      _$ServiceApiDispatchReceiptFromJson({
        ...json,
        if (!json.containsKey('status')) 'status': 'succeeded',
      });
}

@freezed
abstract class ServiceOperationRequest with _$ServiceOperationRequest {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ServiceOperationRequest.def({
    required ServiceOperationContext context,
    required String service,
    Object? operation,
    ServiceApiDispatchRequest? apiDispatch,
    @UuidValueConverter() UuidValue? streamTargetId,
    @UuidValueConverter() UuidValue? streamCorrelationId,
    @UuidValueConverter() UuidValue? networkRequestId,
  }) = _ServiceOperationRequest;

  factory ServiceOperationRequest({
    required ServiceOperationContext context,
    required String service,
    Object? operation,
    ServiceApiDispatchRequest? apiDispatch,
    UuidValue? streamTargetId,
    UuidValue? streamCorrelationId,
    UuidValue? networkRequestId,
  }) {
    return _ServiceOperationRequest(
      context: context,
      service: service,
      operation: operation,
      apiDispatch: apiDispatch,
      streamTargetId: streamTargetId,
      streamCorrelationId: streamCorrelationId,
      networkRequestId: networkRequestId,
    );
  }

  factory ServiceOperationRequest.fromJson(Map<String, dynamic> json) =>
      _$ServiceOperationRequestFromJson(json);
}

@freezed
abstract class ServiceOperationResponse with _$ServiceOperationResponse {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ServiceOperationResponse.def({
    @JsonKey(
      fromJson: RequestStatusExtension.fromJson,
      toJson: RequestStatusExtension.toJson,
    )
    required RequestStatus status,
    String? error,
    Object? responsePayload,
    ServiceApiDispatchReceipt? receipt,
    @JsonKey(
      fromJson: StreamLifecycleExtension.fromJson,
      toJson: StreamLifecycleExtension.toJson,
    )
    required StreamLifecycle streamLifecycle,
  }) = _ServiceOperationResponse;

  factory ServiceOperationResponse({
    required RequestStatus status,
    String? error,
    Object? responsePayload,
    ServiceApiDispatchReceipt? receipt,
    StreamLifecycle? streamLifecycle,
  }) {
    return _ServiceOperationResponse(
      status: status,
      error: error,
      responsePayload: responsePayload,
      receipt: receipt,
      streamLifecycle: streamLifecycle ?? StreamLifecycle.autoClose,
    );
  }

  factory ServiceOperationResponse.fromJson(Map<String, dynamic> json) =>
      _$ServiceOperationResponseFromJson({
        ...json,
        if (!json.containsKey('stream_lifecycle'))
          'stream_lifecycle': 'auto_close',
      });
}
