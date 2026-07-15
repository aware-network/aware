// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'service_diagnostic_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$ServiceDiagnosticEntry {

 String get key; Object? get value;
/// Create a copy of ServiceDiagnosticEntry
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ServiceDiagnosticEntryCopyWith<ServiceDiagnosticEntry> get copyWith => _$ServiceDiagnosticEntryCopyWithImpl<ServiceDiagnosticEntry>(this as ServiceDiagnosticEntry, _$identity);

  /// Serializes this ServiceDiagnosticEntry to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ServiceDiagnosticEntry&&(identical(other.key, key) || other.key == key)&&const DeepCollectionEquality().equals(other.value, value));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,key,const DeepCollectionEquality().hash(value));

@override
String toString() {
  return 'ServiceDiagnosticEntry(key: $key, value: $value)';
}


}

/// @nodoc
abstract mixin class $ServiceDiagnosticEntryCopyWith<$Res>  {
  factory $ServiceDiagnosticEntryCopyWith(ServiceDiagnosticEntry value, $Res Function(ServiceDiagnosticEntry) _then) = _$ServiceDiagnosticEntryCopyWithImpl;
@useResult
$Res call({
 String key, Object? value
});




}
/// @nodoc
class _$ServiceDiagnosticEntryCopyWithImpl<$Res>
    implements $ServiceDiagnosticEntryCopyWith<$Res> {
  _$ServiceDiagnosticEntryCopyWithImpl(this._self, this._then);

  final ServiceDiagnosticEntry _self;
  final $Res Function(ServiceDiagnosticEntry) _then;

/// Create a copy of ServiceDiagnosticEntry
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? key = null,Object? value = freezed,}) {
  return _then(_self.copyWith(
key: null == key ? _self.key : key // ignore: cast_nullable_to_non_nullable
as String,value: freezed == value ? _self.value : value ,
  ));
}

}


/// Adds pattern-matching-related methods to [ServiceDiagnosticEntry].
extension ServiceDiagnosticEntryPatterns on ServiceDiagnosticEntry {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ServiceDiagnosticEntry value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ServiceDiagnosticEntry() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ServiceDiagnosticEntry value)  def,}){
final _that = this;
switch (_that) {
case _ServiceDiagnosticEntry():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ServiceDiagnosticEntry value)?  def,}){
final _that = this;
switch (_that) {
case _ServiceDiagnosticEntry() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String key,  Object? value)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ServiceDiagnosticEntry() when def != null:
return def(_that.key,_that.value);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String key,  Object? value)  def,}) {final _that = this;
switch (_that) {
case _ServiceDiagnosticEntry():
return def(_that.key,_that.value);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String key,  Object? value)?  def,}) {final _that = this;
switch (_that) {
case _ServiceDiagnosticEntry() when def != null:
return def(_that.key,_that.value);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ServiceDiagnosticEntry implements ServiceDiagnosticEntry {
   _ServiceDiagnosticEntry({required this.key, required this.value});
  factory _ServiceDiagnosticEntry.fromJson(Map<String, dynamic> json) => _$ServiceDiagnosticEntryFromJson(json);

@override final  String key;
@override final  Object? value;

/// Create a copy of ServiceDiagnosticEntry
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ServiceDiagnosticEntryCopyWith<_ServiceDiagnosticEntry> get copyWith => __$ServiceDiagnosticEntryCopyWithImpl<_ServiceDiagnosticEntry>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ServiceDiagnosticEntryToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ServiceDiagnosticEntry&&(identical(other.key, key) || other.key == key)&&const DeepCollectionEquality().equals(other.value, value));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,key,const DeepCollectionEquality().hash(value));

@override
String toString() {
  return 'ServiceDiagnosticEntry.def(key: $key, value: $value)';
}


}

