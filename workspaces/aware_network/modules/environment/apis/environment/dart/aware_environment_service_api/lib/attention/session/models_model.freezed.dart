// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'models_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$AttentionSessionPin {

@UuidValueConverter() UuidValue get attentionSessionId;@UuidValueConverter() UuidValue get identitySessionId;@UuidValueConverter() UuidValue? get activeLayoutId; String? get key; String? get title; String? get description; String? get purpose; String get status; String? get sourceKind; String? get sourceRef; Map<String, dynamic> get metadataJson;
/// Create a copy of AttentionSessionPin
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$AttentionSessionPinCopyWith<AttentionSessionPin> get copyWith => _$AttentionSessionPinCopyWithImpl<AttentionSessionPin>(this as AttentionSessionPin, _$identity);

  /// Serializes this AttentionSessionPin to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is AttentionSessionPin&&(identical(other.attentionSessionId, attentionSessionId) || other.attentionSessionId == attentionSessionId)&&(identical(other.identitySessionId, identitySessionId) || other.identitySessionId == identitySessionId)&&(identical(other.activeLayoutId, activeLayoutId) || other.activeLayoutId == activeLayoutId)&&(identical(other.key, key) || other.key == key)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.purpose, purpose) || other.purpose == purpose)&&(identical(other.status, status) || other.status == status)&&(identical(other.sourceKind, sourceKind) || other.sourceKind == sourceKind)&&(identical(other.sourceRef, sourceRef) || other.sourceRef == sourceRef)&&const DeepCollectionEquality().equals(other.metadataJson, metadataJson));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,attentionSessionId,identitySessionId,activeLayoutId,key,title,description,purpose,status,sourceKind,sourceRef,const DeepCollectionEquality().hash(metadataJson));

@override
String toString() {
  return 'AttentionSessionPin(attentionSessionId: $attentionSessionId, identitySessionId: $identitySessionId, activeLayoutId: $activeLayoutId, key: $key, title: $title, description: $description, purpose: $purpose, status: $status, sourceKind: $sourceKind, sourceRef: $sourceRef, metadataJson: $metadataJson)';
}


}

/// @nodoc
abstract mixin class $AttentionSessionPinCopyWith<$Res>  {
  factory $AttentionSessionPinCopyWith(AttentionSessionPin value, $Res Function(AttentionSessionPin) _then) = _$AttentionSessionPinCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue attentionSessionId,@UuidValueConverter() UuidValue identitySessionId,@UuidValueConverter() UuidValue? activeLayoutId, String? key, String? title, String? description, String? purpose, String status, String? sourceKind, String? sourceRef, Map<String, dynamic> metadataJson
});




}
/// @nodoc
class _$AttentionSessionPinCopyWithImpl<$Res>
    implements $AttentionSessionPinCopyWith<$Res> {
  _$AttentionSessionPinCopyWithImpl(this._self, this._then);

  final AttentionSessionPin _self;
  final $Res Function(AttentionSessionPin) _then;

/// Create a copy of AttentionSessionPin
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? attentionSessionId = null,Object? identitySessionId = null,Object? activeLayoutId = freezed,Object? key = freezed,Object? title = freezed,Object? description = freezed,Object? purpose = freezed,Object? status = null,Object? sourceKind = freezed,Object? sourceRef = freezed,Object? metadataJson = null,}) {
  return _then(_self.copyWith(
attentionSessionId: null == attentionSessionId ? _self.attentionSessionId : attentionSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,identitySessionId: null == identitySessionId ? _self.identitySessionId : identitySessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,activeLayoutId: freezed == activeLayoutId ? _self.activeLayoutId : activeLayoutId // ignore: cast_nullable_to_non_nullable
as UuidValue?,key: freezed == key ? _self.key : key // ignore: cast_nullable_to_non_nullable
as String?,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,purpose: freezed == purpose ? _self.purpose : purpose // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,sourceKind: freezed == sourceKind ? _self.sourceKind : sourceKind // ignore: cast_nullable_to_non_nullable
as String?,sourceRef: freezed == sourceRef ? _self.sourceRef : sourceRef // ignore: cast_nullable_to_non_nullable
as String?,metadataJson: null == metadataJson ? _self.metadataJson : metadataJson // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [AttentionSessionPin].
extension AttentionSessionPinPatterns on AttentionSessionPin {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _AttentionSessionPin value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _AttentionSessionPin() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _AttentionSessionPin value)  def,}){
final _that = this;
switch (_that) {
case _AttentionSessionPin():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _AttentionSessionPin value)?  def,}){
final _that = this;
switch (_that) {
case _AttentionSessionPin() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue attentionSessionId, @UuidValueConverter()  UuidValue identitySessionId, @UuidValueConverter()  UuidValue? activeLayoutId,  String? key,  String? title,  String? description,  String? purpose,  String status,  String? sourceKind,  String? sourceRef,  Map<String, dynamic> metadataJson)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _AttentionSessionPin() when def != null:
return def(_that.attentionSessionId,_that.identitySessionId,_that.activeLayoutId,_that.key,_that.title,_that.description,_that.purpose,_that.status,_that.sourceKind,_that.sourceRef,_that.metadataJson);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue attentionSessionId, @UuidValueConverter()  UuidValue identitySessionId, @UuidValueConverter()  UuidValue? activeLayoutId,  String? key,  String? title,  String? description,  String? purpose,  String status,  String? sourceKind,  String? sourceRef,  Map<String, dynamic> metadataJson)  def,}) {final _that = this;
switch (_that) {
case _AttentionSessionPin():
return def(_that.attentionSessionId,_that.identitySessionId,_that.activeLayoutId,_that.key,_that.title,_that.description,_that.purpose,_that.status,_that.sourceKind,_that.sourceRef,_that.metadataJson);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue attentionSessionId, @UuidValueConverter()  UuidValue identitySessionId, @UuidValueConverter()  UuidValue? activeLayoutId,  String? key,  String? title,  String? description,  String? purpose,  String status,  String? sourceKind,  String? sourceRef,  Map<String, dynamic> metadataJson)?  def,}) {final _that = this;
switch (_that) {
case _AttentionSessionPin() when def != null:
return def(_that.attentionSessionId,_that.identitySessionId,_that.activeLayoutId,_that.key,_that.title,_that.description,_that.purpose,_that.status,_that.sourceKind,_that.sourceRef,_that.metadataJson);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _AttentionSessionPin implements AttentionSessionPin {
   _AttentionSessionPin({@UuidValueConverter() required this.attentionSessionId, @UuidValueConverter() required this.identitySessionId, @UuidValueConverter() this.activeLayoutId, this.key, this.title, this.description, this.purpose, required this.status, this.sourceKind, this.sourceRef, required final  Map<String, dynamic> metadataJson}): _metadataJson = metadataJson;
  factory _AttentionSessionPin.fromJson(Map<String, dynamic> json) => _$AttentionSessionPinFromJson(json);

@override@UuidValueConverter() final  UuidValue attentionSessionId;
@override@UuidValueConverter() final  UuidValue identitySessionId;
@override@UuidValueConverter() final  UuidValue? activeLayoutId;
@override final  String? key;
@override final  String? title;
@override final  String? description;
@override final  String? purpose;
@override final  String status;
@override final  String? sourceKind;
@override final  String? sourceRef;
 final  Map<String, dynamic> _metadataJson;
@override Map<String, dynamic> get metadataJson {
  if (_metadataJson is EqualUnmodifiableMapView) return _metadataJson;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_metadataJson);
}


/// Create a copy of AttentionSessionPin
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$AttentionSessionPinCopyWith<_AttentionSessionPin> get copyWith => __$AttentionSessionPinCopyWithImpl<_AttentionSessionPin>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$AttentionSessionPinToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _AttentionSessionPin&&(identical(other.attentionSessionId, attentionSessionId) || other.attentionSessionId == attentionSessionId)&&(identical(other.identitySessionId, identitySessionId) || other.identitySessionId == identitySessionId)&&(identical(other.activeLayoutId, activeLayoutId) || other.activeLayoutId == activeLayoutId)&&(identical(other.key, key) || other.key == key)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.purpose, purpose) || other.purpose == purpose)&&(identical(other.status, status) || other.status == status)&&(identical(other.sourceKind, sourceKind) || other.sourceKind == sourceKind)&&(identical(other.sourceRef, sourceRef) || other.sourceRef == sourceRef)&&const DeepCollectionEquality().equals(other._metadataJson, _metadataJson));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,attentionSessionId,identitySessionId,activeLayoutId,key,title,description,purpose,status,sourceKind,sourceRef,const DeepCollectionEquality().hash(_metadataJson));

