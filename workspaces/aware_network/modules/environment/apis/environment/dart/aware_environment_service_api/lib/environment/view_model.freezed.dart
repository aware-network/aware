// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'view_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$EnvironmentStatusBlockSummaryV1 {

 String get name; bool get available; String? get authorityKind; String? get unavailableReason; Map<String, dynamic> get payload;
/// Create a copy of EnvironmentStatusBlockSummaryV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$EnvironmentStatusBlockSummaryV1CopyWith<EnvironmentStatusBlockSummaryV1> get copyWith => _$EnvironmentStatusBlockSummaryV1CopyWithImpl<EnvironmentStatusBlockSummaryV1>(this as EnvironmentStatusBlockSummaryV1, _$identity);

  /// Serializes this EnvironmentStatusBlockSummaryV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is EnvironmentStatusBlockSummaryV1&&(identical(other.name, name) || other.name == name)&&(identical(other.available, available) || other.available == available)&&(identical(other.authorityKind, authorityKind) || other.authorityKind == authorityKind)&&(identical(other.unavailableReason, unavailableReason) || other.unavailableReason == unavailableReason)&&const DeepCollectionEquality().equals(other.payload, payload));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,name,available,authorityKind,unavailableReason,const DeepCollectionEquality().hash(payload));

@override
String toString() {
  return 'EnvironmentStatusBlockSummaryV1(name: $name, available: $available, authorityKind: $authorityKind, unavailableReason: $unavailableReason, payload: $payload)';
}


}

/// @nodoc
abstract mixin class $EnvironmentStatusBlockSummaryV1CopyWith<$Res>  {
  factory $EnvironmentStatusBlockSummaryV1CopyWith(EnvironmentStatusBlockSummaryV1 value, $Res Function(EnvironmentStatusBlockSummaryV1) _then) = _$EnvironmentStatusBlockSummaryV1CopyWithImpl;
@useResult
$Res call({
 String name, bool available, String? authorityKind, String? unavailableReason, Map<String, dynamic> payload
});




}
/// @nodoc
class _$EnvironmentStatusBlockSummaryV1CopyWithImpl<$Res>
    implements $EnvironmentStatusBlockSummaryV1CopyWith<$Res> {
  _$EnvironmentStatusBlockSummaryV1CopyWithImpl(this._self, this._then);

  final EnvironmentStatusBlockSummaryV1 _self;
  final $Res Function(EnvironmentStatusBlockSummaryV1) _then;

/// Create a copy of EnvironmentStatusBlockSummaryV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? name = null,Object? available = null,Object? authorityKind = freezed,Object? unavailableReason = freezed,Object? payload = null,}) {
  return _then(_self.copyWith(
name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,available: null == available ? _self.available : available // ignore: cast_nullable_to_non_nullable
as bool,authorityKind: freezed == authorityKind ? _self.authorityKind : authorityKind // ignore: cast_nullable_to_non_nullable
as String?,unavailableReason: freezed == unavailableReason ? _self.unavailableReason : unavailableReason // ignore: cast_nullable_to_non_nullable
as String?,payload: null == payload ? _self.payload : payload // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [EnvironmentStatusBlockSummaryV1].
extension EnvironmentStatusBlockSummaryV1Patterns on EnvironmentStatusBlockSummaryV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _EnvironmentStatusBlockSummaryV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _EnvironmentStatusBlockSummaryV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _EnvironmentStatusBlockSummaryV1 value)  def,}){
final _that = this;
switch (_that) {
case _EnvironmentStatusBlockSummaryV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _EnvironmentStatusBlockSummaryV1 value)?  def,}){
final _that = this;
switch (_that) {
case _EnvironmentStatusBlockSummaryV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String name,  bool available,  String? authorityKind,  String? unavailableReason,  Map<String, dynamic> payload)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _EnvironmentStatusBlockSummaryV1() when def != null:
return def(_that.name,_that.available,_that.authorityKind,_that.unavailableReason,_that.payload);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String name,  bool available,  String? authorityKind,  String? unavailableReason,  Map<String, dynamic> payload)  def,}) {final _that = this;
switch (_that) {
case _EnvironmentStatusBlockSummaryV1():
return def(_that.name,_that.available,_that.authorityKind,_that.unavailableReason,_that.payload);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String name,  bool available,  String? authorityKind,  String? unavailableReason,  Map<String, dynamic> payload)?  def,}) {final _that = this;
switch (_that) {
case _EnvironmentStatusBlockSummaryV1() when def != null:
return def(_that.name,_that.available,_that.authorityKind,_that.unavailableReason,_that.payload);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _EnvironmentStatusBlockSummaryV1 implements EnvironmentStatusBlockSummaryV1 {
   _EnvironmentStatusBlockSummaryV1({required this.name, required this.available, this.authorityKind, this.unavailableReason, required final  Map<String, dynamic> payload}): _payload = payload;
  factory _EnvironmentStatusBlockSummaryV1.fromJson(Map<String, dynamic> json) => _$EnvironmentStatusBlockSummaryV1FromJson(json);

@override final  String name;
@override final  bool available;
@override final  String? authorityKind;
@override final  String? unavailableReason;
 final  Map<String, dynamic> _payload;
@override Map<String, dynamic> get payload {
  if (_payload is EqualUnmodifiableMapView) return _payload;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_payload);
}


/// Create a copy of EnvironmentStatusBlockSummaryV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$EnvironmentStatusBlockSummaryV1CopyWith<_EnvironmentStatusBlockSummaryV1> get copyWith => __$EnvironmentStatusBlockSummaryV1CopyWithImpl<_EnvironmentStatusBlockSummaryV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$EnvironmentStatusBlockSummaryV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _EnvironmentStatusBlockSummaryV1&&(identical(other.name, name) || other.name == name)&&(identical(other.available, available) || other.available == available)&&(identical(other.authorityKind, authorityKind) || other.authorityKind == authorityKind)&&(identical(other.unavailableReason, unavailableReason) || other.unavailableReason == unavailableReason)&&const DeepCollectionEquality().equals(other._payload, _payload));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,name,available,authorityKind,unavailableReason,const DeepCollectionEquality().hash(_payload));

@override
String toString() {
  return 'EnvironmentStatusBlockSummaryV1.def(name: $name, available: $available, authorityKind: $authorityKind, unavailableReason: $unavailableReason, payload: $payload)';
}


}

/// @nodoc
abstract mixin class _$EnvironmentStatusBlockSummaryV1CopyWith<$Res> implements $EnvironmentStatusBlockSummaryV1CopyWith<$Res> {
  factory _$EnvironmentStatusBlockSummaryV1CopyWith(_EnvironmentStatusBlockSummaryV1 value, $Res Function(_EnvironmentStatusBlockSummaryV1) _then) = __$EnvironmentStatusBlockSummaryV1CopyWithImpl;
@override @useResult
$Res call({
 String name, bool available, String? authorityKind, String? unavailableReason, Map<String, dynamic> payload
});




}
/// @nodoc
class __$EnvironmentStatusBlockSummaryV1CopyWithImpl<$Res>
    implements _$EnvironmentStatusBlockSummaryV1CopyWith<$Res> {
  __$EnvironmentStatusBlockSummaryV1CopyWithImpl(this._self, this._then);

  final _EnvironmentStatusBlockSummaryV1 _self;
  final $Res Function(_EnvironmentStatusBlockSummaryV1) _then;

/// Create a copy of EnvironmentStatusBlockSummaryV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? name = null,Object? available = null,Object? authorityKind = freezed,Object? unavailableReason = freezed,Object? payload = null,}) {
  return _then(_EnvironmentStatusBlockSummaryV1(
name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,available: null == available ? _self.available : available // ignore: cast_nullable_to_non_nullable
as bool,authorityKind: freezed == authorityKind ? _self.authorityKind : authorityKind // ignore: cast_nullable_to_non_nullable
as String?,unavailableReason: freezed == unavailableReason ? _self.unavailableReason : unavailableReason // ignore: cast_nullable_to_non_nullable
as String?,payload: null == payload ? _self._payload : payload // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$EnvironmentThreadNavigationItemV1 {

@UuidValueConverter() UuidValue? get threadId; String? get threadKey; String get title; String? get description; int get attachmentCount; int get activeAttachmentCount; bool get isSelected;
/// Create a copy of EnvironmentThreadNavigationItemV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$EnvironmentThreadNavigationItemV1CopyWith<EnvironmentThreadNavigationItemV1> get copyWith => _$EnvironmentThreadNavigationItemV1CopyWithImpl<EnvironmentThreadNavigationItemV1>(this as EnvironmentThreadNavigationItemV1, _$identity);

  /// Serializes this EnvironmentThreadNavigationItemV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is EnvironmentThreadNavigationItemV1&&(identical(other.threadId, threadId) || other.threadId == threadId)&&(identical(other.threadKey, threadKey) || other.threadKey == threadKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.attachmentCount, attachmentCount) || other.attachmentCount == attachmentCount)&&(identical(other.activeAttachmentCount, activeAttachmentCount) || other.activeAttachmentCount == activeAttachmentCount)&&(identical(other.isSelected, isSelected) || other.isSelected == isSelected));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,threadId,threadKey,title,description,attachmentCount,activeAttachmentCount,isSelected);

@override
String toString() {
  return 'EnvironmentThreadNavigationItemV1(threadId: $threadId, threadKey: $threadKey, title: $title, description: $description, attachmentCount: $attachmentCount, activeAttachmentCount: $activeAttachmentCount, isSelected: $isSelected)';
}


}

/// @nodoc
abstract mixin class $EnvironmentThreadNavigationItemV1CopyWith<$Res>  {
  factory $EnvironmentThreadNavigationItemV1CopyWith(EnvironmentThreadNavigationItemV1 value, $Res Function(EnvironmentThreadNavigationItemV1) _then) = _$EnvironmentThreadNavigationItemV1CopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? threadId, String? threadKey, String title, String? description, int attachmentCount, int activeAttachmentCount, bool isSelected
});




}
/// @nodoc
class _$EnvironmentThreadNavigationItemV1CopyWithImpl<$Res>
    implements $EnvironmentThreadNavigationItemV1CopyWith<$Res> {
  _$EnvironmentThreadNavigationItemV1CopyWithImpl(this._self, this._then);

  final EnvironmentThreadNavigationItemV1 _self;
  final $Res Function(EnvironmentThreadNavigationItemV1) _then;

/// Create a copy of EnvironmentThreadNavigationItemV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? threadId = freezed,Object? threadKey = freezed,Object? title = null,Object? description = freezed,Object? attachmentCount = null,Object? activeAttachmentCount = null,Object? isSelected = null,}) {
  return _then(_self.copyWith(
threadId: freezed == threadId ? _self.threadId : threadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,threadKey: freezed == threadKey ? _self.threadKey : threadKey // ignore: cast_nullable_to_non_nullable
as String?,title: null == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,attachmentCount: null == attachmentCount ? _self.attachmentCount : attachmentCount // ignore: cast_nullable_to_non_nullable
as int,activeAttachmentCount: null == activeAttachmentCount ? _self.activeAttachmentCount : activeAttachmentCount // ignore: cast_nullable_to_non_nullable
as int,isSelected: null == isSelected ? _self.isSelected : isSelected // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}

}


/// Adds pattern-matching-related methods to [EnvironmentThreadNavigationItemV1].
extension EnvironmentThreadNavigationItemV1Patterns on EnvironmentThreadNavigationItemV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _EnvironmentThreadNavigationItemV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _EnvironmentThreadNavigationItemV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _EnvironmentThreadNavigationItemV1 value)  def,}){
final _that = this;
switch (_that) {
case _EnvironmentThreadNavigationItemV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _EnvironmentThreadNavigationItemV1 value)?  def,}){
final _that = this;
switch (_that) {
case _EnvironmentThreadNavigationItemV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? threadId,  String? threadKey,  String title,  String? description,  int attachmentCount,  int activeAttachmentCount,  bool isSelected)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _EnvironmentThreadNavigationItemV1() when def != null:
return def(_that.threadId,_that.threadKey,_that.title,_that.description,_that.attachmentCount,_that.activeAttachmentCount,_that.isSelected);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? threadId,  String? threadKey,  String title,  String? description,  int attachmentCount,  int activeAttachmentCount,  bool isSelected)  def,}) {final _that = this;
switch (_that) {
case _EnvironmentThreadNavigationItemV1():
return def(_that.threadId,_that.threadKey,_that.title,_that.description,_that.attachmentCount,_that.activeAttachmentCount,_that.isSelected);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? threadId,  String? threadKey,  String title,  String? description,  int attachmentCount,  int activeAttachmentCount,  bool isSelected)?  def,}) {final _that = this;
switch (_that) {
case _EnvironmentThreadNavigationItemV1() when def != null:
return def(_that.threadId,_that.threadKey,_that.title,_that.description,_that.attachmentCount,_that.activeAttachmentCount,_that.isSelected);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _EnvironmentThreadNavigationItemV1 implements EnvironmentThreadNavigationItemV1 {
   _EnvironmentThreadNavigationItemV1({@UuidValueConverter() this.threadId, this.threadKey, required this.title, this.description, required this.attachmentCount, required this.activeAttachmentCount, required this.isSelected});
  factory _EnvironmentThreadNavigationItemV1.fromJson(Map<String, dynamic> json) => _$EnvironmentThreadNavigationItemV1FromJson(json);

@override@UuidValueConverter() final  UuidValue? threadId;
@override final  String? threadKey;
@override final  String title;
@override final  String? description;
@override final  int attachmentCount;
@override final  int activeAttachmentCount;
@override final  bool isSelected;

/// Create a copy of EnvironmentThreadNavigationItemV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$EnvironmentThreadNavigationItemV1CopyWith<_EnvironmentThreadNavigationItemV1> get copyWith => __$EnvironmentThreadNavigationItemV1CopyWithImpl<_EnvironmentThreadNavigationItemV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$EnvironmentThreadNavigationItemV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _EnvironmentThreadNavigationItemV1&&(identical(other.threadId, threadId) || other.threadId == threadId)&&(identical(other.threadKey, threadKey) || other.threadKey == threadKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.attachmentCount, attachmentCount) || other.attachmentCount == attachmentCount)&&(identical(other.activeAttachmentCount, activeAttachmentCount) || other.activeAttachmentCount == activeAttachmentCount)&&(identical(other.isSelected, isSelected) || other.isSelected == isSelected));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,threadId,threadKey,title,description,attachmentCount,activeAttachmentCount,isSelected);

@override
String toString() {
  return 'EnvironmentThreadNavigationItemV1.def(threadId: $threadId, threadKey: $threadKey, title: $title, description: $description, attachmentCount: $attachmentCount, activeAttachmentCount: $activeAttachmentCount, isSelected: $isSelected)';
}


}

/// @nodoc
abstract mixin class _$EnvironmentThreadNavigationItemV1CopyWith<$Res> implements $EnvironmentThreadNavigationItemV1CopyWith<$Res> {
  factory _$EnvironmentThreadNavigationItemV1CopyWith(_EnvironmentThreadNavigationItemV1 value, $Res Function(_EnvironmentThreadNavigationItemV1) _then) = __$EnvironmentThreadNavigationItemV1CopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? threadId, String? threadKey, String title, String? description, int attachmentCount, int activeAttachmentCount, bool isSelected
});




}
/// @nodoc
class __$EnvironmentThreadNavigationItemV1CopyWithImpl<$Res>
    implements _$EnvironmentThreadNavigationItemV1CopyWith<$Res> {
  __$EnvironmentThreadNavigationItemV1CopyWithImpl(this._self, this._then);

  final _EnvironmentThreadNavigationItemV1 _self;
  final $Res Function(_EnvironmentThreadNavigationItemV1) _then;

/// Create a copy of EnvironmentThreadNavigationItemV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? threadId = freezed,Object? threadKey = freezed,Object? title = null,Object? description = freezed,Object? attachmentCount = null,Object? activeAttachmentCount = null,Object? isSelected = null,}) {
  return _then(_EnvironmentThreadNavigationItemV1(
threadId: freezed == threadId ? _self.threadId : threadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,threadKey: freezed == threadKey ? _self.threadKey : threadKey // ignore: cast_nullable_to_non_nullable
as String?,title: null == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,attachmentCount: null == attachmentCount ? _self.attachmentCount : attachmentCount // ignore: cast_nullable_to_non_nullable
as int,activeAttachmentCount: null == activeAttachmentCount ? _self.activeAttachmentCount : activeAttachmentCount // ignore: cast_nullable_to_non_nullable
as int,isSelected: null == isSelected ? _self.isSelected : isSelected // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}


}


/// @nodoc
mixin _$EnvironmentProcessNavigationItemV1 {

@UuidValueConverter() UuidValue? get processId; String? get processKey; String get title; String? get description; int get threadCount; bool get isSelected; List<EnvironmentThreadNavigationItemV1> get threads;
/// Create a copy of EnvironmentProcessNavigationItemV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$EnvironmentProcessNavigationItemV1CopyWith<EnvironmentProcessNavigationItemV1> get copyWith => _$EnvironmentProcessNavigationItemV1CopyWithImpl<EnvironmentProcessNavigationItemV1>(this as EnvironmentProcessNavigationItemV1, _$identity);

  /// Serializes this EnvironmentProcessNavigationItemV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is EnvironmentProcessNavigationItemV1&&(identical(other.processId, processId) || other.processId == processId)&&(identical(other.processKey, processKey) || other.processKey == processKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.threadCount, threadCount) || other.threadCount == threadCount)&&(identical(other.isSelected, isSelected) || other.isSelected == isSelected)&&const DeepCollectionEquality().equals(other.threads, threads));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,processId,processKey,title,description,threadCount,isSelected,const DeepCollectionEquality().hash(threads));

@override
String toString() {
  return 'EnvironmentProcessNavigationItemV1(processId: $processId, processKey: $processKey, title: $title, description: $description, threadCount: $threadCount, isSelected: $isSelected, threads: $threads)';
}


}

/// @nodoc
abstract mixin class $EnvironmentProcessNavigationItemV1CopyWith<$Res>  {
  factory $EnvironmentProcessNavigationItemV1CopyWith(EnvironmentProcessNavigationItemV1 value, $Res Function(EnvironmentProcessNavigationItemV1) _then) = _$EnvironmentProcessNavigationItemV1CopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? processId, String? processKey, String title, String? description, int threadCount, bool isSelected, List<EnvironmentThreadNavigationItemV1> threads
});




}
/// @nodoc
class _$EnvironmentProcessNavigationItemV1CopyWithImpl<$Res>
    implements $EnvironmentProcessNavigationItemV1CopyWith<$Res> {
  _$EnvironmentProcessNavigationItemV1CopyWithImpl(this._self, this._then);

  final EnvironmentProcessNavigationItemV1 _self;
  final $Res Function(EnvironmentProcessNavigationItemV1) _then;

/// Create a copy of EnvironmentProcessNavigationItemV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? processId = freezed,Object? processKey = freezed,Object? title = null,Object? description = freezed,Object? threadCount = null,Object? isSelected = null,Object? threads = null,}) {
  return _then(_self.copyWith(
processId: freezed == processId ? _self.processId : processId // ignore: cast_nullable_to_non_nullable
as UuidValue?,processKey: freezed == processKey ? _self.processKey : processKey // ignore: cast_nullable_to_non_nullable
as String?,title: null == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,threadCount: null == threadCount ? _self.threadCount : threadCount // ignore: cast_nullable_to_non_nullable
as int,isSelected: null == isSelected ? _self.isSelected : isSelected // ignore: cast_nullable_to_non_nullable
as bool,threads: null == threads ? _self.threads : threads // ignore: cast_nullable_to_non_nullable
as List<EnvironmentThreadNavigationItemV1>,
  ));
}

}


