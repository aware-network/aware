// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'content_service_operation_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$ContentTextPartV1 {

@UuidValueConverter() UuidValue? get contentPartContentId;@UuidValueConverter() UuidValue? get contentPartId;@UuidValueConverter() UuidValue? get contentPartTextId; int get position; String? get partKey; String get mediaType; String get text; String get digestAlgorithm; String? get digest; int get sizeBytes; String get sourceKind; Map<String, dynamic> get provenance;
/// Create a copy of ContentTextPartV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ContentTextPartV1CopyWith<ContentTextPartV1> get copyWith => _$ContentTextPartV1CopyWithImpl<ContentTextPartV1>(this as ContentTextPartV1, _$identity);

  /// Serializes this ContentTextPartV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ContentTextPartV1&&(identical(other.contentPartContentId, contentPartContentId) || other.contentPartContentId == contentPartContentId)&&(identical(other.contentPartId, contentPartId) || other.contentPartId == contentPartId)&&(identical(other.contentPartTextId, contentPartTextId) || other.contentPartTextId == contentPartTextId)&&(identical(other.position, position) || other.position == position)&&(identical(other.partKey, partKey) || other.partKey == partKey)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.text, text) || other.text == text)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.sourceKind, sourceKind) || other.sourceKind == sourceKind)&&const DeepCollectionEquality().equals(other.provenance, provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,contentPartContentId,contentPartId,contentPartTextId,position,partKey,mediaType,text,digestAlgorithm,digest,sizeBytes,sourceKind,const DeepCollectionEquality().hash(provenance));

