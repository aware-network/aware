// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'channel_heads_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$HubPublicDiscoveryDescriptorV1 {

 String? get packageName; String? get language; String? get surface; String? get manifestKind; String? get version; String? get revisionId; String? get digest; String? get packageRoot; String? get sourcesRoot; String? get fqnPrefix; String? get manifestRelativePath; String? get artifactMediaType; int? get artifactSizeBytes; String? get downloadHandle; Map<String, dynamic> get metadata;
/// Create a copy of HubPublicDiscoveryDescriptorV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$HubPublicDiscoveryDescriptorV1CopyWith<HubPublicDiscoveryDescriptorV1> get copyWith => _$HubPublicDiscoveryDescriptorV1CopyWithImpl<HubPublicDiscoveryDescriptorV1>(this as HubPublicDiscoveryDescriptorV1, _$identity);

  /// Serializes this HubPublicDiscoveryDescriptorV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is HubPublicDiscoveryDescriptorV1&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.language, language) || other.language == language)&&(identical(other.surface, surface) || other.surface == surface)&&(identical(other.manifestKind, manifestKind) || other.manifestKind == manifestKind)&&(identical(other.version, version) || other.version == version)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.packageRoot, packageRoot) || other.packageRoot == packageRoot)&&(identical(other.sourcesRoot, sourcesRoot) || other.sourcesRoot == sourcesRoot)&&(identical(other.fqnPrefix, fqnPrefix) || other.fqnPrefix == fqnPrefix)&&(identical(other.manifestRelativePath, manifestRelativePath) || other.manifestRelativePath == manifestRelativePath)&&(identical(other.artifactMediaType, artifactMediaType) || other.artifactMediaType == artifactMediaType)&&(identical(other.artifactSizeBytes, artifactSizeBytes) || other.artifactSizeBytes == artifactSizeBytes)&&(identical(other.downloadHandle, downloadHandle) || other.downloadHandle == downloadHandle)&&const DeepCollectionEquality().equals(other.metadata, metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,packageName,language,surface,manifestKind,version,revisionId,digest,packageRoot,sourcesRoot,fqnPrefix,manifestRelativePath,artifactMediaType,artifactSizeBytes,downloadHandle,const DeepCollectionEquality().hash(metadata));

