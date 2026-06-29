// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'service_operation_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;
StorageServiceRequest _$StorageServiceRequestFromJson(
  Map<String, dynamic> json
) {
        switch (json['operation']) {
                  case 'register_blob':
          return RegisterStorageBlobRequest.fromJson(
            json
          );
                case 'describe_blob':
          return DescribeStorageBlobRequest.fromJson(
            json
          );
                case 'resolve_media':
          return ResolveStorageMediaRequest.fromJson(
            json
          );
        
          default:
            throw CheckedFromJsonException(
  json,
  'operation',
  'StorageServiceRequest',
  'Invalid union type "${json['operation']}"!'
);
        }
      
}

/// @nodoc
mixin _$StorageServiceRequest {

@UuidValueConverter() UuidValue? get requestId;@UuidValueConverter() UuidValue? get actorId;
/// Create a copy of StorageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$StorageServiceRequestCopyWith<StorageServiceRequest> get copyWith => _$StorageServiceRequestCopyWithImpl<StorageServiceRequest>(this as StorageServiceRequest, _$identity);

  /// Serializes this StorageServiceRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is StorageServiceRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.actorId, actorId) || other.actorId == actorId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,actorId);

@override
String toString() {
  return 'StorageServiceRequest(requestId: $requestId, actorId: $actorId)';
}


}

/// @nodoc
abstract mixin class $StorageServiceRequestCopyWith<$Res>  {
  factory $StorageServiceRequestCopyWith(StorageServiceRequest value, $Res Function(StorageServiceRequest) _then) = _$StorageServiceRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue? actorId
});




}
/// @nodoc
class _$StorageServiceRequestCopyWithImpl<$Res>
    implements $StorageServiceRequestCopyWith<$Res> {
  _$StorageServiceRequestCopyWithImpl(this._self, this._then);

  final StorageServiceRequest _self;
  final $Res Function(StorageServiceRequest) _then;

/// Create a copy of StorageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? actorId = freezed,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

}


