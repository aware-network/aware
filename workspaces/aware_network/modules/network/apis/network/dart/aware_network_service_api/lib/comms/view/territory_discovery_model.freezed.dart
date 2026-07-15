// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'territory_discovery_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$NetworkTerritoryNodeRouteViewStateV1 {

 String? get nodeId; String? get publicKey; String? get hostname; int? get port; String? get baseUrl; String get status; String? get lastSeenAt;
/// Create a copy of NetworkTerritoryNodeRouteViewStateV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkTerritoryNodeRouteViewStateV1CopyWith<NetworkTerritoryNodeRouteViewStateV1> get copyWith => _$NetworkTerritoryNodeRouteViewStateV1CopyWithImpl<NetworkTerritoryNodeRouteViewStateV1>(this as NetworkTerritoryNodeRouteViewStateV1, _$identity);

  /// Serializes this NetworkTerritoryNodeRouteViewStateV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkTerritoryNodeRouteViewStateV1&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.publicKey, publicKey) || other.publicKey == publicKey)&&(identical(other.hostname, hostname) || other.hostname == hostname)&&(identical(other.port, port) || other.port == port)&&(identical(other.baseUrl, baseUrl) || other.baseUrl == baseUrl)&&(identical(other.status, status) || other.status == status)&&(identical(other.lastSeenAt, lastSeenAt) || other.lastSeenAt == lastSeenAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,nodeId,publicKey,hostname,port,baseUrl,status,lastSeenAt);

@override
String toString() {
  return 'NetworkTerritoryNodeRouteViewStateV1(nodeId: $nodeId, publicKey: $publicKey, hostname: $hostname, port: $port, baseUrl: $baseUrl, status: $status, lastSeenAt: $lastSeenAt)';
}


}

