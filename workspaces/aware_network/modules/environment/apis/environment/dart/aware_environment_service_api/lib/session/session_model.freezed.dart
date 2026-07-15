// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'session_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$SessionSummary {

@UuidValueConverter() UuidValue get sessionId;@UuidValueConverter() UuidValue get sessionConfigId;@UuidValueConverter() UuidValue? get parentSessionId; String get key; String? get title; String? get description; String? get purpose; String get status;@UuidValueConverter() UuidValue? get createdByActorId; String? get sourceKind; String? get sourceRef; Map<String, dynamic> get metadataJson; List<SessionProviderSessionSummary> get providerSessions; int get memberCount;
/// Create a copy of SessionSummary
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$SessionSummaryCopyWith<SessionSummary> get copyWith => _$SessionSummaryCopyWithImpl<SessionSummary>(this as SessionSummary, _$identity);

  /// Serializes this SessionSummary to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is SessionSummary&&(identical(other.sessionId, sessionId) || other.sessionId == sessionId)&&(identical(other.sessionConfigId, sessionConfigId) || other.sessionConfigId == sessionConfigId)&&(identical(other.parentSessionId, parentSessionId) || other.parentSessionId == parentSessionId)&&(identical(other.key, key) || other.key == key)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.purpose, purpose) || other.purpose == purpose)&&(identical(other.status, status) || other.status == status)&&(identical(other.createdByActorId, createdByActorId) || other.createdByActorId == createdByActorId)&&(identical(other.sourceKind, sourceKind) || other.sourceKind == sourceKind)&&(identical(other.sourceRef, sourceRef) || other.sourceRef == sourceRef)&&const DeepCollectionEquality().equals(other.metadataJson, metadataJson)&&const DeepCollectionEquality().equals(other.providerSessions, providerSessions)&&(identical(other.memberCount, memberCount) || other.memberCount == memberCount));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,sessionId,sessionConfigId,parentSessionId,key,title,description,purpose,status,createdByActorId,sourceKind,sourceRef,const DeepCollectionEquality().hash(metadataJson),const DeepCollectionEquality().hash(providerSessions),memberCount);

@override
String toString() {
  return 'SessionSummary(sessionId: $sessionId, sessionConfigId: $sessionConfigId, parentSessionId: $parentSessionId, key: $key, title: $title, description: $description, purpose: $purpose, status: $status, createdByActorId: $createdByActorId, sourceKind: $sourceKind, sourceRef: $sourceRef, metadataJson: $metadataJson, providerSessions: $providerSessions, memberCount: $memberCount)';
}


}

/// @nodoc
abstract mixin class $SessionSummaryCopyWith<$Res>  {
  factory $SessionSummaryCopyWith(SessionSummary value, $Res Function(SessionSummary) _then) = _$SessionSummaryCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue sessionId,@UuidValueConverter() UuidValue sessionConfigId,@UuidValueConverter() UuidValue? parentSessionId, String key, String? title, String? description, String? purpose, String status,@UuidValueConverter() UuidValue? createdByActorId, String? sourceKind, String? sourceRef, Map<String, dynamic> metadataJson, List<SessionProviderSessionSummary> providerSessions, int memberCount
});




}
/// @nodoc
class _$SessionSummaryCopyWithImpl<$Res>
    implements $SessionSummaryCopyWith<$Res> {
  _$SessionSummaryCopyWithImpl(this._self, this._then);

  final SessionSummary _self;
  final $Res Function(SessionSummary) _then;

/// Create a copy of SessionSummary
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? sessionId = null,Object? sessionConfigId = null,Object? parentSessionId = freezed,Object? key = null,Object? title = freezed,Object? description = freezed,Object? purpose = freezed,Object? status = null,Object? createdByActorId = freezed,Object? sourceKind = freezed,Object? sourceRef = freezed,Object? metadataJson = null,Object? providerSessions = null,Object? memberCount = null,}) {
  return _then(_self.copyWith(
sessionId: null == sessionId ? _self.sessionId : sessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,sessionConfigId: null == sessionConfigId ? _self.sessionConfigId : sessionConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,parentSessionId: freezed == parentSessionId ? _self.parentSessionId : parentSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,key: null == key ? _self.key : key // ignore: cast_nullable_to_non_nullable
as String,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,purpose: freezed == purpose ? _self.purpose : purpose // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,createdByActorId: freezed == createdByActorId ? _self.createdByActorId : createdByActorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sourceKind: freezed == sourceKind ? _self.sourceKind : sourceKind // ignore: cast_nullable_to_non_nullable
as String?,sourceRef: freezed == sourceRef ? _self.sourceRef : sourceRef // ignore: cast_nullable_to_non_nullable
as String?,metadataJson: null == metadataJson ? _self.metadataJson : metadataJson // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,providerSessions: null == providerSessions ? _self.providerSessions : providerSessions // ignore: cast_nullable_to_non_nullable
as List<SessionProviderSessionSummary>,memberCount: null == memberCount ? _self.memberCount : memberCount // ignore: cast_nullable_to_non_nullable
as int,
  ));
}

}