/// Adds pattern-matching-related methods to [StorageServiceRequest].
extension StorageServiceRequestPatterns on StorageServiceRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( RegisterStorageBlobRequest value)?  registerBlob,TResult Function( DescribeStorageBlobRequest value)?  describeBlob,TResult Function( ResolveStorageMediaRequest value)?  resolveMedia,required TResult orElse(),}){
final _that = this;
switch (_that) {
case RegisterStorageBlobRequest() when registerBlob != null:
return registerBlob(_that);case DescribeStorageBlobRequest() when describeBlob != null:
return describeBlob(_that);case ResolveStorageMediaRequest() when resolveMedia != null:
return resolveMedia(_that);case _:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( RegisterStorageBlobRequest value)  registerBlob,required TResult Function( DescribeStorageBlobRequest value)  describeBlob,required TResult Function( ResolveStorageMediaRequest value)  resolveMedia,}){
final _that = this;
switch (_that) {
case RegisterStorageBlobRequest():
return registerBlob(_that);case DescribeStorageBlobRequest():
return describeBlob(_that);case ResolveStorageMediaRequest():
return resolveMedia(_that);case _:
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( RegisterStorageBlobRequest value)?  registerBlob,TResult? Function( DescribeStorageBlobRequest value)?  describeBlob,TResult? Function( ResolveStorageMediaRequest value)?  resolveMedia,}){
final _that = this;
switch (_that) {
case RegisterStorageBlobRequest() when registerBlob != null:
return registerBlob(_that);case DescribeStorageBlobRequest() when describeBlob != null:
return describeBlob(_that);case ResolveStorageMediaRequest() when resolveMedia != null:
return resolveMedia(_that);case _:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? objectId,  String sha,  String mimeType,  int sizeBytes, @UuidValueConverter()  UuidValue? bucketId,  String? objectKey,  String? pathLocal)?  registerBlob,TResult Function(@UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue objectId)?  describeBlob,TResult Function(@UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? actorId,  StorageMediaRef mediaRef,  bool requireOwnership,  bool includeHttpUrl,  String? preferredUriScheme,  String? filename, @JsonKey(fromJson: StorageMediaDispositionExtension.fromJson, toJson: StorageMediaDispositionExtension.toJson)  StorageMediaDisposition disposition)?  resolveMedia,required TResult orElse(),}) {final _that = this;
switch (_that) {
case RegisterStorageBlobRequest() when registerBlob != null:
return registerBlob(_that.requestId,_that.actorId,_that.objectId,_that.sha,_that.mimeType,_that.sizeBytes,_that.bucketId,_that.objectKey,_that.pathLocal);case DescribeStorageBlobRequest() when describeBlob != null:
return describeBlob(_that.requestId,_that.actorId,_that.objectId);case ResolveStorageMediaRequest() when resolveMedia != null:
return resolveMedia(_that.requestId,_that.actorId,_that.mediaRef,_that.requireOwnership,_that.includeHttpUrl,_that.preferredUriScheme,_that.filename,_that.disposition);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? objectId,  String sha,  String mimeType,  int sizeBytes, @UuidValueConverter()  UuidValue? bucketId,  String? objectKey,  String? pathLocal)  registerBlob,required TResult Function(@UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue objectId)  describeBlob,required TResult Function(@UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? actorId,  StorageMediaRef mediaRef,  bool requireOwnership,  bool includeHttpUrl,  String? preferredUriScheme,  String? filename, @JsonKey(fromJson: StorageMediaDispositionExtension.fromJson, toJson: StorageMediaDispositionExtension.toJson)  StorageMediaDisposition disposition)  resolveMedia,}) {final _that = this;
switch (_that) {
case RegisterStorageBlobRequest():
return registerBlob(_that.requestId,_that.actorId,_that.objectId,_that.sha,_that.mimeType,_that.sizeBytes,_that.bucketId,_that.objectKey,_that.pathLocal);case DescribeStorageBlobRequest():
return describeBlob(_that.requestId,_that.actorId,_that.objectId);case ResolveStorageMediaRequest():
return resolveMedia(_that.requestId,_that.actorId,_that.mediaRef,_that.requireOwnership,_that.includeHttpUrl,_that.preferredUriScheme,_that.filename,_that.disposition);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? objectId,  String sha,  String mimeType,  int sizeBytes, @UuidValueConverter()  UuidValue? bucketId,  String? objectKey,  String? pathLocal)?  registerBlob,TResult? Function(@UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue objectId)?  describeBlob,TResult? Function(@UuidValueConverter()  UuidValue? requestId, @UuidValueConverter()  UuidValue? actorId,  StorageMediaRef mediaRef,  bool requireOwnership,  bool includeHttpUrl,  String? preferredUriScheme,  String? filename, @JsonKey(fromJson: StorageMediaDispositionExtension.fromJson, toJson: StorageMediaDispositionExtension.toJson)  StorageMediaDisposition disposition)?  resolveMedia,}) {final _that = this;
switch (_that) {
case RegisterStorageBlobRequest() when registerBlob != null:
return registerBlob(_that.requestId,_that.actorId,_that.objectId,_that.sha,_that.mimeType,_that.sizeBytes,_that.bucketId,_that.objectKey,_that.pathLocal);case DescribeStorageBlobRequest() when describeBlob != null:
return describeBlob(_that.requestId,_that.actorId,_that.objectId);case ResolveStorageMediaRequest() when resolveMedia != null:
return resolveMedia(_that.requestId,_that.actorId,_that.mediaRef,_that.requireOwnership,_that.includeHttpUrl,_that.preferredUriScheme,_that.filename,_that.disposition);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class RegisterStorageBlobRequest implements StorageServiceRequest {
   RegisterStorageBlobRequest({@UuidValueConverter() this.requestId, @UuidValueConverter() this.actorId, @UuidValueConverter() this.objectId, required this.sha, required this.mimeType, required this.sizeBytes, @UuidValueConverter() this.bucketId, this.objectKey, this.pathLocal, final  String? $type}): $type = $type ?? 'register_blob';
  factory RegisterStorageBlobRequest.fromJson(Map<String, dynamic> json) => _$RegisterStorageBlobRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override@UuidValueConverter() final  UuidValue? actorId;
@UuidValueConverter() final  UuidValue? objectId;
 final  String sha;
 final  String mimeType;
 final  int sizeBytes;
@UuidValueConverter() final  UuidValue? bucketId;
 final  String? objectKey;
 final  String? pathLocal;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of StorageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$RegisterStorageBlobRequestCopyWith<RegisterStorageBlobRequest> get copyWith => _$RegisterStorageBlobRequestCopyWithImpl<RegisterStorageBlobRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$RegisterStorageBlobRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is RegisterStorageBlobRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.objectId, objectId) || other.objectId == objectId)&&(identical(other.sha, sha) || other.sha == sha)&&(identical(other.mimeType, mimeType) || other.mimeType == mimeType)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.bucketId, bucketId) || other.bucketId == bucketId)&&(identical(other.objectKey, objectKey) || other.objectKey == objectKey)&&(identical(other.pathLocal, pathLocal) || other.pathLocal == pathLocal));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,actorId,objectId,sha,mimeType,sizeBytes,bucketId,objectKey,pathLocal);

