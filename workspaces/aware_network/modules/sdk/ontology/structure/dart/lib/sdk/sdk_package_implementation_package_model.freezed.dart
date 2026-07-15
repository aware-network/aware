// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'sdk_package_implementation_package_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$SdkPackageImplementationPackage {

@UuidValueConverter() UuidValue get id; CodePackage? get codePackage; String? get entrypoint; List<dynamic> get excludePaths; String get importRoot; List<dynamic> get includePaths;@JsonKey(fromJson: CodeLanguageExtension.fromJson, toJson: CodeLanguageExtension.toJson) CodeLanguage get language; String get manifestRelativePath; String get packageName; String get packageRoot; String get role;@UuidValueConverter() UuidValue get sdkPackageId;@UuidValueConverter() UuidValue? get codePackageId;
/// Create a copy of SdkPackageImplementationPackage
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$SdkPackageImplementationPackageCopyWith<SdkPackageImplementationPackage> get copyWith => _$SdkPackageImplementationPackageCopyWithImpl<SdkPackageImplementationPackage>(this as SdkPackageImplementationPackage, _$identity);

  /// Serializes this SdkPackageImplementationPackage to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is SdkPackageImplementationPackage&&(identical(other.id, id) || other.id == id)&&(identical(other.codePackage, codePackage) || other.codePackage == codePackage)&&(identical(other.entrypoint, entrypoint) || other.entrypoint == entrypoint)&&const DeepCollectionEquality().equals(other.excludePaths, excludePaths)&&(identical(other.importRoot, importRoot) || other.importRoot == importRoot)&&const DeepCollectionEquality().equals(other.includePaths, includePaths)&&(identical(other.language, language) || other.language == language)&&(identical(other.manifestRelativePath, manifestRelativePath) || other.manifestRelativePath == manifestRelativePath)&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.packageRoot, packageRoot) || other.packageRoot == packageRoot)&&(identical(other.role, role) || other.role == role)&&(identical(other.sdkPackageId, sdkPackageId) || other.sdkPackageId == sdkPackageId)&&(identical(other.codePackageId, codePackageId) || other.codePackageId == codePackageId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,codePackage,entrypoint,const DeepCollectionEquality().hash(excludePaths),importRoot,const DeepCollectionEquality().hash(includePaths),language,manifestRelativePath,packageName,packageRoot,role,sdkPackageId,codePackageId);

@override
String toString() {
  return 'SdkPackageImplementationPackage(id: $id, codePackage: $codePackage, entrypoint: $entrypoint, excludePaths: $excludePaths, importRoot: $importRoot, includePaths: $includePaths, language: $language, manifestRelativePath: $manifestRelativePath, packageName: $packageName, packageRoot: $packageRoot, role: $role, sdkPackageId: $sdkPackageId, codePackageId: $codePackageId)';
}


}

/// @nodoc
abstract mixin class $SdkPackageImplementationPackageCopyWith<$Res>  {
  factory $SdkPackageImplementationPackageCopyWith(SdkPackageImplementationPackage value, $Res Function(SdkPackageImplementationPackage) _then) = _$SdkPackageImplementationPackageCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue id, CodePackage? codePackage, String? entrypoint, List<dynamic> excludePaths, String importRoot, List<dynamic> includePaths,@JsonKey(fromJson: CodeLanguageExtension.fromJson, toJson: CodeLanguageExtension.toJson) CodeLanguage language, String manifestRelativePath, String packageName, String packageRoot, String role,@UuidValueConverter() UuidValue sdkPackageId,@UuidValueConverter() UuidValue? codePackageId
});


