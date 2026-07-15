// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'package_distribution_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;
CodePackageServiceRequest _$CodePackageServiceRequestFromJson(
  Map<String, dynamic> json
) {
        switch (json['operation']) {
                  case 'discover_code_package_channel_heads':
          return DiscoverCodePackageChannelHeadsRequest.fromJson(
            json
          );
                case 'search_code_package':
          return SearchCodePackageRequest.fromJson(
            json
          );
                case 'describe_code_package':
          return DescribeCodePackageRequest.fromJson(
            json
          );
                case 'resolve_code_package':
          return ResolveCodePackageRequest.fromJson(
            json
          );
                case 'download_code_package':
          return DownloadCodePackageRequest.fromJson(
            json
          );
                case 'publish_code_package':
          return PublishCodePackageRequest.fromJson(
            json
          );
        
          default:
            throw CheckedFromJsonException(
  json,
  'operation',
  'CodePackageServiceRequest',
  'Invalid union type "${json['operation']}"!'
);
        }
      
}

/// @nodoc
mixin _$CodePackageServiceRequest {

@UuidValueConverter() UuidValue? get requestId; String? get authorityBaseUrl; String? get indexUrl;
/// Create a copy of CodePackageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$CodePackageServiceRequestCopyWith<CodePackageServiceRequest> get copyWith => _$CodePackageServiceRequestCopyWithImpl<CodePackageServiceRequest>(this as CodePackageServiceRequest, _$identity);

  /// Serializes this CodePackageServiceRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is CodePackageServiceRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.authorityBaseUrl, authorityBaseUrl) || other.authorityBaseUrl == authorityBaseUrl)&&(identical(other.indexUrl, indexUrl) || other.indexUrl == indexUrl));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,authorityBaseUrl,indexUrl);

@override
String toString() {
  return 'CodePackageServiceRequest(requestId: $requestId, authorityBaseUrl: $authorityBaseUrl, indexUrl: $indexUrl)';
}


}

/// @nodoc
abstract mixin class $CodePackageServiceRequestCopyWith<$Res>  {
  factory $CodePackageServiceRequestCopyWith(CodePackageServiceRequest value, $Res Function(CodePackageServiceRequest) _then) = _$CodePackageServiceRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, String? authorityBaseUrl, String? indexUrl
});




}
/// @nodoc
class _$CodePackageServiceRequestCopyWithImpl<$Res>
    implements $CodePackageServiceRequestCopyWith<$Res> {
  _$CodePackageServiceRequestCopyWithImpl(this._self, this._then);

  final CodePackageServiceRequest _self;
  final $Res Function(CodePackageServiceRequest) _then;

/// Create a copy of CodePackageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? authorityBaseUrl = freezed,Object? indexUrl = freezed,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,authorityBaseUrl: freezed == authorityBaseUrl ? _self.authorityBaseUrl : authorityBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,indexUrl: freezed == indexUrl ? _self.indexUrl : indexUrl // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [CodePackageServiceRequest].
extension CodePackageServiceRequestPatterns on CodePackageServiceRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( DiscoverCodePackageChannelHeadsRequest value)?  discoverCodePackageChannelHeads,TResult Function( SearchCodePackageRequest value)?  searchCodePackage,TResult Function( DescribeCodePackageRequest value)?  describeCodePackage,TResult Function( ResolveCodePackageRequest value)?  resolveCodePackage,TResult Function( DownloadCodePackageRequest value)?  downloadCodePackage,TResult Function( PublishCodePackageRequest value)?  publishCodePackage,required TResult orElse(),}){
final _that = this;
switch (_that) {
case DiscoverCodePackageChannelHeadsRequest() when discoverCodePackageChannelHeads != null:
return discoverCodePackageChannelHeads(_that);case SearchCodePackageRequest() when searchCodePackage != null:
return searchCodePackage(_that);case DescribeCodePackageRequest() when describeCodePackage != null:
return describeCodePackage(_that);case ResolveCodePackageRequest() when resolveCodePackage != null:
return resolveCodePackage(_that);case DownloadCodePackageRequest() when downloadCodePackage != null:
return downloadCodePackage(_that);case PublishCodePackageRequest() when publishCodePackage != null:
return publishCodePackage(_that);case _:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( DiscoverCodePackageChannelHeadsRequest value)  discoverCodePackageChannelHeads,required TResult Function( SearchCodePackageRequest value)  searchCodePackage,required TResult Function( DescribeCodePackageRequest value)  describeCodePackage,required TResult Function( ResolveCodePackageRequest value)  resolveCodePackage,required TResult Function( DownloadCodePackageRequest value)  downloadCodePackage,required TResult Function( PublishCodePackageRequest value)  publishCodePackage,}){
final _that = this;
switch (_that) {
case DiscoverCodePackageChannelHeadsRequest():
return discoverCodePackageChannelHeads(_that);case SearchCodePackageRequest():
return searchCodePackage(_that);case DescribeCodePackageRequest():
return describeCodePackage(_that);case ResolveCodePackageRequest():
return resolveCodePackage(_that);case DownloadCodePackageRequest():
return downloadCodePackage(_that);case PublishCodePackageRequest():
return publishCodePackage(_that);case _:
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( DiscoverCodePackageChannelHeadsRequest value)?  discoverCodePackageChannelHeads,TResult? Function( SearchCodePackageRequest value)?  searchCodePackage,TResult? Function( DescribeCodePackageRequest value)?  describeCodePackage,TResult? Function( ResolveCodePackageRequest value)?  resolveCodePackage,TResult? Function( DownloadCodePackageRequest value)?  downloadCodePackage,TResult? Function( PublishCodePackageRequest value)?  publishCodePackage,}){
final _that = this;
switch (_that) {
case DiscoverCodePackageChannelHeadsRequest() when discoverCodePackageChannelHeads != null:
return discoverCodePackageChannelHeads(_that);case SearchCodePackageRequest() when searchCodePackage != null:
return searchCodePackage(_that);case DescribeCodePackageRequest() when describeCodePackage != null:
return describeCodePackage(_that);case ResolveCodePackageRequest() when resolveCodePackage != null:
return resolveCodePackage(_that);case DownloadCodePackageRequest() when downloadCodePackage != null:
return downloadCodePackage(_that);case PublishCodePackageRequest() when publishCodePackage != null:
return publishCodePackage(_that);case _:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  String? query,  String? packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable)  CodeLanguage? language,  String? surface,  String? channel,  String? authorityBaseUrl,  String? indexUrl,  int limit)?  discoverCodePackageChannelHeads,TResult Function(@UuidValueConverter()  UuidValue? requestId,  String? query,  String? packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable)  CodeLanguage? language,  String? surface,  String channel,  String? authorityBaseUrl,  String? indexUrl,  int limit)?  searchCodePackage,TResult Function(@UuidValueConverter()  UuidValue? requestId,  CodePackageRef selector,  String? authorityBaseUrl,  String? indexUrl)?  describeCodePackage,TResult Function(@UuidValueConverter()  UuidValue? requestId,  CodePackageRef selector,  String? authorityBaseUrl,  String? indexUrl)?  resolveCodePackage,TResult Function(@UuidValueConverter()  UuidValue? requestId,  CodePackageRef selector,  String? authorityBaseUrl,  String? indexUrl)?  downloadCodePackage,TResult Function(@UuidValueConverter()  UuidValue? requestId,  CodePackageDescriptor descriptor,  CodePackageArtifactLock artifactLock,  String channel,  String? authorityBaseUrl,  String? indexUrl,  String? publisherExecutionId,  String? idempotencyKey)?  publishCodePackage,required TResult orElse(),}) {final _that = this;
switch (_that) {
case DiscoverCodePackageChannelHeadsRequest() when discoverCodePackageChannelHeads != null:
return discoverCodePackageChannelHeads(_that.requestId,_that.query,_that.packageName,_that.language,_that.surface,_that.channel,_that.authorityBaseUrl,_that.indexUrl,_that.limit);case SearchCodePackageRequest() when searchCodePackage != null:
return searchCodePackage(_that.requestId,_that.query,_that.packageName,_that.language,_that.surface,_that.channel,_that.authorityBaseUrl,_that.indexUrl,_that.limit);case DescribeCodePackageRequest() when describeCodePackage != null:
return describeCodePackage(_that.requestId,_that.selector,_that.authorityBaseUrl,_that.indexUrl);case ResolveCodePackageRequest() when resolveCodePackage != null:
return resolveCodePackage(_that.requestId,_that.selector,_that.authorityBaseUrl,_that.indexUrl);case DownloadCodePackageRequest() when downloadCodePackage != null:
return downloadCodePackage(_that.requestId,_that.selector,_that.authorityBaseUrl,_that.indexUrl);case PublishCodePackageRequest() when publishCodePackage != null:
return publishCodePackage(_that.requestId,_that.descriptor,_that.artifactLock,_that.channel,_that.authorityBaseUrl,_that.indexUrl,_that.publisherExecutionId,_that.idempotencyKey);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  String? query,  String? packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable)  CodeLanguage? language,  String? surface,  String? channel,  String? authorityBaseUrl,  String? indexUrl,  int limit)  discoverCodePackageChannelHeads,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  String? query,  String? packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable)  CodeLanguage? language,  String? surface,  String channel,  String? authorityBaseUrl,  String? indexUrl,  int limit)  searchCodePackage,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  CodePackageRef selector,  String? authorityBaseUrl,  String? indexUrl)  describeCodePackage,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  CodePackageRef selector,  String? authorityBaseUrl,  String? indexUrl)  resolveCodePackage,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  CodePackageRef selector,  String? authorityBaseUrl,  String? indexUrl)  downloadCodePackage,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  CodePackageDescriptor descriptor,  CodePackageArtifactLock artifactLock,  String channel,  String? authorityBaseUrl,  String? indexUrl,  String? publisherExecutionId,  String? idempotencyKey)  publishCodePackage,}) {final _that = this;
switch (_that) {
case DiscoverCodePackageChannelHeadsRequest():
return discoverCodePackageChannelHeads(_that.requestId,_that.query,_that.packageName,_that.language,_that.surface,_that.channel,_that.authorityBaseUrl,_that.indexUrl,_that.limit);case SearchCodePackageRequest():
return searchCodePackage(_that.requestId,_that.query,_that.packageName,_that.language,_that.surface,_that.channel,_that.authorityBaseUrl,_that.indexUrl,_that.limit);case DescribeCodePackageRequest():
return describeCodePackage(_that.requestId,_that.selector,_that.authorityBaseUrl,_that.indexUrl);case ResolveCodePackageRequest():
return resolveCodePackage(_that.requestId,_that.selector,_that.authorityBaseUrl,_that.indexUrl);case DownloadCodePackageRequest():
return downloadCodePackage(_that.requestId,_that.selector,_that.authorityBaseUrl,_that.indexUrl);case PublishCodePackageRequest():
return publishCodePackage(_that.requestId,_that.descriptor,_that.artifactLock,_that.channel,_that.authorityBaseUrl,_that.indexUrl,_that.publisherExecutionId,_that.idempotencyKey);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  String? query,  String? packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable)  CodeLanguage? language,  String? surface,  String? channel,  String? authorityBaseUrl,  String? indexUrl,  int limit)?  discoverCodePackageChannelHeads,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  String? query,  String? packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable)  CodeLanguage? language,  String? surface,  String channel,  String? authorityBaseUrl,  String? indexUrl,  int limit)?  searchCodePackage,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  CodePackageRef selector,  String? authorityBaseUrl,  String? indexUrl)?  describeCodePackage,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  CodePackageRef selector,  String? authorityBaseUrl,  String? indexUrl)?  resolveCodePackage,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  CodePackageRef selector,  String? authorityBaseUrl,  String? indexUrl)?  downloadCodePackage,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  CodePackageDescriptor descriptor,  CodePackageArtifactLock artifactLock,  String channel,  String? authorityBaseUrl,  String? indexUrl,  String? publisherExecutionId,  String? idempotencyKey)?  publishCodePackage,}) {final _that = this;
switch (_that) {
case DiscoverCodePackageChannelHeadsRequest() when discoverCodePackageChannelHeads != null:
return discoverCodePackageChannelHeads(_that.requestId,_that.query,_that.packageName,_that.language,_that.surface,_that.channel,_that.authorityBaseUrl,_that.indexUrl,_that.limit);case SearchCodePackageRequest() when searchCodePackage != null:
return searchCodePackage(_that.requestId,_that.query,_that.packageName,_that.language,_that.surface,_that.channel,_that.authorityBaseUrl,_that.indexUrl,_that.limit);case DescribeCodePackageRequest() when describeCodePackage != null:
return describeCodePackage(_that.requestId,_that.selector,_that.authorityBaseUrl,_that.indexUrl);case ResolveCodePackageRequest() when resolveCodePackage != null:
return resolveCodePackage(_that.requestId,_that.selector,_that.authorityBaseUrl,_that.indexUrl);case DownloadCodePackageRequest() when downloadCodePackage != null:
return downloadCodePackage(_that.requestId,_that.selector,_that.authorityBaseUrl,_that.indexUrl);case PublishCodePackageRequest() when publishCodePackage != null:
return publishCodePackage(_that.requestId,_that.descriptor,_that.artifactLock,_that.channel,_that.authorityBaseUrl,_that.indexUrl,_that.publisherExecutionId,_that.idempotencyKey);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DiscoverCodePackageChannelHeadsRequest implements CodePackageServiceRequest {
   DiscoverCodePackageChannelHeadsRequest({@UuidValueConverter() this.requestId, this.query, this.packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable) this.language, this.surface, this.channel, this.authorityBaseUrl, this.indexUrl, required this.limit, final  String? $type}): $type = $type ?? 'discover_code_package_channel_heads';
  factory DiscoverCodePackageChannelHeadsRequest.fromJson(Map<String, dynamic> json) => _$DiscoverCodePackageChannelHeadsRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
 final  String? query;
 final  String? packageName;
@JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable) final  CodeLanguage? language;
 final  String? surface;
 final  String? channel;
@override final  String? authorityBaseUrl;
@override final  String? indexUrl;
 final  int limit;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of CodePackageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DiscoverCodePackageChannelHeadsRequestCopyWith<DiscoverCodePackageChannelHeadsRequest> get copyWith => _$DiscoverCodePackageChannelHeadsRequestCopyWithImpl<DiscoverCodePackageChannelHeadsRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DiscoverCodePackageChannelHeadsRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DiscoverCodePackageChannelHeadsRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.query, query) || other.query == query)&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.language, language) || other.language == language)&&(identical(other.surface, surface) || other.surface == surface)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.authorityBaseUrl, authorityBaseUrl) || other.authorityBaseUrl == authorityBaseUrl)&&(identical(other.indexUrl, indexUrl) || other.indexUrl == indexUrl)&&(identical(other.limit, limit) || other.limit == limit));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,query,packageName,language,surface,channel,authorityBaseUrl,indexUrl,limit);