@override
String toString() {
  return 'StorageServiceRequest.registerBlob(requestId: $requestId, actorId: $actorId, objectId: $objectId, sha: $sha, mimeType: $mimeType, sizeBytes: $sizeBytes, bucketId: $bucketId, objectKey: $objectKey, pathLocal: $pathLocal)';
}


}

/// @nodoc
abstract mixin class $RegisterStorageBlobRequestCopyWith<$Res> implements $StorageServiceRequestCopyWith<$Res> {
  factory $RegisterStorageBlobRequestCopyWith(RegisterStorageBlobRequest value, $Res Function(RegisterStorageBlobRequest) _then) = _$RegisterStorageBlobRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? objectId, String sha, String mimeType, int sizeBytes,@UuidValueConverter() UuidValue? bucketId, String? objectKey, String? pathLocal
});




}
/// @nodoc
class _$RegisterStorageBlobRequestCopyWithImpl<$Res>
    implements $RegisterStorageBlobRequestCopyWith<$Res> {
  _$RegisterStorageBlobRequestCopyWithImpl(this._self, this._then);

  final RegisterStorageBlobRequest _self;
  final $Res Function(RegisterStorageBlobRequest) _then;

/// Create a copy of StorageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? actorId = freezed,Object? objectId = freezed,Object? sha = null,Object? mimeType = null,Object? sizeBytes = null,Object? bucketId = freezed,Object? objectKey = freezed,Object? pathLocal = freezed,}) {
  return _then(RegisterStorageBlobRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectId: freezed == objectId ? _self.objectId : objectId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sha: null == sha ? _self.sha : sha // ignore: cast_nullable_to_non_nullable
as String,mimeType: null == mimeType ? _self.mimeType : mimeType // ignore: cast_nullable_to_non_nullable
as String,sizeBytes: null == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int,bucketId: freezed == bucketId ? _self.bucketId : bucketId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectKey: freezed == objectKey ? _self.objectKey : objectKey // ignore: cast_nullable_to_non_nullable
as String?,pathLocal: freezed == pathLocal ? _self.pathLocal : pathLocal // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DescribeStorageBlobRequest implements StorageServiceRequest {
   DescribeStorageBlobRequest({@UuidValueConverter() this.requestId, @UuidValueConverter() this.actorId, @UuidValueConverter() required this.objectId, final  String? $type}): $type = $type ?? 'describe_blob';
  factory DescribeStorageBlobRequest.fromJson(Map<String, dynamic> json) => _$DescribeStorageBlobRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override@UuidValueConverter() final  UuidValue? actorId;
@UuidValueConverter() final  UuidValue objectId;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of StorageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DescribeStorageBlobRequestCopyWith<DescribeStorageBlobRequest> get copyWith => _$DescribeStorageBlobRequestCopyWithImpl<DescribeStorageBlobRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DescribeStorageBlobRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DescribeStorageBlobRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.objectId, objectId) || other.objectId == objectId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,actorId,objectId);

@override
String toString() {
  return 'StorageServiceRequest.describeBlob(requestId: $requestId, actorId: $actorId, objectId: $objectId)';
}


}

