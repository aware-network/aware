// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'network_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$NetworkRequest {

@UuidValueConverter() UuidValue? get id;@JsonKey(fromJson: NetworkRequestStatusExtension.fromJson, toJson: NetworkRequestStatusExtension.toJson) NetworkRequestStatus get status;@UuidValueConverter() UuidValue? get requesterId; Map<String, dynamic>? get requester;
/// Create a copy of NetworkRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkRequestCopyWith<NetworkRequest> get copyWith => _$NetworkRequestCopyWithImpl<NetworkRequest>(this as NetworkRequest, _$identity);

  /// Serializes this NetworkRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkRequest&&(identical(other.id, id) || other.id == id)&&(identical(other.status, status) || other.status == status)&&(identical(other.requesterId, requesterId) || other.requesterId == requesterId)&&const DeepCollectionEquality().equals(other.requester, requester));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,status,requesterId,const DeepCollectionEquality().hash(requester));

@override
String toString() {
  return 'NetworkRequest(id: $id, status: $status, requesterId: $requesterId, requester: $requester)';
}


}

/// @nodoc
abstract mixin class $NetworkRequestCopyWith<$Res>  {
  factory $NetworkRequestCopyWith(NetworkRequest value, $Res Function(NetworkRequest) _then) = _$NetworkRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? id,@JsonKey(fromJson: NetworkRequestStatusExtension.fromJson, toJson: NetworkRequestStatusExtension.toJson) NetworkRequestStatus status,@UuidValueConverter() UuidValue? requesterId, Map<String, dynamic>? requester
});




}
/// @nodoc
class _$NetworkRequestCopyWithImpl<$Res>
    implements $NetworkRequestCopyWith<$Res> {
  _$NetworkRequestCopyWithImpl(this._self, this._then);

  final NetworkRequest _self;
  final $Res Function(NetworkRequest) _then;

/// Create a copy of NetworkRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? id = freezed,Object? status = null,Object? requesterId = freezed,Object? requester = freezed,}) {
  return _then(_self.copyWith(
id: freezed == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as NetworkRequestStatus,requesterId: freezed == requesterId ? _self.requesterId : requesterId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requester: freezed == requester ? _self.requester : requester // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkRequest].
extension NetworkRequestPatterns on NetworkRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkRequest value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkRequest() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkRequest value)  def,}){
final _that = this;
switch (_that) {
case _NetworkRequest():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkRequest value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkRequest() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? id, @JsonKey(fromJson: NetworkRequestStatusExtension.fromJson, toJson: NetworkRequestStatusExtension.toJson)  NetworkRequestStatus status, @UuidValueConverter()  UuidValue? requesterId,  Map<String, dynamic>? requester)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkRequest() when def != null:
return def(_that.id,_that.status,_that.requesterId,_that.requester);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? id, @JsonKey(fromJson: NetworkRequestStatusExtension.fromJson, toJson: NetworkRequestStatusExtension.toJson)  NetworkRequestStatus status, @UuidValueConverter()  UuidValue? requesterId,  Map<String, dynamic>? requester)  def,}) {final _that = this;
switch (_that) {
case _NetworkRequest():
return def(_that.id,_that.status,_that.requesterId,_that.requester);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? id, @JsonKey(fromJson: NetworkRequestStatusExtension.fromJson, toJson: NetworkRequestStatusExtension.toJson)  NetworkRequestStatus status, @UuidValueConverter()  UuidValue? requesterId,  Map<String, dynamic>? requester)?  def,}) {final _that = this;
switch (_that) {
case _NetworkRequest() when def != null:
return def(_that.id,_that.status,_that.requesterId,_that.requester);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkRequest implements NetworkRequest {
   _NetworkRequest({@UuidValueConverter() this.id, @JsonKey(fromJson: NetworkRequestStatusExtension.fromJson, toJson: NetworkRequestStatusExtension.toJson) required this.status, @UuidValueConverter() this.requesterId, final  Map<String, dynamic>? requester}): _requester = requester;
  factory _NetworkRequest.fromJson(Map<String, dynamic> json) => _$NetworkRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? id;
@override@JsonKey(fromJson: NetworkRequestStatusExtension.fromJson, toJson: NetworkRequestStatusExtension.toJson) final  NetworkRequestStatus status;
@override@UuidValueConverter() final  UuidValue? requesterId;
 final  Map<String, dynamic>? _requester;
@override Map<String, dynamic>? get requester {
  final value = _requester;
  if (value == null) return null;
  if (_requester is EqualUnmodifiableMapView) return _requester;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(value);
}


/// Create a copy of NetworkRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkRequestCopyWith<_NetworkRequest> get copyWith => __$NetworkRequestCopyWithImpl<_NetworkRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkRequest&&(identical(other.id, id) || other.id == id)&&(identical(other.status, status) || other.status == status)&&(identical(other.requesterId, requesterId) || other.requesterId == requesterId)&&const DeepCollectionEquality().equals(other._requester, _requester));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,status,requesterId,const DeepCollectionEquality().hash(_requester));

@override
String toString() {
  return 'NetworkRequest.def(id: $id, status: $status, requesterId: $requesterId, requester: $requester)';
}


}

/// @nodoc
abstract mixin class _$NetworkRequestCopyWith<$Res> implements $NetworkRequestCopyWith<$Res> {
  factory _$NetworkRequestCopyWith(_NetworkRequest value, $Res Function(_NetworkRequest) _then) = __$NetworkRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? id,@JsonKey(fromJson: NetworkRequestStatusExtension.fromJson, toJson: NetworkRequestStatusExtension.toJson) NetworkRequestStatus status,@UuidValueConverter() UuidValue? requesterId, Map<String, dynamic>? requester
});




}
/// @nodoc
class __$NetworkRequestCopyWithImpl<$Res>
    implements _$NetworkRequestCopyWith<$Res> {
  __$NetworkRequestCopyWithImpl(this._self, this._then);

  final _NetworkRequest _self;
  final $Res Function(_NetworkRequest) _then;

/// Create a copy of NetworkRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? id = freezed,Object? status = null,Object? requesterId = freezed,Object? requester = freezed,}) {
  return _then(_NetworkRequest(
id: freezed == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as NetworkRequestStatus,requesterId: freezed == requesterId ? _self.requesterId : requesterId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requester: freezed == requester ? _self._requester : requester // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>?,
  ));
}


}