/// Adds pattern-matching-related methods to [SessionSummary].
extension SessionSummaryPatterns on SessionSummary {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _SessionSummary value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _SessionSummary() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _SessionSummary value)  def,}){
final _that = this;
switch (_that) {
case _SessionSummary():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _SessionSummary value)?  def,}){
final _that = this;
switch (_that) {
case _SessionSummary() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue sessionId, @UuidValueConverter()  UuidValue sessionConfigId, @UuidValueConverter()  UuidValue? parentSessionId,  String key,  String? title,  String? description,  String? purpose,  String status, @UuidValueConverter()  UuidValue? createdByActorId,  String? sourceKind,  String? sourceRef,  Map<String, dynamic> metadataJson,  List<SessionProviderSessionSummary> providerSessions,  int memberCount)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _SessionSummary() when def != null:
return def(_that.sessionId,_that.sessionConfigId,_that.parentSessionId,_that.key,_that.title,_that.description,_that.purpose,_that.status,_that.createdByActorId,_that.sourceKind,_that.sourceRef,_that.metadataJson,_that.providerSessions,_that.memberCount);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue sessionId, @UuidValueConverter()  UuidValue sessionConfigId, @UuidValueConverter()  UuidValue? parentSessionId,  String key,  String? title,  String? description,  String? purpose,  String status, @UuidValueConverter()  UuidValue? createdByActorId,  String? sourceKind,  String? sourceRef,  Map<String, dynamic> metadataJson,  List<SessionProviderSessionSummary> providerSessions,  int memberCount)  def,}) {final _that = this;
switch (_that) {
case _SessionSummary():
return def(_that.sessionId,_that.sessionConfigId,_that.parentSessionId,_that.key,_that.title,_that.description,_that.purpose,_that.status,_that.createdByActorId,_that.sourceKind,_that.sourceRef,_that.metadataJson,_that.providerSessions,_that.memberCount);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue sessionId, @UuidValueConverter()  UuidValue sessionConfigId, @UuidValueConverter()  UuidValue? parentSessionId,  String key,  String? title,  String? description,  String? purpose,  String status, @UuidValueConverter()  UuidValue? createdByActorId,  String? sourceKind,  String? sourceRef,  Map<String, dynamic> metadataJson,  List<SessionProviderSessionSummary> providerSessions,  int memberCount)?  def,}) {final _that = this;
switch (_that) {
case _SessionSummary() when def != null:
return def(_that.sessionId,_that.sessionConfigId,_that.parentSessionId,_that.key,_that.title,_that.description,_that.purpose,_that.status,_that.createdByActorId,_that.sourceKind,_that.sourceRef,_that.metadataJson,_that.providerSessions,_that.memberCount);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _SessionSummary implements SessionSummary {
   _SessionSummary({@UuidValueConverter() required this.sessionId, @UuidValueConverter() required this.sessionConfigId, @UuidValueConverter() this.parentSessionId, required this.key, this.title, this.description, this.purpose, required this.status, @UuidValueConverter() this.createdByActorId, this.sourceKind, this.sourceRef, required final  Map<String, dynamic> metadataJson, final  List<SessionProviderSessionSummary> providerSessions = const [], required this.memberCount}): _metadataJson = metadataJson,_providerSessions = providerSessions;
  factory _SessionSummary.fromJson(Map<String, dynamic> json) => _$SessionSummaryFromJson(json);

@override@UuidValueConverter() final  UuidValue sessionId;
@override@UuidValueConverter() final  UuidValue sessionConfigId;
@override@UuidValueConverter() final  UuidValue? parentSessionId;
@override final  String key;
@override final  String? title;
@override final  String? description;
@override final  String? purpose;
@override final  String status;
@override@UuidValueConverter() final  UuidValue? createdByActorId;
@override final  String? sourceKind;
@override final  String? sourceRef;
 final  Map<String, dynamic> _metadataJson;
@override Map<String, dynamic> get metadataJson {
  if (_metadataJson is EqualUnmodifiableMapView) return _metadataJson;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_metadataJson);
}

 final  List<SessionProviderSessionSummary> _providerSessions;
@override@JsonKey() List<SessionProviderSessionSummary> get providerSessions {
  if (_providerSessions is EqualUnmodifiableListView) return _providerSessions;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_providerSessions);
}

@override final  int memberCount;

/// Create a copy of SessionSummary
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$SessionSummaryCopyWith<_SessionSummary> get copyWith => __$SessionSummaryCopyWithImpl<_SessionSummary>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$SessionSummaryToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _SessionSummary&&(identical(other.sessionId, sessionId) || other.sessionId == sessionId)&&(identical(other.sessionConfigId, sessionConfigId) || other.sessionConfigId == sessionConfigId)&&(identical(other.parentSessionId, parentSessionId) || other.parentSessionId == parentSessionId)&&(identical(other.key, key) || other.key == key)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.purpose, purpose) || other.purpose == purpose)&&(identical(other.status, status) || other.status == status)&&(identical(other.createdByActorId, createdByActorId) || other.createdByActorId == createdByActorId)&&(identical(other.sourceKind, sourceKind) || other.sourceKind == sourceKind)&&(identical(other.sourceRef, sourceRef) || other.sourceRef == sourceRef)&&const DeepCollectionEquality().equals(other._metadataJson, _metadataJson)&&const DeepCollectionEquality().equals(other._providerSessions, _providerSessions)&&(identical(other.memberCount, memberCount) || other.memberCount == memberCount));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,sessionId,sessionConfigId,parentSessionId,key,title,description,purpose,status,createdByActorId,sourceKind,sourceRef,const DeepCollectionEquality().hash(_metadataJson),const DeepCollectionEquality().hash(_providerSessions),memberCount);

@override
String toString() {
  return 'SessionSummary.def(sessionId: $sessionId, sessionConfigId: $sessionConfigId, parentSessionId: $parentSessionId, key: $key, title: $title, description: $description, purpose: $purpose, status: $status, createdByActorId: $createdByActorId, sourceKind: $sourceKind, sourceRef: $sourceRef, metadataJson: $metadataJson, providerSessions: $providerSessions, memberCount: $memberCount)';
}


}

/// @nodoc
abstract mixin class _$SessionSummaryCopyWith<$Res> implements $SessionSummaryCopyWith<$Res> {
  factory _$SessionSummaryCopyWith(_SessionSummary value, $Res Function(_SessionSummary) _then) = __$SessionSummaryCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue sessionId,@UuidValueConverter() UuidValue sessionConfigId,@UuidValueConverter() UuidValue? parentSessionId, String key, String? title, String? description, String? purpose, String status,@UuidValueConverter() UuidValue? createdByActorId, String? sourceKind, String? sourceRef, Map<String, dynamic> metadataJson, List<SessionProviderSessionSummary> providerSessions, int memberCount
});




}
/// @nodoc
class __$SessionSummaryCopyWithImpl<$Res>
    implements _$SessionSummaryCopyWith<$Res> {
  __$SessionSummaryCopyWithImpl(this._self, this._then);

  final _SessionSummary _self;
  final $Res Function(_SessionSummary) _then;

/// Create a copy of SessionSummary
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? sessionId = null,Object? sessionConfigId = null,Object? parentSessionId = freezed,Object? key = null,Object? title = freezed,Object? description = freezed,Object? purpose = freezed,Object? status = null,Object? createdByActorId = freezed,Object? sourceKind = freezed,Object? sourceRef = freezed,Object? metadataJson = null,Object? providerSessions = null,Object? memberCount = null,}) {
  return _then(_SessionSummary(
sessionId: null == sessionId ? _self.sessionId : sessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,sessionConfigId: null == sessionConfigId ? _self.sessionConfigId : sessionConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,parentSessionId: freezed == parentSessionId ? _self.parentSessionId : parentSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,key: null == key ? _self.key : key // ignore: cast_nullable_to_non_nullable
as String,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,purpose: freezed == purpose ? _self.purpose : purpose // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,createdByActorId: freezed == createdByActorId ? _self.createdByActorId : createdByActorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sourceKind: freezed == sourceKind ? _self.sourceKind : sourceKind // ignore: cast_nullable_to_non_nullable
as String?,sourceRef: freezed == sourceRef ? _self.sourceRef : sourceRef // ignore: cast_nullable_to_non_nullable
as String?,metadataJson: null == metadataJson ? _self._metadataJson : metadataJson // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,providerSessions: null == providerSessions ? _self._providerSessions : providerSessions // ignore: cast_nullable_to_non_nullable
as List<SessionProviderSessionSummary>,memberCount: null == memberCount ? _self.memberCount : memberCount // ignore: cast_nullable_to_non_nullable
as int,
  ));
}


}


