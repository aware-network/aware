// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'models_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$ExperienceActorConfigRoleEligibility {

@UuidValueConverter() UuidValue get actorConfigRoleConfigId;@UuidValueConverter() UuidValue get roleConfigId; String? get roleConfigName;
/// Create a copy of ExperienceActorConfigRoleEligibility
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ExperienceActorConfigRoleEligibilityCopyWith<ExperienceActorConfigRoleEligibility> get copyWith => _$ExperienceActorConfigRoleEligibilityCopyWithImpl<ExperienceActorConfigRoleEligibility>(this as ExperienceActorConfigRoleEligibility, _$identity);

  /// Serializes this ExperienceActorConfigRoleEligibility to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ExperienceActorConfigRoleEligibility&&(identical(other.actorConfigRoleConfigId, actorConfigRoleConfigId) || other.actorConfigRoleConfigId == actorConfigRoleConfigId)&&(identical(other.roleConfigId, roleConfigId) || other.roleConfigId == roleConfigId)&&(identical(other.roleConfigName, roleConfigName) || other.roleConfigName == roleConfigName));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorConfigRoleConfigId,roleConfigId,roleConfigName);

@override
String toString() {
  return 'ExperienceActorConfigRoleEligibility(actorConfigRoleConfigId: $actorConfigRoleConfigId, roleConfigId: $roleConfigId, roleConfigName: $roleConfigName)';
}


}

/// @nodoc
abstract mixin class $ExperienceActorConfigRoleEligibilityCopyWith<$Res>  {
  factory $ExperienceActorConfigRoleEligibilityCopyWith(ExperienceActorConfigRoleEligibility value, $Res Function(ExperienceActorConfigRoleEligibility) _then) = _$ExperienceActorConfigRoleEligibilityCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue actorConfigRoleConfigId,@UuidValueConverter() UuidValue roleConfigId, String? roleConfigName
});




}
/// @nodoc
class _$ExperienceActorConfigRoleEligibilityCopyWithImpl<$Res>
    implements $ExperienceActorConfigRoleEligibilityCopyWith<$Res> {
  _$ExperienceActorConfigRoleEligibilityCopyWithImpl(this._self, this._then);

  final ExperienceActorConfigRoleEligibility _self;
  final $Res Function(ExperienceActorConfigRoleEligibility) _then;

/// Create a copy of ExperienceActorConfigRoleEligibility
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorConfigRoleConfigId = null,Object? roleConfigId = null,Object? roleConfigName = freezed,}) {
  return _then(_self.copyWith(
actorConfigRoleConfigId: null == actorConfigRoleConfigId ? _self.actorConfigRoleConfigId : actorConfigRoleConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,roleConfigId: null == roleConfigId ? _self.roleConfigId : roleConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,roleConfigName: freezed == roleConfigName ? _self.roleConfigName : roleConfigName // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [ExperienceActorConfigRoleEligibility].
extension ExperienceActorConfigRoleEligibilityPatterns on ExperienceActorConfigRoleEligibility {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ExperienceActorConfigRoleEligibility value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ExperienceActorConfigRoleEligibility() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ExperienceActorConfigRoleEligibility value)  def,}){
final _that = this;
switch (_that) {
case _ExperienceActorConfigRoleEligibility():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ExperienceActorConfigRoleEligibility value)?  def,}){
final _that = this;
switch (_that) {
case _ExperienceActorConfigRoleEligibility() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue actorConfigRoleConfigId, @UuidValueConverter()  UuidValue roleConfigId,  String? roleConfigName)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ExperienceActorConfigRoleEligibility() when def != null:
return def(_that.actorConfigRoleConfigId,_that.roleConfigId,_that.roleConfigName);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue actorConfigRoleConfigId, @UuidValueConverter()  UuidValue roleConfigId,  String? roleConfigName)  def,}) {final _that = this;
switch (_that) {
case _ExperienceActorConfigRoleEligibility():
return def(_that.actorConfigRoleConfigId,_that.roleConfigId,_that.roleConfigName);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue actorConfigRoleConfigId, @UuidValueConverter()  UuidValue roleConfigId,  String? roleConfigName)?  def,}) {final _that = this;
switch (_that) {
case _ExperienceActorConfigRoleEligibility() when def != null:
return def(_that.actorConfigRoleConfigId,_that.roleConfigId,_that.roleConfigName);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ExperienceActorConfigRoleEligibility implements ExperienceActorConfigRoleEligibility {
   _ExperienceActorConfigRoleEligibility({@UuidValueConverter() required this.actorConfigRoleConfigId, @UuidValueConverter() required this.roleConfigId, this.roleConfigName});
  factory _ExperienceActorConfigRoleEligibility.fromJson(Map<String, dynamic> json) => _$ExperienceActorConfigRoleEligibilityFromJson(json);

@override@UuidValueConverter() final  UuidValue actorConfigRoleConfigId;
@override@UuidValueConverter() final  UuidValue roleConfigId;
@override final  String? roleConfigName;

/// Create a copy of ExperienceActorConfigRoleEligibility
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ExperienceActorConfigRoleEligibilityCopyWith<_ExperienceActorConfigRoleEligibility> get copyWith => __$ExperienceActorConfigRoleEligibilityCopyWithImpl<_ExperienceActorConfigRoleEligibility>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ExperienceActorConfigRoleEligibilityToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ExperienceActorConfigRoleEligibility&&(identical(other.actorConfigRoleConfigId, actorConfigRoleConfigId) || other.actorConfigRoleConfigId == actorConfigRoleConfigId)&&(identical(other.roleConfigId, roleConfigId) || other.roleConfigId == roleConfigId)&&(identical(other.roleConfigName, roleConfigName) || other.roleConfigName == roleConfigName));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorConfigRoleConfigId,roleConfigId,roleConfigName);

@override
String toString() {
  return 'ExperienceActorConfigRoleEligibility.def(actorConfigRoleConfigId: $actorConfigRoleConfigId, roleConfigId: $roleConfigId, roleConfigName: $roleConfigName)';
}


}

