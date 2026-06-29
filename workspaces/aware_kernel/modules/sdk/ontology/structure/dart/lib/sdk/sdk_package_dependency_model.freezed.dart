// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'sdk_package_dependency_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$SdkPackageDependency {

@UuidValueConverter() UuidValue get id; SdkPackage? get targetSdkPackage; ObjectInstanceGraphCommit? get targetSdkPackageObjectInstanceGraphCommit; String get targetPackageName; int? get targetVersionNumber; String? get expectedHashSha256; String? get description;@UuidValueConverter() UuidValue get sdkPackageId;@UuidValueConverter() UuidValue? get targetSdkPackageId;@UuidValueConverter() UuidValue? get targetSdkPackageObjectInstanceGraphCommitId;
/// Create a copy of SdkPackageDependency
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$SdkPackageDependencyCopyWith<SdkPackageDependency> get copyWith => _$SdkPackageDependencyCopyWithImpl<SdkPackageDependency>(this as SdkPackageDependency, _$identity);

  /// Serializes this SdkPackageDependency to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is SdkPackageDependency&&(identical(other.id, id) || other.id == id)&&(identical(other.targetSdkPackage, targetSdkPackage) || other.targetSdkPackage == targetSdkPackage)&&(identical(other.targetSdkPackageObjectInstanceGraphCommit, targetSdkPackageObjectInstanceGraphCommit) || other.targetSdkPackageObjectInstanceGraphCommit == targetSdkPackageObjectInstanceGraphCommit)&&(identical(other.targetPackageName, targetPackageName) || other.targetPackageName == targetPackageName)&&(identical(other.targetVersionNumber, targetVersionNumber) || other.targetVersionNumber == targetVersionNumber)&&(identical(other.expectedHashSha256, expectedHashSha256) || other.expectedHashSha256 == expectedHashSha256)&&(identical(other.description, description) || other.description == description)&&(identical(other.sdkPackageId, sdkPackageId) || other.sdkPackageId == sdkPackageId)&&(identical(other.targetSdkPackageId, targetSdkPackageId) || other.targetSdkPackageId == targetSdkPackageId)&&(identical(other.targetSdkPackageObjectInstanceGraphCommitId, targetSdkPackageObjectInstanceGraphCommitId) || other.targetSdkPackageObjectInstanceGraphCommitId == targetSdkPackageObjectInstanceGraphCommitId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,targetSdkPackage,targetSdkPackageObjectInstanceGraphCommit,targetPackageName,targetVersionNumber,expectedHashSha256,description,sdkPackageId,targetSdkPackageId,targetSdkPackageObjectInstanceGraphCommitId);

@override
String toString() {
  return 'SdkPackageDependency(id: $id, targetSdkPackage: $targetSdkPackage, targetSdkPackageObjectInstanceGraphCommit: $targetSdkPackageObjectInstanceGraphCommit, targetPackageName: $targetPackageName, targetVersionNumber: $targetVersionNumber, expectedHashSha256: $expectedHashSha256, description: $description, sdkPackageId: $sdkPackageId, targetSdkPackageId: $targetSdkPackageId, targetSdkPackageObjectInstanceGraphCommitId: $targetSdkPackageObjectInstanceGraphCommitId)';
}


}

/// @nodoc
abstract mixin class $SdkPackageDependencyCopyWith<$Res>  {
  factory $SdkPackageDependencyCopyWith(SdkPackageDependency value, $Res Function(SdkPackageDependency) _then) = _$SdkPackageDependencyCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue id, SdkPackage? targetSdkPackage, ObjectInstanceGraphCommit? targetSdkPackageObjectInstanceGraphCommit, String targetPackageName, int? targetVersionNumber, String? expectedHashSha256, String? description,@UuidValueConverter() UuidValue sdkPackageId,@UuidValueConverter() UuidValue? targetSdkPackageId,@UuidValueConverter() UuidValue? targetSdkPackageObjectInstanceGraphCommitId
});


