// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'public_map_discovery_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;
PublicMapDiscoveryRequest _$PublicMapDiscoveryRequestFromJson(
  Map<String, dynamic> json
) {
    return DiscoverPublicMapRequest.fromJson(
      json
    );
}

/// @nodoc
mixin _$PublicMapDiscoveryRequest {

@UuidValueConverter() UuidValue? get requestId; String? get query; String? get artifactFamily; String? get artifactKey; String? get packageName; String? get experienceName; String? get channel; String? get authorityBaseUrl; String? get indexUrl; int get limit;
/// Create a copy of PublicMapDiscoveryRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$PublicMapDiscoveryRequestCopyWith<PublicMapDiscoveryRequest> get copyWith => _$PublicMapDiscoveryRequestCopyWithImpl<PublicMapDiscoveryRequest>(this as PublicMapDiscoveryRequest, _$identity);

  /// Serializes this PublicMapDiscoveryRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is PublicMapDiscoveryRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.query, query) || other.query == query)&&(identical(other.artifactFamily, artifactFamily) || other.artifactFamily == artifactFamily)&&(identical(other.artifactKey, artifactKey) || other.artifactKey == artifactKey)&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.experienceName, experienceName) || other.experienceName == experienceName)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.authorityBaseUrl, authorityBaseUrl) || other.authorityBaseUrl == authorityBaseUrl)&&(identical(other.indexUrl, indexUrl) || other.indexUrl == indexUrl)&&(identical(other.limit, limit) || other.limit == limit));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,query,artifactFamily,artifactKey,packageName,experienceName,channel,authorityBaseUrl,indexUrl,limit);

@override
String toString() {
  return 'PublicMapDiscoveryRequest(requestId: $requestId, query: $query, artifactFamily: $artifactFamily, artifactKey: $artifactKey, packageName: $packageName, experienceName: $experienceName, channel: $channel, authorityBaseUrl: $authorityBaseUrl, indexUrl: $indexUrl, limit: $limit)';
}


}

/// @nodoc
abstract mixin class $PublicMapDiscoveryRequestCopyWith<$Res>  {
  factory $PublicMapDiscoveryRequestCopyWith(PublicMapDiscoveryRequest value, $Res Function(PublicMapDiscoveryRequest) _then) = _$PublicMapDiscoveryRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, String? query, String? artifactFamily, String? artifactKey, String? packageName, String? experienceName, String? channel, String? authorityBaseUrl, String? indexUrl, int limit
});




}
/// @nodoc
class _$PublicMapDiscoveryRequestCopyWithImpl<$Res>
    implements $PublicMapDiscoveryRequestCopyWith<$Res> {
  _$PublicMapDiscoveryRequestCopyWithImpl(this._self, this._then);

  final PublicMapDiscoveryRequest _self;
  final $Res Function(PublicMapDiscoveryRequest) _then;

/// Create a copy of PublicMapDiscoveryRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? query = freezed,Object? artifactFamily = freezed,Object? artifactKey = freezed,Object? packageName = freezed,Object? experienceName = freezed,Object? channel = freezed,Object? authorityBaseUrl = freezed,Object? indexUrl = freezed,Object? limit = null,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,query: freezed == query ? _self.query : query // ignore: cast_nullable_to_non_nullable
as String?,artifactFamily: freezed == artifactFamily ? _self.artifactFamily : artifactFamily // ignore: cast_nullable_to_non_nullable
as String?,artifactKey: freezed == artifactKey ? _self.artifactKey : artifactKey // ignore: cast_nullable_to_non_nullable
as String?,packageName: freezed == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String?,experienceName: freezed == experienceName ? _self.experienceName : experienceName // ignore: cast_nullable_to_non_nullable
as String?,channel: freezed == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String?,authorityBaseUrl: freezed == authorityBaseUrl ? _self.authorityBaseUrl : authorityBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,indexUrl: freezed == indexUrl ? _self.indexUrl : indexUrl // ignore: cast_nullable_to_non_nullable
as String?,limit: null == limit ? _self.limit : limit // ignore: cast_nullable_to_non_nullable
as int,
  ));
}

}