@override
String toString() {
  return 'CodePackageServiceRequest.discoverCodePackageChannelHeads(requestId: $requestId, query: $query, packageName: $packageName, language: $language, surface: $surface, channel: $channel, authorityBaseUrl: $authorityBaseUrl, indexUrl: $indexUrl, limit: $limit)';
}


}

/// @nodoc
abstract mixin class $DiscoverCodePackageChannelHeadsRequestCopyWith<$Res> implements $CodePackageServiceRequestCopyWith<$Res> {
  factory $DiscoverCodePackageChannelHeadsRequestCopyWith(DiscoverCodePackageChannelHeadsRequest value, $Res Function(DiscoverCodePackageChannelHeadsRequest) _then) = _$DiscoverCodePackageChannelHeadsRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, String? query, String? packageName,@JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable) CodeLanguage? language, String? surface, String? channel, String? authorityBaseUrl, String? indexUrl, int limit
});




}
/// @nodoc
class _$DiscoverCodePackageChannelHeadsRequestCopyWithImpl<$Res>
    implements $DiscoverCodePackageChannelHeadsRequestCopyWith<$Res> {
  _$DiscoverCodePackageChannelHeadsRequestCopyWithImpl(this._self, this._then);

  final DiscoverCodePackageChannelHeadsRequest _self;
  final $Res Function(DiscoverCodePackageChannelHeadsRequest) _then;

/// Create a copy of CodePackageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? query = freezed,Object? packageName = freezed,Object? language = freezed,Object? surface = freezed,Object? channel = freezed,Object? authorityBaseUrl = freezed,Object? indexUrl = freezed,Object? limit = null,}) {
  return _then(DiscoverCodePackageChannelHeadsRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,query: freezed == query ? _self.query : query // ignore: cast_nullable_to_non_nullable
as String?,packageName: freezed == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String?,language: freezed == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as CodeLanguage?,surface: freezed == surface ? _self.surface : surface // ignore: cast_nullable_to_non_nullable
as String?,channel: freezed == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String?,authorityBaseUrl: freezed == authorityBaseUrl ? _self.authorityBaseUrl : authorityBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,indexUrl: freezed == indexUrl ? _self.indexUrl : indexUrl // ignore: cast_nullable_to_non_nullable
as String?,limit: null == limit ? _self.limit : limit // ignore: cast_nullable_to_non_nullable
as int,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class SearchCodePackageRequest implements CodePackageServiceRequest {
   SearchCodePackageRequest({@UuidValueConverter() this.requestId, this.query, this.packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable) this.language, this.surface, required this.channel, this.authorityBaseUrl, this.indexUrl, required this.limit, final  String? $type}): $type = $type ?? 'search_code_package';
  factory SearchCodePackageRequest.fromJson(Map<String, dynamic> json) => _$SearchCodePackageRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
 final  String? query;
 final  String? packageName;
@JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable) final  CodeLanguage? language;
 final  String? surface;
 final  String channel;
@override final  String? authorityBaseUrl;
@override final  String? indexUrl;
 final  int limit;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of CodePackageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$SearchCodePackageRequestCopyWith<SearchCodePackageRequest> get copyWith => _$SearchCodePackageRequestCopyWithImpl<SearchCodePackageRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$SearchCodePackageRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is SearchCodePackageRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.query, query) || other.query == query)&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.language, language) || other.language == language)&&(identical(other.surface, surface) || other.surface == surface)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.authorityBaseUrl, authorityBaseUrl) || other.authorityBaseUrl == authorityBaseUrl)&&(identical(other.indexUrl, indexUrl) || other.indexUrl == indexUrl)&&(identical(other.limit, limit) || other.limit == limit));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,query,packageName,language,surface,channel,authorityBaseUrl,indexUrl,limit);

@override
String toString() {
  return 'CodePackageServiceRequest.searchCodePackage(requestId: $requestId, query: $query, packageName: $packageName, language: $language, surface: $surface, channel: $channel, authorityBaseUrl: $authorityBaseUrl, indexUrl: $indexUrl, limit: $limit)';
}


}

/// @nodoc
abstract mixin class $SearchCodePackageRequestCopyWith<$Res> implements $CodePackageServiceRequestCopyWith<$Res> {
  factory $SearchCodePackageRequestCopyWith(SearchCodePackageRequest value, $Res Function(SearchCodePackageRequest) _then) = _$SearchCodePackageRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, String? query, String? packageName,@JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable) CodeLanguage? language, String? surface, String channel, String? authorityBaseUrl, String? indexUrl, int limit
});




}
/// @nodoc
class _$SearchCodePackageRequestCopyWithImpl<$Res>
    implements $SearchCodePackageRequestCopyWith<$Res> {
  _$SearchCodePackageRequestCopyWithImpl(this._self, this._then);

  final SearchCodePackageRequest _self;
  final $Res Function(SearchCodePackageRequest) _then;

/// Create a copy of CodePackageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? query = freezed,Object? packageName = freezed,Object? language = freezed,Object? surface = freezed,Object? channel = null,Object? authorityBaseUrl = freezed,Object? indexUrl = freezed,Object? limit = null,}) {
  return _then(SearchCodePackageRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,query: freezed == query ? _self.query : query // ignore: cast_nullable_to_non_nullable
as String?,packageName: freezed == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String?,language: freezed == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as CodeLanguage?,surface: freezed == surface ? _self.surface : surface // ignore: cast_nullable_to_non_nullable
as String?,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,authorityBaseUrl: freezed == authorityBaseUrl ? _self.authorityBaseUrl : authorityBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,indexUrl: freezed == indexUrl ? _self.indexUrl : indexUrl // ignore: cast_nullable_to_non_nullable
as String?,limit: null == limit ? _self.limit : limit // ignore: cast_nullable_to_non_nullable
as int,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DescribeCodePackageRequest implements CodePackageServiceRequest {
   DescribeCodePackageRequest({@UuidValueConverter() this.requestId, required this.selector, this.authorityBaseUrl, this.indexUrl, final  String? $type}): $type = $type ?? 'describe_code_package';
  factory DescribeCodePackageRequest.fromJson(Map<String, dynamic> json) => _$DescribeCodePackageRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
 final  CodePackageRef selector;
@override final  String? authorityBaseUrl;
@override final  String? indexUrl;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of CodePackageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DescribeCodePackageRequestCopyWith<DescribeCodePackageRequest> get copyWith => _$DescribeCodePackageRequestCopyWithImpl<DescribeCodePackageRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DescribeCodePackageRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DescribeCodePackageRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.selector, selector) || other.selector == selector)&&(identical(other.authorityBaseUrl, authorityBaseUrl) || other.authorityBaseUrl == authorityBaseUrl)&&(identical(other.indexUrl, indexUrl) || other.indexUrl == indexUrl));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,selector,authorityBaseUrl,indexUrl);

@override
String toString() {
  return 'CodePackageServiceRequest.describeCodePackage(requestId: $requestId, selector: $selector, authorityBaseUrl: $authorityBaseUrl, indexUrl: $indexUrl)';
}


}

/// @nodoc
abstract mixin class $DescribeCodePackageRequestCopyWith<$Res> implements $CodePackageServiceRequestCopyWith<$Res> {
  factory $DescribeCodePackageRequestCopyWith(DescribeCodePackageRequest value, $Res Function(DescribeCodePackageRequest) _then) = _$DescribeCodePackageRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, CodePackageRef selector, String? authorityBaseUrl, String? indexUrl
});


$CodePackageRefCopyWith<$Res> get selector;

}
/// @nodoc
class _$DescribeCodePackageRequestCopyWithImpl<$Res>
    implements $DescribeCodePackageRequestCopyWith<$Res> {
  _$DescribeCodePackageRequestCopyWithImpl(this._self, this._then);

  final DescribeCodePackageRequest _self;
  final $Res Function(DescribeCodePackageRequest) _then;

/// Create a copy of CodePackageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? selector = null,Object? authorityBaseUrl = freezed,Object? indexUrl = freezed,}) {
  return _then(DescribeCodePackageRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,selector: null == selector ? _self.selector : selector // ignore: cast_nullable_to_non_nullable
as CodePackageRef,authorityBaseUrl: freezed == authorityBaseUrl ? _self.authorityBaseUrl : authorityBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,indexUrl: freezed == indexUrl ? _self.indexUrl : indexUrl // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

/// Create a copy of CodePackageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageRefCopyWith<$Res> get selector {
  
  return $CodePackageRefCopyWith<$Res>(_self.selector, (value) {
    return _then(_self.copyWith(selector: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class ResolveCodePackageRequest implements CodePackageServiceRequest {
   ResolveCodePackageRequest({@UuidValueConverter() this.requestId, required this.selector, this.authorityBaseUrl, this.indexUrl, final  String? $type}): $type = $type ?? 'resolve_code_package';
  factory ResolveCodePackageRequest.fromJson(Map<String, dynamic> json) => _$ResolveCodePackageRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
 final  CodePackageRef selector;
@override final  String? authorityBaseUrl;
@override final  String? indexUrl;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of CodePackageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ResolveCodePackageRequestCopyWith<ResolveCodePackageRequest> get copyWith => _$ResolveCodePackageRequestCopyWithImpl<ResolveCodePackageRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ResolveCodePackageRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ResolveCodePackageRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.selector, selector) || other.selector == selector)&&(identical(other.authorityBaseUrl, authorityBaseUrl) || other.authorityBaseUrl == authorityBaseUrl)&&(identical(other.indexUrl, indexUrl) || other.indexUrl == indexUrl));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,selector,authorityBaseUrl,indexUrl);

@override
String toString() {
  return 'CodePackageServiceRequest.resolveCodePackage(requestId: $requestId, selector: $selector, authorityBaseUrl: $authorityBaseUrl, indexUrl: $indexUrl)';
}


}

/// @nodoc
abstract mixin class $ResolveCodePackageRequestCopyWith<$Res> implements $CodePackageServiceRequestCopyWith<$Res> {
  factory $ResolveCodePackageRequestCopyWith(ResolveCodePackageRequest value, $Res Function(ResolveCodePackageRequest) _then) = _$ResolveCodePackageRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, CodePackageRef selector, String? authorityBaseUrl, String? indexUrl
});


$CodePackageRefCopyWith<$Res> get selector;

}
/// @nodoc
class _$ResolveCodePackageRequestCopyWithImpl<$Res>
    implements $ResolveCodePackageRequestCopyWith<$Res> {
  _$ResolveCodePackageRequestCopyWithImpl(this._self, this._then);

  final ResolveCodePackageRequest _self;
  final $Res Function(ResolveCodePackageRequest) _then;

/// Create a copy of CodePackageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? selector = null,Object? authorityBaseUrl = freezed,Object? indexUrl = freezed,}) {
  return _then(ResolveCodePackageRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,selector: null == selector ? _self.selector : selector // ignore: cast_nullable_to_non_nullable
as CodePackageRef,authorityBaseUrl: freezed == authorityBaseUrl ? _self.authorityBaseUrl : authorityBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,indexUrl: freezed == indexUrl ? _self.indexUrl : indexUrl // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

/// Create a copy of CodePackageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageRefCopyWith<$Res> get selector {
  
  return $CodePackageRefCopyWith<$Res>(_self.selector, (value) {
    return _then(_self.copyWith(selector: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DownloadCodePackageRequest implements CodePackageServiceRequest {
   DownloadCodePackageRequest({@UuidValueConverter() this.requestId, required this.selector, this.authorityBaseUrl, this.indexUrl, final  String? $type}): $type = $type ?? 'download_code_package';
  factory DownloadCodePackageRequest.fromJson(Map<String, dynamic> json) => _$DownloadCodePackageRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
 final  CodePackageRef selector;
@override final  String? authorityBaseUrl;
@override final  String? indexUrl;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of CodePackageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DownloadCodePackageRequestCopyWith<DownloadCodePackageRequest> get copyWith => _$DownloadCodePackageRequestCopyWithImpl<DownloadCodePackageRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DownloadCodePackageRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DownloadCodePackageRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.selector, selector) || other.selector == selector)&&(identical(other.authorityBaseUrl, authorityBaseUrl) || other.authorityBaseUrl == authorityBaseUrl)&&(identical(other.indexUrl, indexUrl) || other.indexUrl == indexUrl));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,selector,authorityBaseUrl,indexUrl);

@override
String toString() {
  return 'CodePackageServiceRequest.downloadCodePackage(requestId: $requestId, selector: $selector, authorityBaseUrl: $authorityBaseUrl, indexUrl: $indexUrl)';
}


}

/// @nodoc
abstract mixin class $DownloadCodePackageRequestCopyWith<$Res> implements $CodePackageServiceRequestCopyWith<$Res> {
  factory $DownloadCodePackageRequestCopyWith(DownloadCodePackageRequest value, $Res Function(DownloadCodePackageRequest) _then) = _$DownloadCodePackageRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, CodePackageRef selector, String? authorityBaseUrl, String? indexUrl
});


$CodePackageRefCopyWith<$Res> get selector;

}
/// @nodoc
class _$DownloadCodePackageRequestCopyWithImpl<$Res>
    implements $DownloadCodePackageRequestCopyWith<$Res> {
  _$DownloadCodePackageRequestCopyWithImpl(this._self, this._then);

  final DownloadCodePackageRequest _self;
  final $Res Function(DownloadCodePackageRequest) _then;

/// Create a copy of CodePackageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? selector = null,Object? authorityBaseUrl = freezed,Object? indexUrl = freezed,}) {
  return _then(DownloadCodePackageRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,selector: null == selector ? _self.selector : selector // ignore: cast_nullable_to_non_nullable
as CodePackageRef,authorityBaseUrl: freezed == authorityBaseUrl ? _self.authorityBaseUrl : authorityBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,indexUrl: freezed == indexUrl ? _self.indexUrl : indexUrl // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

/// Create a copy of CodePackageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageRefCopyWith<$Res> get selector {
  
  return $CodePackageRefCopyWith<$Res>(_self.selector, (value) {
    return _then(_self.copyWith(selector: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class PublishCodePackageRequest implements CodePackageServiceRequest {
   PublishCodePackageRequest({@UuidValueConverter() this.requestId, required this.descriptor, required this.artifactLock, required this.channel, this.authorityBaseUrl, this.indexUrl, this.publisherExecutionId, this.idempotencyKey, final  String? $type}): $type = $type ?? 'publish_code_package';
  factory PublishCodePackageRequest.fromJson(Map<String, dynamic> json) => _$PublishCodePackageRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
 final  CodePackageDescriptor descriptor;
 final  CodePackageArtifactLock artifactLock;
 final  String channel;
@override final  String? authorityBaseUrl;
@override final  String? indexUrl;
 final  String? publisherExecutionId;
 final  String? idempotencyKey;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of CodePackageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$PublishCodePackageRequestCopyWith<PublishCodePackageRequest> get copyWith => _$PublishCodePackageRequestCopyWithImpl<PublishCodePackageRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$PublishCodePackageRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is PublishCodePackageRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.descriptor, descriptor) || other.descriptor == descriptor)&&(identical(other.artifactLock, artifactLock) || other.artifactLock == artifactLock)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.authorityBaseUrl, authorityBaseUrl) || other.authorityBaseUrl == authorityBaseUrl)&&(identical(other.indexUrl, indexUrl) || other.indexUrl == indexUrl)&&(identical(other.publisherExecutionId, publisherExecutionId) || other.publisherExecutionId == publisherExecutionId)&&(identical(other.idempotencyKey, idempotencyKey) || other.idempotencyKey == idempotencyKey));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,descriptor,artifactLock,channel,authorityBaseUrl,indexUrl,publisherExecutionId,idempotencyKey);

@override
String toString() {
  return 'CodePackageServiceRequest.publishCodePackage(requestId: $requestId, descriptor: $descriptor, artifactLock: $artifactLock, channel: $channel, authorityBaseUrl: $authorityBaseUrl, indexUrl: $indexUrl, publisherExecutionId: $publisherExecutionId, idempotencyKey: $idempotencyKey)';
}


}

