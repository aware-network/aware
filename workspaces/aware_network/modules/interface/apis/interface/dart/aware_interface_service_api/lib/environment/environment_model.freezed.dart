// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'environment_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$EnvironmentActorAdmissionRoleEligibility {

@UuidValueConverter() UuidValue get environmentProfileActorConfigId;@UuidValueConverter() UuidValue get actorConfigRoleConfigId;@UuidValueConverter() UuidValue get roleConfigId; String? get roleConfigName;
/// Create a copy of EnvironmentActorAdmissionRoleEligibility
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$EnvironmentActorAdmissionRoleEligibilityCopyWith<EnvironmentActorAdmissionRoleEligibility> get copyWith => _$EnvironmentActorAdmissionRoleEligibilityCopyWithImpl<EnvironmentActorAdmissionRoleEligibility>(this as EnvironmentActorAdmissionRoleEligibility, _$identity);

  /// Serializes this EnvironmentActorAdmissionRoleEligibility to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is EnvironmentActorAdmissionRoleEligibility&&(identical(other.environmentProfileActorConfigId, environmentProfileActorConfigId) || other.environmentProfileActorConfigId == environmentProfileActorConfigId)&&(identical(other.actorConfigRoleConfigId, actorConfigRoleConfigId) || other.actorConfigRoleConfigId == actorConfigRoleConfigId)&&(identical(other.roleConfigId, roleConfigId) || other.roleConfigId == roleConfigId)&&(identical(other.roleConfigName, roleConfigName) || other.roleConfigName == roleConfigName));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,environmentProfileActorConfigId,actorConfigRoleConfigId,roleConfigId,roleConfigName);

@override
String toString() {
  return 'EnvironmentActorAdmissionRoleEligibility(environmentProfileActorConfigId: $environmentProfileActorConfigId, actorConfigRoleConfigId: $actorConfigRoleConfigId, roleConfigId: $roleConfigId, roleConfigName: $roleConfigName)';
}


}

/// @nodoc
abstract mixin class $EnvironmentActorAdmissionRoleEligibilityCopyWith<$Res>  {
  factory $EnvironmentActorAdmissionRoleEligibilityCopyWith(EnvironmentActorAdmissionRoleEligibility value, $Res Function(EnvironmentActorAdmissionRoleEligibility) _then) = _$EnvironmentActorAdmissionRoleEligibilityCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue environmentProfileActorConfigId,@UuidValueConverter() UuidValue actorConfigRoleConfigId,@UuidValueConverter() UuidValue roleConfigId, String? roleConfigName
});




}
/// @nodoc
class _$EnvironmentActorAdmissionRoleEligibilityCopyWithImpl<$Res>
    implements $EnvironmentActorAdmissionRoleEligibilityCopyWith<$Res> {
  _$EnvironmentActorAdmissionRoleEligibilityCopyWithImpl(this._self, this._then);

  final EnvironmentActorAdmissionRoleEligibility _self;
  final $Res Function(EnvironmentActorAdmissionRoleEligibility) _then;

/// Create a copy of EnvironmentActorAdmissionRoleEligibility
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? environmentProfileActorConfigId = null,Object? actorConfigRoleConfigId = null,Object? roleConfigId = null,Object? roleConfigName = freezed,}) {
  return _then(_self.copyWith(
environmentProfileActorConfigId: null == environmentProfileActorConfigId ? _self.environmentProfileActorConfigId : environmentProfileActorConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,actorConfigRoleConfigId: null == actorConfigRoleConfigId ? _self.actorConfigRoleConfigId : actorConfigRoleConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,roleConfigId: null == roleConfigId ? _self.roleConfigId : roleConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,roleConfigName: freezed == roleConfigName ? _self.roleConfigName : roleConfigName // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [EnvironmentActorAdmissionRoleEligibility].
extension EnvironmentActorAdmissionRoleEligibilityPatterns on EnvironmentActorAdmissionRoleEligibility {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _EnvironmentActorAdmissionRoleEligibility value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _EnvironmentActorAdmissionRoleEligibility() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _EnvironmentActorAdmissionRoleEligibility value)  def,}){
final _that = this;
switch (_that) {
case _EnvironmentActorAdmissionRoleEligibility():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _EnvironmentActorAdmissionRoleEligibility value)?  def,}){
final _that = this;
switch (_that) {
case _EnvironmentActorAdmissionRoleEligibility() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue environmentProfileActorConfigId, @UuidValueConverter()  UuidValue actorConfigRoleConfigId, @UuidValueConverter()  UuidValue roleConfigId,  String? roleConfigName)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _EnvironmentActorAdmissionRoleEligibility() when def != null:
return def(_that.environmentProfileActorConfigId,_that.actorConfigRoleConfigId,_that.roleConfigId,_that.roleConfigName);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue environmentProfileActorConfigId, @UuidValueConverter()  UuidValue actorConfigRoleConfigId, @UuidValueConverter()  UuidValue roleConfigId,  String? roleConfigName)  def,}) {final _that = this;
switch (_that) {
case _EnvironmentActorAdmissionRoleEligibility():
return def(_that.environmentProfileActorConfigId,_that.actorConfigRoleConfigId,_that.roleConfigId,_that.roleConfigName);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue environmentProfileActorConfigId, @UuidValueConverter()  UuidValue actorConfigRoleConfigId, @UuidValueConverter()  UuidValue roleConfigId,  String? roleConfigName)?  def,}) {final _that = this;
switch (_that) {
case _EnvironmentActorAdmissionRoleEligibility() when def != null:
return def(_that.environmentProfileActorConfigId,_that.actorConfigRoleConfigId,_that.roleConfigId,_that.roleConfigName);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _EnvironmentActorAdmissionRoleEligibility implements EnvironmentActorAdmissionRoleEligibility {
   _EnvironmentActorAdmissionRoleEligibility({@UuidValueConverter() required this.environmentProfileActorConfigId, @UuidValueConverter() required this.actorConfigRoleConfigId, @UuidValueConverter() required this.roleConfigId, this.roleConfigName});
  factory _EnvironmentActorAdmissionRoleEligibility.fromJson(Map<String, dynamic> json) => _$EnvironmentActorAdmissionRoleEligibilityFromJson(json);

@override@UuidValueConverter() final  UuidValue environmentProfileActorConfigId;
@override@UuidValueConverter() final  UuidValue actorConfigRoleConfigId;
@override@UuidValueConverter() final  UuidValue roleConfigId;
@override final  String? roleConfigName;

/// Create a copy of EnvironmentActorAdmissionRoleEligibility
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$EnvironmentActorAdmissionRoleEligibilityCopyWith<_EnvironmentActorAdmissionRoleEligibility> get copyWith => __$EnvironmentActorAdmissionRoleEligibilityCopyWithImpl<_EnvironmentActorAdmissionRoleEligibility>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$EnvironmentActorAdmissionRoleEligibilityToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _EnvironmentActorAdmissionRoleEligibility&&(identical(other.environmentProfileActorConfigId, environmentProfileActorConfigId) || other.environmentProfileActorConfigId == environmentProfileActorConfigId)&&(identical(other.actorConfigRoleConfigId, actorConfigRoleConfigId) || other.actorConfigRoleConfigId == actorConfigRoleConfigId)&&(identical(other.roleConfigId, roleConfigId) || other.roleConfigId == roleConfigId)&&(identical(other.roleConfigName, roleConfigName) || other.roleConfigName == roleConfigName));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,environmentProfileActorConfigId,actorConfigRoleConfigId,roleConfigId,roleConfigName);

@override
String toString() {
  return 'EnvironmentActorAdmissionRoleEligibility.def(environmentProfileActorConfigId: $environmentProfileActorConfigId, actorConfigRoleConfigId: $actorConfigRoleConfigId, roleConfigId: $roleConfigId, roleConfigName: $roleConfigName)';
}


}

