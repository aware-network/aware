// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'artifact_authority_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;
HubArtifactAuthorityRequest _$HubArtifactAuthorityRequestFromJson(
  Map<String, dynamic> json
) {
        switch (json['operation']) {
                  case 'publish_hub_artifact':
          return PublishHubArtifactRequest.fromJson(
            json
          );
                case 'resolve_hub_artifact':
          return ResolveHubArtifactRequest.fromJson(
            json
          );
        
          default:
            throw CheckedFromJsonException(
  json,
  'operation',
  'HubArtifactAuthorityRequest',
  'Invalid union type "${json['operation']}"!'
);
        }
      
}

/// @nodoc
mixin _$HubArtifactAuthorityRequest {

@UuidValueConverter() UuidValue? get requestId; String get artifactFamily; String get artifactKey; String? get revisionId; String get channel; String? get authorityBaseUrl; String? get indexUrl;
/// Create a copy of HubArtifactAuthorityRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$HubArtifactAuthorityRequestCopyWith<HubArtifactAuthorityRequest> get copyWith => _$HubArtifactAuthorityRequestCopyWithImpl<HubArtifactAuthorityRequest>(this as HubArtifactAuthorityRequest, _$identity);

  /// Serializes this HubArtifactAuthorityRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is HubArtifactAuthorityRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.artifactFamily, artifactFamily) || other.artifactFamily == artifactFamily)&&(identical(other.artifactKey, artifactKey) || other.artifactKey == artifactKey)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.authorityBaseUrl, authorityBaseUrl) || other.authorityBaseUrl == authorityBaseUrl)&&(identical(other.indexUrl, indexUrl) || other.indexUrl == indexUrl));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,artifactFamily,artifactKey,revisionId,channel,authorityBaseUrl,indexUrl);

@override
String toString() {
  return 'HubArtifactAuthorityRequest(requestId: $requestId, artifactFamily: $artifactFamily, artifactKey: $artifactKey, revisionId: $revisionId, channel: $channel, authorityBaseUrl: $authorityBaseUrl, indexUrl: $indexUrl)';
}


}

