// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'hosted_interface_namespace_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$HostedInterfaceNamespace {

 String get namespace; String get hostLabel; bool get started;@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue? get interfaceId;@UuidValueConverter() UuidValue? get interfaceSessionId;@UuidValueConverter() UuidValue? get environmentId;@UuidValueConverter() UuidValue? get environmentConfigId; List<String> get warnings;
/// Create a copy of HostedInterfaceNamespace
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$HostedInterfaceNamespaceCopyWith<HostedInterfaceNamespace> get copyWith => _$HostedInterfaceNamespaceCopyWithImpl<HostedInterfaceNamespace>(this as HostedInterfaceNamespace, _$identity);

  /// Serializes this HostedInterfaceNamespace to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is HostedInterfaceNamespace&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.hostLabel, hostLabel) || other.hostLabel == hostLabel)&&(identical(other.started, started) || other.started == started)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.interfaceId, interfaceId) || other.interfaceId == interfaceId)&&(identical(other.interfaceSessionId, interfaceSessionId) || other.interfaceSessionId == interfaceSessionId)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentConfigId, environmentConfigId) || other.environmentConfigId == environmentConfigId)&&const DeepCollectionEquality().equals(other.warnings, warnings));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,namespace,hostLabel,started,actorId,interfaceId,interfaceSessionId,environmentId,environmentConfigId,const DeepCollectionEquality().hash(warnings));

@override
String toString() {
  return 'HostedInterfaceNamespace(namespace: $namespace, hostLabel: $hostLabel, started: $started, actorId: $actorId, interfaceId: $interfaceId, interfaceSessionId: $interfaceSessionId, environmentId: $environmentId, environmentConfigId: $environmentConfigId, warnings: $warnings)';
}


}

/// @nodoc
abstract mixin class $HostedInterfaceNamespaceCopyWith<$Res>  {
  factory $HostedInterfaceNamespaceCopyWith(HostedInterfaceNamespace value, $Res Function(HostedInterfaceNamespace) _then) = _$HostedInterfaceNamespaceCopyWithImpl;
@useResult
$Res call({
 String namespace, String hostLabel, bool started,@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? interfaceId,@UuidValueConverter() UuidValue? interfaceSessionId,@UuidValueConverter() UuidValue? environmentId,@UuidValueConverter() UuidValue? environmentConfigId, List<String> warnings
});




}
/// @nodoc
class _$HostedInterfaceNamespaceCopyWithImpl<$Res>
    implements $HostedInterfaceNamespaceCopyWith<$Res> {
  _$HostedInterfaceNamespaceCopyWithImpl(this._self, this._then);

  final HostedInterfaceNamespace _self;
  final $Res Function(HostedInterfaceNamespace) _then;

/// Create a copy of HostedInterfaceNamespace
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? namespace = null,Object? hostLabel = null,Object? started = null,Object? actorId = freezed,Object? interfaceId = freezed,Object? interfaceSessionId = freezed,Object? environmentId = freezed,Object? environmentConfigId = freezed,Object? warnings = null,}) {
  return _then(_self.copyWith(
namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,hostLabel: null == hostLabel ? _self.hostLabel : hostLabel // ignore: cast_nullable_to_non_nullable
as String,started: null == started ? _self.started : started // ignore: cast_nullable_to_non_nullable
as bool,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,interfaceId: freezed == interfaceId ? _self.interfaceId : interfaceId // ignore: cast_nullable_to_non_nullable
as UuidValue?,interfaceSessionId: freezed == interfaceSessionId ? _self.interfaceSessionId : interfaceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentId: freezed == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentConfigId: freezed == environmentConfigId ? _self.environmentConfigId : environmentConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,warnings: null == warnings ? _self.warnings : warnings // ignore: cast_nullable_to_non_nullable
as List<String>,
  ));
}

}


