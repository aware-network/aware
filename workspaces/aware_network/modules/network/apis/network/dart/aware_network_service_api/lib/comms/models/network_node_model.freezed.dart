// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'network_node_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$NetworkNodeOperationContext {

@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue? get nodeId;
/// Create a copy of NetworkNodeOperationContext
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkNodeOperationContextCopyWith<NetworkNodeOperationContext> get copyWith => _$NetworkNodeOperationContextCopyWithImpl<NetworkNodeOperationContext>(this as NetworkNodeOperationContext, _$identity);

  /// Serializes this NetworkNodeOperationContext to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkNodeOperationContext&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId);

@override
String toString() {
  return 'NetworkNodeOperationContext(actorId: $actorId, nodeId: $nodeId)';
}


}

/// @nodoc
abstract mixin class $NetworkNodeOperationContextCopyWith<$Res>  {
  factory $NetworkNodeOperationContextCopyWith(NetworkNodeOperationContext value, $Res Function(NetworkNodeOperationContext) _then) = _$NetworkNodeOperationContextCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId
});




}
/// @nodoc
class _$NetworkNodeOperationContextCopyWithImpl<$Res>
    implements $NetworkNodeOperationContextCopyWith<$Res> {
  _$NetworkNodeOperationContextCopyWithImpl(this._self, this._then);

  final NetworkNodeOperationContext _self;
  final $Res Function(NetworkNodeOperationContext) _then;

/// Create a copy of NetworkNodeOperationContext
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? nodeId = freezed,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkNodeOperationContext].
extension NetworkNodeOperationContextPatterns on NetworkNodeOperationContext {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkNodeOperationContext value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkNodeOperationContext() when def != null:
return def(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkNodeOperationContext value)  def,}){
final _that = this;
switch (_that) {
case _NetworkNodeOperationContext():
return def(_that);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkNodeOperationContext value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkNodeOperationContext() when def != null:
return def(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkNodeOperationContext() when def != null:
return def(_that.actorId,_that.nodeId);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)  def,}) {final _that = this;
switch (_that) {
case _NetworkNodeOperationContext():
return def(_that.actorId,_that.nodeId);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)?  def,}) {final _that = this;
switch (_that) {
case _NetworkNodeOperationContext() when def != null:
return def(_that.actorId,_that.nodeId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkNodeOperationContext implements NetworkNodeOperationContext {
   _NetworkNodeOperationContext({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId});
  factory _NetworkNodeOperationContext.fromJson(Map<String, dynamic> json) => _$NetworkNodeOperationContextFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;

/// Create a copy of NetworkNodeOperationContext
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkNodeOperationContextCopyWith<_NetworkNodeOperationContext> get copyWith => __$NetworkNodeOperationContextCopyWithImpl<_NetworkNodeOperationContext>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkNodeOperationContextToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkNodeOperationContext&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId);

@override
String toString() {
  return 'NetworkNodeOperationContext.def(actorId: $actorId, nodeId: $nodeId)';
}


}

/// @nodoc
abstract mixin class _$NetworkNodeOperationContextCopyWith<$Res> implements $NetworkNodeOperationContextCopyWith<$Res> {
  factory _$NetworkNodeOperationContextCopyWith(_NetworkNodeOperationContext value, $Res Function(_NetworkNodeOperationContext) _then) = __$NetworkNodeOperationContextCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId
});




}
/// @nodoc
class __$NetworkNodeOperationContextCopyWithImpl<$Res>
    implements _$NetworkNodeOperationContextCopyWith<$Res> {
  __$NetworkNodeOperationContextCopyWithImpl(this._self, this._then);

  final _NetworkNodeOperationContext _self;
  final $Res Function(_NetworkNodeOperationContext) _then;

/// Create a copy of NetworkNodeOperationContext
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,}) {
  return _then(_NetworkNodeOperationContext(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}


}


/// @nodoc
mixin _$NetworkNodeOperation {

 NetworkNodeOperationRequest? get request; NetworkNodeOperationResponse? get response;
/// Create a copy of NetworkNodeOperation
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkNodeOperationCopyWith<NetworkNodeOperation> get copyWith => _$NetworkNodeOperationCopyWithImpl<NetworkNodeOperation>(this as NetworkNodeOperation, _$identity);

  /// Serializes this NetworkNodeOperation to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkNodeOperation&&(identical(other.request, request) || other.request == request)&&(identical(other.response, response) || other.response == response));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,request,response);

@override
String toString() {
  return 'NetworkNodeOperation(request: $request, response: $response)';
}


}

/// @nodoc
abstract mixin class $NetworkNodeOperationCopyWith<$Res>  {
  factory $NetworkNodeOperationCopyWith(NetworkNodeOperation value, $Res Function(NetworkNodeOperation) _then) = _$NetworkNodeOperationCopyWithImpl;
@useResult
$Res call({
 NetworkNodeOperationRequest? request, NetworkNodeOperationResponse? response
});


$NetworkNodeOperationRequestCopyWith<$Res>? get request;$NetworkNodeOperationResponseCopyWith<$Res>? get response;

}
/// @nodoc
class _$NetworkNodeOperationCopyWithImpl<$Res>
    implements $NetworkNodeOperationCopyWith<$Res> {
  _$NetworkNodeOperationCopyWithImpl(this._self, this._then);

  final NetworkNodeOperation _self;
  final $Res Function(NetworkNodeOperation) _then;

/// Create a copy of NetworkNodeOperation
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? request = freezed,Object? response = freezed,}) {
  return _then(_self.copyWith(
request: freezed == request ? _self.request : request // ignore: cast_nullable_to_non_nullable
as NetworkNodeOperationRequest?,response: freezed == response ? _self.response : response // ignore: cast_nullable_to_non_nullable
as NetworkNodeOperationResponse?,
  ));
}
/// Create a copy of NetworkNodeOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodeOperationRequestCopyWith<$Res>? get request {
    if (_self.request == null) {
    return null;
  }

  return $NetworkNodeOperationRequestCopyWith<$Res>(_self.request!, (value) {
    return _then(_self.copyWith(request: value));
  });
}/// Create a copy of NetworkNodeOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodeOperationResponseCopyWith<$Res>? get response {
    if (_self.response == null) {
    return null;
  }

  return $NetworkNodeOperationResponseCopyWith<$Res>(_self.response!, (value) {
    return _then(_self.copyWith(response: value));
  });
}
}


/// Adds pattern-matching-related methods to [NetworkNodeOperation].
extension NetworkNodeOperationPatterns on NetworkNodeOperation {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkNodeOperation value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkNodeOperation() when def != null:
return def(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkNodeOperation value)  def,}){
final _that = this;
switch (_that) {
case _NetworkNodeOperation():
return def(_that);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkNodeOperation value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkNodeOperation() when def != null:
return def(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( NetworkNodeOperationRequest? request,  NetworkNodeOperationResponse? response)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkNodeOperation() when def != null:
return def(_that.request,_that.response);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( NetworkNodeOperationRequest? request,  NetworkNodeOperationResponse? response)  def,}) {final _that = this;
switch (_that) {
case _NetworkNodeOperation():
return def(_that.request,_that.response);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( NetworkNodeOperationRequest? request,  NetworkNodeOperationResponse? response)?  def,}) {final _that = this;
switch (_that) {
case _NetworkNodeOperation() when def != null:
return def(_that.request,_that.response);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkNodeOperation implements NetworkNodeOperation {
   _NetworkNodeOperation({this.request, this.response});
  factory _NetworkNodeOperation.fromJson(Map<String, dynamic> json) => _$NetworkNodeOperationFromJson(json);

@override final  NetworkNodeOperationRequest? request;
@override final  NetworkNodeOperationResponse? response;

/// Create a copy of NetworkNodeOperation
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkNodeOperationCopyWith<_NetworkNodeOperation> get copyWith => __$NetworkNodeOperationCopyWithImpl<_NetworkNodeOperation>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkNodeOperationToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkNodeOperation&&(identical(other.request, request) || other.request == request)&&(identical(other.response, response) || other.response == response));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,request,response);

@override
String toString() {
  return 'NetworkNodeOperation.def(request: $request, response: $response)';
}


}

/// @nodoc
abstract mixin class _$NetworkNodeOperationCopyWith<$Res> implements $NetworkNodeOperationCopyWith<$Res> {
  factory _$NetworkNodeOperationCopyWith(_NetworkNodeOperation value, $Res Function(_NetworkNodeOperation) _then) = __$NetworkNodeOperationCopyWithImpl;
@override @useResult
$Res call({
 NetworkNodeOperationRequest? request, NetworkNodeOperationResponse? response
});


@override $NetworkNodeOperationRequestCopyWith<$Res>? get request;@override $NetworkNodeOperationResponseCopyWith<$Res>? get response;

}
/// @nodoc
class __$NetworkNodeOperationCopyWithImpl<$Res>
    implements _$NetworkNodeOperationCopyWith<$Res> {
  __$NetworkNodeOperationCopyWithImpl(this._self, this._then);

  final _NetworkNodeOperation _self;
  final $Res Function(_NetworkNodeOperation) _then;

/// Create a copy of NetworkNodeOperation
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? request = freezed,Object? response = freezed,}) {
  return _then(_NetworkNodeOperation(
request: freezed == request ? _self.request : request // ignore: cast_nullable_to_non_nullable
as NetworkNodeOperationRequest?,response: freezed == response ? _self.response : response // ignore: cast_nullable_to_non_nullable
as NetworkNodeOperationResponse?,
  ));
}

/// Create a copy of NetworkNodeOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodeOperationRequestCopyWith<$Res>? get request {
    if (_self.request == null) {
    return null;
  }

  return $NetworkNodeOperationRequestCopyWith<$Res>(_self.request!, (value) {
    return _then(_self.copyWith(request: value));
  });
}/// Create a copy of NetworkNodeOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodeOperationResponseCopyWith<$Res>? get response {
    if (_self.response == null) {
    return null;
  }

  return $NetworkNodeOperationResponseCopyWith<$Res>(_self.response!, (value) {
    return _then(_self.copyWith(response: value));
  });
}
}

NetworkNodeOperationRequest _$NetworkNodeOperationRequestFromJson(
  Map<String, dynamic> json
) {
        switch (json['operation']) {
                  case 'identity_challenge':
          return IdentityChallengeRequest.fromJson(
            json
          );
                case 'identity_login':
          return IdentityLoginRequest.fromJson(
            json
          );
                case 'token_login':
          return TokenLoginRequest.fromJson(
            json
          );
                case 'whoami':
          return WhoamiRequest.fromJson(
            json
          );
                case 'membership_status':
          return MembershipStatusRequest.fromJson(
            json
          );
                case 'membership_checkout_session_create':
          return MembershipCheckoutSessionCreateRequest.fromJson(
            json
          );
                case 'membership_purchase_prepare':
          return MembershipPurchasePrepareRequest.fromJson(
            json
          );
                case 'membership_purchase_claim':
          return MembershipPurchaseClaimRequest.fromJson(
            json
          );
                case 'provision_environment':
          return ProvisionEnvironmentRequest.fromJson(
            json
          );
                case 'get_boot_environment_descriptor':
          return GetBootEnvironmentDescriptorRequest.fromJson(
            json
          );
                case 'discover_environment_configs':
          return DiscoverEnvironmentConfigsRequest.fromJson(
            json
          );
                case 'discover_service_api_dependency_routes':
          return DiscoverServiceApiDependencyRoutesRequest.fromJson(
            json
          );
                case 'discover_hosted_services':
          return DiscoverHostedServicesRequest.fromJson(
            json
          );
                case 'describe_hosted_service_runtimes':
          return DescribeHostedServiceRuntimesRequest.fromJson(
            json
          );
                case 'get_environment_status':
          return GetEnvironmentStatusRequest.fromJson(
            json
          );
                case 'close_stream':
          return CloseStreamRequest.fromJson(
            json
          );
                case 'interface_session_register':
          return InterfaceSessionRegisterRequest.fromJson(
            json
          );
                case 'interface_session_heartbeat':
          return InterfaceSessionHeartbeatRequest.fromJson(
            json
          );
        
          default:
            throw CheckedFromJsonException(
  json,
  'operation',
  'NetworkNodeOperationRequest',
  'Invalid union type "${json['operation']}"!'
);
        }
      
}

/// @nodoc
mixin _$NetworkNodeOperationRequest {

@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue? get nodeId;
/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkNodeOperationRequestCopyWith<NetworkNodeOperationRequest> get copyWith => _$NetworkNodeOperationRequestCopyWithImpl<NetworkNodeOperationRequest>(this as NetworkNodeOperationRequest, _$identity);

  /// Serializes this NetworkNodeOperationRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkNodeOperationRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId);

@override
String toString() {
  return 'NetworkNodeOperationRequest(actorId: $actorId, nodeId: $nodeId)';
}


}

/// @nodoc
abstract mixin class $NetworkNodeOperationRequestCopyWith<$Res>  {
  factory $NetworkNodeOperationRequestCopyWith(NetworkNodeOperationRequest value, $Res Function(NetworkNodeOperationRequest) _then) = _$NetworkNodeOperationRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId
});




}
/// @nodoc
class _$NetworkNodeOperationRequestCopyWithImpl<$Res>
    implements $NetworkNodeOperationRequestCopyWith<$Res> {
  _$NetworkNodeOperationRequestCopyWithImpl(this._self, this._then);

  final NetworkNodeOperationRequest _self;
  final $Res Function(NetworkNodeOperationRequest) _then;

/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? nodeId = freezed,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkNodeOperationRequest].
extension NetworkNodeOperationRequestPatterns on NetworkNodeOperationRequest {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( IdentityChallengeRequest value)?  identityChallenge,TResult Function( IdentityLoginRequest value)?  identityLogin,TResult Function( TokenLoginRequest value)?  tokenLogin,TResult Function( WhoamiRequest value)?  whoami,TResult Function( MembershipStatusRequest value)?  membershipStatus,TResult Function( MembershipCheckoutSessionCreateRequest value)?  membershipCheckoutSessionCreate,TResult Function( MembershipPurchasePrepareRequest value)?  membershipPurchasePrepare,TResult Function( MembershipPurchaseClaimRequest value)?  membershipPurchaseClaim,TResult Function( ProvisionEnvironmentRequest value)?  provisionEnvironment,TResult Function( GetBootEnvironmentDescriptorRequest value)?  getBootEnvironmentDescriptor,TResult Function( DiscoverEnvironmentConfigsRequest value)?  discoverEnvironmentConfigs,TResult Function( DiscoverServiceApiDependencyRoutesRequest value)?  discoverServiceApiDependencyRoutes,TResult Function( DiscoverHostedServicesRequest value)?  discoverHostedServices,TResult Function( DescribeHostedServiceRuntimesRequest value)?  describeHostedServiceRuntimes,TResult Function( GetEnvironmentStatusRequest value)?  getEnvironmentStatus,TResult Function( CloseStreamRequest value)?  closeStream,TResult Function( InterfaceSessionRegisterRequest value)?  interfaceSessionRegister,TResult Function( InterfaceSessionHeartbeatRequest value)?  interfaceSessionHeartbeat,required TResult orElse(),}){
final _that = this;
switch (_that) {
case IdentityChallengeRequest() when identityChallenge != null:
return identityChallenge(_that);case IdentityLoginRequest() when identityLogin != null:
return identityLogin(_that);case TokenLoginRequest() when tokenLogin != null:
return tokenLogin(_that);case WhoamiRequest() when whoami != null:
return whoami(_that);case MembershipStatusRequest() when membershipStatus != null:
return membershipStatus(_that);case MembershipCheckoutSessionCreateRequest() when membershipCheckoutSessionCreate != null:
return membershipCheckoutSessionCreate(_that);case MembershipPurchasePrepareRequest() when membershipPurchasePrepare != null:
return membershipPurchasePrepare(_that);case MembershipPurchaseClaimRequest() when membershipPurchaseClaim != null:
return membershipPurchaseClaim(_that);case ProvisionEnvironmentRequest() when provisionEnvironment != null:
return provisionEnvironment(_that);case GetBootEnvironmentDescriptorRequest() when getBootEnvironmentDescriptor != null:
return getBootEnvironmentDescriptor(_that);case DiscoverEnvironmentConfigsRequest() when discoverEnvironmentConfigs != null:
return discoverEnvironmentConfigs(_that);case DiscoverServiceApiDependencyRoutesRequest() when discoverServiceApiDependencyRoutes != null:
return discoverServiceApiDependencyRoutes(_that);case DiscoverHostedServicesRequest() when discoverHostedServices != null:
return discoverHostedServices(_that);case DescribeHostedServiceRuntimesRequest() when describeHostedServiceRuntimes != null:
return describeHostedServiceRuntimes(_that);case GetEnvironmentStatusRequest() when getEnvironmentStatus != null:
return getEnvironmentStatus(_that);case CloseStreamRequest() when closeStream != null:
return closeStream(_that);case InterfaceSessionRegisterRequest() when interfaceSessionRegister != null:
return interfaceSessionRegister(_that);case InterfaceSessionHeartbeatRequest() when interfaceSessionHeartbeat != null:
return interfaceSessionHeartbeat(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( IdentityChallengeRequest value)  identityChallenge,required TResult Function( IdentityLoginRequest value)  identityLogin,required TResult Function( TokenLoginRequest value)  tokenLogin,required TResult Function( WhoamiRequest value)  whoami,required TResult Function( MembershipStatusRequest value)  membershipStatus,required TResult Function( MembershipCheckoutSessionCreateRequest value)  membershipCheckoutSessionCreate,required TResult Function( MembershipPurchasePrepareRequest value)  membershipPurchasePrepare,required TResult Function( MembershipPurchaseClaimRequest value)  membershipPurchaseClaim,required TResult Function( ProvisionEnvironmentRequest value)  provisionEnvironment,required TResult Function( GetBootEnvironmentDescriptorRequest value)  getBootEnvironmentDescriptor,required TResult Function( DiscoverEnvironmentConfigsRequest value)  discoverEnvironmentConfigs,required TResult Function( DiscoverServiceApiDependencyRoutesRequest value)  discoverServiceApiDependencyRoutes,required TResult Function( DiscoverHostedServicesRequest value)  discoverHostedServices,required TResult Function( DescribeHostedServiceRuntimesRequest value)  describeHostedServiceRuntimes,required TResult Function( GetEnvironmentStatusRequest value)  getEnvironmentStatus,required TResult Function( CloseStreamRequest value)  closeStream,required TResult Function( InterfaceSessionRegisterRequest value)  interfaceSessionRegister,required TResult Function( InterfaceSessionHeartbeatRequest value)  interfaceSessionHeartbeat,}){
final _that = this;
switch (_that) {
case IdentityChallengeRequest():
return identityChallenge(_that);case IdentityLoginRequest():
return identityLogin(_that);case TokenLoginRequest():
return tokenLogin(_that);case WhoamiRequest():
return whoami(_that);case MembershipStatusRequest():
return membershipStatus(_that);case MembershipCheckoutSessionCreateRequest():
return membershipCheckoutSessionCreate(_that);case MembershipPurchasePrepareRequest():
return membershipPurchasePrepare(_that);case MembershipPurchaseClaimRequest():
return membershipPurchaseClaim(_that);case ProvisionEnvironmentRequest():
return provisionEnvironment(_that);case GetBootEnvironmentDescriptorRequest():
return getBootEnvironmentDescriptor(_that);case DiscoverEnvironmentConfigsRequest():
return discoverEnvironmentConfigs(_that);case DiscoverServiceApiDependencyRoutesRequest():
return discoverServiceApiDependencyRoutes(_that);case DiscoverHostedServicesRequest():
return discoverHostedServices(_that);case DescribeHostedServiceRuntimesRequest():
return describeHostedServiceRuntimes(_that);case GetEnvironmentStatusRequest():
return getEnvironmentStatus(_that);case CloseStreamRequest():
return closeStream(_that);case InterfaceSessionRegisterRequest():
return interfaceSessionRegister(_that);case InterfaceSessionHeartbeatRequest():
return interfaceSessionHeartbeat(_that);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( IdentityChallengeRequest value)?  identityChallenge,TResult? Function( IdentityLoginRequest value)?  identityLogin,TResult? Function( TokenLoginRequest value)?  tokenLogin,TResult? Function( WhoamiRequest value)?  whoami,TResult? Function( MembershipStatusRequest value)?  membershipStatus,TResult? Function( MembershipCheckoutSessionCreateRequest value)?  membershipCheckoutSessionCreate,TResult? Function( MembershipPurchasePrepareRequest value)?  membershipPurchasePrepare,TResult? Function( MembershipPurchaseClaimRequest value)?  membershipPurchaseClaim,TResult? Function( ProvisionEnvironmentRequest value)?  provisionEnvironment,TResult? Function( GetBootEnvironmentDescriptorRequest value)?  getBootEnvironmentDescriptor,TResult? Function( DiscoverEnvironmentConfigsRequest value)?  discoverEnvironmentConfigs,TResult? Function( DiscoverServiceApiDependencyRoutesRequest value)?  discoverServiceApiDependencyRoutes,TResult? Function( DiscoverHostedServicesRequest value)?  discoverHostedServices,TResult? Function( DescribeHostedServiceRuntimesRequest value)?  describeHostedServiceRuntimes,TResult? Function( GetEnvironmentStatusRequest value)?  getEnvironmentStatus,TResult? Function( CloseStreamRequest value)?  closeStream,TResult? Function( InterfaceSessionRegisterRequest value)?  interfaceSessionRegister,TResult? Function( InterfaceSessionHeartbeatRequest value)?  interfaceSessionHeartbeat,}){
final _that = this;
switch (_that) {
case IdentityChallengeRequest() when identityChallenge != null:
return identityChallenge(_that);case IdentityLoginRequest() when identityLogin != null:
return identityLogin(_that);case TokenLoginRequest() when tokenLogin != null:
return tokenLogin(_that);case WhoamiRequest() when whoami != null:
return whoami(_that);case MembershipStatusRequest() when membershipStatus != null:
return membershipStatus(_that);case MembershipCheckoutSessionCreateRequest() when membershipCheckoutSessionCreate != null:
return membershipCheckoutSessionCreate(_that);case MembershipPurchasePrepareRequest() when membershipPurchasePrepare != null:
return membershipPurchasePrepare(_that);case MembershipPurchaseClaimRequest() when membershipPurchaseClaim != null:
return membershipPurchaseClaim(_that);case ProvisionEnvironmentRequest() when provisionEnvironment != null:
return provisionEnvironment(_that);case GetBootEnvironmentDescriptorRequest() when getBootEnvironmentDescriptor != null:
return getBootEnvironmentDescriptor(_that);case DiscoverEnvironmentConfigsRequest() when discoverEnvironmentConfigs != null:
return discoverEnvironmentConfigs(_that);case DiscoverServiceApiDependencyRoutesRequest() when discoverServiceApiDependencyRoutes != null:
return discoverServiceApiDependencyRoutes(_that);case DiscoverHostedServicesRequest() when discoverHostedServices != null:
return discoverHostedServices(_that);case DescribeHostedServiceRuntimesRequest() when describeHostedServiceRuntimes != null:
return describeHostedServiceRuntimes(_that);case GetEnvironmentStatusRequest() when getEnvironmentStatus != null:
return getEnvironmentStatus(_that);case CloseStreamRequest() when closeStream != null:
return closeStream(_that);case InterfaceSessionRegisterRequest() when interfaceSessionRegister != null:
return interfaceSessionRegister(_that);case InterfaceSessionHeartbeatRequest() when interfaceSessionHeartbeat != null:
return interfaceSessionHeartbeat(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String publicKey)?  identityChallenge,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String publicKey,  String challenge,  String signature)?  identityLogin,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String token)?  tokenLogin,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)?  whoami,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)?  membershipStatus,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String? planKey,  String? successUrl,  String? cancelUrl)?  membershipCheckoutSessionCreate,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String? planKey,  String? platform)?  membershipPurchasePrepare,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String provider,  String? planKey,  String? appleProductId,  String? appleReceipt,  String? appleTransactionId,  String? googleProductId,  String? googlePurchaseToken)?  membershipPurchaseClaim,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue environmentConfigId,  String? environmentTitle,  String? environmentDescription,  int? environmentPort,  String? databaseUrl,  String? persistenceBackend,  bool eagerReady)?  provisionEnvironment,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)?  getBootEnvironmentDescriptor,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)?  discoverEnvironmentConfigs,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue? consumerServicePackageId, @UuidValueConverter()  UuidValue? apiPackageId)?  discoverServiceApiDependencyRoutes,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)?  discoverHostedServices,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)?  describeHostedServiceRuntimes,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue environmentId)?  getEnvironmentStatus,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue networkOperationId)?  closeStream,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue interfaceId, @UuidValueConverter()  UuidValue interfaceSessionId,  String? sessionLabel,  List<String> capabilities,  int protocolVersion)?  interfaceSessionRegister,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue interfaceSessionId,  String? timestamp)?  interfaceSessionHeartbeat,required TResult orElse(),}) {final _that = this;
switch (_that) {
case IdentityChallengeRequest() when identityChallenge != null:
return identityChallenge(_that.actorId,_that.nodeId,_that.publicKey);case IdentityLoginRequest() when identityLogin != null:
return identityLogin(_that.actorId,_that.nodeId,_that.publicKey,_that.challenge,_that.signature);case TokenLoginRequest() when tokenLogin != null:
return tokenLogin(_that.actorId,_that.nodeId,_that.token);case WhoamiRequest() when whoami != null:
return whoami(_that.actorId,_that.nodeId);case MembershipStatusRequest() when membershipStatus != null:
return membershipStatus(_that.actorId,_that.nodeId);case MembershipCheckoutSessionCreateRequest() when membershipCheckoutSessionCreate != null:
return membershipCheckoutSessionCreate(_that.actorId,_that.nodeId,_that.planKey,_that.successUrl,_that.cancelUrl);case MembershipPurchasePrepareRequest() when membershipPurchasePrepare != null:
return membershipPurchasePrepare(_that.actorId,_that.nodeId,_that.planKey,_that.platform);case MembershipPurchaseClaimRequest() when membershipPurchaseClaim != null:
return membershipPurchaseClaim(_that.actorId,_that.nodeId,_that.provider,_that.planKey,_that.appleProductId,_that.appleReceipt,_that.appleTransactionId,_that.googleProductId,_that.googlePurchaseToken);case ProvisionEnvironmentRequest() when provisionEnvironment != null:
return provisionEnvironment(_that.actorId,_that.nodeId,_that.environmentConfigId,_that.environmentTitle,_that.environmentDescription,_that.environmentPort,_that.databaseUrl,_that.persistenceBackend,_that.eagerReady);case GetBootEnvironmentDescriptorRequest() when getBootEnvironmentDescriptor != null:
return getBootEnvironmentDescriptor(_that.actorId,_that.nodeId);case DiscoverEnvironmentConfigsRequest() when discoverEnvironmentConfigs != null:
return discoverEnvironmentConfigs(_that.actorId,_that.nodeId);case DiscoverServiceApiDependencyRoutesRequest() when discoverServiceApiDependencyRoutes != null:
return discoverServiceApiDependencyRoutes(_that.actorId,_that.nodeId,_that.consumerServicePackageId,_that.apiPackageId);case DiscoverHostedServicesRequest() when discoverHostedServices != null:
return discoverHostedServices(_that.actorId,_that.nodeId);case DescribeHostedServiceRuntimesRequest() when describeHostedServiceRuntimes != null:
return describeHostedServiceRuntimes(_that.actorId,_that.nodeId);case GetEnvironmentStatusRequest() when getEnvironmentStatus != null:
return getEnvironmentStatus(_that.actorId,_that.nodeId,_that.environmentId);case CloseStreamRequest() when closeStream != null:
return closeStream(_that.actorId,_that.nodeId,_that.networkOperationId);case InterfaceSessionRegisterRequest() when interfaceSessionRegister != null:
return interfaceSessionRegister(_that.actorId,_that.nodeId,_that.interfaceId,_that.interfaceSessionId,_that.sessionLabel,_that.capabilities,_that.protocolVersion);case InterfaceSessionHeartbeatRequest() when interfaceSessionHeartbeat != null:
return interfaceSessionHeartbeat(_that.actorId,_that.nodeId,_that.interfaceSessionId,_that.timestamp);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String publicKey)  identityChallenge,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String publicKey,  String challenge,  String signature)  identityLogin,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String token)  tokenLogin,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)  whoami,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)  membershipStatus,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String? planKey,  String? successUrl,  String? cancelUrl)  membershipCheckoutSessionCreate,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String? planKey,  String? platform)  membershipPurchasePrepare,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String provider,  String? planKey,  String? appleProductId,  String? appleReceipt,  String? appleTransactionId,  String? googleProductId,  String? googlePurchaseToken)  membershipPurchaseClaim,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue environmentConfigId,  String? environmentTitle,  String? environmentDescription,  int? environmentPort,  String? databaseUrl,  String? persistenceBackend,  bool eagerReady)  provisionEnvironment,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)  getBootEnvironmentDescriptor,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)  discoverEnvironmentConfigs,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue? consumerServicePackageId, @UuidValueConverter()  UuidValue? apiPackageId)  discoverServiceApiDependencyRoutes,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)  discoverHostedServices,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)  describeHostedServiceRuntimes,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue environmentId)  getEnvironmentStatus,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue networkOperationId)  closeStream,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue interfaceId, @UuidValueConverter()  UuidValue interfaceSessionId,  String? sessionLabel,  List<String> capabilities,  int protocolVersion)  interfaceSessionRegister,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue interfaceSessionId,  String? timestamp)  interfaceSessionHeartbeat,}) {final _that = this;
switch (_that) {
case IdentityChallengeRequest():
return identityChallenge(_that.actorId,_that.nodeId,_that.publicKey);case IdentityLoginRequest():
return identityLogin(_that.actorId,_that.nodeId,_that.publicKey,_that.challenge,_that.signature);case TokenLoginRequest():
return tokenLogin(_that.actorId,_that.nodeId,_that.token);case WhoamiRequest():
return whoami(_that.actorId,_that.nodeId);case MembershipStatusRequest():
return membershipStatus(_that.actorId,_that.nodeId);case MembershipCheckoutSessionCreateRequest():
return membershipCheckoutSessionCreate(_that.actorId,_that.nodeId,_that.planKey,_that.successUrl,_that.cancelUrl);case MembershipPurchasePrepareRequest():
return membershipPurchasePrepare(_that.actorId,_that.nodeId,_that.planKey,_that.platform);case MembershipPurchaseClaimRequest():
return membershipPurchaseClaim(_that.actorId,_that.nodeId,_that.provider,_that.planKey,_that.appleProductId,_that.appleReceipt,_that.appleTransactionId,_that.googleProductId,_that.googlePurchaseToken);case ProvisionEnvironmentRequest():
return provisionEnvironment(_that.actorId,_that.nodeId,_that.environmentConfigId,_that.environmentTitle,_that.environmentDescription,_that.environmentPort,_that.databaseUrl,_that.persistenceBackend,_that.eagerReady);case GetBootEnvironmentDescriptorRequest():
return getBootEnvironmentDescriptor(_that.actorId,_that.nodeId);case DiscoverEnvironmentConfigsRequest():
return discoverEnvironmentConfigs(_that.actorId,_that.nodeId);case DiscoverServiceApiDependencyRoutesRequest():
return discoverServiceApiDependencyRoutes(_that.actorId,_that.nodeId,_that.consumerServicePackageId,_that.apiPackageId);case DiscoverHostedServicesRequest():
return discoverHostedServices(_that.actorId,_that.nodeId);case DescribeHostedServiceRuntimesRequest():
return describeHostedServiceRuntimes(_that.actorId,_that.nodeId);case GetEnvironmentStatusRequest():
return getEnvironmentStatus(_that.actorId,_that.nodeId,_that.environmentId);case CloseStreamRequest():
return closeStream(_that.actorId,_that.nodeId,_that.networkOperationId);case InterfaceSessionRegisterRequest():
return interfaceSessionRegister(_that.actorId,_that.nodeId,_that.interfaceId,_that.interfaceSessionId,_that.sessionLabel,_that.capabilities,_that.protocolVersion);case InterfaceSessionHeartbeatRequest():
return interfaceSessionHeartbeat(_that.actorId,_that.nodeId,_that.interfaceSessionId,_that.timestamp);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String publicKey)?  identityChallenge,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String publicKey,  String challenge,  String signature)?  identityLogin,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String token)?  tokenLogin,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)?  whoami,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)?  membershipStatus,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String? planKey,  String? successUrl,  String? cancelUrl)?  membershipCheckoutSessionCreate,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String? planKey,  String? platform)?  membershipPurchasePrepare,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String provider,  String? planKey,  String? appleProductId,  String? appleReceipt,  String? appleTransactionId,  String? googleProductId,  String? googlePurchaseToken)?  membershipPurchaseClaim,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue environmentConfigId,  String? environmentTitle,  String? environmentDescription,  int? environmentPort,  String? databaseUrl,  String? persistenceBackend,  bool eagerReady)?  provisionEnvironment,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)?  getBootEnvironmentDescriptor,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)?  discoverEnvironmentConfigs,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue? consumerServicePackageId, @UuidValueConverter()  UuidValue? apiPackageId)?  discoverServiceApiDependencyRoutes,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)?  discoverHostedServices,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId)?  describeHostedServiceRuntimes,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue environmentId)?  getEnvironmentStatus,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue networkOperationId)?  closeStream,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue interfaceId, @UuidValueConverter()  UuidValue interfaceSessionId,  String? sessionLabel,  List<String> capabilities,  int protocolVersion)?  interfaceSessionRegister,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue interfaceSessionId,  String? timestamp)?  interfaceSessionHeartbeat,}) {final _that = this;
switch (_that) {
case IdentityChallengeRequest() when identityChallenge != null:
return identityChallenge(_that.actorId,_that.nodeId,_that.publicKey);case IdentityLoginRequest() when identityLogin != null:
return identityLogin(_that.actorId,_that.nodeId,_that.publicKey,_that.challenge,_that.signature);case TokenLoginRequest() when tokenLogin != null:
return tokenLogin(_that.actorId,_that.nodeId,_that.token);case WhoamiRequest() when whoami != null:
return whoami(_that.actorId,_that.nodeId);case MembershipStatusRequest() when membershipStatus != null:
return membershipStatus(_that.actorId,_that.nodeId);case MembershipCheckoutSessionCreateRequest() when membershipCheckoutSessionCreate != null:
return membershipCheckoutSessionCreate(_that.actorId,_that.nodeId,_that.planKey,_that.successUrl,_that.cancelUrl);case MembershipPurchasePrepareRequest() when membershipPurchasePrepare != null:
return membershipPurchasePrepare(_that.actorId,_that.nodeId,_that.planKey,_that.platform);case MembershipPurchaseClaimRequest() when membershipPurchaseClaim != null:
return membershipPurchaseClaim(_that.actorId,_that.nodeId,_that.provider,_that.planKey,_that.appleProductId,_that.appleReceipt,_that.appleTransactionId,_that.googleProductId,_that.googlePurchaseToken);case ProvisionEnvironmentRequest() when provisionEnvironment != null:
return provisionEnvironment(_that.actorId,_that.nodeId,_that.environmentConfigId,_that.environmentTitle,_that.environmentDescription,_that.environmentPort,_that.databaseUrl,_that.persistenceBackend,_that.eagerReady);case GetBootEnvironmentDescriptorRequest() when getBootEnvironmentDescriptor != null:
return getBootEnvironmentDescriptor(_that.actorId,_that.nodeId);case DiscoverEnvironmentConfigsRequest() when discoverEnvironmentConfigs != null:
return discoverEnvironmentConfigs(_that.actorId,_that.nodeId);case DiscoverServiceApiDependencyRoutesRequest() when discoverServiceApiDependencyRoutes != null:
return discoverServiceApiDependencyRoutes(_that.actorId,_that.nodeId,_that.consumerServicePackageId,_that.apiPackageId);case DiscoverHostedServicesRequest() when discoverHostedServices != null:
return discoverHostedServices(_that.actorId,_that.nodeId);case DescribeHostedServiceRuntimesRequest() when describeHostedServiceRuntimes != null:
return describeHostedServiceRuntimes(_that.actorId,_that.nodeId);case GetEnvironmentStatusRequest() when getEnvironmentStatus != null:
return getEnvironmentStatus(_that.actorId,_that.nodeId,_that.environmentId);case CloseStreamRequest() when closeStream != null:
return closeStream(_that.actorId,_that.nodeId,_that.networkOperationId);case InterfaceSessionRegisterRequest() when interfaceSessionRegister != null:
return interfaceSessionRegister(_that.actorId,_that.nodeId,_that.interfaceId,_that.interfaceSessionId,_that.sessionLabel,_that.capabilities,_that.protocolVersion);case InterfaceSessionHeartbeatRequest() when interfaceSessionHeartbeat != null:
return interfaceSessionHeartbeat(_that.actorId,_that.nodeId,_that.interfaceSessionId,_that.timestamp);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class IdentityChallengeRequest implements NetworkNodeOperationRequest {
   IdentityChallengeRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, required this.publicKey, final  String? $type}): $type = $type ?? 'identity_challenge';
  factory IdentityChallengeRequest.fromJson(Map<String, dynamic> json) => _$IdentityChallengeRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String publicKey;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$IdentityChallengeRequestCopyWith<IdentityChallengeRequest> get copyWith => _$IdentityChallengeRequestCopyWithImpl<IdentityChallengeRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$IdentityChallengeRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is IdentityChallengeRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.publicKey, publicKey) || other.publicKey == publicKey));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,publicKey);

