// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'sdk_package_api_package_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$SdkPackageApiPackage {

@UuidValueConverter() UuidValue get id; ApiPackage? get apiPackage; String? get description;@UuidValueConverter() UuidValue get sdkPackageId;@UuidValueConverter() UuidValue? get apiPackageId;
/// Create a copy of SdkPackageApiPackage
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$SdkPackageApiPackageCopyWith<SdkPackageApiPackage> get copyWith => _$SdkPackageApiPackageCopyWithImpl<SdkPackageApiPackage>(this as SdkPackageApiPackage, _$identity);

  /// Serializes this SdkPackageApiPackage to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is SdkPackageApiPackage&&(identical(other.id, id) || other.id == id)&&(identical(other.apiPackage, apiPackage) || other.apiPackage == apiPackage)&&(identical(other.description, description) || other.description == description)&&(identical(other.sdkPackageId, sdkPackageId) || other.sdkPackageId == sdkPackageId)&&(identical(other.apiPackageId, apiPackageId) || other.apiPackageId == apiPackageId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,apiPackage,description,sdkPackageId,apiPackageId);

@override
String toString() {
  return 'SdkPackageApiPackage(id: $id, apiPackage: $apiPackage, description: $description, sdkPackageId: $sdkPackageId, apiPackageId: $apiPackageId)';
}


}

/// @nodoc
abstract mixin class $SdkPackageApiPackageCopyWith<$Res>  {
  factory $SdkPackageApiPackageCopyWith(SdkPackageApiPackage value, $Res Function(SdkPackageApiPackage) _then) = _$SdkPackageApiPackageCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue id, ApiPackage? apiPackage, String? description,@UuidValueConverter() UuidValue sdkPackageId,@UuidValueConverter() UuidValue? apiPackageId
});


