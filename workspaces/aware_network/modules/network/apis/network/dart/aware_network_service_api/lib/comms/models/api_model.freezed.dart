// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'api_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$ApiOperationContext {

@UuidValueConverter() UuidValue? get actorId;
/// Create a copy of ApiOperationContext
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ApiOperationContextCopyWith<ApiOperationContext> get copyWith => _$ApiOperationContextCopyWithImpl<ApiOperationContext>(this as ApiOperationContext, _$identity);

  /// Serializes this ApiOperationContext to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ApiOperationContext&&(identical(other.actorId, actorId) || other.actorId == actorId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId);

@override
String toString() {
  return 'ApiOperationContext(actorId: $actorId)';
}


}

/// @nodoc
abstract mixin class $ApiOperationContextCopyWith<$Res>  {
  factory $ApiOperationContextCopyWith(ApiOperationContext value, $Res Function(ApiOperationContext) _then) = _$ApiOperationContextCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId
});




}
/// @nodoc
class _$ApiOperationContextCopyWithImpl<$Res>
    implements $ApiOperationContextCopyWith<$Res> {
  _$ApiOperationContextCopyWithImpl(this._self, this._then);

  final ApiOperationContext _self;
  final $Res Function(ApiOperationContext) _then;

/// Create a copy of ApiOperationContext
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

}


/// Adds pattern-matching-related methods to [ApiOperationContext].
extension ApiOperationContextPatterns on ApiOperationContext {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ApiOperationContext value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ApiOperationContext() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ApiOperationContext value)  def,}){
final _that = this;
switch (_that) {
case _ApiOperationContext():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ApiOperationContext value)?  def,}){
final _that = this;
switch (_that) {
case _ApiOperationContext() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ApiOperationContext() when def != null:
return def(_that.actorId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId)  def,}) {final _that = this;
switch (_that) {
case _ApiOperationContext():
return def(_that.actorId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId)?  def,}) {final _that = this;
switch (_that) {
case _ApiOperationContext() when def != null:
return def(_that.actorId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ApiOperationContext implements ApiOperationContext {
   _ApiOperationContext({@UuidValueConverter() this.actorId});
  factory _ApiOperationContext.fromJson(Map<String, dynamic> json) => _$ApiOperationContextFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;

/// Create a copy of ApiOperationContext
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ApiOperationContextCopyWith<_ApiOperationContext> get copyWith => __$ApiOperationContextCopyWithImpl<_ApiOperationContext>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ApiOperationContextToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ApiOperationContext&&(identical(other.actorId, actorId) || other.actorId == actorId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId);

@override
String toString() {
  return 'ApiOperationContext.def(actorId: $actorId)';
}


}

/// @nodoc
abstract mixin class _$ApiOperationContextCopyWith<$Res> implements $ApiOperationContextCopyWith<$Res> {
  factory _$ApiOperationContextCopyWith(_ApiOperationContext value, $Res Function(_ApiOperationContext) _then) = __$ApiOperationContextCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId
});




}
/// @nodoc
class __$ApiOperationContextCopyWithImpl<$Res>
    implements _$ApiOperationContextCopyWith<$Res> {
  __$ApiOperationContextCopyWithImpl(this._self, this._then);

  final _ApiOperationContext _self;
  final $Res Function(_ApiOperationContext) _then;

/// Create a copy of ApiOperationContext
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,}) {
  return _then(_ApiOperationContext(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}


}


/// @nodoc
mixin _$ApiOperation {

 ApiOperationRequest? get request; ApiOperationResponse? get response;
/// Create a copy of ApiOperation
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ApiOperationCopyWith<ApiOperation> get copyWith => _$ApiOperationCopyWithImpl<ApiOperation>(this as ApiOperation, _$identity);

  /// Serializes this ApiOperation to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ApiOperation&&(identical(other.request, request) || other.request == request)&&(identical(other.response, response) || other.response == response));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,request,response);

@override
String toString() {
  return 'ApiOperation(request: $request, response: $response)';
}


}

/// @nodoc
abstract mixin class $ApiOperationCopyWith<$Res>  {
  factory $ApiOperationCopyWith(ApiOperation value, $Res Function(ApiOperation) _then) = _$ApiOperationCopyWithImpl;
@useResult
$Res call({
 ApiOperationRequest? request, ApiOperationResponse? response
});


$ApiOperationRequestCopyWith<$Res>? get request;$ApiOperationResponseCopyWith<$Res>? get response;

}
/// @nodoc
class _$ApiOperationCopyWithImpl<$Res>
    implements $ApiOperationCopyWith<$Res> {
  _$ApiOperationCopyWithImpl(this._self, this._then);

  final ApiOperation _self;
  final $Res Function(ApiOperation) _then;

/// Create a copy of ApiOperation
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? request = freezed,Object? response = freezed,}) {
  return _then(_self.copyWith(
request: freezed == request ? _self.request : request // ignore: cast_nullable_to_non_nullable
as ApiOperationRequest?,response: freezed == response ? _self.response : response // ignore: cast_nullable_to_non_nullable
as ApiOperationResponse?,
  ));
}
/// Create a copy of ApiOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ApiOperationRequestCopyWith<$Res>? get request {
    if (_self.request == null) {
    return null;
  }

  return $ApiOperationRequestCopyWith<$Res>(_self.request!, (value) {
    return _then(_self.copyWith(request: value));
  });
}/// Create a copy of ApiOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ApiOperationResponseCopyWith<$Res>? get response {
    if (_self.response == null) {
    return null;
  }

  return $ApiOperationResponseCopyWith<$Res>(_self.response!, (value) {
    return _then(_self.copyWith(response: value));
  });
}
}


