// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'service_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_ServiceOperationContext _$ServiceOperationContextFromJson(
  Map<String, dynamic> json,
) => _ServiceOperationContext(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  branchId: const UuidValueConverter().fromJson(json['branch_id'] as String),
  projectionHash: json['projection_hash'] as String,
);

Map<String, dynamic> _$ServiceOperationContextToJson(
  _ServiceOperationContext instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': const UuidValueConverter().toJson(instance.branchId),
  'projection_hash': instance.projectionHash,
};

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);

_ServiceOperationEconomicReceiptRefsV1
_$ServiceOperationEconomicReceiptRefsV1FromJson(Map<String, dynamic> json) =>
    _ServiceOperationEconomicReceiptRefsV1(
      contractVersion: json['contract_version'] as String,
      serviceOperationId: const UuidValueConverter().fromJson(
        json['service_operation_id'] as String,
      ),
      serviceContractId: const UuidValueConverter().fromJson(
        json['service_contract_id'] as String,
      ),
      permitId: const UuidValueConverter().fromJson(
        json['permit_id'] as String,
      ),
      priceId: const UuidValueConverter().fromJson(json['price_id'] as String),
      priceScheduleId: const UuidValueConverter().fromJson(
        json['price_schedule_id'] as String,
      ),
      rateSnapshotId: const UuidValueConverter().fromJson(
        json['rate_snapshot_id'] as String,
      ),
      priceReservationId: const UuidValueConverter().fromJson(
        json['price_reservation_id'] as String,
      ),
      smartContractReservationId: const UuidValueConverter().fromJson(
        json['smart_contract_reservation_id'] as String,
      ),
      settlementId: const UuidValueConverter().fromJson(
        json['settlement_id'] as String,
      ),
      transactionId: _$JsonConverterFromJson<String, UuidValue>(
        json['transaction_id'],
        const UuidValueConverter().fromJson,
      ),
      payerWalletBalanceId: const UuidValueConverter().fromJson(
        json['payer_wallet_balance_id'] as String,
      ),
      receiverWalletBalanceId: const UuidValueConverter().fromJson(
        json['receiver_wallet_balance_id'] as String,
      ),
      status: json['status'] as String,
      idempotentReplay: json['idempotent_replay'] as bool,
    );

Map<String, dynamic> _$ServiceOperationEconomicReceiptRefsV1ToJson(
  _ServiceOperationEconomicReceiptRefsV1 instance,
) => <String, dynamic>{
  'contract_version': instance.contractVersion,
  'service_operation_id': const UuidValueConverter().toJson(
    instance.serviceOperationId,
  ),
  'service_contract_id': const UuidValueConverter().toJson(
    instance.serviceContractId,
  ),
  'permit_id': const UuidValueConverter().toJson(instance.permitId),
  'price_id': const UuidValueConverter().toJson(instance.priceId),
  'price_schedule_id': const UuidValueConverter().toJson(
    instance.priceScheduleId,
  ),
  'rate_snapshot_id': const UuidValueConverter().toJson(
    instance.rateSnapshotId,
  ),
  'price_reservation_id': const UuidValueConverter().toJson(
    instance.priceReservationId,
  ),
  'smart_contract_reservation_id': const UuidValueConverter().toJson(
    instance.smartContractReservationId,
  ),
  'settlement_id': const UuidValueConverter().toJson(instance.settlementId),
  'transaction_id': _$JsonConverterToJson<String, UuidValue>(
    instance.transactionId,
    const UuidValueConverter().toJson,
  ),
  'payer_wallet_balance_id': const UuidValueConverter().toJson(
    instance.payerWalletBalanceId,
  ),
  'receiver_wallet_balance_id': const UuidValueConverter().toJson(
    instance.receiverWalletBalanceId,
  ),
  'status': instance.status,
  'idempotent_replay': instance.idempotentReplay,
};

_ServiceOperation _$ServiceOperationFromJson(Map<String, dynamic> json) =>
    _ServiceOperation(
      request: json['request'] == null
          ? null
          : ServiceOperationRequest.fromJson(
              json['request'] as Map<String, dynamic>,
            ),
      response: json['response'] == null
          ? null
          : ServiceOperationResponse.fromJson(
              json['response'] as Map<String, dynamic>,
            ),
    );

Map<String, dynamic> _$ServiceOperationToJson(_ServiceOperation instance) =>
    <String, dynamic>{
      'request': instance.request?.toJson(),
      'response': instance.response?.toJson(),
    };

