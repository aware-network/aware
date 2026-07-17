// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'interface_config_bundle_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$InterfaceConfigApiBundle {

@UuidValueConverter() UuidValue get interfaceConfigApiId;@UuidValueConverter() UuidValue get apiId; String get apiRef;
/// Create a copy of InterfaceConfigApiBundle
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceConfigApiBundleCopyWith<InterfaceConfigApiBundle> get copyWith => _$InterfaceConfigApiBundleCopyWithImpl<InterfaceConfigApiBundle>(this as InterfaceConfigApiBundle, _$identity);

  /// Serializes this InterfaceConfigApiBundle to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceConfigApiBundle&&(identical(other.interfaceConfigApiId, interfaceConfigApiId) || other.interfaceConfigApiId == interfaceConfigApiId)&&(identical(other.apiId, apiId) || other.apiId == apiId)&&(identical(other.apiRef, apiRef) || other.apiRef == apiRef));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,interfaceConfigApiId,apiId,apiRef);

@override
String toString() {
  return 'InterfaceConfigApiBundle(interfaceConfigApiId: $interfaceConfigApiId, apiId: $apiId, apiRef: $apiRef)';
}


}

/// @nodoc
abstract mixin class $InterfaceConfigApiBundleCopyWith<$Res>  {
  factory $InterfaceConfigApiBundleCopyWith(InterfaceConfigApiBundle value, $Res Function(InterfaceConfigApiBundle) _then) = _$InterfaceConfigApiBundleCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue interfaceConfigApiId,@UuidValueConverter() UuidValue apiId, String apiRef
});




}
/// @nodoc
class _$InterfaceConfigApiBundleCopyWithImpl<$Res>
    implements $InterfaceConfigApiBundleCopyWith<$Res> {
  _$InterfaceConfigApiBundleCopyWithImpl(this._self, this._then);

  final InterfaceConfigApiBundle _self;
  final $Res Function(InterfaceConfigApiBundle) _then;

/// Create a copy of InterfaceConfigApiBundle
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? interfaceConfigApiId = null,Object? apiId = null,Object? apiRef = null,}) {
  return _then(_self.copyWith(
interfaceConfigApiId: null == interfaceConfigApiId ? _self.interfaceConfigApiId : interfaceConfigApiId // ignore: cast_nullable_to_non_nullable
as UuidValue,apiId: null == apiId ? _self.apiId : apiId // ignore: cast_nullable_to_non_nullable
as UuidValue,apiRef: null == apiRef ? _self.apiRef : apiRef // ignore: cast_nullable_to_non_nullable
as String,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfaceConfigApiBundle].
extension InterfaceConfigApiBundlePatterns on InterfaceConfigApiBundle {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfaceConfigApiBundle value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfaceConfigApiBundle() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfaceConfigApiBundle value)  def,}){
final _that = this;
switch (_that) {
case _InterfaceConfigApiBundle():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfaceConfigApiBundle value)?  def,}){
final _that = this;
switch (_that) {
case _InterfaceConfigApiBundle() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue interfaceConfigApiId, @UuidValueConverter()  UuidValue apiId,  String apiRef)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfaceConfigApiBundle() when def != null:
return def(_that.interfaceConfigApiId,_that.apiId,_that.apiRef);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue interfaceConfigApiId, @UuidValueConverter()  UuidValue apiId,  String apiRef)  def,}) {final _that = this;
switch (_that) {
case _InterfaceConfigApiBundle():
return def(_that.interfaceConfigApiId,_that.apiId,_that.apiRef);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue interfaceConfigApiId, @UuidValueConverter()  UuidValue apiId,  String apiRef)?  def,}) {final _that = this;
switch (_that) {
case _InterfaceConfigApiBundle() when def != null:
return def(_that.interfaceConfigApiId,_that.apiId,_that.apiRef);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfaceConfigApiBundle implements InterfaceConfigApiBundle {
   _InterfaceConfigApiBundle({@UuidValueConverter() required this.interfaceConfigApiId, @UuidValueConverter() required this.apiId, required this.apiRef});
  factory _InterfaceConfigApiBundle.fromJson(Map<String, dynamic> json) => _$InterfaceConfigApiBundleFromJson(json);

@override@UuidValueConverter() final  UuidValue interfaceConfigApiId;
@override@UuidValueConverter() final  UuidValue apiId;
@override final  String apiRef;

/// Create a copy of InterfaceConfigApiBundle
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfaceConfigApiBundleCopyWith<_InterfaceConfigApiBundle> get copyWith => __$InterfaceConfigApiBundleCopyWithImpl<_InterfaceConfigApiBundle>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceConfigApiBundleToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfaceConfigApiBundle&&(identical(other.interfaceConfigApiId, interfaceConfigApiId) || other.interfaceConfigApiId == interfaceConfigApiId)&&(identical(other.apiId, apiId) || other.apiId == apiId)&&(identical(other.apiRef, apiRef) || other.apiRef == apiRef));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,interfaceConfigApiId,apiId,apiRef);

@override
String toString() {
  return 'InterfaceConfigApiBundle.def(interfaceConfigApiId: $interfaceConfigApiId, apiId: $apiId, apiRef: $apiRef)';
}


}

/// @nodoc
abstract mixin class _$InterfaceConfigApiBundleCopyWith<$Res> implements $InterfaceConfigApiBundleCopyWith<$Res> {
  factory _$InterfaceConfigApiBundleCopyWith(_InterfaceConfigApiBundle value, $Res Function(_InterfaceConfigApiBundle) _then) = __$InterfaceConfigApiBundleCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue interfaceConfigApiId,@UuidValueConverter() UuidValue apiId, String apiRef
});




}
/// @nodoc
class __$InterfaceConfigApiBundleCopyWithImpl<$Res>
    implements _$InterfaceConfigApiBundleCopyWith<$Res> {
  __$InterfaceConfigApiBundleCopyWithImpl(this._self, this._then);

  final _InterfaceConfigApiBundle _self;
  final $Res Function(_InterfaceConfigApiBundle) _then;

/// Create a copy of InterfaceConfigApiBundle
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? interfaceConfigApiId = null,Object? apiId = null,Object? apiRef = null,}) {
  return _then(_InterfaceConfigApiBundle(
interfaceConfigApiId: null == interfaceConfigApiId ? _self.interfaceConfigApiId : interfaceConfigApiId // ignore: cast_nullable_to_non_nullable
as UuidValue,apiId: null == apiId ? _self.apiId : apiId // ignore: cast_nullable_to_non_nullable
as UuidValue,apiRef: null == apiRef ? _self.apiRef : apiRef // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}


/// @nodoc
mixin _$InterfaceWindowLayoutSectionBundle {

@UuidValueConverter() UuidValue get layoutConfigSectionConfigId; String get key;
/// Create a copy of InterfaceWindowLayoutSectionBundle
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceWindowLayoutSectionBundleCopyWith<InterfaceWindowLayoutSectionBundle> get copyWith => _$InterfaceWindowLayoutSectionBundleCopyWithImpl<InterfaceWindowLayoutSectionBundle>(this as InterfaceWindowLayoutSectionBundle, _$identity);

  /// Serializes this InterfaceWindowLayoutSectionBundle to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceWindowLayoutSectionBundle&&(identical(other.layoutConfigSectionConfigId, layoutConfigSectionConfigId) || other.layoutConfigSectionConfigId == layoutConfigSectionConfigId)&&(identical(other.key, key) || other.key == key));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,layoutConfigSectionConfigId,key);

@override
String toString() {
  return 'InterfaceWindowLayoutSectionBundle(layoutConfigSectionConfigId: $layoutConfigSectionConfigId, key: $key)';
}


}

/// @nodoc
abstract mixin class $InterfaceWindowLayoutSectionBundleCopyWith<$Res>  {
  factory $InterfaceWindowLayoutSectionBundleCopyWith(InterfaceWindowLayoutSectionBundle value, $Res Function(InterfaceWindowLayoutSectionBundle) _then) = _$InterfaceWindowLayoutSectionBundleCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue layoutConfigSectionConfigId, String key
});




}
/// @nodoc
class _$InterfaceWindowLayoutSectionBundleCopyWithImpl<$Res>
    implements $InterfaceWindowLayoutSectionBundleCopyWith<$Res> {
  _$InterfaceWindowLayoutSectionBundleCopyWithImpl(this._self, this._then);

  final InterfaceWindowLayoutSectionBundle _self;
  final $Res Function(InterfaceWindowLayoutSectionBundle) _then;

/// Create a copy of InterfaceWindowLayoutSectionBundle
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? layoutConfigSectionConfigId = null,Object? key = null,}) {
  return _then(_self.copyWith(
layoutConfigSectionConfigId: null == layoutConfigSectionConfigId ? _self.layoutConfigSectionConfigId : layoutConfigSectionConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,key: null == key ? _self.key : key // ignore: cast_nullable_to_non_nullable
as String,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfaceWindowLayoutSectionBundle].
extension InterfaceWindowLayoutSectionBundlePatterns on InterfaceWindowLayoutSectionBundle {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfaceWindowLayoutSectionBundle value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfaceWindowLayoutSectionBundle() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfaceWindowLayoutSectionBundle value)  def,}){
final _that = this;
switch (_that) {
case _InterfaceWindowLayoutSectionBundle():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfaceWindowLayoutSectionBundle value)?  def,}){
final _that = this;
switch (_that) {
case _InterfaceWindowLayoutSectionBundle() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue layoutConfigSectionConfigId,  String key)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfaceWindowLayoutSectionBundle() when def != null:
return def(_that.layoutConfigSectionConfigId,_that.key);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue layoutConfigSectionConfigId,  String key)  def,}) {final _that = this;
switch (_that) {
case _InterfaceWindowLayoutSectionBundle():
return def(_that.layoutConfigSectionConfigId,_that.key);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue layoutConfigSectionConfigId,  String key)?  def,}) {final _that = this;
switch (_that) {
case _InterfaceWindowLayoutSectionBundle() when def != null:
return def(_that.layoutConfigSectionConfigId,_that.key);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfaceWindowLayoutSectionBundle implements InterfaceWindowLayoutSectionBundle {
   _InterfaceWindowLayoutSectionBundle({@UuidValueConverter() required this.layoutConfigSectionConfigId, required this.key});
  factory _InterfaceWindowLayoutSectionBundle.fromJson(Map<String, dynamic> json) => _$InterfaceWindowLayoutSectionBundleFromJson(json);

@override@UuidValueConverter() final  UuidValue layoutConfigSectionConfigId;
@override final  String key;

/// Create a copy of InterfaceWindowLayoutSectionBundle
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfaceWindowLayoutSectionBundleCopyWith<_InterfaceWindowLayoutSectionBundle> get copyWith => __$InterfaceWindowLayoutSectionBundleCopyWithImpl<_InterfaceWindowLayoutSectionBundle>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceWindowLayoutSectionBundleToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfaceWindowLayoutSectionBundle&&(identical(other.layoutConfigSectionConfigId, layoutConfigSectionConfigId) || other.layoutConfigSectionConfigId == layoutConfigSectionConfigId)&&(identical(other.key, key) || other.key == key));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,layoutConfigSectionConfigId,key);

@override
String toString() {
  return 'InterfaceWindowLayoutSectionBundle.def(layoutConfigSectionConfigId: $layoutConfigSectionConfigId, key: $key)';
}


}