/// @nodoc
mixin _$SessionMemberSummary {

@UuidValueConverter() UuidValue get sessionMemberId;@UuidValueConverter() UuidValue get sessionId;@UuidValueConverter() UuidValue get actorId;@UuidValueConverter() UuidValue get sessionActorConfigId; String get status; int? get joinedAtUnixMs; int? get leftAtUnixMs; Map<String, dynamic> get metadataJson; List<SessionMemberActorRoleSummary> get actorRoles;
/// Create a copy of SessionMemberSummary
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$SessionMemberSummaryCopyWith<SessionMemberSummary> get copyWith => _$SessionMemberSummaryCopyWithImpl<SessionMemberSummary>(this as SessionMemberSummary, _$identity);

  /// Serializes this SessionMemberSummary to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is SessionMemberSummary&&(identical(other.sessionMemberId, sessionMemberId) || other.sessionMemberId == sessionMemberId)&&(identical(other.sessionId, sessionId) || other.sessionId == sessionId)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.sessionActorConfigId, sessionActorConfigId) || other.sessionActorConfigId == sessionActorConfigId)&&(identical(other.status, status) || other.status == status)&&(identical(other.joinedAtUnixMs, joinedAtUnixMs) || other.joinedAtUnixMs == joinedAtUnixMs)&&(identical(other.leftAtUnixMs, leftAtUnixMs) || other.leftAtUnixMs == leftAtUnixMs)&&const DeepCollectionEquality().equals(other.metadataJson, metadataJson)&&const DeepCollectionEquality().equals(other.actorRoles, actorRoles));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,sessionMemberId,sessionId,actorId,sessionActorConfigId,status,joinedAtUnixMs,leftAtUnixMs,const DeepCollectionEquality().hash(metadataJson),const DeepCollectionEquality().hash(actorRoles));

@override
String toString() {
  return 'SessionMemberSummary(sessionMemberId: $sessionMemberId, sessionId: $sessionId, actorId: $actorId, sessionActorConfigId: $sessionActorConfigId, status: $status, joinedAtUnixMs: $joinedAtUnixMs, leftAtUnixMs: $leftAtUnixMs, metadataJson: $metadataJson, actorRoles: $actorRoles)';
}


}

/// @nodoc
abstract mixin class $SessionMemberSummaryCopyWith<$Res>  {
  factory $SessionMemberSummaryCopyWith(SessionMemberSummary value, $Res Function(SessionMemberSummary) _then) = _$SessionMemberSummaryCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue sessionMemberId,@UuidValueConverter() UuidValue sessionId,@UuidValueConverter() UuidValue actorId,@UuidValueConverter() UuidValue sessionActorConfigId, String status, int? joinedAtUnixMs, int? leftAtUnixMs, Map<String, dynamic> metadataJson, List<SessionMemberActorRoleSummary> actorRoles
});




}
/// @nodoc
class _$SessionMemberSummaryCopyWithImpl<$Res>
    implements $SessionMemberSummaryCopyWith<$Res> {
  _$SessionMemberSummaryCopyWithImpl(this._self, this._then);

  final SessionMemberSummary _self;
  final $Res Function(SessionMemberSummary) _then;

/// Create a copy of SessionMemberSummary
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? sessionMemberId = null,Object? sessionId = null,Object? actorId = null,Object? sessionActorConfigId = null,Object? status = null,Object? joinedAtUnixMs = freezed,Object? leftAtUnixMs = freezed,Object? metadataJson = null,Object? actorRoles = null,}) {
  return _then(_self.copyWith(
sessionMemberId: null == sessionMemberId ? _self.sessionMemberId : sessionMemberId // ignore: cast_nullable_to_non_nullable
as UuidValue,sessionId: null == sessionId ? _self.sessionId : sessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,actorId: null == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue,sessionActorConfigId: null == sessionActorConfigId ? _self.sessionActorConfigId : sessionActorConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,joinedAtUnixMs: freezed == joinedAtUnixMs ? _self.joinedAtUnixMs : joinedAtUnixMs // ignore: cast_nullable_to_non_nullable
as int?,leftAtUnixMs: freezed == leftAtUnixMs ? _self.leftAtUnixMs : leftAtUnixMs // ignore: cast_nullable_to_non_nullable
as int?,metadataJson: null == metadataJson ? _self.metadataJson : metadataJson // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,actorRoles: null == actorRoles ? _self.actorRoles : actorRoles // ignore: cast_nullable_to_non_nullable
as List<SessionMemberActorRoleSummary>,
  ));
}

}