@override
String toString() {
  return 'ContentTextPartV1(contentPartContentId: $contentPartContentId, contentPartId: $contentPartId, contentPartTextId: $contentPartTextId, position: $position, partKey: $partKey, mediaType: $mediaType, text: $text, digestAlgorithm: $digestAlgorithm, digest: $digest, sizeBytes: $sizeBytes, sourceKind: $sourceKind, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class $ContentTextPartV1CopyWith<$Res>  {
  factory $ContentTextPartV1CopyWith(ContentTextPartV1 value, $Res Function(ContentTextPartV1) _then) = _$ContentTextPartV1CopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? contentPartContentId,@UuidValueConverter() UuidValue? contentPartId,@UuidValueConverter() UuidValue? contentPartTextId, int position, String? partKey, String mediaType, String text, String digestAlgorithm, String? digest, int sizeBytes, String sourceKind, Map<String, dynamic> provenance
});




}
/// @nodoc
class _$ContentTextPartV1CopyWithImpl<$Res>
    implements $ContentTextPartV1CopyWith<$Res> {
  _$ContentTextPartV1CopyWithImpl(this._self, this._then);

  final ContentTextPartV1 _self;
  final $Res Function(ContentTextPartV1) _then;

/// Create a copy of ContentTextPartV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? contentPartContentId = freezed,Object? contentPartId = freezed,Object? contentPartTextId = freezed,Object? position = null,Object? partKey = freezed,Object? mediaType = null,Object? text = null,Object? digestAlgorithm = null,Object? digest = freezed,Object? sizeBytes = null,Object? sourceKind = null,Object? provenance = null,}) {
  return _then(_self.copyWith(
contentPartContentId: freezed == contentPartContentId ? _self.contentPartContentId : contentPartContentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,contentPartId: freezed == contentPartId ? _self.contentPartId : contentPartId // ignore: cast_nullable_to_non_nullable
as UuidValue?,contentPartTextId: freezed == contentPartTextId ? _self.contentPartTextId : contentPartTextId // ignore: cast_nullable_to_non_nullable
as UuidValue?,position: null == position ? _self.position : position // ignore: cast_nullable_to_non_nullable
as int,partKey: freezed == partKey ? _self.partKey : partKey // ignore: cast_nullable_to_non_nullable
as String?,mediaType: null == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String,text: null == text ? _self.text : text // ignore: cast_nullable_to_non_nullable
as String,digestAlgorithm: null == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: null == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int,sourceKind: null == sourceKind ? _self.sourceKind : sourceKind // ignore: cast_nullable_to_non_nullable
as String,provenance: null == provenance ? _self.provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [ContentTextPartV1].
extension ContentTextPartV1Patterns on ContentTextPartV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ContentTextPartV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ContentTextPartV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ContentTextPartV1 value)  def,}){
final _that = this;
switch (_that) {
case _ContentTextPartV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ContentTextPartV1 value)?  def,}){
final _that = this;
switch (_that) {
case _ContentTextPartV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? contentPartContentId, @UuidValueConverter()  UuidValue? contentPartId, @UuidValueConverter()  UuidValue? contentPartTextId,  int position,  String? partKey,  String mediaType,  String text,  String digestAlgorithm,  String? digest,  int sizeBytes,  String sourceKind,  Map<String, dynamic> provenance)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ContentTextPartV1() when def != null:
return def(_that.contentPartContentId,_that.contentPartId,_that.contentPartTextId,_that.position,_that.partKey,_that.mediaType,_that.text,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.sourceKind,_that.provenance);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? contentPartContentId, @UuidValueConverter()  UuidValue? contentPartId, @UuidValueConverter()  UuidValue? contentPartTextId,  int position,  String? partKey,  String mediaType,  String text,  String digestAlgorithm,  String? digest,  int sizeBytes,  String sourceKind,  Map<String, dynamic> provenance)  def,}) {final _that = this;
switch (_that) {
case _ContentTextPartV1():
return def(_that.contentPartContentId,_that.contentPartId,_that.contentPartTextId,_that.position,_that.partKey,_that.mediaType,_that.text,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.sourceKind,_that.provenance);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? contentPartContentId, @UuidValueConverter()  UuidValue? contentPartId, @UuidValueConverter()  UuidValue? contentPartTextId,  int position,  String? partKey,  String mediaType,  String text,  String digestAlgorithm,  String? digest,  int sizeBytes,  String sourceKind,  Map<String, dynamic> provenance)?  def,}) {final _that = this;
switch (_that) {
case _ContentTextPartV1() when def != null:
return def(_that.contentPartContentId,_that.contentPartId,_that.contentPartTextId,_that.position,_that.partKey,_that.mediaType,_that.text,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.sourceKind,_that.provenance);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ContentTextPartV1 implements ContentTextPartV1 {
   _ContentTextPartV1({@UuidValueConverter() this.contentPartContentId, @UuidValueConverter() this.contentPartId, @UuidValueConverter() this.contentPartTextId, required this.position, this.partKey, required this.mediaType, required this.text, required this.digestAlgorithm, this.digest, required this.sizeBytes, required this.sourceKind, required final  Map<String, dynamic> provenance}): _provenance = provenance;
  factory _ContentTextPartV1.fromJson(Map<String, dynamic> json) => _$ContentTextPartV1FromJson(json);

@override@UuidValueConverter() final  UuidValue? contentPartContentId;
@override@UuidValueConverter() final  UuidValue? contentPartId;
@override@UuidValueConverter() final  UuidValue? contentPartTextId;
@override final  int position;
@override final  String? partKey;
@override final  String mediaType;
@override final  String text;
@override final  String digestAlgorithm;
@override final  String? digest;
@override final  int sizeBytes;
@override final  String sourceKind;
 final  Map<String, dynamic> _provenance;
@override Map<String, dynamic> get provenance {
  if (_provenance is EqualUnmodifiableMapView) return _provenance;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_provenance);
}


/// Create a copy of ContentTextPartV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ContentTextPartV1CopyWith<_ContentTextPartV1> get copyWith => __$ContentTextPartV1CopyWithImpl<_ContentTextPartV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ContentTextPartV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ContentTextPartV1&&(identical(other.contentPartContentId, contentPartContentId) || other.contentPartContentId == contentPartContentId)&&(identical(other.contentPartId, contentPartId) || other.contentPartId == contentPartId)&&(identical(other.contentPartTextId, contentPartTextId) || other.contentPartTextId == contentPartTextId)&&(identical(other.position, position) || other.position == position)&&(identical(other.partKey, partKey) || other.partKey == partKey)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.text, text) || other.text == text)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.sourceKind, sourceKind) || other.sourceKind == sourceKind)&&const DeepCollectionEquality().equals(other._provenance, _provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,contentPartContentId,contentPartId,contentPartTextId,position,partKey,mediaType,text,digestAlgorithm,digest,sizeBytes,sourceKind,const DeepCollectionEquality().hash(_provenance));

@override
String toString() {
  return 'ContentTextPartV1.def(contentPartContentId: $contentPartContentId, contentPartId: $contentPartId, contentPartTextId: $contentPartTextId, position: $position, partKey: $partKey, mediaType: $mediaType, text: $text, digestAlgorithm: $digestAlgorithm, digest: $digest, sizeBytes: $sizeBytes, sourceKind: $sourceKind, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class _$ContentTextPartV1CopyWith<$Res> implements $ContentTextPartV1CopyWith<$Res> {
  factory _$ContentTextPartV1CopyWith(_ContentTextPartV1 value, $Res Function(_ContentTextPartV1) _then) = __$ContentTextPartV1CopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? contentPartContentId,@UuidValueConverter() UuidValue? contentPartId,@UuidValueConverter() UuidValue? contentPartTextId, int position, String? partKey, String mediaType, String text, String digestAlgorithm, String? digest, int sizeBytes, String sourceKind, Map<String, dynamic> provenance
});




}
/// @nodoc
class __$ContentTextPartV1CopyWithImpl<$Res>
    implements _$ContentTextPartV1CopyWith<$Res> {
  __$ContentTextPartV1CopyWithImpl(this._self, this._then);

  final _ContentTextPartV1 _self;
  final $Res Function(_ContentTextPartV1) _then;

/// Create a copy of ContentTextPartV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? contentPartContentId = freezed,Object? contentPartId = freezed,Object? contentPartTextId = freezed,Object? position = null,Object? partKey = freezed,Object? mediaType = null,Object? text = null,Object? digestAlgorithm = null,Object? digest = freezed,Object? sizeBytes = null,Object? sourceKind = null,Object? provenance = null,}) {
  return _then(_ContentTextPartV1(
contentPartContentId: freezed == contentPartContentId ? _self.contentPartContentId : contentPartContentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,contentPartId: freezed == contentPartId ? _self.contentPartId : contentPartId // ignore: cast_nullable_to_non_nullable
as UuidValue?,contentPartTextId: freezed == contentPartTextId ? _self.contentPartTextId : contentPartTextId // ignore: cast_nullable_to_non_nullable
as UuidValue?,position: null == position ? _self.position : position // ignore: cast_nullable_to_non_nullable
as int,partKey: freezed == partKey ? _self.partKey : partKey // ignore: cast_nullable_to_non_nullable
as String?,mediaType: null == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String,text: null == text ? _self.text : text // ignore: cast_nullable_to_non_nullable
as String,digestAlgorithm: null == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: null == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int,sourceKind: null == sourceKind ? _self.sourceKind : sourceKind // ignore: cast_nullable_to_non_nullable
as String,provenance: null == provenance ? _self._provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$ContentTextResolutionV1 {

@UuidValueConverter() UuidValue get contentId; String? get contentKey; String? get title; String get mediaType; String get text; List<ContentTextPartV1> get parts; String get digestAlgorithm; String? get digest; int get sizeBytes; String get sourceKind; Map<String, dynamic> get provenance;
/// Create a copy of ContentTextResolutionV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ContentTextResolutionV1CopyWith<ContentTextResolutionV1> get copyWith => _$ContentTextResolutionV1CopyWithImpl<ContentTextResolutionV1>(this as ContentTextResolutionV1, _$identity);

  /// Serializes this ContentTextResolutionV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ContentTextResolutionV1&&(identical(other.contentId, contentId) || other.contentId == contentId)&&(identical(other.contentKey, contentKey) || other.contentKey == contentKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.text, text) || other.text == text)&&const DeepCollectionEquality().equals(other.parts, parts)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.sourceKind, sourceKind) || other.sourceKind == sourceKind)&&const DeepCollectionEquality().equals(other.provenance, provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,contentId,contentKey,title,mediaType,text,const DeepCollectionEquality().hash(parts),digestAlgorithm,digest,sizeBytes,sourceKind,const DeepCollectionEquality().hash(provenance));

@override
String toString() {
  return 'ContentTextResolutionV1(contentId: $contentId, contentKey: $contentKey, title: $title, mediaType: $mediaType, text: $text, parts: $parts, digestAlgorithm: $digestAlgorithm, digest: $digest, sizeBytes: $sizeBytes, sourceKind: $sourceKind, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class $ContentTextResolutionV1CopyWith<$Res>  {
  factory $ContentTextResolutionV1CopyWith(ContentTextResolutionV1 value, $Res Function(ContentTextResolutionV1) _then) = _$ContentTextResolutionV1CopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue contentId, String? contentKey, String? title, String mediaType, String text, List<ContentTextPartV1> parts, String digestAlgorithm, String? digest, int sizeBytes, String sourceKind, Map<String, dynamic> provenance
});




}
/// @nodoc
class _$ContentTextResolutionV1CopyWithImpl<$Res>
    implements $ContentTextResolutionV1CopyWith<$Res> {
  _$ContentTextResolutionV1CopyWithImpl(this._self, this._then);

  final ContentTextResolutionV1 _self;
  final $Res Function(ContentTextResolutionV1) _then;

/// Create a copy of ContentTextResolutionV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? contentId = null,Object? contentKey = freezed,Object? title = freezed,Object? mediaType = null,Object? text = null,Object? parts = null,Object? digestAlgorithm = null,Object? digest = freezed,Object? sizeBytes = null,Object? sourceKind = null,Object? provenance = null,}) {
  return _then(_self.copyWith(
contentId: null == contentId ? _self.contentId : contentId // ignore: cast_nullable_to_non_nullable
as UuidValue,contentKey: freezed == contentKey ? _self.contentKey : contentKey // ignore: cast_nullable_to_non_nullable
as String?,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,mediaType: null == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String,text: null == text ? _self.text : text // ignore: cast_nullable_to_non_nullable
as String,parts: null == parts ? _self.parts : parts // ignore: cast_nullable_to_non_nullable
as List<ContentTextPartV1>,digestAlgorithm: null == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: null == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int,sourceKind: null == sourceKind ? _self.sourceKind : sourceKind // ignore: cast_nullable_to_non_nullable
as String,provenance: null == provenance ? _self.provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [ContentTextResolutionV1].
extension ContentTextResolutionV1Patterns on ContentTextResolutionV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ContentTextResolutionV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ContentTextResolutionV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ContentTextResolutionV1 value)  def,}){
final _that = this;
switch (_that) {
case _ContentTextResolutionV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ContentTextResolutionV1 value)?  def,}){
final _that = this;
switch (_that) {
case _ContentTextResolutionV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue contentId,  String? contentKey,  String? title,  String mediaType,  String text,  List<ContentTextPartV1> parts,  String digestAlgorithm,  String? digest,  int sizeBytes,  String sourceKind,  Map<String, dynamic> provenance)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ContentTextResolutionV1() when def != null:
return def(_that.contentId,_that.contentKey,_that.title,_that.mediaType,_that.text,_that.parts,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.sourceKind,_that.provenance);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue contentId,  String? contentKey,  String? title,  String mediaType,  String text,  List<ContentTextPartV1> parts,  String digestAlgorithm,  String? digest,  int sizeBytes,  String sourceKind,  Map<String, dynamic> provenance)  def,}) {final _that = this;
switch (_that) {
case _ContentTextResolutionV1():
return def(_that.contentId,_that.contentKey,_that.title,_that.mediaType,_that.text,_that.parts,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.sourceKind,_that.provenance);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue contentId,  String? contentKey,  String? title,  String mediaType,  String text,  List<ContentTextPartV1> parts,  String digestAlgorithm,  String? digest,  int sizeBytes,  String sourceKind,  Map<String, dynamic> provenance)?  def,}) {final _that = this;
switch (_that) {
case _ContentTextResolutionV1() when def != null:
return def(_that.contentId,_that.contentKey,_that.title,_that.mediaType,_that.text,_that.parts,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.sourceKind,_that.provenance);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ContentTextResolutionV1 implements ContentTextResolutionV1 {
   _ContentTextResolutionV1({@UuidValueConverter() required this.contentId, this.contentKey, this.title, required this.mediaType, required this.text, final  List<ContentTextPartV1> parts = const [], required this.digestAlgorithm, this.digest, required this.sizeBytes, required this.sourceKind, required final  Map<String, dynamic> provenance}): _parts = parts,_provenance = provenance;
  factory _ContentTextResolutionV1.fromJson(Map<String, dynamic> json) => _$ContentTextResolutionV1FromJson(json);

@override@UuidValueConverter() final  UuidValue contentId;
@override final  String? contentKey;
@override final  String? title;
@override final  String mediaType;
@override final  String text;
 final  List<ContentTextPartV1> _parts;
@override@JsonKey() List<ContentTextPartV1> get parts {
  if (_parts is EqualUnmodifiableListView) return _parts;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_parts);
}

@override final  String digestAlgorithm;
@override final  String? digest;
@override final  int sizeBytes;
@override final  String sourceKind;
 final  Map<String, dynamic> _provenance;
@override Map<String, dynamic> get provenance {
  if (_provenance is EqualUnmodifiableMapView) return _provenance;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_provenance);
}


/// Create a copy of ContentTextResolutionV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ContentTextResolutionV1CopyWith<_ContentTextResolutionV1> get copyWith => __$ContentTextResolutionV1CopyWithImpl<_ContentTextResolutionV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ContentTextResolutionV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ContentTextResolutionV1&&(identical(other.contentId, contentId) || other.contentId == contentId)&&(identical(other.contentKey, contentKey) || other.contentKey == contentKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.text, text) || other.text == text)&&const DeepCollectionEquality().equals(other._parts, _parts)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.sourceKind, sourceKind) || other.sourceKind == sourceKind)&&const DeepCollectionEquality().equals(other._provenance, _provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,contentId,contentKey,title,mediaType,text,const DeepCollectionEquality().hash(_parts),digestAlgorithm,digest,sizeBytes,sourceKind,const DeepCollectionEquality().hash(_provenance));

@override
String toString() {
  return 'ContentTextResolutionV1.def(contentId: $contentId, contentKey: $contentKey, title: $title, mediaType: $mediaType, text: $text, parts: $parts, digestAlgorithm: $digestAlgorithm, digest: $digest, sizeBytes: $sizeBytes, sourceKind: $sourceKind, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class _$ContentTextResolutionV1CopyWith<$Res> implements $ContentTextResolutionV1CopyWith<$Res> {
  factory _$ContentTextResolutionV1CopyWith(_ContentTextResolutionV1 value, $Res Function(_ContentTextResolutionV1) _then) = __$ContentTextResolutionV1CopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue contentId, String? contentKey, String? title, String mediaType, String text, List<ContentTextPartV1> parts, String digestAlgorithm, String? digest, int sizeBytes, String sourceKind, Map<String, dynamic> provenance
});




}
/// @nodoc
class __$ContentTextResolutionV1CopyWithImpl<$Res>
    implements _$ContentTextResolutionV1CopyWith<$Res> {
  __$ContentTextResolutionV1CopyWithImpl(this._self, this._then);

  final _ContentTextResolutionV1 _self;
  final $Res Function(_ContentTextResolutionV1) _then;

/// Create a copy of ContentTextResolutionV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? contentId = null,Object? contentKey = freezed,Object? title = freezed,Object? mediaType = null,Object? text = null,Object? parts = null,Object? digestAlgorithm = null,Object? digest = freezed,Object? sizeBytes = null,Object? sourceKind = null,Object? provenance = null,}) {
  return _then(_ContentTextResolutionV1(
contentId: null == contentId ? _self.contentId : contentId // ignore: cast_nullable_to_non_nullable
as UuidValue,contentKey: freezed == contentKey ? _self.contentKey : contentKey // ignore: cast_nullable_to_non_nullable
as String?,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,mediaType: null == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String,text: null == text ? _self.text : text // ignore: cast_nullable_to_non_nullable
as String,parts: null == parts ? _self._parts : parts // ignore: cast_nullable_to_non_nullable
as List<ContentTextPartV1>,digestAlgorithm: null == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: null == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int,sourceKind: null == sourceKind ? _self.sourceKind : sourceKind // ignore: cast_nullable_to_non_nullable
as String,provenance: null == provenance ? _self._provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$ContentTextCommitPartV1 {

 int get position; String? get partKey; String get mediaType; String get text; String get digestAlgorithm; String? get digest; int? get sizeBytes; Map<String, dynamic> get provenance;
/// Create a copy of ContentTextCommitPartV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ContentTextCommitPartV1CopyWith<ContentTextCommitPartV1> get copyWith => _$ContentTextCommitPartV1CopyWithImpl<ContentTextCommitPartV1>(this as ContentTextCommitPartV1, _$identity);

  /// Serializes this ContentTextCommitPartV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ContentTextCommitPartV1&&(identical(other.position, position) || other.position == position)&&(identical(other.partKey, partKey) || other.partKey == partKey)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.text, text) || other.text == text)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&const DeepCollectionEquality().equals(other.provenance, provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,position,partKey,mediaType,text,digestAlgorithm,digest,sizeBytes,const DeepCollectionEquality().hash(provenance));

@override
String toString() {
  return 'ContentTextCommitPartV1(position: $position, partKey: $partKey, mediaType: $mediaType, text: $text, digestAlgorithm: $digestAlgorithm, digest: $digest, sizeBytes: $sizeBytes, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class $ContentTextCommitPartV1CopyWith<$Res>  {
  factory $ContentTextCommitPartV1CopyWith(ContentTextCommitPartV1 value, $Res Function(ContentTextCommitPartV1) _then) = _$ContentTextCommitPartV1CopyWithImpl;
@useResult
$Res call({
 int position, String? partKey, String mediaType, String text, String digestAlgorithm, String? digest, int? sizeBytes, Map<String, dynamic> provenance
});




}
/// @nodoc
class _$ContentTextCommitPartV1CopyWithImpl<$Res>
    implements $ContentTextCommitPartV1CopyWith<$Res> {
  _$ContentTextCommitPartV1CopyWithImpl(this._self, this._then);

  final ContentTextCommitPartV1 _self;
  final $Res Function(ContentTextCommitPartV1) _then;

/// Create a copy of ContentTextCommitPartV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? position = null,Object? partKey = freezed,Object? mediaType = null,Object? text = null,Object? digestAlgorithm = null,Object? digest = freezed,Object? sizeBytes = freezed,Object? provenance = null,}) {
  return _then(_self.copyWith(
position: null == position ? _self.position : position // ignore: cast_nullable_to_non_nullable
as int,partKey: freezed == partKey ? _self.partKey : partKey // ignore: cast_nullable_to_non_nullable
as String?,mediaType: null == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String,text: null == text ? _self.text : text // ignore: cast_nullable_to_non_nullable
as String,digestAlgorithm: null == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,provenance: null == provenance ? _self.provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [ContentTextCommitPartV1].
extension ContentTextCommitPartV1Patterns on ContentTextCommitPartV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ContentTextCommitPartV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ContentTextCommitPartV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ContentTextCommitPartV1 value)  def,}){
final _that = this;
switch (_that) {
case _ContentTextCommitPartV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ContentTextCommitPartV1 value)?  def,}){
final _that = this;
switch (_that) {
case _ContentTextCommitPartV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( int position,  String? partKey,  String mediaType,  String text,  String digestAlgorithm,  String? digest,  int? sizeBytes,  Map<String, dynamic> provenance)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ContentTextCommitPartV1() when def != null:
return def(_that.position,_that.partKey,_that.mediaType,_that.text,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.provenance);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( int position,  String? partKey,  String mediaType,  String text,  String digestAlgorithm,  String? digest,  int? sizeBytes,  Map<String, dynamic> provenance)  def,}) {final _that = this;
switch (_that) {
case _ContentTextCommitPartV1():
return def(_that.position,_that.partKey,_that.mediaType,_that.text,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.provenance);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( int position,  String? partKey,  String mediaType,  String text,  String digestAlgorithm,  String? digest,  int? sizeBytes,  Map<String, dynamic> provenance)?  def,}) {final _that = this;
switch (_that) {
case _ContentTextCommitPartV1() when def != null:
return def(_that.position,_that.partKey,_that.mediaType,_that.text,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.provenance);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ContentTextCommitPartV1 implements ContentTextCommitPartV1 {
   _ContentTextCommitPartV1({required this.position, this.partKey, required this.mediaType, required this.text, required this.digestAlgorithm, this.digest, this.sizeBytes, required final  Map<String, dynamic> provenance}): _provenance = provenance;
  factory _ContentTextCommitPartV1.fromJson(Map<String, dynamic> json) => _$ContentTextCommitPartV1FromJson(json);

@override final  int position;
@override final  String? partKey;
@override final  String mediaType;
@override final  String text;
@override final  String digestAlgorithm;
@override final  String? digest;
@override final  int? sizeBytes;
 final  Map<String, dynamic> _provenance;
@override Map<String, dynamic> get provenance {
  if (_provenance is EqualUnmodifiableMapView) return _provenance;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_provenance);
}


/// Create a copy of ContentTextCommitPartV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ContentTextCommitPartV1CopyWith<_ContentTextCommitPartV1> get copyWith => __$ContentTextCommitPartV1CopyWithImpl<_ContentTextCommitPartV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ContentTextCommitPartV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ContentTextCommitPartV1&&(identical(other.position, position) || other.position == position)&&(identical(other.partKey, partKey) || other.partKey == partKey)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.text, text) || other.text == text)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&const DeepCollectionEquality().equals(other._provenance, _provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,position,partKey,mediaType,text,digestAlgorithm,digest,sizeBytes,const DeepCollectionEquality().hash(_provenance));

@override
String toString() {
  return 'ContentTextCommitPartV1.def(position: $position, partKey: $partKey, mediaType: $mediaType, text: $text, digestAlgorithm: $digestAlgorithm, digest: $digest, sizeBytes: $sizeBytes, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class _$ContentTextCommitPartV1CopyWith<$Res> implements $ContentTextCommitPartV1CopyWith<$Res> {
  factory _$ContentTextCommitPartV1CopyWith(_ContentTextCommitPartV1 value, $Res Function(_ContentTextCommitPartV1) _then) = __$ContentTextCommitPartV1CopyWithImpl;
@override @useResult
$Res call({
 int position, String? partKey, String mediaType, String text, String digestAlgorithm, String? digest, int? sizeBytes, Map<String, dynamic> provenance
});




}
/// @nodoc
class __$ContentTextCommitPartV1CopyWithImpl<$Res>
    implements _$ContentTextCommitPartV1CopyWith<$Res> {
  __$ContentTextCommitPartV1CopyWithImpl(this._self, this._then);

  final _ContentTextCommitPartV1 _self;
  final $Res Function(_ContentTextCommitPartV1) _then;

/// Create a copy of ContentTextCommitPartV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? position = null,Object? partKey = freezed,Object? mediaType = null,Object? text = null,Object? digestAlgorithm = null,Object? digest = freezed,Object? sizeBytes = freezed,Object? provenance = null,}) {
  return _then(_ContentTextCommitPartV1(
position: null == position ? _self.position : position // ignore: cast_nullable_to_non_nullable
as int,partKey: freezed == partKey ? _self.partKey : partKey // ignore: cast_nullable_to_non_nullable
as String?,mediaType: null == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String,text: null == text ? _self.text : text // ignore: cast_nullable_to_non_nullable
as String,digestAlgorithm: null == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,provenance: null == provenance ? _self._provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$ContentTextCommitResultV1 {

@UuidValueConverter() UuidValue get contentId; String get contentKey; String? get title; String get sourceKind; String get sourceRef; String get mediaType; String get digestAlgorithm; String get digest; int get sizeBytes;@UuidValueConverter() UuidValue? get domainCommitId;@UuidValueConverter() UuidValue? get objectInstanceGraphCommitId; String? get serviceHostReceiptRef; Map<String, dynamic> get provenance;
/// Create a copy of ContentTextCommitResultV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ContentTextCommitResultV1CopyWith<ContentTextCommitResultV1> get copyWith => _$ContentTextCommitResultV1CopyWithImpl<ContentTextCommitResultV1>(this as ContentTextCommitResultV1, _$identity);

  /// Serializes this ContentTextCommitResultV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ContentTextCommitResultV1&&(identical(other.contentId, contentId) || other.contentId == contentId)&&(identical(other.contentKey, contentKey) || other.contentKey == contentKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.sourceKind, sourceKind) || other.sourceKind == sourceKind)&&(identical(other.sourceRef, sourceRef) || other.sourceRef == sourceRef)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.domainCommitId, domainCommitId) || other.domainCommitId == domainCommitId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.serviceHostReceiptRef, serviceHostReceiptRef) || other.serviceHostReceiptRef == serviceHostReceiptRef)&&const DeepCollectionEquality().equals(other.provenance, provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,contentId,contentKey,title,sourceKind,sourceRef,mediaType,digestAlgorithm,digest,sizeBytes,domainCommitId,objectInstanceGraphCommitId,serviceHostReceiptRef,const DeepCollectionEquality().hash(provenance));

@override
String toString() {
  return 'ContentTextCommitResultV1(contentId: $contentId, contentKey: $contentKey, title: $title, sourceKind: $sourceKind, sourceRef: $sourceRef, mediaType: $mediaType, digestAlgorithm: $digestAlgorithm, digest: $digest, sizeBytes: $sizeBytes, domainCommitId: $domainCommitId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, serviceHostReceiptRef: $serviceHostReceiptRef, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class $ContentTextCommitResultV1CopyWith<$Res>  {
  factory $ContentTextCommitResultV1CopyWith(ContentTextCommitResultV1 value, $Res Function(ContentTextCommitResultV1) _then) = _$ContentTextCommitResultV1CopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue contentId, String contentKey, String? title, String sourceKind, String sourceRef, String mediaType, String digestAlgorithm, String digest, int sizeBytes,@UuidValueConverter() UuidValue? domainCommitId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String? serviceHostReceiptRef, Map<String, dynamic> provenance
});




}
/// @nodoc
class _$ContentTextCommitResultV1CopyWithImpl<$Res>
    implements $ContentTextCommitResultV1CopyWith<$Res> {
  _$ContentTextCommitResultV1CopyWithImpl(this._self, this._then);

  final ContentTextCommitResultV1 _self;
  final $Res Function(ContentTextCommitResultV1) _then;

/// Create a copy of ContentTextCommitResultV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? contentId = null,Object? contentKey = null,Object? title = freezed,Object? sourceKind = null,Object? sourceRef = null,Object? mediaType = null,Object? digestAlgorithm = null,Object? digest = null,Object? sizeBytes = null,Object? domainCommitId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? serviceHostReceiptRef = freezed,Object? provenance = null,}) {
  return _then(_self.copyWith(
contentId: null == contentId ? _self.contentId : contentId // ignore: cast_nullable_to_non_nullable
as UuidValue,contentKey: null == contentKey ? _self.contentKey : contentKey // ignore: cast_nullable_to_non_nullable
as String,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,sourceKind: null == sourceKind ? _self.sourceKind : sourceKind // ignore: cast_nullable_to_non_nullable
as String,sourceRef: null == sourceRef ? _self.sourceRef : sourceRef // ignore: cast_nullable_to_non_nullable
as String,mediaType: null == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String,digestAlgorithm: null == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String,digest: null == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String,sizeBytes: null == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int,domainCommitId: freezed == domainCommitId ? _self.domainCommitId : domainCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceHostReceiptRef: freezed == serviceHostReceiptRef ? _self.serviceHostReceiptRef : serviceHostReceiptRef // ignore: cast_nullable_to_non_nullable
as String?,provenance: null == provenance ? _self.provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [ContentTextCommitResultV1].
extension ContentTextCommitResultV1Patterns on ContentTextCommitResultV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ContentTextCommitResultV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ContentTextCommitResultV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ContentTextCommitResultV1 value)  def,}){
final _that = this;
switch (_that) {
case _ContentTextCommitResultV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ContentTextCommitResultV1 value)?  def,}){
final _that = this;
switch (_that) {
case _ContentTextCommitResultV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue contentId,  String contentKey,  String? title,  String sourceKind,  String sourceRef,  String mediaType,  String digestAlgorithm,  String digest,  int sizeBytes, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? serviceHostReceiptRef,  Map<String, dynamic> provenance)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ContentTextCommitResultV1() when def != null:
return def(_that.contentId,_that.contentKey,_that.title,_that.sourceKind,_that.sourceRef,_that.mediaType,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.serviceHostReceiptRef,_that.provenance);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue contentId,  String contentKey,  String? title,  String sourceKind,  String sourceRef,  String mediaType,  String digestAlgorithm,  String digest,  int sizeBytes, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? serviceHostReceiptRef,  Map<String, dynamic> provenance)  def,}) {final _that = this;
switch (_that) {
case _ContentTextCommitResultV1():
return def(_that.contentId,_that.contentKey,_that.title,_that.sourceKind,_that.sourceRef,_that.mediaType,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.serviceHostReceiptRef,_that.provenance);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue contentId,  String contentKey,  String? title,  String sourceKind,  String sourceRef,  String mediaType,  String digestAlgorithm,  String digest,  int sizeBytes, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? serviceHostReceiptRef,  Map<String, dynamic> provenance)?  def,}) {final _that = this;
switch (_that) {
case _ContentTextCommitResultV1() when def != null:
return def(_that.contentId,_that.contentKey,_that.title,_that.sourceKind,_that.sourceRef,_that.mediaType,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.serviceHostReceiptRef,_that.provenance);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ContentTextCommitResultV1 implements ContentTextCommitResultV1 {
   _ContentTextCommitResultV1({@UuidValueConverter() required this.contentId, required this.contentKey, this.title, required this.sourceKind, required this.sourceRef, required this.mediaType, required this.digestAlgorithm, required this.digest, required this.sizeBytes, @UuidValueConverter() this.domainCommitId, @UuidValueConverter() this.objectInstanceGraphCommitId, this.serviceHostReceiptRef, required final  Map<String, dynamic> provenance}): _provenance = provenance;
  factory _ContentTextCommitResultV1.fromJson(Map<String, dynamic> json) => _$ContentTextCommitResultV1FromJson(json);

@override@UuidValueConverter() final  UuidValue contentId;
@override final  String contentKey;
@override final  String? title;
@override final  String sourceKind;
@override final  String sourceRef;
@override final  String mediaType;
@override final  String digestAlgorithm;
@override final  String digest;
@override final  int sizeBytes;
@override@UuidValueConverter() final  UuidValue? domainCommitId;
@override@UuidValueConverter() final  UuidValue? objectInstanceGraphCommitId;
@override final  String? serviceHostReceiptRef;
 final  Map<String, dynamic> _provenance;
@override Map<String, dynamic> get provenance {
  if (_provenance is EqualUnmodifiableMapView) return _provenance;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_provenance);
}


/// Create a copy of ContentTextCommitResultV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ContentTextCommitResultV1CopyWith<_ContentTextCommitResultV1> get copyWith => __$ContentTextCommitResultV1CopyWithImpl<_ContentTextCommitResultV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ContentTextCommitResultV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ContentTextCommitResultV1&&(identical(other.contentId, contentId) || other.contentId == contentId)&&(identical(other.contentKey, contentKey) || other.contentKey == contentKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.sourceKind, sourceKind) || other.sourceKind == sourceKind)&&(identical(other.sourceRef, sourceRef) || other.sourceRef == sourceRef)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.domainCommitId, domainCommitId) || other.domainCommitId == domainCommitId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.serviceHostReceiptRef, serviceHostReceiptRef) || other.serviceHostReceiptRef == serviceHostReceiptRef)&&const DeepCollectionEquality().equals(other._provenance, _provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,contentId,contentKey,title,sourceKind,sourceRef,mediaType,digestAlgorithm,digest,sizeBytes,domainCommitId,objectInstanceGraphCommitId,serviceHostReceiptRef,const DeepCollectionEquality().hash(_provenance));

@override
String toString() {
  return 'ContentTextCommitResultV1.def(contentId: $contentId, contentKey: $contentKey, title: $title, sourceKind: $sourceKind, sourceRef: $sourceRef, mediaType: $mediaType, digestAlgorithm: $digestAlgorithm, digest: $digest, sizeBytes: $sizeBytes, domainCommitId: $domainCommitId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, serviceHostReceiptRef: $serviceHostReceiptRef, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class _$ContentTextCommitResultV1CopyWith<$Res> implements $ContentTextCommitResultV1CopyWith<$Res> {
  factory _$ContentTextCommitResultV1CopyWith(_ContentTextCommitResultV1 value, $Res Function(_ContentTextCommitResultV1) _then) = __$ContentTextCommitResultV1CopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue contentId, String contentKey, String? title, String sourceKind, String sourceRef, String mediaType, String digestAlgorithm, String digest, int sizeBytes,@UuidValueConverter() UuidValue? domainCommitId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String? serviceHostReceiptRef, Map<String, dynamic> provenance
});




}
/// @nodoc
class __$ContentTextCommitResultV1CopyWithImpl<$Res>
    implements _$ContentTextCommitResultV1CopyWith<$Res> {
  __$ContentTextCommitResultV1CopyWithImpl(this._self, this._then);

  final _ContentTextCommitResultV1 _self;
  final $Res Function(_ContentTextCommitResultV1) _then;

/// Create a copy of ContentTextCommitResultV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? contentId = null,Object? contentKey = null,Object? title = freezed,Object? sourceKind = null,Object? sourceRef = null,Object? mediaType = null,Object? digestAlgorithm = null,Object? digest = null,Object? sizeBytes = null,Object? domainCommitId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? serviceHostReceiptRef = freezed,Object? provenance = null,}) {
  return _then(_ContentTextCommitResultV1(
contentId: null == contentId ? _self.contentId : contentId // ignore: cast_nullable_to_non_nullable
as UuidValue,contentKey: null == contentKey ? _self.contentKey : contentKey // ignore: cast_nullable_to_non_nullable
as String,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,sourceKind: null == sourceKind ? _self.sourceKind : sourceKind // ignore: cast_nullable_to_non_nullable
as String,sourceRef: null == sourceRef ? _self.sourceRef : sourceRef // ignore: cast_nullable_to_non_nullable
as String,mediaType: null == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String,digestAlgorithm: null == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String,digest: null == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String,sizeBytes: null == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int,domainCommitId: freezed == domainCommitId ? _self.domainCommitId : domainCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceHostReceiptRef: freezed == serviceHostReceiptRef ? _self.serviceHostReceiptRef : serviceHostReceiptRef // ignore: cast_nullable_to_non_nullable
as String?,provenance: null == provenance ? _self._provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$ContentPackageExportPartV1 {

 String get partKey; int get position; String get modalityType; String get contentPartType; String get mediaType; String? get text; String? get rawPath; String? get uri; String? get providerId; String get digestAlgorithm; String? get digest; int? get sizeBytes; Map<String, dynamic> get awareContentMapping; Map<String, dynamic> get provenance;
/// Create a copy of ContentPackageExportPartV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ContentPackageExportPartV1CopyWith<ContentPackageExportPartV1> get copyWith => _$ContentPackageExportPartV1CopyWithImpl<ContentPackageExportPartV1>(this as ContentPackageExportPartV1, _$identity);

  /// Serializes this ContentPackageExportPartV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ContentPackageExportPartV1&&(identical(other.partKey, partKey) || other.partKey == partKey)&&(identical(other.position, position) || other.position == position)&&(identical(other.modalityType, modalityType) || other.modalityType == modalityType)&&(identical(other.contentPartType, contentPartType) || other.contentPartType == contentPartType)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.text, text) || other.text == text)&&(identical(other.rawPath, rawPath) || other.rawPath == rawPath)&&(identical(other.uri, uri) || other.uri == uri)&&(identical(other.providerId, providerId) || other.providerId == providerId)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&const DeepCollectionEquality().equals(other.awareContentMapping, awareContentMapping)&&const DeepCollectionEquality().equals(other.provenance, provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,partKey,position,modalityType,contentPartType,mediaType,text,rawPath,uri,providerId,digestAlgorithm,digest,sizeBytes,const DeepCollectionEquality().hash(awareContentMapping),const DeepCollectionEquality().hash(provenance));

@override
String toString() {
  return 'ContentPackageExportPartV1(partKey: $partKey, position: $position, modalityType: $modalityType, contentPartType: $contentPartType, mediaType: $mediaType, text: $text, rawPath: $rawPath, uri: $uri, providerId: $providerId, digestAlgorithm: $digestAlgorithm, digest: $digest, sizeBytes: $sizeBytes, awareContentMapping: $awareContentMapping, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class $ContentPackageExportPartV1CopyWith<$Res>  {
  factory $ContentPackageExportPartV1CopyWith(ContentPackageExportPartV1 value, $Res Function(ContentPackageExportPartV1) _then) = _$ContentPackageExportPartV1CopyWithImpl;
@useResult
$Res call({
 String partKey, int position, String modalityType, String contentPartType, String mediaType, String? text, String? rawPath, String? uri, String? providerId, String digestAlgorithm, String? digest, int? sizeBytes, Map<String, dynamic> awareContentMapping, Map<String, dynamic> provenance
});




}
/// @nodoc
class _$ContentPackageExportPartV1CopyWithImpl<$Res>
    implements $ContentPackageExportPartV1CopyWith<$Res> {
  _$ContentPackageExportPartV1CopyWithImpl(this._self, this._then);

  final ContentPackageExportPartV1 _self;
  final $Res Function(ContentPackageExportPartV1) _then;

/// Create a copy of ContentPackageExportPartV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? partKey = null,Object? position = null,Object? modalityType = null,Object? contentPartType = null,Object? mediaType = null,Object? text = freezed,Object? rawPath = freezed,Object? uri = freezed,Object? providerId = freezed,Object? digestAlgorithm = null,Object? digest = freezed,Object? sizeBytes = freezed,Object? awareContentMapping = null,Object? provenance = null,}) {
  return _then(_self.copyWith(
partKey: null == partKey ? _self.partKey : partKey // ignore: cast_nullable_to_non_nullable
as String,position: null == position ? _self.position : position // ignore: cast_nullable_to_non_nullable
as int,modalityType: null == modalityType ? _self.modalityType : modalityType // ignore: cast_nullable_to_non_nullable
as String,contentPartType: null == contentPartType ? _self.contentPartType : contentPartType // ignore: cast_nullable_to_non_nullable
as String,mediaType: null == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String,text: freezed == text ? _self.text : text // ignore: cast_nullable_to_non_nullable
as String?,rawPath: freezed == rawPath ? _self.rawPath : rawPath // ignore: cast_nullable_to_non_nullable
as String?,uri: freezed == uri ? _self.uri : uri // ignore: cast_nullable_to_non_nullable
as String?,providerId: freezed == providerId ? _self.providerId : providerId // ignore: cast_nullable_to_non_nullable
as String?,digestAlgorithm: null == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,awareContentMapping: null == awareContentMapping ? _self.awareContentMapping : awareContentMapping // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,provenance: null == provenance ? _self.provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [ContentPackageExportPartV1].
extension ContentPackageExportPartV1Patterns on ContentPackageExportPartV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ContentPackageExportPartV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ContentPackageExportPartV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ContentPackageExportPartV1 value)  def,}){
final _that = this;
switch (_that) {
case _ContentPackageExportPartV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ContentPackageExportPartV1 value)?  def,}){
final _that = this;
switch (_that) {
case _ContentPackageExportPartV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String partKey,  int position,  String modalityType,  String contentPartType,  String mediaType,  String? text,  String? rawPath,  String? uri,  String? providerId,  String digestAlgorithm,  String? digest,  int? sizeBytes,  Map<String, dynamic> awareContentMapping,  Map<String, dynamic> provenance)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ContentPackageExportPartV1() when def != null:
return def(_that.partKey,_that.position,_that.modalityType,_that.contentPartType,_that.mediaType,_that.text,_that.rawPath,_that.uri,_that.providerId,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.awareContentMapping,_that.provenance);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String partKey,  int position,  String modalityType,  String contentPartType,  String mediaType,  String? text,  String? rawPath,  String? uri,  String? providerId,  String digestAlgorithm,  String? digest,  int? sizeBytes,  Map<String, dynamic> awareContentMapping,  Map<String, dynamic> provenance)  def,}) {final _that = this;
switch (_that) {
case _ContentPackageExportPartV1():
return def(_that.partKey,_that.position,_that.modalityType,_that.contentPartType,_that.mediaType,_that.text,_that.rawPath,_that.uri,_that.providerId,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.awareContentMapping,_that.provenance);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String partKey,  int position,  String modalityType,  String contentPartType,  String mediaType,  String? text,  String? rawPath,  String? uri,  String? providerId,  String digestAlgorithm,  String? digest,  int? sizeBytes,  Map<String, dynamic> awareContentMapping,  Map<String, dynamic> provenance)?  def,}) {final _that = this;
switch (_that) {
case _ContentPackageExportPartV1() when def != null:
return def(_that.partKey,_that.position,_that.modalityType,_that.contentPartType,_that.mediaType,_that.text,_that.rawPath,_that.uri,_that.providerId,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.awareContentMapping,_that.provenance);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ContentPackageExportPartV1 implements ContentPackageExportPartV1 {
   _ContentPackageExportPartV1({required this.partKey, required this.position, required this.modalityType, required this.contentPartType, required this.mediaType, this.text, this.rawPath, this.uri, this.providerId, required this.digestAlgorithm, this.digest, this.sizeBytes, required final  Map<String, dynamic> awareContentMapping, required final  Map<String, dynamic> provenance}): _awareContentMapping = awareContentMapping,_provenance = provenance;
  factory _ContentPackageExportPartV1.fromJson(Map<String, dynamic> json) => _$ContentPackageExportPartV1FromJson(json);

@override final  String partKey;
@override final  int position;
@override final  String modalityType;
@override final  String contentPartType;
@override final  String mediaType;
@override final  String? text;
@override final  String? rawPath;
@override final  String? uri;
@override final  String? providerId;
@override final  String digestAlgorithm;
@override final  String? digest;
@override final  int? sizeBytes;
 final  Map<String, dynamic> _awareContentMapping;
@override Map<String, dynamic> get awareContentMapping {
  if (_awareContentMapping is EqualUnmodifiableMapView) return _awareContentMapping;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_awareContentMapping);
}

 final  Map<String, dynamic> _provenance;
@override Map<String, dynamic> get provenance {
  if (_provenance is EqualUnmodifiableMapView) return _provenance;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_provenance);
}


/// Create a copy of ContentPackageExportPartV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ContentPackageExportPartV1CopyWith<_ContentPackageExportPartV1> get copyWith => __$ContentPackageExportPartV1CopyWithImpl<_ContentPackageExportPartV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ContentPackageExportPartV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ContentPackageExportPartV1&&(identical(other.partKey, partKey) || other.partKey == partKey)&&(identical(other.position, position) || other.position == position)&&(identical(other.modalityType, modalityType) || other.modalityType == modalityType)&&(identical(other.contentPartType, contentPartType) || other.contentPartType == contentPartType)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.text, text) || other.text == text)&&(identical(other.rawPath, rawPath) || other.rawPath == rawPath)&&(identical(other.uri, uri) || other.uri == uri)&&(identical(other.providerId, providerId) || other.providerId == providerId)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&const DeepCollectionEquality().equals(other._awareContentMapping, _awareContentMapping)&&const DeepCollectionEquality().equals(other._provenance, _provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,partKey,position,modalityType,contentPartType,mediaType,text,rawPath,uri,providerId,digestAlgorithm,digest,sizeBytes,const DeepCollectionEquality().hash(_awareContentMapping),const DeepCollectionEquality().hash(_provenance));

@override
String toString() {
  return 'ContentPackageExportPartV1.def(partKey: $partKey, position: $position, modalityType: $modalityType, contentPartType: $contentPartType, mediaType: $mediaType, text: $text, rawPath: $rawPath, uri: $uri, providerId: $providerId, digestAlgorithm: $digestAlgorithm, digest: $digest, sizeBytes: $sizeBytes, awareContentMapping: $awareContentMapping, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class _$ContentPackageExportPartV1CopyWith<$Res> implements $ContentPackageExportPartV1CopyWith<$Res> {
  factory _$ContentPackageExportPartV1CopyWith(_ContentPackageExportPartV1 value, $Res Function(_ContentPackageExportPartV1) _then) = __$ContentPackageExportPartV1CopyWithImpl;
@override @useResult
$Res call({
 String partKey, int position, String modalityType, String contentPartType, String mediaType, String? text, String? rawPath, String? uri, String? providerId, String digestAlgorithm, String? digest, int? sizeBytes, Map<String, dynamic> awareContentMapping, Map<String, dynamic> provenance
});




}
/// @nodoc
class __$ContentPackageExportPartV1CopyWithImpl<$Res>
    implements _$ContentPackageExportPartV1CopyWith<$Res> {
  __$ContentPackageExportPartV1CopyWithImpl(this._self, this._then);

  final _ContentPackageExportPartV1 _self;
  final $Res Function(_ContentPackageExportPartV1) _then;

/// Create a copy of ContentPackageExportPartV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? partKey = null,Object? position = null,Object? modalityType = null,Object? contentPartType = null,Object? mediaType = null,Object? text = freezed,Object? rawPath = freezed,Object? uri = freezed,Object? providerId = freezed,Object? digestAlgorithm = null,Object? digest = freezed,Object? sizeBytes = freezed,Object? awareContentMapping = null,Object? provenance = null,}) {
  return _then(_ContentPackageExportPartV1(
partKey: null == partKey ? _self.partKey : partKey // ignore: cast_nullable_to_non_nullable
as String,position: null == position ? _self.position : position // ignore: cast_nullable_to_non_nullable
as int,modalityType: null == modalityType ? _self.modalityType : modalityType // ignore: cast_nullable_to_non_nullable
as String,contentPartType: null == contentPartType ? _self.contentPartType : contentPartType // ignore: cast_nullable_to_non_nullable
as String,mediaType: null == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String,text: freezed == text ? _self.text : text // ignore: cast_nullable_to_non_nullable
as String?,rawPath: freezed == rawPath ? _self.rawPath : rawPath // ignore: cast_nullable_to_non_nullable
as String?,uri: freezed == uri ? _self.uri : uri // ignore: cast_nullable_to_non_nullable
as String?,providerId: freezed == providerId ? _self.providerId : providerId // ignore: cast_nullable_to_non_nullable
as String?,digestAlgorithm: null == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,awareContentMapping: null == awareContentMapping ? _self._awareContentMapping : awareContentMapping // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,provenance: null == provenance ? _self._provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$ContentPackageArtifactProjectionV1 {

 String get outputKey; String get artifactKey; String get artifactFamily; String get artifactRole; List<String> get requiredFor; String get producerProviderKey; String get producerKey; String get producerKind; int? get materializationIndex; String get relativePath; String? get uri; String get mediaType; String get digestAlgorithm; String? get digest; int? get sizeBytes; String get runtimeContractVersion; Map<String, dynamic> get providerPayload; Map<String, dynamic> get receiptPayload;
/// Create a copy of ContentPackageArtifactProjectionV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ContentPackageArtifactProjectionV1CopyWith<ContentPackageArtifactProjectionV1> get copyWith => _$ContentPackageArtifactProjectionV1CopyWithImpl<ContentPackageArtifactProjectionV1>(this as ContentPackageArtifactProjectionV1, _$identity);

  /// Serializes this ContentPackageArtifactProjectionV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ContentPackageArtifactProjectionV1&&(identical(other.outputKey, outputKey) || other.outputKey == outputKey)&&(identical(other.artifactKey, artifactKey) || other.artifactKey == artifactKey)&&(identical(other.artifactFamily, artifactFamily) || other.artifactFamily == artifactFamily)&&(identical(other.artifactRole, artifactRole) || other.artifactRole == artifactRole)&&const DeepCollectionEquality().equals(other.requiredFor, requiredFor)&&(identical(other.producerProviderKey, producerProviderKey) || other.producerProviderKey == producerProviderKey)&&(identical(other.producerKey, producerKey) || other.producerKey == producerKey)&&(identical(other.producerKind, producerKind) || other.producerKind == producerKind)&&(identical(other.materializationIndex, materializationIndex) || other.materializationIndex == materializationIndex)&&(identical(other.relativePath, relativePath) || other.relativePath == relativePath)&&(identical(other.uri, uri) || other.uri == uri)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.runtimeContractVersion, runtimeContractVersion) || other.runtimeContractVersion == runtimeContractVersion)&&const DeepCollectionEquality().equals(other.providerPayload, providerPayload)&&const DeepCollectionEquality().equals(other.receiptPayload, receiptPayload));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,outputKey,artifactKey,artifactFamily,artifactRole,const DeepCollectionEquality().hash(requiredFor),producerProviderKey,producerKey,producerKind,materializationIndex,relativePath,uri,mediaType,digestAlgorithm,digest,sizeBytes,runtimeContractVersion,const DeepCollectionEquality().hash(providerPayload),const DeepCollectionEquality().hash(receiptPayload));

@override
String toString() {
  return 'ContentPackageArtifactProjectionV1(outputKey: $outputKey, artifactKey: $artifactKey, artifactFamily: $artifactFamily, artifactRole: $artifactRole, requiredFor: $requiredFor, producerProviderKey: $producerProviderKey, producerKey: $producerKey, producerKind: $producerKind, materializationIndex: $materializationIndex, relativePath: $relativePath, uri: $uri, mediaType: $mediaType, digestAlgorithm: $digestAlgorithm, digest: $digest, sizeBytes: $sizeBytes, runtimeContractVersion: $runtimeContractVersion, providerPayload: $providerPayload, receiptPayload: $receiptPayload)';
}


}

/// @nodoc
abstract mixin class $ContentPackageArtifactProjectionV1CopyWith<$Res>  {
  factory $ContentPackageArtifactProjectionV1CopyWith(ContentPackageArtifactProjectionV1 value, $Res Function(ContentPackageArtifactProjectionV1) _then) = _$ContentPackageArtifactProjectionV1CopyWithImpl;
@useResult
$Res call({
 String outputKey, String artifactKey, String artifactFamily, String artifactRole, List<String> requiredFor, String producerProviderKey, String producerKey, String producerKind, int? materializationIndex, String relativePath, String? uri, String mediaType, String digestAlgorithm, String? digest, int? sizeBytes, String runtimeContractVersion, Map<String, dynamic> providerPayload, Map<String, dynamic> receiptPayload
});




}
/// @nodoc
class _$ContentPackageArtifactProjectionV1CopyWithImpl<$Res>
    implements $ContentPackageArtifactProjectionV1CopyWith<$Res> {
  _$ContentPackageArtifactProjectionV1CopyWithImpl(this._self, this._then);

  final ContentPackageArtifactProjectionV1 _self;
  final $Res Function(ContentPackageArtifactProjectionV1) _then;

/// Create a copy of ContentPackageArtifactProjectionV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? outputKey = null,Object? artifactKey = null,Object? artifactFamily = null,Object? artifactRole = null,Object? requiredFor = null,Object? producerProviderKey = null,Object? producerKey = null,Object? producerKind = null,Object? materializationIndex = freezed,Object? relativePath = null,Object? uri = freezed,Object? mediaType = null,Object? digestAlgorithm = null,Object? digest = freezed,Object? sizeBytes = freezed,Object? runtimeContractVersion = null,Object? providerPayload = null,Object? receiptPayload = null,}) {
  return _then(_self.copyWith(
outputKey: null == outputKey ? _self.outputKey : outputKey // ignore: cast_nullable_to_non_nullable
as String,artifactKey: null == artifactKey ? _self.artifactKey : artifactKey // ignore: cast_nullable_to_non_nullable
as String,artifactFamily: null == artifactFamily ? _self.artifactFamily : artifactFamily // ignore: cast_nullable_to_non_nullable
as String,artifactRole: null == artifactRole ? _self.artifactRole : artifactRole // ignore: cast_nullable_to_non_nullable
as String,requiredFor: null == requiredFor ? _self.requiredFor : requiredFor // ignore: cast_nullable_to_non_nullable
as List<String>,producerProviderKey: null == producerProviderKey ? _self.producerProviderKey : producerProviderKey // ignore: cast_nullable_to_non_nullable
as String,producerKey: null == producerKey ? _self.producerKey : producerKey // ignore: cast_nullable_to_non_nullable
as String,producerKind: null == producerKind ? _self.producerKind : producerKind // ignore: cast_nullable_to_non_nullable
as String,materializationIndex: freezed == materializationIndex ? _self.materializationIndex : materializationIndex // ignore: cast_nullable_to_non_nullable
as int?,relativePath: null == relativePath ? _self.relativePath : relativePath // ignore: cast_nullable_to_non_nullable
as String,uri: freezed == uri ? _self.uri : uri // ignore: cast_nullable_to_non_nullable
as String?,mediaType: null == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String,digestAlgorithm: null == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,runtimeContractVersion: null == runtimeContractVersion ? _self.runtimeContractVersion : runtimeContractVersion // ignore: cast_nullable_to_non_nullable
as String,providerPayload: null == providerPayload ? _self.providerPayload : providerPayload // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,receiptPayload: null == receiptPayload ? _self.receiptPayload : receiptPayload // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [ContentPackageArtifactProjectionV1].
extension ContentPackageArtifactProjectionV1Patterns on ContentPackageArtifactProjectionV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ContentPackageArtifactProjectionV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ContentPackageArtifactProjectionV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ContentPackageArtifactProjectionV1 value)  def,}){
final _that = this;
switch (_that) {
case _ContentPackageArtifactProjectionV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ContentPackageArtifactProjectionV1 value)?  def,}){
final _that = this;
switch (_that) {
case _ContentPackageArtifactProjectionV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String outputKey,  String artifactKey,  String artifactFamily,  String artifactRole,  List<String> requiredFor,  String producerProviderKey,  String producerKey,  String producerKind,  int? materializationIndex,  String relativePath,  String? uri,  String mediaType,  String digestAlgorithm,  String? digest,  int? sizeBytes,  String runtimeContractVersion,  Map<String, dynamic> providerPayload,  Map<String, dynamic> receiptPayload)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ContentPackageArtifactProjectionV1() when def != null:
return def(_that.outputKey,_that.artifactKey,_that.artifactFamily,_that.artifactRole,_that.requiredFor,_that.producerProviderKey,_that.producerKey,_that.producerKind,_that.materializationIndex,_that.relativePath,_that.uri,_that.mediaType,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.runtimeContractVersion,_that.providerPayload,_that.receiptPayload);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String outputKey,  String artifactKey,  String artifactFamily,  String artifactRole,  List<String> requiredFor,  String producerProviderKey,  String producerKey,  String producerKind,  int? materializationIndex,  String relativePath,  String? uri,  String mediaType,  String digestAlgorithm,  String? digest,  int? sizeBytes,  String runtimeContractVersion,  Map<String, dynamic> providerPayload,  Map<String, dynamic> receiptPayload)  def,}) {final _that = this;
switch (_that) {
case _ContentPackageArtifactProjectionV1():
return def(_that.outputKey,_that.artifactKey,_that.artifactFamily,_that.artifactRole,_that.requiredFor,_that.producerProviderKey,_that.producerKey,_that.producerKind,_that.materializationIndex,_that.relativePath,_that.uri,_that.mediaType,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.runtimeContractVersion,_that.providerPayload,_that.receiptPayload);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String outputKey,  String artifactKey,  String artifactFamily,  String artifactRole,  List<String> requiredFor,  String producerProviderKey,  String producerKey,  String producerKind,  int? materializationIndex,  String relativePath,  String? uri,  String mediaType,  String digestAlgorithm,  String? digest,  int? sizeBytes,  String runtimeContractVersion,  Map<String, dynamic> providerPayload,  Map<String, dynamic> receiptPayload)?  def,}) {final _that = this;
switch (_that) {
case _ContentPackageArtifactProjectionV1() when def != null:
return def(_that.outputKey,_that.artifactKey,_that.artifactFamily,_that.artifactRole,_that.requiredFor,_that.producerProviderKey,_that.producerKey,_that.producerKind,_that.materializationIndex,_that.relativePath,_that.uri,_that.mediaType,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.runtimeContractVersion,_that.providerPayload,_that.receiptPayload);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ContentPackageArtifactProjectionV1 implements ContentPackageArtifactProjectionV1 {
   _ContentPackageArtifactProjectionV1({required this.outputKey, required this.artifactKey, required this.artifactFamily, required this.artifactRole, final  List<String> requiredFor = const [], required this.producerProviderKey, required this.producerKey, required this.producerKind, this.materializationIndex, required this.relativePath, this.uri, required this.mediaType, required this.digestAlgorithm, this.digest, this.sizeBytes, required this.runtimeContractVersion, required final  Map<String, dynamic> providerPayload, required final  Map<String, dynamic> receiptPayload}): _requiredFor = requiredFor,_providerPayload = providerPayload,_receiptPayload = receiptPayload;
  factory _ContentPackageArtifactProjectionV1.fromJson(Map<String, dynamic> json) => _$ContentPackageArtifactProjectionV1FromJson(json);

@override final  String outputKey;
@override final  String artifactKey;
@override final  String artifactFamily;
@override final  String artifactRole;
 final  List<String> _requiredFor;
@override@JsonKey() List<String> get requiredFor {
  if (_requiredFor is EqualUnmodifiableListView) return _requiredFor;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_requiredFor);
}

@override final  String producerProviderKey;
@override final  String producerKey;
@override final  String producerKind;
@override final  int? materializationIndex;
@override final  String relativePath;
@override final  String? uri;
@override final  String mediaType;
@override final  String digestAlgorithm;
@override final  String? digest;
@override final  int? sizeBytes;
@override final  String runtimeContractVersion;
 final  Map<String, dynamic> _providerPayload;
@override Map<String, dynamic> get providerPayload {
  if (_providerPayload is EqualUnmodifiableMapView) return _providerPayload;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_providerPayload);
}

 final  Map<String, dynamic> _receiptPayload;
@override Map<String, dynamic> get receiptPayload {
  if (_receiptPayload is EqualUnmodifiableMapView) return _receiptPayload;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_receiptPayload);
}


/// Create a copy of ContentPackageArtifactProjectionV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ContentPackageArtifactProjectionV1CopyWith<_ContentPackageArtifactProjectionV1> get copyWith => __$ContentPackageArtifactProjectionV1CopyWithImpl<_ContentPackageArtifactProjectionV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ContentPackageArtifactProjectionV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ContentPackageArtifactProjectionV1&&(identical(other.outputKey, outputKey) || other.outputKey == outputKey)&&(identical(other.artifactKey, artifactKey) || other.artifactKey == artifactKey)&&(identical(other.artifactFamily, artifactFamily) || other.artifactFamily == artifactFamily)&&(identical(other.artifactRole, artifactRole) || other.artifactRole == artifactRole)&&const DeepCollectionEquality().equals(other._requiredFor, _requiredFor)&&(identical(other.producerProviderKey, producerProviderKey) || other.producerProviderKey == producerProviderKey)&&(identical(other.producerKey, producerKey) || other.producerKey == producerKey)&&(identical(other.producerKind, producerKind) || other.producerKind == producerKind)&&(identical(other.materializationIndex, materializationIndex) || other.materializationIndex == materializationIndex)&&(identical(other.relativePath, relativePath) || other.relativePath == relativePath)&&(identical(other.uri, uri) || other.uri == uri)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.runtimeContractVersion, runtimeContractVersion) || other.runtimeContractVersion == runtimeContractVersion)&&const DeepCollectionEquality().equals(other._providerPayload, _providerPayload)&&const DeepCollectionEquality().equals(other._receiptPayload, _receiptPayload));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,outputKey,artifactKey,artifactFamily,artifactRole,const DeepCollectionEquality().hash(_requiredFor),producerProviderKey,producerKey,producerKind,materializationIndex,relativePath,uri,mediaType,digestAlgorithm,digest,sizeBytes,runtimeContractVersion,const DeepCollectionEquality().hash(_providerPayload),const DeepCollectionEquality().hash(_receiptPayload));

@override
String toString() {
  return 'ContentPackageArtifactProjectionV1.def(outputKey: $outputKey, artifactKey: $artifactKey, artifactFamily: $artifactFamily, artifactRole: $artifactRole, requiredFor: $requiredFor, producerProviderKey: $producerProviderKey, producerKey: $producerKey, producerKind: $producerKind, materializationIndex: $materializationIndex, relativePath: $relativePath, uri: $uri, mediaType: $mediaType, digestAlgorithm: $digestAlgorithm, digest: $digest, sizeBytes: $sizeBytes, runtimeContractVersion: $runtimeContractVersion, providerPayload: $providerPayload, receiptPayload: $receiptPayload)';
}


}

/// @nodoc
abstract mixin class _$ContentPackageArtifactProjectionV1CopyWith<$Res> implements $ContentPackageArtifactProjectionV1CopyWith<$Res> {
  factory _$ContentPackageArtifactProjectionV1CopyWith(_ContentPackageArtifactProjectionV1 value, $Res Function(_ContentPackageArtifactProjectionV1) _then) = __$ContentPackageArtifactProjectionV1CopyWithImpl;
@override @useResult
$Res call({
 String outputKey, String artifactKey, String artifactFamily, String artifactRole, List<String> requiredFor, String producerProviderKey, String producerKey, String producerKind, int? materializationIndex, String relativePath, String? uri, String mediaType, String digestAlgorithm, String? digest, int? sizeBytes, String runtimeContractVersion, Map<String, dynamic> providerPayload, Map<String, dynamic> receiptPayload
});




}
/// @nodoc
class __$ContentPackageArtifactProjectionV1CopyWithImpl<$Res>
    implements _$ContentPackageArtifactProjectionV1CopyWith<$Res> {
  __$ContentPackageArtifactProjectionV1CopyWithImpl(this._self, this._then);

  final _ContentPackageArtifactProjectionV1 _self;
  final $Res Function(_ContentPackageArtifactProjectionV1) _then;

/// Create a copy of ContentPackageArtifactProjectionV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? outputKey = null,Object? artifactKey = null,Object? artifactFamily = null,Object? artifactRole = null,Object? requiredFor = null,Object? producerProviderKey = null,Object? producerKey = null,Object? producerKind = null,Object? materializationIndex = freezed,Object? relativePath = null,Object? uri = freezed,Object? mediaType = null,Object? digestAlgorithm = null,Object? digest = freezed,Object? sizeBytes = freezed,Object? runtimeContractVersion = null,Object? providerPayload = null,Object? receiptPayload = null,}) {
  return _then(_ContentPackageArtifactProjectionV1(
outputKey: null == outputKey ? _self.outputKey : outputKey // ignore: cast_nullable_to_non_nullable
as String,artifactKey: null == artifactKey ? _self.artifactKey : artifactKey // ignore: cast_nullable_to_non_nullable
as String,artifactFamily: null == artifactFamily ? _self.artifactFamily : artifactFamily // ignore: cast_nullable_to_non_nullable
as String,artifactRole: null == artifactRole ? _self.artifactRole : artifactRole // ignore: cast_nullable_to_non_nullable
as String,requiredFor: null == requiredFor ? _self._requiredFor : requiredFor // ignore: cast_nullable_to_non_nullable
as List<String>,producerProviderKey: null == producerProviderKey ? _self.producerProviderKey : producerProviderKey // ignore: cast_nullable_to_non_nullable
as String,producerKey: null == producerKey ? _self.producerKey : producerKey // ignore: cast_nullable_to_non_nullable
as String,producerKind: null == producerKind ? _self.producerKind : producerKind // ignore: cast_nullable_to_non_nullable
as String,materializationIndex: freezed == materializationIndex ? _self.materializationIndex : materializationIndex // ignore: cast_nullable_to_non_nullable
as int?,relativePath: null == relativePath ? _self.relativePath : relativePath // ignore: cast_nullable_to_non_nullable
as String,uri: freezed == uri ? _self.uri : uri // ignore: cast_nullable_to_non_nullable
as String?,mediaType: null == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String,digestAlgorithm: null == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,runtimeContractVersion: null == runtimeContractVersion ? _self.runtimeContractVersion : runtimeContractVersion // ignore: cast_nullable_to_non_nullable
as String,providerPayload: null == providerPayload ? _self._providerPayload : providerPayload // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,receiptPayload: null == receiptPayload ? _self._receiptPayload : receiptPayload // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$ContentPackageExportDocumentV1 {

 String get exportKind; String get contractVersion; String get packageName; String? get packageRoot; String? get manifestRelativePath; String? get title; String get packageKind; String get sourceProviderKey; String get sourceRef; String get runtimeContractVersion; String? get contentKey; String? get contentTitle; String get targetPath; String get mediaType; String get digestAlgorithm; String? get digest; int? get sizeBytes; String? get contentText; List<ContentPackageExportPartV1> get parts; ContentPackageArtifactProjectionV1? get artifact; Map<String, dynamic> get awareContentMapping; Map<String, dynamic> get providerPayload; Map<String, dynamic> get provenance;
/// Create a copy of ContentPackageExportDocumentV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ContentPackageExportDocumentV1CopyWith<ContentPackageExportDocumentV1> get copyWith => _$ContentPackageExportDocumentV1CopyWithImpl<ContentPackageExportDocumentV1>(this as ContentPackageExportDocumentV1, _$identity);

  /// Serializes this ContentPackageExportDocumentV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ContentPackageExportDocumentV1&&(identical(other.exportKind, exportKind) || other.exportKind == exportKind)&&(identical(other.contractVersion, contractVersion) || other.contractVersion == contractVersion)&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.packageRoot, packageRoot) || other.packageRoot == packageRoot)&&(identical(other.manifestRelativePath, manifestRelativePath) || other.manifestRelativePath == manifestRelativePath)&&(identical(other.title, title) || other.title == title)&&(identical(other.packageKind, packageKind) || other.packageKind == packageKind)&&(identical(other.sourceProviderKey, sourceProviderKey) || other.sourceProviderKey == sourceProviderKey)&&(identical(other.sourceRef, sourceRef) || other.sourceRef == sourceRef)&&(identical(other.runtimeContractVersion, runtimeContractVersion) || other.runtimeContractVersion == runtimeContractVersion)&&(identical(other.contentKey, contentKey) || other.contentKey == contentKey)&&(identical(other.contentTitle, contentTitle) || other.contentTitle == contentTitle)&&(identical(other.targetPath, targetPath) || other.targetPath == targetPath)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.contentText, contentText) || other.contentText == contentText)&&const DeepCollectionEquality().equals(other.parts, parts)&&(identical(other.artifact, artifact) || other.artifact == artifact)&&const DeepCollectionEquality().equals(other.awareContentMapping, awareContentMapping)&&const DeepCollectionEquality().equals(other.providerPayload, providerPayload)&&const DeepCollectionEquality().equals(other.provenance, provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,exportKind,contractVersion,packageName,packageRoot,manifestRelativePath,title,packageKind,sourceProviderKey,sourceRef,runtimeContractVersion,contentKey,contentTitle,targetPath,mediaType,digestAlgorithm,digest,sizeBytes,contentText,const DeepCollectionEquality().hash(parts),artifact,const DeepCollectionEquality().hash(awareContentMapping),const DeepCollectionEquality().hash(providerPayload),const DeepCollectionEquality().hash(provenance)]);

@override
String toString() {
  return 'ContentPackageExportDocumentV1(exportKind: $exportKind, contractVersion: $contractVersion, packageName: $packageName, packageRoot: $packageRoot, manifestRelativePath: $manifestRelativePath, title: $title, packageKind: $packageKind, sourceProviderKey: $sourceProviderKey, sourceRef: $sourceRef, runtimeContractVersion: $runtimeContractVersion, contentKey: $contentKey, contentTitle: $contentTitle, targetPath: $targetPath, mediaType: $mediaType, digestAlgorithm: $digestAlgorithm, digest: $digest, sizeBytes: $sizeBytes, contentText: $contentText, parts: $parts, artifact: $artifact, awareContentMapping: $awareContentMapping, providerPayload: $providerPayload, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class $ContentPackageExportDocumentV1CopyWith<$Res>  {
  factory $ContentPackageExportDocumentV1CopyWith(ContentPackageExportDocumentV1 value, $Res Function(ContentPackageExportDocumentV1) _then) = _$ContentPackageExportDocumentV1CopyWithImpl;
@useResult
$Res call({
 String exportKind, String contractVersion, String packageName, String? packageRoot, String? manifestRelativePath, String? title, String packageKind, String sourceProviderKey, String sourceRef, String runtimeContractVersion, String? contentKey, String? contentTitle, String targetPath, String mediaType, String digestAlgorithm, String? digest, int? sizeBytes, String? contentText, List<ContentPackageExportPartV1> parts, ContentPackageArtifactProjectionV1? artifact, Map<String, dynamic> awareContentMapping, Map<String, dynamic> providerPayload, Map<String, dynamic> provenance
});


$ContentPackageArtifactProjectionV1CopyWith<$Res>? get artifact;

}
/// @nodoc
class _$ContentPackageExportDocumentV1CopyWithImpl<$Res>
    implements $ContentPackageExportDocumentV1CopyWith<$Res> {
  _$ContentPackageExportDocumentV1CopyWithImpl(this._self, this._then);

  final ContentPackageExportDocumentV1 _self;
  final $Res Function(ContentPackageExportDocumentV1) _then;

/// Create a copy of ContentPackageExportDocumentV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? exportKind = null,Object? contractVersion = null,Object? packageName = null,Object? packageRoot = freezed,Object? manifestRelativePath = freezed,Object? title = freezed,Object? packageKind = null,Object? sourceProviderKey = null,Object? sourceRef = null,Object? runtimeContractVersion = null,Object? contentKey = freezed,Object? contentTitle = freezed,Object? targetPath = null,Object? mediaType = null,Object? digestAlgorithm = null,Object? digest = freezed,Object? sizeBytes = freezed,Object? contentText = freezed,Object? parts = null,Object? artifact = freezed,Object? awareContentMapping = null,Object? providerPayload = null,Object? provenance = null,}) {
  return _then(_self.copyWith(
exportKind: null == exportKind ? _self.exportKind : exportKind // ignore: cast_nullable_to_non_nullable
as String,contractVersion: null == contractVersion ? _self.contractVersion : contractVersion // ignore: cast_nullable_to_non_nullable
as String,packageName: null == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String,packageRoot: freezed == packageRoot ? _self.packageRoot : packageRoot // ignore: cast_nullable_to_non_nullable
as String?,manifestRelativePath: freezed == manifestRelativePath ? _self.manifestRelativePath : manifestRelativePath // ignore: cast_nullable_to_non_nullable
as String?,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,packageKind: null == packageKind ? _self.packageKind : packageKind // ignore: cast_nullable_to_non_nullable
as String,sourceProviderKey: null == sourceProviderKey ? _self.sourceProviderKey : sourceProviderKey // ignore: cast_nullable_to_non_nullable
as String,sourceRef: null == sourceRef ? _self.sourceRef : sourceRef // ignore: cast_nullable_to_non_nullable
as String,runtimeContractVersion: null == runtimeContractVersion ? _self.runtimeContractVersion : runtimeContractVersion // ignore: cast_nullable_to_non_nullable
as String,contentKey: freezed == contentKey ? _self.contentKey : contentKey // ignore: cast_nullable_to_non_nullable
as String?,contentTitle: freezed == contentTitle ? _self.contentTitle : contentTitle // ignore: cast_nullable_to_non_nullable
as String?,targetPath: null == targetPath ? _self.targetPath : targetPath // ignore: cast_nullable_to_non_nullable
as String,mediaType: null == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String,digestAlgorithm: null == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,contentText: freezed == contentText ? _self.contentText : contentText // ignore: cast_nullable_to_non_nullable
as String?,parts: null == parts ? _self.parts : parts // ignore: cast_nullable_to_non_nullable
as List<ContentPackageExportPartV1>,artifact: freezed == artifact ? _self.artifact : artifact // ignore: cast_nullable_to_non_nullable
as ContentPackageArtifactProjectionV1?,awareContentMapping: null == awareContentMapping ? _self.awareContentMapping : awareContentMapping // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,providerPayload: null == providerPayload ? _self.providerPayload : providerPayload // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,provenance: null == provenance ? _self.provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}
/// Create a copy of ContentPackageExportDocumentV1
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ContentPackageArtifactProjectionV1CopyWith<$Res>? get artifact {
    if (_self.artifact == null) {
    return null;
  }

  return $ContentPackageArtifactProjectionV1CopyWith<$Res>(_self.artifact!, (value) {
    return _then(_self.copyWith(artifact: value));
  });
}
}


/// Adds pattern-matching-related methods to [ContentPackageExportDocumentV1].
extension ContentPackageExportDocumentV1Patterns on ContentPackageExportDocumentV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ContentPackageExportDocumentV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ContentPackageExportDocumentV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ContentPackageExportDocumentV1 value)  def,}){
final _that = this;
switch (_that) {
case _ContentPackageExportDocumentV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ContentPackageExportDocumentV1 value)?  def,}){
final _that = this;
switch (_that) {
case _ContentPackageExportDocumentV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String exportKind,  String contractVersion,  String packageName,  String? packageRoot,  String? manifestRelativePath,  String? title,  String packageKind,  String sourceProviderKey,  String sourceRef,  String runtimeContractVersion,  String? contentKey,  String? contentTitle,  String targetPath,  String mediaType,  String digestAlgorithm,  String? digest,  int? sizeBytes,  String? contentText,  List<ContentPackageExportPartV1> parts,  ContentPackageArtifactProjectionV1? artifact,  Map<String, dynamic> awareContentMapping,  Map<String, dynamic> providerPayload,  Map<String, dynamic> provenance)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ContentPackageExportDocumentV1() when def != null:
return def(_that.exportKind,_that.contractVersion,_that.packageName,_that.packageRoot,_that.manifestRelativePath,_that.title,_that.packageKind,_that.sourceProviderKey,_that.sourceRef,_that.runtimeContractVersion,_that.contentKey,_that.contentTitle,_that.targetPath,_that.mediaType,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.contentText,_that.parts,_that.artifact,_that.awareContentMapping,_that.providerPayload,_that.provenance);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String exportKind,  String contractVersion,  String packageName,  String? packageRoot,  String? manifestRelativePath,  String? title,  String packageKind,  String sourceProviderKey,  String sourceRef,  String runtimeContractVersion,  String? contentKey,  String? contentTitle,  String targetPath,  String mediaType,  String digestAlgorithm,  String? digest,  int? sizeBytes,  String? contentText,  List<ContentPackageExportPartV1> parts,  ContentPackageArtifactProjectionV1? artifact,  Map<String, dynamic> awareContentMapping,  Map<String, dynamic> providerPayload,  Map<String, dynamic> provenance)  def,}) {final _that = this;
switch (_that) {
case _ContentPackageExportDocumentV1():
return def(_that.exportKind,_that.contractVersion,_that.packageName,_that.packageRoot,_that.manifestRelativePath,_that.title,_that.packageKind,_that.sourceProviderKey,_that.sourceRef,_that.runtimeContractVersion,_that.contentKey,_that.contentTitle,_that.targetPath,_that.mediaType,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.contentText,_that.parts,_that.artifact,_that.awareContentMapping,_that.providerPayload,_that.provenance);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String exportKind,  String contractVersion,  String packageName,  String? packageRoot,  String? manifestRelativePath,  String? title,  String packageKind,  String sourceProviderKey,  String sourceRef,  String runtimeContractVersion,  String? contentKey,  String? contentTitle,  String targetPath,  String mediaType,  String digestAlgorithm,  String? digest,  int? sizeBytes,  String? contentText,  List<ContentPackageExportPartV1> parts,  ContentPackageArtifactProjectionV1? artifact,  Map<String, dynamic> awareContentMapping,  Map<String, dynamic> providerPayload,  Map<String, dynamic> provenance)?  def,}) {final _that = this;
switch (_that) {
case _ContentPackageExportDocumentV1() when def != null:
return def(_that.exportKind,_that.contractVersion,_that.packageName,_that.packageRoot,_that.manifestRelativePath,_that.title,_that.packageKind,_that.sourceProviderKey,_that.sourceRef,_that.runtimeContractVersion,_that.contentKey,_that.contentTitle,_that.targetPath,_that.mediaType,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.contentText,_that.parts,_that.artifact,_that.awareContentMapping,_that.providerPayload,_that.provenance);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ContentPackageExportDocumentV1 implements ContentPackageExportDocumentV1 {
   _ContentPackageExportDocumentV1({required this.exportKind, required this.contractVersion, required this.packageName, this.packageRoot, this.manifestRelativePath, this.title, required this.packageKind, required this.sourceProviderKey, required this.sourceRef, required this.runtimeContractVersion, this.contentKey, this.contentTitle, required this.targetPath, required this.mediaType, required this.digestAlgorithm, this.digest, this.sizeBytes, this.contentText, final  List<ContentPackageExportPartV1> parts = const [], this.artifact, required final  Map<String, dynamic> awareContentMapping, required final  Map<String, dynamic> providerPayload, required final  Map<String, dynamic> provenance}): _parts = parts,_awareContentMapping = awareContentMapping,_providerPayload = providerPayload,_provenance = provenance;
  factory _ContentPackageExportDocumentV1.fromJson(Map<String, dynamic> json) => _$ContentPackageExportDocumentV1FromJson(json);

@override final  String exportKind;
@override final  String contractVersion;
@override final  String packageName;
@override final  String? packageRoot;
@override final  String? manifestRelativePath;
@override final  String? title;
@override final  String packageKind;
@override final  String sourceProviderKey;
@override final  String sourceRef;
@override final  String runtimeContractVersion;
@override final  String? contentKey;
@override final  String? contentTitle;
@override final  String targetPath;
@override final  String mediaType;
@override final  String digestAlgorithm;
@override final  String? digest;
@override final  int? sizeBytes;
@override final  String? contentText;
 final  List<ContentPackageExportPartV1> _parts;
@override@JsonKey() List<ContentPackageExportPartV1> get parts {
  if (_parts is EqualUnmodifiableListView) return _parts;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_parts);
}

@override final  ContentPackageArtifactProjectionV1? artifact;
 final  Map<String, dynamic> _awareContentMapping;
@override Map<String, dynamic> get awareContentMapping {
  if (_awareContentMapping is EqualUnmodifiableMapView) return _awareContentMapping;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_awareContentMapping);
}

 final  Map<String, dynamic> _providerPayload;
@override Map<String, dynamic> get providerPayload {
  if (_providerPayload is EqualUnmodifiableMapView) return _providerPayload;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_providerPayload);
}

 final  Map<String, dynamic> _provenance;