/// @nodoc
abstract mixin class $HubArtifactAuthorityRequestCopyWith<$Res>  {
  factory $HubArtifactAuthorityRequestCopyWith(HubArtifactAuthorityRequest value, $Res Function(HubArtifactAuthorityRequest) _then) = _$HubArtifactAuthorityRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, String artifactFamily, String artifactKey, String revisionId, String channel, String? authorityBaseUrl, String? indexUrl
});




}
/// @nodoc
class _$HubArtifactAuthorityRequestCopyWithImpl<$Res>
    implements $HubArtifactAuthorityRequestCopyWith<$Res> {
  _$HubArtifactAuthorityRequestCopyWithImpl(this._self, this._then);

  final HubArtifactAuthorityRequest _self;
  final $Res Function(HubArtifactAuthorityRequest) _then;

/// Create a copy of HubArtifactAuthorityRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? artifactFamily = null,Object? artifactKey = null,Object? revisionId = null,Object? channel = null,Object? authorityBaseUrl = freezed,Object? indexUrl = freezed,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,artifactFamily: null == artifactFamily ? _self.artifactFamily : artifactFamily // ignore: cast_nullable_to_non_nullable
as String,artifactKey: null == artifactKey ? _self.artifactKey : artifactKey // ignore: cast_nullable_to_non_nullable
as String,revisionId: null == revisionId ? _self.revisionId! : revisionId // ignore: cast_nullable_to_non_nullable
as String,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,authorityBaseUrl: freezed == authorityBaseUrl ? _self.authorityBaseUrl : authorityBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,indexUrl: freezed == indexUrl ? _self.indexUrl : indexUrl // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [HubArtifactAuthorityRequest].
extension HubArtifactAuthorityRequestPatterns on HubArtifactAuthorityRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( PublishHubArtifactRequest value)?  publishHubArtifact,TResult Function( ResolveHubArtifactRequest value)?  resolveHubArtifact,required TResult orElse(),}){
final _that = this;
switch (_that) {
case PublishHubArtifactRequest() when publishHubArtifact != null:
return publishHubArtifact(_that);case ResolveHubArtifactRequest() when resolveHubArtifact != null:
return resolveHubArtifact(_that);case _:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( PublishHubArtifactRequest value)  publishHubArtifact,required TResult Function( ResolveHubArtifactRequest value)  resolveHubArtifact,}){
final _that = this;
switch (_that) {
case PublishHubArtifactRequest():
return publishHubArtifact(_that);case ResolveHubArtifactRequest():
return resolveHubArtifact(_that);case _:
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( PublishHubArtifactRequest value)?  publishHubArtifact,TResult? Function( ResolveHubArtifactRequest value)?  resolveHubArtifact,}){
final _that = this;
switch (_that) {
case PublishHubArtifactRequest() when publishHubArtifact != null:
return publishHubArtifact(_that);case ResolveHubArtifactRequest() when resolveHubArtifact != null:
return resolveHubArtifact(_that);case _:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  String artifactFamily,  String artifactKey,  String revisionId,  String channel,  String? authorityBaseUrl,  String? indexUrl,  String? payloadUrl,  String? payloadSha256,  int? payloadSizeBytes,  String? payloadMediaType,  String? payloadContract,  Map<String, dynamic>? payloadJson,  String? payloadBytesBase64,  String? payloadSourceUrl,  String? selectorKey,  String? targetRef,  HubArtifactProducerProvenance? producer,  String? publisherExecutionId,  String? idempotencyKey,  String? publishedAtUtc,  Map<String, dynamic> metadata)?  publishHubArtifact,TResult Function(@UuidValueConverter()  UuidValue? requestId,  String artifactFamily,  String artifactKey,  String channel,  String? revisionId,  String? authorityBaseUrl,  String? indexUrl)?  resolveHubArtifact,required TResult orElse(),}) {final _that = this;
switch (_that) {
case PublishHubArtifactRequest() when publishHubArtifact != null:
return publishHubArtifact(_that.requestId,_that.artifactFamily,_that.artifactKey,_that.revisionId,_that.channel,_that.authorityBaseUrl,_that.indexUrl,_that.payloadUrl,_that.payloadSha256,_that.payloadSizeBytes,_that.payloadMediaType,_that.payloadContract,_that.payloadJson,_that.payloadBytesBase64,_that.payloadSourceUrl,_that.selectorKey,_that.targetRef,_that.producer,_that.publisherExecutionId,_that.idempotencyKey,_that.publishedAtUtc,_that.metadata);case ResolveHubArtifactRequest() when resolveHubArtifact != null:
return resolveHubArtifact(_that.requestId,_that.artifactFamily,_that.artifactKey,_that.channel,_that.revisionId,_that.authorityBaseUrl,_that.indexUrl);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  String artifactFamily,  String artifactKey,  String revisionId,  String channel,  String? authorityBaseUrl,  String? indexUrl,  String? payloadUrl,  String? payloadSha256,  int? payloadSizeBytes,  String? payloadMediaType,  String? payloadContract,  Map<String, dynamic>? payloadJson,  String? payloadBytesBase64,  String? payloadSourceUrl,  String? selectorKey,  String? targetRef,  HubArtifactProducerProvenance? producer,  String? publisherExecutionId,  String? idempotencyKey,  String? publishedAtUtc,  Map<String, dynamic> metadata)  publishHubArtifact,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  String artifactFamily,  String artifactKey,  String channel,  String? revisionId,  String? authorityBaseUrl,  String? indexUrl)  resolveHubArtifact,}) {final _that = this;
switch (_that) {
case PublishHubArtifactRequest():
return publishHubArtifact(_that.requestId,_that.artifactFamily,_that.artifactKey,_that.revisionId,_that.channel,_that.authorityBaseUrl,_that.indexUrl,_that.payloadUrl,_that.payloadSha256,_that.payloadSizeBytes,_that.payloadMediaType,_that.payloadContract,_that.payloadJson,_that.payloadBytesBase64,_that.payloadSourceUrl,_that.selectorKey,_that.targetRef,_that.producer,_that.publisherExecutionId,_that.idempotencyKey,_that.publishedAtUtc,_that.metadata);case ResolveHubArtifactRequest():
return resolveHubArtifact(_that.requestId,_that.artifactFamily,_that.artifactKey,_that.channel,_that.revisionId,_that.authorityBaseUrl,_that.indexUrl);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  String artifactFamily,  String artifactKey,  String revisionId,  String channel,  String? authorityBaseUrl,  String? indexUrl,  String? payloadUrl,  String? payloadSha256,  int? payloadSizeBytes,  String? payloadMediaType,  String? payloadContract,  Map<String, dynamic>? payloadJson,  String? payloadBytesBase64,  String? payloadSourceUrl,  String? selectorKey,  String? targetRef,  HubArtifactProducerProvenance? producer,  String? publisherExecutionId,  String? idempotencyKey,  String? publishedAtUtc,  Map<String, dynamic> metadata)?  publishHubArtifact,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  String artifactFamily,  String artifactKey,  String channel,  String? revisionId,  String? authorityBaseUrl,  String? indexUrl)?  resolveHubArtifact,}) {final _that = this;
switch (_that) {
case PublishHubArtifactRequest() when publishHubArtifact != null:
return publishHubArtifact(_that.requestId,_that.artifactFamily,_that.artifactKey,_that.revisionId,_that.channel,_that.authorityBaseUrl,_that.indexUrl,_that.payloadUrl,_that.payloadSha256,_that.payloadSizeBytes,_that.payloadMediaType,_that.payloadContract,_that.payloadJson,_that.payloadBytesBase64,_that.payloadSourceUrl,_that.selectorKey,_that.targetRef,_that.producer,_that.publisherExecutionId,_that.idempotencyKey,_that.publishedAtUtc,_that.metadata);case ResolveHubArtifactRequest() when resolveHubArtifact != null:
return resolveHubArtifact(_that.requestId,_that.artifactFamily,_that.artifactKey,_that.channel,_that.revisionId,_that.authorityBaseUrl,_that.indexUrl);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class PublishHubArtifactRequest implements HubArtifactAuthorityRequest {
   PublishHubArtifactRequest({@UuidValueConverter() this.requestId, required this.artifactFamily, required this.artifactKey, required this.revisionId, required this.channel, this.authorityBaseUrl, this.indexUrl, this.payloadUrl, this.payloadSha256, this.payloadSizeBytes, this.payloadMediaType, this.payloadContract, final  Map<String, dynamic>? payloadJson, this.payloadBytesBase64, this.payloadSourceUrl, this.selectorKey, this.targetRef, this.producer, this.publisherExecutionId, this.idempotencyKey, this.publishedAtUtc, required final  Map<String, dynamic> metadata, final  String? $type}): _payloadJson = payloadJson,_metadata = metadata,$type = $type ?? 'publish_hub_artifact';
  factory PublishHubArtifactRequest.fromJson(Map<String, dynamic> json) => _$PublishHubArtifactRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  String artifactFamily;
@override final  String artifactKey;
@override final  String revisionId;
@override final  String channel;
@override final  String? authorityBaseUrl;
@override final  String? indexUrl;
 final  String? payloadUrl;
 final  String? payloadSha256;
 final  int? payloadSizeBytes;
 final  String? payloadMediaType;
 final  String? payloadContract;
 final  Map<String, dynamic>? _payloadJson;
 Map<String, dynamic>? get payloadJson {
  final value = _payloadJson;
  if (value == null) return null;
  if (_payloadJson is EqualUnmodifiableMapView) return _payloadJson;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(value);
}

 final  String? payloadBytesBase64;
 final  String? payloadSourceUrl;
 final  String? selectorKey;
 final  String? targetRef;
 final  HubArtifactProducerProvenance? producer;
 final  String? publisherExecutionId;
 final  String? idempotencyKey;
 final  String? publishedAtUtc;
 final  Map<String, dynamic> _metadata;
 Map<String, dynamic> get metadata {
  if (_metadata is EqualUnmodifiableMapView) return _metadata;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_metadata);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of HubArtifactAuthorityRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$PublishHubArtifactRequestCopyWith<PublishHubArtifactRequest> get copyWith => _$PublishHubArtifactRequestCopyWithImpl<PublishHubArtifactRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$PublishHubArtifactRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is PublishHubArtifactRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.artifactFamily, artifactFamily) || other.artifactFamily == artifactFamily)&&(identical(other.artifactKey, artifactKey) || other.artifactKey == artifactKey)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.authorityBaseUrl, authorityBaseUrl) || other.authorityBaseUrl == authorityBaseUrl)&&(identical(other.indexUrl, indexUrl) || other.indexUrl == indexUrl)&&(identical(other.payloadUrl, payloadUrl) || other.payloadUrl == payloadUrl)&&(identical(other.payloadSha256, payloadSha256) || other.payloadSha256 == payloadSha256)&&(identical(other.payloadSizeBytes, payloadSizeBytes) || other.payloadSizeBytes == payloadSizeBytes)&&(identical(other.payloadMediaType, payloadMediaType) || other.payloadMediaType == payloadMediaType)&&(identical(other.payloadContract, payloadContract) || other.payloadContract == payloadContract)&&const DeepCollectionEquality().equals(other._payloadJson, _payloadJson)&&(identical(other.payloadBytesBase64, payloadBytesBase64) || other.payloadBytesBase64 == payloadBytesBase64)&&(identical(other.payloadSourceUrl, payloadSourceUrl) || other.payloadSourceUrl == payloadSourceUrl)&&(identical(other.selectorKey, selectorKey) || other.selectorKey == selectorKey)&&(identical(other.targetRef, targetRef) || other.targetRef == targetRef)&&(identical(other.producer, producer) || other.producer == producer)&&(identical(other.publisherExecutionId, publisherExecutionId) || other.publisherExecutionId == publisherExecutionId)&&(identical(other.idempotencyKey, idempotencyKey) || other.idempotencyKey == idempotencyKey)&&(identical(other.publishedAtUtc, publishedAtUtc) || other.publishedAtUtc == publishedAtUtc)&&const DeepCollectionEquality().equals(other._metadata, _metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,requestId,artifactFamily,artifactKey,revisionId,channel,authorityBaseUrl,indexUrl,payloadUrl,payloadSha256,payloadSizeBytes,payloadMediaType,payloadContract,const DeepCollectionEquality().hash(_payloadJson),payloadBytesBase64,payloadSourceUrl,selectorKey,targetRef,producer,publisherExecutionId,idempotencyKey,publishedAtUtc,const DeepCollectionEquality().hash(_metadata)]);

@override
String toString() {
  return 'HubArtifactAuthorityRequest.publishHubArtifact(requestId: $requestId, artifactFamily: $artifactFamily, artifactKey: $artifactKey, revisionId: $revisionId, channel: $channel, authorityBaseUrl: $authorityBaseUrl, indexUrl: $indexUrl, payloadUrl: $payloadUrl, payloadSha256: $payloadSha256, payloadSizeBytes: $payloadSizeBytes, payloadMediaType: $payloadMediaType, payloadContract: $payloadContract, payloadJson: $payloadJson, payloadBytesBase64: $payloadBytesBase64, payloadSourceUrl: $payloadSourceUrl, selectorKey: $selectorKey, targetRef: $targetRef, producer: $producer, publisherExecutionId: $publisherExecutionId, idempotencyKey: $idempotencyKey, publishedAtUtc: $publishedAtUtc, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class $PublishHubArtifactRequestCopyWith<$Res> implements $HubArtifactAuthorityRequestCopyWith<$Res> {
  factory $PublishHubArtifactRequestCopyWith(PublishHubArtifactRequest value, $Res Function(PublishHubArtifactRequest) _then) = _$PublishHubArtifactRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, String artifactFamily, String artifactKey, String revisionId, String channel, String? authorityBaseUrl, String? indexUrl, String? payloadUrl, String? payloadSha256, int? payloadSizeBytes, String? payloadMediaType, String? payloadContract, Map<String, dynamic>? payloadJson, String? payloadBytesBase64, String? payloadSourceUrl, String? selectorKey, String? targetRef, HubArtifactProducerProvenance? producer, String? publisherExecutionId, String? idempotencyKey, String? publishedAtUtc, Map<String, dynamic> metadata
});