/// @nodoc
abstract mixin class $PublishCodePackageRequestCopyWith<$Res> implements $CodePackageServiceRequestCopyWith<$Res> {
  factory $PublishCodePackageRequestCopyWith(PublishCodePackageRequest value, $Res Function(PublishCodePackageRequest) _then) = _$PublishCodePackageRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, CodePackageDescriptor descriptor, CodePackageArtifactLock artifactLock, String channel, String? authorityBaseUrl, String? indexUrl, String? publisherExecutionId, String? idempotencyKey
});


$CodePackageDescriptorCopyWith<$Res> get descriptor;$CodePackageArtifactLockCopyWith<$Res> get artifactLock;

}
/// @nodoc
class _$PublishCodePackageRequestCopyWithImpl<$Res>
    implements $PublishCodePackageRequestCopyWith<$Res> {
  _$PublishCodePackageRequestCopyWithImpl(this._self, this._then);

  final PublishCodePackageRequest _self;
  final $Res Function(PublishCodePackageRequest) _then;

/// Create a copy of CodePackageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? descriptor = null,Object? artifactLock = null,Object? channel = null,Object? authorityBaseUrl = freezed,Object? indexUrl = freezed,Object? publisherExecutionId = freezed,Object? idempotencyKey = freezed,}) {
  return _then(PublishCodePackageRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,descriptor: null == descriptor ? _self.descriptor : descriptor // ignore: cast_nullable_to_non_nullable
as CodePackageDescriptor,artifactLock: null == artifactLock ? _self.artifactLock : artifactLock // ignore: cast_nullable_to_non_nullable
as CodePackageArtifactLock,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,authorityBaseUrl: freezed == authorityBaseUrl ? _self.authorityBaseUrl : authorityBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,indexUrl: freezed == indexUrl ? _self.indexUrl : indexUrl // ignore: cast_nullable_to_non_nullable
as String?,publisherExecutionId: freezed == publisherExecutionId ? _self.publisherExecutionId : publisherExecutionId // ignore: cast_nullable_to_non_nullable
as String?,idempotencyKey: freezed == idempotencyKey ? _self.idempotencyKey : idempotencyKey // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

/// Create a copy of CodePackageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageDescriptorCopyWith<$Res> get descriptor {
  
  return $CodePackageDescriptorCopyWith<$Res>(_self.descriptor, (value) {
    return _then(_self.copyWith(descriptor: value));
  });
}/// Create a copy of CodePackageServiceRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageArtifactLockCopyWith<$Res> get artifactLock {
  
  return $CodePackageArtifactLockCopyWith<$Res>(_self.artifactLock, (value) {
    return _then(_self.copyWith(artifactLock: value));
  });
}
}

CodePackageServiceResponse _$CodePackageServiceResponseFromJson(
  Map<String, dynamic> json
) {
        switch (json['operation']) {
                  case 'discover_code_package_channel_heads':
          return DiscoverCodePackageChannelHeadsResponse.fromJson(
            json
          );
                case 'search_code_package':
          return SearchCodePackageResponse.fromJson(
            json
          );
                case 'describe_code_package':
          return DescribeCodePackageResponse.fromJson(
            json
          );
                case 'resolve_code_package':
          return ResolveCodePackageResponse.fromJson(
            json
          );
                case 'download_code_package':
          return DownloadCodePackageResponse.fromJson(
            json
          );
                case 'publish_code_package':
          return PublishCodePackageResponse.fromJson(
            json
          );
        
          default:
            throw CheckedFromJsonException(
  json,
  'operation',
  'CodePackageServiceResponse',
  'Invalid union type "${json['operation']}"!'
);
        }
      
}

/// @nodoc
mixin _$CodePackageServiceResponse {

@UuidValueConverter() UuidValue? get requestId; bool get success; String? get info; String? get error; String? get authoritySourceUrl;
/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$CodePackageServiceResponseCopyWith<CodePackageServiceResponse> get copyWith => _$CodePackageServiceResponseCopyWithImpl<CodePackageServiceResponse>(this as CodePackageServiceResponse, _$identity);

  /// Serializes this CodePackageServiceResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is CodePackageServiceResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.info, info) || other.info == info)&&(identical(other.error, error) || other.error == error)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,info,error,authoritySourceUrl);

@override
String toString() {
  return 'CodePackageServiceResponse(requestId: $requestId, success: $success, info: $info, error: $error, authoritySourceUrl: $authoritySourceUrl)';
}


}

/// @nodoc
abstract mixin class $CodePackageServiceResponseCopyWith<$Res>  {
  factory $CodePackageServiceResponseCopyWith(CodePackageServiceResponse value, $Res Function(CodePackageServiceResponse) _then) = _$CodePackageServiceResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? info, String? error, String? authoritySourceUrl
});




}
/// @nodoc
class _$CodePackageServiceResponseCopyWithImpl<$Res>
    implements $CodePackageServiceResponseCopyWith<$Res> {
  _$CodePackageServiceResponseCopyWithImpl(this._self, this._then);

  final CodePackageServiceResponse _self;
  final $Res Function(CodePackageServiceResponse) _then;

/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? success = null,Object? info = freezed,Object? error = freezed,Object? authoritySourceUrl = freezed,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,info: freezed == info ? _self.info : info // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,authoritySourceUrl: freezed == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [CodePackageServiceResponse].
extension CodePackageServiceResponsePatterns on CodePackageServiceResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( DiscoverCodePackageChannelHeadsResponse value)?  discoverCodePackageChannelHeads,TResult Function( SearchCodePackageResponse value)?  searchCodePackage,TResult Function( DescribeCodePackageResponse value)?  describeCodePackage,TResult Function( ResolveCodePackageResponse value)?  resolveCodePackage,TResult Function( DownloadCodePackageResponse value)?  downloadCodePackage,TResult Function( PublishCodePackageResponse value)?  publishCodePackage,required TResult orElse(),}){
final _that = this;
switch (_that) {
case DiscoverCodePackageChannelHeadsResponse() when discoverCodePackageChannelHeads != null:
return discoverCodePackageChannelHeads(_that);case SearchCodePackageResponse() when searchCodePackage != null:
return searchCodePackage(_that);case DescribeCodePackageResponse() when describeCodePackage != null:
return describeCodePackage(_that);case ResolveCodePackageResponse() when resolveCodePackage != null:
return resolveCodePackage(_that);case DownloadCodePackageResponse() when downloadCodePackage != null:
return downloadCodePackage(_that);case PublishCodePackageResponse() when publishCodePackage != null:
return publishCodePackage(_that);case _:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( DiscoverCodePackageChannelHeadsResponse value)  discoverCodePackageChannelHeads,required TResult Function( SearchCodePackageResponse value)  searchCodePackage,required TResult Function( DescribeCodePackageResponse value)  describeCodePackage,required TResult Function( ResolveCodePackageResponse value)  resolveCodePackage,required TResult Function( DownloadCodePackageResponse value)  downloadCodePackage,required TResult Function( PublishCodePackageResponse value)  publishCodePackage,}){
final _that = this;
switch (_that) {
case DiscoverCodePackageChannelHeadsResponse():
return discoverCodePackageChannelHeads(_that);case SearchCodePackageResponse():
return searchCodePackage(_that);case DescribeCodePackageResponse():
return describeCodePackage(_that);case ResolveCodePackageResponse():
return resolveCodePackage(_that);case DownloadCodePackageResponse():
return downloadCodePackage(_that);case PublishCodePackageResponse():
return publishCodePackage(_that);case _:
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( DiscoverCodePackageChannelHeadsResponse value)?  discoverCodePackageChannelHeads,TResult? Function( SearchCodePackageResponse value)?  searchCodePackage,TResult? Function( DescribeCodePackageResponse value)?  describeCodePackage,TResult? Function( ResolveCodePackageResponse value)?  resolveCodePackage,TResult? Function( DownloadCodePackageResponse value)?  downloadCodePackage,TResult? Function( PublishCodePackageResponse value)?  publishCodePackage,}){
final _that = this;
switch (_that) {
case DiscoverCodePackageChannelHeadsResponse() when discoverCodePackageChannelHeads != null:
return discoverCodePackageChannelHeads(_that);case SearchCodePackageResponse() when searchCodePackage != null:
return searchCodePackage(_that);case DescribeCodePackageResponse() when describeCodePackage != null:
return describeCodePackage(_that);case ResolveCodePackageResponse() when resolveCodePackage != null:
return resolveCodePackage(_that);case DownloadCodePackageResponse() when downloadCodePackage != null:
return downloadCodePackage(_that);case PublishCodePackageResponse() when publishCodePackage != null:
return publishCodePackage(_that);case _:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  List<CodePackageDiscoveryEntry> entries)?  discoverCodePackageChannelHeads,TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  List<CodePackageDescriptor> descriptors)?  searchCodePackage,TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  CodePackageDescriptor? descriptor)?  describeCodePackage,TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  CodePackageRef selector,  CodePackageDescriptor descriptor,  CodePackageArtifactLock artifactLock)?  resolveCodePackage,TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  CodePackageRef selector,  CodePackageArtifactLock artifactLock)?  downloadCodePackage,TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  CodePackageRef? selector,  CodePackageDescriptor? descriptor,  CodePackageArtifactLock? artifactLock,  bool accepted)?  publishCodePackage,required TResult orElse(),}) {final _that = this;
switch (_that) {
case DiscoverCodePackageChannelHeadsResponse() when discoverCodePackageChannelHeads != null:
return discoverCodePackageChannelHeads(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.entries);case SearchCodePackageResponse() when searchCodePackage != null:
return searchCodePackage(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.descriptors);case DescribeCodePackageResponse() when describeCodePackage != null:
return describeCodePackage(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.descriptor);case ResolveCodePackageResponse() when resolveCodePackage != null:
return resolveCodePackage(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.selector,_that.descriptor,_that.artifactLock);case DownloadCodePackageResponse() when downloadCodePackage != null:
return downloadCodePackage(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.selector,_that.artifactLock);case PublishCodePackageResponse() when publishCodePackage != null:
return publishCodePackage(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.selector,_that.descriptor,_that.artifactLock,_that.accepted);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  List<CodePackageDiscoveryEntry> entries)  discoverCodePackageChannelHeads,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  List<CodePackageDescriptor> descriptors)  searchCodePackage,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  CodePackageDescriptor? descriptor)  describeCodePackage,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  CodePackageRef selector,  CodePackageDescriptor descriptor,  CodePackageArtifactLock artifactLock)  resolveCodePackage,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  CodePackageRef selector,  CodePackageArtifactLock artifactLock)  downloadCodePackage,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  CodePackageRef? selector,  CodePackageDescriptor? descriptor,  CodePackageArtifactLock? artifactLock,  bool accepted)  publishCodePackage,}) {final _that = this;
switch (_that) {
case DiscoverCodePackageChannelHeadsResponse():
return discoverCodePackageChannelHeads(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.entries);case SearchCodePackageResponse():
return searchCodePackage(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.descriptors);case DescribeCodePackageResponse():
return describeCodePackage(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.descriptor);case ResolveCodePackageResponse():
return resolveCodePackage(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.selector,_that.descriptor,_that.artifactLock);case DownloadCodePackageResponse():
return downloadCodePackage(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.selector,_that.artifactLock);case PublishCodePackageResponse():
return publishCodePackage(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.selector,_that.descriptor,_that.artifactLock,_that.accepted);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  List<CodePackageDiscoveryEntry> entries)?  discoverCodePackageChannelHeads,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  List<CodePackageDescriptor> descriptors)?  searchCodePackage,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  CodePackageDescriptor? descriptor)?  describeCodePackage,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  CodePackageRef selector,  CodePackageDescriptor descriptor,  CodePackageArtifactLock artifactLock)?  resolveCodePackage,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  CodePackageRef selector,  CodePackageArtifactLock artifactLock)?  downloadCodePackage,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  CodePackageRef? selector,  CodePackageDescriptor? descriptor,  CodePackageArtifactLock? artifactLock,  bool accepted)?  publishCodePackage,}) {final _that = this;
switch (_that) {
case DiscoverCodePackageChannelHeadsResponse() when discoverCodePackageChannelHeads != null:
return discoverCodePackageChannelHeads(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.entries);case SearchCodePackageResponse() when searchCodePackage != null:
return searchCodePackage(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.descriptors);case DescribeCodePackageResponse() when describeCodePackage != null:
return describeCodePackage(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.descriptor);case ResolveCodePackageResponse() when resolveCodePackage != null:
return resolveCodePackage(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.selector,_that.descriptor,_that.artifactLock);case DownloadCodePackageResponse() when downloadCodePackage != null:
return downloadCodePackage(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.selector,_that.artifactLock);case PublishCodePackageResponse() when publishCodePackage != null:
return publishCodePackage(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.selector,_that.descriptor,_that.artifactLock,_that.accepted);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DiscoverCodePackageChannelHeadsResponse implements CodePackageServiceResponse {
   DiscoverCodePackageChannelHeadsResponse({@UuidValueConverter() this.requestId, required this.success, this.info, this.error, this.authoritySourceUrl, final  List<CodePackageDiscoveryEntry> entries = const [], final  String? $type}): _entries = entries,$type = $type ?? 'discover_code_package_channel_heads';
  factory DiscoverCodePackageChannelHeadsResponse.fromJson(Map<String, dynamic> json) => _$DiscoverCodePackageChannelHeadsResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? info;
@override final  String? error;
@override final  String? authoritySourceUrl;
 final  List<CodePackageDiscoveryEntry> _entries;
@JsonKey() List<CodePackageDiscoveryEntry> get entries {
  if (_entries is EqualUnmodifiableListView) return _entries;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_entries);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DiscoverCodePackageChannelHeadsResponseCopyWith<DiscoverCodePackageChannelHeadsResponse> get copyWith => _$DiscoverCodePackageChannelHeadsResponseCopyWithImpl<DiscoverCodePackageChannelHeadsResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DiscoverCodePackageChannelHeadsResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DiscoverCodePackageChannelHeadsResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.info, info) || other.info == info)&&(identical(other.error, error) || other.error == error)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl)&&const DeepCollectionEquality().equals(other._entries, _entries));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,info,error,authoritySourceUrl,const DeepCollectionEquality().hash(_entries));