/// @nodoc
abstract mixin class _$InterfaceWindowLayoutSectionBundleCopyWith<$Res> implements $InterfaceWindowLayoutSectionBundleCopyWith<$Res> {
  factory _$InterfaceWindowLayoutSectionBundleCopyWith(_InterfaceWindowLayoutSectionBundle value, $Res Function(_InterfaceWindowLayoutSectionBundle) _then) = __$InterfaceWindowLayoutSectionBundleCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue layoutConfigSectionConfigId, String key
});




}
/// @nodoc
class __$InterfaceWindowLayoutSectionBundleCopyWithImpl<$Res>
    implements _$InterfaceWindowLayoutSectionBundleCopyWith<$Res> {
  __$InterfaceWindowLayoutSectionBundleCopyWithImpl(this._self, this._then);

  final _InterfaceWindowLayoutSectionBundle _self;
  final $Res Function(_InterfaceWindowLayoutSectionBundle) _then;

/// Create a copy of InterfaceWindowLayoutSectionBundle
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? layoutConfigSectionConfigId = null,Object? key = null,}) {
  return _then(_InterfaceWindowLayoutSectionBundle(
layoutConfigSectionConfigId: null == layoutConfigSectionConfigId ? _self.layoutConfigSectionConfigId : layoutConfigSectionConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,key: null == key ? _self.key : key // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}


/// @nodoc
mixin _$InterfaceWindowConfigLayoutBundle {

@UuidValueConverter() UuidValue get windowConfigLayoutConfigId;@UuidValueConverter() UuidValue get layoutConfigId; String get key; List<InterfaceWindowLayoutSectionBundle> get sections;
/// Create a copy of InterfaceWindowConfigLayoutBundle
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceWindowConfigLayoutBundleCopyWith<InterfaceWindowConfigLayoutBundle> get copyWith => _$InterfaceWindowConfigLayoutBundleCopyWithImpl<InterfaceWindowConfigLayoutBundle>(this as InterfaceWindowConfigLayoutBundle, _$identity);

  /// Serializes this InterfaceWindowConfigLayoutBundle to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceWindowConfigLayoutBundle&&(identical(other.windowConfigLayoutConfigId, windowConfigLayoutConfigId) || other.windowConfigLayoutConfigId == windowConfigLayoutConfigId)&&(identical(other.layoutConfigId, layoutConfigId) || other.layoutConfigId == layoutConfigId)&&(identical(other.key, key) || other.key == key)&&const DeepCollectionEquality().equals(other.sections, sections));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,windowConfigLayoutConfigId,layoutConfigId,key,const DeepCollectionEquality().hash(sections));

@override
String toString() {
  return 'InterfaceWindowConfigLayoutBundle(windowConfigLayoutConfigId: $windowConfigLayoutConfigId, layoutConfigId: $layoutConfigId, key: $key, sections: $sections)';
}


}

/// @nodoc
abstract mixin class $InterfaceWindowConfigLayoutBundleCopyWith<$Res>  {
  factory $InterfaceWindowConfigLayoutBundleCopyWith(InterfaceWindowConfigLayoutBundle value, $Res Function(InterfaceWindowConfigLayoutBundle) _then) = _$InterfaceWindowConfigLayoutBundleCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue windowConfigLayoutConfigId,@UuidValueConverter() UuidValue layoutConfigId, String key, List<InterfaceWindowLayoutSectionBundle> sections
});




}
/// @nodoc
class _$InterfaceWindowConfigLayoutBundleCopyWithImpl<$Res>
    implements $InterfaceWindowConfigLayoutBundleCopyWith<$Res> {
  _$InterfaceWindowConfigLayoutBundleCopyWithImpl(this._self, this._then);

  final InterfaceWindowConfigLayoutBundle _self;
  final $Res Function(InterfaceWindowConfigLayoutBundle) _then;

/// Create a copy of InterfaceWindowConfigLayoutBundle
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? windowConfigLayoutConfigId = null,Object? layoutConfigId = null,Object? key = null,Object? sections = null,}) {
  return _then(_self.copyWith(
windowConfigLayoutConfigId: null == windowConfigLayoutConfigId ? _self.windowConfigLayoutConfigId : windowConfigLayoutConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,layoutConfigId: null == layoutConfigId ? _self.layoutConfigId : layoutConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,key: null == key ? _self.key : key // ignore: cast_nullable_to_non_nullable
as String,sections: null == sections ? _self.sections : sections // ignore: cast_nullable_to_non_nullable
as List<InterfaceWindowLayoutSectionBundle>,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfaceWindowConfigLayoutBundle].
extension InterfaceWindowConfigLayoutBundlePatterns on InterfaceWindowConfigLayoutBundle {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfaceWindowConfigLayoutBundle value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfaceWindowConfigLayoutBundle() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfaceWindowConfigLayoutBundle value)  def,}){
final _that = this;
switch (_that) {
case _InterfaceWindowConfigLayoutBundle():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfaceWindowConfigLayoutBundle value)?  def,}){
final _that = this;
switch (_that) {
case _InterfaceWindowConfigLayoutBundle() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue windowConfigLayoutConfigId, @UuidValueConverter()  UuidValue layoutConfigId,  String key,  List<InterfaceWindowLayoutSectionBundle> sections)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfaceWindowConfigLayoutBundle() when def != null:
return def(_that.windowConfigLayoutConfigId,_that.layoutConfigId,_that.key,_that.sections);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue windowConfigLayoutConfigId, @UuidValueConverter()  UuidValue layoutConfigId,  String key,  List<InterfaceWindowLayoutSectionBundle> sections)  def,}) {final _that = this;
switch (_that) {
case _InterfaceWindowConfigLayoutBundle():
return def(_that.windowConfigLayoutConfigId,_that.layoutConfigId,_that.key,_that.sections);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue windowConfigLayoutConfigId, @UuidValueConverter()  UuidValue layoutConfigId,  String key,  List<InterfaceWindowLayoutSectionBundle> sections)?  def,}) {final _that = this;
switch (_that) {
case _InterfaceWindowConfigLayoutBundle() when def != null:
return def(_that.windowConfigLayoutConfigId,_that.layoutConfigId,_that.key,_that.sections);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfaceWindowConfigLayoutBundle implements InterfaceWindowConfigLayoutBundle {
   _InterfaceWindowConfigLayoutBundle({@UuidValueConverter() required this.windowConfigLayoutConfigId, @UuidValueConverter() required this.layoutConfigId, required this.key, final  List<InterfaceWindowLayoutSectionBundle> sections = const []}): _sections = sections;
  factory _InterfaceWindowConfigLayoutBundle.fromJson(Map<String, dynamic> json) => _$InterfaceWindowConfigLayoutBundleFromJson(json);

@override@UuidValueConverter() final  UuidValue windowConfigLayoutConfigId;
@override@UuidValueConverter() final  UuidValue layoutConfigId;
@override final  String key;
 final  List<InterfaceWindowLayoutSectionBundle> _sections;
@override@JsonKey() List<InterfaceWindowLayoutSectionBundle> get sections {
  if (_sections is EqualUnmodifiableListView) return _sections;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_sections);
}


/// Create a copy of InterfaceWindowConfigLayoutBundle
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfaceWindowConfigLayoutBundleCopyWith<_InterfaceWindowConfigLayoutBundle> get copyWith => __$InterfaceWindowConfigLayoutBundleCopyWithImpl<_InterfaceWindowConfigLayoutBundle>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceWindowConfigLayoutBundleToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfaceWindowConfigLayoutBundle&&(identical(other.windowConfigLayoutConfigId, windowConfigLayoutConfigId) || other.windowConfigLayoutConfigId == windowConfigLayoutConfigId)&&(identical(other.layoutConfigId, layoutConfigId) || other.layoutConfigId == layoutConfigId)&&(identical(other.key, key) || other.key == key)&&const DeepCollectionEquality().equals(other._sections, _sections));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,windowConfigLayoutConfigId,layoutConfigId,key,const DeepCollectionEquality().hash(_sections));

@override
String toString() {
  return 'InterfaceWindowConfigLayoutBundle.def(windowConfigLayoutConfigId: $windowConfigLayoutConfigId, layoutConfigId: $layoutConfigId, key: $key, sections: $sections)';
}


}

/// @nodoc
abstract mixin class _$InterfaceWindowConfigLayoutBundleCopyWith<$Res> implements $InterfaceWindowConfigLayoutBundleCopyWith<$Res> {
  factory _$InterfaceWindowConfigLayoutBundleCopyWith(_InterfaceWindowConfigLayoutBundle value, $Res Function(_InterfaceWindowConfigLayoutBundle) _then) = __$InterfaceWindowConfigLayoutBundleCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue windowConfigLayoutConfigId,@UuidValueConverter() UuidValue layoutConfigId, String key, List<InterfaceWindowLayoutSectionBundle> sections
});




}
/// @nodoc
class __$InterfaceWindowConfigLayoutBundleCopyWithImpl<$Res>
    implements _$InterfaceWindowConfigLayoutBundleCopyWith<$Res> {
  __$InterfaceWindowConfigLayoutBundleCopyWithImpl(this._self, this._then);

  final _InterfaceWindowConfigLayoutBundle _self;
  final $Res Function(_InterfaceWindowConfigLayoutBundle) _then;

/// Create a copy of InterfaceWindowConfigLayoutBundle
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? windowConfigLayoutConfigId = null,Object? layoutConfigId = null,Object? key = null,Object? sections = null,}) {
  return _then(_InterfaceWindowConfigLayoutBundle(
windowConfigLayoutConfigId: null == windowConfigLayoutConfigId ? _self.windowConfigLayoutConfigId : windowConfigLayoutConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,layoutConfigId: null == layoutConfigId ? _self.layoutConfigId : layoutConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,key: null == key ? _self.key : key // ignore: cast_nullable_to_non_nullable
as String,sections: null == sections ? _self._sections : sections // ignore: cast_nullable_to_non_nullable
as List<InterfaceWindowLayoutSectionBundle>,
  ));
}


}


/// @nodoc
mixin _$InterfaceWindowConfigBundle {

@UuidValueConverter() UuidValue get interfaceConfigWindowConfigId;@UuidValueConverter() UuidValue get windowConfigId; String get key; String? get description; List<InterfaceWindowConfigLayoutBundle> get layoutConfigs;
/// Create a copy of InterfaceWindowConfigBundle
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceWindowConfigBundleCopyWith<InterfaceWindowConfigBundle> get copyWith => _$InterfaceWindowConfigBundleCopyWithImpl<InterfaceWindowConfigBundle>(this as InterfaceWindowConfigBundle, _$identity);

  /// Serializes this InterfaceWindowConfigBundle to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceWindowConfigBundle&&(identical(other.interfaceConfigWindowConfigId, interfaceConfigWindowConfigId) || other.interfaceConfigWindowConfigId == interfaceConfigWindowConfigId)&&(identical(other.windowConfigId, windowConfigId) || other.windowConfigId == windowConfigId)&&(identical(other.key, key) || other.key == key)&&(identical(other.description, description) || other.description == description)&&const DeepCollectionEquality().equals(other.layoutConfigs, layoutConfigs));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,interfaceConfigWindowConfigId,windowConfigId,key,description,const DeepCollectionEquality().hash(layoutConfigs));

@override
String toString() {
  return 'InterfaceWindowConfigBundle(interfaceConfigWindowConfigId: $interfaceConfigWindowConfigId, windowConfigId: $windowConfigId, key: $key, description: $description, layoutConfigs: $layoutConfigs)';
}


}

/// @nodoc
abstract mixin class $InterfaceWindowConfigBundleCopyWith<$Res>  {
  factory $InterfaceWindowConfigBundleCopyWith(InterfaceWindowConfigBundle value, $Res Function(InterfaceWindowConfigBundle) _then) = _$InterfaceWindowConfigBundleCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue interfaceConfigWindowConfigId,@UuidValueConverter() UuidValue windowConfigId, String key, String? description, List<InterfaceWindowConfigLayoutBundle> layoutConfigs
});




}
/// @nodoc
class _$InterfaceWindowConfigBundleCopyWithImpl<$Res>
    implements $InterfaceWindowConfigBundleCopyWith<$Res> {
  _$InterfaceWindowConfigBundleCopyWithImpl(this._self, this._then);

  final InterfaceWindowConfigBundle _self;
  final $Res Function(InterfaceWindowConfigBundle) _then;

/// Create a copy of InterfaceWindowConfigBundle
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? interfaceConfigWindowConfigId = null,Object? windowConfigId = null,Object? key = null,Object? description = freezed,Object? layoutConfigs = null,}) {
  return _then(_self.copyWith(
interfaceConfigWindowConfigId: null == interfaceConfigWindowConfigId ? _self.interfaceConfigWindowConfigId : interfaceConfigWindowConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,windowConfigId: null == windowConfigId ? _self.windowConfigId : windowConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,key: null == key ? _self.key : key // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,layoutConfigs: null == layoutConfigs ? _self.layoutConfigs : layoutConfigs // ignore: cast_nullable_to_non_nullable
as List<InterfaceWindowConfigLayoutBundle>,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfaceWindowConfigBundle].
extension InterfaceWindowConfigBundlePatterns on InterfaceWindowConfigBundle {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfaceWindowConfigBundle value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfaceWindowConfigBundle() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfaceWindowConfigBundle value)  def,}){
final _that = this;
switch (_that) {
case _InterfaceWindowConfigBundle():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfaceWindowConfigBundle value)?  def,}){
final _that = this;
switch (_that) {
case _InterfaceWindowConfigBundle() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue interfaceConfigWindowConfigId, @UuidValueConverter()  UuidValue windowConfigId,  String key,  String? description,  List<InterfaceWindowConfigLayoutBundle> layoutConfigs)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfaceWindowConfigBundle() when def != null:
return def(_that.interfaceConfigWindowConfigId,_that.windowConfigId,_that.key,_that.description,_that.layoutConfigs);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue interfaceConfigWindowConfigId, @UuidValueConverter()  UuidValue windowConfigId,  String key,  String? description,  List<InterfaceWindowConfigLayoutBundle> layoutConfigs)  def,}) {final _that = this;
switch (_that) {
case _InterfaceWindowConfigBundle():
return def(_that.interfaceConfigWindowConfigId,_that.windowConfigId,_that.key,_that.description,_that.layoutConfigs);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue interfaceConfigWindowConfigId, @UuidValueConverter()  UuidValue windowConfigId,  String key,  String? description,  List<InterfaceWindowConfigLayoutBundle> layoutConfigs)?  def,}) {final _that = this;
switch (_that) {
case _InterfaceWindowConfigBundle() when def != null:
return def(_that.interfaceConfigWindowConfigId,_that.windowConfigId,_that.key,_that.description,_that.layoutConfigs);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfaceWindowConfigBundle implements InterfaceWindowConfigBundle {
   _InterfaceWindowConfigBundle({@UuidValueConverter() required this.interfaceConfigWindowConfigId, @UuidValueConverter() required this.windowConfigId, required this.key, this.description, final  List<InterfaceWindowConfigLayoutBundle> layoutConfigs = const []}): _layoutConfigs = layoutConfigs;
  factory _InterfaceWindowConfigBundle.fromJson(Map<String, dynamic> json) => _$InterfaceWindowConfigBundleFromJson(json);

@override@UuidValueConverter() final  UuidValue interfaceConfigWindowConfigId;
@override@UuidValueConverter() final  UuidValue windowConfigId;
@override final  String key;
@override final  String? description;
 final  List<InterfaceWindowConfigLayoutBundle> _layoutConfigs;
@override@JsonKey() List<InterfaceWindowConfigLayoutBundle> get layoutConfigs {
  if (_layoutConfigs is EqualUnmodifiableListView) return _layoutConfigs;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_layoutConfigs);
}


/// Create a copy of InterfaceWindowConfigBundle
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfaceWindowConfigBundleCopyWith<_InterfaceWindowConfigBundle> get copyWith => __$InterfaceWindowConfigBundleCopyWithImpl<_InterfaceWindowConfigBundle>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceWindowConfigBundleToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfaceWindowConfigBundle&&(identical(other.interfaceConfigWindowConfigId, interfaceConfigWindowConfigId) || other.interfaceConfigWindowConfigId == interfaceConfigWindowConfigId)&&(identical(other.windowConfigId, windowConfigId) || other.windowConfigId == windowConfigId)&&(identical(other.key, key) || other.key == key)&&(identical(other.description, description) || other.description == description)&&const DeepCollectionEquality().equals(other._layoutConfigs, _layoutConfigs));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,interfaceConfigWindowConfigId,windowConfigId,key,description,const DeepCollectionEquality().hash(_layoutConfigs));

@override
String toString() {
  return 'InterfaceWindowConfigBundle.def(interfaceConfigWindowConfigId: $interfaceConfigWindowConfigId, windowConfigId: $windowConfigId, key: $key, description: $description, layoutConfigs: $layoutConfigs)';
}


}

