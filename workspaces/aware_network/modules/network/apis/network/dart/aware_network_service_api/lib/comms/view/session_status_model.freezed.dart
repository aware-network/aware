// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'session_status_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$NetworkNodeSessionStatusViewStateV1 {

 bool get managed; bool get available; bool get ready; String get phase; String? get activeTargetId; String? get targetKey; String? get displayName; String? get backendKind; String? get summary; String? get error; List<String> get recentLogLines; List<Map<String, dynamic>> get targetStatuses;
/// Create a copy of NetworkNodeSessionStatusViewStateV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NetworkNodeSessionStatusViewStateV1CopyWith<NetworkNodeSessionStatusViewStateV1> get copyWith => _$NetworkNodeSessionStatusViewStateV1CopyWithImpl<NetworkNodeSessionStatusViewStateV1>(this as NetworkNodeSessionStatusViewStateV1, _$identity);

  /// Serializes this NetworkNodeSessionStatusViewStateV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NetworkNodeSessionStatusViewStateV1&&(identical(other.managed, managed) || other.managed == managed)&&(identical(other.available, available) || other.available == available)&&(identical(other.ready, ready) || other.ready == ready)&&(identical(other.phase, phase) || other.phase == phase)&&(identical(other.activeTargetId, activeTargetId) || other.activeTargetId == activeTargetId)&&(identical(other.targetKey, targetKey) || other.targetKey == targetKey)&&(identical(other.displayName, displayName) || other.displayName == displayName)&&(identical(other.backendKind, backendKind) || other.backendKind == backendKind)&&(identical(other.summary, summary) || other.summary == summary)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other.recentLogLines, recentLogLines)&&const DeepCollectionEquality().equals(other.targetStatuses, targetStatuses));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,managed,available,ready,phase,activeTargetId,targetKey,displayName,backendKind,summary,error,const DeepCollectionEquality().hash(recentLogLines),const DeepCollectionEquality().hash(targetStatuses));

@override
String toString() {
  return 'NetworkNodeSessionStatusViewStateV1(managed: $managed, available: $available, ready: $ready, phase: $phase, activeTargetId: $activeTargetId, targetKey: $targetKey, displayName: $displayName, backendKind: $backendKind, summary: $summary, error: $error, recentLogLines: $recentLogLines, targetStatuses: $targetStatuses)';
}


}

/// @nodoc
abstract mixin class $NetworkNodeSessionStatusViewStateV1CopyWith<$Res>  {
  factory $NetworkNodeSessionStatusViewStateV1CopyWith(NetworkNodeSessionStatusViewStateV1 value, $Res Function(NetworkNodeSessionStatusViewStateV1) _then) = _$NetworkNodeSessionStatusViewStateV1CopyWithImpl;
@useResult
$Res call({
 bool managed, bool available, bool ready, String phase, String? activeTargetId, String? targetKey, String? displayName, String? backendKind, String? summary, String? error, List<String> recentLogLines, List<Map<String, dynamic>> targetStatuses
});




}
/// @nodoc
class _$NetworkNodeSessionStatusViewStateV1CopyWithImpl<$Res>
    implements $NetworkNodeSessionStatusViewStateV1CopyWith<$Res> {
  _$NetworkNodeSessionStatusViewStateV1CopyWithImpl(this._self, this._then);

  final NetworkNodeSessionStatusViewStateV1 _self;
  final $Res Function(NetworkNodeSessionStatusViewStateV1) _then;

/// Create a copy of NetworkNodeSessionStatusViewStateV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? managed = null,Object? available = null,Object? ready = null,Object? phase = null,Object? activeTargetId = freezed,Object? targetKey = freezed,Object? displayName = freezed,Object? backendKind = freezed,Object? summary = freezed,Object? error = freezed,Object? recentLogLines = null,Object? targetStatuses = null,}) {
  return _then(_self.copyWith(
managed: null == managed ? _self.managed : managed // ignore: cast_nullable_to_non_nullable
as bool,available: null == available ? _self.available : available // ignore: cast_nullable_to_non_nullable
as bool,ready: null == ready ? _self.ready : ready // ignore: cast_nullable_to_non_nullable
as bool,phase: null == phase ? _self.phase : phase // ignore: cast_nullable_to_non_nullable
as String,activeTargetId: freezed == activeTargetId ? _self.activeTargetId : activeTargetId // ignore: cast_nullable_to_non_nullable
as String?,targetKey: freezed == targetKey ? _self.targetKey : targetKey // ignore: cast_nullable_to_non_nullable
as String?,displayName: freezed == displayName ? _self.displayName : displayName // ignore: cast_nullable_to_non_nullable
as String?,backendKind: freezed == backendKind ? _self.backendKind : backendKind // ignore: cast_nullable_to_non_nullable
as String?,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,recentLogLines: null == recentLogLines ? _self.recentLogLines : recentLogLines // ignore: cast_nullable_to_non_nullable
as List<String>,targetStatuses: null == targetStatuses ? _self.targetStatuses : targetStatuses // ignore: cast_nullable_to_non_nullable
as List<Map<String, dynamic>>,
  ));
}

}