@override Map<String, dynamic> get provenance {
  if (_provenance is EqualUnmodifiableMapView) return _provenance;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_provenance);
}


/// Create a copy of ContentPackageExportDocumentV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ContentPackageExportDocumentV1CopyWith<_ContentPackageExportDocumentV1> get copyWith => __$ContentPackageExportDocumentV1CopyWithImpl<_ContentPackageExportDocumentV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ContentPackageExportDocumentV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ContentPackageExportDocumentV1&&(identical(other.exportKind, exportKind) || other.exportKind == exportKind)&&(identical(other.contractVersion, contractVersion) || other.contractVersion == contractVersion)&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.packageRoot, packageRoot) || other.packageRoot == packageRoot)&&(identical(other.manifestRelativePath, manifestRelativePath) || other.manifestRelativePath == manifestRelativePath)&&(identical(other.title, title) || other.title == title)&&(identical(other.packageKind, packageKind) || other.packageKind == packageKind)&&(identical(other.sourceProviderKey, sourceProviderKey) || other.sourceProviderKey == sourceProviderKey)&&(identical(other.sourceRef, sourceRef) || other.sourceRef == sourceRef)&&(identical(other.runtimeContractVersion, runtimeContractVersion) || other.runtimeContractVersion == runtimeContractVersion)&&(identical(other.contentKey, contentKey) || other.contentKey == contentKey)&&(identical(other.contentTitle, contentTitle) || other.contentTitle == contentTitle)&&(identical(other.targetPath, targetPath) || other.targetPath == targetPath)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.contentText, contentText) || other.contentText == contentText)&&const DeepCollectionEquality().equals(other._parts, _parts)&&(identical(other.artifact, artifact) || other.artifact == artifact)&&const DeepCollectionEquality().equals(other._awareContentMapping, _awareContentMapping)&&const DeepCollectionEquality().equals(other._providerPayload, _providerPayload)&&const DeepCollectionEquality().equals(other._provenance, _provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,exportKind,contractVersion,packageName,packageRoot,manifestRelativePath,title,packageKind,sourceProviderKey,sourceRef,runtimeContractVersion,contentKey,contentTitle,targetPath,mediaType,digestAlgorithm,digest,sizeBytes,contentText,const DeepCollectionEquality().hash(_parts),artifact,const DeepCollectionEquality().hash(_awareContentMapping),const DeepCollectionEquality().hash(_providerPayload),const DeepCollectionEquality().hash(_provenance)]);