/// @nodoc
abstract mixin class _$InterfaceWindowConfigBundleCopyWith<$Res> implements $InterfaceWindowConfigBundleCopyWith<$Res> {
  factory _$InterfaceWindowConfigBundleCopyWith(_InterfaceWindowConfigBundle value, $Res Function(_InterfaceWindowConfigBundle) _then) = __$InterfaceWindowConfigBundleCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue interfaceConfigWindowConfigId,@UuidValueConverter() UuidValue windowConfigId, String key, String? description, List<InterfaceWindowConfigLayoutBundle> layoutConfigs
});




}
/// @nodoc
class __$InterfaceWindowConfigBundleCopyWithImpl<$Res>
    implements _$InterfaceWindowConfigBundleCopyWith<$Res> {
  __$InterfaceWindowConfigBundleCopyWithImpl(this._self, this._then);

  final _InterfaceWindowConfigBundle _self;
  final $Res Function(_InterfaceWindowConfigBundle) _then;

/// Create a copy of InterfaceWindowConfigBundle
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? interfaceConfigWindowConfigId = null,Object? windowConfigId = null,Object? key = null,Object? description = freezed,Object? layoutConfigs = null,}) {
  return _then(_InterfaceWindowConfigBundle(
interfaceConfigWindowConfigId: null == interfaceConfigWindowConfigId ? _self.interfaceConfigWindowConfigId : interfaceConfigWindowConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,windowConfigId: null == windowConfigId ? _self.windowConfigId : windowConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,key: null == key ? _self.key : key // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,layoutConfigs: null == layoutConfigs ? _self._layoutConfigs : layoutConfigs // ignore: cast_nullable_to_non_nullable
as List<InterfaceWindowConfigLayoutBundle>,
  ));
}


}


/// @nodoc
mixin _$InterfacePaneSectionMountBundle {

@UuidValueConverter() UuidValue get mountId;@UuidValueConverter() UuidValue get layoutConfigSectionConfigId;
/// Create a copy of InterfacePaneSectionMountBundle
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfacePaneSectionMountBundleCopyWith<InterfacePaneSectionMountBundle> get copyWith => _$InterfacePaneSectionMountBundleCopyWithImpl<InterfacePaneSectionMountBundle>(this as InterfacePaneSectionMountBundle, _$identity);

  /// Serializes this InterfacePaneSectionMountBundle to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfacePaneSectionMountBundle&&(identical(other.mountId, mountId) || other.mountId == mountId)&&(identical(other.layoutConfigSectionConfigId, layoutConfigSectionConfigId) || other.layoutConfigSectionConfigId == layoutConfigSectionConfigId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,mountId,layoutConfigSectionConfigId);

@override
String toString() {
  return 'InterfacePaneSectionMountBundle(mountId: $mountId, layoutConfigSectionConfigId: $layoutConfigSectionConfigId)';
}


}

/// @nodoc
abstract mixin class $InterfacePaneSectionMountBundleCopyWith<$Res>  {
  factory $InterfacePaneSectionMountBundleCopyWith(InterfacePaneSectionMountBundle value, $Res Function(InterfacePaneSectionMountBundle) _then) = _$InterfacePaneSectionMountBundleCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue mountId,@UuidValueConverter() UuidValue layoutConfigSectionConfigId
});




}
/// @nodoc
class _$InterfacePaneSectionMountBundleCopyWithImpl<$Res>
    implements $InterfacePaneSectionMountBundleCopyWith<$Res> {
  _$InterfacePaneSectionMountBundleCopyWithImpl(this._self, this._then);

  final InterfacePaneSectionMountBundle _self;
  final $Res Function(InterfacePaneSectionMountBundle) _then;

/// Create a copy of InterfacePaneSectionMountBundle
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? mountId = null,Object? layoutConfigSectionConfigId = null,}) {
  return _then(_self.copyWith(
mountId: null == mountId ? _self.mountId : mountId // ignore: cast_nullable_to_non_nullable
as UuidValue,layoutConfigSectionConfigId: null == layoutConfigSectionConfigId ? _self.layoutConfigSectionConfigId : layoutConfigSectionConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfacePaneSectionMountBundle].
extension InterfacePaneSectionMountBundlePatterns on InterfacePaneSectionMountBundle {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfacePaneSectionMountBundle value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfacePaneSectionMountBundle() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfacePaneSectionMountBundle value)  def,}){
final _that = this;
switch (_that) {
case _InterfacePaneSectionMountBundle():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfacePaneSectionMountBundle value)?  def,}){
final _that = this;
switch (_that) {
case _InterfacePaneSectionMountBundle() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue mountId, @UuidValueConverter()  UuidValue layoutConfigSectionConfigId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfacePaneSectionMountBundle() when def != null:
return def(_that.mountId,_that.layoutConfigSectionConfigId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue mountId, @UuidValueConverter()  UuidValue layoutConfigSectionConfigId)  def,}) {final _that = this;
switch (_that) {
case _InterfacePaneSectionMountBundle():
return def(_that.mountId,_that.layoutConfigSectionConfigId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue mountId, @UuidValueConverter()  UuidValue layoutConfigSectionConfigId)?  def,}) {final _that = this;
switch (_that) {
case _InterfacePaneSectionMountBundle() when def != null:
return def(_that.mountId,_that.layoutConfigSectionConfigId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfacePaneSectionMountBundle implements InterfacePaneSectionMountBundle {
   _InterfacePaneSectionMountBundle({@UuidValueConverter() required this.mountId, @UuidValueConverter() required this.layoutConfigSectionConfigId});
  factory _InterfacePaneSectionMountBundle.fromJson(Map<String, dynamic> json) => _$InterfacePaneSectionMountBundleFromJson(json);

@override@UuidValueConverter() final  UuidValue mountId;
@override@UuidValueConverter() final  UuidValue layoutConfigSectionConfigId;

/// Create a copy of InterfacePaneSectionMountBundle
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfacePaneSectionMountBundleCopyWith<_InterfacePaneSectionMountBundle> get copyWith => __$InterfacePaneSectionMountBundleCopyWithImpl<_InterfacePaneSectionMountBundle>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfacePaneSectionMountBundleToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfacePaneSectionMountBundle&&(identical(other.mountId, mountId) || other.mountId == mountId)&&(identical(other.layoutConfigSectionConfigId, layoutConfigSectionConfigId) || other.layoutConfigSectionConfigId == layoutConfigSectionConfigId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,mountId,layoutConfigSectionConfigId);

@override
String toString() {
  return 'InterfacePaneSectionMountBundle.def(mountId: $mountId, layoutConfigSectionConfigId: $layoutConfigSectionConfigId)';
}


}

/// @nodoc
abstract mixin class _$InterfacePaneSectionMountBundleCopyWith<$Res> implements $InterfacePaneSectionMountBundleCopyWith<$Res> {
  factory _$InterfacePaneSectionMountBundleCopyWith(_InterfacePaneSectionMountBundle value, $Res Function(_InterfacePaneSectionMountBundle) _then) = __$InterfacePaneSectionMountBundleCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue mountId,@UuidValueConverter() UuidValue layoutConfigSectionConfigId
});




}
/// @nodoc
class __$InterfacePaneSectionMountBundleCopyWithImpl<$Res>
    implements _$InterfacePaneSectionMountBundleCopyWith<$Res> {
  __$InterfacePaneSectionMountBundleCopyWithImpl(this._self, this._then);

  final _InterfacePaneSectionMountBundle _self;
  final $Res Function(_InterfacePaneSectionMountBundle) _then;

/// Create a copy of InterfacePaneSectionMountBundle
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? mountId = null,Object? layoutConfigSectionConfigId = null,}) {
  return _then(_InterfacePaneSectionMountBundle(
mountId: null == mountId ? _self.mountId : mountId // ignore: cast_nullable_to_non_nullable
as UuidValue,layoutConfigSectionConfigId: null == layoutConfigSectionConfigId ? _self.layoutConfigSectionConfigId : layoutConfigSectionConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,
  ));
}


}


/// @nodoc
mixin _$InterfacePaneViewInvocationActionBundle {

@UuidValueConverter() UuidValue get projectionExperienceViewInvocationActionId; String get actionKey; String get actionKind; String get targetRef;@UuidValueConverter() UuidValue? get apiCapabilityEndpointId;@UuidValueConverter() UuidValue? get sdkOperationId; String? get label; String? get receiptPolicy; String? get confirmationPolicy; String? get optimisticPolicy;
/// Create a copy of InterfacePaneViewInvocationActionBundle
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfacePaneViewInvocationActionBundleCopyWith<InterfacePaneViewInvocationActionBundle> get copyWith => _$InterfacePaneViewInvocationActionBundleCopyWithImpl<InterfacePaneViewInvocationActionBundle>(this as InterfacePaneViewInvocationActionBundle, _$identity);

  /// Serializes this InterfacePaneViewInvocationActionBundle to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfacePaneViewInvocationActionBundle&&(identical(other.projectionExperienceViewInvocationActionId, projectionExperienceViewInvocationActionId) || other.projectionExperienceViewInvocationActionId == projectionExperienceViewInvocationActionId)&&(identical(other.actionKey, actionKey) || other.actionKey == actionKey)&&(identical(other.actionKind, actionKind) || other.actionKind == actionKind)&&(identical(other.targetRef, targetRef) || other.targetRef == targetRef)&&(identical(other.apiCapabilityEndpointId, apiCapabilityEndpointId) || other.apiCapabilityEndpointId == apiCapabilityEndpointId)&&(identical(other.sdkOperationId, sdkOperationId) || other.sdkOperationId == sdkOperationId)&&(identical(other.label, label) || other.label == label)&&(identical(other.receiptPolicy, receiptPolicy) || other.receiptPolicy == receiptPolicy)&&(identical(other.confirmationPolicy, confirmationPolicy) || other.confirmationPolicy == confirmationPolicy)&&(identical(other.optimisticPolicy, optimisticPolicy) || other.optimisticPolicy == optimisticPolicy));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,projectionExperienceViewInvocationActionId,actionKey,actionKind,targetRef,apiCapabilityEndpointId,sdkOperationId,label,receiptPolicy,confirmationPolicy,optimisticPolicy);

@override
String toString() {
  return 'InterfacePaneViewInvocationActionBundle(projectionExperienceViewInvocationActionId: $projectionExperienceViewInvocationActionId, actionKey: $actionKey, actionKind: $actionKind, targetRef: $targetRef, apiCapabilityEndpointId: $apiCapabilityEndpointId, sdkOperationId: $sdkOperationId, label: $label, receiptPolicy: $receiptPolicy, confirmationPolicy: $confirmationPolicy, optimisticPolicy: $optimisticPolicy)';
}


}

