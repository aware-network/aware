// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'deployment_artifact_authority_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;
DeploymentArtifactAuthorityRequest _$DeploymentArtifactAuthorityRequestFromJson(
  Map<String, dynamic> json
) {
    return ResolveDeploymentArtifactRequest.fromJson(
      json
    );
}

/// @nodoc
mixin _$DeploymentArtifactAuthorityRequest {

@UuidValueConverter() UuidValue? get requestId; String get artifactFamily; String? get artifactKey; String get channel; String? get revisionId; String? get authorityBaseUrl; String? get indexUrl;
/// Create a copy of DeploymentArtifactAuthorityRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DeploymentArtifactAuthorityRequestCopyWith<DeploymentArtifactAuthorityRequest> get copyWith => _$DeploymentArtifactAuthorityRequestCopyWithImpl<DeploymentArtifactAuthorityRequest>(this as DeploymentArtifactAuthorityRequest, _$identity);

  /// Serializes this DeploymentArtifactAuthorityRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DeploymentArtifactAuthorityRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.artifactFamily, artifactFamily) || other.artifactFamily == artifactFamily)&&(identical(other.artifactKey, artifactKey) || other.artifactKey == artifactKey)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.authorityBaseUrl, authorityBaseUrl) || other.authorityBaseUrl == authorityBaseUrl)&&(identical(other.indexUrl, indexUrl) || other.indexUrl == indexUrl));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,artifactFamily,artifactKey,channel,revisionId,authorityBaseUrl,indexUrl);

@override
String toString() {
  return 'DeploymentArtifactAuthorityRequest(requestId: $requestId, artifactFamily: $artifactFamily, artifactKey: $artifactKey, channel: $channel, revisionId: $revisionId, authorityBaseUrl: $authorityBaseUrl, indexUrl: $indexUrl)';
}


}