$HubArtifactProducerProvenanceCopyWith<$Res>? get producer;

}
/// @nodoc
class _$PublishHubArtifactRequestCopyWithImpl<$Res>
    implements $PublishHubArtifactRequestCopyWith<$Res> {
  _$PublishHubArtifactRequestCopyWithImpl(this._self, this._then);

  final PublishHubArtifactRequest _self;
  final $Res Function(PublishHubArtifactRequest) _then;

/// Create a copy of HubArtifactAuthorityRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? artifactFamily = null,Object? artifactKey = null,Object? revisionId = null,Object? channel = null,Object? authorityBaseUrl = freezed,Object? indexUrl = freezed,Object? payloadUrl = freezed,Object? payloadSha256 = freezed,Object? payloadSizeBytes = freezed,Object? payloadMediaType = freezed,Object? payloadContract = freezed,Object? payloadJson = freezed,Object? payloadBytesBase64 = freezed,Object? payloadSourceUrl = freezed,Object? selectorKey = freezed,Object? targetRef = freezed,Object? producer = freezed,Object? publisherExecutionId = freezed,Object? idempotencyKey = freezed,Object? publishedAtUtc = freezed,Object? metadata = null,}) {
  return _then(PublishHubArtifactRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,artifactFamily: null == artifactFamily ? _self.artifactFamily : artifactFamily // ignore: cast_nullable_to_non_nullable
as String,artifactKey: null == artifactKey ? _self.artifactKey : artifactKey // ignore: cast_nullable_to_non_nullable
as String,revisionId: null == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,authorityBaseUrl: freezed == authorityBaseUrl ? _self.authorityBaseUrl : authorityBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,indexUrl: freezed == indexUrl ? _self.indexUrl : indexUrl // ignore: cast_nullable_to_non_nullable
as String?,payloadUrl: freezed == payloadUrl ? _self.payloadUrl : payloadUrl // ignore: cast_nullable_to_non_nullable
as String?,payloadSha256: freezed == payloadSha256 ? _self.payloadSha256 : payloadSha256 // ignore: cast_nullable_to_non_nullable
as String?,payloadSizeBytes: freezed == payloadSizeBytes ? _self.payloadSizeBytes : payloadSizeBytes // ignore: cast_nullable_to_non_nullable
as int?,payloadMediaType: freezed == payloadMediaType ? _self.payloadMediaType : payloadMediaType // ignore: cast_nullable_to_non_nullable
as String?,payloadContract: freezed == payloadContract ? _self.payloadContract : payloadContract // ignore: cast_nullable_to_non_nullable
as String?,payloadJson: freezed == payloadJson ? _self._payloadJson : payloadJson // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>?,payloadBytesBase64: freezed == payloadBytesBase64 ? _self.payloadBytesBase64 : payloadBytesBase64 // ignore: cast_nullable_to_non_nullable
as String?,payloadSourceUrl: freezed == payloadSourceUrl ? _self.payloadSourceUrl : payloadSourceUrl // ignore: cast_nullable_to_non_nullable
as String?,selectorKey: freezed == selectorKey ? _self.selectorKey : selectorKey // ignore: cast_nullable_to_non_nullable
as String?,targetRef: freezed == targetRef ? _self.targetRef : targetRef // ignore: cast_nullable_to_non_nullable
as String?,producer: freezed == producer ? _self.producer : producer // ignore: cast_nullable_to_non_nullable
as HubArtifactProducerProvenance?,publisherExecutionId: freezed == publisherExecutionId ? _self.publisherExecutionId : publisherExecutionId // ignore: cast_nullable_to_non_nullable
as String?,idempotencyKey: freezed == idempotencyKey ? _self.idempotencyKey : idempotencyKey // ignore: cast_nullable_to_non_nullable
as String?,publishedAtUtc: freezed == publishedAtUtc ? _self.publishedAtUtc : publishedAtUtc // ignore: cast_nullable_to_non_nullable
as String?,metadata: null == metadata ? _self._metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

/// Create a copy of HubArtifactAuthorityRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$HubArtifactProducerProvenanceCopyWith<$Res>? get producer {
    if (_self.producer == null) {
    return null;
  }

  return $HubArtifactProducerProvenanceCopyWith<$Res>(_self.producer!, (value) {
    return _then(_self.copyWith(producer: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class ResolveHubArtifactRequest implements HubArtifactAuthorityRequest {
   ResolveHubArtifactRequest({@UuidValueConverter() this.requestId, required this.artifactFamily, required this.artifactKey, required this.channel, this.revisionId, this.authorityBaseUrl, this.indexUrl, final  String? $type}): $type = $type ?? 'resolve_hub_artifact';
  factory ResolveHubArtifactRequest.fromJson(Map<String, dynamic> json) => _$ResolveHubArtifactRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  String artifactFamily;
@override final  String artifactKey;
@override final  String channel;
@override final  String? revisionId;
@override final  String? authorityBaseUrl;
@override final  String? indexUrl;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of HubArtifactAuthorityRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ResolveHubArtifactRequestCopyWith<ResolveHubArtifactRequest> get copyWith => _$ResolveHubArtifactRequestCopyWithImpl<ResolveHubArtifactRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ResolveHubArtifactRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ResolveHubArtifactRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.artifactFamily, artifactFamily) || other.artifactFamily == artifactFamily)&&(identical(other.artifactKey, artifactKey) || other.artifactKey == artifactKey)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.authorityBaseUrl, authorityBaseUrl) || other.authorityBaseUrl == authorityBaseUrl)&&(identical(other.indexUrl, indexUrl) || other.indexUrl == indexUrl));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,artifactFamily,artifactKey,channel,revisionId,authorityBaseUrl,indexUrl);

@override
String toString() {
  return 'HubArtifactAuthorityRequest.resolveHubArtifact(requestId: $requestId, artifactFamily: $artifactFamily, artifactKey: $artifactKey, channel: $channel, revisionId: $revisionId, authorityBaseUrl: $authorityBaseUrl, indexUrl: $indexUrl)';
}


}