/// @nodoc
abstract mixin class $InterfacePaneViewInvocationActionBundleCopyWith<$Res>  {
  factory $InterfacePaneViewInvocationActionBundleCopyWith(InterfacePaneViewInvocationActionBundle value, $Res Function(InterfacePaneViewInvocationActionBundle) _then) = _$InterfacePaneViewInvocationActionBundleCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue projectionExperienceViewInvocationActionId, String actionKey, String actionKind, String targetRef,@UuidValueConverter() UuidValue? apiCapabilityEndpointId,@UuidValueConverter() UuidValue? sdkOperationId, String? label, String? receiptPolicy, String? confirmationPolicy, String? optimisticPolicy
});




}
/// @nodoc
class _$InterfacePaneViewInvocationActionBundleCopyWithImpl<$Res>
    implements $InterfacePaneViewInvocationActionBundleCopyWith<$Res> {
  _$InterfacePaneViewInvocationActionBundleCopyWithImpl(this._self, this._then);

  final InterfacePaneViewInvocationActionBundle _self;
  final $Res Function(InterfacePaneViewInvocationActionBundle) _then;

/// Create a copy of InterfacePaneViewInvocationActionBundle
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? projectionExperienceViewInvocationActionId = null,Object? actionKey = null,Object? actionKind = null,Object? targetRef = null,Object? apiCapabilityEndpointId = freezed,Object? sdkOperationId = freezed,Object? label = freezed,Object? receiptPolicy = freezed,Object? confirmationPolicy = freezed,Object? optimisticPolicy = freezed,}) {
  return _then(_self.copyWith(
projectionExperienceViewInvocationActionId: null == projectionExperienceViewInvocationActionId ? _self.projectionExperienceViewInvocationActionId : projectionExperienceViewInvocationActionId // ignore: cast_nullable_to_non_nullable
as UuidValue,actionKey: null == actionKey ? _self.actionKey : actionKey // ignore: cast_nullable_to_non_nullable
as String,actionKind: null == actionKind ? _self.actionKind : actionKind // ignore: cast_nullable_to_non_nullable
as String,targetRef: null == targetRef ? _self.targetRef : targetRef // ignore: cast_nullable_to_non_nullable
as String,apiCapabilityEndpointId: freezed == apiCapabilityEndpointId ? _self.apiCapabilityEndpointId : apiCapabilityEndpointId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sdkOperationId: freezed == sdkOperationId ? _self.sdkOperationId : sdkOperationId // ignore: cast_nullable_to_non_nullable
as UuidValue?,label: freezed == label ? _self.label : label // ignore: cast_nullable_to_non_nullable
as String?,receiptPolicy: freezed == receiptPolicy ? _self.receiptPolicy : receiptPolicy // ignore: cast_nullable_to_non_nullable
as String?,confirmationPolicy: freezed == confirmationPolicy ? _self.confirmationPolicy : confirmationPolicy // ignore: cast_nullable_to_non_nullable
as String?,optimisticPolicy: freezed == optimisticPolicy ? _self.optimisticPolicy : optimisticPolicy // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfacePaneViewInvocationActionBundle].
extension InterfacePaneViewInvocationActionBundlePatterns on InterfacePaneViewInvocationActionBundle {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfacePaneViewInvocationActionBundle value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfacePaneViewInvocationActionBundle() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfacePaneViewInvocationActionBundle value)  def,}){
final _that = this;
switch (_that) {
case _InterfacePaneViewInvocationActionBundle():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfacePaneViewInvocationActionBundle value)?  def,}){
final _that = this;
switch (_that) {
case _InterfacePaneViewInvocationActionBundle() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue projectionExperienceViewInvocationActionId,  String actionKey,  String actionKind,  String targetRef, @UuidValueConverter()  UuidValue? apiCapabilityEndpointId, @UuidValueConverter()  UuidValue? sdkOperationId,  String? label,  String? receiptPolicy,  String? confirmationPolicy,  String? optimisticPolicy)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfacePaneViewInvocationActionBundle() when def != null:
return def(_that.projectionExperienceViewInvocationActionId,_that.actionKey,_that.actionKind,_that.targetRef,_that.apiCapabilityEndpointId,_that.sdkOperationId,_that.label,_that.receiptPolicy,_that.confirmationPolicy,_that.optimisticPolicy);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue projectionExperienceViewInvocationActionId,  String actionKey,  String actionKind,  String targetRef, @UuidValueConverter()  UuidValue? apiCapabilityEndpointId, @UuidValueConverter()  UuidValue? sdkOperationId,  String? label,  String? receiptPolicy,  String? confirmationPolicy,  String? optimisticPolicy)  def,}) {final _that = this;
switch (_that) {
case _InterfacePaneViewInvocationActionBundle():
return def(_that.projectionExperienceViewInvocationActionId,_that.actionKey,_that.actionKind,_that.targetRef,_that.apiCapabilityEndpointId,_that.sdkOperationId,_that.label,_that.receiptPolicy,_that.confirmationPolicy,_that.optimisticPolicy);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue projectionExperienceViewInvocationActionId,  String actionKey,  String actionKind,  String targetRef, @UuidValueConverter()  UuidValue? apiCapabilityEndpointId, @UuidValueConverter()  UuidValue? sdkOperationId,  String? label,  String? receiptPolicy,  String? confirmationPolicy,  String? optimisticPolicy)?  def,}) {final _that = this;
switch (_that) {
case _InterfacePaneViewInvocationActionBundle() when def != null:
return def(_that.projectionExperienceViewInvocationActionId,_that.actionKey,_that.actionKind,_that.targetRef,_that.apiCapabilityEndpointId,_that.sdkOperationId,_that.label,_that.receiptPolicy,_that.confirmationPolicy,_that.optimisticPolicy);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfacePaneViewInvocationActionBundle implements InterfacePaneViewInvocationActionBundle {
   _InterfacePaneViewInvocationActionBundle({@UuidValueConverter() required this.projectionExperienceViewInvocationActionId, required this.actionKey, required this.actionKind, required this.targetRef, @UuidValueConverter() this.apiCapabilityEndpointId, @UuidValueConverter() this.sdkOperationId, this.label, this.receiptPolicy, this.confirmationPolicy, this.optimisticPolicy});
  factory _InterfacePaneViewInvocationActionBundle.fromJson(Map<String, dynamic> json) => _$InterfacePaneViewInvocationActionBundleFromJson(json);

@override@UuidValueConverter() final  UuidValue projectionExperienceViewInvocationActionId;
@override final  String actionKey;
@override final  String actionKind;
@override final  String targetRef;
@override@UuidValueConverter() final  UuidValue? apiCapabilityEndpointId;
@override@UuidValueConverter() final  UuidValue? sdkOperationId;
@override final  String? label;
@override final  String? receiptPolicy;
@override final  String? confirmationPolicy;
@override final  String? optimisticPolicy;

/// Create a copy of InterfacePaneViewInvocationActionBundle
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfacePaneViewInvocationActionBundleCopyWith<_InterfacePaneViewInvocationActionBundle> get copyWith => __$InterfacePaneViewInvocationActionBundleCopyWithImpl<_InterfacePaneViewInvocationActionBundle>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfacePaneViewInvocationActionBundleToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfacePaneViewInvocationActionBundle&&(identical(other.projectionExperienceViewInvocationActionId, projectionExperienceViewInvocationActionId) || other.projectionExperienceViewInvocationActionId == projectionExperienceViewInvocationActionId)&&(identical(other.actionKey, actionKey) || other.actionKey == actionKey)&&(identical(other.actionKind, actionKind) || other.actionKind == actionKind)&&(identical(other.targetRef, targetRef) || other.targetRef == targetRef)&&(identical(other.apiCapabilityEndpointId, apiCapabilityEndpointId) || other.apiCapabilityEndpointId == apiCapabilityEndpointId)&&(identical(other.sdkOperationId, sdkOperationId) || other.sdkOperationId == sdkOperationId)&&(identical(other.label, label) || other.label == label)&&(identical(other.receiptPolicy, receiptPolicy) || other.receiptPolicy == receiptPolicy)&&(identical(other.confirmationPolicy, confirmationPolicy) || other.confirmationPolicy == confirmationPolicy)&&(identical(other.optimisticPolicy, optimisticPolicy) || other.optimisticPolicy == optimisticPolicy));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,projectionExperienceViewInvocationActionId,actionKey,actionKind,targetRef,apiCapabilityEndpointId,sdkOperationId,label,receiptPolicy,confirmationPolicy,optimisticPolicy);

@override
String toString() {
  return 'InterfacePaneViewInvocationActionBundle.def(projectionExperienceViewInvocationActionId: $projectionExperienceViewInvocationActionId, actionKey: $actionKey, actionKind: $actionKind, targetRef: $targetRef, apiCapabilityEndpointId: $apiCapabilityEndpointId, sdkOperationId: $sdkOperationId, label: $label, receiptPolicy: $receiptPolicy, confirmationPolicy: $confirmationPolicy, optimisticPolicy: $optimisticPolicy)';
}


}

