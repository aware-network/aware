// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'sdk_config_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$SdkConfig {

@UuidValueConverter() UuidValue get id; List<SdkOperation> get operations; List<SdkSurface> get surfaces; String get name; String? get title; String? get description;
/// Create a copy of SdkConfig
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$SdkConfigCopyWith<SdkConfig> get copyWith => _$SdkConfigCopyWithImpl<SdkConfig>(this as SdkConfig, _$identity);

  /// Serializes this SdkConfig to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is SdkConfig&&(identical(other.id, id) || other.id == id)&&const DeepCollectionEquality().equals(other.operations, operations)&&const DeepCollectionEquality().equals(other.surfaces, surfaces)&&(identical(other.name, name) || other.name == name)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,const DeepCollectionEquality().hash(operations),const DeepCollectionEquality().hash(surfaces),name,title,description);

@override
String toString() {
  return 'SdkConfig(id: $id, operations: $operations, surfaces: $surfaces, name: $name, title: $title, description: $description)';
}


}

/// @nodoc
abstract mixin class $SdkConfigCopyWith<$Res>  {
  factory $SdkConfigCopyWith(SdkConfig value, $Res Function(SdkConfig) _then) = _$SdkConfigCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue id, List<SdkOperation> operations, List<SdkSurface> surfaces, String name, String? title, String? description
});




}
/// @nodoc
class _$SdkConfigCopyWithImpl<$Res>
    implements $SdkConfigCopyWith<$Res> {
  _$SdkConfigCopyWithImpl(this._self, this._then);

  final SdkConfig _self;
  final $Res Function(SdkConfig) _then;

/// Create a copy of SdkConfig
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? id = null,Object? operations = null,Object? surfaces = null,Object? name = null,Object? title = freezed,Object? description = freezed,}) {
  return _then(_self.copyWith(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,operations: null == operations ? _self.operations : operations // ignore: cast_nullable_to_non_nullable
as List<SdkOperation>,surfaces: null == surfaces ? _self.surfaces : surfaces // ignore: cast_nullable_to_non_nullable
as List<SdkSurface>,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [SdkConfig].
extension SdkConfigPatterns on SdkConfig {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _SdkConfig value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _SdkConfig() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _SdkConfig value)  def,}){
final _that = this;
switch (_that) {
case _SdkConfig():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _SdkConfig value)?  def,}){
final _that = this;
switch (_that) {
case _SdkConfig() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue id,  List<SdkOperation> operations,  List<SdkSurface> surfaces,  String name,  String? title,  String? description)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _SdkConfig() when def != null:
return def(_that.id,_that.operations,_that.surfaces,_that.name,_that.title,_that.description);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue id,  List<SdkOperation> operations,  List<SdkSurface> surfaces,  String name,  String? title,  String? description)  def,}) {final _that = this;
switch (_that) {
case _SdkConfig():
return def(_that.id,_that.operations,_that.surfaces,_that.name,_that.title,_that.description);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue id,  List<SdkOperation> operations,  List<SdkSurface> surfaces,  String name,  String? title,  String? description)?  def,}) {final _that = this;
switch (_that) {
case _SdkConfig() when def != null:
return def(_that.id,_that.operations,_that.surfaces,_that.name,_that.title,_that.description);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _SdkConfig implements SdkConfig {
   _SdkConfig({@UuidValueConverter() required this.id, final  List<SdkOperation> operations = const [], final  List<SdkSurface> surfaces = const [], required this.name, this.title, this.description}): _operations = operations,_surfaces = surfaces;
  factory _SdkConfig.fromJson(Map<String, dynamic> json) => _$SdkConfigFromJson(json);

@override@UuidValueConverter() final  UuidValue id;
 final  List<SdkOperation> _operations;
@override@JsonKey() List<SdkOperation> get operations {
  if (_operations is EqualUnmodifiableListView) return _operations;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_operations);
}

 final  List<SdkSurface> _surfaces;
@override@JsonKey() List<SdkSurface> get surfaces {
  if (_surfaces is EqualUnmodifiableListView) return _surfaces;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_surfaces);
}

@override final  String name;
@override final  String? title;
@override final  String? description;

/// Create a copy of SdkConfig
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$SdkConfigCopyWith<_SdkConfig> get copyWith => __$SdkConfigCopyWithImpl<_SdkConfig>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$SdkConfigToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _SdkConfig&&(identical(other.id, id) || other.id == id)&&const DeepCollectionEquality().equals(other._operations, _operations)&&const DeepCollectionEquality().equals(other._surfaces, _surfaces)&&(identical(other.name, name) || other.name == name)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,const DeepCollectionEquality().hash(_operations),const DeepCollectionEquality().hash(_surfaces),name,title,description);

@override
String toString() {
  return 'SdkConfig.def(id: $id, operations: $operations, surfaces: $surfaces, name: $name, title: $title, description: $description)';
}


}

/// @nodoc
abstract mixin class _$SdkConfigCopyWith<$Res> implements $SdkConfigCopyWith<$Res> {
  factory _$SdkConfigCopyWith(_SdkConfig value, $Res Function(_SdkConfig) _then) = __$SdkConfigCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue id, List<SdkOperation> operations, List<SdkSurface> surfaces, String name, String? title, String? description
});




}
/// @nodoc
class __$SdkConfigCopyWithImpl<$Res>
    implements _$SdkConfigCopyWith<$Res> {
  __$SdkConfigCopyWithImpl(this._self, this._then);

  final _SdkConfig _self;
  final $Res Function(_SdkConfig) _then;

/// Create a copy of SdkConfig
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? id = null,Object? operations = null,Object? surfaces = null,Object? name = null,Object? title = freezed,Object? description = freezed,}) {
  return _then(_SdkConfig(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,operations: null == operations ? _self._operations : operations // ignore: cast_nullable_to_non_nullable
as List<SdkOperation>,surfaces: null == surfaces ? _self._surfaces : surfaces // ignore: cast_nullable_to_non_nullable
as List<SdkSurface>,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

// dart format on