/// @nodoc
abstract mixin class _$ServiceDiagnosticEntryCopyWith<$Res> implements $ServiceDiagnosticEntryCopyWith<$Res> {
  factory _$ServiceDiagnosticEntryCopyWith(_ServiceDiagnosticEntry value, $Res Function(_ServiceDiagnosticEntry) _then) = __$ServiceDiagnosticEntryCopyWithImpl;
@override @useResult
$Res call({
 String key, Object? value
});




}
/// @nodoc
class __$ServiceDiagnosticEntryCopyWithImpl<$Res>
    implements _$ServiceDiagnosticEntryCopyWith<$Res> {
  __$ServiceDiagnosticEntryCopyWithImpl(this._self, this._then);

  final _ServiceDiagnosticEntry _self;
  final $Res Function(_ServiceDiagnosticEntry) _then;

/// Create a copy of ServiceDiagnosticEntry
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? key = null,Object? value = freezed,}) {
  return _then(_ServiceDiagnosticEntry(
key: null == key ? _self.key : key // ignore: cast_nullable_to_non_nullable
as String,value: freezed == value ? _self.value : value ,
  ));
}


}


/// @nodoc
mixin _$ServiceDiagnosticSection {

 String get title; List<ServiceDiagnosticEntry> get entries;
/// Create a copy of ServiceDiagnosticSection
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ServiceDiagnosticSectionCopyWith<ServiceDiagnosticSection> get copyWith => _$ServiceDiagnosticSectionCopyWithImpl<ServiceDiagnosticSection>(this as ServiceDiagnosticSection, _$identity);

  /// Serializes this ServiceDiagnosticSection to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ServiceDiagnosticSection&&(identical(other.title, title) || other.title == title)&&const DeepCollectionEquality().equals(other.entries, entries));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,title,const DeepCollectionEquality().hash(entries));

@override
String toString() {
  return 'ServiceDiagnosticSection(title: $title, entries: $entries)';
}


}

/// @nodoc
abstract mixin class $ServiceDiagnosticSectionCopyWith<$Res>  {
  factory $ServiceDiagnosticSectionCopyWith(ServiceDiagnosticSection value, $Res Function(ServiceDiagnosticSection) _then) = _$ServiceDiagnosticSectionCopyWithImpl;
@useResult
$Res call({
 String title, List<ServiceDiagnosticEntry> entries
});




}
/// @nodoc
class _$ServiceDiagnosticSectionCopyWithImpl<$Res>
    implements $ServiceDiagnosticSectionCopyWith<$Res> {
  _$ServiceDiagnosticSectionCopyWithImpl(this._self, this._then);

  final ServiceDiagnosticSection _self;
  final $Res Function(ServiceDiagnosticSection) _then;

/// Create a copy of ServiceDiagnosticSection
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? title = null,Object? entries = null,}) {
  return _then(_self.copyWith(
title: null == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String,entries: null == entries ? _self.entries : entries // ignore: cast_nullable_to_non_nullable
as List<ServiceDiagnosticEntry>,
  ));
}

}


/// Adds pattern-matching-related methods to [ServiceDiagnosticSection].
extension ServiceDiagnosticSectionPatterns on ServiceDiagnosticSection {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ServiceDiagnosticSection value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ServiceDiagnosticSection() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ServiceDiagnosticSection value)  def,}){
final _that = this;
switch (_that) {
case _ServiceDiagnosticSection():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ServiceDiagnosticSection value)?  def,}){
final _that = this;
switch (_that) {
case _ServiceDiagnosticSection() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String title,  List<ServiceDiagnosticEntry> entries)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ServiceDiagnosticSection() when def != null:
return def(_that.title,_that.entries);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String title,  List<ServiceDiagnosticEntry> entries)  def,}) {final _that = this;
switch (_that) {
case _ServiceDiagnosticSection():
return def(_that.title,_that.entries);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String title,  List<ServiceDiagnosticEntry> entries)?  def,}) {final _that = this;
switch (_that) {
case _ServiceDiagnosticSection() when def != null:
return def(_that.title,_that.entries);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ServiceDiagnosticSection implements ServiceDiagnosticSection {
   _ServiceDiagnosticSection({required this.title, final  List<ServiceDiagnosticEntry> entries = const []}): _entries = entries;
  factory _ServiceDiagnosticSection.fromJson(Map<String, dynamic> json) => _$ServiceDiagnosticSectionFromJson(json);

@override final  String title;
 final  List<ServiceDiagnosticEntry> _entries;
@override@JsonKey() List<ServiceDiagnosticEntry> get entries {
  if (_entries is EqualUnmodifiableListView) return _entries;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_entries);
}


/// Create a copy of ServiceDiagnosticSection
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ServiceDiagnosticSectionCopyWith<_ServiceDiagnosticSection> get copyWith => __$ServiceDiagnosticSectionCopyWithImpl<_ServiceDiagnosticSection>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ServiceDiagnosticSectionToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ServiceDiagnosticSection&&(identical(other.title, title) || other.title == title)&&const DeepCollectionEquality().equals(other._entries, _entries));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,title,const DeepCollectionEquality().hash(_entries));