/// @nodoc
abstract mixin class $DeploymentArtifactAuthorityRequestCopyWith<$Res>  {
  factory $DeploymentArtifactAuthorityRequestCopyWith(DeploymentArtifactAuthorityRequest value, $Res Function(DeploymentArtifactAuthorityRequest) _then) = _$DeploymentArtifactAuthorityRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, String artifactFamily, String? artifactKey, String channel, String? revisionId, String? authorityBaseUrl, String? indexUrl
});




}
/// @nodoc
class _$DeploymentArtifactAuthorityRequestCopyWithImpl<$Res>
    implements $DeploymentArtifactAuthorityRequestCopyWith<$Res> {
  _$DeploymentArtifactAuthorityRequestCopyWithImpl(this._self, this._then);

  final DeploymentArtifactAuthorityRequest _self;
  final $Res Function(DeploymentArtifactAuthorityRequest) _then;

/// Create a copy of DeploymentArtifactAuthorityRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? artifactFamily = null,Object? artifactKey = freezed,Object? channel = null,Object? revisionId = freezed,Object? authorityBaseUrl = freezed,Object? indexUrl = freezed,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,artifactFamily: null == artifactFamily ? _self.artifactFamily : artifactFamily // ignore: cast_nullable_to_non_nullable
as String,artifactKey: freezed == artifactKey ? _self.artifactKey : artifactKey // ignore: cast_nullable_to_non_nullable
as String?,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,revisionId: freezed == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String?,authorityBaseUrl: freezed == authorityBaseUrl ? _self.authorityBaseUrl : authorityBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,indexUrl: freezed == indexUrl ? _self.indexUrl : indexUrl // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [DeploymentArtifactAuthorityRequest].
extension DeploymentArtifactAuthorityRequestPatterns on DeploymentArtifactAuthorityRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( ResolveDeploymentArtifactRequest value)?  resolveDeploymentArtifact,required TResult orElse(),}){
final _that = this;
switch (_that) {
case ResolveDeploymentArtifactRequest() when resolveDeploymentArtifact != null:
return resolveDeploymentArtifact(_that);case _:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( ResolveDeploymentArtifactRequest value)  resolveDeploymentArtifact,}){
final _that = this;
switch (_that) {
case ResolveDeploymentArtifactRequest():
return resolveDeploymentArtifact(_that);case _:
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( ResolveDeploymentArtifactRequest value)?  resolveDeploymentArtifact,}){
final _that = this;
switch (_that) {
case ResolveDeploymentArtifactRequest() when resolveDeploymentArtifact != null:
return resolveDeploymentArtifact(_that);case _:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  String artifactFamily,  String? artifactKey,  String channel,  String? revisionId,  String? authorityBaseUrl,  String? indexUrl)?  resolveDeploymentArtifact,required TResult orElse(),}) {final _that = this;
switch (_that) {
case ResolveDeploymentArtifactRequest() when resolveDeploymentArtifact != null:
return resolveDeploymentArtifact(_that.requestId,_that.artifactFamily,_that.artifactKey,_that.channel,_that.revisionId,_that.authorityBaseUrl,_that.indexUrl);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  String artifactFamily,  String? artifactKey,  String channel,  String? revisionId,  String? authorityBaseUrl,  String? indexUrl)  resolveDeploymentArtifact,}) {final _that = this;
switch (_that) {
case ResolveDeploymentArtifactRequest():
return resolveDeploymentArtifact(_that.requestId,_that.artifactFamily,_that.artifactKey,_that.channel,_that.revisionId,_that.authorityBaseUrl,_that.indexUrl);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  String artifactFamily,  String? artifactKey,  String channel,  String? revisionId,  String? authorityBaseUrl,  String? indexUrl)?  resolveDeploymentArtifact,}) {final _that = this;
switch (_that) {
case ResolveDeploymentArtifactRequest() when resolveDeploymentArtifact != null:
return resolveDeploymentArtifact(_that.requestId,_that.artifactFamily,_that.artifactKey,_that.channel,_that.revisionId,_that.authorityBaseUrl,_that.indexUrl);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class ResolveDeploymentArtifactRequest implements DeploymentArtifactAuthorityRequest {
   ResolveDeploymentArtifactRequest({@UuidValueConverter() this.requestId, required this.artifactFamily, this.artifactKey, required this.channel, this.revisionId, this.authorityBaseUrl, this.indexUrl});
  factory ResolveDeploymentArtifactRequest.fromJson(Map<String, dynamic> json) => _$ResolveDeploymentArtifactRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  String artifactFamily;
@override final  String? artifactKey;
@override final  String channel;
@override final  String? revisionId;
@override final  String? authorityBaseUrl;
@override final  String? indexUrl;

/// Create a copy of DeploymentArtifactAuthorityRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ResolveDeploymentArtifactRequestCopyWith<ResolveDeploymentArtifactRequest> get copyWith => _$ResolveDeploymentArtifactRequestCopyWithImpl<ResolveDeploymentArtifactRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ResolveDeploymentArtifactRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ResolveDeploymentArtifactRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.artifactFamily, artifactFamily) || other.artifactFamily == artifactFamily)&&(identical(other.artifactKey, artifactKey) || other.artifactKey == artifactKey)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.authorityBaseUrl, authorityBaseUrl) || other.authorityBaseUrl == authorityBaseUrl)&&(identical(other.indexUrl, indexUrl) || other.indexUrl == indexUrl));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,artifactFamily,artifactKey,channel,revisionId,authorityBaseUrl,indexUrl);

@override
String toString() {
  return 'DeploymentArtifactAuthorityRequest.resolveDeploymentArtifact(requestId: $requestId, artifactFamily: $artifactFamily, artifactKey: $artifactKey, channel: $channel, revisionId: $revisionId, authorityBaseUrl: $authorityBaseUrl, indexUrl: $indexUrl)';
}


}

/// @nodoc
abstract mixin class $ResolveDeploymentArtifactRequestCopyWith<$Res> implements $DeploymentArtifactAuthorityRequestCopyWith<$Res> {
  factory $ResolveDeploymentArtifactRequestCopyWith(ResolveDeploymentArtifactRequest value, $Res Function(ResolveDeploymentArtifactRequest) _then) = _$ResolveDeploymentArtifactRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, String artifactFamily, String? artifactKey, String channel, String? revisionId, String? authorityBaseUrl, String? indexUrl
});




}
/// @nodoc
class _$ResolveDeploymentArtifactRequestCopyWithImpl<$Res>
    implements $ResolveDeploymentArtifactRequestCopyWith<$Res> {
  _$ResolveDeploymentArtifactRequestCopyWithImpl(this._self, this._then);

  final ResolveDeploymentArtifactRequest _self;
  final $Res Function(ResolveDeploymentArtifactRequest) _then;

/// Create a copy of DeploymentArtifactAuthorityRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? artifactFamily = null,Object? artifactKey = freezed,Object? channel = null,Object? revisionId = freezed,Object? authorityBaseUrl = freezed,Object? indexUrl = freezed,}) {
  return _then(ResolveDeploymentArtifactRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,artifactFamily: null == artifactFamily ? _self.artifactFamily : artifactFamily // ignore: cast_nullable_to_non_nullable
as String,artifactKey: freezed == artifactKey ? _self.artifactKey : artifactKey // ignore: cast_nullable_to_non_nullable
as String?,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,revisionId: freezed == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String?,authorityBaseUrl: freezed == authorityBaseUrl ? _self.authorityBaseUrl : authorityBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,indexUrl: freezed == indexUrl ? _self.indexUrl : indexUrl // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

DeploymentArtifactAuthorityResponse _$DeploymentArtifactAuthorityResponseFromJson(
  Map<String, dynamic> json
) {
    return ResolveDeploymentArtifactResponse.fromJson(
      json
    );
}

/// @nodoc
mixin _$DeploymentArtifactAuthorityResponse {

@UuidValueConverter() UuidValue? get requestId; bool get success; String? get info; String? get error; String get authoritySourceUrl; String get artifactFamily; String get artifactKey; String get channel; String get revisionId; String get payloadUrl; String get payloadSha256; String get selectorKey; String get targetRef; DeploymentArtifactProducerProvenance get producer; String get nodePackageName; DeploymentArtifactLock get artifactLock; DeploymentArtifactTarget get target;
/// Create a copy of DeploymentArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DeploymentArtifactAuthorityResponseCopyWith<DeploymentArtifactAuthorityResponse> get copyWith => _$DeploymentArtifactAuthorityResponseCopyWithImpl<DeploymentArtifactAuthorityResponse>(this as DeploymentArtifactAuthorityResponse, _$identity);

  /// Serializes this DeploymentArtifactAuthorityResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DeploymentArtifactAuthorityResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.info, info) || other.info == info)&&(identical(other.error, error) || other.error == error)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl)&&(identical(other.artifactFamily, artifactFamily) || other.artifactFamily == artifactFamily)&&(identical(other.artifactKey, artifactKey) || other.artifactKey == artifactKey)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.payloadUrl, payloadUrl) || other.payloadUrl == payloadUrl)&&(identical(other.payloadSha256, payloadSha256) || other.payloadSha256 == payloadSha256)&&(identical(other.selectorKey, selectorKey) || other.selectorKey == selectorKey)&&(identical(other.targetRef, targetRef) || other.targetRef == targetRef)&&(identical(other.producer, producer) || other.producer == producer)&&(identical(other.nodePackageName, nodePackageName) || other.nodePackageName == nodePackageName)&&(identical(other.artifactLock, artifactLock) || other.artifactLock == artifactLock)&&(identical(other.target, target) || other.target == target));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,info,error,authoritySourceUrl,artifactFamily,artifactKey,channel,revisionId,payloadUrl,payloadSha256,selectorKey,targetRef,producer,nodePackageName,artifactLock,target);

@override
String toString() {
  return 'DeploymentArtifactAuthorityResponse(requestId: $requestId, success: $success, info: $info, error: $error, authoritySourceUrl: $authoritySourceUrl, artifactFamily: $artifactFamily, artifactKey: $artifactKey, channel: $channel, revisionId: $revisionId, payloadUrl: $payloadUrl, payloadSha256: $payloadSha256, selectorKey: $selectorKey, targetRef: $targetRef, producer: $producer, nodePackageName: $nodePackageName, artifactLock: $artifactLock, target: $target)';
}


}

/// @nodoc
abstract mixin class $DeploymentArtifactAuthorityResponseCopyWith<$Res>  {
  factory $DeploymentArtifactAuthorityResponseCopyWith(DeploymentArtifactAuthorityResponse value, $Res Function(DeploymentArtifactAuthorityResponse) _then) = _$DeploymentArtifactAuthorityResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? info, String? error, String authoritySourceUrl, String artifactFamily, String artifactKey, String channel, String revisionId, String payloadUrl, String payloadSha256, String selectorKey, String targetRef, DeploymentArtifactProducerProvenance producer, String nodePackageName, DeploymentArtifactLock artifactLock, DeploymentArtifactTarget target
});


$DeploymentArtifactProducerProvenanceCopyWith<$Res> get producer;$DeploymentArtifactLockCopyWith<$Res> get artifactLock;$DeploymentArtifactTargetCopyWith<$Res> get target;

}
/// @nodoc
class _$DeploymentArtifactAuthorityResponseCopyWithImpl<$Res>
    implements $DeploymentArtifactAuthorityResponseCopyWith<$Res> {
  _$DeploymentArtifactAuthorityResponseCopyWithImpl(this._self, this._then);

  final DeploymentArtifactAuthorityResponse _self;
  final $Res Function(DeploymentArtifactAuthorityResponse) _then;

/// Create a copy of DeploymentArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? success = null,Object? info = freezed,Object? error = freezed,Object? authoritySourceUrl = null,Object? artifactFamily = null,Object? artifactKey = null,Object? channel = null,Object? revisionId = null,Object? payloadUrl = null,Object? payloadSha256 = null,Object? selectorKey = null,Object? targetRef = null,Object? producer = null,Object? nodePackageName = null,Object? artifactLock = null,Object? target = null,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,info: freezed == info ? _self.info : info // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,authoritySourceUrl: null == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String,artifactFamily: null == artifactFamily ? _self.artifactFamily : artifactFamily // ignore: cast_nullable_to_non_nullable
as String,artifactKey: null == artifactKey ? _self.artifactKey : artifactKey // ignore: cast_nullable_to_non_nullable
as String,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,revisionId: null == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String,payloadUrl: null == payloadUrl ? _self.payloadUrl : payloadUrl // ignore: cast_nullable_to_non_nullable
as String,payloadSha256: null == payloadSha256 ? _self.payloadSha256 : payloadSha256 // ignore: cast_nullable_to_non_nullable
as String,selectorKey: null == selectorKey ? _self.selectorKey : selectorKey // ignore: cast_nullable_to_non_nullable
as String,targetRef: null == targetRef ? _self.targetRef : targetRef // ignore: cast_nullable_to_non_nullable
as String,producer: null == producer ? _self.producer : producer // ignore: cast_nullable_to_non_nullable
as DeploymentArtifactProducerProvenance,nodePackageName: null == nodePackageName ? _self.nodePackageName : nodePackageName // ignore: cast_nullable_to_non_nullable
as String,artifactLock: null == artifactLock ? _self.artifactLock : artifactLock // ignore: cast_nullable_to_non_nullable
as DeploymentArtifactLock,target: null == target ? _self.target : target // ignore: cast_nullable_to_non_nullable
as DeploymentArtifactTarget,
  ));
}
/// Create a copy of DeploymentArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$DeploymentArtifactProducerProvenanceCopyWith<$Res> get producer {
  
  return $DeploymentArtifactProducerProvenanceCopyWith<$Res>(_self.producer, (value) {
    return _then(_self.copyWith(producer: value));
  });
}/// Create a copy of DeploymentArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$DeploymentArtifactLockCopyWith<$Res> get artifactLock {
  
  return $DeploymentArtifactLockCopyWith<$Res>(_self.artifactLock, (value) {
    return _then(_self.copyWith(artifactLock: value));
  });
}/// Create a copy of DeploymentArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$DeploymentArtifactTargetCopyWith<$Res> get target {
  
  return $DeploymentArtifactTargetCopyWith<$Res>(_self.target, (value) {
    return _then(_self.copyWith(target: value));
  });
}
}


