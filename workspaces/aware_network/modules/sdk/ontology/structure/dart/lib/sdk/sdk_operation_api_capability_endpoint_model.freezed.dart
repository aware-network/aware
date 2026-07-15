// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'sdk_operation_api_capability_endpoint_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$SdkOperationApiCapabilityEndpoint {

@UuidValueConverter() UuidValue get id; ApiCapabilityEndpoint? get apiCapabilityEndpoint; String get name; String? get endpointRef; String? get discriminant; String get role; int get order;@JsonKey(name: 'required') bool get required_;@UuidValueConverter() UuidValue get sdkOperationId;@UuidValueConverter() UuidValue? get apiCapabilityEndpointId;
/// Create a copy of SdkOperationApiCapabilityEndpoint
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$SdkOperationApiCapabilityEndpointCopyWith<SdkOperationApiCapabilityEndpoint> get copyWith => _$SdkOperationApiCapabilityEndpointCopyWithImpl<SdkOperationApiCapabilityEndpoint>(this as SdkOperationApiCapabilityEndpoint, _$identity);

  /// Serializes this SdkOperationApiCapabilityEndpoint to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is SdkOperationApiCapabilityEndpoint&&(identical(other.id, id) || other.id == id)&&(identical(other.apiCapabilityEndpoint, apiCapabilityEndpoint) || other.apiCapabilityEndpoint == apiCapabilityEndpoint)&&(identical(other.name, name) || other.name == name)&&(identical(other.endpointRef, endpointRef) || other.endpointRef == endpointRef)&&(identical(other.discriminant, discriminant) || other.discriminant == discriminant)&&(identical(other.role, role) || other.role == role)&&(identical(other.order, order) || other.order == order)&&(identical(other.required_, required_) || other.required_ == required_)&&(identical(other.sdkOperationId, sdkOperationId) || other.sdkOperationId == sdkOperationId)&&(identical(other.apiCapabilityEndpointId, apiCapabilityEndpointId) || other.apiCapabilityEndpointId == apiCapabilityEndpointId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,apiCapabilityEndpoint,name,endpointRef,discriminant,role,order,required_,sdkOperationId,apiCapabilityEndpointId);

@override
String toString() {
  return 'SdkOperationApiCapabilityEndpoint(id: $id, apiCapabilityEndpoint: $apiCapabilityEndpoint, name: $name, endpointRef: $endpointRef, discriminant: $discriminant, role: $role, order: $order, required_: $required_, sdkOperationId: $sdkOperationId, apiCapabilityEndpointId: $apiCapabilityEndpointId)';
}


}

/// @nodoc
abstract mixin class $SdkOperationApiCapabilityEndpointCopyWith<$Res>  {
  factory $SdkOperationApiCapabilityEndpointCopyWith(SdkOperationApiCapabilityEndpoint value, $Res Function(SdkOperationApiCapabilityEndpoint) _then) = _$SdkOperationApiCapabilityEndpointCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue id, ApiCapabilityEndpoint? apiCapabilityEndpoint, String name, String? endpointRef, String? discriminant, String role, int order,@JsonKey(name: 'required') bool required_,@UuidValueConverter() UuidValue sdkOperationId,@UuidValueConverter() UuidValue? apiCapabilityEndpointId
});


