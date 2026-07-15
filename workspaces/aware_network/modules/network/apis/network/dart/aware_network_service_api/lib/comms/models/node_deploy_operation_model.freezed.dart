// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'node_deploy_operation_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$NodeDeployTarget {

@UuidValueConverter() UuidValue? get targetId; String? get targetKey; String? get displayName; String? get nodeBaseUrl; String? get nodeWebsocketPath;
/// Create a copy of NodeDeployTarget
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NodeDeployTargetCopyWith<NodeDeployTarget> get copyWith => _$NodeDeployTargetCopyWithImpl<NodeDeployTarget>(this as NodeDeployTarget, _$identity);

  /// Serializes this NodeDeployTarget to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NodeDeployTarget&&(identical(other.targetId, targetId) || other.targetId == targetId)&&(identical(other.targetKey, targetKey) || other.targetKey == targetKey)&&(identical(other.displayName, displayName) || other.displayName == displayName)&&(identical(other.nodeBaseUrl, nodeBaseUrl) || other.nodeBaseUrl == nodeBaseUrl)&&(identical(other.nodeWebsocketPath, nodeWebsocketPath) || other.nodeWebsocketPath == nodeWebsocketPath));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,targetId,targetKey,displayName,nodeBaseUrl,nodeWebsocketPath);

@override
String toString() {
  return 'NodeDeployTarget(targetId: $targetId, targetKey: $targetKey, displayName: $displayName, nodeBaseUrl: $nodeBaseUrl, nodeWebsocketPath: $nodeWebsocketPath)';
}


}

/// @nodoc
abstract mixin class $NodeDeployTargetCopyWith<$Res>  {
  factory $NodeDeployTargetCopyWith(NodeDeployTarget value, $Res Function(NodeDeployTarget) _then) = _$NodeDeployTargetCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? targetId, String? targetKey, String? displayName, String? nodeBaseUrl, String? nodeWebsocketPath
});




}
/// @nodoc
class _$NodeDeployTargetCopyWithImpl<$Res>
    implements $NodeDeployTargetCopyWith<$Res> {
  _$NodeDeployTargetCopyWithImpl(this._self, this._then);

  final NodeDeployTarget _self;
  final $Res Function(NodeDeployTarget) _then;

/// Create a copy of NodeDeployTarget
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? targetId = freezed,Object? targetKey = freezed,Object? displayName = freezed,Object? nodeBaseUrl = freezed,Object? nodeWebsocketPath = freezed,}) {
  return _then(_self.copyWith(
targetId: freezed == targetId ? _self.targetId : targetId // ignore: cast_nullable_to_non_nullable
as UuidValue?,targetKey: freezed == targetKey ? _self.targetKey : targetKey // ignore: cast_nullable_to_non_nullable
as String?,displayName: freezed == displayName ? _self.displayName : displayName // ignore: cast_nullable_to_non_nullable
as String?,nodeBaseUrl: freezed == nodeBaseUrl ? _self.nodeBaseUrl : nodeBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,nodeWebsocketPath: freezed == nodeWebsocketPath ? _self.nodeWebsocketPath : nodeWebsocketPath // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [NodeDeployTarget].
extension NodeDeployTargetPatterns on NodeDeployTarget {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NodeDeployTarget value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NodeDeployTarget() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NodeDeployTarget value)  def,}){
final _that = this;
switch (_that) {
case _NodeDeployTarget():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NodeDeployTarget value)?  def,}){
final _that = this;
switch (_that) {
case _NodeDeployTarget() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? targetId,  String? targetKey,  String? displayName,  String? nodeBaseUrl,  String? nodeWebsocketPath)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NodeDeployTarget() when def != null:
return def(_that.targetId,_that.targetKey,_that.displayName,_that.nodeBaseUrl,_that.nodeWebsocketPath);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? targetId,  String? targetKey,  String? displayName,  String? nodeBaseUrl,  String? nodeWebsocketPath)  def,}) {final _that = this;
switch (_that) {
case _NodeDeployTarget():
return def(_that.targetId,_that.targetKey,_that.displayName,_that.nodeBaseUrl,_that.nodeWebsocketPath);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? targetId,  String? targetKey,  String? displayName,  String? nodeBaseUrl,  String? nodeWebsocketPath)?  def,}) {final _that = this;
switch (_that) {
case _NodeDeployTarget() when def != null:
return def(_that.targetId,_that.targetKey,_that.displayName,_that.nodeBaseUrl,_that.nodeWebsocketPath);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NodeDeployTarget implements NodeDeployTarget {
   _NodeDeployTarget({@UuidValueConverter() this.targetId, this.targetKey, this.displayName, this.nodeBaseUrl, this.nodeWebsocketPath});
  factory _NodeDeployTarget.fromJson(Map<String, dynamic> json) => _$NodeDeployTargetFromJson(json);

@override@UuidValueConverter() final  UuidValue? targetId;
@override final  String? targetKey;
@override final  String? displayName;
@override final  String? nodeBaseUrl;
@override final  String? nodeWebsocketPath;

/// Create a copy of NodeDeployTarget
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NodeDeployTargetCopyWith<_NodeDeployTarget> get copyWith => __$NodeDeployTargetCopyWithImpl<_NodeDeployTarget>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NodeDeployTargetToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NodeDeployTarget&&(identical(other.targetId, targetId) || other.targetId == targetId)&&(identical(other.targetKey, targetKey) || other.targetKey == targetKey)&&(identical(other.displayName, displayName) || other.displayName == displayName)&&(identical(other.nodeBaseUrl, nodeBaseUrl) || other.nodeBaseUrl == nodeBaseUrl)&&(identical(other.nodeWebsocketPath, nodeWebsocketPath) || other.nodeWebsocketPath == nodeWebsocketPath));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,targetId,targetKey,displayName,nodeBaseUrl,nodeWebsocketPath);

@override
String toString() {
  return 'NodeDeployTarget.def(targetId: $targetId, targetKey: $targetKey, displayName: $displayName, nodeBaseUrl: $nodeBaseUrl, nodeWebsocketPath: $nodeWebsocketPath)';
}


}

/// @nodoc
abstract mixin class _$NodeDeployTargetCopyWith<$Res> implements $NodeDeployTargetCopyWith<$Res> {
  factory _$NodeDeployTargetCopyWith(_NodeDeployTarget value, $Res Function(_NodeDeployTarget) _then) = __$NodeDeployTargetCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? targetId, String? targetKey, String? displayName, String? nodeBaseUrl, String? nodeWebsocketPath
});




}
/// @nodoc
class __$NodeDeployTargetCopyWithImpl<$Res>
    implements _$NodeDeployTargetCopyWith<$Res> {
  __$NodeDeployTargetCopyWithImpl(this._self, this._then);

  final _NodeDeployTarget _self;
  final $Res Function(_NodeDeployTarget) _then;

/// Create a copy of NodeDeployTarget
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? targetId = freezed,Object? targetKey = freezed,Object? displayName = freezed,Object? nodeBaseUrl = freezed,Object? nodeWebsocketPath = freezed,}) {
  return _then(_NodeDeployTarget(
targetId: freezed == targetId ? _self.targetId : targetId // ignore: cast_nullable_to_non_nullable
as UuidValue?,targetKey: freezed == targetKey ? _self.targetKey : targetKey // ignore: cast_nullable_to_non_nullable
as String?,displayName: freezed == displayName ? _self.displayName : displayName // ignore: cast_nullable_to_non_nullable
as String?,nodeBaseUrl: freezed == nodeBaseUrl ? _self.nodeBaseUrl : nodeBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,nodeWebsocketPath: freezed == nodeWebsocketPath ? _self.nodeWebsocketPath : nodeWebsocketPath // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$NodeDeployTargetStatus {

 String get targetId; String get displayName; String? get kind; String? get endpoint; String get phase; bool get isActive; bool get isHealthy; String? get summary; String? get error; List<String> get detailLines;
/// Create a copy of NodeDeployTargetStatus
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NodeDeployTargetStatusCopyWith<NodeDeployTargetStatus> get copyWith => _$NodeDeployTargetStatusCopyWithImpl<NodeDeployTargetStatus>(this as NodeDeployTargetStatus, _$identity);

  /// Serializes this NodeDeployTargetStatus to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NodeDeployTargetStatus&&(identical(other.targetId, targetId) || other.targetId == targetId)&&(identical(other.displayName, displayName) || other.displayName == displayName)&&(identical(other.kind, kind) || other.kind == kind)&&(identical(other.endpoint, endpoint) || other.endpoint == endpoint)&&(identical(other.phase, phase) || other.phase == phase)&&(identical(other.isActive, isActive) || other.isActive == isActive)&&(identical(other.isHealthy, isHealthy) || other.isHealthy == isHealthy)&&(identical(other.summary, summary) || other.summary == summary)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other.detailLines, detailLines));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,targetId,displayName,kind,endpoint,phase,isActive,isHealthy,summary,error,const DeepCollectionEquality().hash(detailLines));

@override
String toString() {
  return 'NodeDeployTargetStatus(targetId: $targetId, displayName: $displayName, kind: $kind, endpoint: $endpoint, phase: $phase, isActive: $isActive, isHealthy: $isHealthy, summary: $summary, error: $error, detailLines: $detailLines)';
}


}

/// @nodoc
abstract mixin class $NodeDeployTargetStatusCopyWith<$Res>  {
  factory $NodeDeployTargetStatusCopyWith(NodeDeployTargetStatus value, $Res Function(NodeDeployTargetStatus) _then) = _$NodeDeployTargetStatusCopyWithImpl;
@useResult
$Res call({
 String targetId, String displayName, String? kind, String? endpoint, String phase, bool isActive, bool isHealthy, String? summary, String? error, List<String> detailLines
});




}
/// @nodoc
class _$NodeDeployTargetStatusCopyWithImpl<$Res>
    implements $NodeDeployTargetStatusCopyWith<$Res> {
  _$NodeDeployTargetStatusCopyWithImpl(this._self, this._then);

  final NodeDeployTargetStatus _self;
  final $Res Function(NodeDeployTargetStatus) _then;

/// Create a copy of NodeDeployTargetStatus
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? targetId = null,Object? displayName = null,Object? kind = freezed,Object? endpoint = freezed,Object? phase = null,Object? isActive = null,Object? isHealthy = null,Object? summary = freezed,Object? error = freezed,Object? detailLines = null,}) {
  return _then(_self.copyWith(
targetId: null == targetId ? _self.targetId : targetId // ignore: cast_nullable_to_non_nullable
as String,displayName: null == displayName ? _self.displayName : displayName // ignore: cast_nullable_to_non_nullable
as String,kind: freezed == kind ? _self.kind : kind // ignore: cast_nullable_to_non_nullable
as String?,endpoint: freezed == endpoint ? _self.endpoint : endpoint // ignore: cast_nullable_to_non_nullable
as String?,phase: null == phase ? _self.phase : phase // ignore: cast_nullable_to_non_nullable
as String,isActive: null == isActive ? _self.isActive : isActive // ignore: cast_nullable_to_non_nullable
as bool,isHealthy: null == isHealthy ? _self.isHealthy : isHealthy // ignore: cast_nullable_to_non_nullable
as bool,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,detailLines: null == detailLines ? _self.detailLines : detailLines // ignore: cast_nullable_to_non_nullable
as List<String>,
  ));
}

}


/// Adds pattern-matching-related methods to [NodeDeployTargetStatus].
extension NodeDeployTargetStatusPatterns on NodeDeployTargetStatus {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NodeDeployTargetStatus value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NodeDeployTargetStatus() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NodeDeployTargetStatus value)  def,}){
final _that = this;
switch (_that) {
case _NodeDeployTargetStatus():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NodeDeployTargetStatus value)?  def,}){
final _that = this;
switch (_that) {
case _NodeDeployTargetStatus() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String targetId,  String displayName,  String? kind,  String? endpoint,  String phase,  bool isActive,  bool isHealthy,  String? summary,  String? error,  List<String> detailLines)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NodeDeployTargetStatus() when def != null:
return def(_that.targetId,_that.displayName,_that.kind,_that.endpoint,_that.phase,_that.isActive,_that.isHealthy,_that.summary,_that.error,_that.detailLines);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String targetId,  String displayName,  String? kind,  String? endpoint,  String phase,  bool isActive,  bool isHealthy,  String? summary,  String? error,  List<String> detailLines)  def,}) {final _that = this;
switch (_that) {
case _NodeDeployTargetStatus():
return def(_that.targetId,_that.displayName,_that.kind,_that.endpoint,_that.phase,_that.isActive,_that.isHealthy,_that.summary,_that.error,_that.detailLines);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String targetId,  String displayName,  String? kind,  String? endpoint,  String phase,  bool isActive,  bool isHealthy,  String? summary,  String? error,  List<String> detailLines)?  def,}) {final _that = this;
switch (_that) {
case _NodeDeployTargetStatus() when def != null:
return def(_that.targetId,_that.displayName,_that.kind,_that.endpoint,_that.phase,_that.isActive,_that.isHealthy,_that.summary,_that.error,_that.detailLines);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NodeDeployTargetStatus implements NodeDeployTargetStatus {
   _NodeDeployTargetStatus({required this.targetId, required this.displayName, this.kind, this.endpoint, required this.phase, required this.isActive, required this.isHealthy, this.summary, this.error, final  List<String> detailLines = const []}): _detailLines = detailLines;
  factory _NodeDeployTargetStatus.fromJson(Map<String, dynamic> json) => _$NodeDeployTargetStatusFromJson(json);

@override final  String targetId;
@override final  String displayName;
@override final  String? kind;
@override final  String? endpoint;
@override final  String phase;
@override final  bool isActive;
@override final  bool isHealthy;
@override final  String? summary;
@override final  String? error;
 final  List<String> _detailLines;
@override@JsonKey() List<String> get detailLines {
  if (_detailLines is EqualUnmodifiableListView) return _detailLines;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_detailLines);
}


/// Create a copy of NodeDeployTargetStatus
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NodeDeployTargetStatusCopyWith<_NodeDeployTargetStatus> get copyWith => __$NodeDeployTargetStatusCopyWithImpl<_NodeDeployTargetStatus>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NodeDeployTargetStatusToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NodeDeployTargetStatus&&(identical(other.targetId, targetId) || other.targetId == targetId)&&(identical(other.displayName, displayName) || other.displayName == displayName)&&(identical(other.kind, kind) || other.kind == kind)&&(identical(other.endpoint, endpoint) || other.endpoint == endpoint)&&(identical(other.phase, phase) || other.phase == phase)&&(identical(other.isActive, isActive) || other.isActive == isActive)&&(identical(other.isHealthy, isHealthy) || other.isHealthy == isHealthy)&&(identical(other.summary, summary) || other.summary == summary)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other._detailLines, _detailLines));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,targetId,displayName,kind,endpoint,phase,isActive,isHealthy,summary,error,const DeepCollectionEquality().hash(_detailLines));

@override
String toString() {
  return 'NodeDeployTargetStatus.def(targetId: $targetId, displayName: $displayName, kind: $kind, endpoint: $endpoint, phase: $phase, isActive: $isActive, isHealthy: $isHealthy, summary: $summary, error: $error, detailLines: $detailLines)';
}


}