/// @nodoc
abstract mixin class $DescribeStorageBlobRequestCopyWith<$Res> implements $StorageServiceRequestCopyWith<$Res> {
  factory $DescribeStorageBlobRequestCopyWith(DescribeStorageBlobRequest value, $Res Function(DescribeStorageBlobRequest) _then) = _$DescribeStorageBlobRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue objectId
});




}
/// @nodoc
class _$DescribeStorageBlobRequestCopyWithImpl<$Res>
    implements $DescribeStorageBlobRequestCopyWith<$Res> {
  _$DescribeStorageBlobRequestCopyWithImpl(this._self, this._then);

  final DescribeStorageBlobRequest _self;
  final $Res Function(DescribeStorageBlobRequest) _then;

/// Create a copy of StorageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? actorId = freezed,Object? objectId = null,}) {
  return _then(DescribeStorageBlobRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectId: null == objectId ? _self.objectId : objectId // ignore: cast_nullable_to_non_nullable
as UuidValue,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class ResolveStorageMediaRequest implements StorageServiceRequest {
   ResolveStorageMediaRequest({@UuidValueConverter() this.requestId, @UuidValueConverter() this.actorId, required this.mediaRef, required this.requireOwnership, required this.includeHttpUrl, this.preferredUriScheme, this.filename, @JsonKey(fromJson: StorageMediaDispositionExtension.fromJson, toJson: StorageMediaDispositionExtension.toJson) required this.disposition, final  String? $type}): $type = $type ?? 'resolve_media';
  factory ResolveStorageMediaRequest.fromJson(Map<String, dynamic> json) => _$ResolveStorageMediaRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override@UuidValueConverter() final  UuidValue? actorId;
 final  StorageMediaRef mediaRef;
 final  bool requireOwnership;
 final  bool includeHttpUrl;
 final  String? preferredUriScheme;
 final  String? filename;
@JsonKey(fromJson: StorageMediaDispositionExtension.fromJson, toJson: StorageMediaDispositionExtension.toJson) final  StorageMediaDisposition disposition;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of StorageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ResolveStorageMediaRequestCopyWith<ResolveStorageMediaRequest> get copyWith => _$ResolveStorageMediaRequestCopyWithImpl<ResolveStorageMediaRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ResolveStorageMediaRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ResolveStorageMediaRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.mediaRef, mediaRef) || other.mediaRef == mediaRef)&&(identical(other.requireOwnership, requireOwnership) || other.requireOwnership == requireOwnership)&&(identical(other.includeHttpUrl, includeHttpUrl) || other.includeHttpUrl == includeHttpUrl)&&(identical(other.preferredUriScheme, preferredUriScheme) || other.preferredUriScheme == preferredUriScheme)&&(identical(other.filename, filename) || other.filename == filename)&&(identical(other.disposition, disposition) || other.disposition == disposition));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,actorId,mediaRef,requireOwnership,includeHttpUrl,preferredUriScheme,filename,disposition);

@override
String toString() {
  return 'StorageServiceRequest.resolveMedia(requestId: $requestId, actorId: $actorId, mediaRef: $mediaRef, requireOwnership: $requireOwnership, includeHttpUrl: $includeHttpUrl, preferredUriScheme: $preferredUriScheme, filename: $filename, disposition: $disposition)';
}


}

/// @nodoc
abstract mixin class $ResolveStorageMediaRequestCopyWith<$Res> implements $StorageServiceRequestCopyWith<$Res> {
  factory $ResolveStorageMediaRequestCopyWith(ResolveStorageMediaRequest value, $Res Function(ResolveStorageMediaRequest) _then) = _$ResolveStorageMediaRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId,@UuidValueConverter() UuidValue? actorId, StorageMediaRef mediaRef, bool requireOwnership, bool includeHttpUrl, String? preferredUriScheme, String? filename,@JsonKey(fromJson: StorageMediaDispositionExtension.fromJson, toJson: StorageMediaDispositionExtension.toJson) StorageMediaDisposition disposition
});


$StorageMediaRefCopyWith<$Res> get mediaRef;

}
/// @nodoc
class _$ResolveStorageMediaRequestCopyWithImpl<$Res>
    implements $ResolveStorageMediaRequestCopyWith<$Res> {
  _$ResolveStorageMediaRequestCopyWithImpl(this._self, this._then);

  final ResolveStorageMediaRequest _self;
  final $Res Function(ResolveStorageMediaRequest) _then;

/// Create a copy of StorageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? actorId = freezed,Object? mediaRef = null,Object? requireOwnership = null,Object? includeHttpUrl = null,Object? preferredUriScheme = freezed,Object? filename = freezed,Object? disposition = null,}) {
  return _then(ResolveStorageMediaRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,mediaRef: null == mediaRef ? _self.mediaRef : mediaRef // ignore: cast_nullable_to_non_nullable
as StorageMediaRef,requireOwnership: null == requireOwnership ? _self.requireOwnership : requireOwnership // ignore: cast_nullable_to_non_nullable
as bool,includeHttpUrl: null == includeHttpUrl ? _self.includeHttpUrl : includeHttpUrl // ignore: cast_nullable_to_non_nullable
as bool,preferredUriScheme: freezed == preferredUriScheme ? _self.preferredUriScheme : preferredUriScheme // ignore: cast_nullable_to_non_nullable
as String?,filename: freezed == filename ? _self.filename : filename // ignore: cast_nullable_to_non_nullable
as String?,disposition: null == disposition ? _self.disposition : disposition // ignore: cast_nullable_to_non_nullable
as StorageMediaDisposition,
  ));
}