/// @nodoc
mixin _$NetworkResponse {

@UuidValueConverter() UuidValue? get id;@JsonKey(fromJson: NetworkRequestStatusExtension.fromJson, toJson: NetworkRequestStatusExtension.toJson) NetworkRequestStatus get status; String? get error;@UuidValueConverter() UuidValue? get networkRequestId;
/// Create a copy of NetworkResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkResponseCopyWith<NetworkResponse> get copyWith => _$NetworkResponseCopyWithImpl<NetworkResponse>(this as NetworkResponse, _$identity);

  /// Serializes this NetworkResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkResponse&&(identical(other.id, id) || other.id == id)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.networkRequestId, networkRequestId) || other.networkRequestId == networkRequestId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,status,error,networkRequestId);

@override
String toString() {
  return 'NetworkResponse(id: $id, status: $status, error: $error, networkRequestId: $networkRequestId)';
}


}

/// @nodoc
abstract mixin class $NetworkResponseCopyWith<$Res>  {
  factory $NetworkResponseCopyWith(NetworkResponse value, $Res Function(NetworkResponse) _then) = _$NetworkResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? id,@JsonKey(fromJson: NetworkRequestStatusExtension.fromJson, toJson: NetworkRequestStatusExtension.toJson) NetworkRequestStatus status, String? error,@UuidValueConverter() UuidValue? networkRequestId
});




}
/// @nodoc
class _$NetworkResponseCopyWithImpl<$Res>
    implements $NetworkResponseCopyWith<$Res> {
  _$NetworkResponseCopyWithImpl(this._self, this._then);

  final NetworkResponse _self;
  final $Res Function(NetworkResponse) _then;

/// Create a copy of NetworkResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? id = freezed,Object? status = null,Object? error = freezed,Object? networkRequestId = freezed,}) {
  return _then(_self.copyWith(
id: freezed == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as NetworkRequestStatus,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,networkRequestId: freezed == networkRequestId ? _self.networkRequestId : networkRequestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkResponse].
extension NetworkResponsePatterns on NetworkResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkResponse value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkResponse() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkResponse value)  def,}){
final _that = this;
switch (_that) {
case _NetworkResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkResponse value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkResponse() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? id, @JsonKey(fromJson: NetworkRequestStatusExtension.fromJson, toJson: NetworkRequestStatusExtension.toJson)  NetworkRequestStatus status,  String? error, @UuidValueConverter()  UuidValue? networkRequestId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkResponse() when def != null:
return def(_that.id,_that.status,_that.error,_that.networkRequestId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? id, @JsonKey(fromJson: NetworkRequestStatusExtension.fromJson, toJson: NetworkRequestStatusExtension.toJson)  NetworkRequestStatus status,  String? error, @UuidValueConverter()  UuidValue? networkRequestId)  def,}) {final _that = this;
switch (_that) {
case _NetworkResponse():
return def(_that.id,_that.status,_that.error,_that.networkRequestId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? id, @JsonKey(fromJson: NetworkRequestStatusExtension.fromJson, toJson: NetworkRequestStatusExtension.toJson)  NetworkRequestStatus status,  String? error, @UuidValueConverter()  UuidValue? networkRequestId)?  def,}) {final _that = this;
switch (_that) {
case _NetworkResponse() when def != null:
return def(_that.id,_that.status,_that.error,_that.networkRequestId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkResponse implements NetworkResponse {
   _NetworkResponse({@UuidValueConverter() this.id, @JsonKey(fromJson: NetworkRequestStatusExtension.fromJson, toJson: NetworkRequestStatusExtension.toJson) required this.status, this.error, @UuidValueConverter() this.networkRequestId});
  factory _NetworkResponse.fromJson(Map<String, dynamic> json) => _$NetworkResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? id;
@override@JsonKey(fromJson: NetworkRequestStatusExtension.fromJson, toJson: NetworkRequestStatusExtension.toJson) final  NetworkRequestStatus status;
@override final  String? error;
@override@UuidValueConverter() final  UuidValue? networkRequestId;

/// Create a copy of NetworkResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkResponseCopyWith<_NetworkResponse> get copyWith => __$NetworkResponseCopyWithImpl<_NetworkResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkResponse&&(identical(other.id, id) || other.id == id)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.networkRequestId, networkRequestId) || other.networkRequestId == networkRequestId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,status,error,networkRequestId);

@override
String toString() {
  return 'NetworkResponse.def(id: $id, status: $status, error: $error, networkRequestId: $networkRequestId)';
}


}

/// @nodoc
abstract mixin class _$NetworkResponseCopyWith<$Res> implements $NetworkResponseCopyWith<$Res> {
  factory _$NetworkResponseCopyWith(_NetworkResponse value, $Res Function(_NetworkResponse) _then) = __$NetworkResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? id,@JsonKey(fromJson: NetworkRequestStatusExtension.fromJson, toJson: NetworkRequestStatusExtension.toJson) NetworkRequestStatus status, String? error,@UuidValueConverter() UuidValue? networkRequestId
});




}
/// @nodoc
class __$NetworkResponseCopyWithImpl<$Res>
    implements _$NetworkResponseCopyWith<$Res> {
  __$NetworkResponseCopyWithImpl(this._self, this._then);

  final _NetworkResponse _self;
  final $Res Function(_NetworkResponse) _then;

/// Create a copy of NetworkResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? id = freezed,Object? status = null,Object? error = freezed,Object? networkRequestId = freezed,}) {
  return _then(_NetworkResponse(
id: freezed == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as NetworkRequestStatus,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,networkRequestId: freezed == networkRequestId ? _self.networkRequestId : networkRequestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}


}


/// @nodoc
mixin _$NetworkOperationHop {

@JsonKey(fromJson: NetworkAppTypeExtension.fromJson, toJson: NetworkAppTypeExtension.toJson) NetworkAppType get sourceAppType;@JsonKey(fromJson: NetworkAppTypeExtension.fromJson, toJson: NetworkAppTypeExtension.toJson) NetworkAppType get targetAppType;@UuidValueConverter() UuidValue? get sourceNodeId;@UuidValueConverter() UuidValue? get sourceInterfaceId;@UuidValueConverter() UuidValue? get sourceEnvironmentId;@UuidValueConverter() UuidValue? get targetNodeId;@UuidValueConverter() UuidValue? get targetInterfaceId;@UuidValueConverter() UuidValue? get targetEnvironmentId;
/// Create a copy of NetworkOperationHop
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkOperationHopCopyWith<NetworkOperationHop> get copyWith => _$NetworkOperationHopCopyWithImpl<NetworkOperationHop>(this as NetworkOperationHop, _$identity);

  /// Serializes this NetworkOperationHop to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkOperationHop&&(identical(other.sourceAppType, sourceAppType) || other.sourceAppType == sourceAppType)&&(identical(other.targetAppType, targetAppType) || other.targetAppType == targetAppType)&&(identical(other.sourceNodeId, sourceNodeId) || other.sourceNodeId == sourceNodeId)&&(identical(other.sourceInterfaceId, sourceInterfaceId) || other.sourceInterfaceId == sourceInterfaceId)&&(identical(other.sourceEnvironmentId, sourceEnvironmentId) || other.sourceEnvironmentId == sourceEnvironmentId)&&(identical(other.targetNodeId, targetNodeId) || other.targetNodeId == targetNodeId)&&(identical(other.targetInterfaceId, targetInterfaceId) || other.targetInterfaceId == targetInterfaceId)&&(identical(other.targetEnvironmentId, targetEnvironmentId) || other.targetEnvironmentId == targetEnvironmentId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,sourceAppType,targetAppType,sourceNodeId,sourceInterfaceId,sourceEnvironmentId,targetNodeId,targetInterfaceId,targetEnvironmentId);

@override
String toString() {
  return 'NetworkOperationHop(sourceAppType: $sourceAppType, targetAppType: $targetAppType, sourceNodeId: $sourceNodeId, sourceInterfaceId: $sourceInterfaceId, sourceEnvironmentId: $sourceEnvironmentId, targetNodeId: $targetNodeId, targetInterfaceId: $targetInterfaceId, targetEnvironmentId: $targetEnvironmentId)';
}


}

/// @nodoc
abstract mixin class $NetworkOperationHopCopyWith<$Res>  {
  factory $NetworkOperationHopCopyWith(NetworkOperationHop value, $Res Function(NetworkOperationHop) _then) = _$NetworkOperationHopCopyWithImpl;
@useResult
$Res call({
@JsonKey(fromJson: NetworkAppTypeExtension.fromJson, toJson: NetworkAppTypeExtension.toJson) NetworkAppType sourceAppType,@JsonKey(fromJson: NetworkAppTypeExtension.fromJson, toJson: NetworkAppTypeExtension.toJson) NetworkAppType targetAppType,@UuidValueConverter() UuidValue? sourceNodeId,@UuidValueConverter() UuidValue? sourceInterfaceId,@UuidValueConverter() UuidValue? sourceEnvironmentId,@UuidValueConverter() UuidValue? targetNodeId,@UuidValueConverter() UuidValue? targetInterfaceId,@UuidValueConverter() UuidValue? targetEnvironmentId
});




}
/// @nodoc
class _$NetworkOperationHopCopyWithImpl<$Res>
    implements $NetworkOperationHopCopyWith<$Res> {
  _$NetworkOperationHopCopyWithImpl(this._self, this._then);

  final NetworkOperationHop _self;
  final $Res Function(NetworkOperationHop) _then;

/// Create a copy of NetworkOperationHop
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? sourceAppType = null,Object? targetAppType = null,Object? sourceNodeId = freezed,Object? sourceInterfaceId = freezed,Object? sourceEnvironmentId = freezed,Object? targetNodeId = freezed,Object? targetInterfaceId = freezed,Object? targetEnvironmentId = freezed,}) {
  return _then(_self.copyWith(
sourceAppType: null == sourceAppType ? _self.sourceAppType : sourceAppType // ignore: cast_nullable_to_non_nullable
as NetworkAppType,targetAppType: null == targetAppType ? _self.targetAppType : targetAppType // ignore: cast_nullable_to_non_nullable
as NetworkAppType,sourceNodeId: freezed == sourceNodeId ? _self.sourceNodeId : sourceNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sourceInterfaceId: freezed == sourceInterfaceId ? _self.sourceInterfaceId : sourceInterfaceId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sourceEnvironmentId: freezed == sourceEnvironmentId ? _self.sourceEnvironmentId : sourceEnvironmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,targetNodeId: freezed == targetNodeId ? _self.targetNodeId : targetNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,targetInterfaceId: freezed == targetInterfaceId ? _self.targetInterfaceId : targetInterfaceId // ignore: cast_nullable_to_non_nullable
as UuidValue?,targetEnvironmentId: freezed == targetEnvironmentId ? _self.targetEnvironmentId : targetEnvironmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkOperationHop].
extension NetworkOperationHopPatterns on NetworkOperationHop {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkOperationHop value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkOperationHop() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkOperationHop value)  def,}){
final _that = this;
switch (_that) {
case _NetworkOperationHop():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkOperationHop value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkOperationHop() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@JsonKey(fromJson: NetworkAppTypeExtension.fromJson, toJson: NetworkAppTypeExtension.toJson)  NetworkAppType sourceAppType, @JsonKey(fromJson: NetworkAppTypeExtension.fromJson, toJson: NetworkAppTypeExtension.toJson)  NetworkAppType targetAppType, @UuidValueConverter()  UuidValue? sourceNodeId, @UuidValueConverter()  UuidValue? sourceInterfaceId, @UuidValueConverter()  UuidValue? sourceEnvironmentId, @UuidValueConverter()  UuidValue? targetNodeId, @UuidValueConverter()  UuidValue? targetInterfaceId, @UuidValueConverter()  UuidValue? targetEnvironmentId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkOperationHop() when def != null:
return def(_that.sourceAppType,_that.targetAppType,_that.sourceNodeId,_that.sourceInterfaceId,_that.sourceEnvironmentId,_that.targetNodeId,_that.targetInterfaceId,_that.targetEnvironmentId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@JsonKey(fromJson: NetworkAppTypeExtension.fromJson, toJson: NetworkAppTypeExtension.toJson)  NetworkAppType sourceAppType, @JsonKey(fromJson: NetworkAppTypeExtension.fromJson, toJson: NetworkAppTypeExtension.toJson)  NetworkAppType targetAppType, @UuidValueConverter()  UuidValue? sourceNodeId, @UuidValueConverter()  UuidValue? sourceInterfaceId, @UuidValueConverter()  UuidValue? sourceEnvironmentId, @UuidValueConverter()  UuidValue? targetNodeId, @UuidValueConverter()  UuidValue? targetInterfaceId, @UuidValueConverter()  UuidValue? targetEnvironmentId)  def,}) {final _that = this;
switch (_that) {
case _NetworkOperationHop():
return def(_that.sourceAppType,_that.targetAppType,_that.sourceNodeId,_that.sourceInterfaceId,_that.sourceEnvironmentId,_that.targetNodeId,_that.targetInterfaceId,_that.targetEnvironmentId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@JsonKey(fromJson: NetworkAppTypeExtension.fromJson, toJson: NetworkAppTypeExtension.toJson)  NetworkAppType sourceAppType, @JsonKey(fromJson: NetworkAppTypeExtension.fromJson, toJson: NetworkAppTypeExtension.toJson)  NetworkAppType targetAppType, @UuidValueConverter()  UuidValue? sourceNodeId, @UuidValueConverter()  UuidValue? sourceInterfaceId, @UuidValueConverter()  UuidValue? sourceEnvironmentId, @UuidValueConverter()  UuidValue? targetNodeId, @UuidValueConverter()  UuidValue? targetInterfaceId, @UuidValueConverter()  UuidValue? targetEnvironmentId)?  def,}) {final _that = this;
switch (_that) {
case _NetworkOperationHop() when def != null:
return def(_that.sourceAppType,_that.targetAppType,_that.sourceNodeId,_that.sourceInterfaceId,_that.sourceEnvironmentId,_that.targetNodeId,_that.targetInterfaceId,_that.targetEnvironmentId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkOperationHop implements NetworkOperationHop {
   _NetworkOperationHop({@JsonKey(fromJson: NetworkAppTypeExtension.fromJson, toJson: NetworkAppTypeExtension.toJson) required this.sourceAppType, @JsonKey(fromJson: NetworkAppTypeExtension.fromJson, toJson: NetworkAppTypeExtension.toJson) required this.targetAppType, @UuidValueConverter() this.sourceNodeId, @UuidValueConverter() this.sourceInterfaceId, @UuidValueConverter() this.sourceEnvironmentId, @UuidValueConverter() this.targetNodeId, @UuidValueConverter() this.targetInterfaceId, @UuidValueConverter() this.targetEnvironmentId});
  factory _NetworkOperationHop.fromJson(Map<String, dynamic> json) => _$NetworkOperationHopFromJson(json);

@override@JsonKey(fromJson: NetworkAppTypeExtension.fromJson, toJson: NetworkAppTypeExtension.toJson) final  NetworkAppType sourceAppType;
@override@JsonKey(fromJson: NetworkAppTypeExtension.fromJson, toJson: NetworkAppTypeExtension.toJson) final  NetworkAppType targetAppType;
@override@UuidValueConverter() final  UuidValue? sourceNodeId;
@override@UuidValueConverter() final  UuidValue? sourceInterfaceId;
@override@UuidValueConverter() final  UuidValue? sourceEnvironmentId;
@override@UuidValueConverter() final  UuidValue? targetNodeId;
@override@UuidValueConverter() final  UuidValue? targetInterfaceId;
@override@UuidValueConverter() final  UuidValue? targetEnvironmentId;

/// Create a copy of NetworkOperationHop
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkOperationHopCopyWith<_NetworkOperationHop> get copyWith => __$NetworkOperationHopCopyWithImpl<_NetworkOperationHop>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkOperationHopToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkOperationHop&&(identical(other.sourceAppType, sourceAppType) || other.sourceAppType == sourceAppType)&&(identical(other.targetAppType, targetAppType) || other.targetAppType == targetAppType)&&(identical(other.sourceNodeId, sourceNodeId) || other.sourceNodeId == sourceNodeId)&&(identical(other.sourceInterfaceId, sourceInterfaceId) || other.sourceInterfaceId == sourceInterfaceId)&&(identical(other.sourceEnvironmentId, sourceEnvironmentId) || other.sourceEnvironmentId == sourceEnvironmentId)&&(identical(other.targetNodeId, targetNodeId) || other.targetNodeId == targetNodeId)&&(identical(other.targetInterfaceId, targetInterfaceId) || other.targetInterfaceId == targetInterfaceId)&&(identical(other.targetEnvironmentId, targetEnvironmentId) || other.targetEnvironmentId == targetEnvironmentId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,sourceAppType,targetAppType,sourceNodeId,sourceInterfaceId,sourceEnvironmentId,targetNodeId,targetInterfaceId,targetEnvironmentId);

@override
String toString() {
  return 'NetworkOperationHop.def(sourceAppType: $sourceAppType, targetAppType: $targetAppType, sourceNodeId: $sourceNodeId, sourceInterfaceId: $sourceInterfaceId, sourceEnvironmentId: $sourceEnvironmentId, targetNodeId: $targetNodeId, targetInterfaceId: $targetInterfaceId, targetEnvironmentId: $targetEnvironmentId)';
}


}

/// @nodoc
abstract mixin class _$NetworkOperationHopCopyWith<$Res> implements $NetworkOperationHopCopyWith<$Res> {
  factory _$NetworkOperationHopCopyWith(_NetworkOperationHop value, $Res Function(_NetworkOperationHop) _then) = __$NetworkOperationHopCopyWithImpl;
@override @useResult
$Res call({
@JsonKey(fromJson: NetworkAppTypeExtension.fromJson, toJson: NetworkAppTypeExtension.toJson) NetworkAppType sourceAppType,@JsonKey(fromJson: NetworkAppTypeExtension.fromJson, toJson: NetworkAppTypeExtension.toJson) NetworkAppType targetAppType,@UuidValueConverter() UuidValue? sourceNodeId,@UuidValueConverter() UuidValue? sourceInterfaceId,@UuidValueConverter() UuidValue? sourceEnvironmentId,@UuidValueConverter() UuidValue? targetNodeId,@UuidValueConverter() UuidValue? targetInterfaceId,@UuidValueConverter() UuidValue? targetEnvironmentId
});




}
/// @nodoc
class __$NetworkOperationHopCopyWithImpl<$Res>
    implements _$NetworkOperationHopCopyWith<$Res> {
  __$NetworkOperationHopCopyWithImpl(this._self, this._then);

  final _NetworkOperationHop _self;
  final $Res Function(_NetworkOperationHop) _then;

/// Create a copy of NetworkOperationHop
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? sourceAppType = null,Object? targetAppType = null,Object? sourceNodeId = freezed,Object? sourceInterfaceId = freezed,Object? sourceEnvironmentId = freezed,Object? targetNodeId = freezed,Object? targetInterfaceId = freezed,Object? targetEnvironmentId = freezed,}) {
  return _then(_NetworkOperationHop(
sourceAppType: null == sourceAppType ? _self.sourceAppType : sourceAppType // ignore: cast_nullable_to_non_nullable
as NetworkAppType,targetAppType: null == targetAppType ? _self.targetAppType : targetAppType // ignore: cast_nullable_to_non_nullable
as NetworkAppType,sourceNodeId: freezed == sourceNodeId ? _self.sourceNodeId : sourceNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sourceInterfaceId: freezed == sourceInterfaceId ? _self.sourceInterfaceId : sourceInterfaceId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sourceEnvironmentId: freezed == sourceEnvironmentId ? _self.sourceEnvironmentId : sourceEnvironmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,targetNodeId: freezed == targetNodeId ? _self.targetNodeId : targetNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,targetInterfaceId: freezed == targetInterfaceId ? _self.targetInterfaceId : targetInterfaceId // ignore: cast_nullable_to_non_nullable
as UuidValue?,targetEnvironmentId: freezed == targetEnvironmentId ? _self.targetEnvironmentId : targetEnvironmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}


}


/// @nodoc
mixin _$NetworkOperation {

@UuidValueConverter() UuidValue get id;@JsonKey(fromJson: NetworkOperationMessageTypeExtension.fromJson, toJson: NetworkOperationMessageTypeExtension.toJson) NetworkOperationMessageType get messageType;@JsonKey(fromJson: NetworkOperationTypeExtension.fromJson, toJson: NetworkOperationTypeExtension.toJson) NetworkOperationType get type; List<NetworkOperationHop> get networkOperationHopList; NetworkRequest? get networkRequest; NetworkResponse? get networkResponse; ApiOperation? get apiOperation; ServiceOperation? get serviceOperation; NetworkNodeOperation? get networkNodeOperation;
/// Create a copy of NetworkOperation
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkOperationCopyWith<NetworkOperation> get copyWith => _$NetworkOperationCopyWithImpl<NetworkOperation>(this as NetworkOperation, _$identity);

  /// Serializes this NetworkOperation to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkOperation&&(identical(other.id, id) || other.id == id)&&(identical(other.messageType, messageType) || other.messageType == messageType)&&(identical(other.type, type) || other.type == type)&&const DeepCollectionEquality().equals(other.networkOperationHopList, networkOperationHopList)&&(identical(other.networkRequest, networkRequest) || other.networkRequest == networkRequest)&&(identical(other.networkResponse, networkResponse) || other.networkResponse == networkResponse)&&(identical(other.apiOperation, apiOperation) || other.apiOperation == apiOperation)&&(identical(other.serviceOperation, serviceOperation) || other.serviceOperation == serviceOperation)&&(identical(other.networkNodeOperation, networkNodeOperation) || other.networkNodeOperation == networkNodeOperation));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,messageType,type,const DeepCollectionEquality().hash(networkOperationHopList),networkRequest,networkResponse,apiOperation,serviceOperation,networkNodeOperation);

@override
String toString() {
  return 'NetworkOperation(id: $id, messageType: $messageType, type: $type, networkOperationHopList: $networkOperationHopList, networkRequest: $networkRequest, networkResponse: $networkResponse, apiOperation: $apiOperation, serviceOperation: $serviceOperation, networkNodeOperation: $networkNodeOperation)';
}


}

/// @nodoc
abstract mixin class $NetworkOperationCopyWith<$Res>  {
  factory $NetworkOperationCopyWith(NetworkOperation value, $Res Function(NetworkOperation) _then) = _$NetworkOperationCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue id,@JsonKey(fromJson: NetworkOperationMessageTypeExtension.fromJson, toJson: NetworkOperationMessageTypeExtension.toJson) NetworkOperationMessageType messageType,@JsonKey(fromJson: NetworkOperationTypeExtension.fromJson, toJson: NetworkOperationTypeExtension.toJson) NetworkOperationType type, List<NetworkOperationHop> networkOperationHopList, NetworkRequest? networkRequest, NetworkResponse? networkResponse, ApiOperation? apiOperation, ServiceOperation? serviceOperation, NetworkNodeOperation? networkNodeOperation
});


$NetworkRequestCopyWith<$Res>? get networkRequest;$NetworkResponseCopyWith<$Res>? get networkResponse;$ApiOperationCopyWith<$Res>? get apiOperation;$ServiceOperationCopyWith<$Res>? get serviceOperation;$NetworkNodeOperationCopyWith<$Res>? get networkNodeOperation;

}
/// @nodoc
class _$NetworkOperationCopyWithImpl<$Res>
    implements $NetworkOperationCopyWith<$Res> {
  _$NetworkOperationCopyWithImpl(this._self, this._then);

  final NetworkOperation _self;
  final $Res Function(NetworkOperation) _then;

/// Create a copy of NetworkOperation
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? id = null,Object? messageType = null,Object? type = null,Object? networkOperationHopList = null,Object? networkRequest = freezed,Object? networkResponse = freezed,Object? apiOperation = freezed,Object? serviceOperation = freezed,Object? networkNodeOperation = freezed,}) {
  return _then(_self.copyWith(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,messageType: null == messageType ? _self.messageType : messageType // ignore: cast_nullable_to_non_nullable
as NetworkOperationMessageType,type: null == type ? _self.type : type // ignore: cast_nullable_to_non_nullable
as NetworkOperationType,networkOperationHopList: null == networkOperationHopList ? _self.networkOperationHopList : networkOperationHopList // ignore: cast_nullable_to_non_nullable
as List<NetworkOperationHop>,networkRequest: freezed == networkRequest ? _self.networkRequest : networkRequest // ignore: cast_nullable_to_non_nullable
as NetworkRequest?,networkResponse: freezed == networkResponse ? _self.networkResponse : networkResponse // ignore: cast_nullable_to_non_nullable
as NetworkResponse?,apiOperation: freezed == apiOperation ? _self.apiOperation : apiOperation // ignore: cast_nullable_to_non_nullable
as ApiOperation?,serviceOperation: freezed == serviceOperation ? _self.serviceOperation : serviceOperation // ignore: cast_nullable_to_non_nullable
as ServiceOperation?,networkNodeOperation: freezed == networkNodeOperation ? _self.networkNodeOperation : networkNodeOperation // ignore: cast_nullable_to_non_nullable
as NetworkNodeOperation?,
  ));
}
/// Create a copy of NetworkOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkRequestCopyWith<$Res>? get networkRequest {
    if (_self.networkRequest == null) {
    return null;
  }

  return $NetworkRequestCopyWith<$Res>(_self.networkRequest!, (value) {
    return _then(_self.copyWith(networkRequest: value));
  });
}/// Create a copy of NetworkOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkResponseCopyWith<$Res>? get networkResponse {
    if (_self.networkResponse == null) {
    return null;
  }

  return $NetworkResponseCopyWith<$Res>(_self.networkResponse!, (value) {
    return _then(_self.copyWith(networkResponse: value));
  });
}/// Create a copy of NetworkOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ApiOperationCopyWith<$Res>? get apiOperation {
    if (_self.apiOperation == null) {
    return null;
  }

  return $ApiOperationCopyWith<$Res>(_self.apiOperation!, (value) {
    return _then(_self.copyWith(apiOperation: value));
  });
}/// Create a copy of NetworkOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceOperationCopyWith<$Res>? get serviceOperation {
    if (_self.serviceOperation == null) {
    return null;
  }

  return $ServiceOperationCopyWith<$Res>(_self.serviceOperation!, (value) {
    return _then(_self.copyWith(serviceOperation: value));
  });
}/// Create a copy of NetworkOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodeOperationCopyWith<$Res>? get networkNodeOperation {
    if (_self.networkNodeOperation == null) {
    return null;
  }

  return $NetworkNodeOperationCopyWith<$Res>(_self.networkNodeOperation!, (value) {
    return _then(_self.copyWith(networkNodeOperation: value));
  });
}
}