/// @nodoc
abstract mixin class _$InterfacePaneViewInvocationActionBundleCopyWith<$Res> implements $InterfacePaneViewInvocationActionBundleCopyWith<$Res> {
  factory _$InterfacePaneViewInvocationActionBundleCopyWith(_InterfacePaneViewInvocationActionBundle value, $Res Function(_InterfacePaneViewInvocationActionBundle) _then) = __$InterfacePaneViewInvocationActionBundleCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue projectionExperienceViewInvocationActionId, String actionKey, String actionKind, String targetRef,@UuidValueConverter() UuidValue? apiCapabilityEndpointId,@UuidValueConverter() UuidValue? sdkOperationId, String? label, String? receiptPolicy, String? confirmationPolicy, String? optimisticPolicy
});




}
/// @nodoc
class __$InterfacePaneViewInvocationActionBundleCopyWithImpl<$Res>
    implements _$InterfacePaneViewInvocationActionBundleCopyWith<$Res> {
  __$InterfacePaneViewInvocationActionBundleCopyWithImpl(this._self, this._then);

  final _InterfacePaneViewInvocationActionBundle _self;
  final $Res Function(_InterfacePaneViewInvocationActionBundle) _then;

/// Create a copy of InterfacePaneViewInvocationActionBundle
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? projectionExperienceViewInvocationActionId = null,Object? actionKey = null,Object? actionKind = null,Object? targetRef = null,Object? apiCapabilityEndpointId = freezed,Object? sdkOperationId = freezed,Object? label = freezed,Object? receiptPolicy = freezed,Object? confirmationPolicy = freezed,Object? optimisticPolicy = freezed,}) {
  return _then(_InterfacePaneViewInvocationActionBundle(
projectionExperienceViewInvocationActionId: null == projectionExperienceViewInvocationActionId ? _self.projectionExperienceViewInvocationActionId : projectionExperienceViewInvocationActionId // ignore: cast_nullable_to_non_nullable
as UuidValue,actionKey: null == actionKey ? _self.actionKey : actionKey // ignore: cast_nullable_to_non_nullable
as String,actionKind: null == actionKind ? _self.actionKind : actionKind // ignore: cast_nullable_to_non_nullable
as String,targetRef: null == targetRef ? _self.targetRef : targetRef // ignore: cast_nullable_to_non_nullable
as String,apiCapabilityEndpointId: freezed == apiCapabilityEndpointId ? _self.apiCapabilityEndpointId : apiCapabilityEndpointId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sdkOperationId: freezed == sdkOperationId ? _self.sdkOperationId : sdkOperationId // ignore: cast_nullable_to_non_nullable
as UuidValue?,label: freezed == label ? _self.label : label // ignore: cast_nullable_to_non_nullable
as String?,receiptPolicy: freezed == receiptPolicy ? _self.receiptPolicy : receiptPolicy // ignore: cast_nullable_to_non_nullable
as String?,confirmationPolicy: freezed == confirmationPolicy ? _self.confirmationPolicy : confirmationPolicy // ignore: cast_nullable_to_non_nullable
as String?,optimisticPolicy: freezed == optimisticPolicy ? _self.optimisticPolicy : optimisticPolicy // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$InterfacePaneProjectionExperienceViewBundle {

@UuidValueConverter() UuidValue get bindingId;@UuidValueConverter() UuidValue get projectionExperienceViewId;@UuidValueConverter() UuidValue? get objectProjectionGraphObservableId;@UuidValueConverter() UuidValue? get projectionExperienceGraphIdentityId;@UuidValueConverter() UuidValue? get objectProjectionGraphIdentityId; String? get sectionGraphBindingKey;@UuidValueConverter() UuidValue? get stateModelId; String get viewRef; String? get projectionViewKey; bool get isDefault; List<InterfacePaneViewInvocationActionBundle> get invocationActions; List<InterfacePaneSectionMountBundle> get sectionMounts;
/// Create a copy of InterfacePaneProjectionExperienceViewBundle
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfacePaneProjectionExperienceViewBundleCopyWith<InterfacePaneProjectionExperienceViewBundle> get copyWith => _$InterfacePaneProjectionExperienceViewBundleCopyWithImpl<InterfacePaneProjectionExperienceViewBundle>(this as InterfacePaneProjectionExperienceViewBundle, _$identity);

  /// Serializes this InterfacePaneProjectionExperienceViewBundle to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfacePaneProjectionExperienceViewBundle&&(identical(other.bindingId, bindingId) || other.bindingId == bindingId)&&(identical(other.projectionExperienceViewId, projectionExperienceViewId) || other.projectionExperienceViewId == projectionExperienceViewId)&&(identical(other.objectProjectionGraphObservableId, objectProjectionGraphObservableId) || other.objectProjectionGraphObservableId == objectProjectionGraphObservableId)&&(identical(other.projectionExperienceGraphIdentityId, projectionExperienceGraphIdentityId) || other.projectionExperienceGraphIdentityId == projectionExperienceGraphIdentityId)&&(identical(other.objectProjectionGraphIdentityId, objectProjectionGraphIdentityId) || other.objectProjectionGraphIdentityId == objectProjectionGraphIdentityId)&&(identical(other.sectionGraphBindingKey, sectionGraphBindingKey) || other.sectionGraphBindingKey == sectionGraphBindingKey)&&(identical(other.stateModelId, stateModelId) || other.stateModelId == stateModelId)&&(identical(other.viewRef, viewRef) || other.viewRef == viewRef)&&(identical(other.projectionViewKey, projectionViewKey) || other.projectionViewKey == projectionViewKey)&&(identical(other.isDefault, isDefault) || other.isDefault == isDefault)&&const DeepCollectionEquality().equals(other.invocationActions, invocationActions)&&const DeepCollectionEquality().equals(other.sectionMounts, sectionMounts));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,bindingId,projectionExperienceViewId,objectProjectionGraphObservableId,projectionExperienceGraphIdentityId,objectProjectionGraphIdentityId,sectionGraphBindingKey,stateModelId,viewRef,projectionViewKey,isDefault,const DeepCollectionEquality().hash(invocationActions),const DeepCollectionEquality().hash(sectionMounts));

@override
String toString() {
  return 'InterfacePaneProjectionExperienceViewBundle(bindingId: $bindingId, projectionExperienceViewId: $projectionExperienceViewId, objectProjectionGraphObservableId: $objectProjectionGraphObservableId, projectionExperienceGraphIdentityId: $projectionExperienceGraphIdentityId, objectProjectionGraphIdentityId: $objectProjectionGraphIdentityId, sectionGraphBindingKey: $sectionGraphBindingKey, stateModelId: $stateModelId, viewRef: $viewRef, projectionViewKey: $projectionViewKey, isDefault: $isDefault, invocationActions: $invocationActions, sectionMounts: $sectionMounts)';
}


}

/// @nodoc
abstract mixin class $InterfacePaneProjectionExperienceViewBundleCopyWith<$Res>  {
  factory $InterfacePaneProjectionExperienceViewBundleCopyWith(InterfacePaneProjectionExperienceViewBundle value, $Res Function(InterfacePaneProjectionExperienceViewBundle) _then) = _$InterfacePaneProjectionExperienceViewBundleCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue bindingId,@UuidValueConverter() UuidValue projectionExperienceViewId,@UuidValueConverter() UuidValue? objectProjectionGraphObservableId,@UuidValueConverter() UuidValue? projectionExperienceGraphIdentityId,@UuidValueConverter() UuidValue? objectProjectionGraphIdentityId, String? sectionGraphBindingKey,@UuidValueConverter() UuidValue? stateModelId, String viewRef, String? projectionViewKey, bool isDefault, List<InterfacePaneViewInvocationActionBundle> invocationActions, List<InterfacePaneSectionMountBundle> sectionMounts
});




}
/// @nodoc
class _$InterfacePaneProjectionExperienceViewBundleCopyWithImpl<$Res>
    implements $InterfacePaneProjectionExperienceViewBundleCopyWith<$Res> {
  _$InterfacePaneProjectionExperienceViewBundleCopyWithImpl(this._self, this._then);

  final InterfacePaneProjectionExperienceViewBundle _self;
  final $Res Function(InterfacePaneProjectionExperienceViewBundle) _then;

/// Create a copy of InterfacePaneProjectionExperienceViewBundle
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? bindingId = null,Object? projectionExperienceViewId = null,Object? objectProjectionGraphObservableId = freezed,Object? projectionExperienceGraphIdentityId = freezed,Object? objectProjectionGraphIdentityId = freezed,Object? sectionGraphBindingKey = freezed,Object? stateModelId = freezed,Object? viewRef = null,Object? projectionViewKey = freezed,Object? isDefault = null,Object? invocationActions = null,Object? sectionMounts = null,}) {
  return _then(_self.copyWith(
bindingId: null == bindingId ? _self.bindingId : bindingId // ignore: cast_nullable_to_non_nullable
as UuidValue,projectionExperienceViewId: null == projectionExperienceViewId ? _self.projectionExperienceViewId : projectionExperienceViewId // ignore: cast_nullable_to_non_nullable
as UuidValue,objectProjectionGraphObservableId: freezed == objectProjectionGraphObservableId ? _self.objectProjectionGraphObservableId : objectProjectionGraphObservableId // ignore: cast_nullable_to_non_nullable
as UuidValue?,projectionExperienceGraphIdentityId: freezed == projectionExperienceGraphIdentityId ? _self.projectionExperienceGraphIdentityId : projectionExperienceGraphIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectProjectionGraphIdentityId: freezed == objectProjectionGraphIdentityId ? _self.objectProjectionGraphIdentityId : objectProjectionGraphIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sectionGraphBindingKey: freezed == sectionGraphBindingKey ? _self.sectionGraphBindingKey : sectionGraphBindingKey // ignore: cast_nullable_to_non_nullable
as String?,stateModelId: freezed == stateModelId ? _self.stateModelId : stateModelId // ignore: cast_nullable_to_non_nullable
as UuidValue?,viewRef: null == viewRef ? _self.viewRef : viewRef // ignore: cast_nullable_to_non_nullable
as String,projectionViewKey: freezed == projectionViewKey ? _self.projectionViewKey : projectionViewKey // ignore: cast_nullable_to_non_nullable
as String?,isDefault: null == isDefault ? _self.isDefault : isDefault // ignore: cast_nullable_to_non_nullable
as bool,invocationActions: null == invocationActions ? _self.invocationActions : invocationActions // ignore: cast_nullable_to_non_nullable
as List<InterfacePaneViewInvocationActionBundle>,sectionMounts: null == sectionMounts ? _self.sectionMounts : sectionMounts // ignore: cast_nullable_to_non_nullable
as List<InterfacePaneSectionMountBundle>,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfacePaneProjectionExperienceViewBundle].
extension InterfacePaneProjectionExperienceViewBundlePatterns on InterfacePaneProjectionExperienceViewBundle {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfacePaneProjectionExperienceViewBundle value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfacePaneProjectionExperienceViewBundle() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfacePaneProjectionExperienceViewBundle value)  def,}){
final _that = this;
switch (_that) {
case _InterfacePaneProjectionExperienceViewBundle():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfacePaneProjectionExperienceViewBundle value)?  def,}){
final _that = this;
switch (_that) {
case _InterfacePaneProjectionExperienceViewBundle() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue bindingId, @UuidValueConverter()  UuidValue projectionExperienceViewId, @UuidValueConverter()  UuidValue? objectProjectionGraphObservableId, @UuidValueConverter()  UuidValue? projectionExperienceGraphIdentityId, @UuidValueConverter()  UuidValue? objectProjectionGraphIdentityId,  String? sectionGraphBindingKey, @UuidValueConverter()  UuidValue? stateModelId,  String viewRef,  String? projectionViewKey,  bool isDefault,  List<InterfacePaneViewInvocationActionBundle> invocationActions,  List<InterfacePaneSectionMountBundle> sectionMounts)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfacePaneProjectionExperienceViewBundle() when def != null:
return def(_that.bindingId,_that.projectionExperienceViewId,_that.objectProjectionGraphObservableId,_that.projectionExperienceGraphIdentityId,_that.objectProjectionGraphIdentityId,_that.sectionGraphBindingKey,_that.stateModelId,_that.viewRef,_that.projectionViewKey,_that.isDefault,_that.invocationActions,_that.sectionMounts);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue bindingId, @UuidValueConverter()  UuidValue projectionExperienceViewId, @UuidValueConverter()  UuidValue? objectProjectionGraphObservableId, @UuidValueConverter()  UuidValue? projectionExperienceGraphIdentityId, @UuidValueConverter()  UuidValue? objectProjectionGraphIdentityId,  String? sectionGraphBindingKey, @UuidValueConverter()  UuidValue? stateModelId,  String viewRef,  String? projectionViewKey,  bool isDefault,  List<InterfacePaneViewInvocationActionBundle> invocationActions,  List<InterfacePaneSectionMountBundle> sectionMounts)  def,}) {final _that = this;
switch (_that) {
case _InterfacePaneProjectionExperienceViewBundle():
return def(_that.bindingId,_that.projectionExperienceViewId,_that.objectProjectionGraphObservableId,_that.projectionExperienceGraphIdentityId,_that.objectProjectionGraphIdentityId,_that.sectionGraphBindingKey,_that.stateModelId,_that.viewRef,_that.projectionViewKey,_that.isDefault,_that.invocationActions,_that.sectionMounts);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue bindingId, @UuidValueConverter()  UuidValue projectionExperienceViewId, @UuidValueConverter()  UuidValue? objectProjectionGraphObservableId, @UuidValueConverter()  UuidValue? projectionExperienceGraphIdentityId, @UuidValueConverter()  UuidValue? objectProjectionGraphIdentityId,  String? sectionGraphBindingKey, @UuidValueConverter()  UuidValue? stateModelId,  String viewRef,  String? projectionViewKey,  bool isDefault,  List<InterfacePaneViewInvocationActionBundle> invocationActions,  List<InterfacePaneSectionMountBundle> sectionMounts)?  def,}) {final _that = this;
switch (_that) {
case _InterfacePaneProjectionExperienceViewBundle() when def != null:
return def(_that.bindingId,_that.projectionExperienceViewId,_that.objectProjectionGraphObservableId,_that.projectionExperienceGraphIdentityId,_that.objectProjectionGraphIdentityId,_that.sectionGraphBindingKey,_that.stateModelId,_that.viewRef,_that.projectionViewKey,_that.isDefault,_that.invocationActions,_that.sectionMounts);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfacePaneProjectionExperienceViewBundle implements InterfacePaneProjectionExperienceViewBundle {
   _InterfacePaneProjectionExperienceViewBundle({@UuidValueConverter() required this.bindingId, @UuidValueConverter() required this.projectionExperienceViewId, @UuidValueConverter() this.objectProjectionGraphObservableId, @UuidValueConverter() this.projectionExperienceGraphIdentityId, @UuidValueConverter() this.objectProjectionGraphIdentityId, this.sectionGraphBindingKey, @UuidValueConverter() this.stateModelId, required this.viewRef, this.projectionViewKey, required this.isDefault, final  List<InterfacePaneViewInvocationActionBundle> invocationActions = const [], final  List<InterfacePaneSectionMountBundle> sectionMounts = const []}): _invocationActions = invocationActions,_sectionMounts = sectionMounts;
  factory _InterfacePaneProjectionExperienceViewBundle.fromJson(Map<String, dynamic> json) => _$InterfacePaneProjectionExperienceViewBundleFromJson(json);

@override@UuidValueConverter() final  UuidValue bindingId;
@override@UuidValueConverter() final  UuidValue projectionExperienceViewId;
@override@UuidValueConverter() final  UuidValue? objectProjectionGraphObservableId;
@override@UuidValueConverter() final  UuidValue? projectionExperienceGraphIdentityId;
@override@UuidValueConverter() final  UuidValue? objectProjectionGraphIdentityId;
@override final  String? sectionGraphBindingKey;
@override@UuidValueConverter() final  UuidValue? stateModelId;
@override final  String viewRef;
@override final  String? projectionViewKey;
@override final  bool isDefault;
 final  List<InterfacePaneViewInvocationActionBundle> _invocationActions;
@override@JsonKey() List<InterfacePaneViewInvocationActionBundle> get invocationActions {
  if (_invocationActions is EqualUnmodifiableListView) return _invocationActions;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_invocationActions);
}

 final  List<InterfacePaneSectionMountBundle> _sectionMounts;
@override@JsonKey() List<InterfacePaneSectionMountBundle> get sectionMounts {
  if (_sectionMounts is EqualUnmodifiableListView) return _sectionMounts;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_sectionMounts);
}


/// Create a copy of InterfacePaneProjectionExperienceViewBundle
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfacePaneProjectionExperienceViewBundleCopyWith<_InterfacePaneProjectionExperienceViewBundle> get copyWith => __$InterfacePaneProjectionExperienceViewBundleCopyWithImpl<_InterfacePaneProjectionExperienceViewBundle>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfacePaneProjectionExperienceViewBundleToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfacePaneProjectionExperienceViewBundle&&(identical(other.bindingId, bindingId) || other.bindingId == bindingId)&&(identical(other.projectionExperienceViewId, projectionExperienceViewId) || other.projectionExperienceViewId == projectionExperienceViewId)&&(identical(other.objectProjectionGraphObservableId, objectProjectionGraphObservableId) || other.objectProjectionGraphObservableId == objectProjectionGraphObservableId)&&(identical(other.projectionExperienceGraphIdentityId, projectionExperienceGraphIdentityId) || other.projectionExperienceGraphIdentityId == projectionExperienceGraphIdentityId)&&(identical(other.objectProjectionGraphIdentityId, objectProjectionGraphIdentityId) || other.objectProjectionGraphIdentityId == objectProjectionGraphIdentityId)&&(identical(other.sectionGraphBindingKey, sectionGraphBindingKey) || other.sectionGraphBindingKey == sectionGraphBindingKey)&&(identical(other.stateModelId, stateModelId) || other.stateModelId == stateModelId)&&(identical(other.viewRef, viewRef) || other.viewRef == viewRef)&&(identical(other.projectionViewKey, projectionViewKey) || other.projectionViewKey == projectionViewKey)&&(identical(other.isDefault, isDefault) || other.isDefault == isDefault)&&const DeepCollectionEquality().equals(other._invocationActions, _invocationActions)&&const DeepCollectionEquality().equals(other._sectionMounts, _sectionMounts));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,bindingId,projectionExperienceViewId,objectProjectionGraphObservableId,projectionExperienceGraphIdentityId,objectProjectionGraphIdentityId,sectionGraphBindingKey,stateModelId,viewRef,projectionViewKey,isDefault,const DeepCollectionEquality().hash(_invocationActions),const DeepCollectionEquality().hash(_sectionMounts));

@override
String toString() {
  return 'InterfacePaneProjectionExperienceViewBundle.def(bindingId: $bindingId, projectionExperienceViewId: $projectionExperienceViewId, objectProjectionGraphObservableId: $objectProjectionGraphObservableId, projectionExperienceGraphIdentityId: $projectionExperienceGraphIdentityId, objectProjectionGraphIdentityId: $objectProjectionGraphIdentityId, sectionGraphBindingKey: $sectionGraphBindingKey, stateModelId: $stateModelId, viewRef: $viewRef, projectionViewKey: $projectionViewKey, isDefault: $isDefault, invocationActions: $invocationActions, sectionMounts: $sectionMounts)';
}


}

/// @nodoc
abstract mixin class _$InterfacePaneProjectionExperienceViewBundleCopyWith<$Res> implements $InterfacePaneProjectionExperienceViewBundleCopyWith<$Res> {
  factory _$InterfacePaneProjectionExperienceViewBundleCopyWith(_InterfacePaneProjectionExperienceViewBundle value, $Res Function(_InterfacePaneProjectionExperienceViewBundle) _then) = __$InterfacePaneProjectionExperienceViewBundleCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue bindingId,@UuidValueConverter() UuidValue projectionExperienceViewId,@UuidValueConverter() UuidValue? objectProjectionGraphObservableId,@UuidValueConverter() UuidValue? projectionExperienceGraphIdentityId,@UuidValueConverter() UuidValue? objectProjectionGraphIdentityId, String? sectionGraphBindingKey,@UuidValueConverter() UuidValue? stateModelId, String viewRef, String? projectionViewKey, bool isDefault, List<InterfacePaneViewInvocationActionBundle> invocationActions, List<InterfacePaneSectionMountBundle> sectionMounts
});




}
/// @nodoc
class __$InterfacePaneProjectionExperienceViewBundleCopyWithImpl<$Res>
    implements _$InterfacePaneProjectionExperienceViewBundleCopyWith<$Res> {
  __$InterfacePaneProjectionExperienceViewBundleCopyWithImpl(this._self, this._then);

  final _InterfacePaneProjectionExperienceViewBundle _self;
  final $Res Function(_InterfacePaneProjectionExperienceViewBundle) _then;

/// Create a copy of InterfacePaneProjectionExperienceViewBundle
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? bindingId = null,Object? projectionExperienceViewId = null,Object? objectProjectionGraphObservableId = freezed,Object? projectionExperienceGraphIdentityId = freezed,Object? objectProjectionGraphIdentityId = freezed,Object? sectionGraphBindingKey = freezed,Object? stateModelId = freezed,Object? viewRef = null,Object? projectionViewKey = freezed,Object? isDefault = null,Object? invocationActions = null,Object? sectionMounts = null,}) {
  return _then(_InterfacePaneProjectionExperienceViewBundle(
bindingId: null == bindingId ? _self.bindingId : bindingId // ignore: cast_nullable_to_non_nullable
as UuidValue,projectionExperienceViewId: null == projectionExperienceViewId ? _self.projectionExperienceViewId : projectionExperienceViewId // ignore: cast_nullable_to_non_nullable
as UuidValue,objectProjectionGraphObservableId: freezed == objectProjectionGraphObservableId ? _self.objectProjectionGraphObservableId : objectProjectionGraphObservableId // ignore: cast_nullable_to_non_nullable
as UuidValue?,projectionExperienceGraphIdentityId: freezed == projectionExperienceGraphIdentityId ? _self.projectionExperienceGraphIdentityId : projectionExperienceGraphIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectProjectionGraphIdentityId: freezed == objectProjectionGraphIdentityId ? _self.objectProjectionGraphIdentityId : objectProjectionGraphIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sectionGraphBindingKey: freezed == sectionGraphBindingKey ? _self.sectionGraphBindingKey : sectionGraphBindingKey // ignore: cast_nullable_to_non_nullable
as String?,stateModelId: freezed == stateModelId ? _self.stateModelId : stateModelId // ignore: cast_nullable_to_non_nullable
as UuidValue?,viewRef: null == viewRef ? _self.viewRef : viewRef // ignore: cast_nullable_to_non_nullable
as String,projectionViewKey: freezed == projectionViewKey ? _self.projectionViewKey : projectionViewKey // ignore: cast_nullable_to_non_nullable
as String?,isDefault: null == isDefault ? _self.isDefault : isDefault // ignore: cast_nullable_to_non_nullable
as bool,invocationActions: null == invocationActions ? _self._invocationActions : invocationActions // ignore: cast_nullable_to_non_nullable
as List<InterfacePaneViewInvocationActionBundle>,sectionMounts: null == sectionMounts ? _self._sectionMounts : sectionMounts // ignore: cast_nullable_to_non_nullable
as List<InterfacePaneSectionMountBundle>,
  ));
}


}