/// @nodoc
abstract mixin class $NetworkTerritoryNodeRouteViewStateV1CopyWith<$Res>  {
  factory $NetworkTerritoryNodeRouteViewStateV1CopyWith(NetworkTerritoryNodeRouteViewStateV1 value, $Res Function(NetworkTerritoryNodeRouteViewStateV1) _then) = _$NetworkTerritoryNodeRouteViewStateV1CopyWithImpl;
@useResult
$Res call({
 String? nodeId, String? publicKey, String? hostname, int? port, String? baseUrl, String status, String? lastSeenAt
});




}
/// @nodoc
class _$NetworkTerritoryNodeRouteViewStateV1CopyWithImpl<$Res>
    implements $NetworkTerritoryNodeRouteViewStateV1CopyWith<$Res> {
  _$NetworkTerritoryNodeRouteViewStateV1CopyWithImpl(this._self, this._then);

  final NetworkTerritoryNodeRouteViewStateV1 _self;
  final $Res Function(NetworkTerritoryNodeRouteViewStateV1) _then;

/// Create a copy of NetworkTerritoryNodeRouteViewStateV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? nodeId = freezed,Object? publicKey = freezed,Object? hostname = freezed,Object? port = freezed,Object? baseUrl = freezed,Object? status = null,Object? lastSeenAt = freezed,}) {
  return _then(_self.copyWith(
nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as String?,publicKey: freezed == publicKey ? _self.publicKey : publicKey // ignore: cast_nullable_to_non_nullable
as String?,hostname: freezed == hostname ? _self.hostname : hostname // ignore: cast_nullable_to_non_nullable
as String?,port: freezed == port ? _self.port : port // ignore: cast_nullable_to_non_nullable
as int?,baseUrl: freezed == baseUrl ? _self.baseUrl : baseUrl // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,lastSeenAt: freezed == lastSeenAt ? _self.lastSeenAt : lastSeenAt // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkTerritoryNodeRouteViewStateV1].
extension NetworkTerritoryNodeRouteViewStateV1Patterns on NetworkTerritoryNodeRouteViewStateV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkTerritoryNodeRouteViewStateV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkTerritoryNodeRouteViewStateV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkTerritoryNodeRouteViewStateV1 value)  def,}){
final _that = this;
switch (_that) {
case _NetworkTerritoryNodeRouteViewStateV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkTerritoryNodeRouteViewStateV1 value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkTerritoryNodeRouteViewStateV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String? nodeId,  String? publicKey,  String? hostname,  int? port,  String? baseUrl,  String status,  String? lastSeenAt)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkTerritoryNodeRouteViewStateV1() when def != null:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String? nodeId,  String? publicKey,  String? hostname,  int? port,  String? baseUrl,  String status,  String? lastSeenAt)  def,}) {final _that = this;
switch (_that) {
case _NetworkTerritoryNodeRouteViewStateV1():
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String? nodeId,  String? publicKey,  String? hostname,  int? port,  String? baseUrl,  String status,  String? lastSeenAt)?  def,}) {final _that = this;
switch (_that) {
case _NetworkTerritoryNodeRouteViewStateV1() when def != null:
return def(_that.nodeId,_that.publicKey,_that.hostname,_that.port,_that.baseUrl,_that.status,_that.lastSeenAt);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkTerritoryNodeRouteViewStateV1 implements NetworkTerritoryNodeRouteViewStateV1 {
   _NetworkTerritoryNodeRouteViewStateV1({this.nodeId, this.publicKey, this.hostname, this.port, this.baseUrl, required this.status, this.lastSeenAt});
  factory _NetworkTerritoryNodeRouteViewStateV1.fromJson(Map<String, dynamic> json) => _$NetworkTerritoryNodeRouteViewStateV1FromJson(json);

@override final  String? nodeId;
@override final  String? publicKey;
@override final  String? hostname;
@override final  int? port;
@override final  String? baseUrl;
@override final  String status;
@override final  String? lastSeenAt;

/// Create a copy of NetworkTerritoryNodeRouteViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkTerritoryNodeRouteViewStateV1CopyWith<_NetworkTerritoryNodeRouteViewStateV1> get copyWith => __$NetworkTerritoryNodeRouteViewStateV1CopyWithImpl<_NetworkTerritoryNodeRouteViewStateV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkTerritoryNodeRouteViewStateV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkTerritoryNodeRouteViewStateV1&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.publicKey, publicKey) || other.publicKey == publicKey)&&(identical(other.hostname, hostname) || other.hostname == hostname)&&(identical(other.port, port) || other.port == port)&&(identical(other.baseUrl, baseUrl) || other.baseUrl == baseUrl)&&(identical(other.status, status) || other.status == status)&&(identical(other.lastSeenAt, lastSeenAt) || other.lastSeenAt == lastSeenAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,nodeId,publicKey,hostname,port,baseUrl,status,lastSeenAt);

@override
String toString() {
  return 'NetworkTerritoryNodeRouteViewStateV1.def(nodeId: $nodeId, publicKey: $publicKey, hostname: $hostname, port: $port, baseUrl: $baseUrl, status: $status, lastSeenAt: $lastSeenAt)';
}


}

/// @nodoc
abstract mixin class _$NetworkTerritoryNodeRouteViewStateV1CopyWith<$Res> implements $NetworkTerritoryNodeRouteViewStateV1CopyWith<$Res> {
  factory _$NetworkTerritoryNodeRouteViewStateV1CopyWith(_NetworkTerritoryNodeRouteViewStateV1 value, $Res Function(_NetworkTerritoryNodeRouteViewStateV1) _then) = __$NetworkTerritoryNodeRouteViewStateV1CopyWithImpl;
@override @useResult
$Res call({
 String? nodeId, String? publicKey, String? hostname, int? port, String? baseUrl, String status, String? lastSeenAt
});




}
/// @nodoc
class __$NetworkTerritoryNodeRouteViewStateV1CopyWithImpl<$Res>
    implements _$NetworkTerritoryNodeRouteViewStateV1CopyWith<$Res> {
  __$NetworkTerritoryNodeRouteViewStateV1CopyWithImpl(this._self, this._then);

  final _NetworkTerritoryNodeRouteViewStateV1 _self;
  final $Res Function(_NetworkTerritoryNodeRouteViewStateV1) _then;

/// Create a copy of NetworkTerritoryNodeRouteViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? nodeId = freezed,Object? publicKey = freezed,Object? hostname = freezed,Object? port = freezed,Object? baseUrl = freezed,Object? status = null,Object? lastSeenAt = freezed,}) {
  return _then(_NetworkTerritoryNodeRouteViewStateV1(
nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as String?,publicKey: freezed == publicKey ? _self.publicKey : publicKey // ignore: cast_nullable_to_non_nullable
as String?,hostname: freezed == hostname ? _self.hostname : hostname // ignore: cast_nullable_to_non_nullable
as String?,port: freezed == port ? _self.port : port // ignore: cast_nullable_to_non_nullable
as int?,baseUrl: freezed == baseUrl ? _self.baseUrl : baseUrl // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,lastSeenAt: freezed == lastSeenAt ? _self.lastSeenAt : lastSeenAt // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$NetworkTerritoryEnvironmentViewStateV1 {

 String? get nodeId; String? get environmentId; String? get environmentKey; String? get environmentTitle; String get role; bool get isActive; int get priority; String get status; List<String> get experienceNames; String? get environmentConfigId; String? get environmentConfigKey;
/// Create a copy of NetworkTerritoryEnvironmentViewStateV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkTerritoryEnvironmentViewStateV1CopyWith<NetworkTerritoryEnvironmentViewStateV1> get copyWith => _$NetworkTerritoryEnvironmentViewStateV1CopyWithImpl<NetworkTerritoryEnvironmentViewStateV1>(this as NetworkTerritoryEnvironmentViewStateV1, _$identity);

  /// Serializes this NetworkTerritoryEnvironmentViewStateV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkTerritoryEnvironmentViewStateV1&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentKey, environmentKey) || other.environmentKey == environmentKey)&&(identical(other.environmentTitle, environmentTitle) || other.environmentTitle == environmentTitle)&&(identical(other.role, role) || other.role == role)&&(identical(other.isActive, isActive) || other.isActive == isActive)&&(identical(other.priority, priority) || other.priority == priority)&&(identical(other.status, status) || other.status == status)&&const DeepCollectionEquality().equals(other.experienceNames, experienceNames)&&(identical(other.environmentConfigId, environmentConfigId) || other.environmentConfigId == environmentConfigId)&&(identical(other.environmentConfigKey, environmentConfigKey) || other.environmentConfigKey == environmentConfigKey));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,nodeId,environmentId,environmentKey,environmentTitle,role,isActive,priority,status,const DeepCollectionEquality().hash(experienceNames),environmentConfigId,environmentConfigKey);

@override
String toString() {
  return 'NetworkTerritoryEnvironmentViewStateV1(nodeId: $nodeId, environmentId: $environmentId, environmentKey: $environmentKey, environmentTitle: $environmentTitle, role: $role, isActive: $isActive, priority: $priority, status: $status, experienceNames: $experienceNames, environmentConfigId: $environmentConfigId, environmentConfigKey: $environmentConfigKey)';
}


}

/// @nodoc
abstract mixin class $NetworkTerritoryEnvironmentViewStateV1CopyWith<$Res>  {
  factory $NetworkTerritoryEnvironmentViewStateV1CopyWith(NetworkTerritoryEnvironmentViewStateV1 value, $Res Function(NetworkTerritoryEnvironmentViewStateV1) _then) = _$NetworkTerritoryEnvironmentViewStateV1CopyWithImpl;
@useResult
$Res call({
 String? nodeId, String? environmentId, String? environmentKey, String? environmentTitle, String role, bool isActive, int priority, String status, List<String> experienceNames, String? environmentConfigId, String? environmentConfigKey
});




}
/// @nodoc
class _$NetworkTerritoryEnvironmentViewStateV1CopyWithImpl<$Res>
    implements $NetworkTerritoryEnvironmentViewStateV1CopyWith<$Res> {
  _$NetworkTerritoryEnvironmentViewStateV1CopyWithImpl(this._self, this._then);

  final NetworkTerritoryEnvironmentViewStateV1 _self;
  final $Res Function(NetworkTerritoryEnvironmentViewStateV1) _then;

/// Create a copy of NetworkTerritoryEnvironmentViewStateV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? nodeId = freezed,Object? environmentId = freezed,Object? environmentKey = freezed,Object? environmentTitle = freezed,Object? role = null,Object? isActive = null,Object? priority = null,Object? status = null,Object? experienceNames = null,Object? environmentConfigId = freezed,Object? environmentConfigKey = freezed,}) {
  return _then(_self.copyWith(
nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as String?,environmentId: freezed == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as String?,environmentKey: freezed == environmentKey ? _self.environmentKey : environmentKey // ignore: cast_nullable_to_non_nullable
as String?,environmentTitle: freezed == environmentTitle ? _self.environmentTitle : environmentTitle // ignore: cast_nullable_to_non_nullable
as String?,role: null == role ? _self.role : role // ignore: cast_nullable_to_non_nullable
as String,isActive: null == isActive ? _self.isActive : isActive // ignore: cast_nullable_to_non_nullable
as bool,priority: null == priority ? _self.priority : priority // ignore: cast_nullable_to_non_nullable
as int,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,experienceNames: null == experienceNames ? _self.experienceNames : experienceNames // ignore: cast_nullable_to_non_nullable
as List<String>,environmentConfigId: freezed == environmentConfigId ? _self.environmentConfigId : environmentConfigId // ignore: cast_nullable_to_non_nullable
as String?,environmentConfigKey: freezed == environmentConfigKey ? _self.environmentConfigKey : environmentConfigKey // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkTerritoryEnvironmentViewStateV1].
extension NetworkTerritoryEnvironmentViewStateV1Patterns on NetworkTerritoryEnvironmentViewStateV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkTerritoryEnvironmentViewStateV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkTerritoryEnvironmentViewStateV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkTerritoryEnvironmentViewStateV1 value)  def,}){
final _that = this;
switch (_that) {
case _NetworkTerritoryEnvironmentViewStateV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkTerritoryEnvironmentViewStateV1 value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkTerritoryEnvironmentViewStateV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String? nodeId,  String? environmentId,  String? environmentKey,  String? environmentTitle,  String role,  bool isActive,  int priority,  String status,  List<String> experienceNames,  String? environmentConfigId,  String? environmentConfigKey)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkTerritoryEnvironmentViewStateV1() when def != null:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String? nodeId,  String? environmentId,  String? environmentKey,  String? environmentTitle,  String role,  bool isActive,  int priority,  String status,  List<String> experienceNames,  String? environmentConfigId,  String? environmentConfigKey)  def,}) {final _that = this;
switch (_that) {
case _NetworkTerritoryEnvironmentViewStateV1():
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String? nodeId,  String? environmentId,  String? environmentKey,  String? environmentTitle,  String role,  bool isActive,  int priority,  String status,  List<String> experienceNames,  String? environmentConfigId,  String? environmentConfigKey)?  def,}) {final _that = this;
switch (_that) {
case _NetworkTerritoryEnvironmentViewStateV1() when def != null:
return def(_that.nodeId,_that.environmentId,_that.environmentKey,_that.environmentTitle,_that.role,_that.isActive,_that.priority,_that.status,_that.experienceNames,_that.environmentConfigId,_that.environmentConfigKey);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkTerritoryEnvironmentViewStateV1 implements NetworkTerritoryEnvironmentViewStateV1 {
   _NetworkTerritoryEnvironmentViewStateV1({this.nodeId, this.environmentId, this.environmentKey, this.environmentTitle, required this.role, required this.isActive, required this.priority, required this.status, final  List<String> experienceNames = const [], this.environmentConfigId, this.environmentConfigKey}): _experienceNames = experienceNames;
  factory _NetworkTerritoryEnvironmentViewStateV1.fromJson(Map<String, dynamic> json) => _$NetworkTerritoryEnvironmentViewStateV1FromJson(json);

@override final  String? nodeId;
@override final  String? environmentId;
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

@override final  String? environmentConfigId;
@override final  String? environmentConfigKey;

/// Create a copy of NetworkTerritoryEnvironmentViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkTerritoryEnvironmentViewStateV1CopyWith<_NetworkTerritoryEnvironmentViewStateV1> get copyWith => __$NetworkTerritoryEnvironmentViewStateV1CopyWithImpl<_NetworkTerritoryEnvironmentViewStateV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkTerritoryEnvironmentViewStateV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkTerritoryEnvironmentViewStateV1&&(identical(other.nodeId, nodeId) || other.nodeId == nodeId)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentKey, environmentKey) || other.environmentKey == environmentKey)&&(identical(other.environmentTitle, environmentTitle) || other.environmentTitle == environmentTitle)&&(identical(other.role, role) || other.role == role)&&(identical(other.isActive, isActive) || other.isActive == isActive)&&(identical(other.priority, priority) || other.priority == priority)&&(identical(other.status, status) || other.status == status)&&const DeepCollectionEquality().equals(other._experienceNames, _experienceNames)&&(identical(other.environmentConfigId, environmentConfigId) || other.environmentConfigId == environmentConfigId)&&(identical(other.environmentConfigKey, environmentConfigKey) || other.environmentConfigKey == environmentConfigKey));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,nodeId,environmentId,environmentKey,environmentTitle,role,isActive,priority,status,const DeepCollectionEquality().hash(_experienceNames),environmentConfigId,environmentConfigKey);

@override
String toString() {
  return 'NetworkTerritoryEnvironmentViewStateV1.def(nodeId: $nodeId, environmentId: $environmentId, environmentKey: $environmentKey, environmentTitle: $environmentTitle, role: $role, isActive: $isActive, priority: $priority, status: $status, experienceNames: $experienceNames, environmentConfigId: $environmentConfigId, environmentConfigKey: $environmentConfigKey)';
}


}

/// @nodoc
abstract mixin class _$NetworkTerritoryEnvironmentViewStateV1CopyWith<$Res> implements $NetworkTerritoryEnvironmentViewStateV1CopyWith<$Res> {
  factory _$NetworkTerritoryEnvironmentViewStateV1CopyWith(_NetworkTerritoryEnvironmentViewStateV1 value, $Res Function(_NetworkTerritoryEnvironmentViewStateV1) _then) = __$NetworkTerritoryEnvironmentViewStateV1CopyWithImpl;
@override @useResult
$Res call({
 String? nodeId, String? environmentId, String? environmentKey, String? environmentTitle, String role, bool isActive, int priority, String status, List<String> experienceNames, String? environmentConfigId, String? environmentConfigKey
});




}
/// @nodoc
class __$NetworkTerritoryEnvironmentViewStateV1CopyWithImpl<$Res>
    implements _$NetworkTerritoryEnvironmentViewStateV1CopyWith<$Res> {
  __$NetworkTerritoryEnvironmentViewStateV1CopyWithImpl(this._self, this._then);

  final _NetworkTerritoryEnvironmentViewStateV1 _self;
  final $Res Function(_NetworkTerritoryEnvironmentViewStateV1) _then;

/// Create a copy of NetworkTerritoryEnvironmentViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? nodeId = freezed,Object? environmentId = freezed,Object? environmentKey = freezed,Object? environmentTitle = freezed,Object? role = null,Object? isActive = null,Object? priority = null,Object? status = null,Object? experienceNames = null,Object? environmentConfigId = freezed,Object? environmentConfigKey = freezed,}) {
  return _then(_NetworkTerritoryEnvironmentViewStateV1(
nodeId: freezed == nodeId ? _self.nodeId : nodeId // ignore: cast_nullable_to_non_nullable
as String?,environmentId: freezed == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as String?,environmentKey: freezed == environmentKey ? _self.environmentKey : environmentKey // ignore: cast_nullable_to_non_nullable
as String?,environmentTitle: freezed == environmentTitle ? _self.environmentTitle : environmentTitle // ignore: cast_nullable_to_non_nullable
as String?,role: null == role ? _self.role : role // ignore: cast_nullable_to_non_nullable
as String,isActive: null == isActive ? _self.isActive : isActive // ignore: cast_nullable_to_non_nullable
as bool,priority: null == priority ? _self.priority : priority // ignore: cast_nullable_to_non_nullable
as int,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,experienceNames: null == experienceNames ? _self._experienceNames : experienceNames // ignore: cast_nullable_to_non_nullable
as List<String>,environmentConfigId: freezed == environmentConfigId ? _self.environmentConfigId : environmentConfigId // ignore: cast_nullable_to_non_nullable
as String?,environmentConfigKey: freezed == environmentConfigKey ? _self.environmentConfigKey : environmentConfigKey // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$NetworkTerritoryHostedServiceViewStateV1 {

 String? get serviceId; String? get serviceName; List<String> get servicePackageNames; List<String> get endpointRefs; List<String> get streamEndpointRefs; String? get hostId; String? get hostVersion; String? get protocolVersion; bool get supportsStreamEvents;
/// Create a copy of NetworkTerritoryHostedServiceViewStateV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkTerritoryHostedServiceViewStateV1CopyWith<NetworkTerritoryHostedServiceViewStateV1> get copyWith => _$NetworkTerritoryHostedServiceViewStateV1CopyWithImpl<NetworkTerritoryHostedServiceViewStateV1>(this as NetworkTerritoryHostedServiceViewStateV1, _$identity);

  /// Serializes this NetworkTerritoryHostedServiceViewStateV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkTerritoryHostedServiceViewStateV1&&(identical(other.serviceId, serviceId) || other.serviceId == serviceId)&&(identical(other.serviceName, serviceName) || other.serviceName == serviceName)&&const DeepCollectionEquality().equals(other.servicePackageNames, servicePackageNames)&&const DeepCollectionEquality().equals(other.endpointRefs, endpointRefs)&&const DeepCollectionEquality().equals(other.streamEndpointRefs, streamEndpointRefs)&&(identical(other.hostId, hostId) || other.hostId == hostId)&&(identical(other.hostVersion, hostVersion) || other.hostVersion == hostVersion)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.supportsStreamEvents, supportsStreamEvents) || other.supportsStreamEvents == supportsStreamEvents));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,serviceId,serviceName,const DeepCollectionEquality().hash(servicePackageNames),const DeepCollectionEquality().hash(endpointRefs),const DeepCollectionEquality().hash(streamEndpointRefs),hostId,hostVersion,protocolVersion,supportsStreamEvents);

@override
String toString() {
  return 'NetworkTerritoryHostedServiceViewStateV1(serviceId: $serviceId, serviceName: $serviceName, servicePackageNames: $servicePackageNames, endpointRefs: $endpointRefs, streamEndpointRefs: $streamEndpointRefs, hostId: $hostId, hostVersion: $hostVersion, protocolVersion: $protocolVersion, supportsStreamEvents: $supportsStreamEvents)';
}


}

/// @nodoc
abstract mixin class $NetworkTerritoryHostedServiceViewStateV1CopyWith<$Res>  {
  factory $NetworkTerritoryHostedServiceViewStateV1CopyWith(NetworkTerritoryHostedServiceViewStateV1 value, $Res Function(NetworkTerritoryHostedServiceViewStateV1) _then) = _$NetworkTerritoryHostedServiceViewStateV1CopyWithImpl;
@useResult
$Res call({
 String? serviceId, String? serviceName, List<String> servicePackageNames, List<String> endpointRefs, List<String> streamEndpointRefs, String? hostId, String? hostVersion, String? protocolVersion, bool supportsStreamEvents
});




}
/// @nodoc
class _$NetworkTerritoryHostedServiceViewStateV1CopyWithImpl<$Res>
    implements $NetworkTerritoryHostedServiceViewStateV1CopyWith<$Res> {
  _$NetworkTerritoryHostedServiceViewStateV1CopyWithImpl(this._self, this._then);

  final NetworkTerritoryHostedServiceViewStateV1 _self;
  final $Res Function(NetworkTerritoryHostedServiceViewStateV1) _then;

/// Create a copy of NetworkTerritoryHostedServiceViewStateV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? serviceId = freezed,Object? serviceName = freezed,Object? servicePackageNames = null,Object? endpointRefs = null,Object? streamEndpointRefs = null,Object? hostId = freezed,Object? hostVersion = freezed,Object? protocolVersion = freezed,Object? supportsStreamEvents = null,}) {
  return _then(_self.copyWith(
serviceId: freezed == serviceId ? _self.serviceId : serviceId // ignore: cast_nullable_to_non_nullable
as String?,serviceName: freezed == serviceName ? _self.serviceName : serviceName // ignore: cast_nullable_to_non_nullable
as String?,servicePackageNames: null == servicePackageNames ? _self.servicePackageNames : servicePackageNames // ignore: cast_nullable_to_non_nullable
as List<String>,endpointRefs: null == endpointRefs ? _self.endpointRefs : endpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,streamEndpointRefs: null == streamEndpointRefs ? _self.streamEndpointRefs : streamEndpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,hostId: freezed == hostId ? _self.hostId : hostId // ignore: cast_nullable_to_non_nullable
as String?,hostVersion: freezed == hostVersion ? _self.hostVersion : hostVersion // ignore: cast_nullable_to_non_nullable
as String?,protocolVersion: freezed == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as String?,supportsStreamEvents: null == supportsStreamEvents ? _self.supportsStreamEvents : supportsStreamEvents // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkTerritoryHostedServiceViewStateV1].
extension NetworkTerritoryHostedServiceViewStateV1Patterns on NetworkTerritoryHostedServiceViewStateV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkTerritoryHostedServiceViewStateV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkTerritoryHostedServiceViewStateV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkTerritoryHostedServiceViewStateV1 value)  def,}){
final _that = this;
switch (_that) {
case _NetworkTerritoryHostedServiceViewStateV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkTerritoryHostedServiceViewStateV1 value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkTerritoryHostedServiceViewStateV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String? serviceId,  String? serviceName,  List<String> servicePackageNames,  List<String> endpointRefs,  List<String> streamEndpointRefs,  String? hostId,  String? hostVersion,  String? protocolVersion,  bool supportsStreamEvents)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkTerritoryHostedServiceViewStateV1() when def != null:
return def(_that.serviceId,_that.serviceName,_that.servicePackageNames,_that.endpointRefs,_that.streamEndpointRefs,_that.hostId,_that.hostVersion,_that.protocolVersion,_that.supportsStreamEvents);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String? serviceId,  String? serviceName,  List<String> servicePackageNames,  List<String> endpointRefs,  List<String> streamEndpointRefs,  String? hostId,  String? hostVersion,  String? protocolVersion,  bool supportsStreamEvents)  def,}) {final _that = this;
switch (_that) {
case _NetworkTerritoryHostedServiceViewStateV1():
return def(_that.serviceId,_that.serviceName,_that.servicePackageNames,_that.endpointRefs,_that.streamEndpointRefs,_that.hostId,_that.hostVersion,_that.protocolVersion,_that.supportsStreamEvents);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String? serviceId,  String? serviceName,  List<String> servicePackageNames,  List<String> endpointRefs,  List<String> streamEndpointRefs,  String? hostId,  String? hostVersion,  String? protocolVersion,  bool supportsStreamEvents)?  def,}) {final _that = this;
switch (_that) {
case _NetworkTerritoryHostedServiceViewStateV1() when def != null:
return def(_that.serviceId,_that.serviceName,_that.servicePackageNames,_that.endpointRefs,_that.streamEndpointRefs,_that.hostId,_that.hostVersion,_that.protocolVersion,_that.supportsStreamEvents);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkTerritoryHostedServiceViewStateV1 implements NetworkTerritoryHostedServiceViewStateV1 {
   _NetworkTerritoryHostedServiceViewStateV1({this.serviceId, this.serviceName, final  List<String> servicePackageNames = const [], final  List<String> endpointRefs = const [], final  List<String> streamEndpointRefs = const [], this.hostId, this.hostVersion, this.protocolVersion, required this.supportsStreamEvents}): _servicePackageNames = servicePackageNames,_endpointRefs = endpointRefs,_streamEndpointRefs = streamEndpointRefs;
  factory _NetworkTerritoryHostedServiceViewStateV1.fromJson(Map<String, dynamic> json) => _$NetworkTerritoryHostedServiceViewStateV1FromJson(json);

@override final  String? serviceId;
@override final  String? serviceName;
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

@override final  String? hostId;
@override final  String? hostVersion;
@override final  String? protocolVersion;
@override final  bool supportsStreamEvents;

/// Create a copy of NetworkTerritoryHostedServiceViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkTerritoryHostedServiceViewStateV1CopyWith<_NetworkTerritoryHostedServiceViewStateV1> get copyWith => __$NetworkTerritoryHostedServiceViewStateV1CopyWithImpl<_NetworkTerritoryHostedServiceViewStateV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkTerritoryHostedServiceViewStateV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkTerritoryHostedServiceViewStateV1&&(identical(other.serviceId, serviceId) || other.serviceId == serviceId)&&(identical(other.serviceName, serviceName) || other.serviceName == serviceName)&&const DeepCollectionEquality().equals(other._servicePackageNames, _servicePackageNames)&&const DeepCollectionEquality().equals(other._endpointRefs, _endpointRefs)&&const DeepCollectionEquality().equals(other._streamEndpointRefs, _streamEndpointRefs)&&(identical(other.hostId, hostId) || other.hostId == hostId)&&(identical(other.hostVersion, hostVersion) || other.hostVersion == hostVersion)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.supportsStreamEvents, supportsStreamEvents) || other.supportsStreamEvents == supportsStreamEvents));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,serviceId,serviceName,const DeepCollectionEquality().hash(_servicePackageNames),const DeepCollectionEquality().hash(_endpointRefs),const DeepCollectionEquality().hash(_streamEndpointRefs),hostId,hostVersion,protocolVersion,supportsStreamEvents);

@override
String toString() {
  return 'NetworkTerritoryHostedServiceViewStateV1.def(serviceId: $serviceId, serviceName: $serviceName, servicePackageNames: $servicePackageNames, endpointRefs: $endpointRefs, streamEndpointRefs: $streamEndpointRefs, hostId: $hostId, hostVersion: $hostVersion, protocolVersion: $protocolVersion, supportsStreamEvents: $supportsStreamEvents)';
}


}

/// @nodoc
abstract mixin class _$NetworkTerritoryHostedServiceViewStateV1CopyWith<$Res> implements $NetworkTerritoryHostedServiceViewStateV1CopyWith<$Res> {
  factory _$NetworkTerritoryHostedServiceViewStateV1CopyWith(_NetworkTerritoryHostedServiceViewStateV1 value, $Res Function(_NetworkTerritoryHostedServiceViewStateV1) _then) = __$NetworkTerritoryHostedServiceViewStateV1CopyWithImpl;
@override @useResult
$Res call({
 String? serviceId, String? serviceName, List<String> servicePackageNames, List<String> endpointRefs, List<String> streamEndpointRefs, String? hostId, String? hostVersion, String? protocolVersion, bool supportsStreamEvents
});




}
/// @nodoc
class __$NetworkTerritoryHostedServiceViewStateV1CopyWithImpl<$Res>
    implements _$NetworkTerritoryHostedServiceViewStateV1CopyWith<$Res> {
  __$NetworkTerritoryHostedServiceViewStateV1CopyWithImpl(this._self, this._then);

  final _NetworkTerritoryHostedServiceViewStateV1 _self;
  final $Res Function(_NetworkTerritoryHostedServiceViewStateV1) _then;

/// Create a copy of NetworkTerritoryHostedServiceViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? serviceId = freezed,Object? serviceName = freezed,Object? servicePackageNames = null,Object? endpointRefs = null,Object? streamEndpointRefs = null,Object? hostId = freezed,Object? hostVersion = freezed,Object? protocolVersion = freezed,Object? supportsStreamEvents = null,}) {
  return _then(_NetworkTerritoryHostedServiceViewStateV1(
serviceId: freezed == serviceId ? _self.serviceId : serviceId // ignore: cast_nullable_to_non_nullable
as String?,serviceName: freezed == serviceName ? _self.serviceName : serviceName // ignore: cast_nullable_to_non_nullable
as String?,servicePackageNames: null == servicePackageNames ? _self._servicePackageNames : servicePackageNames // ignore: cast_nullable_to_non_nullable
as List<String>,endpointRefs: null == endpointRefs ? _self._endpointRefs : endpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,streamEndpointRefs: null == streamEndpointRefs ? _self._streamEndpointRefs : streamEndpointRefs // ignore: cast_nullable_to_non_nullable
as List<String>,hostId: freezed == hostId ? _self.hostId : hostId // ignore: cast_nullable_to_non_nullable
as String?,hostVersion: freezed == hostVersion ? _self.hostVersion : hostVersion // ignore: cast_nullable_to_non_nullable
as String?,protocolVersion: freezed == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as String?,supportsStreamEvents: null == supportsStreamEvents ? _self.supportsStreamEvents : supportsStreamEvents // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}


}


/// @nodoc
mixin _$NetworkTerritoryPeerViewStateV1 {

 String? get edgeId; String? get sourceNodeId; String? get targetNodeId; String? get peerNodeId; String? get peerBaseUrl; String get direction; String get status; double get trustScore; String? get connectedAt; String? get lastPingAt;
/// Create a copy of NetworkTerritoryPeerViewStateV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkTerritoryPeerViewStateV1CopyWith<NetworkTerritoryPeerViewStateV1> get copyWith => _$NetworkTerritoryPeerViewStateV1CopyWithImpl<NetworkTerritoryPeerViewStateV1>(this as NetworkTerritoryPeerViewStateV1, _$identity);

  /// Serializes this NetworkTerritoryPeerViewStateV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkTerritoryPeerViewStateV1&&(identical(other.edgeId, edgeId) || other.edgeId == edgeId)&&(identical(other.sourceNodeId, sourceNodeId) || other.sourceNodeId == sourceNodeId)&&(identical(other.targetNodeId, targetNodeId) || other.targetNodeId == targetNodeId)&&(identical(other.peerNodeId, peerNodeId) || other.peerNodeId == peerNodeId)&&(identical(other.peerBaseUrl, peerBaseUrl) || other.peerBaseUrl == peerBaseUrl)&&(identical(other.direction, direction) || other.direction == direction)&&(identical(other.status, status) || other.status == status)&&(identical(other.trustScore, trustScore) || other.trustScore == trustScore)&&(identical(other.connectedAt, connectedAt) || other.connectedAt == connectedAt)&&(identical(other.lastPingAt, lastPingAt) || other.lastPingAt == lastPingAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,edgeId,sourceNodeId,targetNodeId,peerNodeId,peerBaseUrl,direction,status,trustScore,connectedAt,lastPingAt);

@override
String toString() {
  return 'NetworkTerritoryPeerViewStateV1(edgeId: $edgeId, sourceNodeId: $sourceNodeId, targetNodeId: $targetNodeId, peerNodeId: $peerNodeId, peerBaseUrl: $peerBaseUrl, direction: $direction, status: $status, trustScore: $trustScore, connectedAt: $connectedAt, lastPingAt: $lastPingAt)';
}


}

/// @nodoc
abstract mixin class $NetworkTerritoryPeerViewStateV1CopyWith<$Res>  {
  factory $NetworkTerritoryPeerViewStateV1CopyWith(NetworkTerritoryPeerViewStateV1 value, $Res Function(NetworkTerritoryPeerViewStateV1) _then) = _$NetworkTerritoryPeerViewStateV1CopyWithImpl;
@useResult
$Res call({
 String? edgeId, String? sourceNodeId, String? targetNodeId, String? peerNodeId, String? peerBaseUrl, String direction, String status, double trustScore, String? connectedAt, String? lastPingAt
});




}
/// @nodoc
class _$NetworkTerritoryPeerViewStateV1CopyWithImpl<$Res>
    implements $NetworkTerritoryPeerViewStateV1CopyWith<$Res> {
  _$NetworkTerritoryPeerViewStateV1CopyWithImpl(this._self, this._then);

  final NetworkTerritoryPeerViewStateV1 _self;
  final $Res Function(NetworkTerritoryPeerViewStateV1) _then;

/// Create a copy of NetworkTerritoryPeerViewStateV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? edgeId = freezed,Object? sourceNodeId = freezed,Object? targetNodeId = freezed,Object? peerNodeId = freezed,Object? peerBaseUrl = freezed,Object? direction = null,Object? status = null,Object? trustScore = null,Object? connectedAt = freezed,Object? lastPingAt = freezed,}) {
  return _then(_self.copyWith(
edgeId: freezed == edgeId ? _self.edgeId : edgeId // ignore: cast_nullable_to_non_nullable
as String?,sourceNodeId: freezed == sourceNodeId ? _self.sourceNodeId : sourceNodeId // ignore: cast_nullable_to_non_nullable
as String?,targetNodeId: freezed == targetNodeId ? _self.targetNodeId : targetNodeId // ignore: cast_nullable_to_non_nullable
as String?,peerNodeId: freezed == peerNodeId ? _self.peerNodeId : peerNodeId // ignore: cast_nullable_to_non_nullable
as String?,peerBaseUrl: freezed == peerBaseUrl ? _self.peerBaseUrl : peerBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,direction: null == direction ? _self.direction : direction // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,trustScore: null == trustScore ? _self.trustScore : trustScore // ignore: cast_nullable_to_non_nullable
as double,connectedAt: freezed == connectedAt ? _self.connectedAt : connectedAt // ignore: cast_nullable_to_non_nullable
as String?,lastPingAt: freezed == lastPingAt ? _self.lastPingAt : lastPingAt // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkTerritoryPeerViewStateV1].
extension NetworkTerritoryPeerViewStateV1Patterns on NetworkTerritoryPeerViewStateV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkTerritoryPeerViewStateV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkTerritoryPeerViewStateV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkTerritoryPeerViewStateV1 value)  def,}){
final _that = this;
switch (_that) {
case _NetworkTerritoryPeerViewStateV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkTerritoryPeerViewStateV1 value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkTerritoryPeerViewStateV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String? edgeId,  String? sourceNodeId,  String? targetNodeId,  String? peerNodeId,  String? peerBaseUrl,  String direction,  String status,  double trustScore,  String? connectedAt,  String? lastPingAt)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkTerritoryPeerViewStateV1() when def != null:
return def(_that.edgeId,_that.sourceNodeId,_that.targetNodeId,_that.peerNodeId,_that.peerBaseUrl,_that.direction,_that.status,_that.trustScore,_that.connectedAt,_that.lastPingAt);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String? edgeId,  String? sourceNodeId,  String? targetNodeId,  String? peerNodeId,  String? peerBaseUrl,  String direction,  String status,  double trustScore,  String? connectedAt,  String? lastPingAt)  def,}) {final _that = this;
switch (_that) {
case _NetworkTerritoryPeerViewStateV1():
return def(_that.edgeId,_that.sourceNodeId,_that.targetNodeId,_that.peerNodeId,_that.peerBaseUrl,_that.direction,_that.status,_that.trustScore,_that.connectedAt,_that.lastPingAt);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String? edgeId,  String? sourceNodeId,  String? targetNodeId,  String? peerNodeId,  String? peerBaseUrl,  String direction,  String status,  double trustScore,  String? connectedAt,  String? lastPingAt)?  def,}) {final _that = this;
switch (_that) {
case _NetworkTerritoryPeerViewStateV1() when def != null:
return def(_that.edgeId,_that.sourceNodeId,_that.targetNodeId,_that.peerNodeId,_that.peerBaseUrl,_that.direction,_that.status,_that.trustScore,_that.connectedAt,_that.lastPingAt);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkTerritoryPeerViewStateV1 implements NetworkTerritoryPeerViewStateV1 {
   _NetworkTerritoryPeerViewStateV1({this.edgeId, this.sourceNodeId, this.targetNodeId, this.peerNodeId, this.peerBaseUrl, required this.direction, required this.status, required this.trustScore, this.connectedAt, this.lastPingAt});
  factory _NetworkTerritoryPeerViewStateV1.fromJson(Map<String, dynamic> json) => _$NetworkTerritoryPeerViewStateV1FromJson(json);

@override final  String? edgeId;
@override final  String? sourceNodeId;
@override final  String? targetNodeId;
@override final  String? peerNodeId;
@override final  String? peerBaseUrl;
@override final  String direction;
@override final  String status;
@override final  double trustScore;
@override final  String? connectedAt;
@override final  String? lastPingAt;

/// Create a copy of NetworkTerritoryPeerViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkTerritoryPeerViewStateV1CopyWith<_NetworkTerritoryPeerViewStateV1> get copyWith => __$NetworkTerritoryPeerViewStateV1CopyWithImpl<_NetworkTerritoryPeerViewStateV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkTerritoryPeerViewStateV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkTerritoryPeerViewStateV1&&(identical(other.edgeId, edgeId) || other.edgeId == edgeId)&&(identical(other.sourceNodeId, sourceNodeId) || other.sourceNodeId == sourceNodeId)&&(identical(other.targetNodeId, targetNodeId) || other.targetNodeId == targetNodeId)&&(identical(other.peerNodeId, peerNodeId) || other.peerNodeId == peerNodeId)&&(identical(other.peerBaseUrl, peerBaseUrl) || other.peerBaseUrl == peerBaseUrl)&&(identical(other.direction, direction) || other.direction == direction)&&(identical(other.status, status) || other.status == status)&&(identical(other.trustScore, trustScore) || other.trustScore == trustScore)&&(identical(other.connectedAt, connectedAt) || other.connectedAt == connectedAt)&&(identical(other.lastPingAt, lastPingAt) || other.lastPingAt == lastPingAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,edgeId,sourceNodeId,targetNodeId,peerNodeId,peerBaseUrl,direction,status,trustScore,connectedAt,lastPingAt);

@override
String toString() {
  return 'NetworkTerritoryPeerViewStateV1.def(edgeId: $edgeId, sourceNodeId: $sourceNodeId, targetNodeId: $targetNodeId, peerNodeId: $peerNodeId, peerBaseUrl: $peerBaseUrl, direction: $direction, status: $status, trustScore: $trustScore, connectedAt: $connectedAt, lastPingAt: $lastPingAt)';
}


}

/// @nodoc
abstract mixin class _$NetworkTerritoryPeerViewStateV1CopyWith<$Res> implements $NetworkTerritoryPeerViewStateV1CopyWith<$Res> {
  factory _$NetworkTerritoryPeerViewStateV1CopyWith(_NetworkTerritoryPeerViewStateV1 value, $Res Function(_NetworkTerritoryPeerViewStateV1) _then) = __$NetworkTerritoryPeerViewStateV1CopyWithImpl;
@override @useResult
$Res call({
 String? edgeId, String? sourceNodeId, String? targetNodeId, String? peerNodeId, String? peerBaseUrl, String direction, String status, double trustScore, String? connectedAt, String? lastPingAt
});




}
/// @nodoc
class __$NetworkTerritoryPeerViewStateV1CopyWithImpl<$Res>
    implements _$NetworkTerritoryPeerViewStateV1CopyWith<$Res> {
  __$NetworkTerritoryPeerViewStateV1CopyWithImpl(this._self, this._then);

  final _NetworkTerritoryPeerViewStateV1 _self;
  final $Res Function(_NetworkTerritoryPeerViewStateV1) _then;

/// Create a copy of NetworkTerritoryPeerViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? edgeId = freezed,Object? sourceNodeId = freezed,Object? targetNodeId = freezed,Object? peerNodeId = freezed,Object? peerBaseUrl = freezed,Object? direction = null,Object? status = null,Object? trustScore = null,Object? connectedAt = freezed,Object? lastPingAt = freezed,}) {
  return _then(_NetworkTerritoryPeerViewStateV1(
edgeId: freezed == edgeId ? _self.edgeId : edgeId // ignore: cast_nullable_to_non_nullable
as String?,sourceNodeId: freezed == sourceNodeId ? _self.sourceNodeId : sourceNodeId // ignore: cast_nullable_to_non_nullable
as String?,targetNodeId: freezed == targetNodeId ? _self.targetNodeId : targetNodeId // ignore: cast_nullable_to_non_nullable
as String?,peerNodeId: freezed == peerNodeId ? _self.peerNodeId : peerNodeId // ignore: cast_nullable_to_non_nullable
as String?,peerBaseUrl: freezed == peerBaseUrl ? _self.peerBaseUrl : peerBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,direction: null == direction ? _self.direction : direction // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,trustScore: null == trustScore ? _self.trustScore : trustScore // ignore: cast_nullable_to_non_nullable
as double,connectedAt: freezed == connectedAt ? _self.connectedAt : connectedAt // ignore: cast_nullable_to_non_nullable
as String?,lastPingAt: freezed == lastPingAt ? _self.lastPingAt : lastPingAt // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$NetworkTerritoryNodeViewStateV1 {

 NetworkTerritoryNodeRouteViewStateV1? get node; List<NetworkTerritoryEnvironmentViewStateV1> get environments; List<NetworkTerritoryHostedServiceViewStateV1> get hostedServices; List<NetworkTerritoryPeerViewStateV1> get peers;
/// Create a copy of NetworkTerritoryNodeViewStateV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkTerritoryNodeViewStateV1CopyWith<NetworkTerritoryNodeViewStateV1> get copyWith => _$NetworkTerritoryNodeViewStateV1CopyWithImpl<NetworkTerritoryNodeViewStateV1>(this as NetworkTerritoryNodeViewStateV1, _$identity);

  /// Serializes this NetworkTerritoryNodeViewStateV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkTerritoryNodeViewStateV1&&(identical(other.node, node) || other.node == node)&&const DeepCollectionEquality().equals(other.environments, environments)&&const DeepCollectionEquality().equals(other.hostedServices, hostedServices)&&const DeepCollectionEquality().equals(other.peers, peers));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,node,const DeepCollectionEquality().hash(environments),const DeepCollectionEquality().hash(hostedServices),const DeepCollectionEquality().hash(peers));

@override
String toString() {
  return 'NetworkTerritoryNodeViewStateV1(node: $node, environments: $environments, hostedServices: $hostedServices, peers: $peers)';
}


}

/// @nodoc
abstract mixin class $NetworkTerritoryNodeViewStateV1CopyWith<$Res>  {
  factory $NetworkTerritoryNodeViewStateV1CopyWith(NetworkTerritoryNodeViewStateV1 value, $Res Function(NetworkTerritoryNodeViewStateV1) _then) = _$NetworkTerritoryNodeViewStateV1CopyWithImpl;
@useResult
$Res call({
 NetworkTerritoryNodeRouteViewStateV1? node, List<NetworkTerritoryEnvironmentViewStateV1> environments, List<NetworkTerritoryHostedServiceViewStateV1> hostedServices, List<NetworkTerritoryPeerViewStateV1> peers
});


$NetworkTerritoryNodeRouteViewStateV1CopyWith<$Res>? get node;

}
/// @nodoc
class _$NetworkTerritoryNodeViewStateV1CopyWithImpl<$Res>
    implements $NetworkTerritoryNodeViewStateV1CopyWith<$Res> {
  _$NetworkTerritoryNodeViewStateV1CopyWithImpl(this._self, this._then);

  final NetworkTerritoryNodeViewStateV1 _self;
  final $Res Function(NetworkTerritoryNodeViewStateV1) _then;

/// Create a copy of NetworkTerritoryNodeViewStateV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? node = freezed,Object? environments = null,Object? hostedServices = null,Object? peers = null,}) {
  return _then(_self.copyWith(
node: freezed == node ? _self.node : node // ignore: cast_nullable_to_non_nullable
as NetworkTerritoryNodeRouteViewStateV1?,environments: null == environments ? _self.environments : environments // ignore: cast_nullable_to_non_nullable
as List<NetworkTerritoryEnvironmentViewStateV1>,hostedServices: null == hostedServices ? _self.hostedServices : hostedServices // ignore: cast_nullable_to_non_nullable
as List<NetworkTerritoryHostedServiceViewStateV1>,peers: null == peers ? _self.peers : peers // ignore: cast_nullable_to_non_nullable
as List<NetworkTerritoryPeerViewStateV1>,
  ));
}
/// Create a copy of NetworkTerritoryNodeViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkTerritoryNodeRouteViewStateV1CopyWith<$Res>? get node {
    if (_self.node == null) {
    return null;
  }

  return $NetworkTerritoryNodeRouteViewStateV1CopyWith<$Res>(_self.node!, (value) {
    return _then(_self.copyWith(node: value));
  });
}
}


/// Adds pattern-matching-related methods to [NetworkTerritoryNodeViewStateV1].
extension NetworkTerritoryNodeViewStateV1Patterns on NetworkTerritoryNodeViewStateV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkTerritoryNodeViewStateV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkTerritoryNodeViewStateV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkTerritoryNodeViewStateV1 value)  def,}){
final _that = this;
switch (_that) {
case _NetworkTerritoryNodeViewStateV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkTerritoryNodeViewStateV1 value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkTerritoryNodeViewStateV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( NetworkTerritoryNodeRouteViewStateV1? node,  List<NetworkTerritoryEnvironmentViewStateV1> environments,  List<NetworkTerritoryHostedServiceViewStateV1> hostedServices,  List<NetworkTerritoryPeerViewStateV1> peers)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkTerritoryNodeViewStateV1() when def != null:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( NetworkTerritoryNodeRouteViewStateV1? node,  List<NetworkTerritoryEnvironmentViewStateV1> environments,  List<NetworkTerritoryHostedServiceViewStateV1> hostedServices,  List<NetworkTerritoryPeerViewStateV1> peers)  def,}) {final _that = this;
switch (_that) {
case _NetworkTerritoryNodeViewStateV1():
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( NetworkTerritoryNodeRouteViewStateV1? node,  List<NetworkTerritoryEnvironmentViewStateV1> environments,  List<NetworkTerritoryHostedServiceViewStateV1> hostedServices,  List<NetworkTerritoryPeerViewStateV1> peers)?  def,}) {final _that = this;
switch (_that) {
case _NetworkTerritoryNodeViewStateV1() when def != null:
return def(_that.node,_that.environments,_that.hostedServices,_that.peers);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkTerritoryNodeViewStateV1 implements NetworkTerritoryNodeViewStateV1 {
   _NetworkTerritoryNodeViewStateV1({this.node, final  List<NetworkTerritoryEnvironmentViewStateV1> environments = const [], final  List<NetworkTerritoryHostedServiceViewStateV1> hostedServices = const [], final  List<NetworkTerritoryPeerViewStateV1> peers = const []}): _environments = environments,_hostedServices = hostedServices,_peers = peers;
  factory _NetworkTerritoryNodeViewStateV1.fromJson(Map<String, dynamic> json) => _$NetworkTerritoryNodeViewStateV1FromJson(json);

@override final  NetworkTerritoryNodeRouteViewStateV1? node;
 final  List<NetworkTerritoryEnvironmentViewStateV1> _environments;
@override@JsonKey() List<NetworkTerritoryEnvironmentViewStateV1> get environments {
  if (_environments is EqualUnmodifiableListView) return _environments;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_environments);
}

 final  List<NetworkTerritoryHostedServiceViewStateV1> _hostedServices;
@override@JsonKey() List<NetworkTerritoryHostedServiceViewStateV1> get hostedServices {
  if (_hostedServices is EqualUnmodifiableListView) return _hostedServices;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_hostedServices);
}

 final  List<NetworkTerritoryPeerViewStateV1> _peers;
@override@JsonKey() List<NetworkTerritoryPeerViewStateV1> get peers {
  if (_peers is EqualUnmodifiableListView) return _peers;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_peers);
}


/// Create a copy of NetworkTerritoryNodeViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkTerritoryNodeViewStateV1CopyWith<_NetworkTerritoryNodeViewStateV1> get copyWith => __$NetworkTerritoryNodeViewStateV1CopyWithImpl<_NetworkTerritoryNodeViewStateV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkTerritoryNodeViewStateV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkTerritoryNodeViewStateV1&&(identical(other.node, node) || other.node == node)&&const DeepCollectionEquality().equals(other._environments, _environments)&&const DeepCollectionEquality().equals(other._hostedServices, _hostedServices)&&const DeepCollectionEquality().equals(other._peers, _peers));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,node,const DeepCollectionEquality().hash(_environments),const DeepCollectionEquality().hash(_hostedServices),const DeepCollectionEquality().hash(_peers));

@override
String toString() {
  return 'NetworkTerritoryNodeViewStateV1.def(node: $node, environments: $environments, hostedServices: $hostedServices, peers: $peers)';
}


}

/// @nodoc
abstract mixin class _$NetworkTerritoryNodeViewStateV1CopyWith<$Res> implements $NetworkTerritoryNodeViewStateV1CopyWith<$Res> {
  factory _$NetworkTerritoryNodeViewStateV1CopyWith(_NetworkTerritoryNodeViewStateV1 value, $Res Function(_NetworkTerritoryNodeViewStateV1) _then) = __$NetworkTerritoryNodeViewStateV1CopyWithImpl;
@override @useResult
$Res call({
 NetworkTerritoryNodeRouteViewStateV1? node, List<NetworkTerritoryEnvironmentViewStateV1> environments, List<NetworkTerritoryHostedServiceViewStateV1> hostedServices, List<NetworkTerritoryPeerViewStateV1> peers
});


@override $NetworkTerritoryNodeRouteViewStateV1CopyWith<$Res>? get node;

}
/// @nodoc
class __$NetworkTerritoryNodeViewStateV1CopyWithImpl<$Res>
    implements _$NetworkTerritoryNodeViewStateV1CopyWith<$Res> {
  __$NetworkTerritoryNodeViewStateV1CopyWithImpl(this._self, this._then);

  final _NetworkTerritoryNodeViewStateV1 _self;
  final $Res Function(_NetworkTerritoryNodeViewStateV1) _then;

/// Create a copy of NetworkTerritoryNodeViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? node = freezed,Object? environments = null,Object? hostedServices = null,Object? peers = null,}) {
  return _then(_NetworkTerritoryNodeViewStateV1(
node: freezed == node ? _self.node : node // ignore: cast_nullable_to_non_nullable
as NetworkTerritoryNodeRouteViewStateV1?,environments: null == environments ? _self._environments : environments // ignore: cast_nullable_to_non_nullable
as List<NetworkTerritoryEnvironmentViewStateV1>,hostedServices: null == hostedServices ? _self._hostedServices : hostedServices // ignore: cast_nullable_to_non_nullable
as List<NetworkTerritoryHostedServiceViewStateV1>,peers: null == peers ? _self._peers : peers // ignore: cast_nullable_to_non_nullable
as List<NetworkTerritoryPeerViewStateV1>,
  ));
}

/// Create a copy of NetworkTerritoryNodeViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NetworkTerritoryNodeRouteViewStateV1CopyWith<$Res>? get node {
    if (_self.node == null) {
    return null;
  }

  return $NetworkTerritoryNodeRouteViewStateV1CopyWith<$Res>(_self.node!, (value) {
    return _then(_self.copyWith(node: value));
  });
}
}