/// Adds pattern-matching-related methods to [SessionMemberSummary].
extension SessionMemberSummaryPatterns on SessionMemberSummary {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _SessionMemberSummary value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _SessionMemberSummary() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _SessionMemberSummary value)  def,}){
final _that = this;
switch (_that) {
case _SessionMemberSummary():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _SessionMemberSummary value)?  def,}){
final _that = this;
switch (_that) {
case _SessionMemberSummary() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue sessionMemberId, @UuidValueConverter()  UuidValue sessionId, @UuidValueConverter()  UuidValue actorId, @UuidValueConverter()  UuidValue sessionActorConfigId,  String status,  int? joinedAtUnixMs,  int? leftAtUnixMs,  Map<String, dynamic> metadataJson,  List<SessionMemberActorRoleSummary> actorRoles)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _SessionMemberSummary() when def != null:
return def(_that.sessionMemberId,_that.sessionId,_that.actorId,_that.sessionActorConfigId,_that.status,_that.joinedAtUnixMs,_that.leftAtUnixMs,_that.metadataJson,_that.actorRoles);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue sessionMemberId, @UuidValueConverter()  UuidValue sessionId, @UuidValueConverter()  UuidValue actorId, @UuidValueConverter()  UuidValue sessionActorConfigId,  String status,  int? joinedAtUnixMs,  int? leftAtUnixMs,  Map<String, dynamic> metadataJson,  List<SessionMemberActorRoleSummary> actorRoles)  def,}) {final _that = this;
switch (_that) {
case _SessionMemberSummary():
return def(_that.sessionMemberId,_that.sessionId,_that.actorId,_that.sessionActorConfigId,_that.status,_that.joinedAtUnixMs,_that.leftAtUnixMs,_that.metadataJson,_that.actorRoles);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue sessionMemberId, @UuidValueConverter()  UuidValue sessionId, @UuidValueConverter()  UuidValue actorId, @UuidValueConverter()  UuidValue sessionActorConfigId,  String status,  int? joinedAtUnixMs,  int? leftAtUnixMs,  Map<String, dynamic> metadataJson,  List<SessionMemberActorRoleSummary> actorRoles)?  def,}) {final _that = this;
switch (_that) {
case _SessionMemberSummary() when def != null:
return def(_that.sessionMemberId,_that.sessionId,_that.actorId,_that.sessionActorConfigId,_that.status,_that.joinedAtUnixMs,_that.leftAtUnixMs,_that.metadataJson,_that.actorRoles);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _SessionMemberSummary implements SessionMemberSummary {
   _SessionMemberSummary({@UuidValueConverter() required this.sessionMemberId, @UuidValueConverter() required this.sessionId, @UuidValueConverter() required this.actorId, @UuidValueConverter() required this.sessionActorConfigId, required this.status, this.joinedAtUnixMs, this.leftAtUnixMs, required final  Map<String, dynamic> metadataJson, final  List<SessionMemberActorRoleSummary> actorRoles = const []}): _metadataJson = metadataJson,_actorRoles = actorRoles;
  factory _SessionMemberSummary.fromJson(Map<String, dynamic> json) => _$SessionMemberSummaryFromJson(json);

@override@UuidValueConverter() final  UuidValue sessionMemberId;
@override@UuidValueConverter() final  UuidValue sessionId;
@override@UuidValueConverter() final  UuidValue actorId;
@override@UuidValueConverter() final  UuidValue sessionActorConfigId;
@override final  String status;
@override final  int? joinedAtUnixMs;
@override final  int? leftAtUnixMs;
 final  Map<String, dynamic> _metadataJson;
@override Map<String, dynamic> get metadataJson {
  if (_metadataJson is EqualUnmodifiableMapView) return _metadataJson;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_metadataJson);
}

 final  List<SessionMemberActorRoleSummary> _actorRoles;
@override@JsonKey() List<SessionMemberActorRoleSummary> get actorRoles {
  if (_actorRoles is EqualUnmodifiableListView) return _actorRoles;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_actorRoles);
}


/// Create a copy of SessionMemberSummary
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$SessionMemberSummaryCopyWith<_SessionMemberSummary> get copyWith => __$SessionMemberSummaryCopyWithImpl<_SessionMemberSummary>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$SessionMemberSummaryToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _SessionMemberSummary&&(identical(other.sessionMemberId, sessionMemberId) || other.sessionMemberId == sessionMemberId)&&(identical(other.sessionId, sessionId) || other.sessionId == sessionId)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.sessionActorConfigId, sessionActorConfigId) || other.sessionActorConfigId == sessionActorConfigId)&&(identical(other.status, status) || other.status == status)&&(identical(other.joinedAtUnixMs, joinedAtUnixMs) || other.joinedAtUnixMs == joinedAtUnixMs)&&(identical(other.leftAtUnixMs, leftAtUnixMs) || other.leftAtUnixMs == leftAtUnixMs)&&const DeepCollectionEquality().equals(other._metadataJson, _metadataJson)&&const DeepCollectionEquality().equals(other._actorRoles, _actorRoles));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,sessionMemberId,sessionId,actorId,sessionActorConfigId,status,joinedAtUnixMs,leftAtUnixMs,const DeepCollectionEquality().hash(_metadataJson),const DeepCollectionEquality().hash(_actorRoles));

@override
String toString() {
  return 'SessionMemberSummary.def(sessionMemberId: $sessionMemberId, sessionId: $sessionId, actorId: $actorId, sessionActorConfigId: $sessionActorConfigId, status: $status, joinedAtUnixMs: $joinedAtUnixMs, leftAtUnixMs: $leftAtUnixMs, metadataJson: $metadataJson, actorRoles: $actorRoles)';
}


}

/// @nodoc
abstract mixin class _$SessionMemberSummaryCopyWith<$Res> implements $SessionMemberSummaryCopyWith<$Res> {
  factory _$SessionMemberSummaryCopyWith(_SessionMemberSummary value, $Res Function(_SessionMemberSummary) _then) = __$SessionMemberSummaryCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue sessionMemberId,@UuidValueConverter() UuidValue sessionId,@UuidValueConverter() UuidValue actorId,@UuidValueConverter() UuidValue sessionActorConfigId, String status, int? joinedAtUnixMs, int? leftAtUnixMs, Map<String, dynamic> metadataJson, List<SessionMemberActorRoleSummary> actorRoles
});




}
/// @nodoc
class __$SessionMemberSummaryCopyWithImpl<$Res>
    implements _$SessionMemberSummaryCopyWith<$Res> {
  __$SessionMemberSummaryCopyWithImpl(this._self, this._then);

  final _SessionMemberSummary _self;
  final $Res Function(_SessionMemberSummary) _then;

/// Create a copy of SessionMemberSummary
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? sessionMemberId = null,Object? sessionId = null,Object? actorId = null,Object? sessionActorConfigId = null,Object? status = null,Object? joinedAtUnixMs = freezed,Object? leftAtUnixMs = freezed,Object? metadataJson = null,Object? actorRoles = null,}) {
  return _then(_SessionMemberSummary(
sessionMemberId: null == sessionMemberId ? _self.sessionMemberId : sessionMemberId // ignore: cast_nullable_to_non_nullable
as UuidValue,sessionId: null == sessionId ? _self.sessionId : sessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,actorId: null == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue,sessionActorConfigId: null == sessionActorConfigId ? _self.sessionActorConfigId : sessionActorConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,joinedAtUnixMs: freezed == joinedAtUnixMs ? _self.joinedAtUnixMs : joinedAtUnixMs // ignore: cast_nullable_to_non_nullable
as int?,leftAtUnixMs: freezed == leftAtUnixMs ? _self.leftAtUnixMs : leftAtUnixMs // ignore: cast_nullable_to_non_nullable
as int?,metadataJson: null == metadataJson ? _self._metadataJson : metadataJson // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,actorRoles: null == actorRoles ? _self._actorRoles : actorRoles // ignore: cast_nullable_to_non_nullable
as List<SessionMemberActorRoleSummary>,
  ));
}


}


