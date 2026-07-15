// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'sdk_package_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$SdkPackage {

@UuidValueConverter() UuidValue get id; CodePackage? get sourceCodePackage; List<SdkPackageApiPackage> get apiPackages; List<SdkPackageImplementationPackage> get implementationPackages; List<SdkPackageObjectConfigGraphPackage> get objectConfigGraphPackages; List<SdkPackageDependency> get sdkPackageDependencies; SdkConfig? get sdkConfig; ObjectInstanceGraphCommit? get sdkConfigObjectInstanceGraphCommit; int get awareSdkVersion; String get compilationMode; List<dynamic> get dependencies; String? get description; List<dynamic> get excludePaths; bool get forceFreshScan; String? get fqnPrefix; List<dynamic> get includePaths; String? get manifestRelativePath; String get name; String get packageRoot; String get sourcesRoot; Map<String, dynamic> get targets; String? get title; int get versionNumber;@UuidValueConverter() UuidValue? get sourceCodePackageId;@UuidValueConverter() UuidValue? get sdkConfigId;@UuidValueConverter() UuidValue? get sdkConfigObjectInstanceGraphCommitId;
/// Create a copy of SdkPackage
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$SdkPackageCopyWith<SdkPackage> get copyWith => _$SdkPackageCopyWithImpl<SdkPackage>(this as SdkPackage, _$identity);

  /// Serializes this SdkPackage to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is SdkPackage&&(identical(other.id, id) || other.id == id)&&(identical(other.sourceCodePackage, sourceCodePackage) || other.sourceCodePackage == sourceCodePackage)&&const DeepCollectionEquality().equals(other.apiPackages, apiPackages)&&const DeepCollectionEquality().equals(other.implementationPackages, implementationPackages)&&const DeepCollectionEquality().equals(other.objectConfigGraphPackages, objectConfigGraphPackages)&&const DeepCollectionEquality().equals(other.sdkPackageDependencies, sdkPackageDependencies)&&(identical(other.sdkConfig, sdkConfig) || other.sdkConfig == sdkConfig)&&(identical(other.sdkConfigObjectInstanceGraphCommit, sdkConfigObjectInstanceGraphCommit) || other.sdkConfigObjectInstanceGraphCommit == sdkConfigObjectInstanceGraphCommit)&&(identical(other.awareSdkVersion, awareSdkVersion) || other.awareSdkVersion == awareSdkVersion)&&(identical(other.compilationMode, compilationMode) || other.compilationMode == compilationMode)&&const DeepCollectionEquality().equals(other.dependencies, dependencies)&&(identical(other.description, description) || other.description == description)&&const DeepCollectionEquality().equals(other.excludePaths, excludePaths)&&(identical(other.forceFreshScan, forceFreshScan) || other.forceFreshScan == forceFreshScan)&&(identical(other.fqnPrefix, fqnPrefix) || other.fqnPrefix == fqnPrefix)&&const DeepCollectionEquality().equals(other.includePaths, includePaths)&&(identical(other.manifestRelativePath, manifestRelativePath) || other.manifestRelativePath == manifestRelativePath)&&(identical(other.name, name) || other.name == name)&&(identical(other.packageRoot, packageRoot) || other.packageRoot == packageRoot)&&(identical(other.sourcesRoot, sourcesRoot) || other.sourcesRoot == sourcesRoot)&&const DeepCollectionEquality().equals(other.targets, targets)&&(identical(other.title, title) || other.title == title)&&(identical(other.versionNumber, versionNumber) || other.versionNumber == versionNumber)&&(identical(other.sourceCodePackageId, sourceCodePackageId) || other.sourceCodePackageId == sourceCodePackageId)&&(identical(other.sdkConfigId, sdkConfigId) || other.sdkConfigId == sdkConfigId)&&(identical(other.sdkConfigObjectInstanceGraphCommitId, sdkConfigObjectInstanceGraphCommitId) || other.sdkConfigObjectInstanceGraphCommitId == sdkConfigObjectInstanceGraphCommitId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,id,sourceCodePackage,const DeepCollectionEquality().hash(apiPackages),const DeepCollectionEquality().hash(implementationPackages),const DeepCollectionEquality().hash(objectConfigGraphPackages),const DeepCollectionEquality().hash(sdkPackageDependencies),sdkConfig,sdkConfigObjectInstanceGraphCommit,awareSdkVersion,compilationMode,const DeepCollectionEquality().hash(dependencies),description,const DeepCollectionEquality().hash(excludePaths),forceFreshScan,fqnPrefix,const DeepCollectionEquality().hash(includePaths),manifestRelativePath,name,packageRoot,sourcesRoot,const DeepCollectionEquality().hash(targets),title,versionNumber,sourceCodePackageId,sdkConfigId,sdkConfigObjectInstanceGraphCommitId]);