/// @nodoc
mixin _$InterfacePaneApiCapabilityEndpointBundle {

@UuidValueConverter() UuidValue get bindingId;@UuidValueConverter() UuidValue get apiCapabilityEndpointId; String? get endpointRef; String? get discriminant;
/// Create a copy of InterfacePaneApiCapabilityEndpointBundle
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfacePaneApiCapabilityEndpointBundleCopyWith<InterfacePaneApiCapabilityEndpointBundle> get copyWith => _$InterfacePaneApiCapabilityEndpointBundleCopyWithImpl<InterfacePaneApiCapabilityEndpointBundle>(this as InterfacePaneApiCapabilityEndpointBundle, _$identity);

  /// Serializes this InterfacePaneApiCapabilityEndpointBundle to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfacePaneApiCapabilityEndpointBundle&&(identical(other.bindingId, bindingId) || other.bindingId == bindingId)&&(identical(other.apiCapabilityEndpointId, apiCapabilityEndpointId) || other.apiCapabilityEndpointId == apiCapabilityEndpointId)&&(identical(other.endpointRef, endpointRef) || other.endpointRef == endpointRef)&&(identical(other.discriminant, discriminant) || other.discriminant == discriminant));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,bindingId,apiCapabilityEndpointId,endpointRef,discriminant);

@override
String toString() {
  return 'InterfacePaneApiCapabilityEndpointBundle(bindingId: $bindingId, apiCapabilityEndpointId: $apiCapabilityEndpointId, endpointRef: $endpointRef, discriminant: $discriminant)';
}


}

/// @nodoc
abstract mixin class $InterfacePaneApiCapabilityEndpointBundleCopyWith<$Res>  {
  factory $InterfacePaneApiCapabilityEndpointBundleCopyWith(InterfacePaneApiCapabilityEndpointBundle value, $Res Function(InterfacePaneApiCapabilityEndpointBundle) _then) = _$InterfacePaneApiCapabilityEndpointBundleCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue bindingId,@UuidValueConverter() UuidValue apiCapabilityEndpointId, String? endpointRef, String? discriminant
});




}
/// @nodoc
class _$InterfacePaneApiCapabilityEndpointBundleCopyWithImpl<$Res>
    implements $InterfacePaneApiCapabilityEndpointBundleCopyWith<$Res> {
  _$InterfacePaneApiCapabilityEndpointBundleCopyWithImpl(this._self, this._then);

  final InterfacePaneApiCapabilityEndpointBundle _self;
  final $Res Function(InterfacePaneApiCapabilityEndpointBundle) _then;

/// Create a copy of InterfacePaneApiCapabilityEndpointBundle
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? bindingId = null,Object? apiCapabilityEndpointId = null,Object? endpointRef = freezed,Object? discriminant = freezed,}) {
  return _then(_self.copyWith(
bindingId: null == bindingId ? _self.bindingId : bindingId // ignore: cast_nullable_to_non_nullable
as UuidValue,apiCapabilityEndpointId: null == apiCapabilityEndpointId ? _self.apiCapabilityEndpointId : apiCapabilityEndpointId // ignore: cast_nullable_to_non_nullable
as UuidValue,endpointRef: freezed == endpointRef ? _self.endpointRef : endpointRef // ignore: cast_nullable_to_non_nullable
as String?,discriminant: freezed == discriminant ? _self.discriminant : discriminant // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfacePaneApiCapabilityEndpointBundle].
extension InterfacePaneApiCapabilityEndpointBundlePatterns on InterfacePaneApiCapabilityEndpointBundle {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfacePaneApiCapabilityEndpointBundle value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfacePaneApiCapabilityEndpointBundle() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfacePaneApiCapabilityEndpointBundle value)  def,}){
final _that = this;
switch (_that) {
case _InterfacePaneApiCapabilityEndpointBundle():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfacePaneApiCapabilityEndpointBundle value)?  def,}){
final _that = this;
switch (_that) {
case _InterfacePaneApiCapabilityEndpointBundle() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue bindingId, @UuidValueConverter()  UuidValue apiCapabilityEndpointId,  String? endpointRef,  String? discriminant)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfacePaneApiCapabilityEndpointBundle() when def != null:
return def(_that.bindingId,_that.apiCapabilityEndpointId,_that.endpointRef,_that.discriminant);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue bindingId, @UuidValueConverter()  UuidValue apiCapabilityEndpointId,  String? endpointRef,  String? discriminant)  def,}) {final _that = this;
switch (_that) {
case _InterfacePaneApiCapabilityEndpointBundle():
return def(_that.bindingId,_that.apiCapabilityEndpointId,_that.endpointRef,_that.discriminant);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue bindingId, @UuidValueConverter()  UuidValue apiCapabilityEndpointId,  String? endpointRef,  String? discriminant)?  def,}) {final _that = this;
switch (_that) {
case _InterfacePaneApiCapabilityEndpointBundle() when def != null:
return def(_that.bindingId,_that.apiCapabilityEndpointId,_that.endpointRef,_that.discriminant);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfacePaneApiCapabilityEndpointBundle implements InterfacePaneApiCapabilityEndpointBundle {
   _InterfacePaneApiCapabilityEndpointBundle({@UuidValueConverter() required this.bindingId, @UuidValueConverter() required this.apiCapabilityEndpointId, this.endpointRef, this.discriminant});
  factory _InterfacePaneApiCapabilityEndpointBundle.fromJson(Map<String, dynamic> json) => _$InterfacePaneApiCapabilityEndpointBundleFromJson(json);

@override@UuidValueConverter() final  UuidValue bindingId;
@override@UuidValueConverter() final  UuidValue apiCapabilityEndpointId;
@override final  String? endpointRef;
@override final  String? discriminant;

/// Create a copy of InterfacePaneApiCapabilityEndpointBundle
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfacePaneApiCapabilityEndpointBundleCopyWith<_InterfacePaneApiCapabilityEndpointBundle> get copyWith => __$InterfacePaneApiCapabilityEndpointBundleCopyWithImpl<_InterfacePaneApiCapabilityEndpointBundle>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfacePaneApiCapabilityEndpointBundleToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfacePaneApiCapabilityEndpointBundle&&(identical(other.bindingId, bindingId) || other.bindingId == bindingId)&&(identical(other.apiCapabilityEndpointId, apiCapabilityEndpointId) || other.apiCapabilityEndpointId == apiCapabilityEndpointId)&&(identical(other.endpointRef, endpointRef) || other.endpointRef == endpointRef)&&(identical(other.discriminant, discriminant) || other.discriminant == discriminant));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,bindingId,apiCapabilityEndpointId,endpointRef,discriminant);

@override
String toString() {
  return 'InterfacePaneApiCapabilityEndpointBundle.def(bindingId: $bindingId, apiCapabilityEndpointId: $apiCapabilityEndpointId, endpointRef: $endpointRef, discriminant: $discriminant)';
}


}

/// @nodoc
abstract mixin class _$InterfacePaneApiCapabilityEndpointBundleCopyWith<$Res> implements $InterfacePaneApiCapabilityEndpointBundleCopyWith<$Res> {
  factory _$InterfacePaneApiCapabilityEndpointBundleCopyWith(_InterfacePaneApiCapabilityEndpointBundle value, $Res Function(_InterfacePaneApiCapabilityEndpointBundle) _then) = __$InterfacePaneApiCapabilityEndpointBundleCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue bindingId,@UuidValueConverter() UuidValue apiCapabilityEndpointId, String? endpointRef, String? discriminant
});




}
/// @nodoc
class __$InterfacePaneApiCapabilityEndpointBundleCopyWithImpl<$Res>
    implements _$InterfacePaneApiCapabilityEndpointBundleCopyWith<$Res> {
  __$InterfacePaneApiCapabilityEndpointBundleCopyWithImpl(this._self, this._then);

  final _InterfacePaneApiCapabilityEndpointBundle _self;
  final $Res Function(_InterfacePaneApiCapabilityEndpointBundle) _then;

/// Create a copy of InterfacePaneApiCapabilityEndpointBundle
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? bindingId = null,Object? apiCapabilityEndpointId = null,Object? endpointRef = freezed,Object? discriminant = freezed,}) {
  return _then(_InterfacePaneApiCapabilityEndpointBundle(
bindingId: null == bindingId ? _self.bindingId : bindingId // ignore: cast_nullable_to_non_nullable
as UuidValue,apiCapabilityEndpointId: null == apiCapabilityEndpointId ? _self.apiCapabilityEndpointId : apiCapabilityEndpointId // ignore: cast_nullable_to_non_nullable
as UuidValue,endpointRef: freezed == endpointRef ? _self.endpointRef : endpointRef // ignore: cast_nullable_to_non_nullable
as String?,discriminant: freezed == discriminant ? _self.discriminant : discriminant // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$InterfacePaneSdkOperationBundle {

@UuidValueConverter() UuidValue get bindingId;@UuidValueConverter() UuidValue get sdkOperationId; String? get operationRef; String? get discriminant;
/// Create a copy of InterfacePaneSdkOperationBundle
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfacePaneSdkOperationBundleCopyWith<InterfacePaneSdkOperationBundle> get copyWith => _$InterfacePaneSdkOperationBundleCopyWithImpl<InterfacePaneSdkOperationBundle>(this as InterfacePaneSdkOperationBundle, _$identity);

  /// Serializes this InterfacePaneSdkOperationBundle to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfacePaneSdkOperationBundle&&(identical(other.bindingId, bindingId) || other.bindingId == bindingId)&&(identical(other.sdkOperationId, sdkOperationId) || other.sdkOperationId == sdkOperationId)&&(identical(other.operationRef, operationRef) || other.operationRef == operationRef)&&(identical(other.discriminant, discriminant) || other.discriminant == discriminant));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,bindingId,sdkOperationId,operationRef,discriminant);

@override
String toString() {
  return 'InterfacePaneSdkOperationBundle(bindingId: $bindingId, sdkOperationId: $sdkOperationId, operationRef: $operationRef, discriminant: $discriminant)';
}


}

/// @nodoc
abstract mixin class $InterfacePaneSdkOperationBundleCopyWith<$Res>  {
  factory $InterfacePaneSdkOperationBundleCopyWith(InterfacePaneSdkOperationBundle value, $Res Function(InterfacePaneSdkOperationBundle) _then) = _$InterfacePaneSdkOperationBundleCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue bindingId,@UuidValueConverter() UuidValue sdkOperationId, String? operationRef, String? discriminant
});




}
/// @nodoc
class _$InterfacePaneSdkOperationBundleCopyWithImpl<$Res>
    implements $InterfacePaneSdkOperationBundleCopyWith<$Res> {
  _$InterfacePaneSdkOperationBundleCopyWithImpl(this._self, this._then);

  final InterfacePaneSdkOperationBundle _self;
  final $Res Function(InterfacePaneSdkOperationBundle) _then;

/// Create a copy of InterfacePaneSdkOperationBundle
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? bindingId = null,Object? sdkOperationId = null,Object? operationRef = freezed,Object? discriminant = freezed,}) {
  return _then(_self.copyWith(
bindingId: null == bindingId ? _self.bindingId : bindingId // ignore: cast_nullable_to_non_nullable
as UuidValue,sdkOperationId: null == sdkOperationId ? _self.sdkOperationId : sdkOperationId // ignore: cast_nullable_to_non_nullable
as UuidValue,operationRef: freezed == operationRef ? _self.operationRef : operationRef // ignore: cast_nullable_to_non_nullable
as String?,discriminant: freezed == discriminant ? _self.discriminant : discriminant // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfacePaneSdkOperationBundle].
extension InterfacePaneSdkOperationBundlePatterns on InterfacePaneSdkOperationBundle {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfacePaneSdkOperationBundle value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfacePaneSdkOperationBundle() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfacePaneSdkOperationBundle value)  def,}){
final _that = this;
switch (_that) {
case _InterfacePaneSdkOperationBundle():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfacePaneSdkOperationBundle value)?  def,}){
final _that = this;
switch (_that) {
case _InterfacePaneSdkOperationBundle() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue bindingId, @UuidValueConverter()  UuidValue sdkOperationId,  String? operationRef,  String? discriminant)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfacePaneSdkOperationBundle() when def != null:
return def(_that.bindingId,_that.sdkOperationId,_that.operationRef,_that.discriminant);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue bindingId, @UuidValueConverter()  UuidValue sdkOperationId,  String? operationRef,  String? discriminant)  def,}) {final _that = this;
switch (_that) {
case _InterfacePaneSdkOperationBundle():
return def(_that.bindingId,_that.sdkOperationId,_that.operationRef,_that.discriminant);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue bindingId, @UuidValueConverter()  UuidValue sdkOperationId,  String? operationRef,  String? discriminant)?  def,}) {final _that = this;
switch (_that) {
case _InterfacePaneSdkOperationBundle() when def != null:
return def(_that.bindingId,_that.sdkOperationId,_that.operationRef,_that.discriminant);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfacePaneSdkOperationBundle implements InterfacePaneSdkOperationBundle {
   _InterfacePaneSdkOperationBundle({@UuidValueConverter() required this.bindingId, @UuidValueConverter() required this.sdkOperationId, this.operationRef, this.discriminant});
  factory _InterfacePaneSdkOperationBundle.fromJson(Map<String, dynamic> json) => _$InterfacePaneSdkOperationBundleFromJson(json);

@override@UuidValueConverter() final  UuidValue bindingId;
@override@UuidValueConverter() final  UuidValue sdkOperationId;
@override final  String? operationRef;
@override final  String? discriminant;

/// Create a copy of InterfacePaneSdkOperationBundle
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfacePaneSdkOperationBundleCopyWith<_InterfacePaneSdkOperationBundle> get copyWith => __$InterfacePaneSdkOperationBundleCopyWithImpl<_InterfacePaneSdkOperationBundle>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfacePaneSdkOperationBundleToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfacePaneSdkOperationBundle&&(identical(other.bindingId, bindingId) || other.bindingId == bindingId)&&(identical(other.sdkOperationId, sdkOperationId) || other.sdkOperationId == sdkOperationId)&&(identical(other.operationRef, operationRef) || other.operationRef == operationRef)&&(identical(other.discriminant, discriminant) || other.discriminant == discriminant));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,bindingId,sdkOperationId,operationRef,discriminant);

@override
String toString() {
  return 'InterfacePaneSdkOperationBundle.def(bindingId: $bindingId, sdkOperationId: $sdkOperationId, operationRef: $operationRef, discriminant: $discriminant)';
}


}