@override
String toString() {
  return 'ContentPackageExportDocumentV1.def(exportKind: $exportKind, contractVersion: $contractVersion, packageName: $packageName, packageRoot: $packageRoot, manifestRelativePath: $manifestRelativePath, title: $title, packageKind: $packageKind, sourceProviderKey: $sourceProviderKey, sourceRef: $sourceRef, runtimeContractVersion: $runtimeContractVersion, contentKey: $contentKey, contentTitle: $contentTitle, targetPath: $targetPath, mediaType: $mediaType, digestAlgorithm: $digestAlgorithm, digest: $digest, sizeBytes: $sizeBytes, contentText: $contentText, parts: $parts, artifact: $artifact, awareContentMapping: $awareContentMapping, providerPayload: $providerPayload, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class _$ContentPackageExportDocumentV1CopyWith<$Res> implements $ContentPackageExportDocumentV1CopyWith<$Res> {
  factory _$ContentPackageExportDocumentV1CopyWith(_ContentPackageExportDocumentV1 value, $Res Function(_ContentPackageExportDocumentV1) _then) = __$ContentPackageExportDocumentV1CopyWithImpl;
@override @useResult
$Res call({
 String exportKind, String contractVersion, String packageName, String? packageRoot, String? manifestRelativePath, String? title, String packageKind, String sourceProviderKey, String sourceRef, String runtimeContractVersion, String? contentKey, String? contentTitle, String targetPath, String mediaType, String digestAlgorithm, String? digest, int? sizeBytes, String? contentText, List<ContentPackageExportPartV1> parts, ContentPackageArtifactProjectionV1? artifact, Map<String, dynamic> awareContentMapping, Map<String, dynamic> providerPayload, Map<String, dynamic> provenance
});


@override $ContentPackageArtifactProjectionV1CopyWith<$Res>? get artifact;

}
/// @nodoc
class __$ContentPackageExportDocumentV1CopyWithImpl<$Res>
    implements _$ContentPackageExportDocumentV1CopyWith<$Res> {
  __$ContentPackageExportDocumentV1CopyWithImpl(this._self, this._then);

  final _ContentPackageExportDocumentV1 _self;
  final $Res Function(_ContentPackageExportDocumentV1) _then;

/// Create a copy of ContentPackageExportDocumentV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? exportKind = null,Object? contractVersion = null,Object? packageName = null,Object? packageRoot = freezed,Object? manifestRelativePath = freezed,Object? title = freezed,Object? packageKind = null,Object? sourceProviderKey = null,Object? sourceRef = null,Object? runtimeContractVersion = null,Object? contentKey = freezed,Object? contentTitle = freezed,Object? targetPath = null,Object? mediaType = null,Object? digestAlgorithm = null,Object? digest = freezed,Object? sizeBytes = freezed,Object? contentText = freezed,Object? parts = null,Object? artifact = freezed,Object? awareContentMapping = null,Object? providerPayload = null,Object? provenance = null,}) {
  return _then(_ContentPackageExportDocumentV1(
exportKind: null == exportKind ? _self.exportKind : exportKind // ignore: cast_nullable_to_non_nullable
as String,contractVersion: null == contractVersion ? _self.contractVersion : contractVersion // ignore: cast_nullable_to_non_nullable
as String,packageName: null == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String,packageRoot: freezed == packageRoot ? _self.packageRoot : packageRoot // ignore: cast_nullable_to_non_nullable
as String?,manifestRelativePath: freezed == manifestRelativePath ? _self.manifestRelativePath : manifestRelativePath // ignore: cast_nullable_to_non_nullable
as String?,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,packageKind: null == packageKind ? _self.packageKind : packageKind // ignore: cast_nullable_to_non_nullable
as String,sourceProviderKey: null == sourceProviderKey ? _self.sourceProviderKey : sourceProviderKey // ignore: cast_nullable_to_non_nullable
as String,sourceRef: null == sourceRef ? _self.sourceRef : sourceRef // ignore: cast_nullable_to_non_nullable
as String,runtimeContractVersion: null == runtimeContractVersion ? _self.runtimeContractVersion : runtimeContractVersion // ignore: cast_nullable_to_non_nullable
as String,contentKey: freezed == contentKey ? _self.contentKey : contentKey // ignore: cast_nullable_to_non_nullable
as String?,contentTitle: freezed == contentTitle ? _self.contentTitle : contentTitle // ignore: cast_nullable_to_non_nullable
as String?,targetPath: null == targetPath ? _self.targetPath : targetPath // ignore: cast_nullable_to_non_nullable
as String,mediaType: null == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String,digestAlgorithm: null == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,contentText: freezed == contentText ? _self.contentText : contentText // ignore: cast_nullable_to_non_nullable
as String?,parts: null == parts ? _self._parts : parts // ignore: cast_nullable_to_non_nullable
as List<ContentPackageExportPartV1>,artifact: freezed == artifact ? _self.artifact : artifact // ignore: cast_nullable_to_non_nullable
as ContentPackageArtifactProjectionV1?,awareContentMapping: null == awareContentMapping ? _self._awareContentMapping : awareContentMapping // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,providerPayload: null == providerPayload ? _self._providerPayload : providerPayload // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,provenance: null == provenance ? _self._provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

/// Create a copy of ContentPackageExportDocumentV1
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ContentPackageArtifactProjectionV1CopyWith<$Res>? get artifact {
    if (_self.artifact == null) {
    return null;
  }

  return $ContentPackageArtifactProjectionV1CopyWith<$Res>(_self.artifact!, (value) {
    return _then(_self.copyWith(artifact: value));
  });
}
}


/// @nodoc
mixin _$ContentPackageMaterializedArtifactRefV1 {

@UuidValueConverter() UuidValue? get contentPackageId;@UuidValueConverter() UuidValue? get contentId;@UuidValueConverter() UuidValue? get domainCommitId;@UuidValueConverter() UuidValue? get objectInstanceGraphCommitId; String? get serviceHostReceiptRef; String get outputKey; String get artifactKey; String get status; String? get artifactFamily; String? get artifactRole; List<String> get requiredFor; String? get producerProviderKey; String? get producerKey; String? get producerKind; int? get materializationIndex; String? get digestAlgorithm; String? get digest; String? get relativePath; String? get uri; String? get mediaType; int? get sizeBytes; String? get runtimeContractVersion; Map<String, dynamic> get providerPayload; Map<String, dynamic> get receiptPayload;
/// Create a copy of ContentPackageMaterializedArtifactRefV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ContentPackageMaterializedArtifactRefV1CopyWith<ContentPackageMaterializedArtifactRefV1> get copyWith => _$ContentPackageMaterializedArtifactRefV1CopyWithImpl<ContentPackageMaterializedArtifactRefV1>(this as ContentPackageMaterializedArtifactRefV1, _$identity);

  /// Serializes this ContentPackageMaterializedArtifactRefV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ContentPackageMaterializedArtifactRefV1&&(identical(other.contentPackageId, contentPackageId) || other.contentPackageId == contentPackageId)&&(identical(other.contentId, contentId) || other.contentId == contentId)&&(identical(other.domainCommitId, domainCommitId) || other.domainCommitId == domainCommitId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.serviceHostReceiptRef, serviceHostReceiptRef) || other.serviceHostReceiptRef == serviceHostReceiptRef)&&(identical(other.outputKey, outputKey) || other.outputKey == outputKey)&&(identical(other.artifactKey, artifactKey) || other.artifactKey == artifactKey)&&(identical(other.status, status) || other.status == status)&&(identical(other.artifactFamily, artifactFamily) || other.artifactFamily == artifactFamily)&&(identical(other.artifactRole, artifactRole) || other.artifactRole == artifactRole)&&const DeepCollectionEquality().equals(other.requiredFor, requiredFor)&&(identical(other.producerProviderKey, producerProviderKey) || other.producerProviderKey == producerProviderKey)&&(identical(other.producerKey, producerKey) || other.producerKey == producerKey)&&(identical(other.producerKind, producerKind) || other.producerKind == producerKind)&&(identical(other.materializationIndex, materializationIndex) || other.materializationIndex == materializationIndex)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.relativePath, relativePath) || other.relativePath == relativePath)&&(identical(other.uri, uri) || other.uri == uri)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.runtimeContractVersion, runtimeContractVersion) || other.runtimeContractVersion == runtimeContractVersion)&&const DeepCollectionEquality().equals(other.providerPayload, providerPayload)&&const DeepCollectionEquality().equals(other.receiptPayload, receiptPayload));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,contentPackageId,contentId,domainCommitId,objectInstanceGraphCommitId,serviceHostReceiptRef,outputKey,artifactKey,status,artifactFamily,artifactRole,const DeepCollectionEquality().hash(requiredFor),producerProviderKey,producerKey,producerKind,materializationIndex,digestAlgorithm,digest,relativePath,uri,mediaType,sizeBytes,runtimeContractVersion,const DeepCollectionEquality().hash(providerPayload),const DeepCollectionEquality().hash(receiptPayload)]);

@override
String toString() {
  return 'ContentPackageMaterializedArtifactRefV1(contentPackageId: $contentPackageId, contentId: $contentId, domainCommitId: $domainCommitId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, serviceHostReceiptRef: $serviceHostReceiptRef, outputKey: $outputKey, artifactKey: $artifactKey, status: $status, artifactFamily: $artifactFamily, artifactRole: $artifactRole, requiredFor: $requiredFor, producerProviderKey: $producerProviderKey, producerKey: $producerKey, producerKind: $producerKind, materializationIndex: $materializationIndex, digestAlgorithm: $digestAlgorithm, digest: $digest, relativePath: $relativePath, uri: $uri, mediaType: $mediaType, sizeBytes: $sizeBytes, runtimeContractVersion: $runtimeContractVersion, providerPayload: $providerPayload, receiptPayload: $receiptPayload)';
}


}

/// @nodoc
abstract mixin class $ContentPackageMaterializedArtifactRefV1CopyWith<$Res>  {
  factory $ContentPackageMaterializedArtifactRefV1CopyWith(ContentPackageMaterializedArtifactRefV1 value, $Res Function(ContentPackageMaterializedArtifactRefV1) _then) = _$ContentPackageMaterializedArtifactRefV1CopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? contentPackageId,@UuidValueConverter() UuidValue? contentId,@UuidValueConverter() UuidValue? domainCommitId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String? serviceHostReceiptRef, String outputKey, String artifactKey, String status, String? artifactFamily, String? artifactRole, List<String> requiredFor, String? producerProviderKey, String? producerKey, String? producerKind, int? materializationIndex, String? digestAlgorithm, String? digest, String? relativePath, String? uri, String? mediaType, int? sizeBytes, String? runtimeContractVersion, Map<String, dynamic> providerPayload, Map<String, dynamic> receiptPayload
});




}
/// @nodoc
class _$ContentPackageMaterializedArtifactRefV1CopyWithImpl<$Res>
    implements $ContentPackageMaterializedArtifactRefV1CopyWith<$Res> {
  _$ContentPackageMaterializedArtifactRefV1CopyWithImpl(this._self, this._then);

  final ContentPackageMaterializedArtifactRefV1 _self;
  final $Res Function(ContentPackageMaterializedArtifactRefV1) _then;

/// Create a copy of ContentPackageMaterializedArtifactRefV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? contentPackageId = freezed,Object? contentId = freezed,Object? domainCommitId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? serviceHostReceiptRef = freezed,Object? outputKey = null,Object? artifactKey = null,Object? status = null,Object? artifactFamily = freezed,Object? artifactRole = freezed,Object? requiredFor = null,Object? producerProviderKey = freezed,Object? producerKey = freezed,Object? producerKind = freezed,Object? materializationIndex = freezed,Object? digestAlgorithm = freezed,Object? digest = freezed,Object? relativePath = freezed,Object? uri = freezed,Object? mediaType = freezed,Object? sizeBytes = freezed,Object? runtimeContractVersion = freezed,Object? providerPayload = null,Object? receiptPayload = null,}) {
  return _then(_self.copyWith(
contentPackageId: freezed == contentPackageId ? _self.contentPackageId : contentPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,contentId: freezed == contentId ? _self.contentId : contentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,domainCommitId: freezed == domainCommitId ? _self.domainCommitId : domainCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceHostReceiptRef: freezed == serviceHostReceiptRef ? _self.serviceHostReceiptRef : serviceHostReceiptRef // ignore: cast_nullable_to_non_nullable
as String?,outputKey: null == outputKey ? _self.outputKey : outputKey // ignore: cast_nullable_to_non_nullable
as String,artifactKey: null == artifactKey ? _self.artifactKey : artifactKey // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,artifactFamily: freezed == artifactFamily ? _self.artifactFamily : artifactFamily // ignore: cast_nullable_to_non_nullable
as String?,artifactRole: freezed == artifactRole ? _self.artifactRole : artifactRole // ignore: cast_nullable_to_non_nullable
as String?,requiredFor: null == requiredFor ? _self.requiredFor : requiredFor // ignore: cast_nullable_to_non_nullable
as List<String>,producerProviderKey: freezed == producerProviderKey ? _self.producerProviderKey : producerProviderKey // ignore: cast_nullable_to_non_nullable
as String?,producerKey: freezed == producerKey ? _self.producerKey : producerKey // ignore: cast_nullable_to_non_nullable
as String?,producerKind: freezed == producerKind ? _self.producerKind : producerKind // ignore: cast_nullable_to_non_nullable
as String?,materializationIndex: freezed == materializationIndex ? _self.materializationIndex : materializationIndex // ignore: cast_nullable_to_non_nullable
as int?,digestAlgorithm: freezed == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String?,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,relativePath: freezed == relativePath ? _self.relativePath : relativePath // ignore: cast_nullable_to_non_nullable
as String?,uri: freezed == uri ? _self.uri : uri // ignore: cast_nullable_to_non_nullable
as String?,mediaType: freezed == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,runtimeContractVersion: freezed == runtimeContractVersion ? _self.runtimeContractVersion : runtimeContractVersion // ignore: cast_nullable_to_non_nullable
as String?,providerPayload: null == providerPayload ? _self.providerPayload : providerPayload // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,receiptPayload: null == receiptPayload ? _self.receiptPayload : receiptPayload // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [ContentPackageMaterializedArtifactRefV1].
extension ContentPackageMaterializedArtifactRefV1Patterns on ContentPackageMaterializedArtifactRefV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ContentPackageMaterializedArtifactRefV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ContentPackageMaterializedArtifactRefV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ContentPackageMaterializedArtifactRefV1 value)  def,}){
final _that = this;
switch (_that) {
case _ContentPackageMaterializedArtifactRefV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ContentPackageMaterializedArtifactRefV1 value)?  def,}){
final _that = this;
switch (_that) {
case _ContentPackageMaterializedArtifactRefV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? contentPackageId, @UuidValueConverter()  UuidValue? contentId, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? serviceHostReceiptRef,  String outputKey,  String artifactKey,  String status,  String? artifactFamily,  String? artifactRole,  List<String> requiredFor,  String? producerProviderKey,  String? producerKey,  String? producerKind,  int? materializationIndex,  String? digestAlgorithm,  String? digest,  String? relativePath,  String? uri,  String? mediaType,  int? sizeBytes,  String? runtimeContractVersion,  Map<String, dynamic> providerPayload,  Map<String, dynamic> receiptPayload)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ContentPackageMaterializedArtifactRefV1() when def != null:
return def(_that.contentPackageId,_that.contentId,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.serviceHostReceiptRef,_that.outputKey,_that.artifactKey,_that.status,_that.artifactFamily,_that.artifactRole,_that.requiredFor,_that.producerProviderKey,_that.producerKey,_that.producerKind,_that.materializationIndex,_that.digestAlgorithm,_that.digest,_that.relativePath,_that.uri,_that.mediaType,_that.sizeBytes,_that.runtimeContractVersion,_that.providerPayload,_that.receiptPayload);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? contentPackageId, @UuidValueConverter()  UuidValue? contentId, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? serviceHostReceiptRef,  String outputKey,  String artifactKey,  String status,  String? artifactFamily,  String? artifactRole,  List<String> requiredFor,  String? producerProviderKey,  String? producerKey,  String? producerKind,  int? materializationIndex,  String? digestAlgorithm,  String? digest,  String? relativePath,  String? uri,  String? mediaType,  int? sizeBytes,  String? runtimeContractVersion,  Map<String, dynamic> providerPayload,  Map<String, dynamic> receiptPayload)  def,}) {final _that = this;
switch (_that) {
case _ContentPackageMaterializedArtifactRefV1():
return def(_that.contentPackageId,_that.contentId,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.serviceHostReceiptRef,_that.outputKey,_that.artifactKey,_that.status,_that.artifactFamily,_that.artifactRole,_that.requiredFor,_that.producerProviderKey,_that.producerKey,_that.producerKind,_that.materializationIndex,_that.digestAlgorithm,_that.digest,_that.relativePath,_that.uri,_that.mediaType,_that.sizeBytes,_that.runtimeContractVersion,_that.providerPayload,_that.receiptPayload);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? contentPackageId, @UuidValueConverter()  UuidValue? contentId, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? serviceHostReceiptRef,  String outputKey,  String artifactKey,  String status,  String? artifactFamily,  String? artifactRole,  List<String> requiredFor,  String? producerProviderKey,  String? producerKey,  String? producerKind,  int? materializationIndex,  String? digestAlgorithm,  String? digest,  String? relativePath,  String? uri,  String? mediaType,  int? sizeBytes,  String? runtimeContractVersion,  Map<String, dynamic> providerPayload,  Map<String, dynamic> receiptPayload)?  def,}) {final _that = this;
switch (_that) {
case _ContentPackageMaterializedArtifactRefV1() when def != null:
return def(_that.contentPackageId,_that.contentId,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.serviceHostReceiptRef,_that.outputKey,_that.artifactKey,_that.status,_that.artifactFamily,_that.artifactRole,_that.requiredFor,_that.producerProviderKey,_that.producerKey,_that.producerKind,_that.materializationIndex,_that.digestAlgorithm,_that.digest,_that.relativePath,_that.uri,_that.mediaType,_that.sizeBytes,_that.runtimeContractVersion,_that.providerPayload,_that.receiptPayload);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ContentPackageMaterializedArtifactRefV1 implements ContentPackageMaterializedArtifactRefV1 {
   _ContentPackageMaterializedArtifactRefV1({@UuidValueConverter() this.contentPackageId, @UuidValueConverter() this.contentId, @UuidValueConverter() this.domainCommitId, @UuidValueConverter() this.objectInstanceGraphCommitId, this.serviceHostReceiptRef, required this.outputKey, required this.artifactKey, required this.status, this.artifactFamily, this.artifactRole, final  List<String> requiredFor = const [], this.producerProviderKey, this.producerKey, this.producerKind, this.materializationIndex, this.digestAlgorithm, this.digest, this.relativePath, this.uri, this.mediaType, this.sizeBytes, this.runtimeContractVersion, required final  Map<String, dynamic> providerPayload, required final  Map<String, dynamic> receiptPayload}): _requiredFor = requiredFor,_providerPayload = providerPayload,_receiptPayload = receiptPayload;
  factory _ContentPackageMaterializedArtifactRefV1.fromJson(Map<String, dynamic> json) => _$ContentPackageMaterializedArtifactRefV1FromJson(json);

@override@UuidValueConverter() final  UuidValue? contentPackageId;
@override@UuidValueConverter() final  UuidValue? contentId;
@override@UuidValueConverter() final  UuidValue? domainCommitId;
@override@UuidValueConverter() final  UuidValue? objectInstanceGraphCommitId;
@override final  String? serviceHostReceiptRef;
@override final  String outputKey;
@override final  String artifactKey;
@override final  String status;
@override final  String? artifactFamily;
@override final  String? artifactRole;
 final  List<String> _requiredFor;
@override@JsonKey() List<String> get requiredFor {
  if (_requiredFor is EqualUnmodifiableListView) return _requiredFor;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_requiredFor);
}

@override final  String? producerProviderKey;
@override final  String? producerKey;
@override final  String? producerKind;
@override final  int? materializationIndex;
@override final  String? digestAlgorithm;
@override final  String? digest;
@override final  String? relativePath;
@override final  String? uri;
@override final  String? mediaType;
@override final  int? sizeBytes;
@override final  String? runtimeContractVersion;
 final  Map<String, dynamic> _providerPayload;
@override Map<String, dynamic> get providerPayload {
  if (_providerPayload is EqualUnmodifiableMapView) return _providerPayload;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_providerPayload);
}

 final  Map<String, dynamic> _receiptPayload;
@override Map<String, dynamic> get receiptPayload {
  if (_receiptPayload is EqualUnmodifiableMapView) return _receiptPayload;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_receiptPayload);
}


