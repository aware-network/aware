// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'mount_status_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$InterfaceMountStatusViewStateV1 {

 bool get mounted; bool get ready; String get status; String? get summary; String? get error; String? get activeLayoutKey; String? get activeSectionKey;
/// Create a copy of InterfaceMountStatusViewStateV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceMountStatusViewStateV1CopyWith<InterfaceMountStatusViewStateV1> get copyWith => _$InterfaceMountStatusViewStateV1CopyWithImpl<InterfaceMountStatusViewStateV1>(this as InterfaceMountStatusViewStateV1, _$identity);

  /// Serializes this InterfaceMountStatusViewStateV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceMountStatusViewStateV1&&(identical(other.mounted, mounted) || other.mounted == mounted)&&(identical(other.ready, ready) || other.ready == ready)&&(identical(other.status, status) || other.status == status)&&(identical(other.summary, summary) || other.summary == summary)&&(identical(other.error, error) || other.error == error)&&(identical(other.activeLayoutKey, activeLayoutKey) || other.activeLayoutKey == activeLayoutKey)&&(identical(other.activeSectionKey, activeSectionKey) || other.activeSectionKey == activeSectionKey));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,mounted,ready,status,summary,error,activeLayoutKey,activeSectionKey);

@override
String toString() {
  return 'InterfaceMountStatusViewStateV1(mounted: $mounted, ready: $ready, status: $status, summary: $summary, error: $error, activeLayoutKey: $activeLayoutKey, activeSectionKey: $activeSectionKey)';
}


}