/// Adds pattern-matching-related methods to [NetworkOperation].
extension NetworkOperationPatterns on NetworkOperation {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkOperation value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkOperation() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkOperation value)  def,}){
final _that = this;
switch (_that) {
case _NetworkOperation():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkOperation value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkOperation() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue id, @JsonKey(fromJson: NetworkOperationMessageTypeExtension.fromJson, toJson: NetworkOperationMessageTypeExtension.toJson)  NetworkOperationMessageType messageType, @JsonKey(fromJson: NetworkOperationTypeExtension.fromJson, toJson: NetworkOperationTypeExtension.toJson)  NetworkOperationType type,  List<NetworkOperationHop> networkOperationHopList,  NetworkRequest? networkRequest,  NetworkResponse? networkResponse,  ApiOperation? apiOperation,  ServiceOperation? serviceOperation,  NetworkNodeOperation? networkNodeOperation)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkOperation() when def != null:
return def(_that.id,_that.messageType,_that.type,_that.networkOperationHopList,_that.networkRequest,_that.networkResponse,_that.apiOperation,_that.serviceOperation,_that.networkNodeOperation);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue id, @JsonKey(fromJson: NetworkOperationMessageTypeExtension.fromJson, toJson: NetworkOperationMessageTypeExtension.toJson)  NetworkOperationMessageType messageType, @JsonKey(fromJson: NetworkOperationTypeExtension.fromJson, toJson: NetworkOperationTypeExtension.toJson)  NetworkOperationType type,  List<NetworkOperationHop> networkOperationHopList,  NetworkRequest? networkRequest,  NetworkResponse? networkResponse,  ApiOperation? apiOperation,  ServiceOperation? serviceOperation,  NetworkNodeOperation? networkNodeOperation)  def,}) {final _that = this;
switch (_that) {
case _NetworkOperation():
return def(_that.id,_that.messageType,_that.type,_that.networkOperationHopList,_that.networkRequest,_that.networkResponse,_that.apiOperation,_that.serviceOperation,_that.networkNodeOperation);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue id, @JsonKey(fromJson: NetworkOperationMessageTypeExtension.fromJson, toJson: NetworkOperationMessageTypeExtension.toJson)  NetworkOperationMessageType messageType, @JsonKey(fromJson: NetworkOperationTypeExtension.fromJson, toJson: NetworkOperationTypeExtension.toJson)  NetworkOperationType type,  List<NetworkOperationHop> networkOperationHopList,  NetworkRequest? networkRequest,  NetworkResponse? networkResponse,  ApiOperation? apiOperation,  ServiceOperation? serviceOperation,  NetworkNodeOperation? networkNodeOperation)?  def,}) {final _that = this;
switch (_that) {
case _NetworkOperation() when def != null:
return def(_that.id,_that.messageType,_that.type,_that.networkOperationHopList,_that.networkRequest,_that.networkResponse,_that.apiOperation,_that.serviceOperation,_that.networkNodeOperation);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkOperation implements NetworkOperation {
   _NetworkOperation({@UuidValueConverter() required this.id, @JsonKey(fromJson: NetworkOperationMessageTypeExtension.fromJson, toJson: NetworkOperationMessageTypeExtension.toJson) required this.messageType, @JsonKey(fromJson: NetworkOperationTypeExtension.fromJson, toJson: NetworkOperationTypeExtension.toJson) required this.type, final  List<NetworkOperationHop> networkOperationHopList = const [], this.networkRequest, this.networkResponse, this.apiOperation, this.serviceOperation, this.networkNodeOperation}): _networkOperationHopList = networkOperationHopList;
  factory _NetworkOperation.fromJson(Map<String, dynamic> json) => _$NetworkOperationFromJson(json);

@override@UuidValueConverter() final  UuidValue id;
@override@JsonKey(fromJson: NetworkOperationMessageTypeExtension.fromJson, toJson: NetworkOperationMessageTypeExtension.toJson) final  NetworkOperationMessageType messageType;
@override@JsonKey(fromJson: NetworkOperationTypeExtension.fromJson, toJson: NetworkOperationTypeExtension.toJson) final  NetworkOperationType type;
 final  List<NetworkOperationHop> _networkOperationHopList;
@override@JsonKey() List<NetworkOperationHop> get networkOperationHopList {
  if (_networkOperationHopList is EqualUnmodifiableListView) return _networkOperationHopList;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_networkOperationHopList);
}

@override final  NetworkRequest? networkRequest;
@override final  NetworkResponse? networkResponse;
@override final  ApiOperation? apiOperation;
@override final  ServiceOperation? serviceOperation;
@override final  NetworkNodeOperation? networkNodeOperation;

/// Create a copy of NetworkOperation
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkOperationCopyWith<_NetworkOperation> get copyWith => __$NetworkOperationCopyWithImpl<_NetworkOperation>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkOperationToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkOperation&&(identical(other.id, id) || other.id == id)&&(identical(other.messageType, messageType) || other.messageType == messageType)&&(identical(other.type, type) || other.type == type)&&const DeepCollectionEquality().equals(other._networkOperationHopList, _networkOperationHopList)&&(identical(other.networkRequest, networkRequest) || other.networkRequest == networkRequest)&&(identical(other.networkResponse, networkResponse) || other.networkResponse == networkResponse)&&(identical(other.apiOperation, apiOperation) || other.apiOperation == apiOperation)&&(identical(other.serviceOperation, serviceOperation) || other.serviceOperation == serviceOperation)&&(identical(other.networkNodeOperation, networkNodeOperation) || other.networkNodeOperation == networkNodeOperation));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,messageType,type,const DeepCollectionEquality().hash(_networkOperationHopList),networkRequest,networkResponse,apiOperation,serviceOperation,networkNodeOperation);