@override
String toString() {
  return 'NetworkNodeOperationRequest.identityChallenge(actorId: $actorId, nodeId: $nodeId, publicKey: $publicKey)';
}


}

/// @nodoc
abstract mixin class $IdentityChallengeRequestCopyWith<$Res> implements $NetworkNodeOperationRequestCopyWith<$Res> {
  factory $IdentityChallengeRequestCopyWith(IdentityChallengeRequest value, $Res Function(IdentityChallengeRequest) _then) = _$IdentityChallengeRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String publicKey
});




}
/// @nodoc
class _$IdentityChallengeRequestCopyWithImpl<$Res>
    implements $IdentityChallengeRequestCopyWith<$Res> {
  _$IdentityChallengeRequestCopyWithImpl(this._self, this._then);

  final IdentityChallengeRequest _self;
  final $Res Function(IdentityChallengeRequest) _then;

/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? publicKey = null,}) {
  return _then(IdentityChallengeRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,publicKey: null == publicKey ? _self.publicKey : publicKey // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class IdentityLoginRequest implements NetworkNodeOperationRequest {
   IdentityLoginRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, required this.publicKey, required this.challenge, required this.signature, final  String? $type}): $type = $type ?? 'identity_login';
  factory IdentityLoginRequest.fromJson(Map<String, dynamic> json) => _$IdentityLoginRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String publicKey;
 final  String challenge;
 final  String signature;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$IdentityLoginRequestCopyWith<IdentityLoginRequest> get copyWith => _$IdentityLoginRequestCopyWithImpl<IdentityLoginRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$IdentityLoginRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is IdentityLoginRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.publicKey, publicKey) || other.publicKey == publicKey)&&(identical(other.challenge, challenge) || other.challenge == challenge)&&(identical(other.signature, signature) || other.signature == signature));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,publicKey,challenge,signature);

@override
String toString() {
  return 'NetworkNodeOperationRequest.identityLogin(actorId: $actorId, nodeId: $nodeId, publicKey: $publicKey, challenge: $challenge, signature: $signature)';
}


}

/// @nodoc
abstract mixin class $IdentityLoginRequestCopyWith<$Res> implements $NetworkNodeOperationRequestCopyWith<$Res> {
  factory $IdentityLoginRequestCopyWith(IdentityLoginRequest value, $Res Function(IdentityLoginRequest) _then) = _$IdentityLoginRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String publicKey, String challenge, String signature
});




}
/// @nodoc
class _$IdentityLoginRequestCopyWithImpl<$Res>
    implements $IdentityLoginRequestCopyWith<$Res> {
  _$IdentityLoginRequestCopyWithImpl(this._self, this._then);

  final IdentityLoginRequest _self;
  final $Res Function(IdentityLoginRequest) _then;

/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? publicKey = null,Object? challenge = null,Object? signature = null,}) {
  return _then(IdentityLoginRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,publicKey: null == publicKey ? _self.publicKey : publicKey // ignore: cast_nullable_to_non_nullable
as String,challenge: null == challenge ? _self.challenge : challenge // ignore: cast_nullable_to_non_nullable
as String,signature: null == signature ? _self.signature : signature // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class TokenLoginRequest implements NetworkNodeOperationRequest {
   TokenLoginRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, required this.token, final  String? $type}): $type = $type ?? 'token_login';
  factory TokenLoginRequest.fromJson(Map<String, dynamic> json) => _$TokenLoginRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String token;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$TokenLoginRequestCopyWith<TokenLoginRequest> get copyWith => _$TokenLoginRequestCopyWithImpl<TokenLoginRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$TokenLoginRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is TokenLoginRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.token, token) || other.token == token));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,token);

@override
String toString() {
  return 'NetworkNodeOperationRequest.tokenLogin(actorId: $actorId, nodeId: $nodeId, token: $token)';
}


}

/// @nodoc
abstract mixin class $TokenLoginRequestCopyWith<$Res> implements $NetworkNodeOperationRequestCopyWith<$Res> {
  factory $TokenLoginRequestCopyWith(TokenLoginRequest value, $Res Function(TokenLoginRequest) _then) = _$TokenLoginRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String token
});




}
/// @nodoc
class _$TokenLoginRequestCopyWithImpl<$Res>
    implements $TokenLoginRequestCopyWith<$Res> {
  _$TokenLoginRequestCopyWithImpl(this._self, this._then);

  final TokenLoginRequest _self;
  final $Res Function(TokenLoginRequest) _then;

/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? token = null,}) {
  return _then(TokenLoginRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,token: null == token ? _self.token : token // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class WhoamiRequest implements NetworkNodeOperationRequest {
   WhoamiRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, final  String? $type}): $type = $type ?? 'whoami';
  factory WhoamiRequest.fromJson(Map<String, dynamic> json) => _$WhoamiRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$WhoamiRequestCopyWith<WhoamiRequest> get copyWith => _$WhoamiRequestCopyWithImpl<WhoamiRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$WhoamiRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is WhoamiRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId);

@override
String toString() {
  return 'NetworkNodeOperationRequest.whoami(actorId: $actorId, nodeId: $nodeId)';
}


}

/// @nodoc
abstract mixin class $WhoamiRequestCopyWith<$Res> implements $NetworkNodeOperationRequestCopyWith<$Res> {
  factory $WhoamiRequestCopyWith(WhoamiRequest value, $Res Function(WhoamiRequest) _then) = _$WhoamiRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId
});




}
/// @nodoc
class _$WhoamiRequestCopyWithImpl<$Res>
    implements $WhoamiRequestCopyWith<$Res> {
  _$WhoamiRequestCopyWithImpl(this._self, this._then);

  final WhoamiRequest _self;
  final $Res Function(WhoamiRequest) _then;

/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,}) {
  return _then(WhoamiRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class MembershipStatusRequest implements NetworkNodeOperationRequest {
   MembershipStatusRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, final  String? $type}): $type = $type ?? 'membership_status';
  factory MembershipStatusRequest.fromJson(Map<String, dynamic> json) => _$MembershipStatusRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$MembershipStatusRequestCopyWith<MembershipStatusRequest> get copyWith => _$MembershipStatusRequestCopyWithImpl<MembershipStatusRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$MembershipStatusRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is MembershipStatusRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId);

@override
String toString() {
  return 'NetworkNodeOperationRequest.membershipStatus(actorId: $actorId, nodeId: $nodeId)';
}


}

/// @nodoc
abstract mixin class $MembershipStatusRequestCopyWith<$Res> implements $NetworkNodeOperationRequestCopyWith<$Res> {
  factory $MembershipStatusRequestCopyWith(MembershipStatusRequest value, $Res Function(MembershipStatusRequest) _then) = _$MembershipStatusRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId
});




}
/// @nodoc
class _$MembershipStatusRequestCopyWithImpl<$Res>
    implements $MembershipStatusRequestCopyWith<$Res> {
  _$MembershipStatusRequestCopyWithImpl(this._self, this._then);

  final MembershipStatusRequest _self;
  final $Res Function(MembershipStatusRequest) _then;

/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,}) {
  return _then(MembershipStatusRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class MembershipCheckoutSessionCreateRequest implements NetworkNodeOperationRequest {
   MembershipCheckoutSessionCreateRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, this.planKey, this.successUrl, this.cancelUrl, final  String? $type}): $type = $type ?? 'membership_checkout_session_create';
  factory MembershipCheckoutSessionCreateRequest.fromJson(Map<String, dynamic> json) => _$MembershipCheckoutSessionCreateRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String? planKey;
 final  String? successUrl;
 final  String? cancelUrl;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$MembershipCheckoutSessionCreateRequestCopyWith<MembershipCheckoutSessionCreateRequest> get copyWith => _$MembershipCheckoutSessionCreateRequestCopyWithImpl<MembershipCheckoutSessionCreateRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$MembershipCheckoutSessionCreateRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is MembershipCheckoutSessionCreateRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.planKey, planKey) || other.planKey == planKey)&&(identical(other.successUrl, successUrl) || other.successUrl == successUrl)&&(identical(other.cancelUrl, cancelUrl) || other.cancelUrl == cancelUrl));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,planKey,successUrl,cancelUrl);

@override
String toString() {
  return 'NetworkNodeOperationRequest.membershipCheckoutSessionCreate(actorId: $actorId, nodeId: $nodeId, planKey: $planKey, successUrl: $successUrl, cancelUrl: $cancelUrl)';
}


}

/// @nodoc
abstract mixin class $MembershipCheckoutSessionCreateRequestCopyWith<$Res> implements $NetworkNodeOperationRequestCopyWith<$Res> {
  factory $MembershipCheckoutSessionCreateRequestCopyWith(MembershipCheckoutSessionCreateRequest value, $Res Function(MembershipCheckoutSessionCreateRequest) _then) = _$MembershipCheckoutSessionCreateRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String? planKey, String? successUrl, String? cancelUrl
});




}
/// @nodoc
class _$MembershipCheckoutSessionCreateRequestCopyWithImpl<$Res>
    implements $MembershipCheckoutSessionCreateRequestCopyWith<$Res> {
  _$MembershipCheckoutSessionCreateRequestCopyWithImpl(this._self, this._then);

  final MembershipCheckoutSessionCreateRequest _self;
  final $Res Function(MembershipCheckoutSessionCreateRequest) _then;

/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? planKey = freezed,Object? successUrl = freezed,Object? cancelUrl = freezed,}) {
  return _then(MembershipCheckoutSessionCreateRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,planKey: freezed == planKey ? _self.planKey : planKey // ignore: cast_nullable_to_non_nullable
as String?,successUrl: freezed == successUrl ? _self.successUrl : successUrl // ignore: cast_nullable_to_non_nullable
as String?,cancelUrl: freezed == cancelUrl ? _self.cancelUrl : cancelUrl // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class MembershipPurchasePrepareRequest implements NetworkNodeOperationRequest {
   MembershipPurchasePrepareRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, this.planKey, this.platform, final  String? $type}): $type = $type ?? 'membership_purchase_prepare';
  factory MembershipPurchasePrepareRequest.fromJson(Map<String, dynamic> json) => _$MembershipPurchasePrepareRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String? planKey;
 final  String? platform;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$MembershipPurchasePrepareRequestCopyWith<MembershipPurchasePrepareRequest> get copyWith => _$MembershipPurchasePrepareRequestCopyWithImpl<MembershipPurchasePrepareRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$MembershipPurchasePrepareRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is MembershipPurchasePrepareRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.planKey, planKey) || other.planKey == planKey)&&(identical(other.platform, platform) || other.platform == platform));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,planKey,platform);

@override
String toString() {
  return 'NetworkNodeOperationRequest.membershipPurchasePrepare(actorId: $actorId, nodeId: $nodeId, planKey: $planKey, platform: $platform)';
}


}

/// @nodoc
abstract mixin class $MembershipPurchasePrepareRequestCopyWith<$Res> implements $NetworkNodeOperationRequestCopyWith<$Res> {
  factory $MembershipPurchasePrepareRequestCopyWith(MembershipPurchasePrepareRequest value, $Res Function(MembershipPurchasePrepareRequest) _then) = _$MembershipPurchasePrepareRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String? planKey, String? platform
});




}
/// @nodoc
class _$MembershipPurchasePrepareRequestCopyWithImpl<$Res>
    implements $MembershipPurchasePrepareRequestCopyWith<$Res> {
  _$MembershipPurchasePrepareRequestCopyWithImpl(this._self, this._then);

  final MembershipPurchasePrepareRequest _self;
  final $Res Function(MembershipPurchasePrepareRequest) _then;

/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? planKey = freezed,Object? platform = freezed,}) {
  return _then(MembershipPurchasePrepareRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,planKey: freezed == planKey ? _self.planKey : planKey // ignore: cast_nullable_to_non_nullable
as String?,platform: freezed == platform ? _self.platform : platform // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class MembershipPurchaseClaimRequest implements NetworkNodeOperationRequest {
   MembershipPurchaseClaimRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, required this.provider, this.planKey, this.appleProductId, this.appleReceipt, this.appleTransactionId, this.googleProductId, this.googlePurchaseToken, final  String? $type}): $type = $type ?? 'membership_purchase_claim';
  factory MembershipPurchaseClaimRequest.fromJson(Map<String, dynamic> json) => _$MembershipPurchaseClaimRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String provider;
 final  String? planKey;
 final  String? appleProductId;
 final  String? appleReceipt;
 final  String? appleTransactionId;
 final  String? googleProductId;
 final  String? googlePurchaseToken;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$MembershipPurchaseClaimRequestCopyWith<MembershipPurchaseClaimRequest> get copyWith => _$MembershipPurchaseClaimRequestCopyWithImpl<MembershipPurchaseClaimRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$MembershipPurchaseClaimRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is MembershipPurchaseClaimRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.provider, provider) || other.provider == provider)&&(identical(other.planKey, planKey) || other.planKey == planKey)&&(identical(other.appleProductId, appleProductId) || other.appleProductId == appleProductId)&&(identical(other.appleReceipt, appleReceipt) || other.appleReceipt == appleReceipt)&&(identical(other.appleTransactionId, appleTransactionId) || other.appleTransactionId == appleTransactionId)&&(identical(other.googleProductId, googleProductId) || other.googleProductId == googleProductId)&&(identical(other.googlePurchaseToken, googlePurchaseToken) || other.googlePurchaseToken == googlePurchaseToken));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,provider,planKey,appleProductId,appleReceipt,appleTransactionId,googleProductId,googlePurchaseToken);

@override
String toString() {
  return 'NetworkNodeOperationRequest.membershipPurchaseClaim(actorId: $actorId, nodeId: $nodeId, provider: $provider, planKey: $planKey, appleProductId: $appleProductId, appleReceipt: $appleReceipt, appleTransactionId: $appleTransactionId, googleProductId: $googleProductId, googlePurchaseToken: $googlePurchaseToken)';
}


}

/// @nodoc
abstract mixin class $MembershipPurchaseClaimRequestCopyWith<$Res> implements $NetworkNodeOperationRequestCopyWith<$Res> {
  factory $MembershipPurchaseClaimRequestCopyWith(MembershipPurchaseClaimRequest value, $Res Function(MembershipPurchaseClaimRequest) _then) = _$MembershipPurchaseClaimRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String provider, String? planKey, String? appleProductId, String? appleReceipt, String? appleTransactionId, String? googleProductId, String? googlePurchaseToken
});




}
/// @nodoc
class _$MembershipPurchaseClaimRequestCopyWithImpl<$Res>
    implements $MembershipPurchaseClaimRequestCopyWith<$Res> {
  _$MembershipPurchaseClaimRequestCopyWithImpl(this._self, this._then);

  final MembershipPurchaseClaimRequest _self;
  final $Res Function(MembershipPurchaseClaimRequest) _then;

/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? provider = null,Object? planKey = freezed,Object? appleProductId = freezed,Object? appleReceipt = freezed,Object? appleTransactionId = freezed,Object? googleProductId = freezed,Object? googlePurchaseToken = freezed,}) {
  return _then(MembershipPurchaseClaimRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,provider: null == provider ? _self.provider : provider // ignore: cast_nullable_to_non_nullable
as String,planKey: freezed == planKey ? _self.planKey : planKey // ignore: cast_nullable_to_non_nullable
as String?,appleProductId: freezed == appleProductId ? _self.appleProductId : appleProductId // ignore: cast_nullable_to_non_nullable
as String?,appleReceipt: freezed == appleReceipt ? _self.appleReceipt : appleReceipt // ignore: cast_nullable_to_non_nullable
as String?,appleTransactionId: freezed == appleTransactionId ? _self.appleTransactionId : appleTransactionId // ignore: cast_nullable_to_non_nullable
as String?,googleProductId: freezed == googleProductId ? _self.googleProductId : googleProductId // ignore: cast_nullable_to_non_nullable
as String?,googlePurchaseToken: freezed == googlePurchaseToken ? _self.googlePurchaseToken : googlePurchaseToken // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class ProvisionEnvironmentRequest implements NetworkNodeOperationRequest {
   ProvisionEnvironmentRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, @UuidValueConverter() required this.environmentConfigId, this.environmentTitle, this.environmentDescription, this.environmentPort, this.databaseUrl, this.persistenceBackend, required this.eagerReady, final  String? $type}): $type = $type ?? 'provision_environment';
  factory ProvisionEnvironmentRequest.fromJson(Map<String, dynamic> json) => _$ProvisionEnvironmentRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
@UuidValueConverter() final  UuidValue environmentConfigId;
 final  String? environmentTitle;
 final  String? environmentDescription;
 final  int? environmentPort;
 final  String? databaseUrl;
 final  String? persistenceBackend;
 final  bool eagerReady;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ProvisionEnvironmentRequestCopyWith<ProvisionEnvironmentRequest> get copyWith => _$ProvisionEnvironmentRequestCopyWithImpl<ProvisionEnvironmentRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ProvisionEnvironmentRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ProvisionEnvironmentRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.environmentConfigId, environmentConfigId) || other.environmentConfigId == environmentConfigId)&&(identical(other.environmentTitle, environmentTitle) || other.environmentTitle == environmentTitle)&&(identical(other.environmentDescription, environmentDescription) || other.environmentDescription == environmentDescription)&&(identical(other.environmentPort, environmentPort) || other.environmentPort == environmentPort)&&(identical(other.databaseUrl, databaseUrl) || other.databaseUrl == databaseUrl)&&(identical(other.persistenceBackend, persistenceBackend) || other.persistenceBackend == persistenceBackend)&&(identical(other.eagerReady, eagerReady) || other.eagerReady == eagerReady));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,environmentConfigId,environmentTitle,environmentDescription,environmentPort,databaseUrl,persistenceBackend,eagerReady);

@override
String toString() {
  return 'NetworkNodeOperationRequest.provisionEnvironment(actorId: $actorId, nodeId: $nodeId, environmentConfigId: $environmentConfigId, environmentTitle: $environmentTitle, environmentDescription: $environmentDescription, environmentPort: $environmentPort, databaseUrl: $databaseUrl, persistenceBackend: $persistenceBackend, eagerReady: $eagerReady)';
}


}

/// @nodoc
abstract mixin class $ProvisionEnvironmentRequestCopyWith<$Res> implements $NetworkNodeOperationRequestCopyWith<$Res> {
  factory $ProvisionEnvironmentRequestCopyWith(ProvisionEnvironmentRequest value, $Res Function(ProvisionEnvironmentRequest) _then) = _$ProvisionEnvironmentRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId,@UuidValueConverter() UuidValue environmentConfigId, String? environmentTitle, String? environmentDescription, int? environmentPort, String? databaseUrl, String? persistenceBackend, bool eagerReady
});




}
/// @nodoc
class _$ProvisionEnvironmentRequestCopyWithImpl<$Res>
    implements $ProvisionEnvironmentRequestCopyWith<$Res> {
  _$ProvisionEnvironmentRequestCopyWithImpl(this._self, this._then);

  final ProvisionEnvironmentRequest _self;
  final $Res Function(ProvisionEnvironmentRequest) _then;

/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? environmentConfigId = null,Object? environmentTitle = freezed,Object? environmentDescription = freezed,Object? environmentPort = freezed,Object? databaseUrl = freezed,Object? persistenceBackend = freezed,Object? eagerReady = null,}) {
  return _then(ProvisionEnvironmentRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentConfigId: null == environmentConfigId ? _self.environmentConfigId : environmentConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentTitle: freezed == environmentTitle ? _self.environmentTitle : environmentTitle // ignore: cast_nullable_to_non_nullable
as String?,environmentDescription: freezed == environmentDescription ? _self.environmentDescription : environmentDescription // ignore: cast_nullable_to_non_nullable
as String?,environmentPort: freezed == environmentPort ? _self.environmentPort : environmentPort // ignore: cast_nullable_to_non_nullable
as int?,databaseUrl: freezed == databaseUrl ? _self.databaseUrl : databaseUrl // ignore: cast_nullable_to_non_nullable
as String?,persistenceBackend: freezed == persistenceBackend ? _self.persistenceBackend : persistenceBackend // ignore: cast_nullable_to_non_nullable
as String?,eagerReady: null == eagerReady ? _self.eagerReady : eagerReady // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class GetBootEnvironmentDescriptorRequest implements NetworkNodeOperationRequest {
   GetBootEnvironmentDescriptorRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, final  String? $type}): $type = $type ?? 'get_boot_environment_descriptor';
  factory GetBootEnvironmentDescriptorRequest.fromJson(Map<String, dynamic> json) => _$GetBootEnvironmentDescriptorRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$GetBootEnvironmentDescriptorRequestCopyWith<GetBootEnvironmentDescriptorRequest> get copyWith => _$GetBootEnvironmentDescriptorRequestCopyWithImpl<GetBootEnvironmentDescriptorRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$GetBootEnvironmentDescriptorRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is GetBootEnvironmentDescriptorRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId);

@override
String toString() {
  return 'NetworkNodeOperationRequest.getBootEnvironmentDescriptor(actorId: $actorId, nodeId: $nodeId)';
}


}

/// @nodoc
abstract mixin class $GetBootEnvironmentDescriptorRequestCopyWith<$Res> implements $NetworkNodeOperationRequestCopyWith<$Res> {
  factory $GetBootEnvironmentDescriptorRequestCopyWith(GetBootEnvironmentDescriptorRequest value, $Res Function(GetBootEnvironmentDescriptorRequest) _then) = _$GetBootEnvironmentDescriptorRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId
});




}
/// @nodoc
class _$GetBootEnvironmentDescriptorRequestCopyWithImpl<$Res>
    implements $GetBootEnvironmentDescriptorRequestCopyWith<$Res> {
  _$GetBootEnvironmentDescriptorRequestCopyWithImpl(this._self, this._then);

  final GetBootEnvironmentDescriptorRequest _self;
  final $Res Function(GetBootEnvironmentDescriptorRequest) _then;

/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,}) {
  return _then(GetBootEnvironmentDescriptorRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DiscoverEnvironmentConfigsRequest implements NetworkNodeOperationRequest {
   DiscoverEnvironmentConfigsRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, final  String? $type}): $type = $type ?? 'discover_environment_configs';
  factory DiscoverEnvironmentConfigsRequest.fromJson(Map<String, dynamic> json) => _$DiscoverEnvironmentConfigsRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DiscoverEnvironmentConfigsRequestCopyWith<DiscoverEnvironmentConfigsRequest> get copyWith => _$DiscoverEnvironmentConfigsRequestCopyWithImpl<DiscoverEnvironmentConfigsRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DiscoverEnvironmentConfigsRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DiscoverEnvironmentConfigsRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId);

@override
String toString() {
  return 'NetworkNodeOperationRequest.discoverEnvironmentConfigs(actorId: $actorId, nodeId: $nodeId)';
}


}

/// @nodoc
abstract mixin class $DiscoverEnvironmentConfigsRequestCopyWith<$Res> implements $NetworkNodeOperationRequestCopyWith<$Res> {
  factory $DiscoverEnvironmentConfigsRequestCopyWith(DiscoverEnvironmentConfigsRequest value, $Res Function(DiscoverEnvironmentConfigsRequest) _then) = _$DiscoverEnvironmentConfigsRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId
});




}
/// @nodoc
class _$DiscoverEnvironmentConfigsRequestCopyWithImpl<$Res>
    implements $DiscoverEnvironmentConfigsRequestCopyWith<$Res> {
  _$DiscoverEnvironmentConfigsRequestCopyWithImpl(this._self, this._then);

  final DiscoverEnvironmentConfigsRequest _self;
  final $Res Function(DiscoverEnvironmentConfigsRequest) _then;

/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,}) {
  return _then(DiscoverEnvironmentConfigsRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DiscoverServiceApiDependencyRoutesRequest implements NetworkNodeOperationRequest {
   DiscoverServiceApiDependencyRoutesRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, @UuidValueConverter() this.consumerServicePackageId, @UuidValueConverter() this.apiPackageId, final  String? $type}): $type = $type ?? 'discover_service_api_dependency_routes';
  factory DiscoverServiceApiDependencyRoutesRequest.fromJson(Map<String, dynamic> json) => _$DiscoverServiceApiDependencyRoutesRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
@UuidValueConverter() final  UuidValue? consumerServicePackageId;
@UuidValueConverter() final  UuidValue? apiPackageId;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DiscoverServiceApiDependencyRoutesRequestCopyWith<DiscoverServiceApiDependencyRoutesRequest> get copyWith => _$DiscoverServiceApiDependencyRoutesRequestCopyWithImpl<DiscoverServiceApiDependencyRoutesRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DiscoverServiceApiDependencyRoutesRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DiscoverServiceApiDependencyRoutesRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.consumerServicePackageId, consumerServicePackageId) || other.consumerServicePackageId == consumerServicePackageId)&&(identical(other.apiPackageId, apiPackageId) || other.apiPackageId == apiPackageId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,consumerServicePackageId,apiPackageId);

@override
String toString() {
  return 'NetworkNodeOperationRequest.discoverServiceApiDependencyRoutes(actorId: $actorId, nodeId: $nodeId, consumerServicePackageId: $consumerServicePackageId, apiPackageId: $apiPackageId)';
}


}

/// @nodoc
abstract mixin class $DiscoverServiceApiDependencyRoutesRequestCopyWith<$Res> implements $NetworkNodeOperationRequestCopyWith<$Res> {
  factory $DiscoverServiceApiDependencyRoutesRequestCopyWith(DiscoverServiceApiDependencyRoutesRequest value, $Res Function(DiscoverServiceApiDependencyRoutesRequest) _then) = _$DiscoverServiceApiDependencyRoutesRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId,@UuidValueConverter() UuidValue? consumerServicePackageId,@UuidValueConverter() UuidValue? apiPackageId
});




}
/// @nodoc
class _$DiscoverServiceApiDependencyRoutesRequestCopyWithImpl<$Res>
    implements $DiscoverServiceApiDependencyRoutesRequestCopyWith<$Res> {
  _$DiscoverServiceApiDependencyRoutesRequestCopyWithImpl(this._self, this._then);

  final DiscoverServiceApiDependencyRoutesRequest _self;
  final $Res Function(DiscoverServiceApiDependencyRoutesRequest) _then;

/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? consumerServicePackageId = freezed,Object? apiPackageId = freezed,}) {
  return _then(DiscoverServiceApiDependencyRoutesRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,consumerServicePackageId: freezed == consumerServicePackageId ? _self.consumerServicePackageId : consumerServicePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,apiPackageId: freezed == apiPackageId ? _self.apiPackageId : apiPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DiscoverHostedServicesRequest implements NetworkNodeOperationRequest {
   DiscoverHostedServicesRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, final  String? $type}): $type = $type ?? 'discover_hosted_services';
  factory DiscoverHostedServicesRequest.fromJson(Map<String, dynamic> json) => _$DiscoverHostedServicesRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DiscoverHostedServicesRequestCopyWith<DiscoverHostedServicesRequest> get copyWith => _$DiscoverHostedServicesRequestCopyWithImpl<DiscoverHostedServicesRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DiscoverHostedServicesRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DiscoverHostedServicesRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId);

@override
String toString() {
  return 'NetworkNodeOperationRequest.discoverHostedServices(actorId: $actorId, nodeId: $nodeId)';
}


}

/// @nodoc
abstract mixin class $DiscoverHostedServicesRequestCopyWith<$Res> implements $NetworkNodeOperationRequestCopyWith<$Res> {
  factory $DiscoverHostedServicesRequestCopyWith(DiscoverHostedServicesRequest value, $Res Function(DiscoverHostedServicesRequest) _then) = _$DiscoverHostedServicesRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId
});




}
/// @nodoc
class _$DiscoverHostedServicesRequestCopyWithImpl<$Res>
    implements $DiscoverHostedServicesRequestCopyWith<$Res> {
  _$DiscoverHostedServicesRequestCopyWithImpl(this._self, this._then);

  final DiscoverHostedServicesRequest _self;
  final $Res Function(DiscoverHostedServicesRequest) _then;

/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,}) {
  return _then(DiscoverHostedServicesRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DescribeHostedServiceRuntimesRequest implements NetworkNodeOperationRequest {
   DescribeHostedServiceRuntimesRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, final  String? $type}): $type = $type ?? 'describe_hosted_service_runtimes';
  factory DescribeHostedServiceRuntimesRequest.fromJson(Map<String, dynamic> json) => _$DescribeHostedServiceRuntimesRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DescribeHostedServiceRuntimesRequestCopyWith<DescribeHostedServiceRuntimesRequest> get copyWith => _$DescribeHostedServiceRuntimesRequestCopyWithImpl<DescribeHostedServiceRuntimesRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DescribeHostedServiceRuntimesRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DescribeHostedServiceRuntimesRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId);

@override
String toString() {
  return 'NetworkNodeOperationRequest.describeHostedServiceRuntimes(actorId: $actorId, nodeId: $nodeId)';
}


}

/// @nodoc
abstract mixin class $DescribeHostedServiceRuntimesRequestCopyWith<$Res> implements $NetworkNodeOperationRequestCopyWith<$Res> {
  factory $DescribeHostedServiceRuntimesRequestCopyWith(DescribeHostedServiceRuntimesRequest value, $Res Function(DescribeHostedServiceRuntimesRequest) _then) = _$DescribeHostedServiceRuntimesRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId
});




}
/// @nodoc
class _$DescribeHostedServiceRuntimesRequestCopyWithImpl<$Res>
    implements $DescribeHostedServiceRuntimesRequestCopyWith<$Res> {
  _$DescribeHostedServiceRuntimesRequestCopyWithImpl(this._self, this._then);

  final DescribeHostedServiceRuntimesRequest _self;
  final $Res Function(DescribeHostedServiceRuntimesRequest) _then;

/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,}) {
  return _then(DescribeHostedServiceRuntimesRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class GetEnvironmentStatusRequest implements NetworkNodeOperationRequest {
   GetEnvironmentStatusRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, @UuidValueConverter() required this.environmentId, final  String? $type}): $type = $type ?? 'get_environment_status';
  factory GetEnvironmentStatusRequest.fromJson(Map<String, dynamic> json) => _$GetEnvironmentStatusRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
@UuidValueConverter() final  UuidValue environmentId;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$GetEnvironmentStatusRequestCopyWith<GetEnvironmentStatusRequest> get copyWith => _$GetEnvironmentStatusRequestCopyWithImpl<GetEnvironmentStatusRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$GetEnvironmentStatusRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is GetEnvironmentStatusRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,environmentId);

@override
String toString() {
  return 'NetworkNodeOperationRequest.getEnvironmentStatus(actorId: $actorId, nodeId: $nodeId, environmentId: $environmentId)';
}


}

/// @nodoc
abstract mixin class $GetEnvironmentStatusRequestCopyWith<$Res> implements $NetworkNodeOperationRequestCopyWith<$Res> {
  factory $GetEnvironmentStatusRequestCopyWith(GetEnvironmentStatusRequest value, $Res Function(GetEnvironmentStatusRequest) _then) = _$GetEnvironmentStatusRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId,@UuidValueConverter() UuidValue environmentId
});




}
/// @nodoc
class _$GetEnvironmentStatusRequestCopyWithImpl<$Res>
    implements $GetEnvironmentStatusRequestCopyWith<$Res> {
  _$GetEnvironmentStatusRequestCopyWithImpl(this._self, this._then);

  final GetEnvironmentStatusRequest _self;
  final $Res Function(GetEnvironmentStatusRequest) _then;

/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? environmentId = null,}) {
  return _then(GetEnvironmentStatusRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentId: null == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class CloseStreamRequest implements NetworkNodeOperationRequest {
   CloseStreamRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, @UuidValueConverter() required this.networkOperationId, final  String? $type}): $type = $type ?? 'close_stream';
  factory CloseStreamRequest.fromJson(Map<String, dynamic> json) => _$CloseStreamRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
@UuidValueConverter() final  UuidValue networkOperationId;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$CloseStreamRequestCopyWith<CloseStreamRequest> get copyWith => _$CloseStreamRequestCopyWithImpl<CloseStreamRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$CloseStreamRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is CloseStreamRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.networkOperationId, networkOperationId) || other.networkOperationId == networkOperationId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,networkOperationId);

@override
String toString() {
  return 'NetworkNodeOperationRequest.closeStream(actorId: $actorId, nodeId: $nodeId, networkOperationId: $networkOperationId)';
}


}

/// @nodoc
abstract mixin class $CloseStreamRequestCopyWith<$Res> implements $NetworkNodeOperationRequestCopyWith<$Res> {
  factory $CloseStreamRequestCopyWith(CloseStreamRequest value, $Res Function(CloseStreamRequest) _then) = _$CloseStreamRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId,@UuidValueConverter() UuidValue networkOperationId
});




}
/// @nodoc
class _$CloseStreamRequestCopyWithImpl<$Res>
    implements $CloseStreamRequestCopyWith<$Res> {
  _$CloseStreamRequestCopyWithImpl(this._self, this._then);

  final CloseStreamRequest _self;
  final $Res Function(CloseStreamRequest) _then;

/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? networkOperationId = null,}) {
  return _then(CloseStreamRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,networkOperationId: null == networkOperationId ? _self.networkOperationId : networkOperationId // ignore: cast_nullable_to_non_nullable
as UuidValue,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceSessionRegisterRequest implements NetworkNodeOperationRequest {
   InterfaceSessionRegisterRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, @UuidValueConverter() required this.interfaceId, @UuidValueConverter() required this.interfaceSessionId, this.sessionLabel, final  List<String> capabilities = const [], required this.protocolVersion, final  String? $type}): _capabilities = capabilities,$type = $type ?? 'interface_session_register';
  factory InterfaceSessionRegisterRequest.fromJson(Map<String, dynamic> json) => _$InterfaceSessionRegisterRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
@UuidValueConverter() final  UuidValue interfaceId;
@UuidValueConverter() final  UuidValue interfaceSessionId;
 final  String? sessionLabel;
 final  List<String> _capabilities;
@JsonKey() List<String> get capabilities {
  if (_capabilities is EqualUnmodifiableListView) return _capabilities;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_capabilities);
}

 final  int protocolVersion;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSessionRegisterRequestCopyWith<InterfaceSessionRegisterRequest> get copyWith => _$InterfaceSessionRegisterRequestCopyWithImpl<InterfaceSessionRegisterRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSessionRegisterRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSessionRegisterRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.interfaceId, interfaceId) || other.interfaceId == interfaceId)&&(identical(other.interfaceSessionId, interfaceSessionId) || other.interfaceSessionId == interfaceSessionId)&&(identical(other.sessionLabel, sessionLabel) || other.sessionLabel == sessionLabel)&&const DeepCollectionEquality().equals(other._capabilities, _capabilities)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,interfaceId,interfaceSessionId,sessionLabel,const DeepCollectionEquality().hash(_capabilities),protocolVersion);