@override
String toString() {
  return 'AttentionSessionPin.def(attentionSessionId: $attentionSessionId, identitySessionId: $identitySessionId, activeLayoutId: $activeLayoutId, key: $key, title: $title, description: $description, purpose: $purpose, status: $status, sourceKind: $sourceKind, sourceRef: $sourceRef, metadataJson: $metadataJson)';
}


}

/// @nodoc
abstract mixin class _$AttentionSessionPinCopyWith<$Res> implements $AttentionSessionPinCopyWith<$Res> {
  factory _$AttentionSessionPinCopyWith(_AttentionSessionPin value, $Res Function(_AttentionSessionPin) _then) = __$AttentionSessionPinCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue attentionSessionId,@UuidValueConverter() UuidValue identitySessionId,@UuidValueConverter() UuidValue? activeLayoutId, String? key, String? title, String? description, String? purpose, String status, String? sourceKind, String? sourceRef, Map<String, dynamic> metadataJson
});




}
/// @nodoc
class __$AttentionSessionPinCopyWithImpl<$Res>
    implements _$AttentionSessionPinCopyWith<$Res> {
  __$AttentionSessionPinCopyWithImpl(this._self, this._then);

  final _AttentionSessionPin _self;
  final $Res Function(_AttentionSessionPin) _then;

/// Create a copy of AttentionSessionPin
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? attentionSessionId = null,Object? identitySessionId = null,Object? activeLayoutId = freezed,Object? key = freezed,Object? title = freezed,Object? description = freezed,Object? purpose = freezed,Object? status = null,Object? sourceKind = freezed,Object? sourceRef = freezed,Object? metadataJson = null,}) {
  return _then(_AttentionSessionPin(
attentionSessionId: null == attentionSessionId ? _self.attentionSessionId : attentionSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,identitySessionId: null == identitySessionId ? _self.identitySessionId : identitySessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,activeLayoutId: freezed == activeLayoutId ? _self.activeLayoutId : activeLayoutId // ignore: cast_nullable_to_non_nullable
as UuidValue?,key: freezed == key ? _self.key : key // ignore: cast_nullable_to_non_nullable
as String?,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,purpose: freezed == purpose ? _self.purpose : purpose // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,sourceKind: freezed == sourceKind ? _self.sourceKind : sourceKind // ignore: cast_nullable_to_non_nullable
as String?,sourceRef: freezed == sourceRef ? _self.sourceRef : sourceRef // ignore: cast_nullable_to_non_nullable
as String?,metadataJson: null == metadataJson ? _self._metadataJson : metadataJson // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$AttentionFocusTransitionPin {

@UuidValueConverter() UuidValue get attentionFocusTransitionId;@UuidValueConverter() UuidValue get attentionSessionSectionId;@UuidValueConverter() UuidValue? get attentionSessionLayoutId;@UuidValueConverter() UuidValue? get attentionSessionId;@UuidValueConverter() UuidValue? get identitySessionId;@UuidValueConverter() UuidValue? get layoutSectionId;@UuidValueConverter() UuidValue? get sectionId; String? get sectionKey;@UuidValueConverter() UuidValue? get layoutId;@UuidValueConverter() UuidValue? get layoutConfigId;@UuidValueConverter() UuidValue? get previousTransitionId;@UuidValueConverter() UuidValue get focusScopeId;@UuidValueConverter() UuidValue? get focusId;@UuidValueConverter() UuidValue? get observableId;@UuidValueConverter() UuidValue? get objectProjectionGraphIdentityId;@UuidValueConverter() UuidValue? get objectInstanceGraphBranchId;@UuidValueConverter() UuidValue? get objectInstanceGraphCommitId; String get transitionKey; int get sequence; String? get projectionHash; String get transitionKind; String? get rationale; String? get sourceKind; String? get sourceRef; Map<String, dynamic> get metadataJson;
/// Create a copy of AttentionFocusTransitionPin
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$AttentionFocusTransitionPinCopyWith<AttentionFocusTransitionPin> get copyWith => _$AttentionFocusTransitionPinCopyWithImpl<AttentionFocusTransitionPin>(this as AttentionFocusTransitionPin, _$identity);

  /// Serializes this AttentionFocusTransitionPin to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is AttentionFocusTransitionPin&&(identical(other.attentionFocusTransitionId, attentionFocusTransitionId) || other.attentionFocusTransitionId == attentionFocusTransitionId)&&(identical(other.attentionSessionSectionId, attentionSessionSectionId) || other.attentionSessionSectionId == attentionSessionSectionId)&&(identical(other.attentionSessionLayoutId, attentionSessionLayoutId) || other.attentionSessionLayoutId == attentionSessionLayoutId)&&(identical(other.attentionSessionId, attentionSessionId) || other.attentionSessionId == attentionSessionId)&&(identical(other.identitySessionId, identitySessionId) || other.identitySessionId == identitySessionId)&&(identical(other.layoutSectionId, layoutSectionId) || other.layoutSectionId == layoutSectionId)&&(identical(other.sectionId, sectionId) || other.sectionId == sectionId)&&(identical(other.sectionKey, sectionKey) || other.sectionKey == sectionKey)&&(identical(other.layoutId, layoutId) || other.layoutId == layoutId)&&(identical(other.layoutConfigId, layoutConfigId) || other.layoutConfigId == layoutConfigId)&&(identical(other.previousTransitionId, previousTransitionId) || other.previousTransitionId == previousTransitionId)&&(identical(other.focusScopeId, focusScopeId) || other.focusScopeId == focusScopeId)&&(identical(other.focusId, focusId) || other.focusId == focusId)&&(identical(other.observableId, observableId) || other.observableId == observableId)&&(identical(other.objectProjectionGraphIdentityId, objectProjectionGraphIdentityId) || other.objectProjectionGraphIdentityId == objectProjectionGraphIdentityId)&&(identical(other.objectInstanceGraphBranchId, objectInstanceGraphBranchId) || other.objectInstanceGraphBranchId == objectInstanceGraphBranchId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.transitionKey, transitionKey) || other.transitionKey == transitionKey)&&(identical(other.sequence, sequence) || other.sequence == sequence)&&(identical(other.projectionHash, projectionHash) || other.projectionHash == projectionHash)&&(identical(other.transitionKind, transitionKind) || other.transitionKind == transitionKind)&&(identical(other.rationale, rationale) || other.rationale == rationale)&&(identical(other.sourceKind, sourceKind) || other.sourceKind == sourceKind)&&(identical(other.sourceRef, sourceRef) || other.sourceRef == sourceRef)&&const DeepCollectionEquality().equals(other.metadataJson, metadataJson));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,attentionFocusTransitionId,attentionSessionSectionId,attentionSessionLayoutId,attentionSessionId,identitySessionId,layoutSectionId,sectionId,sectionKey,layoutId,layoutConfigId,previousTransitionId,focusScopeId,focusId,observableId,objectProjectionGraphIdentityId,objectInstanceGraphBranchId,objectInstanceGraphCommitId,transitionKey,sequence,projectionHash,transitionKind,rationale,sourceKind,sourceRef,const DeepCollectionEquality().hash(metadataJson)]);

@override
String toString() {
  return 'AttentionFocusTransitionPin(attentionFocusTransitionId: $attentionFocusTransitionId, attentionSessionSectionId: $attentionSessionSectionId, attentionSessionLayoutId: $attentionSessionLayoutId, attentionSessionId: $attentionSessionId, identitySessionId: $identitySessionId, layoutSectionId: $layoutSectionId, sectionId: $sectionId, sectionKey: $sectionKey, layoutId: $layoutId, layoutConfigId: $layoutConfigId, previousTransitionId: $previousTransitionId, focusScopeId: $focusScopeId, focusId: $focusId, observableId: $observableId, objectProjectionGraphIdentityId: $objectProjectionGraphIdentityId, objectInstanceGraphBranchId: $objectInstanceGraphBranchId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, transitionKey: $transitionKey, sequence: $sequence, projectionHash: $projectionHash, transitionKind: $transitionKind, rationale: $rationale, sourceKind: $sourceKind, sourceRef: $sourceRef, metadataJson: $metadataJson)';
}


}

/// @nodoc
abstract mixin class $AttentionFocusTransitionPinCopyWith<$Res>  {
  factory $AttentionFocusTransitionPinCopyWith(AttentionFocusTransitionPin value, $Res Function(AttentionFocusTransitionPin) _then) = _$AttentionFocusTransitionPinCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue attentionFocusTransitionId,@UuidValueConverter() UuidValue attentionSessionSectionId,@UuidValueConverter() UuidValue? attentionSessionLayoutId,@UuidValueConverter() UuidValue? attentionSessionId,@UuidValueConverter() UuidValue? identitySessionId,@UuidValueConverter() UuidValue? layoutSectionId,@UuidValueConverter() UuidValue? sectionId, String? sectionKey,@UuidValueConverter() UuidValue? layoutId,@UuidValueConverter() UuidValue? layoutConfigId,@UuidValueConverter() UuidValue? previousTransitionId,@UuidValueConverter() UuidValue focusScopeId,@UuidValueConverter() UuidValue? focusId,@UuidValueConverter() UuidValue? observableId,@UuidValueConverter() UuidValue? objectProjectionGraphIdentityId,@UuidValueConverter() UuidValue? objectInstanceGraphBranchId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String transitionKey, int sequence, String? projectionHash, String transitionKind, String? rationale, String? sourceKind, String? sourceRef, Map<String, dynamic> metadataJson
});




}
/// @nodoc
class _$AttentionFocusTransitionPinCopyWithImpl<$Res>
    implements $AttentionFocusTransitionPinCopyWith<$Res> {
  _$AttentionFocusTransitionPinCopyWithImpl(this._self, this._then);

  final AttentionFocusTransitionPin _self;
  final $Res Function(AttentionFocusTransitionPin) _then;

/// Create a copy of AttentionFocusTransitionPin
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? attentionFocusTransitionId = null,Object? attentionSessionSectionId = null,Object? attentionSessionLayoutId = freezed,Object? attentionSessionId = freezed,Object? identitySessionId = freezed,Object? layoutSectionId = freezed,Object? sectionId = freezed,Object? sectionKey = freezed,Object? layoutId = freezed,Object? layoutConfigId = freezed,Object? previousTransitionId = freezed,Object? focusScopeId = null,Object? focusId = freezed,Object? observableId = freezed,Object? objectProjectionGraphIdentityId = freezed,Object? objectInstanceGraphBranchId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? transitionKey = null,Object? sequence = null,Object? projectionHash = freezed,Object? transitionKind = null,Object? rationale = freezed,Object? sourceKind = freezed,Object? sourceRef = freezed,Object? metadataJson = null,}) {
  return _then(_self.copyWith(
attentionFocusTransitionId: null == attentionFocusTransitionId ? _self.attentionFocusTransitionId : attentionFocusTransitionId // ignore: cast_nullable_to_non_nullable
as UuidValue,attentionSessionSectionId: null == attentionSessionSectionId ? _self.attentionSessionSectionId : attentionSessionSectionId // ignore: cast_nullable_to_non_nullable
as UuidValue,attentionSessionLayoutId: freezed == attentionSessionLayoutId ? _self.attentionSessionLayoutId : attentionSessionLayoutId // ignore: cast_nullable_to_non_nullable
as UuidValue?,attentionSessionId: freezed == attentionSessionId ? _self.attentionSessionId : attentionSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,identitySessionId: freezed == identitySessionId ? _self.identitySessionId : identitySessionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,layoutSectionId: freezed == layoutSectionId ? _self.layoutSectionId : layoutSectionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sectionId: freezed == sectionId ? _self.sectionId : sectionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sectionKey: freezed == sectionKey ? _self.sectionKey : sectionKey // ignore: cast_nullable_to_non_nullable
as String?,layoutId: freezed == layoutId ? _self.layoutId : layoutId // ignore: cast_nullable_to_non_nullable
as UuidValue?,layoutConfigId: freezed == layoutConfigId ? _self.layoutConfigId : layoutConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,previousTransitionId: freezed == previousTransitionId ? _self.previousTransitionId : previousTransitionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,focusScopeId: null == focusScopeId ? _self.focusScopeId : focusScopeId // ignore: cast_nullable_to_non_nullable
as UuidValue,focusId: freezed == focusId ? _self.focusId : focusId // ignore: cast_nullable_to_non_nullable
as UuidValue?,observableId: freezed == observableId ? _self.observableId : observableId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectProjectionGraphIdentityId: freezed == objectProjectionGraphIdentityId ? _self.objectProjectionGraphIdentityId : objectProjectionGraphIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphBranchId: freezed == objectInstanceGraphBranchId ? _self.objectInstanceGraphBranchId : objectInstanceGraphBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,transitionKey: null == transitionKey ? _self.transitionKey : transitionKey // ignore: cast_nullable_to_non_nullable
as String,sequence: null == sequence ? _self.sequence : sequence // ignore: cast_nullable_to_non_nullable
as int,projectionHash: freezed == projectionHash ? _self.projectionHash : projectionHash // ignore: cast_nullable_to_non_nullable
as String?,transitionKind: null == transitionKind ? _self.transitionKind : transitionKind // ignore: cast_nullable_to_non_nullable
as String,rationale: freezed == rationale ? _self.rationale : rationale // ignore: cast_nullable_to_non_nullable
as String?,sourceKind: freezed == sourceKind ? _self.sourceKind : sourceKind // ignore: cast_nullable_to_non_nullable
as String?,sourceRef: freezed == sourceRef ? _self.sourceRef : sourceRef // ignore: cast_nullable_to_non_nullable
as String?,metadataJson: null == metadataJson ? _self.metadataJson : metadataJson // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [AttentionFocusTransitionPin].
extension AttentionFocusTransitionPinPatterns on AttentionFocusTransitionPin {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _AttentionFocusTransitionPin value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _AttentionFocusTransitionPin() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _AttentionFocusTransitionPin value)  def,}){
final _that = this;
switch (_that) {
case _AttentionFocusTransitionPin():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _AttentionFocusTransitionPin value)?  def,}){
final _that = this;
switch (_that) {
case _AttentionFocusTransitionPin() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue attentionFocusTransitionId, @UuidValueConverter()  UuidValue attentionSessionSectionId, @UuidValueConverter()  UuidValue? attentionSessionLayoutId, @UuidValueConverter()  UuidValue? attentionSessionId, @UuidValueConverter()  UuidValue? identitySessionId, @UuidValueConverter()  UuidValue? layoutSectionId, @UuidValueConverter()  UuidValue? sectionId,  String? sectionKey, @UuidValueConverter()  UuidValue? layoutId, @UuidValueConverter()  UuidValue? layoutConfigId, @UuidValueConverter()  UuidValue? previousTransitionId, @UuidValueConverter()  UuidValue focusScopeId, @UuidValueConverter()  UuidValue? focusId, @UuidValueConverter()  UuidValue? observableId, @UuidValueConverter()  UuidValue? objectProjectionGraphIdentityId, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String transitionKey,  int sequence,  String? projectionHash,  String transitionKind,  String? rationale,  String? sourceKind,  String? sourceRef,  Map<String, dynamic> metadataJson)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _AttentionFocusTransitionPin() when def != null:
return def(_that.attentionFocusTransitionId,_that.attentionSessionSectionId,_that.attentionSessionLayoutId,_that.attentionSessionId,_that.identitySessionId,_that.layoutSectionId,_that.sectionId,_that.sectionKey,_that.layoutId,_that.layoutConfigId,_that.previousTransitionId,_that.focusScopeId,_that.focusId,_that.observableId,_that.objectProjectionGraphIdentityId,_that.objectInstanceGraphBranchId,_that.objectInstanceGraphCommitId,_that.transitionKey,_that.sequence,_that.projectionHash,_that.transitionKind,_that.rationale,_that.sourceKind,_that.sourceRef,_that.metadataJson);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue attentionFocusTransitionId, @UuidValueConverter()  UuidValue attentionSessionSectionId, @UuidValueConverter()  UuidValue? attentionSessionLayoutId, @UuidValueConverter()  UuidValue? attentionSessionId, @UuidValueConverter()  UuidValue? identitySessionId, @UuidValueConverter()  UuidValue? layoutSectionId, @UuidValueConverter()  UuidValue? sectionId,  String? sectionKey, @UuidValueConverter()  UuidValue? layoutId, @UuidValueConverter()  UuidValue? layoutConfigId, @UuidValueConverter()  UuidValue? previousTransitionId, @UuidValueConverter()  UuidValue focusScopeId, @UuidValueConverter()  UuidValue? focusId, @UuidValueConverter()  UuidValue? observableId, @UuidValueConverter()  UuidValue? objectProjectionGraphIdentityId, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String transitionKey,  int sequence,  String? projectionHash,  String transitionKind,  String? rationale,  String? sourceKind,  String? sourceRef,  Map<String, dynamic> metadataJson)  def,}) {final _that = this;
switch (_that) {
case _AttentionFocusTransitionPin():
return def(_that.attentionFocusTransitionId,_that.attentionSessionSectionId,_that.attentionSessionLayoutId,_that.attentionSessionId,_that.identitySessionId,_that.layoutSectionId,_that.sectionId,_that.sectionKey,_that.layoutId,_that.layoutConfigId,_that.previousTransitionId,_that.focusScopeId,_that.focusId,_that.observableId,_that.objectProjectionGraphIdentityId,_that.objectInstanceGraphBranchId,_that.objectInstanceGraphCommitId,_that.transitionKey,_that.sequence,_that.projectionHash,_that.transitionKind,_that.rationale,_that.sourceKind,_that.sourceRef,_that.metadataJson);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue attentionFocusTransitionId, @UuidValueConverter()  UuidValue attentionSessionSectionId, @UuidValueConverter()  UuidValue? attentionSessionLayoutId, @UuidValueConverter()  UuidValue? attentionSessionId, @UuidValueConverter()  UuidValue? identitySessionId, @UuidValueConverter()  UuidValue? layoutSectionId, @UuidValueConverter()  UuidValue? sectionId,  String? sectionKey, @UuidValueConverter()  UuidValue? layoutId, @UuidValueConverter()  UuidValue? layoutConfigId, @UuidValueConverter()  UuidValue? previousTransitionId, @UuidValueConverter()  UuidValue focusScopeId, @UuidValueConverter()  UuidValue? focusId, @UuidValueConverter()  UuidValue? observableId, @UuidValueConverter()  UuidValue? objectProjectionGraphIdentityId, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String transitionKey,  int sequence,  String? projectionHash,  String transitionKind,  String? rationale,  String? sourceKind,  String? sourceRef,  Map<String, dynamic> metadataJson)?  def,}) {final _that = this;
switch (_that) {
case _AttentionFocusTransitionPin() when def != null:
return def(_that.attentionFocusTransitionId,_that.attentionSessionSectionId,_that.attentionSessionLayoutId,_that.attentionSessionId,_that.identitySessionId,_that.layoutSectionId,_that.sectionId,_that.sectionKey,_that.layoutId,_that.layoutConfigId,_that.previousTransitionId,_that.focusScopeId,_that.focusId,_that.observableId,_that.objectProjectionGraphIdentityId,_that.objectInstanceGraphBranchId,_that.objectInstanceGraphCommitId,_that.transitionKey,_that.sequence,_that.projectionHash,_that.transitionKind,_that.rationale,_that.sourceKind,_that.sourceRef,_that.metadataJson);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _AttentionFocusTransitionPin implements AttentionFocusTransitionPin {
   _AttentionFocusTransitionPin({@UuidValueConverter() required this.attentionFocusTransitionId, @UuidValueConverter() required this.attentionSessionSectionId, @UuidValueConverter() this.attentionSessionLayoutId, @UuidValueConverter() this.attentionSessionId, @UuidValueConverter() this.identitySessionId, @UuidValueConverter() this.layoutSectionId, @UuidValueConverter() this.sectionId, this.sectionKey, @UuidValueConverter() this.layoutId, @UuidValueConverter() this.layoutConfigId, @UuidValueConverter() this.previousTransitionId, @UuidValueConverter() required this.focusScopeId, @UuidValueConverter() this.focusId, @UuidValueConverter() this.observableId, @UuidValueConverter() this.objectProjectionGraphIdentityId, @UuidValueConverter() this.objectInstanceGraphBranchId, @UuidValueConverter() this.objectInstanceGraphCommitId, required this.transitionKey, required this.sequence, this.projectionHash, required this.transitionKind, this.rationale, this.sourceKind, this.sourceRef, required final  Map<String, dynamic> metadataJson}): _metadataJson = metadataJson;
  factory _AttentionFocusTransitionPin.fromJson(Map<String, dynamic> json) => _$AttentionFocusTransitionPinFromJson(json);

@override@UuidValueConverter() final  UuidValue attentionFocusTransitionId;
@override@UuidValueConverter() final  UuidValue attentionSessionSectionId;
@override@UuidValueConverter() final  UuidValue? attentionSessionLayoutId;
@override@UuidValueConverter() final  UuidValue? attentionSessionId;
@override@UuidValueConverter() final  UuidValue? identitySessionId;
@override@UuidValueConverter() final  UuidValue? layoutSectionId;
@override@UuidValueConverter() final  UuidValue? sectionId;
@override final  String? sectionKey;
@override@UuidValueConverter() final  UuidValue? layoutId;
@override@UuidValueConverter() final  UuidValue? layoutConfigId;
@override@UuidValueConverter() final  UuidValue? previousTransitionId;
@override@UuidValueConverter() final  UuidValue focusScopeId;
@override@UuidValueConverter() final  UuidValue? focusId;
@override@UuidValueConverter() final  UuidValue? observableId;
@override@UuidValueConverter() final  UuidValue? objectProjectionGraphIdentityId;
@override@UuidValueConverter() final  UuidValue? objectInstanceGraphBranchId;
@override@UuidValueConverter() final  UuidValue? objectInstanceGraphCommitId;
@override final  String transitionKey;
@override final  int sequence;
@override final  String? projectionHash;
@override final  String transitionKind;
@override final  String? rationale;
@override final  String? sourceKind;
@override final  String? sourceRef;
 final  Map<String, dynamic> _metadataJson;
@override Map<String, dynamic> get metadataJson {
  if (_metadataJson is EqualUnmodifiableMapView) return _metadataJson;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_metadataJson);
}


/// Create a copy of AttentionFocusTransitionPin
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$AttentionFocusTransitionPinCopyWith<_AttentionFocusTransitionPin> get copyWith => __$AttentionFocusTransitionPinCopyWithImpl<_AttentionFocusTransitionPin>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$AttentionFocusTransitionPinToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _AttentionFocusTransitionPin&&(identical(other.attentionFocusTransitionId, attentionFocusTransitionId) || other.attentionFocusTransitionId == attentionFocusTransitionId)&&(identical(other.attentionSessionSectionId, attentionSessionSectionId) || other.attentionSessionSectionId == attentionSessionSectionId)&&(identical(other.attentionSessionLayoutId, attentionSessionLayoutId) || other.attentionSessionLayoutId == attentionSessionLayoutId)&&(identical(other.attentionSessionId, attentionSessionId) || other.attentionSessionId == attentionSessionId)&&(identical(other.identitySessionId, identitySessionId) || other.identitySessionId == identitySessionId)&&(identical(other.layoutSectionId, layoutSectionId) || other.layoutSectionId == layoutSectionId)&&(identical(other.sectionId, sectionId) || other.sectionId == sectionId)&&(identical(other.sectionKey, sectionKey) || other.sectionKey == sectionKey)&&(identical(other.layoutId, layoutId) || other.layoutId == layoutId)&&(identical(other.layoutConfigId, layoutConfigId) || other.layoutConfigId == layoutConfigId)&&(identical(other.previousTransitionId, previousTransitionId) || other.previousTransitionId == previousTransitionId)&&(identical(other.focusScopeId, focusScopeId) || other.focusScopeId == focusScopeId)&&(identical(other.focusId, focusId) || other.focusId == focusId)&&(identical(other.observableId, observableId) || other.observableId == observableId)&&(identical(other.objectProjectionGraphIdentityId, objectProjectionGraphIdentityId) || other.objectProjectionGraphIdentityId == objectProjectionGraphIdentityId)&&(identical(other.objectInstanceGraphBranchId, objectInstanceGraphBranchId) || other.objectInstanceGraphBranchId == objectInstanceGraphBranchId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.transitionKey, transitionKey) || other.transitionKey == transitionKey)&&(identical(other.sequence, sequence) || other.sequence == sequence)&&(identical(other.projectionHash, projectionHash) || other.projectionHash == projectionHash)&&(identical(other.transitionKind, transitionKind) || other.transitionKind == transitionKind)&&(identical(other.rationale, rationale) || other.rationale == rationale)&&(identical(other.sourceKind, sourceKind) || other.sourceKind == sourceKind)&&(identical(other.sourceRef, sourceRef) || other.sourceRef == sourceRef)&&const DeepCollectionEquality().equals(other._metadataJson, _metadataJson));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,attentionFocusTransitionId,attentionSessionSectionId,attentionSessionLayoutId,attentionSessionId,identitySessionId,layoutSectionId,sectionId,sectionKey,layoutId,layoutConfigId,previousTransitionId,focusScopeId,focusId,observableId,objectProjectionGraphIdentityId,objectInstanceGraphBranchId,objectInstanceGraphCommitId,transitionKey,sequence,projectionHash,transitionKind,rationale,sourceKind,sourceRef,const DeepCollectionEquality().hash(_metadataJson)]);