@override
String toString() {
  return 'CodePackageServiceResponse.discoverCodePackageChannelHeads(requestId: $requestId, success: $success, info: $info, error: $error, authoritySourceUrl: $authoritySourceUrl, entries: $entries)';
}


}

/// @nodoc
abstract mixin class $DiscoverCodePackageChannelHeadsResponseCopyWith<$Res> implements $CodePackageServiceResponseCopyWith<$Res> {
  factory $DiscoverCodePackageChannelHeadsResponseCopyWith(DiscoverCodePackageChannelHeadsResponse value, $Res Function(DiscoverCodePackageChannelHeadsResponse) _then) = _$DiscoverCodePackageChannelHeadsResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? info, String? error, String? authoritySourceUrl, List<CodePackageDiscoveryEntry> entries
});




}
/// @nodoc
class _$DiscoverCodePackageChannelHeadsResponseCopyWithImpl<$Res>
    implements $DiscoverCodePackageChannelHeadsResponseCopyWith<$Res> {
  _$DiscoverCodePackageChannelHeadsResponseCopyWithImpl(this._self, this._then);

  final DiscoverCodePackageChannelHeadsResponse _self;
  final $Res Function(DiscoverCodePackageChannelHeadsResponse) _then;

/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? info = freezed,Object? error = freezed,Object? authoritySourceUrl = freezed,Object? entries = null,}) {
  return _then(DiscoverCodePackageChannelHeadsResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,info: freezed == info ? _self.info : info // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,authoritySourceUrl: freezed == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String?,entries: null == entries ? _self._entries : entries // ignore: cast_nullable_to_non_nullable
as List<CodePackageDiscoveryEntry>,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class SearchCodePackageResponse implements CodePackageServiceResponse {
   SearchCodePackageResponse({@UuidValueConverter() this.requestId, required this.success, this.info, this.error, this.authoritySourceUrl, final  List<CodePackageDescriptor> descriptors = const [], final  String? $type}): _descriptors = descriptors,$type = $type ?? 'search_code_package';
  factory SearchCodePackageResponse.fromJson(Map<String, dynamic> json) => _$SearchCodePackageResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? info;
@override final  String? error;
@override final  String? authoritySourceUrl;
 final  List<CodePackageDescriptor> _descriptors;
@JsonKey() List<CodePackageDescriptor> get descriptors {
  if (_descriptors is EqualUnmodifiableListView) return _descriptors;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_descriptors);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$SearchCodePackageResponseCopyWith<SearchCodePackageResponse> get copyWith => _$SearchCodePackageResponseCopyWithImpl<SearchCodePackageResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$SearchCodePackageResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is SearchCodePackageResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.info, info) || other.info == info)&&(identical(other.error, error) || other.error == error)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl)&&const DeepCollectionEquality().equals(other._descriptors, _descriptors));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,info,error,authoritySourceUrl,const DeepCollectionEquality().hash(_descriptors));

@override
String toString() {
  return 'CodePackageServiceResponse.searchCodePackage(requestId: $requestId, success: $success, info: $info, error: $error, authoritySourceUrl: $authoritySourceUrl, descriptors: $descriptors)';
}


}

/// @nodoc
abstract mixin class $SearchCodePackageResponseCopyWith<$Res> implements $CodePackageServiceResponseCopyWith<$Res> {
  factory $SearchCodePackageResponseCopyWith(SearchCodePackageResponse value, $Res Function(SearchCodePackageResponse) _then) = _$SearchCodePackageResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? info, String? error, String? authoritySourceUrl, List<CodePackageDescriptor> descriptors
});




}
/// @nodoc
class _$SearchCodePackageResponseCopyWithImpl<$Res>
    implements $SearchCodePackageResponseCopyWith<$Res> {
  _$SearchCodePackageResponseCopyWithImpl(this._self, this._then);

  final SearchCodePackageResponse _self;
  final $Res Function(SearchCodePackageResponse) _then;

/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? info = freezed,Object? error = freezed,Object? authoritySourceUrl = freezed,Object? descriptors = null,}) {
  return _then(SearchCodePackageResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,info: freezed == info ? _self.info : info // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,authoritySourceUrl: freezed == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String?,descriptors: null == descriptors ? _self._descriptors : descriptors // ignore: cast_nullable_to_non_nullable
as List<CodePackageDescriptor>,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DescribeCodePackageResponse implements CodePackageServiceResponse {
   DescribeCodePackageResponse({@UuidValueConverter() this.requestId, required this.success, this.info, this.error, this.authoritySourceUrl, this.descriptor, final  String? $type}): $type = $type ?? 'describe_code_package';
  factory DescribeCodePackageResponse.fromJson(Map<String, dynamic> json) => _$DescribeCodePackageResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? info;
@override final  String? error;
@override final  String? authoritySourceUrl;
 final  CodePackageDescriptor? descriptor;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DescribeCodePackageResponseCopyWith<DescribeCodePackageResponse> get copyWith => _$DescribeCodePackageResponseCopyWithImpl<DescribeCodePackageResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DescribeCodePackageResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DescribeCodePackageResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.info, info) || other.info == info)&&(identical(other.error, error) || other.error == error)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl)&&(identical(other.descriptor, descriptor) || other.descriptor == descriptor));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,info,error,authoritySourceUrl,descriptor);

@override
String toString() {
  return 'CodePackageServiceResponse.describeCodePackage(requestId: $requestId, success: $success, info: $info, error: $error, authoritySourceUrl: $authoritySourceUrl, descriptor: $descriptor)';
}


}

/// @nodoc
abstract mixin class $DescribeCodePackageResponseCopyWith<$Res> implements $CodePackageServiceResponseCopyWith<$Res> {
  factory $DescribeCodePackageResponseCopyWith(DescribeCodePackageResponse value, $Res Function(DescribeCodePackageResponse) _then) = _$DescribeCodePackageResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? info, String? error, String? authoritySourceUrl, CodePackageDescriptor? descriptor
});


$CodePackageDescriptorCopyWith<$Res>? get descriptor;

}
/// @nodoc
class _$DescribeCodePackageResponseCopyWithImpl<$Res>
    implements $DescribeCodePackageResponseCopyWith<$Res> {
  _$DescribeCodePackageResponseCopyWithImpl(this._self, this._then);

  final DescribeCodePackageResponse _self;
  final $Res Function(DescribeCodePackageResponse) _then;

/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? info = freezed,Object? error = freezed,Object? authoritySourceUrl = freezed,Object? descriptor = freezed,}) {
  return _then(DescribeCodePackageResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,info: freezed == info ? _self.info : info // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,authoritySourceUrl: freezed == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String?,descriptor: freezed == descriptor ? _self.descriptor : descriptor // ignore: cast_nullable_to_non_nullable
as CodePackageDescriptor?,
  ));
}

/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageDescriptorCopyWith<$Res>? get descriptor {
    if (_self.descriptor == null) {
    return null;
  }

  return $CodePackageDescriptorCopyWith<$Res>(_self.descriptor!, (value) {
    return _then(_self.copyWith(descriptor: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class ResolveCodePackageResponse implements CodePackageServiceResponse {
   ResolveCodePackageResponse({@UuidValueConverter() this.requestId, required this.success, this.info, this.error, this.authoritySourceUrl, required this.selector, required this.descriptor, required this.artifactLock, final  String? $type}): $type = $type ?? 'resolve_code_package';
  factory ResolveCodePackageResponse.fromJson(Map<String, dynamic> json) => _$ResolveCodePackageResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? info;
@override final  String? error;
@override final  String? authoritySourceUrl;
 final  CodePackageRef selector;
 final  CodePackageDescriptor descriptor;
 final  CodePackageArtifactLock artifactLock;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ResolveCodePackageResponseCopyWith<ResolveCodePackageResponse> get copyWith => _$ResolveCodePackageResponseCopyWithImpl<ResolveCodePackageResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ResolveCodePackageResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ResolveCodePackageResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.info, info) || other.info == info)&&(identical(other.error, error) || other.error == error)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl)&&(identical(other.selector, selector) || other.selector == selector)&&(identical(other.descriptor, descriptor) || other.descriptor == descriptor)&&(identical(other.artifactLock, artifactLock) || other.artifactLock == artifactLock));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,info,error,authoritySourceUrl,selector,descriptor,artifactLock);

@override
String toString() {
  return 'CodePackageServiceResponse.resolveCodePackage(requestId: $requestId, success: $success, info: $info, error: $error, authoritySourceUrl: $authoritySourceUrl, selector: $selector, descriptor: $descriptor, artifactLock: $artifactLock)';
}


}

/// @nodoc
abstract mixin class $ResolveCodePackageResponseCopyWith<$Res> implements $CodePackageServiceResponseCopyWith<$Res> {
  factory $ResolveCodePackageResponseCopyWith(ResolveCodePackageResponse value, $Res Function(ResolveCodePackageResponse) _then) = _$ResolveCodePackageResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? info, String? error, String? authoritySourceUrl, CodePackageRef selector, CodePackageDescriptor descriptor, CodePackageArtifactLock artifactLock
});


$CodePackageRefCopyWith<$Res> get selector;$CodePackageDescriptorCopyWith<$Res> get descriptor;$CodePackageArtifactLockCopyWith<$Res> get artifactLock;

}
/// @nodoc
class _$ResolveCodePackageResponseCopyWithImpl<$Res>
    implements $ResolveCodePackageResponseCopyWith<$Res> {
  _$ResolveCodePackageResponseCopyWithImpl(this._self, this._then);

  final ResolveCodePackageResponse _self;
  final $Res Function(ResolveCodePackageResponse) _then;

/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? info = freezed,Object? error = freezed,Object? authoritySourceUrl = freezed,Object? selector = null,Object? descriptor = null,Object? artifactLock = null,}) {
  return _then(ResolveCodePackageResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,info: freezed == info ? _self.info : info // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,authoritySourceUrl: freezed == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String?,selector: null == selector ? _self.selector : selector // ignore: cast_nullable_to_non_nullable
as CodePackageRef,descriptor: null == descriptor ? _self.descriptor : descriptor // ignore: cast_nullable_to_non_nullable
as CodePackageDescriptor,artifactLock: null == artifactLock ? _self.artifactLock : artifactLock // ignore: cast_nullable_to_non_nullable
as CodePackageArtifactLock,
  ));
}

