// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'media_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$StorageBlobRef {

@UuidValueConverter() UuidValue? get objectId; String? get sha;
/// Create a copy of StorageBlobRef
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$StorageBlobRefCopyWith<StorageBlobRef> get copyWith => _$StorageBlobRefCopyWithImpl<StorageBlobRef>(this as StorageBlobRef, _$identity);

  /// Serializes this StorageBlobRef to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is StorageBlobRef&&(identical(other.objectId, objectId) || other.objectId == objectId)&&(identical(other.sha, sha) || other.sha == sha));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,objectId,sha);

@override
String toString() {
  return 'StorageBlobRef(objectId: $objectId, sha: $sha)';
}


}

/// @nodoc
abstract mixin class $StorageBlobRefCopyWith<$Res>  {
  factory $StorageBlobRefCopyWith(StorageBlobRef value, $Res Function(StorageBlobRef) _then) = _$StorageBlobRefCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? objectId, String? sha
});




}
/// @nodoc
class _$StorageBlobRefCopyWithImpl<$Res>
    implements $StorageBlobRefCopyWith<$Res> {
  _$StorageBlobRefCopyWithImpl(this._self, this._then);

  final StorageBlobRef _self;
  final $Res Function(StorageBlobRef) _then;

/// Create a copy of StorageBlobRef
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? objectId = freezed,Object? sha = freezed,}) {
  return _then(_self.copyWith(
objectId: freezed == objectId ? _self.objectId : objectId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sha: freezed == sha ? _self.sha : sha // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [StorageBlobRef].
extension StorageBlobRefPatterns on StorageBlobRef {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _StorageBlobRef value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _StorageBlobRef() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _StorageBlobRef value)  def,}){
final _that = this;
switch (_that) {
case _StorageBlobRef():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _StorageBlobRef value)?  def,}){
final _that = this;
switch (_that) {
case _StorageBlobRef() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? objectId,  String? sha)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _StorageBlobRef() when def != null:
return def(_that.objectId,_that.sha);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? objectId,  String? sha)  def,}) {final _that = this;
switch (_that) {
case _StorageBlobRef():
return def(_that.objectId,_that.sha);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? objectId,  String? sha)?  def,}) {final _that = this;
switch (_that) {
case _StorageBlobRef() when def != null:
return def(_that.objectId,_that.sha);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _StorageBlobRef implements StorageBlobRef {
   _StorageBlobRef({@UuidValueConverter() this.objectId, this.sha});
  factory _StorageBlobRef.fromJson(Map<String, dynamic> json) => _$StorageBlobRefFromJson(json);

@override@UuidValueConverter() final  UuidValue? objectId;
@override final  String? sha;

/// Create a copy of StorageBlobRef
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$StorageBlobRefCopyWith<_StorageBlobRef> get copyWith => __$StorageBlobRefCopyWithImpl<_StorageBlobRef>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$StorageBlobRefToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _StorageBlobRef&&(identical(other.objectId, objectId) || other.objectId == objectId)&&(identical(other.sha, sha) || other.sha == sha));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,objectId,sha);

@override
String toString() {
  return 'StorageBlobRef.def(objectId: $objectId, sha: $sha)';
}


}