/// Adds pattern-matching-related methods to [PublicMapDiscoveryRequest].
extension PublicMapDiscoveryRequestPatterns on PublicMapDiscoveryRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( DiscoverPublicMapRequest value)?  discoverPublicMap,required TResult orElse(),}){
final _that = this;
switch (_that) {
case DiscoverPublicMapRequest() when discoverPublicMap != null:
return discoverPublicMap(_that);case _:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( DiscoverPublicMapRequest value)  discoverPublicMap,}){
final _that = this;
switch (_that) {
case DiscoverPublicMapRequest():
return discoverPublicMap(_that);case _:
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( DiscoverPublicMapRequest value)?  discoverPublicMap,}){
final _that = this;
switch (_that) {
case DiscoverPublicMapRequest() when discoverPublicMap != null:
return discoverPublicMap(_that);case _:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  String? query,  String? artifactFamily,  String? artifactKey,  String? packageName,  String? experienceName,  String? channel,  String? authorityBaseUrl,  String? indexUrl,  int limit)?  discoverPublicMap,required TResult orElse(),}) {final _that = this;
switch (_that) {
case DiscoverPublicMapRequest() when discoverPublicMap != null:
return discoverPublicMap(_that.requestId,_that.query,_that.artifactFamily,_that.artifactKey,_that.packageName,_that.experienceName,_that.channel,_that.authorityBaseUrl,_that.indexUrl,_that.limit);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  String? query,  String? artifactFamily,  String? artifactKey,  String? packageName,  String? experienceName,  String? channel,  String? authorityBaseUrl,  String? indexUrl,  int limit)  discoverPublicMap,}) {final _that = this;
switch (_that) {
case DiscoverPublicMapRequest():
return discoverPublicMap(_that.requestId,_that.query,_that.artifactFamily,_that.artifactKey,_that.packageName,_that.experienceName,_that.channel,_that.authorityBaseUrl,_that.indexUrl,_that.limit);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  String? query,  String? artifactFamily,  String? artifactKey,  String? packageName,  String? experienceName,  String? channel,  String? authorityBaseUrl,  String? indexUrl,  int limit)?  discoverPublicMap,}) {final _that = this;
switch (_that) {
case DiscoverPublicMapRequest() when discoverPublicMap != null:
return discoverPublicMap(_that.requestId,_that.query,_that.artifactFamily,_that.artifactKey,_that.packageName,_that.experienceName,_that.channel,_that.authorityBaseUrl,_that.indexUrl,_that.limit);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DiscoverPublicMapRequest implements PublicMapDiscoveryRequest {
   DiscoverPublicMapRequest({@UuidValueConverter() this.requestId, this.query, this.artifactFamily, this.artifactKey, this.packageName, this.experienceName, this.channel, this.authorityBaseUrl, this.indexUrl, required this.limit});
  factory DiscoverPublicMapRequest.fromJson(Map<String, dynamic> json) => _$DiscoverPublicMapRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  String? query;
@override final  String? artifactFamily;
@override final  String? artifactKey;
@override final  String? packageName;
@override final  String? experienceName;
@override final  String? channel;
@override final  String? authorityBaseUrl;
@override final  String? indexUrl;
@override final  int limit;

/// Create a copy of PublicMapDiscoveryRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DiscoverPublicMapRequestCopyWith<DiscoverPublicMapRequest> get copyWith => _$DiscoverPublicMapRequestCopyWithImpl<DiscoverPublicMapRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DiscoverPublicMapRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DiscoverPublicMapRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.query, query) || other.query == query)&&(identical(other.artifactFamily, artifactFamily) || other.artifactFamily == artifactFamily)&&(identical(other.artifactKey, artifactKey) || other.artifactKey == artifactKey)&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.experienceName, experienceName) || other.experienceName == experienceName)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.authorityBaseUrl, authorityBaseUrl) || other.authorityBaseUrl == authorityBaseUrl)&&(identical(other.indexUrl, indexUrl) || other.indexUrl == indexUrl)&&(identical(other.limit, limit) || other.limit == limit));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,query,artifactFamily,artifactKey,packageName,experienceName,channel,authorityBaseUrl,indexUrl,limit);

@override
String toString() {
  return 'PublicMapDiscoveryRequest.discoverPublicMap(requestId: $requestId, query: $query, artifactFamily: $artifactFamily, artifactKey: $artifactKey, packageName: $packageName, experienceName: $experienceName, channel: $channel, authorityBaseUrl: $authorityBaseUrl, indexUrl: $indexUrl, limit: $limit)';
}


}

/// @nodoc
abstract mixin class $DiscoverPublicMapRequestCopyWith<$Res> implements $PublicMapDiscoveryRequestCopyWith<$Res> {
  factory $DiscoverPublicMapRequestCopyWith(DiscoverPublicMapRequest value, $Res Function(DiscoverPublicMapRequest) _then) = _$DiscoverPublicMapRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, String? query, String? artifactFamily, String? artifactKey, String? packageName, String? experienceName, String? channel, String? authorityBaseUrl, String? indexUrl, int limit
});




}
/// @nodoc
class _$DiscoverPublicMapRequestCopyWithImpl<$Res>
    implements $DiscoverPublicMapRequestCopyWith<$Res> {
  _$DiscoverPublicMapRequestCopyWithImpl(this._self, this._then);

  final DiscoverPublicMapRequest _self;
  final $Res Function(DiscoverPublicMapRequest) _then;

/// Create a copy of PublicMapDiscoveryRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? query = freezed,Object? artifactFamily = freezed,Object? artifactKey = freezed,Object? packageName = freezed,Object? experienceName = freezed,Object? channel = freezed,Object? authorityBaseUrl = freezed,Object? indexUrl = freezed,Object? limit = null,}) {
  return _then(DiscoverPublicMapRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,query: freezed == query ? _self.query : query // ignore: cast_nullable_to_non_nullable
as String?,artifactFamily: freezed == artifactFamily ? _self.artifactFamily : artifactFamily // ignore: cast_nullable_to_non_nullable
as String?,artifactKey: freezed == artifactKey ? _self.artifactKey : artifactKey // ignore: cast_nullable_to_non_nullable
as String?,packageName: freezed == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String?,experienceName: freezed == experienceName ? _self.experienceName : experienceName // ignore: cast_nullable_to_non_nullable
as String?,channel: freezed == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String?,authorityBaseUrl: freezed == authorityBaseUrl ? _self.authorityBaseUrl : authorityBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,indexUrl: freezed == indexUrl ? _self.indexUrl : indexUrl // ignore: cast_nullable_to_non_nullable
as String?,limit: null == limit ? _self.limit : limit // ignore: cast_nullable_to_non_nullable
as int,
  ));
}


}