@override
String toString() {
  return 'NetworkNodeOperationRequest.interfaceSessionRegister(actorId: $actorId, nodeId: $nodeId, interfaceId: $interfaceId, interfaceSessionId: $interfaceSessionId, sessionLabel: $sessionLabel, capabilities: $capabilities, protocolVersion: $protocolVersion)';
}


}

/// @nodoc
abstract mixin class $InterfaceSessionRegisterRequestCopyWith<$Res> implements $NetworkNodeOperationRequestCopyWith<$Res> {
  factory $InterfaceSessionRegisterRequestCopyWith(InterfaceSessionRegisterRequest value, $Res Function(InterfaceSessionRegisterRequest) _then) = _$InterfaceSessionRegisterRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId,@UuidValueConverter() UuidValue interfaceId,@UuidValueConverter() UuidValue interfaceSessionId, String? sessionLabel, List<String> capabilities, int protocolVersion
});




}
/// @nodoc
class _$InterfaceSessionRegisterRequestCopyWithImpl<$Res>
    implements $InterfaceSessionRegisterRequestCopyWith<$Res> {
  _$InterfaceSessionRegisterRequestCopyWithImpl(this._self, this._then);

  final InterfaceSessionRegisterRequest _self;
  final $Res Function(InterfaceSessionRegisterRequest) _then;

/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? interfaceId = null,Object? interfaceSessionId = null,Object? sessionLabel = freezed,Object? capabilities = null,Object? protocolVersion = null,}) {
  return _then(InterfaceSessionRegisterRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,interfaceId: null == interfaceId ? _self.interfaceId : interfaceId // ignore: cast_nullable_to_non_nullable
as UuidValue,interfaceSessionId: null == interfaceSessionId ? _self.interfaceSessionId : interfaceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,sessionLabel: freezed == sessionLabel ? _self.sessionLabel : sessionLabel // ignore: cast_nullable_to_non_nullable
as String?,capabilities: null == capabilities ? _self._capabilities : capabilities // ignore: cast_nullable_to_non_nullable
as List<String>,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceSessionHeartbeatRequest implements NetworkNodeOperationRequest {
   InterfaceSessionHeartbeatRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, @UuidValueConverter() required this.interfaceSessionId, this.timestamp, final  String? $type}): $type = $type ?? 'interface_session_heartbeat';
  factory InterfaceSessionHeartbeatRequest.fromJson(Map<String, dynamic> json) => _$InterfaceSessionHeartbeatRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
@UuidValueConverter() final  UuidValue interfaceSessionId;
 final  String? timestamp;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSessionHeartbeatRequestCopyWith<InterfaceSessionHeartbeatRequest> get copyWith => _$InterfaceSessionHeartbeatRequestCopyWithImpl<InterfaceSessionHeartbeatRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSessionHeartbeatRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSessionHeartbeatRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.interfaceSessionId, interfaceSessionId) || other.interfaceSessionId == interfaceSessionId)&&(identical(other.timestamp, timestamp) || other.timestamp == timestamp));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,interfaceSessionId,timestamp);

@override
String toString() {
  return 'NetworkNodeOperationRequest.interfaceSessionHeartbeat(actorId: $actorId, nodeId: $nodeId, interfaceSessionId: $interfaceSessionId, timestamp: $timestamp)';
}


}

/// @nodoc
abstract mixin class $InterfaceSessionHeartbeatRequestCopyWith<$Res> implements $NetworkNodeOperationRequestCopyWith<$Res> {
  factory $InterfaceSessionHeartbeatRequestCopyWith(InterfaceSessionHeartbeatRequest value, $Res Function(InterfaceSessionHeartbeatRequest) _then) = _$InterfaceSessionHeartbeatRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId,@UuidValueConverter() UuidValue interfaceSessionId, String? timestamp
});




}
/// @nodoc
class _$InterfaceSessionHeartbeatRequestCopyWithImpl<$Res>
    implements $InterfaceSessionHeartbeatRequestCopyWith<$Res> {
  _$InterfaceSessionHeartbeatRequestCopyWithImpl(this._self, this._then);

  final InterfaceSessionHeartbeatRequest _self;
  final $Res Function(InterfaceSessionHeartbeatRequest) _then;

/// Create a copy of NetworkNodeOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? interfaceSessionId = null,Object? timestamp = freezed,}) {
  return _then(InterfaceSessionHeartbeatRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,interfaceSessionId: null == interfaceSessionId ? _self.interfaceSessionId : interfaceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,timestamp: freezed == timestamp ? _self.timestamp : timestamp // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

NetworkNodeOperationResponse _$NetworkNodeOperationResponseFromJson(
  Map<String, dynamic> json
) {
        switch (json['operation']) {
                  case 'identity_challenge':
          return IdentityChallengeResponse.fromJson(
            json
          );
                case 'identity_login':
          return IdentityLoginResponse.fromJson(
            json
          );
                case 'token_login':
          return TokenLoginResponse.fromJson(
            json
          );
                case 'whoami':
          return WhoamiResponse.fromJson(
            json
          );
                case 'membership_status':
          return MembershipStatusResponse.fromJson(
            json
          );
                case 'membership_checkout_session_create':
          return MembershipCheckoutSessionCreateResponse.fromJson(
            json
          );
                case 'membership_purchase_prepare':
          return MembershipPurchasePrepareResponse.fromJson(
            json
          );
                case 'membership_purchase_claim':
          return MembershipPurchaseClaimResponse.fromJson(
            json
          );
                case 'provision_environment':
          return ProvisionEnvironmentResponse.fromJson(
            json
          );
                case 'get_boot_environment_descriptor':
          return GetBootEnvironmentDescriptorResponse.fromJson(
            json
          );
                case 'discover_environment_configs':
          return DiscoverEnvironmentConfigsResponse.fromJson(
            json
          );
                case 'discover_service_api_dependency_routes':
          return DiscoverServiceApiDependencyRoutesResponse.fromJson(
            json
          );
                case 'discover_hosted_services':
          return DiscoverHostedServicesResponse.fromJson(
            json
          );
                case 'describe_hosted_service_runtimes':
          return DescribeHostedServiceRuntimesResponse.fromJson(
            json
          );
                case 'get_environment_status':
          return GetEnvironmentStatusResponse.fromJson(
            json
          );
                case 'close_stream':
          return CloseStreamResponse.fromJson(
            json
          );
                case 'interface_session_register':
          return InterfaceSessionRegisterResponse.fromJson(
            json
          );
                case 'interface_session_heartbeat':
          return InterfaceSessionHeartbeatResponse.fromJson(
            json
          );
        
          default:
            throw CheckedFromJsonException(
  json,
  'operation',
  'NetworkNodeOperationResponse',
  'Invalid union type "${json['operation']}"!'
);
        }
      
}

/// @nodoc
mixin _$NetworkNodeOperationResponse {

@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue? get nodeId;
/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkNodeOperationResponseCopyWith<NetworkNodeOperationResponse> get copyWith => _$NetworkNodeOperationResponseCopyWithImpl<NetworkNodeOperationResponse>(this as NetworkNodeOperationResponse, _$identity);

  /// Serializes this NetworkNodeOperationResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkNodeOperationResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId);

@override
String toString() {
  return 'NetworkNodeOperationResponse(actorId: $actorId, nodeId: $nodeId)';
}


}

/// @nodoc
abstract mixin class $NetworkNodeOperationResponseCopyWith<$Res>  {
  factory $NetworkNodeOperationResponseCopyWith(NetworkNodeOperationResponse value, $Res Function(NetworkNodeOperationResponse) _then) = _$NetworkNodeOperationResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId
});




}
/// @nodoc
class _$NetworkNodeOperationResponseCopyWithImpl<$Res>
    implements $NetworkNodeOperationResponseCopyWith<$Res> {
  _$NetworkNodeOperationResponseCopyWithImpl(this._self, this._then);

  final NetworkNodeOperationResponse _self;
  final $Res Function(NetworkNodeOperationResponse) _then;

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? nodeId = freezed,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkNodeOperationResponse].
extension NetworkNodeOperationResponsePatterns on NetworkNodeOperationResponse {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( IdentityChallengeResponse value)?  identityChallenge,TResult Function( IdentityLoginResponse value)?  identityLogin,TResult Function( TokenLoginResponse value)?  tokenLogin,TResult Function( WhoamiResponse value)?  whoami,TResult Function( MembershipStatusResponse value)?  membershipStatus,TResult Function( MembershipCheckoutSessionCreateResponse value)?  membershipCheckoutSessionCreate,TResult Function( MembershipPurchasePrepareResponse value)?  membershipPurchasePrepare,TResult Function( MembershipPurchaseClaimResponse value)?  membershipPurchaseClaim,TResult Function( ProvisionEnvironmentResponse value)?  provisionEnvironment,TResult Function( GetBootEnvironmentDescriptorResponse value)?  getBootEnvironmentDescriptor,TResult Function( DiscoverEnvironmentConfigsResponse value)?  discoverEnvironmentConfigs,TResult Function( DiscoverServiceApiDependencyRoutesResponse value)?  discoverServiceApiDependencyRoutes,TResult Function( DiscoverHostedServicesResponse value)?  discoverHostedServices,TResult Function( DescribeHostedServiceRuntimesResponse value)?  describeHostedServiceRuntimes,TResult Function( GetEnvironmentStatusResponse value)?  getEnvironmentStatus,TResult Function( CloseStreamResponse value)?  closeStream,TResult Function( InterfaceSessionRegisterResponse value)?  interfaceSessionRegister,TResult Function( InterfaceSessionHeartbeatResponse value)?  interfaceSessionHeartbeat,required TResult orElse(),}){
final _that = this;
switch (_that) {
case IdentityChallengeResponse() when identityChallenge != null:
return identityChallenge(_that);case IdentityLoginResponse() when identityLogin != null:
return identityLogin(_that);case TokenLoginResponse() when tokenLogin != null:
return tokenLogin(_that);case WhoamiResponse() when whoami != null:
return whoami(_that);case MembershipStatusResponse() when membershipStatus != null:
return membershipStatus(_that);case MembershipCheckoutSessionCreateResponse() when membershipCheckoutSessionCreate != null:
return membershipCheckoutSessionCreate(_that);case MembershipPurchasePrepareResponse() when membershipPurchasePrepare != null:
return membershipPurchasePrepare(_that);case MembershipPurchaseClaimResponse() when membershipPurchaseClaim != null:
return membershipPurchaseClaim(_that);case ProvisionEnvironmentResponse() when provisionEnvironment != null:
return provisionEnvironment(_that);case GetBootEnvironmentDescriptorResponse() when getBootEnvironmentDescriptor != null:
return getBootEnvironmentDescriptor(_that);case DiscoverEnvironmentConfigsResponse() when discoverEnvironmentConfigs != null:
return discoverEnvironmentConfigs(_that);case DiscoverServiceApiDependencyRoutesResponse() when discoverServiceApiDependencyRoutes != null:
return discoverServiceApiDependencyRoutes(_that);case DiscoverHostedServicesResponse() when discoverHostedServices != null:
return discoverHostedServices(_that);case DescribeHostedServiceRuntimesResponse() when describeHostedServiceRuntimes != null:
return describeHostedServiceRuntimes(_that);case GetEnvironmentStatusResponse() when getEnvironmentStatus != null:
return getEnvironmentStatus(_that);case CloseStreamResponse() when closeStream != null:
return closeStream(_that);case InterfaceSessionRegisterResponse() when interfaceSessionRegister != null:
return interfaceSessionRegister(_that);case InterfaceSessionHeartbeatResponse() when interfaceSessionHeartbeat != null:
return interfaceSessionHeartbeat(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( IdentityChallengeResponse value)  identityChallenge,required TResult Function( IdentityLoginResponse value)  identityLogin,required TResult Function( TokenLoginResponse value)  tokenLogin,required TResult Function( WhoamiResponse value)  whoami,required TResult Function( MembershipStatusResponse value)  membershipStatus,required TResult Function( MembershipCheckoutSessionCreateResponse value)  membershipCheckoutSessionCreate,required TResult Function( MembershipPurchasePrepareResponse value)  membershipPurchasePrepare,required TResult Function( MembershipPurchaseClaimResponse value)  membershipPurchaseClaim,required TResult Function( ProvisionEnvironmentResponse value)  provisionEnvironment,required TResult Function( GetBootEnvironmentDescriptorResponse value)  getBootEnvironmentDescriptor,required TResult Function( DiscoverEnvironmentConfigsResponse value)  discoverEnvironmentConfigs,required TResult Function( DiscoverServiceApiDependencyRoutesResponse value)  discoverServiceApiDependencyRoutes,required TResult Function( DiscoverHostedServicesResponse value)  discoverHostedServices,required TResult Function( DescribeHostedServiceRuntimesResponse value)  describeHostedServiceRuntimes,required TResult Function( GetEnvironmentStatusResponse value)  getEnvironmentStatus,required TResult Function( CloseStreamResponse value)  closeStream,required TResult Function( InterfaceSessionRegisterResponse value)  interfaceSessionRegister,required TResult Function( InterfaceSessionHeartbeatResponse value)  interfaceSessionHeartbeat,}){
final _that = this;
switch (_that) {
case IdentityChallengeResponse():
return identityChallenge(_that);case IdentityLoginResponse():
return identityLogin(_that);case TokenLoginResponse():
return tokenLogin(_that);case WhoamiResponse():
return whoami(_that);case MembershipStatusResponse():
return membershipStatus(_that);case MembershipCheckoutSessionCreateResponse():
return membershipCheckoutSessionCreate(_that);case MembershipPurchasePrepareResponse():
return membershipPurchasePrepare(_that);case MembershipPurchaseClaimResponse():
return membershipPurchaseClaim(_that);case ProvisionEnvironmentResponse():
return provisionEnvironment(_that);case GetBootEnvironmentDescriptorResponse():
return getBootEnvironmentDescriptor(_that);case DiscoverEnvironmentConfigsResponse():
return discoverEnvironmentConfigs(_that);case DiscoverServiceApiDependencyRoutesResponse():
return discoverServiceApiDependencyRoutes(_that);case DiscoverHostedServicesResponse():
return discoverHostedServices(_that);case DescribeHostedServiceRuntimesResponse():
return describeHostedServiceRuntimes(_that);case GetEnvironmentStatusResponse():
return getEnvironmentStatus(_that);case CloseStreamResponse():
return closeStream(_that);case InterfaceSessionRegisterResponse():
return interfaceSessionRegister(_that);case InterfaceSessionHeartbeatResponse():
return interfaceSessionHeartbeat(_that);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( IdentityChallengeResponse value)?  identityChallenge,TResult? Function( IdentityLoginResponse value)?  identityLogin,TResult? Function( TokenLoginResponse value)?  tokenLogin,TResult? Function( WhoamiResponse value)?  whoami,TResult? Function( MembershipStatusResponse value)?  membershipStatus,TResult? Function( MembershipCheckoutSessionCreateResponse value)?  membershipCheckoutSessionCreate,TResult? Function( MembershipPurchasePrepareResponse value)?  membershipPurchasePrepare,TResult? Function( MembershipPurchaseClaimResponse value)?  membershipPurchaseClaim,TResult? Function( ProvisionEnvironmentResponse value)?  provisionEnvironment,TResult? Function( GetBootEnvironmentDescriptorResponse value)?  getBootEnvironmentDescriptor,TResult? Function( DiscoverEnvironmentConfigsResponse value)?  discoverEnvironmentConfigs,TResult? Function( DiscoverServiceApiDependencyRoutesResponse value)?  discoverServiceApiDependencyRoutes,TResult? Function( DiscoverHostedServicesResponse value)?  discoverHostedServices,TResult? Function( DescribeHostedServiceRuntimesResponse value)?  describeHostedServiceRuntimes,TResult? Function( GetEnvironmentStatusResponse value)?  getEnvironmentStatus,TResult? Function( CloseStreamResponse value)?  closeStream,TResult? Function( InterfaceSessionRegisterResponse value)?  interfaceSessionRegister,TResult? Function( InterfaceSessionHeartbeatResponse value)?  interfaceSessionHeartbeat,}){
final _that = this;
switch (_that) {
case IdentityChallengeResponse() when identityChallenge != null:
return identityChallenge(_that);case IdentityLoginResponse() when identityLogin != null:
return identityLogin(_that);case TokenLoginResponse() when tokenLogin != null:
return tokenLogin(_that);case WhoamiResponse() when whoami != null:
return whoami(_that);case MembershipStatusResponse() when membershipStatus != null:
return membershipStatus(_that);case MembershipCheckoutSessionCreateResponse() when membershipCheckoutSessionCreate != null:
return membershipCheckoutSessionCreate(_that);case MembershipPurchasePrepareResponse() when membershipPurchasePrepare != null:
return membershipPurchasePrepare(_that);case MembershipPurchaseClaimResponse() when membershipPurchaseClaim != null:
return membershipPurchaseClaim(_that);case ProvisionEnvironmentResponse() when provisionEnvironment != null:
return provisionEnvironment(_that);case GetBootEnvironmentDescriptorResponse() when getBootEnvironmentDescriptor != null:
return getBootEnvironmentDescriptor(_that);case DiscoverEnvironmentConfigsResponse() when discoverEnvironmentConfigs != null:
return discoverEnvironmentConfigs(_that);case DiscoverServiceApiDependencyRoutesResponse() when discoverServiceApiDependencyRoutes != null:
return discoverServiceApiDependencyRoutes(_that);case DiscoverHostedServicesResponse() when discoverHostedServices != null:
return discoverHostedServices(_that);case DescribeHostedServiceRuntimesResponse() when describeHostedServiceRuntimes != null:
return describeHostedServiceRuntimes(_that);case GetEnvironmentStatusResponse() when getEnvironmentStatus != null:
return getEnvironmentStatus(_that);case CloseStreamResponse() when closeStream != null:
return closeStream(_that);case InterfaceSessionRegisterResponse() when interfaceSessionRegister != null:
return interfaceSessionRegister(_that);case InterfaceSessionHeartbeatResponse() when interfaceSessionHeartbeat != null:
return interfaceSessionHeartbeat(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  String publicKey,  String challenge,  String? expiresAt)?  identityChallenge,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  String publicKey,  List<String> roles)?  identityLogin,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  String? publicKey,  List<String> roles, @UuidValueConverter()  UuidValue? tokenId,  String? tokenType,  List<String> scopes, @UuidValueConverter()  UuidValue? contextEnvironmentId, @UuidValueConverter()  UuidValue? contextProcessId, @UuidValueConverter()  UuidValue? contextThreadId,  String? expiresAt)?  tokenLogin,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  bool authenticated,  String? publicKey,  List<String> roles, @UuidValueConverter()  UuidValue? interfaceSessionId, @UuidValueConverter()  UuidValue? interfaceId,  String? lastSeenAt)?  whoami,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  bool isActive,  bool isBypassed,  String? planLabel,  String? currentPeriodEnd)?  membershipStatus,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  String? checkoutUrl,  String? checkoutSessionId)?  membershipCheckoutSessionCreate,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  String provider,  String? planLabel,  String? checkoutUrl,  String? appleProductId,  String? googleProductId)?  membershipPurchasePrepare,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  bool isActive,  String? planLabel,  String? currentPeriodEnd)?  membershipPurchaseClaim,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error, @UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue? environmentConfigId,  String? environmentConfigTitle,  String? environmentTitle,  String? environmentEndpoint,  String? ocgHash, @UuidValueConverter()  UuidValue? processId, @UuidValueConverter()  UuidValue? threadId, @UuidValueConverter()  UuidValue? branchId,  List<String> opgHashes,  NodeEnvironmentProvisioningReceipt? provisioningReceipt)?  provisionEnvironment,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  BootEnvironmentDescriptor? descriptor)?  getBootEnvironmentDescriptor,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  List<EnvironmentConfigDescriptor> configs)?  discoverEnvironmentConfigs,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  List<ServiceApiDependencyRouteDescriptor> routes)?  discoverServiceApiDependencyRoutes,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  List<HostedServiceAdvertisement> hostedServices)?  discoverHostedServices,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  List<HostedServiceRuntimeStatus> hostedServiceRuntimes)?  describeHostedServiceRuntimes,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error, @UuidValueConverter()  UuidValue environmentId, @UuidValueConverter()  UuidValue? environmentConfigId,  String? environmentConfigTitle,  String? environmentTitle,  String? environmentEndpoint,  String? ocgHash, @UuidValueConverter()  UuidValue? processId, @UuidValueConverter()  UuidValue? threadId, @UuidValueConverter()  UuidValue? branchId,  List<String> opgHashes,  NodeEnvironmentProvisioningReceipt? provisioningReceipt)?  getEnvironmentStatus,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error, @UuidValueConverter()  UuidValue networkOperationId)?  closeStream,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error, @UuidValueConverter()  UuidValue interfaceId, @UuidValueConverter()  UuidValue interfaceSessionId, @UuidValueConverter()  UuidValue? interfaceIdentityNetworkNodeId, @UuidValueConverter()  UuidValue? interfaceSessionNetworkBindingId,  String? lastSeenAt,  int protocolVersion)?  interfaceSessionRegister,TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error, @UuidValueConverter()  UuidValue interfaceSessionId,  String? lastSeenAt)?  interfaceSessionHeartbeat,required TResult orElse(),}) {final _that = this;
switch (_that) {
case IdentityChallengeResponse() when identityChallenge != null:
return identityChallenge(_that.actorId,_that.nodeId,_that.status,_that.error,_that.publicKey,_that.challenge,_that.expiresAt);case IdentityLoginResponse() when identityLogin != null:
return identityLogin(_that.actorId,_that.nodeId,_that.status,_that.error,_that.publicKey,_that.roles);case TokenLoginResponse() when tokenLogin != null:
return tokenLogin(_that.actorId,_that.nodeId,_that.status,_that.error,_that.publicKey,_that.roles,_that.tokenId,_that.tokenType,_that.scopes,_that.contextEnvironmentId,_that.contextProcessId,_that.contextThreadId,_that.expiresAt);case WhoamiResponse() when whoami != null:
return whoami(_that.actorId,_that.nodeId,_that.status,_that.error,_that.authenticated,_that.publicKey,_that.roles,_that.interfaceSessionId,_that.interfaceId,_that.lastSeenAt);case MembershipStatusResponse() when membershipStatus != null:
return membershipStatus(_that.actorId,_that.nodeId,_that.status,_that.error,_that.isActive,_that.isBypassed,_that.planLabel,_that.currentPeriodEnd);case MembershipCheckoutSessionCreateResponse() when membershipCheckoutSessionCreate != null:
return membershipCheckoutSessionCreate(_that.actorId,_that.nodeId,_that.status,_that.error,_that.checkoutUrl,_that.checkoutSessionId);case MembershipPurchasePrepareResponse() when membershipPurchasePrepare != null:
return membershipPurchasePrepare(_that.actorId,_that.nodeId,_that.status,_that.error,_that.provider,_that.planLabel,_that.checkoutUrl,_that.appleProductId,_that.googleProductId);case MembershipPurchaseClaimResponse() when membershipPurchaseClaim != null:
return membershipPurchaseClaim(_that.actorId,_that.nodeId,_that.status,_that.error,_that.isActive,_that.planLabel,_that.currentPeriodEnd);case ProvisionEnvironmentResponse() when provisionEnvironment != null:
return provisionEnvironment(_that.actorId,_that.nodeId,_that.status,_that.error,_that.environmentId,_that.environmentConfigId,_that.environmentConfigTitle,_that.environmentTitle,_that.environmentEndpoint,_that.ocgHash,_that.processId,_that.threadId,_that.branchId,_that.opgHashes,_that.provisioningReceipt);case GetBootEnvironmentDescriptorResponse() when getBootEnvironmentDescriptor != null:
return getBootEnvironmentDescriptor(_that.actorId,_that.nodeId,_that.status,_that.error,_that.descriptor);case DiscoverEnvironmentConfigsResponse() when discoverEnvironmentConfigs != null:
return discoverEnvironmentConfigs(_that.actorId,_that.nodeId,_that.configs);case DiscoverServiceApiDependencyRoutesResponse() when discoverServiceApiDependencyRoutes != null:
return discoverServiceApiDependencyRoutes(_that.actorId,_that.nodeId,_that.routes);case DiscoverHostedServicesResponse() when discoverHostedServices != null:
return discoverHostedServices(_that.actorId,_that.nodeId,_that.hostedServices);case DescribeHostedServiceRuntimesResponse() when describeHostedServiceRuntimes != null:
return describeHostedServiceRuntimes(_that.actorId,_that.nodeId,_that.hostedServiceRuntimes);case GetEnvironmentStatusResponse() when getEnvironmentStatus != null:
return getEnvironmentStatus(_that.actorId,_that.nodeId,_that.status,_that.error,_that.environmentId,_that.environmentConfigId,_that.environmentConfigTitle,_that.environmentTitle,_that.environmentEndpoint,_that.ocgHash,_that.processId,_that.threadId,_that.branchId,_that.opgHashes,_that.provisioningReceipt);case CloseStreamResponse() when closeStream != null:
return closeStream(_that.actorId,_that.nodeId,_that.status,_that.error,_that.networkOperationId);case InterfaceSessionRegisterResponse() when interfaceSessionRegister != null:
return interfaceSessionRegister(_that.actorId,_that.nodeId,_that.status,_that.error,_that.interfaceId,_that.interfaceSessionId,_that.interfaceIdentityNetworkNodeId,_that.interfaceSessionNetworkBindingId,_that.lastSeenAt,_that.protocolVersion);case InterfaceSessionHeartbeatResponse() when interfaceSessionHeartbeat != null:
return interfaceSessionHeartbeat(_that.actorId,_that.nodeId,_that.status,_that.error,_that.interfaceSessionId,_that.lastSeenAt);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  String publicKey,  String challenge,  String? expiresAt)  identityChallenge,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  String publicKey,  List<String> roles)  identityLogin,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  String? publicKey,  List<String> roles, @UuidValueConverter()  UuidValue? tokenId,  String? tokenType,  List<String> scopes, @UuidValueConverter()  UuidValue? contextEnvironmentId, @UuidValueConverter()  UuidValue? contextProcessId, @UuidValueConverter()  UuidValue? contextThreadId,  String? expiresAt)  tokenLogin,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  bool authenticated,  String? publicKey,  List<String> roles, @UuidValueConverter()  UuidValue? interfaceSessionId, @UuidValueConverter()  UuidValue? interfaceId,  String? lastSeenAt)  whoami,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  bool isActive,  bool isBypassed,  String? planLabel,  String? currentPeriodEnd)  membershipStatus,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  String? checkoutUrl,  String? checkoutSessionId)  membershipCheckoutSessionCreate,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  String provider,  String? planLabel,  String? checkoutUrl,  String? appleProductId,  String? googleProductId)  membershipPurchasePrepare,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  bool isActive,  String? planLabel,  String? currentPeriodEnd)  membershipPurchaseClaim,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error, @UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue? environmentConfigId,  String? environmentConfigTitle,  String? environmentTitle,  String? environmentEndpoint,  String? ocgHash, @UuidValueConverter()  UuidValue? processId, @UuidValueConverter()  UuidValue? threadId, @UuidValueConverter()  UuidValue? branchId,  List<String> opgHashes,  NodeEnvironmentProvisioningReceipt? provisioningReceipt)  provisionEnvironment,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  BootEnvironmentDescriptor? descriptor)  getBootEnvironmentDescriptor,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  List<EnvironmentConfigDescriptor> configs)  discoverEnvironmentConfigs,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  List<ServiceApiDependencyRouteDescriptor> routes)  discoverServiceApiDependencyRoutes,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  List<HostedServiceAdvertisement> hostedServices)  discoverHostedServices,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  List<HostedServiceRuntimeStatus> hostedServiceRuntimes)  describeHostedServiceRuntimes,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error, @UuidValueConverter()  UuidValue environmentId, @UuidValueConverter()  UuidValue? environmentConfigId,  String? environmentConfigTitle,  String? environmentTitle,  String? environmentEndpoint,  String? ocgHash, @UuidValueConverter()  UuidValue? processId, @UuidValueConverter()  UuidValue? threadId, @UuidValueConverter()  UuidValue? branchId,  List<String> opgHashes,  NodeEnvironmentProvisioningReceipt? provisioningReceipt)  getEnvironmentStatus,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error, @UuidValueConverter()  UuidValue networkOperationId)  closeStream,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error, @UuidValueConverter()  UuidValue interfaceId, @UuidValueConverter()  UuidValue interfaceSessionId, @UuidValueConverter()  UuidValue? interfaceIdentityNetworkNodeId, @UuidValueConverter()  UuidValue? interfaceSessionNetworkBindingId,  String? lastSeenAt,  int protocolVersion)  interfaceSessionRegister,required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error, @UuidValueConverter()  UuidValue interfaceSessionId,  String? lastSeenAt)  interfaceSessionHeartbeat,}) {final _that = this;
switch (_that) {
case IdentityChallengeResponse():
return identityChallenge(_that.actorId,_that.nodeId,_that.status,_that.error,_that.publicKey,_that.challenge,_that.expiresAt);case IdentityLoginResponse():
return identityLogin(_that.actorId,_that.nodeId,_that.status,_that.error,_that.publicKey,_that.roles);case TokenLoginResponse():
return tokenLogin(_that.actorId,_that.nodeId,_that.status,_that.error,_that.publicKey,_that.roles,_that.tokenId,_that.tokenType,_that.scopes,_that.contextEnvironmentId,_that.contextProcessId,_that.contextThreadId,_that.expiresAt);case WhoamiResponse():
return whoami(_that.actorId,_that.nodeId,_that.status,_that.error,_that.authenticated,_that.publicKey,_that.roles,_that.interfaceSessionId,_that.interfaceId,_that.lastSeenAt);case MembershipStatusResponse():
return membershipStatus(_that.actorId,_that.nodeId,_that.status,_that.error,_that.isActive,_that.isBypassed,_that.planLabel,_that.currentPeriodEnd);case MembershipCheckoutSessionCreateResponse():
return membershipCheckoutSessionCreate(_that.actorId,_that.nodeId,_that.status,_that.error,_that.checkoutUrl,_that.checkoutSessionId);case MembershipPurchasePrepareResponse():
return membershipPurchasePrepare(_that.actorId,_that.nodeId,_that.status,_that.error,_that.provider,_that.planLabel,_that.checkoutUrl,_that.appleProductId,_that.googleProductId);case MembershipPurchaseClaimResponse():
return membershipPurchaseClaim(_that.actorId,_that.nodeId,_that.status,_that.error,_that.isActive,_that.planLabel,_that.currentPeriodEnd);case ProvisionEnvironmentResponse():
return provisionEnvironment(_that.actorId,_that.nodeId,_that.status,_that.error,_that.environmentId,_that.environmentConfigId,_that.environmentConfigTitle,_that.environmentTitle,_that.environmentEndpoint,_that.ocgHash,_that.processId,_that.threadId,_that.branchId,_that.opgHashes,_that.provisioningReceipt);case GetBootEnvironmentDescriptorResponse():
return getBootEnvironmentDescriptor(_that.actorId,_that.nodeId,_that.status,_that.error,_that.descriptor);case DiscoverEnvironmentConfigsResponse():
return discoverEnvironmentConfigs(_that.actorId,_that.nodeId,_that.configs);case DiscoverServiceApiDependencyRoutesResponse():
return discoverServiceApiDependencyRoutes(_that.actorId,_that.nodeId,_that.routes);case DiscoverHostedServicesResponse():
return discoverHostedServices(_that.actorId,_that.nodeId,_that.hostedServices);case DescribeHostedServiceRuntimesResponse():
return describeHostedServiceRuntimes(_that.actorId,_that.nodeId,_that.hostedServiceRuntimes);case GetEnvironmentStatusResponse():
return getEnvironmentStatus(_that.actorId,_that.nodeId,_that.status,_that.error,_that.environmentId,_that.environmentConfigId,_that.environmentConfigTitle,_that.environmentTitle,_that.environmentEndpoint,_that.ocgHash,_that.processId,_that.threadId,_that.branchId,_that.opgHashes,_that.provisioningReceipt);case CloseStreamResponse():
return closeStream(_that.actorId,_that.nodeId,_that.status,_that.error,_that.networkOperationId);case InterfaceSessionRegisterResponse():
return interfaceSessionRegister(_that.actorId,_that.nodeId,_that.status,_that.error,_that.interfaceId,_that.interfaceSessionId,_that.interfaceIdentityNetworkNodeId,_that.interfaceSessionNetworkBindingId,_that.lastSeenAt,_that.protocolVersion);case InterfaceSessionHeartbeatResponse():
return interfaceSessionHeartbeat(_that.actorId,_that.nodeId,_that.status,_that.error,_that.interfaceSessionId,_that.lastSeenAt);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  String publicKey,  String challenge,  String? expiresAt)?  identityChallenge,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  String publicKey,  List<String> roles)?  identityLogin,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  String? publicKey,  List<String> roles, @UuidValueConverter()  UuidValue? tokenId,  String? tokenType,  List<String> scopes, @UuidValueConverter()  UuidValue? contextEnvironmentId, @UuidValueConverter()  UuidValue? contextProcessId, @UuidValueConverter()  UuidValue? contextThreadId,  String? expiresAt)?  tokenLogin,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  bool authenticated,  String? publicKey,  List<String> roles, @UuidValueConverter()  UuidValue? interfaceSessionId, @UuidValueConverter()  UuidValue? interfaceId,  String? lastSeenAt)?  whoami,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  bool isActive,  bool isBypassed,  String? planLabel,  String? currentPeriodEnd)?  membershipStatus,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  String? checkoutUrl,  String? checkoutSessionId)?  membershipCheckoutSessionCreate,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  String provider,  String? planLabel,  String? checkoutUrl,  String? appleProductId,  String? googleProductId)?  membershipPurchasePrepare,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  bool isActive,  String? planLabel,  String? currentPeriodEnd)?  membershipPurchaseClaim,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error, @UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue? environmentConfigId,  String? environmentConfigTitle,  String? environmentTitle,  String? environmentEndpoint,  String? ocgHash, @UuidValueConverter()  UuidValue? processId, @UuidValueConverter()  UuidValue? threadId, @UuidValueConverter()  UuidValue? branchId,  List<String> opgHashes,  NodeEnvironmentProvisioningReceipt? provisioningReceipt)?  provisionEnvironment,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error,  BootEnvironmentDescriptor? descriptor)?  getBootEnvironmentDescriptor,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  List<EnvironmentConfigDescriptor> configs)?  discoverEnvironmentConfigs,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  List<ServiceApiDependencyRouteDescriptor> routes)?  discoverServiceApiDependencyRoutes,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  List<HostedServiceAdvertisement> hostedServices)?  discoverHostedServices,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  List<HostedServiceRuntimeStatus> hostedServiceRuntimes)?  describeHostedServiceRuntimes,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error, @UuidValueConverter()  UuidValue environmentId, @UuidValueConverter()  UuidValue? environmentConfigId,  String? environmentConfigTitle,  String? environmentTitle,  String? environmentEndpoint,  String? ocgHash, @UuidValueConverter()  UuidValue? processId, @UuidValueConverter()  UuidValue? threadId, @UuidValueConverter()  UuidValue? branchId,  List<String> opgHashes,  NodeEnvironmentProvisioningReceipt? provisioningReceipt)?  getEnvironmentStatus,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error, @UuidValueConverter()  UuidValue networkOperationId)?  closeStream,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error, @UuidValueConverter()  UuidValue interfaceId, @UuidValueConverter()  UuidValue interfaceSessionId, @UuidValueConverter()  UuidValue? interfaceIdentityNetworkNodeId, @UuidValueConverter()  UuidValue? interfaceSessionNetworkBindingId,  String? lastSeenAt,  int protocolVersion)?  interfaceSessionRegister,TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId,  String status,  String? error, @UuidValueConverter()  UuidValue interfaceSessionId,  String? lastSeenAt)?  interfaceSessionHeartbeat,}) {final _that = this;
switch (_that) {
case IdentityChallengeResponse() when identityChallenge != null:
return identityChallenge(_that.actorId,_that.nodeId,_that.status,_that.error,_that.publicKey,_that.challenge,_that.expiresAt);case IdentityLoginResponse() when identityLogin != null:
return identityLogin(_that.actorId,_that.nodeId,_that.status,_that.error,_that.publicKey,_that.roles);case TokenLoginResponse() when tokenLogin != null:
return tokenLogin(_that.actorId,_that.nodeId,_that.status,_that.error,_that.publicKey,_that.roles,_that.tokenId,_that.tokenType,_that.scopes,_that.contextEnvironmentId,_that.contextProcessId,_that.contextThreadId,_that.expiresAt);case WhoamiResponse() when whoami != null:
return whoami(_that.actorId,_that.nodeId,_that.status,_that.error,_that.authenticated,_that.publicKey,_that.roles,_that.interfaceSessionId,_that.interfaceId,_that.lastSeenAt);case MembershipStatusResponse() when membershipStatus != null:
return membershipStatus(_that.actorId,_that.nodeId,_that.status,_that.error,_that.isActive,_that.isBypassed,_that.planLabel,_that.currentPeriodEnd);case MembershipCheckoutSessionCreateResponse() when membershipCheckoutSessionCreate != null:
return membershipCheckoutSessionCreate(_that.actorId,_that.nodeId,_that.status,_that.error,_that.checkoutUrl,_that.checkoutSessionId);case MembershipPurchasePrepareResponse() when membershipPurchasePrepare != null:
return membershipPurchasePrepare(_that.actorId,_that.nodeId,_that.status,_that.error,_that.provider,_that.planLabel,_that.checkoutUrl,_that.appleProductId,_that.googleProductId);case MembershipPurchaseClaimResponse() when membershipPurchaseClaim != null:
return membershipPurchaseClaim(_that.actorId,_that.nodeId,_that.status,_that.error,_that.isActive,_that.planLabel,_that.currentPeriodEnd);case ProvisionEnvironmentResponse() when provisionEnvironment != null:
return provisionEnvironment(_that.actorId,_that.nodeId,_that.status,_that.error,_that.environmentId,_that.environmentConfigId,_that.environmentConfigTitle,_that.environmentTitle,_that.environmentEndpoint,_that.ocgHash,_that.processId,_that.threadId,_that.branchId,_that.opgHashes,_that.provisioningReceipt);case GetBootEnvironmentDescriptorResponse() when getBootEnvironmentDescriptor != null:
return getBootEnvironmentDescriptor(_that.actorId,_that.nodeId,_that.status,_that.error,_that.descriptor);case DiscoverEnvironmentConfigsResponse() when discoverEnvironmentConfigs != null:
return discoverEnvironmentConfigs(_that.actorId,_that.nodeId,_that.configs);case DiscoverServiceApiDependencyRoutesResponse() when discoverServiceApiDependencyRoutes != null:
return discoverServiceApiDependencyRoutes(_that.actorId,_that.nodeId,_that.routes);case DiscoverHostedServicesResponse() when discoverHostedServices != null:
return discoverHostedServices(_that.actorId,_that.nodeId,_that.hostedServices);case DescribeHostedServiceRuntimesResponse() when describeHostedServiceRuntimes != null:
return describeHostedServiceRuntimes(_that.actorId,_that.nodeId,_that.hostedServiceRuntimes);case GetEnvironmentStatusResponse() when getEnvironmentStatus != null:
return getEnvironmentStatus(_that.actorId,_that.nodeId,_that.status,_that.error,_that.environmentId,_that.environmentConfigId,_that.environmentConfigTitle,_that.environmentTitle,_that.environmentEndpoint,_that.ocgHash,_that.processId,_that.threadId,_that.branchId,_that.opgHashes,_that.provisioningReceipt);case CloseStreamResponse() when closeStream != null:
return closeStream(_that.actorId,_that.nodeId,_that.status,_that.error,_that.networkOperationId);case InterfaceSessionRegisterResponse() when interfaceSessionRegister != null:
return interfaceSessionRegister(_that.actorId,_that.nodeId,_that.status,_that.error,_that.interfaceId,_that.interfaceSessionId,_that.interfaceIdentityNetworkNodeId,_that.interfaceSessionNetworkBindingId,_that.lastSeenAt,_that.protocolVersion);case InterfaceSessionHeartbeatResponse() when interfaceSessionHeartbeat != null:
return interfaceSessionHeartbeat(_that.actorId,_that.nodeId,_that.status,_that.error,_that.interfaceSessionId,_that.lastSeenAt);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class IdentityChallengeResponse implements NetworkNodeOperationResponse {
   IdentityChallengeResponse({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, required this.status, this.error, required this.publicKey, required this.challenge, this.expiresAt, final  String? $type}): $type = $type ?? 'identity_challenge';
  factory IdentityChallengeResponse.fromJson(Map<String, dynamic> json) => _$IdentityChallengeResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String status;
 final  String? error;
 final  String publicKey;
 final  String challenge;
 final  String? expiresAt;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$IdentityChallengeResponseCopyWith<IdentityChallengeResponse> get copyWith => _$IdentityChallengeResponseCopyWithImpl<IdentityChallengeResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$IdentityChallengeResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is IdentityChallengeResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.publicKey, publicKey) || other.publicKey == publicKey)&&(identical(other.challenge, challenge) || other.challenge == challenge)&&(identical(other.expiresAt, expiresAt) || other.expiresAt == expiresAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,status,error,publicKey,challenge,expiresAt);

@override
String toString() {
  return 'NetworkNodeOperationResponse.identityChallenge(actorId: $actorId, nodeId: $nodeId, status: $status, error: $error, publicKey: $publicKey, challenge: $challenge, expiresAt: $expiresAt)';
}


}