/// @nodoc
abstract mixin class _$EnvironmentActorAdmissionRoleEligibilityCopyWith<$Res> implements $EnvironmentActorAdmissionRoleEligibilityCopyWith<$Res> {
  factory _$EnvironmentActorAdmissionRoleEligibilityCopyWith(_EnvironmentActorAdmissionRoleEligibility value, $Res Function(_EnvironmentActorAdmissionRoleEligibility) _then) = __$EnvironmentActorAdmissionRoleEligibilityCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue environmentProfileActorConfigId,@UuidValueConverter() UuidValue actorConfigRoleConfigId,@UuidValueConverter() UuidValue roleConfigId, String? roleConfigName
});




}
/// @nodoc
class __$EnvironmentActorAdmissionRoleEligibilityCopyWithImpl<$Res>
    implements _$EnvironmentActorAdmissionRoleEligibilityCopyWith<$Res> {
  __$EnvironmentActorAdmissionRoleEligibilityCopyWithImpl(this._self, this._then);

  final _EnvironmentActorAdmissionRoleEligibility _self;
  final $Res Function(_EnvironmentActorAdmissionRoleEligibility) _then;

/// Create a copy of EnvironmentActorAdmissionRoleEligibility
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? environmentProfileActorConfigId = null,Object? actorConfigRoleConfigId = null,Object? roleConfigId = null,Object? roleConfigName = freezed,}) {
  return _then(_EnvironmentActorAdmissionRoleEligibility(
environmentProfileActorConfigId: null == environmentProfileActorConfigId ? _self.environmentProfileActorConfigId : environmentProfileActorConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,actorConfigRoleConfigId: null == actorConfigRoleConfigId ? _self.actorConfigRoleConfigId : actorConfigRoleConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,roleConfigId: null == roleConfigId ? _self.roleConfigId : roleConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,roleConfigName: freezed == roleConfigName ? _self.roleConfigName : roleConfigName // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$EnvironmentActorAdmissionRoleBinding {

@UuidValueConverter() UuidValue get environmentProfileActorConfigId;@UuidValueConverter() UuidValue get actorConfigRoleConfigId;@UuidValueConverter() UuidValue get roleConfigId; String? get roleConfigName;@UuidValueConverter() UuidValue get actorId;@UuidValueConverter() UuidValue get roleId;@UuidValueConverter() UuidValue get actorRoleId;@UuidValueConverter() UuidValue get roleClassInstanceId;@UuidValueConverter() UuidValue get classInstanceIdentityId;@UuidValueConverter() UuidValue get roleConfigClassConfigId;@UuidValueConverter() UuidValue get objectInstanceGraphIdentityId; String get objectInstanceGraphBranchKey;@UuidValueConverter() UuidValue? get objectInstanceGraphBranchId;
/// Create a copy of EnvironmentActorAdmissionRoleBinding
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$EnvironmentActorAdmissionRoleBindingCopyWith<EnvironmentActorAdmissionRoleBinding> get copyWith => _$EnvironmentActorAdmissionRoleBindingCopyWithImpl<EnvironmentActorAdmissionRoleBinding>(this as EnvironmentActorAdmissionRoleBinding, _$identity);

  /// Serializes this EnvironmentActorAdmissionRoleBinding to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is EnvironmentActorAdmissionRoleBinding&&(identical(other.environmentProfileActorConfigId, environmentProfileActorConfigId) || other.environmentProfileActorConfigId == environmentProfileActorConfigId)&&(identical(other.actorConfigRoleConfigId, actorConfigRoleConfigId) || other.actorConfigRoleConfigId == actorConfigRoleConfigId)&&(identical(other.roleConfigId, roleConfigId) || other.roleConfigId == roleConfigId)&&(identical(other.roleConfigName, roleConfigName) || other.roleConfigName == roleConfigName)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.roleId, roleId) || other.roleId == roleId)&&(identical(other.actorRoleId, actorRoleId) || other.actorRoleId == actorRoleId)&&(identical(other.roleClassInstanceId, roleClassInstanceId) || other.roleClassInstanceId == roleClassInstanceId)&&(identical(other.classInstanceIdentityId, classInstanceIdentityId) || other.classInstanceIdentityId == classInstanceIdentityId)&&(identical(other.roleConfigClassConfigId, roleConfigClassConfigId) || other.roleConfigClassConfigId == roleConfigClassConfigId)&&(identical(other.objectInstanceGraphIdentityId, objectInstanceGraphIdentityId) || other.objectInstanceGraphIdentityId == objectInstanceGraphIdentityId)&&(identical(other.objectInstanceGraphBranchKey, objectInstanceGraphBranchKey) || other.objectInstanceGraphBranchKey == objectInstanceGraphBranchKey)&&(identical(other.objectInstanceGraphBranchId, objectInstanceGraphBranchId) || other.objectInstanceGraphBranchId == objectInstanceGraphBranchId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,environmentProfileActorConfigId,actorConfigRoleConfigId,roleConfigId,roleConfigName,actorId,roleId,actorRoleId,roleClassInstanceId,classInstanceIdentityId,roleConfigClassConfigId,objectInstanceGraphIdentityId,objectInstanceGraphBranchKey,objectInstanceGraphBranchId);

@override
String toString() {
  return 'EnvironmentActorAdmissionRoleBinding(environmentProfileActorConfigId: $environmentProfileActorConfigId, actorConfigRoleConfigId: $actorConfigRoleConfigId, roleConfigId: $roleConfigId, roleConfigName: $roleConfigName, actorId: $actorId, roleId: $roleId, actorRoleId: $actorRoleId, roleClassInstanceId: $roleClassInstanceId, classInstanceIdentityId: $classInstanceIdentityId, roleConfigClassConfigId: $roleConfigClassConfigId, objectInstanceGraphIdentityId: $objectInstanceGraphIdentityId, objectInstanceGraphBranchKey: $objectInstanceGraphBranchKey, objectInstanceGraphBranchId: $objectInstanceGraphBranchId)';
}


}

/// @nodoc
abstract mixin class $EnvironmentActorAdmissionRoleBindingCopyWith<$Res>  {
  factory $EnvironmentActorAdmissionRoleBindingCopyWith(EnvironmentActorAdmissionRoleBinding value, $Res Function(EnvironmentActorAdmissionRoleBinding) _then) = _$EnvironmentActorAdmissionRoleBindingCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue environmentProfileActorConfigId,@UuidValueConverter() UuidValue actorConfigRoleConfigId,@UuidValueConverter() UuidValue roleConfigId, String? roleConfigName,@UuidValueConverter() UuidValue actorId,@UuidValueConverter() UuidValue roleId,@UuidValueConverter() UuidValue actorRoleId,@UuidValueConverter() UuidValue roleClassInstanceId,@UuidValueConverter() UuidValue classInstanceIdentityId,@UuidValueConverter() UuidValue roleConfigClassConfigId,@UuidValueConverter() UuidValue objectInstanceGraphIdentityId, String objectInstanceGraphBranchKey,@UuidValueConverter() UuidValue? objectInstanceGraphBranchId
});




}
/// @nodoc
class _$EnvironmentActorAdmissionRoleBindingCopyWithImpl<$Res>
    implements $EnvironmentActorAdmissionRoleBindingCopyWith<$Res> {
  _$EnvironmentActorAdmissionRoleBindingCopyWithImpl(this._self, this._then);

  final EnvironmentActorAdmissionRoleBinding _self;
  final $Res Function(EnvironmentActorAdmissionRoleBinding) _then;

/// Create a copy of EnvironmentActorAdmissionRoleBinding
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? environmentProfileActorConfigId = null,Object? actorConfigRoleConfigId = null,Object? roleConfigId = null,Object? roleConfigName = freezed,Object? actorId = null,Object? roleId = null,Object? actorRoleId = null,Object? roleClassInstanceId = null,Object? classInstanceIdentityId = null,Object? roleConfigClassConfigId = null,Object? objectInstanceGraphIdentityId = null,Object? objectInstanceGraphBranchKey = null,Object? objectInstanceGraphBranchId = freezed,}) {
  return _then(_self.copyWith(
environmentProfileActorConfigId: null == environmentProfileActorConfigId ? _self.environmentProfileActorConfigId : environmentProfileActorConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,actorConfigRoleConfigId: null == actorConfigRoleConfigId ? _self.actorConfigRoleConfigId : actorConfigRoleConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,roleConfigId: null == roleConfigId ? _self.roleConfigId : roleConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,roleConfigName: freezed == roleConfigName ? _self.roleConfigName : roleConfigName // ignore: cast_nullable_to_non_nullable
as String?,actorId: null == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue,roleId: null == roleId ? _self.roleId : roleId // ignore: cast_nullable_to_non_nullable
as UuidValue,actorRoleId: null == actorRoleId ? _self.actorRoleId : actorRoleId // ignore: cast_nullable_to_non_nullable
as UuidValue,roleClassInstanceId: null == roleClassInstanceId ? _self.roleClassInstanceId : roleClassInstanceId // ignore: cast_nullable_to_non_nullable
as UuidValue,classInstanceIdentityId: null == classInstanceIdentityId ? _self.classInstanceIdentityId : classInstanceIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue,roleConfigClassConfigId: null == roleConfigClassConfigId ? _self.roleConfigClassConfigId : roleConfigClassConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,objectInstanceGraphIdentityId: null == objectInstanceGraphIdentityId ? _self.objectInstanceGraphIdentityId : objectInstanceGraphIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue,objectInstanceGraphBranchKey: null == objectInstanceGraphBranchKey ? _self.objectInstanceGraphBranchKey : objectInstanceGraphBranchKey // ignore: cast_nullable_to_non_nullable
as String,objectInstanceGraphBranchId: freezed == objectInstanceGraphBranchId ? _self.objectInstanceGraphBranchId : objectInstanceGraphBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

}


/// Adds pattern-matching-related methods to [EnvironmentActorAdmissionRoleBinding].
extension EnvironmentActorAdmissionRoleBindingPatterns on EnvironmentActorAdmissionRoleBinding {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _EnvironmentActorAdmissionRoleBinding value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _EnvironmentActorAdmissionRoleBinding() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _EnvironmentActorAdmissionRoleBinding value)  def,}){
final _that = this;
switch (_that) {
case _EnvironmentActorAdmissionRoleBinding():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _EnvironmentActorAdmissionRoleBinding value)?  def,}){
final _that = this;
switch (_that) {
case _EnvironmentActorAdmissionRoleBinding() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue environmentProfileActorConfigId, @UuidValueConverter()  UuidValue actorConfigRoleConfigId, @UuidValueConverter()  UuidValue roleConfigId,  String? roleConfigName, @UuidValueConverter()  UuidValue actorId, @UuidValueConverter()  UuidValue roleId, @UuidValueConverter()  UuidValue actorRoleId, @UuidValueConverter()  UuidValue roleClassInstanceId, @UuidValueConverter()  UuidValue classInstanceIdentityId, @UuidValueConverter()  UuidValue roleConfigClassConfigId, @UuidValueConverter()  UuidValue objectInstanceGraphIdentityId,  String objectInstanceGraphBranchKey, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _EnvironmentActorAdmissionRoleBinding() when def != null:
return def(_that.environmentProfileActorConfigId,_that.actorConfigRoleConfigId,_that.roleConfigId,_that.roleConfigName,_that.actorId,_that.roleId,_that.actorRoleId,_that.roleClassInstanceId,_that.classInstanceIdentityId,_that.roleConfigClassConfigId,_that.objectInstanceGraphIdentityId,_that.objectInstanceGraphBranchKey,_that.objectInstanceGraphBranchId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue environmentProfileActorConfigId, @UuidValueConverter()  UuidValue actorConfigRoleConfigId, @UuidValueConverter()  UuidValue roleConfigId,  String? roleConfigName, @UuidValueConverter()  UuidValue actorId, @UuidValueConverter()  UuidValue roleId, @UuidValueConverter()  UuidValue actorRoleId, @UuidValueConverter()  UuidValue roleClassInstanceId, @UuidValueConverter()  UuidValue classInstanceIdentityId, @UuidValueConverter()  UuidValue roleConfigClassConfigId, @UuidValueConverter()  UuidValue objectInstanceGraphIdentityId,  String objectInstanceGraphBranchKey, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId)  def,}) {final _that = this;
switch (_that) {
case _EnvironmentActorAdmissionRoleBinding():
return def(_that.environmentProfileActorConfigId,_that.actorConfigRoleConfigId,_that.roleConfigId,_that.roleConfigName,_that.actorId,_that.roleId,_that.actorRoleId,_that.roleClassInstanceId,_that.classInstanceIdentityId,_that.roleConfigClassConfigId,_that.objectInstanceGraphIdentityId,_that.objectInstanceGraphBranchKey,_that.objectInstanceGraphBranchId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue environmentProfileActorConfigId, @UuidValueConverter()  UuidValue actorConfigRoleConfigId, @UuidValueConverter()  UuidValue roleConfigId,  String? roleConfigName, @UuidValueConverter()  UuidValue actorId, @UuidValueConverter()  UuidValue roleId, @UuidValueConverter()  UuidValue actorRoleId, @UuidValueConverter()  UuidValue roleClassInstanceId, @UuidValueConverter()  UuidValue classInstanceIdentityId, @UuidValueConverter()  UuidValue roleConfigClassConfigId, @UuidValueConverter()  UuidValue objectInstanceGraphIdentityId,  String objectInstanceGraphBranchKey, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId)?  def,}) {final _that = this;
switch (_that) {
case _EnvironmentActorAdmissionRoleBinding() when def != null:
return def(_that.environmentProfileActorConfigId,_that.actorConfigRoleConfigId,_that.roleConfigId,_that.roleConfigName,_that.actorId,_that.roleId,_that.actorRoleId,_that.roleClassInstanceId,_that.classInstanceIdentityId,_that.roleConfigClassConfigId,_that.objectInstanceGraphIdentityId,_that.objectInstanceGraphBranchKey,_that.objectInstanceGraphBranchId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _EnvironmentActorAdmissionRoleBinding implements EnvironmentActorAdmissionRoleBinding {
   _EnvironmentActorAdmissionRoleBinding({@UuidValueConverter() required this.environmentProfileActorConfigId, @UuidValueConverter() required this.actorConfigRoleConfigId, @UuidValueConverter() required this.roleConfigId, this.roleConfigName, @UuidValueConverter() required this.actorId, @UuidValueConverter() required this.roleId, @UuidValueConverter() required this.actorRoleId, @UuidValueConverter() required this.roleClassInstanceId, @UuidValueConverter() required this.classInstanceIdentityId, @UuidValueConverter() required this.roleConfigClassConfigId, @UuidValueConverter() required this.objectInstanceGraphIdentityId, required this.objectInstanceGraphBranchKey, @UuidValueConverter() this.objectInstanceGraphBranchId});
  factory _EnvironmentActorAdmissionRoleBinding.fromJson(Map<String, dynamic> json) => _$EnvironmentActorAdmissionRoleBindingFromJson(json);

@override@UuidValueConverter() final  UuidValue environmentProfileActorConfigId;
@override@UuidValueConverter() final  UuidValue actorConfigRoleConfigId;
@override@UuidValueConverter() final  UuidValue roleConfigId;
@override final  String? roleConfigName;
@override@UuidValueConverter() final  UuidValue actorId;
@override@UuidValueConverter() final  UuidValue roleId;
@override@UuidValueConverter() final  UuidValue actorRoleId;
@override@UuidValueConverter() final  UuidValue roleClassInstanceId;
@override@UuidValueConverter() final  UuidValue classInstanceIdentityId;
@override@UuidValueConverter() final  UuidValue roleConfigClassConfigId;
@override@UuidValueConverter() final  UuidValue objectInstanceGraphIdentityId;
@override final  String objectInstanceGraphBranchKey;
@override@UuidValueConverter() final  UuidValue? objectInstanceGraphBranchId;

/// Create a copy of EnvironmentActorAdmissionRoleBinding
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$EnvironmentActorAdmissionRoleBindingCopyWith<_EnvironmentActorAdmissionRoleBinding> get copyWith => __$EnvironmentActorAdmissionRoleBindingCopyWithImpl<_EnvironmentActorAdmissionRoleBinding>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$EnvironmentActorAdmissionRoleBindingToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _EnvironmentActorAdmissionRoleBinding&&(identical(other.environmentProfileActorConfigId, environmentProfileActorConfigId) || other.environmentProfileActorConfigId == environmentProfileActorConfigId)&&(identical(other.actorConfigRoleConfigId, actorConfigRoleConfigId) || other.actorConfigRoleConfigId == actorConfigRoleConfigId)&&(identical(other.roleConfigId, roleConfigId) || other.roleConfigId == roleConfigId)&&(identical(other.roleConfigName, roleConfigName) || other.roleConfigName == roleConfigName)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.roleId, roleId) || other.roleId == roleId)&&(identical(other.actorRoleId, actorRoleId) || other.actorRoleId == actorRoleId)&&(identical(other.roleClassInstanceId, roleClassInstanceId) || other.roleClassInstanceId == roleClassInstanceId)&&(identical(other.classInstanceIdentityId, classInstanceIdentityId) || other.classInstanceIdentityId == classInstanceIdentityId)&&(identical(other.roleConfigClassConfigId, roleConfigClassConfigId) || other.roleConfigClassConfigId == roleConfigClassConfigId)&&(identical(other.objectInstanceGraphIdentityId, objectInstanceGraphIdentityId) || other.objectInstanceGraphIdentityId == objectInstanceGraphIdentityId)&&(identical(other.objectInstanceGraphBranchKey, objectInstanceGraphBranchKey) || other.objectInstanceGraphBranchKey == objectInstanceGraphBranchKey)&&(identical(other.objectInstanceGraphBranchId, objectInstanceGraphBranchId) || other.objectInstanceGraphBranchId == objectInstanceGraphBranchId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,environmentProfileActorConfigId,actorConfigRoleConfigId,roleConfigId,roleConfigName,actorId,roleId,actorRoleId,roleClassInstanceId,classInstanceIdentityId,roleConfigClassConfigId,objectInstanceGraphIdentityId,objectInstanceGraphBranchKey,objectInstanceGraphBranchId);

@override
String toString() {
  return 'EnvironmentActorAdmissionRoleBinding.def(environmentProfileActorConfigId: $environmentProfileActorConfigId, actorConfigRoleConfigId: $actorConfigRoleConfigId, roleConfigId: $roleConfigId, roleConfigName: $roleConfigName, actorId: $actorId, roleId: $roleId, actorRoleId: $actorRoleId, roleClassInstanceId: $roleClassInstanceId, classInstanceIdentityId: $classInstanceIdentityId, roleConfigClassConfigId: $roleConfigClassConfigId, objectInstanceGraphIdentityId: $objectInstanceGraphIdentityId, objectInstanceGraphBranchKey: $objectInstanceGraphBranchKey, objectInstanceGraphBranchId: $objectInstanceGraphBranchId)';
}


}

/// @nodoc
abstract mixin class _$EnvironmentActorAdmissionRoleBindingCopyWith<$Res> implements $EnvironmentActorAdmissionRoleBindingCopyWith<$Res> {
  factory _$EnvironmentActorAdmissionRoleBindingCopyWith(_EnvironmentActorAdmissionRoleBinding value, $Res Function(_EnvironmentActorAdmissionRoleBinding) _then) = __$EnvironmentActorAdmissionRoleBindingCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue environmentProfileActorConfigId,@UuidValueConverter() UuidValue actorConfigRoleConfigId,@UuidValueConverter() UuidValue roleConfigId, String? roleConfigName,@UuidValueConverter() UuidValue actorId,@UuidValueConverter() UuidValue roleId,@UuidValueConverter() UuidValue actorRoleId,@UuidValueConverter() UuidValue roleClassInstanceId,@UuidValueConverter() UuidValue classInstanceIdentityId,@UuidValueConverter() UuidValue roleConfigClassConfigId,@UuidValueConverter() UuidValue objectInstanceGraphIdentityId, String objectInstanceGraphBranchKey,@UuidValueConverter() UuidValue? objectInstanceGraphBranchId
});




}
/// @nodoc
class __$EnvironmentActorAdmissionRoleBindingCopyWithImpl<$Res>
    implements _$EnvironmentActorAdmissionRoleBindingCopyWith<$Res> {
  __$EnvironmentActorAdmissionRoleBindingCopyWithImpl(this._self, this._then);

  final _EnvironmentActorAdmissionRoleBinding _self;
  final $Res Function(_EnvironmentActorAdmissionRoleBinding) _then;

/// Create a copy of EnvironmentActorAdmissionRoleBinding
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? environmentProfileActorConfigId = null,Object? actorConfigRoleConfigId = null,Object? roleConfigId = null,Object? roleConfigName = freezed,Object? actorId = null,Object? roleId = null,Object? actorRoleId = null,Object? roleClassInstanceId = null,Object? classInstanceIdentityId = null,Object? roleConfigClassConfigId = null,Object? objectInstanceGraphIdentityId = null,Object? objectInstanceGraphBranchKey = null,Object? objectInstanceGraphBranchId = freezed,}) {
  return _then(_EnvironmentActorAdmissionRoleBinding(
environmentProfileActorConfigId: null == environmentProfileActorConfigId ? _self.environmentProfileActorConfigId : environmentProfileActorConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,actorConfigRoleConfigId: null == actorConfigRoleConfigId ? _self.actorConfigRoleConfigId : actorConfigRoleConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,roleConfigId: null == roleConfigId ? _self.roleConfigId : roleConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,roleConfigName: freezed == roleConfigName ? _self.roleConfigName : roleConfigName // ignore: cast_nullable_to_non_nullable
as String?,actorId: null == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue,roleId: null == roleId ? _self.roleId : roleId // ignore: cast_nullable_to_non_nullable
as UuidValue,actorRoleId: null == actorRoleId ? _self.actorRoleId : actorRoleId // ignore: cast_nullable_to_non_nullable
as UuidValue,roleClassInstanceId: null == roleClassInstanceId ? _self.roleClassInstanceId : roleClassInstanceId // ignore: cast_nullable_to_non_nullable
as UuidValue,classInstanceIdentityId: null == classInstanceIdentityId ? _self.classInstanceIdentityId : classInstanceIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue,roleConfigClassConfigId: null == roleConfigClassConfigId ? _self.roleConfigClassConfigId : roleConfigClassConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,objectInstanceGraphIdentityId: null == objectInstanceGraphIdentityId ? _self.objectInstanceGraphIdentityId : objectInstanceGraphIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue,objectInstanceGraphBranchKey: null == objectInstanceGraphBranchKey ? _self.objectInstanceGraphBranchKey : objectInstanceGraphBranchKey // ignore: cast_nullable_to_non_nullable
as String,objectInstanceGraphBranchId: freezed == objectInstanceGraphBranchId ? _self.objectInstanceGraphBranchId : objectInstanceGraphBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}


}


/// @nodoc
mixin _$EnvironmentActorAdmissionReceipt {

 bool get accepted; String get status; String? get error; String? get reason;@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue get environmentId;@UuidValueConverter() UuidValue get environmentProfileId;@UuidValueConverter() UuidValue? get environmentProfileActorConfigId;@UuidValueConverter() UuidValue? get actorConfigId;@UuidValueConverter() UuidValue? get classInstanceIdentityId; String get objectInstanceGraphBranchKey;@UuidValueConverter() UuidValue? get objectInstanceGraphBranchId;@UuidValueListConverter() List<UuidValue> get requestedRoleConfigIds; List<String> get requestedRoleConfigNames; List<EnvironmentActorAdmissionRoleEligibility> get eligibleRoles; List<EnvironmentActorAdmissionRoleBinding> get bindings; List<String> get blockers; Map<String, dynamic> get evidence;
/// Create a copy of EnvironmentActorAdmissionReceipt
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$EnvironmentActorAdmissionReceiptCopyWith<EnvironmentActorAdmissionReceipt> get copyWith => _$EnvironmentActorAdmissionReceiptCopyWithImpl<EnvironmentActorAdmissionReceipt>(this as EnvironmentActorAdmissionReceipt, _$identity);

  /// Serializes this EnvironmentActorAdmissionReceipt to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is EnvironmentActorAdmissionReceipt&&(identical(other.accepted, accepted) || other.accepted == accepted)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.reason, reason) || other.reason == reason)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentProfileId, environmentProfileId) || other.environmentProfileId == environmentProfileId)&&(identical(other.environmentProfileActorConfigId, environmentProfileActorConfigId) || other.environmentProfileActorConfigId == environmentProfileActorConfigId)&&(identical(other.actorConfigId, actorConfigId) || other.actorConfigId == actorConfigId)&&(identical(other.classInstanceIdentityId, classInstanceIdentityId) || other.classInstanceIdentityId == classInstanceIdentityId)&&(identical(other.objectInstanceGraphBranchKey, objectInstanceGraphBranchKey) || other.objectInstanceGraphBranchKey == objectInstanceGraphBranchKey)&&(identical(other.objectInstanceGraphBranchId, objectInstanceGraphBranchId) || other.objectInstanceGraphBranchId == objectInstanceGraphBranchId)&&const DeepCollectionEquality().equals(other.requestedRoleConfigIds, requestedRoleConfigIds)&&const DeepCollectionEquality().equals(other.requestedRoleConfigNames, requestedRoleConfigNames)&&const DeepCollectionEquality().equals(other.eligibleRoles, eligibleRoles)&&const DeepCollectionEquality().equals(other.bindings, bindings)&&const DeepCollectionEquality().equals(other.blockers, blockers)&&const DeepCollectionEquality().equals(other.evidence, evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,accepted,status,error,reason,actorId,environmentId,environmentProfileId,environmentProfileActorConfigId,actorConfigId,classInstanceIdentityId,objectInstanceGraphBranchKey,objectInstanceGraphBranchId,const DeepCollectionEquality().hash(requestedRoleConfigIds),const DeepCollectionEquality().hash(requestedRoleConfigNames),const DeepCollectionEquality().hash(eligibleRoles),const DeepCollectionEquality().hash(bindings),const DeepCollectionEquality().hash(blockers),const DeepCollectionEquality().hash(evidence));

@override
String toString() {
  return 'EnvironmentActorAdmissionReceipt(accepted: $accepted, status: $status, error: $error, reason: $reason, actorId: $actorId, environmentId: $environmentId, environmentProfileId: $environmentProfileId, environmentProfileActorConfigId: $environmentProfileActorConfigId, actorConfigId: $actorConfigId, classInstanceIdentityId: $classInstanceIdentityId, objectInstanceGraphBranchKey: $objectInstanceGraphBranchKey, objectInstanceGraphBranchId: $objectInstanceGraphBranchId, requestedRoleConfigIds: $requestedRoleConfigIds, requestedRoleConfigNames: $requestedRoleConfigNames, eligibleRoles: $eligibleRoles, bindings: $bindings, blockers: $blockers, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class $EnvironmentActorAdmissionReceiptCopyWith<$Res>  {
  factory $EnvironmentActorAdmissionReceiptCopyWith(EnvironmentActorAdmissionReceipt value, $Res Function(EnvironmentActorAdmissionReceipt) _then) = _$EnvironmentActorAdmissionReceiptCopyWithImpl;
@useResult
$Res call({
 bool accepted, String status, String? error, String? reason,@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue environmentId,@UuidValueConverter() UuidValue environmentProfileId,@UuidValueConverter() UuidValue? environmentProfileActorConfigId,@UuidValueConverter() UuidValue? actorConfigId,@UuidValueConverter() UuidValue? classInstanceIdentityId, String objectInstanceGraphBranchKey,@UuidValueConverter() UuidValue? objectInstanceGraphBranchId,@UuidValueListConverter() List<UuidValue> requestedRoleConfigIds, List<String> requestedRoleConfigNames, List<EnvironmentActorAdmissionRoleEligibility> eligibleRoles, List<EnvironmentActorAdmissionRoleBinding> bindings, List<String> blockers, Map<String, dynamic> evidence
});




}
/// @nodoc
class _$EnvironmentActorAdmissionReceiptCopyWithImpl<$Res>
    implements $EnvironmentActorAdmissionReceiptCopyWith<$Res> {
  _$EnvironmentActorAdmissionReceiptCopyWithImpl(this._self, this._then);

  final EnvironmentActorAdmissionReceipt _self;
  final $Res Function(EnvironmentActorAdmissionReceipt) _then;

/// Create a copy of EnvironmentActorAdmissionReceipt
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? accepted = null,Object? status = null,Object? error = freezed,Object? reason = freezed,Object? actorId = freezed,Object? environmentId = null,Object? environmentProfileId = null,Object? environmentProfileActorConfigId = freezed,Object? actorConfigId = freezed,Object? classInstanceIdentityId = freezed,Object? objectInstanceGraphBranchKey = null,Object? objectInstanceGraphBranchId = freezed,Object? requestedRoleConfigIds = null,Object? requestedRoleConfigNames = null,Object? eligibleRoles = null,Object? bindings = null,Object? blockers = null,Object? evidence = null,}) {
  return _then(_self.copyWith(
accepted: null == accepted ? _self.accepted : accepted // ignore: cast_nullable_to_non_nullable
as bool,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,reason: freezed == reason ? _self.reason : reason // ignore: cast_nullable_to_non_nullable
as String?,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentId: null == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentProfileId: null == environmentProfileId ? _self.environmentProfileId : environmentProfileId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentProfileActorConfigId: freezed == environmentProfileActorConfigId ? _self.environmentProfileActorConfigId : environmentProfileActorConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,actorConfigId: freezed == actorConfigId ? _self.actorConfigId : actorConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,classInstanceIdentityId: freezed == classInstanceIdentityId ? _self.classInstanceIdentityId : classInstanceIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphBranchKey: null == objectInstanceGraphBranchKey ? _self.objectInstanceGraphBranchKey : objectInstanceGraphBranchKey // ignore: cast_nullable_to_non_nullable
as String,objectInstanceGraphBranchId: freezed == objectInstanceGraphBranchId ? _self.objectInstanceGraphBranchId : objectInstanceGraphBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestedRoleConfigIds: null == requestedRoleConfigIds ? _self.requestedRoleConfigIds : requestedRoleConfigIds // ignore: cast_nullable_to_non_nullable
as List<UuidValue>,requestedRoleConfigNames: null == requestedRoleConfigNames ? _self.requestedRoleConfigNames : requestedRoleConfigNames // ignore: cast_nullable_to_non_nullable
as List<String>,eligibleRoles: null == eligibleRoles ? _self.eligibleRoles : eligibleRoles // ignore: cast_nullable_to_non_nullable
as List<EnvironmentActorAdmissionRoleEligibility>,bindings: null == bindings ? _self.bindings : bindings // ignore: cast_nullable_to_non_nullable
as List<EnvironmentActorAdmissionRoleBinding>,blockers: null == blockers ? _self.blockers : blockers // ignore: cast_nullable_to_non_nullable
as List<String>,evidence: null == evidence ? _self.evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [EnvironmentActorAdmissionReceipt].
extension EnvironmentActorAdmissionReceiptPatterns on EnvironmentActorAdmissionReceipt {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _EnvironmentActorAdmissionReceipt value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _EnvironmentActorAdmissionReceipt() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _EnvironmentActorAdmissionReceipt value)  def,}){
final _that = this;
switch (_that) {
case _EnvironmentActorAdmissionReceipt():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _EnvironmentActorAdmissionReceipt value)?  def,}){
final _that = this;
switch (_that) {
case _EnvironmentActorAdmissionReceipt() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( bool accepted,  String status,  String? error,  String? reason, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue environmentId, @UuidValueConverter()  UuidValue environmentProfileId, @UuidValueConverter()  UuidValue? environmentProfileActorConfigId, @UuidValueConverter()  UuidValue? actorConfigId, @UuidValueConverter()  UuidValue? classInstanceIdentityId,  String objectInstanceGraphBranchKey, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId, @UuidValueListConverter()  List<UuidValue> requestedRoleConfigIds,  List<String> requestedRoleConfigNames,  List<EnvironmentActorAdmissionRoleEligibility> eligibleRoles,  List<EnvironmentActorAdmissionRoleBinding> bindings,  List<String> blockers,  Map<String, dynamic> evidence)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _EnvironmentActorAdmissionReceipt() when def != null:
return def(_that.accepted,_that.status,_that.error,_that.reason,_that.actorId,_that.environmentId,_that.environmentProfileId,_that.environmentProfileActorConfigId,_that.actorConfigId,_that.classInstanceIdentityId,_that.objectInstanceGraphBranchKey,_that.objectInstanceGraphBranchId,_that.requestedRoleConfigIds,_that.requestedRoleConfigNames,_that.eligibleRoles,_that.bindings,_that.blockers,_that.evidence);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( bool accepted,  String status,  String? error,  String? reason, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue environmentId, @UuidValueConverter()  UuidValue environmentProfileId, @UuidValueConverter()  UuidValue? environmentProfileActorConfigId, @UuidValueConverter()  UuidValue? actorConfigId, @UuidValueConverter()  UuidValue? classInstanceIdentityId,  String objectInstanceGraphBranchKey, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId, @UuidValueListConverter()  List<UuidValue> requestedRoleConfigIds,  List<String> requestedRoleConfigNames,  List<EnvironmentActorAdmissionRoleEligibility> eligibleRoles,  List<EnvironmentActorAdmissionRoleBinding> bindings,  List<String> blockers,  Map<String, dynamic> evidence)  def,}) {final _that = this;
switch (_that) {
case _EnvironmentActorAdmissionReceipt():
return def(_that.accepted,_that.status,_that.error,_that.reason,_that.actorId,_that.environmentId,_that.environmentProfileId,_that.environmentProfileActorConfigId,_that.actorConfigId,_that.classInstanceIdentityId,_that.objectInstanceGraphBranchKey,_that.objectInstanceGraphBranchId,_that.requestedRoleConfigIds,_that.requestedRoleConfigNames,_that.eligibleRoles,_that.bindings,_that.blockers,_that.evidence);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( bool accepted,  String status,  String? error,  String? reason, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue environmentId, @UuidValueConverter()  UuidValue environmentProfileId, @UuidValueConverter()  UuidValue? environmentProfileActorConfigId, @UuidValueConverter()  UuidValue? actorConfigId, @UuidValueConverter()  UuidValue? classInstanceIdentityId,  String objectInstanceGraphBranchKey, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId, @UuidValueListConverter()  List<UuidValue> requestedRoleConfigIds,  List<String> requestedRoleConfigNames,  List<EnvironmentActorAdmissionRoleEligibility> eligibleRoles,  List<EnvironmentActorAdmissionRoleBinding> bindings,  List<String> blockers,  Map<String, dynamic> evidence)?  def,}) {final _that = this;
switch (_that) {
case _EnvironmentActorAdmissionReceipt() when def != null:
return def(_that.accepted,_that.status,_that.error,_that.reason,_that.actorId,_that.environmentId,_that.environmentProfileId,_that.environmentProfileActorConfigId,_that.actorConfigId,_that.classInstanceIdentityId,_that.objectInstanceGraphBranchKey,_that.objectInstanceGraphBranchId,_that.requestedRoleConfigIds,_that.requestedRoleConfigNames,_that.eligibleRoles,_that.bindings,_that.blockers,_that.evidence);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _EnvironmentActorAdmissionReceipt implements EnvironmentActorAdmissionReceipt {
   _EnvironmentActorAdmissionReceipt({required this.accepted, required this.status, this.error, this.reason, @UuidValueConverter() this.actorId, @UuidValueConverter() required this.environmentId, @UuidValueConverter() required this.environmentProfileId, @UuidValueConverter() this.environmentProfileActorConfigId, @UuidValueConverter() this.actorConfigId, @UuidValueConverter() this.classInstanceIdentityId, required this.objectInstanceGraphBranchKey, @UuidValueConverter() this.objectInstanceGraphBranchId, @UuidValueListConverter() final  List<UuidValue> requestedRoleConfigIds = const [], final  List<String> requestedRoleConfigNames = const [], final  List<EnvironmentActorAdmissionRoleEligibility> eligibleRoles = const [], final  List<EnvironmentActorAdmissionRoleBinding> bindings = const [], final  List<String> blockers = const [], required final  Map<String, dynamic> evidence}): _requestedRoleConfigIds = requestedRoleConfigIds,_requestedRoleConfigNames = requestedRoleConfigNames,_eligibleRoles = eligibleRoles,_bindings = bindings,_blockers = blockers,_evidence = evidence;
  factory _EnvironmentActorAdmissionReceipt.fromJson(Map<String, dynamic> json) => _$EnvironmentActorAdmissionReceiptFromJson(json);

@override final  bool accepted;
@override final  String status;
@override final  String? error;
@override final  String? reason;
@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue environmentId;
@override@UuidValueConverter() final  UuidValue environmentProfileId;
@override@UuidValueConverter() final  UuidValue? environmentProfileActorConfigId;
@override@UuidValueConverter() final  UuidValue? actorConfigId;
@override@UuidValueConverter() final  UuidValue? classInstanceIdentityId;
@override final  String objectInstanceGraphBranchKey;
@override@UuidValueConverter() final  UuidValue? objectInstanceGraphBranchId;
 final  List<UuidValue> _requestedRoleConfigIds;
@override@JsonKey()@UuidValueListConverter() List<UuidValue> get requestedRoleConfigIds {
  if (_requestedRoleConfigIds is EqualUnmodifiableListView) return _requestedRoleConfigIds;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_requestedRoleConfigIds);
}

 final  List<String> _requestedRoleConfigNames;
@override@JsonKey() List<String> get requestedRoleConfigNames {
  if (_requestedRoleConfigNames is EqualUnmodifiableListView) return _requestedRoleConfigNames;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_requestedRoleConfigNames);
}

 final  List<EnvironmentActorAdmissionRoleEligibility> _eligibleRoles;
@override@JsonKey() List<EnvironmentActorAdmissionRoleEligibility> get eligibleRoles {
  if (_eligibleRoles is EqualUnmodifiableListView) return _eligibleRoles;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_eligibleRoles);
}

 final  List<EnvironmentActorAdmissionRoleBinding> _bindings;
@override@JsonKey() List<EnvironmentActorAdmissionRoleBinding> get bindings {
  if (_bindings is EqualUnmodifiableListView) return _bindings;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_bindings);
}

 final  List<String> _blockers;