PublicMapDiscoveryResponse _$PublicMapDiscoveryResponseFromJson(
  Map<String, dynamic> json
) {
    return DiscoverPublicMapResponse.fromJson(
      json
    );
}

/// @nodoc
mixin _$PublicMapDiscoveryResponse {

@UuidValueConverter() UuidValue? get requestId; bool get success; String? get info; String? get error; String? get authoritySourceUrl; List<HubPublicMapEntry> get entries;
/// Create a copy of PublicMapDiscoveryResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$PublicMapDiscoveryResponseCopyWith<PublicMapDiscoveryResponse> get copyWith => _$PublicMapDiscoveryResponseCopyWithImpl<PublicMapDiscoveryResponse>(this as PublicMapDiscoveryResponse, _$identity);

  /// Serializes this PublicMapDiscoveryResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is PublicMapDiscoveryResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.info, info) || other.info == info)&&(identical(other.error, error) || other.error == error)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl)&&const DeepCollectionEquality().equals(other.entries, entries));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,info,error,authoritySourceUrl,const DeepCollectionEquality().hash(entries));

@override
String toString() {
  return 'PublicMapDiscoveryResponse(requestId: $requestId, success: $success, info: $info, error: $error, authoritySourceUrl: $authoritySourceUrl, entries: $entries)';
}


}

/// @nodoc
abstract mixin class $PublicMapDiscoveryResponseCopyWith<$Res>  {
  factory $PublicMapDiscoveryResponseCopyWith(PublicMapDiscoveryResponse value, $Res Function(PublicMapDiscoveryResponse) _then) = _$PublicMapDiscoveryResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? info, String? error, String? authoritySourceUrl, List<HubPublicMapEntry> entries
});




}
/// @nodoc
class _$PublicMapDiscoveryResponseCopyWithImpl<$Res>
    implements $PublicMapDiscoveryResponseCopyWith<$Res> {
  _$PublicMapDiscoveryResponseCopyWithImpl(this._self, this._then);

  final PublicMapDiscoveryResponse _self;
  final $Res Function(PublicMapDiscoveryResponse) _then;

/// Create a copy of PublicMapDiscoveryResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? success = null,Object? info = freezed,Object? error = freezed,Object? authoritySourceUrl = freezed,Object? entries = null,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,info: freezed == info ? _self.info : info // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,authoritySourceUrl: freezed == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String?,entries: null == entries ? _self.entries : entries // ignore: cast_nullable_to_non_nullable
as List<HubPublicMapEntry>,
  ));
}

}