/// @nodoc
abstract mixin class _$NodeDeployTargetStatusCopyWith<$Res> implements $NodeDeployTargetStatusCopyWith<$Res> {
  factory _$NodeDeployTargetStatusCopyWith(_NodeDeployTargetStatus value, $Res Function(_NodeDeployTargetStatus) _then) = __$NodeDeployTargetStatusCopyWithImpl;
@override @useResult
$Res call({
 String targetId, String displayName, String? kind, String? endpoint, String phase, bool isActive, bool isHealthy, String? summary, String? error, List<String> detailLines
});




}
/// @nodoc
class __$NodeDeployTargetStatusCopyWithImpl<$Res>
    implements _$NodeDeployTargetStatusCopyWith<$Res> {
  __$NodeDeployTargetStatusCopyWithImpl(this._self, this._then);

  final _NodeDeployTargetStatus _self;
  final $Res Function(_NodeDeployTargetStatus) _then;

/// Create a copy of NodeDeployTargetStatus
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? targetId = null,Object? displayName = null,Object? kind = freezed,Object? endpoint = freezed,Object? phase = null,Object? isActive = null,Object? isHealthy = null,Object? summary = freezed,Object? error = freezed,Object? detailLines = null,}) {
  return _then(_NodeDeployTargetStatus(
targetId: null == targetId ? _self.targetId : targetId // ignore: cast_nullable_to_non_nullable
as String,displayName: null == displayName ? _self.displayName : displayName // ignore: cast_nullable_to_non_nullable
as String,kind: freezed == kind ? _self.kind : kind // ignore: cast_nullable_to_non_nullable
as String?,endpoint: freezed == endpoint ? _self.endpoint : endpoint // ignore: cast_nullable_to_non_nullable
as String?,phase: null == phase ? _self.phase : phase // ignore: cast_nullable_to_non_nullable
as String,isActive: null == isActive ? _self.isActive : isActive // ignore: cast_nullable_to_non_nullable
as bool,isHealthy: null == isHealthy ? _self.isHealthy : isHealthy // ignore: cast_nullable_to_non_nullable
as bool,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,detailLines: null == detailLines ? _self._detailLines : detailLines // ignore: cast_nullable_to_non_nullable
as List<String>,
  ));
}


}


/// @nodoc
mixin _$NodeDeployRuntimeStatus {

 NodeDeployTarget? get target;@JsonKey(fromJson: NodeDeployRuntimePhaseExtension.fromJson, toJson: NodeDeployRuntimePhaseExtension.toJson) NodeDeployRuntimePhase get phase; String? get activeTargetId; String? get backendKind; bool get isActive; bool get isHealthy; String? get nodeBaseUrl; String? get nodeWebsocketPath; String? get summary; String? get error; String? get updatedAt; List<String> get recentLogLines; List<NodeDeployTargetStatus> get targetStatuses;
/// Create a copy of NodeDeployRuntimeStatus
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NodeDeployRuntimeStatusCopyWith<NodeDeployRuntimeStatus> get copyWith => _$NodeDeployRuntimeStatusCopyWithImpl<NodeDeployRuntimeStatus>(this as NodeDeployRuntimeStatus, _$identity);

  /// Serializes this NodeDeployRuntimeStatus to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NodeDeployRuntimeStatus&&(identical(other.target, target) || other.target == target)&&(identical(other.phase, phase) || other.phase == phase)&&(identical(other.activeTargetId, activeTargetId) || other.activeTargetId == activeTargetId)&&(identical(other.backendKind, backendKind) || other.backendKind == backendKind)&&(identical(other.isActive, isActive) || other.isActive == isActive)&&(identical(other.isHealthy, isHealthy) || other.isHealthy == isHealthy)&&(identical(other.nodeBaseUrl, nodeBaseUrl) || other.nodeBaseUrl == nodeBaseUrl)&&(identical(other.nodeWebsocketPath, nodeWebsocketPath) || other.nodeWebsocketPath == nodeWebsocketPath)&&(identical(other.summary, summary) || other.summary == summary)&&(identical(other.error, error) || other.error == error)&&(identical(other.updatedAt, updatedAt) || other.updatedAt == updatedAt)&&const DeepCollectionEquality().equals(other.recentLogLines, recentLogLines)&&const DeepCollectionEquality().equals(other.targetStatuses, targetStatuses));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,target,phase,activeTargetId,backendKind,isActive,isHealthy,nodeBaseUrl,nodeWebsocketPath,summary,error,updatedAt,const DeepCollectionEquality().hash(recentLogLines),const DeepCollectionEquality().hash(targetStatuses));

@override
String toString() {
  return 'NodeDeployRuntimeStatus(target: $target, phase: $phase, activeTargetId: $activeTargetId, backendKind: $backendKind, isActive: $isActive, isHealthy: $isHealthy, nodeBaseUrl: $nodeBaseUrl, nodeWebsocketPath: $nodeWebsocketPath, summary: $summary, error: $error, updatedAt: $updatedAt, recentLogLines: $recentLogLines, targetStatuses: $targetStatuses)';
}


}

/// @nodoc
abstract mixin class $NodeDeployRuntimeStatusCopyWith<$Res>  {
  factory $NodeDeployRuntimeStatusCopyWith(NodeDeployRuntimeStatus value, $Res Function(NodeDeployRuntimeStatus) _then) = _$NodeDeployRuntimeStatusCopyWithImpl;
@useResult
$Res call({
 NodeDeployTarget? target,@JsonKey(fromJson: NodeDeployRuntimePhaseExtension.fromJson, toJson: NodeDeployRuntimePhaseExtension.toJson) NodeDeployRuntimePhase phase, String? activeTargetId, String? backendKind, bool isActive, bool isHealthy, String? nodeBaseUrl, String? nodeWebsocketPath, String? summary, String? error, String? updatedAt, List<String> recentLogLines, List<NodeDeployTargetStatus> targetStatuses
});


$NodeDeployTargetCopyWith<$Res>? get target;

}
/// @nodoc
class _$NodeDeployRuntimeStatusCopyWithImpl<$Res>
    implements $NodeDeployRuntimeStatusCopyWith<$Res> {
  _$NodeDeployRuntimeStatusCopyWithImpl(this._self, this._then);

  final NodeDeployRuntimeStatus _self;
  final $Res Function(NodeDeployRuntimeStatus) _then;

/// Create a copy of NodeDeployRuntimeStatus
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? target = freezed,Object? phase = null,Object? activeTargetId = freezed,Object? backendKind = freezed,Object? isActive = null,Object? isHealthy = null,Object? nodeBaseUrl = freezed,Object? nodeWebsocketPath = freezed,Object? summary = freezed,Object? error = freezed,Object? updatedAt = freezed,Object? recentLogLines = null,Object? targetStatuses = null,}) {
  return _then(_self.copyWith(
target: freezed == target ? _self.target : target // ignore: cast_nullable_to_non_nullable
as NodeDeployTarget?,phase: null == phase ? _self.phase : phase // ignore: cast_nullable_to_non_nullable
as NodeDeployRuntimePhase,activeTargetId: freezed == activeTargetId ? _self.activeTargetId : activeTargetId // ignore: cast_nullable_to_non_nullable
as String?,backendKind: freezed == backendKind ? _self.backendKind : backendKind // ignore: cast_nullable_to_non_nullable
as String?,isActive: null == isActive ? _self.isActive : isActive // ignore: cast_nullable_to_non_nullable
as bool,isHealthy: null == isHealthy ? _self.isHealthy : isHealthy // ignore: cast_nullable_to_non_nullable
as bool,nodeBaseUrl: freezed == nodeBaseUrl ? _self.nodeBaseUrl : nodeBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,nodeWebsocketPath: freezed == nodeWebsocketPath ? _self.nodeWebsocketPath : nodeWebsocketPath // ignore: cast_nullable_to_non_nullable
as String?,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,updatedAt: freezed == updatedAt ? _self.updatedAt : updatedAt // ignore: cast_nullable_to_non_nullable
as String?,recentLogLines: null == recentLogLines ? _self.recentLogLines : recentLogLines // ignore: cast_nullable_to_non_nullable
as List<String>,targetStatuses: null == targetStatuses ? _self.targetStatuses : targetStatuses // ignore: cast_nullable_to_non_nullable
as List<NodeDeployTargetStatus>,
  ));
}
/// Create a copy of NodeDeployRuntimeStatus
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployTargetCopyWith<$Res>? get target {
    if (_self.target == null) {
    return null;
  }

  return $NodeDeployTargetCopyWith<$Res>(_self.target!, (value) {
    return _then(_self.copyWith(target: value));
  });
}
}


/// Adds pattern-matching-related methods to [NodeDeployRuntimeStatus].
extension NodeDeployRuntimeStatusPatterns on NodeDeployRuntimeStatus {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NodeDeployRuntimeStatus value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NodeDeployRuntimeStatus() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NodeDeployRuntimeStatus value)  def,}){
final _that = this;
switch (_that) {
case _NodeDeployRuntimeStatus():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NodeDeployRuntimeStatus value)?  def,}){
final _that = this;
switch (_that) {
case _NodeDeployRuntimeStatus() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( NodeDeployTarget? target, @JsonKey(fromJson: NodeDeployRuntimePhaseExtension.fromJson, toJson: NodeDeployRuntimePhaseExtension.toJson)  NodeDeployRuntimePhase phase,  String? activeTargetId,  String? backendKind,  bool isActive,  bool isHealthy,  String? nodeBaseUrl,  String? nodeWebsocketPath,  String? summary,  String? error,  String? updatedAt,  List<String> recentLogLines,  List<NodeDeployTargetStatus> targetStatuses)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NodeDeployRuntimeStatus() when def != null:
return def(_that.target,_that.phase,_that.activeTargetId,_that.backendKind,_that.isActive,_that.isHealthy,_that.nodeBaseUrl,_that.nodeWebsocketPath,_that.summary,_that.error,_that.updatedAt,_that.recentLogLines,_that.targetStatuses);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( NodeDeployTarget? target, @JsonKey(fromJson: NodeDeployRuntimePhaseExtension.fromJson, toJson: NodeDeployRuntimePhaseExtension.toJson)  NodeDeployRuntimePhase phase,  String? activeTargetId,  String? backendKind,  bool isActive,  bool isHealthy,  String? nodeBaseUrl,  String? nodeWebsocketPath,  String? summary,  String? error,  String? updatedAt,  List<String> recentLogLines,  List<NodeDeployTargetStatus> targetStatuses)  def,}) {final _that = this;
switch (_that) {
case _NodeDeployRuntimeStatus():
return def(_that.target,_that.phase,_that.activeTargetId,_that.backendKind,_that.isActive,_that.isHealthy,_that.nodeBaseUrl,_that.nodeWebsocketPath,_that.summary,_that.error,_that.updatedAt,_that.recentLogLines,_that.targetStatuses);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( NodeDeployTarget? target, @JsonKey(fromJson: NodeDeployRuntimePhaseExtension.fromJson, toJson: NodeDeployRuntimePhaseExtension.toJson)  NodeDeployRuntimePhase phase,  String? activeTargetId,  String? backendKind,  bool isActive,  bool isHealthy,  String? nodeBaseUrl,  String? nodeWebsocketPath,  String? summary,  String? error,  String? updatedAt,  List<String> recentLogLines,  List<NodeDeployTargetStatus> targetStatuses)?  def,}) {final _that = this;
switch (_that) {
case _NodeDeployRuntimeStatus() when def != null:
return def(_that.target,_that.phase,_that.activeTargetId,_that.backendKind,_that.isActive,_that.isHealthy,_that.nodeBaseUrl,_that.nodeWebsocketPath,_that.summary,_that.error,_that.updatedAt,_that.recentLogLines,_that.targetStatuses);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NodeDeployRuntimeStatus implements NodeDeployRuntimeStatus {
   _NodeDeployRuntimeStatus({this.target, @JsonKey(fromJson: NodeDeployRuntimePhaseExtension.fromJson, toJson: NodeDeployRuntimePhaseExtension.toJson) required this.phase, this.activeTargetId, this.backendKind, required this.isActive, required this.isHealthy, this.nodeBaseUrl, this.nodeWebsocketPath, this.summary, this.error, this.updatedAt, final  List<String> recentLogLines = const [], final  List<NodeDeployTargetStatus> targetStatuses = const []}): _recentLogLines = recentLogLines,_targetStatuses = targetStatuses;
  factory _NodeDeployRuntimeStatus.fromJson(Map<String, dynamic> json) => _$NodeDeployRuntimeStatusFromJson(json);

@override final  NodeDeployTarget? target;
@override@JsonKey(fromJson: NodeDeployRuntimePhaseExtension.fromJson, toJson: NodeDeployRuntimePhaseExtension.toJson) final  NodeDeployRuntimePhase phase;
@override final  String? activeTargetId;
@override final  String? backendKind;
@override final  bool isActive;
@override final  bool isHealthy;
@override final  String? nodeBaseUrl;
@override final  String? nodeWebsocketPath;
@override final  String? summary;
@override final  String? error;
@override final  String? updatedAt;
 final  List<String> _recentLogLines;
@override@JsonKey() List<String> get recentLogLines {
  if (_recentLogLines is EqualUnmodifiableListView) return _recentLogLines;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_recentLogLines);
}

 final  List<NodeDeployTargetStatus> _targetStatuses;
@override@JsonKey() List<NodeDeployTargetStatus> get targetStatuses {
  if (_targetStatuses is EqualUnmodifiableListView) return _targetStatuses;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_targetStatuses);
}


/// Create a copy of NodeDeployRuntimeStatus
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NodeDeployRuntimeStatusCopyWith<_NodeDeployRuntimeStatus> get copyWith => __$NodeDeployRuntimeStatusCopyWithImpl<_NodeDeployRuntimeStatus>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NodeDeployRuntimeStatusToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NodeDeployRuntimeStatus&&(identical(other.target, target) || other.target == target)&&(identical(other.phase, phase) || other.phase == phase)&&(identical(other.activeTargetId, activeTargetId) || other.activeTargetId == activeTargetId)&&(identical(other.backendKind, backendKind) || other.backendKind == backendKind)&&(identical(other.isActive, isActive) || other.isActive == isActive)&&(identical(other.isHealthy, isHealthy) || other.isHealthy == isHealthy)&&(identical(other.nodeBaseUrl, nodeBaseUrl) || other.nodeBaseUrl == nodeBaseUrl)&&(identical(other.nodeWebsocketPath, nodeWebsocketPath) || other.nodeWebsocketPath == nodeWebsocketPath)&&(identical(other.summary, summary) || other.summary == summary)&&(identical(other.error, error) || other.error == error)&&(identical(other.updatedAt, updatedAt) || other.updatedAt == updatedAt)&&const DeepCollectionEquality().equals(other._recentLogLines, _recentLogLines)&&const DeepCollectionEquality().equals(other._targetStatuses, _targetStatuses));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,target,phase,activeTargetId,backendKind,isActive,isHealthy,nodeBaseUrl,nodeWebsocketPath,summary,error,updatedAt,const DeepCollectionEquality().hash(_recentLogLines),const DeepCollectionEquality().hash(_targetStatuses));

@override
String toString() {
  return 'NodeDeployRuntimeStatus.def(target: $target, phase: $phase, activeTargetId: $activeTargetId, backendKind: $backendKind, isActive: $isActive, isHealthy: $isHealthy, nodeBaseUrl: $nodeBaseUrl, nodeWebsocketPath: $nodeWebsocketPath, summary: $summary, error: $error, updatedAt: $updatedAt, recentLogLines: $recentLogLines, targetStatuses: $targetStatuses)';
}


}

