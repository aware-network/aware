// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'network_node_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_NetworkNodeOperationContext _$NetworkNodeOperationContextFromJson(
  Map<String, dynamic> json,
) => _NetworkNodeOperationContext(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
);

Map<String, dynamic> _$NetworkNodeOperationContextToJson(
  _NetworkNodeOperationContext instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
};

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);

_NetworkNodeOperation _$NetworkNodeOperationFromJson(
  Map<String, dynamic> json,
) => _NetworkNodeOperation(
  request: json['request'] == null
      ? null
      : NetworkNodeOperationRequest.fromJson(
          json['request'] as Map<String, dynamic>,
        ),
  response: json['response'] == null
      ? null
      : NetworkNodeOperationResponse.fromJson(
          json['response'] as Map<String, dynamic>,
        ),
);

Map<String, dynamic> _$NetworkNodeOperationToJson(
  _NetworkNodeOperation instance,
) => <String, dynamic>{
  'request': instance.request?.toJson(),
  'response': instance.response?.toJson(),
};

IdentityChallengeRequest _$IdentityChallengeRequestFromJson(
  Map<String, dynamic> json,
) => IdentityChallengeRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  publicKey: json['public_key'] as String,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$IdentityChallengeRequestToJson(
  IdentityChallengeRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'public_key': instance.publicKey,
  'operation': instance.$type,
};

IdentityLoginRequest _$IdentityLoginRequestFromJson(
  Map<String, dynamic> json,
) => IdentityLoginRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  publicKey: json['public_key'] as String,
  challenge: json['challenge'] as String,
  signature: json['signature'] as String,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$IdentityLoginRequestToJson(
  IdentityLoginRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'public_key': instance.publicKey,
  'challenge': instance.challenge,
  'signature': instance.signature,
  'operation': instance.$type,
};