/// @nodoc
abstract mixin class _$StorageBlobRefCopyWith<$Res> implements $StorageBlobRefCopyWith<$Res> {
  factory _$StorageBlobRefCopyWith(_StorageBlobRef value, $Res Function(_StorageBlobRef) _then) = __$StorageBlobRefCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? objectId, String? sha
});




}
/// @nodoc
class __$StorageBlobRefCopyWithImpl<$Res>
    implements _$StorageBlobRefCopyWith<$Res> {
  __$StorageBlobRefCopyWithImpl(this._self, this._then);

  final _StorageBlobRef _self;
  final $Res Function(_StorageBlobRef) _then;

/// Create a copy of StorageBlobRef
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? objectId = freezed,Object? sha = freezed,}) {
  return _then(_StorageBlobRef(
objectId: freezed == objectId ? _self.objectId : objectId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sha: freezed == sha ? _self.sha : sha // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$StorageMediaRef {

@UuidValueConverter() UuidValue get objectId; String? get uri; String get uriScheme; String? get mediaKind; String? get mimeType; String? get sha; String? get variantKey; String? get renditionKey; String? get filename; Map<String, dynamic> get metadata;
/// Create a copy of StorageMediaRef
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$StorageMediaRefCopyWith<StorageMediaRef> get copyWith => _$StorageMediaRefCopyWithImpl<StorageMediaRef>(this as StorageMediaRef, _$identity);

  /// Serializes this StorageMediaRef to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is StorageMediaRef&&(identical(other.objectId, objectId) || other.objectId == objectId)&&(identical(other.uri, uri) || other.uri == uri)&&(identical(other.uriScheme, uriScheme) || other.uriScheme == uriScheme)&&(identical(other.mediaKind, mediaKind) || other.mediaKind == mediaKind)&&(identical(other.mimeType, mimeType) || other.mimeType == mimeType)&&(identical(other.sha, sha) || other.sha == sha)&&(identical(other.variantKey, variantKey) || other.variantKey == variantKey)&&(identical(other.renditionKey, renditionKey) || other.renditionKey == renditionKey)&&(identical(other.filename, filename) || other.filename == filename)&&const DeepCollectionEquality().equals(other.metadata, metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,objectId,uri,uriScheme,mediaKind,mimeType,sha,variantKey,renditionKey,filename,const DeepCollectionEquality().hash(metadata));

@override
String toString() {
  return 'StorageMediaRef(objectId: $objectId, uri: $uri, uriScheme: $uriScheme, mediaKind: $mediaKind, mimeType: $mimeType, sha: $sha, variantKey: $variantKey, renditionKey: $renditionKey, filename: $filename, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class $StorageMediaRefCopyWith<$Res>  {
  factory $StorageMediaRefCopyWith(StorageMediaRef value, $Res Function(StorageMediaRef) _then) = _$StorageMediaRefCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue objectId, String? uri, String uriScheme, String? mediaKind, String? mimeType, String? sha, String? variantKey, String? renditionKey, String? filename, Map<String, dynamic> metadata
});




}
/// @nodoc
class _$StorageMediaRefCopyWithImpl<$Res>
    implements $StorageMediaRefCopyWith<$Res> {
  _$StorageMediaRefCopyWithImpl(this._self, this._then);

  final StorageMediaRef _self;
  final $Res Function(StorageMediaRef) _then;

/// Create a copy of StorageMediaRef
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? objectId = null,Object? uri = freezed,Object? uriScheme = null,Object? mediaKind = freezed,Object? mimeType = freezed,Object? sha = freezed,Object? variantKey = freezed,Object? renditionKey = freezed,Object? filename = freezed,Object? metadata = null,}) {
  return _then(_self.copyWith(
objectId: null == objectId ? _self.objectId : objectId // ignore: cast_nullable_to_non_nullable
as UuidValue,uri: freezed == uri ? _self.uri : uri // ignore: cast_nullable_to_non_nullable
as String?,uriScheme: null == uriScheme ? _self.uriScheme : uriScheme // ignore: cast_nullable_to_non_nullable
as String,mediaKind: freezed == mediaKind ? _self.mediaKind : mediaKind // ignore: cast_nullable_to_non_nullable
as String?,mimeType: freezed == mimeType ? _self.mimeType : mimeType // ignore: cast_nullable_to_non_nullable
as String?,sha: freezed == sha ? _self.sha : sha // ignore: cast_nullable_to_non_nullable
as String?,variantKey: freezed == variantKey ? _self.variantKey : variantKey // ignore: cast_nullable_to_non_nullable
as String?,renditionKey: freezed == renditionKey ? _self.renditionKey : renditionKey // ignore: cast_nullable_to_non_nullable
as String?,filename: freezed == filename ? _self.filename : filename // ignore: cast_nullable_to_non_nullable
as String?,metadata: null == metadata ? _self.metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [StorageMediaRef].
extension StorageMediaRefPatterns on StorageMediaRef {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _StorageMediaRef value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _StorageMediaRef() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _StorageMediaRef value)  def,}){
final _that = this;
switch (_that) {
case _StorageMediaRef():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _StorageMediaRef value)?  def,}){
final _that = this;
switch (_that) {
case _StorageMediaRef() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue objectId,  String? uri,  String uriScheme,  String? mediaKind,  String? mimeType,  String? sha,  String? variantKey,  String? renditionKey,  String? filename,  Map<String, dynamic> metadata)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _StorageMediaRef() when def != null:
return def(_that.objectId,_that.uri,_that.uriScheme,_that.mediaKind,_that.mimeType,_that.sha,_that.variantKey,_that.renditionKey,_that.filename,_that.metadata);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue objectId,  String? uri,  String uriScheme,  String? mediaKind,  String? mimeType,  String? sha,  String? variantKey,  String? renditionKey,  String? filename,  Map<String, dynamic> metadata)  def,}) {final _that = this;
switch (_that) {
case _StorageMediaRef():
return def(_that.objectId,_that.uri,_that.uriScheme,_that.mediaKind,_that.mimeType,_that.sha,_that.variantKey,_that.renditionKey,_that.filename,_that.metadata);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue objectId,  String? uri,  String uriScheme,  String? mediaKind,  String? mimeType,  String? sha,  String? variantKey,  String? renditionKey,  String? filename,  Map<String, dynamic> metadata)?  def,}) {final _that = this;
switch (_that) {
case _StorageMediaRef() when def != null:
return def(_that.objectId,_that.uri,_that.uriScheme,_that.mediaKind,_that.mimeType,_that.sha,_that.variantKey,_that.renditionKey,_that.filename,_that.metadata);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _StorageMediaRef implements StorageMediaRef {
   _StorageMediaRef({@UuidValueConverter() required this.objectId, this.uri, required this.uriScheme, this.mediaKind, this.mimeType, this.sha, this.variantKey, this.renditionKey, this.filename, required final  Map<String, dynamic> metadata}): _metadata = metadata;
  factory _StorageMediaRef.fromJson(Map<String, dynamic> json) => _$StorageMediaRefFromJson(json);

@override@UuidValueConverter() final  UuidValue objectId;
@override final  String? uri;
@override final  String uriScheme;
@override final  String? mediaKind;
@override final  String? mimeType;
@override final  String? sha;
@override final  String? variantKey;
@override final  String? renditionKey;
@override final  String? filename;
 final  Map<String, dynamic> _metadata;
@override Map<String, dynamic> get metadata {
  if (_metadata is EqualUnmodifiableMapView) return _metadata;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_metadata);
}


/// Create a copy of StorageMediaRef
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$StorageMediaRefCopyWith<_StorageMediaRef> get copyWith => __$StorageMediaRefCopyWithImpl<_StorageMediaRef>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$StorageMediaRefToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _StorageMediaRef&&(identical(other.objectId, objectId) || other.objectId == objectId)&&(identical(other.uri, uri) || other.uri == uri)&&(identical(other.uriScheme, uriScheme) || other.uriScheme == uriScheme)&&(identical(other.mediaKind, mediaKind) || other.mediaKind == mediaKind)&&(identical(other.mimeType, mimeType) || other.mimeType == mimeType)&&(identical(other.sha, sha) || other.sha == sha)&&(identical(other.variantKey, variantKey) || other.variantKey == variantKey)&&(identical(other.renditionKey, renditionKey) || other.renditionKey == renditionKey)&&(identical(other.filename, filename) || other.filename == filename)&&const DeepCollectionEquality().equals(other._metadata, _metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,objectId,uri,uriScheme,mediaKind,mimeType,sha,variantKey,renditionKey,filename,const DeepCollectionEquality().hash(_metadata));

@override
String toString() {
  return 'StorageMediaRef.def(objectId: $objectId, uri: $uri, uriScheme: $uriScheme, mediaKind: $mediaKind, mimeType: $mimeType, sha: $sha, variantKey: $variantKey, renditionKey: $renditionKey, filename: $filename, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class _$StorageMediaRefCopyWith<$Res> implements $StorageMediaRefCopyWith<$Res> {
  factory _$StorageMediaRefCopyWith(_StorageMediaRef value, $Res Function(_StorageMediaRef) _then) = __$StorageMediaRefCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue objectId, String? uri, String uriScheme, String? mediaKind, String? mimeType, String? sha, String? variantKey, String? renditionKey, String? filename, Map<String, dynamic> metadata
});




}
/// @nodoc
class __$StorageMediaRefCopyWithImpl<$Res>
    implements _$StorageMediaRefCopyWith<$Res> {
  __$StorageMediaRefCopyWithImpl(this._self, this._then);

  final _StorageMediaRef _self;
  final $Res Function(_StorageMediaRef) _then;

/// Create a copy of StorageMediaRef
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? objectId = null,Object? uri = freezed,Object? uriScheme = null,Object? mediaKind = freezed,Object? mimeType = freezed,Object? sha = freezed,Object? variantKey = freezed,Object? renditionKey = freezed,Object? filename = freezed,Object? metadata = null,}) {
  return _then(_StorageMediaRef(
objectId: null == objectId ? _self.objectId : objectId // ignore: cast_nullable_to_non_nullable
as UuidValue,uri: freezed == uri ? _self.uri : uri // ignore: cast_nullable_to_non_nullable
as String?,uriScheme: null == uriScheme ? _self.uriScheme : uriScheme // ignore: cast_nullable_to_non_nullable
as String,mediaKind: freezed == mediaKind ? _self.mediaKind : mediaKind // ignore: cast_nullable_to_non_nullable
as String?,mimeType: freezed == mimeType ? _self.mimeType : mimeType // ignore: cast_nullable_to_non_nullable
as String?,sha: freezed == sha ? _self.sha : sha // ignore: cast_nullable_to_non_nullable
as String?,variantKey: freezed == variantKey ? _self.variantKey : variantKey // ignore: cast_nullable_to_non_nullable
as String?,renditionKey: freezed == renditionKey ? _self.renditionKey : renditionKey // ignore: cast_nullable_to_non_nullable
as String?,filename: freezed == filename ? _self.filename : filename // ignore: cast_nullable_to_non_nullable
as String?,metadata: null == metadata ? _self._metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$StorageBlobMetadata {

@UuidValueConverter() UuidValue get objectId; String get sha; String get mimeType; int get sizeBytes; String? get objectKey; String? get pathLocal;@UuidValueConverter() UuidValue? get bucketId;
/// Create a copy of StorageBlobMetadata
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$StorageBlobMetadataCopyWith<StorageBlobMetadata> get copyWith => _$StorageBlobMetadataCopyWithImpl<StorageBlobMetadata>(this as StorageBlobMetadata, _$identity);

  /// Serializes this StorageBlobMetadata to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is StorageBlobMetadata&&(identical(other.objectId, objectId) || other.objectId == objectId)&&(identical(other.sha, sha) || other.sha == sha)&&(identical(other.mimeType, mimeType) || other.mimeType == mimeType)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.objectKey, objectKey) || other.objectKey == objectKey)&&(identical(other.pathLocal, pathLocal) || other.pathLocal == pathLocal)&&(identical(other.bucketId, bucketId) || other.bucketId == bucketId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,objectId,sha,mimeType,sizeBytes,objectKey,pathLocal,bucketId);

@override
String toString() {
  return 'StorageBlobMetadata(objectId: $objectId, sha: $sha, mimeType: $mimeType, sizeBytes: $sizeBytes, objectKey: $objectKey, pathLocal: $pathLocal, bucketId: $bucketId)';
}


}

/// @nodoc
abstract mixin class $StorageBlobMetadataCopyWith<$Res>  {
  factory $StorageBlobMetadataCopyWith(StorageBlobMetadata value, $Res Function(StorageBlobMetadata) _then) = _$StorageBlobMetadataCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue objectId, String sha, String mimeType, int sizeBytes, String? objectKey, String? pathLocal,@UuidValueConverter() UuidValue? bucketId
});




}
/// @nodoc
class _$StorageBlobMetadataCopyWithImpl<$Res>
    implements $StorageBlobMetadataCopyWith<$Res> {
  _$StorageBlobMetadataCopyWithImpl(this._self, this._then);

  final StorageBlobMetadata _self;
  final $Res Function(StorageBlobMetadata) _then;

/// Create a copy of StorageBlobMetadata
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? objectId = null,Object? sha = null,Object? mimeType = null,Object? sizeBytes = null,Object? objectKey = freezed,Object? pathLocal = freezed,Object? bucketId = freezed,}) {
  return _then(_self.copyWith(
objectId: null == objectId ? _self.objectId : objectId // ignore: cast_nullable_to_non_nullable
as UuidValue,sha: null == sha ? _self.sha : sha // ignore: cast_nullable_to_non_nullable
as String,mimeType: null == mimeType ? _self.mimeType : mimeType // ignore: cast_nullable_to_non_nullable
as String,sizeBytes: null == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int,objectKey: freezed == objectKey ? _self.objectKey : objectKey // ignore: cast_nullable_to_non_nullable
as String?,pathLocal: freezed == pathLocal ? _self.pathLocal : pathLocal // ignore: cast_nullable_to_non_nullable
as String?,bucketId: freezed == bucketId ? _self.bucketId : bucketId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

}


/// Adds pattern-matching-related methods to [StorageBlobMetadata].
extension StorageBlobMetadataPatterns on StorageBlobMetadata {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _StorageBlobMetadata value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _StorageBlobMetadata() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _StorageBlobMetadata value)  def,}){
final _that = this;
switch (_that) {
case _StorageBlobMetadata():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _StorageBlobMetadata value)?  def,}){
final _that = this;
switch (_that) {
case _StorageBlobMetadata() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue objectId,  String sha,  String mimeType,  int sizeBytes,  String? objectKey,  String? pathLocal, @UuidValueConverter()  UuidValue? bucketId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _StorageBlobMetadata() when def != null:
return def(_that.objectId,_that.sha,_that.mimeType,_that.sizeBytes,_that.objectKey,_that.pathLocal,_that.bucketId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue objectId,  String sha,  String mimeType,  int sizeBytes,  String? objectKey,  String? pathLocal, @UuidValueConverter()  UuidValue? bucketId)  def,}) {final _that = this;
switch (_that) {
case _StorageBlobMetadata():
return def(_that.objectId,_that.sha,_that.mimeType,_that.sizeBytes,_that.objectKey,_that.pathLocal,_that.bucketId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue objectId,  String sha,  String mimeType,  int sizeBytes,  String? objectKey,  String? pathLocal, @UuidValueConverter()  UuidValue? bucketId)?  def,}) {final _that = this;
switch (_that) {
case _StorageBlobMetadata() when def != null:
return def(_that.objectId,_that.sha,_that.mimeType,_that.sizeBytes,_that.objectKey,_that.pathLocal,_that.bucketId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _StorageBlobMetadata implements StorageBlobMetadata {
   _StorageBlobMetadata({@UuidValueConverter() required this.objectId, required this.sha, required this.mimeType, required this.sizeBytes, this.objectKey, this.pathLocal, @UuidValueConverter() this.bucketId});
  factory _StorageBlobMetadata.fromJson(Map<String, dynamic> json) => _$StorageBlobMetadataFromJson(json);

@override@UuidValueConverter() final  UuidValue objectId;
@override final  String sha;
@override final  String mimeType;
@override final  int sizeBytes;
@override final  String? objectKey;
@override final  String? pathLocal;
@override@UuidValueConverter() final  UuidValue? bucketId;

/// Create a copy of StorageBlobMetadata
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$StorageBlobMetadataCopyWith<_StorageBlobMetadata> get copyWith => __$StorageBlobMetadataCopyWithImpl<_StorageBlobMetadata>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$StorageBlobMetadataToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _StorageBlobMetadata&&(identical(other.objectId, objectId) || other.objectId == objectId)&&(identical(other.sha, sha) || other.sha == sha)&&(identical(other.mimeType, mimeType) || other.mimeType == mimeType)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.objectKey, objectKey) || other.objectKey == objectKey)&&(identical(other.pathLocal, pathLocal) || other.pathLocal == pathLocal)&&(identical(other.bucketId, bucketId) || other.bucketId == bucketId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,objectId,sha,mimeType,sizeBytes,objectKey,pathLocal,bucketId);

@override
String toString() {
  return 'StorageBlobMetadata.def(objectId: $objectId, sha: $sha, mimeType: $mimeType, sizeBytes: $sizeBytes, objectKey: $objectKey, pathLocal: $pathLocal, bucketId: $bucketId)';
}


}

/// @nodoc
abstract mixin class _$StorageBlobMetadataCopyWith<$Res> implements $StorageBlobMetadataCopyWith<$Res> {
  factory _$StorageBlobMetadataCopyWith(_StorageBlobMetadata value, $Res Function(_StorageBlobMetadata) _then) = __$StorageBlobMetadataCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue objectId, String sha, String mimeType, int sizeBytes, String? objectKey, String? pathLocal,@UuidValueConverter() UuidValue? bucketId
});




}
/// @nodoc
class __$StorageBlobMetadataCopyWithImpl<$Res>
    implements _$StorageBlobMetadataCopyWith<$Res> {
  __$StorageBlobMetadataCopyWithImpl(this._self, this._then);

  final _StorageBlobMetadata _self;
  final $Res Function(_StorageBlobMetadata) _then;

/// Create a copy of StorageBlobMetadata
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? objectId = null,Object? sha = null,Object? mimeType = null,Object? sizeBytes = null,Object? objectKey = freezed,Object? pathLocal = freezed,Object? bucketId = freezed,}) {
  return _then(_StorageBlobMetadata(
objectId: null == objectId ? _self.objectId : objectId // ignore: cast_nullable_to_non_nullable
as UuidValue,sha: null == sha ? _self.sha : sha // ignore: cast_nullable_to_non_nullable
as String,mimeType: null == mimeType ? _self.mimeType : mimeType // ignore: cast_nullable_to_non_nullable
as String,sizeBytes: null == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int,objectKey: freezed == objectKey ? _self.objectKey : objectKey // ignore: cast_nullable_to_non_nullable
as String?,pathLocal: freezed == pathLocal ? _self.pathLocal : pathLocal // ignore: cast_nullable_to_non_nullable
as String?,bucketId: freezed == bucketId ? _self.bucketId : bucketId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}


}


/// @nodoc
mixin _$StorageMediaResolution {

 StorageMediaRef get mediaRef;@UuidValueConverter() UuidValue get objectId; String get sha; String get mimeType; int get sizeBytes; String get uri; String get uriScheme; String? get httpUrl; String? get cacheControl; String? get etag; String? get contentDisposition; String? get filename; String? get expiresAt; Map<String, dynamic> get metadata;
/// Create a copy of StorageMediaResolution
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$StorageMediaResolutionCopyWith<StorageMediaResolution> get copyWith => _$StorageMediaResolutionCopyWithImpl<StorageMediaResolution>(this as StorageMediaResolution, _$identity);

  /// Serializes this StorageMediaResolution to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is StorageMediaResolution&&(identical(other.mediaRef, mediaRef) || other.mediaRef == mediaRef)&&(identical(other.objectId, objectId) || other.objectId == objectId)&&(identical(other.sha, sha) || other.sha == sha)&&(identical(other.mimeType, mimeType) || other.mimeType == mimeType)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.uri, uri) || other.uri == uri)&&(identical(other.uriScheme, uriScheme) || other.uriScheme == uriScheme)&&(identical(other.httpUrl, httpUrl) || other.httpUrl == httpUrl)&&(identical(other.cacheControl, cacheControl) || other.cacheControl == cacheControl)&&(identical(other.etag, etag) || other.etag == etag)&&(identical(other.contentDisposition, contentDisposition) || other.contentDisposition == contentDisposition)&&(identical(other.filename, filename) || other.filename == filename)&&(identical(other.expiresAt, expiresAt) || other.expiresAt == expiresAt)&&const DeepCollectionEquality().equals(other.metadata, metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,mediaRef,objectId,sha,mimeType,sizeBytes,uri,uriScheme,httpUrl,cacheControl,etag,contentDisposition,filename,expiresAt,const DeepCollectionEquality().hash(metadata));

@override
String toString() {
  return 'StorageMediaResolution(mediaRef: $mediaRef, objectId: $objectId, sha: $sha, mimeType: $mimeType, sizeBytes: $sizeBytes, uri: $uri, uriScheme: $uriScheme, httpUrl: $httpUrl, cacheControl: $cacheControl, etag: $etag, contentDisposition: $contentDisposition, filename: $filename, expiresAt: $expiresAt, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class $StorageMediaResolutionCopyWith<$Res>  {
  factory $StorageMediaResolutionCopyWith(StorageMediaResolution value, $Res Function(StorageMediaResolution) _then) = _$StorageMediaResolutionCopyWithImpl;
@useResult
$Res call({
 StorageMediaRef mediaRef,@UuidValueConverter() UuidValue objectId, String sha, String mimeType, int sizeBytes, String uri, String uriScheme, String? httpUrl, String? cacheControl, String? etag, String? contentDisposition, String? filename, String? expiresAt, Map<String, dynamic> metadata
});


$StorageMediaRefCopyWith<$Res> get mediaRef;

}
/// @nodoc
class _$StorageMediaResolutionCopyWithImpl<$Res>
    implements $StorageMediaResolutionCopyWith<$Res> {
  _$StorageMediaResolutionCopyWithImpl(this._self, this._then);

  final StorageMediaResolution _self;
  final $Res Function(StorageMediaResolution) _then;

/// Create a copy of StorageMediaResolution
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? mediaRef = null,Object? objectId = null,Object? sha = null,Object? mimeType = null,Object? sizeBytes = null,Object? uri = null,Object? uriScheme = null,Object? httpUrl = freezed,Object? cacheControl = freezed,Object? etag = freezed,Object? contentDisposition = freezed,Object? filename = freezed,Object? expiresAt = freezed,Object? metadata = null,}) {
  return _then(_self.copyWith(
mediaRef: null == mediaRef ? _self.mediaRef : mediaRef // ignore: cast_nullable_to_non_nullable
as StorageMediaRef,objectId: null == objectId ? _self.objectId : objectId // ignore: cast_nullable_to_non_nullable
as UuidValue,sha: null == sha ? _self.sha : sha // ignore: cast_nullable_to_non_nullable
as String,mimeType: null == mimeType ? _self.mimeType : mimeType // ignore: cast_nullable_to_non_nullable
as String,sizeBytes: null == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int,uri: null == uri ? _self.uri : uri // ignore: cast_nullable_to_non_nullable
as String,uriScheme: null == uriScheme ? _self.uriScheme : uriScheme // ignore: cast_nullable_to_non_nullable
as String,httpUrl: freezed == httpUrl ? _self.httpUrl : httpUrl // ignore: cast_nullable_to_non_nullable
as String?,cacheControl: freezed == cacheControl ? _self.cacheControl : cacheControl // ignore: cast_nullable_to_non_nullable
as String?,etag: freezed == etag ? _self.etag : etag // ignore: cast_nullable_to_non_nullable
as String?,contentDisposition: freezed == contentDisposition ? _self.contentDisposition : contentDisposition // ignore: cast_nullable_to_non_nullable
as String?,filename: freezed == filename ? _self.filename : filename // ignore: cast_nullable_to_non_nullable
as String?,expiresAt: freezed == expiresAt ? _self.expiresAt : expiresAt // ignore: cast_nullable_to_non_nullable
as String?,metadata: null == metadata ? _self.metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}
/// Create a copy of StorageMediaResolution
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$StorageMediaRefCopyWith<$Res> get mediaRef {
  
  return $StorageMediaRefCopyWith<$Res>(_self.mediaRef, (value) {
    return _then(_self.copyWith(mediaRef: value));
  });
}
}


/// Adds pattern-matching-related methods to [StorageMediaResolution].
extension StorageMediaResolutionPatterns on StorageMediaResolution {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _StorageMediaResolution value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _StorageMediaResolution() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _StorageMediaResolution value)  def,}){
final _that = this;
switch (_that) {
case _StorageMediaResolution():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _StorageMediaResolution value)?  def,}){
final _that = this;
switch (_that) {
case _StorageMediaResolution() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( StorageMediaRef mediaRef, @UuidValueConverter()  UuidValue objectId,  String sha,  String mimeType,  int sizeBytes,  String uri,  String uriScheme,  String? httpUrl,  String? cacheControl,  String? etag,  String? contentDisposition,  String? filename,  String? expiresAt,  Map<String, dynamic> metadata)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _StorageMediaResolution() when def != null:
return def(_that.mediaRef,_that.objectId,_that.sha,_that.mimeType,_that.sizeBytes,_that.uri,_that.uriScheme,_that.httpUrl,_that.cacheControl,_that.etag,_that.contentDisposition,_that.filename,_that.expiresAt,_that.metadata);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( StorageMediaRef mediaRef, @UuidValueConverter()  UuidValue objectId,  String sha,  String mimeType,  int sizeBytes,  String uri,  String uriScheme,  String? httpUrl,  String? cacheControl,  String? etag,  String? contentDisposition,  String? filename,  String? expiresAt,  Map<String, dynamic> metadata)  def,}) {final _that = this;
switch (_that) {
case _StorageMediaResolution():
return def(_that.mediaRef,_that.objectId,_that.sha,_that.mimeType,_that.sizeBytes,_that.uri,_that.uriScheme,_that.httpUrl,_that.cacheControl,_that.etag,_that.contentDisposition,_that.filename,_that.expiresAt,_that.metadata);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( StorageMediaRef mediaRef, @UuidValueConverter()  UuidValue objectId,  String sha,  String mimeType,  int sizeBytes,  String uri,  String uriScheme,  String? httpUrl,  String? cacheControl,  String? etag,  String? contentDisposition,  String? filename,  String? expiresAt,  Map<String, dynamic> metadata)?  def,}) {final _that = this;
switch (_that) {
case _StorageMediaResolution() when def != null:
return def(_that.mediaRef,_that.objectId,_that.sha,_that.mimeType,_that.sizeBytes,_that.uri,_that.uriScheme,_that.httpUrl,_that.cacheControl,_that.etag,_that.contentDisposition,_that.filename,_that.expiresAt,_that.metadata);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _StorageMediaResolution implements StorageMediaResolution {
   _StorageMediaResolution({required this.mediaRef, @UuidValueConverter() required this.objectId, required this.sha, required this.mimeType, required this.sizeBytes, required this.uri, required this.uriScheme, this.httpUrl, this.cacheControl, this.etag, this.contentDisposition, this.filename, this.expiresAt, required final  Map<String, dynamic> metadata}): _metadata = metadata;
  factory _StorageMediaResolution.fromJson(Map<String, dynamic> json) => _$StorageMediaResolutionFromJson(json);

@override final  StorageMediaRef mediaRef;
@override@UuidValueConverter() final  UuidValue objectId;
@override final  String sha;
@override final  String mimeType;
@override final  int sizeBytes;
@override final  String uri;
@override final  String uriScheme;
@override final  String? httpUrl;
@override final  String? cacheControl;
@override final  String? etag;
@override final  String? contentDisposition;
@override final  String? filename;
@override final  String? expiresAt;
 final  Map<String, dynamic> _metadata;
@override Map<String, dynamic> get metadata {
  if (_metadata is EqualUnmodifiableMapView) return _metadata;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_metadata);
}


/// Create a copy of StorageMediaResolution
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$StorageMediaResolutionCopyWith<_StorageMediaResolution> get copyWith => __$StorageMediaResolutionCopyWithImpl<_StorageMediaResolution>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$StorageMediaResolutionToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _StorageMediaResolution&&(identical(other.mediaRef, mediaRef) || other.mediaRef == mediaRef)&&(identical(other.objectId, objectId) || other.objectId == objectId)&&(identical(other.sha, sha) || other.sha == sha)&&(identical(other.mimeType, mimeType) || other.mimeType == mimeType)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.uri, uri) || other.uri == uri)&&(identical(other.uriScheme, uriScheme) || other.uriScheme == uriScheme)&&(identical(other.httpUrl, httpUrl) || other.httpUrl == httpUrl)&&(identical(other.cacheControl, cacheControl) || other.cacheControl == cacheControl)&&(identical(other.etag, etag) || other.etag == etag)&&(identical(other.contentDisposition, contentDisposition) || other.contentDisposition == contentDisposition)&&(identical(other.filename, filename) || other.filename == filename)&&(identical(other.expiresAt, expiresAt) || other.expiresAt == expiresAt)&&const DeepCollectionEquality().equals(other._metadata, _metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,mediaRef,objectId,sha,mimeType,sizeBytes,uri,uriScheme,httpUrl,cacheControl,etag,contentDisposition,filename,expiresAt,const DeepCollectionEquality().hash(_metadata));