@override
String toString() {
  return 'SdkPackage(id: $id, sourceCodePackage: $sourceCodePackage, apiPackages: $apiPackages, implementationPackages: $implementationPackages, objectConfigGraphPackages: $objectConfigGraphPackages, sdkPackageDependencies: $sdkPackageDependencies, sdkConfig: $sdkConfig, sdkConfigObjectInstanceGraphCommit: $sdkConfigObjectInstanceGraphCommit, awareSdkVersion: $awareSdkVersion, compilationMode: $compilationMode, dependencies: $dependencies, description: $description, excludePaths: $excludePaths, forceFreshScan: $forceFreshScan, fqnPrefix: $fqnPrefix, includePaths: $includePaths, manifestRelativePath: $manifestRelativePath, name: $name, packageRoot: $packageRoot, sourcesRoot: $sourcesRoot, targets: $targets, title: $title, versionNumber: $versionNumber, sourceCodePackageId: $sourceCodePackageId, sdkConfigId: $sdkConfigId, sdkConfigObjectInstanceGraphCommitId: $sdkConfigObjectInstanceGraphCommitId)';
}


}

/// @nodoc
abstract mixin class $SdkPackageCopyWith<$Res>  {
  factory $SdkPackageCopyWith(SdkPackage value, $Res Function(SdkPackage) _then) = _$SdkPackageCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue id, CodePackage? sourceCodePackage, List<SdkPackageApiPackage> apiPackages, List<SdkPackageImplementationPackage> implementationPackages, List<SdkPackageObjectConfigGraphPackage> objectConfigGraphPackages, List<SdkPackageDependency> sdkPackageDependencies, SdkConfig? sdkConfig, ObjectInstanceGraphCommit? sdkConfigObjectInstanceGraphCommit, int awareSdkVersion, String compilationMode, List<dynamic> dependencies, String? description, List<dynamic> excludePaths, bool forceFreshScan, String? fqnPrefix, List<dynamic> includePaths, String? manifestRelativePath, String name, String packageRoot, String sourcesRoot, Map<String, dynamic> targets, String? title, int versionNumber,@UuidValueConverter() UuidValue? sourceCodePackageId,@UuidValueConverter() UuidValue? sdkConfigId,@UuidValueConverter() UuidValue? sdkConfigObjectInstanceGraphCommitId
});


