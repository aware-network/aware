// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'sdk_operation_dependency_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$SdkOperationDependency {

@UuidValueConverter() UuidValue get id; SdkOperation? get targetSdkOperation; String get targetOperationRef; String get targetSdkName; String get targetOperationName; String? get targetPackageName; String get role; int get order;@JsonKey(name: 'required') bool get required_; String? get description;@UuidValueConverter() UuidValue get sdkOperationId;@UuidValueConverter() UuidValue? get targetSdkOperationId;
/// Create a copy of SdkOperationDependency
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$SdkOperationDependencyCopyWith<SdkOperationDependency> get copyWith => _$SdkOperationDependencyCopyWithImpl<SdkOperationDependency>(this as SdkOperationDependency, _$identity);

  /// Serializes this SdkOperationDependency to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is SdkOperationDependency&&(identical(other.id, id) || other.id == id)&&(identical(other.targetSdkOperation, targetSdkOperation) || other.targetSdkOperation == targetSdkOperation)&&(identical(other.targetOperationRef, targetOperationRef) || other.targetOperationRef == targetOperationRef)&&(identical(other.targetSdkName, targetSdkName) || other.targetSdkName == targetSdkName)&&(identical(other.targetOperationName, targetOperationName) || other.targetOperationName == targetOperationName)&&(identical(other.targetPackageName, targetPackageName) || other.targetPackageName == targetPackageName)&&(identical(other.role, role) || other.role == role)&&(identical(other.order, order) || other.order == order)&&(identical(other.required_, required_) || other.required_ == required_)&&(identical(other.description, description) || other.description == description)&&(identical(other.sdkOperationId, sdkOperationId) || other.sdkOperationId == sdkOperationId)&&(identical(other.targetSdkOperationId, targetSdkOperationId) || other.targetSdkOperationId == targetSdkOperationId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,targetSdkOperation,targetOperationRef,targetSdkName,targetOperationName,targetPackageName,role,order,required_,description,sdkOperationId,targetSdkOperationId);

@override
String toString() {
  return 'SdkOperationDependency(id: $id, targetSdkOperation: $targetSdkOperation, targetOperationRef: $targetOperationRef, targetSdkName: $targetSdkName, targetOperationName: $targetOperationName, targetPackageName: $targetPackageName, role: $role, order: $order, required_: $required_, description: $description, sdkOperationId: $sdkOperationId, targetSdkOperationId: $targetSdkOperationId)';
}


}

/// @nodoc
abstract mixin class $SdkOperationDependencyCopyWith<$Res>  {
  factory $SdkOperationDependencyCopyWith(SdkOperationDependency value, $Res Function(SdkOperationDependency) _then) = _$SdkOperationDependencyCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue id, SdkOperation? targetSdkOperation, String targetOperationRef, String targetSdkName, String targetOperationName, String? targetPackageName, String role, int order,@JsonKey(name: 'required') bool required_, String? description,@UuidValueConverter() UuidValue sdkOperationId,@UuidValueConverter() UuidValue? targetSdkOperationId
});