/// @nodoc
abstract mixin class _$InterfacePaneSdkOperationBundleCopyWith<$Res> implements $InterfacePaneSdkOperationBundleCopyWith<$Res> {
  factory _$InterfacePaneSdkOperationBundleCopyWith(_InterfacePaneSdkOperationBundle value, $Res Function(_InterfacePaneSdkOperationBundle) _then) = __$InterfacePaneSdkOperationBundleCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue bindingId,@UuidValueConverter() UuidValue sdkOperationId, String? operationRef, String? discriminant
});




}
/// @nodoc
class __$InterfacePaneSdkOperationBundleCopyWithImpl<$Res>
    implements _$InterfacePaneSdkOperationBundleCopyWith<$Res> {
  __$InterfacePaneSdkOperationBundleCopyWithImpl(this._self, this._then);

  final _InterfacePaneSdkOperationBundle _self;
  final $Res Function(_InterfacePaneSdkOperationBundle) _then;

/// Create a copy of InterfacePaneSdkOperationBundle
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? bindingId = null,Object? sdkOperationId = null,Object? operationRef = freezed,Object? discriminant = freezed,}) {
  return _then(_InterfacePaneSdkOperationBundle(
bindingId: null == bindingId ? _self.bindingId : bindingId // ignore: cast_nullable_to_non_nullable
as UuidValue,sdkOperationId: null == sdkOperationId ? _self.sdkOperationId : sdkOperationId // ignore: cast_nullable_to_non_nullable
as UuidValue,operationRef: freezed == operationRef ? _self.operationRef : operationRef // ignore: cast_nullable_to_non_nullable
as String?,discriminant: freezed == discriminant ? _self.discriminant : discriminant // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$InterfacePaneConfigBundle {

@UuidValueConverter() UuidValue get paneConfigId;@UuidValueConverter() UuidValue? get panePackageId; String? get panePackageName; String get name; String get paneKind; String? get description; String? get narrativeKey; List<InterfacePaneProjectionExperienceViewBundle> get projectionExperienceViews; List<InterfacePaneApiCapabilityEndpointBundle> get apiCapabilityEndpoints; List<InterfacePaneSdkOperationBundle> get sdkOperations;
/// Create a copy of InterfacePaneConfigBundle
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfacePaneConfigBundleCopyWith<InterfacePaneConfigBundle> get copyWith => _$InterfacePaneConfigBundleCopyWithImpl<InterfacePaneConfigBundle>(this as InterfacePaneConfigBundle, _$identity);

  /// Serializes this InterfacePaneConfigBundle to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfacePaneConfigBundle&&(identical(other.paneConfigId, paneConfigId) || other.paneConfigId == paneConfigId)&&(identical(other.panePackageId, panePackageId) || other.panePackageId == panePackageId)&&(identical(other.panePackageName, panePackageName) || other.panePackageName == panePackageName)&&(identical(other.name, name) || other.name == name)&&(identical(other.paneKind, paneKind) || other.paneKind == paneKind)&&(identical(other.description, description) || other.description == description)&&(identical(other.narrativeKey, narrativeKey) || other.narrativeKey == narrativeKey)&&const DeepCollectionEquality().equals(other.projectionExperienceViews, projectionExperienceViews)&&const DeepCollectionEquality().equals(other.apiCapabilityEndpoints, apiCapabilityEndpoints)&&const DeepCollectionEquality().equals(other.sdkOperations, sdkOperations));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,paneConfigId,panePackageId,panePackageName,name,paneKind,description,narrativeKey,const DeepCollectionEquality().hash(projectionExperienceViews),const DeepCollectionEquality().hash(apiCapabilityEndpoints),const DeepCollectionEquality().hash(sdkOperations));

@override
String toString() {
  return 'InterfacePaneConfigBundle(paneConfigId: $paneConfigId, panePackageId: $panePackageId, panePackageName: $panePackageName, name: $name, paneKind: $paneKind, description: $description, narrativeKey: $narrativeKey, projectionExperienceViews: $projectionExperienceViews, apiCapabilityEndpoints: $apiCapabilityEndpoints, sdkOperations: $sdkOperations)';
}


}

/// @nodoc
abstract mixin class $InterfacePaneConfigBundleCopyWith<$Res>  {
  factory $InterfacePaneConfigBundleCopyWith(InterfacePaneConfigBundle value, $Res Function(InterfacePaneConfigBundle) _then) = _$InterfacePaneConfigBundleCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue paneConfigId,@UuidValueConverter() UuidValue? panePackageId, String? panePackageName, String name, String paneKind, String? description, String? narrativeKey, List<InterfacePaneProjectionExperienceViewBundle> projectionExperienceViews, List<InterfacePaneApiCapabilityEndpointBundle> apiCapabilityEndpoints, List<InterfacePaneSdkOperationBundle> sdkOperations
});




}
/// @nodoc
class _$InterfacePaneConfigBundleCopyWithImpl<$Res>
    implements $InterfacePaneConfigBundleCopyWith<$Res> {
  _$InterfacePaneConfigBundleCopyWithImpl(this._self, this._then);

  final InterfacePaneConfigBundle _self;
  final $Res Function(InterfacePaneConfigBundle) _then;

/// Create a copy of InterfacePaneConfigBundle
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? paneConfigId = null,Object? panePackageId = freezed,Object? panePackageName = freezed,Object? name = null,Object? paneKind = null,Object? description = freezed,Object? narrativeKey = freezed,Object? projectionExperienceViews = null,Object? apiCapabilityEndpoints = null,Object? sdkOperations = null,}) {
  return _then(_self.copyWith(
paneConfigId: null == paneConfigId ? _self.paneConfigId : paneConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,panePackageId: freezed == panePackageId ? _self.panePackageId : panePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,panePackageName: freezed == panePackageName ? _self.panePackageName : panePackageName // ignore: cast_nullable_to_non_nullable
as String?,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,paneKind: null == paneKind ? _self.paneKind : paneKind // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,narrativeKey: freezed == narrativeKey ? _self.narrativeKey : narrativeKey // ignore: cast_nullable_to_non_nullable
as String?,projectionExperienceViews: null == projectionExperienceViews ? _self.projectionExperienceViews : projectionExperienceViews // ignore: cast_nullable_to_non_nullable
as List<InterfacePaneProjectionExperienceViewBundle>,apiCapabilityEndpoints: null == apiCapabilityEndpoints ? _self.apiCapabilityEndpoints : apiCapabilityEndpoints // ignore: cast_nullable_to_non_nullable
as List<InterfacePaneApiCapabilityEndpointBundle>,sdkOperations: null == sdkOperations ? _self.sdkOperations : sdkOperations // ignore: cast_nullable_to_non_nullable
as List<InterfacePaneSdkOperationBundle>,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfacePaneConfigBundle].
extension InterfacePaneConfigBundlePatterns on InterfacePaneConfigBundle {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfacePaneConfigBundle value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfacePaneConfigBundle() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfacePaneConfigBundle value)  def,}){
final _that = this;
switch (_that) {
case _InterfacePaneConfigBundle():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfacePaneConfigBundle value)?  def,}){
final _that = this;
switch (_that) {
case _InterfacePaneConfigBundle() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue paneConfigId, @UuidValueConverter()  UuidValue? panePackageId,  String? panePackageName,  String name,  String paneKind,  String? description,  String? narrativeKey,  List<InterfacePaneProjectionExperienceViewBundle> projectionExperienceViews,  List<InterfacePaneApiCapabilityEndpointBundle> apiCapabilityEndpoints,  List<InterfacePaneSdkOperationBundle> sdkOperations)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfacePaneConfigBundle() when def != null:
return def(_that.paneConfigId,_that.panePackageId,_that.panePackageName,_that.name,_that.paneKind,_that.description,_that.narrativeKey,_that.projectionExperienceViews,_that.apiCapabilityEndpoints,_that.sdkOperations);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue paneConfigId, @UuidValueConverter()  UuidValue? panePackageId,  String? panePackageName,  String name,  String paneKind,  String? description,  String? narrativeKey,  List<InterfacePaneProjectionExperienceViewBundle> projectionExperienceViews,  List<InterfacePaneApiCapabilityEndpointBundle> apiCapabilityEndpoints,  List<InterfacePaneSdkOperationBundle> sdkOperations)  def,}) {final _that = this;
switch (_that) {
case _InterfacePaneConfigBundle():
return def(_that.paneConfigId,_that.panePackageId,_that.panePackageName,_that.name,_that.paneKind,_that.description,_that.narrativeKey,_that.projectionExperienceViews,_that.apiCapabilityEndpoints,_that.sdkOperations);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue paneConfigId, @UuidValueConverter()  UuidValue? panePackageId,  String? panePackageName,  String name,  String paneKind,  String? description,  String? narrativeKey,  List<InterfacePaneProjectionExperienceViewBundle> projectionExperienceViews,  List<InterfacePaneApiCapabilityEndpointBundle> apiCapabilityEndpoints,  List<InterfacePaneSdkOperationBundle> sdkOperations)?  def,}) {final _that = this;
switch (_that) {
case _InterfacePaneConfigBundle() when def != null:
return def(_that.paneConfigId,_that.panePackageId,_that.panePackageName,_that.name,_that.paneKind,_that.description,_that.narrativeKey,_that.projectionExperienceViews,_that.apiCapabilityEndpoints,_that.sdkOperations);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfacePaneConfigBundle implements InterfacePaneConfigBundle {
   _InterfacePaneConfigBundle({@UuidValueConverter() required this.paneConfigId, @UuidValueConverter() this.panePackageId, this.panePackageName, required this.name, required this.paneKind, this.description, this.narrativeKey, final  List<InterfacePaneProjectionExperienceViewBundle> projectionExperienceViews = const [], final  List<InterfacePaneApiCapabilityEndpointBundle> apiCapabilityEndpoints = const [], final  List<InterfacePaneSdkOperationBundle> sdkOperations = const []}): _projectionExperienceViews = projectionExperienceViews,_apiCapabilityEndpoints = apiCapabilityEndpoints,_sdkOperations = sdkOperations;
  factory _InterfacePaneConfigBundle.fromJson(Map<String, dynamic> json) => _$InterfacePaneConfigBundleFromJson(json);

@override@UuidValueConverter() final  UuidValue paneConfigId;
@override@UuidValueConverter() final  UuidValue? panePackageId;
@override final  String? panePackageName;
@override final  String name;
@override final  String paneKind;
@override final  String? description;
@override final  String? narrativeKey;
 final  List<InterfacePaneProjectionExperienceViewBundle> _projectionExperienceViews;
@override@JsonKey() List<InterfacePaneProjectionExperienceViewBundle> get projectionExperienceViews {
  if (_projectionExperienceViews is EqualUnmodifiableListView) return _projectionExperienceViews;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_projectionExperienceViews);
}

 final  List<InterfacePaneApiCapabilityEndpointBundle> _apiCapabilityEndpoints;
@override@JsonKey() List<InterfacePaneApiCapabilityEndpointBundle> get apiCapabilityEndpoints {
  if (_apiCapabilityEndpoints is EqualUnmodifiableListView) return _apiCapabilityEndpoints;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_apiCapabilityEndpoints);
}

 final  List<InterfacePaneSdkOperationBundle> _sdkOperations;
@override@JsonKey() List<InterfacePaneSdkOperationBundle> get sdkOperations {
  if (_sdkOperations is EqualUnmodifiableListView) return _sdkOperations;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_sdkOperations);
}


/// Create a copy of InterfacePaneConfigBundle
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfacePaneConfigBundleCopyWith<_InterfacePaneConfigBundle> get copyWith => __$InterfacePaneConfigBundleCopyWithImpl<_InterfacePaneConfigBundle>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfacePaneConfigBundleToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfacePaneConfigBundle&&(identical(other.paneConfigId, paneConfigId) || other.paneConfigId == paneConfigId)&&(identical(other.panePackageId, panePackageId) || other.panePackageId == panePackageId)&&(identical(other.panePackageName, panePackageName) || other.panePackageName == panePackageName)&&(identical(other.name, name) || other.name == name)&&(identical(other.paneKind, paneKind) || other.paneKind == paneKind)&&(identical(other.description, description) || other.description == description)&&(identical(other.narrativeKey, narrativeKey) || other.narrativeKey == narrativeKey)&&const DeepCollectionEquality().equals(other._projectionExperienceViews, _projectionExperienceViews)&&const DeepCollectionEquality().equals(other._apiCapabilityEndpoints, _apiCapabilityEndpoints)&&const DeepCollectionEquality().equals(other._sdkOperations, _sdkOperations));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,paneConfigId,panePackageId,panePackageName,name,paneKind,description,narrativeKey,const DeepCollectionEquality().hash(_projectionExperienceViews),const DeepCollectionEquality().hash(_apiCapabilityEndpoints),const DeepCollectionEquality().hash(_sdkOperations));

@override
String toString() {
  return 'InterfacePaneConfigBundle.def(paneConfigId: $paneConfigId, panePackageId: $panePackageId, panePackageName: $panePackageName, name: $name, paneKind: $paneKind, description: $description, narrativeKey: $narrativeKey, projectionExperienceViews: $projectionExperienceViews, apiCapabilityEndpoints: $apiCapabilityEndpoints, sdkOperations: $sdkOperations)';
}


}