/// @nodoc
abstract mixin class $IdentityChallengeResponseCopyWith<$Res> implements $NetworkNodeOperationResponseCopyWith<$Res> {
  factory $IdentityChallengeResponseCopyWith(IdentityChallengeResponse value, $Res Function(IdentityChallengeResponse) _then) = _$IdentityChallengeResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String status, String? error, String publicKey, String challenge, String? expiresAt
});




}
/// @nodoc
class _$IdentityChallengeResponseCopyWithImpl<$Res>
    implements $IdentityChallengeResponseCopyWith<$Res> {
  _$IdentityChallengeResponseCopyWithImpl(this._self, this._then);

  final IdentityChallengeResponse _self;
  final $Res Function(IdentityChallengeResponse) _then;

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? status = null,Object? error = freezed,Object? publicKey = null,Object? challenge = null,Object? expiresAt = freezed,}) {
  return _then(IdentityChallengeResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,publicKey: null == publicKey ? _self.publicKey : publicKey // ignore: cast_nullable_to_non_nullable
as String,challenge: null == challenge ? _self.challenge : challenge // ignore: cast_nullable_to_non_nullable
as String,expiresAt: freezed == expiresAt ? _self.expiresAt : expiresAt // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class IdentityLoginResponse implements NetworkNodeOperationResponse {
   IdentityLoginResponse({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, required this.status, this.error, required this.publicKey, final  List<String> roles = const [], final  String? $type}): _roles = roles,$type = $type ?? 'identity_login';
  factory IdentityLoginResponse.fromJson(Map<String, dynamic> json) => _$IdentityLoginResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String status;
 final  String? error;
 final  String publicKey;
 final  List<String> _roles;
@JsonKey() List<String> get roles {
  if (_roles is EqualUnmodifiableListView) return _roles;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_roles);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$IdentityLoginResponseCopyWith<IdentityLoginResponse> get copyWith => _$IdentityLoginResponseCopyWithImpl<IdentityLoginResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$IdentityLoginResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is IdentityLoginResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.publicKey, publicKey) || other.publicKey == publicKey)&&const DeepCollectionEquality().equals(other._roles, _roles));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,status,error,publicKey,const DeepCollectionEquality().hash(_roles));

@override
String toString() {
  return 'NetworkNodeOperationResponse.identityLogin(actorId: $actorId, nodeId: $nodeId, status: $status, error: $error, publicKey: $publicKey, roles: $roles)';
}


}

/// @nodoc
abstract mixin class $IdentityLoginResponseCopyWith<$Res> implements $NetworkNodeOperationResponseCopyWith<$Res> {
  factory $IdentityLoginResponseCopyWith(IdentityLoginResponse value, $Res Function(IdentityLoginResponse) _then) = _$IdentityLoginResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String status, String? error, String publicKey, List<String> roles
});




}
/// @nodoc
class _$IdentityLoginResponseCopyWithImpl<$Res>
    implements $IdentityLoginResponseCopyWith<$Res> {
  _$IdentityLoginResponseCopyWithImpl(this._self, this._then);

  final IdentityLoginResponse _self;
  final $Res Function(IdentityLoginResponse) _then;

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? status = null,Object? error = freezed,Object? publicKey = null,Object? roles = null,}) {
  return _then(IdentityLoginResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,publicKey: null == publicKey ? _self.publicKey : publicKey // ignore: cast_nullable_to_non_nullable
as String,roles: null == roles ? _self._roles : roles // ignore: cast_nullable_to_non_nullable
as List<String>,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class TokenLoginResponse implements NetworkNodeOperationResponse {
   TokenLoginResponse({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, required this.status, this.error, this.publicKey, final  List<String> roles = const [], @UuidValueConverter() this.tokenId, this.tokenType, final  List<String> scopes = const [], @UuidValueConverter() this.contextEnvironmentId, @UuidValueConverter() this.contextProcessId, @UuidValueConverter() this.contextThreadId, this.expiresAt, final  String? $type}): _roles = roles,_scopes = scopes,$type = $type ?? 'token_login';
  factory TokenLoginResponse.fromJson(Map<String, dynamic> json) => _$TokenLoginResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String status;
 final  String? error;
 final  String? publicKey;
 final  List<String> _roles;
@JsonKey() List<String> get roles {
  if (_roles is EqualUnmodifiableListView) return _roles;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_roles);
}

@UuidValueConverter() final  UuidValue? tokenId;
 final  String? tokenType;
 final  List<String> _scopes;
@JsonKey() List<String> get scopes {
  if (_scopes is EqualUnmodifiableListView) return _scopes;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_scopes);
}

@UuidValueConverter() final  UuidValue? contextEnvironmentId;
@UuidValueConverter() final  UuidValue? contextProcessId;
@UuidValueConverter() final  UuidValue? contextThreadId;
 final  String? expiresAt;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$TokenLoginResponseCopyWith<TokenLoginResponse> get copyWith => _$TokenLoginResponseCopyWithImpl<TokenLoginResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$TokenLoginResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is TokenLoginResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.publicKey, publicKey) || other.publicKey == publicKey)&&const DeepCollectionEquality().equals(other._roles, _roles)&&(identical(other.tokenId, tokenId) || other.tokenId == tokenId)&&(identical(other.tokenType, tokenType) || other.tokenType == tokenType)&&const DeepCollectionEquality().equals(other._scopes, _scopes)&&(identical(other.contextEnvironmentId, contextEnvironmentId) || other.contextEnvironmentId == contextEnvironmentId)&&(identical(other.contextProcessId, contextProcessId) || other.contextProcessId == contextProcessId)&&(identical(other.contextThreadId, contextThreadId) || other.contextThreadId == contextThreadId)&&(identical(other.expiresAt, expiresAt) || other.expiresAt == expiresAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,status,error,publicKey,const DeepCollectionEquality().hash(_roles),tokenId,tokenType,const DeepCollectionEquality().hash(_scopes),contextEnvironmentId,contextProcessId,contextThreadId,expiresAt);

@override
String toString() {
  return 'NetworkNodeOperationResponse.tokenLogin(actorId: $actorId, nodeId: $nodeId, status: $status, error: $error, publicKey: $publicKey, roles: $roles, tokenId: $tokenId, tokenType: $tokenType, scopes: $scopes, contextEnvironmentId: $contextEnvironmentId, contextProcessId: $contextProcessId, contextThreadId: $contextThreadId, expiresAt: $expiresAt)';
}


}

/// @nodoc
abstract mixin class $TokenLoginResponseCopyWith<$Res> implements $NetworkNodeOperationResponseCopyWith<$Res> {
  factory $TokenLoginResponseCopyWith(TokenLoginResponse value, $Res Function(TokenLoginResponse) _then) = _$TokenLoginResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String status, String? error, String? publicKey, List<String> roles,@UuidValueConverter() UuidValue? tokenId, String? tokenType, List<String> scopes,@UuidValueConverter() UuidValue? contextEnvironmentId,@UuidValueConverter() UuidValue? contextProcessId,@UuidValueConverter() UuidValue? contextThreadId, String? expiresAt
});




}
/// @nodoc
class _$TokenLoginResponseCopyWithImpl<$Res>
    implements $TokenLoginResponseCopyWith<$Res> {
  _$TokenLoginResponseCopyWithImpl(this._self, this._then);

  final TokenLoginResponse _self;
  final $Res Function(TokenLoginResponse) _then;

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? status = null,Object? error = freezed,Object? publicKey = freezed,Object? roles = null,Object? tokenId = freezed,Object? tokenType = freezed,Object? scopes = null,Object? contextEnvironmentId = freezed,Object? contextProcessId = freezed,Object? contextThreadId = freezed,Object? expiresAt = freezed,}) {
  return _then(TokenLoginResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,publicKey: freezed == publicKey ? _self.publicKey : publicKey // ignore: cast_nullable_to_non_nullable
as String?,roles: null == roles ? _self._roles : roles // ignore: cast_nullable_to_non_nullable
as List<String>,tokenId: freezed == tokenId ? _self.tokenId : tokenId // ignore: cast_nullable_to_non_nullable
as UuidValue?,tokenType: freezed == tokenType ? _self.tokenType : tokenType // ignore: cast_nullable_to_non_nullable
as String?,scopes: null == scopes ? _self._scopes : scopes // ignore: cast_nullable_to_non_nullable
as List<String>,contextEnvironmentId: freezed == contextEnvironmentId ? _self.contextEnvironmentId : contextEnvironmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,contextProcessId: freezed == contextProcessId ? _self.contextProcessId : contextProcessId // ignore: cast_nullable_to_non_nullable
as UuidValue?,contextThreadId: freezed == contextThreadId ? _self.contextThreadId : contextThreadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,expiresAt: freezed == expiresAt ? _self.expiresAt : expiresAt // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class WhoamiResponse implements NetworkNodeOperationResponse {
   WhoamiResponse({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, required this.status, this.error, required this.authenticated, this.publicKey, final  List<String> roles = const [], @UuidValueConverter() this.interfaceSessionId, @UuidValueConverter() this.interfaceId, this.lastSeenAt, final  String? $type}): _roles = roles,$type = $type ?? 'whoami';
  factory WhoamiResponse.fromJson(Map<String, dynamic> json) => _$WhoamiResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String status;
 final  String? error;
 final  bool authenticated;
 final  String? publicKey;
 final  List<String> _roles;
@JsonKey() List<String> get roles {
  if (_roles is EqualUnmodifiableListView) return _roles;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_roles);
}

@UuidValueConverter() final  UuidValue? interfaceSessionId;
@UuidValueConverter() final  UuidValue? interfaceId;
 final  String? lastSeenAt;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$WhoamiResponseCopyWith<WhoamiResponse> get copyWith => _$WhoamiResponseCopyWithImpl<WhoamiResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$WhoamiResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is WhoamiResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.authenticated, authenticated) || other.authenticated == authenticated)&&(identical(other.publicKey, publicKey) || other.publicKey == publicKey)&&const DeepCollectionEquality().equals(other._roles, _roles)&&(identical(other.interfaceSessionId, interfaceSessionId) || other.interfaceSessionId == interfaceSessionId)&&(identical(other.interfaceId, interfaceId) || other.interfaceId == interfaceId)&&(identical(other.lastSeenAt, lastSeenAt) || other.lastSeenAt == lastSeenAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,status,error,authenticated,publicKey,const DeepCollectionEquality().hash(_roles),interfaceSessionId,interfaceId,lastSeenAt);

@override
String toString() {
  return 'NetworkNodeOperationResponse.whoami(actorId: $actorId, nodeId: $nodeId, status: $status, error: $error, authenticated: $authenticated, publicKey: $publicKey, roles: $roles, interfaceSessionId: $interfaceSessionId, interfaceId: $interfaceId, lastSeenAt: $lastSeenAt)';
}


}

/// @nodoc
abstract mixin class $WhoamiResponseCopyWith<$Res> implements $NetworkNodeOperationResponseCopyWith<$Res> {
  factory $WhoamiResponseCopyWith(WhoamiResponse value, $Res Function(WhoamiResponse) _then) = _$WhoamiResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String status, String? error, bool authenticated, String? publicKey, List<String> roles,@UuidValueConverter() UuidValue? interfaceSessionId,@UuidValueConverter() UuidValue? interfaceId, String? lastSeenAt
});




}
/// @nodoc
class _$WhoamiResponseCopyWithImpl<$Res>
    implements $WhoamiResponseCopyWith<$Res> {
  _$WhoamiResponseCopyWithImpl(this._self, this._then);

  final WhoamiResponse _self;
  final $Res Function(WhoamiResponse) _then;

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? status = null,Object? error = freezed,Object? authenticated = null,Object? publicKey = freezed,Object? roles = null,Object? interfaceSessionId = freezed,Object? interfaceId = freezed,Object? lastSeenAt = freezed,}) {
  return _then(WhoamiResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,authenticated: null == authenticated ? _self.authenticated : authenticated // ignore: cast_nullable_to_non_nullable
as bool,publicKey: freezed == publicKey ? _self.publicKey : publicKey // ignore: cast_nullable_to_non_nullable
as String?,roles: null == roles ? _self._roles : roles // ignore: cast_nullable_to_non_nullable
as List<String>,interfaceSessionId: freezed == interfaceSessionId ? _self.interfaceSessionId : interfaceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,interfaceId: freezed == interfaceId ? _self.interfaceId : interfaceId // ignore: cast_nullable_to_non_nullable
as UuidValue?,lastSeenAt: freezed == lastSeenAt ? _self.lastSeenAt : lastSeenAt // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class MembershipStatusResponse implements NetworkNodeOperationResponse {
   MembershipStatusResponse({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, required this.status, this.error, required this.isActive, required this.isBypassed, this.planLabel, this.currentPeriodEnd, final  String? $type}): $type = $type ?? 'membership_status';
  factory MembershipStatusResponse.fromJson(Map<String, dynamic> json) => _$MembershipStatusResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String status;
 final  String? error;
 final  bool isActive;
 final  bool isBypassed;
 final  String? planLabel;
 final  String? currentPeriodEnd;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$MembershipStatusResponseCopyWith<MembershipStatusResponse> get copyWith => _$MembershipStatusResponseCopyWithImpl<MembershipStatusResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$MembershipStatusResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is MembershipStatusResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.isActive, isActive) || other.isActive == isActive)&&(identical(other.isBypassed, isBypassed) || other.isBypassed == isBypassed)&&(identical(other.planLabel, planLabel) || other.planLabel == planLabel)&&(identical(other.currentPeriodEnd, currentPeriodEnd) || other.currentPeriodEnd == currentPeriodEnd));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,status,error,isActive,isBypassed,planLabel,currentPeriodEnd);

@override
String toString() {
  return 'NetworkNodeOperationResponse.membershipStatus(actorId: $actorId, nodeId: $nodeId, status: $status, error: $error, isActive: $isActive, isBypassed: $isBypassed, planLabel: $planLabel, currentPeriodEnd: $currentPeriodEnd)';
}


}

/// @nodoc
abstract mixin class $MembershipStatusResponseCopyWith<$Res> implements $NetworkNodeOperationResponseCopyWith<$Res> {
  factory $MembershipStatusResponseCopyWith(MembershipStatusResponse value, $Res Function(MembershipStatusResponse) _then) = _$MembershipStatusResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String status, String? error, bool isActive, bool isBypassed, String? planLabel, String? currentPeriodEnd
});




}
/// @nodoc
class _$MembershipStatusResponseCopyWithImpl<$Res>
    implements $MembershipStatusResponseCopyWith<$Res> {
  _$MembershipStatusResponseCopyWithImpl(this._self, this._then);

  final MembershipStatusResponse _self;
  final $Res Function(MembershipStatusResponse) _then;

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? status = null,Object? error = freezed,Object? isActive = null,Object? isBypassed = null,Object? planLabel = freezed,Object? currentPeriodEnd = freezed,}) {
  return _then(MembershipStatusResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,isActive: null == isActive ? _self.isActive : isActive // ignore: cast_nullable_to_non_nullable
as bool,isBypassed: null == isBypassed ? _self.isBypassed : isBypassed // ignore: cast_nullable_to_non_nullable
as bool,planLabel: freezed == planLabel ? _self.planLabel : planLabel // ignore: cast_nullable_to_non_nullable
as String?,currentPeriodEnd: freezed == currentPeriodEnd ? _self.currentPeriodEnd : currentPeriodEnd // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class MembershipCheckoutSessionCreateResponse implements NetworkNodeOperationResponse {
   MembershipCheckoutSessionCreateResponse({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, required this.status, this.error, this.checkoutUrl, this.checkoutSessionId, final  String? $type}): $type = $type ?? 'membership_checkout_session_create';
  factory MembershipCheckoutSessionCreateResponse.fromJson(Map<String, dynamic> json) => _$MembershipCheckoutSessionCreateResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String status;
 final  String? error;
 final  String? checkoutUrl;
 final  String? checkoutSessionId;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$MembershipCheckoutSessionCreateResponseCopyWith<MembershipCheckoutSessionCreateResponse> get copyWith => _$MembershipCheckoutSessionCreateResponseCopyWithImpl<MembershipCheckoutSessionCreateResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$MembershipCheckoutSessionCreateResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is MembershipCheckoutSessionCreateResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.checkoutUrl, checkoutUrl) || other.checkoutUrl == checkoutUrl)&&(identical(other.checkoutSessionId, checkoutSessionId) || other.checkoutSessionId == checkoutSessionId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,status,error,checkoutUrl,checkoutSessionId);

@override
String toString() {
  return 'NetworkNodeOperationResponse.membershipCheckoutSessionCreate(actorId: $actorId, nodeId: $nodeId, status: $status, error: $error, checkoutUrl: $checkoutUrl, checkoutSessionId: $checkoutSessionId)';
}


}

/// @nodoc
abstract mixin class $MembershipCheckoutSessionCreateResponseCopyWith<$Res> implements $NetworkNodeOperationResponseCopyWith<$Res> {
  factory $MembershipCheckoutSessionCreateResponseCopyWith(MembershipCheckoutSessionCreateResponse value, $Res Function(MembershipCheckoutSessionCreateResponse) _then) = _$MembershipCheckoutSessionCreateResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String status, String? error, String? checkoutUrl, String? checkoutSessionId
});




}
/// @nodoc
class _$MembershipCheckoutSessionCreateResponseCopyWithImpl<$Res>
    implements $MembershipCheckoutSessionCreateResponseCopyWith<$Res> {
  _$MembershipCheckoutSessionCreateResponseCopyWithImpl(this._self, this._then);

  final MembershipCheckoutSessionCreateResponse _self;
  final $Res Function(MembershipCheckoutSessionCreateResponse) _then;

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? status = null,Object? error = freezed,Object? checkoutUrl = freezed,Object? checkoutSessionId = freezed,}) {
  return _then(MembershipCheckoutSessionCreateResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,checkoutUrl: freezed == checkoutUrl ? _self.checkoutUrl : checkoutUrl // ignore: cast_nullable_to_non_nullable
as String?,checkoutSessionId: freezed == checkoutSessionId ? _self.checkoutSessionId : checkoutSessionId // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class MembershipPurchasePrepareResponse implements NetworkNodeOperationResponse {
   MembershipPurchasePrepareResponse({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, required this.status, this.error, required this.provider, this.planLabel, this.checkoutUrl, this.appleProductId, this.googleProductId, final  String? $type}): $type = $type ?? 'membership_purchase_prepare';
  factory MembershipPurchasePrepareResponse.fromJson(Map<String, dynamic> json) => _$MembershipPurchasePrepareResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String status;
 final  String? error;
 final  String provider;
 final  String? planLabel;
 final  String? checkoutUrl;
 final  String? appleProductId;
 final  String? googleProductId;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$MembershipPurchasePrepareResponseCopyWith<MembershipPurchasePrepareResponse> get copyWith => _$MembershipPurchasePrepareResponseCopyWithImpl<MembershipPurchasePrepareResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$MembershipPurchasePrepareResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is MembershipPurchasePrepareResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.provider, provider) || other.provider == provider)&&(identical(other.planLabel, planLabel) || other.planLabel == planLabel)&&(identical(other.checkoutUrl, checkoutUrl) || other.checkoutUrl == checkoutUrl)&&(identical(other.appleProductId, appleProductId) || other.appleProductId == appleProductId)&&(identical(other.googleProductId, googleProductId) || other.googleProductId == googleProductId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,status,error,provider,planLabel,checkoutUrl,appleProductId,googleProductId);

@override
String toString() {
  return 'NetworkNodeOperationResponse.membershipPurchasePrepare(actorId: $actorId, nodeId: $nodeId, status: $status, error: $error, provider: $provider, planLabel: $planLabel, checkoutUrl: $checkoutUrl, appleProductId: $appleProductId, googleProductId: $googleProductId)';
}


}

/// @nodoc
abstract mixin class $MembershipPurchasePrepareResponseCopyWith<$Res> implements $NetworkNodeOperationResponseCopyWith<$Res> {
  factory $MembershipPurchasePrepareResponseCopyWith(MembershipPurchasePrepareResponse value, $Res Function(MembershipPurchasePrepareResponse) _then) = _$MembershipPurchasePrepareResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String status, String? error, String provider, String? planLabel, String? checkoutUrl, String? appleProductId, String? googleProductId
});




}
/// @nodoc
class _$MembershipPurchasePrepareResponseCopyWithImpl<$Res>
    implements $MembershipPurchasePrepareResponseCopyWith<$Res> {
  _$MembershipPurchasePrepareResponseCopyWithImpl(this._self, this._then);

  final MembershipPurchasePrepareResponse _self;
  final $Res Function(MembershipPurchasePrepareResponse) _then;

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? status = null,Object? error = freezed,Object? provider = null,Object? planLabel = freezed,Object? checkoutUrl = freezed,Object? appleProductId = freezed,Object? googleProductId = freezed,}) {
  return _then(MembershipPurchasePrepareResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,provider: null == provider ? _self.provider : provider // ignore: cast_nullable_to_non_nullable
as String,planLabel: freezed == planLabel ? _self.planLabel : planLabel // ignore: cast_nullable_to_non_nullable
as String?,checkoutUrl: freezed == checkoutUrl ? _self.checkoutUrl : checkoutUrl // ignore: cast_nullable_to_non_nullable
as String?,appleProductId: freezed == appleProductId ? _self.appleProductId : appleProductId // ignore: cast_nullable_to_non_nullable
as String?,googleProductId: freezed == googleProductId ? _self.googleProductId : googleProductId // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class MembershipPurchaseClaimResponse implements NetworkNodeOperationResponse {
   MembershipPurchaseClaimResponse({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, required this.status, this.error, required this.isActive, this.planLabel, this.currentPeriodEnd, final  String? $type}): $type = $type ?? 'membership_purchase_claim';
  factory MembershipPurchaseClaimResponse.fromJson(Map<String, dynamic> json) => _$MembershipPurchaseClaimResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String status;
 final  String? error;
 final  bool isActive;
 final  String? planLabel;
 final  String? currentPeriodEnd;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$MembershipPurchaseClaimResponseCopyWith<MembershipPurchaseClaimResponse> get copyWith => _$MembershipPurchaseClaimResponseCopyWithImpl<MembershipPurchaseClaimResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$MembershipPurchaseClaimResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is MembershipPurchaseClaimResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.isActive, isActive) || other.isActive == isActive)&&(identical(other.planLabel, planLabel) || other.planLabel == planLabel)&&(identical(other.currentPeriodEnd, currentPeriodEnd) || other.currentPeriodEnd == currentPeriodEnd));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,status,error,isActive,planLabel,currentPeriodEnd);

@override
String toString() {
  return 'NetworkNodeOperationResponse.membershipPurchaseClaim(actorId: $actorId, nodeId: $nodeId, status: $status, error: $error, isActive: $isActive, planLabel: $planLabel, currentPeriodEnd: $currentPeriodEnd)';
}


}

/// @nodoc
abstract mixin class $MembershipPurchaseClaimResponseCopyWith<$Res> implements $NetworkNodeOperationResponseCopyWith<$Res> {
  factory $MembershipPurchaseClaimResponseCopyWith(MembershipPurchaseClaimResponse value, $Res Function(MembershipPurchaseClaimResponse) _then) = _$MembershipPurchaseClaimResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String status, String? error, bool isActive, String? planLabel, String? currentPeriodEnd
});




}
/// @nodoc
class _$MembershipPurchaseClaimResponseCopyWithImpl<$Res>
    implements $MembershipPurchaseClaimResponseCopyWith<$Res> {
  _$MembershipPurchaseClaimResponseCopyWithImpl(this._self, this._then);

  final MembershipPurchaseClaimResponse _self;
  final $Res Function(MembershipPurchaseClaimResponse) _then;

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? status = null,Object? error = freezed,Object? isActive = null,Object? planLabel = freezed,Object? currentPeriodEnd = freezed,}) {
  return _then(MembershipPurchaseClaimResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,isActive: null == isActive ? _self.isActive : isActive // ignore: cast_nullable_to_non_nullable
as bool,planLabel: freezed == planLabel ? _self.planLabel : planLabel // ignore: cast_nullable_to_non_nullable
as String?,currentPeriodEnd: freezed == currentPeriodEnd ? _self.currentPeriodEnd : currentPeriodEnd // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class ProvisionEnvironmentResponse implements NetworkNodeOperationResponse {
   ProvisionEnvironmentResponse({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, required this.status, this.error, @UuidValueConverter() this.environmentId, @UuidValueConverter() this.environmentConfigId, this.environmentConfigTitle, this.environmentTitle, this.environmentEndpoint, this.ocgHash, @UuidValueConverter() this.processId, @UuidValueConverter() this.threadId, @UuidValueConverter() this.branchId, final  List<String> opgHashes = const [], this.provisioningReceipt, final  String? $type}): _opgHashes = opgHashes,$type = $type ?? 'provision_environment';
  factory ProvisionEnvironmentResponse.fromJson(Map<String, dynamic> json) => _$ProvisionEnvironmentResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String status;
 final  String? error;
@UuidValueConverter() final  UuidValue? environmentId;
@UuidValueConverter() final  UuidValue? environmentConfigId;
 final  String? environmentConfigTitle;
 final  String? environmentTitle;
 final  String? environmentEndpoint;
 final  String? ocgHash;
@UuidValueConverter() final  UuidValue? processId;
@UuidValueConverter() final  UuidValue? threadId;
@UuidValueConverter() final  UuidValue? branchId;
 final  List<String> _opgHashes;
@JsonKey() List<String> get opgHashes {
  if (_opgHashes is EqualUnmodifiableListView) return _opgHashes;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_opgHashes);
}

 final  NodeEnvironmentProvisioningReceipt? provisioningReceipt;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ProvisionEnvironmentResponseCopyWith<ProvisionEnvironmentResponse> get copyWith => _$ProvisionEnvironmentResponseCopyWithImpl<ProvisionEnvironmentResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ProvisionEnvironmentResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ProvisionEnvironmentResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentConfigId, environmentConfigId) || other.environmentConfigId == environmentConfigId)&&(identical(other.environmentConfigTitle, environmentConfigTitle) || other.environmentConfigTitle == environmentConfigTitle)&&(identical(other.environmentTitle, environmentTitle) || other.environmentTitle == environmentTitle)&&(identical(other.environmentEndpoint, environmentEndpoint) || other.environmentEndpoint == environmentEndpoint)&&(identical(other.ocgHash, ocgHash) || other.ocgHash == ocgHash)&&(identical(other.processId, processId) || other.processId == processId)&&(identical(other.threadId, threadId) || other.threadId == threadId)&&(identical(other.branchId, branchId) || other.branchId == branchId)&&const DeepCollectionEquality().equals(other._opgHashes, _opgHashes)&&(identical(other.provisioningReceipt, provisioningReceipt) || other.provisioningReceipt == provisioningReceipt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,status,error,environmentId,environmentConfigId,environmentConfigTitle,environmentTitle,environmentEndpoint,ocgHash,processId,threadId,branchId,const DeepCollectionEquality().hash(_opgHashes),provisioningReceipt);

@override
String toString() {
  return 'NetworkNodeOperationResponse.provisionEnvironment(actorId: $actorId, nodeId: $nodeId, status: $status, error: $error, environmentId: $environmentId, environmentConfigId: $environmentConfigId, environmentConfigTitle: $environmentConfigTitle, environmentTitle: $environmentTitle, environmentEndpoint: $environmentEndpoint, ocgHash: $ocgHash, processId: $processId, threadId: $threadId, branchId: $branchId, opgHashes: $opgHashes, provisioningReceipt: $provisioningReceipt)';
}


}

/// @nodoc
abstract mixin class $ProvisionEnvironmentResponseCopyWith<$Res> implements $NetworkNodeOperationResponseCopyWith<$Res> {
  factory $ProvisionEnvironmentResponseCopyWith(ProvisionEnvironmentResponse value, $Res Function(ProvisionEnvironmentResponse) _then) = _$ProvisionEnvironmentResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String status, String? error,@UuidValueConverter() UuidValue? environmentId,@UuidValueConverter() UuidValue? environmentConfigId, String? environmentConfigTitle, String? environmentTitle, String? environmentEndpoint, String? ocgHash,@UuidValueConverter() UuidValue? processId,@UuidValueConverter() UuidValue? threadId,@UuidValueConverter() UuidValue? branchId, List<String> opgHashes, NodeEnvironmentProvisioningReceipt? provisioningReceipt
});