/// Create a copy of ContentPackageMaterializedArtifactRefV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ContentPackageMaterializedArtifactRefV1CopyWith<_ContentPackageMaterializedArtifactRefV1> get copyWith => __$ContentPackageMaterializedArtifactRefV1CopyWithImpl<_ContentPackageMaterializedArtifactRefV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ContentPackageMaterializedArtifactRefV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ContentPackageMaterializedArtifactRefV1&&(identical(other.contentPackageId, contentPackageId) || other.contentPackageId == contentPackageId)&&(identical(other.contentId, contentId) || other.contentId == contentId)&&(identical(other.domainCommitId, domainCommitId) || other.domainCommitId == domainCommitId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.serviceHostReceiptRef, serviceHostReceiptRef) || other.serviceHostReceiptRef == serviceHostReceiptRef)&&(identical(other.outputKey, outputKey) || other.outputKey == outputKey)&&(identical(other.artifactKey, artifactKey) || other.artifactKey == artifactKey)&&(identical(other.status, status) || other.status == status)&&(identical(other.artifactFamily, artifactFamily) || other.artifactFamily == artifactFamily)&&(identical(other.artifactRole, artifactRole) || other.artifactRole == artifactRole)&&const DeepCollectionEquality().equals(other._requiredFor, _requiredFor)&&(identical(other.producerProviderKey, producerProviderKey) || other.producerProviderKey == producerProviderKey)&&(identical(other.producerKey, producerKey) || other.producerKey == producerKey)&&(identical(other.producerKind, producerKind) || other.producerKind == producerKind)&&(identical(other.materializationIndex, materializationIndex) || other.materializationIndex == materializationIndex)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.relativePath, relativePath) || other.relativePath == relativePath)&&(identical(other.uri, uri) || other.uri == uri)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.runtimeContractVersion, runtimeContractVersion) || other.runtimeContractVersion == runtimeContractVersion)&&const DeepCollectionEquality().equals(other._providerPayload, _providerPayload)&&const DeepCollectionEquality().equals(other._receiptPayload, _receiptPayload));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,contentPackageId,contentId,domainCommitId,objectInstanceGraphCommitId,serviceHostReceiptRef,outputKey,artifactKey,status,artifactFamily,artifactRole,const DeepCollectionEquality().hash(_requiredFor),producerProviderKey,producerKey,producerKind,materializationIndex,digestAlgorithm,digest,relativePath,uri,mediaType,sizeBytes,runtimeContractVersion,const DeepCollectionEquality().hash(_providerPayload),const DeepCollectionEquality().hash(_receiptPayload)]);

@override
String toString() {
  return 'ContentPackageMaterializedArtifactRefV1.def(contentPackageId: $contentPackageId, contentId: $contentId, domainCommitId: $domainCommitId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, serviceHostReceiptRef: $serviceHostReceiptRef, outputKey: $outputKey, artifactKey: $artifactKey, status: $status, artifactFamily: $artifactFamily, artifactRole: $artifactRole, requiredFor: $requiredFor, producerProviderKey: $producerProviderKey, producerKey: $producerKey, producerKind: $producerKind, materializationIndex: $materializationIndex, digestAlgorithm: $digestAlgorithm, digest: $digest, relativePath: $relativePath, uri: $uri, mediaType: $mediaType, sizeBytes: $sizeBytes, runtimeContractVersion: $runtimeContractVersion, providerPayload: $providerPayload, receiptPayload: $receiptPayload)';
}


}