/// @nodoc
abstract mixin class _$NodeDeployRuntimeStatusCopyWith<$Res> implements $NodeDeployRuntimeStatusCopyWith<$Res> {
  factory _$NodeDeployRuntimeStatusCopyWith(_NodeDeployRuntimeStatus value, $Res Function(_NodeDeployRuntimeStatus) _then) = __$NodeDeployRuntimeStatusCopyWithImpl;
@override @useResult
$Res call({
 NodeDeployTarget? target,@JsonKey(fromJson: NodeDeployRuntimePhaseExtension.fromJson, toJson: NodeDeployRuntimePhaseExtension.toJson) NodeDeployRuntimePhase phase, String? activeTargetId, String? backendKind, bool isActive, bool isHealthy, String? nodeBaseUrl, String? nodeWebsocketPath, String? summary, String? error, String? updatedAt, List<String> recentLogLines, List<NodeDeployTargetStatus> targetStatuses
});


@override $NodeDeployTargetCopyWith<$Res>? get target;

}
/// @nodoc
class __$NodeDeployRuntimeStatusCopyWithImpl<$Res>
    implements _$NodeDeployRuntimeStatusCopyWith<$Res> {
  __$NodeDeployRuntimeStatusCopyWithImpl(this._self, this._then);

  final _NodeDeployRuntimeStatus _self;
  final $Res Function(_NodeDeployRuntimeStatus) _then;

/// Create a copy of NodeDeployRuntimeStatus
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? target = freezed,Object? phase = null,Object? activeTargetId = freezed,Object? backendKind = freezed,Object? isActive = null,Object? isHealthy = null,Object? nodeBaseUrl = freezed,Object? nodeWebsocketPath = freezed,Object? summary = freezed,Object? error = freezed,Object? updatedAt = freezed,Object? recentLogLines = null,Object? targetStatuses = null,}) {
  return _then(_NodeDeployRuntimeStatus(
target: freezed == target ? _self.target : target // ignore: cast_nullable_to_non_nullable
as NodeDeployTarget?,phase: null == phase ? _self.phase : phase // ignore: cast_nullable_to_non_nullable
as NodeDeployRuntimePhase,activeTargetId: freezed == activeTargetId ? _self.activeTargetId : activeTargetId // ignore: cast_nullable_to_non_nullable
as String?,backendKind: freezed == backendKind ? _self.backendKind : backendKind // ignore: cast_nullable_to_non_nullable
as String?,isActive: null == isActive ? _self.isActive : isActive // ignore: cast_nullable_to_non_nullable
as bool,isHealthy: null == isHealthy ? _self.isHealthy : isHealthy // ignore: cast_nullable_to_non_nullable
as bool,nodeBaseUrl: freezed == nodeBaseUrl ? _self.nodeBaseUrl : nodeBaseUrl // ignore: cast_nullable_to_non_nullable
as String?,nodeWebsocketPath: freezed == nodeWebsocketPath ? _self.nodeWebsocketPath : nodeWebsocketPath // ignore: cast_nullable_to_non_nullable
as String?,summary: freezed == summary ? _self.summary : summary // ignore: cast_nullable_to_non_nullable
as String?,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,updatedAt: freezed == updatedAt ? _self.updatedAt : updatedAt // ignore: cast_nullable_to_non_nullable
as String?,recentLogLines: null == recentLogLines ? _self._recentLogLines : recentLogLines // ignore: cast_nullable_to_non_nullable
as List<String>,targetStatuses: null == targetStatuses ? _self._targetStatuses : targetStatuses // ignore: cast_nullable_to_non_nullable
as List<NodeDeployTargetStatus>,
  ));
}

/// Create a copy of NodeDeployRuntimeStatus
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployTargetCopyWith<$Res>? get target {
    if (_self.target == null) {
    return null;
  }

  return $NodeDeployTargetCopyWith<$Res>(_self.target!, (value) {
    return _then(_self.copyWith(target: value));
  });
}
}


/// @nodoc
mixin _$NodeDeployOperationContext {

@UuidValueConverter() UuidValue? get actorId;
/// Create a copy of NodeDeployOperationContext
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NodeDeployOperationContextCopyWith<NodeDeployOperationContext> get copyWith => _$NodeDeployOperationContextCopyWithImpl<NodeDeployOperationContext>(this as NodeDeployOperationContext, _$identity);

  /// Serializes this NodeDeployOperationContext to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NodeDeployOperationContext&&(identical(other.actorId, actorId) || other.actorId == actorId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId);

@override
String toString() {
  return 'NodeDeployOperationContext(actorId: $actorId)';
}


}

/// @nodoc
abstract mixin class $NodeDeployOperationContextCopyWith<$Res>  {
  factory $NodeDeployOperationContextCopyWith(NodeDeployOperationContext value, $Res Function(NodeDeployOperationContext) _then) = _$NodeDeployOperationContextCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId
});




}
/// @nodoc
class _$NodeDeployOperationContextCopyWithImpl<$Res>
    implements $NodeDeployOperationContextCopyWith<$Res> {
  _$NodeDeployOperationContextCopyWithImpl(this._self, this._then);

  final NodeDeployOperationContext _self;
  final $Res Function(NodeDeployOperationContext) _then;

/// Create a copy of NodeDeployOperationContext
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

}


/// Adds pattern-matching-related methods to [NodeDeployOperationContext].
extension NodeDeployOperationContextPatterns on NodeDeployOperationContext {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NodeDeployOperationContext value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NodeDeployOperationContext() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NodeDeployOperationContext value)  def,}){
final _that = this;
switch (_that) {
case _NodeDeployOperationContext():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NodeDeployOperationContext value)?  def,}){
final _that = this;
switch (_that) {
case _NodeDeployOperationContext() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NodeDeployOperationContext() when def != null:
return def(_that.actorId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId)  def,}) {final _that = this;
switch (_that) {
case _NodeDeployOperationContext():
return def(_that.actorId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId)?  def,}) {final _that = this;
switch (_that) {
case _NodeDeployOperationContext() when def != null:
return def(_that.actorId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NodeDeployOperationContext implements NodeDeployOperationContext {
   _NodeDeployOperationContext({@UuidValueConverter() this.actorId});
  factory _NodeDeployOperationContext.fromJson(Map<String, dynamic> json) => _$NodeDeployOperationContextFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;

/// Create a copy of NodeDeployOperationContext
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NodeDeployOperationContextCopyWith<_NodeDeployOperationContext> get copyWith => __$NodeDeployOperationContextCopyWithImpl<_NodeDeployOperationContext>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NodeDeployOperationContextToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NodeDeployOperationContext&&(identical(other.actorId, actorId) || other.actorId == actorId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId);

@override
String toString() {
  return 'NodeDeployOperationContext.def(actorId: $actorId)';
}


}

/// @nodoc
abstract mixin class _$NodeDeployOperationContextCopyWith<$Res> implements $NodeDeployOperationContextCopyWith<$Res> {
  factory _$NodeDeployOperationContextCopyWith(_NodeDeployOperationContext value, $Res Function(_NodeDeployOperationContext) _then) = __$NodeDeployOperationContextCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId
});




}
/// @nodoc
class __$NodeDeployOperationContextCopyWithImpl<$Res>
    implements _$NodeDeployOperationContextCopyWith<$Res> {
  __$NodeDeployOperationContextCopyWithImpl(this._self, this._then);

  final _NodeDeployOperationContext _self;
  final $Res Function(_NodeDeployOperationContext) _then;

/// Create a copy of NodeDeployOperationContext
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,}) {
  return _then(_NodeDeployOperationContext(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}


}


/// @nodoc
mixin _$NodeDeployOperation {

 NodeDeployOperationRequest? get request; NodeDeployOperationResponse? get response; NodeDeployOperationEvent? get streamItem;
/// Create a copy of NodeDeployOperation
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NodeDeployOperationCopyWith<NodeDeployOperation> get copyWith => _$NodeDeployOperationCopyWithImpl<NodeDeployOperation>(this as NodeDeployOperation, _$identity);

  /// Serializes this NodeDeployOperation to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NodeDeployOperation&&(identical(other.request, request) || other.request == request)&&(identical(other.response, response) || other.response == response)&&(identical(other.streamItem, streamItem) || other.streamItem == streamItem));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,request,response,streamItem);

@override
String toString() {
  return 'NodeDeployOperation(request: $request, response: $response, streamItem: $streamItem)';
}


}

/// @nodoc
abstract mixin class $NodeDeployOperationCopyWith<$Res>  {
  factory $NodeDeployOperationCopyWith(NodeDeployOperation value, $Res Function(NodeDeployOperation) _then) = _$NodeDeployOperationCopyWithImpl;
@useResult
$Res call({
 NodeDeployOperationRequest? request, NodeDeployOperationResponse? response, NodeDeployOperationEvent? streamItem
});


$NodeDeployOperationRequestCopyWith<$Res>? get request;$NodeDeployOperationResponseCopyWith<$Res>? get response;$NodeDeployOperationEventCopyWith<$Res>? get streamItem;

}
/// @nodoc
class _$NodeDeployOperationCopyWithImpl<$Res>
    implements $NodeDeployOperationCopyWith<$Res> {
  _$NodeDeployOperationCopyWithImpl(this._self, this._then);

  final NodeDeployOperation _self;
  final $Res Function(NodeDeployOperation) _then;

/// Create a copy of NodeDeployOperation
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? request = freezed,Object? response = freezed,Object? streamItem = freezed,}) {
  return _then(_self.copyWith(
request: freezed == request ? _self.request : request // ignore: cast_nullable_to_non_nullable
as NodeDeployOperationRequest?,response: freezed == response ? _self.response : response // ignore: cast_nullable_to_non_nullable
as NodeDeployOperationResponse?,streamItem: freezed == streamItem ? _self.streamItem : streamItem // ignore: cast_nullable_to_non_nullable
as NodeDeployOperationEvent?,
  ));
}
/// Create a copy of NodeDeployOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployOperationRequestCopyWith<$Res>? get request {
    if (_self.request == null) {
    return null;
  }

  return $NodeDeployOperationRequestCopyWith<$Res>(_self.request!, (value) {
    return _then(_self.copyWith(request: value));
  });
}/// Create a copy of NodeDeployOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployOperationResponseCopyWith<$Res>? get response {
    if (_self.response == null) {
    return null;
  }

  return $NodeDeployOperationResponseCopyWith<$Res>(_self.response!, (value) {
    return _then(_self.copyWith(response: value));
  });
}/// Create a copy of NodeDeployOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployOperationEventCopyWith<$Res>? get streamItem {
    if (_self.streamItem == null) {
    return null;
  }

  return $NodeDeployOperationEventCopyWith<$Res>(_self.streamItem!, (value) {
    return _then(_self.copyWith(streamItem: value));
  });
}
}


/// Adds pattern-matching-related methods to [NodeDeployOperation].
extension NodeDeployOperationPatterns on NodeDeployOperation {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _NodeDeployOperation value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _NodeDeployOperation() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _NodeDeployOperation value)  def,}){
final _that = this;
switch (_that) {
case _NodeDeployOperation():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _NodeDeployOperation value)?  def,}){
final _that = this;
switch (_that) {
case _NodeDeployOperation() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( NodeDeployOperationRequest? request,  NodeDeployOperationResponse? response,  NodeDeployOperationEvent? streamItem)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _NodeDeployOperation() when def != null:
return def(_that.request,_that.response,_that.streamItem);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( NodeDeployOperationRequest? request,  NodeDeployOperationResponse? response,  NodeDeployOperationEvent? streamItem)  def,}) {final _that = this;
switch (_that) {
case _NodeDeployOperation():
return def(_that.request,_that.response,_that.streamItem);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( NodeDeployOperationRequest? request,  NodeDeployOperationResponse? response,  NodeDeployOperationEvent? streamItem)?  def,}) {final _that = this;
switch (_that) {
case _NodeDeployOperation() when def != null:
return def(_that.request,_that.response,_that.streamItem);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _NodeDeployOperation implements NodeDeployOperation {
   _NodeDeployOperation({this.request, this.response, this.streamItem});
  factory _NodeDeployOperation.fromJson(Map<String, dynamic> json) => _$NodeDeployOperationFromJson(json);

@override final  NodeDeployOperationRequest? request;
@override final  NodeDeployOperationResponse? response;
@override final  NodeDeployOperationEvent? streamItem;

/// Create a copy of NodeDeployOperation
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$NodeDeployOperationCopyWith<_NodeDeployOperation> get copyWith => __$NodeDeployOperationCopyWithImpl<_NodeDeployOperation>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NodeDeployOperationToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _NodeDeployOperation&&(identical(other.request, request) || other.request == request)&&(identical(other.response, response) || other.response == response)&&(identical(other.streamItem, streamItem) || other.streamItem == streamItem));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,request,response,streamItem);

@override
String toString() {
  return 'NodeDeployOperation.def(request: $request, response: $response, streamItem: $streamItem)';
}


}

/// @nodoc
abstract mixin class _$NodeDeployOperationCopyWith<$Res> implements $NodeDeployOperationCopyWith<$Res> {
  factory _$NodeDeployOperationCopyWith(_NodeDeployOperation value, $Res Function(_NodeDeployOperation) _then) = __$NodeDeployOperationCopyWithImpl;
@override @useResult
$Res call({
 NodeDeployOperationRequest? request, NodeDeployOperationResponse? response, NodeDeployOperationEvent? streamItem
});


@override $NodeDeployOperationRequestCopyWith<$Res>? get request;@override $NodeDeployOperationResponseCopyWith<$Res>? get response;@override $NodeDeployOperationEventCopyWith<$Res>? get streamItem;

}
/// @nodoc
class __$NodeDeployOperationCopyWithImpl<$Res>
    implements _$NodeDeployOperationCopyWith<$Res> {
  __$NodeDeployOperationCopyWithImpl(this._self, this._then);

  final _NodeDeployOperation _self;
  final $Res Function(_NodeDeployOperation) _then;

/// Create a copy of NodeDeployOperation
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? request = freezed,Object? response = freezed,Object? streamItem = freezed,}) {
  return _then(_NodeDeployOperation(
request: freezed == request ? _self.request : request // ignore: cast_nullable_to_non_nullable
as NodeDeployOperationRequest?,response: freezed == response ? _self.response : response // ignore: cast_nullable_to_non_nullable
as NodeDeployOperationResponse?,streamItem: freezed == streamItem ? _self.streamItem : streamItem // ignore: cast_nullable_to_non_nullable
as NodeDeployOperationEvent?,
  ));
}

/// Create a copy of NodeDeployOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployOperationRequestCopyWith<$Res>? get request {
    if (_self.request == null) {
    return null;
  }

  return $NodeDeployOperationRequestCopyWith<$Res>(_self.request!, (value) {
    return _then(_self.copyWith(request: value));
  });
}/// Create a copy of NodeDeployOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployOperationResponseCopyWith<$Res>? get response {
    if (_self.response == null) {
    return null;
  }

  return $NodeDeployOperationResponseCopyWith<$Res>(_self.response!, (value) {
    return _then(_self.copyWith(response: value));
  });
}/// Create a copy of NodeDeployOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployOperationEventCopyWith<$Res>? get streamItem {
    if (_self.streamItem == null) {
    return null;
  }

  return $NodeDeployOperationEventCopyWith<$Res>(_self.streamItem!, (value) {
    return _then(_self.copyWith(streamItem: value));
  });
}
}

