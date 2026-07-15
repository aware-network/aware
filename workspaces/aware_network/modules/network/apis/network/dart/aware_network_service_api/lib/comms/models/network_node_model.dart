// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'network_node_model.freezed.dart';
part 'network_node_model.g.dart';

/// Wire DTOs for Network Node operations (control-plane; graph/ORM agnostic).
@freezed
abstract class NetworkNodeOperationContext with _$NetworkNodeOperationContext {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationContext.def({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
  }) = _NetworkNodeOperationContext;

  factory NetworkNodeOperationContext({UuidValue? actorId, UuidValue? nodeId}) {
    return _NetworkNodeOperationContext(actorId: actorId, nodeId: nodeId);
  }

  factory NetworkNodeOperationContext.fromJson(Map<String, dynamic> json) =>
      _$NetworkNodeOperationContextFromJson(json);
}

/// NetworkNodeOperation is either a request or a response.
@freezed
abstract class NetworkNodeOperation with _$NetworkNodeOperation {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperation.def({
    NetworkNodeOperationRequest? request,
    NetworkNodeOperationResponse? response,
  }) = _NetworkNodeOperation;

  factory NetworkNodeOperation({
    NetworkNodeOperationRequest? request,
    NetworkNodeOperationResponse? response,
  }) {
    return _NetworkNodeOperation(request: request, response: response);
  }

  factory NetworkNodeOperation.fromJson(Map<String, dynamic> json) =>
      _$NetworkNodeOperationFromJson(json);
}

/// Request union base (operation + context).
@Freezed(unionKey: 'operation')
abstract class NetworkNodeOperationRequest with _$NetworkNodeOperationRequest {
  @FreezedUnionValue('identity_challenge')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationRequest.identityChallenge({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    required String publicKey,
  }) = IdentityChallengeRequest;

  @FreezedUnionValue('identity_login')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationRequest.identityLogin({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    required String publicKey,
    required String challenge,
    required String signature,
  }) = IdentityLoginRequest;

  @FreezedUnionValue('token_login')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationRequest.tokenLogin({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    required String token,
  }) = TokenLoginRequest;

  @FreezedUnionValue('whoami')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationRequest.whoami({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
  }) = WhoamiRequest;

  @FreezedUnionValue('membership_status')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationRequest.membershipStatus({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
  }) = MembershipStatusRequest;

  @FreezedUnionValue('membership_checkout_session_create')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationRequest.membershipCheckoutSessionCreate({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    String? planKey,
    String? successUrl,
    String? cancelUrl,
  }) = MembershipCheckoutSessionCreateRequest;

  @FreezedUnionValue('membership_purchase_prepare')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationRequest.membershipPurchasePrepare({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    String? planKey,
    String? platform,
  }) = MembershipPurchasePrepareRequest;

  @FreezedUnionValue('membership_purchase_claim')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationRequest.membershipPurchaseClaim({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    required String provider,
    String? planKey,
    String? appleProductId,
    String? appleReceipt,
    String? appleTransactionId,
    String? googleProductId,
    String? googlePurchaseToken,
  }) = MembershipPurchaseClaimRequest;

  @FreezedUnionValue('provision_environment')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationRequest.provisionEnvironment({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    @UuidValueConverter() required UuidValue environmentConfigId,
    String? environmentTitle,
    String? environmentDescription,
    int? environmentPort,
    String? databaseUrl,
    String? persistenceBackend,
    required bool eagerReady,
  }) = ProvisionEnvironmentRequest;

  @FreezedUnionValue('get_boot_environment_descriptor')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationRequest.getBootEnvironmentDescriptor({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
  }) = GetBootEnvironmentDescriptorRequest;

  @FreezedUnionValue('discover_environment_configs')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationRequest.discoverEnvironmentConfigs({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
  }) = DiscoverEnvironmentConfigsRequest;