/// @nodoc
abstract mixin class _$ContentPackageMaterializedArtifactRefV1CopyWith<$Res> implements $ContentPackageMaterializedArtifactRefV1CopyWith<$Res> {
  factory _$ContentPackageMaterializedArtifactRefV1CopyWith(_ContentPackageMaterializedArtifactRefV1 value, $Res Function(_ContentPackageMaterializedArtifactRefV1) _then) = __$ContentPackageMaterializedArtifactRefV1CopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? contentPackageId,@UuidValueConverter() UuidValue? contentId,@UuidValueConverter() UuidValue? domainCommitId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String? serviceHostReceiptRef, String outputKey, String artifactKey, String status, String? artifactFamily, String? artifactRole, List<String> requiredFor, String? producerProviderKey, String? producerKey, String? producerKind, int? materializationIndex, String? digestAlgorithm, String? digest, String? relativePath, String? uri, String? mediaType, int? sizeBytes, String? runtimeContractVersion, Map<String, dynamic> providerPayload, Map<String, dynamic> receiptPayload
});




}
/// @nodoc
class __$ContentPackageMaterializedArtifactRefV1CopyWithImpl<$Res>
    implements _$ContentPackageMaterializedArtifactRefV1CopyWith<$Res> {
  __$ContentPackageMaterializedArtifactRefV1CopyWithImpl(this._self, this._then);

  final _ContentPackageMaterializedArtifactRefV1 _self;
  final $Res Function(_ContentPackageMaterializedArtifactRefV1) _then;

/// Create a copy of ContentPackageMaterializedArtifactRefV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? contentPackageId = freezed,Object? contentId = freezed,Object? domainCommitId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? serviceHostReceiptRef = freezed,Object? outputKey = null,Object? artifactKey = null,Object? status = null,Object? artifactFamily = freezed,Object? artifactRole = freezed,Object? requiredFor = null,Object? producerProviderKey = freezed,Object? producerKey = freezed,Object? producerKind = freezed,Object? materializationIndex = freezed,Object? digestAlgorithm = freezed,Object? digest = freezed,Object? relativePath = freezed,Object? uri = freezed,Object? mediaType = freezed,Object? sizeBytes = freezed,Object? runtimeContractVersion = freezed,Object? providerPayload = null,Object? receiptPayload = null,}) {
  return _then(_ContentPackageMaterializedArtifactRefV1(
contentPackageId: freezed == contentPackageId ? _self.contentPackageId : contentPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,contentId: freezed == contentId ? _self.contentId : contentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,domainCommitId: freezed == domainCommitId ? _self.domainCommitId : domainCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceHostReceiptRef: freezed == serviceHostReceiptRef ? _self.serviceHostReceiptRef : serviceHostReceiptRef // ignore: cast_nullable_to_non_nullable
as String?,outputKey: null == outputKey ? _self.outputKey : outputKey // ignore: cast_nullable_to_non_nullable
as String,artifactKey: null == artifactKey ? _self.artifactKey : artifactKey // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,artifactFamily: freezed == artifactFamily ? _self.artifactFamily : artifactFamily // ignore: cast_nullable_to_non_nullable
as String?,artifactRole: freezed == artifactRole ? _self.artifactRole : artifactRole // ignore: cast_nullable_to_non_nullable
as String?,requiredFor: null == requiredFor ? _self._requiredFor : requiredFor // ignore: cast_nullable_to_non_nullable
as List<String>,producerProviderKey: freezed == producerProviderKey ? _self.producerProviderKey : producerProviderKey // ignore: cast_nullable_to_non_nullable
as String?,producerKey: freezed == producerKey ? _self.producerKey : producerKey // ignore: cast_nullable_to_non_nullable
as String?,producerKind: freezed == producerKind ? _self.producerKind : producerKind // ignore: cast_nullable_to_non_nullable
as String?,materializationIndex: freezed == materializationIndex ? _self.materializationIndex : materializationIndex // ignore: cast_nullable_to_non_nullable
as int?,digestAlgorithm: freezed == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String?,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,relativePath: freezed == relativePath ? _self.relativePath : relativePath // ignore: cast_nullable_to_non_nullable
as String?,uri: freezed == uri ? _self.uri : uri // ignore: cast_nullable_to_non_nullable
as String?,mediaType: freezed == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,runtimeContractVersion: freezed == runtimeContractVersion ? _self.runtimeContractVersion : runtimeContractVersion // ignore: cast_nullable_to_non_nullable
as String?,providerPayload: null == providerPayload ? _self._providerPayload : providerPayload // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,receiptPayload: null == receiptPayload ? _self._receiptPayload : receiptPayload // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$ContentPackageMaterializationResultV1 {

@UuidValueConverter() UuidValue? get contentPackageId;@UuidValueConverter() UuidValue? get contentId;@UuidValueConverter() UuidValue? get domainCommitId;@UuidValueConverter() UuidValue? get objectInstanceGraphCommitId; String? get serviceHostReceiptRef; String get packageName; String? get contentKey; String get sourceProviderKey; String get sourceRef; String get targetPath; String get mediaType; String get digestAlgorithm; String? get digest; int? get sizeBytes; List<ContentPackageMaterializedArtifactRefV1> get artifactRefs; Map<String, dynamic> get awareContentMapping; Map<String, dynamic> get provenance;
/// Create a copy of ContentPackageMaterializationResultV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ContentPackageMaterializationResultV1CopyWith<ContentPackageMaterializationResultV1> get copyWith => _$ContentPackageMaterializationResultV1CopyWithImpl<ContentPackageMaterializationResultV1>(this as ContentPackageMaterializationResultV1, _$identity);

  /// Serializes this ContentPackageMaterializationResultV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ContentPackageMaterializationResultV1&&(identical(other.contentPackageId, contentPackageId) || other.contentPackageId == contentPackageId)&&(identical(other.contentId, contentId) || other.contentId == contentId)&&(identical(other.domainCommitId, domainCommitId) || other.domainCommitId == domainCommitId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.serviceHostReceiptRef, serviceHostReceiptRef) || other.serviceHostReceiptRef == serviceHostReceiptRef)&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.contentKey, contentKey) || other.contentKey == contentKey)&&(identical(other.sourceProviderKey, sourceProviderKey) || other.sourceProviderKey == sourceProviderKey)&&(identical(other.sourceRef, sourceRef) || other.sourceRef == sourceRef)&&(identical(other.targetPath, targetPath) || other.targetPath == targetPath)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&const DeepCollectionEquality().equals(other.artifactRefs, artifactRefs)&&const DeepCollectionEquality().equals(other.awareContentMapping, awareContentMapping)&&const DeepCollectionEquality().equals(other.provenance, provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,contentPackageId,contentId,domainCommitId,objectInstanceGraphCommitId,serviceHostReceiptRef,packageName,contentKey,sourceProviderKey,sourceRef,targetPath,mediaType,digestAlgorithm,digest,sizeBytes,const DeepCollectionEquality().hash(artifactRefs),const DeepCollectionEquality().hash(awareContentMapping),const DeepCollectionEquality().hash(provenance));

@override
String toString() {
  return 'ContentPackageMaterializationResultV1(contentPackageId: $contentPackageId, contentId: $contentId, domainCommitId: $domainCommitId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, serviceHostReceiptRef: $serviceHostReceiptRef, packageName: $packageName, contentKey: $contentKey, sourceProviderKey: $sourceProviderKey, sourceRef: $sourceRef, targetPath: $targetPath, mediaType: $mediaType, digestAlgorithm: $digestAlgorithm, digest: $digest, sizeBytes: $sizeBytes, artifactRefs: $artifactRefs, awareContentMapping: $awareContentMapping, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class $ContentPackageMaterializationResultV1CopyWith<$Res>  {
  factory $ContentPackageMaterializationResultV1CopyWith(ContentPackageMaterializationResultV1 value, $Res Function(ContentPackageMaterializationResultV1) _then) = _$ContentPackageMaterializationResultV1CopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? contentPackageId,@UuidValueConverter() UuidValue? contentId,@UuidValueConverter() UuidValue? domainCommitId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String? serviceHostReceiptRef, String packageName, String? contentKey, String sourceProviderKey, String sourceRef, String targetPath, String mediaType, String digestAlgorithm, String? digest, int? sizeBytes, List<ContentPackageMaterializedArtifactRefV1> artifactRefs, Map<String, dynamic> awareContentMapping, Map<String, dynamic> provenance
});




}
/// @nodoc
class _$ContentPackageMaterializationResultV1CopyWithImpl<$Res>
    implements $ContentPackageMaterializationResultV1CopyWith<$Res> {
  _$ContentPackageMaterializationResultV1CopyWithImpl(this._self, this._then);

  final ContentPackageMaterializationResultV1 _self;
  final $Res Function(ContentPackageMaterializationResultV1) _then;

/// Create a copy of ContentPackageMaterializationResultV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? contentPackageId = freezed,Object? contentId = freezed,Object? domainCommitId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? serviceHostReceiptRef = freezed,Object? packageName = null,Object? contentKey = freezed,Object? sourceProviderKey = null,Object? sourceRef = null,Object? targetPath = null,Object? mediaType = null,Object? digestAlgorithm = null,Object? digest = freezed,Object? sizeBytes = freezed,Object? artifactRefs = null,Object? awareContentMapping = null,Object? provenance = null,}) {
  return _then(_self.copyWith(
contentPackageId: freezed == contentPackageId ? _self.contentPackageId : contentPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,contentId: freezed == contentId ? _self.contentId : contentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,domainCommitId: freezed == domainCommitId ? _self.domainCommitId : domainCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceHostReceiptRef: freezed == serviceHostReceiptRef ? _self.serviceHostReceiptRef : serviceHostReceiptRef // ignore: cast_nullable_to_non_nullable
as String?,packageName: null == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String,contentKey: freezed == contentKey ? _self.contentKey : contentKey // ignore: cast_nullable_to_non_nullable
as String?,sourceProviderKey: null == sourceProviderKey ? _self.sourceProviderKey : sourceProviderKey // ignore: cast_nullable_to_non_nullable
as String,sourceRef: null == sourceRef ? _self.sourceRef : sourceRef // ignore: cast_nullable_to_non_nullable
as String,targetPath: null == targetPath ? _self.targetPath : targetPath // ignore: cast_nullable_to_non_nullable
as String,mediaType: null == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String,digestAlgorithm: null == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,artifactRefs: null == artifactRefs ? _self.artifactRefs : artifactRefs // ignore: cast_nullable_to_non_nullable
as List<ContentPackageMaterializedArtifactRefV1>,awareContentMapping: null == awareContentMapping ? _self.awareContentMapping : awareContentMapping // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,provenance: null == provenance ? _self.provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [ContentPackageMaterializationResultV1].
extension ContentPackageMaterializationResultV1Patterns on ContentPackageMaterializationResultV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ContentPackageMaterializationResultV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ContentPackageMaterializationResultV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ContentPackageMaterializationResultV1 value)  def,}){
final _that = this;
switch (_that) {
case _ContentPackageMaterializationResultV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ContentPackageMaterializationResultV1 value)?  def,}){
final _that = this;
switch (_that) {
case _ContentPackageMaterializationResultV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? contentPackageId, @UuidValueConverter()  UuidValue? contentId, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? serviceHostReceiptRef,  String packageName,  String? contentKey,  String sourceProviderKey,  String sourceRef,  String targetPath,  String mediaType,  String digestAlgorithm,  String? digest,  int? sizeBytes,  List<ContentPackageMaterializedArtifactRefV1> artifactRefs,  Map<String, dynamic> awareContentMapping,  Map<String, dynamic> provenance)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ContentPackageMaterializationResultV1() when def != null:
return def(_that.contentPackageId,_that.contentId,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.serviceHostReceiptRef,_that.packageName,_that.contentKey,_that.sourceProviderKey,_that.sourceRef,_that.targetPath,_that.mediaType,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.artifactRefs,_that.awareContentMapping,_that.provenance);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? contentPackageId, @UuidValueConverter()  UuidValue? contentId, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? serviceHostReceiptRef,  String packageName,  String? contentKey,  String sourceProviderKey,  String sourceRef,  String targetPath,  String mediaType,  String digestAlgorithm,  String? digest,  int? sizeBytes,  List<ContentPackageMaterializedArtifactRefV1> artifactRefs,  Map<String, dynamic> awareContentMapping,  Map<String, dynamic> provenance)  def,}) {final _that = this;
switch (_that) {
case _ContentPackageMaterializationResultV1():
return def(_that.contentPackageId,_that.contentId,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.serviceHostReceiptRef,_that.packageName,_that.contentKey,_that.sourceProviderKey,_that.sourceRef,_that.targetPath,_that.mediaType,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.artifactRefs,_that.awareContentMapping,_that.provenance);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? contentPackageId, @UuidValueConverter()  UuidValue? contentId, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? serviceHostReceiptRef,  String packageName,  String? contentKey,  String sourceProviderKey,  String sourceRef,  String targetPath,  String mediaType,  String digestAlgorithm,  String? digest,  int? sizeBytes,  List<ContentPackageMaterializedArtifactRefV1> artifactRefs,  Map<String, dynamic> awareContentMapping,  Map<String, dynamic> provenance)?  def,}) {final _that = this;
switch (_that) {
case _ContentPackageMaterializationResultV1() when def != null:
return def(_that.contentPackageId,_that.contentId,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.serviceHostReceiptRef,_that.packageName,_that.contentKey,_that.sourceProviderKey,_that.sourceRef,_that.targetPath,_that.mediaType,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.artifactRefs,_that.awareContentMapping,_that.provenance);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ContentPackageMaterializationResultV1 implements ContentPackageMaterializationResultV1 {
   _ContentPackageMaterializationResultV1({@UuidValueConverter() this.contentPackageId, @UuidValueConverter() this.contentId, @UuidValueConverter() this.domainCommitId, @UuidValueConverter() this.objectInstanceGraphCommitId, this.serviceHostReceiptRef, required this.packageName, this.contentKey, required this.sourceProviderKey, required this.sourceRef, required this.targetPath, required this.mediaType, required this.digestAlgorithm, this.digest, this.sizeBytes, final  List<ContentPackageMaterializedArtifactRefV1> artifactRefs = const [], required final  Map<String, dynamic> awareContentMapping, required final  Map<String, dynamic> provenance}): _artifactRefs = artifactRefs,_awareContentMapping = awareContentMapping,_provenance = provenance;
  factory _ContentPackageMaterializationResultV1.fromJson(Map<String, dynamic> json) => _$ContentPackageMaterializationResultV1FromJson(json);

@override@UuidValueConverter() final  UuidValue? contentPackageId;
@override@UuidValueConverter() final  UuidValue? contentId;
@override@UuidValueConverter() final  UuidValue? domainCommitId;
@override@UuidValueConverter() final  UuidValue? objectInstanceGraphCommitId;
@override final  String? serviceHostReceiptRef;
@override final  String packageName;
@override final  String? contentKey;
@override final  String sourceProviderKey;
@override final  String sourceRef;
@override final  String targetPath;
@override final  String mediaType;
@override final  String digestAlgorithm;
@override final  String? digest;
@override final  int? sizeBytes;
 final  List<ContentPackageMaterializedArtifactRefV1> _artifactRefs;
@override@JsonKey() List<ContentPackageMaterializedArtifactRefV1> get artifactRefs {
  if (_artifactRefs is EqualUnmodifiableListView) return _artifactRefs;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_artifactRefs);
}

 final  Map<String, dynamic> _awareContentMapping;
@override Map<String, dynamic> get awareContentMapping {
  if (_awareContentMapping is EqualUnmodifiableMapView) return _awareContentMapping;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_awareContentMapping);
}

 final  Map<String, dynamic> _provenance;
@override Map<String, dynamic> get provenance {
  if (_provenance is EqualUnmodifiableMapView) return _provenance;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_provenance);
}


/// Create a copy of ContentPackageMaterializationResultV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ContentPackageMaterializationResultV1CopyWith<_ContentPackageMaterializationResultV1> get copyWith => __$ContentPackageMaterializationResultV1CopyWithImpl<_ContentPackageMaterializationResultV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ContentPackageMaterializationResultV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ContentPackageMaterializationResultV1&&(identical(other.contentPackageId, contentPackageId) || other.contentPackageId == contentPackageId)&&(identical(other.contentId, contentId) || other.contentId == contentId)&&(identical(other.domainCommitId, domainCommitId) || other.domainCommitId == domainCommitId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.serviceHostReceiptRef, serviceHostReceiptRef) || other.serviceHostReceiptRef == serviceHostReceiptRef)&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.contentKey, contentKey) || other.contentKey == contentKey)&&(identical(other.sourceProviderKey, sourceProviderKey) || other.sourceProviderKey == sourceProviderKey)&&(identical(other.sourceRef, sourceRef) || other.sourceRef == sourceRef)&&(identical(other.targetPath, targetPath) || other.targetPath == targetPath)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&const DeepCollectionEquality().equals(other._artifactRefs, _artifactRefs)&&const DeepCollectionEquality().equals(other._awareContentMapping, _awareContentMapping)&&const DeepCollectionEquality().equals(other._provenance, _provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,contentPackageId,contentId,domainCommitId,objectInstanceGraphCommitId,serviceHostReceiptRef,packageName,contentKey,sourceProviderKey,sourceRef,targetPath,mediaType,digestAlgorithm,digest,sizeBytes,const DeepCollectionEquality().hash(_artifactRefs),const DeepCollectionEquality().hash(_awareContentMapping),const DeepCollectionEquality().hash(_provenance));