@override@JsonKey() List<String> get blockers {
  if (_blockers is EqualUnmodifiableListView) return _blockers;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_blockers);
}

 final  Map<String, dynamic> _evidence;
@override Map<String, dynamic> get evidence {
  if (_evidence is EqualUnmodifiableMapView) return _evidence;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_evidence);
}


/// Create a copy of EnvironmentActorAdmissionReceipt
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$EnvironmentActorAdmissionReceiptCopyWith<_EnvironmentActorAdmissionReceipt> get copyWith => __$EnvironmentActorAdmissionReceiptCopyWithImpl<_EnvironmentActorAdmissionReceipt>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$EnvironmentActorAdmissionReceiptToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _EnvironmentActorAdmissionReceipt&&(identical(other.accepted, accepted) || other.accepted == accepted)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.reason, reason) || other.reason == reason)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentProfileId, environmentProfileId) || other.environmentProfileId == environmentProfileId)&&(identical(other.environmentProfileActorConfigId, environmentProfileActorConfigId) || other.environmentProfileActorConfigId == environmentProfileActorConfigId)&&(identical(other.actorConfigId, actorConfigId) || other.actorConfigId == actorConfigId)&&(identical(other.classInstanceIdentityId, classInstanceIdentityId) || other.classInstanceIdentityId == classInstanceIdentityId)&&(identical(other.objectInstanceGraphBranchKey, objectInstanceGraphBranchKey) || other.objectInstanceGraphBranchKey == objectInstanceGraphBranchKey)&&(identical(other.objectInstanceGraphBranchId, objectInstanceGraphBranchId) || other.objectInstanceGraphBranchId == objectInstanceGraphBranchId)&&const DeepCollectionEquality().equals(other._requestedRoleConfigIds, _requestedRoleConfigIds)&&const DeepCollectionEquality().equals(other._requestedRoleConfigNames, _requestedRoleConfigNames)&&const DeepCollectionEquality().equals(other._eligibleRoles, _eligibleRoles)&&const DeepCollectionEquality().equals(other._bindings, _bindings)&&const DeepCollectionEquality().equals(other._blockers, _blockers)&&const DeepCollectionEquality().equals(other._evidence, _evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,accepted,status,error,reason,actorId,environmentId,environmentProfileId,environmentProfileActorConfigId,actorConfigId,classInstanceIdentityId,objectInstanceGraphBranchKey,objectInstanceGraphBranchId,const DeepCollectionEquality().hash(_requestedRoleConfigIds),const DeepCollectionEquality().hash(_requestedRoleConfigNames),const DeepCollectionEquality().hash(_eligibleRoles),const DeepCollectionEquality().hash(_bindings),const DeepCollectionEquality().hash(_blockers),const DeepCollectionEquality().hash(_evidence));