  @FreezedUnionValue('discover_service_api_dependency_routes')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationRequest.discoverServiceApiDependencyRoutes({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    @UuidValueConverter() UuidValue? consumerServicePackageId,
    @UuidValueConverter() UuidValue? apiPackageId,
  }) = DiscoverServiceApiDependencyRoutesRequest;

  @FreezedUnionValue('discover_hosted_services')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationRequest.discoverHostedServices({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
  }) = DiscoverHostedServicesRequest;

  @FreezedUnionValue('describe_hosted_service_runtimes')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationRequest.describeHostedServiceRuntimes({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
  }) = DescribeHostedServiceRuntimesRequest;

  @FreezedUnionValue('get_environment_status')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationRequest.getEnvironmentStatus({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    @UuidValueConverter() required UuidValue environmentId,
  }) = GetEnvironmentStatusRequest;

  @FreezedUnionValue('close_stream')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationRequest.closeStream({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    @UuidValueConverter() required UuidValue networkOperationId,
  }) = CloseStreamRequest;

  @FreezedUnionValue('interface_session_register')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationRequest.interfaceSessionRegister({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    @UuidValueConverter() required UuidValue interfaceId,
    @UuidValueConverter() required UuidValue interfaceSessionId,
    String? sessionLabel,
    @Default(const []) List<String> capabilities,
    required int protocolVersion,
  }) = InterfaceSessionRegisterRequest;

  @FreezedUnionValue('interface_session_heartbeat')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationRequest.interfaceSessionHeartbeat({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    @UuidValueConverter() required UuidValue interfaceSessionId,
    String? timestamp,
  }) = InterfaceSessionHeartbeatRequest;

  factory NetworkNodeOperationRequest.fromJson(Map<String, dynamic> json) =>
      _$NetworkNodeOperationRequestFromJson(json);
}