/// @nodoc
abstract mixin class $ResolveHubArtifactRequestCopyWith<$Res> implements $HubArtifactAuthorityRequestCopyWith<$Res> {
  factory $ResolveHubArtifactRequestCopyWith(ResolveHubArtifactRequest value, $Res Function(ResolveHubArtifactRequest) _then) = _$ResolveHubArtifactRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, String artifactFamily, String artifactKey, String channel, String? revisionId, String? authorityBaseUrl, String? indexUrl
});




}
/// @nodoc
class _$ResolveHubArtifactRequestCopyWithImpl<$Res>
    implements $ResolveHubArtifactRequestCopyWith<$Res> {
  _$ResolveHubArtifactRequestCopyWithImpl(this._self, this._then);

  final ResolveHubArtifactRequest _self;
  final $Res Function(ResolveHubArtifactRequest) _then;

/// Create a copy of HubArtifactAuthorityRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? artifactFamily = null,Object? artifactKey = null,Object? channel = null,Object? revisionId = freezed,Object? authorityBaseUrl = freezed,Object? indexUrl = freezed,}) {
  return _then(ResolveHubArtifactRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,artifactFamily: null == artifactFamily ? _self.artifactFamily : artifactFamily // ignore: cast_nullable_to_non_nullable
as String,artifactKey: null == artifactKey ? _self.artifactKey : artifactKey // ignore: cast_nullable_to_non_nullable
as String,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,revisionId: freezed == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String?,authorityBaseUrl: freezed == authorityBaseUrl ? _self.authorityBaseUrl : authorityBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,indexUrl: freezed == indexUrl ? _self.indexUrl : indexUrl // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

HubArtifactAuthorityResponse _$HubArtifactAuthorityResponseFromJson(
  Map<String, dynamic> json
) {
        switch (json['operation']) {
                  case 'publish_hub_artifact':
          return PublishHubArtifactResponse.fromJson(
            json
          );
                case 'resolve_hub_artifact':
          return ResolveHubArtifactResponse.fromJson(
            json
          );
        
          default:
            throw CheckedFromJsonException(
  json,
  'operation',
  'HubArtifactAuthorityResponse',
  'Invalid union type "${json['operation']}"!'
);
        }
      
}

/// @nodoc
mixin _$HubArtifactAuthorityResponse {

@UuidValueConverter() UuidValue? get requestId; bool get success; String? get info; String? get error; String get authoritySourceUrl; HubArtifactPayloadLock get artifactLock; HubArtifactProducerProvenance? get producer;
/// Create a copy of HubArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$HubArtifactAuthorityResponseCopyWith<HubArtifactAuthorityResponse> get copyWith => _$HubArtifactAuthorityResponseCopyWithImpl<HubArtifactAuthorityResponse>(this as HubArtifactAuthorityResponse, _$identity);

  /// Serializes this HubArtifactAuthorityResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is HubArtifactAuthorityResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.info, info) || other.info == info)&&(identical(other.error, error) || other.error == error)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl)&&(identical(other.artifactLock, artifactLock) || other.artifactLock == artifactLock)&&(identical(other.producer, producer) || other.producer == producer));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,info,error,authoritySourceUrl,artifactLock,producer);

@override
String toString() {
  return 'HubArtifactAuthorityResponse(requestId: $requestId, success: $success, info: $info, error: $error, authoritySourceUrl: $authoritySourceUrl, artifactLock: $artifactLock, producer: $producer)';
}


}

/// @nodoc
abstract mixin class $HubArtifactAuthorityResponseCopyWith<$Res>  {
  factory $HubArtifactAuthorityResponseCopyWith(HubArtifactAuthorityResponse value, $Res Function(HubArtifactAuthorityResponse) _then) = _$HubArtifactAuthorityResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? info, String? error, String authoritySourceUrl, HubArtifactPayloadLock artifactLock, HubArtifactProducerProvenance? producer
});


$HubArtifactPayloadLockCopyWith<$Res> get artifactLock;$HubArtifactProducerProvenanceCopyWith<$Res>? get producer;

}
/// @nodoc
class _$HubArtifactAuthorityResponseCopyWithImpl<$Res>
    implements $HubArtifactAuthorityResponseCopyWith<$Res> {
  _$HubArtifactAuthorityResponseCopyWithImpl(this._self, this._then);

  final HubArtifactAuthorityResponse _self;
  final $Res Function(HubArtifactAuthorityResponse) _then;

/// Create a copy of HubArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? success = null,Object? info = freezed,Object? error = freezed,Object? authoritySourceUrl = null,Object? artifactLock = null,Object? producer = freezed,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,info: freezed == info ? _self.info : info // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,authoritySourceUrl: null == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String,artifactLock: null == artifactLock ? _self.artifactLock : artifactLock // ignore: cast_nullable_to_non_nullable
as HubArtifactPayloadLock,producer: freezed == producer ? _self.producer : producer // ignore: cast_nullable_to_non_nullable
as HubArtifactProducerProvenance?,
  ));
}
/// Create a copy of HubArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$HubArtifactPayloadLockCopyWith<$Res> get artifactLock {
  
  return $HubArtifactPayloadLockCopyWith<$Res>(_self.artifactLock, (value) {
    return _then(_self.copyWith(artifactLock: value));
  });
}/// Create a copy of HubArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$HubArtifactProducerProvenanceCopyWith<$Res>? get producer {
    if (_self.producer == null) {
    return null;
  }

  return $HubArtifactProducerProvenanceCopyWith<$Res>(_self.producer!, (value) {
    return _then(_self.copyWith(producer: value));
  });
}
}


/// Adds pattern-matching-related methods to [HubArtifactAuthorityResponse].
extension HubArtifactAuthorityResponsePatterns on HubArtifactAuthorityResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( PublishHubArtifactResponse value)?  publishHubArtifact,TResult Function( ResolveHubArtifactResponse value)?  resolveHubArtifact,required TResult orElse(),}){
final _that = this;
switch (_that) {
case PublishHubArtifactResponse() when publishHubArtifact != null:
return publishHubArtifact(_that);case ResolveHubArtifactResponse() when resolveHubArtifact != null:
return resolveHubArtifact(_that);case _:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( PublishHubArtifactResponse value)  publishHubArtifact,required TResult Function( ResolveHubArtifactResponse value)  resolveHubArtifact,}){
final _that = this;
switch (_that) {
case PublishHubArtifactResponse():
return publishHubArtifact(_that);case ResolveHubArtifactResponse():
return resolveHubArtifact(_that);case _:
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( PublishHubArtifactResponse value)?  publishHubArtifact,TResult? Function( ResolveHubArtifactResponse value)?  resolveHubArtifact,}){
final _that = this;
switch (_that) {
case PublishHubArtifactResponse() when publishHubArtifact != null:
return publishHubArtifact(_that);case ResolveHubArtifactResponse() when resolveHubArtifact != null:
return resolveHubArtifact(_that);case _:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  bool accepted,  String authoritySourceUrl,  HubArtifactPayloadLock artifactLock,  HubArtifactProducerProvenance? producer)?  publishHubArtifact,TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String authoritySourceUrl,  HubArtifactPayloadLock artifactLock,  HubArtifactProducerProvenance? producer)?  resolveHubArtifact,required TResult orElse(),}) {final _that = this;
switch (_that) {
case PublishHubArtifactResponse() when publishHubArtifact != null:
return publishHubArtifact(_that.requestId,_that.success,_that.info,_that.error,_that.accepted,_that.authoritySourceUrl,_that.artifactLock,_that.producer);case ResolveHubArtifactResponse() when resolveHubArtifact != null:
return resolveHubArtifact(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.artifactLock,_that.producer);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  bool accepted,  String authoritySourceUrl,  HubArtifactPayloadLock artifactLock,  HubArtifactProducerProvenance? producer)  publishHubArtifact,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String authoritySourceUrl,  HubArtifactPayloadLock artifactLock,  HubArtifactProducerProvenance? producer)  resolveHubArtifact,}) {final _that = this;
switch (_that) {
case PublishHubArtifactResponse():
return publishHubArtifact(_that.requestId,_that.success,_that.info,_that.error,_that.accepted,_that.authoritySourceUrl,_that.artifactLock,_that.producer);case ResolveHubArtifactResponse():
return resolveHubArtifact(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.artifactLock,_that.producer);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  bool accepted,  String authoritySourceUrl,  HubArtifactPayloadLock artifactLock,  HubArtifactProducerProvenance? producer)?  publishHubArtifact,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String authoritySourceUrl,  HubArtifactPayloadLock artifactLock,  HubArtifactProducerProvenance? producer)?  resolveHubArtifact,}) {final _that = this;
switch (_that) {
case PublishHubArtifactResponse() when publishHubArtifact != null:
return publishHubArtifact(_that.requestId,_that.success,_that.info,_that.error,_that.accepted,_that.authoritySourceUrl,_that.artifactLock,_that.producer);case ResolveHubArtifactResponse() when resolveHubArtifact != null:
return resolveHubArtifact(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.artifactLock,_that.producer);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class PublishHubArtifactResponse implements HubArtifactAuthorityResponse {
   PublishHubArtifactResponse({@UuidValueConverter() this.requestId, required this.success, this.info, this.error, required this.accepted, required this.authoritySourceUrl, required this.artifactLock, this.producer, final  String? $type}): $type = $type ?? 'publish_hub_artifact';
  factory PublishHubArtifactResponse.fromJson(Map<String, dynamic> json) => _$PublishHubArtifactResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? info;
@override final  String? error;
 final  bool accepted;
@override final  String authoritySourceUrl;
@override final  HubArtifactPayloadLock artifactLock;
@override final  HubArtifactProducerProvenance? producer;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of HubArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$PublishHubArtifactResponseCopyWith<PublishHubArtifactResponse> get copyWith => _$PublishHubArtifactResponseCopyWithImpl<PublishHubArtifactResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$PublishHubArtifactResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is PublishHubArtifactResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.info, info) || other.info == info)&&(identical(other.error, error) || other.error == error)&&(identical(other.accepted, accepted) || other.accepted == accepted)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl)&&(identical(other.artifactLock, artifactLock) || other.artifactLock == artifactLock)&&(identical(other.producer, producer) || other.producer == producer));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,info,error,accepted,authoritySourceUrl,artifactLock,producer);