NodeDeployOperationRequest _$NodeDeployOperationRequestFromJson(
  Map<String, dynamic> json
) {
        switch (json['operation']) {
                  case 'describe_node_runtime':
          return DescribeNodeRuntimeRequest.fromJson(
            json
          );
                case 'ensure_node_runtime_started':
          return EnsureNodeRuntimeStartedRequest.fromJson(
            json
          );
                case 'restart_node_runtime':
          return RestartNodeRuntimeRequest.fromJson(
            json
          );
                case 'stop_node_runtime':
          return StopNodeRuntimeRequest.fromJson(
            json
          );
                case 'tail_node_runtime_logs':
          return TailNodeRuntimeLogsRequest.fromJson(
            json
          );
                case 'stream_node_runtime_events':
          return StreamNodeRuntimeEventsRequest.fromJson(
            json
          );
        
          default:
            throw CheckedFromJsonException(
  json,
  'operation',
  'NodeDeployOperationRequest',
  'Invalid union type "${json['operation']}"!'
);
        }
      
}

/// @nodoc
mixin _$NodeDeployOperationRequest {

@UuidValueConverter() UuidValue? get actorId; NodeDeployTarget? get target;
/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NodeDeployOperationRequestCopyWith<NodeDeployOperationRequest> get copyWith => _$NodeDeployOperationRequestCopyWithImpl<NodeDeployOperationRequest>(this as NodeDeployOperationRequest, _$identity);

  /// Serializes this NodeDeployOperationRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NodeDeployOperationRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.target, target) || other.target == target));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,target);

@override
String toString() {
  return 'NodeDeployOperationRequest(actorId: $actorId, target: $target)';
}


}

/// @nodoc
abstract mixin class $NodeDeployOperationRequestCopyWith<$Res>  {
  factory $NodeDeployOperationRequestCopyWith(NodeDeployOperationRequest value, $Res Function(NodeDeployOperationRequest) _then) = _$NodeDeployOperationRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, NodeDeployTarget? target
});


$NodeDeployTargetCopyWith<$Res>? get target;

}
/// @nodoc
class _$NodeDeployOperationRequestCopyWithImpl<$Res>
    implements $NodeDeployOperationRequestCopyWith<$Res> {
  _$NodeDeployOperationRequestCopyWithImpl(this._self, this._then);

  final NodeDeployOperationRequest _self;
  final $Res Function(NodeDeployOperationRequest) _then;

/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? target = freezed,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,target: freezed == target ? _self.target : target // ignore: cast_nullable_to_non_nullable
as NodeDeployTarget?,
  ));
}
/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployTargetCopyWith<$Res>? get target {
    if (_self.target == null) {
    return null;
  }

  return $NodeDeployTargetCopyWith<$Res>(_self.target!, (value) {
    return _then(_self.copyWith(target: value));
  });
}
}


/// Adds pattern-matching-related methods to [NodeDeployOperationRequest].
extension NodeDeployOperationRequestPatterns on NodeDeployOperationRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( DescribeNodeRuntimeRequest value)?  describeNodeRuntime,TResult Function( EnsureNodeRuntimeStartedRequest value)?  ensureNodeRuntimeStarted,TResult Function( RestartNodeRuntimeRequest value)?  restartNodeRuntime,TResult Function( StopNodeRuntimeRequest value)?  stopNodeRuntime,TResult Function( TailNodeRuntimeLogsRequest value)?  tailNodeRuntimeLogs,TResult Function( StreamNodeRuntimeEventsRequest value)?  streamNodeRuntimeEvents,required TResult orElse(),}){
final _that = this;
switch (_that) {
case DescribeNodeRuntimeRequest() when describeNodeRuntime != null:
return describeNodeRuntime(_that);case EnsureNodeRuntimeStartedRequest() when ensureNodeRuntimeStarted != null:
return ensureNodeRuntimeStarted(_that);case RestartNodeRuntimeRequest() when restartNodeRuntime != null:
return restartNodeRuntime(_that);case StopNodeRuntimeRequest() when stopNodeRuntime != null:
return stopNodeRuntime(_that);case TailNodeRuntimeLogsRequest() when tailNodeRuntimeLogs != null:
return tailNodeRuntimeLogs(_that);case StreamNodeRuntimeEventsRequest() when streamNodeRuntimeEvents != null:
return streamNodeRuntimeEvents(_that);case _:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( DescribeNodeRuntimeRequest value)  describeNodeRuntime,required TResult Function( EnsureNodeRuntimeStartedRequest value)  ensureNodeRuntimeStarted,required TResult Function( RestartNodeRuntimeRequest value)  restartNodeRuntime,required TResult Function( StopNodeRuntimeRequest value)  stopNodeRuntime,required TResult Function( TailNodeRuntimeLogsRequest value)  tailNodeRuntimeLogs,required TResult Function( StreamNodeRuntimeEventsRequest value)  streamNodeRuntimeEvents,}){
final _that = this;
switch (_that) {
case DescribeNodeRuntimeRequest():
return describeNodeRuntime(_that);case EnsureNodeRuntimeStartedRequest():
return ensureNodeRuntimeStarted(_that);case RestartNodeRuntimeRequest():
return restartNodeRuntime(_that);case StopNodeRuntimeRequest():
return stopNodeRuntime(_that);case TailNodeRuntimeLogsRequest():
return tailNodeRuntimeLogs(_that);case StreamNodeRuntimeEventsRequest():
return streamNodeRuntimeEvents(_that);case _:
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( DescribeNodeRuntimeRequest value)?  describeNodeRuntime,TResult? Function( EnsureNodeRuntimeStartedRequest value)?  ensureNodeRuntimeStarted,TResult? Function( RestartNodeRuntimeRequest value)?  restartNodeRuntime,TResult? Function( StopNodeRuntimeRequest value)?  stopNodeRuntime,TResult? Function( TailNodeRuntimeLogsRequest value)?  tailNodeRuntimeLogs,TResult? Function( StreamNodeRuntimeEventsRequest value)?  streamNodeRuntimeEvents,}){
final _that = this;
switch (_that) {
case DescribeNodeRuntimeRequest() when describeNodeRuntime != null:
return describeNodeRuntime(_that);case EnsureNodeRuntimeStartedRequest() when ensureNodeRuntimeStarted != null:
return ensureNodeRuntimeStarted(_that);case RestartNodeRuntimeRequest() when restartNodeRuntime != null:
return restartNodeRuntime(_that);case StopNodeRuntimeRequest() when stopNodeRuntime != null:
return stopNodeRuntime(_that);case TailNodeRuntimeLogsRequest() when tailNodeRuntimeLogs != null:
return tailNodeRuntimeLogs(_that);case StreamNodeRuntimeEventsRequest() when streamNodeRuntimeEvents != null:
return streamNodeRuntimeEvents(_that);case _:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId,  NodeDeployTarget? target)?  describeNodeRuntime,TResult Function(@UuidValueConverter()  UuidValue? actorId,  NodeDeployTarget? target,  bool waitForReady)?  ensureNodeRuntimeStarted,TResult Function(@UuidValueConverter()  UuidValue? actorId,  NodeDeployTarget? target,  bool waitForReady)?  restartNodeRuntime,TResult Function(@UuidValueConverter()  UuidValue? actorId,  NodeDeployTarget? target,  bool force)?  stopNodeRuntime,TResult Function(@UuidValueConverter()  UuidValue? actorId,  NodeDeployTarget? target,  int lineCount)?  tailNodeRuntimeLogs,TResult Function(@UuidValueConverter()  UuidValue? actorId,  NodeDeployTarget? target,  bool includeHistory)?  streamNodeRuntimeEvents,required TResult orElse(),}) {final _that = this;
switch (_that) {
case DescribeNodeRuntimeRequest() when describeNodeRuntime != null:
return describeNodeRuntime(_that.actorId,_that.target);case EnsureNodeRuntimeStartedRequest() when ensureNodeRuntimeStarted != null:
return ensureNodeRuntimeStarted(_that.actorId,_that.target,_that.waitForReady);case RestartNodeRuntimeRequest() when restartNodeRuntime != null:
return restartNodeRuntime(_that.actorId,_that.target,_that.waitForReady);case StopNodeRuntimeRequest() when stopNodeRuntime != null:
return stopNodeRuntime(_that.actorId,_that.target,_that.force);case TailNodeRuntimeLogsRequest() when tailNodeRuntimeLogs != null:
return tailNodeRuntimeLogs(_that.actorId,_that.target,_that.lineCount);case StreamNodeRuntimeEventsRequest() when streamNodeRuntimeEvents != null:
return streamNodeRuntimeEvents(_that.actorId,_that.target,_that.includeHistory);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId,  NodeDeployTarget? target)  describeNodeRuntime,required TResult Function(@UuidValueConverter()  UuidValue? actorId,  NodeDeployTarget? target,  bool waitForReady)  ensureNodeRuntimeStarted,required TResult Function(@UuidValueConverter()  UuidValue? actorId,  NodeDeployTarget? target,  bool waitForReady)  restartNodeRuntime,required TResult Function(@UuidValueConverter()  UuidValue? actorId,  NodeDeployTarget? target,  bool force)  stopNodeRuntime,required TResult Function(@UuidValueConverter()  UuidValue? actorId,  NodeDeployTarget? target,  int lineCount)  tailNodeRuntimeLogs,required TResult Function(@UuidValueConverter()  UuidValue? actorId,  NodeDeployTarget? target,  bool includeHistory)  streamNodeRuntimeEvents,}) {final _that = this;
switch (_that) {
case DescribeNodeRuntimeRequest():
return describeNodeRuntime(_that.actorId,_that.target);case EnsureNodeRuntimeStartedRequest():
return ensureNodeRuntimeStarted(_that.actorId,_that.target,_that.waitForReady);case RestartNodeRuntimeRequest():
return restartNodeRuntime(_that.actorId,_that.target,_that.waitForReady);case StopNodeRuntimeRequest():
return stopNodeRuntime(_that.actorId,_that.target,_that.force);case TailNodeRuntimeLogsRequest():
return tailNodeRuntimeLogs(_that.actorId,_that.target,_that.lineCount);case StreamNodeRuntimeEventsRequest():
return streamNodeRuntimeEvents(_that.actorId,_that.target,_that.includeHistory);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId,  NodeDeployTarget? target)?  describeNodeRuntime,TResult? Function(@UuidValueConverter()  UuidValue? actorId,  NodeDeployTarget? target,  bool waitForReady)?  ensureNodeRuntimeStarted,TResult? Function(@UuidValueConverter()  UuidValue? actorId,  NodeDeployTarget? target,  bool waitForReady)?  restartNodeRuntime,TResult? Function(@UuidValueConverter()  UuidValue? actorId,  NodeDeployTarget? target,  bool force)?  stopNodeRuntime,TResult? Function(@UuidValueConverter()  UuidValue? actorId,  NodeDeployTarget? target,  int lineCount)?  tailNodeRuntimeLogs,TResult? Function(@UuidValueConverter()  UuidValue? actorId,  NodeDeployTarget? target,  bool includeHistory)?  streamNodeRuntimeEvents,}) {final _that = this;
switch (_that) {
case DescribeNodeRuntimeRequest() when describeNodeRuntime != null:
return describeNodeRuntime(_that.actorId,_that.target);case EnsureNodeRuntimeStartedRequest() when ensureNodeRuntimeStarted != null:
return ensureNodeRuntimeStarted(_that.actorId,_that.target,_that.waitForReady);case RestartNodeRuntimeRequest() when restartNodeRuntime != null:
return restartNodeRuntime(_that.actorId,_that.target,_that.waitForReady);case StopNodeRuntimeRequest() when stopNodeRuntime != null:
return stopNodeRuntime(_that.actorId,_that.target,_that.force);case TailNodeRuntimeLogsRequest() when tailNodeRuntimeLogs != null:
return tailNodeRuntimeLogs(_that.actorId,_that.target,_that.lineCount);case StreamNodeRuntimeEventsRequest() when streamNodeRuntimeEvents != null:
return streamNodeRuntimeEvents(_that.actorId,_that.target,_that.includeHistory);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DescribeNodeRuntimeRequest implements NodeDeployOperationRequest {
   DescribeNodeRuntimeRequest({@UuidValueConverter() this.actorId, this.target, final  String? $type}): $type = $type ?? 'describe_node_runtime';
  factory DescribeNodeRuntimeRequest.fromJson(Map<String, dynamic> json) => _$DescribeNodeRuntimeRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override final  NodeDeployTarget? target;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DescribeNodeRuntimeRequestCopyWith<DescribeNodeRuntimeRequest> get copyWith => _$DescribeNodeRuntimeRequestCopyWithImpl<DescribeNodeRuntimeRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DescribeNodeRuntimeRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DescribeNodeRuntimeRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.target, target) || other.target == target));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,target);

@override
String toString() {
  return 'NodeDeployOperationRequest.describeNodeRuntime(actorId: $actorId, target: $target)';
}


}

/// @nodoc
abstract mixin class $DescribeNodeRuntimeRequestCopyWith<$Res> implements $NodeDeployOperationRequestCopyWith<$Res> {
  factory $DescribeNodeRuntimeRequestCopyWith(DescribeNodeRuntimeRequest value, $Res Function(DescribeNodeRuntimeRequest) _then) = _$DescribeNodeRuntimeRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, NodeDeployTarget? target
});


@override $NodeDeployTargetCopyWith<$Res>? get target;

}
/// @nodoc
class _$DescribeNodeRuntimeRequestCopyWithImpl<$Res>
    implements $DescribeNodeRuntimeRequestCopyWith<$Res> {
  _$DescribeNodeRuntimeRequestCopyWithImpl(this._self, this._then);

  final DescribeNodeRuntimeRequest _self;
  final $Res Function(DescribeNodeRuntimeRequest) _then;

/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? target = freezed,}) {
  return _then(DescribeNodeRuntimeRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,target: freezed == target ? _self.target : target // ignore: cast_nullable_to_non_nullable
as NodeDeployTarget?,
  ));
}

/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployTargetCopyWith<$Res>? get target {
    if (_self.target == null) {
    return null;
  }

  return $NodeDeployTargetCopyWith<$Res>(_self.target!, (value) {
    return _then(_self.copyWith(target: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class EnsureNodeRuntimeStartedRequest implements NodeDeployOperationRequest {
   EnsureNodeRuntimeStartedRequest({@UuidValueConverter() this.actorId, this.target, required this.waitForReady, final  String? $type}): $type = $type ?? 'ensure_node_runtime_started';
  factory EnsureNodeRuntimeStartedRequest.fromJson(Map<String, dynamic> json) => _$EnsureNodeRuntimeStartedRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override final  NodeDeployTarget? target;
 final  bool waitForReady;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$EnsureNodeRuntimeStartedRequestCopyWith<EnsureNodeRuntimeStartedRequest> get copyWith => _$EnsureNodeRuntimeStartedRequestCopyWithImpl<EnsureNodeRuntimeStartedRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$EnsureNodeRuntimeStartedRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is EnsureNodeRuntimeStartedRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.target, target) || other.target == target)&&(identical(other.waitForReady, waitForReady) || other.waitForReady == waitForReady));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,target,waitForReady);

@override
String toString() {
  return 'NodeDeployOperationRequest.ensureNodeRuntimeStarted(actorId: $actorId, target: $target, waitForReady: $waitForReady)';
}


}

/// @nodoc
abstract mixin class $EnsureNodeRuntimeStartedRequestCopyWith<$Res> implements $NodeDeployOperationRequestCopyWith<$Res> {
  factory $EnsureNodeRuntimeStartedRequestCopyWith(EnsureNodeRuntimeStartedRequest value, $Res Function(EnsureNodeRuntimeStartedRequest) _then) = _$EnsureNodeRuntimeStartedRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, NodeDeployTarget? target, bool waitForReady
});


