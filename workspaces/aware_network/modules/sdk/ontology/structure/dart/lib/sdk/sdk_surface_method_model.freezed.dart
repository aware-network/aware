// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'sdk_surface_method_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$SdkSurfaceMethod {

@UuidValueConverter() UuidValue get id; SdkOperation? get targetSdkOperation; String get name; String get operationRef; String get operationName; String get methodFamily; String get effect; String get mutationScope; String get confirmationPolicy; String get executionMode; String get runtimeBindingKind; String? get description;@UuidValueConverter() UuidValue get sdkSurfaceId;@UuidValueConverter() UuidValue? get targetSdkOperationId;
/// Create a copy of SdkSurfaceMethod
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$SdkSurfaceMethodCopyWith<SdkSurfaceMethod> get copyWith => _$SdkSurfaceMethodCopyWithImpl<SdkSurfaceMethod>(this as SdkSurfaceMethod, _$identity);

  /// Serializes this SdkSurfaceMethod to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is SdkSurfaceMethod&&(identical(other.id, id) || other.id == id)&&(identical(other.targetSdkOperation, targetSdkOperation) || other.targetSdkOperation == targetSdkOperation)&&(identical(other.name, name) || other.name == name)&&(identical(other.operationRef, operationRef) || other.operationRef == operationRef)&&(identical(other.operationName, operationName) || other.operationName == operationName)&&(identical(other.methodFamily, methodFamily) || other.methodFamily == methodFamily)&&(identical(other.effect, effect) || other.effect == effect)&&(identical(other.mutationScope, mutationScope) || other.mutationScope == mutationScope)&&(identical(other.confirmationPolicy, confirmationPolicy) || other.confirmationPolicy == confirmationPolicy)&&(identical(other.executionMode, executionMode) || other.executionMode == executionMode)&&(identical(other.runtimeBindingKind, runtimeBindingKind) || other.runtimeBindingKind == runtimeBindingKind)&&(identical(other.description, description) || other.description == description)&&(identical(other.sdkSurfaceId, sdkSurfaceId) || other.sdkSurfaceId == sdkSurfaceId)&&(identical(other.targetSdkOperationId, targetSdkOperationId) || other.targetSdkOperationId == targetSdkOperationId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,targetSdkOperation,name,operationRef,operationName,methodFamily,effect,mutationScope,confirmationPolicy,executionMode,runtimeBindingKind,description,sdkSurfaceId,targetSdkOperationId);

@override
String toString() {
  return 'SdkSurfaceMethod(id: $id, targetSdkOperation: $targetSdkOperation, name: $name, operationRef: $operationRef, operationName: $operationName, methodFamily: $methodFamily, effect: $effect, mutationScope: $mutationScope, confirmationPolicy: $confirmationPolicy, executionMode: $executionMode, runtimeBindingKind: $runtimeBindingKind, description: $description, sdkSurfaceId: $sdkSurfaceId, targetSdkOperationId: $targetSdkOperationId)';
}


}

/// @nodoc
abstract mixin class $SdkSurfaceMethodCopyWith<$Res>  {
  factory $SdkSurfaceMethodCopyWith(SdkSurfaceMethod value, $Res Function(SdkSurfaceMethod) _then) = _$SdkSurfaceMethodCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue id, SdkOperation? targetSdkOperation, String name, String operationRef, String operationName, String methodFamily, String effect, String mutationScope, String confirmationPolicy, String executionMode, String runtimeBindingKind, String? description,@UuidValueConverter() UuidValue sdkSurfaceId,@UuidValueConverter() UuidValue? targetSdkOperationId
});