/// Create a copy of StorageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$StorageMediaRefCopyWith<$Res> get mediaRef {
  
  return $StorageMediaRefCopyWith<$Res>(_self.mediaRef, (value) {
    return _then(_self.copyWith(mediaRef: value));
  });
}
}

StorageServiceResponse _$StorageServiceResponseFromJson(
  Map<String, dynamic> json
) {
        switch (json['operation']) {
                  case 'register_blob':
          return RegisterStorageBlobResponse.fromJson(
            json
          );
                case 'describe_blob':
          return DescribeStorageBlobResponse.fromJson(
            json
          );
                case 'resolve_media':
          return ResolveStorageMediaResponse.fromJson(
            json
          );
        
          default:
            throw CheckedFromJsonException(
  json,
  'operation',
  'StorageServiceResponse',
  'Invalid union type "${json['operation']}"!'
);
        }
      
}

/// @nodoc
mixin _$StorageServiceResponse {

@UuidValueConverter() UuidValue? get requestId; bool get success; String? get error; StorageOperationReceipt? get receipt; StorageBlobMetadata? get metadata;
/// Create a copy of StorageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$StorageServiceResponseCopyWith<StorageServiceResponse> get copyWith => _$StorageServiceResponseCopyWithImpl<StorageServiceResponse>(this as StorageServiceResponse, _$identity);

  /// Serializes this StorageServiceResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is StorageServiceResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.receipt, receipt) || other.receipt == receipt)&&(identical(other.metadata, metadata) || other.metadata == metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,receipt,metadata);

@override
String toString() {
  return 'StorageServiceResponse(requestId: $requestId, success: $success, error: $error, receipt: $receipt, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class $StorageServiceResponseCopyWith<$Res>  {
  factory $StorageServiceResponseCopyWith(StorageServiceResponse value, $Res Function(StorageServiceResponse) _then) = _$StorageServiceResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, StorageOperationReceipt? receipt, StorageBlobMetadata? metadata
});


$StorageOperationReceiptCopyWith<$Res>? get receipt;$StorageBlobMetadataCopyWith<$Res>? get metadata;

}
/// @nodoc
class _$StorageServiceResponseCopyWithImpl<$Res>
    implements $StorageServiceResponseCopyWith<$Res> {
  _$StorageServiceResponseCopyWithImpl(this._self, this._then);

  final StorageServiceResponse _self;
  final $Res Function(StorageServiceResponse) _then;

/// Create a copy of StorageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? receipt = freezed,Object? metadata = freezed,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,receipt: freezed == receipt ? _self.receipt : receipt // ignore: cast_nullable_to_non_nullable
as StorageOperationReceipt?,metadata: freezed == metadata ? _self.metadata : metadata // ignore: cast_nullable_to_non_nullable
as StorageBlobMetadata?,
  ));
}
/// Create a copy of StorageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$StorageOperationReceiptCopyWith<$Res>? get receipt {
    if (_self.receipt == null) {
    return null;
  }

  return $StorageOperationReceiptCopyWith<$Res>(_self.receipt!, (value) {
    return _then(_self.copyWith(receipt: value));
  });
}/// Create a copy of StorageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$StorageBlobMetadataCopyWith<$Res>? get metadata {
    if (_self.metadata == null) {
    return null;
  }

  return $StorageBlobMetadataCopyWith<$Res>(_self.metadata!, (value) {
    return _then(_self.copyWith(metadata: value));
  });
}
}


