// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'sdk_operation_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$SdkOperation {

@UuidValueConverter() UuidValue get id; List<SdkOperationApiCapabilityEndpoint> get apiCapabilityEndpoints; List<SdkOperationDependency> get sdkOperationDependencies; String get name; String? get title; String? get description; String? get implementationRef;@UuidValueConverter() UuidValue get sdkConfigId;
/// Create a copy of SdkOperation
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$SdkOperationCopyWith<SdkOperation> get copyWith => _$SdkOperationCopyWithImpl<SdkOperation>(this as SdkOperation, _$identity);

  /// Serializes this SdkOperation to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is SdkOperation&&(identical(other.id, id) || other.id == id)&&const DeepCollectionEquality().equals(other.apiCapabilityEndpoints, apiCapabilityEndpoints)&&const DeepCollectionEquality().equals(other.sdkOperationDependencies, sdkOperationDependencies)&&(identical(other.name, name) || other.name == name)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.implementationRef, implementationRef) || other.implementationRef == implementationRef)&&(identical(other.sdkConfigId, sdkConfigId) || other.sdkConfigId == sdkConfigId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,const DeepCollectionEquality().hash(apiCapabilityEndpoints),const DeepCollectionEquality().hash(sdkOperationDependencies),name,title,description,implementationRef,sdkConfigId);

@override
String toString() {
  return 'SdkOperation(id: $id, apiCapabilityEndpoints: $apiCapabilityEndpoints, sdkOperationDependencies: $sdkOperationDependencies, name: $name, title: $title, description: $description, implementationRef: $implementationRef, sdkConfigId: $sdkConfigId)';
}


}

/// @nodoc
abstract mixin class $SdkOperationCopyWith<$Res>  {
  factory $SdkOperationCopyWith(SdkOperation value, $Res Function(SdkOperation) _then) = _$SdkOperationCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue id, List<SdkOperationApiCapabilityEndpoint> apiCapabilityEndpoints, List<SdkOperationDependency> sdkOperationDependencies, String name, String? title, String? description, String? implementationRef,@UuidValueConverter() UuidValue sdkConfigId
});




}
/// @nodoc
class _$SdkOperationCopyWithImpl<$Res>
    implements $SdkOperationCopyWith<$Res> {
  _$SdkOperationCopyWithImpl(this._self, this._then);

  final SdkOperation _self;
  final $Res Function(SdkOperation) _then;

/// Create a copy of SdkOperation
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? id = null,Object? apiCapabilityEndpoints = null,Object? sdkOperationDependencies = null,Object? name = null,Object? title = freezed,Object? description = freezed,Object? implementationRef = freezed,Object? sdkConfigId = null,}) {
  return _then(_self.copyWith(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,apiCapabilityEndpoints: null == apiCapabilityEndpoints ? _self.apiCapabilityEndpoints : apiCapabilityEndpoints // ignore: cast_nullable_to_non_nullable
as List<SdkOperationApiCapabilityEndpoint>,sdkOperationDependencies: null == sdkOperationDependencies ? _self.sdkOperationDependencies : sdkOperationDependencies // ignore: cast_nullable_to_non_nullable
as List<SdkOperationDependency>,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,implementationRef: freezed == implementationRef ? _self.implementationRef : implementationRef // ignore: cast_nullable_to_non_nullable
as String?,sdkConfigId: null == sdkConfigId ? _self.sdkConfigId : sdkConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,
  ));
}

}