@override $NodeDeployTargetCopyWith<$Res>? get target;

}
/// @nodoc
class _$EnsureNodeRuntimeStartedRequestCopyWithImpl<$Res>
    implements $EnsureNodeRuntimeStartedRequestCopyWith<$Res> {
  _$EnsureNodeRuntimeStartedRequestCopyWithImpl(this._self, this._then);

  final EnsureNodeRuntimeStartedRequest _self;
  final $Res Function(EnsureNodeRuntimeStartedRequest) _then;

/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? target = freezed,Object? waitForReady = null,}) {
  return _then(EnsureNodeRuntimeStartedRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,target: freezed == target ? _self.target : target // ignore: cast_nullable_to_non_nullable
as NodeDeployTarget?,waitForReady: null == waitForReady ? _self.waitForReady : waitForReady // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}

/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployTargetCopyWith<$Res>? get target {
    if (_self.target == null) {
    return null;
  }

  return $NodeDeployTargetCopyWith<$Res>(_self.target!, (value) {
    return _then(_self.copyWith(target: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class RestartNodeRuntimeRequest implements NodeDeployOperationRequest {
   RestartNodeRuntimeRequest({@UuidValueConverter() this.actorId, this.target, required this.waitForReady, final  String? $type}): $type = $type ?? 'restart_node_runtime';
  factory RestartNodeRuntimeRequest.fromJson(Map<String, dynamic> json) => _$RestartNodeRuntimeRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override final  NodeDeployTarget? target;
 final  bool waitForReady;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$RestartNodeRuntimeRequestCopyWith<RestartNodeRuntimeRequest> get copyWith => _$RestartNodeRuntimeRequestCopyWithImpl<RestartNodeRuntimeRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$RestartNodeRuntimeRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is RestartNodeRuntimeRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.target, target) || other.target == target)&&(identical(other.waitForReady, waitForReady) || other.waitForReady == waitForReady));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,target,waitForReady);

@override
String toString() {
  return 'NodeDeployOperationRequest.restartNodeRuntime(actorId: $actorId, target: $target, waitForReady: $waitForReady)';
}


}

/// @nodoc
abstract mixin class $RestartNodeRuntimeRequestCopyWith<$Res> implements $NodeDeployOperationRequestCopyWith<$Res> {
  factory $RestartNodeRuntimeRequestCopyWith(RestartNodeRuntimeRequest value, $Res Function(RestartNodeRuntimeRequest) _then) = _$RestartNodeRuntimeRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, NodeDeployTarget? target, bool waitForReady
});


@override $NodeDeployTargetCopyWith<$Res>? get target;

}
/// @nodoc
class _$RestartNodeRuntimeRequestCopyWithImpl<$Res>
    implements $RestartNodeRuntimeRequestCopyWith<$Res> {
  _$RestartNodeRuntimeRequestCopyWithImpl(this._self, this._then);

  final RestartNodeRuntimeRequest _self;
  final $Res Function(RestartNodeRuntimeRequest) _then;

/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? target = freezed,Object? waitForReady = null,}) {
  return _then(RestartNodeRuntimeRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,target: freezed == target ? _self.target : target // ignore: cast_nullable_to_non_nullable
as NodeDeployTarget?,waitForReady: null == waitForReady ? _self.waitForReady : waitForReady // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}

/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployTargetCopyWith<$Res>? get target {
    if (_self.target == null) {
    return null;
  }

  return $NodeDeployTargetCopyWith<$Res>(_self.target!, (value) {
    return _then(_self.copyWith(target: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class StopNodeRuntimeRequest implements NodeDeployOperationRequest {
   StopNodeRuntimeRequest({@UuidValueConverter() this.actorId, this.target, required this.force, final  String? $type}): $type = $type ?? 'stop_node_runtime';
  factory StopNodeRuntimeRequest.fromJson(Map<String, dynamic> json) => _$StopNodeRuntimeRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override final  NodeDeployTarget? target;
 final  bool force;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$StopNodeRuntimeRequestCopyWith<StopNodeRuntimeRequest> get copyWith => _$StopNodeRuntimeRequestCopyWithImpl<StopNodeRuntimeRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$StopNodeRuntimeRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is StopNodeRuntimeRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.target, target) || other.target == target)&&(identical(other.force, force) || other.force == force));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,target,force);

@override
String toString() {
  return 'NodeDeployOperationRequest.stopNodeRuntime(actorId: $actorId, target: $target, force: $force)';
}


}

/// @nodoc
abstract mixin class $StopNodeRuntimeRequestCopyWith<$Res> implements $NodeDeployOperationRequestCopyWith<$Res> {
  factory $StopNodeRuntimeRequestCopyWith(StopNodeRuntimeRequest value, $Res Function(StopNodeRuntimeRequest) _then) = _$StopNodeRuntimeRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, NodeDeployTarget? target, bool force
});


@override $NodeDeployTargetCopyWith<$Res>? get target;

}
/// @nodoc
class _$StopNodeRuntimeRequestCopyWithImpl<$Res>
    implements $StopNodeRuntimeRequestCopyWith<$Res> {
  _$StopNodeRuntimeRequestCopyWithImpl(this._self, this._then);

  final StopNodeRuntimeRequest _self;
  final $Res Function(StopNodeRuntimeRequest) _then;

/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? target = freezed,Object? force = null,}) {
  return _then(StopNodeRuntimeRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,target: freezed == target ? _self.target : target // ignore: cast_nullable_to_non_nullable
as NodeDeployTarget?,force: null == force ? _self.force : force // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}

/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployTargetCopyWith<$Res>? get target {
    if (_self.target == null) {
    return null;
  }

  return $NodeDeployTargetCopyWith<$Res>(_self.target!, (value) {
    return _then(_self.copyWith(target: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class TailNodeRuntimeLogsRequest implements NodeDeployOperationRequest {
   TailNodeRuntimeLogsRequest({@UuidValueConverter() this.actorId, this.target, required this.lineCount, final  String? $type}): $type = $type ?? 'tail_node_runtime_logs';
  factory TailNodeRuntimeLogsRequest.fromJson(Map<String, dynamic> json) => _$TailNodeRuntimeLogsRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override final  NodeDeployTarget? target;
 final  int lineCount;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$TailNodeRuntimeLogsRequestCopyWith<TailNodeRuntimeLogsRequest> get copyWith => _$TailNodeRuntimeLogsRequestCopyWithImpl<TailNodeRuntimeLogsRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$TailNodeRuntimeLogsRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is TailNodeRuntimeLogsRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.target, target) || other.target == target)&&(identical(other.lineCount, lineCount) || other.lineCount == lineCount));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,target,lineCount);

@override
String toString() {
  return 'NodeDeployOperationRequest.tailNodeRuntimeLogs(actorId: $actorId, target: $target, lineCount: $lineCount)';
}


}

/// @nodoc
abstract mixin class $TailNodeRuntimeLogsRequestCopyWith<$Res> implements $NodeDeployOperationRequestCopyWith<$Res> {
  factory $TailNodeRuntimeLogsRequestCopyWith(TailNodeRuntimeLogsRequest value, $Res Function(TailNodeRuntimeLogsRequest) _then) = _$TailNodeRuntimeLogsRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, NodeDeployTarget? target, int lineCount
});


@override $NodeDeployTargetCopyWith<$Res>? get target;

}
/// @nodoc
class _$TailNodeRuntimeLogsRequestCopyWithImpl<$Res>
    implements $TailNodeRuntimeLogsRequestCopyWith<$Res> {
  _$TailNodeRuntimeLogsRequestCopyWithImpl(this._self, this._then);

  final TailNodeRuntimeLogsRequest _self;
  final $Res Function(TailNodeRuntimeLogsRequest) _then;

/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? target = freezed,Object? lineCount = null,}) {
  return _then(TailNodeRuntimeLogsRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,target: freezed == target ? _self.target : target // ignore: cast_nullable_to_non_nullable
as NodeDeployTarget?,lineCount: null == lineCount ? _self.lineCount : lineCount // ignore: cast_nullable_to_non_nullable
as int,
  ));
}

/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployTargetCopyWith<$Res>? get target {
    if (_self.target == null) {
    return null;
  }

  return $NodeDeployTargetCopyWith<$Res>(_self.target!, (value) {
    return _then(_self.copyWith(target: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class StreamNodeRuntimeEventsRequest implements NodeDeployOperationRequest {
   StreamNodeRuntimeEventsRequest({@UuidValueConverter() this.actorId, this.target, required this.includeHistory, final  String? $type}): $type = $type ?? 'stream_node_runtime_events';
  factory StreamNodeRuntimeEventsRequest.fromJson(Map<String, dynamic> json) => _$StreamNodeRuntimeEventsRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override final  NodeDeployTarget? target;
 final  bool includeHistory;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$StreamNodeRuntimeEventsRequestCopyWith<StreamNodeRuntimeEventsRequest> get copyWith => _$StreamNodeRuntimeEventsRequestCopyWithImpl<StreamNodeRuntimeEventsRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$StreamNodeRuntimeEventsRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is StreamNodeRuntimeEventsRequest&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.target, target) || other.target == target)&&(identical(other.includeHistory, includeHistory) || other.includeHistory == includeHistory));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,target,includeHistory);

@override
String toString() {
  return 'NodeDeployOperationRequest.streamNodeRuntimeEvents(actorId: $actorId, target: $target, includeHistory: $includeHistory)';
}


}

/// @nodoc
abstract mixin class $StreamNodeRuntimeEventsRequestCopyWith<$Res> implements $NodeDeployOperationRequestCopyWith<$Res> {
  factory $StreamNodeRuntimeEventsRequestCopyWith(StreamNodeRuntimeEventsRequest value, $Res Function(StreamNodeRuntimeEventsRequest) _then) = _$StreamNodeRuntimeEventsRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, NodeDeployTarget? target, bool includeHistory
});


@override $NodeDeployTargetCopyWith<$Res>? get target;

}
/// @nodoc
class _$StreamNodeRuntimeEventsRequestCopyWithImpl<$Res>
    implements $StreamNodeRuntimeEventsRequestCopyWith<$Res> {
  _$StreamNodeRuntimeEventsRequestCopyWithImpl(this._self, this._then);

  final StreamNodeRuntimeEventsRequest _self;
  final $Res Function(StreamNodeRuntimeEventsRequest) _then;

/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? target = freezed,Object? includeHistory = null,}) {
  return _then(StreamNodeRuntimeEventsRequest(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,target: freezed == target ? _self.target : target // ignore: cast_nullable_to_non_nullable
as NodeDeployTarget?,includeHistory: null == includeHistory ? _self.includeHistory : includeHistory // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}

/// Create a copy of NodeDeployOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployTargetCopyWith<$Res>? get target {
    if (_self.target == null) {
    return null;
  }

  return $NodeDeployTargetCopyWith<$Res>(_self.target!, (value) {
    return _then(_self.copyWith(target: value));
  });
}
}

NodeDeployOperationResponse _$NodeDeployOperationResponseFromJson(
  Map<String, dynamic> json
) {
        switch (json['operation']) {
                  case 'describe_node_runtime':
          return DescribeNodeRuntimeResponse.fromJson(
            json
          );
                case 'ensure_node_runtime_started':
          return EnsureNodeRuntimeStartedResponse.fromJson(
            json
          );
                case 'restart_node_runtime':
          return RestartNodeRuntimeResponse.fromJson(
            json
          );
                case 'stop_node_runtime':
          return StopNodeRuntimeResponse.fromJson(
            json
          );
                case 'tail_node_runtime_logs':
          return TailNodeRuntimeLogsResponse.fromJson(
            json
          );
                case 'stream_node_runtime_events':
          return StreamNodeRuntimeEventsResponse.fromJson(
            json
          );
        
          default:
            throw CheckedFromJsonException(
  json,
  'operation',
  'NodeDeployOperationResponse',
  'Invalid union type "${json['operation']}"!'
);
        }
      
}

/// @nodoc
mixin _$NodeDeployOperationResponse {

@UuidValueConverter() UuidValue? get actorId; String get status; String? get error; NodeDeployRuntimeStatus? get runtimeStatus;
/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NodeDeployOperationResponseCopyWith<NodeDeployOperationResponse> get copyWith => _$NodeDeployOperationResponseCopyWithImpl<NodeDeployOperationResponse>(this as NodeDeployOperationResponse, _$identity);

  /// Serializes this NodeDeployOperationResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NodeDeployOperationResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.runtimeStatus, runtimeStatus) || other.runtimeStatus == runtimeStatus));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,status,error,runtimeStatus);

@override
String toString() {
  return 'NodeDeployOperationResponse(actorId: $actorId, status: $status, error: $error, runtimeStatus: $runtimeStatus)';
}


}

/// @nodoc
abstract mixin class $NodeDeployOperationResponseCopyWith<$Res>  {
  factory $NodeDeployOperationResponseCopyWith(NodeDeployOperationResponse value, $Res Function(NodeDeployOperationResponse) _then) = _$NodeDeployOperationResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, String status, String? error, NodeDeployRuntimeStatus? runtimeStatus
});


$NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus;

}
/// @nodoc
class _$NodeDeployOperationResponseCopyWithImpl<$Res>
    implements $NodeDeployOperationResponseCopyWith<$Res> {
  _$NodeDeployOperationResponseCopyWithImpl(this._self, this._then);

  final NodeDeployOperationResponse _self;
  final $Res Function(NodeDeployOperationResponse) _then;

/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? status = null,Object? error = freezed,Object? runtimeStatus = freezed,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,runtimeStatus: freezed == runtimeStatus ? _self.runtimeStatus : runtimeStatus // ignore: cast_nullable_to_non_nullable
as NodeDeployRuntimeStatus?,
  ));
}
/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus {
    if (_self.runtimeStatus == null) {
    return null;
  }

  return $NodeDeployRuntimeStatusCopyWith<$Res>(_self.runtimeStatus!, (value) {
    return _then(_self.copyWith(runtimeStatus: value));
  });
}
}