@override
String toString() {
  return 'HubPublicDiscoveryDescriptorV1(packageName: $packageName, language: $language, surface: $surface, manifestKind: $manifestKind, version: $version, revisionId: $revisionId, digest: $digest, packageRoot: $packageRoot, sourcesRoot: $sourcesRoot, fqnPrefix: $fqnPrefix, manifestRelativePath: $manifestRelativePath, artifactMediaType: $artifactMediaType, artifactSizeBytes: $artifactSizeBytes, downloadHandle: $downloadHandle, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class $HubPublicDiscoveryDescriptorV1CopyWith<$Res>  {
  factory $HubPublicDiscoveryDescriptorV1CopyWith(HubPublicDiscoveryDescriptorV1 value, $Res Function(HubPublicDiscoveryDescriptorV1) _then) = _$HubPublicDiscoveryDescriptorV1CopyWithImpl;
@useResult
$Res call({
 String? packageName, String? language, String? surface, String? manifestKind, String? version, String? revisionId, String? digest, String? packageRoot, String? sourcesRoot, String? fqnPrefix, String? manifestRelativePath, String? artifactMediaType, int? artifactSizeBytes, String? downloadHandle, Map<String, dynamic> metadata
});




}
/// @nodoc
class _$HubPublicDiscoveryDescriptorV1CopyWithImpl<$Res>
    implements $HubPublicDiscoveryDescriptorV1CopyWith<$Res> {
  _$HubPublicDiscoveryDescriptorV1CopyWithImpl(this._self, this._then);

  final HubPublicDiscoveryDescriptorV1 _self;
  final $Res Function(HubPublicDiscoveryDescriptorV1) _then;

/// Create a copy of HubPublicDiscoveryDescriptorV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? packageName = freezed,Object? language = freezed,Object? surface = freezed,Object? manifestKind = freezed,Object? version = freezed,Object? revisionId = freezed,Object? digest = freezed,Object? packageRoot = freezed,Object? sourcesRoot = freezed,Object? fqnPrefix = freezed,Object? manifestRelativePath = freezed,Object? artifactMediaType = freezed,Object? artifactSizeBytes = freezed,Object? downloadHandle = freezed,Object? metadata = null,}) {
  return _then(_self.copyWith(
packageName: freezed == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String?,language: freezed == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as String?,surface: freezed == surface ? _self.surface : surface // ignore: cast_nullable_to_non_nullable
as String?,manifestKind: freezed == manifestKind ? _self.manifestKind : manifestKind // ignore: cast_nullable_to_non_nullable
as String?,version: freezed == version ? _self.version : version // ignore: cast_nullable_to_non_nullable
as String?,revisionId: freezed == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String?,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,packageRoot: freezed == packageRoot ? _self.packageRoot : packageRoot // ignore: cast_nullable_to_non_nullable
as String?,sourcesRoot: freezed == sourcesRoot ? _self.sourcesRoot : sourcesRoot // ignore: cast_nullable_to_non_nullable
as String?,fqnPrefix: freezed == fqnPrefix ? _self.fqnPrefix : fqnPrefix // ignore: cast_nullable_to_non_nullable
as String?,manifestRelativePath: freezed == manifestRelativePath ? _self.manifestRelativePath : manifestRelativePath // ignore: cast_nullable_to_non_nullable
as String?,artifactMediaType: freezed == artifactMediaType ? _self.artifactMediaType : artifactMediaType // ignore: cast_nullable_to_non_nullable
as String?,artifactSizeBytes: freezed == artifactSizeBytes ? _self.artifactSizeBytes : artifactSizeBytes // ignore: cast_nullable_to_non_nullable
as int?,downloadHandle: freezed == downloadHandle ? _self.downloadHandle : downloadHandle // ignore: cast_nullable_to_non_nullable
as String?,metadata: null == metadata ? _self.metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [HubPublicDiscoveryDescriptorV1].
extension HubPublicDiscoveryDescriptorV1Patterns on HubPublicDiscoveryDescriptorV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _HubPublicDiscoveryDescriptorV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _HubPublicDiscoveryDescriptorV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _HubPublicDiscoveryDescriptorV1 value)  def,}){
final _that = this;
switch (_that) {
case _HubPublicDiscoveryDescriptorV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _HubPublicDiscoveryDescriptorV1 value)?  def,}){
final _that = this;
switch (_that) {
case _HubPublicDiscoveryDescriptorV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String? packageName,  String? language,  String? surface,  String? manifestKind,  String? version,  String? revisionId,  String? digest,  String? packageRoot,  String? sourcesRoot,  String? fqnPrefix,  String? manifestRelativePath,  String? artifactMediaType,  int? artifactSizeBytes,  String? downloadHandle,  Map<String, dynamic> metadata)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _HubPublicDiscoveryDescriptorV1() when def != null:
return def(_that.packageName,_that.language,_that.surface,_that.manifestKind,_that.version,_that.revisionId,_that.digest,_that.packageRoot,_that.sourcesRoot,_that.fqnPrefix,_that.manifestRelativePath,_that.artifactMediaType,_that.artifactSizeBytes,_that.downloadHandle,_that.metadata);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String? packageName,  String? language,  String? surface,  String? manifestKind,  String? version,  String? revisionId,  String? digest,  String? packageRoot,  String? sourcesRoot,  String? fqnPrefix,  String? manifestRelativePath,  String? artifactMediaType,  int? artifactSizeBytes,  String? downloadHandle,  Map<String, dynamic> metadata)  def,}) {final _that = this;
switch (_that) {
case _HubPublicDiscoveryDescriptorV1():
return def(_that.packageName,_that.language,_that.surface,_that.manifestKind,_that.version,_that.revisionId,_that.digest,_that.packageRoot,_that.sourcesRoot,_that.fqnPrefix,_that.manifestRelativePath,_that.artifactMediaType,_that.artifactSizeBytes,_that.downloadHandle,_that.metadata);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String? packageName,  String? language,  String? surface,  String? manifestKind,  String? version,  String? revisionId,  String? digest,  String? packageRoot,  String? sourcesRoot,  String? fqnPrefix,  String? manifestRelativePath,  String? artifactMediaType,  int? artifactSizeBytes,  String? downloadHandle,  Map<String, dynamic> metadata)?  def,}) {final _that = this;
switch (_that) {
case _HubPublicDiscoveryDescriptorV1() when def != null:
return def(_that.packageName,_that.language,_that.surface,_that.manifestKind,_that.version,_that.revisionId,_that.digest,_that.packageRoot,_that.sourcesRoot,_that.fqnPrefix,_that.manifestRelativePath,_that.artifactMediaType,_that.artifactSizeBytes,_that.downloadHandle,_that.metadata);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _HubPublicDiscoveryDescriptorV1 implements HubPublicDiscoveryDescriptorV1 {
   _HubPublicDiscoveryDescriptorV1({this.packageName, this.language, this.surface, this.manifestKind, this.version, this.revisionId, this.digest, this.packageRoot, this.sourcesRoot, this.fqnPrefix, this.manifestRelativePath, this.artifactMediaType, this.artifactSizeBytes, this.downloadHandle, required final  Map<String, dynamic> metadata}): _metadata = metadata;
  factory _HubPublicDiscoveryDescriptorV1.fromJson(Map<String, dynamic> json) => _$HubPublicDiscoveryDescriptorV1FromJson(json);

@override final  String? packageName;
@override final  String? language;
@override final  String? surface;
@override final  String? manifestKind;
@override final  String? version;
@override final  String? revisionId;
@override final  String? digest;
@override final  String? packageRoot;
@override final  String? sourcesRoot;
@override final  String? fqnPrefix;
@override final  String? manifestRelativePath;
@override final  String? artifactMediaType;
@override final  int? artifactSizeBytes;
@override final  String? downloadHandle;
 final  Map<String, dynamic> _metadata;
@override Map<String, dynamic> get metadata {
  if (_metadata is EqualUnmodifiableMapView) return _metadata;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_metadata);
}


/// Create a copy of HubPublicDiscoveryDescriptorV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$HubPublicDiscoveryDescriptorV1CopyWith<_HubPublicDiscoveryDescriptorV1> get copyWith => __$HubPublicDiscoveryDescriptorV1CopyWithImpl<_HubPublicDiscoveryDescriptorV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$HubPublicDiscoveryDescriptorV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _HubPublicDiscoveryDescriptorV1&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.language, language) || other.language == language)&&(identical(other.surface, surface) || other.surface == surface)&&(identical(other.manifestKind, manifestKind) || other.manifestKind == manifestKind)&&(identical(other.version, version) || other.version == version)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.packageRoot, packageRoot) || other.packageRoot == packageRoot)&&(identical(other.sourcesRoot, sourcesRoot) || other.sourcesRoot == sourcesRoot)&&(identical(other.fqnPrefix, fqnPrefix) || other.fqnPrefix == fqnPrefix)&&(identical(other.manifestRelativePath, manifestRelativePath) || other.manifestRelativePath == manifestRelativePath)&&(identical(other.artifactMediaType, artifactMediaType) || other.artifactMediaType == artifactMediaType)&&(identical(other.artifactSizeBytes, artifactSizeBytes) || other.artifactSizeBytes == artifactSizeBytes)&&(identical(other.downloadHandle, downloadHandle) || other.downloadHandle == downloadHandle)&&const DeepCollectionEquality().equals(other._metadata, _metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,packageName,language,surface,manifestKind,version,revisionId,digest,packageRoot,sourcesRoot,fqnPrefix,manifestRelativePath,artifactMediaType,artifactSizeBytes,downloadHandle,const DeepCollectionEquality().hash(_metadata));

@override
String toString() {
  return 'HubPublicDiscoveryDescriptorV1.def(packageName: $packageName, language: $language, surface: $surface, manifestKind: $manifestKind, version: $version, revisionId: $revisionId, digest: $digest, packageRoot: $packageRoot, sourcesRoot: $sourcesRoot, fqnPrefix: $fqnPrefix, manifestRelativePath: $manifestRelativePath, artifactMediaType: $artifactMediaType, artifactSizeBytes: $artifactSizeBytes, downloadHandle: $downloadHandle, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class _$HubPublicDiscoveryDescriptorV1CopyWith<$Res> implements $HubPublicDiscoveryDescriptorV1CopyWith<$Res> {
  factory _$HubPublicDiscoveryDescriptorV1CopyWith(_HubPublicDiscoveryDescriptorV1 value, $Res Function(_HubPublicDiscoveryDescriptorV1) _then) = __$HubPublicDiscoveryDescriptorV1CopyWithImpl;
@override @useResult
$Res call({
 String? packageName, String? language, String? surface, String? manifestKind, String? version, String? revisionId, String? digest, String? packageRoot, String? sourcesRoot, String? fqnPrefix, String? manifestRelativePath, String? artifactMediaType, int? artifactSizeBytes, String? downloadHandle, Map<String, dynamic> metadata
});




}
/// @nodoc
class __$HubPublicDiscoveryDescriptorV1CopyWithImpl<$Res>
    implements _$HubPublicDiscoveryDescriptorV1CopyWith<$Res> {
  __$HubPublicDiscoveryDescriptorV1CopyWithImpl(this._self, this._then);

  final _HubPublicDiscoveryDescriptorV1 _self;
  final $Res Function(_HubPublicDiscoveryDescriptorV1) _then;

/// Create a copy of HubPublicDiscoveryDescriptorV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? packageName = freezed,Object? language = freezed,Object? surface = freezed,Object? manifestKind = freezed,Object? version = freezed,Object? revisionId = freezed,Object? digest = freezed,Object? packageRoot = freezed,Object? sourcesRoot = freezed,Object? fqnPrefix = freezed,Object? manifestRelativePath = freezed,Object? artifactMediaType = freezed,Object? artifactSizeBytes = freezed,Object? downloadHandle = freezed,Object? metadata = null,}) {
  return _then(_HubPublicDiscoveryDescriptorV1(
packageName: freezed == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String?,language: freezed == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as String?,surface: freezed == surface ? _self.surface : surface // ignore: cast_nullable_to_non_nullable
as String?,manifestKind: freezed == manifestKind ? _self.manifestKind : manifestKind // ignore: cast_nullable_to_non_nullable
as String?,version: freezed == version ? _self.version : version // ignore: cast_nullable_to_non_nullable
as String?,revisionId: freezed == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String?,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,packageRoot: freezed == packageRoot ? _self.packageRoot : packageRoot // ignore: cast_nullable_to_non_nullable
as String?,sourcesRoot: freezed == sourcesRoot ? _self.sourcesRoot : sourcesRoot // ignore: cast_nullable_to_non_nullable
as String?,fqnPrefix: freezed == fqnPrefix ? _self.fqnPrefix : fqnPrefix // ignore: cast_nullable_to_non_nullable
as String?,manifestRelativePath: freezed == manifestRelativePath ? _self.manifestRelativePath : manifestRelativePath // ignore: cast_nullable_to_non_nullable
as String?,artifactMediaType: freezed == artifactMediaType ? _self.artifactMediaType : artifactMediaType // ignore: cast_nullable_to_non_nullable
as String?,artifactSizeBytes: freezed == artifactSizeBytes ? _self.artifactSizeBytes : artifactSizeBytes // ignore: cast_nullable_to_non_nullable
as int?,downloadHandle: freezed == downloadHandle ? _self.downloadHandle : downloadHandle // ignore: cast_nullable_to_non_nullable
as String?,metadata: null == metadata ? _self._metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$HubPublicDiscoveryArtifactLockV1 {

 String? get artifactUrl; String? get sha256; int? get sizeBytes; String? get mediaType; String? get archiveFormat; String? get revisionId; String? get publishedAt;
/// Create a copy of HubPublicDiscoveryArtifactLockV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$HubPublicDiscoveryArtifactLockV1CopyWith<HubPublicDiscoveryArtifactLockV1> get copyWith => _$HubPublicDiscoveryArtifactLockV1CopyWithImpl<HubPublicDiscoveryArtifactLockV1>(this as HubPublicDiscoveryArtifactLockV1, _$identity);

  /// Serializes this HubPublicDiscoveryArtifactLockV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is HubPublicDiscoveryArtifactLockV1&&(identical(other.artifactUrl, artifactUrl) || other.artifactUrl == artifactUrl)&&(identical(other.sha256, sha256) || other.sha256 == sha256)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.archiveFormat, archiveFormat) || other.archiveFormat == archiveFormat)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.publishedAt, publishedAt) || other.publishedAt == publishedAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,artifactUrl,sha256,sizeBytes,mediaType,archiveFormat,revisionId,publishedAt);

@override
String toString() {
  return 'HubPublicDiscoveryArtifactLockV1(artifactUrl: $artifactUrl, sha256: $sha256, sizeBytes: $sizeBytes, mediaType: $mediaType, archiveFormat: $archiveFormat, revisionId: $revisionId, publishedAt: $publishedAt)';
}


}

/// @nodoc
abstract mixin class $HubPublicDiscoveryArtifactLockV1CopyWith<$Res>  {
  factory $HubPublicDiscoveryArtifactLockV1CopyWith(HubPublicDiscoveryArtifactLockV1 value, $Res Function(HubPublicDiscoveryArtifactLockV1) _then) = _$HubPublicDiscoveryArtifactLockV1CopyWithImpl;
@useResult
$Res call({
 String? artifactUrl, String? sha256, int? sizeBytes, String? mediaType, String? archiveFormat, String? revisionId, String? publishedAt
});




}
/// @nodoc
class _$HubPublicDiscoveryArtifactLockV1CopyWithImpl<$Res>
    implements $HubPublicDiscoveryArtifactLockV1CopyWith<$Res> {
  _$HubPublicDiscoveryArtifactLockV1CopyWithImpl(this._self, this._then);

  final HubPublicDiscoveryArtifactLockV1 _self;
  final $Res Function(HubPublicDiscoveryArtifactLockV1) _then;

/// Create a copy of HubPublicDiscoveryArtifactLockV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? artifactUrl = freezed,Object? sha256 = freezed,Object? sizeBytes = freezed,Object? mediaType = freezed,Object? archiveFormat = freezed,Object? revisionId = freezed,Object? publishedAt = freezed,}) {
  return _then(_self.copyWith(
artifactUrl: freezed == artifactUrl ? _self.artifactUrl : artifactUrl // ignore: cast_nullable_to_non_nullable
as String?,sha256: freezed == sha256 ? _self.sha256 : sha256 // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,mediaType: freezed == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String?,archiveFormat: freezed == archiveFormat ? _self.archiveFormat : archiveFormat // ignore: cast_nullable_to_non_nullable
as String?,revisionId: freezed == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String?,publishedAt: freezed == publishedAt ? _self.publishedAt : publishedAt // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [HubPublicDiscoveryArtifactLockV1].
extension HubPublicDiscoveryArtifactLockV1Patterns on HubPublicDiscoveryArtifactLockV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _HubPublicDiscoveryArtifactLockV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _HubPublicDiscoveryArtifactLockV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _HubPublicDiscoveryArtifactLockV1 value)  def,}){
final _that = this;
switch (_that) {
case _HubPublicDiscoveryArtifactLockV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _HubPublicDiscoveryArtifactLockV1 value)?  def,}){
final _that = this;
switch (_that) {
case _HubPublicDiscoveryArtifactLockV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String? artifactUrl,  String? sha256,  int? sizeBytes,  String? mediaType,  String? archiveFormat,  String? revisionId,  String? publishedAt)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _HubPublicDiscoveryArtifactLockV1() when def != null:
return def(_that.artifactUrl,_that.sha256,_that.sizeBytes,_that.mediaType,_that.archiveFormat,_that.revisionId,_that.publishedAt);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String? artifactUrl,  String? sha256,  int? sizeBytes,  String? mediaType,  String? archiveFormat,  String? revisionId,  String? publishedAt)  def,}) {final _that = this;
switch (_that) {
case _HubPublicDiscoveryArtifactLockV1():
return def(_that.artifactUrl,_that.sha256,_that.sizeBytes,_that.mediaType,_that.archiveFormat,_that.revisionId,_that.publishedAt);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String? artifactUrl,  String? sha256,  int? sizeBytes,  String? mediaType,  String? archiveFormat,  String? revisionId,  String? publishedAt)?  def,}) {final _that = this;
switch (_that) {
case _HubPublicDiscoveryArtifactLockV1() when def != null:
return def(_that.artifactUrl,_that.sha256,_that.sizeBytes,_that.mediaType,_that.archiveFormat,_that.revisionId,_that.publishedAt);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _HubPublicDiscoveryArtifactLockV1 implements HubPublicDiscoveryArtifactLockV1 {
   _HubPublicDiscoveryArtifactLockV1({this.artifactUrl, this.sha256, this.sizeBytes, this.mediaType, this.archiveFormat, this.revisionId, this.publishedAt});
  factory _HubPublicDiscoveryArtifactLockV1.fromJson(Map<String, dynamic> json) => _$HubPublicDiscoveryArtifactLockV1FromJson(json);

@override final  String? artifactUrl;
@override final  String? sha256;
@override final  int? sizeBytes;
@override final  String? mediaType;
@override final  String? archiveFormat;
@override final  String? revisionId;
@override final  String? publishedAt;

/// Create a copy of HubPublicDiscoveryArtifactLockV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$HubPublicDiscoveryArtifactLockV1CopyWith<_HubPublicDiscoveryArtifactLockV1> get copyWith => __$HubPublicDiscoveryArtifactLockV1CopyWithImpl<_HubPublicDiscoveryArtifactLockV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$HubPublicDiscoveryArtifactLockV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _HubPublicDiscoveryArtifactLockV1&&(identical(other.artifactUrl, artifactUrl) || other.artifactUrl == artifactUrl)&&(identical(other.sha256, sha256) || other.sha256 == sha256)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.archiveFormat, archiveFormat) || other.archiveFormat == archiveFormat)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.publishedAt, publishedAt) || other.publishedAt == publishedAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,artifactUrl,sha256,sizeBytes,mediaType,archiveFormat,revisionId,publishedAt);

@override
String toString() {
  return 'HubPublicDiscoveryArtifactLockV1.def(artifactUrl: $artifactUrl, sha256: $sha256, sizeBytes: $sizeBytes, mediaType: $mediaType, archiveFormat: $archiveFormat, revisionId: $revisionId, publishedAt: $publishedAt)';
}


}

/// @nodoc
abstract mixin class _$HubPublicDiscoveryArtifactLockV1CopyWith<$Res> implements $HubPublicDiscoveryArtifactLockV1CopyWith<$Res> {
  factory _$HubPublicDiscoveryArtifactLockV1CopyWith(_HubPublicDiscoveryArtifactLockV1 value, $Res Function(_HubPublicDiscoveryArtifactLockV1) _then) = __$HubPublicDiscoveryArtifactLockV1CopyWithImpl;
@override @useResult
$Res call({
 String? artifactUrl, String? sha256, int? sizeBytes, String? mediaType, String? archiveFormat, String? revisionId, String? publishedAt
});




}
/// @nodoc
class __$HubPublicDiscoveryArtifactLockV1CopyWithImpl<$Res>
    implements _$HubPublicDiscoveryArtifactLockV1CopyWith<$Res> {
  __$HubPublicDiscoveryArtifactLockV1CopyWithImpl(this._self, this._then);

  final _HubPublicDiscoveryArtifactLockV1 _self;
  final $Res Function(_HubPublicDiscoveryArtifactLockV1) _then;

/// Create a copy of HubPublicDiscoveryArtifactLockV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? artifactUrl = freezed,Object? sha256 = freezed,Object? sizeBytes = freezed,Object? mediaType = freezed,Object? archiveFormat = freezed,Object? revisionId = freezed,Object? publishedAt = freezed,}) {
  return _then(_HubPublicDiscoveryArtifactLockV1(
artifactUrl: freezed == artifactUrl ? _self.artifactUrl : artifactUrl // ignore: cast_nullable_to_non_nullable
as String?,sha256: freezed == sha256 ? _self.sha256 : sha256 // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,mediaType: freezed == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String?,archiveFormat: freezed == archiveFormat ? _self.archiveFormat : archiveFormat // ignore: cast_nullable_to_non_nullable
as String?,revisionId: freezed == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String?,publishedAt: freezed == publishedAt ? _self.publishedAt : publishedAt // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$HubPublicDiscoveryEntryV1 {

 String? get packageName; String? get language; String? get surface; String get channel; String? get revisionId; String? get updatedAt; String? get publisherExecutionId; String? get idempotencyKey; Map<String, dynamic> get metadata; HubPublicDiscoveryDescriptorV1? get descriptor; HubPublicDiscoveryArtifactLockV1? get artifactLock; Map<String, dynamic> get refs;
/// Create a copy of HubPublicDiscoveryEntryV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$HubPublicDiscoveryEntryV1CopyWith<HubPublicDiscoveryEntryV1> get copyWith => _$HubPublicDiscoveryEntryV1CopyWithImpl<HubPublicDiscoveryEntryV1>(this as HubPublicDiscoveryEntryV1, _$identity);

  /// Serializes this HubPublicDiscoveryEntryV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is HubPublicDiscoveryEntryV1&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.language, language) || other.language == language)&&(identical(other.surface, surface) || other.surface == surface)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.updatedAt, updatedAt) || other.updatedAt == updatedAt)&&(identical(other.publisherExecutionId, publisherExecutionId) || other.publisherExecutionId == publisherExecutionId)&&(identical(other.idempotencyKey, idempotencyKey) || other.idempotencyKey == idempotencyKey)&&const DeepCollectionEquality().equals(other.metadata, metadata)&&(identical(other.descriptor, descriptor) || other.descriptor == descriptor)&&(identical(other.artifactLock, artifactLock) || other.artifactLock == artifactLock)&&const DeepCollectionEquality().equals(other.refs, refs));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,packageName,language,surface,channel,revisionId,updatedAt,publisherExecutionId,idempotencyKey,const DeepCollectionEquality().hash(metadata),descriptor,artifactLock,const DeepCollectionEquality().hash(refs));

@override
String toString() {
  return 'HubPublicDiscoveryEntryV1(packageName: $packageName, language: $language, surface: $surface, channel: $channel, revisionId: $revisionId, updatedAt: $updatedAt, publisherExecutionId: $publisherExecutionId, idempotencyKey: $idempotencyKey, metadata: $metadata, descriptor: $descriptor, artifactLock: $artifactLock, refs: $refs)';
}


}

/// @nodoc
abstract mixin class $HubPublicDiscoveryEntryV1CopyWith<$Res>  {
  factory $HubPublicDiscoveryEntryV1CopyWith(HubPublicDiscoveryEntryV1 value, $Res Function(HubPublicDiscoveryEntryV1) _then) = _$HubPublicDiscoveryEntryV1CopyWithImpl;
@useResult
$Res call({
 String? packageName, String? language, String? surface, String channel, String? revisionId, String? updatedAt, String? publisherExecutionId, String? idempotencyKey, Map<String, dynamic> metadata, HubPublicDiscoveryDescriptorV1? descriptor, HubPublicDiscoveryArtifactLockV1? artifactLock, Map<String, dynamic> refs
});


$HubPublicDiscoveryDescriptorV1CopyWith<$Res>? get descriptor;$HubPublicDiscoveryArtifactLockV1CopyWith<$Res>? get artifactLock;

}
/// @nodoc
class _$HubPublicDiscoveryEntryV1CopyWithImpl<$Res>
    implements $HubPublicDiscoveryEntryV1CopyWith<$Res> {
  _$HubPublicDiscoveryEntryV1CopyWithImpl(this._self, this._then);

  final HubPublicDiscoveryEntryV1 _self;
  final $Res Function(HubPublicDiscoveryEntryV1) _then;

/// Create a copy of HubPublicDiscoveryEntryV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? packageName = freezed,Object? language = freezed,Object? surface = freezed,Object? channel = null,Object? revisionId = freezed,Object? updatedAt = freezed,Object? publisherExecutionId = freezed,Object? idempotencyKey = freezed,Object? metadata = null,Object? descriptor = freezed,Object? artifactLock = freezed,Object? refs = null,}) {
  return _then(_self.copyWith(
packageName: freezed == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String?,language: freezed == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as String?,surface: freezed == surface ? _self.surface : surface // ignore: cast_nullable_to_non_nullable
as String?,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,revisionId: freezed == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String?,updatedAt: freezed == updatedAt ? _self.updatedAt : updatedAt // ignore: cast_nullable_to_non_nullable
as String?,publisherExecutionId: freezed == publisherExecutionId ? _self.publisherExecutionId : publisherExecutionId // ignore: cast_nullable_to_non_nullable
as String?,idempotencyKey: freezed == idempotencyKey ? _self.idempotencyKey : idempotencyKey // ignore: cast_nullable_to_non_nullable
as String?,metadata: null == metadata ? _self.metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,descriptor: freezed == descriptor ? _self.descriptor : descriptor // ignore: cast_nullable_to_non_nullable
as HubPublicDiscoveryDescriptorV1?,artifactLock: freezed == artifactLock ? _self.artifactLock : artifactLock // ignore: cast_nullable_to_non_nullable
as HubPublicDiscoveryArtifactLockV1?,refs: null == refs ? _self.refs : refs // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}
/// Create a copy of HubPublicDiscoveryEntryV1
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$HubPublicDiscoveryDescriptorV1CopyWith<$Res>? get descriptor {
    if (_self.descriptor == null) {
    return null;
  }

  return $HubPublicDiscoveryDescriptorV1CopyWith<$Res>(_self.descriptor!, (value) {
    return _then(_self.copyWith(descriptor: value));
  });
}/// Create a copy of HubPublicDiscoveryEntryV1
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$HubPublicDiscoveryArtifactLockV1CopyWith<$Res>? get artifactLock {
    if (_self.artifactLock == null) {
    return null;
  }

  return $HubPublicDiscoveryArtifactLockV1CopyWith<$Res>(_self.artifactLock!, (value) {
    return _then(_self.copyWith(artifactLock: value));
  });
}
}


/// Adds pattern-matching-related methods to [HubPublicDiscoveryEntryV1].
extension HubPublicDiscoveryEntryV1Patterns on HubPublicDiscoveryEntryV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _HubPublicDiscoveryEntryV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _HubPublicDiscoveryEntryV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _HubPublicDiscoveryEntryV1 value)  def,}){
final _that = this;
switch (_that) {
case _HubPublicDiscoveryEntryV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _HubPublicDiscoveryEntryV1 value)?  def,}){
final _that = this;
switch (_that) {
case _HubPublicDiscoveryEntryV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String? packageName,  String? language,  String? surface,  String channel,  String? revisionId,  String? updatedAt,  String? publisherExecutionId,  String? idempotencyKey,  Map<String, dynamic> metadata,  HubPublicDiscoveryDescriptorV1? descriptor,  HubPublicDiscoveryArtifactLockV1? artifactLock,  Map<String, dynamic> refs)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _HubPublicDiscoveryEntryV1() when def != null:
return def(_that.packageName,_that.language,_that.surface,_that.channel,_that.revisionId,_that.updatedAt,_that.publisherExecutionId,_that.idempotencyKey,_that.metadata,_that.descriptor,_that.artifactLock,_that.refs);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String? packageName,  String? language,  String? surface,  String channel,  String? revisionId,  String? updatedAt,  String? publisherExecutionId,  String? idempotencyKey,  Map<String, dynamic> metadata,  HubPublicDiscoveryDescriptorV1? descriptor,  HubPublicDiscoveryArtifactLockV1? artifactLock,  Map<String, dynamic> refs)  def,}) {final _that = this;
switch (_that) {
case _HubPublicDiscoveryEntryV1():
return def(_that.packageName,_that.language,_that.surface,_that.channel,_that.revisionId,_that.updatedAt,_that.publisherExecutionId,_that.idempotencyKey,_that.metadata,_that.descriptor,_that.artifactLock,_that.refs);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String? packageName,  String? language,  String? surface,  String channel,  String? revisionId,  String? updatedAt,  String? publisherExecutionId,  String? idempotencyKey,  Map<String, dynamic> metadata,  HubPublicDiscoveryDescriptorV1? descriptor,  HubPublicDiscoveryArtifactLockV1? artifactLock,  Map<String, dynamic> refs)?  def,}) {final _that = this;
switch (_that) {
case _HubPublicDiscoveryEntryV1() when def != null:
return def(_that.packageName,_that.language,_that.surface,_that.channel,_that.revisionId,_that.updatedAt,_that.publisherExecutionId,_that.idempotencyKey,_that.metadata,_that.descriptor,_that.artifactLock,_that.refs);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _HubPublicDiscoveryEntryV1 implements HubPublicDiscoveryEntryV1 {
   _HubPublicDiscoveryEntryV1({this.packageName, this.language, this.surface, required this.channel, this.revisionId, this.updatedAt, this.publisherExecutionId, this.idempotencyKey, required final  Map<String, dynamic> metadata, this.descriptor, this.artifactLock, required final  Map<String, dynamic> refs}): _metadata = metadata,_refs = refs;
  factory _HubPublicDiscoveryEntryV1.fromJson(Map<String, dynamic> json) => _$HubPublicDiscoveryEntryV1FromJson(json);

@override final  String? packageName;
@override final  String? language;
@override final  String? surface;
@override final  String channel;
@override final  String? revisionId;
@override final  String? updatedAt;
@override final  String? publisherExecutionId;
@override final  String? idempotencyKey;
 final  Map<String, dynamic> _metadata;
@override Map<String, dynamic> get metadata {
  if (_metadata is EqualUnmodifiableMapView) return _metadata;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_metadata);
}

@override final  HubPublicDiscoveryDescriptorV1? descriptor;
@override final  HubPublicDiscoveryArtifactLockV1? artifactLock;
 final  Map<String, dynamic> _refs;
@override Map<String, dynamic> get refs {
  if (_refs is EqualUnmodifiableMapView) return _refs;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_refs);
}


/// Create a copy of HubPublicDiscoveryEntryV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$HubPublicDiscoveryEntryV1CopyWith<_HubPublicDiscoveryEntryV1> get copyWith => __$HubPublicDiscoveryEntryV1CopyWithImpl<_HubPublicDiscoveryEntryV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$HubPublicDiscoveryEntryV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _HubPublicDiscoveryEntryV1&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.language, language) || other.language == language)&&(identical(other.surface, surface) || other.surface == surface)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.updatedAt, updatedAt) || other.updatedAt == updatedAt)&&(identical(other.publisherExecutionId, publisherExecutionId) || other.publisherExecutionId == publisherExecutionId)&&(identical(other.idempotencyKey, idempotencyKey) || other.idempotencyKey == idempotencyKey)&&const DeepCollectionEquality().equals(other._metadata, _metadata)&&(identical(other.descriptor, descriptor) || other.descriptor == descriptor)&&(identical(other.artifactLock, artifactLock) || other.artifactLock == artifactLock)&&const DeepCollectionEquality().equals(other._refs, _refs));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,packageName,language,surface,channel,revisionId,updatedAt,publisherExecutionId,idempotencyKey,const DeepCollectionEquality().hash(_metadata),descriptor,artifactLock,const DeepCollectionEquality().hash(_refs));

@override
String toString() {
  return 'HubPublicDiscoveryEntryV1.def(packageName: $packageName, language: $language, surface: $surface, channel: $channel, revisionId: $revisionId, updatedAt: $updatedAt, publisherExecutionId: $publisherExecutionId, idempotencyKey: $idempotencyKey, metadata: $metadata, descriptor: $descriptor, artifactLock: $artifactLock, refs: $refs)';
}


}