/// @nodoc
mixin _$SessionMemberActorRoleSummary {

@UuidValueConverter() UuidValue get sessionMemberActorRoleId;@UuidValueConverter() UuidValue get sessionMemberId;@UuidValueConverter() UuidValue get actorRoleId; String get sourceKind; String get status; Map<String, dynamic> get evidenceJson;
/// Create a copy of SessionMemberActorRoleSummary
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$SessionMemberActorRoleSummaryCopyWith<SessionMemberActorRoleSummary> get copyWith => _$SessionMemberActorRoleSummaryCopyWithImpl<SessionMemberActorRoleSummary>(this as SessionMemberActorRoleSummary, _$identity);

  /// Serializes this SessionMemberActorRoleSummary to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is SessionMemberActorRoleSummary&&(identical(other.sessionMemberActorRoleId, sessionMemberActorRoleId) || other.sessionMemberActorRoleId == sessionMemberActorRoleId)&&(identical(other.sessionMemberId, sessionMemberId) || other.sessionMemberId == sessionMemberId)&&(identical(other.actorRoleId, actorRoleId) || other.actorRoleId == actorRoleId)&&(identical(other.sourceKind, sourceKind) || other.sourceKind == sourceKind)&&(identical(other.status, status) || other.status == status)&&const DeepCollectionEquality().equals(other.evidenceJson, evidenceJson));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,sessionMemberActorRoleId,sessionMemberId,actorRoleId,sourceKind,status,const DeepCollectionEquality().hash(evidenceJson));

@override
String toString() {
  return 'SessionMemberActorRoleSummary(sessionMemberActorRoleId: $sessionMemberActorRoleId, sessionMemberId: $sessionMemberId, actorRoleId: $actorRoleId, sourceKind: $sourceKind, status: $status, evidenceJson: $evidenceJson)';
}


}

/// @nodoc
abstract mixin class $SessionMemberActorRoleSummaryCopyWith<$Res>  {
  factory $SessionMemberActorRoleSummaryCopyWith(SessionMemberActorRoleSummary value, $Res Function(SessionMemberActorRoleSummary) _then) = _$SessionMemberActorRoleSummaryCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue sessionMemberActorRoleId,@UuidValueConverter() UuidValue sessionMemberId,@UuidValueConverter() UuidValue actorRoleId, String sourceKind, String status, Map<String, dynamic> evidenceJson
});




}
/// @nodoc
class _$SessionMemberActorRoleSummaryCopyWithImpl<$Res>
    implements $SessionMemberActorRoleSummaryCopyWith<$Res> {
  _$SessionMemberActorRoleSummaryCopyWithImpl(this._self, this._then);

  final SessionMemberActorRoleSummary _self;
  final $Res Function(SessionMemberActorRoleSummary) _then;

/// Create a copy of SessionMemberActorRoleSummary
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? sessionMemberActorRoleId = null,Object? sessionMemberId = null,Object? actorRoleId = null,Object? sourceKind = null,Object? status = null,Object? evidenceJson = null,}) {
  return _then(_self.copyWith(
sessionMemberActorRoleId: null == sessionMemberActorRoleId ? _self.sessionMemberActorRoleId : sessionMemberActorRoleId // ignore: cast_nullable_to_non_nullable
as UuidValue,sessionMemberId: null == sessionMemberId ? _self.sessionMemberId : sessionMemberId // ignore: cast_nullable_to_non_nullable
as UuidValue,actorRoleId: null == actorRoleId ? _self.actorRoleId : actorRoleId // ignore: cast_nullable_to_non_nullable
as UuidValue,sourceKind: null == sourceKind ? _self.sourceKind : sourceKind // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,evidenceJson: null == evidenceJson ? _self.evidenceJson : evidenceJson // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [SessionMemberActorRoleSummary].
extension SessionMemberActorRoleSummaryPatterns on SessionMemberActorRoleSummary {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _SessionMemberActorRoleSummary value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _SessionMemberActorRoleSummary() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _SessionMemberActorRoleSummary value)  def,}){
final _that = this;
switch (_that) {
case _SessionMemberActorRoleSummary():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _SessionMemberActorRoleSummary value)?  def,}){
final _that = this;
switch (_that) {
case _SessionMemberActorRoleSummary() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue sessionMemberActorRoleId, @UuidValueConverter()  UuidValue sessionMemberId, @UuidValueConverter()  UuidValue actorRoleId,  String sourceKind,  String status,  Map<String, dynamic> evidenceJson)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _SessionMemberActorRoleSummary() when def != null:
return def(_that.sessionMemberActorRoleId,_that.sessionMemberId,_that.actorRoleId,_that.sourceKind,_that.status,_that.evidenceJson);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue sessionMemberActorRoleId, @UuidValueConverter()  UuidValue sessionMemberId, @UuidValueConverter()  UuidValue actorRoleId,  String sourceKind,  String status,  Map<String, dynamic> evidenceJson)  def,}) {final _that = this;
switch (_that) {
case _SessionMemberActorRoleSummary():
return def(_that.sessionMemberActorRoleId,_that.sessionMemberId,_that.actorRoleId,_that.sourceKind,_that.status,_that.evidenceJson);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue sessionMemberActorRoleId, @UuidValueConverter()  UuidValue sessionMemberId, @UuidValueConverter()  UuidValue actorRoleId,  String sourceKind,  String status,  Map<String, dynamic> evidenceJson)?  def,}) {final _that = this;
switch (_that) {
case _SessionMemberActorRoleSummary() when def != null:
return def(_that.sessionMemberActorRoleId,_that.sessionMemberId,_that.actorRoleId,_that.sourceKind,_that.status,_that.evidenceJson);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _SessionMemberActorRoleSummary implements SessionMemberActorRoleSummary {
   _SessionMemberActorRoleSummary({@UuidValueConverter() required this.sessionMemberActorRoleId, @UuidValueConverter() required this.sessionMemberId, @UuidValueConverter() required this.actorRoleId, required this.sourceKind, required this.status, required final  Map<String, dynamic> evidenceJson}): _evidenceJson = evidenceJson;
  factory _SessionMemberActorRoleSummary.fromJson(Map<String, dynamic> json) => _$SessionMemberActorRoleSummaryFromJson(json);

@override@UuidValueConverter() final  UuidValue sessionMemberActorRoleId;
@override@UuidValueConverter() final  UuidValue sessionMemberId;
@override@UuidValueConverter() final  UuidValue actorRoleId;
@override final  String sourceKind;
@override final  String status;
 final  Map<String, dynamic> _evidenceJson;
@override Map<String, dynamic> get evidenceJson {
  if (_evidenceJson is EqualUnmodifiableMapView) return _evidenceJson;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_evidenceJson);
}


/// Create a copy of SessionMemberActorRoleSummary
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$SessionMemberActorRoleSummaryCopyWith<_SessionMemberActorRoleSummary> get copyWith => __$SessionMemberActorRoleSummaryCopyWithImpl<_SessionMemberActorRoleSummary>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$SessionMemberActorRoleSummaryToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _SessionMemberActorRoleSummary&&(identical(other.sessionMemberActorRoleId, sessionMemberActorRoleId) || other.sessionMemberActorRoleId == sessionMemberActorRoleId)&&(identical(other.sessionMemberId, sessionMemberId) || other.sessionMemberId == sessionMemberId)&&(identical(other.actorRoleId, actorRoleId) || other.actorRoleId == actorRoleId)&&(identical(other.sourceKind, sourceKind) || other.sourceKind == sourceKind)&&(identical(other.status, status) || other.status == status)&&const DeepCollectionEquality().equals(other._evidenceJson, _evidenceJson));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,sessionMemberActorRoleId,sessionMemberId,actorRoleId,sourceKind,status,const DeepCollectionEquality().hash(_evidenceJson));