$ApiCapabilityEndpointCopyWith<$Res>? get apiCapabilityEndpoint;

}
/// @nodoc
class _$SdkOperationApiCapabilityEndpointCopyWithImpl<$Res>
    implements $SdkOperationApiCapabilityEndpointCopyWith<$Res> {
  _$SdkOperationApiCapabilityEndpointCopyWithImpl(this._self, this._then);

  final SdkOperationApiCapabilityEndpoint _self;
  final $Res Function(SdkOperationApiCapabilityEndpoint) _then;

/// Create a copy of SdkOperationApiCapabilityEndpoint
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? id = null,Object? apiCapabilityEndpoint = freezed,Object? name = null,Object? endpointRef = freezed,Object? discriminant = freezed,Object? role = null,Object? order = null,Object? required_ = null,Object? sdkOperationId = null,Object? apiCapabilityEndpointId = freezed,}) {
  return _then(_self.copyWith(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,apiCapabilityEndpoint: freezed == apiCapabilityEndpoint ? _self.apiCapabilityEndpoint : apiCapabilityEndpoint // ignore: cast_nullable_to_non_nullable
as ApiCapabilityEndpoint?,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,endpointRef: freezed == endpointRef ? _self.endpointRef : endpointRef // ignore: cast_nullable_to_non_nullable
as String?,discriminant: freezed == discriminant ? _self.discriminant : discriminant // ignore: cast_nullable_to_non_nullable
as String?,role: null == role ? _self.role : role // ignore: cast_nullable_to_non_nullable
as String,order: null == order ? _self.order : order // ignore: cast_nullable_to_non_nullable
as int,required_: null == required_ ? _self.required_ : required_ // ignore: cast_nullable_to_non_nullable
as bool,sdkOperationId: null == sdkOperationId ? _self.sdkOperationId : sdkOperationId // ignore: cast_nullable_to_non_nullable
as UuidValue,apiCapabilityEndpointId: freezed == apiCapabilityEndpointId ? _self.apiCapabilityEndpointId : apiCapabilityEndpointId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}
/// Create a copy of SdkOperationApiCapabilityEndpoint
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ApiCapabilityEndpointCopyWith<$Res>? get apiCapabilityEndpoint {
    if (_self.apiCapabilityEndpoint == null) {
    return null;
  }

  return $ApiCapabilityEndpointCopyWith<$Res>(_self.apiCapabilityEndpoint!, (value) {
    return _then(_self.copyWith(apiCapabilityEndpoint: value));
  });
}
}


/// Adds pattern-matching-related methods to [SdkOperationApiCapabilityEndpoint].
extension SdkOperationApiCapabilityEndpointPatterns on SdkOperationApiCapabilityEndpoint {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _SdkOperationApiCapabilityEndpoint value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _SdkOperationApiCapabilityEndpoint() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _SdkOperationApiCapabilityEndpoint value)  def,}){
final _that = this;
switch (_that) {
case _SdkOperationApiCapabilityEndpoint():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _SdkOperationApiCapabilityEndpoint value)?  def,}){
final _that = this;
switch (_that) {
case _SdkOperationApiCapabilityEndpoint() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue id,  ApiCapabilityEndpoint? apiCapabilityEndpoint,  String name,  String? endpointRef,  String? discriminant,  String role,  int order, @JsonKey(name: 'required')  bool required_, @UuidValueConverter()  UuidValue sdkOperationId, @UuidValueConverter()  UuidValue? apiCapabilityEndpointId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _SdkOperationApiCapabilityEndpoint() when def != null:
return def(_that.id,_that.apiCapabilityEndpoint,_that.name,_that.endpointRef,_that.discriminant,_that.role,_that.order,_that.required_,_that.sdkOperationId,_that.apiCapabilityEndpointId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue id,  ApiCapabilityEndpoint? apiCapabilityEndpoint,  String name,  String? endpointRef,  String? discriminant,  String role,  int order, @JsonKey(name: 'required')  bool required_, @UuidValueConverter()  UuidValue sdkOperationId, @UuidValueConverter()  UuidValue? apiCapabilityEndpointId)  def,}) {final _that = this;
switch (_that) {
case _SdkOperationApiCapabilityEndpoint():
return def(_that.id,_that.apiCapabilityEndpoint,_that.name,_that.endpointRef,_that.discriminant,_that.role,_that.order,_that.required_,_that.sdkOperationId,_that.apiCapabilityEndpointId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue id,  ApiCapabilityEndpoint? apiCapabilityEndpoint,  String name,  String? endpointRef,  String? discriminant,  String role,  int order, @JsonKey(name: 'required')  bool required_, @UuidValueConverter()  UuidValue sdkOperationId, @UuidValueConverter()  UuidValue? apiCapabilityEndpointId)?  def,}) {final _that = this;
switch (_that) {
case _SdkOperationApiCapabilityEndpoint() when def != null:
return def(_that.id,_that.apiCapabilityEndpoint,_that.name,_that.endpointRef,_that.discriminant,_that.role,_that.order,_that.required_,_that.sdkOperationId,_that.apiCapabilityEndpointId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _SdkOperationApiCapabilityEndpoint implements SdkOperationApiCapabilityEndpoint {
   _SdkOperationApiCapabilityEndpoint({@UuidValueConverter() required this.id, this.apiCapabilityEndpoint, required this.name, this.endpointRef, this.discriminant, required this.role, required this.order, @JsonKey(name: 'required') required this.required_, @UuidValueConverter() required this.sdkOperationId, @UuidValueConverter() this.apiCapabilityEndpointId});
  factory _SdkOperationApiCapabilityEndpoint.fromJson(Map<String, dynamic> json) => _$SdkOperationApiCapabilityEndpointFromJson(json);

@override@UuidValueConverter() final  UuidValue id;
@override final  ApiCapabilityEndpoint? apiCapabilityEndpoint;
@override final  String name;
@override final  String? endpointRef;
@override final  String? discriminant;
@override final  String role;
@override final  int order;
@override@JsonKey(name: 'required') final  bool required_;
@override@UuidValueConverter() final  UuidValue sdkOperationId;
@override@UuidValueConverter() final  UuidValue? apiCapabilityEndpointId;

/// Create a copy of SdkOperationApiCapabilityEndpoint
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$SdkOperationApiCapabilityEndpointCopyWith<_SdkOperationApiCapabilityEndpoint> get copyWith => __$SdkOperationApiCapabilityEndpointCopyWithImpl<_SdkOperationApiCapabilityEndpoint>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$SdkOperationApiCapabilityEndpointToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _SdkOperationApiCapabilityEndpoint&&(identical(other.id, id) || other.id == id)&&(identical(other.apiCapabilityEndpoint, apiCapabilityEndpoint) || other.apiCapabilityEndpoint == apiCapabilityEndpoint)&&(identical(other.name, name) || other.name == name)&&(identical(other.endpointRef, endpointRef) || other.endpointRef == endpointRef)&&(identical(other.discriminant, discriminant) || other.discriminant == discriminant)&&(identical(other.role, role) || other.role == role)&&(identical(other.order, order) || other.order == order)&&(identical(other.required_, required_) || other.required_ == required_)&&(identical(other.sdkOperationId, sdkOperationId) || other.sdkOperationId == sdkOperationId)&&(identical(other.apiCapabilityEndpointId, apiCapabilityEndpointId) || other.apiCapabilityEndpointId == apiCapabilityEndpointId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,apiCapabilityEndpoint,name,endpointRef,discriminant,role,order,required_,sdkOperationId,apiCapabilityEndpointId);

@override
String toString() {
  return 'SdkOperationApiCapabilityEndpoint.def(id: $id, apiCapabilityEndpoint: $apiCapabilityEndpoint, name: $name, endpointRef: $endpointRef, discriminant: $discriminant, role: $role, order: $order, required_: $required_, sdkOperationId: $sdkOperationId, apiCapabilityEndpointId: $apiCapabilityEndpointId)';
}


}

/// @nodoc
abstract mixin class _$SdkOperationApiCapabilityEndpointCopyWith<$Res> implements $SdkOperationApiCapabilityEndpointCopyWith<$Res> {
  factory _$SdkOperationApiCapabilityEndpointCopyWith(_SdkOperationApiCapabilityEndpoint value, $Res Function(_SdkOperationApiCapabilityEndpoint) _then) = __$SdkOperationApiCapabilityEndpointCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue id, ApiCapabilityEndpoint? apiCapabilityEndpoint, String name, String? endpointRef, String? discriminant, String role, int order,@JsonKey(name: 'required') bool required_,@UuidValueConverter() UuidValue sdkOperationId,@UuidValueConverter() UuidValue? apiCapabilityEndpointId
});


@override $ApiCapabilityEndpointCopyWith<$Res>? get apiCapabilityEndpoint;

}
/// @nodoc
class __$SdkOperationApiCapabilityEndpointCopyWithImpl<$Res>
    implements _$SdkOperationApiCapabilityEndpointCopyWith<$Res> {
  __$SdkOperationApiCapabilityEndpointCopyWithImpl(this._self, this._then);

  final _SdkOperationApiCapabilityEndpoint _self;
  final $Res Function(_SdkOperationApiCapabilityEndpoint) _then;

/// Create a copy of SdkOperationApiCapabilityEndpoint
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? id = null,Object? apiCapabilityEndpoint = freezed,Object? name = null,Object? endpointRef = freezed,Object? discriminant = freezed,Object? role = null,Object? order = null,Object? required_ = null,Object? sdkOperationId = null,Object? apiCapabilityEndpointId = freezed,}) {
  return _then(_SdkOperationApiCapabilityEndpoint(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,apiCapabilityEndpoint: freezed == apiCapabilityEndpoint ? _self.apiCapabilityEndpoint : apiCapabilityEndpoint // ignore: cast_nullable_to_non_nullable
as ApiCapabilityEndpoint?,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,endpointRef: freezed == endpointRef ? _self.endpointRef : endpointRef // ignore: cast_nullable_to_non_nullable
as String?,discriminant: freezed == discriminant ? _self.discriminant : discriminant // ignore: cast_nullable_to_non_nullable
as String?,role: null == role ? _self.role : role // ignore: cast_nullable_to_non_nullable
as String,order: null == order ? _self.order : order // ignore: cast_nullable_to_non_nullable
as int,required_: null == required_ ? _self.required_ : required_ // ignore: cast_nullable_to_non_nullable
as bool,sdkOperationId: null == sdkOperationId ? _self.sdkOperationId : sdkOperationId // ignore: cast_nullable_to_non_nullable
as UuidValue,apiCapabilityEndpointId: freezed == apiCapabilityEndpointId ? _self.apiCapabilityEndpointId : apiCapabilityEndpointId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

/// Create a copy of SdkOperationApiCapabilityEndpoint
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ApiCapabilityEndpointCopyWith<$Res>? get apiCapabilityEndpoint {
    if (_self.apiCapabilityEndpoint == null) {
    return null;
  }

  return $ApiCapabilityEndpointCopyWith<$Res>(_self.apiCapabilityEndpoint!, (value) {
    return _then(_self.copyWith(apiCapabilityEndpoint: value));
  });
}
}

// dart format on