$NodeEnvironmentProvisioningReceiptCopyWith<$Res>? get provisioningReceipt;

}
/// @nodoc
class _$ProvisionEnvironmentResponseCopyWithImpl<$Res>
    implements $ProvisionEnvironmentResponseCopyWith<$Res> {
  _$ProvisionEnvironmentResponseCopyWithImpl(this._self, this._then);

  final ProvisionEnvironmentResponse _self;
  final $Res Function(ProvisionEnvironmentResponse) _then;

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? status = null,Object? error = freezed,Object? environmentId = freezed,Object? environmentConfigId = freezed,Object? environmentConfigTitle = freezed,Object? environmentTitle = freezed,Object? environmentEndpoint = freezed,Object? ocgHash = freezed,Object? processId = freezed,Object? threadId = freezed,Object? branchId = freezed,Object? opgHashes = null,Object? provisioningReceipt = freezed,}) {
  return _then(ProvisionEnvironmentResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,environmentId: freezed == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentConfigId: freezed == environmentConfigId ? _self.environmentConfigId : environmentConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentConfigTitle: freezed == environmentConfigTitle ? _self.environmentConfigTitle : environmentConfigTitle // ignore: cast_nullable_to_non_nullable
as String?,environmentTitle: freezed == environmentTitle ? _self.environmentTitle : environmentTitle // ignore: cast_nullable_to_non_nullable
as String?,environmentEndpoint: freezed == environmentEndpoint ? _self.environmentEndpoint : environmentEndpoint // ignore: cast_nullable_to_non_nullable
as String?,ocgHash: freezed == ocgHash ? _self.ocgHash : ocgHash // ignore: cast_nullable_to_non_nullable
as String?,processId: freezed == processId ? _self.processId : processId // ignore: cast_nullable_to_non_nullable
as UuidValue?,threadId: freezed == threadId ? _self.threadId : threadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,branchId: freezed == branchId ? _self.branchId : branchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,opgHashes: null == opgHashes ? _self._opgHashes : opgHashes // ignore: cast_nullable_to_non_nullable
as List<String>,provisioningReceipt: freezed == provisioningReceipt ? _self.provisioningReceipt : provisioningReceipt // ignore: cast_nullable_to_non_nullable
as NodeEnvironmentProvisioningReceipt?,
  ));
}

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeEnvironmentProvisioningReceiptCopyWith<$Res>? get provisioningReceipt {
    if (_self.provisioningReceipt == null) {
    return null;
  }

  return $NodeEnvironmentProvisioningReceiptCopyWith<$Res>(_self.provisioningReceipt!, (value) {
    return _then(_self.copyWith(provisioningReceipt: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class GetBootEnvironmentDescriptorResponse implements NetworkNodeOperationResponse {
   GetBootEnvironmentDescriptorResponse({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, required this.status, this.error, this.descriptor, final  String? $type}): $type = $type ?? 'get_boot_environment_descriptor';
  factory GetBootEnvironmentDescriptorResponse.fromJson(Map<String, dynamic> json) => _$GetBootEnvironmentDescriptorResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String status;
 final  String? error;
 final  BootEnvironmentDescriptor? descriptor;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$GetBootEnvironmentDescriptorResponseCopyWith<GetBootEnvironmentDescriptorResponse> get copyWith => _$GetBootEnvironmentDescriptorResponseCopyWithImpl<GetBootEnvironmentDescriptorResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$GetBootEnvironmentDescriptorResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is GetBootEnvironmentDescriptorResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.descriptor, descriptor) || other.descriptor == descriptor));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,status,error,descriptor);

@override
String toString() {
  return 'NetworkNodeOperationResponse.getBootEnvironmentDescriptor(actorId: $actorId, nodeId: $nodeId, status: $status, error: $error, descriptor: $descriptor)';
}


}

/// @nodoc
abstract mixin class $GetBootEnvironmentDescriptorResponseCopyWith<$Res> implements $NetworkNodeOperationResponseCopyWith<$Res> {
  factory $GetBootEnvironmentDescriptorResponseCopyWith(GetBootEnvironmentDescriptorResponse value, $Res Function(GetBootEnvironmentDescriptorResponse) _then) = _$GetBootEnvironmentDescriptorResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String status, String? error, BootEnvironmentDescriptor? descriptor
});


$BootEnvironmentDescriptorCopyWith<$Res>? get descriptor;

}
/// @nodoc
class _$GetBootEnvironmentDescriptorResponseCopyWithImpl<$Res>
    implements $GetBootEnvironmentDescriptorResponseCopyWith<$Res> {
  _$GetBootEnvironmentDescriptorResponseCopyWithImpl(this._self, this._then);

  final GetBootEnvironmentDescriptorResponse _self;
  final $Res Function(GetBootEnvironmentDescriptorResponse) _then;

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? status = null,Object? error = freezed,Object? descriptor = freezed,}) {
  return _then(GetBootEnvironmentDescriptorResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,descriptor: freezed == descriptor ? _self.descriptor : descriptor // ignore: cast_nullable_to_non_nullable
as BootEnvironmentDescriptor?,
  ));
}

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$BootEnvironmentDescriptorCopyWith<$Res>? get descriptor {
    if (_self.descriptor == null) {
    return null;
  }

  return $BootEnvironmentDescriptorCopyWith<$Res>(_self.descriptor!, (value) {
    return _then(_self.copyWith(descriptor: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DiscoverEnvironmentConfigsResponse implements NetworkNodeOperationResponse {
   DiscoverEnvironmentConfigsResponse({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, final  List<EnvironmentConfigDescriptor> configs = const [], final  String? $type}): _configs = configs,$type = $type ?? 'discover_environment_configs';
  factory DiscoverEnvironmentConfigsResponse.fromJson(Map<String, dynamic> json) => _$DiscoverEnvironmentConfigsResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  List<EnvironmentConfigDescriptor> _configs;
@JsonKey() List<EnvironmentConfigDescriptor> get configs {
  if (_configs is EqualUnmodifiableListView) return _configs;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_configs);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DiscoverEnvironmentConfigsResponseCopyWith<DiscoverEnvironmentConfigsResponse> get copyWith => _$DiscoverEnvironmentConfigsResponseCopyWithImpl<DiscoverEnvironmentConfigsResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DiscoverEnvironmentConfigsResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DiscoverEnvironmentConfigsResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&const DeepCollectionEquality().equals(other._configs, _configs));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,const DeepCollectionEquality().hash(_configs));

@override
String toString() {
  return 'NetworkNodeOperationResponse.discoverEnvironmentConfigs(actorId: $actorId, nodeId: $nodeId, configs: $configs)';
}


}

/// @nodoc
abstract mixin class $DiscoverEnvironmentConfigsResponseCopyWith<$Res> implements $NetworkNodeOperationResponseCopyWith<$Res> {
  factory $DiscoverEnvironmentConfigsResponseCopyWith(DiscoverEnvironmentConfigsResponse value, $Res Function(DiscoverEnvironmentConfigsResponse) _then) = _$DiscoverEnvironmentConfigsResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, List<EnvironmentConfigDescriptor> configs
});




}
/// @nodoc
class _$DiscoverEnvironmentConfigsResponseCopyWithImpl<$Res>
    implements $DiscoverEnvironmentConfigsResponseCopyWith<$Res> {
  _$DiscoverEnvironmentConfigsResponseCopyWithImpl(this._self, this._then);

  final DiscoverEnvironmentConfigsResponse _self;
  final $Res Function(DiscoverEnvironmentConfigsResponse) _then;

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? configs = null,}) {
  return _then(DiscoverEnvironmentConfigsResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,configs: null == configs ? _self._configs : configs // ignore: cast_nullable_to_non_nullable
as List<EnvironmentConfigDescriptor>,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DiscoverServiceApiDependencyRoutesResponse implements NetworkNodeOperationResponse {
   DiscoverServiceApiDependencyRoutesResponse({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, final  List<ServiceApiDependencyRouteDescriptor> routes = const [], final  String? $type}): _routes = routes,$type = $type ?? 'discover_service_api_dependency_routes';
  factory DiscoverServiceApiDependencyRoutesResponse.fromJson(Map<String, dynamic> json) => _$DiscoverServiceApiDependencyRoutesResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  List<ServiceApiDependencyRouteDescriptor> _routes;
@JsonKey() List<ServiceApiDependencyRouteDescriptor> get routes {
  if (_routes is EqualUnmodifiableListView) return _routes;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_routes);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DiscoverServiceApiDependencyRoutesResponseCopyWith<DiscoverServiceApiDependencyRoutesResponse> get copyWith => _$DiscoverServiceApiDependencyRoutesResponseCopyWithImpl<DiscoverServiceApiDependencyRoutesResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DiscoverServiceApiDependencyRoutesResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DiscoverServiceApiDependencyRoutesResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&const DeepCollectionEquality().equals(other._routes, _routes));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,const DeepCollectionEquality().hash(_routes));

@override
String toString() {
  return 'NetworkNodeOperationResponse.discoverServiceApiDependencyRoutes(actorId: $actorId, nodeId: $nodeId, routes: $routes)';
}


}

/// @nodoc
abstract mixin class $DiscoverServiceApiDependencyRoutesResponseCopyWith<$Res> implements $NetworkNodeOperationResponseCopyWith<$Res> {
  factory $DiscoverServiceApiDependencyRoutesResponseCopyWith(DiscoverServiceApiDependencyRoutesResponse value, $Res Function(DiscoverServiceApiDependencyRoutesResponse) _then) = _$DiscoverServiceApiDependencyRoutesResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, List<ServiceApiDependencyRouteDescriptor> routes
});




}
/// @nodoc
class _$DiscoverServiceApiDependencyRoutesResponseCopyWithImpl<$Res>
    implements $DiscoverServiceApiDependencyRoutesResponseCopyWith<$Res> {
  _$DiscoverServiceApiDependencyRoutesResponseCopyWithImpl(this._self, this._then);

  final DiscoverServiceApiDependencyRoutesResponse _self;
  final $Res Function(DiscoverServiceApiDependencyRoutesResponse) _then;

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? routes = null,}) {
  return _then(DiscoverServiceApiDependencyRoutesResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,routes: null == routes ? _self._routes : routes // ignore: cast_nullable_to_non_nullable
as List<ServiceApiDependencyRouteDescriptor>,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DiscoverHostedServicesResponse implements NetworkNodeOperationResponse {
   DiscoverHostedServicesResponse({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, final  List<HostedServiceAdvertisement> hostedServices = const [], final  String? $type}): _hostedServices = hostedServices,$type = $type ?? 'discover_hosted_services';
  factory DiscoverHostedServicesResponse.fromJson(Map<String, dynamic> json) => _$DiscoverHostedServicesResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  List<HostedServiceAdvertisement> _hostedServices;
@JsonKey() List<HostedServiceAdvertisement> get hostedServices {
  if (_hostedServices is EqualUnmodifiableListView) return _hostedServices;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_hostedServices);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DiscoverHostedServicesResponseCopyWith<DiscoverHostedServicesResponse> get copyWith => _$DiscoverHostedServicesResponseCopyWithImpl<DiscoverHostedServicesResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DiscoverHostedServicesResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DiscoverHostedServicesResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&const DeepCollectionEquality().equals(other._hostedServices, _hostedServices));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,const DeepCollectionEquality().hash(_hostedServices));

@override
String toString() {
  return 'NetworkNodeOperationResponse.discoverHostedServices(actorId: $actorId, nodeId: $nodeId, hostedServices: $hostedServices)';
}


}

/// @nodoc
abstract mixin class $DiscoverHostedServicesResponseCopyWith<$Res> implements $NetworkNodeOperationResponseCopyWith<$Res> {
  factory $DiscoverHostedServicesResponseCopyWith(DiscoverHostedServicesResponse value, $Res Function(DiscoverHostedServicesResponse) _then) = _$DiscoverHostedServicesResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, List<HostedServiceAdvertisement> hostedServices
});




}
/// @nodoc
class _$DiscoverHostedServicesResponseCopyWithImpl<$Res>
    implements $DiscoverHostedServicesResponseCopyWith<$Res> {
  _$DiscoverHostedServicesResponseCopyWithImpl(this._self, this._then);

  final DiscoverHostedServicesResponse _self;
  final $Res Function(DiscoverHostedServicesResponse) _then;

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? hostedServices = null,}) {
  return _then(DiscoverHostedServicesResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,hostedServices: null == hostedServices ? _self._hostedServices : hostedServices // ignore: cast_nullable_to_non_nullable
as List<HostedServiceAdvertisement>,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DescribeHostedServiceRuntimesResponse implements NetworkNodeOperationResponse {
   DescribeHostedServiceRuntimesResponse({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, final  List<HostedServiceRuntimeStatus> hostedServiceRuntimes = const [], final  String? $type}): _hostedServiceRuntimes = hostedServiceRuntimes,$type = $type ?? 'describe_hosted_service_runtimes';
  factory DescribeHostedServiceRuntimesResponse.fromJson(Map<String, dynamic> json) => _$DescribeHostedServiceRuntimesResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  List<HostedServiceRuntimeStatus> _hostedServiceRuntimes;
@JsonKey() List<HostedServiceRuntimeStatus> get hostedServiceRuntimes {
  if (_hostedServiceRuntimes is EqualUnmodifiableListView) return _hostedServiceRuntimes;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_hostedServiceRuntimes);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DescribeHostedServiceRuntimesResponseCopyWith<DescribeHostedServiceRuntimesResponse> get copyWith => _$DescribeHostedServiceRuntimesResponseCopyWithImpl<DescribeHostedServiceRuntimesResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DescribeHostedServiceRuntimesResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DescribeHostedServiceRuntimesResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&const DeepCollectionEquality().equals(other._hostedServiceRuntimes, _hostedServiceRuntimes));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,const DeepCollectionEquality().hash(_hostedServiceRuntimes));

@override
String toString() {
  return 'NetworkNodeOperationResponse.describeHostedServiceRuntimes(actorId: $actorId, nodeId: $nodeId, hostedServiceRuntimes: $hostedServiceRuntimes)';
}


}

/// @nodoc
abstract mixin class $DescribeHostedServiceRuntimesResponseCopyWith<$Res> implements $NetworkNodeOperationResponseCopyWith<$Res> {
  factory $DescribeHostedServiceRuntimesResponseCopyWith(DescribeHostedServiceRuntimesResponse value, $Res Function(DescribeHostedServiceRuntimesResponse) _then) = _$DescribeHostedServiceRuntimesResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, List<HostedServiceRuntimeStatus> hostedServiceRuntimes
});




}
/// @nodoc
class _$DescribeHostedServiceRuntimesResponseCopyWithImpl<$Res>
    implements $DescribeHostedServiceRuntimesResponseCopyWith<$Res> {
  _$DescribeHostedServiceRuntimesResponseCopyWithImpl(this._self, this._then);

  final DescribeHostedServiceRuntimesResponse _self;
  final $Res Function(DescribeHostedServiceRuntimesResponse) _then;

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? hostedServiceRuntimes = null,}) {
  return _then(DescribeHostedServiceRuntimesResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,hostedServiceRuntimes: null == hostedServiceRuntimes ? _self._hostedServiceRuntimes : hostedServiceRuntimes // ignore: cast_nullable_to_non_nullable
as List<HostedServiceRuntimeStatus>,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class GetEnvironmentStatusResponse implements NetworkNodeOperationResponse {
   GetEnvironmentStatusResponse({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, required this.status, this.error, @UuidValueConverter() required this.environmentId, @UuidValueConverter() this.environmentConfigId, this.environmentConfigTitle, this.environmentTitle, this.environmentEndpoint, this.ocgHash, @UuidValueConverter() this.processId, @UuidValueConverter() this.threadId, @UuidValueConverter() this.branchId, final  List<String> opgHashes = const [], this.provisioningReceipt, final  String? $type}): _opgHashes = opgHashes,$type = $type ?? 'get_environment_status';
  factory GetEnvironmentStatusResponse.fromJson(Map<String, dynamic> json) => _$GetEnvironmentStatusResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String status;
 final  String? error;
@UuidValueConverter() final  UuidValue environmentId;
@UuidValueConverter() final  UuidValue? environmentConfigId;
 final  String? environmentConfigTitle;
 final  String? environmentTitle;
 final  String? environmentEndpoint;
 final  String? ocgHash;
@UuidValueConverter() final  UuidValue? processId;
@UuidValueConverter() final  UuidValue? threadId;
@UuidValueConverter() final  UuidValue? branchId;
 final  List<String> _opgHashes;
@JsonKey() List<String> get opgHashes {
  if (_opgHashes is EqualUnmodifiableListView) return _opgHashes;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_opgHashes);
}

 final  NodeEnvironmentProvisioningReceipt? provisioningReceipt;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$GetEnvironmentStatusResponseCopyWith<GetEnvironmentStatusResponse> get copyWith => _$GetEnvironmentStatusResponseCopyWithImpl<GetEnvironmentStatusResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$GetEnvironmentStatusResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is GetEnvironmentStatusResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentConfigId, environmentConfigId) || other.environmentConfigId == environmentConfigId)&&(identical(other.environmentConfigTitle, environmentConfigTitle) || other.environmentConfigTitle == environmentConfigTitle)&&(identical(other.environmentTitle, environmentTitle) || other.environmentTitle == environmentTitle)&&(identical(other.environmentEndpoint, environmentEndpoint) || other.environmentEndpoint == environmentEndpoint)&&(identical(other.ocgHash, ocgHash) || other.ocgHash == ocgHash)&&(identical(other.processId, processId) || other.processId == processId)&&(identical(other.threadId, threadId) || other.threadId == threadId)&&(identical(other.branchId, branchId) || other.branchId == branchId)&&const DeepCollectionEquality().equals(other._opgHashes, _opgHashes)&&(identical(other.provisioningReceipt, provisioningReceipt) || other.provisioningReceipt == provisioningReceipt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,status,error,environmentId,environmentConfigId,environmentConfigTitle,environmentTitle,environmentEndpoint,ocgHash,processId,threadId,branchId,const DeepCollectionEquality().hash(_opgHashes),provisioningReceipt);

@override
String toString() {
  return 'NetworkNodeOperationResponse.getEnvironmentStatus(actorId: $actorId, nodeId: $nodeId, status: $status, error: $error, environmentId: $environmentId, environmentConfigId: $environmentConfigId, environmentConfigTitle: $environmentConfigTitle, environmentTitle: $environmentTitle, environmentEndpoint: $environmentEndpoint, ocgHash: $ocgHash, processId: $processId, threadId: $threadId, branchId: $branchId, opgHashes: $opgHashes, provisioningReceipt: $provisioningReceipt)';
}


}

/// @nodoc
abstract mixin class $GetEnvironmentStatusResponseCopyWith<$Res> implements $NetworkNodeOperationResponseCopyWith<$Res> {
  factory $GetEnvironmentStatusResponseCopyWith(GetEnvironmentStatusResponse value, $Res Function(GetEnvironmentStatusResponse) _then) = _$GetEnvironmentStatusResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String status, String? error,@UuidValueConverter() UuidValue environmentId,@UuidValueConverter() UuidValue? environmentConfigId, String? environmentConfigTitle, String? environmentTitle, String? environmentEndpoint, String? ocgHash,@UuidValueConverter() UuidValue? processId,@UuidValueConverter() UuidValue? threadId,@UuidValueConverter() UuidValue? branchId, List<String> opgHashes, NodeEnvironmentProvisioningReceipt? provisioningReceipt
});


$NodeEnvironmentProvisioningReceiptCopyWith<$Res>? get provisioningReceipt;

}
/// @nodoc
class _$GetEnvironmentStatusResponseCopyWithImpl<$Res>
    implements $GetEnvironmentStatusResponseCopyWith<$Res> {
  _$GetEnvironmentStatusResponseCopyWithImpl(this._self, this._then);

  final GetEnvironmentStatusResponse _self;
  final $Res Function(GetEnvironmentStatusResponse) _then;

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? status = null,Object? error = freezed,Object? environmentId = null,Object? environmentConfigId = freezed,Object? environmentConfigTitle = freezed,Object? environmentTitle = freezed,Object? environmentEndpoint = freezed,Object? ocgHash = freezed,Object? processId = freezed,Object? threadId = freezed,Object? branchId = freezed,Object? opgHashes = null,Object? provisioningReceipt = freezed,}) {
  return _then(GetEnvironmentStatusResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,environmentId: null == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentConfigId: freezed == environmentConfigId ? _self.environmentConfigId : environmentConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentConfigTitle: freezed == environmentConfigTitle ? _self.environmentConfigTitle : environmentConfigTitle // ignore: cast_nullable_to_non_nullable
as String?,environmentTitle: freezed == environmentTitle ? _self.environmentTitle : environmentTitle // ignore: cast_nullable_to_non_nullable
as String?,environmentEndpoint: freezed == environmentEndpoint ? _self.environmentEndpoint : environmentEndpoint // ignore: cast_nullable_to_non_nullable
as String?,ocgHash: freezed == ocgHash ? _self.ocgHash : ocgHash // ignore: cast_nullable_to_non_nullable
as String?,processId: freezed == processId ? _self.processId : processId // ignore: cast_nullable_to_non_nullable
as UuidValue?,threadId: freezed == threadId ? _self.threadId : threadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,branchId: freezed == branchId ? _self.branchId : branchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,opgHashes: null == opgHashes ? _self._opgHashes : opgHashes // ignore: cast_nullable_to_non_nullable
as List<String>,provisioningReceipt: freezed == provisioningReceipt ? _self.provisioningReceipt : provisioningReceipt // ignore: cast_nullable_to_non_nullable
as NodeEnvironmentProvisioningReceipt?,
  ));
}

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeEnvironmentProvisioningReceiptCopyWith<$Res>? get provisioningReceipt {
    if (_self.provisioningReceipt == null) {
    return null;
  }

  return $NodeEnvironmentProvisioningReceiptCopyWith<$Res>(_self.provisioningReceipt!, (value) {
    return _then(_self.copyWith(provisioningReceipt: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class CloseStreamResponse implements NetworkNodeOperationResponse {
   CloseStreamResponse({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, required this.status, this.error, @UuidValueConverter() required this.networkOperationId, final  String? $type}): $type = $type ?? 'close_stream';
  factory CloseStreamResponse.fromJson(Map<String, dynamic> json) => _$CloseStreamResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String status;
 final  String? error;
@UuidValueConverter() final  UuidValue networkOperationId;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$CloseStreamResponseCopyWith<CloseStreamResponse> get copyWith => _$CloseStreamResponseCopyWithImpl<CloseStreamResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$CloseStreamResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is CloseStreamResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.networkOperationId, networkOperationId) || other.networkOperationId == networkOperationId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,status,error,networkOperationId);

@override
String toString() {
  return 'NetworkNodeOperationResponse.closeStream(actorId: $actorId, nodeId: $nodeId, status: $status, error: $error, networkOperationId: $networkOperationId)';
}


}

/// @nodoc
abstract mixin class $CloseStreamResponseCopyWith<$Res> implements $NetworkNodeOperationResponseCopyWith<$Res> {
  factory $CloseStreamResponseCopyWith(CloseStreamResponse value, $Res Function(CloseStreamResponse) _then) = _$CloseStreamResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String status, String? error,@UuidValueConverter() UuidValue networkOperationId
});




}
/// @nodoc
class _$CloseStreamResponseCopyWithImpl<$Res>
    implements $CloseStreamResponseCopyWith<$Res> {
  _$CloseStreamResponseCopyWithImpl(this._self, this._then);

  final CloseStreamResponse _self;
  final $Res Function(CloseStreamResponse) _then;

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? status = null,Object? error = freezed,Object? networkOperationId = null,}) {
  return _then(CloseStreamResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,networkOperationId: null == networkOperationId ? _self.networkOperationId : networkOperationId // ignore: cast_nullable_to_non_nullable
as UuidValue,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceSessionRegisterResponse implements NetworkNodeOperationResponse {
   InterfaceSessionRegisterResponse({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, required this.status, this.error, @UuidValueConverter() required this.interfaceId, @UuidValueConverter() required this.interfaceSessionId, @UuidValueConverter() this.interfaceIdentityNetworkNodeId, @UuidValueConverter() this.interfaceSessionNetworkBindingId, this.lastSeenAt, required this.protocolVersion, final  String? $type}): $type = $type ?? 'interface_session_register';
  factory InterfaceSessionRegisterResponse.fromJson(Map<String, dynamic> json) => _$InterfaceSessionRegisterResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String status;
 final  String? error;
@UuidValueConverter() final  UuidValue interfaceId;
@UuidValueConverter() final  UuidValue interfaceSessionId;
@UuidValueConverter() final  UuidValue? interfaceIdentityNetworkNodeId;
@UuidValueConverter() final  UuidValue? interfaceSessionNetworkBindingId;
 final  String? lastSeenAt;
 final  int protocolVersion;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSessionRegisterResponseCopyWith<InterfaceSessionRegisterResponse> get copyWith => _$InterfaceSessionRegisterResponseCopyWithImpl<InterfaceSessionRegisterResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSessionRegisterResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSessionRegisterResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.interfaceId, interfaceId) || other.interfaceId == interfaceId)&&(identical(other.interfaceSessionId, interfaceSessionId) || other.interfaceSessionId == interfaceSessionId)&&(identical(other.interfaceIdentityNetworkNodeId, interfaceIdentityNetworkNodeId) || other.interfaceIdentityNetworkNodeId == interfaceIdentityNetworkNodeId)&&(identical(other.interfaceSessionNetworkBindingId, interfaceSessionNetworkBindingId) || other.interfaceSessionNetworkBindingId == interfaceSessionNetworkBindingId)&&(identical(other.lastSeenAt, lastSeenAt) || other.lastSeenAt == lastSeenAt)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,status,error,interfaceId,interfaceSessionId,interfaceIdentityNetworkNodeId,interfaceSessionNetworkBindingId,lastSeenAt,protocolVersion);

@override
String toString() {
  return 'NetworkNodeOperationResponse.interfaceSessionRegister(actorId: $actorId, nodeId: $nodeId, status: $status, error: $error, interfaceId: $interfaceId, interfaceSessionId: $interfaceSessionId, interfaceIdentityNetworkNodeId: $interfaceIdentityNetworkNodeId, interfaceSessionNetworkBindingId: $interfaceSessionNetworkBindingId, lastSeenAt: $lastSeenAt, protocolVersion: $protocolVersion)';
}


}

/// @nodoc
abstract mixin class $InterfaceSessionRegisterResponseCopyWith<$Res> implements $NetworkNodeOperationResponseCopyWith<$Res> {
  factory $InterfaceSessionRegisterResponseCopyWith(InterfaceSessionRegisterResponse value, $Res Function(InterfaceSessionRegisterResponse) _then) = _$InterfaceSessionRegisterResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String status, String? error,@UuidValueConverter() UuidValue interfaceId,@UuidValueConverter() UuidValue interfaceSessionId,@UuidValueConverter() UuidValue? interfaceIdentityNetworkNodeId,@UuidValueConverter() UuidValue? interfaceSessionNetworkBindingId, String? lastSeenAt, int protocolVersion
});




}
/// @nodoc
class _$InterfaceSessionRegisterResponseCopyWithImpl<$Res>
    implements $InterfaceSessionRegisterResponseCopyWith<$Res> {
  _$InterfaceSessionRegisterResponseCopyWithImpl(this._self, this._then);

  final InterfaceSessionRegisterResponse _self;
  final $Res Function(InterfaceSessionRegisterResponse) _then;

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? status = null,Object? error = freezed,Object? interfaceId = null,Object? interfaceSessionId = null,Object? interfaceIdentityNetworkNodeId = freezed,Object? interfaceSessionNetworkBindingId = freezed,Object? lastSeenAt = freezed,Object? protocolVersion = null,}) {
  return _then(InterfaceSessionRegisterResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,interfaceId: null == interfaceId ? _self.interfaceId : interfaceId // ignore: cast_nullable_to_non_nullable
as UuidValue,interfaceSessionId: null == interfaceSessionId ? _self.interfaceSessionId : interfaceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,interfaceIdentityNetworkNodeId: freezed == interfaceIdentityNetworkNodeId ? _self.interfaceIdentityNetworkNodeId : interfaceIdentityNetworkNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,interfaceSessionNetworkBindingId: freezed == interfaceSessionNetworkBindingId ? _self.interfaceSessionNetworkBindingId : interfaceSessionNetworkBindingId // ignore: cast_nullable_to_non_nullable
as UuidValue?,lastSeenAt: freezed == lastSeenAt ? _self.lastSeenAt : lastSeenAt // ignore: cast_nullable_to_non_nullable
as String?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceSessionHeartbeatResponse implements NetworkNodeOperationResponse {
   InterfaceSessionHeartbeatResponse({@UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, required this.status, this.error, @UuidValueConverter() required this.interfaceSessionId, this.lastSeenAt, final  String? $type}): $type = $type ?? 'interface_session_heartbeat';
  factory InterfaceSessionHeartbeatResponse.fromJson(Map<String, dynamic> json) => _$InterfaceSessionHeartbeatResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
 final  String status;
 final  String? error;
@UuidValueConverter() final  UuidValue interfaceSessionId;
 final  String? lastSeenAt;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSessionHeartbeatResponseCopyWith<InterfaceSessionHeartbeatResponse> get copyWith => _$InterfaceSessionHeartbeatResponseCopyWithImpl<InterfaceSessionHeartbeatResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSessionHeartbeatResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSessionHeartbeatResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.interfaceSessionId, interfaceSessionId) || other.interfaceSessionId == interfaceSessionId)&&(identical(other.lastSeenAt, lastSeenAt) || other.lastSeenAt == lastSeenAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,nodeId,status,error,interfaceSessionId,lastSeenAt);

@override
String toString() {
  return 'NetworkNodeOperationResponse.interfaceSessionHeartbeat(actorId: $actorId, nodeId: $nodeId, status: $status, error: $error, interfaceSessionId: $interfaceSessionId, lastSeenAt: $lastSeenAt)';
}


}