$CodePackageCopyWith<$Res>? get sourceCodePackage;$SdkConfigCopyWith<$Res>? get sdkConfig;$ObjectInstanceGraphCommitCopyWith<$Res>? get sdkConfigObjectInstanceGraphCommit;

}
/// @nodoc
class _$SdkPackageCopyWithImpl<$Res>
    implements $SdkPackageCopyWith<$Res> {
  _$SdkPackageCopyWithImpl(this._self, this._then);

  final SdkPackage _self;
  final $Res Function(SdkPackage) _then;

/// Create a copy of SdkPackage
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? id = null,Object? sourceCodePackage = freezed,Object? apiPackages = null,Object? implementationPackages = null,Object? objectConfigGraphPackages = null,Object? sdkPackageDependencies = null,Object? sdkConfig = freezed,Object? sdkConfigObjectInstanceGraphCommit = freezed,Object? awareSdkVersion = null,Object? compilationMode = null,Object? dependencies = null,Object? description = freezed,Object? excludePaths = null,Object? forceFreshScan = null,Object? fqnPrefix = freezed,Object? includePaths = null,Object? manifestRelativePath = freezed,Object? name = null,Object? packageRoot = null,Object? sourcesRoot = null,Object? targets = null,Object? title = freezed,Object? versionNumber = null,Object? sourceCodePackageId = freezed,Object? sdkConfigId = freezed,Object? sdkConfigObjectInstanceGraphCommitId = freezed,}) {
  return _then(_self.copyWith(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,sourceCodePackage: freezed == sourceCodePackage ? _self.sourceCodePackage : sourceCodePackage // ignore: cast_nullable_to_non_nullable
as CodePackage?,apiPackages: null == apiPackages ? _self.apiPackages : apiPackages // ignore: cast_nullable_to_non_nullable
as List<SdkPackageApiPackage>,implementationPackages: null == implementationPackages ? _self.implementationPackages : implementationPackages // ignore: cast_nullable_to_non_nullable
as List<SdkPackageImplementationPackage>,objectConfigGraphPackages: null == objectConfigGraphPackages ? _self.objectConfigGraphPackages : objectConfigGraphPackages // ignore: cast_nullable_to_non_nullable
as List<SdkPackageObjectConfigGraphPackage>,sdkPackageDependencies: null == sdkPackageDependencies ? _self.sdkPackageDependencies : sdkPackageDependencies // ignore: cast_nullable_to_non_nullable
as List<SdkPackageDependency>,sdkConfig: freezed == sdkConfig ? _self.sdkConfig : sdkConfig // ignore: cast_nullable_to_non_nullable
as SdkConfig?,sdkConfigObjectInstanceGraphCommit: freezed == sdkConfigObjectInstanceGraphCommit ? _self.sdkConfigObjectInstanceGraphCommit : sdkConfigObjectInstanceGraphCommit // ignore: cast_nullable_to_non_nullable
as ObjectInstanceGraphCommit?,awareSdkVersion: null == awareSdkVersion ? _self.awareSdkVersion : awareSdkVersion // ignore: cast_nullable_to_non_nullable
as int,compilationMode: null == compilationMode ? _self.compilationMode : compilationMode // ignore: cast_nullable_to_non_nullable
as String,dependencies: null == dependencies ? _self.dependencies : dependencies // ignore: cast_nullable_to_non_nullable
as List<dynamic>,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,excludePaths: null == excludePaths ? _self.excludePaths : excludePaths // ignore: cast_nullable_to_non_nullable
as List<dynamic>,forceFreshScan: null == forceFreshScan ? _self.forceFreshScan : forceFreshScan // ignore: cast_nullable_to_non_nullable
as bool,fqnPrefix: freezed == fqnPrefix ? _self.fqnPrefix : fqnPrefix // ignore: cast_nullable_to_non_nullable
as String?,includePaths: null == includePaths ? _self.includePaths : includePaths // ignore: cast_nullable_to_non_nullable
as List<dynamic>,manifestRelativePath: freezed == manifestRelativePath ? _self.manifestRelativePath : manifestRelativePath // ignore: cast_nullable_to_non_nullable
as String?,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,packageRoot: null == packageRoot ? _self.packageRoot : packageRoot // ignore: cast_nullable_to_non_nullable
as String,sourcesRoot: null == sourcesRoot ? _self.sourcesRoot : sourcesRoot // ignore: cast_nullable_to_non_nullable
as String,targets: null == targets ? _self.targets : targets // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,versionNumber: null == versionNumber ? _self.versionNumber : versionNumber // ignore: cast_nullable_to_non_nullable
as int,sourceCodePackageId: freezed == sourceCodePackageId ? _self.sourceCodePackageId : sourceCodePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sdkConfigId: freezed == sdkConfigId ? _self.sdkConfigId : sdkConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sdkConfigObjectInstanceGraphCommitId: freezed == sdkConfigObjectInstanceGraphCommitId ? _self.sdkConfigObjectInstanceGraphCommitId : sdkConfigObjectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}
/// Create a copy of SdkPackage
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageCopyWith<$Res>? get sourceCodePackage {
    if (_self.sourceCodePackage == null) {
    return null;
  }

  return $CodePackageCopyWith<$Res>(_self.sourceCodePackage!, (value) {
    return _then(_self.copyWith(sourceCodePackage: value));
  });
}/// Create a copy of SdkPackage
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$SdkConfigCopyWith<$Res>? get sdkConfig {
    if (_self.sdkConfig == null) {
    return null;
  }

  return $SdkConfigCopyWith<$Res>(_self.sdkConfig!, (value) {
    return _then(_self.copyWith(sdkConfig: value));
  });
}/// Create a copy of SdkPackage
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ObjectInstanceGraphCommitCopyWith<$Res>? get sdkConfigObjectInstanceGraphCommit {
    if (_self.sdkConfigObjectInstanceGraphCommit == null) {
    return null;
  }

  return $ObjectInstanceGraphCommitCopyWith<$Res>(_self.sdkConfigObjectInstanceGraphCommit!, (value) {
    return _then(_self.copyWith(sdkConfigObjectInstanceGraphCommit: value));
  });
}
}


/// Adds pattern-matching-related methods to [SdkPackage].
extension SdkPackagePatterns on SdkPackage {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _SdkPackage value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _SdkPackage() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _SdkPackage value)  def,}){
final _that = this;
switch (_that) {
case _SdkPackage():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _SdkPackage value)?  def,}){
final _that = this;
switch (_that) {
case _SdkPackage() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue id,  CodePackage? sourceCodePackage,  List<SdkPackageApiPackage> apiPackages,  List<SdkPackageImplementationPackage> implementationPackages,  List<SdkPackageObjectConfigGraphPackage> objectConfigGraphPackages,  List<SdkPackageDependency> sdkPackageDependencies,  SdkConfig? sdkConfig,  ObjectInstanceGraphCommit? sdkConfigObjectInstanceGraphCommit,  int awareSdkVersion,  String compilationMode,  List<dynamic> dependencies,  String? description,  List<dynamic> excludePaths,  bool forceFreshScan,  String? fqnPrefix,  List<dynamic> includePaths,  String? manifestRelativePath,  String name,  String packageRoot,  String sourcesRoot,  Map<String, dynamic> targets,  String? title,  int versionNumber, @UuidValueConverter()  UuidValue? sourceCodePackageId, @UuidValueConverter()  UuidValue? sdkConfigId, @UuidValueConverter()  UuidValue? sdkConfigObjectInstanceGraphCommitId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _SdkPackage() when def != null:
return def(_that.id,_that.sourceCodePackage,_that.apiPackages,_that.implementationPackages,_that.objectConfigGraphPackages,_that.sdkPackageDependencies,_that.sdkConfig,_that.sdkConfigObjectInstanceGraphCommit,_that.awareSdkVersion,_that.compilationMode,_that.dependencies,_that.description,_that.excludePaths,_that.forceFreshScan,_that.fqnPrefix,_that.includePaths,_that.manifestRelativePath,_that.name,_that.packageRoot,_that.sourcesRoot,_that.targets,_that.title,_that.versionNumber,_that.sourceCodePackageId,_that.sdkConfigId,_that.sdkConfigObjectInstanceGraphCommitId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue id,  CodePackage? sourceCodePackage,  List<SdkPackageApiPackage> apiPackages,  List<SdkPackageImplementationPackage> implementationPackages,  List<SdkPackageObjectConfigGraphPackage> objectConfigGraphPackages,  List<SdkPackageDependency> sdkPackageDependencies,  SdkConfig? sdkConfig,  ObjectInstanceGraphCommit? sdkConfigObjectInstanceGraphCommit,  int awareSdkVersion,  String compilationMode,  List<dynamic> dependencies,  String? description,  List<dynamic> excludePaths,  bool forceFreshScan,  String? fqnPrefix,  List<dynamic> includePaths,  String? manifestRelativePath,  String name,  String packageRoot,  String sourcesRoot,  Map<String, dynamic> targets,  String? title,  int versionNumber, @UuidValueConverter()  UuidValue? sourceCodePackageId, @UuidValueConverter()  UuidValue? sdkConfigId, @UuidValueConverter()  UuidValue? sdkConfigObjectInstanceGraphCommitId)  def,}) {final _that = this;
switch (_that) {
case _SdkPackage():
return def(_that.id,_that.sourceCodePackage,_that.apiPackages,_that.implementationPackages,_that.objectConfigGraphPackages,_that.sdkPackageDependencies,_that.sdkConfig,_that.sdkConfigObjectInstanceGraphCommit,_that.awareSdkVersion,_that.compilationMode,_that.dependencies,_that.description,_that.excludePaths,_that.forceFreshScan,_that.fqnPrefix,_that.includePaths,_that.manifestRelativePath,_that.name,_that.packageRoot,_that.sourcesRoot,_that.targets,_that.title,_that.versionNumber,_that.sourceCodePackageId,_that.sdkConfigId,_that.sdkConfigObjectInstanceGraphCommitId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue id,  CodePackage? sourceCodePackage,  List<SdkPackageApiPackage> apiPackages,  List<SdkPackageImplementationPackage> implementationPackages,  List<SdkPackageObjectConfigGraphPackage> objectConfigGraphPackages,  List<SdkPackageDependency> sdkPackageDependencies,  SdkConfig? sdkConfig,  ObjectInstanceGraphCommit? sdkConfigObjectInstanceGraphCommit,  int awareSdkVersion,  String compilationMode,  List<dynamic> dependencies,  String? description,  List<dynamic> excludePaths,  bool forceFreshScan,  String? fqnPrefix,  List<dynamic> includePaths,  String? manifestRelativePath,  String name,  String packageRoot,  String sourcesRoot,  Map<String, dynamic> targets,  String? title,  int versionNumber, @UuidValueConverter()  UuidValue? sourceCodePackageId, @UuidValueConverter()  UuidValue? sdkConfigId, @UuidValueConverter()  UuidValue? sdkConfigObjectInstanceGraphCommitId)?  def,}) {final _that = this;
switch (_that) {
case _SdkPackage() when def != null:
return def(_that.id,_that.sourceCodePackage,_that.apiPackages,_that.implementationPackages,_that.objectConfigGraphPackages,_that.sdkPackageDependencies,_that.sdkConfig,_that.sdkConfigObjectInstanceGraphCommit,_that.awareSdkVersion,_that.compilationMode,_that.dependencies,_that.description,_that.excludePaths,_that.forceFreshScan,_that.fqnPrefix,_that.includePaths,_that.manifestRelativePath,_that.name,_that.packageRoot,_that.sourcesRoot,_that.targets,_that.title,_that.versionNumber,_that.sourceCodePackageId,_that.sdkConfigId,_that.sdkConfigObjectInstanceGraphCommitId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _SdkPackage implements SdkPackage {
   _SdkPackage({@UuidValueConverter() required this.id, this.sourceCodePackage, final  List<SdkPackageApiPackage> apiPackages = const [], final  List<SdkPackageImplementationPackage> implementationPackages = const [], final  List<SdkPackageObjectConfigGraphPackage> objectConfigGraphPackages = const [], final  List<SdkPackageDependency> sdkPackageDependencies = const [], this.sdkConfig, this.sdkConfigObjectInstanceGraphCommit, required this.awareSdkVersion, required this.compilationMode, required final  List<dynamic> dependencies, this.description, required final  List<dynamic> excludePaths, required this.forceFreshScan, this.fqnPrefix, required final  List<dynamic> includePaths, this.manifestRelativePath, required this.name, required this.packageRoot, required this.sourcesRoot, required final  Map<String, dynamic> targets, this.title, required this.versionNumber, @UuidValueConverter() this.sourceCodePackageId, @UuidValueConverter() this.sdkConfigId, @UuidValueConverter() this.sdkConfigObjectInstanceGraphCommitId}): _apiPackages = apiPackages,_implementationPackages = implementationPackages,_objectConfigGraphPackages = objectConfigGraphPackages,_sdkPackageDependencies = sdkPackageDependencies,_dependencies = dependencies,_excludePaths = excludePaths,_includePaths = includePaths,_targets = targets;
  factory _SdkPackage.fromJson(Map<String, dynamic> json) => _$SdkPackageFromJson(json);

@override@UuidValueConverter() final  UuidValue id;
@override final  CodePackage? sourceCodePackage;
 final  List<SdkPackageApiPackage> _apiPackages;
@override@JsonKey() List<SdkPackageApiPackage> get apiPackages {
  if (_apiPackages is EqualUnmodifiableListView) return _apiPackages;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_apiPackages);
}

 final  List<SdkPackageImplementationPackage> _implementationPackages;
@override@JsonKey() List<SdkPackageImplementationPackage> get implementationPackages {
  if (_implementationPackages is EqualUnmodifiableListView) return _implementationPackages;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_implementationPackages);
}

 final  List<SdkPackageObjectConfigGraphPackage> _objectConfigGraphPackages;
@override@JsonKey() List<SdkPackageObjectConfigGraphPackage> get objectConfigGraphPackages {
  if (_objectConfigGraphPackages is EqualUnmodifiableListView) return _objectConfigGraphPackages;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_objectConfigGraphPackages);
}

 final  List<SdkPackageDependency> _sdkPackageDependencies;
@override@JsonKey() List<SdkPackageDependency> get sdkPackageDependencies {
  if (_sdkPackageDependencies is EqualUnmodifiableListView) return _sdkPackageDependencies;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_sdkPackageDependencies);
}