/// Adds pattern-matching-related methods to [PublicMapDiscoveryResponse].
extension PublicMapDiscoveryResponsePatterns on PublicMapDiscoveryResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( DiscoverPublicMapResponse value)?  discoverPublicMap,required TResult orElse(),}){
final _that = this;
switch (_that) {
case DiscoverPublicMapResponse() when discoverPublicMap != null:
return discoverPublicMap(_that);case _:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( DiscoverPublicMapResponse value)  discoverPublicMap,}){
final _that = this;
switch (_that) {
case DiscoverPublicMapResponse():
return discoverPublicMap(_that);case _:
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( DiscoverPublicMapResponse value)?  discoverPublicMap,}){
final _that = this;
switch (_that) {
case DiscoverPublicMapResponse() when discoverPublicMap != null:
return discoverPublicMap(_that);case _:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  List<HubPublicMapEntry> entries)?  discoverPublicMap,required TResult orElse(),}) {final _that = this;
switch (_that) {
case DiscoverPublicMapResponse() when discoverPublicMap != null:
return discoverPublicMap(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.entries);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  List<HubPublicMapEntry> entries)  discoverPublicMap,}) {final _that = this;
switch (_that) {
case DiscoverPublicMapResponse():
return discoverPublicMap(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.entries);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  bool success,  String? info,  String? error,  String? authoritySourceUrl,  List<HubPublicMapEntry> entries)?  discoverPublicMap,}) {final _that = this;
switch (_that) {
case DiscoverPublicMapResponse() when discoverPublicMap != null:
return discoverPublicMap(_that.requestId,_that.success,_that.info,_that.error,_that.authoritySourceUrl,_that.entries);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DiscoverPublicMapResponse implements PublicMapDiscoveryResponse {
   DiscoverPublicMapResponse({@UuidValueConverter() this.requestId, required this.success, this.info, this.error, this.authoritySourceUrl, final  List<HubPublicMapEntry> entries = const []}): _entries = entries;
  factory DiscoverPublicMapResponse.fromJson(Map<String, dynamic> json) => _$DiscoverPublicMapResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  bool success;
@override final  String? info;
@override final  String? error;
@override final  String? authoritySourceUrl;
 final  List<HubPublicMapEntry> _entries;
@override@JsonKey() List<HubPublicMapEntry> get entries {
  if (_entries is EqualUnmodifiableListView) return _entries;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_entries);
}


/// Create a copy of PublicMapDiscoveryResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DiscoverPublicMapResponseCopyWith<DiscoverPublicMapResponse> get copyWith => _$DiscoverPublicMapResponseCopyWithImpl<DiscoverPublicMapResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DiscoverPublicMapResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DiscoverPublicMapResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.success, success) || other.success == success)&&(identical(other.info, info) || other.info == info)&&(identical(other.error, error) || other.error == error)&&(identical(other.authoritySourceUrl, authoritySourceUrl) || other.authoritySourceUrl == authoritySourceUrl)&&const DeepCollectionEquality().equals(other._entries, _entries));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,success,info,error,authoritySourceUrl,const DeepCollectionEquality().hash(_entries));

@override
String toString() {
  return 'PublicMapDiscoveryResponse.discoverPublicMap(requestId: $requestId, success: $success, info: $info, error: $error, authoritySourceUrl: $authoritySourceUrl, entries: $entries)';
}


}

/// @nodoc
abstract mixin class $DiscoverPublicMapResponseCopyWith<$Res> implements $PublicMapDiscoveryResponseCopyWith<$Res> {
  factory $DiscoverPublicMapResponseCopyWith(DiscoverPublicMapResponse value, $Res Function(DiscoverPublicMapResponse) _then) = _$DiscoverPublicMapResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, bool success, String? info, String? error, String? authoritySourceUrl, List<HubPublicMapEntry> entries
});




}
/// @nodoc
class _$DiscoverPublicMapResponseCopyWithImpl<$Res>
    implements $DiscoverPublicMapResponseCopyWith<$Res> {
  _$DiscoverPublicMapResponseCopyWithImpl(this._self, this._then);

  final DiscoverPublicMapResponse _self;
  final $Res Function(DiscoverPublicMapResponse) _then;

/// Create a copy of PublicMapDiscoveryResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? success = null,Object? info = freezed,Object? error = freezed,Object? authoritySourceUrl = freezed,Object? entries = null,}) {
  return _then(DiscoverPublicMapResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,info: freezed == info ? _self.info : info // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,authoritySourceUrl: freezed == authoritySourceUrl ? _self.authoritySourceUrl : authoritySourceUrl // ignore: cast_nullable_to_non_nullable
as String?,entries: null == entries ? _self._entries : entries // ignore: cast_nullable_to_non_nullable
as List<HubPublicMapEntry>,
  ));
}


}