@override
String toString() {
  return 'AttentionFocusTransitionPin.def(attentionFocusTransitionId: $attentionFocusTransitionId, attentionSessionSectionId: $attentionSessionSectionId, attentionSessionLayoutId: $attentionSessionLayoutId, attentionSessionId: $attentionSessionId, identitySessionId: $identitySessionId, layoutSectionId: $layoutSectionId, sectionId: $sectionId, sectionKey: $sectionKey, layoutId: $layoutId, layoutConfigId: $layoutConfigId, previousTransitionId: $previousTransitionId, focusScopeId: $focusScopeId, focusId: $focusId, observableId: $observableId, objectProjectionGraphIdentityId: $objectProjectionGraphIdentityId, objectInstanceGraphBranchId: $objectInstanceGraphBranchId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, transitionKey: $transitionKey, sequence: $sequence, projectionHash: $projectionHash, transitionKind: $transitionKind, rationale: $rationale, sourceKind: $sourceKind, sourceRef: $sourceRef, metadataJson: $metadataJson)';
}


}

/// @nodoc
abstract mixin class _$AttentionFocusTransitionPinCopyWith<$Res> implements $AttentionFocusTransitionPinCopyWith<$Res> {
  factory _$AttentionFocusTransitionPinCopyWith(_AttentionFocusTransitionPin value, $Res Function(_AttentionFocusTransitionPin) _then) = __$AttentionFocusTransitionPinCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue attentionFocusTransitionId,@UuidValueConverter() UuidValue attentionSessionSectionId,@UuidValueConverter() UuidValue? attentionSessionLayoutId,@UuidValueConverter() UuidValue? attentionSessionId,@UuidValueConverter() UuidValue? identitySessionId,@UuidValueConverter() UuidValue? layoutSectionId,@UuidValueConverter() UuidValue? sectionId, String? sectionKey,@UuidValueConverter() UuidValue? layoutId,@UuidValueConverter() UuidValue? layoutConfigId,@UuidValueConverter() UuidValue? previousTransitionId,@UuidValueConverter() UuidValue focusScopeId,@UuidValueConverter() UuidValue? focusId,@UuidValueConverter() UuidValue? observableId,@UuidValueConverter() UuidValue? objectProjectionGraphIdentityId,@UuidValueConverter() UuidValue? objectInstanceGraphBranchId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String transitionKey, int sequence, String? projectionHash, String transitionKind, String? rationale, String? sourceKind, String? sourceRef, Map<String, dynamic> metadataJson
});




}
/// @nodoc
class __$AttentionFocusTransitionPinCopyWithImpl<$Res>
    implements _$AttentionFocusTransitionPinCopyWith<$Res> {
  __$AttentionFocusTransitionPinCopyWithImpl(this._self, this._then);

  final _AttentionFocusTransitionPin _self;
  final $Res Function(_AttentionFocusTransitionPin) _then;

/// Create a copy of AttentionFocusTransitionPin
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? attentionFocusTransitionId = null,Object? attentionSessionSectionId = null,Object? attentionSessionLayoutId = freezed,Object? attentionSessionId = freezed,Object? identitySessionId = freezed,Object? layoutSectionId = freezed,Object? sectionId = freezed,Object? sectionKey = freezed,Object? layoutId = freezed,Object? layoutConfigId = freezed,Object? previousTransitionId = freezed,Object? focusScopeId = null,Object? focusId = freezed,Object? observableId = freezed,Object? objectProjectionGraphIdentityId = freezed,Object? objectInstanceGraphBranchId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? transitionKey = null,Object? sequence = null,Object? projectionHash = freezed,Object? transitionKind = null,Object? rationale = freezed,Object? sourceKind = freezed,Object? sourceRef = freezed,Object? metadataJson = null,}) {
  return _then(_AttentionFocusTransitionPin(
attentionFocusTransitionId: null == attentionFocusTransitionId ? _self.attentionFocusTransitionId : attentionFocusTransitionId // ignore: cast_nullable_to_non_nullable
as UuidValue,attentionSessionSectionId: null == attentionSessionSectionId ? _self.attentionSessionSectionId : attentionSessionSectionId // ignore: cast_nullable_to_non_nullable
as UuidValue,attentionSessionLayoutId: freezed == attentionSessionLayoutId ? _self.attentionSessionLayoutId : attentionSessionLayoutId // ignore: cast_nullable_to_non_nullable
as UuidValue?,attentionSessionId: freezed == attentionSessionId ? _self.attentionSessionId : attentionSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,identitySessionId: freezed == identitySessionId ? _self.identitySessionId : identitySessionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,layoutSectionId: freezed == layoutSectionId ? _self.layoutSectionId : layoutSectionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sectionId: freezed == sectionId ? _self.sectionId : sectionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sectionKey: freezed == sectionKey ? _self.sectionKey : sectionKey // ignore: cast_nullable_to_non_nullable
as String?,layoutId: freezed == layoutId ? _self.layoutId : layoutId // ignore: cast_nullable_to_non_nullable
as UuidValue?,layoutConfigId: freezed == layoutConfigId ? _self.layoutConfigId : layoutConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,previousTransitionId: freezed == previousTransitionId ? _self.previousTransitionId : previousTransitionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,focusScopeId: null == focusScopeId ? _self.focusScopeId : focusScopeId // ignore: cast_nullable_to_non_nullable
as UuidValue,focusId: freezed == focusId ? _self.focusId : focusId // ignore: cast_nullable_to_non_nullable
as UuidValue?,observableId: freezed == observableId ? _self.observableId : observableId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectProjectionGraphIdentityId: freezed == objectProjectionGraphIdentityId ? _self.objectProjectionGraphIdentityId : objectProjectionGraphIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphBranchId: freezed == objectInstanceGraphBranchId ? _self.objectInstanceGraphBranchId : objectInstanceGraphBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,transitionKey: null == transitionKey ? _self.transitionKey : transitionKey // ignore: cast_nullable_to_non_nullable
as String,sequence: null == sequence ? _self.sequence : sequence // ignore: cast_nullable_to_non_nullable
as int,projectionHash: freezed == projectionHash ? _self.projectionHash : projectionHash // ignore: cast_nullable_to_non_nullable
as String?,transitionKind: null == transitionKind ? _self.transitionKind : transitionKind // ignore: cast_nullable_to_non_nullable
as String,rationale: freezed == rationale ? _self.rationale : rationale // ignore: cast_nullable_to_non_nullable
as String?,sourceKind: freezed == sourceKind ? _self.sourceKind : sourceKind // ignore: cast_nullable_to_non_nullable
as String?,sourceRef: freezed == sourceRef ? _self.sourceRef : sourceRef // ignore: cast_nullable_to_non_nullable
as String?,metadataJson: null == metadataJson ? _self._metadataJson : metadataJson // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$AttentionTransitionValidationResult {

 bool get exists; bool get valid; List<String> get failureReasons; AttentionFocusTransitionPin? get transition;
/// Create a copy of AttentionTransitionValidationResult
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$AttentionTransitionValidationResultCopyWith<AttentionTransitionValidationResult> get copyWith => _$AttentionTransitionValidationResultCopyWithImpl<AttentionTransitionValidationResult>(this as AttentionTransitionValidationResult, _$identity);

  /// Serializes this AttentionTransitionValidationResult to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is AttentionTransitionValidationResult&&(identical(other.exists, exists) || other.exists == exists)&&(identical(other.valid, valid) || other.valid == valid)&&const DeepCollectionEquality().equals(other.failureReasons, failureReasons)&&(identical(other.transition, transition) || other.transition == transition));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,exists,valid,const DeepCollectionEquality().hash(failureReasons),transition);

@override
String toString() {
  return 'AttentionTransitionValidationResult(exists: $exists, valid: $valid, failureReasons: $failureReasons, transition: $transition)';
}


}

/// @nodoc
abstract mixin class $AttentionTransitionValidationResultCopyWith<$Res>  {
  factory $AttentionTransitionValidationResultCopyWith(AttentionTransitionValidationResult value, $Res Function(AttentionTransitionValidationResult) _then) = _$AttentionTransitionValidationResultCopyWithImpl;
@useResult
$Res call({
 bool exists, bool valid, List<String> failureReasons, AttentionFocusTransitionPin? transition
});


$AttentionFocusTransitionPinCopyWith<$Res>? get transition;

}
/// @nodoc
class _$AttentionTransitionValidationResultCopyWithImpl<$Res>
    implements $AttentionTransitionValidationResultCopyWith<$Res> {
  _$AttentionTransitionValidationResultCopyWithImpl(this._self, this._then);

  final AttentionTransitionValidationResult _self;
  final $Res Function(AttentionTransitionValidationResult) _then;

/// Create a copy of AttentionTransitionValidationResult
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? exists = null,Object? valid = null,Object? failureReasons = null,Object? transition = freezed,}) {
  return _then(_self.copyWith(
exists: null == exists ? _self.exists : exists // ignore: cast_nullable_to_non_nullable
as bool,valid: null == valid ? _self.valid : valid // ignore: cast_nullable_to_non_nullable
as bool,failureReasons: null == failureReasons ? _self.failureReasons : failureReasons // ignore: cast_nullable_to_non_nullable
as List<String>,transition: freezed == transition ? _self.transition : transition // ignore: cast_nullable_to_non_nullable
as AttentionFocusTransitionPin?,
  ));
}
/// Create a copy of AttentionTransitionValidationResult
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$AttentionFocusTransitionPinCopyWith<$Res>? get transition {
    if (_self.transition == null) {
    return null;
  }

  return $AttentionFocusTransitionPinCopyWith<$Res>(_self.transition!, (value) {
    return _then(_self.copyWith(transition: value));
  });
}
}