@override
String toString() {
  return 'EnvironmentActorAdmissionReceipt.def(accepted: $accepted, status: $status, error: $error, reason: $reason, actorId: $actorId, environmentId: $environmentId, environmentProfileId: $environmentProfileId, environmentProfileActorConfigId: $environmentProfileActorConfigId, actorConfigId: $actorConfigId, classInstanceIdentityId: $classInstanceIdentityId, objectInstanceGraphBranchKey: $objectInstanceGraphBranchKey, objectInstanceGraphBranchId: $objectInstanceGraphBranchId, requestedRoleConfigIds: $requestedRoleConfigIds, requestedRoleConfigNames: $requestedRoleConfigNames, eligibleRoles: $eligibleRoles, bindings: $bindings, blockers: $blockers, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class _$EnvironmentActorAdmissionReceiptCopyWith<$Res> implements $EnvironmentActorAdmissionReceiptCopyWith<$Res> {
  factory _$EnvironmentActorAdmissionReceiptCopyWith(_EnvironmentActorAdmissionReceipt value, $Res Function(_EnvironmentActorAdmissionReceipt) _then) = __$EnvironmentActorAdmissionReceiptCopyWithImpl;
@override @useResult
$Res call({
 bool accepted, String status, String? error, String? reason,@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue environmentId,@UuidValueConverter() UuidValue environmentProfileId,@UuidValueConverter() UuidValue? environmentProfileActorConfigId,@UuidValueConverter() UuidValue? actorConfigId,@UuidValueConverter() UuidValue? classInstanceIdentityId, String objectInstanceGraphBranchKey,@UuidValueConverter() UuidValue? objectInstanceGraphBranchId,@UuidValueListConverter() List<UuidValue> requestedRoleConfigIds, List<String> requestedRoleConfigNames, List<EnvironmentActorAdmissionRoleEligibility> eligibleRoles, List<EnvironmentActorAdmissionRoleBinding> bindings, List<String> blockers, Map<String, dynamic> evidence
});




}
/// @nodoc
class __$EnvironmentActorAdmissionReceiptCopyWithImpl<$Res>
    implements _$EnvironmentActorAdmissionReceiptCopyWith<$Res> {
  __$EnvironmentActorAdmissionReceiptCopyWithImpl(this._self, this._then);

  final _EnvironmentActorAdmissionReceipt _self;
  final $Res Function(_EnvironmentActorAdmissionReceipt) _then;

/// Create a copy of EnvironmentActorAdmissionReceipt
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? accepted = null,Object? status = null,Object? error = freezed,Object? reason = freezed,Object? actorId = freezed,Object? environmentId = null,Object? environmentProfileId = null,Object? environmentProfileActorConfigId = freezed,Object? actorConfigId = freezed,Object? classInstanceIdentityId = freezed,Object? objectInstanceGraphBranchKey = null,Object? objectInstanceGraphBranchId = freezed,Object? requestedRoleConfigIds = null,Object? requestedRoleConfigNames = null,Object? eligibleRoles = null,Object? bindings = null,Object? blockers = null,Object? evidence = null,}) {
  return _then(_EnvironmentActorAdmissionReceipt(
accepted: null == accepted ? _self.accepted : accepted // ignore: cast_nullable_to_non_nullable
as bool,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,reason: freezed == reason ? _self.reason : reason // ignore: cast_nullable_to_non_nullable
as String?,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentId: null == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentProfileId: null == environmentProfileId ? _self.environmentProfileId : environmentProfileId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentProfileActorConfigId: freezed == environmentProfileActorConfigId ? _self.environmentProfileActorConfigId : environmentProfileActorConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,actorConfigId: freezed == actorConfigId ? _self.actorConfigId : actorConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,classInstanceIdentityId: freezed == classInstanceIdentityId ? _self.classInstanceIdentityId : classInstanceIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphBranchKey: null == objectInstanceGraphBranchKey ? _self.objectInstanceGraphBranchKey : objectInstanceGraphBranchKey // ignore: cast_nullable_to_non_nullable
as String,objectInstanceGraphBranchId: freezed == objectInstanceGraphBranchId ? _self.objectInstanceGraphBranchId : objectInstanceGraphBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestedRoleConfigIds: null == requestedRoleConfigIds ? _self._requestedRoleConfigIds : requestedRoleConfigIds // ignore: cast_nullable_to_non_nullable
as List<UuidValue>,requestedRoleConfigNames: null == requestedRoleConfigNames ? _self._requestedRoleConfigNames : requestedRoleConfigNames // ignore: cast_nullable_to_non_nullable
as List<String>,eligibleRoles: null == eligibleRoles ? _self._eligibleRoles : eligibleRoles // ignore: cast_nullable_to_non_nullable
as List<EnvironmentActorAdmissionRoleEligibility>,bindings: null == bindings ? _self._bindings : bindings // ignore: cast_nullable_to_non_nullable
as List<EnvironmentActorAdmissionRoleBinding>,blockers: null == blockers ? _self._blockers : blockers // ignore: cast_nullable_to_non_nullable
as List<String>,evidence: null == evidence ? _self._evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$EnvironmentSessionIdentityEvidence {

 SessionSummary? get identitySession; SessionMemberSummary? get identityMember; List<SessionMemberActorRoleSummary> get identityActorRoles; Map<String, dynamic> get evidence;
/// Create a copy of EnvironmentSessionIdentityEvidence
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$EnvironmentSessionIdentityEvidenceCopyWith<EnvironmentSessionIdentityEvidence> get copyWith => _$EnvironmentSessionIdentityEvidenceCopyWithImpl<EnvironmentSessionIdentityEvidence>(this as EnvironmentSessionIdentityEvidence, _$identity);

  /// Serializes this EnvironmentSessionIdentityEvidence to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is EnvironmentSessionIdentityEvidence&&(identical(other.identitySession, identitySession) || other.identitySession == identitySession)&&(identical(other.identityMember, identityMember) || other.identityMember == identityMember)&&const DeepCollectionEquality().equals(other.identityActorRoles, identityActorRoles)&&const DeepCollectionEquality().equals(other.evidence, evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,identitySession,identityMember,const DeepCollectionEquality().hash(identityActorRoles),const DeepCollectionEquality().hash(evidence));

@override
String toString() {
  return 'EnvironmentSessionIdentityEvidence(identitySession: $identitySession, identityMember: $identityMember, identityActorRoles: $identityActorRoles, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class $EnvironmentSessionIdentityEvidenceCopyWith<$Res>  {
  factory $EnvironmentSessionIdentityEvidenceCopyWith(EnvironmentSessionIdentityEvidence value, $Res Function(EnvironmentSessionIdentityEvidence) _then) = _$EnvironmentSessionIdentityEvidenceCopyWithImpl;
@useResult
$Res call({
 SessionSummary? identitySession, SessionMemberSummary? identityMember, List<SessionMemberActorRoleSummary> identityActorRoles, Map<String, dynamic> evidence
});


$SessionSummaryCopyWith<$Res>? get identitySession;$SessionMemberSummaryCopyWith<$Res>? get identityMember;

}
/// @nodoc
class _$EnvironmentSessionIdentityEvidenceCopyWithImpl<$Res>
    implements $EnvironmentSessionIdentityEvidenceCopyWith<$Res> {
  _$EnvironmentSessionIdentityEvidenceCopyWithImpl(this._self, this._then);

  final EnvironmentSessionIdentityEvidence _self;
  final $Res Function(EnvironmentSessionIdentityEvidence) _then;

/// Create a copy of EnvironmentSessionIdentityEvidence
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? identitySession = freezed,Object? identityMember = freezed,Object? identityActorRoles = null,Object? evidence = null,}) {
  return _then(_self.copyWith(
identitySession: freezed == identitySession ? _self.identitySession : identitySession // ignore: cast_nullable_to_non_nullable
as SessionSummary?,identityMember: freezed == identityMember ? _self.identityMember : identityMember // ignore: cast_nullable_to_non_nullable
as SessionMemberSummary?,identityActorRoles: null == identityActorRoles ? _self.identityActorRoles : identityActorRoles // ignore: cast_nullable_to_non_nullable
as List<SessionMemberActorRoleSummary>,evidence: null == evidence ? _self.evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}
/// Create a copy of EnvironmentSessionIdentityEvidence
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$SessionSummaryCopyWith<$Res>? get identitySession {
    if (_self.identitySession == null) {
    return null;
  }

  return $SessionSummaryCopyWith<$Res>(_self.identitySession!, (value) {
    return _then(_self.copyWith(identitySession: value));
  });
}/// Create a copy of EnvironmentSessionIdentityEvidence
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$SessionMemberSummaryCopyWith<$Res>? get identityMember {
    if (_self.identityMember == null) {
    return null;
  }

  return $SessionMemberSummaryCopyWith<$Res>(_self.identityMember!, (value) {
    return _then(_self.copyWith(identityMember: value));
  });
}
}


/// Adds pattern-matching-related methods to [EnvironmentSessionIdentityEvidence].
extension EnvironmentSessionIdentityEvidencePatterns on EnvironmentSessionIdentityEvidence {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _EnvironmentSessionIdentityEvidence value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _EnvironmentSessionIdentityEvidence() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _EnvironmentSessionIdentityEvidence value)  def,}){
final _that = this;
switch (_that) {
case _EnvironmentSessionIdentityEvidence():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _EnvironmentSessionIdentityEvidence value)?  def,}){
final _that = this;
switch (_that) {
case _EnvironmentSessionIdentityEvidence() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( SessionSummary? identitySession,  SessionMemberSummary? identityMember,  List<SessionMemberActorRoleSummary> identityActorRoles,  Map<String, dynamic> evidence)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _EnvironmentSessionIdentityEvidence() when def != null:
return def(_that.identitySession,_that.identityMember,_that.identityActorRoles,_that.evidence);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( SessionSummary? identitySession,  SessionMemberSummary? identityMember,  List<SessionMemberActorRoleSummary> identityActorRoles,  Map<String, dynamic> evidence)  def,}) {final _that = this;
switch (_that) {
case _EnvironmentSessionIdentityEvidence():
return def(_that.identitySession,_that.identityMember,_that.identityActorRoles,_that.evidence);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( SessionSummary? identitySession,  SessionMemberSummary? identityMember,  List<SessionMemberActorRoleSummary> identityActorRoles,  Map<String, dynamic> evidence)?  def,}) {final _that = this;
switch (_that) {
case _EnvironmentSessionIdentityEvidence() when def != null:
return def(_that.identitySession,_that.identityMember,_that.identityActorRoles,_that.evidence);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _EnvironmentSessionIdentityEvidence implements EnvironmentSessionIdentityEvidence {
   _EnvironmentSessionIdentityEvidence({this.identitySession, this.identityMember, final  List<SessionMemberActorRoleSummary> identityActorRoles = const [], required final  Map<String, dynamic> evidence}): _identityActorRoles = identityActorRoles,_evidence = evidence;
  factory _EnvironmentSessionIdentityEvidence.fromJson(Map<String, dynamic> json) => _$EnvironmentSessionIdentityEvidenceFromJson(json);

@override final  SessionSummary? identitySession;
@override final  SessionMemberSummary? identityMember;
 final  List<SessionMemberActorRoleSummary> _identityActorRoles;
@override@JsonKey() List<SessionMemberActorRoleSummary> get identityActorRoles {
  if (_identityActorRoles is EqualUnmodifiableListView) return _identityActorRoles;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_identityActorRoles);
}

 final  Map<String, dynamic> _evidence;
@override Map<String, dynamic> get evidence {
  if (_evidence is EqualUnmodifiableMapView) return _evidence;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_evidence);
}


/// Create a copy of EnvironmentSessionIdentityEvidence
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$EnvironmentSessionIdentityEvidenceCopyWith<_EnvironmentSessionIdentityEvidence> get copyWith => __$EnvironmentSessionIdentityEvidenceCopyWithImpl<_EnvironmentSessionIdentityEvidence>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$EnvironmentSessionIdentityEvidenceToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _EnvironmentSessionIdentityEvidence&&(identical(other.identitySession, identitySession) || other.identitySession == identitySession)&&(identical(other.identityMember, identityMember) || other.identityMember == identityMember)&&const DeepCollectionEquality().equals(other._identityActorRoles, _identityActorRoles)&&const DeepCollectionEquality().equals(other._evidence, _evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,identitySession,identityMember,const DeepCollectionEquality().hash(_identityActorRoles),const DeepCollectionEquality().hash(_evidence));

@override
String toString() {
  return 'EnvironmentSessionIdentityEvidence.def(identitySession: $identitySession, identityMember: $identityMember, identityActorRoles: $identityActorRoles, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class _$EnvironmentSessionIdentityEvidenceCopyWith<$Res> implements $EnvironmentSessionIdentityEvidenceCopyWith<$Res> {
  factory _$EnvironmentSessionIdentityEvidenceCopyWith(_EnvironmentSessionIdentityEvidence value, $Res Function(_EnvironmentSessionIdentityEvidence) _then) = __$EnvironmentSessionIdentityEvidenceCopyWithImpl;
@override @useResult
$Res call({
 SessionSummary? identitySession, SessionMemberSummary? identityMember, List<SessionMemberActorRoleSummary> identityActorRoles, Map<String, dynamic> evidence
});


@override $SessionSummaryCopyWith<$Res>? get identitySession;@override $SessionMemberSummaryCopyWith<$Res>? get identityMember;

}
/// @nodoc
class __$EnvironmentSessionIdentityEvidenceCopyWithImpl<$Res>
    implements _$EnvironmentSessionIdentityEvidenceCopyWith<$Res> {
  __$EnvironmentSessionIdentityEvidenceCopyWithImpl(this._self, this._then);

  final _EnvironmentSessionIdentityEvidence _self;
  final $Res Function(_EnvironmentSessionIdentityEvidence) _then;

/// Create a copy of EnvironmentSessionIdentityEvidence
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? identitySession = freezed,Object? identityMember = freezed,Object? identityActorRoles = null,Object? evidence = null,}) {
  return _then(_EnvironmentSessionIdentityEvidence(
identitySession: freezed == identitySession ? _self.identitySession : identitySession // ignore: cast_nullable_to_non_nullable
as SessionSummary?,identityMember: freezed == identityMember ? _self.identityMember : identityMember // ignore: cast_nullable_to_non_nullable
as SessionMemberSummary?,identityActorRoles: null == identityActorRoles ? _self._identityActorRoles : identityActorRoles // ignore: cast_nullable_to_non_nullable
as List<SessionMemberActorRoleSummary>,evidence: null == evidence ? _self._evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

/// Create a copy of EnvironmentSessionIdentityEvidence
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$SessionSummaryCopyWith<$Res>? get identitySession {
    if (_self.identitySession == null) {
    return null;
  }

  return $SessionSummaryCopyWith<$Res>(_self.identitySession!, (value) {
    return _then(_self.copyWith(identitySession: value));
  });
}/// Create a copy of EnvironmentSessionIdentityEvidence
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$SessionMemberSummaryCopyWith<$Res>? get identityMember {
    if (_self.identityMember == null) {
    return null;
  }

  return $SessionMemberSummaryCopyWith<$Res>(_self.identityMember!, (value) {
    return _then(_self.copyWith(identityMember: value));
  });
}
}


/// @nodoc
mixin _$EnvironmentSessionView {

@UuidValueConverter() UuidValue get environmentSessionId;@UuidValueConverter() UuidValue? get environmentSessionConfigId;@UuidValueConverter() UuidValue? get identitySessionId; SessionSummary? get identitySession;@UuidValueConverter() UuidValue get environmentId;@UuidValueConverter() UuidValue get environmentProfileId; String get sessionKey; String? get title; String? get description; String? get purpose; String get status;@UuidValueConverter() UuidValue? get createdByActorId; String? get sourceKind; String? get sourceRef; Map<String, dynamic> get evidence;
/// Create a copy of EnvironmentSessionView
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$EnvironmentSessionViewCopyWith<EnvironmentSessionView> get copyWith => _$EnvironmentSessionViewCopyWithImpl<EnvironmentSessionView>(this as EnvironmentSessionView, _$identity);

  /// Serializes this EnvironmentSessionView to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is EnvironmentSessionView&&(identical(other.environmentSessionId, environmentSessionId) || other.environmentSessionId == environmentSessionId)&&(identical(other.environmentSessionConfigId, environmentSessionConfigId) || other.environmentSessionConfigId == environmentSessionConfigId)&&(identical(other.identitySessionId, identitySessionId) || other.identitySessionId == identitySessionId)&&(identical(other.identitySession, identitySession) || other.identitySession == identitySession)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentProfileId, environmentProfileId) || other.environmentProfileId == environmentProfileId)&&(identical(other.sessionKey, sessionKey) || other.sessionKey == sessionKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.purpose, purpose) || other.purpose == purpose)&&(identical(other.status, status) || other.status == status)&&(identical(other.createdByActorId, createdByActorId) || other.createdByActorId == createdByActorId)&&(identical(other.sourceKind, sourceKind) || other.sourceKind == sourceKind)&&(identical(other.sourceRef, sourceRef) || other.sourceRef == sourceRef)&&const DeepCollectionEquality().equals(other.evidence, evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,environmentSessionId,environmentSessionConfigId,identitySessionId,identitySession,environmentId,environmentProfileId,sessionKey,title,description,purpose,status,createdByActorId,sourceKind,sourceRef,const DeepCollectionEquality().hash(evidence));

@override
String toString() {
  return 'EnvironmentSessionView(environmentSessionId: $environmentSessionId, environmentSessionConfigId: $environmentSessionConfigId, identitySessionId: $identitySessionId, identitySession: $identitySession, environmentId: $environmentId, environmentProfileId: $environmentProfileId, sessionKey: $sessionKey, title: $title, description: $description, purpose: $purpose, status: $status, createdByActorId: $createdByActorId, sourceKind: $sourceKind, sourceRef: $sourceRef, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class $EnvironmentSessionViewCopyWith<$Res>  {
  factory $EnvironmentSessionViewCopyWith(EnvironmentSessionView value, $Res Function(EnvironmentSessionView) _then) = _$EnvironmentSessionViewCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue environmentSessionId,@UuidValueConverter() UuidValue? environmentSessionConfigId,@UuidValueConverter() UuidValue? identitySessionId, SessionSummary? identitySession,@UuidValueConverter() UuidValue environmentId,@UuidValueConverter() UuidValue environmentProfileId, String sessionKey, String? title, String? description, String? purpose, String status,@UuidValueConverter() UuidValue? createdByActorId, String? sourceKind, String? sourceRef, Map<String, dynamic> evidence
});


$SessionSummaryCopyWith<$Res>? get identitySession;

}
/// @nodoc
class _$EnvironmentSessionViewCopyWithImpl<$Res>
    implements $EnvironmentSessionViewCopyWith<$Res> {
  _$EnvironmentSessionViewCopyWithImpl(this._self, this._then);

  final EnvironmentSessionView _self;
  final $Res Function(EnvironmentSessionView) _then;

/// Create a copy of EnvironmentSessionView
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? environmentSessionId = null,Object? environmentSessionConfigId = freezed,Object? identitySessionId = freezed,Object? identitySession = freezed,Object? environmentId = null,Object? environmentProfileId = null,Object? sessionKey = null,Object? title = freezed,Object? description = freezed,Object? purpose = freezed,Object? status = null,Object? createdByActorId = freezed,Object? sourceKind = freezed,Object? sourceRef = freezed,Object? evidence = null,}) {
  return _then(_self.copyWith(
environmentSessionId: null == environmentSessionId ? _self.environmentSessionId : environmentSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentSessionConfigId: freezed == environmentSessionConfigId ? _self.environmentSessionConfigId : environmentSessionConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,identitySessionId: freezed == identitySessionId ? _self.identitySessionId : identitySessionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,identitySession: freezed == identitySession ? _self.identitySession : identitySession // ignore: cast_nullable_to_non_nullable
as SessionSummary?,environmentId: null == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentProfileId: null == environmentProfileId ? _self.environmentProfileId : environmentProfileId // ignore: cast_nullable_to_non_nullable
as UuidValue,sessionKey: null == sessionKey ? _self.sessionKey : sessionKey // ignore: cast_nullable_to_non_nullable
as String,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,purpose: freezed == purpose ? _self.purpose : purpose // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,createdByActorId: freezed == createdByActorId ? _self.createdByActorId : createdByActorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sourceKind: freezed == sourceKind ? _self.sourceKind : sourceKind // ignore: cast_nullable_to_non_nullable
as String?,sourceRef: freezed == sourceRef ? _self.sourceRef : sourceRef // ignore: cast_nullable_to_non_nullable
as String?,evidence: null == evidence ? _self.evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}
/// Create a copy of EnvironmentSessionView
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$SessionSummaryCopyWith<$Res>? get identitySession {
    if (_self.identitySession == null) {
    return null;
  }

  return $SessionSummaryCopyWith<$Res>(_self.identitySession!, (value) {
    return _then(_self.copyWith(identitySession: value));
  });
}
}


/// Adds pattern-matching-related methods to [EnvironmentSessionView].
extension EnvironmentSessionViewPatterns on EnvironmentSessionView {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _EnvironmentSessionView value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _EnvironmentSessionView() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _EnvironmentSessionView value)  def,}){
final _that = this;
switch (_that) {
case _EnvironmentSessionView():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _EnvironmentSessionView value)?  def,}){
final _that = this;
switch (_that) {
case _EnvironmentSessionView() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue environmentSessionId, @UuidValueConverter()  UuidValue? environmentSessionConfigId, @UuidValueConverter()  UuidValue? identitySessionId,  SessionSummary? identitySession, @UuidValueConverter()  UuidValue environmentId, @UuidValueConverter()  UuidValue environmentProfileId,  String sessionKey,  String? title,  String? description,  String? purpose,  String status, @UuidValueConverter()  UuidValue? createdByActorId,  String? sourceKind,  String? sourceRef,  Map<String, dynamic> evidence)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _EnvironmentSessionView() when def != null:
return def(_that.environmentSessionId,_that.environmentSessionConfigId,_that.identitySessionId,_that.identitySession,_that.environmentId,_that.environmentProfileId,_that.sessionKey,_that.title,_that.description,_that.purpose,_that.status,_that.createdByActorId,_that.sourceKind,_that.sourceRef,_that.evidence);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue environmentSessionId, @UuidValueConverter()  UuidValue? environmentSessionConfigId, @UuidValueConverter()  UuidValue? identitySessionId,  SessionSummary? identitySession, @UuidValueConverter()  UuidValue environmentId, @UuidValueConverter()  UuidValue environmentProfileId,  String sessionKey,  String? title,  String? description,  String? purpose,  String status, @UuidValueConverter()  UuidValue? createdByActorId,  String? sourceKind,  String? sourceRef,  Map<String, dynamic> evidence)  def,}) {final _that = this;
switch (_that) {
case _EnvironmentSessionView():
return def(_that.environmentSessionId,_that.environmentSessionConfigId,_that.identitySessionId,_that.identitySession,_that.environmentId,_that.environmentProfileId,_that.sessionKey,_that.title,_that.description,_that.purpose,_that.status,_that.createdByActorId,_that.sourceKind,_that.sourceRef,_that.evidence);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue environmentSessionId, @UuidValueConverter()  UuidValue? environmentSessionConfigId, @UuidValueConverter()  UuidValue? identitySessionId,  SessionSummary? identitySession, @UuidValueConverter()  UuidValue environmentId, @UuidValueConverter()  UuidValue environmentProfileId,  String sessionKey,  String? title,  String? description,  String? purpose,  String status, @UuidValueConverter()  UuidValue? createdByActorId,  String? sourceKind,  String? sourceRef,  Map<String, dynamic> evidence)?  def,}) {final _that = this;
switch (_that) {
case _EnvironmentSessionView() when def != null:
return def(_that.environmentSessionId,_that.environmentSessionConfigId,_that.identitySessionId,_that.identitySession,_that.environmentId,_that.environmentProfileId,_that.sessionKey,_that.title,_that.description,_that.purpose,_that.status,_that.createdByActorId,_that.sourceKind,_that.sourceRef,_that.evidence);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _EnvironmentSessionView implements EnvironmentSessionView {
   _EnvironmentSessionView({@UuidValueConverter() required this.environmentSessionId, @UuidValueConverter() this.environmentSessionConfigId, @UuidValueConverter() this.identitySessionId, this.identitySession, @UuidValueConverter() required this.environmentId, @UuidValueConverter() required this.environmentProfileId, required this.sessionKey, this.title, this.description, this.purpose, required this.status, @UuidValueConverter() this.createdByActorId, this.sourceKind, this.sourceRef, required final  Map<String, dynamic> evidence}): _evidence = evidence;
  factory _EnvironmentSessionView.fromJson(Map<String, dynamic> json) => _$EnvironmentSessionViewFromJson(json);

@override@UuidValueConverter() final  UuidValue environmentSessionId;
@override@UuidValueConverter() final  UuidValue? environmentSessionConfigId;
@override@UuidValueConverter() final  UuidValue? identitySessionId;
@override final  SessionSummary? identitySession;
@override@UuidValueConverter() final  UuidValue environmentId;
@override@UuidValueConverter() final  UuidValue environmentProfileId;
@override final  String sessionKey;
@override final  String? title;
@override final  String? description;
@override final  String? purpose;
@override final  String status;
@override@UuidValueConverter() final  UuidValue? createdByActorId;
@override final  String? sourceKind;
@override final  String? sourceRef;
 final  Map<String, dynamic> _evidence;
@override Map<String, dynamic> get evidence {
  if (_evidence is EqualUnmodifiableMapView) return _evidence;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_evidence);
}


/// Create a copy of EnvironmentSessionView
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$EnvironmentSessionViewCopyWith<_EnvironmentSessionView> get copyWith => __$EnvironmentSessionViewCopyWithImpl<_EnvironmentSessionView>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$EnvironmentSessionViewToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _EnvironmentSessionView&&(identical(other.environmentSessionId, environmentSessionId) || other.environmentSessionId == environmentSessionId)&&(identical(other.environmentSessionConfigId, environmentSessionConfigId) || other.environmentSessionConfigId == environmentSessionConfigId)&&(identical(other.identitySessionId, identitySessionId) || other.identitySessionId == identitySessionId)&&(identical(other.identitySession, identitySession) || other.identitySession == identitySession)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentProfileId, environmentProfileId) || other.environmentProfileId == environmentProfileId)&&(identical(other.sessionKey, sessionKey) || other.sessionKey == sessionKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.purpose, purpose) || other.purpose == purpose)&&(identical(other.status, status) || other.status == status)&&(identical(other.createdByActorId, createdByActorId) || other.createdByActorId == createdByActorId)&&(identical(other.sourceKind, sourceKind) || other.sourceKind == sourceKind)&&(identical(other.sourceRef, sourceRef) || other.sourceRef == sourceRef)&&const DeepCollectionEquality().equals(other._evidence, _evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,environmentSessionId,environmentSessionConfigId,identitySessionId,identitySession,environmentId,environmentProfileId,sessionKey,title,description,purpose,status,createdByActorId,sourceKind,sourceRef,const DeepCollectionEquality().hash(_evidence));