$SdkOperationCopyWith<$Res>? get targetSdkOperation;

}
/// @nodoc
class _$SdkSurfaceMethodCopyWithImpl<$Res>
    implements $SdkSurfaceMethodCopyWith<$Res> {
  _$SdkSurfaceMethodCopyWithImpl(this._self, this._then);

  final SdkSurfaceMethod _self;
  final $Res Function(SdkSurfaceMethod) _then;

/// Create a copy of SdkSurfaceMethod
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? id = null,Object? targetSdkOperation = freezed,Object? name = null,Object? operationRef = null,Object? operationName = null,Object? methodFamily = null,Object? effect = null,Object? mutationScope = null,Object? confirmationPolicy = null,Object? executionMode = null,Object? runtimeBindingKind = null,Object? description = freezed,Object? sdkSurfaceId = null,Object? targetSdkOperationId = freezed,}) {
  return _then(_self.copyWith(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,targetSdkOperation: freezed == targetSdkOperation ? _self.targetSdkOperation : targetSdkOperation // ignore: cast_nullable_to_non_nullable
as SdkOperation?,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,operationRef: null == operationRef ? _self.operationRef : operationRef // ignore: cast_nullable_to_non_nullable
as String,operationName: null == operationName ? _self.operationName : operationName // ignore: cast_nullable_to_non_nullable
as String,methodFamily: null == methodFamily ? _self.methodFamily : methodFamily // ignore: cast_nullable_to_non_nullable
as String,effect: null == effect ? _self.effect : effect // ignore: cast_nullable_to_non_nullable
as String,mutationScope: null == mutationScope ? _self.mutationScope : mutationScope // ignore: cast_nullable_to_non_nullable
as String,confirmationPolicy: null == confirmationPolicy ? _self.confirmationPolicy : confirmationPolicy // ignore: cast_nullable_to_non_nullable
as String,executionMode: null == executionMode ? _self.executionMode : executionMode // ignore: cast_nullable_to_non_nullable
as String,runtimeBindingKind: null == runtimeBindingKind ? _self.runtimeBindingKind : runtimeBindingKind // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,sdkSurfaceId: null == sdkSurfaceId ? _self.sdkSurfaceId : sdkSurfaceId // ignore: cast_nullable_to_non_nullable
as UuidValue,targetSdkOperationId: freezed == targetSdkOperationId ? _self.targetSdkOperationId : targetSdkOperationId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}
/// Create a copy of SdkSurfaceMethod
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


/// Adds pattern-matching-related methods to [SdkSurfaceMethod].
extension SdkSurfaceMethodPatterns on SdkSurfaceMethod {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _SdkSurfaceMethod value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _SdkSurfaceMethod() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _SdkSurfaceMethod value)  def,}){
final _that = this;
switch (_that) {
case _SdkSurfaceMethod():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _SdkSurfaceMethod value)?  def,}){
final _that = this;
switch (_that) {
case _SdkSurfaceMethod() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue id,  SdkOperation? targetSdkOperation,  String name,  String operationRef,  String operationName,  String methodFamily,  String effect,  String mutationScope,  String confirmationPolicy,  String executionMode,  String runtimeBindingKind,  String? description, @UuidValueConverter()  UuidValue sdkSurfaceId, @UuidValueConverter()  UuidValue? targetSdkOperationId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _SdkSurfaceMethod() when def != null:
return def(_that.id,_that.targetSdkOperation,_that.name,_that.operationRef,_that.operationName,_that.methodFamily,_that.effect,_that.mutationScope,_that.confirmationPolicy,_that.executionMode,_that.runtimeBindingKind,_that.description,_that.sdkSurfaceId,_that.targetSdkOperationId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue id,  SdkOperation? targetSdkOperation,  String name,  String operationRef,  String operationName,  String methodFamily,  String effect,  String mutationScope,  String confirmationPolicy,  String executionMode,  String runtimeBindingKind,  String? description, @UuidValueConverter()  UuidValue sdkSurfaceId, @UuidValueConverter()  UuidValue? targetSdkOperationId)  def,}) {final _that = this;
switch (_that) {
case _SdkSurfaceMethod():
return def(_that.id,_that.targetSdkOperation,_that.name,_that.operationRef,_that.operationName,_that.methodFamily,_that.effect,_that.mutationScope,_that.confirmationPolicy,_that.executionMode,_that.runtimeBindingKind,_that.description,_that.sdkSurfaceId,_that.targetSdkOperationId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue id,  SdkOperation? targetSdkOperation,  String name,  String operationRef,  String operationName,  String methodFamily,  String effect,  String mutationScope,  String confirmationPolicy,  String executionMode,  String runtimeBindingKind,  String? description, @UuidValueConverter()  UuidValue sdkSurfaceId, @UuidValueConverter()  UuidValue? targetSdkOperationId)?  def,}) {final _that = this;
switch (_that) {
case _SdkSurfaceMethod() when def != null:
return def(_that.id,_that.targetSdkOperation,_that.name,_that.operationRef,_that.operationName,_that.methodFamily,_that.effect,_that.mutationScope,_that.confirmationPolicy,_that.executionMode,_that.runtimeBindingKind,_that.description,_that.sdkSurfaceId,_that.targetSdkOperationId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _SdkSurfaceMethod implements SdkSurfaceMethod {
   _SdkSurfaceMethod({@UuidValueConverter() required this.id, this.targetSdkOperation, required this.name, required this.operationRef, required this.operationName, required this.methodFamily, required this.effect, required this.mutationScope, required this.confirmationPolicy, required this.executionMode, required this.runtimeBindingKind, this.description, @UuidValueConverter() required this.sdkSurfaceId, @UuidValueConverter() this.targetSdkOperationId});
  factory _SdkSurfaceMethod.fromJson(Map<String, dynamic> json) => _$SdkSurfaceMethodFromJson(json);

@override@UuidValueConverter() final  UuidValue id;
@override final  SdkOperation? targetSdkOperation;
@override final  String name;
@override final  String operationRef;
@override final  String operationName;
@override final  String methodFamily;
@override final  String effect;
@override final  String mutationScope;
@override final  String confirmationPolicy;
@override final  String executionMode;
@override final  String runtimeBindingKind;
@override final  String? description;
@override@UuidValueConverter() final  UuidValue sdkSurfaceId;
@override@UuidValueConverter() final  UuidValue? targetSdkOperationId;

/// Create a copy of SdkSurfaceMethod
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$SdkSurfaceMethodCopyWith<_SdkSurfaceMethod> get copyWith => __$SdkSurfaceMethodCopyWithImpl<_SdkSurfaceMethod>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$SdkSurfaceMethodToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _SdkSurfaceMethod&&(identical(other.id, id) || other.id == id)&&(identical(other.targetSdkOperation, targetSdkOperation) || other.targetSdkOperation == targetSdkOperation)&&(identical(other.name, name) || other.name == name)&&(identical(other.operationRef, operationRef) || other.operationRef == operationRef)&&(identical(other.operationName, operationName) || other.operationName == operationName)&&(identical(other.methodFamily, methodFamily) || other.methodFamily == methodFamily)&&(identical(other.effect, effect) || other.effect == effect)&&(identical(other.mutationScope, mutationScope) || other.mutationScope == mutationScope)&&(identical(other.confirmationPolicy, confirmationPolicy) || other.confirmationPolicy == confirmationPolicy)&&(identical(other.executionMode, executionMode) || other.executionMode == executionMode)&&(identical(other.runtimeBindingKind, runtimeBindingKind) || other.runtimeBindingKind == runtimeBindingKind)&&(identical(other.description, description) || other.description == description)&&(identical(other.sdkSurfaceId, sdkSurfaceId) || other.sdkSurfaceId == sdkSurfaceId)&&(identical(other.targetSdkOperationId, targetSdkOperationId) || other.targetSdkOperationId == targetSdkOperationId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,targetSdkOperation,name,operationRef,operationName,methodFamily,effect,mutationScope,confirmationPolicy,executionMode,runtimeBindingKind,description,sdkSurfaceId,targetSdkOperationId);

@override
String toString() {
  return 'SdkSurfaceMethod.def(id: $id, targetSdkOperation: $targetSdkOperation, name: $name, operationRef: $operationRef, operationName: $operationName, methodFamily: $methodFamily, effect: $effect, mutationScope: $mutationScope, confirmationPolicy: $confirmationPolicy, executionMode: $executionMode, runtimeBindingKind: $runtimeBindingKind, description: $description, sdkSurfaceId: $sdkSurfaceId, targetSdkOperationId: $targetSdkOperationId)';
}


}

/// @nodoc
abstract mixin class _$SdkSurfaceMethodCopyWith<$Res> implements $SdkSurfaceMethodCopyWith<$Res> {
  factory _$SdkSurfaceMethodCopyWith(_SdkSurfaceMethod value, $Res Function(_SdkSurfaceMethod) _then) = __$SdkSurfaceMethodCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue id, SdkOperation? targetSdkOperation, String name, String operationRef, String operationName, String methodFamily, String effect, String mutationScope, String confirmationPolicy, String executionMode, String runtimeBindingKind, String? description,@UuidValueConverter() UuidValue sdkSurfaceId,@UuidValueConverter() UuidValue? targetSdkOperationId
});


@override $SdkOperationCopyWith<$Res>? get targetSdkOperation;

}
/// @nodoc
class __$SdkSurfaceMethodCopyWithImpl<$Res>
    implements _$SdkSurfaceMethodCopyWith<$Res> {
  __$SdkSurfaceMethodCopyWithImpl(this._self, this._then);

  final _SdkSurfaceMethod _self;
  final $Res Function(_SdkSurfaceMethod) _then;

/// Create a copy of SdkSurfaceMethod
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? id = null,Object? targetSdkOperation = freezed,Object? name = null,Object? operationRef = null,Object? operationName = null,Object? methodFamily = null,Object? effect = null,Object? mutationScope = null,Object? confirmationPolicy = null,Object? executionMode = null,Object? runtimeBindingKind = null,Object? description = freezed,Object? sdkSurfaceId = null,Object? targetSdkOperationId = freezed,}) {
  return _then(_SdkSurfaceMethod(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,targetSdkOperation: freezed == targetSdkOperation ? _self.targetSdkOperation : targetSdkOperation // ignore: cast_nullable_to_non_nullable
as SdkOperation?,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,operationRef: null == operationRef ? _self.operationRef : operationRef // ignore: cast_nullable_to_non_nullable
as String,operationName: null == operationName ? _self.operationName : operationName // ignore: cast_nullable_to_non_nullable
as String,methodFamily: null == methodFamily ? _self.methodFamily : methodFamily // ignore: cast_nullable_to_non_nullable
as String,effect: null == effect ? _self.effect : effect // ignore: cast_nullable_to_non_nullable
as String,mutationScope: null == mutationScope ? _self.mutationScope : mutationScope // ignore: cast_nullable_to_non_nullable
as String,confirmationPolicy: null == confirmationPolicy ? _self.confirmationPolicy : confirmationPolicy // ignore: cast_nullable_to_non_nullable
as String,executionMode: null == executionMode ? _self.executionMode : executionMode // ignore: cast_nullable_to_non_nullable
as String,runtimeBindingKind: null == runtimeBindingKind ? _self.runtimeBindingKind : runtimeBindingKind // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,sdkSurfaceId: null == sdkSurfaceId ? _self.sdkSurfaceId : sdkSurfaceId // ignore: cast_nullable_to_non_nullable
as UuidValue,targetSdkOperationId: freezed == targetSdkOperationId ? _self.targetSdkOperationId : targetSdkOperationId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

/// Create a copy of SdkSurfaceMethod
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