/// Adds pattern-matching-related methods to [EnvironmentProcessNavigationItemV1].
extension EnvironmentProcessNavigationItemV1Patterns on EnvironmentProcessNavigationItemV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _EnvironmentProcessNavigationItemV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _EnvironmentProcessNavigationItemV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _EnvironmentProcessNavigationItemV1 value)  def,}){
final _that = this;
switch (_that) {
case _EnvironmentProcessNavigationItemV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _EnvironmentProcessNavigationItemV1 value)?  def,}){
final _that = this;
switch (_that) {
case _EnvironmentProcessNavigationItemV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? processId,  String? processKey,  String title,  String? description,  int threadCount,  bool isSelected,  List<EnvironmentThreadNavigationItemV1> threads)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _EnvironmentProcessNavigationItemV1() when def != null:
return def(_that.processId,_that.processKey,_that.title,_that.description,_that.threadCount,_that.isSelected,_that.threads);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? processId,  String? processKey,  String title,  String? description,  int threadCount,  bool isSelected,  List<EnvironmentThreadNavigationItemV1> threads)  def,}) {final _that = this;
switch (_that) {
case _EnvironmentProcessNavigationItemV1():
return def(_that.processId,_that.processKey,_that.title,_that.description,_that.threadCount,_that.isSelected,_that.threads);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? processId,  String? processKey,  String title,  String? description,  int threadCount,  bool isSelected,  List<EnvironmentThreadNavigationItemV1> threads)?  def,}) {final _that = this;
switch (_that) {
case _EnvironmentProcessNavigationItemV1() when def != null:
return def(_that.processId,_that.processKey,_that.title,_that.description,_that.threadCount,_that.isSelected,_that.threads);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _EnvironmentProcessNavigationItemV1 implements EnvironmentProcessNavigationItemV1 {
   _EnvironmentProcessNavigationItemV1({@UuidValueConverter() this.processId, this.processKey, required this.title, this.description, required this.threadCount, required this.isSelected, final  List<EnvironmentThreadNavigationItemV1> threads = const []}): _threads = threads;
  factory _EnvironmentProcessNavigationItemV1.fromJson(Map<String, dynamic> json) => _$EnvironmentProcessNavigationItemV1FromJson(json);

@override@UuidValueConverter() final  UuidValue? processId;
@override final  String? processKey;
@override final  String title;
@override final  String? description;
@override final  int threadCount;
@override final  bool isSelected;
 final  List<EnvironmentThreadNavigationItemV1> _threads;
@override@JsonKey() List<EnvironmentThreadNavigationItemV1> get threads {
  if (_threads is EqualUnmodifiableListView) return _threads;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_threads);
}


/// Create a copy of EnvironmentProcessNavigationItemV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$EnvironmentProcessNavigationItemV1CopyWith<_EnvironmentProcessNavigationItemV1> get copyWith => __$EnvironmentProcessNavigationItemV1CopyWithImpl<_EnvironmentProcessNavigationItemV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$EnvironmentProcessNavigationItemV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _EnvironmentProcessNavigationItemV1&&(identical(other.processId, processId) || other.processId == processId)&&(identical(other.processKey, processKey) || other.processKey == processKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.threadCount, threadCount) || other.threadCount == threadCount)&&(identical(other.isSelected, isSelected) || other.isSelected == isSelected)&&const DeepCollectionEquality().equals(other._threads, _threads));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,processId,processKey,title,description,threadCount,isSelected,const DeepCollectionEquality().hash(_threads));

@override
String toString() {
  return 'EnvironmentProcessNavigationItemV1.def(processId: $processId, processKey: $processKey, title: $title, description: $description, threadCount: $threadCount, isSelected: $isSelected, threads: $threads)';
}


}

/// @nodoc
abstract mixin class _$EnvironmentProcessNavigationItemV1CopyWith<$Res> implements $EnvironmentProcessNavigationItemV1CopyWith<$Res> {
  factory _$EnvironmentProcessNavigationItemV1CopyWith(_EnvironmentProcessNavigationItemV1 value, $Res Function(_EnvironmentProcessNavigationItemV1) _then) = __$EnvironmentProcessNavigationItemV1CopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? processId, String? processKey, String title, String? description, int threadCount, bool isSelected, List<EnvironmentThreadNavigationItemV1> threads
});




}
/// @nodoc
class __$EnvironmentProcessNavigationItemV1CopyWithImpl<$Res>
    implements _$EnvironmentProcessNavigationItemV1CopyWith<$Res> {
  __$EnvironmentProcessNavigationItemV1CopyWithImpl(this._self, this._then);

  final _EnvironmentProcessNavigationItemV1 _self;
  final $Res Function(_EnvironmentProcessNavigationItemV1) _then;

/// Create a copy of EnvironmentProcessNavigationItemV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? processId = freezed,Object? processKey = freezed,Object? title = null,Object? description = freezed,Object? threadCount = null,Object? isSelected = null,Object? threads = null,}) {
  return _then(_EnvironmentProcessNavigationItemV1(
processId: freezed == processId ? _self.processId : processId // ignore: cast_nullable_to_non_nullable
as UuidValue?,processKey: freezed == processKey ? _self.processKey : processKey // ignore: cast_nullable_to_non_nullable
as String?,title: null == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,threadCount: null == threadCount ? _self.threadCount : threadCount // ignore: cast_nullable_to_non_nullable
as int,isSelected: null == isSelected ? _self.isSelected : isSelected // ignore: cast_nullable_to_non_nullable
as bool,threads: null == threads ? _self._threads : threads // ignore: cast_nullable_to_non_nullable
as List<EnvironmentThreadNavigationItemV1>,
  ));
}


}