@override
String toString() {
  return 'SessionMemberActorRoleSummary.def(sessionMemberActorRoleId: $sessionMemberActorRoleId, sessionMemberId: $sessionMemberId, actorRoleId: $actorRoleId, sourceKind: $sourceKind, status: $status, evidenceJson: $evidenceJson)';
}


}

/// @nodoc
abstract mixin class _$SessionMemberActorRoleSummaryCopyWith<$Res> implements $SessionMemberActorRoleSummaryCopyWith<$Res> {
  factory _$SessionMemberActorRoleSummaryCopyWith(_SessionMemberActorRoleSummary value, $Res Function(_SessionMemberActorRoleSummary) _then) = __$SessionMemberActorRoleSummaryCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue sessionMemberActorRoleId,@UuidValueConverter() UuidValue sessionMemberId,@UuidValueConverter() UuidValue actorRoleId, String sourceKind, String status, Map<String, dynamic> evidenceJson
});




}
/// @nodoc
class __$SessionMemberActorRoleSummaryCopyWithImpl<$Res>
    implements _$SessionMemberActorRoleSummaryCopyWith<$Res> {
  __$SessionMemberActorRoleSummaryCopyWithImpl(this._self, this._then);

  final _SessionMemberActorRoleSummary _self;
  final $Res Function(_SessionMemberActorRoleSummary) _then;

/// Create a copy of SessionMemberActorRoleSummary
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? sessionMemberActorRoleId = null,Object? sessionMemberId = null,Object? actorRoleId = null,Object? sourceKind = null,Object? status = null,Object? evidenceJson = null,}) {
  return _then(_SessionMemberActorRoleSummary(
sessionMemberActorRoleId: null == sessionMemberActorRoleId ? _self.sessionMemberActorRoleId : sessionMemberActorRoleId // ignore: cast_nullable_to_non_nullable
as UuidValue,sessionMemberId: null == sessionMemberId ? _self.sessionMemberId : sessionMemberId // ignore: cast_nullable_to_non_nullable
as UuidValue,actorRoleId: null == actorRoleId ? _self.actorRoleId : actorRoleId // ignore: cast_nullable_to_non_nullable
as UuidValue,sourceKind: null == sourceKind ? _self.sourceKind : sourceKind // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,evidenceJson: null == evidenceJson ? _self._evidenceJson : evidenceJson // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$SessionProviderSessionSummary {

@UuidValueConverter() UuidValue get sessionProviderSessionId;@UuidValueConverter() UuidValue get sessionId;@UuidValueConverter() UuidValue get providerSessionConfigId; String get providerSessionKey; String? get providerSessionRef;@UuidValueConverter() UuidValue? get providerObjectInstanceGraphIdentityId;@UuidValueConverter() UuidValue? get providerClassInstanceIdentityId;@UuidValueConverter() UuidValue? get providerObjectInstanceGraphBranchId; String get status; Map<String, dynamic> get metadataJson;
/// Create a copy of SessionProviderSessionSummary
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$SessionProviderSessionSummaryCopyWith<SessionProviderSessionSummary> get copyWith => _$SessionProviderSessionSummaryCopyWithImpl<SessionProviderSessionSummary>(this as SessionProviderSessionSummary, _$identity);

  /// Serializes this SessionProviderSessionSummary to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is SessionProviderSessionSummary&&(identical(other.sessionProviderSessionId, sessionProviderSessionId) || other.sessionProviderSessionId == sessionProviderSessionId)&&(identical(other.sessionId, sessionId) || other.sessionId == sessionId)&&(identical(other.providerSessionConfigId, providerSessionConfigId) || other.providerSessionConfigId == providerSessionConfigId)&&(identical(other.providerSessionKey, providerSessionKey) || other.providerSessionKey == providerSessionKey)&&(identical(other.providerSessionRef, providerSessionRef) || other.providerSessionRef == providerSessionRef)&&(identical(other.providerObjectInstanceGraphIdentityId, providerObjectInstanceGraphIdentityId) || other.providerObjectInstanceGraphIdentityId == providerObjectInstanceGraphIdentityId)&&(identical(other.providerClassInstanceIdentityId, providerClassInstanceIdentityId) || other.providerClassInstanceIdentityId == providerClassInstanceIdentityId)&&(identical(other.providerObjectInstanceGraphBranchId, providerObjectInstanceGraphBranchId) || other.providerObjectInstanceGraphBranchId == providerObjectInstanceGraphBranchId)&&(identical(other.status, status) || other.status == status)&&const DeepCollectionEquality().equals(other.metadataJson, metadataJson));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,sessionProviderSessionId,sessionId,providerSessionConfigId,providerSessionKey,providerSessionRef,providerObjectInstanceGraphIdentityId,providerClassInstanceIdentityId,providerObjectInstanceGraphBranchId,status,const DeepCollectionEquality().hash(metadataJson));

@override
String toString() {
  return 'SessionProviderSessionSummary(sessionProviderSessionId: $sessionProviderSessionId, sessionId: $sessionId, providerSessionConfigId: $providerSessionConfigId, providerSessionKey: $providerSessionKey, providerSessionRef: $providerSessionRef, providerObjectInstanceGraphIdentityId: $providerObjectInstanceGraphIdentityId, providerClassInstanceIdentityId: $providerClassInstanceIdentityId, providerObjectInstanceGraphBranchId: $providerObjectInstanceGraphBranchId, status: $status, metadataJson: $metadataJson)';
}


}

/// @nodoc
abstract mixin class $SessionProviderSessionSummaryCopyWith<$Res>  {
  factory $SessionProviderSessionSummaryCopyWith(SessionProviderSessionSummary value, $Res Function(SessionProviderSessionSummary) _then) = _$SessionProviderSessionSummaryCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue sessionProviderSessionId,@UuidValueConverter() UuidValue sessionId,@UuidValueConverter() UuidValue providerSessionConfigId, String providerSessionKey, String? providerSessionRef,@UuidValueConverter() UuidValue? providerObjectInstanceGraphIdentityId,@UuidValueConverter() UuidValue? providerClassInstanceIdentityId,@UuidValueConverter() UuidValue? providerObjectInstanceGraphBranchId, String status, Map<String, dynamic> metadataJson
});




}
/// @nodoc
class _$SessionProviderSessionSummaryCopyWithImpl<$Res>
    implements $SessionProviderSessionSummaryCopyWith<$Res> {
  _$SessionProviderSessionSummaryCopyWithImpl(this._self, this._then);

  final SessionProviderSessionSummary _self;
  final $Res Function(SessionProviderSessionSummary) _then;

/// Create a copy of SessionProviderSessionSummary
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? sessionProviderSessionId = null,Object? sessionId = null,Object? providerSessionConfigId = null,Object? providerSessionKey = null,Object? providerSessionRef = freezed,Object? providerObjectInstanceGraphIdentityId = freezed,Object? providerClassInstanceIdentityId = freezed,Object? providerObjectInstanceGraphBranchId = freezed,Object? status = null,Object? metadataJson = null,}) {
  return _then(_self.copyWith(
sessionProviderSessionId: null == sessionProviderSessionId ? _self.sessionProviderSessionId : sessionProviderSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,sessionId: null == sessionId ? _self.sessionId : sessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,providerSessionConfigId: null == providerSessionConfigId ? _self.providerSessionConfigId : providerSessionConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,providerSessionKey: null == providerSessionKey ? _self.providerSessionKey : providerSessionKey // ignore: cast_nullable_to_non_nullable
as String,providerSessionRef: freezed == providerSessionRef ? _self.providerSessionRef : providerSessionRef // ignore: cast_nullable_to_non_nullable
as String?,providerObjectInstanceGraphIdentityId: freezed == providerObjectInstanceGraphIdentityId ? _self.providerObjectInstanceGraphIdentityId : providerObjectInstanceGraphIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue?,providerClassInstanceIdentityId: freezed == providerClassInstanceIdentityId ? _self.providerClassInstanceIdentityId : providerClassInstanceIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue?,providerObjectInstanceGraphBranchId: freezed == providerObjectInstanceGraphBranchId ? _self.providerObjectInstanceGraphBranchId : providerObjectInstanceGraphBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,metadataJson: null == metadataJson ? _self.metadataJson : metadataJson // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [SessionProviderSessionSummary].
extension SessionProviderSessionSummaryPatterns on SessionProviderSessionSummary {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _SessionProviderSessionSummary value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _SessionProviderSessionSummary() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _SessionProviderSessionSummary value)  def,}){
final _that = this;
switch (_that) {
case _SessionProviderSessionSummary():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _SessionProviderSessionSummary value)?  def,}){
final _that = this;
switch (_that) {
case _SessionProviderSessionSummary() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue sessionProviderSessionId, @UuidValueConverter()  UuidValue sessionId, @UuidValueConverter()  UuidValue providerSessionConfigId,  String providerSessionKey,  String? providerSessionRef, @UuidValueConverter()  UuidValue? providerObjectInstanceGraphIdentityId, @UuidValueConverter()  UuidValue? providerClassInstanceIdentityId, @UuidValueConverter()  UuidValue? providerObjectInstanceGraphBranchId,  String status,  Map<String, dynamic> metadataJson)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _SessionProviderSessionSummary() when def != null:
return def(_that.sessionProviderSessionId,_that.sessionId,_that.providerSessionConfigId,_that.providerSessionKey,_that.providerSessionRef,_that.providerObjectInstanceGraphIdentityId,_that.providerClassInstanceIdentityId,_that.providerObjectInstanceGraphBranchId,_that.status,_that.metadataJson);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue sessionProviderSessionId, @UuidValueConverter()  UuidValue sessionId, @UuidValueConverter()  UuidValue providerSessionConfigId,  String providerSessionKey,  String? providerSessionRef, @UuidValueConverter()  UuidValue? providerObjectInstanceGraphIdentityId, @UuidValueConverter()  UuidValue? providerClassInstanceIdentityId, @UuidValueConverter()  UuidValue? providerObjectInstanceGraphBranchId,  String status,  Map<String, dynamic> metadataJson)  def,}) {final _that = this;
switch (_that) {
case _SessionProviderSessionSummary():
return def(_that.sessionProviderSessionId,_that.sessionId,_that.providerSessionConfigId,_that.providerSessionKey,_that.providerSessionRef,_that.providerObjectInstanceGraphIdentityId,_that.providerClassInstanceIdentityId,_that.providerObjectInstanceGraphBranchId,_that.status,_that.metadataJson);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue sessionProviderSessionId, @UuidValueConverter()  UuidValue sessionId, @UuidValueConverter()  UuidValue providerSessionConfigId,  String providerSessionKey,  String? providerSessionRef, @UuidValueConverter()  UuidValue? providerObjectInstanceGraphIdentityId, @UuidValueConverter()  UuidValue? providerClassInstanceIdentityId, @UuidValueConverter()  UuidValue? providerObjectInstanceGraphBranchId,  String status,  Map<String, dynamic> metadataJson)?  def,}) {final _that = this;
switch (_that) {
case _SessionProviderSessionSummary() when def != null:
return def(_that.sessionProviderSessionId,_that.sessionId,_that.providerSessionConfigId,_that.providerSessionKey,_that.providerSessionRef,_that.providerObjectInstanceGraphIdentityId,_that.providerClassInstanceIdentityId,_that.providerObjectInstanceGraphBranchId,_that.status,_that.metadataJson);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _SessionProviderSessionSummary implements SessionProviderSessionSummary {
   _SessionProviderSessionSummary({@UuidValueConverter() required this.sessionProviderSessionId, @UuidValueConverter() required this.sessionId, @UuidValueConverter() required this.providerSessionConfigId, required this.providerSessionKey, this.providerSessionRef, @UuidValueConverter() this.providerObjectInstanceGraphIdentityId, @UuidValueConverter() this.providerClassInstanceIdentityId, @UuidValueConverter() this.providerObjectInstanceGraphBranchId, required this.status, required final  Map<String, dynamic> metadataJson}): _metadataJson = metadataJson;
  factory _SessionProviderSessionSummary.fromJson(Map<String, dynamic> json) => _$SessionProviderSessionSummaryFromJson(json);

@override@UuidValueConverter() final  UuidValue sessionProviderSessionId;
@override@UuidValueConverter() final  UuidValue sessionId;
@override@UuidValueConverter() final  UuidValue providerSessionConfigId;
@override final  String providerSessionKey;
@override final  String? providerSessionRef;
@override@UuidValueConverter() final  UuidValue? providerObjectInstanceGraphIdentityId;
@override@UuidValueConverter() final  UuidValue? providerClassInstanceIdentityId;
@override@UuidValueConverter() final  UuidValue? providerObjectInstanceGraphBranchId;
@override final  String status;
 final  Map<String, dynamic> _metadataJson;
@override Map<String, dynamic> get metadataJson {
  if (_metadataJson is EqualUnmodifiableMapView) return _metadataJson;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_metadataJson);
}


/// Create a copy of SessionProviderSessionSummary
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$SessionProviderSessionSummaryCopyWith<_SessionProviderSessionSummary> get copyWith => __$SessionProviderSessionSummaryCopyWithImpl<_SessionProviderSessionSummary>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$SessionProviderSessionSummaryToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _SessionProviderSessionSummary&&(identical(other.sessionProviderSessionId, sessionProviderSessionId) || other.sessionProviderSessionId == sessionProviderSessionId)&&(identical(other.sessionId, sessionId) || other.sessionId == sessionId)&&(identical(other.providerSessionConfigId, providerSessionConfigId) || other.providerSessionConfigId == providerSessionConfigId)&&(identical(other.providerSessionKey, providerSessionKey) || other.providerSessionKey == providerSessionKey)&&(identical(other.providerSessionRef, providerSessionRef) || other.providerSessionRef == providerSessionRef)&&(identical(other.providerObjectInstanceGraphIdentityId, providerObjectInstanceGraphIdentityId) || other.providerObjectInstanceGraphIdentityId == providerObjectInstanceGraphIdentityId)&&(identical(other.providerClassInstanceIdentityId, providerClassInstanceIdentityId) || other.providerClassInstanceIdentityId == providerClassInstanceIdentityId)&&(identical(other.providerObjectInstanceGraphBranchId, providerObjectInstanceGraphBranchId) || other.providerObjectInstanceGraphBranchId == providerObjectInstanceGraphBranchId)&&(identical(other.status, status) || other.status == status)&&const DeepCollectionEquality().equals(other._metadataJson, _metadataJson));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,sessionProviderSessionId,sessionId,providerSessionConfigId,providerSessionKey,providerSessionRef,providerObjectInstanceGraphIdentityId,providerClassInstanceIdentityId,providerObjectInstanceGraphBranchId,status,const DeepCollectionEquality().hash(_metadataJson));