/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageRefCopyWith<$Res> get selector {
  
  return $CodePackageRefCopyWith<$Res>(_self.selector, (value) {
    return _then(_self.copyWith(selector: value));
  });
}/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageDescriptorCopyWith<$Res> get descriptor {
  
  return $CodePackageDescriptorCopyWith<$Res>(_self.descriptor, (value) {
    return _then(_self.copyWith(descriptor: value));
  });
}/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageArtifactLockCopyWith<$Res> get artifactLock {
  
  return $CodePackageArtifactLockCopyWith<$Res>(_self.artifactLock, (value) {
    return _then(_self.copyWith(artifactLock: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DownloadCodePackageResponse implements CodePackageServiceResponse {
   DownloadCodePackageResponse({@UuidValueConverter() this.requestId, required this.success, this.info, this.error, this.authoritySourceUrl, required this.selector, required this.artifactLock, final  String? $type}): $type = $type ?? 'download_code_package';
  factory DownloadCodePackageResponse.fromJson(Map<String, dynamic> json) => _$DownloadCodePackageResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? info;
@override final  String? error;
@override final  String? authoritySourceUrl;
 final  CodePackageRef selector;
 final  CodePackageArtifactLock artifactLock;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DownloadCodePackageResponseCopyWith<DownloadCodePackageResponse> get copyWith => _$DownloadCodePackageResponseCopyWithImpl<DownloadCodePackageResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DownloadCodePackageResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DownloadCodePackageResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.info, info) || other.info == info)&&(identical(other.error, error) || other.error == error)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl)&&(identical(other.selector, selector) || other.selector == selector)&&(identical(other.artifactLock, artifactLock) || other.artifactLock == artifactLock));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,info,error,authoritySourceUrl,selector,artifactLock);

@override
String toString() {
  return 'CodePackageServiceResponse.downloadCodePackage(requestId: $requestId, success: $success, info: $info, error: $error, authoritySourceUrl: $authoritySourceUrl, selector: $selector, artifactLock: $artifactLock)';
}


}

/// @nodoc
abstract mixin class $DownloadCodePackageResponseCopyWith<$Res> implements $CodePackageServiceResponseCopyWith<$Res> {
  factory $DownloadCodePackageResponseCopyWith(DownloadCodePackageResponse value, $Res Function(DownloadCodePackageResponse) _then) = _$DownloadCodePackageResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? info, String? error, String? authoritySourceUrl, CodePackageRef selector, CodePackageArtifactLock artifactLock
});


$CodePackageRefCopyWith<$Res> get selector;$CodePackageArtifactLockCopyWith<$Res> get artifactLock;

}
/// @nodoc
class _$DownloadCodePackageResponseCopyWithImpl<$Res>
    implements $DownloadCodePackageResponseCopyWith<$Res> {
  _$DownloadCodePackageResponseCopyWithImpl(this._self, this._then);

  final DownloadCodePackageResponse _self;
  final $Res Function(DownloadCodePackageResponse) _then;

/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? info = freezed,Object? error = freezed,Object? authoritySourceUrl = freezed,Object? selector = null,Object? artifactLock = null,}) {
  return _then(DownloadCodePackageResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,info: freezed == info ? _self.info : info // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,authoritySourceUrl: freezed == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String?,selector: null == selector ? _self.selector : selector // ignore: cast_nullable_to_non_nullable
as CodePackageRef,artifactLock: null == artifactLock ? _self.artifactLock : artifactLock // ignore: cast_nullable_to_non_nullable
as CodePackageArtifactLock,
  ));
}

/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageRefCopyWith<$Res> get selector {
  
  return $CodePackageRefCopyWith<$Res>(_self.selector, (value) {
    return _then(_self.copyWith(selector: value));
  });
}/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageArtifactLockCopyWith<$Res> get artifactLock {
  
  return $CodePackageArtifactLockCopyWith<$Res>(_self.artifactLock, (value) {
    return _then(_self.copyWith(artifactLock: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class PublishCodePackageResponse implements CodePackageServiceResponse {
   PublishCodePackageResponse({@UuidValueConverter() this.requestId, required this.success, this.info, this.error, this.authoritySourceUrl, this.selector, this.descriptor, this.artifactLock, required this.accepted, final  String? $type}): $type = $type ?? 'publish_code_package';
  factory PublishCodePackageResponse.fromJson(Map<String, dynamic> json) => _$PublishCodePackageResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? info;
@override final  String? error;
@override final  String? authoritySourceUrl;
 final  CodePackageRef? selector;
 final  CodePackageDescriptor? descriptor;
 final  CodePackageArtifactLock? artifactLock;
 final  bool accepted;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$PublishCodePackageResponseCopyWith<PublishCodePackageResponse> get copyWith => _$PublishCodePackageResponseCopyWithImpl<PublishCodePackageResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$PublishCodePackageResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is PublishCodePackageResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.info, info) || other.info == info)&&(identical(other.error, error) || other.error == error)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl)&&(identical(other.selector, selector) || other.selector == selector)&&(identical(other.descriptor, descriptor) || other.descriptor == descriptor)&&(identical(other.artifactLock, artifactLock) || other.artifactLock == artifactLock)&&(identical(other.accepted, accepted) || other.accepted == accepted));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,info,error,authoritySourceUrl,selector,descriptor,artifactLock,accepted);

@override
String toString() {
  return 'CodePackageServiceResponse.publishCodePackage(requestId: $requestId, success: $success, info: $info, error: $error, authoritySourceUrl: $authoritySourceUrl, selector: $selector, descriptor: $descriptor, artifactLock: $artifactLock, accepted: $accepted)';
}


}

/// @nodoc
abstract mixin class $PublishCodePackageResponseCopyWith<$Res> implements $CodePackageServiceResponseCopyWith<$Res> {
  factory $PublishCodePackageResponseCopyWith(PublishCodePackageResponse value, $Res Function(PublishCodePackageResponse) _then) = _$PublishCodePackageResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? info, String? error, String? authoritySourceUrl, CodePackageRef? selector, CodePackageDescriptor? descriptor, CodePackageArtifactLock? artifactLock, bool accepted
});


$CodePackageRefCopyWith<$Res>? get selector;$CodePackageDescriptorCopyWith<$Res>? get descriptor;$CodePackageArtifactLockCopyWith<$Res>? get artifactLock;

}
/// @nodoc
class _$PublishCodePackageResponseCopyWithImpl<$Res>
    implements $PublishCodePackageResponseCopyWith<$Res> {
  _$PublishCodePackageResponseCopyWithImpl(this._self, this._then);

  final PublishCodePackageResponse _self;
  final $Res Function(PublishCodePackageResponse) _then;

/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? info = freezed,Object? error = freezed,Object? authoritySourceUrl = freezed,Object? selector = freezed,Object? descriptor = freezed,Object? artifactLock = freezed,Object? accepted = null,}) {
  return _then(PublishCodePackageResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,info: freezed == info ? _self.info : info // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,authoritySourceUrl: freezed == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String?,selector: freezed == selector ? _self.selector : selector // ignore: cast_nullable_to_non_nullable
as CodePackageRef?,descriptor: freezed == descriptor ? _self.descriptor : descriptor // ignore: cast_nullable_to_non_nullable
as CodePackageDescriptor?,artifactLock: freezed == artifactLock ? _self.artifactLock : artifactLock // ignore: cast_nullable_to_non_nullable
as CodePackageArtifactLock?,accepted: null == accepted ? _self.accepted : accepted // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}

/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageRefCopyWith<$Res>? get selector {
    if (_self.selector == null) {
    return null;
  }

  return $CodePackageRefCopyWith<$Res>(_self.selector!, (value) {
    return _then(_self.copyWith(selector: value));
  });
}/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageDescriptorCopyWith<$Res>? get descriptor {
    if (_self.descriptor == null) {
    return null;
  }

  return $CodePackageDescriptorCopyWith<$Res>(_self.descriptor!, (value) {
    return _then(_self.copyWith(descriptor: value));
  });
}/// Create a copy of CodePackageServiceResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageArtifactLockCopyWith<$Res>? get artifactLock {
    if (_self.artifactLock == null) {
    return null;
  }

  return $CodePackageArtifactLockCopyWith<$Res>(_self.artifactLock!, (value) {
    return _then(_self.copyWith(artifactLock: value));
  });
}
}


/// @nodoc
mixin _$CodePackageRef {

 String get packageName;@JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable) CodeLanguage? get language; String? get surface; String get channel; String? get version; String? get revisionId; String? get digest;
/// Create a copy of CodePackageRef
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$CodePackageRefCopyWith<CodePackageRef> get copyWith => _$CodePackageRefCopyWithImpl<CodePackageRef>(this as CodePackageRef, _$identity);

  /// Serializes this CodePackageRef to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is CodePackageRef&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.language, language) || other.language == language)&&(identical(other.surface, surface) || other.surface == surface)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.version, version) || other.version == version)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.digest, digest) || other.digest == digest));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,packageName,language,surface,channel,version,revisionId,digest);

@override
String toString() {
  return 'CodePackageRef(packageName: $packageName, language: $language, surface: $surface, channel: $channel, version: $version, revisionId: $revisionId, digest: $digest)';
}


}

/// @nodoc
abstract mixin class $CodePackageRefCopyWith<$Res>  {
  factory $CodePackageRefCopyWith(CodePackageRef value, $Res Function(CodePackageRef) _then) = _$CodePackageRefCopyWithImpl;
@useResult
$Res call({
 String packageName,@JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable) CodeLanguage? language, String? surface, String channel, String? version, String? revisionId, String? digest
});




}
/// @nodoc
class _$CodePackageRefCopyWithImpl<$Res>
    implements $CodePackageRefCopyWith<$Res> {
  _$CodePackageRefCopyWithImpl(this._self, this._then);

  final CodePackageRef _self;
  final $Res Function(CodePackageRef) _then;

/// Create a copy of CodePackageRef
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? packageName = null,Object? language = freezed,Object? surface = freezed,Object? channel = null,Object? version = freezed,Object? revisionId = freezed,Object? digest = freezed,}) {
  return _then(_self.copyWith(
packageName: null == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String,language: freezed == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as CodeLanguage?,surface: freezed == surface ? _self.surface : surface // ignore: cast_nullable_to_non_nullable
as String?,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,version: freezed == version ? _self.version : version // ignore: cast_nullable_to_non_nullable
as String?,revisionId: freezed == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String?,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [CodePackageRef].
extension CodePackageRefPatterns on CodePackageRef {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _CodePackageRef value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _CodePackageRef() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _CodePackageRef value)  def,}){
final _that = this;
switch (_that) {
case _CodePackageRef():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _CodePackageRef value)?  def,}){
final _that = this;
switch (_that) {
case _CodePackageRef() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable)  CodeLanguage? language,  String? surface,  String channel,  String? version,  String? revisionId,  String? digest)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _CodePackageRef() when def != null:
return def(_that.packageName,_that.language,_that.surface,_that.channel,_that.version,_that.revisionId,_that.digest);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable)  CodeLanguage? language,  String? surface,  String channel,  String? version,  String? revisionId,  String? digest)  def,}) {final _that = this;
switch (_that) {
case _CodePackageRef():
return def(_that.packageName,_that.language,_that.surface,_that.channel,_that.version,_that.revisionId,_that.digest);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable)  CodeLanguage? language,  String? surface,  String channel,  String? version,  String? revisionId,  String? digest)?  def,}) {final _that = this;
switch (_that) {
case _CodePackageRef() when def != null:
return def(_that.packageName,_that.language,_that.surface,_that.channel,_that.version,_that.revisionId,_that.digest);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _CodePackageRef implements CodePackageRef {
   _CodePackageRef({required this.packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable) this.language, this.surface, required this.channel, this.version, this.revisionId, this.digest});
  factory _CodePackageRef.fromJson(Map<String, dynamic> json) => _$CodePackageRefFromJson(json);

@override final  String packageName;
@override@JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable) final  CodeLanguage? language;
@override final  String? surface;
@override final  String channel;
@override final  String? version;
@override final  String? revisionId;
@override final  String? digest;

/// Create a copy of CodePackageRef
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$CodePackageRefCopyWith<_CodePackageRef> get copyWith => __$CodePackageRefCopyWithImpl<_CodePackageRef>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$CodePackageRefToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _CodePackageRef&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.language, language) || other.language == language)&&(identical(other.surface, surface) || other.surface == surface)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.version, version) || other.version == version)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.digest, digest) || other.digest == digest));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,packageName,language,surface,channel,version,revisionId,digest);

@override
String toString() {
  return 'CodePackageRef.def(packageName: $packageName, language: $language, surface: $surface, channel: $channel, version: $version, revisionId: $revisionId, digest: $digest)';
}


}