/// Adds pattern-matching-related methods to [AttentionTransitionValidationResult].
extension AttentionTransitionValidationResultPatterns on AttentionTransitionValidationResult {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _AttentionTransitionValidationResult value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _AttentionTransitionValidationResult() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _AttentionTransitionValidationResult value)  def,}){
final _that = this;
switch (_that) {
case _AttentionTransitionValidationResult():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _AttentionTransitionValidationResult value)?  def,}){
final _that = this;
switch (_that) {
case _AttentionTransitionValidationResult() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( bool exists,  bool valid,  List<String> failureReasons,  AttentionFocusTransitionPin? transition)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _AttentionTransitionValidationResult() when def != null:
return def(_that.exists,_that.valid,_that.failureReasons,_that.transition);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( bool exists,  bool valid,  List<String> failureReasons,  AttentionFocusTransitionPin? transition)  def,}) {final _that = this;
switch (_that) {
case _AttentionTransitionValidationResult():
return def(_that.exists,_that.valid,_that.failureReasons,_that.transition);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( bool exists,  bool valid,  List<String> failureReasons,  AttentionFocusTransitionPin? transition)?  def,}) {final _that = this;
switch (_that) {
case _AttentionTransitionValidationResult() when def != null:
return def(_that.exists,_that.valid,_that.failureReasons,_that.transition);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _AttentionTransitionValidationResult implements AttentionTransitionValidationResult {
   _AttentionTransitionValidationResult({required this.exists, required this.valid, final  List<String> failureReasons = const [], this.transition}): _failureReasons = failureReasons;
  factory _AttentionTransitionValidationResult.fromJson(Map<String, dynamic> json) => _$AttentionTransitionValidationResultFromJson(json);

@override final  bool exists;
@override final  bool valid;
 final  List<String> _failureReasons;
@override@JsonKey() List<String> get failureReasons {
  if (_failureReasons is EqualUnmodifiableListView) return _failureReasons;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_failureReasons);
}

@override final  AttentionFocusTransitionPin? transition;

/// Create a copy of AttentionTransitionValidationResult
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$AttentionTransitionValidationResultCopyWith<_AttentionTransitionValidationResult> get copyWith => __$AttentionTransitionValidationResultCopyWithImpl<_AttentionTransitionValidationResult>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$AttentionTransitionValidationResultToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _AttentionTransitionValidationResult&&(identical(other.exists, exists) || other.exists == exists)&&(identical(other.valid, valid) || other.valid == valid)&&const DeepCollectionEquality().equals(other._failureReasons, _failureReasons)&&(identical(other.transition, transition) || other.transition == transition));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,exists,valid,const DeepCollectionEquality().hash(_failureReasons),transition);