/// Adds pattern-matching-related methods to [ApiOperation].
extension ApiOperationPatterns on ApiOperation {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ApiOperation value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ApiOperation() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ApiOperation value)  def,}){
final _that = this;
switch (_that) {
case _ApiOperation():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ApiOperation value)?  def,}){
final _that = this;
switch (_that) {
case _ApiOperation() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( ApiOperationRequest? request,  ApiOperationResponse? response)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ApiOperation() when def != null:
return def(_that.request,_that.response);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( ApiOperationRequest? request,  ApiOperationResponse? response)  def,}) {final _that = this;
switch (_that) {
case _ApiOperation():
return def(_that.request,_that.response);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( ApiOperationRequest? request,  ApiOperationResponse? response)?  def,}) {final _that = this;
switch (_that) {
case _ApiOperation() when def != null:
return def(_that.request,_that.response);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ApiOperation implements ApiOperation {
   _ApiOperation({this.request, this.response});
  factory _ApiOperation.fromJson(Map<String, dynamic> json) => _$ApiOperationFromJson(json);

@override final  ApiOperationRequest? request;
@override final  ApiOperationResponse? response;

/// Create a copy of ApiOperation
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ApiOperationCopyWith<_ApiOperation> get copyWith => __$ApiOperationCopyWithImpl<_ApiOperation>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ApiOperationToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ApiOperation&&(identical(other.request, request) || other.request == request)&&(identical(other.response, response) || other.response == response));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,request,response);

@override
String toString() {
  return 'ApiOperation.def(request: $request, response: $response)';
}


}

/// @nodoc
abstract mixin class _$ApiOperationCopyWith<$Res> implements $ApiOperationCopyWith<$Res> {
  factory _$ApiOperationCopyWith(_ApiOperation value, $Res Function(_ApiOperation) _then) = __$ApiOperationCopyWithImpl;
@override @useResult
$Res call({
 ApiOperationRequest? request, ApiOperationResponse? response
});


@override $ApiOperationRequestCopyWith<$Res>? get request;@override $ApiOperationResponseCopyWith<$Res>? get response;

}
/// @nodoc
class __$ApiOperationCopyWithImpl<$Res>
    implements _$ApiOperationCopyWith<$Res> {
  __$ApiOperationCopyWithImpl(this._self, this._then);

  final _ApiOperation _self;
  final $Res Function(_ApiOperation) _then;

/// Create a copy of ApiOperation
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? request = freezed,Object? response = freezed,}) {
  return _then(_ApiOperation(
request: freezed == request ? _self.request : request // ignore: cast_nullable_to_non_nullable
as ApiOperationRequest?,response: freezed == response ? _self.response : response // ignore: cast_nullable_to_non_nullable
as ApiOperationResponse?,
  ));
}