@override
String toString() {
  return 'EnvironmentSessionView.def(environmentSessionId: $environmentSessionId, environmentSessionConfigId: $environmentSessionConfigId, identitySessionId: $identitySessionId, identitySession: $identitySession, environmentId: $environmentId, environmentProfileId: $environmentProfileId, sessionKey: $sessionKey, title: $title, description: $description, purpose: $purpose, status: $status, createdByActorId: $createdByActorId, sourceKind: $sourceKind, sourceRef: $sourceRef, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class _$EnvironmentSessionViewCopyWith<$Res> implements $EnvironmentSessionViewCopyWith<$Res> {
  factory _$EnvironmentSessionViewCopyWith(_EnvironmentSessionView value, $Res Function(_EnvironmentSessionView) _then) = __$EnvironmentSessionViewCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue environmentSessionId,@UuidValueConverter() UuidValue? environmentSessionConfigId,@UuidValueConverter() UuidValue? identitySessionId, SessionSummary? identitySession,@UuidValueConverter() UuidValue environmentId,@UuidValueConverter() UuidValue environmentProfileId, String sessionKey, String? title, String? description, String? purpose, String status,@UuidValueConverter() UuidValue? createdByActorId, String? sourceKind, String? sourceRef, Map<String, dynamic> evidence
});