/// @nodoc
mixin _$EnvironmentNavigatorViewStateV1 {

@UuidValueConverter() UuidValue? get environmentId; String get title; String get status; bool get ready;@UuidValueConverter() UuidValue? get selectedProcessId; String? get selectedProcessKey;@UuidValueConverter() UuidValue? get selectedThreadId; String? get selectedThreadKey; List<EnvironmentProcessNavigationItemV1> get processes; List<EnvironmentStatusBlockSummaryV1> get statusBlocks; String get emptyMessage; Map<String, dynamic> get provenance;
/// Create a copy of EnvironmentNavigatorViewStateV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$EnvironmentNavigatorViewStateV1CopyWith<EnvironmentNavigatorViewStateV1> get copyWith => _$EnvironmentNavigatorViewStateV1CopyWithImpl<EnvironmentNavigatorViewStateV1>(this as EnvironmentNavigatorViewStateV1, _$identity);

  /// Serializes this EnvironmentNavigatorViewStateV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is EnvironmentNavigatorViewStateV1&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.title, title) || other.title == title)&&(identical(other.status, status) || other.status == status)&&(identical(other.ready, ready) || other.ready == ready)&&(identical(other.selectedProcessId, selectedProcessId) || other.selectedProcessId == selectedProcessId)&&(identical(other.selectedProcessKey, selectedProcessKey) || other.selectedProcessKey == selectedProcessKey)&&(identical(other.selectedThreadId, selectedThreadId) || other.selectedThreadId == selectedThreadId)&&(identical(other.selectedThreadKey, selectedThreadKey) || other.selectedThreadKey == selectedThreadKey)&&const DeepCollectionEquality().equals(other.processes, processes)&&const DeepCollectionEquality().equals(other.statusBlocks, statusBlocks)&&(identical(other.emptyMessage, emptyMessage) || other.emptyMessage == emptyMessage)&&const DeepCollectionEquality().equals(other.provenance, provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,environmentId,title,status,ready,selectedProcessId,selectedProcessKey,selectedThreadId,selectedThreadKey,const DeepCollectionEquality().hash(processes),const DeepCollectionEquality().hash(statusBlocks),emptyMessage,const DeepCollectionEquality().hash(provenance));

@override
String toString() {
  return 'EnvironmentNavigatorViewStateV1(environmentId: $environmentId, title: $title, status: $status, ready: $ready, selectedProcessId: $selectedProcessId, selectedProcessKey: $selectedProcessKey, selectedThreadId: $selectedThreadId, selectedThreadKey: $selectedThreadKey, processes: $processes, statusBlocks: $statusBlocks, emptyMessage: $emptyMessage, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class $EnvironmentNavigatorViewStateV1CopyWith<$Res>  {
  factory $EnvironmentNavigatorViewStateV1CopyWith(EnvironmentNavigatorViewStateV1 value, $Res Function(EnvironmentNavigatorViewStateV1) _then) = _$EnvironmentNavigatorViewStateV1CopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? environmentId, String title, String status, bool ready,@UuidValueConverter() UuidValue? selectedProcessId, String? selectedProcessKey,@UuidValueConverter() UuidValue? selectedThreadId, String? selectedThreadKey, List<EnvironmentProcessNavigationItemV1> processes, List<EnvironmentStatusBlockSummaryV1> statusBlocks, String emptyMessage, Map<String, dynamic> provenance
});




}
/// @nodoc
class _$EnvironmentNavigatorViewStateV1CopyWithImpl<$Res>
    implements $EnvironmentNavigatorViewStateV1CopyWith<$Res> {
  _$EnvironmentNavigatorViewStateV1CopyWithImpl(this._self, this._then);

  final EnvironmentNavigatorViewStateV1 _self;
  final $Res Function(EnvironmentNavigatorViewStateV1) _then;

/// Create a copy of EnvironmentNavigatorViewStateV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? environmentId = freezed,Object? title = null,Object? status = null,Object? ready = null,Object? selectedProcessId = freezed,Object? selectedProcessKey = freezed,Object? selectedThreadId = freezed,Object? selectedThreadKey = freezed,Object? processes = null,Object? statusBlocks = null,Object? emptyMessage = null,Object? provenance = null,}) {
  return _then(_self.copyWith(
environmentId: freezed == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,title: null == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,ready: null == ready ? _self.ready : ready // ignore: cast_nullable_to_non_nullable
as bool,selectedProcessId: freezed == selectedProcessId ? _self.selectedProcessId : selectedProcessId // ignore: cast_nullable_to_non_nullable
as UuidValue?,selectedProcessKey: freezed == selectedProcessKey ? _self.selectedProcessKey : selectedProcessKey // ignore: cast_nullable_to_non_nullable
as String?,selectedThreadId: freezed == selectedThreadId ? _self.selectedThreadId : selectedThreadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,selectedThreadKey: freezed == selectedThreadKey ? _self.selectedThreadKey : selectedThreadKey // ignore: cast_nullable_to_non_nullable
as String?,processes: null == processes ? _self.processes : processes // ignore: cast_nullable_to_non_nullable
as List<EnvironmentProcessNavigationItemV1>,statusBlocks: null == statusBlocks ? _self.statusBlocks : statusBlocks // ignore: cast_nullable_to_non_nullable
as List<EnvironmentStatusBlockSummaryV1>,emptyMessage: null == emptyMessage ? _self.emptyMessage : emptyMessage // ignore: cast_nullable_to_non_nullable
as String,provenance: null == provenance ? _self.provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [EnvironmentNavigatorViewStateV1].
extension EnvironmentNavigatorViewStateV1Patterns on EnvironmentNavigatorViewStateV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _EnvironmentNavigatorViewStateV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _EnvironmentNavigatorViewStateV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _EnvironmentNavigatorViewStateV1 value)  def,}){
final _that = this;
switch (_that) {
case _EnvironmentNavigatorViewStateV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _EnvironmentNavigatorViewStateV1 value)?  def,}){
final _that = this;
switch (_that) {
case _EnvironmentNavigatorViewStateV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? environmentId,  String title,  String status,  bool ready, @UuidValueConverter()  UuidValue? selectedProcessId,  String? selectedProcessKey, @UuidValueConverter()  UuidValue? selectedThreadId,  String? selectedThreadKey,  List<EnvironmentProcessNavigationItemV1> processes,  List<EnvironmentStatusBlockSummaryV1> statusBlocks,  String emptyMessage,  Map<String, dynamic> provenance)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _EnvironmentNavigatorViewStateV1() when def != null:
return def(_that.environmentId,_that.title,_that.status,_that.ready,_that.selectedProcessId,_that.selectedProcessKey,_that.selectedThreadId,_that.selectedThreadKey,_that.processes,_that.statusBlocks,_that.emptyMessage,_that.provenance);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? environmentId,  String title,  String status,  bool ready, @UuidValueConverter()  UuidValue? selectedProcessId,  String? selectedProcessKey, @UuidValueConverter()  UuidValue? selectedThreadId,  String? selectedThreadKey,  List<EnvironmentProcessNavigationItemV1> processes,  List<EnvironmentStatusBlockSummaryV1> statusBlocks,  String emptyMessage,  Map<String, dynamic> provenance)  def,}) {final _that = this;
switch (_that) {
case _EnvironmentNavigatorViewStateV1():
return def(_that.environmentId,_that.title,_that.status,_that.ready,_that.selectedProcessId,_that.selectedProcessKey,_that.selectedThreadId,_that.selectedThreadKey,_that.processes,_that.statusBlocks,_that.emptyMessage,_that.provenance);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? environmentId,  String title,  String status,  bool ready, @UuidValueConverter()  UuidValue? selectedProcessId,  String? selectedProcessKey, @UuidValueConverter()  UuidValue? selectedThreadId,  String? selectedThreadKey,  List<EnvironmentProcessNavigationItemV1> processes,  List<EnvironmentStatusBlockSummaryV1> statusBlocks,  String emptyMessage,  Map<String, dynamic> provenance)?  def,}) {final _that = this;
switch (_that) {
case _EnvironmentNavigatorViewStateV1() when def != null:
return def(_that.environmentId,_that.title,_that.status,_that.ready,_that.selectedProcessId,_that.selectedProcessKey,_that.selectedThreadId,_that.selectedThreadKey,_that.processes,_that.statusBlocks,_that.emptyMessage,_that.provenance);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _EnvironmentNavigatorViewStateV1 implements EnvironmentNavigatorViewStateV1 {
   _EnvironmentNavigatorViewStateV1({@UuidValueConverter() this.environmentId, required this.title, required this.status, required this.ready, @UuidValueConverter() this.selectedProcessId, this.selectedProcessKey, @UuidValueConverter() this.selectedThreadId, this.selectedThreadKey, final  List<EnvironmentProcessNavigationItemV1> processes = const [], final  List<EnvironmentStatusBlockSummaryV1> statusBlocks = const [], required this.emptyMessage, required final  Map<String, dynamic> provenance}): _processes = processes,_statusBlocks = statusBlocks,_provenance = provenance;
  factory _EnvironmentNavigatorViewStateV1.fromJson(Map<String, dynamic> json) => _$EnvironmentNavigatorViewStateV1FromJson(json);

@override@UuidValueConverter() final  UuidValue? environmentId;
@override final  String title;
@override final  String status;
@override final  bool ready;
@override@UuidValueConverter() final  UuidValue? selectedProcessId;
@override final  String? selectedProcessKey;
@override@UuidValueConverter() final  UuidValue? selectedThreadId;
@override final  String? selectedThreadKey;
 final  List<EnvironmentProcessNavigationItemV1> _processes;
@override@JsonKey() List<EnvironmentProcessNavigationItemV1> get processes {
  if (_processes is EqualUnmodifiableListView) return _processes;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_processes);
}

 final  List<EnvironmentStatusBlockSummaryV1> _statusBlocks;
@override@JsonKey() List<EnvironmentStatusBlockSummaryV1> get statusBlocks {
  if (_statusBlocks is EqualUnmodifiableListView) return _statusBlocks;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_statusBlocks);
}

@override final  String emptyMessage;
 final  Map<String, dynamic> _provenance;
@override Map<String, dynamic> get provenance {
  if (_provenance is EqualUnmodifiableMapView) return _provenance;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_provenance);
}


/// Create a copy of EnvironmentNavigatorViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$EnvironmentNavigatorViewStateV1CopyWith<_EnvironmentNavigatorViewStateV1> get copyWith => __$EnvironmentNavigatorViewStateV1CopyWithImpl<_EnvironmentNavigatorViewStateV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$EnvironmentNavigatorViewStateV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _EnvironmentNavigatorViewStateV1&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.title, title) || other.title == title)&&(identical(other.status, status) || other.status == status)&&(identical(other.ready, ready) || other.ready == ready)&&(identical(other.selectedProcessId, selectedProcessId) || other.selectedProcessId == selectedProcessId)&&(identical(other.selectedProcessKey, selectedProcessKey) || other.selectedProcessKey == selectedProcessKey)&&(identical(other.selectedThreadId, selectedThreadId) || other.selectedThreadId == selectedThreadId)&&(identical(other.selectedThreadKey, selectedThreadKey) || other.selectedThreadKey == selectedThreadKey)&&const DeepCollectionEquality().equals(other._processes, _processes)&&const DeepCollectionEquality().equals(other._statusBlocks, _statusBlocks)&&(identical(other.emptyMessage, emptyMessage) || other.emptyMessage == emptyMessage)&&const DeepCollectionEquality().equals(other._provenance, _provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,environmentId,title,status,ready,selectedProcessId,selectedProcessKey,selectedThreadId,selectedThreadKey,const DeepCollectionEquality().hash(_processes),const DeepCollectionEquality().hash(_statusBlocks),emptyMessage,const DeepCollectionEquality().hash(_provenance));