/// Response union base (operation + context).
@Freezed(unionKey: 'operation')
abstract class NetworkNodeOperationResponse
    with _$NetworkNodeOperationResponse {
  @FreezedUnionValue('identity_challenge')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationResponse.identityChallenge({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    required String status,
    String? error,
    required String publicKey,
    required String challenge,
    String? expiresAt,
  }) = IdentityChallengeResponse;

  @FreezedUnionValue('identity_login')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationResponse.identityLogin({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    required String status,
    String? error,
    required String publicKey,
    @Default(const []) List<String> roles,
  }) = IdentityLoginResponse;

  @FreezedUnionValue('token_login')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationResponse.tokenLogin({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    required String status,
    String? error,
    String? publicKey,
    @Default(const []) List<String> roles,
    @UuidValueConverter() UuidValue? tokenId,
    String? tokenType,
    @Default(const []) List<String> scopes,
    @UuidValueConverter() UuidValue? contextEnvironmentId,
    @UuidValueConverter() UuidValue? contextProcessId,
    @UuidValueConverter() UuidValue? contextThreadId,
    String? expiresAt,
  }) = TokenLoginResponse;

  @FreezedUnionValue('whoami')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationResponse.whoami({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    required String status,
    String? error,
    required bool authenticated,
    String? publicKey,
    @Default(const []) List<String> roles,
    @UuidValueConverter() UuidValue? interfaceSessionId,
    @UuidValueConverter() UuidValue? interfaceId,
    String? lastSeenAt,
  }) = WhoamiResponse;

  @FreezedUnionValue('membership_status')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationResponse.membershipStatus({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    required String status,
    String? error,
    required bool isActive,
    required bool isBypassed,
    String? planLabel,
    String? currentPeriodEnd,
  }) = MembershipStatusResponse;

  @FreezedUnionValue('membership_checkout_session_create')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationResponse.membershipCheckoutSessionCreate({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    required String status,
    String? error,
    String? checkoutUrl,
    String? checkoutSessionId,
  }) = MembershipCheckoutSessionCreateResponse;

  @FreezedUnionValue('membership_purchase_prepare')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationResponse.membershipPurchasePrepare({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    required String status,
    String? error,
    required String provider,
    String? planLabel,
    String? checkoutUrl,
    String? appleProductId,
    String? googleProductId,
  }) = MembershipPurchasePrepareResponse;

  @FreezedUnionValue('membership_purchase_claim')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationResponse.membershipPurchaseClaim({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    required String status,
    String? error,
    required bool isActive,
    String? planLabel,
    String? currentPeriodEnd,
  }) = MembershipPurchaseClaimResponse;

  @FreezedUnionValue('provision_environment')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationResponse.provisionEnvironment({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    required String status,
    String? error,
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() UuidValue? environmentConfigId,
    String? environmentConfigTitle,
    String? environmentTitle,
    String? environmentEndpoint,
    String? ocgHash,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    @Default(const []) List<String> opgHashes,
    NodeEnvironmentProvisioningReceipt? provisioningReceipt,
  }) = ProvisionEnvironmentResponse;

  @FreezedUnionValue('get_boot_environment_descriptor')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationResponse.getBootEnvironmentDescriptor({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    required String status,
    String? error,
    BootEnvironmentDescriptor? descriptor,
  }) = GetBootEnvironmentDescriptorResponse;

  @FreezedUnionValue('discover_environment_configs')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationResponse.discoverEnvironmentConfigs({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    @Default(const []) List<EnvironmentConfigDescriptor> configs,
  }) = DiscoverEnvironmentConfigsResponse;

  @FreezedUnionValue('discover_service_api_dependency_routes')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationResponse.discoverServiceApiDependencyRoutes({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    @Default(const []) List<ServiceApiDependencyRouteDescriptor> routes,
  }) = DiscoverServiceApiDependencyRoutesResponse;

  @FreezedUnionValue('discover_hosted_services')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationResponse.discoverHostedServices({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    @Default(const []) List<HostedServiceAdvertisement> hostedServices,
  }) = DiscoverHostedServicesResponse;

  @FreezedUnionValue('describe_hosted_service_runtimes')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationResponse.describeHostedServiceRuntimes({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    @Default(const []) List<HostedServiceRuntimeStatus> hostedServiceRuntimes,
  }) = DescribeHostedServiceRuntimesResponse;

  @FreezedUnionValue('get_environment_status')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationResponse.getEnvironmentStatus({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    required String status,
    String? error,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() UuidValue? environmentConfigId,
    String? environmentConfigTitle,
    String? environmentTitle,
    String? environmentEndpoint,
    String? ocgHash,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    @Default(const []) List<String> opgHashes,
    NodeEnvironmentProvisioningReceipt? provisioningReceipt,
  }) = GetEnvironmentStatusResponse;

  @FreezedUnionValue('close_stream')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationResponse.closeStream({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    required String status,
    String? error,
    @UuidValueConverter() required UuidValue networkOperationId,
  }) = CloseStreamResponse;

  @FreezedUnionValue('interface_session_register')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationResponse.interfaceSessionRegister({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    required String status,
    String? error,
    @UuidValueConverter() required UuidValue interfaceId,
    @UuidValueConverter() required UuidValue interfaceSessionId,
    @UuidValueConverter() UuidValue? interfaceIdentityNetworkNodeId,
    @UuidValueConverter() UuidValue? interfaceSessionNetworkBindingId,
    String? lastSeenAt,
    required int protocolVersion,
  }) = InterfaceSessionRegisterResponse;

  @FreezedUnionValue('interface_session_heartbeat')
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NetworkNodeOperationResponse.interfaceSessionHeartbeat({
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    required String status,
    String? error,
    @UuidValueConverter() required UuidValue interfaceSessionId,
    String? lastSeenAt,
  }) = InterfaceSessionHeartbeatResponse;

  factory NetworkNodeOperationResponse.fromJson(Map<String, dynamic> json) =>
      _$NetworkNodeOperationResponseFromJson(json);
}