@override
String toString() {
  return 'HubArtifactAuthorityResponse.publishHubArtifact(requestId: $requestId, success: $success, info: $info, error: $error, accepted: $accepted, authoritySourceUrl: $authoritySourceUrl, artifactLock: $artifactLock, producer: $producer)';
}


}

/// @nodoc
abstract mixin class $PublishHubArtifactResponseCopyWith<$Res> implements $HubArtifactAuthorityResponseCopyWith<$Res> {
  factory $PublishHubArtifactResponseCopyWith(PublishHubArtifactResponse value, $Res Function(PublishHubArtifactResponse) _then) = _$PublishHubArtifactResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? info, String? error, bool accepted, String authoritySourceUrl, HubArtifactPayloadLock artifactLock, HubArtifactProducerProvenance? producer
});


@override $HubArtifactPayloadLockCopyWith<$Res> get artifactLock;@override $HubArtifactProducerProvenanceCopyWith<$Res>? get producer;

}
/// @nodoc
class _$PublishHubArtifactResponseCopyWithImpl<$Res>
    implements $PublishHubArtifactResponseCopyWith<$Res> {
  _$PublishHubArtifactResponseCopyWithImpl(this._self, this._then);

  final PublishHubArtifactResponse _self;
  final $Res Function(PublishHubArtifactResponse) _then;

/// Create a copy of HubArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? info = freezed,Object? error = freezed,Object? accepted = null,Object? authoritySourceUrl = null,Object? artifactLock = null,Object? producer = freezed,}) {
  return _then(PublishHubArtifactResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,info: freezed == info ? _self.info : info // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,accepted: null == accepted ? _self.accepted : accepted // ignore: cast_nullable_to_non_nullable
as bool,authoritySourceUrl: null == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String,artifactLock: null == artifactLock ? _self.artifactLock : artifactLock // ignore: cast_nullable_to_non_nullable
as HubArtifactPayloadLock,producer: freezed == producer ? _self.producer : producer // ignore: cast_nullable_to_non_nullable
as HubArtifactProducerProvenance?,
  ));
}

/// Create a copy of HubArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$HubArtifactPayloadLockCopyWith<$Res> get artifactLock {
  
  return $HubArtifactPayloadLockCopyWith<$Res>(_self.artifactLock, (value) {
    return _then(_self.copyWith(artifactLock: value));
  });
}/// Create a copy of HubArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$HubArtifactProducerProvenanceCopyWith<$Res>? get producer {
    if (_self.producer == null) {
    return null;
  }

  return $HubArtifactProducerProvenanceCopyWith<$Res>(_self.producer!, (value) {
    return _then(_self.copyWith(producer: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class ResolveHubArtifactResponse implements HubArtifactAuthorityResponse {
   ResolveHubArtifactResponse({@UuidValueConverter() this.requestId, required this.success, this.info, this.error, required this.authoritySourceUrl, required this.artifactLock, this.producer, final  String? $type}): $type = $type ?? 'resolve_hub_artifact';
  factory ResolveHubArtifactResponse.fromJson(Map<String, dynamic> json) => _$ResolveHubArtifactResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? info;
@override final  String? error;
@override final  String authoritySourceUrl;
@override final  HubArtifactPayloadLock artifactLock;
@override final  HubArtifactProducerProvenance? producer;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of HubArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ResolveHubArtifactResponseCopyWith<ResolveHubArtifactResponse> get copyWith => _$ResolveHubArtifactResponseCopyWithImpl<ResolveHubArtifactResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ResolveHubArtifactResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ResolveHubArtifactResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.info, info) || other.info == info)&&(identical(other.error, error) || other.error == error)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl)&&(identical(other.artifactLock, artifactLock) || other.artifactLock == artifactLock)&&(identical(other.producer, producer) || other.producer == producer));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,info,error,authoritySourceUrl,artifactLock,producer);

@override
String toString() {
  return 'HubArtifactAuthorityResponse.resolveHubArtifact(requestId: $requestId, success: $success, info: $info, error: $error, authoritySourceUrl: $authoritySourceUrl, artifactLock: $artifactLock, producer: $producer)';
}


}

/// @nodoc
abstract mixin class $ResolveHubArtifactResponseCopyWith<$Res> implements $HubArtifactAuthorityResponseCopyWith<$Res> {
  factory $ResolveHubArtifactResponseCopyWith(ResolveHubArtifactResponse value, $Res Function(ResolveHubArtifactResponse) _then) = _$ResolveHubArtifactResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? info, String? error, String authoritySourceUrl, HubArtifactPayloadLock artifactLock, HubArtifactProducerProvenance? producer
});


@override $HubArtifactPayloadLockCopyWith<$Res> get artifactLock;@override $HubArtifactProducerProvenanceCopyWith<$Res>? get producer;

}
/// @nodoc
class _$ResolveHubArtifactResponseCopyWithImpl<$Res>
    implements $ResolveHubArtifactResponseCopyWith<$Res> {
  _$ResolveHubArtifactResponseCopyWithImpl(this._self, this._then);

  final ResolveHubArtifactResponse _self;
  final $Res Function(ResolveHubArtifactResponse) _then;

/// Create a copy of HubArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? info = freezed,Object? error = freezed,Object? authoritySourceUrl = null,Object? artifactLock = null,Object? producer = freezed,}) {
  return _then(ResolveHubArtifactResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,info: freezed == info ? _self.info : info // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,authoritySourceUrl: null == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String,artifactLock: null == artifactLock ? _self.artifactLock : artifactLock // ignore: cast_nullable_to_non_nullable
as HubArtifactPayloadLock,producer: freezed == producer ? _self.producer : producer // ignore: cast_nullable_to_non_nullable
as HubArtifactProducerProvenance?,
  ));
}

/// Create a copy of HubArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$HubArtifactPayloadLockCopyWith<$Res> get artifactLock {
  
  return $HubArtifactPayloadLockCopyWith<$Res>(_self.artifactLock, (value) {
    return _then(_self.copyWith(artifactLock: value));
  });
}/// Create a copy of HubArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$HubArtifactProducerProvenanceCopyWith<$Res>? get producer {
    if (_self.producer == null) {
    return null;
  }

  return $HubArtifactProducerProvenanceCopyWith<$Res>(_self.producer!, (value) {
    return _then(_self.copyWith(producer: value));
  });
}
}