_ServiceApiDispatchEnvelope _$ServiceApiDispatchEnvelopeFromJson(
  Map<String, dynamic> json,
) => _ServiceApiDispatchEnvelope(
  apiCallId: const UuidValueConverter().fromJson(json['api_call_id'] as String),
  apiCapabilityEndpointId: const UuidValueConverter().fromJson(
    json['api_capability_endpoint_id'] as String,
  ),
  callKey: const UuidValueConverter().fromJson(json['call_key'] as String),
  requestHash: json['request_hash'] as String,
  commitId: const UuidValueConverter().fromJson(json['commit_id'] as String),
  headCommitId: const UuidValueConverter().fromJson(
    json['head_commit_id'] as String,
  ),
  branchId: const UuidValueConverter().fromJson(json['branch_id'] as String),
  projectionHash: json['projection_hash'] as String,
  apiName: json['api_name'] as String,
  capabilityName: json['capability_name'] as String,
  endpointName: json['endpoint_name'] as String,
  endpointRef: json['endpoint_ref'] as String,
  discriminant: json['discriminant'] as String,
  sourcePath: json['source_path'] as String,
  requestModelId: const UuidValueConverter().fromJson(
    json['request_model_id'] as String,
  ),
  requestClassConfigId: const UuidValueConverter().fromJson(
    json['request_class_config_id'] as String,
  ),
  requestClassRef: json['request_class_ref'] as String,
  requestSourcePath: json['request_source_path'] as String,
  responseClassRef: json['response_class_ref'] as String?,
  responseSourcePath: json['response_source_path'] as String?,
);

Map<String, dynamic> _$ServiceApiDispatchEnvelopeToJson(
  _ServiceApiDispatchEnvelope instance,
) => <String, dynamic>{
  'api_call_id': const UuidValueConverter().toJson(instance.apiCallId),
  'api_capability_endpoint_id': const UuidValueConverter().toJson(
    instance.apiCapabilityEndpointId,
  ),
  'call_key': const UuidValueConverter().toJson(instance.callKey),
  'request_hash': instance.requestHash,
  'commit_id': const UuidValueConverter().toJson(instance.commitId),
  'head_commit_id': const UuidValueConverter().toJson(instance.headCommitId),
  'branch_id': const UuidValueConverter().toJson(instance.branchId),
  'projection_hash': instance.projectionHash,
  'api_name': instance.apiName,
  'capability_name': instance.capabilityName,
  'endpoint_name': instance.endpointName,
  'endpoint_ref': instance.endpointRef,
  'discriminant': instance.discriminant,
  'source_path': instance.sourcePath,
  'request_model_id': const UuidValueConverter().toJson(
    instance.requestModelId,
  ),
  'request_class_config_id': const UuidValueConverter().toJson(
    instance.requestClassConfigId,
  ),
  'request_class_ref': instance.requestClassRef,
  'request_source_path': instance.requestSourcePath,
  'response_class_ref': instance.responseClassRef,
  'response_source_path': instance.responseSourcePath,
};

_ServiceApiDispatchFulfillmentBinding
_$ServiceApiDispatchFulfillmentBindingFromJson(
  Map<String, dynamic> json,
) => _ServiceApiDispatchFulfillmentBinding(
  name: json['name'] as String,
  graphTarget: json['graph_target'] as String,
  graphCapabilityFunctionName: json['graph_capability_function_name'] as String,
  graphFunctionPythonRef: json['graph_function_python_ref'] as String,
  graphFunctionRuntimeTarget: json['graph_function_runtime_target'] as String,
  methodName: json['method_name'] as String,
  requestTypeRef: json['request_type_ref'] as String,
  responseTypeRef: json['response_type_ref'] as String,
  sourcePath: json['source_path'] as String,
  apiCapabilityEndpointFunctionId: _$JsonConverterFromJson<String, UuidValue>(
    json['api_capability_endpoint_function_id'],
    const UuidValueConverter().fromJson,
  ),
);

Map<String, dynamic> _$ServiceApiDispatchFulfillmentBindingToJson(
  _ServiceApiDispatchFulfillmentBinding instance,
) => <String, dynamic>{
  'name': instance.name,
  'graph_target': instance.graphTarget,
  'graph_capability_function_name': instance.graphCapabilityFunctionName,
  'graph_function_python_ref': instance.graphFunctionPythonRef,
  'graph_function_runtime_target': instance.graphFunctionRuntimeTarget,
  'method_name': instance.methodName,
  'request_type_ref': instance.requestTypeRef,
  'response_type_ref': instance.responseTypeRef,
  'source_path': instance.sourcePath,
  'api_capability_endpoint_function_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.apiCapabilityEndpointFunctionId,
        const UuidValueConverter().toJson,
      ),
};