/// Create a copy of ApiOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ApiOperationRequestCopyWith<$Res>? get request {
    if (_self.request == null) {
    return null;
  }

  return $ApiOperationRequestCopyWith<$Res>(_self.request!, (value) {
    return _then(_self.copyWith(request: value));
  });
}/// Create a copy of ApiOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ApiOperationResponseCopyWith<$Res>? get response {
    if (_self.response == null) {
    return null;
  }

  return $ApiOperationResponseCopyWith<$Res>(_self.response!, (value) {
    return _then(_self.copyWith(response: value));
  });
}
}


/// @nodoc
mixin _$ApiOperationRequest {

@UuidValueConverter() UuidValue? get actorId; String get operation;
/// Create a copy of ApiOperationRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ApiOperationRequestCopyWith<ApiOperationRequest> get copyWith => _$ApiOperationRequestCopyWithImpl<ApiOperationRequest>(this as ApiOperationRequest, _$identity);

  /// Serializes this ApiOperationRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ApiOperationRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.operation, operation) || other.operation == operation));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,operation);

@override
String toString() {
  return 'ApiOperationRequest(actorId: $actorId, operation: $operation)';
}


}

/// @nodoc
abstract mixin class $ApiOperationRequestCopyWith<$Res>  {
  factory $ApiOperationRequestCopyWith(ApiOperationRequest value, $Res Function(ApiOperationRequest) _then) = _$ApiOperationRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, String operation
});




}
/// @nodoc
class _$ApiOperationRequestCopyWithImpl<$Res>
    implements $ApiOperationRequestCopyWith<$Res> {
  _$ApiOperationRequestCopyWithImpl(this._self, this._then);

  final ApiOperationRequest _self;
  final $Res Function(ApiOperationRequest) _then;

/// Create a copy of ApiOperationRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? operation = null,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,
  ));
}

}


/// Adds pattern-matching-related methods to [ApiOperationRequest].
extension ApiOperationRequestPatterns on ApiOperationRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ApiOperationRequest value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ApiOperationRequest() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ApiOperationRequest value)  def,}){
final _that = this;
switch (_that) {
case _ApiOperationRequest():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ApiOperationRequest value)?  def,}){
final _that = this;
switch (_that) {
case _ApiOperationRequest() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId,  String operation)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ApiOperationRequest() when def != null:
return def(_that.actorId,_that.operation);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId,  String operation)  def,}) {final _that = this;
switch (_that) {
case _ApiOperationRequest():
return def(_that.actorId,_that.operation);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId,  String operation)?  def,}) {final _that = this;
switch (_that) {
case _ApiOperationRequest() when def != null:
return def(_that.actorId,_that.operation);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ApiOperationRequest implements ApiOperationRequest {
   _ApiOperationRequest({@UuidValueConverter() this.actorId, required this.operation});
  factory _ApiOperationRequest.fromJson(Map<String, dynamic> json) => _$ApiOperationRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override final  String operation;

/// Create a copy of ApiOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ApiOperationRequestCopyWith<_ApiOperationRequest> get copyWith => __$ApiOperationRequestCopyWithImpl<_ApiOperationRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ApiOperationRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ApiOperationRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.operation, operation) || other.operation == operation));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,operation);

@override
String toString() {
  return 'ApiOperationRequest.def(actorId: $actorId, operation: $operation)';
}


}

/// @nodoc
abstract mixin class _$ApiOperationRequestCopyWith<$Res> implements $ApiOperationRequestCopyWith<$Res> {
  factory _$ApiOperationRequestCopyWith(_ApiOperationRequest value, $Res Function(_ApiOperationRequest) _then) = __$ApiOperationRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, String operation
});




}
/// @nodoc
class __$ApiOperationRequestCopyWithImpl<$Res>
    implements _$ApiOperationRequestCopyWith<$Res> {
  __$ApiOperationRequestCopyWithImpl(this._self, this._then);

  final _ApiOperationRequest _self;
  final $Res Function(_ApiOperationRequest) _then;

/// Create a copy of ApiOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? operation = null,}) {
  return _then(_ApiOperationRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}


/// @nodoc
mixin _$ApiOperationResponse {

@UuidValueConverter() UuidValue? get actorId; String get operation;
/// Create a copy of ApiOperationResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ApiOperationResponseCopyWith<ApiOperationResponse> get copyWith => _$ApiOperationResponseCopyWithImpl<ApiOperationResponse>(this as ApiOperationResponse, _$identity);

  /// Serializes this ApiOperationResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ApiOperationResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.operation, operation) || other.operation == operation));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,operation);

@override
String toString() {
  return 'ApiOperationResponse(actorId: $actorId, operation: $operation)';
}


}

/// @nodoc
abstract mixin class $ApiOperationResponseCopyWith<$Res>  {
  factory $ApiOperationResponseCopyWith(ApiOperationResponse value, $Res Function(ApiOperationResponse) _then) = _$ApiOperationResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, String operation
});




}
/// @nodoc
class _$ApiOperationResponseCopyWithImpl<$Res>
    implements $ApiOperationResponseCopyWith<$Res> {
  _$ApiOperationResponseCopyWithImpl(this._self, this._then);

  final ApiOperationResponse _self;
  final $Res Function(ApiOperationResponse) _then;

/// Create a copy of ApiOperationResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? operation = null,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,
  ));
}

}