@override
String toString() {
  return 'EnvironmentNavigatorViewStateV1.def(environmentId: $environmentId, title: $title, status: $status, ready: $ready, selectedProcessId: $selectedProcessId, selectedProcessKey: $selectedProcessKey, selectedThreadId: $selectedThreadId, selectedThreadKey: $selectedThreadKey, processes: $processes, statusBlocks: $statusBlocks, emptyMessage: $emptyMessage, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class _$EnvironmentNavigatorViewStateV1CopyWith<$Res> implements $EnvironmentNavigatorViewStateV1CopyWith<$Res> {
  factory _$EnvironmentNavigatorViewStateV1CopyWith(_EnvironmentNavigatorViewStateV1 value, $Res Function(_EnvironmentNavigatorViewStateV1) _then) = __$EnvironmentNavigatorViewStateV1CopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? environmentId, String title, String status, bool ready,@UuidValueConverter() UuidValue? selectedProcessId, String? selectedProcessKey,@UuidValueConverter() UuidValue? selectedThreadId, String? selectedThreadKey, List<EnvironmentProcessNavigationItemV1> processes, List<EnvironmentStatusBlockSummaryV1> statusBlocks, String emptyMessage, Map<String, dynamic> provenance
});




}
/// @nodoc
class __$EnvironmentNavigatorViewStateV1CopyWithImpl<$Res>
    implements _$EnvironmentNavigatorViewStateV1CopyWith<$Res> {
  __$EnvironmentNavigatorViewStateV1CopyWithImpl(this._self, this._then);

  final _EnvironmentNavigatorViewStateV1 _self;
  final $Res Function(_EnvironmentNavigatorViewStateV1) _then;

/// Create a copy of EnvironmentNavigatorViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? environmentId = freezed,Object? title = null,Object? status = null,Object? ready = null,Object? selectedProcessId = freezed,Object? selectedProcessKey = freezed,Object? selectedThreadId = freezed,Object? selectedThreadKey = freezed,Object? processes = null,Object? statusBlocks = null,Object? emptyMessage = null,Object? provenance = null,}) {
  return _then(_EnvironmentNavigatorViewStateV1(
environmentId: freezed == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,title: null == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,ready: null == ready ? _self.ready : ready // ignore: cast_nullable_to_non_nullable
as bool,selectedProcessId: freezed == selectedProcessId ? _self.selectedProcessId : selectedProcessId // ignore: cast_nullable_to_non_nullable
as UuidValue?,selectedProcessKey: freezed == selectedProcessKey ? _self.selectedProcessKey : selectedProcessKey // ignore: cast_nullable_to_non_nullable
as String?,selectedThreadId: freezed == selectedThreadId ? _self.selectedThreadId : selectedThreadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,selectedThreadKey: freezed == selectedThreadKey ? _self.selectedThreadKey : selectedThreadKey // ignore: cast_nullable_to_non_nullable
as String?,processes: null == processes ? _self._processes : processes // ignore: cast_nullable_to_non_nullable
as List<EnvironmentProcessNavigationItemV1>,statusBlocks: null == statusBlocks ? _self._statusBlocks : statusBlocks // ignore: cast_nullable_to_non_nullable
as List<EnvironmentStatusBlockSummaryV1>,emptyMessage: null == emptyMessage ? _self.emptyMessage : emptyMessage // ignore: cast_nullable_to_non_nullable
as String,provenance: null == provenance ? _self._provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$ProcessWorkspaceThreadViewStateV1 {

@UuidValueConverter() UuidValue? get threadId; String? get threadKey; String get title; String? get description; int get attachmentCount; int get activeAttachmentCount; int get laneCount; int get layoutCount; bool get isSelected;
/// Create a copy of ProcessWorkspaceThreadViewStateV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ProcessWorkspaceThreadViewStateV1CopyWith<ProcessWorkspaceThreadViewStateV1> get copyWith => _$ProcessWorkspaceThreadViewStateV1CopyWithImpl<ProcessWorkspaceThreadViewStateV1>(this as ProcessWorkspaceThreadViewStateV1, _$identity);

  /// Serializes this ProcessWorkspaceThreadViewStateV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ProcessWorkspaceThreadViewStateV1&&(identical(other.threadId, threadId) || other.threadId == threadId)&&(identical(other.threadKey, threadKey) || other.threadKey == threadKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.attachmentCount, attachmentCount) || other.attachmentCount == attachmentCount)&&(identical(other.activeAttachmentCount, activeAttachmentCount) || other.activeAttachmentCount == activeAttachmentCount)&&(identical(other.laneCount, laneCount) || other.laneCount == laneCount)&&(identical(other.layoutCount, layoutCount) || other.layoutCount == layoutCount)&&(identical(other.isSelected, isSelected) || other.isSelected == isSelected));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,threadId,threadKey,title,description,attachmentCount,activeAttachmentCount,laneCount,layoutCount,isSelected);

@override
String toString() {
  return 'ProcessWorkspaceThreadViewStateV1(threadId: $threadId, threadKey: $threadKey, title: $title, description: $description, attachmentCount: $attachmentCount, activeAttachmentCount: $activeAttachmentCount, laneCount: $laneCount, layoutCount: $layoutCount, isSelected: $isSelected)';
}


}

/// @nodoc
abstract mixin class $ProcessWorkspaceThreadViewStateV1CopyWith<$Res>  {
  factory $ProcessWorkspaceThreadViewStateV1CopyWith(ProcessWorkspaceThreadViewStateV1 value, $Res Function(ProcessWorkspaceThreadViewStateV1) _then) = _$ProcessWorkspaceThreadViewStateV1CopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? threadId, String? threadKey, String title, String? description, int attachmentCount, int activeAttachmentCount, int laneCount, int layoutCount, bool isSelected
});




}
/// @nodoc
class _$ProcessWorkspaceThreadViewStateV1CopyWithImpl<$Res>
    implements $ProcessWorkspaceThreadViewStateV1CopyWith<$Res> {
  _$ProcessWorkspaceThreadViewStateV1CopyWithImpl(this._self, this._then);

  final ProcessWorkspaceThreadViewStateV1 _self;
  final $Res Function(ProcessWorkspaceThreadViewStateV1) _then;

/// Create a copy of ProcessWorkspaceThreadViewStateV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? threadId = freezed,Object? threadKey = freezed,Object? title = null,Object? description = freezed,Object? attachmentCount = null,Object? activeAttachmentCount = null,Object? laneCount = null,Object? layoutCount = null,Object? isSelected = null,}) {
  return _then(_self.copyWith(
threadId: freezed == threadId ? _self.threadId : threadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,threadKey: freezed == threadKey ? _self.threadKey : threadKey // ignore: cast_nullable_to_non_nullable
as String?,title: null == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,attachmentCount: null == attachmentCount ? _self.attachmentCount : attachmentCount // ignore: cast_nullable_to_non_nullable
as int,activeAttachmentCount: null == activeAttachmentCount ? _self.activeAttachmentCount : activeAttachmentCount // ignore: cast_nullable_to_non_nullable
as int,laneCount: null == laneCount ? _self.laneCount : laneCount // ignore: cast_nullable_to_non_nullable
as int,layoutCount: null == layoutCount ? _self.layoutCount : layoutCount // ignore: cast_nullable_to_non_nullable
as int,isSelected: null == isSelected ? _self.isSelected : isSelected // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}

}


/// Adds pattern-matching-related methods to [ProcessWorkspaceThreadViewStateV1].
extension ProcessWorkspaceThreadViewStateV1Patterns on ProcessWorkspaceThreadViewStateV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ProcessWorkspaceThreadViewStateV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ProcessWorkspaceThreadViewStateV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ProcessWorkspaceThreadViewStateV1 value)  def,}){
final _that = this;
switch (_that) {
case _ProcessWorkspaceThreadViewStateV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ProcessWorkspaceThreadViewStateV1 value)?  def,}){
final _that = this;
switch (_that) {
case _ProcessWorkspaceThreadViewStateV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? threadId,  String? threadKey,  String title,  String? description,  int attachmentCount,  int activeAttachmentCount,  int laneCount,  int layoutCount,  bool isSelected)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ProcessWorkspaceThreadViewStateV1() when def != null:
return def(_that.threadId,_that.threadKey,_that.title,_that.description,_that.attachmentCount,_that.activeAttachmentCount,_that.laneCount,_that.layoutCount,_that.isSelected);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? threadId,  String? threadKey,  String title,  String? description,  int attachmentCount,  int activeAttachmentCount,  int laneCount,  int layoutCount,  bool isSelected)  def,}) {final _that = this;
switch (_that) {
case _ProcessWorkspaceThreadViewStateV1():
return def(_that.threadId,_that.threadKey,_that.title,_that.description,_that.attachmentCount,_that.activeAttachmentCount,_that.laneCount,_that.layoutCount,_that.isSelected);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? threadId,  String? threadKey,  String title,  String? description,  int attachmentCount,  int activeAttachmentCount,  int laneCount,  int layoutCount,  bool isSelected)?  def,}) {final _that = this;
switch (_that) {
case _ProcessWorkspaceThreadViewStateV1() when def != null:
return def(_that.threadId,_that.threadKey,_that.title,_that.description,_that.attachmentCount,_that.activeAttachmentCount,_that.laneCount,_that.layoutCount,_that.isSelected);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ProcessWorkspaceThreadViewStateV1 implements ProcessWorkspaceThreadViewStateV1 {
   _ProcessWorkspaceThreadViewStateV1({@UuidValueConverter() this.threadId, this.threadKey, required this.title, this.description, required this.attachmentCount, required this.activeAttachmentCount, required this.laneCount, required this.layoutCount, required this.isSelected});
  factory _ProcessWorkspaceThreadViewStateV1.fromJson(Map<String, dynamic> json) => _$ProcessWorkspaceThreadViewStateV1FromJson(json);

@override@UuidValueConverter() final  UuidValue? threadId;
@override final  String? threadKey;
@override final  String title;
@override final  String? description;
@override final  int attachmentCount;
@override final  int activeAttachmentCount;
@override final  int laneCount;
@override final  int layoutCount;
@override final  bool isSelected;

/// Create a copy of ProcessWorkspaceThreadViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ProcessWorkspaceThreadViewStateV1CopyWith<_ProcessWorkspaceThreadViewStateV1> get copyWith => __$ProcessWorkspaceThreadViewStateV1CopyWithImpl<_ProcessWorkspaceThreadViewStateV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ProcessWorkspaceThreadViewStateV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ProcessWorkspaceThreadViewStateV1&&(identical(other.threadId, threadId) || other.threadId == threadId)&&(identical(other.threadKey, threadKey) || other.threadKey == threadKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.attachmentCount, attachmentCount) || other.attachmentCount == attachmentCount)&&(identical(other.activeAttachmentCount, activeAttachmentCount) || other.activeAttachmentCount == activeAttachmentCount)&&(identical(other.laneCount, laneCount) || other.laneCount == laneCount)&&(identical(other.layoutCount, layoutCount) || other.layoutCount == layoutCount)&&(identical(other.isSelected, isSelected) || other.isSelected == isSelected));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,threadId,threadKey,title,description,attachmentCount,activeAttachmentCount,laneCount,layoutCount,isSelected);

@override
String toString() {
  return 'ProcessWorkspaceThreadViewStateV1.def(threadId: $threadId, threadKey: $threadKey, title: $title, description: $description, attachmentCount: $attachmentCount, activeAttachmentCount: $activeAttachmentCount, laneCount: $laneCount, layoutCount: $layoutCount, isSelected: $isSelected)';
}


}

/// @nodoc
abstract mixin class _$ProcessWorkspaceThreadViewStateV1CopyWith<$Res> implements $ProcessWorkspaceThreadViewStateV1CopyWith<$Res> {
  factory _$ProcessWorkspaceThreadViewStateV1CopyWith(_ProcessWorkspaceThreadViewStateV1 value, $Res Function(_ProcessWorkspaceThreadViewStateV1) _then) = __$ProcessWorkspaceThreadViewStateV1CopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? threadId, String? threadKey, String title, String? description, int attachmentCount, int activeAttachmentCount, int laneCount, int layoutCount, bool isSelected
});




}
/// @nodoc
class __$ProcessWorkspaceThreadViewStateV1CopyWithImpl<$Res>
    implements _$ProcessWorkspaceThreadViewStateV1CopyWith<$Res> {
  __$ProcessWorkspaceThreadViewStateV1CopyWithImpl(this._self, this._then);

  final _ProcessWorkspaceThreadViewStateV1 _self;
  final $Res Function(_ProcessWorkspaceThreadViewStateV1) _then;

/// Create a copy of ProcessWorkspaceThreadViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? threadId = freezed,Object? threadKey = freezed,Object? title = null,Object? description = freezed,Object? attachmentCount = null,Object? activeAttachmentCount = null,Object? laneCount = null,Object? layoutCount = null,Object? isSelected = null,}) {
  return _then(_ProcessWorkspaceThreadViewStateV1(
threadId: freezed == threadId ? _self.threadId : threadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,threadKey: freezed == threadKey ? _self.threadKey : threadKey // ignore: cast_nullable_to_non_nullable
as String?,title: null == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,attachmentCount: null == attachmentCount ? _self.attachmentCount : attachmentCount // ignore: cast_nullable_to_non_nullable
as int,activeAttachmentCount: null == activeAttachmentCount ? _self.activeAttachmentCount : activeAttachmentCount // ignore: cast_nullable_to_non_nullable
as int,laneCount: null == laneCount ? _self.laneCount : laneCount // ignore: cast_nullable_to_non_nullable
as int,layoutCount: null == layoutCount ? _self.layoutCount : layoutCount // ignore: cast_nullable_to_non_nullable
as int,isSelected: null == isSelected ? _self.isSelected : isSelected // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}


}


/// @nodoc
mixin _$ProcessWorkspaceViewStateV1 {

@UuidValueConverter() UuidValue? get environmentId;@UuidValueConverter() UuidValue? get processId; String? get processKey; String get title; String? get description; String get status;@UuidValueConverter() UuidValue? get selectedThreadId; String? get selectedThreadKey; List<ProcessWorkspaceThreadViewStateV1> get threads; String get emptyMessage; Map<String, dynamic> get provenance;
/// Create a copy of ProcessWorkspaceViewStateV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ProcessWorkspaceViewStateV1CopyWith<ProcessWorkspaceViewStateV1> get copyWith => _$ProcessWorkspaceViewStateV1CopyWithImpl<ProcessWorkspaceViewStateV1>(this as ProcessWorkspaceViewStateV1, _$identity);

  /// Serializes this ProcessWorkspaceViewStateV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ProcessWorkspaceViewStateV1&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.processId, processId) || other.processId == processId)&&(identical(other.processKey, processKey) || other.processKey == processKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.status, status) || other.status == status)&&(identical(other.selectedThreadId, selectedThreadId) || other.selectedThreadId == selectedThreadId)&&(identical(other.selectedThreadKey, selectedThreadKey) || other.selectedThreadKey == selectedThreadKey)&&const DeepCollectionEquality().equals(other.threads, threads)&&(identical(other.emptyMessage, emptyMessage) || other.emptyMessage == emptyMessage)&&const DeepCollectionEquality().equals(other.provenance, provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,environmentId,processId,processKey,title,description,status,selectedThreadId,selectedThreadKey,const DeepCollectionEquality().hash(threads),emptyMessage,const DeepCollectionEquality().hash(provenance));

@override
String toString() {
  return 'ProcessWorkspaceViewStateV1(environmentId: $environmentId, processId: $processId, processKey: $processKey, title: $title, description: $description, status: $status, selectedThreadId: $selectedThreadId, selectedThreadKey: $selectedThreadKey, threads: $threads, emptyMessage: $emptyMessage, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class $ProcessWorkspaceViewStateV1CopyWith<$Res>  {
  factory $ProcessWorkspaceViewStateV1CopyWith(ProcessWorkspaceViewStateV1 value, $Res Function(ProcessWorkspaceViewStateV1) _then) = _$ProcessWorkspaceViewStateV1CopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? environmentId,@UuidValueConverter() UuidValue? processId, String? processKey, String title, String? description, String status,@UuidValueConverter() UuidValue? selectedThreadId, String? selectedThreadKey, List<ProcessWorkspaceThreadViewStateV1> threads, String emptyMessage, Map<String, dynamic> provenance
});




}
/// @nodoc
class _$ProcessWorkspaceViewStateV1CopyWithImpl<$Res>
    implements $ProcessWorkspaceViewStateV1CopyWith<$Res> {
  _$ProcessWorkspaceViewStateV1CopyWithImpl(this._self, this._then);

  final ProcessWorkspaceViewStateV1 _self;
  final $Res Function(ProcessWorkspaceViewStateV1) _then;

/// Create a copy of ProcessWorkspaceViewStateV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? environmentId = freezed,Object? processId = freezed,Object? processKey = freezed,Object? title = null,Object? description = freezed,Object? status = null,Object? selectedThreadId = freezed,Object? selectedThreadKey = freezed,Object? threads = null,Object? emptyMessage = null,Object? provenance = null,}) {
  return _then(_self.copyWith(
environmentId: freezed == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,processId: freezed == processId ? _self.processId : processId // ignore: cast_nullable_to_non_nullable
as UuidValue?,processKey: freezed == processKey ? _self.processKey : processKey // ignore: cast_nullable_to_non_nullable
as String?,title: null == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,selectedThreadId: freezed == selectedThreadId ? _self.selectedThreadId : selectedThreadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,selectedThreadKey: freezed == selectedThreadKey ? _self.selectedThreadKey : selectedThreadKey // ignore: cast_nullable_to_non_nullable
as String?,threads: null == threads ? _self.threads : threads // ignore: cast_nullable_to_non_nullable
as List<ProcessWorkspaceThreadViewStateV1>,emptyMessage: null == emptyMessage ? _self.emptyMessage : emptyMessage // ignore: cast_nullable_to_non_nullable
as String,provenance: null == provenance ? _self.provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [ProcessWorkspaceViewStateV1].
extension ProcessWorkspaceViewStateV1Patterns on ProcessWorkspaceViewStateV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ProcessWorkspaceViewStateV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ProcessWorkspaceViewStateV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ProcessWorkspaceViewStateV1 value)  def,}){
final _that = this;
switch (_that) {
case _ProcessWorkspaceViewStateV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ProcessWorkspaceViewStateV1 value)?  def,}){
final _that = this;
switch (_that) {
case _ProcessWorkspaceViewStateV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue? processId,  String? processKey,  String title,  String? description,  String status, @UuidValueConverter()  UuidValue? selectedThreadId,  String? selectedThreadKey,  List<ProcessWorkspaceThreadViewStateV1> threads,  String emptyMessage,  Map<String, dynamic> provenance)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ProcessWorkspaceViewStateV1() when def != null:
return def(_that.environmentId,_that.processId,_that.processKey,_that.title,_that.description,_that.status,_that.selectedThreadId,_that.selectedThreadKey,_that.threads,_that.emptyMessage,_that.provenance);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue? processId,  String? processKey,  String title,  String? description,  String status, @UuidValueConverter()  UuidValue? selectedThreadId,  String? selectedThreadKey,  List<ProcessWorkspaceThreadViewStateV1> threads,  String emptyMessage,  Map<String, dynamic> provenance)  def,}) {final _that = this;
switch (_that) {
case _ProcessWorkspaceViewStateV1():
return def(_that.environmentId,_that.processId,_that.processKey,_that.title,_that.description,_that.status,_that.selectedThreadId,_that.selectedThreadKey,_that.threads,_that.emptyMessage,_that.provenance);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue? processId,  String? processKey,  String title,  String? description,  String status, @UuidValueConverter()  UuidValue? selectedThreadId,  String? selectedThreadKey,  List<ProcessWorkspaceThreadViewStateV1> threads,  String emptyMessage,  Map<String, dynamic> provenance)?  def,}) {final _that = this;
switch (_that) {
case _ProcessWorkspaceViewStateV1() when def != null:
return def(_that.environmentId,_that.processId,_that.processKey,_that.title,_that.description,_that.status,_that.selectedThreadId,_that.selectedThreadKey,_that.threads,_that.emptyMessage,_that.provenance);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ProcessWorkspaceViewStateV1 implements ProcessWorkspaceViewStateV1 {
   _ProcessWorkspaceViewStateV1({@UuidValueConverter() this.environmentId, @UuidValueConverter() this.processId, this.processKey, required this.title, this.description, required this.status, @UuidValueConverter() this.selectedThreadId, this.selectedThreadKey, final  List<ProcessWorkspaceThreadViewStateV1> threads = const [], required this.emptyMessage, required final  Map<String, dynamic> provenance}): _threads = threads,_provenance = provenance;
  factory _ProcessWorkspaceViewStateV1.fromJson(Map<String, dynamic> json) => _$ProcessWorkspaceViewStateV1FromJson(json);

@override@UuidValueConverter() final  UuidValue? environmentId;
@override@UuidValueConverter() final  UuidValue? processId;
@override final  String? processKey;
@override final  String title;
@override final  String? description;
@override final  String status;
@override@UuidValueConverter() final  UuidValue? selectedThreadId;
@override final  String? selectedThreadKey;
 final  List<ProcessWorkspaceThreadViewStateV1> _threads;
@override@JsonKey() List<ProcessWorkspaceThreadViewStateV1> get threads {
  if (_threads is EqualUnmodifiableListView) return _threads;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_threads);
}

@override final  String emptyMessage;
 final  Map<String, dynamic> _provenance;
@override Map<String, dynamic> get provenance {
  if (_provenance is EqualUnmodifiableMapView) return _provenance;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_provenance);
}


/// Create a copy of ProcessWorkspaceViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ProcessWorkspaceViewStateV1CopyWith<_ProcessWorkspaceViewStateV1> get copyWith => __$ProcessWorkspaceViewStateV1CopyWithImpl<_ProcessWorkspaceViewStateV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ProcessWorkspaceViewStateV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ProcessWorkspaceViewStateV1&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.processId, processId) || other.processId == processId)&&(identical(other.processKey, processKey) || other.processKey == processKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.status, status) || other.status == status)&&(identical(other.selectedThreadId, selectedThreadId) || other.selectedThreadId == selectedThreadId)&&(identical(other.selectedThreadKey, selectedThreadKey) || other.selectedThreadKey == selectedThreadKey)&&const DeepCollectionEquality().equals(other._threads, _threads)&&(identical(other.emptyMessage, emptyMessage) || other.emptyMessage == emptyMessage)&&const DeepCollectionEquality().equals(other._provenance, _provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,environmentId,processId,processKey,title,description,status,selectedThreadId,selectedThreadKey,const DeepCollectionEquality().hash(_threads),emptyMessage,const DeepCollectionEquality().hash(_provenance));

@override
String toString() {
  return 'ProcessWorkspaceViewStateV1.def(environmentId: $environmentId, processId: $processId, processKey: $processKey, title: $title, description: $description, status: $status, selectedThreadId: $selectedThreadId, selectedThreadKey: $selectedThreadKey, threads: $threads, emptyMessage: $emptyMessage, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class _$ProcessWorkspaceViewStateV1CopyWith<$Res> implements $ProcessWorkspaceViewStateV1CopyWith<$Res> {
  factory _$ProcessWorkspaceViewStateV1CopyWith(_ProcessWorkspaceViewStateV1 value, $Res Function(_ProcessWorkspaceViewStateV1) _then) = __$ProcessWorkspaceViewStateV1CopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? environmentId,@UuidValueConverter() UuidValue? processId, String? processKey, String title, String? description, String status,@UuidValueConverter() UuidValue? selectedThreadId, String? selectedThreadKey, List<ProcessWorkspaceThreadViewStateV1> threads, String emptyMessage, Map<String, dynamic> provenance
});




}
/// @nodoc
class __$ProcessWorkspaceViewStateV1CopyWithImpl<$Res>
    implements _$ProcessWorkspaceViewStateV1CopyWith<$Res> {
  __$ProcessWorkspaceViewStateV1CopyWithImpl(this._self, this._then);

  final _ProcessWorkspaceViewStateV1 _self;
  final $Res Function(_ProcessWorkspaceViewStateV1) _then;

/// Create a copy of ProcessWorkspaceViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? environmentId = freezed,Object? processId = freezed,Object? processKey = freezed,Object? title = null,Object? description = freezed,Object? status = null,Object? selectedThreadId = freezed,Object? selectedThreadKey = freezed,Object? threads = null,Object? emptyMessage = null,Object? provenance = null,}) {
  return _then(_ProcessWorkspaceViewStateV1(
environmentId: freezed == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,processId: freezed == processId ? _self.processId : processId // ignore: cast_nullable_to_non_nullable
as UuidValue?,processKey: freezed == processKey ? _self.processKey : processKey // ignore: cast_nullable_to_non_nullable
as String?,title: null == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,selectedThreadId: freezed == selectedThreadId ? _self.selectedThreadId : selectedThreadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,selectedThreadKey: freezed == selectedThreadKey ? _self.selectedThreadKey : selectedThreadKey // ignore: cast_nullable_to_non_nullable
as String?,threads: null == threads ? _self._threads : threads // ignore: cast_nullable_to_non_nullable
as List<ProcessWorkspaceThreadViewStateV1>,emptyMessage: null == emptyMessage ? _self.emptyMessage : emptyMessage // ignore: cast_nullable_to_non_nullable
as String,provenance: null == provenance ? _self._provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$ThreadLayoutLaneViewStateV1 {

 String get laneHash;@UuidValueConverter() UuidValue? get opgId; String? get opgName;
/// Create a copy of ThreadLayoutLaneViewStateV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ThreadLayoutLaneViewStateV1CopyWith<ThreadLayoutLaneViewStateV1> get copyWith => _$ThreadLayoutLaneViewStateV1CopyWithImpl<ThreadLayoutLaneViewStateV1>(this as ThreadLayoutLaneViewStateV1, _$identity);

  /// Serializes this ThreadLayoutLaneViewStateV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ThreadLayoutLaneViewStateV1&&(identical(other.laneHash, laneHash) || other.laneHash == laneHash)&&(identical(other.opgId, opgId) || other.opgId == opgId)&&(identical(other.opgName, opgName) || other.opgName == opgName));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,laneHash,opgId,opgName);

@override
String toString() {
  return 'ThreadLayoutLaneViewStateV1(laneHash: $laneHash, opgId: $opgId, opgName: $opgName)';
}


}

/// @nodoc
abstract mixin class $ThreadLayoutLaneViewStateV1CopyWith<$Res>  {
  factory $ThreadLayoutLaneViewStateV1CopyWith(ThreadLayoutLaneViewStateV1 value, $Res Function(ThreadLayoutLaneViewStateV1) _then) = _$ThreadLayoutLaneViewStateV1CopyWithImpl;
@useResult
$Res call({
 String laneHash,@UuidValueConverter() UuidValue? opgId, String? opgName
});




}
/// @nodoc
class _$ThreadLayoutLaneViewStateV1CopyWithImpl<$Res>
    implements $ThreadLayoutLaneViewStateV1CopyWith<$Res> {
  _$ThreadLayoutLaneViewStateV1CopyWithImpl(this._self, this._then);

  final ThreadLayoutLaneViewStateV1 _self;
  final $Res Function(ThreadLayoutLaneViewStateV1) _then;

/// Create a copy of ThreadLayoutLaneViewStateV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? laneHash = null,Object? opgId = freezed,Object? opgName = freezed,}) {
  return _then(_self.copyWith(
laneHash: null == laneHash ? _self.laneHash : laneHash // ignore: cast_nullable_to_non_nullable
as String,opgId: freezed == opgId ? _self.opgId : opgId // ignore: cast_nullable_to_non_nullable
as UuidValue?,opgName: freezed == opgName ? _self.opgName : opgName // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [ThreadLayoutLaneViewStateV1].
extension ThreadLayoutLaneViewStateV1Patterns on ThreadLayoutLaneViewStateV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ThreadLayoutLaneViewStateV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ThreadLayoutLaneViewStateV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ThreadLayoutLaneViewStateV1 value)  def,}){
final _that = this;
switch (_that) {
case _ThreadLayoutLaneViewStateV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ThreadLayoutLaneViewStateV1 value)?  def,}){
final _that = this;
switch (_that) {
case _ThreadLayoutLaneViewStateV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String laneHash, @UuidValueConverter()  UuidValue? opgId,  String? opgName)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ThreadLayoutLaneViewStateV1() when def != null:
return def(_that.laneHash,_that.opgId,_that.opgName);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String laneHash, @UuidValueConverter()  UuidValue? opgId,  String? opgName)  def,}) {final _that = this;
switch (_that) {
case _ThreadLayoutLaneViewStateV1():
return def(_that.laneHash,_that.opgId,_that.opgName);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String laneHash, @UuidValueConverter()  UuidValue? opgId,  String? opgName)?  def,}) {final _that = this;
switch (_that) {
case _ThreadLayoutLaneViewStateV1() when def != null:
return def(_that.laneHash,_that.opgId,_that.opgName);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ThreadLayoutLaneViewStateV1 implements ThreadLayoutLaneViewStateV1 {
   _ThreadLayoutLaneViewStateV1({required this.laneHash, @UuidValueConverter() this.opgId, this.opgName});
  factory _ThreadLayoutLaneViewStateV1.fromJson(Map<String, dynamic> json) => _$ThreadLayoutLaneViewStateV1FromJson(json);

@override final  String laneHash;
@override@UuidValueConverter() final  UuidValue? opgId;
@override final  String? opgName;

/// Create a copy of ThreadLayoutLaneViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ThreadLayoutLaneViewStateV1CopyWith<_ThreadLayoutLaneViewStateV1> get copyWith => __$ThreadLayoutLaneViewStateV1CopyWithImpl<_ThreadLayoutLaneViewStateV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ThreadLayoutLaneViewStateV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ThreadLayoutLaneViewStateV1&&(identical(other.laneHash, laneHash) || other.laneHash == laneHash)&&(identical(other.opgId, opgId) || other.opgId == opgId)&&(identical(other.opgName, opgName) || other.opgName == opgName));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,laneHash,opgId,opgName);

@override
String toString() {
  return 'ThreadLayoutLaneViewStateV1.def(laneHash: $laneHash, opgId: $opgId, opgName: $opgName)';
}


}

/// @nodoc
abstract mixin class _$ThreadLayoutLaneViewStateV1CopyWith<$Res> implements $ThreadLayoutLaneViewStateV1CopyWith<$Res> {
  factory _$ThreadLayoutLaneViewStateV1CopyWith(_ThreadLayoutLaneViewStateV1 value, $Res Function(_ThreadLayoutLaneViewStateV1) _then) = __$ThreadLayoutLaneViewStateV1CopyWithImpl;
@override @useResult
$Res call({
 String laneHash,@UuidValueConverter() UuidValue? opgId, String? opgName
});




}
/// @nodoc
class __$ThreadLayoutLaneViewStateV1CopyWithImpl<$Res>
    implements _$ThreadLayoutLaneViewStateV1CopyWith<$Res> {
  __$ThreadLayoutLaneViewStateV1CopyWithImpl(this._self, this._then);

  final _ThreadLayoutLaneViewStateV1 _self;
  final $Res Function(_ThreadLayoutLaneViewStateV1) _then;

/// Create a copy of ThreadLayoutLaneViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? laneHash = null,Object? opgId = freezed,Object? opgName = freezed,}) {
  return _then(_ThreadLayoutLaneViewStateV1(
laneHash: null == laneHash ? _self.laneHash : laneHash // ignore: cast_nullable_to_non_nullable
as String,opgId: freezed == opgId ? _self.opgId : opgId // ignore: cast_nullable_to_non_nullable
as UuidValue?,opgName: freezed == opgName ? _self.opgName : opgName // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$ThreadLayoutAttachmentViewStateV1 {

@UuidValueConverter() UuidValue? get attachmentId; String? get title; bool get isActive;@UuidValueConverter() UuidValue? get objectInstanceGraphBranchId;@UuidValueConverter() UuidValue? get objectInstanceGraphIdentityId;@UuidValueConverter() UuidValue? get domainBranchId; List<ThreadLayoutLaneViewStateV1> get lanes;
/// Create a copy of ThreadLayoutAttachmentViewStateV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ThreadLayoutAttachmentViewStateV1CopyWith<ThreadLayoutAttachmentViewStateV1> get copyWith => _$ThreadLayoutAttachmentViewStateV1CopyWithImpl<ThreadLayoutAttachmentViewStateV1>(this as ThreadLayoutAttachmentViewStateV1, _$identity);

  /// Serializes this ThreadLayoutAttachmentViewStateV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ThreadLayoutAttachmentViewStateV1&&(identical(other.attachmentId, attachmentId) || other.attachmentId == attachmentId)&&(identical(other.title, title) || other.title == title)&&(identical(other.isActive, isActive) || other.isActive == isActive)&&(identical(other.objectInstanceGraphBranchId, objectInstanceGraphBranchId) || other.objectInstanceGraphBranchId == objectInstanceGraphBranchId)&&(identical(other.objectInstanceGraphIdentityId, objectInstanceGraphIdentityId) || other.objectInstanceGraphIdentityId == objectInstanceGraphIdentityId)&&(identical(other.domainBranchId, domainBranchId) || other.domainBranchId == domainBranchId)&&const DeepCollectionEquality().equals(other.lanes, lanes));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,attachmentId,title,isActive,objectInstanceGraphBranchId,objectInstanceGraphIdentityId,domainBranchId,const DeepCollectionEquality().hash(lanes));

@override
String toString() {
  return 'ThreadLayoutAttachmentViewStateV1(attachmentId: $attachmentId, title: $title, isActive: $isActive, objectInstanceGraphBranchId: $objectInstanceGraphBranchId, objectInstanceGraphIdentityId: $objectInstanceGraphIdentityId, domainBranchId: $domainBranchId, lanes: $lanes)';
}


}

/// @nodoc
abstract mixin class $ThreadLayoutAttachmentViewStateV1CopyWith<$Res>  {
  factory $ThreadLayoutAttachmentViewStateV1CopyWith(ThreadLayoutAttachmentViewStateV1 value, $Res Function(ThreadLayoutAttachmentViewStateV1) _then) = _$ThreadLayoutAttachmentViewStateV1CopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? attachmentId, String? title, bool isActive,@UuidValueConverter() UuidValue? objectInstanceGraphBranchId,@UuidValueConverter() UuidValue? objectInstanceGraphIdentityId,@UuidValueConverter() UuidValue? domainBranchId, List<ThreadLayoutLaneViewStateV1> lanes
});




}
/// @nodoc
class _$ThreadLayoutAttachmentViewStateV1CopyWithImpl<$Res>
    implements $ThreadLayoutAttachmentViewStateV1CopyWith<$Res> {
  _$ThreadLayoutAttachmentViewStateV1CopyWithImpl(this._self, this._then);

  final ThreadLayoutAttachmentViewStateV1 _self;
  final $Res Function(ThreadLayoutAttachmentViewStateV1) _then;

/// Create a copy of ThreadLayoutAttachmentViewStateV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? attachmentId = freezed,Object? title = freezed,Object? isActive = null,Object? objectInstanceGraphBranchId = freezed,Object? objectInstanceGraphIdentityId = freezed,Object? domainBranchId = freezed,Object? lanes = null,}) {
  return _then(_self.copyWith(
attachmentId: freezed == attachmentId ? _self.attachmentId : attachmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,isActive: null == isActive ? _self.isActive : isActive // ignore: cast_nullable_to_non_nullable
as bool,objectInstanceGraphBranchId: freezed == objectInstanceGraphBranchId ? _self.objectInstanceGraphBranchId : objectInstanceGraphBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphIdentityId: freezed == objectInstanceGraphIdentityId ? _self.objectInstanceGraphIdentityId : objectInstanceGraphIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue?,domainBranchId: freezed == domainBranchId ? _self.domainBranchId : domainBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,lanes: null == lanes ? _self.lanes : lanes // ignore: cast_nullable_to_non_nullable
as List<ThreadLayoutLaneViewStateV1>,
  ));
}

}


/// Adds pattern-matching-related methods to [ThreadLayoutAttachmentViewStateV1].
extension ThreadLayoutAttachmentViewStateV1Patterns on ThreadLayoutAttachmentViewStateV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ThreadLayoutAttachmentViewStateV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ThreadLayoutAttachmentViewStateV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ThreadLayoutAttachmentViewStateV1 value)  def,}){
final _that = this;
switch (_that) {
case _ThreadLayoutAttachmentViewStateV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ThreadLayoutAttachmentViewStateV1 value)?  def,}){
final _that = this;
switch (_that) {
case _ThreadLayoutAttachmentViewStateV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? attachmentId,  String? title,  bool isActive, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId, @UuidValueConverter()  UuidValue? objectInstanceGraphIdentityId, @UuidValueConverter()  UuidValue? domainBranchId,  List<ThreadLayoutLaneViewStateV1> lanes)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ThreadLayoutAttachmentViewStateV1() when def != null:
return def(_that.attachmentId,_that.title,_that.isActive,_that.objectInstanceGraphBranchId,_that.objectInstanceGraphIdentityId,_that.domainBranchId,_that.lanes);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? attachmentId,  String? title,  bool isActive, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId, @UuidValueConverter()  UuidValue? objectInstanceGraphIdentityId, @UuidValueConverter()  UuidValue? domainBranchId,  List<ThreadLayoutLaneViewStateV1> lanes)  def,}) {final _that = this;
switch (_that) {
case _ThreadLayoutAttachmentViewStateV1():
return def(_that.attachmentId,_that.title,_that.isActive,_that.objectInstanceGraphBranchId,_that.objectInstanceGraphIdentityId,_that.domainBranchId,_that.lanes);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? attachmentId,  String? title,  bool isActive, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId, @UuidValueConverter()  UuidValue? objectInstanceGraphIdentityId, @UuidValueConverter()  UuidValue? domainBranchId,  List<ThreadLayoutLaneViewStateV1> lanes)?  def,}) {final _that = this;
switch (_that) {
case _ThreadLayoutAttachmentViewStateV1() when def != null:
return def(_that.attachmentId,_that.title,_that.isActive,_that.objectInstanceGraphBranchId,_that.objectInstanceGraphIdentityId,_that.domainBranchId,_that.lanes);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ThreadLayoutAttachmentViewStateV1 implements ThreadLayoutAttachmentViewStateV1 {
   _ThreadLayoutAttachmentViewStateV1({@UuidValueConverter() this.attachmentId, this.title, required this.isActive, @UuidValueConverter() this.objectInstanceGraphBranchId, @UuidValueConverter() this.objectInstanceGraphIdentityId, @UuidValueConverter() this.domainBranchId, final  List<ThreadLayoutLaneViewStateV1> lanes = const []}): _lanes = lanes;
  factory _ThreadLayoutAttachmentViewStateV1.fromJson(Map<String, dynamic> json) => _$ThreadLayoutAttachmentViewStateV1FromJson(json);

@override@UuidValueConverter() final  UuidValue? attachmentId;
@override final  String? title;
@override final  bool isActive;
@override@UuidValueConverter() final  UuidValue? objectInstanceGraphBranchId;
@override@UuidValueConverter() final  UuidValue? objectInstanceGraphIdentityId;
@override@UuidValueConverter() final  UuidValue? domainBranchId;
 final  List<ThreadLayoutLaneViewStateV1> _lanes;
@override@JsonKey() List<ThreadLayoutLaneViewStateV1> get lanes {
  if (_lanes is EqualUnmodifiableListView) return _lanes;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_lanes);
}


/// Create a copy of ThreadLayoutAttachmentViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ThreadLayoutAttachmentViewStateV1CopyWith<_ThreadLayoutAttachmentViewStateV1> get copyWith => __$ThreadLayoutAttachmentViewStateV1CopyWithImpl<_ThreadLayoutAttachmentViewStateV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ThreadLayoutAttachmentViewStateV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ThreadLayoutAttachmentViewStateV1&&(identical(other.attachmentId, attachmentId) || other.attachmentId == attachmentId)&&(identical(other.title, title) || other.title == title)&&(identical(other.isActive, isActive) || other.isActive == isActive)&&(identical(other.objectInstanceGraphBranchId, objectInstanceGraphBranchId) || other.objectInstanceGraphBranchId == objectInstanceGraphBranchId)&&(identical(other.objectInstanceGraphIdentityId, objectInstanceGraphIdentityId) || other.objectInstanceGraphIdentityId == objectInstanceGraphIdentityId)&&(identical(other.domainBranchId, domainBranchId) || other.domainBranchId == domainBranchId)&&const DeepCollectionEquality().equals(other._lanes, _lanes));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,attachmentId,title,isActive,objectInstanceGraphBranchId,objectInstanceGraphIdentityId,domainBranchId,const DeepCollectionEquality().hash(_lanes));

@override
String toString() {
  return 'ThreadLayoutAttachmentViewStateV1.def(attachmentId: $attachmentId, title: $title, isActive: $isActive, objectInstanceGraphBranchId: $objectInstanceGraphBranchId, objectInstanceGraphIdentityId: $objectInstanceGraphIdentityId, domainBranchId: $domainBranchId, lanes: $lanes)';
}


}

/// @nodoc
abstract mixin class _$ThreadLayoutAttachmentViewStateV1CopyWith<$Res> implements $ThreadLayoutAttachmentViewStateV1CopyWith<$Res> {
  factory _$ThreadLayoutAttachmentViewStateV1CopyWith(_ThreadLayoutAttachmentViewStateV1 value, $Res Function(_ThreadLayoutAttachmentViewStateV1) _then) = __$ThreadLayoutAttachmentViewStateV1CopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? attachmentId, String? title, bool isActive,@UuidValueConverter() UuidValue? objectInstanceGraphBranchId,@UuidValueConverter() UuidValue? objectInstanceGraphIdentityId,@UuidValueConverter() UuidValue? domainBranchId, List<ThreadLayoutLaneViewStateV1> lanes
});




}
/// @nodoc
class __$ThreadLayoutAttachmentViewStateV1CopyWithImpl<$Res>
    implements _$ThreadLayoutAttachmentViewStateV1CopyWith<$Res> {
  __$ThreadLayoutAttachmentViewStateV1CopyWithImpl(this._self, this._then);

  final _ThreadLayoutAttachmentViewStateV1 _self;
  final $Res Function(_ThreadLayoutAttachmentViewStateV1) _then;

/// Create a copy of ThreadLayoutAttachmentViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? attachmentId = freezed,Object? title = freezed,Object? isActive = null,Object? objectInstanceGraphBranchId = freezed,Object? objectInstanceGraphIdentityId = freezed,Object? domainBranchId = freezed,Object? lanes = null,}) {
  return _then(_ThreadLayoutAttachmentViewStateV1(
attachmentId: freezed == attachmentId ? _self.attachmentId : attachmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,isActive: null == isActive ? _self.isActive : isActive // ignore: cast_nullable_to_non_nullable
as bool,objectInstanceGraphBranchId: freezed == objectInstanceGraphBranchId ? _self.objectInstanceGraphBranchId : objectInstanceGraphBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphIdentityId: freezed == objectInstanceGraphIdentityId ? _self.objectInstanceGraphIdentityId : objectInstanceGraphIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue?,domainBranchId: freezed == domainBranchId ? _self.domainBranchId : domainBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,lanes: null == lanes ? _self._lanes : lanes // ignore: cast_nullable_to_non_nullable
as List<ThreadLayoutLaneViewStateV1>,
  ));
}


}


