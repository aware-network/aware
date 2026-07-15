// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'environment_service_operation_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$EnvironmentServiceOperation {

 String get service; String? get operation;
/// Create a copy of EnvironmentServiceOperation
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$EnvironmentServiceOperationCopyWith<EnvironmentServiceOperation> get copyWith => _$EnvironmentServiceOperationCopyWithImpl<EnvironmentServiceOperation>(this as EnvironmentServiceOperation, _$identity);

  /// Serializes this EnvironmentServiceOperation to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is EnvironmentServiceOperation&&(identical(other.service, service) || other.service == service)&&(identical(other.operation, operation) || other.operation == operation));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,service,operation);

@override
String toString() {
  return 'EnvironmentServiceOperation(service: $service, operation: $operation)';
}


}

/// @nodoc
abstract mixin class $EnvironmentServiceOperationCopyWith<$Res>  {
  factory $EnvironmentServiceOperationCopyWith(EnvironmentServiceOperation value, $Res Function(EnvironmentServiceOperation) _then) = _$EnvironmentServiceOperationCopyWithImpl;
@useResult
$Res call({
 String service, String? operation
});




}
/// @nodoc
class _$EnvironmentServiceOperationCopyWithImpl<$Res>
    implements $EnvironmentServiceOperationCopyWith<$Res> {
  _$EnvironmentServiceOperationCopyWithImpl(this._self, this._then);

  final EnvironmentServiceOperation _self;
  final $Res Function(EnvironmentServiceOperation) _then;

/// Create a copy of EnvironmentServiceOperation
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? service = null,Object? operation = freezed,}) {
  return _then(_self.copyWith(
service: null == service ? _self.service : service // ignore: cast_nullable_to_non_nullable
as String,operation: freezed == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [EnvironmentServiceOperation].
extension EnvironmentServiceOperationPatterns on EnvironmentServiceOperation {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _EnvironmentServiceOperation value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _EnvironmentServiceOperation() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _EnvironmentServiceOperation value)  def,}){
final _that = this;
switch (_that) {
case _EnvironmentServiceOperation():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _EnvironmentServiceOperation value)?  def,}){
final _that = this;
switch (_that) {
case _EnvironmentServiceOperation() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String service,  String? operation)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _EnvironmentServiceOperation() when def != null:
return def(_that.service,_that.operation);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String service,  String? operation)  def,}) {final _that = this;
switch (_that) {
case _EnvironmentServiceOperation():
return def(_that.service,_that.operation);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String service,  String? operation)?  def,}) {final _that = this;
switch (_that) {
case _EnvironmentServiceOperation() when def != null:
return def(_that.service,_that.operation);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _EnvironmentServiceOperation implements EnvironmentServiceOperation {
   _EnvironmentServiceOperation({required this.service, this.operation});
  factory _EnvironmentServiceOperation.fromJson(Map<String, dynamic> json) => _$EnvironmentServiceOperationFromJson(json);

@override final  String service;
@override final  String? operation;

/// Create a copy of EnvironmentServiceOperation
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$EnvironmentServiceOperationCopyWith<_EnvironmentServiceOperation> get copyWith => __$EnvironmentServiceOperationCopyWithImpl<_EnvironmentServiceOperation>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$EnvironmentServiceOperationToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _EnvironmentServiceOperation&&(identical(other.service, service) || other.service == service)&&(identical(other.operation, operation) || other.operation == operation));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,service,operation);

@override
String toString() {
  return 'EnvironmentServiceOperation.def(service: $service, operation: $operation)';
}


}

/// @nodoc
abstract mixin class _$EnvironmentServiceOperationCopyWith<$Res> implements $EnvironmentServiceOperationCopyWith<$Res> {
  factory _$EnvironmentServiceOperationCopyWith(_EnvironmentServiceOperation value, $Res Function(_EnvironmentServiceOperation) _then) = __$EnvironmentServiceOperationCopyWithImpl;
@override @useResult
$Res call({
 String service, String? operation
});




}
/// @nodoc
class __$EnvironmentServiceOperationCopyWithImpl<$Res>
    implements _$EnvironmentServiceOperationCopyWith<$Res> {
  __$EnvironmentServiceOperationCopyWithImpl(this._self, this._then);

  final _EnvironmentServiceOperation _self;
  final $Res Function(_EnvironmentServiceOperation) _then;

/// Create a copy of EnvironmentServiceOperation
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? service = null,Object? operation = freezed,}) {
  return _then(_EnvironmentServiceOperation(
service: null == service ? _self.service : service // ignore: cast_nullable_to_non_nullable
as String,operation: freezed == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

// dart format on