_ServiceApiDispatchRequest _$ServiceApiDispatchRequestFromJson(
  Map<String, dynamic> json,
) => _ServiceApiDispatchRequest(
  operationKey: json['operation_key'] as String,
  envelope: ServiceApiDispatchEnvelope.fromJson(
    json['envelope'] as Map<String, dynamic>,
  ),
  requestPayload: json['request_payload'] as Map<String, dynamic>,
  fulfillmentBindings:
      (json['fulfillment_bindings'] as List<dynamic>?)
          ?.map(
            (e) => ServiceApiDispatchFulfillmentBinding.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$ServiceApiDispatchRequestToJson(
  _ServiceApiDispatchRequest instance,
) => <String, dynamic>{
  'operation_key': instance.operationKey,
  'envelope': instance.envelope.toJson(),
  'request_payload': instance.requestPayload,
  'fulfillment_bindings': instance.fulfillmentBindings
      .map((e) => e.toJson())
      .toList(),
};

_ServiceApiDispatchReceipt _$ServiceApiDispatchReceiptFromJson(
  Map<String, dynamic> json,
) => _ServiceApiDispatchReceipt(
  endpointRef: json['endpoint_ref'] as String,
  discriminant: json['discriminant'] as String,
  status: RequestStatusExtension.fromJson(json['status'] as String),
  networkRequestId: _$JsonConverterFromJson<String, UuidValue>(
    json['network_request_id'],
    const UuidValueConverter().fromJson,
  ),
  apiCallId: _$JsonConverterFromJson<String, UuidValue>(
    json['api_call_id'],
    const UuidValueConverter().fromJson,
  ),
  apiCapabilityEndpointId: _$JsonConverterFromJson<String, UuidValue>(
    json['api_capability_endpoint_id'],
    const UuidValueConverter().fromJson,
  ),
  callKey: _$JsonConverterFromJson<String, UuidValue>(
    json['call_key'],
    const UuidValueConverter().fromJson,
  ),
  requestHash: json['request_hash'] as String?,
  requestModelId: _$JsonConverterFromJson<String, UuidValue>(
    json['request_model_id'],
    const UuidValueConverter().fromJson,
  ),
  apiCallOutcomeId: _$JsonConverterFromJson<String, UuidValue>(
    json['api_call_outcome_id'],
    const UuidValueConverter().fromJson,
  ),
  responseModelId: _$JsonConverterFromJson<String, UuidValue>(
    json['response_model_id'],
    const UuidValueConverter().fromJson,
  ),
  serviceOperationId: _$JsonConverterFromJson<String, UuidValue>(
    json['service_operation_id'],
    const UuidValueConverter().fromJson,
  ),
  serviceOperationConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['service_operation_config_id'],
    const UuidValueConverter().fromJson,
  ),
  serviceOperationConfigApiEndpointId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['service_operation_config_api_endpoint_id'],
        const UuidValueConverter().fromJson,
      ),
  serviceOperationCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['service_operation_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  serviceOperationHeadCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['service_operation_head_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  serviceOperationBranchId: _$JsonConverterFromJson<String, UuidValue>(
    json['service_operation_branch_id'],
    const UuidValueConverter().fromJson,
  ),
  serviceOperationProjectionHash:
      json['service_operation_projection_hash'] as String?,
  apiCallOutcomeCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['api_call_outcome_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  apiCallOutcomeHeadCommitId: _$JsonConverterFromJson<String, UuidValue>(
    json['api_call_outcome_head_commit_id'],
    const UuidValueConverter().fromJson,
  ),
  apiCallOutcomeBranchId: _$JsonConverterFromJson<String, UuidValue>(
    json['api_call_outcome_branch_id'],
    const UuidValueConverter().fromJson,
  ),
  apiCallOutcomeProjectionHash:
      json['api_call_outcome_projection_hash'] as String?,
  economicReceipt: json['economic_receipt'] == null
      ? null
      : ServiceOperationEconomicReceiptRefsV1.fromJson(
          json['economic_receipt'] as Map<String, dynamic>,
        ),
);

Map<String, dynamic> _$ServiceApiDispatchReceiptToJson(
  _ServiceApiDispatchReceipt instance,
) => <String, dynamic>{
  'endpoint_ref': instance.endpointRef,
  'discriminant': instance.discriminant,
  'status': RequestStatusExtension.toJson(instance.status),
  'network_request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.networkRequestId,
    const UuidValueConverter().toJson,
  ),
  'api_call_id': _$JsonConverterToJson<String, UuidValue>(
    instance.apiCallId,
    const UuidValueConverter().toJson,
  ),
  'api_capability_endpoint_id': _$JsonConverterToJson<String, UuidValue>(
    instance.apiCapabilityEndpointId,
    const UuidValueConverter().toJson,
  ),
  'call_key': _$JsonConverterToJson<String, UuidValue>(
    instance.callKey,
    const UuidValueConverter().toJson,
  ),
  'request_hash': instance.requestHash,
  'request_model_id': _$JsonConverterToJson<String, UuidValue>(
    instance.requestModelId,
    const UuidValueConverter().toJson,
  ),
  'api_call_outcome_id': _$JsonConverterToJson<String, UuidValue>(
    instance.apiCallOutcomeId,
    const UuidValueConverter().toJson,
  ),
  'response_model_id': _$JsonConverterToJson<String, UuidValue>(
    instance.responseModelId,
    const UuidValueConverter().toJson,
  ),
  'service_operation_id': _$JsonConverterToJson<String, UuidValue>(
    instance.serviceOperationId,
    const UuidValueConverter().toJson,
  ),
  'service_operation_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.serviceOperationConfigId,
    const UuidValueConverter().toJson,
  ),
  'service_operation_config_api_endpoint_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.serviceOperationConfigApiEndpointId,
        const UuidValueConverter().toJson,
      ),
  'service_operation_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.serviceOperationCommitId,
    const UuidValueConverter().toJson,
  ),
  'service_operation_head_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.serviceOperationHeadCommitId,
    const UuidValueConverter().toJson,
  ),
  'service_operation_branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.serviceOperationBranchId,
    const UuidValueConverter().toJson,
  ),
  'service_operation_projection_hash': instance.serviceOperationProjectionHash,
  'api_call_outcome_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.apiCallOutcomeCommitId,
    const UuidValueConverter().toJson,
  ),
  'api_call_outcome_head_commit_id': _$JsonConverterToJson<String, UuidValue>(
    instance.apiCallOutcomeHeadCommitId,
    const UuidValueConverter().toJson,
  ),
  'api_call_outcome_branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.apiCallOutcomeBranchId,
    const UuidValueConverter().toJson,
  ),
  'api_call_outcome_projection_hash': instance.apiCallOutcomeProjectionHash,
  'economic_receipt': instance.economicReceipt?.toJson(),
};