/// Adds pattern-matching-related methods to [DeploymentArtifactAuthorityResponse].
extension DeploymentArtifactAuthorityResponsePatterns on DeploymentArtifactAuthorityResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( ResolveDeploymentArtifactResponse value)?  resolveDeploymentArtifact,required TResult orElse(),}){
final _that = this;
switch (_that) {
case ResolveDeploymentArtifactResponse() when resolveDeploymentArtifact != null:
return resolveDeploymentArtifact(_that);case _:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( ResolveDeploymentArtifactResponse value)  resolveDeploymentArtifact,}){
final _that = this;
switch (_that) {
case ResolveDeploymentArtifactResponse():
return resolveDeploymentArtifact(_that);case _:
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( ResolveDeploymentArtifactResponse value)?  resolveDeploymentArtifact,}){
final _that = this;
switch (_that) {
case ResolveDeploymentArtifactResponse() when resolveDeploymentArtifact != null:
return resolveDeploymentArtifact(_that);case _:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String authoritySourceUrl,  String artifactFamily,  String artifactKey,  String channel,  String revisionId,  String payloadUrl,  String payloadSha256,  String selectorKey,  String targetRef,  DeploymentArtifactProducerProvenance producer,  String nodePackageName,  DeploymentArtifactLock artifactLock,  DeploymentArtifactTarget target)?  resolveDeploymentArtifact,required TResult orElse(),}) {final _that = this;
switch (_that) {
case ResolveDeploymentArtifactResponse() when resolveDeploymentArtifact != null:
return resolveDeploymentArtifact(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.artifactFamily,_that.artifactKey,_that.channel,_that.revisionId,_that.payloadUrl,_that.payloadSha256,_that.selectorKey,_that.targetRef,_that.producer,_that.nodePackageName,_that.artifactLock,_that.target);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String authoritySourceUrl,  String artifactFamily,  String artifactKey,  String channel,  String revisionId,  String payloadUrl,  String payloadSha256,  String selectorKey,  String targetRef,  DeploymentArtifactProducerProvenance producer,  String nodePackageName,  DeploymentArtifactLock artifactLock,  DeploymentArtifactTarget target)  resolveDeploymentArtifact,}) {final _that = this;
switch (_that) {
case ResolveDeploymentArtifactResponse():
return resolveDeploymentArtifact(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.artifactFamily,_that.artifactKey,_that.channel,_that.revisionId,_that.payloadUrl,_that.payloadSha256,_that.selectorKey,_that.targetRef,_that.producer,_that.nodePackageName,_that.artifactLock,_that.target);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String authoritySourceUrl,  String artifactFamily,  String artifactKey,  String channel,  String revisionId,  String payloadUrl,  String payloadSha256,  String selectorKey,  String targetRef,  DeploymentArtifactProducerProvenance producer,  String nodePackageName,  DeploymentArtifactLock artifactLock,  DeploymentArtifactTarget target)?  resolveDeploymentArtifact,}) {final _that = this;
switch (_that) {
case ResolveDeploymentArtifactResponse() when resolveDeploymentArtifact != null:
return resolveDeploymentArtifact(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.artifactFamily,_that.artifactKey,_that.channel,_that.revisionId,_that.payloadUrl,_that.payloadSha256,_that.selectorKey,_that.targetRef,_that.producer,_that.nodePackageName,_that.artifactLock,_that.target);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class ResolveDeploymentArtifactResponse implements DeploymentArtifactAuthorityResponse {
   ResolveDeploymentArtifactResponse({@UuidValueConverter() this.requestId, required this.success, this.info, this.error, required this.authoritySourceUrl, required this.artifactFamily, required this.artifactKey, required this.channel, required this.revisionId, required this.payloadUrl, required this.payloadSha256, required this.selectorKey, required this.targetRef, required this.producer, required this.nodePackageName, required this.artifactLock, required this.target});
  factory ResolveDeploymentArtifactResponse.fromJson(Map<String, dynamic> json) => _$ResolveDeploymentArtifactResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? info;
@override final  String? error;
@override final  String authoritySourceUrl;
@override final  String artifactFamily;
@override final  String artifactKey;
@override final  String channel;
@override final  String revisionId;
@override final  String payloadUrl;
@override final  String payloadSha256;
@override final  String selectorKey;
@override final  String targetRef;
@override final  DeploymentArtifactProducerProvenance producer;
@override final  String nodePackageName;
@override final  DeploymentArtifactLock artifactLock;
@override final  DeploymentArtifactTarget target;

/// Create a copy of DeploymentArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ResolveDeploymentArtifactResponseCopyWith<ResolveDeploymentArtifactResponse> get copyWith => _$ResolveDeploymentArtifactResponseCopyWithImpl<ResolveDeploymentArtifactResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ResolveDeploymentArtifactResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ResolveDeploymentArtifactResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.info, info) || other.info == info)&&(identical(other.error, error) || other.error == error)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl)&&(identical(other.artifactFamily, artifactFamily) || other.artifactFamily == artifactFamily)&&(identical(other.artifactKey, artifactKey) || other.artifactKey == artifactKey)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.payloadUrl, payloadUrl) || other.payloadUrl == payloadUrl)&&(identical(other.payloadSha256, payloadSha256) || other.payloadSha256 == payloadSha256)&&(identical(other.selectorKey, selectorKey) || other.selectorKey == selectorKey)&&(identical(other.targetRef, targetRef) || other.targetRef == targetRef)&&(identical(other.producer, producer) || other.producer == producer)&&(identical(other.nodePackageName, nodePackageName) || other.nodePackageName == nodePackageName)&&(identical(other.artifactLock, artifactLock) || other.artifactLock == artifactLock)&&(identical(other.target, target) || other.target == target));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,info,error,authoritySourceUrl,artifactFamily,artifactKey,channel,revisionId,payloadUrl,payloadSha256,selectorKey,targetRef,producer,nodePackageName,artifactLock,target);

@override
String toString() {
  return 'DeploymentArtifactAuthorityResponse.resolveDeploymentArtifact(requestId: $requestId, success: $success, info: $info, error: $error, authoritySourceUrl: $authoritySourceUrl, artifactFamily: $artifactFamily, artifactKey: $artifactKey, channel: $channel, revisionId: $revisionId, payloadUrl: $payloadUrl, payloadSha256: $payloadSha256, selectorKey: $selectorKey, targetRef: $targetRef, producer: $producer, nodePackageName: $nodePackageName, artifactLock: $artifactLock, target: $target)';
}


}

/// @nodoc
abstract mixin class $ResolveDeploymentArtifactResponseCopyWith<$Res> implements $DeploymentArtifactAuthorityResponseCopyWith<$Res> {
  factory $ResolveDeploymentArtifactResponseCopyWith(ResolveDeploymentArtifactResponse value, $Res Function(ResolveDeploymentArtifactResponse) _then) = _$ResolveDeploymentArtifactResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? info, String? error, String authoritySourceUrl, String artifactFamily, String artifactKey, String channel, String revisionId, String payloadUrl, String payloadSha256, String selectorKey, String targetRef, DeploymentArtifactProducerProvenance producer, String nodePackageName, DeploymentArtifactLock artifactLock, DeploymentArtifactTarget target
});


@override $DeploymentArtifactProducerProvenanceCopyWith<$Res> get producer;@override $DeploymentArtifactLockCopyWith<$Res> get artifactLock;@override $DeploymentArtifactTargetCopyWith<$Res> get target;

}
/// @nodoc
class _$ResolveDeploymentArtifactResponseCopyWithImpl<$Res>
    implements $ResolveDeploymentArtifactResponseCopyWith<$Res> {
  _$ResolveDeploymentArtifactResponseCopyWithImpl(this._self, this._then);

  final ResolveDeploymentArtifactResponse _self;
  final $Res Function(ResolveDeploymentArtifactResponse) _then;

/// Create a copy of DeploymentArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? info = freezed,Object? error = freezed,Object? authoritySourceUrl = null,Object? artifactFamily = null,Object? artifactKey = null,Object? channel = null,Object? revisionId = null,Object? payloadUrl = null,Object? payloadSha256 = null,Object? selectorKey = null,Object? targetRef = null,Object? producer = null,Object? nodePackageName = null,Object? artifactLock = null,Object? target = null,}) {
  return _then(ResolveDeploymentArtifactResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,info: freezed == info ? _self.info : info // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,authoritySourceUrl: null == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String,artifactFamily: null == artifactFamily ? _self.artifactFamily : artifactFamily // ignore: cast_nullable_to_non_nullable
as String,artifactKey: null == artifactKey ? _self.artifactKey : artifactKey // ignore: cast_nullable_to_non_nullable
as String,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,revisionId: null == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String,payloadUrl: null == payloadUrl ? _self.payloadUrl : payloadUrl // ignore: cast_nullable_to_non_nullable
as String,payloadSha256: null == payloadSha256 ? _self.payloadSha256 : payloadSha256 // ignore: cast_nullable_to_non_nullable
as String,selectorKey: null == selectorKey ? _self.selectorKey : selectorKey // ignore: cast_nullable_to_non_nullable
as String,targetRef: null == targetRef ? _self.targetRef : targetRef // ignore: cast_nullable_to_non_nullable
as String,producer: null == producer ? _self.producer : producer // ignore: cast_nullable_to_non_nullable
as DeploymentArtifactProducerProvenance,nodePackageName: null == nodePackageName ? _self.nodePackageName : nodePackageName // ignore: cast_nullable_to_non_nullable
as String,artifactLock: null == artifactLock ? _self.artifactLock : artifactLock // ignore: cast_nullable_to_non_nullable
as DeploymentArtifactLock,target: null == target ? _self.target : target // ignore: cast_nullable_to_non_nullable
as DeploymentArtifactTarget,
  ));
}