/// @nodoc
abstract mixin class _$CodePackageRefCopyWith<$Res> implements $CodePackageRefCopyWith<$Res> {
  factory _$CodePackageRefCopyWith(_CodePackageRef value, $Res Function(_CodePackageRef) _then) = __$CodePackageRefCopyWithImpl;
@override @useResult
$Res call({
 String packageName,@JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable) CodeLanguage? language, String? surface, String channel, String? version, String? revisionId, String? digest
});




}
/// @nodoc
class __$CodePackageRefCopyWithImpl<$Res>
    implements _$CodePackageRefCopyWith<$Res> {
  __$CodePackageRefCopyWithImpl(this._self, this._then);

  final _CodePackageRef _self;
  final $Res Function(_CodePackageRef) _then;

/// Create a copy of CodePackageRef
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? packageName = null,Object? language = freezed,Object? surface = freezed,Object? channel = null,Object? version = freezed,Object? revisionId = freezed,Object? digest = freezed,}) {
  return _then(_CodePackageRef(
packageName: null == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String,language: freezed == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as CodeLanguage?,surface: freezed == surface ? _self.surface : surface // ignore: cast_nullable_to_non_nullable
as String?,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,version: freezed == version ? _self.version : version // ignore: cast_nullable_to_non_nullable
as String?,revisionId: freezed == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String?,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$CodePackageArtifactLock {

 String get artifactUrl; String get sha256; int? get sizeBytes; String? get mediaType; String? get archiveFormat; String? get revisionId; String? get publishedAt;
/// Create a copy of CodePackageArtifactLock
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$CodePackageArtifactLockCopyWith<CodePackageArtifactLock> get copyWith => _$CodePackageArtifactLockCopyWithImpl<CodePackageArtifactLock>(this as CodePackageArtifactLock, _$identity);

  /// Serializes this CodePackageArtifactLock to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is CodePackageArtifactLock&&(identical(other.artifactUrl, artifactUrl) || other.artifactUrl == artifactUrl)&&(identical(other.sha256, sha256) || other.sha256 == sha256)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.archiveFormat, archiveFormat) || other.archiveFormat == archiveFormat)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.publishedAt, publishedAt) || other.publishedAt == publishedAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,artifactUrl,sha256,sizeBytes,mediaType,archiveFormat,revisionId,publishedAt);

@override
String toString() {
  return 'CodePackageArtifactLock(artifactUrl: $artifactUrl, sha256: $sha256, sizeBytes: $sizeBytes, mediaType: $mediaType, archiveFormat: $archiveFormat, revisionId: $revisionId, publishedAt: $publishedAt)';
}


}

/// @nodoc
abstract mixin class $CodePackageArtifactLockCopyWith<$Res>  {
  factory $CodePackageArtifactLockCopyWith(CodePackageArtifactLock value, $Res Function(CodePackageArtifactLock) _then) = _$CodePackageArtifactLockCopyWithImpl;
@useResult
$Res call({
 String artifactUrl, String sha256, int? sizeBytes, String? mediaType, String? archiveFormat, String? revisionId, String? publishedAt
});




}
/// @nodoc
class _$CodePackageArtifactLockCopyWithImpl<$Res>
    implements $CodePackageArtifactLockCopyWith<$Res> {
  _$CodePackageArtifactLockCopyWithImpl(this._self, this._then);

  final CodePackageArtifactLock _self;
  final $Res Function(CodePackageArtifactLock) _then;

/// Create a copy of CodePackageArtifactLock
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? artifactUrl = null,Object? sha256 = null,Object? sizeBytes = freezed,Object? mediaType = freezed,Object? archiveFormat = freezed,Object? revisionId = freezed,Object? publishedAt = freezed,}) {
  return _then(_self.copyWith(
artifactUrl: null == artifactUrl ? _self.artifactUrl : artifactUrl // ignore: cast_nullable_to_non_nullable
as String,sha256: null == sha256 ? _self.sha256 : sha256 // ignore: cast_nullable_to_non_nullable
as String,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,mediaType: freezed == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String?,archiveFormat: freezed == archiveFormat ? _self.archiveFormat : archiveFormat // ignore: cast_nullable_to_non_nullable
as String?,revisionId: freezed == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String?,publishedAt: freezed == publishedAt ? _self.publishedAt : publishedAt // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [CodePackageArtifactLock].
extension CodePackageArtifactLockPatterns on CodePackageArtifactLock {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _CodePackageArtifactLock value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _CodePackageArtifactLock() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _CodePackageArtifactLock value)  def,}){
final _that = this;
switch (_that) {
case _CodePackageArtifactLock():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _CodePackageArtifactLock value)?  def,}){
final _that = this;
switch (_that) {
case _CodePackageArtifactLock() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String artifactUrl,  String sha256,  int? sizeBytes,  String? mediaType,  String? archiveFormat,  String? revisionId,  String? publishedAt)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _CodePackageArtifactLock() when def != null:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String artifactUrl,  String sha256,  int? sizeBytes,  String? mediaType,  String? archiveFormat,  String? revisionId,  String? publishedAt)  def,}) {final _that = this;
switch (_that) {
case _CodePackageArtifactLock():
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String artifactUrl,  String sha256,  int? sizeBytes,  String? mediaType,  String? archiveFormat,  String? revisionId,  String? publishedAt)?  def,}) {final _that = this;
switch (_that) {
case _CodePackageArtifactLock() when def != null:
return def(_that.artifactUrl,_that.sha256,_that.sizeBytes,_that.mediaType,_that.archiveFormat,_that.revisionId,_that.publishedAt);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _CodePackageArtifactLock implements CodePackageArtifactLock {
   _CodePackageArtifactLock({required this.artifactUrl, required this.sha256, this.sizeBytes, this.mediaType, this.archiveFormat, this.revisionId, this.publishedAt});
  factory _CodePackageArtifactLock.fromJson(Map<String, dynamic> json) => _$CodePackageArtifactLockFromJson(json);

@override final  String artifactUrl;
@override final  String sha256;
@override final  int? sizeBytes;
@override final  String? mediaType;
@override final  String? archiveFormat;
@override final  String? revisionId;
@override final  String? publishedAt;

/// Create a copy of CodePackageArtifactLock
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$CodePackageArtifactLockCopyWith<_CodePackageArtifactLock> get copyWith => __$CodePackageArtifactLockCopyWithImpl<_CodePackageArtifactLock>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$CodePackageArtifactLockToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _CodePackageArtifactLock&&(identical(other.artifactUrl, artifactUrl) || other.artifactUrl == artifactUrl)&&(identical(other.sha256, sha256) || other.sha256 == sha256)&&(identical(other.sizeBytes, sizeBytes) || other.sizeBytes == sizeBytes)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.archiveFormat, archiveFormat) || other.archiveFormat == archiveFormat)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.publishedAt, publishedAt) || other.publishedAt == publishedAt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,artifactUrl,sha256,sizeBytes,mediaType,archiveFormat,revisionId,publishedAt);

@override
String toString() {
  return 'CodePackageArtifactLock.def(artifactUrl: $artifactUrl, sha256: $sha256, sizeBytes: $sizeBytes, mediaType: $mediaType, archiveFormat: $archiveFormat, revisionId: $revisionId, publishedAt: $publishedAt)';
}


}