/// @nodoc
abstract mixin class _$InterfacePaneConfigBundleCopyWith<$Res> implements $InterfacePaneConfigBundleCopyWith<$Res> {
  factory _$InterfacePaneConfigBundleCopyWith(_InterfacePaneConfigBundle value, $Res Function(_InterfacePaneConfigBundle) _then) = __$InterfacePaneConfigBundleCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue paneConfigId,@UuidValueConverter() UuidValue? panePackageId, String? panePackageName, String name, String paneKind, String? description, String? narrativeKey, List<InterfacePaneProjectionExperienceViewBundle> projectionExperienceViews, List<InterfacePaneApiCapabilityEndpointBundle> apiCapabilityEndpoints, List<InterfacePaneSdkOperationBundle> sdkOperations
});




}
/// @nodoc
class __$InterfacePaneConfigBundleCopyWithImpl<$Res>
    implements _$InterfacePaneConfigBundleCopyWith<$Res> {
  __$InterfacePaneConfigBundleCopyWithImpl(this._self, this._then);

  final _InterfacePaneConfigBundle _self;
  final $Res Function(_InterfacePaneConfigBundle) _then;

/// Create a copy of InterfacePaneConfigBundle
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? paneConfigId = null,Object? panePackageId = freezed,Object? panePackageName = freezed,Object? name = null,Object? paneKind = null,Object? description = freezed,Object? narrativeKey = freezed,Object? projectionExperienceViews = null,Object? apiCapabilityEndpoints = null,Object? sdkOperations = null,}) {
  return _then(_InterfacePaneConfigBundle(
paneConfigId: null == paneConfigId ? _self.paneConfigId : paneConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,panePackageId: freezed == panePackageId ? _self.panePackageId : panePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,panePackageName: freezed == panePackageName ? _self.panePackageName : panePackageName // ignore: cast_nullable_to_non_nullable
as String?,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,paneKind: null == paneKind ? _self.paneKind : paneKind // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,narrativeKey: freezed == narrativeKey ? _self.narrativeKey : narrativeKey // ignore: cast_nullable_to_non_nullable
as String?,projectionExperienceViews: null == projectionExperienceViews ? _self._projectionExperienceViews : projectionExperienceViews // ignore: cast_nullable_to_non_nullable
as List<InterfacePaneProjectionExperienceViewBundle>,apiCapabilityEndpoints: null == apiCapabilityEndpoints ? _self._apiCapabilityEndpoints : apiCapabilityEndpoints // ignore: cast_nullable_to_non_nullable
as List<InterfacePaneApiCapabilityEndpointBundle>,sdkOperations: null == sdkOperations ? _self._sdkOperations : sdkOperations // ignore: cast_nullable_to_non_nullable
as List<InterfacePaneSdkOperationBundle>,
  ));
}


}


/// @nodoc
mixin _$InterfaceConfigBundle {

@UuidValueConverter() UuidValue get interfacePackageId; String get interfacePackageName;@UuidValueConverter() UuidValue get interfaceConfigId; String get name; String? get description; List<InterfaceConfigApiBundle> get apis; List<InterfaceWindowConfigBundle> get windowConfigs; List<InterfacePaneConfigBundle> get paneConfigs;
/// Create a copy of InterfaceConfigBundle
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceConfigBundleCopyWith<InterfaceConfigBundle> get copyWith => _$InterfaceConfigBundleCopyWithImpl<InterfaceConfigBundle>(this as InterfaceConfigBundle, _$identity);

  /// Serializes this InterfaceConfigBundle to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceConfigBundle&&(identical(other.interfacePackageId, interfacePackageId) || other.interfacePackageId == interfacePackageId)&&(identical(other.interfacePackageName, interfacePackageName) || other.interfacePackageName == interfacePackageName)&&(identical(other.interfaceConfigId, interfaceConfigId) || other.interfaceConfigId == interfaceConfigId)&&(identical(other.name, name) || other.name == name)&&(identical(other.description, description) || other.description == description)&&const DeepCollectionEquality().equals(other.apis, apis)&&const DeepCollectionEquality().equals(other.windowConfigs, windowConfigs)&&const DeepCollectionEquality().equals(other.paneConfigs, paneConfigs));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,interfacePackageId,interfacePackageName,interfaceConfigId,name,description,const DeepCollectionEquality().hash(apis),const DeepCollectionEquality().hash(windowConfigs),const DeepCollectionEquality().hash(paneConfigs));

@override
String toString() {
  return 'InterfaceConfigBundle(interfacePackageId: $interfacePackageId, interfacePackageName: $interfacePackageName, interfaceConfigId: $interfaceConfigId, name: $name, description: $description, apis: $apis, windowConfigs: $windowConfigs, paneConfigs: $paneConfigs)';
}


}

/// @nodoc
abstract mixin class $InterfaceConfigBundleCopyWith<$Res>  {
  factory $InterfaceConfigBundleCopyWith(InterfaceConfigBundle value, $Res Function(InterfaceConfigBundle) _then) = _$InterfaceConfigBundleCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue interfacePackageId, String interfacePackageName,@UuidValueConverter() UuidValue interfaceConfigId, String name, String? description, List<InterfaceConfigApiBundle> apis, List<InterfaceWindowConfigBundle> windowConfigs, List<InterfacePaneConfigBundle> paneConfigs
});




}
/// @nodoc
class _$InterfaceConfigBundleCopyWithImpl<$Res>
    implements $InterfaceConfigBundleCopyWith<$Res> {
  _$InterfaceConfigBundleCopyWithImpl(this._self, this._then);

  final InterfaceConfigBundle _self;
  final $Res Function(InterfaceConfigBundle) _then;

/// Create a copy of InterfaceConfigBundle
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? interfacePackageId = null,Object? interfacePackageName = null,Object? interfaceConfigId = null,Object? name = null,Object? description = freezed,Object? apis = null,Object? windowConfigs = null,Object? paneConfigs = null,}) {
  return _then(_self.copyWith(
interfacePackageId: null == interfacePackageId ? _self.interfacePackageId : interfacePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,interfacePackageName: null == interfacePackageName ? _self.interfacePackageName : interfacePackageName // ignore: cast_nullable_to_non_nullable
as String,interfaceConfigId: null == interfaceConfigId ? _self.interfaceConfigId : interfaceConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,apis: null == apis ? _self.apis : apis // ignore: cast_nullable_to_non_nullable
as List<InterfaceConfigApiBundle>,windowConfigs: null == windowConfigs ? _self.windowConfigs : windowConfigs // ignore: cast_nullable_to_non_nullable
as List<InterfaceWindowConfigBundle>,paneConfigs: null == paneConfigs ? _self.paneConfigs : paneConfigs // ignore: cast_nullable_to_non_nullable
as List<InterfacePaneConfigBundle>,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfaceConfigBundle].
extension InterfaceConfigBundlePatterns on InterfaceConfigBundle {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfaceConfigBundle value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfaceConfigBundle() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfaceConfigBundle value)  def,}){
final _that = this;
switch (_that) {
case _InterfaceConfigBundle():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfaceConfigBundle value)?  def,}){
final _that = this;
switch (_that) {
case _InterfaceConfigBundle() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue interfacePackageId,  String interfacePackageName, @UuidValueConverter()  UuidValue interfaceConfigId,  String name,  String? description,  List<InterfaceConfigApiBundle> apis,  List<InterfaceWindowConfigBundle> windowConfigs,  List<InterfacePaneConfigBundle> paneConfigs)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfaceConfigBundle() when def != null:
return def(_that.interfacePackageId,_that.interfacePackageName,_that.interfaceConfigId,_that.name,_that.description,_that.apis,_that.windowConfigs,_that.paneConfigs);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue interfacePackageId,  String interfacePackageName, @UuidValueConverter()  UuidValue interfaceConfigId,  String name,  String? description,  List<InterfaceConfigApiBundle> apis,  List<InterfaceWindowConfigBundle> windowConfigs,  List<InterfacePaneConfigBundle> paneConfigs)  def,}) {final _that = this;
switch (_that) {
case _InterfaceConfigBundle():
return def(_that.interfacePackageId,_that.interfacePackageName,_that.interfaceConfigId,_that.name,_that.description,_that.apis,_that.windowConfigs,_that.paneConfigs);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue interfacePackageId,  String interfacePackageName, @UuidValueConverter()  UuidValue interfaceConfigId,  String name,  String? description,  List<InterfaceConfigApiBundle> apis,  List<InterfaceWindowConfigBundle> windowConfigs,  List<InterfacePaneConfigBundle> paneConfigs)?  def,}) {final _that = this;
switch (_that) {
case _InterfaceConfigBundle() when def != null:
return def(_that.interfacePackageId,_that.interfacePackageName,_that.interfaceConfigId,_that.name,_that.description,_that.apis,_that.windowConfigs,_that.paneConfigs);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfaceConfigBundle implements InterfaceConfigBundle {
   _InterfaceConfigBundle({@UuidValueConverter() required this.interfacePackageId, required this.interfacePackageName, @UuidValueConverter() required this.interfaceConfigId, required this.name, this.description, final  List<InterfaceConfigApiBundle> apis = const [], final  List<InterfaceWindowConfigBundle> windowConfigs = const [], final  List<InterfacePaneConfigBundle> paneConfigs = const []}): _apis = apis,_windowConfigs = windowConfigs,_paneConfigs = paneConfigs;
  factory _InterfaceConfigBundle.fromJson(Map<String, dynamic> json) => _$InterfaceConfigBundleFromJson(json);

@override@UuidValueConverter() final  UuidValue interfacePackageId;
@override final  String interfacePackageName;
@override@UuidValueConverter() final  UuidValue interfaceConfigId;
@override final  String name;
@override final  String? description;
 final  List<InterfaceConfigApiBundle> _apis;
@override@JsonKey() List<InterfaceConfigApiBundle> get apis {
  if (_apis is EqualUnmodifiableListView) return _apis;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_apis);
}

 final  List<InterfaceWindowConfigBundle> _windowConfigs;
@override@JsonKey() List<InterfaceWindowConfigBundle> get windowConfigs {
  if (_windowConfigs is EqualUnmodifiableListView) return _windowConfigs;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_windowConfigs);
}

 final  List<InterfacePaneConfigBundle> _paneConfigs;
@override@JsonKey() List<InterfacePaneConfigBundle> get paneConfigs {
  if (_paneConfigs is EqualUnmodifiableListView) return _paneConfigs;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_paneConfigs);
}


/// Create a copy of InterfaceConfigBundle
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfaceConfigBundleCopyWith<_InterfaceConfigBundle> get copyWith => __$InterfaceConfigBundleCopyWithImpl<_InterfaceConfigBundle>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceConfigBundleToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfaceConfigBundle&&(identical(other.interfacePackageId, interfacePackageId) || other.interfacePackageId == interfacePackageId)&&(identical(other.interfacePackageName, interfacePackageName) || other.interfacePackageName == interfacePackageName)&&(identical(other.interfaceConfigId, interfaceConfigId) || other.interfaceConfigId == interfaceConfigId)&&(identical(other.name, name) || other.name == name)&&(identical(other.description, description) || other.description == description)&&const DeepCollectionEquality().equals(other._apis, _apis)&&const DeepCollectionEquality().equals(other._windowConfigs, _windowConfigs)&&const DeepCollectionEquality().equals(other._paneConfigs, _paneConfigs));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,interfacePackageId,interfacePackageName,interfaceConfigId,name,description,const DeepCollectionEquality().hash(_apis),const DeepCollectionEquality().hash(_windowConfigs),const DeepCollectionEquality().hash(_paneConfigs));

@override
String toString() {
  return 'InterfaceConfigBundle.def(interfacePackageId: $interfacePackageId, interfacePackageName: $interfacePackageName, interfaceConfigId: $interfaceConfigId, name: $name, description: $description, apis: $apis, windowConfigs: $windowConfigs, paneConfigs: $paneConfigs)';
}


}

/// @nodoc
abstract mixin class _$InterfaceConfigBundleCopyWith<$Res> implements $InterfaceConfigBundleCopyWith<$Res> {
  factory _$InterfaceConfigBundleCopyWith(_InterfaceConfigBundle value, $Res Function(_InterfaceConfigBundle) _then) = __$InterfaceConfigBundleCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue interfacePackageId, String interfacePackageName,@UuidValueConverter() UuidValue interfaceConfigId, String name, String? description, List<InterfaceConfigApiBundle> apis, List<InterfaceWindowConfigBundle> windowConfigs, List<InterfacePaneConfigBundle> paneConfigs
});




}
/// @nodoc
class __$InterfaceConfigBundleCopyWithImpl<$Res>
    implements _$InterfaceConfigBundleCopyWith<$Res> {
  __$InterfaceConfigBundleCopyWithImpl(this._self, this._then);

  final _InterfaceConfigBundle _self;
  final $Res Function(_InterfaceConfigBundle) _then;

/// Create a copy of InterfaceConfigBundle
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? interfacePackageId = null,Object? interfacePackageName = null,Object? interfaceConfigId = null,Object? name = null,Object? description = freezed,Object? apis = null,Object? windowConfigs = null,Object? paneConfigs = null,}) {
  return _then(_InterfaceConfigBundle(
interfacePackageId: null == interfacePackageId ? _self.interfacePackageId : interfacePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,interfacePackageName: null == interfacePackageName ? _self.interfacePackageName : interfacePackageName // ignore: cast_nullable_to_non_nullable
as String,interfaceConfigId: null == interfaceConfigId ? _self.interfaceConfigId : interfaceConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,apis: null == apis ? _self._apis : apis // ignore: cast_nullable_to_non_nullable
as List<InterfaceConfigApiBundle>,windowConfigs: null == windowConfigs ? _self._windowConfigs : windowConfigs // ignore: cast_nullable_to_non_nullable
as List<InterfaceWindowConfigBundle>,paneConfigs: null == paneConfigs ? _self._paneConfigs : paneConfigs // ignore: cast_nullable_to_non_nullable
as List<InterfacePaneConfigBundle>,
  ));
}


}

// dart format on