/// @nodoc
abstract mixin class $InterfaceSessionHeartbeatResponseCopyWith<$Res> implements $NetworkNodeOperationResponseCopyWith<$Res> {
  factory $InterfaceSessionHeartbeatResponseCopyWith(InterfaceSessionHeartbeatResponse value, $Res Function(InterfaceSessionHeartbeatResponse) _then) = _$InterfaceSessionHeartbeatResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId, String status, String? error,@UuidValueConverter() UuidValue interfaceSessionId, String? lastSeenAt
});




}
/// @nodoc
class _$InterfaceSessionHeartbeatResponseCopyWithImpl<$Res>
    implements $InterfaceSessionHeartbeatResponseCopyWith<$Res> {
  _$InterfaceSessionHeartbeatResponseCopyWithImpl(this._self, this._then);

  final InterfaceSessionHeartbeatResponse _self;
  final $Res Function(InterfaceSessionHeartbeatResponse) _then;

/// Create a copy of NetworkNodeOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? nodeId = freezed,Object? status = null,Object? error = freezed,Object? interfaceSessionId = null,Object? lastSeenAt = freezed,}) {
  return _then(InterfaceSessionHeartbeatResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,interfaceSessionId: null == interfaceSessionId ? _self.interfaceSessionId : interfaceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,lastSeenAt: freezed == lastSeenAt ? _self.lastSeenAt : lastSeenAt // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$NodeEnvironmentProvisioningReceipt {

 String get status; String? get error;@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue? get nodeId;@UuidValueConverter() UuidValue? get environmentId;@UuidValueConverter() UuidValue? get environmentConfigId; String? get environmentConfigTitle; String? get environmentTitle; String? get environmentEndpoint; String? get ocgHash; List<String> get opgHashes; String? get runtimeArtifactRefsJson; String? get serviceApiProviderRefsJson;@UuidValueConverter() UuidValue? get processId;@UuidValueConverter() UuidValue? get threadId;@UuidValueConverter() UuidValue? get branchId; String? get outerWrapperKind; String? get environmentHandle; String? get workspaceRoot; String? get workspaceTomlPath; String? get workspaceId; String? get workspacePackageId; String? get workspaceBuildInvocationId; String? get workspaceBuildReceiptPath; String? get workspaceBuildLatestPath; String? get workspaceTargetLatestPath; String? get workspaceTargetRef; Map<String, dynamic>? get readinessReceipt; Map<String, dynamic>? get networkNodeEnvironmentReceipt;
/// Create a copy of NodeEnvironmentProvisioningReceipt
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NodeEnvironmentProvisioningReceiptCopyWith<NodeEnvironmentProvisioningReceipt> get copyWith => _$NodeEnvironmentProvisioningReceiptCopyWithImpl<NodeEnvironmentProvisioningReceipt>(this as NodeEnvironmentProvisioningReceipt, _$identity);

  /// Serializes this NodeEnvironmentProvisioningReceipt to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NodeEnvironmentProvisioningReceipt&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentConfigId, environmentConfigId) || other.environmentConfigId == environmentConfigId)&&(identical(other.environmentConfigTitle, environmentConfigTitle) || other.environmentConfigTitle == environmentConfigTitle)&&(identical(other.environmentTitle, environmentTitle) || other.environmentTitle == environmentTitle)&&(identical(other.environmentEndpoint, environmentEndpoint) || other.environmentEndpoint == environmentEndpoint)&&(identical(other.ocgHash, ocgHash) || other.ocgHash == ocgHash)&&const DeepCollectionEquality().equals(other.opgHashes, opgHashes)&&(identical(other.runtimeArtifactRefsJson, runtimeArtifactRefsJson) || other.runtimeArtifactRefsJson == runtimeArtifactRefsJson)&&(identical(other.serviceApiProviderRefsJson, serviceApiProviderRefsJson) || other.serviceApiProviderRefsJson == serviceApiProviderRefsJson)&&(identical(other.processId, processId) || other.processId == processId)&&(identical(other.threadId, threadId) || other.threadId == threadId)&&(identical(other.branchId, branchId) || other.branchId == branchId)&&(identical(other.outerWrapperKind, outerWrapperKind) || other.outerWrapperKind == outerWrapperKind)&&(identical(other.environmentHandle, environmentHandle) || other.environmentHandle == environmentHandle)&&(identical(other.workspaceRoot, workspaceRoot) || other.workspaceRoot == workspaceRoot)&&(identical(other.workspaceTomlPath, workspaceTomlPath) || other.workspaceTomlPath == workspaceTomlPath)&&(identical(other.workspaceId, workspaceId) || other.workspaceId == workspaceId)&&(identical(other.workspacePackageId, workspacePackageId) || other.workspacePackageId == workspacePackageId)&&(identical(other.workspaceBuildInvocationId, workspaceBuildInvocationId) || other.workspaceBuildInvocationId == workspaceBuildInvocationId)&&(identical(other.workspaceBuildReceiptPath, workspaceBuildReceiptPath) || other.workspaceBuildReceiptPath == workspaceBuildReceiptPath)&&(identical(other.workspaceBuildLatestPath, workspaceBuildLatestPath) || other.workspaceBuildLatestPath == workspaceBuildLatestPath)&&(identical(other.workspaceTargetLatestPath, workspaceTargetLatestPath) || other.workspaceTargetLatestPath == workspaceTargetLatestPath)&&(identical(other.workspaceTargetRef, workspaceTargetRef) || other.workspaceTargetRef == workspaceTargetRef)&&const DeepCollectionEquality().equals(other.readinessReceipt, readinessReceipt)&&const DeepCollectionEquality().equals(other.networkNodeEnvironmentReceipt, networkNodeEnvironmentReceipt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,status,error,actorId,nodeId,environmentId,environmentConfigId,environmentConfigTitle,environmentTitle,environmentEndpoint,ocgHash,const DeepCollectionEquality().hash(opgHashes),runtimeArtifactRefsJson,serviceApiProviderRefsJson,processId,threadId,branchId,outerWrapperKind,environmentHandle,workspaceRoot,workspaceTomlPath,workspaceId,workspacePackageId,workspaceBuildInvocationId,workspaceBuildReceiptPath,workspaceBuildLatestPath,workspaceTargetLatestPath,workspaceTargetRef,const DeepCollectionEquality().hash(readinessReceipt),const DeepCollectionEquality().hash(networkNodeEnvironmentReceipt)]);

@override
String toString() {
  return 'NodeEnvironmentProvisioningReceipt(status: $status, error: $error, actorId: $actorId, nodeId: $nodeId, environmentId: $environmentId, environmentConfigId: $environmentConfigId, environmentConfigTitle: $environmentConfigTitle, environmentTitle: $environmentTitle, environmentEndpoint: $environmentEndpoint, ocgHash: $ocgHash, opgHashes: $opgHashes, runtimeArtifactRefsJson: $runtimeArtifactRefsJson, serviceApiProviderRefsJson: $serviceApiProviderRefsJson, processId: $processId, threadId: $threadId, branchId: $branchId, outerWrapperKind: $outerWrapperKind, environmentHandle: $environmentHandle, workspaceRoot: $workspaceRoot, workspaceTomlPath: $workspaceTomlPath, workspaceId: $workspaceId, workspacePackageId: $workspacePackageId, workspaceBuildInvocationId: $workspaceBuildInvocationId, workspaceBuildReceiptPath: $workspaceBuildReceiptPath, workspaceBuildLatestPath: $workspaceBuildLatestPath, workspaceTargetLatestPath: $workspaceTargetLatestPath, workspaceTargetRef: $workspaceTargetRef, readinessReceipt: $readinessReceipt, networkNodeEnvironmentReceipt: $networkNodeEnvironmentReceipt)';
}


}

/// @nodoc
abstract mixin class $NodeEnvironmentProvisioningReceiptCopyWith<$Res>  {
  factory $NodeEnvironmentProvisioningReceiptCopyWith(NodeEnvironmentProvisioningReceipt value, $Res Function(NodeEnvironmentProvisioningReceipt) _then) = _$NodeEnvironmentProvisioningReceiptCopyWithImpl;
@useResult
$Res call({
 String status, String? error,@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId,@UuidValueConverter() UuidValue? environmentId,@UuidValueConverter() UuidValue? environmentConfigId, String? environmentConfigTitle, String? environmentTitle, String? environmentEndpoint, String? ocgHash, List<String> opgHashes, String? runtimeArtifactRefsJson, String? serviceApiProviderRefsJson,@UuidValueConverter() UuidValue? processId,@UuidValueConverter() UuidValue? threadId,@UuidValueConverter() UuidValue? branchId, String? outerWrapperKind, String? environmentHandle, String? workspaceRoot, String? workspaceTomlPath, String? workspaceId, String? workspacePackageId, String? workspaceBuildInvocationId, String? workspaceBuildReceiptPath, String? workspaceBuildLatestPath, String? workspaceTargetLatestPath, String? workspaceTargetRef, Map<String, dynamic>? readinessReceipt, Map<String, dynamic>? networkNodeEnvironmentReceipt
});




}
/// @nodoc
class _$NodeEnvironmentProvisioningReceiptCopyWithImpl<$Res>
    implements $NodeEnvironmentProvisioningReceiptCopyWith<$Res> {
  _$NodeEnvironmentProvisioningReceiptCopyWithImpl(this._self, this._then);

  final NodeEnvironmentProvisioningReceipt _self;
  final $Res Function(NodeEnvironmentProvisioningReceipt) _then;

/// Create a copy of NodeEnvironmentProvisioningReceipt
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? status = null,Object? error = freezed,Object? actorId = freezed,Object? nodeId = freezed,Object? environmentId = freezed,Object? environmentConfigId = freezed,Object? environmentConfigTitle = freezed,Object? environmentTitle = freezed,Object? environmentEndpoint = freezed,Object? ocgHash = freezed,Object? opgHashes = null,Object? runtimeArtifactRefsJson = freezed,Object? serviceApiProviderRefsJson = freezed,Object? processId = freezed,Object? threadId = freezed,Object? branchId = freezed,Object? outerWrapperKind = freezed,Object? environmentHandle = freezed,Object? workspaceRoot = freezed,Object? workspaceTomlPath = freezed,Object? workspaceId = freezed,Object? workspacePackageId = freezed,Object? workspaceBuildInvocationId = freezed,Object? workspaceBuildReceiptPath = freezed,Object? workspaceBuildLatestPath = freezed,Object? workspaceTargetLatestPath = freezed,Object? workspaceTargetRef = freezed,Object? readinessReceipt = freezed,Object? networkNodeEnvironmentReceipt = freezed,}) {
  return _then(_self.copyWith(
status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentId: freezed == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentConfigId: freezed == environmentConfigId ? _self.environmentConfigId : environmentConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentConfigTitle: freezed == environmentConfigTitle ? _self.environmentConfigTitle : environmentConfigTitle // ignore: cast_nullable_to_non_nullable
as String?,environmentTitle: freezed == environmentTitle ? _self.environmentTitle : environmentTitle // ignore: cast_nullable_to_non_nullable
as String?,environmentEndpoint: freezed == environmentEndpoint ? _self.environmentEndpoint : environmentEndpoint // ignore: cast_nullable_to_non_nullable
as String?,ocgHash: freezed == ocgHash ? _self.ocgHash : ocgHash // ignore: cast_nullable_to_non_nullable
as String?,opgHashes: null == opgHashes ? _self.opgHashes : opgHashes // ignore: cast_nullable_to_non_nullable
as List<String>,runtimeArtifactRefsJson: freezed == runtimeArtifactRefsJson ? _self.runtimeArtifactRefsJson : runtimeArtifactRefsJson // ignore: cast_nullable_to_non_nullable
as String?,serviceApiProviderRefsJson: freezed == serviceApiProviderRefsJson ? _self.serviceApiProviderRefsJson : serviceApiProviderRefsJson // ignore: cast_nullable_to_non_nullable
as String?,processId: freezed == processId ? _self.processId : processId // ignore: cast_nullable_to_non_nullable
as UuidValue?,threadId: freezed == threadId ? _self.threadId : threadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,branchId: freezed == branchId ? _self.branchId : branchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,outerWrapperKind: freezed == outerWrapperKind ? _self.outerWrapperKind : outerWrapperKind // ignore: cast_nullable_to_non_nullable
as String?,environmentHandle: freezed == environmentHandle ? _self.environmentHandle : environmentHandle // ignore: cast_nullable_to_non_nullable
as String?,workspaceRoot: freezed == workspaceRoot ? _self.workspaceRoot : workspaceRoot // ignore: cast_nullable_to_non_nullable
as String?,workspaceTomlPath: freezed == workspaceTomlPath ? _self.workspaceTomlPath : workspaceTomlPath // ignore: cast_nullable_to_non_nullable
as String?,workspaceId: freezed == workspaceId ? _self.workspaceId : workspaceId // ignore: cast_nullable_to_non_nullable
as String?,workspacePackageId: freezed == workspacePackageId ? _self.workspacePackageId : workspacePackageId // ignore: cast_nullable_to_non_nullable
as String?,workspaceBuildInvocationId: freezed == workspaceBuildInvocationId ? _self.workspaceBuildInvocationId : workspaceBuildInvocationId // ignore: cast_nullable_to_non_nullable
as String?,workspaceBuildReceiptPath: freezed == workspaceBuildReceiptPath ? _self.workspaceBuildReceiptPath : workspaceBuildReceiptPath // ignore: cast_nullable_to_non_nullable
as String?,workspaceBuildLatestPath: freezed == workspaceBuildLatestPath ? _self.workspaceBuildLatestPath : workspaceBuildLatestPath // ignore: cast_nullable_to_non_nullable
as String?,workspaceTargetLatestPath: freezed == workspaceTargetLatestPath ? _self.workspaceTargetLatestPath : workspaceTargetLatestPath // ignore: cast_nullable_to_non_nullable
as String?,workspaceTargetRef: freezed == workspaceTargetRef ? _self.workspaceTargetRef : workspaceTargetRef // ignore: cast_nullable_to_non_nullable
as String?,readinessReceipt: freezed == readinessReceipt ? _self.readinessReceipt : readinessReceipt // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>?,networkNodeEnvironmentReceipt: freezed == networkNodeEnvironmentReceipt ? _self.networkNodeEnvironmentReceipt : networkNodeEnvironmentReceipt // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>?,
  ));
}

}


/// Adds pattern-matching-related methods to [NodeEnvironmentProvisioningReceipt].
extension NodeEnvironmentProvisioningReceiptPatterns on NodeEnvironmentProvisioningReceipt {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NodeEnvironmentProvisioningReceipt value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NodeEnvironmentProvisioningReceipt() when def != null:
return def(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NodeEnvironmentProvisioningReceipt value)  def,}){
final _that = this;
switch (_that) {
case _NodeEnvironmentProvisioningReceipt():
return def(_that);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NodeEnvironmentProvisioningReceipt value)?  def,}){
final _that = this;
switch (_that) {
case _NodeEnvironmentProvisioningReceipt() when def != null:
return def(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String status,  String? error, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue? environmentConfigId,  String? environmentConfigTitle,  String? environmentTitle,  String? environmentEndpoint,  String? ocgHash,  List<String> opgHashes,  String? runtimeArtifactRefsJson,  String? serviceApiProviderRefsJson, @UuidValueConverter()  UuidValue? processId, @UuidValueConverter()  UuidValue? threadId, @UuidValueConverter()  UuidValue? branchId,  String? outerWrapperKind,  String? environmentHandle,  String? workspaceRoot,  String? workspaceTomlPath,  String? workspaceId,  String? workspacePackageId,  String? workspaceBuildInvocationId,  String? workspaceBuildReceiptPath,  String? workspaceBuildLatestPath,  String? workspaceTargetLatestPath,  String? workspaceTargetRef,  Map<String, dynamic>? readinessReceipt,  Map<String, dynamic>? networkNodeEnvironmentReceipt)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NodeEnvironmentProvisioningReceipt() when def != null:
return def(_that.status,_that.error,_that.actorId,_that.nodeId,_that.environmentId,_that.environmentConfigId,_that.environmentConfigTitle,_that.environmentTitle,_that.environmentEndpoint,_that.ocgHash,_that.opgHashes,_that.runtimeArtifactRefsJson,_that.serviceApiProviderRefsJson,_that.processId,_that.threadId,_that.branchId,_that.outerWrapperKind,_that.environmentHandle,_that.workspaceRoot,_that.workspaceTomlPath,_that.workspaceId,_that.workspacePackageId,_that.workspaceBuildInvocationId,_that.workspaceBuildReceiptPath,_that.workspaceBuildLatestPath,_that.workspaceTargetLatestPath,_that.workspaceTargetRef,_that.readinessReceipt,_that.networkNodeEnvironmentReceipt);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String status,  String? error, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue? environmentConfigId,  String? environmentConfigTitle,  String? environmentTitle,  String? environmentEndpoint,  String? ocgHash,  List<String> opgHashes,  String? runtimeArtifactRefsJson,  String? serviceApiProviderRefsJson, @UuidValueConverter()  UuidValue? processId, @UuidValueConverter()  UuidValue? threadId, @UuidValueConverter()  UuidValue? branchId,  String? outerWrapperKind,  String? environmentHandle,  String? workspaceRoot,  String? workspaceTomlPath,  String? workspaceId,  String? workspacePackageId,  String? workspaceBuildInvocationId,  String? workspaceBuildReceiptPath,  String? workspaceBuildLatestPath,  String? workspaceTargetLatestPath,  String? workspaceTargetRef,  Map<String, dynamic>? readinessReceipt,  Map<String, dynamic>? networkNodeEnvironmentReceipt)  def,}) {final _that = this;
switch (_that) {
case _NodeEnvironmentProvisioningReceipt():
return def(_that.status,_that.error,_that.actorId,_that.nodeId,_that.environmentId,_that.environmentConfigId,_that.environmentConfigTitle,_that.environmentTitle,_that.environmentEndpoint,_that.ocgHash,_that.opgHashes,_that.runtimeArtifactRefsJson,_that.serviceApiProviderRefsJson,_that.processId,_that.threadId,_that.branchId,_that.outerWrapperKind,_that.environmentHandle,_that.workspaceRoot,_that.workspaceTomlPath,_that.workspaceId,_that.workspacePackageId,_that.workspaceBuildInvocationId,_that.workspaceBuildReceiptPath,_that.workspaceBuildLatestPath,_that.workspaceTargetLatestPath,_that.workspaceTargetRef,_that.readinessReceipt,_that.networkNodeEnvironmentReceipt);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String status,  String? error, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue? environmentConfigId,  String? environmentConfigTitle,  String? environmentTitle,  String? environmentEndpoint,  String? ocgHash,  List<String> opgHashes,  String? runtimeArtifactRefsJson,  String? serviceApiProviderRefsJson, @UuidValueConverter()  UuidValue? processId, @UuidValueConverter()  UuidValue? threadId, @UuidValueConverter()  UuidValue? branchId,  String? outerWrapperKind,  String? environmentHandle,  String? workspaceRoot,  String? workspaceTomlPath,  String? workspaceId,  String? workspacePackageId,  String? workspaceBuildInvocationId,  String? workspaceBuildReceiptPath,  String? workspaceBuildLatestPath,  String? workspaceTargetLatestPath,  String? workspaceTargetRef,  Map<String, dynamic>? readinessReceipt,  Map<String, dynamic>? networkNodeEnvironmentReceipt)?  def,}) {final _that = this;
switch (_that) {
case _NodeEnvironmentProvisioningReceipt() when def != null:
return def(_that.status,_that.error,_that.actorId,_that.nodeId,_that.environmentId,_that.environmentConfigId,_that.environmentConfigTitle,_that.environmentTitle,_that.environmentEndpoint,_that.ocgHash,_that.opgHashes,_that.runtimeArtifactRefsJson,_that.serviceApiProviderRefsJson,_that.processId,_that.threadId,_that.branchId,_that.outerWrapperKind,_that.environmentHandle,_that.workspaceRoot,_that.workspaceTomlPath,_that.workspaceId,_that.workspacePackageId,_that.workspaceBuildInvocationId,_that.workspaceBuildReceiptPath,_that.workspaceBuildLatestPath,_that.workspaceTargetLatestPath,_that.workspaceTargetRef,_that.readinessReceipt,_that.networkNodeEnvironmentReceipt);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NodeEnvironmentProvisioningReceipt implements NodeEnvironmentProvisioningReceipt {
   _NodeEnvironmentProvisioningReceipt({required this.status, this.error, @UuidValueConverter() this.actorId, @UuidValueConverter() this.nodeId, @UuidValueConverter() this.environmentId, @UuidValueConverter() this.environmentConfigId, this.environmentConfigTitle, this.environmentTitle, this.environmentEndpoint, this.ocgHash, final  List<String> opgHashes = const [], this.runtimeArtifactRefsJson, this.serviceApiProviderRefsJson, @UuidValueConverter() this.processId, @UuidValueConverter() this.threadId, @UuidValueConverter() this.branchId, this.outerWrapperKind, this.environmentHandle, this.workspaceRoot, this.workspaceTomlPath, this.workspaceId, this.workspacePackageId, this.workspaceBuildInvocationId, this.workspaceBuildReceiptPath, this.workspaceBuildLatestPath, this.workspaceTargetLatestPath, this.workspaceTargetRef, final  Map<String, dynamic>? readinessReceipt, final  Map<String, dynamic>? networkNodeEnvironmentReceipt}): _opgHashes = opgHashes,_readinessReceipt = readinessReceipt,_networkNodeEnvironmentReceipt = networkNodeEnvironmentReceipt;
  factory _NodeEnvironmentProvisioningReceipt.fromJson(Map<String, dynamic> json) => _$NodeEnvironmentProvisioningReceiptFromJson(json);

@override final  String status;
@override final  String? error;
@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? nodeId;
@override@UuidValueConverter() final  UuidValue? environmentId;
@override@UuidValueConverter() final  UuidValue? environmentConfigId;
@override final  String? environmentConfigTitle;
@override final  String? environmentTitle;
@override final  String? environmentEndpoint;
@override final  String? ocgHash;
 final  List<String> _opgHashes;
@override@JsonKey() List<String> get opgHashes {
  if (_opgHashes is EqualUnmodifiableListView) return _opgHashes;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_opgHashes);
}

@override final  String? runtimeArtifactRefsJson;
@override final  String? serviceApiProviderRefsJson;
@override@UuidValueConverter() final  UuidValue? processId;
@override@UuidValueConverter() final  UuidValue? threadId;
@override@UuidValueConverter() final  UuidValue? branchId;
@override final  String? outerWrapperKind;
@override final  String? environmentHandle;
@override final  String? workspaceRoot;
@override final  String? workspaceTomlPath;
@override final  String? workspaceId;
@override final  String? workspacePackageId;
@override final  String? workspaceBuildInvocationId;
@override final  String? workspaceBuildReceiptPath;
@override final  String? workspaceBuildLatestPath;
@override final  String? workspaceTargetLatestPath;
@override final  String? workspaceTargetRef;
 final  Map<String, dynamic>? _readinessReceipt;
@override Map<String, dynamic>? get readinessReceipt {
  final value = _readinessReceipt;
  if (value == null) return null;
  if (_readinessReceipt is EqualUnmodifiableMapView) return _readinessReceipt;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(value);
}

 final  Map<String, dynamic>? _networkNodeEnvironmentReceipt;
@override Map<String, dynamic>? get networkNodeEnvironmentReceipt {
  final value = _networkNodeEnvironmentReceipt;
  if (value == null) return null;
  if (_networkNodeEnvironmentReceipt is EqualUnmodifiableMapView) return _networkNodeEnvironmentReceipt;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(value);
}


/// Create a copy of NodeEnvironmentProvisioningReceipt
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NodeEnvironmentProvisioningReceiptCopyWith<_NodeEnvironmentProvisioningReceipt> get copyWith => __$NodeEnvironmentProvisioningReceiptCopyWithImpl<_NodeEnvironmentProvisioningReceipt>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NodeEnvironmentProvisioningReceiptToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NodeEnvironmentProvisioningReceipt&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentConfigId, environmentConfigId) || other.environmentConfigId == environmentConfigId)&&(identical(other.environmentConfigTitle, environmentConfigTitle) || other.environmentConfigTitle == environmentConfigTitle)&&(identical(other.environmentTitle, environmentTitle) || other.environmentTitle == environmentTitle)&&(identical(other.environmentEndpoint, environmentEndpoint) || other.environmentEndpoint == environmentEndpoint)&&(identical(other.ocgHash, ocgHash) || other.ocgHash == ocgHash)&&const DeepCollectionEquality().equals(other._opgHashes, _opgHashes)&&(identical(other.runtimeArtifactRefsJson, runtimeArtifactRefsJson) || other.runtimeArtifactRefsJson == runtimeArtifactRefsJson)&&(identical(other.serviceApiProviderRefsJson, serviceApiProviderRefsJson) || other.serviceApiProviderRefsJson == serviceApiProviderRefsJson)&&(identical(other.processId, processId) || other.processId == processId)&&(identical(other.threadId, threadId) || other.threadId == threadId)&&(identical(other.branchId, branchId) || other.branchId == branchId)&&(identical(other.outerWrapperKind, outerWrapperKind) || other.outerWrapperKind == outerWrapperKind)&&(identical(other.environmentHandle, environmentHandle) || other.environmentHandle == environmentHandle)&&(identical(other.workspaceRoot, workspaceRoot) || other.workspaceRoot == workspaceRoot)&&(identical(other.workspaceTomlPath, workspaceTomlPath) || other.workspaceTomlPath == workspaceTomlPath)&&(identical(other.workspaceId, workspaceId) || other.workspaceId == workspaceId)&&(identical(other.workspacePackageId, workspacePackageId) || other.workspacePackageId == workspacePackageId)&&(identical(other.workspaceBuildInvocationId, workspaceBuildInvocationId) || other.workspaceBuildInvocationId == workspaceBuildInvocationId)&&(identical(other.workspaceBuildReceiptPath, workspaceBuildReceiptPath) || other.workspaceBuildReceiptPath == workspaceBuildReceiptPath)&&(identical(other.workspaceBuildLatestPath, workspaceBuildLatestPath) || other.workspaceBuildLatestPath == workspaceBuildLatestPath)&&(identical(other.workspaceTargetLatestPath, workspaceTargetLatestPath) || other.workspaceTargetLatestPath == workspaceTargetLatestPath)&&(identical(other.workspaceTargetRef, workspaceTargetRef) || other.workspaceTargetRef == workspaceTargetRef)&&const DeepCollectionEquality().equals(other._readinessReceipt, _readinessReceipt)&&const DeepCollectionEquality().equals(other._networkNodeEnvironmentReceipt, _networkNodeEnvironmentReceipt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,status,error,actorId,nodeId,environmentId,environmentConfigId,environmentConfigTitle,environmentTitle,environmentEndpoint,ocgHash,const DeepCollectionEquality().hash(_opgHashes),runtimeArtifactRefsJson,serviceApiProviderRefsJson,processId,threadId,branchId,outerWrapperKind,environmentHandle,workspaceRoot,workspaceTomlPath,workspaceId,workspacePackageId,workspaceBuildInvocationId,workspaceBuildReceiptPath,workspaceBuildLatestPath,workspaceTargetLatestPath,workspaceTargetRef,const DeepCollectionEquality().hash(_readinessReceipt),const DeepCollectionEquality().hash(_networkNodeEnvironmentReceipt)]);

@override
String toString() {
  return 'NodeEnvironmentProvisioningReceipt.def(status: $status, error: $error, actorId: $actorId, nodeId: $nodeId, environmentId: $environmentId, environmentConfigId: $environmentConfigId, environmentConfigTitle: $environmentConfigTitle, environmentTitle: $environmentTitle, environmentEndpoint: $environmentEndpoint, ocgHash: $ocgHash, opgHashes: $opgHashes, runtimeArtifactRefsJson: $runtimeArtifactRefsJson, serviceApiProviderRefsJson: $serviceApiProviderRefsJson, processId: $processId, threadId: $threadId, branchId: $branchId, outerWrapperKind: $outerWrapperKind, environmentHandle: $environmentHandle, workspaceRoot: $workspaceRoot, workspaceTomlPath: $workspaceTomlPath, workspaceId: $workspaceId, workspacePackageId: $workspacePackageId, workspaceBuildInvocationId: $workspaceBuildInvocationId, workspaceBuildReceiptPath: $workspaceBuildReceiptPath, workspaceBuildLatestPath: $workspaceBuildLatestPath, workspaceTargetLatestPath: $workspaceTargetLatestPath, workspaceTargetRef: $workspaceTargetRef, readinessReceipt: $readinessReceipt, networkNodeEnvironmentReceipt: $networkNodeEnvironmentReceipt)';
}


}

/// @nodoc
abstract mixin class _$NodeEnvironmentProvisioningReceiptCopyWith<$Res> implements $NodeEnvironmentProvisioningReceiptCopyWith<$Res> {
  factory _$NodeEnvironmentProvisioningReceiptCopyWith(_NodeEnvironmentProvisioningReceipt value, $Res Function(_NodeEnvironmentProvisioningReceipt) _then) = __$NodeEnvironmentProvisioningReceiptCopyWithImpl;
@override @useResult
$Res call({
 String status, String? error,@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? nodeId,@UuidValueConverter() UuidValue? environmentId,@UuidValueConverter() UuidValue? environmentConfigId, String? environmentConfigTitle, String? environmentTitle, String? environmentEndpoint, String? ocgHash, List<String> opgHashes, String? runtimeArtifactRefsJson, String? serviceApiProviderRefsJson,@UuidValueConverter() UuidValue? processId,@UuidValueConverter() UuidValue? threadId,@UuidValueConverter() UuidValue? branchId, String? outerWrapperKind, String? environmentHandle, String? workspaceRoot, String? workspaceTomlPath, String? workspaceId, String? workspacePackageId, String? workspaceBuildInvocationId, String? workspaceBuildReceiptPath, String? workspaceBuildLatestPath, String? workspaceTargetLatestPath, String? workspaceTargetRef, Map<String, dynamic>? readinessReceipt, Map<String, dynamic>? networkNodeEnvironmentReceipt
});




}
/// @nodoc
class __$NodeEnvironmentProvisioningReceiptCopyWithImpl<$Res>
    implements _$NodeEnvironmentProvisioningReceiptCopyWith<$Res> {
  __$NodeEnvironmentProvisioningReceiptCopyWithImpl(this._self, this._then);

  final _NodeEnvironmentProvisioningReceipt _self;
  final $Res Function(_NodeEnvironmentProvisioningReceipt) _then;

/// Create a copy of NodeEnvironmentProvisioningReceipt
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? status = null,Object? error = freezed,Object? actorId = freezed,Object? nodeId = freezed,Object? environmentId = freezed,Object? environmentConfigId = freezed,Object? environmentConfigTitle = freezed,Object? environmentTitle = freezed,Object? environmentEndpoint = freezed,Object? ocgHash = freezed,Object? opgHashes = null,Object? runtimeArtifactRefsJson = freezed,Object? serviceApiProviderRefsJson = freezed,Object? processId = freezed,Object? threadId = freezed,Object? branchId = freezed,Object? outerWrapperKind = freezed,Object? environmentHandle = freezed,Object? workspaceRoot = freezed,Object? workspaceTomlPath = freezed,Object? workspaceId = freezed,Object? workspacePackageId = freezed,Object? workspaceBuildInvocationId = freezed,Object? workspaceBuildReceiptPath = freezed,Object? workspaceBuildLatestPath = freezed,Object? workspaceTargetLatestPath = freezed,Object? workspaceTargetRef = freezed,Object? readinessReceipt = freezed,Object? networkNodeEnvironmentReceipt = freezed,}) {
  return _then(_NodeEnvironmentProvisioningReceipt(
status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentId: freezed == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentConfigId: freezed == environmentConfigId ? _self.environmentConfigId : environmentConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentConfigTitle: freezed == environmentConfigTitle ? _self.environmentConfigTitle : environmentConfigTitle // ignore: cast_nullable_to_non_nullable
as String?,environmentTitle: freezed == environmentTitle ? _self.environmentTitle : environmentTitle // ignore: cast_nullable_to_non_nullable
as String?,environmentEndpoint: freezed == environmentEndpoint ? _self.environmentEndpoint : environmentEndpoint // ignore: cast_nullable_to_non_nullable
as String?,ocgHash: freezed == ocgHash ? _self.ocgHash : ocgHash // ignore: cast_nullable_to_non_nullable
as String?,opgHashes: null == opgHashes ? _self._opgHashes : opgHashes // ignore: cast_nullable_to_non_nullable
as List<String>,runtimeArtifactRefsJson: freezed == runtimeArtifactRefsJson ? _self.runtimeArtifactRefsJson : runtimeArtifactRefsJson // ignore: cast_nullable_to_non_nullable
as String?,serviceApiProviderRefsJson: freezed == serviceApiProviderRefsJson ? _self.serviceApiProviderRefsJson : serviceApiProviderRefsJson // ignore: cast_nullable_to_non_nullable
as String?,processId: freezed == processId ? _self.processId : processId // ignore: cast_nullable_to_non_nullable
as UuidValue?,threadId: freezed == threadId ? _self.threadId : threadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,branchId: freezed == branchId ? _self.branchId : branchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,outerWrapperKind: freezed == outerWrapperKind ? _self.outerWrapperKind : outerWrapperKind // ignore: cast_nullable_to_non_nullable
as String?,environmentHandle: freezed == environmentHandle ? _self.environmentHandle : environmentHandle // ignore: cast_nullable_to_non_nullable
as String?,workspaceRoot: freezed == workspaceRoot ? _self.workspaceRoot : workspaceRoot // ignore: cast_nullable_to_non_nullable
as String?,workspaceTomlPath: freezed == workspaceTomlPath ? _self.workspaceTomlPath : workspaceTomlPath // ignore: cast_nullable_to_non_nullable
as String?,workspaceId: freezed == workspaceId ? _self.workspaceId : workspaceId // ignore: cast_nullable_to_non_nullable
as String?,workspacePackageId: freezed == workspacePackageId ? _self.workspacePackageId : workspacePackageId // ignore: cast_nullable_to_non_nullable
as String?,workspaceBuildInvocationId: freezed == workspaceBuildInvocationId ? _self.workspaceBuildInvocationId : workspaceBuildInvocationId // ignore: cast_nullable_to_non_nullable
as String?,workspaceBuildReceiptPath: freezed == workspaceBuildReceiptPath ? _self.workspaceBuildReceiptPath : workspaceBuildReceiptPath // ignore: cast_nullable_to_non_nullable
as String?,workspaceBuildLatestPath: freezed == workspaceBuildLatestPath ? _self.workspaceBuildLatestPath : workspaceBuildLatestPath // ignore: cast_nullable_to_non_nullable
as String?,workspaceTargetLatestPath: freezed == workspaceTargetLatestPath ? _self.workspaceTargetLatestPath : workspaceTargetLatestPath // ignore: cast_nullable_to_non_nullable
as String?,workspaceTargetRef: freezed == workspaceTargetRef ? _self.workspaceTargetRef : workspaceTargetRef // ignore: cast_nullable_to_non_nullable
as String?,readinessReceipt: freezed == readinessReceipt ? _self._readinessReceipt : readinessReceipt // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>?,networkNodeEnvironmentReceipt: freezed == networkNodeEnvironmentReceipt ? _self._networkNodeEnvironmentReceipt : networkNodeEnvironmentReceipt // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>?,
  ));
}


}


/// @nodoc
mixin _$EnvironmentConfigDescriptor {

@UuidValueConverter() UuidValue get environmentConfigId; String? get title; String? get canonicalLanguage; String? get ocgHash; List<String> get opgHashes; String? get outerWrapperKind; String? get environmentHandle; String? get workspaceTargetRef;
/// Create a copy of EnvironmentConfigDescriptor
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$EnvironmentConfigDescriptorCopyWith<EnvironmentConfigDescriptor> get copyWith => _$EnvironmentConfigDescriptorCopyWithImpl<EnvironmentConfigDescriptor>(this as EnvironmentConfigDescriptor, _$identity);

  /// Serializes this EnvironmentConfigDescriptor to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is EnvironmentConfigDescriptor&&(identical(other.environmentConfigId, environmentConfigId) || other.environmentConfigId == environmentConfigId)&&(identical(other.title, title) || other.title == title)&&(identical(other.canonicalLanguage, canonicalLanguage) || other.canonicalLanguage == canonicalLanguage)&&(identical(other.ocgHash, ocgHash) || other.ocgHash == ocgHash)&&const DeepCollectionEquality().equals(other.opgHashes, opgHashes)&&(identical(other.outerWrapperKind, outerWrapperKind) || other.outerWrapperKind == outerWrapperKind)&&(identical(other.environmentHandle, environmentHandle) || other.environmentHandle == environmentHandle)&&(identical(other.workspaceTargetRef, workspaceTargetRef) || other.workspaceTargetRef == workspaceTargetRef));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,environmentConfigId,title,canonicalLanguage,ocgHash,const DeepCollectionEquality().hash(opgHashes),outerWrapperKind,environmentHandle,workspaceTargetRef);

@override
String toString() {
  return 'EnvironmentConfigDescriptor(environmentConfigId: $environmentConfigId, title: $title, canonicalLanguage: $canonicalLanguage, ocgHash: $ocgHash, opgHashes: $opgHashes, outerWrapperKind: $outerWrapperKind, environmentHandle: $environmentHandle, workspaceTargetRef: $workspaceTargetRef)';
}


}