/// @nodoc
mixin _$ThreadLayoutSectionViewStateV1 {

 String get sectionKey; String get title; String? get description; int get order; double get flex; bool get isVisible;@UuidValueConverter() UuidValue? get focusScopeId; String? get viewRef; String? get viewKey; String? get packageName; String? get paneKey;
/// Create a copy of ThreadLayoutSectionViewStateV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ThreadLayoutSectionViewStateV1CopyWith<ThreadLayoutSectionViewStateV1> get copyWith => _$ThreadLayoutSectionViewStateV1CopyWithImpl<ThreadLayoutSectionViewStateV1>(this as ThreadLayoutSectionViewStateV1, _$identity);

  /// Serializes this ThreadLayoutSectionViewStateV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ThreadLayoutSectionViewStateV1&&(identical(other.sectionKey, sectionKey) || other.sectionKey == sectionKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.order, order) || other.order == order)&&(identical(other.flex, flex) || other.flex == flex)&&(identical(other.isVisible, isVisible) || other.isVisible == isVisible)&&(identical(other.focusScopeId, focusScopeId) || other.focusScopeId == focusScopeId)&&(identical(other.viewRef, viewRef) || other.viewRef == viewRef)&&(identical(other.viewKey, viewKey) || other.viewKey == viewKey)&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.paneKey, paneKey) || other.paneKey == paneKey));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,sectionKey,title,description,order,flex,isVisible,focusScopeId,viewRef,viewKey,packageName,paneKey);

@override
String toString() {
  return 'ThreadLayoutSectionViewStateV1(sectionKey: $sectionKey, title: $title, description: $description, order: $order, flex: $flex, isVisible: $isVisible, focusScopeId: $focusScopeId, viewRef: $viewRef, viewKey: $viewKey, packageName: $packageName, paneKey: $paneKey)';
}


}