/// Adds pattern-matching-related methods to [NodeDeployOperationResponse].
extension NodeDeployOperationResponsePatterns on NodeDeployOperationResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( DescribeNodeRuntimeResponse value)?  describeNodeRuntime,TResult Function( EnsureNodeRuntimeStartedResponse value)?  ensureNodeRuntimeStarted,TResult Function( RestartNodeRuntimeResponse value)?  restartNodeRuntime,TResult Function( StopNodeRuntimeResponse value)?  stopNodeRuntime,TResult Function( TailNodeRuntimeLogsResponse value)?  tailNodeRuntimeLogs,TResult Function( StreamNodeRuntimeEventsResponse value)?  streamNodeRuntimeEvents,required TResult orElse(),}){
final _that = this;
switch (_that) {
case DescribeNodeRuntimeResponse() when describeNodeRuntime != null:
return describeNodeRuntime(_that);case EnsureNodeRuntimeStartedResponse() when ensureNodeRuntimeStarted != null:
return ensureNodeRuntimeStarted(_that);case RestartNodeRuntimeResponse() when restartNodeRuntime != null:
return restartNodeRuntime(_that);case StopNodeRuntimeResponse() when stopNodeRuntime != null:
return stopNodeRuntime(_that);case TailNodeRuntimeLogsResponse() when tailNodeRuntimeLogs != null:
return tailNodeRuntimeLogs(_that);case StreamNodeRuntimeEventsResponse() when streamNodeRuntimeEvents != null:
return streamNodeRuntimeEvents(_that);case _:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( DescribeNodeRuntimeResponse value)  describeNodeRuntime,required TResult Function( EnsureNodeRuntimeStartedResponse value)  ensureNodeRuntimeStarted,required TResult Function( RestartNodeRuntimeResponse value)  restartNodeRuntime,required TResult Function( StopNodeRuntimeResponse value)  stopNodeRuntime,required TResult Function( TailNodeRuntimeLogsResponse value)  tailNodeRuntimeLogs,required TResult Function( StreamNodeRuntimeEventsResponse value)  streamNodeRuntimeEvents,}){
final _that = this;
switch (_that) {
case DescribeNodeRuntimeResponse():
return describeNodeRuntime(_that);case EnsureNodeRuntimeStartedResponse():
return ensureNodeRuntimeStarted(_that);case RestartNodeRuntimeResponse():
return restartNodeRuntime(_that);case StopNodeRuntimeResponse():
return stopNodeRuntime(_that);case TailNodeRuntimeLogsResponse():
return tailNodeRuntimeLogs(_that);case StreamNodeRuntimeEventsResponse():
return streamNodeRuntimeEvents(_that);case _:
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( DescribeNodeRuntimeResponse value)?  describeNodeRuntime,TResult? Function( EnsureNodeRuntimeStartedResponse value)?  ensureNodeRuntimeStarted,TResult? Function( RestartNodeRuntimeResponse value)?  restartNodeRuntime,TResult? Function( StopNodeRuntimeResponse value)?  stopNodeRuntime,TResult? Function( TailNodeRuntimeLogsResponse value)?  tailNodeRuntimeLogs,TResult? Function( StreamNodeRuntimeEventsResponse value)?  streamNodeRuntimeEvents,}){
final _that = this;
switch (_that) {
case DescribeNodeRuntimeResponse() when describeNodeRuntime != null:
return describeNodeRuntime(_that);case EnsureNodeRuntimeStartedResponse() when ensureNodeRuntimeStarted != null:
return ensureNodeRuntimeStarted(_that);case RestartNodeRuntimeResponse() when restartNodeRuntime != null:
return restartNodeRuntime(_that);case StopNodeRuntimeResponse() when stopNodeRuntime != null:
return stopNodeRuntime(_that);case TailNodeRuntimeLogsResponse() when tailNodeRuntimeLogs != null:
return tailNodeRuntimeLogs(_that);case StreamNodeRuntimeEventsResponse() when streamNodeRuntimeEvents != null:
return streamNodeRuntimeEvents(_that);case _:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId,  String status,  String? error,  NodeDeployRuntimeStatus? runtimeStatus)?  describeNodeRuntime,TResult Function(@UuidValueConverter()  UuidValue? actorId,  String status,  String? error,  NodeDeployRuntimeStatus? runtimeStatus)?  ensureNodeRuntimeStarted,TResult Function(@UuidValueConverter()  UuidValue? actorId,  String status,  String? error,  NodeDeployRuntimeStatus? runtimeStatus)?  restartNodeRuntime,TResult Function(@UuidValueConverter()  UuidValue? actorId,  String status,  String? error,  NodeDeployRuntimeStatus? runtimeStatus)?  stopNodeRuntime,TResult Function(@UuidValueConverter()  UuidValue? actorId,  String status,  String? error,  NodeDeployRuntimeStatus? runtimeStatus,  List<String> logLines)?  tailNodeRuntimeLogs,TResult Function(@UuidValueConverter()  UuidValue? actorId,  String status,  String? error,  NodeDeployRuntimeStatus? runtimeStatus,  bool streamOpen)?  streamNodeRuntimeEvents,required TResult orElse(),}) {final _that = this;
switch (_that) {
case DescribeNodeRuntimeResponse() when describeNodeRuntime != null:
return describeNodeRuntime(_that.actorId,_that.status,_that.error,_that.runtimeStatus);case EnsureNodeRuntimeStartedResponse() when ensureNodeRuntimeStarted != null:
return ensureNodeRuntimeStarted(_that.actorId,_that.status,_that.error,_that.runtimeStatus);case RestartNodeRuntimeResponse() when restartNodeRuntime != null:
return restartNodeRuntime(_that.actorId,_that.status,_that.error,_that.runtimeStatus);case StopNodeRuntimeResponse() when stopNodeRuntime != null:
return stopNodeRuntime(_that.actorId,_that.status,_that.error,_that.runtimeStatus);case TailNodeRuntimeLogsResponse() when tailNodeRuntimeLogs != null:
return tailNodeRuntimeLogs(_that.actorId,_that.status,_that.error,_that.runtimeStatus,_that.logLines);case StreamNodeRuntimeEventsResponse() when streamNodeRuntimeEvents != null:
return streamNodeRuntimeEvents(_that.actorId,_that.status,_that.error,_that.runtimeStatus,_that.streamOpen);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId,  String status,  String? error,  NodeDeployRuntimeStatus? runtimeStatus)  describeNodeRuntime,required TResult Function(@UuidValueConverter()  UuidValue? actorId,  String status,  String? error,  NodeDeployRuntimeStatus? runtimeStatus)  ensureNodeRuntimeStarted,required TResult Function(@UuidValueConverter()  UuidValue? actorId,  String status,  String? error,  NodeDeployRuntimeStatus? runtimeStatus)  restartNodeRuntime,required TResult Function(@UuidValueConverter()  UuidValue? actorId,  String status,  String? error,  NodeDeployRuntimeStatus? runtimeStatus)  stopNodeRuntime,required TResult Function(@UuidValueConverter()  UuidValue? actorId,  String status,  String? error,  NodeDeployRuntimeStatus? runtimeStatus,  List<String> logLines)  tailNodeRuntimeLogs,required TResult Function(@UuidValueConverter()  UuidValue? actorId,  String status,  String? error,  NodeDeployRuntimeStatus? runtimeStatus,  bool streamOpen)  streamNodeRuntimeEvents,}) {final _that = this;
switch (_that) {
case DescribeNodeRuntimeResponse():
return describeNodeRuntime(_that.actorId,_that.status,_that.error,_that.runtimeStatus);case EnsureNodeRuntimeStartedResponse():
return ensureNodeRuntimeStarted(_that.actorId,_that.status,_that.error,_that.runtimeStatus);case RestartNodeRuntimeResponse():
return restartNodeRuntime(_that.actorId,_that.status,_that.error,_that.runtimeStatus);case StopNodeRuntimeResponse():
return stopNodeRuntime(_that.actorId,_that.status,_that.error,_that.runtimeStatus);case TailNodeRuntimeLogsResponse():
return tailNodeRuntimeLogs(_that.actorId,_that.status,_that.error,_that.runtimeStatus,_that.logLines);case StreamNodeRuntimeEventsResponse():
return streamNodeRuntimeEvents(_that.actorId,_that.status,_that.error,_that.runtimeStatus,_that.streamOpen);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId,  String status,  String? error,  NodeDeployRuntimeStatus? runtimeStatus)?  describeNodeRuntime,TResult? Function(@UuidValueConverter()  UuidValue? actorId,  String status,  String? error,  NodeDeployRuntimeStatus? runtimeStatus)?  ensureNodeRuntimeStarted,TResult? Function(@UuidValueConverter()  UuidValue? actorId,  String status,  String? error,  NodeDeployRuntimeStatus? runtimeStatus)?  restartNodeRuntime,TResult? Function(@UuidValueConverter()  UuidValue? actorId,  String status,  String? error,  NodeDeployRuntimeStatus? runtimeStatus)?  stopNodeRuntime,TResult? Function(@UuidValueConverter()  UuidValue? actorId,  String status,  String? error,  NodeDeployRuntimeStatus? runtimeStatus,  List<String> logLines)?  tailNodeRuntimeLogs,TResult? Function(@UuidValueConverter()  UuidValue? actorId,  String status,  String? error,  NodeDeployRuntimeStatus? runtimeStatus,  bool streamOpen)?  streamNodeRuntimeEvents,}) {final _that = this;
switch (_that) {
case DescribeNodeRuntimeResponse() when describeNodeRuntime != null:
return describeNodeRuntime(_that.actorId,_that.status,_that.error,_that.runtimeStatus);case EnsureNodeRuntimeStartedResponse() when ensureNodeRuntimeStarted != null:
return ensureNodeRuntimeStarted(_that.actorId,_that.status,_that.error,_that.runtimeStatus);case RestartNodeRuntimeResponse() when restartNodeRuntime != null:
return restartNodeRuntime(_that.actorId,_that.status,_that.error,_that.runtimeStatus);case StopNodeRuntimeResponse() when stopNodeRuntime != null:
return stopNodeRuntime(_that.actorId,_that.status,_that.error,_that.runtimeStatus);case TailNodeRuntimeLogsResponse() when tailNodeRuntimeLogs != null:
return tailNodeRuntimeLogs(_that.actorId,_that.status,_that.error,_that.runtimeStatus,_that.logLines);case StreamNodeRuntimeEventsResponse() when streamNodeRuntimeEvents != null:
return streamNodeRuntimeEvents(_that.actorId,_that.status,_that.error,_that.runtimeStatus,_that.streamOpen);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class DescribeNodeRuntimeResponse implements NodeDeployOperationResponse {
   DescribeNodeRuntimeResponse({@UuidValueConverter() this.actorId, required this.status, this.error, this.runtimeStatus, final  String? $type}): $type = $type ?? 'describe_node_runtime';
  factory DescribeNodeRuntimeResponse.fromJson(Map<String, dynamic> json) => _$DescribeNodeRuntimeResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override final  String status;
@override final  String? error;
@override final  NodeDeployRuntimeStatus? runtimeStatus;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$DescribeNodeRuntimeResponseCopyWith<DescribeNodeRuntimeResponse> get copyWith => _$DescribeNodeRuntimeResponseCopyWithImpl<DescribeNodeRuntimeResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$DescribeNodeRuntimeResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is DescribeNodeRuntimeResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.runtimeStatus, runtimeStatus) || other.runtimeStatus == runtimeStatus));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,status,error,runtimeStatus);

@override
String toString() {
  return 'NodeDeployOperationResponse.describeNodeRuntime(actorId: $actorId, status: $status, error: $error, runtimeStatus: $runtimeStatus)';
}


}

/// @nodoc
abstract mixin class $DescribeNodeRuntimeResponseCopyWith<$Res> implements $NodeDeployOperationResponseCopyWith<$Res> {
  factory $DescribeNodeRuntimeResponseCopyWith(DescribeNodeRuntimeResponse value, $Res Function(DescribeNodeRuntimeResponse) _then) = _$DescribeNodeRuntimeResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, String status, String? error, NodeDeployRuntimeStatus? runtimeStatus
});


@override $NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus;

}
/// @nodoc
class _$DescribeNodeRuntimeResponseCopyWithImpl<$Res>
    implements $DescribeNodeRuntimeResponseCopyWith<$Res> {
  _$DescribeNodeRuntimeResponseCopyWithImpl(this._self, this._then);

  final DescribeNodeRuntimeResponse _self;
  final $Res Function(DescribeNodeRuntimeResponse) _then;

/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? status = null,Object? error = freezed,Object? runtimeStatus = freezed,}) {
  return _then(DescribeNodeRuntimeResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,runtimeStatus: freezed == runtimeStatus ? _self.runtimeStatus : runtimeStatus // ignore: cast_nullable_to_non_nullable
as NodeDeployRuntimeStatus?,
  ));
}

/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus {
    if (_self.runtimeStatus == null) {
    return null;
  }

  return $NodeDeployRuntimeStatusCopyWith<$Res>(_self.runtimeStatus!, (value) {
    return _then(_self.copyWith(runtimeStatus: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class EnsureNodeRuntimeStartedResponse implements NodeDeployOperationResponse {
   EnsureNodeRuntimeStartedResponse({@UuidValueConverter() this.actorId, required this.status, this.error, this.runtimeStatus, final  String? $type}): $type = $type ?? 'ensure_node_runtime_started';
  factory EnsureNodeRuntimeStartedResponse.fromJson(Map<String, dynamic> json) => _$EnsureNodeRuntimeStartedResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override final  String status;
@override final  String? error;
@override final  NodeDeployRuntimeStatus? runtimeStatus;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$EnsureNodeRuntimeStartedResponseCopyWith<EnsureNodeRuntimeStartedResponse> get copyWith => _$EnsureNodeRuntimeStartedResponseCopyWithImpl<EnsureNodeRuntimeStartedResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$EnsureNodeRuntimeStartedResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is EnsureNodeRuntimeStartedResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.runtimeStatus, runtimeStatus) || other.runtimeStatus == runtimeStatus));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,status,error,runtimeStatus);

@override
String toString() {
  return 'NodeDeployOperationResponse.ensureNodeRuntimeStarted(actorId: $actorId, status: $status, error: $error, runtimeStatus: $runtimeStatus)';
}


}

/// @nodoc
abstract mixin class $EnsureNodeRuntimeStartedResponseCopyWith<$Res> implements $NodeDeployOperationResponseCopyWith<$Res> {
  factory $EnsureNodeRuntimeStartedResponseCopyWith(EnsureNodeRuntimeStartedResponse value, $Res Function(EnsureNodeRuntimeStartedResponse) _then) = _$EnsureNodeRuntimeStartedResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, String status, String? error, NodeDeployRuntimeStatus? runtimeStatus
});


@override $NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus;

}
/// @nodoc
class _$EnsureNodeRuntimeStartedResponseCopyWithImpl<$Res>
    implements $EnsureNodeRuntimeStartedResponseCopyWith<$Res> {
  _$EnsureNodeRuntimeStartedResponseCopyWithImpl(this._self, this._then);

  final EnsureNodeRuntimeStartedResponse _self;
  final $Res Function(EnsureNodeRuntimeStartedResponse) _then;

/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? status = null,Object? error = freezed,Object? runtimeStatus = freezed,}) {
  return _then(EnsureNodeRuntimeStartedResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,runtimeStatus: freezed == runtimeStatus ? _self.runtimeStatus : runtimeStatus // ignore: cast_nullable_to_non_nullable
as NodeDeployRuntimeStatus?,
  ));
}