/// @nodoc
abstract mixin class $EnvironmentConfigDescriptorCopyWith<$Res>  {
  factory $EnvironmentConfigDescriptorCopyWith(EnvironmentConfigDescriptor value, $Res Function(EnvironmentConfigDescriptor) _then) = _$EnvironmentConfigDescriptorCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue environmentConfigId, String? title, String? canonicalLanguage, String? ocgHash, List<String> opgHashes, String? outerWrapperKind, String? environmentHandle, String? workspaceTargetRef
});




}
/// @nodoc
class _$EnvironmentConfigDescriptorCopyWithImpl<$Res>
    implements $EnvironmentConfigDescriptorCopyWith<$Res> {
  _$EnvironmentConfigDescriptorCopyWithImpl(this._self, this._then);

  final EnvironmentConfigDescriptor _self;
  final $Res Function(EnvironmentConfigDescriptor) _then;

/// Create a copy of EnvironmentConfigDescriptor
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? environmentConfigId = null,Object? title = freezed,Object? canonicalLanguage = freezed,Object? ocgHash = freezed,Object? opgHashes = null,Object? outerWrapperKind = freezed,Object? environmentHandle = freezed,Object? workspaceTargetRef = freezed,}) {
  return _then(_self.copyWith(
environmentConfigId: null == environmentConfigId ? _self.environmentConfigId : environmentConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,canonicalLanguage: freezed == canonicalLanguage ? _self.canonicalLanguage : canonicalLanguage // ignore: cast_nullable_to_non_nullable
as String?,ocgHash: freezed == ocgHash ? _self.ocgHash : ocgHash // ignore: cast_nullable_to_non_nullable
as String?,opgHashes: null == opgHashes ? _self.opgHashes : opgHashes // ignore: cast_nullable_to_non_nullable
as List<String>,outerWrapperKind: freezed == outerWrapperKind ? _self.outerWrapperKind : outerWrapperKind // ignore: cast_nullable_to_non_nullable
as String?,environmentHandle: freezed == environmentHandle ? _self.environmentHandle : environmentHandle // ignore: cast_nullable_to_non_nullable
as String?,workspaceTargetRef: freezed == workspaceTargetRef ? _self.workspaceTargetRef : workspaceTargetRef // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [EnvironmentConfigDescriptor].
extension EnvironmentConfigDescriptorPatterns on EnvironmentConfigDescriptor {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _EnvironmentConfigDescriptor value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _EnvironmentConfigDescriptor() when def != null:
return def(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _EnvironmentConfigDescriptor value)  def,}){
final _that = this;
switch (_that) {
case _EnvironmentConfigDescriptor():
return def(_that);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _EnvironmentConfigDescriptor value)?  def,}){
final _that = this;
switch (_that) {
case _EnvironmentConfigDescriptor() when def != null:
return def(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue environmentConfigId,  String? title,  String? canonicalLanguage,  String? ocgHash,  List<String> opgHashes,  String? outerWrapperKind,  String? environmentHandle,  String? workspaceTargetRef)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _EnvironmentConfigDescriptor() when def != null:
return def(_that.environmentConfigId,_that.title,_that.canonicalLanguage,_that.ocgHash,_that.opgHashes,_that.outerWrapperKind,_that.environmentHandle,_that.workspaceTargetRef);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue environmentConfigId,  String? title,  String? canonicalLanguage,  String? ocgHash,  List<String> opgHashes,  String? outerWrapperKind,  String? environmentHandle,  String? workspaceTargetRef)  def,}) {final _that = this;
switch (_that) {
case _EnvironmentConfigDescriptor():
return def(_that.environmentConfigId,_that.title,_that.canonicalLanguage,_that.ocgHash,_that.opgHashes,_that.outerWrapperKind,_that.environmentHandle,_that.workspaceTargetRef);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue environmentConfigId,  String? title,  String? canonicalLanguage,  String? ocgHash,  List<String> opgHashes,  String? outerWrapperKind,  String? environmentHandle,  String? workspaceTargetRef)?  def,}) {final _that = this;
switch (_that) {
case _EnvironmentConfigDescriptor() when def != null:
return def(_that.environmentConfigId,_that.title,_that.canonicalLanguage,_that.ocgHash,_that.opgHashes,_that.outerWrapperKind,_that.environmentHandle,_that.workspaceTargetRef);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _EnvironmentConfigDescriptor implements EnvironmentConfigDescriptor {
   _EnvironmentConfigDescriptor({@UuidValueConverter() required this.environmentConfigId, this.title, this.canonicalLanguage, this.ocgHash, final  List<String> opgHashes = const [], this.outerWrapperKind, this.environmentHandle, this.workspaceTargetRef}): _opgHashes = opgHashes;
  factory _EnvironmentConfigDescriptor.fromJson(Map<String, dynamic> json) => _$EnvironmentConfigDescriptorFromJson(json);

@override@UuidValueConverter() final  UuidValue environmentConfigId;
@override final  String? title;
@override final  String? canonicalLanguage;
@override final  String? ocgHash;
 final  List<String> _opgHashes;
@override@JsonKey() List<String> get opgHashes {
  if (_opgHashes is EqualUnmodifiableListView) return _opgHashes;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_opgHashes);
}

@override final  String? outerWrapperKind;
@override final  String? environmentHandle;
@override final  String? workspaceTargetRef;

/// Create a copy of EnvironmentConfigDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$EnvironmentConfigDescriptorCopyWith<_EnvironmentConfigDescriptor> get copyWith => __$EnvironmentConfigDescriptorCopyWithImpl<_EnvironmentConfigDescriptor>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$EnvironmentConfigDescriptorToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _EnvironmentConfigDescriptor&&(identical(other.environmentConfigId, environmentConfigId) || other.environmentConfigId == environmentConfigId)&&(identical(other.title, title) || other.title == title)&&(identical(other.canonicalLanguage, canonicalLanguage) || other.canonicalLanguage == canonicalLanguage)&&(identical(other.ocgHash, ocgHash) || other.ocgHash == ocgHash)&&const DeepCollectionEquality().equals(other._opgHashes, _opgHashes)&&(identical(other.outerWrapperKind, outerWrapperKind) || other.outerWrapperKind == outerWrapperKind)&&(identical(other.environmentHandle, environmentHandle) || other.environmentHandle == environmentHandle)&&(identical(other.workspaceTargetRef, workspaceTargetRef) || other.workspaceTargetRef == workspaceTargetRef));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,environmentConfigId,title,canonicalLanguage,ocgHash,const DeepCollectionEquality().hash(_opgHashes),outerWrapperKind,environmentHandle,workspaceTargetRef);

@override
String toString() {
  return 'EnvironmentConfigDescriptor.def(environmentConfigId: $environmentConfigId, title: $title, canonicalLanguage: $canonicalLanguage, ocgHash: $ocgHash, opgHashes: $opgHashes, outerWrapperKind: $outerWrapperKind, environmentHandle: $environmentHandle, workspaceTargetRef: $workspaceTargetRef)';
}


}

/// @nodoc
abstract mixin class _$EnvironmentConfigDescriptorCopyWith<$Res> implements $EnvironmentConfigDescriptorCopyWith<$Res> {
  factory _$EnvironmentConfigDescriptorCopyWith(_EnvironmentConfigDescriptor value, $Res Function(_EnvironmentConfigDescriptor) _then) = __$EnvironmentConfigDescriptorCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue environmentConfigId, String? title, String? canonicalLanguage, String? ocgHash, List<String> opgHashes, String? outerWrapperKind, String? environmentHandle, String? workspaceTargetRef
});




}
/// @nodoc
class __$EnvironmentConfigDescriptorCopyWithImpl<$Res>
    implements _$EnvironmentConfigDescriptorCopyWith<$Res> {
  __$EnvironmentConfigDescriptorCopyWithImpl(this._self, this._then);

  final _EnvironmentConfigDescriptor _self;
  final $Res Function(_EnvironmentConfigDescriptor) _then;

/// Create a copy of EnvironmentConfigDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? environmentConfigId = null,Object? title = freezed,Object? canonicalLanguage = freezed,Object? ocgHash = freezed,Object? opgHashes = null,Object? outerWrapperKind = freezed,Object? environmentHandle = freezed,Object? workspaceTargetRef = freezed,}) {
  return _then(_EnvironmentConfigDescriptor(
environmentConfigId: null == environmentConfigId ? _self.environmentConfigId : environmentConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,canonicalLanguage: freezed == canonicalLanguage ? _self.canonicalLanguage : canonicalLanguage // ignore: cast_nullable_to_non_nullable
as String?,ocgHash: freezed == ocgHash ? _self.ocgHash : ocgHash // ignore: cast_nullable_to_non_nullable
as String?,opgHashes: null == opgHashes ? _self._opgHashes : opgHashes // ignore: cast_nullable_to_non_nullable
as List<String>,outerWrapperKind: freezed == outerWrapperKind ? _self.outerWrapperKind : outerWrapperKind // ignore: cast_nullable_to_non_nullable
as String?,environmentHandle: freezed == environmentHandle ? _self.environmentHandle : environmentHandle // ignore: cast_nullable_to_non_nullable
as String?,workspaceTargetRef: freezed == workspaceTargetRef ? _self.workspaceTargetRef : workspaceTargetRef // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$BootEnvironmentDescriptor {

@UuidValueConverter() UuidValue get kernelEnvironmentConfigId;@UuidValueConverter() UuidValue get bootEnvironmentId; String? get kernelEnvironmentConfigTitle; String? get bootEnvironmentTitle;@UuidValueConverter() UuidValue? get processId;@UuidValueConverter() UuidValue? get threadId;@UuidValueConverter() UuidValue? get branchId; List<String> get opgHashes;
/// Create a copy of BootEnvironmentDescriptor
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$BootEnvironmentDescriptorCopyWith<BootEnvironmentDescriptor> get copyWith => _$BootEnvironmentDescriptorCopyWithImpl<BootEnvironmentDescriptor>(this as BootEnvironmentDescriptor, _$identity);

  /// Serializes this BootEnvironmentDescriptor to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is BootEnvironmentDescriptor&&(identical(other.kernelEnvironmentConfigId, kernelEnvironmentConfigId) || other.kernelEnvironmentConfigId == kernelEnvironmentConfigId)&&(identical(other.bootEnvironmentId, bootEnvironmentId) || other.bootEnvironmentId == bootEnvironmentId)&&(identical(other.kernelEnvironmentConfigTitle, kernelEnvironmentConfigTitle) || other.kernelEnvironmentConfigTitle == kernelEnvironmentConfigTitle)&&(identical(other.bootEnvironmentTitle, bootEnvironmentTitle) || other.bootEnvironmentTitle == bootEnvironmentTitle)&&(identical(other.processId, processId) || other.processId == processId)&&(identical(other.threadId, threadId) || other.threadId == threadId)&&(identical(other.branchId, branchId) || other.branchId == branchId)&&const DeepCollectionEquality().equals(other.opgHashes, opgHashes));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,kernelEnvironmentConfigId,bootEnvironmentId,kernelEnvironmentConfigTitle,bootEnvironmentTitle,processId,threadId,branchId,const DeepCollectionEquality().hash(opgHashes));

@override
String toString() {
  return 'BootEnvironmentDescriptor(kernelEnvironmentConfigId: $kernelEnvironmentConfigId, bootEnvironmentId: $bootEnvironmentId, kernelEnvironmentConfigTitle: $kernelEnvironmentConfigTitle, bootEnvironmentTitle: $bootEnvironmentTitle, processId: $processId, threadId: $threadId, branchId: $branchId, opgHashes: $opgHashes)';
}


}

/// @nodoc
abstract mixin class $BootEnvironmentDescriptorCopyWith<$Res>  {
  factory $BootEnvironmentDescriptorCopyWith(BootEnvironmentDescriptor value, $Res Function(BootEnvironmentDescriptor) _then) = _$BootEnvironmentDescriptorCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue kernelEnvironmentConfigId,@UuidValueConverter() UuidValue bootEnvironmentId, String? kernelEnvironmentConfigTitle, String? bootEnvironmentTitle,@UuidValueConverter() UuidValue? processId,@UuidValueConverter() UuidValue? threadId,@UuidValueConverter() UuidValue? branchId, List<String> opgHashes
});




}
/// @nodoc
class _$BootEnvironmentDescriptorCopyWithImpl<$Res>
    implements $BootEnvironmentDescriptorCopyWith<$Res> {
  _$BootEnvironmentDescriptorCopyWithImpl(this._self, this._then);

  final BootEnvironmentDescriptor _self;
  final $Res Function(BootEnvironmentDescriptor) _then;

/// Create a copy of BootEnvironmentDescriptor
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? kernelEnvironmentConfigId = null,Object? bootEnvironmentId = null,Object? kernelEnvironmentConfigTitle = freezed,Object? bootEnvironmentTitle = freezed,Object? processId = freezed,Object? threadId = freezed,Object? branchId = freezed,Object? opgHashes = null,}) {
  return _then(_self.copyWith(
kernelEnvironmentConfigId: null == kernelEnvironmentConfigId ? _self.kernelEnvironmentConfigId : kernelEnvironmentConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,bootEnvironmentId: null == bootEnvironmentId ? _self.bootEnvironmentId : bootEnvironmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,kernelEnvironmentConfigTitle: freezed == kernelEnvironmentConfigTitle ? _self.kernelEnvironmentConfigTitle : kernelEnvironmentConfigTitle // ignore: cast_nullable_to_non_nullable
as String?,bootEnvironmentTitle: freezed == bootEnvironmentTitle ? _self.bootEnvironmentTitle : bootEnvironmentTitle // ignore: cast_nullable_to_non_nullable
as String?,processId: freezed == processId ? _self.processId : processId // ignore: cast_nullable_to_non_nullable
as UuidValue?,threadId: freezed == threadId ? _self.threadId : threadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,branchId: freezed == branchId ? _self.branchId : branchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,opgHashes: null == opgHashes ? _self.opgHashes : opgHashes // ignore: cast_nullable_to_non_nullable
as List<String>,
  ));
}

}


/// Adds pattern-matching-related methods to [BootEnvironmentDescriptor].
extension BootEnvironmentDescriptorPatterns on BootEnvironmentDescriptor {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _BootEnvironmentDescriptor value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _BootEnvironmentDescriptor() when def != null:
return def(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _BootEnvironmentDescriptor value)  def,}){
final _that = this;
switch (_that) {
case _BootEnvironmentDescriptor():
return def(_that);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _BootEnvironmentDescriptor value)?  def,}){
final _that = this;
switch (_that) {
case _BootEnvironmentDescriptor() when def != null:
return def(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue kernelEnvironmentConfigId, @UuidValueConverter()  UuidValue bootEnvironmentId,  String? kernelEnvironmentConfigTitle,  String? bootEnvironmentTitle, @UuidValueConverter()  UuidValue? processId, @UuidValueConverter()  UuidValue? threadId, @UuidValueConverter()  UuidValue? branchId,  List<String> opgHashes)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _BootEnvironmentDescriptor() when def != null:
return def(_that.kernelEnvironmentConfigId,_that.bootEnvironmentId,_that.kernelEnvironmentConfigTitle,_that.bootEnvironmentTitle,_that.processId,_that.threadId,_that.branchId,_that.opgHashes);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue kernelEnvironmentConfigId, @UuidValueConverter()  UuidValue bootEnvironmentId,  String? kernelEnvironmentConfigTitle,  String? bootEnvironmentTitle, @UuidValueConverter()  UuidValue? processId, @UuidValueConverter()  UuidValue? threadId, @UuidValueConverter()  UuidValue? branchId,  List<String> opgHashes)  def,}) {final _that = this;
switch (_that) {
case _BootEnvironmentDescriptor():
return def(_that.kernelEnvironmentConfigId,_that.bootEnvironmentId,_that.kernelEnvironmentConfigTitle,_that.bootEnvironmentTitle,_that.processId,_that.threadId,_that.branchId,_that.opgHashes);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue kernelEnvironmentConfigId, @UuidValueConverter()  UuidValue bootEnvironmentId,  String? kernelEnvironmentConfigTitle,  String? bootEnvironmentTitle, @UuidValueConverter()  UuidValue? processId, @UuidValueConverter()  UuidValue? threadId, @UuidValueConverter()  UuidValue? branchId,  List<String> opgHashes)?  def,}) {final _that = this;
switch (_that) {
case _BootEnvironmentDescriptor() when def != null:
return def(_that.kernelEnvironmentConfigId,_that.bootEnvironmentId,_that.kernelEnvironmentConfigTitle,_that.bootEnvironmentTitle,_that.processId,_that.threadId,_that.branchId,_that.opgHashes);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _BootEnvironmentDescriptor implements BootEnvironmentDescriptor {
   _BootEnvironmentDescriptor({@UuidValueConverter() required this.kernelEnvironmentConfigId, @UuidValueConverter() required this.bootEnvironmentId, this.kernelEnvironmentConfigTitle, this.bootEnvironmentTitle, @UuidValueConverter() this.processId, @UuidValueConverter() this.threadId, @UuidValueConverter() this.branchId, final  List<String> opgHashes = const []}): _opgHashes = opgHashes;
  factory _BootEnvironmentDescriptor.fromJson(Map<String, dynamic> json) => _$BootEnvironmentDescriptorFromJson(json);

@override@UuidValueConverter() final  UuidValue kernelEnvironmentConfigId;
@override@UuidValueConverter() final  UuidValue bootEnvironmentId;
@override final  String? kernelEnvironmentConfigTitle;
@override final  String? bootEnvironmentTitle;
@override@UuidValueConverter() final  UuidValue? processId;
@override@UuidValueConverter() final  UuidValue? threadId;
@override@UuidValueConverter() final  UuidValue? branchId;
 final  List<String> _opgHashes;
@override@JsonKey() List<String> get opgHashes {
  if (_opgHashes is EqualUnmodifiableListView) return _opgHashes;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_opgHashes);
}


/// Create a copy of BootEnvironmentDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$BootEnvironmentDescriptorCopyWith<_BootEnvironmentDescriptor> get copyWith => __$BootEnvironmentDescriptorCopyWithImpl<_BootEnvironmentDescriptor>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$BootEnvironmentDescriptorToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _BootEnvironmentDescriptor&&(identical(other.kernelEnvironmentConfigId, kernelEnvironmentConfigId) || other.kernelEnvironmentConfigId == kernelEnvironmentConfigId)&&(identical(other.bootEnvironmentId, bootEnvironmentId) || other.bootEnvironmentId == bootEnvironmentId)&&(identical(other.kernelEnvironmentConfigTitle, kernelEnvironmentConfigTitle) || other.kernelEnvironmentConfigTitle == kernelEnvironmentConfigTitle)&&(identical(other.bootEnvironmentTitle, bootEnvironmentTitle) || other.bootEnvironmentTitle == bootEnvironmentTitle)&&(identical(other.processId, processId) || other.processId == processId)&&(identical(other.threadId, threadId) || other.threadId == threadId)&&(identical(other.branchId, branchId) || other.branchId == branchId)&&const DeepCollectionEquality().equals(other._opgHashes, _opgHashes));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,kernelEnvironmentConfigId,bootEnvironmentId,kernelEnvironmentConfigTitle,bootEnvironmentTitle,processId,threadId,branchId,const DeepCollectionEquality().hash(_opgHashes));

@override
String toString() {
  return 'BootEnvironmentDescriptor.def(kernelEnvironmentConfigId: $kernelEnvironmentConfigId, bootEnvironmentId: $bootEnvironmentId, kernelEnvironmentConfigTitle: $kernelEnvironmentConfigTitle, bootEnvironmentTitle: $bootEnvironmentTitle, processId: $processId, threadId: $threadId, branchId: $branchId, opgHashes: $opgHashes)';
}


}

/// @nodoc
abstract mixin class _$BootEnvironmentDescriptorCopyWith<$Res> implements $BootEnvironmentDescriptorCopyWith<$Res> {
  factory _$BootEnvironmentDescriptorCopyWith(_BootEnvironmentDescriptor value, $Res Function(_BootEnvironmentDescriptor) _then) = __$BootEnvironmentDescriptorCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue kernelEnvironmentConfigId,@UuidValueConverter() UuidValue bootEnvironmentId, String? kernelEnvironmentConfigTitle, String? bootEnvironmentTitle,@UuidValueConverter() UuidValue? processId,@UuidValueConverter() UuidValue? threadId,@UuidValueConverter() UuidValue? branchId, List<String> opgHashes
});




}
/// @nodoc
class __$BootEnvironmentDescriptorCopyWithImpl<$Res>
    implements _$BootEnvironmentDescriptorCopyWith<$Res> {
  __$BootEnvironmentDescriptorCopyWithImpl(this._self, this._then);

  final _BootEnvironmentDescriptor _self;
  final $Res Function(_BootEnvironmentDescriptor) _then;

/// Create a copy of BootEnvironmentDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? kernelEnvironmentConfigId = null,Object? bootEnvironmentId = null,Object? kernelEnvironmentConfigTitle = freezed,Object? bootEnvironmentTitle = freezed,Object? processId = freezed,Object? threadId = freezed,Object? branchId = freezed,Object? opgHashes = null,}) {
  return _then(_BootEnvironmentDescriptor(
kernelEnvironmentConfigId: null == kernelEnvironmentConfigId ? _self.kernelEnvironmentConfigId : kernelEnvironmentConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,bootEnvironmentId: null == bootEnvironmentId ? _self.bootEnvironmentId : bootEnvironmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,kernelEnvironmentConfigTitle: freezed == kernelEnvironmentConfigTitle ? _self.kernelEnvironmentConfigTitle : kernelEnvironmentConfigTitle // ignore: cast_nullable_to_non_nullable
as String?,bootEnvironmentTitle: freezed == bootEnvironmentTitle ? _self.bootEnvironmentTitle : bootEnvironmentTitle // ignore: cast_nullable_to_non_nullable
as String?,processId: freezed == processId ? _self.processId : processId // ignore: cast_nullable_to_non_nullable
as UuidValue?,threadId: freezed == threadId ? _self.threadId : threadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,branchId: freezed == branchId ? _self.branchId : branchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,opgHashes: null == opgHashes ? _self._opgHashes : opgHashes // ignore: cast_nullable_to_non_nullable
as List<String>,
  ));
}


}


/// @nodoc
mixin _$ServiceApiDependencyRouteDescriptor {

@UuidValueConverter() UuidValue get consumerServicePackageId; String get consumerServicePackageName;@UuidValueConverter() UuidValue get providerServicePackageId; String get providerServicePackageName;@UuidValueConverter() UuidValue get apiPackageId; String? get apiPackageName; String get routeKind; String get hostId; String? get hostVersion; String get protocolVersion; String? get socketPath;@UuidValueConverter() UuidValue? get consumerNodeId;@UuidValueConverter() UuidValue? get providerNodeId; String? get providerNodeBaseUrl;@UuidValueConverter() UuidValue? get routeConnectionId; double get requestTimeoutS; List<String> get serviceNames; Map<String, dynamic> get endpointRefsByService; Map<String, dynamic> get streamEndpointRefsByService;
/// Create a copy of ServiceApiDependencyRouteDescriptor
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ServiceApiDependencyRouteDescriptorCopyWith<ServiceApiDependencyRouteDescriptor> get copyWith => _$ServiceApiDependencyRouteDescriptorCopyWithImpl<ServiceApiDependencyRouteDescriptor>(this as ServiceApiDependencyRouteDescriptor, _$identity);

  /// Serializes this ServiceApiDependencyRouteDescriptor to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ServiceApiDependencyRouteDescriptor&&(identical(other.consumerServicePackageId, consumerServicePackageId) || other.consumerServicePackageId == consumerServicePackageId)&&(identical(other.consumerServicePackageName, consumerServicePackageName) || other.consumerServicePackageName == consumerServicePackageName)&&(identical(other.providerServicePackageId, providerServicePackageId) || other.providerServicePackageId == providerServicePackageId)&&(identical(other.providerServicePackageName, providerServicePackageName) || other.providerServicePackageName == providerServicePackageName)&&(identical(other.apiPackageId, apiPackageId) || other.apiPackageId == apiPackageId)&&(identical(other.apiPackageName, apiPackageName) || other.apiPackageName == apiPackageName)&&(identical(other.routeKind, routeKind) || other.routeKind == routeKind)&&(identical(other.hostId, hostId) || other.hostId == hostId)&&(identical(other.hostVersion, hostVersion) || other.hostVersion == hostVersion)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.socketPath, socketPath) || other.socketPath == socketPath)&&(identical(other.consumerNodeId, consumerNodeId) || other.consumerNodeId == consumerNodeId)&&(identical(other.providerNodeId, providerNodeId) || other.providerNodeId == providerNodeId)&&(identical(other.providerNodeBaseUrl, providerNodeBaseUrl) || other.providerNodeBaseUrl == providerNodeBaseUrl)&&(identical(other.routeConnectionId, routeConnectionId) || other.routeConnectionId == routeConnectionId)&&(identical(other.requestTimeoutS, requestTimeoutS) || other.requestTimeoutS == requestTimeoutS)&&const DeepCollectionEquality().equals(other.serviceNames, serviceNames)&&const DeepCollectionEquality().equals(other.endpointRefsByService, endpointRefsByService)&&const DeepCollectionEquality().equals(other.streamEndpointRefsByService, streamEndpointRefsByService));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,consumerServicePackageId,consumerServicePackageName,providerServicePackageId,providerServicePackageName,apiPackageId,apiPackageName,routeKind,hostId,hostVersion,protocolVersion,socketPath,consumerNodeId,providerNodeId,providerNodeBaseUrl,routeConnectionId,requestTimeoutS,const DeepCollectionEquality().hash(serviceNames),const DeepCollectionEquality().hash(endpointRefsByService),const DeepCollectionEquality().hash(streamEndpointRefsByService)]);

@override
String toString() {
  return 'ServiceApiDependencyRouteDescriptor(consumerServicePackageId: $consumerServicePackageId, consumerServicePackageName: $consumerServicePackageName, providerServicePackageId: $providerServicePackageId, providerServicePackageName: $providerServicePackageName, apiPackageId: $apiPackageId, apiPackageName: $apiPackageName, routeKind: $routeKind, hostId: $hostId, hostVersion: $hostVersion, protocolVersion: $protocolVersion, socketPath: $socketPath, consumerNodeId: $consumerNodeId, providerNodeId: $providerNodeId, providerNodeBaseUrl: $providerNodeBaseUrl, routeConnectionId: $routeConnectionId, requestTimeoutS: $requestTimeoutS, serviceNames: $serviceNames, endpointRefsByService: $endpointRefsByService, streamEndpointRefsByService: $streamEndpointRefsByService)';
}


}

/// @nodoc
abstract mixin class $ServiceApiDependencyRouteDescriptorCopyWith<$Res>  {
  factory $ServiceApiDependencyRouteDescriptorCopyWith(ServiceApiDependencyRouteDescriptor value, $Res Function(ServiceApiDependencyRouteDescriptor) _then) = _$ServiceApiDependencyRouteDescriptorCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue consumerServicePackageId, String consumerServicePackageName,@UuidValueConverter() UuidValue providerServicePackageId, String providerServicePackageName,@UuidValueConverter() UuidValue apiPackageId, String? apiPackageName, String routeKind, String hostId, String? hostVersion, String protocolVersion, String? socketPath,@UuidValueConverter() UuidValue? consumerNodeId,@UuidValueConverter() UuidValue? providerNodeId, String? providerNodeBaseUrl,@UuidValueConverter() UuidValue? routeConnectionId, double requestTimeoutS, List<String> serviceNames, Map<String, dynamic> endpointRefsByService, Map<String, dynamic> streamEndpointRefsByService
});




}
/// @nodoc
class _$ServiceApiDependencyRouteDescriptorCopyWithImpl<$Res>
    implements $ServiceApiDependencyRouteDescriptorCopyWith<$Res> {
  _$ServiceApiDependencyRouteDescriptorCopyWithImpl(this._self, this._then);

  final ServiceApiDependencyRouteDescriptor _self;
  final $Res Function(ServiceApiDependencyRouteDescriptor) _then;

/// Create a copy of ServiceApiDependencyRouteDescriptor
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? consumerServicePackageId = null,Object? consumerServicePackageName = null,Object? providerServicePackageId = null,Object? providerServicePackageName = null,Object? apiPackageId = null,Object? apiPackageName = freezed,Object? routeKind = null,Object? hostId = null,Object? hostVersion = freezed,Object? protocolVersion = null,Object? socketPath = freezed,Object? consumerNodeId = freezed,Object? providerNodeId = freezed,Object? providerNodeBaseUrl = freezed,Object? routeConnectionId = freezed,Object? requestTimeoutS = null,Object? serviceNames = null,Object? endpointRefsByService = null,Object? streamEndpointRefsByService = null,}) {
  return _then(_self.copyWith(
consumerServicePackageId: null == consumerServicePackageId ? _self.consumerServicePackageId : consumerServicePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,consumerServicePackageName: null == consumerServicePackageName ? _self.consumerServicePackageName : consumerServicePackageName // ignore: cast_nullable_to_non_nullable
as String,providerServicePackageId: null == providerServicePackageId ? _self.providerServicePackageId : providerServicePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,providerServicePackageName: null == providerServicePackageName ? _self.providerServicePackageName : providerServicePackageName // ignore: cast_nullable_to_non_nullable
as String,apiPackageId: null == apiPackageId ? _self.apiPackageId : apiPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,apiPackageName: freezed == apiPackageName ? _self.apiPackageName : apiPackageName // ignore: cast_nullable_to_non_nullable
as String?,routeKind: null == routeKind ? _self.routeKind : routeKind // ignore: cast_nullable_to_non_nullable
as String,hostId: null == hostId ? _self.hostId : hostId // ignore: cast_nullable_to_non_nullable
as String,hostVersion: freezed == hostVersion ? _self.hostVersion : hostVersion // ignore: cast_nullable_to_non_nullable
as String?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as String,socketPath: freezed == socketPath ? _self.socketPath : socketPath // ignore: cast_nullable_to_non_nullable
as String?,consumerNodeId: freezed == consumerNodeId ? _self.consumerNodeId : consumerNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,providerNodeId: freezed == providerNodeId ? _self.providerNodeId : providerNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,providerNodeBaseUrl: freezed == providerNodeBaseUrl ? _self.providerNodeBaseUrl : providerNodeBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,routeConnectionId: freezed == routeConnectionId ? _self.routeConnectionId : routeConnectionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestTimeoutS: null == requestTimeoutS ? _self.requestTimeoutS : requestTimeoutS // ignore: cast_nullable_to_non_nullable
as double,serviceNames: null == serviceNames ? _self.serviceNames : serviceNames // ignore: cast_nullable_to_non_nullable
as List<String>,endpointRefsByService: null == endpointRefsByService ? _self.endpointRefsByService : endpointRefsByService // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,streamEndpointRefsByService: null == streamEndpointRefsByService ? _self.streamEndpointRefsByService : streamEndpointRefsByService // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [ServiceApiDependencyRouteDescriptor].
extension ServiceApiDependencyRouteDescriptorPatterns on ServiceApiDependencyRouteDescriptor {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ServiceApiDependencyRouteDescriptor value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ServiceApiDependencyRouteDescriptor() when def != null:
return def(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ServiceApiDependencyRouteDescriptor value)  def,}){
final _that = this;
switch (_that) {
case _ServiceApiDependencyRouteDescriptor():
return def(_that);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ServiceApiDependencyRouteDescriptor value)?  def,}){
final _that = this;
switch (_that) {
case _ServiceApiDependencyRouteDescriptor() when def != null:
return def(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue consumerServicePackageId,  String consumerServicePackageName, @UuidValueConverter()  UuidValue providerServicePackageId,  String providerServicePackageName, @UuidValueConverter()  UuidValue apiPackageId,  String? apiPackageName,  String routeKind,  String hostId,  String? hostVersion,  String protocolVersion,  String? socketPath, @UuidValueConverter()  UuidValue? consumerNodeId, @UuidValueConverter()  UuidValue? providerNodeId,  String? providerNodeBaseUrl, @UuidValueConverter()  UuidValue? routeConnectionId,  double requestTimeoutS,  List<String> serviceNames,  Map<String, dynamic> endpointRefsByService,  Map<String, dynamic> streamEndpointRefsByService)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ServiceApiDependencyRouteDescriptor() when def != null:
return def(_that.consumerServicePackageId,_that.consumerServicePackageName,_that.providerServicePackageId,_that.providerServicePackageName,_that.apiPackageId,_that.apiPackageName,_that.routeKind,_that.hostId,_that.hostVersion,_that.protocolVersion,_that.socketPath,_that.consumerNodeId,_that.providerNodeId,_that.providerNodeBaseUrl,_that.routeConnectionId,_that.requestTimeoutS,_that.serviceNames,_that.endpointRefsByService,_that.streamEndpointRefsByService);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue consumerServicePackageId,  String consumerServicePackageName, @UuidValueConverter()  UuidValue providerServicePackageId,  String providerServicePackageName, @UuidValueConverter()  UuidValue apiPackageId,  String? apiPackageName,  String routeKind,  String hostId,  String? hostVersion,  String protocolVersion,  String? socketPath, @UuidValueConverter()  UuidValue? consumerNodeId, @UuidValueConverter()  UuidValue? providerNodeId,  String? providerNodeBaseUrl, @UuidValueConverter()  UuidValue? routeConnectionId,  double requestTimeoutS,  List<String> serviceNames,  Map<String, dynamic> endpointRefsByService,  Map<String, dynamic> streamEndpointRefsByService)  def,}) {final _that = this;
switch (_that) {
case _ServiceApiDependencyRouteDescriptor():
return def(_that.consumerServicePackageId,_that.consumerServicePackageName,_that.providerServicePackageId,_that.providerServicePackageName,_that.apiPackageId,_that.apiPackageName,_that.routeKind,_that.hostId,_that.hostVersion,_that.protocolVersion,_that.socketPath,_that.consumerNodeId,_that.providerNodeId,_that.providerNodeBaseUrl,_that.routeConnectionId,_that.requestTimeoutS,_that.serviceNames,_that.endpointRefsByService,_that.streamEndpointRefsByService);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue consumerServicePackageId,  String consumerServicePackageName, @UuidValueConverter()  UuidValue providerServicePackageId,  String providerServicePackageName, @UuidValueConverter()  UuidValue apiPackageId,  String? apiPackageName,  String routeKind,  String hostId,  String? hostVersion,  String protocolVersion,  String? socketPath, @UuidValueConverter()  UuidValue? consumerNodeId, @UuidValueConverter()  UuidValue? providerNodeId,  String? providerNodeBaseUrl, @UuidValueConverter()  UuidValue? routeConnectionId,  double requestTimeoutS,  List<String> serviceNames,  Map<String, dynamic> endpointRefsByService,  Map<String, dynamic> streamEndpointRefsByService)?  def,}) {final _that = this;
switch (_that) {
case _ServiceApiDependencyRouteDescriptor() when def != null:
return def(_that.consumerServicePackageId,_that.consumerServicePackageName,_that.providerServicePackageId,_that.providerServicePackageName,_that.apiPackageId,_that.apiPackageName,_that.routeKind,_that.hostId,_that.hostVersion,_that.protocolVersion,_that.socketPath,_that.consumerNodeId,_that.providerNodeId,_that.providerNodeBaseUrl,_that.routeConnectionId,_that.requestTimeoutS,_that.serviceNames,_that.endpointRefsByService,_that.streamEndpointRefsByService);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ServiceApiDependencyRouteDescriptor implements ServiceApiDependencyRouteDescriptor {
   _ServiceApiDependencyRouteDescriptor({@UuidValueConverter() required this.consumerServicePackageId, required this.consumerServicePackageName, @UuidValueConverter() required this.providerServicePackageId, required this.providerServicePackageName, @UuidValueConverter() required this.apiPackageId, this.apiPackageName, required this.routeKind, required this.hostId, this.hostVersion, required this.protocolVersion, this.socketPath, @UuidValueConverter() this.consumerNodeId, @UuidValueConverter() this.providerNodeId, this.providerNodeBaseUrl, @UuidValueConverter() this.routeConnectionId, required this.requestTimeoutS, final  List<String> serviceNames = const [], required final  Map<String, dynamic> endpointRefsByService, required final  Map<String, dynamic> streamEndpointRefsByService}): _serviceNames = serviceNames,_endpointRefsByService = endpointRefsByService,_streamEndpointRefsByService = streamEndpointRefsByService;
  factory _ServiceApiDependencyRouteDescriptor.fromJson(Map<String, dynamic> json) => _$ServiceApiDependencyRouteDescriptorFromJson(json);

@override@UuidValueConverter() final  UuidValue consumerServicePackageId;
@override final  String consumerServicePackageName;
@override@UuidValueConverter() final  UuidValue providerServicePackageId;
@override final  String providerServicePackageName;
@override@UuidValueConverter() final  UuidValue apiPackageId;
@override final  String? apiPackageName;
@override final  String routeKind;
@override final  String hostId;
@override final  String? hostVersion;
@override final  String protocolVersion;
@override final  String? socketPath;
@override@UuidValueConverter() final  UuidValue? consumerNodeId;
@override@UuidValueConverter() final  UuidValue? providerNodeId;
@override final  String? providerNodeBaseUrl;
@override@UuidValueConverter() final  UuidValue? routeConnectionId;
@override final  double requestTimeoutS;
 final  List<String> _serviceNames;
@override@JsonKey() List<String> get serviceNames {
  if (_serviceNames is EqualUnmodifiableListView) return _serviceNames;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_serviceNames);
}

 final  Map<String, dynamic> _endpointRefsByService;
@override Map<String, dynamic> get endpointRefsByService {
  if (_endpointRefsByService is EqualUnmodifiableMapView) return _endpointRefsByService;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_endpointRefsByService);
}

 final  Map<String, dynamic> _streamEndpointRefsByService;
@override Map<String, dynamic> get streamEndpointRefsByService {
  if (_streamEndpointRefsByService is EqualUnmodifiableMapView) return _streamEndpointRefsByService;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_streamEndpointRefsByService);
}


/// Create a copy of ServiceApiDependencyRouteDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ServiceApiDependencyRouteDescriptorCopyWith<_ServiceApiDependencyRouteDescriptor> get copyWith => __$ServiceApiDependencyRouteDescriptorCopyWithImpl<_ServiceApiDependencyRouteDescriptor>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ServiceApiDependencyRouteDescriptorToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ServiceApiDependencyRouteDescriptor&&(identical(other.consumerServicePackageId, consumerServicePackageId) || other.consumerServicePackageId == consumerServicePackageId)&&(identical(other.consumerServicePackageName, consumerServicePackageName) || other.consumerServicePackageName == consumerServicePackageName)&&(identical(other.providerServicePackageId, providerServicePackageId) || other.providerServicePackageId == providerServicePackageId)&&(identical(other.providerServicePackageName, providerServicePackageName) || other.providerServicePackageName == providerServicePackageName)&&(identical(other.apiPackageId, apiPackageId) || other.apiPackageId == apiPackageId)&&(identical(other.apiPackageName, apiPackageName) || other.apiPackageName == apiPackageName)&&(identical(other.routeKind, routeKind) || other.routeKind == routeKind)&&(identical(other.hostId, hostId) || other.hostId == hostId)&&(identical(other.hostVersion, hostVersion) || other.hostVersion == hostVersion)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.socketPath, socketPath) || other.socketPath == socketPath)&&(identical(other.consumerNodeId, consumerNodeId) || other.consumerNodeId == consumerNodeId)&&(identical(other.providerNodeId, providerNodeId) || other.providerNodeId == providerNodeId)&&(identical(other.providerNodeBaseUrl, providerNodeBaseUrl) || other.providerNodeBaseUrl == providerNodeBaseUrl)&&(identical(other.routeConnectionId, routeConnectionId) || other.routeConnectionId == routeConnectionId)&&(identical(other.requestTimeoutS, requestTimeoutS) || other.requestTimeoutS == requestTimeoutS)&&const DeepCollectionEquality().equals(other._serviceNames, _serviceNames)&&const DeepCollectionEquality().equals(other._endpointRefsByService, _endpointRefsByService)&&const DeepCollectionEquality().equals(other._streamEndpointRefsByService, _streamEndpointRefsByService));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,consumerServicePackageId,consumerServicePackageName,providerServicePackageId,providerServicePackageName,apiPackageId,apiPackageName,routeKind,hostId,hostVersion,protocolVersion,socketPath,consumerNodeId,providerNodeId,providerNodeBaseUrl,routeConnectionId,requestTimeoutS,const DeepCollectionEquality().hash(_serviceNames),const DeepCollectionEquality().hash(_endpointRefsByService),const DeepCollectionEquality().hash(_streamEndpointRefsByService)]);