/// Create a copy of DeploymentArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$DeploymentArtifactProducerProvenanceCopyWith<$Res> get producer {
  
  return $DeploymentArtifactProducerProvenanceCopyWith<$Res>(_self.producer, (value) {
    return _then(_self.copyWith(producer: value));
  });
}/// Create a copy of DeploymentArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$DeploymentArtifactLockCopyWith<$Res> get artifactLock {
  
  return $DeploymentArtifactLockCopyWith<$Res>(_self.artifactLock, (value) {
    return _then(_self.copyWith(artifactLock: value));
  });
}/// Create a copy of DeploymentArtifactAuthorityResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$DeploymentArtifactTargetCopyWith<$Res> get target {
  
  return $DeploymentArtifactTargetCopyWith<$Res>(_self.target, (value) {
    return _then(_self.copyWith(target: value));
  });
}
}


/// @nodoc
mixin _$DeploymentArtifactProducerProvenance {

 String get producerKind; String? get producerRevisionId; String? get sourceRevisionId; String? get sourceRevisionKind; String? get materializationRef; String? get buildRef;
/// Create a copy of DeploymentArtifactProducerProvenance
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DeploymentArtifactProducerProvenanceCopyWith<DeploymentArtifactProducerProvenance> get copyWith => _$DeploymentArtifactProducerProvenanceCopyWithImpl<DeploymentArtifactProducerProvenance>(this as DeploymentArtifactProducerProvenance, _$identity);

  /// Serializes this DeploymentArtifactProducerProvenance to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DeploymentArtifactProducerProvenance&&(identical(other.producerKind, producerKind) || other.producerKind == producerKind)&&(identical(other.producerRevisionId, producerRevisionId) || other.producerRevisionId == producerRevisionId)&&(identical(other.sourceRevisionId, sourceRevisionId) || other.sourceRevisionId == sourceRevisionId)&&(identical(other.sourceRevisionKind, sourceRevisionKind) || other.sourceRevisionKind == sourceRevisionKind)&&(identical(other.materializationRef, materializationRef) || other.materializationRef == materializationRef)&&(identical(other.buildRef, buildRef) || other.buildRef == buildRef));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,producerKind,producerRevisionId,sourceRevisionId,sourceRevisionKind,materializationRef,buildRef);

@override
String toString() {
  return 'DeploymentArtifactProducerProvenance(producerKind: $producerKind, producerRevisionId: $producerRevisionId, sourceRevisionId: $sourceRevisionId, sourceRevisionKind: $sourceRevisionKind, materializationRef: $materializationRef, buildRef: $buildRef)';
}


}