@override $SessionSummaryCopyWith<$Res>? get identitySession;

}
/// @nodoc
class __$EnvironmentSessionViewCopyWithImpl<$Res>
    implements _$EnvironmentSessionViewCopyWith<$Res> {
  __$EnvironmentSessionViewCopyWithImpl(this._self, this._then);

  final _EnvironmentSessionView _self;
  final $Res Function(_EnvironmentSessionView) _then;

/// Create a copy of EnvironmentSessionView
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? environmentSessionId = null,Object? environmentSessionConfigId = freezed,Object? identitySessionId = freezed,Object? identitySession = freezed,Object? environmentId = null,Object? environmentProfileId = null,Object? sessionKey = null,Object? title = freezed,Object? description = freezed,Object? purpose = freezed,Object? status = null,Object? createdByActorId = freezed,Object? sourceKind = freezed,Object? sourceRef = freezed,Object? evidence = null,}) {
  return _then(_EnvironmentSessionView(
environmentSessionId: null == environmentSessionId ? _self.environmentSessionId : environmentSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentSessionConfigId: freezed == environmentSessionConfigId ? _self.environmentSessionConfigId : environmentSessionConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,identitySessionId: freezed == identitySessionId ? _self.identitySessionId : identitySessionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,identitySession: freezed == identitySession ? _self.identitySession : identitySession // ignore: cast_nullable_to_non_nullable
as SessionSummary?,environmentId: null == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentProfileId: null == environmentProfileId ? _self.environmentProfileId : environmentProfileId // ignore: cast_nullable_to_non_nullable
as UuidValue,sessionKey: null == sessionKey ? _self.sessionKey : sessionKey // ignore: cast_nullable_to_non_nullable
as String,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,purpose: freezed == purpose ? _self.purpose : purpose // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,createdByActorId: freezed == createdByActorId ? _self.createdByActorId : createdByActorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sourceKind: freezed == sourceKind ? _self.sourceKind : sourceKind // ignore: cast_nullable_to_non_nullable
as String?,sourceRef: freezed == sourceRef ? _self.sourceRef : sourceRef // ignore: cast_nullable_to_non_nullable
as String?,evidence: null == evidence ? _self._evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

/// Create a copy of EnvironmentSessionView
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$SessionSummaryCopyWith<$Res>? get identitySession {
    if (_self.identitySession == null) {
    return null;
  }

  return $SessionSummaryCopyWith<$Res>(_self.identitySession!, (value) {
    return _then(_self.copyWith(identitySession: value));
  });
}
}


/// @nodoc
mixin _$EnvironmentSessionJoinReceipt {

 bool get accepted; String get status; String? get error; String? get reason;@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue get environmentId;@UuidValueConverter() UuidValue get environmentProfileId;@UuidValueConverter() UuidValue? get environmentSessionId; String? get environmentSessionKey; EnvironmentSessionIdentityEvidence? get identityEvidence; List<String> get blockers; Map<String, dynamic> get evidence;
/// Create a copy of EnvironmentSessionJoinReceipt
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$EnvironmentSessionJoinReceiptCopyWith<EnvironmentSessionJoinReceipt> get copyWith => _$EnvironmentSessionJoinReceiptCopyWithImpl<EnvironmentSessionJoinReceipt>(this as EnvironmentSessionJoinReceipt, _$identity);

  /// Serializes this EnvironmentSessionJoinReceipt to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is EnvironmentSessionJoinReceipt&&(identical(other.accepted, accepted) || other.accepted == accepted)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.reason, reason) || other.reason == reason)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentProfileId, environmentProfileId) || other.environmentProfileId == environmentProfileId)&&(identical(other.environmentSessionId, environmentSessionId) || other.environmentSessionId == environmentSessionId)&&(identical(other.environmentSessionKey, environmentSessionKey) || other.environmentSessionKey == environmentSessionKey)&&(identical(other.identityEvidence, identityEvidence) || other.identityEvidence == identityEvidence)&&const DeepCollectionEquality().equals(other.blockers, blockers)&&const DeepCollectionEquality().equals(other.evidence, evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,accepted,status,error,reason,actorId,environmentId,environmentProfileId,environmentSessionId,environmentSessionKey,identityEvidence,const DeepCollectionEquality().hash(blockers),const DeepCollectionEquality().hash(evidence));

@override
String toString() {
  return 'EnvironmentSessionJoinReceipt(accepted: $accepted, status: $status, error: $error, reason: $reason, actorId: $actorId, environmentId: $environmentId, environmentProfileId: $environmentProfileId, environmentSessionId: $environmentSessionId, environmentSessionKey: $environmentSessionKey, identityEvidence: $identityEvidence, blockers: $blockers, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class $EnvironmentSessionJoinReceiptCopyWith<$Res>  {
  factory $EnvironmentSessionJoinReceiptCopyWith(EnvironmentSessionJoinReceipt value, $Res Function(EnvironmentSessionJoinReceipt) _then) = _$EnvironmentSessionJoinReceiptCopyWithImpl;
@useResult
$Res call({
 bool accepted, String status, String? error, String? reason,@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue environmentId,@UuidValueConverter() UuidValue environmentProfileId,@UuidValueConverter() UuidValue? environmentSessionId, String? environmentSessionKey, EnvironmentSessionIdentityEvidence? identityEvidence, List<String> blockers, Map<String, dynamic> evidence
});


$EnvironmentSessionIdentityEvidenceCopyWith<$Res>? get identityEvidence;

}
/// @nodoc
class _$EnvironmentSessionJoinReceiptCopyWithImpl<$Res>
    implements $EnvironmentSessionJoinReceiptCopyWith<$Res> {
  _$EnvironmentSessionJoinReceiptCopyWithImpl(this._self, this._then);

  final EnvironmentSessionJoinReceipt _self;
  final $Res Function(EnvironmentSessionJoinReceipt) _then;

/// Create a copy of EnvironmentSessionJoinReceipt
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? accepted = null,Object? status = null,Object? error = freezed,Object? reason = freezed,Object? actorId = freezed,Object? environmentId = null,Object? environmentProfileId = null,Object? environmentSessionId = freezed,Object? environmentSessionKey = freezed,Object? identityEvidence = freezed,Object? blockers = null,Object? evidence = null,}) {
  return _then(_self.copyWith(
accepted: null == accepted ? _self.accepted : accepted // ignore: cast_nullable_to_non_nullable
as bool,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,reason: freezed == reason ? _self.reason : reason // ignore: cast_nullable_to_non_nullable
as String?,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentId: null == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentProfileId: null == environmentProfileId ? _self.environmentProfileId : environmentProfileId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentSessionId: freezed == environmentSessionId ? _self.environmentSessionId : environmentSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentSessionKey: freezed == environmentSessionKey ? _self.environmentSessionKey : environmentSessionKey // ignore: cast_nullable_to_non_nullable
as String?,identityEvidence: freezed == identityEvidence ? _self.identityEvidence : identityEvidence // ignore: cast_nullable_to_non_nullable
as EnvironmentSessionIdentityEvidence?,blockers: null == blockers ? _self.blockers : blockers // ignore: cast_nullable_to_non_nullable
as List<String>,evidence: null == evidence ? _self.evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}
/// Create a copy of EnvironmentSessionJoinReceipt
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$EnvironmentSessionIdentityEvidenceCopyWith<$Res>? get identityEvidence {
    if (_self.identityEvidence == null) {
    return null;
  }

  return $EnvironmentSessionIdentityEvidenceCopyWith<$Res>(_self.identityEvidence!, (value) {
    return _then(_self.copyWith(identityEvidence: value));
  });
}
}


/// Adds pattern-matching-related methods to [EnvironmentSessionJoinReceipt].
extension EnvironmentSessionJoinReceiptPatterns on EnvironmentSessionJoinReceipt {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _EnvironmentSessionJoinReceipt value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _EnvironmentSessionJoinReceipt() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _EnvironmentSessionJoinReceipt value)  def,}){
final _that = this;
switch (_that) {
case _EnvironmentSessionJoinReceipt():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _EnvironmentSessionJoinReceipt value)?  def,}){
final _that = this;
switch (_that) {
case _EnvironmentSessionJoinReceipt() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( bool accepted,  String status,  String? error,  String? reason, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue environmentId, @UuidValueConverter()  UuidValue environmentProfileId, @UuidValueConverter()  UuidValue? environmentSessionId,  String? environmentSessionKey,  EnvironmentSessionIdentityEvidence? identityEvidence,  List<String> blockers,  Map<String, dynamic> evidence)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _EnvironmentSessionJoinReceipt() when def != null:
return def(_that.accepted,_that.status,_that.error,_that.reason,_that.actorId,_that.environmentId,_that.environmentProfileId,_that.environmentSessionId,_that.environmentSessionKey,_that.identityEvidence,_that.blockers,_that.evidence);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( bool accepted,  String status,  String? error,  String? reason, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue environmentId, @UuidValueConverter()  UuidValue environmentProfileId, @UuidValueConverter()  UuidValue? environmentSessionId,  String? environmentSessionKey,  EnvironmentSessionIdentityEvidence? identityEvidence,  List<String> blockers,  Map<String, dynamic> evidence)  def,}) {final _that = this;
switch (_that) {
case _EnvironmentSessionJoinReceipt():
return def(_that.accepted,_that.status,_that.error,_that.reason,_that.actorId,_that.environmentId,_that.environmentProfileId,_that.environmentSessionId,_that.environmentSessionKey,_that.identityEvidence,_that.blockers,_that.evidence);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( bool accepted,  String status,  String? error,  String? reason, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue environmentId, @UuidValueConverter()  UuidValue environmentProfileId, @UuidValueConverter()  UuidValue? environmentSessionId,  String? environmentSessionKey,  EnvironmentSessionIdentityEvidence? identityEvidence,  List<String> blockers,  Map<String, dynamic> evidence)?  def,}) {final _that = this;
switch (_that) {
case _EnvironmentSessionJoinReceipt() when def != null:
return def(_that.accepted,_that.status,_that.error,_that.reason,_that.actorId,_that.environmentId,_that.environmentProfileId,_that.environmentSessionId,_that.environmentSessionKey,_that.identityEvidence,_that.blockers,_that.evidence);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _EnvironmentSessionJoinReceipt implements EnvironmentSessionJoinReceipt {
   _EnvironmentSessionJoinReceipt({required this.accepted, required this.status, this.error, this.reason, @UuidValueConverter() this.actorId, @UuidValueConverter() required this.environmentId, @UuidValueConverter() required this.environmentProfileId, @UuidValueConverter() this.environmentSessionId, this.environmentSessionKey, this.identityEvidence, final  List<String> blockers = const [], required final  Map<String, dynamic> evidence}): _blockers = blockers,_evidence = evidence;
  factory _EnvironmentSessionJoinReceipt.fromJson(Map<String, dynamic> json) => _$EnvironmentSessionJoinReceiptFromJson(json);

@override final  bool accepted;
@override final  String status;
@override final  String? error;
@override final  String? reason;
@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue environmentId;
@override@UuidValueConverter() final  UuidValue environmentProfileId;
@override@UuidValueConverter() final  UuidValue? environmentSessionId;
@override final  String? environmentSessionKey;
@override final  EnvironmentSessionIdentityEvidence? identityEvidence;
 final  List<String> _blockers;
@override@JsonKey() List<String> get blockers {
  if (_blockers is EqualUnmodifiableListView) return _blockers;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_blockers);
}

 final  Map<String, dynamic> _evidence;
@override Map<String, dynamic> get evidence {
  if (_evidence is EqualUnmodifiableMapView) return _evidence;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_evidence);
}


/// Create a copy of EnvironmentSessionJoinReceipt
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$EnvironmentSessionJoinReceiptCopyWith<_EnvironmentSessionJoinReceipt> get copyWith => __$EnvironmentSessionJoinReceiptCopyWithImpl<_EnvironmentSessionJoinReceipt>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$EnvironmentSessionJoinReceiptToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _EnvironmentSessionJoinReceipt&&(identical(other.accepted, accepted) || other.accepted == accepted)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.reason, reason) || other.reason == reason)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentProfileId, environmentProfileId) || other.environmentProfileId == environmentProfileId)&&(identical(other.environmentSessionId, environmentSessionId) || other.environmentSessionId == environmentSessionId)&&(identical(other.environmentSessionKey, environmentSessionKey) || other.environmentSessionKey == environmentSessionKey)&&(identical(other.identityEvidence, identityEvidence) || other.identityEvidence == identityEvidence)&&const DeepCollectionEquality().equals(other._blockers, _blockers)&&const DeepCollectionEquality().equals(other._evidence, _evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,accepted,status,error,reason,actorId,environmentId,environmentProfileId,environmentSessionId,environmentSessionKey,identityEvidence,const DeepCollectionEquality().hash(_blockers),const DeepCollectionEquality().hash(_evidence));

@override
String toString() {
  return 'EnvironmentSessionJoinReceipt.def(accepted: $accepted, status: $status, error: $error, reason: $reason, actorId: $actorId, environmentId: $environmentId, environmentProfileId: $environmentProfileId, environmentSessionId: $environmentSessionId, environmentSessionKey: $environmentSessionKey, identityEvidence: $identityEvidence, blockers: $blockers, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class _$EnvironmentSessionJoinReceiptCopyWith<$Res> implements $EnvironmentSessionJoinReceiptCopyWith<$Res> {
  factory _$EnvironmentSessionJoinReceiptCopyWith(_EnvironmentSessionJoinReceipt value, $Res Function(_EnvironmentSessionJoinReceipt) _then) = __$EnvironmentSessionJoinReceiptCopyWithImpl;
@override @useResult
$Res call({
 bool accepted, String status, String? error, String? reason,@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue environmentId,@UuidValueConverter() UuidValue environmentProfileId,@UuidValueConverter() UuidValue? environmentSessionId, String? environmentSessionKey, EnvironmentSessionIdentityEvidence? identityEvidence, List<String> blockers, Map<String, dynamic> evidence
});


@override $EnvironmentSessionIdentityEvidenceCopyWith<$Res>? get identityEvidence;

}
/// @nodoc
class __$EnvironmentSessionJoinReceiptCopyWithImpl<$Res>
    implements _$EnvironmentSessionJoinReceiptCopyWith<$Res> {
  __$EnvironmentSessionJoinReceiptCopyWithImpl(this._self, this._then);

  final _EnvironmentSessionJoinReceipt _self;
  final $Res Function(_EnvironmentSessionJoinReceipt) _then;

/// Create a copy of EnvironmentSessionJoinReceipt
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? accepted = null,Object? status = null,Object? error = freezed,Object? reason = freezed,Object? actorId = freezed,Object? environmentId = null,Object? environmentProfileId = null,Object? environmentSessionId = freezed,Object? environmentSessionKey = freezed,Object? identityEvidence = freezed,Object? blockers = null,Object? evidence = null,}) {
  return _then(_EnvironmentSessionJoinReceipt(
accepted: null == accepted ? _self.accepted : accepted // ignore: cast_nullable_to_non_nullable
as bool,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,reason: freezed == reason ? _self.reason : reason // ignore: cast_nullable_to_non_nullable
as String?,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentId: null == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentProfileId: null == environmentProfileId ? _self.environmentProfileId : environmentProfileId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentSessionId: freezed == environmentSessionId ? _self.environmentSessionId : environmentSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentSessionKey: freezed == environmentSessionKey ? _self.environmentSessionKey : environmentSessionKey // ignore: cast_nullable_to_non_nullable
as String?,identityEvidence: freezed == identityEvidence ? _self.identityEvidence : identityEvidence // ignore: cast_nullable_to_non_nullable
as EnvironmentSessionIdentityEvidence?,blockers: null == blockers ? _self._blockers : blockers // ignore: cast_nullable_to_non_nullable
as List<String>,evidence: null == evidence ? _self._evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

/// Create a copy of EnvironmentSessionJoinReceipt
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$EnvironmentSessionIdentityEvidenceCopyWith<$Res>? get identityEvidence {
    if (_self.identityEvidence == null) {
    return null;
  }

  return $EnvironmentSessionIdentityEvidenceCopyWith<$Res>(_self.identityEvidence!, (value) {
    return _then(_self.copyWith(identityEvidence: value));
  });
}
}


/// @nodoc
mixin _$EnvironmentNavigationContextView {

@UuidValueConverter() UuidValue get environmentNavigationContextId;@UuidValueConverter() UuidValue get environmentSessionId;@UuidValueConverter() UuidValue get environmentId; String get key; String? get title; String get status; bool get isDefault;@UuidValueConverter() UuidValue? get selectedProcessId;@UuidValueConverter() UuidValue? get selectedThreadId;@UuidValueConverter() UuidValue? get branchId; String? get projectionHash;@UuidValueConverter() UuidValue? get rootObjectId;@UuidValueConverter() UuidValue? get commitId;@UuidValueConverter() UuidValue? get objectInstanceGraphCommitId; String? get graphHashPost; Map<String, dynamic> get evidence;
/// Create a copy of EnvironmentNavigationContextView
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$EnvironmentNavigationContextViewCopyWith<EnvironmentNavigationContextView> get copyWith => _$EnvironmentNavigationContextViewCopyWithImpl<EnvironmentNavigationContextView>(this as EnvironmentNavigationContextView, _$identity);

  /// Serializes this EnvironmentNavigationContextView to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is EnvironmentNavigationContextView&&(identical(other.environmentNavigationContextId, environmentNavigationContextId) || other.environmentNavigationContextId == environmentNavigationContextId)&&(identical(other.environmentSessionId, environmentSessionId) || other.environmentSessionId == environmentSessionId)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.key, key) || other.key == key)&&(identical(other.title, title) || other.title == title)&&(identical(other.status, status) || other.status == status)&&(identical(other.isDefault, isDefault) || other.isDefault == isDefault)&&(identical(other.selectedProcessId, selectedProcessId) || other.selectedProcessId == selectedProcessId)&&(identical(other.selectedThreadId, selectedThreadId) || other.selectedThreadId == selectedThreadId)&&(identical(other.branchId, branchId) || other.branchId == branchId)&&(identical(other.projectionHash, projectionHash) || other.projectionHash == projectionHash)&&(identical(other.rootObjectId, rootObjectId) || other.rootObjectId == rootObjectId)&&(identical(other.commitId, commitId) || other.commitId == commitId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.graphHashPost, graphHashPost) || other.graphHashPost == graphHashPost)&&const DeepCollectionEquality().equals(other.evidence, evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,environmentNavigationContextId,environmentSessionId,environmentId,key,title,status,isDefault,selectedProcessId,selectedThreadId,branchId,projectionHash,rootObjectId,commitId,objectInstanceGraphCommitId,graphHashPost,const DeepCollectionEquality().hash(evidence));

@override
String toString() {
  return 'EnvironmentNavigationContextView(environmentNavigationContextId: $environmentNavigationContextId, environmentSessionId: $environmentSessionId, environmentId: $environmentId, key: $key, title: $title, status: $status, isDefault: $isDefault, selectedProcessId: $selectedProcessId, selectedThreadId: $selectedThreadId, branchId: $branchId, projectionHash: $projectionHash, rootObjectId: $rootObjectId, commitId: $commitId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, graphHashPost: $graphHashPost, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class $EnvironmentNavigationContextViewCopyWith<$Res>  {
  factory $EnvironmentNavigationContextViewCopyWith(EnvironmentNavigationContextView value, $Res Function(EnvironmentNavigationContextView) _then) = _$EnvironmentNavigationContextViewCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue environmentNavigationContextId,@UuidValueConverter() UuidValue environmentSessionId,@UuidValueConverter() UuidValue environmentId, String key, String? title, String status, bool isDefault,@UuidValueConverter() UuidValue? selectedProcessId,@UuidValueConverter() UuidValue? selectedThreadId,@UuidValueConverter() UuidValue? branchId, String? projectionHash,@UuidValueConverter() UuidValue? rootObjectId,@UuidValueConverter() UuidValue? commitId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String? graphHashPost, Map<String, dynamic> evidence
});




}
/// @nodoc
class _$EnvironmentNavigationContextViewCopyWithImpl<$Res>
    implements $EnvironmentNavigationContextViewCopyWith<$Res> {
  _$EnvironmentNavigationContextViewCopyWithImpl(this._self, this._then);

  final EnvironmentNavigationContextView _self;
  final $Res Function(EnvironmentNavigationContextView) _then;

/// Create a copy of EnvironmentNavigationContextView
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? environmentNavigationContextId = null,Object? environmentSessionId = null,Object? environmentId = null,Object? key = null,Object? title = freezed,Object? status = null,Object? isDefault = null,Object? selectedProcessId = freezed,Object? selectedThreadId = freezed,Object? branchId = freezed,Object? projectionHash = freezed,Object? rootObjectId = freezed,Object? commitId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? graphHashPost = freezed,Object? evidence = null,}) {
  return _then(_self.copyWith(
environmentNavigationContextId: null == environmentNavigationContextId ? _self.environmentNavigationContextId : environmentNavigationContextId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentSessionId: null == environmentSessionId ? _self.environmentSessionId : environmentSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentId: null == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,key: null == key ? _self.key : key // ignore: cast_nullable_to_non_nullable
as String,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,isDefault: null == isDefault ? _self.isDefault : isDefault // ignore: cast_nullable_to_non_nullable
as bool,selectedProcessId: freezed == selectedProcessId ? _self.selectedProcessId : selectedProcessId // ignore: cast_nullable_to_non_nullable
as UuidValue?,selectedThreadId: freezed == selectedThreadId ? _self.selectedThreadId : selectedThreadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,branchId: freezed == branchId ? _self.branchId : branchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,projectionHash: freezed == projectionHash ? _self.projectionHash : projectionHash // ignore: cast_nullable_to_non_nullable
as String?,rootObjectId: freezed == rootObjectId ? _self.rootObjectId : rootObjectId // ignore: cast_nullable_to_non_nullable
as UuidValue?,commitId: freezed == commitId ? _self.commitId : commitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,graphHashPost: freezed == graphHashPost ? _self.graphHashPost : graphHashPost // ignore: cast_nullable_to_non_nullable
as String?,evidence: null == evidence ? _self.evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [EnvironmentNavigationContextView].
extension EnvironmentNavigationContextViewPatterns on EnvironmentNavigationContextView {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _EnvironmentNavigationContextView value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _EnvironmentNavigationContextView() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _EnvironmentNavigationContextView value)  def,}){
final _that = this;
switch (_that) {
case _EnvironmentNavigationContextView():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _EnvironmentNavigationContextView value)?  def,}){
final _that = this;
switch (_that) {
case _EnvironmentNavigationContextView() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue environmentNavigationContextId, @UuidValueConverter()  UuidValue environmentSessionId, @UuidValueConverter()  UuidValue environmentId,  String key,  String? title,  String status,  bool isDefault, @UuidValueConverter()  UuidValue? selectedProcessId, @UuidValueConverter()  UuidValue? selectedThreadId, @UuidValueConverter()  UuidValue? branchId,  String? projectionHash, @UuidValueConverter()  UuidValue? rootObjectId, @UuidValueConverter()  UuidValue? commitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? graphHashPost,  Map<String, dynamic> evidence)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _EnvironmentNavigationContextView() when def != null:
return def(_that.environmentNavigationContextId,_that.environmentSessionId,_that.environmentId,_that.key,_that.title,_that.status,_that.isDefault,_that.selectedProcessId,_that.selectedThreadId,_that.branchId,_that.projectionHash,_that.rootObjectId,_that.commitId,_that.objectInstanceGraphCommitId,_that.graphHashPost,_that.evidence);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue environmentNavigationContextId, @UuidValueConverter()  UuidValue environmentSessionId, @UuidValueConverter()  UuidValue environmentId,  String key,  String? title,  String status,  bool isDefault, @UuidValueConverter()  UuidValue? selectedProcessId, @UuidValueConverter()  UuidValue? selectedThreadId, @UuidValueConverter()  UuidValue? branchId,  String? projectionHash, @UuidValueConverter()  UuidValue? rootObjectId, @UuidValueConverter()  UuidValue? commitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? graphHashPost,  Map<String, dynamic> evidence)  def,}) {final _that = this;
switch (_that) {
case _EnvironmentNavigationContextView():
return def(_that.environmentNavigationContextId,_that.environmentSessionId,_that.environmentId,_that.key,_that.title,_that.status,_that.isDefault,_that.selectedProcessId,_that.selectedThreadId,_that.branchId,_that.projectionHash,_that.rootObjectId,_that.commitId,_that.objectInstanceGraphCommitId,_that.graphHashPost,_that.evidence);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue environmentNavigationContextId, @UuidValueConverter()  UuidValue environmentSessionId, @UuidValueConverter()  UuidValue environmentId,  String key,  String? title,  String status,  bool isDefault, @UuidValueConverter()  UuidValue? selectedProcessId, @UuidValueConverter()  UuidValue? selectedThreadId, @UuidValueConverter()  UuidValue? branchId,  String? projectionHash, @UuidValueConverter()  UuidValue? rootObjectId, @UuidValueConverter()  UuidValue? commitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? graphHashPost,  Map<String, dynamic> evidence)?  def,}) {final _that = this;
switch (_that) {
case _EnvironmentNavigationContextView() when def != null:
return def(_that.environmentNavigationContextId,_that.environmentSessionId,_that.environmentId,_that.key,_that.title,_that.status,_that.isDefault,_that.selectedProcessId,_that.selectedThreadId,_that.branchId,_that.projectionHash,_that.rootObjectId,_that.commitId,_that.objectInstanceGraphCommitId,_that.graphHashPost,_that.evidence);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _EnvironmentNavigationContextView implements EnvironmentNavigationContextView {
   _EnvironmentNavigationContextView({@UuidValueConverter() required this.environmentNavigationContextId, @UuidValueConverter() required this.environmentSessionId, @UuidValueConverter() required this.environmentId, required this.key, this.title, required this.status, required this.isDefault, @UuidValueConverter() this.selectedProcessId, @UuidValueConverter() this.selectedThreadId, @UuidValueConverter() this.branchId, this.projectionHash, @UuidValueConverter() this.rootObjectId, @UuidValueConverter() this.commitId, @UuidValueConverter() this.objectInstanceGraphCommitId, this.graphHashPost, required final  Map<String, dynamic> evidence}): _evidence = evidence;
  factory _EnvironmentNavigationContextView.fromJson(Map<String, dynamic> json) => _$EnvironmentNavigationContextViewFromJson(json);

@override@UuidValueConverter() final  UuidValue environmentNavigationContextId;
@override@UuidValueConverter() final  UuidValue environmentSessionId;
@override@UuidValueConverter() final  UuidValue environmentId;
@override final  String key;
@override final  String? title;
@override final  String status;
@override final  bool isDefault;
@override@UuidValueConverter() final  UuidValue? selectedProcessId;
@override@UuidValueConverter() final  UuidValue? selectedThreadId;
@override@UuidValueConverter() final  UuidValue? branchId;
@override final  String? projectionHash;
@override@UuidValueConverter() final  UuidValue? rootObjectId;
@override@UuidValueConverter() final  UuidValue? commitId;
@override@UuidValueConverter() final  UuidValue? objectInstanceGraphCommitId;
@override final  String? graphHashPost;
 final  Map<String, dynamic> _evidence;
@override Map<String, dynamic> get evidence {
  if (_evidence is EqualUnmodifiableMapView) return _evidence;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_evidence);
}


/// Create a copy of EnvironmentNavigationContextView
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$EnvironmentNavigationContextViewCopyWith<_EnvironmentNavigationContextView> get copyWith => __$EnvironmentNavigationContextViewCopyWithImpl<_EnvironmentNavigationContextView>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$EnvironmentNavigationContextViewToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _EnvironmentNavigationContextView&&(identical(other.environmentNavigationContextId, environmentNavigationContextId) || other.environmentNavigationContextId == environmentNavigationContextId)&&(identical(other.environmentSessionId, environmentSessionId) || other.environmentSessionId == environmentSessionId)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.key, key) || other.key == key)&&(identical(other.title, title) || other.title == title)&&(identical(other.status, status) || other.status == status)&&(identical(other.isDefault, isDefault) || other.isDefault == isDefault)&&(identical(other.selectedProcessId, selectedProcessId) || other.selectedProcessId == selectedProcessId)&&(identical(other.selectedThreadId, selectedThreadId) || other.selectedThreadId == selectedThreadId)&&(identical(other.branchId, branchId) || other.branchId == branchId)&&(identical(other.projectionHash, projectionHash) || other.projectionHash == projectionHash)&&(identical(other.rootObjectId, rootObjectId) || other.rootObjectId == rootObjectId)&&(identical(other.commitId, commitId) || other.commitId == commitId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.graphHashPost, graphHashPost) || other.graphHashPost == graphHashPost)&&const DeepCollectionEquality().equals(other._evidence, _evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,environmentNavigationContextId,environmentSessionId,environmentId,key,title,status,isDefault,selectedProcessId,selectedThreadId,branchId,projectionHash,rootObjectId,commitId,objectInstanceGraphCommitId,graphHashPost,const DeepCollectionEquality().hash(_evidence));