TokenLoginRequest _$TokenLoginRequestFromJson(Map<String, dynamic> json) =>
    TokenLoginRequest(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      nodeId: _$JsonConverterFromJson<String, UuidValue>(
        json['node_id'],
        const UuidValueConverter().fromJson,
      ),
      token: json['token'] as String,
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$TokenLoginRequestToJson(TokenLoginRequest instance) =>
    <String, dynamic>{
      'actor_id': _$JsonConverterToJson<String, UuidValue>(
        instance.actorId,
        const UuidValueConverter().toJson,
      ),
      'node_id': _$JsonConverterToJson<String, UuidValue>(
        instance.nodeId,
        const UuidValueConverter().toJson,
      ),
      'token': instance.token,
      'operation': instance.$type,
    };

WhoamiRequest _$WhoamiRequestFromJson(Map<String, dynamic> json) =>
    WhoamiRequest(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      nodeId: _$JsonConverterFromJson<String, UuidValue>(
        json['node_id'],
        const UuidValueConverter().fromJson,
      ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$WhoamiRequestToJson(WhoamiRequest instance) =>
    <String, dynamic>{
      'actor_id': _$JsonConverterToJson<String, UuidValue>(
        instance.actorId,
        const UuidValueConverter().toJson,
      ),
      'node_id': _$JsonConverterToJson<String, UuidValue>(
        instance.nodeId,
        const UuidValueConverter().toJson,
      ),
      'operation': instance.$type,
    };

MembershipStatusRequest _$MembershipStatusRequestFromJson(
  Map<String, dynamic> json,
) => MembershipStatusRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$MembershipStatusRequestToJson(
  MembershipStatusRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'operation': instance.$type,
};

MembershipCheckoutSessionCreateRequest
_$MembershipCheckoutSessionCreateRequestFromJson(Map<String, dynamic> json) =>
    MembershipCheckoutSessionCreateRequest(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      nodeId: _$JsonConverterFromJson<String, UuidValue>(
        json['node_id'],
        const UuidValueConverter().fromJson,
      ),
      planKey: json['plan_key'] as String?,
      successUrl: json['success_url'] as String?,
      cancelUrl: json['cancel_url'] as String?,
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$MembershipCheckoutSessionCreateRequestToJson(
  MembershipCheckoutSessionCreateRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'plan_key': instance.planKey,
  'success_url': instance.successUrl,
  'cancel_url': instance.cancelUrl,
  'operation': instance.$type,
};

MembershipPurchasePrepareRequest _$MembershipPurchasePrepareRequestFromJson(
  Map<String, dynamic> json,
) => MembershipPurchasePrepareRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  planKey: json['plan_key'] as String?,
  platform: json['platform'] as String?,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$MembershipPurchasePrepareRequestToJson(
  MembershipPurchasePrepareRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'plan_key': instance.planKey,
  'platform': instance.platform,
  'operation': instance.$type,
};

MembershipPurchaseClaimRequest _$MembershipPurchaseClaimRequestFromJson(
  Map<String, dynamic> json,
) => MembershipPurchaseClaimRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  provider: json['provider'] as String,
  planKey: json['plan_key'] as String?,
  appleProductId: json['apple_product_id'] as String?,
  appleReceipt: json['apple_receipt'] as String?,
  appleTransactionId: json['apple_transaction_id'] as String?,
  googleProductId: json['google_product_id'] as String?,
  googlePurchaseToken: json['google_purchase_token'] as String?,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$MembershipPurchaseClaimRequestToJson(
  MembershipPurchaseClaimRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'provider': instance.provider,
  'plan_key': instance.planKey,
  'apple_product_id': instance.appleProductId,
  'apple_receipt': instance.appleReceipt,
  'apple_transaction_id': instance.appleTransactionId,
  'google_product_id': instance.googleProductId,
  'google_purchase_token': instance.googlePurchaseToken,
  'operation': instance.$type,
};

ProvisionEnvironmentRequest _$ProvisionEnvironmentRequestFromJson(
  Map<String, dynamic> json,
) => ProvisionEnvironmentRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentConfigId: const UuidValueConverter().fromJson(
    json['environment_config_id'] as String,
  ),
  environmentTitle: json['environment_title'] as String?,
  environmentDescription: json['environment_description'] as String?,
  environmentPort: (json['environment_port'] as num?)?.toInt(),
  databaseUrl: json['database_url'] as String?,
  persistenceBackend: json['persistence_backend'] as String?,
  eagerReady: json['eager_ready'] as bool,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$ProvisionEnvironmentRequestToJson(
  ProvisionEnvironmentRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'environment_config_id': const UuidValueConverter().toJson(
    instance.environmentConfigId,
  ),
  'environment_title': instance.environmentTitle,
  'environment_description': instance.environmentDescription,
  'environment_port': instance.environmentPort,
  'database_url': instance.databaseUrl,
  'persistence_backend': instance.persistenceBackend,
  'eager_ready': instance.eagerReady,
  'operation': instance.$type,
};

GetBootEnvironmentDescriptorRequest
_$GetBootEnvironmentDescriptorRequestFromJson(Map<String, dynamic> json) =>
    GetBootEnvironmentDescriptorRequest(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      nodeId: _$JsonConverterFromJson<String, UuidValue>(
        json['node_id'],
        const UuidValueConverter().fromJson,
      ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$GetBootEnvironmentDescriptorRequestToJson(
  GetBootEnvironmentDescriptorRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'operation': instance.$type,
};

DiscoverEnvironmentConfigsRequest _$DiscoverEnvironmentConfigsRequestFromJson(
  Map<String, dynamic> json,
) => DiscoverEnvironmentConfigsRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DiscoverEnvironmentConfigsRequestToJson(
  DiscoverEnvironmentConfigsRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'operation': instance.$type,
};

DiscoverServiceApiDependencyRoutesRequest
_$DiscoverServiceApiDependencyRoutesRequestFromJson(
  Map<String, dynamic> json,
) => DiscoverServiceApiDependencyRoutesRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  consumerServicePackageId: _$JsonConverterFromJson<String, UuidValue>(
    json['consumer_service_package_id'],
    const UuidValueConverter().fromJson,
  ),
  apiPackageId: _$JsonConverterFromJson<String, UuidValue>(
    json['api_package_id'],
    const UuidValueConverter().fromJson,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DiscoverServiceApiDependencyRoutesRequestToJson(
  DiscoverServiceApiDependencyRoutesRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'consumer_service_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.consumerServicePackageId,
    const UuidValueConverter().toJson,
  ),
  'api_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.apiPackageId,
    const UuidValueConverter().toJson,
  ),
  'operation': instance.$type,
};

DiscoverHostedServicesRequest _$DiscoverHostedServicesRequestFromJson(
  Map<String, dynamic> json,
) => DiscoverHostedServicesRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DiscoverHostedServicesRequestToJson(
  DiscoverHostedServicesRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'operation': instance.$type,
};

DescribeHostedServiceRuntimesRequest
_$DescribeHostedServiceRuntimesRequestFromJson(Map<String, dynamic> json) =>
    DescribeHostedServiceRuntimesRequest(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      nodeId: _$JsonConverterFromJson<String, UuidValue>(
        json['node_id'],
        const UuidValueConverter().fromJson,
      ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$DescribeHostedServiceRuntimesRequestToJson(
  DescribeHostedServiceRuntimesRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'operation': instance.$type,
};

GetEnvironmentStatusRequest _$GetEnvironmentStatusRequestFromJson(
  Map<String, dynamic> json,
) => GetEnvironmentStatusRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$GetEnvironmentStatusRequestToJson(
  GetEnvironmentStatusRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
  'operation': instance.$type,
};

CloseStreamRequest _$CloseStreamRequestFromJson(Map<String, dynamic> json) =>
    CloseStreamRequest(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      nodeId: _$JsonConverterFromJson<String, UuidValue>(
        json['node_id'],
        const UuidValueConverter().fromJson,
      ),
      networkOperationId: const UuidValueConverter().fromJson(
        json['network_operation_id'] as String,
      ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$CloseStreamRequestToJson(CloseStreamRequest instance) =>
    <String, dynamic>{
      'actor_id': _$JsonConverterToJson<String, UuidValue>(
        instance.actorId,
        const UuidValueConverter().toJson,
      ),
      'node_id': _$JsonConverterToJson<String, UuidValue>(
        instance.nodeId,
        const UuidValueConverter().toJson,
      ),
      'network_operation_id': const UuidValueConverter().toJson(
        instance.networkOperationId,
      ),
      'operation': instance.$type,
    };

InterfaceSessionRegisterRequest _$InterfaceSessionRegisterRequestFromJson(
  Map<String, dynamic> json,
) => InterfaceSessionRegisterRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  interfaceId: const UuidValueConverter().fromJson(
    json['interface_id'] as String,
  ),
  interfaceSessionId: const UuidValueConverter().fromJson(
    json['interface_session_id'] as String,
  ),
  sessionLabel: json['session_label'] as String?,
  capabilities:
      (json['capabilities'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  protocolVersion: (json['protocol_version'] as num).toInt(),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceSessionRegisterRequestToJson(
  InterfaceSessionRegisterRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'interface_id': const UuidValueConverter().toJson(instance.interfaceId),
  'interface_session_id': const UuidValueConverter().toJson(
    instance.interfaceSessionId,
  ),
  'session_label': instance.sessionLabel,
  'capabilities': instance.capabilities,
  'protocol_version': instance.protocolVersion,
  'operation': instance.$type,
};

InterfaceSessionHeartbeatRequest _$InterfaceSessionHeartbeatRequestFromJson(
  Map<String, dynamic> json,
) => InterfaceSessionHeartbeatRequest(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  interfaceSessionId: const UuidValueConverter().fromJson(
    json['interface_session_id'] as String,
  ),
  timestamp: json['timestamp'] as String?,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceSessionHeartbeatRequestToJson(
  InterfaceSessionHeartbeatRequest instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'interface_session_id': const UuidValueConverter().toJson(
    instance.interfaceSessionId,
  ),
  'timestamp': instance.timestamp,
  'operation': instance.$type,
};

IdentityChallengeResponse _$IdentityChallengeResponseFromJson(
  Map<String, dynamic> json,
) => IdentityChallengeResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  status: json['status'] as String,
  error: json['error'] as String?,
  publicKey: json['public_key'] as String,
  challenge: json['challenge'] as String,
  expiresAt: json['expires_at'] as String?,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$IdentityChallengeResponseToJson(
  IdentityChallengeResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'status': instance.status,
  'error': instance.error,
  'public_key': instance.publicKey,
  'challenge': instance.challenge,
  'expires_at': instance.expiresAt,
  'operation': instance.$type,
};

IdentityLoginResponse _$IdentityLoginResponseFromJson(
  Map<String, dynamic> json,
) => IdentityLoginResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  status: json['status'] as String,
  error: json['error'] as String?,
  publicKey: json['public_key'] as String,
  roles:
      (json['roles'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$IdentityLoginResponseToJson(
  IdentityLoginResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'status': instance.status,
  'error': instance.error,
  'public_key': instance.publicKey,
  'roles': instance.roles,
  'operation': instance.$type,
};

TokenLoginResponse _$TokenLoginResponseFromJson(Map<String, dynamic> json) =>
    TokenLoginResponse(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      nodeId: _$JsonConverterFromJson<String, UuidValue>(
        json['node_id'],
        const UuidValueConverter().fromJson,
      ),
      status: json['status'] as String,
      error: json['error'] as String?,
      publicKey: json['public_key'] as String?,
      roles:
          (json['roles'] as List<dynamic>?)?.map((e) => e as String).toList() ??
          const [],
      tokenId: _$JsonConverterFromJson<String, UuidValue>(
        json['token_id'],
        const UuidValueConverter().fromJson,
      ),
      tokenType: json['token_type'] as String?,
      scopes:
          (json['scopes'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      contextEnvironmentId: _$JsonConverterFromJson<String, UuidValue>(
        json['context_environment_id'],
        const UuidValueConverter().fromJson,
      ),
      contextProcessId: _$JsonConverterFromJson<String, UuidValue>(
        json['context_process_id'],
        const UuidValueConverter().fromJson,
      ),
      contextThreadId: _$JsonConverterFromJson<String, UuidValue>(
        json['context_thread_id'],
        const UuidValueConverter().fromJson,
      ),
      expiresAt: json['expires_at'] as String?,
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$TokenLoginResponseToJson(TokenLoginResponse instance) =>
    <String, dynamic>{
      'actor_id': _$JsonConverterToJson<String, UuidValue>(
        instance.actorId,
        const UuidValueConverter().toJson,
      ),
      'node_id': _$JsonConverterToJson<String, UuidValue>(
        instance.nodeId,
        const UuidValueConverter().toJson,
      ),
      'status': instance.status,
      'error': instance.error,
      'public_key': instance.publicKey,
      'roles': instance.roles,
      'token_id': _$JsonConverterToJson<String, UuidValue>(
        instance.tokenId,
        const UuidValueConverter().toJson,
      ),
      'token_type': instance.tokenType,
      'scopes': instance.scopes,
      'context_environment_id': _$JsonConverterToJson<String, UuidValue>(
        instance.contextEnvironmentId,
        const UuidValueConverter().toJson,
      ),
      'context_process_id': _$JsonConverterToJson<String, UuidValue>(
        instance.contextProcessId,
        const UuidValueConverter().toJson,
      ),
      'context_thread_id': _$JsonConverterToJson<String, UuidValue>(
        instance.contextThreadId,
        const UuidValueConverter().toJson,
      ),
      'expires_at': instance.expiresAt,
      'operation': instance.$type,
    };

WhoamiResponse _$WhoamiResponseFromJson(Map<String, dynamic> json) =>
    WhoamiResponse(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      nodeId: _$JsonConverterFromJson<String, UuidValue>(
        json['node_id'],
        const UuidValueConverter().fromJson,
      ),
      status: json['status'] as String,
      error: json['error'] as String?,
      authenticated: json['authenticated'] as bool,
      publicKey: json['public_key'] as String?,
      roles:
          (json['roles'] as List<dynamic>?)?.map((e) => e as String).toList() ??
          const [],
      interfaceSessionId: _$JsonConverterFromJson<String, UuidValue>(
        json['interface_session_id'],
        const UuidValueConverter().fromJson,
      ),
      interfaceId: _$JsonConverterFromJson<String, UuidValue>(
        json['interface_id'],
        const UuidValueConverter().fromJson,
      ),
      lastSeenAt: json['last_seen_at'] as String?,
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$WhoamiResponseToJson(WhoamiResponse instance) =>
    <String, dynamic>{
      'actor_id': _$JsonConverterToJson<String, UuidValue>(
        instance.actorId,
        const UuidValueConverter().toJson,
      ),
      'node_id': _$JsonConverterToJson<String, UuidValue>(
        instance.nodeId,
        const UuidValueConverter().toJson,
      ),
      'status': instance.status,
      'error': instance.error,
      'authenticated': instance.authenticated,
      'public_key': instance.publicKey,
      'roles': instance.roles,
      'interface_session_id': _$JsonConverterToJson<String, UuidValue>(
        instance.interfaceSessionId,
        const UuidValueConverter().toJson,
      ),
      'interface_id': _$JsonConverterToJson<String, UuidValue>(
        instance.interfaceId,
        const UuidValueConverter().toJson,
      ),
      'last_seen_at': instance.lastSeenAt,
      'operation': instance.$type,
    };

MembershipStatusResponse _$MembershipStatusResponseFromJson(
  Map<String, dynamic> json,
) => MembershipStatusResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  status: json['status'] as String,
  error: json['error'] as String?,
  isActive: json['is_active'] as bool,
  isBypassed: json['is_bypassed'] as bool,
  planLabel: json['plan_label'] as String?,
  currentPeriodEnd: json['current_period_end'] as String?,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$MembershipStatusResponseToJson(
  MembershipStatusResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'status': instance.status,
  'error': instance.error,
  'is_active': instance.isActive,
  'is_bypassed': instance.isBypassed,
  'plan_label': instance.planLabel,
  'current_period_end': instance.currentPeriodEnd,
  'operation': instance.$type,
};

MembershipCheckoutSessionCreateResponse
_$MembershipCheckoutSessionCreateResponseFromJson(Map<String, dynamic> json) =>
    MembershipCheckoutSessionCreateResponse(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      nodeId: _$JsonConverterFromJson<String, UuidValue>(
        json['node_id'],
        const UuidValueConverter().fromJson,
      ),
      status: json['status'] as String,
      error: json['error'] as String?,
      checkoutUrl: json['checkout_url'] as String?,
      checkoutSessionId: json['checkout_session_id'] as String?,
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$MembershipCheckoutSessionCreateResponseToJson(
  MembershipCheckoutSessionCreateResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'status': instance.status,
  'error': instance.error,
  'checkout_url': instance.checkoutUrl,
  'checkout_session_id': instance.checkoutSessionId,
  'operation': instance.$type,
};

MembershipPurchasePrepareResponse _$MembershipPurchasePrepareResponseFromJson(
  Map<String, dynamic> json,
) => MembershipPurchasePrepareResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  status: json['status'] as String,
  error: json['error'] as String?,
  provider: json['provider'] as String,
  planLabel: json['plan_label'] as String?,
  checkoutUrl: json['checkout_url'] as String?,
  appleProductId: json['apple_product_id'] as String?,
  googleProductId: json['google_product_id'] as String?,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$MembershipPurchasePrepareResponseToJson(
  MembershipPurchasePrepareResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'status': instance.status,
  'error': instance.error,
  'provider': instance.provider,
  'plan_label': instance.planLabel,
  'checkout_url': instance.checkoutUrl,
  'apple_product_id': instance.appleProductId,
  'google_product_id': instance.googleProductId,
  'operation': instance.$type,
};

MembershipPurchaseClaimResponse _$MembershipPurchaseClaimResponseFromJson(
  Map<String, dynamic> json,
) => MembershipPurchaseClaimResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  status: json['status'] as String,
  error: json['error'] as String?,
  isActive: json['is_active'] as bool,
  planLabel: json['plan_label'] as String?,
  currentPeriodEnd: json['current_period_end'] as String?,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$MembershipPurchaseClaimResponseToJson(
  MembershipPurchaseClaimResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'status': instance.status,
  'error': instance.error,
  'is_active': instance.isActive,
  'plan_label': instance.planLabel,
  'current_period_end': instance.currentPeriodEnd,
  'operation': instance.$type,
};

ProvisionEnvironmentResponse _$ProvisionEnvironmentResponseFromJson(
  Map<String, dynamic> json,
) => ProvisionEnvironmentResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  status: json['status'] as String,
  error: json['error'] as String?,
  environmentId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_config_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentConfigTitle: json['environment_config_title'] as String?,
  environmentTitle: json['environment_title'] as String?,
  environmentEndpoint: json['environment_endpoint'] as String?,
  ocgHash: json['ocg_hash'] as String?,
  processId: _$JsonConverterFromJson<String, UuidValue>(
    json['process_id'],
    const UuidValueConverter().fromJson,
  ),
  threadId: _$JsonConverterFromJson<String, UuidValue>(
    json['thread_id'],
    const UuidValueConverter().fromJson,
  ),
  branchId: _$JsonConverterFromJson<String, UuidValue>(
    json['branch_id'],
    const UuidValueConverter().fromJson,
  ),
  opgHashes:
      (json['opg_hashes'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  provisioningReceipt: json['provisioning_receipt'] == null
      ? null
      : NodeEnvironmentProvisioningReceipt.fromJson(
          json['provisioning_receipt'] as Map<String, dynamic>,
        ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$ProvisionEnvironmentResponseToJson(
  ProvisionEnvironmentResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'status': instance.status,
  'error': instance.error,
  'environment_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentId,
    const UuidValueConverter().toJson,
  ),
  'environment_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentConfigId,
    const UuidValueConverter().toJson,
  ),
  'environment_config_title': instance.environmentConfigTitle,
  'environment_title': instance.environmentTitle,
  'environment_endpoint': instance.environmentEndpoint,
  'ocg_hash': instance.ocgHash,
  'process_id': _$JsonConverterToJson<String, UuidValue>(
    instance.processId,
    const UuidValueConverter().toJson,
  ),
  'thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.branchId,
    const UuidValueConverter().toJson,
  ),
  'opg_hashes': instance.opgHashes,
  'provisioning_receipt': instance.provisioningReceipt?.toJson(),
  'operation': instance.$type,
};

GetBootEnvironmentDescriptorResponse
_$GetBootEnvironmentDescriptorResponseFromJson(Map<String, dynamic> json) =>
    GetBootEnvironmentDescriptorResponse(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      nodeId: _$JsonConverterFromJson<String, UuidValue>(
        json['node_id'],
        const UuidValueConverter().fromJson,
      ),
      status: json['status'] as String,
      error: json['error'] as String?,
      descriptor: json['descriptor'] == null
          ? null
          : BootEnvironmentDescriptor.fromJson(
              json['descriptor'] as Map<String, dynamic>,
            ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$GetBootEnvironmentDescriptorResponseToJson(
  GetBootEnvironmentDescriptorResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'status': instance.status,
  'error': instance.error,
  'descriptor': instance.descriptor?.toJson(),
  'operation': instance.$type,
};

DiscoverEnvironmentConfigsResponse _$DiscoverEnvironmentConfigsResponseFromJson(
  Map<String, dynamic> json,
) => DiscoverEnvironmentConfigsResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  configs:
      (json['configs'] as List<dynamic>?)
          ?.map(
            (e) =>
                EnvironmentConfigDescriptor.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DiscoverEnvironmentConfigsResponseToJson(
  DiscoverEnvironmentConfigsResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'configs': instance.configs.map((e) => e.toJson()).toList(),
  'operation': instance.$type,
};

DiscoverServiceApiDependencyRoutesResponse
_$DiscoverServiceApiDependencyRoutesResponseFromJson(
  Map<String, dynamic> json,
) => DiscoverServiceApiDependencyRoutesResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  routes:
      (json['routes'] as List<dynamic>?)
          ?.map(
            (e) => ServiceApiDependencyRouteDescriptor.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DiscoverServiceApiDependencyRoutesResponseToJson(
  DiscoverServiceApiDependencyRoutesResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'routes': instance.routes.map((e) => e.toJson()).toList(),
  'operation': instance.$type,
};

DiscoverHostedServicesResponse _$DiscoverHostedServicesResponseFromJson(
  Map<String, dynamic> json,
) => DiscoverHostedServicesResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  hostedServices:
      (json['hosted_services'] as List<dynamic>?)
          ?.map(
            (e) =>
                HostedServiceAdvertisement.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$DiscoverHostedServicesResponseToJson(
  DiscoverHostedServicesResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'hosted_services': instance.hostedServices.map((e) => e.toJson()).toList(),
  'operation': instance.$type,
};

DescribeHostedServiceRuntimesResponse
_$DescribeHostedServiceRuntimesResponseFromJson(Map<String, dynamic> json) =>
    DescribeHostedServiceRuntimesResponse(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      nodeId: _$JsonConverterFromJson<String, UuidValue>(
        json['node_id'],
        const UuidValueConverter().fromJson,
      ),
      hostedServiceRuntimes:
          (json['hosted_service_runtimes'] as List<dynamic>?)
              ?.map(
                (e) => HostedServiceRuntimeStatus.fromJson(
                  e as Map<String, dynamic>,
                ),
              )
              .toList() ??
          const [],
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$DescribeHostedServiceRuntimesResponseToJson(
  DescribeHostedServiceRuntimesResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'hosted_service_runtimes': instance.hostedServiceRuntimes
      .map((e) => e.toJson())
      .toList(),
  'operation': instance.$type,
};

GetEnvironmentStatusResponse _$GetEnvironmentStatusResponseFromJson(
  Map<String, dynamic> json,
) => GetEnvironmentStatusResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  status: json['status'] as String,
  error: json['error'] as String?,
  environmentId: const UuidValueConverter().fromJson(
    json['environment_id'] as String,
  ),
  environmentConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_config_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentConfigTitle: json['environment_config_title'] as String?,
  environmentTitle: json['environment_title'] as String?,
  environmentEndpoint: json['environment_endpoint'] as String?,
  ocgHash: json['ocg_hash'] as String?,
  processId: _$JsonConverterFromJson<String, UuidValue>(
    json['process_id'],
    const UuidValueConverter().fromJson,
  ),
  threadId: _$JsonConverterFromJson<String, UuidValue>(
    json['thread_id'],
    const UuidValueConverter().fromJson,
  ),
  branchId: _$JsonConverterFromJson<String, UuidValue>(
    json['branch_id'],
    const UuidValueConverter().fromJson,
  ),
  opgHashes:
      (json['opg_hashes'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  provisioningReceipt: json['provisioning_receipt'] == null
      ? null
      : NodeEnvironmentProvisioningReceipt.fromJson(
          json['provisioning_receipt'] as Map<String, dynamic>,
        ),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$GetEnvironmentStatusResponseToJson(
  GetEnvironmentStatusResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'status': instance.status,
  'error': instance.error,
  'environment_id': const UuidValueConverter().toJson(instance.environmentId),
  'environment_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentConfigId,
    const UuidValueConverter().toJson,
  ),
  'environment_config_title': instance.environmentConfigTitle,
  'environment_title': instance.environmentTitle,
  'environment_endpoint': instance.environmentEndpoint,
  'ocg_hash': instance.ocgHash,
  'process_id': _$JsonConverterToJson<String, UuidValue>(
    instance.processId,
    const UuidValueConverter().toJson,
  ),
  'thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.branchId,
    const UuidValueConverter().toJson,
  ),
  'opg_hashes': instance.opgHashes,
  'provisioning_receipt': instance.provisioningReceipt?.toJson(),
  'operation': instance.$type,
};

CloseStreamResponse _$CloseStreamResponseFromJson(Map<String, dynamic> json) =>
    CloseStreamResponse(
      actorId: _$JsonConverterFromJson<String, UuidValue>(
        json['actor_id'],
        const UuidValueConverter().fromJson,
      ),
      nodeId: _$JsonConverterFromJson<String, UuidValue>(
        json['node_id'],
        const UuidValueConverter().fromJson,
      ),
      status: json['status'] as String,
      error: json['error'] as String?,
      networkOperationId: const UuidValueConverter().fromJson(
        json['network_operation_id'] as String,
      ),
      $type: json['operation'] as String?,
    );

Map<String, dynamic> _$CloseStreamResponseToJson(
  CloseStreamResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'status': instance.status,
  'error': instance.error,
  'network_operation_id': const UuidValueConverter().toJson(
    instance.networkOperationId,
  ),
  'operation': instance.$type,
};

InterfaceSessionRegisterResponse _$InterfaceSessionRegisterResponseFromJson(
  Map<String, dynamic> json,
) => InterfaceSessionRegisterResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  status: json['status'] as String,
  error: json['error'] as String?,
  interfaceId: const UuidValueConverter().fromJson(
    json['interface_id'] as String,
  ),
  interfaceSessionId: const UuidValueConverter().fromJson(
    json['interface_session_id'] as String,
  ),
  interfaceIdentityNetworkNodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['interface_identity_network_node_id'],
    const UuidValueConverter().fromJson,
  ),
  interfaceSessionNetworkBindingId: _$JsonConverterFromJson<String, UuidValue>(
    json['interface_session_network_binding_id'],
    const UuidValueConverter().fromJson,
  ),
  lastSeenAt: json['last_seen_at'] as String?,
  protocolVersion: (json['protocol_version'] as num).toInt(),
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceSessionRegisterResponseToJson(
  InterfaceSessionRegisterResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'status': instance.status,
  'error': instance.error,
  'interface_id': const UuidValueConverter().toJson(instance.interfaceId),
  'interface_session_id': const UuidValueConverter().toJson(
    instance.interfaceSessionId,
  ),
  'interface_identity_network_node_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.interfaceIdentityNetworkNodeId,
        const UuidValueConverter().toJson,
      ),
  'interface_session_network_binding_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.interfaceSessionNetworkBindingId,
        const UuidValueConverter().toJson,
      ),
  'last_seen_at': instance.lastSeenAt,
  'protocol_version': instance.protocolVersion,
  'operation': instance.$type,
};

InterfaceSessionHeartbeatResponse _$InterfaceSessionHeartbeatResponseFromJson(
  Map<String, dynamic> json,
) => InterfaceSessionHeartbeatResponse(
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  status: json['status'] as String,
  error: json['error'] as String?,
  interfaceSessionId: const UuidValueConverter().fromJson(
    json['interface_session_id'] as String,
  ),
  lastSeenAt: json['last_seen_at'] as String?,
  $type: json['operation'] as String?,
);

Map<String, dynamic> _$InterfaceSessionHeartbeatResponseToJson(
  InterfaceSessionHeartbeatResponse instance,
) => <String, dynamic>{
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'status': instance.status,
  'error': instance.error,
  'interface_session_id': const UuidValueConverter().toJson(
    instance.interfaceSessionId,
  ),
  'last_seen_at': instance.lastSeenAt,
  'operation': instance.$type,
};

_NodeEnvironmentProvisioningReceipt
_$NodeEnvironmentProvisioningReceiptFromJson(
  Map<String, dynamic> json,
) => _NodeEnvironmentProvisioningReceipt(
  status: json['status'] as String,
  error: json['error'] as String?,
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  nodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['node_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['environment_config_id'],
    const UuidValueConverter().fromJson,
  ),
  environmentConfigTitle: json['environment_config_title'] as String?,
  environmentTitle: json['environment_title'] as String?,
  environmentEndpoint: json['environment_endpoint'] as String?,
  ocgHash: json['ocg_hash'] as String?,
  opgHashes:
      (json['opg_hashes'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  runtimeArtifactRefsJson: json['runtime_artifact_refs_json'] as String?,
  serviceApiProviderRefsJson: json['service_api_provider_refs_json'] as String?,
  processId: _$JsonConverterFromJson<String, UuidValue>(
    json['process_id'],
    const UuidValueConverter().fromJson,
  ),
  threadId: _$JsonConverterFromJson<String, UuidValue>(
    json['thread_id'],
    const UuidValueConverter().fromJson,
  ),
  branchId: _$JsonConverterFromJson<String, UuidValue>(
    json['branch_id'],
    const UuidValueConverter().fromJson,
  ),
  outerWrapperKind: json['outer_wrapper_kind'] as String?,
  environmentHandle: json['environment_handle'] as String?,
  workspaceRoot: json['workspace_root'] as String?,
  workspaceTomlPath: json['workspace_toml_path'] as String?,
  workspaceId: json['workspace_id'] as String?,
  workspacePackageId: json['workspace_package_id'] as String?,
  workspaceBuildInvocationId: json['workspace_build_invocation_id'] as String?,
  workspaceBuildReceiptPath: json['workspace_build_receipt_path'] as String?,
  workspaceBuildLatestPath: json['workspace_build_latest_path'] as String?,
  workspaceTargetLatestPath: json['workspace_target_latest_path'] as String?,
  workspaceTargetRef: json['workspace_target_ref'] as String?,
  readinessReceipt: json['readiness_receipt'] as Map<String, dynamic>?,
  networkNodeEnvironmentReceipt:
      json['network_node_environment_receipt'] as Map<String, dynamic>?,
);

Map<String, dynamic> _$NodeEnvironmentProvisioningReceiptToJson(
  _NodeEnvironmentProvisioningReceipt instance,
) => <String, dynamic>{
  'status': instance.status,
  'error': instance.error,
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.nodeId,
    const UuidValueConverter().toJson,
  ),
  'environment_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentId,
    const UuidValueConverter().toJson,
  ),
  'environment_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.environmentConfigId,
    const UuidValueConverter().toJson,
  ),
  'environment_config_title': instance.environmentConfigTitle,
  'environment_title': instance.environmentTitle,
  'environment_endpoint': instance.environmentEndpoint,
  'ocg_hash': instance.ocgHash,
  'opg_hashes': instance.opgHashes,
  'runtime_artifact_refs_json': instance.runtimeArtifactRefsJson,
  'service_api_provider_refs_json': instance.serviceApiProviderRefsJson,
  'process_id': _$JsonConverterToJson<String, UuidValue>(
    instance.processId,
    const UuidValueConverter().toJson,
  ),
  'thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.branchId,
    const UuidValueConverter().toJson,
  ),
  'outer_wrapper_kind': instance.outerWrapperKind,
  'environment_handle': instance.environmentHandle,
  'workspace_root': instance.workspaceRoot,
  'workspace_toml_path': instance.workspaceTomlPath,
  'workspace_id': instance.workspaceId,
  'workspace_package_id': instance.workspacePackageId,
  'workspace_build_invocation_id': instance.workspaceBuildInvocationId,
  'workspace_build_receipt_path': instance.workspaceBuildReceiptPath,
  'workspace_build_latest_path': instance.workspaceBuildLatestPath,
  'workspace_target_latest_path': instance.workspaceTargetLatestPath,
  'workspace_target_ref': instance.workspaceTargetRef,
  'readiness_receipt': instance.readinessReceipt,
  'network_node_environment_receipt': instance.networkNodeEnvironmentReceipt,
};

_EnvironmentConfigDescriptor _$EnvironmentConfigDescriptorFromJson(
  Map<String, dynamic> json,
) => _EnvironmentConfigDescriptor(
  environmentConfigId: const UuidValueConverter().fromJson(
    json['environment_config_id'] as String,
  ),
  title: json['title'] as String?,
  canonicalLanguage: json['canonical_language'] as String?,
  ocgHash: json['ocg_hash'] as String?,
  opgHashes:
      (json['opg_hashes'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  outerWrapperKind: json['outer_wrapper_kind'] as String?,
  environmentHandle: json['environment_handle'] as String?,
  workspaceTargetRef: json['workspace_target_ref'] as String?,
);

Map<String, dynamic> _$EnvironmentConfigDescriptorToJson(
  _EnvironmentConfigDescriptor instance,
) => <String, dynamic>{
  'environment_config_id': const UuidValueConverter().toJson(
    instance.environmentConfigId,
  ),
  'title': instance.title,
  'canonical_language': instance.canonicalLanguage,
  'ocg_hash': instance.ocgHash,
  'opg_hashes': instance.opgHashes,
  'outer_wrapper_kind': instance.outerWrapperKind,
  'environment_handle': instance.environmentHandle,
  'workspace_target_ref': instance.workspaceTargetRef,
};

_BootEnvironmentDescriptor _$BootEnvironmentDescriptorFromJson(
  Map<String, dynamic> json,
) => _BootEnvironmentDescriptor(
  kernelEnvironmentConfigId: const UuidValueConverter().fromJson(
    json['kernel_environment_config_id'] as String,
  ),
  bootEnvironmentId: const UuidValueConverter().fromJson(
    json['boot_environment_id'] as String,
  ),
  kernelEnvironmentConfigTitle:
      json['kernel_environment_config_title'] as String?,
  bootEnvironmentTitle: json['boot_environment_title'] as String?,
  processId: _$JsonConverterFromJson<String, UuidValue>(
    json['process_id'],
    const UuidValueConverter().fromJson,
  ),
  threadId: _$JsonConverterFromJson<String, UuidValue>(
    json['thread_id'],
    const UuidValueConverter().fromJson,
  ),
  branchId: _$JsonConverterFromJson<String, UuidValue>(
    json['branch_id'],
    const UuidValueConverter().fromJson,
  ),
  opgHashes:
      (json['opg_hashes'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
);

Map<String, dynamic> _$BootEnvironmentDescriptorToJson(
  _BootEnvironmentDescriptor instance,
) => <String, dynamic>{
  'kernel_environment_config_id': const UuidValueConverter().toJson(
    instance.kernelEnvironmentConfigId,
  ),
  'boot_environment_id': const UuidValueConverter().toJson(
    instance.bootEnvironmentId,
  ),
  'kernel_environment_config_title': instance.kernelEnvironmentConfigTitle,
  'boot_environment_title': instance.bootEnvironmentTitle,
  'process_id': _$JsonConverterToJson<String, UuidValue>(
    instance.processId,
    const UuidValueConverter().toJson,
  ),
  'thread_id': _$JsonConverterToJson<String, UuidValue>(
    instance.threadId,
    const UuidValueConverter().toJson,
  ),
  'branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.branchId,
    const UuidValueConverter().toJson,
  ),
  'opg_hashes': instance.opgHashes,
};

_ServiceApiDependencyRouteDescriptor
_$ServiceApiDependencyRouteDescriptorFromJson(
  Map<String, dynamic> json,
) => _ServiceApiDependencyRouteDescriptor(
  consumerServicePackageId: const UuidValueConverter().fromJson(
    json['consumer_service_package_id'] as String,
  ),
  consumerServicePackageName: json['consumer_service_package_name'] as String,
  providerServicePackageId: const UuidValueConverter().fromJson(
    json['provider_service_package_id'] as String,
  ),
  providerServicePackageName: json['provider_service_package_name'] as String,
  apiPackageId: const UuidValueConverter().fromJson(
    json['api_package_id'] as String,
  ),
  apiPackageName: json['api_package_name'] as String?,
  routeKind: json['route_kind'] as String,
  hostId: json['host_id'] as String,
  hostVersion: json['host_version'] as String?,
  protocolVersion: json['protocol_version'] as String,
  socketPath: json['socket_path'] as String?,
  consumerNodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['consumer_node_id'],
    const UuidValueConverter().fromJson,
  ),
  providerNodeId: _$JsonConverterFromJson<String, UuidValue>(
    json['provider_node_id'],
    const UuidValueConverter().fromJson,
  ),
  providerNodeBaseUrl: json['provider_node_base_url'] as String?,
  routeConnectionId: _$JsonConverterFromJson<String, UuidValue>(
    json['route_connection_id'],
    const UuidValueConverter().fromJson,
  ),
  requestTimeoutS: (json['request_timeout_s'] as num).toDouble(),
  serviceNames:
      (json['service_names'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  endpointRefsByService:
      json['endpoint_refs_by_service'] as Map<String, dynamic>,
  streamEndpointRefsByService:
      json['stream_endpoint_refs_by_service'] as Map<String, dynamic>,
);

Map<String, dynamic> _$ServiceApiDependencyRouteDescriptorToJson(
  _ServiceApiDependencyRouteDescriptor instance,
) => <String, dynamic>{
  'consumer_service_package_id': const UuidValueConverter().toJson(
    instance.consumerServicePackageId,
  ),
  'consumer_service_package_name': instance.consumerServicePackageName,
  'provider_service_package_id': const UuidValueConverter().toJson(
    instance.providerServicePackageId,
  ),
  'provider_service_package_name': instance.providerServicePackageName,
  'api_package_id': const UuidValueConverter().toJson(instance.apiPackageId),
  'api_package_name': instance.apiPackageName,
  'route_kind': instance.routeKind,
  'host_id': instance.hostId,
  'host_version': instance.hostVersion,
  'protocol_version': instance.protocolVersion,
  'socket_path': instance.socketPath,
  'consumer_node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.consumerNodeId,
    const UuidValueConverter().toJson,
  ),
  'provider_node_id': _$JsonConverterToJson<String, UuidValue>(
    instance.providerNodeId,
    const UuidValueConverter().toJson,
  ),
  'provider_node_base_url': instance.providerNodeBaseUrl,
  'route_connection_id': _$JsonConverterToJson<String, UuidValue>(
    instance.routeConnectionId,
    const UuidValueConverter().toJson,
  ),
  'request_timeout_s': instance.requestTimeoutS,
  'service_names': instance.serviceNames,
  'endpoint_refs_by_service': instance.endpointRefsByService,
  'stream_endpoint_refs_by_service': instance.streamEndpointRefsByService,
};

_HostedServiceAdvertisement _$HostedServiceAdvertisementFromJson(
  Map<String, dynamic> json,
) => _HostedServiceAdvertisement(
  servicePackageId: _$JsonConverterFromJson<String, UuidValue>(
    json['service_package_id'],
    const UuidValueConverter().fromJson,
  ),
  serviceId: _$JsonConverterFromJson<String, UuidValue>(
    json['service_id'],
    const UuidValueConverter().fromJson,
  ),
  serviceName: json['service_name'] as String,
  servicePackageNames:
      (json['service_package_names'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  endpointRefs:
      (json['endpoint_refs'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  hostId: json['host_id'] as String,
  hostVersion: json['host_version'] as String?,
  protocolVersion: json['protocol_version'] as String,
  supportsStreamEvents: json['supports_stream_events'] as bool,
);

Map<String, dynamic> _$HostedServiceAdvertisementToJson(
  _HostedServiceAdvertisement instance,
) => <String, dynamic>{
  'service_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.servicePackageId,
    const UuidValueConverter().toJson,
  ),
  'service_id': _$JsonConverterToJson<String, UuidValue>(
    instance.serviceId,
    const UuidValueConverter().toJson,
  ),
  'service_name': instance.serviceName,
  'service_package_names': instance.servicePackageNames,
  'endpoint_refs': instance.endpointRefs,
  'host_id': instance.hostId,
  'host_version': instance.hostVersion,
  'protocol_version': instance.protocolVersion,
  'supports_stream_events': instance.supportsStreamEvents,
};

_HostedServiceRuntimeServiceStatus _$HostedServiceRuntimeServiceStatusFromJson(
  Map<String, dynamic> json,
) => _HostedServiceRuntimeServiceStatus(
  serviceName: json['service_name'] as String,
  endpointRefs:
      (json['endpoint_refs'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  streamEndpointRefs:
      (json['stream_endpoint_refs'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
);

Map<String, dynamic> _$HostedServiceRuntimeServiceStatusToJson(
  _HostedServiceRuntimeServiceStatus instance,
) => <String, dynamic>{
  'service_name': instance.serviceName,
  'endpoint_refs': instance.endpointRefs,
  'stream_endpoint_refs': instance.streamEndpointRefs,
};

_HostedServiceRuntimeStatus _$HostedServiceRuntimeStatusFromJson(
  Map<String, dynamic> json,
) => _HostedServiceRuntimeStatus(
  hostId: json['host_id'] as String,
  hostVersion: json['host_version'] as String?,
  protocolVersion: json['protocol_version'] as String,
  readinessStatus: json['readiness_status'] as String,
  isReady: json['is_ready'] as bool,
  isAlive: json['is_alive'] as bool,
  supportsStreamEvents: json['supports_stream_events'] as bool,
  summary: json['summary'] as String?,
  error: json['error'] as String?,
  updatedAt: json['updated_at'] as String?,
  services:
      (json['services'] as List<dynamic>?)
          ?.map(
            (e) => HostedServiceRuntimeServiceStatus.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$HostedServiceRuntimeStatusToJson(
  _HostedServiceRuntimeStatus instance,
) => <String, dynamic>{
  'host_id': instance.hostId,
  'host_version': instance.hostVersion,
  'protocol_version': instance.protocolVersion,
  'readiness_status': instance.readinessStatus,
  'is_ready': instance.isReady,
  'is_alive': instance.isAlive,
  'supports_stream_events': instance.supportsStreamEvents,
  'summary': instance.summary,
  'error': instance.error,
  'updated_at': instance.updatedAt,
  'services': instance.services.map((e) => e.toJson()).toList(),
};