@override
String toString() {
  return 'NetworkOperation.def(id: $id, messageType: $messageType, type: $type, networkOperationHopList: $networkOperationHopList, networkRequest: $networkRequest, networkResponse: $networkResponse, apiOperation: $apiOperation, serviceOperation: $serviceOperation, networkNodeOperation: $networkNodeOperation)';
}


}

/// @nodoc
abstract mixin class _$NetworkOperationCopyWith<$Res> implements $NetworkOperationCopyWith<$Res> {
  factory _$NetworkOperationCopyWith(_NetworkOperation value, $Res Function(_NetworkOperation) _then) = __$NetworkOperationCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue id,@JsonKey(fromJson: NetworkOperationMessageTypeExtension.fromJson, toJson: NetworkOperationMessageTypeExtension.toJson) NetworkOperationMessageType messageType,@JsonKey(fromJson: NetworkOperationTypeExtension.fromJson, toJson: NetworkOperationTypeExtension.toJson) NetworkOperationType type, List<NetworkOperationHop> networkOperationHopList, NetworkRequest? networkRequest, NetworkResponse? networkResponse, ApiOperation? apiOperation, ServiceOperation? serviceOperation, NetworkNodeOperation? networkNodeOperation
});


@override $NetworkRequestCopyWith<$Res>? get networkRequest;@override $NetworkResponseCopyWith<$Res>? get networkResponse;@override $ApiOperationCopyWith<$Res>? get apiOperation;@override $ServiceOperationCopyWith<$Res>? get serviceOperation;@override $NetworkNodeOperationCopyWith<$Res>? get networkNodeOperation;

}
/// @nodoc
class __$NetworkOperationCopyWithImpl<$Res>
    implements _$NetworkOperationCopyWith<$Res> {
  __$NetworkOperationCopyWithImpl(this._self, this._then);

  final _NetworkOperation _self;
  final $Res Function(_NetworkOperation) _then;

/// Create a copy of NetworkOperation
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? id = null,Object? messageType = null,Object? type = null,Object? networkOperationHopList = null,Object? networkRequest = freezed,Object? networkResponse = freezed,Object? apiOperation = freezed,Object? serviceOperation = freezed,Object? networkNodeOperation = freezed,}) {
  return _then(_NetworkOperation(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,messageType: null == messageType ? _self.messageType : messageType // ignore: cast_nullable_to_non_nullable
as NetworkOperationMessageType,type: null == type ? _self.type : type // ignore: cast_nullable_to_non_nullable
as NetworkOperationType,networkOperationHopList: null == networkOperationHopList ? _self._networkOperationHopList : networkOperationHopList // ignore: cast_nullable_to_non_nullable
as List<NetworkOperationHop>,networkRequest: freezed == networkRequest ? _self.networkRequest : networkRequest // ignore: cast_nullable_to_non_nullable
as NetworkRequest?,networkResponse: freezed == networkResponse ? _self.networkResponse : networkResponse // ignore: cast_nullable_to_non_nullable
as NetworkResponse?,apiOperation: freezed == apiOperation ? _self.apiOperation : apiOperation // ignore: cast_nullable_to_non_nullable
as ApiOperation?,serviceOperation: freezed == serviceOperation ? _self.serviceOperation : serviceOperation // ignore: cast_nullable_to_non_nullable
as ServiceOperation?,networkNodeOperation: freezed == networkNodeOperation ? _self.networkNodeOperation : networkNodeOperation // ignore: cast_nullable_to_non_nullable
as NetworkNodeOperation?,
  ));
}