$SdkPackageCopyWith<$Res>? get targetSdkPackage;$ObjectInstanceGraphCommitCopyWith<$Res>? get targetSdkPackageObjectInstanceGraphCommit;

}
/// @nodoc
class _$SdkPackageDependencyCopyWithImpl<$Res>
    implements $SdkPackageDependencyCopyWith<$Res> {
  _$SdkPackageDependencyCopyWithImpl(this._self, this._then);

  final SdkPackageDependency _self;
  final $Res Function(SdkPackageDependency) _then;

/// Create a copy of SdkPackageDependency
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? id = null,Object? targetSdkPackage = freezed,Object? targetSdkPackageObjectInstanceGraphCommit = freezed,Object? targetPackageName = null,Object? targetVersionNumber = freezed,Object? expectedHashSha256 = freezed,Object? description = freezed,Object? sdkPackageId = null,Object? targetSdkPackageId = freezed,Object? targetSdkPackageObjectInstanceGraphCommitId = freezed,}) {
  return _then(_self.copyWith(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,targetSdkPackage: freezed == targetSdkPackage ? _self.targetSdkPackage : targetSdkPackage // ignore: cast_nullable_to_non_nullable
as SdkPackage?,targetSdkPackageObjectInstanceGraphCommit: freezed == targetSdkPackageObjectInstanceGraphCommit ? _self.targetSdkPackageObjectInstanceGraphCommit : targetSdkPackageObjectInstanceGraphCommit // ignore: cast_nullable_to_non_nullable
as ObjectInstanceGraphCommit?,targetPackageName: null == targetPackageName ? _self.targetPackageName : targetPackageName // ignore: cast_nullable_to_non_nullable
as String,targetVersionNumber: freezed == targetVersionNumber ? _self.targetVersionNumber : targetVersionNumber // ignore: cast_nullable_to_non_nullable
as int?,expectedHashSha256: freezed == expectedHashSha256 ? _self.expectedHashSha256 : expectedHashSha256 // ignore: cast_nullable_to_non_nullable
as String?,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,sdkPackageId: null == sdkPackageId ? _self.sdkPackageId : sdkPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,targetSdkPackageId: freezed == targetSdkPackageId ? _self.targetSdkPackageId : targetSdkPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,targetSdkPackageObjectInstanceGraphCommitId: freezed == targetSdkPackageObjectInstanceGraphCommitId ? _self.targetSdkPackageObjectInstanceGraphCommitId : targetSdkPackageObjectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}
/// Create a copy of SdkPackageDependency
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$SdkPackageCopyWith<$Res>? get targetSdkPackage {
    if (_self.targetSdkPackage == null) {
    return null;
  }

  return $SdkPackageCopyWith<$Res>(_self.targetSdkPackage!, (value) {
    return _then(_self.copyWith(targetSdkPackage: value));
  });
}/// Create a copy of SdkPackageDependency
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ObjectInstanceGraphCommitCopyWith<$Res>? get targetSdkPackageObjectInstanceGraphCommit {
    if (_self.targetSdkPackageObjectInstanceGraphCommit == null) {
    return null;
  }

  return $ObjectInstanceGraphCommitCopyWith<$Res>(_self.targetSdkPackageObjectInstanceGraphCommit!, (value) {
    return _then(_self.copyWith(targetSdkPackageObjectInstanceGraphCommit: value));
  });
}
}


/// Adds pattern-matching-related methods to [SdkPackageDependency].
extension SdkPackageDependencyPatterns on SdkPackageDependency {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _SdkPackageDependency value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _SdkPackageDependency() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _SdkPackageDependency value)  def,}){
final _that = this;
switch (_that) {
case _SdkPackageDependency():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _SdkPackageDependency value)?  def,}){
final _that = this;
switch (_that) {
case _SdkPackageDependency() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue id,  SdkPackage? targetSdkPackage,  ObjectInstanceGraphCommit? targetSdkPackageObjectInstanceGraphCommit,  String targetPackageName,  int? targetVersionNumber,  String? expectedHashSha256,  String? description, @UuidValueConverter()  UuidValue sdkPackageId, @UuidValueConverter()  UuidValue? targetSdkPackageId, @UuidValueConverter()  UuidValue? targetSdkPackageObjectInstanceGraphCommitId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _SdkPackageDependency() when def != null:
return def(_that.id,_that.targetSdkPackage,_that.targetSdkPackageObjectInstanceGraphCommit,_that.targetPackageName,_that.targetVersionNumber,_that.expectedHashSha256,_that.description,_that.sdkPackageId,_that.targetSdkPackageId,_that.targetSdkPackageObjectInstanceGraphCommitId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue id,  SdkPackage? targetSdkPackage,  ObjectInstanceGraphCommit? targetSdkPackageObjectInstanceGraphCommit,  String targetPackageName,  int? targetVersionNumber,  String? expectedHashSha256,  String? description, @UuidValueConverter()  UuidValue sdkPackageId, @UuidValueConverter()  UuidValue? targetSdkPackageId, @UuidValueConverter()  UuidValue? targetSdkPackageObjectInstanceGraphCommitId)  def,}) {final _that = this;
switch (_that) {
case _SdkPackageDependency():
return def(_that.id,_that.targetSdkPackage,_that.targetSdkPackageObjectInstanceGraphCommit,_that.targetPackageName,_that.targetVersionNumber,_that.expectedHashSha256,_that.description,_that.sdkPackageId,_that.targetSdkPackageId,_that.targetSdkPackageObjectInstanceGraphCommitId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue id,  SdkPackage? targetSdkPackage,  ObjectInstanceGraphCommit? targetSdkPackageObjectInstanceGraphCommit,  String targetPackageName,  int? targetVersionNumber,  String? expectedHashSha256,  String? description, @UuidValueConverter()  UuidValue sdkPackageId, @UuidValueConverter()  UuidValue? targetSdkPackageId, @UuidValueConverter()  UuidValue? targetSdkPackageObjectInstanceGraphCommitId)?  def,}) {final _that = this;
switch (_that) {
case _SdkPackageDependency() when def != null:
return def(_that.id,_that.targetSdkPackage,_that.targetSdkPackageObjectInstanceGraphCommit,_that.targetPackageName,_that.targetVersionNumber,_that.expectedHashSha256,_that.description,_that.sdkPackageId,_that.targetSdkPackageId,_that.targetSdkPackageObjectInstanceGraphCommitId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _SdkPackageDependency implements SdkPackageDependency {
   _SdkPackageDependency({@UuidValueConverter() required this.id, this.targetSdkPackage, this.targetSdkPackageObjectInstanceGraphCommit, required this.targetPackageName, this.targetVersionNumber, this.expectedHashSha256, this.description, @UuidValueConverter() required this.sdkPackageId, @UuidValueConverter() this.targetSdkPackageId, @UuidValueConverter() this.targetSdkPackageObjectInstanceGraphCommitId});
  factory _SdkPackageDependency.fromJson(Map<String, dynamic> json) => _$SdkPackageDependencyFromJson(json);

@override@UuidValueConverter() final  UuidValue id;
@override final  SdkPackage? targetSdkPackage;
@override final  ObjectInstanceGraphCommit? targetSdkPackageObjectInstanceGraphCommit;
@override final  String targetPackageName;
@override final  int? targetVersionNumber;
@override final  String? expectedHashSha256;
@override final  String? description;
@override@UuidValueConverter() final  UuidValue sdkPackageId;
@override@UuidValueConverter() final  UuidValue? targetSdkPackageId;
@override@UuidValueConverter() final  UuidValue? targetSdkPackageObjectInstanceGraphCommitId;

/// Create a copy of SdkPackageDependency
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$SdkPackageDependencyCopyWith<_SdkPackageDependency> get copyWith => __$SdkPackageDependencyCopyWithImpl<_SdkPackageDependency>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$SdkPackageDependencyToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _SdkPackageDependency&&(identical(other.id, id) || other.id == id)&&(identical(other.targetSdkPackage, targetSdkPackage) || other.targetSdkPackage == targetSdkPackage)&&(identical(other.targetSdkPackageObjectInstanceGraphCommit, targetSdkPackageObjectInstanceGraphCommit) || other.targetSdkPackageObjectInstanceGraphCommit == targetSdkPackageObjectInstanceGraphCommit)&&(identical(other.targetPackageName, targetPackageName) || other.targetPackageName == targetPackageName)&&(identical(other.targetVersionNumber, targetVersionNumber) || other.targetVersionNumber == targetVersionNumber)&&(identical(other.expectedHashSha256, expectedHashSha256) || other.expectedHashSha256 == expectedHashSha256)&&(identical(other.description, description) || other.description == description)&&(identical(other.sdkPackageId, sdkPackageId) || other.sdkPackageId == sdkPackageId)&&(identical(other.targetSdkPackageId, targetSdkPackageId) || other.targetSdkPackageId == targetSdkPackageId)&&(identical(other.targetSdkPackageObjectInstanceGraphCommitId, targetSdkPackageObjectInstanceGraphCommitId) || other.targetSdkPackageObjectInstanceGraphCommitId == targetSdkPackageObjectInstanceGraphCommitId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,targetSdkPackage,targetSdkPackageObjectInstanceGraphCommit,targetPackageName,targetVersionNumber,expectedHashSha256,description,sdkPackageId,targetSdkPackageId,targetSdkPackageObjectInstanceGraphCommitId);

@override
String toString() {
  return 'SdkPackageDependency.def(id: $id, targetSdkPackage: $targetSdkPackage, targetSdkPackageObjectInstanceGraphCommit: $targetSdkPackageObjectInstanceGraphCommit, targetPackageName: $targetPackageName, targetVersionNumber: $targetVersionNumber, expectedHashSha256: $expectedHashSha256, description: $description, sdkPackageId: $sdkPackageId, targetSdkPackageId: $targetSdkPackageId, targetSdkPackageObjectInstanceGraphCommitId: $targetSdkPackageObjectInstanceGraphCommitId)';
}


}

/// @nodoc
abstract mixin class _$SdkPackageDependencyCopyWith<$Res> implements $SdkPackageDependencyCopyWith<$Res> {
  factory _$SdkPackageDependencyCopyWith(_SdkPackageDependency value, $Res Function(_SdkPackageDependency) _then) = __$SdkPackageDependencyCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue id, SdkPackage? targetSdkPackage, ObjectInstanceGraphCommit? targetSdkPackageObjectInstanceGraphCommit, String targetPackageName, int? targetVersionNumber, String? expectedHashSha256, String? description,@UuidValueConverter() UuidValue sdkPackageId,@UuidValueConverter() UuidValue? targetSdkPackageId,@UuidValueConverter() UuidValue? targetSdkPackageObjectInstanceGraphCommitId
});


@override $SdkPackageCopyWith<$Res>? get targetSdkPackage;@override $ObjectInstanceGraphCommitCopyWith<$Res>? get targetSdkPackageObjectInstanceGraphCommit;

}
/// @nodoc
class __$SdkPackageDependencyCopyWithImpl<$Res>
    implements _$SdkPackageDependencyCopyWith<$Res> {
  __$SdkPackageDependencyCopyWithImpl(this._self, this._then);

  final _SdkPackageDependency _self;
  final $Res Function(_SdkPackageDependency) _then;

/// Create a copy of SdkPackageDependency
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? id = null,Object? targetSdkPackage = freezed,Object? targetSdkPackageObjectInstanceGraphCommit = freezed,Object? targetPackageName = null,Object? targetVersionNumber = freezed,Object? expectedHashSha256 = freezed,Object? description = freezed,Object? sdkPackageId = null,Object? targetSdkPackageId = freezed,Object? targetSdkPackageObjectInstanceGraphCommitId = freezed,}) {
  return _then(_SdkPackageDependency(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,targetSdkPackage: freezed == targetSdkPackage ? _self.targetSdkPackage : targetSdkPackage // ignore: cast_nullable_to_non_nullable
as SdkPackage?,targetSdkPackageObjectInstanceGraphCommit: freezed == targetSdkPackageObjectInstanceGraphCommit ? _self.targetSdkPackageObjectInstanceGraphCommit : targetSdkPackageObjectInstanceGraphCommit // ignore: cast_nullable_to_non_nullable
as ObjectInstanceGraphCommit?,targetPackageName: null == targetPackageName ? _self.targetPackageName : targetPackageName // ignore: cast_nullable_to_non_nullable
as String,targetVersionNumber: freezed == targetVersionNumber ? _self.targetVersionNumber : targetVersionNumber // ignore: cast_nullable_to_non_nullable
as int?,expectedHashSha256: freezed == expectedHashSha256 ? _self.expectedHashSha256 : expectedHashSha256 // ignore: cast_nullable_to_non_nullable
as String?,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,sdkPackageId: null == sdkPackageId ? _self.sdkPackageId : sdkPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,targetSdkPackageId: freezed == targetSdkPackageId ? _self.targetSdkPackageId : targetSdkPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,targetSdkPackageObjectInstanceGraphCommitId: freezed == targetSdkPackageObjectInstanceGraphCommitId ? _self.targetSdkPackageObjectInstanceGraphCommitId : targetSdkPackageObjectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

/// Create a copy of SdkPackageDependency
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$SdkPackageCopyWith<$Res>? get targetSdkPackage {
    if (_self.targetSdkPackage == null) {
    return null;
  }

  return $SdkPackageCopyWith<$Res>(_self.targetSdkPackage!, (value) {
    return _then(_self.copyWith(targetSdkPackage: value));
  });
}/// Create a copy of SdkPackageDependency
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ObjectInstanceGraphCommitCopyWith<$Res>? get targetSdkPackageObjectInstanceGraphCommit {
    if (_self.targetSdkPackageObjectInstanceGraphCommit == null) {
    return null;
  }

  return $ObjectInstanceGraphCommitCopyWith<$Res>(_self.targetSdkPackageObjectInstanceGraphCommit!, (value) {
    return _then(_self.copyWith(targetSdkPackageObjectInstanceGraphCommit: value));
  });
}
}

// dart format on