@override
String toString() {
  return 'ServiceApiDependencyRouteDescriptor.def(consumerServicePackageId: $consumerServicePackageId, consumerServicePackageName: $consumerServicePackageName, providerServicePackageId: $providerServicePackageId, providerServicePackageName: $providerServicePackageName, apiPackageId: $apiPackageId, apiPackageName: $apiPackageName, routeKind: $routeKind, hostId: $hostId, hostVersion: $hostVersion, protocolVersion: $protocolVersion, socketPath: $socketPath, consumerNodeId: $consumerNodeId, providerNodeId: $providerNodeId, providerNodeBaseUrl: $providerNodeBaseUrl, routeConnectionId: $routeConnectionId, requestTimeoutS: $requestTimeoutS, serviceNames: $serviceNames, endpointRefsByService: $endpointRefsByService, streamEndpointRefsByService: $streamEndpointRefsByService)';
}


}

/// @nodoc
abstract mixin class _$ServiceApiDependencyRouteDescriptorCopyWith<$Res> implements $ServiceApiDependencyRouteDescriptorCopyWith<$Res> {
  factory _$ServiceApiDependencyRouteDescriptorCopyWith(_ServiceApiDependencyRouteDescriptor value, $Res Function(_ServiceApiDependencyRouteDescriptor) _then) = __$ServiceApiDependencyRouteDescriptorCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue consumerServicePackageId, String consumerServicePackageName,@UuidValueConverter() UuidValue providerServicePackageId, String providerServicePackageName,@UuidValueConverter() UuidValue apiPackageId, String? apiPackageName, String routeKind, String hostId, String? hostVersion, String protocolVersion, String? socketPath,@UuidValueConverter() UuidValue? consumerNodeId,@UuidValueConverter() UuidValue? providerNodeId, String? providerNodeBaseUrl,@UuidValueConverter() UuidValue? routeConnectionId, double requestTimeoutS, List<String> serviceNames, Map<String, dynamic> endpointRefsByService, Map<String, dynamic> streamEndpointRefsByService
});




}
/// @nodoc
class __$ServiceApiDependencyRouteDescriptorCopyWithImpl<$Res>
    implements _$ServiceApiDependencyRouteDescriptorCopyWith<$Res> {
  __$ServiceApiDependencyRouteDescriptorCopyWithImpl(this._self, this._then);

  final _ServiceApiDependencyRouteDescriptor _self;
  final $Res Function(_ServiceApiDependencyRouteDescriptor) _then;

/// Create a copy of ServiceApiDependencyRouteDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? consumerServicePackageId = null,Object? consumerServicePackageName = null,Object? providerServicePackageId = null,Object? providerServicePackageName = null,Object? apiPackageId = null,Object? apiPackageName = freezed,Object? routeKind = null,Object? hostId = null,Object? hostVersion = freezed,Object? protocolVersion = null,Object? socketPath = freezed,Object? consumerNodeId = freezed,Object? providerNodeId = freezed,Object? providerNodeBaseUrl = freezed,Object? routeConnectionId = freezed,Object? requestTimeoutS = null,Object? serviceNames = null,Object? endpointRefsByService = null,Object? streamEndpointRefsByService = null,}) {
  return _then(_ServiceApiDependencyRouteDescriptor(
consumerServicePackageId: null == consumerServicePackageId ? _self.consumerServicePackageId : consumerServicePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,consumerServicePackageName: null == consumerServicePackageName ? _self.consumerServicePackageName : consumerServicePackageName // ignore: cast_nullable_to_non_nullable
as String,providerServicePackageId: null == providerServicePackageId ? _self.providerServicePackageId : providerServicePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,providerServicePackageName: null == providerServicePackageName ? _self.providerServicePackageName : providerServicePackageName // ignore: cast_nullable_to_non_nullable
as String,apiPackageId: null == apiPackageId ? _self.apiPackageId : apiPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,apiPackageName: freezed == apiPackageName ? _self.apiPackageName : apiPackageName // ignore: cast_nullable_to_non_nullable
as String?,routeKind: null == routeKind ? _self.routeKind : routeKind // ignore: cast_nullable_to_non_nullable
as String,hostId: null == hostId ? _self.hostId : hostId // ignore: cast_nullable_to_non_nullable
as String,hostVersion: freezed == hostVersion ? _self.hostVersion : hostVersion // ignore: cast_nullable_to_non_nullable
as String?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as String,socketPath: freezed == socketPath ? _self.socketPath : socketPath // ignore: cast_nullable_to_non_nullable
as String?,consumerNodeId: freezed == consumerNodeId ? _self.consumerNodeId : consumerNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,providerNodeId: freezed == providerNodeId ? _self.providerNodeId : providerNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,providerNodeBaseUrl: freezed == providerNodeBaseUrl ? _self.providerNodeBaseUrl : providerNodeBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,routeConnectionId: freezed == routeConnectionId ? _self.routeConnectionId : routeConnectionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestTimeoutS: null == requestTimeoutS ? _self.requestTimeoutS : requestTimeoutS // ignore: cast_nullable_to_non_nullable
as double,serviceNames: null == serviceNames ? _self._serviceNames : serviceNames // ignore: cast_nullable_to_non_nullable
as List<String>,endpointRefsByService: null == endpointRefsByService ? _self._endpointRefsByService : endpointRefsByService // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,streamEndpointRefsByService: null == streamEndpointRefsByService ? _self._streamEndpointRefsByService : streamEndpointRefsByService // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$HostedServiceAdvertisement {

@UuidValueConverter() UuidValue? get servicePackageId;@UuidValueConverter() UuidValue? get serviceId; String get serviceName; List<String> get servicePackageNames; List<String> get endpointRefs; String get hostId; String? get hostVersion; String get protocolVersion; bool get supportsStreamEvents;
/// Create a copy of HostedServiceAdvertisement
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$HostedServiceAdvertisementCopyWith<HostedServiceAdvertisement> get copyWith => _$HostedServiceAdvertisementCopyWithImpl<HostedServiceAdvertisement>(this as HostedServiceAdvertisement, _$identity);

  /// Serializes this HostedServiceAdvertisement to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is HostedServiceAdvertisement&&(identical(other.servicePackageId, servicePackageId) || other.servicePackageId == servicePackageId)&&(identical(other.serviceId, serviceId) || other.serviceId == serviceId)&&(identical(other.serviceName, serviceName) || other.serviceName == serviceName)&&const DeepCollectionEquality().equals(other.servicePackageNames, servicePackageNames)&&const DeepCollectionEquality().equals(other.endpointRefs, endpointRefs)&&(identical(other.hostId, hostId) || other.hostId == hostId)&&(identical(other.hostVersion, hostVersion) || other.hostVersion == hostVersion)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.supportsStreamEvents, supportsStreamEvents) || other.supportsStreamEvents == supportsStreamEvents));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,servicePackageId,serviceId,serviceName,const DeepCollectionEquality().hash(servicePackageNames),const DeepCollectionEquality().hash(endpointRefs),hostId,hostVersion,protocolVersion,supportsStreamEvents);

@override
String toString() {
  return 'HostedServiceAdvertisement(servicePackageId: $servicePackageId, serviceId: $serviceId, serviceName: $serviceName, servicePackageNames: $servicePackageNames, endpointRefs: $endpointRefs, hostId: $hostId, hostVersion: $hostVersion, protocolVersion: $protocolVersion, supportsStreamEvents: $supportsStreamEvents)';
}


}

/// @nodoc
abstract mixin class $HostedServiceAdvertisementCopyWith<$Res>  {
  factory $HostedServiceAdvertisementCopyWith(HostedServiceAdvertisement value, $Res Function(HostedServiceAdvertisement) _then) = _$HostedServiceAdvertisementCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? servicePackageId,@UuidValueConverter() UuidValue? serviceId, String serviceName, List<String> servicePackageNames, List<String> endpointRefs, String hostId, String? hostVersion, String protocolVersion, bool supportsStreamEvents
});




}
/// @nodoc
class _$HostedServiceAdvertisementCopyWithImpl<$Res>
    implements $HostedServiceAdvertisementCopyWith<$Res> {
  _$HostedServiceAdvertisementCopyWithImpl(this._self, this._then);

  final HostedServiceAdvertisement _self;
  final $Res Function(HostedServiceAdvertisement) _then;

/// Create a copy of HostedServiceAdvertisement
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? servicePackageId = freezed,Object? serviceId = freezed,Object? serviceName = null,Object? servicePackageNames = null,Object? endpointRefs = null,Object? hostId = null,Object? hostVersion = freezed,Object? protocolVersion = null,Object? supportsStreamEvents = null,}) {
  return _then(_self.copyWith(
servicePackageId: freezed == servicePackageId ? _self.servicePackageId : servicePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceId: freezed == serviceId ? _self.serviceId : serviceId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceName: null == serviceName ? _self.serviceName : serviceName // ignore: cast_nullable_to_non_nullable
as String,servicePackageNames: null == servicePackageNames ? _self.servicePackageNames : servicePackageNames // ignore: cast_nullable_to_non_nullable
as List<String>,endpointRefs: null == endpointRefs ? _self.endpointRefs : endpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,hostId: null == hostId ? _self.hostId : hostId // ignore: cast_nullable_to_non_nullable
as String,hostVersion: freezed == hostVersion ? _self.hostVersion : hostVersion // ignore: cast_nullable_to_non_nullable
as String?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as String,supportsStreamEvents: null == supportsStreamEvents ? _self.supportsStreamEvents : supportsStreamEvents // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}

}


/// Adds pattern-matching-related methods to [HostedServiceAdvertisement].
extension HostedServiceAdvertisementPatterns on HostedServiceAdvertisement {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _HostedServiceAdvertisement value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _HostedServiceAdvertisement() when def != null:
return def(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _HostedServiceAdvertisement value)  def,}){
final _that = this;
switch (_that) {
case _HostedServiceAdvertisement():
return def(_that);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _HostedServiceAdvertisement value)?  def,}){
final _that = this;
switch (_that) {
case _HostedServiceAdvertisement() when def != null:
return def(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? servicePackageId, @UuidValueConverter()  UuidValue? serviceId,  String serviceName,  List<String> servicePackageNames,  List<String> endpointRefs,  String hostId,  String? hostVersion,  String protocolVersion,  bool supportsStreamEvents)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _HostedServiceAdvertisement() when def != null:
return def(_that.servicePackageId,_that.serviceId,_that.serviceName,_that.servicePackageNames,_that.endpointRefs,_that.hostId,_that.hostVersion,_that.protocolVersion,_that.supportsStreamEvents);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? servicePackageId, @UuidValueConverter()  UuidValue? serviceId,  String serviceName,  List<String> servicePackageNames,  List<String> endpointRefs,  String hostId,  String? hostVersion,  String protocolVersion,  bool supportsStreamEvents)  def,}) {final _that = this;
switch (_that) {
case _HostedServiceAdvertisement():
return def(_that.servicePackageId,_that.serviceId,_that.serviceName,_that.servicePackageNames,_that.endpointRefs,_that.hostId,_that.hostVersion,_that.protocolVersion,_that.supportsStreamEvents);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? servicePackageId, @UuidValueConverter()  UuidValue? serviceId,  String serviceName,  List<String> servicePackageNames,  List<String> endpointRefs,  String hostId,  String? hostVersion,  String protocolVersion,  bool supportsStreamEvents)?  def,}) {final _that = this;
switch (_that) {
case _HostedServiceAdvertisement() when def != null:
return def(_that.servicePackageId,_that.serviceId,_that.serviceName,_that.servicePackageNames,_that.endpointRefs,_that.hostId,_that.hostVersion,_that.protocolVersion,_that.supportsStreamEvents);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _HostedServiceAdvertisement implements HostedServiceAdvertisement {
   _HostedServiceAdvertisement({@UuidValueConverter() this.servicePackageId, @UuidValueConverter() this.serviceId, required this.serviceName, final  List<String> servicePackageNames = const [], final  List<String> endpointRefs = const [], required this.hostId, this.hostVersion, required this.protocolVersion, required this.supportsStreamEvents}): _servicePackageNames = servicePackageNames,_endpointRefs = endpointRefs;
  factory _HostedServiceAdvertisement.fromJson(Map<String, dynamic> json) => _$HostedServiceAdvertisementFromJson(json);

@override@UuidValueConverter() final  UuidValue? servicePackageId;
@override@UuidValueConverter() final  UuidValue? serviceId;
@override final  String serviceName;
 final  List<String> _servicePackageNames;
@override@JsonKey() List<String> get servicePackageNames {
  if (_servicePackageNames is EqualUnmodifiableListView) return _servicePackageNames;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_servicePackageNames);
}

 final  List<String> _endpointRefs;
@override@JsonKey() List<String> get endpointRefs {
  if (_endpointRefs is EqualUnmodifiableListView) return _endpointRefs;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_endpointRefs);
}

@override final  String hostId;
@override final  String? hostVersion;
@override final  String protocolVersion;
@override final  bool supportsStreamEvents;

/// Create a copy of HostedServiceAdvertisement
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$HostedServiceAdvertisementCopyWith<_HostedServiceAdvertisement> get copyWith => __$HostedServiceAdvertisementCopyWithImpl<_HostedServiceAdvertisement>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$HostedServiceAdvertisementToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _HostedServiceAdvertisement&&(identical(other.servicePackageId, servicePackageId) || other.servicePackageId == servicePackageId)&&(identical(other.serviceId, serviceId) || other.serviceId == serviceId)&&(identical(other.serviceName, serviceName) || other.serviceName == serviceName)&&const DeepCollectionEquality().equals(other._servicePackageNames, _servicePackageNames)&&const DeepCollectionEquality().equals(other._endpointRefs, _endpointRefs)&&(identical(other.hostId, hostId) || other.hostId == hostId)&&(identical(other.hostVersion, hostVersion) || other.hostVersion == hostVersion)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.supportsStreamEvents, supportsStreamEvents) || other.supportsStreamEvents == supportsStreamEvents));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,servicePackageId,serviceId,serviceName,const DeepCollectionEquality().hash(_servicePackageNames),const DeepCollectionEquality().hash(_endpointRefs),hostId,hostVersion,protocolVersion,supportsStreamEvents);

@override
String toString() {
  return 'HostedServiceAdvertisement.def(servicePackageId: $servicePackageId, serviceId: $serviceId, serviceName: $serviceName, servicePackageNames: $servicePackageNames, endpointRefs: $endpointRefs, hostId: $hostId, hostVersion: $hostVersion, protocolVersion: $protocolVersion, supportsStreamEvents: $supportsStreamEvents)';
}


}

/// @nodoc
abstract mixin class _$HostedServiceAdvertisementCopyWith<$Res> implements $HostedServiceAdvertisementCopyWith<$Res> {
  factory _$HostedServiceAdvertisementCopyWith(_HostedServiceAdvertisement value, $Res Function(_HostedServiceAdvertisement) _then) = __$HostedServiceAdvertisementCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? servicePackageId,@UuidValueConverter() UuidValue? serviceId, String serviceName, List<String> servicePackageNames, List<String> endpointRefs, String hostId, String? hostVersion, String protocolVersion, bool supportsStreamEvents
});




}
/// @nodoc
class __$HostedServiceAdvertisementCopyWithImpl<$Res>
    implements _$HostedServiceAdvertisementCopyWith<$Res> {
  __$HostedServiceAdvertisementCopyWithImpl(this._self, this._then);

  final _HostedServiceAdvertisement _self;
  final $Res Function(_HostedServiceAdvertisement) _then;

/// Create a copy of HostedServiceAdvertisement
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? servicePackageId = freezed,Object? serviceId = freezed,Object? serviceName = null,Object? servicePackageNames = null,Object? endpointRefs = null,Object? hostId = null,Object? hostVersion = freezed,Object? protocolVersion = null,Object? supportsStreamEvents = null,}) {
  return _then(_HostedServiceAdvertisement(
servicePackageId: freezed == servicePackageId ? _self.servicePackageId : servicePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceId: freezed == serviceId ? _self.serviceId : serviceId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceName: null == serviceName ? _self.serviceName : serviceName // ignore: cast_nullable_to_non_nullable
as String,servicePackageNames: null == servicePackageNames ? _self._servicePackageNames : servicePackageNames // ignore: cast_nullable_to_non_nullable
as List<String>,endpointRefs: null == endpointRefs ? _self._endpointRefs : endpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,hostId: null == hostId ? _self.hostId : hostId // ignore: cast_nullable_to_non_nullable
as String,hostVersion: freezed == hostVersion ? _self.hostVersion : hostVersion // ignore: cast_nullable_to_non_nullable
as String?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as String,supportsStreamEvents: null == supportsStreamEvents ? _self.supportsStreamEvents : supportsStreamEvents // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}


}


/// @nodoc
mixin _$HostedServiceRuntimeServiceStatus {

 String get serviceName; List<String> get endpointRefs; List<String> get streamEndpointRefs;
/// Create a copy of HostedServiceRuntimeServiceStatus
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$HostedServiceRuntimeServiceStatusCopyWith<HostedServiceRuntimeServiceStatus> get copyWith => _$HostedServiceRuntimeServiceStatusCopyWithImpl<HostedServiceRuntimeServiceStatus>(this as HostedServiceRuntimeServiceStatus, _$identity);

  /// Serializes this HostedServiceRuntimeServiceStatus to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is HostedServiceRuntimeServiceStatus&&(identical(other.serviceName, serviceName) || other.serviceName == serviceName)&&const DeepCollectionEquality().equals(other.endpointRefs, endpointRefs)&&const DeepCollectionEquality().equals(other.streamEndpointRefs, streamEndpointRefs));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,serviceName,const DeepCollectionEquality().hash(endpointRefs),const DeepCollectionEquality().hash(streamEndpointRefs));

@override
String toString() {
  return 'HostedServiceRuntimeServiceStatus(serviceName: $serviceName, endpointRefs: $endpointRefs, streamEndpointRefs: $streamEndpointRefs)';
}


}

/// @nodoc
abstract mixin class $HostedServiceRuntimeServiceStatusCopyWith<$Res>  {
  factory $HostedServiceRuntimeServiceStatusCopyWith(HostedServiceRuntimeServiceStatus value, $Res Function(HostedServiceRuntimeServiceStatus) _then) = _$HostedServiceRuntimeServiceStatusCopyWithImpl;
@useResult
$Res call({
 String serviceName, List<String> endpointRefs, List<String> streamEndpointRefs
});




}
/// @nodoc
class _$HostedServiceRuntimeServiceStatusCopyWithImpl<$Res>
    implements $HostedServiceRuntimeServiceStatusCopyWith<$Res> {
  _$HostedServiceRuntimeServiceStatusCopyWithImpl(this._self, this._then);

  final HostedServiceRuntimeServiceStatus _self;
  final $Res Function(HostedServiceRuntimeServiceStatus) _then;

/// Create a copy of HostedServiceRuntimeServiceStatus
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? serviceName = null,Object? endpointRefs = null,Object? streamEndpointRefs = null,}) {
  return _then(_self.copyWith(
serviceName: null == serviceName ? _self.serviceName : serviceName // ignore: cast_nullable_to_non_nullable
as String,endpointRefs: null == endpointRefs ? _self.endpointRefs : endpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,streamEndpointRefs: null == streamEndpointRefs ? _self.streamEndpointRefs : streamEndpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,
  ));
}

}


/// Adds pattern-matching-related methods to [HostedServiceRuntimeServiceStatus].
extension HostedServiceRuntimeServiceStatusPatterns on HostedServiceRuntimeServiceStatus {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _HostedServiceRuntimeServiceStatus value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _HostedServiceRuntimeServiceStatus() when def != null:
return def(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _HostedServiceRuntimeServiceStatus value)  def,}){
final _that = this;
switch (_that) {
case _HostedServiceRuntimeServiceStatus():
return def(_that);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _HostedServiceRuntimeServiceStatus value)?  def,}){
final _that = this;
switch (_that) {
case _HostedServiceRuntimeServiceStatus() when def != null:
return def(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String serviceName,  List<String> endpointRefs,  List<String> streamEndpointRefs)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _HostedServiceRuntimeServiceStatus() when def != null:
return def(_that.serviceName,_that.endpointRefs,_that.streamEndpointRefs);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String serviceName,  List<String> endpointRefs,  List<String> streamEndpointRefs)  def,}) {final _that = this;
switch (_that) {
case _HostedServiceRuntimeServiceStatus():
return def(_that.serviceName,_that.endpointRefs,_that.streamEndpointRefs);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String serviceName,  List<String> endpointRefs,  List<String> streamEndpointRefs)?  def,}) {final _that = this;
switch (_that) {
case _HostedServiceRuntimeServiceStatus() when def != null:
return def(_that.serviceName,_that.endpointRefs,_that.streamEndpointRefs);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _HostedServiceRuntimeServiceStatus implements HostedServiceRuntimeServiceStatus {
   _HostedServiceRuntimeServiceStatus({required this.serviceName, final  List<String> endpointRefs = const [], final  List<String> streamEndpointRefs = const []}): _endpointRefs = endpointRefs,_streamEndpointRefs = streamEndpointRefs;
  factory _HostedServiceRuntimeServiceStatus.fromJson(Map<String, dynamic> json) => _$HostedServiceRuntimeServiceStatusFromJson(json);

@override final  String serviceName;
 final  List<String> _endpointRefs;
@override@JsonKey() List<String> get endpointRefs {
  if (_endpointRefs is EqualUnmodifiableListView) return _endpointRefs;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_endpointRefs);
}

 final  List<String> _streamEndpointRefs;
@override@JsonKey() List<String> get streamEndpointRefs {
  if (_streamEndpointRefs is EqualUnmodifiableListView) return _streamEndpointRefs;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_streamEndpointRefs);
}


/// Create a copy of HostedServiceRuntimeServiceStatus
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$HostedServiceRuntimeServiceStatusCopyWith<_HostedServiceRuntimeServiceStatus> get copyWith => __$HostedServiceRuntimeServiceStatusCopyWithImpl<_HostedServiceRuntimeServiceStatus>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$HostedServiceRuntimeServiceStatusToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _HostedServiceRuntimeServiceStatus&&(identical(other.serviceName, serviceName) || other.serviceName == serviceName)&&const DeepCollectionEquality().equals(other._endpointRefs, _endpointRefs)&&const DeepCollectionEquality().equals(other._streamEndpointRefs, _streamEndpointRefs));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,serviceName,const DeepCollectionEquality().hash(_endpointRefs),const DeepCollectionEquality().hash(_streamEndpointRefs));

@override
String toString() {
  return 'HostedServiceRuntimeServiceStatus.def(serviceName: $serviceName, endpointRefs: $endpointRefs, streamEndpointRefs: $streamEndpointRefs)';
}


}

/// @nodoc
abstract mixin class _$HostedServiceRuntimeServiceStatusCopyWith<$Res> implements $HostedServiceRuntimeServiceStatusCopyWith<$Res> {
  factory _$HostedServiceRuntimeServiceStatusCopyWith(_HostedServiceRuntimeServiceStatus value, $Res Function(_HostedServiceRuntimeServiceStatus) _then) = __$HostedServiceRuntimeServiceStatusCopyWithImpl;
@override @useResult
$Res call({
 String serviceName, List<String> endpointRefs, List<String> streamEndpointRefs
});




}
/// @nodoc
class __$HostedServiceRuntimeServiceStatusCopyWithImpl<$Res>
    implements _$HostedServiceRuntimeServiceStatusCopyWith<$Res> {
  __$HostedServiceRuntimeServiceStatusCopyWithImpl(this._self, this._then);

  final _HostedServiceRuntimeServiceStatus _self;
  final $Res Function(_HostedServiceRuntimeServiceStatus) _then;

/// Create a copy of HostedServiceRuntimeServiceStatus
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? serviceName = null,Object? endpointRefs = null,Object? streamEndpointRefs = null,}) {
  return _then(_HostedServiceRuntimeServiceStatus(
serviceName: null == serviceName ? _self.serviceName : serviceName // ignore: cast_nullable_to_non_nullable
as String,endpointRefs: null == endpointRefs ? _self._endpointRefs : endpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,streamEndpointRefs: null == streamEndpointRefs ? _self._streamEndpointRefs : streamEndpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,
  ));
}


}


/// @nodoc
mixin _$HostedServiceRuntimeStatus {

 String get hostId; String? get hostVersion; String get protocolVersion; String get readinessStatus; bool get isReady; bool get isAlive; bool get supportsStreamEvents; String? get summary; String? get error; String? get updatedAt; List<HostedServiceRuntimeServiceStatus> get services;
/// Create a copy of HostedServiceRuntimeStatus
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$HostedServiceRuntimeStatusCopyWith<HostedServiceRuntimeStatus> get copyWith => _$HostedServiceRuntimeStatusCopyWithImpl<HostedServiceRuntimeStatus>(this as HostedServiceRuntimeStatus, _$identity);

  /// Serializes this HostedServiceRuntimeStatus to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is HostedServiceRuntimeStatus&&(identical(other.hostId, hostId) || other.hostId == hostId)&&(identical(other.hostVersion, hostVersion) || other.hostVersion == hostVersion)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.readinessStatus, readinessStatus) || other.readinessStatus == readinessStatus)&&(identical(other.isReady, isReady) || other.isReady == isReady)&&(identical(other.isAlive, isAlive) || other.isAlive == isAlive)&&(identical(other.supportsStreamEvents, supportsStreamEvents) || other.supportsStreamEvents == supportsStreamEvents)&&(identical(other.summary, summary) || other.summary == summary)&&(identical(other.error, error) || other.error == error)&&(identical(other.updatedAt, updatedAt) || other.updatedAt == updatedAt)&&const DeepCollectionEquality().equals(other.services, services));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,hostId,hostVersion,protocolVersion,readinessStatus,isReady,isAlive,supportsStreamEvents,summary,error,updatedAt,const DeepCollectionEquality().hash(services));

@override
String toString() {
  return 'HostedServiceRuntimeStatus(hostId: $hostId, hostVersion: $hostVersion, protocolVersion: $protocolVersion, readinessStatus: $readinessStatus, isReady: $isReady, isAlive: $isAlive, supportsStreamEvents: $supportsStreamEvents, summary: $summary, error: $error, updatedAt: $updatedAt, services: $services)';
}


}

/// @nodoc
abstract mixin class $HostedServiceRuntimeStatusCopyWith<$Res>  {
  factory $HostedServiceRuntimeStatusCopyWith(HostedServiceRuntimeStatus value, $Res Function(HostedServiceRuntimeStatus) _then) = _$HostedServiceRuntimeStatusCopyWithImpl;
@useResult
$Res call({
 String hostId, String? hostVersion, String protocolVersion, String readinessStatus, bool isReady, bool isAlive, bool supportsStreamEvents, String? summary, String? error, String? updatedAt, List<HostedServiceRuntimeServiceStatus> services
});




}
/// @nodoc
class _$HostedServiceRuntimeStatusCopyWithImpl<$Res>
    implements $HostedServiceRuntimeStatusCopyWith<$Res> {
  _$HostedServiceRuntimeStatusCopyWithImpl(this._self, this._then);

  final HostedServiceRuntimeStatus _self;
  final $Res Function(HostedServiceRuntimeStatus) _then;

/// Create a copy of HostedServiceRuntimeStatus
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? hostId = null,Object? hostVersion = freezed,Object? protocolVersion = null,Object? readinessStatus = null,Object? isReady = null,Object? isAlive = null,Object? supportsStreamEvents = null,Object? summary = freezed,Object? error = freezed,Object? updatedAt = freezed,Object? services = null,}) {
  return _then(_self.copyWith(
hostId: null == hostId ? _self.hostId : hostId // ignore: cast_nullable_to_non_nullable
as String,hostVersion: freezed == hostVersion ? _self.hostVersion : hostVersion // ignore: cast_nullable_to_non_nullable
as String?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as String,readinessStatus: null == readinessStatus ? _self.readinessStatus : readinessStatus // ignore: cast_nullable_to_non_nullable
as String,isReady: null == isReady ? _self.isReady : isReady // ignore: cast_nullable_to_non_nullable
as bool,isAlive: null == isAlive ? _self.isAlive : isAlive // ignore: cast_nullable_to_non_nullable
as bool,supportsStreamEvents: null == supportsStreamEvents ? _self.supportsStreamEvents : supportsStreamEvents // ignore: cast_nullable_to_non_nullable
as bool,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,updatedAt: freezed == updatedAt ? _self.updatedAt : updatedAt // ignore: cast_nullable_to_non_nullable
as String?,services: null == services ? _self.services : services // ignore: cast_nullable_to_non_nullable
as List<HostedServiceRuntimeServiceStatus>,
  ));
}

}


/// Adds pattern-matching-related methods to [HostedServiceRuntimeStatus].
extension HostedServiceRuntimeStatusPatterns on HostedServiceRuntimeStatus {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _HostedServiceRuntimeStatus value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _HostedServiceRuntimeStatus() when def != null:
return def(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _HostedServiceRuntimeStatus value)  def,}){
final _that = this;
switch (_that) {
case _HostedServiceRuntimeStatus():
return def(_that);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _HostedServiceRuntimeStatus value)?  def,}){
final _that = this;
switch (_that) {
case _HostedServiceRuntimeStatus() when def != null:
return def(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String hostId,  String? hostVersion,  String protocolVersion,  String readinessStatus,  bool isReady,  bool isAlive,  bool supportsStreamEvents,  String? summary,  String? error,  String? updatedAt,  List<HostedServiceRuntimeServiceStatus> services)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _HostedServiceRuntimeStatus() when def != null:
return def(_that.hostId,_that.hostVersion,_that.protocolVersion,_that.readinessStatus,_that.isReady,_that.isAlive,_that.supportsStreamEvents,_that.summary,_that.error,_that.updatedAt,_that.services);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String hostId,  String? hostVersion,  String protocolVersion,  String readinessStatus,  bool isReady,  bool isAlive,  bool supportsStreamEvents,  String? summary,  String? error,  String? updatedAt,  List<HostedServiceRuntimeServiceStatus> services)  def,}) {final _that = this;
switch (_that) {
case _HostedServiceRuntimeStatus():
return def(_that.hostId,_that.hostVersion,_that.protocolVersion,_that.readinessStatus,_that.isReady,_that.isAlive,_that.supportsStreamEvents,_that.summary,_that.error,_that.updatedAt,_that.services);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String hostId,  String? hostVersion,  String protocolVersion,  String readinessStatus,  bool isReady,  bool isAlive,  bool supportsStreamEvents,  String? summary,  String? error,  String? updatedAt,  List<HostedServiceRuntimeServiceStatus> services)?  def,}) {final _that = this;
switch (_that) {
case _HostedServiceRuntimeStatus() when def != null:
return def(_that.hostId,_that.hostVersion,_that.protocolVersion,_that.readinessStatus,_that.isReady,_that.isAlive,_that.supportsStreamEvents,_that.summary,_that.error,_that.updatedAt,_that.services);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _HostedServiceRuntimeStatus implements HostedServiceRuntimeStatus {
   _HostedServiceRuntimeStatus({required this.hostId, this.hostVersion, required this.protocolVersion, required this.readinessStatus, required this.isReady, required this.isAlive, required this.supportsStreamEvents, this.summary, this.error, this.updatedAt, final  List<HostedServiceRuntimeServiceStatus> services = const []}): _services = services;
  factory _HostedServiceRuntimeStatus.fromJson(Map<String, dynamic> json) => _$HostedServiceRuntimeStatusFromJson(json);

@override final  String hostId;
@override final  String? hostVersion;
@override final  String protocolVersion;
@override final  String readinessStatus;
@override final  bool isReady;
@override final  bool isAlive;
@override final  bool supportsStreamEvents;
@override final  String? summary;
@override final  String? error;
@override final  String? updatedAt;
 final  List<HostedServiceRuntimeServiceStatus> _services;
@override@JsonKey() List<HostedServiceRuntimeServiceStatus> get services {
  if (_services is EqualUnmodifiableListView) return _services;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_services);
}


/// Create a copy of HostedServiceRuntimeStatus
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$HostedServiceRuntimeStatusCopyWith<_HostedServiceRuntimeStatus> get copyWith => __$HostedServiceRuntimeStatusCopyWithImpl<_HostedServiceRuntimeStatus>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$HostedServiceRuntimeStatusToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _HostedServiceRuntimeStatus&&(identical(other.hostId, hostId) || other.hostId == hostId)&&(identical(other.hostVersion, hostVersion) || other.hostVersion == hostVersion)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.readinessStatus, readinessStatus) || other.readinessStatus == readinessStatus)&&(identical(other.isReady, isReady) || other.isReady == isReady)&&(identical(other.isAlive, isAlive) || other.isAlive == isAlive)&&(identical(other.supportsStreamEvents, supportsStreamEvents) || other.supportsStreamEvents == supportsStreamEvents)&&(identical(other.summary, summary) || other.summary == summary)&&(identical(other.error, error) || other.error == error)&&(identical(other.updatedAt, updatedAt) || other.updatedAt == updatedAt)&&const DeepCollectionEquality().equals(other._services, _services));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,hostId,hostVersion,protocolVersion,readinessStatus,isReady,isAlive,supportsStreamEvents,summary,error,updatedAt,const DeepCollectionEquality().hash(_services));

@override
String toString() {
  return 'HostedServiceRuntimeStatus.def(hostId: $hostId, hostVersion: $hostVersion, protocolVersion: $protocolVersion, readinessStatus: $readinessStatus, isReady: $isReady, isAlive: $isAlive, supportsStreamEvents: $supportsStreamEvents, summary: $summary, error: $error, updatedAt: $updatedAt, services: $services)';
}


}

/// @nodoc
abstract mixin class _$HostedServiceRuntimeStatusCopyWith<$Res> implements $HostedServiceRuntimeStatusCopyWith<$Res> {
  factory _$HostedServiceRuntimeStatusCopyWith(_HostedServiceRuntimeStatus value, $Res Function(_HostedServiceRuntimeStatus) _then) = __$HostedServiceRuntimeStatusCopyWithImpl;
@override @useResult
$Res call({
 String hostId, String? hostVersion, String protocolVersion, String readinessStatus, bool isReady, bool isAlive, bool supportsStreamEvents, String? summary, String? error, String? updatedAt, List<HostedServiceRuntimeServiceStatus> services
});




}
/// @nodoc
class __$HostedServiceRuntimeStatusCopyWithImpl<$Res>
    implements _$HostedServiceRuntimeStatusCopyWith<$Res> {
  __$HostedServiceRuntimeStatusCopyWithImpl(this._self, this._then);

  final _HostedServiceRuntimeStatus _self;
  final $Res Function(_HostedServiceRuntimeStatus) _then;

/// Create a copy of HostedServiceRuntimeStatus
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? hostId = null,Object? hostVersion = freezed,Object? protocolVersion = null,Object? readinessStatus = null,Object? isReady = null,Object? isAlive = null,Object? supportsStreamEvents = null,Object? summary = freezed,Object? error = freezed,Object? updatedAt = freezed,Object? services = null,}) {
  return _then(_HostedServiceRuntimeStatus(
hostId: null == hostId ? _self.hostId : hostId // ignore: cast_nullable_to_non_nullable
as String,hostVersion: freezed == hostVersion ? _self.hostVersion : hostVersion // ignore: cast_nullable_to_non_nullable
as String?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as String,readinessStatus: null == readinessStatus ? _self.readinessStatus : readinessStatus // ignore: cast_nullable_to_non_nullable
as String,isReady: null == isReady ? _self.isReady : isReady // ignore: cast_nullable_to_non_nullable
as bool,isAlive: null == isAlive ? _self.isAlive : isAlive // ignore: cast_nullable_to_non_nullable
as bool,supportsStreamEvents: null == supportsStreamEvents ? _self.supportsStreamEvents : supportsStreamEvents // ignore: cast_nullable_to_non_nullable
as bool,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,updatedAt: freezed == updatedAt ? _self.updatedAt : updatedAt // ignore: cast_nullable_to_non_nullable
as String?,services: null == services ? _self._services : services // ignore: cast_nullable_to_non_nullable
as List<HostedServiceRuntimeServiceStatus>,
  ));
}


}

// dart format on