/// Product receipt for a NetworkNode-provisioned Environment.
/// The nested `readiness_receipt` is the public Environment API receipt payload.
/// Network keeps it as JSON so Network control-plane DTOs stay decoupled from
/// Environment Environment DTO packages while exposing full provenance evidence.
@freezed
abstract class NodeEnvironmentProvisioningReceipt
    with _$NodeEnvironmentProvisioningReceipt {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory NodeEnvironmentProvisioningReceipt.def({
    required String status,
    String? error,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? nodeId,
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() UuidValue? environmentConfigId,
    String? environmentConfigTitle,
    String? environmentTitle,
    String? environmentEndpoint,
    String? ocgHash,
    @Default(const []) List<String> opgHashes,
    String? runtimeArtifactRefsJson,
    String? serviceApiProviderRefsJson,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    String? outerWrapperKind,
    String? environmentHandle,
    String? workspaceRoot,
    String? workspaceTomlPath,
    String? workspaceId,
    String? workspacePackageId,
    String? workspaceBuildInvocationId,
    String? workspaceBuildReceiptPath,
    String? workspaceBuildLatestPath,
    String? workspaceTargetLatestPath,
    String? workspaceTargetRef,
    Map<String, dynamic>? readinessReceipt,
    Map<String, dynamic>? networkNodeEnvironmentReceipt,
  }) = _NodeEnvironmentProvisioningReceipt;

  factory NodeEnvironmentProvisioningReceipt({
    required String status,
    String? error,
    UuidValue? actorId,
    UuidValue? nodeId,
    UuidValue? environmentId,
    UuidValue? environmentConfigId,
    String? environmentConfigTitle,
    String? environmentTitle,
    String? environmentEndpoint,
    String? ocgHash,
    List<String> opgHashes = const [],
    String? runtimeArtifactRefsJson,
    String? serviceApiProviderRefsJson,
    UuidValue? processId,
    UuidValue? threadId,
    UuidValue? branchId,
    String? outerWrapperKind,
    String? environmentHandle,
    String? workspaceRoot,
    String? workspaceTomlPath,
    String? workspaceId,
    String? workspacePackageId,
    String? workspaceBuildInvocationId,
    String? workspaceBuildReceiptPath,
    String? workspaceBuildLatestPath,
    String? workspaceTargetLatestPath,
    String? workspaceTargetRef,
    Map<String, dynamic>? readinessReceipt,
    Map<String, dynamic>? networkNodeEnvironmentReceipt,
  }) {
    return _NodeEnvironmentProvisioningReceipt(
      status: status,
      error: error,
      actorId: actorId,
      nodeId: nodeId,
      environmentId: environmentId,
      environmentConfigId: environmentConfigId,
      environmentConfigTitle: environmentConfigTitle,
      environmentTitle: environmentTitle,
      environmentEndpoint: environmentEndpoint,
      ocgHash: ocgHash,
      opgHashes: opgHashes,
      runtimeArtifactRefsJson: runtimeArtifactRefsJson,
      serviceApiProviderRefsJson: serviceApiProviderRefsJson,
      processId: processId,
      threadId: threadId,
      branchId: branchId,
      outerWrapperKind: outerWrapperKind,
      environmentHandle: environmentHandle,
      workspaceRoot: workspaceRoot,
      workspaceTomlPath: workspaceTomlPath,
      workspaceId: workspaceId,
      workspacePackageId: workspacePackageId,
      workspaceBuildInvocationId: workspaceBuildInvocationId,
      workspaceBuildReceiptPath: workspaceBuildReceiptPath,
      workspaceBuildLatestPath: workspaceBuildLatestPath,
      workspaceTargetLatestPath: workspaceTargetLatestPath,
      workspaceTargetRef: workspaceTargetRef,
      readinessReceipt: readinessReceipt,
      networkNodeEnvironmentReceipt: networkNodeEnvironmentReceipt,
    );
  }

  factory NodeEnvironmentProvisioningReceipt.fromJson(
    Map<String, dynamic> json,
  ) => _$NodeEnvironmentProvisioningReceiptFromJson(json);
}