/// @nodoc
abstract mixin class $DeploymentArtifactProducerProvenanceCopyWith<$Res>  {
  factory $DeploymentArtifactProducerProvenanceCopyWith(DeploymentArtifactProducerProvenance value, $Res Function(DeploymentArtifactProducerProvenance) _then) = _$DeploymentArtifactProducerProvenanceCopyWithImpl;
@useResult
$Res call({
 String producerKind, String? producerRevisionId, String? sourceRevisionId, String? sourceRevisionKind, String? materializationRef, String? buildRef
});




}
/// @nodoc
class _$DeploymentArtifactProducerProvenanceCopyWithImpl<$Res>
    implements $DeploymentArtifactProducerProvenanceCopyWith<$Res> {
  _$DeploymentArtifactProducerProvenanceCopyWithImpl(this._self, this._then);

  final DeploymentArtifactProducerProvenance _self;
  final $Res Function(DeploymentArtifactProducerProvenance) _then;

/// Create a copy of DeploymentArtifactProducerProvenance
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? producerKind = null,Object? producerRevisionId = freezed,Object? sourceRevisionId = freezed,Object? sourceRevisionKind = freezed,Object? materializationRef = freezed,Object? buildRef = freezed,}) {
  return _then(_self.copyWith(
producerKind: null == producerKind ? _self.producerKind : producerKind // ignore: cast_nullable_to_non_nullable
as String,producerRevisionId: freezed == producerRevisionId ? _self.producerRevisionId : producerRevisionId // ignore: cast_nullable_to_non_nullable
as String?,sourceRevisionId: freezed == sourceRevisionId ? _self.sourceRevisionId : sourceRevisionId // ignore: cast_nullable_to_non_nullable
as String?,sourceRevisionKind: freezed == sourceRevisionKind ? _self.sourceRevisionKind : sourceRevisionKind // ignore: cast_nullable_to_non_nullable
as String?,materializationRef: freezed == materializationRef ? _self.materializationRef : materializationRef // ignore: cast_nullable_to_non_nullable
as String?,buildRef: freezed == buildRef ? _self.buildRef : buildRef // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [DeploymentArtifactProducerProvenance].
extension DeploymentArtifactProducerProvenancePatterns on DeploymentArtifactProducerProvenance {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _DeploymentArtifactProducerProvenance value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _DeploymentArtifactProducerProvenance() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _DeploymentArtifactProducerProvenance value)  def,}){
final _that = this;
switch (_that) {
case _DeploymentArtifactProducerProvenance():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _DeploymentArtifactProducerProvenance value)?  def,}){
final _that = this;
switch (_that) {
case _DeploymentArtifactProducerProvenance() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String producerKind,  String? producerRevisionId,  String? sourceRevisionId,  String? sourceRevisionKind,  String? materializationRef,  String? buildRef)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _DeploymentArtifactProducerProvenance() when def != null:
return def(_that.producerKind,_that.producerRevisionId,_that.sourceRevisionId,_that.sourceRevisionKind,_that.materializationRef,_that.buildRef);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String producerKind,  String? producerRevisionId,  String? sourceRevisionId,  String? sourceRevisionKind,  String? materializationRef,  String? buildRef)  def,}) {final _that = this;
switch (_that) {
case _DeploymentArtifactProducerProvenance():
return def(_that.producerKind,_that.producerRevisionId,_that.sourceRevisionId,_that.sourceRevisionKind,_that.materializationRef,_that.buildRef);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String producerKind,  String? producerRevisionId,  String? sourceRevisionId,  String? sourceRevisionKind,  String? materializationRef,  String? buildRef)?  def,}) {final _that = this;
switch (_that) {
case _DeploymentArtifactProducerProvenance() when def != null:
return def(_that.producerKind,_that.producerRevisionId,_that.sourceRevisionId,_that.sourceRevisionKind,_that.materializationRef,_that.buildRef);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _DeploymentArtifactProducerProvenance implements DeploymentArtifactProducerProvenance {
   _DeploymentArtifactProducerProvenance({required this.producerKind, this.producerRevisionId, this.sourceRevisionId, this.sourceRevisionKind, this.materializationRef, this.buildRef});
  factory _DeploymentArtifactProducerProvenance.fromJson(Map<String, dynamic> json) => _$DeploymentArtifactProducerProvenanceFromJson(json);

@override final  String producerKind;
@override final  String? producerRevisionId;
@override final  String? sourceRevisionId;
@override final  String? sourceRevisionKind;
@override final  String? materializationRef;
@override final  String? buildRef;

/// Create a copy of DeploymentArtifactProducerProvenance
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$DeploymentArtifactProducerProvenanceCopyWith<_DeploymentArtifactProducerProvenance> get copyWith => __$DeploymentArtifactProducerProvenanceCopyWithImpl<_DeploymentArtifactProducerProvenance>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DeploymentArtifactProducerProvenanceToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _DeploymentArtifactProducerProvenance&&(identical(other.producerKind, producerKind) || other.producerKind == producerKind)&&(identical(other.producerRevisionId, producerRevisionId) || other.producerRevisionId == producerRevisionId)&&(identical(other.sourceRevisionId, sourceRevisionId) || other.sourceRevisionId == sourceRevisionId)&&(identical(other.sourceRevisionKind, sourceRevisionKind) || other.sourceRevisionKind == sourceRevisionKind)&&(identical(other.materializationRef, materializationRef) || other.materializationRef == materializationRef)&&(identical(other.buildRef, buildRef) || other.buildRef == buildRef));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,producerKind,producerRevisionId,sourceRevisionId,sourceRevisionKind,materializationRef,buildRef);

@override
String toString() {
  return 'DeploymentArtifactProducerProvenance.def(producerKind: $producerKind, producerRevisionId: $producerRevisionId, sourceRevisionId: $sourceRevisionId, sourceRevisionKind: $sourceRevisionKind, materializationRef: $materializationRef, buildRef: $buildRef)';
}


}