/// @nodoc
abstract mixin class _$ExperienceActorConfigRoleEligibilityCopyWith<$Res> implements $ExperienceActorConfigRoleEligibilityCopyWith<$Res> {
  factory _$ExperienceActorConfigRoleEligibilityCopyWith(_ExperienceActorConfigRoleEligibility value, $Res Function(_ExperienceActorConfigRoleEligibility) _then) = __$ExperienceActorConfigRoleEligibilityCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue actorConfigRoleConfigId,@UuidValueConverter() UuidValue roleConfigId, String? roleConfigName
});




}
/// @nodoc
class __$ExperienceActorConfigRoleEligibilityCopyWithImpl<$Res>
    implements _$ExperienceActorConfigRoleEligibilityCopyWith<$Res> {
  __$ExperienceActorConfigRoleEligibilityCopyWithImpl(this._self, this._then);

  final _ExperienceActorConfigRoleEligibility _self;
  final $Res Function(_ExperienceActorConfigRoleEligibility) _then;

/// Create a copy of ExperienceActorConfigRoleEligibility
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorConfigRoleConfigId = null,Object? roleConfigId = null,Object? roleConfigName = freezed,}) {
  return _then(_ExperienceActorConfigRoleEligibility(
actorConfigRoleConfigId: null == actorConfigRoleConfigId ? _self.actorConfigRoleConfigId : actorConfigRoleConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,roleConfigId: null == roleConfigId ? _self.roleConfigId : roleConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,roleConfigName: freezed == roleConfigName ? _self.roleConfigName : roleConfigName // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$ExperienceActorConfigRoleAdmissionBinding {

@UuidValueConverter() UuidValue get actorConfigRoleConfigId;@UuidValueConverter() UuidValue get roleConfigId; String? get roleConfigName;@UuidValueConverter() UuidValue get actorId;@UuidValueConverter() UuidValue get roleId;@UuidValueConverter() UuidValue get actorRoleId;@UuidValueConverter() UuidValue get roleClassInstanceId;@UuidValueConverter() UuidValue get classInstanceIdentityId;@UuidValueConverter() UuidValue get roleConfigClassConfigId;@UuidValueConverter() UuidValue get objectInstanceGraphIdentityId; String get objectInstanceGraphBranchKey;@UuidValueConverter() UuidValue? get objectInstanceGraphBranchId;
/// Create a copy of ExperienceActorConfigRoleAdmissionBinding
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ExperienceActorConfigRoleAdmissionBindingCopyWith<ExperienceActorConfigRoleAdmissionBinding> get copyWith => _$ExperienceActorConfigRoleAdmissionBindingCopyWithImpl<ExperienceActorConfigRoleAdmissionBinding>(this as ExperienceActorConfigRoleAdmissionBinding, _$identity);

  /// Serializes this ExperienceActorConfigRoleAdmissionBinding to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ExperienceActorConfigRoleAdmissionBinding&&(identical(other.actorConfigRoleConfigId, actorConfigRoleConfigId) || other.actorConfigRoleConfigId == actorConfigRoleConfigId)&&(identical(other.roleConfigId, roleConfigId) || other.roleConfigId == roleConfigId)&&(identical(other.roleConfigName, roleConfigName) || other.roleConfigName == roleConfigName)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.roleId, roleId) || other.roleId == roleId)&&(identical(other.actorRoleId, actorRoleId) || other.actorRoleId == actorRoleId)&&(identical(other.roleClassInstanceId, roleClassInstanceId) || other.roleClassInstanceId == roleClassInstanceId)&&(identical(other.classInstanceIdentityId, classInstanceIdentityId) || other.classInstanceIdentityId == classInstanceIdentityId)&&(identical(other.roleConfigClassConfigId, roleConfigClassConfigId) || other.roleConfigClassConfigId == roleConfigClassConfigId)&&(identical(other.objectInstanceGraphIdentityId, objectInstanceGraphIdentityId) || other.objectInstanceGraphIdentityId == objectInstanceGraphIdentityId)&&(identical(other.objectInstanceGraphBranchKey, objectInstanceGraphBranchKey) || other.objectInstanceGraphBranchKey == objectInstanceGraphBranchKey)&&(identical(other.objectInstanceGraphBranchId, objectInstanceGraphBranchId) || other.objectInstanceGraphBranchId == objectInstanceGraphBranchId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorConfigRoleConfigId,roleConfigId,roleConfigName,actorId,roleId,actorRoleId,roleClassInstanceId,classInstanceIdentityId,roleConfigClassConfigId,objectInstanceGraphIdentityId,objectInstanceGraphBranchKey,objectInstanceGraphBranchId);

@override
String toString() {
  return 'ExperienceActorConfigRoleAdmissionBinding(actorConfigRoleConfigId: $actorConfigRoleConfigId, roleConfigId: $roleConfigId, roleConfigName: $roleConfigName, actorId: $actorId, roleId: $roleId, actorRoleId: $actorRoleId, roleClassInstanceId: $roleClassInstanceId, classInstanceIdentityId: $classInstanceIdentityId, roleConfigClassConfigId: $roleConfigClassConfigId, objectInstanceGraphIdentityId: $objectInstanceGraphIdentityId, objectInstanceGraphBranchKey: $objectInstanceGraphBranchKey, objectInstanceGraphBranchId: $objectInstanceGraphBranchId)';
}


}

/// @nodoc
abstract mixin class $ExperienceActorConfigRoleAdmissionBindingCopyWith<$Res>  {
  factory $ExperienceActorConfigRoleAdmissionBindingCopyWith(ExperienceActorConfigRoleAdmissionBinding value, $Res Function(ExperienceActorConfigRoleAdmissionBinding) _then) = _$ExperienceActorConfigRoleAdmissionBindingCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue actorConfigRoleConfigId,@UuidValueConverter() UuidValue roleConfigId, String? roleConfigName,@UuidValueConverter() UuidValue actorId,@UuidValueConverter() UuidValue roleId,@UuidValueConverter() UuidValue actorRoleId,@UuidValueConverter() UuidValue roleClassInstanceId,@UuidValueConverter() UuidValue classInstanceIdentityId,@UuidValueConverter() UuidValue roleConfigClassConfigId,@UuidValueConverter() UuidValue objectInstanceGraphIdentityId, String objectInstanceGraphBranchKey,@UuidValueConverter() UuidValue? objectInstanceGraphBranchId
});




}
/// @nodoc
class _$ExperienceActorConfigRoleAdmissionBindingCopyWithImpl<$Res>
    implements $ExperienceActorConfigRoleAdmissionBindingCopyWith<$Res> {
  _$ExperienceActorConfigRoleAdmissionBindingCopyWithImpl(this._self, this._then);

  final ExperienceActorConfigRoleAdmissionBinding _self;
  final $Res Function(ExperienceActorConfigRoleAdmissionBinding) _then;

/// Create a copy of ExperienceActorConfigRoleAdmissionBinding
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorConfigRoleConfigId = null,Object? roleConfigId = null,Object? roleConfigName = freezed,Object? actorId = null,Object? roleId = null,Object? actorRoleId = null,Object? roleClassInstanceId = null,Object? classInstanceIdentityId = null,Object? roleConfigClassConfigId = null,Object? objectInstanceGraphIdentityId = null,Object? objectInstanceGraphBranchKey = null,Object? objectInstanceGraphBranchId = freezed,}) {
  return _then(_self.copyWith(
actorConfigRoleConfigId: null == actorConfigRoleConfigId ? _self.actorConfigRoleConfigId : actorConfigRoleConfigId // ignore: cast_nullable_to_non_nullable
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


/// Adds pattern-matching-related methods to [ExperienceActorConfigRoleAdmissionBinding].
extension ExperienceActorConfigRoleAdmissionBindingPatterns on ExperienceActorConfigRoleAdmissionBinding {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ExperienceActorConfigRoleAdmissionBinding value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ExperienceActorConfigRoleAdmissionBinding() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ExperienceActorConfigRoleAdmissionBinding value)  def,}){
final _that = this;
switch (_that) {
case _ExperienceActorConfigRoleAdmissionBinding():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ExperienceActorConfigRoleAdmissionBinding value)?  def,}){
final _that = this;
switch (_that) {
case _ExperienceActorConfigRoleAdmissionBinding() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue actorConfigRoleConfigId, @UuidValueConverter()  UuidValue roleConfigId,  String? roleConfigName, @UuidValueConverter()  UuidValue actorId, @UuidValueConverter()  UuidValue roleId, @UuidValueConverter()  UuidValue actorRoleId, @UuidValueConverter()  UuidValue roleClassInstanceId, @UuidValueConverter()  UuidValue classInstanceIdentityId, @UuidValueConverter()  UuidValue roleConfigClassConfigId, @UuidValueConverter()  UuidValue objectInstanceGraphIdentityId,  String objectInstanceGraphBranchKey, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ExperienceActorConfigRoleAdmissionBinding() when def != null:
return def(_that.actorConfigRoleConfigId,_that.roleConfigId,_that.roleConfigName,_that.actorId,_that.roleId,_that.actorRoleId,_that.roleClassInstanceId,_that.classInstanceIdentityId,_that.roleConfigClassConfigId,_that.objectInstanceGraphIdentityId,_that.objectInstanceGraphBranchKey,_that.objectInstanceGraphBranchId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue actorConfigRoleConfigId, @UuidValueConverter()  UuidValue roleConfigId,  String? roleConfigName, @UuidValueConverter()  UuidValue actorId, @UuidValueConverter()  UuidValue roleId, @UuidValueConverter()  UuidValue actorRoleId, @UuidValueConverter()  UuidValue roleClassInstanceId, @UuidValueConverter()  UuidValue classInstanceIdentityId, @UuidValueConverter()  UuidValue roleConfigClassConfigId, @UuidValueConverter()  UuidValue objectInstanceGraphIdentityId,  String objectInstanceGraphBranchKey, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId)  def,}) {final _that = this;
switch (_that) {
case _ExperienceActorConfigRoleAdmissionBinding():
return def(_that.actorConfigRoleConfigId,_that.roleConfigId,_that.roleConfigName,_that.actorId,_that.roleId,_that.actorRoleId,_that.roleClassInstanceId,_that.classInstanceIdentityId,_that.roleConfigClassConfigId,_that.objectInstanceGraphIdentityId,_that.objectInstanceGraphBranchKey,_that.objectInstanceGraphBranchId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue actorConfigRoleConfigId, @UuidValueConverter()  UuidValue roleConfigId,  String? roleConfigName, @UuidValueConverter()  UuidValue actorId, @UuidValueConverter()  UuidValue roleId, @UuidValueConverter()  UuidValue actorRoleId, @UuidValueConverter()  UuidValue roleClassInstanceId, @UuidValueConverter()  UuidValue classInstanceIdentityId, @UuidValueConverter()  UuidValue roleConfigClassConfigId, @UuidValueConverter()  UuidValue objectInstanceGraphIdentityId,  String objectInstanceGraphBranchKey, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId)?  def,}) {final _that = this;
switch (_that) {
case _ExperienceActorConfigRoleAdmissionBinding() when def != null:
return def(_that.actorConfigRoleConfigId,_that.roleConfigId,_that.roleConfigName,_that.actorId,_that.roleId,_that.actorRoleId,_that.roleClassInstanceId,_that.classInstanceIdentityId,_that.roleConfigClassConfigId,_that.objectInstanceGraphIdentityId,_that.objectInstanceGraphBranchKey,_that.objectInstanceGraphBranchId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ExperienceActorConfigRoleAdmissionBinding implements ExperienceActorConfigRoleAdmissionBinding {
   _ExperienceActorConfigRoleAdmissionBinding({@UuidValueConverter() required this.actorConfigRoleConfigId, @UuidValueConverter() required this.roleConfigId, this.roleConfigName, @UuidValueConverter() required this.actorId, @UuidValueConverter() required this.roleId, @UuidValueConverter() required this.actorRoleId, @UuidValueConverter() required this.roleClassInstanceId, @UuidValueConverter() required this.classInstanceIdentityId, @UuidValueConverter() required this.roleConfigClassConfigId, @UuidValueConverter() required this.objectInstanceGraphIdentityId, required this.objectInstanceGraphBranchKey, @UuidValueConverter() this.objectInstanceGraphBranchId});
  factory _ExperienceActorConfigRoleAdmissionBinding.fromJson(Map<String, dynamic> json) => _$ExperienceActorConfigRoleAdmissionBindingFromJson(json);

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

/// Create a copy of ExperienceActorConfigRoleAdmissionBinding
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ExperienceActorConfigRoleAdmissionBindingCopyWith<_ExperienceActorConfigRoleAdmissionBinding> get copyWith => __$ExperienceActorConfigRoleAdmissionBindingCopyWithImpl<_ExperienceActorConfigRoleAdmissionBinding>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ExperienceActorConfigRoleAdmissionBindingToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ExperienceActorConfigRoleAdmissionBinding&&(identical(other.actorConfigRoleConfigId, actorConfigRoleConfigId) || other.actorConfigRoleConfigId == actorConfigRoleConfigId)&&(identical(other.roleConfigId, roleConfigId) || other.roleConfigId == roleConfigId)&&(identical(other.roleConfigName, roleConfigName) || other.roleConfigName == roleConfigName)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.roleId, roleId) || other.roleId == roleId)&&(identical(other.actorRoleId, actorRoleId) || other.actorRoleId == actorRoleId)&&(identical(other.roleClassInstanceId, roleClassInstanceId) || other.roleClassInstanceId == roleClassInstanceId)&&(identical(other.classInstanceIdentityId, classInstanceIdentityId) || other.classInstanceIdentityId == classInstanceIdentityId)&&(identical(other.roleConfigClassConfigId, roleConfigClassConfigId) || other.roleConfigClassConfigId == roleConfigClassConfigId)&&(identical(other.objectInstanceGraphIdentityId, objectInstanceGraphIdentityId) || other.objectInstanceGraphIdentityId == objectInstanceGraphIdentityId)&&(identical(other.objectInstanceGraphBranchKey, objectInstanceGraphBranchKey) || other.objectInstanceGraphBranchKey == objectInstanceGraphBranchKey)&&(identical(other.objectInstanceGraphBranchId, objectInstanceGraphBranchId) || other.objectInstanceGraphBranchId == objectInstanceGraphBranchId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorConfigRoleConfigId,roleConfigId,roleConfigName,actorId,roleId,actorRoleId,roleClassInstanceId,classInstanceIdentityId,roleConfigClassConfigId,objectInstanceGraphIdentityId,objectInstanceGraphBranchKey,objectInstanceGraphBranchId);

@override
String toString() {
  return 'ExperienceActorConfigRoleAdmissionBinding.def(actorConfigRoleConfigId: $actorConfigRoleConfigId, roleConfigId: $roleConfigId, roleConfigName: $roleConfigName, actorId: $actorId, roleId: $roleId, actorRoleId: $actorRoleId, roleClassInstanceId: $roleClassInstanceId, classInstanceIdentityId: $classInstanceIdentityId, roleConfigClassConfigId: $roleConfigClassConfigId, objectInstanceGraphIdentityId: $objectInstanceGraphIdentityId, objectInstanceGraphBranchKey: $objectInstanceGraphBranchKey, objectInstanceGraphBranchId: $objectInstanceGraphBranchId)';
}


}

/// @nodoc
abstract mixin class _$ExperienceActorConfigRoleAdmissionBindingCopyWith<$Res> implements $ExperienceActorConfigRoleAdmissionBindingCopyWith<$Res> {
  factory _$ExperienceActorConfigRoleAdmissionBindingCopyWith(_ExperienceActorConfigRoleAdmissionBinding value, $Res Function(_ExperienceActorConfigRoleAdmissionBinding) _then) = __$ExperienceActorConfigRoleAdmissionBindingCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue actorConfigRoleConfigId,@UuidValueConverter() UuidValue roleConfigId, String? roleConfigName,@UuidValueConverter() UuidValue actorId,@UuidValueConverter() UuidValue roleId,@UuidValueConverter() UuidValue actorRoleId,@UuidValueConverter() UuidValue roleClassInstanceId,@UuidValueConverter() UuidValue classInstanceIdentityId,@UuidValueConverter() UuidValue roleConfigClassConfigId,@UuidValueConverter() UuidValue objectInstanceGraphIdentityId, String objectInstanceGraphBranchKey,@UuidValueConverter() UuidValue? objectInstanceGraphBranchId
});




}
/// @nodoc
class __$ExperienceActorConfigRoleAdmissionBindingCopyWithImpl<$Res>
    implements _$ExperienceActorConfigRoleAdmissionBindingCopyWith<$Res> {
  __$ExperienceActorConfigRoleAdmissionBindingCopyWithImpl(this._self, this._then);

  final _ExperienceActorConfigRoleAdmissionBinding _self;
  final $Res Function(_ExperienceActorConfigRoleAdmissionBinding) _then;

/// Create a copy of ExperienceActorConfigRoleAdmissionBinding
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorConfigRoleConfigId = null,Object? roleConfigId = null,Object? roleConfigName = freezed,Object? actorId = null,Object? roleId = null,Object? actorRoleId = null,Object? roleClassInstanceId = null,Object? classInstanceIdentityId = null,Object? roleConfigClassConfigId = null,Object? objectInstanceGraphIdentityId = null,Object? objectInstanceGraphBranchKey = null,Object? objectInstanceGraphBranchId = freezed,}) {
  return _then(_ExperienceActorConfigRoleAdmissionBinding(
actorConfigRoleConfigId: null == actorConfigRoleConfigId ? _self.actorConfigRoleConfigId : actorConfigRoleConfigId // ignore: cast_nullable_to_non_nullable
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
mixin _$ExperienceActorConfigAdmissionReceipt {

 bool get accepted; String get status; String? get reason; String get experienceName;@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue? get actorConfigId;@UuidValueConverter() UuidValue? get classInstanceIdentityId; String get objectInstanceGraphBranchKey;@UuidValueConverter() UuidValue? get objectInstanceGraphBranchId;@UuidValueListConverter() List<UuidValue> get requestedRoleConfigIds; List<String> get requestedRoleConfigNames; List<ExperienceActorConfigRoleEligibility> get eligibleRoles; List<ExperienceActorConfigRoleAdmissionBinding> get bindings; List<String> get blockers; Map<String, dynamic> get evidence;
/// Create a copy of ExperienceActorConfigAdmissionReceipt
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ExperienceActorConfigAdmissionReceiptCopyWith<ExperienceActorConfigAdmissionReceipt> get copyWith => _$ExperienceActorConfigAdmissionReceiptCopyWithImpl<ExperienceActorConfigAdmissionReceipt>(this as ExperienceActorConfigAdmissionReceipt, _$identity);

  /// Serializes this ExperienceActorConfigAdmissionReceipt to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ExperienceActorConfigAdmissionReceipt&&(identical(other.accepted, accepted) || other.accepted == accepted)&&(identical(other.status, status) || other.status == status)&&(identical(other.reason, reason) || other.reason == reason)&&(identical(other.experienceName, experienceName) || other.experienceName == experienceName)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.actorConfigId, actorConfigId) || other.actorConfigId == actorConfigId)&&(identical(other.classInstanceIdentityId, classInstanceIdentityId) || other.classInstanceIdentityId == classInstanceIdentityId)&&(identical(other.objectInstanceGraphBranchKey, objectInstanceGraphBranchKey) || other.objectInstanceGraphBranchKey == objectInstanceGraphBranchKey)&&(identical(other.objectInstanceGraphBranchId, objectInstanceGraphBranchId) || other.objectInstanceGraphBranchId == objectInstanceGraphBranchId)&&const DeepCollectionEquality().equals(other.requestedRoleConfigIds, requestedRoleConfigIds)&&const DeepCollectionEquality().equals(other.requestedRoleConfigNames, requestedRoleConfigNames)&&const DeepCollectionEquality().equals(other.eligibleRoles, eligibleRoles)&&const DeepCollectionEquality().equals(other.bindings, bindings)&&const DeepCollectionEquality().equals(other.blockers, blockers)&&const DeepCollectionEquality().equals(other.evidence, evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,accepted,status,reason,experienceName,actorId,actorConfigId,classInstanceIdentityId,objectInstanceGraphBranchKey,objectInstanceGraphBranchId,const DeepCollectionEquality().hash(requestedRoleConfigIds),const DeepCollectionEquality().hash(requestedRoleConfigNames),const DeepCollectionEquality().hash(eligibleRoles),const DeepCollectionEquality().hash(bindings),const DeepCollectionEquality().hash(blockers),const DeepCollectionEquality().hash(evidence));

@override
String toString() {
  return 'ExperienceActorConfigAdmissionReceipt(accepted: $accepted, status: $status, reason: $reason, experienceName: $experienceName, actorId: $actorId, actorConfigId: $actorConfigId, classInstanceIdentityId: $classInstanceIdentityId, objectInstanceGraphBranchKey: $objectInstanceGraphBranchKey, objectInstanceGraphBranchId: $objectInstanceGraphBranchId, requestedRoleConfigIds: $requestedRoleConfigIds, requestedRoleConfigNames: $requestedRoleConfigNames, eligibleRoles: $eligibleRoles, bindings: $bindings, blockers: $blockers, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class $ExperienceActorConfigAdmissionReceiptCopyWith<$Res>  {
  factory $ExperienceActorConfigAdmissionReceiptCopyWith(ExperienceActorConfigAdmissionReceipt value, $Res Function(ExperienceActorConfigAdmissionReceipt) _then) = _$ExperienceActorConfigAdmissionReceiptCopyWithImpl;
@useResult
$Res call({
 bool accepted, String status, String? reason, String experienceName,@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? actorConfigId,@UuidValueConverter() UuidValue? classInstanceIdentityId, String objectInstanceGraphBranchKey,@UuidValueConverter() UuidValue? objectInstanceGraphBranchId,@UuidValueListConverter() List<UuidValue> requestedRoleConfigIds, List<String> requestedRoleConfigNames, List<ExperienceActorConfigRoleEligibility> eligibleRoles, List<ExperienceActorConfigRoleAdmissionBinding> bindings, List<String> blockers, Map<String, dynamic> evidence
});




}
/// @nodoc
class _$ExperienceActorConfigAdmissionReceiptCopyWithImpl<$Res>
    implements $ExperienceActorConfigAdmissionReceiptCopyWith<$Res> {
  _$ExperienceActorConfigAdmissionReceiptCopyWithImpl(this._self, this._then);

  final ExperienceActorConfigAdmissionReceipt _self;
  final $Res Function(ExperienceActorConfigAdmissionReceipt) _then;

/// Create a copy of ExperienceActorConfigAdmissionReceipt
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? accepted = null,Object? status = null,Object? reason = freezed,Object? experienceName = null,Object? actorId = freezed,Object? actorConfigId = freezed,Object? classInstanceIdentityId = freezed,Object? objectInstanceGraphBranchKey = null,Object? objectInstanceGraphBranchId = freezed,Object? requestedRoleConfigIds = null,Object? requestedRoleConfigNames = null,Object? eligibleRoles = null,Object? bindings = null,Object? blockers = null,Object? evidence = null,}) {
  return _then(_self.copyWith(
accepted: null == accepted ? _self.accepted : accepted // ignore: cast_nullable_to_non_nullable
as bool,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,reason: freezed == reason ? _self.reason : reason // ignore: cast_nullable_to_non_nullable
as String?,experienceName: null == experienceName ? _self.experienceName : experienceName // ignore: cast_nullable_to_non_nullable
as String,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,actorConfigId: freezed == actorConfigId ? _self.actorConfigId : actorConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,classInstanceIdentityId: freezed == classInstanceIdentityId ? _self.classInstanceIdentityId : classInstanceIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphBranchKey: null == objectInstanceGraphBranchKey ? _self.objectInstanceGraphBranchKey : objectInstanceGraphBranchKey // ignore: cast_nullable_to_non_nullable
as String,objectInstanceGraphBranchId: freezed == objectInstanceGraphBranchId ? _self.objectInstanceGraphBranchId : objectInstanceGraphBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestedRoleConfigIds: null == requestedRoleConfigIds ? _self.requestedRoleConfigIds : requestedRoleConfigIds // ignore: cast_nullable_to_non_nullable
as List<UuidValue>,requestedRoleConfigNames: null == requestedRoleConfigNames ? _self.requestedRoleConfigNames : requestedRoleConfigNames // ignore: cast_nullable_to_non_nullable
as List<String>,eligibleRoles: null == eligibleRoles ? _self.eligibleRoles : eligibleRoles // ignore: cast_nullable_to_non_nullable
as List<ExperienceActorConfigRoleEligibility>,bindings: null == bindings ? _self.bindings : bindings // ignore: cast_nullable_to_non_nullable
as List<ExperienceActorConfigRoleAdmissionBinding>,blockers: null == blockers ? _self.blockers : blockers // ignore: cast_nullable_to_non_nullable
as List<String>,evidence: null == evidence ? _self.evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [ExperienceActorConfigAdmissionReceipt].
extension ExperienceActorConfigAdmissionReceiptPatterns on ExperienceActorConfigAdmissionReceipt {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ExperienceActorConfigAdmissionReceipt value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ExperienceActorConfigAdmissionReceipt() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ExperienceActorConfigAdmissionReceipt value)  def,}){
final _that = this;
switch (_that) {
case _ExperienceActorConfigAdmissionReceipt():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ExperienceActorConfigAdmissionReceipt value)?  def,}){
final _that = this;
switch (_that) {
case _ExperienceActorConfigAdmissionReceipt() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( bool accepted,  String status,  String? reason,  String experienceName, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? actorConfigId, @UuidValueConverter()  UuidValue? classInstanceIdentityId,  String objectInstanceGraphBranchKey, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId, @UuidValueListConverter()  List<UuidValue> requestedRoleConfigIds,  List<String> requestedRoleConfigNames,  List<ExperienceActorConfigRoleEligibility> eligibleRoles,  List<ExperienceActorConfigRoleAdmissionBinding> bindings,  List<String> blockers,  Map<String, dynamic> evidence)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ExperienceActorConfigAdmissionReceipt() when def != null:
return def(_that.accepted,_that.status,_that.reason,_that.experienceName,_that.actorId,_that.actorConfigId,_that.classInstanceIdentityId,_that.objectInstanceGraphBranchKey,_that.objectInstanceGraphBranchId,_that.requestedRoleConfigIds,_that.requestedRoleConfigNames,_that.eligibleRoles,_that.bindings,_that.blockers,_that.evidence);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( bool accepted,  String status,  String? reason,  String experienceName, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? actorConfigId, @UuidValueConverter()  UuidValue? classInstanceIdentityId,  String objectInstanceGraphBranchKey, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId, @UuidValueListConverter()  List<UuidValue> requestedRoleConfigIds,  List<String> requestedRoleConfigNames,  List<ExperienceActorConfigRoleEligibility> eligibleRoles,  List<ExperienceActorConfigRoleAdmissionBinding> bindings,  List<String> blockers,  Map<String, dynamic> evidence)  def,}) {final _that = this;
switch (_that) {
case _ExperienceActorConfigAdmissionReceipt():
return def(_that.accepted,_that.status,_that.reason,_that.experienceName,_that.actorId,_that.actorConfigId,_that.classInstanceIdentityId,_that.objectInstanceGraphBranchKey,_that.objectInstanceGraphBranchId,_that.requestedRoleConfigIds,_that.requestedRoleConfigNames,_that.eligibleRoles,_that.bindings,_that.blockers,_that.evidence);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( bool accepted,  String status,  String? reason,  String experienceName, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? actorConfigId, @UuidValueConverter()  UuidValue? classInstanceIdentityId,  String objectInstanceGraphBranchKey, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId, @UuidValueListConverter()  List<UuidValue> requestedRoleConfigIds,  List<String> requestedRoleConfigNames,  List<ExperienceActorConfigRoleEligibility> eligibleRoles,  List<ExperienceActorConfigRoleAdmissionBinding> bindings,  List<String> blockers,  Map<String, dynamic> evidence)?  def,}) {final _that = this;
switch (_that) {
case _ExperienceActorConfigAdmissionReceipt() when def != null:
return def(_that.accepted,_that.status,_that.reason,_that.experienceName,_that.actorId,_that.actorConfigId,_that.classInstanceIdentityId,_that.objectInstanceGraphBranchKey,_that.objectInstanceGraphBranchId,_that.requestedRoleConfigIds,_that.requestedRoleConfigNames,_that.eligibleRoles,_that.bindings,_that.blockers,_that.evidence);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ExperienceActorConfigAdmissionReceipt implements ExperienceActorConfigAdmissionReceipt {
   _ExperienceActorConfigAdmissionReceipt({required this.accepted, required this.status, this.reason, required this.experienceName, @UuidValueConverter() this.actorId, @UuidValueConverter() this.actorConfigId, @UuidValueConverter() this.classInstanceIdentityId, required this.objectInstanceGraphBranchKey, @UuidValueConverter() this.objectInstanceGraphBranchId, @UuidValueListConverter() final  List<UuidValue> requestedRoleConfigIds = const [], final  List<String> requestedRoleConfigNames = const [], final  List<ExperienceActorConfigRoleEligibility> eligibleRoles = const [], final  List<ExperienceActorConfigRoleAdmissionBinding> bindings = const [], final  List<String> blockers = const [], required final  Map<String, dynamic> evidence}): _requestedRoleConfigIds = requestedRoleConfigIds,_requestedRoleConfigNames = requestedRoleConfigNames,_eligibleRoles = eligibleRoles,_bindings = bindings,_blockers = blockers,_evidence = evidence;
  factory _ExperienceActorConfigAdmissionReceipt.fromJson(Map<String, dynamic> json) => _$ExperienceActorConfigAdmissionReceiptFromJson(json);

@override final  bool accepted;
@override final  String status;
@override final  String? reason;
@override final  String experienceName;
@override@UuidValueConverter() final  UuidValue? actorId;
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

 final  List<ExperienceActorConfigRoleEligibility> _eligibleRoles;
@override@JsonKey() List<ExperienceActorConfigRoleEligibility> get eligibleRoles {
  if (_eligibleRoles is EqualUnmodifiableListView) return _eligibleRoles;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_eligibleRoles);
}

 final  List<ExperienceActorConfigRoleAdmissionBinding> _bindings;
@override@JsonKey() List<ExperienceActorConfigRoleAdmissionBinding> get bindings {
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


/// Create a copy of ExperienceActorConfigAdmissionReceipt
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ExperienceActorConfigAdmissionReceiptCopyWith<_ExperienceActorConfigAdmissionReceipt> get copyWith => __$ExperienceActorConfigAdmissionReceiptCopyWithImpl<_ExperienceActorConfigAdmissionReceipt>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ExperienceActorConfigAdmissionReceiptToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ExperienceActorConfigAdmissionReceipt&&(identical(other.accepted, accepted) || other.accepted == accepted)&&(identical(other.status, status) || other.status == status)&&(identical(other.reason, reason) || other.reason == reason)&&(identical(other.experienceName, experienceName) || other.experienceName == experienceName)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.actorConfigId, actorConfigId) || other.actorConfigId == actorConfigId)&&(identical(other.classInstanceIdentityId, classInstanceIdentityId) || other.classInstanceIdentityId == classInstanceIdentityId)&&(identical(other.objectInstanceGraphBranchKey, objectInstanceGraphBranchKey) || other.objectInstanceGraphBranchKey == objectInstanceGraphBranchKey)&&(identical(other.objectInstanceGraphBranchId, objectInstanceGraphBranchId) || other.objectInstanceGraphBranchId == objectInstanceGraphBranchId)&&const DeepCollectionEquality().equals(other._requestedRoleConfigIds, _requestedRoleConfigIds)&&const DeepCollectionEquality().equals(other._requestedRoleConfigNames, _requestedRoleConfigNames)&&const DeepCollectionEquality().equals(other._eligibleRoles, _eligibleRoles)&&const DeepCollectionEquality().equals(other._bindings, _bindings)&&const DeepCollectionEquality().equals(other._blockers, _blockers)&&const DeepCollectionEquality().equals(other._evidence, _evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,accepted,status,reason,experienceName,actorId,actorConfigId,classInstanceIdentityId,objectInstanceGraphBranchKey,objectInstanceGraphBranchId,const DeepCollectionEquality().hash(_requestedRoleConfigIds),const DeepCollectionEquality().hash(_requestedRoleConfigNames),const DeepCollectionEquality().hash(_eligibleRoles),const DeepCollectionEquality().hash(_bindings),const DeepCollectionEquality().hash(_blockers),const DeepCollectionEquality().hash(_evidence));

@override
String toString() {
  return 'ExperienceActorConfigAdmissionReceipt.def(accepted: $accepted, status: $status, reason: $reason, experienceName: $experienceName, actorId: $actorId, actorConfigId: $actorConfigId, classInstanceIdentityId: $classInstanceIdentityId, objectInstanceGraphBranchKey: $objectInstanceGraphBranchKey, objectInstanceGraphBranchId: $objectInstanceGraphBranchId, requestedRoleConfigIds: $requestedRoleConfigIds, requestedRoleConfigNames: $requestedRoleConfigNames, eligibleRoles: $eligibleRoles, bindings: $bindings, blockers: $blockers, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class _$ExperienceActorConfigAdmissionReceiptCopyWith<$Res> implements $ExperienceActorConfigAdmissionReceiptCopyWith<$Res> {
  factory _$ExperienceActorConfigAdmissionReceiptCopyWith(_ExperienceActorConfigAdmissionReceipt value, $Res Function(_ExperienceActorConfigAdmissionReceipt) _then) = __$ExperienceActorConfigAdmissionReceiptCopyWithImpl;
@override @useResult
$Res call({
 bool accepted, String status, String? reason, String experienceName,@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? actorConfigId,@UuidValueConverter() UuidValue? classInstanceIdentityId, String objectInstanceGraphBranchKey,@UuidValueConverter() UuidValue? objectInstanceGraphBranchId,@UuidValueListConverter() List<UuidValue> requestedRoleConfigIds, List<String> requestedRoleConfigNames, List<ExperienceActorConfigRoleEligibility> eligibleRoles, List<ExperienceActorConfigRoleAdmissionBinding> bindings, List<String> blockers, Map<String, dynamic> evidence
});




}
/// @nodoc
class __$ExperienceActorConfigAdmissionReceiptCopyWithImpl<$Res>
    implements _$ExperienceActorConfigAdmissionReceiptCopyWith<$Res> {
  __$ExperienceActorConfigAdmissionReceiptCopyWithImpl(this._self, this._then);

  final _ExperienceActorConfigAdmissionReceipt _self;
  final $Res Function(_ExperienceActorConfigAdmissionReceipt) _then;

/// Create a copy of ExperienceActorConfigAdmissionReceipt
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? accepted = null,Object? status = null,Object? reason = freezed,Object? experienceName = null,Object? actorId = freezed,Object? actorConfigId = freezed,Object? classInstanceIdentityId = freezed,Object? objectInstanceGraphBranchKey = null,Object? objectInstanceGraphBranchId = freezed,Object? requestedRoleConfigIds = null,Object? requestedRoleConfigNames = null,Object? eligibleRoles = null,Object? bindings = null,Object? blockers = null,Object? evidence = null,}) {
  return _then(_ExperienceActorConfigAdmissionReceipt(
accepted: null == accepted ? _self.accepted : accepted // ignore: cast_nullable_to_non_nullable
as bool,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,reason: freezed == reason ? _self.reason : reason // ignore: cast_nullable_to_non_nullable
as String?,experienceName: null == experienceName ? _self.experienceName : experienceName // ignore: cast_nullable_to_non_nullable
as String,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,actorConfigId: freezed == actorConfigId ? _self.actorConfigId : actorConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,classInstanceIdentityId: freezed == classInstanceIdentityId ? _self.classInstanceIdentityId : classInstanceIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphBranchKey: null == objectInstanceGraphBranchKey ? _self.objectInstanceGraphBranchKey : objectInstanceGraphBranchKey // ignore: cast_nullable_to_non_nullable
as String,objectInstanceGraphBranchId: freezed == objectInstanceGraphBranchId ? _self.objectInstanceGraphBranchId : objectInstanceGraphBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestedRoleConfigIds: null == requestedRoleConfigIds ? _self._requestedRoleConfigIds : requestedRoleConfigIds // ignore: cast_nullable_to_non_nullable
as List<UuidValue>,requestedRoleConfigNames: null == requestedRoleConfigNames ? _self._requestedRoleConfigNames : requestedRoleConfigNames // ignore: cast_nullable_to_non_nullable
as List<String>,eligibleRoles: null == eligibleRoles ? _self._eligibleRoles : eligibleRoles // ignore: cast_nullable_to_non_nullable
as List<ExperienceActorConfigRoleEligibility>,bindings: null == bindings ? _self._bindings : bindings // ignore: cast_nullable_to_non_nullable
as List<ExperienceActorConfigRoleAdmissionBinding>,blockers: null == blockers ? _self._blockers : blockers // ignore: cast_nullable_to_non_nullable
as List<String>,evidence: null == evidence ? _self._evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}

// dart format on