/// @nodoc
mixin _$HubArtifactProducerProvenance {

 String get producerKind; String get producerKey; String? get provenanceKey; String? get producerRevisionId; String? get sourceRevisionId; String? get sourceRevisionKind; String? get materializationRef; String? get buildRef; Map<String, dynamic> get metadata;
/// Create a copy of HubArtifactProducerProvenance
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$HubArtifactProducerProvenanceCopyWith<HubArtifactProducerProvenance> get copyWith => _$HubArtifactProducerProvenanceCopyWithImpl<HubArtifactProducerProvenance>(this as HubArtifactProducerProvenance, _$identity);

  /// Serializes this HubArtifactProducerProvenance to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is HubArtifactProducerProvenance&&(identical(other.producerKind, producerKind) || other.producerKind == producerKind)&&(identical(other.producerKey, producerKey) || other.producerKey == producerKey)&&(identical(other.provenanceKey, provenanceKey) || other.provenanceKey == provenanceKey)&&(identical(other.producerRevisionId, producerRevisionId) || other.producerRevisionId == producerRevisionId)&&(identical(other.sourceRevisionId, sourceRevisionId) || other.sourceRevisionId == sourceRevisionId)&&(identical(other.sourceRevisionKind, sourceRevisionKind) || other.sourceRevisionKind == sourceRevisionKind)&&(identical(other.materializationRef, materializationRef) || other.materializationRef == materializationRef)&&(identical(other.buildRef, buildRef) || other.buildRef == buildRef)&&const DeepCollectionEquality().equals(other.metadata, metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,producerKind,producerKey,provenanceKey,producerRevisionId,sourceRevisionId,sourceRevisionKind,materializationRef,buildRef,const DeepCollectionEquality().hash(metadata));

@override
String toString() {
  return 'HubArtifactProducerProvenance(producerKind: $producerKind, producerKey: $producerKey, provenanceKey: $provenanceKey, producerRevisionId: $producerRevisionId, sourceRevisionId: $sourceRevisionId, sourceRevisionKind: $sourceRevisionKind, materializationRef: $materializationRef, buildRef: $buildRef, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class $HubArtifactProducerProvenanceCopyWith<$Res>  {
  factory $HubArtifactProducerProvenanceCopyWith(HubArtifactProducerProvenance value, $Res Function(HubArtifactProducerProvenance) _then) = _$HubArtifactProducerProvenanceCopyWithImpl;
@useResult
$Res call({
 String producerKind, String producerKey, String? provenanceKey, String? producerRevisionId, String? sourceRevisionId, String? sourceRevisionKind, String? materializationRef, String? buildRef, Map<String, dynamic> metadata
});




}
/// @nodoc
class _$HubArtifactProducerProvenanceCopyWithImpl<$Res>
    implements $HubArtifactProducerProvenanceCopyWith<$Res> {
  _$HubArtifactProducerProvenanceCopyWithImpl(this._self, this._then);

  final HubArtifactProducerProvenance _self;
  final $Res Function(HubArtifactProducerProvenance) _then;

/// Create a copy of HubArtifactProducerProvenance
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? producerKind = null,Object? producerKey = null,Object? provenanceKey = freezed,Object? producerRevisionId = freezed,Object? sourceRevisionId = freezed,Object? sourceRevisionKind = freezed,Object? materializationRef = freezed,Object? buildRef = freezed,Object? metadata = null,}) {
  return _then(_self.copyWith(
producerKind: null == producerKind ? _self.producerKind : producerKind // ignore: cast_nullable_to_non_nullable
as String,producerKey: null == producerKey ? _self.producerKey : producerKey // ignore: cast_nullable_to_non_nullable
as String,provenanceKey: freezed == provenanceKey ? _self.provenanceKey : provenanceKey // ignore: cast_nullable_to_non_nullable
as String?,producerRevisionId: freezed == producerRevisionId ? _self.producerRevisionId : producerRevisionId // ignore: cast_nullable_to_non_nullable
as String?,sourceRevisionId: freezed == sourceRevisionId ? _self.sourceRevisionId : sourceRevisionId // ignore: cast_nullable_to_non_nullable
as String?,sourceRevisionKind: freezed == sourceRevisionKind ? _self.sourceRevisionKind : sourceRevisionKind // ignore: cast_nullable_to_non_nullable
as String?,materializationRef: freezed == materializationRef ? _self.materializationRef : materializationRef // ignore: cast_nullable_to_non_nullable
as String?,buildRef: freezed == buildRef ? _self.buildRef : buildRef // ignore: cast_nullable_to_non_nullable
as String?,metadata: null == metadata ? _self.metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [HubArtifactProducerProvenance].
extension HubArtifactProducerProvenancePatterns on HubArtifactProducerProvenance {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _HubArtifactProducerProvenance value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _HubArtifactProducerProvenance() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _HubArtifactProducerProvenance value)  def,}){
final _that = this;
switch (_that) {
case _HubArtifactProducerProvenance():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _HubArtifactProducerProvenance value)?  def,}){
final _that = this;
switch (_that) {
case _HubArtifactProducerProvenance() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String producerKind,  String producerKey,  String? provenanceKey,  String? producerRevisionId,  String? sourceRevisionId,  String? sourceRevisionKind,  String? materializationRef,  String? buildRef,  Map<String, dynamic> metadata)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _HubArtifactProducerProvenance() when def != null:
return def(_that.producerKind,_that.producerKey,_that.provenanceKey,_that.producerRevisionId,_that.sourceRevisionId,_that.sourceRevisionKind,_that.materializationRef,_that.buildRef,_that.metadata);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String producerKind,  String producerKey,  String? provenanceKey,  String? producerRevisionId,  String? sourceRevisionId,  String? sourceRevisionKind,  String? materializationRef,  String? buildRef,  Map<String, dynamic> metadata)  def,}) {final _that = this;
switch (_that) {
case _HubArtifactProducerProvenance():
return def(_that.producerKind,_that.producerKey,_that.provenanceKey,_that.producerRevisionId,_that.sourceRevisionId,_that.sourceRevisionKind,_that.materializationRef,_that.buildRef,_that.metadata);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String producerKind,  String producerKey,  String? provenanceKey,  String? producerRevisionId,  String? sourceRevisionId,  String? sourceRevisionKind,  String? materializationRef,  String? buildRef,  Map<String, dynamic> metadata)?  def,}) {final _that = this;
switch (_that) {
case _HubArtifactProducerProvenance() when def != null:
return def(_that.producerKind,_that.producerKey,_that.provenanceKey,_that.producerRevisionId,_that.sourceRevisionId,_that.sourceRevisionKind,_that.materializationRef,_that.buildRef,_that.metadata);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _HubArtifactProducerProvenance implements HubArtifactProducerProvenance {
   _HubArtifactProducerProvenance({required this.producerKind, required this.producerKey, this.provenanceKey, this.producerRevisionId, this.sourceRevisionId, this.sourceRevisionKind, this.materializationRef, this.buildRef, required final  Map<String, dynamic> metadata}): _metadata = metadata;
  factory _HubArtifactProducerProvenance.fromJson(Map<String, dynamic> json) => _$HubArtifactProducerProvenanceFromJson(json);

@override final  String producerKind;
@override final  String producerKey;
@override final  String? provenanceKey;
@override final  String? producerRevisionId;
@override final  String? sourceRevisionId;
@override final  String? sourceRevisionKind;
@override final  String? materializationRef;
@override final  String? buildRef;
 final  Map<String, dynamic> _metadata;
@override Map<String, dynamic> get metadata {
  if (_metadata is EqualUnmodifiableMapView) return _metadata;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_metadata);
}


/// Create a copy of HubArtifactProducerProvenance
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$HubArtifactProducerProvenanceCopyWith<_HubArtifactProducerProvenance> get copyWith => __$HubArtifactProducerProvenanceCopyWithImpl<_HubArtifactProducerProvenance>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$HubArtifactProducerProvenanceToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _HubArtifactProducerProvenance&&(identical(other.producerKind, producerKind) || other.producerKind == producerKind)&&(identical(other.producerKey, producerKey) || other.producerKey == producerKey)&&(identical(other.provenanceKey, provenanceKey) || other.provenanceKey == provenanceKey)&&(identical(other.producerRevisionId, producerRevisionId) || other.producerRevisionId == producerRevisionId)&&(identical(other.sourceRevisionId, sourceRevisionId) || other.sourceRevisionId == sourceRevisionId)&&(identical(other.sourceRevisionKind, sourceRevisionKind) || other.sourceRevisionKind == sourceRevisionKind)&&(identical(other.materializationRef, materializationRef) || other.materializationRef == materializationRef)&&(identical(other.buildRef, buildRef) || other.buildRef == buildRef)&&const DeepCollectionEquality().equals(other._metadata, _metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,producerKind,producerKey,provenanceKey,producerRevisionId,sourceRevisionId,sourceRevisionKind,materializationRef,buildRef,const DeepCollectionEquality().hash(_metadata));

@override
String toString() {
  return 'HubArtifactProducerProvenance.def(producerKind: $producerKind, producerKey: $producerKey, provenanceKey: $provenanceKey, producerRevisionId: $producerRevisionId, sourceRevisionId: $sourceRevisionId, sourceRevisionKind: $sourceRevisionKind, materializationRef: $materializationRef, buildRef: $buildRef, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class _$HubArtifactProducerProvenanceCopyWith<$Res> implements $HubArtifactProducerProvenanceCopyWith<$Res> {
  factory _$HubArtifactProducerProvenanceCopyWith(_HubArtifactProducerProvenance value, $Res Function(_HubArtifactProducerProvenance) _then) = __$HubArtifactProducerProvenanceCopyWithImpl;
@override @useResult
$Res call({
 String producerKind, String producerKey, String? provenanceKey, String? producerRevisionId, String? sourceRevisionId, String? sourceRevisionKind, String? materializationRef, String? buildRef, Map<String, dynamic> metadata
});




}
/// @nodoc
class __$HubArtifactProducerProvenanceCopyWithImpl<$Res>
    implements _$HubArtifactProducerProvenanceCopyWith<$Res> {
  __$HubArtifactProducerProvenanceCopyWithImpl(this._self, this._then);

  final _HubArtifactProducerProvenance _self;
  final $Res Function(_HubArtifactProducerProvenance) _then;

/// Create a copy of HubArtifactProducerProvenance
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? producerKind = null,Object? producerKey = null,Object? provenanceKey = freezed,Object? producerRevisionId = freezed,Object? sourceRevisionId = freezed,Object? sourceRevisionKind = freezed,Object? materializationRef = freezed,Object? buildRef = freezed,Object? metadata = null,}) {
  return _then(_HubArtifactProducerProvenance(
producerKind: null == producerKind ? _self.producerKind : producerKind // ignore: cast_nullable_to_non_nullable
as String,producerKey: null == producerKey ? _self.producerKey : producerKey // ignore: cast_nullable_to_non_nullable
as String,provenanceKey: freezed == provenanceKey ? _self.provenanceKey : provenanceKey // ignore: cast_nullable_to_non_nullable
as String?,producerRevisionId: freezed == producerRevisionId ? _self.producerRevisionId : producerRevisionId // ignore: cast_nullable_to_non_nullable
as String?,sourceRevisionId: freezed == sourceRevisionId ? _self.sourceRevisionId : sourceRevisionId // ignore: cast_nullable_to_non_nullable
as String?,sourceRevisionKind: freezed == sourceRevisionKind ? _self.sourceRevisionKind : sourceRevisionKind // ignore: cast_nullable_to_non_nullable
as String?,materializationRef: freezed == materializationRef ? _self.materializationRef : materializationRef // ignore: cast_nullable_to_non_nullable
as String?,buildRef: freezed == buildRef ? _self.buildRef : buildRef // ignore: cast_nullable_to_non_nullable
as String?,metadata: null == metadata ? _self._metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$HubArtifactPayloadLock {

 String get artifactFamily; String get artifactKey; String get channel; String get revisionId; String get payloadUrl; String get payloadSha256; int? get payloadSizeBytes; String? get payloadMediaType; String? get payloadContract; String? get authoritySourceUrl; String? get selectorKey; String? get targetRef; Map<String, dynamic> get metadata;
/// Create a copy of HubArtifactPayloadLock
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$HubArtifactPayloadLockCopyWith<HubArtifactPayloadLock> get copyWith => _$HubArtifactPayloadLockCopyWithImpl<HubArtifactPayloadLock>(this as HubArtifactPayloadLock, _$identity);

  /// Serializes this HubArtifactPayloadLock to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is HubArtifactPayloadLock&&(identical(other.artifactFamily, artifactFamily) || other.artifactFamily == artifactFamily)&&(identical(other.artifactKey, artifactKey) || other.artifactKey == artifactKey)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.payloadUrl, payloadUrl) || other.payloadUrl == payloadUrl)&&(identical(other.payloadSha256, payloadSha256) || other.payloadSha256 == payloadSha256)&&(identical(other.payloadSizeBytes, payloadSizeBytes) || other.payloadSizeBytes == payloadSizeBytes)&&(identical(other.payloadMediaType, payloadMediaType) || other.payloadMediaType == payloadMediaType)&&(identical(other.payloadContract, payloadContract) || other.payloadContract == payloadContract)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl)&&(identical(other.selectorKey, selectorKey) || other.selectorKey == selectorKey)&&(identical(other.targetRef, targetRef) || other.targetRef == targetRef)&&const DeepCollectionEquality().equals(other.metadata, metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,artifactFamily,artifactKey,channel,revisionId,payloadUrl,payloadSha256,payloadSizeBytes,payloadMediaType,payloadContract,authoritySourceUrl,selectorKey,targetRef,const DeepCollectionEquality().hash(metadata));

@override
String toString() {
  return 'HubArtifactPayloadLock(artifactFamily: $artifactFamily, artifactKey: $artifactKey, channel: $channel, revisionId: $revisionId, payloadUrl: $payloadUrl, payloadSha256: $payloadSha256, payloadSizeBytes: $payloadSizeBytes, payloadMediaType: $payloadMediaType, payloadContract: $payloadContract, authoritySourceUrl: $authoritySourceUrl, selectorKey: $selectorKey, targetRef: $targetRef, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class $HubArtifactPayloadLockCopyWith<$Res>  {
  factory $HubArtifactPayloadLockCopyWith(HubArtifactPayloadLock value, $Res Function(HubArtifactPayloadLock) _then) = _$HubArtifactPayloadLockCopyWithImpl;
@useResult
$Res call({
 String artifactFamily, String artifactKey, String channel, String revisionId, String payloadUrl, String payloadSha256, int? payloadSizeBytes, String? payloadMediaType, String? payloadContract, String? authoritySourceUrl, String? selectorKey, String? targetRef, Map<String, dynamic> metadata
});




}
/// @nodoc
class _$HubArtifactPayloadLockCopyWithImpl<$Res>
    implements $HubArtifactPayloadLockCopyWith<$Res> {
  _$HubArtifactPayloadLockCopyWithImpl(this._self, this._then);

  final HubArtifactPayloadLock _self;
  final $Res Function(HubArtifactPayloadLock) _then;

/// Create a copy of HubArtifactPayloadLock
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? artifactFamily = null,Object? artifactKey = null,Object? channel = null,Object? revisionId = null,Object? payloadUrl = null,Object? payloadSha256 = null,Object? payloadSizeBytes = freezed,Object? payloadMediaType = freezed,Object? payloadContract = freezed,Object? authoritySourceUrl = freezed,Object? selectorKey = freezed,Object? targetRef = freezed,Object? metadata = null,}) {
  return _then(_self.copyWith(
artifactFamily: null == artifactFamily ? _self.artifactFamily : artifactFamily // ignore: cast_nullable_to_non_nullable
as String,artifactKey: null == artifactKey ? _self.artifactKey : artifactKey // ignore: cast_nullable_to_non_nullable
as String,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,revisionId: null == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String,payloadUrl: null == payloadUrl ? _self.payloadUrl : payloadUrl // ignore: cast_nullable_to_non_nullable
as String,payloadSha256: null == payloadSha256 ? _self.payloadSha256 : payloadSha256 // ignore: cast_nullable_to_non_nullable
as String,payloadSizeBytes: freezed == payloadSizeBytes ? _self.payloadSizeBytes : payloadSizeBytes // ignore: cast_nullable_to_non_nullable
as int?,payloadMediaType: freezed == payloadMediaType ? _self.payloadMediaType : payloadMediaType // ignore: cast_nullable_to_non_nullable
as String?,payloadContract: freezed == payloadContract ? _self.payloadContract : payloadContract // ignore: cast_nullable_to_non_nullable
as String?,authoritySourceUrl: freezed == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String?,selectorKey: freezed == selectorKey ? _self.selectorKey : selectorKey // ignore: cast_nullable_to_non_nullable
as String?,targetRef: freezed == targetRef ? _self.targetRef : targetRef // ignore: cast_nullable_to_non_nullable
as String?,metadata: null == metadata ? _self.metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [HubArtifactPayloadLock].
extension HubArtifactPayloadLockPatterns on HubArtifactPayloadLock {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _HubArtifactPayloadLock value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _HubArtifactPayloadLock() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _HubArtifactPayloadLock value)  def,}){
final _that = this;
switch (_that) {
case _HubArtifactPayloadLock():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _HubArtifactPayloadLock value)?  def,}){
final _that = this;
switch (_that) {
case _HubArtifactPayloadLock() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String artifactFamily,  String artifactKey,  String channel,  String revisionId,  String payloadUrl,  String payloadSha256,  int? payloadSizeBytes,  String? payloadMediaType,  String? payloadContract,  String? authoritySourceUrl,  String? selectorKey,  String? targetRef,  Map<String, dynamic> metadata)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _HubArtifactPayloadLock() when def != null:
return def(_that.artifactFamily,_that.artifactKey,_that.channel,_that.revisionId,_that.payloadUrl,_that.payloadSha256,_that.payloadSizeBytes,_that.payloadMediaType,_that.payloadContract,_that.authoritySourceUrl,_that.selectorKey,_that.targetRef,_that.metadata);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String artifactFamily,  String artifactKey,  String channel,  String revisionId,  String payloadUrl,  String payloadSha256,  int? payloadSizeBytes,  String? payloadMediaType,  String? payloadContract,  String? authoritySourceUrl,  String? selectorKey,  String? targetRef,  Map<String, dynamic> metadata)  def,}) {final _that = this;
switch (_that) {
case _HubArtifactPayloadLock():
return def(_that.artifactFamily,_that.artifactKey,_that.channel,_that.revisionId,_that.payloadUrl,_that.payloadSha256,_that.payloadSizeBytes,_that.payloadMediaType,_that.payloadContract,_that.authoritySourceUrl,_that.selectorKey,_that.targetRef,_that.metadata);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String artifactFamily,  String artifactKey,  String channel,  String revisionId,  String payloadUrl,  String payloadSha256,  int? payloadSizeBytes,  String? payloadMediaType,  String? payloadContract,  String? authoritySourceUrl,  String? selectorKey,  String? targetRef,  Map<String, dynamic> metadata)?  def,}) {final _that = this;
switch (_that) {
case _HubArtifactPayloadLock() when def != null:
return def(_that.artifactFamily,_that.artifactKey,_that.channel,_that.revisionId,_that.payloadUrl,_that.payloadSha256,_that.payloadSizeBytes,_that.payloadMediaType,_that.payloadContract,_that.authoritySourceUrl,_that.selectorKey,_that.targetRef,_that.metadata);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _HubArtifactPayloadLock implements HubArtifactPayloadLock {
   _HubArtifactPayloadLock({required this.artifactFamily, required this.artifactKey, required this.channel, required this.revisionId, required this.payloadUrl, required this.payloadSha256, this.payloadSizeBytes, this.payloadMediaType, this.payloadContract, this.authoritySourceUrl, this.selectorKey, this.targetRef, required final  Map<String, dynamic> metadata}): _metadata = metadata;
  factory _HubArtifactPayloadLock.fromJson(Map<String, dynamic> json) => _$HubArtifactPayloadLockFromJson(json);

@override final  String artifactFamily;
@override final  String artifactKey;
@override final  String channel;
@override final  String revisionId;
@override final  String payloadUrl;
@override final  String payloadSha256;
@override final  int? payloadSizeBytes;
@override final  String? payloadMediaType;
@override final  String? payloadContract;
@override final  String? authoritySourceUrl;
@override final  String? selectorKey;
@override final  String? targetRef;
 final  Map<String, dynamic> _metadata;
@override Map<String, dynamic> get metadata {
  if (_metadata is EqualUnmodifiableMapView) return _metadata;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_metadata);
}


/// Create a copy of HubArtifactPayloadLock
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$HubArtifactPayloadLockCopyWith<_HubArtifactPayloadLock> get copyWith => __$HubArtifactPayloadLockCopyWithImpl<_HubArtifactPayloadLock>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$HubArtifactPayloadLockToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _HubArtifactPayloadLock&&(identical(other.artifactFamily, artifactFamily) || other.artifactFamily == artifactFamily)&&(identical(other.artifactKey, artifactKey) || other.artifactKey == artifactKey)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.payloadUrl, payloadUrl) || other.payloadUrl == payloadUrl)&&(identical(other.payloadSha256, payloadSha256) || other.payloadSha256 == payloadSha256)&&(identical(other.payloadSizeBytes, payloadSizeBytes) || other.payloadSizeBytes == payloadSizeBytes)&&(identical(other.payloadMediaType, payloadMediaType) || other.payloadMediaType == payloadMediaType)&&(identical(other.payloadContract, payloadContract) || other.payloadContract == payloadContract)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl)&&(identical(other.selectorKey, selectorKey) || other.selectorKey == selectorKey)&&(identical(other.targetRef, targetRef) || other.targetRef == targetRef)&&const DeepCollectionEquality().equals(other._metadata, _metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,artifactFamily,artifactKey,channel,revisionId,payloadUrl,payloadSha256,payloadSizeBytes,payloadMediaType,payloadContract,authoritySourceUrl,selectorKey,targetRef,const DeepCollectionEquality().hash(_metadata));