/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus {
    if (_self.runtimeStatus == null) {
    return null;
  }

  return $NodeDeployRuntimeStatusCopyWith<$Res>(_self.runtimeStatus!, (value) {
    return _then(_self.copyWith(runtimeStatus: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class RestartNodeRuntimeResponse implements NodeDeployOperationResponse {
   RestartNodeRuntimeResponse({@UuidValueConverter() this.actorId, required this.status, this.error, this.runtimeStatus, final  String? $type}): $type = $type ?? 'restart_node_runtime';
  factory RestartNodeRuntimeResponse.fromJson(Map<String, dynamic> json) => _$RestartNodeRuntimeResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override final  String status;
@override final  String? error;
@override final  NodeDeployRuntimeStatus? runtimeStatus;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$RestartNodeRuntimeResponseCopyWith<RestartNodeRuntimeResponse> get copyWith => _$RestartNodeRuntimeResponseCopyWithImpl<RestartNodeRuntimeResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$RestartNodeRuntimeResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is RestartNodeRuntimeResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.runtimeStatus, runtimeStatus) || other.runtimeStatus == runtimeStatus));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,status,error,runtimeStatus);

@override
String toString() {
  return 'NodeDeployOperationResponse.restartNodeRuntime(actorId: $actorId, status: $status, error: $error, runtimeStatus: $runtimeStatus)';
}


}

/// @nodoc
abstract mixin class $RestartNodeRuntimeResponseCopyWith<$Res> implements $NodeDeployOperationResponseCopyWith<$Res> {
  factory $RestartNodeRuntimeResponseCopyWith(RestartNodeRuntimeResponse value, $Res Function(RestartNodeRuntimeResponse) _then) = _$RestartNodeRuntimeResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, String status, String? error, NodeDeployRuntimeStatus? runtimeStatus
});


@override $NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus;

}
/// @nodoc
class _$RestartNodeRuntimeResponseCopyWithImpl<$Res>
    implements $RestartNodeRuntimeResponseCopyWith<$Res> {
  _$RestartNodeRuntimeResponseCopyWithImpl(this._self, this._then);

  final RestartNodeRuntimeResponse _self;
  final $Res Function(RestartNodeRuntimeResponse) _then;

/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? status = null,Object? error = freezed,Object? runtimeStatus = freezed,}) {
  return _then(RestartNodeRuntimeResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,runtimeStatus: freezed == runtimeStatus ? _self.runtimeStatus : runtimeStatus // ignore: cast_nullable_to_non_nullable
as NodeDeployRuntimeStatus?,
  ));
}

/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus {
    if (_self.runtimeStatus == null) {
    return null;
  }

  return $NodeDeployRuntimeStatusCopyWith<$Res>(_self.runtimeStatus!, (value) {
    return _then(_self.copyWith(runtimeStatus: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class StopNodeRuntimeResponse implements NodeDeployOperationResponse {
   StopNodeRuntimeResponse({@UuidValueConverter() this.actorId, required this.status, this.error, this.runtimeStatus, final  String? $type}): $type = $type ?? 'stop_node_runtime';
  factory StopNodeRuntimeResponse.fromJson(Map<String, dynamic> json) => _$StopNodeRuntimeResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override final  String status;
@override final  String? error;
@override final  NodeDeployRuntimeStatus? runtimeStatus;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$StopNodeRuntimeResponseCopyWith<StopNodeRuntimeResponse> get copyWith => _$StopNodeRuntimeResponseCopyWithImpl<StopNodeRuntimeResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$StopNodeRuntimeResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is StopNodeRuntimeResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.runtimeStatus, runtimeStatus) || other.runtimeStatus == runtimeStatus));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,status,error,runtimeStatus);

@override
String toString() {
  return 'NodeDeployOperationResponse.stopNodeRuntime(actorId: $actorId, status: $status, error: $error, runtimeStatus: $runtimeStatus)';
}


}

/// @nodoc
abstract mixin class $StopNodeRuntimeResponseCopyWith<$Res> implements $NodeDeployOperationResponseCopyWith<$Res> {
  factory $StopNodeRuntimeResponseCopyWith(StopNodeRuntimeResponse value, $Res Function(StopNodeRuntimeResponse) _then) = _$StopNodeRuntimeResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, String status, String? error, NodeDeployRuntimeStatus? runtimeStatus
});


@override $NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus;

}
/// @nodoc
class _$StopNodeRuntimeResponseCopyWithImpl<$Res>
    implements $StopNodeRuntimeResponseCopyWith<$Res> {
  _$StopNodeRuntimeResponseCopyWithImpl(this._self, this._then);

  final StopNodeRuntimeResponse _self;
  final $Res Function(StopNodeRuntimeResponse) _then;

/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? status = null,Object? error = freezed,Object? runtimeStatus = freezed,}) {
  return _then(StopNodeRuntimeResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,runtimeStatus: freezed == runtimeStatus ? _self.runtimeStatus : runtimeStatus // ignore: cast_nullable_to_non_nullable
as NodeDeployRuntimeStatus?,
  ));
}

/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus {
    if (_self.runtimeStatus == null) {
    return null;
  }

  return $NodeDeployRuntimeStatusCopyWith<$Res>(_self.runtimeStatus!, (value) {
    return _then(_self.copyWith(runtimeStatus: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class TailNodeRuntimeLogsResponse implements NodeDeployOperationResponse {
   TailNodeRuntimeLogsResponse({@UuidValueConverter() this.actorId, required this.status, this.error, this.runtimeStatus, final  List<String> logLines = const [], final  String? $type}): _logLines = logLines,$type = $type ?? 'tail_node_runtime_logs';
  factory TailNodeRuntimeLogsResponse.fromJson(Map<String, dynamic> json) => _$TailNodeRuntimeLogsResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override final  String status;
@override final  String? error;
@override final  NodeDeployRuntimeStatus? runtimeStatus;
 final  List<String> _logLines;
@JsonKey() List<String> get logLines {
  if (_logLines is EqualUnmodifiableListView) return _logLines;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_logLines);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$TailNodeRuntimeLogsResponseCopyWith<TailNodeRuntimeLogsResponse> get copyWith => _$TailNodeRuntimeLogsResponseCopyWithImpl<TailNodeRuntimeLogsResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$TailNodeRuntimeLogsResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is TailNodeRuntimeLogsResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.runtimeStatus, runtimeStatus) || other.runtimeStatus == runtimeStatus)&&const DeepCollectionEquality().equals(other._logLines, _logLines));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,status,error,runtimeStatus,const DeepCollectionEquality().hash(_logLines));

@override
String toString() {
  return 'NodeDeployOperationResponse.tailNodeRuntimeLogs(actorId: $actorId, status: $status, error: $error, runtimeStatus: $runtimeStatus, logLines: $logLines)';
}


}

/// @nodoc
abstract mixin class $TailNodeRuntimeLogsResponseCopyWith<$Res> implements $NodeDeployOperationResponseCopyWith<$Res> {
  factory $TailNodeRuntimeLogsResponseCopyWith(TailNodeRuntimeLogsResponse value, $Res Function(TailNodeRuntimeLogsResponse) _then) = _$TailNodeRuntimeLogsResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, String status, String? error, NodeDeployRuntimeStatus? runtimeStatus, List<String> logLines
});


@override $NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus;

}
/// @nodoc
class _$TailNodeRuntimeLogsResponseCopyWithImpl<$Res>
    implements $TailNodeRuntimeLogsResponseCopyWith<$Res> {
  _$TailNodeRuntimeLogsResponseCopyWithImpl(this._self, this._then);

  final TailNodeRuntimeLogsResponse _self;
  final $Res Function(TailNodeRuntimeLogsResponse) _then;

/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? status = null,Object? error = freezed,Object? runtimeStatus = freezed,Object? logLines = null,}) {
  return _then(TailNodeRuntimeLogsResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,runtimeStatus: freezed == runtimeStatus ? _self.runtimeStatus : runtimeStatus // ignore: cast_nullable_to_non_nullable
as NodeDeployRuntimeStatus?,logLines: null == logLines ? _self._logLines : logLines // ignore: cast_nullable_to_non_nullable
as List<String>,
  ));
}

/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus {
    if (_self.runtimeStatus == null) {
    return null;
  }

  return $NodeDeployRuntimeStatusCopyWith<$Res>(_self.runtimeStatus!, (value) {
    return _then(_self.copyWith(runtimeStatus: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class StreamNodeRuntimeEventsResponse implements NodeDeployOperationResponse {
   StreamNodeRuntimeEventsResponse({@UuidValueConverter() this.actorId, required this.status, this.error, this.runtimeStatus, required this.streamOpen, final  String? $type}): $type = $type ?? 'stream_node_runtime_events';
  factory StreamNodeRuntimeEventsResponse.fromJson(Map<String, dynamic> json) => _$StreamNodeRuntimeEventsResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override final  String status;
@override final  String? error;
@override final  NodeDeployRuntimeStatus? runtimeStatus;
 final  bool streamOpen;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$StreamNodeRuntimeEventsResponseCopyWith<StreamNodeRuntimeEventsResponse> get copyWith => _$StreamNodeRuntimeEventsResponseCopyWithImpl<StreamNodeRuntimeEventsResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$StreamNodeRuntimeEventsResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is StreamNodeRuntimeEventsResponse&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&(identical(other.runtimeStatus, runtimeStatus) || other.runtimeStatus == runtimeStatus)&&(identical(other.streamOpen, streamOpen) || other.streamOpen == streamOpen));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,status,error,runtimeStatus,streamOpen);

@override
String toString() {
  return 'NodeDeployOperationResponse.streamNodeRuntimeEvents(actorId: $actorId, status: $status, error: $error, runtimeStatus: $runtimeStatus, streamOpen: $streamOpen)';
}


}

/// @nodoc
abstract mixin class $StreamNodeRuntimeEventsResponseCopyWith<$Res> implements $NodeDeployOperationResponseCopyWith<$Res> {
  factory $StreamNodeRuntimeEventsResponseCopyWith(StreamNodeRuntimeEventsResponse value, $Res Function(StreamNodeRuntimeEventsResponse) _then) = _$StreamNodeRuntimeEventsResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, String status, String? error, NodeDeployRuntimeStatus? runtimeStatus, bool streamOpen
});


@override $NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus;

}
/// @nodoc
class _$StreamNodeRuntimeEventsResponseCopyWithImpl<$Res>
    implements $StreamNodeRuntimeEventsResponseCopyWith<$Res> {
  _$StreamNodeRuntimeEventsResponseCopyWithImpl(this._self, this._then);

  final StreamNodeRuntimeEventsResponse _self;
  final $Res Function(StreamNodeRuntimeEventsResponse) _then;

/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? status = null,Object? error = freezed,Object? runtimeStatus = freezed,Object? streamOpen = null,}) {
  return _then(StreamNodeRuntimeEventsResponse(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,runtimeStatus: freezed == runtimeStatus ? _self.runtimeStatus : runtimeStatus // ignore: cast_nullable_to_non_nullable
as NodeDeployRuntimeStatus?,streamOpen: null == streamOpen ? _self.streamOpen : streamOpen // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}

/// Create a copy of NodeDeployOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus {
    if (_self.runtimeStatus == null) {
    return null;
  }

  return $NodeDeployRuntimeStatusCopyWith<$Res>(_self.runtimeStatus!, (value) {
    return _then(_self.copyWith(runtimeStatus: value));
  });
}
}

NodeDeployOperationEvent _$NodeDeployOperationEventFromJson(
  Map<String, dynamic> json
) {
        switch (json['kind']) {
                  case 'runtime_status':
          return NodeDeployRuntimeStatusEvent.fromJson(
            json
          );
                case 'runtime_log':
          return NodeDeployRuntimeLogEvent.fromJson(
            json
          );
                case 'runtime_terminal':
          return NodeDeployRuntimeTerminalEvent.fromJson(
            json
          );
        
          default:
            throw CheckedFromJsonException(
  json,
  'kind',
  'NodeDeployOperationEvent',
  'Invalid union type "${json['kind']}"!'
);
        }
      
}

/// @nodoc
mixin _$NodeDeployOperationEvent {

@UuidValueConverter() UuidValue? get actorId; String? get operation; NodeDeployRuntimeStatus? get runtimeStatus; String? get message; String? get timestamp;
/// Create a copy of NodeDeployOperationEvent
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NodeDeployOperationEventCopyWith<NodeDeployOperationEvent> get copyWith => _$NodeDeployOperationEventCopyWithImpl<NodeDeployOperationEvent>(this as NodeDeployOperationEvent, _$identity);

  /// Serializes this NodeDeployOperationEvent to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NodeDeployOperationEvent&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.runtimeStatus, runtimeStatus) || other.runtimeStatus == runtimeStatus)&&(identical(other.message, message) || other.message == message)&&(identical(other.timestamp, timestamp) || other.timestamp == timestamp));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,operation,runtimeStatus,message,timestamp);

@override
String toString() {
  return 'NodeDeployOperationEvent(actorId: $actorId, operation: $operation, runtimeStatus: $runtimeStatus, message: $message, timestamp: $timestamp)';
}


}

/// @nodoc
abstract mixin class $NodeDeployOperationEventCopyWith<$Res>  {
  factory $NodeDeployOperationEventCopyWith(NodeDeployOperationEvent value, $Res Function(NodeDeployOperationEvent) _then) = _$NodeDeployOperationEventCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, String? operation, NodeDeployRuntimeStatus? runtimeStatus, String? message, String? timestamp
});


$NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus;

}
/// @nodoc
class _$NodeDeployOperationEventCopyWithImpl<$Res>
    implements $NodeDeployOperationEventCopyWith<$Res> {
  _$NodeDeployOperationEventCopyWithImpl(this._self, this._then);

  final NodeDeployOperationEvent _self;
  final $Res Function(NodeDeployOperationEvent) _then;

/// Create a copy of NodeDeployOperationEvent
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? operation = freezed,Object? runtimeStatus = freezed,Object? message = freezed,Object? timestamp = freezed,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,operation: freezed == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String?,runtimeStatus: freezed == runtimeStatus ? _self.runtimeStatus : runtimeStatus // ignore: cast_nullable_to_non_nullable
as NodeDeployRuntimeStatus?,message: freezed == message ? _self.message : message // ignore: cast_nullable_to_non_nullable
as String?,timestamp: freezed == timestamp ? _self.timestamp : timestamp // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}
/// Create a copy of NodeDeployOperationEvent
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus {
    if (_self.runtimeStatus == null) {
    return null;
  }

  return $NodeDeployRuntimeStatusCopyWith<$Res>(_self.runtimeStatus!, (value) {
    return _then(_self.copyWith(runtimeStatus: value));
  });
}
}