/// @nodoc
mixin _$HubPublicMapEntry {

 String get artifactFamily; String get artifactKey; String get channel; String? get revisionId; String? get packageName; String? get language; String? get surface; String? get manifestKind; String? get digest; String? get artifactUrl; String? get artifactSha256; int? get artifactSizeBytes; String? get mediaType; String? get title; String? get summary; String? get experienceName; String? get fqnPrefix; String? get producerKind; String? get producerRevisionId; String? get sourceRevisionId; String get visibility; Map<String, dynamic> get metadata;
/// Create a copy of HubPublicMapEntry
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$HubPublicMapEntryCopyWith<HubPublicMapEntry> get copyWith => _$HubPublicMapEntryCopyWithImpl<HubPublicMapEntry>(this as HubPublicMapEntry, _$identity);

  /// Serializes this HubPublicMapEntry to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is HubPublicMapEntry&&(identical(other.artifactFamily, artifactFamily) || other.artifactFamily == artifactFamily)&&(identical(other.artifactKey, artifactKey) || other.artifactKey == artifactKey)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.language, language) || other.language == language)&&(identical(other.surface, surface) || other.surface == surface)&&(identical(other.manifestKind, manifestKind) || other.manifestKind == manifestKind)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.artifactUrl, artifactUrl) || other.artifactUrl == artifactUrl)&&(identical(other.artifactSha256, artifactSha256) || other.artifactSha256 == artifactSha256)&&(identical(other.artifactSizeBytes, artifactSizeBytes) || other.artifactSizeBytes == artifactSizeBytes)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.title, title) || other.title == title)&&(identical(other.summary, summary) || other.summary == summary)&&(identical(other.experienceName, experienceName) || other.experienceName == experienceName)&&(identical(other.fqnPrefix, fqnPrefix) || other.fqnPrefix == fqnPrefix)&&(identical(other.producerKind, producerKind) || other.producerKind == producerKind)&&(identical(other.producerRevisionId, producerRevisionId) || other.producerRevisionId == producerRevisionId)&&(identical(other.sourceRevisionId, sourceRevisionId) || other.sourceRevisionId == sourceRevisionId)&&(identical(other.visibility, visibility) || other.visibility == visibility)&&const DeepCollectionEquality().equals(other.metadata, metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,artifactFamily,artifactKey,channel,revisionId,packageName,language,surface,manifestKind,digest,artifactUrl,artifactSha256,artifactSizeBytes,mediaType,title,summary,experienceName,fqnPrefix,producerKind,producerRevisionId,sourceRevisionId,visibility,const DeepCollectionEquality().hash(metadata)]);

@override
String toString() {
  return 'HubPublicMapEntry(artifactFamily: $artifactFamily, artifactKey: $artifactKey, channel: $channel, revisionId: $revisionId, packageName: $packageName, language: $language, surface: $surface, manifestKind: $manifestKind, digest: $digest, artifactUrl: $artifactUrl, artifactSha256: $artifactSha256, artifactSizeBytes: $artifactSizeBytes, mediaType: $mediaType, title: $title, summary: $summary, experienceName: $experienceName, fqnPrefix: $fqnPrefix, producerKind: $producerKind, producerRevisionId: $producerRevisionId, sourceRevisionId: $sourceRevisionId, visibility: $visibility, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class $HubPublicMapEntryCopyWith<$Res>  {
  factory $HubPublicMapEntryCopyWith(HubPublicMapEntry value, $Res Function(HubPublicMapEntry) _then) = _$HubPublicMapEntryCopyWithImpl;
@useResult
$Res call({
 String artifactFamily, String artifactKey, String channel, String? revisionId, String? packageName, String? language, String? surface, String? manifestKind, String? digest, String? artifactUrl, String? artifactSha256, int? artifactSizeBytes, String? mediaType, String? title, String? summary, String? experienceName, String? fqnPrefix, String? producerKind, String? producerRevisionId, String? sourceRevisionId, String visibility, Map<String, dynamic> metadata
});




}
/// @nodoc
class _$HubPublicMapEntryCopyWithImpl<$Res>
    implements $HubPublicMapEntryCopyWith<$Res> {
  _$HubPublicMapEntryCopyWithImpl(this._self, this._then);

  final HubPublicMapEntry _self;
  final $Res Function(HubPublicMapEntry) _then;

/// Create a copy of HubPublicMapEntry
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? artifactFamily = null,Object? artifactKey = null,Object? channel = null,Object? revisionId = freezed,Object? packageName = freezed,Object? language = freezed,Object? surface = freezed,Object? manifestKind = freezed,Object? digest = freezed,Object? artifactUrl = freezed,Object? artifactSha256 = freezed,Object? artifactSizeBytes = freezed,Object? mediaType = freezed,Object? title = freezed,Object? summary = freezed,Object? experienceName = freezed,Object? fqnPrefix = freezed,Object? producerKind = freezed,Object? producerRevisionId = freezed,Object? sourceRevisionId = freezed,Object? visibility = null,Object? metadata = null,}) {
  return _then(_self.copyWith(
artifactFamily: null == artifactFamily ? _self.artifactFamily : artifactFamily // ignore: cast_nullable_to_non_nullable
as String,artifactKey: null == artifactKey ? _self.artifactKey : artifactKey // ignore: cast_nullable_to_non_nullable
as String,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,revisionId: freezed == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String?,packageName: freezed == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String?,language: freezed == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as String?,surface: freezed == surface ? _self.surface : surface // ignore: cast_nullable_to_non_nullable
as String?,manifestKind: freezed == manifestKind ? _self.manifestKind : manifestKind // ignore: cast_nullable_to_non_nullable
as String?,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,artifactUrl: freezed == artifactUrl ? _self.artifactUrl : artifactUrl // ignore: cast_nullable_to_non_nullable
as String?,artifactSha256: freezed == artifactSha256 ? _self.artifactSha256 : artifactSha256 // ignore: cast_nullable_to_non_nullable
as String?,artifactSizeBytes: freezed == artifactSizeBytes ? _self.artifactSizeBytes : artifactSizeBytes // ignore: cast_nullable_to_non_nullable
as int?,mediaType: freezed == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String?,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,experienceName: freezed == experienceName ? _self.experienceName : experienceName // ignore: cast_nullable_to_non_nullable
as String?,fqnPrefix: freezed == fqnPrefix ? _self.fqnPrefix : fqnPrefix // ignore: cast_nullable_to_non_nullable
as String?,producerKind: freezed == producerKind ? _self.producerKind : producerKind // ignore: cast_nullable_to_non_nullable
as String?,producerRevisionId: freezed == producerRevisionId ? _self.producerRevisionId : producerRevisionId // ignore: cast_nullable_to_non_nullable
as String?,sourceRevisionId: freezed == sourceRevisionId ? _self.sourceRevisionId : sourceRevisionId // ignore: cast_nullable_to_non_nullable
as String?,visibility: null == visibility ? _self.visibility : visibility // ignore: cast_nullable_to_non_nullable
as String,metadata: null == metadata ? _self.metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [HubPublicMapEntry].
extension HubPublicMapEntryPatterns on HubPublicMapEntry {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _HubPublicMapEntry value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _HubPublicMapEntry() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _HubPublicMapEntry value)  def,}){
final _that = this;
switch (_that) {
case _HubPublicMapEntry():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _HubPublicMapEntry value)?  def,}){
final _that = this;
switch (_that) {
case _HubPublicMapEntry() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String artifactFamily,  String artifactKey,  String channel,  String? revisionId,  String? packageName,  String? language,  String? surface,  String? manifestKind,  String? digest,  String? artifactUrl,  String? artifactSha256,  int? artifactSizeBytes,  String? mediaType,  String? title,  String? summary,  String? experienceName,  String? fqnPrefix,  String? producerKind,  String? producerRevisionId,  String? sourceRevisionId,  String visibility,  Map<String, dynamic> metadata)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _HubPublicMapEntry() when def != null:
return def(_that.artifactFamily,_that.artifactKey,_that.channel,_that.revisionId,_that.packageName,_that.language,_that.surface,_that.manifestKind,_that.digest,_that.artifactUrl,_that.artifactSha256,_that.artifactSizeBytes,_that.mediaType,_that.title,_that.summary,_that.experienceName,_that.fqnPrefix,_that.producerKind,_that.producerRevisionId,_that.sourceRevisionId,_that.visibility,_that.metadata);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String artifactFamily,  String artifactKey,  String channel,  String? revisionId,  String? packageName,  String? language,  String? surface,  String? manifestKind,  String? digest,  String? artifactUrl,  String? artifactSha256,  int? artifactSizeBytes,  String? mediaType,  String? title,  String? summary,  String? experienceName,  String? fqnPrefix,  String? producerKind,  String? producerRevisionId,  String? sourceRevisionId,  String visibility,  Map<String, dynamic> metadata)  def,}) {final _that = this;
switch (_that) {
case _HubPublicMapEntry():
return def(_that.artifactFamily,_that.artifactKey,_that.channel,_that.revisionId,_that.packageName,_that.language,_that.surface,_that.manifestKind,_that.digest,_that.artifactUrl,_that.artifactSha256,_that.artifactSizeBytes,_that.mediaType,_that.title,_that.summary,_that.experienceName,_that.fqnPrefix,_that.producerKind,_that.producerRevisionId,_that.sourceRevisionId,_that.visibility,_that.metadata);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String artifactFamily,  String artifactKey,  String channel,  String? revisionId,  String? packageName,  String? language,  String? surface,  String? manifestKind,  String? digest,  String? artifactUrl,  String? artifactSha256,  int? artifactSizeBytes,  String? mediaType,  String? title,  String? summary,  String? experienceName,  String? fqnPrefix,  String? producerKind,  String? producerRevisionId,  String? sourceRevisionId,  String visibility,  Map<String, dynamic> metadata)?  def,}) {final _that = this;
switch (_that) {
case _HubPublicMapEntry() when def != null:
return def(_that.artifactFamily,_that.artifactKey,_that.channel,_that.revisionId,_that.packageName,_that.language,_that.surface,_that.manifestKind,_that.digest,_that.artifactUrl,_that.artifactSha256,_that.artifactSizeBytes,_that.mediaType,_that.title,_that.summary,_that.experienceName,_that.fqnPrefix,_that.producerKind,_that.producerRevisionId,_that.sourceRevisionId,_that.visibility,_that.metadata);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _HubPublicMapEntry implements HubPublicMapEntry {
   _HubPublicMapEntry({required this.artifactFamily, required this.artifactKey, required this.channel, this.revisionId, this.packageName, this.language, this.surface, this.manifestKind, this.digest, this.artifactUrl, this.artifactSha256, this.artifactSizeBytes, this.mediaType, this.title, this.summary, this.experienceName, this.fqnPrefix, this.producerKind, this.producerRevisionId, this.sourceRevisionId, required this.visibility, required final  Map<String, dynamic> metadata}): _metadata = metadata;
  factory _HubPublicMapEntry.fromJson(Map<String, dynamic> json) => _$HubPublicMapEntryFromJson(json);

@override final  String artifactFamily;
@override final  String artifactKey;
@override final  String channel;
@override final  String? revisionId;
@override final  String? packageName;
@override final  String? language;
@override final  String? surface;
@override final  String? manifestKind;
@override final  String? digest;
@override final  String? artifactUrl;
@override final  String? artifactSha256;
@override final  int? artifactSizeBytes;
@override final  String? mediaType;
@override final  String? title;
@override final  String? summary;
@override final  String? experienceName;
@override final  String? fqnPrefix;
@override final  String? producerKind;
@override final  String? producerRevisionId;
@override final  String? sourceRevisionId;
@override final  String visibility;
 final  Map<String, dynamic> _metadata;
@override Map<String, dynamic> get metadata {
  if (_metadata is EqualUnmodifiableMapView) return _metadata;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_metadata);
}


/// Create a copy of HubPublicMapEntry
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$HubPublicMapEntryCopyWith<_HubPublicMapEntry> get copyWith => __$HubPublicMapEntryCopyWithImpl<_HubPublicMapEntry>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$HubPublicMapEntryToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _HubPublicMapEntry&&(identical(other.artifactFamily, artifactFamily) || other.artifactFamily == artifactFamily)&&(identical(other.artifactKey, artifactKey) || other.artifactKey == artifactKey)&&(identical(other.channel, channel) || other.channel == channel)&&(identical(other.revisionId, revisionId) || other.revisionId == revisionId)&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.language, language) || other.language == language)&&(identical(other.surface, surface) || other.surface == surface)&&(identical(other.manifestKind, manifestKind) || other.manifestKind == manifestKind)&&(identical(other.digest, digest) || other.digest == digest)&&(identical(other.artifactUrl, artifactUrl) || other.artifactUrl == artifactUrl)&&(identical(other.artifactSha256, artifactSha256) || other.artifactSha256 == artifactSha256)&&(identical(other.artifactSizeBytes, artifactSizeBytes) || other.artifactSizeBytes == artifactSizeBytes)&&(identical(other.mediaType, mediaType) || other.mediaType == mediaType)&&(identical(other.title, title) || other.title == title)&&(identical(other.summary, summary) || other.summary == summary)&&(identical(other.experienceName, experienceName) || other.experienceName == experienceName)&&(identical(other.fqnPrefix, fqnPrefix) || other.fqnPrefix == fqnPrefix)&&(identical(other.producerKind, producerKind) || other.producerKind == producerKind)&&(identical(other.producerRevisionId, producerRevisionId) || other.producerRevisionId == producerRevisionId)&&(identical(other.sourceRevisionId, sourceRevisionId) || other.sourceRevisionId == sourceRevisionId)&&(identical(other.visibility, visibility) || other.visibility == visibility)&&const DeepCollectionEquality().equals(other._metadata, _metadata));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,artifactFamily,artifactKey,channel,revisionId,packageName,language,surface,manifestKind,digest,artifactUrl,artifactSha256,artifactSizeBytes,mediaType,title,summary,experienceName,fqnPrefix,producerKind,producerRevisionId,sourceRevisionId,visibility,const DeepCollectionEquality().hash(_metadata)]);