/// Adds pattern-matching-related methods to [NetworkNodeSessionStatusViewStateV1].
extension NetworkNodeSessionStatusViewStateV1Patterns on NetworkNodeSessionStatusViewStateV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NetworkNodeSessionStatusViewStateV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NetworkNodeSessionStatusViewStateV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NetworkNodeSessionStatusViewStateV1 value)  def,}){
final _that = this;
switch (_that) {
case _NetworkNodeSessionStatusViewStateV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NetworkNodeSessionStatusViewStateV1 value)?  def,}){
final _that = this;
switch (_that) {
case _NetworkNodeSessionStatusViewStateV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( bool managed,  bool available,  bool ready,  String phase,  String? activeTargetId,  String? targetKey,  String? displayName,  String? backendKind,  String? summary,  String? error,  List<String> recentLogLines,  List<Map<String, dynamic>> targetStatuses)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NetworkNodeSessionStatusViewStateV1() when def != null:
return def(_that.managed,_that.available,_that.ready,_that.phase,_that.activeTargetId,_that.targetKey,_that.displayName,_that.backendKind,_that.summary,_that.error,_that.recentLogLines,_that.targetStatuses);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( bool managed,  bool available,  bool ready,  String phase,  String? activeTargetId,  String? targetKey,  String? displayName,  String? backendKind,  String? summary,  String? error,  List<String> recentLogLines,  List<Map<String, dynamic>> targetStatuses)  def,}) {final _that = this;
switch (_that) {
case _NetworkNodeSessionStatusViewStateV1():
return def(_that.managed,_that.available,_that.ready,_that.phase,_that.activeTargetId,_that.targetKey,_that.displayName,_that.backendKind,_that.summary,_that.error,_that.recentLogLines,_that.targetStatuses);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( bool managed,  bool available,  bool ready,  String phase,  String? activeTargetId,  String? targetKey,  String? displayName,  String? backendKind,  String? summary,  String? error,  List<String> recentLogLines,  List<Map<String, dynamic>> targetStatuses)?  def,}) {final _that = this;
switch (_that) {
case _NetworkNodeSessionStatusViewStateV1() when def != null:
return def(_that.managed,_that.available,_that.ready,_that.phase,_that.activeTargetId,_that.targetKey,_that.displayName,_that.backendKind,_that.summary,_that.error,_that.recentLogLines,_that.targetStatuses);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NetworkNodeSessionStatusViewStateV1 implements NetworkNodeSessionStatusViewStateV1 {
   _NetworkNodeSessionStatusViewStateV1({required this.managed, required this.available, required this.ready, required this.phase, this.activeTargetId, this.targetKey, this.displayName, this.backendKind, this.summary, this.error, final  List<String> recentLogLines = const [], final  List<Map<String, dynamic>> targetStatuses = const []}): _recentLogLines = recentLogLines,_targetStatuses = targetStatuses;
  factory _NetworkNodeSessionStatusViewStateV1.fromJson(Map<String, dynamic> json) => _$NetworkNodeSessionStatusViewStateV1FromJson(json);

@override final  bool managed;
@override final  bool available;
@override final  bool ready;
@override final  String phase;
@override final  String? activeTargetId;
@override final  String? targetKey;
@override final  String? displayName;
@override final  String? backendKind;
@override final  String? summary;
@override final  String? error;
 final  List<String> _recentLogLines;
@override@JsonKey() List<String> get recentLogLines {
  if (_recentLogLines is EqualUnmodifiableListView) return _recentLogLines;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_recentLogLines);
}

 final  List<Map<String, dynamic>> _targetStatuses;
@override@JsonKey() List<Map<String, dynamic>> get targetStatuses {
  if (_targetStatuses is EqualUnmodifiableListView) return _targetStatuses;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_targetStatuses);
}


/// Create a copy of NetworkNodeSessionStatusViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NetworkNodeSessionStatusViewStateV1CopyWith<_NetworkNodeSessionStatusViewStateV1> get copyWith => __$NetworkNodeSessionStatusViewStateV1CopyWithImpl<_NetworkNodeSessionStatusViewStateV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NetworkNodeSessionStatusViewStateV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NetworkNodeSessionStatusViewStateV1&&(identical(other.managed, managed) || other.managed == managed)&&(identical(other.available, available) || other.available == available)&&(identical(other.ready, ready) || other.ready == ready)&&(identical(other.phase, phase) || other.phase == phase)&&(identical(other.activeTargetId, activeTargetId) || other.activeTargetId == activeTargetId)&&(identical(other.targetKey, targetKey) || other.targetKey == targetKey)&&(identical(other.displayName, displayName) || other.displayName == displayName)&&(identical(other.backendKind, backendKind) || other.backendKind == backendKind)&&(identical(other.summary, summary) || other.summary == summary)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other._recentLogLines, _recentLogLines)&&const DeepCollectionEquality().equals(other._targetStatuses, _targetStatuses));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,managed,available,ready,phase,activeTargetId,targetKey,displayName,backendKind,summary,error,const DeepCollectionEquality().hash(_recentLogLines),const DeepCollectionEquality().hash(_targetStatuses));

@override
String toString() {
  return 'NetworkNodeSessionStatusViewStateV1.def(managed: $managed, available: $available, ready: $ready, phase: $phase, activeTargetId: $activeTargetId, targetKey: $targetKey, displayName: $displayName, backendKind: $backendKind, summary: $summary, error: $error, recentLogLines: $recentLogLines, targetStatuses: $targetStatuses)';
}


}