/// @nodoc
abstract mixin class $ThreadLayoutSectionViewStateV1CopyWith<$Res>  {
  factory $ThreadLayoutSectionViewStateV1CopyWith(ThreadLayoutSectionViewStateV1 value, $Res Function(ThreadLayoutSectionViewStateV1) _then) = _$ThreadLayoutSectionViewStateV1CopyWithImpl;
@useResult
$Res call({
 String sectionKey, String title, String? description, int order, double flex, bool isVisible,@UuidValueConverter() UuidValue? focusScopeId, String? viewRef, String? viewKey, String? packageName, String? paneKey
});




}
/// @nodoc
class _$ThreadLayoutSectionViewStateV1CopyWithImpl<$Res>
    implements $ThreadLayoutSectionViewStateV1CopyWith<$Res> {
  _$ThreadLayoutSectionViewStateV1CopyWithImpl(this._self, this._then);

  final ThreadLayoutSectionViewStateV1 _self;
  final $Res Function(ThreadLayoutSectionViewStateV1) _then;

/// Create a copy of ThreadLayoutSectionViewStateV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? sectionKey = null,Object? title = null,Object? description = freezed,Object? order = null,Object? flex = null,Object? isVisible = null,Object? focusScopeId = freezed,Object? viewRef = freezed,Object? viewKey = freezed,Object? packageName = freezed,Object? paneKey = freezed,}) {
  return _then(_self.copyWith(
sectionKey: null == sectionKey ? _self.sectionKey : sectionKey // ignore: cast_nullable_to_non_nullable
as String,title: null == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,order: null == order ? _self.order : order // ignore: cast_nullable_to_non_nullable
as int,flex: null == flex ? _self.flex : flex // ignore: cast_nullable_to_non_nullable
as double,isVisible: null == isVisible ? _self.isVisible : isVisible // ignore: cast_nullable_to_non_nullable
as bool,focusScopeId: freezed == focusScopeId ? _self.focusScopeId : focusScopeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,viewRef: freezed == viewRef ? _self.viewRef : viewRef // ignore: cast_nullable_to_non_nullable
as String?,viewKey: freezed == viewKey ? _self.viewKey : viewKey // ignore: cast_nullable_to_non_nullable
as String?,packageName: freezed == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String?,paneKey: freezed == paneKey ? _self.paneKey : paneKey // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [ThreadLayoutSectionViewStateV1].
extension ThreadLayoutSectionViewStateV1Patterns on ThreadLayoutSectionViewStateV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ThreadLayoutSectionViewStateV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ThreadLayoutSectionViewStateV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ThreadLayoutSectionViewStateV1 value)  def,}){
final _that = this;
switch (_that) {
case _ThreadLayoutSectionViewStateV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ThreadLayoutSectionViewStateV1 value)?  def,}){
final _that = this;
switch (_that) {
case _ThreadLayoutSectionViewStateV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String sectionKey,  String title,  String? description,  int order,  double flex,  bool isVisible, @UuidValueConverter()  UuidValue? focusScopeId,  String? viewRef,  String? viewKey,  String? packageName,  String? paneKey)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ThreadLayoutSectionViewStateV1() when def != null:
return def(_that.sectionKey,_that.title,_that.description,_that.order,_that.flex,_that.isVisible,_that.focusScopeId,_that.viewRef,_that.viewKey,_that.packageName,_that.paneKey);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String sectionKey,  String title,  String? description,  int order,  double flex,  bool isVisible, @UuidValueConverter()  UuidValue? focusScopeId,  String? viewRef,  String? viewKey,  String? packageName,  String? paneKey)  def,}) {final _that = this;
switch (_that) {
case _ThreadLayoutSectionViewStateV1():
return def(_that.sectionKey,_that.title,_that.description,_that.order,_that.flex,_that.isVisible,_that.focusScopeId,_that.viewRef,_that.viewKey,_that.packageName,_that.paneKey);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String sectionKey,  String title,  String? description,  int order,  double flex,  bool isVisible, @UuidValueConverter()  UuidValue? focusScopeId,  String? viewRef,  String? viewKey,  String? packageName,  String? paneKey)?  def,}) {final _that = this;
switch (_that) {
case _ThreadLayoutSectionViewStateV1() when def != null:
return def(_that.sectionKey,_that.title,_that.description,_that.order,_that.flex,_that.isVisible,_that.focusScopeId,_that.viewRef,_that.viewKey,_that.packageName,_that.paneKey);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ThreadLayoutSectionViewStateV1 implements ThreadLayoutSectionViewStateV1 {
   _ThreadLayoutSectionViewStateV1({required this.sectionKey, required this.title, this.description, required this.order, required this.flex, required this.isVisible, @UuidValueConverter() this.focusScopeId, this.viewRef, this.viewKey, this.packageName, this.paneKey});
  factory _ThreadLayoutSectionViewStateV1.fromJson(Map<String, dynamic> json) => _$ThreadLayoutSectionViewStateV1FromJson(json);

@override final  String sectionKey;
@override final  String title;
@override final  String? description;
@override final  int order;
@override final  double flex;
@override final  bool isVisible;
@override@UuidValueConverter() final  UuidValue? focusScopeId;
@override final  String? viewRef;
@override final  String? viewKey;
@override final  String? packageName;
@override final  String? paneKey;

/// Create a copy of ThreadLayoutSectionViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ThreadLayoutSectionViewStateV1CopyWith<_ThreadLayoutSectionViewStateV1> get copyWith => __$ThreadLayoutSectionViewStateV1CopyWithImpl<_ThreadLayoutSectionViewStateV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ThreadLayoutSectionViewStateV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ThreadLayoutSectionViewStateV1&&(identical(other.sectionKey, sectionKey) || other.sectionKey == sectionKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.order, order) || other.order == order)&&(identical(other.flex, flex) || other.flex == flex)&&(identical(other.isVisible, isVisible) || other.isVisible == isVisible)&&(identical(other.focusScopeId, focusScopeId) || other.focusScopeId == focusScopeId)&&(identical(other.viewRef, viewRef) || other.viewRef == viewRef)&&(identical(other.viewKey, viewKey) || other.viewKey == viewKey)&&(identical(other.packageName, packageName) || other.packageName == packageName)&&(identical(other.paneKey, paneKey) || other.paneKey == paneKey));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,sectionKey,title,description,order,flex,isVisible,focusScopeId,viewRef,viewKey,packageName,paneKey);

@override
String toString() {
  return 'ThreadLayoutSectionViewStateV1.def(sectionKey: $sectionKey, title: $title, description: $description, order: $order, flex: $flex, isVisible: $isVisible, focusScopeId: $focusScopeId, viewRef: $viewRef, viewKey: $viewKey, packageName: $packageName, paneKey: $paneKey)';
}


}

/// @nodoc
abstract mixin class _$ThreadLayoutSectionViewStateV1CopyWith<$Res> implements $ThreadLayoutSectionViewStateV1CopyWith<$Res> {
  factory _$ThreadLayoutSectionViewStateV1CopyWith(_ThreadLayoutSectionViewStateV1 value, $Res Function(_ThreadLayoutSectionViewStateV1) _then) = __$ThreadLayoutSectionViewStateV1CopyWithImpl;
@override @useResult
$Res call({
 String sectionKey, String title, String? description, int order, double flex, bool isVisible,@UuidValueConverter() UuidValue? focusScopeId, String? viewRef, String? viewKey, String? packageName, String? paneKey
});




}
/// @nodoc
class __$ThreadLayoutSectionViewStateV1CopyWithImpl<$Res>
    implements _$ThreadLayoutSectionViewStateV1CopyWith<$Res> {
  __$ThreadLayoutSectionViewStateV1CopyWithImpl(this._self, this._then);

  final _ThreadLayoutSectionViewStateV1 _self;
  final $Res Function(_ThreadLayoutSectionViewStateV1) _then;

/// Create a copy of ThreadLayoutSectionViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? sectionKey = null,Object? title = null,Object? description = freezed,Object? order = null,Object? flex = null,Object? isVisible = null,Object? focusScopeId = freezed,Object? viewRef = freezed,Object? viewKey = freezed,Object? packageName = freezed,Object? paneKey = freezed,}) {
  return _then(_ThreadLayoutSectionViewStateV1(
sectionKey: null == sectionKey ? _self.sectionKey : sectionKey // ignore: cast_nullable_to_non_nullable
as String,title: null == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,order: null == order ? _self.order : order // ignore: cast_nullable_to_non_nullable
as int,flex: null == flex ? _self.flex : flex // ignore: cast_nullable_to_non_nullable
as double,isVisible: null == isVisible ? _self.isVisible : isVisible // ignore: cast_nullable_to_non_nullable
as bool,focusScopeId: freezed == focusScopeId ? _self.focusScopeId : focusScopeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,viewRef: freezed == viewRef ? _self.viewRef : viewRef // ignore: cast_nullable_to_non_nullable
as String?,viewKey: freezed == viewKey ? _self.viewKey : viewKey // ignore: cast_nullable_to_non_nullable
as String?,packageName: freezed == packageName ? _self.packageName : packageName // ignore: cast_nullable_to_non_nullable
as String?,paneKey: freezed == paneKey ? _self.paneKey : paneKey // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$ThreadLayoutCandidateViewStateV1 {

@UuidValueConverter() UuidValue? get layoutId; String? get layoutKey; String get title; String? get description; bool get isActive; List<ThreadLayoutSectionViewStateV1> get sections;
/// Create a copy of ThreadLayoutCandidateViewStateV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ThreadLayoutCandidateViewStateV1CopyWith<ThreadLayoutCandidateViewStateV1> get copyWith => _$ThreadLayoutCandidateViewStateV1CopyWithImpl<ThreadLayoutCandidateViewStateV1>(this as ThreadLayoutCandidateViewStateV1, _$identity);

  /// Serializes this ThreadLayoutCandidateViewStateV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ThreadLayoutCandidateViewStateV1&&(identical(other.layoutId, layoutId) || other.layoutId == layoutId)&&(identical(other.layoutKey, layoutKey) || other.layoutKey == layoutKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.isActive, isActive) || other.isActive == isActive)&&const DeepCollectionEquality().equals(other.sections, sections));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,layoutId,layoutKey,title,description,isActive,const DeepCollectionEquality().hash(sections));

@override
String toString() {
  return 'ThreadLayoutCandidateViewStateV1(layoutId: $layoutId, layoutKey: $layoutKey, title: $title, description: $description, isActive: $isActive, sections: $sections)';
}


}

/// @nodoc
abstract mixin class $ThreadLayoutCandidateViewStateV1CopyWith<$Res>  {
  factory $ThreadLayoutCandidateViewStateV1CopyWith(ThreadLayoutCandidateViewStateV1 value, $Res Function(ThreadLayoutCandidateViewStateV1) _then) = _$ThreadLayoutCandidateViewStateV1CopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? layoutId, String? layoutKey, String title, String? description, bool isActive, List<ThreadLayoutSectionViewStateV1> sections
});




}
/// @nodoc
class _$ThreadLayoutCandidateViewStateV1CopyWithImpl<$Res>
    implements $ThreadLayoutCandidateViewStateV1CopyWith<$Res> {
  _$ThreadLayoutCandidateViewStateV1CopyWithImpl(this._self, this._then);

  final ThreadLayoutCandidateViewStateV1 _self;
  final $Res Function(ThreadLayoutCandidateViewStateV1) _then;

/// Create a copy of ThreadLayoutCandidateViewStateV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? layoutId = freezed,Object? layoutKey = freezed,Object? title = null,Object? description = freezed,Object? isActive = null,Object? sections = null,}) {
  return _then(_self.copyWith(
layoutId: freezed == layoutId ? _self.layoutId : layoutId // ignore: cast_nullable_to_non_nullable
as UuidValue?,layoutKey: freezed == layoutKey ? _self.layoutKey : layoutKey // ignore: cast_nullable_to_non_nullable
as String?,title: null == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,isActive: null == isActive ? _self.isActive : isActive // ignore: cast_nullable_to_non_nullable
as bool,sections: null == sections ? _self.sections : sections // ignore: cast_nullable_to_non_nullable
as List<ThreadLayoutSectionViewStateV1>,
  ));
}

}


/// Adds pattern-matching-related methods to [ThreadLayoutCandidateViewStateV1].
extension ThreadLayoutCandidateViewStateV1Patterns on ThreadLayoutCandidateViewStateV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ThreadLayoutCandidateViewStateV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ThreadLayoutCandidateViewStateV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ThreadLayoutCandidateViewStateV1 value)  def,}){
final _that = this;
switch (_that) {
case _ThreadLayoutCandidateViewStateV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ThreadLayoutCandidateViewStateV1 value)?  def,}){
final _that = this;
switch (_that) {
case _ThreadLayoutCandidateViewStateV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? layoutId,  String? layoutKey,  String title,  String? description,  bool isActive,  List<ThreadLayoutSectionViewStateV1> sections)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ThreadLayoutCandidateViewStateV1() when def != null:
return def(_that.layoutId,_that.layoutKey,_that.title,_that.description,_that.isActive,_that.sections);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? layoutId,  String? layoutKey,  String title,  String? description,  bool isActive,  List<ThreadLayoutSectionViewStateV1> sections)  def,}) {final _that = this;
switch (_that) {
case _ThreadLayoutCandidateViewStateV1():
return def(_that.layoutId,_that.layoutKey,_that.title,_that.description,_that.isActive,_that.sections);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? layoutId,  String? layoutKey,  String title,  String? description,  bool isActive,  List<ThreadLayoutSectionViewStateV1> sections)?  def,}) {final _that = this;
switch (_that) {
case _ThreadLayoutCandidateViewStateV1() when def != null:
return def(_that.layoutId,_that.layoutKey,_that.title,_that.description,_that.isActive,_that.sections);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ThreadLayoutCandidateViewStateV1 implements ThreadLayoutCandidateViewStateV1 {
   _ThreadLayoutCandidateViewStateV1({@UuidValueConverter() this.layoutId, this.layoutKey, required this.title, this.description, required this.isActive, final  List<ThreadLayoutSectionViewStateV1> sections = const []}): _sections = sections;
  factory _ThreadLayoutCandidateViewStateV1.fromJson(Map<String, dynamic> json) => _$ThreadLayoutCandidateViewStateV1FromJson(json);

@override@UuidValueConverter() final  UuidValue? layoutId;
@override final  String? layoutKey;
@override final  String title;
@override final  String? description;
@override final  bool isActive;
 final  List<ThreadLayoutSectionViewStateV1> _sections;
@override@JsonKey() List<ThreadLayoutSectionViewStateV1> get sections {
  if (_sections is EqualUnmodifiableListView) return _sections;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_sections);
}


/// Create a copy of ThreadLayoutCandidateViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ThreadLayoutCandidateViewStateV1CopyWith<_ThreadLayoutCandidateViewStateV1> get copyWith => __$ThreadLayoutCandidateViewStateV1CopyWithImpl<_ThreadLayoutCandidateViewStateV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ThreadLayoutCandidateViewStateV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ThreadLayoutCandidateViewStateV1&&(identical(other.layoutId, layoutId) || other.layoutId == layoutId)&&(identical(other.layoutKey, layoutKey) || other.layoutKey == layoutKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.isActive, isActive) || other.isActive == isActive)&&const DeepCollectionEquality().equals(other._sections, _sections));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,layoutId,layoutKey,title,description,isActive,const DeepCollectionEquality().hash(_sections));

@override
String toString() {
  return 'ThreadLayoutCandidateViewStateV1.def(layoutId: $layoutId, layoutKey: $layoutKey, title: $title, description: $description, isActive: $isActive, sections: $sections)';
}


}

/// @nodoc
abstract mixin class _$ThreadLayoutCandidateViewStateV1CopyWith<$Res> implements $ThreadLayoutCandidateViewStateV1CopyWith<$Res> {
  factory _$ThreadLayoutCandidateViewStateV1CopyWith(_ThreadLayoutCandidateViewStateV1 value, $Res Function(_ThreadLayoutCandidateViewStateV1) _then) = __$ThreadLayoutCandidateViewStateV1CopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? layoutId, String? layoutKey, String title, String? description, bool isActive, List<ThreadLayoutSectionViewStateV1> sections
});




}
/// @nodoc
class __$ThreadLayoutCandidateViewStateV1CopyWithImpl<$Res>
    implements _$ThreadLayoutCandidateViewStateV1CopyWith<$Res> {
  __$ThreadLayoutCandidateViewStateV1CopyWithImpl(this._self, this._then);

  final _ThreadLayoutCandidateViewStateV1 _self;
  final $Res Function(_ThreadLayoutCandidateViewStateV1) _then;

/// Create a copy of ThreadLayoutCandidateViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? layoutId = freezed,Object? layoutKey = freezed,Object? title = null,Object? description = freezed,Object? isActive = null,Object? sections = null,}) {
  return _then(_ThreadLayoutCandidateViewStateV1(
layoutId: freezed == layoutId ? _self.layoutId : layoutId // ignore: cast_nullable_to_non_nullable
as UuidValue?,layoutKey: freezed == layoutKey ? _self.layoutKey : layoutKey // ignore: cast_nullable_to_non_nullable
as String?,title: null == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,isActive: null == isActive ? _self.isActive : isActive // ignore: cast_nullable_to_non_nullable
as bool,sections: null == sections ? _self._sections : sections // ignore: cast_nullable_to_non_nullable
as List<ThreadLayoutSectionViewStateV1>,
  ));
}


}