@override
String toString() {
  return 'AttentionTransitionValidationResult.def(exists: $exists, valid: $valid, failureReasons: $failureReasons, transition: $transition)';
}


}

/// @nodoc
abstract mixin class _$AttentionTransitionValidationResultCopyWith<$Res> implements $AttentionTransitionValidationResultCopyWith<$Res> {
  factory _$AttentionTransitionValidationResultCopyWith(_AttentionTransitionValidationResult value, $Res Function(_AttentionTransitionValidationResult) _then) = __$AttentionTransitionValidationResultCopyWithImpl;
@override @useResult
$Res call({
 bool exists, bool valid, List<String> failureReasons, AttentionFocusTransitionPin? transition
});


@override $AttentionFocusTransitionPinCopyWith<$Res>? get transition;

}
/// @nodoc
class __$AttentionTransitionValidationResultCopyWithImpl<$Res>
    implements _$AttentionTransitionValidationResultCopyWith<$Res> {
  __$AttentionTransitionValidationResultCopyWithImpl(this._self, this._then);

  final _AttentionTransitionValidationResult _self;
  final $Res Function(_AttentionTransitionValidationResult) _then;

/// Create a copy of AttentionTransitionValidationResult
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? exists = null,Object? valid = null,Object? failureReasons = null,Object? transition = freezed,}) {
  return _then(_AttentionTransitionValidationResult(
exists: null == exists ? _self.exists : exists // ignore: cast_nullable_to_non_nullable
as bool,valid: null == valid ? _self.valid : valid // ignore: cast_nullable_to_non_nullable
as bool,failureReasons: null == failureReasons ? _self._failureReasons : failureReasons // ignore: cast_nullable_to_non_nullable
as List<String>,transition: freezed == transition ? _self.transition : transition // ignore: cast_nullable_to_non_nullable
as AttentionFocusTransitionPin?,
  ));
}

/// Create a copy of AttentionTransitionValidationResult
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$AttentionFocusTransitionPinCopyWith<$Res>? get transition {
    if (_self.transition == null) {
    return null;
  }

  return $AttentionFocusTransitionPinCopyWith<$Res>(_self.transition!, (value) {
    return _then(_self.copyWith(transition: value));
  });
}
}

// dart format on