@override
String toString() {
  return 'SessionProviderSessionSummary.def(sessionProviderSessionId: $sessionProviderSessionId, sessionId: $sessionId, providerSessionConfigId: $providerSessionConfigId, providerSessionKey: $providerSessionKey, providerSessionRef: $providerSessionRef, providerObjectInstanceGraphIdentityId: $providerObjectInstanceGraphIdentityId, providerClassInstanceIdentityId: $providerClassInstanceIdentityId, providerObjectInstanceGraphBranchId: $providerObjectInstanceGraphBranchId, status: $status, metadataJson: $metadataJson)';
}


}

/// @nodoc
abstract mixin class _$SessionProviderSessionSummaryCopyWith<$Res> implements $SessionProviderSessionSummaryCopyWith<$Res> {
  factory _$SessionProviderSessionSummaryCopyWith(_SessionProviderSessionSummary value, $Res Function(_SessionProviderSessionSummary) _then) = __$SessionProviderSessionSummaryCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue sessionProviderSessionId,@UuidValueConverter() UuidValue sessionId,@UuidValueConverter() UuidValue providerSessionConfigId, String providerSessionKey, String? providerSessionRef,@UuidValueConverter() UuidValue? providerObjectInstanceGraphIdentityId,@UuidValueConverter() UuidValue? providerClassInstanceIdentityId,@UuidValueConverter() UuidValue? providerObjectInstanceGraphBranchId, String status, Map<String, dynamic> metadataJson
});




}
/// @nodoc
class __$SessionProviderSessionSummaryCopyWithImpl<$Res>
    implements _$SessionProviderSessionSummaryCopyWith<$Res> {
  __$SessionProviderSessionSummaryCopyWithImpl(this._self, this._then);

  final _SessionProviderSessionSummary _self;
  final $Res Function(_SessionProviderSessionSummary) _then;

/// Create a copy of SessionProviderSessionSummary
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? sessionProviderSessionId = null,Object? sessionId = null,Object? providerSessionConfigId = null,Object? providerSessionKey = null,Object? providerSessionRef = freezed,Object? providerObjectInstanceGraphIdentityId = freezed,Object? providerClassInstanceIdentityId = freezed,Object? providerObjectInstanceGraphBranchId = freezed,Object? status = null,Object? metadataJson = null,}) {
  return _then(_SessionProviderSessionSummary(
sessionProviderSessionId: null == sessionProviderSessionId ? _self.sessionProviderSessionId : sessionProviderSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,sessionId: null == sessionId ? _self.sessionId : sessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,providerSessionConfigId: null == providerSessionConfigId ? _self.providerSessionConfigId : providerSessionConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,providerSessionKey: null == providerSessionKey ? _self.providerSessionKey : providerSessionKey // ignore: cast_nullable_to_non_nullable
as String,providerSessionRef: freezed == providerSessionRef ? _self.providerSessionRef : providerSessionRef // ignore: cast_nullable_to_non_nullable
as String?,providerObjectInstanceGraphIdentityId: freezed == providerObjectInstanceGraphIdentityId ? _self.providerObjectInstanceGraphIdentityId : providerObjectInstanceGraphIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue?,providerClassInstanceIdentityId: freezed == providerClassInstanceIdentityId ? _self.providerClassInstanceIdentityId : providerClassInstanceIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue?,providerObjectInstanceGraphBranchId: freezed == providerObjectInstanceGraphBranchId ? _self.providerObjectInstanceGraphBranchId : providerObjectInstanceGraphBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,metadataJson: null == metadataJson ? _self._metadataJson : metadataJson // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}

// dart format on