@override
String toString() {
  return 'EnvironmentNavigationContextView.def(environmentNavigationContextId: $environmentNavigationContextId, environmentSessionId: $environmentSessionId, environmentId: $environmentId, key: $key, title: $title, status: $status, isDefault: $isDefault, selectedProcessId: $selectedProcessId, selectedThreadId: $selectedThreadId, branchId: $branchId, projectionHash: $projectionHash, rootObjectId: $rootObjectId, commitId: $commitId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, graphHashPost: $graphHashPost, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class _$EnvironmentNavigationContextViewCopyWith<$Res> implements $EnvironmentNavigationContextViewCopyWith<$Res> {
  factory _$EnvironmentNavigationContextViewCopyWith(_EnvironmentNavigationContextView value, $Res Function(_EnvironmentNavigationContextView) _then) = __$EnvironmentNavigationContextViewCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue environmentNavigationContextId,@UuidValueConverter() UuidValue environmentSessionId,@UuidValueConverter() UuidValue environmentId, String key, String? title, String status, bool isDefault,@UuidValueConverter() UuidValue? selectedProcessId,@UuidValueConverter() UuidValue? selectedThreadId,@UuidValueConverter() UuidValue? branchId, String? projectionHash,@UuidValueConverter() UuidValue? rootObjectId,@UuidValueConverter() UuidValue? commitId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String? graphHashPost, Map<String, dynamic> evidence
});




}
/// @nodoc
class __$EnvironmentNavigationContextViewCopyWithImpl<$Res>
    implements _$EnvironmentNavigationContextViewCopyWith<$Res> {
  __$EnvironmentNavigationContextViewCopyWithImpl(this._self, this._then);

  final _EnvironmentNavigationContextView _self;
  final $Res Function(_EnvironmentNavigationContextView) _then;

/// Create a copy of EnvironmentNavigationContextView
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? environmentNavigationContextId = null,Object? environmentSessionId = null,Object? environmentId = null,Object? key = null,Object? title = freezed,Object? status = null,Object? isDefault = null,Object? selectedProcessId = freezed,Object? selectedThreadId = freezed,Object? branchId = freezed,Object? projectionHash = freezed,Object? rootObjectId = freezed,Object? commitId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? graphHashPost = freezed,Object? evidence = null,}) {
  return _then(_EnvironmentNavigationContextView(
environmentNavigationContextId: null == environmentNavigationContextId ? _self.environmentNavigationContextId : environmentNavigationContextId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentSessionId: null == environmentSessionId ? _self.environmentSessionId : environmentSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentId: null == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,key: null == key ? _self.key : key // ignore: cast_nullable_to_non_nullable
as String,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,isDefault: null == isDefault ? _self.isDefault : isDefault // ignore: cast_nullable_to_non_nullable
as bool,selectedProcessId: freezed == selectedProcessId ? _self.selectedProcessId : selectedProcessId // ignore: cast_nullable_to_non_nullable
as UuidValue?,selectedThreadId: freezed == selectedThreadId ? _self.selectedThreadId : selectedThreadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,branchId: freezed == branchId ? _self.branchId : branchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,projectionHash: freezed == projectionHash ? _self.projectionHash : projectionHash // ignore: cast_nullable_to_non_nullable
as String?,rootObjectId: freezed == rootObjectId ? _self.rootObjectId : rootObjectId // ignore: cast_nullable_to_non_nullable
as UuidValue?,commitId: freezed == commitId ? _self.commitId : commitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,graphHashPost: freezed == graphHashPost ? _self.graphHashPost : graphHashPost // ignore: cast_nullable_to_non_nullable
as String?,evidence: null == evidence ? _self._evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$EnvironmentNavigationCommitReceipt {

 bool get accepted; String get status; String? get error; String? get reason;@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue get environmentId;@UuidValueConverter() UuidValue get environmentSessionId;@UuidValueConverter() UuidValue? get environmentNavigationContextId; String? get key; bool get isDefault;@UuidValueConverter() UuidValue? get branchId; String? get projectionHash;@UuidValueConverter() UuidValue? get rootObjectId;@UuidValueConverter() UuidValue? get commitId;@UuidValueConverter() UuidValue? get objectInstanceGraphCommitId; String? get graphHashPre; String? get graphHashPost;@UuidValueConverter() UuidValue? get functionCallId;@UuidValueConverter() UuidValue? get functionCallResponseId;@UuidValueConverter() UuidValue? get selectedProcessId;@UuidValueConverter() UuidValue? get selectedThreadId; List<String> get blockers; Map<String, dynamic> get evidence;
/// Create a copy of EnvironmentNavigationCommitReceipt
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$EnvironmentNavigationCommitReceiptCopyWith<EnvironmentNavigationCommitReceipt> get copyWith => _$EnvironmentNavigationCommitReceiptCopyWithImpl<EnvironmentNavigationCommitReceipt>(this as EnvironmentNavigationCommitReceipt, _$identity);

  /// Serializes this EnvironmentNavigationCommitReceipt to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is EnvironmentNavigationCommitReceipt&&(identical(other.accepted, accepted) || other.accepted == accepted)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.reason, reason) || other.reason == reason)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentSessionId, environmentSessionId) || other.environmentSessionId == environmentSessionId)&&(identical(other.environmentNavigationContextId, environmentNavigationContextId) || other.environmentNavigationContextId == environmentNavigationContextId)&&(identical(other.key, key) || other.key == key)&&(identical(other.isDefault, isDefault) || other.isDefault == isDefault)&&(identical(other.branchId, branchId) || other.branchId == branchId)&&(identical(other.projectionHash, projectionHash) || other.projectionHash == projectionHash)&&(identical(other.rootObjectId, rootObjectId) || other.rootObjectId == rootObjectId)&&(identical(other.commitId, commitId) || other.commitId == commitId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.graphHashPre, graphHashPre) || other.graphHashPre == graphHashPre)&&(identical(other.graphHashPost, graphHashPost) || other.graphHashPost == graphHashPost)&&(identical(other.functionCallId, functionCallId) || other.functionCallId == functionCallId)&&(identical(other.functionCallResponseId, functionCallResponseId) || other.functionCallResponseId == functionCallResponseId)&&(identical(other.selectedProcessId, selectedProcessId) || other.selectedProcessId == selectedProcessId)&&(identical(other.selectedThreadId, selectedThreadId) || other.selectedThreadId == selectedThreadId)&&const DeepCollectionEquality().equals(other.blockers, blockers)&&const DeepCollectionEquality().equals(other.evidence, evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,accepted,status,error,reason,actorId,environmentId,environmentSessionId,environmentNavigationContextId,key,isDefault,branchId,projectionHash,rootObjectId,commitId,objectInstanceGraphCommitId,graphHashPre,graphHashPost,functionCallId,functionCallResponseId,selectedProcessId,selectedThreadId,const DeepCollectionEquality().hash(blockers),const DeepCollectionEquality().hash(evidence)]);

@override
String toString() {
  return 'EnvironmentNavigationCommitReceipt(accepted: $accepted, status: $status, error: $error, reason: $reason, actorId: $actorId, environmentId: $environmentId, environmentSessionId: $environmentSessionId, environmentNavigationContextId: $environmentNavigationContextId, key: $key, isDefault: $isDefault, branchId: $branchId, projectionHash: $projectionHash, rootObjectId: $rootObjectId, commitId: $commitId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, graphHashPre: $graphHashPre, graphHashPost: $graphHashPost, functionCallId: $functionCallId, functionCallResponseId: $functionCallResponseId, selectedProcessId: $selectedProcessId, selectedThreadId: $selectedThreadId, blockers: $blockers, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class $EnvironmentNavigationCommitReceiptCopyWith<$Res>  {
  factory $EnvironmentNavigationCommitReceiptCopyWith(EnvironmentNavigationCommitReceipt value, $Res Function(EnvironmentNavigationCommitReceipt) _then) = _$EnvironmentNavigationCommitReceiptCopyWithImpl;
@useResult
$Res call({
 bool accepted, String status, String? error, String? reason,@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue environmentId,@UuidValueConverter() UuidValue environmentSessionId,@UuidValueConverter() UuidValue? environmentNavigationContextId, String? key, bool isDefault,@UuidValueConverter() UuidValue? branchId, String? projectionHash,@UuidValueConverter() UuidValue? rootObjectId,@UuidValueConverter() UuidValue? commitId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String? graphHashPre, String? graphHashPost,@UuidValueConverter() UuidValue? functionCallId,@UuidValueConverter() UuidValue? functionCallResponseId,@UuidValueConverter() UuidValue? selectedProcessId,@UuidValueConverter() UuidValue? selectedThreadId, List<String> blockers, Map<String, dynamic> evidence
});




}
/// @nodoc
class _$EnvironmentNavigationCommitReceiptCopyWithImpl<$Res>
    implements $EnvironmentNavigationCommitReceiptCopyWith<$Res> {
  _$EnvironmentNavigationCommitReceiptCopyWithImpl(this._self, this._then);

  final EnvironmentNavigationCommitReceipt _self;
  final $Res Function(EnvironmentNavigationCommitReceipt) _then;

/// Create a copy of EnvironmentNavigationCommitReceipt
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? accepted = null,Object? status = null,Object? error = freezed,Object? reason = freezed,Object? actorId = freezed,Object? environmentId = null,Object? environmentSessionId = null,Object? environmentNavigationContextId = freezed,Object? key = freezed,Object? isDefault = null,Object? branchId = freezed,Object? projectionHash = freezed,Object? rootObjectId = freezed,Object? commitId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? graphHashPre = freezed,Object? graphHashPost = freezed,Object? functionCallId = freezed,Object? functionCallResponseId = freezed,Object? selectedProcessId = freezed,Object? selectedThreadId = freezed,Object? blockers = null,Object? evidence = null,}) {
  return _then(_self.copyWith(
accepted: null == accepted ? _self.accepted : accepted // ignore: cast_nullable_to_non_nullable
as bool,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,reason: freezed == reason ? _self.reason : reason // ignore: cast_nullable_to_non_nullable
as String?,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentId: null == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentSessionId: null == environmentSessionId ? _self.environmentSessionId : environmentSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentNavigationContextId: freezed == environmentNavigationContextId ? _self.environmentNavigationContextId : environmentNavigationContextId // ignore: cast_nullable_to_non_nullable
as UuidValue?,key: freezed == key ? _self.key : key // ignore: cast_nullable_to_non_nullable
as String?,isDefault: null == isDefault ? _self.isDefault : isDefault // ignore: cast_nullable_to_non_nullable
as bool,branchId: freezed == branchId ? _self.branchId : branchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,projectionHash: freezed == projectionHash ? _self.projectionHash : projectionHash // ignore: cast_nullable_to_non_nullable
as String?,rootObjectId: freezed == rootObjectId ? _self.rootObjectId : rootObjectId // ignore: cast_nullable_to_non_nullable
as UuidValue?,commitId: freezed == commitId ? _self.commitId : commitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,graphHashPre: freezed == graphHashPre ? _self.graphHashPre : graphHashPre // ignore: cast_nullable_to_non_nullable
as String?,graphHashPost: freezed == graphHashPost ? _self.graphHashPost : graphHashPost // ignore: cast_nullable_to_non_nullable
as String?,functionCallId: freezed == functionCallId ? _self.functionCallId : functionCallId // ignore: cast_nullable_to_non_nullable
as UuidValue?,functionCallResponseId: freezed == functionCallResponseId ? _self.functionCallResponseId : functionCallResponseId // ignore: cast_nullable_to_non_nullable
as UuidValue?,selectedProcessId: freezed == selectedProcessId ? _self.selectedProcessId : selectedProcessId // ignore: cast_nullable_to_non_nullable
as UuidValue?,selectedThreadId: freezed == selectedThreadId ? _self.selectedThreadId : selectedThreadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,blockers: null == blockers ? _self.blockers : blockers // ignore: cast_nullable_to_non_nullable
as List<String>,evidence: null == evidence ? _self.evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [EnvironmentNavigationCommitReceipt].
extension EnvironmentNavigationCommitReceiptPatterns on EnvironmentNavigationCommitReceipt {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _EnvironmentNavigationCommitReceipt value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _EnvironmentNavigationCommitReceipt() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _EnvironmentNavigationCommitReceipt value)  def,}){
final _that = this;
switch (_that) {
case _EnvironmentNavigationCommitReceipt():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _EnvironmentNavigationCommitReceipt value)?  def,}){
final _that = this;
switch (_that) {
case _EnvironmentNavigationCommitReceipt() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( bool accepted,  String status,  String? error,  String? reason, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue environmentId, @UuidValueConverter()  UuidValue environmentSessionId, @UuidValueConverter()  UuidValue? environmentNavigationContextId,  String? key,  bool isDefault, @UuidValueConverter()  UuidValue? branchId,  String? projectionHash, @UuidValueConverter()  UuidValue? rootObjectId, @UuidValueConverter()  UuidValue? commitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? graphHashPre,  String? graphHashPost, @UuidValueConverter()  UuidValue? functionCallId, @UuidValueConverter()  UuidValue? functionCallResponseId, @UuidValueConverter()  UuidValue? selectedProcessId, @UuidValueConverter()  UuidValue? selectedThreadId,  List<String> blockers,  Map<String, dynamic> evidence)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _EnvironmentNavigationCommitReceipt() when def != null:
return def(_that.accepted,_that.status,_that.error,_that.reason,_that.actorId,_that.environmentId,_that.environmentSessionId,_that.environmentNavigationContextId,_that.key,_that.isDefault,_that.branchId,_that.projectionHash,_that.rootObjectId,_that.commitId,_that.objectInstanceGraphCommitId,_that.graphHashPre,_that.graphHashPost,_that.functionCallId,_that.functionCallResponseId,_that.selectedProcessId,_that.selectedThreadId,_that.blockers,_that.evidence);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( bool accepted,  String status,  String? error,  String? reason, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue environmentId, @UuidValueConverter()  UuidValue environmentSessionId, @UuidValueConverter()  UuidValue? environmentNavigationContextId,  String? key,  bool isDefault, @UuidValueConverter()  UuidValue? branchId,  String? projectionHash, @UuidValueConverter()  UuidValue? rootObjectId, @UuidValueConverter()  UuidValue? commitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? graphHashPre,  String? graphHashPost, @UuidValueConverter()  UuidValue? functionCallId, @UuidValueConverter()  UuidValue? functionCallResponseId, @UuidValueConverter()  UuidValue? selectedProcessId, @UuidValueConverter()  UuidValue? selectedThreadId,  List<String> blockers,  Map<String, dynamic> evidence)  def,}) {final _that = this;
switch (_that) {
case _EnvironmentNavigationCommitReceipt():
return def(_that.accepted,_that.status,_that.error,_that.reason,_that.actorId,_that.environmentId,_that.environmentSessionId,_that.environmentNavigationContextId,_that.key,_that.isDefault,_that.branchId,_that.projectionHash,_that.rootObjectId,_that.commitId,_that.objectInstanceGraphCommitId,_that.graphHashPre,_that.graphHashPost,_that.functionCallId,_that.functionCallResponseId,_that.selectedProcessId,_that.selectedThreadId,_that.blockers,_that.evidence);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( bool accepted,  String status,  String? error,  String? reason, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue environmentId, @UuidValueConverter()  UuidValue environmentSessionId, @UuidValueConverter()  UuidValue? environmentNavigationContextId,  String? key,  bool isDefault, @UuidValueConverter()  UuidValue? branchId,  String? projectionHash, @UuidValueConverter()  UuidValue? rootObjectId, @UuidValueConverter()  UuidValue? commitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? graphHashPre,  String? graphHashPost, @UuidValueConverter()  UuidValue? functionCallId, @UuidValueConverter()  UuidValue? functionCallResponseId, @UuidValueConverter()  UuidValue? selectedProcessId, @UuidValueConverter()  UuidValue? selectedThreadId,  List<String> blockers,  Map<String, dynamic> evidence)?  def,}) {final _that = this;
switch (_that) {
case _EnvironmentNavigationCommitReceipt() when def != null:
return def(_that.accepted,_that.status,_that.error,_that.reason,_that.actorId,_that.environmentId,_that.environmentSessionId,_that.environmentNavigationContextId,_that.key,_that.isDefault,_that.branchId,_that.projectionHash,_that.rootObjectId,_that.commitId,_that.objectInstanceGraphCommitId,_that.graphHashPre,_that.graphHashPost,_that.functionCallId,_that.functionCallResponseId,_that.selectedProcessId,_that.selectedThreadId,_that.blockers,_that.evidence);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _EnvironmentNavigationCommitReceipt implements EnvironmentNavigationCommitReceipt {
   _EnvironmentNavigationCommitReceipt({required this.accepted, required this.status, this.error, this.reason, @UuidValueConverter() this.actorId, @UuidValueConverter() required this.environmentId, @UuidValueConverter() required this.environmentSessionId, @UuidValueConverter() this.environmentNavigationContextId, this.key, required this.isDefault, @UuidValueConverter() this.branchId, this.projectionHash, @UuidValueConverter() this.rootObjectId, @UuidValueConverter() this.commitId, @UuidValueConverter() this.objectInstanceGraphCommitId, this.graphHashPre, this.graphHashPost, @UuidValueConverter() this.functionCallId, @UuidValueConverter() this.functionCallResponseId, @UuidValueConverter() this.selectedProcessId, @UuidValueConverter() this.selectedThreadId, final  List<String> blockers = const [], required final  Map<String, dynamic> evidence}): _blockers = blockers,_evidence = evidence;
  factory _EnvironmentNavigationCommitReceipt.fromJson(Map<String, dynamic> json) => _$EnvironmentNavigationCommitReceiptFromJson(json);

@override final  bool accepted;
@override final  String status;
@override final  String? error;
@override final  String? reason;
@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue environmentId;
@override@UuidValueConverter() final  UuidValue environmentSessionId;
@override@UuidValueConverter() final  UuidValue? environmentNavigationContextId;
@override final  String? key;
@override final  bool isDefault;
@override@UuidValueConverter() final  UuidValue? branchId;
@override final  String? projectionHash;
@override@UuidValueConverter() final  UuidValue? rootObjectId;
@override@UuidValueConverter() final  UuidValue? commitId;
@override@UuidValueConverter() final  UuidValue? objectInstanceGraphCommitId;
@override final  String? graphHashPre;
@override final  String? graphHashPost;
@override@UuidValueConverter() final  UuidValue? functionCallId;
@override@UuidValueConverter() final  UuidValue? functionCallResponseId;
@override@UuidValueConverter() final  UuidValue? selectedProcessId;
@override@UuidValueConverter() final  UuidValue? selectedThreadId;
 final  List<String> _blockers;
@override@JsonKey() List<String> get blockers {
  if (_blockers is EqualUnmodifiableListView) return _blockers;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_blockers);
}

 final  Map<String, dynamic> _evidence;
@override Map<String, dynamic> get evidence {
  if (_evidence is EqualUnmodifiableMapView) return _evidence;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_evidence);
}


/// Create a copy of EnvironmentNavigationCommitReceipt
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$EnvironmentNavigationCommitReceiptCopyWith<_EnvironmentNavigationCommitReceipt> get copyWith => __$EnvironmentNavigationCommitReceiptCopyWithImpl<_EnvironmentNavigationCommitReceipt>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$EnvironmentNavigationCommitReceiptToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _EnvironmentNavigationCommitReceipt&&(identical(other.accepted, accepted) || other.accepted == accepted)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.reason, reason) || other.reason == reason)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentSessionId, environmentSessionId) || other.environmentSessionId == environmentSessionId)&&(identical(other.environmentNavigationContextId, environmentNavigationContextId) || other.environmentNavigationContextId == environmentNavigationContextId)&&(identical(other.key, key) || other.key == key)&&(identical(other.isDefault, isDefault) || other.isDefault == isDefault)&&(identical(other.branchId, branchId) || other.branchId == branchId)&&(identical(other.projectionHash, projectionHash) || other.projectionHash == projectionHash)&&(identical(other.rootObjectId, rootObjectId) || other.rootObjectId == rootObjectId)&&(identical(other.commitId, commitId) || other.commitId == commitId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.graphHashPre, graphHashPre) || other.graphHashPre == graphHashPre)&&(identical(other.graphHashPost, graphHashPost) || other.graphHashPost == graphHashPost)&&(identical(other.functionCallId, functionCallId) || other.functionCallId == functionCallId)&&(identical(other.functionCallResponseId, functionCallResponseId) || other.functionCallResponseId == functionCallResponseId)&&(identical(other.selectedProcessId, selectedProcessId) || other.selectedProcessId == selectedProcessId)&&(identical(other.selectedThreadId, selectedThreadId) || other.selectedThreadId == selectedThreadId)&&const DeepCollectionEquality().equals(other._blockers, _blockers)&&const DeepCollectionEquality().equals(other._evidence, _evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,accepted,status,error,reason,actorId,environmentId,environmentSessionId,environmentNavigationContextId,key,isDefault,branchId,projectionHash,rootObjectId,commitId,objectInstanceGraphCommitId,graphHashPre,graphHashPost,functionCallId,functionCallResponseId,selectedProcessId,selectedThreadId,const DeepCollectionEquality().hash(_blockers),const DeepCollectionEquality().hash(_evidence)]);