@override final  SdkConfig? sdkConfig;
@override final  ObjectInstanceGraphCommit? sdkConfigObjectInstanceGraphCommit;
@override final  int awareSdkVersion;
@override final  String compilationMode;
 final  List<dynamic> _dependencies;
@override List<dynamic> get dependencies {
  if (_dependencies is EqualUnmodifiableListView) return _dependencies;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_dependencies);
}

@override final  String? description;
 final  List<dynamic> _excludePaths;
@override List<dynamic> get excludePaths {
  if (_excludePaths is EqualUnmodifiableListView) return _excludePaths;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_excludePaths);
}

@override final  bool forceFreshScan;
@override final  String? fqnPrefix;
 final  List<dynamic> _includePaths;
@override List<dynamic> get includePaths {
  if (_includePaths is EqualUnmodifiableListView) return _includePaths;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_includePaths);
}

@override final  String? manifestRelativePath;
@override final  String name;
@override final  String packageRoot;
@override final  String sourcesRoot;
 final  Map<String, dynamic> _targets;
@override Map<String, dynamic> get targets {
  if (_targets is EqualUnmodifiableMapView) return _targets;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_targets);
}

@override final  String? title;
@override final  int versionNumber;
@override@UuidValueConverter() final  UuidValue? sourceCodePackageId;
@override@UuidValueConverter() final  UuidValue? sdkConfigId;
@override@UuidValueConverter() final  UuidValue? sdkConfigObjectInstanceGraphCommitId;