@override
String toString() {
  return 'StorageMediaResolution.def(mediaRef: $mediaRef, objectId: $objectId, sha: $sha, mimeType: $mimeType, sizeBytes: $sizeBytes, uri: $uri, uriScheme: $uriScheme, httpUrl: $httpUrl, cacheControl: $cacheControl, etag: $etag, contentDisposition: $contentDisposition, filename: $filename, expiresAt: $expiresAt, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class _$StorageMediaResolutionCopyWith<$Res> implements $StorageMediaResolutionCopyWith<$Res> {
  factory _$StorageMediaResolutionCopyWith(_StorageMediaResolution value, $Res Function(_StorageMediaResolution) _then) = __$StorageMediaResolutionCopyWithImpl;
@override @useResult
$Res call({
 StorageMediaRef mediaRef,@UuidValueConverter() UuidValue objectId, String sha, String mimeType, int sizeBytes, String uri, String uriScheme, String? httpUrl, String? cacheControl, String? etag, String? contentDisposition, String? filename, String? expiresAt, Map<String, dynamic> metadata
});


@override $StorageMediaRefCopyWith<$Res> get mediaRef;

}
/// @nodoc
class __$StorageMediaResolutionCopyWithImpl<$Res>
    implements _$StorageMediaResolutionCopyWith<$Res> {
  __$StorageMediaResolutionCopyWithImpl(this._self, this._then);

  final _StorageMediaResolution _self;
  final $Res Function(_StorageMediaResolution) _then;

/// Create a copy of StorageMediaResolution
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? mediaRef = null,Object? objectId = null,Object? sha = null,Object? mimeType = null,Object? sizeBytes = null,Object? uri = null,Object? uriScheme = null,Object? httpUrl = freezed,Object? cacheControl = freezed,Object? etag = freezed,Object? contentDisposition = freezed,Object? filename = freezed,Object? expiresAt = freezed,Object? metadata = null,}) {
  return _then(_StorageMediaResolution(
mediaRef: null == mediaRef ? _self.mediaRef : mediaRef // ignore: cast_nullable_to_non_nullable
as StorageMediaRef,objectId: null == objectId ? _self.objectId : objectId // ignore: cast_nullable_to_non_nullable
as UuidValue,sha: null == sha ? _self.sha : sha // ignore: cast_nullable_to_non_nullable
as String,mimeType: null == mimeType ? _self.mimeType : mimeType // ignore: cast_nullable_to_non_nullable
as String,sizeBytes: null == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int,uri: null == uri ? _self.uri : uri // ignore: cast_nullable_to_non_nullable
as String,uriScheme: null == uriScheme ? _self.uriScheme : uriScheme // ignore: cast_nullable_to_non_nullable
as String,httpUrl: freezed == httpUrl ? _self.httpUrl : httpUrl // ignore: cast_nullable_to_non_nullable
as String?,cacheControl: freezed == cacheControl ? _self.cacheControl : cacheControl // ignore: cast_nullable_to_non_nullable
as String?,etag: freezed == etag ? _self.etag : etag // ignore: cast_nullable_to_non_nullable
as String?,contentDisposition: freezed == contentDisposition ? _self.contentDisposition : contentDisposition // ignore: cast_nullable_to_non_nullable
as String?,filename: freezed == filename ? _self.filename : filename // ignore: cast_nullable_to_non_nullable
as String?,expiresAt: freezed == expiresAt ? _self.expiresAt : expiresAt // ignore: cast_nullable_to_non_nullable
as String?,metadata: null == metadata ? _self._metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

/// Create a copy of StorageMediaResolution
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$StorageMediaRefCopyWith<$Res> get mediaRef {
  
  return $StorageMediaRefCopyWith<$Res>(_self.mediaRef, (value) {
    return _then(_self.copyWith(mediaRef: value));
  });
}
}


/// @nodoc
mixin _$StorageOperationReceipt {

 String get operation; String get status;@UuidValueConverter() UuidValue? get objectId; String? get sha; int? get sizeBytes; String? get mimeType; String get backendKind; String get dataPlane; Map<String, dynamic> get metadata;
/// Create a copy of StorageOperationReceipt
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$StorageOperationReceiptCopyWith<StorageOperationReceipt> get copyWith => _$StorageOperationReceiptCopyWithImpl<StorageOperationReceipt>(this as StorageOperationReceipt, _$identity);

  /// Serializes this StorageOperationReceipt to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is StorageOperationReceipt&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.status, status) || other.status == status)&&(identical(other.objectId, objectId) || other.objectId == objectId)&&(identical(other.sha, sha) || other.sha == sha)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.mimeType, mimeType) || other.mimeType == mimeType)&&(identical(other.backendKind, backendKind) || other.backendKind == backendKind)&&(identical(other.dataPlane, dataPlane) || other.dataPlane == dataPlane)&&const DeepCollectionEquality().equals(other.metadata, metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,status,objectId,sha,sizeBytes,mimeType,backendKind,dataPlane,const DeepCollectionEquality().hash(metadata));

@override
String toString() {
  return 'StorageOperationReceipt(operation: $operation, status: $status, objectId: $objectId, sha: $sha, sizeBytes: $sizeBytes, mimeType: $mimeType, backendKind: $backendKind, dataPlane: $dataPlane, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class $StorageOperationReceiptCopyWith<$Res>  {
  factory $StorageOperationReceiptCopyWith(StorageOperationReceipt value, $Res Function(StorageOperationReceipt) _then) = _$StorageOperationReceiptCopyWithImpl;
@useResult
$Res call({
 String operation, String status,@UuidValueConverter() UuidValue? objectId, String? sha, int? sizeBytes, String? mimeType, String backendKind, String dataPlane, Map<String, dynamic> metadata
});




}
/// @nodoc
class _$StorageOperationReceiptCopyWithImpl<$Res>
    implements $StorageOperationReceiptCopyWith<$Res> {
  _$StorageOperationReceiptCopyWithImpl(this._self, this._then);

  final StorageOperationReceipt _self;
  final $Res Function(StorageOperationReceipt) _then;

/// Create a copy of StorageOperationReceipt
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? operation = null,Object? status = null,Object? objectId = freezed,Object? sha = freezed,Object? sizeBytes = freezed,Object? mimeType = freezed,Object? backendKind = null,Object? dataPlane = null,Object? metadata = null,}) {
  return _then(_self.copyWith(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,objectId: freezed == objectId ? _self.objectId : objectId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sha: freezed == sha ? _self.sha : sha // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,mimeType: freezed == mimeType ? _self.mimeType : mimeType // ignore: cast_nullable_to_non_nullable
as String?,backendKind: null == backendKind ? _self.backendKind : backendKind // ignore: cast_nullable_to_non_nullable
as String,dataPlane: null == dataPlane ? _self.dataPlane : dataPlane // ignore: cast_nullable_to_non_nullable
as String,metadata: null == metadata ? _self.metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [StorageOperationReceipt].
extension StorageOperationReceiptPatterns on StorageOperationReceipt {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _StorageOperationReceipt value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _StorageOperationReceipt() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _StorageOperationReceipt value)  def,}){
final _that = this;
switch (_that) {
case _StorageOperationReceipt():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _StorageOperationReceipt value)?  def,}){
final _that = this;
switch (_that) {
case _StorageOperationReceipt() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String operation,  String status, @UuidValueConverter()  UuidValue? objectId,  String? sha,  int? sizeBytes,  String? mimeType,  String backendKind,  String dataPlane,  Map<String, dynamic> metadata)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _StorageOperationReceipt() when def != null:
return def(_that.operation,_that.status,_that.objectId,_that.sha,_that.sizeBytes,_that.mimeType,_that.backendKind,_that.dataPlane,_that.metadata);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String operation,  String status, @UuidValueConverter()  UuidValue? objectId,  String? sha,  int? sizeBytes,  String? mimeType,  String backendKind,  String dataPlane,  Map<String, dynamic> metadata)  def,}) {final _that = this;
switch (_that) {
case _StorageOperationReceipt():
return def(_that.operation,_that.status,_that.objectId,_that.sha,_that.sizeBytes,_that.mimeType,_that.backendKind,_that.dataPlane,_that.metadata);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String operation,  String status, @UuidValueConverter()  UuidValue? objectId,  String? sha,  int? sizeBytes,  String? mimeType,  String backendKind,  String dataPlane,  Map<String, dynamic> metadata)?  def,}) {final _that = this;
switch (_that) {
case _StorageOperationReceipt() when def != null:
return def(_that.operation,_that.status,_that.objectId,_that.sha,_that.sizeBytes,_that.mimeType,_that.backendKind,_that.dataPlane,_that.metadata);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _StorageOperationReceipt implements StorageOperationReceipt {
   _StorageOperationReceipt({required this.operation, required this.status, @UuidValueConverter() this.objectId, this.sha, this.sizeBytes, this.mimeType, required this.backendKind, required this.dataPlane, required final  Map<String, dynamic> metadata}): _metadata = metadata;
  factory _StorageOperationReceipt.fromJson(Map<String, dynamic> json) => _$StorageOperationReceiptFromJson(json);

@override final  String operation;
@override final  String status;
@override@UuidValueConverter() final  UuidValue? objectId;
@override final  String? sha;
@override final  int? sizeBytes;
@override final  String? mimeType;
@override final  String backendKind;
@override final  String dataPlane;
 final  Map<String, dynamic> _metadata;
@override Map<String, dynamic> get metadata {
  if (_metadata is EqualUnmodifiableMapView) return _metadata;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_metadata);
}


/// Create a copy of StorageOperationReceipt
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$StorageOperationReceiptCopyWith<_StorageOperationReceipt> get copyWith => __$StorageOperationReceiptCopyWithImpl<_StorageOperationReceipt>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$StorageOperationReceiptToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _StorageOperationReceipt&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.status, status) || other.status == status)&&(identical(other.objectId, objectId) || other.objectId == objectId)&&(identical(other.sha, sha) || other.sha == sha)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.mimeType, mimeType) || other.mimeType == mimeType)&&(identical(other.backendKind, backendKind) || other.backendKind == backendKind)&&(identical(other.dataPlane, dataPlane) || other.dataPlane == dataPlane)&&const DeepCollectionEquality().equals(other._metadata, _metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,status,objectId,sha,sizeBytes,mimeType,backendKind,dataPlane,const DeepCollectionEquality().hash(_metadata));