/// @nodoc
abstract mixin class $InterfaceMountStatusViewStateV1CopyWith<$Res>  {
  factory $InterfaceMountStatusViewStateV1CopyWith(InterfaceMountStatusViewStateV1 value, $Res Function(InterfaceMountStatusViewStateV1) _then) = _$InterfaceMountStatusViewStateV1CopyWithImpl;
@useResult
$Res call({
 bool mounted, bool ready, String status, String? summary, String? error, String? activeLayoutKey, String? activeSectionKey
});




}
/// @nodoc
class _$InterfaceMountStatusViewStateV1CopyWithImpl<$Res>
    implements $InterfaceMountStatusViewStateV1CopyWith<$Res> {
  _$InterfaceMountStatusViewStateV1CopyWithImpl(this._self, this._then);

  final InterfaceMountStatusViewStateV1 _self;
  final $Res Function(InterfaceMountStatusViewStateV1) _then;

/// Create a copy of InterfaceMountStatusViewStateV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? mounted = null,Object? ready = null,Object? status = null,Object? summary = freezed,Object? error = freezed,Object? activeLayoutKey = freezed,Object? activeSectionKey = freezed,}) {
  return _then(_self.copyWith(
mounted: null == mounted ? _self.mounted : mounted // ignore: cast_nullable_to_non_nullable
as bool,ready: null == ready ? _self.ready : ready // ignore: cast_nullable_to_non_nullable
as bool,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,activeLayoutKey: freezed == activeLayoutKey ? _self.activeLayoutKey : activeLayoutKey // ignore: cast_nullable_to_non_nullable
as String?,activeSectionKey: freezed == activeSectionKey ? _self.activeSectionKey : activeSectionKey // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfaceMountStatusViewStateV1].
extension InterfaceMountStatusViewStateV1Patterns on InterfaceMountStatusViewStateV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfaceMountStatusViewStateV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfaceMountStatusViewStateV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfaceMountStatusViewStateV1 value)  def,}){
final _that = this;
switch (_that) {
case _InterfaceMountStatusViewStateV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfaceMountStatusViewStateV1 value)?  def,}){
final _that = this;
switch (_that) {
case _InterfaceMountStatusViewStateV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( bool mounted,  bool ready,  String status,  String? summary,  String? error,  String? activeLayoutKey,  String? activeSectionKey)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfaceMountStatusViewStateV1() when def != null:
return def(_that.mounted,_that.ready,_that.status,_that.summary,_that.error,_that.activeLayoutKey,_that.activeSectionKey);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( bool mounted,  bool ready,  String status,  String? summary,  String? error,  String? activeLayoutKey,  String? activeSectionKey)  def,}) {final _that = this;
switch (_that) {
case _InterfaceMountStatusViewStateV1():
return def(_that.mounted,_that.ready,_that.status,_that.summary,_that.error,_that.activeLayoutKey,_that.activeSectionKey);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( bool mounted,  bool ready,  String status,  String? summary,  String? error,  String? activeLayoutKey,  String? activeSectionKey)?  def,}) {final _that = this;
switch (_that) {
case _InterfaceMountStatusViewStateV1() when def != null:
return def(_that.mounted,_that.ready,_that.status,_that.summary,_that.error,_that.activeLayoutKey,_that.activeSectionKey);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfaceMountStatusViewStateV1 implements InterfaceMountStatusViewStateV1 {
   _InterfaceMountStatusViewStateV1({required this.mounted, required this.ready, required this.status, this.summary, this.error, this.activeLayoutKey, this.activeSectionKey});
  factory _InterfaceMountStatusViewStateV1.fromJson(Map<String, dynamic> json) => _$InterfaceMountStatusViewStateV1FromJson(json);

@override final  bool mounted;
@override final  bool ready;
@override final  String status;
@override final  String? summary;
@override final  String? error;
@override final  String? activeLayoutKey;
@override final  String? activeSectionKey;

/// Create a copy of InterfaceMountStatusViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfaceMountStatusViewStateV1CopyWith<_InterfaceMountStatusViewStateV1> get copyWith => __$InterfaceMountStatusViewStateV1CopyWithImpl<_InterfaceMountStatusViewStateV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceMountStatusViewStateV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfaceMountStatusViewStateV1&&(identical(other.mounted, mounted) || other.mounted == mounted)&&(identical(other.ready, ready) || other.ready == ready)&&(identical(other.status, status) || other.status == status)&&(identical(other.summary, summary) || other.summary == summary)&&(identical(other.error, error) || other.error == error)&&(identical(other.activeLayoutKey, activeLayoutKey) || other.activeLayoutKey == activeLayoutKey)&&(identical(other.activeSectionKey, activeSectionKey) || other.activeSectionKey == activeSectionKey));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,mounted,ready,status,summary,error,activeLayoutKey,activeSectionKey);

@override
String toString() {
  return 'InterfaceMountStatusViewStateV1.def(mounted: $mounted, ready: $ready, status: $status, summary: $summary, error: $error, activeLayoutKey: $activeLayoutKey, activeSectionKey: $activeSectionKey)';
}


}

/// @nodoc
abstract mixin class _$InterfaceMountStatusViewStateV1CopyWith<$Res> implements $InterfaceMountStatusViewStateV1CopyWith<$Res> {
  factory _$InterfaceMountStatusViewStateV1CopyWith(_InterfaceMountStatusViewStateV1 value, $Res Function(_InterfaceMountStatusViewStateV1) _then) = __$InterfaceMountStatusViewStateV1CopyWithImpl;
@override @useResult
$Res call({
 bool mounted, bool ready, String status, String? summary, String? error, String? activeLayoutKey, String? activeSectionKey
});




}
/// @nodoc
class __$InterfaceMountStatusViewStateV1CopyWithImpl<$Res>
    implements _$InterfaceMountStatusViewStateV1CopyWith<$Res> {
  __$InterfaceMountStatusViewStateV1CopyWithImpl(this._self, this._then);

  final _InterfaceMountStatusViewStateV1 _self;
  final $Res Function(_InterfaceMountStatusViewStateV1) _then;

/// Create a copy of InterfaceMountStatusViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? mounted = null,Object? ready = null,Object? status = null,Object? summary = freezed,Object? error = freezed,Object? activeLayoutKey = freezed,Object? activeSectionKey = freezed,}) {
  return _then(_InterfaceMountStatusViewStateV1(
mounted: null == mounted ? _self.mounted : mounted // ignore: cast_nullable_to_non_nullable
as bool,ready: null == ready ? _self.ready : ready // ignore: cast_nullable_to_non_nullable
as bool,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,activeLayoutKey: freezed == activeLayoutKey ? _self.activeLayoutKey : activeLayoutKey // ignore: cast_nullable_to_non_nullable
as String?,activeSectionKey: freezed == activeSectionKey ? _self.activeSectionKey : activeSectionKey // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

// dart format on