/// Adds pattern-matching-related methods to [ApiOperationResponse].
extension ApiOperationResponsePatterns on ApiOperationResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ApiOperationResponse value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ApiOperationResponse() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ApiOperationResponse value)  def,}){
final _that = this;
switch (_that) {
case _ApiOperationResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ApiOperationResponse value)?  def,}){
final _that = this;
switch (_that) {
case _ApiOperationResponse() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId,  String operation)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ApiOperationResponse() when def != null:
return def(_that.actorId,_that.operation);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId,  String operation)  def,}) {final _that = this;
switch (_that) {
case _ApiOperationResponse():
return def(_that.actorId,_that.operation);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId,  String operation)?  def,}) {final _that = this;
switch (_that) {
case _ApiOperationResponse() when def != null:
return def(_that.actorId,_that.operation);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ApiOperationResponse implements ApiOperationResponse {
   _ApiOperationResponse({@UuidValueConverter() this.actorId, required this.operation});
  factory _ApiOperationResponse.fromJson(Map<String, dynamic> json) => _$ApiOperationResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override final  String operation;

/// Create a copy of ApiOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ApiOperationResponseCopyWith<_ApiOperationResponse> get copyWith => __$ApiOperationResponseCopyWithImpl<_ApiOperationResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ApiOperationResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ApiOperationResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.operation, operation) || other.operation == operation));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,operation);

@override
String toString() {
  return 'ApiOperationResponse.def(actorId: $actorId, operation: $operation)';
}


}

/// @nodoc
abstract mixin class _$ApiOperationResponseCopyWith<$Res> implements $ApiOperationResponseCopyWith<$Res> {
  factory _$ApiOperationResponseCopyWith(_ApiOperationResponse value, $Res Function(_ApiOperationResponse) _then) = __$ApiOperationResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, String operation
});




}
/// @nodoc
class __$ApiOperationResponseCopyWithImpl<$Res>
    implements _$ApiOperationResponseCopyWith<$Res> {
  __$ApiOperationResponseCopyWithImpl(this._self, this._then);

  final _ApiOperationResponse _self;
  final $Res Function(_ApiOperationResponse) _then;

/// Create a copy of ApiOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? operation = null,}) {
  return _then(_ApiOperationResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}

// dart format on