$CodePackageCopyWith<$Res>? get codePackage;

}
/// @nodoc
class _$SdkPackageImplementationPackageCopyWithImpl<$Res>
    implements $SdkPackageImplementationPackageCopyWith<$Res> {
  _$SdkPackageImplementationPackageCopyWithImpl(this._self, this._then);

  final SdkPackageImplementationPackage _self;
  final $Res Function(SdkPackageImplementationPackage) _then;

/// Create a copy of SdkPackageImplementationPackage
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? id = null,Object? codePackage = freezed,Object? entrypoint = freezed,Object? excludePaths = null,Object? importRoot = null,Object? includePaths = null,Object? language = null,Object? manifestRelativePath = null,Object? packageName = null,Object? packageRoot = null,Object? role = null,Object? sdkPackageId = null,Object? codePackageId = freezed,}) {
  return _then(_self.copyWith(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,codePackage: freezed == codePackage ? _self.codePackage : codePackage // ignore: cast_nullable_to_non_nullable
as CodePackage?,entrypoint: freezed == entrypoint ? _self.entrypoint : entrypoint // ignore: cast_nullable_to_non_nullable
as String?,excludePaths: null == excludePaths ? _self.excludePaths : excludePaths // ignore: cast_nullable_to_non_nullable
as List<dynamic>,importRoot: null == importRoot ? _self.importRoot : importRoot // ignore: cast_nullable_to_non_nullable
as String,includePaths: null == includePaths ? _self.includePaths : includePaths // ignore: cast_nullable_to_non_nullable
as List<dynamic>,language: null == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as CodeLanguage,manifestRelativePath: null == manifestRelativePath ? _self.manifestRelativePath : manifestRelativePath // ignore: cast_nullable_to_non_nullable
as String,packageName: null == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String,packageRoot: null == packageRoot ? _self.packageRoot : packageRoot // ignore: cast_nullable_to_non_nullable
as String,role: null == role ? _self.role : role // ignore: cast_nullable_to_non_nullable
as String,sdkPackageId: null == sdkPackageId ? _self.sdkPackageId : sdkPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,codePackageId: freezed == codePackageId ? _self.codePackageId : codePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}
/// Create a copy of SdkPackageImplementationPackage
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageCopyWith<$Res>? get codePackage {
    if (_self.codePackage == null) {
    return null;
  }

  return $CodePackageCopyWith<$Res>(_self.codePackage!, (value) {
    return _then(_self.copyWith(codePackage: value));
  });
}
}


/// Adds pattern-matching-related methods to [SdkPackageImplementationPackage].
extension SdkPackageImplementationPackagePatterns on SdkPackageImplementationPackage {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _SdkPackageImplementationPackage value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _SdkPackageImplementationPackage() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _SdkPackageImplementationPackage value)  def,}){
final _that = this;
switch (_that) {
case _SdkPackageImplementationPackage():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _SdkPackageImplementationPackage value)?  def,}){
final _that = this;
switch (_that) {
case _SdkPackageImplementationPackage() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue id,  CodePackage? codePackage,  String? entrypoint,  List<dynamic> excludePaths,  String importRoot,  List<dynamic> includePaths, @JsonKey(fromJson: CodeLanguageExtension.fromJson, toJson: CodeLanguageExtension.toJson)  CodeLanguage language,  String manifestRelativePath,  String packageName,  String packageRoot,  String role, @UuidValueConverter()  UuidValue sdkPackageId, @UuidValueConverter()  UuidValue? codePackageId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _SdkPackageImplementationPackage() when def != null:
return def(_that.id,_that.codePackage,_that.entrypoint,_that.excludePaths,_that.importRoot,_that.includePaths,_that.language,_that.manifestRelativePath,_that.packageName,_that.packageRoot,_that.role,_that.sdkPackageId,_that.codePackageId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue id,  CodePackage? codePackage,  String? entrypoint,  List<dynamic> excludePaths,  String importRoot,  List<dynamic> includePaths, @JsonKey(fromJson: CodeLanguageExtension.fromJson, toJson: CodeLanguageExtension.toJson)  CodeLanguage language,  String manifestRelativePath,  String packageName,  String packageRoot,  String role, @UuidValueConverter()  UuidValue sdkPackageId, @UuidValueConverter()  UuidValue? codePackageId)  def,}) {final _that = this;
switch (_that) {
case _SdkPackageImplementationPackage():
return def(_that.id,_that.codePackage,_that.entrypoint,_that.excludePaths,_that.importRoot,_that.includePaths,_that.language,_that.manifestRelativePath,_that.packageName,_that.packageRoot,_that.role,_that.sdkPackageId,_that.codePackageId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue id,  CodePackage? codePackage,  String? entrypoint,  List<dynamic> excludePaths,  String importRoot,  List<dynamic> includePaths, @JsonKey(fromJson: CodeLanguageExtension.fromJson, toJson: CodeLanguageExtension.toJson)  CodeLanguage language,  String manifestRelativePath,  String packageName,  String packageRoot,  String role, @UuidValueConverter()  UuidValue sdkPackageId, @UuidValueConverter()  UuidValue? codePackageId)?  def,}) {final _that = this;
switch (_that) {
case _SdkPackageImplementationPackage() when def != null:
return def(_that.id,_that.codePackage,_that.entrypoint,_that.excludePaths,_that.importRoot,_that.includePaths,_that.language,_that.manifestRelativePath,_that.packageName,_that.packageRoot,_that.role,_that.sdkPackageId,_that.codePackageId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _SdkPackageImplementationPackage implements SdkPackageImplementationPackage {
   _SdkPackageImplementationPackage({@UuidValueConverter() required this.id, this.codePackage, this.entrypoint, required final  List<dynamic> excludePaths, required this.importRoot, required final  List<dynamic> includePaths, @JsonKey(fromJson: CodeLanguageExtension.fromJson, toJson: CodeLanguageExtension.toJson) required this.language, required this.manifestRelativePath, required this.packageName, required this.packageRoot, required this.role, @UuidValueConverter() required this.sdkPackageId, @UuidValueConverter() this.codePackageId}): _excludePaths = excludePaths,_includePaths = includePaths;
  factory _SdkPackageImplementationPackage.fromJson(Map<String, dynamic> json) => _$SdkPackageImplementationPackageFromJson(json);

@override@UuidValueConverter() final  UuidValue id;
@override final  CodePackage? codePackage;
@override final  String? entrypoint;
 final  List<dynamic> _excludePaths;
@override List<dynamic> get excludePaths {
  if (_excludePaths is EqualUnmodifiableListView) return _excludePaths;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_excludePaths);
}

@override final  String importRoot;
 final  List<dynamic> _includePaths;
@override List<dynamic> get includePaths {
  if (_includePaths is EqualUnmodifiableListView) return _includePaths;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_includePaths);
}

@override@JsonKey(fromJson: CodeLanguageExtension.fromJson, toJson: CodeLanguageExtension.toJson) final  CodeLanguage language;
@override final  String manifestRelativePath;
@override final  String packageName;
@override final  String packageRoot;
@override final  String role;
@override@UuidValueConverter() final  UuidValue sdkPackageId;
@override@UuidValueConverter() final  UuidValue? codePackageId;

/// Create a copy of SdkPackageImplementationPackage
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$SdkPackageImplementationPackageCopyWith<_SdkPackageImplementationPackage> get copyWith => __$SdkPackageImplementationPackageCopyWithImpl<_SdkPackageImplementationPackage>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$SdkPackageImplementationPackageToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _SdkPackageImplementationPackage&&(identical(other.id, id) || other.id == id)&&(identical(other.codePackage, codePackage) || other.codePackage == codePackage)&&(identical(other.entrypoint, entrypoint) || other.entrypoint == entrypoint)&&const DeepCollectionEquality().equals(other._excludePaths, _excludePaths)&&(identical(other.importRoot, importRoot) || other.importRoot == importRoot)&&const DeepCollectionEquality().equals(other._includePaths, _includePaths)&&(identical(other.language, language) || other.language == language)&&(identical(other.manifestRelativePath, manifestRelativePath) || other.manifestRelativePath == manifestRelativePath)&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.packageRoot, packageRoot) || other.packageRoot == packageRoot)&&(identical(other.role, role) || other.role == role)&&(identical(other.sdkPackageId, sdkPackageId) || other.sdkPackageId == sdkPackageId)&&(identical(other.codePackageId, codePackageId) || other.codePackageId == codePackageId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,codePackage,entrypoint,const DeepCollectionEquality().hash(_excludePaths),importRoot,const DeepCollectionEquality().hash(_includePaths),language,manifestRelativePath,packageName,packageRoot,role,sdkPackageId,codePackageId);