/// Adds pattern-matching-related methods to [StorageServiceResponse].
extension StorageServiceResponsePatterns on StorageServiceResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( RegisterStorageBlobResponse value)?  registerBlob,TResult Function( DescribeStorageBlobResponse value)?  describeBlob,TResult Function( ResolveStorageMediaResponse value)?  resolveMedia,required TResult orElse(),}){
final _that = this;
switch (_that) {
case RegisterStorageBlobResponse() when registerBlob != null:
return registerBlob(_that);case DescribeStorageBlobResponse() when describeBlob != null:
return describeBlob(_that);case ResolveStorageMediaResponse() when resolveMedia != null:
return resolveMedia(_that);case _:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( RegisterStorageBlobResponse value)  registerBlob,required TResult Function( DescribeStorageBlobResponse value)  describeBlob,required TResult Function( ResolveStorageMediaResponse value)  resolveMedia,}){
final _that = this;
switch (_that) {
case RegisterStorageBlobResponse():
return registerBlob(_that);case DescribeStorageBlobResponse():
return describeBlob(_that);case ResolveStorageMediaResponse():
return resolveMedia(_that);case _:
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( RegisterStorageBlobResponse value)?  registerBlob,TResult? Function( DescribeStorageBlobResponse value)?  describeBlob,TResult? Function( ResolveStorageMediaResponse value)?  resolveMedia,}){
final _that = this;
switch (_that) {
case RegisterStorageBlobResponse() when registerBlob != null:
return registerBlob(_that);case DescribeStorageBlobResponse() when describeBlob != null:
return describeBlob(_that);case ResolveStorageMediaResponse() when resolveMedia != null:
return resolveMedia(_that);case _:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  StorageOperationReceipt? receipt,  StorageBlobMetadata? metadata)?  registerBlob,TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  StorageOperationReceipt? receipt,  StorageBlobMetadata? metadata)?  describeBlob,TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  StorageOperationReceipt? receipt,  StorageBlobMetadata? metadata,  StorageMediaResolution? resolution)?  resolveMedia,required TResult orElse(),}) {final _that = this;
switch (_that) {
case RegisterStorageBlobResponse() when registerBlob != null:
return registerBlob(_that.requestId,_that.success,_that.error,_that.receipt,_that.metadata);case DescribeStorageBlobResponse() when describeBlob != null:
return describeBlob(_that.requestId,_that.success,_that.error,_that.receipt,_that.metadata);case ResolveStorageMediaResponse() when resolveMedia != null:
return resolveMedia(_that.requestId,_that.success,_that.error,_that.receipt,_that.metadata,_that.resolution);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  StorageOperationReceipt? receipt,  StorageBlobMetadata? metadata)  registerBlob,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  StorageOperationReceipt? receipt,  StorageBlobMetadata? metadata)  describeBlob,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  StorageOperationReceipt? receipt,  StorageBlobMetadata? metadata,  StorageMediaResolution? resolution)  resolveMedia,}) {final _that = this;
switch (_that) {
case RegisterStorageBlobResponse():
return registerBlob(_that.requestId,_that.success,_that.error,_that.receipt,_that.metadata);case DescribeStorageBlobResponse():
return describeBlob(_that.requestId,_that.success,_that.error,_that.receipt,_that.metadata);case ResolveStorageMediaResponse():
return resolveMedia(_that.requestId,_that.success,_that.error,_that.receipt,_that.metadata,_that.resolution);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  StorageOperationReceipt? receipt,  StorageBlobMetadata? metadata)?  registerBlob,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  StorageOperationReceipt? receipt,  StorageBlobMetadata? metadata)?  describeBlob,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? error,  StorageOperationReceipt? receipt,  StorageBlobMetadata? metadata,  StorageMediaResolution? resolution)?  resolveMedia,}) {final _that = this;
switch (_that) {
case RegisterStorageBlobResponse() when registerBlob != null:
return registerBlob(_that.requestId,_that.success,_that.error,_that.receipt,_that.metadata);case DescribeStorageBlobResponse() when describeBlob != null:
return describeBlob(_that.requestId,_that.success,_that.error,_that.receipt,_that.metadata);case ResolveStorageMediaResponse() when resolveMedia != null:
return resolveMedia(_that.requestId,_that.success,_that.error,_that.receipt,_that.metadata,_that.resolution);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class RegisterStorageBlobResponse implements StorageServiceResponse {
   RegisterStorageBlobResponse({@UuidValueConverter() this.requestId, required this.success, this.error, this.receipt, this.metadata, final  String? $type}): $type = $type ?? 'register_blob';
  factory RegisterStorageBlobResponse.fromJson(Map<String, dynamic> json) => _$RegisterStorageBlobResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? error;
@override final  StorageOperationReceipt? receipt;
@override final  StorageBlobMetadata? metadata;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of StorageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$RegisterStorageBlobResponseCopyWith<RegisterStorageBlobResponse> get copyWith => _$RegisterStorageBlobResponseCopyWithImpl<RegisterStorageBlobResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$RegisterStorageBlobResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is RegisterStorageBlobResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.receipt, receipt) || other.receipt == receipt)&&(identical(other.metadata, metadata) || other.metadata == metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,receipt,metadata);

@override
String toString() {
  return 'StorageServiceResponse.registerBlob(requestId: $requestId, success: $success, error: $error, receipt: $receipt, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class $RegisterStorageBlobResponseCopyWith<$Res> implements $StorageServiceResponseCopyWith<$Res> {
  factory $RegisterStorageBlobResponseCopyWith(RegisterStorageBlobResponse value, $Res Function(RegisterStorageBlobResponse) _then) = _$RegisterStorageBlobResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, StorageOperationReceipt? receipt, StorageBlobMetadata? metadata
});