@override
String toString() {
  return 'EnvironmentNavigationCommitReceipt.def(accepted: $accepted, status: $status, error: $error, reason: $reason, actorId: $actorId, environmentId: $environmentId, environmentSessionId: $environmentSessionId, environmentNavigationContextId: $environmentNavigationContextId, key: $key, isDefault: $isDefault, branchId: $branchId, projectionHash: $projectionHash, rootObjectId: $rootObjectId, commitId: $commitId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, graphHashPre: $graphHashPre, graphHashPost: $graphHashPost, functionCallId: $functionCallId, functionCallResponseId: $functionCallResponseId, selectedProcessId: $selectedProcessId, selectedThreadId: $selectedThreadId, blockers: $blockers, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class _$EnvironmentNavigationCommitReceiptCopyWith<$Res> implements $EnvironmentNavigationCommitReceiptCopyWith<$Res> {
  factory _$EnvironmentNavigationCommitReceiptCopyWith(_EnvironmentNavigationCommitReceipt value, $Res Function(_EnvironmentNavigationCommitReceipt) _then) = __$EnvironmentNavigationCommitReceiptCopyWithImpl;
@override @useResult
$Res call({
 bool accepted, String status, String? error, String? reason,@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue environmentId,@UuidValueConverter() UuidValue environmentSessionId,@UuidValueConverter() UuidValue? environmentNavigationContextId, String? key, bool isDefault,@UuidValueConverter() UuidValue? branchId, String? projectionHash,@UuidValueConverter() UuidValue? rootObjectId,@UuidValueConverter() UuidValue? commitId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String? graphHashPre, String? graphHashPost,@UuidValueConverter() UuidValue? functionCallId,@UuidValueConverter() UuidValue? functionCallResponseId,@UuidValueConverter() UuidValue? selectedProcessId,@UuidValueConverter() UuidValue? selectedThreadId, List<String> blockers, Map<String, dynamic> evidence
});




}
/// @nodoc
class __$EnvironmentNavigationCommitReceiptCopyWithImpl<$Res>
    implements _$EnvironmentNavigationCommitReceiptCopyWith<$Res> {
  __$EnvironmentNavigationCommitReceiptCopyWithImpl(this._self, this._then);

  final _EnvironmentNavigationCommitReceipt _self;
  final $Res Function(_EnvironmentNavigationCommitReceipt) _then;

/// Create a copy of EnvironmentNavigationCommitReceipt
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? accepted = null,Object? status = null,Object? error = freezed,Object? reason = freezed,Object? actorId = freezed,Object? environmentId = null,Object? environmentSessionId = null,Object? environmentNavigationContextId = freezed,Object? key = freezed,Object? isDefault = null,Object? branchId = freezed,Object? projectionHash = freezed,Object? rootObjectId = freezed,Object? commitId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? graphHashPre = freezed,Object? graphHashPost = freezed,Object? functionCallId = freezed,Object? functionCallResponseId = freezed,Object? selectedProcessId = freezed,Object? selectedThreadId = freezed,Object? blockers = null,Object? evidence = null,}) {
  return _then(_EnvironmentNavigationCommitReceipt(
accepted: null == accepted ? _self.accepted : accepted // ignore: cast_nullable_to_non_nullable
as bool,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,reason: freezed == reason ? _self.reason : reason // ignore: cast_nullable_to_non_nullable
as String?,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentId: null == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentSessionId: null == environmentSessionId ? _self.environmentSessionId : environmentSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentNavigationContextId: freezed == environmentNavigationContextId ? _self.environmentNavigationContextId : environmentNavigationContextId // ignore: cast_nullable_to_non_nullable
as UuidValue?,key: freezed == key ? _self.key : key // ignore: cast_nullable_to_non_nullable
as String?,isDefault: null == isDefault ? _self.isDefault : isDefault // ignore: cast_nullable_to_non_nullable
as bool,branchId: freezed == branchId ? _self.branchId : branchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,projectionHash: freezed == projectionHash ? _self.projectionHash : projectionHash // ignore: cast_nullable_to_non_nullable
as String?,rootObjectId: freezed == rootObjectId ? _self.rootObjectId : rootObjectId // ignore: cast_nullable_to_non_nullable
as UuidValue?,commitId: freezed == commitId ? _self.commitId : commitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,graphHashPre: freezed == graphHashPre ? _self.graphHashPre : graphHashPre // ignore: cast_nullable_to_non_nullable
as String?,graphHashPost: freezed == graphHashPost ? _self.graphHashPost : graphHashPost // ignore: cast_nullable_to_non_nullable
as String?,functionCallId: freezed == functionCallId ? _self.functionCallId : functionCallId // ignore: cast_nullable_to_non_nullable
as UuidValue?,functionCallResponseId: freezed == functionCallResponseId ? _self.functionCallResponseId : functionCallResponseId // ignore: cast_nullable_to_non_nullable
as UuidValue?,selectedProcessId: freezed == selectedProcessId ? _self.selectedProcessId : selectedProcessId // ignore: cast_nullable_to_non_nullable
as UuidValue?,selectedThreadId: freezed == selectedThreadId ? _self.selectedThreadId : selectedThreadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,blockers: null == blockers ? _self._blockers : blockers // ignore: cast_nullable_to_non_nullable
as List<String>,evidence: null == evidence ? _self._evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}

// dart format on