@override
String toString() {
  return 'SdkPackageImplementationPackage.def(id: $id, codePackage: $codePackage, entrypoint: $entrypoint, excludePaths: $excludePaths, importRoot: $importRoot, includePaths: $includePaths, language: $language, manifestRelativePath: $manifestRelativePath, packageName: $packageName, packageRoot: $packageRoot, role: $role, sdkPackageId: $sdkPackageId, codePackageId: $codePackageId)';
}


}

/// @nodoc
abstract mixin class _$SdkPackageImplementationPackageCopyWith<$Res> implements $SdkPackageImplementationPackageCopyWith<$Res> {
  factory _$SdkPackageImplementationPackageCopyWith(_SdkPackageImplementationPackage value, $Res Function(_SdkPackageImplementationPackage) _then) = __$SdkPackageImplementationPackageCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue id, CodePackage? codePackage, String? entrypoint, List<dynamic> excludePaths, String importRoot, List<dynamic> includePaths,@JsonKey(fromJson: CodeLanguageExtension.fromJson, toJson: CodeLanguageExtension.toJson) CodeLanguage language, String manifestRelativePath, String packageName, String packageRoot, String role,@UuidValueConverter() UuidValue sdkPackageId,@UuidValueConverter() UuidValue? codePackageId
});