/// @nodoc
abstract mixin class _$DeploymentArtifactProducerProvenanceCopyWith<$Res> implements $DeploymentArtifactProducerProvenanceCopyWith<$Res> {
  factory _$DeploymentArtifactProducerProvenanceCopyWith(_DeploymentArtifactProducerProvenance value, $Res Function(_DeploymentArtifactProducerProvenance) _then) = __$DeploymentArtifactProducerProvenanceCopyWithImpl;
@override @useResult
$Res call({
 String producerKind, String? producerRevisionId, String? sourceRevisionId, String? sourceRevisionKind, String? materializationRef, String? buildRef
});




}
/// @nodoc
class __$DeploymentArtifactProducerProvenanceCopyWithImpl<$Res>
    implements _$DeploymentArtifactProducerProvenanceCopyWith<$Res> {
  __$DeploymentArtifactProducerProvenanceCopyWithImpl(this._self, this._then);

  final _DeploymentArtifactProducerProvenance _self;
  final $Res Function(_DeploymentArtifactProducerProvenance) _then;

/// Create a copy of DeploymentArtifactProducerProvenance
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? producerKind = null,Object? producerRevisionId = freezed,Object? sourceRevisionId = freezed,Object? sourceRevisionKind = freezed,Object? materializationRef = freezed,Object? buildRef = freezed,}) {
  return _then(_DeploymentArtifactProducerProvenance(
producerKind: null == producerKind ? _self.producerKind : producerKind // ignore: cast_nullable_to_non_nullable
as String,producerRevisionId: freezed == producerRevisionId ? _self.producerRevisionId : producerRevisionId // ignore: cast_nullable_to_non_nullable
as String?,sourceRevisionId: freezed == sourceRevisionId ? _self.sourceRevisionId : sourceRevisionId // ignore: cast_nullable_to_non_nullable
as String?,sourceRevisionKind: freezed == sourceRevisionKind ? _self.sourceRevisionKind : sourceRevisionKind // ignore: cast_nullable_to_non_nullable
as String?,materializationRef: freezed == materializationRef ? _self.materializationRef : materializationRef // ignore: cast_nullable_to_non_nullable
as String?,buildRef: freezed == buildRef ? _self.buildRef : buildRef // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$DeploymentArtifactLock {

 String get artifactFamily; String get artifactKey; String get channel; String get revisionId; String get payloadUrl; String get payloadSha256; String get payloadContractVersion;
/// Create a copy of DeploymentArtifactLock
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DeploymentArtifactLockCopyWith<DeploymentArtifactLock> get copyWith => _$DeploymentArtifactLockCopyWithImpl<DeploymentArtifactLock>(this as DeploymentArtifactLock, _$identity);

  /// Serializes this DeploymentArtifactLock to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DeploymentArtifactLock&&(identical(other.artifactFamily, artifactFamily) || other.artifactFamily == artifactFamily)&&(identical(other.artifactKey, artifactKey) || other.artifactKey == artifactKey)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.payloadUrl, payloadUrl) || other.payloadUrl == payloadUrl)&&(identical(other.payloadSha256, payloadSha256) || other.payloadSha256 == payloadSha256)&&(identical(other.payloadContractVersion, payloadContractVersion) || other.payloadContractVersion == payloadContractVersion));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,artifactFamily,artifactKey,channel,revisionId,payloadUrl,payloadSha256,payloadContractVersion);

@override
String toString() {
  return 'DeploymentArtifactLock(artifactFamily: $artifactFamily, artifactKey: $artifactKey, channel: $channel, revisionId: $revisionId, payloadUrl: $payloadUrl, payloadSha256: $payloadSha256, payloadContractVersion: $payloadContractVersion)';
}


}

/// @nodoc
abstract mixin class $DeploymentArtifactLockCopyWith<$Res>  {
  factory $DeploymentArtifactLockCopyWith(DeploymentArtifactLock value, $Res Function(DeploymentArtifactLock) _then) = _$DeploymentArtifactLockCopyWithImpl;
@useResult
$Res call({
 String artifactFamily, String artifactKey, String channel, String revisionId, String payloadUrl, String payloadSha256, String payloadContractVersion
});




}
/// @nodoc
class _$DeploymentArtifactLockCopyWithImpl<$Res>
    implements $DeploymentArtifactLockCopyWith<$Res> {
  _$DeploymentArtifactLockCopyWithImpl(this._self, this._then);

  final DeploymentArtifactLock _self;
  final $Res Function(DeploymentArtifactLock) _then;

/// Create a copy of DeploymentArtifactLock
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? artifactFamily = null,Object? artifactKey = null,Object? channel = null,Object? revisionId = null,Object? payloadUrl = null,Object? payloadSha256 = null,Object? payloadContractVersion = null,}) {
  return _then(_self.copyWith(
artifactFamily: null == artifactFamily ? _self.artifactFamily : artifactFamily // ignore: cast_nullable_to_non_nullable
as String,artifactKey: null == artifactKey ? _self.artifactKey : artifactKey // ignore: cast_nullable_to_non_nullable
as String,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,revisionId: null == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String,payloadUrl: null == payloadUrl ? _self.payloadUrl : payloadUrl // ignore: cast_nullable_to_non_nullable
as String,payloadSha256: null == payloadSha256 ? _self.payloadSha256 : payloadSha256 // ignore: cast_nullable_to_non_nullable
as String,payloadContractVersion: null == payloadContractVersion ? _self.payloadContractVersion : payloadContractVersion // ignore: cast_nullable_to_non_nullable
as String,
  ));
}

}