/// @nodoc
abstract mixin class _$CodePackageArtifactLockCopyWith<$Res> implements $CodePackageArtifactLockCopyWith<$Res> {
  factory _$CodePackageArtifactLockCopyWith(_CodePackageArtifactLock value, $Res Function(_CodePackageArtifactLock) _then) = __$CodePackageArtifactLockCopyWithImpl;
@override @useResult
$Res call({
 String artifactUrl, String sha256, int? sizeBytes, String? mediaType, String? archiveFormat, String? revisionId, String? publishedAt
});




}
/// @nodoc
class __$CodePackageArtifactLockCopyWithImpl<$Res>
    implements _$CodePackageArtifactLockCopyWith<$Res> {
  __$CodePackageArtifactLockCopyWithImpl(this._self, this._then);

  final _CodePackageArtifactLock _self;
  final $Res Function(_CodePackageArtifactLock) _then;

/// Create a copy of CodePackageArtifactLock
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? artifactUrl = null,Object? sha256 = null,Object? sizeBytes = freezed,Object? mediaType = freezed,Object? archiveFormat = freezed,Object? revisionId = freezed,Object? publishedAt = freezed,}) {
  return _then(_CodePackageArtifactLock(
artifactUrl: null == artifactUrl ? _self.artifactUrl : artifactUrl // ignore: cast_nullable_to_non_nullable
as String,sha256: null == sha256 ? _self.sha256 : sha256 // ignore: cast_nullable_to_non_nullable
as String,sizeBytes: freezed == sizeBytes ? _self.sizeBytes : sizeBytes // ignore: cast_nullable_to_non_nullable
as int?,mediaType: freezed == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String?,archiveFormat: freezed == archiveFormat ? _self.archiveFormat : archiveFormat // ignore: cast_nullable_to_non_nullable
as String?,revisionId: freezed == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String?,publishedAt: freezed == publishedAt ? _self.publishedAt : publishedAt // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$CodePackageDescriptor {

 String get packageName;@JsonKey(fromJson: CodeLanguageExtension.fromJson, toJson: CodeLanguageExtension.toJson) CodeLanguage get language; String get surface; String get manifestKind; String get manifestRelativePath; String get packageRoot; String? get sourcesRoot; String? get fqnPrefix; String? get version; String? get revisionId; String? get digest; String? get artifactMediaType; int? get artifactSizeBytes; String? get downloadHandle; Map<String, dynamic> get metadata;
/// Create a copy of CodePackageDescriptor
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$CodePackageDescriptorCopyWith<CodePackageDescriptor> get copyWith => _$CodePackageDescriptorCopyWithImpl<CodePackageDescriptor>(this as CodePackageDescriptor, _$identity);

  /// Serializes this CodePackageDescriptor to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is CodePackageDescriptor&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.language, language) || other.language == language)&&(identical(other.surface, surface) || other.surface == surface)&&(identical(other.manifestKind, manifestKind) || other.manifestKind == manifestKind)&&(identical(other.manifestRelativePath, manifestRelativePath) || other.manifestRelativePath == manifestRelativePath)&&(identical(other.packageRoot, packageRoot) || other.packageRoot == packageRoot)&&(identical(other.sourcesRoot, sourcesRoot) || other.sourcesRoot == sourcesRoot)&&(identical(other.fqnPrefix, fqnPrefix) || other.fqnPrefix == fqnPrefix)&&(identical(other.version, version) || other.version == version)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.artifactMediaType, artifactMediaType) || other.artifactMediaType == artifactMediaType)&&(identical(other.artifactSizeBytes, artifactSizeBytes) || other.artifactSizeBytes == artifactSizeBytes)&&(identical(other.downloadHandle, downloadHandle) || other.downloadHandle == downloadHandle)&&const DeepCollectionEquality().equals(other.metadata, metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,packageName,language,surface,manifestKind,manifestRelativePath,packageRoot,sourcesRoot,fqnPrefix,version,revisionId,digest,artifactMediaType,artifactSizeBytes,downloadHandle,const DeepCollectionEquality().hash(metadata));

@override
String toString() {
  return 'CodePackageDescriptor(packageName: $packageName, language: $language, surface: $surface, manifestKind: $manifestKind, manifestRelativePath: $manifestRelativePath, packageRoot: $packageRoot, sourcesRoot: $sourcesRoot, fqnPrefix: $fqnPrefix, version: $version, revisionId: $revisionId, digest: $digest, artifactMediaType: $artifactMediaType, artifactSizeBytes: $artifactSizeBytes, downloadHandle: $downloadHandle, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class $CodePackageDescriptorCopyWith<$Res>  {
  factory $CodePackageDescriptorCopyWith(CodePackageDescriptor value, $Res Function(CodePackageDescriptor) _then) = _$CodePackageDescriptorCopyWithImpl;
@useResult
$Res call({
 String packageName,@JsonKey(fromJson: CodeLanguageExtension.fromJson, toJson: CodeLanguageExtension.toJson) CodeLanguage language, String surface, String manifestKind, String manifestRelativePath, String packageRoot, String? sourcesRoot, String? fqnPrefix, String? version, String? revisionId, String? digest, String? artifactMediaType, int? artifactSizeBytes, String? downloadHandle, Map<String, dynamic> metadata
});




}
/// @nodoc
class _$CodePackageDescriptorCopyWithImpl<$Res>
    implements $CodePackageDescriptorCopyWith<$Res> {
  _$CodePackageDescriptorCopyWithImpl(this._self, this._then);

  final CodePackageDescriptor _self;
  final $Res Function(CodePackageDescriptor) _then;

/// Create a copy of CodePackageDescriptor
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? packageName = null,Object? language = null,Object? surface = null,Object? manifestKind = null,Object? manifestRelativePath = null,Object? packageRoot = null,Object? sourcesRoot = freezed,Object? fqnPrefix = freezed,Object? version = freezed,Object? revisionId = freezed,Object? digest = freezed,Object? artifactMediaType = freezed,Object? artifactSizeBytes = freezed,Object? downloadHandle = freezed,Object? metadata = null,}) {
  return _then(_self.copyWith(
packageName: null == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String,language: null == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as CodeLanguage,surface: null == surface ? _self.surface : surface // ignore: cast_nullable_to_non_nullable
as String,manifestKind: null == manifestKind ? _self.manifestKind : manifestKind // ignore: cast_nullable_to_non_nullable
as String,manifestRelativePath: null == manifestRelativePath ? _self.manifestRelativePath : manifestRelativePath // ignore: cast_nullable_to_non_nullable
as String,packageRoot: null == packageRoot ? _self.packageRoot : packageRoot // ignore: cast_nullable_to_non_nullable
as String,sourcesRoot: freezed == sourcesRoot ? _self.sourcesRoot : sourcesRoot // ignore: cast_nullable_to_non_nullable
as String?,fqnPrefix: freezed == fqnPrefix ? _self.fqnPrefix : fqnPrefix // ignore: cast_nullable_to_non_nullable
as String?,version: freezed == version ? _self.version : version // ignore: cast_nullable_to_non_nullable
as String?,revisionId: freezed == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String?,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,artifactMediaType: freezed == artifactMediaType ? _self.artifactMediaType : artifactMediaType // ignore: cast_nullable_to_non_nullable
as String?,artifactSizeBytes: freezed == artifactSizeBytes ? _self.artifactSizeBytes : artifactSizeBytes // ignore: cast_nullable_to_non_nullable
as int?,downloadHandle: freezed == downloadHandle ? _self.downloadHandle : downloadHandle // ignore: cast_nullable_to_non_nullable
as String?,metadata: null == metadata ? _self.metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [CodePackageDescriptor].
extension CodePackageDescriptorPatterns on CodePackageDescriptor {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _CodePackageDescriptor value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _CodePackageDescriptor() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _CodePackageDescriptor value)  def,}){
final _that = this;
switch (_that) {
case _CodePackageDescriptor():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _CodePackageDescriptor value)?  def,}){
final _that = this;
switch (_that) {
case _CodePackageDescriptor() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJson, toJson: CodeLanguageExtension.toJson)  CodeLanguage language,  String surface,  String manifestKind,  String manifestRelativePath,  String packageRoot,  String? sourcesRoot,  String? fqnPrefix,  String? version,  String? revisionId,  String? digest,  String? artifactMediaType,  int? artifactSizeBytes,  String? downloadHandle,  Map<String, dynamic> metadata)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _CodePackageDescriptor() when def != null:
return def(_that.packageName,_that.language,_that.surface,_that.manifestKind,_that.manifestRelativePath,_that.packageRoot,_that.sourcesRoot,_that.fqnPrefix,_that.version,_that.revisionId,_that.digest,_that.artifactMediaType,_that.artifactSizeBytes,_that.downloadHandle,_that.metadata);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJson, toJson: CodeLanguageExtension.toJson)  CodeLanguage language,  String surface,  String manifestKind,  String manifestRelativePath,  String packageRoot,  String? sourcesRoot,  String? fqnPrefix,  String? version,  String? revisionId,  String? digest,  String? artifactMediaType,  int? artifactSizeBytes,  String? downloadHandle,  Map<String, dynamic> metadata)  def,}) {final _that = this;
switch (_that) {
case _CodePackageDescriptor():
return def(_that.packageName,_that.language,_that.surface,_that.manifestKind,_that.manifestRelativePath,_that.packageRoot,_that.sourcesRoot,_that.fqnPrefix,_that.version,_that.revisionId,_that.digest,_that.artifactMediaType,_that.artifactSizeBytes,_that.downloadHandle,_that.metadata);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJson, toJson: CodeLanguageExtension.toJson)  CodeLanguage language,  String surface,  String manifestKind,  String manifestRelativePath,  String packageRoot,  String? sourcesRoot,  String? fqnPrefix,  String? version,  String? revisionId,  String? digest,  String? artifactMediaType,  int? artifactSizeBytes,  String? downloadHandle,  Map<String, dynamic> metadata)?  def,}) {final _that = this;
switch (_that) {
case _CodePackageDescriptor() when def != null:
return def(_that.packageName,_that.language,_that.surface,_that.manifestKind,_that.manifestRelativePath,_that.packageRoot,_that.sourcesRoot,_that.fqnPrefix,_that.version,_that.revisionId,_that.digest,_that.artifactMediaType,_that.artifactSizeBytes,_that.downloadHandle,_that.metadata);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _CodePackageDescriptor implements CodePackageDescriptor {
   _CodePackageDescriptor({required this.packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJson, toJson: CodeLanguageExtension.toJson) required this.language, required this.surface, required this.manifestKind, required this.manifestRelativePath, required this.packageRoot, this.sourcesRoot, this.fqnPrefix, this.version, this.revisionId, this.digest, this.artifactMediaType, this.artifactSizeBytes, this.downloadHandle, required final  Map<String, dynamic> metadata}): _metadata = metadata;
  factory _CodePackageDescriptor.fromJson(Map<String, dynamic> json) => _$CodePackageDescriptorFromJson(json);

@override final  String packageName;
@override@JsonKey(fromJson: CodeLanguageExtension.fromJson, toJson: CodeLanguageExtension.toJson) final  CodeLanguage language;
@override final  String surface;
@override final  String manifestKind;
@override final  String manifestRelativePath;
@override final  String packageRoot;
@override final  String? sourcesRoot;
@override final  String? fqnPrefix;
@override final  String? version;
@override final  String? revisionId;
@override final  String? digest;
@override final  String? artifactMediaType;
@override final  int? artifactSizeBytes;
@override final  String? downloadHandle;
 final  Map<String, dynamic> _metadata;
@override Map<String, dynamic> get metadata {
  if (_metadata is EqualUnmodifiableMapView) return _metadata;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_metadata);
}


/// Create a copy of CodePackageDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$CodePackageDescriptorCopyWith<_CodePackageDescriptor> get copyWith => __$CodePackageDescriptorCopyWithImpl<_CodePackageDescriptor>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$CodePackageDescriptorToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _CodePackageDescriptor&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.language, language) || other.language == language)&&(identical(other.surface, surface) || other.surface == surface)&&(identical(other.manifestKind, manifestKind) || other.manifestKind == manifestKind)&&(identical(other.manifestRelativePath, manifestRelativePath) || other.manifestRelativePath == manifestRelativePath)&&(identical(other.packageRoot, packageRoot) || other.packageRoot == packageRoot)&&(identical(other.sourcesRoot, sourcesRoot) || other.sourcesRoot == sourcesRoot)&&(identical(other.fqnPrefix, fqnPrefix) || other.fqnPrefix == fqnPrefix)&&(identical(other.version, version) || other.version == version)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.artifactMediaType, artifactMediaType) || other.artifactMediaType == artifactMediaType)&&(identical(other.artifactSizeBytes, artifactSizeBytes) || other.artifactSizeBytes == artifactSizeBytes)&&(identical(other.downloadHandle, downloadHandle) || other.downloadHandle == downloadHandle)&&const DeepCollectionEquality().equals(other._metadata, _metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,packageName,language,surface,manifestKind,manifestRelativePath,packageRoot,sourcesRoot,fqnPrefix,version,revisionId,digest,artifactMediaType,artifactSizeBytes,downloadHandle,const DeepCollectionEquality().hash(_metadata));

@override
String toString() {
  return 'CodePackageDescriptor.def(packageName: $packageName, language: $language, surface: $surface, manifestKind: $manifestKind, manifestRelativePath: $manifestRelativePath, packageRoot: $packageRoot, sourcesRoot: $sourcesRoot, fqnPrefix: $fqnPrefix, version: $version, revisionId: $revisionId, digest: $digest, artifactMediaType: $artifactMediaType, artifactSizeBytes: $artifactSizeBytes, downloadHandle: $downloadHandle, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class _$CodePackageDescriptorCopyWith<$Res> implements $CodePackageDescriptorCopyWith<$Res> {
  factory _$CodePackageDescriptorCopyWith(_CodePackageDescriptor value, $Res Function(_CodePackageDescriptor) _then) = __$CodePackageDescriptorCopyWithImpl;
@override @useResult
$Res call({
 String packageName,@JsonKey(fromJson: CodeLanguageExtension.fromJson, toJson: CodeLanguageExtension.toJson) CodeLanguage language, String surface, String manifestKind, String manifestRelativePath, String packageRoot, String? sourcesRoot, String? fqnPrefix, String? version, String? revisionId, String? digest, String? artifactMediaType, int? artifactSizeBytes, String? downloadHandle, Map<String, dynamic> metadata
});




}
/// @nodoc
class __$CodePackageDescriptorCopyWithImpl<$Res>
    implements _$CodePackageDescriptorCopyWith<$Res> {
  __$CodePackageDescriptorCopyWithImpl(this._self, this._then);

  final _CodePackageDescriptor _self;
  final $Res Function(_CodePackageDescriptor) _then;

/// Create a copy of CodePackageDescriptor
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? packageName = null,Object? language = null,Object? surface = null,Object? manifestKind = null,Object? manifestRelativePath = null,Object? packageRoot = null,Object? sourcesRoot = freezed,Object? fqnPrefix = freezed,Object? version = freezed,Object? revisionId = freezed,Object? digest = freezed,Object? artifactMediaType = freezed,Object? artifactSizeBytes = freezed,Object? downloadHandle = freezed,Object? metadata = null,}) {
  return _then(_CodePackageDescriptor(
packageName: null == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String,language: null == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as CodeLanguage,surface: null == surface ? _self.surface : surface // ignore: cast_nullable_to_non_nullable
as String,manifestKind: null == manifestKind ? _self.manifestKind : manifestKind // ignore: cast_nullable_to_non_nullable
as String,manifestRelativePath: null == manifestRelativePath ? _self.manifestRelativePath : manifestRelativePath // ignore: cast_nullable_to_non_nullable
as String,packageRoot: null == packageRoot ? _self.packageRoot : packageRoot // ignore: cast_nullable_to_non_nullable
as String,sourcesRoot: freezed == sourcesRoot ? _self.sourcesRoot : sourcesRoot // ignore: cast_nullable_to_non_nullable
as String?,fqnPrefix: freezed == fqnPrefix ? _self.fqnPrefix : fqnPrefix // ignore: cast_nullable_to_non_nullable
as String?,version: freezed == version ? _self.version : version // ignore: cast_nullable_to_non_nullable
as String?,revisionId: freezed == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String?,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,artifactMediaType: freezed == artifactMediaType ? _self.artifactMediaType : artifactMediaType // ignore: cast_nullable_to_non_nullable
as String?,artifactSizeBytes: freezed == artifactSizeBytes ? _self.artifactSizeBytes : artifactSizeBytes // ignore: cast_nullable_to_non_nullable
as int?,downloadHandle: freezed == downloadHandle ? _self.downloadHandle : downloadHandle // ignore: cast_nullable_to_non_nullable
as String?,metadata: null == metadata ? _self._metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$CodePackageChannelHead {

 String get packageName;@JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable) CodeLanguage? get language; String? get surface; String get channel; String get revisionId; String? get updatedAt; String? get publisherExecutionId; String? get idempotencyKey; Map<String, dynamic> get metadata;
/// Create a copy of CodePackageChannelHead
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$CodePackageChannelHeadCopyWith<CodePackageChannelHead> get copyWith => _$CodePackageChannelHeadCopyWithImpl<CodePackageChannelHead>(this as CodePackageChannelHead, _$identity);

  /// Serializes this CodePackageChannelHead to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is CodePackageChannelHead&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.language, language) || other.language == language)&&(identical(other.surface, surface) || other.surface == surface)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.updatedAt, updatedAt) || other.updatedAt == updatedAt)&&(identical(other.publisherExecutionId, publisherExecutionId) || other.publisherExecutionId == publisherExecutionId)&&(identical(other.idempotencyKey, idempotencyKey) || other.idempotencyKey == idempotencyKey)&&const DeepCollectionEquality().equals(other.metadata, metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,packageName,language,surface,channel,revisionId,updatedAt,publisherExecutionId,idempotencyKey,const DeepCollectionEquality().hash(metadata));

@override
String toString() {
  return 'CodePackageChannelHead(packageName: $packageName, language: $language, surface: $surface, channel: $channel, revisionId: $revisionId, updatedAt: $updatedAt, publisherExecutionId: $publisherExecutionId, idempotencyKey: $idempotencyKey, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class $CodePackageChannelHeadCopyWith<$Res>  {
  factory $CodePackageChannelHeadCopyWith(CodePackageChannelHead value, $Res Function(CodePackageChannelHead) _then) = _$CodePackageChannelHeadCopyWithImpl;
@useResult
$Res call({
 String packageName,@JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable) CodeLanguage? language, String? surface, String channel, String revisionId, String? updatedAt, String? publisherExecutionId, String? idempotencyKey, Map<String, dynamic> metadata
});




}
/// @nodoc
class _$CodePackageChannelHeadCopyWithImpl<$Res>
    implements $CodePackageChannelHeadCopyWith<$Res> {
  _$CodePackageChannelHeadCopyWithImpl(this._self, this._then);

  final CodePackageChannelHead _self;
  final $Res Function(CodePackageChannelHead) _then;

/// Create a copy of CodePackageChannelHead
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? packageName = null,Object? language = freezed,Object? surface = freezed,Object? channel = null,Object? revisionId = null,Object? updatedAt = freezed,Object? publisherExecutionId = freezed,Object? idempotencyKey = freezed,Object? metadata = null,}) {
  return _then(_self.copyWith(
packageName: null == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String,language: freezed == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as CodeLanguage?,surface: freezed == surface ? _self.surface : surface // ignore: cast_nullable_to_non_nullable
as String?,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,revisionId: null == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String,updatedAt: freezed == updatedAt ? _self.updatedAt : updatedAt // ignore: cast_nullable_to_non_nullable
as String?,publisherExecutionId: freezed == publisherExecutionId ? _self.publisherExecutionId : publisherExecutionId // ignore: cast_nullable_to_non_nullable
as String?,idempotencyKey: freezed == idempotencyKey ? _self.idempotencyKey : idempotencyKey // ignore: cast_nullable_to_non_nullable
as String?,metadata: null == metadata ? _self.metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [CodePackageChannelHead].
extension CodePackageChannelHeadPatterns on CodePackageChannelHead {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _CodePackageChannelHead value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _CodePackageChannelHead() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _CodePackageChannelHead value)  def,}){
final _that = this;
switch (_that) {
case _CodePackageChannelHead():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _CodePackageChannelHead value)?  def,}){
final _that = this;
switch (_that) {
case _CodePackageChannelHead() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable)  CodeLanguage? language,  String? surface,  String channel,  String revisionId,  String? updatedAt,  String? publisherExecutionId,  String? idempotencyKey,  Map<String, dynamic> metadata)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _CodePackageChannelHead() when def != null:
return def(_that.packageName,_that.language,_that.surface,_that.channel,_that.revisionId,_that.updatedAt,_that.publisherExecutionId,_that.idempotencyKey,_that.metadata);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable)  CodeLanguage? language,  String? surface,  String channel,  String revisionId,  String? updatedAt,  String? publisherExecutionId,  String? idempotencyKey,  Map<String, dynamic> metadata)  def,}) {final _that = this;
switch (_that) {
case _CodePackageChannelHead():
return def(_that.packageName,_that.language,_that.surface,_that.channel,_that.revisionId,_that.updatedAt,_that.publisherExecutionId,_that.idempotencyKey,_that.metadata);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable)  CodeLanguage? language,  String? surface,  String channel,  String revisionId,  String? updatedAt,  String? publisherExecutionId,  String? idempotencyKey,  Map<String, dynamic> metadata)?  def,}) {final _that = this;
switch (_that) {
case _CodePackageChannelHead() when def != null:
return def(_that.packageName,_that.language,_that.surface,_that.channel,_that.revisionId,_that.updatedAt,_that.publisherExecutionId,_that.idempotencyKey,_that.metadata);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _CodePackageChannelHead implements CodePackageChannelHead {
   _CodePackageChannelHead({required this.packageName, @JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable) this.language, this.surface, required this.channel, required this.revisionId, this.updatedAt, this.publisherExecutionId, this.idempotencyKey, required final  Map<String, dynamic> metadata}): _metadata = metadata;
  factory _CodePackageChannelHead.fromJson(Map<String, dynamic> json) => _$CodePackageChannelHeadFromJson(json);

@override final  String packageName;
@override@JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable) final  CodeLanguage? language;
@override final  String? surface;
@override final  String channel;
@override final  String revisionId;
@override final  String? updatedAt;
@override final  String? publisherExecutionId;
@override final  String? idempotencyKey;
 final  Map<String, dynamic> _metadata;
@override Map<String, dynamic> get metadata {
  if (_metadata is EqualUnmodifiableMapView) return _metadata;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_metadata);
}