@override
String toString() {
  return 'HubPublicMapEntry.def(artifactFamily: $artifactFamily, artifactKey: $artifactKey, channel: $channel, revisionId: $revisionId, packageName: $packageName, language: $language, surface: $surface, manifestKind: $manifestKind, digest: $digest, artifactUrl: $artifactUrl, artifactSha256: $artifactSha256, artifactSizeBytes: $artifactSizeBytes, mediaType: $mediaType, title: $title, summary: $summary, experienceName: $experienceName, fqnPrefix: $fqnPrefix, producerKind: $producerKind, producerRevisionId: $producerRevisionId, sourceRevisionId: $sourceRevisionId, visibility: $visibility, metadata: $metadata)';
}


}

/// @nodoc
abstract mixin class _$HubPublicMapEntryCopyWith<$Res> implements $HubPublicMapEntryCopyWith<$Res> {
  factory _$HubPublicMapEntryCopyWith(_HubPublicMapEntry value, $Res Function(_HubPublicMapEntry) _then) = __$HubPublicMapEntryCopyWithImpl;
@override @useResult
$Res call({
 String artifactFamily, String artifactKey, String channel, String? revisionId, String? packageName, String? language, String? surface, String? manifestKind, String? digest, String? artifactUrl, String? artifactSha256, int? artifactSizeBytes, String? mediaType, String? title, String? summary, String? experienceName, String? fqnPrefix, String? producerKind, String? producerRevisionId, String? sourceRevisionId, String visibility, Map<String, dynamic> metadata
});




}
/// @nodoc
class __$HubPublicMapEntryCopyWithImpl<$Res>
    implements _$HubPublicMapEntryCopyWith<$Res> {
  __$HubPublicMapEntryCopyWithImpl(this._self, this._then);

  final _HubPublicMapEntry _self;
  final $Res Function(_HubPublicMapEntry) _then;

/// Create a copy of HubPublicMapEntry
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? artifactFamily = null,Object? artifactKey = null,Object? channel = null,Object? revisionId = freezed,Object? packageName = freezed,Object? language = freezed,Object? surface = freezed,Object? manifestKind = freezed,Object? digest = freezed,Object? artifactUrl = freezed,Object? artifactSha256 = freezed,Object? artifactSizeBytes = freezed,Object? mediaType = freezed,Object? title = freezed,Object? summary = freezed,Object? experienceName = freezed,Object? fqnPrefix = freezed,Object? producerKind = freezed,Object? producerRevisionId = freezed,Object? sourceRevisionId = freezed,Object? visibility = null,Object? metadata = null,}) {
  return _then(_HubPublicMapEntry(
artifactFamily: null == artifactFamily ? _self.artifactFamily : artifactFamily // ignore: cast_nullable_to_non_nullable
as String,artifactKey: null == artifactKey ? _self.artifactKey : artifactKey // ignore: cast_nullable_to_non_nullable
as String,channel: null == channel ? _self.channel : channel // ignore: cast_nullable_to_non_nullable
as String,revisionId: freezed == revisionId ? _self.revisionId : revisionId // ignore: cast_nullable_to_non_nullable
as String?,packageName: freezed == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String?,language: freezed == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as String?,surface: freezed == surface ? _self.surface : surface // ignore: cast_nullable_to_non_nullable
as String?,manifestKind: freezed == manifestKind ? _self.manifestKind : manifestKind // ignore: cast_nullable_to_non_nullable
as String?,digest: freezed == digest ? _self.digest : digest // ignore: cast_nullable_to_non_nullable
as String?,artifactUrl: freezed == artifactUrl ? _self.artifactUrl : artifactUrl // ignore: cast_nullable_to_non_nullable
as String?,artifactSha256: freezed == artifactSha256 ? _self.artifactSha256 : artifactSha256 // ignore: cast_nullable_to_non_nullable
as String?,artifactSizeBytes: freezed == artifactSizeBytes ? _self.artifactSizeBytes : artifactSizeBytes // ignore: cast_nullable_to_non_nullable
as int?,mediaType: freezed == mediaType ? _self.mediaType : mediaType // ignore: cast_nullable_to_non_nullable
as String?,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,experienceName: freezed == experienceName ? _self.experienceName : experienceName // ignore: cast_nullable_to_non_nullable
as String?,fqnPrefix: freezed == fqnPrefix ? _self.fqnPrefix : fqnPrefix // ignore: cast_nullable_to_non_nullable
as String?,producerKind: freezed == producerKind ? _self.producerKind : producerKind // ignore: cast_nullable_to_non_nullable
as String?,producerRevisionId: freezed == producerRevisionId ? _self.producerRevisionId : producerRevisionId // ignore: cast_nullable_to_non_nullable
as String?,sourceRevisionId: freezed == sourceRevisionId ? _self.sourceRevisionId : sourceRevisionId // ignore: cast_nullable_to_non_nullable
as String?,visibility: null == visibility ? _self.visibility : visibility // ignore: cast_nullable_to_non_nullable
as String,metadata: null == metadata ? _self._metadata : metadata // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}

// dart format on