@override
String toString() {
  return 'ServiceDiagnosticSection.def(title: $title, entries: $entries)';
}


}

/// @nodoc
abstract mixin class _$ServiceDiagnosticSectionCopyWith<$Res> implements $ServiceDiagnosticSectionCopyWith<$Res> {
  factory _$ServiceDiagnosticSectionCopyWith(_ServiceDiagnosticSection value, $Res Function(_ServiceDiagnosticSection) _then) = __$ServiceDiagnosticSectionCopyWithImpl;
@override @useResult
$Res call({
 String title, List<ServiceDiagnosticEntry> entries
});




}
/// @nodoc
class __$ServiceDiagnosticSectionCopyWithImpl<$Res>
    implements _$ServiceDiagnosticSectionCopyWith<$Res> {
  __$ServiceDiagnosticSectionCopyWithImpl(this._self, this._then);

  final _ServiceDiagnosticSection _self;
  final $Res Function(_ServiceDiagnosticSection) _then;

/// Create a copy of ServiceDiagnosticSection
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? title = null,Object? entries = null,}) {
  return _then(_ServiceDiagnosticSection(
title: null == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String,entries: null == entries ? _self._entries : entries // ignore: cast_nullable_to_non_nullable
as List<ServiceDiagnosticEntry>,
  ));
}


}


/// @nodoc
mixin _$ServiceDiagnostic {

 String get code;@JsonKey(fromJson: ServiceDiagnosticCategoryExtension.fromJson, toJson: ServiceDiagnosticCategoryExtension.toJson) ServiceDiagnosticCategory get category;@JsonKey(fromJson: ServiceDiagnosticSeverityExtension.fromJson, toJson: ServiceDiagnosticSeverityExtension.toJson) ServiceDiagnosticSeverity get severity; String get summary; String? get detail; String? get hint; ServiceDiagnosticSection get semanticRefs; ServiceDiagnosticSection get invocationContext; ServiceDiagnosticSection get provenance;@JsonKey(fromJson: ServiceDiagnosticResolutionStatusExtension.fromJson, toJson: ServiceDiagnosticResolutionStatusExtension.toJson) ServiceDiagnosticResolutionStatus get resolutionStatus; ServiceDiagnosticSection? get debug;
/// Create a copy of ServiceDiagnostic
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ServiceDiagnosticCopyWith<ServiceDiagnostic> get copyWith => _$ServiceDiagnosticCopyWithImpl<ServiceDiagnostic>(this as ServiceDiagnostic, _$identity);

  /// Serializes this ServiceDiagnostic to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ServiceDiagnostic&&(identical(other.code, code) || other.code == code)&&(identical(other.category, category) || other.category == category)&&(identical(other.severity, severity) || other.severity == severity)&&(identical(other.summary, summary) || other.summary == summary)&&(identical(other.detail, detail) || other.detail == detail)&&(identical(other.hint, hint) || other.hint == hint)&&(identical(other.semanticRefs, semanticRefs) || other.semanticRefs == semanticRefs)&&(identical(other.invocationContext, invocationContext) || other.invocationContext == invocationContext)&&(identical(other.provenance, provenance) || other.provenance == provenance)&&(identical(other.resolutionStatus, resolutionStatus) || other.resolutionStatus == resolutionStatus)&&(identical(other.debug, debug) || other.debug == debug));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,code,category,severity,summary,detail,hint,semanticRefs,invocationContext,provenance,resolutionStatus,debug);

@override
String toString() {
  return 'ServiceDiagnostic(code: $code, category: $category, severity: $severity, summary: $summary, detail: $detail, hint: $hint, semanticRefs: $semanticRefs, invocationContext: $invocationContext, provenance: $provenance, resolutionStatus: $resolutionStatus, debug: $debug)';
}


}