/// Adds pattern-matching-related methods to [NodeDeployOperationEvent].
extension NodeDeployOperationEventPatterns on NodeDeployOperationEvent {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( NodeDeployRuntimeStatusEvent value)?  runtimeStatus,TResult Function( NodeDeployRuntimeLogEvent value)?  runtimeLog,TResult Function( NodeDeployRuntimeTerminalEvent value)?  runtimeTerminal,required TResult orElse(),}){
final _that = this;
switch (_that) {
case NodeDeployRuntimeStatusEvent() when runtimeStatus != null:
return runtimeStatus(_that);case NodeDeployRuntimeLogEvent() when runtimeLog != null:
return runtimeLog(_that);case NodeDeployRuntimeTerminalEvent() when runtimeTerminal != null:
return runtimeTerminal(_that);case _:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( NodeDeployRuntimeStatusEvent value)  runtimeStatus,required TResult Function( NodeDeployRuntimeLogEvent value)  runtimeLog,required TResult Function( NodeDeployRuntimeTerminalEvent value)  runtimeTerminal,}){
final _that = this;
switch (_that) {
case NodeDeployRuntimeStatusEvent():
return runtimeStatus(_that);case NodeDeployRuntimeLogEvent():
return runtimeLog(_that);case NodeDeployRuntimeTerminalEvent():
return runtimeTerminal(_that);case _:
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( NodeDeployRuntimeStatusEvent value)?  runtimeStatus,TResult? Function( NodeDeployRuntimeLogEvent value)?  runtimeLog,TResult? Function( NodeDeployRuntimeTerminalEvent value)?  runtimeTerminal,}){
final _that = this;
switch (_that) {
case NodeDeployRuntimeStatusEvent() when runtimeStatus != null:
return runtimeStatus(_that);case NodeDeployRuntimeLogEvent() when runtimeLog != null:
return runtimeLog(_that);case NodeDeployRuntimeTerminalEvent() when runtimeTerminal != null:
return runtimeTerminal(_that);case _:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId,  String? operation,  NodeDeployRuntimeStatus? runtimeStatus,  String? message,  String? timestamp)?  runtimeStatus,TResult Function(@UuidValueConverter()  UuidValue? actorId,  String? operation,  NodeDeployRuntimeStatus? runtimeStatus,  String? message,  String? timestamp,  String? logLine)?  runtimeLog,TResult Function(@UuidValueConverter()  UuidValue? actorId,  String? operation,  NodeDeployRuntimeStatus? runtimeStatus,  String? message,  String? timestamp,  String terminalStatus)?  runtimeTerminal,required TResult orElse(),}) {final _that = this;
switch (_that) {
case NodeDeployRuntimeStatusEvent() when runtimeStatus != null:
return runtimeStatus(_that.actorId,_that.operation,_that.runtimeStatus,_that.message,_that.timestamp);case NodeDeployRuntimeLogEvent() when runtimeLog != null:
return runtimeLog(_that.actorId,_that.operation,_that.runtimeStatus,_that.message,_that.timestamp,_that.logLine);case NodeDeployRuntimeTerminalEvent() when runtimeTerminal != null:
return runtimeTerminal(_that.actorId,_that.operation,_that.runtimeStatus,_that.message,_that.timestamp,_that.terminalStatus);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId,  String? operation,  NodeDeployRuntimeStatus? runtimeStatus,  String? message,  String? timestamp)  runtimeStatus,required TResult Function(@UuidValueConverter()  UuidValue? actorId,  String? operation,  NodeDeployRuntimeStatus? runtimeStatus,  String? message,  String? timestamp,  String? logLine)  runtimeLog,required TResult Function(@UuidValueConverter()  UuidValue? actorId,  String? operation,  NodeDeployRuntimeStatus? runtimeStatus,  String? message,  String? timestamp,  String terminalStatus)  runtimeTerminal,}) {final _that = this;
switch (_that) {
case NodeDeployRuntimeStatusEvent():
return runtimeStatus(_that.actorId,_that.operation,_that.runtimeStatus,_that.message,_that.timestamp);case NodeDeployRuntimeLogEvent():
return runtimeLog(_that.actorId,_that.operation,_that.runtimeStatus,_that.message,_that.timestamp,_that.logLine);case NodeDeployRuntimeTerminalEvent():
return runtimeTerminal(_that.actorId,_that.operation,_that.runtimeStatus,_that.message,_that.timestamp,_that.terminalStatus);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId,  String? operation,  NodeDeployRuntimeStatus? runtimeStatus,  String? message,  String? timestamp)?  runtimeStatus,TResult? Function(@UuidValueConverter()  UuidValue? actorId,  String? operation,  NodeDeployRuntimeStatus? runtimeStatus,  String? message,  String? timestamp,  String? logLine)?  runtimeLog,TResult? Function(@UuidValueConverter()  UuidValue? actorId,  String? operation,  NodeDeployRuntimeStatus? runtimeStatus,  String? message,  String? timestamp,  String terminalStatus)?  runtimeTerminal,}) {final _that = this;
switch (_that) {
case NodeDeployRuntimeStatusEvent() when runtimeStatus != null:
return runtimeStatus(_that.actorId,_that.operation,_that.runtimeStatus,_that.message,_that.timestamp);case NodeDeployRuntimeLogEvent() when runtimeLog != null:
return runtimeLog(_that.actorId,_that.operation,_that.runtimeStatus,_that.message,_that.timestamp,_that.logLine);case NodeDeployRuntimeTerminalEvent() when runtimeTerminal != null:
return runtimeTerminal(_that.actorId,_that.operation,_that.runtimeStatus,_that.message,_that.timestamp,_that.terminalStatus);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class NodeDeployRuntimeStatusEvent implements NodeDeployOperationEvent {
   NodeDeployRuntimeStatusEvent({@UuidValueConverter() this.actorId, this.operation, this.runtimeStatus, this.message, this.timestamp, final  String? $type}): $type = $type ?? 'runtime_status';
  factory NodeDeployRuntimeStatusEvent.fromJson(Map<String, dynamic> json) => _$NodeDeployRuntimeStatusEventFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override final  String? operation;
@override final  NodeDeployRuntimeStatus? runtimeStatus;
@override final  String? message;
@override final  String? timestamp;

@JsonKey(name: 'kind')
final String $type;


/// Create a copy of NodeDeployOperationEvent
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NodeDeployRuntimeStatusEventCopyWith<NodeDeployRuntimeStatusEvent> get copyWith => _$NodeDeployRuntimeStatusEventCopyWithImpl<NodeDeployRuntimeStatusEvent>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NodeDeployRuntimeStatusEventToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NodeDeployRuntimeStatusEvent&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.runtimeStatus, runtimeStatus) || other.runtimeStatus == runtimeStatus)&&(identical(other.message, message) || other.message == message)&&(identical(other.timestamp, timestamp) || other.timestamp == timestamp));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,operation,runtimeStatus,message,timestamp);

@override
String toString() {
  return 'NodeDeployOperationEvent.runtimeStatus(actorId: $actorId, operation: $operation, runtimeStatus: $runtimeStatus, message: $message, timestamp: $timestamp)';
}


}

/// @nodoc
abstract mixin class $NodeDeployRuntimeStatusEventCopyWith<$Res> implements $NodeDeployOperationEventCopyWith<$Res> {
  factory $NodeDeployRuntimeStatusEventCopyWith(NodeDeployRuntimeStatusEvent value, $Res Function(NodeDeployRuntimeStatusEvent) _then) = _$NodeDeployRuntimeStatusEventCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, String? operation, NodeDeployRuntimeStatus? runtimeStatus, String? message, String? timestamp
});


@override $NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus;

}
/// @nodoc
class _$NodeDeployRuntimeStatusEventCopyWithImpl<$Res>
    implements $NodeDeployRuntimeStatusEventCopyWith<$Res> {
  _$NodeDeployRuntimeStatusEventCopyWithImpl(this._self, this._then);

  final NodeDeployRuntimeStatusEvent _self;
  final $Res Function(NodeDeployRuntimeStatusEvent) _then;

/// Create a copy of NodeDeployOperationEvent
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? operation = freezed,Object? runtimeStatus = freezed,Object? message = freezed,Object? timestamp = freezed,}) {
  return _then(NodeDeployRuntimeStatusEvent(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,operation: freezed == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String?,runtimeStatus: freezed == runtimeStatus ? _self.runtimeStatus : runtimeStatus // ignore: cast_nullable_to_non_nullable
as NodeDeployRuntimeStatus?,message: freezed == message ? _self.message : message // ignore: cast_nullable_to_non_nullable
as String?,timestamp: freezed == timestamp ? _self.timestamp : timestamp // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

/// Create a copy of NodeDeployOperationEvent
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus {
    if (_self.runtimeStatus == null) {
    return null;
  }

  return $NodeDeployRuntimeStatusCopyWith<$Res>(_self.runtimeStatus!, (value) {
    return _then(_self.copyWith(runtimeStatus: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class NodeDeployRuntimeLogEvent implements NodeDeployOperationEvent {
   NodeDeployRuntimeLogEvent({@UuidValueConverter() this.actorId, this.operation, this.runtimeStatus, this.message, this.timestamp, this.logLine, final  String? $type}): $type = $type ?? 'runtime_log';
  factory NodeDeployRuntimeLogEvent.fromJson(Map<String, dynamic> json) => _$NodeDeployRuntimeLogEventFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override final  String? operation;
@override final  NodeDeployRuntimeStatus? runtimeStatus;
@override final  String? message;
@override final  String? timestamp;
 final  String? logLine;

@JsonKey(name: 'kind')
final String $type;


/// Create a copy of NodeDeployOperationEvent
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NodeDeployRuntimeLogEventCopyWith<NodeDeployRuntimeLogEvent> get copyWith => _$NodeDeployRuntimeLogEventCopyWithImpl<NodeDeployRuntimeLogEvent>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NodeDeployRuntimeLogEventToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NodeDeployRuntimeLogEvent&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.runtimeStatus, runtimeStatus) || other.runtimeStatus == runtimeStatus)&&(identical(other.message, message) || other.message == message)&&(identical(other.timestamp, timestamp) || other.timestamp == timestamp)&&(identical(other.logLine, logLine) || other.logLine == logLine));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,operation,runtimeStatus,message,timestamp,logLine);

@override
String toString() {
  return 'NodeDeployOperationEvent.runtimeLog(actorId: $actorId, operation: $operation, runtimeStatus: $runtimeStatus, message: $message, timestamp: $timestamp, logLine: $logLine)';
}


}

/// @nodoc
abstract mixin class $NodeDeployRuntimeLogEventCopyWith<$Res> implements $NodeDeployOperationEventCopyWith<$Res> {
  factory $NodeDeployRuntimeLogEventCopyWith(NodeDeployRuntimeLogEvent value, $Res Function(NodeDeployRuntimeLogEvent) _then) = _$NodeDeployRuntimeLogEventCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, String? operation, NodeDeployRuntimeStatus? runtimeStatus, String? message, String? timestamp, String? logLine
});


@override $NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus;

}
/// @nodoc
class _$NodeDeployRuntimeLogEventCopyWithImpl<$Res>
    implements $NodeDeployRuntimeLogEventCopyWith<$Res> {
  _$NodeDeployRuntimeLogEventCopyWithImpl(this._self, this._then);

  final NodeDeployRuntimeLogEvent _self;
  final $Res Function(NodeDeployRuntimeLogEvent) _then;

/// Create a copy of NodeDeployOperationEvent
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? operation = freezed,Object? runtimeStatus = freezed,Object? message = freezed,Object? timestamp = freezed,Object? logLine = freezed,}) {
  return _then(NodeDeployRuntimeLogEvent(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,operation: freezed == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String?,runtimeStatus: freezed == runtimeStatus ? _self.runtimeStatus : runtimeStatus // ignore: cast_nullable_to_non_nullable
as NodeDeployRuntimeStatus?,message: freezed == message ? _self.message : message // ignore: cast_nullable_to_non_nullable
as String?,timestamp: freezed == timestamp ? _self.timestamp : timestamp // ignore: cast_nullable_to_non_nullable
as String?,logLine: freezed == logLine ? _self.logLine : logLine // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

/// Create a copy of NodeDeployOperationEvent
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus {
    if (_self.runtimeStatus == null) {
    return null;
  }

  return $NodeDeployRuntimeStatusCopyWith<$Res>(_self.runtimeStatus!, (value) {
    return _then(_self.copyWith(runtimeStatus: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class NodeDeployRuntimeTerminalEvent implements NodeDeployOperationEvent {
   NodeDeployRuntimeTerminalEvent({@UuidValueConverter() this.actorId, this.operation, this.runtimeStatus, this.message, this.timestamp, required this.terminalStatus, final  String? $type}): $type = $type ?? 'runtime_terminal';
  factory NodeDeployRuntimeTerminalEvent.fromJson(Map<String, dynamic> json) => _$NodeDeployRuntimeTerminalEventFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override final  String? operation;
@override final  NodeDeployRuntimeStatus? runtimeStatus;
@override final  String? message;
@override final  String? timestamp;
 final  String terminalStatus;

@JsonKey(name: 'kind')
final String $type;


/// Create a copy of NodeDeployOperationEvent
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NodeDeployRuntimeTerminalEventCopyWith<NodeDeployRuntimeTerminalEvent> get copyWith => _$NodeDeployRuntimeTerminalEventCopyWithImpl<NodeDeployRuntimeTerminalEvent>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NodeDeployRuntimeTerminalEventToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NodeDeployRuntimeTerminalEvent&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.runtimeStatus, runtimeStatus) || other.runtimeStatus == runtimeStatus)&&(identical(other.message, message) || other.message == message)&&(identical(other.timestamp, timestamp) || other.timestamp == timestamp)&&(identical(other.terminalStatus, terminalStatus) || other.terminalStatus == terminalStatus));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,operation,runtimeStatus,message,timestamp,terminalStatus);

@override
String toString() {
  return 'NodeDeployOperationEvent.runtimeTerminal(actorId: $actorId, operation: $operation, runtimeStatus: $runtimeStatus, message: $message, timestamp: $timestamp, terminalStatus: $terminalStatus)';
}


}

/// @nodoc
abstract mixin class $NodeDeployRuntimeTerminalEventCopyWith<$Res> implements $NodeDeployOperationEventCopyWith<$Res> {
  factory $NodeDeployRuntimeTerminalEventCopyWith(NodeDeployRuntimeTerminalEvent value, $Res Function(NodeDeployRuntimeTerminalEvent) _then) = _$NodeDeployRuntimeTerminalEventCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId, String? operation, NodeDeployRuntimeStatus? runtimeStatus, String? message, String? timestamp, String terminalStatus
});


@override $NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus;

}
/// @nodoc
class _$NodeDeployRuntimeTerminalEventCopyWithImpl<$Res>
    implements $NodeDeployRuntimeTerminalEventCopyWith<$Res> {
  _$NodeDeployRuntimeTerminalEventCopyWithImpl(this._self, this._then);

  final NodeDeployRuntimeTerminalEvent _self;
  final $Res Function(NodeDeployRuntimeTerminalEvent) _then;

/// Create a copy of NodeDeployOperationEvent
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? operation = freezed,Object? runtimeStatus = freezed,Object? message = freezed,Object? timestamp = freezed,Object? terminalStatus = null,}) {
  return _then(NodeDeployRuntimeTerminalEvent(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,operation: freezed == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String?,runtimeStatus: freezed == runtimeStatus ? _self.runtimeStatus : runtimeStatus // ignore: cast_nullable_to_non_nullable
as NodeDeployRuntimeStatus?,message: freezed == message ? _self.message : message // ignore: cast_nullable_to_non_nullable
as String?,timestamp: freezed == timestamp ? _self.timestamp : timestamp // ignore: cast_nullable_to_non_nullable
as String?,terminalStatus: null == terminalStatus ? _self.terminalStatus : terminalStatus // ignore: cast_nullable_to_non_nullable
as String,
  ));
}

/// Create a copy of NodeDeployOperationEvent
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$NodeDeployRuntimeStatusCopyWith<$Res>? get runtimeStatus {
    if (_self.runtimeStatus == null) {
    return null;
  }

  return $NodeDeployRuntimeStatusCopyWith<$Res>(_self.runtimeStatus!, (value) {
    return _then(_self.copyWith(runtimeStatus: value));
  });
}
}

// dart format on