@override
String toString() {
  return 'HubArtifactPayloadLock.def(artifactFamily: $artifactFamily, artifactKey: $artifactKey, channel: $channel, revisionId: $revisionId, payloadUrl: $payloadUrl, payloadSha256: $payloadSha256, payloadSizeBytes: $payloadSizeBytes, payloadMediaType: $payloadMediaType, payloadContract: $payloadContract, authoritySourceUrl: $authoritySourceUrl, selectorKey: $selectorKey, targetRef: $targetRef, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class _$HubArtifactPayloadLockCopyWith<$Res> implements $HubArtifactPayloadLockCopyWith<$Res> {
  factory _$HubArtifactPayloadLockCopyWith(_HubArtifactPayloadLock value, $Res Function(_HubArtifactPayloadLock) _then) = __$HubArtifactPayloadLockCopyWithImpl;
@override @useResult
$Res call({
 String artifactFamily, String artifactKey, String channel, String revisionId, String payloadUrl, String payloadSha256, int? payloadSizeBytes, String? payloadMediaType, String? payloadContract, String? authoritySourceUrl, String? selectorKey, String? targetRef, Map<String, dynamic> metadata
});




}
/// @nodoc
class __$HubArtifactPayloadLockCopyWithImpl<$Res>
    implements _$HubArtifactPayloadLockCopyWith<$Res> {
  __$HubArtifactPayloadLockCopyWithImpl(this._self, this._then);

  final _HubArtifactPayloadLock _self;
  final $Res Function(_HubArtifactPayloadLock) _then;

/// Create a copy of HubArtifactPayloadLock
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? artifactFamily = null,Object? artifactKey = null,Object? channel = null,Object? revisionId = null,Object? payloadUrl = null,Object? payloadSha256 = null,Object? payloadSizeBytes = freezed,Object? payloadMediaType = freezed,Object? payloadContract = freezed,Object? authoritySourceUrl = freezed,Object? selectorKey = freezed,Object? targetRef = freezed,Object? metadata = null,}) {
  return _then(_HubArtifactPayloadLock(
artifactFamily: null == artifactFamily ? _self.artifactFamily : artifactFamily // ignore: cast_nullable_to_non_nullable
as String,artifactKey: null == artifactKey ? _self.artifactKey : artifactKey // ignore: cast_nullable_to_non_nullable
as String,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,revisionId: null == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String,payloadUrl: null == payloadUrl ? _self.payloadUrl : payloadUrl // ignore: cast_nullable_to_non_nullable
as String,payloadSha256: null == payloadSha256 ? _self.payloadSha256 : payloadSha256 // ignore: cast_nullable_to_non_nullable
as String,payloadSizeBytes: freezed == payloadSizeBytes ? _self.payloadSizeBytes : payloadSizeBytes // ignore: cast_nullable_to_non_nullable
as int?,payloadMediaType: freezed == payloadMediaType ? _self.payloadMediaType : payloadMediaType // ignore: cast_nullable_to_non_nullable
as String?,payloadContract: freezed == payloadContract ? _self.payloadContract : payloadContract // ignore: cast_nullable_to_non_nullable
as String?,authoritySourceUrl: freezed == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String?,selectorKey: freezed == selectorKey ? _self.selectorKey : selectorKey // ignore: cast_nullable_to_non_nullable
as String?,targetRef: freezed == targetRef ? _self.targetRef : targetRef // ignore: cast_nullable_to_non_nullable
as String?,metadata: null == metadata ? _self._metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}

// dart format on