/// @nodoc
abstract mixin class $ServiceDiagnosticCopyWith<$Res>  {
  factory $ServiceDiagnosticCopyWith(ServiceDiagnostic value, $Res Function(ServiceDiagnostic) _then) = _$ServiceDiagnosticCopyWithImpl;
@useResult
$Res call({
 String code,@JsonKey(fromJson: ServiceDiagnosticCategoryExtension.fromJson, toJson: ServiceDiagnosticCategoryExtension.toJson) ServiceDiagnosticCategory category,@JsonKey(fromJson: ServiceDiagnosticSeverityExtension.fromJson, toJson: ServiceDiagnosticSeverityExtension.toJson) ServiceDiagnosticSeverity severity, String summary, String? detail, String? hint, ServiceDiagnosticSection semanticRefs, ServiceDiagnosticSection invocationContext, ServiceDiagnosticSection provenance,@JsonKey(fromJson: ServiceDiagnosticResolutionStatusExtension.fromJson, toJson: ServiceDiagnosticResolutionStatusExtension.toJson) ServiceDiagnosticResolutionStatus resolutionStatus, ServiceDiagnosticSection? debug
});


$ServiceDiagnosticSectionCopyWith<$Res> get semanticRefs;$ServiceDiagnosticSectionCopyWith<$Res> get invocationContext;$ServiceDiagnosticSectionCopyWith<$Res> get provenance;$ServiceDiagnosticSectionCopyWith<$Res>? get debug;

}
/// @nodoc
class _$ServiceDiagnosticCopyWithImpl<$Res>
    implements $ServiceDiagnosticCopyWith<$Res> {
  _$ServiceDiagnosticCopyWithImpl(this._self, this._then);

  final ServiceDiagnostic _self;
  final $Res Function(ServiceDiagnostic) _then;

/// Create a copy of ServiceDiagnostic
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? code = null,Object? category = null,Object? severity = null,Object? summary = null,Object? detail = freezed,Object? hint = freezed,Object? semanticRefs = null,Object? invocationContext = null,Object? provenance = null,Object? resolutionStatus = null,Object? debug = freezed,}) {
  return _then(_self.copyWith(
code: null == code ? _self.code : code // ignore: cast_nullable_to_non_nullable
as String,category: null == category ? _self.category : category // ignore: cast_nullable_to_non_nullable
as ServiceDiagnosticCategory,severity: null == severity ? _self.severity : severity // ignore: cast_nullable_to_non_nullable
as ServiceDiagnosticSeverity,summary: null == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String,detail: freezed == detail ? _self.detail : detail // ignore: cast_nullable_to_non_nullable
as String?,hint: freezed == hint ? _self.hint : hint // ignore: cast_nullable_to_non_nullable
as String?,semanticRefs: null == semanticRefs ? _self.semanticRefs : semanticRefs // ignore: cast_nullable_to_non_nullable
as ServiceDiagnosticSection,invocationContext: null == invocationContext ? _self.invocationContext : invocationContext // ignore: cast_nullable_to_non_nullable
as ServiceDiagnosticSection,provenance: null == provenance ? _self.provenance : provenance // ignore: cast_nullable_to_non_nullable
as ServiceDiagnosticSection,resolutionStatus: null == resolutionStatus ? _self.resolutionStatus : resolutionStatus // ignore: cast_nullable_to_non_nullable
as ServiceDiagnosticResolutionStatus,debug: freezed == debug ? _self.debug : debug // ignore: cast_nullable_to_non_nullable
as ServiceDiagnosticSection?,
  ));
}
/// Create a copy of ServiceDiagnostic
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceDiagnosticSectionCopyWith<$Res> get semanticRefs {
  
  return $ServiceDiagnosticSectionCopyWith<$Res>(_self.semanticRefs, (value) {
    return _then(_self.copyWith(semanticRefs: value));
  });
}/// Create a copy of ServiceDiagnostic
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceDiagnosticSectionCopyWith<$Res> get invocationContext {
  
  return $ServiceDiagnosticSectionCopyWith<$Res>(_self.invocationContext, (value) {
    return _then(_self.copyWith(invocationContext: value));
  });
}/// Create a copy of ServiceDiagnostic
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceDiagnosticSectionCopyWith<$Res> get provenance {
  
  return $ServiceDiagnosticSectionCopyWith<$Res>(_self.provenance, (value) {
    return _then(_self.copyWith(provenance: value));
  });
}/// Create a copy of ServiceDiagnostic
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceDiagnosticSectionCopyWith<$Res>? get debug {
    if (_self.debug == null) {
    return null;
  }

  return $ServiceDiagnosticSectionCopyWith<$Res>(_self.debug!, (value) {
    return _then(_self.copyWith(debug: value));
  });
}
}