@override $StorageOperationReceiptCopyWith<$Res>? get receipt;@override $StorageBlobMetadataCopyWith<$Res>? get metadata;

}
/// @nodoc
class _$RegisterStorageBlobResponseCopyWithImpl<$Res>
    implements $RegisterStorageBlobResponseCopyWith<$Res> {
  _$RegisterStorageBlobResponseCopyWithImpl(this._self, this._then);

  final RegisterStorageBlobResponse _self;
  final $Res Function(RegisterStorageBlobResponse) _then;

/// Create a copy of StorageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? receipt = freezed,Object? metadata = freezed,}) {
  return _then(RegisterStorageBlobResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,receipt: freezed == receipt ? _self.receipt : receipt // ignore: cast_nullable_to_non_nullable
as StorageOperationReceipt?,metadata: freezed == metadata ? _self.metadata : metadata // ignore: cast_nullable_to_non_nullable
as StorageBlobMetadata?,
  ));
}

/// Create a copy of StorageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$StorageOperationReceiptCopyWith<$Res>? get receipt {
    if (_self.receipt == null) {
    return null;
  }

  return $StorageOperationReceiptCopyWith<$Res>(_self.receipt!, (value) {
    return _then(_self.copyWith(receipt: value));
  });
}/// Create a copy of StorageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$StorageBlobMetadataCopyWith<$Res>? get metadata {
    if (_self.metadata == null) {
    return null;
  }

  return $StorageBlobMetadataCopyWith<$Res>(_self.metadata!, (value) {
    return _then(_self.copyWith(metadata: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DescribeStorageBlobResponse implements StorageServiceResponse {
   DescribeStorageBlobResponse({@UuidValueConverter() this.requestId, required this.success, this.error, this.receipt, this.metadata, final  String? $type}): $type = $type ?? 'describe_blob';
  factory DescribeStorageBlobResponse.fromJson(Map<String, dynamic> json) => _$DescribeStorageBlobResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? error;
@override final  StorageOperationReceipt? receipt;
@override final  StorageBlobMetadata? metadata;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of StorageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DescribeStorageBlobResponseCopyWith<DescribeStorageBlobResponse> get copyWith => _$DescribeStorageBlobResponseCopyWithImpl<DescribeStorageBlobResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DescribeStorageBlobResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DescribeStorageBlobResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.receipt, receipt) || other.receipt == receipt)&&(identical(other.metadata, metadata) || other.metadata == metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,receipt,metadata);

@override
String toString() {
  return 'StorageServiceResponse.describeBlob(requestId: $requestId, success: $success, error: $error, receipt: $receipt, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class $DescribeStorageBlobResponseCopyWith<$Res> implements $StorageServiceResponseCopyWith<$Res> {
  factory $DescribeStorageBlobResponseCopyWith(DescribeStorageBlobResponse value, $Res Function(DescribeStorageBlobResponse) _then) = _$DescribeStorageBlobResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, StorageOperationReceipt? receipt, StorageBlobMetadata? metadata
});


@override $StorageOperationReceiptCopyWith<$Res>? get receipt;@override $StorageBlobMetadataCopyWith<$Res>? get metadata;

}
/// @nodoc
class _$DescribeStorageBlobResponseCopyWithImpl<$Res>
    implements $DescribeStorageBlobResponseCopyWith<$Res> {
  _$DescribeStorageBlobResponseCopyWithImpl(this._self, this._then);

  final DescribeStorageBlobResponse _self;
  final $Res Function(DescribeStorageBlobResponse) _then;

/// Create a copy of StorageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? receipt = freezed,Object? metadata = freezed,}) {
  return _then(DescribeStorageBlobResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,receipt: freezed == receipt ? _self.receipt : receipt // ignore: cast_nullable_to_non_nullable
as StorageOperationReceipt?,metadata: freezed == metadata ? _self.metadata : metadata // ignore: cast_nullable_to_non_nullable
as StorageBlobMetadata?,
  ));
}