/// @nodoc
abstract mixin class _$HubPublicDiscoveryEntryV1CopyWith<$Res> implements $HubPublicDiscoveryEntryV1CopyWith<$Res> {
  factory _$HubPublicDiscoveryEntryV1CopyWith(_HubPublicDiscoveryEntryV1 value, $Res Function(_HubPublicDiscoveryEntryV1) _then) = __$HubPublicDiscoveryEntryV1CopyWithImpl;
@override @useResult
$Res call({
 String? packageName, String? language, String? surface, String channel, String? revisionId, String? updatedAt, String? publisherExecutionId, String? idempotencyKey, Map<String, dynamic> metadata, HubPublicDiscoveryDescriptorV1? descriptor, HubPublicDiscoveryArtifactLockV1? artifactLock, Map<String, dynamic> refs
});


@override $HubPublicDiscoveryDescriptorV1CopyWith<$Res>? get descriptor;@override $HubPublicDiscoveryArtifactLockV1CopyWith<$Res>? get artifactLock;

}
/// @nodoc
class __$HubPublicDiscoveryEntryV1CopyWithImpl<$Res>
    implements _$HubPublicDiscoveryEntryV1CopyWith<$Res> {
  __$HubPublicDiscoveryEntryV1CopyWithImpl(this._self, this._then);

  final _HubPublicDiscoveryEntryV1 _self;
  final $Res Function(_HubPublicDiscoveryEntryV1) _then;

/// Create a copy of HubPublicDiscoveryEntryV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? packageName = freezed,Object? language = freezed,Object? surface = freezed,Object? channel = null,Object? revisionId = freezed,Object? updatedAt = freezed,Object? publisherExecutionId = freezed,Object? idempotencyKey = freezed,Object? metadata = null,Object? descriptor = freezed,Object? artifactLock = freezed,Object? refs = null,}) {
  return _then(_HubPublicDiscoveryEntryV1(
packageName: freezed == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String?,language: freezed == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as String?,surface: freezed == surface ? _self.surface : surface // ignore: cast_nullable_to_non_nullable
as String?,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,revisionId: freezed == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String?,updatedAt: freezed == updatedAt ? _self.updatedAt : updatedAt // ignore: cast_nullable_to_non_nullable
as String?,publisherExecutionId: freezed == publisherExecutionId ? _self.publisherExecutionId : publisherExecutionId // ignore: cast_nullable_to_non_nullable
as String?,idempotencyKey: freezed == idempotencyKey ? _self.idempotencyKey : idempotencyKey // ignore: cast_nullable_to_non_nullable
as String?,metadata: null == metadata ? _self._metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,descriptor: freezed == descriptor ? _self.descriptor : descriptor // ignore: cast_nullable_to_non_nullable
as HubPublicDiscoveryDescriptorV1?,artifactLock: freezed == artifactLock ? _self.artifactLock : artifactLock // ignore: cast_nullable_to_non_nullable
as HubPublicDiscoveryArtifactLockV1?,refs: null == refs ? _self._refs : refs // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

/// Create a copy of HubPublicDiscoveryEntryV1
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$HubPublicDiscoveryDescriptorV1CopyWith<$Res>? get descriptor {
    if (_self.descriptor == null) {
    return null;
  }

  return $HubPublicDiscoveryDescriptorV1CopyWith<$Res>(_self.descriptor!, (value) {
    return _then(_self.copyWith(descriptor: value));
  });
}/// Create a copy of HubPublicDiscoveryEntryV1
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$HubPublicDiscoveryArtifactLockV1CopyWith<$Res>? get artifactLock {
    if (_self.artifactLock == null) {
    return null;
  }

  return $HubPublicDiscoveryArtifactLockV1CopyWith<$Res>(_self.artifactLock!, (value) {
    return _then(_self.copyWith(artifactLock: value));
  });
}
}


/// @nodoc
mixin _$HubPublicDiscoveryViewStateV1 {

 String get status; String? get authoritySourceUrl; String? get query; String? get packageName; String? get language; String? get surface; String? get channel; int get limit; List<HubPublicDiscoveryEntryV1> get entries; String? get summary; String get emptyMessage; String? get error; Map<String, dynamic> get provenance;
/// Create a copy of HubPublicDiscoveryViewStateV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$HubPublicDiscoveryViewStateV1CopyWith<HubPublicDiscoveryViewStateV1> get copyWith => _$HubPublicDiscoveryViewStateV1CopyWithImpl<HubPublicDiscoveryViewStateV1>(this as HubPublicDiscoveryViewStateV1, _$identity);

  /// Serializes this HubPublicDiscoveryViewStateV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is HubPublicDiscoveryViewStateV1&&(identical(other.status, status) || other.status == status)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl)&&(identical(other.query, query) || other.query == query)&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.language, language) || other.language == language)&&(identical(other.surface, surface) || other.surface == surface)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.limit, limit) || other.limit == limit)&&const DeepCollectionEquality().equals(other.entries, entries)&&(identical(other.summary, summary) || other.summary == summary)&&(identical(other.emptyMessage, emptyMessage) || other.emptyMessage == emptyMessage)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other.provenance, provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,status,authoritySourceUrl,query,packageName,language,surface,channel,limit,const DeepCollectionEquality().hash(entries),summary,emptyMessage,error,const DeepCollectionEquality().hash(provenance));

@override
String toString() {
  return 'HubPublicDiscoveryViewStateV1(status: $status, authoritySourceUrl: $authoritySourceUrl, query: $query, packageName: $packageName, language: $language, surface: $surface, channel: $channel, limit: $limit, entries: $entries, summary: $summary, emptyMessage: $emptyMessage, error: $error, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class $HubPublicDiscoveryViewStateV1CopyWith<$Res>  {
  factory $HubPublicDiscoveryViewStateV1CopyWith(HubPublicDiscoveryViewStateV1 value, $Res Function(HubPublicDiscoveryViewStateV1) _then) = _$HubPublicDiscoveryViewStateV1CopyWithImpl;
@useResult
$Res call({
 String status, String? authoritySourceUrl, String? query, String? packageName, String? language, String? surface, String? channel, int limit, List<HubPublicDiscoveryEntryV1> entries, String? summary, String emptyMessage, String? error, Map<String, dynamic> provenance
});




}
/// @nodoc
class _$HubPublicDiscoveryViewStateV1CopyWithImpl<$Res>
    implements $HubPublicDiscoveryViewStateV1CopyWith<$Res> {
  _$HubPublicDiscoveryViewStateV1CopyWithImpl(this._self, this._then);

  final HubPublicDiscoveryViewStateV1 _self;
  final $Res Function(HubPublicDiscoveryViewStateV1) _then;

/// Create a copy of HubPublicDiscoveryViewStateV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? status = null,Object? authoritySourceUrl = freezed,Object? query = freezed,Object? packageName = freezed,Object? language = freezed,Object? surface = freezed,Object? channel = freezed,Object? limit = null,Object? entries = null,Object? summary = freezed,Object? emptyMessage = null,Object? error = freezed,Object? provenance = null,}) {
  return _then(_self.copyWith(
status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,authoritySourceUrl: freezed == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String?,query: freezed == query ? _self.query : query // ignore: cast_nullable_to_non_nullable
as String?,packageName: freezed == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String?,language: freezed == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as String?,surface: freezed == surface ? _self.surface : surface // ignore: cast_nullable_to_non_nullable
as String?,channel: freezed == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String?,limit: null == limit ? _self.limit : limit // ignore: cast_nullable_to_non_nullable
as int,entries: null == entries ? _self.entries : entries // ignore: cast_nullable_to_non_nullable
as List<HubPublicDiscoveryEntryV1>,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,emptyMessage: null == emptyMessage ? _self.emptyMessage : emptyMessage // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,provenance: null == provenance ? _self.provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [HubPublicDiscoveryViewStateV1].
extension HubPublicDiscoveryViewStateV1Patterns on HubPublicDiscoveryViewStateV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _HubPublicDiscoveryViewStateV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _HubPublicDiscoveryViewStateV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _HubPublicDiscoveryViewStateV1 value)  def,}){
final _that = this;
switch (_that) {
case _HubPublicDiscoveryViewStateV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _HubPublicDiscoveryViewStateV1 value)?  def,}){
final _that = this;
switch (_that) {
case _HubPublicDiscoveryViewStateV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String status,  String? authoritySourceUrl,  String? query,  String? packageName,  String? language,  String? surface,  String? channel,  int limit,  List<HubPublicDiscoveryEntryV1> entries,  String? summary,  String emptyMessage,  String? error,  Map<String, dynamic> provenance)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _HubPublicDiscoveryViewStateV1() when def != null:
return def(_that.status,_that.authoritySourceUrl,_that.query,_that.packageName,_that.language,_that.surface,_that.channel,_that.limit,_that.entries,_that.summary,_that.emptyMessage,_that.error,_that.provenance);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String status,  String? authoritySourceUrl,  String? query,  String? packageName,  String? language,  String? surface,  String? channel,  int limit,  List<HubPublicDiscoveryEntryV1> entries,  String? summary,  String emptyMessage,  String? error,  Map<String, dynamic> provenance)  def,}) {final _that = this;
switch (_that) {
case _HubPublicDiscoveryViewStateV1():
return def(_that.status,_that.authoritySourceUrl,_that.query,_that.packageName,_that.language,_that.surface,_that.channel,_that.limit,_that.entries,_that.summary,_that.emptyMessage,_that.error,_that.provenance);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String status,  String? authoritySourceUrl,  String? query,  String? packageName,  String? language,  String? surface,  String? channel,  int limit,  List<HubPublicDiscoveryEntryV1> entries,  String? summary,  String emptyMessage,  String? error,  Map<String, dynamic> provenance)?  def,}) {final _that = this;
switch (_that) {
case _HubPublicDiscoveryViewStateV1() when def != null:
return def(_that.status,_that.authoritySourceUrl,_that.query,_that.packageName,_that.language,_that.surface,_that.channel,_that.limit,_that.entries,_that.summary,_that.emptyMessage,_that.error,_that.provenance);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _HubPublicDiscoveryViewStateV1 implements HubPublicDiscoveryViewStateV1 {
   _HubPublicDiscoveryViewStateV1({required this.status, this.authoritySourceUrl, this.query, this.packageName, this.language, this.surface, this.channel, required this.limit, final  List<HubPublicDiscoveryEntryV1> entries = const [], this.summary, required this.emptyMessage, this.error, required final  Map<String, dynamic> provenance}): _entries = entries,_provenance = provenance;
  factory _HubPublicDiscoveryViewStateV1.fromJson(Map<String, dynamic> json) => _$HubPublicDiscoveryViewStateV1FromJson(json);

@override final  String status;
@override final  String? authoritySourceUrl;
@override final  String? query;
@override final  String? packageName;
@override final  String? language;
@override final  String? surface;
@override final  String? channel;
@override final  int limit;
 final  List<HubPublicDiscoveryEntryV1> _entries;
@override@JsonKey() List<HubPublicDiscoveryEntryV1> get entries {
  if (_entries is EqualUnmodifiableListView) return _entries;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_entries);
}

@override final  String? summary;
@override final  String emptyMessage;
@override final  String? error;
 final  Map<String, dynamic> _provenance;
@override Map<String, dynamic> get provenance {
  if (_provenance is EqualUnmodifiableMapView) return _provenance;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_provenance);
}


/// Create a copy of HubPublicDiscoveryViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$HubPublicDiscoveryViewStateV1CopyWith<_HubPublicDiscoveryViewStateV1> get copyWith => __$HubPublicDiscoveryViewStateV1CopyWithImpl<_HubPublicDiscoveryViewStateV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$HubPublicDiscoveryViewStateV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _HubPublicDiscoveryViewStateV1&&(identical(other.status, status) || other.status == status)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl)&&(identical(other.query, query) || other.query == query)&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.language, language) || other.language == language)&&(identical(other.surface, surface) || other.surface == surface)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.limit, limit) || other.limit == limit)&&const DeepCollectionEquality().equals(other._entries, _entries)&&(identical(other.summary, summary) || other.summary == summary)&&(identical(other.emptyMessage, emptyMessage) || other.emptyMessage == emptyMessage)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other._provenance, _provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,status,authoritySourceUrl,query,packageName,language,surface,channel,limit,const DeepCollectionEquality().hash(_entries),summary,emptyMessage,error,const DeepCollectionEquality().hash(_provenance));

@override
String toString() {
  return 'HubPublicDiscoveryViewStateV1.def(status: $status, authoritySourceUrl: $authoritySourceUrl, query: $query, packageName: $packageName, language: $language, surface: $surface, channel: $channel, limit: $limit, entries: $entries, summary: $summary, emptyMessage: $emptyMessage, error: $error, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class _$HubPublicDiscoveryViewStateV1CopyWith<$Res> implements $HubPublicDiscoveryViewStateV1CopyWith<$Res> {
  factory _$HubPublicDiscoveryViewStateV1CopyWith(_HubPublicDiscoveryViewStateV1 value, $Res Function(_HubPublicDiscoveryViewStateV1) _then) = __$HubPublicDiscoveryViewStateV1CopyWithImpl;
@override @useResult
$Res call({
 String status, String? authoritySourceUrl, String? query, String? packageName, String? language, String? surface, String? channel, int limit, List<HubPublicDiscoveryEntryV1> entries, String? summary, String emptyMessage, String? error, Map<String, dynamic> provenance
});




}
/// @nodoc
class __$HubPublicDiscoveryViewStateV1CopyWithImpl<$Res>
    implements _$HubPublicDiscoveryViewStateV1CopyWith<$Res> {
  __$HubPublicDiscoveryViewStateV1CopyWithImpl(this._self, this._then);

  final _HubPublicDiscoveryViewStateV1 _self;
  final $Res Function(_HubPublicDiscoveryViewStateV1) _then;

/// Create a copy of HubPublicDiscoveryViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? status = null,Object? authoritySourceUrl = freezed,Object? query = freezed,Object? packageName = freezed,Object? language = freezed,Object? surface = freezed,Object? channel = freezed,Object? limit = null,Object? entries = null,Object? summary = freezed,Object? emptyMessage = null,Object? error = freezed,Object? provenance = null,}) {
  return _then(_HubPublicDiscoveryViewStateV1(
status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,authoritySourceUrl: freezed == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String?,query: freezed == query ? _self.query : query // ignore: cast_nullable_to_non_nullable
as String?,packageName: freezed == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String?,language: freezed == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as String?,surface: freezed == surface ? _self.surface : surface // ignore: cast_nullable_to_non_nullable
as String?,channel: freezed == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String?,limit: null == limit ? _self.limit : limit // ignore: cast_nullable_to_non_nullable
as int,entries: null == entries ? _self._entries : entries // ignore: cast_nullable_to_non_nullable
as List<HubPublicDiscoveryEntryV1>,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,emptyMessage: null == emptyMessage ? _self.emptyMessage : emptyMessage // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,provenance: null == provenance ? _self._provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}

// dart format on