/// Describe an environment config (template/map) available for provisioning.
@freezed
abstract class EnvironmentConfigDescriptor with _$EnvironmentConfigDescriptor {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentConfigDescriptor.def({
    @UuidValueConverter() required UuidValue environmentConfigId,
    String? title,
    String? canonicalLanguage,
    String? ocgHash,
    @Default(const []) List<String> opgHashes,
    String? outerWrapperKind,
    String? environmentHandle,
    String? workspaceTargetRef,
  }) = _EnvironmentConfigDescriptor;

  factory EnvironmentConfigDescriptor({
    required UuidValue environmentConfigId,
    String? title,
    String? canonicalLanguage,
    String? ocgHash,
    List<String> opgHashes = const [],
    String? outerWrapperKind,
    String? environmentHandle,
    String? workspaceTargetRef,
  }) {
    return _EnvironmentConfigDescriptor(
      environmentConfigId: environmentConfigId,
      title: title,
      canonicalLanguage: canonicalLanguage,
      ocgHash: ocgHash,
      opgHashes: opgHashes,
      outerWrapperKind: outerWrapperKind,
      environmentHandle: environmentHandle,
      workspaceTargetRef: workspaceTargetRef,
    );
  }

  factory EnvironmentConfigDescriptor.fromJson(Map<String, dynamic> json) =>
      _$EnvironmentConfigDescriptorFromJson(json);
}

/// Descriptor for the node-managed BOOT environment (v0).
/// IMPORTANT:
/// - The "kernel" is an EnvironmentConfig (module mount set).
/// - The "boot environment" is an Environment instance derived from that config.
/// - This DTO exists to avoid client-side heuristics for selecting the kernel config.
@freezed
abstract class BootEnvironmentDescriptor with _$BootEnvironmentDescriptor {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory BootEnvironmentDescriptor.def({
    @UuidValueConverter() required UuidValue kernelEnvironmentConfigId,
    @UuidValueConverter() required UuidValue bootEnvironmentId,
    String? kernelEnvironmentConfigTitle,
    String? bootEnvironmentTitle,
    @UuidValueConverter() UuidValue? processId,
    @UuidValueConverter() UuidValue? threadId,
    @UuidValueConverter() UuidValue? branchId,
    @Default(const []) List<String> opgHashes,
  }) = _BootEnvironmentDescriptor;

  factory BootEnvironmentDescriptor({
    required UuidValue kernelEnvironmentConfigId,
    required UuidValue bootEnvironmentId,
    String? kernelEnvironmentConfigTitle,
    String? bootEnvironmentTitle,
    UuidValue? processId,
    UuidValue? threadId,
    UuidValue? branchId,
    List<String> opgHashes = const [],
  }) {
    return _BootEnvironmentDescriptor(
      kernelEnvironmentConfigId: kernelEnvironmentConfigId,
      bootEnvironmentId: bootEnvironmentId,
      kernelEnvironmentConfigTitle: kernelEnvironmentConfigTitle,
      bootEnvironmentTitle: bootEnvironmentTitle,
      processId: processId,
      threadId: threadId,
      branchId: branchId,
      opgHashes: opgHashes,
    );
  }

  factory BootEnvironmentDescriptor.fromJson(Map<String, dynamic> json) =>
      _$BootEnvironmentDescriptorFromJson(json);
}

