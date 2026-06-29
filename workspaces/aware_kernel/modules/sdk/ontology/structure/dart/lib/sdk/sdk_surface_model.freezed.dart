// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'sdk_surface_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$SdkSurface {

@UuidValueConverter() UuidValue get id; List<SdkSurfaceMethod> get methods; String get name; String? get title; String? get description;@UuidValueConverter() UuidValue get sdkConfigId;
/// Create a copy of SdkSurface
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$SdkSurfaceCopyWith<SdkSurface> get copyWith => _$SdkSurfaceCopyWithImpl<SdkSurface>(this as SdkSurface, _$identity);

  /// Serializes this SdkSurface to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is SdkSurface&&(identical(other.id, id) || other.id == id)&&const DeepCollectionEquality().equals(other.methods, methods)&&(identical(other.name, name) || other.name == name)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.sdkConfigId, sdkConfigId) || other.sdkConfigId == sdkConfigId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,const DeepCollectionEquality().hash(methods),name,title,description,sdkConfigId);

@override
String toString() {
  return 'SdkSurface(id: $id, methods: $methods, name: $name, title: $title, description: $description, sdkConfigId: $sdkConfigId)';
}


}

/// @nodoc
abstract mixin class $SdkSurfaceCopyWith<$Res>  {
  factory $SdkSurfaceCopyWith(SdkSurface value, $Res Function(SdkSurface) _then) = _$SdkSurfaceCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue id, List<SdkSurfaceMethod> methods, String name, String? title, String? description,@UuidValueConverter() UuidValue sdkConfigId
});




}
/// @nodoc
class _$SdkSurfaceCopyWithImpl<$Res>
    implements $SdkSurfaceCopyWith<$Res> {
  _$SdkSurfaceCopyWithImpl(this._self, this._then);

  final SdkSurface _self;
  final $Res Function(SdkSurface) _then;

/// Create a copy of SdkSurface
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? id = null,Object? methods = null,Object? name = null,Object? title = freezed,Object? description = freezed,Object? sdkConfigId = null,}) {
  return _then(_self.copyWith(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,methods: null == methods ? _self.methods : methods // ignore: cast_nullable_to_non_nullable
as List<SdkSurfaceMethod>,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,sdkConfigId: null == sdkConfigId ? _self.sdkConfigId : sdkConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,
  ));
}

}


/// Adds pattern-matching-related methods to [SdkSurface].
extension SdkSurfacePatterns on SdkSurface {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _SdkSurface value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _SdkSurface() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _SdkSurface value)  def,}){
final _that = this;
switch (_that) {
case _SdkSurface():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _SdkSurface value)?  def,}){
final _that = this;
switch (_that) {
case _SdkSurface() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue id,  List<SdkSurfaceMethod> methods,  String name,  String? title,  String? description, @UuidValueConverter()  UuidValue sdkConfigId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _SdkSurface() when def != null:
return def(_that.id,_that.methods,_that.name,_that.title,_that.description,_that.sdkConfigId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue id,  List<SdkSurfaceMethod> methods,  String name,  String? title,  String? description, @UuidValueConverter()  UuidValue sdkConfigId)  def,}) {final _that = this;
switch (_that) {
case _SdkSurface():
return def(_that.id,_that.methods,_that.name,_that.title,_that.description,_that.sdkConfigId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue id,  List<SdkSurfaceMethod> methods,  String name,  String? title,  String? description, @UuidValueConverter()  UuidValue sdkConfigId)?  def,}) {final _that = this;
switch (_that) {
case _SdkSurface() when def != null:
return def(_that.id,_that.methods,_that.name,_that.title,_that.description,_that.sdkConfigId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _SdkSurface implements SdkSurface {
   _SdkSurface({@UuidValueConverter() required this.id, final  List<SdkSurfaceMethod> methods = const [], required this.name, this.title, this.description, @UuidValueConverter() required this.sdkConfigId}): _methods = methods;
  factory _SdkSurface.fromJson(Map<String, dynamic> json) => _$SdkSurfaceFromJson(json);

@override@UuidValueConverter() final  UuidValue id;
 final  List<SdkSurfaceMethod> _methods;
@override@JsonKey() List<SdkSurfaceMethod> get methods {
  if (_methods is EqualUnmodifiableListView) return _methods;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_methods);
}

@override final  String name;
@override final  String? title;
@override final  String? description;
@override@UuidValueConverter() final  UuidValue sdkConfigId;

/// Create a copy of SdkSurface
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$SdkSurfaceCopyWith<_SdkSurface> get copyWith => __$SdkSurfaceCopyWithImpl<_SdkSurface>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$SdkSurfaceToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _SdkSurface&&(identical(other.id, id) || other.id == id)&&const DeepCollectionEquality().equals(other._methods, _methods)&&(identical(other.name, name) || other.name == name)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.sdkConfigId, sdkConfigId) || other.sdkConfigId == sdkConfigId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,const DeepCollectionEquality().hash(_methods),name,title,description,sdkConfigId);

@override
String toString() {
  return 'SdkSurface.def(id: $id, methods: $methods, name: $name, title: $title, description: $description, sdkConfigId: $sdkConfigId)';
}


}

/// @nodoc
abstract mixin class _$SdkSurfaceCopyWith<$Res> implements $SdkSurfaceCopyWith<$Res> {
  factory _$SdkSurfaceCopyWith(_SdkSurface value, $Res Function(_SdkSurface) _then) = __$SdkSurfaceCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue id, List<SdkSurfaceMethod> methods, String name, String? title, String? description,@UuidValueConverter() UuidValue sdkConfigId
});




}
/// @nodoc
class __$SdkSurfaceCopyWithImpl<$Res>
    implements _$SdkSurfaceCopyWith<$Res> {
  __$SdkSurfaceCopyWithImpl(this._self, this._then);

  final _SdkSurface _self;
  final $Res Function(_SdkSurface) _then;

/// Create a copy of SdkSurface
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? id = null,Object? methods = null,Object? name = null,Object? title = freezed,Object? description = freezed,Object? sdkConfigId = null,}) {
  return _then(_SdkSurface(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,methods: null == methods ? _self._methods : methods // ignore: cast_nullable_to_non_nullable
as List<SdkSurfaceMethod>,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,sdkConfigId: null == sdkConfigId ? _self.sdkConfigId : sdkConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,
  ));
}


}

// dart format on