/// Create a copy of CodePackageChannelHead
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$CodePackageChannelHeadCopyWith<_CodePackageChannelHead> get copyWith => __$CodePackageChannelHeadCopyWithImpl<_CodePackageChannelHead>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$CodePackageChannelHeadToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _CodePackageChannelHead&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.language, language) || other.language == language)&&(identical(other.surface, surface) || other.surface == surface)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.updatedAt, updatedAt) || other.updatedAt == updatedAt)&&(identical(other.publisherExecutionId, publisherExecutionId) || other.publisherExecutionId == publisherExecutionId)&&(identical(other.idempotencyKey, idempotencyKey) || other.idempotencyKey == idempotencyKey)&&const DeepCollectionEquality().equals(other._metadata, _metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,packageName,language,surface,channel,revisionId,updatedAt,publisherExecutionId,idempotencyKey,const DeepCollectionEquality().hash(_metadata));

@override
String toString() {
  return 'CodePackageChannelHead.def(packageName: $packageName, language: $language, surface: $surface, channel: $channel, revisionId: $revisionId, updatedAt: $updatedAt, publisherExecutionId: $publisherExecutionId, idempotencyKey: $idempotencyKey, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class _$CodePackageChannelHeadCopyWith<$Res> implements $CodePackageChannelHeadCopyWith<$Res> {
  factory _$CodePackageChannelHeadCopyWith(_CodePackageChannelHead value, $Res Function(_CodePackageChannelHead) _then) = __$CodePackageChannelHeadCopyWithImpl;
@override @useResult
$Res call({
 String packageName,@JsonKey(fromJson: CodeLanguageExtension.fromJsonNullable, toJson: CodeLanguageExtension.toJsonNullable) CodeLanguage? language, String? surface, String channel, String revisionId, String? updatedAt, String? publisherExecutionId, String? idempotencyKey, Map<String, dynamic> metadata
});




}
/// @nodoc
class __$CodePackageChannelHeadCopyWithImpl<$Res>
    implements _$CodePackageChannelHeadCopyWith<$Res> {
  __$CodePackageChannelHeadCopyWithImpl(this._self, this._then);

  final _CodePackageChannelHead _self;
  final $Res Function(_CodePackageChannelHead) _then;

/// Create a copy of CodePackageChannelHead
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? packageName = null,Object? language = freezed,Object? surface = freezed,Object? channel = null,Object? revisionId = null,Object? updatedAt = freezed,Object? publisherExecutionId = freezed,Object? idempotencyKey = freezed,Object? metadata = null,}) {
  return _then(_CodePackageChannelHead(
packageName: null == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String,language: freezed == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as CodeLanguage?,surface: freezed == surface ? _self.surface : surface // ignore: cast_nullable_to_non_nullable
as String?,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,revisionId: null == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String,updatedAt: freezed == updatedAt ? _self.updatedAt : updatedAt // ignore: cast_nullable_to_non_nullable
as String?,publisherExecutionId: freezed == publisherExecutionId ? _self.publisherExecutionId : publisherExecutionId // ignore: cast_nullable_to_non_nullable
as String?,idempotencyKey: freezed == idempotencyKey ? _self.idempotencyKey : idempotencyKey // ignore: cast_nullable_to_non_nullable
as String?,metadata: null == metadata ? _self._metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$CodePackageDiscoveryEntry {

 CodePackageChannelHead get channelHead; CodePackageDescriptor? get descriptor; CodePackageArtifactLock? get artifactLock;
/// Create a copy of CodePackageDiscoveryEntry
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$CodePackageDiscoveryEntryCopyWith<CodePackageDiscoveryEntry> get copyWith => _$CodePackageDiscoveryEntryCopyWithImpl<CodePackageDiscoveryEntry>(this as CodePackageDiscoveryEntry, _$identity);

  /// Serializes this CodePackageDiscoveryEntry to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is CodePackageDiscoveryEntry&&(identical(other.channelHead, channelHead) || other.channelHead == channelHead)&&(identical(other.descriptor, descriptor) || other.descriptor == descriptor)&&(identical(other.artifactLock, artifactLock) || other.artifactLock == artifactLock));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,channelHead,descriptor,artifactLock);

@override
String toString() {
  return 'CodePackageDiscoveryEntry(channelHead: $channelHead, descriptor: $descriptor, artifactLock: $artifactLock)';
}


}

/// @nodoc
abstract mixin class $CodePackageDiscoveryEntryCopyWith<$Res>  {
  factory $CodePackageDiscoveryEntryCopyWith(CodePackageDiscoveryEntry value, $Res Function(CodePackageDiscoveryEntry) _then) = _$CodePackageDiscoveryEntryCopyWithImpl;
@useResult
$Res call({
 CodePackageChannelHead channelHead, CodePackageDescriptor? descriptor, CodePackageArtifactLock? artifactLock
});


$CodePackageChannelHeadCopyWith<$Res> get channelHead;$CodePackageDescriptorCopyWith<$Res>? get descriptor;$CodePackageArtifactLockCopyWith<$Res>? get artifactLock;

}
/// @nodoc
class _$CodePackageDiscoveryEntryCopyWithImpl<$Res>
    implements $CodePackageDiscoveryEntryCopyWith<$Res> {
  _$CodePackageDiscoveryEntryCopyWithImpl(this._self, this._then);

  final CodePackageDiscoveryEntry _self;
  final $Res Function(CodePackageDiscoveryEntry) _then;

/// Create a copy of CodePackageDiscoveryEntry
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? channelHead = null,Object? descriptor = freezed,Object? artifactLock = freezed,}) {
  return _then(_self.copyWith(
channelHead: null == channelHead ? _self.channelHead : channelHead // ignore: cast_nullable_to_non_nullable
as CodePackageChannelHead,descriptor: freezed == descriptor ? _self.descriptor : descriptor // ignore: cast_nullable_to_non_nullable
as CodePackageDescriptor?,artifactLock: freezed == artifactLock ? _self.artifactLock : artifactLock // ignore: cast_nullable_to_non_nullable
as CodePackageArtifactLock?,
  ));
}
/// Create a copy of CodePackageDiscoveryEntry
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageChannelHeadCopyWith<$Res> get channelHead {
  
  return $CodePackageChannelHeadCopyWith<$Res>(_self.channelHead, (value) {
    return _then(_self.copyWith(channelHead: value));
  });
}/// Create a copy of CodePackageDiscoveryEntry
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageDescriptorCopyWith<$Res>? get descriptor {
    if (_self.descriptor == null) {
    return null;
  }

  return $CodePackageDescriptorCopyWith<$Res>(_self.descriptor!, (value) {
    return _then(_self.copyWith(descriptor: value));
  });
}/// Create a copy of CodePackageDiscoveryEntry
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageArtifactLockCopyWith<$Res>? get artifactLock {
    if (_self.artifactLock == null) {
    return null;
  }

  return $CodePackageArtifactLockCopyWith<$Res>(_self.artifactLock!, (value) {
    return _then(_self.copyWith(artifactLock: value));
  });
}
}


/// Adds pattern-matching-related methods to [CodePackageDiscoveryEntry].
extension CodePackageDiscoveryEntryPatterns on CodePackageDiscoveryEntry {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _CodePackageDiscoveryEntry value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _CodePackageDiscoveryEntry() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _CodePackageDiscoveryEntry value)  def,}){
final _that = this;
switch (_that) {
case _CodePackageDiscoveryEntry():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _CodePackageDiscoveryEntry value)?  def,}){
final _that = this;
switch (_that) {
case _CodePackageDiscoveryEntry() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( CodePackageChannelHead channelHead,  CodePackageDescriptor? descriptor,  CodePackageArtifactLock? artifactLock)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _CodePackageDiscoveryEntry() when def != null:
return def(_that.channelHead,_that.descriptor,_that.artifactLock);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( CodePackageChannelHead channelHead,  CodePackageDescriptor? descriptor,  CodePackageArtifactLock? artifactLock)  def,}) {final _that = this;
switch (_that) {
case _CodePackageDiscoveryEntry():
return def(_that.channelHead,_that.descriptor,_that.artifactLock);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( CodePackageChannelHead channelHead,  CodePackageDescriptor? descriptor,  CodePackageArtifactLock? artifactLock)?  def,}) {final _that = this;
switch (_that) {
case _CodePackageDiscoveryEntry() when def != null:
return def(_that.channelHead,_that.descriptor,_that.artifactLock);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _CodePackageDiscoveryEntry implements CodePackageDiscoveryEntry {
   _CodePackageDiscoveryEntry({required this.channelHead, this.descriptor, this.artifactLock});
  factory _CodePackageDiscoveryEntry.fromJson(Map<String, dynamic> json) => _$CodePackageDiscoveryEntryFromJson(json);

@override final  CodePackageChannelHead channelHead;
@override final  CodePackageDescriptor? descriptor;
@override final  CodePackageArtifactLock? artifactLock;

/// Create a copy of CodePackageDiscoveryEntry
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$CodePackageDiscoveryEntryCopyWith<_CodePackageDiscoveryEntry> get copyWith => __$CodePackageDiscoveryEntryCopyWithImpl<_CodePackageDiscoveryEntry>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$CodePackageDiscoveryEntryToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _CodePackageDiscoveryEntry&&(identical(other.channelHead, channelHead) || other.channelHead == channelHead)&&(identical(other.descriptor, descriptor) || other.descriptor == descriptor)&&(identical(other.artifactLock, artifactLock) || other.artifactLock == artifactLock));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,channelHead,descriptor,artifactLock);

@override
String toString() {
  return 'CodePackageDiscoveryEntry.def(channelHead: $channelHead, descriptor: $descriptor, artifactLock: $artifactLock)';
}


}

/// @nodoc
abstract mixin class _$CodePackageDiscoveryEntryCopyWith<$Res> implements $CodePackageDiscoveryEntryCopyWith<$Res> {
  factory _$CodePackageDiscoveryEntryCopyWith(_CodePackageDiscoveryEntry value, $Res Function(_CodePackageDiscoveryEntry) _then) = __$CodePackageDiscoveryEntryCopyWithImpl;
@override @useResult
$Res call({
 CodePackageChannelHead channelHead, CodePackageDescriptor? descriptor, CodePackageArtifactLock? artifactLock
});


@override $CodePackageChannelHeadCopyWith<$Res> get channelHead;@override $CodePackageDescriptorCopyWith<$Res>? get descriptor;@override $CodePackageArtifactLockCopyWith<$Res>? get artifactLock;

}
/// @nodoc
class __$CodePackageDiscoveryEntryCopyWithImpl<$Res>
    implements _$CodePackageDiscoveryEntryCopyWith<$Res> {
  __$CodePackageDiscoveryEntryCopyWithImpl(this._self, this._then);

  final _CodePackageDiscoveryEntry _self;
  final $Res Function(_CodePackageDiscoveryEntry) _then;

/// Create a copy of CodePackageDiscoveryEntry
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? channelHead = null,Object? descriptor = freezed,Object? artifactLock = freezed,}) {
  return _then(_CodePackageDiscoveryEntry(
channelHead: null == channelHead ? _self.channelHead : channelHead // ignore: cast_nullable_to_non_nullable
as CodePackageChannelHead,descriptor: freezed == descriptor ? _self.descriptor : descriptor // ignore: cast_nullable_to_non_nullable
as CodePackageDescriptor?,artifactLock: freezed == artifactLock ? _self.artifactLock : artifactLock // ignore: cast_nullable_to_non_nullable
as CodePackageArtifactLock?,
  ));
}

/// Create a copy of CodePackageDiscoveryEntry
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageChannelHeadCopyWith<$Res> get channelHead {
  
  return $CodePackageChannelHeadCopyWith<$Res>(_self.channelHead, (value) {
    return _then(_self.copyWith(channelHead: value));
  });
}/// Create a copy of CodePackageDiscoveryEntry
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageDescriptorCopyWith<$Res>? get descriptor {
    if (_self.descriptor == null) {
    return null;
  }

  return $CodePackageDescriptorCopyWith<$Res>(_self.descriptor!, (value) {
    return _then(_self.copyWith(descriptor: value));
  });
}/// Create a copy of CodePackageDiscoveryEntry
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CodePackageArtifactLockCopyWith<$Res>? get artifactLock {
    if (_self.artifactLock == null) {
    return null;
  }

  return $CodePackageArtifactLockCopyWith<$Res>(_self.artifactLock!, (value) {
    return _then(_self.copyWith(artifactLock: value));
  });
}
}

// dart format on