@override $CodePackageCopyWith<$Res>? get codePackage;

}
/// @nodoc
class __$SdkPackageImplementationPackageCopyWithImpl<$Res>
    implements _$SdkPackageImplementationPackageCopyWith<$Res> {
  __$SdkPackageImplementationPackageCopyWithImpl(this._self, this._then);

  final _SdkPackageImplementationPackage _self;
  final $Res Function(_SdkPackageImplementationPackage) _then;

/// Create a copy of SdkPackageImplementationPackage
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? id = null,Object? codePackage = freezed,Object? entrypoint = freezed,Object? excludePaths = null,Object? importRoot = null,Object? includePaths = null,Object? language = null,Object? manifestRelativePath = null,Object? packageName = null,Object? packageRoot = null,Object? role = null,Object? sdkPackageId = null,Object? codePackageId = freezed,}) {
  return _then(_SdkPackageImplementationPackage(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,codePackage: freezed == codePackage ? _self.codePackage : codePackage // ignore: cast_nullable_to_non_nullable
as CodePackage?,entrypoint: freezed == entrypoint ? _self.entrypoint : entrypoint // ignore: cast_nullable_to_non_nullable
as String?,excludePaths: null == excludePaths ? _self._excludePaths : excludePaths // ignore: cast_nullable_to_non_nullable
as List<dynamic>,importRoot: null == importRoot ? _self.importRoot : importRoot // ignore: cast_nullable_to_non_nullable
as String,includePaths: null == includePaths ? _self._includePaths : includePaths // ignore: cast_nullable_to_non_nullable
as List<dynamic>,language: null == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as CodeLanguage,manifestRelativePath: null == manifestRelativePath ? _self.manifestRelativePath : manifestRelativePath // ignore: cast_nullable_to_non_nullable
as String,packageName: null == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String,packageRoot: null == packageRoot ? _self.packageRoot : packageRoot // ignore: cast_nullable_to_non_nullable
as String,role: null == role ? _self.role : role // ignore: cast_nullable_to_non_nullable
as String,sdkPackageId: null == sdkPackageId ? _self.sdkPackageId : sdkPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,codePackageId: freezed == codePackageId ? _self.codePackageId : codePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

/// Create a copy of SdkPackageImplementationPackage
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageCopyWith<$Res>? get codePackage {
    if (_self.codePackage == null) {
    return null;
  }

  return $CodePackageCopyWith<$Res>(_self.codePackage!, (value) {
    return _then(_self.copyWith(codePackage: value));
  });
}
}

// dart format on