/// Adds pattern-matching-related methods to [DeploymentArtifactLock].
extension DeploymentArtifactLockPatterns on DeploymentArtifactLock {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _DeploymentArtifactLock value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _DeploymentArtifactLock() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _DeploymentArtifactLock value)  def,}){
final _that = this;
switch (_that) {
case _DeploymentArtifactLock():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _DeploymentArtifactLock value)?  def,}){
final _that = this;
switch (_that) {
case _DeploymentArtifactLock() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String artifactFamily,  String artifactKey,  String channel,  String revisionId,  String payloadUrl,  String payloadSha256,  String payloadContractVersion)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _DeploymentArtifactLock() when def != null:
return def(_that.artifactFamily,_that.artifactKey,_that.channel,_that.revisionId,_that.payloadUrl,_that.payloadSha256,_that.payloadContractVersion);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String artifactFamily,  String artifactKey,  String channel,  String revisionId,  String payloadUrl,  String payloadSha256,  String payloadContractVersion)  def,}) {final _that = this;
switch (_that) {
case _DeploymentArtifactLock():
return def(_that.artifactFamily,_that.artifactKey,_that.channel,_that.revisionId,_that.payloadUrl,_that.payloadSha256,_that.payloadContractVersion);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String artifactFamily,  String artifactKey,  String channel,  String revisionId,  String payloadUrl,  String payloadSha256,  String payloadContractVersion)?  def,}) {final _that = this;
switch (_that) {
case _DeploymentArtifactLock() when def != null:
return def(_that.artifactFamily,_that.artifactKey,_that.channel,_that.revisionId,_that.payloadUrl,_that.payloadSha256,_that.payloadContractVersion);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _DeploymentArtifactLock implements DeploymentArtifactLock {
   _DeploymentArtifactLock({required this.artifactFamily, required this.artifactKey, required this.channel, required this.revisionId, required this.payloadUrl, required this.payloadSha256, required this.payloadContractVersion});
  factory _DeploymentArtifactLock.fromJson(Map<String, dynamic> json) => _$DeploymentArtifactLockFromJson(json);

@override final  String artifactFamily;
@override final  String artifactKey;
@override final  String channel;
@override final  String revisionId;
@override final  String payloadUrl;
@override final  String payloadSha256;
@override final  String payloadContractVersion;

/// Create a copy of DeploymentArtifactLock
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$DeploymentArtifactLockCopyWith<_DeploymentArtifactLock> get copyWith => __$DeploymentArtifactLockCopyWithImpl<_DeploymentArtifactLock>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DeploymentArtifactLockToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _DeploymentArtifactLock&&(identical(other.artifactFamily, artifactFamily) || other.artifactFamily == artifactFamily)&&(identical(other.artifactKey, artifactKey) || other.artifactKey == artifactKey)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.payloadUrl, payloadUrl) || other.payloadUrl == payloadUrl)&&(identical(other.payloadSha256, payloadSha256) || other.payloadSha256 == payloadSha256)&&(identical(other.payloadContractVersion, payloadContractVersion) || other.payloadContractVersion == payloadContractVersion));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,artifactFamily,artifactKey,channel,revisionId,payloadUrl,payloadSha256,payloadContractVersion);

@override
String toString() {
  return 'DeploymentArtifactLock.def(artifactFamily: $artifactFamily, artifactKey: $artifactKey, channel: $channel, revisionId: $revisionId, payloadUrl: $payloadUrl, payloadSha256: $payloadSha256, payloadContractVersion: $payloadContractVersion)';
}


}

