// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'sdk_package_object_config_graph_package_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$SdkPackageObjectConfigGraphPackage {

@UuidValueConverter() UuidValue get id; ObjectConfigGraphPackage? get objectConfigGraphPackage; ObjectInstanceGraphCommit? get objectConfigGraphPackageObjectInstanceGraphCommit; String get role; String get manifestRelativePath; String get packageKind; String? get expectedHashSha256; String? get description;@UuidValueConverter() UuidValue get sdkPackageId;@UuidValueConverter() UuidValue? get objectConfigGraphPackageId;@UuidValueConverter() UuidValue? get objectConfigGraphPackageObjectInstanceGraphCommitId;
/// Create a copy of SdkPackageObjectConfigGraphPackage
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$SdkPackageObjectConfigGraphPackageCopyWith<SdkPackageObjectConfigGraphPackage> get copyWith => _$SdkPackageObjectConfigGraphPackageCopyWithImpl<SdkPackageObjectConfigGraphPackage>(this as SdkPackageObjectConfigGraphPackage, _$identity);

  /// Serializes this SdkPackageObjectConfigGraphPackage to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is SdkPackageObjectConfigGraphPackage&&(identical(other.id, id) || other.id == id)&&(identical(other.objectConfigGraphPackage, objectConfigGraphPackage) || other.objectConfigGraphPackage == objectConfigGraphPackage)&&(identical(other.objectConfigGraphPackageObjectInstanceGraphCommit, objectConfigGraphPackageObjectInstanceGraphCommit) || other.objectConfigGraphPackageObjectInstanceGraphCommit == objectConfigGraphPackageObjectInstanceGraphCommit)&&(identical(other.role, role) || other.role == role)&&(identical(other.manifestRelativePath, manifestRelativePath) || other.manifestRelativePath == manifestRelativePath)&&(identical(other.packageKind, packageKind) || other.packageKind == packageKind)&&(identical(other.expectedHashSha256, expectedHashSha256) || other.expectedHashSha256 == expectedHashSha256)&&(identical(other.description, description) || other.description == description)&&(identical(other.sdkPackageId, sdkPackageId) || other.sdkPackageId == sdkPackageId)&&(identical(other.objectConfigGraphPackageId, objectConfigGraphPackageId) || other.objectConfigGraphPackageId == objectConfigGraphPackageId)&&(identical(other.objectConfigGraphPackageObjectInstanceGraphCommitId, objectConfigGraphPackageObjectInstanceGraphCommitId) || other.objectConfigGraphPackageObjectInstanceGraphCommitId == objectConfigGraphPackageObjectInstanceGraphCommitId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,objectConfigGraphPackage,objectConfigGraphPackageObjectInstanceGraphCommit,role,manifestRelativePath,packageKind,expectedHashSha256,description,sdkPackageId,objectConfigGraphPackageId,objectConfigGraphPackageObjectInstanceGraphCommitId);

@override
String toString() {
  return 'SdkPackageObjectConfigGraphPackage(id: $id, objectConfigGraphPackage: $objectConfigGraphPackage, objectConfigGraphPackageObjectInstanceGraphCommit: $objectConfigGraphPackageObjectInstanceGraphCommit, role: $role, manifestRelativePath: $manifestRelativePath, packageKind: $packageKind, expectedHashSha256: $expectedHashSha256, description: $description, sdkPackageId: $sdkPackageId, objectConfigGraphPackageId: $objectConfigGraphPackageId, objectConfigGraphPackageObjectInstanceGraphCommitId: $objectConfigGraphPackageObjectInstanceGraphCommitId)';
}


}

/// @nodoc
abstract mixin class $SdkPackageObjectConfigGraphPackageCopyWith<$Res>  {
  factory $SdkPackageObjectConfigGraphPackageCopyWith(SdkPackageObjectConfigGraphPackage value, $Res Function(SdkPackageObjectConfigGraphPackage) _then) = _$SdkPackageObjectConfigGraphPackageCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue id, ObjectConfigGraphPackage? objectConfigGraphPackage, ObjectInstanceGraphCommit? objectConfigGraphPackageObjectInstanceGraphCommit, String role, String manifestRelativePath, String packageKind, String? expectedHashSha256, String? description,@UuidValueConverter() UuidValue sdkPackageId,@UuidValueConverter() UuidValue? objectConfigGraphPackageId,@UuidValueConverter() UuidValue? objectConfigGraphPackageObjectInstanceGraphCommitId
});