/// Create a copy of StorageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$StorageOperationReceiptCopyWith<$Res>? get receipt {
    if (_self.receipt == null) {
    return null;
  }

  return $StorageOperationReceiptCopyWith<$Res>(_self.receipt!, (value) {
    return _then(_self.copyWith(receipt: value));
  });
}/// Create a copy of StorageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$StorageBlobMetadataCopyWith<$Res>? get metadata {
    if (_self.metadata == null) {
    return null;
  }

  return $StorageBlobMetadataCopyWith<$Res>(_self.metadata!, (value) {
    return _then(_self.copyWith(metadata: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class ResolveStorageMediaResponse implements StorageServiceResponse {
   ResolveStorageMediaResponse({@UuidValueConverter() this.requestId, required this.success, this.error, this.receipt, this.metadata, this.resolution, final  String? $type}): $type = $type ?? 'resolve_media';
  factory ResolveStorageMediaResponse.fromJson(Map<String, dynamic> json) => _$ResolveStorageMediaResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? error;
@override final  StorageOperationReceipt? receipt;
@override final  StorageBlobMetadata? metadata;
 final  StorageMediaResolution? resolution;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of StorageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ResolveStorageMediaResponseCopyWith<ResolveStorageMediaResponse> get copyWith => _$ResolveStorageMediaResponseCopyWithImpl<ResolveStorageMediaResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ResolveStorageMediaResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ResolveStorageMediaResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.receipt, receipt) || other.receipt == receipt)&&(identical(other.metadata, metadata) || other.metadata == metadata)&&(identical(other.resolution, resolution) || other.resolution == resolution));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,error,receipt,metadata,resolution);

@override
String toString() {
  return 'StorageServiceResponse.resolveMedia(requestId: $requestId, success: $success, error: $error, receipt: $receipt, metadata: $metadata, resolution: $resolution)';
}


}

/// @nodoc
abstract mixin class $ResolveStorageMediaResponseCopyWith<$Res> implements $StorageServiceResponseCopyWith<$Res> {
  factory $ResolveStorageMediaResponseCopyWith(ResolveStorageMediaResponse value, $Res Function(ResolveStorageMediaResponse) _then) = _$ResolveStorageMediaResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? error, StorageOperationReceipt? receipt, StorageBlobMetadata? metadata, StorageMediaResolution? resolution
});


@override $StorageOperationReceiptCopyWith<$Res>? get receipt;@override $StorageBlobMetadataCopyWith<$Res>? get metadata;$StorageMediaResolutionCopyWith<$Res>? get resolution;

}
/// @nodoc
class _$ResolveStorageMediaResponseCopyWithImpl<$Res>
    implements $ResolveStorageMediaResponseCopyWith<$Res> {
  _$ResolveStorageMediaResponseCopyWithImpl(this._self, this._then);

  final ResolveStorageMediaResponse _self;
  final $Res Function(ResolveStorageMediaResponse) _then;

/// Create a copy of StorageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? error = freezed,Object? receipt = freezed,Object? metadata = freezed,Object? resolution = freezed,}) {
  return _then(ResolveStorageMediaResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,receipt: freezed == receipt ? _self.receipt : receipt // ignore: cast_nullable_to_non_nullable
as StorageOperationReceipt?,metadata: freezed == metadata ? _self.metadata : metadata // ignore: cast_nullable_to_non_nullable
as StorageBlobMetadata?,resolution: freezed == resolution ? _self.resolution : resolution // ignore: cast_nullable_to_non_nullable
as StorageMediaResolution?,
  ));
}

/// Create a copy of StorageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$StorageOperationReceiptCopyWith<$Res>? get receipt {
    if (_self.receipt == null) {
    return null;
  }

  return $StorageOperationReceiptCopyWith<$Res>(_self.receipt!, (value) {
    return _then(_self.copyWith(receipt: value));
  });
}/// Create a copy of StorageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$StorageBlobMetadataCopyWith<$Res>? get metadata {
    if (_self.metadata == null) {
    return null;
  }

  return $StorageBlobMetadataCopyWith<$Res>(_self.metadata!, (value) {
    return _then(_self.copyWith(metadata: value));
  });
}/// Create a copy of StorageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$StorageMediaResolutionCopyWith<$Res>? get resolution {
    if (_self.resolution == null) {
    return null;
  }

  return $StorageMediaResolutionCopyWith<$Res>(_self.resolution!, (value) {
    return _then(_self.copyWith(resolution: value));
  });
}
}

// dart format on