/// Adds pattern-matching-related methods to [ServiceDiagnostic].
extension ServiceDiagnosticPatterns on ServiceDiagnostic {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ServiceDiagnostic value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ServiceDiagnostic() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ServiceDiagnostic value)  def,}){
final _that = this;
switch (_that) {
case _ServiceDiagnostic():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ServiceDiagnostic value)?  def,}){
final _that = this;
switch (_that) {
case _ServiceDiagnostic() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String code, @JsonKey(fromJson: ServiceDiagnosticCategoryExtension.fromJson, toJson: ServiceDiagnosticCategoryExtension.toJson)  ServiceDiagnosticCategory category, @JsonKey(fromJson: ServiceDiagnosticSeverityExtension.fromJson, toJson: ServiceDiagnosticSeverityExtension.toJson)  ServiceDiagnosticSeverity severity,  String summary,  String? detail,  String? hint,  ServiceDiagnosticSection semanticRefs,  ServiceDiagnosticSection invocationContext,  ServiceDiagnosticSection provenance, @JsonKey(fromJson: ServiceDiagnosticResolutionStatusExtension.fromJson, toJson: ServiceDiagnosticResolutionStatusExtension.toJson)  ServiceDiagnosticResolutionStatus resolutionStatus,  ServiceDiagnosticSection? debug)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ServiceDiagnostic() when def != null:
return def(_that.code,_that.category,_that.severity,_that.summary,_that.detail,_that.hint,_that.semanticRefs,_that.invocationContext,_that.provenance,_that.resolutionStatus,_that.debug);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String code, @JsonKey(fromJson: ServiceDiagnosticCategoryExtension.fromJson, toJson: ServiceDiagnosticCategoryExtension.toJson)  ServiceDiagnosticCategory category, @JsonKey(fromJson: ServiceDiagnosticSeverityExtension.fromJson, toJson: ServiceDiagnosticSeverityExtension.toJson)  ServiceDiagnosticSeverity severity,  String summary,  String? detail,  String? hint,  ServiceDiagnosticSection semanticRefs,  ServiceDiagnosticSection invocationContext,  ServiceDiagnosticSection provenance, @JsonKey(fromJson: ServiceDiagnosticResolutionStatusExtension.fromJson, toJson: ServiceDiagnosticResolutionStatusExtension.toJson)  ServiceDiagnosticResolutionStatus resolutionStatus,  ServiceDiagnosticSection? debug)  def,}) {final _that = this;
switch (_that) {
case _ServiceDiagnostic():
return def(_that.code,_that.category,_that.severity,_that.summary,_that.detail,_that.hint,_that.semanticRefs,_that.invocationContext,_that.provenance,_that.resolutionStatus,_that.debug);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String code, @JsonKey(fromJson: ServiceDiagnosticCategoryExtension.fromJson, toJson: ServiceDiagnosticCategoryExtension.toJson)  ServiceDiagnosticCategory category, @JsonKey(fromJson: ServiceDiagnosticSeverityExtension.fromJson, toJson: ServiceDiagnosticSeverityExtension.toJson)  ServiceDiagnosticSeverity severity,  String summary,  String? detail,  String? hint,  ServiceDiagnosticSection semanticRefs,  ServiceDiagnosticSection invocationContext,  ServiceDiagnosticSection provenance, @JsonKey(fromJson: ServiceDiagnosticResolutionStatusExtension.fromJson, toJson: ServiceDiagnosticResolutionStatusExtension.toJson)  ServiceDiagnosticResolutionStatus resolutionStatus,  ServiceDiagnosticSection? debug)?  def,}) {final _that = this;
switch (_that) {
case _ServiceDiagnostic() when def != null:
return def(_that.code,_that.category,_that.severity,_that.summary,_that.detail,_that.hint,_that.semanticRefs,_that.invocationContext,_that.provenance,_that.resolutionStatus,_that.debug);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ServiceDiagnostic implements ServiceDiagnostic {
   _ServiceDiagnostic({required this.code, @JsonKey(fromJson: ServiceDiagnosticCategoryExtension.fromJson, toJson: ServiceDiagnosticCategoryExtension.toJson) required this.category, @JsonKey(fromJson: ServiceDiagnosticSeverityExtension.fromJson, toJson: ServiceDiagnosticSeverityExtension.toJson) required this.severity, required this.summary, this.detail, this.hint, required this.semanticRefs, required this.invocationContext, required this.provenance, @JsonKey(fromJson: ServiceDiagnosticResolutionStatusExtension.fromJson, toJson: ServiceDiagnosticResolutionStatusExtension.toJson) required this.resolutionStatus, this.debug});
  factory _ServiceDiagnostic.fromJson(Map<String, dynamic> json) => _$ServiceDiagnosticFromJson(json);

@override final  String code;
@override@JsonKey(fromJson: ServiceDiagnosticCategoryExtension.fromJson, toJson: ServiceDiagnosticCategoryExtension.toJson) final  ServiceDiagnosticCategory category;
@override@JsonKey(fromJson: ServiceDiagnosticSeverityExtension.fromJson, toJson: ServiceDiagnosticSeverityExtension.toJson) final  ServiceDiagnosticSeverity severity;
@override final  String summary;
@override final  String? detail;
@override final  String? hint;
@override final  ServiceDiagnosticSection semanticRefs;
@override final  ServiceDiagnosticSection invocationContext;
@override final  ServiceDiagnosticSection provenance;
@override@JsonKey(fromJson: ServiceDiagnosticResolutionStatusExtension.fromJson, toJson: ServiceDiagnosticResolutionStatusExtension.toJson) final  ServiceDiagnosticResolutionStatus resolutionStatus;
@override final  ServiceDiagnosticSection? debug;

/// Create a copy of ServiceDiagnostic
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ServiceDiagnosticCopyWith<_ServiceDiagnostic> get copyWith => __$ServiceDiagnosticCopyWithImpl<_ServiceDiagnostic>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ServiceDiagnosticToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ServiceDiagnostic&&(identical(other.code, code) || other.code == code)&&(identical(other.category, category) || other.category == category)&&(identical(other.severity, severity) || other.severity == severity)&&(identical(other.summary, summary) || other.summary == summary)&&(identical(other.detail, detail) || other.detail == detail)&&(identical(other.hint, hint) || other.hint == hint)&&(identical(other.semanticRefs, semanticRefs) || other.semanticRefs == semanticRefs)&&(identical(other.invocationContext, invocationContext) || other.invocationContext == invocationContext)&&(identical(other.provenance, provenance) || other.provenance == provenance)&&(identical(other.resolutionStatus, resolutionStatus) || other.resolutionStatus == resolutionStatus)&&(identical(other.debug, debug) || other.debug == debug));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,code,category,severity,summary,detail,hint,semanticRefs,invocationContext,provenance,resolutionStatus,debug);

@override
String toString() {
  return 'ServiceDiagnostic.def(code: $code, category: $category, severity: $severity, summary: $summary, detail: $detail, hint: $hint, semanticRefs: $semanticRefs, invocationContext: $invocationContext, provenance: $provenance, resolutionStatus: $resolutionStatus, debug: $debug)';
}


}