/// @nodoc
mixin _$ThreadLayoutViewStateV1 {

@UuidValueConverter() UuidValue? get environmentId;@UuidValueConverter() UuidValue? get processId; String? get processKey;@UuidValueConverter() UuidValue? get threadId; String? get threadKey; String get title; String? get description; String get status;@UuidValueConverter() UuidValue? get activeLayoutId; String? get activeLayoutKey; List<ThreadLayoutCandidateViewStateV1> get layouts; List<ThreadLayoutSectionViewStateV1> get sections; List<ThreadLayoutAttachmentViewStateV1> get attachments; String get emptyMessage; Map<String, dynamic> get provenance;
/// Create a copy of ThreadLayoutViewStateV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ThreadLayoutViewStateV1CopyWith<ThreadLayoutViewStateV1> get copyWith => _$ThreadLayoutViewStateV1CopyWithImpl<ThreadLayoutViewStateV1>(this as ThreadLayoutViewStateV1, _$identity);

  /// Serializes this ThreadLayoutViewStateV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ThreadLayoutViewStateV1&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.processId, processId) || other.processId == processId)&&(identical(other.processKey, processKey) || other.processKey == processKey)&&(identical(other.threadId, threadId) || other.threadId == threadId)&&(identical(other.threadKey, threadKey) || other.threadKey == threadKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.status, status) || other.status == status)&&(identical(other.activeLayoutId, activeLayoutId) || other.activeLayoutId == activeLayoutId)&&(identical(other.activeLayoutKey, activeLayoutKey) || other.activeLayoutKey == activeLayoutKey)&&const DeepCollectionEquality().equals(other.layouts, layouts)&&const DeepCollectionEquality().equals(other.sections, sections)&&const DeepCollectionEquality().equals(other.attachments, attachments)&&(identical(other.emptyMessage, emptyMessage) || other.emptyMessage == emptyMessage)&&const DeepCollectionEquality().equals(other.provenance, provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,environmentId,processId,processKey,threadId,threadKey,title,description,status,activeLayoutId,activeLayoutKey,const DeepCollectionEquality().hash(layouts),const DeepCollectionEquality().hash(sections),const DeepCollectionEquality().hash(attachments),emptyMessage,const DeepCollectionEquality().hash(provenance));

@override
String toString() {
  return 'ThreadLayoutViewStateV1(environmentId: $environmentId, processId: $processId, processKey: $processKey, threadId: $threadId, threadKey: $threadKey, title: $title, description: $description, status: $status, activeLayoutId: $activeLayoutId, activeLayoutKey: $activeLayoutKey, layouts: $layouts, sections: $sections, attachments: $attachments, emptyMessage: $emptyMessage, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class $ThreadLayoutViewStateV1CopyWith<$Res>  {
  factory $ThreadLayoutViewStateV1CopyWith(ThreadLayoutViewStateV1 value, $Res Function(ThreadLayoutViewStateV1) _then) = _$ThreadLayoutViewStateV1CopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? environmentId,@UuidValueConverter() UuidValue? processId, String? processKey,@UuidValueConverter() UuidValue? threadId, String? threadKey, String title, String? description, String status,@UuidValueConverter() UuidValue? activeLayoutId, String? activeLayoutKey, List<ThreadLayoutCandidateViewStateV1> layouts, List<ThreadLayoutSectionViewStateV1> sections, List<ThreadLayoutAttachmentViewStateV1> attachments, String emptyMessage, Map<String, dynamic> provenance
});




}
/// @nodoc
class _$ThreadLayoutViewStateV1CopyWithImpl<$Res>
    implements $ThreadLayoutViewStateV1CopyWith<$Res> {
  _$ThreadLayoutViewStateV1CopyWithImpl(this._self, this._then);

  final ThreadLayoutViewStateV1 _self;
  final $Res Function(ThreadLayoutViewStateV1) _then;

/// Create a copy of ThreadLayoutViewStateV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? environmentId = freezed,Object? processId = freezed,Object? processKey = freezed,Object? threadId = freezed,Object? threadKey = freezed,Object? title = null,Object? description = freezed,Object? status = null,Object? activeLayoutId = freezed,Object? activeLayoutKey = freezed,Object? layouts = null,Object? sections = null,Object? attachments = null,Object? emptyMessage = null,Object? provenance = null,}) {
  return _then(_self.copyWith(
environmentId: freezed == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,processId: freezed == processId ? _self.processId : processId // ignore: cast_nullable_to_non_nullable
as UuidValue?,processKey: freezed == processKey ? _self.processKey : processKey // ignore: cast_nullable_to_non_nullable
as String?,threadId: freezed == threadId ? _self.threadId : threadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,threadKey: freezed == threadKey ? _self.threadKey : threadKey // ignore: cast_nullable_to_non_nullable
as String?,title: null == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,activeLayoutId: freezed == activeLayoutId ? _self.activeLayoutId : activeLayoutId // ignore: cast_nullable_to_non_nullable
as UuidValue?,activeLayoutKey: freezed == activeLayoutKey ? _self.activeLayoutKey : activeLayoutKey // ignore: cast_nullable_to_non_nullable
as String?,layouts: null == layouts ? _self.layouts : layouts // ignore: cast_nullable_to_non_nullable
as List<ThreadLayoutCandidateViewStateV1>,sections: null == sections ? _self.sections : sections // ignore: cast_nullable_to_non_nullable
as List<ThreadLayoutSectionViewStateV1>,attachments: null == attachments ? _self.attachments : attachments // ignore: cast_nullable_to_non_nullable
as List<ThreadLayoutAttachmentViewStateV1>,emptyMessage: null == emptyMessage ? _self.emptyMessage : emptyMessage // ignore: cast_nullable_to_non_nullable
as String,provenance: null == provenance ? _self.provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [ThreadLayoutViewStateV1].
extension ThreadLayoutViewStateV1Patterns on ThreadLayoutViewStateV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ThreadLayoutViewStateV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ThreadLayoutViewStateV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ThreadLayoutViewStateV1 value)  def,}){
final _that = this;
switch (_that) {
case _ThreadLayoutViewStateV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ThreadLayoutViewStateV1 value)?  def,}){
final _that = this;
switch (_that) {
case _ThreadLayoutViewStateV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue? processId,  String? processKey, @UuidValueConverter()  UuidValue? threadId,  String? threadKey,  String title,  String? description,  String status, @UuidValueConverter()  UuidValue? activeLayoutId,  String? activeLayoutKey,  List<ThreadLayoutCandidateViewStateV1> layouts,  List<ThreadLayoutSectionViewStateV1> sections,  List<ThreadLayoutAttachmentViewStateV1> attachments,  String emptyMessage,  Map<String, dynamic> provenance)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ThreadLayoutViewStateV1() when def != null:
return def(_that.environmentId,_that.processId,_that.processKey,_that.threadId,_that.threadKey,_that.title,_that.description,_that.status,_that.activeLayoutId,_that.activeLayoutKey,_that.layouts,_that.sections,_that.attachments,_that.emptyMessage,_that.provenance);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue? processId,  String? processKey, @UuidValueConverter()  UuidValue? threadId,  String? threadKey,  String title,  String? description,  String status, @UuidValueConverter()  UuidValue? activeLayoutId,  String? activeLayoutKey,  List<ThreadLayoutCandidateViewStateV1> layouts,  List<ThreadLayoutSectionViewStateV1> sections,  List<ThreadLayoutAttachmentViewStateV1> attachments,  String emptyMessage,  Map<String, dynamic> provenance)  def,}) {final _that = this;
switch (_that) {
case _ThreadLayoutViewStateV1():
return def(_that.environmentId,_that.processId,_that.processKey,_that.threadId,_that.threadKey,_that.title,_that.description,_that.status,_that.activeLayoutId,_that.activeLayoutKey,_that.layouts,_that.sections,_that.attachments,_that.emptyMessage,_that.provenance);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue? processId,  String? processKey, @UuidValueConverter()  UuidValue? threadId,  String? threadKey,  String title,  String? description,  String status, @UuidValueConverter()  UuidValue? activeLayoutId,  String? activeLayoutKey,  List<ThreadLayoutCandidateViewStateV1> layouts,  List<ThreadLayoutSectionViewStateV1> sections,  List<ThreadLayoutAttachmentViewStateV1> attachments,  String emptyMessage,  Map<String, dynamic> provenance)?  def,}) {final _that = this;
switch (_that) {
case _ThreadLayoutViewStateV1() when def != null:
return def(_that.environmentId,_that.processId,_that.processKey,_that.threadId,_that.threadKey,_that.title,_that.description,_that.status,_that.activeLayoutId,_that.activeLayoutKey,_that.layouts,_that.sections,_that.attachments,_that.emptyMessage,_that.provenance);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ThreadLayoutViewStateV1 implements ThreadLayoutViewStateV1 {
   _ThreadLayoutViewStateV1({@UuidValueConverter() this.environmentId, @UuidValueConverter() this.processId, this.processKey, @UuidValueConverter() this.threadId, this.threadKey, required this.title, this.description, required this.status, @UuidValueConverter() this.activeLayoutId, this.activeLayoutKey, final  List<ThreadLayoutCandidateViewStateV1> layouts = const [], final  List<ThreadLayoutSectionViewStateV1> sections = const [], final  List<ThreadLayoutAttachmentViewStateV1> attachments = const [], required this.emptyMessage, required final  Map<String, dynamic> provenance}): _layouts = layouts,_sections = sections,_attachments = attachments,_provenance = provenance;
  factory _ThreadLayoutViewStateV1.fromJson(Map<String, dynamic> json) => _$ThreadLayoutViewStateV1FromJson(json);

@override@UuidValueConverter() final  UuidValue? environmentId;
@override@UuidValueConverter() final  UuidValue? processId;
@override final  String? processKey;
@override@UuidValueConverter() final  UuidValue? threadId;
@override final  String? threadKey;
@override final  String title;
@override final  String? description;
@override final  String status;
@override@UuidValueConverter() final  UuidValue? activeLayoutId;
@override final  String? activeLayoutKey;
 final  List<ThreadLayoutCandidateViewStateV1> _layouts;
@override@JsonKey() List<ThreadLayoutCandidateViewStateV1> get layouts {
  if (_layouts is EqualUnmodifiableListView) return _layouts;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_layouts);
}

 final  List<ThreadLayoutSectionViewStateV1> _sections;
@override@JsonKey() List<ThreadLayoutSectionViewStateV1> get sections {
  if (_sections is EqualUnmodifiableListView) return _sections;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_sections);
}

 final  List<ThreadLayoutAttachmentViewStateV1> _attachments;
@override@JsonKey() List<ThreadLayoutAttachmentViewStateV1> get attachments {
  if (_attachments is EqualUnmodifiableListView) return _attachments;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_attachments);
}