/// Adds pattern-matching-related methods to [HostedInterfaceNamespace].
extension HostedInterfaceNamespacePatterns on HostedInterfaceNamespace {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _HostedInterfaceNamespace value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _HostedInterfaceNamespace() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _HostedInterfaceNamespace value)  def,}){
final _that = this;
switch (_that) {
case _HostedInterfaceNamespace():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _HostedInterfaceNamespace value)?  def,}){
final _that = this;
switch (_that) {
case _HostedInterfaceNamespace() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String namespace,  String hostLabel,  bool started, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? interfaceId, @UuidValueConverter()  UuidValue? interfaceSessionId, @UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue? environmentConfigId,  List<String> warnings)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _HostedInterfaceNamespace() when def != null:
return def(_that.namespace,_that.hostLabel,_that.started,_that.actorId,_that.interfaceId,_that.interfaceSessionId,_that.environmentId,_that.environmentConfigId,_that.warnings);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String namespace,  String hostLabel,  bool started, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? interfaceId, @UuidValueConverter()  UuidValue? interfaceSessionId, @UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue? environmentConfigId,  List<String> warnings)  def,}) {final _that = this;
switch (_that) {
case _HostedInterfaceNamespace():
return def(_that.namespace,_that.hostLabel,_that.started,_that.actorId,_that.interfaceId,_that.interfaceSessionId,_that.environmentId,_that.environmentConfigId,_that.warnings);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String namespace,  String hostLabel,  bool started, @UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue? interfaceId, @UuidValueConverter()  UuidValue? interfaceSessionId, @UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue? environmentConfigId,  List<String> warnings)?  def,}) {final _that = this;
switch (_that) {
case _HostedInterfaceNamespace() when def != null:
return def(_that.namespace,_that.hostLabel,_that.started,_that.actorId,_that.interfaceId,_that.interfaceSessionId,_that.environmentId,_that.environmentConfigId,_that.warnings);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _HostedInterfaceNamespace implements HostedInterfaceNamespace {
   _HostedInterfaceNamespace({required this.namespace, required this.hostLabel, required this.started, @UuidValueConverter() this.actorId, @UuidValueConverter() this.interfaceId, @UuidValueConverter() this.interfaceSessionId, @UuidValueConverter() this.environmentId, @UuidValueConverter() this.environmentConfigId, final  List<String> warnings = const []}): _warnings = warnings;
  factory _HostedInterfaceNamespace.fromJson(Map<String, dynamic> json) => _$HostedInterfaceNamespaceFromJson(json);

@override final  String namespace;
@override final  String hostLabel;
@override final  bool started;
@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue? interfaceId;
@override@UuidValueConverter() final  UuidValue? interfaceSessionId;
@override@UuidValueConverter() final  UuidValue? environmentId;
@override@UuidValueConverter() final  UuidValue? environmentConfigId;
 final  List<String> _warnings;
@override@JsonKey() List<String> get warnings {
  if (_warnings is EqualUnmodifiableListView) return _warnings;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_warnings);
}


/// Create a copy of HostedInterfaceNamespace
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$HostedInterfaceNamespaceCopyWith<_HostedInterfaceNamespace> get copyWith => __$HostedInterfaceNamespaceCopyWithImpl<_HostedInterfaceNamespace>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$HostedInterfaceNamespaceToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _HostedInterfaceNamespace&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.hostLabel, hostLabel) || other.hostLabel == hostLabel)&&(identical(other.started, started) || other.started == started)&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.interfaceId, interfaceId) || other.interfaceId == interfaceId)&&(identical(other.interfaceSessionId, interfaceSessionId) || other.interfaceSessionId == interfaceSessionId)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentConfigId, environmentConfigId) || other.environmentConfigId == environmentConfigId)&&const DeepCollectionEquality().equals(other._warnings, _warnings));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,namespace,hostLabel,started,actorId,interfaceId,interfaceSessionId,environmentId,environmentConfigId,const DeepCollectionEquality().hash(_warnings));

@override
String toString() {
  return 'HostedInterfaceNamespace.def(namespace: $namespace, hostLabel: $hostLabel, started: $started, actorId: $actorId, interfaceId: $interfaceId, interfaceSessionId: $interfaceSessionId, environmentId: $environmentId, environmentConfigId: $environmentConfigId, warnings: $warnings)';
}


}

/// @nodoc
abstract mixin class _$HostedInterfaceNamespaceCopyWith<$Res> implements $HostedInterfaceNamespaceCopyWith<$Res> {
  factory _$HostedInterfaceNamespaceCopyWith(_HostedInterfaceNamespace value, $Res Function(_HostedInterfaceNamespace) _then) = __$HostedInterfaceNamespaceCopyWithImpl;
@override @useResult
$Res call({
 String namespace, String hostLabel, bool started,@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue? interfaceId,@UuidValueConverter() UuidValue? interfaceSessionId,@UuidValueConverter() UuidValue? environmentId,@UuidValueConverter() UuidValue? environmentConfigId, List<String> warnings
});




}
/// @nodoc
class __$HostedInterfaceNamespaceCopyWithImpl<$Res>
    implements _$HostedInterfaceNamespaceCopyWith<$Res> {
  __$HostedInterfaceNamespaceCopyWithImpl(this._self, this._then);

  final _HostedInterfaceNamespace _self;
  final $Res Function(_HostedInterfaceNamespace) _then;

/// Create a copy of HostedInterfaceNamespace
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? namespace = null,Object? hostLabel = null,Object? started = null,Object? actorId = freezed,Object? interfaceId = freezed,Object? interfaceSessionId = freezed,Object? environmentId = freezed,Object? environmentConfigId = freezed,Object? warnings = null,}) {
  return _then(_HostedInterfaceNamespace(
namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,hostLabel: null == hostLabel ? _self.hostLabel : hostLabel // ignore: cast_nullable_to_non_nullable
as String,started: null == started ? _self.started : started // ignore: cast_nullable_to_non_nullable
as bool,actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,interfaceId: freezed == interfaceId ? _self.interfaceId : interfaceId // ignore: cast_nullable_to_non_nullable
as UuidValue?,interfaceSessionId: freezed == interfaceSessionId ? _self.interfaceSessionId : interfaceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentId: freezed == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentConfigId: freezed == environmentConfigId ? _self.environmentConfigId : environmentConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,warnings: null == warnings ? _self._warnings : warnings // ignore: cast_nullable_to_non_nullable
as List<String>,
  ));
}


}

// dart format on