/// Create a copy of SdkPackage
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$SdkPackageCopyWith<_SdkPackage> get copyWith => __$SdkPackageCopyWithImpl<_SdkPackage>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$SdkPackageToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _SdkPackage&&(identical(other.id, id) || other.id == id)&&(identical(other.sourceCodePackage, sourceCodePackage) || other.sourceCodePackage == sourceCodePackage)&&const DeepCollectionEquality().equals(other._apiPackages, _apiPackages)&&const DeepCollectionEquality().equals(other._implementationPackages, _implementationPackages)&&const DeepCollectionEquality().equals(other._objectConfigGraphPackages, _objectConfigGraphPackages)&&const DeepCollectionEquality().equals(other._sdkPackageDependencies, _sdkPackageDependencies)&&(identical(other.sdkConfig, sdkConfig) || other.sdkConfig == sdkConfig)&&(identical(other.sdkConfigObjectInstanceGraphCommit, sdkConfigObjectInstanceGraphCommit) || other.sdkConfigObjectInstanceGraphCommit == sdkConfigObjectInstanceGraphCommit)&&(identical(other.awareSdkVersion, awareSdkVersion) || other.awareSdkVersion == awareSdkVersion)&&(identical(other.compilationMode, compilationMode) || other.compilationMode == compilationMode)&&const DeepCollectionEquality().equals(other._dependencies, _dependencies)&&(identical(other.description, description) || other.description == description)&&const DeepCollectionEquality().equals(other._excludePaths, _excludePaths)&&(identical(other.forceFreshScan, forceFreshScan) || other.forceFreshScan == forceFreshScan)&&(identical(other.fqnPrefix, fqnPrefix) || other.fqnPrefix == fqnPrefix)&&const DeepCollectionEquality().equals(other._includePaths, _includePaths)&&(identical(other.manifestRelativePath, manifestRelativePath) || other.manifestRelativePath == manifestRelativePath)&&(identical(other.name, name) || other.name == name)&&(identical(other.packageRoot, packageRoot) || other.packageRoot == packageRoot)&&(identical(other.sourcesRoot, sourcesRoot) || other.sourcesRoot == sourcesRoot)&&const DeepCollectionEquality().equals(other._targets, _targets)&&(identical(other.title, title) || other.title == title)&&(identical(other.versionNumber, versionNumber) || other.versionNumber == versionNumber)&&(identical(other.sourceCodePackageId, sourceCodePackageId) || other.sourceCodePackageId == sourceCodePackageId)&&(identical(other.sdkConfigId, sdkConfigId) || other.sdkConfigId == sdkConfigId)&&(identical(other.sdkConfigObjectInstanceGraphCommitId, sdkConfigObjectInstanceGraphCommitId) || other.sdkConfigObjectInstanceGraphCommitId == sdkConfigObjectInstanceGraphCommitId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,id,sourceCodePackage,const DeepCollectionEquality().hash(_apiPackages),const DeepCollectionEquality().hash(_implementationPackages),const DeepCollectionEquality().hash(_objectConfigGraphPackages),const DeepCollectionEquality().hash(_sdkPackageDependencies),sdkConfig,sdkConfigObjectInstanceGraphCommit,awareSdkVersion,compilationMode,const DeepCollectionEquality().hash(_dependencies),description,const DeepCollectionEquality().hash(_excludePaths),forceFreshScan,fqnPrefix,const DeepCollectionEquality().hash(_includePaths),manifestRelativePath,name,packageRoot,sourcesRoot,const DeepCollectionEquality().hash(_targets),title,versionNumber,sourceCodePackageId,sdkConfigId,sdkConfigObjectInstanceGraphCommitId]);