_ServiceOperationRequest _$ServiceOperationRequestFromJson(
  Map<String, dynamic> json,
) => _ServiceOperationRequest(
  context: ServiceOperationContext.fromJson(
    json['context'] as Map<String, dynamic>,
  ),
  service: json['service'] as String,
  operation: json['operation'],
  apiDispatch: json['api_dispatch'] == null
      ? null
      : ServiceApiDispatchRequest.fromJson(
          json['api_dispatch'] as Map<String, dynamic>,
        ),
  streamTargetId: _$JsonConverterFromJson<String, UuidValue>(
    json['stream_target_id'],
    const UuidValueConverter().fromJson,
  ),
  streamCorrelationId: _$JsonConverterFromJson<String, UuidValue>(
    json['stream_correlation_id'],
    const UuidValueConverter().fromJson,
  ),
  networkRequestId: _$JsonConverterFromJson<String, UuidValue>(
    json['network_request_id'],
    const UuidValueConverter().fromJson,
  ),
);

Map<String, dynamic> _$ServiceOperationRequestToJson(
  _ServiceOperationRequest instance,
) => <String, dynamic>{
  'context': instance.context.toJson(),
  'service': instance.service,
  'operation': instance.operation,
  'api_dispatch': instance.apiDispatch?.toJson(),
  'stream_target_id': _$JsonConverterToJson<String, UuidValue>(
    instance.streamTargetId,
    const UuidValueConverter().toJson,
  ),
  'stream_correlation_id': _$JsonConverterToJson<String, UuidValue>(
    instance.streamCorrelationId,
    const UuidValueConverter().toJson,
  ),
  'network_request_id': _$JsonConverterToJson<String, UuidValue>(
    instance.networkRequestId,
    const UuidValueConverter().toJson,
  ),
};

_ServiceOperationResponse _$ServiceOperationResponseFromJson(
  Map<String, dynamic> json,
) => _ServiceOperationResponse(
  status: RequestStatusExtension.fromJson(json['status'] as String),
  error: json['error'] as String?,
  responsePayload: json['response_payload'],
  receipt: json['receipt'] == null
      ? null
      : ServiceApiDispatchReceipt.fromJson(
          json['receipt'] as Map<String, dynamic>,
        ),
  streamLifecycle: StreamLifecycleExtension.fromJson(
    json['stream_lifecycle'] as String,
  ),
);

Map<String, dynamic> _$ServiceOperationResponseToJson(
  _ServiceOperationResponse instance,
) => <String, dynamic>{
  'status': RequestStatusExtension.toJson(instance.status),
  'error': instance.error,
  'response_payload': instance.responsePayload,
  'receipt': instance.receipt?.toJson(),
  'stream_lifecycle': StreamLifecycleExtension.toJson(instance.streamLifecycle),
};