$ObjectConfigGraphPackageCopyWith<$Res>? get objectConfigGraphPackage;$ObjectInstanceGraphCommitCopyWith<$Res>? get objectConfigGraphPackageObjectInstanceGraphCommit;

}
/// @nodoc
class _$SdkPackageObjectConfigGraphPackageCopyWithImpl<$Res>
    implements $SdkPackageObjectConfigGraphPackageCopyWith<$Res> {
  _$SdkPackageObjectConfigGraphPackageCopyWithImpl(this._self, this._then);

  final SdkPackageObjectConfigGraphPackage _self;
  final $Res Function(SdkPackageObjectConfigGraphPackage) _then;

/// Create a copy of SdkPackageObjectConfigGraphPackage
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? id = null,Object? objectConfigGraphPackage = freezed,Object? objectConfigGraphPackageObjectInstanceGraphCommit = freezed,Object? role = null,Object? manifestRelativePath = null,Object? packageKind = null,Object? expectedHashSha256 = freezed,Object? description = freezed,Object? sdkPackageId = null,Object? objectConfigGraphPackageId = freezed,Object? objectConfigGraphPackageObjectInstanceGraphCommitId = freezed,}) {
  return _then(_self.copyWith(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,objectConfigGraphPackage: freezed == objectConfigGraphPackage ? _self.objectConfigGraphPackage : objectConfigGraphPackage // ignore: cast_nullable_to_non_nullable
as ObjectConfigGraphPackage?,objectConfigGraphPackageObjectInstanceGraphCommit: freezed == objectConfigGraphPackageObjectInstanceGraphCommit ? _self.objectConfigGraphPackageObjectInstanceGraphCommit : objectConfigGraphPackageObjectInstanceGraphCommit // ignore: cast_nullable_to_non_nullable
as ObjectInstanceGraphCommit?,role: null == role ? _self.role : role // ignore: cast_nullable_to_non_nullable
as String,manifestRelativePath: null == manifestRelativePath ? _self.manifestRelativePath : manifestRelativePath // ignore: cast_nullable_to_non_nullable
as String,packageKind: null == packageKind ? _self.packageKind : packageKind // ignore: cast_nullable_to_non_nullable
as String,expectedHashSha256: freezed == expectedHashSha256 ? _self.expectedHashSha256 : expectedHashSha256 // ignore: cast_nullable_to_non_nullable
as String?,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,sdkPackageId: null == sdkPackageId ? _self.sdkPackageId : sdkPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,objectConfigGraphPackageId: freezed == objectConfigGraphPackageId ? _self.objectConfigGraphPackageId : objectConfigGraphPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectConfigGraphPackageObjectInstanceGraphCommitId: freezed == objectConfigGraphPackageObjectInstanceGraphCommitId ? _self.objectConfigGraphPackageObjectInstanceGraphCommitId : objectConfigGraphPackageObjectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}
/// Create a copy of SdkPackageObjectConfigGraphPackage
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ObjectConfigGraphPackageCopyWith<$Res>? get objectConfigGraphPackage {
    if (_self.objectConfigGraphPackage == null) {
    return null;
  }

  return $ObjectConfigGraphPackageCopyWith<$Res>(_self.objectConfigGraphPackage!, (value) {
    return _then(_self.copyWith(objectConfigGraphPackage: value));
  });
}/// Create a copy of SdkPackageObjectConfigGraphPackage
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ObjectInstanceGraphCommitCopyWith<$Res>? get objectConfigGraphPackageObjectInstanceGraphCommit {
    if (_self.objectConfigGraphPackageObjectInstanceGraphCommit == null) {
    return null;
  }

  return $ObjectInstanceGraphCommitCopyWith<$Res>(_self.objectConfigGraphPackageObjectInstanceGraphCommit!, (value) {
    return _then(_self.copyWith(objectConfigGraphPackageObjectInstanceGraphCommit: value));
  });
}
}


/// Adds pattern-matching-related methods to [SdkPackageObjectConfigGraphPackage].
extension SdkPackageObjectConfigGraphPackagePatterns on SdkPackageObjectConfigGraphPackage {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _SdkPackageObjectConfigGraphPackage value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _SdkPackageObjectConfigGraphPackage() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _SdkPackageObjectConfigGraphPackage value)  def,}){
final _that = this;
switch (_that) {
case _SdkPackageObjectConfigGraphPackage():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _SdkPackageObjectConfigGraphPackage value)?  def,}){
final _that = this;
switch (_that) {
case _SdkPackageObjectConfigGraphPackage() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue id,  ObjectConfigGraphPackage? objectConfigGraphPackage,  ObjectInstanceGraphCommit? objectConfigGraphPackageObjectInstanceGraphCommit,  String role,  String manifestRelativePath,  String packageKind,  String? expectedHashSha256,  String? description, @UuidValueConverter()  UuidValue sdkPackageId, @UuidValueConverter()  UuidValue? objectConfigGraphPackageId, @UuidValueConverter()  UuidValue? objectConfigGraphPackageObjectInstanceGraphCommitId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _SdkPackageObjectConfigGraphPackage() when def != null:
return def(_that.id,_that.objectConfigGraphPackage,_that.objectConfigGraphPackageObjectInstanceGraphCommit,_that.role,_that.manifestRelativePath,_that.packageKind,_that.expectedHashSha256,_that.description,_that.sdkPackageId,_that.objectConfigGraphPackageId,_that.objectConfigGraphPackageObjectInstanceGraphCommitId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue id,  ObjectConfigGraphPackage? objectConfigGraphPackage,  ObjectInstanceGraphCommit? objectConfigGraphPackageObjectInstanceGraphCommit,  String role,  String manifestRelativePath,  String packageKind,  String? expectedHashSha256,  String? description, @UuidValueConverter()  UuidValue sdkPackageId, @UuidValueConverter()  UuidValue? objectConfigGraphPackageId, @UuidValueConverter()  UuidValue? objectConfigGraphPackageObjectInstanceGraphCommitId)  def,}) {final _that = this;
switch (_that) {
case _SdkPackageObjectConfigGraphPackage():
return def(_that.id,_that.objectConfigGraphPackage,_that.objectConfigGraphPackageObjectInstanceGraphCommit,_that.role,_that.manifestRelativePath,_that.packageKind,_that.expectedHashSha256,_that.description,_that.sdkPackageId,_that.objectConfigGraphPackageId,_that.objectConfigGraphPackageObjectInstanceGraphCommitId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue id,  ObjectConfigGraphPackage? objectConfigGraphPackage,  ObjectInstanceGraphCommit? objectConfigGraphPackageObjectInstanceGraphCommit,  String role,  String manifestRelativePath,  String packageKind,  String? expectedHashSha256,  String? description, @UuidValueConverter()  UuidValue sdkPackageId, @UuidValueConverter()  UuidValue? objectConfigGraphPackageId, @UuidValueConverter()  UuidValue? objectConfigGraphPackageObjectInstanceGraphCommitId)?  def,}) {final _that = this;
switch (_that) {
case _SdkPackageObjectConfigGraphPackage() when def != null:
return def(_that.id,_that.objectConfigGraphPackage,_that.objectConfigGraphPackageObjectInstanceGraphCommit,_that.role,_that.manifestRelativePath,_that.packageKind,_that.expectedHashSha256,_that.description,_that.sdkPackageId,_that.objectConfigGraphPackageId,_that.objectConfigGraphPackageObjectInstanceGraphCommitId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _SdkPackageObjectConfigGraphPackage implements SdkPackageObjectConfigGraphPackage {
   _SdkPackageObjectConfigGraphPackage({@UuidValueConverter() required this.id, this.objectConfigGraphPackage, this.objectConfigGraphPackageObjectInstanceGraphCommit, required this.role, required this.manifestRelativePath, required this.packageKind, this.expectedHashSha256, this.description, @UuidValueConverter() required this.sdkPackageId, @UuidValueConverter() this.objectConfigGraphPackageId, @UuidValueConverter() this.objectConfigGraphPackageObjectInstanceGraphCommitId});
  factory _SdkPackageObjectConfigGraphPackage.fromJson(Map<String, dynamic> json) => _$SdkPackageObjectConfigGraphPackageFromJson(json);

@override@UuidValueConverter() final  UuidValue id;
@override final  ObjectConfigGraphPackage? objectConfigGraphPackage;
@override final  ObjectInstanceGraphCommit? objectConfigGraphPackageObjectInstanceGraphCommit;
@override final  String role;
@override final  String manifestRelativePath;
@override final  String packageKind;
@override final  String? expectedHashSha256;
@override final  String? description;
@override@UuidValueConverter() final  UuidValue sdkPackageId;
@override@UuidValueConverter() final  UuidValue? objectConfigGraphPackageId;
@override@UuidValueConverter() final  UuidValue? objectConfigGraphPackageObjectInstanceGraphCommitId;

/// Create a copy of SdkPackageObjectConfigGraphPackage
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$SdkPackageObjectConfigGraphPackageCopyWith<_SdkPackageObjectConfigGraphPackage> get copyWith => __$SdkPackageObjectConfigGraphPackageCopyWithImpl<_SdkPackageObjectConfigGraphPackage>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$SdkPackageObjectConfigGraphPackageToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _SdkPackageObjectConfigGraphPackage&&(identical(other.id, id) || other.id == id)&&(identical(other.objectConfigGraphPackage, objectConfigGraphPackage) || other.objectConfigGraphPackage == objectConfigGraphPackage)&&(identical(other.objectConfigGraphPackageObjectInstanceGraphCommit, objectConfigGraphPackageObjectInstanceGraphCommit) || other.objectConfigGraphPackageObjectInstanceGraphCommit == objectConfigGraphPackageObjectInstanceGraphCommit)&&(identical(other.role, role) || other.role == role)&&(identical(other.manifestRelativePath, manifestRelativePath) || other.manifestRelativePath == manifestRelativePath)&&(identical(other.packageKind, packageKind) || other.packageKind == packageKind)&&(identical(other.expectedHashSha256, expectedHashSha256) || other.expectedHashSha256 == expectedHashSha256)&&(identical(other.description, description) || other.description == description)&&(identical(other.sdkPackageId, sdkPackageId) || other.sdkPackageId == sdkPackageId)&&(identical(other.objectConfigGraphPackageId, objectConfigGraphPackageId) || other.objectConfigGraphPackageId == objectConfigGraphPackageId)&&(identical(other.objectConfigGraphPackageObjectInstanceGraphCommitId, objectConfigGraphPackageObjectInstanceGraphCommitId) || other.objectConfigGraphPackageObjectInstanceGraphCommitId == objectConfigGraphPackageObjectInstanceGraphCommitId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,objectConfigGraphPackage,objectConfigGraphPackageObjectInstanceGraphCommit,role,manifestRelativePath,packageKind,expectedHashSha256,description,sdkPackageId,objectConfigGraphPackageId,objectConfigGraphPackageObjectInstanceGraphCommitId);

@override
String toString() {
  return 'SdkPackageObjectConfigGraphPackage.def(id: $id, objectConfigGraphPackage: $objectConfigGraphPackage, objectConfigGraphPackageObjectInstanceGraphCommit: $objectConfigGraphPackageObjectInstanceGraphCommit, role: $role, manifestRelativePath: $manifestRelativePath, packageKind: $packageKind, expectedHashSha256: $expectedHashSha256, description: $description, sdkPackageId: $sdkPackageId, objectConfigGraphPackageId: $objectConfigGraphPackageId, objectConfigGraphPackageObjectInstanceGraphCommitId: $objectConfigGraphPackageObjectInstanceGraphCommitId)';
}


}

/// @nodoc
abstract mixin class _$SdkPackageObjectConfigGraphPackageCopyWith<$Res> implements $SdkPackageObjectConfigGraphPackageCopyWith<$Res> {
  factory _$SdkPackageObjectConfigGraphPackageCopyWith(_SdkPackageObjectConfigGraphPackage value, $Res Function(_SdkPackageObjectConfigGraphPackage) _then) = __$SdkPackageObjectConfigGraphPackageCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue id, ObjectConfigGraphPackage? objectConfigGraphPackage, ObjectInstanceGraphCommit? objectConfigGraphPackageObjectInstanceGraphCommit, String role, String manifestRelativePath, String packageKind, String? expectedHashSha256, String? description,@UuidValueConverter() UuidValue sdkPackageId,@UuidValueConverter() UuidValue? objectConfigGraphPackageId,@UuidValueConverter() UuidValue? objectConfigGraphPackageObjectInstanceGraphCommitId
});


@override $ObjectConfigGraphPackageCopyWith<$Res>? get objectConfigGraphPackage;@override $ObjectInstanceGraphCommitCopyWith<$Res>? get objectConfigGraphPackageObjectInstanceGraphCommit;

}
/// @nodoc
class __$SdkPackageObjectConfigGraphPackageCopyWithImpl<$Res>
    implements _$SdkPackageObjectConfigGraphPackageCopyWith<$Res> {
  __$SdkPackageObjectConfigGraphPackageCopyWithImpl(this._self, this._then);

  final _SdkPackageObjectConfigGraphPackage _self;
  final $Res Function(_SdkPackageObjectConfigGraphPackage) _then;

/// Create a copy of SdkPackageObjectConfigGraphPackage
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? id = null,Object? objectConfigGraphPackage = freezed,Object? objectConfigGraphPackageObjectInstanceGraphCommit = freezed,Object? role = null,Object? manifestRelativePath = null,Object? packageKind = null,Object? expectedHashSha256 = freezed,Object? description = freezed,Object? sdkPackageId = null,Object? objectConfigGraphPackageId = freezed,Object? objectConfigGraphPackageObjectInstanceGraphCommitId = freezed,}) {
  return _then(_SdkPackageObjectConfigGraphPackage(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,objectConfigGraphPackage: freezed == objectConfigGraphPackage ? _self.objectConfigGraphPackage : objectConfigGraphPackage // ignore: cast_nullable_to_non_nullable
as ObjectConfigGraphPackage?,objectConfigGraphPackageObjectInstanceGraphCommit: freezed == objectConfigGraphPackageObjectInstanceGraphCommit ? _self.objectConfigGraphPackageObjectInstanceGraphCommit : objectConfigGraphPackageObjectInstanceGraphCommit // ignore: cast_nullable_to_non_nullable
as ObjectInstanceGraphCommit?,role: null == role ? _self.role : role // ignore: cast_nullable_to_non_nullable
as String,manifestRelativePath: null == manifestRelativePath ? _self.manifestRelativePath : manifestRelativePath // ignore: cast_nullable_to_non_nullable
as String,packageKind: null == packageKind ? _self.packageKind : packageKind // ignore: cast_nullable_to_non_nullable
as String,expectedHashSha256: freezed == expectedHashSha256 ? _self.expectedHashSha256 : expectedHashSha256 // ignore: cast_nullable_to_non_nullable
as String?,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,sdkPackageId: null == sdkPackageId ? _self.sdkPackageId : sdkPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,objectConfigGraphPackageId: freezed == objectConfigGraphPackageId ? _self.objectConfigGraphPackageId : objectConfigGraphPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectConfigGraphPackageObjectInstanceGraphCommitId: freezed == objectConfigGraphPackageObjectInstanceGraphCommitId ? _self.objectConfigGraphPackageObjectInstanceGraphCommitId : objectConfigGraphPackageObjectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

/// Create a copy of SdkPackageObjectConfigGraphPackage
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ObjectConfigGraphPackageCopyWith<$Res>? get objectConfigGraphPackage {
    if (_self.objectConfigGraphPackage == null) {
    return null;
  }

  return $ObjectConfigGraphPackageCopyWith<$Res>(_self.objectConfigGraphPackage!, (value) {
    return _then(_self.copyWith(objectConfigGraphPackage: value));
  });
}/// Create a copy of SdkPackageObjectConfigGraphPackage
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ObjectInstanceGraphCommitCopyWith<$Res>? get objectConfigGraphPackageObjectInstanceGraphCommit {
    if (_self.objectConfigGraphPackageObjectInstanceGraphCommit == null) {
    return null;
  }

  return $ObjectInstanceGraphCommitCopyWith<$Res>(_self.objectConfigGraphPackageObjectInstanceGraphCommit!, (value) {
    return _then(_self.copyWith(objectConfigGraphPackageObjectInstanceGraphCommit: value));
  });
}
}

// dart format on