/// Adds pattern-matching-related methods to [SdkOperation].
extension SdkOperationPatterns on SdkOperation {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _SdkOperation value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _SdkOperation() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _SdkOperation value)  def,}){
final _that = this;
switch (_that) {
case _SdkOperation():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _SdkOperation value)?  def,}){
final _that = this;
switch (_that) {
case _SdkOperation() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue id,  List<SdkOperationApiCapabilityEndpoint> apiCapabilityEndpoints,  List<SdkOperationDependency> sdkOperationDependencies,  String name,  String? title,  String? description,  String? implementationRef, @UuidValueConverter()  UuidValue sdkConfigId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _SdkOperation() when def != null:
return def(_that.id,_that.apiCapabilityEndpoints,_that.sdkOperationDependencies,_that.name,_that.title,_that.description,_that.implementationRef,_that.sdkConfigId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue id,  List<SdkOperationApiCapabilityEndpoint> apiCapabilityEndpoints,  List<SdkOperationDependency> sdkOperationDependencies,  String name,  String? title,  String? description,  String? implementationRef, @UuidValueConverter()  UuidValue sdkConfigId)  def,}) {final _that = this;
switch (_that) {
case _SdkOperation():
return def(_that.id,_that.apiCapabilityEndpoints,_that.sdkOperationDependencies,_that.name,_that.title,_that.description,_that.implementationRef,_that.sdkConfigId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue id,  List<SdkOperationApiCapabilityEndpoint> apiCapabilityEndpoints,  List<SdkOperationDependency> sdkOperationDependencies,  String name,  String? title,  String? description,  String? implementationRef, @UuidValueConverter()  UuidValue sdkConfigId)?  def,}) {final _that = this;
switch (_that) {
case _SdkOperation() when def != null:
return def(_that.id,_that.apiCapabilityEndpoints,_that.sdkOperationDependencies,_that.name,_that.title,_that.description,_that.implementationRef,_that.sdkConfigId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _SdkOperation implements SdkOperation {
   _SdkOperation({@UuidValueConverter() required this.id, final  List<SdkOperationApiCapabilityEndpoint> apiCapabilityEndpoints = const [], final  List<SdkOperationDependency> sdkOperationDependencies = const [], required this.name, this.title, this.description, this.implementationRef, @UuidValueConverter() required this.sdkConfigId}): _apiCapabilityEndpoints = apiCapabilityEndpoints,_sdkOperationDependencies = sdkOperationDependencies;
  factory _SdkOperation.fromJson(Map<String, dynamic> json) => _$SdkOperationFromJson(json);

@override@UuidValueConverter() final  UuidValue id;
 final  List<SdkOperationApiCapabilityEndpoint> _apiCapabilityEndpoints;
@override@JsonKey() List<SdkOperationApiCapabilityEndpoint> get apiCapabilityEndpoints {
  if (_apiCapabilityEndpoints is EqualUnmodifiableListView) return _apiCapabilityEndpoints;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_apiCapabilityEndpoints);
}

 final  List<SdkOperationDependency> _sdkOperationDependencies;
@override@JsonKey() List<SdkOperationDependency> get sdkOperationDependencies {
  if (_sdkOperationDependencies is EqualUnmodifiableListView) return _sdkOperationDependencies;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_sdkOperationDependencies);
}

@override final  String name;
@override final  String? title;
@override final  String? description;
@override final  String? implementationRef;
@override@UuidValueConverter() final  UuidValue sdkConfigId;

/// Create a copy of SdkOperation
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$SdkOperationCopyWith<_SdkOperation> get copyWith => __$SdkOperationCopyWithImpl<_SdkOperation>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$SdkOperationToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _SdkOperation&&(identical(other.id, id) || other.id == id)&&const DeepCollectionEquality().equals(other._apiCapabilityEndpoints, _apiCapabilityEndpoints)&&const DeepCollectionEquality().equals(other._sdkOperationDependencies, _sdkOperationDependencies)&&(identical(other.name, name) || other.name == name)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.implementationRef, implementationRef) || other.implementationRef == implementationRef)&&(identical(other.sdkConfigId, sdkConfigId) || other.sdkConfigId == sdkConfigId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,const DeepCollectionEquality().hash(_apiCapabilityEndpoints),const DeepCollectionEquality().hash(_sdkOperationDependencies),name,title,description,implementationRef,sdkConfigId);

@override
String toString() {
  return 'SdkOperation.def(id: $id, apiCapabilityEndpoints: $apiCapabilityEndpoints, sdkOperationDependencies: $sdkOperationDependencies, name: $name, title: $title, description: $description, implementationRef: $implementationRef, sdkConfigId: $sdkConfigId)';
}


}

/// @nodoc
abstract mixin class _$SdkOperationCopyWith<$Res> implements $SdkOperationCopyWith<$Res> {
  factory _$SdkOperationCopyWith(_SdkOperation value, $Res Function(_SdkOperation) _then) = __$SdkOperationCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue id, List<SdkOperationApiCapabilityEndpoint> apiCapabilityEndpoints, List<SdkOperationDependency> sdkOperationDependencies, String name, String? title, String? description, String? implementationRef,@UuidValueConverter() UuidValue sdkConfigId
});




}
/// @nodoc
class __$SdkOperationCopyWithImpl<$Res>
    implements _$SdkOperationCopyWith<$Res> {
  __$SdkOperationCopyWithImpl(this._self, this._then);

  final _SdkOperation _self;
  final $Res Function(_SdkOperation) _then;

/// Create a copy of SdkOperation
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? id = null,Object? apiCapabilityEndpoints = null,Object? sdkOperationDependencies = null,Object? name = null,Object? title = freezed,Object? description = freezed,Object? implementationRef = freezed,Object? sdkConfigId = null,}) {
  return _then(_SdkOperation(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as UuidValue,apiCapabilityEndpoints: null == apiCapabilityEndpoints ? _self._apiCapabilityEndpoints : apiCapabilityEndpoints // ignore: cast_nullable_to_non_nullable
as List<SdkOperationApiCapabilityEndpoint>,sdkOperationDependencies: null == sdkOperationDependencies ? _self._sdkOperationDependencies : sdkOperationDependencies // ignore: cast_nullable_to_non_nullable
as List<SdkOperationDependency>,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,implementationRef: freezed == implementationRef ? _self.implementationRef : implementationRef // ignore: cast_nullable_to_non_nullable
as String?,sdkConfigId: null == sdkConfigId ? _self.sdkConfigId : sdkConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,
  ));
}


}

// dart format on