/// @nodoc
abstract mixin class _$DeploymentArtifactLockCopyWith<$Res> implements $DeploymentArtifactLockCopyWith<$Res> {
  factory _$DeploymentArtifactLockCopyWith(_DeploymentArtifactLock value, $Res Function(_DeploymentArtifactLock) _then) = __$DeploymentArtifactLockCopyWithImpl;
@override @useResult
$Res call({
 String artifactFamily, String artifactKey, String channel, String revisionId, String payloadUrl, String payloadSha256, String payloadContractVersion
});




}
/// @nodoc
class __$DeploymentArtifactLockCopyWithImpl<$Res>
    implements _$DeploymentArtifactLockCopyWith<$Res> {
  __$DeploymentArtifactLockCopyWithImpl(this._self, this._then);

  final _DeploymentArtifactLock _self;
  final $Res Function(_DeploymentArtifactLock) _then;

/// Create a copy of DeploymentArtifactLock
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? artifactFamily = null,Object? artifactKey = null,Object? channel = null,Object? revisionId = null,Object? payloadUrl = null,Object? payloadSha256 = null,Object? payloadContractVersion = null,}) {
  return _then(_DeploymentArtifactLock(
artifactFamily: null == artifactFamily ? _self.artifactFamily : artifactFamily // ignore: cast_nullable_to_non_nullable
as String,artifactKey: null == artifactKey ? _self.artifactKey : artifactKey // ignore: cast_nullable_to_non_nullable
as String,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,revisionId: null == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String,payloadUrl: null == payloadUrl ? _self.payloadUrl : payloadUrl // ignore: cast_nullable_to_non_nullable
as String,payloadSha256: null == payloadSha256 ? _self.payloadSha256 : payloadSha256 // ignore: cast_nullable_to_non_nullable
as String,payloadContractVersion: null == payloadContractVersion ? _self.payloadContractVersion : payloadContractVersion // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}


/// @nodoc
mixin _$DeploymentArtifactTarget {

 String get selectorKey; String get targetRef; String get nodePackageName;
/// Create a copy of DeploymentArtifactTarget
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DeploymentArtifactTargetCopyWith<DeploymentArtifactTarget> get copyWith => _$DeploymentArtifactTargetCopyWithImpl<DeploymentArtifactTarget>(this as DeploymentArtifactTarget, _$identity);

  /// Serializes this DeploymentArtifactTarget to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DeploymentArtifactTarget&&(identical(other.selectorKey, selectorKey) || other.selectorKey == selectorKey)&&(identical(other.targetRef, targetRef) || other.targetRef == targetRef)&&(identical(other.nodePackageName, nodePackageName) || other.nodePackageName == nodePackageName));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,selectorKey,targetRef,nodePackageName);

@override
String toString() {
  return 'DeploymentArtifactTarget(selectorKey: $selectorKey, targetRef: $targetRef, nodePackageName: $nodePackageName)';
}


}

/// @nodoc
abstract mixin class $DeploymentArtifactTargetCopyWith<$Res>  {
  factory $DeploymentArtifactTargetCopyWith(DeploymentArtifactTarget value, $Res Function(DeploymentArtifactTarget) _then) = _$DeploymentArtifactTargetCopyWithImpl;
@useResult
$Res call({
 String selectorKey, String targetRef, String nodePackageName
});




}
/// @nodoc
class _$DeploymentArtifactTargetCopyWithImpl<$Res>
    implements $DeploymentArtifactTargetCopyWith<$Res> {
  _$DeploymentArtifactTargetCopyWithImpl(this._self, this._then);

  final DeploymentArtifactTarget _self;
  final $Res Function(DeploymentArtifactTarget) _then;

/// Create a copy of DeploymentArtifactTarget
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? selectorKey = null,Object? targetRef = null,Object? nodePackageName = null,}) {
  return _then(_self.copyWith(
selectorKey: null == selectorKey ? _self.selectorKey : selectorKey // ignore: cast_nullable_to_non_nullable
as String,targetRef: null == targetRef ? _self.targetRef : targetRef // ignore: cast_nullable_to_non_nullable
as String,nodePackageName: null == nodePackageName ? _self.nodePackageName : nodePackageName // ignore: cast_nullable_to_non_nullable
as String,
  ));
}

}


/// Adds pattern-matching-related methods to [DeploymentArtifactTarget].
extension DeploymentArtifactTargetPatterns on DeploymentArtifactTarget {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _DeploymentArtifactTarget value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _DeploymentArtifactTarget() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _DeploymentArtifactTarget value)  def,}){
final _that = this;
switch (_that) {
case _DeploymentArtifactTarget():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _DeploymentArtifactTarget value)?  def,}){
final _that = this;
switch (_that) {
case _DeploymentArtifactTarget() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String selectorKey,  String targetRef,  String nodePackageName)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _DeploymentArtifactTarget() when def != null:
return def(_that.selectorKey,_that.targetRef,_that.nodePackageName);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String selectorKey,  String targetRef,  String nodePackageName)  def,}) {final _that = this;
switch (_that) {
case _DeploymentArtifactTarget():
return def(_that.selectorKey,_that.targetRef,_that.nodePackageName);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String selectorKey,  String targetRef,  String nodePackageName)?  def,}) {final _that = this;
switch (_that) {
case _DeploymentArtifactTarget() when def != null:
return def(_that.selectorKey,_that.targetRef,_that.nodePackageName);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _DeploymentArtifactTarget implements DeploymentArtifactTarget {
   _DeploymentArtifactTarget({required this.selectorKey, required this.targetRef, required this.nodePackageName});
  factory _DeploymentArtifactTarget.fromJson(Map<String, dynamic> json) => _$DeploymentArtifactTargetFromJson(json);

@override final  String selectorKey;
@override final  String targetRef;
@override final  String nodePackageName;

/// Create a copy of DeploymentArtifactTarget
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$DeploymentArtifactTargetCopyWith<_DeploymentArtifactTarget> get copyWith => __$DeploymentArtifactTargetCopyWithImpl<_DeploymentArtifactTarget>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DeploymentArtifactTargetToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _DeploymentArtifactTarget&&(identical(other.selectorKey, selectorKey) || other.selectorKey == selectorKey)&&(identical(other.targetRef, targetRef) || other.targetRef == targetRef)&&(identical(other.nodePackageName, nodePackageName) || other.nodePackageName == nodePackageName));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,selectorKey,targetRef,nodePackageName);

@override
String toString() {
  return 'DeploymentArtifactTarget.def(selectorKey: $selectorKey, targetRef: $targetRef, nodePackageName: $nodePackageName)';
}


}

/// @nodoc
abstract mixin class _$DeploymentArtifactTargetCopyWith<$Res> implements $DeploymentArtifactTargetCopyWith<$Res> {
  factory _$DeploymentArtifactTargetCopyWith(_DeploymentArtifactTarget value, $Res Function(_DeploymentArtifactTarget) _then) = __$DeploymentArtifactTargetCopyWithImpl;
@override @useResult
$Res call({
 String selectorKey, String targetRef, String nodePackageName
});




}
/// @nodoc
class __$DeploymentArtifactTargetCopyWithImpl<$Res>
    implements _$DeploymentArtifactTargetCopyWith<$Res> {
  __$DeploymentArtifactTargetCopyWithImpl(this._self, this._then);

  final _DeploymentArtifactTarget _self;
  final $Res Function(_DeploymentArtifactTarget) _then;

/// Create a copy of DeploymentArtifactTarget
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? selectorKey = null,Object? targetRef = null,Object? nodePackageName = null,}) {
  return _then(_DeploymentArtifactTarget(
selectorKey: null == selectorKey ? _self.selectorKey : selectorKey // ignore: cast_nullable_to_non_nullable
as String,targetRef: null == targetRef ? _self.targetRef : targetRef // ignore: cast_nullable_to_non_nullable
as String,nodePackageName: null == nodePackageName ? _self.nodePackageName : nodePackageName // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}

// dart format on