@override
String toString() {
  return 'StorageOperationReceipt.def(operation: $operation, status: $status, objectId: $objectId, sha: $sha, sizeBytes: $sizeBytes, mimeType: $mimeType, backendKind: $backendKind, dataPlane: $dataPlane, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class _$StorageOperationReceiptCopyWith<$Res> implements $StorageOperationReceiptCopyWith<$Res> {
  factory _$StorageOperationReceiptCopyWith(_StorageOperationReceipt value, $Res Function(_StorageOperationReceipt) _then) = __$StorageOperationReceiptCopyWithImpl;
@override @useResult
$Res call({
 String operation, String status,@UuidValueConverter() UuidValue? objectId, String? sha, int? sizeBytes, String? mimeType, String backendKind, String dataPlane, Map<String, dynamic> metadata
});




}
/// @nodoc
class __$StorageOperationReceiptCopyWithImpl<$Res>
    implements _$StorageOperationReceiptCopyWith<$Res> {
  __$StorageOperationReceiptCopyWithImpl(this._self, this._then);

  final _StorageOperationReceipt _self;
  final $Res Function(_StorageOperationReceipt) _then;

/// Create a copy of StorageOperationReceipt
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? operation = null,Object? status = null,Object? objectId = freezed,Object? sha = freezed,Object? sizeBytes = freezed,Object? mimeType = freezed,Object? backendKind = null,Object? dataPlane = null,Object? metadata = null,}) {
  return _then(_StorageOperationReceipt(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,objectId: freezed == objectId ? _self.objectId : objectId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sha: freezed == sha ? _self.sha : sha // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,mimeType: freezed == mimeType ? _self.mimeType : mimeType // ignore: cast_nullable_to_non_nullable
as String?,backendKind: null == backendKind ? _self.backendKind : backendKind // ignore: cast_nullable_to_non_nullable
as String,dataPlane: null == dataPlane ? _self.dataPlane : dataPlane // ignore: cast_nullable_to_non_nullable
as String,metadata: null == metadata ? _self._metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}

// dart format on