$SdkOperationCopyWith<$Res>? get targetSdkOperation;

}
/// @nodoc
class _$SdkOperationDependencyCopyWithImpl<$Res>
    implements $SdkOperationDependencyCopyWith<$Res> {
  _$SdkOperationDependencyCopyWithImpl(this._self, this._then);

  final SdkOperationDependency _self;
  final $Res Function(SdkOperationDependency) _then;

/// Create a copy of SdkOperationDependency
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? id = null,Object? targetSdkOperation = freezed,Object? targetOperationRef = null,Object? targetSdkName = null,Object? targetOperationName = null,Object? targetPackageName = freezed,Object? role = null,Object? order = null,Object? required_ = null,Object? description = freezed,Object? sdkOperationId = null,Object? targetSdkOperationId = freezed,}) {
  return _then(_self.copyWith(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,targetSdkOperation: freezed == targetSdkOperation ? _self.targetSdkOperation : targetSdkOperation // ignore: cast_nullable_to_non_nullable
as SdkOperation?,targetOperationRef: null == targetOperationRef ? _self.targetOperationRef : targetOperationRef // ignore: cast_nullable_to_non_nullable
as String,targetSdkName: null == targetSdkName ? _self.targetSdkName : targetSdkName // ignore: cast_nullable_to_non_nullable
as String,targetOperationName: null == targetOperationName ? _self.targetOperationName : targetOperationName // ignore: cast_nullable_to_non_nullable
as String,targetPackageName: freezed == targetPackageName ? _self.targetPackageName : targetPackageName // ignore: cast_nullable_to_non_nullable
as String?,role: null == role ? _self.role : role // ignore: cast_nullable_to_non_nullable
as String,order: null == order ? _self.order : order // ignore: cast_nullable_to_non_nullable
as int,required_: null == required_ ? _self.required_ : required_ // ignore: cast_nullable_to_non_nullable
as bool,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,sdkOperationId: null == sdkOperationId ? _self.sdkOperationId : sdkOperationId // ignore: cast_nullable_to_non_nullable
as UuidValue,targetSdkOperationId: freezed == targetSdkOperationId ? _self.targetSdkOperationId : targetSdkOperationId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}
/// Create a copy of SdkOperationDependency
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$SdkOperationCopyWith<$Res>? get targetSdkOperation {
    if (_self.targetSdkOperation == null) {
    return null;
  }

  return $SdkOperationCopyWith<$Res>(_self.targetSdkOperation!, (value) {
    return _then(_self.copyWith(targetSdkOperation: value));
  });
}
}


/// Adds pattern-matching-related methods to [SdkOperationDependency].
extension SdkOperationDependencyPatterns on SdkOperationDependency {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _SdkOperationDependency value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _SdkOperationDependency() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _SdkOperationDependency value)  def,}){
final _that = this;
switch (_that) {
case _SdkOperationDependency():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _SdkOperationDependency value)?  def,}){
final _that = this;
switch (_that) {
case _SdkOperationDependency() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue id,  SdkOperation? targetSdkOperation,  String targetOperationRef,  String targetSdkName,  String targetOperationName,  String? targetPackageName,  String role,  int order, @JsonKey(name: 'required')  bool required_,  String? description, @UuidValueConverter()  UuidValue sdkOperationId, @UuidValueConverter()  UuidValue? targetSdkOperationId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _SdkOperationDependency() when def != null:
return def(_that.id,_that.targetSdkOperation,_that.targetOperationRef,_that.targetSdkName,_that.targetOperationName,_that.targetPackageName,_that.role,_that.order,_that.required_,_that.description,_that.sdkOperationId,_that.targetSdkOperationId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue id,  SdkOperation? targetSdkOperation,  String targetOperationRef,  String targetSdkName,  String targetOperationName,  String? targetPackageName,  String role,  int order, @JsonKey(name: 'required')  bool required_,  String? description, @UuidValueConverter()  UuidValue sdkOperationId, @UuidValueConverter()  UuidValue? targetSdkOperationId)  def,}) {final _that = this;
switch (_that) {
case _SdkOperationDependency():
return def(_that.id,_that.targetSdkOperation,_that.targetOperationRef,_that.targetSdkName,_that.targetOperationName,_that.targetPackageName,_that.role,_that.order,_that.required_,_that.description,_that.sdkOperationId,_that.targetSdkOperationId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue id,  SdkOperation? targetSdkOperation,  String targetOperationRef,  String targetSdkName,  String targetOperationName,  String? targetPackageName,  String role,  int order, @JsonKey(name: 'required')  bool required_,  String? description, @UuidValueConverter()  UuidValue sdkOperationId, @UuidValueConverter()  UuidValue? targetSdkOperationId)?  def,}) {final _that = this;
switch (_that) {
case _SdkOperationDependency() when def != null:
return def(_that.id,_that.targetSdkOperation,_that.targetOperationRef,_that.targetSdkName,_that.targetOperationName,_that.targetPackageName,_that.role,_that.order,_that.required_,_that.description,_that.sdkOperationId,_that.targetSdkOperationId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _SdkOperationDependency implements SdkOperationDependency {
   _SdkOperationDependency({@UuidValueConverter() required this.id, this.targetSdkOperation, required this.targetOperationRef, required this.targetSdkName, required this.targetOperationName, this.targetPackageName, required this.role, required this.order, @JsonKey(name: 'required') required this.required_, this.description, @UuidValueConverter() required this.sdkOperationId, @UuidValueConverter() this.targetSdkOperationId});
  factory _SdkOperationDependency.fromJson(Map<String, dynamic> json) => _$SdkOperationDependencyFromJson(json);

@override@UuidValueConverter() final  UuidValue id;
@override final  SdkOperation? targetSdkOperation;
@override final  String targetOperationRef;
@override final  String targetSdkName;
@override final  String targetOperationName;
@override final  String? targetPackageName;
@override final  String role;
@override final  int order;
@override@JsonKey(name: 'required') final  bool required_;
@override final  String? description;
@override@UuidValueConverter() final  UuidValue sdkOperationId;
@override@UuidValueConverter() final  UuidValue? targetSdkOperationId;

/// Create a copy of SdkOperationDependency
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$SdkOperationDependencyCopyWith<_SdkOperationDependency> get copyWith => __$SdkOperationDependencyCopyWithImpl<_SdkOperationDependency>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$SdkOperationDependencyToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _SdkOperationDependency&&(identical(other.id, id) || other.id == id)&&(identical(other.targetSdkOperation, targetSdkOperation) || other.targetSdkOperation == targetSdkOperation)&&(identical(other.targetOperationRef, targetOperationRef) || other.targetOperationRef == targetOperationRef)&&(identical(other.targetSdkName, targetSdkName) || other.targetSdkName == targetSdkName)&&(identical(other.targetOperationName, targetOperationName) || other.targetOperationName == targetOperationName)&&(identical(other.targetPackageName, targetPackageName) || other.targetPackageName == targetPackageName)&&(identical(other.role, role) || other.role == role)&&(identical(other.order, order) || other.order == order)&&(identical(other.required_, required_) || other.required_ == required_)&&(identical(other.description, description) || other.description == description)&&(identical(other.sdkOperationId, sdkOperationId) || other.sdkOperationId == sdkOperationId)&&(identical(other.targetSdkOperationId, targetSdkOperationId) || other.targetSdkOperationId == targetSdkOperationId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,targetSdkOperation,targetOperationRef,targetSdkName,targetOperationName,targetPackageName,role,order,required_,description,sdkOperationId,targetSdkOperationId);

@override
String toString() {
  return 'SdkOperationDependency.def(id: $id, targetSdkOperation: $targetSdkOperation, targetOperationRef: $targetOperationRef, targetSdkName: $targetSdkName, targetOperationName: $targetOperationName, targetPackageName: $targetPackageName, role: $role, order: $order, required_: $required_, description: $description, sdkOperationId: $sdkOperationId, targetSdkOperationId: $targetSdkOperationId)';
}


}

/// @nodoc
abstract mixin class _$SdkOperationDependencyCopyWith<$Res> implements $SdkOperationDependencyCopyWith<$Res> {
  factory _$SdkOperationDependencyCopyWith(_SdkOperationDependency value, $Res Function(_SdkOperationDependency) _then) = __$SdkOperationDependencyCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue id, SdkOperation? targetSdkOperation, String targetOperationRef, String targetSdkName, String targetOperationName, String? targetPackageName, String role, int order,@JsonKey(name: 'required') bool required_, String? description,@UuidValueConverter() UuidValue sdkOperationId,@UuidValueConverter() UuidValue? targetSdkOperationId
});


@override $SdkOperationCopyWith<$Res>? get targetSdkOperation;

}
/// @nodoc
class __$SdkOperationDependencyCopyWithImpl<$Res>
    implements _$SdkOperationDependencyCopyWith<$Res> {
  __$SdkOperationDependencyCopyWithImpl(this._self, this._then);

  final _SdkOperationDependency _self;
  final $Res Function(_SdkOperationDependency) _then;

/// Create a copy of SdkOperationDependency
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? id = null,Object? targetSdkOperation = freezed,Object? targetOperationRef = null,Object? targetSdkName = null,Object? targetOperationName = null,Object? targetPackageName = freezed,Object? role = null,Object? order = null,Object? required_ = null,Object? description = freezed,Object? sdkOperationId = null,Object? targetSdkOperationId = freezed,}) {
  return _then(_SdkOperationDependency(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,targetSdkOperation: freezed == targetSdkOperation ? _self.targetSdkOperation : targetSdkOperation // ignore: cast_nullable_to_non_nullable
as SdkOperation?,targetOperationRef: null == targetOperationRef ? _self.targetOperationRef : targetOperationRef // ignore: cast_nullable_to_non_nullable
as String,targetSdkName: null == targetSdkName ? _self.targetSdkName : targetSdkName // ignore: cast_nullable_to_non_nullable
as String,targetOperationName: null == targetOperationName ? _self.targetOperationName : targetOperationName // ignore: cast_nullable_to_non_nullable
as String,targetPackageName: freezed == targetPackageName ? _self.targetPackageName : targetPackageName // ignore: cast_nullable_to_non_nullable
as String?,role: null == role ? _self.role : role // ignore: cast_nullable_to_non_nullable
as String,order: null == order ? _self.order : order // ignore: cast_nullable_to_non_nullable
as int,required_: null == required_ ? _self.required_ : required_ // ignore: cast_nullable_to_non_nullable
as bool,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,sdkOperationId: null == sdkOperationId ? _self.sdkOperationId : sdkOperationId // ignore: cast_nullable_to_non_nullable
as UuidValue,targetSdkOperationId: freezed == targetSdkOperationId ? _self.targetSdkOperationId : targetSdkOperationId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

/// Create a copy of SdkOperationDependency
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$SdkOperationCopyWith<$Res>? get targetSdkOperation {
    if (_self.targetSdkOperation == null) {
    return null;
  }

  return $SdkOperationCopyWith<$Res>(_self.targetSdkOperation!, (value) {
    return _then(_self.copyWith(targetSdkOperation: value));
  });
}
}

// dart format on