/// Node-owned route descriptor for one bound service-to-service API dependency.
/// This is the network transport DTO for NodeHost route-registry truth. Node
/// derives it from selected ServicePackage required/provided ApiPackage bridges
/// plus live ServiceHost handshakes; remote/subprocess consumers must not
/// reopen package manifests or infer provider routes locally.
@freezed
abstract class ServiceApiDependencyRouteDescriptor
    with _$ServiceApiDependencyRouteDescriptor {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ServiceApiDependencyRouteDescriptor.def({
    @UuidValueConverter() required UuidValue consumerServicePackageId,
    required String consumerServicePackageName,
    @UuidValueConverter() required UuidValue providerServicePackageId,
    required String providerServicePackageName,
    @UuidValueConverter() required UuidValue apiPackageId,
    String? apiPackageName,
    required String routeKind,
    required String hostId,
    String? hostVersion,
    required String protocolVersion,
    String? socketPath,
    @UuidValueConverter() UuidValue? consumerNodeId,
    @UuidValueConverter() UuidValue? providerNodeId,
    String? providerNodeBaseUrl,
    @UuidValueConverter() UuidValue? routeConnectionId,
    required double requestTimeoutS,
    @Default(const []) List<String> serviceNames,
    required Map<String, dynamic> endpointRefsByService,
    required Map<String, dynamic> streamEndpointRefsByService,
  }) = _ServiceApiDependencyRouteDescriptor;

  factory ServiceApiDependencyRouteDescriptor({
    required UuidValue consumerServicePackageId,
    required String consumerServicePackageName,
    required UuidValue providerServicePackageId,
    required String providerServicePackageName,
    required UuidValue apiPackageId,
    String? apiPackageName,
    required String routeKind,
    required String hostId,
    String? hostVersion,
    required String protocolVersion,
    String? socketPath,
    UuidValue? consumerNodeId,
    UuidValue? providerNodeId,
    String? providerNodeBaseUrl,
    UuidValue? routeConnectionId,
    required double requestTimeoutS,
    List<String> serviceNames = const [],
    Map<String, dynamic>? endpointRefsByService,
    Map<String, dynamic>? streamEndpointRefsByService,
  }) {
    return _ServiceApiDependencyRouteDescriptor(
      consumerServicePackageId: consumerServicePackageId,
      consumerServicePackageName: consumerServicePackageName,
      providerServicePackageId: providerServicePackageId,
      providerServicePackageName: providerServicePackageName,
      apiPackageId: apiPackageId,
      apiPackageName: apiPackageName,
      routeKind: routeKind,
      hostId: hostId,
      hostVersion: hostVersion,
      protocolVersion: protocolVersion,
      socketPath: socketPath,
      consumerNodeId: consumerNodeId,
      providerNodeId: providerNodeId,
      providerNodeBaseUrl: providerNodeBaseUrl,
      routeConnectionId: routeConnectionId,
      requestTimeoutS: requestTimeoutS,
      serviceNames: serviceNames,
      endpointRefsByService: endpointRefsByService ?? {},
      streamEndpointRefsByService: streamEndpointRefsByService ?? {},
    );
  }

  factory ServiceApiDependencyRouteDescriptor.fromJson(
    Map<String, dynamic> json,
  ) => _$ServiceApiDependencyRouteDescriptorFromJson({
    ...json,
    if (!json.containsKey('endpoint_refs_by_service'))
      'endpoint_refs_by_service': {},
    if (!json.containsKey('stream_endpoint_refs_by_service'))
      'stream_endpoint_refs_by_service': {},
  });
}

/// Node-owned advertisement for one supervised hosted generic Service.
/// This is control-plane discovery truth derived by the hosting Node from its
/// private Service-host handshake/runtime registry. Remote Nodes consume this
/// DTO; they do not consume the raw Service-host handshake contract directly.
@freezed
abstract class HostedServiceAdvertisement with _$HostedServiceAdvertisement {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory HostedServiceAdvertisement.def({
    @UuidValueConverter() UuidValue? servicePackageId,
    @UuidValueConverter() UuidValue? serviceId,
    required String serviceName,
    @Default(const []) List<String> servicePackageNames,
    @Default(const []) List<String> endpointRefs,
    required String hostId,
    String? hostVersion,
    required String protocolVersion,
    required bool supportsStreamEvents,
  }) = _HostedServiceAdvertisement;