@override
String toString() {
  return 'SdkPackage.def(id: $id, sourceCodePackage: $sourceCodePackage, apiPackages: $apiPackages, implementationPackages: $implementationPackages, objectConfigGraphPackages: $objectConfigGraphPackages, sdkPackageDependencies: $sdkPackageDependencies, sdkConfig: $sdkConfig, sdkConfigObjectInstanceGraphCommit: $sdkConfigObjectInstanceGraphCommit, awareSdkVersion: $awareSdkVersion, compilationMode: $compilationMode, dependencies: $dependencies, description: $description, excludePaths: $excludePaths, forceFreshScan: $forceFreshScan, fqnPrefix: $fqnPrefix, includePaths: $includePaths, manifestRelativePath: $manifestRelativePath, name: $name, packageRoot: $packageRoot, sourcesRoot: $sourcesRoot, targets: $targets, title: $title, versionNumber: $versionNumber, sourceCodePackageId: $sourceCodePackageId, sdkConfigId: $sdkConfigId, sdkConfigObjectInstanceGraphCommitId: $sdkConfigObjectInstanceGraphCommitId)';
}


}

/// @nodoc
abstract mixin class _$SdkPackageCopyWith<$Res> implements $SdkPackageCopyWith<$Res> {
  factory _$SdkPackageCopyWith(_SdkPackage value, $Res Function(_SdkPackage) _then) = __$SdkPackageCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue id, CodePackage? sourceCodePackage, List<SdkPackageApiPackage> apiPackages, List<SdkPackageImplementationPackage> implementationPackages, List<SdkPackageObjectConfigGraphPackage> objectConfigGraphPackages, List<SdkPackageDependency> sdkPackageDependencies, SdkConfig? sdkConfig, ObjectInstanceGraphCommit? sdkConfigObjectInstanceGraphCommit, int awareSdkVersion, String compilationMode, List<dynamic> dependencies, String? description, List<dynamic> excludePaths, bool forceFreshScan, String? fqnPrefix, List<dynamic> includePaths, String? manifestRelativePath, String name, String packageRoot, String sourcesRoot, Map<String, dynamic> targets, String? title, int versionNumber,@UuidValueConverter() UuidValue? sourceCodePackageId,@UuidValueConverter() UuidValue? sdkConfigId,@UuidValueConverter() UuidValue? sdkConfigObjectInstanceGraphCommitId
});