@override final  String emptyMessage;
 final  Map<String, dynamic> _provenance;
@override Map<String, dynamic> get provenance {
  if (_provenance is EqualUnmodifiableMapView) return _provenance;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_provenance);
}


/// Create a copy of ThreadLayoutViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ThreadLayoutViewStateV1CopyWith<_ThreadLayoutViewStateV1> get copyWith => __$ThreadLayoutViewStateV1CopyWithImpl<_ThreadLayoutViewStateV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ThreadLayoutViewStateV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ThreadLayoutViewStateV1&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.processId, processId) || other.processId == processId)&&(identical(other.processKey, processKey) || other.processKey == processKey)&&(identical(other.threadId, threadId) || other.threadId == threadId)&&(identical(other.threadKey, threadKey) || other.threadKey == threadKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.status, status) || other.status == status)&&(identical(other.activeLayoutId, activeLayoutId) || other.activeLayoutId == activeLayoutId)&&(identical(other.activeLayoutKey, activeLayoutKey) || other.activeLayoutKey == activeLayoutKey)&&const DeepCollectionEquality().equals(other._layouts, _layouts)&&const DeepCollectionEquality().equals(other._sections, _sections)&&const DeepCollectionEquality().equals(other._attachments, _attachments)&&(identical(other.emptyMessage, emptyMessage) || other.emptyMessage == emptyMessage)&&const DeepCollectionEquality().equals(other._provenance, _provenance));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,environmentId,processId,processKey,threadId,threadKey,title,description,status,activeLayoutId,activeLayoutKey,const DeepCollectionEquality().hash(_layouts),const DeepCollectionEquality().hash(_sections),const DeepCollectionEquality().hash(_attachments),emptyMessage,const DeepCollectionEquality().hash(_provenance));

@override
String toString() {
  return 'ThreadLayoutViewStateV1.def(environmentId: $environmentId, processId: $processId, processKey: $processKey, threadId: $threadId, threadKey: $threadKey, title: $title, description: $description, status: $status, activeLayoutId: $activeLayoutId, activeLayoutKey: $activeLayoutKey, layouts: $layouts, sections: $sections, attachments: $attachments, emptyMessage: $emptyMessage, provenance: $provenance)';
}


}

/// @nodoc
abstract mixin class _$ThreadLayoutViewStateV1CopyWith<$Res> implements $ThreadLayoutViewStateV1CopyWith<$Res> {
  factory _$ThreadLayoutViewStateV1CopyWith(_ThreadLayoutViewStateV1 value, $Res Function(_ThreadLayoutViewStateV1) _then) = __$ThreadLayoutViewStateV1CopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? environmentId,@UuidValueConverter() UuidValue? processId, String? processKey,@UuidValueConverter() UuidValue? threadId, String? threadKey, String title, String? description, String status,@UuidValueConverter() UuidValue? activeLayoutId, String? activeLayoutKey, List<ThreadLayoutCandidateViewStateV1> layouts, List<ThreadLayoutSectionViewStateV1> sections, List<ThreadLayoutAttachmentViewStateV1> attachments, String emptyMessage, Map<String, dynamic> provenance
});




}
/// @nodoc
class __$ThreadLayoutViewStateV1CopyWithImpl<$Res>
    implements _$ThreadLayoutViewStateV1CopyWith<$Res> {
  __$ThreadLayoutViewStateV1CopyWithImpl(this._self, this._then);

  final _ThreadLayoutViewStateV1 _self;
  final $Res Function(_ThreadLayoutViewStateV1) _then;

/// Create a copy of ThreadLayoutViewStateV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? environmentId = freezed,Object? processId = freezed,Object? processKey = freezed,Object? threadId = freezed,Object? threadKey = freezed,Object? title = null,Object? description = freezed,Object? status = null,Object? activeLayoutId = freezed,Object? activeLayoutKey = freezed,Object? layouts = null,Object? sections = null,Object? attachments = null,Object? emptyMessage = null,Object? provenance = null,}) {
  return _then(_ThreadLayoutViewStateV1(
environmentId: freezed == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,processId: freezed == processId ? _self.processId : processId // ignore: cast_nullable_to_non_nullable
as UuidValue?,processKey: freezed == processKey ? _self.processKey : processKey // ignore: cast_nullable_to_non_nullable
as String?,threadId: freezed == threadId ? _self.threadId : threadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,threadKey: freezed == threadKey ? _self.threadKey : threadKey // ignore: cast_nullable_to_non_nullable
as String?,title: null == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,activeLayoutId: freezed == activeLayoutId ? _self.activeLayoutId : activeLayoutId // ignore: cast_nullable_to_non_nullable
as UuidValue?,activeLayoutKey: freezed == activeLayoutKey ? _self.activeLayoutKey : activeLayoutKey // ignore: cast_nullable_to_non_nullable
as String?,layouts: null == layouts ? _self._layouts : layouts // ignore: cast_nullable_to_non_nullable
as List<ThreadLayoutCandidateViewStateV1>,sections: null == sections ? _self._sections : sections // ignore: cast_nullable_to_non_nullable
as List<ThreadLayoutSectionViewStateV1>,attachments: null == attachments ? _self._attachments : attachments // ignore: cast_nullable_to_non_nullable
as List<ThreadLayoutAttachmentViewStateV1>,emptyMessage: null == emptyMessage ? _self.emptyMessage : emptyMessage // ignore: cast_nullable_to_non_nullable
as String,provenance: null == provenance ? _self._provenance : provenance // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}

// dart format on