  factory HostedServiceAdvertisement({
    UuidValue? servicePackageId,
    UuidValue? serviceId,
    required String serviceName,
    List<String> servicePackageNames = const [],
    List<String> endpointRefs = const [],
    required String hostId,
    String? hostVersion,
    required String protocolVersion,
    bool? supportsStreamEvents,
  }) {
    return _HostedServiceAdvertisement(
      servicePackageId: servicePackageId,
      serviceId: serviceId,
      serviceName: serviceName,
      servicePackageNames: servicePackageNames,
      endpointRefs: endpointRefs,
      hostId: hostId,
      hostVersion: hostVersion,
      protocolVersion: protocolVersion,
      supportsStreamEvents: supportsStreamEvents ?? false,
    );
  }

  factory HostedServiceAdvertisement.fromJson(Map<String, dynamic> json) =>
      _$HostedServiceAdvertisementFromJson({
        ...json,
        if (!json.containsKey('supports_stream_events'))
          'supports_stream_events': false,
      });
}

/// Typed per-service view of one supervised hosted-Service runtime.
/// This is runtime-status truth, not routing-only advertisement.
@freezed
abstract class HostedServiceRuntimeServiceStatus
    with _$HostedServiceRuntimeServiceStatus {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory HostedServiceRuntimeServiceStatus.def({
    required String serviceName,
    @Default(const []) List<String> endpointRefs,
    @Default(const []) List<String> streamEndpointRefs,
  }) = _HostedServiceRuntimeServiceStatus;

  factory HostedServiceRuntimeServiceStatus({
    required String serviceName,
    List<String> endpointRefs = const [],
    List<String> streamEndpointRefs = const [],
  }) {
    return _HostedServiceRuntimeServiceStatus(
      serviceName: serviceName,
      endpointRefs: endpointRefs,
      streamEndpointRefs: streamEndpointRefs,
    );
  }

  factory HostedServiceRuntimeServiceStatus.fromJson(
    Map<String, dynamic> json,
  ) => _$HostedServiceRuntimeServiceStatusFromJson(json);
}

/// Node-owned runtime status for one supervised hosted-Service host/runtime.
/// IMPORTANT:
/// - This remains control-plane truth owned by the supervising Node.
/// - It is derived from private Service-host handshake + process supervision.
/// - It is intentionally separate from `HostedServiceAdvertisement`, which
/// remains routing/discovery-only.
@freezed
abstract class HostedServiceRuntimeStatus with _$HostedServiceRuntimeStatus {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory HostedServiceRuntimeStatus.def({
    required String hostId,
    String? hostVersion,
    required String protocolVersion,
    required String readinessStatus,
    required bool isReady,
    required bool isAlive,
    required bool supportsStreamEvents,
    String? summary,
    String? error,
    String? updatedAt,
    @Default(const []) List<HostedServiceRuntimeServiceStatus> services,
  }) = _HostedServiceRuntimeStatus;

  factory HostedServiceRuntimeStatus({
    required String hostId,
    String? hostVersion,
    required String protocolVersion,
    String? readinessStatus,
    bool? isReady,
    bool? isAlive,
    bool? supportsStreamEvents,
    String? summary,
    String? error,
    String? updatedAt,
    List<HostedServiceRuntimeServiceStatus> services = const [],
  }) {
    return _HostedServiceRuntimeStatus(
      hostId: hostId,
      hostVersion: hostVersion,
      protocolVersion: protocolVersion,
      readinessStatus: readinessStatus ?? 'unknown',
      isReady: isReady ?? false,
      isAlive: isAlive ?? false,
      supportsStreamEvents: supportsStreamEvents ?? false,
      summary: summary,
      error: error,
      updatedAt: updatedAt,
      services: services,
    );
  }

  factory HostedServiceRuntimeStatus.fromJson(Map<String, dynamic> json) =>
      _$HostedServiceRuntimeStatusFromJson({
        ...json,
        if (!json.containsKey('readiness_status'))
          'readiness_status': 'unknown',
        if (!json.containsKey('is_ready')) 'is_ready': false,
        if (!json.containsKey('is_alive')) 'is_alive': false,
        if (!json.containsKey('supports_stream_events'))
          'supports_stream_events': false,
      });
}
