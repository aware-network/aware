// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'network_service_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$NetworkNodeRouteDescriptor {

@UuidValueConverter() UuidValue get nodeId; String? get publicKey; String get hostname; int get port; String? get baseUrl; String get status; String? get lastSeenAt;
/// Create a copy of NetworkNodeRouteDescriptor
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkNodeRouteDescriptorCopyWith<NetworkNodeRouteDescriptor> get copyWith => _$NetworkNodeRouteDescriptorCopyWithImpl<NetworkNodeRouteDescriptor>(this as NetworkNodeRouteDescriptor, _$identity);

  /// Serializes this NetworkNodeRouteDescriptor to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkNodeRouteDescriptor&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.publicKey, publicKey) || other.publicKey == publicKey)&&(identical(other.hostname, hostname) || other.hostname == hostname)&&(identical(other.port, port) || other.port == port)&&(identical(other.baseUrl, baseUrl) || other.baseUrl == baseUrl)&&(identical(other.status, status) || other.status == status)&&(identical(other.lastSeenAt, lastSeenAt) || other.lastSeenAt == lastSeenAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,nodeId,publicKey,hostname,port,baseUrl,status,lastSeenAt);

@override
String toString() {
  return 'NetworkNodeRouteDescriptor(nodeId: $nodeId, publicKey: $publicKey, hostname: $hostname, port: $port, baseUrl: $baseUrl, status: $status, lastSeenAt: $lastSeenAt)';
}


}

/// @nodoc
abstract mixin class $NetworkNodeRouteDescriptorCopyWith<$Res>  {
  factory $NetworkNodeRouteDescriptorCopyWith(NetworkNodeRouteDescriptor value, $Res Function(NetworkNodeRouteDescriptor) _then) = _$NetworkNodeRouteDescriptorCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue nodeId, String? publicKey, String hostname, int port, String? baseUrl, String status, String? lastSeenAt
});




}
/// @nodoc
class _$NetworkNodeRouteDescriptorCopyWithImpl<$Res>
    implements $NetworkNodeRouteDescriptorCopyWith<$Res> {
  _$NetworkNodeRouteDescriptorCopyWithImpl(this._self, this._then);

  final NetworkNodeRouteDescriptor _self;
  final $Res Function(NetworkNodeRouteDescriptor) _then;

/// Create a copy of NetworkNodeRouteDescriptor
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? nodeId = null,Object? publicKey = freezed,Object? hostname = null,Object? port = null,Object? baseUrl = freezed,Object? status = null,Object? lastSeenAt = freezed,}) {
  return _then(_self.copyWith(
nodeId: null == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,publicKey: freezed == publicKey ? _self.publicKey : publicKey // ignore: cast_nullable_to_non_nullable
as String?,hostname: null == hostname ? _self.hostname : hostname // ignore: cast_nullable_to_non_nullable
as String,port: null == port ? _self.port : port // ignore: cast_nullable_to_non_nullable
as int,baseUrl: freezed == baseUrl ? _self.baseUrl : baseUrl // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,lastSeenAt: freezed == lastSeenAt ? _self.lastSeenAt : lastSeenAt // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkNodeRouteDescriptor].
extension NetworkNodeRouteDescriptorPatterns on NetworkNodeRouteDescriptor {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkNodeRouteDescriptor value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkNodeRouteDescriptor() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkNodeRouteDescriptor value)  def,}){
final _that = this;
switch (_that) {
case _NetworkNodeRouteDescriptor():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkNodeRouteDescriptor value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkNodeRouteDescriptor() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue nodeId,  String? publicKey,  String hostname,  int port,  String? baseUrl,  String status,  String? lastSeenAt)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkNodeRouteDescriptor() when def != null:
return def(_that.nodeId,_that.publicKey,_that.hostname,_that.port,_that.baseUrl,_that.status,_that.lastSeenAt);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue nodeId,  String? publicKey,  String hostname,  int port,  String? baseUrl,  String status,  String? lastSeenAt)  def,}) {final _that = this;
switch (_that) {
case _NetworkNodeRouteDescriptor():
return def(_that.nodeId,_that.publicKey,_that.hostname,_that.port,_that.baseUrl,_that.status,_that.lastSeenAt);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue nodeId,  String? publicKey,  String hostname,  int port,  String? baseUrl,  String status,  String? lastSeenAt)?  def,}) {final _that = this;
switch (_that) {
case _NetworkNodeRouteDescriptor() when def != null:
return def(_that.nodeId,_that.publicKey,_that.hostname,_that.port,_that.baseUrl,_that.status,_that.lastSeenAt);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkNodeRouteDescriptor implements NetworkNodeRouteDescriptor {
   _NetworkNodeRouteDescriptor({@UuidValueConverter() required this.nodeId, this.publicKey, required this.hostname, required this.port, this.baseUrl, required this.status, this.lastSeenAt});
  factory _NetworkNodeRouteDescriptor.fromJson(Map<String, dynamic> json) => _$NetworkNodeRouteDescriptorFromJson(json);

@override@UuidValueConverter() final  UuidValue nodeId;
@override final  String? publicKey;
@override final  String hostname;
@override final  int port;
@override final  String? baseUrl;
@override final  String status;
@override final  String? lastSeenAt;

/// Create a copy of NetworkNodeRouteDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkNodeRouteDescriptorCopyWith<_NetworkNodeRouteDescriptor> get copyWith => __$NetworkNodeRouteDescriptorCopyWithImpl<_NetworkNodeRouteDescriptor>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkNodeRouteDescriptorToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkNodeRouteDescriptor&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.publicKey, publicKey) || other.publicKey == publicKey)&&(identical(other.hostname, hostname) || other.hostname == hostname)&&(identical(other.port, port) || other.port == port)&&(identical(other.baseUrl, baseUrl) || other.baseUrl == baseUrl)&&(identical(other.status, status) || other.status == status)&&(identical(other.lastSeenAt, lastSeenAt) || other.lastSeenAt == lastSeenAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,nodeId,publicKey,hostname,port,baseUrl,status,lastSeenAt);

@override
String toString() {
  return 'NetworkNodeRouteDescriptor.def(nodeId: $nodeId, publicKey: $publicKey, hostname: $hostname, port: $port, baseUrl: $baseUrl, status: $status, lastSeenAt: $lastSeenAt)';
}


}

/// @nodoc
abstract mixin class _$NetworkNodeRouteDescriptorCopyWith<$Res> implements $NetworkNodeRouteDescriptorCopyWith<$Res> {
  factory _$NetworkNodeRouteDescriptorCopyWith(_NetworkNodeRouteDescriptor value, $Res Function(_NetworkNodeRouteDescriptor) _then) = __$NetworkNodeRouteDescriptorCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue nodeId, String? publicKey, String hostname, int port, String? baseUrl, String status, String? lastSeenAt
});




}
/// @nodoc
class __$NetworkNodeRouteDescriptorCopyWithImpl<$Res>
    implements _$NetworkNodeRouteDescriptorCopyWith<$Res> {
  __$NetworkNodeRouteDescriptorCopyWithImpl(this._self, this._then);

  final _NetworkNodeRouteDescriptor _self;
  final $Res Function(_NetworkNodeRouteDescriptor) _then;

/// Create a copy of NetworkNodeRouteDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? nodeId = null,Object? publicKey = freezed,Object? hostname = null,Object? port = null,Object? baseUrl = freezed,Object? status = null,Object? lastSeenAt = freezed,}) {
  return _then(_NetworkNodeRouteDescriptor(
nodeId: null == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,publicKey: freezed == publicKey ? _self.publicKey : publicKey // ignore: cast_nullable_to_non_nullable
as String?,hostname: null == hostname ? _self.hostname : hostname // ignore: cast_nullable_to_non_nullable
as String,port: null == port ? _self.port : port // ignore: cast_nullable_to_non_nullable
as int,baseUrl: freezed == baseUrl ? _self.baseUrl : baseUrl // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,lastSeenAt: freezed == lastSeenAt ? _self.lastSeenAt : lastSeenAt // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$NetworkPeerFanoutRuleDescriptor {

@UuidValueConverter() UuidValue? get id;@UuidValueConverter() UuidValue get laneBranchId; String get laneProjectionHash; bool get enabled; String get mode;
/// Create a copy of NetworkPeerFanoutRuleDescriptor
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkPeerFanoutRuleDescriptorCopyWith<NetworkPeerFanoutRuleDescriptor> get copyWith => _$NetworkPeerFanoutRuleDescriptorCopyWithImpl<NetworkPeerFanoutRuleDescriptor>(this as NetworkPeerFanoutRuleDescriptor, _$identity);

  /// Serializes this NetworkPeerFanoutRuleDescriptor to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkPeerFanoutRuleDescriptor&&(identical(other.id, id) || other.id == id)&&(identical(other.laneBranchId, laneBranchId) || other.laneBranchId == laneBranchId)&&(identical(other.laneProjectionHash, laneProjectionHash) || other.laneProjectionHash == laneProjectionHash)&&(identical(other.enabled, enabled) || other.enabled == enabled)&&(identical(other.mode, mode) || other.mode == mode));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,laneBranchId,laneProjectionHash,enabled,mode);

@override
String toString() {
  return 'NetworkPeerFanoutRuleDescriptor(id: $id, laneBranchId: $laneBranchId, laneProjectionHash: $laneProjectionHash, enabled: $enabled, mode: $mode)';
}


}

/// @nodoc
abstract mixin class $NetworkPeerFanoutRuleDescriptorCopyWith<$Res>  {
  factory $NetworkPeerFanoutRuleDescriptorCopyWith(NetworkPeerFanoutRuleDescriptor value, $Res Function(NetworkPeerFanoutRuleDescriptor) _then) = _$NetworkPeerFanoutRuleDescriptorCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? id,@UuidValueConverter() UuidValue laneBranchId, String laneProjectionHash, bool enabled, String mode
});




}
/// @nodoc
class _$NetworkPeerFanoutRuleDescriptorCopyWithImpl<$Res>
    implements $NetworkPeerFanoutRuleDescriptorCopyWith<$Res> {
  _$NetworkPeerFanoutRuleDescriptorCopyWithImpl(this._self, this._then);

  final NetworkPeerFanoutRuleDescriptor _self;
  final $Res Function(NetworkPeerFanoutRuleDescriptor) _then;

/// Create a copy of NetworkPeerFanoutRuleDescriptor
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? id = freezed,Object? laneBranchId = null,Object? laneProjectionHash = null,Object? enabled = null,Object? mode = null,}) {
  return _then(_self.copyWith(
id: freezed == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue?,laneBranchId: null == laneBranchId ? _self.laneBranchId : laneBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue,laneProjectionHash: null == laneProjectionHash ? _self.laneProjectionHash : laneProjectionHash // ignore: cast_nullable_to_non_nullable
as String,enabled: null == enabled ? _self.enabled : enabled // ignore: cast_nullable_to_non_nullable
as bool,mode: null == mode ? _self.mode : mode // ignore: cast_nullable_to_non_nullable
as String,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkPeerFanoutRuleDescriptor].
extension NetworkPeerFanoutRuleDescriptorPatterns on NetworkPeerFanoutRuleDescriptor {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkPeerFanoutRuleDescriptor value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkPeerFanoutRuleDescriptor() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkPeerFanoutRuleDescriptor value)  def,}){
final _that = this;
switch (_that) {
case _NetworkPeerFanoutRuleDescriptor():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkPeerFanoutRuleDescriptor value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkPeerFanoutRuleDescriptor() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? id, @UuidValueConverter()  UuidValue laneBranchId,  String laneProjectionHash,  bool enabled,  String mode)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkPeerFanoutRuleDescriptor() when def != null:
return def(_that.id,_that.laneBranchId,_that.laneProjectionHash,_that.enabled,_that.mode);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? id, @UuidValueConverter()  UuidValue laneBranchId,  String laneProjectionHash,  bool enabled,  String mode)  def,}) {final _that = this;
switch (_that) {
case _NetworkPeerFanoutRuleDescriptor():
return def(_that.id,_that.laneBranchId,_that.laneProjectionHash,_that.enabled,_that.mode);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? id, @UuidValueConverter()  UuidValue laneBranchId,  String laneProjectionHash,  bool enabled,  String mode)?  def,}) {final _that = this;
switch (_that) {
case _NetworkPeerFanoutRuleDescriptor() when def != null:
return def(_that.id,_that.laneBranchId,_that.laneProjectionHash,_that.enabled,_that.mode);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkPeerFanoutRuleDescriptor implements NetworkPeerFanoutRuleDescriptor {
   _NetworkPeerFanoutRuleDescriptor({@UuidValueConverter() this.id, @UuidValueConverter() required this.laneBranchId, required this.laneProjectionHash, required this.enabled, required this.mode});
  factory _NetworkPeerFanoutRuleDescriptor.fromJson(Map<String, dynamic> json) => _$NetworkPeerFanoutRuleDescriptorFromJson(json);

@override@UuidValueConverter() final  UuidValue? id;
@override@UuidValueConverter() final  UuidValue laneBranchId;
@override final  String laneProjectionHash;
@override final  bool enabled;
@override final  String mode;

/// Create a copy of NetworkPeerFanoutRuleDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkPeerFanoutRuleDescriptorCopyWith<_NetworkPeerFanoutRuleDescriptor> get copyWith => __$NetworkPeerFanoutRuleDescriptorCopyWithImpl<_NetworkPeerFanoutRuleDescriptor>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkPeerFanoutRuleDescriptorToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkPeerFanoutRuleDescriptor&&(identical(other.id, id) || other.id == id)&&(identical(other.laneBranchId, laneBranchId) || other.laneBranchId == laneBranchId)&&(identical(other.laneProjectionHash, laneProjectionHash) || other.laneProjectionHash == laneProjectionHash)&&(identical(other.enabled, enabled) || other.enabled == enabled)&&(identical(other.mode, mode) || other.mode == mode));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,laneBranchId,laneProjectionHash,enabled,mode);

@override
String toString() {
  return 'NetworkPeerFanoutRuleDescriptor.def(id: $id, laneBranchId: $laneBranchId, laneProjectionHash: $laneProjectionHash, enabled: $enabled, mode: $mode)';
}


}

/// @nodoc
abstract mixin class _$NetworkPeerFanoutRuleDescriptorCopyWith<$Res> implements $NetworkPeerFanoutRuleDescriptorCopyWith<$Res> {
  factory _$NetworkPeerFanoutRuleDescriptorCopyWith(_NetworkPeerFanoutRuleDescriptor value, $Res Function(_NetworkPeerFanoutRuleDescriptor) _then) = __$NetworkPeerFanoutRuleDescriptorCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? id,@UuidValueConverter() UuidValue laneBranchId, String laneProjectionHash, bool enabled, String mode
});




}
/// @nodoc
class __$NetworkPeerFanoutRuleDescriptorCopyWithImpl<$Res>
    implements _$NetworkPeerFanoutRuleDescriptorCopyWith<$Res> {
  __$NetworkPeerFanoutRuleDescriptorCopyWithImpl(this._self, this._then);

  final _NetworkPeerFanoutRuleDescriptor _self;
  final $Res Function(_NetworkPeerFanoutRuleDescriptor) _then;

/// Create a copy of NetworkPeerFanoutRuleDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? id = freezed,Object? laneBranchId = null,Object? laneProjectionHash = null,Object? enabled = null,Object? mode = null,}) {
  return _then(_NetworkPeerFanoutRuleDescriptor(
id: freezed == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue?,laneBranchId: null == laneBranchId ? _self.laneBranchId : laneBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue,laneProjectionHash: null == laneProjectionHash ? _self.laneProjectionHash : laneProjectionHash // ignore: cast_nullable_to_non_nullable
as String,enabled: null == enabled ? _self.enabled : enabled // ignore: cast_nullable_to_non_nullable
as bool,mode: null == mode ? _self.mode : mode // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}


/// @nodoc
mixin _$NetworkPeerDescriptor {

@UuidValueConverter() UuidValue? get edgeId;@UuidValueConverter() UuidValue get sourceNodeId;@UuidValueConverter() UuidValue get targetNodeId;@UuidValueConverter() UuidValue get peerNodeId; String get peerBaseUrl; String get direction; String get status; double get trustScore; List<NetworkPeerFanoutRuleDescriptor> get fanoutRules; String? get connectedAt; String? get lastPingAt;
/// Create a copy of NetworkPeerDescriptor
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkPeerDescriptorCopyWith<NetworkPeerDescriptor> get copyWith => _$NetworkPeerDescriptorCopyWithImpl<NetworkPeerDescriptor>(this as NetworkPeerDescriptor, _$identity);

  /// Serializes this NetworkPeerDescriptor to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkPeerDescriptor&&(identical(other.edgeId, edgeId) || other.edgeId == edgeId)&&(identical(other.sourceNodeId, sourceNodeId) || other.sourceNodeId == sourceNodeId)&&(identical(other.targetNodeId, targetNodeId) || other.targetNodeId == targetNodeId)&&(identical(other.peerNodeId, peerNodeId) || other.peerNodeId == peerNodeId)&&(identical(other.peerBaseUrl, peerBaseUrl) || other.peerBaseUrl == peerBaseUrl)&&(identical(other.direction, direction) || other.direction == direction)&&(identical(other.status, status) || other.status == status)&&(identical(other.trustScore, trustScore) || other.trustScore == trustScore)&&const DeepCollectionEquality().equals(other.fanoutRules, fanoutRules)&&(identical(other.connectedAt, connectedAt) || other.connectedAt == connectedAt)&&(identical(other.lastPingAt, lastPingAt) || other.lastPingAt == lastPingAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,edgeId,sourceNodeId,targetNodeId,peerNodeId,peerBaseUrl,direction,status,trustScore,const DeepCollectionEquality().hash(fanoutRules),connectedAt,lastPingAt);

@override
String toString() {
  return 'NetworkPeerDescriptor(edgeId: $edgeId, sourceNodeId: $sourceNodeId, targetNodeId: $targetNodeId, peerNodeId: $peerNodeId, peerBaseUrl: $peerBaseUrl, direction: $direction, status: $status, trustScore: $trustScore, fanoutRules: $fanoutRules, connectedAt: $connectedAt, lastPingAt: $lastPingAt)';
}


}

/// @nodoc
abstract mixin class $NetworkPeerDescriptorCopyWith<$Res>  {
  factory $NetworkPeerDescriptorCopyWith(NetworkPeerDescriptor value, $Res Function(NetworkPeerDescriptor) _then) = _$NetworkPeerDescriptorCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? edgeId,@UuidValueConverter() UuidValue sourceNodeId,@UuidValueConverter() UuidValue targetNodeId,@UuidValueConverter() UuidValue peerNodeId, String peerBaseUrl, String direction, String status, double trustScore, List<NetworkPeerFanoutRuleDescriptor> fanoutRules, String? connectedAt, String? lastPingAt
});




}
/// @nodoc
class _$NetworkPeerDescriptorCopyWithImpl<$Res>
    implements $NetworkPeerDescriptorCopyWith<$Res> {
  _$NetworkPeerDescriptorCopyWithImpl(this._self, this._then);

  final NetworkPeerDescriptor _self;
  final $Res Function(NetworkPeerDescriptor) _then;

/// Create a copy of NetworkPeerDescriptor
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? edgeId = freezed,Object? sourceNodeId = null,Object? targetNodeId = null,Object? peerNodeId = null,Object? peerBaseUrl = null,Object? direction = null,Object? status = null,Object? trustScore = null,Object? fanoutRules = null,Object? connectedAt = freezed,Object? lastPingAt = freezed,}) {
  return _then(_self.copyWith(
edgeId: freezed == edgeId ? _self.edgeId : edgeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sourceNodeId: null == sourceNodeId ? _self.sourceNodeId : sourceNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,targetNodeId: null == targetNodeId ? _self.targetNodeId : targetNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,peerNodeId: null == peerNodeId ? _self.peerNodeId : peerNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,peerBaseUrl: null == peerBaseUrl ? _self.peerBaseUrl : peerBaseUrl // ignore: cast_nullable_to_non_nullable
as String,direction: null == direction ? _self.direction : direction // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,trustScore: null == trustScore ? _self.trustScore : trustScore // ignore: cast_nullable_to_non_nullable
as double,fanoutRules: null == fanoutRules ? _self.fanoutRules : fanoutRules // ignore: cast_nullable_to_non_nullable
as List<NetworkPeerFanoutRuleDescriptor>,connectedAt: freezed == connectedAt ? _self.connectedAt : connectedAt // ignore: cast_nullable_to_non_nullable
as String?,lastPingAt: freezed == lastPingAt ? _self.lastPingAt : lastPingAt // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkPeerDescriptor].
extension NetworkPeerDescriptorPatterns on NetworkPeerDescriptor {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkPeerDescriptor value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkPeerDescriptor() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkPeerDescriptor value)  def,}){
final _that = this;
switch (_that) {
case _NetworkPeerDescriptor():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkPeerDescriptor value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkPeerDescriptor() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? edgeId, @UuidValueConverter()  UuidValue sourceNodeId, @UuidValueConverter()  UuidValue targetNodeId, @UuidValueConverter()  UuidValue peerNodeId,  String peerBaseUrl,  String direction,  String status,  double trustScore,  List<NetworkPeerFanoutRuleDescriptor> fanoutRules,  String? connectedAt,  String? lastPingAt)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkPeerDescriptor() when def != null:
return def(_that.edgeId,_that.sourceNodeId,_that.targetNodeId,_that.peerNodeId,_that.peerBaseUrl,_that.direction,_that.status,_that.trustScore,_that.fanoutRules,_that.connectedAt,_that.lastPingAt);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? edgeId, @UuidValueConverter()  UuidValue sourceNodeId, @UuidValueConverter()  UuidValue targetNodeId, @UuidValueConverter()  UuidValue peerNodeId,  String peerBaseUrl,  String direction,  String status,  double trustScore,  List<NetworkPeerFanoutRuleDescriptor> fanoutRules,  String? connectedAt,  String? lastPingAt)  def,}) {final _that = this;
switch (_that) {
case _NetworkPeerDescriptor():
return def(_that.edgeId,_that.sourceNodeId,_that.targetNodeId,_that.peerNodeId,_that.peerBaseUrl,_that.direction,_that.status,_that.trustScore,_that.fanoutRules,_that.connectedAt,_that.lastPingAt);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? edgeId, @UuidValueConverter()  UuidValue sourceNodeId, @UuidValueConverter()  UuidValue targetNodeId, @UuidValueConverter()  UuidValue peerNodeId,  String peerBaseUrl,  String direction,  String status,  double trustScore,  List<NetworkPeerFanoutRuleDescriptor> fanoutRules,  String? connectedAt,  String? lastPingAt)?  def,}) {final _that = this;
switch (_that) {
case _NetworkPeerDescriptor() when def != null:
return def(_that.edgeId,_that.sourceNodeId,_that.targetNodeId,_that.peerNodeId,_that.peerBaseUrl,_that.direction,_that.status,_that.trustScore,_that.fanoutRules,_that.connectedAt,_that.lastPingAt);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkPeerDescriptor implements NetworkPeerDescriptor {
   _NetworkPeerDescriptor({@UuidValueConverter() this.edgeId, @UuidValueConverter() required this.sourceNodeId, @UuidValueConverter() required this.targetNodeId, @UuidValueConverter() required this.peerNodeId, required this.peerBaseUrl, required this.direction, required this.status, required this.trustScore, final  List<NetworkPeerFanoutRuleDescriptor> fanoutRules = const [], this.connectedAt, this.lastPingAt}): _fanoutRules = fanoutRules;
  factory _NetworkPeerDescriptor.fromJson(Map<String, dynamic> json) => _$NetworkPeerDescriptorFromJson(json);

@override@UuidValueConverter() final  UuidValue? edgeId;
@override@UuidValueConverter() final  UuidValue sourceNodeId;
@override@UuidValueConverter() final  UuidValue targetNodeId;
@override@UuidValueConverter() final  UuidValue peerNodeId;
@override final  String peerBaseUrl;
@override final  String direction;
@override final  String status;
@override final  double trustScore;
 final  List<NetworkPeerFanoutRuleDescriptor> _fanoutRules;
@override@JsonKey() List<NetworkPeerFanoutRuleDescriptor> get fanoutRules {
  if (_fanoutRules is EqualUnmodifiableListView) return _fanoutRules;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_fanoutRules);
}

@override final  String? connectedAt;
@override final  String? lastPingAt;

/// Create a copy of NetworkPeerDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkPeerDescriptorCopyWith<_NetworkPeerDescriptor> get copyWith => __$NetworkPeerDescriptorCopyWithImpl<_NetworkPeerDescriptor>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkPeerDescriptorToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkPeerDescriptor&&(identical(other.edgeId, edgeId) || other.edgeId == edgeId)&&(identical(other.sourceNodeId, sourceNodeId) || other.sourceNodeId == sourceNodeId)&&(identical(other.targetNodeId, targetNodeId) || other.targetNodeId == targetNodeId)&&(identical(other.peerNodeId, peerNodeId) || other.peerNodeId == peerNodeId)&&(identical(other.peerBaseUrl, peerBaseUrl) || other.peerBaseUrl == peerBaseUrl)&&(identical(other.direction, direction) || other.direction == direction)&&(identical(other.status, status) || other.status == status)&&(identical(other.trustScore, trustScore) || other.trustScore == trustScore)&&const DeepCollectionEquality().equals(other._fanoutRules, _fanoutRules)&&(identical(other.connectedAt, connectedAt) || other.connectedAt == connectedAt)&&(identical(other.lastPingAt, lastPingAt) || other.lastPingAt == lastPingAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,edgeId,sourceNodeId,targetNodeId,peerNodeId,peerBaseUrl,direction,status,trustScore,const DeepCollectionEquality().hash(_fanoutRules),connectedAt,lastPingAt);

@override
String toString() {
  return 'NetworkPeerDescriptor.def(edgeId: $edgeId, sourceNodeId: $sourceNodeId, targetNodeId: $targetNodeId, peerNodeId: $peerNodeId, peerBaseUrl: $peerBaseUrl, direction: $direction, status: $status, trustScore: $trustScore, fanoutRules: $fanoutRules, connectedAt: $connectedAt, lastPingAt: $lastPingAt)';
}


}

/// @nodoc
abstract mixin class _$NetworkPeerDescriptorCopyWith<$Res> implements $NetworkPeerDescriptorCopyWith<$Res> {
  factory _$NetworkPeerDescriptorCopyWith(_NetworkPeerDescriptor value, $Res Function(_NetworkPeerDescriptor) _then) = __$NetworkPeerDescriptorCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? edgeId,@UuidValueConverter() UuidValue sourceNodeId,@UuidValueConverter() UuidValue targetNodeId,@UuidValueConverter() UuidValue peerNodeId, String peerBaseUrl, String direction, String status, double trustScore, List<NetworkPeerFanoutRuleDescriptor> fanoutRules, String? connectedAt, String? lastPingAt
});




}
/// @nodoc
class __$NetworkPeerDescriptorCopyWithImpl<$Res>
    implements _$NetworkPeerDescriptorCopyWith<$Res> {
  __$NetworkPeerDescriptorCopyWithImpl(this._self, this._then);

  final _NetworkPeerDescriptor _self;
  final $Res Function(_NetworkPeerDescriptor) _then;

/// Create a copy of NetworkPeerDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? edgeId = freezed,Object? sourceNodeId = null,Object? targetNodeId = null,Object? peerNodeId = null,Object? peerBaseUrl = null,Object? direction = null,Object? status = null,Object? trustScore = null,Object? fanoutRules = null,Object? connectedAt = freezed,Object? lastPingAt = freezed,}) {
  return _then(_NetworkPeerDescriptor(
edgeId: freezed == edgeId ? _self.edgeId : edgeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sourceNodeId: null == sourceNodeId ? _self.sourceNodeId : sourceNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,targetNodeId: null == targetNodeId ? _self.targetNodeId : targetNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,peerNodeId: null == peerNodeId ? _self.peerNodeId : peerNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,peerBaseUrl: null == peerBaseUrl ? _self.peerBaseUrl : peerBaseUrl // ignore: cast_nullable_to_non_nullable
as String,direction: null == direction ? _self.direction : direction // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,trustScore: null == trustScore ? _self.trustScore : trustScore // ignore: cast_nullable_to_non_nullable
as double,fanoutRules: null == fanoutRules ? _self._fanoutRules : fanoutRules // ignore: cast_nullable_to_non_nullable
as List<NetworkPeerFanoutRuleDescriptor>,connectedAt: freezed == connectedAt ? _self.connectedAt : connectedAt // ignore: cast_nullable_to_non_nullable
as String?,lastPingAt: freezed == lastPingAt ? _self.lastPingAt : lastPingAt // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$NetworkHostedServiceDescriptor {

@UuidValueConverter() UuidValue? get servicePackageId;@UuidValueConverter() UuidValue get serviceId; String get serviceName; List<String> get servicePackageNames; List<String> get endpointRefs; List<String> get streamEndpointRefs; String get hostId; String? get hostVersion; String get protocolVersion; bool get supportsStreamEvents;
/// Create a copy of NetworkHostedServiceDescriptor
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkHostedServiceDescriptorCopyWith<NetworkHostedServiceDescriptor> get copyWith => _$NetworkHostedServiceDescriptorCopyWithImpl<NetworkHostedServiceDescriptor>(this as NetworkHostedServiceDescriptor, _$identity);

  /// Serializes this NetworkHostedServiceDescriptor to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkHostedServiceDescriptor&&(identical(other.servicePackageId, servicePackageId) || other.servicePackageId == servicePackageId)&&(identical(other.serviceId, serviceId) || other.serviceId == serviceId)&&(identical(other.serviceName, serviceName) || other.serviceName == serviceName)&&const DeepCollectionEquality().equals(other.servicePackageNames, servicePackageNames)&&const DeepCollectionEquality().equals(other.endpointRefs, endpointRefs)&&const DeepCollectionEquality().equals(other.streamEndpointRefs, streamEndpointRefs)&&(identical(other.hostId, hostId) || other.hostId == hostId)&&(identical(other.hostVersion, hostVersion) || other.hostVersion == hostVersion)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.supportsStreamEvents, supportsStreamEvents) || other.supportsStreamEvents == supportsStreamEvents));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,servicePackageId,serviceId,serviceName,const DeepCollectionEquality().hash(servicePackageNames),const DeepCollectionEquality().hash(endpointRefs),const DeepCollectionEquality().hash(streamEndpointRefs),hostId,hostVersion,protocolVersion,supportsStreamEvents);

@override
String toString() {
  return 'NetworkHostedServiceDescriptor(servicePackageId: $servicePackageId, serviceId: $serviceId, serviceName: $serviceName, servicePackageNames: $servicePackageNames, endpointRefs: $endpointRefs, streamEndpointRefs: $streamEndpointRefs, hostId: $hostId, hostVersion: $hostVersion, protocolVersion: $protocolVersion, supportsStreamEvents: $supportsStreamEvents)';
}


}

/// @nodoc
abstract mixin class $NetworkHostedServiceDescriptorCopyWith<$Res>  {
  factory $NetworkHostedServiceDescriptorCopyWith(NetworkHostedServiceDescriptor value, $Res Function(NetworkHostedServiceDescriptor) _then) = _$NetworkHostedServiceDescriptorCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? servicePackageId,@UuidValueConverter() UuidValue serviceId, String serviceName, List<String> servicePackageNames, List<String> endpointRefs, List<String> streamEndpointRefs, String hostId, String? hostVersion, String protocolVersion, bool supportsStreamEvents
});




}
/// @nodoc
class _$NetworkHostedServiceDescriptorCopyWithImpl<$Res>
    implements $NetworkHostedServiceDescriptorCopyWith<$Res> {
  _$NetworkHostedServiceDescriptorCopyWithImpl(this._self, this._then);

  final NetworkHostedServiceDescriptor _self;
  final $Res Function(NetworkHostedServiceDescriptor) _then;

/// Create a copy of NetworkHostedServiceDescriptor
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? servicePackageId = freezed,Object? serviceId = null,Object? serviceName = null,Object? servicePackageNames = null,Object? endpointRefs = null,Object? streamEndpointRefs = null,Object? hostId = null,Object? hostVersion = freezed,Object? protocolVersion = null,Object? supportsStreamEvents = null,}) {
  return _then(_self.copyWith(
servicePackageId: freezed == servicePackageId ? _self.servicePackageId : servicePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceId: null == serviceId ? _self.serviceId : serviceId // ignore: cast_nullable_to_non_nullable
as UuidValue,serviceName: null == serviceName ? _self.serviceName : serviceName // ignore: cast_nullable_to_non_nullable
as String,servicePackageNames: null == servicePackageNames ? _self.servicePackageNames : servicePackageNames // ignore: cast_nullable_to_non_nullable
as List<String>,endpointRefs: null == endpointRefs ? _self.endpointRefs : endpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,streamEndpointRefs: null == streamEndpointRefs ? _self.streamEndpointRefs : streamEndpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,hostId: null == hostId ? _self.hostId : hostId // ignore: cast_nullable_to_non_nullable
as String,hostVersion: freezed == hostVersion ? _self.hostVersion : hostVersion // ignore: cast_nullable_to_non_nullable
as String?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as String,supportsStreamEvents: null == supportsStreamEvents ? _self.supportsStreamEvents : supportsStreamEvents // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkHostedServiceDescriptor].
extension NetworkHostedServiceDescriptorPatterns on NetworkHostedServiceDescriptor {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkHostedServiceDescriptor value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkHostedServiceDescriptor() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkHostedServiceDescriptor value)  def,}){
final _that = this;
switch (_that) {
case _NetworkHostedServiceDescriptor():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkHostedServiceDescriptor value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkHostedServiceDescriptor() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? servicePackageId, @UuidValueConverter()  UuidValue serviceId,  String serviceName,  List<String> servicePackageNames,  List<String> endpointRefs,  List<String> streamEndpointRefs,  String hostId,  String? hostVersion,  String protocolVersion,  bool supportsStreamEvents)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkHostedServiceDescriptor() when def != null:
return def(_that.servicePackageId,_that.serviceId,_that.serviceName,_that.servicePackageNames,_that.endpointRefs,_that.streamEndpointRefs,_that.hostId,_that.hostVersion,_that.protocolVersion,_that.supportsStreamEvents);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? servicePackageId, @UuidValueConverter()  UuidValue serviceId,  String serviceName,  List<String> servicePackageNames,  List<String> endpointRefs,  List<String> streamEndpointRefs,  String hostId,  String? hostVersion,  String protocolVersion,  bool supportsStreamEvents)  def,}) {final _that = this;
switch (_that) {
case _NetworkHostedServiceDescriptor():
return def(_that.servicePackageId,_that.serviceId,_that.serviceName,_that.servicePackageNames,_that.endpointRefs,_that.streamEndpointRefs,_that.hostId,_that.hostVersion,_that.protocolVersion,_that.supportsStreamEvents);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? servicePackageId, @UuidValueConverter()  UuidValue serviceId,  String serviceName,  List<String> servicePackageNames,  List<String> endpointRefs,  List<String> streamEndpointRefs,  String hostId,  String? hostVersion,  String protocolVersion,  bool supportsStreamEvents)?  def,}) {final _that = this;
switch (_that) {
case _NetworkHostedServiceDescriptor() when def != null:
return def(_that.servicePackageId,_that.serviceId,_that.serviceName,_that.servicePackageNames,_that.endpointRefs,_that.streamEndpointRefs,_that.hostId,_that.hostVersion,_that.protocolVersion,_that.supportsStreamEvents);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkHostedServiceDescriptor implements NetworkHostedServiceDescriptor {
   _NetworkHostedServiceDescriptor({@UuidValueConverter() this.servicePackageId, @UuidValueConverter() required this.serviceId, required this.serviceName, final  List<String> servicePackageNames = const [], final  List<String> endpointRefs = const [], final  List<String> streamEndpointRefs = const [], required this.hostId, this.hostVersion, required this.protocolVersion, required this.supportsStreamEvents}): _servicePackageNames = servicePackageNames,_endpointRefs = endpointRefs,_streamEndpointRefs = streamEndpointRefs;
  factory _NetworkHostedServiceDescriptor.fromJson(Map<String, dynamic> json) => _$NetworkHostedServiceDescriptorFromJson(json);

@override@UuidValueConverter() final  UuidValue? servicePackageId;
@override@UuidValueConverter() final  UuidValue serviceId;
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

 final  List<String> _streamEndpointRefs;
@override@JsonKey() List<String> get streamEndpointRefs {
  if (_streamEndpointRefs is EqualUnmodifiableListView) return _streamEndpointRefs;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_streamEndpointRefs);
}

@override final  String hostId;
@override final  String? hostVersion;
@override final  String protocolVersion;
@override final  bool supportsStreamEvents;

/// Create a copy of NetworkHostedServiceDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkHostedServiceDescriptorCopyWith<_NetworkHostedServiceDescriptor> get copyWith => __$NetworkHostedServiceDescriptorCopyWithImpl<_NetworkHostedServiceDescriptor>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkHostedServiceDescriptorToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkHostedServiceDescriptor&&(identical(other.servicePackageId, servicePackageId) || other.servicePackageId == servicePackageId)&&(identical(other.serviceId, serviceId) || other.serviceId == serviceId)&&(identical(other.serviceName, serviceName) || other.serviceName == serviceName)&&const DeepCollectionEquality().equals(other._servicePackageNames, _servicePackageNames)&&const DeepCollectionEquality().equals(other._endpointRefs, _endpointRefs)&&const DeepCollectionEquality().equals(other._streamEndpointRefs, _streamEndpointRefs)&&(identical(other.hostId, hostId) || other.hostId == hostId)&&(identical(other.hostVersion, hostVersion) || other.hostVersion == hostVersion)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.supportsStreamEvents, supportsStreamEvents) || other.supportsStreamEvents == supportsStreamEvents));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,servicePackageId,serviceId,serviceName,const DeepCollectionEquality().hash(_servicePackageNames),const DeepCollectionEquality().hash(_endpointRefs),const DeepCollectionEquality().hash(_streamEndpointRefs),hostId,hostVersion,protocolVersion,supportsStreamEvents);

@override
String toString() {
  return 'NetworkHostedServiceDescriptor.def(servicePackageId: $servicePackageId, serviceId: $serviceId, serviceName: $serviceName, servicePackageNames: $servicePackageNames, endpointRefs: $endpointRefs, streamEndpointRefs: $streamEndpointRefs, hostId: $hostId, hostVersion: $hostVersion, protocolVersion: $protocolVersion, supportsStreamEvents: $supportsStreamEvents)';
}


}

/// @nodoc
abstract mixin class _$NetworkHostedServiceDescriptorCopyWith<$Res> implements $NetworkHostedServiceDescriptorCopyWith<$Res> {
  factory _$NetworkHostedServiceDescriptorCopyWith(_NetworkHostedServiceDescriptor value, $Res Function(_NetworkHostedServiceDescriptor) _then) = __$NetworkHostedServiceDescriptorCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? servicePackageId,@UuidValueConverter() UuidValue serviceId, String serviceName, List<String> servicePackageNames, List<String> endpointRefs, List<String> streamEndpointRefs, String hostId, String? hostVersion, String protocolVersion, bool supportsStreamEvents
});




}
/// @nodoc
class __$NetworkHostedServiceDescriptorCopyWithImpl<$Res>
    implements _$NetworkHostedServiceDescriptorCopyWith<$Res> {
  __$NetworkHostedServiceDescriptorCopyWithImpl(this._self, this._then);

  final _NetworkHostedServiceDescriptor _self;
  final $Res Function(_NetworkHostedServiceDescriptor) _then;

/// Create a copy of NetworkHostedServiceDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? servicePackageId = freezed,Object? serviceId = null,Object? serviceName = null,Object? servicePackageNames = null,Object? endpointRefs = null,Object? streamEndpointRefs = null,Object? hostId = null,Object? hostVersion = freezed,Object? protocolVersion = null,Object? supportsStreamEvents = null,}) {
  return _then(_NetworkHostedServiceDescriptor(
servicePackageId: freezed == servicePackageId ? _self.servicePackageId : servicePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceId: null == serviceId ? _self.serviceId : serviceId // ignore: cast_nullable_to_non_nullable
as UuidValue,serviceName: null == serviceName ? _self.serviceName : serviceName // ignore: cast_nullable_to_non_nullable
as String,servicePackageNames: null == servicePackageNames ? _self._servicePackageNames : servicePackageNames // ignore: cast_nullable_to_non_nullable
as List<String>,endpointRefs: null == endpointRefs ? _self._endpointRefs : endpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,streamEndpointRefs: null == streamEndpointRefs ? _self._streamEndpointRefs : streamEndpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,hostId: null == hostId ? _self.hostId : hostId // ignore: cast_nullable_to_non_nullable
as String,hostVersion: freezed == hostVersion ? _self.hostVersion : hostVersion // ignore: cast_nullable_to_non_nullable
as String?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as String,supportsStreamEvents: null == supportsStreamEvents ? _self.supportsStreamEvents : supportsStreamEvents // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}


}


/// @nodoc
mixin _$NetworkEnvironmentDescriptor {

@UuidValueConverter() UuidValue? get nodeId;@UuidValueConverter() UuidValue get environmentId; String? get environmentKey; String? get environmentTitle; String get role; bool get isActive; int get priority; String get status; List<String> get experienceNames;@UuidValueConverter() UuidValue? get environmentConfigId; String? get environmentConfigKey;
/// Create a copy of NetworkEnvironmentDescriptor
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkEnvironmentDescriptorCopyWith<NetworkEnvironmentDescriptor> get copyWith => _$NetworkEnvironmentDescriptorCopyWithImpl<NetworkEnvironmentDescriptor>(this as NetworkEnvironmentDescriptor, _$identity);

  /// Serializes this NetworkEnvironmentDescriptor to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkEnvironmentDescriptor&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentKey, environmentKey) || other.environmentKey == environmentKey)&&(identical(other.environmentTitle, environmentTitle) || other.environmentTitle == environmentTitle)&&(identical(other.role, role) || other.role == role)&&(identical(other.isActive, isActive) || other.isActive == isActive)&&(identical(other.priority, priority) || other.priority == priority)&&(identical(other.status, status) || other.status == status)&&const DeepCollectionEquality().equals(other.experienceNames, experienceNames)&&(identical(other.environmentConfigId, environmentConfigId) || other.environmentConfigId == environmentConfigId)&&(identical(other.environmentConfigKey, environmentConfigKey) || other.environmentConfigKey == environmentConfigKey));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,nodeId,environmentId,environmentKey,environmentTitle,role,isActive,priority,status,const DeepCollectionEquality().hash(experienceNames),environmentConfigId,environmentConfigKey);

@override
String toString() {
  return 'NetworkEnvironmentDescriptor(nodeId: $nodeId, environmentId: $environmentId, environmentKey: $environmentKey, environmentTitle: $environmentTitle, role: $role, isActive: $isActive, priority: $priority, status: $status, experienceNames: $experienceNames, environmentConfigId: $environmentConfigId, environmentConfigKey: $environmentConfigKey)';
}


}

/// @nodoc
abstract mixin class $NetworkEnvironmentDescriptorCopyWith<$Res>  {
  factory $NetworkEnvironmentDescriptorCopyWith(NetworkEnvironmentDescriptor value, $Res Function(NetworkEnvironmentDescriptor) _then) = _$NetworkEnvironmentDescriptorCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? nodeId,@UuidValueConverter() UuidValue environmentId, String? environmentKey, String? environmentTitle, String role, bool isActive, int priority, String status, List<String> experienceNames,@UuidValueConverter() UuidValue? environmentConfigId, String? environmentConfigKey
});




}
/// @nodoc
class _$NetworkEnvironmentDescriptorCopyWithImpl<$Res>
    implements $NetworkEnvironmentDescriptorCopyWith<$Res> {
  _$NetworkEnvironmentDescriptorCopyWithImpl(this._self, this._then);

  final NetworkEnvironmentDescriptor _self;
  final $Res Function(NetworkEnvironmentDescriptor) _then;

/// Create a copy of NetworkEnvironmentDescriptor
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? nodeId = freezed,Object? environmentId = null,Object? environmentKey = freezed,Object? environmentTitle = freezed,Object? role = null,Object? isActive = null,Object? priority = null,Object? status = null,Object? experienceNames = null,Object? environmentConfigId = freezed,Object? environmentConfigKey = freezed,}) {
  return _then(_self.copyWith(
nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentId: null == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentKey: freezed == environmentKey ? _self.environmentKey : environmentKey // ignore: cast_nullable_to_non_nullable
as String?,environmentTitle: freezed == environmentTitle ? _self.environmentTitle : environmentTitle // ignore: cast_nullable_to_non_nullable
as String?,role: null == role ? _self.role : role // ignore: cast_nullable_to_non_nullable
as String,isActive: null == isActive ? _self.isActive : isActive // ignore: cast_nullable_to_non_nullable
as bool,priority: null == priority ? _self.priority : priority // ignore: cast_nullable_to_non_nullable
as int,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,experienceNames: null == experienceNames ? _self.experienceNames : experienceNames // ignore: cast_nullable_to_non_nullable
as List<String>,environmentConfigId: freezed == environmentConfigId ? _self.environmentConfigId : environmentConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentConfigKey: freezed == environmentConfigKey ? _self.environmentConfigKey : environmentConfigKey // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkEnvironmentDescriptor].
extension NetworkEnvironmentDescriptorPatterns on NetworkEnvironmentDescriptor {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkEnvironmentDescriptor value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkEnvironmentDescriptor() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkEnvironmentDescriptor value)  def,}){
final _that = this;
switch (_that) {
case _NetworkEnvironmentDescriptor():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkEnvironmentDescriptor value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkEnvironmentDescriptor() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue environmentId,  String? environmentKey,  String? environmentTitle,  String role,  bool isActive,  int priority,  String status,  List<String> experienceNames, @UuidValueConverter()  UuidValue? environmentConfigId,  String? environmentConfigKey)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkEnvironmentDescriptor() when def != null:
return def(_that.nodeId,_that.environmentId,_that.environmentKey,_that.environmentTitle,_that.role,_that.isActive,_that.priority,_that.status,_that.experienceNames,_that.environmentConfigId,_that.environmentConfigKey);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue environmentId,  String? environmentKey,  String? environmentTitle,  String role,  bool isActive,  int priority,  String status,  List<String> experienceNames, @UuidValueConverter()  UuidValue? environmentConfigId,  String? environmentConfigKey)  def,}) {final _that = this;
switch (_that) {
case _NetworkEnvironmentDescriptor():
return def(_that.nodeId,_that.environmentId,_that.environmentKey,_that.environmentTitle,_that.role,_that.isActive,_that.priority,_that.status,_that.experienceNames,_that.environmentConfigId,_that.environmentConfigKey);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? nodeId, @UuidValueConverter()  UuidValue environmentId,  String? environmentKey,  String? environmentTitle,  String role,  bool isActive,  int priority,  String status,  List<String> experienceNames, @UuidValueConverter()  UuidValue? environmentConfigId,  String? environmentConfigKey)?  def,}) {final _that = this;
switch (_that) {
case _NetworkEnvironmentDescriptor() when def != null:
return def(_that.nodeId,_that.environmentId,_that.environmentKey,_that.environmentTitle,_that.role,_that.isActive,_that.priority,_that.status,_that.experienceNames,_that.environmentConfigId,_that.environmentConfigKey);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkEnvironmentDescriptor implements NetworkEnvironmentDescriptor {
   _NetworkEnvironmentDescriptor({@UuidValueConverter() this.nodeId, @UuidValueConverter() required this.environmentId, this.environmentKey, this.environmentTitle, required this.role, required this.isActive, required this.priority, required this.status, final  List<String> experienceNames = const [], @UuidValueConverter() this.environmentConfigId, this.environmentConfigKey}): _experienceNames = experienceNames;
  factory _NetworkEnvironmentDescriptor.fromJson(Map<String, dynamic> json) => _$NetworkEnvironmentDescriptorFromJson(json);

@override@UuidValueConverter() final  UuidValue? nodeId;
@override@UuidValueConverter() final  UuidValue environmentId;
@override final  String? environmentKey;
@override final  String? environmentTitle;
@override final  String role;
@override final  bool isActive;
@override final  int priority;
@override final  String status;
 final  List<String> _experienceNames;
@override@JsonKey() List<String> get experienceNames {
  if (_experienceNames is EqualUnmodifiableListView) return _experienceNames;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_experienceNames);
}

@override@UuidValueConverter() final  UuidValue? environmentConfigId;
@override final  String? environmentConfigKey;

/// Create a copy of NetworkEnvironmentDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkEnvironmentDescriptorCopyWith<_NetworkEnvironmentDescriptor> get copyWith => __$NetworkEnvironmentDescriptorCopyWithImpl<_NetworkEnvironmentDescriptor>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkEnvironmentDescriptorToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkEnvironmentDescriptor&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentKey, environmentKey) || other.environmentKey == environmentKey)&&(identical(other.environmentTitle, environmentTitle) || other.environmentTitle == environmentTitle)&&(identical(other.role, role) || other.role == role)&&(identical(other.isActive, isActive) || other.isActive == isActive)&&(identical(other.priority, priority) || other.priority == priority)&&(identical(other.status, status) || other.status == status)&&const DeepCollectionEquality().equals(other._experienceNames, _experienceNames)&&(identical(other.environmentConfigId, environmentConfigId) || other.environmentConfigId == environmentConfigId)&&(identical(other.environmentConfigKey, environmentConfigKey) || other.environmentConfigKey == environmentConfigKey));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,nodeId,environmentId,environmentKey,environmentTitle,role,isActive,priority,status,const DeepCollectionEquality().hash(_experienceNames),environmentConfigId,environmentConfigKey);

@override
String toString() {
  return 'NetworkEnvironmentDescriptor.def(nodeId: $nodeId, environmentId: $environmentId, environmentKey: $environmentKey, environmentTitle: $environmentTitle, role: $role, isActive: $isActive, priority: $priority, status: $status, experienceNames: $experienceNames, environmentConfigId: $environmentConfigId, environmentConfigKey: $environmentConfigKey)';
}


}

/// @nodoc
abstract mixin class _$NetworkEnvironmentDescriptorCopyWith<$Res> implements $NetworkEnvironmentDescriptorCopyWith<$Res> {
  factory _$NetworkEnvironmentDescriptorCopyWith(_NetworkEnvironmentDescriptor value, $Res Function(_NetworkEnvironmentDescriptor) _then) = __$NetworkEnvironmentDescriptorCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? nodeId,@UuidValueConverter() UuidValue environmentId, String? environmentKey, String? environmentTitle, String role, bool isActive, int priority, String status, List<String> experienceNames,@UuidValueConverter() UuidValue? environmentConfigId, String? environmentConfigKey
});




}
/// @nodoc
class __$NetworkEnvironmentDescriptorCopyWithImpl<$Res>
    implements _$NetworkEnvironmentDescriptorCopyWith<$Res> {
  __$NetworkEnvironmentDescriptorCopyWithImpl(this._self, this._then);

  final _NetworkEnvironmentDescriptor _self;
  final $Res Function(_NetworkEnvironmentDescriptor) _then;

/// Create a copy of NetworkEnvironmentDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? nodeId = freezed,Object? environmentId = null,Object? environmentKey = freezed,Object? environmentTitle = freezed,Object? role = null,Object? isActive = null,Object? priority = null,Object? status = null,Object? experienceNames = null,Object? environmentConfigId = freezed,Object? environmentConfigKey = freezed,}) {
  return _then(_NetworkEnvironmentDescriptor(
nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentId: null == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentKey: freezed == environmentKey ? _self.environmentKey : environmentKey // ignore: cast_nullable_to_non_nullable
as String?,environmentTitle: freezed == environmentTitle ? _self.environmentTitle : environmentTitle // ignore: cast_nullable_to_non_nullable
as String?,role: null == role ? _self.role : role // ignore: cast_nullable_to_non_nullable
as String,isActive: null == isActive ? _self.isActive : isActive // ignore: cast_nullable_to_non_nullable
as bool,priority: null == priority ? _self.priority : priority // ignore: cast_nullable_to_non_nullable
as int,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,experienceNames: null == experienceNames ? _self._experienceNames : experienceNames // ignore: cast_nullable_to_non_nullable
as List<String>,environmentConfigId: freezed == environmentConfigId ? _self.environmentConfigId : environmentConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentConfigKey: freezed == environmentConfigKey ? _self.environmentConfigKey : environmentConfigKey // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$NetworkResolvedHostedServiceRoute {

@UuidValueConverter() UuidValue get providerNodeId; String get providerNodeBaseUrl;@UuidValueConverter() UuidValue? get routeConnectionId; NetworkHostedServiceDescriptor get hostedService;
/// Create a copy of NetworkResolvedHostedServiceRoute
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkResolvedHostedServiceRouteCopyWith<NetworkResolvedHostedServiceRoute> get copyWith => _$NetworkResolvedHostedServiceRouteCopyWithImpl<NetworkResolvedHostedServiceRoute>(this as NetworkResolvedHostedServiceRoute, _$identity);

  /// Serializes this NetworkResolvedHostedServiceRoute to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkResolvedHostedServiceRoute&&(identical(other.providerNodeId, providerNodeId) || other.providerNodeId == providerNodeId)&&(identical(other.providerNodeBaseUrl, providerNodeBaseUrl) || other.providerNodeBaseUrl == providerNodeBaseUrl)&&(identical(other.routeConnectionId, routeConnectionId) || other.routeConnectionId == routeConnectionId)&&(identical(other.hostedService, hostedService) || other.hostedService == hostedService));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,providerNodeId,providerNodeBaseUrl,routeConnectionId,hostedService);

@override
String toString() {
  return 'NetworkResolvedHostedServiceRoute(providerNodeId: $providerNodeId, providerNodeBaseUrl: $providerNodeBaseUrl, routeConnectionId: $routeConnectionId, hostedService: $hostedService)';
}


}

/// @nodoc
abstract mixin class $NetworkResolvedHostedServiceRouteCopyWith<$Res>  {
  factory $NetworkResolvedHostedServiceRouteCopyWith(NetworkResolvedHostedServiceRoute value, $Res Function(NetworkResolvedHostedServiceRoute) _then) = _$NetworkResolvedHostedServiceRouteCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue providerNodeId, String providerNodeBaseUrl,@UuidValueConverter() UuidValue? routeConnectionId, NetworkHostedServiceDescriptor hostedService
});


$NetworkHostedServiceDescriptorCopyWith<$Res> get hostedService;

}
/// @nodoc
class _$NetworkResolvedHostedServiceRouteCopyWithImpl<$Res>
    implements $NetworkResolvedHostedServiceRouteCopyWith<$Res> {
  _$NetworkResolvedHostedServiceRouteCopyWithImpl(this._self, this._then);

  final NetworkResolvedHostedServiceRoute _self;
  final $Res Function(NetworkResolvedHostedServiceRoute) _then;

/// Create a copy of NetworkResolvedHostedServiceRoute
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? providerNodeId = null,Object? providerNodeBaseUrl = null,Object? routeConnectionId = freezed,Object? hostedService = null,}) {
  return _then(_self.copyWith(
providerNodeId: null == providerNodeId ? _self.providerNodeId : providerNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,providerNodeBaseUrl: null == providerNodeBaseUrl ? _self.providerNodeBaseUrl : providerNodeBaseUrl // ignore: cast_nullable_to_non_nullable
as String,routeConnectionId: freezed == routeConnectionId ? _self.routeConnectionId : routeConnectionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,hostedService: null == hostedService ? _self.hostedService : hostedService // ignore: cast_nullable_to_non_nullable
as NetworkHostedServiceDescriptor,
  ));
}
/// Create a copy of NetworkResolvedHostedServiceRoute
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkHostedServiceDescriptorCopyWith<$Res> get hostedService {
  
  return $NetworkHostedServiceDescriptorCopyWith<$Res>(_self.hostedService, (value) {
    return _then(_self.copyWith(hostedService: value));
  });
}
}


/// Adds pattern-matching-related methods to [NetworkResolvedHostedServiceRoute].
extension NetworkResolvedHostedServiceRoutePatterns on NetworkResolvedHostedServiceRoute {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkResolvedHostedServiceRoute value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkResolvedHostedServiceRoute() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkResolvedHostedServiceRoute value)  def,}){
final _that = this;
switch (_that) {
case _NetworkResolvedHostedServiceRoute():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkResolvedHostedServiceRoute value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkResolvedHostedServiceRoute() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue providerNodeId,  String providerNodeBaseUrl, @UuidValueConverter()  UuidValue? routeConnectionId,  NetworkHostedServiceDescriptor hostedService)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkResolvedHostedServiceRoute() when def != null:
return def(_that.providerNodeId,_that.providerNodeBaseUrl,_that.routeConnectionId,_that.hostedService);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue providerNodeId,  String providerNodeBaseUrl, @UuidValueConverter()  UuidValue? routeConnectionId,  NetworkHostedServiceDescriptor hostedService)  def,}) {final _that = this;
switch (_that) {
case _NetworkResolvedHostedServiceRoute():
return def(_that.providerNodeId,_that.providerNodeBaseUrl,_that.routeConnectionId,_that.hostedService);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue providerNodeId,  String providerNodeBaseUrl, @UuidValueConverter()  UuidValue? routeConnectionId,  NetworkHostedServiceDescriptor hostedService)?  def,}) {final _that = this;
switch (_that) {
case _NetworkResolvedHostedServiceRoute() when def != null:
return def(_that.providerNodeId,_that.providerNodeBaseUrl,_that.routeConnectionId,_that.hostedService);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkResolvedHostedServiceRoute implements NetworkResolvedHostedServiceRoute {
   _NetworkResolvedHostedServiceRoute({@UuidValueConverter() required this.providerNodeId, required this.providerNodeBaseUrl, @UuidValueConverter() this.routeConnectionId, required this.hostedService});
  factory _NetworkResolvedHostedServiceRoute.fromJson(Map<String, dynamic> json) => _$NetworkResolvedHostedServiceRouteFromJson(json);

@override@UuidValueConverter() final  UuidValue providerNodeId;
@override final  String providerNodeBaseUrl;
@override@UuidValueConverter() final  UuidValue? routeConnectionId;
@override final  NetworkHostedServiceDescriptor hostedService;

/// Create a copy of NetworkResolvedHostedServiceRoute
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkResolvedHostedServiceRouteCopyWith<_NetworkResolvedHostedServiceRoute> get copyWith => __$NetworkResolvedHostedServiceRouteCopyWithImpl<_NetworkResolvedHostedServiceRoute>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkResolvedHostedServiceRouteToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkResolvedHostedServiceRoute&&(identical(other.providerNodeId, providerNodeId) || other.providerNodeId == providerNodeId)&&(identical(other.providerNodeBaseUrl, providerNodeBaseUrl) || other.providerNodeBaseUrl == providerNodeBaseUrl)&&(identical(other.routeConnectionId, routeConnectionId) || other.routeConnectionId == routeConnectionId)&&(identical(other.hostedService, hostedService) || other.hostedService == hostedService));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,providerNodeId,providerNodeBaseUrl,routeConnectionId,hostedService);

@override
String toString() {
  return 'NetworkResolvedHostedServiceRoute.def(providerNodeId: $providerNodeId, providerNodeBaseUrl: $providerNodeBaseUrl, routeConnectionId: $routeConnectionId, hostedService: $hostedService)';
}


}

/// @nodoc
abstract mixin class _$NetworkResolvedHostedServiceRouteCopyWith<$Res> implements $NetworkResolvedHostedServiceRouteCopyWith<$Res> {
  factory _$NetworkResolvedHostedServiceRouteCopyWith(_NetworkResolvedHostedServiceRoute value, $Res Function(_NetworkResolvedHostedServiceRoute) _then) = __$NetworkResolvedHostedServiceRouteCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue providerNodeId, String providerNodeBaseUrl,@UuidValueConverter() UuidValue? routeConnectionId, NetworkHostedServiceDescriptor hostedService
});


@override $NetworkHostedServiceDescriptorCopyWith<$Res> get hostedService;

}
/// @nodoc
class __$NetworkResolvedHostedServiceRouteCopyWithImpl<$Res>
    implements _$NetworkResolvedHostedServiceRouteCopyWith<$Res> {
  __$NetworkResolvedHostedServiceRouteCopyWithImpl(this._self, this._then);

  final _NetworkResolvedHostedServiceRoute _self;
  final $Res Function(_NetworkResolvedHostedServiceRoute) _then;

/// Create a copy of NetworkResolvedHostedServiceRoute
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? providerNodeId = null,Object? providerNodeBaseUrl = null,Object? routeConnectionId = freezed,Object? hostedService = null,}) {
  return _then(_NetworkResolvedHostedServiceRoute(
providerNodeId: null == providerNodeId ? _self.providerNodeId : providerNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,providerNodeBaseUrl: null == providerNodeBaseUrl ? _self.providerNodeBaseUrl : providerNodeBaseUrl // ignore: cast_nullable_to_non_nullable
as String,routeConnectionId: freezed == routeConnectionId ? _self.routeConnectionId : routeConnectionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,hostedService: null == hostedService ? _self.hostedService : hostedService // ignore: cast_nullable_to_non_nullable
as NetworkHostedServiceDescriptor,
  ));
}

/// Create a copy of NetworkResolvedHostedServiceRoute
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkHostedServiceDescriptorCopyWith<$Res> get hostedService {
  
  return $NetworkHostedServiceDescriptorCopyWith<$Res>(_self.hostedService, (value) {
    return _then(_self.copyWith(hostedService: value));
  });
}
}


/// @nodoc
mixin _$NetworkTerritoryNodeDescriptor {

 NetworkNodeRouteDescriptor get node; List<NetworkEnvironmentDescriptor> get environments; List<NetworkHostedServiceDescriptor> get hostedServices; List<NetworkPeerDescriptor> get peers;
/// Create a copy of NetworkTerritoryNodeDescriptor
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkTerritoryNodeDescriptorCopyWith<NetworkTerritoryNodeDescriptor> get copyWith => _$NetworkTerritoryNodeDescriptorCopyWithImpl<NetworkTerritoryNodeDescriptor>(this as NetworkTerritoryNodeDescriptor, _$identity);

  /// Serializes this NetworkTerritoryNodeDescriptor to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkTerritoryNodeDescriptor&&(identical(other.node, node) || other.node == node)&&const DeepCollectionEquality().equals(other.environments, environments)&&const DeepCollectionEquality().equals(other.hostedServices, hostedServices)&&const DeepCollectionEquality().equals(other.peers, peers));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,node,const DeepCollectionEquality().hash(environments),const DeepCollectionEquality().hash(hostedServices),const DeepCollectionEquality().hash(peers));

@override
String toString() {
  return 'NetworkTerritoryNodeDescriptor(node: $node, environments: $environments, hostedServices: $hostedServices, peers: $peers)';
}


}

/// @nodoc
abstract mixin class $NetworkTerritoryNodeDescriptorCopyWith<$Res>  {
  factory $NetworkTerritoryNodeDescriptorCopyWith(NetworkTerritoryNodeDescriptor value, $Res Function(NetworkTerritoryNodeDescriptor) _then) = _$NetworkTerritoryNodeDescriptorCopyWithImpl;
@useResult
$Res call({
 NetworkNodeRouteDescriptor node, List<NetworkEnvironmentDescriptor> environments, List<NetworkHostedServiceDescriptor> hostedServices, List<NetworkPeerDescriptor> peers
});


$NetworkNodeRouteDescriptorCopyWith<$Res> get node;

}
/// @nodoc
class _$NetworkTerritoryNodeDescriptorCopyWithImpl<$Res>
    implements $NetworkTerritoryNodeDescriptorCopyWith<$Res> {
  _$NetworkTerritoryNodeDescriptorCopyWithImpl(this._self, this._then);

  final NetworkTerritoryNodeDescriptor _self;
  final $Res Function(NetworkTerritoryNodeDescriptor) _then;

/// Create a copy of NetworkTerritoryNodeDescriptor
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? node = null,Object? environments = null,Object? hostedServices = null,Object? peers = null,}) {
  return _then(_self.copyWith(
node: null == node ? _self.node : node // ignore: cast_nullable_to_non_nullable
as NetworkNodeRouteDescriptor,environments: null == environments ? _self.environments : environments // ignore: cast_nullable_to_non_nullable
as List<NetworkEnvironmentDescriptor>,hostedServices: null == hostedServices ? _self.hostedServices : hostedServices // ignore: cast_nullable_to_non_nullable
as List<NetworkHostedServiceDescriptor>,peers: null == peers ? _self.peers : peers // ignore: cast_nullable_to_non_nullable
as List<NetworkPeerDescriptor>,
  ));
}
/// Create a copy of NetworkTerritoryNodeDescriptor
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodeRouteDescriptorCopyWith<$Res> get node {
  
  return $NetworkNodeRouteDescriptorCopyWith<$Res>(_self.node, (value) {
    return _then(_self.copyWith(node: value));
  });
}
}


/// Adds pattern-matching-related methods to [NetworkTerritoryNodeDescriptor].
extension NetworkTerritoryNodeDescriptorPatterns on NetworkTerritoryNodeDescriptor {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkTerritoryNodeDescriptor value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkTerritoryNodeDescriptor() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkTerritoryNodeDescriptor value)  def,}){
final _that = this;
switch (_that) {
case _NetworkTerritoryNodeDescriptor():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkTerritoryNodeDescriptor value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkTerritoryNodeDescriptor() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( NetworkNodeRouteDescriptor node,  List<NetworkEnvironmentDescriptor> environments,  List<NetworkHostedServiceDescriptor> hostedServices,  List<NetworkPeerDescriptor> peers)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkTerritoryNodeDescriptor() when def != null:
return def(_that.node,_that.environments,_that.hostedServices,_that.peers);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( NetworkNodeRouteDescriptor node,  List<NetworkEnvironmentDescriptor> environments,  List<NetworkHostedServiceDescriptor> hostedServices,  List<NetworkPeerDescriptor> peers)  def,}) {final _that = this;
switch (_that) {
case _NetworkTerritoryNodeDescriptor():
return def(_that.node,_that.environments,_that.hostedServices,_that.peers);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( NetworkNodeRouteDescriptor node,  List<NetworkEnvironmentDescriptor> environments,  List<NetworkHostedServiceDescriptor> hostedServices,  List<NetworkPeerDescriptor> peers)?  def,}) {final _that = this;
switch (_that) {
case _NetworkTerritoryNodeDescriptor() when def != null:
return def(_that.node,_that.environments,_that.hostedServices,_that.peers);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkTerritoryNodeDescriptor implements NetworkTerritoryNodeDescriptor {
   _NetworkTerritoryNodeDescriptor({required this.node, final  List<NetworkEnvironmentDescriptor> environments = const [], final  List<NetworkHostedServiceDescriptor> hostedServices = const [], final  List<NetworkPeerDescriptor> peers = const []}): _environments = environments,_hostedServices = hostedServices,_peers = peers;
  factory _NetworkTerritoryNodeDescriptor.fromJson(Map<String, dynamic> json) => _$NetworkTerritoryNodeDescriptorFromJson(json);

@override final  NetworkNodeRouteDescriptor node;
 final  List<NetworkEnvironmentDescriptor> _environments;
@override@JsonKey() List<NetworkEnvironmentDescriptor> get environments {
  if (_environments is EqualUnmodifiableListView) return _environments;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_environments);
}

 final  List<NetworkHostedServiceDescriptor> _hostedServices;
@override@JsonKey() List<NetworkHostedServiceDescriptor> get hostedServices {
  if (_hostedServices is EqualUnmodifiableListView) return _hostedServices;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_hostedServices);
}

 final  List<NetworkPeerDescriptor> _peers;
@override@JsonKey() List<NetworkPeerDescriptor> get peers {
  if (_peers is EqualUnmodifiableListView) return _peers;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_peers);
}


/// Create a copy of NetworkTerritoryNodeDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkTerritoryNodeDescriptorCopyWith<_NetworkTerritoryNodeDescriptor> get copyWith => __$NetworkTerritoryNodeDescriptorCopyWithImpl<_NetworkTerritoryNodeDescriptor>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkTerritoryNodeDescriptorToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkTerritoryNodeDescriptor&&(identical(other.node, node) || other.node == node)&&const DeepCollectionEquality().equals(other._environments, _environments)&&const DeepCollectionEquality().equals(other._hostedServices, _hostedServices)&&const DeepCollectionEquality().equals(other._peers, _peers));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,node,const DeepCollectionEquality().hash(_environments),const DeepCollectionEquality().hash(_hostedServices),const DeepCollectionEquality().hash(_peers));

@override
String toString() {
  return 'NetworkTerritoryNodeDescriptor.def(node: $node, environments: $environments, hostedServices: $hostedServices, peers: $peers)';
}


}

/// @nodoc
abstract mixin class _$NetworkTerritoryNodeDescriptorCopyWith<$Res> implements $NetworkTerritoryNodeDescriptorCopyWith<$Res> {
  factory _$NetworkTerritoryNodeDescriptorCopyWith(_NetworkTerritoryNodeDescriptor value, $Res Function(_NetworkTerritoryNodeDescriptor) _then) = __$NetworkTerritoryNodeDescriptorCopyWithImpl;
@override @useResult
$Res call({
 NetworkNodeRouteDescriptor node, List<NetworkEnvironmentDescriptor> environments, List<NetworkHostedServiceDescriptor> hostedServices, List<NetworkPeerDescriptor> peers
});


@override $NetworkNodeRouteDescriptorCopyWith<$Res> get node;

}
/// @nodoc
class __$NetworkTerritoryNodeDescriptorCopyWithImpl<$Res>
    implements _$NetworkTerritoryNodeDescriptorCopyWith<$Res> {
  __$NetworkTerritoryNodeDescriptorCopyWithImpl(this._self, this._then);

  final _NetworkTerritoryNodeDescriptor _self;
  final $Res Function(_NetworkTerritoryNodeDescriptor) _then;

/// Create a copy of NetworkTerritoryNodeDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? node = null,Object? environments = null,Object? hostedServices = null,Object? peers = null,}) {
  return _then(_NetworkTerritoryNodeDescriptor(
node: null == node ? _self.node : node // ignore: cast_nullable_to_non_nullable
as NetworkNodeRouteDescriptor,environments: null == environments ? _self._environments : environments // ignore: cast_nullable_to_non_nullable
as List<NetworkEnvironmentDescriptor>,hostedServices: null == hostedServices ? _self._hostedServices : hostedServices // ignore: cast_nullable_to_non_nullable
as List<NetworkHostedServiceDescriptor>,peers: null == peers ? _self._peers : peers // ignore: cast_nullable_to_non_nullable
as List<NetworkPeerDescriptor>,
  ));
}

/// Create a copy of NetworkTerritoryNodeDescriptor
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodeRouteDescriptorCopyWith<$Res> get node {
  
  return $NetworkNodeRouteDescriptorCopyWith<$Res>(_self.node, (value) {
    return _then(_self.copyWith(node: value));
  });
}
}


/// @nodoc
mixin _$NetworkExperienceServiceCandidate {

 NetworkHostedServiceDescriptor get hostedService;@UuidValueConverter() UuidValue get providerNodeId; String? get providerNodeBaseUrl;@UuidValueConverter() UuidValue? get routeConnectionId; String get routeStatus; List<String> get matchedServicePackageNames; List<String> get matchedEndpointRefs; List<String> get missingServicePackageNames; List<String> get missingEndpointRefs;
/// Create a copy of NetworkExperienceServiceCandidate
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkExperienceServiceCandidateCopyWith<NetworkExperienceServiceCandidate> get copyWith => _$NetworkExperienceServiceCandidateCopyWithImpl<NetworkExperienceServiceCandidate>(this as NetworkExperienceServiceCandidate, _$identity);

  /// Serializes this NetworkExperienceServiceCandidate to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkExperienceServiceCandidate&&(identical(other.hostedService, hostedService) || other.hostedService == hostedService)&&(identical(other.providerNodeId, providerNodeId) || other.providerNodeId == providerNodeId)&&(identical(other.providerNodeBaseUrl, providerNodeBaseUrl) || other.providerNodeBaseUrl == providerNodeBaseUrl)&&(identical(other.routeConnectionId, routeConnectionId) || other.routeConnectionId == routeConnectionId)&&(identical(other.routeStatus, routeStatus) || other.routeStatus == routeStatus)&&const DeepCollectionEquality().equals(other.matchedServicePackageNames, matchedServicePackageNames)&&const DeepCollectionEquality().equals(other.matchedEndpointRefs, matchedEndpointRefs)&&const DeepCollectionEquality().equals(other.missingServicePackageNames, missingServicePackageNames)&&const DeepCollectionEquality().equals(other.missingEndpointRefs, missingEndpointRefs));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,hostedService,providerNodeId,providerNodeBaseUrl,routeConnectionId,routeStatus,const DeepCollectionEquality().hash(matchedServicePackageNames),const DeepCollectionEquality().hash(matchedEndpointRefs),const DeepCollectionEquality().hash(missingServicePackageNames),const DeepCollectionEquality().hash(missingEndpointRefs));

@override
String toString() {
  return 'NetworkExperienceServiceCandidate(hostedService: $hostedService, providerNodeId: $providerNodeId, providerNodeBaseUrl: $providerNodeBaseUrl, routeConnectionId: $routeConnectionId, routeStatus: $routeStatus, matchedServicePackageNames: $matchedServicePackageNames, matchedEndpointRefs: $matchedEndpointRefs, missingServicePackageNames: $missingServicePackageNames, missingEndpointRefs: $missingEndpointRefs)';
}


}

/// @nodoc
abstract mixin class $NetworkExperienceServiceCandidateCopyWith<$Res>  {
  factory $NetworkExperienceServiceCandidateCopyWith(NetworkExperienceServiceCandidate value, $Res Function(NetworkExperienceServiceCandidate) _then) = _$NetworkExperienceServiceCandidateCopyWithImpl;
@useResult
$Res call({
 NetworkHostedServiceDescriptor hostedService,@UuidValueConverter() UuidValue providerNodeId, String? providerNodeBaseUrl,@UuidValueConverter() UuidValue? routeConnectionId, String routeStatus, List<String> matchedServicePackageNames, List<String> matchedEndpointRefs, List<String> missingServicePackageNames, List<String> missingEndpointRefs
});


$NetworkHostedServiceDescriptorCopyWith<$Res> get hostedService;

}
/// @nodoc
class _$NetworkExperienceServiceCandidateCopyWithImpl<$Res>
    implements $NetworkExperienceServiceCandidateCopyWith<$Res> {
  _$NetworkExperienceServiceCandidateCopyWithImpl(this._self, this._then);

  final NetworkExperienceServiceCandidate _self;
  final $Res Function(NetworkExperienceServiceCandidate) _then;

/// Create a copy of NetworkExperienceServiceCandidate
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? hostedService = null,Object? providerNodeId = null,Object? providerNodeBaseUrl = freezed,Object? routeConnectionId = freezed,Object? routeStatus = null,Object? matchedServicePackageNames = null,Object? matchedEndpointRefs = null,Object? missingServicePackageNames = null,Object? missingEndpointRefs = null,}) {
  return _then(_self.copyWith(
hostedService: null == hostedService ? _self.hostedService : hostedService // ignore: cast_nullable_to_non_nullable
as NetworkHostedServiceDescriptor,providerNodeId: null == providerNodeId ? _self.providerNodeId : providerNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,providerNodeBaseUrl: freezed == providerNodeBaseUrl ? _self.providerNodeBaseUrl : providerNodeBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,routeConnectionId: freezed == routeConnectionId ? _self.routeConnectionId : routeConnectionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,routeStatus: null == routeStatus ? _self.routeStatus : routeStatus // ignore: cast_nullable_to_non_nullable
as String,matchedServicePackageNames: null == matchedServicePackageNames ? _self.matchedServicePackageNames : matchedServicePackageNames // ignore: cast_nullable_to_non_nullable
as List<String>,matchedEndpointRefs: null == matchedEndpointRefs ? _self.matchedEndpointRefs : matchedEndpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,missingServicePackageNames: null == missingServicePackageNames ? _self.missingServicePackageNames : missingServicePackageNames // ignore: cast_nullable_to_non_nullable
as List<String>,missingEndpointRefs: null == missingEndpointRefs ? _self.missingEndpointRefs : missingEndpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,
  ));
}
/// Create a copy of NetworkExperienceServiceCandidate
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkHostedServiceDescriptorCopyWith<$Res> get hostedService {
  
  return $NetworkHostedServiceDescriptorCopyWith<$Res>(_self.hostedService, (value) {
    return _then(_self.copyWith(hostedService: value));
  });
}
}


/// Adds pattern-matching-related methods to [NetworkExperienceServiceCandidate].
extension NetworkExperienceServiceCandidatePatterns on NetworkExperienceServiceCandidate {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkExperienceServiceCandidate value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkExperienceServiceCandidate() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkExperienceServiceCandidate value)  def,}){
final _that = this;
switch (_that) {
case _NetworkExperienceServiceCandidate():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkExperienceServiceCandidate value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkExperienceServiceCandidate() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( NetworkHostedServiceDescriptor hostedService, @UuidValueConverter()  UuidValue providerNodeId,  String? providerNodeBaseUrl, @UuidValueConverter()  UuidValue? routeConnectionId,  String routeStatus,  List<String> matchedServicePackageNames,  List<String> matchedEndpointRefs,  List<String> missingServicePackageNames,  List<String> missingEndpointRefs)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkExperienceServiceCandidate() when def != null:
return def(_that.hostedService,_that.providerNodeId,_that.providerNodeBaseUrl,_that.routeConnectionId,_that.routeStatus,_that.matchedServicePackageNames,_that.matchedEndpointRefs,_that.missingServicePackageNames,_that.missingEndpointRefs);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( NetworkHostedServiceDescriptor hostedService, @UuidValueConverter()  UuidValue providerNodeId,  String? providerNodeBaseUrl, @UuidValueConverter()  UuidValue? routeConnectionId,  String routeStatus,  List<String> matchedServicePackageNames,  List<String> matchedEndpointRefs,  List<String> missingServicePackageNames,  List<String> missingEndpointRefs)  def,}) {final _that = this;
switch (_that) {
case _NetworkExperienceServiceCandidate():
return def(_that.hostedService,_that.providerNodeId,_that.providerNodeBaseUrl,_that.routeConnectionId,_that.routeStatus,_that.matchedServicePackageNames,_that.matchedEndpointRefs,_that.missingServicePackageNames,_that.missingEndpointRefs);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( NetworkHostedServiceDescriptor hostedService, @UuidValueConverter()  UuidValue providerNodeId,  String? providerNodeBaseUrl, @UuidValueConverter()  UuidValue? routeConnectionId,  String routeStatus,  List<String> matchedServicePackageNames,  List<String> matchedEndpointRefs,  List<String> missingServicePackageNames,  List<String> missingEndpointRefs)?  def,}) {final _that = this;
switch (_that) {
case _NetworkExperienceServiceCandidate() when def != null:
return def(_that.hostedService,_that.providerNodeId,_that.providerNodeBaseUrl,_that.routeConnectionId,_that.routeStatus,_that.matchedServicePackageNames,_that.matchedEndpointRefs,_that.missingServicePackageNames,_that.missingEndpointRefs);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkExperienceServiceCandidate implements NetworkExperienceServiceCandidate {
   _NetworkExperienceServiceCandidate({required this.hostedService, @UuidValueConverter() required this.providerNodeId, this.providerNodeBaseUrl, @UuidValueConverter() this.routeConnectionId, required this.routeStatus, final  List<String> matchedServicePackageNames = const [], final  List<String> matchedEndpointRefs = const [], final  List<String> missingServicePackageNames = const [], final  List<String> missingEndpointRefs = const []}): _matchedServicePackageNames = matchedServicePackageNames,_matchedEndpointRefs = matchedEndpointRefs,_missingServicePackageNames = missingServicePackageNames,_missingEndpointRefs = missingEndpointRefs;
  factory _NetworkExperienceServiceCandidate.fromJson(Map<String, dynamic> json) => _$NetworkExperienceServiceCandidateFromJson(json);

@override final  NetworkHostedServiceDescriptor hostedService;
@override@UuidValueConverter() final  UuidValue providerNodeId;
@override final  String? providerNodeBaseUrl;
@override@UuidValueConverter() final  UuidValue? routeConnectionId;
@override final  String routeStatus;
 final  List<String> _matchedServicePackageNames;
@override@JsonKey() List<String> get matchedServicePackageNames {
  if (_matchedServicePackageNames is EqualUnmodifiableListView) return _matchedServicePackageNames;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_matchedServicePackageNames);
}

 final  List<String> _matchedEndpointRefs;
@override@JsonKey() List<String> get matchedEndpointRefs {
  if (_matchedEndpointRefs is EqualUnmodifiableListView) return _matchedEndpointRefs;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_matchedEndpointRefs);
}

 final  List<String> _missingServicePackageNames;
@override@JsonKey() List<String> get missingServicePackageNames {
  if (_missingServicePackageNames is EqualUnmodifiableListView) return _missingServicePackageNames;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_missingServicePackageNames);
}

 final  List<String> _missingEndpointRefs;
@override@JsonKey() List<String> get missingEndpointRefs {
  if (_missingEndpointRefs is EqualUnmodifiableListView) return _missingEndpointRefs;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_missingEndpointRefs);
}


/// Create a copy of NetworkExperienceServiceCandidate
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkExperienceServiceCandidateCopyWith<_NetworkExperienceServiceCandidate> get copyWith => __$NetworkExperienceServiceCandidateCopyWithImpl<_NetworkExperienceServiceCandidate>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkExperienceServiceCandidateToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkExperienceServiceCandidate&&(identical(other.hostedService, hostedService) || other.hostedService == hostedService)&&(identical(other.providerNodeId, providerNodeId) || other.providerNodeId == providerNodeId)&&(identical(other.providerNodeBaseUrl, providerNodeBaseUrl) || other.providerNodeBaseUrl == providerNodeBaseUrl)&&(identical(other.routeConnectionId, routeConnectionId) || other.routeConnectionId == routeConnectionId)&&(identical(other.routeStatus, routeStatus) || other.routeStatus == routeStatus)&&const DeepCollectionEquality().equals(other._matchedServicePackageNames, _matchedServicePackageNames)&&const DeepCollectionEquality().equals(other._matchedEndpointRefs, _matchedEndpointRefs)&&const DeepCollectionEquality().equals(other._missingServicePackageNames, _missingServicePackageNames)&&const DeepCollectionEquality().equals(other._missingEndpointRefs, _missingEndpointRefs));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,hostedService,providerNodeId,providerNodeBaseUrl,routeConnectionId,routeStatus,const DeepCollectionEquality().hash(_matchedServicePackageNames),const DeepCollectionEquality().hash(_matchedEndpointRefs),const DeepCollectionEquality().hash(_missingServicePackageNames),const DeepCollectionEquality().hash(_missingEndpointRefs));

@override
String toString() {
  return 'NetworkExperienceServiceCandidate.def(hostedService: $hostedService, providerNodeId: $providerNodeId, providerNodeBaseUrl: $providerNodeBaseUrl, routeConnectionId: $routeConnectionId, routeStatus: $routeStatus, matchedServicePackageNames: $matchedServicePackageNames, matchedEndpointRefs: $matchedEndpointRefs, missingServicePackageNames: $missingServicePackageNames, missingEndpointRefs: $missingEndpointRefs)';
}


}

/// @nodoc
abstract mixin class _$NetworkExperienceServiceCandidateCopyWith<$Res> implements $NetworkExperienceServiceCandidateCopyWith<$Res> {
  factory _$NetworkExperienceServiceCandidateCopyWith(_NetworkExperienceServiceCandidate value, $Res Function(_NetworkExperienceServiceCandidate) _then) = __$NetworkExperienceServiceCandidateCopyWithImpl;
@override @useResult
$Res call({
 NetworkHostedServiceDescriptor hostedService,@UuidValueConverter() UuidValue providerNodeId, String? providerNodeBaseUrl,@UuidValueConverter() UuidValue? routeConnectionId, String routeStatus, List<String> matchedServicePackageNames, List<String> matchedEndpointRefs, List<String> missingServicePackageNames, List<String> missingEndpointRefs
});


@override $NetworkHostedServiceDescriptorCopyWith<$Res> get hostedService;

}
/// @nodoc
class __$NetworkExperienceServiceCandidateCopyWithImpl<$Res>
    implements _$NetworkExperienceServiceCandidateCopyWith<$Res> {
  __$NetworkExperienceServiceCandidateCopyWithImpl(this._self, this._then);

  final _NetworkExperienceServiceCandidate _self;
  final $Res Function(_NetworkExperienceServiceCandidate) _then;

/// Create a copy of NetworkExperienceServiceCandidate
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? hostedService = null,Object? providerNodeId = null,Object? providerNodeBaseUrl = freezed,Object? routeConnectionId = freezed,Object? routeStatus = null,Object? matchedServicePackageNames = null,Object? matchedEndpointRefs = null,Object? missingServicePackageNames = null,Object? missingEndpointRefs = null,}) {
  return _then(_NetworkExperienceServiceCandidate(
hostedService: null == hostedService ? _self.hostedService : hostedService // ignore: cast_nullable_to_non_nullable
as NetworkHostedServiceDescriptor,providerNodeId: null == providerNodeId ? _self.providerNodeId : providerNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,providerNodeBaseUrl: freezed == providerNodeBaseUrl ? _self.providerNodeBaseUrl : providerNodeBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,routeConnectionId: freezed == routeConnectionId ? _self.routeConnectionId : routeConnectionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,routeStatus: null == routeStatus ? _self.routeStatus : routeStatus // ignore: cast_nullable_to_non_nullable
as String,matchedServicePackageNames: null == matchedServicePackageNames ? _self._matchedServicePackageNames : matchedServicePackageNames // ignore: cast_nullable_to_non_nullable
as List<String>,matchedEndpointRefs: null == matchedEndpointRefs ? _self._matchedEndpointRefs : matchedEndpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,missingServicePackageNames: null == missingServicePackageNames ? _self._missingServicePackageNames : missingServicePackageNames // ignore: cast_nullable_to_non_nullable
as List<String>,missingEndpointRefs: null == missingEndpointRefs ? _self._missingEndpointRefs : missingEndpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,
  ));
}

/// Create a copy of NetworkExperienceServiceCandidate
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkHostedServiceDescriptorCopyWith<$Res> get hostedService {
  
  return $NetworkHostedServiceDescriptorCopyWith<$Res>(_self.hostedService, (value) {
    return _then(_self.copyWith(hostedService: value));
  });
}
}


/// @nodoc
mixin _$NetworkExperienceTerritoryEntry {

 String get experienceName; NetworkNodeRouteDescriptor get node; NetworkEnvironmentDescriptor get environment; List<NetworkExperienceServiceCandidate> get serviceCandidates; String get routeStatus; List<String> get missingServicePackageNames; List<String> get missingEndpointRefs;
/// Create a copy of NetworkExperienceTerritoryEntry
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkExperienceTerritoryEntryCopyWith<NetworkExperienceTerritoryEntry> get copyWith => _$NetworkExperienceTerritoryEntryCopyWithImpl<NetworkExperienceTerritoryEntry>(this as NetworkExperienceTerritoryEntry, _$identity);

  /// Serializes this NetworkExperienceTerritoryEntry to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkExperienceTerritoryEntry&&(identical(other.experienceName, experienceName) || other.experienceName == experienceName)&&(identical(other.node, node) || other.node == node)&&(identical(other.environment, environment) || other.environment == environment)&&const DeepCollectionEquality().equals(other.serviceCandidates, serviceCandidates)&&(identical(other.routeStatus, routeStatus) || other.routeStatus == routeStatus)&&const DeepCollectionEquality().equals(other.missingServicePackageNames, missingServicePackageNames)&&const DeepCollectionEquality().equals(other.missingEndpointRefs, missingEndpointRefs));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,experienceName,node,environment,const DeepCollectionEquality().hash(serviceCandidates),routeStatus,const DeepCollectionEquality().hash(missingServicePackageNames),const DeepCollectionEquality().hash(missingEndpointRefs));

@override
String toString() {
  return 'NetworkExperienceTerritoryEntry(experienceName: $experienceName, node: $node, environment: $environment, serviceCandidates: $serviceCandidates, routeStatus: $routeStatus, missingServicePackageNames: $missingServicePackageNames, missingEndpointRefs: $missingEndpointRefs)';
}


}

/// @nodoc
abstract mixin class $NetworkExperienceTerritoryEntryCopyWith<$Res>  {
  factory $NetworkExperienceTerritoryEntryCopyWith(NetworkExperienceTerritoryEntry value, $Res Function(NetworkExperienceTerritoryEntry) _then) = _$NetworkExperienceTerritoryEntryCopyWithImpl;
@useResult
$Res call({
 String experienceName, NetworkNodeRouteDescriptor node, NetworkEnvironmentDescriptor environment, List<NetworkExperienceServiceCandidate> serviceCandidates, String routeStatus, List<String> missingServicePackageNames, List<String> missingEndpointRefs
});


$NetworkNodeRouteDescriptorCopyWith<$Res> get node;$NetworkEnvironmentDescriptorCopyWith<$Res> get environment;

}
/// @nodoc
class _$NetworkExperienceTerritoryEntryCopyWithImpl<$Res>
    implements $NetworkExperienceTerritoryEntryCopyWith<$Res> {
  _$NetworkExperienceTerritoryEntryCopyWithImpl(this._self, this._then);

  final NetworkExperienceTerritoryEntry _self;
  final $Res Function(NetworkExperienceTerritoryEntry) _then;

/// Create a copy of NetworkExperienceTerritoryEntry
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? experienceName = null,Object? node = null,Object? environment = null,Object? serviceCandidates = null,Object? routeStatus = null,Object? missingServicePackageNames = null,Object? missingEndpointRefs = null,}) {
  return _then(_self.copyWith(
experienceName: null == experienceName ? _self.experienceName : experienceName // ignore: cast_nullable_to_non_nullable
as String,node: null == node ? _self.node : node // ignore: cast_nullable_to_non_nullable
as NetworkNodeRouteDescriptor,environment: null == environment ? _self.environment : environment // ignore: cast_nullable_to_non_nullable
as NetworkEnvironmentDescriptor,serviceCandidates: null == serviceCandidates ? _self.serviceCandidates : serviceCandidates // ignore: cast_nullable_to_non_nullable
as List<NetworkExperienceServiceCandidate>,routeStatus: null == routeStatus ? _self.routeStatus : routeStatus // ignore: cast_nullable_to_non_nullable
as String,missingServicePackageNames: null == missingServicePackageNames ? _self.missingServicePackageNames : missingServicePackageNames // ignore: cast_nullable_to_non_nullable
as List<String>,missingEndpointRefs: null == missingEndpointRefs ? _self.missingEndpointRefs : missingEndpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,
  ));
}
/// Create a copy of NetworkExperienceTerritoryEntry
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodeRouteDescriptorCopyWith<$Res> get node {
  
  return $NetworkNodeRouteDescriptorCopyWith<$Res>(_self.node, (value) {
    return _then(_self.copyWith(node: value));
  });
}/// Create a copy of NetworkExperienceTerritoryEntry
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkEnvironmentDescriptorCopyWith<$Res> get environment {
  
  return $NetworkEnvironmentDescriptorCopyWith<$Res>(_self.environment, (value) {
    return _then(_self.copyWith(environment: value));
  });
}
}


/// Adds pattern-matching-related methods to [NetworkExperienceTerritoryEntry].
extension NetworkExperienceTerritoryEntryPatterns on NetworkExperienceTerritoryEntry {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkExperienceTerritoryEntry value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkExperienceTerritoryEntry() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkExperienceTerritoryEntry value)  def,}){
final _that = this;
switch (_that) {
case _NetworkExperienceTerritoryEntry():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkExperienceTerritoryEntry value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkExperienceTerritoryEntry() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String experienceName,  NetworkNodeRouteDescriptor node,  NetworkEnvironmentDescriptor environment,  List<NetworkExperienceServiceCandidate> serviceCandidates,  String routeStatus,  List<String> missingServicePackageNames,  List<String> missingEndpointRefs)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkExperienceTerritoryEntry() when def != null:
return def(_that.experienceName,_that.node,_that.environment,_that.serviceCandidates,_that.routeStatus,_that.missingServicePackageNames,_that.missingEndpointRefs);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String experienceName,  NetworkNodeRouteDescriptor node,  NetworkEnvironmentDescriptor environment,  List<NetworkExperienceServiceCandidate> serviceCandidates,  String routeStatus,  List<String> missingServicePackageNames,  List<String> missingEndpointRefs)  def,}) {final _that = this;
switch (_that) {
case _NetworkExperienceTerritoryEntry():
return def(_that.experienceName,_that.node,_that.environment,_that.serviceCandidates,_that.routeStatus,_that.missingServicePackageNames,_that.missingEndpointRefs);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String experienceName,  NetworkNodeRouteDescriptor node,  NetworkEnvironmentDescriptor environment,  List<NetworkExperienceServiceCandidate> serviceCandidates,  String routeStatus,  List<String> missingServicePackageNames,  List<String> missingEndpointRefs)?  def,}) {final _that = this;
switch (_that) {
case _NetworkExperienceTerritoryEntry() when def != null:
return def(_that.experienceName,_that.node,_that.environment,_that.serviceCandidates,_that.routeStatus,_that.missingServicePackageNames,_that.missingEndpointRefs);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkExperienceTerritoryEntry implements NetworkExperienceTerritoryEntry {
   _NetworkExperienceTerritoryEntry({required this.experienceName, required this.node, required this.environment, final  List<NetworkExperienceServiceCandidate> serviceCandidates = const [], required this.routeStatus, final  List<String> missingServicePackageNames = const [], final  List<String> missingEndpointRefs = const []}): _serviceCandidates = serviceCandidates,_missingServicePackageNames = missingServicePackageNames,_missingEndpointRefs = missingEndpointRefs;
  factory _NetworkExperienceTerritoryEntry.fromJson(Map<String, dynamic> json) => _$NetworkExperienceTerritoryEntryFromJson(json);

@override final  String experienceName;
@override final  NetworkNodeRouteDescriptor node;
@override final  NetworkEnvironmentDescriptor environment;
 final  List<NetworkExperienceServiceCandidate> _serviceCandidates;
@override@JsonKey() List<NetworkExperienceServiceCandidate> get serviceCandidates {
  if (_serviceCandidates is EqualUnmodifiableListView) return _serviceCandidates;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_serviceCandidates);
}

@override final  String routeStatus;
 final  List<String> _missingServicePackageNames;
@override@JsonKey() List<String> get missingServicePackageNames {
  if (_missingServicePackageNames is EqualUnmodifiableListView) return _missingServicePackageNames;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_missingServicePackageNames);
}

 final  List<String> _missingEndpointRefs;
@override@JsonKey() List<String> get missingEndpointRefs {
  if (_missingEndpointRefs is EqualUnmodifiableListView) return _missingEndpointRefs;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_missingEndpointRefs);
}


/// Create a copy of NetworkExperienceTerritoryEntry
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkExperienceTerritoryEntryCopyWith<_NetworkExperienceTerritoryEntry> get copyWith => __$NetworkExperienceTerritoryEntryCopyWithImpl<_NetworkExperienceTerritoryEntry>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkExperienceTerritoryEntryToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkExperienceTerritoryEntry&&(identical(other.experienceName, experienceName) || other.experienceName == experienceName)&&(identical(other.node, node) || other.node == node)&&(identical(other.environment, environment) || other.environment == environment)&&const DeepCollectionEquality().equals(other._serviceCandidates, _serviceCandidates)&&(identical(other.routeStatus, routeStatus) || other.routeStatus == routeStatus)&&const DeepCollectionEquality().equals(other._missingServicePackageNames, _missingServicePackageNames)&&const DeepCollectionEquality().equals(other._missingEndpointRefs, _missingEndpointRefs));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,experienceName,node,environment,const DeepCollectionEquality().hash(_serviceCandidates),routeStatus,const DeepCollectionEquality().hash(_missingServicePackageNames),const DeepCollectionEquality().hash(_missingEndpointRefs));

@override
String toString() {
  return 'NetworkExperienceTerritoryEntry.def(experienceName: $experienceName, node: $node, environment: $environment, serviceCandidates: $serviceCandidates, routeStatus: $routeStatus, missingServicePackageNames: $missingServicePackageNames, missingEndpointRefs: $missingEndpointRefs)';
}


}

/// @nodoc
abstract mixin class _$NetworkExperienceTerritoryEntryCopyWith<$Res> implements $NetworkExperienceTerritoryEntryCopyWith<$Res> {
  factory _$NetworkExperienceTerritoryEntryCopyWith(_NetworkExperienceTerritoryEntry value, $Res Function(_NetworkExperienceTerritoryEntry) _then) = __$NetworkExperienceTerritoryEntryCopyWithImpl;
@override @useResult
$Res call({
 String experienceName, NetworkNodeRouteDescriptor node, NetworkEnvironmentDescriptor environment, List<NetworkExperienceServiceCandidate> serviceCandidates, String routeStatus, List<String> missingServicePackageNames, List<String> missingEndpointRefs
});


@override $NetworkNodeRouteDescriptorCopyWith<$Res> get node;@override $NetworkEnvironmentDescriptorCopyWith<$Res> get environment;

}
/// @nodoc
class __$NetworkExperienceTerritoryEntryCopyWithImpl<$Res>
    implements _$NetworkExperienceTerritoryEntryCopyWith<$Res> {
  __$NetworkExperienceTerritoryEntryCopyWithImpl(this._self, this._then);

  final _NetworkExperienceTerritoryEntry _self;
  final $Res Function(_NetworkExperienceTerritoryEntry) _then;

/// Create a copy of NetworkExperienceTerritoryEntry
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? experienceName = null,Object? node = null,Object? environment = null,Object? serviceCandidates = null,Object? routeStatus = null,Object? missingServicePackageNames = null,Object? missingEndpointRefs = null,}) {
  return _then(_NetworkExperienceTerritoryEntry(
experienceName: null == experienceName ? _self.experienceName : experienceName // ignore: cast_nullable_to_non_nullable
as String,node: null == node ? _self.node : node // ignore: cast_nullable_to_non_nullable
as NetworkNodeRouteDescriptor,environment: null == environment ? _self.environment : environment // ignore: cast_nullable_to_non_nullable
as NetworkEnvironmentDescriptor,serviceCandidates: null == serviceCandidates ? _self._serviceCandidates : serviceCandidates // ignore: cast_nullable_to_non_nullable
as List<NetworkExperienceServiceCandidate>,routeStatus: null == routeStatus ? _self.routeStatus : routeStatus // ignore: cast_nullable_to_non_nullable
as String,missingServicePackageNames: null == missingServicePackageNames ? _self._missingServicePackageNames : missingServicePackageNames // ignore: cast_nullable_to_non_nullable
as List<String>,missingEndpointRefs: null == missingEndpointRefs ? _self._missingEndpointRefs : missingEndpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,
  ));
}

/// Create a copy of NetworkExperienceTerritoryEntry
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodeRouteDescriptorCopyWith<$Res> get node {
  
  return $NetworkNodeRouteDescriptorCopyWith<$Res>(_self.node, (value) {
    return _then(_self.copyWith(node: value));
  });
}/// Create a copy of NetworkExperienceTerritoryEntry
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkEnvironmentDescriptorCopyWith<$Res> get environment {
  
  return $NetworkEnvironmentDescriptorCopyWith<$Res>(_self.environment, (value) {
    return _then(_self.copyWith(environment: value));
  });
}
}


/// @nodoc
mixin _$NetworkNodePublicationNode {

@UuidValueConverter() UuidValue get nodeId; String get publicKey; String get hostname; int get port; String? get baseUrl; String get status;
/// Create a copy of NetworkNodePublicationNode
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkNodePublicationNodeCopyWith<NetworkNodePublicationNode> get copyWith => _$NetworkNodePublicationNodeCopyWithImpl<NetworkNodePublicationNode>(this as NetworkNodePublicationNode, _$identity);

  /// Serializes this NetworkNodePublicationNode to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkNodePublicationNode&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.publicKey, publicKey) || other.publicKey == publicKey)&&(identical(other.hostname, hostname) || other.hostname == hostname)&&(identical(other.port, port) || other.port == port)&&(identical(other.baseUrl, baseUrl) || other.baseUrl == baseUrl)&&(identical(other.status, status) || other.status == status));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,nodeId,publicKey,hostname,port,baseUrl,status);

@override
String toString() {
  return 'NetworkNodePublicationNode(nodeId: $nodeId, publicKey: $publicKey, hostname: $hostname, port: $port, baseUrl: $baseUrl, status: $status)';
}


}

/// @nodoc
abstract mixin class $NetworkNodePublicationNodeCopyWith<$Res>  {
  factory $NetworkNodePublicationNodeCopyWith(NetworkNodePublicationNode value, $Res Function(NetworkNodePublicationNode) _then) = _$NetworkNodePublicationNodeCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue nodeId, String publicKey, String hostname, int port, String? baseUrl, String status
});




}
/// @nodoc
class _$NetworkNodePublicationNodeCopyWithImpl<$Res>
    implements $NetworkNodePublicationNodeCopyWith<$Res> {
  _$NetworkNodePublicationNodeCopyWithImpl(this._self, this._then);

  final NetworkNodePublicationNode _self;
  final $Res Function(NetworkNodePublicationNode) _then;

/// Create a copy of NetworkNodePublicationNode
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? nodeId = null,Object? publicKey = null,Object? hostname = null,Object? port = null,Object? baseUrl = freezed,Object? status = null,}) {
  return _then(_self.copyWith(
nodeId: null == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,publicKey: null == publicKey ? _self.publicKey : publicKey // ignore: cast_nullable_to_non_nullable
as String,hostname: null == hostname ? _self.hostname : hostname // ignore: cast_nullable_to_non_nullable
as String,port: null == port ? _self.port : port // ignore: cast_nullable_to_non_nullable
as int,baseUrl: freezed == baseUrl ? _self.baseUrl : baseUrl // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkNodePublicationNode].
extension NetworkNodePublicationNodePatterns on NetworkNodePublicationNode {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkNodePublicationNode value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkNodePublicationNode() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkNodePublicationNode value)  def,}){
final _that = this;
switch (_that) {
case _NetworkNodePublicationNode():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkNodePublicationNode value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkNodePublicationNode() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue nodeId,  String publicKey,  String hostname,  int port,  String? baseUrl,  String status)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkNodePublicationNode() when def != null:
return def(_that.nodeId,_that.publicKey,_that.hostname,_that.port,_that.baseUrl,_that.status);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue nodeId,  String publicKey,  String hostname,  int port,  String? baseUrl,  String status)  def,}) {final _that = this;
switch (_that) {
case _NetworkNodePublicationNode():
return def(_that.nodeId,_that.publicKey,_that.hostname,_that.port,_that.baseUrl,_that.status);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue nodeId,  String publicKey,  String hostname,  int port,  String? baseUrl,  String status)?  def,}) {final _that = this;
switch (_that) {
case _NetworkNodePublicationNode() when def != null:
return def(_that.nodeId,_that.publicKey,_that.hostname,_that.port,_that.baseUrl,_that.status);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkNodePublicationNode implements NetworkNodePublicationNode {
   _NetworkNodePublicationNode({@UuidValueConverter() required this.nodeId, required this.publicKey, required this.hostname, required this.port, this.baseUrl, required this.status});
  factory _NetworkNodePublicationNode.fromJson(Map<String, dynamic> json) => _$NetworkNodePublicationNodeFromJson(json);

@override@UuidValueConverter() final  UuidValue nodeId;
@override final  String publicKey;
@override final  String hostname;
@override final  int port;
@override final  String? baseUrl;
@override final  String status;

/// Create a copy of NetworkNodePublicationNode
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkNodePublicationNodeCopyWith<_NetworkNodePublicationNode> get copyWith => __$NetworkNodePublicationNodeCopyWithImpl<_NetworkNodePublicationNode>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkNodePublicationNodeToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkNodePublicationNode&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.publicKey, publicKey) || other.publicKey == publicKey)&&(identical(other.hostname, hostname) || other.hostname == hostname)&&(identical(other.port, port) || other.port == port)&&(identical(other.baseUrl, baseUrl) || other.baseUrl == baseUrl)&&(identical(other.status, status) || other.status == status));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,nodeId,publicKey,hostname,port,baseUrl,status);

@override
String toString() {
  return 'NetworkNodePublicationNode.def(nodeId: $nodeId, publicKey: $publicKey, hostname: $hostname, port: $port, baseUrl: $baseUrl, status: $status)';
}


}

/// @nodoc
abstract mixin class _$NetworkNodePublicationNodeCopyWith<$Res> implements $NetworkNodePublicationNodeCopyWith<$Res> {
  factory _$NetworkNodePublicationNodeCopyWith(_NetworkNodePublicationNode value, $Res Function(_NetworkNodePublicationNode) _then) = __$NetworkNodePublicationNodeCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue nodeId, String publicKey, String hostname, int port, String? baseUrl, String status
});




}
/// @nodoc
class __$NetworkNodePublicationNodeCopyWithImpl<$Res>
    implements _$NetworkNodePublicationNodeCopyWith<$Res> {
  __$NetworkNodePublicationNodeCopyWithImpl(this._self, this._then);

  final _NetworkNodePublicationNode _self;
  final $Res Function(_NetworkNodePublicationNode) _then;

/// Create a copy of NetworkNodePublicationNode
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? nodeId = null,Object? publicKey = null,Object? hostname = null,Object? port = null,Object? baseUrl = freezed,Object? status = null,}) {
  return _then(_NetworkNodePublicationNode(
nodeId: null == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,publicKey: null == publicKey ? _self.publicKey : publicKey // ignore: cast_nullable_to_non_nullable
as String,hostname: null == hostname ? _self.hostname : hostname // ignore: cast_nullable_to_non_nullable
as String,port: null == port ? _self.port : port // ignore: cast_nullable_to_non_nullable
as int,baseUrl: freezed == baseUrl ? _self.baseUrl : baseUrl // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}


/// @nodoc
mixin _$NetworkNodePublicationEnvironment {

@UuidValueConverter() UuidValue get environmentId; String? get environmentKey; String? get environmentTitle; String get role; bool get isActive; int get priority; String get status; List<String> get experienceNames;@UuidValueConverter() UuidValue? get environmentConfigId; String? get environmentConfigKey;
/// Create a copy of NetworkNodePublicationEnvironment
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkNodePublicationEnvironmentCopyWith<NetworkNodePublicationEnvironment> get copyWith => _$NetworkNodePublicationEnvironmentCopyWithImpl<NetworkNodePublicationEnvironment>(this as NetworkNodePublicationEnvironment, _$identity);

  /// Serializes this NetworkNodePublicationEnvironment to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkNodePublicationEnvironment&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentKey, environmentKey) || other.environmentKey == environmentKey)&&(identical(other.environmentTitle, environmentTitle) || other.environmentTitle == environmentTitle)&&(identical(other.role, role) || other.role == role)&&(identical(other.isActive, isActive) || other.isActive == isActive)&&(identical(other.priority, priority) || other.priority == priority)&&(identical(other.status, status) || other.status == status)&&const DeepCollectionEquality().equals(other.experienceNames, experienceNames)&&(identical(other.environmentConfigId, environmentConfigId) || other.environmentConfigId == environmentConfigId)&&(identical(other.environmentConfigKey, environmentConfigKey) || other.environmentConfigKey == environmentConfigKey));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,environmentId,environmentKey,environmentTitle,role,isActive,priority,status,const DeepCollectionEquality().hash(experienceNames),environmentConfigId,environmentConfigKey);

@override
String toString() {
  return 'NetworkNodePublicationEnvironment(environmentId: $environmentId, environmentKey: $environmentKey, environmentTitle: $environmentTitle, role: $role, isActive: $isActive, priority: $priority, status: $status, experienceNames: $experienceNames, environmentConfigId: $environmentConfigId, environmentConfigKey: $environmentConfigKey)';
}


}

/// @nodoc
abstract mixin class $NetworkNodePublicationEnvironmentCopyWith<$Res>  {
  factory $NetworkNodePublicationEnvironmentCopyWith(NetworkNodePublicationEnvironment value, $Res Function(NetworkNodePublicationEnvironment) _then) = _$NetworkNodePublicationEnvironmentCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue environmentId, String? environmentKey, String? environmentTitle, String role, bool isActive, int priority, String status, List<String> experienceNames,@UuidValueConverter() UuidValue? environmentConfigId, String? environmentConfigKey
});




}
/// @nodoc
class _$NetworkNodePublicationEnvironmentCopyWithImpl<$Res>
    implements $NetworkNodePublicationEnvironmentCopyWith<$Res> {
  _$NetworkNodePublicationEnvironmentCopyWithImpl(this._self, this._then);

  final NetworkNodePublicationEnvironment _self;
  final $Res Function(NetworkNodePublicationEnvironment) _then;

/// Create a copy of NetworkNodePublicationEnvironment
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? environmentId = null,Object? environmentKey = freezed,Object? environmentTitle = freezed,Object? role = null,Object? isActive = null,Object? priority = null,Object? status = null,Object? experienceNames = null,Object? environmentConfigId = freezed,Object? environmentConfigKey = freezed,}) {
  return _then(_self.copyWith(
environmentId: null == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentKey: freezed == environmentKey ? _self.environmentKey : environmentKey // ignore: cast_nullable_to_non_nullable
as String?,environmentTitle: freezed == environmentTitle ? _self.environmentTitle : environmentTitle // ignore: cast_nullable_to_non_nullable
as String?,role: null == role ? _self.role : role // ignore: cast_nullable_to_non_nullable
as String,isActive: null == isActive ? _self.isActive : isActive // ignore: cast_nullable_to_non_nullable
as bool,priority: null == priority ? _self.priority : priority // ignore: cast_nullable_to_non_nullable
as int,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,experienceNames: null == experienceNames ? _self.experienceNames : experienceNames // ignore: cast_nullable_to_non_nullable
as List<String>,environmentConfigId: freezed == environmentConfigId ? _self.environmentConfigId : environmentConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentConfigKey: freezed == environmentConfigKey ? _self.environmentConfigKey : environmentConfigKey // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkNodePublicationEnvironment].
extension NetworkNodePublicationEnvironmentPatterns on NetworkNodePublicationEnvironment {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkNodePublicationEnvironment value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkNodePublicationEnvironment() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkNodePublicationEnvironment value)  def,}){
final _that = this;
switch (_that) {
case _NetworkNodePublicationEnvironment():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkNodePublicationEnvironment value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkNodePublicationEnvironment() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue environmentId,  String? environmentKey,  String? environmentTitle,  String role,  bool isActive,  int priority,  String status,  List<String> experienceNames, @UuidValueConverter()  UuidValue? environmentConfigId,  String? environmentConfigKey)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkNodePublicationEnvironment() when def != null:
return def(_that.environmentId,_that.environmentKey,_that.environmentTitle,_that.role,_that.isActive,_that.priority,_that.status,_that.experienceNames,_that.environmentConfigId,_that.environmentConfigKey);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue environmentId,  String? environmentKey,  String? environmentTitle,  String role,  bool isActive,  int priority,  String status,  List<String> experienceNames, @UuidValueConverter()  UuidValue? environmentConfigId,  String? environmentConfigKey)  def,}) {final _that = this;
switch (_that) {
case _NetworkNodePublicationEnvironment():
return def(_that.environmentId,_that.environmentKey,_that.environmentTitle,_that.role,_that.isActive,_that.priority,_that.status,_that.experienceNames,_that.environmentConfigId,_that.environmentConfigKey);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue environmentId,  String? environmentKey,  String? environmentTitle,  String role,  bool isActive,  int priority,  String status,  List<String> experienceNames, @UuidValueConverter()  UuidValue? environmentConfigId,  String? environmentConfigKey)?  def,}) {final _that = this;
switch (_that) {
case _NetworkNodePublicationEnvironment() when def != null:
return def(_that.environmentId,_that.environmentKey,_that.environmentTitle,_that.role,_that.isActive,_that.priority,_that.status,_that.experienceNames,_that.environmentConfigId,_that.environmentConfigKey);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkNodePublicationEnvironment implements NetworkNodePublicationEnvironment {
   _NetworkNodePublicationEnvironment({@UuidValueConverter() required this.environmentId, this.environmentKey, this.environmentTitle, required this.role, required this.isActive, required this.priority, required this.status, final  List<String> experienceNames = const [], @UuidValueConverter() this.environmentConfigId, this.environmentConfigKey}): _experienceNames = experienceNames;
  factory _NetworkNodePublicationEnvironment.fromJson(Map<String, dynamic> json) => _$NetworkNodePublicationEnvironmentFromJson(json);

@override@UuidValueConverter() final  UuidValue environmentId;
@override final  String? environmentKey;
@override final  String? environmentTitle;
@override final  String role;
@override final  bool isActive;
@override final  int priority;
@override final  String status;
 final  List<String> _experienceNames;
@override@JsonKey() List<String> get experienceNames {
  if (_experienceNames is EqualUnmodifiableListView) return _experienceNames;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_experienceNames);
}

@override@UuidValueConverter() final  UuidValue? environmentConfigId;
@override final  String? environmentConfigKey;

/// Create a copy of NetworkNodePublicationEnvironment
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkNodePublicationEnvironmentCopyWith<_NetworkNodePublicationEnvironment> get copyWith => __$NetworkNodePublicationEnvironmentCopyWithImpl<_NetworkNodePublicationEnvironment>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkNodePublicationEnvironmentToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkNodePublicationEnvironment&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentKey, environmentKey) || other.environmentKey == environmentKey)&&(identical(other.environmentTitle, environmentTitle) || other.environmentTitle == environmentTitle)&&(identical(other.role, role) || other.role == role)&&(identical(other.isActive, isActive) || other.isActive == isActive)&&(identical(other.priority, priority) || other.priority == priority)&&(identical(other.status, status) || other.status == status)&&const DeepCollectionEquality().equals(other._experienceNames, _experienceNames)&&(identical(other.environmentConfigId, environmentConfigId) || other.environmentConfigId == environmentConfigId)&&(identical(other.environmentConfigKey, environmentConfigKey) || other.environmentConfigKey == environmentConfigKey));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,environmentId,environmentKey,environmentTitle,role,isActive,priority,status,const DeepCollectionEquality().hash(_experienceNames),environmentConfigId,environmentConfigKey);

@override
String toString() {
  return 'NetworkNodePublicationEnvironment.def(environmentId: $environmentId, environmentKey: $environmentKey, environmentTitle: $environmentTitle, role: $role, isActive: $isActive, priority: $priority, status: $status, experienceNames: $experienceNames, environmentConfigId: $environmentConfigId, environmentConfigKey: $environmentConfigKey)';
}


}

/// @nodoc
abstract mixin class _$NetworkNodePublicationEnvironmentCopyWith<$Res> implements $NetworkNodePublicationEnvironmentCopyWith<$Res> {
  factory _$NetworkNodePublicationEnvironmentCopyWith(_NetworkNodePublicationEnvironment value, $Res Function(_NetworkNodePublicationEnvironment) _then) = __$NetworkNodePublicationEnvironmentCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue environmentId, String? environmentKey, String? environmentTitle, String role, bool isActive, int priority, String status, List<String> experienceNames,@UuidValueConverter() UuidValue? environmentConfigId, String? environmentConfigKey
});




}
/// @nodoc
class __$NetworkNodePublicationEnvironmentCopyWithImpl<$Res>
    implements _$NetworkNodePublicationEnvironmentCopyWith<$Res> {
  __$NetworkNodePublicationEnvironmentCopyWithImpl(this._self, this._then);

  final _NetworkNodePublicationEnvironment _self;
  final $Res Function(_NetworkNodePublicationEnvironment) _then;

/// Create a copy of NetworkNodePublicationEnvironment
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? environmentId = null,Object? environmentKey = freezed,Object? environmentTitle = freezed,Object? role = null,Object? isActive = null,Object? priority = null,Object? status = null,Object? experienceNames = null,Object? environmentConfigId = freezed,Object? environmentConfigKey = freezed,}) {
  return _then(_NetworkNodePublicationEnvironment(
environmentId: null == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentKey: freezed == environmentKey ? _self.environmentKey : environmentKey // ignore: cast_nullable_to_non_nullable
as String?,environmentTitle: freezed == environmentTitle ? _self.environmentTitle : environmentTitle // ignore: cast_nullable_to_non_nullable
as String?,role: null == role ? _self.role : role // ignore: cast_nullable_to_non_nullable
as String,isActive: null == isActive ? _self.isActive : isActive // ignore: cast_nullable_to_non_nullable
as bool,priority: null == priority ? _self.priority : priority // ignore: cast_nullable_to_non_nullable
as int,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,experienceNames: null == experienceNames ? _self._experienceNames : experienceNames // ignore: cast_nullable_to_non_nullable
as List<String>,environmentConfigId: freezed == environmentConfigId ? _self.environmentConfigId : environmentConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentConfigKey: freezed == environmentConfigKey ? _self.environmentConfigKey : environmentConfigKey // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$NetworkNodePublicationHostedService {

@UuidValueConverter() UuidValue get servicePackageId;@UuidValueConverter() UuidValue get serviceId; String get serviceName; List<String> get servicePackageNames; List<String> get endpointRefs; List<String> get streamEndpointRefs; String get hostId; String? get hostVersion; String get protocolVersion; bool get supportsStreamEvents;
/// Create a copy of NetworkNodePublicationHostedService
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkNodePublicationHostedServiceCopyWith<NetworkNodePublicationHostedService> get copyWith => _$NetworkNodePublicationHostedServiceCopyWithImpl<NetworkNodePublicationHostedService>(this as NetworkNodePublicationHostedService, _$identity);

  /// Serializes this NetworkNodePublicationHostedService to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkNodePublicationHostedService&&(identical(other.servicePackageId, servicePackageId) || other.servicePackageId == servicePackageId)&&(identical(other.serviceId, serviceId) || other.serviceId == serviceId)&&(identical(other.serviceName, serviceName) || other.serviceName == serviceName)&&const DeepCollectionEquality().equals(other.servicePackageNames, servicePackageNames)&&const DeepCollectionEquality().equals(other.endpointRefs, endpointRefs)&&const DeepCollectionEquality().equals(other.streamEndpointRefs, streamEndpointRefs)&&(identical(other.hostId, hostId) || other.hostId == hostId)&&(identical(other.hostVersion, hostVersion) || other.hostVersion == hostVersion)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.supportsStreamEvents, supportsStreamEvents) || other.supportsStreamEvents == supportsStreamEvents));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,servicePackageId,serviceId,serviceName,const DeepCollectionEquality().hash(servicePackageNames),const DeepCollectionEquality().hash(endpointRefs),const DeepCollectionEquality().hash(streamEndpointRefs),hostId,hostVersion,protocolVersion,supportsStreamEvents);

@override
String toString() {
  return 'NetworkNodePublicationHostedService(servicePackageId: $servicePackageId, serviceId: $serviceId, serviceName: $serviceName, servicePackageNames: $servicePackageNames, endpointRefs: $endpointRefs, streamEndpointRefs: $streamEndpointRefs, hostId: $hostId, hostVersion: $hostVersion, protocolVersion: $protocolVersion, supportsStreamEvents: $supportsStreamEvents)';
}


}

/// @nodoc
abstract mixin class $NetworkNodePublicationHostedServiceCopyWith<$Res>  {
  factory $NetworkNodePublicationHostedServiceCopyWith(NetworkNodePublicationHostedService value, $Res Function(NetworkNodePublicationHostedService) _then) = _$NetworkNodePublicationHostedServiceCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue servicePackageId,@UuidValueConverter() UuidValue serviceId, String serviceName, List<String> servicePackageNames, List<String> endpointRefs, List<String> streamEndpointRefs, String hostId, String? hostVersion, String protocolVersion, bool supportsStreamEvents
});




}
/// @nodoc
class _$NetworkNodePublicationHostedServiceCopyWithImpl<$Res>
    implements $NetworkNodePublicationHostedServiceCopyWith<$Res> {
  _$NetworkNodePublicationHostedServiceCopyWithImpl(this._self, this._then);

  final NetworkNodePublicationHostedService _self;
  final $Res Function(NetworkNodePublicationHostedService) _then;

/// Create a copy of NetworkNodePublicationHostedService
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? servicePackageId = null,Object? serviceId = null,Object? serviceName = null,Object? servicePackageNames = null,Object? endpointRefs = null,Object? streamEndpointRefs = null,Object? hostId = null,Object? hostVersion = freezed,Object? protocolVersion = null,Object? supportsStreamEvents = null,}) {
  return _then(_self.copyWith(
servicePackageId: null == servicePackageId ? _self.servicePackageId : servicePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,serviceId: null == serviceId ? _self.serviceId : serviceId // ignore: cast_nullable_to_non_nullable
as UuidValue,serviceName: null == serviceName ? _self.serviceName : serviceName // ignore: cast_nullable_to_non_nullable
as String,servicePackageNames: null == servicePackageNames ? _self.servicePackageNames : servicePackageNames // ignore: cast_nullable_to_non_nullable
as List<String>,endpointRefs: null == endpointRefs ? _self.endpointRefs : endpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,streamEndpointRefs: null == streamEndpointRefs ? _self.streamEndpointRefs : streamEndpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,hostId: null == hostId ? _self.hostId : hostId // ignore: cast_nullable_to_non_nullable
as String,hostVersion: freezed == hostVersion ? _self.hostVersion : hostVersion // ignore: cast_nullable_to_non_nullable
as String?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as String,supportsStreamEvents: null == supportsStreamEvents ? _self.supportsStreamEvents : supportsStreamEvents // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkNodePublicationHostedService].
extension NetworkNodePublicationHostedServicePatterns on NetworkNodePublicationHostedService {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkNodePublicationHostedService value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkNodePublicationHostedService() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkNodePublicationHostedService value)  def,}){
final _that = this;
switch (_that) {
case _NetworkNodePublicationHostedService():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkNodePublicationHostedService value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkNodePublicationHostedService() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue servicePackageId, @UuidValueConverter()  UuidValue serviceId,  String serviceName,  List<String> servicePackageNames,  List<String> endpointRefs,  List<String> streamEndpointRefs,  String hostId,  String? hostVersion,  String protocolVersion,  bool supportsStreamEvents)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkNodePublicationHostedService() when def != null:
return def(_that.servicePackageId,_that.serviceId,_that.serviceName,_that.servicePackageNames,_that.endpointRefs,_that.streamEndpointRefs,_that.hostId,_that.hostVersion,_that.protocolVersion,_that.supportsStreamEvents);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue servicePackageId, @UuidValueConverter()  UuidValue serviceId,  String serviceName,  List<String> servicePackageNames,  List<String> endpointRefs,  List<String> streamEndpointRefs,  String hostId,  String? hostVersion,  String protocolVersion,  bool supportsStreamEvents)  def,}) {final _that = this;
switch (_that) {
case _NetworkNodePublicationHostedService():
return def(_that.servicePackageId,_that.serviceId,_that.serviceName,_that.servicePackageNames,_that.endpointRefs,_that.streamEndpointRefs,_that.hostId,_that.hostVersion,_that.protocolVersion,_that.supportsStreamEvents);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue servicePackageId, @UuidValueConverter()  UuidValue serviceId,  String serviceName,  List<String> servicePackageNames,  List<String> endpointRefs,  List<String> streamEndpointRefs,  String hostId,  String? hostVersion,  String protocolVersion,  bool supportsStreamEvents)?  def,}) {final _that = this;
switch (_that) {
case _NetworkNodePublicationHostedService() when def != null:
return def(_that.servicePackageId,_that.serviceId,_that.serviceName,_that.servicePackageNames,_that.endpointRefs,_that.streamEndpointRefs,_that.hostId,_that.hostVersion,_that.protocolVersion,_that.supportsStreamEvents);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkNodePublicationHostedService implements NetworkNodePublicationHostedService {
   _NetworkNodePublicationHostedService({@UuidValueConverter() required this.servicePackageId, @UuidValueConverter() required this.serviceId, required this.serviceName, final  List<String> servicePackageNames = const [], final  List<String> endpointRefs = const [], final  List<String> streamEndpointRefs = const [], required this.hostId, this.hostVersion, required this.protocolVersion, required this.supportsStreamEvents}): _servicePackageNames = servicePackageNames,_endpointRefs = endpointRefs,_streamEndpointRefs = streamEndpointRefs;
  factory _NetworkNodePublicationHostedService.fromJson(Map<String, dynamic> json) => _$NetworkNodePublicationHostedServiceFromJson(json);

@override@UuidValueConverter() final  UuidValue servicePackageId;
@override@UuidValueConverter() final  UuidValue serviceId;
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

 final  List<String> _streamEndpointRefs;
@override@JsonKey() List<String> get streamEndpointRefs {
  if (_streamEndpointRefs is EqualUnmodifiableListView) return _streamEndpointRefs;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_streamEndpointRefs);
}

@override final  String hostId;
@override final  String? hostVersion;
@override final  String protocolVersion;
@override final  bool supportsStreamEvents;

/// Create a copy of NetworkNodePublicationHostedService
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkNodePublicationHostedServiceCopyWith<_NetworkNodePublicationHostedService> get copyWith => __$NetworkNodePublicationHostedServiceCopyWithImpl<_NetworkNodePublicationHostedService>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkNodePublicationHostedServiceToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkNodePublicationHostedService&&(identical(other.servicePackageId, servicePackageId) || other.servicePackageId == servicePackageId)&&(identical(other.serviceId, serviceId) || other.serviceId == serviceId)&&(identical(other.serviceName, serviceName) || other.serviceName == serviceName)&&const DeepCollectionEquality().equals(other._servicePackageNames, _servicePackageNames)&&const DeepCollectionEquality().equals(other._endpointRefs, _endpointRefs)&&const DeepCollectionEquality().equals(other._streamEndpointRefs, _streamEndpointRefs)&&(identical(other.hostId, hostId) || other.hostId == hostId)&&(identical(other.hostVersion, hostVersion) || other.hostVersion == hostVersion)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.supportsStreamEvents, supportsStreamEvents) || other.supportsStreamEvents == supportsStreamEvents));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,servicePackageId,serviceId,serviceName,const DeepCollectionEquality().hash(_servicePackageNames),const DeepCollectionEquality().hash(_endpointRefs),const DeepCollectionEquality().hash(_streamEndpointRefs),hostId,hostVersion,protocolVersion,supportsStreamEvents);

@override
String toString() {
  return 'NetworkNodePublicationHostedService.def(servicePackageId: $servicePackageId, serviceId: $serviceId, serviceName: $serviceName, servicePackageNames: $servicePackageNames, endpointRefs: $endpointRefs, streamEndpointRefs: $streamEndpointRefs, hostId: $hostId, hostVersion: $hostVersion, protocolVersion: $protocolVersion, supportsStreamEvents: $supportsStreamEvents)';
}


}

/// @nodoc
abstract mixin class _$NetworkNodePublicationHostedServiceCopyWith<$Res> implements $NetworkNodePublicationHostedServiceCopyWith<$Res> {
  factory _$NetworkNodePublicationHostedServiceCopyWith(_NetworkNodePublicationHostedService value, $Res Function(_NetworkNodePublicationHostedService) _then) = __$NetworkNodePublicationHostedServiceCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue servicePackageId,@UuidValueConverter() UuidValue serviceId, String serviceName, List<String> servicePackageNames, List<String> endpointRefs, List<String> streamEndpointRefs, String hostId, String? hostVersion, String protocolVersion, bool supportsStreamEvents
});




}
/// @nodoc
class __$NetworkNodePublicationHostedServiceCopyWithImpl<$Res>
    implements _$NetworkNodePublicationHostedServiceCopyWith<$Res> {
  __$NetworkNodePublicationHostedServiceCopyWithImpl(this._self, this._then);

  final _NetworkNodePublicationHostedService _self;
  final $Res Function(_NetworkNodePublicationHostedService) _then;

/// Create a copy of NetworkNodePublicationHostedService
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? servicePackageId = null,Object? serviceId = null,Object? serviceName = null,Object? servicePackageNames = null,Object? endpointRefs = null,Object? streamEndpointRefs = null,Object? hostId = null,Object? hostVersion = freezed,Object? protocolVersion = null,Object? supportsStreamEvents = null,}) {
  return _then(_NetworkNodePublicationHostedService(
servicePackageId: null == servicePackageId ? _self.servicePackageId : servicePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,serviceId: null == serviceId ? _self.serviceId : serviceId // ignore: cast_nullable_to_non_nullable
as UuidValue,serviceName: null == serviceName ? _self.serviceName : serviceName // ignore: cast_nullable_to_non_nullable
as String,servicePackageNames: null == servicePackageNames ? _self._servicePackageNames : servicePackageNames // ignore: cast_nullable_to_non_nullable
as List<String>,endpointRefs: null == endpointRefs ? _self._endpointRefs : endpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,streamEndpointRefs: null == streamEndpointRefs ? _self._streamEndpointRefs : streamEndpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,hostId: null == hostId ? _self.hostId : hostId // ignore: cast_nullable_to_non_nullable
as String,hostVersion: freezed == hostVersion ? _self.hostVersion : hostVersion // ignore: cast_nullable_to_non_nullable
as String?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as String,supportsStreamEvents: null == supportsStreamEvents ? _self.supportsStreamEvents : supportsStreamEvents // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}


}


/// @nodoc
mixin _$NetworkNodePublicationIntent {

 String get publicationDigest; NetworkNodePublicationNode get node; NetworkNodePublicationEnvironment get environment; List<NetworkNodePublicationHostedService> get hostedServices;@UuidValueConverter() UuidValue? get sourceWorkspaceRevisionId;@UuidValueConverter() UuidValue? get sourceNodeConfigId;
/// Create a copy of NetworkNodePublicationIntent
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkNodePublicationIntentCopyWith<NetworkNodePublicationIntent> get copyWith => _$NetworkNodePublicationIntentCopyWithImpl<NetworkNodePublicationIntent>(this as NetworkNodePublicationIntent, _$identity);

  /// Serializes this NetworkNodePublicationIntent to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkNodePublicationIntent&&(identical(other.publicationDigest, publicationDigest) || other.publicationDigest == publicationDigest)&&(identical(other.node, node) || other.node == node)&&(identical(other.environment, environment) || other.environment == environment)&&const DeepCollectionEquality().equals(other.hostedServices, hostedServices)&&(identical(other.sourceWorkspaceRevisionId, sourceWorkspaceRevisionId) || other.sourceWorkspaceRevisionId == sourceWorkspaceRevisionId)&&(identical(other.sourceNodeConfigId, sourceNodeConfigId) || other.sourceNodeConfigId == sourceNodeConfigId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,publicationDigest,node,environment,const DeepCollectionEquality().hash(hostedServices),sourceWorkspaceRevisionId,sourceNodeConfigId);

@override
String toString() {
  return 'NetworkNodePublicationIntent(publicationDigest: $publicationDigest, node: $node, environment: $environment, hostedServices: $hostedServices, sourceWorkspaceRevisionId: $sourceWorkspaceRevisionId, sourceNodeConfigId: $sourceNodeConfigId)';
}


}

/// @nodoc
abstract mixin class $NetworkNodePublicationIntentCopyWith<$Res>  {
  factory $NetworkNodePublicationIntentCopyWith(NetworkNodePublicationIntent value, $Res Function(NetworkNodePublicationIntent) _then) = _$NetworkNodePublicationIntentCopyWithImpl;
@useResult
$Res call({
 String publicationDigest, NetworkNodePublicationNode node, NetworkNodePublicationEnvironment environment, List<NetworkNodePublicationHostedService> hostedServices,@UuidValueConverter() UuidValue? sourceWorkspaceRevisionId,@UuidValueConverter() UuidValue? sourceNodeConfigId
});


$NetworkNodePublicationNodeCopyWith<$Res> get node;$NetworkNodePublicationEnvironmentCopyWith<$Res> get environment;

}
/// @nodoc
class _$NetworkNodePublicationIntentCopyWithImpl<$Res>
    implements $NetworkNodePublicationIntentCopyWith<$Res> {
  _$NetworkNodePublicationIntentCopyWithImpl(this._self, this._then);

  final NetworkNodePublicationIntent _self;
  final $Res Function(NetworkNodePublicationIntent) _then;

/// Create a copy of NetworkNodePublicationIntent
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? publicationDigest = null,Object? node = null,Object? environment = null,Object? hostedServices = null,Object? sourceWorkspaceRevisionId = freezed,Object? sourceNodeConfigId = freezed,}) {
  return _then(_self.copyWith(
publicationDigest: null == publicationDigest ? _self.publicationDigest : publicationDigest // ignore: cast_nullable_to_non_nullable
as String,node: null == node ? _self.node : node // ignore: cast_nullable_to_non_nullable
as NetworkNodePublicationNode,environment: null == environment ? _self.environment : environment // ignore: cast_nullable_to_non_nullable
as NetworkNodePublicationEnvironment,hostedServices: null == hostedServices ? _self.hostedServices : hostedServices // ignore: cast_nullable_to_non_nullable
as List<NetworkNodePublicationHostedService>,sourceWorkspaceRevisionId: freezed == sourceWorkspaceRevisionId ? _self.sourceWorkspaceRevisionId : sourceWorkspaceRevisionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sourceNodeConfigId: freezed == sourceNodeConfigId ? _self.sourceNodeConfigId : sourceNodeConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}
/// Create a copy of NetworkNodePublicationIntent
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodePublicationNodeCopyWith<$Res> get node {
  
  return $NetworkNodePublicationNodeCopyWith<$Res>(_self.node, (value) {
    return _then(_self.copyWith(node: value));
  });
}/// Create a copy of NetworkNodePublicationIntent
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodePublicationEnvironmentCopyWith<$Res> get environment {
  
  return $NetworkNodePublicationEnvironmentCopyWith<$Res>(_self.environment, (value) {
    return _then(_self.copyWith(environment: value));
  });
}
}


/// Adds pattern-matching-related methods to [NetworkNodePublicationIntent].
extension NetworkNodePublicationIntentPatterns on NetworkNodePublicationIntent {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkNodePublicationIntent value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkNodePublicationIntent() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkNodePublicationIntent value)  def,}){
final _that = this;
switch (_that) {
case _NetworkNodePublicationIntent():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkNodePublicationIntent value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkNodePublicationIntent() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String publicationDigest,  NetworkNodePublicationNode node,  NetworkNodePublicationEnvironment environment,  List<NetworkNodePublicationHostedService> hostedServices, @UuidValueConverter()  UuidValue? sourceWorkspaceRevisionId, @UuidValueConverter()  UuidValue? sourceNodeConfigId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkNodePublicationIntent() when def != null:
return def(_that.publicationDigest,_that.node,_that.environment,_that.hostedServices,_that.sourceWorkspaceRevisionId,_that.sourceNodeConfigId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String publicationDigest,  NetworkNodePublicationNode node,  NetworkNodePublicationEnvironment environment,  List<NetworkNodePublicationHostedService> hostedServices, @UuidValueConverter()  UuidValue? sourceWorkspaceRevisionId, @UuidValueConverter()  UuidValue? sourceNodeConfigId)  def,}) {final _that = this;
switch (_that) {
case _NetworkNodePublicationIntent():
return def(_that.publicationDigest,_that.node,_that.environment,_that.hostedServices,_that.sourceWorkspaceRevisionId,_that.sourceNodeConfigId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String publicationDigest,  NetworkNodePublicationNode node,  NetworkNodePublicationEnvironment environment,  List<NetworkNodePublicationHostedService> hostedServices, @UuidValueConverter()  UuidValue? sourceWorkspaceRevisionId, @UuidValueConverter()  UuidValue? sourceNodeConfigId)?  def,}) {final _that = this;
switch (_that) {
case _NetworkNodePublicationIntent() when def != null:
return def(_that.publicationDigest,_that.node,_that.environment,_that.hostedServices,_that.sourceWorkspaceRevisionId,_that.sourceNodeConfigId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkNodePublicationIntent implements NetworkNodePublicationIntent {
   _NetworkNodePublicationIntent({required this.publicationDigest, required this.node, required this.environment, final  List<NetworkNodePublicationHostedService> hostedServices = const [], @UuidValueConverter() this.sourceWorkspaceRevisionId, @UuidValueConverter() this.sourceNodeConfigId}): _hostedServices = hostedServices;
  factory _NetworkNodePublicationIntent.fromJson(Map<String, dynamic> json) => _$NetworkNodePublicationIntentFromJson(json);

@override final  String publicationDigest;
@override final  NetworkNodePublicationNode node;
@override final  NetworkNodePublicationEnvironment environment;
 final  List<NetworkNodePublicationHostedService> _hostedServices;
@override@JsonKey() List<NetworkNodePublicationHostedService> get hostedServices {
  if (_hostedServices is EqualUnmodifiableListView) return _hostedServices;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_hostedServices);
}

@override@UuidValueConverter() final  UuidValue? sourceWorkspaceRevisionId;
@override@UuidValueConverter() final  UuidValue? sourceNodeConfigId;

/// Create a copy of NetworkNodePublicationIntent
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkNodePublicationIntentCopyWith<_NetworkNodePublicationIntent> get copyWith => __$NetworkNodePublicationIntentCopyWithImpl<_NetworkNodePublicationIntent>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkNodePublicationIntentToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkNodePublicationIntent&&(identical(other.publicationDigest, publicationDigest) || other.publicationDigest == publicationDigest)&&(identical(other.node, node) || other.node == node)&&(identical(other.environment, environment) || other.environment == environment)&&const DeepCollectionEquality().equals(other._hostedServices, _hostedServices)&&(identical(other.sourceWorkspaceRevisionId, sourceWorkspaceRevisionId) || other.sourceWorkspaceRevisionId == sourceWorkspaceRevisionId)&&(identical(other.sourceNodeConfigId, sourceNodeConfigId) || other.sourceNodeConfigId == sourceNodeConfigId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,publicationDigest,node,environment,const DeepCollectionEquality().hash(_hostedServices),sourceWorkspaceRevisionId,sourceNodeConfigId);

@override
String toString() {
  return 'NetworkNodePublicationIntent.def(publicationDigest: $publicationDigest, node: $node, environment: $environment, hostedServices: $hostedServices, sourceWorkspaceRevisionId: $sourceWorkspaceRevisionId, sourceNodeConfigId: $sourceNodeConfigId)';
}


}

/// @nodoc
abstract mixin class _$NetworkNodePublicationIntentCopyWith<$Res> implements $NetworkNodePublicationIntentCopyWith<$Res> {
  factory _$NetworkNodePublicationIntentCopyWith(_NetworkNodePublicationIntent value, $Res Function(_NetworkNodePublicationIntent) _then) = __$NetworkNodePublicationIntentCopyWithImpl;
@override @useResult
$Res call({
 String publicationDigest, NetworkNodePublicationNode node, NetworkNodePublicationEnvironment environment, List<NetworkNodePublicationHostedService> hostedServices,@UuidValueConverter() UuidValue? sourceWorkspaceRevisionId,@UuidValueConverter() UuidValue? sourceNodeConfigId
});


@override $NetworkNodePublicationNodeCopyWith<$Res> get node;@override $NetworkNodePublicationEnvironmentCopyWith<$Res> get environment;

}
/// @nodoc
class __$NetworkNodePublicationIntentCopyWithImpl<$Res>
    implements _$NetworkNodePublicationIntentCopyWith<$Res> {
  __$NetworkNodePublicationIntentCopyWithImpl(this._self, this._then);

  final _NetworkNodePublicationIntent _self;
  final $Res Function(_NetworkNodePublicationIntent) _then;

/// Create a copy of NetworkNodePublicationIntent
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? publicationDigest = null,Object? node = null,Object? environment = null,Object? hostedServices = null,Object? sourceWorkspaceRevisionId = freezed,Object? sourceNodeConfigId = freezed,}) {
  return _then(_NetworkNodePublicationIntent(
publicationDigest: null == publicationDigest ? _self.publicationDigest : publicationDigest // ignore: cast_nullable_to_non_nullable
as String,node: null == node ? _self.node : node // ignore: cast_nullable_to_non_nullable
as NetworkNodePublicationNode,environment: null == environment ? _self.environment : environment // ignore: cast_nullable_to_non_nullable
as NetworkNodePublicationEnvironment,hostedServices: null == hostedServices ? _self._hostedServices : hostedServices // ignore: cast_nullable_to_non_nullable
as List<NetworkNodePublicationHostedService>,sourceWorkspaceRevisionId: freezed == sourceWorkspaceRevisionId ? _self.sourceWorkspaceRevisionId : sourceWorkspaceRevisionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sourceNodeConfigId: freezed == sourceNodeConfigId ? _self.sourceNodeConfigId : sourceNodeConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

/// Create a copy of NetworkNodePublicationIntent
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodePublicationNodeCopyWith<$Res> get node {
  
  return $NetworkNodePublicationNodeCopyWith<$Res>(_self.node, (value) {
    return _then(_self.copyWith(node: value));
  });
}/// Create a copy of NetworkNodePublicationIntent
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodePublicationEnvironmentCopyWith<$Res> get environment {
  
  return $NetworkNodePublicationEnvironmentCopyWith<$Res>(_self.environment, (value) {
    return _then(_self.copyWith(environment: value));
  });
}
}


/// @nodoc
mixin _$NetworkNodePublicationCommitReceipt {

 String get operation;@UuidValueConverter() UuidValue? get domainCommitId;@UuidValueConverter() UuidValue? get objectInstanceGraphCommitId;@UuidValueConverter() UuidValue? get rootObjectId;
/// Create a copy of NetworkNodePublicationCommitReceipt
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkNodePublicationCommitReceiptCopyWith<NetworkNodePublicationCommitReceipt> get copyWith => _$NetworkNodePublicationCommitReceiptCopyWithImpl<NetworkNodePublicationCommitReceipt>(this as NetworkNodePublicationCommitReceipt, _$identity);

  /// Serializes this NetworkNodePublicationCommitReceipt to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkNodePublicationCommitReceipt&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.domainCommitId, domainCommitId) || other.domainCommitId == domainCommitId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.rootObjectId, rootObjectId) || other.rootObjectId == rootObjectId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,domainCommitId,objectInstanceGraphCommitId,rootObjectId);

@override
String toString() {
  return 'NetworkNodePublicationCommitReceipt(operation: $operation, domainCommitId: $domainCommitId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, rootObjectId: $rootObjectId)';
}


}

/// @nodoc
abstract mixin class $NetworkNodePublicationCommitReceiptCopyWith<$Res>  {
  factory $NetworkNodePublicationCommitReceiptCopyWith(NetworkNodePublicationCommitReceipt value, $Res Function(NetworkNodePublicationCommitReceipt) _then) = _$NetworkNodePublicationCommitReceiptCopyWithImpl;
@useResult
$Res call({
 String operation,@UuidValueConverter() UuidValue? domainCommitId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId,@UuidValueConverter() UuidValue? rootObjectId
});




}
/// @nodoc
class _$NetworkNodePublicationCommitReceiptCopyWithImpl<$Res>
    implements $NetworkNodePublicationCommitReceiptCopyWith<$Res> {
  _$NetworkNodePublicationCommitReceiptCopyWithImpl(this._self, this._then);

  final NetworkNodePublicationCommitReceipt _self;
  final $Res Function(NetworkNodePublicationCommitReceipt) _then;

/// Create a copy of NetworkNodePublicationCommitReceipt
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? operation = null,Object? domainCommitId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? rootObjectId = freezed,}) {
  return _then(_self.copyWith(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,domainCommitId: freezed == domainCommitId ? _self.domainCommitId : domainCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,rootObjectId: freezed == rootObjectId ? _self.rootObjectId : rootObjectId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkNodePublicationCommitReceipt].
extension NetworkNodePublicationCommitReceiptPatterns on NetworkNodePublicationCommitReceipt {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkNodePublicationCommitReceipt value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkNodePublicationCommitReceipt() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkNodePublicationCommitReceipt value)  def,}){
final _that = this;
switch (_that) {
case _NetworkNodePublicationCommitReceipt():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkNodePublicationCommitReceipt value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkNodePublicationCommitReceipt() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String operation, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId, @UuidValueConverter()  UuidValue? rootObjectId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkNodePublicationCommitReceipt() when def != null:
return def(_that.operation,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.rootObjectId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String operation, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId, @UuidValueConverter()  UuidValue? rootObjectId)  def,}) {final _that = this;
switch (_that) {
case _NetworkNodePublicationCommitReceipt():
return def(_that.operation,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.rootObjectId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String operation, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId, @UuidValueConverter()  UuidValue? rootObjectId)?  def,}) {final _that = this;
switch (_that) {
case _NetworkNodePublicationCommitReceipt() when def != null:
return def(_that.operation,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.rootObjectId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkNodePublicationCommitReceipt implements NetworkNodePublicationCommitReceipt {
   _NetworkNodePublicationCommitReceipt({required this.operation, @UuidValueConverter() this.domainCommitId, @UuidValueConverter() this.objectInstanceGraphCommitId, @UuidValueConverter() this.rootObjectId});
  factory _NetworkNodePublicationCommitReceipt.fromJson(Map<String, dynamic> json) => _$NetworkNodePublicationCommitReceiptFromJson(json);

@override final  String operation;
@override@UuidValueConverter() final  UuidValue? domainCommitId;
@override@UuidValueConverter() final  UuidValue? objectInstanceGraphCommitId;
@override@UuidValueConverter() final  UuidValue? rootObjectId;

/// Create a copy of NetworkNodePublicationCommitReceipt
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkNodePublicationCommitReceiptCopyWith<_NetworkNodePublicationCommitReceipt> get copyWith => __$NetworkNodePublicationCommitReceiptCopyWithImpl<_NetworkNodePublicationCommitReceipt>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkNodePublicationCommitReceiptToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkNodePublicationCommitReceipt&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.domainCommitId, domainCommitId) || other.domainCommitId == domainCommitId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.rootObjectId, rootObjectId) || other.rootObjectId == rootObjectId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,domainCommitId,objectInstanceGraphCommitId,rootObjectId);

@override
String toString() {
  return 'NetworkNodePublicationCommitReceipt.def(operation: $operation, domainCommitId: $domainCommitId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, rootObjectId: $rootObjectId)';
}


}

/// @nodoc
abstract mixin class _$NetworkNodePublicationCommitReceiptCopyWith<$Res> implements $NetworkNodePublicationCommitReceiptCopyWith<$Res> {
  factory _$NetworkNodePublicationCommitReceiptCopyWith(_NetworkNodePublicationCommitReceipt value, $Res Function(_NetworkNodePublicationCommitReceipt) _then) = __$NetworkNodePublicationCommitReceiptCopyWithImpl;
@override @useResult
$Res call({
 String operation,@UuidValueConverter() UuidValue? domainCommitId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId,@UuidValueConverter() UuidValue? rootObjectId
});




}
/// @nodoc
class __$NetworkNodePublicationCommitReceiptCopyWithImpl<$Res>
    implements _$NetworkNodePublicationCommitReceiptCopyWith<$Res> {
  __$NetworkNodePublicationCommitReceiptCopyWithImpl(this._self, this._then);

  final _NetworkNodePublicationCommitReceipt _self;
  final $Res Function(_NetworkNodePublicationCommitReceipt) _then;

/// Create a copy of NetworkNodePublicationCommitReceipt
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? operation = null,Object? domainCommitId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? rootObjectId = freezed,}) {
  return _then(_NetworkNodePublicationCommitReceipt(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,domainCommitId: freezed == domainCommitId ? _self.domainCommitId : domainCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,rootObjectId: freezed == rootObjectId ? _self.rootObjectId : rootObjectId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}


}


/// @nodoc
mixin _$NetworkNodePublicationCoverage {

 bool get nodeRegistered; bool get environmentPublished;@UuidValueListConverter() List<UuidValue> get hostedServicePackageIds;@UuidValueListConverter() List<UuidValue> get missingHostedServicePackageIds;@UuidValueListConverter() List<UuidValue> get unexpectedHostedServicePackageIds;
/// Create a copy of NetworkNodePublicationCoverage
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkNodePublicationCoverageCopyWith<NetworkNodePublicationCoverage> get copyWith => _$NetworkNodePublicationCoverageCopyWithImpl<NetworkNodePublicationCoverage>(this as NetworkNodePublicationCoverage, _$identity);

  /// Serializes this NetworkNodePublicationCoverage to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkNodePublicationCoverage&&(identical(other.nodeRegistered, nodeRegistered) || other.nodeRegistered == nodeRegistered)&&(identical(other.environmentPublished, environmentPublished) || other.environmentPublished == environmentPublished)&&const DeepCollectionEquality().equals(other.hostedServicePackageIds, hostedServicePackageIds)&&const DeepCollectionEquality().equals(other.missingHostedServicePackageIds, missingHostedServicePackageIds)&&const DeepCollectionEquality().equals(other.unexpectedHostedServicePackageIds, unexpectedHostedServicePackageIds));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,nodeRegistered,environmentPublished,const DeepCollectionEquality().hash(hostedServicePackageIds),const DeepCollectionEquality().hash(missingHostedServicePackageIds),const DeepCollectionEquality().hash(unexpectedHostedServicePackageIds));

@override
String toString() {
  return 'NetworkNodePublicationCoverage(nodeRegistered: $nodeRegistered, environmentPublished: $environmentPublished, hostedServicePackageIds: $hostedServicePackageIds, missingHostedServicePackageIds: $missingHostedServicePackageIds, unexpectedHostedServicePackageIds: $unexpectedHostedServicePackageIds)';
}


}

/// @nodoc
abstract mixin class $NetworkNodePublicationCoverageCopyWith<$Res>  {
  factory $NetworkNodePublicationCoverageCopyWith(NetworkNodePublicationCoverage value, $Res Function(NetworkNodePublicationCoverage) _then) = _$NetworkNodePublicationCoverageCopyWithImpl;
@useResult
$Res call({
 bool nodeRegistered, bool environmentPublished,@UuidValueListConverter() List<UuidValue> hostedServicePackageIds,@UuidValueListConverter() List<UuidValue> missingHostedServicePackageIds,@UuidValueListConverter() List<UuidValue> unexpectedHostedServicePackageIds
});




}
/// @nodoc
class _$NetworkNodePublicationCoverageCopyWithImpl<$Res>
    implements $NetworkNodePublicationCoverageCopyWith<$Res> {
  _$NetworkNodePublicationCoverageCopyWithImpl(this._self, this._then);

  final NetworkNodePublicationCoverage _self;
  final $Res Function(NetworkNodePublicationCoverage) _then;

/// Create a copy of NetworkNodePublicationCoverage
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? nodeRegistered = null,Object? environmentPublished = null,Object? hostedServicePackageIds = null,Object? missingHostedServicePackageIds = null,Object? unexpectedHostedServicePackageIds = null,}) {
  return _then(_self.copyWith(
nodeRegistered: null == nodeRegistered ? _self.nodeRegistered : nodeRegistered // ignore: cast_nullable_to_non_nullable
as bool,environmentPublished: null == environmentPublished ? _self.environmentPublished : environmentPublished // ignore: cast_nullable_to_non_nullable
as bool,hostedServicePackageIds: null == hostedServicePackageIds ? _self.hostedServicePackageIds : hostedServicePackageIds // ignore: cast_nullable_to_non_nullable
as List<UuidValue>,missingHostedServicePackageIds: null == missingHostedServicePackageIds ? _self.missingHostedServicePackageIds : missingHostedServicePackageIds // ignore: cast_nullable_to_non_nullable
as List<UuidValue>,unexpectedHostedServicePackageIds: null == unexpectedHostedServicePackageIds ? _self.unexpectedHostedServicePackageIds : unexpectedHostedServicePackageIds // ignore: cast_nullable_to_non_nullable
as List<UuidValue>,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkNodePublicationCoverage].
extension NetworkNodePublicationCoveragePatterns on NetworkNodePublicationCoverage {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkNodePublicationCoverage value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkNodePublicationCoverage() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkNodePublicationCoverage value)  def,}){
final _that = this;
switch (_that) {
case _NetworkNodePublicationCoverage():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkNodePublicationCoverage value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkNodePublicationCoverage() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( bool nodeRegistered,  bool environmentPublished, @UuidValueListConverter()  List<UuidValue> hostedServicePackageIds, @UuidValueListConverter()  List<UuidValue> missingHostedServicePackageIds, @UuidValueListConverter()  List<UuidValue> unexpectedHostedServicePackageIds)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkNodePublicationCoverage() when def != null:
return def(_that.nodeRegistered,_that.environmentPublished,_that.hostedServicePackageIds,_that.missingHostedServicePackageIds,_that.unexpectedHostedServicePackageIds);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( bool nodeRegistered,  bool environmentPublished, @UuidValueListConverter()  List<UuidValue> hostedServicePackageIds, @UuidValueListConverter()  List<UuidValue> missingHostedServicePackageIds, @UuidValueListConverter()  List<UuidValue> unexpectedHostedServicePackageIds)  def,}) {final _that = this;
switch (_that) {
case _NetworkNodePublicationCoverage():
return def(_that.nodeRegistered,_that.environmentPublished,_that.hostedServicePackageIds,_that.missingHostedServicePackageIds,_that.unexpectedHostedServicePackageIds);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( bool nodeRegistered,  bool environmentPublished, @UuidValueListConverter()  List<UuidValue> hostedServicePackageIds, @UuidValueListConverter()  List<UuidValue> missingHostedServicePackageIds, @UuidValueListConverter()  List<UuidValue> unexpectedHostedServicePackageIds)?  def,}) {final _that = this;
switch (_that) {
case _NetworkNodePublicationCoverage() when def != null:
return def(_that.nodeRegistered,_that.environmentPublished,_that.hostedServicePackageIds,_that.missingHostedServicePackageIds,_that.unexpectedHostedServicePackageIds);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkNodePublicationCoverage implements NetworkNodePublicationCoverage {
   _NetworkNodePublicationCoverage({required this.nodeRegistered, required this.environmentPublished, @UuidValueListConverter() final  List<UuidValue> hostedServicePackageIds = const [], @UuidValueListConverter() final  List<UuidValue> missingHostedServicePackageIds = const [], @UuidValueListConverter() final  List<UuidValue> unexpectedHostedServicePackageIds = const []}): _hostedServicePackageIds = hostedServicePackageIds,_missingHostedServicePackageIds = missingHostedServicePackageIds,_unexpectedHostedServicePackageIds = unexpectedHostedServicePackageIds;
  factory _NetworkNodePublicationCoverage.fromJson(Map<String, dynamic> json) => _$NetworkNodePublicationCoverageFromJson(json);

@override final  bool nodeRegistered;
@override final  bool environmentPublished;
 final  List<UuidValue> _hostedServicePackageIds;
@override@JsonKey()@UuidValueListConverter() List<UuidValue> get hostedServicePackageIds {
  if (_hostedServicePackageIds is EqualUnmodifiableListView) return _hostedServicePackageIds;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_hostedServicePackageIds);
}

 final  List<UuidValue> _missingHostedServicePackageIds;
@override@JsonKey()@UuidValueListConverter() List<UuidValue> get missingHostedServicePackageIds {
  if (_missingHostedServicePackageIds is EqualUnmodifiableListView) return _missingHostedServicePackageIds;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_missingHostedServicePackageIds);
}

 final  List<UuidValue> _unexpectedHostedServicePackageIds;
@override@JsonKey()@UuidValueListConverter() List<UuidValue> get unexpectedHostedServicePackageIds {
  if (_unexpectedHostedServicePackageIds is EqualUnmodifiableListView) return _unexpectedHostedServicePackageIds;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_unexpectedHostedServicePackageIds);
}


/// Create a copy of NetworkNodePublicationCoverage
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkNodePublicationCoverageCopyWith<_NetworkNodePublicationCoverage> get copyWith => __$NetworkNodePublicationCoverageCopyWithImpl<_NetworkNodePublicationCoverage>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkNodePublicationCoverageToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkNodePublicationCoverage&&(identical(other.nodeRegistered, nodeRegistered) || other.nodeRegistered == nodeRegistered)&&(identical(other.environmentPublished, environmentPublished) || other.environmentPublished == environmentPublished)&&const DeepCollectionEquality().equals(other._hostedServicePackageIds, _hostedServicePackageIds)&&const DeepCollectionEquality().equals(other._missingHostedServicePackageIds, _missingHostedServicePackageIds)&&const DeepCollectionEquality().equals(other._unexpectedHostedServicePackageIds, _unexpectedHostedServicePackageIds));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,nodeRegistered,environmentPublished,const DeepCollectionEquality().hash(_hostedServicePackageIds),const DeepCollectionEquality().hash(_missingHostedServicePackageIds),const DeepCollectionEquality().hash(_unexpectedHostedServicePackageIds));

@override
String toString() {
  return 'NetworkNodePublicationCoverage.def(nodeRegistered: $nodeRegistered, environmentPublished: $environmentPublished, hostedServicePackageIds: $hostedServicePackageIds, missingHostedServicePackageIds: $missingHostedServicePackageIds, unexpectedHostedServicePackageIds: $unexpectedHostedServicePackageIds)';
}


}

/// @nodoc
abstract mixin class _$NetworkNodePublicationCoverageCopyWith<$Res> implements $NetworkNodePublicationCoverageCopyWith<$Res> {
  factory _$NetworkNodePublicationCoverageCopyWith(_NetworkNodePublicationCoverage value, $Res Function(_NetworkNodePublicationCoverage) _then) = __$NetworkNodePublicationCoverageCopyWithImpl;
@override @useResult
$Res call({
 bool nodeRegistered, bool environmentPublished,@UuidValueListConverter() List<UuidValue> hostedServicePackageIds,@UuidValueListConverter() List<UuidValue> missingHostedServicePackageIds,@UuidValueListConverter() List<UuidValue> unexpectedHostedServicePackageIds
});




}
/// @nodoc
class __$NetworkNodePublicationCoverageCopyWithImpl<$Res>
    implements _$NetworkNodePublicationCoverageCopyWith<$Res> {
  __$NetworkNodePublicationCoverageCopyWithImpl(this._self, this._then);

  final _NetworkNodePublicationCoverage _self;
  final $Res Function(_NetworkNodePublicationCoverage) _then;

/// Create a copy of NetworkNodePublicationCoverage
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? nodeRegistered = null,Object? environmentPublished = null,Object? hostedServicePackageIds = null,Object? missingHostedServicePackageIds = null,Object? unexpectedHostedServicePackageIds = null,}) {
  return _then(_NetworkNodePublicationCoverage(
nodeRegistered: null == nodeRegistered ? _self.nodeRegistered : nodeRegistered // ignore: cast_nullable_to_non_nullable
as bool,environmentPublished: null == environmentPublished ? _self.environmentPublished : environmentPublished // ignore: cast_nullable_to_non_nullable
as bool,hostedServicePackageIds: null == hostedServicePackageIds ? _self._hostedServicePackageIds : hostedServicePackageIds // ignore: cast_nullable_to_non_nullable
as List<UuidValue>,missingHostedServicePackageIds: null == missingHostedServicePackageIds ? _self._missingHostedServicePackageIds : missingHostedServicePackageIds // ignore: cast_nullable_to_non_nullable
as List<UuidValue>,unexpectedHostedServicePackageIds: null == unexpectedHostedServicePackageIds ? _self._unexpectedHostedServicePackageIds : unexpectedHostedServicePackageIds // ignore: cast_nullable_to_non_nullable
as List<UuidValue>,
  ));
}


}


/// @nodoc
mixin _$NetworkReconcileNodePublicationRequest {

@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue? get requestId; NetworkNodePublicationIntent get intent;
/// Create a copy of NetworkReconcileNodePublicationRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkReconcileNodePublicationRequestCopyWith<NetworkReconcileNodePublicationRequest> get copyWith => _$NetworkReconcileNodePublicationRequestCopyWithImpl<NetworkReconcileNodePublicationRequest>(this as NetworkReconcileNodePublicationRequest, _$identity);

  /// Serializes this NetworkReconcileNodePublicationRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkReconcileNodePublicationRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.intent, intent) || other.intent == intent));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,intent);

@override
String toString() {
  return 'NetworkReconcileNodePublicationRequest(actorId: $actorId, requestId: $requestId, intent: $intent)';
}


}

/// @nodoc
abstract mixin class $NetworkReconcileNodePublicationRequestCopyWith<$Res>  {
  factory $NetworkReconcileNodePublicationRequestCopyWith(NetworkReconcileNodePublicationRequest value, $Res Function(NetworkReconcileNodePublicationRequest) _then) = _$NetworkReconcileNodePublicationRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId, NetworkNodePublicationIntent intent
});


$NetworkNodePublicationIntentCopyWith<$Res> get intent;

}
/// @nodoc
class _$NetworkReconcileNodePublicationRequestCopyWithImpl<$Res>
    implements $NetworkReconcileNodePublicationRequestCopyWith<$Res> {
  _$NetworkReconcileNodePublicationRequestCopyWithImpl(this._self, this._then);

  final NetworkReconcileNodePublicationRequest _self;
  final $Res Function(NetworkReconcileNodePublicationRequest) _then;

/// Create a copy of NetworkReconcileNodePublicationRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? intent = null,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,intent: null == intent ? _self.intent : intent // ignore: cast_nullable_to_non_nullable
as NetworkNodePublicationIntent,
  ));
}
/// Create a copy of NetworkReconcileNodePublicationRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodePublicationIntentCopyWith<$Res> get intent {
  
  return $NetworkNodePublicationIntentCopyWith<$Res>(_self.intent, (value) {
    return _then(_self.copyWith(intent: value));
  });
}
}


/// Adds pattern-matching-related methods to [NetworkReconcileNodePublicationRequest].
extension NetworkReconcileNodePublicationRequestPatterns on NetworkReconcileNodePublicationRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkReconcileNodePublicationRequest value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkReconcileNodePublicationRequest() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkReconcileNodePublicationRequest value)  def,}){
final _that = this;
switch (_that) {
case _NetworkReconcileNodePublicationRequest():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkReconcileNodePublicationRequest value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkReconcileNodePublicationRequest() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId,  NetworkNodePublicationIntent intent)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkReconcileNodePublicationRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.intent);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId,  NetworkNodePublicationIntent intent)  def,}) {final _that = this;
switch (_that) {
case _NetworkReconcileNodePublicationRequest():
return def(_that.actorId,_that.requestId,_that.intent);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId,  NetworkNodePublicationIntent intent)?  def,}) {final _that = this;
switch (_that) {
case _NetworkReconcileNodePublicationRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.intent);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkReconcileNodePublicationRequest implements NetworkReconcileNodePublicationRequest {
   _NetworkReconcileNodePublicationRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.requestId, required this.intent});
  factory _NetworkReconcileNodePublicationRequest.fromJson(Map<String, dynamic> json) => _$NetworkReconcileNodePublicationRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? requestId;
@override final  NetworkNodePublicationIntent intent;

/// Create a copy of NetworkReconcileNodePublicationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkReconcileNodePublicationRequestCopyWith<_NetworkReconcileNodePublicationRequest> get copyWith => __$NetworkReconcileNodePublicationRequestCopyWithImpl<_NetworkReconcileNodePublicationRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkReconcileNodePublicationRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkReconcileNodePublicationRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.intent, intent) || other.intent == intent));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,intent);

@override
String toString() {
  return 'NetworkReconcileNodePublicationRequest.def(actorId: $actorId, requestId: $requestId, intent: $intent)';
}


}

/// @nodoc
abstract mixin class _$NetworkReconcileNodePublicationRequestCopyWith<$Res> implements $NetworkReconcileNodePublicationRequestCopyWith<$Res> {
  factory _$NetworkReconcileNodePublicationRequestCopyWith(_NetworkReconcileNodePublicationRequest value, $Res Function(_NetworkReconcileNodePublicationRequest) _then) = __$NetworkReconcileNodePublicationRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId, NetworkNodePublicationIntent intent
});


@override $NetworkNodePublicationIntentCopyWith<$Res> get intent;

}
/// @nodoc
class __$NetworkReconcileNodePublicationRequestCopyWithImpl<$Res>
    implements _$NetworkReconcileNodePublicationRequestCopyWith<$Res> {
  __$NetworkReconcileNodePublicationRequestCopyWithImpl(this._self, this._then);

  final _NetworkReconcileNodePublicationRequest _self;
  final $Res Function(_NetworkReconcileNodePublicationRequest) _then;

/// Create a copy of NetworkReconcileNodePublicationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? intent = null,}) {
  return _then(_NetworkReconcileNodePublicationRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,intent: null == intent ? _self.intent : intent // ignore: cast_nullable_to_non_nullable
as NetworkNodePublicationIntent,
  ));
}

/// Create a copy of NetworkReconcileNodePublicationRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodePublicationIntentCopyWith<$Res> get intent {
  
  return $NetworkNodePublicationIntentCopyWith<$Res>(_self.intent, (value) {
    return _then(_self.copyWith(intent: value));
  });
}
}


/// @nodoc
mixin _$NetworkReconcileNodePublicationResponse {

@UuidValueConverter() UuidValue? get requestId; bool get success; String get status; String? get error; String? get publicationDigest; NetworkNodeRouteDescriptor? get node; NetworkEnvironmentDescriptor? get environment; List<NetworkHostedServiceDescriptor> get hostedServices; NetworkNodePublicationCoverage? get coverage; List<NetworkNodePublicationCommitReceipt> get commitReceipts;
/// Create a copy of NetworkReconcileNodePublicationResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkReconcileNodePublicationResponseCopyWith<NetworkReconcileNodePublicationResponse> get copyWith => _$NetworkReconcileNodePublicationResponseCopyWithImpl<NetworkReconcileNodePublicationResponse>(this as NetworkReconcileNodePublicationResponse, _$identity);

  /// Serializes this NetworkReconcileNodePublicationResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkReconcileNodePublicationResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.publicationDigest, publicationDigest) || other.publicationDigest == publicationDigest)&&(identical(other.node, node) || other.node == node)&&(identical(other.environment, environment) || other.environment == environment)&&const DeepCollectionEquality().equals(other.hostedServices, hostedServices)&&(identical(other.coverage, coverage) || other.coverage == coverage)&&const DeepCollectionEquality().equals(other.commitReceipts, commitReceipts));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,status,error,publicationDigest,node,environment,const DeepCollectionEquality().hash(hostedServices),coverage,const DeepCollectionEquality().hash(commitReceipts));

@override
String toString() {
  return 'NetworkReconcileNodePublicationResponse(requestId: $requestId, success: $success, status: $status, error: $error, publicationDigest: $publicationDigest, node: $node, environment: $environment, hostedServices: $hostedServices, coverage: $coverage, commitReceipts: $commitReceipts)';
}


}

/// @nodoc
abstract mixin class $NetworkReconcileNodePublicationResponseCopyWith<$Res>  {
  factory $NetworkReconcileNodePublicationResponseCopyWith(NetworkReconcileNodePublicationResponse value, $Res Function(NetworkReconcileNodePublicationResponse) _then) = _$NetworkReconcileNodePublicationResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String status, String? error, String? publicationDigest, NetworkNodeRouteDescriptor? node, NetworkEnvironmentDescriptor? environment, List<NetworkHostedServiceDescriptor> hostedServices, NetworkNodePublicationCoverage? coverage, List<NetworkNodePublicationCommitReceipt> commitReceipts
});


$NetworkNodeRouteDescriptorCopyWith<$Res>? get node;$NetworkEnvironmentDescriptorCopyWith<$Res>? get environment;$NetworkNodePublicationCoverageCopyWith<$Res>? get coverage;

}
/// @nodoc
class _$NetworkReconcileNodePublicationResponseCopyWithImpl<$Res>
    implements $NetworkReconcileNodePublicationResponseCopyWith<$Res> {
  _$NetworkReconcileNodePublicationResponseCopyWithImpl(this._self, this._then);

  final NetworkReconcileNodePublicationResponse _self;
  final $Res Function(NetworkReconcileNodePublicationResponse) _then;

/// Create a copy of NetworkReconcileNodePublicationResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? success = null,Object? status = null,Object? error = freezed,Object? publicationDigest = freezed,Object? node = freezed,Object? environment = freezed,Object? hostedServices = null,Object? coverage = freezed,Object? commitReceipts = null,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,publicationDigest: freezed == publicationDigest ? _self.publicationDigest : publicationDigest // ignore: cast_nullable_to_non_nullable
as String?,node: freezed == node ? _self.node : node // ignore: cast_nullable_to_non_nullable
as NetworkNodeRouteDescriptor?,environment: freezed == environment ? _self.environment : environment // ignore: cast_nullable_to_non_nullable
as NetworkEnvironmentDescriptor?,hostedServices: null == hostedServices ? _self.hostedServices : hostedServices // ignore: cast_nullable_to_non_nullable
as List<NetworkHostedServiceDescriptor>,coverage: freezed == coverage ? _self.coverage : coverage // ignore: cast_nullable_to_non_nullable
as NetworkNodePublicationCoverage?,commitReceipts: null == commitReceipts ? _self.commitReceipts : commitReceipts // ignore: cast_nullable_to_non_nullable
as List<NetworkNodePublicationCommitReceipt>,
  ));
}
/// Create a copy of NetworkReconcileNodePublicationResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodeRouteDescriptorCopyWith<$Res>? get node {
    if (_self.node == null) {
    return null;
  }

  return $NetworkNodeRouteDescriptorCopyWith<$Res>(_self.node!, (value) {
    return _then(_self.copyWith(node: value));
  });
}/// Create a copy of NetworkReconcileNodePublicationResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkEnvironmentDescriptorCopyWith<$Res>? get environment {
    if (_self.environment == null) {
    return null;
  }

  return $NetworkEnvironmentDescriptorCopyWith<$Res>(_self.environment!, (value) {
    return _then(_self.copyWith(environment: value));
  });
}/// Create a copy of NetworkReconcileNodePublicationResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodePublicationCoverageCopyWith<$Res>? get coverage {
    if (_self.coverage == null) {
    return null;
  }

  return $NetworkNodePublicationCoverageCopyWith<$Res>(_self.coverage!, (value) {
    return _then(_self.copyWith(coverage: value));
  });
}
}


/// Adds pattern-matching-related methods to [NetworkReconcileNodePublicationResponse].
extension NetworkReconcileNodePublicationResponsePatterns on NetworkReconcileNodePublicationResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkReconcileNodePublicationResponse value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkReconcileNodePublicationResponse() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkReconcileNodePublicationResponse value)  def,}){
final _that = this;
switch (_that) {
case _NetworkReconcileNodePublicationResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkReconcileNodePublicationResponse value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkReconcileNodePublicationResponse() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String status,  String? error,  String? publicationDigest,  NetworkNodeRouteDescriptor? node,  NetworkEnvironmentDescriptor? environment,  List<NetworkHostedServiceDescriptor> hostedServices,  NetworkNodePublicationCoverage? coverage,  List<NetworkNodePublicationCommitReceipt> commitReceipts)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkReconcileNodePublicationResponse() when def != null:
return def(_that.requestId,_that.success,_that.status,_that.error,_that.publicationDigest,_that.node,_that.environment,_that.hostedServices,_that.coverage,_that.commitReceipts);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String status,  String? error,  String? publicationDigest,  NetworkNodeRouteDescriptor? node,  NetworkEnvironmentDescriptor? environment,  List<NetworkHostedServiceDescriptor> hostedServices,  NetworkNodePublicationCoverage? coverage,  List<NetworkNodePublicationCommitReceipt> commitReceipts)  def,}) {final _that = this;
switch (_that) {
case _NetworkReconcileNodePublicationResponse():
return def(_that.requestId,_that.success,_that.status,_that.error,_that.publicationDigest,_that.node,_that.environment,_that.hostedServices,_that.coverage,_that.commitReceipts);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String status,  String? error,  String? publicationDigest,  NetworkNodeRouteDescriptor? node,  NetworkEnvironmentDescriptor? environment,  List<NetworkHostedServiceDescriptor> hostedServices,  NetworkNodePublicationCoverage? coverage,  List<NetworkNodePublicationCommitReceipt> commitReceipts)?  def,}) {final _that = this;
switch (_that) {
case _NetworkReconcileNodePublicationResponse() when def != null:
return def(_that.requestId,_that.success,_that.status,_that.error,_that.publicationDigest,_that.node,_that.environment,_that.hostedServices,_that.coverage,_that.commitReceipts);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkReconcileNodePublicationResponse implements NetworkReconcileNodePublicationResponse {
   _NetworkReconcileNodePublicationResponse({@UuidValueConverter() this.requestId, required this.success, required this.status, this.error, this.publicationDigest, this.node, this.environment, final  List<NetworkHostedServiceDescriptor> hostedServices = const [], this.coverage, final  List<NetworkNodePublicationCommitReceipt> commitReceipts = const []}): _hostedServices = hostedServices,_commitReceipts = commitReceipts;
  factory _NetworkReconcileNodePublicationResponse.fromJson(Map<String, dynamic> json) => _$NetworkReconcileNodePublicationResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String status;
@override final  String? error;
@override final  String? publicationDigest;
@override final  NetworkNodeRouteDescriptor? node;
@override final  NetworkEnvironmentDescriptor? environment;
 final  List<NetworkHostedServiceDescriptor> _hostedServices;
@override@JsonKey() List<NetworkHostedServiceDescriptor> get hostedServices {
  if (_hostedServices is EqualUnmodifiableListView) return _hostedServices;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_hostedServices);
}

@override final  NetworkNodePublicationCoverage? coverage;
 final  List<NetworkNodePublicationCommitReceipt> _commitReceipts;
@override@JsonKey() List<NetworkNodePublicationCommitReceipt> get commitReceipts {
  if (_commitReceipts is EqualUnmodifiableListView) return _commitReceipts;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_commitReceipts);
}


/// Create a copy of NetworkReconcileNodePublicationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkReconcileNodePublicationResponseCopyWith<_NetworkReconcileNodePublicationResponse> get copyWith => __$NetworkReconcileNodePublicationResponseCopyWithImpl<_NetworkReconcileNodePublicationResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkReconcileNodePublicationResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkReconcileNodePublicationResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.publicationDigest, publicationDigest) || other.publicationDigest == publicationDigest)&&(identical(other.node, node) || other.node == node)&&(identical(other.environment, environment) || other.environment == environment)&&const DeepCollectionEquality().equals(other._hostedServices, _hostedServices)&&(identical(other.coverage, coverage) || other.coverage == coverage)&&const DeepCollectionEquality().equals(other._commitReceipts, _commitReceipts));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,status,error,publicationDigest,node,environment,const DeepCollectionEquality().hash(_hostedServices),coverage,const DeepCollectionEquality().hash(_commitReceipts));

@override
String toString() {
  return 'NetworkReconcileNodePublicationResponse.def(requestId: $requestId, success: $success, status: $status, error: $error, publicationDigest: $publicationDigest, node: $node, environment: $environment, hostedServices: $hostedServices, coverage: $coverage, commitReceipts: $commitReceipts)';
}


}

/// @nodoc
abstract mixin class _$NetworkReconcileNodePublicationResponseCopyWith<$Res> implements $NetworkReconcileNodePublicationResponseCopyWith<$Res> {
  factory _$NetworkReconcileNodePublicationResponseCopyWith(_NetworkReconcileNodePublicationResponse value, $Res Function(_NetworkReconcileNodePublicationResponse) _then) = __$NetworkReconcileNodePublicationResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String status, String? error, String? publicationDigest, NetworkNodeRouteDescriptor? node, NetworkEnvironmentDescriptor? environment, List<NetworkHostedServiceDescriptor> hostedServices, NetworkNodePublicationCoverage? coverage, List<NetworkNodePublicationCommitReceipt> commitReceipts
});


@override $NetworkNodeRouteDescriptorCopyWith<$Res>? get node;@override $NetworkEnvironmentDescriptorCopyWith<$Res>? get environment;@override $NetworkNodePublicationCoverageCopyWith<$Res>? get coverage;

}
/// @nodoc
class __$NetworkReconcileNodePublicationResponseCopyWithImpl<$Res>
    implements _$NetworkReconcileNodePublicationResponseCopyWith<$Res> {
  __$NetworkReconcileNodePublicationResponseCopyWithImpl(this._self, this._then);

  final _NetworkReconcileNodePublicationResponse _self;
  final $Res Function(_NetworkReconcileNodePublicationResponse) _then;

/// Create a copy of NetworkReconcileNodePublicationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? status = null,Object? error = freezed,Object? publicationDigest = freezed,Object? node = freezed,Object? environment = freezed,Object? hostedServices = null,Object? coverage = freezed,Object? commitReceipts = null,}) {
  return _then(_NetworkReconcileNodePublicationResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,publicationDigest: freezed == publicationDigest ? _self.publicationDigest : publicationDigest // ignore: cast_nullable_to_non_nullable
as String?,node: freezed == node ? _self.node : node // ignore: cast_nullable_to_non_nullable
as NetworkNodeRouteDescriptor?,environment: freezed == environment ? _self.environment : environment // ignore: cast_nullable_to_non_nullable
as NetworkEnvironmentDescriptor?,hostedServices: null == hostedServices ? _self._hostedServices : hostedServices // ignore: cast_nullable_to_non_nullable
as List<NetworkHostedServiceDescriptor>,coverage: freezed == coverage ? _self.coverage : coverage // ignore: cast_nullable_to_non_nullable
as NetworkNodePublicationCoverage?,commitReceipts: null == commitReceipts ? _self._commitReceipts : commitReceipts // ignore: cast_nullable_to_non_nullable
as List<NetworkNodePublicationCommitReceipt>,
  ));
}

/// Create a copy of NetworkReconcileNodePublicationResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodeRouteDescriptorCopyWith<$Res>? get node {
    if (_self.node == null) {
    return null;
  }

  return $NetworkNodeRouteDescriptorCopyWith<$Res>(_self.node!, (value) {
    return _then(_self.copyWith(node: value));
  });
}/// Create a copy of NetworkReconcileNodePublicationResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkEnvironmentDescriptorCopyWith<$Res>? get environment {
    if (_self.environment == null) {
    return null;
  }

  return $NetworkEnvironmentDescriptorCopyWith<$Res>(_self.environment!, (value) {
    return _then(_self.copyWith(environment: value));
  });
}/// Create a copy of NetworkReconcileNodePublicationResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodePublicationCoverageCopyWith<$Res>? get coverage {
    if (_self.coverage == null) {
    return null;
  }

  return $NetworkNodePublicationCoverageCopyWith<$Res>(_self.coverage!, (value) {
    return _then(_self.copyWith(coverage: value));
  });
}
}


/// @nodoc
mixin _$NetworkRegisterNodeRequest {

@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue? get requestId;@UuidValueConverter() UuidValue? get nodeId; String get publicKey; String get hostname; int get port; String? get baseUrl; String get status;
/// Create a copy of NetworkRegisterNodeRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkRegisterNodeRequestCopyWith<NetworkRegisterNodeRequest> get copyWith => _$NetworkRegisterNodeRequestCopyWithImpl<NetworkRegisterNodeRequest>(this as NetworkRegisterNodeRequest, _$identity);

  /// Serializes this NetworkRegisterNodeRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkRegisterNodeRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.publicKey, publicKey) || other.publicKey == publicKey)&&(identical(other.hostname, hostname) || other.hostname == hostname)&&(identical(other.port, port) || other.port == port)&&(identical(other.baseUrl, baseUrl) || other.baseUrl == baseUrl)&&(identical(other.status, status) || other.status == status));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,nodeId,publicKey,hostname,port,baseUrl,status);

@override
String toString() {
  return 'NetworkRegisterNodeRequest(actorId: $actorId, requestId: $requestId, nodeId: $nodeId, publicKey: $publicKey, hostname: $hostname, port: $port, baseUrl: $baseUrl, status: $status)';
}


}

/// @nodoc
abstract mixin class $NetworkRegisterNodeRequestCopyWith<$Res>  {
  factory $NetworkRegisterNodeRequestCopyWith(NetworkRegisterNodeRequest value, $Res Function(NetworkRegisterNodeRequest) _then) = _$NetworkRegisterNodeRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue? nodeId, String publicKey, String hostname, int port, String? baseUrl, String status
});




}
/// @nodoc
class _$NetworkRegisterNodeRequestCopyWithImpl<$Res>
    implements $NetworkRegisterNodeRequestCopyWith<$Res> {
  _$NetworkRegisterNodeRequestCopyWithImpl(this._self, this._then);

  final NetworkRegisterNodeRequest _self;
  final $Res Function(NetworkRegisterNodeRequest) _then;

/// Create a copy of NetworkRegisterNodeRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? nodeId = freezed,Object? publicKey = null,Object? hostname = null,Object? port = null,Object? baseUrl = freezed,Object? status = null,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,publicKey: null == publicKey ? _self.publicKey : publicKey // ignore: cast_nullable_to_non_nullable
as String,hostname: null == hostname ? _self.hostname : hostname // ignore: cast_nullable_to_non_nullable
as String,port: null == port ? _self.port : port // ignore: cast_nullable_to_non_nullable
as int,baseUrl: freezed == baseUrl ? _self.baseUrl : baseUrl // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkRegisterNodeRequest].
extension NetworkRegisterNodeRequestPatterns on NetworkRegisterNodeRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkRegisterNodeRequest value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkRegisterNodeRequest() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkRegisterNodeRequest value)  def,}){
final _that = this;
switch (_that) {
case _NetworkRegisterNodeRequest():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkRegisterNodeRequest value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkRegisterNodeRequest() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? nodeId,  String publicKey,  String hostname,  int port,  String? baseUrl,  String status)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkRegisterNodeRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.nodeId,_that.publicKey,_that.hostname,_that.port,_that.baseUrl,_that.status);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? nodeId,  String publicKey,  String hostname,  int port,  String? baseUrl,  String status)  def,}) {final _that = this;
switch (_that) {
case _NetworkRegisterNodeRequest():
return def(_that.actorId,_that.requestId,_that.nodeId,_that.publicKey,_that.hostname,_that.port,_that.baseUrl,_that.status);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? nodeId,  String publicKey,  String hostname,  int port,  String? baseUrl,  String status)?  def,}) {final _that = this;
switch (_that) {
case _NetworkRegisterNodeRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.nodeId,_that.publicKey,_that.hostname,_that.port,_that.baseUrl,_that.status);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkRegisterNodeRequest implements NetworkRegisterNodeRequest {
   _NetworkRegisterNodeRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.requestId, @UuidValueConverter() this.nodeId, required this.publicKey, required this.hostname, required this.port, this.baseUrl, required this.status});
  factory _NetworkRegisterNodeRequest.fromJson(Map<String, dynamic> json) => _$NetworkRegisterNodeRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? requestId;
@override@UuidValueConverter() final  UuidValue? nodeId;
@override final  String publicKey;
@override final  String hostname;
@override final  int port;
@override final  String? baseUrl;
@override final  String status;

/// Create a copy of NetworkRegisterNodeRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkRegisterNodeRequestCopyWith<_NetworkRegisterNodeRequest> get copyWith => __$NetworkRegisterNodeRequestCopyWithImpl<_NetworkRegisterNodeRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkRegisterNodeRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkRegisterNodeRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.publicKey, publicKey) || other.publicKey == publicKey)&&(identical(other.hostname, hostname) || other.hostname == hostname)&&(identical(other.port, port) || other.port == port)&&(identical(other.baseUrl, baseUrl) || other.baseUrl == baseUrl)&&(identical(other.status, status) || other.status == status));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,nodeId,publicKey,hostname,port,baseUrl,status);

@override
String toString() {
  return 'NetworkRegisterNodeRequest.def(actorId: $actorId, requestId: $requestId, nodeId: $nodeId, publicKey: $publicKey, hostname: $hostname, port: $port, baseUrl: $baseUrl, status: $status)';
}


}

/// @nodoc
abstract mixin class _$NetworkRegisterNodeRequestCopyWith<$Res> implements $NetworkRegisterNodeRequestCopyWith<$Res> {
  factory _$NetworkRegisterNodeRequestCopyWith(_NetworkRegisterNodeRequest value, $Res Function(_NetworkRegisterNodeRequest) _then) = __$NetworkRegisterNodeRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue? nodeId, String publicKey, String hostname, int port, String? baseUrl, String status
});




}
/// @nodoc
class __$NetworkRegisterNodeRequestCopyWithImpl<$Res>
    implements _$NetworkRegisterNodeRequestCopyWith<$Res> {
  __$NetworkRegisterNodeRequestCopyWithImpl(this._self, this._then);

  final _NetworkRegisterNodeRequest _self;
  final $Res Function(_NetworkRegisterNodeRequest) _then;

/// Create a copy of NetworkRegisterNodeRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? nodeId = freezed,Object? publicKey = null,Object? hostname = null,Object? port = null,Object? baseUrl = freezed,Object? status = null,}) {
  return _then(_NetworkRegisterNodeRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,publicKey: null == publicKey ? _self.publicKey : publicKey // ignore: cast_nullable_to_non_nullable
as String,hostname: null == hostname ? _self.hostname : hostname // ignore: cast_nullable_to_non_nullable
as String,port: null == port ? _self.port : port // ignore: cast_nullable_to_non_nullable
as int,baseUrl: freezed == baseUrl ? _self.baseUrl : baseUrl // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}


/// @nodoc
mixin _$NetworkRegisterNodeResponse {

@UuidValueConverter() UuidValue? get requestId; bool get success; String? get error; NetworkNodeRouteDescriptor? get node;
/// Create a copy of NetworkRegisterNodeResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkRegisterNodeResponseCopyWith<NetworkRegisterNodeResponse> get copyWith => _$NetworkRegisterNodeResponseCopyWithImpl<NetworkRegisterNodeResponse>(this as NetworkRegisterNodeResponse, _$identity);

  /// Serializes this NetworkRegisterNodeResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkRegisterNodeResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.node, node) || other.node == node));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,node);

@override
String toString() {
  return 'NetworkRegisterNodeResponse(requestId: $requestId, success: $success, error: $error, node: $node)';
}


}

/// @nodoc
abstract mixin class $NetworkRegisterNodeResponseCopyWith<$Res>  {
  factory $NetworkRegisterNodeResponseCopyWith(NetworkRegisterNodeResponse value, $Res Function(NetworkRegisterNodeResponse) _then) = _$NetworkRegisterNodeResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, NetworkNodeRouteDescriptor? node
});


$NetworkNodeRouteDescriptorCopyWith<$Res>? get node;

}
/// @nodoc
class _$NetworkRegisterNodeResponseCopyWithImpl<$Res>
    implements $NetworkRegisterNodeResponseCopyWith<$Res> {
  _$NetworkRegisterNodeResponseCopyWithImpl(this._self, this._then);

  final NetworkRegisterNodeResponse _self;
  final $Res Function(NetworkRegisterNodeResponse) _then;

/// Create a copy of NetworkRegisterNodeResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? node = freezed,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,node: freezed == node ? _self.node : node // ignore: cast_nullable_to_non_nullable
as NetworkNodeRouteDescriptor?,
  ));
}
/// Create a copy of NetworkRegisterNodeResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodeRouteDescriptorCopyWith<$Res>? get node {
    if (_self.node == null) {
    return null;
  }

  return $NetworkNodeRouteDescriptorCopyWith<$Res>(_self.node!, (value) {
    return _then(_self.copyWith(node: value));
  });
}
}


/// Adds pattern-matching-related methods to [NetworkRegisterNodeResponse].
extension NetworkRegisterNodeResponsePatterns on NetworkRegisterNodeResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkRegisterNodeResponse value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkRegisterNodeResponse() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkRegisterNodeResponse value)  def,}){
final _that = this;
switch (_that) {
case _NetworkRegisterNodeResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkRegisterNodeResponse value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkRegisterNodeResponse() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  NetworkNodeRouteDescriptor? node)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkRegisterNodeResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.node);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  NetworkNodeRouteDescriptor? node)  def,}) {final _that = this;
switch (_that) {
case _NetworkRegisterNodeResponse():
return def(_that.requestId,_that.success,_that.error,_that.node);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  NetworkNodeRouteDescriptor? node)?  def,}) {final _that = this;
switch (_that) {
case _NetworkRegisterNodeResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.node);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkRegisterNodeResponse implements NetworkRegisterNodeResponse {
   _NetworkRegisterNodeResponse({@UuidValueConverter() this.requestId, required this.success, this.error, this.node});
  factory _NetworkRegisterNodeResponse.fromJson(Map<String, dynamic> json) => _$NetworkRegisterNodeResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? error;
@override final  NetworkNodeRouteDescriptor? node;

/// Create a copy of NetworkRegisterNodeResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkRegisterNodeResponseCopyWith<_NetworkRegisterNodeResponse> get copyWith => __$NetworkRegisterNodeResponseCopyWithImpl<_NetworkRegisterNodeResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkRegisterNodeResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkRegisterNodeResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.node, node) || other.node == node));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,node);

@override
String toString() {
  return 'NetworkRegisterNodeResponse.def(requestId: $requestId, success: $success, error: $error, node: $node)';
}


}

/// @nodoc
abstract mixin class _$NetworkRegisterNodeResponseCopyWith<$Res> implements $NetworkRegisterNodeResponseCopyWith<$Res> {
  factory _$NetworkRegisterNodeResponseCopyWith(_NetworkRegisterNodeResponse value, $Res Function(_NetworkRegisterNodeResponse) _then) = __$NetworkRegisterNodeResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, NetworkNodeRouteDescriptor? node
});


@override $NetworkNodeRouteDescriptorCopyWith<$Res>? get node;

}
/// @nodoc
class __$NetworkRegisterNodeResponseCopyWithImpl<$Res>
    implements _$NetworkRegisterNodeResponseCopyWith<$Res> {
  __$NetworkRegisterNodeResponseCopyWithImpl(this._self, this._then);

  final _NetworkRegisterNodeResponse _self;
  final $Res Function(_NetworkRegisterNodeResponse) _then;

/// Create a copy of NetworkRegisterNodeResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? node = freezed,}) {
  return _then(_NetworkRegisterNodeResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,node: freezed == node ? _self.node : node // ignore: cast_nullable_to_non_nullable
as NetworkNodeRouteDescriptor?,
  ));
}

/// Create a copy of NetworkRegisterNodeResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkNodeRouteDescriptorCopyWith<$Res>? get node {
    if (_self.node == null) {
    return null;
  }

  return $NetworkNodeRouteDescriptorCopyWith<$Res>(_self.node!, (value) {
    return _then(_self.copyWith(node: value));
  });
}
}


/// @nodoc
mixin _$NetworkUpsertPeerRequest {

@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue? get requestId;@UuidValueConverter() UuidValue get sourceNodeId;@UuidValueConverter() UuidValue get targetNodeId; String get targetBaseUrl; String get status; double get trustScore;
/// Create a copy of NetworkUpsertPeerRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkUpsertPeerRequestCopyWith<NetworkUpsertPeerRequest> get copyWith => _$NetworkUpsertPeerRequestCopyWithImpl<NetworkUpsertPeerRequest>(this as NetworkUpsertPeerRequest, _$identity);

  /// Serializes this NetworkUpsertPeerRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkUpsertPeerRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.sourceNodeId, sourceNodeId) || other.sourceNodeId == sourceNodeId)&&(identical(other.targetNodeId, targetNodeId) || other.targetNodeId == targetNodeId)&&(identical(other.targetBaseUrl, targetBaseUrl) || other.targetBaseUrl == targetBaseUrl)&&(identical(other.status, status) || other.status == status)&&(identical(other.trustScore, trustScore) || other.trustScore == trustScore));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,sourceNodeId,targetNodeId,targetBaseUrl,status,trustScore);

@override
String toString() {
  return 'NetworkUpsertPeerRequest(actorId: $actorId, requestId: $requestId, sourceNodeId: $sourceNodeId, targetNodeId: $targetNodeId, targetBaseUrl: $targetBaseUrl, status: $status, trustScore: $trustScore)';
}


}

/// @nodoc
abstract mixin class $NetworkUpsertPeerRequestCopyWith<$Res>  {
  factory $NetworkUpsertPeerRequestCopyWith(NetworkUpsertPeerRequest value, $Res Function(NetworkUpsertPeerRequest) _then) = _$NetworkUpsertPeerRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue sourceNodeId,@UuidValueConverter() UuidValue targetNodeId, String targetBaseUrl, String status, double trustScore
});




}
/// @nodoc
class _$NetworkUpsertPeerRequestCopyWithImpl<$Res>
    implements $NetworkUpsertPeerRequestCopyWith<$Res> {
  _$NetworkUpsertPeerRequestCopyWithImpl(this._self, this._then);

  final NetworkUpsertPeerRequest _self;
  final $Res Function(NetworkUpsertPeerRequest) _then;

/// Create a copy of NetworkUpsertPeerRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? sourceNodeId = null,Object? targetNodeId = null,Object? targetBaseUrl = null,Object? status = null,Object? trustScore = null,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sourceNodeId: null == sourceNodeId ? _self.sourceNodeId : sourceNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,targetNodeId: null == targetNodeId ? _self.targetNodeId : targetNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,targetBaseUrl: null == targetBaseUrl ? _self.targetBaseUrl : targetBaseUrl // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,trustScore: null == trustScore ? _self.trustScore : trustScore // ignore: cast_nullable_to_non_nullable
as double,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkUpsertPeerRequest].
extension NetworkUpsertPeerRequestPatterns on NetworkUpsertPeerRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkUpsertPeerRequest value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkUpsertPeerRequest() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkUpsertPeerRequest value)  def,}){
final _that = this;
switch (_that) {
case _NetworkUpsertPeerRequest():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkUpsertPeerRequest value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkUpsertPeerRequest() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue sourceNodeId, @UuidValueConverter()  UuidValue targetNodeId,  String targetBaseUrl,  String status,  double trustScore)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkUpsertPeerRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.sourceNodeId,_that.targetNodeId,_that.targetBaseUrl,_that.status,_that.trustScore);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue sourceNodeId, @UuidValueConverter()  UuidValue targetNodeId,  String targetBaseUrl,  String status,  double trustScore)  def,}) {final _that = this;
switch (_that) {
case _NetworkUpsertPeerRequest():
return def(_that.actorId,_that.requestId,_that.sourceNodeId,_that.targetNodeId,_that.targetBaseUrl,_that.status,_that.trustScore);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue sourceNodeId, @UuidValueConverter()  UuidValue targetNodeId,  String targetBaseUrl,  String status,  double trustScore)?  def,}) {final _that = this;
switch (_that) {
case _NetworkUpsertPeerRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.sourceNodeId,_that.targetNodeId,_that.targetBaseUrl,_that.status,_that.trustScore);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkUpsertPeerRequest implements NetworkUpsertPeerRequest {
   _NetworkUpsertPeerRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.requestId, @UuidValueConverter() required this.sourceNodeId, @UuidValueConverter() required this.targetNodeId, required this.targetBaseUrl, required this.status, required this.trustScore});
  factory _NetworkUpsertPeerRequest.fromJson(Map<String, dynamic> json) => _$NetworkUpsertPeerRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? requestId;
@override@UuidValueConverter() final  UuidValue sourceNodeId;
@override@UuidValueConverter() final  UuidValue targetNodeId;
@override final  String targetBaseUrl;
@override final  String status;
@override final  double trustScore;

/// Create a copy of NetworkUpsertPeerRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkUpsertPeerRequestCopyWith<_NetworkUpsertPeerRequest> get copyWith => __$NetworkUpsertPeerRequestCopyWithImpl<_NetworkUpsertPeerRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkUpsertPeerRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkUpsertPeerRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.sourceNodeId, sourceNodeId) || other.sourceNodeId == sourceNodeId)&&(identical(other.targetNodeId, targetNodeId) || other.targetNodeId == targetNodeId)&&(identical(other.targetBaseUrl, targetBaseUrl) || other.targetBaseUrl == targetBaseUrl)&&(identical(other.status, status) || other.status == status)&&(identical(other.trustScore, trustScore) || other.trustScore == trustScore));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,sourceNodeId,targetNodeId,targetBaseUrl,status,trustScore);

@override
String toString() {
  return 'NetworkUpsertPeerRequest.def(actorId: $actorId, requestId: $requestId, sourceNodeId: $sourceNodeId, targetNodeId: $targetNodeId, targetBaseUrl: $targetBaseUrl, status: $status, trustScore: $trustScore)';
}


}

/// @nodoc
abstract mixin class _$NetworkUpsertPeerRequestCopyWith<$Res> implements $NetworkUpsertPeerRequestCopyWith<$Res> {
  factory _$NetworkUpsertPeerRequestCopyWith(_NetworkUpsertPeerRequest value, $Res Function(_NetworkUpsertPeerRequest) _then) = __$NetworkUpsertPeerRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue sourceNodeId,@UuidValueConverter() UuidValue targetNodeId, String targetBaseUrl, String status, double trustScore
});




}
/// @nodoc
class __$NetworkUpsertPeerRequestCopyWithImpl<$Res>
    implements _$NetworkUpsertPeerRequestCopyWith<$Res> {
  __$NetworkUpsertPeerRequestCopyWithImpl(this._self, this._then);

  final _NetworkUpsertPeerRequest _self;
  final $Res Function(_NetworkUpsertPeerRequest) _then;

/// Create a copy of NetworkUpsertPeerRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? sourceNodeId = null,Object? targetNodeId = null,Object? targetBaseUrl = null,Object? status = null,Object? trustScore = null,}) {
  return _then(_NetworkUpsertPeerRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sourceNodeId: null == sourceNodeId ? _self.sourceNodeId : sourceNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,targetNodeId: null == targetNodeId ? _self.targetNodeId : targetNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,targetBaseUrl: null == targetBaseUrl ? _self.targetBaseUrl : targetBaseUrl // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,trustScore: null == trustScore ? _self.trustScore : trustScore // ignore: cast_nullable_to_non_nullable
as double,
  ));
}


}


/// @nodoc
mixin _$NetworkUpsertPeerResponse {

@UuidValueConverter() UuidValue? get requestId; bool get success; String? get error; NetworkPeerDescriptor? get peer;
/// Create a copy of NetworkUpsertPeerResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkUpsertPeerResponseCopyWith<NetworkUpsertPeerResponse> get copyWith => _$NetworkUpsertPeerResponseCopyWithImpl<NetworkUpsertPeerResponse>(this as NetworkUpsertPeerResponse, _$identity);

  /// Serializes this NetworkUpsertPeerResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkUpsertPeerResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.peer, peer) || other.peer == peer));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,peer);

@override
String toString() {
  return 'NetworkUpsertPeerResponse(requestId: $requestId, success: $success, error: $error, peer: $peer)';
}


}

/// @nodoc
abstract mixin class $NetworkUpsertPeerResponseCopyWith<$Res>  {
  factory $NetworkUpsertPeerResponseCopyWith(NetworkUpsertPeerResponse value, $Res Function(NetworkUpsertPeerResponse) _then) = _$NetworkUpsertPeerResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, NetworkPeerDescriptor? peer
});


$NetworkPeerDescriptorCopyWith<$Res>? get peer;

}
/// @nodoc
class _$NetworkUpsertPeerResponseCopyWithImpl<$Res>
    implements $NetworkUpsertPeerResponseCopyWith<$Res> {
  _$NetworkUpsertPeerResponseCopyWithImpl(this._self, this._then);

  final NetworkUpsertPeerResponse _self;
  final $Res Function(NetworkUpsertPeerResponse) _then;

/// Create a copy of NetworkUpsertPeerResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? peer = freezed,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,peer: freezed == peer ? _self.peer : peer // ignore: cast_nullable_to_non_nullable
as NetworkPeerDescriptor?,
  ));
}
/// Create a copy of NetworkUpsertPeerResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkPeerDescriptorCopyWith<$Res>? get peer {
    if (_self.peer == null) {
    return null;
  }

  return $NetworkPeerDescriptorCopyWith<$Res>(_self.peer!, (value) {
    return _then(_self.copyWith(peer: value));
  });
}
}


/// Adds pattern-matching-related methods to [NetworkUpsertPeerResponse].
extension NetworkUpsertPeerResponsePatterns on NetworkUpsertPeerResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkUpsertPeerResponse value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkUpsertPeerResponse() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkUpsertPeerResponse value)  def,}){
final _that = this;
switch (_that) {
case _NetworkUpsertPeerResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkUpsertPeerResponse value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkUpsertPeerResponse() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  NetworkPeerDescriptor? peer)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkUpsertPeerResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.peer);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  NetworkPeerDescriptor? peer)  def,}) {final _that = this;
switch (_that) {
case _NetworkUpsertPeerResponse():
return def(_that.requestId,_that.success,_that.error,_that.peer);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  NetworkPeerDescriptor? peer)?  def,}) {final _that = this;
switch (_that) {
case _NetworkUpsertPeerResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.peer);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkUpsertPeerResponse implements NetworkUpsertPeerResponse {
   _NetworkUpsertPeerResponse({@UuidValueConverter() this.requestId, required this.success, this.error, this.peer});
  factory _NetworkUpsertPeerResponse.fromJson(Map<String, dynamic> json) => _$NetworkUpsertPeerResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? error;
@override final  NetworkPeerDescriptor? peer;

/// Create a copy of NetworkUpsertPeerResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkUpsertPeerResponseCopyWith<_NetworkUpsertPeerResponse> get copyWith => __$NetworkUpsertPeerResponseCopyWithImpl<_NetworkUpsertPeerResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkUpsertPeerResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkUpsertPeerResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.peer, peer) || other.peer == peer));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,peer);

@override
String toString() {
  return 'NetworkUpsertPeerResponse.def(requestId: $requestId, success: $success, error: $error, peer: $peer)';
}


}

/// @nodoc
abstract mixin class _$NetworkUpsertPeerResponseCopyWith<$Res> implements $NetworkUpsertPeerResponseCopyWith<$Res> {
  factory _$NetworkUpsertPeerResponseCopyWith(_NetworkUpsertPeerResponse value, $Res Function(_NetworkUpsertPeerResponse) _then) = __$NetworkUpsertPeerResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, NetworkPeerDescriptor? peer
});


@override $NetworkPeerDescriptorCopyWith<$Res>? get peer;

}
/// @nodoc
class __$NetworkUpsertPeerResponseCopyWithImpl<$Res>
    implements _$NetworkUpsertPeerResponseCopyWith<$Res> {
  __$NetworkUpsertPeerResponseCopyWithImpl(this._self, this._then);

  final _NetworkUpsertPeerResponse _self;
  final $Res Function(_NetworkUpsertPeerResponse) _then;

/// Create a copy of NetworkUpsertPeerResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? peer = freezed,}) {
  return _then(_NetworkUpsertPeerResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,peer: freezed == peer ? _self.peer : peer // ignore: cast_nullable_to_non_nullable
as NetworkPeerDescriptor?,
  ));
}

/// Create a copy of NetworkUpsertPeerResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkPeerDescriptorCopyWith<$Res>? get peer {
    if (_self.peer == null) {
    return null;
  }

  return $NetworkPeerDescriptorCopyWith<$Res>(_self.peer!, (value) {
    return _then(_self.copyWith(peer: value));
  });
}
}


/// @nodoc
mixin _$NetworkListPeersRequest {

@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue? get requestId;@UuidValueConverter() UuidValue get nodeId; bool get includeIncoming; bool get includeOutgoing; bool get acceptedOnly; int? get limitResults;
/// Create a copy of NetworkListPeersRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkListPeersRequestCopyWith<NetworkListPeersRequest> get copyWith => _$NetworkListPeersRequestCopyWithImpl<NetworkListPeersRequest>(this as NetworkListPeersRequest, _$identity);

  /// Serializes this NetworkListPeersRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkListPeersRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.includeIncoming, includeIncoming) || other.includeIncoming == includeIncoming)&&(identical(other.includeOutgoing, includeOutgoing) || other.includeOutgoing == includeOutgoing)&&(identical(other.acceptedOnly, acceptedOnly) || other.acceptedOnly == acceptedOnly)&&(identical(other.limitResults, limitResults) || other.limitResults == limitResults));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,nodeId,includeIncoming,includeOutgoing,acceptedOnly,limitResults);

@override
String toString() {
  return 'NetworkListPeersRequest(actorId: $actorId, requestId: $requestId, nodeId: $nodeId, includeIncoming: $includeIncoming, includeOutgoing: $includeOutgoing, acceptedOnly: $acceptedOnly, limitResults: $limitResults)';
}


}

/// @nodoc
abstract mixin class $NetworkListPeersRequestCopyWith<$Res>  {
  factory $NetworkListPeersRequestCopyWith(NetworkListPeersRequest value, $Res Function(NetworkListPeersRequest) _then) = _$NetworkListPeersRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue nodeId, bool includeIncoming, bool includeOutgoing, bool acceptedOnly, int? limitResults
});




}
/// @nodoc
class _$NetworkListPeersRequestCopyWithImpl<$Res>
    implements $NetworkListPeersRequestCopyWith<$Res> {
  _$NetworkListPeersRequestCopyWithImpl(this._self, this._then);

  final NetworkListPeersRequest _self;
  final $Res Function(NetworkListPeersRequest) _then;

/// Create a copy of NetworkListPeersRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? nodeId = null,Object? includeIncoming = null,Object? includeOutgoing = null,Object? acceptedOnly = null,Object? limitResults = freezed,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: null == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,includeIncoming: null == includeIncoming ? _self.includeIncoming : includeIncoming // ignore: cast_nullable_to_non_nullable
as bool,includeOutgoing: null == includeOutgoing ? _self.includeOutgoing : includeOutgoing // ignore: cast_nullable_to_non_nullable
as bool,acceptedOnly: null == acceptedOnly ? _self.acceptedOnly : acceptedOnly // ignore: cast_nullable_to_non_nullable
as bool,limitResults: freezed == limitResults ? _self.limitResults : limitResults // ignore: cast_nullable_to_non_nullable
as int?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkListPeersRequest].
extension NetworkListPeersRequestPatterns on NetworkListPeersRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkListPeersRequest value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkListPeersRequest() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkListPeersRequest value)  def,}){
final _that = this;
switch (_that) {
case _NetworkListPeersRequest():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkListPeersRequest value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkListPeersRequest() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue nodeId,  bool includeIncoming,  bool includeOutgoing,  bool acceptedOnly,  int? limitResults)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkListPeersRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.nodeId,_that.includeIncoming,_that.includeOutgoing,_that.acceptedOnly,_that.limitResults);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue nodeId,  bool includeIncoming,  bool includeOutgoing,  bool acceptedOnly,  int? limitResults)  def,}) {final _that = this;
switch (_that) {
case _NetworkListPeersRequest():
return def(_that.actorId,_that.requestId,_that.nodeId,_that.includeIncoming,_that.includeOutgoing,_that.acceptedOnly,_that.limitResults);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue nodeId,  bool includeIncoming,  bool includeOutgoing,  bool acceptedOnly,  int? limitResults)?  def,}) {final _that = this;
switch (_that) {
case _NetworkListPeersRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.nodeId,_that.includeIncoming,_that.includeOutgoing,_that.acceptedOnly,_that.limitResults);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkListPeersRequest implements NetworkListPeersRequest {
   _NetworkListPeersRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.requestId, @UuidValueConverter() required this.nodeId, required this.includeIncoming, required this.includeOutgoing, required this.acceptedOnly, this.limitResults});
  factory _NetworkListPeersRequest.fromJson(Map<String, dynamic> json) => _$NetworkListPeersRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? requestId;
@override@UuidValueConverter() final  UuidValue nodeId;
@override final  bool includeIncoming;
@override final  bool includeOutgoing;
@override final  bool acceptedOnly;
@override final  int? limitResults;

/// Create a copy of NetworkListPeersRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkListPeersRequestCopyWith<_NetworkListPeersRequest> get copyWith => __$NetworkListPeersRequestCopyWithImpl<_NetworkListPeersRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkListPeersRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkListPeersRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.includeIncoming, includeIncoming) || other.includeIncoming == includeIncoming)&&(identical(other.includeOutgoing, includeOutgoing) || other.includeOutgoing == includeOutgoing)&&(identical(other.acceptedOnly, acceptedOnly) || other.acceptedOnly == acceptedOnly)&&(identical(other.limitResults, limitResults) || other.limitResults == limitResults));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,nodeId,includeIncoming,includeOutgoing,acceptedOnly,limitResults);

@override
String toString() {
  return 'NetworkListPeersRequest.def(actorId: $actorId, requestId: $requestId, nodeId: $nodeId, includeIncoming: $includeIncoming, includeOutgoing: $includeOutgoing, acceptedOnly: $acceptedOnly, limitResults: $limitResults)';
}


}

/// @nodoc
abstract mixin class _$NetworkListPeersRequestCopyWith<$Res> implements $NetworkListPeersRequestCopyWith<$Res> {
  factory _$NetworkListPeersRequestCopyWith(_NetworkListPeersRequest value, $Res Function(_NetworkListPeersRequest) _then) = __$NetworkListPeersRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue nodeId, bool includeIncoming, bool includeOutgoing, bool acceptedOnly, int? limitResults
});




}
/// @nodoc
class __$NetworkListPeersRequestCopyWithImpl<$Res>
    implements _$NetworkListPeersRequestCopyWith<$Res> {
  __$NetworkListPeersRequestCopyWithImpl(this._self, this._then);

  final _NetworkListPeersRequest _self;
  final $Res Function(_NetworkListPeersRequest) _then;

/// Create a copy of NetworkListPeersRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? nodeId = null,Object? includeIncoming = null,Object? includeOutgoing = null,Object? acceptedOnly = null,Object? limitResults = freezed,}) {
  return _then(_NetworkListPeersRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: null == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,includeIncoming: null == includeIncoming ? _self.includeIncoming : includeIncoming // ignore: cast_nullable_to_non_nullable
as bool,includeOutgoing: null == includeOutgoing ? _self.includeOutgoing : includeOutgoing // ignore: cast_nullable_to_non_nullable
as bool,acceptedOnly: null == acceptedOnly ? _self.acceptedOnly : acceptedOnly // ignore: cast_nullable_to_non_nullable
as bool,limitResults: freezed == limitResults ? _self.limitResults : limitResults // ignore: cast_nullable_to_non_nullable
as int?,
  ));
}


}


/// @nodoc
mixin _$NetworkListPeersResponse {

@UuidValueConverter() UuidValue? get requestId; bool get success; String? get error; List<NetworkPeerDescriptor> get peers;
/// Create a copy of NetworkListPeersResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkListPeersResponseCopyWith<NetworkListPeersResponse> get copyWith => _$NetworkListPeersResponseCopyWithImpl<NetworkListPeersResponse>(this as NetworkListPeersResponse, _$identity);

  /// Serializes this NetworkListPeersResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkListPeersResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other.peers, peers));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,const DeepCollectionEquality().hash(peers));

@override
String toString() {
  return 'NetworkListPeersResponse(requestId: $requestId, success: $success, error: $error, peers: $peers)';
}


}

/// @nodoc
abstract mixin class $NetworkListPeersResponseCopyWith<$Res>  {
  factory $NetworkListPeersResponseCopyWith(NetworkListPeersResponse value, $Res Function(NetworkListPeersResponse) _then) = _$NetworkListPeersResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, List<NetworkPeerDescriptor> peers
});




}
/// @nodoc
class _$NetworkListPeersResponseCopyWithImpl<$Res>
    implements $NetworkListPeersResponseCopyWith<$Res> {
  _$NetworkListPeersResponseCopyWithImpl(this._self, this._then);

  final NetworkListPeersResponse _self;
  final $Res Function(NetworkListPeersResponse) _then;

/// Create a copy of NetworkListPeersResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? peers = null,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,peers: null == peers ? _self.peers : peers // ignore: cast_nullable_to_non_nullable
as List<NetworkPeerDescriptor>,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkListPeersResponse].
extension NetworkListPeersResponsePatterns on NetworkListPeersResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkListPeersResponse value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkListPeersResponse() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkListPeersResponse value)  def,}){
final _that = this;
switch (_that) {
case _NetworkListPeersResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkListPeersResponse value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkListPeersResponse() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  List<NetworkPeerDescriptor> peers)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkListPeersResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.peers);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  List<NetworkPeerDescriptor> peers)  def,}) {final _that = this;
switch (_that) {
case _NetworkListPeersResponse():
return def(_that.requestId,_that.success,_that.error,_that.peers);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  List<NetworkPeerDescriptor> peers)?  def,}) {final _that = this;
switch (_that) {
case _NetworkListPeersResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.peers);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkListPeersResponse implements NetworkListPeersResponse {
   _NetworkListPeersResponse({@UuidValueConverter() this.requestId, required this.success, this.error, final  List<NetworkPeerDescriptor> peers = const []}): _peers = peers;
  factory _NetworkListPeersResponse.fromJson(Map<String, dynamic> json) => _$NetworkListPeersResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? error;
 final  List<NetworkPeerDescriptor> _peers;
@override@JsonKey() List<NetworkPeerDescriptor> get peers {
  if (_peers is EqualUnmodifiableListView) return _peers;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_peers);
}


/// Create a copy of NetworkListPeersResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkListPeersResponseCopyWith<_NetworkListPeersResponse> get copyWith => __$NetworkListPeersResponseCopyWithImpl<_NetworkListPeersResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkListPeersResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkListPeersResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other._peers, _peers));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,const DeepCollectionEquality().hash(_peers));

@override
String toString() {
  return 'NetworkListPeersResponse.def(requestId: $requestId, success: $success, error: $error, peers: $peers)';
}


}

/// @nodoc
abstract mixin class _$NetworkListPeersResponseCopyWith<$Res> implements $NetworkListPeersResponseCopyWith<$Res> {
  factory _$NetworkListPeersResponseCopyWith(_NetworkListPeersResponse value, $Res Function(_NetworkListPeersResponse) _then) = __$NetworkListPeersResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, List<NetworkPeerDescriptor> peers
});




}
/// @nodoc
class __$NetworkListPeersResponseCopyWithImpl<$Res>
    implements _$NetworkListPeersResponseCopyWith<$Res> {
  __$NetworkListPeersResponseCopyWithImpl(this._self, this._then);

  final _NetworkListPeersResponse _self;
  final $Res Function(_NetworkListPeersResponse) _then;

/// Create a copy of NetworkListPeersResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? peers = null,}) {
  return _then(_NetworkListPeersResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,peers: null == peers ? _self._peers : peers // ignore: cast_nullable_to_non_nullable
as List<NetworkPeerDescriptor>,
  ));
}


}


/// @nodoc
mixin _$NetworkPublishHostedServiceRequest {

@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue? get requestId;@UuidValueConverter() UuidValue get nodeId;@UuidValueConverter() UuidValue? get servicePackageId;@UuidValueConverter() UuidValue get serviceId; String get serviceName; List<String> get servicePackageNames; List<String> get endpointRefs; List<String> get streamEndpointRefs; String get hostId; String? get hostVersion; String get protocolVersion; bool get supportsStreamEvents;
/// Create a copy of NetworkPublishHostedServiceRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkPublishHostedServiceRequestCopyWith<NetworkPublishHostedServiceRequest> get copyWith => _$NetworkPublishHostedServiceRequestCopyWithImpl<NetworkPublishHostedServiceRequest>(this as NetworkPublishHostedServiceRequest, _$identity);

  /// Serializes this NetworkPublishHostedServiceRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkPublishHostedServiceRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.servicePackageId, servicePackageId) || other.servicePackageId == servicePackageId)&&(identical(other.serviceId, serviceId) || other.serviceId == serviceId)&&(identical(other.serviceName, serviceName) || other.serviceName == serviceName)&&const DeepCollectionEquality().equals(other.servicePackageNames, servicePackageNames)&&const DeepCollectionEquality().equals(other.endpointRefs, endpointRefs)&&const DeepCollectionEquality().equals(other.streamEndpointRefs, streamEndpointRefs)&&(identical(other.hostId, hostId) || other.hostId == hostId)&&(identical(other.hostVersion, hostVersion) || other.hostVersion == hostVersion)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.supportsStreamEvents, supportsStreamEvents) || other.supportsStreamEvents == supportsStreamEvents));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,nodeId,servicePackageId,serviceId,serviceName,const DeepCollectionEquality().hash(servicePackageNames),const DeepCollectionEquality().hash(endpointRefs),const DeepCollectionEquality().hash(streamEndpointRefs),hostId,hostVersion,protocolVersion,supportsStreamEvents);

@override
String toString() {
  return 'NetworkPublishHostedServiceRequest(actorId: $actorId, requestId: $requestId, nodeId: $nodeId, servicePackageId: $servicePackageId, serviceId: $serviceId, serviceName: $serviceName, servicePackageNames: $servicePackageNames, endpointRefs: $endpointRefs, streamEndpointRefs: $streamEndpointRefs, hostId: $hostId, hostVersion: $hostVersion, protocolVersion: $protocolVersion, supportsStreamEvents: $supportsStreamEvents)';
}


}

/// @nodoc
abstract mixin class $NetworkPublishHostedServiceRequestCopyWith<$Res>  {
  factory $NetworkPublishHostedServiceRequestCopyWith(NetworkPublishHostedServiceRequest value, $Res Function(NetworkPublishHostedServiceRequest) _then) = _$NetworkPublishHostedServiceRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue nodeId,@UuidValueConverter() UuidValue? servicePackageId,@UuidValueConverter() UuidValue serviceId, String serviceName, List<String> servicePackageNames, List<String> endpointRefs, List<String> streamEndpointRefs, String hostId, String? hostVersion, String protocolVersion, bool supportsStreamEvents
});




}
/// @nodoc
class _$NetworkPublishHostedServiceRequestCopyWithImpl<$Res>
    implements $NetworkPublishHostedServiceRequestCopyWith<$Res> {
  _$NetworkPublishHostedServiceRequestCopyWithImpl(this._self, this._then);

  final NetworkPublishHostedServiceRequest _self;
  final $Res Function(NetworkPublishHostedServiceRequest) _then;

/// Create a copy of NetworkPublishHostedServiceRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? nodeId = null,Object? servicePackageId = freezed,Object? serviceId = null,Object? serviceName = null,Object? servicePackageNames = null,Object? endpointRefs = null,Object? streamEndpointRefs = null,Object? hostId = null,Object? hostVersion = freezed,Object? protocolVersion = null,Object? supportsStreamEvents = null,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: null == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,servicePackageId: freezed == servicePackageId ? _self.servicePackageId : servicePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceId: null == serviceId ? _self.serviceId : serviceId // ignore: cast_nullable_to_non_nullable
as UuidValue,serviceName: null == serviceName ? _self.serviceName : serviceName // ignore: cast_nullable_to_non_nullable
as String,servicePackageNames: null == servicePackageNames ? _self.servicePackageNames : servicePackageNames // ignore: cast_nullable_to_non_nullable
as List<String>,endpointRefs: null == endpointRefs ? _self.endpointRefs : endpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,streamEndpointRefs: null == streamEndpointRefs ? _self.streamEndpointRefs : streamEndpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,hostId: null == hostId ? _self.hostId : hostId // ignore: cast_nullable_to_non_nullable
as String,hostVersion: freezed == hostVersion ? _self.hostVersion : hostVersion // ignore: cast_nullable_to_non_nullable
as String?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as String,supportsStreamEvents: null == supportsStreamEvents ? _self.supportsStreamEvents : supportsStreamEvents // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkPublishHostedServiceRequest].
extension NetworkPublishHostedServiceRequestPatterns on NetworkPublishHostedServiceRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkPublishHostedServiceRequest value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkPublishHostedServiceRequest() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkPublishHostedServiceRequest value)  def,}){
final _that = this;
switch (_that) {
case _NetworkPublishHostedServiceRequest():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkPublishHostedServiceRequest value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkPublishHostedServiceRequest() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue nodeId, @UuidValueConverter()  UuidValue? servicePackageId, @UuidValueConverter()  UuidValue serviceId,  String serviceName,  List<String> servicePackageNames,  List<String> endpointRefs,  List<String> streamEndpointRefs,  String hostId,  String? hostVersion,  String protocolVersion,  bool supportsStreamEvents)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkPublishHostedServiceRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.nodeId,_that.servicePackageId,_that.serviceId,_that.serviceName,_that.servicePackageNames,_that.endpointRefs,_that.streamEndpointRefs,_that.hostId,_that.hostVersion,_that.protocolVersion,_that.supportsStreamEvents);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue nodeId, @UuidValueConverter()  UuidValue? servicePackageId, @UuidValueConverter()  UuidValue serviceId,  String serviceName,  List<String> servicePackageNames,  List<String> endpointRefs,  List<String> streamEndpointRefs,  String hostId,  String? hostVersion,  String protocolVersion,  bool supportsStreamEvents)  def,}) {final _that = this;
switch (_that) {
case _NetworkPublishHostedServiceRequest():
return def(_that.actorId,_that.requestId,_that.nodeId,_that.servicePackageId,_that.serviceId,_that.serviceName,_that.servicePackageNames,_that.endpointRefs,_that.streamEndpointRefs,_that.hostId,_that.hostVersion,_that.protocolVersion,_that.supportsStreamEvents);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue nodeId, @UuidValueConverter()  UuidValue? servicePackageId, @UuidValueConverter()  UuidValue serviceId,  String serviceName,  List<String> servicePackageNames,  List<String> endpointRefs,  List<String> streamEndpointRefs,  String hostId,  String? hostVersion,  String protocolVersion,  bool supportsStreamEvents)?  def,}) {final _that = this;
switch (_that) {
case _NetworkPublishHostedServiceRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.nodeId,_that.servicePackageId,_that.serviceId,_that.serviceName,_that.servicePackageNames,_that.endpointRefs,_that.streamEndpointRefs,_that.hostId,_that.hostVersion,_that.protocolVersion,_that.supportsStreamEvents);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkPublishHostedServiceRequest implements NetworkPublishHostedServiceRequest {
   _NetworkPublishHostedServiceRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.requestId, @UuidValueConverter() required this.nodeId, @UuidValueConverter() this.servicePackageId, @UuidValueConverter() required this.serviceId, required this.serviceName, final  List<String> servicePackageNames = const [], final  List<String> endpointRefs = const [], final  List<String> streamEndpointRefs = const [], required this.hostId, this.hostVersion, required this.protocolVersion, required this.supportsStreamEvents}): _servicePackageNames = servicePackageNames,_endpointRefs = endpointRefs,_streamEndpointRefs = streamEndpointRefs;
  factory _NetworkPublishHostedServiceRequest.fromJson(Map<String, dynamic> json) => _$NetworkPublishHostedServiceRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? requestId;
@override@UuidValueConverter() final  UuidValue nodeId;
@override@UuidValueConverter() final  UuidValue? servicePackageId;
@override@UuidValueConverter() final  UuidValue serviceId;
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

 final  List<String> _streamEndpointRefs;
@override@JsonKey() List<String> get streamEndpointRefs {
  if (_streamEndpointRefs is EqualUnmodifiableListView) return _streamEndpointRefs;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_streamEndpointRefs);
}

@override final  String hostId;
@override final  String? hostVersion;
@override final  String protocolVersion;
@override final  bool supportsStreamEvents;

/// Create a copy of NetworkPublishHostedServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkPublishHostedServiceRequestCopyWith<_NetworkPublishHostedServiceRequest> get copyWith => __$NetworkPublishHostedServiceRequestCopyWithImpl<_NetworkPublishHostedServiceRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkPublishHostedServiceRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkPublishHostedServiceRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.servicePackageId, servicePackageId) || other.servicePackageId == servicePackageId)&&(identical(other.serviceId, serviceId) || other.serviceId == serviceId)&&(identical(other.serviceName, serviceName) || other.serviceName == serviceName)&&const DeepCollectionEquality().equals(other._servicePackageNames, _servicePackageNames)&&const DeepCollectionEquality().equals(other._endpointRefs, _endpointRefs)&&const DeepCollectionEquality().equals(other._streamEndpointRefs, _streamEndpointRefs)&&(identical(other.hostId, hostId) || other.hostId == hostId)&&(identical(other.hostVersion, hostVersion) || other.hostVersion == hostVersion)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.supportsStreamEvents, supportsStreamEvents) || other.supportsStreamEvents == supportsStreamEvents));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,nodeId,servicePackageId,serviceId,serviceName,const DeepCollectionEquality().hash(_servicePackageNames),const DeepCollectionEquality().hash(_endpointRefs),const DeepCollectionEquality().hash(_streamEndpointRefs),hostId,hostVersion,protocolVersion,supportsStreamEvents);

@override
String toString() {
  return 'NetworkPublishHostedServiceRequest.def(actorId: $actorId, requestId: $requestId, nodeId: $nodeId, servicePackageId: $servicePackageId, serviceId: $serviceId, serviceName: $serviceName, servicePackageNames: $servicePackageNames, endpointRefs: $endpointRefs, streamEndpointRefs: $streamEndpointRefs, hostId: $hostId, hostVersion: $hostVersion, protocolVersion: $protocolVersion, supportsStreamEvents: $supportsStreamEvents)';
}


}

/// @nodoc
abstract mixin class _$NetworkPublishHostedServiceRequestCopyWith<$Res> implements $NetworkPublishHostedServiceRequestCopyWith<$Res> {
  factory _$NetworkPublishHostedServiceRequestCopyWith(_NetworkPublishHostedServiceRequest value, $Res Function(_NetworkPublishHostedServiceRequest) _then) = __$NetworkPublishHostedServiceRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue nodeId,@UuidValueConverter() UuidValue? servicePackageId,@UuidValueConverter() UuidValue serviceId, String serviceName, List<String> servicePackageNames, List<String> endpointRefs, List<String> streamEndpointRefs, String hostId, String? hostVersion, String protocolVersion, bool supportsStreamEvents
});




}
/// @nodoc
class __$NetworkPublishHostedServiceRequestCopyWithImpl<$Res>
    implements _$NetworkPublishHostedServiceRequestCopyWith<$Res> {
  __$NetworkPublishHostedServiceRequestCopyWithImpl(this._self, this._then);

  final _NetworkPublishHostedServiceRequest _self;
  final $Res Function(_NetworkPublishHostedServiceRequest) _then;

/// Create a copy of NetworkPublishHostedServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? nodeId = null,Object? servicePackageId = freezed,Object? serviceId = null,Object? serviceName = null,Object? servicePackageNames = null,Object? endpointRefs = null,Object? streamEndpointRefs = null,Object? hostId = null,Object? hostVersion = freezed,Object? protocolVersion = null,Object? supportsStreamEvents = null,}) {
  return _then(_NetworkPublishHostedServiceRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: null == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,servicePackageId: freezed == servicePackageId ? _self.servicePackageId : servicePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceId: null == serviceId ? _self.serviceId : serviceId // ignore: cast_nullable_to_non_nullable
as UuidValue,serviceName: null == serviceName ? _self.serviceName : serviceName // ignore: cast_nullable_to_non_nullable
as String,servicePackageNames: null == servicePackageNames ? _self._servicePackageNames : servicePackageNames // ignore: cast_nullable_to_non_nullable
as List<String>,endpointRefs: null == endpointRefs ? _self._endpointRefs : endpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,streamEndpointRefs: null == streamEndpointRefs ? _self._streamEndpointRefs : streamEndpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,hostId: null == hostId ? _self.hostId : hostId // ignore: cast_nullable_to_non_nullable
as String,hostVersion: freezed == hostVersion ? _self.hostVersion : hostVersion // ignore: cast_nullable_to_non_nullable
as String?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as String,supportsStreamEvents: null == supportsStreamEvents ? _self.supportsStreamEvents : supportsStreamEvents // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}


}


/// @nodoc
mixin _$NetworkPublishHostedServiceResponse {

@UuidValueConverter() UuidValue? get requestId; bool get success; String? get error; NetworkHostedServiceDescriptor? get hostedService;
/// Create a copy of NetworkPublishHostedServiceResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkPublishHostedServiceResponseCopyWith<NetworkPublishHostedServiceResponse> get copyWith => _$NetworkPublishHostedServiceResponseCopyWithImpl<NetworkPublishHostedServiceResponse>(this as NetworkPublishHostedServiceResponse, _$identity);

  /// Serializes this NetworkPublishHostedServiceResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkPublishHostedServiceResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.hostedService, hostedService) || other.hostedService == hostedService));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,hostedService);

@override
String toString() {
  return 'NetworkPublishHostedServiceResponse(requestId: $requestId, success: $success, error: $error, hostedService: $hostedService)';
}


}

/// @nodoc
abstract mixin class $NetworkPublishHostedServiceResponseCopyWith<$Res>  {
  factory $NetworkPublishHostedServiceResponseCopyWith(NetworkPublishHostedServiceResponse value, $Res Function(NetworkPublishHostedServiceResponse) _then) = _$NetworkPublishHostedServiceResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, NetworkHostedServiceDescriptor? hostedService
});


$NetworkHostedServiceDescriptorCopyWith<$Res>? get hostedService;

}
/// @nodoc
class _$NetworkPublishHostedServiceResponseCopyWithImpl<$Res>
    implements $NetworkPublishHostedServiceResponseCopyWith<$Res> {
  _$NetworkPublishHostedServiceResponseCopyWithImpl(this._self, this._then);

  final NetworkPublishHostedServiceResponse _self;
  final $Res Function(NetworkPublishHostedServiceResponse) _then;

/// Create a copy of NetworkPublishHostedServiceResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? hostedService = freezed,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,hostedService: freezed == hostedService ? _self.hostedService : hostedService // ignore: cast_nullable_to_non_nullable
as NetworkHostedServiceDescriptor?,
  ));
}
/// Create a copy of NetworkPublishHostedServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkHostedServiceDescriptorCopyWith<$Res>? get hostedService {
    if (_self.hostedService == null) {
    return null;
  }

  return $NetworkHostedServiceDescriptorCopyWith<$Res>(_self.hostedService!, (value) {
    return _then(_self.copyWith(hostedService: value));
  });
}
}


/// Adds pattern-matching-related methods to [NetworkPublishHostedServiceResponse].
extension NetworkPublishHostedServiceResponsePatterns on NetworkPublishHostedServiceResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkPublishHostedServiceResponse value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkPublishHostedServiceResponse() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkPublishHostedServiceResponse value)  def,}){
final _that = this;
switch (_that) {
case _NetworkPublishHostedServiceResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkPublishHostedServiceResponse value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkPublishHostedServiceResponse() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  NetworkHostedServiceDescriptor? hostedService)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkPublishHostedServiceResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.hostedService);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  NetworkHostedServiceDescriptor? hostedService)  def,}) {final _that = this;
switch (_that) {
case _NetworkPublishHostedServiceResponse():
return def(_that.requestId,_that.success,_that.error,_that.hostedService);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  NetworkHostedServiceDescriptor? hostedService)?  def,}) {final _that = this;
switch (_that) {
case _NetworkPublishHostedServiceResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.hostedService);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkPublishHostedServiceResponse implements NetworkPublishHostedServiceResponse {
   _NetworkPublishHostedServiceResponse({@UuidValueConverter() this.requestId, required this.success, this.error, this.hostedService});
  factory _NetworkPublishHostedServiceResponse.fromJson(Map<String, dynamic> json) => _$NetworkPublishHostedServiceResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? error;
@override final  NetworkHostedServiceDescriptor? hostedService;

/// Create a copy of NetworkPublishHostedServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkPublishHostedServiceResponseCopyWith<_NetworkPublishHostedServiceResponse> get copyWith => __$NetworkPublishHostedServiceResponseCopyWithImpl<_NetworkPublishHostedServiceResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkPublishHostedServiceResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkPublishHostedServiceResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.hostedService, hostedService) || other.hostedService == hostedService));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,hostedService);

@override
String toString() {
  return 'NetworkPublishHostedServiceResponse.def(requestId: $requestId, success: $success, error: $error, hostedService: $hostedService)';
}


}

/// @nodoc
abstract mixin class _$NetworkPublishHostedServiceResponseCopyWith<$Res> implements $NetworkPublishHostedServiceResponseCopyWith<$Res> {
  factory _$NetworkPublishHostedServiceResponseCopyWith(_NetworkPublishHostedServiceResponse value, $Res Function(_NetworkPublishHostedServiceResponse) _then) = __$NetworkPublishHostedServiceResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, NetworkHostedServiceDescriptor? hostedService
});


@override $NetworkHostedServiceDescriptorCopyWith<$Res>? get hostedService;

}
/// @nodoc
class __$NetworkPublishHostedServiceResponseCopyWithImpl<$Res>
    implements _$NetworkPublishHostedServiceResponseCopyWith<$Res> {
  __$NetworkPublishHostedServiceResponseCopyWithImpl(this._self, this._then);

  final _NetworkPublishHostedServiceResponse _self;
  final $Res Function(_NetworkPublishHostedServiceResponse) _then;

/// Create a copy of NetworkPublishHostedServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? hostedService = freezed,}) {
  return _then(_NetworkPublishHostedServiceResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,hostedService: freezed == hostedService ? _self.hostedService : hostedService // ignore: cast_nullable_to_non_nullable
as NetworkHostedServiceDescriptor?,
  ));
}

/// Create a copy of NetworkPublishHostedServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkHostedServiceDescriptorCopyWith<$Res>? get hostedService {
    if (_self.hostedService == null) {
    return null;
  }

  return $NetworkHostedServiceDescriptorCopyWith<$Res>(_self.hostedService!, (value) {
    return _then(_self.copyWith(hostedService: value));
  });
}
}


/// @nodoc
mixin _$NetworkListHostedServicesRequest {

@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue? get requestId;@UuidValueConverter() UuidValue get nodeId;
/// Create a copy of NetworkListHostedServicesRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkListHostedServicesRequestCopyWith<NetworkListHostedServicesRequest> get copyWith => _$NetworkListHostedServicesRequestCopyWithImpl<NetworkListHostedServicesRequest>(this as NetworkListHostedServicesRequest, _$identity);

  /// Serializes this NetworkListHostedServicesRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkListHostedServicesRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,nodeId);

@override
String toString() {
  return 'NetworkListHostedServicesRequest(actorId: $actorId, requestId: $requestId, nodeId: $nodeId)';
}


}

/// @nodoc
abstract mixin class $NetworkListHostedServicesRequestCopyWith<$Res>  {
  factory $NetworkListHostedServicesRequestCopyWith(NetworkListHostedServicesRequest value, $Res Function(NetworkListHostedServicesRequest) _then) = _$NetworkListHostedServicesRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue nodeId
});




}
/// @nodoc
class _$NetworkListHostedServicesRequestCopyWithImpl<$Res>
    implements $NetworkListHostedServicesRequestCopyWith<$Res> {
  _$NetworkListHostedServicesRequestCopyWithImpl(this._self, this._then);

  final NetworkListHostedServicesRequest _self;
  final $Res Function(NetworkListHostedServicesRequest) _then;

/// Create a copy of NetworkListHostedServicesRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? nodeId = null,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: null == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkListHostedServicesRequest].
extension NetworkListHostedServicesRequestPatterns on NetworkListHostedServicesRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkListHostedServicesRequest value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkListHostedServicesRequest() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkListHostedServicesRequest value)  def,}){
final _that = this;
switch (_that) {
case _NetworkListHostedServicesRequest():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkListHostedServicesRequest value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkListHostedServicesRequest() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue nodeId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkListHostedServicesRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.nodeId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue nodeId)  def,}) {final _that = this;
switch (_that) {
case _NetworkListHostedServicesRequest():
return def(_that.actorId,_that.requestId,_that.nodeId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue nodeId)?  def,}) {final _that = this;
switch (_that) {
case _NetworkListHostedServicesRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.nodeId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkListHostedServicesRequest implements NetworkListHostedServicesRequest {
   _NetworkListHostedServicesRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.requestId, @UuidValueConverter() required this.nodeId});
  factory _NetworkListHostedServicesRequest.fromJson(Map<String, dynamic> json) => _$NetworkListHostedServicesRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? requestId;
@override@UuidValueConverter() final  UuidValue nodeId;

/// Create a copy of NetworkListHostedServicesRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkListHostedServicesRequestCopyWith<_NetworkListHostedServicesRequest> get copyWith => __$NetworkListHostedServicesRequestCopyWithImpl<_NetworkListHostedServicesRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkListHostedServicesRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkListHostedServicesRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,nodeId);

@override
String toString() {
  return 'NetworkListHostedServicesRequest.def(actorId: $actorId, requestId: $requestId, nodeId: $nodeId)';
}


}

/// @nodoc
abstract mixin class _$NetworkListHostedServicesRequestCopyWith<$Res> implements $NetworkListHostedServicesRequestCopyWith<$Res> {
  factory _$NetworkListHostedServicesRequestCopyWith(_NetworkListHostedServicesRequest value, $Res Function(_NetworkListHostedServicesRequest) _then) = __$NetworkListHostedServicesRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue nodeId
});




}
/// @nodoc
class __$NetworkListHostedServicesRequestCopyWithImpl<$Res>
    implements _$NetworkListHostedServicesRequestCopyWith<$Res> {
  __$NetworkListHostedServicesRequestCopyWithImpl(this._self, this._then);

  final _NetworkListHostedServicesRequest _self;
  final $Res Function(_NetworkListHostedServicesRequest) _then;

/// Create a copy of NetworkListHostedServicesRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? nodeId = null,}) {
  return _then(_NetworkListHostedServicesRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: null == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,
  ));
}


}


/// @nodoc
mixin _$NetworkListHostedServicesResponse {

@UuidValueConverter() UuidValue? get requestId; bool get success; String? get error; List<NetworkHostedServiceDescriptor> get hostedServices;
/// Create a copy of NetworkListHostedServicesResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkListHostedServicesResponseCopyWith<NetworkListHostedServicesResponse> get copyWith => _$NetworkListHostedServicesResponseCopyWithImpl<NetworkListHostedServicesResponse>(this as NetworkListHostedServicesResponse, _$identity);

  /// Serializes this NetworkListHostedServicesResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkListHostedServicesResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other.hostedServices, hostedServices));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,const DeepCollectionEquality().hash(hostedServices));

@override
String toString() {
  return 'NetworkListHostedServicesResponse(requestId: $requestId, success: $success, error: $error, hostedServices: $hostedServices)';
}


}

/// @nodoc
abstract mixin class $NetworkListHostedServicesResponseCopyWith<$Res>  {
  factory $NetworkListHostedServicesResponseCopyWith(NetworkListHostedServicesResponse value, $Res Function(NetworkListHostedServicesResponse) _then) = _$NetworkListHostedServicesResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, List<NetworkHostedServiceDescriptor> hostedServices
});




}
/// @nodoc
class _$NetworkListHostedServicesResponseCopyWithImpl<$Res>
    implements $NetworkListHostedServicesResponseCopyWith<$Res> {
  _$NetworkListHostedServicesResponseCopyWithImpl(this._self, this._then);

  final NetworkListHostedServicesResponse _self;
  final $Res Function(NetworkListHostedServicesResponse) _then;

/// Create a copy of NetworkListHostedServicesResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? hostedServices = null,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,hostedServices: null == hostedServices ? _self.hostedServices : hostedServices // ignore: cast_nullable_to_non_nullable
as List<NetworkHostedServiceDescriptor>,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkListHostedServicesResponse].
extension NetworkListHostedServicesResponsePatterns on NetworkListHostedServicesResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkListHostedServicesResponse value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkListHostedServicesResponse() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkListHostedServicesResponse value)  def,}){
final _that = this;
switch (_that) {
case _NetworkListHostedServicesResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkListHostedServicesResponse value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkListHostedServicesResponse() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  List<NetworkHostedServiceDescriptor> hostedServices)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkListHostedServicesResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.hostedServices);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  List<NetworkHostedServiceDescriptor> hostedServices)  def,}) {final _that = this;
switch (_that) {
case _NetworkListHostedServicesResponse():
return def(_that.requestId,_that.success,_that.error,_that.hostedServices);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  List<NetworkHostedServiceDescriptor> hostedServices)?  def,}) {final _that = this;
switch (_that) {
case _NetworkListHostedServicesResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.hostedServices);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkListHostedServicesResponse implements NetworkListHostedServicesResponse {
   _NetworkListHostedServicesResponse({@UuidValueConverter() this.requestId, required this.success, this.error, final  List<NetworkHostedServiceDescriptor> hostedServices = const []}): _hostedServices = hostedServices;
  factory _NetworkListHostedServicesResponse.fromJson(Map<String, dynamic> json) => _$NetworkListHostedServicesResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? error;
 final  List<NetworkHostedServiceDescriptor> _hostedServices;
@override@JsonKey() List<NetworkHostedServiceDescriptor> get hostedServices {
  if (_hostedServices is EqualUnmodifiableListView) return _hostedServices;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_hostedServices);
}


/// Create a copy of NetworkListHostedServicesResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkListHostedServicesResponseCopyWith<_NetworkListHostedServicesResponse> get copyWith => __$NetworkListHostedServicesResponseCopyWithImpl<_NetworkListHostedServicesResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkListHostedServicesResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkListHostedServicesResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other._hostedServices, _hostedServices));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,const DeepCollectionEquality().hash(_hostedServices));

@override
String toString() {
  return 'NetworkListHostedServicesResponse.def(requestId: $requestId, success: $success, error: $error, hostedServices: $hostedServices)';
}


}

/// @nodoc
abstract mixin class _$NetworkListHostedServicesResponseCopyWith<$Res> implements $NetworkListHostedServicesResponseCopyWith<$Res> {
  factory _$NetworkListHostedServicesResponseCopyWith(_NetworkListHostedServicesResponse value, $Res Function(_NetworkListHostedServicesResponse) _then) = __$NetworkListHostedServicesResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, List<NetworkHostedServiceDescriptor> hostedServices
});




}
/// @nodoc
class __$NetworkListHostedServicesResponseCopyWithImpl<$Res>
    implements _$NetworkListHostedServicesResponseCopyWith<$Res> {
  __$NetworkListHostedServicesResponseCopyWithImpl(this._self, this._then);

  final _NetworkListHostedServicesResponse _self;
  final $Res Function(_NetworkListHostedServicesResponse) _then;

/// Create a copy of NetworkListHostedServicesResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? hostedServices = null,}) {
  return _then(_NetworkListHostedServicesResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,hostedServices: null == hostedServices ? _self._hostedServices : hostedServices // ignore: cast_nullable_to_non_nullable
as List<NetworkHostedServiceDescriptor>,
  ));
}


}


/// @nodoc
mixin _$NetworkPublishEnvironmentRequest {

@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue? get requestId;@UuidValueConverter() UuidValue get nodeId;@UuidValueConverter() UuidValue get environmentId; String? get environmentKey; String? get environmentTitle; String get role; bool get isActive; int get priority; String get status; List<String> get experienceNames;@UuidValueConverter() UuidValue? get environmentConfigId; String? get environmentConfigKey;
/// Create a copy of NetworkPublishEnvironmentRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkPublishEnvironmentRequestCopyWith<NetworkPublishEnvironmentRequest> get copyWith => _$NetworkPublishEnvironmentRequestCopyWithImpl<NetworkPublishEnvironmentRequest>(this as NetworkPublishEnvironmentRequest, _$identity);

  /// Serializes this NetworkPublishEnvironmentRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkPublishEnvironmentRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentKey, environmentKey) || other.environmentKey == environmentKey)&&(identical(other.environmentTitle, environmentTitle) || other.environmentTitle == environmentTitle)&&(identical(other.role, role) || other.role == role)&&(identical(other.isActive, isActive) || other.isActive == isActive)&&(identical(other.priority, priority) || other.priority == priority)&&(identical(other.status, status) || other.status == status)&&const DeepCollectionEquality().equals(other.experienceNames, experienceNames)&&(identical(other.environmentConfigId, environmentConfigId) || other.environmentConfigId == environmentConfigId)&&(identical(other.environmentConfigKey, environmentConfigKey) || other.environmentConfigKey == environmentConfigKey));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,nodeId,environmentId,environmentKey,environmentTitle,role,isActive,priority,status,const DeepCollectionEquality().hash(experienceNames),environmentConfigId,environmentConfigKey);

@override
String toString() {
  return 'NetworkPublishEnvironmentRequest(actorId: $actorId, requestId: $requestId, nodeId: $nodeId, environmentId: $environmentId, environmentKey: $environmentKey, environmentTitle: $environmentTitle, role: $role, isActive: $isActive, priority: $priority, status: $status, experienceNames: $experienceNames, environmentConfigId: $environmentConfigId, environmentConfigKey: $environmentConfigKey)';
}


}

/// @nodoc
abstract mixin class $NetworkPublishEnvironmentRequestCopyWith<$Res>  {
  factory $NetworkPublishEnvironmentRequestCopyWith(NetworkPublishEnvironmentRequest value, $Res Function(NetworkPublishEnvironmentRequest) _then) = _$NetworkPublishEnvironmentRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue nodeId,@UuidValueConverter() UuidValue environmentId, String? environmentKey, String? environmentTitle, String role, bool isActive, int priority, String status, List<String> experienceNames,@UuidValueConverter() UuidValue? environmentConfigId, String? environmentConfigKey
});




}
/// @nodoc
class _$NetworkPublishEnvironmentRequestCopyWithImpl<$Res>
    implements $NetworkPublishEnvironmentRequestCopyWith<$Res> {
  _$NetworkPublishEnvironmentRequestCopyWithImpl(this._self, this._then);

  final NetworkPublishEnvironmentRequest _self;
  final $Res Function(NetworkPublishEnvironmentRequest) _then;

/// Create a copy of NetworkPublishEnvironmentRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? nodeId = null,Object? environmentId = null,Object? environmentKey = freezed,Object? environmentTitle = freezed,Object? role = null,Object? isActive = null,Object? priority = null,Object? status = null,Object? experienceNames = null,Object? environmentConfigId = freezed,Object? environmentConfigKey = freezed,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: null == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentId: null == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentKey: freezed == environmentKey ? _self.environmentKey : environmentKey // ignore: cast_nullable_to_non_nullable
as String?,environmentTitle: freezed == environmentTitle ? _self.environmentTitle : environmentTitle // ignore: cast_nullable_to_non_nullable
as String?,role: null == role ? _self.role : role // ignore: cast_nullable_to_non_nullable
as String,isActive: null == isActive ? _self.isActive : isActive // ignore: cast_nullable_to_non_nullable
as bool,priority: null == priority ? _self.priority : priority // ignore: cast_nullable_to_non_nullable
as int,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,experienceNames: null == experienceNames ? _self.experienceNames : experienceNames // ignore: cast_nullable_to_non_nullable
as List<String>,environmentConfigId: freezed == environmentConfigId ? _self.environmentConfigId : environmentConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentConfigKey: freezed == environmentConfigKey ? _self.environmentConfigKey : environmentConfigKey // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkPublishEnvironmentRequest].
extension NetworkPublishEnvironmentRequestPatterns on NetworkPublishEnvironmentRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkPublishEnvironmentRequest value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkPublishEnvironmentRequest() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkPublishEnvironmentRequest value)  def,}){
final _that = this;
switch (_that) {
case _NetworkPublishEnvironmentRequest():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkPublishEnvironmentRequest value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkPublishEnvironmentRequest() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue nodeId, @UuidValueConverter()  UuidValue environmentId,  String? environmentKey,  String? environmentTitle,  String role,  bool isActive,  int priority,  String status,  List<String> experienceNames, @UuidValueConverter()  UuidValue? environmentConfigId,  String? environmentConfigKey)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkPublishEnvironmentRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.nodeId,_that.environmentId,_that.environmentKey,_that.environmentTitle,_that.role,_that.isActive,_that.priority,_that.status,_that.experienceNames,_that.environmentConfigId,_that.environmentConfigKey);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue nodeId, @UuidValueConverter()  UuidValue environmentId,  String? environmentKey,  String? environmentTitle,  String role,  bool isActive,  int priority,  String status,  List<String> experienceNames, @UuidValueConverter()  UuidValue? environmentConfigId,  String? environmentConfigKey)  def,}) {final _that = this;
switch (_that) {
case _NetworkPublishEnvironmentRequest():
return def(_that.actorId,_that.requestId,_that.nodeId,_that.environmentId,_that.environmentKey,_that.environmentTitle,_that.role,_that.isActive,_that.priority,_that.status,_that.experienceNames,_that.environmentConfigId,_that.environmentConfigKey);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue nodeId, @UuidValueConverter()  UuidValue environmentId,  String? environmentKey,  String? environmentTitle,  String role,  bool isActive,  int priority,  String status,  List<String> experienceNames, @UuidValueConverter()  UuidValue? environmentConfigId,  String? environmentConfigKey)?  def,}) {final _that = this;
switch (_that) {
case _NetworkPublishEnvironmentRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.nodeId,_that.environmentId,_that.environmentKey,_that.environmentTitle,_that.role,_that.isActive,_that.priority,_that.status,_that.experienceNames,_that.environmentConfigId,_that.environmentConfigKey);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkPublishEnvironmentRequest implements NetworkPublishEnvironmentRequest {
   _NetworkPublishEnvironmentRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.requestId, @UuidValueConverter() required this.nodeId, @UuidValueConverter() required this.environmentId, this.environmentKey, this.environmentTitle, required this.role, required this.isActive, required this.priority, required this.status, final  List<String> experienceNames = const [], @UuidValueConverter() this.environmentConfigId, this.environmentConfigKey}): _experienceNames = experienceNames;
  factory _NetworkPublishEnvironmentRequest.fromJson(Map<String, dynamic> json) => _$NetworkPublishEnvironmentRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? requestId;
@override@UuidValueConverter() final  UuidValue nodeId;
@override@UuidValueConverter() final  UuidValue environmentId;
@override final  String? environmentKey;
@override final  String? environmentTitle;
@override final  String role;
@override final  bool isActive;
@override final  int priority;
@override final  String status;
 final  List<String> _experienceNames;
@override@JsonKey() List<String> get experienceNames {
  if (_experienceNames is EqualUnmodifiableListView) return _experienceNames;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_experienceNames);
}

@override@UuidValueConverter() final  UuidValue? environmentConfigId;
@override final  String? environmentConfigKey;

/// Create a copy of NetworkPublishEnvironmentRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkPublishEnvironmentRequestCopyWith<_NetworkPublishEnvironmentRequest> get copyWith => __$NetworkPublishEnvironmentRequestCopyWithImpl<_NetworkPublishEnvironmentRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkPublishEnvironmentRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkPublishEnvironmentRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentKey, environmentKey) || other.environmentKey == environmentKey)&&(identical(other.environmentTitle, environmentTitle) || other.environmentTitle == environmentTitle)&&(identical(other.role, role) || other.role == role)&&(identical(other.isActive, isActive) || other.isActive == isActive)&&(identical(other.priority, priority) || other.priority == priority)&&(identical(other.status, status) || other.status == status)&&const DeepCollectionEquality().equals(other._experienceNames, _experienceNames)&&(identical(other.environmentConfigId, environmentConfigId) || other.environmentConfigId == environmentConfigId)&&(identical(other.environmentConfigKey, environmentConfigKey) || other.environmentConfigKey == environmentConfigKey));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,nodeId,environmentId,environmentKey,environmentTitle,role,isActive,priority,status,const DeepCollectionEquality().hash(_experienceNames),environmentConfigId,environmentConfigKey);

@override
String toString() {
  return 'NetworkPublishEnvironmentRequest.def(actorId: $actorId, requestId: $requestId, nodeId: $nodeId, environmentId: $environmentId, environmentKey: $environmentKey, environmentTitle: $environmentTitle, role: $role, isActive: $isActive, priority: $priority, status: $status, experienceNames: $experienceNames, environmentConfigId: $environmentConfigId, environmentConfigKey: $environmentConfigKey)';
}


}

/// @nodoc
abstract mixin class _$NetworkPublishEnvironmentRequestCopyWith<$Res> implements $NetworkPublishEnvironmentRequestCopyWith<$Res> {
  factory _$NetworkPublishEnvironmentRequestCopyWith(_NetworkPublishEnvironmentRequest value, $Res Function(_NetworkPublishEnvironmentRequest) _then) = __$NetworkPublishEnvironmentRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue nodeId,@UuidValueConverter() UuidValue environmentId, String? environmentKey, String? environmentTitle, String role, bool isActive, int priority, String status, List<String> experienceNames,@UuidValueConverter() UuidValue? environmentConfigId, String? environmentConfigKey
});




}
/// @nodoc
class __$NetworkPublishEnvironmentRequestCopyWithImpl<$Res>
    implements _$NetworkPublishEnvironmentRequestCopyWith<$Res> {
  __$NetworkPublishEnvironmentRequestCopyWithImpl(this._self, this._then);

  final _NetworkPublishEnvironmentRequest _self;
  final $Res Function(_NetworkPublishEnvironmentRequest) _then;

/// Create a copy of NetworkPublishEnvironmentRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? nodeId = null,Object? environmentId = null,Object? environmentKey = freezed,Object? environmentTitle = freezed,Object? role = null,Object? isActive = null,Object? priority = null,Object? status = null,Object? experienceNames = null,Object? environmentConfigId = freezed,Object? environmentConfigKey = freezed,}) {
  return _then(_NetworkPublishEnvironmentRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: null == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentId: null == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentKey: freezed == environmentKey ? _self.environmentKey : environmentKey // ignore: cast_nullable_to_non_nullable
as String?,environmentTitle: freezed == environmentTitle ? _self.environmentTitle : environmentTitle // ignore: cast_nullable_to_non_nullable
as String?,role: null == role ? _self.role : role // ignore: cast_nullable_to_non_nullable
as String,isActive: null == isActive ? _self.isActive : isActive // ignore: cast_nullable_to_non_nullable
as bool,priority: null == priority ? _self.priority : priority // ignore: cast_nullable_to_non_nullable
as int,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,experienceNames: null == experienceNames ? _self._experienceNames : experienceNames // ignore: cast_nullable_to_non_nullable
as List<String>,environmentConfigId: freezed == environmentConfigId ? _self.environmentConfigId : environmentConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentConfigKey: freezed == environmentConfigKey ? _self.environmentConfigKey : environmentConfigKey // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$NetworkPublishEnvironmentResponse {

@UuidValueConverter() UuidValue? get requestId; bool get success; String? get error; NetworkEnvironmentDescriptor? get environment;
/// Create a copy of NetworkPublishEnvironmentResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkPublishEnvironmentResponseCopyWith<NetworkPublishEnvironmentResponse> get copyWith => _$NetworkPublishEnvironmentResponseCopyWithImpl<NetworkPublishEnvironmentResponse>(this as NetworkPublishEnvironmentResponse, _$identity);

  /// Serializes this NetworkPublishEnvironmentResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkPublishEnvironmentResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.environment, environment) || other.environment == environment));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,environment);

@override
String toString() {
  return 'NetworkPublishEnvironmentResponse(requestId: $requestId, success: $success, error: $error, environment: $environment)';
}


}

/// @nodoc
abstract mixin class $NetworkPublishEnvironmentResponseCopyWith<$Res>  {
  factory $NetworkPublishEnvironmentResponseCopyWith(NetworkPublishEnvironmentResponse value, $Res Function(NetworkPublishEnvironmentResponse) _then) = _$NetworkPublishEnvironmentResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, NetworkEnvironmentDescriptor? environment
});


$NetworkEnvironmentDescriptorCopyWith<$Res>? get environment;

}
/// @nodoc
class _$NetworkPublishEnvironmentResponseCopyWithImpl<$Res>
    implements $NetworkPublishEnvironmentResponseCopyWith<$Res> {
  _$NetworkPublishEnvironmentResponseCopyWithImpl(this._self, this._then);

  final NetworkPublishEnvironmentResponse _self;
  final $Res Function(NetworkPublishEnvironmentResponse) _then;

/// Create a copy of NetworkPublishEnvironmentResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? environment = freezed,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,environment: freezed == environment ? _self.environment : environment // ignore: cast_nullable_to_non_nullable
as NetworkEnvironmentDescriptor?,
  ));
}
/// Create a copy of NetworkPublishEnvironmentResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkEnvironmentDescriptorCopyWith<$Res>? get environment {
    if (_self.environment == null) {
    return null;
  }

  return $NetworkEnvironmentDescriptorCopyWith<$Res>(_self.environment!, (value) {
    return _then(_self.copyWith(environment: value));
  });
}
}


/// Adds pattern-matching-related methods to [NetworkPublishEnvironmentResponse].
extension NetworkPublishEnvironmentResponsePatterns on NetworkPublishEnvironmentResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkPublishEnvironmentResponse value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkPublishEnvironmentResponse() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkPublishEnvironmentResponse value)  def,}){
final _that = this;
switch (_that) {
case _NetworkPublishEnvironmentResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkPublishEnvironmentResponse value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkPublishEnvironmentResponse() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  NetworkEnvironmentDescriptor? environment)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkPublishEnvironmentResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.environment);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  NetworkEnvironmentDescriptor? environment)  def,}) {final _that = this;
switch (_that) {
case _NetworkPublishEnvironmentResponse():
return def(_that.requestId,_that.success,_that.error,_that.environment);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  NetworkEnvironmentDescriptor? environment)?  def,}) {final _that = this;
switch (_that) {
case _NetworkPublishEnvironmentResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.environment);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkPublishEnvironmentResponse implements NetworkPublishEnvironmentResponse {
   _NetworkPublishEnvironmentResponse({@UuidValueConverter() this.requestId, required this.success, this.error, this.environment});
  factory _NetworkPublishEnvironmentResponse.fromJson(Map<String, dynamic> json) => _$NetworkPublishEnvironmentResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? error;
@override final  NetworkEnvironmentDescriptor? environment;

/// Create a copy of NetworkPublishEnvironmentResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkPublishEnvironmentResponseCopyWith<_NetworkPublishEnvironmentResponse> get copyWith => __$NetworkPublishEnvironmentResponseCopyWithImpl<_NetworkPublishEnvironmentResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkPublishEnvironmentResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkPublishEnvironmentResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.environment, environment) || other.environment == environment));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,environment);

@override
String toString() {
  return 'NetworkPublishEnvironmentResponse.def(requestId: $requestId, success: $success, error: $error, environment: $environment)';
}


}

/// @nodoc
abstract mixin class _$NetworkPublishEnvironmentResponseCopyWith<$Res> implements $NetworkPublishEnvironmentResponseCopyWith<$Res> {
  factory _$NetworkPublishEnvironmentResponseCopyWith(_NetworkPublishEnvironmentResponse value, $Res Function(_NetworkPublishEnvironmentResponse) _then) = __$NetworkPublishEnvironmentResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, NetworkEnvironmentDescriptor? environment
});


@override $NetworkEnvironmentDescriptorCopyWith<$Res>? get environment;

}
/// @nodoc
class __$NetworkPublishEnvironmentResponseCopyWithImpl<$Res>
    implements _$NetworkPublishEnvironmentResponseCopyWith<$Res> {
  __$NetworkPublishEnvironmentResponseCopyWithImpl(this._self, this._then);

  final _NetworkPublishEnvironmentResponse _self;
  final $Res Function(_NetworkPublishEnvironmentResponse) _then;

/// Create a copy of NetworkPublishEnvironmentResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? environment = freezed,}) {
  return _then(_NetworkPublishEnvironmentResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,environment: freezed == environment ? _self.environment : environment // ignore: cast_nullable_to_non_nullable
as NetworkEnvironmentDescriptor?,
  ));
}

/// Create a copy of NetworkPublishEnvironmentResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkEnvironmentDescriptorCopyWith<$Res>? get environment {
    if (_self.environment == null) {
    return null;
  }

  return $NetworkEnvironmentDescriptorCopyWith<$Res>(_self.environment!, (value) {
    return _then(_self.copyWith(environment: value));
  });
}
}


/// @nodoc
mixin _$NetworkListEnvironmentsRequest {

@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue? get requestId;@UuidValueConverter() UuidValue? get nodeId; bool get activeOnly;
/// Create a copy of NetworkListEnvironmentsRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkListEnvironmentsRequestCopyWith<NetworkListEnvironmentsRequest> get copyWith => _$NetworkListEnvironmentsRequestCopyWithImpl<NetworkListEnvironmentsRequest>(this as NetworkListEnvironmentsRequest, _$identity);

  /// Serializes this NetworkListEnvironmentsRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkListEnvironmentsRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.activeOnly, activeOnly) || other.activeOnly == activeOnly));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,nodeId,activeOnly);

@override
String toString() {
  return 'NetworkListEnvironmentsRequest(actorId: $actorId, requestId: $requestId, nodeId: $nodeId, activeOnly: $activeOnly)';
}


}

/// @nodoc
abstract mixin class $NetworkListEnvironmentsRequestCopyWith<$Res>  {
  factory $NetworkListEnvironmentsRequestCopyWith(NetworkListEnvironmentsRequest value, $Res Function(NetworkListEnvironmentsRequest) _then) = _$NetworkListEnvironmentsRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue? nodeId, bool activeOnly
});




}
/// @nodoc
class _$NetworkListEnvironmentsRequestCopyWithImpl<$Res>
    implements $NetworkListEnvironmentsRequestCopyWith<$Res> {
  _$NetworkListEnvironmentsRequestCopyWithImpl(this._self, this._then);

  final NetworkListEnvironmentsRequest _self;
  final $Res Function(NetworkListEnvironmentsRequest) _then;

/// Create a copy of NetworkListEnvironmentsRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? nodeId = freezed,Object? activeOnly = null,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,activeOnly: null == activeOnly ? _self.activeOnly : activeOnly // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkListEnvironmentsRequest].
extension NetworkListEnvironmentsRequestPatterns on NetworkListEnvironmentsRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkListEnvironmentsRequest value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkListEnvironmentsRequest() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkListEnvironmentsRequest value)  def,}){
final _that = this;
switch (_that) {
case _NetworkListEnvironmentsRequest():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkListEnvironmentsRequest value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkListEnvironmentsRequest() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? nodeId,  bool activeOnly)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkListEnvironmentsRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.nodeId,_that.activeOnly);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? nodeId,  bool activeOnly)  def,}) {final _that = this;
switch (_that) {
case _NetworkListEnvironmentsRequest():
return def(_that.actorId,_that.requestId,_that.nodeId,_that.activeOnly);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? nodeId,  bool activeOnly)?  def,}) {final _that = this;
switch (_that) {
case _NetworkListEnvironmentsRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.nodeId,_that.activeOnly);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkListEnvironmentsRequest implements NetworkListEnvironmentsRequest {
   _NetworkListEnvironmentsRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.requestId, @UuidValueConverter() this.nodeId, required this.activeOnly});
  factory _NetworkListEnvironmentsRequest.fromJson(Map<String, dynamic> json) => _$NetworkListEnvironmentsRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? requestId;
@override@UuidValueConverter() final  UuidValue? nodeId;
@override final  bool activeOnly;

/// Create a copy of NetworkListEnvironmentsRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkListEnvironmentsRequestCopyWith<_NetworkListEnvironmentsRequest> get copyWith => __$NetworkListEnvironmentsRequestCopyWithImpl<_NetworkListEnvironmentsRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkListEnvironmentsRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkListEnvironmentsRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.activeOnly, activeOnly) || other.activeOnly == activeOnly));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,nodeId,activeOnly);

@override
String toString() {
  return 'NetworkListEnvironmentsRequest.def(actorId: $actorId, requestId: $requestId, nodeId: $nodeId, activeOnly: $activeOnly)';
}


}

/// @nodoc
abstract mixin class _$NetworkListEnvironmentsRequestCopyWith<$Res> implements $NetworkListEnvironmentsRequestCopyWith<$Res> {
  factory _$NetworkListEnvironmentsRequestCopyWith(_NetworkListEnvironmentsRequest value, $Res Function(_NetworkListEnvironmentsRequest) _then) = __$NetworkListEnvironmentsRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue? nodeId, bool activeOnly
});




}
/// @nodoc
class __$NetworkListEnvironmentsRequestCopyWithImpl<$Res>
    implements _$NetworkListEnvironmentsRequestCopyWith<$Res> {
  __$NetworkListEnvironmentsRequestCopyWithImpl(this._self, this._then);

  final _NetworkListEnvironmentsRequest _self;
  final $Res Function(_NetworkListEnvironmentsRequest) _then;

/// Create a copy of NetworkListEnvironmentsRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? nodeId = freezed,Object? activeOnly = null,}) {
  return _then(_NetworkListEnvironmentsRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,activeOnly: null == activeOnly ? _self.activeOnly : activeOnly // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}


}


/// @nodoc
mixin _$NetworkListEnvironmentsResponse {

@UuidValueConverter() UuidValue? get requestId; bool get success; String? get error; List<NetworkEnvironmentDescriptor> get environments;
/// Create a copy of NetworkListEnvironmentsResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkListEnvironmentsResponseCopyWith<NetworkListEnvironmentsResponse> get copyWith => _$NetworkListEnvironmentsResponseCopyWithImpl<NetworkListEnvironmentsResponse>(this as NetworkListEnvironmentsResponse, _$identity);

  /// Serializes this NetworkListEnvironmentsResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkListEnvironmentsResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other.environments, environments));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,const DeepCollectionEquality().hash(environments));

@override
String toString() {
  return 'NetworkListEnvironmentsResponse(requestId: $requestId, success: $success, error: $error, environments: $environments)';
}


}

/// @nodoc
abstract mixin class $NetworkListEnvironmentsResponseCopyWith<$Res>  {
  factory $NetworkListEnvironmentsResponseCopyWith(NetworkListEnvironmentsResponse value, $Res Function(NetworkListEnvironmentsResponse) _then) = _$NetworkListEnvironmentsResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, List<NetworkEnvironmentDescriptor> environments
});




}
/// @nodoc
class _$NetworkListEnvironmentsResponseCopyWithImpl<$Res>
    implements $NetworkListEnvironmentsResponseCopyWith<$Res> {
  _$NetworkListEnvironmentsResponseCopyWithImpl(this._self, this._then);

  final NetworkListEnvironmentsResponse _self;
  final $Res Function(NetworkListEnvironmentsResponse) _then;

/// Create a copy of NetworkListEnvironmentsResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? environments = null,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,environments: null == environments ? _self.environments : environments // ignore: cast_nullable_to_non_nullable
as List<NetworkEnvironmentDescriptor>,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkListEnvironmentsResponse].
extension NetworkListEnvironmentsResponsePatterns on NetworkListEnvironmentsResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkListEnvironmentsResponse value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkListEnvironmentsResponse() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkListEnvironmentsResponse value)  def,}){
final _that = this;
switch (_that) {
case _NetworkListEnvironmentsResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkListEnvironmentsResponse value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkListEnvironmentsResponse() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  List<NetworkEnvironmentDescriptor> environments)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkListEnvironmentsResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.environments);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  List<NetworkEnvironmentDescriptor> environments)  def,}) {final _that = this;
switch (_that) {
case _NetworkListEnvironmentsResponse():
return def(_that.requestId,_that.success,_that.error,_that.environments);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  List<NetworkEnvironmentDescriptor> environments)?  def,}) {final _that = this;
switch (_that) {
case _NetworkListEnvironmentsResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.environments);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkListEnvironmentsResponse implements NetworkListEnvironmentsResponse {
   _NetworkListEnvironmentsResponse({@UuidValueConverter() this.requestId, required this.success, this.error, final  List<NetworkEnvironmentDescriptor> environments = const []}): _environments = environments;
  factory _NetworkListEnvironmentsResponse.fromJson(Map<String, dynamic> json) => _$NetworkListEnvironmentsResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? error;
 final  List<NetworkEnvironmentDescriptor> _environments;
@override@JsonKey() List<NetworkEnvironmentDescriptor> get environments {
  if (_environments is EqualUnmodifiableListView) return _environments;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_environments);
}


/// Create a copy of NetworkListEnvironmentsResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkListEnvironmentsResponseCopyWith<_NetworkListEnvironmentsResponse> get copyWith => __$NetworkListEnvironmentsResponseCopyWithImpl<_NetworkListEnvironmentsResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkListEnvironmentsResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkListEnvironmentsResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other._environments, _environments));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,const DeepCollectionEquality().hash(_environments));

@override
String toString() {
  return 'NetworkListEnvironmentsResponse.def(requestId: $requestId, success: $success, error: $error, environments: $environments)';
}


}

/// @nodoc
abstract mixin class _$NetworkListEnvironmentsResponseCopyWith<$Res> implements $NetworkListEnvironmentsResponseCopyWith<$Res> {
  factory _$NetworkListEnvironmentsResponseCopyWith(_NetworkListEnvironmentsResponse value, $Res Function(_NetworkListEnvironmentsResponse) _then) = __$NetworkListEnvironmentsResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, List<NetworkEnvironmentDescriptor> environments
});




}
/// @nodoc
class __$NetworkListEnvironmentsResponseCopyWithImpl<$Res>
    implements _$NetworkListEnvironmentsResponseCopyWith<$Res> {
  __$NetworkListEnvironmentsResponseCopyWithImpl(this._self, this._then);

  final _NetworkListEnvironmentsResponse _self;
  final $Res Function(_NetworkListEnvironmentsResponse) _then;

/// Create a copy of NetworkListEnvironmentsResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? environments = null,}) {
  return _then(_NetworkListEnvironmentsResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,environments: null == environments ? _self._environments : environments // ignore: cast_nullable_to_non_nullable
as List<NetworkEnvironmentDescriptor>,
  ));
}


}


/// @nodoc
mixin _$NetworkResolveHostedServiceRoutesRequest {

@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue? get requestId;@UuidValueConverter() UuidValue get consumerNodeId; String? get serviceName; String? get endpointRef; bool get acceptedPeersOnly;
/// Create a copy of NetworkResolveHostedServiceRoutesRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkResolveHostedServiceRoutesRequestCopyWith<NetworkResolveHostedServiceRoutesRequest> get copyWith => _$NetworkResolveHostedServiceRoutesRequestCopyWithImpl<NetworkResolveHostedServiceRoutesRequest>(this as NetworkResolveHostedServiceRoutesRequest, _$identity);

  /// Serializes this NetworkResolveHostedServiceRoutesRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkResolveHostedServiceRoutesRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.consumerNodeId, consumerNodeId) || other.consumerNodeId == consumerNodeId)&&(identical(other.serviceName, serviceName) || other.serviceName == serviceName)&&(identical(other.endpointRef, endpointRef) || other.endpointRef == endpointRef)&&(identical(other.acceptedPeersOnly, acceptedPeersOnly) || other.acceptedPeersOnly == acceptedPeersOnly));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,consumerNodeId,serviceName,endpointRef,acceptedPeersOnly);

@override
String toString() {
  return 'NetworkResolveHostedServiceRoutesRequest(actorId: $actorId, requestId: $requestId, consumerNodeId: $consumerNodeId, serviceName: $serviceName, endpointRef: $endpointRef, acceptedPeersOnly: $acceptedPeersOnly)';
}


}

/// @nodoc
abstract mixin class $NetworkResolveHostedServiceRoutesRequestCopyWith<$Res>  {
  factory $NetworkResolveHostedServiceRoutesRequestCopyWith(NetworkResolveHostedServiceRoutesRequest value, $Res Function(NetworkResolveHostedServiceRoutesRequest) _then) = _$NetworkResolveHostedServiceRoutesRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue consumerNodeId, String? serviceName, String? endpointRef, bool acceptedPeersOnly
});




}
/// @nodoc
class _$NetworkResolveHostedServiceRoutesRequestCopyWithImpl<$Res>
    implements $NetworkResolveHostedServiceRoutesRequestCopyWith<$Res> {
  _$NetworkResolveHostedServiceRoutesRequestCopyWithImpl(this._self, this._then);

  final NetworkResolveHostedServiceRoutesRequest _self;
  final $Res Function(NetworkResolveHostedServiceRoutesRequest) _then;

/// Create a copy of NetworkResolveHostedServiceRoutesRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? consumerNodeId = null,Object? serviceName = freezed,Object? endpointRef = freezed,Object? acceptedPeersOnly = null,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,consumerNodeId: null == consumerNodeId ? _self.consumerNodeId : consumerNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,serviceName: freezed == serviceName ? _self.serviceName : serviceName // ignore: cast_nullable_to_non_nullable
as String?,endpointRef: freezed == endpointRef ? _self.endpointRef : endpointRef // ignore: cast_nullable_to_non_nullable
as String?,acceptedPeersOnly: null == acceptedPeersOnly ? _self.acceptedPeersOnly : acceptedPeersOnly // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkResolveHostedServiceRoutesRequest].
extension NetworkResolveHostedServiceRoutesRequestPatterns on NetworkResolveHostedServiceRoutesRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkResolveHostedServiceRoutesRequest value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkResolveHostedServiceRoutesRequest() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkResolveHostedServiceRoutesRequest value)  def,}){
final _that = this;
switch (_that) {
case _NetworkResolveHostedServiceRoutesRequest():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkResolveHostedServiceRoutesRequest value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkResolveHostedServiceRoutesRequest() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue consumerNodeId,  String? serviceName,  String? endpointRef,  bool acceptedPeersOnly)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkResolveHostedServiceRoutesRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.consumerNodeId,_that.serviceName,_that.endpointRef,_that.acceptedPeersOnly);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue consumerNodeId,  String? serviceName,  String? endpointRef,  bool acceptedPeersOnly)  def,}) {final _that = this;
switch (_that) {
case _NetworkResolveHostedServiceRoutesRequest():
return def(_that.actorId,_that.requestId,_that.consumerNodeId,_that.serviceName,_that.endpointRef,_that.acceptedPeersOnly);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue consumerNodeId,  String? serviceName,  String? endpointRef,  bool acceptedPeersOnly)?  def,}) {final _that = this;
switch (_that) {
case _NetworkResolveHostedServiceRoutesRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.consumerNodeId,_that.serviceName,_that.endpointRef,_that.acceptedPeersOnly);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkResolveHostedServiceRoutesRequest implements NetworkResolveHostedServiceRoutesRequest {
   _NetworkResolveHostedServiceRoutesRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.requestId, @UuidValueConverter() required this.consumerNodeId, this.serviceName, this.endpointRef, required this.acceptedPeersOnly});
  factory _NetworkResolveHostedServiceRoutesRequest.fromJson(Map<String, dynamic> json) => _$NetworkResolveHostedServiceRoutesRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? requestId;
@override@UuidValueConverter() final  UuidValue consumerNodeId;
@override final  String? serviceName;
@override final  String? endpointRef;
@override final  bool acceptedPeersOnly;

/// Create a copy of NetworkResolveHostedServiceRoutesRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkResolveHostedServiceRoutesRequestCopyWith<_NetworkResolveHostedServiceRoutesRequest> get copyWith => __$NetworkResolveHostedServiceRoutesRequestCopyWithImpl<_NetworkResolveHostedServiceRoutesRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkResolveHostedServiceRoutesRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkResolveHostedServiceRoutesRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.consumerNodeId, consumerNodeId) || other.consumerNodeId == consumerNodeId)&&(identical(other.serviceName, serviceName) || other.serviceName == serviceName)&&(identical(other.endpointRef, endpointRef) || other.endpointRef == endpointRef)&&(identical(other.acceptedPeersOnly, acceptedPeersOnly) || other.acceptedPeersOnly == acceptedPeersOnly));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,consumerNodeId,serviceName,endpointRef,acceptedPeersOnly);

@override
String toString() {
  return 'NetworkResolveHostedServiceRoutesRequest.def(actorId: $actorId, requestId: $requestId, consumerNodeId: $consumerNodeId, serviceName: $serviceName, endpointRef: $endpointRef, acceptedPeersOnly: $acceptedPeersOnly)';
}


}

/// @nodoc
abstract mixin class _$NetworkResolveHostedServiceRoutesRequestCopyWith<$Res> implements $NetworkResolveHostedServiceRoutesRequestCopyWith<$Res> {
  factory _$NetworkResolveHostedServiceRoutesRequestCopyWith(_NetworkResolveHostedServiceRoutesRequest value, $Res Function(_NetworkResolveHostedServiceRoutesRequest) _then) = __$NetworkResolveHostedServiceRoutesRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue consumerNodeId, String? serviceName, String? endpointRef, bool acceptedPeersOnly
});




}
/// @nodoc
class __$NetworkResolveHostedServiceRoutesRequestCopyWithImpl<$Res>
    implements _$NetworkResolveHostedServiceRoutesRequestCopyWith<$Res> {
  __$NetworkResolveHostedServiceRoutesRequestCopyWithImpl(this._self, this._then);

  final _NetworkResolveHostedServiceRoutesRequest _self;
  final $Res Function(_NetworkResolveHostedServiceRoutesRequest) _then;

/// Create a copy of NetworkResolveHostedServiceRoutesRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? consumerNodeId = null,Object? serviceName = freezed,Object? endpointRef = freezed,Object? acceptedPeersOnly = null,}) {
  return _then(_NetworkResolveHostedServiceRoutesRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,consumerNodeId: null == consumerNodeId ? _self.consumerNodeId : consumerNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue,serviceName: freezed == serviceName ? _self.serviceName : serviceName // ignore: cast_nullable_to_non_nullable
as String?,endpointRef: freezed == endpointRef ? _self.endpointRef : endpointRef // ignore: cast_nullable_to_non_nullable
as String?,acceptedPeersOnly: null == acceptedPeersOnly ? _self.acceptedPeersOnly : acceptedPeersOnly // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}


}


/// @nodoc
mixin _$NetworkResolveHostedServiceRoutesResponse {

@UuidValueConverter() UuidValue? get requestId; bool get success; String? get error; List<NetworkResolvedHostedServiceRoute> get routes;
/// Create a copy of NetworkResolveHostedServiceRoutesResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkResolveHostedServiceRoutesResponseCopyWith<NetworkResolveHostedServiceRoutesResponse> get copyWith => _$NetworkResolveHostedServiceRoutesResponseCopyWithImpl<NetworkResolveHostedServiceRoutesResponse>(this as NetworkResolveHostedServiceRoutesResponse, _$identity);

  /// Serializes this NetworkResolveHostedServiceRoutesResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkResolveHostedServiceRoutesResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other.routes, routes));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,const DeepCollectionEquality().hash(routes));

@override
String toString() {
  return 'NetworkResolveHostedServiceRoutesResponse(requestId: $requestId, success: $success, error: $error, routes: $routes)';
}


}

/// @nodoc
abstract mixin class $NetworkResolveHostedServiceRoutesResponseCopyWith<$Res>  {
  factory $NetworkResolveHostedServiceRoutesResponseCopyWith(NetworkResolveHostedServiceRoutesResponse value, $Res Function(NetworkResolveHostedServiceRoutesResponse) _then) = _$NetworkResolveHostedServiceRoutesResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, List<NetworkResolvedHostedServiceRoute> routes
});




}
/// @nodoc
class _$NetworkResolveHostedServiceRoutesResponseCopyWithImpl<$Res>
    implements $NetworkResolveHostedServiceRoutesResponseCopyWith<$Res> {
  _$NetworkResolveHostedServiceRoutesResponseCopyWithImpl(this._self, this._then);

  final NetworkResolveHostedServiceRoutesResponse _self;
  final $Res Function(NetworkResolveHostedServiceRoutesResponse) _then;

/// Create a copy of NetworkResolveHostedServiceRoutesResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? routes = null,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,routes: null == routes ? _self.routes : routes // ignore: cast_nullable_to_non_nullable
as List<NetworkResolvedHostedServiceRoute>,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkResolveHostedServiceRoutesResponse].
extension NetworkResolveHostedServiceRoutesResponsePatterns on NetworkResolveHostedServiceRoutesResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkResolveHostedServiceRoutesResponse value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkResolveHostedServiceRoutesResponse() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkResolveHostedServiceRoutesResponse value)  def,}){
final _that = this;
switch (_that) {
case _NetworkResolveHostedServiceRoutesResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkResolveHostedServiceRoutesResponse value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkResolveHostedServiceRoutesResponse() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  List<NetworkResolvedHostedServiceRoute> routes)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkResolveHostedServiceRoutesResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.routes);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  List<NetworkResolvedHostedServiceRoute> routes)  def,}) {final _that = this;
switch (_that) {
case _NetworkResolveHostedServiceRoutesResponse():
return def(_that.requestId,_that.success,_that.error,_that.routes);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  List<NetworkResolvedHostedServiceRoute> routes)?  def,}) {final _that = this;
switch (_that) {
case _NetworkResolveHostedServiceRoutesResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.routes);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkResolveHostedServiceRoutesResponse implements NetworkResolveHostedServiceRoutesResponse {
   _NetworkResolveHostedServiceRoutesResponse({@UuidValueConverter() this.requestId, required this.success, this.error, final  List<NetworkResolvedHostedServiceRoute> routes = const []}): _routes = routes;
  factory _NetworkResolveHostedServiceRoutesResponse.fromJson(Map<String, dynamic> json) => _$NetworkResolveHostedServiceRoutesResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? error;
 final  List<NetworkResolvedHostedServiceRoute> _routes;
@override@JsonKey() List<NetworkResolvedHostedServiceRoute> get routes {
  if (_routes is EqualUnmodifiableListView) return _routes;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_routes);
}


/// Create a copy of NetworkResolveHostedServiceRoutesResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkResolveHostedServiceRoutesResponseCopyWith<_NetworkResolveHostedServiceRoutesResponse> get copyWith => __$NetworkResolveHostedServiceRoutesResponseCopyWithImpl<_NetworkResolveHostedServiceRoutesResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkResolveHostedServiceRoutesResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkResolveHostedServiceRoutesResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other._routes, _routes));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,const DeepCollectionEquality().hash(_routes));

@override
String toString() {
  return 'NetworkResolveHostedServiceRoutesResponse.def(requestId: $requestId, success: $success, error: $error, routes: $routes)';
}


}

/// @nodoc
abstract mixin class _$NetworkResolveHostedServiceRoutesResponseCopyWith<$Res> implements $NetworkResolveHostedServiceRoutesResponseCopyWith<$Res> {
  factory _$NetworkResolveHostedServiceRoutesResponseCopyWith(_NetworkResolveHostedServiceRoutesResponse value, $Res Function(_NetworkResolveHostedServiceRoutesResponse) _then) = __$NetworkResolveHostedServiceRoutesResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, List<NetworkResolvedHostedServiceRoute> routes
});




}
/// @nodoc
class __$NetworkResolveHostedServiceRoutesResponseCopyWithImpl<$Res>
    implements _$NetworkResolveHostedServiceRoutesResponseCopyWith<$Res> {
  __$NetworkResolveHostedServiceRoutesResponseCopyWithImpl(this._self, this._then);

  final _NetworkResolveHostedServiceRoutesResponse _self;
  final $Res Function(_NetworkResolveHostedServiceRoutesResponse) _then;

/// Create a copy of NetworkResolveHostedServiceRoutesResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? routes = null,}) {
  return _then(_NetworkResolveHostedServiceRoutesResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,routes: null == routes ? _self._routes : routes // ignore: cast_nullable_to_non_nullable
as List<NetworkResolvedHostedServiceRoute>,
  ));
}


}


/// @nodoc
mixin _$NetworkDiscoverTerritoryRequest {

@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue? get requestId;@UuidValueConverter() UuidValue? get nodeId; bool get includePeers; bool get includeHostedServices; bool get includeEnvironments; bool get activeEnvironmentsOnly; bool get acceptedPeersOnly; int? get limitNodes;
/// Create a copy of NetworkDiscoverTerritoryRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkDiscoverTerritoryRequestCopyWith<NetworkDiscoverTerritoryRequest> get copyWith => _$NetworkDiscoverTerritoryRequestCopyWithImpl<NetworkDiscoverTerritoryRequest>(this as NetworkDiscoverTerritoryRequest, _$identity);

  /// Serializes this NetworkDiscoverTerritoryRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkDiscoverTerritoryRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.includePeers, includePeers) || other.includePeers == includePeers)&&(identical(other.includeHostedServices, includeHostedServices) || other.includeHostedServices == includeHostedServices)&&(identical(other.includeEnvironments, includeEnvironments) || other.includeEnvironments == includeEnvironments)&&(identical(other.activeEnvironmentsOnly, activeEnvironmentsOnly) || other.activeEnvironmentsOnly == activeEnvironmentsOnly)&&(identical(other.acceptedPeersOnly, acceptedPeersOnly) || other.acceptedPeersOnly == acceptedPeersOnly)&&(identical(other.limitNodes, limitNodes) || other.limitNodes == limitNodes));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,nodeId,includePeers,includeHostedServices,includeEnvironments,activeEnvironmentsOnly,acceptedPeersOnly,limitNodes);

@override
String toString() {
  return 'NetworkDiscoverTerritoryRequest(actorId: $actorId, requestId: $requestId, nodeId: $nodeId, includePeers: $includePeers, includeHostedServices: $includeHostedServices, includeEnvironments: $includeEnvironments, activeEnvironmentsOnly: $activeEnvironmentsOnly, acceptedPeersOnly: $acceptedPeersOnly, limitNodes: $limitNodes)';
}


}

/// @nodoc
abstract mixin class $NetworkDiscoverTerritoryRequestCopyWith<$Res>  {
  factory $NetworkDiscoverTerritoryRequestCopyWith(NetworkDiscoverTerritoryRequest value, $Res Function(NetworkDiscoverTerritoryRequest) _then) = _$NetworkDiscoverTerritoryRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue? nodeId, bool includePeers, bool includeHostedServices, bool includeEnvironments, bool activeEnvironmentsOnly, bool acceptedPeersOnly, int? limitNodes
});




}
/// @nodoc
class _$NetworkDiscoverTerritoryRequestCopyWithImpl<$Res>
    implements $NetworkDiscoverTerritoryRequestCopyWith<$Res> {
  _$NetworkDiscoverTerritoryRequestCopyWithImpl(this._self, this._then);

  final NetworkDiscoverTerritoryRequest _self;
  final $Res Function(NetworkDiscoverTerritoryRequest) _then;

/// Create a copy of NetworkDiscoverTerritoryRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? nodeId = freezed,Object? includePeers = null,Object? includeHostedServices = null,Object? includeEnvironments = null,Object? activeEnvironmentsOnly = null,Object? acceptedPeersOnly = null,Object? limitNodes = freezed,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,includePeers: null == includePeers ? _self.includePeers : includePeers // ignore: cast_nullable_to_non_nullable
as bool,includeHostedServices: null == includeHostedServices ? _self.includeHostedServices : includeHostedServices // ignore: cast_nullable_to_non_nullable
as bool,includeEnvironments: null == includeEnvironments ? _self.includeEnvironments : includeEnvironments // ignore: cast_nullable_to_non_nullable
as bool,activeEnvironmentsOnly: null == activeEnvironmentsOnly ? _self.activeEnvironmentsOnly : activeEnvironmentsOnly // ignore: cast_nullable_to_non_nullable
as bool,acceptedPeersOnly: null == acceptedPeersOnly ? _self.acceptedPeersOnly : acceptedPeersOnly // ignore: cast_nullable_to_non_nullable
as bool,limitNodes: freezed == limitNodes ? _self.limitNodes : limitNodes // ignore: cast_nullable_to_non_nullable
as int?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkDiscoverTerritoryRequest].
extension NetworkDiscoverTerritoryRequestPatterns on NetworkDiscoverTerritoryRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkDiscoverTerritoryRequest value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkDiscoverTerritoryRequest() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkDiscoverTerritoryRequest value)  def,}){
final _that = this;
switch (_that) {
case _NetworkDiscoverTerritoryRequest():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkDiscoverTerritoryRequest value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkDiscoverTerritoryRequest() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? nodeId,  bool includePeers,  bool includeHostedServices,  bool includeEnvironments,  bool activeEnvironmentsOnly,  bool acceptedPeersOnly,  int? limitNodes)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkDiscoverTerritoryRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.nodeId,_that.includePeers,_that.includeHostedServices,_that.includeEnvironments,_that.activeEnvironmentsOnly,_that.acceptedPeersOnly,_that.limitNodes);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? nodeId,  bool includePeers,  bool includeHostedServices,  bool includeEnvironments,  bool activeEnvironmentsOnly,  bool acceptedPeersOnly,  int? limitNodes)  def,}) {final _that = this;
switch (_that) {
case _NetworkDiscoverTerritoryRequest():
return def(_that.actorId,_that.requestId,_that.nodeId,_that.includePeers,_that.includeHostedServices,_that.includeEnvironments,_that.activeEnvironmentsOnly,_that.acceptedPeersOnly,_that.limitNodes);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? nodeId,  bool includePeers,  bool includeHostedServices,  bool includeEnvironments,  bool activeEnvironmentsOnly,  bool acceptedPeersOnly,  int? limitNodes)?  def,}) {final _that = this;
switch (_that) {
case _NetworkDiscoverTerritoryRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.nodeId,_that.includePeers,_that.includeHostedServices,_that.includeEnvironments,_that.activeEnvironmentsOnly,_that.acceptedPeersOnly,_that.limitNodes);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkDiscoverTerritoryRequest implements NetworkDiscoverTerritoryRequest {
   _NetworkDiscoverTerritoryRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.requestId, @UuidValueConverter() this.nodeId, required this.includePeers, required this.includeHostedServices, required this.includeEnvironments, required this.activeEnvironmentsOnly, required this.acceptedPeersOnly, this.limitNodes});
  factory _NetworkDiscoverTerritoryRequest.fromJson(Map<String, dynamic> json) => _$NetworkDiscoverTerritoryRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? requestId;
@override@UuidValueConverter() final  UuidValue? nodeId;
@override final  bool includePeers;
@override final  bool includeHostedServices;
@override final  bool includeEnvironments;
@override final  bool activeEnvironmentsOnly;
@override final  bool acceptedPeersOnly;
@override final  int? limitNodes;

/// Create a copy of NetworkDiscoverTerritoryRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkDiscoverTerritoryRequestCopyWith<_NetworkDiscoverTerritoryRequest> get copyWith => __$NetworkDiscoverTerritoryRequestCopyWithImpl<_NetworkDiscoverTerritoryRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkDiscoverTerritoryRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkDiscoverTerritoryRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.includePeers, includePeers) || other.includePeers == includePeers)&&(identical(other.includeHostedServices, includeHostedServices) || other.includeHostedServices == includeHostedServices)&&(identical(other.includeEnvironments, includeEnvironments) || other.includeEnvironments == includeEnvironments)&&(identical(other.activeEnvironmentsOnly, activeEnvironmentsOnly) || other.activeEnvironmentsOnly == activeEnvironmentsOnly)&&(identical(other.acceptedPeersOnly, acceptedPeersOnly) || other.acceptedPeersOnly == acceptedPeersOnly)&&(identical(other.limitNodes, limitNodes) || other.limitNodes == limitNodes));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,nodeId,includePeers,includeHostedServices,includeEnvironments,activeEnvironmentsOnly,acceptedPeersOnly,limitNodes);

@override
String toString() {
  return 'NetworkDiscoverTerritoryRequest.def(actorId: $actorId, requestId: $requestId, nodeId: $nodeId, includePeers: $includePeers, includeHostedServices: $includeHostedServices, includeEnvironments: $includeEnvironments, activeEnvironmentsOnly: $activeEnvironmentsOnly, acceptedPeersOnly: $acceptedPeersOnly, limitNodes: $limitNodes)';
}


}

/// @nodoc
abstract mixin class _$NetworkDiscoverTerritoryRequestCopyWith<$Res> implements $NetworkDiscoverTerritoryRequestCopyWith<$Res> {
  factory _$NetworkDiscoverTerritoryRequestCopyWith(_NetworkDiscoverTerritoryRequest value, $Res Function(_NetworkDiscoverTerritoryRequest) _then) = __$NetworkDiscoverTerritoryRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue? nodeId, bool includePeers, bool includeHostedServices, bool includeEnvironments, bool activeEnvironmentsOnly, bool acceptedPeersOnly, int? limitNodes
});




}
/// @nodoc
class __$NetworkDiscoverTerritoryRequestCopyWithImpl<$Res>
    implements _$NetworkDiscoverTerritoryRequestCopyWith<$Res> {
  __$NetworkDiscoverTerritoryRequestCopyWithImpl(this._self, this._then);

  final _NetworkDiscoverTerritoryRequest _self;
  final $Res Function(_NetworkDiscoverTerritoryRequest) _then;

/// Create a copy of NetworkDiscoverTerritoryRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? nodeId = freezed,Object? includePeers = null,Object? includeHostedServices = null,Object? includeEnvironments = null,Object? activeEnvironmentsOnly = null,Object? acceptedPeersOnly = null,Object? limitNodes = freezed,}) {
  return _then(_NetworkDiscoverTerritoryRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,includePeers: null == includePeers ? _self.includePeers : includePeers // ignore: cast_nullable_to_non_nullable
as bool,includeHostedServices: null == includeHostedServices ? _self.includeHostedServices : includeHostedServices // ignore: cast_nullable_to_non_nullable
as bool,includeEnvironments: null == includeEnvironments ? _self.includeEnvironments : includeEnvironments // ignore: cast_nullable_to_non_nullable
as bool,activeEnvironmentsOnly: null == activeEnvironmentsOnly ? _self.activeEnvironmentsOnly : activeEnvironmentsOnly // ignore: cast_nullable_to_non_nullable
as bool,acceptedPeersOnly: null == acceptedPeersOnly ? _self.acceptedPeersOnly : acceptedPeersOnly // ignore: cast_nullable_to_non_nullable
as bool,limitNodes: freezed == limitNodes ? _self.limitNodes : limitNodes // ignore: cast_nullable_to_non_nullable
as int?,
  ));
}


}


/// @nodoc
mixin _$NetworkDiscoverTerritoryResponse {

@UuidValueConverter() UuidValue? get requestId; bool get success; String? get error; List<NetworkTerritoryNodeDescriptor> get nodes; String? get summary;
/// Create a copy of NetworkDiscoverTerritoryResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkDiscoverTerritoryResponseCopyWith<NetworkDiscoverTerritoryResponse> get copyWith => _$NetworkDiscoverTerritoryResponseCopyWithImpl<NetworkDiscoverTerritoryResponse>(this as NetworkDiscoverTerritoryResponse, _$identity);

  /// Serializes this NetworkDiscoverTerritoryResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkDiscoverTerritoryResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other.nodes, nodes)&&(identical(other.summary, summary) || other.summary == summary));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,const DeepCollectionEquality().hash(nodes),summary);

@override
String toString() {
  return 'NetworkDiscoverTerritoryResponse(requestId: $requestId, success: $success, error: $error, nodes: $nodes, summary: $summary)';
}


}

/// @nodoc
abstract mixin class $NetworkDiscoverTerritoryResponseCopyWith<$Res>  {
  factory $NetworkDiscoverTerritoryResponseCopyWith(NetworkDiscoverTerritoryResponse value, $Res Function(NetworkDiscoverTerritoryResponse) _then) = _$NetworkDiscoverTerritoryResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, List<NetworkTerritoryNodeDescriptor> nodes, String? summary
});




}
/// @nodoc
class _$NetworkDiscoverTerritoryResponseCopyWithImpl<$Res>
    implements $NetworkDiscoverTerritoryResponseCopyWith<$Res> {
  _$NetworkDiscoverTerritoryResponseCopyWithImpl(this._self, this._then);

  final NetworkDiscoverTerritoryResponse _self;
  final $Res Function(NetworkDiscoverTerritoryResponse) _then;

/// Create a copy of NetworkDiscoverTerritoryResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? nodes = null,Object? summary = freezed,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,nodes: null == nodes ? _self.nodes : nodes // ignore: cast_nullable_to_non_nullable
as List<NetworkTerritoryNodeDescriptor>,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkDiscoverTerritoryResponse].
extension NetworkDiscoverTerritoryResponsePatterns on NetworkDiscoverTerritoryResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkDiscoverTerritoryResponse value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkDiscoverTerritoryResponse() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkDiscoverTerritoryResponse value)  def,}){
final _that = this;
switch (_that) {
case _NetworkDiscoverTerritoryResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkDiscoverTerritoryResponse value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkDiscoverTerritoryResponse() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  List<NetworkTerritoryNodeDescriptor> nodes,  String? summary)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkDiscoverTerritoryResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.nodes,_that.summary);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  List<NetworkTerritoryNodeDescriptor> nodes,  String? summary)  def,}) {final _that = this;
switch (_that) {
case _NetworkDiscoverTerritoryResponse():
return def(_that.requestId,_that.success,_that.error,_that.nodes,_that.summary);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  List<NetworkTerritoryNodeDescriptor> nodes,  String? summary)?  def,}) {final _that = this;
switch (_that) {
case _NetworkDiscoverTerritoryResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.nodes,_that.summary);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkDiscoverTerritoryResponse implements NetworkDiscoverTerritoryResponse {
   _NetworkDiscoverTerritoryResponse({@UuidValueConverter() this.requestId, required this.success, this.error, final  List<NetworkTerritoryNodeDescriptor> nodes = const [], this.summary}): _nodes = nodes;
  factory _NetworkDiscoverTerritoryResponse.fromJson(Map<String, dynamic> json) => _$NetworkDiscoverTerritoryResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? error;
 final  List<NetworkTerritoryNodeDescriptor> _nodes;
@override@JsonKey() List<NetworkTerritoryNodeDescriptor> get nodes {
  if (_nodes is EqualUnmodifiableListView) return _nodes;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_nodes);
}

@override final  String? summary;

/// Create a copy of NetworkDiscoverTerritoryResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkDiscoverTerritoryResponseCopyWith<_NetworkDiscoverTerritoryResponse> get copyWith => __$NetworkDiscoverTerritoryResponseCopyWithImpl<_NetworkDiscoverTerritoryResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkDiscoverTerritoryResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkDiscoverTerritoryResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other._nodes, _nodes)&&(identical(other.summary, summary) || other.summary == summary));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,const DeepCollectionEquality().hash(_nodes),summary);

@override
String toString() {
  return 'NetworkDiscoverTerritoryResponse.def(requestId: $requestId, success: $success, error: $error, nodes: $nodes, summary: $summary)';
}


}

/// @nodoc
abstract mixin class _$NetworkDiscoverTerritoryResponseCopyWith<$Res> implements $NetworkDiscoverTerritoryResponseCopyWith<$Res> {
  factory _$NetworkDiscoverTerritoryResponseCopyWith(_NetworkDiscoverTerritoryResponse value, $Res Function(_NetworkDiscoverTerritoryResponse) _then) = __$NetworkDiscoverTerritoryResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, List<NetworkTerritoryNodeDescriptor> nodes, String? summary
});




}
/// @nodoc
class __$NetworkDiscoverTerritoryResponseCopyWithImpl<$Res>
    implements _$NetworkDiscoverTerritoryResponseCopyWith<$Res> {
  __$NetworkDiscoverTerritoryResponseCopyWithImpl(this._self, this._then);

  final _NetworkDiscoverTerritoryResponse _self;
  final $Res Function(_NetworkDiscoverTerritoryResponse) _then;

/// Create a copy of NetworkDiscoverTerritoryResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? nodes = null,Object? summary = freezed,}) {
  return _then(_NetworkDiscoverTerritoryResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,nodes: null == nodes ? _self._nodes : nodes // ignore: cast_nullable_to_non_nullable
as List<NetworkTerritoryNodeDescriptor>,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$NetworkDiscoverExperienceTerritoryRequest {

@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue? get requestId; String get experienceName; List<String> get requiredServicePackageNames; List<String> get requiredEndpointRefs;@UuidValueConverter() UuidValue? get consumerNodeId; bool get activeEnvironmentsOnly; bool get acceptedPeersOnly; bool get includeRouteHints; bool get requireAccessEvidence; List<String> get accessEvidenceRefs; int? get limitEntries;
/// Create a copy of NetworkDiscoverExperienceTerritoryRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkDiscoverExperienceTerritoryRequestCopyWith<NetworkDiscoverExperienceTerritoryRequest> get copyWith => _$NetworkDiscoverExperienceTerritoryRequestCopyWithImpl<NetworkDiscoverExperienceTerritoryRequest>(this as NetworkDiscoverExperienceTerritoryRequest, _$identity);

  /// Serializes this NetworkDiscoverExperienceTerritoryRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkDiscoverExperienceTerritoryRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.experienceName, experienceName) || other.experienceName == experienceName)&&const DeepCollectionEquality().equals(other.requiredServicePackageNames, requiredServicePackageNames)&&const DeepCollectionEquality().equals(other.requiredEndpointRefs, requiredEndpointRefs)&&(identical(other.consumerNodeId, consumerNodeId) || other.consumerNodeId == consumerNodeId)&&(identical(other.activeEnvironmentsOnly, activeEnvironmentsOnly) || other.activeEnvironmentsOnly == activeEnvironmentsOnly)&&(identical(other.acceptedPeersOnly, acceptedPeersOnly) || other.acceptedPeersOnly == acceptedPeersOnly)&&(identical(other.includeRouteHints, includeRouteHints) || other.includeRouteHints == includeRouteHints)&&(identical(other.requireAccessEvidence, requireAccessEvidence) || other.requireAccessEvidence == requireAccessEvidence)&&const DeepCollectionEquality().equals(other.accessEvidenceRefs, accessEvidenceRefs)&&(identical(other.limitEntries, limitEntries) || other.limitEntries == limitEntries));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,experienceName,const DeepCollectionEquality().hash(requiredServicePackageNames),const DeepCollectionEquality().hash(requiredEndpointRefs),consumerNodeId,activeEnvironmentsOnly,acceptedPeersOnly,includeRouteHints,requireAccessEvidence,const DeepCollectionEquality().hash(accessEvidenceRefs),limitEntries);

@override
String toString() {
  return 'NetworkDiscoverExperienceTerritoryRequest(actorId: $actorId, requestId: $requestId, experienceName: $experienceName, requiredServicePackageNames: $requiredServicePackageNames, requiredEndpointRefs: $requiredEndpointRefs, consumerNodeId: $consumerNodeId, activeEnvironmentsOnly: $activeEnvironmentsOnly, acceptedPeersOnly: $acceptedPeersOnly, includeRouteHints: $includeRouteHints, requireAccessEvidence: $requireAccessEvidence, accessEvidenceRefs: $accessEvidenceRefs, limitEntries: $limitEntries)';
}


}

/// @nodoc
abstract mixin class $NetworkDiscoverExperienceTerritoryRequestCopyWith<$Res>  {
  factory $NetworkDiscoverExperienceTerritoryRequestCopyWith(NetworkDiscoverExperienceTerritoryRequest value, $Res Function(NetworkDiscoverExperienceTerritoryRequest) _then) = _$NetworkDiscoverExperienceTerritoryRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId, String experienceName, List<String> requiredServicePackageNames, List<String> requiredEndpointRefs,@UuidValueConverter() UuidValue? consumerNodeId, bool activeEnvironmentsOnly, bool acceptedPeersOnly, bool includeRouteHints, bool requireAccessEvidence, List<String> accessEvidenceRefs, int? limitEntries
});




}
/// @nodoc
class _$NetworkDiscoverExperienceTerritoryRequestCopyWithImpl<$Res>
    implements $NetworkDiscoverExperienceTerritoryRequestCopyWith<$Res> {
  _$NetworkDiscoverExperienceTerritoryRequestCopyWithImpl(this._self, this._then);

  final NetworkDiscoverExperienceTerritoryRequest _self;
  final $Res Function(NetworkDiscoverExperienceTerritoryRequest) _then;

/// Create a copy of NetworkDiscoverExperienceTerritoryRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? experienceName = null,Object? requiredServicePackageNames = null,Object? requiredEndpointRefs = null,Object? consumerNodeId = freezed,Object? activeEnvironmentsOnly = null,Object? acceptedPeersOnly = null,Object? includeRouteHints = null,Object? requireAccessEvidence = null,Object? accessEvidenceRefs = null,Object? limitEntries = freezed,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,experienceName: null == experienceName ? _self.experienceName : experienceName // ignore: cast_nullable_to_non_nullable
as String,requiredServicePackageNames: null == requiredServicePackageNames ? _self.requiredServicePackageNames : requiredServicePackageNames // ignore: cast_nullable_to_non_nullable
as List<String>,requiredEndpointRefs: null == requiredEndpointRefs ? _self.requiredEndpointRefs : requiredEndpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,consumerNodeId: freezed == consumerNodeId ? _self.consumerNodeId : consumerNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,activeEnvironmentsOnly: null == activeEnvironmentsOnly ? _self.activeEnvironmentsOnly : activeEnvironmentsOnly // ignore: cast_nullable_to_non_nullable
as bool,acceptedPeersOnly: null == acceptedPeersOnly ? _self.acceptedPeersOnly : acceptedPeersOnly // ignore: cast_nullable_to_non_nullable
as bool,includeRouteHints: null == includeRouteHints ? _self.includeRouteHints : includeRouteHints // ignore: cast_nullable_to_non_nullable
as bool,requireAccessEvidence: null == requireAccessEvidence ? _self.requireAccessEvidence : requireAccessEvidence // ignore: cast_nullable_to_non_nullable
as bool,accessEvidenceRefs: null == accessEvidenceRefs ? _self.accessEvidenceRefs : accessEvidenceRefs // ignore: cast_nullable_to_non_nullable
as List<String>,limitEntries: freezed == limitEntries ? _self.limitEntries : limitEntries // ignore: cast_nullable_to_non_nullable
as int?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkDiscoverExperienceTerritoryRequest].
extension NetworkDiscoverExperienceTerritoryRequestPatterns on NetworkDiscoverExperienceTerritoryRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkDiscoverExperienceTerritoryRequest value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkDiscoverExperienceTerritoryRequest() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkDiscoverExperienceTerritoryRequest value)  def,}){
final _that = this;
switch (_that) {
case _NetworkDiscoverExperienceTerritoryRequest():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkDiscoverExperienceTerritoryRequest value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkDiscoverExperienceTerritoryRequest() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId,  String experienceName,  List<String> requiredServicePackageNames,  List<String> requiredEndpointRefs, @UuidValueConverter()  UuidValue? consumerNodeId,  bool activeEnvironmentsOnly,  bool acceptedPeersOnly,  bool includeRouteHints,  bool requireAccessEvidence,  List<String> accessEvidenceRefs,  int? limitEntries)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkDiscoverExperienceTerritoryRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.experienceName,_that.requiredServicePackageNames,_that.requiredEndpointRefs,_that.consumerNodeId,_that.activeEnvironmentsOnly,_that.acceptedPeersOnly,_that.includeRouteHints,_that.requireAccessEvidence,_that.accessEvidenceRefs,_that.limitEntries);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId,  String experienceName,  List<String> requiredServicePackageNames,  List<String> requiredEndpointRefs, @UuidValueConverter()  UuidValue? consumerNodeId,  bool activeEnvironmentsOnly,  bool acceptedPeersOnly,  bool includeRouteHints,  bool requireAccessEvidence,  List<String> accessEvidenceRefs,  int? limitEntries)  def,}) {final _that = this;
switch (_that) {
case _NetworkDiscoverExperienceTerritoryRequest():
return def(_that.actorId,_that.requestId,_that.experienceName,_that.requiredServicePackageNames,_that.requiredEndpointRefs,_that.consumerNodeId,_that.activeEnvironmentsOnly,_that.acceptedPeersOnly,_that.includeRouteHints,_that.requireAccessEvidence,_that.accessEvidenceRefs,_that.limitEntries);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? requestId,  String experienceName,  List<String> requiredServicePackageNames,  List<String> requiredEndpointRefs, @UuidValueConverter()  UuidValue? consumerNodeId,  bool activeEnvironmentsOnly,  bool acceptedPeersOnly,  bool includeRouteHints,  bool requireAccessEvidence,  List<String> accessEvidenceRefs,  int? limitEntries)?  def,}) {final _that = this;
switch (_that) {
case _NetworkDiscoverExperienceTerritoryRequest() when def != null:
return def(_that.actorId,_that.requestId,_that.experienceName,_that.requiredServicePackageNames,_that.requiredEndpointRefs,_that.consumerNodeId,_that.activeEnvironmentsOnly,_that.acceptedPeersOnly,_that.includeRouteHints,_that.requireAccessEvidence,_that.accessEvidenceRefs,_that.limitEntries);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkDiscoverExperienceTerritoryRequest implements NetworkDiscoverExperienceTerritoryRequest {
   _NetworkDiscoverExperienceTerritoryRequest({@UuidValueConverter() this.actorId, @UuidValueConverter() this.requestId, required this.experienceName, final  List<String> requiredServicePackageNames = const [], final  List<String> requiredEndpointRefs = const [], @UuidValueConverter() this.consumerNodeId, required this.activeEnvironmentsOnly, required this.acceptedPeersOnly, required this.includeRouteHints, required this.requireAccessEvidence, final  List<String> accessEvidenceRefs = const [], this.limitEntries}): _requiredServicePackageNames = requiredServicePackageNames,_requiredEndpointRefs = requiredEndpointRefs,_accessEvidenceRefs = accessEvidenceRefs;
  factory _NetworkDiscoverExperienceTerritoryRequest.fromJson(Map<String, dynamic> json) => _$NetworkDiscoverExperienceTerritoryRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? requestId;
@override final  String experienceName;
 final  List<String> _requiredServicePackageNames;
@override@JsonKey() List<String> get requiredServicePackageNames {
  if (_requiredServicePackageNames is EqualUnmodifiableListView) return _requiredServicePackageNames;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_requiredServicePackageNames);
}

 final  List<String> _requiredEndpointRefs;
@override@JsonKey() List<String> get requiredEndpointRefs {
  if (_requiredEndpointRefs is EqualUnmodifiableListView) return _requiredEndpointRefs;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_requiredEndpointRefs);
}

@override@UuidValueConverter() final  UuidValue? consumerNodeId;
@override final  bool activeEnvironmentsOnly;
@override final  bool acceptedPeersOnly;
@override final  bool includeRouteHints;
@override final  bool requireAccessEvidence;
 final  List<String> _accessEvidenceRefs;
@override@JsonKey() List<String> get accessEvidenceRefs {
  if (_accessEvidenceRefs is EqualUnmodifiableListView) return _accessEvidenceRefs;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_accessEvidenceRefs);
}

@override final  int? limitEntries;

/// Create a copy of NetworkDiscoverExperienceTerritoryRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkDiscoverExperienceTerritoryRequestCopyWith<_NetworkDiscoverExperienceTerritoryRequest> get copyWith => __$NetworkDiscoverExperienceTerritoryRequestCopyWithImpl<_NetworkDiscoverExperienceTerritoryRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkDiscoverExperienceTerritoryRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkDiscoverExperienceTerritoryRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.experienceName, experienceName) || other.experienceName == experienceName)&&const DeepCollectionEquality().equals(other._requiredServicePackageNames, _requiredServicePackageNames)&&const DeepCollectionEquality().equals(other._requiredEndpointRefs, _requiredEndpointRefs)&&(identical(other.consumerNodeId, consumerNodeId) || other.consumerNodeId == consumerNodeId)&&(identical(other.activeEnvironmentsOnly, activeEnvironmentsOnly) || other.activeEnvironmentsOnly == activeEnvironmentsOnly)&&(identical(other.acceptedPeersOnly, acceptedPeersOnly) || other.acceptedPeersOnly == acceptedPeersOnly)&&(identical(other.includeRouteHints, includeRouteHints) || other.includeRouteHints == includeRouteHints)&&(identical(other.requireAccessEvidence, requireAccessEvidence) || other.requireAccessEvidence == requireAccessEvidence)&&const DeepCollectionEquality().equals(other._accessEvidenceRefs, _accessEvidenceRefs)&&(identical(other.limitEntries, limitEntries) || other.limitEntries == limitEntries));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,requestId,experienceName,const DeepCollectionEquality().hash(_requiredServicePackageNames),const DeepCollectionEquality().hash(_requiredEndpointRefs),consumerNodeId,activeEnvironmentsOnly,acceptedPeersOnly,includeRouteHints,requireAccessEvidence,const DeepCollectionEquality().hash(_accessEvidenceRefs),limitEntries);

@override
String toString() {
  return 'NetworkDiscoverExperienceTerritoryRequest.def(actorId: $actorId, requestId: $requestId, experienceName: $experienceName, requiredServicePackageNames: $requiredServicePackageNames, requiredEndpointRefs: $requiredEndpointRefs, consumerNodeId: $consumerNodeId, activeEnvironmentsOnly: $activeEnvironmentsOnly, acceptedPeersOnly: $acceptedPeersOnly, includeRouteHints: $includeRouteHints, requireAccessEvidence: $requireAccessEvidence, accessEvidenceRefs: $accessEvidenceRefs, limitEntries: $limitEntries)';
}


}

/// @nodoc
abstract mixin class _$NetworkDiscoverExperienceTerritoryRequestCopyWith<$Res> implements $NetworkDiscoverExperienceTerritoryRequestCopyWith<$Res> {
  factory _$NetworkDiscoverExperienceTerritoryRequestCopyWith(_NetworkDiscoverExperienceTerritoryRequest value, $Res Function(_NetworkDiscoverExperienceTerritoryRequest) _then) = __$NetworkDiscoverExperienceTerritoryRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? requestId, String experienceName, List<String> requiredServicePackageNames, List<String> requiredEndpointRefs,@UuidValueConverter() UuidValue? consumerNodeId, bool activeEnvironmentsOnly, bool acceptedPeersOnly, bool includeRouteHints, bool requireAccessEvidence, List<String> accessEvidenceRefs, int? limitEntries
});




}
/// @nodoc
class __$NetworkDiscoverExperienceTerritoryRequestCopyWithImpl<$Res>
    implements _$NetworkDiscoverExperienceTerritoryRequestCopyWith<$Res> {
  __$NetworkDiscoverExperienceTerritoryRequestCopyWithImpl(this._self, this._then);

  final _NetworkDiscoverExperienceTerritoryRequest _self;
  final $Res Function(_NetworkDiscoverExperienceTerritoryRequest) _then;

/// Create a copy of NetworkDiscoverExperienceTerritoryRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? requestId = freezed,Object? experienceName = null,Object? requiredServicePackageNames = null,Object? requiredEndpointRefs = null,Object? consumerNodeId = freezed,Object? activeEnvironmentsOnly = null,Object? acceptedPeersOnly = null,Object? includeRouteHints = null,Object? requireAccessEvidence = null,Object? accessEvidenceRefs = null,Object? limitEntries = freezed,}) {
  return _then(_NetworkDiscoverExperienceTerritoryRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,experienceName: null == experienceName ? _self.experienceName : experienceName // ignore: cast_nullable_to_non_nullable
as String,requiredServicePackageNames: null == requiredServicePackageNames ? _self._requiredServicePackageNames : requiredServicePackageNames // ignore: cast_nullable_to_non_nullable
as List<String>,requiredEndpointRefs: null == requiredEndpointRefs ? _self._requiredEndpointRefs : requiredEndpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,consumerNodeId: freezed == consumerNodeId ? _self.consumerNodeId : consumerNodeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,activeEnvironmentsOnly: null == activeEnvironmentsOnly ? _self.activeEnvironmentsOnly : activeEnvironmentsOnly // ignore: cast_nullable_to_non_nullable
as bool,acceptedPeersOnly: null == acceptedPeersOnly ? _self.acceptedPeersOnly : acceptedPeersOnly // ignore: cast_nullable_to_non_nullable
as bool,includeRouteHints: null == includeRouteHints ? _self.includeRouteHints : includeRouteHints // ignore: cast_nullable_to_non_nullable
as bool,requireAccessEvidence: null == requireAccessEvidence ? _self.requireAccessEvidence : requireAccessEvidence // ignore: cast_nullable_to_non_nullable
as bool,accessEvidenceRefs: null == accessEvidenceRefs ? _self._accessEvidenceRefs : accessEvidenceRefs // ignore: cast_nullable_to_non_nullable
as List<String>,limitEntries: freezed == limitEntries ? _self.limitEntries : limitEntries // ignore: cast_nullable_to_non_nullable
as int?,
  ));
}


}


/// @nodoc
mixin _$NetworkDiscoverExperienceTerritoryResponse {

@UuidValueConverter() UuidValue? get requestId; bool get success; String? get error; String? get experienceName; List<NetworkExperienceTerritoryEntry> get entries; String? get summary;
/// Create a copy of NetworkDiscoverExperienceTerritoryResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkDiscoverExperienceTerritoryResponseCopyWith<NetworkDiscoverExperienceTerritoryResponse> get copyWith => _$NetworkDiscoverExperienceTerritoryResponseCopyWithImpl<NetworkDiscoverExperienceTerritoryResponse>(this as NetworkDiscoverExperienceTerritoryResponse, _$identity);

  /// Serializes this NetworkDiscoverExperienceTerritoryResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkDiscoverExperienceTerritoryResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.experienceName, experienceName) || other.experienceName == experienceName)&&const DeepCollectionEquality().equals(other.entries, entries)&&(identical(other.summary, summary) || other.summary == summary));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,experienceName,const DeepCollectionEquality().hash(entries),summary);

@override
String toString() {
  return 'NetworkDiscoverExperienceTerritoryResponse(requestId: $requestId, success: $success, error: $error, experienceName: $experienceName, entries: $entries, summary: $summary)';
}


}

/// @nodoc
abstract mixin class $NetworkDiscoverExperienceTerritoryResponseCopyWith<$Res>  {
  factory $NetworkDiscoverExperienceTerritoryResponseCopyWith(NetworkDiscoverExperienceTerritoryResponse value, $Res Function(NetworkDiscoverExperienceTerritoryResponse) _then) = _$NetworkDiscoverExperienceTerritoryResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, String? experienceName, List<NetworkExperienceTerritoryEntry> entries, String? summary
});




}
/// @nodoc
class _$NetworkDiscoverExperienceTerritoryResponseCopyWithImpl<$Res>
    implements $NetworkDiscoverExperienceTerritoryResponseCopyWith<$Res> {
  _$NetworkDiscoverExperienceTerritoryResponseCopyWithImpl(this._self, this._then);

  final NetworkDiscoverExperienceTerritoryResponse _self;
  final $Res Function(NetworkDiscoverExperienceTerritoryResponse) _then;

/// Create a copy of NetworkDiscoverExperienceTerritoryResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? experienceName = freezed,Object? entries = null,Object? summary = freezed,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,experienceName: freezed == experienceName ? _self.experienceName : experienceName // ignore: cast_nullable_to_non_nullable
as String?,entries: null == entries ? _self.entries : entries // ignore: cast_nullable_to_non_nullable
as List<NetworkExperienceTerritoryEntry>,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkDiscoverExperienceTerritoryResponse].
extension NetworkDiscoverExperienceTerritoryResponsePatterns on NetworkDiscoverExperienceTerritoryResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkDiscoverExperienceTerritoryResponse value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkDiscoverExperienceTerritoryResponse() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkDiscoverExperienceTerritoryResponse value)  def,}){
final _that = this;
switch (_that) {
case _NetworkDiscoverExperienceTerritoryResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkDiscoverExperienceTerritoryResponse value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkDiscoverExperienceTerritoryResponse() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  String? experienceName,  List<NetworkExperienceTerritoryEntry> entries,  String? summary)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkDiscoverExperienceTerritoryResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.experienceName,_that.entries,_that.summary);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  String? experienceName,  List<NetworkExperienceTerritoryEntry> entries,  String? summary)  def,}) {final _that = this;
switch (_that) {
case _NetworkDiscoverExperienceTerritoryResponse():
return def(_that.requestId,_that.success,_that.error,_that.experienceName,_that.entries,_that.summary);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  String? experienceName,  List<NetworkExperienceTerritoryEntry> entries,  String? summary)?  def,}) {final _that = this;
switch (_that) {
case _NetworkDiscoverExperienceTerritoryResponse() when def != null:
return def(_that.requestId,_that.success,_that.error,_that.experienceName,_that.entries,_that.summary);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkDiscoverExperienceTerritoryResponse implements NetworkDiscoverExperienceTerritoryResponse {
   _NetworkDiscoverExperienceTerritoryResponse({@UuidValueConverter() this.requestId, required this.success, this.error, this.experienceName, final  List<NetworkExperienceTerritoryEntry> entries = const [], this.summary}): _entries = entries;
  factory _NetworkDiscoverExperienceTerritoryResponse.fromJson(Map<String, dynamic> json) => _$NetworkDiscoverExperienceTerritoryResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? error;
@override final  String? experienceName;
 final  List<NetworkExperienceTerritoryEntry> _entries;
@override@JsonKey() List<NetworkExperienceTerritoryEntry> get entries {
  if (_entries is EqualUnmodifiableListView) return _entries;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_entries);
}

@override final  String? summary;

/// Create a copy of NetworkDiscoverExperienceTerritoryResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkDiscoverExperienceTerritoryResponseCopyWith<_NetworkDiscoverExperienceTerritoryResponse> get copyWith => __$NetworkDiscoverExperienceTerritoryResponseCopyWithImpl<_NetworkDiscoverExperienceTerritoryResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkDiscoverExperienceTerritoryResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkDiscoverExperienceTerritoryResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.experienceName, experienceName) || other.experienceName == experienceName)&&const DeepCollectionEquality().equals(other._entries, _entries)&&(identical(other.summary, summary) || other.summary == summary));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,experienceName,const DeepCollectionEquality().hash(_entries),summary);

@override
String toString() {
  return 'NetworkDiscoverExperienceTerritoryResponse.def(requestId: $requestId, success: $success, error: $error, experienceName: $experienceName, entries: $entries, summary: $summary)';
}


}

/// @nodoc
abstract mixin class _$NetworkDiscoverExperienceTerritoryResponseCopyWith<$Res> implements $NetworkDiscoverExperienceTerritoryResponseCopyWith<$Res> {
  factory _$NetworkDiscoverExperienceTerritoryResponseCopyWith(_NetworkDiscoverExperienceTerritoryResponse value, $Res Function(_NetworkDiscoverExperienceTerritoryResponse) _then) = __$NetworkDiscoverExperienceTerritoryResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, String? experienceName, List<NetworkExperienceTerritoryEntry> entries, String? summary
});




}
/// @nodoc
class __$NetworkDiscoverExperienceTerritoryResponseCopyWithImpl<$Res>
    implements _$NetworkDiscoverExperienceTerritoryResponseCopyWith<$Res> {
  __$NetworkDiscoverExperienceTerritoryResponseCopyWithImpl(this._self, this._then);

  final _NetworkDiscoverExperienceTerritoryResponse _self;
  final $Res Function(_NetworkDiscoverExperienceTerritoryResponse) _then;

/// Create a copy of NetworkDiscoverExperienceTerritoryResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? experienceName = freezed,Object? entries = null,Object? summary = freezed,}) {
  return _then(_NetworkDiscoverExperienceTerritoryResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,experienceName: freezed == experienceName ? _self.experienceName : experienceName // ignore: cast_nullable_to_non_nullable
as String?,entries: null == entries ? _self._entries : entries // ignore: cast_nullable_to_non_nullable
as List<NetworkExperienceTerritoryEntry>,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

// dart format on