/// @nodoc
abstract mixin class _$NetworkNodeSessionStatusViewStateV1CopyWith<$Res> implements $NetworkNodeSessionStatusViewStateV1CopyWith<$Res> {
  factory _$NetworkNodeSessionStatusViewStateV1CopyWith(_NetworkNodeSessionStatusViewStateV1 value, $Res Function(_NetworkNodeSessionStatusViewStateV1) _then) = __$NetworkNodeSessionStatusViewStateV1CopyWithImpl;
@override @useResult
$Res call({
 bool managed, bool available, bool ready, String phase, String? activeTargetId, String? targetKey, String? displayName, String? backendKind, String? summary, String? error, List<String> recentLogLines, List<Map<String, dynamic>> targetStatuses
});




}
/// @nodoc
class __$NetworkNodeSessionStatusViewStateV1CopyWithImpl<$Res>
    implements _$NetworkNodeSessionStatusViewStateV1CopyWith<$Res> {
  __$NetworkNodeSessionStatusViewStateV1CopyWithImpl(this._self, this._then);

  final _NetworkNodeSessionStatusViewStateV1 _self;
  final $Res Function(_NetworkNodeSessionStatusViewStateV1) _then;

/// Create a copy of NetworkNodeSessionStatusViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? managed = null,Object? available = null,Object? ready = null,Object? phase = null,Object? activeTargetId = freezed,Object? targetKey = freezed,Object? displayName = freezed,Object? backendKind = freezed,Object? summary = freezed,Object? error = freezed,Object? recentLogLines = null,Object? targetStatuses = null,}) {
  return _then(_NetworkNodeSessionStatusViewStateV1(
managed: null == managed ? _self.managed : managed // ignore: cast_nullable_to_non_nullable
as bool,available: null == available ? _self.available : available // ignore: cast_nullable_to_non_nullable
as bool,ready: null == ready ? _self.ready : ready // ignore: cast_nullable_to_non_nullable
as bool,phase: null == phase ? _self.phase : phase // ignore: cast_nullable_to_non_nullable
as String,activeTargetId: freezed == activeTargetId ? _self.activeTargetId : activeTargetId // ignore: cast_nullable_to_non_nullable
as String?,targetKey: freezed == targetKey ? _self.targetKey : targetKey // ignore: cast_nullable_to_non_nullable
as String?,displayName: freezed == displayName ? _self.displayName : displayName // ignore: cast_nullable_to_non_nullable
as String?,backendKind: freezed == backendKind ? _self.backendKind : backendKind // ignore: cast_nullable_to_non_nullable
as String?,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,recentLogLines: null == recentLogLines ? _self._recentLogLines : recentLogLines // ignore: cast_nullable_to_non_nullable
as List<String>,targetStatuses: null == targetStatuses ? _self._targetStatuses : targetStatuses // ignore: cast_nullable_to_non_nullable
as List<Map<String, dynamic>>,
  ));
}


}

// dart format on