$ApiPackageCopyWith<$Res>? get apiPackage;

}
/// @nodoc
class _$SdkPackageApiPackageCopyWithImpl<$Res>
    implements $SdkPackageApiPackageCopyWith<$Res> {
  _$SdkPackageApiPackageCopyWithImpl(this._self, this._then);

  final SdkPackageApiPackage _self;
  final $Res Function(SdkPackageApiPackage) _then;

/// Create a copy of SdkPackageApiPackage
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? id = null,Object? apiPackage = freezed,Object? description = freezed,Object? sdkPackageId = null,Object? apiPackageId = freezed,}) {
  return _then(_self.copyWith(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,apiPackage: freezed == apiPackage ? _self.apiPackage : apiPackage // ignore: cast_nullable_to_non_nullable
as ApiPackage?,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,sdkPackageId: null == sdkPackageId ? _self.sdkPackageId : sdkPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,apiPackageId: freezed == apiPackageId ? _self.apiPackageId : apiPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}
/// Create a copy of SdkPackageApiPackage
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ApiPackageCopyWith<$Res>? get apiPackage {
    if (_self.apiPackage == null) {
    return null;
  }

  return $ApiPackageCopyWith<$Res>(_self.apiPackage!, (value) {
    return _then(_self.copyWith(apiPackage: value));
  });
}
}


/// Adds pattern-matching-related methods to [SdkPackageApiPackage].
extension SdkPackageApiPackagePatterns on SdkPackageApiPackage {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _SdkPackageApiPackage value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _SdkPackageApiPackage() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _SdkPackageApiPackage value)  def,}){
final _that = this;
switch (_that) {
case _SdkPackageApiPackage():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _SdkPackageApiPackage value)?  def,}){
final _that = this;
switch (_that) {
case _SdkPackageApiPackage() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue id,  ApiPackage? apiPackage,  String? description, @UuidValueConverter()  UuidValue sdkPackageId, @UuidValueConverter()  UuidValue? apiPackageId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _SdkPackageApiPackage() when def != null:
return def(_that.id,_that.apiPackage,_that.description,_that.sdkPackageId,_that.apiPackageId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue id,  ApiPackage? apiPackage,  String? description, @UuidValueConverter()  UuidValue sdkPackageId, @UuidValueConverter()  UuidValue? apiPackageId)  def,}) {final _that = this;
switch (_that) {
case _SdkPackageApiPackage():
return def(_that.id,_that.apiPackage,_that.description,_that.sdkPackageId,_that.apiPackageId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue id,  ApiPackage? apiPackage,  String? description, @UuidValueConverter()  UuidValue sdkPackageId, @UuidValueConverter()  UuidValue? apiPackageId)?  def,}) {final _that = this;
switch (_that) {
case _SdkPackageApiPackage() when def != null:
return def(_that.id,_that.apiPackage,_that.description,_that.sdkPackageId,_that.apiPackageId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _SdkPackageApiPackage implements SdkPackageApiPackage {
   _SdkPackageApiPackage({@UuidValueConverter() required this.id, this.apiPackage, this.description, @UuidValueConverter() required this.sdkPackageId, @UuidValueConverter() this.apiPackageId});
  factory _SdkPackageApiPackage.fromJson(Map<String, dynamic> json) => _$SdkPackageApiPackageFromJson(json);

@override@UuidValueConverter() final  UuidValue id;
@override final  ApiPackage? apiPackage;
@override final  String? description;
@override@UuidValueConverter() final  UuidValue sdkPackageId;
@override@UuidValueConverter() final  UuidValue? apiPackageId;

/// Create a copy of SdkPackageApiPackage
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$SdkPackageApiPackageCopyWith<_SdkPackageApiPackage> get copyWith => __$SdkPackageApiPackageCopyWithImpl<_SdkPackageApiPackage>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$SdkPackageApiPackageToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _SdkPackageApiPackage&&(identical(other.id, id) || other.id == id)&&(identical(other.apiPackage, apiPackage) || other.apiPackage == apiPackage)&&(identical(other.description, description) || other.description == description)&&(identical(other.sdkPackageId, sdkPackageId) || other.sdkPackageId == sdkPackageId)&&(identical(other.apiPackageId, apiPackageId) || other.apiPackageId == apiPackageId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,apiPackage,description,sdkPackageId,apiPackageId);

@override
String toString() {
  return 'SdkPackageApiPackage.def(id: $id, apiPackage: $apiPackage, description: $description, sdkPackageId: $sdkPackageId, apiPackageId: $apiPackageId)';
}


}

/// @nodoc
abstract mixin class _$SdkPackageApiPackageCopyWith<$Res> implements $SdkPackageApiPackageCopyWith<$Res> {
  factory _$SdkPackageApiPackageCopyWith(_SdkPackageApiPackage value, $Res Function(_SdkPackageApiPackage) _then) = __$SdkPackageApiPackageCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue id, ApiPackage? apiPackage, String? description,@UuidValueConverter() UuidValue sdkPackageId,@UuidValueConverter() UuidValue? apiPackageId
});


@override $ApiPackageCopyWith<$Res>? get apiPackage;

}
/// @nodoc
class __$SdkPackageApiPackageCopyWithImpl<$Res>
    implements _$SdkPackageApiPackageCopyWith<$Res> {
  __$SdkPackageApiPackageCopyWithImpl(this._self, this._then);

  final _SdkPackageApiPackage _self;
  final $Res Function(_SdkPackageApiPackage) _then;

/// Create a copy of SdkPackageApiPackage
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? id = null,Object? apiPackage = freezed,Object? description = freezed,Object? sdkPackageId = null,Object? apiPackageId = freezed,}) {
  return _then(_SdkPackageApiPackage(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,apiPackage: freezed == apiPackage ? _self.apiPackage : apiPackage // ignore: cast_nullable_to_non_nullable
as ApiPackage?,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,sdkPackageId: null == sdkPackageId ? _self.sdkPackageId : sdkPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,apiPackageId: freezed == apiPackageId ? _self.apiPackageId : apiPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

/// Create a copy of SdkPackageApiPackage
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ApiPackageCopyWith<$Res>? get apiPackage {
    if (_self.apiPackage == null) {
    return null;
  }

  return $ApiPackageCopyWith<$Res>(_self.apiPackage!, (value) {
    return _then(_self.copyWith(apiPackage: value));
  });
}
}

// dart format on