@override $CodePackageCopyWith<$Res>? get sourceCodePackage;@override $SdkConfigCopyWith<$Res>? get sdkConfig;@override $ObjectInstanceGraphCommitCopyWith<$Res>? get sdkConfigObjectInstanceGraphCommit;

}
/// @nodoc
class __$SdkPackageCopyWithImpl<$Res>
    implements _$SdkPackageCopyWith<$Res> {
  __$SdkPackageCopyWithImpl(this._self, this._then);

  final _SdkPackage _self;
  final $Res Function(_SdkPackage) _then;

/// Create a copy of SdkPackage
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? id = null,Object? sourceCodePackage = freezed,Object? apiPackages = null,Object? implementationPackages = null,Object? objectConfigGraphPackages = null,Object? sdkPackageDependencies = null,Object? sdkConfig = freezed,Object? sdkConfigObjectInstanceGraphCommit = freezed,Object? awareSdkVersion = null,Object? compilationMode = null,Object? dependencies = null,Object? description = freezed,Object? excludePaths = null,Object? forceFreshScan = null,Object? fqnPrefix = freezed,Object? includePaths = null,Object? manifestRelativePath = freezed,Object? name = null,Object? packageRoot = null,Object? sourcesRoot = null,Object? targets = null,Object? title = freezed,Object? versionNumber = null,Object? sourceCodePackageId = freezed,Object? sdkConfigId = freezed,Object? sdkConfigObjectInstanceGraphCommitId = freezed,}) {
  return _then(_SdkPackage(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,sourceCodePackage: freezed == sourceCodePackage ? _self.sourceCodePackage : sourceCodePackage // ignore: cast_nullable_to_non_nullable
as CodePackage?,apiPackages: null == apiPackages ? _self._apiPackages : apiPackages // ignore: cast_nullable_to_non_nullable
as List<SdkPackageApiPackage>,implementationPackages: null == implementationPackages ? _self._implementationPackages : implementationPackages // ignore: cast_nullable_to_non_nullable
as List<SdkPackageImplementationPackage>,objectConfigGraphPackages: null == objectConfigGraphPackages ? _self._objectConfigGraphPackages : objectConfigGraphPackages // ignore: cast_nullable_to_non_nullable
as List<SdkPackageObjectConfigGraphPackage>,sdkPackageDependencies: null == sdkPackageDependencies ? _self._sdkPackageDependencies : sdkPackageDependencies // ignore: cast_nullable_to_non_nullable
as List<SdkPackageDependency>,sdkConfig: freezed == sdkConfig ? _self.sdkConfig : sdkConfig // ignore: cast_nullable_to_non_nullable
as SdkConfig?,sdkConfigObjectInstanceGraphCommit: freezed == sdkConfigObjectInstanceGraphCommit ? _self.sdkConfigObjectInstanceGraphCommit : sdkConfigObjectInstanceGraphCommit // ignore: cast_nullable_to_non_nullable
as ObjectInstanceGraphCommit?,awareSdkVersion: null == awareSdkVersion ? _self.awareSdkVersion : awareSdkVersion // ignore: cast_nullable_to_non_nullable
as int,compilationMode: null == compilationMode ? _self.compilationMode : compilationMode // ignore: cast_nullable_to_non_nullable
as String,dependencies: null == dependencies ? _self._dependencies : dependencies // ignore: cast_nullable_to_non_nullable
as List<dynamic>,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,excludePaths: null == excludePaths ? _self._excludePaths : excludePaths // ignore: cast_nullable_to_non_nullable
as List<dynamic>,forceFreshScan: null == forceFreshScan ? _self.forceFreshScan : forceFreshScan // ignore: cast_nullable_to_non_nullable
as bool,fqnPrefix: freezed == fqnPrefix ? _self.fqnPrefix : fqnPrefix // ignore: cast_nullable_to_non_nullable
as String?,includePaths: null == includePaths ? _self._includePaths : includePaths // ignore: cast_nullable_to_non_nullable
as List<dynamic>,manifestRelativePath: freezed == manifestRelativePath ? _self.manifestRelativePath : manifestRelativePath // ignore: cast_nullable_to_non_nullable
as String?,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,packageRoot: null == packageRoot ? _self.packageRoot : packageRoot // ignore: cast_nullable_to_non_nullable
as String,sourcesRoot: null == sourcesRoot ? _self.sourcesRoot : sourcesRoot // ignore: cast_nullable_to_non_nullable
as String,targets: null == targets ? _self._targets : targets // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,versionNumber: null == versionNumber ? _self.versionNumber : versionNumber // ignore: cast_nullable_to_non_nullable
as int,sourceCodePackageId: freezed == sourceCodePackageId ? _self.sourceCodePackageId : sourceCodePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sdkConfigId: freezed == sdkConfigId ? _self.sdkConfigId : sdkConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sdkConfigObjectInstanceGraphCommitId: freezed == sdkConfigObjectInstanceGraphCommitId ? _self.sdkConfigObjectInstanceGraphCommitId : sdkConfigObjectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

/// Create a copy of SdkPackage
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageCopyWith<$Res>? get sourceCodePackage {
    if (_self.sourceCodePackage == null) {
    return null;
  }

  return $CodePackageCopyWith<$Res>(_self.sourceCodePackage!, (value) {
    return _then(_self.copyWith(sourceCodePackage: value));
  });
}/// Create a copy of SdkPackage
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$SdkConfigCopyWith<$Res>? get sdkConfig {
    if (_self.sdkConfig == null) {
    return null;
  }

  return $SdkConfigCopyWith<$Res>(_self.sdkConfig!, (value) {
    return _then(_self.copyWith(sdkConfig: value));
  });
}/// Create a copy of SdkPackage
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ObjectInstanceGraphCommitCopyWith<$Res>? get sdkConfigObjectInstanceGraphCommit {
    if (_self.sdkConfigObjectInstanceGraphCommit == null) {
    return null;
  }

  return $ObjectInstanceGraphCommitCopyWith<$Res>(_self.sdkConfigObjectInstanceGraphCommit!, (value) {
    return _then(_self.copyWith(sdkConfigObjectInstanceGraphCommit: value));
  });
}
}

// dart format on