@override
String toString() {
  return 'ContentPackageMaterializationResultV1.def(contentPackageId: $contentPackageId, contentId: $contentId, domainCommitId: $domainCommitId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, serviceHostReceiptRef: $serviceHostReceiptRef, packageName: $packageName, contentKey: $contentKey, sourceProviderKey: $sourceProviderKey, sourceRef: $sourceRef, targetPath: $targetPath, mediaType: $mediaType, digestAlgorithm: $digestAlgorithm, digest: $digest, sizeBytes: $sizeBytes, artifactRefs: $artifactRefs, awareContentMapping: $awareContentMapping, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class _$ContentPackageMaterializationResultV1CopyWith<$Res> implements $ContentPackageMaterializationResultV1CopyWith<$Res> {
  factory _$ContentPackageMaterializationResultV1CopyWith(_ContentPackageMaterializationResultV1 value, $Res Function(_ContentPackageMaterializationResultV1) _then) = __$ContentPackageMaterializationResultV1CopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? contentPackageId,@UuidValueConverter() UuidValue? contentId,@UuidValueConverter() UuidValue? domainCommitId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String? serviceHostReceiptRef, String packageName, String? contentKey, String sourceProviderKey, String sourceRef, String targetPath, String mediaType, String digestAlgorithm, String? digest, int? sizeBytes, List<ContentPackageMaterializedArtifactRefV1> artifactRefs, Map<String, dynamic> awareContentMapping, Map<String, dynamic> provenance
});




}
/// @nodoc
class __$ContentPackageMaterializationResultV1CopyWithImpl<$Res>
    implements _$ContentPackageMaterializationResultV1CopyWith<$Res> {
  __$ContentPackageMaterializationResultV1CopyWithImpl(this._self, this._then);

  final _ContentPackageMaterializationResultV1 _self;
  final $Res Function(_ContentPackageMaterializationResultV1) _then;

/// Create a copy of ContentPackageMaterializationResultV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? contentPackageId = freezed,Object? contentId = freezed,Object? domainCommitId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? serviceHostReceiptRef = freezed,Object? packageName = null,Object? contentKey = freezed,Object? sourceProviderKey = null,Object? sourceRef = null,Object? targetPath = null,Object? mediaType = null,Object? digestAlgorithm = null,Object? digest = freezed,Object? sizeBytes = freezed,Object? artifactRefs = null,Object? awareContentMapping = null,Object? provenance = null,}) {
  return _then(_ContentPackageMaterializationResultV1(
contentPackageId: freezed == contentPackageId ? _self.contentPackageId : contentPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,contentId: freezed == contentId ? _self.contentId : contentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,domainCommitId: freezed == domainCommitId ? _self.domainCommitId : domainCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceHostReceiptRef: freezed == serviceHostReceiptRef ? _self.serviceHostReceiptRef : serviceHostReceiptRef // ignore: cast_nullable_to_non_nullable
as String?,packageName: null == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String,contentKey: freezed == contentKey ? _self.contentKey : contentKey // ignore: cast_nullable_to_non_nullable
as String?,sourceProviderKey: null == sourceProviderKey ? _self.sourceProviderKey : sourceProviderKey // ignore: cast_nullable_to_non_nullable
as String,sourceRef: null == sourceRef ? _self.sourceRef : sourceRef // ignore: cast_nullable_to_non_nullable
as String,targetPath: null == targetPath ? _self.targetPath : targetPath // ignore: cast_nullable_to_non_nullable
as String,mediaType: null == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String,digestAlgorithm: null == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,artifactRefs: null == artifactRefs ? _self._artifactRefs : artifactRefs // ignore: cast_nullable_to_non_nullable
as List<ContentPackageMaterializedArtifactRefV1>,awareContentMapping: null == awareContentMapping ? _self._awareContentMapping : awareContentMapping // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,provenance: null == provenance ? _self._provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$ContentOperationReceipt {

 String get operation; String get status;@UuidValueConverter() UuidValue? get contentId;@UuidValueConverter() UuidValue? get contentPackageId;@UuidValueConverter() UuidValue? get domainCommitId;@UuidValueConverter() UuidValue? get objectInstanceGraphCommitId; String? get serviceHostReceiptRef; String? get packageName; String get digestAlgorithm; String? get digest; int? get sizeBytes; String get backendKind; Map<String, dynamic> get metadata;
/// Create a copy of ContentOperationReceipt
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ContentOperationReceiptCopyWith<ContentOperationReceipt> get copyWith => _$ContentOperationReceiptCopyWithImpl<ContentOperationReceipt>(this as ContentOperationReceipt, _$identity);

  /// Serializes this ContentOperationReceipt to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ContentOperationReceipt&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.status, status) || other.status == status)&&(identical(other.contentId, contentId) || other.contentId == contentId)&&(identical(other.contentPackageId, contentPackageId) || other.contentPackageId == contentPackageId)&&(identical(other.domainCommitId, domainCommitId) || other.domainCommitId == domainCommitId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.serviceHostReceiptRef, serviceHostReceiptRef) || other.serviceHostReceiptRef == serviceHostReceiptRef)&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.backendKind, backendKind) || other.backendKind == backendKind)&&const DeepCollectionEquality().equals(other.metadata, metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,status,contentId,contentPackageId,domainCommitId,objectInstanceGraphCommitId,serviceHostReceiptRef,packageName,digestAlgorithm,digest,sizeBytes,backendKind,const DeepCollectionEquality().hash(metadata));

@override
String toString() {
  return 'ContentOperationReceipt(operation: $operation, status: $status, contentId: $contentId, contentPackageId: $contentPackageId, domainCommitId: $domainCommitId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, serviceHostReceiptRef: $serviceHostReceiptRef, packageName: $packageName, digestAlgorithm: $digestAlgorithm, digest: $digest, sizeBytes: $sizeBytes, backendKind: $backendKind, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class $ContentOperationReceiptCopyWith<$Res>  {
  factory $ContentOperationReceiptCopyWith(ContentOperationReceipt value, $Res Function(ContentOperationReceipt) _then) = _$ContentOperationReceiptCopyWithImpl;
@useResult
$Res call({
 String operation, String status,@UuidValueConverter() UuidValue? contentId,@UuidValueConverter() UuidValue? contentPackageId,@UuidValueConverter() UuidValue? domainCommitId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String? serviceHostReceiptRef, String? packageName, String digestAlgorithm, String? digest, int? sizeBytes, String backendKind, Map<String, dynamic> metadata
});




}
/// @nodoc
class _$ContentOperationReceiptCopyWithImpl<$Res>
    implements $ContentOperationReceiptCopyWith<$Res> {
  _$ContentOperationReceiptCopyWithImpl(this._self, this._then);

  final ContentOperationReceipt _self;
  final $Res Function(ContentOperationReceipt) _then;

/// Create a copy of ContentOperationReceipt
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? operation = null,Object? status = null,Object? contentId = freezed,Object? contentPackageId = freezed,Object? domainCommitId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? serviceHostReceiptRef = freezed,Object? packageName = freezed,Object? digestAlgorithm = null,Object? digest = freezed,Object? sizeBytes = freezed,Object? backendKind = null,Object? metadata = null,}) {
  return _then(_self.copyWith(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,contentId: freezed == contentId ? _self.contentId : contentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,contentPackageId: freezed == contentPackageId ? _self.contentPackageId : contentPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,domainCommitId: freezed == domainCommitId ? _self.domainCommitId : domainCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceHostReceiptRef: freezed == serviceHostReceiptRef ? _self.serviceHostReceiptRef : serviceHostReceiptRef // ignore: cast_nullable_to_non_nullable
as String?,packageName: freezed == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String?,digestAlgorithm: null == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,backendKind: null == backendKind ? _self.backendKind : backendKind // ignore: cast_nullable_to_non_nullable
as String,metadata: null == metadata ? _self.metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [ContentOperationReceipt].
extension ContentOperationReceiptPatterns on ContentOperationReceipt {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ContentOperationReceipt value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ContentOperationReceipt() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ContentOperationReceipt value)  def,}){
final _that = this;
switch (_that) {
case _ContentOperationReceipt():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ContentOperationReceipt value)?  def,}){
final _that = this;
switch (_that) {
case _ContentOperationReceipt() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String operation,  String status, @UuidValueConverter()  UuidValue? contentId, @UuidValueConverter()  UuidValue? contentPackageId, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? serviceHostReceiptRef,  String? packageName,  String digestAlgorithm,  String? digest,  int? sizeBytes,  String backendKind,  Map<String, dynamic> metadata)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ContentOperationReceipt() when def != null:
return def(_that.operation,_that.status,_that.contentId,_that.contentPackageId,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.serviceHostReceiptRef,_that.packageName,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.backendKind,_that.metadata);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String operation,  String status, @UuidValueConverter()  UuidValue? contentId, @UuidValueConverter()  UuidValue? contentPackageId, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? serviceHostReceiptRef,  String? packageName,  String digestAlgorithm,  String? digest,  int? sizeBytes,  String backendKind,  Map<String, dynamic> metadata)  def,}) {final _that = this;
switch (_that) {
case _ContentOperationReceipt():
return def(_that.operation,_that.status,_that.contentId,_that.contentPackageId,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.serviceHostReceiptRef,_that.packageName,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.backendKind,_that.metadata);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String operation,  String status, @UuidValueConverter()  UuidValue? contentId, @UuidValueConverter()  UuidValue? contentPackageId, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? serviceHostReceiptRef,  String? packageName,  String digestAlgorithm,  String? digest,  int? sizeBytes,  String backendKind,  Map<String, dynamic> metadata)?  def,}) {final _that = this;
switch (_that) {
case _ContentOperationReceipt() when def != null:
return def(_that.operation,_that.status,_that.contentId,_that.contentPackageId,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.serviceHostReceiptRef,_that.packageName,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.backendKind,_that.metadata);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ContentOperationReceipt implements ContentOperationReceipt {
   _ContentOperationReceipt({required this.operation, required this.status, @UuidValueConverter() this.contentId, @UuidValueConverter() this.contentPackageId, @UuidValueConverter() this.domainCommitId, @UuidValueConverter() this.objectInstanceGraphCommitId, this.serviceHostReceiptRef, this.packageName, required this.digestAlgorithm, this.digest, this.sizeBytes, required this.backendKind, required final  Map<String, dynamic> metadata}): _metadata = metadata;
  factory _ContentOperationReceipt.fromJson(Map<String, dynamic> json) => _$ContentOperationReceiptFromJson(json);

@override final  String operation;
@override final  String status;
@override@UuidValueConverter() final  UuidValue? contentId;
@override@UuidValueConverter() final  UuidValue? contentPackageId;
@override@UuidValueConverter() final  UuidValue? domainCommitId;
@override@UuidValueConverter() final  UuidValue? objectInstanceGraphCommitId;
@override final  String? serviceHostReceiptRef;
@override final  String? packageName;
@override final  String digestAlgorithm;
@override final  String? digest;
@override final  int? sizeBytes;
@override final  String backendKind;
 final  Map<String, dynamic> _metadata;
@override Map<String, dynamic> get metadata {
  if (_metadata is EqualUnmodifiableMapView) return _metadata;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_metadata);
}


/// Create a copy of ContentOperationReceipt
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ContentOperationReceiptCopyWith<_ContentOperationReceipt> get copyWith => __$ContentOperationReceiptCopyWithImpl<_ContentOperationReceipt>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ContentOperationReceiptToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ContentOperationReceipt&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.status, status) || other.status == status)&&(identical(other.contentId, contentId) || other.contentId == contentId)&&(identical(other.contentPackageId, contentPackageId) || other.contentPackageId == contentPackageId)&&(identical(other.domainCommitId, domainCommitId) || other.domainCommitId == domainCommitId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.serviceHostReceiptRef, serviceHostReceiptRef) || other.serviceHostReceiptRef == serviceHostReceiptRef)&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.backendKind, backendKind) || other.backendKind == backendKind)&&const DeepCollectionEquality().equals(other._metadata, _metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,status,contentId,contentPackageId,domainCommitId,objectInstanceGraphCommitId,serviceHostReceiptRef,packageName,digestAlgorithm,digest,sizeBytes,backendKind,const DeepCollectionEquality().hash(_metadata));

@override
String toString() {
  return 'ContentOperationReceipt.def(operation: $operation, status: $status, contentId: $contentId, contentPackageId: $contentPackageId, domainCommitId: $domainCommitId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, serviceHostReceiptRef: $serviceHostReceiptRef, packageName: $packageName, digestAlgorithm: $digestAlgorithm, digest: $digest, sizeBytes: $sizeBytes, backendKind: $backendKind, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class _$ContentOperationReceiptCopyWith<$Res> implements $ContentOperationReceiptCopyWith<$Res> {
  factory _$ContentOperationReceiptCopyWith(_ContentOperationReceipt value, $Res Function(_ContentOperationReceipt) _then) = __$ContentOperationReceiptCopyWithImpl;
@override @useResult
$Res call({
 String operation, String status,@UuidValueConverter() UuidValue? contentId,@UuidValueConverter() UuidValue? contentPackageId,@UuidValueConverter() UuidValue? domainCommitId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String? serviceHostReceiptRef, String? packageName, String digestAlgorithm, String? digest, int? sizeBytes, String backendKind, Map<String, dynamic> metadata
});




}
/// @nodoc
class __$ContentOperationReceiptCopyWithImpl<$Res>
    implements _$ContentOperationReceiptCopyWith<$Res> {
  __$ContentOperationReceiptCopyWithImpl(this._self, this._then);

  final _ContentOperationReceipt _self;
  final $Res Function(_ContentOperationReceipt) _then;

/// Create a copy of ContentOperationReceipt
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? operation = null,Object? status = null,Object? contentId = freezed,Object? contentPackageId = freezed,Object? domainCommitId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? serviceHostReceiptRef = freezed,Object? packageName = freezed,Object? digestAlgorithm = null,Object? digest = freezed,Object? sizeBytes = freezed,Object? backendKind = null,Object? metadata = null,}) {
  return _then(_ContentOperationReceipt(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,contentId: freezed == contentId ? _self.contentId : contentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,contentPackageId: freezed == contentPackageId ? _self.contentPackageId : contentPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,domainCommitId: freezed == domainCommitId ? _self.domainCommitId : domainCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceHostReceiptRef: freezed == serviceHostReceiptRef ? _self.serviceHostReceiptRef : serviceHostReceiptRef // ignore: cast_nullable_to_non_nullable
as String?,packageName: freezed == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String?,digestAlgorithm: null == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,backendKind: null == backendKind ? _self.backendKind : backendKind // ignore: cast_nullable_to_non_nullable
as String,metadata: null == metadata ? _self._metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}

ContentServiceRequest _$ContentServiceRequestFromJson(
  Map<String, dynamic> json
) {
        switch (json['operation']) {
                  case 'resolve_content_text':
          return ResolveContentTextRequest.fromJson(
            json
          );
                case 'commit_content_text':
          return CommitContentTextRequest.fromJson(
            json
          );
                case 'materialize_content_package':
          return MaterializeContentPackageRequest.fromJson(
            json
          );
        
          default:
            throw CheckedFromJsonException(
  json,
  'operation',
  'ContentServiceRequest',
  'Invalid union type "${json['operation']}"!'
);
        }
      
}

/// @nodoc
mixin _$ContentServiceRequest {

@UuidValueConverter() UuidValue? get requestId;@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue? get branchId;
/// Create a copy of ContentServiceRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ContentServiceRequestCopyWith<ContentServiceRequest> get copyWith => _$ContentServiceRequestCopyWithImpl<ContentServiceRequest>(this as ContentServiceRequest, _$identity);

  /// Serializes this ContentServiceRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ContentServiceRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.branchId, branchId) || other.branchId == branchId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,actorId,branchId);

@override
String toString() {
  return 'ContentServiceRequest(requestId: $requestId, actorId: $actorId, branchId: $branchId)';
}


}

/// @nodoc
abstract mixin class $ContentServiceRequestCopyWith<$Res>  {
  factory $ContentServiceRequestCopyWith(ContentServiceRequest value, $Res Function(ContentServiceRequest) _then) = _$ContentServiceRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? branchId
});




}
/// @nodoc
class _$ContentServiceRequestCopyWithImpl<$Res>
    implements $ContentServiceRequestCopyWith<$Res> {
  _$ContentServiceRequestCopyWithImpl(this._self, this._then);

  final ContentServiceRequest _self;
  final $Res Function(ContentServiceRequest) _then;

/// Create a copy of ContentServiceRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? actorId = freezed,Object? branchId = freezed,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,branchId: freezed == branchId ? _self.branchId : branchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

}


/// Adds pattern-matching-related methods to [ContentServiceRequest].
extension ContentServiceRequestPatterns on ContentServiceRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( ResolveContentTextRequest value)?  resolveContentText,TResult Function( CommitContentTextRequest value)?  commitContentText,TResult Function( MaterializeContentPackageRequest value)?  materializeContentPackage,required TResult orElse(),}){
final _that = this;
switch (_that) {
case ResolveContentTextRequest() when resolveContentText != null:
return resolveContentText(_that);case CommitContentTextRequest() when commitContentText != null:
return commitContentText(_that);case MaterializeContentPackageRequest() when materializeContentPackage != null:
return materializeContentPackage(_that);case _:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( ResolveContentTextRequest value)  resolveContentText,required TResult Function( CommitContentTextRequest value)  commitContentText,required TResult Function( MaterializeContentPackageRequest value)  materializeContentPackage,}){
final _that = this;
switch (_that) {
case ResolveContentTextRequest():
return resolveContentText(_that);case CommitContentTextRequest():
return commitContentText(_that);case MaterializeContentPackageRequest():
return materializeContentPackage(_that);case _:
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( ResolveContentTextRequest value)?  resolveContentText,TResult? Function( CommitContentTextRequest value)?  commitContentText,TResult? Function( MaterializeContentPackageRequest value)?  materializeContentPackage,}){
final _that = this;
switch (_that) {
case ResolveContentTextRequest() when resolveContentText != null:
return resolveContentText(_that);case CommitContentTextRequest() when commitContentText != null:
return commitContentText(_that);case MaterializeContentPackageRequest() when materializeContentPackage != null:
return materializeContentPackage(_that);case _:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? branchId, @UuidValueConverter()  UuidValue? contentId, @UuidValueConverter()  UuidValue? contentClassInstanceIdentityId, @UuidValueConverter()  UuidValue? contentClassConfigId,  String mediaType,  bool includeParts,  int? maxChars)?  resolveContentText,TResult Function(@UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? branchId,  String contentKey,  String? title,  String sourceKind,  String sourceRef,  String mediaType,  String? text,  List<ContentTextCommitPartV1> parts,  String digestAlgorithm,  String? digest,  int? sizeBytes,  Map<String, dynamic> provenance)?  commitContentText,TResult Function(@UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? branchId,  ContentPackageExportDocumentV1 packageExport)?  materializeContentPackage,required TResult orElse(),}) {final _that = this;
switch (_that) {
case ResolveContentTextRequest() when resolveContentText != null:
return resolveContentText(_that.requestId,_that.actorId,_that.branchId,_that.contentId,_that.contentClassInstanceIdentityId,_that.contentClassConfigId,_that.mediaType,_that.includeParts,_that.maxChars);case CommitContentTextRequest() when commitContentText != null:
return commitContentText(_that.requestId,_that.actorId,_that.branchId,_that.contentKey,_that.title,_that.sourceKind,_that.sourceRef,_that.mediaType,_that.text,_that.parts,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.provenance);case MaterializeContentPackageRequest() when materializeContentPackage != null:
return materializeContentPackage(_that.requestId,_that.actorId,_that.branchId,_that.packageExport);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? branchId, @UuidValueConverter()  UuidValue? contentId, @UuidValueConverter()  UuidValue? contentClassInstanceIdentityId, @UuidValueConverter()  UuidValue? contentClassConfigId,  String mediaType,  bool includeParts,  int? maxChars)  resolveContentText,required TResult Function(@UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? branchId,  String contentKey,  String? title,  String sourceKind,  String sourceRef,  String mediaType,  String? text,  List<ContentTextCommitPartV1> parts,  String digestAlgorithm,  String? digest,  int? sizeBytes,  Map<String, dynamic> provenance)  commitContentText,required TResult Function(@UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? branchId,  ContentPackageExportDocumentV1 packageExport)  materializeContentPackage,}) {final _that = this;
switch (_that) {
case ResolveContentTextRequest():
return resolveContentText(_that.requestId,_that.actorId,_that.branchId,_that.contentId,_that.contentClassInstanceIdentityId,_that.contentClassConfigId,_that.mediaType,_that.includeParts,_that.maxChars);case CommitContentTextRequest():
return commitContentText(_that.requestId,_that.actorId,_that.branchId,_that.contentKey,_that.title,_that.sourceKind,_that.sourceRef,_that.mediaType,_that.text,_that.parts,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.provenance);case MaterializeContentPackageRequest():
return materializeContentPackage(_that.requestId,_that.actorId,_that.branchId,_that.packageExport);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? branchId, @UuidValueConverter()  UuidValue? contentId, @UuidValueConverter()  UuidValue? contentClassInstanceIdentityId, @UuidValueConverter()  UuidValue? contentClassConfigId,  String mediaType,  bool includeParts,  int? maxChars)?  resolveContentText,TResult? Function(@UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? branchId,  String contentKey,  String? title,  String sourceKind,  String sourceRef,  String mediaType,  String? text,  List<ContentTextCommitPartV1> parts,  String digestAlgorithm,  String? digest,  int? sizeBytes,  Map<String, dynamic> provenance)?  commitContentText,TResult? Function(@UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? branchId,  ContentPackageExportDocumentV1 packageExport)?  materializeContentPackage,}) {final _that = this;
switch (_that) {
case ResolveContentTextRequest() when resolveContentText != null:
return resolveContentText(_that.requestId,_that.actorId,_that.branchId,_that.contentId,_that.contentClassInstanceIdentityId,_that.contentClassConfigId,_that.mediaType,_that.includeParts,_that.maxChars);case CommitContentTextRequest() when commitContentText != null:
return commitContentText(_that.requestId,_that.actorId,_that.branchId,_that.contentKey,_that.title,_that.sourceKind,_that.sourceRef,_that.mediaType,_that.text,_that.parts,_that.digestAlgorithm,_that.digest,_that.sizeBytes,_that.provenance);case MaterializeContentPackageRequest() when materializeContentPackage != null:
return materializeContentPackage(_that.requestId,_that.actorId,_that.branchId,_that.packageExport);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class ResolveContentTextRequest implements ContentServiceRequest {
   ResolveContentTextRequest({@UuidValueConverter() this.requestId, @UuidValueConverter() this.actorId, @UuidValueConverter() this.branchId, @UuidValueConverter() this.contentId, @UuidValueConverter() this.contentClassInstanceIdentityId, @UuidValueConverter() this.contentClassConfigId, required this.mediaType, required this.includeParts, this.maxChars, final  String? $type}): $type = $type ?? 'resolve_content_text';
  factory ResolveContentTextRequest.fromJson(Map<String, dynamic> json) => _$ResolveContentTextRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? branchId;
@UuidValueConverter() final  UuidValue? contentId;
@UuidValueConverter() final  UuidValue? contentClassInstanceIdentityId;
@UuidValueConverter() final  UuidValue? contentClassConfigId;
 final  String mediaType;
 final  bool includeParts;
 final  int? maxChars;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of ContentServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ResolveContentTextRequestCopyWith<ResolveContentTextRequest> get copyWith => _$ResolveContentTextRequestCopyWithImpl<ResolveContentTextRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ResolveContentTextRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ResolveContentTextRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.branchId, branchId) || other.branchId == branchId)&&(identical(other.contentId, contentId) || other.contentId == contentId)&&(identical(other.contentClassInstanceIdentityId, contentClassInstanceIdentityId) || other.contentClassInstanceIdentityId == contentClassInstanceIdentityId)&&(identical(other.contentClassConfigId, contentClassConfigId) || other.contentClassConfigId == contentClassConfigId)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.includeParts, includeParts) || other.includeParts == includeParts)&&(identical(other.maxChars, maxChars) || other.maxChars == maxChars));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,actorId,branchId,contentId,contentClassInstanceIdentityId,contentClassConfigId,mediaType,includeParts,maxChars);

@override
String toString() {
  return 'ContentServiceRequest.resolveContentText(requestId: $requestId, actorId: $actorId, branchId: $branchId, contentId: $contentId, contentClassInstanceIdentityId: $contentClassInstanceIdentityId, contentClassConfigId: $contentClassConfigId, mediaType: $mediaType, includeParts: $includeParts, maxChars: $maxChars)';
}


}

/// @nodoc
abstract mixin class $ResolveContentTextRequestCopyWith<$Res> implements $ContentServiceRequestCopyWith<$Res> {
  factory $ResolveContentTextRequestCopyWith(ResolveContentTextRequest value, $Res Function(ResolveContentTextRequest) _then) = _$ResolveContentTextRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? branchId,@UuidValueConverter() UuidValue? contentId,@UuidValueConverter() UuidValue? contentClassInstanceIdentityId,@UuidValueConverter() UuidValue? contentClassConfigId, String mediaType, bool includeParts, int? maxChars
});




}
/// @nodoc
class _$ResolveContentTextRequestCopyWithImpl<$Res>
    implements $ResolveContentTextRequestCopyWith<$Res> {
  _$ResolveContentTextRequestCopyWithImpl(this._self, this._then);

  final ResolveContentTextRequest _self;
  final $Res Function(ResolveContentTextRequest) _then;

/// Create a copy of ContentServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? actorId = freezed,Object? branchId = freezed,Object? contentId = freezed,Object? contentClassInstanceIdentityId = freezed,Object? contentClassConfigId = freezed,Object? mediaType = null,Object? includeParts = null,Object? maxChars = freezed,}) {
  return _then(ResolveContentTextRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,branchId: freezed == branchId ? _self.branchId : branchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,contentId: freezed == contentId ? _self.contentId : contentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,contentClassInstanceIdentityId: freezed == contentClassInstanceIdentityId ? _self.contentClassInstanceIdentityId : contentClassInstanceIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue?,contentClassConfigId: freezed == contentClassConfigId ? _self.contentClassConfigId : contentClassConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,mediaType: null == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String,includeParts: null == includeParts ? _self.includeParts : includeParts // ignore: cast_nullable_to_non_nullable
as bool,maxChars: freezed == maxChars ? _self.maxChars : maxChars // ignore: cast_nullable_to_non_nullable
as int?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class CommitContentTextRequest implements ContentServiceRequest {
   CommitContentTextRequest({@UuidValueConverter() this.requestId, @UuidValueConverter() this.actorId, @UuidValueConverter() this.branchId, required this.contentKey, this.title, required this.sourceKind, required this.sourceRef, required this.mediaType, this.text, final  List<ContentTextCommitPartV1> parts = const [], required this.digestAlgorithm, this.digest, this.sizeBytes, required final  Map<String, dynamic> provenance, final  String? $type}): _parts = parts,_provenance = provenance,$type = $type ?? 'commit_content_text';
  factory CommitContentTextRequest.fromJson(Map<String, dynamic> json) => _$CommitContentTextRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? branchId;
 final  String contentKey;
 final  String? title;
 final  String sourceKind;
 final  String sourceRef;
 final  String mediaType;
 final  String? text;
 final  List<ContentTextCommitPartV1> _parts;
@JsonKey() List<ContentTextCommitPartV1> get parts {
  if (_parts is EqualUnmodifiableListView) return _parts;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_parts);
}

 final  String digestAlgorithm;
 final  String? digest;
 final  int? sizeBytes;
 final  Map<String, dynamic> _provenance;
 Map<String, dynamic> get provenance {
  if (_provenance is EqualUnmodifiableMapView) return _provenance;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_provenance);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of ContentServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$CommitContentTextRequestCopyWith<CommitContentTextRequest> get copyWith => _$CommitContentTextRequestCopyWithImpl<CommitContentTextRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$CommitContentTextRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is CommitContentTextRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.branchId, branchId) || other.branchId == branchId)&&(identical(other.contentKey, contentKey) || other.contentKey == contentKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.sourceKind, sourceKind) || other.sourceKind == sourceKind)&&(identical(other.sourceRef, sourceRef) || other.sourceRef == sourceRef)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.text, text) || other.text == text)&&const DeepCollectionEquality().equals(other._parts, _parts)&&(identical(other.digestAlgorithm, digestAlgorithm) || other.digestAlgorithm == digestAlgorithm)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&const DeepCollectionEquality().equals(other._provenance, _provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,actorId,branchId,contentKey,title,sourceKind,sourceRef,mediaType,text,const DeepCollectionEquality().hash(_parts),digestAlgorithm,digest,sizeBytes,const DeepCollectionEquality().hash(_provenance));