/// @nodoc
abstract mixin class _$ServiceDiagnosticCopyWith<$Res> implements $ServiceDiagnosticCopyWith<$Res> {
  factory _$ServiceDiagnosticCopyWith(_ServiceDiagnostic value, $Res Function(_ServiceDiagnostic) _then) = __$ServiceDiagnosticCopyWithImpl;
@override @useResult
$Res call({
 String code,@JsonKey(fromJson: ServiceDiagnosticCategoryExtension.fromJson, toJson: ServiceDiagnosticCategoryExtension.toJson) ServiceDiagnosticCategory category,@JsonKey(fromJson: ServiceDiagnosticSeverityExtension.fromJson, toJson: ServiceDiagnosticSeverityExtension.toJson) ServiceDiagnosticSeverity severity, String summary, String? detail, String? hint, ServiceDiagnosticSection semanticRefs, ServiceDiagnosticSection invocationContext, ServiceDiagnosticSection provenance,@JsonKey(fromJson: ServiceDiagnosticResolutionStatusExtension.fromJson, toJson: ServiceDiagnosticResolutionStatusExtension.toJson) ServiceDiagnosticResolutionStatus resolutionStatus, ServiceDiagnosticSection? debug
});


@override $ServiceDiagnosticSectionCopyWith<$Res> get semanticRefs;@override $ServiceDiagnosticSectionCopyWith<$Res> get invocationContext;@override $ServiceDiagnosticSectionCopyWith<$Res> get provenance;@override $ServiceDiagnosticSectionCopyWith<$Res>? get debug;

}
/// @nodoc
class __$ServiceDiagnosticCopyWithImpl<$Res>
    implements _$ServiceDiagnosticCopyWith<$Res> {
  __$ServiceDiagnosticCopyWithImpl(this._self, this._then);

  final _ServiceDiagnostic _self;
  final $Res Function(_ServiceDiagnostic) _then;

/// Create a copy of ServiceDiagnostic
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? code = null,Object? category = null,Object? severity = null,Object? summary = null,Object? detail = freezed,Object? hint = freezed,Object? semanticRefs = null,Object? invocationContext = null,Object? provenance = null,Object? resolutionStatus = null,Object? debug = freezed,}) {
  return _then(_ServiceDiagnostic(
code: null == code ? _self.code : code // ignore: cast_nullable_to_non_nullable
as String,category: null == category ? _self.category : category // ignore: cast_nullable_to_non_nullable
as ServiceDiagnosticCategory,severity: null == severity ? _self.severity : severity // ignore: cast_nullable_to_non_nullable
as ServiceDiagnosticSeverity,summary: null == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String,detail: freezed == detail ? _self.detail : detail // ignore: cast_nullable_to_non_nullable
as String?,hint: freezed == hint ? _self.hint : hint // ignore: cast_nullable_to_non_nullable
as String?,semanticRefs: null == semanticRefs ? _self.semanticRefs : semanticRefs // ignore: cast_nullable_to_non_nullable
as ServiceDiagnosticSection,invocationContext: null == invocationContext ? _self.invocationContext : invocationContext // ignore: cast_nullable_to_non_nullable
as ServiceDiagnosticSection,provenance: null == provenance ? _self.provenance : provenance // ignore: cast_nullable_to_non_nullable
as ServiceDiagnosticSection,resolutionStatus: null == resolutionStatus ? _self.resolutionStatus : resolutionStatus // ignore: cast_nullable_to_non_nullable
as ServiceDiagnosticResolutionStatus,debug: freezed == debug ? _self.debug : debug // ignore: cast_nullable_to_non_nullable
as ServiceDiagnosticSection?,
  ));
}

/// Create a copy of ServiceDiagnostic
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceDiagnosticSectionCopyWith<$Res> get semanticRefs {
  
  return $ServiceDiagnosticSectionCopyWith<$Res>(_self.semanticRefs, (value) {
    return _then(_self.copyWith(semanticRefs: value));
  });
}/// Create a copy of ServiceDiagnostic
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceDiagnosticSectionCopyWith<$Res> get invocationContext {
  
  return $ServiceDiagnosticSectionCopyWith<$Res>(_self.invocationContext, (value) {
    return _then(_self.copyWith(invocationContext: value));
  });
}/// Create a copy of ServiceDiagnostic
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceDiagnosticSectionCopyWith<$Res> get provenance {
  
  return $ServiceDiagnosticSectionCopyWith<$Res>(_self.provenance, (value) {
    return _then(_self.copyWith(provenance: value));
  });
}/// Create a copy of ServiceDiagnostic
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceDiagnosticSectionCopyWith<$Res>? get debug {
    if (_self.debug == null) {
    return null;
  }

  return $ServiceDiagnosticSectionCopyWith<$Res>(_self.debug!, (value) {
    return _then(_self.copyWith(debug: value));
  });
}
}

// dart format on