/// Create a copy of NetworkOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkRequestCopyWith<$Res>? get networkRequest {
    if (_self.networkRequest == null) {
    return null;
  }

  return $NetworkRequestCopyWith<$Res>(_self.networkRequest!, (value) {
    return _then(_self.copyWith(networkRequest: value));
  });
}/// Create a copy of NetworkOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkResponseCopyWith<$Res>? get networkResponse {
    if (_self.networkResponse == null) {
    return null;
  }

  return $NetworkResponseCopyWith<$Res>(_self.networkResponse!, (value) {
    return _then(_self.copyWith(networkResponse: value));
  });
}/// Create a copy of NetworkOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ApiOperationCopyWith<$Res>? get apiOperation {
    if (_self.apiOperation == null) {
    return null;
  }

  return $ApiOperationCopyWith<$Res>(_self.apiOperation!, (value) {
    return _then(_self.copyWith(apiOperation: value));
  });
}/// Create a copy of NetworkOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceOperationCopyWith<$Res>? get serviceOperation {
    if (_self.serviceOperation == null) {
    return null;
  }

  return $ServiceOperationCopyWith<$Res>(_self.serviceOperation!, (value) {
    return _then(_self.copyWith(serviceOperation: value));
  });
}/// Create a copy of NetworkOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodeOperationCopyWith<$Res>? get networkNodeOperation {
    if (_self.networkNodeOperation == null) {
    return null;
  }

  return $NetworkNodeOperationCopyWith<$Res>(_self.networkNodeOperation!, (value) {
    return _then(_self.copyWith(networkNodeOperation: value));
  });
}
}

// dart format on