/// @nodoc
mixin _$NetworkTerritoryDiscoveryViewStateV1 {

 String get status; String? get authoritySourceUrl; List<NetworkTerritoryNodeViewStateV1> get nodes; String? get summary; String get emptyMessage; String? get error; Map<String, dynamic> get provenance;
/// Create a copy of NetworkTerritoryDiscoveryViewStateV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkTerritoryDiscoveryViewStateV1CopyWith<NetworkTerritoryDiscoveryViewStateV1> get copyWith => _$NetworkTerritoryDiscoveryViewStateV1CopyWithImpl<NetworkTerritoryDiscoveryViewStateV1>(this as NetworkTerritoryDiscoveryViewStateV1, _$identity);

  /// Serializes this NetworkTerritoryDiscoveryViewStateV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkTerritoryDiscoveryViewStateV1&&(identical(other.status, status) || other.status == status)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl)&&const DeepCollectionEquality().equals(other.nodes, nodes)&&(identical(other.summary, summary) || other.summary == summary)&&(identical(other.emptyMessage, emptyMessage) || other.emptyMessage == emptyMessage)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other.provenance, provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,status,authoritySourceUrl,const DeepCollectionEquality().hash(nodes),summary,emptyMessage,error,const DeepCollectionEquality().hash(provenance));

@override
String toString() {
  return 'NetworkTerritoryDiscoveryViewStateV1(status: $status, authoritySourceUrl: $authoritySourceUrl, nodes: $nodes, summary: $summary, emptyMessage: $emptyMessage, error: $error, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class $NetworkTerritoryDiscoveryViewStateV1CopyWith<$Res>  {
  factory $NetworkTerritoryDiscoveryViewStateV1CopyWith(NetworkTerritoryDiscoveryViewStateV1 value, $Res Function(NetworkTerritoryDiscoveryViewStateV1) _then) = _$NetworkTerritoryDiscoveryViewStateV1CopyWithImpl;
@useResult
$Res call({
 String status, String? authoritySourceUrl, List<NetworkTerritoryNodeViewStateV1> nodes, String? summary, String emptyMessage, String? error, Map<String, dynamic> provenance
});




}
/// @nodoc
class _$NetworkTerritoryDiscoveryViewStateV1CopyWithImpl<$Res>
    implements $NetworkTerritoryDiscoveryViewStateV1CopyWith<$Res> {
  _$NetworkTerritoryDiscoveryViewStateV1CopyWithImpl(this._self, this._then);

  final NetworkTerritoryDiscoveryViewStateV1 _self;
  final $Res Function(NetworkTerritoryDiscoveryViewStateV1) _then;

/// Create a copy of NetworkTerritoryDiscoveryViewStateV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? status = null,Object? authoritySourceUrl = freezed,Object? nodes = null,Object? summary = freezed,Object? emptyMessage = null,Object? error = freezed,Object? provenance = null,}) {
  return _then(_self.copyWith(
status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,authoritySourceUrl: freezed == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String?,nodes: null == nodes ? _self.nodes : nodes // ignore: cast_nullable_to_non_nullable
as List<NetworkTerritoryNodeViewStateV1>,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,emptyMessage: null == emptyMessage ? _self.emptyMessage : emptyMessage // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,provenance: null == provenance ? _self.provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkTerritoryDiscoveryViewStateV1].
extension NetworkTerritoryDiscoveryViewStateV1Patterns on NetworkTerritoryDiscoveryViewStateV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkTerritoryDiscoveryViewStateV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkTerritoryDiscoveryViewStateV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkTerritoryDiscoveryViewStateV1 value)  def,}){
final _that = this;
switch (_that) {
case _NetworkTerritoryDiscoveryViewStateV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkTerritoryDiscoveryViewStateV1 value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkTerritoryDiscoveryViewStateV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String status,  String? authoritySourceUrl,  List<NetworkTerritoryNodeViewStateV1> nodes,  String? summary,  String emptyMessage,  String? error,  Map<String, dynamic> provenance)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkTerritoryDiscoveryViewStateV1() when def != null:
return def(_that.status,_that.authoritySourceUrl,_that.nodes,_that.summary,_that.emptyMessage,_that.error,_that.provenance);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String status,  String? authoritySourceUrl,  List<NetworkTerritoryNodeViewStateV1> nodes,  String? summary,  String emptyMessage,  String? error,  Map<String, dynamic> provenance)  def,}) {final _that = this;
switch (_that) {
case _NetworkTerritoryDiscoveryViewStateV1():
return def(_that.status,_that.authoritySourceUrl,_that.nodes,_that.summary,_that.emptyMessage,_that.error,_that.provenance);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String status,  String? authoritySourceUrl,  List<NetworkTerritoryNodeViewStateV1> nodes,  String? summary,  String emptyMessage,  String? error,  Map<String, dynamic> provenance)?  def,}) {final _that = this;
switch (_that) {
case _NetworkTerritoryDiscoveryViewStateV1() when def != null:
return def(_that.status,_that.authoritySourceUrl,_that.nodes,_that.summary,_that.emptyMessage,_that.error,_that.provenance);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkTerritoryDiscoveryViewStateV1 implements NetworkTerritoryDiscoveryViewStateV1 {
   _NetworkTerritoryDiscoveryViewStateV1({required this.status, this.authoritySourceUrl, final  List<NetworkTerritoryNodeViewStateV1> nodes = const [], this.summary, required this.emptyMessage, this.error, required final  Map<String, dynamic> provenance}): _nodes = nodes,_provenance = provenance;
  factory _NetworkTerritoryDiscoveryViewStateV1.fromJson(Map<String, dynamic> json) => _$NetworkTerritoryDiscoveryViewStateV1FromJson(json);

@override final  String status;
@override final  String? authoritySourceUrl;
 final  List<NetworkTerritoryNodeViewStateV1> _nodes;
@override@JsonKey() List<NetworkTerritoryNodeViewStateV1> get nodes {
  if (_nodes is EqualUnmodifiableListView) return _nodes;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_nodes);
}

@override final  String? summary;
@override final  String emptyMessage;
@override final  String? error;
 final  Map<String, dynamic> _provenance;
@override Map<String, dynamic> get provenance {
  if (_provenance is EqualUnmodifiableMapView) return _provenance;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_provenance);
}


/// Create a copy of NetworkTerritoryDiscoveryViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkTerritoryDiscoveryViewStateV1CopyWith<_NetworkTerritoryDiscoveryViewStateV1> get copyWith => __$NetworkTerritoryDiscoveryViewStateV1CopyWithImpl<_NetworkTerritoryDiscoveryViewStateV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkTerritoryDiscoveryViewStateV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkTerritoryDiscoveryViewStateV1&&(identical(other.status, status) || other.status == status)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl)&&const DeepCollectionEquality().equals(other._nodes, _nodes)&&(identical(other.summary, summary) || other.summary == summary)&&(identical(other.emptyMessage, emptyMessage) || other.emptyMessage == emptyMessage)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other._provenance, _provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,status,authoritySourceUrl,const DeepCollectionEquality().hash(_nodes),summary,emptyMessage,error,const DeepCollectionEquality().hash(_provenance));

@override
String toString() {
  return 'NetworkTerritoryDiscoveryViewStateV1.def(status: $status, authoritySourceUrl: $authoritySourceUrl, nodes: $nodes, summary: $summary, emptyMessage: $emptyMessage, error: $error, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class _$NetworkTerritoryDiscoveryViewStateV1CopyWith<$Res> implements $NetworkTerritoryDiscoveryViewStateV1CopyWith<$Res> {
  factory _$NetworkTerritoryDiscoveryViewStateV1CopyWith(_NetworkTerritoryDiscoveryViewStateV1 value, $Res Function(_NetworkTerritoryDiscoveryViewStateV1) _then) = __$NetworkTerritoryDiscoveryViewStateV1CopyWithImpl;
@override @useResult
$Res call({
 String status, String? authoritySourceUrl, List<NetworkTerritoryNodeViewStateV1> nodes, String? summary, String emptyMessage, String? error, Map<String, dynamic> provenance
});




}
/// @nodoc
class __$NetworkTerritoryDiscoveryViewStateV1CopyWithImpl<$Res>
    implements _$NetworkTerritoryDiscoveryViewStateV1CopyWith<$Res> {
  __$NetworkTerritoryDiscoveryViewStateV1CopyWithImpl(this._self, this._then);

  final _NetworkTerritoryDiscoveryViewStateV1 _self;
  final $Res Function(_NetworkTerritoryDiscoveryViewStateV1) _then;

/// Create a copy of NetworkTerritoryDiscoveryViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? status = null,Object? authoritySourceUrl = freezed,Object? nodes = null,Object? summary = freezed,Object? emptyMessage = null,Object? error = freezed,Object? provenance = null,}) {
  return _then(_NetworkTerritoryDiscoveryViewStateV1(
status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,authoritySourceUrl: freezed == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String?,nodes: null == nodes ? _self._nodes : nodes // ignore: cast_nullable_to_non_nullable
as List<NetworkTerritoryNodeViewStateV1>,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,emptyMessage: null == emptyMessage ? _self.emptyMessage : emptyMessage // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,provenance: null == provenance ? _self._provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}

// dart format on