@override
String toString() {
  return 'ContentServiceRequest.commitContentText(requestId: $requestId, actorId: $actorId, branchId: $branchId, contentKey: $contentKey, title: $title, sourceKind: $sourceKind, sourceRef: $sourceRef, mediaType: $mediaType, text: $text, parts: $parts, digestAlgorithm: $digestAlgorithm, digest: $digest, sizeBytes: $sizeBytes, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class $CommitContentTextRequestCopyWith<$Res> implements $ContentServiceRequestCopyWith<$Res> {
  factory $CommitContentTextRequestCopyWith(CommitContentTextRequest value, $Res Function(CommitContentTextRequest) _then) = _$CommitContentTextRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? branchId, String contentKey, String? title, String sourceKind, String sourceRef, String mediaType, String? text, List<ContentTextCommitPartV1> parts, String digestAlgorithm, String? digest, int? sizeBytes, Map<String, dynamic> provenance
});




}
/// @nodoc
class _$CommitContentTextRequestCopyWithImpl<$Res>
    implements $CommitContentTextRequestCopyWith<$Res> {
  _$CommitContentTextRequestCopyWithImpl(this._self, this._then);

  final CommitContentTextRequest _self;
  final $Res Function(CommitContentTextRequest) _then;

/// Create a copy of ContentServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? actorId = freezed,Object? branchId = freezed,Object? contentKey = null,Object? title = freezed,Object? sourceKind = null,Object? sourceRef = null,Object? mediaType = null,Object? text = freezed,Object? parts = null,Object? digestAlgorithm = null,Object? digest = freezed,Object? sizeBytes = freezed,Object? provenance = null,}) {
  return _then(CommitContentTextRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,branchId: freezed == branchId ? _self.branchId : branchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,contentKey: null == contentKey ? _self.contentKey : contentKey // ignore: cast_nullable_to_non_nullable
as String,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,sourceKind: null == sourceKind ? _self.sourceKind : sourceKind // ignore: cast_nullable_to_non_nullable
as String,sourceRef: null == sourceRef ? _self.sourceRef : sourceRef // ignore: cast_nullable_to_non_nullable
as String,mediaType: null == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String,text: freezed == text ? _self.text : text // ignore: cast_nullable_to_non_nullable
as String?,parts: null == parts ? _self._parts : parts // ignore: cast_nullable_to_non_nullable
as List<ContentTextCommitPartV1>,digestAlgorithm: null == digestAlgorithm ? _self.digestAlgorithm : digestAlgorithm // ignore: cast_nullable_to_non_nullable
as String,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,provenance: null == provenance ? _self._provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class MaterializeContentPackageRequest implements ContentServiceRequest {
   MaterializeContentPackageRequest({@UuidValueConverter() this.requestId, @UuidValueConverter() this.actorId, @UuidValueConverter() this.branchId, required this.packageExport, final  String? $type}): $type = $type ?? 'materialize_content_package';
  factory MaterializeContentPackageRequest.fromJson(Map<String, dynamic> json) => _$MaterializeContentPackageRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? branchId;
 final  ContentPackageExportDocumentV1 packageExport;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of ContentServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$MaterializeContentPackageRequestCopyWith<MaterializeContentPackageRequest> get copyWith => _$MaterializeContentPackageRequestCopyWithImpl<MaterializeContentPackageRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$MaterializeContentPackageRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is MaterializeContentPackageRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.branchId, branchId) || other.branchId == branchId)&&(identical(other.packageExport, packageExport) || other.packageExport == packageExport));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,actorId,branchId,packageExport);

@override
String toString() {
  return 'ContentServiceRequest.materializeContentPackage(requestId: $requestId, actorId: $actorId, branchId: $branchId, packageExport: $packageExport)';
}


}

/// @nodoc
abstract mixin class $MaterializeContentPackageRequestCopyWith<$Res> implements $ContentServiceRequestCopyWith<$Res> {
  factory $MaterializeContentPackageRequestCopyWith(MaterializeContentPackageRequest value, $Res Function(MaterializeContentPackageRequest) _then) = _$MaterializeContentPackageRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? branchId, ContentPackageExportDocumentV1 packageExport
});


$ContentPackageExportDocumentV1CopyWith<$Res> get packageExport;

}
/// @nodoc
class _$MaterializeContentPackageRequestCopyWithImpl<$Res>
    implements $MaterializeContentPackageRequestCopyWith<$Res> {
  _$MaterializeContentPackageRequestCopyWithImpl(this._self, this._then);

  final MaterializeContentPackageRequest _self;
  final $Res Function(MaterializeContentPackageRequest) _then;

/// Create a copy of ContentServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? actorId = freezed,Object? branchId = freezed,Object? packageExport = null,}) {
  return _then(MaterializeContentPackageRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,branchId: freezed == branchId ? _self.branchId : branchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,packageExport: null == packageExport ? _self.packageExport : packageExport // ignore: cast_nullable_to_non_nullable
as ContentPackageExportDocumentV1,
  ));
}

/// Create a copy of ContentServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ContentPackageExportDocumentV1CopyWith<$Res> get packageExport {
  
  return $ContentPackageExportDocumentV1CopyWith<$Res>(_self.packageExport, (value) {
    return _then(_self.copyWith(packageExport: value));
  });
}
}

ContentServiceResponse _$ContentServiceResponseFromJson(
  Map<String, dynamic> json
) {
        switch (json['operation']) {
                  case 'resolve_content_text':
          return ResolveContentTextResponse.fromJson(
            json
          );
                case 'commit_content_text':
          return CommitContentTextResponse.fromJson(
            json
          );
                case 'materialize_content_package':
          return MaterializeContentPackageResponse.fromJson(
            json
          );
        
          default:
            throw CheckedFromJsonException(
  json,
  'operation',
  'ContentServiceResponse',
  'Invalid union type "${json['operation']}"!'
);
        }
      
}

/// @nodoc
mixin _$ContentServiceResponse {

@UuidValueConverter() UuidValue? get requestId; bool get success; String? get error; ContentOperationReceipt? get receipt;
/// Create a copy of ContentServiceResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ContentServiceResponseCopyWith<ContentServiceResponse> get copyWith => _$ContentServiceResponseCopyWithImpl<ContentServiceResponse>(this as ContentServiceResponse, _$identity);

  /// Serializes this ContentServiceResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ContentServiceResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.receipt, receipt) || other.receipt == receipt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,receipt);

@override
String toString() {
  return 'ContentServiceResponse(requestId: $requestId, success: $success, error: $error, receipt: $receipt)';
}


}

/// @nodoc
abstract mixin class $ContentServiceResponseCopyWith<$Res>  {
  factory $ContentServiceResponseCopyWith(ContentServiceResponse value, $Res Function(ContentServiceResponse) _then) = _$ContentServiceResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, ContentOperationReceipt? receipt
});


$ContentOperationReceiptCopyWith<$Res>? get receipt;

}
/// @nodoc
class _$ContentServiceResponseCopyWithImpl<$Res>
    implements $ContentServiceResponseCopyWith<$Res> {
  _$ContentServiceResponseCopyWithImpl(this._self, this._then);

  final ContentServiceResponse _self;
  final $Res Function(ContentServiceResponse) _then;

/// Create a copy of ContentServiceResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? receipt = freezed,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,receipt: freezed == receipt ? _self.receipt : receipt // ignore: cast_nullable_to_non_nullable
as ContentOperationReceipt?,
  ));
}
/// Create a copy of ContentServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ContentOperationReceiptCopyWith<$Res>? get receipt {
    if (_self.receipt == null) {
    return null;
  }

  return $ContentOperationReceiptCopyWith<$Res>(_self.receipt!, (value) {
    return _then(_self.copyWith(receipt: value));
  });
}
}


/// Adds pattern-matching-related methods to [ContentServiceResponse].
extension ContentServiceResponsePatterns on ContentServiceResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( ResolveContentTextResponse value)?  resolveContentText,TResult Function( CommitContentTextResponse value)?  commitContentText,TResult Function( MaterializeContentPackageResponse value)?  materializeContentPackage,required TResult orElse(),}){
final _that = this;
switch (_that) {
case ResolveContentTextResponse() when resolveContentText != null:
return resolveContentText(_that);case CommitContentTextResponse() when commitContentText != null:
return commitContentText(_that);case MaterializeContentPackageResponse() when materializeContentPackage != null:
return materializeContentPackage(_that);case _:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( ResolveContentTextResponse value)  resolveContentText,required TResult Function( CommitContentTextResponse value)  commitContentText,required TResult Function( MaterializeContentPackageResponse value)  materializeContentPackage,}){
final _that = this;
switch (_that) {
case ResolveContentTextResponse():
return resolveContentText(_that);case CommitContentTextResponse():
return commitContentText(_that);case MaterializeContentPackageResponse():
return materializeContentPackage(_that);case _:
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( ResolveContentTextResponse value)?  resolveContentText,TResult? Function( CommitContentTextResponse value)?  commitContentText,TResult? Function( MaterializeContentPackageResponse value)?  materializeContentPackage,}){
final _that = this;
switch (_that) {
case ResolveContentTextResponse() when resolveContentText != null:
return resolveContentText(_that);case CommitContentTextResponse() when commitContentText != null:
return commitContentText(_that);case MaterializeContentPackageResponse() when materializeContentPackage != null:
return materializeContentPackage(_that);case _:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  ContentOperationReceipt? receipt,  ContentTextResolutionV1? resolution)?  resolveContentText,TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  ContentOperationReceipt? receipt,  ContentTextCommitResultV1? commitResult)?  commitContentText,TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  ContentOperationReceipt? receipt,  ContentPackageMaterializationResultV1? materialization)?  materializeContentPackage,required TResult orElse(),}) {final _that = this;
switch (_that) {
case ResolveContentTextResponse() when resolveContentText != null:
return resolveContentText(_that.requestId,_that.success,_that.error,_that.receipt,_that.resolution);case CommitContentTextResponse() when commitContentText != null:
return commitContentText(_that.requestId,_that.success,_that.error,_that.receipt,_that.commitResult);case MaterializeContentPackageResponse() when materializeContentPackage != null:
return materializeContentPackage(_that.requestId,_that.success,_that.error,_that.receipt,_that.materialization);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  ContentOperationReceipt? receipt,  ContentTextResolutionV1? resolution)  resolveContentText,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  ContentOperationReceipt? receipt,  ContentTextCommitResultV1? commitResult)  commitContentText,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  ContentOperationReceipt? receipt,  ContentPackageMaterializationResultV1? materialization)  materializeContentPackage,}) {final _that = this;
switch (_that) {
case ResolveContentTextResponse():
return resolveContentText(_that.requestId,_that.success,_that.error,_that.receipt,_that.resolution);case CommitContentTextResponse():
return commitContentText(_that.requestId,_that.success,_that.error,_that.receipt,_that.commitResult);case MaterializeContentPackageResponse():
return materializeContentPackage(_that.requestId,_that.success,_that.error,_that.receipt,_that.materialization);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  ContentOperationReceipt? receipt,  ContentTextResolutionV1? resolution)?  resolveContentText,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  ContentOperationReceipt? receipt,  ContentTextCommitResultV1? commitResult)?  commitContentText,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  ContentOperationReceipt? receipt,  ContentPackageMaterializationResultV1? materialization)?  materializeContentPackage,}) {final _that = this;
switch (_that) {
case ResolveContentTextResponse() when resolveContentText != null:
return resolveContentText(_that.requestId,_that.success,_that.error,_that.receipt,_that.resolution);case CommitContentTextResponse() when commitContentText != null:
return commitContentText(_that.requestId,_that.success,_that.error,_that.receipt,_that.commitResult);case MaterializeContentPackageResponse() when materializeContentPackage != null:
return materializeContentPackage(_that.requestId,_that.success,_that.error,_that.receipt,_that.materialization);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class ResolveContentTextResponse implements ContentServiceResponse {
   ResolveContentTextResponse({@UuidValueConverter() this.requestId, required this.success, this.error, this.receipt, this.resolution, final  String? $type}): $type = $type ?? 'resolve_content_text';
  factory ResolveContentTextResponse.fromJson(Map<String, dynamic> json) => _$ResolveContentTextResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? error;
@override final  ContentOperationReceipt? receipt;
 final  ContentTextResolutionV1? resolution;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of ContentServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ResolveContentTextResponseCopyWith<ResolveContentTextResponse> get copyWith => _$ResolveContentTextResponseCopyWithImpl<ResolveContentTextResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ResolveContentTextResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ResolveContentTextResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.receipt, receipt) || other.receipt == receipt)&&(identical(other.resolution, resolution) || other.resolution == resolution));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,receipt,resolution);

@override
String toString() {
  return 'ContentServiceResponse.resolveContentText(requestId: $requestId, success: $success, error: $error, receipt: $receipt, resolution: $resolution)';
}


}

/// @nodoc
abstract mixin class $ResolveContentTextResponseCopyWith<$Res> implements $ContentServiceResponseCopyWith<$Res> {
  factory $ResolveContentTextResponseCopyWith(ResolveContentTextResponse value, $Res Function(ResolveContentTextResponse) _then) = _$ResolveContentTextResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, ContentOperationReceipt? receipt, ContentTextResolutionV1? resolution
});


@override $ContentOperationReceiptCopyWith<$Res>? get receipt;$ContentTextResolutionV1CopyWith<$Res>? get resolution;

}
/// @nodoc
class _$ResolveContentTextResponseCopyWithImpl<$Res>
    implements $ResolveContentTextResponseCopyWith<$Res> {
  _$ResolveContentTextResponseCopyWithImpl(this._self, this._then);

  final ResolveContentTextResponse _self;
  final $Res Function(ResolveContentTextResponse) _then;

/// Create a copy of ContentServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? receipt = freezed,Object? resolution = freezed,}) {
  return _then(ResolveContentTextResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,receipt: freezed == receipt ? _self.receipt : receipt // ignore: cast_nullable_to_non_nullable
as ContentOperationReceipt?,resolution: freezed == resolution ? _self.resolution : resolution // ignore: cast_nullable_to_non_nullable
as ContentTextResolutionV1?,
  ));
}

/// Create a copy of ContentServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ContentOperationReceiptCopyWith<$Res>? get receipt {
    if (_self.receipt == null) {
    return null;
  }

  return $ContentOperationReceiptCopyWith<$Res>(_self.receipt!, (value) {
    return _then(_self.copyWith(receipt: value));
  });
}/// Create a copy of ContentServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ContentTextResolutionV1CopyWith<$Res>? get resolution {
    if (_self.resolution == null) {
    return null;
  }

  return $ContentTextResolutionV1CopyWith<$Res>(_self.resolution!, (value) {
    return _then(_self.copyWith(resolution: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class CommitContentTextResponse implements ContentServiceResponse {
   CommitContentTextResponse({@UuidValueConverter() this.requestId, required this.success, this.error, this.receipt, this.commitResult, final  String? $type}): $type = $type ?? 'commit_content_text';
  factory CommitContentTextResponse.fromJson(Map<String, dynamic> json) => _$CommitContentTextResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? error;
@override final  ContentOperationReceipt? receipt;
 final  ContentTextCommitResultV1? commitResult;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of ContentServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$CommitContentTextResponseCopyWith<CommitContentTextResponse> get copyWith => _$CommitContentTextResponseCopyWithImpl<CommitContentTextResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$CommitContentTextResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is CommitContentTextResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.receipt, receipt) || other.receipt == receipt)&&(identical(other.commitResult, commitResult) || other.commitResult == commitResult));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,receipt,commitResult);

@override
String toString() {
  return 'ContentServiceResponse.commitContentText(requestId: $requestId, success: $success, error: $error, receipt: $receipt, commitResult: $commitResult)';
}


}

/// @nodoc
abstract mixin class $CommitContentTextResponseCopyWith<$Res> implements $ContentServiceResponseCopyWith<$Res> {
  factory $CommitContentTextResponseCopyWith(CommitContentTextResponse value, $Res Function(CommitContentTextResponse) _then) = _$CommitContentTextResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, ContentOperationReceipt? receipt, ContentTextCommitResultV1? commitResult
});


@override $ContentOperationReceiptCopyWith<$Res>? get receipt;$ContentTextCommitResultV1CopyWith<$Res>? get commitResult;

}
/// @nodoc
class _$CommitContentTextResponseCopyWithImpl<$Res>
    implements $CommitContentTextResponseCopyWith<$Res> {
  _$CommitContentTextResponseCopyWithImpl(this._self, this._then);

  final CommitContentTextResponse _self;
  final $Res Function(CommitContentTextResponse) _then;

/// Create a copy of ContentServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? receipt = freezed,Object? commitResult = freezed,}) {
  return _then(CommitContentTextResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,receipt: freezed == receipt ? _self.receipt : receipt // ignore: cast_nullable_to_non_nullable
as ContentOperationReceipt?,commitResult: freezed == commitResult ? _self.commitResult : commitResult // ignore: cast_nullable_to_non_nullable
as ContentTextCommitResultV1?,
  ));
}

/// Create a copy of ContentServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ContentOperationReceiptCopyWith<$Res>? get receipt {
    if (_self.receipt == null) {
    return null;
  }

  return $ContentOperationReceiptCopyWith<$Res>(_self.receipt!, (value) {
    return _then(_self.copyWith(receipt: value));
  });
}/// Create a copy of ContentServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ContentTextCommitResultV1CopyWith<$Res>? get commitResult {
    if (_self.commitResult == null) {
    return null;
  }

  return $ContentTextCommitResultV1CopyWith<$Res>(_self.commitResult!, (value) {
    return _then(_self.copyWith(commitResult: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class MaterializeContentPackageResponse implements ContentServiceResponse {
   MaterializeContentPackageResponse({@UuidValueConverter() this.requestId, required this.success, this.error, this.receipt, this.materialization, final  String? $type}): $type = $type ?? 'materialize_content_package';
  factory MaterializeContentPackageResponse.fromJson(Map<String, dynamic> json) => _$MaterializeContentPackageResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? error;
@override final  ContentOperationReceipt? receipt;
 final  ContentPackageMaterializationResultV1? materialization;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of ContentServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$MaterializeContentPackageResponseCopyWith<MaterializeContentPackageResponse> get copyWith => _$MaterializeContentPackageResponseCopyWithImpl<MaterializeContentPackageResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$MaterializeContentPackageResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is MaterializeContentPackageResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.receipt, receipt) || other.receipt == receipt)&&(identical(other.materialization, materialization) || other.materialization == materialization));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,receipt,materialization);

@override
String toString() {
  return 'ContentServiceResponse.materializeContentPackage(requestId: $requestId, success: $success, error: $error, receipt: $receipt, materialization: $materialization)';
}


}

/// @nodoc
abstract mixin class $MaterializeContentPackageResponseCopyWith<$Res> implements $ContentServiceResponseCopyWith<$Res> {
  factory $MaterializeContentPackageResponseCopyWith(MaterializeContentPackageResponse value, $Res Function(MaterializeContentPackageResponse) _then) = _$MaterializeContentPackageResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, ContentOperationReceipt? receipt, ContentPackageMaterializationResultV1? materialization
});


@override $ContentOperationReceiptCopyWith<$Res>? get receipt;$ContentPackageMaterializationResultV1CopyWith<$Res>? get materialization;

}
/// @nodoc
class _$MaterializeContentPackageResponseCopyWithImpl<$Res>
    implements $MaterializeContentPackageResponseCopyWith<$Res> {
  _$MaterializeContentPackageResponseCopyWithImpl(this._self, this._then);

  final MaterializeContentPackageResponse _self;
  final $Res Function(MaterializeContentPackageResponse) _then;

/// Create a copy of ContentServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? receipt = freezed,Object? materialization = freezed,}) {
  return _then(MaterializeContentPackageResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,receipt: freezed == receipt ? _self.receipt : receipt // ignore: cast_nullable_to_non_nullable
as ContentOperationReceipt?,materialization: freezed == materialization ? _self.materialization : materialization // ignore: cast_nullable_to_non_nullable
as ContentPackageMaterializationResultV1?,
  ));
}

/// Create a copy of ContentServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ContentOperationReceiptCopyWith<$Res>? get receipt {
    if (_self.receipt == null) {
    return null;
  }

  return $ContentOperationReceiptCopyWith<$Res>(_self.receipt!, (value) {
    return _then(_self.copyWith(receipt: value));
  });
}/// Create a copy of ContentServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ContentPackageMaterializationResultV1CopyWith<$Res>? get materialization {
    if (_self.materialization == null) {
    return null;
  }

  return $ContentPackageMaterializationResultV1CopyWith<$Res>(_self.materialization!, (value) {
    return _then(_self.copyWith(materialization: value));
  });
}
}

// dart format on
